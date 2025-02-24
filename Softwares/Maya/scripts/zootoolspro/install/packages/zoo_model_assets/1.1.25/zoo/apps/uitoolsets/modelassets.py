import os
from functools import partial

from zoo.core.util import env

if env.isMaya():
    from maya import cmds
    from zoo.libs.maya.cmds.assets import assetsimportexport
    from zoo.libs.maya.cmds.objutils import namehandling
    from zoo.libs.maya.cmds.renderer import rendererload, exportabcshaderlights


from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.apps.toolsetsui.widgets.toolsetresizer import ToolsetResizer
from zoo.apps.toolsetsui.mixins import MiniBrowserMixin
from zoo.apps.toolsetsui.ext.renderers import RendererMixin
from zoo.libs.zooscene import zooscenefiles
from zoo.libs.pyqt.extended.imageview.models import zooscenemodel
from zoo.libs.pyqt import keyboardmouse
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements
from zoo.libs.utils import output

from zoo.preferences.interfaces import assetinterfaces, coreinterfaces

from zoo.core.util import zlogging

from zoovendor.Qt import QtWidgets


logger = zlogging.getLogger(__name__)


DFLT_RNDR_MODES = [("arnold", "Arnold"), ("redshift", "Redshift"), ("renderman", "Renderman")]
REPLACE_COMBO = ["Replace Asset By Type", "Replace All Assets", "Add To Scene"]
UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1


