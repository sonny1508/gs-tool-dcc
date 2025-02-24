""" ---------- Match & Bake Anim -------------
Multiple constrain and bake tool for Maya.

IMPORTANT
TODO: Automate marking menu without opening window?
TODO: Add ability on UI load to set the default constraint type

EASY LATER
TODO: Shuffle up down functionality

LATER
TODO: Save presets to JSON prefs
TODO: Remember the previous settings or at least the primary constraint type


"""
import os

from zoovendor.Qt import QtWidgets, QtCore

from zoo.libs.utils import output, filesystem
from zoo.libs.maya.cmds.filemanage import saveexportimport
from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.libs.pyqt import utils, uiconstants as uic
from zoo.libs.pyqt.widgets import elements
from zoo.libs import iconlib
from zoo.libs.maya.cmds.workspace import mayaworkspace
from zoo.apps.toolsetsui.widgets.toolsetresizer import ToolsetResizer
from zoo.libs.maya.cmds.animation import batchconstraintbake, batchconstraintconstants, timerange, mocap

# Table imports -----------------
from zoo.libs.pyqt.extended import tableviewplus
from zoo.libs.pyqt.models import tablemodel, delegates
from zoo.libs.pyqt.models import datasources, constants

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1

ALL_MAPPINGS = batchconstraintconstants.ALL_MAPPINGS

CONSTRAINT_TYPES = ["parent", "orient", "scale", "point"]
TIME_RANGE_COMBO_LIST = ["Playback Range", "Full Animation Range", "Custom Frame Range"]

CONSTRAINT_LIST_KEY = "constraintList"
OPTIONS_DICT_KEY = "optionsDict"


