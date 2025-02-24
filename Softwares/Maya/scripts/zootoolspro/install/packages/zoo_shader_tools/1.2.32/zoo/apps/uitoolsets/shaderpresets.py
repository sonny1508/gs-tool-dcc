import os

from zoo.apps.shader_tools.shadermixin import ShaderMixin
from zoo.apps.toolsetsui.ext.renderers import RendererMixin
from zoo.apps.toolsetsui.mixins import MiniBrowserMixin
from zoovendor.Qt import QtWidgets, QtCore

from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements
from zoo.libs.utils import output, color

from zoo.libs.zooscene.constants import ZOOSCENE_EXT

from zoo.apps.toolsetsui.widgets.toolsetresizer import ToolsetResizer
from zoo.apps.toolsetsui.widgets import toolsetwidget

from zoo.preferences.interfaces import coreinterfaces, shaderinterfaces

from zoo.core.util import env
from zoo.libs.zooscene import zooscenefiles
from zoo.libs.pyqt.extended.imageview.models import zooscenemodel

if env.isMaya():
    from zoo.libs.maya.cmds.shaders import shaderutils, shadermultirenderer as shdmult, shadermulti, shdmultconstants
    from zoo.libs.maya.cmds.renderer import rendererload, exportabcshaderlights
    from maya import cmds

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1


