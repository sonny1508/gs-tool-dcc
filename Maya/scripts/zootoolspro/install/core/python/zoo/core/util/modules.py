"""This module deals with module paths, importing and the like.
"""
import inspect

import sys
import os
import importlib

from zoo.core.util import zlogging

logger = zlogging.getLogger(__name__)

# File prefixes to exclude for determining a valid python module
# include Operating System meta files and hidden files to ignore
MODULE_EXCLUDE_PREFIXES = ("__init__.py",
                           ".__init__",
                           # OSX related metaFiles
                           ".DS_Store",
                           ".Spotlight-V100",
                           ".Trashes",
                           ".fseventsd",
                           "._")
# py2 and py3 support
if sys.version_info[0] < 3:
    import imp


    def _importModule(name, path):
        """Python 2 helper function for importing a python module.

        :param name: The module name
        :type name: str
        :param path: The full path to the module
        :type path: str
        :return: The imported module object
        :rtype: module
        """
        if path.endswith(".py"):
            return imp.load_source(name, path)
        elif path.endswith(".pyc"):
            return imp.load_compiled(name, path)
        return __import__(name)
else:
    def _importModule(name, path):
        """Python 3 helper function for importing a python module.

        :param name: The module name
        :type name: str
        :param path: The full path to the module
        :type path: str
        :return: The imported module object
        :rtype: module
        """
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        sys.modules[name] = mod  # ensure we add to the global to mirror the behaviour of the py2 version
        return mod


def importModule(modulePath, name=None):
    """Imports the modulePath, if ModulePath is a dottedPath then the function will use importlib otherwise it's
    expected that modulePath is the absolute path to the source file. If the name arg is not provided then the basename
    without the extension will be used.

    :param modulePath: The module path either a dottedPath eg. zoo.libs.utils.zoomath or a absolute path.
    :type modulePath: str
    :param name: The name for the imported module which will be used if the modulepath is a absolute path.
    :type name: str
    :return: The imported module object
    :rtype: ModuleObject
    """
    if isDottedPath(modulePath) and not os.path.exists(modulePath):
        try:

            return importlib.import_module(modulePath)
        except ImportError:
            logger.error("Failed to load module->{}".format(modulePath), exc_info=True)
    try:
        if not name:
            name = os.path.splitext(os.path.basename(modulePath))[0]
        if name in sys.modules:
            return sys.modules[name]
        if os.path.isdir(modulePath):
            modulePath = os.path.join(modulePath, "__init__.py")
            if not os.path.exists(modulePath):
                raise ValueError("Cannot find modulepath: {}".format(modulePath))

        return _importModule(name, os.path.realpath(modulePath))
    except ImportError:
        logger.error("Failed to load module {}".format(modulePath))
        raise

def validModulePath(path, exclude=None):
    """Determines if the path is a valid python module path.
    The python must be ending with either .py or .pyc and not be in the exclude list provide
    nor in the MODULE_EXCLUDE_PREFIXES.

    :param path: The file path to check.
    :type path: str
    :param exclude: File name prefixes or file base names to exclude.
    :type exclude: list[str]
    :rtype: bool
    """
    exclude = exclude or []
    basename = os.path.basename(path)
    if not basename.startswith(MODULE_EXCLUDE_PREFIXES) and basename not in exclude:
        return path.endswith(".py") or path.endswith(".pyc")
    return False

def iterModules(path, exclude=None):
    """Iterate of the modules of a given folder path

    :param path: str, The folder path to iterate
    :param exclude: list, a list of files to exclude
    :return: iterator
    """
    exclude = exclude or []
    for root, dirs, files in os.walk(path):
        if "__init__.py" not in files:
            continue
        for f in files:
            modulePath = os.path.join(root, f)
            if validModulePath(modulePath, exclude):
                yield modulePath


def iterMembers(module, predicate=None):
    """Iterates the members of the module, use predicte to restrict to a type

    :param module:Object, the module object to iterate
    :param predicate: inspect.class
    :return:iterator
    """
    for mod in inspect.getmembers(module, predicate=predicate):
        yield mod


def isDottedPath(path):
    """Determines if the path is a dotted path. Bit of a hack

    :param path: str
    :return: bool
    """
    return len(path.split(".")) > 2


def iterSubclassesFromModule(module, classType):
    """Iterates all classes within a module object returning subclasses of type `classType`.

    :param module: the module object to iterate on
    :type module: module object
    :param classType: The class object
    :type classType: object
    :return: genertor function returning class objects
    :rtype: generator(object)
    """
    for member in iterMembers(module, predicate=inspect.isclass):
        if issubclass(member[1], classType):
            yield member[1]


def asDottedPath(path):
    """ Returns a dotted path relative to the python path.

    .. code-block:: python

        import sys
        currentPath = os.path.expanduser("someRandomPath")
        sys.path.append(currentPath)
        asDottedPath("someRandomPath/subfolder/subsubfolder.py")
        #result: subfolder.subsubfolder

    :param path: the absolute path to convert to a dotted path
    :type path: str
    :return: The dotted path relative to the python
    :rtype: str
    """
    d, f = os.path.split(path)
    f = os.path.splitext(f)[0]
    packagePath = [f]  # __package__ will be a reversed list of package name parts
    syspath = sys.path
    driveLetter = os.path.splitdrive(path)[0] + "/"
    while d not in syspath:  # go up until we run out of __init__.py files
        d, name = os.path.split(d)  # pull of a lowest level directory name
        if d == driveLetter or name == "":
            return ""
        packagePath.append(name)  # add it to the package parts list
    return ".".join(reversed(packagePath))


def runScriptFunction(filePath, funcName, message, *args):
    """Runs a function in the provided python script.

    :param filePath: The full path to the python script.
    :type filePath: str
    :param funcName: The function name within the script to run.
    :type funcName: str
    :param message: The debug message to print before the function is run.
    :type message: str
    :param args: The arguments to pass to the function which will be executed.
    :type args: tuple
    :return: The function return value or None.
    """
    try:
        scope = {}
        with open(filePath, "rb") as f:
            exec(compile(f.read(), filePath, 'exec'), scope)
        func = scope.get(funcName)
        if func is not None:
            logger.debug(message)
            return func(*args)
    except Exception:
        msg = "Problem loading {}".format(filePath)
        logger.error(msg, exc_info=True)
