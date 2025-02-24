import collections
from functools import partial

from zoovendor.Qt import QtWidgets, QtCore
from zoo.core import api
from zoo.core.util import env
from zoo.libs.pyqt.widgets.frameless import window

from preferences.interface.preference_interface import ZooToolsPreference
from zoo.libs.pyqt import uiconstants as uic
from zoo.apps.preferencesui import prefmodel
from zoo.apps.preferencesui.example import examplewidget
from zoo.libs.pyqt import utils, stylesheet
from zoo.libs.utils import color, filesystem, output
from zoo.core.util import zlogging
from zoo.preferences.interfaces import coreinterfaces
from zoo.preferences.core import preference

from zoo.libs.pyqt.widgets import elements
from zoo.apps.preferencesui.stylesheetui import stylesheetui_constants as sc

if env.isMaya():
    from zoo.libs.maya.qt import cmdswidgets


logger = zlogging.getLogger(__name__)


class InterfaceWidget(prefmodel.SettingWidget):
    """Widget that creates the UI with color picker/size/icon settings for Stylesheets
    """
    categoryTitle = "Theme Colors"
    prefDataRelativePath = "prefs/global/stylesheet.pref"
    globalColorWidgets = []  # type: list[cmdswidgets.MayaColorBtn]

    def __init__(self, parent=None, setting=None):
        super(InterfaceWidget, self).__init__(parent, setting)
        self.sectionGridWidgetList = list()
        self.allCurrentThemeDict = dict()
        self.globalColorUpdate = True  # when False disables the global color updates as the globals are set
        self.themeUnsaved = False  # Specific to the theme, different to isModified()
        self.currentZooInstance = api.currentConfig()
        self.prefInterface = preference.interface("core_interface")  # type: ZooToolsPreference
        self.prefs = {}
        self.sheets = {}
        self.updateSheets()  # update all themes (all dictionaries) each theme is a sheet
        self._initUI()
        self.connections()


    def _initUI(self):
        """Build the UI"""
        layout = QtWidgets.QVBoxLayout(self)

        themeSwitchLayout = elements.hBoxLayout()

        themeComboBtnsLayout = elements.hBoxLayout()
        themeBoxAdminLayout = elements.hBoxLayout()
        toolTip = "Choose the current color UI Theme"
        self.themeBox = elements.ComboBoxRegular("Theme:", labelRatio=1, boxRatio=2, toolTip=toolTip,
                                                 sortAlphabetically=True, parent=self)

        toolTip = "Admin save to {} for setting Zoo Defaults".format(InterfaceWidget.prefDataRelativePath)
        self.adminSaveBtn = elements.styledButton("Admin", "save", parent=self, toolTip=toolTip,
                                                  minWidth=uic.BTN_W_REG_SML, maxWidth=uic.BTN_W_REG_SML,
                                                  iconColor=uic.COLOR_ADMIN_GREEN_RGB)
        if self.currentZooInstance.isAdmin:
            self.adminSaveBtn.setHidden(True)

        toolTip = "Create/add a new UI Theme"
        self.createNewThemeBtn = elements.styledButton(icon="plus", parent=self, toolTip=toolTip,
                                                       style=uic.BTN_TRANSPARENT_BG,
                                                       minWidth=uic.BTN_W_ICN_REG)
        self.createNewThemeBtn.setHidden(True)
        toolTip = "Rename the current UI Theme"
        self.renameThemeBtn = elements.styledButton(icon="editText", parent=self, toolTip=toolTip,
                                                    style=uic.BTN_TRANSPARENT_BG,
                                                    minWidth=uic.BTN_W_ICN_REG)
        self.renameThemeBtn.setHidden(True)
        toolTip = "Delete the current UI Theme"
        self.deleteThemeBtn = elements.styledButton(icon="trash", parent=self, toolTip=toolTip,
                                                    style=uic.BTN_TRANSPARENT_BG,
                                                    minWidth=uic.BTN_W_ICN_REG)

        toolTip = "Open the Test Colors Window"
        self.themeExampleBtn = elements.styledButton("Test Window", "windowBrowser", parent=self, toolTip=toolTip,
                                                     minWidth=uic.BTN_W_REG_LRG, maxWidth=uic.BTN_W_REG_LRG)

        toolTip = "Revert current theme to factory default"
        self.revertThemeBtn = elements.styledButton(icon="shippingBox", parent=self,
                                                    style=uic.BTN_TRANSPARENT_BG, toolTip=toolTip,
                                                    minWidth=uic.BTN_W_ICN_REG)
        themeBoxAdminLayout.addWidget(self.themeBox)
        themeBoxAdminLayout.addWidget(self.adminSaveBtn)
        themeComboBtnsLayout.addWidget(self.createNewThemeBtn, 1)
        themeComboBtnsLayout.addWidget(self.renameThemeBtn, 1)
        themeComboBtnsLayout.addWidget(self.revertThemeBtn, 1)
        themeComboBtnsLayout.addWidget(self.deleteThemeBtn, 1)
        themeComboBtnsLayout.addStretch(10)
        themeComboBtnsLayout.addWidget(self.themeExampleBtn, 10)
        layout.addLayout(themeSwitchLayout)
        themeSwitchLayout.addLayout(themeBoxAdminLayout, 1)
        themeSwitchLayout.addLayout(themeComboBtnsLayout, 1)
        comboNameList = self.getThemeNameList()
        for i, name in enumerate(comboNameList):
            self.themeBox.addItem(name.decode())

        self.themeWindow = examplewidget.exampleWidget(parent=self)

        currentActiveTheme = self.prefs["current_theme"]
        themeDict = self.sheets[currentActiveTheme]
        self.themeBox.setCurrentText(currentActiveTheme)
        self.themeWindow.setStyleSheet(self.prefInterface.stylesheet().data)
        # build the color globals section
        globalColorsVLayout = self.buildGlobalColorsUI(themeDict)
        layout.addLayout(globalColorsVLayout)
        # build the color tweak layouts
        layout.addItem(elements.Spacer(0, 10))
        sectionLabel = elements.TitleLabel(text="STYLE BY WIDGET", parent=self)
        layout.addWidget(sectionLabel)
        colorTweakVLayout = self.buildColorTweakUI(themeDict)
        layout.addLayout(colorTweakVLayout)
        layout.addStretch(1)

    def ui_createWindowPopup(self):
        message = "Create and save a new theme name."
        newThemeName = elements.MessageBox.inputDialog(title="Add A New UI Theme", text="New Theme Name",
                                                       parent=self,
                                                       message=message)
        return newThemeName

    def ui_revertThemePopup(self):
        message = "Are you sure you want to revert \"{}\" theme?".format(self.themeBox.currentText())
        okPressed = elements.MessageBox.showOK(title="Revert theme to default", parent=self.window(), message=message)
        return okPressed

    def ui_adminSave(self):
        """Saves all themes to the stylesheet within zootools_pro

        :return okPressed: has the ok button been pressed, or was it cancelled
        :rtype okPressed: bool
        """
        message = "Are you sure you want to ADMIN save all themes as defaults?"
        # TODO parent is set to None to default to Maya stylesheeting
        okPressed = elements.MessageBox.showOK(title="Admin theme Save?", parent=self.window(), message=message)
        return okPressed

    def ui_renameWindowPopup(self):
        """rename popup window, returns new name if ok is pressed

        :return newThemeName: the new name of the theme to be renamed
        :rtype newThemeName: str
        """
        currentTheme = self.themeBox.currentText()
        message = "Rename '{}' theme?".format(currentTheme)
        newThemeName = elements.MessageBox.inputDialog(title="Rename Theme",
                                                       text=currentTheme, parent=self.window(),
                                                       message=message)
        return newThemeName

    def ui_deleteWindowPopup(self):
        """delete popup window asking whether to delete a theme

        :return okPressed: has the ok button been pressed, or was it cancelled
        :rtype okPressed: bool
        """
        currentTheme = self.themeBox.currentText()
        message = "Delete the theme \n\n'{}' \n\nThis will permanently delete the theme".format(currentTheme)
        okPressed = elements.MessageBox.showOK(title="Delete Theme?", parent=self.window(), message=message)
        return okPressed

    def getThemeNameList(self):
        """returns a list of theme name (strings) alphabetically sorted

        :return comboNameList: list of theme name (strings) alphabetically sorted
        :rtype comboNameList: list
        """
        comboNameList = list()
        for name, info in self.sheets.items():
            comboNameList.append(str(name))
        comboNameList = [x.encode('UTF8') for x in comboNameList]  # if unicode convert to str
        comboNameList.sort(key=lambda c: c.lower())  # sort alphabetically
        return comboNameList

    def buildGlobalColorsUI(self, themeDict):
        """ Builds the Global Overall Colors section, uses COLOR_GROUP_DICT[colorGroup] to set section color matches

        :param themeDict: a themeDict the sheet from a single theme
        :type themeDict: dict
        :return globalColorsVLayout: the vLayout containing the Global Colors widgets
        :rtype globalColorsVLayout: QLayout
        """
        # get the colors for the initial UI
        colorList = globalColorList(themeDict)
        self.globalColorWidgets = list()
        # build the ui with collapsable frame layout with a grid layout of color swatches inside
        globalColorsVLayout = elements.vBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SPACING)
        collapseWidget = elements.CollapsableFrame("Set Overall Global Colors", parent=self, collapsed=False)
        gridLayout = elements.GridLayout(margins=(uic.SMLPAD, uic.TOPPAD, uic.SMLPAD, uic.BOTPAD),
                                         vSpacing=uic.SREG, hSpacing=uic.SVLRG)
        row, col = 0, 0
        for i, (colorGroup, value) in enumerate(iter(sc.COLORGROUP_ODICT.items())):
            col = i % 2
            if col == 0:
                row += 1
            # convert colour
            colorSrgbInt = color.hexToRGB(colorList[i])  # needs to be in int 255 srgb values
            # Color picker
            colorPicker = elements.ColorBtn(text=colorGroup, parent=self,
                                            colorWidth=100, btnRatio=35, labelRatio=75)
            colorPicker.setColorSrgbInt(colorSrgbInt)
            gridLayout.addWidget(colorPicker, row, col, 1, 1)
            # add the color picker to the self.globalColorWidgets so it can be iterated over later
            self.globalColorWidgets.append(colorPicker)
        collapseWidget.addLayout(gridLayout)
        globalColorsVLayout.addWidget(collapseWidget)
        return globalColorsVLayout

    def buildColorTweakUI(self, themeDict):
        """Divides the stylesheet dict into sections for better UI organisation,
        and builds the collapse-able layout

        Uses the function divideThemeDictToSections(themeDict)

        :param themeDict: a themeDict the sheet from a single theme
        :type themeDict: dict
        """
        sectionKeyValue_odict = divideThemeDictToSections(themeDict)
        # now loop through, build each section UI with a bold QLabel then the section widgets
        collapsed = True
        colorTweakVLayout = elements.vBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SPACING)

        for sectionLabel, styleKeyDict in sectionKeyValue_odict.items():
            collapseWidget = elements.CollapsableFrame(sectionLabel, parent=self, collapsed=collapsed)
            sectionGridWidget = ThemeSectionWidget(styleKeyDict, parent=self)
            collapseWidget.addWidget(sectionGridWidget)
            colorTweakVLayout.addWidget(collapseWidget)
            sectionGridWidget.colorChanged.connect(self.colorChanged)
            # append each section's grid layout, needed later for extraction and updating the data
            self.sectionGridWidgetList.append(sectionGridWidget)

        return colorTweakVLayout

    def colorChanged(self):
        """ Color changed

        :return:
        """
        applyFromThemeDict(self.updateCurrentKeyDict())
        self.themeUnsaved = True
        self.setModified(True)

    def currentTheme(self):
        return self.themeBox.currentText()

    def setGlobalColors(self, colPickerWidget, linearColorFloat):
        """ Called when the user changes a global color, uses COLOR_GROUP_DICT[colorGroup] to set section color matches

        Iterates through the UI sections looking for matches in the color group (using the colPickerWidget label name)
        Will change all matching color pickers to the color from the colPickerWidget

        :param colPickerWidget: a global color widget (Set Overall Global Colors), will retrieve the label name
        :type colPickerWidget: elements.ColorBtn
        """
        if not self.globalColorUpdate:  # bail if this variable is not true, could be switching themes
            return
        # get list of Keys
        colorGroup = colPickerWidget.text()  # the label of the widget
        rgbColor = colPickerWidget.colorSrgbInt()
        keylist = list(sc.COLORGROUP_ODICT[colorGroup])  # need a copy of the list as it breaks with reassign
        changed = False
        # convert to nice names to match labels
        for i, key in enumerate(keylist):
            keylist[i] = themeKeyToName(key)
        # iterate through the UI Sections to see if matches and if so change the color
        for sectionGridWidget in self.sectionGridWidgetList:
            for i in range(sectionGridWidget.gridLayout.count()):
                currentWidget = sectionGridWidget.gridLayout.itemAt(i).widget()
                labelName = currentWidget.text()  # widgets are subclassed and have .text methods (label name)

                for key in keylist:  # check if the labelName is a match
                    if labelName == key:
                        currentWidget.setColorSrgbInt(rgbColor)
                        changed = True

        if changed:
            self.colorChanged()

    def updateGlobalUIColorSwatches(self):
        """ Updates the color swatch widgets in the Global grid layout to match the first key in
        each COLOR_GROUP_DICT

        Get the colors from the theme name set in the 'Theme' combo box
        """
        themeName = self.themeBox.currentText()
        themeDict = self.sheets[themeName]
        colorList = globalColorList(themeDict)
        row, col = 0, 0
        # shouldn't update the Style By Widget section so set temp variable to stop the update
        self.globalColorUpdate = False
        for i, (colorGroup, value) in enumerate(iter(sc.COLORGROUP_ODICT.items())):
            col = i % 2
            if col == 0:
                row += 1
            colorSrgbInt = color.hexToRGB(colorList[i])  # rgb is in 255 values
            self.globalColorWidgets[i].setColorSrgbInt(colorSrgbInt)  # set the widget color
        self.globalColorUpdate = True

    def onThemeChanged(self, event=None):
        """ When the theme is changed in the Theme combo box, update the UI to match the current theme

        :param event: Event with all the values related to the change.
        :type event: zoo.libs.pyqt.extended.combobox.ComboItemChangedEvent
        :return:
        :rtype:
        """

        theme = self.currentTheme()

        if self.themeUnsaved:
            msg = "There are unsaved changes for '{}'. Do you wish to save?".format(event.prevText)
            # buttonPressed = elements.MessageBox.showOK(windowName="Save File", parent=None, message=msg)

            result = elements.MessageBox.showQuestion(title="Save Preference", parent=self.window(), message=msg,
                                                      buttonA="OK", buttonB="No", buttonC="Cancel")
            if result == "A":  # Ok
                self.serialize(event.prevText)
            elif result == "B":  # No
                pass
            else:  # Cancel
                self.themeBox.blockSignals(True)
                self.themeBox.setIndex(event.prevIndex)
                self.themeBox.blockSignals(False)
                return
            self.themeUnsaved = False

        self.setThemeUI(theme)
        self.setModified(True)

    def setThemeUI(self, theme):
        """ Sets the theme in the ui

        :param theme: the theme name
        :rtype theme: str
        """
        sheet = self.prefInterface.stylesheetForTheme(theme)  # the qss text for this theme
        self.themeWindow.setStyleSheet(sheet.data)  # updates the test window
        applyTheme(theme)

        # update the UI
        themeDict = self.sheets[theme]
        sectionKeyValue_odict = divideThemeDictToSections(themeDict)  # returns a OrderedDict(OrderedDict)
        for i, (sectionLabel, sectionDict) in enumerate(iter(sectionKeyValue_odict.items())):
            self.sectionGridWidgetList[i].buildSection(sectionDict)  # clears and rebuilds the grid section layout
        self.updateGlobalUIColorSwatches()  # updates the Overall Global Colors

    def updateCurrentKeyDict(self):
        """ Updates the current dict (one theme only) from current widget settings

        :return self.allCurrentThemeDict: Updates the current dict (one theme only) from current widget settings
        :rtype self.allCurrentThemeDict: dict
        """

        self.allCurrentThemeDict = self.prefInterface.themeDict(self.currentTheme())  # convert to theme dict
        for i, sectionGridWidget in enumerate(self.sectionGridWidgetList):
            sectionDict = sectionGridWidget.data()
            self.allCurrentThemeDict.update(sectionDict)

        return self.allCurrentThemeDict

    def updateSheets(self):
        """ Update sheets (all theme dicts) with all new settings from preference.interface("core_interface")"""

        self.prefs = self.prefInterface.settings().settings
        self.sheets = self.prefs["themes"]

    def serialize(self, theme=None):
        """ Save the Preference file,  saves the current theme and it's dict

        Can update a current theme or add a new theme too.

        Iterate over the grid widget sections adding their dicts together to make a master stylesheet dictionary
        save it to the prefs directory as a json under the current theme name from the theme combo box.

        Keen note: Feels like this should be handled in the PreferenceManager class instead.
        """
        data = self.prefInterface.preference.findSetting(InterfaceWidget.prefDataRelativePath, root=None)
        if data.isValid():
            theme = theme or self.themeBox.currentText()
            # iterate over the section grid layouts to create the dictionary
            data['settings']['themes'][theme] = self.updateCurrentKeyDict()  # save or add the theme dict to disk
            data['settings']['current_theme'] = theme  # save the current theme name to disk
            path = data.save(indent=True, sort=True)  # dump format nicely
            output.displayInfo("Success: Theme '{}' Saved To Disk '{}'".format(theme, path))
            self.themeUnsaved = False
            self.updateSheets()
        return True

    def revert(self):
        """ Revert settings

        :return:
        """
        # Reset stylesheet

        self.themeUnsaved = False
        theme = self.prefInterface.currentTheme()
        self.themeBox.setToText(theme)
        self.setThemeUI(theme)
        applyTheme(theme)
        self.setModified(False)

    def adminSave(self):
        """ Admin save to /Preferences/prefs/global/stylesheet.pref for setting Zoo Defaults

        Will set all current settings as the Zoo Defaults for everyone

        :return:
        """

        okPressed = self.ui_adminSave()
        if not okPressed:
            output.displayInfo("Admin Save Cancelled")
            return
        data = self.prefInterface.preference.findSetting(InterfaceWidget.prefDataRelativePath, root=None)
        if data.isValid():
            zoo_preferences_package_root = self.prefInterface.preference.packagePreferenceRootLocation(
                "zoo_preferences")
            stylesheetAdminPath = zoo_preferences_package_root / InterfaceWidget.prefDataRelativePath
            theme = self.themeBox.currentText()
            # self.updateCurrentKeyDict() = iterate over the section grid layouts to create the dictionary
            data['settings']['themes'][theme] = self.updateCurrentKeyDict()  # save or add the theme dict to disk
            data['settings']['current_theme'] = theme  # save the current theme name to disk
            saveFileDict = dict()
            saveFileDict['settings'] = data['settings']  # file should only have one key, 'settings', data has more
            filesystem.saveJson(saveFileDict, str(stylesheetAdminPath), indent=2, sort_keys=True)
            output.displayInfo("Admin Save: All Themes Saved To Disk '{}'".format(stylesheetAdminPath))
            self.themeUnsaved = False

    def createTheme(self):
        """ Adds a new Theme to the combo box

        Saves the data to the user preferences stylesheet.pref and sets combo box

        :return:
        """
        newThemeName = self.ui_createWindowPopup()
        if not newThemeName:
            output.displayInfo("Theme creation cancelled")
            return
        self.themeBox.blockSignals(True)
        self.themeBox.addItem(newThemeName)
        self.themeBox.model().sort(0)  # sorts alphabetically
        self.themeBox.setToText(newThemeName)
        # save the data
        self.serialize()  # saves to disk with current settings
        self.themeBox.blockSignals(False)
        self.updateSheets()  # update all theme dicts

    def renameTheme(self):
        """ Rename theme

        :return:
        :rtype:
        """
        oldThemeName = self.themeBox.currentText()
        newThemeName = self.ui_renameWindowPopup()

        if newThemeName == "":
            return

        # rename and save the prefs dict
        data = self.prefInterface.preference.findSetting(InterfaceWidget.prefDataRelativePath, root=None)
        if data.isValid():
            data['settings']['themes'][newThemeName] = data['settings']['themes'].pop(oldThemeName)  # rename the key
            data['settings']['current_theme'] = newThemeName  # save the current theme name to disk
            data.save(indent=True, sort=True)  # dump format nicely
            output.displayInfo("Success: Theme '{}' Renamed To {}".format(oldThemeName, newThemeName))

        # update the combo box
        self.themeBox.blockSignals(True)
        self.themeBox.addItem(newThemeName)
        self.themeBox.model().sort(0)  # sorts alphabetically
        self.themeBox.setToText(newThemeName)
        self.themeBox.removeItemByText(oldThemeName)
        self.themeBox.blockSignals(False)
        self.updateSheets()  # update all theme dicts

    def deleteTheme(self):
        """ Delete theme

        :return:
        :rtype:
        """
        okPressed = self.ui_deleteWindowPopup()
        if not okPressed:
            output.displayInfo("Delete Cancelled")
            return
        currentTheme = self.themeBox.currentText()
        data = self.prefInterface.preference.findSetting(InterfaceWidget.prefDataRelativePath, root=None)
        if data.isValid():
            data['settings']['themes'].pop(currentTheme)  # delete the current theme dict
            # Combo Box current theme update
            self.themeBox.removeItemByText(currentTheme)
            self.themeBox.setIndex(0)
            newThemeName = self.themeBox.currentText()
            data['settings']['current_theme'] = newThemeName  # save the current theme name to disk
            data.save(indent=True)  # dump = format nicely
            # self.onThemeChanged()  # update widgets to first theme
            output.displayInfo(
                "Success: Theme '{}' has been deleted and all themes have been saved".format(currentTheme))

    def connections(self):
        """ Connect Up The UI

        :return:
        """
        self.themeExampleBtn.clicked.connect(self.themeWindow.show)
        self.revertThemeBtn.clicked.connect(self.revertTheme)
        self.themeBox.itemChanged.connect(self.onThemeChanged)  # combo updates
        self.adminSaveBtn.clicked.connect(self.adminSave)
        self.createNewThemeBtn.clicked.connect(self.createTheme)
        self.renameThemeBtn.clicked.connect(self.renameTheme)
        self.deleteThemeBtn.clicked.connect(self.deleteTheme)

        for widget in self.globalColorWidgets:  # if global colors are changed
            widget.colorChanged.connect(partial(self.setGlobalColors, widget))  # also emits a linearColorFloat

    def revertTheme(self):
        """ Revert current theme

        :return:
        :rtype:
        """
        if self.ui_revertThemePopup():
            self.prefInterface.revertThemeToDefault(save=True)
            theme = self.themeBox.currentText()
            self.setThemeUI(theme)

    def themeBoxTheme(self):
        return self.themeBox.currentText()


