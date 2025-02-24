"""saving exporting and importing and references

from zoo.libs.maya.cmds.filemanage import saveexportimport
saveexportimport.multipleImport("D:/aFile.ma", duplicates=4, namespace="xx")

"""

import os

from maya import cmds, mel

from zoo.libs.maya.cmds.workspace import mayaworkspace
from zoo.libs.pyqt.widgets.popups import MessageBox
from zoo.libs.utils import output


def fileModified():
    """Checks if the current scene has been modified, returns True if it needs saving.

    :return: True is there have been modifications to the current scene
    :rtype: bool
    """
    return cmds.file(query=True, modified=True)


def untitledFileName():
    """Returns the default maya file name i.e. untitled
    :rtype: str
    """
    return mel.eval("untitledFileName()")


def isCurrentSceneUntitled():
    """Determines if the current maya scene is the default untitled file path
    :rtype: bool
    """
    return len(currentSceneFilePath()) == 0


def isPathUntitled(path):
    """Determines if the provided path is an untitled file i.e. mayas default untitled scene

    :param path: The File Path to check
    :type path: str
    :rtype: bool
    """
    return os.path.basename(path).startswith(untitledFileName())


def currentSceneFilePath():
    """Returns the current full file path name of the scene, will be "" if not saved

    :return: The full file path of the current scene
    :rtype: str
    """
    return cmds.file(query=True, sceneName=True, shortName=False)  # The current filename of the scene


def saveAsDialogMaMb(windowCaption="Save File", directory="", okCaption="OK"):
    """Pops up a save file dialog and save's to the new path, returns the name of the file to save.

    :return: The path of the file saved, if cancelled will be "".
    :rtype: str
    """
    if not directory:
        # get the current file location
        currentFilePath = cmds.file(query=True, sceneName=True, shortName=False)  # the current filename
        if not currentFilePath:  # is an unsaved file
            directory = mayaworkspace.getProjSubDirectory(sudDirectory="scenes")
        else:
            directory = os.path.split(currentFilePath)[0]  # the directory path
    multipleFilters = "Maya Files (*.ma *.mb);;Maya ASCII (*.ma);;Maya Binary (*.mb)"
    filePath = cmds.fileDialog2(fileFilter=multipleFilters,
                                caption=windowCaption,
                                startingDirectory=directory,
                                okCaption=okCaption)
    if not filePath:
        return filePath
    if filePath:  # Is a list so make a string path
        filePath = filePath[0]
    # Save file
    if filePath.split(".")[-1] == "ma":  # Need to force lower
        cmds.file(rename=filePath)
        cmds.file(force=True, type='mayaAscii', save=True)
    if filePath.split(".")[-1] == "mb":  # Need to force lower
        cmds.file(rename=filePath)
        cmds.file(force=True, type='mayaBinary', save=True)
    output.displayInfo("Success: File saved `{}`".format(filePath))
    return filePath


def sceneModifiedDialogue():
    """Checks if the file has already been saved. Returns "save", "discard" or "cancel".

    If not saved opens "save", "discard" or "cancel" window.  Returns the button pressed if "discard" or "cancel"

    If "save" is clicked it will try to save the current file, if cancelled will return "cancel"

    :return: The button clicked returned as a lower case string "save", "discard" or "cancel"
    :rtype: str
    """
    sceneModified = fileModified()
    if not sceneModified:  # Has been saved already so continue
        createNewScene()
        return "save"
    # Open dialog window with Save/Discard/Cancel buttons
    fullMessage = "Creating a new scene, save the current file?"
    buttonPressed = MessageBox.showSave(title="Save File", parent=None, message=fullMessage)
    if buttonPressed == "save":
        if saveAsDialogMaMb():  # file saved
            return "save"
        else:
            return "cancel"
    return buttonPressed


def createNewScene(force=True):
    """Creates a new maya scene

    :param force: Will force a new scene even if the current scene has not been saved, False will error if not saved
    :type force: bool
    """
    cmds.file(newFile=True, force=force)


def asciiOrBinary(filePath):
    if filePath.split(".")[-1] == "ma":  # Need to force lower
        return 'mayaAscii'
    elif filePath.split(".")[-1] == "mb":  # Need to force lower
        return 'mayaBinary'
    else:
        return None


def importAllReferences():
    # Get a list of all the current references.  They in turn
    # may reference other things that will be exposed once
    # they are imported:
    allrefs = cmds.file(query=True, reference=True)
    for ref in allrefs:
        try:
            cmds.file(ref, importReference=True)
        except RuntimeError:
            pass
        # See if there are any new references to import:
        newrefs = cmds.file(query=True, reference=True)
        if len(newrefs):
            allrefs += newrefs


def multipleReference(filePath, duplicates=4, namespace="xx", ):
    """References multiple files into the scene

    :param filePath: The full path of the file to import, must be a .ma or .mb file
    :type filePath: str
    :param duplicates: How many times to import the file
    :type duplicates: int
    :param namespace: The name of the namespace, will increment with each import xx0, xx1, xx2 etc
    :type namespace: str
    :return: success if the import was successful
    :rtype: bool
    """
    for i in range(duplicates):
        # get the file extension
        asciiBinary = asciiOrBinary(filePath)
        if not asciiBinary:
            output.displayError("File extension not recognised `{}`".format(filePath))
            return
        # add a number to the namespace
        nspc = "".join([namespace, str(i + 1)])
        cmds.file(filePath, reference=True, type=asciiBinary, ignoreVersion=True, namespace=nspc, options="v=0;")


def multipleImport(filePath, duplicates=4, namespace="xx"):
    """Import a file multiple times in the scene

    :param filePath: The full path of the file to import, must be a .ma or .mb file
    :type filePath: str
    :param duplicates: How many times to import the file
    :type duplicates: int
    :param namespace: The name of the namespace, will increment with each import xx0, xx1, xx2 etc
    :type namespace: str
    :return: success if the import was successful
    :rtype: bool
    """
    for i in range(duplicates):
        # get the file extension
        asciiBinary = asciiOrBinary(filePath)
        if not asciiBinary:
            output.displayError("File extension not recognised `{}`".format(filePath))
            return False
            # add a number to the namespace
        nspc = "".join([namespace, str(i + 1)])
        cmds.file(filePath, i=True, type=asciiBinary, ignoreVersion=True, namespace=nspc, options="v=0;",
                  mergeNamespacesOnClash=False, importTimeRange="combine", renameAll=True, preserveReferences=True)
    return True

