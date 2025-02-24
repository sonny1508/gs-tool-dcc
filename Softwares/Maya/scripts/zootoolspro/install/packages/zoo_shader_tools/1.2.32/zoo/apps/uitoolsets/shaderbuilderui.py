""" ---------- Shader Builder UI Tool -------------
Builds Shaders from images inside directories.


"""
import os

from zoovendor.Qt import QtWidgets

from zoo.libs.maya.cmds.workspace import mayaworkspace

from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements

from zoo.libs.maya.cmds.textures.shaderbuilder import shaderbuilder

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1

PRESET_LIST = shaderbuilder.PRESET_LIST
PRESET_DICT = shaderbuilder.PRESET_DICT


class ShaderBuilder(object):  # toolsetwidget.ToolsetWidget
    id = "shaderBuilder"
    info = "Builds Shaders from images inside directories."
    uiData = {"label": "Shader Builder (Alpha)",
              "icon": "shaderBall",
              "tooltip": "Builds Shaders from images inside directories.",
              "defaultActionDoubleClick": False}

    # ------------------
    # STARTUP
    # ------------------

    def preContentSetup(self):
        """First code to run, treat this as the __init__() method"""
        pass

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
        self.presetList = PRESET_LIST
        self.presetDict = PRESET_DICT
        self.setPreset()
        self.uiConnections()

    def defaultAction(self):
        """Double Click
        Double clicking the tools toolset icon will run this method
        Be sure "defaultActionDoubleClick": True is set inside self.uiData (meta data of this class)"""
        pass

    def currentWidget(self):
        """ Currently active widget

        :return:
        :rtype: GuiAdvanced or GuiCompact
        """
        return super(ShaderBuilder, self).currentWidget()

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiAdvanced or GuiCompact]
        """
        return super(ShaderBuilder, self).widgets()

    # ------------------
    # SET DIRECTORY
    # ------------------

    def loadDirectoryPath(self):
        """Loads a select directory window to browse for directory on disk"""
        directory = self.properties.folderPathTxt.value

        if not directory:  # If no directory found then sets to sourceImages in project directory
            projectDirectory = mayaworkspace.getCurrentMayaWorkspace()
            directory = os.path.join(projectDirectory, "sourceImages/")

        if not os.path.exists(directory):  # no directory found so use home
            directory = os.path.expanduser("~")

        # Open dialog ------------------------------------------------
        directoryPath = elements.FileDialog_directory(windowName="Set Shader Builder Directory", defaultPath=directory)
        if not directoryPath:
            return
        self.properties.folderPathTxt.value = directoryPath
        self.updateDirectoryTxt()

    def updateDirectoryTxt(self):
        self.updateFromProperties()
        shaderList = shaderbuilder.previewShaders(
            directory=self.properties.folderPathTxt.value)  # todo add more options
        for widget in self.widgets():
            if shaderList:
                widget.buildButton.setText("Build Shaders From "
                                           "Texture Directories ({} Found)".format(str(len(shaderList))))
            else:
                widget.buildButton.setText("Build Shaders From Texture Directories (0 Found)")

    # ------------------
    # SET PRESET
    # ------------------

    def _listStr(self, aList):
        delim = ', '
        return delim.join(aList)

    def setPreset(self):
        presetKey = self.presetList[self.properties.presetCombo.value]
        presetDict = self.presetDict[presetKey]

        self.properties.attrDiffuseColStr.value = self._listStr(presetDict[shaderbuilder.DIFFUSE_COLOR])
        self.properties.attrAlbedoColStr.value = self._listStr(presetDict[shaderbuilder.ALBEDO_COLOR])
        self.properties.attrSpecularColStr.value = self._listStr(presetDict[shaderbuilder.SPECULAR_COLOR])
        self.properties.attrSpecularRoughnessStr.value = self._listStr(presetDict[shaderbuilder.SPECULAR_ROUGHNESS])
        self.properties.attrMetalnessStr.value = self._listStr(presetDict[shaderbuilder.METALNESS])
        self.properties.attrNormalStr.value = self._listStr(presetDict[shaderbuilder.NORMAL])
        self.properties.attrBumpStr.value = self._listStr(presetDict[shaderbuilder.BUMP])
        self.properties.attrAoStr.value = self._listStr(presetDict[shaderbuilder.AO])
        self.properties.attrArmStr.value = self._listStr(presetDict[shaderbuilder.ARM])

        self.updateFromProperties()

    # ------------------
    # LOGIC
    # ------------------

    def shaderBuilder(self):
        """
        """
        # build many shaders from sub directories.
        shaderbuilder.buildShadersTextures(directory=self.properties.folderPathTxt.value)

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        for widget in self.widgets():
            widget.browseBtn.clicked.connect(self.loadDirectoryPath)
            widget.buildButton.clicked.connect(self.shaderBuilder)
            widget.folderPathTxt.edit.textModified.connect(self.updateDirectoryTxt)
            widget.presetCombo.itemChanged.connect(self.setPreset)


class GuiWidgets(QtWidgets.QWidget):
    def __init__(self, parent=None, properties=None, uiMode=None, toolsetWidget=None):
        """Builds the main widgets for all GUIs

        properties is the list(dictionaries) used to set logic and pass between the different UI layouts
        such as compact/adv etc

        :param parent: the parent of this widget
        :type parent: QtWidgets.QWidget
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: zoo.apps.toolsetsui.widgets.toolsetwidget.PropertiesDict
        :param uiMode: 0 is compact ui mode, 1 is advanced ui mode
        :type uiMode: int
        """
        super(GuiWidgets, self).__init__(parent=parent)
        self.properties = properties
        # Preset Combo ---------------------------------------
        self.presetCombo = elements.ComboBoxRegular(label="Preset", items=PRESET_LIST, labelRatio=2, boxRatio=9)

        # Attribute Build Options Title -----------------------------------------------------------------------------
        self.buildOptionsCollapsable = elements.CollapsableFrameThin("Attribute Build Options", collapsed=True)

        # combineNormalBump=True, includeAO=True, includeArm=True
        tooltip = ""
        self.useAoCheckbox = elements.CheckBox(label="Use AO", checked=True, toolTip=tooltip)
        self.useArmCheckbox = elements.CheckBox(label="Use ARM", checked=True, toolTip=tooltip)
        self.combineNormalBumpCheckbox = elements.CheckBox(label="Combine Normal Bump", checked=True, toolTip=tooltip)

        self.diffuseColorSlider = elements.ColorSlider(label="Diffuse Color", color=(0.5, 0.5, 0.5))

        # Texture Tagging Options Title -----------------------------------------------------------------------------
        self.textureTaggingCollapsable = elements.CollapsableFrameThin("Texture Tagging Options", collapsed=True)
        labelRatio = 10
        editRatio = 20
        self.attrDiffuseColStr = elements.StringEdit(label="Diffuse Color", editText="", toolTip=tooltip,
                                                     labelRatio=labelRatio, editRatio=editRatio)
        self.attrAlbedoColStr = elements.StringEdit(label="Albedo Color", editText="", toolTip=tooltip,
                                                    labelRatio=labelRatio, editRatio=editRatio)
        self.attrSpecularColStr = elements.StringEdit(label="Specular Color", editText="", toolTip=tooltip,
                                                      labelRatio=labelRatio, editRatio=editRatio)
        self.attrSpecularRoughnessStr = elements.StringEdit(label="Specular Roughness", editText="", toolTip=tooltip,
                                                            labelRatio=labelRatio, editRatio=editRatio)
        self.attrMetalnessStr = elements.StringEdit(label="Metalness", editText="", toolTip=tooltip,
                                                    labelRatio=labelRatio, editRatio=editRatio)
        self.attrNormalStr = elements.StringEdit(label="Normal", editText="", toolTip=tooltip,
                                                 labelRatio=labelRatio, editRatio=editRatio)
        self.attrBumpStr = elements.StringEdit(label="Bump", editText="", toolTip=tooltip,
                                               labelRatio=labelRatio, editRatio=editRatio)
        self.attrAoStr = elements.StringEdit(label="Ambient Occlusion", editText="", toolTip=tooltip,
                                             labelRatio=labelRatio, editRatio=editRatio)
        self.attrArmStr = elements.StringEdit(label="ARM", editText="", toolTip=tooltip,
                                              labelRatio=labelRatio, editRatio=editRatio)

        # General Options Title -----------------------------------------------------------------------------
        self.generalCollapsable = elements.CollapsableFrameThin("General Options", collapsed=False)

        # Shader Type --------------------------------------
        self.shaderTypeCombo = elements.ComboBoxRegular(label="Build Type", items=["standardSurface"], labelRatio=2,
                                                        boxRatio=9)

        # Directory Path Location --------------------------------------
        toolTip = "Set the path of the root texture directory, also builds subdirectories. \n\n" \
                  "Current Limitation: One shader per directory. \n" \
                  "Skips sub-directories where no compatible textures are found."
        self.folderPathTxt = elements.StringEdit("Textures",
                                                 "",
                                                 editPlaceholder="Add Directory",
                                                 labelRatio=100,
                                                 editRatio=400,
                                                 toolTip=toolTip)
        self.browseBtn = elements.styledButton("",
                                               "browse",
                                               self,
                                               toolTip=toolTip,
                                               style=uic.BTN_DEFAULT,
                                               minWidth=uic.BTN_W_ICN_MED)

        # Build Folder ---------------------------------------
        tooltip = "Builds shaders from textures found in the directory and subdirectories. \n\n" \
                  "Current Limitation: One shader per directory. \n" \
                  "Skips sub-directories where no compatible textures are found."
        self.buildButton = elements.styledButton("Build Shaders From Texture Directories (0 Found)",
                                                 icon="shaderBall",
                                                 toolTip=tooltip,
                                                 style=uic.BTN_DEFAULT)


class GuiCompact(GuiWidgets):
    def __init__(self, parent=None, properties=None, uiMode=UI_MODE_COMPACT, toolsetWidget=None):
        """Adds the layout building the compact version of the GUI:

            default uiMode - 0 is advanced (UI_MODE_COMPACT)

        :param parent: the parent of this widget
        :type parent: QtWidgets.QWidget
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: zoo.apps.toolsetsui.widgets.toolsetwidget.PropertiesDict
        """
        super(GuiCompact, self).__init__(parent=parent, properties=properties, uiMode=uiMode,
                                         toolsetWidget=toolsetWidget)
        # Main Layout ---------------------------------------
        mainLayout = elements.vBoxLayout(self, margins=(uic.WINSIDEPAD, uic.WINBOTPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SREG)

        # Combo Layout ---------------------------------------
        comboLayout = elements.hBoxLayout(margins=(uic.SREG, 0, uic.SREG, 0))
        comboLayout.addWidget(self.presetCombo)

        # Checkbox Layout ---------------------------------------
        checkboxLayout = elements.hBoxLayout(margins=(uic.SREG, uic.SREG, uic.SREG, 0))
        checkboxLayout.addWidget(self.useAoCheckbox, 1)
        checkboxLayout.addWidget(self.useArmCheckbox, 1)
        checkboxLayout.addWidget(self.combineNormalBumpCheckbox, 1)

        # Color Layout ---------------------------------------
        colorLayout = elements.vBoxLayout(margins=(uic.SREG, uic.SREG, uic.SREG, 0))
        colorLayout.addWidget(self.diffuseColorSlider, 1)

        # Tag Layout ---------------------------------------
        tagLayout = elements.vBoxLayout(margins=(uic.SREG, uic.SREG, uic.SREG, 0))
        tagLayout.addWidget(self.attrDiffuseColStr)
        tagLayout.addWidget(self.attrAlbedoColStr)
        tagLayout.addWidget(self.attrSpecularColStr)
        tagLayout.addWidget(self.attrSpecularRoughnessStr)
        tagLayout.addWidget(self.attrMetalnessStr)
        tagLayout.addWidget(self.attrNormalStr)
        tagLayout.addWidget(self.attrBumpStr)
        tagLayout.addWidget(self.attrAoStr)
        tagLayout.addWidget(self.attrArmStr)

        # Browse Layout ---------------------------------------
        browseLayout = elements.hBoxLayout(margins=(uic.SREG, 0, uic.SREG, 0))
        browseLayout.addWidget(self.folderPathTxt, 10)
        browseLayout.addWidget(self.browseBtn, 1)

        # Type Combo Layout ---------------------------------------
        typeLayout = elements.hBoxLayout(margins=(uic.SREG, 0, uic.SREG, 0))
        typeLayout.addWidget(self.shaderTypeCombo)

        # Add To Main Layout ---------------------------------------
        mainLayout.addLayout(comboLayout)

        mainLayout.addWidget(self.buildOptionsCollapsable)
        self.buildOptionsCollapsable.hiderLayout.addLayout(checkboxLayout)
        self.buildOptionsCollapsable.hiderLayout.addLayout(colorLayout)

        mainLayout.addWidget(self.textureTaggingCollapsable)
        self.textureTaggingCollapsable.hiderLayout.addLayout(tagLayout)

        mainLayout.addWidget(self.generalCollapsable)
        self.generalCollapsable.hiderLayout.addLayout(typeLayout)
        self.generalCollapsable.hiderLayout.addLayout(browseLayout)

        mainLayout.addWidget(self.buildButton)

        # Collapsable Connections -------------------------------------
        self.buildOptionsCollapsable.toggled.connect(toolsetWidget.treeWidget.updateTree)
        self.textureTaggingCollapsable.toggled.connect(toolsetWidget.treeWidget.updateTree)
        self.generalCollapsable.toggled.connect(toolsetWidget.treeWidget.updateTree)


class GuiAdvanced(GuiWidgets):
    def __init__(self, parent=None, properties=None, uiMode=UI_MODE_ADVANCED, toolsetWidget=None):
        """Adds the layout building the advanced version of the GUI:

            default uiMode - 1 is advanced (UI_MODE_ADVANCED)

        :param parent: the parent of this widget
        :type parent: QtWidgets.QWidget
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: zoo.apps.toolsetsui.widgets.toolsetwidget.PropertiesDict
        """
        super(GuiAdvanced, self).__init__(parent=parent, properties=properties, uiMode=uiMode,
                                          toolsetWidget=toolsetWidget)
        # Main Layout ---------------------------------------
        mainLayout = elements.vBoxLayout(self, margins=(uic.WINSIDEPAD, uic.WINBOTPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SREG)
        # Add To Main Layout ---------------------------------------
        mainLayout.addWidget(self.buildButton)