class AlembicAssets(toolsetwidget.ToolsetWidget, RendererMixin, MiniBrowserMixin):
    id = "alembicAssets"
    uiData = {"label": "Alembic Assets (Multi-Renderer)",
              "icon": "packageAssets",
              "tooltip": "Mini browser for alembic models and dynamic shaders",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-model-assets/"
              }

    # ------------------------------------
    # START UP
    # ------------------------------------

    def preContentSetup(self):
        """First code to run"""
        self.toolsetWidget = self  # needed for callback decorators
        self.modelAssetsPrefInterface = assetinterfaces.modelAssetsInterface()
        self.setAssetPreferences(self.modelAssetsPrefInterface.modelAssetsPreference)
        self.initRendererMixin(disableVray=True, disableMaya=True)  # sets the renderer


    def contents(self):
        """The UI Modes to build, compact, medium and or advanced """
        return [self.initCompactWidget(), self.initAdvancedWidget()]

    def initCompactWidget(self):
        """Builds the Compact GUI (self.compactWidget) """
        self.compactWidget = GuiCompact(parent=self, properties=self.properties, toolsetWidget=self)
        return self.compactWidget

    def initAdvancedWidget(self):
        """Builds the Advanced GUI (self.advancedWidget) """
        self.advancedWidget = GuiAdvanced(parent=self, properties=self.properties, toolsetWidget=self)
        return self.advancedWidget

    def postContentSetup(self):
        """Last of the initialize code"""
        self.setMiniBrowsers([w.miniBrowser for w in self.widgets()])
        self.uiconnections()
        self.disableStartEndFrame()  # set embed window int boxes disabled state

    def currentWidget(self):
        """ Current active widget

        :return:
        :rtype:  :class:`AllWidgets`
        """
        return super(AlembicAssets, self).currentWidget()

    def widgets(self):
        """ List of widgets

        :return:
        :rtype: list[:class:`AllWidgets`]
        """
        return super(AlembicAssets, self).widgets()

    # ------------------------------------
    # PROPERTIES
    # ------------------------------------

    def initializeProperties(self):
        return [{"name": "rendererIconMenu", "label": "", "value": "Arnold"}]


    # ------------------------------------
    # THUMBNAIL
    # ------------------------------------

    def refreshThumbs(self):
        """Refreshes the GUI """
        self.currentWidget().miniBrowser.refreshThumbs()

    # ------------------------------------
    # RENDERER - AND SEND/RECEIVE ALL TOOLSETS
    # ------------------------------------

    def checkRenderLoaded(self, renderer):
        """Checks that the renderer is loaded, if not opens a window asking the user to load it

        :param renderer: the nice name of the renderer "Arnold" or "Redshift" etc
        :type renderer: str
        :return rendererLoaded: True if the renderer is loaded
        :rtype rendererLoaded: bool
        """
        logger.debug("checkRenderLoaded()")
        if not rendererload.getRendererIsLoaded(renderer):
            okPressed = self.ui_loadRenderer(renderer)
            if not okPressed:
                return False
            return rendererload.loadRenderer(renderer)
        return True

    # ------------------------------------
    # DOTS MENU
    # ------------------------------------

    def exportGenericAlembic(self):
        """Exports all geo, cams and lights in the scene/selected as generic type .zooScene:

            - Objects.geo and cameras are saved as alembic
            - Lights saved as generic .zooLights
            - Shaders saved as generic .zooShaders

        """
        # Get UI data
        renderer = self.properties.rendererIconMenu.value
        exportSelected = not self.properties.fromSelectedRadio.value
        frameRange = ""
        if self.properties.animationRadio.value:
            frameRange = " ".join([str(self.properties.startFrameInt.value),
                                   str(self.properties.endFrameInt.value)])
        # Get Model Asset directory


        # Check can export
        if exportSelected and not cmds.ls(selection=True):
            output.displayWarning("Nothing Selected, Please Select Object/s")
            return

        modelAssetsDirectory = self.currentWidget().miniBrowser.getSaveDirectory()
        if not modelAssetsDirectory:
            return
        name = elements.MessageBox.inputDialog(title="Scene Name", parent=self,
                                               message="New Scene Name: ")
        if not name:
            return

        fullFilePath = os.path.join(modelAssetsDirectory,
                                    os.path.extsep.join((name, exportabcshaderlights.ZOOSCENESUFFIX))
                                    )
        # Save
        assetsimportexport.saveAsset(fullFilePath, renderer,
                                     exportSelected=exportSelected,
                                     exportShaders=True,
                                     exportLights=False,
                                     exportAbc=True,
                                     noMayaDefaultCams=True,
                                     exportGeo=True,
                                     exportCams=True,
                                     exportAll=False,
                                     dataFormat="ogawa",
                                     frameRange=frameRange,
                                     visibility=True,
                                     creases=True,
                                     uvSets=True,
                                     exportSubD=True)
        # Refresh browser UIs
        self.refreshThumbs()
        return fullFilePath

    def renameAsset(self):
        """Renames the asset on disk, can fail if alembic animation. Alembic animation must not be loaded"""
        miniBrowser = self.currentWidget().miniBrowser
        currentFileNoSuffix = miniBrowser.itemFileName()
        if not currentFileNoSuffix:  # no image has been selected
            output.displayWarning("Please select an asset thumbnail image to rename.")
            return
        message = "Rename Related `{}` Files As:".format(currentFileNoSuffix)
        renameText = elements.MessageBox.inputDialog(title="Rename Model Asset",
                                                     text=currentFileNoSuffix, parent=None,
                                                     message=message)
        if not renameText:
            return

        zooScenePath = miniBrowser.itemFilePath()
        # Do the rename
        fileRenameList = zooscenefiles.renameZooSceneOnDisk(renameText, zooScenePath)
        if not fileRenameList:
            output.displayWarning("Files could not be renamed, they are probably in use by the current scene. "
                                  "Do not have the renamed assets loaded in the scene, "
                                  "or check your file permissions.")
            return
        output.displayInfo(
            "Success: Files `{}*` Have Been Renamed To `{}*`".format(currentFileNoSuffix, renameText))
        self.refreshThumbs()

    def deletePresetPopup(self):
        """Popup window that asks the user if they want to delete the currently selected asset from disk?"""
        fileNameNoSuffix = self.currentWidget().browserModel.currentImage
        filenameWithSuffix = "{}.{}".format(fileNameNoSuffix, exportabcshaderlights.ZOOSCENESUFFIX)
        zooScenePath = os.path.join(os.path.dirname(self.currentWidget().miniBrowser.itemFilePath()),
                                    filenameWithSuffix)
        # Build popup window
        message = "Warning: Delete the preset `{}` and it's dependencies?  " \
                  "This will permanently delete these file/s from disk?".format(filenameWithSuffix)
        result = elements.MessageBox.showOK(title="Delete Asset From Disk?",
                                            message=message)  # None will parent to Maya
        # After answering Ok or cancel
        if result:  # Ok was pressed
            filesFullPathDeleted = zooscenefiles.deleteZooSceneFiles(zooScenePath, message=True)
            self.refreshThumbs()
            output.displayInfo("Success, File/s Deleted: {}".format(filesFullPathDeleted))

    # ------------------------------------
    # MANAGE IN SCENE
    # ------------------------------------

    def selectPackageRootGrpsInScene(self):
        """Selects all package asset grps from selected, if none found then tries from the UI selection
        """
        uiSelectedName = self.getImageNameWithoutExtension()
        assetsimportexport.selectZooAssetGrps(uiSelectedName=uiSelectedName)

    def getImageNameWithoutExtension(self):
        """Returns the name of the current selection in the browser without the file extension
        Handles the Maya version of the name which cannot have spaces etc

        :return uiSelectedName: the selection without file extension, Maya name with "_". None if nothing selected
        :rtype uiSelectedName: str
        """
        uiSelectedName = self.currentWidget().browserModel.currentImage
        if uiSelectedName:
            uiSelectedName = os.path.splitext(uiSelectedName)[0]
            uiSelectedName = namehandling.convertStringToMayaCompatibleStr(uiSelectedName)
        return uiSelectedName

    @toolsetwidget.ToolsetWidget.undoDecorator
    def deleteAssetInScene(self):
        """Removes the package asset from the scene
        Tries the selected objects package, if not found will try the UI name matches
        * needs undo support
        """
        uiSelectedName = self.getImageNameWithoutExtension()  # TODO probably missing
        assetsimportexport.deleteZooAssetSelected(uiSelectedName=uiSelectedName)

    # ------------------------------------
    # ALEMBIC MANAGEMENT
    # ------------------------------------

    def loadAbcPopup(self):
        """The popup window if alembic plugins aren't loaded
        """
        message = "The Alembic (.abc) plugins need to be loaded. \nLoad Now?"
        result = elements.MessageBox.showOK(title="Load Alembic Plugin?",
                                            message=message)  # None will parent to Maya
        if result:
            assetsimportexport.loadAbcPlugin()
        return result

    def checkAbcLoaded(self):
        """Checks if the alembic plugins are loaded
        """
        if not assetsimportexport.getPluginAbcLoaded()[0] or not assetsimportexport.getPluginAbcLoaded()[1]:
            result = self.loadAbcPopup()
            return result
        return True

    @toolsetwidget.ToolsetWidget.undoDecorator
    def loopAbc(self):
        """Loops selected objects if they have alembic nodes with anim data.

        Tries the selected objects package, if not found will try the GUI name matches.
        """
        uiSelectedName = self.getImageNameWithoutExtension()
        alembicNodes = assetsimportexport.loopAbcSelectedAsset(cycleInt=1, uiSelectedName=uiSelectedName, message=True)
        if alembicNodes:
            output.displayInfo("Alembic Nodes Set To Cycle: {}".format(alembicNodes))
        else:
            output.displayWarning("No Alembic Nodes found via asset or mesh connections, please select")

    @toolsetwidget.ToolsetWidget.undoDecorator
    def unLoopAbc(self):
        """Removes abc loop of selected objects if they have alembic nodes with anim data checks all selected meshes \
        and assets, sets to constant
        """
        uiSelectedName = self.getImageNameWithoutExtension()
        alembicNodes = assetsimportexport.loopAbcSelectedAsset(cycleInt=0, uiSelectedName=uiSelectedName, message=True)
        if alembicNodes:
            output.displayInfo("Alembic Nodes Set To Constant: {}".format(alembicNodes))
        else:
            output.displayWarning("No Alembic Nodes found via asset or mesh connections, please select")

    # ------------------------------------
    # SCALE ROTATE ASSETS
    # ------------------------------------

    @toolsetwidget.ToolsetWidget.undoDecorator
    def scaleRotSelPackage(self, x=None, y=None):
        """Scales and rotates the selected objects package, if not found will try the UI name matches

        x and y values are for connected widgets
        """
        scaleValue = self.properties.scaleFloat.value
        rotYValue = self.properties.rotateFloat.value

        uiSelectedName = self.getImageNameWithoutExtension()
        assetsimportexport.scaleRotateAssetSelected(scaleValue, rotYValue, uiSelectedName, message=False)
        self.updateFromProperties()  # updates the UI

    def packageRotOffset(self, offset=15.0, neg=False):
        """Scales the rotate value by a potential multiplier, alt shift etc, then runs the scale/rotate function"""
        multiplier, reset = keyboardmouse.ctrlShiftMultiplier(shiftMultiply=5.0, ctrlMultiply=0.2, altMultiply=1.0)
        rotYValue = self.properties.rotateFloat.value
        if reset:
            self.properties.rotateFloat.value = 0.0
        else:
            if neg:
                offset = -offset
            if multiplier > 1:
                multiplier = 2.0  # dim faster value as 5.0 is too fast
            offset = offset * multiplier
            self.properties.rotateFloat.value = rotYValue + offset
        self.scaleRotSelPackage()  # Do the scale/rot and update UI

    def packageScaleOffset(self, offset=.1, neg=False):
        """Scales the scale value by a potential multiplier, alt shift etc, then runs the scale/rotate function"""
        multiplier, reset = keyboardmouse.ctrlShiftMultiplier(shiftMultiply=5.0, ctrlMultiply=0.2, altMultiply=1.0)
        scaleValue = self.properties.scaleFloat.value
        if reset:
            self.properties.scaleFloat.value = 1.0
        else:
            offset = offset * multiplier
            if neg:
                offset = - offset
            self.properties.scaleFloat.value = scaleValue + offset
        self.scaleRotSelPackage()  # Do the scale/rot and update UI

    # ------------------------------------
    # CREATE IMPORT ASSETS
    # ------------------------------------

    @toolsetwidget.ToolsetWidget.undoDecorator
    def importAsset(self, assetName=""):
        """ Imports the zooScene asset given the GUI settings

        :param assetName:
        :type assetName:
        :return:
        :rtype:
        """
        logger.debug("Starting asset importing process")
        item = self.currentWidget().miniBrowser.currentItem()

        if item is None:  # no image has been selected
            output.displayWarning("Please select an asset thumbnail image.")
            return


        # Renderer loaded?
        rendererNiceName = self.properties.rendererIconMenu.value
        if not self.checkRenderLoaded(rendererNiceName):
            return
        # Alembic loaded?
        abcState = self.checkAbcLoaded()
        if not abcState:
            return
        # Replace Assets
        replaceIndex = self.properties.replaceCombo.value
        if replaceIndex == 0:
            replaceAssets = True
            replaceByType = True
        elif replaceIndex == 1:
            replaceAssets = True
            replaceByType = False
        else:
            replaceAssets = False
            replaceByType = False
        # Do the import
        allNodes = assetsimportexport.importZooSceneAsAsset(item.filePath,
                                                            rendererNiceName,
                                                            replaceAssets=replaceAssets,
                                                            importAbc=True,
                                                            importShaders=True,
                                                            importLights=True,
                                                            replaceShaders=False,
                                                            addShaderSuffix=True,
                                                            importSubDInfo=True,
                                                            replaceRoots=True,
                                                            turnStart=0,
                                                            turnEnd=0,
                                                            turnOffset=0.0,
                                                            loopAbc=self.properties.autoLoopCheckBox.value,
                                                            replaceByType=replaceByType,
                                                            rotYOffset=self.properties.rotateFloat.value,
                                                            scaleOffset=self.properties.scaleFloat.value)
        if allNodes:
            output.displayInfo("Success: File Imported As An Asset")


    # ------------------------------------
    # EMBED WINDOWS
    # ------------------------------------

    def setEmbedVisible(self, vis=False):
        """Shows and hides the saveEmbedWindow"""
        if not vis:
            pass
        self.currentWidget().saveEmbedWinContainer.setEmbedVisible(vis)

    # ------------------------------------
    # DISABLE ENABLE
    # ------------------------------------

    def disableStartEndFrame(self):
        """Sets the disabled/enabled state of the Start and End frame int boxes
        """
        for uiInstance in self.widgets():
            uiInstance.startFrameInt.setDisabled(not self.properties.animationRadio.value)
            uiInstance.endFrameInt.setDisabled(not self.properties.animationRadio.value)

    # ------------------------------------
    # CONNECTIONS
    # ------------------------------------

    def uiconnections(self):
        """Hooks up the actual button/widgets functionality
        """
        super(AlembicAssets, self).uiconnections()

        for w in self.widgets():
            # dots menu viewer
            w.miniBrowser.dotsMenu.applyAction.connect(self.importAsset)
            w.miniBrowser.dotsMenu.createAction.connect(partial(self.setEmbedVisible, vis=True))
            w.saveModelAssetBtn.clicked.connect(self.exportGenericAlembic)  # does the save asset
            w.miniBrowser.dotsMenu.renameAction.connect(self.renameAsset)
            w.miniBrowser.dotsMenu.deleteAction.connect(self.deletePresetPopup)

            # Thumbnail viewer
            w.browserModel.doubleClicked.connect(self.importAsset)
            # Offsets
            w.rotatePosBtn.clicked.connect(partial(self.packageRotOffset, neg=False))
            w.rotateNegBtn.clicked.connect(partial(self.packageRotOffset, neg=True))
            w.rotateFloat.textModified.connect(self.scaleRotSelPackage)
            w.scaleUpBtn.clicked.connect(partial(self.packageScaleOffset, neg=False))
            w.scaleDownBtn.clicked.connect(partial(self.packageScaleOffset, neg=True))
            w.scaleFloat.textModified.connect(self.scaleRotSelPackage)
            # Change renderer
            w.rendererIconMenu.actionTriggered.connect(self.global_changeRenderer)
            # Embed window
            w.animationRadio.toggled.connect(self.disableStartEndFrame)
            w.cancelSaveBtn.clicked.connect(partial(self.setEmbedVisible, vis=False))
            w.removeFromSceneBtn.clicked.connect(self.deleteAssetInScene)
            # Manage object in scene
            w.selectRootBtn.clicked.connect(self.selectPackageRootGrpsInScene)

        # Abc
        self.advancedWidget.loopAbcAnimationBtn.clicked.connect(self.loopAbc)
        self.advancedWidget.removeAbcLoopBtn.clicked.connect(self.unLoopAbc)



