from zoovendor.Qt import QtWidgets

from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements
from zoo.libs.utils import output

from zoo.preferences.interfaces import coreinterfaces

from zoo.core.util import env

if env.isMaya():
    from zoo.libs.maya.cmds.shaders import toggleshaders, shdmultconstants

    SHADER_TYPES = shdmultconstants.SHADER_TYPE_LIST
    SHADERTYPE_SUFFIX_DICT = shdmultconstants.SHADERTYPE_SUFFIX_DICT
    RENDERER_SUFFIXES = list()
    for shader in SHADER_TYPES:
        RENDERER_SUFFIXES.append(SHADERTYPE_SUFFIX_DICT[shader])  # Accounts for 2019 and lower

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1


class ShaderSwapSuffix(toolsetwidget.ToolsetWidget):
    id = "shaderSwapSuffix"
    info = "Swaps shader assignments by suffix names."
    uiData = {"label": "Swap By Shader Suffix",
              "icon": "invert",
              "tooltip": "Swaps shader assignments by suffix names.",
              "helpUrl": "https://create3dcharacters.com/maya-tool-shader-swap/",
              "defaultActionDoubleClick": False}

    # ------------------
    # STARTUP
    # ------------------

    def preContentSetup(self):
        """First code to run, treat this as the __init__() method"""
        self.generalPrefs = coreinterfaces.generalInterface()
        self.renderer = self.generalPrefs.primaryRenderer()
        self.shaderType = shdmultconstants.RENDERER_DEFAULT_SHADER[self.renderer]

    def contents(self):
        """The UI Modes to build, compact, medium and or advanced """
        return [self.initCompactWidget()]

    def initCompactWidget(self):
        """Builds the Compact GUI (self.compactWidget) """
        self.compactWidget = GuiCompact(parent=self, properties=self.properties, toolsetWidget=self)
        return self.compactWidget

    def postContentSetup(self):
        """Last of the initialize code"""
        self.properties.quickSuffix1Combo.value = SHADER_TYPES.index(self.shaderType)  # set first suffix index
        self.updateSwapSuffixOne()  # update the suffix and properties
        self.uiConnections()

    def defaultAction(self):
        """Double Click
        Double clicking the tools toolset icon will run this method
        Be sure "defaultActionDoubleClick": True is set inside self.uiData (meta data of this class)"""
        pass

    def currentWidget(self):
        """Returns the current widget class eg. self.compactWidget or self.advancedWidget

        Over ridden class
        :rtype: GuiWidgets
        """
        return super(ShaderSwapSuffix, self).currentWidget()

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiAdvanced or GuiCompact]
        """
        return super(ShaderSwapSuffix, self).widgets()

    # ------------------
    # RENDERER - AND SEND/RECEIVE ALL TOOLSETS
    # ------------------

    def global_receiveRendererChange(self, renderer):
        """Receives from other GUIs, changes the renderer when it is changed"""
        self.shaderType = shdmultconstants.RENDERER_DEFAULT_SHADER[renderer]
        self.properties.quickSuffix1Combo.value = SHADER_TYPES.index(self.shaderType)  # Set first suffix index
        self.updateSwapSuffixOne()  # Update the suffix and properties

    # ------------------
    # UPDATE GUI
    # ------------------

    def updateSwapSuffixOne(self, event=None):
        """ Updates the text for Suffix One on the combobox change

        :param event: Event with all the values related to the change.
        :type event: zoo.libs.pyqt.extended.combobox.ComboItemChangedEvent
        """
        self.properties.suffix1Txt.value = RENDERER_SUFFIXES[self.properties.quickSuffix1Combo.value]
        self.updateFromProperties()

    def updateSwapSuffixTwo(self, event=None):
        """ Updates the text for Suffix Two on the combobox change

        :param event: Event with all the values related to the change.
        :type event: zoo.libs.pyqt.extended.combobox.ComboItemChangedEvent
        """
        self.properties.suffix2Txt.value = RENDERER_SUFFIXES[self.properties.quickSuffix2Combo.value]
        self.updateFromProperties()

    # ------------------
    # LOGIC
    # ------------------

    @toolsetwidget.ToolsetWidget.undoDecorator
    def shaderSwap(self):
        """Swaps shader assignments based on the suffixes from the GUI
        """
        if self.properties.suffix2Txt.value == self.properties.suffix1Txt.value:
            output.displayWarning("Shader suffix's are identical, suffix types must be unique.")
            return
        toggleshaders.toggleShaderAuto(shader1Suffix=self.properties.suffix1Txt.value,
                                       shader2Suffix=self.properties.suffix2Txt.value)

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        # Main Button
        self.compactWidget.shaderSwapBtn.clicked.connect(self.shaderSwap)
        # Combo Update GUI
        self.compactWidget.quickSuffix1Combo.itemChanged.connect(self.updateSwapSuffixOne)
        self.compactWidget.quickSuffix2Combo.itemChanged.connect(self.updateSwapSuffixTwo)


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
        self.properties = properties
        # Quick Suffix Combos ---------------------------------------
        toolTip = "Switch to quickly add the renderer's suffix in the textbox below"
        self.quickSuffix1Combo = elements.ComboBoxRegular(label="Shader",
                                                          items=SHADER_TYPES,
                                                          setIndex=0,
                                                          toolTip=toolTip,
                                                          labelRatio=2,
                                                          boxRatio=5)
        self.quickSuffix2Combo = elements.ComboBoxRegular(label="Shader",
                                                          items=SHADER_TYPES,
                                                          setIndex=3,
                                                          toolTip=toolTip,
                                                          labelRatio=2,
                                                          boxRatio=5)
        # Suffix Text Boxes ---------------------------------------
        toolTip = "The name of a suffix to swap, the order does not matter"
        self.suffix1Txt = elements.StringEdit(label="Suffix 1",
                                              editText=RENDERER_SUFFIXES[0],
                                              toolTip=toolTip,
                                              labelRatio=2,
                                              editRatio=5)
        self.suffix2Txt = elements.StringEdit(label="Suffix 2",
                                              editText=RENDERER_SUFFIXES[3],
                                              toolTip=toolTip,
                                              labelRatio=2,
                                              editRatio=5)
        # Shader Swap Button ---------------------------------------
        tooltip = "Swap reassigns all shaders in the scene. Order does not matter. \n" \
                  "Any matching shaders will be swapped between suffix1 and suffix2 names \n" \
                  "Example Suffix One `ARN`, Suffix 2 `VP2`: \n" \
                  "    `gold_ARN` geo assignments will be swapped to the \n" \
                  "    `gold_VP2` shader if it exists"
        self.shaderSwapBtn = elements.styledButton("Swap Shader Toggle",
                                                   icon="invert",
                                                   toolTip=tooltip,
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
                                         spacing=uic.SREG)
        # Combo Row ---------------------------------------
        comboLayout = elements.hBoxLayout(spacing=uic.SREG)
        comboLayout.addWidget(self.quickSuffix1Combo)
        comboLayout.addWidget(self.quickSuffix2Combo)
        # Suffix Row ---------------------------------------
        suffixLayout = elements.hBoxLayout(spacing=uic.SREG)
        suffixLayout.addWidget(self.suffix1Txt)
        suffixLayout.addWidget(self.suffix2Txt)
        # Add To Main Layout ---------------------------------------
        mainLayout.addLayout(comboLayout)
        mainLayout.addLayout(suffixLayout)
        mainLayout.addWidget(self.shaderSwapBtn)
