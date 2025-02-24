from zoovendor.Qt import QtWidgets, QtCore

from zoo.libs.utils import output
from zoo.preferences.interfaces import coreinterfaces

from maya import cmds
from zoo.libs.maya.utils import mayaenv
from zoo.libs.maya.cmds.modeling import mirror

from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements
from zoo.apps.tooltips import modelingtooltips as tt

# Dots Menu
from zoo.libs.pyqt.widgets.iconmenu import IconMenuButton
from zoo.libs import iconlib
from zoo.libs.pyqt import utils

MAYA_VERSION = mayaenv.mayaVersion()  # whole numbers (int) 2020 etc
UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1
DIRECTION_LIST = ["+", "-"]
SYMMETRY_LIST = ["World X", "World Y", "World Z", "Object X", "Object Y", "Object Z"]
SPACE_LIST = ["World", "Object"]
MIRROR_LIST = ["+X to -X", "-X to +X", "+Y to -Y", "-Y to +Y", "+Z to -Z", "-Z to +Z"]

ATTR_MIRROR_AXIS = 0
ATTR_DIRECTION = 0
ATTR_MERGE_THRESHOLD = 0.001
ATTR_SMOOTH_ANGLE = 120.00
ATTR_DELETE_HISTORY = False
ATTR_FORCE_SMOOTH_ALL = False


