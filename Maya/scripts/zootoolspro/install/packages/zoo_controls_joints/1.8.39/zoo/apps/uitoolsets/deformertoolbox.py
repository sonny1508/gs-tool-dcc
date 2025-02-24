""" ---------- Deformer Toolbox UI (Multiple UI Modes) -------------


"""

from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.libs import iconlib
from zoo.libs.pyqt import uiconstants as uic, utils
from zoo.libs.pyqt.widgets import elements
from zoovendor.Qt import QtWidgets
from zoo.apps.tooltips import deformertooltips as tt

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1


class DeformerToolbox(object):  # toolsetwidget.ToolsetWidget
    id = "deformerToolbox"
    info = "Maya deformer tools and hotkey trainer."
    uiData = {"label": "Deformer Toolbox",
              "icon": "twistDeform",
              "tooltip": "Maya deformer tools and hotkey trainer.",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-deformer-toolbox/"}

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
        return super(DeformerToolbox, self).currentWidget()

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiAdvanced or GuiCompact]
        """
        return super(DeformerToolbox, self).widgets()

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
        toolTipDict = tt.deformerToolbox()
        self.properties = properties
        # MAIN ----------------------------------------------------------------------------------
        # Wire Deformer - maya btn ---------------------------------------
        self.blendshapeBtn = self.mayaBtn("Blendshape UI (R-Click)", ":blendShape", toolTipDict["blendShape"])
        # Create Cluster - maya btn ---------------------------------------
        self.deltaMushBtn = self.mayaBtn("Delta Mush (R-Click)", ":deltaMush", toolTipDict["deltaMush"])
        # Wire Deformer - maya btn ---------------------------------------
        self.wireDeformerBtn = self.mayaBtn("Wire Deformer (R-Click)", ":wire", toolTipDict["wireDeformer"])
        # Create Cluster - maya btn ---------------------------------------
        self.createClusterBtn = self.mayaBtn("Create Cluster (R-Click)", ":cluster", toolTipDict["createCluster"])
        # Controls On Curve - zoo btn ---------------------------------------
        self.controlsOnCurveClusterBtn = self.zooBtn("Controls On Curve (R-Click)", "clusterCurve",
                                                     toolTipDict["controlsOnCurve"])
        # Create Cluster - maya btn ---------------------------------------
        self.createLatticeBtn = self.mayaBtn("Create Lattice (R-Click)", ":out_lattice",
                                             toolTipDict["createLattice"])
        # Soft Modifier - maya btn ---------------------------------------
        self.softModifierBtn = self.mayaBtn("Soft Modifier (R-Click)", ":softMod", toolTipDict["softModifier"])
        # Bend Deformer - maya btn ---------------------------------------
        self.bendDeformerBtn = self.mayaBtn("Bend Deformer (R-Click)", ":bendNLD", toolTipDict["bendDeformer"])
        # Wrap Deformer - maya btn ---------------------------------------
        self.wrapDeformerBtn = self.mayaBtn("Wrap Deformer (R-Click)", ":wrap", toolTipDict["wrapDeformer"])
        # Proximity Wrap - maya btn ---------------------------------------
        self.proximityWrap = self.mayaBtn("Proximity Wrap (R-Click)", ":proximityWrap",
                                          toolTipDict["proximityWrap"])
        # Sculpt Deformer - maya btn ---------------------------------------
        self.sculptDeformerBtn = self.mayaBtn("Sculpt Deformer (R-Click)", ":sculpt", toolTipDict["sculptDeformer"])
        # Twist Deformer - maya btn ---------------------------------------
        self.twistDeformerBtn = self.mayaBtn("Twist Deformer (R-Click)", ":twistNLD", toolTipDict["twistDeformer"])
        # Wave Deformer - maya btn ---------------------------------------
        self.waveDeformerBtn = self.mayaBtn("Wave Deformer (R-Click)", ":waveNLD", toolTipDict["waveDeformer"])
        # Flare Deformer - maya btn ---------------------------------------
        self.flareDeformerBtn = self.mayaBtn("Flare Deformer (R-Click)", ":flareNLD", toolTipDict["flareDeformer"])
        # Jiggle Deformer - maya btn ---------------------------------------
        self.jiggleDeformer = self.mayaBtn("Jiggle Deformer (R-Click)", ":flareNLD", toolTipDict["jiggleDeformer"])
        # Sine Deformer - maya btn ---------------------------------------
        self.sineDeformer = self.mayaBtn("Sine Deformer (R-Click)", ":flareNLD", toolTipDict["sineDeformer"])

        # curve warp
        # squash deformer
        # shrink wrap
        # wrinkle
        # tension
        # solidify

        # paint weights
        # export/import weights



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
        mainDeformerLayout = elements.GridLayout(spacing=uic.SPACING, margins=(uic.SREG, uic.SSML, uic.SREG, 0))
        row = 0
        mainDeformerLayout.addWidget(self.blendshapeBtn, row, 0)
        mainDeformerLayout.addWidget(self.deltaMushBtn, row, 1)
        row += 1
        mainDeformerLayout.addWidget(self.wireDeformerBtn, row, 0)
        mainDeformerLayout.addWidget(self.createClusterBtn, row, 1)
        row += 1
        mainDeformerLayout.addWidget(self.controlsOnCurveClusterBtn, row, 0)
        mainDeformerLayout.addWidget(self.createLatticeBtn, row, 1)
        row += 1
        mainDeformerLayout.addWidget(self.softModifierBtn, row, 0)
        mainDeformerLayout.addWidget(self.bendDeformerBtn, row, 1)
        row += 1
        mainDeformerLayout.addWidget(self.wrapDeformerBtn, row, 0)
        mainDeformerLayout.addWidget(self.proximityWrap, row, 1)
        row += 1
        mainDeformerLayout.addWidget(self.sculptDeformerBtn, row, 0)
        mainDeformerLayout.addWidget(self.twistDeformerBtn, row, 1)
        row += 1
        mainDeformerLayout.addWidget(self.waveDeformerBtn, row, 0)
        mainDeformerLayout.addWidget(self.flareDeformerBtn, row, 1)
        row += 1
        mainDeformerLayout.addWidget(self.jiggleDeformer, row, 0)
        mainDeformerLayout.addWidget(self.sineDeformer, row, 1)

        mainDeformerLayout.setColumnStretch(0, 1)
        mainDeformerLayout.setColumnStretch(1, 1)

        # Add To Main Layout ---------------------------------------
        mainLayout.addLayout(mainDeformerLayout)


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
