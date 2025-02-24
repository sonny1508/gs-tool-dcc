import copy
import os
import random

from zoo.apps.hiveartistui.hivenaming import fieldwidget, presetwidget, rulewidget
from zoo.core import api
from zoo.core.util import zlogging
from zoo.libs.hive import api as hiveapi
from zoo.libs.naming import naming
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt import utils
from zoo.libs.pyqt.widgets import elements
from zoovendor.Qt import QtWidgets, QtCore

logger = zlogging.getLogger(__name__)


class NamingConventionUI(elements.ZooWindow):
    helpUrl = "https://create3dcharacters.com/maya-tool-hive-naming-convention/"
    windowSettingsPath = "zoo/hivenamingconventionui"

    def _initUi(self):
        super(NamingConventionUI, self)._initUi()
        self.uiState = UIState()
        self.uiState.isAdmin = api.currentConfig().isAdmin
        self.presetView = presetwidget.PresetView(parent=self)
        self.presetView.setMaximumWidth(utils.dpiScale(200))

        self.conventionCombobox = elements.ComboBoxRegular("Hive Type", items=[],
                                                           boxRatio=100,
                                                           labelRatio=8,
                                                           parent=self,
                                                           sortAlphabetically=True)
        self.conventionCombobox.layout().setAlignment(self.conventionCombobox.label, QtCore.Qt.AlignRight)
        self.rulesCombobox = elements.ComboBoxRegular(label="Rule Type",
                                                      labelRatio=8,
                                                      boxRatio=100,
                                                      items=[],
                                                      parent=self,
                                                      sortAlphabetically=True)
        self.rulesCombobox.layout().setAlignment(self.rulesCombobox.label, QtCore.Qt.AlignRight)

        self.rulePreviewLabel = elements.Label(text="Rule Preview", parent=self)
        self.ruleExpressionWidget = rulewidget.CompleterStringEdit("Rule", labelRatio=8, editRatio=100, parent=self)
        self.ruleExpressionWidget.layout().setAlignment(self.ruleExpressionWidget.label, QtCore.Qt.AlignRight)

        self.fieldsWidget = fieldwidget.FieldsWidget(parent=self)
        self.fieldsLabel = elements.LabelDivider("Fields", parent=self)
        self.saveCancelBtn = elements.OkCancelButtons("Save", parent=self)

        self.ruleCompleter = QtWidgets.QCompleter([], parent=self)
        self.ruleExpressionWidget.edit.setCompleter(self.ruleCompleter)

        # Main Layout ---------------------------------------
        self._setupLayout()
        self._setupConnections()
        self.disableState()
        self._initializePresetTree()

    def _setupLayout(self):
        mainLayout = elements.vBoxLayout(margins=(uic.WINSIDEPAD, uic.WINBOTPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=2)
        self.setMainLayout(mainLayout)

        conventionWidget = QtWidgets.QWidget(parent=self)
        conventionLayout = elements.vBoxLayout(parent=conventionWidget)

        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal, parent=self)
        splitter.addWidget(self.presetView)
        splitter.addWidget(conventionWidget)

        conventionLayout.addWidget(self.conventionCombobox)
        conventionLayout.addWidget(self.rulesCombobox)
        conventionLayout.addWidget(self.ruleExpressionWidget)
        conventionLayout.addWidget(self.rulePreviewLabel)
        conventionLayout.addWidget(self.fieldsLabel)
        conventionLayout.addWidget(self.fieldsWidget, 1)
        mainLayout.addWidget(splitter, 1)
        mainLayout.addWidget(self.saveCancelBtn, 0, QtCore.Qt.AlignBottom)

    def _setupConnections(self):
        self.presetView.selectionChanged.connect(self._onPresetSelectionChanged)
        self.presetView.presetModel.dataChanged.connect(self._onPresetDataChanged)
        self.conventionCombobox.currentIndexChanged.connect(self._onConventionTypeChanged)
        self.rulesCombobox.currentIndexChanged.connect(self._onRuleTypeChanged)
        self.presetView.createPresetBtn.triggered.connect(self._onCreatePreset)
        self.presetView.removePresetBtn.triggered.connect(self._onRemovePreset)
        self.saveCancelBtn.OkBtnPressed.connect(self._onSave)
        self.saveCancelBtn.CancelBtnPressed.connect(self._onCancel)
        self.ruleExpressionWidget.textChanged.connect(self._onRuleExpressionChanged)

    def _initializePresetTree(self):
        self.uiState.presetManager = hiveapi.namingpresets.PresetManager()
        self.uiState.originalManager = hiveapi.namingpresets.PresetManager()
        hierarchy = self.uiState.presetManager.prefInterface.namingPresetHierarchy()
        hiveConfig = hiveapi.Configuration()
        self.uiState.rigConfig = hiveConfig
        componentTypes = hiveConfig.componentRegistry().components.keys()
        self.uiState.presetManager.updateAvailableConfigTypes(componentTypes)
        self.uiState.originalManager.updateAvailableConfigTypes(componentTypes)
        self.uiState.presetManager.loadFromEnv(hierarchy)
        self.uiState.originalManager.loadFromEnv(hierarchy)
        root = self.uiState.presetManager.rootPreset
        if root is not None:
            self.presetView.loadPreset(root, includeRoot=self.uiState.isAdmin, parent=None)

    def enabledState(self, preset=True):
        if preset:
            self.conventionCombobox.setEnabled(True)
        else:
            self.rulesCombobox.setEnabled(True)
            self.rulePreviewLabel.setEnabled(True)
            self.ruleExpressionWidget.setEnabled(True)
            self.fieldsWidget.setEnabled(True)
            self.fieldsLabel.setEnabled(True)

    def disableState(self):
        self.conventionCombobox.setEnabled(False)
        self.rulesCombobox.setEnabled(False)
        self.rulePreviewLabel.setEnabled(False)
        self.ruleExpressionWidget.setEnabled(False)
        self.fieldsWidget.setEnabled(False)
        self.fieldsLabel.setEnabled(False)

    def _onPresetSelectionChanged(self, event):
        """When the preset changes we refresh the UI for the new preset.

        :param event:
        :type event: :class:`zoo.libs.pyqt.extended.treeviewplus.TreeViewPlusSelectionChangedEvent`
        """
        logger.debug("Preset Selection Changed")
        for selection in event.currentItems:
            presetName = selection.data(0)
            self._loadPreset(presetName)
            break
        self.enabledState(True)

    def _onConventionTypeChanged(self, index):
        self.conventionCombobox.itemData(index, QtCore.Qt.UserRole)
        requestedConvention = self.conventionCombobox.currentText()
        isLocal = self.conventionCombobox.currentData(QtCore.Qt.UserRole)
        config = self.uiState.currentPreset.findNamingConfigForType(requestedConvention)
        if not isLocal:
            # create a new empty configuration based on the requested type that way we only store
            # the local changes and don't modify the original
            rules = [i.serialize() for i in config.rules(recursive=True)]
            fields = [i.serialize() for i in config.fields(recursive=True)]
            config = self.uiState.currentPreset.createConfig(name=None, hiveType=requestedConvention,
                                                             rules=rules, fields=fields).config
            # now copy the rules and fields into the new config, and we'll diff the changes on save
            self.conventionCombobox.setItemData(index, True)  # 77 is now isLocal
            self.uiState.presetsOps.createConfigOp(self.uiState.currentPreset, requestedConvention)
            self.uiState.requiresSave = True
        else:
            self.uiState.presetsOps.createConfigUpdateOp(self.uiState.currentPreset, requestedConvention)
            self.uiState.requiresSave = True
            # copy all fields into the local config, this will be diffed on save
            config.setFields(copy.deepcopy(set(config.fields(recursive=True))))

        self.uiState.currentConfig = config
        logger.debug("Changed Hive config Type to: {}".format(config.name))
        self._updateRuleTypes()
        self.fieldsWidget.reloadFromConfig(self.uiState.currentConfig)
        self.enabledState(False)

    def _onRuleTypeChanged(self, index):
        self._resetCurrentRule()

    def _onCreatePreset(self):
        selectedIndices = self.presetView.selectedQIndices()
        model = self.presetView.presetModel
        if not selectedIndices:
            index = QtCore.QModelIndex()
        else:
            index = selectedIndices[0]

        label = elements.InputDialogQt(windowName="Preset Name",
                                       message="Please Enter a Unique Preset Name",
                                       parent=self)
        if not label:
            return
        existingPreset = self.uiState.presetManager.findPreset(label)
        if existingPreset is not None:
            elements.MessageBox.showWarning(title="Non-Unique Name", parent=self,
                                            message="Preset name '{}' must be unique")
        outputFolder = self.uiState.presetManager.prefInterface.namingPresetSavePath()
        if index.isValid():
            parentPresetLabel = model.data(index)
        else:
            parentPresetLabel = hiveapi.constants.DEFAULT_BUILTIN_PRESET_NAME
        parentPreset = self.uiState.presetManager.findPreset(parentPresetLabel)
        newPreset = self.uiState.presetManager.createPreset(label, outputFolder, parent=parentPreset)
        self.uiState.presetsOps.createAddPresetOp(newPreset)
        self.uiState.requiresSave = True
        model.insertRow(0, parent=index, label=newPreset.name)
        self.presetView.expandAll()

    def _onRemovePreset(self):
        items = self.presetView.selectedItems()
        if not items:
            return
        model = self.presetView.presetModel
        for item in items:
            label = item.data(0)
            if label == hiveapi.constants.DEFAULT_BUILTIN_PRESET_NAME:
                continue

            preset = self.uiState.presetManager.findPreset(label)
            if self.uiState.presetManager.removePreset(label):
                self.uiState.presetsOps.createDeletePresetOp(preset)
                self.uiState.requiresSave = True
                index = item.modelIndex()
                model.removeRows(index.row(), 1, parent=index.parent())

    def _onPresetDataChanged(self, topLeft, bottomRight, roles):
        dataSource = self.presetView.presetModel.itemFromIndex(topLeft)
        name = dataSource.label
        if name == hiveapi.constants.DEFAULT_BUILTIN_PRESET_NAME:
            return

        preset = self.uiState.presetManager.findPreset(dataSource.previousLabel)

        self.uiState.presetsOps.createRenameOp(preset, preset.name, name)
        preset.name = name
        self.uiState.requiresSave = True

    def _onRuleExpressionChanged(self, text):
        currentRuleName = self.rulesCombobox.currentText()
        cfg = self.uiState.currentConfig
        if cfg.hasRule(currentRuleName, recursive=False):
            currentRule = cfg.rule(currentRuleName)
        else:
            parentRule = cfg.rule(currentRuleName)
            currentRule = cfg.addRule(recursive=False, **parentRule.serialize())

        fields = currentRule.exampleFields
        expression = []
        for field in text.split("_"):
            hasField = fields.get(field)
            if not hasField:
                expression.append(field)
            else:
                expression.append(hiveapi.namingpresets.surroundTextAsField(field))
        self.uiState.currentConfig.rule(currentRuleName).expression = "_".join(expression)
        self.updatePreviewRuleLabel()

    def _onSave(self):
        save(self.uiState.presetManager.prefInterface, self.uiState)
        self.uiState.requiresSave = False
        self.close()

    def close(self):
        if self.uiState.requiresSave:
            result = elements.MessageBox.showWarning(parent=self, title="You May Have Unsaved Changes",
                                                     message="Save Changes to current convention?",
                                                     buttonA="Save", buttonB="Don't Save", buttonC="Cancel")
            if result == "C":
                return
            if result == "A":
                self._onSave()
        super(NamingConventionUI, self).close()

    def _onCancel(self):
        self.close()

    def _loadPreset(self, presetName):
        logger.debug("Loading preset: {}".format(presetName))
        self.uiState.currentPreset = self.uiState.presetManager.findPreset(presetName)
        self._updateComponentTypes()

    def _updateComponentTypes(self):
        types = sorted(list(self.uiState.presetManager.availableConfigTypes()))
        localTypes = {i.hiveType for i in self.uiState.currentPreset.configs}
        self.conventionCombobox.blockSignals(True)
        self.conventionCombobox.clear()
        # setup component types with user data to mark if that component has been modified
        # locally on the current preset

        for globalType in types:
            data = globalType in localTypes
            self.conventionCombobox.addItem(globalType, userData=data)
        self.conventionCombobox.blockSignals(False)
        self._onConventionTypeChanged(0)

    def _updateRuleTypes(self):
        logger.debug("Updating Rule Widget for config: {}".format(self.uiState.currentConfig.name))
        globalRules = list(sorted(self.uiState.currentConfig.rules(recursive=True), key=lambda x: x.name))
        localRules = list(self.uiState.currentConfig.rules(recursive=False))
        self.rulesCombobox.blockSignals(True)
        self.rulesCombobox.clear()
        for globalType in globalRules:
            data = globalType in localRules
            self.rulesCombobox.addItem(globalType.name, userData=data)
        self.rulesCombobox.blockSignals(False)

        self._onRuleTypeChanged(0)

    def _resetCurrentRule(self):
        currentRule = self.rulesCombobox.currentText()
        config = self.uiState.currentConfig
        rule = config.rule(currentRule, recursive=True)
        ruleFields = rule.exampleFields
        fieldValues = dict(rule.exampleFields)
        ruleFieldsLineEdit = {}
        for fieldName in ruleFields:

            field = config.field(fieldName)
            ruleFieldsLineEdit[fieldName] = fieldName
            # returns None because it's likely an implicit field ie. componentName
            if field is None:
                continue
            randomFieldInt = random.randrange(0, field.count())
            keyValue = list(field.keyValues())[randomFieldInt]
            fieldValues[fieldName] = keyValue.value
        self.ruleExpressionWidget.setText(config.resolve(rule.name, ruleFieldsLineEdit))
        self.ruleCompleter.setModel(QtCore.QStringListModel(ruleFields.keys()))
        self.setPreviewRuleText(config.resolve(currentRule, fieldValues))

    def updatePreviewRuleLabel(self):
        currentRule = self.rulesCombobox.currentText()
        config = self.uiState.currentConfig
        rule = config.rule(currentRule, recursive=True)
        ruleFields = rule.fields()
        fieldValues = dict(rule.exampleFields)
        for fieldName in ruleFields:

            field = config.field(fieldName)
            # returns None because it's likely an implicit field ie. componentName
            if field is None:
                continue
            randomFieldInt = random.randrange(0, field.count())
            keyValue = list(field.keyValues())[randomFieldInt]
            fieldValues[fieldName] = keyValue.value

        previewLabel = config.resolve(currentRule, fieldValues)
        self.setPreviewRuleText(previewLabel)
        return fieldValues, previewLabel

    def setPreviewRuleText(self, suffix):
        prefix = "<b>Rule Preview:</b> <i>{}</i>".format(suffix)

        self.rulePreviewLabel.setText(prefix)


