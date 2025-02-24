import locale
import functools
import os
from zoo.apps.shader_tools.shadermixin import ShaderMixin

from zoovendor.Qt import QtWidgets
from zoo.apps.toolsetsui.ext.renderers import RendererMixin
from zoo.libs.utils import filesystem

from maya import cmds
from zoo.libs.maya import zapi
from zoo.libs.maya.cmds.shaders import shaderutils, shadermultirenderer as shdmult
from zoo.libs.maya.cmds.shaders import shadermulti, shdmultconstants as shdCnst
from zoo.libs.maya.cmds.renderer import rendererload

from zoo.libs.maya.cmds.shaders.shdmultconstants import RENDERER_SHADERS_DICT, RENDERER_ICONS_LIST, \
    DIFFUSE_DEFAULT, DIFFUSE_WEIGHT_DEFAULT, DIFFUSE_ROUGHNESS_DEFAULT, METALNESS_DEFAULT, SPECULAR_DEFAULT, \
    SPECULAR_WEIGHT_DEFAULT, ROUGHNESS_DEFAULT, IOR_DEFAULT, COAT_COLOR_DEFAULT, COAT_ROUGH_DEFAULT, \
    COAT_WEIGHT_DEFAULT, COAT_IOR_DEFAULT, EMISSION_DEFAULT, EMISSION_WEIGHT_DEFAULT

from zoo.apps.toolsetsui.widgets import toolsetwidget

from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements
from zoo.libs.utils import output

from zoo.preferences.interfaces import coreinterfaces
from zoo.apps.toolsetsui import toolsetui, toolsetcallbacks

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1

SHADER_TYPES = ["Standard IOR"]

DEFAULT_SHADER_NAME = "shader_01"


