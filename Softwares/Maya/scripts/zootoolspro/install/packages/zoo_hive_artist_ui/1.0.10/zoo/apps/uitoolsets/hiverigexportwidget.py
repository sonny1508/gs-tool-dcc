import os
from functools import partial
from collections import OrderedDict

from zoo.apps.hiveartistui import uiinterface
from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.libs import iconlib
from zoo.libs.hive import api as hiveapi
from zoo.libs.maya.api import anim
from zoo.libs.maya.cmds.filemanage import saveexportimport
from zoo.libs.maya.utils import fbx as fbxutils
from zoo.libs.maya.utils import general
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements
from zoo.libs.utils import output
from zoovendor.Qt import QtWidgets, QtCore

from zoo.libs.utils import general as libgeneral

if libgeneral.TYPE_CHECKING:
    # changed to TYPE_CHECKING to avoid circular import
    pass
from zoo.libs.hive.library.exporters import fbxexporter

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1

WORLD_UP_LIST = ["Y", "Z"]

FBX_WORLD_UP_KEY = "worldUp"
FBX_VERSION_KEY = "fbxVersion"
PRESET_DICT = OrderedDict()

PRESET_DICT['Custom Preset - None'] = {}
PRESET_DICT['3dsMax 2018'] = {FBX_WORLD_UP_KEY: "Z",
                              FBX_VERSION_KEY: "FBX 2018"}
PRESET_DICT['3dsMax 2019'] = {FBX_WORLD_UP_KEY: "Z",
                              FBX_VERSION_KEY: "FBX 2019"}
PRESET_DICT['3dsMax 2020'] = {FBX_WORLD_UP_KEY: "Z",
                              FBX_VERSION_KEY: "FBX 2020"}
PRESET_DICT['Houdini 17'] = {FBX_WORLD_UP_KEY: "Y",
                             FBX_VERSION_KEY: "FBX 2018"}
PRESET_DICT['Unity 2021'] = {FBX_WORLD_UP_KEY: "Y",
                             FBX_VERSION_KEY: "FBX 2020"}
PRESET_DICT['Unity 2022'] = {FBX_WORLD_UP_KEY: "Y",
                             FBX_VERSION_KEY: "FBX 2020"}
PRESET_DICT['Unreal 4'] = {FBX_WORLD_UP_KEY: "Y",
                           FBX_VERSION_KEY: "FBX 2018"}
PRESET_DICT['Unreal 5'] = {FBX_WORLD_UP_KEY: "Y",
                           FBX_VERSION_KEY: "FBX 2020"}

SAVE_SCENE_MSG = "WARNING: This scene will be destroyed in the process of FBX exporting. \n\n" \
                 "Zoo Tools will close and reload this Maya scene file after the FBX export completes.\n\n" \
                 "Save the current file to avoid losing changes?"


