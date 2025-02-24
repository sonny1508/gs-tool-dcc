""" ---------- Sculpting Toolbox UI (Multiple UI Modes) -------------


"""

from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.libs import iconlib
from zoo.libs.pyqt import uiconstants as uic, utils
from zoo.libs.pyqt.widgets import elements
from zoovendor.Qt import QtWidgets
from zoo.libs.maya.cmds.hotkeys import definedhotkeys
from zoo.apps.tooltips import modelingtooltips as tt

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1


class SculptingToolbox(toolsetwidget.ToolsetWidget):
    id = "sculptingToolbox"
    info = "Maya sculpt tools and hotkey trainer."
    uiData = {"label": "Sculpting Toolbox",
              "icon": "sculpting",
              "tooltip": "Maya sculpt tools and hotkey trainer.",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-sculpting-toolbox/"}

    # ------------------
    # STARTUP
    # ------------------

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
        self.uiConnections()

    def currentWidget(self):
        """ Currently active widget

        :return:
        :rtype: GuiAdvanced or GuiCompact
        """
        return super(SculptingToolbox, self).currentWidget()

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiAdvanced or GuiCompact]
        """
        return super(SculptingToolbox, self).widgets()

    # ------------------
    # LOGIC
    # ------------------

    def sculptToolMel(self):
        """Sets the Sculpt Tool"""
        definedhotkeys.sculptToolMel()

    def sculptToolKnifeMel(self):
        """Sets the Sculpt Tool"""
        definedhotkeys.sculptToolKnifeMel()

    def sculptToolDirectionalPinchMel(self):
        """Sets the Sculpt Tool and sets the v_directionalPinch_vdm.tif stamp"""
        definedhotkeys.sculptToolDirectionalPinchMel()

    def sculptToolEdgeMel(self):
        """Sets the Sculpt Tool and sets the v_edge_vdm.tif stamp"""
        definedhotkeys.sculptToolEdgeMel()

    def sculptToolEdgeMelFlip(self):
        """Sets the Sculpt Tool and sets the v_edge_vdm.tif stamp"""
        definedhotkeys.sculptToolEdgeMel(flipY=True)

    def sculptToolFoldMel(self):
        """Sets the Sculpt Tool and sets the v_fold_vdm.tif stamp"""
        definedhotkeys.sculptToolFoldMel()

    def sculptToolTubeMel(self):
        """Sets the Sculpt Tool and sets the v_tube_vdm.tif stamp"""
        definedhotkeys.sculptToolTubeMel()

    def smoothToolMel(self):
        """Sets the Sculpt Tool"""
        definedhotkeys.smoothToolMel()

    def relaxToolMel(self):
        """Sets the Sculpt Tool"""
        definedhotkeys.relaxToolMel()

    def grabToolMel(self):
        """Sets the Sculpt Tool"""
        definedhotkeys.grabToolMel()

    def pinchToolMel(self):
        """Sets the Sculpt Tool"""
        definedhotkeys.pinchToolMel()

    def flattenToolMel(self):
        """Sets the Sculpt Tool"""
        definedhotkeys.flattenToolMel()

    def sculptFalloffSurfaceVolumeMel(self):
        definedhotkeys.sculptFalloffSurfaceVolumeMel()

    def sculptFalloffSurfaceMel(self):
        definedhotkeys.sculptFalloffSurfaceMel()

    def sculptFalloffVolumeMel(self):
        definedhotkeys.sculptFalloffVolumeMel()

    def foamyToolMel(self):
        """Sets the Sculpt Tool"""
        definedhotkeys.foamyToolMel()

    def sprayToolMel(self):
        """Sets the Sculpt Tool"""
        definedhotkeys.sprayToolMel()

    def repeatToolMel(self):
        """Sets the Sculpt Tool"""
        definedhotkeys.repeatToolMel()

    def imprintToolMel(self):
        """Sets the Sculpt Tool"""
        definedhotkeys.imprintToolMel()

    def waxToolMel(self):
        """Sets the Sculpt Tool"""
        definedhotkeys.waxToolMel()

    def waxToolMelHardAlpha(self):
        """Sets the Wax Tool"""
        definedhotkeys.waxToolMelHardAlpha()

    def waxToolMelSquareAlpha(self):
        """Sets the Wax Tool with bw_strip.tif alpha"""
        definedhotkeys.waxToolMelSquareAlpha()

    def scrapeToolMel(self):
        """Sets the Sculpt Tool"""
        definedhotkeys.scrapeToolMel()

    def fillToolMel(self):
        """Sets the Sculpt Tool"""
        definedhotkeys.fillToolMel()

    def knifeToolMel(self):
        """Sets the Sculpt Tool"""
        definedhotkeys.knifeToolMel()

    def smearToolMel(self):
        """Sets the Sculpt Tool"""
        definedhotkeys.smearToolMel()

    def bulgeToolMel(self):
        """Sets the Sculpt Tool"""
        definedhotkeys.bulgeToolMel()

    def amplifyToolMel(self):
        """Sets the Sculpt Tool"""
        definedhotkeys.amplifyToolMel()

    def freezeToolMel(self):
        """Sets the Sculpt Tool"""
        definedhotkeys.freezeToolMel()

    def convertToFrozenToolMel(self):
        """Sets the Sculpt Tool"""
        definedhotkeys.convertToFrozenToolMel()

    def unfreezeToolMel(self):
        """Sets the Sculpt Tool"""
        definedhotkeys.unfreezeToolMel()

    def invertFreeze(self):
        """Sets the Sculpt Tool"""
        definedhotkeys.invertFreezeToolMel()

    def toggleToolSettings(self):
        """Sets the Sculpt Tool"""
        definedhotkeys.toggleToolSettings()

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        for widget in self.widgets():
            widget.waxBtn.clicked.connect(self.waxToolMelHardAlpha)
            widget.grabBtn.clicked.connect(self.grabToolMel)
            widget.sculptKnifeBtn.clicked.connect(self.sculptToolKnifeMel)
            widget.pinchBtn.clicked.connect(self.pinchToolMel)
            widget.sculptBtn.clicked.connect(self.sculptToolMel)
            widget.flattenBtn.clicked.connect(self.flattenToolMel)
            widget.freezeBtn.clicked.connect(self.freezeToolMel)
            widget.unfreezeBtn.clicked.connect(self.unfreezeToolMel)
            widget.invertFreezeBtn.clicked.connect(self.invertFreeze)
            widget.toggleToolSettingsBtn.clicked.connect(self.toggleToolSettings)
            # ------------------
            widget.knifeBtn.clicked.connect(self.knifeToolMel)
            widget.scrapeBtn.clicked.connect(self.scrapeToolMel)
            widget.fillBtn.clicked.connect(self.fillToolMel)
            widget.smearBtn.clicked.connect(self.smearToolMel)
            widget.bulgeBtn.clicked.connect(self.bulgeToolMel)
            widget.amplifyBtn.clicked.connect(self.amplifyToolMel)
            widget.foamyBtn.clicked.connect(self.foamyToolMel)
            widget.sprayBtn.clicked.connect(self.sprayToolMel)
            widget.repeatBtn.clicked.connect(self.repeatToolMel)
            widget.imprintBtn.clicked.connect(self.imprintToolMel)
            # RIGHT CLICKS -----------------------
            # Wax -----------------------
            waxIcon = iconlib.icon(":Wax", size=uic.MAYA_BTN_ICON_SIZE)
            widget.waxBtn.createMenuItem(text="Wax - Hard Edge Alpha (default)", icon=waxIcon,
                                         connection=self.waxToolMelHardAlpha)
            widget.waxBtn.createMenuItem(text="Wax Brush - No Alpha", icon=waxIcon,
                                         connection=self.waxToolMel)
            widget.waxBtn.createMenuItem(text="Wax - Square Alpha", icon=waxIcon,
                                         connection=self.waxToolMelHardAlpha)
            # Knife -----------------------
            sculptIcon = iconlib.icon(":Sculpt", size=uic.MAYA_BTN_ICON_SIZE)
            widget.sculptKnifeBtn.createMenuItem(text="Sculpt - Knife (default)", icon=sculptIcon,
                                                 connection=self.sculptToolKnifeMel)
            widget.sculptKnifeBtn.createMenuItem(text="Sculpt - No Alpha", icon=sculptIcon,
                                                 connection=self.sculptToolMel)
            widget.sculptKnifeBtn.createMenuItem(text="Sculpt - Pinch Alpha", icon=sculptIcon,
                                                 connection=self.sculptToolDirectionalPinchMel)
            widget.sculptKnifeBtn.createMenuItem(text="Sculpt - Fold Alpha", icon=sculptIcon,
                                                 connection=self.sculptToolFoldMel)
            widget.sculptKnifeBtn.createMenuItem(text="Sculpt - Tube Alpha", icon=sculptIcon,
                                                 connection=self.sculptToolTubeMel)
            widget.sculptKnifeBtn.createMenuItem(text="Sculpt - Edge Alpha", icon=sculptIcon,
                                                 connection=self.sculptToolEdgeMel)
            widget.sculptKnifeBtn.createMenuItem(text="Sculpt - Edge Alpha Flip", icon=sculptIcon,
                                                 connection=self.sculptToolEdgeMelFlip)
            # Freeze Mask -----------------------
            widget.freezeBtn.createMenuItem(text="Freeze Mask (Default)", icon=sculptIcon,
                                            connection=self.freezeToolMel)
            widget.freezeBtn.createMenuItem(text="Convert Selection To Frozen", icon=sculptIcon,
                                            connection=self.convertToFrozenToolMel)
        # Advanced Mode -----------------------
        self.advancedWidget.smoothBtn.clicked.connect(self.smoothToolMel)
        self.advancedWidget.relaxBtn.clicked.connect(self.relaxToolMel)
        self.advancedWidget.surfaceFalloffBtn.clicked.connect(self.sculptFalloffSurfaceMel)
        self.advancedWidget.volumeFalloffBtn.clicked.connect(self.sculptFalloffVolumeMel)


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
        toolTipDict = tt.sculptingToolbox()
        self.properties = properties
        # MAIN ----------------------------------------------------------------------------------
        # maya btn ---------------------------------------
        self.waxBtn = self.mayaBtn("Wax Hard (Right Click)", ":Wax", toolTipDict["wax"])
        # maya btn ---------------------------------------
        self.grabBtn = self.mayaBtn("Grab (Move)", ":Grab", toolTipDict["grab"])
        # maya btn ---------------------------------------
        self.sculptKnifeBtn = self.mayaBtn("Knife Sculpt (Right Click)", ":Sculpt", toolTipDict["knifeSculpt"])
        # maya btn ---------------------------------------
        self.pinchBtn = self.mayaBtn("Pinch", ":Pinch", toolTipDict["pinch"])
        # maya btn ---------------------------------------
        self.sculptBtn = self.mayaBtn("Sculpt", ":Sculpt", toolTipDict["sculpt"])
        # maya btn ---------------------------------------
        self.flattenBtn = self.mayaBtn("Flatten", ":Flatten", toolTipDict["flatten"])
        if uiMode == UI_MODE_ADVANCED:  # If compact mode then search all nodes
            # maya btn ---------------------------------------
            self.smoothBtn = self.mayaBtn("Smooth", ":Smooth", toolTipDict["smooth"])
            # maya btn ---------------------------------------
            self.relaxBtn = self.mayaBtn("Relax", ":Relax", toolTipDict["relax"])
        # maya btn ---------------------------------------
        self.freezeBtn = self.mayaBtn("Freeze Mask (Right Click)", ":Freeze", toolTipDict["freeze"])
        # maya btn ---------------------------------------
        self.unfreezeBtn = self.mayaBtn("Unfreeze", ":freezeSelected", toolTipDict["unfreeze"])
        # zoo btn ---------------------------------------
        self.toggleToolSettingsBtn = self.zooBtn("Toggle Tool Settings", "windowBrowser",
                                                 toolTipDict["toggleToolSettings"])
        if uiMode == UI_MODE_ADVANCED:
            # maya btn ---------------------------------------
            self.volumeFalloffBtn = self.mayaBtn("Falloff Volume", ":volumeSphere", toolTipDict["falloffVolume"])
            # maya btn ---------------------------------------
            self.surfaceFalloffBtn = self.mayaBtn("Falloff Surface", ":ghostingObjectTypeGeometry",
                                                  toolTipDict["falloffSurface"])
        # maya btn ---------------------------------------
        self.invertFreezeBtn = self.mayaBtn("Invert Freeze", ":Freeze", toolTipDict["invertFreeze"])
        # MISC ----------------------------------------------------------------------------------
        # maya btn ---------------------------------------
        self.knifeBtn = self.mayaBtn("Knife (Default)", ":Knife", toolTipDict["knife"])
        # maya btn ---------------------------------------
        self.scrapeBtn = self.mayaBtn("Scrape", ":Scrape", toolTipDict["scrape"])
        # maya btn ---------------------------------------
        self.fillBtn = self.mayaBtn("Fill", ":Fill", toolTipDict["fill"])
        # maya btn ---------------------------------------
        self.smearBtn = self.mayaBtn("Smear", ":Smear", toolTipDict["smear"])
        # maya btn ---------------------------------------
        self.bulgeBtn = self.mayaBtn("Bulge", ":Bulge", toolTipDict["bulge"])
        # maya btn ---------------------------------------
        self.amplifyBtn = self.mayaBtn("Amplify", ":Amplify", toolTipDict["amplify"])
        # maya btn ---------------------------------------
        self.foamyBtn = self.mayaBtn("Foamy", ":Foamy", toolTipDict["foamy"])
        # maya btn ---------------------------------------
        self.sprayBtn = self.mayaBtn("Spray", ":Spray", toolTipDict["spray"])
        # maya btn ---------------------------------------
        self.repeatBtn = self.mayaBtn("Repeat", ":Repeat", toolTipDict["repeat"])
        # maya btn ---------------------------------------
        self.imprintBtn = self.mayaBtn("Imprint", ":Imprint", toolTipDict["imprint"])

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
        mainSulptLayout = elements.GridLayout(spacing=uic.SPACING, margins=(uic.SREG, uic.SSML, uic.SREG, 0))
        row = 0
        mainSulptLayout.addWidget(self.waxBtn, row, 0)
        mainSulptLayout.addWidget(self.grabBtn, row, 1)
        row += 1
        mainSulptLayout.addWidget(self.sculptKnifeBtn, row, 0)
        mainSulptLayout.addWidget(self.pinchBtn, row, 1)
        row += 1
        mainSulptLayout.addWidget(self.sculptBtn, row, 0)
        mainSulptLayout.addWidget(self.flattenBtn, row, 1)
        row += 1
        mainSulptLayout.addWidget(self.freezeBtn, row, 0)
        mainSulptLayout.addWidget(self.unfreezeBtn, row, 1)
        row += 1
        mainSulptLayout.addWidget(self.invertFreezeBtn, row, 0)
        mainSulptLayout.addWidget(self.toggleToolSettingsBtn, row, 1)
        # Grid Layout -----------------------------
        miscLayout = elements.GridLayout(spacing=uic.SPACING, margins=(uic.SREG, uic.SSML, uic.SREG, 0))
        row = 0
        miscLayout.addWidget(self.fillBtn, row, 0)
        miscLayout.addWidget(self.scrapeBtn, row, 1)
        row += 1
        miscLayout.addWidget(self.knifeBtn, row, 0)
        miscLayout.addWidget(self.smearBtn, row, 1)
        row += 1
        miscLayout.addWidget(self.bulgeBtn, row, 0)
        miscLayout.addWidget(self.amplifyBtn, row, 1)
        row += 1
        miscLayout.addWidget(self.foamyBtn, row, 0)
        miscLayout.addWidget(self.sprayBtn, row, 1)
        row += 1
        miscLayout.addWidget(self.repeatBtn, row, 0)
        miscLayout.addWidget(self.imprintBtn, row, 1)
        miscLayout.setColumnStretch(0, 1)
        miscLayout.setColumnStretch(1, 1)

        # Sculpting Main -------------------------------------
        mainCollapsable = elements.CollapsableFrameThin("Main Sculpting ", collapsed=False)
        mainCollapsable.hiderLayout.addLayout(mainSulptLayout)
        mainCollapsable.toggled.connect(toolsetWidget.treeWidget.updateTree)
        mainCollapsableLayout = elements.vBoxLayout(margins=(0, 0, 0, 0))  # adds top margin above title
        mainCollapsableLayout.addWidget(mainCollapsable)

        # Sculpting Misc -------------------------------------
        miscCollapsable = elements.CollapsableFrameThin("Misc Sculpting", collapsed=True)
        miscCollapsable.hiderLayout.addLayout(miscLayout)
        miscCollapsable.toggled.connect(toolsetWidget.treeWidget.updateTree)
        miscCollapseLayout = elements.vBoxLayout(margins=(0, 0, 0, 0))  # adds top margin above title
        miscCollapseLayout.addWidget(miscCollapsable)

        # Add To Main Layout ---------------------------------------
        mainLayout.addLayout(mainCollapsableLayout)
        mainLayout.addLayout(miscCollapseLayout)


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
        # Grid Layout -----------------------------
        mainSulptLayout = elements.GridLayout(spacing=uic.SPACING, margins=(uic.SREG, uic.SSML, uic.SREG, 0))
        row = 0
        mainSulptLayout.addWidget(self.waxBtn, row, 0)
        mainSulptLayout.addWidget(self.grabBtn, row, 1)
        row += 1
        mainSulptLayout.addWidget(self.sculptKnifeBtn, row, 0)
        mainSulptLayout.addWidget(self.pinchBtn, row, 1)
        row += 1
        mainSulptLayout.addWidget(self.sculptBtn, row, 0)
        mainSulptLayout.addWidget(self.flattenBtn, row, 1)
        row += 1
        mainSulptLayout.addWidget(self.smoothBtn, row, 0)
        mainSulptLayout.addWidget(self.relaxBtn, row, 1)
        row += 1
        mainSulptLayout.addWidget(self.freezeBtn, row, 0)
        mainSulptLayout.addWidget(self.unfreezeBtn, row, 1)
        row += 1
        mainSulptLayout.addWidget(self.invertFreezeBtn, row, 0)
        mainSulptLayout.addWidget(self.toggleToolSettingsBtn, row, 1)
        row += 1
        mainSulptLayout.addWidget(self.surfaceFalloffBtn, row, 0)
        mainSulptLayout.addWidget(self.volumeFalloffBtn, row, 1)

        # Grid Layout -----------------------------
        miscLayout = elements.GridLayout(spacing=uic.SPACING, margins=(uic.SREG, uic.SSML, uic.SREG, 0))
        row = 0
        miscLayout.addWidget(self.fillBtn, row, 0)
        miscLayout.addWidget(self.scrapeBtn, row, 1)
        row += 1
        miscLayout.addWidget(self.knifeBtn, row, 0)
        miscLayout.addWidget(self.smearBtn, row, 1)
        row += 1
        miscLayout.addWidget(self.bulgeBtn, row, 0)
        miscLayout.addWidget(self.amplifyBtn, row, 1)
        row += 1
        miscLayout.addWidget(self.foamyBtn, row, 0)
        miscLayout.addWidget(self.sprayBtn, row, 1)
        row += 1
        miscLayout.addWidget(self.repeatBtn, row, 0)
        miscLayout.addWidget(self.imprintBtn, row, 1)
        miscLayout.setColumnStretch(0, 1)
        miscLayout.setColumnStretch(1, 1)

        # Sculpting Main -------------------------------------
        mainCollapsable = elements.CollapsableFrameThin("Main Sculpting ", collapsed=False)
        mainCollapsable.hiderLayout.addLayout(mainSulptLayout)
        mainCollapsable.toggled.connect(toolsetWidget.treeWidget.updateTree)
        mainCollapsableLayout = elements.vBoxLayout(margins=(0, 0, 0, 0))  # adds top margin above title
        mainCollapsableLayout.addWidget(mainCollapsable)

        # Sculpting Misc -------------------------------------
        miscCollapsable = elements.CollapsableFrameThin("Misc Sculpting", collapsed=True)
        miscCollapsable.hiderLayout.addLayout(miscLayout)
        miscCollapsable.toggled.connect(toolsetWidget.treeWidget.updateTree)
        miscCollapseLayout = elements.vBoxLayout(margins=(0, 0, 0, 0))  # adds top margin above title
        miscCollapseLayout.addWidget(miscCollapsable)

        # Add To Main Layout ---------------------------------------
        mainLayout.addLayout(mainCollapsableLayout)
        mainLayout.addLayout(miscCollapseLayout)