class AllWidgets(QtWidgets.QWidget):
    """Create all the widgets for all GUIs, compact and advanced etc"""

    def __init__(self, parent=None, properties=None, uiMode=None, toolsetWidget=None):
        """Builds the main widgets for the IBL light UIs, no layouts and no connections:

            uiMode - 0 is compact (UI_MODE_COMPACT)
            uiMode - 1 is medium (UI_MODE_MEDIUM)
            ui mode - 2 is advanced (UI_MODE_ADVANCED)

        properties is the list(dictionaries) used to set logic and pass between the different UI layouts
        such as compact/adv etc

        :param parent: the parent of this widget
        :type parent: qtObject
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: list[dict]
        :param uiMode: 0 is compact ui mode, 1 is medium ui mode, 2 is advanced ui mode
        :type uiMode: int
        :param toolsetWidget: the widget of the toolset
        :type toolsetWidget: :class:`AlembicAssets`
        """
        super(AllWidgets, self).__init__(parent=parent)
        self.savedThumbHeight = None
        self.toolsetWidget = toolsetWidget
        self.properties = properties
        self.uiMode = uiMode
        # Thumbnail Viewer --------------------------------------------
        self.themePref = coreinterfaces.coreInterface()
        # viewer widget and model
        modelAssetPref = self.toolsetWidget.modelAssetsPrefInterface.modelAssetsPreference
        uniformIcons = modelAssetPref.browserUniformIcons()
        self.miniBrowser = elements.MiniBrowser(parent=self,
                                                toolsetWidget=self.toolsetWidget,
                                                columns=3,
                                                fixedHeight=382,
                                                uniformIcons=uniformIcons,
                                                itemName="Asset",
                                                applyText="Import",
                                                applyIcon="packageAssets",
                                                selectDirectoriesActive=True)
        self.miniBrowser.dotsMenu.setSnapshotActive(True)
        self.miniBrowser.dotsMenu.setDirectoryActive(False)
        self.browserModel = zooscenemodel.ZooSceneModel(self.miniBrowser,
                                                        directories=modelAssetPref.browserFolderPaths(),
                                                        uniformIcons=uniformIcons,
                                                        assetPreference=modelAssetPref)

        self.miniBrowser.setModel(self.browserModel)
        self.resizerWidget = ToolsetResizer(toolsetWidget=self.toolsetWidget, target=self.miniBrowser)
        # Replace Combo --------------------------------------
        toolTip = "Replace the imported asset by \n" \
                  " Type: Replaces any other assets where the asset type matches, see the info section\n" \
                  " All:  Replaces all assets in the scene \n" \
                  " Add: Does not replace, only adds new assets"
        self.replaceCombo = elements.ComboBoxRegular(items=REPLACE_COMBO, toolTip=toolTip)
        # Scale --------------------------------------
        toolTip = "Scale the current selected asset"
        self.scaleFloat = elements.FloatEdit("Scale",
                                             "1.0",
                                             labelRatio=2,
                                             editRatio=3,
                                             toolTip=toolTip)
        toolTip = "Scale the current asset smaller\n" \
                  "(Shift faster, ctrl slower, alt reset)"
        self.scaleDownBtn = elements.styledButton("", "scaleDown",
                                                  self,
                                                  toolTip=toolTip,
                                                  style=uic.BTN_TRANSPARENT_BG,
                                                  minWidth=uic.BTN_W_ICN_MED)
        toolTip = "Scale the current asset larger\n" \
                  "(Shift faster, ctrl slower, alt reset)"
        self.scaleUpBtn = elements.styledButton("",
                                                "scaleUp",
                                                toolTip=toolTip,
                                                style=uic.BTN_TRANSPARENT_BG,
                                                minWidth=uic.BTN_W_ICN_MED)
        # Rotation --------------------------------------
        toolTip = "Rotate the current selected asset"
        self.rotateFloat = elements.FloatEdit("Rotate",
                                              "0.0",
                                              toolTip=toolTip,
                                              smallSlideDist=0.01,
                                              slideDist=0.1,
                                              largeSlideDist=1.0)
        toolTip = "Rotate the current asset in degrees\n" \
                  "(Shift faster, ctrl slower, alt reset)"
        self.rotatePosBtn = elements.styledButton("",
                                                  "arrowRotLeft",
                                                  toolTip=toolTip,
                                                  style=uic.BTN_TRANSPARENT_BG,
                                                  minWidth=uic.BTN_W_ICN_MED)
        self.rotateNegBtn = elements.styledButton("", "arrowRotRight",
                                                  toolTip=toolTip,
                                                  style=uic.BTN_TRANSPARENT_BG,
                                                  minWidth=uic.BTN_W_ICN_MED)
        # Renderer Button --------------------------------------
        toolTip = "Change the Renderer to Arnold, Redshift or Renderman"
        self.rendererIconMenu = elements.iconMenuButtonCombo(DFLT_RNDR_MODES,
                                                             self.properties.rendererIconMenu.value,
                                                             toolTip=toolTip)
        self.saveEmbedWinContainer = self.saveModelAssetEmbedWin(parent)
        if uiMode == UI_MODE_COMPACT:
            #  Delete Select Label
            self.delSelectLabel = elements.Label(text="Select/Delete")

        # Remove From Scene Button --------------------------------------
        toolTip = "Deletes the selected asset from scene. \n" \
                  "Asset can be selected in the 3d view or in the GUI."
        if uiMode == UI_MODE_COMPACT:
            self.removeFromSceneBtn = elements.styledButton("",
                                                            icon="crossXFat",
                                                            toolTip=toolTip,
                                                            style=uic.BTN_LABEL_SML)
        if uiMode == UI_MODE_ADVANCED:
            self.removeFromSceneBtn = elements.styledButton("Delete From Scene",
                                                            icon="crossXFat",
                                                            toolTip=toolTip,
                                                            style=uic.BTN_LABEL_SML)
        # Select Root Button --------------------------------------
        toolTip = "Selects the root froup of the current asset. \n" \
                  "Select any part of an asset in the 3d viewport or the GUI and run."
        if self.uiMode == UI_MODE_COMPACT:
            self.selectRootBtn = elements.styledButton("",
                                                       icon="cursorSelect",
                                                       toolTip=toolTip,
                                                       style=uic.BTN_LABEL_SML)
        if self.uiMode == UI_MODE_ADVANCED:  # widgets that only exist in the advanced mode
            # Select Root Button --------------------------------------
            self.selectRootBtn = elements.styledButton("Select Root",
                                                       icon="cursorSelect",
                                                       toolTip=toolTip,
                                                       style=uic.BTN_LABEL_SML)
            # Loop ABC Button --------------------------------------
            toolTip = "Loop an alembic asset if is has animation, cycle animation will loop.\n" \
                      "Select any part of an asset in the 3d viewport or the GUI and run."
            self.loopAbcAnimationBtn = elements.styledButton("Loop .abc Animation",
                                                             icon="loopAbc",
                                                             toolTip=toolTip,
                                                             style=uic.BTN_LABEL_SML)
            # Loop ABC Button --------------------------------------
            toolTip = "Remove looping alembic animation, if animation exists on the asset.\n" \
                      "Select any part of an asset in the 3d viewport or the GUI and run."
            self.removeAbcLoopBtn = elements.styledButton("Remove .abc Loop",
                                                          icon="removeLoop",
                                                          toolTip=toolTip,
                                                          style=uic.BTN_LABEL_SML)
            # Auto Loop Button --------------------------------------
            toolTip = "On import cycle any imported animation"
            self.autoLoopCheckBox = elements.CheckBox("Auto Loop",
                                                      checked=False,
                                                      toolTip=toolTip)

    def saveModelAssetEmbedWin(self, parent=None):
        """The popup properties UI embedded window for saving assets

        :param parent: the parent widget
        :type parent: Qt.object
        """
        toolTip = "Close the save window"
        self.hidePropertiesBtn = elements.styledButton("",
                                                       "closeX",
                                                       toolTip=toolTip,
                                                       btnWidth=uic.BTN_W_ICN_SML,
                                                       style=uic.BTN_TRANSPARENT_BG)

        saveEmbedWindow = elements.EmbeddedWindow(title="Create Asset From Scene",
                                                  closeButton=self.hidePropertiesBtn,
                                                  margins=(0, uic.SMLPAD, 0, uic.REGPAD),
                                                  uppercase=True,
                                                  resizeTarget=self.miniBrowser)
        saveEmbedWindow.visibilityChanged.connect(self.embedWindowVisChanged)

        self.saveEmbedWinLayout = saveEmbedWindow.getLayout()
        self.saveEmbedWinLbl = saveEmbedWindow.getTitleLbl()
        # Current Frame Radio ------------------------------
        toolTipList = ["", ""]
        radioList = ["Current Frame", "Animation"]
        self.animationRadio = elements.RadioButtonGroup(radioList=radioList,
                                                        toolTipList=toolTipList,
                                                        default=0,
                                                        margins=(0, uic.REGPAD, 0, uic.REGPAD),
                                                        spacing=uic.LRGPAD)
        # Start End Frame Txt ------------------------------
        toolTip = ""
        self.startFrameInt = elements.IntEdit("Start",
                                              editText=0,
                                              editRatio=2,
                                              labelRatio=1,
                                              toolTip=toolTip, )
        toolTip = ""
        self.endFrameInt = elements.IntEdit("End",
                                            editText=100,
                                            editRatio=2,
                                            labelRatio=1,
                                            toolTip=toolTip, )
        # From Selected Radio ------------------------------
        toolTipList = ["", ""]
        radioList = ["From Selected", "Save From Scene"]
        self.fromSelectedRadio = elements.RadioButtonGroup(radioList=radioList,
                                                           toolTipList=toolTipList,
                                                           default=0,
                                                           margins=(0, uic.REGPAD, 0, uic.REGPAD),
                                                           spacing=uic.LRGPAD)
        # Save Button -------------------------------------
        toolTip = ""
        self.saveModelAssetBtn = elements.styledButton("Create Asset",
                                                       icon="save",
                                                       toolTip=toolTip,
                                                       style=uic.BTN_DEFAULT)
        # Cancel Button -------------------------------------
        toolTip = ""
        self.cancelSaveBtn = elements.styledButton("Cancel",
                                                   icon="xMark",
                                                   toolTip=toolTip,
                                                   style=uic.BTN_DEFAULT)
        # start end frame layout -------------------------------------
        startEndFrameLayout = elements.hBoxLayout(spacing=uic.LRGPAD)
        startEndFrameLayout.addWidget(self.startFrameInt)
        startEndFrameLayout.addWidget(self.endFrameInt)
        # save Button  layout -------------------------------------
        saveButtonLayout = elements.hBoxLayout()
        saveButtonLayout.addWidget(self.saveModelAssetBtn)
        saveButtonLayout.addWidget(self.cancelSaveBtn)
        # add to main layout -------------------------------------
        self.saveEmbedWinLayout.addWidget(self.animationRadio)
        self.saveEmbedWinLayout.addLayout(startEndFrameLayout)
        self.saveEmbedWinLayout.addWidget(self.fromSelectedRadio)
        self.saveEmbedWinLayout.addLayout(saveButtonLayout)
        return saveEmbedWindow

    def embedWindowVisChanged(self, visibility):
        self.toolsetWidget.updateTree(delayed=True)


