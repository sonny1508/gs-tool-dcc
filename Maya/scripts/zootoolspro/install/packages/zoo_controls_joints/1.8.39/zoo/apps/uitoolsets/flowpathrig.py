""" ---------- Toolset Boiler Plate (Multiple UI Modes) -------------
The following code is a template (boiler plate) for building Zoo Toolset GUIs that multiple UI modes.

Multiple UI modes include compact and medium or advanced modes.

This UI will use Compact and Advanced Modes.

The code gets more complicated while dealing with UI Modes.

"""

from zoovendor.Qt import QtWidgets

from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements
from zoo.libs.maya.cmds.objutils import curves

from zoo.libs.maya.cmds.meta import metaflowpath
from functools import partial
from maya import cmds  # for callbacks

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1

DIR_COMBO = ["Auto", "X", "Y", "Z"]
AXIS = ['X', 'Y', 'Z']


class AlongAPath(object):  # toolsetwidget.ToolsetWidget
    id = "alongAPath_UI"
    info = "Joints Along Set Path."
    uiData = {"label": "Object Along A Path",
              "icon": "cubeWire_64",
              "tooltip": "Joints Along Set Path.",
              "defaultActionDoubleClick": False}

    # ------------------
    # STARTUP
    # ------------------

    def preContentSetup(self):
        """First code to run, treat this as the __init__() method"""
        self.toolsetWidget = self  # needed for callback decorators

    def contents(self):
        """The UI Modes to build, compact, medium and or advanced """
        return [self.initCompactWidget()]  # self.initAdvancedWidget()

    def initCompactWidget(self):
        """Builds the Compact GUI (self.compactWidget) """
        self.compactWidget = GuiCompact(parent=self, properties=self.properties, toolsetWidget=self)
        return self.compactWidget

    def postContentSetup(self):
        """Last of the initialize code"""
        self.metaNodes = list()
        self.updateSelection()
        self.uiConnections()
        self.startSelectionCallback()  # start selection callback

    def defaultAction(self):
        """Double Click
        Double clicking the tools toolset icon will run this method
        Be sure "defaultActionDoubleClick": True is set inside self.uiData (meta data of this class)"""
        pass

    def currentWidget(self):
        """ Currently active widget

        :return:
        :rtype: GuiCompact
        """
        return super(AlongAPath, self).currentWidget()

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiCompact]
        """
        return super(AlongAPath, self).widgets()

    # ------------------
    # SELECTION CALLBACKS
    # ------------------

    def selectionChanged(self, selection):
        """ Selection Changed callback event

        :param selection:  The selection from zapi
        :type selection: selected objects, only dag objects not components
        """
        if not selection:  # then still may be a selection TODO add this to internal callbacks maybe?
            selection = cmds.ls(selection=True)  # catches component and node selections
            if not selection:  # then nothing is selected
                self.metaNodes = list()
                return
        self.updateSelection()

    def updateSelection(self):
        """ Update metanode based on selection
        """
        self.metaNodes = list(metaflowpath.selectedMetaNodes())
        self.updateUI()

    def updateUI(self):
        """Pulls from the first selected meta node and pulls data into the UI"""
        # Bail if no meta -----------------
        if not self.metaNodes:
            self.updateFromProperties()
            return
        # Uses the first meta node found ------------------
        self.properties.selectFirstJntTxt.value = self.metaNodes[0].getFirstJointStr()
        self.properties.selectLastJntTxt.value = self.metaNodes[0].getLastJointStr()
        self.properties.selectCurveTxt.value = self.metaNodes[0].getPathStr()
        self.properties.upAxisCombo.value = self.metaNodes[0].getUpAxis()
        self.properties.latticeDivision.value = self.metaNodes[0].getLatticeDivision()

        self.updateFromProperties()
        self.updateTree(delayed=True)

    # ------------------
    # LOGIC
    # ------------------

    def buildRig(self):
        """Takes UI inputs and checks inputs before building the motion path rig
        """
        # Getting Values from each input variable
        firstJoint = self.properties.selectFirstJntTxt.value
        lastJoint = self.properties.selectLastJntTxt.value
        curve = self.properties.selectCurveTxt.value
        dirValue = DIR_COMBO[self.properties.directionCombo.value]
        upAxis_value = AXIS[self.properties.upAxisCombo.value]
        lattice_value = self.properties.latticeDivision.value

        metaflowpath.buildRigSetup(firstJoint, lastJoint, curve, dirValue, upAxis_value, lattice_value)

    def loadObject(self, boxNumber, objecttype):
        geo = metaflowpath.checkLoadObject(objecttype)
        if not geo:
            return
        self.updatingTextbox(boxNumber, geo)

    def updatingTextbox(self, boxNumber, object):
        # Updating text box with selected object name
        if boxNumber == 1:
            self.properties.selectFirstJntTxt.value = object
            self.updateFromProperties()
        if boxNumber == 2:
            self.properties.selectLastJntTxt.value = object
            self.updateFromProperties()
        if boxNumber == 3:
            self.properties.selectCurveTxt.value = object
            self.updateFromProperties()

    def setLatticeAttr(self):
        """Sets the path attribute on selected meta, undo is handled by the slider"""
        if not self.metaNodes:
            return
        for meta in self.metaNodes:
            meta.setLattice(self.properties.latticeDivision.value)

    def setMotionPathAttr(self):
        """Sets the path attribute on selected meta, undo is handled by the slider"""
        if not self.metaNodes:
            return
        for meta in self.metaNodes:
            meta.setMotionPath(self.properties.pathSlider.value)

    def deleteBtnClicked(self):
        """Sets the path attribute on selected meta, undo is handled by the slider"""
        if not self.metaNodes:
            return
        for meta in self.metaNodes:
            meta.deleteAttr()
        if self.properties.selectFirstJntTxt.value:
            self.properties.selectFirstJntTxt.value = ""
            self.properties.selectLastJntTxt.value = ""
            self.properties.selectCurveTxt.value = ""
            self.properties.directionCombo.value = 0
            self.properties.latticeDivision.value = 5

        self.updateFromProperties()
        self.updateTree(delayed=True)

    def setKey(self):
        """Keys the control object at the current time with current settings"""
        if not self.metaNodes:
            return
        for meta in self.metaNodes:
            meta.keyPath()  # keys at current time

    def createCurveContext(self):
        """Enters the create curve context (user draws cvs).  Uses mel hardcoded 3 bezier curve.
        """
        curves.createCurveContext(degrees=3)

    def reverseCurves(self):
        """Reverses the curves on the selected rigs"""
        if not self.metaNodes:
            return
        metaflowpath.reverseCurvesMetaNodes(self.metaNodes)

    def updatingUpAxis(self):
        """Reverses the curves on the selected rigs"""
        if not self.metaNodes:
            return
        for meta in self.metaNodes:
            value = self.properties.upAxisCombo.value
            meta.setUpAxis(value)

    def updatingFrontAxis(self):
        """Reverses the curves on the selected rigs"""
        if not self.metaNodes:
            return
        for meta in self.metaNodes:
            value = self.properties.directionCombo.value
            meta.setFrontAxis(value)

    def switchCurves(self):
        """Switches the selected motion path objects onto a new curve
        Select
        """
        metaflowpath.switchSelectedCurves()

    def inverseFront(self):
        """Switches the selected motion path objects onto a new curve
        Select
        """
        if not self.metaNodes:
            return
        for meta in self.metaNodes:
            checkbox_Value = self.properties.frontInverseCheckBox.value
            meta.inverseDirection(checkbox_Value)

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        for widget in self.widgets():
            widget.createFlowRigBtn.clicked.connect(self.buildRig)
            widget.selectFirstJntBtn.clicked.connect(partial(self.loadObject, 1, "joint"))
            widget.selectLastJntBtn.clicked.connect(partial(self.loadObject, 2, "joint"))
            widget.selectCurveBtn.clicked.connect(partial(self.loadObject, 3, "nurbsCurve"))
            widget.latticeDivision.textModified.connect(self.setLatticeAttr)
            widget.pathSlider.numSliderChanged.connect(self.setMotionPathAttr)
            widget.curveCvBtn.clicked.connect(self.createCurveContext)
            widget.reverseBtn.clicked.connect(self.reverseCurves)
            widget.switchCurvesBtn.clicked.connect(self.switchCurves)
            widget.upAxisCombo.itemChanged.connect(self.updatingUpAxis)
            widget.directionCombo.itemChanged.connect(self.updatingFrontAxis)
            widget.frontInverseCheckBox.stateChanged.connect(self.inverseFront)
            widget.keyBtn.clicked.connect(self.setKey)
            widget.deleteBtn.clicked.connect(self.deleteBtnClicked)

        # connect callbacks
        self.selectionCallbacks.callback.connect(self.selectionChanged)
        self.toolsetActivated.connect(self.startSelectionCallback)
        self.toolsetDeactivated.connect(self.stopSelectionCallback)


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

        # First Joint Text
        self.selectFirstJntTxt = elements.StringEdit(label="",
                                                     editPlaceholder="First Joint",
                                                     editText="")
        # First Joint Button
        self.selectFirstJntBtn = elements.styledButton("",
                                                       "arrowLeft",
                                                       style=uic.BTN_TRANSPARENT_BG,
                                                       minWidth=15)
        # Last Joint Text
        self.selectLastJntTxt = elements.StringEdit(label="",
                                                    editPlaceholder="Last Joint",
                                                    editText="")
        # Last Joint Button
        self.selectLastJntBtn = elements.styledButton("",
                                                      "arrowLeft",
                                                      style=uic.BTN_TRANSPARENT_BG,
                                                      minWidth=15)
        # Curve Text
        self.selectCurveTxt = elements.StringEdit(label="",
                                                  editPlaceholder="Curve",
                                                  editText="")
        # Curve Button
        self.selectCurveBtn = elements.styledButton("",
                                                    "arrowLeft",
                                                    style=uic.BTN_TRANSPARENT_BG,
                                                    minWidth=15)
        # Lattice Division Text
        self.latticeDivision = elements.IntEdit("Lattice Division",
                                                rounding=2,
                                                editText=5,
                                                )
        self.latticeDivision.setMinValue(2)

        # Combo Box
        self.directionCombo = elements.ComboBoxRegular(label="Front Direction",
                                                       items=DIR_COMBO,
                                                       margins=(0, 0, 2, 0))

        self.upAxisCombo = elements.ComboBoxRegular(label="Up Axis",
                                                    items=AXIS,
                                                    setIndex=1,
                                                    margins=(2, 0, 0, 0))

        # CheckBox Inverse------------------------------------
        self.frontInverseCheckBox = elements.CheckBox("Inverse Front")

        # Slider ----------------------------------------
        tooltip = "Sets the `path` attribute on live rigs. "
        self.pathSlider = elements.FloatSlider(label="Path",
                                               defaultValue=0.0,
                                               toolTip=tooltip,
                                               labelBtnRatio=12,
                                               sliderRatio=20,
                                               labelRatio=14,
                                               editBoxRatio=20,
                                               decimalPlaces=3)

        # Key Button ----------------------------------------
        self.keyBtn = elements.styledButton("",
                                            "key",
                                            parent=self,
                                            minWidth=uic.BTN_W_ICN_MED)

        # Create CV Curve Btn ------------------------------------
        self.curveCvBtn = elements.styledButton("",
                                                "curveCv",
                                                minWidth=uic.BTN_W_ICN_MED)
        # Reverse Curve Btn ------------------------------------
        self.reverseBtn = elements.styledButton("",
                                                icon="reverseCurves",
                                                minWidth=uic.BTN_W_ICN_MED)

        # Switch Curve Btn ------------------------------------
        self.switchCurvesBtn = elements.styledButton("",
                                                     icon="switchCurves",
                                                     minWidth=uic.BTN_W_ICN_MED)

        # Apply Button
        self.createFlowRigBtn = elements.styledButton(text="Create Flow Path")

        self.deleteBtn = elements.styledButton("",
                                               "trash",
                                               parent=self,
                                               minWidth=uic.BTN_W_ICN_MED)


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

        # Text Layout --------------------------
        subLayoutFirst = elements.hBoxLayout()
        subLayoutFirst.addWidget(self.selectFirstJntTxt, 5)
        subLayoutFirst.addWidget(self.selectFirstJntBtn, 1)
        subLayoutFirst.addWidget(self.selectLastJntTxt, 5)
        subLayoutFirst.addWidget(self.selectLastJntBtn, 1)

        # Curve Layout --------------------------
        subLayoutCurve = elements.hBoxLayout()
        subLayoutCurve.addWidget(self.selectCurveTxt, 5)
        subLayoutCurve.addWidget(self.selectCurveBtn, 1)
        subLayoutCurve.addWidget(self.latticeDivision, 6)

        # Combo Layout --------------------------
        comboLayout = elements.hBoxLayout()
        comboLayout.addWidget(self.directionCombo, 3)
        comboLayout.addWidget(self.upAxisCombo, 3)
        comboLayout.addWidget(self.frontInverseCheckBox, 2)

        # Slider Layout --------------------------
        sliderLayout = elements.hBoxLayout(spacing=uic.SPACING)
        sliderLayout.addWidget(self.pathSlider, 20)
        sliderLayout.addWidget(self.keyBtn, 1)

        # Button Layout --------------------------
        buttonLayout = elements.hBoxLayout(spacing=uic.SPACING)
        buttonLayout.addWidget(self.curveCvBtn)
        buttonLayout.addWidget(self.reverseBtn)
        buttonLayout.addWidget(self.switchCurvesBtn)
        buttonLayout.addWidget(self.createFlowRigBtn, 1)
        buttonLayout.addWidget(self.deleteBtn)

        # Main Layout ---------------------------------------
        mainLayout = elements.vBoxLayout(self, margins=(uic.WINSIDEPAD, uic.WINBOTPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SREG)
        # Add To Main Layout
        mainLayout.addLayout(subLayoutFirst)
        mainLayout.addLayout(subLayoutCurve)
        mainLayout.addLayout(comboLayout)
        mainLayout.addLayout(sliderLayout)
        mainLayout.addLayout(buttonLayout)
