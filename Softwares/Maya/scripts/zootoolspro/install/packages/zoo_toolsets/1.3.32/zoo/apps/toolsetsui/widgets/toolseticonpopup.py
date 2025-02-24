import math
from functools import partial

from zoo.libs.utils import application
from zoovendor.Qt import QtCore, QtWidgets

from zoo.libs.pyqt import utils
from zoo.libs.pyqt.widgets import flowlayout
from zoo.libs.pyqt.widgets import elements
from zoo.libs.pyqt.widgets import extendedbutton


class ToolsetIconPopup(elements.ZooWindow):
    """ The toolset icon popup with all the toolsets in a dialog box

    :param toolsetFrame:
    :type toolsetFrame:
    :param parent:
    :type parent:
    :param width:
    :type width: int
    :param height:
    :type height: int
    :param iconSize:
    :type iconSize: int
    :param toolsetRegistry:
    :type toolsetRegistry:  zoo.apps.toolsetsui.registry.ToolsetRegistry
    """

    def __init__(self, toolsetFrame, toolsetRegistry=None,
                 parent=None, width=160, height=400, iconSize=20):

        name = "ToolsetList"
        super(ToolsetIconPopup, self).__init__(name=name + "menu", title=name,
                                               parent=application.mainWindow(),
                                               resizable=False,
                                               width=width, height=height, modal=False, alwaysShowAllTitle=False,
                                               minButton=False, maxButton=False, onTop=True, saveWindowPref=False,
                                               titleBar=None, overlay=True, minimizeEnabled=False,
                                               initPos=None)
        self.titleBar.setVisible(False)

        self.toolsetFrame = toolsetFrame  # Tool
        self.toolsetRegistry = toolsetRegistry
        self.iconRowSpacing = utils.dpiScale(5)
        self.btnColumns = 8
        self.iconSize = iconSize
        self.buttons = []
        self.searchEdit = QtWidgets.QLineEdit(self)  # todo: switch to stringEdit
        self.tearOffWidget = TearOffWidget(parent=self)
        self.nameLabel = elements.Label(parent=self, enableMenu=False)

        self.initUi()
        self.connections()

    def connections(self):
        """ UI Connections

        :return:
        """
        self.tearOffWidget.clicked.connect(partial(self.setTearOff, True))

    def setButtonColumns(self, col):
        self.btnColumns = col

    def initUi(self):
        self.iconLayout = flowlayout.FlowLayout(spacingX=1, spacingY=2)
        self.parentContainer.setWindowFlags(self.parentContainer.windowFlags() | QtCore.Qt.Popup)
        self.initSearchEdit()
        self.nameLabel.setIndent(utils.dpiScale(3))
        mainLayout = elements.vBoxLayout(margins=(0, 0, 0, 0), spacing=1)
        self.setMainLayout(mainLayout)

        self._iconFlowLayout()
        # Contents Layout
        contentsLayout = elements.vBoxLayout(margins=(0, 0, 0, 0), spacing=0)
        contentsLayout.setSpacing(utils.dpiScale(5))

        contentsLayout.addWidget(self.nameLabel)
        contentsLayout.addLayout(self.iconLayout)
        # Main Layout settings
        mainLayout.addWidget(self.tearOffWidget)
        mainLayout.addWidget(self.searchEdit)
        mainLayout.addLayout(contentsLayout)
        mainLayout.addItem(elements.Spacer(20, 20, vMin=QtWidgets.QSizePolicy.Expanding))

    def _sizeHint(self):
        """ Change the size hint to resize based on the buttons in the icon popup.

        .. note::
            Because this is a zooWindow the size has to be set on the parentContainer, so we don't
            override `sizeHint`method we simply set the parentContainer size on show


        :return:
        """
        if not hasattr(self, "buttons"):
            return QtCore.QSize()
        buttonHeight = 0
        buttonWidth = 0
        if self.buttons:
            buttonHeight = self.buttons[0].sizeHint().height()
            buttonWidth = self.buttons[0].sizeHint().width()
        rows = math.ceil(len(self.buttons) / self.btnColumns)
        spacingX = self.iconLayout.spacingX
        spacingY = self.iconLayout.spacingY
        width = (buttonWidth * (self.btnColumns + 1)) + (spacingX * self.btnColumns + 1)

        height = (buttonHeight * rows + 1) + (spacingY * (rows + 1))

        return QtCore.QSize(width,
                            height + self.titleBar.height() +
                            self.tearOffWidget.height() +
                            self.searchEdit.height() + self.resizerHeight())

    def initSearchEdit(self):
        """ Search edit to filter out the button

        :return:
        """

        self.searchEdit.setPlaceholderText("Search...")
        self.searchEdit.textChanged.connect(self.updateSearch)

    def setTearOff(self, tearOff):
        """ Set Tear Off

        Tear off the window and add its window frame back if tearOff is true, otherwise turn it back into a
        popup

        :param tearOff:
        """
        size = self._sizeHint()
        if tearOff:
            self.tearOffWidget.setVisible(False)
            self.titleBar.setVisible(True)
            self.parentContainer.setWindowFlags(self.parentContainer.defaultWindowFlags)
            self.parentContainer.resize(size.width(), size.height())
            # do show here as this condition body is run by click the tear off button
            self.show()
        else:
            self.tearOffWidget.setVisible(True)
            self.titleBar.setVisible(False)
            self.parentContainer.setWindowFlags(self.parentContainer.windowFlags() | QtCore.Qt.Popup)
            self.parentContainer.resize(size.width(), size.height())

    def updateSearch(self, searchString):
        """ Filter buttons by search string

        :param searchString:
        """
        searchString = searchString or ""
        for b in self.buttons:
            if searchString.lower() in b.name.lower() or searchString == "":
                b.show()
            else:
                b.hide()

    def _iconFlowLayout(self):
        """ Icon flow layout for the buttons

        :return:
        """

        self.iconLayout.setContentsMargins(0, 0, 0, 0)

        for g in self.toolsetRegistry.groupsData():
            groupType = g['type']
            toolsets = self.toolsetRegistry.toolsets(groupType)

            for t in toolsets:
                btn = self._newButton(t)

                self.buttons.append(btn)
                self.iconLayout.addWidget(btn)

        return self.iconLayout

    def _newButton(self, toolset):
        """ Add a new button sets the settings and return so we can add it to the group

        :param toolset:
        :return:
        """
        color = self.toolsetRegistry.toolsetColor(toolset.id)
        btn = ToolsetIconButton(toolset.uiData['icon'], color, toolset.uiData['label'])
        btn.onMousedEnter.connect(self._onEnterButton)
        btn.onMousedLeave.connect(self._onLeaveButton)
        btn.setToolTip(toolset.uiData['label'])
        btn.setProperty('color', color)
        btn.setProperty('toolsetId', toolset.id)
        activated = True
        btn.leftClicked.connect(partial(self.toolsetFrame.toggleToolset, toolset.id, activated))
        btn.middleClicked.connect(partial(self.toolsetFrame.toggleToolset, toolset.id, not activated))

        btn.setIconSize(QtCore.QSize(self.iconSize, self.iconSize))
        return btn

    def show(self, move=None):
        self.searchEdit.setText("")
        self.searchEdit.setFocus()
        super(ToolsetIconPopup, self).show(move)

    def _onEnterButton(self):
        self.nameLabel.setText(self.sender().name)

    def _onLeaveButton(self):
        self.nameLabel.setText("")

    def updateColors(self, actives):
        """ Updates colors based on if it's active or not. Generally becomes dark if it is active

        :param actives: List of toolsetIds
        :type actives: list[str]
        """
        for item in self.iconLayout.items():
            wgt = item.widget()
            if wgt.property('toolsetId') in actives:
                wgt.setIconColor((120, 120, 120))
            else:
                wgt.setIconColor(tuple(wgt.property('color')))