class ShaderManager(toolsetwidget.ToolsetWidget, RendererMixin, ShaderMixin):
    """Large tool for managing and assigning shaders
    """
    id = "shaderManager"
    uiData = {"label": "Shader Manager (Multi-Renderer)",
              "icon": "settingSliders",
              "tooltip": "Shader Manager for creating and managing the main shaders in Arnold Redshift and Renderman",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-shader-manager/"
              }

    # ------------------
    # STARTUP
    # ------------------

    def preContentSetup(self):
        """First code to run"""
        self.toolsetWidget = self  # needed for callback decorators
        self.generalPrefs = coreinterfaces.generalInterface()
        self.initRendererMixin()
        self.undoStateOpen = False
        self.copiedAttributes = dict()
        self.copiedShaderName = ""
        self.buildPresets()  # builds the preset dictionary self.presetDict
        self.uiShaderName = ""

    def contents(self):
        """The UI Modes to build, compact, medium and or advanced """
        return [self.initCompactWidget(), self.initAdvancedWidget()]

    def initCompactWidget(self):
        """Builds the Compact GUI (self.compactWidget) """
        self.compactWidget = GuiCompact(parent=self, properties=self.properties, toolsetWidget=self,
                                        presetShaderList=self.presetShaderList)
        return self.compactWidget

    def initAdvancedWidget(self):
        """Builds the Advanced GUI (self.advancedWidget) """

        self.advancedWidget = GuiAdvanced(parent=self, properties=self.properties, toolsetWidget=self,
                                          presetShaderList=self.presetShaderList)
        return self.advancedWidget

    def postContentSetup(self):
        """Last of the initialization code"""
        self.uiConnections()
        self.shaderInstance = shadermulti.emptyInstance()
        self.oldShaderName = ""
        self.updateSelection()  # sets self.shaderInstance, self.shaderInstances and self.oldShaderName
        self.properties.shaderNameComboE.value = 0  # sets the shaderNameComboE to be the first name found
        self.updateShaderTypeList()  # updates the shader types from the given renderer incl self.shaderTypesList
        self.disableEnableSliders()
        self.updateNameComboE(updateCombo=True)
        self.setGuiShaderInstance()
        self.startSelectionCallback()  # start selection callback

    def currentWidget(self):
        """Returns the current widget class eg. self.compactWidget or self.advancedWidget

        Overridden class

        :return:
        :rtype: GuiWidgets
        """
        return super(ShaderManager, self).currentWidget()

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiAdvanced or GuiCompact]
        """
        return super(ShaderManager, self).widgets()

    # ------------------
    # PROPERTIES
    # ------------------

    def initializeProperties(self):
        return [{"name": "rendererIconMenu", "label": "", "value": "Arnold"}]

    # ------------------
    # SHADER PRESETS CLICKS
    # ------------------

    def buildPresets(self):
        """Shader presets as combo
        """

        path = os.path.abspath(__file__)
        dir_path = os.path.dirname(path)
        jsonPath = os.path.join(dir_path, "shaderPresets.json")
        self.presetDict = filesystem.loadJson(jsonPath)
        self.presetShaderList = list()
        for key in self.presetDict:
            self.presetShaderList.append(str(key))
        self.presetShaderList.sort(key=str.lower)  # alphabetical
        self.presetShaderList.insert(0, "Presets...")

    # ------------------
    # CALLBACKS
    # ------------------

    def selectionChanged(self, selection):
        """Run when the callback selection changes, updates the GUI if an object is selected

        Callbacks are handled automatically by toolsetcallbacks.py which this class inherits"""
        if not selection:  # then still may be a component face selection TODO add this to internal callbacks maybe?
            selection = cmds.ls(selection=True)
            if not selection:  # then nothing is selected
                return
        self.shaderToGuiSel()

    # ------------------
    # UPDATE COMBO
    # ------------------

    def updateSelection(self):
        """Update the current selection updates:

            self.shaderInstances (all selected instances)
            self.shaderInstance (first selected instance)
            self.oldShaderName (the old shader name)

        """
        self.shaderInstances = shadermulti.shaderInstancesFromSelected(message=False)
        if not self.shaderInstances:
            if self.shaderInstance.exists():  # then don't change as still int he UI
                return
            else:  # the current shader instance does not exist so add an empty shader instance
                self.shaderInstance = shadermulti.emptyInstance()
                self.oldShaderName = ""
        else:  # the shader instance is the first selected
            self.shaderInstance = self.shaderInstances[0]
            self.oldShaderName = self.shaderInstance.shaderName()

    # ------------------
    # UPDATE COMBO
    # ------------------

    def enterEvent(self, event):
        """When the cursor enters the UI update it"""
        # note known issue entering Event can cause a double shaderGUI combo update, difficult to solve so leaving.
        self.updateNameComboE(updateCombo=True)  # auto update lists
        self.updateSelection()
        self.shaderToGui()

    def updateInstancesFromName(self, shaderName):
        """Updates self.shaderInstance from the shader name"""
        self.shaderInstance = shadermulti.shaderInstanceFromShader(shaderName)
        if not self.shaderInstance:
            return
        return self.shaderInstance

    def shaderComboEChanged(self, event):
        """ On camera combo changed

        # Note will cause a double gui and combo update in most cases (short lists) because of enterEvent

        :type event: zoo.libs.pyqt.extended.combobox.comboeditwidget.IndexChangedEvent
        """
        # Update the GUI and self.uiShaderName to the new shader --------------------------
        newShaderName = event.items[0].text()  # The new text after changing
        self.updateInstancesFromName(newShaderName)
        if not self.shaderInstance.exists():
            output.displayWarning("Shader not found in scene `{}`".format(newShaderName))
            return
        self.shaderToGui(updateCombo=False)  # Don't update combo potential crash loops
        # Do Primary or Secondary Function ------------------------------------------------
        if event.menuButton == event.Primary:  # Primary then assign the geo
            self.assignShaderToGeo()
        elif event.menuButton == event.Secondary:  # Secondary select the shader
            self.selectShader()

    def alphabetizeLists(self, values):
        locale.setlocale(locale.LC_ALL, '')  # needed for sorting unicode
        if values:
            values = sorted(values, key=functools.cmp_to_key(locale.strcoll))  # alphabetalize
        return values

    def updateNameComboE(self, updateCombo=True, setName=None):
        """Updates to rename combo edit with option to set the current combo edit index with the setname (str)

        :param updateCombo: Will update to rename combo edit if it needs updating
        :type updateCombo: bool
        :param setName: Set this name as the current index in the combo edit, None uses self.currentShader()
        :type setName: str
        """
        shadersCombinedList = list()
        nodeCombinedList = list()

        # Builds allShaders and shadersSelected lists ----------------------------------------------
        shadersAll = self.alphabetizeLists(shaderutils.getAllShaders())
        shadersSelected = list()

        # shader instances are set on change of selection
        for shaderInstance in self.shaderInstances:
            if shaderInstance.exists():
                shadersSelected.append(shaderInstance.shaderName())
        shadersSelected = self.alphabetizeLists(shadersSelected)

        # Build shadersCombinedList which is used by the rename combo edit -------------------------
        if shadersSelected:  # top section of the list with current shaders
            shadersCombinedList += shadersSelected + [elements.ComboEditWidget.SeparatorString]
            nodeCombinedList += list(zapi.nodesByNames([i for i in shadersSelected if i])) + [None]
        if shadersAll:  # bottom section with all shaders
            shadersCombinedList += shadersAll
            nodeCombinedList += list(zapi.nodesByNames([i for i in shadersAll if i]))
        else:
            shadersCombinedList = ["No {} Shaders Found".format(self.properties.rendererIconMenu.value)]
            nodeCombinedList = [None]

        # Updates the Rename Combo Edit -----------------------------------------------------------
        if updateCombo:
            combo = self.currentWidget().shaderNameComboE
            if setName is None:
                setName = self.shaderInstance.shaderName()
            combo.updateList(shadersCombinedList, dataList=nodeCombinedList, setName=setName)
            combo.setText(setName)
            self.uiShaderName = combo.currentText()
            index = combo.currentIndexInt()
            self.properties.shaderNameComboE.value = index  # must update the combo to int value
            self.saveProperties()

    @toolsetcallbacks.ignoreCallbackDecorator
    def renameShaderEvent(self, event):
        """ Rename Shader event

        :param event:
        :type event: zoo.libs.pyqt.extended.combobox.comboeditwidget.EditChangedEvent
        """
        oldShaderName = event.before
        if event.before == event.after:  # TODO Seems to trigger twice weird can't figure
            return
        if self.currentShader() == event.after:  # TODO Seems to trigger twice catch if trying to rename itself.
            return

        if event.after == "":
            output.displayWarning("Cannot rename with no text")
            return
        if not self.shaderInstance.exists():
            output.displayWarning("Shader does not exist or is not supported")
            return
        if event.before is None:
            oldShaderName = self.currentShader()
        newName = self.shaderInstance.setShaderName(event.after, addSuffix=False)  # don't force suffix names
        self.updateNameComboE(updateCombo=True, setName=newName)  # updates all the lists new name
        output.displayInfo("Success: Shader `{}` renamed to `{}`".format(oldShaderName, newName))

    # ------------------------------------
    # CHANGE RENDERER
    # ------------------------------------

    def updateShaderTypeList(self):
        """Updates the shaderTypeCombo on startup or when the renderer is changed

        Sets the list self.shaderTypesList
        """
        self.shaderTypesList = RENDERER_SHADERS_DICT[self.properties.rendererIconMenu.value]
        for widget in self.widgets():
            widget.shaderTypeCombo.clear()
            widget.shaderTypeCombo.addItems(self.shaderTypesList)

    def changeRenderer(self):
        """Run when the renderer is changed"""
        self.updateShaderTypeList()

    # ------------------------------------
    # RENDERER - AND SEND/RECEIVE ALL TOOLSETS
    # ------------------------------------

    def global_receiveShaderUpdated(self):
        """Receives from other GUIs, changes the renderer when it is changed"""
        self.shaderToGuiSel()

    def global_sendDiffuseColor(self):
        """Updates all GUIs with diffuse shader color"""
        toolsets = toolsetui.toolsetsByAttr(attr="global_receiveDiffuseColor")
        for tool in toolsets:
            tool.global_receiveDiffuseColor(self.properties.diffuseColorSldr.value)

    def global_receiveDiffuseColor(self, diffuseColorDisplay):
        """Receives the diffuse shader color from other GUIs"""
        self.properties.diffuseColorSldr.value = diffuseColorDisplay
        self.updateFromProperties()

    # ------------------------------------
    # COPY PASTE - AND SEND/RECEIVE ALL TOOLSETS
    # ------------------------------------

    def global_sendCopyShader(self):
        """Updates all GUIs with the copied shader"""
        toolsets = toolsetui.toolsetsByAttr(attr="global_receiveCopiedShader")
        for tool in toolsets:
            tool.global_receiveCopiedShader(self.copiedShaderName, self.copiedAttributes)

    def global_receiveCopiedShader(self, copiedShaderName, copiedAttributes):
        """Receives the copied shader from other GUIs"""
        self.copiedShaderName = copiedShaderName
        self.copiedAttributes = copiedAttributes

    # ------------------------------------
    # SLIDER UNDO CHUNKS
    # ------------------------------------

    def openUndoChunk(self):
        """Opens the Maya undo chunk, on sliderPressed"""
        super(ShaderManager, self).openUndoChunk()
        self.undoStateOpen = True

    def closeUndoChunk(self):
        """Opens the Maya undo chunk, on sliderReleased"""
        super(ShaderManager, self).closeUndoChunk()
        self.undoStateOpen = False

    # ------------------
    # LOGIC PULL
    # ------------------

    def currentShader(self):
        """Returns the current shader with a few checks, such as falling back on zapi"""
        if not self.shaderInstance.exists():
            return ""  # Shader was probably deleted or never loaded
        return self.shaderInstance.shaderName()

    def disableEnableAttr(self, genKey, enable=True):
        """Disables or enables a widget based off it's key dict for both UIs advanced and compact.

        Some widgets are only in advanced mode.

        :param genKey: a generic key from shdCnst.ATTR_KEY_LIST
        :type genKey: str
        :param enable: Enable the widget True or disable with False
        :type enable: bool
        """
        if genKey == shdCnst.DIFFUSEWEIGHT:
            for w in self.widgets():
                w.diffuseWeightFloatSldr.setEnabled(enable)
        elif genKey == shdCnst.DIFFUSE:
            for w in self.widgets():
                w.diffuseColorSldr.setEnabled(enable)
        elif genKey == shdCnst.DIFFUSEROUGHNESS:
            for w in self.widgets():
                w.diffuseRoughFloatSldr.setEnabled(enable)
        elif genKey == shdCnst.SPECWEIGHT:
            for w in self.widgets():
                w.specularWeightFloatSldr.setEnabled(enable)
        elif genKey == shdCnst.SPECCOLOR:
            for w in self.widgets():
                w.specularColorSldr.setEnabled(enable)
        elif genKey == shdCnst.SPECROUGHNESS:
            for w in self.widgets():
                w.specularRoughFloatSldr.setEnabled(enable)
        elif genKey == shdCnst.SPECIOR:
            for w in self.widgets():
                w.iorFloatSldr.setEnabled(enable)
        elif genKey == shdCnst.METALNESS:
            for w in self.widgets():
                w.metalnessFloatSldr.setEnabled(enable)
        elif genKey == shdCnst.COATWEIGHT:
            for w in self.widgets():
                w.clearCoatWeightFloatSldr.setEnabled(enable)
        elif genKey == shdCnst.COATCOLOR:
            for w in self.widgets():
                w.clearCoatColorSldr.setEnabled(enable)
        elif genKey == shdCnst.COATROUGHNESS:
            for w in self.widgets():
                w.clearCoatRoughFoatSldr.setEnabled(enable)
        elif genKey == shdCnst.COATIOR:
            for w in self.widgets():
                w.clearCoatIorFloatSldr.setEnabled(enable)
        elif genKey == shdCnst.EMISSIONWEIGHT:
            for w in self.widgets():
                w.emissionWeightFloatSldr.setEnabled(enable)
        elif genKey == shdCnst.EMISSION:
            for w in self.widgets():
                w.emissionColorSldr.setEnabled(enable)

    def disableEnableSliders(self):
        """Enables or disables the ui sliders depending on the shader type
        """
        if not self.shaderInstance.exists():
            return
        disableAttrs = list(self.shaderInstance.connectedAttrs().keys())
        disableAttrs += self.shaderInstance.unsupportedAttributes()
        for genKey in shdCnst.ATTR_KEY_LIST:  # All generic keys
            if genKey in disableAttrs:
                self.disableEnableAttr(genKey, enable=False)
            else:
                self.disableEnableAttr(genKey, enable=True)

    def setGuiShaderDict(self, shaderAttributes):
        if shaderAttributes[shdmult.DIFFUSE] is not None:
            self.properties.diffuseColorSldr.value = shaderAttributes[shdmult.DIFFUSE]
        if shaderAttributes[shdmult.DIFFUSEWEIGHT] is not None:
            self.properties.diffuseWeightFloatSldr.value = round(shaderAttributes[shdmult.DIFFUSEWEIGHT], 3)
        if shaderAttributes[shdmult.SPECWEIGHT] is not None:
            self.properties.specularWeightFloatSldr.value = round(shaderAttributes[shdmult.SPECWEIGHT], 3)
        if shaderAttributes[shdmult.SPECCOLOR] is not None:
            self.properties.specularColorSldr.value = shaderAttributes[shdmult.SPECCOLOR]
        if shaderAttributes[shdmult.SPECROUGHNESS] is not None:
            self.properties.specularRoughFloatSldr.value = round(shaderAttributes[shdmult.SPECROUGHNESS], 3)
        if shaderAttributes[shdmult.SPECIOR] is not None:
            self.properties.iorFloatSldr.value = round(shaderAttributes[shdmult.SPECIOR], 3)
        if shaderAttributes[shdmult.COATWEIGHT] is not None:
            self.properties.clearCoatWeightFloatSldr.value = round(shaderAttributes[shdmult.COATWEIGHT], 3)
        if shaderAttributes[shdmult.COATCOLOR] is not None:
            self.properties.clearCoatColorSldr.value = shaderAttributes[shdmult.COATCOLOR]
        if shaderAttributes[shdmult.COATROUGHNESS] is not None:
            self.properties.clearCoatRoughFoatSldr.value = round(shaderAttributes[shdmult.COATROUGHNESS], 3)
        if shaderAttributes[shdmult.COATIOR] is not None:
            self.properties.clearCoatIorFloatSldr.value = round(shaderAttributes[shdmult.COATIOR], 3)
        self.updateFromProperties()

    def setGuiShaderInstance(self):
        """From the self.shaderInstance, pull all values into the UI
        """
        if not self.shaderInstance.exists():
            return  # Bail if shader does not exist

        diffuseWeight = self.shaderInstance.diffuseWeight()
        if diffuseWeight is not None:
            self.properties.diffuseWeightFloatSldr.value = round(diffuseWeight, 3)

        diffuseColor = self.shaderInstance.diffuseDisplay()
        if diffuseColor is not None:
            self.properties.diffuseColorSldr.value = diffuseColor

        diffuseRoughness = self.shaderInstance.diffuseRoughness()
        if diffuseRoughness is not None:
            self.properties.diffuseRoughFloatSldr.value = diffuseRoughness

        specularWeight = self.shaderInstance.specWeight()
        if specularWeight is not None:
            self.properties.specularWeightFloatSldr.value = round(specularWeight, 3)

        specularColor = self.shaderInstance.specColorDisplay()
        if specularColor is not None:
            self.properties.specularColorSldr.value = specularColor

        specularRough = self.shaderInstance.specRoughness()
        if specularRough is not None:
            self.properties.specularRoughFloatSldr.value = round(specularRough, 3)

        specIor = self.shaderInstance.specIOR()
        if specIor is not None:
            self.properties.iorFloatSldr.value = round(specIor, 3)

        metalness = self.shaderInstance.metalness()
        if metalness is not None:
            self.properties.metalnessFloatSldr.value = round(metalness, 3)

        clearCoatWeight = self.shaderInstance.coatWeight()
        if clearCoatWeight is not None:
            self.properties.clearCoatWeightFloatSldr.value = round(clearCoatWeight, 3)

        clearCoatColor = self.shaderInstance.coatColorDisplay()
        if clearCoatColor is not None:
            self.properties.clearCoatColorSldr.value = clearCoatColor

        clearCoatRoughness = self.shaderInstance.coatRoughness()
        if clearCoatRoughness is not None:
            self.properties.clearCoatRoughFoatSldr.value = round(clearCoatRoughness, 3)

        clearCoatIOR = self.shaderInstance.coatIOR()
        if clearCoatIOR is not None:
            self.properties.clearCoatIorFloatSldr.value = round(clearCoatIOR, 3)

        emissionWeight = self.shaderInstance.emissionWeight()
        if emissionWeight is not None:
            self.properties.emissionWeightFloatSldr.value = round(emissionWeight, 3)

        emissionColor = self.shaderInstance.emissionDisplay()
        if emissionColor is not None:
            self.properties.emissionColorSldr.value = emissionColor
        self.updateFromProperties()
        self.updateTypeNameLabel()

    def shaderToGui(self, updateCombo=True, message=False):
        """From a shader name pull it into the GUI

        :param message: report the message to the user?
        :type message: bool
        """
        if not self.shaderInstance.exists():
            return
        # Update GUI ----------------------------------------------------
        self.setGuiShaderInstance()  # Sets and updates properties from the self.shaderInstance
        if updateCombo:
            self.updateNameComboE(updateCombo=updateCombo, setName=self.shaderInstance.shaderName())
        # Disable Sliders on Textured slots ----------------------------
        self.disableEnableSliders()
        if message:
            output.displayInfo("Success: Shader UI Updated {}".format(self.currentWidget()))

    def shaderToGuiSel(self, message=False):
        """From a shader name pull it into the GUI, includes update selection
        """
        self.updateSelection()  # updates self.shaderInstance
        if not self.shaderInstance.exists():
            return
        self.shaderToGui(updateCombo=True, message=message)  # update UI

    def updateTypeNameLabel(self):
        """Updates the label of the Name combo box to be the shader type"""
        if not self.shaderInstance.exists():  # Then use default shader type
            shaderType = self.shaderTypesList[self.properties.shaderTypeCombo.value]
        else:
            shaderType = self.shaderInstance.shaderType()
        shaderType = shaderType[:1].capitalize() + shaderType[1:]  # First letter capital keep camel case
        for widget in self.widgets():
            widget.shaderNameComboE.setLabel(shaderType)  # Change label name

    # ------------------
    # LOGIC CREATE & DELETE
    # ------------------

    @toolsetwidget.ToolsetWidget.undoDecorator
    def createShaderUndo(self):
        """Creates a shader with one undo"""
        self.createShader()

    @toolsetcallbacks.ignoreCallbackDecorator
    def createShader(self):
        """Create Shader
        """
        currRenderer = self.properties.rendererIconMenu.value
        shaderType = self.shaderTypesList[self.properties.shaderTypeCombo.value]
        if not rendererload.getRendererIsLoaded(currRenderer):  # the renderer is not loaded open window
            if not elements.checkRenderLoaded(self.properties.rendererIconMenu.value):
                return
        # Build unique name -------------------------------------------------------
        suffix = shdCnst.SHADERTYPE_SUFFIX_DICT[shaderType]
        name = "_".join([DEFAULT_SHADER_NAME, suffix])
        # Create Set Shader -------------------------------------------------------
        self.shaderInstance = shadermulti.createAssignShdInstType(shaderType)
        self.shaderInstance.setShaderName(name)  # ensures is unique with suffixing
        self.shaderInstances = [self.shaderInstance]
        # Set the shader attributes from the GUI to the new shader ----------------
        self.setShader()
        # UI ----------------------------------------------------------------------
        self.shaderToGui()  # update the GUI (updates properties)
        self.updateNameComboE(updateCombo=True, setName=self.shaderInstance.shaderName())  # recreates all lists combo
        self.disableEnableSliders()  # disable enable sliders based on textures and unused attrs

    @toolsetwidget.ToolsetWidget.undoDecorator
    def deleteShader(self):
        """Deletes the shader in the UI from the scene"""
        if not self.shaderInstance.exists():
            return
        if not self.properties.affectMultiCheckbox.value:  # Single Shader
            self.shaderInstance.deleteShader()
        else:  # Multiple shaders
            for shadInst in self.shaderInstances:
                shadInst.deleteShader()
        self.updateNameComboE()
        self.shaderToGui()

    # ------------------
    # PRESETS AND RESET
    # ------------------

    @toolsetwidget.ToolsetWidget.undoDecorator
    def presetChanged(self, event=None):
        """ Change all attributes on the GUI and shader when the preset combo box is changed

        :param event: Event with all the values related to the change.
        :type event: zoo.libs.pyqt.extended.combobox.ComboItemChangedEvent
        """
        shaderName = self.presetShaderList[self.properties.shaderPresetsCombo.value]
        if shaderName == self.presetShaderList[0]:  # Ignore is the first entry "Presets..."
            return
        shaderAttributes = self.presetDict[shaderName]
        # Update GUI
        self.setGuiShaderDict(shaderAttributes)  # Sets and updates properties
        self.setShader()

    def resetToPreset(self):
        """Reset the current shader attributes to the current preset
        If no preset is selected use the 'bright grey 1 matte' setting"""
        shaderName = self.presetShaderList[self.properties.shaderPresetsCombo.value]
        if self.shaderInstance.exists():
            self.shaderInstance.setDefaults(apply=True)  # Helps if missing keys in the self.presetDict()
            self.shaderInstance.applyCurrentSettings()
        if shaderName == self.presetShaderList[0]:  # is "Presets..." so use matte
            shaderAttributes = self.presetDict[self.presetShaderList[1]]
        else:
            shaderAttributes = self.presetDict[shaderName]
        # Update GUI

        self.setGuiShaderDict(shaderAttributes)  # Sets and updates properties
        self.setShader()

    # ------------------
    # LOGIC SELECT
    # ------------------

    @toolsetwidget.ToolsetWidget.undoDecorator
    @toolsetcallbacks.ignoreCallbackDecorator
    def selectObjFacesFromShader(self):
        """Selects objects and faces assigned from a shader"""
        if not self.shaderInstance.exists():
            return
        if not self.properties.affectMultiCheckbox.value:  # Single Shader
            shaderutils.selectMeshFaceFromShaderName(self.shaderInstance.shaderName())
        else:  # Multiple shaders
            names = list()
            for shadInst in self.shaderInstances:
                names.append(shadInst.shaderName())
            shaderutils.selectMeshFaceFromShaderNames(names)

    @toolsetcallbacks.ignoreCallbackDecorator
    def selectShader(self):
        """Selects the active shader from the GUI"""
        if not self.shaderInstance.exists():
            return
        if not self.properties.affectMultiCheckbox.value:  # Single Shader
            cmds.select(self.shaderInstance.shaderName(), replace=True)
        else:  # Multiple shaders
            cmds.select(clear=True)
            for shadInst in self.shaderInstances:
                cmds.select(shadInst.shaderName(), add=True)

    @toolsetwidget.ToolsetWidget.undoDecorator
    @toolsetcallbacks.ignoreCallbackDecorator
    def assignShaderToGeo(self):
        """Assigns the current self.shaderInstance to the selected geometry
        """
        if not self.shaderInstance.exists():
            return
        self.shaderInstance.assignSelected(message=True)

    # ------------------
    # LOGIC TRANSFER COPY PASTE
    # ------------------

    def copyShader(self):
        """Copies the shader attributes and shader name"""
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
        if not self.copiedAttributes:
            output.displayWarning("Cannot paste as there is nothing in the clipboard.  Please copy a shader.")
            return
        shaderNames = list()
        # Pull latest selection info --------------
        self.updateSelection()  # updates self.shaderInstances and self.shaderInstance
        if not self.shaderInstances:
            output.displayWarning("No shaders selected to paste onto")
            return
        # Set the shaders with pasted attributes --------------
        for shaderInstance in self.shaderInstances:
            shaderInstance.setFromDict(self.copiedAttributes)
        # Update GUI -----------------------------
        self.setGuiShaderInstance()  # Sets and updates properties from self.shaderInstance
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
        if not self.updateInstancesFromName(self.copiedShaderName):
            return
        self.assignShaderToGeo()
        self.shaderToGui()  # updates the GUI
        output.displayInfo("Shader assigned `{}`".format(self.copiedShaderName))

    @toolsetwidget.ToolsetWidget.undoDecorator
    def transferAssign(self):
        """Assigns the shader from the first selected face or object to all other selected objects and faces"""
        success = shaderutils.transferAssignSelection(message=True)
        if not success:  # message already reported to user
            return

    # ------------------
    # LOGIC APPLY
    # ------------------

    def shaderDict(self):
        """Updates the UI to reflect the preset shader selection, colors from the UI are in SRGB
        """
        shaderDict = {shdCnst.DIFFUSEWEIGHT: self.properties.diffuseWeightFloatSldr.value,
                      shdCnst.DIFFUSE: self.properties.diffuseColorSldr.value,
                      shdCnst.DIFFUSEROUGHNESS: self.properties.diffuseRoughFloatSldr.value,
                      shdCnst.METALNESS: self.properties.metalnessFloatSldr.value,
                      shdCnst.SPECWEIGHT: self.properties.specularWeightFloatSldr.value,
                      shdCnst.SPECCOLOR: self.properties.specularColorSldr.value,
                      shdCnst.SPECROUGHNESS: self.properties.specularRoughFloatSldr.value,
                      shdCnst.SPECIOR: self.properties.iorFloatSldr.value,
                      shdCnst.COATWEIGHT: self.properties.clearCoatWeightFloatSldr.value,
                      shdCnst.COATCOLOR: self.properties.clearCoatColorSldr.value,
                      shdCnst.COATROUGHNESS: self.properties.clearCoatRoughFoatSldr.value,
                      shdCnst.COATIOR: self.properties.clearCoatIorFloatSldr.value,
                      shdCnst.EMISSIONWEIGHT: self.properties.emissionWeightFloatSldr.value,
                      shdCnst.EMISSION: self.properties.emissionColorSldr.value}
        return shaderDict

    @toolsetcallbacks.ignoreCallbackDecorator
    def setShader(self):
        """Sets the shader attributes after creation
        """
        if not self.shaderInstance.knownShader() or not self.shaderInstance.exists():
            return
        # Get the shader attributes and assign them to a dict ------------------
        shaderDict = self.shaderDict()
        # Set the shader attributes ----------------------
        self.shaderInstance.setFromDict(shaderDict, colorsAreSrgb=True)

    # ------------------
    # ATTRIBUTE CHANGES
    # ------------------

    def setDiffuseWeight(self):
        if not self.shaderInstance.knownShader() or not self.shaderInstance.exists():
            return
        if not self.properties.affectMultiCheckbox.value:  # Single Shader
            self.shaderInstance.setDiffuseWeight(self.properties.diffuseWeightFloatSldr.value)
        else:  # Multiple shaders
            for shadInst in self.shaderInstances:
                shadInst.setDiffuseWeight(self.properties.diffuseWeightFloatSldr.value)

    def setDiffuseColor(self):  # setDiffuse diffuseColorSldr
        if not self.shaderInstance.knownShader() or not self.shaderInstance.exists():
            return
        if not self.properties.affectMultiCheckbox.value:  # Single Shader
            self.shaderInstance.setDiffuseDisplay(self.properties.diffuseColorSldr.value)
        else:  # Multiple shaders
            for shadInst in self.shaderInstances:
                shadInst.setDiffuseDisplay(self.properties.diffuseColorSldr.value)

    def setDiffuseRoughness(self):  # setDiffuseRoughness diffuseRoughFloatSldr
        if not self.shaderInstance.knownShader() or not self.shaderInstance.exists():
            return
        if not self.properties.affectMultiCheckbox.value:  # Single Shader
            self.shaderInstance.setDiffuseRoughness(self.properties.diffuseRoughFloatSldr.value)
        else:  # Multiple shaders
            for shadInst in self.shaderInstances:
                shadInst.setDiffuseRoughness(self.properties.diffuseRoughFloatSldr.value)

    def setSpecularWeight(self):  # setSpecWeight specularWeightFloatSldr
        if not self.shaderInstance.knownShader() or not self.shaderInstance.exists():
            return
        if not self.properties.affectMultiCheckbox.value:  # Single Shader
            self.shaderInstance.setSpecWeight(self.properties.specularWeightFloatSldr.value)
        else:  # Multiple shaders
            for shadInst in self.shaderInstances:
                shadInst.setSpecWeight(self.properties.specularWeightFloatSldr.value)

    def setSpecularColor(self):  # setSpecColor specularColorSldr
        if not self.shaderInstance.knownShader() or not self.shaderInstance.exists():
            return
        if not self.properties.affectMultiCheckbox.value:  # Single Shader
            self.shaderInstance.setSpecColorDisplay(self.properties.specularColorSldr.value)
        else:  # Multiple shaders
            for shadInst in self.shaderInstances:
                shadInst.setSpecColorDisplay(self.properties.specularColorSldr.value)

    def setSpecularRoughness(self):  # setSpecRoughness specularRoughFloatSldr
        if not self.shaderInstance.knownShader() or not self.shaderInstance.exists():
            return
        if not self.properties.affectMultiCheckbox.value:  # Single Shader
            self.shaderInstance.setSpecRoughness(self.properties.specularRoughFloatSldr.value)
        else:  # Multiple shaders
            for shadInst in self.shaderInstances:
                shadInst.setSpecRoughness(self.properties.specularRoughFloatSldr.value)

    def setSpecularIOR(self):  # setSpecIOR iorFloatSldr
        if not self.shaderInstance.knownShader() or not self.shaderInstance.exists():
            return
        if not self.properties.affectMultiCheckbox.value:  # Single Shader
            self.shaderInstance.setSpecIOR(self.properties.iorFloatSldr.value)
        else:  # Multiple shaders
            for shadInst in self.shaderInstances:
                shadInst.setSpecIOR(self.properties.iorFloatSldr.value)

    def setMetalness(self):  # setMetalness metalnessFloatSldr
        if not self.shaderInstance.knownShader() or not self.shaderInstance.exists():
            return
        if not self.properties.affectMultiCheckbox.value:  # Single Shader
            self.shaderInstance.setMetalness(self.properties.metalnessFloatSldr.value)
        else:  # Multiple shaders
            for shadInst in self.shaderInstances:
                shadInst.setMetalness(self.properties.metalnessFloatSldr.value)

    def setCoatWeight(self):  # setCoatWeight clearCoatWeightFloatSldr
        if not self.shaderInstance.knownShader() or not self.shaderInstance.exists():
            return
        if not self.properties.affectMultiCheckbox.value:  # Single Shader
            self.shaderInstance.setCoatWeight(self.properties.clearCoatWeightFloatSldr.value)
        else:  # Multiple shaders
            for shadInst in self.shaderInstances:
                shadInst.setCoatWeight(self.properties.clearCoatWeightFloatSldr.value)

    def setCoatColor(self):  # setCoatColor clearCoatColorSldr
        if not self.shaderInstance.knownShader() or not self.shaderInstance.exists():
            return
        if not self.properties.affectMultiCheckbox.value:  # Single Shader
            self.shaderInstance.setCoatColorDisplay(self.properties.clearCoatColorSldr.value)
        else:  # Multiple shaders
            for shadInst in self.shaderInstances:
                shadInst.setCoatColorDisplay(self.properties.clearCoatColorSldr.value)

    def setCoatRoughness(self):  # setCoatRoughness clearCoatRoughFoatSldr
        if not self.shaderInstance.knownShader() or not self.shaderInstance.exists():
            return
        if not self.properties.affectMultiCheckbox.value:  # Single Shader
            self.shaderInstance.setCoatRoughness(self.properties.clearCoatRoughFoatSldr.value)
        else:  # Multiple shaders
            for shadInst in self.shaderInstances:
                shadInst.setCoatRoughness(self.properties.clearCoatRoughFoatSldr.value)

    def setCoatIOR(self):  # setCoatIOR clearCoatIorFloatSldr
        if not self.shaderInstance.knownShader() or not self.shaderInstance.exists():
            return
        if not self.properties.affectMultiCheckbox.value:  # Single Shader
            self.shaderInstance.setCoatIOR(self.properties.clearCoatIorFloatSldr.value)
        else:  # Multiple shaders
            for shadInst in self.shaderInstances:
                shadInst.setCoatIOR(self.properties.clearCoatIorFloatSldr.value)

    def setEmissionWeight(self):  # setEmissionWeight emissionWeightFloatSldr
        if not self.shaderInstance.knownShader() or not self.shaderInstance.exists():
            return
        if not self.properties.affectMultiCheckbox.value:  # Single Shader
            self.shaderInstance.setEmissionWeight(self.properties.emissionWeightFloatSldr.value)
        else:  # Multiple shaders
            for shadInst in self.shaderInstances:
                shadInst.setEmissionWeight(self.properties.emissionWeightFloatSldr.value)

    def setEmissionColor(self):  # setEmission emissionColorSldr
        if not self.shaderInstance.knownShader() or not self.shaderInstance.exists():
            return
        if not self.properties.affectMultiCheckbox.value:  # Single Shader
            self.shaderInstance.setEmissionDisplay(self.properties.emissionColorSldr.value)
        else:  # Multiple shaders
            for shadInst in self.shaderInstances:
                shadInst.setEmissionDisplay(self.properties.emissionColorSldr.value)

    def sliderReleased(self):
        self.closeUndoChunk()
        self.global_sendDiffuseColor()

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Widget GUI connections"""
        colSliderList = list()
        floatSliderList = list()

        self.displaySwitched.connect(self.shaderToGuiSel)
        for widget in self.widgets():
            widget.shaderNameComboE.itemRenamed.connect(self.renameShaderEvent)
            widget.shaderNameComboE.itemChanged.connect(self.shaderComboEChanged)
            widget.shaderNameComboE.aboutToShow.connect(self.updateNameComboE)
            widget.shaderPresetsCombo.itemChanged.connect(self.presetChanged)
            widget.createShaderBtn.clicked.connect(self.createShaderUndo)
            widget.reloadShaderBtn.clicked.connect(self.resetToPreset)
            widget.deleteShaderBtn.clicked.connect(self.deleteShader)
            widget.copyShaderBtn.clicked.connect(self.copyShader)
            widget.pasteShaderBtn.clicked.connect(self.pasteAssign)
            widget.pasteAttrBtn.clicked.connect(self.pasteAttributes)
            widget.transferShaderBtn.clicked.connect(self.transferAssign)
            widget.selectShaderBtn.clicked.connect(self.selectShader)
            widget.selectObjectsBtn.clicked.connect(self.selectObjFacesFromShader)
            widget.rendererIconMenu.actionTriggered.connect(self.changeRenderer)
            widget.rendererIconMenu.actionTriggered.connect(self.global_changeRenderer)  # updates other UIs
            widget.shaderTypeCombo.itemChanged.connect(self.global_shaderTypeUpdated)  # updates other UIs

            # Slider connections -------------------
            widget.diffuseWeightFloatSldr.numSliderChanged.connect(self.setDiffuseWeight)
            widget.diffuseColorSldr.colorSliderChanged.connect(self.setDiffuseColor)
            widget.diffuseRoughFloatSldr.numSliderChanged.connect(self.setDiffuseRoughness)
            widget.specularColorSldr.colorSliderChanged.connect(self.setSpecularColor)
            widget.specularRoughFloatSldr.numSliderChanged.connect(self.setSpecularRoughness)
            widget.iorFloatSldr.numSliderChanged.connect(self.setSpecularIOR)
            widget.metalnessFloatSldr.numSliderChanged.connect(self.setMetalness)
            widget.diffuseWeightFloatSldr.numSliderChanged.connect(self.setDiffuseWeight)
            widget.specularWeightFloatSldr.numSliderChanged.connect(self.setSpecularWeight)
            widget.clearCoatWeightFloatSldr.numSliderChanged.connect(self.setCoatWeight)
            widget.clearCoatRoughFoatSldr.numSliderChanged.connect(self.setCoatRoughness)
            widget.clearCoatIorFloatSldr.numSliderChanged.connect(self.setCoatIOR)
            widget.clearCoatColorSldr.colorSliderChanged.connect(self.setCoatColor)
            widget.emissionWeightFloatSldr.numSliderChanged.connect(self.setEmissionWeight)
            widget.emissionColorSldr.colorSliderChanged.connect(self.setEmissionColor)

            # Slider Lists --------------------
            colSliderList.append(widget.diffuseColorSldr)
            colSliderList.append(widget.specularColorSldr)
            colSliderList.append(widget.clearCoatColorSldr)
            colSliderList.append(widget.emissionColorSldr)
            floatSliderList.append(widget.diffuseWeightFloatSldr)
            floatSliderList.append(widget.diffuseRoughFloatSldr)
            floatSliderList.append(widget.metalnessFloatSldr)
            floatSliderList.append(widget.specularWeightFloatSldr)
            floatSliderList.append(widget.specularRoughFloatSldr)
            floatSliderList.append(widget.iorFloatSldr)
            floatSliderList.append(widget.clearCoatWeightFloatSldr)
            floatSliderList.append(widget.clearCoatRoughFoatSldr)
            floatSliderList.append(widget.clearCoatIorFloatSldr)
            floatSliderList.append(widget.emissionWeightFloatSldr)

        # Connect the float and color sliders correctly
        for colorSlider in colSliderList:
            colorSlider.sliderPressed.connect(self.openUndoChunk)
            colorSlider.sliderReleased.connect(self.sliderReleased)
        for floatSlider in floatSliderList:
            floatSlider.sliderPressed.connect(self.openUndoChunk)
            floatSlider.sliderReleased.connect(self.closeUndoChunk)
        # Callback methods
        self.selectionCallbacks.callback.connect(self.selectionChanged)  # monitor selection
        self.toolsetActivated.connect(self.startSelectionCallback)
        self.toolsetDeactivated.connect(self.stopSelectionCallback)


