""" ---------- Toolset Boiler Plate (Multiple UI Modes) -------------
The following code is a template (boiler plate) for building Zoo Toolset GUIs that multiple UI modes.

Multiple UI modes include compact and medium or advanced modes.

This UI will use Compact and Advanced Modes.

The code gets more complicated while dealing with UI Modes.

"""

from zoovendor.Qt import QtWidgets

from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements

from zoo.libs.maya.cmds.objutils import matrix

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1


class MatrixTool(toolsetwidget.ToolsetWidget):
    id = "matrixTool"
    info = "Offset Matrix tools for Maya objects."
    uiData = {"label": "Matrix Tool",
              "icon": "matrix",
              "tooltip": "Offset Matrix tools for Maya objects.",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-matrix-tool/"}

    # ------------------
    # STARTUP
    # ------------------

    def preContentSetup(self):
        """First code to run, treat this as the __init__() method"""
        pass

    def contents(self):
        """The UI Modes to build, compact, medium and or advanced """
        return [self.initCompactWidget()]

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
        return super(MatrixTool, self).currentWidget()

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiAdvanced or GuiCompact]
        """
        return super(MatrixTool, self).widgets()

    # ------------------
    # LOGIC
    # ------------------

    @toolsetwidget.ToolsetWidget.undoDecorator
    def modelerFreezeMatrix(self):
        """Sets an objects translate, rotate to be zero and scale to be one.
        Will freeze scale to avoid unexpected rotation issues"""
        matrix.zeroSrtModelMatrixSel()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def freezeToMatrix(self):
        """Sets an objects translate, rotate to be zero and scale to be one."""
        matrix.srtToMatrixOffsetSel()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def resetMatrix(self):
        """Resets an objects Offset Matrix to be zero."""
        matrix.zeroMatrixOffsetSel()

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        for widget in self.widgets():
            widget.modellerFreezeMatrixBtn.clicked.connect(self.modelerFreezeMatrix)
            widget.freezeOffsetMatrixBtn.clicked.connect(self.freezeToMatrix)
            widget.resetOffsetMatrixBtn.clicked.connect(self.resetMatrix)


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
        # Modeler Freeze Matrix ---------------------------------------
        tooltip = "Modeler Freeze to Parent Offset Matrix \n" \
                  "Sets an object's `translate`, `rotate` to zero and `scale` to one. \n" \
                  "Transfers `translate` and `rotate` information to the `offsetParentMatrix`. \n" \
                  "`Scale` will be frozen to 1.0 to support non-uniform issues with rotation. \n" \
                  "Supported in Maya 2020 and above"
        self.modellerFreezeMatrixBtn = elements.AlignedButton("Modeler Freeze Matrix",
                                                              icon="matrix",
                                                              toolTip=tooltip)
        # Reset Offset Matrix ---------------------------------------
        tooltip = "Freeze to Parent Offset Matrix \n" \
                  "Sets an object's `translate`, `rotate` to zero and `scale` to one. \n" \
                  "Transfers `translate`, `rotate` and `scale` information to the `offsetParentMatrix`. \n" \
                  "Can be non-uniform issues with rotation after freezing, see `Modeler Freeze Matrix`. \n" \
                  "Supported in Maya 2020 and above"
        self.freezeOffsetMatrixBtn = elements.AlignedButton("Freeze To Offset Matrix",
                                                            icon="matrix",
                                                            toolTip=tooltip)
        # Reset Offset Matrix ---------------------------------------
        tooltip = "Resets an objects Offset Matrix to zero. \n" \
                  "Maintains the objects translate, rotate and scale position. \n" \
                  "Supported in Maya 2020 and above"
        self.resetOffsetMatrixBtn = elements.AlignedButton("Unfreeze Offset Matrix",
                                                           icon="matrix",
                                                           toolTip=tooltip)



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
        # Button Freeze Layout -----------------------------
        freezeLayoutGrid = elements.GridLayout(spacing=uic.SPACING)
        row = 0
        freezeLayoutGrid.addWidget(self.modellerFreezeMatrixBtn, row, 0)
        freezeLayoutGrid.addWidget(self.freezeOffsetMatrixBtn, row, 1)
        row += 1
        freezeLayoutGrid.addWidget(self.resetOffsetMatrixBtn, row, 0, 1, 2)
        freezeLayoutGrid.setColumnStretch(0, 1)
        freezeLayoutGrid.setColumnStretch(1, 1)

        # Add To Main Layout ---------------------------------------
        mainLayout.addLayout(freezeLayoutGrid)


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


