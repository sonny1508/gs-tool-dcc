""" ---------- Replace Shapes -------------

- Replaces/copies shape nodes to multiple objects with instancing options

Author: Andrew Silke
"""
from zoovendor.Qt import QtWidgets

from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements

from zoo.libs.utils import output
from zoo.apps.replaceshapenodes import replaceshapenodes

from zoo.libs.maya.cmds.objutils import shapenodes, objhandling

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1


class ReplaceShapes(toolsetwidget.ToolsetWidget):
    id = "replaceShapes"
    info = "Replace shape nodes on multiple objects."
    uiData = {"label": "Replace Shapes",
              "icon": "swapModel",
              "tooltip": "Replace shape nodes on multiple objects.",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-replace-shapes/"}

    # ------------------
    # STARTUP
    # ------------------

    def contents(self):
        """The UI Modes to build, compact, medium and or advanced """
        return [self.initCompactWidget(), self.initAdvancedWidget()]  #

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
        return super(ReplaceShapes, self).currentWidget()

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiAdvanced or GuiCompact]
        """
        return super(ReplaceShapes, self).widgets()

    # ------------------
    # POPUP
    # ------------------

    def resetFreezePopup(self, objList):
        """The popup window asking the user if they'd like to remove the freeze.
        """
        endMessage = "Try to remove the frozen offsets? (usually recommended). \n\n" \
                     "The `Match Pivot Space` button in the `Replace Shapes` UI can also fix this issue, see the " \
                     "`Replace Shapes` help page for more information."
        if len(objList) < 4:
            message = "Object/s `{}` transforms have been frozen, and may not shape parent as expected.  \n\n" \
                      "{}".format(objList, endMessage)
        else:
            message = "Many of the selected transforms have been frozen, and may not shape parent as expected.  \n\n" \
                      "{}".format(endMessage)
        return elements.MessageBox.showQuestion(parent=None,
                                                title="Remove Freeze?",
                                                message=message,
                                                buttonA="Remove Freeze",
                                                buttonB="Continue No freeze",
                                                buttonC="Cancel Operation",
                                                buttonIconA=elements.MessageBox.okIcon,
                                                buttonIconB="arrowStandardRight",
                                                buttonIconC=elements.MessageBox.cancelIcon)  # Parent None parents Maya

    # ------------------
    # LOGIC
    # ------------------

    @toolsetwidget.ToolsetWidget.undoDecorator
    def matchPivotSpace(self):
        """Matches the first selected object to the second selected objects rot and scale pivot attributes
        Requires that the first object does not have incoming connections.
        """
        objhandling.matchPivotSpaceSelection()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def unfreeze(self):
        """Tries to unfreeze the selected objects.   This will fix some issues related to replacing shape nodes.
        """
        objhandling.removeFreezeTransformSelected()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def uninstance(self):
        """Uninstances the selected objects
        """
        objhandling.uninstanceSelected()

    def addMasterObj(self):
        """Adds a surface object to the UI from the scene"""
        # todo: should support zapi and long names
        geo = shapenodes.setShapeReparentObj()
        if not geo:
            return
        self.properties.masterObjectTxt.value = geo
        self.updateFromProperties()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def replaceShapes(self):
        """constraints.constrainObjsToSurfaceSelection(surface=self.properties.placeOnSurfaceTxt.value,
                                                    deleteConstraint=True)"""
        extraObjects = []
        masterObj = self.properties.masterObjectTxt.value
        if masterObj:
            extraObjects = [masterObj]

        # Check if the rotate pivots don't match, if they match then fine continue -----------
        if not objhandling.checkRotatePivMatchSelection(
                extraObjects=extraObjects):  # the objects rotate pivots don't match
            frozenTransforms = objhandling.checkFrozenTransformOffsetSelected(extraObjects=extraObjects)
            if frozenTransforms:  # Then should try and remove the freeze
                result = self.resetFreezePopup(frozenTransforms)  # UI popup --------------
                if result == "A":  # Then try to remove frozen transforms, will report warnings if can't
                    objhandling.removeFreezeTransformList(frozenTransforms)
                elif result == "C":
                    output.displayInfo("The replace operation has been canceled.")
                    return

        # Do the replace --------------------------------------
        replaceshapenodes.shapeNodeParentSelected(masterObj=self.properties.masterObjectTxt.value,
                                                  replace=self.properties.replaceCheckBox.value,
                                                  message=True,
                                                  selectLastObj=False,
                                                  deleteMaster=self.properties.deleteOriginalCheckBox.value,
                                                  objSpaceParent=True,
                                                  instance=self.properties.instanceCheckBox.value,
                                                  keepShaders=self.properties.keepShadersCheckBox.value)

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        for widget in self.widgets():
            widget.replaceShapeBtn.clicked.connect(self.replaceShapes)
            widget.matchPivotSpaceBtn.clicked.connect(self.matchPivotSpace)
            widget.unfreezeBtn.clicked.connect(self.unfreeze)
            widget.selectMasterBtn.clicked.connect(self.addMasterObj)
            widget.uninstanceeBtn.clicked.connect(self.uninstance)


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
        # Instance Checkbox ---------------------------------------
        toolTip = "Will instance the new shape nodes being copied instead of duplicating."
        self.instanceCheckBox = elements.CheckBox("Instance Shape Nodes", checked=False, toolTip=toolTip)
        # Keep Shaders Checkbox ---------------------------------------
        toolTip = "Keeps the existing shaders of the original objects as they are replaced."
        self.keepShadersCheckBox = elements.CheckBox("Keep Target Shaders", checked=False, toolTip=toolTip)
        # Replace Checkbox ---------------------------------------
        toolTip = "If on will replace the existing shape nodes of the target object \n" \
                  "by deleting the existing shape nodes. \n" \
                  "If off, the existing shape nodes will remain and there will be multiple \n" \
                  "shape nodes under the target objects."
        self.replaceCheckBox = elements.CheckBox("Replace Existing Shapes", checked=True, toolTip=toolTip)
        # Instance Checkbox ---------------------------------------
        toolTip = "Will delete the `Master Object` after the replace is run."
        self.deleteOriginalCheckBox = elements.CheckBox("Delete Original Object", checked=False, toolTip=toolTip)
        # Master Object Text ---------------------------------------
        toolTip = "This object will be copied or replaced to other selected objects. \n" \
                  "If left empty the first selected object will be the `Master Object`. "
        self.masterObjectTxt = elements.StringEdit(label="",
                                                   editPlaceholder="Master Object",
                                                   editText="",
                                                   toolTip=toolTip)
        # Master Object Button ---------------------------------------
        toolTip = "Enter the Master Object into the UI. \n" \
                  "Select an object and press."
        self.selectMasterBtn = elements.styledButton("",
                                                     "arrowLeft",
                                                     toolTip=toolTip,
                                                     style=uic.BTN_TRANSPARENT_BG,
                                                     minWidth=15)
        # Match Pivot Space Button ---------------------------------------
        toolTip = "Matches an object's `rotation-pivot` to another. \n" \
                  "Useful for fixing shape replace issues. \n\n" \
                  "- Select two objects, the first object will be matched to the second. \n\n" \
                  "The first object must not have incoming connections."
        self.matchPivotSpaceBtn = elements.AlignedButton("Match Pivot Space",
                                                         icon="matchObjects",
                                                         toolTip=toolTip)
        # Unfreeze Button ---------------------------------------
        toolTip = "Unfreezes selected objects. \n" \
                  "Fixes issues related to replacing shape nodes. \n" \
                  "Objects must have no incoming connections and cannot be referenced. "
        self.unfreezeBtn = elements.AlignedButton("Unfreeze Objects",
                                                  icon="unFreeze",
                                                  toolTip=toolTip)
        # Remove Instance Button ---------------------------------------
        toolTip = "Removes the instances on the selected objects. \n" \
                  "Objects will become regular objects. "
        self.uninstanceeBtn = elements.AlignedButton("Uninstance Selected",
                                                     icon="crossXFat_64",
                                                     toolTip=toolTip)
        # Replace Shape Button ---------------------------------------
        toolTip = "Will copy/replace shape nodes to selected other objects. \n\n" \
                  "Option A: Select the object to copy/replace and shift-select \n" \
                  "the target objects you wish replace and run. \n\n" \
                  "Option B: Add the copy/replace object into the UI as the Master Object, \n" \
                  "then select the objects you wish to replace and run.\n\n" \
                  "Note: Entering a Master Object overrides the `Option A` selection method. \n\n" \
                  "Note: Replacing already instanced objects can cause slowdown.  Remove instances \n" \
                  "before replacing. "
        self.replaceShapeBtn = elements.styledButton("Replace Shape Nodes",
                                                     icon="swapModel",
                                                     toolTip=toolTip,
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
        # Compact Checkbox Layout ---------------------------------------
        compactCheckboxLayout = elements.hBoxLayout(margins=(uic.SREG, uic.SREG, uic.SREG, uic.SREG))
        compactCheckboxLayout.addWidget(self.instanceCheckBox, 1)
        compactCheckboxLayout.addWidget(self.keepShadersCheckBox, 1)
        # SurfaceTextLayout -------------------------
        replaceShapeLayout = elements.hBoxLayout(spacing=uic.SPACING)
        replaceShapeLayout.addWidget(self.masterObjectTxt, 9)
        replaceShapeLayout.addWidget(self.selectMasterBtn, 1)
        # Grid Layout -----------------------------
        gridLayout = elements.GridLayout(spacing=uic.SPACING)
        row = 0
        gridLayout.addWidget(self.matchPivotSpaceBtn, row, 0)
        gridLayout.addWidget(self.unfreezeBtn, row, 1)
        row += 1
        gridLayout.addLayout(replaceShapeLayout, row, 0)
        gridLayout.addWidget(self.uninstanceeBtn, row, 1)
        row += 1
        gridLayout.addWidget(self.replaceShapeBtn, row, 0, 1, 2)
        # Add To Main Layout ---------------------------------------
        mainLayout.addLayout(compactCheckboxLayout)
        mainLayout.addLayout(gridLayout)


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
        # Compact Checkbox Layout ---------------------------------------
        compactCheckboxLayout = elements.hBoxLayout(margins=(uic.SREG, uic.SREG, uic.SREG, uic.SREG))
        compactCheckboxLayout.addWidget(self.instanceCheckBox, 1)
        compactCheckboxLayout.addWidget(self.keepShadersCheckBox, 1)
        # Advanced Checkbox Layout ---------------------------------------
        advancedCheckboxLayout = elements.hBoxLayout(margins=(uic.SREG, uic.SREG, uic.SREG, uic.SREG))
        advancedCheckboxLayout.addWidget(self.replaceCheckBox, 1)
        advancedCheckboxLayout.addWidget(self.deleteOriginalCheckBox, 1)
        # SurfaceTextLayout -------------------------
        replaceShapeLayout = elements.hBoxLayout(spacing=uic.SPACING)
        replaceShapeLayout.addWidget(self.masterObjectTxt, 9)
        replaceShapeLayout.addWidget(self.selectMasterBtn, 1)
        # Grid Layout -----------------------------
        gridLayout = elements.GridLayout(spacing=uic.SPACING)
        row = 0
        gridLayout.addWidget(self.matchPivotSpaceBtn, row, 0)
        gridLayout.addWidget(self.unfreezeBtn, row, 1)
        row += 1
        gridLayout.addLayout(replaceShapeLayout, row, 0)
        gridLayout.addWidget(self.uninstanceeBtn, row, 1)
        row += 1
        gridLayout.addWidget(self.replaceShapeBtn, row, 0, 1, 2)
        # Add To Main Layout ---------------------------------------
        mainLayout.addLayout(compactCheckboxLayout)
        mainLayout.addLayout(advancedCheckboxLayout)
        mainLayout.addLayout(gridLayout)