class UIState(object):
    def __init__(self):
        self.isAdmin = False
        self.presetManager = None  # type: hiveapi.namingpresets.PresetManager
        self.currentConfig = None  # type: naming.NameManager
        self.currentPreset = None  # type: hiveapi.namingpresets.Preset
        self.presetsOps = PresetOperations()
        self.originalManager = None  # type: hiveapi.namingpresets.PresetManager
        self.rigConfig = None
        self.requiresSave = True


class PresetOperations(object):
    def __init__(self):
        self.operations = {}

    def createAddPresetOp(self, preset):
        self.operations.setdefault(preset, {})["add"] = preset

    def createDeletePresetOp(self, preset):
        ops = self.operations.get(preset, {})
        # if the preset was added then it wasn't saved to disk so just remove the op
        try:
            del ops["add"]
            return
        except (NameError, KeyError):
            pass
        self.operations.setdefault(preset, {})["delete"] = preset

    def createRenameOp(self, preset, oldName, newName):
        presetOp = self.operations.get(preset)
        # it may have already been renamed so just update the newName so the
        # oldName stays as the original
        try:
            currentRenameOp = presetOp["rename"]
            currentRenameOp["newName"] = newName
            return
        except (KeyError, TypeError):
            pass
        self.operations.setdefault(preset, {})["rename"] = {"oldName": oldName,
                                                            "newName": newName,
                                                            "preset": preset}

    def createConfigUpdateOp(self, preset, hiveType):
        presetOp = self.operations.get(preset)
        try:
            # the config may have been created so ignore the update op as it's unnecessary
            createOps = presetOp["createConfig"]
            if hiveType in createOps or hiveType in presetOp.get("updateConfig", []):
                return
        except (KeyError, TypeError):
            pass
        self.operations.setdefault(preset, {}).setdefault("updateConfig", []).append(hiveType)

    def createConfigOp(self, preset, hiveType):
        self.operations.setdefault(preset, {}).setdefault("createConfig", []).append(hiveType)

    def createDeleteConfigOp(self, preset, hiveType):
        pass


