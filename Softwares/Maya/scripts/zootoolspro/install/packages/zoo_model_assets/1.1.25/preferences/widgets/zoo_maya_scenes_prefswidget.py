import maya.api.OpenMaya as om2
from zoo.libs.pyqt.extended.imageview.thumbnail import minibrowserpathlist
from zoo.preferences.interfaces import assetinterfaces, coreinterfaces

from zoo.apps.preferencesui import prefmodel
from zoo.libs.pyqt.widgets import elements
from zoo.libs.pyqt import uiconstants as uic


class ZooMayaScenesPrefsWidget(prefmodel.SettingWidget):
    categoryTitle = "Maya Scenes"  # The main title of the Maya Scenes preferences section and also side menu item

    def __init__(self, parent=None, setting=None):
        """Builds the Maya Scenes Section of the preferences window.

        :param parent: the parent widget
        :type parent: Qt.QtWidgets
        """
        super(ZooMayaScenesPrefsWidget, self).__init__(parent, setting)
        self.corePrefs = coreinterfaces.coreInterface()
        self.prefs = assetinterfaces.mayaScenesInterface()

        self.uiWidgets()  # Builds the widgets
        self.uiLayout()  # Adds widgets to the layouts

    # -------------------
    # WIDGETS LAYOUT
    # -------------------

    def uiWidgets(self):
        """Builds all the widgets needed in the GUI"""
        # Maya Scenes Path -----------------------------------------
        toolTip = "The location of the Maya Scenes. \n" \
                  "Folder with the Maya Scenes folders."

        self.browserWidget = minibrowserpathlist.MiniBrowserPathList(self.prefs.scenesAssets, toolTip=toolTip)


    def uiLayout(self):
        """Adds all the widgets to layouts for the GUI"""
        mainLayout = elements.vBoxLayout(self,
                                         margins=(uic.WINSIDEPAD, uic.WINTOPPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SREG)
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
            om2.MGlobal.displayError("The preferences object is not valid")
            return
        self.browserWidget.saveToPrefs()
        self.prefs.saveSettings()
        om2.MGlobal.displayInfo("Success: Maya Scenes preferences Saved To Disk ")

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