class HiveRigExportToolset(toolsetwidget.ToolsetWidget):
    id = "hiveFbxRigExport"
    info = "Hive Fbx rig export tool."
    uiData = {"label": "Hive Export FBX",
              "icon": "hiveExportFbx",
              "tooltip": "Provides an Fbx exporter for hive rigs.",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-hive-export-fbx"}

    def preContentSetup(self):
        general.loadPlugin("fbxmaya")
        # force to 2018 since anything below this isn't support by games
        self._fbxVersions = list(fbxutils.availableFbxVersions(ignoreBeforeVersion="2018"))

    def contents(self):
        """The UI Modes to build, compact, medium and or advanced """
        return [self.initCompactWidget()]

    def initCompactWidget(self):
        """Builds the Compact GUI (self.compactWidget) """
        self.compactWidget = GuiCompact(parent=self, properties=self.properties, toolsetWidget=self)
        return self.compactWidget

    def postContentSetup(self):
        """Last of the initialize code"""
        self.uiFolderPath = ""
        self.optionsRadioChanged()  # Updates the UI visibility of widgets depending on the options radio
        # Update a rig list done in post because we have signals getting emitted by
        # hive UI which require a reload of the list as well.
        self._rigStateChanged()  # Updates the rig combo box
        self.loadUISettingsScene()  # Loads the UI settings from the scene if it exists
        self.uiConnections()

    @property
    def defaultBrowserPath(self):
        outputDirectory = os.path.expanduser("~")
        if not saveexportimport.isCurrentSceneUntitled():
            currentScenePath = saveexportimport.currentSceneFilePath()
            outputDirectory = os.path.dirname(currentScenePath)
        return outputDirectory

    def initializeProperties(self):
        """Used to store and update UI data

        For use in the GUI use:
            current value: self.properties.itemName.value
            default value (automatic): self.properties.itemName.default

        To connect Qt widgets to property methods use:
            self.toolsetWidget.linkProperty(self.widgetQtName, "itemName")

        :return properties: special dictionary used to save and update all GUI widgets
        :rtype properties: list(dict)
        """
        general.loadPlugin("fbxmaya")
        # temporary so we grab 2018 by default, later we'll have presets.
        total = len(list(fbxutils.availableFbxVersions(ignoreBeforeVersion="2018")))
        timeInfo = anim.currentTimeInfo()
        return [
            {"name": "triangulateCheckBox", "value": 1},
            {"name": "blendshapeCheckBox", "value": 1},
            {"name": "fbxFormatCombo", "value": 0},
            {"name": "worldAxisCombo", "value": 0},
            {"name": "rigListCombo", "value": 0},
            {"name": "fbxVersionCombo", "value": total - 1},
            {"name": "animationCheckBox", "value": 1},
            {"name": "meshCheckBox", "value": 1},
            {"name": "startEndFrameAnim", "value": [timeInfo["start"].value, timeInfo["end"].value]},
            {"name": "filePathEdit", "value": ""},
            {"name": "meshCheckBox", "value": 1},
            {"name": "skinningCheckBox", "value": 1}
        ]

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiAdvanced or GuiCompact]
        """
        return super(HiveRigExportToolset, self).widgets()

    # ------------------
    # ENTER
    # ------------------

    def enterEvent(self, event):
        """When the cursor enters the UI update it"""
        self._rigStateChanged()

    # -------------------
    # HIVE CORE SIGNALS
    # -------------------

    def _rigStateChanged(self):
        self._updateSceneRigs()
        for widget in self.widgets():
            widget.updateRigs(self.rigComboNames)

    def _updateSceneRigs(self):
        self.rigComboNames, self.rigInstances = fbxexporter.allRigsComboUI()

    def _currentRigChangedFromArtistUI(self, rigName):
        for widget in self.widgets():
            widget.setCurrentRig(rigName)

    def fbxVersionLabels(self):
        return [i for _, i in self._fbxVersions]

    # -------------------
    # SAVE AND LOAD UI SETTINGS METHODS
    # -------------------

    def uiSettingsDict(self):
        uiSettingsDict = dict()
        self.updateUISettings()
        uiSettingsDict["uiRadioSettings"] = self.uiRadioSettings
        uiSettingsDict["rigCombo"] = self.rigCombo
        uiSettingsDict["outputFolder"] = self.outputFolder
        uiSettingsDict["outputFilePath"] = self.outputFilePath
        uiSettingsDict["uiNamesStr"] = self.uiNamesStr
        uiSettingsDict["uiFrameRangesStr"] = self.uiFrameRangesStr
        uiSettingsDict["uiRigsStr"] = self.uiRigsStr
        uiSettingsDict["suffixName"] = self.suffixName
        uiSettingsDict["prefixCheckbox"] = self.prefixCheckbox
        uiSettingsDict["meshes"] = self.meshes
        uiSettingsDict["versionCombo"] = self.versionCombo
        uiSettingsDict["shapes"] = self.shapes
        uiSettingsDict["presetCombo"] = self.presetCombo
        uiSettingsDict["axisCombo"] = self.axisCombo
        uiSettingsDict["triangulate"] = self.triangulate
        uiSettingsDict["ascii"] = self.ascii
        uiSettingsDict["animation"] = self.animation
        uiSettingsDict["startEndFrameSingle"] = self.startEndFrameSingle
        uiSettingsDict["meshes"] = self.meshes
        uiSettingsDict["skins"] = self.skins
        return uiSettingsDict

    def setUiSettings(self, uiSettingsDict):
        self.properties.optionsRadio.value = uiSettingsDict["uiRadioSettings"]
        self.compactWidget.optionsRadio.radioButtons[uiSettingsDict["uiRadioSettings"]].setChecked(True)
        self.optionsRadioChanged()  # Updates the visibility of the widgets depending on the options radio.
        self.compactWidget.folderPathEdit.setPathText(uiSettingsDict["outputFolder"])
        self.compactWidget.filePathEdit.setPathText(uiSettingsDict["outputFilePath"])
        self.compactWidget.nameOverrideEdit.setPlainText(uiSettingsDict["uiNamesStr"])
        self.compactWidget.timerangesEdit.setPlainText(uiSettingsDict["uiFrameRangesStr"])
        self.compactWidget.rigsEdit.setPlainText(uiSettingsDict["uiRigsStr"])
        self.properties.suffixNameStr.value = uiSettingsDict["suffixName"]
        self.properties.prefixRigNameCheckBox.value = uiSettingsDict["prefixCheckbox"]
        self.properties.meshCheckBox.value = uiSettingsDict["meshes"]
        self.properties.fbxVersionCombo.value = uiSettingsDict["versionCombo"]
        self.properties.blendshapeCheckBox.value = uiSettingsDict["shapes"]
        self.properties.presetsCombo.value = uiSettingsDict["presetCombo"]
        self.properties.worldAxisCombo.value = uiSettingsDict["axisCombo"]
        self.properties.triangulateCheckBox.value = uiSettingsDict["triangulate"]
        self.properties.fbxFormatCombo.value = uiSettingsDict["ascii"]
        self.properties.animationCheckBox.value = uiSettingsDict["animation"]
        self.properties.startEndFrameAnim.value = uiSettingsDict["startEndFrameSingle"]
        self.properties.meshCheckBox.value = uiSettingsDict["meshes"]
        self.properties.skinningCheckBox.value = uiSettingsDict["skins"]
        self.updateFromProperties()  # update UI
        try:  # setting the rig could mess up easily so handle separately
            self.compactWidget.rigListCombo.setIndex(uiSettingsDict["rigCombo"])
        except:
            pass
        # Set checkbox enable/disable states --------------------------
        animState = True
        triState = True
        skinState = True
        shapeState = True
        if not self.properties.animationCheckBox.value:
            animState = False
        if not self.properties.meshCheckBox.value:
            triState = False
            skinState = False
            shapeState = False
        self.compactWidget.startEndFrameAnim.setEnabled(animState)
        self.compactWidget.triangulateCheckBox.setEnabled(triState)
        self.compactWidget.skinningCheckBox.setEnabled(skinState)
        self.compactWidget.blendshapeCheckBox.setEnabled(shapeState)

    def saveUiSettingsScene(self):
        """Saves the uiSettingsDict to the scene."""
        uiSettingsDict = self.uiSettingsDict()
        fbxexporter.saveUIExportSettingsScene(uiSettingsDict)

    def loadUISettingsScene(self):
        """Loads the uiSettingsDict from the scene."""
        uiSettingsDict = fbxexporter.loadUIExportSettingsScene()
        if not uiSettingsDict:
            return
        self.setUiSettings(uiSettingsDict)

    def saveUiSettingsDisk(self):
        """Saves the uiSettingsDict to a file on disk."""
        if not self.uiFolderPath:
            self.uiFolderPath = self.defaultBrowserPath
        filePath, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save the UI Settings File",
                                                            self.defaultBrowserPath, "*.zooFbxUi")
        if not filePath:  # cancel
            return
        self.uiFolderPath = os.path.dirname(filePath)  # update the default browser path
        fbxexporter.saveUIExportSettingsFile(self.uiSettingsDict(), filePath)
        output.displayInfo("Saved UI Settings to: {}".format(filePath))

    def loadUISettingsDisk(self):
        """Loads the uiSettingsDict from a file on disk."""
        if not self.uiFolderPath:
            self.uiFolderPath = self.defaultBrowserPath
        filePath, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open FBX UI Settings File",
                                                            dir=self.uiFolderPath,
                                                            filter="*.zooFbxUi")
        if not filePath:  # cancel
            return
        uiSettingsDict = fbxexporter.loadUIExportSettingsFile(filePath)
        if not uiSettingsDict:
            return
        self.uiFolderPath = os.path.dirname(filePath)  # update the default browser path
        self.setUiSettings(uiSettingsDict)
        output.displayInfo("UI settings file set: {}".format(filePath))

    # -------------------
    # UI METHODS
    # -------------------

    def updateUISettings(self):
        """Updates all the class variables UI based on the current settings"""
        if not self.rigInstances:
            self.rigInstance = None
            self.rigName = ""
        else:
            self.rigInstance = self.rigInstances[self.properties.rigListCombo.value]
            self.rigName = self.rigComboNames[self.properties.rigListCombo.value]

        self.outputFolder = self.compactWidget.folderPathEdit.path()
        self.outputFilePath = self.compactWidget.filePathEdit.path()
        self.uiNamesStr = self.compactWidget.nameOverrideEdit.toPlainText()
        self.uiFrameRangesStr = self.compactWidget.timerangesEdit.toPlainText()
        self.uiRigsStr = self.compactWidget.rigsEdit.toPlainText()
        self.clipNames = fbxexporter.strToClipNameListUI(str(self.uiNamesStr))
        self.startEndList = fbxexporter.strToFrameRangeListUI(str(self.uiFrameRangesStr))
        self.rigNames = fbxexporter.strToRigListUI(str(self.uiRigsStr))
        self.suffixName = self.properties.suffixNameStr.value
        if self.properties.prefixRigNameCheckBox.value:
            self.prefixName = self.rigName
        else:
            self.prefixName = ""
        # FBX Settings --------------------------
        self.meshes = self.properties.meshCheckBox.value
        self.version = self._fbxVersions[self.properties.fbxVersionCombo.value][0]  # the actual FBX not display label
        self.shapes = self.properties.blendshapeCheckBox.value and self.meshes
        self.axis = {0: "y", 1: "z"}.get(self.properties.worldAxisCombo.value)
        self.triangulate = self.properties.triangulateCheckBox.value and self.meshes
        self.ascii = self.properties.fbxFormatCombo.value  # 1 is ascii
        self.animation = self.properties.animationCheckBox.value
        self.startEndFrameSingle = self.properties.startEndFrameAnim.value
        self.meshes = self.meshes
        self.skins = self.properties.skinningCheckBox.value and self.meshes
        self.interactive = True
        # Missing UI Settings --------------------------
        self.uiRadioSettings = self.properties.optionsRadio.value
        self.rigCombo = self.properties.rigListCombo.value
        self.prefixCheckbox = self.properties.prefixRigNameCheckBox.value
        self.versionCombo = self.properties.fbxVersionCombo.value
        self.presetCombo = self.properties.presetsCombo.value
        self.axisCombo = self.properties.worldAxisCombo.value

    def optionsRadioChanged(self):
        """Shows and hides the appropriate widgets based on the radio button selection.
        0 = Single Export
        1 = Multiple Timerange
        2 = Multiple Rigs
        """
        radioInt = self.properties.optionsRadio.value

        # Hide all widgets -----------------
        rigDividerVis = False
        rigListComboVis = False

        rigsDividerVis = False
        rigsEditVis = False
        addRigsBtnVis = False

        filePathDividerVis = False
        filePathEditVis = False

        folderPathDividerVis = False
        folderPathEditVis = False

        fileNamesDividerVis = False
        suffixNameStrVis = False
        prefixRigNameCheckBoxVis = False
        nameOverrideEditVis = False
        addBookmarkNamesBtnVis = False

        timerangesEditVis = False
        addBookmarkRangesBtnVis = False
        animationCheckBoxVis = False
        startEndFrameAnimVis = False

        # Set the visibility of the widgets -----------------
        if radioInt == 0:
            rigDividerVis = True
            rigListComboVis = True
            filePathDividerVis = True
            filePathEditVis = True
            animationCheckBoxVis = True
            startEndFrameAnimVis = True
        elif radioInt == 1:
            rigDividerVis = True
            rigListComboVis = True
            folderPathDividerVis = True
            folderPathEditVis = True
            fileNamesDividerVis = True
            prefixRigNameCheckBoxVis = True
            nameOverrideEditVis = True
            addBookmarkNamesBtnVis = True
            timerangesEditVis = True
            addBookmarkRangesBtnVis = True
        else:  # radioInt == 2
            rigsDividerVis = True
            rigsEditVis = True
            addRigsBtnVis = True
            folderPathDividerVis = True
            folderPathEditVis = True
            fileNamesDividerVis = True
            suffixNameStrVis = True
            animationCheckBoxVis = True
            startEndFrameAnimVis = True

        # Set the visibility of the widgets -----------------
        self.compactWidget.rigDivider.setVisible(rigDividerVis)
        self.compactWidget.rigListCombo.setVisible(rigListComboVis)

        self.compactWidget.rigsDivider.setVisible(rigsDividerVis)
        self.compactWidget.rigsEdit.setVisible(rigsEditVis)
        self.compactWidget.addRigsBtn.setVisible(addRigsBtnVis)

        self.compactWidget.filePathDivider.setVisible(filePathDividerVis)
        self.compactWidget.filePathEdit.setVisible(filePathEditVis)

        self.compactWidget.folderPathDivider.setVisible(folderPathDividerVis)
        self.compactWidget.folderPathEdit.setVisible(folderPathEditVis)

        self.compactWidget.fileNamesDivider.setVisible(fileNamesDividerVis)
        self.compactWidget.suffixNameStr.setVisible(suffixNameStrVis)
        self.compactWidget.prefixRigNameCheckBox.setVisible(prefixRigNameCheckBoxVis)
        self.compactWidget.nameOverrideEdit.setVisible(nameOverrideEditVis)
        self.compactWidget.addBookmarkNamesBtn.setVisible(addBookmarkNamesBtnVis)

        self.compactWidget.timerangesEdit.setVisible(timerangesEditVis)
        self.compactWidget.addBookmarkRangesBtn.setVisible(addBookmarkRangesBtnVis)
        self.compactWidget.animationCheckBox.setVisible(animationCheckBoxVis)
        self.compactWidget.startEndFrameAnim.setVisible(startEndFrameAnimVis)
        # Update UI size ----------------------------
        self.updateTree(delayed=True)  # Refresh GUI size

    def updateMultipleTimerange(self, namesString, frameRangesString, outputFolder):
        """Updates the UI with the given names and frame ranges."""
        if outputFolder:
            self.compactWidget.folderPathEdit.setPathText(outputFolder)
        if namesString:
            self.compactWidget.nameOverrideEdit.setPlainText(namesString)
        if frameRangesString:
            self.compactWidget.timerangesEdit.setPlainText(frameRangesString)

    def addRigsSel(self):
        """Adds the selected rigs to the UI."""
        rigsNamesStr = fbxexporter.rigsFromNodesSelUI()
        if not rigsNamesStr:
            return
        self.compactWidget.rigsEdit.setPlainText(rigsNamesStr)

    def addRigsAll(self):
        """Adds all rigs in the scene to the UI."""
        rigsNamesStr = fbxexporter.allRigsInSceneUI()
        if not rigsNamesStr:
            return
        self.compactWidget.rigsEdit.setPlainText(rigsNamesStr)

    def addFrameRangesBookmarks(self):
        """Adds the time slider bookmark frameranges and names to the UI."""
        namesString, frameRangesString = fbxexporter.bookmarkDataUI()
        self.updateMultipleTimerange(namesString, frameRangesString, "")

    def addFrameRangesGameExporter(self):
        """Adds the frame ranges and clip names from the game exporter to the UI."""
        namesString, frameRangesString, outputFolder = fbxexporter.gameExporterClipDataUI()
        self.updateMultipleTimerange(namesString, frameRangesString, outputFolder)

    # ------------------
    # LOGIC
    # ------------------

    def openMayaGamesExporter(self):
        """Opens the Maya Game Exporter window."""
        fbxexporter.openMayaGameExporter()

    def openTimeSliderBookmark(self):
        """Opens the Create Time Slider Bookmark window."""
        fbxexporter.createTimesliderBookmarkWindow()

    def progressCallback(self, progress, message):
        output.displayInfo("Progress: {}% : {}".format(progress, message))

    def applyPreset(self):
        """Creates light and UI/Viewport settings from a dict preset

        """
        self.updateUISettings()  # updates all the UI settings to class variables for later use.
        self.properties.filePathEdit.value = self.outputFilePath

        dict = list(PRESET_DICT.items())[self.properties.presetsCombo.value][1]
        if not dict:  # is "Custom Preset - None"
            return
        # Set Version --------------------------
        versionList = self.fbxVersionLabels()
        if dict[FBX_VERSION_KEY] in versionList:  # FBX version may not exist
            self.properties.fbxVersionCombo.value = versionList.index(dict[FBX_VERSION_KEY])
        else:
            self.properties.fbxVersionCombo.value = 0
        # Set WORLD UP --------------------------
        self.properties.worldAxisCombo.value = WORLD_UP_LIST.index(dict[FBX_WORLD_UP_KEY])
        # Update UI ---------------------------
        self.updateFromProperties()
        # filePathEdit should already, but isn't so update hack fix.
        self.compactWidget.filePathEdit.setPathText(self.properties.filePathEdit.value)

    def sceneRigs(self):
        """Returns a list of rig names in the scene

        :return: list of rig names in the scene
        :rtype: list(str), list[:class:`zoo.libs.hive.base.rig.Rig`]
        """
        return fbxexporter.allRigsComboUI()

    def _uiRigModel(self):
        """Query from Hive UI the rig model instance. This is so we can sync between the UIs
        """
        hiveUICore = uiinterface.instance().core()
        # todo: support running without the artist ui
        if hiveUICore is None:
            output.displayWarning("Hive Artist UI needs to be open")
            return
        container = hiveUICore.currentRigContainer
        if container is None:
            output.displayWarning("Hive Artist UI needs to have a active rig")
            return
        rigModel = container.rigModel
        if rigModel is None:
            output.displayError("Hive Artist UI needs a active rig")
            return
        return rigModel

    def _ensureFileSaved(self):
        """Checks if the file has already been saved. Return True or False so we know if we should
        continue exporting

        If not saved opens "save", or "cancel" window.  Returns the button pressed if "cancel"

        If "save" is clicked it will try to save the current file, if cancelled will return False

        :return buttonClicked: Whether to continue exporting
        :rtype buttonClicked: str
        """
        # TODO move this into elements under maya cmds
        sceneModified = saveexportimport.fileModified()

        if not sceneModified:  # Has been saved already so continue
            return True
        # Open dialog window with Save/Discard/Cancel buttons
        buttonPressed = elements.MessageBox.showSave(title="Save File", parent=self, message=SAVE_SCENE_MSG,
                                                     showDiscard=True)
        if buttonPressed == "save":
            if saveexportimport.saveAsDialogMaMb():  # file saved
                return True
            return False
        elif buttonPressed == "discard":
            return True
        return False

    def exportFBXButtonPressed(self):
        """Export FBX button pressed, calls the export methods based on the UI settings."""
        self.updateUISettings()  # updates all the UI settings to class variables for later use.
        if self.properties.optionsRadio.value == 0:
            self.exportSingleFile()
        elif self.properties.optionsRadio.value == 1:
            self.batchExportFrameRanges()
        else:  # 2
            self.batchExportRigs()

    def exportSingleFile(self):
        """Single file export
        self.updateUISettings() must be called before this method.
        """
        if self.rigInstance is None:
            output.displayWarning("No valid Rig Selected in the UI")
            return

        if not self.outputFilePath:
            output.displayWarning("Invalid export path: {}".format(self.outputFilePath))
            return

        if not self._ensureFileSaved():
            return

        # Init exporter ------------------------
        exporter = hiveapi.Configuration().exportPluginForId("fbxExport")()
        exporter.onProgressCallbackFunc = self.progressCallback
        settings = exporter.exportSettings()  # type: fbxexporter.ExportSettings
        # Export settings ----------------------
        settings.outputPath = self.outputFilePath
        settings.version = self.version  # the actual FBX not the display label
        settings.shapes = self.shapes
        settings.axis = self.axis
        settings.triangulate = self.triangulate
        settings.ascii = self.ascii
        settings.animation = self.animation
        settings.startEndFrame = self.startEndFrameSingle  # for single file/multi rig export
        settings.meshes = self.meshes
        settings.skins = self.skins
        settings.interactive = self.interactive

        exporter.execute(self.rigInstance, settings)

    def batchExportFrameRanges(self):
        """Batch frame ranges with one rig, ranges calculated by a given start/end list.
        self.updateUISettings() must be called before this method
        """
        if self.rigInstance is None:
            output.displayWarning("No valid Rig Selected in the UI")
            return

        if not self.outputFolder:
            output.displayWarning("No export folder path has been given")
            return

        if self.startEndList:
            if self.startEndList[0] == "error":
                return  # error message already displayed

        if not self.startEndList:
            output.displayWarning("No frame ranges found in the UI")
            return

        if not self._ensureFileSaved():
            return

        # Begin batch export ------------------------
        fbxBatch = fbxexporter.fbxBatchExport()
        # Settings ------------------------------------
        fbxBatch.skeletonDefinition = True
        fbxBatch.shapes = self.shapes
        fbxBatch.skins = self.skins
        fbxBatch.animation = self.animation
        fbxBatch.meshes = self.meshes
        fbxBatch.triangulate = self.triangulate
        fbxBatch.axis = self.axis
        fbxBatch.version = self.version
        # Export ------------------------------------
        fbxBatch.exportStartEndList(self.rigName,
                                    self.outputFolder,
                                    self.startEndList,
                                    fileOverrideList=self.clipNames,
                                    prefixRigName=self.prefixName,
                                    message=True)

    def batchExportRigs(self):
        """Batch the rigs by name with a single frame range.
        self.updateUISettings() must be called before this method
        """
        if not self.rigNames:
            output.displayWarning("No rig names found in the UI")
            return
        if not self.outputFolder:
            output.displayWarning("No export folder path has been given")
            return
        if not self._ensureFileSaved():
            return

        # Begin batch export ------------------------
        from zoo.libs.hive.library.exporters import fbxexporter
        fbxBatch = fbxexporter.fbxBatchExport()
        # Settings ------------------------------------
        fbxBatch.startEndFrame = self.startEndFrameSingle
        fbxBatch.skeletonDefinition = True
        fbxBatch.shapes = self.shapes
        fbxBatch.skins = self.skins
        fbxBatch.animation = self.animation
        fbxBatch.meshes = self.meshes
        fbxBatch.triangulate = self.triangulate
        fbxBatch.axis = self.axis
        fbxBatch.version = self.version
        # Export ------------------------------------
        fbxBatch.exportHiveRigNames(self.rigNames,
                                    self.outputFolder,
                                    fileOverrideList=None,
                                    nameSuffix=self.suffixName,
                                    message=True)

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        hiveUICore = uiinterface.instance()
        for widget in self.widgets():
            widget.exportBtn.clicked.connect(self.exportFBXButtonPressed)
            widget.uiLoadBtn.clicked.connect(self.loadUISettingsDisk)
        if hiveUICore is not None:
            hiveUICore = hiveUICore.core()
            hiveUICore.rigRenamed.connect(self._rigStateChanged)
            hiveUICore.rigsChanged.connect(self._rigStateChanged)
            hiveUICore.currentRigChanged.connect(self._currentRigChangedFromArtistUI)
        self.compactWidget.presetsCombo.itemChanged.connect(self.applyPreset)

        self.compactWidget.optionsRadio.toggled.connect(self.optionsRadioChanged)
        self.compactWidget.optionsRadio.toggled.connect(self.updateFromProperties)
        # Time Slider Bookmarks Names --------------------
        self.compactWidget.addBookmarkNamesBtn.addAction("Add From Time Slider Bookmarks",
                                                         mouseMenu=QtCore.Qt.LeftButton,
                                                         icon=iconlib.icon("cacheAdd"),
                                                         connect=self.addFrameRangesBookmarks)
        self.compactWidget.addBookmarkNamesBtn.addAction("Create Time Slider Bookmark",
                                                         mouseMenu=QtCore.Qt.LeftButton,
                                                         icon=iconlib.icon("windowBrowser"),
                                                         connect=self.openTimeSliderBookmark)
        self.compactWidget.addBookmarkNamesBtn.addAction("Add From Maya Game Exporter",
                                                         mouseMenu=QtCore.Qt.LeftButton,
                                                         icon=iconlib.icon("cacheAdd"),
                                                         connect=self.addFrameRangesGameExporter)
        self.compactWidget.addBookmarkNamesBtn.addAction("Open Maya Game Exporter",
                                                         mouseMenu=QtCore.Qt.LeftButton,
                                                         icon=iconlib.icon("windowBrowser"),
                                                         connect=self.openMayaGamesExporter)
        # Time Slider Bookmarks Ranges --------------------
        self.compactWidget.addBookmarkRangesBtn.addAction("Add From Time Slider Bookmarks",
                                                          mouseMenu=QtCore.Qt.LeftButton,
                                                          icon=iconlib.icon("cacheAdd"),
                                                          connect=self.addFrameRangesBookmarks)
        self.compactWidget.addBookmarkRangesBtn.addAction("Create Time Slider Bookmark",
                                                          mouseMenu=QtCore.Qt.LeftButton,
                                                          icon=iconlib.icon("windowBrowser"),
                                                          connect=self.openTimeSliderBookmark)
        self.compactWidget.addBookmarkRangesBtn.addAction("Add From Maya Game Exporter",
                                                          mouseMenu=QtCore.Qt.LeftButton,
                                                          icon=iconlib.icon("cacheAdd"),
                                                          connect=self.addFrameRangesGameExporter)
        self.compactWidget.addBookmarkRangesBtn.addAction("Open Maya Game Exporter",
                                                          mouseMenu=QtCore.Qt.LeftButton,
                                                          icon=iconlib.icon("windowBrowser"),
                                                          connect=self.openMayaGamesExporter)
        # Add Rigs --------------------
        self.compactWidget.addRigsBtn.addAction("Add All Rigs",
                                                mouseMenu=QtCore.Qt.LeftButton,
                                                icon=iconlib.icon("matchRigs"),
                                                connect=self.addRigsAll)
        self.compactWidget.addRigsBtn.addAction("Add Selected Rigs",
                                                mouseMenu=QtCore.Qt.LeftButton,
                                                icon=iconlib.icon("cursorSelect"),
                                                connect=self.addRigsSel)
        # Save --------------------
        self.compactWidget.uiSaveBtn.addAction("Save UI Settings To Scene",
                                               mouseMenu=QtCore.Qt.LeftButton,
                                               icon=iconlib.icon("save"),
                                               connect=self.saveUiSettingsScene)
        self.compactWidget.uiSaveBtn.addAction("Save UI Settings To Disk",
                                               mouseMenu=QtCore.Qt.LeftButton,
                                               icon=iconlib.icon("save"),
                                               connect=self.saveUiSettingsDisk)


class GuiWidgets(QtWidgets.QWidget):
    def __init__(self, parent=None, properties=None, uiMode=None, toolsetWidget=None):
        """Builds the main widgets for all GUIs

        properties is the list(dictionaries) used to set logic and pass between the different UI layouts
        such as compact/adv etc

        :param parent: the parent of this widget
        :type parent: :class:`QtWidgets.QWidget`
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: :class:`zoo.apps.toolsetsui.widgets.toolsetwidget.PropertiesDict`
        :param uiMode: 0 is compact ui mode, 1 is advanced ui mode
        :type uiMode: int
        :type toolsetWidget: :class:`HiveRigExportToolset`
        """
        super(GuiWidgets, self).__init__(parent=parent)
        self.properties = properties
        # Type Radio -----------------------------
        radioList = ["Single FBX Export", "Multiple Timerange", "Multiple Rigs"]
        toolTipList = ["FBX export a single rig with optional timeframe and settings",
                       "Multiple FBX exports with multiple timeframes in the scene. \n"
                       "Usually used for animation cycles.",
                       "Multiple FBX exports with multiple rigs in the scene. \n"
                       "Usually used for cinematics."]
        self.optionsRadio = elements.RadioButtonGroup(radioList=radioList, parent=parent, toolTipList=toolTipList)

        # Select Hive Rig -----------------------------
        self.rigDivider = elements.LabelDivider(text="Select Hive Rig", parent=parent)
        # Rig Combo -----------------------------
        toolTip = "Select the Hive rig from the scene to export. \n" \
                  "No rigs will appear if there are no valid Hive rigs in the scene."
        self.rigListCombo = elements.ComboBoxRegular("",
                                                     items=[],
                                                     parent=parent,
                                                     labelRatio=1,
                                                     boxRatio=3,
                                                     toolTip=toolTip)
        # Select Hive Rigs (multiple) -----------------------------
        self.rigsDivider = elements.LabelDivider(text="Hive Rig Names", parent=parent)
        # Select Hive Rigs -----------------------------
        toolTip = "Specify multiple Hive rigs from the scene to export. \n" \
                  " - eg. zoo_mannequin, robot, natalie \n" \
                  "If multiple of the same rigs use their namespaces to differentiate them. \n" \
                  " - eg m1:zoo_mannequin, m2:zoo_mannequin, m3:zoo_mannequin \n\n" \
                  "Press the arrow button to add rigs from the scene or selection."
        self.rigsEdit = elements.TextEdit(parent=parent,
                                          placeholderText="zoo_mannequin, robot, natalie \n"
                                                          "(Press arrow to add from Scene or Selection)",
                                          fixedHeight=52,
                                          toolTip=toolTip)
        tooltip = "Select any rig controls in the scene. \n" \
                  "Press to add into the UI"
        self.addRigsBtn = elements.styledButton("",
                                                "arrowLeft",
                                                parent,
                                                toolTip=tooltip,
                                                style=uic.BTN_TRANSPARENT_BG,
                                                minWidth=15)

        # ----------------------------- FILE NAMES -----------------------------
        # File Names Divider -----------------------------
        self.fileNamesDivider = elements.LabelDivider(text="File Names", parent=parent)
        # File Names -----------------------------
        toolTip = "Specify optional name suffix. \n" \
                  " - eg. shot05\n" \
                  " - eg. zoo_mannequin_shot05.fbx, robot_shot05.fbx \n"
        self.suffixNameStr = elements.StringEdit(label="Name Suffix",
                                                 parent=parent,
                                                 editPlaceholder="shot05 (optional, eg. zoo_mannequin_shot05.fbx)",
                                                 toolTip=toolTip)
        # Prefix Rig Name Checkbox -----------------------------
        toolTip = "Check to prefix the rig name to the file name. \n" \
                  "On: \n" \
                  " - zoo_mannequin_walk.fbx, zoo_mannequin_run.fbx \n" \
                  "Off: \n" \
                  " - walk.fbx, run.fbx"
        self.prefixRigNameCheckBox = elements.CheckBox("Prefix With Rig Name",
                                                       toolTip=toolTip,
                                                       checked=True,
                                                       parent=parent)
        # Select Hive Rigs -----------------------------
        toolTip = "Override frame range suffix naming. \n" \
                  " - eg. walk, run, jump \n\n" \
                  "Not Used: \n" \
                  " - eg. zoo_mannequin_1_100.fbx, zoo_mannequin_101-200.fbx, natalie \n" \
                  "Overridden: walk, run: \n" \
                  " - eg. zoo_mannequin_walk.fbx, zoo_mannequin_run.fbx, natalie\n\n" \
                  "Press the arrow button to add from Time Slider Bookmarks from Maya's Game Exporter."
        self.nameOverrideEdit = elements.TextEdit(parent=parent,
                                                  placeholderText="Optional Name Overrides: walk, run, jump \n"
                                                                  "If Not Used: 0_100, 101_200, 201_300 \n"
                                                                  "(Arrow adds from Time Bookmarks or Maya's "
                                                                  "Game Exporter)",
                                                  fixedHeight=52,
                                                  toolTip=toolTip)
        tooltip = "Add Time Slider Bookmark frame-ranges and names from the scene \n" \
                  "or from Maya's Game Exporter. "
        self.addBookmarkNamesBtn = elements.styledButton("",
                                                         "arrowLeft",
                                                         parent,
                                                         toolTip=tooltip,
                                                         style=uic.BTN_TRANSPARENT_BG,
                                                         minWidth=15)

        # ----------------------------- FILE PATHS -----------------------------
        # File Path Divider -----------------------------
        self.filePathDivider = elements.LabelDivider(text="File Path (Single File)", parent=parent)
        # Path Widget -----------------------------
        toolTip = "Set the FBX path and file name that will be saved to disk. "
        self.filePathEdit = elements.PathWidget(parent=parent,
                                                path=self.properties.filePathEdit.value,
                                                toolTip=toolTip)
        self.filePathEdit.defaultBrowserPath = toolsetWidget.defaultBrowserPath
        self.filePathEdit.pathText.setPlaceHolderText("Set FBX export file path...")
        self.filePathEdit.setSearchFilter("*.fbx")

        # Folder Path Divider -----------------------------
        self.folderPathDivider = elements.LabelDivider(text="Folder Location (All Files)", parent=parent)
        # Folder Widget  -----------------------------
        toolTip = "Set the folder path where files will be saved to disk. "
        self.folderPathEdit = elements.DirectoryPathWidget(parent=parent, path="")
        self.folderPathEdit.pathText.setPlaceHolderText("Set FBX export folder location...")
        self.folderPathEdit.setToolTip(toolTip)

        # ----------------------------- ANIMATION -----------------------------
        # Time Ranges -----------------------------
        toolTip = "Specify Time Ranges. \n" \
                  " - eg. 1-100, 101-200, 201-300 \n\n" \
                  "Press the arrow button to add from Time Slider Bookmarks from Maya's Game Exporter."
        self.timerangesEdit = elements.TextEdit(parent=parent,
                                                placeholderText="Time Ranges: 1-100, 101-200, 201-300 \n"
                                                                "(Arrow adds from Time Bookmarks or Maya's "
                                                                "Game Exporter)",
                                                fixedHeight=52,
                                                toolTip=toolTip)
        tooltip = "Add Time Slider Bookmark frame-ranges and names from the scene \n" \
                  "or from Maya's Game Exporter. "
        self.addBookmarkRangesBtn = elements.styledButton("",
                                                          "arrowLeft",
                                                          parent,
                                                          toolTip=tooltip,
                                                          style=uic.BTN_TRANSPARENT_BG,
                                                          minWidth=15)
        # Animation Checkbox -----------------------------
        toolTip = "Exports FBX compatible animation within the frame range."
        self.animationCheckBox = elements.CheckBox("Animation", enableMenu=False, toolTip=toolTip,
                                                   checked=self.properties.animationCheckBox.value,
                                                   parent=parent)
        # Start End Vector -----------------------------
        self.startEndFrameAnim = elements.VectorLineEdit(label="Start/End",
                                                         value=self.properties.startEndFrameAnim.value,
                                                         axis=("start", "end"),
                                                         toolTip=toolTip,
                                                         editRatio=2,
                                                         labelRatio=1,
                                                         parent=parent)

        # ----------------------------- OTHER FBX OPTIONS -----------------------------
        # Mesh Checkbox -----------------------------
        toolTip = "Exports the geometry inside the group `rigName_geo_hrc` on export. "
        self.meshCheckBox = elements.CheckBox("Meshes", enableMenu=False, toolTip=toolTip,
                                              checked=self.properties.meshCheckBox.value,
                                              parent=parent)
        # Triangulate Checkbox -----------------------------
        toolTip = "Triangulate all geometry inside the group `rigName_geo_hrc` on export. \n" \
                  "Game engines may require this setting checked on. "
        self.triangulateCheckBox = elements.CheckBox("Triangulate", enableMenu=False, toolTip=toolTip,
                                                     checked=self.properties.triangulateCheckBox.value,
                                                     parent=parent)
        # Blendshape Checkbox -----------------------------
        toolTip = "Exports blendshape information related to geometry inside the group `rigName_geo_hrc` "
        self.blendshapeCheckBox = elements.CheckBox("Blendshapes", enableMenu=False, toolTip=toolTip,
                                                    checked=self.properties.blendshapeCheckBox.value,
                                                    parent=parent)
        # Blendshape Checkbox -----------------------------
        toolTip = "Exports skinning information related to geometry inside the group `rigName_geo_hrc` "
        self.skinningCheckBox = elements.CheckBox("Skinning", enableMenu=False, toolTip=toolTip,
                                                  checked=self.properties.skinningCheckBox.value,
                                                  parent=parent)

        # Presets Combo -----------------------------
        toolTip = "Select a preset to determine the `World Up` and `FBX Version` supported. "
        self.presetsCombo = elements.ComboBoxRegular("",
                                                     items=list(PRESET_DICT.keys()),
                                                     parent=parent,
                                                     labelRatio=1,
                                                     boxRatio=3,
                                                     toolTip=toolTip)
        # World Up Combo -----------------------------
        toolTip = "Export world up of the FBX. \n" \
                  "Some engines/programs support both Y or Z and you can \n" \
                  "use the settings in the receiving program to accept either."
        self.worldAxisCombo = elements.ComboBoxRegular("World Up",
                                                       items=["Y", "Z"],
                                                       setIndex=self.properties.worldAxisCombo.value,
                                                       parent=parent,
                                                       toolTip=toolTip)
        # Format Combo -----------------------------
        toolTip = "Export as a binary file or ascii? \n" \
                  " - Binary:  File is compressed as binary code and is unreadable. \n" \
                  " - Ascii: File is exported as text, and can be edited. "
        self.fbxFormatCombo = elements.ComboBoxRegular("Format",
                                                       items=["binary", "ascii"],
                                                       setIndex=self.properties.fbxFormatCombo.value,
                                                       parent=parent,
                                                       toolTip=toolTip)
        # Version Combo -----------------------------
        toolTip = "The version of FBX to export.  \n" \
                  "Many programs support older versions of FBX. "
        self.fbxVersionCombo = elements.ComboBoxRegular("Version",
                                                        items=toolsetWidget.fbxVersionLabels(),
                                                        setIndex=self.properties.fbxVersionCombo.value,
                                                        parent=parent,
                                                        toolTip=toolTip)
        # Export Button -----------------------------
        toolTip = "FBX Exports the Hive skeleton/s, geometry and or animation to disk. \n\n" \
                  "All geometry must be placed inside the Hive group `rigName_geo_hrc`. \n" \
                  "The single hierarchy skeleton must be inside the group `rigName_deformLayer_hrc`. \n" \
                  "Supports custom joints parented to the Hive skeleton. "
        self.exportBtn = elements.styledButton("Export Hive Rig As FBX",
                                               icon="hiveExportFbx",
                                               toolTip=toolTip,
                                               minWidth=uic.BTN_W_ICN_MED,
                                               parent=parent)

        # Save Button --------------------------------------
        tooltip = "Save the UI settings to either the `scene` or to `disk`. \n" \
                  " - Scene: Saves the UI settings to a node named `zooHiveExportFbxUiSettings`in the scene. \n" \
                  " - Disk: Saves the UI settings to a file *.zooFbxUi on disk. "
        self.uiSaveBtn = elements.styledButton("",
                                               parent=parent,
                                               icon="save",
                                               toolTip=tooltip,
                                               style=uic.BTN_DEFAULT)
        # Load Button --------------------------------------
        tooltip = "Loads previously saved `Export FBX` settings into the UI. \n" \
                  "Loads a *.zooFbxUi file."
        self.uiLoadBtn = elements.styledButton("",
                                               parent=parent,
                                               icon="openFolder01",
                                               toolTip=tooltip,
                                               style=uic.BTN_DEFAULT)

        self.onAnimationCheckChanged(properties.animationCheckBox.value)
        self.onMeshCheckChanged(properties.meshCheckBox.value)
        # View only connections
        self.animationCheckBox.stateChanged.connect(self.onAnimationCheckChanged)
        self.meshCheckBox.stateChanged.connect(self.onMeshCheckChanged)

    def onAnimationCheckChanged(self, state):
        self.startEndFrameAnim.setEnabled(state)

    def onMeshCheckChanged(self, state):
        self.triangulateCheckBox.setEnabled(state)
        self.skinningCheckBox.setEnabled(state)
        self.blendshapeCheckBox.setEnabled(state)

    def updateRigs(self, rigNames):
        oldPropertyValue = self.rigListCombo.currentText()
        self.rigListCombo.clear()
        self.rigListCombo.addItems(rigNames)
        self.rigListCombo.setToText(oldPropertyValue)

    def setCurrentRig(self, rigName):
        self.rigListCombo.setToText(rigName)


class GuiCompact(GuiWidgets):
    def __init__(self, parent=None, properties=None, uiMode=UI_MODE_COMPACT, toolsetWidget=None):
        """Adds the layout building the compact version of the GUI:

            default uiMode - 0 is advanced (UI_MODE_COMPACT)

        :param parent: the parent of this widget
        :type parent: QtWidgets.QWidget
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: :class:`toolsetwidget.PropertiesDict`
        """
        super(GuiCompact, self).__init__(parent=parent, properties=properties, uiMode=uiMode,
                                         toolsetWidget=toolsetWidget)
        # Main Layout ---------------------------------------
        mainLayout = elements.vBoxLayout(self,
                                         margins=(uic.WINSIDEPAD, uic.WINBOTPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SLRG)
        # Divider Constants -----------------------
        geoDivider = elements.LabelDivider(text="Geometry", parent=parent)
        animDivider = elements.LabelDivider(text="Animation", parent=parent)
        fbxDivider = elements.LabelDivider(text="FBX Settings", parent=parent)
        saveDivider = elements.LabelDivider(text="Save", parent=parent)
        # Rig Layout -----------------------
        rigLayout = elements.hBoxLayout(spacing=uic.SLRG, margins=(uic.REGPAD, 0, uic.REGPAD, 0))
        rigLayout.addWidget(self.rigListCombo, 1)
        # Rigs Layout -----------------------
        rigsLayout = elements.hBoxLayout(spacing=uic.SLRG, margins=(uic.REGPAD, 0, uic.REGPAD, 0))
        rigsLayout.addWidget(self.rigsEdit, 20)
        rigsLayout.addWidget(self.addRigsBtn, 1)
        # Rigs Layout -----------------------
        nameOverrideLayout = elements.hBoxLayout(spacing=uic.SLRG, margins=(uic.REGPAD, 0, uic.REGPAD, 0))
        nameOverrideLayout.addWidget(self.nameOverrideEdit, 20)
        nameOverrideLayout.addWidget(self.addBookmarkNamesBtn, 1)
        # Name Options Layout -----------------------
        nameOptionsLayout = elements.vBoxLayout(spacing=uic.SLRG, margins=(uic.REGPAD, 0, uic.REGPAD, 0))
        nameOptionsLayout.addWidget(self.suffixNameStr, 1)
        nameOptionsLayout.addWidget(self.prefixRigNameCheckBox, 1)
        # File Path Layout -----------------------
        filePathLayout = elements.hBoxLayout(spacing=uic.SLRG, margins=(uic.REGPAD, 0, uic.REGPAD, 0))
        filePathLayout.addWidget(self.filePathEdit, 1)
        # Folder Path Layout -----------------------
        folderPathLayout = elements.hBoxLayout(spacing=uic.SLRG, margins=(uic.REGPAD, 0, uic.REGPAD, 0))
        folderPathLayout.addWidget(self.folderPathEdit, 1)
        # Geometry Layout -----------------------
        geometryLayout = elements.hBoxLayout(spacing=uic.SLRG, margins=(uic.REGPAD, 0, uic.REGPAD, 0))
        geometryLayout.addWidget(self.meshCheckBox, 1)
        geometryLayout.addWidget(self.triangulateCheckBox, 1)
        geometryLayout2 = elements.hBoxLayout(spacing=uic.SLRG, margins=(uic.REGPAD, 0, uic.REGPAD, 0))
        geometryLayout2.addWidget(self.skinningCheckBox, 1)
        geometryLayout2.addWidget(self.blendshapeCheckBox, 1)
        # Time Range Layout -----------------------
        timeRangeLayout = elements.hBoxLayout(spacing=uic.SLRG, margins=(uic.REGPAD, 0, uic.REGPAD, 0))
        timeRangeLayout.addWidget(self.timerangesEdit, 20)
        timeRangeLayout.addWidget(self.addBookmarkRangesBtn, 1)
        # Anim Layout -----------------------
        animLayout = elements.hBoxLayout(spacing=uic.SLRG, margins=(uic.REGPAD, 0, uic.REGPAD, 0))
        animLayout.addWidget(self.animationCheckBox, 1)
        animLayout.addWidget(self.startEndFrameAnim, 1)
        # Presets Layout -----------------------
        presetLayout = elements.hBoxLayout(spacing=uic.SLRG, margins=(uic.REGPAD, 0, uic.REGPAD, 0))
        presetLayout.addWidget(self.presetsCombo, 1)
        # Other Settings Layout -----------------------
        fbxLayout = elements.hBoxLayout(spacing=uic.SVLRG, margins=(uic.REGPAD, 0, uic.REGPAD, 0))
        fbxLayout.addWidget(self.worldAxisCombo, 1)
        fbxLayout.addWidget(self.fbxFormatCombo, 1)
        fbxLayout.addWidget(self.fbxVersionCombo, 1)
        # Button Layout -----------------------
        buttonLayout = elements.hBoxLayout(spacing=uic.SPACING, margins=(uic.SMLPAD, 0, uic.SMLPAD, 0))
        buttonLayout.addWidget(self.exportBtn, 10)
        buttonLayout.addWidget(self.uiSaveBtn, 1)
        buttonLayout.addWidget(self.uiLoadBtn, 1)

        # --------------------------------------- Main Layout ---------------------------------------
        mainLayout.addWidget(self.optionsRadio)

        # Single Rig Export
        mainLayout.addWidget(self.rigDivider)
        mainLayout.addLayout(rigLayout)

        # Multi Rig Export
        mainLayout.addWidget(self.rigsDivider)
        mainLayout.addLayout(rigsLayout)

        # Single Path Export
        mainLayout.addWidget(self.filePathDivider)
        mainLayout.addLayout(filePathLayout)

        # Folder Path Export
        mainLayout.addWidget(self.folderPathDivider)
        mainLayout.addLayout(folderPathLayout)

        # Names Title
        mainLayout.addWidget(self.fileNamesDivider)
        mainLayout.addLayout(nameOptionsLayout)
        mainLayout.addLayout(nameOverrideLayout)

        # Animation Time Ranges
        mainLayout.addWidget(animDivider)
        mainLayout.addLayout(timeRangeLayout)
        mainLayout.addLayout(animLayout)

        # Other FBX Options
        mainLayout.addWidget(geoDivider)
        mainLayout.addLayout(geometryLayout)
        mainLayout.addLayout(geometryLayout2)

        mainLayout.addWidget(fbxDivider)
        mainLayout.addLayout(presetLayout)
        mainLayout.addLayout(fbxLayout)

        # Export FBX Button
        mainLayout.addWidget(saveDivider)
        mainLayout.addLayout(buttonLayout)