def save(preferences, uiState):
    currentPresetManager = uiState.presetManager
    requiresPreferencesSave = False
    for preset, ops in uiState.presetsOps.operations.items():
        savePreset = _handleSaveConfigsOps(ops, preset, uiState)
        requiresPreferencesSave = _handleSaveAddOps(ops, savePreset, preset, uiState) or requiresPreferencesSave
        requiresPreferencesSave = _handleSaveDeleteOps(ops, preset, uiState) or requiresPreferencesSave
        requiresPreferencesSave = _handleSaveRenameOps(ops, preset, uiState) or requiresPreferencesSave

    if requiresPreferencesSave:
        data = currentPresetManager.hierarchyData()
        preferences.setNamingPresetHierarchy(data, save=True)
        hiveReg = hiveapi.Configuration.namePresetRegistry()
        if hiveReg is not None:
            hiveReg.loadFromEnv(data)


def _handleSaveAddOps(ops, savePreset, preset, uiState):
    if "add" in ops or savePreset:
        uiState.presetManager.savePreset(preset)
        return True
    return False


def _handleSaveRenameOps(ops, preset, uiState):
    renameOp = ops.get("rename")
    if renameOp:
        filePath = preset.filePath
        baseName = os.path.basename(filePath)
        baseName = baseName.replace(renameOp["oldName"], renameOp["newName"])
        uiState.presetManager.deletePreset(preset)
        preset.filePath = os.path.join(os.path.dirname(filePath), baseName)
        uiState.presetManager.savePreset(preset)
        return True
    return False


