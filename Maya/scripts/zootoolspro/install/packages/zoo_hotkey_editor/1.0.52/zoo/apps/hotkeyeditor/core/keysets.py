import copy
import glob
import os

import maya.cmds as cmds

from zoo.apps.hotkeyeditor.core import const
from zoo.apps.hotkeyeditor.core import hotkeys
from zoo.apps.hotkeyeditor.core import utils

from zoo.core.util import zlogging, classtypes, filesystem
from zoo.libs.utils import output

from zoovendor import six
from zoovendor.six import string_types

logger = zlogging.getLogger(__name__)


@six.add_metaclass(classtypes.Singleton)
class KeySetManager(object):
    """
    All the keysets together to manage
    """

    defaultKeySetName = const.DEFAULT_KEYSET
    mayaKeySetName = const.DEFAULT_MAYA
    newKeySetTemplateName = const.DEFAULT_TEMPLATE
    prefix = const.KEYSET_PREFIX
    defaultLanguage = "python"  # or "mel"
    version = (1, 8)

    def __init__(self):

        self.hkUserPath = utils.hotkeyPathUserPrefs()
        self.hkInternalPath = utils.hotkeyPathInternalPrefs()
        self.defaultKeySetPath = os.path.join(self.hkInternalPath, self.defaultKeySetName)
        self.mayaKeySetPath = os.path.join(self.hkInternalPath, self.mayaKeySetName)
        self.newKeySetTemplatePath = os.path.join(self.hkInternalPath, self.newKeySetTemplateName)

        self.defaultKeySetPathUser = os.path.join(self.hkUserPath, self.defaultKeySetName)
        self.mayaKeySetPathUser = os.path.join(self.hkUserPath, self.mayaKeySetName)
        self.newKeySetTemplatePathUser = os.path.join(self.hkUserPath, self.newKeySetTemplateName)
        self.defaultKeySet = KeySet(jsonPath=self.defaultKeySetPathUser + ".json")
        self.mayaKeySet = KeySet(jsonPath=self.mayaKeySetPathUser + ".json")
        self.newKeySetTemplate = KeySet(jsonPath=self.newKeySetTemplatePathUser + ".json")
        self.keySets = []  # type: list[KeySet]
        self.reverts = []
        self.locked = [self.defaultKeySetName, self.mayaKeySetName]
        self._currentKeySet = ""  # type: KeySet
        self.revertToDefaults()

    def revertToDefaults(self, force=False):
        self.deleteDefaults(deleteMaya=False)
        self.copyToUserPref()
        self.defaultKeySet = KeySet(jsonPath=self.defaultKeySetPathUser + ".json")
        self.mayaKeySet = KeySet(jsonPath=self.mayaKeySetPathUser + ".json")
        self.newKeySetTemplate = KeySet(jsonPath=self.newKeySetTemplatePathUser + ".json")
        self.keySets = []  # type: list[KeySet]
        self.reverts = []
        self.keySetInit()
        self.updateDefaults(force)

    def keySetInit(self):
        """ Reads the hotkey folder for key set jsons and loads them into memory.

        :return:
        """
        userJson = []
        for f in glob.glob("{}/*.json".format(self.hkUserPath)):
            if os.path.basename(f).startswith(self.prefix):
                userJson.append(f)
        self.keySets = [self.mayaKeySet, self.defaultKeySet]
        for f in userJson:
            keyset = KeySet(jsonPath=f)
            self.keySets.append(keyset)
        # Get the current keyset
        self.currentKeySet(True)
        self.setAllReverts()

    def prefVersion(self):
        """ Get the version of the zoo hotkeys found in the preferences

        :return:
        """
        try:
            return tuple(filesystem.loadJson(os.path.join(self.hkUserPath, "version")))
        except IOError:
            return -1, 0  # Return a version that means that it hasn't existed yet

    def saveVersion(self):
        """ Save the current version to the version file

        :return:
        """
        filesystem.saveJson(self.version, os.path.join(self.hkUserPath, "version"))

    def copyToUserPref(self):
        """ Copy hotkey files to user

        :return:
        """

        files = ((self.defaultKeySetPathUser, self.defaultKeySetPath),
                 (self.mayaKeySetPathUser, self.mayaKeySetPath),
                 (self.newKeySetTemplatePathUser, self.newKeySetTemplatePath))

        # will not override file if it already exists. This gets handled in the update function
        for userPath, originalPath in files:
            utils.copyFile(userPath, originalPath, ".json")
        for userPath, originalPath in files[:-1]:
            utils.copyFile(userPath, originalPath, ".mhk")

    def defaultKeySets(self):
        """ Returns the default keysets

        :return:
        """
        return self.keySetsByName(self.locked)

    def keySetsByName(self, names):
        """ Get keysets by name

        :param names:
        :return:
        """
        keysets = []
        for k in self.keySets:
            if k.keySetName in names:
                keysets.append(k)

        return keysets

    def setAllReverts(self):
        """ Sets the revert data based on the keysets
        :return:
        """
        self.reverts = []
        for k in self.keySets:
            r = KeySet(k)
            self.reverts.append(r)

    def setRevert(self, keySet):
        toDel = ""
        for r in self.reverts:
            if r.keySetName == keySet.keySetName:
                toDel = r
                break

        self.reverts.remove(toDel)
        newR = KeySet(keySet)
        self.reverts.append(newR)

    def revertKeySet(self, keySet):
        """ Set the data from the revert data

        :param keySet:
        :return:
        """
        for r in self.reverts:
            if keySet.keySetName == r.keySetName:
                keySet.setData(r)

                return

    def revertCurrentKeySet(self):
        current = self.currentKeySet()
        self.revertKeySet(current)

    def keySetNames(self, excludeMaya=False):
        """ Generally used by the UI

        :return:
        """
        keysets = []

        for i, k in enumerate(self.keySets):
            # Remove .json
            kset = utils.getFileName(k.filePath)

            # Skip the the defaultKeyset one since its our default Zoo_Tools_Default one
            if kset == self.defaultKeySetName or kset == self.newKeySet:
                keysets.append(kset)
                continue

            # Exclude Maya default key set
            if kset == self.mayaKeySetName and excludeMaya:
                continue

            # Otherwise Assumes that it is prefixed with "Zoo_User_"
            removedPre = utils.removePrefix(self.prefix, kset)
            keysets.append(removedPre)

        return keysets

    def installAll(self):
        """ Install all keysets

        :return:
        """

        for k in self.keySets:
            k.install()

    def _displayMessage(self, keySet):
        """Displays a nice message to the user depending on the key set

        :param keySet: The current key set Maya will switch to.
        :type keySet:
        """
        name = str(keySet.keySetName)
        if name == "Maya_Default_ZooMod":
            messageName = "Maya Default"
        elif name == "Zoo_Tools_Default":
            messageName = "Zoo Tools Default"
        else:
            messageName = name.replace("Zoo_User_", "")
        output.displayInfo("Hotkey set switched to :  `{}`".format(messageName))

    def nextKeySet(self):
        """ Goes to the next keyset.

        Usage:
            from zoo.libs.maya.cmds.hotkeys import keysets
            keysets.KeySetManager().nextKeySet()

        :return:
        """

        nextK = False
        current = self.currentKeySet(forceMaya=True)

        # Loop through keysets
        for ks in self.keySets:
            if nextK:
                self._displayMessage(ks)  # output message
                self.setActive(ks, mayaOnly=True)
                return

            if ks == current and current != self.keySets[-1]:
                nextK = True

        # If it reached here loop it back to the start
        if nextK is False:
            self.setActive(self.keySets[0], mayaOnly=True)
            self._displayMessage(self.keySets[0])  # output message
            return

        if current is None:
            self.setActive(self.getDefaultKeySet())
            self._displayMessage(self.getDefaultKeySet())  # output message

            return

    def getRuntimeCommandNames(self):
        current = self.currentKeySet()
        userRTCs = []
        mayaRTCs = utils.sortedIgnoreCase(utils.getDefaultRuntimeCmdsList())
        zooRTCs = self.defaultKeySet.getRuntimeCommandNames()

        if current is not None:
            userRTCs = current.getRuntimeCommandNames()

        return userRTCs, zooRTCs, mayaRTCs

    def setActive(self, keySet, install=False, mayaOnly=False):
        """
        Set keyset as active. Everything is set up here

        :param keySet:
        :type keySet: KeySet or basestring
        :param install:
        :param mayaOnly:
        :return:
        """

        switchSet = ""
        # By Object
        if isinstance(keySet, KeySet):
            switchSet = keySet

        # By String
        if isinstance(keySet, string_types):
            for ks in self.keySets:
                if keySet == ks.keySetName or self.prefix + keySet == ks.keySetName:
                    switchSet = ks
                    break

        if switchSet != "":
            self._currentKeySet = switchSet

            if install and mayaOnly is False:
                self._currentKeySet.install()
                # logger.info("Applying set {}".format(switchSet.keySetName))

            if mayaOnly:
                cmds.hotkeySet(self._currentKeySet.keySetName, current=1, e=1)
                # logger.info("Applying set {}".format(switchSet.keySetName))

            return self._currentKeySet

        logger.warning("Key set not found! " + keySet, self.keySets)

    def setModified(self, value):
        current = self.currentKeySet()
        current.modified = value

    def isModified(self):
        current = self.currentKeySet()
        return current.modified

    def deleteDefaults(self, deleteMaya=True):
        """ Delete default keysets from maya and the folder

        :return:
        """
        defaults = self.defaultKeySets()
        for d in defaults:
            if deleteMaya:
                d.delete()
            else:
                d.deleteJson()
                d.deleteMHK()

    def currentKeySet(self, forceMaya=False):
        """

        :param forceMaya:
        :return:
        :rtype: :class:`KeySet` or None
        """

        if self._currentKeySet != "" and forceMaya is False:
            return self._currentKeySet

        current = utils.currentMayaSet()

        allKeySets = self.keySets + [self.mayaKeySet]
        for ks in allKeySets:

            if ks.keySetName == current:
                self._currentKeySet = ks
                return self._currentKeySet

    def newKeySet(self, name):
        """ Create new key set

        :param name:
        :return:
        """
        # New key set object
        name = self.prefix + name

        # Check to see if it exists first
        for k in self.keySets:
            if k.keySetName == name or k.prettyName.lower() == name.lower():
                return False

        # Copy the Zoo_Tools_Default key set
        keyset = copy.deepcopy(self.newKeySetTemplate)
        keyset.keySetName = name
        keysetFile = os.path.join(self.hkUserPath, name + ".json")
        keyset.filePath = keysetFile

        self.keySets.append(keyset)
        self.setActive(keyset, install=True)

        # Save it as a json since its a new set
        keyset.save()

        return keyset

    def isDefaultKeySet(self):
        """
        If current active keyset is default
        :return:
        """

        if self.currentKeySet() is not None and \
                self.currentKeySet().keySetName == self.defaultKeySetName:
            return True
        return False

    def isLockedKeySet(self):
        """ Checks if the current keyset is a locked one
        :return:
        """
        current = self.currentKeySet()
        if current is not None and current.keySetName in self.locked:
            return True
        return False

    def isKeySetLocked(self, keySetName=None):
        """ Checks if the keyset is one of the locked keysets. Ie. the default zoo tools key sets

        :param keySetName:
        :return:
        """
        keySetName = keySetName or self.currentKeySet().keySetName
        locked = [utils.removePrefix(self.prefix, x) for x in self.locked]
        return keySetName in locked

    def getDefaultKeySet(self):
        """

        :return:
        """
        if self.defaultKeySet == "":
            self.defaultKeySet = list(filter(lambda x: x.keySetName == self.defaultKeySetName, self.keySets))[0]

        return self.defaultKeySet

    def getMayaKeySet(self):
        """

        :return:
        """
        if self.mayaKeySet == "":
            self.mayaKeySet = list(filter(lambda x: x.keySetName == self.mayaKeySetName, self.keySets))[0]

        return self.mayaKeySet

    def newHotkey(self, name):
        """
        New hotkey based on name, created in the current keyset

        :param name:
        :return:
        """
        return self._currentKeySet.newHotkey(name)

    def deleteHotkey(self, hotkey):
        """

        :param hotkey:
        :type hotkey: hotkeys.Hotkey
        :return:
        """
        if not isinstance(hotkey, hotkeys.Hotkey):
            logger.info("KeySetManager.deleteHotkey(): Expecting Hotkey")
            return
        return self._currentKeySet.deleteHotkey(hotkey)

    def save(self, saveOverDefaults=False):
        """ Save all keysets to their json files and mhk files
        :return:
        """
        # Save as json
        for k in self.keySets:
            if not self.isKeySetLocked(k.keySetName) or utils.isAdminMode() or saveOverDefaults:
                logger.info("{}: Saving to {}".format(k.keySetName, k.filePath))
                utils.backupFile(k.filePath)
                k.save()
            else:
                logger.info("{} is Read-Only. Ignoring.".format(k.keySetName))

        # Reset all the revert data
        self.setAllReverts()

    def keySetByName(self, name):
        """ Gets key set by name

        :param name:
        :return:
        """

        find = list(filter(lambda x: x.keySetName == name or
                                     x.keySetName == KeySetManager.prefix + name,
                           self.keySets))

        if len(find) > 0:
            return find[0]

    def deleteKeySet(self, keySet):
        """
        Delete Key set
        :param keySet:
        :return:
        """
        ks = self.keySetByName(keySet)
        utils.backupFile(ks.filePath)
        os.remove(ks.filePath)
        self.keySets.remove(ks)
        cmds.hotkeySet(ks.keySetName, e=1, delete=1)
        del ks

    def setupRuntimeCmd(self, selectedHotkey, runtimeCmdName, keySet=""):
        """ Set up Runtime command for the key set with the selectedHotkey

        :param selectedHotkey:
        :param runtimeCmdName:
        :param keySet:
        :return: Returns a dictionary full of what the UI should be filled with
        :rtype: dict
        """
        if keySet == "":
            keySet = self.currentKeySet()

        ui = {'commandLanguage': self.defaultLanguage,
              'category': "",
              'command': ""}

        currentRTC = keySet.getRuntimeCmdByName(runtimeCmdName)
        defaultRTC = self.defaultKeySet.getRuntimeCmdByName(runtimeCmdName)
        mayaRTC, lang = utils.getMayaRuntimeCommand(runtimeCmdName)

        rtcType = ""

        if mayaRTC is not None:
            # Maya Runtime Command found
            rtcType = const.RTCTYPE_MAYA
            ui['command'] = mayaRTC
            ui['commandLanguage'] = lang
        elif currentRTC is not None:
            # Runtime Command in current keyset
            ui = dict(currentRTC.cmdAttrs)
            rtcType = const.RTCTYPE_CURRENT
        elif currentRTC is None and defaultRTC is not None:
            # Runtime command in Zoo key set
            ui = dict(defaultRTC.cmdAttrs)
            rtcType = const.RTCTYPE_ZOO
        elif currentRTC is None and defaultRTC is None and not mayaRTC:
            # No runtime found, create a new one. Might want to separate this one out
            rtcType = const.RTCTYPE_NEW

        ui['rtcType'] = rtcType

        keySet.setUpRuntimeCommand(selectedHotkey, runtimeCmdName, rtcType=rtcType)

        return ui

    def updateDefaults(self, force=False):
        """ Update local hotkeys if version is different

        :return:
        """
        if not self.installed() and not force:
            logger.info("Hotkeys not installed, ignoring.", )
            return
        if self.prefVersion() < self.version or force:
            keyset = cmds.hotkeySet(q=1, current=1)
            self.deleteDefaults()
            self.installAll()
            self.save(saveOverDefaults=True)
            cmds.hotkeySet(keyset, current=1, e=1)
            logger.info("Hotkey sets are out of date. Updating to {}.".format(self.versionStr()))
            self.saveVersion()

    def versionStr(self):
        """ Version as a string

        :return:
        """
        return "{}.{}".format(*self.version)

    def installed(self):
        """ Returns true if zoo hotkeys are installed.

        Pretty much just checks if the default keyset is installed into maya.

        :return:
        """
        return cmds.hotkeySet(const.DEFAULT_KEYSET, exists=True)


