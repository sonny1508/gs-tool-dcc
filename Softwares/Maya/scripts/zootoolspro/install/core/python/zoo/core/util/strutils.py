import os
import re

from zoovendor import six


def camelToNice(strInput, space=" "):
    """ Camel case to nicely formatted string

    eg. theQuickBrownFox ==> the Quick Brown Fox

    :param strInput: String to convert
    :type strInput: basestring
    :param space: The separator string, defaults to " "
    :type space: str
    :return: Combined string of the separator and the formatted string
    :rtype: basestring
    """
    splitted = re.sub('(?!^)([A-Z][a-z]+)', r' \1', strInput).split()
    ret = space.join(splitted)

    return ret


def titleCase(strInput):
    """ Turn to title case

    :param strInput:
    :type strInput: str
    :return: The resulting title case of a camel case string
    :rtype: str
    """
    if not strInput:
        return ''
    splitted = re.sub('(?!^)([A-Z][a-z]+)', r' \1', strInput).split()
    ret = " ".join(splitted)
    return ret.replace('_', ' ').title()


def newLines(text):
    """ Get new lines

    :param text:
    :return:
    :rtype: int
    """
    return text.count("\n")


def isStr(text):
    """ If text is a string

    :param text: Text to check if its a string
    :type text: object
    :return: is String
    :rtype: bool
    """
    return isinstance(text, six.string_types)


def fileSafeName(text, spaceTo=" ", keep=(" ", '_', '-')):
    """ Converts string to file safe name
    
    :type text: The File name
    :param keep: Characters to keep in the name
    :type keep: tuple or list
    :param spaceTo: Convert spaces to the following text.
    :type spaceTo: str
    :return:
    """
    filename = "".join([c for c in text if c.isalnum() or c in keep]).rstrip()
    filename = filename.replace(" ", spaceTo)
    return filename


def wordWrapPath(path, length=50):
    """ Format the path and add new lines. Mostly used for showing the path nicely in widgets
    Only for backslashes as it doesn't do this properly for windows/backslashes

    From:
    C:\\Users\\Documents\\zoo_preferences\\assets\\maya_scenes\\New_Project2\\scenes\\mayaScene.ma

    to:
    C:\\Users\\Documents\\zoo_preferences\\assets\\maya_scenes\\...
    ...\\New_Project2\\scenes\\mayaScene.ma

    :param path: The path to wordwrap
    :param length: The number of characters before moving the text into the new line
    :return:
    """

    splitted = path.split("\\")
    ret = splitted[0]
    row = len(splitted[0])
    for s in splitted[1:]:
        if row < length:
            row += len(s)
            ret += "\\" + s
            pass
        else:
            ret += "\\...\n..."
            row = 0

    return ret


def shortenPath(path, length=50):
    """ Truncates the inner path first depending on length

    C:\\hello\\world\\FinalPath
    C:\\...orld\\FinalPath
    C:\\...\\FinalPath
    todo: untested on linux/mac

    :param path:
    :param length:
    :return:
    """
    psplit = os.path.normpath(path).split(os.sep)

    ellipsisLen = 3
    retLen = len(psplit[0]) + 1 + len(psplit[-1]) + 1

    midStr = str(os.sep).join(psplit[1:-1])
    if len(midStr) + retLen < length:
        return path

    retLen += ellipsisLen  # ellipsis
    ret = psplit[0] + os.sep + "..." + midStr[retLen + len(midStr) - length:] + os.sep + psplit[-1]
    return os.path.normpath(ret)


def trailingNumber(name):
    """Returns the trailing number of a string, the name with the number removed, and the padding of the number

    Examples::

        "shaderName" returns "shaderName", None, 0
        "shaderName2" returns "shaderName", 2, 1
        "shader1_Name04" returns "shader1_Name", 4, 2
        "shaderName_99" returns "shaderName_", 99, 2
        "shaderName_0009" returns "shaderName_", 9, 4

    :param name:  The string name incoming
    :type name: str
    :return nameNumberless: The name now with the number removed, will be the same if no number found
    :rtype nameNumberless: str
    :return number: the number if one exists, will be None if no number finishes the string
    :rtype number: int
    :return padding: the padding of the number
    :rtype padding: int
    """
    m = re.search(r'\d+$', name)  # get the number as an object
    if m:
        numberAsString = m.group()  # find the number from it's pointer
        nameNumberless = name[:-len(numberAsString)]  # remove the number at string's end
        padding = len(numberAsString)
        return nameNumberless, int(numberAsString), padding
    return name, None, 0


def incrementName(name):
    """ Increment Name

    Examples:
        "obj"    --> "obj1"
        "obj2"   --> "obj3"
        "obj_5"  --> "obj_5"
        "obj_02" --> "obj_03"

    :param name: the name to increment
    :type name: str
    :return: The new name
    :rtype: str
    """
    strOnly, number, currentPadding = trailingNumber(name)

    if number is None:
        return name + "1"

    return strOnly + str(number + 1).zfill(currentPadding)

def findNonAscii(fn):
    found = ""
    validPath = True
    for ch in fn:
        if ord(ch) < 128:
            found += " "
        else:
            found += "^"
            validPath = False

    return validPath, found

def isAscii(fn):
    return all(ord(ch) < 128 for ch in fn)
