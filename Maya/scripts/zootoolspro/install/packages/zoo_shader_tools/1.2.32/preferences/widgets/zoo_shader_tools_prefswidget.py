import maya.api.OpenMaya as om2
from zoo.libs.pyqt.extended.imageview.thumbnail import minibrowserpathlist

from zoo.preferences.interfaces import coreinterfaces, shaderinterfaces

from zoo.apps.preferencesui import prefmodel
from zoo.libs.pyqt.widgets import elements
from zoo.libs.pyqt import uiconstants as uic, utils


class ZooShaderToolsPrefsWidget(prefmodel.SettingWidget):
    categoryTitle = "Shader Tools"  # The main title of the Camera Tools preferences section and also side menu item

    def __init__(self, parent=None, setting=None):
        """Builds the Camera Tools Section of the preferences window.

        :param parent: the parent widget
        :type parent: Qt.QtWidgets
        """
        super(ZooShaderToolsPrefsWidget, self).__init__(parent, setting)
        self.corePrefs = coreinterfaces.coreInterface()
        self.prefs = shaderinterfaces.shaderInterface()

        self.uiWidgets()  # Builds the widgets
        self.uiLayout()  # Adds widgets to the layouts

    # -------------------
    # WIDGETS LAYOUT
    # -------------------

    def uiWidgets(self):
        """Builds all the widgets needed in the GUI"""
        # Camera Tools Path -----------------------------------------
        toolTip = "The location of the Shader Presets Folder. \n" \
                  "Place shader presets here or change the folder to a path with .zooScene shader files.  \n" \
                  "Supports .jpg and .png"
        self.shaderPresetsWidget = minibrowserpathlist.MiniBrowserPathList(self.prefs.shaderPresetsAssets, toolTip=toolTip)
        self.mayaShadersWidget = minibrowserpathlist.MiniBrowserPathList(self.prefs.mayaShaderAssets, toolTip=toolTip)
        self.shaderPresetFrame = elements.CollapsableFrame("Shader Preset Assets", parent=self, collapsed=False)
        self.mayaShadersFrame = elements.CollapsableFrame("Maya Shader Assets", parent=self, collapsed=False)

    def uiLayout(self):
        """Adds all the widgets to layouts for the GUI"""
        mainLayout = elements.vBoxLayout(self,
                                         margins=(uic.WINSIDEPAD, uic.WINTOPPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SREG)

        # Shader Tools Path Layout ------------------------------------
        self.shaderPresetFrame.addWidget(self.shaderPresetsWidget)
        self.mayaShadersFrame.addWidget(self.mayaShadersWidget)

        mainLayout.addWidget(self.shaderPresetFrame)
        mainLayout.addSpacing(utils.dpiScale(5))
        mainLayout.addWidget(self.mayaShadersFrame)
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
        self.shaderPresetsWidget.saveToPrefs()
        self.mayaShadersWidget.saveToPrefs()
        self.prefs.saveSettings()
        om2.MGlobal.displayInfo("Success: Camera Tools preferences Saved To Disk ")

    def revert(self):
        """Reverts to the previous settings, resets the GUI to the previously saved settings

        Automatically connected to the preferences window revert button via model.SettingWidget
        """
        self.prefs.revertSettings()
        self.shaderPresetsWidget.revert()
        self.mayaShadersWidget.revert()

    def adminSave(self):
        """Method for admin saving internally to Zoo Tools Pro, not connected
        """
        pass
