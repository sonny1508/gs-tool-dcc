from maya import cmds

from zoovendor.Qt import QtWidgets, QtCore, QtGui

from zoo.apps.preferencesui import prefmodel
from zoo.apps.hotkeyeditor.core import keysets
from zoo.apps.hotkeyeditor.core import const as c

from zoo.libs.pyqt.widgets import elements
from zoo.libs.pyqt import uiconstants as uic
from zoo.apps.hotkeyeditor.core import admin
from zoo.apps.hotkeyeditor.core import utils as hotkeyutils
from zoo.core.util import zlogging
from zoo.libs.utils import output

logger = zlogging.getLogger(__name__)


class HotkeyPrefsWidget(prefmodel.SettingWidget):
    categoryTitle = "zoo hotkey editor"

    def __init__(self, parent=None, setting=None):
        super(HotkeyPrefsWidget, self).__init__(parent, setting)
        self.keysetManager = keysets.KeySetManager()
        self.allWidgets()  # Build widgets
        self.allLayouts()  # Add to layouts
        self.connections()  # Connect buttons/checkbox

    # -------------------
    # WIDGETS LAYOUT
    # -------------------

    def allWidgets(self):
        """Builds all the widgets needed in the GUI"""
        toolTip = "Install the Zoo Tools Pro hotkey sets, this will install... \n\n" \
                  "1. `{0}`: the main hotkey set, this will be the active hotkey set. \n" \
                  "2. `{1}`: the Maya Default set that can be toggled with the `;` hotkey. \n\n" \
                  "Custom/user hotkey sets will not be affected and Zoo Tools Pro hotkeys can be removed at \n" \
                  "anytime.".format(c.KEYSETS[0], c.KEYSETS[1])
        self.installHotkeysBtn = elements.styledButton(text="Install Zoo Hotkeys",
                                                       icon="keyboard",
                                                       parent=self,
                                                       toolTip=toolTip,
                                                       style=uic.BTN_DEFAULT,
                                                       minWidth=uic.BTN_W_REG_LRG,
                                                       maxWidth=uic.BTN_W_REG_LRG)
        toolTip = "Update the Zoo Tools Pro default hotkey sets while upgrading Zoo Tools Pro.\n" \
                  "Hotkey sets will be deleted and re-created. \n\n" \
                  "1. `{0}` is the main hotkey set and will become the default set \n" \
                  "2. `{1}` is the Maya Default set that can be toggled with the `;` hotkey. \n\n" \
                  "Any custom/user hotkey sets will not be affected.".format(c.KEYSETS[0], c.KEYSETS[1])
        self.updateHotkeysBtn = elements.styledButton(text="Update Zoo Hotkeys",
                                                      icon="reload",
                                                      parent=self,
                                                      toolTip=toolTip,
                                                      style=uic.BTN_DEFAULT,
                                                      minWidth=uic.BTN_W_REG_LRG,
                                                      maxWidth=uic.BTN_W_REG_LRG)
        toolTip = "Delete the two Zoo Tools Pro hotkey sets... \n\n" \
                  "1. `{0}` \n" \
                  "2. `{1}` \n\n" \
                  "Any custom/user hotkey sets will not be affected.".format(c.KEYSETS[0], c.KEYSETS[1])
        self.deleteBtn = elements.styledButton(text="Delete Default Hotkeys",
                                               icon="trash",
                                               parent=self,
                                               toolTip=toolTip,
                                               style=uic.BTN_DEFAULT,
                                               minWidth=uic.BTN_W_REG_LRG,
                                               maxWidth=uic.BTN_W_REG_LRG)
        sp_retain = QtWidgets.QSizePolicy()
        sp_retain.setRetainSizeWhenHidden(True)
        toolTip = "Deletes ALL hotkeys including any custom ones."
        self.deleteAllBtn = elements.styledButton(text="Delete ALL Hotkeys",
                                                  icon="trash",
                                                  parent=self,
                                                  toolTip=toolTip,
                                                  style=uic.BTN_DEFAULT,
                                                  minWidth=uic.BTN_W_REG_LRG,
                                                  maxWidth=uic.BTN_W_REG_LRG)

        self.deleteAllBtn.setSizePolicy(sp_retain)  # when delete button is hidden it won't affect the layout
        toolTip = "Save the internal JSON Maya hotkey sets `{}` and `{}`\n" \
                  "to .mhk files in the user preferences folder?\n" \
                  "The user preferences .mhk files will be overwritten.\n\n" \
                  "Press this button only to save new saved admin hotkeys.".format(c.KEYSETS[0], c.KEYSETS[1])
        self.saveMHKBtn = elements.styledButton(text="Overwrite MHK",
                                                icon="code",
                                                parent=self,
                                                toolTip=toolTip,
                                                style=uic.BTN_DEFAULT,
                                                minWidth=uic.BTN_W_REG_LRG,
                                                maxWidth=uic.BTN_W_REG_LRG)
        toolTip = "Save the userPrefs .mhk sets `{}` and `{}`\n" \
                  "to .json files in the user preferences folder?\n" \
                  "The user preferences .json files will be overwritten. \n\n" \
                  "WARNING Zoo natively saves to the prefs JSON\n" \
                  "Empty hotkeys may be deleted".format(c.KEYSETS[0], c.KEYSETS[1])
        self.saveJSONBtn = elements.styledButton(text="Save JSON From MHK",
                                                 icon="code",
                                                 parent=self,
                                                 toolTip=toolTip,
                                                 style=uic.BTN_DEFAULT,
                                                 minWidth=uic.BTN_W_REG_LRG,
                                                 maxWidth=uic.BTN_W_REG_LRG)
        toolTip = "Opens the Zoo Tools Pro `Hotkey Editor` window."
        self.openHotkeyEditorBtn = elements.styledButton(text="Open Zoo HK Editor",
                                                         icon="keyboard",
                                                         parent=self,
                                                         toolTip=toolTip,
                                                         style=uic.BTN_DEFAULT,
                                                         minWidth=uic.BTN_W_REG_LRG,
                                                         maxWidth=uic.BTN_W_REG_LRG)
        toolTip = "Set the Admin mode to off"
        self.adminCheckBox = elements.CheckBox(label="Set Admin Mode",
                                               checked=hotkeyutils.isAdminMode(),
                                               parent=self,
                                               toolTip=toolTip)

    def allLayouts(self):
        """Adds all the widgets to GUI layouts"""
        mainLayout = elements.vBoxLayout(self,
                                         margins=(uic.WINSIDEPAD, uic.WINTOPPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SVLRG)
        installBtnLayout = elements.hBoxLayout(spacing=0)
        installBtnLayout.addWidget(self.installHotkeysBtn, 1)
        installBtnLayout.addWidget(self.updateHotkeysBtn, 1)
        # Install delete button layout ---------------------
        buttonLayout = elements.GridLayout(spacing=uic.SVLRG)
        buttonLayout.addLayout(installBtnLayout, 0, 0)
        buttonLayout.addWidget(self.deleteBtn, 0, 1)
        buttonLayout.addWidget(self.deleteAllBtn, 2, 1)
        buttonLayout.addWidget(self.saveMHKBtn, 1, 0)
        buttonLayout.addWidget(self.saveJSONBtn, 1, 1)
        buttonLayout.addWidget(self.openHotkeyEditorBtn, 2, 0)
        # Main layout  ---------------------
        mainLayout.addLayout(buttonLayout)
        mainLayout.addStretch(1)
        mainLayout.addWidget(self.adminCheckBox)
        # show hide GUI elements  ---------------------
        self.hotkeysInstalledShowHide()  # installed or not installed
        self.adminShowHide(self.adminCheckBox.isChecked())  # admin mode or not admin mode

    # -------------------
    # SHOW/HIDE GUI ELEMENTS
    # -------------------

    def hotkeysInstalledShowHide(self):
        """Depending if 'Zoo_Tools_Default' hotkey set exists show/hide the GUI elements"""
        if self.keysetManager.installed():  # Zoo_Tools_Default hotkey set exists
            self.installHotkeysBtn.hide()
            self.updateHotkeysBtn.show()
            self.openHotkeyEditorBtn.show()
            self.deleteBtn.show()
            self.deleteAllBtn.show()
        else:  # Zoo_Tools_Default hotkey set does not exist
            self.installHotkeysBtn.show()
            self.updateHotkeysBtn.hide()
            self.openHotkeyEditorBtn.hide()
            self.deleteBtn.hide()  # del button has setRetainSizeWhenHidden set so layout stays the same
            self.deleteAllBtn.hide()  # del button has setRetainSizeWhenHidden set so layout stays the same
        self.adminShowHide(self.adminCheckBox.isChecked())

    def adminShowHide(self, checked):
        """Depending if Admin mode is on or off show the GUI elements

        Admin mode is the env variable (bool)... os.environ["ZOO_ADMIN"]
        """
        if checked:
            if cmds.hotkeySet(c.DEFAULT_KEYSET, exists=True):
                self.saveJSONBtn.show()
                self.saveMHKBtn.show()
                return
        self.saveJSONBtn.hide()
        self.saveMHKBtn.hide()
        self.adminCheckBox.hide()

    # -------------------
    # LOGIC
    # -------------------

    def adminChecked(self):
        """Turn on/off admin mode depending on the checkbox state.  Also display the GUI elements correctly

        Admin mode is the env variable (bool)... os.environ["ZOO_ADMIN"]
        """
        checked = self.adminCheckBox.isChecked()
        hotkeyutils.setAdminMode(checked)
        self.adminShowHide(checked)  # show hide the GUI buttons
        if checked:
            output.displayInfo("Admin Mode is set to: `On`")
        else:
            output.displayInfo("Admin Mode is set to: `Off`. To return use `os.environ['ZOO_ADMIN'] = '1'`")

    def saveMHKBtnClicked(self):
        """Saves the two user preferences .mhk files from the current Maya hotkey sets:

            "Zoo_Tools_Default.mhk" and "Maya_Default_ZooMod.mhk"

        With popup window ok/cancel
        """
        save = elements.MessageBox.showOK(title="Save Hotkey Sets to MHK?",
                                          parent=None,
                                          message="Are you sure want to save the Maya hotkey sets `{}` and \n"
                                                  "`{}` to MHK files? In the user preferences folder?\n"
                                                  "The userPrefs MHK files will be "
                                                  "overwritten.".format(c.KEYSETS[0], c.KEYSETS[1]))
        if not save:
            logger.info("cancel was clicked")
            return
        admin.saveMHKs()
        output.displayInfo("Success: MHK files saved for hotkey sets: {} ".format(c.KEYSETS))

    def saveJSONBtnClicked(self):
        """Saves the two user preferences .mhk files to the .json files:

            "Zoo_Tools_Default.json" and "Maya_Default_ZooMod.json"

        With popup window ok/cancel
        """
        save = elements.MessageBox.showOK(title="Save MHK to JSON Hotkeys?",
                                          parent=None,
                                          message="Are you sure want to save the userPrefs `{}` and \n"
                                                  "`{}` MHK hotkey files as JSON?\n"
                                                  "The userPrefs JSON files will be "
                                                  "overwritten.".format(c.KEYSETS[0], c.KEYSETS[1]))
        if not save:
            return
        admin.saveHotkeys()
        output.displayInfo("Success: JSON files saved for hotkey sets: {} ".format(c.KEYSETS))

    def reloadDefaultHotkeys(self):
        """Re-installs (overrides) the Zoo Maya Hotkey Sets, inside of Maya:

            "Zoo_Tools_Default" and "Maya_Default_ZooMod"

        With popup window ok/cancel
        """
        reinstall = elements.MessageBox.showOK(title="Update Zoo Hotkeys?",
                                               parent=None,
                                               message="Are you sure want to update the Zoo Tools Pro hotkey sets? \n"
                                                       "This may be desired if you have upgraded Zoo Tools Pro.\n\n"
                                                       "Upgrade hotkeys sets... \n\n"
                                                       "1. `{}` \n"
                                                       "2. `{}` \n\n"
                                                       "These current hotkeys sets will be deleted and replaced by "
                                                       "the latest hotkey sets.  Other hotkey sets will not be "
                                                       "affected.".format(c.KEYSETS[0], c.KEYSETS[1]))
        if reinstall:
            self.keysetManager.revertToDefaults(force=True)

    def installHotkeys(self):
        """Saves the Zoo Maya Hotkey Sets, inside of Maya:

            "Zoo_Tools_Default" and "Maya_Default_ZooMod"

        With popup window ok/cancel.  Will override if the hotkey sets already exist in Maya
        """
        install = elements.MessageBox.showOK(title="Install Zoo Hotkeys?",
                                             parent=None,
                                             message="Install the Zoo Tools Pro hotkey sets, this will install... \n\n"
                                                     "1. `{0}`: the main hotkey set, this will be the active "
                                                     "hotkey set. \n"
                                                     "2. `{1}`: the Maya Default set that can be toggled with the "
                                                     "`;` hotkey. \n\n"
                                                     "Custom/user hotkey sets will not be affected and Zoo Tools Pro "
                                                     "hotkeys can be removed at anytime with a "
                                                     "button.".format(c.KEYSETS[0], c.KEYSETS[1]))
        if install:
            self.loadDefaults()

    def loadDefaults(self):
        """Saves the Zoo Maya Hotkey Sets, inside of Maya:

            "Zoo_Tools_Default" and "Maya_Default_ZooMod"

        Will override if the hotkey sets already exist in Maya
        """
        self.keysetManager.revertToDefaults(force=True)
        self.hotkeysInstalledShowHide()
        output.displayInfo("Success: Zoo Tools Pro hotkeys are installed, and the "
                           "current hotkey set has been set to `Zoo_Tools_Default`")

    def copyFromDefaults(self):
        pass

    def deleteBtnClicked(self):
        """Deletes the Zoo Maya hotkey sets and also the userPreferences json and mhk files:

            "Zoo_Tools_Default" and "Maya_Default_ZooMod"

        With popup window ok/cancel.
        """
        delete = elements.MessageBox.showOK(title="Delete Hotkeys?",
                                            parent=None,
                                            message="Are you sure want to delete the two Zoo Tools Pro hotkey sets? \n\n"
                                                    "1. `{}` \n"
                                                    "2. `{}`\n\n"
                                                    "These hotkey sets can be easily reinstalled at a later "
                                                    "time.  Custom/user hotkey sets will not be "
                                                    "affected".format(c.KEYSETS[0], c.KEYSETS[1]))
        if not delete:
            logger.info("cancel was clicked")
            return

        self.keysetManager.deleteDefaults()
        self.hotkeysInstalledShowHide()
        output.displayInfo("All Zoo Tools Pro default key sets have been deleted")

    def deleteAllHotkeys(self):
        delete = elements.MessageBox.showOK(title="Delete ALL Hotkeys?",
                                            parent=None,
                                            message="This will delete ALL zoo hotkeys, "
                                                    "including any custom ones. Do you want to continue?")
        if not delete:
            return
        admin.deleteMayaKeySets()
        admin.deleteZooKeySets(deletePrefHotkeys=True)
        self.hotkeysInstalledShowHide()
        output.displayInfo("All Zoo Tools Pro hotkey sets have been deleted")

    def openZooHkEditor(self):
        """Opens the Zoo Hotkey Editor"""
        from zoo.apps.toolpalette import run
        run.load().executePluginById("zoo.hotkeyeditorui")

    # -------------------
    # CONNECTIONS
    # -------------------

    def connections(self):
        """Connect the buttons and checkbox"""
        self.installHotkeysBtn.clicked.connect(self.installHotkeys)
        self.deleteBtn.clicked.connect(self.deleteBtnClicked)
        self.deleteAllBtn.clicked.connect(self.deleteAllHotkeys)
        self.saveMHKBtn.clicked.connect(self.saveMHKBtnClicked)
        self.adminCheckBox.stateChanged.connect(self.adminChecked)
        self.saveJSONBtn.clicked.connect(self.saveJSONBtnClicked)
        self.updateHotkeysBtn.clicked.connect(self.reloadDefaultHotkeys)
        self.openHotkeyEditorBtn.clicked.connect(self.openZooHkEditor)
