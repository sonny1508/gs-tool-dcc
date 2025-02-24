""" ---------- Set Multiple Attributes -------------

Author: Andrew Silke
"""

from zoovendor.Qt import QtWidgets

from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements

from zoo.libs.maya.cmds.objutils import attributes


UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1


class SetMultipleAttributes(toolsetwidget.ToolsetWidget):
    id = "setMultipleAttributes"
    info = ""
    uiData = {"label": "Set Multiple Attributes",
              "icon": "pasteAttributes",
              "tooltip": "",
              "defaultActionDoubleClick": False,
              "helpUrl": ""}

    # ------------------
    # STARTUP
    # ------------------

    def preContentSetup(self):
        """First code to run, treat this as the __init__() method"""
        pass

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
        return super(SetMultipleAttributes, self).currentWidget()

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiAdvanced or GuiCompact]
        """
        return super(SetMultipleAttributes, self).widgets()

    # ------------------
    # LOGIC
    # ------------------

    def setAttrCustom(self):
        """Sets the custom attribute section"""
        attributes.setAttrShapeAutoSel(self.properties.attributeNameStr.value,
                                       self.properties.attributeValueFloat.value,
                                       includeTransforms=self.properties.transformCheckbox.value,
                                       includeShapes=self.properties.shapesCheckbox.value)

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        for widget in self.widgets():
            widget.setAttrBtn.clicked.connect(self.setAttrCustom)


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
        # Attr Name ---------------------------------------
        tooltip = "Searches for the attribute name on transform nodes."
        self.attributeNameStr = elements.StringEdit(label="Set Attribute",
                                                    editPlaceholder="AttributeName",
                                                    toolTip=tooltip,
                                                    labelRatio=1,
                                                    editRatio=2)
        # Attr Value ---------------------------------------
        tooltip = "Searches for the attribute name on transform nodes."
        self.attributeValueFloat = elements.FloatEdit(label="Atrribute Value",
                                                      editPlaceholder="AttributeName",
                                                      toolTip=tooltip,
                                                      editRatio=2,
                                                      labelRatio=1)
        # Search Shapes ---------------------------------------
        tooltip = "Searches for the attribute name on transform nodes."
        self.transformCheckbox = elements.CheckBox(label="Search Transform Nodes",
                                                   checked=True,
                                                   toolTip=tooltip)
        # Search Transforms ---------------------------------------
        tooltip = "Searches for the attribute name on shape nodes."
        self.shapesCheckbox = elements.CheckBox(label="Search Shape Nodes",
                                                checked=True,
                                                toolTip=tooltip)
        # Set Attribute  ---------------------------------------
        tooltip = "Set the attribute name on all selected objects or shape nodes."
        self.setAttrBtn = elements.styledButton("Set Attribute Selected",
                                                icon="pasteAttributes",
                                                toolTip=tooltip,
                                                style=uic.BTN_DEFAULT)


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
        # Add To Main Layout ---------------------------------------
        mainLayout.addWidget(self.attributeNameStr)
        mainLayout.addWidget(self.attributeValueFloat)
        mainLayout.addWidget(self.setAttrBtn)


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
        shapeTransformLayout = elements.hBoxLayout(margins=(uic.SREG, uic.SREG, uic.SREG, uic.SREG))
        shapeTransformLayout.addWidget(self.transformCheckbox, 1)
        shapeTransformLayout.addWidget(self.shapesCheckbox, 1)
        # Add To Main Layout ---------------------------------------
        mainLayout.addWidget(self.attributeNameStr)
        mainLayout.addWidget(self.attributeValueFloat)
        mainLayout.addLayout(shapeTransformLayout)
        mainLayout.addWidget(self.setAttrBtn)