def _handleSaveDeleteOps(ops, preset, uiState):
    if "delete" in ops:
        uiState.presetManager.deletePreset(preset)
        return True
    return False


def _handleSaveConfigsOps(ops, preset, uiState):
    presetName = preset.name
    renameOp = ops.get("rename")
    if renameOp:
        presetName = renameOp["oldName"]

    savePreset = False
    originalPreset = uiState.originalManager.findPreset(presetName)
    for hiveType in ops.get("createConfig", []):
        config = preset.findNamingConfigForType(hiveType)
        parentPreset = preset.parent or originalPreset

        if parentPreset is not None:
            diffConfig = config.changes(parentPreset.findNamingConfigForType(hiveType))
            if not diffConfig.hasChanges():
                preset.removeConfigByHiveType(hiveType)
                continue
            config = diffConfig.diff
        savePreset = uiState.presetManager.saveConfig(config)
    savePreset = _handleSaveUpdateConfig(ops, preset, originalPreset, uiState) or savePreset
    return savePreset


def _handleSaveUpdateConfig(ops, preset, originalPreset, uiState):
    savePreset = False
    for hiveType in ops.get("updateConfig", []):
        # The config which the UI is working with
        changeConfig = preset.findNamingConfigForType(hiveType)

        # will default to use the parent config which is the original config
        # i.e the global component config or parent preset config
        changes = changeConfig.changes()
        if not changes.hasChanges():
            preset.deleteConfig(changeConfig)
            savePreset = True
            continue
        savePreset = uiState.presetManager.saveConfig(changes.diff) or savePreset
    return savePreset
