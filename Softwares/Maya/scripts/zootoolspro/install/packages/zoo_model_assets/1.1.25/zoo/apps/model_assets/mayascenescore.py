import os
import webbrowser

from maya import cmds
from zoo.libs.maya.cmds.filemanage import saveexportimport
from zoo.libs.maya.cmds.workspace import mayaworkspace
from zoo.libs.maya.utils import scene, files
from zoo.libs.pyqt.widgets import elements
from zoo.libs.utils import output, filesystem, general
from zoo.core.util import strutils
from zoo.preferences.interfaces import assetinterfaces

if general.TYPE_CHECKING:
    import zoo.libs.pyqt.extended.imageview.items.BaseItem

from zoo.core.util import zlogging

logger = zlogging.getLogger(__name__)


class MayaScenesCore(object):
    def __init__(self, toolsetWidget):
        """

        :type toolsetWidget: :class:`zoo.apps.uitoolsets.mayascenes.MayaScenes`
        :param toolsetWidget:
        """
        self._toolsetWidget = toolsetWidget
        self.directory = None
        self.selectedItem = None  # type: zoo.libs.pyqt.extended.imageview.items.BaseItem
        self.mayaScenesPrefs = assetinterfaces.mayaScenesInterface()

    def saveScene(self, directory, type_="mayaAscii"):
        """

        :param directory:
        :type directory:
        :param type_: "mayaAscii" or "mayaBinary"
        :type type_: str
        :return:
        :rtype:
        """

        forcedType = self._forcedType()
        if forcedType:
            type_ = forcedType
            logger.debug("Unknown node/plugins found. Forcing save type: '{}'".format(forcedType))

        fileName = self.prepareSave(directory, type_)

        if not fileName:
            return

        cmds.file(rename=fileName)
        cmds.file(save=True, type=type_)
        output.displayInfo('Success: File Saved "{}"'.format(fileName))

    def _forcedType(self):
        """ If there are unknown nodes, plugins it needs to save to the correct file type

        :return:
        """
        if scene.hasUnknownNodes() or scene.hasUnknownPlugins():
            return files.mayaFileType(message=False)

    def exportSelected(self, directory, type_="mayaAscii"):
        """ Export selected into directory

        :param directory:
        :param type_:
        :return:
        """

        forcedType = self._forcedType()
        if forcedType:
            type_ = forcedType
            logger.debug("Unknown node/plugins found. Forcing save type: '{}'".format(forcedType))

        fileName = self.prepareSave(directory, type_)
        if not fileName:
            return
        cmds.file(rename=fileName)
        cmds.file(exportSelected=True, type=type_)
        output.displayInfo('Success: File Exported "{}"'.format(fileName))

    def prepareSave(self, directory, type_="mayaAscii"):
        name = self.sceneNameInput()
        fileExt = "ma" if type_ == "mayaAscii" else "mb"

        if not name:
            output.displayInfo("File save cancelled.")
            return

        folderName = self.prepareFolder(directory, name)
        name = strutils.fileSafeName(name)
        folderFullPath = os.path.join(directory, folderName)
        fileName = os.path.join(folderFullPath, os.path.extsep.join([name, fileExt]))
        if os.path.exists(fileName):
            uniqueName = filesystem.uniqueFileName(folderFullPath)
            choice, _ = elements.MessageBox.showMultiChoice(title="Existing file found",
                                                            message="File already exists. Override?",
                                                            choices=["Override.", "Rename to '{}'".format(
                                                                os.path.basename(uniqueName))],
                                                            buttonB="Cancel")

            if choice == 0:
                fileName = fileName
            elif choice == 1:
                newName = uniqueName
                fileName = os.path.normpath(os.path.join(folderFullPath, os.path.extsep.join([newName, fileExt])))
            else:
                return
        return fileName

    def prepareFolder(self, directory, name):
        folderName = strutils.fileSafeName(name, spaceTo="_")
        customFolder = os.path.join(directory, folderName)
        if not os.path.exists(customFolder):
            os.mkdir(customFolder)
        return folderName

    def sceneNameInput(self):
        name = elements.MessageBox.inputDialog(title="Scene Name", parent=self._toolsetWidget.window(),
                                               message="New Scene Name: ")

        return name

    def filePath(self, message=True):
        """ Returns the file path of the currently selected thumbnail's corresponding .ma or .mb image eg:

            C:\\Users\\name\\Documents\\zoo_preferences\\assets\\rmaya_scenes\\croc_rig\\animation_croc_walkAndTurn.ma

        :param message: Report any messages to the user?
        :type message: bool
        :return filePath: the full path of the file of the selected thumb, will be "" if none selected
        :rtype filePath: str
        """
        try:
            return self.selectedItem.filePath
        except AttributeError:
            if message:
                output.displayWarning("No thumbnail is selected in the browser.  Please select an image.")
            return ""

    def importScene(self, assetName=""):
        """ Imports the zooScene asset given the GUI settings
        """
        path = self.filePath()
        if not path:
            output.displayWarning("Thumbnail not selected or file path not found: {}".format(path))
            return
        if path.lower().endswith(".ma"):
            mayaType = "mayaAscii"
        elif path.lower().endswith(".mb"):
            mayaType = "mayaBinary"
        else:
            output.displayWarning("This path has an unknown file type, not .ma or .mb")
            return
        kwargs = dict(
            force=1, options="v=0;", ignoreVersion=1, type=mayaType, i=1
        )
        namespace = elements.MessageBox.inputDialog(parent=self._toolsetWidget,
                                                    title="Namespace",
                                                    message="Please Enter the namespace you would Like.",
                                                    text="")
        if namespace is None:
            return
        elif namespace: # ignore empty string
            kwargs["namespace"] = namespace
        kwargs["preserveReferences"] = True
        output.displayInfo("Import scene options: {}".format(kwargs))
        output.displayInfo("Imported scene: {}".format(path))
        # todo should handle name conflicts better, filenames are junk it conflicts
        cmds.file(path, **kwargs)

    def openReadme(self):
        """Opens the readMe.pdf stored with the thumbnail selection if it exists
        """
        directory = self.thumbDirectory()
        if not directory:
            return
        readMeFile = os.path.join(directory, "readMe.pdf")
        if not os.path.exists(readMeFile):
            output.displayWarning("No readme.pdf was found for this file.")
            return
        webbrowser.open(readMeFile)
        output.displayInfo("ReadMe.pdf opened {}".format(readMeFile))

    def referenceScene(self):
        """ Reference in the scene
        """
        path = self.filePath()
        if not path:
            output.displayWarning("No thumbnail is selected in the browser.  Please select an image.")
            return

        if mayaworkspace.switchWorkspace(path) == "CANCEL":
            return
        namespace = elements.MessageBox.inputDialog(parent=self._toolsetWidget,
                                                    title="Namespace",
                                                    message="Please Enter the namespace you would Like.",
                                                    text=self.selectedItem.fileName)
        if namespace is None:
            return
        elif not namespace:
            namespace = self.selectedItem.fileName
        cmds.file(path,
                  reference=1, ignoreVersion=1, groupLocator=1,
                  mergeNamespacesOnClash=False, namespace=namespace, options="v=0;p=17;f=0")

    def loadScene(self, assetName=""):
        """ Imports the zooScene asset given the GUI settings
        """
        path = self.filePath()
        if not path:
            return
        dialogResult = saveexportimport.sceneModifiedDialogue()  # Dialog popup save scene?
        if dialogResult == "cancel":
            return

        if mayaworkspace.switchWorkspace(self.selectedItem.filePath) == "CANCEL":
            return
        cmds.file(self.selectedItem.filePath, force=1, options="v=0;", ignoreVersion=1, open=1)

    def thumbDirectory(self, message=True):
        """Returns the directory path of the currently selected thumb

        :param message: Report any messages to the user?
        :type message: bool
        :return directory: the path of the directory of the currenlty selected thumb, will be "" if none selected
        :rtype directory: str
        """
        path = self.filePath(message=message)
        if not path:
            return ""
        directory = os.path.dirname(path)
        return directory

    def openHelp(self):
        """The help file url will be stored in a text file in the same directory as the maya file called "helpUrl.txt"

        The contents of that file is the url to the help location.
        """
        directory = self.thumbDirectory()
        if not directory:
            return
        helpTxtFile = os.path.join(directory, "helpUrl.txt")
        if not os.path.exists(helpTxtFile):
            output.displayWarning("No help url was found for this file.")
            return
        url = filesystem.loadFileTxt(helpTxtFile)
        webbrowser.open(url)
        output.displayInfo("Help page opened {}".format(url))

    def mayaScenesFolder(self):
        """ Get maya scenes folder

        :return:
        """
        return self.mayaScenesPrefs.scenesAssets.zooPrefsPath()

    @property
    def uniformIcons(self):
        return self.mayaScenesPrefs.scenesAssets.browserUniformIcons()

    @uniformIcons.setter
    def uniformIcons(self, value):
        self.mayaScenesPrefs.scenesAssets.setBrowserUniformIcons(value)

    def browserDirectory(self):
        return self._toolsetWidget.currentWidget().browserModel.directories[0].path  # todo: fix this

    def deleteScene(self, item):
        """

        :param item:
        :type item: zoo.libs.pyqt.extended.imageview.items.BaseItem
        :return:
        """
        deleted = []
        os.remove(item.filePath)
        deleted.append(os.path.basename(item.filePath))
        if item.thumbnailExists():
            os.remove(item.thumbnail)
            deleted.append(os.path.basename(item.thumbnail))

        # Delete folder if nothing in folder
        if len(os.listdir(item.directory)) == 0:
            os.rmdir(item.directory)
            deleted.append(item.directory)

        return deleted