class ZooMirrorGeo(toolsetwidget.ToolsetWidget):
    id = "zooMirrorGeo"
    info = "Modeling mirror geometry tool."
    uiData = {"label": "Mirror Toolbox",
              "icon": "mirrorGeo",
              "tooltip": "Modeling mirror geometry tool.",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-zoo-mirror-geo/"
              }

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
        # not used
        self.advancedWidget = GuiAdvanced(parent=self, properties=self.properties, toolsetWidget=self)
        return self.advancedWidget

    def postContentSetup(self):
        """Last of the initialize code"""
        self.uiConnections()

    def currentWidget(self):
        """Returns the current widget class eg. self.compactWidget or self.advancedWidget

        Over ridden class
        :rtype: GuiWidgets
        """
        return super(ZooMirrorGeo, self).currentWidget()

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiAdvanced or GuiCompact]
        """
        return super(ZooMirrorGeo, self).widgets()

    # ------------------
    # POPUP
    # ------------------

    def resetFreezePopup(self, obj):
        """The popup window asking the user if they'd like to remove the freeze.
        """
        message = "Object `{}'s` transforms have been frozen, and will not mirror intuitively.  \n\n" \
                  "Remove the frozen offset? (recommended)".format(obj)
        return elements.MessageBox.showOK(title="Remove Freeze?", message=message)  # None will parent to Maya

    # ------------------
    # LOGIC
    # ------------------

    def resetSettings(self):
        """Resets all settings back to the default values

        :return:
        :rtype:
        """
        self.properties.symmetryCombo.value = ATTR_MIRROR_AXIS
        self.properties.directionCombo.value = ATTR_DIRECTION
        self.properties.mergeThresholdFloat.value = ATTR_MERGE_THRESHOLD
        self.properties.smoothAngleFloat.value = ATTR_SMOOTH_ANGLE
        self.properties.deleteHistoryCheckBox.value = ATTR_DELETE_HISTORY
        self.properties.smoothAngleCheckbox.value = ATTR_FORCE_SMOOTH_ALL
        self.updateFromProperties()

    # ------------------
    # LOGIC
    # ------------------

    def removeFreezeSelected(self, popupWarn=False):
        """Checks if the selected objects are frozen and if so asks the user if they'd like to remove the freeze.
        """
        objList = cmds.ls(selection=True, exactType="transform")
        if not objList:
            output.displayWarning("No objects selected, must be a polygon object")
            return
        for obj in objList:
            frozen = mirror.checkForFrozenGeometry(obj)
            if frozen:
                if popupWarn:
                    result = self.resetFreezePopup(obj)
                    if not result:
                        cmds.select(objList, replace=True)
                        return
                mirror.removeFreezeSelected(obj)
        cmds.select(objList, replace=True)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def removeFreezeSelectedUndo(self):
        self.removeFreezeSelected(popupWarn=False)
        objSel = cmds.ls(selection=True)
        if not objSel:
            return
        output.displayInfo("Success Freeze removed: {}".format(objSel))

    @toolsetwidget.ToolsetWidget.undoDecorator
    def symmetrize(self):
        """Uninstance all instances in the scene
        """
        mirror.symmetrize()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def flip(self):
        """Uninstance all instances in the scene
        """
        mirror.flip()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def toggleSymmetry(self):
        """Mirrors with maya's polygon mirror with added steps for centering the selected line
        """
        symmetryMode = SYMMETRY_LIST[self.properties.symmetryCombo.value]
        space = str.lower(symmetryMode.split(" ")[0])
        if space == "object":
            self.removeFreezeSelected(popupWarn=True)
        symState = mirror.symmetryToggle(message=False)
        mirror.changeSymmetryMode(symmetryMode=symmetryMode)
        if symState:
            symState = "Off"
        else:
            symState = "On"
        output.displayInfo("Symmetry mode is `{}`, {}".format(symState, symmetryMode))

    @toolsetwidget.ToolsetWidget.undoDecorator
    def symmetryComboChanged(self, symmetryIndex):
        """Changes the symmetry mode

        :param symmetryIndex: Index from the Symmetry combo box (not used)
        :type symmetryIndex: int
        """
        symmetryMode = SYMMETRY_LIST[self.properties.symmetryCombo.value]
        direction = DIRECTION_LIST[self.properties.directionCombo.value]
        mirror.changeSymmetryMode(symmetryMode=symmetryMode, message=False)
        output.displayInfo("Symmetry plane set to `{}`, direction is `{}`".format(symmetryMode, direction))

    @toolsetwidget.ToolsetWidget.undoDecorator
    def mirrorPolygon(self):
        """Mirrors with maya's polygon mirror with added steps for centering the selected line
        """
        symmetryMode = SYMMETRY_LIST[self.properties.symmetryCombo.value]
        direction = DIRECTION_LIST[self.properties.directionCombo.value]
        space = str.lower(symmetryMode.split(" ")[0])
        axis = str.lower(symmetryMode.split(" ")[-1])
        direction = 1 if direction == '+' else -1
        if space == "object":
            self.removeFreezeSelected(popupWarn=True)
        mirror.mirrorPolyEdgeToZero(smoothEdges=self.properties.smoothAngleCheckbox.value,
                                    deleteHistory=self.properties.deleteHistoryCheckBox.value,
                                    smoothAngle=self.properties.smoothAngleFloat.value,
                                    mergeThreshold=self.properties.mergeThresholdFloat.value,
                                    mirrorAxis=axis,
                                    direction=direction,
                                    space=space)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def instanceMirror(self):
        """Mirrors with grp instance and negative scale
        """
        symmetryMode = SYMMETRY_LIST[self.properties.symmetryCombo.value]
        direction = DIRECTION_LIST[self.properties.directionCombo.value]
        space = str.lower(symmetryMode.split(" ")[0])
        axis = str.lower(symmetryMode.split(" ")[-1])
        mirror.instanceMirror(mirrorAxis=axis, space=space, direction=direction)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def uninstanceAll(self):
        """Uninstance all instances in the scene
        """
        mirror.uninstanceMirrorInstacesAll()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def uninstanceSelected(self):
        """Uninstance selected instances
        """
        mirror.uninstanceMirrorInstanceSel()

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        for w in self.widgets():
            w.mirrorPolygonBtn.clicked.connect(self.mirrorPolygon)
            w.mirrorInstanceBtn.clicked.connect(self.instanceMirror)
            w.toggleSymmetryBtn.clicked.connect(self.toggleSymmetry)
            w.uninstanceAllBtn.clicked.connect(self.uninstanceAll)
            w.uninstanceSelBtn.clicked.connect(self.uninstanceSelected)
            w.symmetrizeBtn.clicked.connect(self.symmetrize)
            w.flipBtn.clicked.connect(self.flip)
            w.symmetryCombo.currentIndexChanged.connect(self.symmetryComboChanged)
            w.directionCombo.currentIndexChanged.connect(self.symmetryComboChanged)
            # Dots Menu
            w.dotsMenu.resetSettings.connect(self.resetSettings)
        self.advancedWidget.removeFreezeBtn.clicked.connect(self.removeFreezeSelectedUndo)


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
        toolTipDict = tt.mirrorToolbox()
        # Symmetry Combo ---------------------------------------
        self.symmetryCombo = elements.ComboBoxRegular(label="Mirror",
                                                      items=SYMMETRY_LIST,
                                                      labelRatio=1,
                                                      boxRatio=2,
                                                      toolTip=toolTipDict["symmetryCombo"])
        # Directional Combo ---------------------------------------
        self.directionCombo = elements.ComboBoxRegular(label="Direction",
                                                       items=DIRECTION_LIST,
                                                       labelRatio=1,
                                                       boxRatio=2,
                                                       toolTip=toolTipDict["directionCombo"])
        # Dots Menu -------------------------------------------
        self.dotsMenu = DotsMenu()
        # Zoo Mirror Polygon ---------------------------------------
        self.toggleSymmetryBtn = elements.AlignedButton("Toggle Sym Mode",
                                                        icon="symmetryMode",
                                                        toolTip=toolTipDict["toggleSymmetryMode"])
        # Symmetrize Polygon ---------------------------------------
        self.symmetrizeBtn = elements.AlignedButton("Symmetrize Mesh",
                                                    icon="mirrorGeo",
                                                    toolTip=toolTipDict["symmetrize"])
        # Flip Polygon ---------------------------------------
        self.flipBtn = elements.AlignedButton("Flip Mesh",
                                              icon="mirrorGeo",
                                              toolTip=toolTipDict["flip"])
        if MAYA_VERSION < 2019:  # only in 2019 and above
            self.symmetrizeBtn.hide()
            self.flipBtn.hide()
        # Zoo Mirror Polygon ---------------------------------------
        if uiMode == UI_MODE_COMPACT:  # button is left aligned
            self.mirrorPolygonBtn = elements.AlignedButton("Zoo Mirror Polygon",
                                                           icon="mirrorGeo",
                                                           toolTip=toolTipDict["zooMirrorPolygon"])
        elif uiMode == UI_MODE_ADVANCED:  # button is centered
            self.mirrorPolygonBtn = elements.styledButton("Zoo Mirror Polygon",
                                                          icon="mirrorGeo",
                                                          toolTip=toolTipDict["zooMirrorPolygon"],
                                                          style=uic.BTN_DEFAULT)
        # Instance Mirror Button ---------------------------------------
        if uiMode == UI_MODE_COMPACT:  # button is left aligned
            self.mirrorInstanceBtn = elements.AlignedButton("Mirror Obj Instance",
                                                            icon="symmetryTri",
                                                            toolTip=toolTipDict["instanceMirror"])
        elif uiMode == UI_MODE_ADVANCED:  # button is centered
            self.mirrorInstanceBtn = elements.styledButton("Mirror Obj Instance",
                                                           icon="symmetryTri",
                                                           toolTip=toolTipDict["instanceMirror"],
                                                           style=uic.BTN_DEFAULT)
        # Remove Instance All Button ---------------------------------------
        if uiMode == UI_MODE_ADVANCED:
            self.uninstanceAllBtn = elements.AlignedButton("Uninstance All",
                                                           icon="crossXFat",
                                                           toolTip=toolTipDict["removeAllInstances"])
        else:
            self.uninstanceAllBtn = elements.AlignedButton("All",
                                                           icon="crossXFat",
                                                           toolTip=toolTipDict["removeAllInstances"])
        # Remove Instance Selected Button ---------------------------------------
        if uiMode == UI_MODE_ADVANCED:
            self.uninstanceSelBtn = elements.AlignedButton("Uninstance Selected",
                                                           icon="crossXFat",
                                                           toolTip=toolTipDict["removeSelectedInstances"])
        else:
            self.uninstanceSelBtn = elements.AlignedButton("Sel",
                                                           icon="crossXFat",
                                                           toolTip=toolTipDict["removeSelectedInstances"])
        if uiMode == UI_MODE_ADVANCED:
            # Symmetry Polygon Title Divider -------------------------------------------------------
            self.symmetryTitle = elements.LabelDivider(text="Symmetry Mode (Non Destructive)")
            # RemoveFreeze1 Button -------------------------------------------------------
            self.removeFreezeBtn = elements.AlignedButton("Remove Freeze",
                                                          icon="freezeSnowFlake",
                                                          toolTip=toolTipDict["removeFreeze"])
            # Mirror Polygon Title Divider -------------------------------------------------------
            self.mirrorPolygonTitle = elements.LabelDivider(text="Mirror Polygon (Delete/Rebuild)")
            # Merge threshold ---------------------------------------
            self.mergeThresholdFloat = elements.FloatEdit(label="Merge Threshold",
                                                          editText="0.001",
                                                          toolTip=toolTipDict["mergeThreshold"],
                                                          labelRatio=20,
                                                          editRatio=15)
            # Smooth Angle ---------------------------------------
            self.smoothAngleFloat = elements.FloatEdit(label="Smooth Angle",
                                                       editText="120.0",
                                                       toolTip=toolTipDict["smoothAngle"],
                                                       labelRatio=20,
                                                       editRatio=15)
            self.smoothAngleCheckbox = elements.CheckBox(label="Force Smooth All",
                                                         checked=False,
                                                         toolTip=toolTipDict["smoothAngle"])
            # Delete History Check Box ---------------------------------------
            self.deleteHistoryCheckBox = elements.CheckBox(label="Delete History",
                                                           checked=False,
                                                           toolTip=toolTipDict["deleteHistory"])
            # Mirror Polygon Title Divider -----------------------------------------------------------
            self.instanceMirrorTitle = elements.LabelDivider(text="Instance Mirror (Separate Objects)")


class DotsMenu(IconMenuButton):
    menuIcon = "menudots"
    resetSettings = QtCore.Signal()
    _iconColor = None

    def __init__(self, parent=None, networkEnabled=False):
        """Builds the dots menu with > Reset Settings
        """
        super(DotsMenu, self).__init__(parent=parent)
        self.networkEnabled = networkEnabled
        if DotsMenu._iconColor is None:
            DotsMenu._iconColor = coreinterfaces.coreInterface().ICON_PRIMARY_COLOR
        self.setIconByName(self.menuIcon, size=16, colors=DotsMenu._iconColor)
        self.setMenuAlign(QtCore.Qt.AlignRight)
        self.setToolTip("File menu. Zoo Mirror Poly")
        self.disableActionList = list()
        # Build the static menu
        # Reset To Defaults --------------------------------------
        reloadIcon = iconlib.iconColorized("reload2", utils.dpiScale(16))
        self.addAction("Reset Settings", connect=lambda: self.resetSettings.emit(), icon=reloadIcon)


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
        mainLayout = elements.vBoxLayout(self,
                                         margins=(uic.WINSIDEPAD, uic.WINBOTPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SPACING)
        # Direction Bots Menu Layout ---------------------------------------
        dirDotsLayout = elements.hBoxLayout(spacing=uic.SVLRG)
        dirDotsLayout.addWidget(self.directionCombo, 6)
        dirDotsLayout.addWidget(self.dotsMenu, 1)
        # Options Layout ---------------------------------------
        optionsLayout = elements.hBoxLayout(spacing=uic.SVLRG)
        optionsLayout.addWidget(self.symmetryCombo, 1)
        optionsLayout.addLayout(dirDotsLayout, 1)
        # Sym Button Layout ---------------------------------------
        symFlipLayout = elements.hBoxLayout(spacing=uic.SPACING)
        symFlipLayout.addWidget(self.symmetrizeBtn, 1)
        symFlipLayout.addWidget(self.flipBtn, 1)
        # Poly Mirror Sym Button Layout ---------------------------------------
        polMSymLayout = elements.hBoxLayout(spacing=uic.SPACING)
        polMSymLayout.addWidget(self.mirrorPolygonBtn, 1)
        polMSymLayout.addWidget(self.toggleSymmetryBtn, 1)
        # Remove Instance Layout ---------------------------------------
        uninstanceLayout = elements.hBoxLayout(spacing=uic.SPACING)
        uninstanceLayout.addWidget(self.uninstanceAllBtn, 1)
        uninstanceLayout.addWidget(self.uninstanceSelBtn, 1)
        # Instance Layout ---------------------------------------
        instanceLayout = elements.hBoxLayout(spacing=uic.SPACING)
        instanceLayout.addWidget(self.mirrorInstanceBtn, 1)
        instanceLayout.addLayout(uninstanceLayout, 1)
        # Add To Main Layout ---------------------------------------
        mainLayout.addLayout(optionsLayout)
        mainLayout.addLayout(symFlipLayout)
        mainLayout.addLayout(polMSymLayout)
        mainLayout.addLayout(instanceLayout)


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
        mainLayout = elements.vBoxLayout(self,
                                         margins=(uic.WINSIDEPAD, uic.WINBOTPAD, uic.WINSIDEPAD, uic.SVLRG),
                                         spacing=uic.SPACING)
        # Direction Bots Menu Layout ---------------------------------------
        dirDotsLayout = elements.hBoxLayout(spacing=uic.SVLRG)
        dirDotsLayout.addWidget(self.directionCombo, 6)
        dirDotsLayout.addWidget(self.dotsMenu, 1)
        # Options Layout ---------------------------------------
        optionsLayout = elements.hBoxLayout(margins=(0, 0, 0, uic.SREG), spacing=uic.SVLRG)
        optionsLayout.addWidget(self.symmetryCombo, 1)
        optionsLayout.addLayout(dirDotsLayout, 1)
        # Sym Flip Button Layout ---------------------------------------
        symFlipLayout = elements.hBoxLayout(spacing=uic.SPACING)
        symFlipLayout.addWidget(self.symmetrizeBtn, 1)
        symFlipLayout.addWidget(self.flipBtn, 1)
        # Symmetry Mode Layout ---------------------------------------
        symmetryLayout = elements.hBoxLayout(margins=(0, 0, 0, uic.SREG), spacing=uic.SPACING)
        symmetryLayout.addWidget(self.removeFreezeBtn)
        symmetryLayout.addWidget(self.toggleSymmetryBtn)
        # Merge/Direction Layout ---------------------------------------
        mergeDirectionLayout = elements.hBoxLayout(margins=(uic.SREG, 0, uic.SREG, 0),
                                                   spacing=uic.SVLRG)
        mergeDirectionLayout.addWidget(self.mergeThresholdFloat, 10)
        mergeDirectionLayout.addWidget(self.deleteHistoryCheckBox, 6)
        # Smooth/History Layout ---------------------------------------
        smoothSpaceLayout = elements.hBoxLayout(margins=(uic.SREG, 0, uic.SREG, 0),
                                                spacing=uic.SVLRG)
        smoothSpaceLayout.addWidget(self.smoothAngleFloat, 10)
        smoothSpaceLayout.addWidget(self.smoothAngleCheckbox, 6)
        # Mirror Button Layout ---------------------------------------
        mirrorPolyLayout = elements.hBoxLayout(margins=(0, 0, 0, uic.SREG), spacing=uic.SPACING)
        mirrorPolyLayout.addWidget(self.mirrorPolygonBtn)
        # Mirror Instance Layout ---------------------------------------
        instanceMirrorLayout = elements.hBoxLayout(spacing=uic.SPACING)
        instanceMirrorLayout.addWidget(self.mirrorInstanceBtn, 1)
        # Remove Instance Layout ---------------------------------------
        removeInstanceLayout = elements.hBoxLayout(spacing=uic.SPACING)
        removeInstanceLayout.addWidget(self.uninstanceAllBtn, 1)
        removeInstanceLayout.addWidget(self.uninstanceSelBtn, 1)
        # Add To Main Layout ---------------------------------------
        mainLayout.addLayout(optionsLayout)
        mainLayout.addWidget(self.symmetryTitle)
        mainLayout.addLayout(symFlipLayout)
        mainLayout.addLayout(symmetryLayout)
        mainLayout.addWidget(self.mirrorPolygonTitle)
        mainLayout.addLayout(mergeDirectionLayout)
        mainLayout.addLayout(smoothSpaceLayout)
        mainLayout.addLayout(mirrorPolyLayout)
        mainLayout.addWidget(self.instanceMirrorTitle)
        mainLayout.addLayout(instanceMirrorLayout)
        mainLayout.addLayout(removeInstanceLayout)
