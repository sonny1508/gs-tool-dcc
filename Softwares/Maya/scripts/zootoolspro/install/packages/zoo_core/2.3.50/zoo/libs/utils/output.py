import sys

try:  # pyside dependant
    from zoo.libs.pyqt import utils
except:
    pass

def _zooLoaded():
    if sys.version_info[0] < 3:
        import imp
        try:
            imp.find_module('zoo')
            found = True
        except ImportError:
            found = False
    else:
        import importlib
        spam_spec = importlib.util.find_spec("zoo")
        found = spam_spec is not None

    return found


if _zooLoaded():
    from zoo.core.util import env

if env.isMaya():
    from maya import cmds
    from maya.api import OpenMaya as om2


# todo maybe put this into core?
def displayInfo(txt):
    """ Display info based on application

    :param txt: Info text
    :return:
    """
    if _zooLoaded():
        if env.isMaya():
            om2.MGlobal.displayInfo(txt)
        else:
            print("Info: {}".format(txt))
    else:
        print("Info: {}".format(txt))


def displayWarning(txt):
    """ Display Warning based on application

    :param txt: warning
    :return:
    """

    if _zooLoaded():
        if env.isMaya():
            om2.MGlobal.displayWarning(txt)
        else:
            print("Warning: {}".format(txt))
    else:
        print("Warning: {}".format(txt))


def displayError(txt):
    """ Display Error based on application

    :param txt: error
    :return:
    """
    if _zooLoaded():
        if env.isMaya():
            om2.MGlobal.displayError(txt)
        else:
            print("ERROR: {}".format(txt))
    else:
        print("ERROR: {}".format(txt))


def clearViewMessage(position="botCenter", clear=True):
    if _zooLoaded():
        if env.isMaya():
            cmds.inViewMessage(position=position, clear=clear)


def inViewMessage(txt="Message highlight <hl>highlight</hl>.", position="botCenter", fade=True, textOffset=30,
                  fadeInTime=1, fadeOutTime=1, fadeStayTime=1500, alpha=1.0):
    try:  # pyside dependant can continue without
        textOffset = utils.dpiScale(int(textOffset))
    except:
        pass
    if _zooLoaded():
        if env.isMaya():
            cmds.inViewMessage(assistMessage=txt, position=position, fade=fade, textOffset=textOffset,
                               fadeInTime=fadeInTime, fadeOutTime=fadeOutTime, fadeStayTime=fadeStayTime, alpha=alpha)