class MatchBakeAnim(toolsetwidget.ToolsetWidget):
    id = "matchBakeAnim"
    info = "Multiple constrain and bake tool for Maya."
    uiData = {"label": "Match And Bake Anim",
              "icon": "checkList",
              "tooltip": "Multiple constrain and bake tool for Maya.",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-match-and-bake-anim/"}

    # ------------------
    # STARTUP
    # ------------------

    def preContentSetup(self):
        """First code to run, treat this as the __init__() method"""
        self.toolsetWidget = self  # needed for table resizer widget

    def contents(self):
        """The UI Modes to build, compact, medium and or advanced """
        return [self.initCompactWidget()]  # self.initAdvancedWidget()

    def initCompactWidget(self):
        """Builds the Compact GUI (self.compactWidget) """
        self.compactWidget = GuiCompact(parent=self, properties=self.properties, toolsetWidget=self)
        return self.compactWidget

    def initAdvancedWidget(self):
        """Builds the Advanced GUI (self.advancedWidget) """
        self.advancedWidget = GuiAdvanced(parent=self, properties=self.properties, toolsetWidget=self)
        return self.advancedWidget

    def postContentSetup(self):
        """Last of the initialize code"""
        self.uiFolderPath = ""  # used for saving and loading UI settings
        sourceObjs, targetObjs = batchconstraintbake.selectionPairs()
        if sourceObjs:
            self.compactWidget.tableControl.onAdd()  # adds selected objects to the UI
        else:
            self.importSceneDataToUI()  # imports the scene data to the UI if it exists

        self.leftRightCheckboxChanged()  # disable the l/r UI elements when the Auto Right Side checkbox is checked off
        self.rangeComboChanged()
        self.uiConnections()

    def defaultAction(self):
        """Double Click
        Double clicking the tools toolset icon will run this method
        Be sure "defaultActionDoubleClick": True is set inside self.uiData (meta data of this class)"""
        pass

    def currentWidget(self):
        """ Currently active widget

        :return:
        :rtype: GuiAdvanced or GuiCompact
        """
        return super(MatchBakeAnim, self).currentWidget()

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiAdvanced or GuiCompact]
        """
        return super(MatchBakeAnim, self).widgets()

    # ------------------
    # UI
    # ------------------

    def rangeComboChanged(self):
        """Enables and disables the start End Frame Float widget
        """
        index = self.properties.rangeOptionsCombo.value
        if index == 0:  # playback range auto
            self.compactWidget.startEndFrameFloat.setDisabled(True)
            self.properties.startEndFrameFloat.value = timerange.getRangePlayback()
        elif index == 1:  # full animation range so auto
            self.compactWidget.startEndFrameFloat.setDisabled(True)
            self.properties.startEndFrameFloat.value = timerange.getRangeAnimation()
        elif index == 2:  # custom user range
            self.compactWidget.startEndFrameFloat.setDisabled(False)
            self.properties.startEndFrameFloat.value = timerange.getRangePlayback()
        self.updateFromProperties()  # updates all widgets

    def enterEvent(self, event):
        """Update selection on enter event
        """
        index = self.properties.rangeOptionsCombo.value
        if index == 0:  # playback range auto
            self.properties.startEndFrameFloat.value = timerange.getRangePlayback()
        elif index == 1:  # full animation range so auto
            self.properties.startEndFrameFloat.value = timerange.getRangeAnimation()
        else:
            return
        self.updateFromProperties()

    def leftRightCheckboxChanged(self):
        """Disable the left and right UI elements when the Auto Right Side checkbox is checked off"""
        state = self.properties.autoLeftRightCheck.value
        self.compactWidget.sourceLeft.setEnabled(state)
        self.compactWidget.sourceRight.setEnabled(state)
        self.compactWidget.sourceLRAlwaysSuffix.setEnabled(state)
        self.compactWidget.sourceLRAlwaysPrefix.setEnabled(state)
        self.compactWidget.sourceLRSeparatorOnBorder.setEnabled(state)
        self.compactWidget.targetLeft.setEnabled(state)
        self.compactWidget.targetRight.setEnabled(state)
        self.compactWidget.targetLRAlwaysSuffix.setEnabled(state)
        self.compactWidget.targetLRAlwaysPrefix.setEnabled(state)
        self.compactWidget.targetLRSeparatorOnBorder.setEnabled(state)

    def resetUiDefaults(self):
        """Resets the UI to the default settings"""
        self.properties.sourceNamespace.value = ""
        self.properties.sourceLeft.value = "_L"
        self.properties.sourceRight.value = "_R"
        self.properties.sourceLRAlwaysPrefix.value = False
        self.properties.sourceLRAlwaysSuffix.value = False
        self.properties.sourceLRSeparatorOnBorder.value = False
        self.properties.sourcePrefix.value = ""
        self.properties.sourceSuffix.value = ""
        self.properties.targetNamespace.value = ""
        self.properties.targetLeft.value = "_L"
        self.properties.targetRight.value = "_R"
        self.properties.targetLRAlwaysPrefix.value = False
        self.properties.targetLRAlwaysSuffix.value = False
        self.properties.targetLRSeparatorOnBorder.value = False
        self.properties.targetPrefix.value = ""
        self.properties.targetSuffix.value = ""
        self.properties.autoLeftRightCheck.value = False
        self.properties.maintainOffsetCheck.value = True
        self.properties.includeScaleCheck.value = False
        self.properties.bakeFrequencyFloat.value = 1.0
        self.properties.defaultConstraintCombo.value = 1
        self.properties.sourceCombo.value = 0
        self.properties.targetCombo.value = 0
        # todo time range
        # Clear Table
        self.compactWidget.tableControl.clear()
        # Update enable disable states
        self.leftRightCheckboxChanged()
        # Update all data
        self.updateFromProperties()

    def setConstraintAll(self):
        """Sets the default constraint type for all rows, add 1 for the title row"""
        constrainInt = self.properties.defaultConstraintCombo.value
        self.compactWidget.tableControl.setConstraintAll(CONSTRAINT_TYPES[constrainInt])

    # ------------------
    # JSON IMPORT EXPORT
    # ------------------
    @property
    def defaultBrowserPath(self):
        """Sets the default browser path to the Maya project data directory or the current scene directory"""

        outputDirectory = os.path.expanduser("~")
        # find the current Maya project data directory if it exists
        if mayaworkspace.getCurrentMayaWorkspace():
            dataDir = mayaworkspace.getProjSubDirectory("data")
            if dataDir:
                outputDirectory = dataDir
        else:
            if not saveexportimport.isCurrentSceneUntitled():
                currentScenePath = saveexportimport.currentSceneFilePath()
                outputDirectory = os.path.dirname(currentScenePath)
        return outputDirectory

    def _globalOptionsDict(self):
        optionsDict = dict()
        optionsDict["autoRightSide"] = self.properties.autoLeftRightCheck.value
        optionsDict["maintainOffset"] = self.properties.maintainOffsetCheck.value
        optionsDict["scaleConstrain"] = self.properties.includeScaleCheck.value
        return optionsDict

    def _sourceDict(self):
        sourceConstraintList = self.compactWidget.tableControl.allData()[0]

        optionsDict = self._globalOptionsDict()
        optionsDict["namespace"] = self.properties.sourceNamespace.value
        optionsDict["leftIdentifier"] = self.properties.sourceLeft.value
        optionsDict["rightIdentifier"] = self.properties.sourceRight.value
        optionsDict["leftRightUnderscore"] = self.properties.sourceLRSeparatorOnBorder.value
        optionsDict["leftRightPrefix"] = self.properties.sourceLRAlwaysPrefix.value
        optionsDict["leftRightSuffix"] = self.properties.sourceLRAlwaysSuffix.value
        optionsDict["prefix"] = self.properties.sourcePrefix.value
        optionsDict["suffix"] = self.properties.sourceSuffix.value

        exportDict = {CONSTRAINT_LIST_KEY: sourceConstraintList, OPTIONS_DICT_KEY: optionsDict}
        return exportDict

    def _targetDict(self):
        targetConstraintList = self.compactWidget.tableControl.allData()[1]

        optionsDict = self._globalOptionsDict()
        optionsDict["namespace"] = self.properties.targetNamespace.value
        optionsDict["leftIdentifier"] = self.properties.targetLeft.value
        optionsDict["rightIdentifier"] = self.properties.targetRight.value
        optionsDict["leftRightUnderscore"] = self.properties.targetLRSeparatorOnBorder.value
        optionsDict["leftRightPrefix"] = self.properties.targetLRAlwaysPrefix.value
        optionsDict["leftRightSuffix"] = self.properties.targetLRAlwaysSuffix.value
        optionsDict["prefix"] = self.properties.targetPrefix.value
        optionsDict["suffix"] = self.properties.targetSuffix.value

        exportDict = {CONSTRAINT_LIST_KEY: targetConstraintList, OPTIONS_DICT_KEY: optionsDict}
        return exportDict

    def _setSourceOptionsDictToUI(self, optionsDict):
        self.properties.sourceNamespace.value = optionsDict["namespace"]
        self.properties.sourceLeft.value = optionsDict["leftIdentifier"]
        self.properties.sourceRight.value = optionsDict["rightIdentifier"]
        self.properties.sourceLRSeparatorOnBorder.value = optionsDict["leftRightUnderscore"]
        self.properties.sourceLRAlwaysPrefix.value = optionsDict["leftRightPrefix"]
        self.properties.sourceLRAlwaysSuffix.value = optionsDict["leftRightSuffix"]
        self.properties.sourcePrefix.value = optionsDict["prefix"]
        self.properties.sourceSuffix.value = optionsDict["suffix"]
        self.updateFromProperties()

    def _setTargetOptionsDictToUI(self, optionsDict):
        self.properties.targetNamespace.value = optionsDict["namespace"]
        self.properties.targetLeft.value = optionsDict["leftIdentifier"]
        self.properties.targetRight.value = optionsDict["rightIdentifier"]
        self.properties.targetLRSeparatorOnBorder.value = optionsDict["leftRightUnderscore"]
        self.properties.targetLRAlwaysPrefix.value = optionsDict["leftRightPrefix"]
        self.properties.targetLRAlwaysSuffix.value = optionsDict["leftRightSuffix"]
        self.properties.targetPrefix.value = optionsDict["prefix"]
        self.properties.targetSuffix.value = optionsDict["suffix"]
        self.properties.autoLeftRightCheck.value = optionsDict["autoRightSide"]
        self.properties.maintainOffsetCheck.value = optionsDict["maintainOffset"]
        self.properties.includeScaleCheck.value = optionsDict["scaleConstrain"]
        self.updateFromProperties()

    def exportSource(self):
        """Exports the source column to a file on disk."""
        sourceDict = self._sourceDict()
        if not sourceDict[CONSTRAINT_LIST_KEY]:
            output.displayWarning("No Source Objects Found in the Table.  Please Add Some Objects.")
            return
        self._saveJsonToDisk(sourceDict, source=True)

    def exportTarget(self):
        """Exports the target column to a file on disk."""
        targetDict = self._targetDict()
        if not targetDict[CONSTRAINT_LIST_KEY]:
            output.displayWarning("No Target Objects Found in the Table.  Please Add Some Objects.")
            return
        self._saveJsonToDisk(targetDict, source=False)

    def _saveJsonToDisk(self, aDict, source=True):
        """Save a dictionary to disk as a JSON file

        :param aDict: A python dictionary to save to disk, will be the source or target dictionary
        :type aDict: dict
        """
        txt = "Target Column"
        if source:
            txt = "Source Column"
        if not self.uiFolderPath:
            self.uiFolderPath = self.defaultBrowserPath
        filePath, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save the {} To Disk".format(txt),
                                                            self.defaultBrowserPath, "*.json")
        if not filePath:  # cancel
            return
        self.uiFolderPath = os.path.dirname(filePath)  # update the default browser path
        filesystem.saveJson(aDict, filePath, indent=4, separators=(",", ":"))
        output.displayInfo("{} File Saved To: {}".format(txt, filePath))

    def importSource(self):
        """Imports the source column from a file on disk."""
        sourceDict = self._importJsonFromDisk(self.defaultBrowserPath)
        if not sourceDict:
            return
        # set the source column to the UI
        self.compactWidget.tableControl.updateSourcesFromDictList(sourceDict[CONSTRAINT_LIST_KEY])
        self._setSourceOptionsDictToUI(sourceDict[OPTIONS_DICT_KEY])
        self.leftRightCheckboxChanged()  # disable the l/r UI elements when the Auto Right Side checkbox is checked off

    def importTarget(self):
        """Imports the target column from a file on disk."""
        targetDict = self._importJsonFromDisk(self.defaultBrowserPath)
        if not targetDict:
            return
        # set the target column to the UI
        self.compactWidget.tableControl.updateTargetsFromDictList(targetDict[CONSTRAINT_LIST_KEY])
        self._setTargetOptionsDictToUI(targetDict[OPTIONS_DICT_KEY])
        self.leftRightCheckboxChanged()  # disable the l/r UI elements when the Auto Right Side checkbox is checked off

    def _importJsonFromDisk(self, source=True):
        """Imports a JSON file from disk and returns the dictionary"""
        txt = "Target Column"
        if source:
            txt = "Source Column"

        if not self.uiFolderPath:
            self.uiFolderPath = self.defaultBrowserPath

        filePath, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open {} Data From Disk".format(txt),
                                                            dir=self.uiFolderPath,
                                                            filter="*.json")
        if not filePath:  # cancel
            return {}
        return filesystem.loadJson(filePath)

    def saveUItoScene(self):
        """Saves the UI settings to the scene as a network node with string attributes"""
        sourceDict = self._sourceDict()
        targetDict = self._targetDict()
        mocap.setMatchAndBakeToScene(sourceDict, targetDict)

    def deleteMocapSceneNode(self):
        """Deletes the mocap network node from the scene.  This is the node that remembers the UI settings"""
        mocap.deleteMocapNetworkNode()

    def importSceneDataToUI(self):
        """Imports the scene data to the UI from the mocap network node, if it doesn't exist do nothing."""
        sourceDict, targetDict = mocap.matchAndBakeDataFromScene()
        if not sourceDict or not targetDict:
            return  # nothing found
        self.compactWidget.tableControl.updateSourcesFromDictList(sourceDict[CONSTRAINT_LIST_KEY])
        self.compactWidget.tableControl.updateTargetsFromDictList(targetDict[CONSTRAINT_LIST_KEY])
        self._setSourceOptionsDictToUI(sourceDict[OPTIONS_DICT_KEY])
        self._setTargetOptionsDictToUI(targetDict[OPTIONS_DICT_KEY])

        self.leftRightCheckboxChanged()  # disable the l/r UI elements when the Auto Right Side checkbox is checked off

        self.updateFromProperties()

    # ------------------
    # LOGIC
    # ------------------

    def applySourcesPreset(self):
        """Updates from the source preset combo box"""
        presetNames = self.compactWidget.tableControl.presetSourceNames
        options = self.compactWidget.tableControl.updateSourcesFromPreset(
            presetNames[self.properties.sourceCombo.value])
        if not options:
            return  # is a title divider
        self.properties.sourceLeft.value = options["leftIdentifier"]
        self.properties.sourceRight.value = options["rightIdentifier"]
        self.properties.sourceLRAlwaysPrefix.value = options["leftRightPrefix"]
        self.properties.sourceLRAlwaysSuffix.value = options["leftRightSuffix"]
        self.properties.sourceLRSeparatorOnBorder.value = options["leftRightUnderscore"]
        self.properties.maintainOffsetCheck.value = options["maintainOffset"]
        self.updateFromProperties()

    def applyTargetsPreset(self):
        """Updates from the source preset combo box"""
        presetNames = self.compactWidget.tableControl.presetSourceNames
        options = self.compactWidget.tableControl.updateTargetsFromPreset(
            presetNames[self.properties.targetCombo.value])
        if not options:
            return
        self.properties.autoLeftRightCheck.value = options["autoRightSide"]
        self.properties.targetLeft.value = options["leftIdentifier"]
        self.properties.targetRight.value = options["rightIdentifier"]
        self.properties.targetLRAlwaysPrefix.value = options["leftRightPrefix"]
        self.properties.targetLRAlwaysSuffix.value = options["leftRightSuffix"]
        self.properties.targetLRSeparatorOnBorder.value = options["leftRightUnderscore"]
        self.properties.maintainOffsetCheck.value = options["maintainOffset"]
        self.leftRightCheckboxChanged()
        self.updateFromProperties()

    def _updateBakeInstance(self):
        """Updates the batch bake instance with the latest settings"""
        sourceConstraintList, targetConstraintList = self.compactWidget.tableControl.allData()
        timeRange = self.properties.startEndFrameFloat.value
        self.batchBakeInstance = batchconstraintbake.BatchConstraintAndBake(sourceConstraintList,
                                                                            targetConstraintList,
                                                                            sourceNamespace=self.properties.sourceNamespace.value,
                                                                            targetNamespace=self.properties.targetNamespace.value,
                                                                            sourcePrefix=self.properties.sourcePrefix.value,
                                                                            targetPrefix=self.properties.targetPrefix.value,
                                                                            sourceSuffix=self.properties.sourceSuffix.value,
                                                                            targetSuffix=self.properties.targetSuffix.value,
                                                                            autoLeftToRight=self.properties.autoLeftRightCheck.value,
                                                                            sourceLeftIdentifier=self.properties.sourceLeft.value,
                                                                            sourceRightIdentifier=self.properties.sourceRight.value,
                                                                            sourceLRIsPrefix=self.properties.sourceLRAlwaysPrefix.value,
                                                                            sourceLRIsSuffix=self.properties.sourceLRAlwaysSuffix.value,
                                                                            sourceLRSeparatorOnBorder=self.properties.sourceLRSeparatorOnBorder.value,
                                                                            targetLeftIdentifier=self.properties.targetLeft.value,
                                                                            targetRightIdentifier=self.properties.targetRight.value,
                                                                            targetLRIsPrefix=self.properties.targetLRAlwaysPrefix.value,
                                                                            targetLRIsSuffix=self.properties.targetLRAlwaysSuffix.value,
                                                                            targetLRSeparatorOnBorder=self.properties.sourceLRSeparatorOnBorder.value,
                                                                            maintainOffset=self.properties.maintainOffsetCheck.value,
                                                                            bakeFrequency=self.properties.bakeFrequencyFloat.value,
                                                                            includeScale=self.properties.includeScaleCheck.value,
                                                                            timeRange=timeRange)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def constrainAndBakeAll(self):
        """Constrains, bakes, and removes the constraints for all target objects"""
        self._updateBakeInstance()
        self.batchBakeInstance.constrainSourceDictToTarget()
        self.batchBakeInstance.bakeAnimTargetObjs()
        self.batchBakeInstance.removeConstraintsTargetObjs()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def constrainObjs(self):
        """Constrains the target objects to the source objects"""
        self._updateBakeInstance()
        self.batchBakeInstance.constrainSourceDictToTarget()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def matchObjs(self):
        """Matches the target objects to the source objects"""
        self._updateBakeInstance()
        self.batchBakeInstance.matchSourceDictToTarget()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def bakeObjs(self):
        """Bakes the animation to the target objects"""
        self._updateBakeInstance()
        self.batchBakeInstance.bakeAnimTargetObjs()
        self.batchBakeInstance.removeConstraintsTargetObjs()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def deleteConstraints(self):
        """Deletes all the constraints on the target objects"""
        self._updateBakeInstance()
        self.batchBakeInstance.removeConstraintsTargetObjs()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def selectSourceObjs(self):
        """Deletes all the constraints on the target objects"""
        self._updateBakeInstance()
        self.batchBakeInstance.selectObjs(selSourceObjs=True)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def selectTargetObjs(self):
        """Deletes all the constraints on the target objects"""
        self._updateBakeInstance()
        self.batchBakeInstance.selectObjs(selTargetObjs=True)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def selectAllObjs(self):
        """Deletes all the constraints on the target objects"""
        self._updateBakeInstance()
        self.batchBakeInstance.selectObjs(selSourceObjs=True, selTargetObjs=True)

    def validateObjects(self):
        """Validates the objects in the table, returns a list of errors"""
        self._updateBakeInstance()
        self.batchBakeInstance.printValidateObjects()

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        for widget in self.widgets():
            widget.rangeOptionsCombo.itemChanged.connect(self.rangeComboChanged)
            widget.constrainBtn.clicked.connect(self.constrainObjs)
            widget.matchBtn.clicked.connect(self.matchObjs)
            widget.bakeBtn.clicked.connect(self.bakeObjs)
            widget.bakeAndConstrainBtn.clicked.connect(self.constrainAndBakeAll)
            widget.sourceCombo.itemChanged.connect(self.applySourcesPreset)
            widget.targetCombo.itemChanged.connect(self.applyTargetsPreset)
            # Auto checkbox changed --------------
            widget.autoLeftRightCheck.stateChanged.connect(self.leftRightCheckboxChanged)
            # Connect Table Functions ------------------
            widget.defaultConstraintCombo.itemChanged.connect(self.setConstraintAll)
            widget.addButton.clicked.connect(widget.tableControl.onAdd)
            widget.clearButton.clicked.connect(widget.tableControl.clear)
            widget.removeButton.clicked.connect(widget.tableControl.removeSelected)
            widget.swapButton.clicked.connect(widget.tableControl.swapSelected)
            # Connect Table Functions ------------------
            widget.validateBtn.addAction("Validate Names In Script Editor",
                                         mouseMenu=QtCore.Qt.LeftButton,
                                         icon=iconlib.icon("list"),
                                         connect=self.validateObjects)
            widget.selectBtn.addAction("Select All Source Objects",
                                       mouseMenu=QtCore.Qt.LeftButton,
                                       icon=iconlib.icon("cursorSelect"),
                                       connect=self.selectSourceObjs)
            widget.selectBtn.addAction("Select All Target Objects",
                                       mouseMenu=QtCore.Qt.LeftButton,
                                       icon=iconlib.icon("cursorSelect"),
                                       connect=self.selectTargetObjs)
            widget.selectBtn.addAction("Select All Objects",
                                       mouseMenu=QtCore.Qt.LeftButton,
                                       icon=iconlib.icon("cursorSelect"),
                                       connect=self.selectAllObjs)
            widget.trashBtn.addAction("Delete All Target Constraints",
                                      mouseMenu=QtCore.Qt.LeftButton,
                                      icon=iconlib.icon("trash"),
                                      connect=self.deleteConstraints)
            widget.dotsMenuButton.addAction("UI - Save Data To Scene (Remember)",
                                            mouseMenu=QtCore.Qt.LeftButton,
                                            icon=iconlib.icon("save"),
                                            connect=self.saveUItoScene)
            widget.dotsMenuButton.addAction("UI - Delete Data From Scene (Forget)",
                                            mouseMenu=QtCore.Qt.LeftButton,
                                            icon=iconlib.icon("trash"),
                                            connect=self.deleteMocapSceneNode)
            widget.dotsMenuButton.addAction("UI - Import Data From Scene",
                                            mouseMenu=QtCore.Qt.LeftButton,
                                            icon=iconlib.icon("lightPush"),
                                            connect=self.importSceneDataToUI)
            widget.dotsMenuButton.addAction("UI - Reset To Defaults",
                                            mouseMenu=QtCore.Qt.LeftButton,
                                            icon=iconlib.icon("reloadWindows"),
                                            connect=self.resetUiDefaults)
            widget.dotsMenuButton.addAction("Export - Source Column To Disk (JSON)",
                                            mouseMenu=QtCore.Qt.LeftButton,
                                            icon=iconlib.icon("save"),
                                            connect=self.exportSource)
            widget.dotsMenuButton.addAction("Export - Target Column To Disk (JSON)",
                                            mouseMenu=QtCore.Qt.LeftButton,
                                            icon=iconlib.icon("save"),
                                            connect=self.exportTarget)
            widget.dotsMenuButton.addAction("Import - File As Source Column (JSON)",
                                            mouseMenu=QtCore.Qt.LeftButton,
                                            icon=iconlib.icon("openFolder01"),
                                            connect=self.importSource)
            widget.dotsMenuButton.addAction("Import - File As Target Column (JSON)",
                                            mouseMenu=QtCore.Qt.LeftButton,
                                            icon=iconlib.icon("openFolder01"),
                                            connect=self.importTarget)


