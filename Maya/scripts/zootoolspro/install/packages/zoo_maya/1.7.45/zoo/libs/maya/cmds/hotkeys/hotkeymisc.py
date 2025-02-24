"""Misc Hotkey Set Functions.  Note Zoo Hotkey Editor related functions see the package zoo_hotkey_editor


from zoo.libs.maya.cmds.hotkeys import hotkeymisc
keyMap = hotkeymisc.getAssignCommandsMap()
hotkeymisc.niceHotkeyFromName("combinePolygons", keyMap)


from zoo.libs.maya.cmds.hotkeys import hotkeymisc
hotkeymisc.nameFromHotkey("q", altModifier=False, commandModifier=False, ctrlModifier=False, shiftModifier=False)


"""
from maya import cmds

from zoo.libs.maya.utils import mayaenv

MAYA_VERSION = mayaenv.mayaVersion()


def getAssignCommandsMap():
    count = cmds.assignCommand(query=True, numElements=True) or 0
    toolsPackage = {}

    for index in range(1, count + 1):
        cmd = cmds.assignCommand(index, query=True, command=True)
        if len(cmd):
            toolsPackage[cmd] = index
    return toolsPackage


def getAssignCommandHotkey2020(index):
    keyString = cmds.assignCommand(index, query=True, keyString=True)

    if not (len(keyString) > 0 and keyString[0] != "NONE"):
        return ''

    isLower = len(keyString[0]) == 1 and keyString[0].islower()
    isMacOS = cmds.about(mac=True)

    if isMacOS:
        keys = {
            'control': 'Ctrl',
            'alt': u'Atl',
            'shift': u'Shift',
            'super': u'Cmd'
        }
    else:
        keys = {
            'control': 'Win',
            'alt': 'Alt',
            'shift': 'Shift',
            'super': 'Ctrl'
        }

    displayString = []

    if "1" == keyString[5]: displayString.append(keys['control'])
    if "1" == keyString[1]: displayString.append(keys['alt'])
    if len(keyString[0]) == 1 and keyString[0].isupper():
        displayString.append(keys['shift'])
    if "1" == keyString[2]: displayString.append(keys['super'])

    if keyString[0].lower() == 'left':
        displayString.append('left')
    elif keyString[0].lower() == 'right':
        displayString.append('right')
    elif keyString[0].lower() == 'del':
        displayString.append('del')
    elif isLower:
        displayString.append(keyString[0].upper())
    else:
        displayString.append(keyString[0])

    if isMacOS:
        return ''.join(displayString)
    else:
        return '+'.join(displayString)


def getHotkeyIndex(keyMap, command):
    try:
        return keyMap.get(command)
    except TypeError:
        return None


def hotkeyFromName(command, keyMap):
    """Returns the hotkey for tooltips and menus as a string:

        "Shift+Ctrl+I"

    Or if not a hotkey:

        "" (as a string)

    :param command:
    :type command:
    :param keyMap:
    :type keyMap:
    :return:
    :rtype:
    """
    index = getHotkeyIndex(keyMap, command)
    if index is None:
        return ""
    """if MAYA_VERSION > 2020:
        from maya.app.TTF import utils
        data = utils.getAssignCommandHotkey(index)
        return data"""
    # All versions as some users are reporting issues with 2022
    keyInfo = cmds.assignCommand(index, query=True, keyString=True)
    if not keyInfo:
        return ""
    return getAssignCommandHotkey2020(index)


def niceHotkeyFromName(hkName, keyMap):
    """Returns the hotkey for tooltips and menus in a nice form:

        "Shift+Ctrl+I"

    Or if not a hotkey:

        "None" (as a string)

    Generate a keymap with getAssignCommandsMap():

        keyMap = getAssignCommandsMap()

    :param hkName:
    :type hkName:
    :param keyMap:
    :type keyMap:
    :return:
    :rtype:
    """
    hotkey = hotkeyFromName(hkName, keyMap)
    if not hotkey:
        return "None"
    return hotkey


def nameFromHotkey(key, altModifier=False, commandModifier=False, ctrlModifier=False, shiftModifier=False):
    """Returns the named command that the key is assigned to, None if none.

    :param key: The key to query
    :type key: str
    :param altModifier: Is the alt key pressed?
    :type altModifier: bool
    :param commandModifier:  Is the command key pressed?
    :type commandModifier: bool
    :param ctrlModifier:  Is the ctrl key pressed?
    :type ctrlModifier: bool
    :param shiftModifier:  Is the shift key pressed?
    :type shiftModifier: bool
    :return: The named command that the key is assigned to, None if none.
    :rtype: str
    """
    return cmds.hotkey(key,
                       altModifier=altModifier,
                       commandModifier=commandModifier,
                       ctrlModifier=ctrlModifier,
                       shiftModifier=shiftModifier,
                       query=True, name=True)