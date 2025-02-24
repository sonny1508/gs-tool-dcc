import glob
import os
import re
import logging
import shutil

import maya.cmds as cmds
from zoo.apps.hotkeyeditor.core import const as c
from zoo.apps.hotkeyeditor.core import hotkeys
from zoo.apps.hotkeyeditor.core import utils
from zoo.core.util import filesystem


logger = logging.getLogger(__name__)


def parseMHK(mhkStr):
    """
    :param mhkStr:
    :return:
    """
    # Use Regex to get all the commands in the file

    regex = r"(^runTimeCommand.*?;$)|(^nameCommand.*?;$)|(^hotkeySet .*?;$)|(^hotkey .*?;$)|(^hotkeyCtx.*?;$)"

    matches = re.finditer(regex, mhkStr, re.MULTILINE | re.DOTALL)
    mhkCommands = []

    for matchNum, match in enumerate(matches):
        mhkCommands.append(match.group())

    # Put the matched data into an MHKCommand object
    mayaDefault = []
    for r in mhkCommands:
        mayaDefault.append(hotkeys.MHKCommand(melStr=r))

    return mayaDefault


def saveMHKs():
    # Save the MHK files first
    for k in c.KEYSETS:
        saveLoc = os.path.join(utils.hotkeyPathUserPrefs(), k + ".mhk")
        cmds.hotkeySet(k, e=1, export=saveLoc)
        logger.debug("File saved to {}".format(saveLoc))


def saveHotkeys():
    # Now open those mhk files and save it as JSON
    for k in c.KEYSETS:
        keySet = os.path.join(utils.hotkeyPathUserPrefs(), k + ".mhk")
        with open(keySet, "r") as f:
            mhkStr = f.read()
            f.close()
            mhkCommands = parseMHK(mhkStr)
            # Use Regex to get all the commands in the file
            saveJSON(mhkCommands, k)


def saveJSON(commands, outName):
    outData = []
    for cmd in commands:
        outData.append(cmd.cmdAttrs)

    fileOut = os.path.join(utils.hotkeyPathUserPrefs(), outName + ".json")
    filesystem.saveJson(outData, fileOut, indent=4)


def loadFromMHK():
    for k in c.KEYSETS:

        if cmds.hotkeySet(k, exists=1):
            cmds.hotkeySet(k, e=1, delete=1)

        path = os.path.join(utils.hotkeyPathUserPrefs(), k + ".mhk")

        utils.importKeySet(path)

    # Set the hotkeys
    cmds.hotkeySet(c.DEFAULT_MAYA, current=1, e=1)


def load():
    loadFromMHK()


def deleteZooKeySets(deletePrefHotkeys=True):
    """

    :param deletePrefHotkeys:
    :return:
    """
    deleteMayaKeySets()
    deleteUserJsons()

    if deletePrefHotkeys:
        deleteZooHotkeysFiles()


def deleteMayaKeySets():
    """ Deletes the Hotkey sets within the maya memory

    :return:
    """
    li = cmds.hotkeySet(q=1, hotkeySetArray=1)
    toDel = []
    for l in li:
        if l in c.KEYSETS:
            toDel.append(l)
        if utils.hasPrefix(c.KEYSET_PREFIX, l):
            toDel.append(l)

    for d in toDel:
        cmds.hotkeySet(d, e=1, delete=1)


def deleteUserJsons():
    """ Deletes all json files within zoo_preferences/prefs/maya/zoo_hotkey_editor

    :return:
    """
    path = os.path.join(utils.hotkeyPathUserPrefs(), "{}*.json".format(c.KEYSET_PREFIX))
    files = glob.glob(path)

    for f in files:
        os.remove(f)


def deleteZooHotkeysFiles():
    """ Deletes Everything under the hotkey preferences folder

    :return:
    """
    files = glob.glob(os.path.join(utils.hotkeyPathUserPrefs(), "*"))

    removed = set()
    for f in files:
        try:
            if os.path.isfile(f):
                os.remove(f)
                removed.add(f)
            elif os.path.isdir(f):
                shutil.rmtree(f)
                removed.add(f)
        except OSError:
            logger.error("Failed to remove File: {}".format(f),
                         exc_info=True)

    return removed