class ShaderPresets(toolsetwidget.ToolsetWidget,
                    RendererMixin, ShaderMixin, MiniBrowserMixin):
    id = "shaderPresets"
    info = "Shader image thumbnail browser with presets"
    uiData = {"label": "Shader Presets (Multi-Renderer)",
              "icon": "shaderPresets",
              "tooltip": "Shader image thumbnail browser with presets",
              "helpUrl": "https://create3dcharacters.com/maya-tool-shader-presets/",
              "defaultActionDoubleClick": False}

    # ------------------
    # STARTUP
    # ------------------

    def preContentSetup(self):
        """First code to run, treat this as the __init__() method"""
        self.toolsetWidget = self  # needed for callback decorators and resizer
        self.generalPrefs = coreinterfaces.generalInterface()
        self.initRendererMixin()
        self.shaderPrefs = shaderinterfaces.shaderInterface()
        self.setAssetPreferences(self.shaderPrefs.shaderPresetsAssets)
        # self.setPrefVariables()  # sets self.directory and self.uniformIcons
        self.copiedAttributes = dict()  # for copy paste shaders
        self.copiedShaderName = ""  # for copy paste shaders
        self._sliderShader = None  # for virtual sliders

    def contents(self):
        """The UI Modes to build, compact, medium and or advanced """
        return [self.initCompactWidget()]  # , self.initAdvancedWidget()

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
        self.uiConnections()
        self.updateShaderTypeList()

    def defaultAction(self):
        """Double Click
        Double clicking the tools toolset icon will run this method
        Be sure "defaultActionDoubleClick": True is set inside self.uiData (meta data of this class)"""
        pass

    def currentWidget(self):
        """Returns the current widget class eg. self.compactWidget or self.advancedWidget

        Over ridden class
        :rtype:  GuiWidgets
        """
        return super(ShaderPresets, self).currentWidget()

    def widgets(self):
        """ List of widgets

        :return:
        :rtype: list[GuiWidgets]
        """
        return super(ShaderPresets, self).widgets()

    # ------------------
    # PROPERTIES
    # ------------------

    def initializeProperties(self):
        """Needed for setting self.properties.rendererIconMenu.value on startup before UI is built

        self.properties.rendererIconMenu.value is set with:

            self.initRendererMixin(disableVray=False, disableMaya=False)
        """
        return [{"name": "rendererIconMenu", "label": "", "value": "Arnold"}]  # will be changed to prefs immediately

    def updateFromProperties(self):
        """ Runs update properties from the base class.

        Widgets will auto update from self.properties if linked via:

            self.linkProperty(widget, "propertyKey")
            or
            self.toolsetWidget.linkProperty(widget, "propertyKey")

        Add code after super() useful for changes such as forcing UI decimal places
        or manually adding unsupported widgets
        """
        super(ShaderPresets, self).updateFromProperties()
        # self.guiName = self.buildShaderName()  # this is used for renaming while nothing is selected

    # ------------------
    # RENAME DELETE SAVE
    # ------------------

    def renameAsset(self):
        """Renames the asset on disk"""
        currentFileNoSuffix = self.currentWidget().browserModel.currentImage
        self.zooScenePath = self.currentWidget().miniBrowser.selectedMetadata()['zooFilePath']
        if not currentFileNoSuffix:  # no image has been selected
            output.displayWarning("Please select a shader preset image to rename.")
            return
        # Get the current directory
        message = "Rename Related `{}` Files As:".format(currentFileNoSuffix)
        renameText = elements.MessageBox.inputDialog(title="Rename Shader Preset", text=currentFileNoSuffix,
                                                     parent=None,
                                                     message=message)
        if not renameText:
            return
        # Do the rename
        fileRenameList = zooscenefiles.renameZooSceneOnDisk(renameText, self.zooScenePath)
        if not fileRenameList:  # shouldn't happen for shaders
            output.displayWarning("Files could not be renamed, they are probably in use by the current scene. "
                                  "Do not have the renamed assets loaded in the scene, "
                                  "or check your file permissions.")
            return
        output.displayInfo("Success: Files `{}*` Have Been Renamed To `{}*`".format(currentFileNoSuffix, renameText))
        self.refreshThumbs()

    def deletePresetPopup(self):
        """Popup window that asks the user if they want to delete the currently selected asset from disk?"""
        filename = self.currentWidget().browserModel.currentImage
        item = self.currentWidget().browserModel.currentItem
        filenameWithSuffix = ".".join([filename, zooscenefiles.ZOOSCENESUFFIX])
        if not filenameWithSuffix:
            output.displayWarning("Nothing selected. Please select a shader preset to delete.")
        path = item.fullPath()
        # Build popup window
        message = "Warning: Delete the preset `{}` and it's dependencies?  " \
                  "This will permanently delete these file/s from disk?".format(filenameWithSuffix)
        result = elements.MessageBox.showOK(title="Delete Shader Preset From Disk?",
                                            message=message)  # None will parent to Maya
        # After answering Ok or cancel
        if result:  # Ok was pressed
            filesFullPathDeleted = zooscenefiles.deleteZooSceneFiles(path, message=True)
            self.refreshThumbs()
            output.displayInfo("Success, File/s Deleted: {}".format(filesFullPathDeleted))

    def savePreset(self):
        """Opens a window to save the shader to the library"""
        # Get the shader to save from scene ----------------------------------
        shaderInstances = shadermulti.shaderInstancesFromSelected(message=True)
        if not shaderInstances:
            return  # message given, please select
        shaderInstance = shaderInstances[0]
        shaderNameNoSuffix = shaderInstance.shaderNameNoSuffix()
        # Popup save window --------------------------------------------------
        message = "Save Shader to Preset Library?"
        shaderName = elements.MessageBox.inputDialog(title="Save Presets", text=shaderNameNoSuffix,
                                                     parent=None, message=message)
        if not shaderName:
            return  # Cancelled or empty string
        # Build paths and check file doesn't already exist ---------------------
        zooSceneFile = ".".join([shaderName, ZOOSCENE_EXT])
        self.directory = self.currentWidget().miniBrowser.getSaveDirectory()
        zooSceneFullPath = os.path.join(self.directory, zooSceneFile)
        if os.path.exists(zooSceneFullPath):  # File already exists, overwrite?
            message = "File  exists, overwrite?\n" \
                      "   {}".format(zooSceneFullPath)
            if not elements.MessageBox.showOK(title="File Already Exists", message=message):
                return
        # Save the file as all check out ----------------------------------------
        exportabcshaderlights.saveShaderInstanceZooScene(zooSceneFullPath, shaderName, shaderInstance)
        # Refresh GUI to add new thumbnail
        self.refreshThumbs()

    # ------------------------------------
    # CHANGE RENDERER
    # ------------------------------------

    def updateShaderTypeList(self):
        """Updates the shaderTypeCombo on startup or when the renderer is changed

        Sets the list self.shaderTypesList
        """
        self.shaderTypesList = shdmultconstants.RENDERER_SHADERS_DICT[self.properties.rendererIconMenu.value]
        for widget in self.widgets():
            widget.shaderTypeCombo.clear()
            widget.shaderTypeCombo.addItems(self.shaderTypesList)

    def changeRenderer(self):
        """Run when the renderer is changed"""
        self.updateShaderTypeList()

    # ------------------
    # LOGIC CREATE
    # ------------------

    def buildShaderName(self):
        return shdmult.buildNameWithSuffix("shader01",
                                           True,
                                           self.properties.rendererIconMenu.value)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def createShaderUndo(self):
        """Creates a shader with one undo"""
        self.createShader()

    def createShader(self):
        """Create Shader
        """
        renderer = self.properties.rendererIconMenu.value
        shaderType = self.shaderTypesList[self.properties.shaderTypeCombo.value]
        if not rendererload.getRendererIsLoaded(renderer):  # the renderer is not loaded open window
            if not elements.checkRenderLoaded(renderer):
                return
        # Create shader -------------------------------------
        shaderInstance = shadermulti.createAssignShdInstType(shaderType)
        # Set & assign the shader attributes
        self.setShaderZooScene([shaderInstance])
        shaderInstance.assignSelected()
        # Rename the new shader ---------------------------------
        shaderName = "_".join([shdmultconstants.DEFAULT_SHADER_NAME,
                               shdmultconstants.SHADERTYPE_SUFFIX_DICT[shaderType]])
        shaderInstance.setShaderName(shaderName)
        output.displayInfo("Shader created `{}`".format(shaderInstance.shaderName()))

    # ------------------
    # LOGIC TRANSFER SELECT
    # ------------------

    @toolsetwidget.ToolsetWidget.undoDecorator
    def transferAssign(self):
        """Assigns the shader from the first selected face or object to all other selected objects and faces"""
        success = shaderutils.transferAssignSelection()
        if not success:  # message already reported to user
            return
        shaderName = self.buildShaderName()
        output.displayInfo("Shader assigned `{}`".format(shaderName))

    @toolsetwidget.ToolsetWidget.undoDecorator
    def selectObjFacesFromShader(self):
        """Selects objects and faces assigned from a shader"""
        shaderList = shaderutils.getShadersSelected()
        if not shaderList:
            return
        shaderutils.selectMeshFaceFromShaderName(shaderList[0])

    @toolsetwidget.ToolsetWidget.undoDecorator
    def selectShader(self):
        """Selects the active shader from the GUI"""
        shaderList = shaderutils.getShadersSelected()
        if not shaderList:
            return
        cmds.selectMode(object=True)
        cmds.select(shaderList[0], replace=True)

    # ------------------
    # LOGIC TRANSFER COPY PASTE
    # ------------------

    def copyShader(self):
        """Copies the shader attributes and shader name"""
        self.shaderInstances = shadermulti.shaderInstancesFromSelected(message=False)
        if not self.shaderInstances:
            output.displayWarning("Please select a shader or geometry.")
            return
        self.shaderInstance = self.shaderInstances[0]
        if not self.shaderInstance.exists():
            output.displayWarning("The current shader is not found in scene or not supported")
            return
        self.copiedAttributes = self.shaderInstance.shaderValues(removeNone=False)
        self.copiedShaderName = self.shaderInstance.shaderName()
        self.global_sendCopyShader()
        output.displayInfo("Shader copied `{}`".format(self.copiedShaderName))

    @toolsetwidget.ToolsetWidget.undoDecorator
    def pasteAttributes(self):
        """sets the copied shader attributes to the selected/active shader, but does not assign, the shader remains"""
        self.shaderInstances = shadermulti.shaderInstancesFromSelected(message=False)
        if not self.shaderInstances:
            output.displayWarning("Please select a shader or geometry to paste the shader attributes.")
            return
        if not self.copiedAttributes:
            output.displayWarning("Cannot paste as there is nothing in the clipboard.  Please copy a shader.")
            return
        shaderNames = list()
        # Set the shaders with pasted attributes --------------
        for shaderInstance in self.shaderInstances:
            shaderInstance.setFromDict(self.copiedAttributes)
        # Message -------------------------------
        for shaderInstance in self.shaderInstances:
            shaderNames.append(shaderInstance.shaderName())
        output.displayInfo("Shader attributes pasted to `{}`".format(shaderNames))

    def pasteAssign(self):
        """Assigns the copied shader (from the shader name) to the selected object/s or faces"""
        if not self.copiedShaderName:
            output.displayWarning("Cannot paste as there is nothing in the clipboard.  Please copy a shader.")
            return
        if not cmds.objExists(self.copiedShaderName):
            output.displayWarning("Shader `` no longer exists in the scene and "
                                  "cannot be assigned".format(self.copiedShaderName))
            return
        output.displayInfo("Shader assigned `{}`".format(self.copiedShaderName))

    # ------------------
    # LOGIC SET
    # ------------------

    def setZooShaderInstance(self, shaderInstance):
        """Sets a single zoo shader instance with the current selections settings

        :param shaderInstances: a list of zoo shader instances
        :type shaderInstance: zoo.libs.maya.cmds.shaders.shadertypes.shaderbase.ShaderBase()
        """
        if not shaderInstance.exists() or not shaderInstance.knownShader() or not shaderInstance.renderer():
            output.displayWarning("The selected shader type is not supported")
            return
        if not rendererload.getRendererIsLoaded(shaderInstance.renderer()):  # the renderer is not loaded open window
            if not elements.checkRenderLoaded(shaderInstance.renderer()):
                return
        # Get the zooScene
        selItem = self.currentWidget().miniBrowser.currentItem()
        if not selItem:
            output.displayWarning("No image/item is selected in the browser, please select.")
            return
        # Set the shader attributes
        exportabcshaderlights.setShaderAttrsZscnInstance(shaderInstance, selItem.fullPath())  # zooScenePath

    def setShaderZooScene(self, shaderInstances):
        """Sets the shader attributes on multiple shader instances after creation or while changing settings

        :param shaderInstances: a list of zoo shader instances
        :type shaderInstances: list(zoo.libs.maya.cmds.shaders.shadertypes.shaderbase.ShaderBase())
        """
        shdrInstance = None
        for shdrInstance in shaderInstances:
            self.setZooShaderInstance(shdrInstance)
        if shdrInstance.exists():
            cmds.select(shdrInstance.shaderName(), replace=True)
        self.global_shaderUpdated()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def setShaderSelectedZooScene(self, name=""):
        """From the selected object or shader, return the first found shader and assign it to a .zooScene file

        :param message: report the message to the user?
        :type message: bool
        """
        shaderInstances = shadermulti.shaderInstancesFromSelected(message=True)
        if not shaderInstances:
            return  # message already reported
        self.setShaderZooScene(shaderInstances)
        self._sliderShader = shaderInstances[-1]  # for sliders

    # ------------------
    # Browser Sliders
    # ------------------

    def clamp(self, value):
        """Clamps 0-1.0"""
        if value > 1.0:
            value = 1.0
        elif value < 0.0:
            value = 0.0
        return value

    def browserSliderPressed(self):
        """ Browser slider pressed, get the shader information, and open the undo chunk if found
        """
        shaderInstances = shadermulti.shaderInstancesFromSelected(message=False)
        if not shaderInstances:
            if self._sliderShader:
                if self._sliderShader.exists():
                    shaderInstances = [self._sliderShader]
            else:
                output.displayWarning("Nothing selected. Please select object/s with shaders.")
                return  # message already reported
        self._sliderShader = shaderInstances[-1]

        self._sliderDiffuseColor = self._sliderShader.diffuse()
        self._sliderSpecRough = self._sliderShader.specRoughness()
        self._sliderSpecColor = self._sliderShader.specColor()
        self._sliderCoatWeight = self._sliderShader.coatWeight()
        self._sliderMetalness = self._sliderShader.metalness()

        self.openUndoChunk()

    def browserSliderChanged(self, event):
        """ Browser slider changed

        :param event: A tuple x and y offset of the virtual slider (21.0, 1.0021)
        :type event: :class:`zoo.libs.pyqt.extended.imageview.thumbnail.virtualslider.MouseSlideEvent`
        """
        if not self._sliderShader:
            output.inViewMessage("<hl>No Shader Selected</hl>: Please select a shader")
            return

        # Set Metalness --------------------
        if event.modifiers == QtCore.Qt.AltModifier | QtCore.Qt.ControlModifier | QtCore.Qt.ShiftModifier:
            if not self._sliderShader.metalnessAttr:  # attribute doesn't exist
                output.inViewMessage("<hl>Metalness</hl>: Does not exist on this shader")
                return
            if event.direction == elements.VirtualSlider.Horizontal:
                value = event.value[0]
            else:
                value = event.value[1] * 100  # vertical is set to be slow for offsets
            newVal = float(self._sliderMetalness + value * 0.005)
            newVal = self.clamp(newVal)
            self._sliderShader.setMetalness(newVal)
            output.inViewMessage("Applying <hl>Metalness</hl>: {}".format("{:.2f}".format(newVal)))
            return

        # Set Clear Coat Weight --------------------
        if event.modifiers == QtCore.Qt.AltModifier | QtCore.Qt.ControlModifier:
            if not self._sliderShader.coatWeightAttr:  # attribute doesn't exist
                output.inViewMessage("<hl>Coat Weight</hl>: Does not exist on this shader")
                return
            if event.direction == elements.VirtualSlider.Horizontal:
                value = event.value[0]
            else:
                value = event.value[1] * 100  # vertical is set to be slow for offsets
            newVal = float(self._sliderCoatWeight + value * 0.005)
            newVal = self.clamp(newVal)
            self._sliderShader.setCoatWeight(newVal)
            output.inViewMessage("Applying <hl>Clear Coat Weight</hl>: {}".format("{:.2f}".format(newVal)))
            return

        # Set Spec --------------------
        if event.modifiers == QtCore.Qt.ControlModifier:

            if event.direction == elements.VirtualSlider.Horizontal:  # Spec Roughness
                if not self._sliderShader.specularRoughnessAttr:  # attribute doesn't exist
                    output.inViewMessage("<hl>Specular Roughness</hl>: Does not exist on this shader")
                    return
                newVal = float(self._sliderSpecRough + event.value[0] * 0.005)
                newVal = self.clamp(newVal)
                self._sliderShader.setSpecRoughness(newVal)
                output.inViewMessage("Applying <hl>Specular Roughness</hl>: {}".format("{:.2f}".format(newVal)))
                return
            elif event.direction == elements.VirtualSlider.Vertical:  # Spec Intensity
                if not self._sliderShader.specularColorAttr:  # attribute doesn't exist
                    output.inViewMessage("<hl>Specular Color</hl>: Does not exist on this shader")
                    return
                hsv = color.offsetValue(color.convertRgbToHsv(self._sliderSpecColor), event.value[1])
                newCol = color.convertHsvToRgb(hsv)
                self._sliderShader.setSpecColor(newCol)
                output.inViewMessage("Applying <hl>Specular Brightness</hl>: {}".format("{:.2f}".format(hsv[2])))
                return

        # Set Color --------------------
        if self._sliderShader.specularColorAttr:  # attribute exists so decide which color to affect diffuse/spec
            spec = self._sliderShader.specIOR() > 4.0
            if spec:
                mainColor = self._sliderSpecColor
            else:
                mainColor = self._sliderDiffuseColor
        else:  # spec color does not exist, so for diffuse
            spec = False
            mainColor = self._sliderDiffuseColor

        # Do the colors -------------
        if event.modifiers == QtCore.Qt.ShiftModifier:  # Saturation shift
            hsv = color.offsetSaturation(color.convertRgbToHsv(mainColor), event.value[0] * 0.005)
            newColor = color.convertHsvToRgb(hsv)
            text = "<hl>Saturation</hl>: {}".format("{:.2f}".format(hsv[1]))
        elif event.direction == elements.VirtualSlider.Horizontal:  # Hue shift
            newColor = color.hueShift(mainColor, event.value[0])
            hsv = color.convertRgbToHsv(newColor)
            text = "<hl>Hue</hl>: {}".format("{:.2f}".format(hsv[0]))
        else:  # Value shift
            hsv = color.offsetValue(color.convertRgbToHsv(mainColor), event.value[1])
            newColor = color.convertHsvToRgb(hsv)
            text = "<hl>Brightness</hl>: {}".format("{:.2f}".format(hsv[2]))

        if newColor:
            if spec:
                self._sliderShader.setSpecColor(newColor)
                output.inViewMessage("Applying <hl>Specular Color</hl> {}".format(text))
            else:
                self._sliderShader.setDiffuse(newColor)
                output.inViewMessage("Applying <hl>Diffuse Color</hl> {}".format(text))

    def browserSliderReleased(self, event):
        """ Browser slider released.

        Close the undo chunk and do any saving if needed.

        :param event: A tuple x and y offset of the virtual slider (21.0, 1.0021)
        :type event: :class:`zoo.libs.pyqt.extended.imageview.thumbnail.virtualslider.MouseSlideEvent`
        :return:
        """
        self.global_shaderUpdated()  # update other UIs
        self.closeUndoChunk()

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        super(ShaderPresets, self).uiconnections()
        for w in self.widgets():
            # Thumbnail viewer
            w.browserModel.doubleClicked.connect(self.setShaderSelectedZooScene)
            # Dots menu
            w.miniBrowser.dotsMenu.applyAction.connect(self.setShaderSelectedZooScene)
            w.miniBrowser.dotsMenu.createAction.connect(self.savePreset)
            w.miniBrowser.dotsMenu.renameAction.connect(self.renameAsset)
            w.miniBrowser.dotsMenu.deleteAction.connect(self.deletePresetPopup)
            # Change Renderer
            w.rendererIconMenu.actionTriggered.connect(self.changeRenderer)
            w.rendererIconMenu.actionTriggered.connect(self.global_changeRenderer)  # updates other UIs
            w.shaderTypeCombo.itemChanged.connect(self.global_shaderTypeUpdated)  # updates other UIs
            # Create Change Shaders
            w.createBtn.clicked.connect(self.createShaderUndo)
            w.changeBtn.clicked.connect(self.setShaderSelectedZooScene)

            w.miniBrowser.sliderChanged.connect(self.browserSliderChanged)
            w.miniBrowser.sliderPressed.connect(self.browserSliderPressed)
            w.miniBrowser.sliderReleased.connect(self.browserSliderReleased)

            # Transfer
            w.transferShaderBtn.clicked.connect(self.transferAssign)
            # Select
            w.selectShaderBtn.clicked.connect(self.selectShader)
            w.selectObjectsBtn.clicked.connect(self.selectObjFacesFromShader)
            # Copy Paste
            w.copyShaderBtn.clicked.connect(self.copyShader)
            w.pasteShaderBtn.clicked.connect(self.pasteAssign)
            w.pasteAttrBtn.clicked.connect(self.pasteAttributes)
            # Save Btn
            w.saveBtn.clicked.connect(self.savePreset)


