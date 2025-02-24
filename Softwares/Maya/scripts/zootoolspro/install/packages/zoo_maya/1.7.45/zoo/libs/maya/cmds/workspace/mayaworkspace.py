import os

import maya.cmds as cmds
import maya.api.OpenMaya as om2
import maya.mel as mel
from zoo.libs.pyqt.widgets.popups import MessageBox

from zoo.core.util import strutils


def getCurrentMayaWorkspace():
    """Returns the current project directory

    :return projectDirectoryPath: the path of the current Maya project directory
    :rtype projectDirectoryPath: str
    """
    return cmds.workspace(q=True, rootDirectory=True)


def getProjSubDirectory(sudDirectory="scenes", message=True):
    """Returns the path of the current Maya project sub directory Eg:

        /scenes/
        or
        /sourceImages/
        etc

    Note: If not found will default to the home directory of your OS.

    :param sudDirectory: The subDirectory of the project directory, can be multiple directories deep
    :type sudDirectory: str
    :param message: Warn the user if the path wasn't found?
    :type message: bool
    :return directoryPath: The path of the directory
    :rtype directoryPath: str
    """
    projectDir = getCurrentMayaWorkspace()
    directory = os.path.join(projectDir, sudDirectory)
    if not os.path.isdir(directory):  # Doesn't exist so set to Home directory
        homeDirectory = os.path.expanduser("~")  # home directory
        om2.MGlobal.displayWarning("Directory `{}` doesn't exist, setting to `{}`".format(directory, homeDirectory))
        directory = homeDirectory
    return directory


def switchWorkspace(path):
    """ Switch workspace to path. Displays a message box before showing.

    If it's the same workspace, nothing will happen.

    :param path:
    :return:
    """

    workspace = findWorkspaceFromScene(path)

    if workspace:
        outStr = strutils.shortenPath(workspace, )

        res = MessageBox.showQuestion(title="Set Maya Project?",
                                      message="Project detected. Would you like to switch the project to:\n\n {}? ".format(
                                          outStr), buttonA="Yes", buttonB="No", buttonC="Cancel")

        if res == "A":
            setProject(workspace)
            return "CHANGED"
        elif res == "B":
            return "NO"

        return "CANCEL"


def findWorkspaceFromScene(path, maxDepth=999):
    """ Find workspace from maya scene path

    "C:/maya_project/scenes/hello.ma" -> "C:/maya_project/"

    :param path:
    :return:
    """
    fileDir = os.path.dirname(path)
    dirPos = fileDir

    for i in range(maxDepth):
        parentDir = os.path.dirname(dirPos)
        if fileDir == parentDir: # base directory
            return

        workspace = os.path.normpath(os.path.join(parentDir, "workspace.mel"))

        currWorkspace = os.path.normpath(getCurrentMayaWorkspace())
        if os.path.exists(workspace) and os.path.normpath(parentDir) != currWorkspace:  # If its already set, ignore.
            return os.path.normpath(parentDir)

        dirPos = parentDir


def setProject(path):
    """ Sets the maya project to path.

    :param path:
    :return:
    """
    newProj = path.replace("\\", "\\\\")
    mel.eval('setProject \"' + newProj + '\"')
