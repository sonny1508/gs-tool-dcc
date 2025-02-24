import os
from functools import partial

from zoo.apps.toolsetsui.ext.renderers import RendererMixin
from zoovendor.Qt import QtWidgets, QtCore

from zoo.libs.zooscene import zooscenefiles
from zoo.preferences.interfaces import lightsuiteinterfaces

from zoo.libs.maya.cmds.lighting import renderertransferlights
from zoo.libs.maya.cmds.lighting.renderertransferlights import LIGHTVISIBILITY
from zoo.libs.maya.cmds.objutils import scaleutils
from zoo.libs.maya.cmds.renderer import exportabcshaderlights

from zoo.libs.zooscene.constants import ZOOSCENE_EXT

from zoo.apps.toolsetsui.widgets.toolsetresizer import ToolsetResizer
from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.apps.toolsetsui.mixins import MiniBrowserMixin
from zoo.libs.pyqt.extended.imageview.models import zooscenemodel
from zoo.libs.pyqt.widgets import elements
from zoo.libs.pyqt import uiconstants as uic

from zoo.core.util import zlogging
from zoo.libs.utils import output

logger = zlogging.getLogger(__name__)

DFLT_RNDR_MODES = [("arnold", "Arnold"), ("redshift", "Redshift"), ("renderman", "Renderman")]
UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1

DFLT_RNDR_MODE = "Arnold"