class ThemeSectionWidget(QtWidgets.QWidget):
    colorChanged = QtCore.Signal(tuple)

    def __init__(self, themeDict, parent=None):
        super(ThemeSectionWidget, self).__init__(parent=parent)
        self.gridLayout = elements.GridLayout(parent=self, margins=(uic.SMLPAD, uic.TOPPAD, uic.SMLPAD, uic.BOTPAD),
                                              vSpacing=uic.SREG, hSpacing=uic.SVLRG)
        self.buildSection(themeDict)

    def buildSection(self, themeDict):
        """Builds the UI colors and text box widgets from the current theme

        Automatically figures the type of widgets to build:

            Pixel Scale
            Color
            Icon
            Other (usually regular number, not px scale)

        :param themeDict: The theme dictionary, with all the keys and colors for the current theme
        :type themeDict: dict
        """
        self.clearLayout()

        row, col = 0, 0
        for i, key in enumerate(themeDict.keys()):
            col = i % 2
            if col == 0:
                row += 1
            # int pixel scale
            if stylesheet.valueType(themeDict[key]) == stylesheet.DPI_SCALE:
                textLabel = StyleTextWidget(themeKeyToName(key), key, parent=self,
                                            textType=StyleTextWidget.TYPE_DPISCALE)
                self.gridLayout.addWidget(textLabel, row, col, 1, 1)
                textLabel.setText(str(themeDict[key][1:]))
            # Color
            elif stylesheet.valueType(themeDict[key]) == stylesheet.COLOR:
                colorSrgbInt = color.hexToRGB(themeDict[key])  # needs to be in int 255 srgb values
                colWidget = elements.ColorBtn(text=themeKeyToName(key), key=key,
                                              parent=self, colorWidth=100, labelRatio=65, btnRatio=35)
                colWidget.setColorSrgbInt(colorSrgbInt)
                colWidget.colorChanged.connect(self.colorChanged.emit)
                self.gridLayout.addWidget(colWidget, row, col, 1, 1)
            # Icon
            elif stylesheet.valueType(themeDict[key]) == stylesheet.ICON:
                textLabel = StyleTextWidget(themeKeyToName(key), key, parent=self,
                                            textType=StyleTextWidget.TYPE_ICON)

                self.gridLayout.addWidget(textLabel, row, col, 1, 1)
                textLabel.setText(str(themeDict[key][5:]))
            # other?
            else:
                textLabel = StyleTextWidget(themeKeyToName(key), key, parent=self)
                self.gridLayout.addWidget(textLabel, row, col, 1, 1)
                textLabel.setText(str(themeDict[key]))
        # set columns to be the same width, the Maya color widgets don't scale well though
        self.gridLayout.setColumnStretch(0, 1)
        self.gridLayout.setColumnStretch(1, 1)

    def clearLayout(self):
        """deletes all widgets of the current Color/Text layout
        """
        utils.clearLayout(self.gridLayout)

    def data(self):
        """ Iterates through the grid layout and returns a themeDict with the updated data.

        widget.data() is retrieved by the class.method:
            StyleTextWidget().keyHex()
            or
            ColorBtn.ColorCmdsWidget().keyHex()

        :return themeDict: A theme dictionary with the new values
        :rtype themeDict: dict
        """
        themeDict = {}

        for i in range(self.gridLayout.count()):
            widget = self.gridLayout.itemAt(i).widget()
            # update the dictionary for a single key value
            # for colors will be like "FRAMELESS_TITLELABEL_COLOR", and value is in hex "ffffff"
            # for string edits "BTN_PADDING" and value might be "30"
            themeDict.update(widget.data())  #

        return themeDict


