import sys

from zoo.core.util import env
from zoo.libs.maya.cmds.filemanage import saveexportimport
import subprocess, os
from maya import cmds


def saveCurrentScene():
    """ Save current scene

    Checks if the file has already been saved. Returns "save", "discard" or "cancel".

    If not saved opens "save", "discard" or "cancel" window.  Returns the button pressed if "discard" or "cancel"

    If "save" is clicked it will try to save the current file, if cancelled will return "cancel"

    :return: The button clicked returned as a lower case string "save", "discard" or "cancel"
    :rtype: str
    """
    # TODO move this into elements under maya cmds

    sceneModified = saveexportimport.fileModified()
    if not sceneModified:  # Has been saved already so continue
        saveexportimport.createNewScene()
        return "save"
    # Open dialog window with Save/Discard/Cancel buttons
    fullMessage = "Creating a new scene, save the current file?"
    from zoo.libs.pyqt.widgets import elements
    buttonPressed = elements.MessageBox.showSave(title="Save File", parent=None, message=fullMessage)
    if buttonPressed == "save":
        if saveexportimport.saveAsDialogMaMb():  # file saved
            return "save"
        else:
            return "cancel"
    return buttonPressed


def restartMaya(force=False, delay=3):
    """ Restarts maya with the same environment.

    Add delay in case maya takes a while to close and save.

    :return:
    """

    my_env = os.environ.copy()
    maya = sys.executable

    if env.isWindows():
        command = "ping -n {} 127.0.0.1 >nul & {}".format(delay, maya)
    else:
        command = "sleep {} && {}".format(delay, maya)

    subprocess.Popen(command, env=my_env, stdout=subprocess.PIPE, shell=True, stderr=subprocess.STDOUT)
    cmds.quit(force=force)