class LightPresets(toolsetwidget.ToolsetWidget, RendererMixin, MiniBrowserMixin):
    id = "lightPresets"
    uiData = {"label": "Light Presets",
              "icon": "lightstudio",
              "tooltip": "Miniature version of the Light Presets Browser",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-light-presets/"
              }

    # ------------------------------------
    # START UP
    # ------------------------------------

    def preContentSetup(self):
        """First code to run"""
        self.sceneUnits = scaleutils.sceneUnits()
        self.toolsetWidget = self  # needed for callback decorators
        self.lightSuitePrefInterface = lightsuiteinterfaces.lightSuiteInterface()
        self.setAssetPreferences(self.lightSuitePrefInterface.lightPresetsPreference)
        self.initRendererMixin(disableVray=True, disableMaya=True)

    def contents(self):
        """The UI Modes to build, compact, medium and or advanced """
        return [self.initCompactWidget()]

    def initCompactWidget(self):
        self.compactWidget = GuiCompact(parent=self, properties=self.properties, toolsetWidget=self)
        return self.compactWidget

    def postContentSetup(self):
        """Last of the initialize code"""
        self._sceneUnitsScaleLabel()
        self.presetPath = ""  # This is the path of the selected image
        self.ignoreInstantApply = False  # For instant apply directional lights and switching ui modes
        self.listeningForRenderer = True  # If True the renderer can be set from other windows or toolsets
        self.setMiniBrowsers([w.miniBrowser for w in self.widgets()])
        self.updateFromProperties()
        self.uiConnections()

    def currentWidget(self):
        """ Current active widget

        :return:
        :rtype:  AllWidgets
        """
        return super(LightPresets, self).currentWidget()

    def widgets(self):
        """ List of widgets

        :return:
        :rtype: list[AllWidgets]
        """
        return super(LightPresets, self).widgets()

    # ------------------------------------
    # PROPERTIES
    # ------------------------------------

    def initializeProperties(self):
        return [{"name": "scale", "label": "Scale (cms)", "value": 180.00},
                {"name": "rotationOffset", "label": "Rotation Offset", "value": 0.00},
                {"name": "intensity", "label": "Intensity", "value": 1.00},
                {"name": "backgroundVisibility", "label": "Background Visibility", "value": False},
                {"name": "instantApply", "label": "Instant Apply", "value": True},
                {"name": "deleteLightsCheckBx", "label": "Delete Lights", "value": True},
                {"name": "rendererIconMenu", "label": "", "value": "Arnold"}]

    # ------------------------------------
    # RECEIVE RENDERER FROM OTHER UIS
    # ------------------------------------

    def global_receiveRendererChange(self, renderer):
        """Receives from other GUIs, changes the renderer when it is changed Overridden"""
        super(LightPresets, self).global_receiveRendererChange(renderer, ignoreMaya=True, ignoreVRay=True)

    # ------------------------------------
    # UPDATE
    # ------------------------------------

    def _sceneUnitsScaleLabel(self):
        """Sets the scene units in the UI"""
        self.compactWidget.scaleEdit.setLabel("Scale {}s:".format(self.sceneUnits))
        self.properties.scale.value = scaleutils.scaleUnitToUnitConversion(180.0, "cm", self.sceneUnits)

    # ------------------------------------
    # DOTS MENU
    # ------------------------------------

    def saveLightPreset(self):
        """Saves all lights in the scene of the current renderer to a .zooScene generic file

        Saves with the dialog window elements.SaveDialog() which uses Qt's QFileDialog

        :return fullFilePath: The full file path of the .json file created, empty string if cancelled
        :rtype fullFilePath: str
        """
        renderer = self.properties.rendererIconMenu.value
        # check exist lights in the scene for the renderer
        areaLightShapeList, directionalLightShapeList, skydomeShapeList = renderertransferlights.getAllLightShapesInScene(
            renderer)
        if not areaLightShapeList and not directionalLightShapeList and not skydomeShapeList:
            output.displayWarning("No Lights Found To Export For {}".format(renderer))
            return

        lightPresetDirectory = self.currentWidget().miniBrowser.getSaveDirectory()

        # After the Save window
        if not lightPresetDirectory:  # If window clicked cancel then cancel
            return ""
        name = elements.MessageBox.inputDialog(title="Scene Name", parent=self,
                                               message="New Scene Name: ")
        if not name:
            return
        fullFilePath = os.path.join(lightPresetDirectory,
                                    os.path.extsep.join((name, exportabcshaderlights.ZOOSCENESUFFIX)))
        # Do the save ------------------------------
        sceneUnits = scaleutils.sceneUnits()  # save the scene units so can be returned
        scaleutils.setSceneUnits("cm")  # always save in "cm"
        exportabcshaderlights.exportAbcGenericShaderLights(fullFilePath,
                                                           rendererNiceName=renderer,
                                                           exportSelected=False,
                                                           exportShaders=False,
                                                           exportLights=True,
                                                           exportAbc=False,
                                                           noMayaDefaultCams=True,
                                                           exportGeo=False,
                                                           exportCams=False,
                                                           exportAll=True,
                                                           keepThumbnailOverride=True)
        scaleutils.setSceneUnits(sceneUnits)  # return to previously set scene units
        # Refresh UI ------------------------------
        output.displayInfo("File and it's dependencies saved: {}".format(lightPresetDirectory))
        self.currentWidget().miniBrowser.refreshThumbs()
        return lightPresetDirectory

    def getPresetFileFolders(self):
        """Return file information from the thumb widget"""
        filePath = self.currentWidget().miniBrowser.itemFilePath()
        if filePath is None:
            return "", "", "", ""
        lightPresetDirectory = os.path.dirname(filePath)
        fileNoExt = self.currentWidget().browserModel.currentImage
        fileName = ".".join([fileNoExt, ZOOSCENE_EXT])
        zooSceneFullPath = os.path.join(lightPresetDirectory, fileName)
        return lightPresetDirectory, fileName, fileNoExt, zooSceneFullPath

    def renamePreset(self):
        """Opens a Rename Window and renames the current .zooScene file on disk while updating
        """
        # get the current directory
        lightPresetDirectory, fileName, fileNoExt, zooSceneFullPath = self.getPresetFileFolders()
        if not lightPresetDirectory:
            return
        # Open the rename window
        message = "Rename Related `{}` Files As:".format(fileNoExt)
        renameText = elements.MessageBox.inputDialog(title="Rename The Current Light Preset",
                                                     text=fileNoExt,
                                                     parent=None,
                                                     message=message)
        # After rename window
        if not renameText:
            return
        # Renaming
        renameFilename = "{}.{}".format(renameText, ".", ZOOSCENE_EXT)
        if os.path.isfile(os.path.join(lightPresetDirectory, renameFilename)):
            output.displayWarning("This filename already exists, please use a different name")
            return
        fileRenameList = zooscenefiles.renameZooSceneOnDisk(renameText, zooSceneFullPath)
        if not fileRenameList:
            output.displayWarning("Files could not be renamed, they are most likely in use. "
                                  "Do not have the renamed assets loaded in the scene, or check file permissions.")
            return
        output.displayInfo("Success: Files `{}*` Have Been Renamed To `{}*`".format(fileNoExt, renameText))
        self.currentWidget().miniBrowser.refreshThumbs()

    def deletePreset(self):
        """Deletes the current preset, shows a popup window asking to confirm
        """
        lightPresetDirectory, fileName, fileNoExt, zooSceneFullPath = self.getPresetFileFolders()
        if not lightPresetDirectory:
            return
        message = "Warning: Delete the preset `{}` and it's dependencies?  " \
                  "This will permanently delete these file/s from disk?".format(fileNoExt)

        result = elements.MessageBox.showQuestion(None, title="Delete File?", message=message,
                                                  buttonA="OK", buttonB="Cancel")
        if result == "A":
            filesFullPathDeleted = zooscenefiles.deleteZooSceneFiles(zooSceneFullPath, message=True)
            output.displayInfo("Success, File/s Deleted: {}".format(filesFullPathDeleted))
        self.currentWidget().miniBrowser.refreshThumbs()

    # ------------------------------------
    # CREATE LIGHT PRESETS
    # ------------------------------------

    def getScaleSelected(self):
        """Gets the longest edge from a bounding box of the selected objects and updates the GUI
        """
        logger.debug("getScaleSelected()")
        longestEdge = scaleutils.getLongestEdgeMultipleSelObjs()
        if not longestEdge:
            return
        self.properties.scale.value = longestEdge
        self.updateFromProperties()
        self.presetInstantApply()

    # ------------------------------------
    # CREATE LIGHT PRESETS
    # ------------------------------------

    def presetInstantApply(self):
        """Creates/recreates the light presets checking if instant apply is on
        Now depreciated due to the thumbnail browser"""
        if not self.properties.instantApply.value:
            return
        logger.debug("presetInstantApply()")
        self.presetApply()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def applyPresetUndo(self, overideDeleteLights, renderer, presetPath, showIBL=False):
        """Creates the lights from the preset and handles Maya's undo queue"""
        logger.debug("applyPresetUndo()")
        os.environ['ZOO_PREFS_IBLS_PATH'] = os.pathsep.join(self.lightSuitePrefInterface.skydomeDirectories())
        exportabcshaderlights.importLightPreset(presetPath, renderer, overideDeleteLights)
        allIblLightShapes = renderertransferlights.getIBLLightsInScene(renderer)
        if allIblLightShapes:  # check if IBL exists to apply the bgVisibility setting from the GUI
            lightDictAttributes = renderertransferlights.getSkydomeLightDictAttributes()  # dict with keys/empty values
            lightDictAttributes[LIGHTVISIBILITY] = showIBL
            renderertransferlights.setIblAttrAuto(lightDictAttributes, renderer, message=False)

    def presetApplyThumbnail(self):
        """Applies the thumbnail view image
        """
        try:
            self.presetPath = self.currentWidget().miniBrowser.itemFilePath()
            self.presetApply()
        except AttributeError:
            output.displayWarning("Please select an image")
            logger.error("bitch", exc_info=True)

    def presetApply(self):
        """Creates/updates the lights from the preset from the GUI properties """
        logger.debug("presetApply()")
        if not self.presetPath:  # no image has been selected
            output.displayWarning("Please select an image")
            return
        rendererNiceName = self.properties.rendererIconMenu.value
        if not self.checkRenderLoaded(rendererNiceName):
            return
        overideDeleteLights = self.properties.deleteLightsCheckBx.value
        showIBL = self.properties.backgroundVisibility.value
        charScale = self.properties.scale.value
        rot = self.properties.rotationOffset.value
        intensity = self.properties.intensity.value
        self.applyPresetUndo(overideDeleteLights, rendererNiceName, self.presetPath,
                             showIBL=showIBL)  # apply the preset

        uiSizeDefault = scaleutils.scaleUnitToUnitConversion(180.0, "cm", self.sceneUnits)
        scale = charScale / uiSizeDefault  # converts to normalized value, default should be 1.0
        # convert to scene units if not cm ------------------------------------

        unitScale = scaleutils.scaleUnitToSceneConversion(1.0, fromUnit="cm")  # adjust for current units
        scale *= unitScale  # multiply by the scene units, inches will be 70.8661
        # Do the scale ---------------------------------------------------------
        scalePercentage = - (100 - (scale * 100))
        renderertransferlights.scaleAllLightsInScene(scalePercentage, rendererNiceName, scalePivot=(0.0, 0.0, 0.0),
                                                     ignoreNormalization=False, ignoreIbl=False, importUnitAdjust=True,
                                                     message=True)
        # rot
        renderertransferlights.rotLightGrp(rendererNiceName, rot, setExactRotation=True)
        # multiply the intensity
        intensityPercentage = (intensity - 1) * 100
        renderertransferlights.scaleAllLightsIntensitySelected(intensityPercentage, rendererNiceName,
                                                               applyExposure=True)

    # ------------------------------------
    # OFFSET BUTTONS
    # ------------------------------------

    def presetMultiplier(self):
        """For offset functions multiply shift and minimise if ctrl is held down
        If alt then call the reset option

        :return multiplier: multiply value, .2 if ctrl 5 if shift 1 if None
        :rtype multiplier: float
        :return reset: reset becomes true for resetting
        :rtype reset: bool
        """
        logger.debug("presetMultiplier()")
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        if modifiers == QtCore.Qt.ShiftModifier:
            return 5.0, False
        elif modifiers == QtCore.Qt.ControlModifier:
            return 0.2, False
        elif modifiers == QtCore.Qt.AltModifier:
            return 1, True
        return 1.0, False

    def presetSetScale(self, neg=False):
        """Used when the offset buttons are pressed, set scale values

        Must rebuild the entire light setup
        :param neg: set to True while scaling smaller
        :type neg: bool
        """
        logger.debug("presetSetScale()")
        multiplier, reset = self.presetMultiplier()
        if reset:
            self.properties.scale.value = 180.0
        else:
            scale = self.properties.scale.value
            offset = 5.0 * multiplier
            if neg:
                offset = - offset
            self.properties.scale.value = scale * (1.0 + (offset / 100.0))
        self.updateFromProperties()
        self.presetInstantApply()

    def presetSetRot(self, neg=False):
        """Used when the offset buttons are pressed, set rotation values

        Must rebuild the entire light setup
        :param neg: set to True while rotating negatively
        :type neg: bool
        """
        logger.debug("presetSetRot()")
        multiplier, reset = self.presetMultiplier()
        if reset:
            self.properties.rotationOffset.value = 0.0
        else:
            rot = self.properties.rotationOffset.value
            if multiplier > 1.0:
                multiplier = 2.0  # dim the fast mode as it's too fast
            offset = 15.0 * multiplier
            if neg:
                offset = - offset
            self.properties.rotationOffset.value = rot + offset
        self.updateFromProperties()
        self.presetInstantApply()

    def presetSetIntensity(self, neg=False):
        """Used when the offset buttons are pressed, set intensity brighten/darken values

        Must rebuild the entire light setup
        :param neg: set to True while darkening the intensity
        :type neg: bool
        """
        logger.debug("presetSetIntensity()")
        multiplier, reset = self.presetMultiplier()
        if reset:
            self.properties.intensity.value = 1.0
        else:
            intensity = self.properties.intensity.value
            offset = .1 * multiplier
            if neg:
                offset = - offset
            self.properties.intensity.value = intensity + offset
        self.updateFromProperties()
        self.presetInstantApply()

    # ------------------------------------
    # CONNECTIONS
    # ------------------------------------

    def uiConnections(self):
        """Runs the add suffix command
        """
        super(LightPresets, self).uiconnections()
        for uiInstance in self.widgets():
            # dots menu viewer
            uiInstance.miniBrowser.dotsMenu.createAction.connect(self.saveLightPreset)
            uiInstance.miniBrowser.dotsMenu.renameAction.connect(self.renamePreset)
            uiInstance.miniBrowser.dotsMenu.deleteAction.connect(self.deletePreset)
            uiInstance.miniBrowser.dotsMenu.applyAction.connect(self.presetApplyThumbnail)
            # widget changes
            uiInstance.scaleEdit.textModified.connect(self.presetInstantApply)
            uiInstance.rotEdit.textModified.connect(self.presetInstantApply)
            uiInstance.intensityEdit.textModified.connect(self.presetInstantApply)
            uiInstance.bgVisCheckBx.stateChanged.connect(self.presetInstantApply)
            # thumbnail viewer
            uiInstance.browserModel.doubleClicked.connect(self.presetApplyThumbnail)
            # offset buttons
            uiInstance.scaleDownBtn.clicked.connect(partial(self.presetSetScale, neg=True))
            uiInstance.scaleUpBtn.clicked.connect(self.presetSetScale)
            uiInstance.rotNegBtn.clicked.connect(partial(self.presetSetRot, neg=True))
            uiInstance.rotPosBtn.clicked.connect(self.presetSetRot)
            uiInstance.darkenBtn.clicked.connect(partial(self.presetSetIntensity, neg=True))
            uiInstance.brightenBtn.clicked.connect(self.presetSetIntensity)
            # change renderer
            uiInstance.rendererLoaded.actionTriggered.connect(self.global_changeRenderer)
            uiInstance.scaleFromBtn.clicked.connect(self.getScaleSelected)


