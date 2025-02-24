from zoovendor.Qt import QtWidgets

from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements

from zoo.libs.maya.cmds.modeling import extrude

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1


class ThickExtrude(toolsetwidget.ToolsetWidget):
    id = "thickExtrude"
    info = "Extrudes from the center of the polygon selection adding thickness."
    uiData = {"label": "Thick Extrude",
              "icon": "extrudeThickness",
              "tooltip": "Extrudes from the center of the polygon selection adding thickness.",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-thick-extrude/"}

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

    def postContentSetup(self):
        """Last of the initialize code"""
        self.uiConnections()
        # Callbacks
        self.selectionCallbacks.callback.connect(self.selectionChanged)  # monitor selection
        self.toolsetActivated.connect(self.startSelectionCallback)
        self.toolsetDeactivated.connect(self.stopSelectionCallback)
        self.startSelectionCallback()  # start selection callback
        # Update latest data
        self.refreshUI()

    def currentWidget(self):
        """Returns the current widget class eg. self.compactWidget or self.advancedWidget

        Over ridden class
        :rtype: GuiWidgets
        """
        return super(ThickExtrude, self).currentWidget()

    def widgets(self):
        """Override base method for autocompletion

        :return:
        :rtype: list[GuiAdvanced or GuiCompact]
        """
        return super(ThickExtrude, self).widgets()

    # ------------------
    # SELECTION CALLBACK
    # ------------------

    def selectionChanged(self, sel):
        """Selection Changed callback event
        """
        if not sel:
            return
        self.refreshUI()

    def enterEvent(self, event):
        """Update selection on enter event

        :param event:
        :type event:
        """
        self.refreshUI()

    # ------------------
    # LOGIC
    # ------------------

    def refreshUI(self):
        """
        """
        thickness, weight = extrude.getExtrudeThicknessSelected(message=False)
        if thickness is None:
            return
        self.properties.thickFSlider.value = thickness
        self.properties.weightFSlider.value = weight
        self.updateFromProperties()

    # ------------------
    # LOGIC
    # ------------------

    @toolsetwidget.ToolsetWidget.undoDecorator
    def createThickness(self):
        """Create the extrude and move vertex setup"""
        extrude.extrudeCenterThicknessSelected(thickness=self.properties.thickFSlider.value,
                                               weight=self.properties.weightFSlider.value)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def deleteThickness(self):
        """Delete the extrude and move vertex setup"""
        extrude.deleteThicknessSelected()

    def setThickness(self):  # Undo is handled
        """Change the extrude and move vertex settings"""
        extrude.setExtrudeThicknessSelected(thickness=self.properties.thickFSlider.value,
                                            weight=self.properties.weightFSlider.value,
                                            message=False)

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""

        for widget in self.widgets():
            widget.createThicknessBtn.clicked.connect(self.createThickness)
            widget.deleteThicknessBtn.clicked.connect(self.deleteThickness)

            widget.thickFSlider.numSliderChanged.connect(self.setThickness)
            widget.thickFSlider.sliderPressed.connect(self.openUndoChunk)
            widget.thickFSlider.sliderReleased.connect(self.closeUndoChunk)

            widget.weightFSlider.numSliderChanged.connect(self.setThickness)
            widget.weightFSlider.sliderPressed.connect(self.openUndoChunk)
            widget.weightFSlider.sliderReleased.connect(self.closeUndoChunk)


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
        # Thickness ---------------------------------------
        tooltip = "The thickness value in Maya units (usually cms) \n" \
                  "Affects the extrude amount"
        self.thickFSlider = elements.FloatSlider(label="Thickness",
                                                 defaultValue=1.0,
                                                 sliderMin=0.0001,
                                                 sliderMax=5.0,
                                                 dynamicMax=True,
                                                 dynamicMin=True,
                                                 decimalPlaces=3,
                                                 toolTip=tooltip)
        # Weight ---------------------------------------
        tooltip = "The offset of the thickness.  \n" \
                  "0.5 centers expands the extrude from the center. \n" \
                  "Other values will weight either side. "
        self.weightFSlider = elements.FloatSlider(label="Weight",
                                                  defaultValue=0.5,
                                                  sliderMin=0.0,
                                                  sliderMax=1.0,
                                                  dynamicMax=True,
                                                  dynamicMin=True,
                                                  decimalPlaces=3,
                                                  toolTip=tooltip)
        # Thickness Button ---------------------------------------
        tooltip = "Creates a thickness on thin object/s extruding in both directions from the center. \n" \
                  "Select a thin polygon object and run. \n" \
                  "The mesh will be thickened from the center or weight value."
        self.createThicknessBtn = elements.styledButton("Thick Extrude",
                                                        icon="extrudeThickness",
                                                        toolTip=tooltip,
                                                        style=uic.BTN_DEFAULT)
        # Thickness Button ---------------------------------------
        toolTip = "Delete the thickness, based on selection. \n" \
                  "Removes the `Extrude` and `MoveVertex` nodes. "
        self.deleteThicknessBtn = elements.styledButton("",
                                                        "trash",
                                                        toolTip=toolTip,
                                                        parent=self,
                                                        minWidth=uic.BTN_W_ICN_MED)


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
        mainLayout = elements.vBoxLayout(self, margins=(uic.WINSIDEPAD, uic.WINBOTPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SREG)
        # Button Layout ---------------------------------------
        buttonLayout = elements.hBoxLayout(spacing=uic.SPACING)
        buttonLayout.addWidget(self.createThicknessBtn, 10)
        buttonLayout.addWidget(self.deleteThicknessBtn, 1)
        # Add To Main Layout ---------------------------------------
        mainLayout.addWidget(self.thickFSlider)
        mainLayout.addWidget(self.weightFSlider)
        mainLayout.addLayout(buttonLayout)
