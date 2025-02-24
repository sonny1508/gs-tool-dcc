import maya.api.OpenMaya as om2
from zoo.libs.pyqt.extended.imageview.thumbnail import minibrowserpathlist
from zoo.preferences.interfaces import camerainterfaces, coreinterfaces

from zoo.apps.preferencesui import prefmodel
from zoo.libs.pyqt.widgets import elements
from zoo.libs.pyqt import uiconstants as uic


class ZooCameraToolsPrefsWidget(prefmodel.SettingWidget):
    categoryTitle = "Camera Tools"  # The main title of the Camera Tools preferences section and also side menu item

    def __init__(self, parent=None, setting=None):
        """Builds the Camera Tools Section of the preferences window.

        :param parent: the parent widget
        :type parent: Qt.QtWidgets
        """
        super(ZooCameraToolsPrefsWidget, self).__init__(parent, setting)
        self.corePref = coreinterfaces.coreInterface()
        self.camPrefs = camerainterfaces.cameraToolInterface()
        self.uiWidgets()  # Builds the widgets
        self.uiLayout()  # Adds widgets to the layouts

    # -------------------
    # WIDGETS LAYOUT
    # -------------------

    def uiWidgets(self):
        """Builds all the widgets needed in the GUI"""
        # Retrieve data from user's .prefs json -------------------------
        # imagePlanePath = self.prefsData["settings"][cc.PREFS_KEY_IMAGEPLANE]
        # Camera Tools Path -----------------------------------------
        toolTip = "The location of the Image Plane Folder. \n" \
                  "Plane image planes here or change the folder to a path with images.  Supports .jpg and .png"
        self.browserWidget = minibrowserpathlist.MiniBrowserPathList(self.camPrefs.imagePlaneAssets, toolTip=toolTip)

    def uiLayout(self):
        """Adds all the widgets to layouts for the GUI"""
        mainLayout = elements.vBoxLayout(self,
                                         margins=(uic.WINSIDEPAD, uic.WINTOPPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SREG)
        mainLayout.addWidget(self.browserWidget)
        # # Camera Tools  Path Layout ------------------------------------
        mainLayout.addStretch(1)

    # -------------------
    # SAVE, APPLY, RESET
    # -------------------

    def serialize(self):
        """ Save the current settings to the preference file, used for both Apply and Save buttons

        Automatically connected to the preferences window buttons via model.SettingWidget
        """
        if not self.camPrefs.settingsValid():
            om2.MGlobal.displayError("The preferences object is not valid")
            return

        self.browserWidget.saveToPrefs()
        self.camPrefs.saveSettings()
        om2.MGlobal.displayInfo("Success: Camera Tools preferences Saved To Disk ")

    def revert(self):
        """Reverts to the previous settings, resets the GUI to the previously saved settings

        Automatically connected to the preferences window revert button via model.SettingWidget
        """
        self.camPrefs.revertSettings()
        self.browserWidget.revert()

    def adminSave(self):
        """Method for admin saving internally to Zoo Tools Pro, not connected
        """
        pass