class ThemeInputWidget(QtWidgets.QWidget):
    def __init__(self, key=None, parent=None):
        """ A generic input widget for the themes in preferences

        :param key: The stylesheet pref key eg. "FRAMELESS_TITLELABEL_COLOR"
        :param parent:
        """
        super(ThemeInputWidget, self).__init__(parent=parent)

        self.key = key

    def data(self):
        pass


class StyleTextWidget(ThemeInputWidget):
    """Builds a text style widget "label/lineEdit" usually from stylesheet keys

        Builds a qLabel and text box (qLineEdit) with:
            text "Title Fontsize"
            key "$TITLE_FONTSIZE"

        textType:
            TYPE_DEFAULT = 0
            TYPE_DPISCALE = 1
            TYPE_ICON = 2
    """
    TYPE_DEFAULT = 0
    TYPE_DPISCALE = 1
    TYPE_ICON = 2

    def __init__(self, text="", key=None, parent=None, textType=TYPE_DEFAULT):
        """Builds a text style widget "label/lineEdit" from stylesheet keys

        Builds a qLabel and text box (qLineEdit) with:
            text "Title Fontsize"
            key "$TITLE_FONTSIZE"

        textType:
            TYPE_DEFAULT = 0
            TYPE_DPISCALE = 1
            TYPE_ICON = 2

        :param text: The text title of the QLabel, a nice string version of the Key Eg. "Title Fontsize"
        :type text: str
        :param key: The key from the stylsheet theme Eg. "$TITLE_FONTSIZE"
        :type key: str
        :param parent: the parent widget
        :type parent: QtWidget
        :param textType: The type of widget to build or return TYPE_DEFAULT = 0, TYPE_DPISCALE = 1, TYPE_ICON = 2
        :type textType: int
        """
        super(StyleTextWidget, self).__init__(parent=parent, key=key)
        layout = elements.hBoxLayout(self)
        self.textEdit = elements.LineEdit("", parent=self, fixedWidth=100)
        self.label = QtWidgets.QLabel(parent=self, text=text)
        layout.addWidget(self.label, 65)
        layout.addWidget(self.textEdit, 35)
        self.textType = textType

    def text(self):
        """returns the label name"""
        return self.label.text()

    def data(self):
        """Returns the current values of the current widget depending on the textType:

            TYPE_DEFAULT = 0
            TYPE_DPISCALE = 1
            TYPE_ICON = 2

        :return widgetValue: the value of the widget as a int or str depending on the textType
        :rtype widgetValue: in/str
        """
        if self.textType == StyleTextWidget.TYPE_DEFAULT:
            return {self.key: int(self.textEdit.text())}
        elif self.textType == StyleTextWidget.TYPE_DPISCALE:
            return {self.key: "^{}".format(self.textEdit.text())}
        elif self.textType == StyleTextWidget.TYPE_ICON:
            return {self.key: "icon:{}".format(self.textEdit.text())}

    def __getattr__(self, item):
        """ Use StyleTextWidget like a LineEdit

        :param item:
        :return:
        """
        return getattr(self.textEdit, item)