class GuiWidgets(QtWidgets.QWidget):
    def __init__(self, parent=None, properties=None, uiMode=None, toolsetWidget=None):
        """Builds the main widgets for all GUIs

        properties is the list(dictionaries) used to set logic and pass between the different UI layouts
        such as compact/adv etc

        :param parent: the parent of this widget
        :type parent: qtObject
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: object
        :param uiMode: 0 is compact ui mode, 1 is advanced ui mode
        :type uiMode: int
        """
        super(GuiWidgets, self).__init__(parent=parent)
        # Thumbnail Viewer --------------------------------------------
        # viewer widget and model
        shaderPrefs = shaderinterfaces.shaderInterface()
        uniformIcons = shaderPrefs.shaderPresetsAssets.browserUniformIcons()
        self.miniBrowser = elements.MiniBrowser(parent=self,
                                                toolsetWidget=toolsetWidget,
                                                columns=3,
                                                fixedHeight=382,
                                                uniformIcons=uniformIcons,
                                                itemName="Shader Preset",
                                                applyText="Apply To Selected",
                                                applyIcon="shaderBall",
                                                createText="Save",
                                                selectDirectoriesActive=True,
                                                virtualSlider=True)
        self.miniBrowser.setSliderSettings(slowSpeedXY=(1, 0.01), speedXY=(2, 0.02), fastSpeedXY=(5, 0.05))
        self.miniBrowser.dotsMenu.setDirectoryActive(
            False)  # todo: remove this since we use multi directory browsers now
        self.miniBrowser.dotsMenu.setSnapshotActive(True)

        directories = shaderPrefs.shaderPresetsAssets.browserFolderPaths()
        self.browserModel = zooscenemodel.ZooSceneModel(self.miniBrowser,
                                                        directories=directories,
                                                        uniformIcons=uniformIcons,
                                                        assetPreference=shaderPrefs.shaderPresetsAssets)
        self.miniBrowser.setModel(self.browserModel)
        self.resizerWidget = ToolsetResizer(toolsetWidget=toolsetWidget, target=self.miniBrowser)
        virtualSliderTooltip = "Tip: Browser Icon Virtual Sliders \n\n" \
                               " MMB (Middle Mouse Button Click) + Horizontal Drag - Shift Hue \n" \
                               " MMB Vertical Drag - Brightness Value \n" \
                               " MMB Shift Horizontal Drag - Saturation \n" \
                               " MMB Ctrl + Horizontal Drag - Specular Roughness \n" \
                               " MMB Ctrl + Vertical Drag - Specular Brightness \n" \
                               " MMB Alt + Ctrl + Drag - Clear Coat Weight \n" \
                               " MMB Shift + Alt + Ctrl + Drag - Metalness"

        # Shader Type Combo ---------------------------------------
        toolTip = "Select a shader type used while creating shaders only."
        self.shaderTypeCombo = elements.ComboBoxRegular(label="",
                                                        items=[],
                                                        parent=self,
                                                        toolTip=toolTip,
                                                        setIndex=0,
                                                        labelRatio=2,
                                                        boxRatio=5)  # is populated by the renderer
        # Change Assign Button ---------------------------------------
        tooltip = "Changes the selected objects/faces shader to the preset values. \n" \
                  "(Default double-click thumbnail) \n" \
                  "Select an object, face or shader.  The shader's type is not changed. \n" \
                  "To create a new shader use `Create`.  \n\n{}".format(virtualSliderTooltip)

        self.changeBtn = elements.styledButton("Change",
                                               icon="shaderPresets",
                                               toolTip=tooltip,
                                               style=uic.BTN_DEFAULT)
        # Create Button ---------------------------------------
        tooltip = "Creates a new shader on the selected objects/faces from the selected thumbnail. \n" \
                  "Will create the shader with the current shader type/renderer. \n" \
                  "If nothing is selected will create a shader only. \n\n{}".format(virtualSliderTooltip)
        self.createBtn = elements.styledButton("Create",
                                               icon="shaderBall",
                                               toolTip=tooltip,
                                               style=uic.BTN_DEFAULT)
        # Renderer Button --------------------------------------
        toolTip = "Change the renderer to Arnold, Redshift or Renderman"
        self.rendererIconMenu = elements.iconMenuButtonCombo(shdmultconstants.RENDERER_ICONS_LIST,
                                                             properties.rendererIconMenu.value,
                                                             toolTip=toolTip)
        # Copy Shader Btn --------------------------------------------
        toolTip = "Copy the current shader settings to the clipboard"
        self.copyShaderBtn = elements.styledButton("Copy", "copyShader",
                                                   toolTip=toolTip,
                                                   style=uic.BTN_DEFAULT)
        # Paste Assign Shader Btn --------------------------------------------
        toolTip = "Paste/Assign the shader from the clipboard \n" \
                  "Existing shader will be assigned to selected geometry"
        self.pasteShaderBtn = elements.styledButton("Paste", "pasteAssign",
                                                    toolTip=toolTip,
                                                    style=uic.BTN_DEFAULT)
        # Save Shader Btn --------------------------------------------
        toolTip = "Save the current shader to a new preset on disk. "
        self.saveBtn = elements.styledButton("", "save",
                                             toolTip=toolTip,
                                             style=uic.BTN_DEFAULT)
        # Paste Attribute Shader Btn --------------------------------------------
        toolTip = "Paste the shader attribute settings from the clipboard \n" \
                  "Shader attribute settings will be pasted, the existing shader will remain."
        self.pasteAttrBtn = elements.styledButton("", "pasteAttributes",
                                                  toolTip=toolTip,
                                                  style=uic.BTN_DEFAULT)
        # Transfer Shader Btn --------------------------------------------
        toolTip = "Transfer the current shader to another object \n" \
                  "- 1. Select two or more objects. \n" \
                  "- 2. The shader from the first object will be transferred to others."
        self.transferShaderBtn = elements.styledButton("Transfer", "transferShader",
                                                       toolTip=toolTip,
                                                       style=uic.BTN_DEFAULT)
        # Select Objects/Faces --------------------------------------------
        toolTip = "Select objects and or faces with this material. "
        self.selectObjectsBtn = elements.styledButton("",
                                                      "selectObject",
                                                      self,
                                                      toolTip=toolTip,
                                                      style=uic.BTN_DEFAULT)
        # Select Shader Btn --------------------------------------------
        toolTip = "Select shader node/s and deselect geometry. \n" \
                  "Useful for seeing objects while changing shaders. "
        self.selectShaderBtn = elements.styledButton("",
                                                     "selectShader",
                                                     self,
                                                     toolTip=toolTip,
                                                     style=uic.BTN_DEFAULT)


