import os
import shutil

from zoovendor.Qt import QtWidgets

from zoo.libs.pyqt import utils
from zoo.libs.pyqt.widgets import elements
from zoo.libs.pyqt import uiconstants as uic

from zoo.libs.utils import filesystem, output, application
from zoo.core.util import env

from zoo.apps.preferencesui import prefmodel
from zoo.preferences.core import preference
from zoo.preferences import preferencesconstants
from zoo.preferences import constants as coreprefconstants
from zoo.preferences.interfaces import coreinterfaces


class GeneralPrefsWidget(prefmodel.SettingWidget):
    categoryTitle = "General"  # The main title of the General preferences section and also side menu item

    def __init__(self, parent=None, setting=None):
        """Builds the General Section of the preferences window.

        :param parent: the parent widget
        :type parent: Qt.QtWidgets
        """
        super(GeneralPrefsWidget, self).__init__(parent, setting)
        self.coreInterface = coreinterfaces.coreInterface()
        self.generalInterface = coreinterfaces.generalInterface()
        self.toolPaletteInterface = preference.interface("artistPalette")
        # Light Suite Pref Object self.lsPrefsObj stores and saves all the .prefs json data
        self.prefsData = preference.findSetting(coreprefconstants.RELATIVE_PREFS_FILE, None)

        self.initialUserPrefsPath = self.coreInterface.userPreferences()
        self.uiWidgets()  # Builds the widgets
        self.uiLayout()  # Adds widgets to the layouts
        # Save, Apply buttons are automatically connected to the self.serialize() method
        # Reset Button is automatically connected to the self.revert() method
        self.uiConnections()

    # -------------------
    # WIDGETS LAYOUT
    # -------------------

    def uiWidgets(self):
        """Builds all the widgets needed in the GUI"""
        primaryRenderer = self.prefsData[preferencesconstants.PREFS_KEY_RENDERER]
        # Light Presets Path -----------------------------------------
        toolTip = "The location of the Zoo User Preferences folder. \n" \
                  "All Zoo Asset and Prefs folder locations are found in this folder unless \n" \
                  "otherwise specified. \n" \
                  "Moving this folder will require a Maya restart."
        self.userPrefPathLbl = elements.Label("Zoo Preferences Folder", parent=self, toolTip=toolTip)
        self.userPrefPathTxt = elements.StringEdit(label="",
                                                   editText=self.initialUserPrefsPath,
                                                   toolTip=toolTip)
        toolTip = "Browse to change the Zoo User Preferences folder."
        self.preferencesSetBtn = elements.styledButton("",
                                                       "browse",
                                                       toolTip=toolTip,
                                                       parent=self,
                                                       minWidth=uic.BTN_W_ICN_MED)
        self.preferencesSetBtn.setFixedWidth(40)

        resetToolTip = "Reset the Zoo User Preferences folder to it's default location."
        exploreToolTip = "Explore, open the directory in your OS browser."
        self.dotsMenu = elements.DotsMenu()
        self.dotsMenu.addAction("Open Folder location",
                                icon="webpage",
                                connect=self.openPrefsFolder, toolTip=exploreToolTip)
        self.dotsMenu.addAction("Reset Preferences to default",
                                icon="arrowBack",
                                connect=self.setZooPrefsDefault,
                                toolTip=resetToolTip
                                )
        self.dotsMenu.setFixedWidth(40)

        # Primary Renderer -----------------------------------------
        toolTip = "Set your primary renderer, will be used by all windows, can be changed at anytime.\n" \
                  "The renderer must be installed on your computer (Redshift or Renderman)."
        self.rendererTitleLabel = elements.Label(text="Primary Renderer",
                                                 parent=self,
                                                 upper=True,
                                                 toolTip=toolTip)
        utils.setStylesheetObjectName(self.rendererTitleLabel, "HeaderLabel")  # set title stylesheet
        currentIndex = preferencesconstants.RENDERER_LIST.index(primaryRenderer)
        self.rendererComboLbl = elements.Label("Set Renderer", parent=self, toolTip=toolTip)
        self.rendererCombo = elements.ComboBoxRegular(label="",
                                                      items=preferencesconstants.RENDERER_LIST,
                                                      toolTip=toolTip,
                                                      setIndex=currentIndex,
                                                      labelRatio=1,
                                                      boxRatio=2,
                                                      boxMinWidth=150)
        toolTip = "Load the Renderer selected in the drop-down combobox.\n " \
                  "The renderer may already be loaded"
        self.loadRendererBtn = elements.styledButton("Load Renderer",
                                                     "checkOnly",
                                                     self,
                                                     toolTip=toolTip,
                                                     style=uic.BTN_DEFAULT,
                                                     minWidth=120)
        toolTip = ""
        self.startUpTitleLabel = elements.Label(text="Start up",
                                                parent=self,
                                                upper=True,
                                                toolTip=toolTip)
        utils.setStylesheetObjectName(self.startUpTitleLabel, "HeaderLabel")  # set title stylesheet
        if env.isMaya():
            toolTip = "Auto-loads Zoo Tools Pro when Maya starts.\n" \
                      "If not checked Zoo Tools will need to be loaded with\n" \
                      "Maya's Plugin Manager after starting Maya. \n\n" \
                      " - Windows > Settings/Preferences > Plug-in Manager"
            self.autoLoadCheckBox = elements.CheckBox(label="Load ZooTools on Start Up",
                                                      checked=self.generalInterface.autoLoadPlugin(),
                                                      parent=self,
                                                      toolTip=toolTip)
            toolTip = "Sets the ZooToolsPro shelf as the the primary active shelf after loading Maya.\n" \
                      " - Note: Plugins that also have shelves that load after Zoo will override this setting."
            self.shelfActiveCheckBox = elements.CheckBox(label="Shelf Active On Start Up",
                                                         checked=self.toolPaletteInterface.isActiveAtStartup(),
                                                         parent=self,
                                                         toolTip=toolTip)
            toolTip = "Auto-loads the ZooToolsPro shelf when Maya starts.\n" \
                       "If not checked then you will need to load the shelf with\n" \
                       " - ZooTools Menu > Preferences > Build Zoo Shelves"
            self.autoLoadShelfCheckBox = elements.CheckBox(label="Load ZooTools Shelf on Start Up",
                                                           checked=self.toolPaletteInterface.loadShelfAtStartup(),
                                                           parent=self,
                                                           toolTip=toolTip)

    def uiLayout(self):
        """Adds all the widgets to layouts for the GUI"""
        mainLayout = elements.vBoxLayout(self,
                                         margins=(uic.WINSIDEPAD, uic.WINTOPPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SREG)
        # Light Preset Path Layout ------------------------------------
        generalPathBtnLayout = elements.hBoxLayout()
        generalPathBtnLayout.addWidget(self.preferencesSetBtn)
        generalPathBtnLayout.addWidget(self.dotsMenu)

        pathGridLayout = elements.GridLayout(
            margins=(0, 0, 0, uic.SXLRG),
            columnMinWidth=(0, 120),
            columnMinWidthB=(2, 60))
        pathGridLayout.addWidget(self.userPrefPathLbl, 0, 0)
        pathGridLayout.addWidget(self.userPrefPathTxt, 0, 1)
        pathGridLayout.addLayout(generalPathBtnLayout, 0, 2)
        # Primary Renderer Combo ------------------------------------
        rendererLayout = elements.hBoxLayout()
        rendererLayout.addWidget(self.rendererCombo)
        rendererLayout.addStretch(1)
        # Primary Renderer Grid top ----------------------------------------------
        rendererGridLayout = elements.GridLayout(margins=(0, uic.SLRG, 0, uic.SXLRG),
                                                 columnMinWidth=(0, 120),
                                                 columnMinWidthB=(2, 120))
        rendererGridLayout.addWidget(self.rendererComboLbl, 0, 0)
        rendererGridLayout.addLayout(rendererLayout, 0, 1)
        rendererGridLayout.addWidget(self.loadRendererBtn, 0, 2)

        # main layout
        mainLayout.addLayout(pathGridLayout)
        mainLayout.addWidget(self.rendererTitleLabel)
        mainLayout.addLayout(rendererGridLayout)
        mainLayout.addWidget(self.startUpTitleLabel)

        if env.isMaya():
            startupCheckboxLayout = elements.hBoxLayout(margins=(0, uic.SVLRG, 0, 0))
            startupCheckboxLayout.addWidget(self.autoLoadCheckBox)
            startupCheckboxLayout.addWidget(self.shelfActiveCheckBox)
            startupCheckboxLayout.addWidget(self.autoLoadShelfCheckBox)
            mainLayout.addLayout(startupCheckboxLayout)
        mainLayout.addStretch(1)

    # ------------------------------------
    # POPUP WINDOWS
    # ------------------------------------

    def ui_changePrefsPopup(self):
        """Popup window dialog asking the user wants to change the preferences folder, will require a restart

        :return okPressed: True if the ok button was pressed, else False if cancelled
        :rtype okPressed: bool
        """
        message = "Are you sure you want to change the Zoo User Preferences Folder? \n\n" \
                  "This will move the entire preferences directory with all files and assets.\n\n" \
                  "Changing the location of this folder will require a full Maya restart after save."
        okPressed = elements.MessageBox.showOK(title="Change Zoo User Preferences "
                                                     "Folder?", parent=None, message=message)
        return okPressed

    def ui_resetPopup(self, prefsDefaultPath):
        """Popup window dialog asking the user wants to return to the preferences folder default, will require restart

        :return okPressed: True if the ok button was pressed, else False if cancelled
        :rtype okPressed: bool
        """
        message = "Are you sure you want to return to the DefaultZoo User Preferences Folder? \n\n" \
                  "{} \n\n" \
                  "This will move the entire preferences directory with all files and assets.\n" \
                  "Changing the location of this folder will require a full Maya restart after save.".format(
            prefsDefaultPath)
        okPressed = elements.MessageBox.showOK(title="Change Zoo User Preferences"
                                                     "Folder?", parent=None, message=message)
        return okPressed

    def ui_restartPopup(self, newPrefsPath):
        """Popup window dialog asking the user to restart Maya after the Zoo User Preferences have changed.

        :param newPrefsPath: The new path to the zoo_preferences folder
        :type newPrefsPath: str
        :return okPressed: True if the ok button was pressed, else False if cancelled
        :rtype okPressed: bool
        """
        message = "The Zoo User Preferences path has been moved to \n\n  " \
                  "{}\n\n" \
                  "You should restart Maya. Close Maya now?".format(newPrefsPath)
        okPressed = elements.MessageBox.showOK(title="Close And Restart Maya?", parent=None,
                                               message=message,
                                               buttonA="Close Maya")
        return okPressed

    # ------------------------------------
    # POPUP WINDOWS
    # ------------------------------------

    def ui_loadRenderer(self, renderer):
        """Popup window dialog asking the user if they'd like to load the given renderer

        :param renderer: The renderer nice name eg. "Arnold"
        :type renderer: str
        :return okPressed: True if the ok button was pressed, else False if cancelled
        :rtype okPressed: bool
        """
        message = "The {} renderer isn't loaded. Load now?".format(renderer)
        okPressed = elements.MessageBox.showOK(title="Load Renderer?", parent=None, message=message)
        return okPressed

    def checkRenderLoaded(self):
        """Checks that the renderer is loaded, if not opens a popup window asking the user to load?

        :return rendererLoaded: True if the renderer is loaded
        :rtype rendererLoaded: bool
        """
        try:  # zoo_core_pro may not be loaded (though unlikely
            from zoo.libs.maya.cmds.renderer import rendererload
            renderer = self.rendererCombo.currentText()
            if not rendererload.getRendererIsLoaded(renderer):
                okPressed = self.ui_loadRenderer(renderer)  # open the popup dialog window
                if okPressed:
                    rendererload.loadRenderer(renderer)  # load the renderer
                    return True
                return False
            else:
                output.displayInfo("The renderer `{}` is already loaded".format(renderer))
            return True
        except:
            output.displayWarning("Check renderer loaded failed, the package zoo_core_pro may "
                                  "not be loaded")

    # -------------------
    # CHANGE PREFERENCES UPDATE OTHER WINDOWS - GLOBAL TOOL SETS
    # -------------------

    def global_changeRenderer(self, event=None):
        """Updates all GUIs with the current renderer

        :param event: Event with all the values related to the change.
        :type event: zoo.libs.pyqt.extended.combobox.ComboItemChangedEvent
        :return:
        :rtype:
        """
        try:  # toolsets may not be loaded
            from zoo.apps.toolsetsui import toolsetui
            toolsets = toolsetui.toolsetsByAttr(attr="global_receiveRendererChange")
            for tool in toolsets:
                tool.global_receiveRendererChange(self.rendererCombo.currentText())
        except:
            output.displayWarning("Change renderer did not send to Toolsets, the package zoo_toolsets may "
                                  "not be loaded")

    def global_receiveRendererChange(self, renderer):
        """Receives from other GUIs, changes the renderer when it is changed

        TODO currently not in use"""
        index = preferencesconstants.RENDERER_LIST.index(renderer)
        self.rendererCombo.setCurrentIndex(index)

    # -------------------
    # LOGIC
    # -------------------

    def setZooPrefsDefault(self):
        """Sets the UI widget path text to the default Zoo User Preferences path"""
        zooDefaultPrefsPath = os.path.normpath(os.path.expanduser("~/zoo_preferences"))  # check this
        if os.path.normpath(self.userPrefPathTxt.text()) == zooDefaultPrefsPath:
            return  # hasn't changed from the saved version
        if self.coreInterface.userPreferences() == zooDefaultPrefsPath:
            self.userPrefPathTxt.setText(zooDefaultPrefsPath)  # matches the saved path
            return
        okPressed = self.ui_resetPopup(zooDefaultPrefsPath)
        if not okPressed:
            return
        self.userPrefPathTxt.setText(zooDefaultPrefsPath)

    def setPrefsFolderClicked(self):
        """ Set Prefs Folder

        :return:
        """
        directoryPath = self.userPrefPathTxt.text()
        if not os.path.isdir(directoryPath):  # if dir doesn't exist set to home directory
            directoryPath = os.path.expanduser("~")
        newDirPath = QtWidgets.QFileDialog.getExistingDirectory(self, "Set the Zoo User Preferences "
                                                                      "folder", directoryPath)
        if not newDirPath:
            return  # cancelled or folder is the same

        self.userPrefPathTxt.setText(os.path.normpath(newDirPath))  # update path GUI

    def openPrefsFolder(self):
        """Opens an os window for browsing files on disk in the users operating system"""
        filesystem.openDirectory(self.userPrefPathTxt.text())
        output.displayInfo("OS window opened to the `Zoo User Preferences` folder location")

    # -------------------
    # SAVE/APPLY AND RESET
    # -------------------
    def _handlePreferencePathChange(self):
        """Determines if the preferences was change and if so provides UI popups to the user.

        :return: True if the preferences path was changed
        :rtype: bool
        """
        previousPath = self.coreInterface.userPreferences()
        newDirPath = os.path.normpath(self.userPrefPathTxt.text())

        if previousPath == newDirPath:  # no change
            return False
        # should we really force the folder name to be zoo_preferences?
        index, resText = elements.MessageBox.showMultiChoice("Zoo Preference", parent=self.window(),
                                                             message="Preference Location was changed",
                                                             choices=["Move Preferences and Assets",
                                                                      "Set Location Only"])
        if index == -1:
            # cancelled
            return False
        # do the prefs move/change

        if index == 0:  # move preferences folder
            # if the folder exists ask if they want to override it, delete it if the user continues
            if os.path.isdir(newDirPath):
                result = elements.MessageBox.showQuestion(parent=self.window(),
                                                          title="Preferences Directory already exists",
                                                          message="The specified directory already exists,\n"
                                                                  "{}\n"
                                                                  "Do you wish to override it?".format(newDirPath))
                if result == "B":
                    # cancelled
                    return False
                shutil.rmtree(newDirPath)  # remove the folder
            output.displayInfo("Moving preferences to: {}, Please Wait".format(newDirPath))
            preference.moveRootLocation("user_preferences", newDirPath)
            output.displayInfo("Finished Moving Preferences")

        if index == 1:  # set preferences folder
            filesystem.ensureFolderExists(newDirPath)
            preference.setRootLocation("user_preferences", newDirPath)

        self.coreInterface.bakePreferenceRoots()
        if index == 1:
            preference.copyOriginalToRoot("user_preferences", force=False)

        # restart popup window
        restartPressed = self.ui_restartPopup(newDirPath)  # restart popup window
        if not restartPressed:  # canceled window
            return True

        application.quit()

    def serialize(self):
        """ Save the current settings to the preference file, used for both Apply and Save buttons

        Automatically connected to the preferences window buttons via model.SettingWidget

        :return: Returns true if successful in saving, false otherwise
        :rtype: bool
        """
        # save renderer to preferences "general_settings.pref"
        self.prefsData[preferencesconstants.PREFS_KEY_RENDERER] = self.rendererCombo.currentText()
        self.prefsData.save(indent=True)  # save and format nicely
        self.generalInterface.setAutoLoad(self.autoLoadCheckBox.isChecked())
        self.toolPaletteInterface.setShelfActiveAtStartup(self.shelfActiveCheckBox.isChecked())
        self.toolPaletteInterface.setLoadShelfAtStartup(self.autoLoadShelfCheckBox.isChecked())
        self.toolPaletteInterface.saveSettings()
        self._handlePreferencePathChange()
        return True

    def revert(self):
        """Reverts to the previous settings, resets the GUI to the previously saved settings

        Automatically connected to the preferences window revert button via model.SettingWidget
        """
        self.userPrefPathTxt.setText(self.coreInterface.userPreferences())

    # -------------------
    # CONNECTIONS
    # -------------------

    def uiConnections(self):
        """Setup the custom connections for the Light Suite Preferences GUI

        # Save, Apply buttons are automatically connected to the self.serialize() methods
        # Reset Button is automatically connected to the self.revert() method
        """
        # load/change renderer
        self.loadRendererBtn.clicked.connect(self.checkRenderLoaded)
        self.rendererCombo.itemChanged.connect(self.global_changeRenderer)
        # zoo_preferences path changes
        self.preferencesSetBtn.clicked.connect(self.setPrefsFolderClicked)
