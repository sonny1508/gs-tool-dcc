import os

from zoo.apps.toolsetsui.ext.renderers import RendererMixin
from zoovendor.Qt import QtWidgets, QtCore

from zoo.apps.light_suite import modelhdrskydome
from zoo.libs.maya.cmds.workspace import mayaworkspace

from zoo.libs.maya.cmds.lighting import lightsmultihdri, lightconstants
from zoo.libs.zooscene import zooscenefiles
from zoo.preferences.interfaces import lightsuiteinterfaces
from zoo.libs.maya.cmds.renderer import rendererload
from zoo.apps.toolsetsui.mixins import MiniBrowserMixin
from zoo.apps.toolsetsui.widgets.toolsetresizer import ToolsetResizer
from zoo.apps.toolsetsui import toolsetcallbacks
from zoo.apps.toolsetsui.widgets import toolsetwidget

from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements

from zoo.libs.utils import output

DFLT_RNDR_MODES = [("arnold", "Arnold"), ("vray", "VRay"), ("redshift", "Redshift"), ("renderman", "Renderman")]
UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1

GENKEYS = [lightconstants.HDRI_INTENSITY, lightconstants.HDRI_ROTATE, lightconstants.HDRI_SCALE,
           lightconstants.HDRI_LIGHTVISIBILITY]