class AllWidgets(QtWidgets.QWidget):
    """Create all the widgets for all GUIs, compact and advanced etc"""

    def __init__(self, parent=None, properties=None, uiMode=None, toolsetWidget=None):
        """Builds the main widgets for the Mini Light Presets UIs, no layouts and no connections:

            uiMode - 0 is compact (UI_MODE_COMPACT)
            ui mode - 1 is advanced (UI_MODE_ADVANCED)

        "properties" is the list(dictionaries) used to set logic and pass between the different UI layouts
        such as compact/adv etc

        :param parent: the parent of this widget
        :type parent: qtObject
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: list[dict]
        :param uiMode: 0 is compact ui mode, 1 is medium ui mode, 2 is advanced ui mode
        :type uiMode: int
        :param toolsetWidget: the widget of the toolset
        :type toolsetWidget: qtObject
        """
        super(AllWidgets, self).__init__(parent=parent)
        self.toolsetWidget = toolsetWidget
        self.properties = properties
        self.uiMode = uiMode
        # Thumbnail Viewer ---------------------------------------
        lightSuitePref = self.toolsetWidget.lightSuitePrefInterface.lightPresetsPreference
        uniformIcons = lightSuitePref.browserUniformIcons()
        self.miniBrowser = elements.MiniBrowser(parent=self,
                                                toolsetWidget=self.toolsetWidget,
                                                fixedHeight=382,
                                                columns=3,
                                                uniformIcons=uniformIcons,
                                                itemName="Preset",
                                                applyIcon="lightstudio",
                                                createText="Save",
                                                createThumbnailActive=True,
                                                selectDirectoriesActive=True,
                                                snapshotActive=True,
                                                newActive=True)
        self.miniBrowser.dotsMenu.setDirectoryActive(False)

        self.browserModel = zooscenemodel.ZooSceneModel(self.miniBrowser,
                                                        directories=lightSuitePref.browserFolderPaths(),
                                                        uniformIcons=uniformIcons,
                                                        assetPreference=lightSuitePref)
        self.miniBrowser.setModel(self.browserModel)
        self.resizerWidget = ToolsetResizer(parent=self, toolsetWidget=self.toolsetWidget, target=self.miniBrowser)
        # Scale --------------------------------------
        toolTip = "Import light presets for models at this scale\n180cm (Maya units) is the default size\n" \
                  "Presets should be saved at 180cm to fit the subject"
        if self.uiMode == UI_MODE_ADVANCED:
            editRatio = 74
            labelRatio = 100
            self.scaleEdit = elements.FloatEdit(self.properties.scale.label,
                                                self.properties.scale.value,
                                                parent=self,
                                                editWidth=None,
                                                labelRatio=labelRatio,
                                                editRatio=editRatio,
                                                rounding=2,
                                                toolTip=toolTip)
        if self.uiMode == UI_MODE_COMPACT:
            editRatio = 1
            labelRatio = 1

            self.scaleEdit = elements.FloatEdit("Scale cms",
                                                self.properties.scale.value,
                                                parent=self,
                                                editWidth=None,
                                                labelRatio=labelRatio,
                                                editRatio=editRatio,
                                                rounding=2,
                                                toolTip=toolTip)

        self.toolsetWidget.linkProperty(self.scaleEdit, "scale")

        toolTip = "Get the scale size of the current object/grp selection\nScale is measured from the longest axis"
        self.scaleFromBtn = elements.styledButton("",
                                                  "arrowLeft",
                                                  self,
                                                  toolTip=toolTip,
                                                  style=uic.BTN_TRANSPARENT_BG,
                                                  minWidth=15)
        toolTip = "Scale all lights smaller from world center\n(Shift faster, ctrl slower, alt reset)\n" \
                  "Rebuilds the light preset, changes will be lost"
        self.scaleDownBtn = elements.styledButton("",
                                                  "scaleDown",
                                                  self,
                                                  toolTip=toolTip,
                                                  style=uic.BTN_TRANSPARENT_BG,
                                                  minWidth=15)
        toolTip = "Scale all lights larger from world center\n(Shift faster, ctrl slower, alt reset)\n" \
                  "Rebuilds the light preset, changes will be lost"
        self.scaleUpBtn = elements.styledButton("",
                                                "scaleUp",
                                                self,
                                                toolTip=toolTip,
                                                style=uic.BTN_TRANSPARENT_BG,
                                                minWidth=15)
        # Rotation --------------------------------------
        toolTip = "The rotate offset in degrees\nThe rotation offset is also applied when importing"
        self.rotEdit = elements.FloatEdit(self.properties.rotationOffset.label,
                                          self.properties.rotationOffset.value,
                                          parent=self,
                                          editWidth=None,
                                          labelRatio=1,
                                          editRatio=1,
                                          toolTip=toolTip)
        self.toolsetWidget.linkProperty(self.rotEdit, "rotationOffset")

        if self.uiMode == UI_MODE_COMPACT:
            self.rotEdit.label.setText("Rotate")
        toolTip = "Rotate all lights from the light group\n(Shift faster, ctrl slower, alt reset)\n" \
                  "Rebuilds the light preset, changes will be lost"
        self.rotNegBtn = elements.styledButton("",
                                               "arrowRotLeft",
                                               self,
                                               toolTip=toolTip,
                                               style=uic.BTN_TRANSPARENT_BG,
                                               minWidth=uic.BTN_W_ICN_SML)
        self.rotPosBtn = elements.styledButton("",
                                               "arrowRotRight",
                                               self,
                                               toolTip=toolTip,
                                               style=uic.BTN_TRANSPARENT_BG,
                                               minWidth=15)
        # Intensity --------------------------------------
        toolTip = "The brightness offset\nBrightens/darkens light presets when imported, default is 1.0"
        self.intensityEdit = elements.FloatEdit(self.properties.intensity.label,
                                                self.properties.intensity.value,
                                                parent=self,
                                                editWidth=None,
                                                labelRatio=1,
                                                editRatio=1,
                                                toolTip=toolTip)
        self.toolsetWidget.linkProperty(self.intensityEdit, "intensity")

        toolTip = "Darken all lights\n(Shift faster, ctrl slower, alt reset)\n" \
                  "Rebuilds the preset, changes will be lost"
        self.darkenBtn = elements.styledButton("",
                                               "darkenBulb",
                                               self,
                                               toolTip=toolTip,
                                               style=uic.BTN_TRANSPARENT_BG,
                                               minWidth=15)
        toolTip = "Brighten all lights in the preset\n(Shift faster, ctrl slower, alt reset)\n" \
                  "Rebuilds the preset, changes will be lost"
        self.brightenBtn = elements.styledButton("",
                                                 "brightenBulb",
                                                 self,
                                                 toolTip=toolTip,
                                                 style=uic.BTN_TRANSPARENT_BG,
                                                 minWidth=15)
        # Background Visibility --------------------------------------
        toolTip = "Render the skydome background on/off, if it exists in the current preset\n" \
                  "The skydome will continue to light the scene, the dome texture only will become invisible"
        self.bgVisCheckBx = elements.CheckBox(self.properties.backgroundVisibility.label,
                                              self.properties.backgroundVisibility.value,
                                              self,
                                              toolTip=toolTip)
        self.toolsetWidget.linkProperty(self.bgVisCheckBx, "backgroundVisibility")

        if self.uiMode == UI_MODE_COMPACT:
            self.bgVisCheckBx.setText("Bg Vis")
        # Renderer Button --------------------------------------
        toolTip = "Set the default renderer"
        self.rendererLoaded = elements.iconMenuButtonCombo(DFLT_RNDR_MODES,
                                                           self.properties.rendererIconMenu.value,
                                                           toolTip=toolTip)
        self.toolsetWidget.linkProperty(self.rendererLoaded, "rendererIconMenu")
        # Keep Lights Apply --------------------------------------
        # TODO names seem to conflict this is not a great feature
        toolTip = "Delete the lights while changing the light preset?  Recommended On."
        self.deleteLightsCheckBx = elements.CheckBox("Del",
                                                     self.properties.deleteLightsCheckBx.value,
                                                     self,
                                                     toolTip=toolTip)


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
        :type toolsetWidget: object
        """
        super(GuiCompact, self).__init__(parent=parent, properties=properties, uiMode=uiMode,
                                         toolsetWidget=toolsetWidget)
        # Main Layout --------------------------
        mainLayout = elements.vBoxLayout(self, margins=(uic.WINSIDEPAD, uic.WINTOPPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=0)
        # Grid Layout --------------------------
        attributesGridLayout = elements.GridLayout(margins=(0, 0, 0, 0), spacing=10)

        scaleBtnLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=10)
        scaleBtnLayout.addWidget(self.scaleDownBtn)
        scaleBtnLayout.addWidget(self.scaleUpBtn)

        rotBtnLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=10)
        rotBtnLayout.addWidget(self.rotNegBtn)
        rotBtnLayout.addWidget(self.rotPosBtn)

        intensityBtnLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=10)
        intensityBtnLayout.addWidget(self.darkenBtn)
        intensityBtnLayout.addWidget(self.brightenBtn)

        directoryRendererLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=10)
        directoryRendererLayout.addWidget(self.deleteLightsCheckBx)
        directoryRendererLayout.addWidget(self.rendererLoaded)

        attributesGridLayout.addWidget(self.scaleEdit, 0, 0)
        attributesGridLayout.addWidget(self.scaleFromBtn, 0, 1)
        attributesGridLayout.addLayout(scaleBtnLayout, 0, 2)
        attributesGridLayout.addWidget(self.rotEdit, 0, 3)
        attributesGridLayout.addLayout(rotBtnLayout, 0, 4)

        attributesGridLayout.addWidget(self.intensityEdit, 1, 0)
        attributesGridLayout.addLayout(intensityBtnLayout, 1, 2)
        attributesGridLayout.addWidget(self.bgVisCheckBx, 1, 3)
        attributesGridLayout.addLayout(directoryRendererLayout, 1, 4)

        attributesGridLayout.setColumnStretch(0, 100)
        attributesGridLayout.setColumnStretch(1, 1)
        attributesGridLayout.setColumnStretch(2, 3)
        attributesGridLayout.setColumnStretch(3, 70)
        attributesGridLayout.setColumnStretch(4, 3)

        # Assign To Main Layout --------------------------
        mainLayout.addWidget(self.miniBrowser)
        mainLayout.addWidget(self.resizerWidget)
        mainLayout.addLayout(attributesGridLayout)
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
        :type toolsetWidget: object
        """
        super(GuiAdvanced, self).__init__(parent=parent, properties=properties,
                                          uiMode=uiMode, toolsetWidget=toolsetWidget)

        # Main Layout --------------------------
        mainLayout = elements.vBoxLayout(self, margins=(uic.WINSIDEPAD, uic.WINTOPPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=0)
        # Grid Layout --------------------------
        attributesGridLayout = elements.GridLayout(margins=(0, 0, 0, uic.LRGPAD), spacing=uic.SREG,
                                                   columnMinWidth=(0, 180))
        # Scale Layout --------------------------
        scaleOptionsSmlLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SREG)
        scaleOptionsSmlLayout.addWidget(self.scaleEdit)
        scaleOptionsSmlLayout.addWidget(self.scaleFromBtn)
        # Bottom Checkbox Section --------------------------
        bottomCheckBxLayout = elements.hBoxLayout(margins=(0, 0, 0, uic.REGPAD), spacing=uic.SREG)
        bottomCheckBxLayout.addItem(elements.Spacer(20, 0, QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed))
        bottomCheckBxLayout.addWidget(self.bgVisCheckBx)
        bottomCheckBxLayout.addWidget(self.deleteLightsCheckBx)
        bottomCheckBxLayout.addWidget(self.rendererLoaded)
        # Create Buttons Section --------------------------
        attributesGridLayout.addLayout(scaleOptionsSmlLayout, 0, 0)
        attributesGridLayout.addWidget(self.scaleDownBtn, 0, 1)
        attributesGridLayout.addWidget(self.scaleUpBtn, 0, 2)

        attributesGridLayout.addWidget(self.rotEdit, 1, 0)
        attributesGridLayout.addWidget(self.rotNegBtn, 1, 1)
        attributesGridLayout.addWidget(self.rotPosBtn, 1, 2)

        attributesGridLayout.addWidget(self.intensityEdit, 2, 0)
        attributesGridLayout.addWidget(self.darkenBtn, 2, 1)
        attributesGridLayout.addWidget(self.brightenBtn, 2, 2)
        # Assign To Main Layout --------------------------
        mainLayout.addWidget(self.miniBrowser)
        mainLayout.addWidget(self.resizerWidget)
        mainLayout.addLayout(attributesGridLayout)
        mainLayout.addLayout(bottomCheckBxLayout)
        mainLayout.addStretch(1)
