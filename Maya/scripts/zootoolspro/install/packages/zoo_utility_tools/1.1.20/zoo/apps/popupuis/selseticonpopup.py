"""Popup windows for selection sets.

Example use:

.. code-block:: python

    # Opens the Selection Set Icon Popup window
    from zoo.apps.popupuis import selseticonpopup
    selseticonpopup.iconWindow()

    # Opens the Create Selection Set Popup
    from zoo.apps.popupuis import selseticonpopup
    selseticonpopup.createSelectionSetWindow()

Author: Andrew Silke
"""

import random
from functools import partial

from zoovendor.Qt import QtGui
from zoo.libs.pyqt.widgets import elements
from zoo.libs.pyqt import uiconstants as uic
from zoovendor.Qt import QtWidgets, QtCore
from zoo.apps.toolsetsui import toolsetui
from zoo.libs.pyqt import utils
from zoo.libs.iconlib import iconlib

from zoo.libs.maya.cmds.sets import selectionsets

WINDOW_WIDTH = 245
WINDOW_WIDTH_CREATE = 300
WINDOW_HEIGHT = 180
WINDOW_OFFSET_Y = -10


class SelSetsIconPopup(elements.ZooWindowThin):

    def __init__(self, name="", title="", parent=None, resizable=True, width=WINDOW_WIDTH, height=WINDOW_HEIGHT,
                 modal=False, alwaysShowAllTitle=False, minButton=False, maxButton=False, onTop=False,
                 saveWindowPref=False, titleBar=None, overlay=True, minimizeEnabled=True, initPos=None, qtPopup=False,
                 coloredIcons=True, imageIcons=True, iconsOnly=True):
        super(SelSetsIconPopup, self).__init__(name, title, parent, resizable, width, height, modal, alwaysShowAllTitle,
                                               minButton, maxButton, onTop, saveWindowPref, titleBar, overlay,
                                               minimizeEnabled, initPos)
        self.iconsOnly = iconsOnly

        if qtPopup:
            self.parentContainer.setWindowFlags(self.parentContainer.defaultWindowFlags | QtCore.Qt.Popup)

        self.iconBtnList = list()
        self.iconList = list()

        if coloredIcons:
            colors = ["Aqua", "Blue", "Purple", "Pink", "Red", "Orange", "Yellow", "Green"]
            shapes = ["st_pentagon", "st_circle", "st_triangle", "st_square", "st_star"]
            for shape in shapes:
                for col in colors:
                    self.iconList.append("".join([shape, col]))

        self.primaryIcon = random.choice(self.iconList)

        if imageIcons:
            whiteIconsRow1 = ["st_man", "st_faceWoman", "st_faceMan", "st_faceSmiley", "st_eye", "st_lips", "st_ear",
                              "st_thumb"]
            whiteIconsRow2 = ["st_hand", "st_thumb", "st_foot", "st_footShoe", "st_paw", "st_arm", "st_leg", "st_pants"]
            whiteIconsRow3 = ["st_fish", "st_robot", "st_cat", "st_dog", "st_wing", "st_tentacle", "st_hair",
                              "st_skirt"]
            whiteIconsRow4 = ["st_fish", "st_thumb", "st_foot", "st_footShoe", "st_paw", "st_arm", "st_leg", "st_pants"]

            self.iconList += whiteIconsRow1 + whiteIconsRow2 + whiteIconsRow3 + whiteIconsRow4

        self.widgets()
        self.layout()

        if not imageIcons:  # Set the focus and select the text to the setName text entry
            self.setName.setFocus()
            self.setName.selectAll()

    # -------------
    # COMMANDS
    # -------------

    def setIconByName(self, iconName):
        """Sets the icon from a string name"""
        icon = iconlib.Icon.icon(iconName, size=utils.dpiScale(32))
        self.mainIconBtn.setIcon(icon)
        self.mainIconBtn.setText(iconName)

    def sendIconName(self, iconName):
        """Sends the icon to toolset UIs (selection set)

        :param iconName: The name of the icon
        :type iconName: str
        """
        if not self.iconsOnly:
            self.setIconByName(iconName)
        else:
            toolsets = toolsetui.toolsetsByAttr(attr="global_receiveIcon")
            for tool in toolsets:
                tool.global_receiveIcon(iconName)

    def createSelSet(self):
        """Creates a selection set based on the UI settings"""
        iconText = self.mainIconBtn.text()
        selectionsets.createSelectionSetZooSel(self.setName.text(),
                                               icon=iconText,
                                               visibility=self.visibleCheckbox.isChecked(),
                                               priority=self.priorityText.value(),
                                               soloParent=True,
                                               selectionSet=not self.setModeRadio.checkedIndex())
        self.close()

    # ------------------------------------
    # UNDO CHUNKS
    # ------------------------------------

    # -------------
    # CREATE WIDGETS
    # -------------

    def makeButton(self, name):
        btn = QtWidgets.QToolButton(parent=self)
        iconSize = utils.dpiScale(16)
        icon = iconlib.Icon.icon(name, size=utils.dpiScale(32))
        btn.setIcon(icon)
        btn.setText(name)
        btn.setToolTip(name)
        btn.setMinimumSize(QtCore.QSize(iconSize, iconSize))
        btn.setIconSize(QtCore.QSize(iconSize, iconSize))
        return btn

    def widgets(self):
        """Build the widgets"""
        # icon table --------------
        for iconName in self.iconList:
            btn = self.makeButton(iconName)
            self.iconBtnList.append(btn)
            btn.clicked.connect(partial(self.sendIconName, iconName))

        if self.iconsOnly:  # only build the icons not the create options.
            return

        # Label and text -------------
        self.mainIconBtn = self.makeButton(self.primaryIcon)

        toolTip = "Enter the name of the set to be created, and set an icon."
        self.labelName = elements.Label(text="Set Name & Icon: ", toolTip=toolTip)
        self.setName = elements.StringEdit(label="", editText="Set", toolTip=toolTip)
        self.mainIconBtn.setToolTip(toolTip)

        # Create Visible checkbox -----------------
        toolTip = "Sets the visibility of the Selection Set in the Zoo \n" \
                  "Selection Set Marking Menu. \n\n" \
                  "Zoo Selection Marking Menu: u (press hold) left-click"
        self.visibleCheckbox = elements.CheckBox("Marking Menu Vis",
                                                 checked=True,
                                                 right=True,
                                                 toolTip=toolTip)

        # Set MM Priority -----------------
        toolTip = "The priority level of the set for cycling in the Zoo Marking Menu. \n" \
                  "A higher number makes the set more selectable while cycling. \n\n" \
                  "Cycle Sets Zoo Hotkey: u (tap/release) & repeat"
        self.priorityText = elements.IntEdit(label="Set MM Priority",
                                             editText=0,
                                             toolTip=toolTip,
                                             editRatio=14,
                                             labelRatio=10)

        # Create Object/Selection Set Radio -----------------
        toolTip = "Create a `Selection Set` or an `Object Set`. \n" \
                  "Note: Object Sets are not seen in the Zoo Selection \n" \
                  "Set Menu and do not have icon settings."
        self.setModeRadio = elements.RadioButtonGroup(radioList=["Selection Set", "Object Set"],
                                                      default=0,
                                                      toolTipList=[toolTip, toolTip],
                                                      margins=[uic.REGPAD, uic.REGPAD, uic.REGPAD, uic.LRGPAD])

        # Bottom Create buttons --------------
        toolTip = "Create a set that will appear in the Outliner window."
        self.createBtn = elements.styledButton("Create Set",
                                               "sets",
                                               toolTip=toolTip,
                                               style=uic.BTN_DEFAULT)
        toolTip = "Cancel and close the window."
        self.cancelBtn = elements.styledButton("Cancel",
                                               "xCircleMark",
                                               toolTip=toolTip,
                                               style=uic.BTN_DEFAULT)
        self.createBtn.clicked.connect(self.createSelSet)
        self.cancelBtn.clicked.connect(self.close)

    # -------------
    # LAYOUT UI
    # -------------

    def layout(self):
        """Layout the widgets into the window"""
        self.mainLayout = elements.vBoxLayout(spacing=0,
                                              margins=(uic.REGPAD, uic.REGPAD, uic.REGPAD, uic.REGPAD))
        if not self.iconsOnly:
            # New Set String Layout -----------------
            labelLayout = elements.hBoxLayout(spacing=uic.SREG,
                                              margins=(uic.REGPAD, uic.SMLPAD, uic.REGPAD, 8))
            labelLayout.addWidget(self.labelName, 1)
            # New Set String Layout -----------------
            setNameLayout = elements.hBoxLayout(spacing=uic.SREG,
                                                margins=(uic.REGPAD, 0, uic.REGPAD, uic.REGPAD))
            setNameLayout.addWidget(self.mainIconBtn, 1)
            setNameLayout.addWidget(self.setName, 100)

        # Icon Layout --------------------
        if self.iconsOnly:
            topBotPad = 0
        else:
            topBotPad = uic.LRGPAD

        iconGridLayout = elements.GridLayout(margins=(0, topBotPad, 0, topBotPad))
        row = 0
        col = 0
        for i, btn in enumerate(self.iconBtnList):
            if col == 8:
                col = 0
                row += 1
            iconGridLayout.addWidget(btn, row, col)
            col += 1

        if not self.iconsOnly:
            # visPriority layout -----------------
            visPriorityLayout = elements.hBoxLayout(spacing=uic.SREG,
                                                    margins=(uic.REGPAD, uic.REGPAD, uic.REGPAD, uic.SMLPAD))
            visPriorityLayout.addWidget(self.visibleCheckbox, 1)
            visPriorityLayout.addWidget(self.priorityText, 1)

            # Create/Cancel Layout -----------------
            createCancelLayout = elements.hBoxLayout(spacing=uic.SPACING,
                                                     margins=(0, uic.LRGPAD, 0, uic.SMLPAD))
            createCancelLayout.addWidget(self.createBtn, 1)
            createCancelLayout.addWidget(self.cancelBtn, 1)

        # Main Layout ------------------
        if not self.iconsOnly:
            self.mainLayout.addLayout(labelLayout)
            self.mainLayout.addLayout(setNameLayout)
            self.mainLayout.addWidget(elements.Divider())

        self.mainLayout.addLayout(iconGridLayout)

        if not self.iconsOnly:
            self.mainLayout.addWidget(elements.Divider())
            self.mainLayout.addLayout(visPriorityLayout)
            self.mainLayout.addWidget(self.setModeRadio)
            self.mainLayout.addWidget(elements.Divider())
            self.mainLayout.addLayout(createCancelLayout)

        self.setMainLayout(self.mainLayout)


def show(win, width, offsetY):
    """Show and place the windows position"""
    offsetX = int(-width / 2)
    point = QtGui.QCursor.pos()
    point.setX(point.x() + offsetX)
    point.setY(point.y() + offsetY)
    win.show(point)


def iconWindow(coloredIcons=True, imageIcons=True):
    """Open the window"""
    win = SelSetsIconPopup(width=WINDOW_WIDTH, coloredIcons=coloredIcons, imageIcons=imageIcons, iconsOnly=True,
                           modal=False)
    show(win, WINDOW_WIDTH, WINDOW_OFFSET_Y)


def createSelectionSetWindow(coloredIcons=True, imageIcons=False):
    """Open the window"""
    win = SelSetsIconPopup(width=WINDOW_WIDTH_CREATE, coloredIcons=coloredIcons, imageIcons=imageIcons, iconsOnly=False,
                           modal=True)
    show(win, WINDOW_WIDTH_CREATE, WINDOW_OFFSET_Y)


if __name__ == "__main__":
    createSelectionSetWindow()
