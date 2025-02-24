""" ---------- Blendshape Toolbox UI (Multiple UI Modes) -------------


"""

from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.libs import iconlib
from zoo.libs.pyqt import uiconstants as uic, utils
from zoo.libs.pyqt.widgets import elements
from zoovendor.Qt import QtWidgets
from zoo.apps.tooltips import deformertooltips as tt

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1


class BlendshapeToolbox(object):  # toolsetwidget.ToolsetWidget
    id = "blendshapeToolbox"
    info = "Maya blendshape tools and hotkey trainer."
    uiData = {"label": "Blendshape Toolbox",
              "icon": "save",
              "tooltip": "Maya blendshape tools and hotkey trainer.",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-blendshape-toolbox/"}

    # ------------------
    # STARTUP
    # ------------------

    def contents(self):
        """The UI Modes to build, compact, medium and or advanced """
        return [self.initCompactWidget()]  # self.initAdvancedWidget()

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
        self.uiConnections()

    def currentWidget(self):
        """ Currently active widget

        :return:
        :rtype: GuiAdvanced or GuiCompact
        """
        return super(BlendshapeToolbox, self).currentWidget()

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiAdvanced or GuiCompact]
        """
        return super(BlendshapeToolbox, self).widgets()

    # ------------------
    # LOGIC
    # ------------------

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        for widget in self.widgets():
            pass
            # RIGHT CLICKS -----------------------
            # Wax -----------------------
            """waxIcon = iconlib.icon(":Wax", size=uic.MAYA_BTN_ICON_SIZE)
            widget.waxBtn.createMenuItem(text="Wax - Hard Edge Alpha (default)", icon=waxIcon,
                                         connection=self.waxToolMelHardAlpha)"""


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
        self.parent = parent
        toolTipDict = tt.blendshapeToolbox()
        self.properties = properties
        # MAIN ----------------------------------------------------------------------------------
        # maya btn ---------------------------------------
        self.xxxBtn = self.mayaBtn("Soft Modifier", ":xxx", toolTipDict["xxx"])

    def zooBtn(self, txt, icon, toolTip):
        """Regular aligned button with Zoo icon"""
        return elements.leftAlignedButton(txt,
                                          icon=iconlib.icon(icon,
                                                            size=utils.dpiScale(20)),
                                          toolTip=toolTip,
                                          parent=self.parent)

    def mayaBtn(self, txt, icon, toolTip):
        """Regular aligned button with a maya icon"""
        iconSize = utils.dpiScale(uic.MAYA_BTN_ICON_SIZE)
        return elements.leftAlignedButton(txt,
                                          icon=iconlib.icon(icon,
                                                            size=iconSize),
                                          padding=uic.MAYA_BTN_PADDING,
                                          toolTip=toolTip, parent=self.parent)


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
        # Grid Layout -----------------------------
        mainBlendshapeLayout = elements.GridLayout(spacing=uic.SPACING, margins=(uic.SREG, uic.SSML, uic.SREG, 0))
        row = 0
        mainBlendshapeLayout.addWidget(self.xxx, row, 0)
        mainBlendshapeLayout.addWidget(self.xxx, row, 1)

        mainBlendshapeLayout.setColumnStretch(0, 1)
        mainBlendshapeLayout.setColumnStretch(1, 1)

        # Add To Main Layout ---------------------------------------
        mainLayout.addLayout(mainBlendshapeLayout)


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
        pass