class HdriSkydomeLights(toolsetwidget.ToolsetWidget, RendererMixin, MiniBrowserMixin):
    ignoreInstantApply = None  # type: object
    id = "hdriSkydomeLights"
    uiData = {"label": "HDRI Skydomes",
              "icon": "sun",
              "tooltip": "Create and manage HDRI Skydome IBL attributes with this tool",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-create-hdr-skydomes/"
              }

    # ------------------------------------
    # START UP
    # ------------------------------------

    def preContentSetup(self):
        """First code to run"""
        self.toolsetWidget = self  # needed for callback decorators
        self.lightSuitePrefInterface = lightsuiteinterfaces.lightSuiteInterface()
        self.setAssetPreferences(self.lightSuitePrefInterface.skydomesPreference)
        self.initRendererMixin(disableVray=False, disableMaya=True)
        # For virtual sliders -----------------
        self._skydomeTransform = None
        self._skydomeShape = None
        self._skydomeRot = None
        self._skydomeIntensity = None

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
        self.hdriInstance = lightsmultihdri.emptyInstance()
        self.uiconnections()
        self.refreshUpdateUI()
        self.disableEnableSliders()

    def currentWidget(self):
        """ Current active widget

        :return:
        :rtype:  AllWidgets
        """
        return super(HdriSkydomeLights, self).currentWidget()

    def widgets(self):
        """ List of widgets

        :return:
        :rtype: list[AllWidgets]
        """
        return super(HdriSkydomeLights, self).widgets()

    # ------------------
    # PROPERTIES
    # ------------------

    def initializeProperties(self):
        return [{"name": "rendererIconMenu", "label": "", "value": "Arnold"}]

    # ------------------
    # MOUSE OVER UI
    # ------------------

    def enterEvent(self, event):
        """Update selection on enter event
        """
        self.refreshUpdateUI()  # update GUI from current in scene selection
        self.disableEnableSliders()

    # ------------------------------------
    # POPUP WINDOWS
    # ------------------------------------

    def ui_loadRenderer(self):
        message = "The {} renderer isn't loaded. Load now?".format(self.properties.rendererIconMenu.value)
        # parent is None to parent to Maya to fix stylesheet issues
        okPressed = elements.MessageBox.showOK(title="Load Renderer", parent=None, message=message)
        return okPressed

    # ------------------------------------
    # CALLBACKS
    # ------------------------------------

    def selectionChanged(self, selection):
        """Run when the callback selection changes, updates the GUI if an object is selected

        Callbacks are handled automatically by toolsetcallbacks.py which this class inherits"""
        if not selection:  # then don't update
            return
        # self.refreshUpdateUIFromSelection()  # will update the GUI

    # ------------------------------------
    # RECEIVE RENDERER FROM OTHER UIS
    # ------------------------------------

    def global_receiveRendererChange(self, renderer):
        """Receives from other GUIs, changes the renderer when it is changed Overridden"""
        pass
        """if renderer == "VRay" or renderer == "Maya":
            return  # Ignore as this UI doesn't support VRay or Maya yet.
        super(HdriSkydomeLights, self).global_receiveRendererChange(renderer)"""

    # ------------------------------------
    # UTILS
    # ------------------------------------

    def loadImagePath(self):
        """Loads a Open File Window to browse for the HDRI Image on disk"""
        if not self.checkRenderLoaded(self.properties.rendererIconMenu.value):
            return

        directory = ""
        imagePath = self.properties.imagePathTxt.value

        if imagePath:  # Gets the directory from the current image path, if doesn't exist then directory = ""
            directory = os.path.dirname(imagePath)
            if not os.path.exists(directory):
                directory = ""

        if not directory:  # If no directory found then sets to sourceImages in project directory
            projectDirectory = mayaworkspace.getCurrentMayaWorkspace()
            directory = os.path.join(projectDirectory, "sourceImages/")

        if not os.path.exists(directory):  # no directory found so use home
            directory = os.path.expanduser("~")

        # Open dialog ------------------------------------------------
        fullFilePath, filter = QtWidgets.QFileDialog.getOpenFileName(self, "Open File", directory)
        if not str(fullFilePath):
            return

        self.properties.imagePathTxt.value = str(fullFilePath)
        self.toolsetWidget.updateFromProperties()

        self.setSkydomeLight()  # Sets all settings from UI to the current skydome

    # ------------------------------------
    # UI
    # ------------------------------------

    def disableEnableAttr(self, genKey, enable=True):
        """Disables or enables a widget based off it's key dict for both UIs advanced and compact.

        Some widgets are only in advanced mode.

        :param genKey: a generic key from shdCnst.ATTR_KEY_LIST
        :type genKey: str
        :param enable: Enable the widget True or disable with False
        :type enable: bool
        """
        if genKey == lightconstants.HDRI_INTENSITY:
            for w in self.widgets():
                w.intensityFloatSldr.setEnabled(enable)
        elif genKey == lightconstants.HDRI_ROTATE:
            for w in self.widgets():
                w.rotateFloatSldr.setEnabled(enable)
        elif genKey == lightconstants.HDRI_SCALE:
            for w in self.widgets():
                w.scaleFloatSldr.setEnabled(enable)
                w.bgInvertCheckbox.setEnabled(enable)  # is scale related
        elif genKey == lightconstants.HDRI_LIGHTVISIBILITY:
            for w in self.widgets():
                w.bgVisCheckbox.setEnabled(enable)

    def disableEnableSliders(self):
        """Enables or disables the ui sliders depending on the shader type
        """
        if not self._checkHdriInstance():
            return
        disableAttrs = list(self.hdriInstance.connectedAttrs().keys())
        for genKey in GENKEYS:  # HDRI generic keys: intensity, rotation, scale, bg visibility
            if genKey in disableAttrs:
                self.disableEnableAttr(genKey, enable=False)
            else:
                self.disableEnableAttr(genKey, enable=True)

    # ------------------------------------
    # CREATE LIGHTS
    # ------------------------------------

    def setHdriFromUI(self):
        """Takes all the UI settings and applies them to the current HDRI skydome.
        """
        if not self._checkHdriInstance():
            return
        self.hdriInstance.setImagePath(self.properties.imagePathTxt.value)
        self.disableEnableSliders()

    def createUpdateSkydomeLight(self):
        """Creates the skydome light
        """
        if not rendererload.getRendererIsLoaded(self.properties.rendererIconMenu.value):  # not loaded open window
            if not elements.checkRenderLoaded(self.properties.rendererIconMenu.value):
                return
        # Returns a single HDRI instance from selected or scene.
        self.hdriInstance = lightsmultihdri.hdriInstanceRenderer(self.properties.rendererIconMenu.value, message=False)
        if not self.hdriInstance:
            name = lightconstants.HDRI_DEFAULT_VALUES[lightconstants.HDRI_NAME]
            self.hdriInstance = lightsmultihdri.createDefaultHdriRenderer(self.properties.rendererIconMenu.value,
                                                                          hdriName=name,
                                                                          lightGroup=True,
                                                                          suffixName=True,
                                                                          select=True)
        self.disableEnableSliders()

    # ------------------------------------
    # SAVE EXTRA OFFSET DATA
    # ------------------------------------

    def saveDefaultOffsetSettings(self):
        """Saves a JSON file and stores the default settings intensityMultiplier and rotationOffset"""
        selThumbHdriPath = self.currentWidget().miniBrowser.itemFilePath()
        if not selThumbHdriPath:
            output.displayWarning("Please select a thumbnail HDRI image to save default values.")
            return
        lightsmultihdri.saveExtraDataJson(self.properties.intensityMultiplier.value,
                                          self.properties.rotationOffset.value,
                                          selThumbHdriPath)
        output.displayInfo("Default Settings saved for: `{}`".format(selThumbHdriPath))
        self.updateFromProperties()

    def loadDefaultOffsetSettings(self):
        selThumbHdriPath = self.currentWidget().miniBrowser.itemFilePath()
        if not selThumbHdriPath:
            return
        intensityMult, rotOffset = lightsmultihdri.loadExtraDataJson(selThumbHdriPath)
        if intensityMult:
            self.properties.intensityMultiplier.value = intensityMult
        else:
            self.properties.intensityMultiplier.value = 1.0
        if rotOffset:
            self.properties.rotationOffset.value = rotOffset
        else:
            self.properties.rotationOffset.value = 0.0

    # ------------------------------------
    # SET (APPLY) LIGHTS
    # ------------------------------------

    def _checkHdriInstance(self):
        if not self.hdriInstance:
            return False
        if not self.hdriInstance.exists():  # Then use default shader type
            return False
        return True

    @toolsetcallbacks.ignoreCallbackDecorator
    @toolsetwidget.ToolsetWidget.undoDecorator
    def setImagePath(self, text=None):
        """Run when changing the image path text, apples the image in Maya"""
        if not self._checkHdriInstance():
            return
        self.hdriInstance.setImagePath(self.properties.imagePathTxt.value)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def setName(self, text=None):
        """Run when changing the image path text, apples the image in Maya"""
        if not self._checkHdriInstance():
            return
        self.hdriInstance.setName(self.properties.hdriName.value)

    def setIntensitySldr(self):
        """Sets the Skydome intensity and applies in Maya"""
        if not self._checkHdriInstance():
            return
        self.hdriInstance.setIntensityAndMultiply(self.properties.intensityFloatSldr.value,
                                                  self.properties.intensityMultiplier.value)

    def setRotateSldr(self):
        """Sets the Skydome's Rotate Y value and applies in Maya"""
        if not self._checkHdriInstance():
            return
        rot = list(self.hdriInstance.rotate())
        rot[1] = self.properties.rotateFloatSldr.value
        self.hdriInstance.setRotateAndOffset(rot, self.properties.rotationOffset.value)

    def setRotateOffset(self):
        if not self._checkHdriInstance():
            return
        self.hdriInstance.setRotateOffset(self.properties.rotationOffset.value)

    def setIntensityMultiply(self):
        if not self._checkHdriInstance():
            return
        self.hdriInstance.setIntensityMultiply(self.properties.intensityMultiplier.value)

    def setScaleSldr(self):
        """Sets the Skydome's Scale as uniform XYZ from the slider and applies in Maya"""
        if not self._checkHdriInstance():
            return
        scale = self.properties.scaleFloatSldr.value
        self.hdriInstance.setScale([scale, scale, scale])

    @toolsetcallbacks.ignoreCallbackDecorator
    @toolsetwidget.ToolsetWidget.undoDecorator
    def setBackgroundVisibility(self, check=None):
        """Sets the Skydome's background visibility setting and applies in Maya"""
        if not self._checkHdriInstance():
            return
        self.hdriInstance.setBackgroundVis(self.properties.bgVisCheckbox.value)

    @toolsetcallbacks.ignoreCallbackDecorator
    @toolsetwidget.ToolsetWidget.undoDecorator
    def setInvert(self, check=None):
        """Inverts the scale of the skydome or reverses the image direction and applies in Maya"""
        if not self._checkHdriInstance():
            return
        self.hdriInstance.setInvert(self.properties.bgInvertCheckbox.value)

    @toolsetcallbacks.ignoreCallbackDecorator
    @toolsetwidget.ToolsetWidget.undoDecorator
    def deleteHdri(self):
        """Deletes the Skydome's and texture nodes from the scene in Maya"""
        if not self._checkHdriInstance():
            return
        self.hdriInstance.delete()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def selectTransform(self):
        """Selects the transform node of the light"""
        if not self._checkHdriInstance():
            return
        self.hdriInstance.selectTransform()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def selectShape(self):
        """Selects the shape node of the light"""
        if not self._checkHdriInstance():
            return
        self.hdriInstance.selectShape()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def setCreateSkydomeLight(self, browserVariable=None):
        """Either creates a new light or sets an existing light with the current settings.

        :param browserVariable: Ignore not used
        :type browserVariable:
        """
        self.createUpdateSkydomeLight()  # Creates or updates an existing HDRI light in the scene. self.hdriInstance
        self.properties.imagePathTxt.value = self.currentWidget().miniBrowser.itemFilePath()
        self.loadDefaultOffsetSettings()  # updates intensity multiplier and rotate offset
        self.updateFromProperties()
        self.setSkydomeLight(ignoreName=True)  # Applies all UI settings

    def setSkydomeLight(self, ignoreName=False):
        """Sets all UI settings and applies to the current Skydome light"""
        if not self._checkHdriInstance():
            return
        scaleV = self.properties.scaleFloatSldr.value
        rot = self.hdriInstance.rotate()
        name = self.properties.hdriName.value
        if name and not ignoreName:
            self.hdriInstance.setName(name)
        self.hdriInstance.setImagePath(self.properties.imagePathTxt.value)
        self.hdriInstance.setIntensityAndMultiply(self.properties.intensityFloatSldr.value,
                                                  self.properties.intensityMultiplier.value)
        self.hdriInstance.setScale([scaleV, scaleV, scaleV])
        self.hdriInstance.setInvert(self.properties.bgInvertCheckbox.value)
        self.hdriInstance.setBackgroundVis(self.properties.bgVisCheckbox.value)
        self.hdriInstance.setRotateAndOffset([rot[0], self.properties.rotateFloatSldr.value, rot[2]],
                                             self.properties.rotationOffset.value)

    # ------------------------------------
    # GET (RETRIEVE) LIGHTS
    # ------------------------------------

    def refreshUpdateUI(self):
        """Updates the UI from the currently selected or first found Skydome"""
        if not rendererload.getRendererIsLoaded(self.properties.rendererIconMenu.value):
            return  # Renderer is not loaded so can't update UI
        self.hdriInstance = lightsmultihdri.hdriInstanceRenderer(self.properties.rendererIconMenu.value, message=False)
        if not self._checkHdriInstance():
            return
        # Intensity -------------------------------------------------------
        intensity, intensityMultiplier = self.hdriInstance.intensityAndMultiply()
        self.properties.intensityFloatSldr.value = intensity
        self.properties.intensityMultiplier.value = intensityMultiplier
        # Rotate -------------------------------------------------------
        rotate, rotateOffset = self.hdriInstance.rotateAndOffset()
        self.properties.rotateFloatSldr.value = rotate[1]
        self.properties.rotationOffset.value = rotateOffset
        # Other -----------------------------------------------------------
        self.properties.hdriName.value = self.hdriInstance.shortName()
        self.properties.scaleFloatSldr.value = self.hdriInstance.scale()[0]
        self.properties.imagePathTxt.value = self.hdriInstance.imagePath()
        self.properties.bgVisCheckbox.value = self.hdriInstance.backgroundVis()
        self.properties.bgInvertCheckbox.value = self.hdriInstance.invert()
        self.updateFromProperties()  # updates the UI with new values

    # ------------------------------------
    # OFFSET ATTRIBUTES
    # ------------------------------------

    # ------------------------------------
    # LIGHT NAME/RENAME/DELETE
    # ------------------------------------

    def renameSkydome(self):
        """Renames the asset on disk"""
        currentFileNoExt = self.currentWidget().browserModel.currentImage
        skydomeFullPath = self.currentWidget().miniBrowser.selectedMetadata()['zooFilePath']
        if not currentFileNoExt:  # no image has been selected
            output.displayWarning("Please select an thumbnail image to rename.")
            return
        # Get the current directory
        message = "Rename Related `{}` Files As:".format(currentFileNoExt)
        renameText = elements.MessageBox.inputDialog(title="Rename HDRI Skydome", text=currentFileNoExt,
                                                     parent=None,
                                                     message=message)
        if not renameText:
            return
        # Do the rename
        fileRenameList = zooscenefiles.renameZooSceneOnDisk(renameText, skydomeFullPath)
        if not fileRenameList:  # shouldn't happen for Skydomes?
            output.displayWarning("Files could not be renamed, they are probably in use by the current scene. "
                                  "Do not have the renamed assets loaded in the scene, "
                                  "or check your file permissions.")
            return
        output.displayInfo("Success: Files `{}*` Have Been Renamed To `{}*`".format(currentFileNoExt, renameText))
        self.refreshThumbs()

    def deleteSkydomePopup(self):
        """Popup window that asks the user if they want to delete the currently selected asset from disk?"""
        filenameNoExt = self.currentWidget().browserModel.currentImage
        if not filenameNoExt:
            output.displayWarning("Nothing selected. Please select an image to delete.")
        fullImagePath = self.currentWidget().miniBrowser.selectedMetadata()['zooFilePath']
        filenameWithExt = os.path.basename(fullImagePath)
        # Build popup window
        message = "Warning: Delete the preset `{}` and it's dependencies?  " \
                  "This will permanently delete these file/s from disk?".format(filenameWithExt)
        result = elements.MessageBox.showOK(title="Delete Image From Disk?",
                                            message=message)  # None will parent to Maya
        # After answering Ok or cancel
        if result:  # Ok was pressed
            filesFullPathDeleted = zooscenefiles.deleteZooSceneFiles(fullImagePath, message=True)
            output.displayInfo("Success, File/s Deleted: {}".format(filesFullPathDeleted))
            self.refreshThumbs()

    def refreshImages(self):
        # This should be automated and shouldn't need to be called in the dots menu
        self.refreshThumbs()

    # ------------------------------------
    # BROWSER VIRTUAL SLIDERS
    # ------------------------------------

    def sliderPressed(self):
        """ Get the skydome information and open the undo chunk if found
        """
        self.hdriInstance = lightsmultihdri.hdriInstanceRenderer(self.properties.rendererIconMenu.value, message=False)
        if not self._checkHdriInstance():
            self._skydomeTransform = None
            self._skydomeShape = None
            self._skydomeRot = None
            self._skydomeIntensity = None
            output.displayWarning("No {} HDRI Skydomes found, please build or select a "
                                  "skydome.".format(self.properties.rendererIconMenu.value))
            return
        self._skydomeTransform = self.hdriInstance.node.fullPathName()
        self._skydomeShape = self.hdriInstance.shapeName()
        self._skydomeRot = list(self.hdriInstance.rotate())
        self._skydomeIntensity = self.hdriInstance.intensity()
        self.openUndoChunk()

    def virtualSliderScrolled(self, event):
        """ Slider scrolled, code is lean/eifficient for fast updates for UI and the skydome.

        :param event: A tuple x and y offset of the virtual slider (21.0, 1.0021)
        :type event: :class:`zoo.libs.pyqt.extended.imageview.thumbnail.virtualslider.MouseSlideEvent`
        """
        if not self._skydomeRot:
            return
        x, y = event.value
        if event.direction == elements.VirtualSlider.Horizontal:  # Direction Horizontal ----------------------------
            if event.modifiers == QtCore.Qt.ShiftModifier:
                rotY = self._skydomeRot[1] - (x / 2.5)
            elif event.modifiers == QtCore.Qt.ControlModifier:
                rotY = self._skydomeRot[1] - (x / 10)
            else:
                rotY = self._skydomeRot[1] - (x / 5)
            # Set the rotation of the skydome ---------------------------
            self.hdriInstance.setRotateLean([self._skydomeRot[0], rotY, self._skydomeRot[2]], self._skydomeTransform)
            for widget in self.widgets():  # update UI
                widget.rotateFloatSldr.blockSignals(True)
                widget.rotateFloatSldr.setText(rotY-self.properties.rotationOffset.value)
                widget.rotateFloatSldr.blockSignals(False)
        else:  # Direction is up/down -------------------------------------------------------------------------
            if event.modifiers == QtCore.Qt.ShiftModifier:
                intensity = self._skydomeIntensity + (y * 1.2)
            elif event.modifiers == QtCore.Qt.ControlModifier:
                intensity = self._skydomeIntensity + (y * 0.1)
            else:
                intensity = self._skydomeIntensity + (y * 0.6)
            if intensity < 0.0:
                intensity = 0.0
            self.hdriInstance.setIntensity(intensity)
            # Update UI -------------------------------------------------
            if self.properties.intensityMultiplier.value and intensity:
                uiIntensity = intensity / self.properties.intensityMultiplier.value
            else:
                uiIntensity = 0.0
            for widget in self.widgets():  # update UI
                widget.intensityFloatSldr.blockSignals(True)
                widget.intensityFloatSldr.setText(uiIntensity)
                widget.intensityFloatSldr.blockSignals(False)

    def sliderReleased(self, event):
        """ Save all the settings into the properties

        :param event: A tuple x and y offset of the virtual slider (21.0, 1.0021)
        :type event: :class:`zoo.libs.pyqt.extended.imageview.thumbnail.virtualslider.MouseSlideEvent`
        """
        self.refreshUpdateUI()
        self.closeUndoChunk()

    def setDefaultSettings(self):
        """Updates the intensity multiplier and rotation offset and sets intensity to 1.0 and rotation to 0.0"""
        self.properties.intensityMultiplier.value *= self.properties.intensityFloatSldr.value
        self.properties.rotationOffset.value += self.properties.rotateFloatSldr.value
        self.properties.intensityFloatSldr.value = 1.0
        self.properties.rotateFloatSldr.value = 0.0
        self.updateFromProperties()

    def refreshOffset(self):
        """Updates the float sliders and sets intensity multiply to 1.0 and rotation offset to 0.0"""
        self.properties.intensityFloatSldr.value *= self.properties.intensityMultiplier.value
        self.properties.rotateFloatSldr.value += self.properties.rotationOffset.value
        self.properties.intensityMultiplier.value = 1.0
        self.properties.rotationOffset.value = 0.0
        self.updateFromProperties()

    # ------------------------------------
    # CONNECTIONS
    # ------------------------------------

    def uiconnections(self):
        """Hooks up the actual button/widgets functionality
        """
        for widget in self.widgets():
            # dots menu viewer
            widget.miniBrowser.dotsMenu.applyAction.connect(self.setCreateSkydomeLight)
            widget.miniBrowser.dotsMenu.renameAction.connect(self.renameSkydome)
            widget.miniBrowser.dotsMenu.deleteAction.connect(self.deleteSkydomePopup)
            widget.miniBrowser.dotsMenu.refreshAction.connect(self.refreshImages)
            # thumbnail viewer
            widget.browserModel.doubleClicked.connect(self.setCreateSkydomeLight)
            # Textbox modified -------------
            widget.imagePathTxt.edit.textModified.connect(self.setImagePath)
            # Slider Undo Chunks ------------------------------
            floatSliderList = [widget.intensityFloatSldr, widget.rotateFloatSldr, widget.scaleFloatSldr]
            for floatSlider in floatSliderList:
                floatSlider.sliderPressed.connect(self.openUndoChunk)
                floatSlider.sliderReleased.connect(self.closeUndoChunk)
            # Sliders -------------------
            widget.intensityFloatSldr.numSliderChanged.connect(self.setIntensitySldr)
            widget.rotateFloatSldr.numSliderChanged.connect(self.setRotateSldr)
            widget.scaleFloatSldr.numSliderChanged.connect(self.setScaleSldr)
            # Offset Multiply
            widget.rotationOffset.textModified.connect(self.setRotateOffset)
            widget.intensityMultiplier.textModified.connect(self.setIntensityMultiply)
            # Checkboxes -------------------
            widget.bgVisCheckbox.stateChanged.connect(self.setBackgroundVisibility)
            widget.bgInvertCheckbox.stateChanged.connect(self.setInvert)
            # Buttons -------------------------
            widget.deleteBtn.clicked.connect(self.deleteHdri)
            widget.selectBtn.clicked.connect(self.selectTransform)
            widget.selectShapeBtn.clicked.connect(self.selectShape)
            widget.browseBtn.clicked.connect(self.loadImagePath)
            # Change renderer
            widget.rendererIconMenu.actionTriggered.connect(self.global_changeRenderer)
            # Virtual Sliders -------------------------------------
            widget.miniBrowser.sliderChanged.connect(self.virtualSliderScrolled)
            widget.miniBrowser.sliderPressed.connect(self.sliderPressed)
            widget.miniBrowser.sliderReleased.connect(self.sliderReleased)
            widget.imagePathTxt.edit.textModified.connect(self.setImagePath)
        self.advancedWidget.hdriName.textModified.connect(self.setName)
        self.advancedWidget.addSettingsBtn.clicked.connect(self.setDefaultSettings)
        self.advancedWidget.refreshOffsetBtn.clicked.connect(self.refreshOffset)
        self.advancedWidget.intensityMultiplier.textModified.connect(self.setIntensitySldr)
        self.advancedWidget.rotationOffset.textModified.connect(self.setRotateSldr)
        self.advancedWidget.saveBtn.clicked.connect(self.saveDefaultOffsetSettings)
        """self.advancedWidget.nameTxt.edit.textModified.connect(self.instantIBLRename)
        self.advancedWidget.browseBtn.clicked.connect(self.loadHDRSkydomeImage)
        self.advancedWidget.scaleInvertChkBx.stateChanged.connect(self.instantSetIBL)
        self.advancedWidget.scaleVEdit.textModified.connect(self.instantSetIBL)
        """
        # Callback connections
        self.selectionCallbacks.callback.connect(self.selectionChanged)  # monitor selection
        self.toolsetActivated.connect(self.startSelectionCallback)
        self.toolsetDeactivated.connect(self.stopSelectionCallback)


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
        :type toolsetWidget: qtObject

        """
        super(AllWidgets, self).__init__(parent=parent)

        self.toolsetWidget = toolsetWidget
        self.properties = properties
        self.uiMode = uiMode
        # Rename Delete Dots Menu  ------------------------------------

        # Thumbnail Viewer ---------------------------------------
        lightSuitePref = self.toolsetWidget.lightSuitePrefInterface.skydomesPreference
        uniformIcons = lightSuitePref.browserUniformIcons()
        # viewer widget and model
        self.miniBrowser = elements.MiniBrowser(toolsetWidget=toolsetWidget, columns=3,
                                                fixedHeight=382,
                                                uniformIcons=uniformIcons,
                                                itemName="IBL",
                                                applyIcon="sun", parent=self,
                                                selectDirectoriesActive=True,
                                                virtualSlider=True)
        self.miniBrowser.setSliderSettings(slowSpeedXY=(.2, 0.01), speedXY=(2, 0.02), fastSpeedXY=(20, 0.05))
        self.miniBrowser.dotsMenu.setSnapshotActive(True)
        self.miniBrowser.dotsMenu.setCreateActive(False)
        self.miniBrowser.dotsMenu.setDirectoryActive(False)

        self.browserModel = modelhdrskydome.HdrSkydomeViewerModel(self.miniBrowser,
                                                                  directories=lightSuitePref.browserFolderPaths(),
                                                                  uniformIcons=uniformIcons,
                                                                  assetPreference=lightSuitePref)
        self.miniBrowser.setModel(self.browserModel)
        self.resizerWidget = ToolsetResizer(toolsetWidget=self.toolsetWidget, target=self.miniBrowser)
        # Name -----------------------------------------------
        tooltip = "Change the HDRI Light's name."
        self.hdriName = elements.StringEdit(label="HDRI Name", toolTip=tooltip, labelRatio=10, editRatio=41)
        # Intensity ------------------------------------------
        self.intensityFloatSldr = elements.FloatSlider(label="Intensity",
                                                       defaultValue=1.0,
                                                       sliderMax=5.0,
                                                       dynamicMax=True,
                                                       sliderRatio=20,
                                                       labelBtnRatio=14)
        # Rotation ------------------------------------------
        self.rotateFloatSldr = elements.FloatSlider(label="Rotation",
                                                    defaultValue=0.0,
                                                    sliderMax=180.0,
                                                    sliderMin=-180,
                                                    dynamicMin=True,
                                                    dynamicMax=True,
                                                    sliderRatio=20,
                                                    labelBtnRatio=14)
        # Scale ------------------------------------------
        toolTip = "Would you like to see the skydome image in renders or not."
        self.scaleFloatSldr = elements.FloatSlider(label="Scale",
                                                   defaultValue=2.5,
                                                   sliderMax=15.0,
                                                   dynamicMax=True,
                                                   sliderRatio=20,
                                                   labelBtnRatio=14,
                                                   toolTip=toolTip)
        # HDRI Image Path Location --------------------------------------
        toolTip = "The path of the skydome image"
        self.imagePathTxt = elements.StringEdit("HDRI Image",
                                                "",
                                                parent=self,
                                                editWidth=None,
                                                labelRatio=115,
                                                editRatio=400,
                                                toolTip=toolTip)
        toolTip = "Browse to load a skydome image"
        self.browseBtn = elements.styledButton("",
                                               "browse",
                                               self,
                                               toolTip=toolTip,
                                               style=uic.BTN_DEFAULT,
                                               minWidth=uic.BTN_W_ICN_MED)
        # Background Vis -----------------------------------
        toolTip = "Would you like to see the skydome image in renders or not."
        self.bgVisCheckbox = elements.CheckBox(label="BG Visibility", checked=True, right=True,
                                               labelRatio=20, boxRatio=20, toolTip=toolTip)
        # Invert Image Vis -----------------------------------
        toolTip = "Inverts the direction of the image with a negative scale. \n" \
                  "Can correct backwards text and invert the lighting direction."
        self.bgInvertCheckbox = elements.CheckBox(label="Invert Image", checked=False, right=True,
                                                  labelRatio=20, boxRatio=20, toolTip=tooltip)
        self.selectBtn = elements.styledButton("", "cursorSelect",
                                               self,
                                               toolTip=toolTip,
                                               style=uic.BTN_TRANSPARENT_BG,
                                               minWidth=uic.BTN_W_ICN_REG)
        self.selectShapeBtn = elements.styledButton("", "ibl",
                                                    self,
                                                    toolTip=toolTip,
                                                    style=uic.BTN_TRANSPARENT_BG,
                                                    minWidth=uic.BTN_W_ICN_REG)
        self.deleteBtn = elements.styledButton("", "trash",
                                               self,
                                               toolTip=toolTip,
                                               style=uic.BTN_TRANSPARENT_BG,
                                               minWidth=uic.BTN_W_ICN_REG)
        # Renderer Button --------------------------------------
        toolTip = "Change the renderer to Arnold, Redshift or Renderman. "
        self.rendererIconMenu = elements.iconMenuButtonCombo(DFLT_RNDR_MODES,
                                                             self.properties.rendererIconMenu.value,
                                                             toolTip=toolTip)
        # Save Default Settings -----------------------------------------------------
        toolTip = "This value will multiply the intensity of the skydome light.  \n" \
                  "Useful for saving with a HDRI Skydome, some Skydomes can be too dark or light \n" \
                  "and this value can be saved as a new default value. "
        self.intensityMultiplier = elements.FloatEdit("Intensity Multiplier", editText=1.0, labelRatio=10, editRatio=6,
                                                      toolTip=toolTip)
        toolTip = "This value will offset the rotation of the skydome light.  \n" \
                  "Useful for saving with a HDRI Skydome, some Skydomes may be oriented badly by default. \n" \
                  "This value can be saved as a new default value. "
        self.rotationOffset = elements.FloatEdit("Rotation Offset", editText=0.0, labelRatio=10, editRatio=6,
                                                 toolTip=toolTip, rounding=1)
        # Arrow Button --------------------------------------
        toolTip = "Add the current values as multiplier/offset values. \n" \
                  "Also resets the main settings. "
        self.addSettingsBtn = elements.styledButton("",
                                                    "arrowLeft",
                                                    toolTip=toolTip,
                                                    style=uic.BTN_TRANSPARENT_BG,
                                                    minWidth=15)
        # Refresh Button --------------------------------------
        toolTip = "Add the current values as multiplier/offset values. \n" \
                  "Also resets the main settings. "
        self.refreshOffsetBtn = elements.styledButton("",
                                                    "reload2",
                                                    toolTip=toolTip,
                                                    style=uic.BTN_TRANSPARENT_BG,
                                                    minWidth=15)
        # Save Scene Button --------------------------------------
        toolTip = "Save the current values to disk. \n" \
                  "The next time images are loaded multiplier/offsets will default to these values."
        self.saveBtn = elements.styledButton("",
                                             icon="save",
                                             toolTip=toolTip,
                                             style=uic.BTN_DEFAULT)
        # Advanced Collapsable -------------------------------------------------------------------------
        self.advancedCollapsable = elements.CollapsableFrameThin("Other Settings", collapsed=True)


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
        super(GuiCompact, self).__init__(parent=parent, properties=properties,
                                         uiMode=uiMode, toolsetWidget=toolsetWidget)
        # Main Layout ---------------------------------------
        mainLayout = elements.vBoxLayout(self,
                                         margins=(uic.WINSIDEPAD, uic.WINTOPPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SREG)
        # HDRI Image location section -----------------------------
        hdriImageLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SREG)
        hdriImageLayout.addWidget(self.imagePathTxt, 20)
        hdriImageLayout.addWidget(self.browseBtn, 1)
        # Bottom Layout -----------------------------
        botLayout = elements.hBoxLayout(margins=(0, 0, 0, 0))
        botLayout.addWidget(self.bgVisCheckbox, 36)
        botLayout.addWidget(self.bgInvertCheckbox, 40)
        botLayout.addWidget(self.selectBtn, 1)
        botLayout.addWidget(self.selectShapeBtn, 1)
        botLayout.addWidget(self.deleteBtn, 1)
        botLayout.addWidget(self.rendererIconMenu, 1)
        # Add to main layout --------------------------------------
        mainLayout.addWidget(self.miniBrowser)
        mainLayout.addWidget(self.resizerWidget)
        mainLayout.addWidget(self.intensityFloatSldr)
        mainLayout.addWidget(self.rotateFloatSldr)
        mainLayout.addLayout(hdriImageLayout)
        mainLayout.addLayout(botLayout)


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
        # Main Layout ---------------------------------------
        mainLayout = elements.vBoxLayout(self,
                                         margins=(uic.WINSIDEPAD, uic.WINTOPPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SREG)
        # HDRI Image location section -----------------------------
        hdriImageLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SREG)
        hdriImageLayout.addWidget(self.imagePathTxt, 20)
        hdriImageLayout.addWidget(self.browseBtn, 1)
        # Default Settings --------------------
        defaultsLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SLRG)
        defaultsLayout.addWidget(self.intensityMultiplier, 7)
        defaultsLayout.addWidget(self.rotationOffset, 7)
        defaultsLayout.addWidget(self.addSettingsBtn, 1)
        defaultsLayout.addWidget(self.refreshOffsetBtn, 1)
        defaultsLayout.addWidget(self.saveBtn, 1)
        # Bottom Layout -----------------------------
        botLayout = elements.hBoxLayout(margins=(0, 0, 0, 0))
        botLayout.addWidget(self.bgVisCheckbox, 36)
        botLayout.addWidget(self.bgInvertCheckbox, 40)
        botLayout.addWidget(self.selectBtn, 1)
        botLayout.addWidget(self.selectShapeBtn, 1)
        botLayout.addWidget(self.deleteBtn, 1)
        botLayout.addWidget(self.rendererIconMenu, 1)
        # Add to main layout --------------------------------------
        mainLayout.addWidget(self.miniBrowser)
        mainLayout.addWidget(self.resizerWidget)
        mainLayout.addWidget(self.hdriName)
        mainLayout.addWidget(self.intensityFloatSldr)
        mainLayout.addWidget(self.rotateFloatSldr)
        mainLayout.addWidget(self.scaleFloatSldr)
        mainLayout.addWidget(elements.LabelDivider(text="Modify/Save Default Settings"))
        mainLayout.addLayout(defaultsLayout)
        mainLayout.addWidget(elements.LabelDivider(text="Other Settings"))
        mainLayout.addLayout(hdriImageLayout)
        mainLayout.addLayout(botLayout)