class GuiWidgets(QtWidgets.QWidget):
    def __init__(self, parent=None, properties=None, uiMode=None, toolsetWidget=None, presetShaderList=None):
        """Builds the main widgets for all GUIs

        properties is the list(dictionaries) used to set logic and pass between the different UI layouts
        such as compact/adv etc

        :param parent: the parent of this widget
        :type parent: qtObject
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: zoo.apps.toolsetsui.widgets.toolsetwidget.PropertiesDict
        :param uiMode: 0 is compact ui mode, 1 is advanced ui mode
        :type uiMode: int
        """
        super(GuiWidgets, self).__init__(parent=parent)
        self.properties = properties
        # Affect Multi Checkbox ----------------------------------------------------------
        toolTip = "While on this checkbox will make the sliders change all selected shaders. \n" \
                  "Useful for changing properties across multiple shaders. \n" \
                  "Tip: Use the Select Shaders icon button to select multiple shaders. "
        self.affectMultiCheckbox = elements.CheckBox("Affect Multiple", checked=False, toolTip=toolTip, right=False)
        # Shader Name Rename Combo edit -----------------------------------------------------
        toolTip = "The currently selected shader name.  Rename the shader by changing the name. "
        primaryTip = "Select assign a shader to the current selection. "
        secondaryTip = "Select a shader. "
        self.shaderNameComboE = elements.ComboEditRename(parent=self, label="Shader Name",
                                                         secondaryActive=True,
                                                         secondaryIcon="cursorSelect",
                                                         primaryTooltip=primaryTip,
                                                         secondaryTooltip=secondaryTip,
                                                         labelStretch=3, mainStretch=8,
                                                         toolTip=toolTip)
        # Shader Type Combo ---------------------------------------
        toolTip = "Select a shader type used while creating new shaders only. \n" \
                  "Change renderers with the renderer icon drop-down list."
        self.shaderTypeCombo = elements.ComboBoxRegular(label="",
                                                        items=SHADER_TYPES,
                                                        parent=self,
                                                        toolTip=toolTip,
                                                        setIndex=0)
        # Shader Presets Combo ---------------------------------------
        toolTip = "Select a preset to apply to the current shader."
        self.shaderPresetsCombo = elements.ComboBoxRegular(label="",
                                                           items=presetShaderList,
                                                           parent=self,
                                                           toolTip=toolTip,
                                                           setIndex=0)

        # Diffuse Title ----------------------------------------------------------------------------------------
        self.baseCollapsable = elements.CollapsableFrameThin("Base")

        # Diffuse Weight Slider --------------------------------------------------------

        toolTip = "Diffuse Weight adjusts the value (brightness) of the Diffuse Color "
        self.diffuseWeightFloatSldr = elements.FloatSlider(label="Diffuse Weight",
                                                           defaultValue=DIFFUSE_WEIGHT_DEFAULT,
                                                           toolTip=toolTip,
                                                           decimalPlaces=3)
        # Diffuse Color Slider ---------------------------------------
        toolTip = "The color of the shader. \n" \
                  "- The color, if not IOR-metal (specular IOR below 2). \n" \
                  "- Should be black if IOR metalness (specular IOR above 4). \n" \
                  "- Keep this color bright if the metalness slider is on. "
        self.diffuseColorSldr = elements.ColorSlider(label="Diffuse Color",
                                                     color=DIFFUSE_DEFAULT,
                                                     toolTip=toolTip)
        # Diffuse Roughness Slider ---------------------------------------
        toolTip = "Multiplies the color, low values darken the current shader/s. "
        self.diffuseRoughFloatSldr = elements.FloatSlider(label="Diffuse Rough",
                                                          defaultValue=DIFFUSE_ROUGHNESS_DEFAULT,
                                                          toolTip=toolTip,
                                                          decimalPlaces=3)
        # Metalness Slider ---------------------------------------
        toolTip = "Increase/decrease the metallic look of the current shader/s. "
        self.metalnessFloatSldr = elements.FloatSlider(label="Metalness",
                                                       defaultValue=METALNESS_DEFAULT,
                                                       toolTip=toolTip,
                                                       decimalPlaces=3)

        # Specular Title ----------------------------------------------------------------------------------------
        self.specCollapsable = elements.CollapsableFrameThin("Specular")

        # Specular Weight Slider --------------------------------------------------------
        toolTip = "Specular Weight multiplies the value (brightness) of the Specular Color. "
        self.specularWeightFloatSldr = elements.FloatSlider(label="Spec Weight",
                                                            defaultValue=SPECULAR_WEIGHT_DEFAULT,
                                                            toolTip=toolTip,
                                                            decimalPlaces=3)
        # Specular Color Slider ---------------------------------------
        toolTip = "Specular color, value in SRGB \n" \
                  "- Black if disabled, non reflective \n" \
                  "- White for most objects (IOR is set to 2 or below) \n" \
                  "- Becomes a color when shader is metal (IOR above 4)"
        self.specularColorSldr = elements.ColorSlider(label="Spec Color",
                                                      color=SPECULAR_DEFAULT,
                                                      toolTip=toolTip)
        # Specular Roughness Slider --------------------------------------------------------
        toolTip = "Specular Roughness \n" \
                  " 0.0 Shiny \n" \
                  " 0.6 Rough \n" \
                  " 1.0 Very rough cloth "
        self.specularRoughFloatSldr = elements.FloatSlider(label="Spec Rough",
                                                           defaultValue=ROUGHNESS_DEFAULT,
                                                           toolTip=toolTip,
                                                           decimalPlaces=3)
        # IOR Slider --------------------------------------------------------
        toolTip = "Incidence Of Refraction value, also Fresnel or Refractive Index. \n" \
                  "Although named `refractive` IOR also affects `specular reflection`. \n" \
                  " 1.0 Not Reflective or Refractive \n" \
                  " 1.3 Water \n" \
                  " 1.5 Most Objects, Plastics and Glass \n" \
                  " 2.0 Crystal \n" \
                  " 4.0 Dull Metal \n" \
                  " 12.0 Shiny Metal \n" \
                  " 20.0 Full Mirror"
        self.iorFloatSldr = elements.FloatSlider(label="IOR",
                                                 defaultValue=IOR_DEFAULT,
                                                 toolTip=toolTip,
                                                 sliderMin=1.0,
                                                 sliderMax=20.0,
                                                 decimalPlaces=2,
                                                 sliderAccuracy=2000)

        # Clear Coat Title -----------------------------------------------------------------------------------------
        self.clearCoatCollapsable = elements.CollapsableFrameThin("Clear Coat", collapsed=True)
        # Clear Coat Weight Slider --------------------------------------------------------
        toolTip = "Clear Coat Weight adjusts the value (brightness) of the Clear Coat Specular Color"
        self.clearCoatWeightFloatSldr = elements.FloatSlider(label="Coat Weight",
                                                             defaultValue=COAT_WEIGHT_DEFAULT,
                                                             toolTip=toolTip,
                                                             decimalPlaces=3)
        # Clear Coat Color Slider ---------------------------------------
        toolTip = "The second specular layer, Clear Coat color. \n" \
                  "- Usually white for a glassy polish"
        self.clearCoatColorSldr = elements.ColorSlider(label="Coat Color",
                                                       color=COAT_COLOR_DEFAULT,
                                                       toolTip=toolTip)
        # Specular Roughness Slider --------------------------------------------------------
        toolTip = "Adjusts the roughness of the second specular layer, Clear Coat. \n" \
                  " 0.0 Shiny \n" \
                  " 0.6 Rough"
        self.clearCoatRoughFoatSldr = elements.FloatSlider(label="Coat Rough",
                                                           defaultValue=COAT_ROUGH_DEFAULT,
                                                           toolTip=toolTip,
                                                           decimalPlaces=3)
        # IOR Clear Coat Slider --------------------------------------------------------
        toolTip = "value for clear coat is usually \n" \
                  "- 1.5 Glass Polish \n" \
                  "- 1.3 Wet Water"

        self.clearCoatIorFloatSldr = elements.FloatSlider(label="IOR",
                                                          defaultValue=COAT_IOR_DEFAULT,
                                                          toolTip=toolTip,
                                                          sliderMin=1.0,
                                                          sliderMax=20.0,
                                                          decimalPlaces=2,
                                                          sliderAccuracy=2000)

        # Emission Title --------------------------------------------------------------------------------------------
        self.emissionCollapsable = elements.CollapsableFrameThin("Emission", collapsed=True)
        # Emission Weight Slider ---------------------------------------
        toolTip = "Multiplies the value (brightness) of the Emission Color. \n" \
                  "Values can go above one and will more brightly affect the scene \n" \
                  "with raytracing. "
        self.emissionWeightFloatSldr = elements.FloatSlider(label="Emit Weight",
                                                            defaultValue=EMISSION_WEIGHT_DEFAULT,
                                                            toolTip=toolTip,
                                                            decimalPlaces=3, dynamicMax=True)
        # Emission Color Slider ---------------------------------------
        toolTip = "Adjusts the glow color of the current shader/s. "
        self.emissionColorSldr = elements.ColorSlider(label="Emission Color",
                                                      color=EMISSION_DEFAULT,
                                                      toolTip=toolTip)

        # Create Main Button ---------------------------------------------------------------------------------------
        toolTip = "Creates a new shader on the selected object/s"
        self.createShaderBtn = elements.styledButton("Create Shader Type",
                                                     "shaderBall",
                                                     self,
                                                     toolTip,
                                                     style=uic.BTN_DEFAULT)
        # Transfer Shader Btn --------------------------------------------
        toolTip = "Transfer the current shader to another object \n" \
                  "- 1. Select two or more objects. \n" \
                  "- 2. The shader from the first object will be transferred to others."
        self.transferShaderBtn = elements.styledButton("Transfer", "transferShader",
                                                       toolTip=toolTip,
                                                       style=uic.BTN_DEFAULT)
        # Copy Shader Btn --------------------------------------------
        toolTip = "Copy the current shader settings to the clipboard"
        self.copyShaderBtn = elements.styledButton("Copy", "copyShader",
                                                   toolTip=toolTip,
                                                   style=uic.BTN_DEFAULT)
        # Paste Attribute Shader Btn --------------------------------------------
        toolTip = "Paste the shader attribute settings from the clipboard \n" \
                  "Shader attribute settings will be pasted, the existing shader will remain."
        self.pasteAttrBtn = elements.styledButton("Paste", "pasteAttributes",
                                                  toolTip=toolTip,
                                                  style=uic.BTN_DEFAULT)
        # Paste Assign Shader Btn --------------------------------------------
        toolTip = "Paste/Assign the shader from the clipboard \n" \
                  "Existing shader will be assigned to selected geometry"
        self.pasteShaderBtn = elements.styledButton("Paste", "pasteAssign",
                                                    toolTip=toolTip,
                                                    style=uic.BTN_DEFAULT)
        # Reset Shader Btn --------------------------------------------
        toolTip = "Reset the shader's attributes to the default or the current preset's values"
        self.reloadShaderBtn = elements.styledButton("", "reload2",
                                                     toolTip=toolTip,
                                                     style=uic.BTN_TRANSPARENT_BG)
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
        # Delete Shader Btn --------------------------------------------
        toolTip = "Deletes the active shader/s from the scene. "
        self.deleteShaderBtn = elements.styledButton("",
                                                     "trash",
                                                     self,
                                                     toolTip=toolTip,
                                                     style=uic.BTN_TRANSPARENT_BG)
        # Renderer Button --------------------------------------
        toolTip = "Change the renderer to Arnold, Redshift or Renderman. "
        self.rendererIconMenu = elements.iconMenuButtonCombo(RENDERER_ICONS_LIST,
                                                             self.properties.rendererIconMenu.value,
                                                             toolTip=toolTip)


