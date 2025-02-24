from zoo.libs.pyqt.extended.imageview.thumbnail import minibrowserpathlist
from zoo.preferences.interfaces import coreinterfaces, controljointsinterfaces

from zoo.libs.utils import output
from zoo.apps.preferencesui import prefmodel
from zoo.libs.pyqt.widgets import elements
from zoo.libs.pyqt import uiconstants as uic


class ZooControlsJointsPrefsWidget(prefmodel.SettingWidget):
    categoryTitle = "Controls Joints"  # The main title of the Model Asset preferences section and also side menu item

    def __init__(self, parent=None, setting=None):
        """Builds the Controls Joints Section of the preferences window.

        :param parent: the parent widget
        :type parent: Qt.QtWidgets
        """
        super(ZooControlsJointsPrefsWidget, self).__init__(parent, setting)
        self.corePrefs = coreinterfaces.coreInterface()
        self.prefs = controljointsinterfaces.controlJointsInterface()

        self.uiWidgets()  # Builds the widgets
        self.uiLayout()  # Adds widgets to the layouts
        # Save, Apply buttons are automatically connected to the self.serialize() method
        # Reset Button is automatically connected to the self.revert() method
        self.initPrefs()

    def initPrefs(self):
        pass

    def updateUI(self):
        """ Reverts the controls joints folders

        :return:
        """
        self.browserWidget.revert()

    # -------------------
    # WIDGETS LAYOUT
    # -------------------

    def uiWidgets(self):
        """Builds all the widgets needed in the GUI"""
        # Controls Joints Path -----------------------------------------
        toolTip = "The location of the Controls Joints. \n" \
                  "Copy your *.zooScene files along with their dependency folders into the root of this folder. "

        self.browserWidget = minibrowserpathlist.MiniBrowserPathList(self.prefs.controlAssets, toolTip=toolTip)
        toolTip = "Browse to change the Controls Joints folder."
        toolTip = "Reset the Controls Controls Joints folder to it's default location."
        toolTip = "Explore, open the directory in your OS browser."

    def uiLayout(self):
        """Adds all the widgets to layouts for the GUI"""

        mainLayout = elements.vBoxLayout(self,
                                         margins=(uic.WINSIDEPAD, uic.WINTOPPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SREG)
        # Path Grid Top Layout ----------------------------------------------
        mainLayout.addWidget(self.browserWidget)

        mainLayout.addStretch(1)

    # -------------------
    # SAVE, APPLY, RESET
    # -------------------

    def serialize(self):
        """ Save the current settings to the preference file, used for both Apply and Save buttons

        Automatically connected to the preferences window buttons via model.SettingWidget
        """
        if not self.prefs.settingsValid():
            output.displayError("The preferences object is not valid")
            return

        self.browserWidget.saveToPrefs()
        self.prefs.saveSettings()
        output.displayInfo(
            "Success: Control joints preferences saved: '{}'".format(self.prefs.controlAssets.zooPrefsPath()))

    def revert(self):
        """Reverts to the previous settings, resets the GUI to the previously saved settings

        Automatically connected to the preferences window revert button via model.SettingWidget
        """

        self.prefs.revertSettings()
        self.browserWidget.revert()

    def adminSave(self):
        """Method for admin saving internally to Zoo Tools Pro, not connected
        """
        pass