class KeySet(object):
    """
    The KeySet class. Reads in the list
    """

    def __init__(self, keySet=None, jsonPath="", name="", source=""):
        """ Either create Keyset through the jsonPath or create a new one by name

        :param jsonPath:
        :param name:
        """
        if isinstance(keySet, KeySet):
            self.__dict__ = copy.deepcopy(keySet.__dict__)
            return

        # All these are lists of MHKCommand()
        self._hotkeyCmds = []
        self._runtimeCmds = []
        self._nameCmds = []
        self._hotkeyCtxCmds = []

        self.keySetName = name
        self.source = source

        self.hotkeys = []  # type: list[hotkeys.Hotkey]
        self.filePath = jsonPath
        self.readOnly = False
        self.modified = False

        self._prettyName = ""

        if os.path.exists(jsonPath):
            self.loadJson(jsonPath)
            self.sort()
            self.setNameFromJson()

    @property
    def prettyName(self):
        return utils.removePrefix(KeySetManager.prefix, self.keySetName)

    def setData(self, keySet):
        if isinstance(keySet, KeySet):
            self.__dict__ = copy.deepcopy(keySet.__dict__)

    def __repr__(self):
        return super(KeySet, self).__repr__().replace("<", "<keySetName=\"{}\" ".format(self.keySetName))

    def newHotkey(self, name):
        """
        Adds a new hotkey to the current keyset
        :return:
        """

        checkName = (name + "NameCommand").lower()
        # Check to see if hotkey exists
        if self.nameCommandExists(checkName):
            return False

        name = utils.toRuntimeStr(name)

        hotkeyCmd = hotkeys.MHKCommand(cmdType=const.MHKType.hotkey, name=name)
        hotkeyCmd.setHotkeyCmd(name + "NameCommand", "", const.KEYEVENT_PRESS)

        hotkey = hotkeys.Hotkey(hotkeyCmd)

        self.hotkeys.append(hotkey)
        self._hotkeyCmds.append(hotkeyCmd)

        return hotkey

    def hotkey(self, name):
        for hotkey in self.hotkeys:
            if hotkey.name == name:
                return hotkey

    def getRuntimeCommandNames(self):
        return [r.cmdAttrs['cmdInput'] for r in self._runtimeCmds]

    def nameCommandExists(self, nameCommand):
        nameCommand = utils.toRuntimeStr(nameCommand)
        nameCommand = nameCommand.lower()
        for h in self.hotkeys:
            if nameCommand == h.nameCommand.lower():
                return True

        return False

    @staticmethod
    def copyHotKeyTo(targetKeySet, sourceHotKey):
        """

        :param targetKeySet:
        :type targetKeySet: :class:`KeySet`
        :param sourceHotKey:
        :type sourceHotKey: :class:`hotkeys.HotKey`
        :return:
        :rtype: :class:`hotkeys.Hotkey`
        """
        checkName = sourceHotKey.getNameCmdName()
        # Check to see if hotkey exists
        if targetKeySet.nameCommandExists(checkName):
            logger.info("Hotkey already exists in keySet: {}".format(targetKeySet.prettyName))
            return False
        logger.info("Copying hotKey '{}', To: {}, requires saving".format(checkName, targetKeySet.prettyName))
        hotkey = copy.deepcopy(sourceHotKey)
        targetKeySet.hotkeys.append(hotkey)
        targetKeySet._hotkeyCmds.append(hotkey.mhkcmds.hotkeyCmd)

    def deleteHotkey(self, hotkey):

        if not isinstance(hotkey, hotkeys.Hotkey):
            logger.info("KeySet.deleteHotkey(): Expecting Hotkey")
            return

        # Todo: Should check if everything got removed properly
        if hotkey.mhkcmds.hotkeyCmd is not None:
            try:
                self._hotkeyCmds.remove(hotkey.mhkcmds.hotkeyCmd)
            except ValueError:
                logger.warning("KeySet.deleteHotkey(): hotkeyCmd Missing!")
                return False
        else:
            logger.warning("KeySet.deleteHotkey(): hotkeyCmd Missing!")
            return False

        if hotkey.mhkcmds.nameCmd is not None:
            try:
                self._nameCmds.remove(hotkey.mhkcmds.nameCmd)
            except ValueError:
                logger.warning("KeySet.deleteHotkey(): hotkeyCmd Missing!")

        if hotkey.mhkcmds.runtimeCmd is not None:
            try:
                self._runtimeCmds.remove(hotkey.mhkcmds.runtimeCmd)
            except ValueError:
                logger.warning("KeySet.deleteHotkey(): hotkeyCmd Missing!")

        if hotkey.mhkcmds.hotkeyCtxCmd is not None:
            try:
                self._hotkeyCtxCmds.remove(hotkey.mhkcmds.hotkeyCtxCmd)
            except ValueError:
                logger.warning("KeySet.deleteHotkey(): hotkeyCmd Missing!")

        try:
            self.hotkeys.remove(hotkey)
        except ValueError:
            logger.warning("KeySet.deleteHotkey(): Hotkey() not found!")

        return True

    def setNameFromJson(self):
        """
        Set the name based on the jsonPath
        :return:
        """

        if self.filePath != "":
            self.keySetName = utils.getFileName(self.filePath)

    def setSource(self, source):
        """ Set the keyset source to use as a hotkey base on.

        eg Maya_Default, Maya_Default_ZooMod, Zoo_Tools_Default

        :param source:
        :return:
        """
        self.source = source

    def count(self, includeEmpty=False):
        """
        Get number of hotkey entries there are.

        :param includeEmpty: Sometimes Maya gives empty hotkey entries. Set to false to exclude them
        :return:
        """
        # Clear out the empty
        if includeEmpty is False:
            nonEmptyList = list(filter(lambda x: x.prettyName != "", self.hotkeys))
            nonEmptyCount = len(nonEmptyList)

            return nonEmptyCount

        return len(self.hotkeys)

    def loadJson(self, path):
        commandList = filesystem.loadJson(path)
        self.filePath = path
        # Get hotkeys only for now
        self.setupCommands(commandList)

    def setupCommands(self, commandList):

        hotkeySet = []

        # Separate out the commands out first
        for cmd in commandList:
            mhkCommand = hotkeys.MHKCommand(cmdDict=cmd)

            if cmd['cmdType'] == const.MHKType.hotkey:
                self._hotkeyCmds.append(mhkCommand)
            elif cmd['cmdType'] == const.MHKType.nameCommand:
                self._nameCmds.append(mhkCommand)
            elif cmd['cmdType'] == const.MHKType.runTimeCommand:
                self._runtimeCmds.append(mhkCommand)
            elif cmd['cmdType'] == const.MHKType.hotkeyCtx:
                self._hotkeyCtxCmds.append(mhkCommand)
            elif cmd['cmdType'] == const.MHKType.hotkeySet:
                hotkeySet = cmd
                pass
            else:
                print("KeySet(): Invalid command type! \"{}\"".format(cmd['cmdType']))

        # Now lets do the set up
        try:
            self.source = hotkeySet['source']
        except TypeError:
            logger.warning("Warning! JSON may be empty!")

        self.setupHotkeys()

    def sort(self):
        if len(self.hotkeys) <= 1:
            return

        self.hotkeys.sort(key=lambda x: x.nameCommand.lower(), reverse=False)

        # Move empty entries to the end (Sort moves empty entries to the front)
        empty = []
        while self.hotkeys is not None and self.hotkeys[0].prettyName == "":
            empty.append(self.hotkeys[0])
            self.hotkeys = self.hotkeys[1:]

        self.hotkeys += empty

    def install(self, override=True):
        """ Installs the keyset into maya

        :type override: object
        :return: If it was installed or not
        """

        if override and self.exists():
            cmds.hotkeySet(self.keySetName, delete=True, e=True)
        if self.exists():
            return False

        logger.debug("Installing hotkey set: {}".format(self.keySetName))
        # Source
        try:
            cmds.hotkeySet(self.keySetName, source=self.source, current=True)
        except RuntimeError:
            output.displayWarning("HotKeySet missing source, defaulting to {}, Please Save!."
                                  " KeySet {}, oldSource: {}".format(const.DEFAULT_KEYSET,
                                                                     self.keySetName, self.source))
            logger.debug("Creating hotkey set: {} with default zoo source because current source({})"
                         " no longer exists".format(self.keySetName, self.source))
            cmds.hotkeySet(self.keySetName, source=const.DEFAULT_KEYSET, current=True)

            # Runtime Commands
        for r in self._runtimeCmds:
            r.run()

        # Name commands
        for n in self._nameCmds:
            n.run()

        # Hotkey commands
        for h in self._hotkeyCmds:
            h.run()

        # hotkeyCTX commands
        for hctx in self._hotkeyCtxCmds:
            hctx.run()

    def exists(self):
        """
        Returns true if it already exists in Maya
        :return:
        """
        return cmds.hotkeySet(self.keySetName, exists=1)

    def setupHotkeys(self, hotkeyCmds='', nameCmds='', runtimeCmds='', hotkeyCtxCmds=''):

        # Use the classes attributes no command lists were given in
        if hotkeyCmds == '':
            hotkeyCmds = self._hotkeyCmds
        if nameCmds == '':
            nameCmds = self._nameCmds
        if runtimeCmds == '':
            runtimeCmds = self._runtimeCmds
        if hotkeyCtxCmds == '':
            hotkeyCtxCmds = self._hotkeyCtxCmds

        # Probably a better way to do this
        for h in hotkeyCmds:  # Populate the KeySet with hotkeys
            hotkey = hotkeys.Hotkey(hotkeyCmd=h)

            try:
                hotkey.ctxClient = h.cmdAttrs['ctxClient']
            except:
                pass

            # Get the info from the name commands
            for n in nameCmds:
                if n.cmdAttrs['cmdInput'] == hotkey.nameCommand:
                    hotkey.setNameCmd(n)
                    break

            if hotkey.runtimeCommand != "":
                for r in runtimeCmds:
                    if r.cmdAttrs['cmdInput'] == hotkey.runtimeCommand:
                        hotkey.setRuntimeCmd(r)
                        break
            else:
                pass

            self.hotkeys.append(hotkey)

    def saveMHK(self):
        """ Save MHK

        :return:
        """
        saveLoc = os.path.join(utils.hotkeyPathUserPrefs(), self.keySetName + ".mhk")
        cmds.hotkeySet(self.keySetName, e=1, export=saveLoc)
        logger.debug("File saved to {}".format(saveLoc))

    def save(self):
        """ Saves json to filePath

        :return:
        """
        self.updateHotkeys()
        hotkeyCmds = (o.cmdAttrs for o in self._hotkeyCmds)
        runtimeCmds = (o.cmdAttrs for o in self._runtimeCmds)
        nameCmds = (o.cmdAttrs for o in self._nameCmds)
        hotkeyCtxCmds = (o.cmdAttrs for o in self._hotkeyCtxCmds)

        hotkeySet = self.getHotkeySetDict()
        jsonExport = list(hotkeyCmds) + \
                     list(runtimeCmds) + \
                     list(nameCmds) + \
                     list(hotkeyCtxCmds) + \
                     [hotkeySet]
        filesystem.saveJson(jsonExport, self.filePath, indent=4)

        # We also need to install the key set into maya
        self.install()
        self.saveMHK()

    def updateHotkeys(self):
        """ Updates cmds array to get ready for saving

        :return:
        """
        for h in self.hotkeys:
            h.updateMHKCommands()

    def getHotkeySetDict(self):
        """ Get hotkeySet dict for json output

        :param self:
        :return:
        """

        ret = {
            "current": const.JSON_TRUE,
            "source": self.source,
            "cmdInput": self.keySetName,
            "cmdType": "hotkeySet"
        }

        return ret

    def setUpRuntimeCommand(self, selectedHotkey, runtimeCmdName, rtcType):
        """ Set up Runtime Command in the mhks classes


        :param selectedHotkey:
        :type selectedHotkey:
        :param runtimeCmdName:
        :type runtimeCmdName:
        :param rtcType:
        :type rtcType:
        :return:
        :rtype:
        """
        if selectedHotkey not in self.hotkeys:
            logger.error("Selected hotkey not found in current keyset! " + self.keySetName)

        if runtimeCmdName == "":
            self.clearHotkey(selectedHotkey)
            return

        runtimeCmd = self.getRuntimeCmdByName(runtimeCmdName)
        newNameCommandName = selectedHotkey.nameCommand

        nameCmd = self.getNameCmdByName(selectedHotkey.nameCommand)

        if rtcType == const.RTCTYPE_MAYA or rtcType == const.RTCTYPE_ZOO:
            # We only want to connect the name command to the runtime command for
            # Maya runtime commands and Zoo runtime commands
            selectedHotkey.mhkcmds.runtimeCmd = None
            selectedHotkey.runtimeCommand = runtimeCmdName
            selectedHotkey.category = ""
            selectedHotkey.commandScript = ""
            selectedHotkey.runtimeType = rtcType

        elif rtcType == const.RTCTYPE_CURRENT:
            # Runtime command exists in current keyset
            selectedHotkey.setRuntimeCmd(runtimeCmd)
            selectedHotkey.runtimeType = rtcType

        elif rtcType == const.RTCTYPE_NEW:
            # Runtime command doesn't exist, create a new one

            runtimeCmd = hotkeys.MHKCommand()
            runtimeCmd.setRuntimeCmd(runtimeCmdName, language=const.LANGUAGE_MEL, category=const.DEFAULT_CATEGORY,
                                     annotation=runtimeCmdName)
            self._runtimeCmds.append(runtimeCmd)
            selectedHotkey.setRuntimeCmd(runtimeCmd)

        # Name command set up
        if nameCmd is None:
            newNameCommand = hotkeys.MHKCommand()
            self._nameCmds.append(newNameCommand)
            selectedHotkey.mhkcmds.nameCmd = newNameCommand
            newNameCommand.setNameCommand(newNameCommandName, runtimeCmdName, const.LANGUAGE_MEL)

        selectedHotkey.modified = True

    def clearHotkey(self, hotkey):
        hotkey.category = ""
        hotkey.commandScript = ""
        hotkey.modified = True

        hotkey.mhkcmds.runtimeCmd = None
        hotkey.runtimeCommand = ""

    def deleteFromMaya(self):
        """ Removes keyset from maya

        :return:
        """
        if cmds.hotkeySet(self.keySetName, exists=1):
            cmds.hotkeySet(self.keySetName, e=1, delete=1)
        else:
            logger.warning("'{}' keyset doesn't exist.".format(self.keySetName))

    def deleteJson(self):
        """ Delete the json file

        :return:
        """
        path = os.path.join(utils.hotkeyPathUserPrefs(), "{}.json".format(self.keySetName))
        files = glob.glob(path)

        for f in files:
            os.remove(f)

    def deleteMHK(self):
        """ Delete the json file

        :return:
        """
        path = os.path.join(utils.hotkeyPathUserPrefs(), "{}.mhk".format(self.keySetName))
        files = glob.glob(path)

        for f in files:
            os.remove(f)

    def delete(self):
        """ Delete the keyset

        :return:
        """
        self.deleteFromMaya()
        self.deleteJson()
        self.deleteMHK()

    def getRuntimeCmdByName(self, runtimeCmdName):
        for r in self._runtimeCmds:
            if r.cmdAttrs['cmdInput'] == runtimeCmdName:
                return r

    def getNameCmdByName(self, nameCmdName):
        for n in self._nameCmds:
            if n.cmdAttrs['cmdInput'] == nameCmdName:
                return n