class TearOffWidget(QtWidgets.QPushButton):
    """
    Tear off widget, so we can detach the menu and turn it into a popup dialog
    """

    def __init__(self, parent=None):
        super(TearOffWidget, self).__init__(parent=parent)
        self.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Fixed)
        self.initUi()

    def initUi(self):
        self.setFixedHeight(utils.dpiScale(15))

        # Tear off pattern
        patternChars = ":::::::"
        dottedPattern = ""
        for i in range(1, 50):
            dottedPattern += patternChars
        self.setText(dottedPattern)


class ToolsetIconButton(extendedbutton.ExtendedButton):
    """ Toolset Icon Button

    The icon button that represents a toolset. When moused over it will
    change the label based on the name

    Example:

    .. code-block: python

        btn = ToolsetIconButton("magic", color=(255,255,255), "my name")

    """
    onMousedEnter = QtCore.Signal()
    onMousedLeave = QtCore.Signal()

    def __init__(self, iconName, color, name):
        super(ToolsetIconButton, self).__init__()
        self.setIconByName(iconName, colors=color, size=24, colorOffset=50)
        self.name = name

    def enterEvent(self, event):
        super(ToolsetIconButton, self).enterEvent(event)
        self.onMousedEnter.emit()

    def leaveEvent(self, event):
        super(ToolsetIconButton, self).leaveEvent(event)
        self.onMousedLeave.emit()
