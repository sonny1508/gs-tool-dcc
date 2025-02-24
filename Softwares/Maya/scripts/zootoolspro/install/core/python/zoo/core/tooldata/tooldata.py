"""
Folder Hierarchy::

    root
        |-hotkeys
        |-tools
            |- toolName
                    |-settingOne.json
                    |SettingTwoFolder
                                |-setting.json

"""
import os
import copy
import shutil
import uuid
import ctypes
try:
    # only accessible on windows
    from ctypes.wintypes import MAX_PATH
except (ImportError, ValueError):
    MAX_PATH = 260

from collections import OrderedDict
from zoovendor import six

from zoo.core.util import pathutils, filesystem, classtypes
from zoo.core.util import zlogging, env


logger = zlogging.getLogger(__name__)


class RootAlreadyExistsError(Exception):
    pass


class RootDoesntExistError(Exception):
    pass


class InvalidSettingsPath(Exception):
    pass


class InvalidRootError(Exception):
    pass


class ToolSet(object):
    """
    .. code-block:: python

        # Create some roots
        tset = ToolSet()

        # the order you add roots is important
        tset.addRoot(os.path.expanduser("~/Documents/maya/2018/scripts/zootools_preferences"), "userPreferences")

        # create a settings instance, if one exists already within one of the roots that setting will be used unless you
        # specify the root to use, in which the associated settingsObject for the root will be returned
        newSetting = tset.createSetting(relative="tools/tests/helloworld",
                                        root="userPreferences",
                                        data={"someData": "hello"})
        print os.path.exists(newSetting.path())
        print newSetting.path()
        # lets open a setting
        foundSetting = tset.findSetting(relative="tools/tests/helloworld", root="userPreferences")

    """

    def __init__(self):
        self.roots = OrderedDict()
        self.extension = ".json"

    def rootNameForPath(self, path):
        p = os.path.normpath(path)
        for name, root in self.roots.items():
            if os.path.normpath(root).startswith(p):
                return name

    def root(self, name):
        if name not in self.roots:
            raise RootDoesntExistError("Root by the name: {} doesn't exist".format(name))
        return self._resolveRoot(self.roots[name])

    def _resolveRoot(self, root):
        root = six.text_type(root)
        return os.path.expandvars(os.path.expanduser(_patchRootPath(root))).replace("\\", "/")

    def addRoot(self, fullPath, name):
        """ Add root

        :param fullPath:
        :param name:
        :return:
        """
        if name in self.roots:
            raise RootAlreadyExistsError("Root already exists: {}".format(name))
        absRoot = self._resolveRoot(fullPath)
        if not os.path.exists(absRoot):
            raise RootDoesntExistError("Root Path Doesn't exist: {}".format(absRoot))
        self.roots[name] = fullPath

    def deleteRoot(self, root):
        """Deletes the root folder location and all files.

        :param root: the root name to delete
        :type root: str
        :return:
        :rtype: bool
        """
        rootPath = self.root(root)
        try:
            shutil.rmtree(rootPath)
        except OSError:
            logger.error("Failed to remove the preference root: {}".format(rootPath),
                         exc_info=True)
            return False
        return True

    def findSetting(self, relativePath, root=None, extension=None):
        """Finds a settings object by searching the roots in reverse order.

        The first path to exist will be the one to be resolved. If a root is specified
        and the root+relativePath exists then that will be returned instead

        :param relativePath:
        :type relativePath: str
        :param root: The Root name to search if root is None then all roots in reverse order will be search until a \
        settings is found.
        :type root: str or None
        :return:
        :rtype: :class:`SettingObject`
        """
        relativePath = six.text_type(relativePath)
        relativePath = pathutils.withExtension(relativePath, extension or self.extension)
        try:
            if root is not None:
                rootPath = self.roots.get(root)

                if rootPath is not None:
                    resolvedRoot = self._resolveRoot(rootPath)
                    fullpath = os.path.normpath(os.path.join(resolvedRoot, relativePath))

                    if not os.path.exists(fullpath):
                        return SettingObject(rootPath, relativePath)
                    return self.open(rootPath, relativePath)
            else:
                for name, p in reversed(self.roots.items()):
                    # we're working with an ordered dict
                    resolvedRoot = self._resolveRoot(p)
                    fullpath = os.path.join(resolvedRoot, relativePath)
                    if not os.path.exists(fullpath):
                        continue
                    return self.open(resolvedRoot, relativePath)
        except ValueError:
            logger.error("Failed to load: {} due to syntactical issue".format(relativePath))
            raise

        return SettingObject("", relativePath)

    def settingFromRootPath(self, relativePath, rootPath, extension=None):
        fullpath = os.path.join(rootPath, pathutils.withExtension(relativePath, extension or self.extension))
        if os.path.exists(fullpath):
            return self.open(rootPath, relativePath)
        return SettingObject("", relativePath)

    def createSetting(self, relative, root, data):
        setting = self.findSetting(relative, root)
        setting.update(data)
        return setting

    def open(self, root, relativePath, extension=None):
        relativePath = pathutils.withExtension(relativePath, extension or self.extension)
        fullPath = os.path.join(root, relativePath)
        if not os.path.exists(fullPath):
            raise InvalidSettingsPath(fullPath)
        data = filesystem.loadJson(fullPath)
        return SettingObject(root, relativePath, **data)


