from zoo.libs import iconlib
from zoo.libs.pyqt import utils, uiconstants
from zoo.libs.pyqt.widgets import elements
from zoo.libs.pyqt.widgets import iconmenu
from zoo.preferences.interfaces import coreinterfaces
from zoovendor.Qt import QtCore, QtWidgets


class RigBoxWidget(QtWidgets.QWidget):
    """
    The RigBoxWidget, the box with the combobox. We add, remove and rename our rigs through
    our UI here.
    """
    _addRigIcon = iconlib.iconColorized("plus", size=64)
    _delRigIcon = iconlib.iconColorized("xCircleMark", size=64)
    _renameIcon = iconlib.iconColorized("pencil", size=64)
    _refreshIcon = iconlib.iconColorized("reload3", size=64)

    addRigClicked = QtCore.Signal()
    deleteRigClicked = QtCore.Signal()
    renameClicked = QtCore.Signal()

    def __init__(self, parent=None):
        """

        :param parent:
        :type parent: :class:`zoo.apps.hiveartistui.artistui.HiveArtistUI`
        """
        super(RigBoxWidget, self).__init__(parent)

        self.artistUi = parent

        self.mainLayout = elements.hBoxLayout(self)

        self.themePref = coreinterfaces.coreInterface()
        self.rigComboBox = QtWidgets.QComboBox(parent=self)

        self.rigMenuBtn = iconmenu.IconMenuButton(parent=self)
        self.createBtn = elements.styledButton(parent=self, icon="plus", style=uiconstants.BTN_TRANSPARENT_BG,
                                               toolTip="Create New Rig", themeUpdates=False)
        self.renameBtn = elements.styledButton(parent=self, icon="pencil", style=uiconstants.BTN_TRANSPARENT_BG,
                                               toolTip="Rename Rig", themeUpdates=False)
        self.deleteBtn = elements.styledButton(parent=self, icon="xCircleMark", style=uiconstants.BTN_TRANSPARENT_BG,
                                               toolTip="Delete Rig", themeUpdates=False)

        self.checkRigExists()

        self.initUi()
        self.connections()

    def initUi(self):
        """ Init ui

        :return:
        :rtype:
        """

        self.initButtons()
        self.mainLayout.addWidget(self.rigComboBox)
        # self.mainLayout.addWidget(self.rigMenuBtn)
        self.mainLayout.addWidget(self.createBtn)
        self.mainLayout.addWidget(self.renameBtn)
        self.mainLayout.addWidget(self.deleteBtn)

        self.mainLayout.setStretchFactor(self.rigComboBox, 5)
        self.mainLayout.setSpacing(utils.dpiScale(2))
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setAlignment(QtCore.Qt.AlignTop)
        self.setFixedHeight(utils.dpiScale(18))
        self.rigComboBox.setMinimumWidth(utils.dpiScale(130))

        self.setLayout(self.mainLayout)

    def initButtons(self):
        """ Init buttons

        :return:
        :rtype:
        """
        self.rigMenuBtn.hide()
        self.rigMenuBtn.setIconByName("menudots", colors=self.themePref.MAIN_FOREGROUND_COLOR)
        self.createBtn.leftClicked.connect(self.addRigClicked.emit)
        self.renameBtn.leftClicked.connect(self.renameClicked)
        self.deleteBtn.leftClicked.connect(self.deleteRigClicked.emit)

        self.createBtn.leftClicked.connect(self.checkRigExists)
        self.renameBtn.leftClicked.connect(self.checkRigExists)
        self.deleteBtn.leftClicked.connect(self.checkRigExists)

    def connections(self):
        self.rigComboBox.currentIndexChanged.connect(self.rigComboBoxActivated)

    def checkRigExists(self):
        """ If rig exists, enable buttons

        :return:
        :rtype:
        """
        rigExists = self.artistUi.core.currentRigExists()
        self.renameBtn.setEnabled(rigExists)
        self.deleteBtn.setEnabled(rigExists)

    def rigComboBoxActivated(self, index):
        self.artistUi.setRig(self.rigComboBox.currentText(), apply=self.updatesEnabled())

    def setCurrentIndex(self, index, update=True):
        """ Set current index based on int

        :param index:
        :param update: If true it will set and update the rig in the ui
        :return:
        """
        if update is False:
            self.setUpdatesEnabled(False)

        ret = self.rigComboBox.setCurrentIndex(index)

        if self.updatesEnabled() is False:
            self.setUpdatesEnabled(True)

        return ret

    def currentText(self):
        """
        Get current text for the rig combobox
        :return:
        """

        return self.rigComboBox.currentText()

    def updateList(self, rigList, setTo="", keepSame=False):
        """ Clear out the combobox and update it with the new list of strings rigList.

        :param rigList:
        :type rigList: list of basestring
        :param setTo: Set to this rig when it has finished updating
        :param keepSame: Attempt to set to the rig to the same rig as before the refresh
        :return:
        """

        # Disable updates to the ui since we're just updating the list
        self.setUpdatesEnabled(False)

        # If we want to set it to to the same text
        origIndex = 0
        if keepSame:
            currText = self.rigComboBox.currentText()
            origIndex = self.rigComboBox.findText(currText)

        # Clear and add the items back
        self.rigComboBox.clear()

        self.rigComboBox.addItems(rigList)

        if keepSame:
            # Set to the latest one if we can't find any
            if origIndex >= len(rigList):
                origIndex = len(rigList) - 1

            self.rigComboBox.setCurrentIndex(origIndex)

        elif setTo != "":
            i = rigList.index(setTo)
            if i >= 0:
                self.rigComboBox.setCurrentIndex(i)

        self.setUpdatesEnabled(True)
        self.checkRigExists()

        return self.rigComboBox.currentText()