class GuiCompact(AllWidgets):
    def __init__(self, parent=None, properties=None, uiMode=UI_MODE_COMPACT, toolsetWidget=None):
        """Builds the compact version of GUI, sub classed from AllWidgets() which creates the widgets:

            default uiMode - 1 is compact (UI_MODE_COMPACT)

        :param parent: the parent of this widget
        :type parent: qtObject
        :param properties: Special dictionary which tracks the properties of each widget for the GUI
        :type properties: list[dict]
        :param uiMode: The UI mode to build, either UI_MODE_COMPACT = 0 or UI_MODE_ADVANCED = 1
        :type uiMode: int
        :param toolsetWidget: The instance of the toolsetWidget class, needed for setting properties.
        :type toolsetWidget: :class:`AlembicAssets`
        """
        super(GuiCompact, self).__init__(parent=parent, properties=properties,
                                         uiMode=uiMode, toolsetWidget=toolsetWidget)
        # Main Layout
        mainLayout = elements.vBoxLayout(self, margins=(uic.WINSIDEPAD, uic.WINTOPPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=0)
        # Renderer layout
        rendererLayout = elements.hBoxLayout()
        rendererLayout.addWidget(self.delSelectLabel, 9)
        rendererLayout.addWidget(self.selectRootBtn, 1)
        rendererLayout.addWidget(self.removeFromSceneBtn, 1)
        rendererLayout.addWidget(self.rendererIconMenu, 1)
        # Rotate layout
        rotateLayout = elements.hBoxLayout()
        rotateLayout.addWidget(self.rotateFloat, 9)
        rotateLayout.addWidget(self.rotatePosBtn, 1)
        rotateLayout.addWidget(self.rotateNegBtn, 1)
        # Scale layout
        scaleLayout = elements.hBoxLayout()
        scaleLayout.addWidget(self.scaleFloat, 9)
        scaleLayout.addWidget(self.scaleDownBtn, 1)
        scaleLayout.addWidget(self.scaleUpBtn, 1)
        # Grid Layout
        gridLayout = elements.GridLayout(margins=(0, 0, 0, 0), hSpacing=uic.SVLRG, vSpacing=uic.SREG)
        gridLayout.addWidget(self.replaceCombo, 0, 0)
        gridLayout.addLayout(rendererLayout, 0, 1)
        gridLayout.addLayout(rotateLayout, 1, 0)
        gridLayout.addLayout(scaleLayout, 1, 1)
        gridLayout.setColumnStretch(0, 1)
        gridLayout.setColumnStretch(1, 1)
        # Add to main layout
        mainLayout.addWidget(self.saveEmbedWinContainer)  # will be hidden
        mainLayout.addWidget(self.miniBrowser)
        mainLayout.addWidget(self.resizerWidget)
        mainLayout.addLayout(gridLayout)
        mainLayout.addStretch(1)


class GuiAdvanced(AllWidgets):
    def __init__(self, parent=None, properties=None, uiMode=UI_MODE_ADVANCED, toolsetWidget=None):
        """Builds the advanced version of GUI, subclassed from AllWidgets() which creates the widgets:

            default uiMode - 1 is advanced (UI_MODE_ADVANCED)

        :param parent: the parent of this widget
        :type parent: qtObject
        :param properties: Special dictionary which tracks the properties of each widget for the GUI
        :type properties: list[dict]
        :param uiMode: The UI mode to build, either UI_MODE_COMPACT = 0 or UI_MODE_ADVANCED = 1
        :type uiMode: int
        :param toolsetWidget: The instance of the toolsetWidget class, needed for setting properties.
        :type toolsetWidget: :class:`AlembicAssets`
        """
        super(GuiAdvanced, self).__init__(parent=parent, properties=properties,
                                          uiMode=uiMode, toolsetWidget=toolsetWidget)
        # Main Layout
        mainLayout = elements.vBoxLayout(self, margins=(uic.WINSIDEPAD, uic.WINTOPPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=0)
        # Renderer layout
        rendererLayout = elements.hBoxLayout()
        rendererLayout.addWidget(self.autoLoopCheckBox, 9)
        rendererLayout.addWidget(self.rendererIconMenu, 1)
        # Rotate layout
        rotateLayout = elements.hBoxLayout()
        rotateLayout.addWidget(self.rotateFloat, 3)
        rotateLayout.addWidget(self.rotatePosBtn, 1)
        rotateLayout.addWidget(self.rotateNegBtn, 1)
        # Scale layout
        scaleLayout = elements.hBoxLayout()
        scaleLayout.addWidget(self.scaleFloat, 3)
        scaleLayout.addWidget(self.scaleDownBtn, 1)
        scaleLayout.addWidget(self.scaleUpBtn, 1)
        # Grid Layout
        gridLayout = elements.GridLayout(margins=(0, 0, 0, 0), hSpacing=uic.SVLRG, vSpacing=uic.SREG)
        gridLayout.addWidget(self.selectRootBtn, 0, 0)
        gridLayout.addWidget(self.removeFromSceneBtn, 0, 1)
        gridLayout.addWidget(self.loopAbcAnimationBtn, 1, 0)
        gridLayout.addWidget(self.removeAbcLoopBtn, 1, 1)
        gridLayout.addWidget(self.replaceCombo, 2, 0)
        gridLayout.addLayout(rendererLayout, 2, 1)
        gridLayout.addLayout(rotateLayout, 3, 0)
        gridLayout.addLayout(scaleLayout, 3, 1)
        gridLayout.setColumnStretch(0, 1)
        gridLayout.setColumnStretch(1, 1)
        # Add to main layout
        mainLayout.addWidget(self.saveEmbedWinContainer)  # will be hidden
        mainLayout.addWidget(self.miniBrowser)
        mainLayout.addWidget(self.resizerWidget)
        mainLayout.addLayout(gridLayout)
        mainLayout.addStretch(1)