def applyTheme(theme):
    """ Applies the theme to all the open windows

    :param theme:
    :type theme:
    :return:
    :rtype:
    """
    themePref = coreinterfaces.coreInterface()
    stylesheet = themePref.stylesheetForTheme(theme).data
    themeDict = themePref.themeDict(theme)

    applyStyleSheet(stylesheet, themeDict)


def applyFromThemeDict(themeDict):
    """ Apply the stylesheet based on the theme dictionary

    :param themeDict:
    :type themeDict: preferences.interface.themedict.ThemeDict
    :return:
    :rtype:
    """
    themePref = coreinterfaces.coreInterface()
    styleSheet = themePref.stylesheetFromData(themeDict).data
    applyStyleSheet(styleSheet, themeDict)


def applyStyleSheet(styleSheet, themeDict):
    """

    :param styleSheet:
    :type styleSheet:
    :param themeDict:
    :type themeDict: preferences.interface.themedict.ThemeDict
    :return:
    :rtype:
    """

    # For some reason it doesn't update the stylesheet until you set the style sheet of the first child
    themePref = coreinterfaces.coreInterface()
    for w in reversed(window.getZooWindows()):
        firstChild = utils.firstVisibleChild(w)
        if firstChild:
            firstChild.setStyleSheet("")
    from zoo.core import engine
    currentEngine = engine.currentEngine()
    currentEngine.setStyleSheet(styleSheet)
    themePref.emitUpdateSignal(styleSheet, themeDict)