class GuiCompact(GuiWidgets):
    def __init__(self, parent=None, properties=None, uiMode=UI_MODE_COMPACT, toolsetWidget=None,
                 presetShaderList=None):
        """Adds the layout building the compact version of the GUI:

            default uiMode - 0 is advanced (UI_MODE_COMPACT)

        :param parent: the parent of this widget
        :type parent: QtWidgets.QWidget
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: zoo.apps.toolsetsui.widgets.toolsetwidget.PropertiesDict
        """
        super(GuiCompact, self).__init__(parent=parent, properties=properties, uiMode=uiMode,
                                         toolsetWidget=toolsetWidget, presetShaderList=presetShaderList)
        # Main Layout ---------------------------------------
        contentsLayout = elements.vBoxLayout(parent=self,
                                             margins=(uic.WINSIDEPAD, uic.WINTOPPAD, uic.WINSIDEPAD, uic.WINBOTPAD))
        # Preset Layout -------------------------------------
        presetLayout = elements.hBoxLayout(spacing=uic.SPACING)
        presetLayout.addWidget(self.shaderPresetsCombo, 10)
        presetLayout.addWidget(self.reloadShaderBtn, 1)
        # Options Layout -------------------------------------
        optionsLayout = elements.hBoxLayout(spacing=uic.SPACING)
        optionsLayout.addWidget(self.affectMultiCheckbox, 10)
        optionsLayout.addWidget(self.selectShaderBtn, 1)
        optionsLayout.addWidget(self.selectObjectsBtn, 1)
        # Top Layout -------------------------------------
        topLayout = elements.hBoxLayout(spacing=uic.SVLRG)
        topLayout.addLayout(presetLayout, 1)
        topLayout.addLayout(optionsLayout, 1)
        # Name Checkbox Layout ---------------------------------------
        nameCheckboxLayout = elements.hBoxLayout(spacing=uic.SPACING)
        nameCheckboxLayout.addWidget(self.shaderNameComboE, 20)
        nameCheckboxLayout.addWidget(self.deleteShaderBtn, 1)
        # Slider Layout ---------------------------------------
        sliderLayout = elements.vBoxLayout(margins=(0, 0, 0, uic.SMLPAD), spacing=uic.SLRG)
        sliderLayout.addWidget(self.diffuseColorSldr)
        sliderLayout.addWidget(self.metalnessFloatSldr)
        sliderLayout.addWidget(self.specularWeightFloatSldr)
        sliderLayout.addWidget(self.specularColorSldr)
        sliderLayout.addWidget(self.specularRoughFloatSldr)
        sliderLayout.addWidget(self.clearCoatWeightFloatSldr)
        # Transfer Layout ----------------------------------------
        transferBtnLayout = elements.hBoxLayout(spacing=uic.SPACING)
        transferBtnLayout.addWidget(self.transferShaderBtn, 1)
        transferBtnLayout.addWidget(self.copyShaderBtn, 1)
        transferBtnLayout.addWidget(self.pasteShaderBtn, 1)
        transferBtnLayout.addWidget(self.pasteAttrBtn, 1)
        # ShaderType Layout ----------------------------------------
        typeLayout = elements.hBoxLayout(spacing=uic.SPACING)
        typeLayout.addWidget(self.shaderTypeCombo, 10)
        typeLayout.addWidget(self.rendererIconMenu, 1)
        # Buttons Main Layout ---------------------------------------
        botBtnLayout = elements.hBoxLayout(spacing=uic.SREG)
        botBtnLayout.addWidget(self.createShaderBtn, 1)
        botBtnLayout.addLayout(typeLayout, 1)
        # Bottom Section Main V Layout ---------------------------------------
        botSectionLayout = elements.vBoxLayout(spacing=uic.SPACING)
        botSectionLayout.addLayout(transferBtnLayout)
        botSectionLayout.addLayout(botBtnLayout)
        # Add To Main Layout ---------------------------------------
        contentsLayout.addLayout(topLayout)
        contentsLayout.addLayout(nameCheckboxLayout)
        contentsLayout.addLayout(sliderLayout)
        # contentsLayout.addLayout(transferBtnLayout)
        contentsLayout.addLayout(botSectionLayout)
        # contentsLayout.addWidget(elements.LabelDivider(text="Create New"))