class GuiCompact(GuiWidgets):
    def __init__(self, parent=None, properties=None, uiMode=UI_MODE_COMPACT, toolsetWidget=None):
        """Adds the layout building the compact version of the GUI:

            default uiMode - 0 is advanced (UI_MODE_COMPACT)

        :param parent: the parent of this widget
        :type parent: qtObject
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: list[dict]
        """
        super(GuiCompact, self).__init__(parent=parent, properties=properties, uiMode=uiMode,
                                         toolsetWidget=toolsetWidget)
        # Main Layout ---------------------------------------
        mainLayout = elements.vBoxLayout(self, margins=(uic.WINSIDEPAD, uic.WINTOPPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SPACING)
        # create button Layout ---------------------------------------
        createBtnLayout = elements.hBoxLayout(spacing=uic.SPACING)
        createBtnLayout.addWidget(self.changeBtn, 10)
        createBtnLayout.addWidget(self.createBtn, 10)
        # shaderType Layout ---------------------------------------
        shaderTypeLayout = elements.hBoxLayout(spacing=uic.SPACING)
        shaderTypeLayout.addWidget(self.shaderTypeCombo, 10)
        shaderTypeLayout.addWidget(self.rendererIconMenu, 1)
        # Transfer Shaders Layout ---------------------------------------
        transferLayout = elements.hBoxLayout(spacing=uic.SPACING)
        transferLayout.addWidget(self.transferShaderBtn, 5)
        transferLayout.addWidget(self.copyShaderBtn, 5)
        # Paste Shaders Layout ---------------------------------------
        pasteLayout = elements.hBoxLayout(spacing=uic.SPACING)
        pasteLayout.addWidget(self.pasteShaderBtn, 5)
        pasteLayout.addWidget(self.pasteAttrBtn, 1)
        pasteLayout.addWidget(self.selectShaderBtn, 1)
        pasteLayout.addWidget(self.selectObjectsBtn, 1)
        pasteLayout.addWidget(self.saveBtn, 1)
        # Transfer/Paste Shaders Layout ---------------------------------------
        transferPasteLayout = elements.hBoxLayout(spacing=uic.SPACING)
        transferPasteLayout.addLayout(transferLayout, 8)
        transferPasteLayout.addLayout(pasteLayout, 10)
        # Button Layout ---------------------------------------
        botBtnLayout = elements.hBoxLayout(spacing=uic.SPACING)
        botBtnLayout.addLayout(createBtnLayout, 8)
        botBtnLayout.addLayout(shaderTypeLayout, 10)
        # Add To Main Layout ---------------------------------------
        mainLayout.addWidget(self.miniBrowser)
        mainLayout.addWidget(self.resizerWidget)
        mainLayout.addLayout(shaderTypeLayout)
        mainLayout.addLayout(transferPasteLayout)
        mainLayout.addLayout(botBtnLayout)


class GuiAdvanced(GuiWidgets):
    def __init__(self, parent=None, properties=None, uiMode=UI_MODE_ADVANCED, toolsetWidget=None):
        """Adds the layout building the advanced version of the GUI:

            default uiMode - 1 is advanced (UI_MODE_ADVANCED)

        :param parent: the parent of this widget
        :type parent: qtObject
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: list[dict]
        """
        super(GuiAdvanced, self).__init__(parent=parent, properties=properties, uiMode=uiMode,
                                          toolsetWidget=toolsetWidget)
        # Main Layout ---------------------------------------
        elements.vBoxLayout(self, margins=(uic.WINSIDEPAD, uic.WINTOPPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                            spacing=uic.SPACING)