class GuiWidgets(QtWidgets.QWidget):
    def __init__(self, parent=None, properties=None, uiMode=None, toolsetWidget=None):
        """Builds the main widgets for all GUIs

        properties is the list(dictionaries) used to set logic and pass between the different UI layouts
        such as compact/adv etc

        :param parent: the parent of this widget
        :type parent: QtWidgets.QWidget
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: zoo.apps.toolsetsui.widgets.toolsetwidget.PropertiesDict
        :param uiMode: 0 is compact ui mode, 1 is advanced ui mode
        :type uiMode: int
        """
        super(GuiWidgets, self).__init__(parent=parent)
        self.parentVar = parent
        self.toolsetWidget = toolsetWidget
        self.properties = properties
        tooltip = "Will automatically try to also find the right side of the given objects. \n" \
                  "See `Source/Target Rename Options` to set the left/right settings. \n" \
                  "Useful for matching full rig setups."
        self.autoLeftRightCheck = elements.CheckBox(label="Auto Right Side",
                                                    checked=False,
                                                    toolTip=tooltip,
                                                    parent=parent)
        tooltip = "On: The constraints will try to maintain their position relative to the source object. \n" \
                  "Off: The constraints will match object positions. "
        self.maintainOffsetCheck = elements.CheckBox(label="Maintain Offset",
                                                     checked=True,
                                                     toolTip=tooltip,
                                                     parent=parent)
        tooltip = "If checked will add a scale constraint for each target object. "
        self.includeScaleCheck = elements.CheckBox(label="Scale Constrain",
                                                   checked=False,
                                                   toolTip=tooltip,
                                                   parent=parent)
        # Time Range -------------------------------------------
        tooltip = "Set the time range to bake. Enable by setting to `Custom Frame Range`"
        self.startEndFrameFloat = elements.VectorLineEdit(label="Start/End",
                                                          value=(1.0, 100.0),
                                                          axis=("start", "end"),
                                                          toolTip=tooltip,
                                                          editRatio=2,
                                                          labelRatio=1)
        # Use Time Slider Range Combo ----------------------------------
        tooltip = "Choose the time range to bake. Channel Box selection only. \n" \
                  " - Playback Range: Frames in the timeline while playing. \n" \
                  " - Full Animation Range: All frames in the min/max time slider setting. \n" \
                  " - Custom Range: User start and end frame."
        self.rangeOptionsCombo = elements.ComboBoxRegular(items=TIME_RANGE_COMBO_LIST,
                                                          setIndex=0,
                                                          toolTip=tooltip)
        tooltip = "Specify the frequency to bake. \n" \
                  " - Example: A value of 2 will bake every second frame. "
        self.bakeFrequencyFloat = elements.FloatEdit(label="Bake By Frame",
                                                     editText=1,
                                                     toolTip=tooltip,
                                                     parent=parent)

        # Source ---------------------------------------
        tooltip = "Specify the namespace to be added to all source names. \n\n" \
                  "  - Example: `characterX` will be added to the name eg `characterX:pCube1`"
        self.sourceNamespace = elements.StringEdit(label="Namespace",
                                                   editPlaceholder="characterX:",
                                                   toolTip=tooltip,
                                                   parent=parent)
        tooltipLR = "Specify the left and right identifiers. `Auto Right Side` must be on.\n\n" \
                    "  - Example: `_L`, `_R` \n" \
                    "  - `pCube1_L_geo` finds `pCube1_R_geo`"
        self.sourceLeft = elements.StringEdit(label="Left Right ID",
                                              editText="_L",
                                              toolTip=tooltipLR,
                                              parent=parent)
        self.sourceRight = elements.StringEdit(label="",
                                               editText="_R",
                                               toolTip=tooltipLR,
                                               parent=parent)
        tooltipForcePrefix = "Forces the left right identifier to always prefix the name. \n" \
                             "`Auto Right Side` must be on. \n\n" \
                             "  - Example: `l`, `r` \n" \
                             "  - `lpSphere1` finds `rpSphere1`"
        self.sourceLRAlwaysPrefix = elements.CheckBox(label="L-R Is Prefix",
                                                      checked=False,
                                                      toolTip=tooltipForcePrefix,
                                                      parent=parent,
                                                      right=True)
        tooltipForceSuffix = "Forces the left right identifier to always suffix the name. \n" \
                             "`Auto Right Side` must be on.\n\n" \
                             "  - Example: `l`, `r` \n" \
                             "  - `pSphere1l` finds `rpSpherer`"
        self.sourceLRAlwaysSuffix = elements.CheckBox(label="L-R Is Suffix",
                                                      checked=False,
                                                      toolTip=tooltipForceSuffix,
                                                      parent=parent,
                                                      right=True)
        tooltipBorder = "While finding the right side an underscore must be on the left or right side of the name. \n" \
                        "`Auto Right Side` must be on.\n\n" \
                        "  - Example: `l`, `r` \n" \
                        "  - `pCube1_l` finds `pCube1_r` \n" \
                        "  or \n" \
                        "  - `l_pCube1` finds `r_pCube1`"
        self.sourceLRSeparatorOnBorder = elements.CheckBox(label="Separator On Border",
                                                           checked=False,
                                                           toolTip=tooltipBorder,
                                                           parent=parent,
                                                           right=True)

        tooltip = "Specify the prefix to be added to all source names. \n\n" \
                  "  - Example: `xxx_` will be added to the name eg `xxx_pCube1`"
        self.sourcePrefix = elements.StringEdit(label="Prefix",
                                                editPlaceholder="xxx_",
                                                toolTip=tooltip,
                                                labelRatio=3,
                                                editRatio=6,
                                                parent=parent)
        tooltip = "Specify the suffix to be added to all source names. \n\n" \
                  "  - Example: `xxx_` will be added to the name eg `pCube1_xxx`"
        self.sourceSuffix = elements.StringEdit(label="Suffix",
                                                editPlaceholder="_xxx",
                                                toolTip=tooltip,
                                                labelRatio=3,
                                                editRatio=6,
                                                parent=parent)

        # Target ---------------------------------------
        tooltip = "Specify the namespace to be added to all target names. \n\n" \
                  "  - Example: `characterX` will be added to the name eg `characterX:pCube1`"
        self.targetNamespace = elements.StringEdit(label="Namespace",
                                                   editPlaceholder="characterX:",
                                                   toolTip=tooltip,
                                                   parent=parent)
        self.targetLeft = elements.StringEdit(label="Left Right ID",
                                              editText="_L",
                                              toolTip=tooltipLR,
                                              parent=parent)
        self.targetRight = elements.StringEdit(label="",
                                               editText="_R",
                                               toolTip=tooltipLR,
                                               parent=parent)
        self.targetLRAlwaysPrefix = elements.CheckBox(label="L-R Is Prefix",
                                                      checked=False,
                                                      toolTip=tooltipForcePrefix,
                                                      parent=parent,
                                                      right=True)
        self.targetLRAlwaysSuffix = elements.CheckBox(label="L-R Is Suffix",
                                                      checked=False,
                                                      toolTip=tooltipForceSuffix,
                                                      parent=parent,
                                                      right=True)
        self.targetLRSeparatorOnBorder = elements.CheckBox(label="Separator On Border",
                                                           checked=False,
                                                           toolTip=tooltipBorder,
                                                           parent=parent,
                                                           right=True)
        tooltip = "Specify the prefix to be added to all target names. \n\n" \
                  "  - Example: `xxx_` will be added to the name eg `xxx_pCube1`"
        self.targetPrefix = elements.StringEdit(label="Prefix",
                                                editPlaceholder="xxx_",
                                                toolTip=tooltip,
                                                labelRatio=3,
                                                editRatio=6,
                                                parent=parent)
        tooltip = "Specify the suffix to be added to all target names. \n\n" \
                  "  - Example: `xxx_` will be added to the name eg `pCube1_xxx`"
        self.targetSuffix = elements.StringEdit(label="Suffix",
                                                editPlaceholder="_xxx",
                                                toolTip=tooltip,
                                                labelRatio=3,
                                                editRatio=6,
                                                parent=parent)
        # Constrain And Bake Btn ---------------------------------------
        tooltip = "Adds the constraints to all target column objects."
        self.constrainBtn = elements.styledButton("Constrain",
                                                  icon="chain",
                                                  toolTip=tooltip,
                                                  style=uic.BTN_DEFAULT,
                                                  parent=parent)
        # Match Btn ---------------------------------------
        tooltip = "Matches all target column objects to the source objects."
        self.matchBtn = elements.styledButton("Match",
                                              icon="matchComponent",
                                              toolTip=tooltip,
                                              style=uic.BTN_DEFAULT,
                                              parent=parent)
        # Constrain And Bake Btn ---------------------------------------
        tooltip = "Animation bakes and removes constraints for all target column objects."
        self.bakeBtn = elements.styledButton("Bake",
                                             icon="bake",
                                             toolTip=tooltip,
                                             style=uic.BTN_DEFAULT,
                                             parent=parent)
        # Constrain And Bake Btn ---------------------------------------
        tooltip = "Will constrain, bake, and remove the constraints.\n" \
                  "1. Adds constraints to the target objects. \n" \
                  "2. Bakes the animation to the target objects \n" \
                  "3. Removes the constraints on the target objects. \n\n" \
                  "This tool can be used for transferring animation and motion capture. \n\n" \
                  "Please see the tools help page by clicking the question mark icon."
        self.bakeAndConstrainBtn = elements.styledButton("Constrain And Bake",
                                                         icon="checkList",
                                                         toolTip=tooltip,
                                                         style=uic.BTN_DEFAULT,
                                                         parent=parent)

        # Swap Table --------------------------------------
        self.tableWidget(parent)  # creates the table widget

        # Resizer widget ----------------------------------
        self.resizerWidget = ToolsetResizer(parent=self,
                                            toolsetWidget=self.toolsetWidget,
                                            target=self.definitionTree,
                                            margins=(0, 3, 0, 10))

        # Combo Presets --------------------------------------
        # Must build after the table
        self.sourceCombo = elements.ComboBoxSearchable(text="",
                                                       items=self.tableControl.presetSourceNames,
                                                       toolTip=tooltip,
                                                       parent=parent)
        self.targetCombo = elements.ComboBoxSearchable(text="",
                                                       items=self.tableControl.presetTargetNames,
                                                       toolTip=tooltip,
                                                       parent=parent)

        # Save Preset Button --------------------------------------
        tooltip = "Saves current tables as presets. Activates menu with options. \n" \
                  " - Save Source Names \n" \
                  " - Save Target Names"
        self.saveBtn = elements.styledButton("",
                                             icon="save",
                                             toolTip=tooltip,
                                             style=uic.BTN_DEFAULT,
                                             parent=parent)
        self.saveBtn.setVisible(False)
        # Validate Button --------------------------------------
        tooltip = "Check object names by printing to the script editor. \n" \
                  "Names will get validated if they exist in the scene."
        self.validateBtn = elements.styledButton("",
                                                 icon="list",
                                                 toolTip=tooltip,
                                                 style=uic.BTN_DEFAULT,
                                                 parent=parent)
        # Select Button --------------------------------------
        tooltip = "Selects the source, target, or all objs. \n" \
                  "Left-click to activate the menu with options."
        self.selectBtn = elements.styledButton("",
                                               icon="cursorSelect",
                                               toolTip=tooltip,
                                               style=uic.BTN_DEFAULT,
                                               parent=parent)
        # Trash Preset Button --------------------------------------
        tooltip = "Deletes the constraints on the source object/s if they exist."
        self.trashBtn = elements.styledButton("",
                                              icon="trash",
                                              toolTip=tooltip,
                                              style=uic.BTN_DEFAULT,
                                              parent=parent)
        # ---------------- COLLAPSABLES ------------------
        self.bakeCollapsable = elements.CollapsableFrameThin("Time Bake Options",
                                                             contentMargins=(uic.SREG, uic.SREG, uic.SREG, uic.SREG),
                                                             contentSpacing=uic.SLRG,
                                                             collapsed=True,
                                                             parent=parent)
        self.sourceCollapsable = elements.CollapsableFrameThin("Source Rename Options",
                                                               contentMargins=(uic.SREG, uic.SREG, uic.SREG, uic.SREG),
                                                               contentSpacing=uic.SLRG,
                                                               collapsed=True,
                                                               parent=parent)
        self.targetCollapsable = elements.CollapsableFrameThin("Target Rename Options",
                                                               contentMargins=(uic.SREG, uic.SREG, uic.SREG, uic.SREG),
                                                               contentSpacing=uic.SLRG,
                                                               collapsed=True,
                                                               parent=parent)

    def tableWidget(self, parent):
        # Build the table tree --------------------------------------------
        self.definitionTree = tableviewplus.TableViewPlus(manualReload=False, searchable=False, parent=parent)

        self.userModel = tablemodel.TableModel(parent=parent)
        self.tableControl = Controller(self.userModel, self.definitionTree, parent=parent)
        self.definitionTree.setModel(self.userModel)
        self.definitionTree.tableView.verticalHeader().hide()
        self.definitionTree.tableView.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.definitionTree.tableView.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        self.definitionTree.registerRowDataSource(SourceColumn(self.tableControl, headerText="Source"))
        self.definitionTree.registerColumnDataSources([TargetColumn(headerText="Target"),
                                                       ConstraintTypeColumn(headerText="Constraint")])

        self.tableControl.clear()  # refresh updates the table
        self.definitionTree.tableView.horizontalHeader().resizeSection(0, utils.dpiScale(130))
        self.definitionTree.tableView.horizontalHeader().resizeSection(1, utils.dpiScale(130))
        self.definitionTree.tableView.horizontalHeader().resizeSection(2, utils.dpiScale(20))
        tooltip = "Set constraint types for all new rows added to the table."
        self.defaultConstraintCombo = elements.ComboBoxRegular(label="All Rows",
                                                               items=CONSTRAINT_TYPES,
                                                               setIndex=1,
                                                               toolTip=tooltip,
                                                               boxMinWidth=100,
                                                               parent=parent)
        # Dots menu button, export, import. --------------------------------------
        tooltip = ("Misc Settings: \n"
                   " - Save and import settings to the scene: Saves data to a node named `zooMocapData_networkNode`.\n"
                   " - Delete the settings from the scene. Deletes the `zooMocapData_networkNode`.\n"
                   " - Reset the UI to Defaults \n"
                   " - Import and Export column data to disk (JSON).")
        self.dotsMenuButton = elements.styledButton("",
                                                    icon="menudots",
                                                    toolTip=tooltip,
                                                    style=uic.BTN_TRANSPARENT_BG,
                                                    parent=parent)
        # Clear/Add/Remove/Swap Row Buttons --------------------------------------
        tooltip = "Clears all the rows in the table."
        self.clearButton = elements.styledButton("",
                                                 icon="checkListDel",
                                                 toolTip=tooltip,
                                                 style=uic.BTN_TRANSPARENT_BG,
                                                 parent=parent)
        tooltip = "Adds new row. \n" \
                  "Select objects sources and then targets to add to the table.\n" \
                  "Can select multiple sources and then multiple targets."
        self.addButton = elements.styledButton("",
                                               icon="plus",
                                               toolTip=tooltip,
                                               style=uic.BTN_TRANSPARENT_BG,
                                               parent=parent)
        tooltip = "Removes the selected row/s. from the table"
        self.removeButton = elements.styledButton("",
                                                  icon="minusSolid",
                                                  toolTip=tooltip,
                                                  style=uic.BTN_TRANSPARENT_BG,
                                                  parent=parent)
        tooltip = "Swaps the selected row/s so the source becomes the target and vice versa."
        self.swapButton = elements.styledButton("",
                                                icon="reverseCurves",
                                                toolTip=tooltip,
                                                style=uic.BTN_TRANSPARENT_BG,
                                                parent=parent)
        tooltip = "Shuffle the selected rows up."
        self.shuffleUpButton = elements.styledButton("",
                                                     icon="arrowSingleUp",
                                                     toolTip=tooltip,
                                                     style=uic.BTN_TRANSPARENT_BG,
                                                     parent=parent)
        self.shuffleUpButton.setVisible(False)
        tooltip = "Shuffle the selected rows down."
        self.shuffleDownButton = elements.styledButton("",
                                                       icon="arrowSingleDown",
                                                       toolTip=tooltip,
                                                       style=uic.BTN_TRANSPARENT_BG,
                                                       parent=parent)
        self.shuffleDownButton.setVisible(False)