def globalColorList(themeDict):
    """Returns the global hex color list from the first color in each key of the given themeDict

    Used to set the "Overall Global Colors" in the UI

    :param themeDict: a themeDict the sheet from a single theme
    :type themeDict: dict
    :return colorListLinear: the list of colors in hex that match the COLOR_GROUP_LIST
    :rtype colorListLinear: list(str)
    """
    colorList = list()
    for colorGroup, value in sc.COLORGROUP_ODICT.items():
        stylesheetKeyList = sc.COLORGROUP_ODICT[colorGroup]
        if stylesheetKeyList:  # could be empty dict
            colorHex = themeDict[stylesheetKeyList[0]]  # color (Hex) from the first Stylesheet Key entry
            colorList.append(colorHex)
        else:  # there are no widgets
            colorList.append(uic.COLOR_ERROR)  # fluorescent green
    return colorList


def themeKeyToName(key):
    """Converts the Key name in caps with underscores to a nice title string:

        "$TITLE_FONTSIZE" is returned as "Title Fontsize"

    :param key: The title key from the theme dictionary Eg. "TITLE_FONTSIZE"
    :type key: str
    :return labelTitle: The title now lowercase and with Upperscase first letters Eg. "Title Fontsize"
    :rtype labelTitle: str
    """
    uppercaseText = key.replace("_", " ").replace("$", "").upper()
    return uppercaseText.lower().title()  # lowercase and title uppercase first letters