class SettingObject(dict):
    """Settings class to encapsulate the json data for a given setting
    """

    def __init__(self, root, relativePath=None, **kwargs):
        relativePath = relativePath or ""
        _, ext = os.path.splitext(relativePath)
        if not ext:
            relativePath = os.path.extsep.join((relativePath, "json"))
        kwargs["relativePath"] = relativePath
        kwargs["root"] = root
        super(SettingObject, self).__init__(**kwargs)

    def rootPath(self):
        if self.root:
            return self.root
        return ""

    def path(self):
        return os.path.join(self.root, self["relativePath"])

    def isValid(self):
        if self.root is None:
            return False
        elif os.path.exists(self.path()):
            return True
        return False

    def __repr__(self):
        return "<{}> root: {}, path: {}".format(self.__class__.__name__, self.root, self.relativePath)

    def __cmp__(self, other):
        return self.name == other and self.version == other.version

    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError:
            return super(SettingObject, self).__getattribute__(item)

    def __setattr__(self, key, value):
        self[key] = value

    def save(self, indent=False, sort=False):
        """Saves file to disk as json

        :param indent: If True format the json nicely (indent=2)
        :type indent: bool
        :return fullPath: The full path to the saved .json file
        :rtype fullPath: str
        """
        root = self.root

        if not root:
            return ""

        fullPath = os.path.join(root, self.relativePath)
        filesystem.ensureFolderExists(os.path.dirname(fullPath))
        output = copy.deepcopy(self)
        del output["root"]
        del output["relativePath"]
        numSplit = len(os.path.splitext(os.path.basename(fullPath)))
        if not numSplit > 0:
            fullPath = fullPath + "json"
        kwargs = {"sort_keys": sort,
                  "data": output,
                  "filepath": fullPath
                  }
        if indent:
            kwargs["indent"] = 2
        filesystem.saveJson(**kwargs)


        return self.path()


class DirectoryPath(classtypes.ObjectDict):
    """
    :param pref:
    :param id_:
    :param alias:
    :param path:
    """
    def __init__(self, path=None, id_=None, alias=None, pref=None):
        """ Directory path to save the directory path setting.

        Holds the alias, path and a unique id

        """
        #temp workaround to handle backward compatiblity
        kwargs = {}
        if pref:
            kwargs = pref
        else:
            kwargs["id"] = id_ or str(uuid.uuid4())[:6]
            kwargs["path"] = pathutils.normpath(path)
            kwargs["alias"] = alias or os.path.basename(path)
        if not kwargs["path"] and kwargs["pref"] is None:
            raise Exception("'pref' or 'path' must be set for DirectoryPath.")
        super(DirectoryPath, self).__init__(**kwargs)


    def serialize(self):
        """ Get the dict

        :return:
        """
        return self

    def __eq__(self, other):
        """ Returns true if the path is the same.
        other can be a string or a DirectoryPath

        :param other:
        :return:
        """
        if isinstance(other, six.string_types):
            return pathutils.normpath(other) == pathutils.normpath(self.path)

        if isinstance(other, DirectoryPath):
            return pathutils.normpath(other.path) == pathutils.normpath(self.path)

        return super(DirectoryPath, self).__eq__(other)


def _patchRootPath(rootPath):
    """Patch for zootools preferences path with the use of "~" where python now prioritizes USERPROFILE
    over HOME which happens to affect maya 2022 and below which sets the USERPROFILE to ~/Documents but
    maya 2023 is set to ~/ so this patches it globally across zoo only if "~" is the first character and
    it's windows ensuring that the existing prefs and updating/new installations are maintained.
    """
    if env.isWindows() and rootPath.startswith("~"):
        parts = os.path.normpath(rootPath).split(os.path.sep)
        dll = ctypes.windll.shell32

        buf = ctypes.create_unicode_buffer(MAX_PATH + 1)
        # note: 0x0005 is CSIDL_PERSONAL from win32com.shell.shellcon module but that doesn't come with python :(
        if dll.SHGetSpecialFolderPathW(None, buf, 0x0005, False):
            return os.path.join(buf.value, *parts[1:])
    return os.path.expanduser(rootPath)