class GuiCompact(GuiWidgets):
    def __init__(self, parent=None, properties=None, uiMode=UI_MODE_COMPACT, toolsetWidget=None):
        """Adds the layout building the compact version of the GUI:

            default uiMode - 0 is advanced (UI_MODE_COMPACT)

        :param parent: the parent of this widget
        :type parent: QtWidgets.QWidget
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: zoo.apps.toolsetsui.widgets.toolsetwidget.PropertiesDict
        """
        super(GuiCompact, self).__init__(parent=parent, properties=properties, uiMode=uiMode,
                                         toolsetWidget=toolsetWidget)
        # Main Layout ---------------------------------------
        mainLayout = elements.vBoxLayout(self, margins=(uic.WINSIDEPAD, uic.WINBOTPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SREG)
        # Checkbox Layout ---------------------------------------
        checkboxLayout = elements.hBoxLayout(self, margins=(uic.SREG, uic.SREG, uic.SREG, uic.SREG), spacing=uic.SREG)
        checkboxLayout.addWidget(self.maintainOffsetCheck, 1)
        checkboxLayout.addWidget(self.includeScaleCheck, 1)
        checkboxLayout.addWidget(self.autoLeftRightCheck, 1)

        # Time Range Layout -----------------------------
        timeRangeLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SREG)
        timeRangeLayout.addWidget(self.rangeOptionsCombo, 1)
        timeRangeLayout.addWidget(self.startEndFrameFloat, 1)

        # Source ---------------------------------------
        sourceNamespaceLayout = elements.hBoxLayout(self, margins=(0, 0, 0, 0), spacing=uic.SREG)
        sourceNamespaceLayout.addWidget(self.sourceNamespace, 15)
        sourceNamespaceLayout.addWidget(self.sourceLeft, 10)
        sourceNamespaceLayout.addWidget(self.sourceRight, 5)

        sourceCheckboxLayout = elements.hBoxLayout(self, margins=(0, 0, 0, 0), spacing=uic.SREG)
        sourceCheckboxLayout.addWidget(self.sourceLRAlwaysPrefix, 1)
        sourceCheckboxLayout.addWidget(self.sourceLRAlwaysSuffix, 1)
        sourceCheckboxLayout.addWidget(self.sourceLRSeparatorOnBorder, 1)

        sourcePrefixSufixLayout = elements.hBoxLayout(self, margins=(0, 0, 0, 0), spacing=uic.SREG)
        sourcePrefixSufixLayout.addWidget(self.sourcePrefix, 1)
        sourcePrefixSufixLayout.addWidget(self.sourceSuffix, 1)

        # Target ---------------------------------------
        targetNamespaceLayout = elements.hBoxLayout(self, margins=(0, 0, 0, 0), spacing=uic.SREG)
        targetNamespaceLayout.addWidget(self.targetNamespace, 15)
        targetNamespaceLayout.addWidget(self.targetLeft, 10)
        targetNamespaceLayout.addWidget(self.targetRight, 5)

        targetCheckboxLayout = elements.hBoxLayout(self, margins=(0, 0, 0, 0), spacing=uic.SREG)
        targetCheckboxLayout.addWidget(self.targetLRAlwaysPrefix, 1)
        targetCheckboxLayout.addWidget(self.targetLRAlwaysSuffix, 1)
        targetCheckboxLayout.addWidget(self.targetLRSeparatorOnBorder, 1)

        targetPrefixSufixLayout = elements.hBoxLayout(self, margins=(0, 0, 0, 0), spacing=uic.SREG)
        targetPrefixSufixLayout.addWidget(self.targetPrefix, 1)
        targetPrefixSufixLayout.addWidget(self.targetSuffix, 1)

        # Combos ---------------------------------------
        combosLayout = elements.hBoxLayout(self, margins=(0, 0, 0, 0), spacing=uic.SREG)
        combosLayout.addWidget(self.sourceCombo, 1)
        combosLayout.addWidget(self.targetCombo, 1)

        # Table and add/remove/swap buttons ---------------------------------------
        tableLayout = elements.vBoxLayout()
        tableLayout.addWidget(self.definitionTree)

        # Table button layout ---------------------------------------
        tableButtonLayout = elements.hBoxLayout(self, margins=(0, 0, 0, 0), spacing=uic.SSML)
        buttonSpacer = QtWidgets.QSpacerItem(1000, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        tableButtonLayout.addWidget(self.dotsMenuButton, 1)
        tableButtonLayout.addWidget(self.addButton, 1)
        tableButtonLayout.addWidget(self.removeButton, 1)
        tableButtonLayout.addWidget(self.clearButton, 1)
        tableButtonLayout.addWidget(self.swapButton, 1)
        tableButtonLayout.addWidget(self.shuffleUpButton, 1)
        tableButtonLayout.addWidget(self.shuffleDownButton, 1)
        tableButtonLayout.addItem(buttonSpacer)
        tableButtonLayout.addWidget(self.defaultConstraintCombo, 1)

        # Buttons ---------------------------------------
        topButtonLayout = elements.hBoxLayout(self, margins=(0, 0, 0, 0), spacing=uic.SPACING)
        topButtonLayout.addWidget(self.constrainBtn, 20)
        topButtonLayout.addWidget(self.matchBtn, 20)
        topButtonLayout.addWidget(self.bakeBtn, 20)
        topButtonLayout.addWidget(self.saveBtn, 1)
        topButtonLayout.addWidget(self.validateBtn, 1)
        topButtonLayout.addWidget(self.selectBtn, 1)
        topButtonLayout.addWidget(self.trashBtn, 1)

        # Buttons ---------------------------------------
        buttonLayout = elements.hBoxLayout(self, margins=(0, 0, 0, 0), spacing=uic.SPACING)
        buttonLayout.addWidget(self.bakeAndConstrainBtn, 20)

        # Button vertical layout ---------------------------------------
        vertButtonLayout = elements.vBoxLayout(self, margins=(0, 0, 0, 0), spacing=uic.SPACING)
        vertButtonLayout.addLayout(topButtonLayout)
        vertButtonLayout.addLayout(buttonLayout)

        #  Flip Collapsable ---------------------------------------
        self.bakeCollapsable.hiderLayout.addLayout(timeRangeLayout)
        self.bakeCollapsable.hiderLayout.addWidget(self.bakeFrequencyFloat)
        #  Pre post Collapsable ---------------------------------------
        self.sourceCollapsable.hiderLayout.addLayout(sourceNamespaceLayout)
        self.sourceCollapsable.hiderLayout.addLayout(sourceCheckboxLayout)
        self.sourceCollapsable.hiderLayout.addLayout(sourcePrefixSufixLayout)
        #  Options Collapsable ---------------------------------------
        self.targetCollapsable.hiderLayout.addLayout(targetNamespaceLayout)
        self.targetCollapsable.hiderLayout.addLayout(targetCheckboxLayout)
        self.targetCollapsable.hiderLayout.addLayout(targetPrefixSufixLayout)
        # Collapsable Connections -------------------------------------
        self.bakeCollapsable.toggled.connect(toolsetWidget.treeWidget.updateTree)
        self.sourceCollapsable.toggled.connect(toolsetWidget.treeWidget.updateTree)
        self.targetCollapsable.toggled.connect(toolsetWidget.treeWidget.updateTree)

        # Add To Main Layout ---------------------------------------
        mainLayout.addLayout(checkboxLayout)
        mainLayout.addWidget(self.bakeCollapsable)
        mainLayout.addWidget(self.sourceCollapsable)
        mainLayout.addWidget(self.targetCollapsable)
        mainLayout.addLayout(combosLayout)
        mainLayout.addLayout(tableLayout)
        mainLayout.addLayout(tableButtonLayout)
        mainLayout.addWidget(self.resizerWidget)
        mainLayout.addLayout(vertButtonLayout)


class GuiAdvanced(GuiWidgets):
    def __init__(self, parent=None, properties=None, uiMode=UI_MODE_ADVANCED, toolsetWidget=None):
        """Adds the layout building the advanced version of the GUI:

            default uiMode - 1 is advanced (UI_MODE_ADVANCED)

        :param parent: the parent of this widget
        :type parent: QtWidgets.QWidget
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: zoo.apps.toolsetsui.widgets.toolsetwidget.PropertiesDict
        """
        super(GuiAdvanced, self).__init__(parent=parent, properties=properties, uiMode=uiMode,
                                          toolsetWidget=toolsetWidget)
        # Main Layout ---------------------------------------
        mainLayout = elements.vBoxLayout(self, margins=(uic.WINSIDEPAD, uic.WINBOTPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SREG)


# Table data --------------------------------------------------------------------------
# note always use constants.userRoleCount +  your custom role number
TYPE_ROLE = constants.userRoleCount + 1


class ItemData(object):
    def __init__(self, source, target, constraintType):
        self.source = source
        self.target = target
        self.constraintType = constraintType

    def __repr__(self):
        return "ItemData(source={}, target={}, constraintType={})".format(self.source, self.target, self.constraintType)


class Controller(QtCore.QObject):
    """Main class that controls the table

    - Adding Rows
    - Removing Rows
    - Swapping Source/Target
    - Clearing the table

    """

    def __init__(self, userModel, definitionTree, parent, defaultConstraint="orient"):
        """
        :param parent: The parent widget
        :type parent: object
        """
        super(Controller, self).__init__(parent)
        self.definitionTree = definitionTree
        # Could use a custom subclass
        self.userModel = userModel
        self.defaultConstraint = defaultConstraint
        # Initialize Presets --------------------------------------
        self.presetMappingList = ALL_MAPPINGS
        self.presetSourceNames = list()
        self.presetTargetNames = list()
        for preset in self.presetMappingList:
            self.presetSourceNames.append(list(preset.keys())[0])
        self.presetTargetNames = list(self.presetSourceNames)
        self.presetSourceNames.insert(0, "--- Sel Source Preset ---")
        self.presetTargetNames.insert(0, "--- Sel Target Preset ---")

    # ------------------
    # MISC
    # ------------------

    def clear(self):
        """Clears the table."""
        # Clears out our data on the root item aka the tree
        self.userModel.rowDataSource.setUserObjects([])
        # internal code to the model to clear QT stuff
        self.userModel.reload()
        # auto discover + insert from template here aka insertRow

    def onAdd(self):
        """Adds a row to the table."""
        self.addItemFromSelection()

    def swapSelected(self):
        """Swaps source and target values in the selected rows of the table.
        """
        visited = set()
        for modelIndex in self.definitionTree.selectedQIndices():
            if modelIndex.row() in visited:
                continue
            visited.add(modelIndex.row())
            # grab our internal item data aka a dict
            item = self.userModel.rowDataSource.userObject(modelIndex.row())
            source = item.source
            target = item.target
            # swap data via the model so that the view gets notified of change.
            self.userModel.setData(self.userModel.index(modelIndex.row(), 0),
                                   target)
            self.userModel.setData(self.userModel.index(modelIndex.row(), 1),
                                   source)

    def columnButtonClicked(self, modelIndex):
        """Called by the source/target column button clicked in the dataSource classes

        Adds objects to the row/column.

        :param modelIndex:
        :type modelIndex: :class:`QtCore.QModelIndex`
        :return:
        :rtype:
        """
        sel = batchconstraintbake.selection()
        if not sel:
            return False
        return self.userModel.setData(modelIndex, sel[0], QtCore.Qt.EditRole)

    # ------------------
    # GET DATA
    # ------------------

    def allData(self):
        """Returns all data, source and target dicts

        - Source List of Dictionaries
        - Target List of Dictionaries

        .. code-block:: python

        sourceConstraintList = [{'0': {'node': 'locator1', 'constraint': 'parent'}},
                                {'1': {'node': 'locator2', 'constraint': 'orient'}}]

        targetConstraintList = [{'0': {'node': 'pCube1', 'constraint': 'parent'}},
                                {'1': {'node': 'pCube2', 'constraint': 'orient'}}]

        :return: The Source Constraint List and Target Constraint List
        :rtype: tuple(list(dict), list(dict))
        """
        sourceConstraintList = list()
        targetConstraintList = list()
        rowCount = self.userModel.rowCount()
        # loop through all rows
        for i, row in enumerate(range(rowCount)):
            item = self.userModel.rowDataSource.userObject(i)
            sourceDict = {"node": item.source, "constraint": item.constraintType}
            targetDict = {"node": item.target, "constraint": item.constraintType}
            sourceConstraintList.append({i: sourceDict})
            targetConstraintList.append({i: targetDict})
            # get the item data for each row
        return sourceConstraintList, targetConstraintList

    def _allItems(self):
        """Returns all the data as a list of class ItemData() instances.

            Class ItemData() instances stores the data for each row.
            "ItemData(source={}, target={}, constraintType={})"

        :return: List of class ItemData() instances
        :rtype: list(:class:`ItemData`)
        """
        items = list()
        rowCount = self.userModel.rowCount()
        # loop through all rows
        for i, row in enumerate(range(rowCount)):
            item = self.userModel.rowDataSource.userObject(i)
            items.append(item)
        return items

    def setConstraintAll(self, constraintType):
        """Sets the constraint type for all rows in the table.

        :param constraintType: The constraint type to set all rows to
        :type constraintType: str
        """
        items = self._allItems()
        for item in items:
            item.constraintType = constraintType
        self._updateTreeFromModelItems(items, clearExisting=True)

    # ------------------
    # ADD ROWS
    # ------------------

    def addItemFromSelection(self):
        """Adds rows to the table.

        Gets selection pairs, ie first four objects in the selection as source objs and last four as targets.

        Creates the new item as a dictionary and adds it to the model.

        After added to item data:
            ItemData(sourceObj, targetObjs[i], "orient")
        Becomes:
            "ItemData(source={}, target={}, constraintType={})"

        """
        sourceObjs, targetObjs = batchconstraintbake.selectionPairs()
        if not sourceObjs:
            sourceObjs = [""]
            targetObjs = [""]
        elif len(sourceObjs) != len(targetObjs):  # lists are odd numbers so last entry will be empty
            targetObjs.append("")
        # Batch adds all items to the model from selection
        items = []
        for i, sourceObj in enumerate(sourceObjs):
            newItem = ItemData(sourceObj, targetObjs[i], "orient")
            items.append(newItem)

        # get the last selected row if not return to the end of the list -----
        indices = self.definitionTree.selectedRowsIndices()
        insertIndex = self.userModel.rowCount()
        if indices:
            insertIndex = indices[-1].row() + 1
        self._updateTreeFromModelItems(items, clearExisting=False, insertIndex=insertIndex)

    def _autoAddRows(self, rowList):
        """Auto add rows to the table if not enough rows for the length of the rowList

        :param rowList: List of class ItemData() instances
        :type rowList: list(:class:`ItemData`)
        """
        newCount = len(rowList)
        items = self._allItems()
        rowCount = len(items)
        if newCount > rowCount:
            newRows = newCount - rowCount
            for i in range(newRows):  # loop for the number of new rows
                blankItem = ItemData("", "", self.defaultConstraint)
                items.append(blankItem)  # add a new item
        return items

    # ------------------
    # UPDATE TABLE
    # ------------------

    def _updateTreeFromModelItems(self, items, clearExisting=True, insertIndex=None):
        """From the ItemData list, update the table tree with the current items:

            Class ItemData() instances stores the data for each row.
            "ItemData(source={}, target={}, constraintType={})"

        :param items: Class storing the row data "ItemData(source={}, target={}, constraintType={})"
        :type items: list(:class:`ItemData`)
        :param clearExisting: If True clears the table before adding the new items
        :type clearExisting: bool
        :param insertIndex: The index to insert the new rows at, if None will append to the end of the table
        :type insertIndex: int
        """
        if clearExisting:
            self.clear()  # clears the table
        # must call the model to insert because this automatically informs the ui it's got something new to render
        # without this your new items won't display until the UI is refresh at some point i.e mouseEnter
        if insertIndex is None:  # None so insert at the end of the table
            insertIndex = self.userModel.rowCount()
        self.userModel.insertRows(insertIndex,
                                  count=len(items),
                                  items=items
                                  )
        tableModel = self.definitionTree.model()  # this is the proxy model
        # we force columns 0 and 1 for all rows to be persistent in other words always render
        # our custom widget in each cell
        for row in range(tableModel.rowCount()):
            firstColumnIndex = tableModel.index(row, 0)
            secondColumnIndex = tableModel.index(row, 1)
            if tableModel.flags(firstColumnIndex) & QtCore.Qt.ItemIsEditable:
                self.definitionTree.openPersistentEditor(firstColumnIndex)
            if tableModel.flags(secondColumnIndex) & QtCore.Qt.ItemIsEditable:
                self.definitionTree.openPersistentEditor(secondColumnIndex)

    # ------------------
    # REMOVE ROWS
    # ------------------

    def removeSelected(self):
        selected = self.definitionTree.selectedRowsIndices()
        if not selected:
            return
        for rowIndex in reversed(selected):
            self.userModel.removeRow(rowIndex.row())

    # ------------------
    # UPDATE FROM PRESETS
    # ------------------

    def _presetDictByName(self, presetKeyName):
        """Returns a preset dict from its preset name.

        Loops over all the preset dicts (self.presetMappingList) and returns the first match.

        :param name: The name of the key of the preset dict eg "Hive Biped Cntrls"
        :type name: str
        :return: The preset dictionary with nodes and options.
        :rtype: dict(dict(str))
        """
        for presetDict in self.presetMappingList:
            if presetKeyName in presetDict.keys():
                return presetDict
        else:
            return None

    def _nodesConstraintsList(self, presetDict):
        """From a preset dictionary returns the nodes and constraints as lists.

        :param presetDict: A single preset dictionary eg "Hive Biped Cntrls"
        :type presetDict: dict(dict(str))
        :return: a list of object names and constraint types as strings
        :rtype: tuple(list(str), list(str))
        """
        nodeList = list()
        constraintTypeList = list()
        valuesDict = list(presetDict.values())[0]
        if not valuesDict:  # Can be empty when a preset is a divider or title.
            return list(), list(), dict()
        optionsDict = valuesDict["options"]
        nodesConstraintsList = valuesDict["nodes"]  # is a list of dictionaries
        for dictDict in nodesConstraintsList:
            nodeConstraintDict = list(dictDict.values())[0]  # get contents of first key
            nodeList.append(nodeConstraintDict["node"])
            constraintTypeList.append(nodeConstraintDict["constraint"])
        return nodeList, constraintTypeList, optionsDict

    def updateSourcesFromPreset(self, presetKeyName, message=False):
        """Updates the sources column from a preset name.
        Adds rows if needed, other column will be blank or defaults.

        :param presetKeyName: The name of the dictionary with nodes and options eg "Hive Biped Cntrls"
        :type presetKeyName: str
        :return: The Options Dict for the target preset intended for the UI to use, left right modifiers etc.
        :rtype: tuple(list(str), list(str))
        """
        presetDict = self._presetDictByName(presetKeyName)
        if not presetDict:
            if message:  # default is off as likely a divider or title
                output.displayWarning("Preset not found: {}".format(presetKeyName))
            return
        sourceNodeList, constraintTypeList, optionsDict = self._nodesConstraintsList(presetDict)
        if not sourceNodeList:  # Likely a divider or title so do nothing.
            return
        self._updateSourcesColumn(sourceNodeList)
        return optionsDict

    def updateTargetsFromPreset(self, presetKeyName, message=False):
        """Updates the targets and constraints column from a preset name.
        Adds rows if needed, other column will be blank or defaults.

        :param presetKeyName: The name of the dictionary with nodes and options eg "Hive Biped Cntrls"
        :type presetKeyName: str
        :return: The Options Dict for the target preset intended for the UI to use, left right modifiers etc.
        :rtype: tuple(list(str), list(str))
        """
        presetDict = self._presetDictByName(presetKeyName)
        if not presetDict:
            if message:  # default is off as likely a divider or title
                output.displayWarning("Preset not found: {}".format(presetKeyName))
            return
        nodeList, constraintTypeList, optionsDict = self._nodesConstraintsList(presetDict)
        if not nodeList:  # Likely a divider or title so do nothing.
            return
        self._updateTargetsColumn(nodeList, constraintTypeList)
        return optionsDict

    def updateSourcesFromDictList(self, presetList):
        """From a constrain dict, updated the sources column.

        [{'root': {'node': 'spine_M_cog_anim', 'constraint': 'parent'}},
         {'shoulder_L': {'node': 'arm_L_shldr_fk_anim', 'constraint': 'orient'}}]

        :param presetList:
        :type presetList:
        :return:
        :rtype:
        """
        if not presetList:
            return
        nodeList = list()
        for constraintDict in presetList:
            nodeList.append(constraintDict[list(constraintDict.keys())[0]]["node"])
        self._updateSourcesColumn(nodeList)

    def updateTargetsFromDictList(self, presetList):
        if not presetList:
            return
        nodeList = list()
        constraintList = list()
        for constraintDict in presetList:
            nodeList.append(constraintDict[list(constraintDict.keys())[0]]["node"])
            constraintList.append(constraintDict[list(constraintDict.keys())[0]]["constraint"])
        self._updateTargetsColumn(nodeList, constraintList)

    def _updateSourcesColumn(self, nodes):
        """Updates the sources column from a list.
        Adds rows if needed, other column will be blank or defaults.

        :param nodes: List of names of source maya objects
        :type nodes: list(str)
        """
        items = self._autoAddRows(nodes)  # be sure there are enough items in the list
        # Update the sources column -------------
        for i, item in enumerate(items):
            item.source = nodes[i]
        self._updateTreeFromModelItems(items, clearExisting=True)

    def _updateTargetsColumn(self, nodes, constraintList):
        """Updates the targets and constrain column from two lists.
        Adds rows if needed, other column will be blank or defaults.

        :param nodes: List of names of source maya objects
        :type nodes: list(str)
        :param constraintList: Matching list of constraint types "orient" or "parent" etc.
        :type constraintList: list(str)
        """
        items = self._autoAddRows(nodes)  # be sure there are enough items in the list
        # Update the sources column -------------
        for i, item in enumerate(items):
            item.target = nodes[i]
            item.constraintType = constraintList[i]
        self._updateTreeFromModelItems(items, clearExisting=True)


class SourceColumn(datasources.BaseDataSource):
    """Data in the first "Source" column
    """

    def __init__(self, controller, headerText=None, model=None, parent=None):
        super(SourceColumn, self).__init__(headerText, model, parent)
        self.controller = controller

    def delegate(self, parent):
        return delegates.LineEditButtonDelegate(parent)

    def columnCount(self):
        # specify how many columns that the item has, note: this is not the same as the number of columns in the view
        # which is can be changed on the view code.
        return 3

    def insertChildren(self, index, children):
        self._children[index:index] = children
        return True

    def insertRowDataSources(self, index, count, items):
        return self.insertChildren(index, items)

    def customRoles(self, index):
        """When you have custom roles i.e in this case TYPE_ROLE is here for search. it allows you
        to retrieve item data via dataByRole method.
        """
        return [TYPE_ROLE, constants.buttonClickedRole]

    def dataByRole(self, index, role):
        if TYPE_ROLE == role:
            return self._baseType
        elif role == constants.buttonClickedRole:
            return self.controller.columnButtonClicked(self.model.index(index, 0))

    def data(self, index):
        userData = self.userObject(index)
        if userData:
            return userData.source
        return ""

    def setData(self, index, value):
        userData = self.userObject(index)
        # you should replace this code with what you need to set the source for the index(row) on the userData object
        if userData:
            userData.source = value
            return True
        return False


class TargetColumn(datasources.ColumnDataSource):
    """Data in the second "Source" column
    """

    def __init__(self, headerText=None, model=None, parent=None):
        super(TargetColumn, self).__init__(headerText, model, parent)

    def delegate(self, parent):
        return delegates.LineEditButtonDelegate(parent)

    def data(self, rowDataSource, index):
        userData = rowDataSource.userObject(index)
        if userData and userData.target:
            return userData.target
        return ""

    def setData(self, rowDataSource, index, value):
        userData = rowDataSource.userObject(index)
        # you should replace this code with what you need to set the target for the index(row) on the userData object
        if userData:
            userData.target = value
            return True
        return False

    def customRoles(self, rowDataSource, index):
        """When you have custom roles i.e in this case TYPE_ROLE is here for search. it allows you
        to retrieve item data via dataByRole method.
        """
        return [TYPE_ROLE, constants.buttonClickedRole]

    def dataByRole(self, rowDataSource, index, role):
        if TYPE_ROLE == role:
            return self._baseType
        elif role == constants.buttonClickedRole:
            return rowDataSource.controller.columnButtonClicked(self.model.index(index, 1))


class ConstraintTypeColumn(datasources.ColumnEnumerationDataSource):
    """Data in the third "Constraint" column"""

    def __init__(self, headerText=None, model=None, parent=None):
        super(ConstraintTypeColumn, self).__init__(headerText, model, parent)
        self.constraintTypes = CONSTRAINT_TYPES

    def data(self, rowDataSource, index):
        """Returns the constraint type as a string.

        :param rowDataSource:
        :type rowDataSource:
        :param index:
        :type index:
        :return: The constraint as a string eg "Parent"
        :rtype: str
        """
        userData = rowDataSource.userObject(index)
        if userData:
            return userData.constraintType
        return ""

    def setData(self, rowDataSource, index, value):
        """Sets the constraint type on the userData object.

        :param rowDataSource: Qt row data source
        :type rowDataSource:
        :param index: The index of the
        :type index:
        :param value:
        :type value:
        :return:
        :rtype:
        """
        userData = rowDataSource.userObject(index)
        if userData:
            userData.constraintType = self.constraintTypes[value]
            return True
        return False

    def enums(self, rowDataSource, index):
        return self.constraintTypes
