from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.libs.hive import api as hiveapi
from zoo.libs.maya import zapi
from zoo.libs.maya.cmds.animation import resetattrs
from zoo.libs.maya.utils import mayamath
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt import utils as qtutils
from zoo.libs.pyqt.widgets import elements
from zoovendor.Qt import QtWidgets
from maya import cmds

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1


class HiveGuideAlignMirrorToolset(toolsetwidget.ToolsetWidget):
    id = "hiveGuideAlignMirror"
    info = "Hive Guide Align and Mirror UI."
    uiData = {"label": "Hive Guide Align And Mirror",
              "icon": "axis",
              "tooltip": "Provides an Fbx exporter for hive rigs.",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-hive-guide-align-and-mirror"}

    def contents(self):
        """The UI Modes to build, compact, medium and or advanced """
        return [self.initCompactWidget()]

    def initCompactWidget(self):
        """Builds the Compact GUI (self.compactWidget) """
        self.compactWidget = GuiCompact(parent=self)
        return self.compactWidget

    def postContentSetup(self):
        """Last of the initialize code"""
        self.uiConnections()
        self.startSelectionCallback()
        self.handleSelection()

    def initializeProperties(self):
        """Used to store and update UI data

        For use in the GUI use:
            current value: self.properties.itemName.value
            default value (automatic): self.properties.itemName.default

        To connect Qt widgets to property methods use:
            self.toolsetWidget.linkProperty(self.widgetQtName, "itemName")

        :return properties: special dictionary used to save and update all GUI widgets
        :rtype properties: list(dict)
        """
        return [
            # {"name": "triangulateCheckBox", "value": 1},
        ]

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiAdvanced or GuiCompact]
        """
        return super(HiveGuideAlignMirrorToolset, self).widgets()

    # ------------------
    # ENTER
    # ------------------

    def enterEvent(self, event):
        """When the cursor enters the UI update it"""
        # self._rigStateChanged()
        # self.startSelectionCallback()

    # -------------------
    # HIVE CORE SIGNALS
    # -------------------
    def handleSelection(self, selection=None):
        selection = selection if selection is not None else zapi.selected(filterTypes=(zapi.kNodeTypes.kTransform,))
        for sel in selection:
            if not hiveapi.Guide.isGuide(sel):
                continue
            self.currentGuide = hiveapi.Guide(sel.object())
            self.oppositeGuide = None
            self.resetUI()
            break

    def selectionChanged(self, selection):
        # Callbacks are handled automatically by toolsetcallbacks.py which this class inherits"""
        self.handleSelection(selection=zapi.nodesByNames(selection))

    def selectedGuides(self):
        selection = zapi.selected(filterTypes=(zapi.kNodeTypes.kTransform,))
        guides = []
        for sel in selection:
            if not hiveapi.Guide.isGuide(sel):
                continue
            guides.append(hiveapi.Guide(sel.object()))
        return guides

    def resetUI(self):
        selection = self.selectedGuides()
        if not selection:
            return
        firstSelection = selection[0]
        widget = self.currentWidget()
        with qtutils.blockSignalsContext([widget.autoAlignCheck,
                                          widget.primaryAxisCombo,
                                          widget.secondaryAxisCombo,
                                          widget.flipPrimaryCheck,
                                          widget.flipSecondaryCheck,
                                          widget.behaviorAxisCombo]):
            widget.autoAlignCheck.setChecked(firstSelection.autoAlign.value())
            aimVector = firstSelection.autoAlignAimVector.value()
            upVector = firstSelection.autoAlignUpVector.value()
            primaryIsNegative = mayamath.isVectorNegative(aimVector)
            secondaryIsNegative = mayamath.isVectorNegative(upVector)

            widget.primaryAxisCombo.setCurrentIndex(mayamath.primaryAxisIndexFromVector(aimVector))
            widget.secondaryAxisCombo.setCurrentIndex(mayamath.primaryAxisIndexFromVector(upVector))
            widget.flipPrimaryCheck.setChecked(primaryIsNegative)
            widget.flipSecondaryCheck.setChecked(secondaryIsNegative)
            widget.behaviorAxisCombo.setCurrentIndex(
                firstSelection.attribute(hiveapi.constants.MIRROR_BEHAVIOUR_ATTR).value())

    @toolsetwidget.ToolsetWidget.undoDecorator
    def onAutoAlignChanged(self, state):
        state = bool(state)  # convert from 0-2 to bool, 2 is checked
        for sel in self.selectedGuides():
            cmds.setAttr(sel.autoAlign.name(), state)
        widget = self.currentWidget()
        widget.primaryAxisCombo.setEnabled(state)
        widget.flipPrimaryCheck.setEnabled(state)
        widget.secondaryAxisCombo.setEnabled(state)
        widget.flipSecondaryCheck.setEnabled(state)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def onShowLocalLRAChanged(self, state):
        selection = self.selectedGuides()
        if not selection:
            return
        components = list(hiveapi.componentsFromNodes(selection).keys())
        if not components:
            return
        hiveapi.commands.setGuideLRA(components, state)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def onFlipPrimaryAxis(self, state):

        for sel in self.selectedGuides():
            aimVector = sel.autoAlignAimVector.value()
            self._setVector(aimVector, state)

            cmds.setAttr(sel.autoAlignAimVector.name(), *list(aimVector))

    def _setVector(self, vector, state):
        axisIndex = mayamath.primaryAxisIndexFromVector(vector)
        vector[axisIndex] = -1.0 if state else 1.0
        return vector

    @toolsetwidget.ToolsetWidget.undoDecorator
    def onFlipSecondaryAxis(self, state):
        for sel in self.selectedGuides():
            upVector = sel.autoAlignUpVector.value()
            self._setVector(upVector, state)
            cmds.setAttr(sel.autoAlignUpVector.name(), *list(upVector))

    @toolsetwidget.ToolsetWidget.undoDecorator
    def onPrimaryAxisChanged(self, index):
        selection = self.selectedGuides()
        if not selection:
            return
        vector = mayamath.AXIS_VECTOR_BY_IDX[index]
        if self.currentWidget().flipPrimaryCheck.isChecked():
            vector *= -1
        for sel in selection:
            cmds.setAttr(sel.autoAlignAimVector.name(), *list(vector))

    @toolsetwidget.ToolsetWidget.undoDecorator
    def onSecondaryAxisChanged(self, index):
        selection = self.selectedGuides()
        if not selection:
            return
        vector = mayamath.AXIS_VECTOR_BY_IDX[index]
        if self.currentWidget().flipSecondaryCheck.isChecked():
            vector *= -1
        for sel in selection:
            cmds.setAttr(sel.autoAlignUpVector.name(), *list(vector))

    @toolsetwidget.ToolsetWidget.undoDecorator
    def onBehaviourChanged(self, index):

        for sel in self.selectedGuides():
            cmds.setAttr(sel.attribute(hiveapi.constants.MIRROR_BEHAVIOUR_ATTR).name(), index)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def onResetAlignment(self):
        for sel in self.selectedGuides():
            resetattrs.resetAttrs(sel.fullPathName(),
                                  ["autoAlignAimVector", "autoAlignUpVector", "autoAlign", "mirrorBehaviour"],
                                  True)

    def onAlignToWorld(self):
        selection = self.selectedGuides()
        if not selection:
            return
        components = set()
        for sel in selection:
            currentComponent = hiveapi.componentFromNode(sel)
            if currentComponent not in components:
                components.add(currentComponent)
                continue
        with hiveapi.componentutils.disconnectComponentsContext(components):
            matrices = []
            for sel in selection:
                sel.autoAlign.set(False)
                transform = sel.transformationMatrix()
                transform.setRotation(zapi.Quaternion())
                matrices.append(transform.asMatrix())

            hiveapi.commands.setGuidesWorldMatrices(selection, matrices)

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""

        # hiveUICore = uiinterface.instance()
        for widget in self.widgets():
            widget.autoAlignCheck.stateChanged.connect(self.onAutoAlignChanged)
            widget.flipPrimaryCheck.stateChanged.connect(self.onFlipPrimaryAxis)
            widget.flipSecondaryCheck.stateChanged.connect(self.onFlipSecondaryAxis)
            widget.primaryAxisCombo.currentIndexChanged.connect(self.onPrimaryAxisChanged)
            widget.secondaryAxisCombo.currentIndexChanged.connect(self.onSecondaryAxisChanged)
            widget.behaviorAxisCombo.currentIndexChanged.connect(self.onBehaviourChanged)
            widget.resetAlignmentBtn.clicked.connect(self.onResetAlignment)
            widget.alignToWorldBtn.clicked.connect(self.onAlignToWorld)
            widget.showLocalLRA.stateChanged.connect(self.onShowLocalLRAChanged)

        # selection callbacks
        self.selectionCallbacks.callback.connect(self.selectionChanged)
        self.toolsetActivated.connect(self.startSelectionCallback)
        self.toolsetDeactivated.connect(self.stopSelectionCallback)