def divideThemeDictToSections(themeDict):
    """create the section dicts now with colors/values OrderedDict(OrderedDict()):

        sectionLabel([stylesheetKey, value])

    :param themeDict: a themeDict the sheet from a single theme, Stylesheet Keys and values
    :type themeDict: dict
    :return sectionKeyValue_odict: And ordered dict of an orderedDict sectionLabel([stylesheetKey, value])
    :rtype sectionKeyValue_odict: orderedDict(orderedDict)
    """
    # create the section dicts now
    copyThemeDict = dict(themeDict)
    sectionKeyValue_odict = collections.OrderedDict()
    # create the sectionKeyValue_odict
    for i, (sectionLabel, keyList) in enumerate(iter(sc.SECTION_ODICT.items())):
        keyValue_odict = collections.OrderedDict()
        for key in keyList:
            try:
                del copyThemeDict[key]
            except KeyError:
                pass
            keyValue_odict[key] = themeDict[key]

        sectionKeyValue_odict[sectionLabel] = keyValue_odict
    if copyThemeDict:  # then there are leftover keys, add them to the last list - otherSettingsDict
        logger.debug("Zoo Admin: Stylesheets 'stylesheetui_constants.py' is missing the key/s {}".format(copyThemeDict))
    return sectionKeyValue_odict
