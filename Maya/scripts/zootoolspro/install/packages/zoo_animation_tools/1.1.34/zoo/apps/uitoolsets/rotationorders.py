from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements
from zoovendor.Qt import QtWidgets, QtCore

from zoo.libs.maya.cmds.animation import generalanimation
from zoo.libs.maya import zapi

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1

EMPTY_LIST = ["Please select an object..."]


class RotationOrderWidget(toolsetwidget.ToolsetWidget):
    id = "rotationOrder"
    info = "Simple UI for Changing Rotation Orders."
    uiData = {"label": "Change Rotation Orders",
              "icon": "rotateManipulator",
              "tooltip": "Simple UI for Changing Rotation Orders.",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-change-rotation-orders/"}

    def preContentSetup(self):
        pass

    def contents(self):
        """The UI Modes to build, compact, medium and or advanced """
        return [self.initCompactWidget()]

    def initCompactWidget(self):
        """Builds the Compact GUI (self.compactWidget) """
        self.compactWidget = GuiCompact(parent=self, properties=self.properties, toolsetWidget=self)
        return self.compactWidget

    def postContentSetup(self):
        """Last of the initialize code"""
        self.uiConnections()

        self.comboInt = self.properties.changeRotOrderCombo.value
        self.startSelectionCallback()

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
        return [{"name": "changeRotOrderCombo", "value": 0},
                {"name": "bakeEveryFrameBtn", "value": False},
                {"name": "rotOrderRadioGrp", "value": 0}]

    def actions(self):
        """Right click menu on the main toolset tool icon"""
        icon = "rotateManipulator"
        return [{"type": "action",
                 "name": "xyz",
                 "label": "XYZ Rot Order",
                 "icon": icon,
                 "tooltip": ""},
                {"type": "action",
                 "name": "yzx",
                 "label": "YZX Rot Order",
                 "icon": icon,
                 "tooltip": ""},
                {"type": "action",
                 "name": "zxy",
                 "label": "ZXY Rot Order",
                 "icon": icon,
                 "tooltip": ""},
                {"type": "action",
                 "name": "xzy",
                 "label": "XZY Rot Order",
                 "icon": icon,
                 "tooltip": ""},
                {"type": "action",
                 "name": "yxz",
                 "label": "YXZ Rot Order",
                 "icon": icon,
                 "tooltip": ""},
                {"type": "action",
                 "name": "zyx",
                 "label": "ZYX Rot Order",
                 "icon": icon,
                 "tooltip": ""}]

    def executeActions(self, action):
        name = action["name"].lower()
        if name in zapi.constants.kRotateOrderNames:
            self.changeRotOrder(newRotOrder=zapi.constants.kRotateOrderNames.index(name))

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiAdvanced or GuiCompact]
        """
        return super(RotationOrderWidget, self).widgets()

    # ------------------
    # ENTER
    # ------------------

    def enterEvent(self, event):
        """When the cursor enters the UI update it"""
        self._updateLabels()

    # ------------------
    # CALLBACKS
    # ------------------

    def selectionChanged(self, selection):
        """Run when the callback selection changes, updates the GUI if an object is selected

        Callbacks are handled automatically by toolsetcallbacks.py which this class inherits"""
        if not selection:  # then don't update
            self._clearCombo()
            self._comboAddItems(EMPTY_LIST)
            return
        selection = next(zapi.nodesByNames(selection), None)
        self._updateLabels(selection)

    # ------------------
    # UI
    # ------------------

    def _clearCombo(self):
        """Clears the combo quietly of all items"""
        self.compactWidget.changeRotOrderCombo.blockSignals(True)
        self.compactWidget.changeRotOrderCombo.clear()
        self.compactWidget.changeRotOrderCombo.blockSignals(False)

    def _comboAddItems(self, items):
        """Adds items to the combo quietly"""
        self.compactWidget.changeRotOrderCombo.blockSignals(True)
        self.compactWidget.changeRotOrderCombo.addItems(items)
        self.compactWidget.changeRotOrderCombo.blockSignals(False)

    def _updateLabels(self, node=None):
        """Updates the combobox items depending on what's selected"""
        self._clearCombo()
        labels = self._rotateOrderLabels(node)
        self._comboAddItems(labels)
        if len(labels) == 1:  # empty list
            return
        self.properties.changeRotOrderCombo.value = self.comboInt
        self.updateFromProperties()

    def comboChanged(self):
        """Saves the int when th combo is changed"""
        self.comboInt = self.properties.changeRotOrderCombo.value

    def _rotateOrderLabels(self, node=None):
        """builds and returns the list of names for the combobox

        :param node: processes current selected or provided nodes keyframes and updates the UI
        :type node: :class:`zapi.DagNode` or None

        :rtype comboNamesList: list of string names/labels for the combobox
        :rtype comboNamesList: list[str]
        """
        values = generalanimation.allGimbalTolerancesForKeys(node,
                                                             currentFrameRange=self.properties.rotOrderRadioGrp.value,
                                                             message=False)
        if not values:
            return EMPTY_LIST
        return generalanimation.gimbalTolerancesToLabels(values)

    # ------------------
    # LOGIC
    # ------------------

    @toolsetwidget.ToolsetWidget.undoDecorator
    def changeRotOrder(self, newRotOrder=None):
        """Main function, uses the GUI to change rotation order of the selected objs in Maya
        The logic here is an open source script by Morgan Loomis, see generalanimation.changeRotOrder for more info.
        """
        generalanimation.changeRotOrder(
            newRotOrder=newRotOrder or self.properties.changeRotOrderCombo.value,
            bakeEveryFrame=self.properties.bakeCheckbox.value,
            timeline=self.properties.rotOrderRadioGrp.value  # timeline is 1 == True
        )

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        for widget in self.widgets():
            # General -------------------------------
            widget.changeRotOrderBtn.clicked.connect(self.changeRotOrder)
            widget.changeRotOrderCombo.itemChanged.connect(self.comboChanged)  # updates other UIs
        # Callback methods
        self.selectionCallbacks.callback.connect(self.selectionChanged)  # monitor selection
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
        :type toolsetWidget: :class:`RotationOrderWidget`
        """
        super(GuiWidgets, self).__init__(parent=parent)
        self.properties = properties
        # Change Rotation Order Combo ---------------------------------------
        toolTip = "Change Rotation Order - Will change the xyz rotation order on selected transforms\n" \
                  "If objects have keyframes will change each key to compensate for the correct rotation."
        self.changeRotOrderCombo = elements.ComboBoxRegular(label="Order",
                                                            items=toolsetWidget._rotateOrderLabels(),
                                                            toolTip=toolTip,
                                                            setIndex=self.properties.changeRotOrderCombo.value,
                                                            labelRatio=10,
                                                            boxRatio=45,
                                                            parent=self)
        # Change Rot Order Button --------------------------
        self.changeRotOrderBtn = elements.styledButton("Change Rotation Order",
                                                       icon="rotateManipulator",
                                                       toolTip=toolTip,
                                                       minWidth=uic.BTN_W_ICN_MED,
                                                       parent=self)
        toolTip = "If Checked will bake on every frame for the frame range."
        self.bakeCheckbox = elements.CheckBox("Bake", enableMenu=False, toolTip=toolTip,
                                              checked=self.properties.bakeEveryFrameBtn.value,
                                              parent=self)
        tooltips = ["Changes all keys in the timeline.",
                    "Changes keys within the active timeline only."]
        # note: margins are 0 because our parent layout is responsible the margins, this makes all \
        # widgets align correctly vertically
        self.rotOrderRadioGrp = elements.RadioButtonGroup(["All Keyed Frames", "Timeline Only"],
                                                          toolTipList=tooltips,
                                                          default=self.properties.rotOrderRadioGrp.value,
                                                          parent=self,
                                                          margins=(uic.SXLRG, uic.SREG, uic.SLRG, uic.SREG),
                                                          alignment=QtCore.Qt.AlignVCenter)


class GuiCompact(GuiWidgets):
    def __init__(self, parent=None, properties=None, uiMode=UI_MODE_COMPACT, toolsetWidget=None):
        """Adds the layout building the compact version of the GUI:

            default uiMode - 0 is advanced (UI_MODE_COMPACT)

        :param parent: the parent of this widget
        :type parent: QtWidgets.QWidget
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: :class:`toolsetwidget.PropertiesDict`
        """
        super(GuiCompact, self).__init__(parent=parent, properties=properties, uiMode=uiMode,
                                         toolsetWidget=toolsetWidget)
        # Main Layout ---------------------------------------
        mainLayout = elements.vBoxLayout(self,
                                         margins=(uic.WINSIDEPAD, uic.WINBOTPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SLRG)
        # Change Rot Order Layout -----------------------------
        changeRotLayout = elements.hBoxLayout(margins=(uic.SREG, 0, uic.SREG, 0),
                                              spacing=uic.SLRG)
        changeRotLayout.addWidget(self.changeRotOrderCombo, 5)
        changeRotLayout.addWidget(self.bakeCheckbox, 1)

        # Main Layout ---------------------------------------
        mainLayout.addWidget(self.rotOrderRadioGrp)
        mainLayout.addLayout(changeRotLayout)
        mainLayout.addWidget(self.changeRotOrderBtn, 1)
