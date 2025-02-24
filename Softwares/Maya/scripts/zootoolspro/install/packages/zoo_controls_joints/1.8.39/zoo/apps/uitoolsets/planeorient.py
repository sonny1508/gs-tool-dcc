from zoo.libs.maya import zapi
from zoo.libs.maya.utils import mayamath
from zoovendor.Qt import QtWidgets

from zoo.apps.toolsetsui.widgets import toolsetwidget

from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements
from zoo.libs.commands import maya
from zoo.libs.maya.meta import base as meta
from zoo.libs.maya.cmds.objutils import joints
from zoo.libs.utils import output


class PlaneOrientToolSet(toolsetwidget.ToolsetWidget):
    id = "planeOrient"
    uiData = {"label": "Plane Orient (Joints And Hive)",
              "icon": "planeOrient",
              "tooltip": "Plane orient node alignment tool",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-plane-orient/"
              }

    # ------------------
    # STARTUP
    # ------------------

    def preContentSetup(self):
        self.initialSelection = list(zapi.selected(filterTypes=(zapi.kNodeTypes.kTransform, zapi.kNodeTypes.kJoint,)))

    def contents(self):
        """The UI Modes to build, compact, medium and or advanced """
        return [CompactLayout(parent=self, properties=self.properties, toolsetWidget=self)]

    def postContentSetup(self):
        """Last of the initialize code"""
        self._startMetaNode()
        self.lockMode = False
        self._initPostUiCreate()
        self.uiConnections()
        self.updateFromProperties()

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiAdvanced or GuiCompact]
        """
        return super(PlaneOrientToolSet, self).widgets()

    # ------------------
    # PROPERTIES
    # ------------------

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
        return []

    def _startMetaNode(self):
        coPlanarMetaNodes = meta.findMetaNodesByClassType("zooPlaneOrient")

        if not coPlanarMetaNodes:
            self._coPlanarMeta = maya.coPlanarAlign(create=True)
            self._coPlanarMeta.createReferencePlane()
        else:
            if coPlanarMetaNodes[0].referencePlane() is None:
                coPlanarMetaNodes[0].createReferencePlane()
            self._coPlanarMeta = coPlanarMetaNodes[0]
            self._populateUiFromMeta()

    # ------------------
    # UI UPDATE
    # ------------------

    def enterEvent(self, event):
        """When the mouse enters the widget check that all nodes are intact in the scene"""
        self._validateStartEndNodes()
        self._validateReferencePlane()
        self._validateMetaNode()

    def _validateStartEndNodes(self):
        """Check the start and end nodes still exist in the scene"""
        if not self._coPlanarMeta:
            return
        startNode, endNode = self._coPlanarMeta.validateStartEndNodes()
        if not startNode:
            self.properties.startNodeEdit.value = ""
        if not endNode:
            self.properties.endNodeEdit.value = ""
        self.updateFromProperties()

    def _validateReferencePlane(self):
        """Check the reference plane geo still exists in the scene"""
        if not self._coPlanarMeta:
            return
        if self._coPlanarMeta.referencePlaneExists():
            return
        # Plane doesn't exists so restart meta node
        self._coPlanarMeta.deleteAllReferencePlanesScene()  # clean other nodes left behind
        self._coPlanarMeta.createReferencePlane()
        self._coPlanarMeta.updateReferencePlane()
        self._setReferencePlaneVisibility()

    def _validateMetaNode(self):
        """Check the meta node exists in the scene, used while opening a new scene for example."""
        if self._coPlanarMeta:
            if self._coPlanarMeta.exists():
                return
            self._coPlanarMeta.delete()
        self._startMetaNode()  # restart meta node
        self.properties.startNodeEdit.value = ""
        self.properties.endNodeEdit.value = ""
        self.updateFromProperties()

    def startEndNodes(self):
        return self._coPlanarMeta.startNode(), self._coPlanarMeta.endNode()

    def _initPostUiCreate(self):
        """Adds a start and end node into the UI automatically if 2 nodes are selected"""
        if self.properties.startNodeEdit.value or self.properties.endNodeEdit.value:
            return  # already has nodes so skip auto populate

        sel = self.initialSelection

        if not sel:
            return
        firstNode = sel[0].name()
        endNode = ""
        self._coPlanarMeta.setStartNode(sel[0])
        if len(sel) > 1:
            endNode = sel[-1].name()
            self._coPlanarMeta.setEndNode(sel[-1])

        for widget in self.widgets():
            widget.startNodeEdit.setText(firstNode)
            widget.endNodeEdit.setText(endNode)
        self._coPlanarMeta.updateReferencePlane()

    def setLockMode(self, locked=True):
        """Sets the lock world axis mode, locked is True (World Axis Align), unlocked is False (Position Mode)"""
        self.lockMode = locked
        for widget in self.widgets():  # both GUIs
            widget.lockButton.setVisible(locked)
            widget.unlockButton.setVisible(not locked)
            widget.normalDirCombo.setDisabled(not locked)
            widget.flipAxisCheckCheckBox.setDisabled(not locked)

        self._onModeChanged()

    def _onLockClicked(self):
        self.setLockMode(False)
        output.displayInfo("Success: Plane Mode - Unlocked (Position Mode) ")

    def _onUnlockClicked(self):
        self.setLockMode(True)
        output.displayInfo("Success: Plane Mode - Locked - (Aligned To World Axis)")

    def _onStartNodeEditFinished(self):
        if not self._coPlanarMeta:
            return
        startObjStr = self.properties.startNodeEdit.value
        if not startObjStr:
            return
        startNode = self._coPlanarMeta.startNode()  # If node names match do nothing
        if startNode:
            if startObjStr == startNode.name():
                return
        node = self._coPlanarMeta.stringToStartNode(startObjStr)
        if not node:
            self.properties.startNodeEdit.value = ""
            self.updateFromProperties()
            output.displayWarning("Start Node not found or does not have a unique name in the scene. "
                                  "Use the UI buttons to enter the object")
            return
        self._coPlanarMeta.updateReferencePlane()

    def _onEndNodeEditFinished(self):
        if not self._coPlanarMeta:
            return
        endObjStr = self.properties.endNodeEdit.value
        if not endObjStr:
            return
        endNode = self._coPlanarMeta.endNode()   # If node names match do nothing
        if endNode:
            if endObjStr == endNode.name():
                return
        node = self._coPlanarMeta.stringToEndNode(endObjStr)
        if not node:
            self.properties.endNodeEdit.value = ""
            self.updateFromProperties()
            output.displayWarning("End Node not found or does not have a unique name in the scene. "
                                  "Use the UI buttons to enter the object")
            return
        self._coPlanarMeta.updateReferencePlane()

    def _populateUiFromMeta(self):
        if not self._coPlanarMeta:
            return
        refPlaneCtrl = self._coPlanarMeta.referencePlane()
        startNode = self._coPlanarMeta.startNode()
        if startNode:
            self.properties.startNodeEdit.value = startNode.name()
        endNode = self._coPlanarMeta.endNode()
        if endNode:
            self.properties.endNodeEdit.value = endNode.name()
        self.properties.primaryAxisCombo.value = self._coPlanarMeta.primaryAxis()
        self.properties.flipPrimaryCheck.value = self._coPlanarMeta.negatePrimaryAxis()
        self.properties.secondaryAxisCombo.value = self._coPlanarMeta.secondaryAxis()
        self.properties.flipSecondaryCheck.value = self._coPlanarMeta.negateSecondaryAxis()
        self.properties.normalDirCombo.value = self._coPlanarMeta.axisAligned()
        self.properties.flipAxisCheckCheckBox.value = self._coPlanarMeta.negateAxisAlignedAxis()

        if refPlaneCtrl:
            self.properties.showPlaneRadio.value = self._coPlanarMeta.referencePlaneVisibility()
        self.updateFromProperties()



    # ------------------
    # CONNECTIONS
    # ------------------

    def _onPlaneRadioChanged(self, value):
        if not self._coPlanarMeta:
            return
        self._setReferencePlaneVisibility()

    def _setReferencePlaneVisibility(self):
        if self.properties.showPlaneRadio.value:
            self._coPlanarMeta.showReferencePlane()
        else:
            self._coPlanarMeta.hideReferencePlane()

    def _onToolSetClosed(self):
        if self._coPlanarMeta:
            self._coPlanarMeta.deleteReferencePlane()
            self._coPlanarMeta.delete()

    def _onStartNodeClicked(self):
        sel = list(zapi.selected())
        if sel and self._coPlanarMeta:
            self._coPlanarMeta.setStartNode(sel[0])
            self.properties.startNodeEdit.value = sel[0].name()
            self.updateFromProperties()
            self._updateReferencePlane()

    def _onEndNodeClicked(self):
        sel = list(zapi.selected())
        if sel and self._coPlanarMeta:
            self._coPlanarMeta.setEndNode(sel[0])
            self.properties.endNodeEdit.value = sel[0].name()
            self.updateFromProperties()
            self._updateReferencePlane()

    def _onPrimaryAxisChanged(self, state):
        if not self._coPlanarMeta:
            return
        self._coPlanarMeta.setPrimaryAxis(state)

    def _onSecondaryAxisChanged(self, state):
        if not self._coPlanarMeta:
            return
        self._coPlanarMeta.setSecondaryAxis(state)

    def _onFlipPrimaryCheck(self, state):
        if not self._coPlanarMeta:
            return
        self._coPlanarMeta.setNegatePrimaryAxis(state)

    def _onFlipSecondaryCheck(self, state):
        if not self._coPlanarMeta:
            return
        self._coPlanarMeta.setNegateSecondaryAxis(state)

    def _updateReferencePlane(self, message=False):
        if not self.lockMode:
            if not self._coPlanarMeta.startNode() or not self._coPlanarMeta.endNode():
                if message:
                    output.displayWarning("Nodes not found. Please add the start and end nodes into the UI. ")
                return
        if not self._coPlanarMeta:
            return
        self._coPlanarMeta.updateReferencePlane()
        output.displayInfo("Reference plane updated")

    def _onApplyClicked(self):
        if not self._coPlanarMeta.startNode() or not self._coPlanarMeta.endNode():
            output.displayWarning("Nodes not found. Please add the start and end nodes into the UI. ")
            return
        if not self._coPlanarMeta:
            return
        maya.coPlanarAlign(align=True, metaNode=self._coPlanarMeta)
        output.displayInfo("Success: Plain Orient has been applied.")

    def _onModeChanged(self):
        if not self._coPlanarMeta:
            return
        self._coPlanarMeta.setMode(self.lockMode)
        self._updateReferencePlane()
        self.updateTreeWidget()

    def _onAxisAlignedNormalChanged(self, state):
        if not self._coPlanarMeta:
            return
        self._coPlanarMeta.setAxisAligned(state)
        self._updateReferencePlane()

    def _onAxisAlignedFlipChanged(self, state):
        if not self._coPlanarMeta:
            return
        self._coPlanarMeta.setNegateAxisAlignedAxis(state)
        self._updateReferencePlane()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def showLRA(self):
        """Show the selected joints local rotation axis or LRA manipulators
        """
        joints.displayLocalRotationAxisSelected(children=False, display=True, message=False)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def hideLRA(self):
        """Hide the selected joints local rotation axis or LRA manipulators
        """
        joints.displayLocalRotationAxisSelected(children=False, display=False, message=False)

    def uiConnections(self):
        # handles the coPlanar close event
        self.toolsetClosed.connect(self._onToolSetClosed)
        # handles the Toolset Window close event
        self.toolsetUi.closed.connect(self._onToolSetClosed)
        for widget in self.widgets():  # both GUIs
            widget.startNodeBtn.clicked.connect(self._onStartNodeClicked)
            widget.endNodeBtn.clicked.connect(self._onEndNodeClicked)
            widget.applyBtn.clicked.connect(self._onApplyClicked)
            widget.updateBtn.clicked.connect(self._updateReferencePlane)
            widget.primaryAxisCombo.currentIndexChanged.connect(self._onPrimaryAxisChanged)
            widget.secondaryAxisCombo.currentIndexChanged.connect(self._onSecondaryAxisChanged)
            widget.normalDirCombo.currentIndexChanged.connect(self._onAxisAlignedNormalChanged)
            widget.flipPrimaryCheck.stateChanged.connect(self._onFlipPrimaryCheck)
            widget.flipSecondaryCheck.stateChanged.connect(self._onFlipSecondaryCheck)
            widget.flipAxisCheckCheckBox.stateChanged.connect(self._onAxisAlignedFlipChanged)
            widget.showPlaneRadio.toggled.connect(self._onPlaneRadioChanged)
            widget.showLRABtn.clicked.connect(self.showLRA)
            widget.hideLRABtn.clicked.connect(self.hideLRA)
            widget.lockButton.clicked.connect(self._onLockClicked)
            widget.unlockButton.clicked.connect(self._onUnlockClicked)
            widget.startNodeEdit.editingFinished.connect(self._onStartNodeEditFinished)
            widget.endNodeEdit.editingFinished.connect(self._onEndNodeEditFinished)


class GuiWidgets(QtWidgets.QWidget):
    def __init__(self, parent=None, properties=None, toolsetWidget=None):
        """Builds the main widgets for all GUIs

        properties is the list(dictionaries) used to set logic and pass between the different UI layouts
        such as compact/adv etc

        :param parent: the parent of this widget
        :type parent: :class:`CoPlanar`
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: object

        """
        super(GuiWidgets, self).__init__(parent=parent)

        self.toolsetWidget = toolsetWidget
        self.properties = properties
        # Start and End Joint ---------------------------------------
        tooltip = "The first joint/node (or FK Hive Guide) in the chain."
        self.startNodeEdit = elements.StringEdit(label="Start Joint",
                                                 editPlaceholder="Add start joint/node (Or Hive FK Guide)",
                                                 editText="",
                                                 toolTip=tooltip,
                                                 editRatio=26,
                                                 labelRatio=7)
        tooltip = "Select the start joint/node or Hive FK Guide. \n" \
                  "This will be the first node in a chain/hierarchy \n" \
                  "Start and End and nodes in between will be aligned. "
        self.startNodeBtn = elements.styledButton("",
                                                  "arrowLeft",
                                                  self,
                                                  toolTip=tooltip,
                                                  style=uic.BTN_TRANSPARENT_BG,
                                                  minWidth=15)
        tooltip = "The end joint/node (or FK Hive Guide) in the chain."
        self.endNodeEdit = elements.StringEdit(label="End Joint",
                                               editPlaceholder="Add end joint/node (Or Hive FK Guide)",
                                               editText="",
                                               toolTip=tooltip,
                                               editRatio=26,
                                               labelRatio=7)
        tooltip = "Select the end joint/node or Hive FK Guide. \n" \
                  "This will be the first node in a chain/hierarchy\n" \
                  "Start and End and nodes in between will be aligned. "
        self.endNodeBtn = elements.styledButton("",
                                                "arrowLeft",
                                                self,
                                                toolTip=tooltip,
                                                style=uic.BTN_TRANSPARENT_BG,
                                                minWidth=15)

        # Display Local Rotation Axis -------------------------------------------
        toolTip = "Show the local rotation axis on the selected joint/s"
        self.showLRABtn = elements.styledButton("Show Local Rotation Axis",
                                                icon="axis",
                                                toolTip=toolTip,
                                                style=uic.BTN_LABEL_SML)
        toolTip = "Hide the local rotation axis on the selected joint/s."
        self.hideLRABtn = elements.styledButton("Hide Local Rotation Axis",
                                                icon="axis",
                                                toolTip=toolTip,
                                                style=uic.BTN_LABEL_SML)

        # Primary Axis -------------------------------
        tooltip = "The aim axis for the joints.  \n" \
                  "This axis will aim towards its child joints."
        self.primaryAxisCombo = elements.ComboBoxRegular("Aim Axis (Primary)", items=mayamath.AXIS_NAMES, parent=self,
                                                         toolTip=tooltip)
        tooltip = "Flip/invert the axis's direction"
        self.flipPrimaryCheck = elements.CheckBox("Negative Axis", checked=False, parent=self, toolTip=tooltip)

        # Secondary Axis -------------------------------
        tooltip = "The up axis for joints/nodes/hive guides.  \n" \
                  "This axis will align to the normal of the reference plane's up arrow"
        self.secondaryAxisCombo = elements.ComboBoxRegular("Up Axis (Secondary)", items=mayamath.AXIS_NAMES,
                                                           setIndex=mayamath.ZAXIS, parent=self,
                                                           toolTip=tooltip)
        tooltip = "Flip/invert the axis's direction"
        self.flipSecondaryCheck = elements.CheckBox("Negative Axis", checked=False, parent=self, toolTip=tooltip)

        # Lock Axis To -------------------------------
        tooltip = "Lock the plane to the given world axis. \n" \
                  "Otherwise the plane will try to automatically align to the joint/node chain. \n" \
                  "Click the lock button to activate the `World Axis Align` mode."
        self.normalDirCombo = elements.ComboBoxRegular("Lock Plane To Axis", items=mayamath.AXIS_NAMES, parent=self,
                                                       setIndex=mayamath.ZAXIS, toolTip=tooltip)
        self.normalDirCombo.setDisabled(True)
        tooltip = "Flip/invert the axis's direction"
        self.flipAxisCheckCheckBox = elements.CheckBox("Negative Axis", checked=False, parent=self, toolTip=tooltip)
        self.flipAxisCheckCheckBox.setDisabled(True)

        # Lock Buttons --------------------------------
        tooltip = "Lock the plane to the given world axis (Mode: World Axis Align). \n" \
                  "Otherwise the plane will try to automatically align to the joint/node chain. (Mode: Position)"
        self.lockButton = elements.styledButton("",
                                                "lock",
                                                self,
                                                toolTip=tooltip,
                                                style=uic.BTN_TRANSPARENT_BG,
                                                minWidth=15)
        self.unlockButton = elements.styledButton("",
                                                  "unlock",
                                                  self,
                                                  toolTip=tooltip,
                                                  style=uic.BTN_TRANSPARENT_BG,
                                                  minWidth=15)
        self.lockButton.setVisible(False)

        # Show Plane Radio Buttons ---------------------
        tooltips = ["Hide the `orient plane` geo in the viewport", "Show the `orient plane` geo in the viewport"]
        self.showPlaneRadio = elements.RadioButtonGroup(radioList=["Hide Axis Plane", "Show Axis Plane"],
                                                        parent=self,
                                                        default=1,
                                                        toolTipList=tooltips,
                                                        margins=(uic.REGPAD, uic.SSML, uic.REGPAD, uic.REGPAD))

        # Buttons ----------------------------------
        tooltip = "Applies the plane orient to the joints/nodes or Hive FK guides set in the UI. \n\n" \
                  " 1. Enter a start and end joint/node or Hive FK guide into the UI. \n" \
                  " 2. The start and end joint must be part of a hierarchy. \n" \
                  " 3. Optionally further orient and position the Plane geometry. \n" \
                  " 4. Click the `Apply Plane Orient` button. \n\n" \
                  "The hierarchy's nodes will position snap to the `orient plane` \n" \
                  "It also aligns the node's orientation to the plane's normal depending on the UI settings."
        self.applyBtn = elements.styledButton(text="Apply Plane Orient",
                                              icon="planeOrient",
                                              parent=self,
                                              toolTip=tooltip,
                                              style=uic.BTN_DEFAULT)
        tooltip = "Update the `orient plane` to the current joint/node chain. \n" \
                  "The plane will need updating if the joint/node chain has changed. "
        self.updateBtn = elements.styledButton(text="Refresh Plane",
                                               icon="reload2",
                                               parent=self,
                                               toolTip=tooltip,
                                               style=uic.BTN_DEFAULT)


class CompactLayout(GuiWidgets):
    def __init__(self, parent=None, properties=None, toolsetWidget=None):
        """Adds the layout building the compact version of the GUI:

            default uiMode - 0 is advanced (UI_MODE_COMPACT)

        :param parent: the parent of this widget
        :type parent: qtObject
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: list[dict]
        """
        super(CompactLayout, self).__init__(parent=parent, properties=properties,
                                            toolsetWidget=toolsetWidget)
        # Main Layout ------------------------------------
        contentsLayout = elements.vBoxLayout(self,
                                             margins=(uic.WINSIDEPAD,
                                                      uic.WINBOTPAD,
                                                      uic.WINSIDEPAD,
                                                      uic.WINBOTPAD),
                                             spacing=uic.SPACING)

        # Start Layout ------------------------------------
        startNodeLayout = elements.hBoxLayout(spacing=uic.SLRG + 2)
        startNodeLayout.addWidget(self.startNodeEdit)
        startNodeLayout.addWidget(self.startNodeBtn)

        # End Layout ------------------------------------
        endNodeLayout = elements.hBoxLayout(spacing=uic.SLRG + 2)
        endNodeLayout.addWidget(self.endNodeEdit)
        endNodeLayout.addWidget(self.endNodeBtn)

        # LRA Layout ------------------------------------
        lraLayout = elements.hBoxLayout(spacing=uic.SXLRG, margins=(0, uic.SREG, 0, 0))
        lraLayout.addWidget(self.hideLRABtn)
        lraLayout.addWidget(self.showLRABtn)

        # Axis Grid Layout ------------------------------------
        axisLayout = elements.GridLayout(hSpacing=uic.SLRG, vSpacing=uic.SPACING, margins=(0, uic.SLRG, 0, uic.SREG))
        row = 0
        axisLayout.addWidget(self.primaryAxisCombo, row, 0)
        axisLayout.addWidget(self.flipPrimaryCheck, row, 1)
        row += 1
        axisLayout.addWidget(self.secondaryAxisCombo, row, 0)
        axisLayout.addWidget(self.flipSecondaryCheck, row, 1)
        row += 1
        axisLayout.addWidget(self.normalDirCombo, row, 0)
        axisLayout.addWidget(self.flipAxisCheckCheckBox, row, 1)
        axisLayout.addWidget(self.lockButton, row, 2)
        axisLayout.addWidget(self.unlockButton, row, 2)
        axisLayout.setColumnStretch(0, 7)
        axisLayout.setColumnStretch(1, 3)
        axisLayout.setColumnStretch(2, 1)

        # Button Layout ------------------------------------
        buttonLayout = elements.hBoxLayout(spacing=uic.SPACING)
        buttonLayout.addWidget(self.applyBtn)
        buttonLayout.addWidget(self.updateBtn)

        contentsLayout.addLayout(startNodeLayout)
        contentsLayout.addLayout(endNodeLayout)
        contentsLayout.addLayout(lraLayout)
        contentsLayout.addLayout(axisLayout)
        contentsLayout.addWidget(self.showPlaneRadio)
        contentsLayout.addLayout(buttonLayout)