class GuiWidgets(QtWidgets.QWidget):
    def __init__(self, parent=None):
        """Builds the main widgets for all GUIs

        properties is the list(dictionaries) used to set logic and pass between the different UI layouts
        such as compact/adv etc

        :param parent: the parent of this widget
        :type parent: :class:`QtWidgets.QWidget`
        """
        super(GuiWidgets, self).__init__(parent=parent)
        self.primaryAxisLayout = elements.hBoxLayout(
            margins=(uic.SLRG, 0, uic.SVLRG, 0),
            spacing=uic.SLRG + 2)
        self.secondaryAxisLayout = elements.hBoxLayout(
            margins=(uic.SLRG, 0, uic.SVLRG, 0),
            spacing=uic.SLRG + 2)

        # Rig Combo -----------------------------
        self.autoAlignCheck = elements.CheckBox("Auto Align", checked=True, parent=self)
        self.showLocalLRA = elements.CheckBox("Toggle LRA", checked=False, parent=self)
        self.primaryAxisCombo = elements.ComboBoxRegular("Primary Axis:", items=mayamath.AXIS_NAMES, parent=self)
        self.secondaryAxisCombo = elements.ComboBoxRegular("Secondary Axis:", items=mayamath.AXIS_NAMES, parent=self)
        self.flipPrimaryCheck = elements.CheckBox("Negative Axis", checked=False, parent=self)
        self.flipSecondaryCheck = elements.CheckBox("Negative Axis", checked=False, parent=self)

        self.behaviorAxisCombo = elements.ComboBoxRegular("Mirror Behaviour:",
                                                          items=hiveapi.constants.MIRROR_BEHAVIOURS_TYPES,
                                                          spacing=0,
                                                          margins=(uic.SLRG, 0, uic.SVLRG, 0),
                                                          parent=self)

        self.resetAlignmentBtn = elements.styledButton("Reset All",
                                                       icon="axis",
                                                       # toolTip=toolTip,
                                                       minWidth=uic.BTN_W_ICN_MED,
                                                       parent=self)
        self.alignToWorldBtn = elements.styledButton("Align To World",
                                                     icon="axis",
                                                     # toolTip=toolTip,
                                                     minWidth=uic.BTN_W_ICN_MED,
                                                     parent=self)
        self.mirrorDivider = elements.LabelDivider(text="Mirror Attributes", parent=self)
        self.alignDivider = elements.LabelDivider(text="Align Attributes", parent=self)
        self.primaryAxisLayout.addWidget(self.primaryAxisCombo)
        self.primaryAxisLayout.addWidget(self.flipPrimaryCheck)

        self.secondaryAxisLayout.addWidget(self.secondaryAxisCombo)
        self.secondaryAxisLayout.addWidget(self.flipSecondaryCheck)

        self.buttonLayout = elements.hBoxLayout(spacing=uic.SPACING)
        self.buttonLayout.addWidget(self.resetAlignmentBtn)
        self.buttonLayout.addWidget(self.alignToWorldBtn)

        self.checkboxLayout = elements.hBoxLayout(spacing=uic.SLRG + 2, margins=(uic.SLRG, 0, uic.SVLRG, 0))
        self.checkboxLayout.addWidget(self.autoAlignCheck)
        self.checkboxLayout.addWidget(self.showLocalLRA)


class GuiCompact(GuiWidgets):
    def __init__(self, parent=None):
        """Adds the layout building the compact version of the GUI:

            default uiMode - 0 is advanced (UI_MODE_COMPACT)

        :param parent: the parent of this widget
        :type parent: QtWidgets.QWidget
        """
        super(GuiCompact, self).__init__(parent=parent)
        # Main Layout ---------------------------------------
        mainLayout = elements.vBoxLayout(self,
                                         margins=(uic.WINSIDEPAD, uic.WINBOTPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SLRG)
        mainLayout.addWidget(self.mirrorDivider)
        mainLayout.addWidget(self.behaviorAxisCombo)
        mainLayout.addWidget(self.alignDivider)
        mainLayout.addLayout(self.checkboxLayout)
        mainLayout.addLayout(self.primaryAxisLayout)
        mainLayout.addLayout(self.secondaryAxisLayout)
        mainLayout.addLayout(self.buttonLayout)