class GuiAdvanced(GuiWidgets):
    def __init__(self, parent=None, properties=None, uiMode=UI_MODE_ADVANCED, toolsetWidget=None,
                 presetShaderList=None):
        """Adds the layout building the advanced version of the GUI:

            default uiMode - 1 is advanced (UI_MODE_ADVANCED)

        :type toolsetWidget: :class:`ShaderManager`
        :param parent: the parent of this widget
        :type parent: QtWidgets.QWidget
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: zoo.apps.toolsetsui.widgets.toolsetwidget.PropertiesDict
        """
        super(GuiAdvanced, self).__init__(parent=parent, properties=properties, uiMode=uiMode,
                                          toolsetWidget=toolsetWidget, presetShaderList=presetShaderList)
        # Main Layout ---------------------------------------
        contentsLayout = elements.vBoxLayout(self,
                                             margins=(uic.WINSIDEPAD, uic.WINTOPPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                             spacing=uic.SREG)
        # Preset Layout -------------------------------------
        presetLayout = elements.hBoxLayout(spacing=uic.SPACING)
        presetLayout.addWidget(self.shaderPresetsCombo, 10)
        presetLayout.addWidget(self.reloadShaderBtn, 1)
        # Options Layout -------------------------------------
        optionsLayout = elements.hBoxLayout(spacing=uic.SPACING)
        optionsLayout.addWidget(self.affectMultiCheckbox, 10)
        optionsLayout.addWidget(self.selectShaderBtn, 1)
        optionsLayout.addWidget(self.selectObjectsBtn, 1)
        # Top Layout -------------------------------------
        topLayout = elements.hBoxLayout(spacing=uic.SVLRG)
        topLayout.addLayout(presetLayout, 1)
        topLayout.addLayout(optionsLayout, 1)
        # Name Checkbox Layout ---------------------------------------
        nameCheckboxLayout = elements.hBoxLayout(spacing=uic.SPACING)
        nameCheckboxLayout.addWidget(self.shaderNameComboE, 20)
        nameCheckboxLayout.addWidget(self.deleteShaderBtn, 1)
        # Base Layout ---------------------------------------
        baseLayout = elements.vBoxLayout(margins=(uic.SREG, 0, uic.SREG, 0), spacing=uic.SLRG)
        baseLayout.addWidget(self.diffuseWeightFloatSldr, 1)
        baseLayout.addWidget(self.diffuseColorSldr, 1)
        baseLayout.addWidget(self.diffuseRoughFloatSldr, 1)
        baseLayout.addWidget(self.metalnessFloatSldr, 1)
        # Specular Layout ---------------------------------------
        specularLayout = elements.vBoxLayout(margins=(uic.SREG, 0, uic.SREG, 0), spacing=uic.SLRG)
        specularLayout.addWidget(self.specularWeightFloatSldr, 1)
        specularLayout.addWidget(self.specularColorSldr, 1)
        specularLayout.addWidget(self.specularRoughFloatSldr, 1)
        specularLayout.addWidget(self.iorFloatSldr, 1)
        # Clear Coat Layout ---------------------------------------
        clearCoatLayout = elements.vBoxLayout(margins=(uic.SREG, 0, uic.SREG, 0), spacing=uic.SLRG)
        clearCoatLayout.addWidget(self.clearCoatWeightFloatSldr, 1)
        clearCoatLayout.addWidget(self.clearCoatColorSldr, 1)
        clearCoatLayout.addWidget(self.clearCoatRoughFoatSldr, 1)
        clearCoatLayout.addWidget(self.clearCoatIorFloatSldr, 1)
        # Emission Layout ---------------------------------------
        emissionLayout = elements.vBoxLayout(margins=(uic.SREG, 0, uic.SREG, uic.SMLPAD), spacing=uic.SLRG)
        emissionLayout.addWidget(self.emissionWeightFloatSldr, 1)
        emissionLayout.addWidget(self.emissionColorSldr, 1)
        # ShaderType Layout ----------------------------------------
        typeLayout = elements.hBoxLayout(spacing=uic.SREG)
        typeLayout.addWidget(self.shaderTypeCombo, 10)
        typeLayout.addWidget(self.rendererIconMenu, 1)
        # Transfer Layout ----------------------------------------
        transferBtnLayout = elements.hBoxLayout(spacing=uic.SPACING)
        transferBtnLayout.addWidget(self.transferShaderBtn, 1)
        transferBtnLayout.addWidget(self.copyShaderBtn, 1)
        transferBtnLayout.addWidget(self.pasteShaderBtn, 1)
        transferBtnLayout.addWidget(self.pasteAttrBtn, 1)
        # Buttons Main Layout ---------------------------------------
        botBtnLayout = elements.hBoxLayout(spacing=uic.SREG)
        botBtnLayout.addWidget(self.createShaderBtn, 1)
        botBtnLayout.addLayout(typeLayout, 1)
        # Bottom Section Main V Layout ---------------------------------------
        botSectionLayout = elements.vBoxLayout(spacing=uic.SPACING)
        botSectionLayout.addLayout(transferBtnLayout)
        botSectionLayout.addLayout(botBtnLayout)
        # Add To Main Layout ---------------------------------------
        contentsLayout.addLayout(topLayout)
        contentsLayout.addLayout(nameCheckboxLayout)
        contentsLayout.addWidget(self.baseCollapsable)
        contentsLayout.addWidget(self.specCollapsable)
        contentsLayout.addWidget(self.clearCoatCollapsable)
        contentsLayout.addWidget(self.emissionCollapsable)
        self.baseCollapsable.hiderLayout.addLayout(baseLayout)
        self.specCollapsable.hiderLayout.addLayout(specularLayout)
        self.clearCoatCollapsable.addLayout(clearCoatLayout)
        self.emissionCollapsable.hiderLayout.addLayout(emissionLayout)
        contentsLayout.addLayout(botSectionLayout)

        # Collapsable Connections -------------------------------------
        self.baseCollapsable.toggled.connect(toolsetWidget.treeWidget.updateTree)
        self.specCollapsable.toggled.connect(toolsetWidget.treeWidget.updateTree)
        self.clearCoatCollapsable.toggled.connect(toolsetWidget.treeWidget.updateTree)
        self.emissionCollapsable.toggled.connect(toolsetWidget.treeWidget.updateTree)
