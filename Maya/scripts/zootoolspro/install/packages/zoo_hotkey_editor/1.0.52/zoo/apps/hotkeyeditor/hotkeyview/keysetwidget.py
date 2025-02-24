from zoovendor.Qt import QtCore, QtWidgets

from zoo.apps.hotkeyeditor.core import keysets
from zoo.apps.hotkeyeditor.core import utils
from zoo.core.util import zlogging
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements
from zoo.libs.utils import output

logger = zlogging.getLogger(__name__)


class KeySetWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(KeySetWidget, self).__init__(parent)

        self.hotkeyView = self.parent()
        self.keySetManager = self.hotkeyView.keySetManager

        self.newSetBtn = elements.styledButton(icon="plus", parent=self, toolTip="Create new hotkey set",
                                               style=uic.BTN_TRANSPARENT_BG)
        self.deleteSetBtn = DeleteSetButton(parent=self)
        self.keySetCombo = elements.ComboBoxRegular.setupComboBox(items=(self.keySetManager.keySetNames()),
                                                                  parent=self,
                                                                  toolTip="Choose a hotkey set")

        self.initUi()
        self.connections()

        self._setUpKeySet()

        # Disable the delete button if the keyset is locked
        current = self.keySetCombo.currentText()
        if self.keySetManager.isKeySetLocked(current):
            self.deleteSetBtn.setEnabled(False)

    def initUi(self):
        keySetLayout = elements.hBoxLayout(self, margins=(0, 2, 0, 2), spacing=uic.SSML)

        keySetLayout.addWidget(self.keySetCombo)
        keySetLayout.addItem(elements.Spacer(5, 0))
        keySetLayout.addWidget(self.newSetBtn)
        keySetLayout.addWidget(self.deleteSetBtn)
        keySetLayout.addStretch(1)

        self.setLayout(keySetLayout)

    def connections(self):
        self.newSetBtn.leftClicked.connect(self.newKeySet)
        # self.applySetBtn.clicked.connect(self.applySetClicked)
        self.keySetCombo.activated.connect(self.keySetComboSwitch)

        self.deleteSetBtn.leftClicked.connect(self.deleteKeySet)

    def keySetComboSwitch(self):
        switchSet = self.keySetCombo.currentText()
        self.keySetUiSwitch(switchSet)
        self.applySet(switchSet)

    def keySetUiSwitch(self, name):
        current = self.keySetManager.setActive(name)
        logger.info("Switching to \"{}\"".format(current.keySetName))
        self.hotkeyView.setKeySet(current)
        self.setComboToText(self.keySetCombo, name)

        # Don't allow the user to delete things in ui
        current = self.keySetCombo.currentText()
        if self.keySetManager.isKeySetLocked(current):
            self.deleteSetBtn.setEnabled(False)
        else:
            self.deleteSetBtn.setEnabled(True)

        # For admin mode allow a few things
        if not self.keySetManager.isKeySetLocked(current) or utils.isAdminMode():
            self.hotkeyView.setHotkeyUiEnabled(True)
        elif self.keySetManager.isKeySetLocked(current):
            self.hotkeyView.setHotkeyUiEnabled(False)

        # Make sure the revert button is enabled properly
        self.hotkeyView.updateRevertUi()

    def applySet(self, setName):
        # Maybe should move this to hotkeyView
        self.keySetManager.setActive(setName, install=True)
        # self.hotkeyView.setActiveLabel(setName)

    def _setUpKeySet(self):
        current = self.keySetManager.currentKeySet(forceMaya=False)
        if current is not None:
            self.keySetUiSwitch(current.keySetName)
            self.applySet(current.keySetName)
            self.setComboToText(self.keySetCombo, current.prettyName)

    def setComboToText(self, combo, text):
        """ Sets the index based on the text

        :param combo:
        :param text: Text to search and switch item to.
        :return:
        """
        index = combo.findText(text, QtCore.Qt.MatchFixedString)
        if index >= 0:
            combo.setCurrentIndex(index)

    def newKeySet(self):
        # Note parenting to None to inherit from Maya and fix stylesheet issues
        ret = elements.MessageBox.inputDialog(parent=self, title='Enter Set Name',
                                              message='Please enter a name for the new hotkey set:',
                                              text="")

        if ret is not None:
            # Check to see if it exists first.
            if ret == "":
                logger.warning("Name can't be empty! Cancelling operation.")
                return

            if self.keySetManager.newKeySet(ret) is False:
                logger.warning("{} already exists! Cancelling operation.".format(ret))
                return

            self.updateKeySets(ret)

    def deleteKeySet(self):
        """ Delete key set

        :return:
        :rtype:
        """

        if self.deleteSetBtn.enabled:

            current = self.keySetCombo.currentText()

            # Note parenting to None to inherit from Maya and fix stylesheet issues
            ret = elements.MessageBox.showWarning(
                None,
                'Are You Sure?',
                'Are you sure you want to delete Key Set: \n\n{}'.format(current),
                buttonA="Yes",
                buttonB="Cancel")

            if ret == "A":
                logger.info("Yes was clicked")

                self.keySetManager.deleteKeySet(current)
                self.updateKeySets(keysets.KeySetManager.defaultKeySetName)
                self.hotkeyView.keySetCleanUp()
                self.keySetComboSwitch()

            elif ret == "B":
                logger.info("cancel was clicked")
        else:
            output.displayWarning(
                "Default Hotkey sets are locked cannot be deleted here. You may delete them in Zoo Preferences.")

    def updateKeySets(self, setToName=""):
        """ Update the keysets. Usually run when there's been a change to the keysets
        :param setToName: Set the combo box to the name

        """
        self.keySetCombo.clear()
        self.keySetCombo.addItems(self.keySetManager.keySetNames())

        if setToName != "":
            index = self.keySetCombo.findText(setToName, QtCore.Qt.MatchFixedString)
            self.keySetCombo.setCurrentIndex(index)
            self.keySetComboSwitch()
            self.hotkeyView.sourceCombo.updateSources()


class DeleteSetButton(elements.ExtendedButton):
    icon = "trash"

    def __init__(self, parent=None):
        """ Override set enabled so we can print something when it is clicked

        :param parent:
        :type parent:
        """
        self.enabled = True

        super(DeleteSetButton, self).__init__(parent=parent)

        self.setIconByName(self.icon)
        self.setToolTip("Delete the current hotkey set")

    def setEnabled(self, enabled):
        if enabled:
            self.setIconColor((255, 255, 255))
        else:
            self.setIconColor((128, 128, 128))

        self.enabled = enabled
