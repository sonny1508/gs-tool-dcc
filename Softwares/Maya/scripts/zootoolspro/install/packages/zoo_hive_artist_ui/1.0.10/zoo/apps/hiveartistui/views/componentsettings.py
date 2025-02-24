from functools import partial

from zoo.apps.hiveartistui.hivenaming import presetwidget
from zoo.apps.hiveartistui.views import widgethelpers
from zoo.apps.hiveartistui.views.spaceswitching import SpaceSwitchWidget, HiveSpaceSwitchController
from zoo.core.util import zlogging
from zoo.libs.commands import hive
from zoo.libs.hive import api as hiveapi
from zoo.libs.maya.api import attrtypes
from zoo.libs.pyqt.widgets import elements
from zoo.core.util import strutils
from zoovendor.Qt import QtWidgets

logger = zlogging.getLogger(__name__)


class ComponentSettingsWidget(QtWidgets.QFrame):
    """
    :param componentWidget: The UI top level component widget(stackItem).
    :type componentWidget: :class:`zoo.apps.hiveartistui.views.componentwidget.ComponentWidget`
    :param parent: The QFrame which is a child of the componentWidget class
    :type parent: :class:`QtWidgets.QFrame`
    :param componentModel: The container class for the component model, this contains the \
    hive component instance.
    :type componentModel: :class:`zoo.apps.hiveartistui.model.ComponentModel`
    """
    showSpaceSwitching = True

    def __init__(self, componentWidget, parent, componentModel):

        super(ComponentSettingsWidget, self).__init__(parent)
        self.rigModel = componentModel.rigModel
        self.componentWidget = componentWidget
        self.componentModel = componentModel
        self.settingsWidgets = []
        self._spaceSwitchLayoutCreated = False
        self._namingLayoutCreated = False

        layout = elements.vBoxLayout(parent=self, margins=(6, 8, 6, 8))
        # Default widgets
        self._parentWidget = widgethelpers.ParentWidget(self.rigModel, componentModel=self.componentModel, parent=self)
        self._parentWidget.parentChanged.connect(self.onParentChanged)
        orientSetting = self.componentModel.component.definition.guideLayer.guideSetting("manualOrient")

        layout.addWidget(self._parentWidget)

        manualOrientWidget = createBooleanWidget(self, orientSetting, "Manual Orient", layout,
                                                 self.settingCheckboxChanged)
        self.settingsWidgets.append((orientSetting, manualOrientWidget))

        self.initUi()

    def initUi(self):
        """Base generic initializer for constructing all supported guide settings types as widgets.
        If overridden in subclass then you'll need to recreate all guide settings other than the manual
        orient.
        """
        layout = self.layout()

        # Add setting widgets
        for setting in self.componentModel.component.definition.guideLayer.settings:
            if setting.name == "manualOrient":
                continue
            name = strutils.titleCase(setting.name)

            if setting.Type == attrtypes.kMFnNumericBoolean:  # Bool
                wid = createBooleanWidget(self, setting, name, layout, self.settingCheckboxChanged)
                self.settingsWidgets.append((setting, wid))

            elif setting.Type in (attrtypes.kMFnNumericInt, attrtypes.kMFnNumericLongLegacy):  # int
                edit = createIntWidget(self, setting, name, layout, self.settingNumericChanged)
                self.settingsWidgets.append((setting, edit))
            # ignore id attribute, legacy template/rig fix
            elif setting.Type == attrtypes.kMFnDataString and name not in ("id", hiveapi.constants.ID_ATTR):  # int
                edit = createStringWidget(self, setting, name, layout, self.settingStringChanged)
                self.settingsWidgets.append((setting, edit))

            elif setting.Type == attrtypes.kMFnNumericFloat:  # float
                edit = createStringWidget(self, setting, name, layout, self.settingNumericChanged)
                self.settingsWidgets.append((setting, edit))

            elif setting.Type == attrtypes.kMFnkEnumAttribute:  # Enum
                edit = createEnumWidget(self, setting, name, layout, None, self.enumChanged)
                self.settingsWidgets.append((setting, edit))
            else:
                logger.warning("Setting {} Type '{}' not yet implemented".format(name,
                                                                                 attrtypes._TYPE_TO_STRING.get(
                                                                                     setting.Type,
                                                                                     "missingType:{}".format(
                                                                                         setting.Type))))
        if self.showSpaceSwitching:
            self.createSpaceLayout()
        self.createNamingConventionLayout()

    def createSpaceLayout(self):
        layout = self.layout()
        self.spaceSwitchFrame = elements.CollapsableFrameThin("Space Switching", parent=self,
                                                              collapsed=True)
        layout.addWidget(self.spaceSwitchFrame)

        self.spaceSwitchFrame.openRequested.connect(self.onSpaceSwitchFrameOpen)
        self.spaceSwitchFrame.closeRequested.connect(
            partial(self.componentWidget.tree.updateTreeWidget, True))

    def createNamingConventionLayout(self):
        layout = self.layout()
        self.namingConventionFrame = elements.CollapsableFrameThin("Naming Convention", parent=self,
                                                                   collapsed=True)
        self.namingConventionFrame.closeRequested.connect(
            partial(self.componentWidget.tree.updateTreeWidget, True))
        self.namingConventionFrame.openRequested.connect(self.onNamingConventionFrameOpen)
        layout.addWidget(self.namingConventionFrame)

    def onSpaceSwitchFrameOpen(self):
        """Called when the user expands the spaceSwitch section.

        This Function will created the space Switch container widget only on the first open.
        We do this only on demand to speed up the widget creation for the component.
        """
        if self._spaceSwitchLayoutCreated:
            self.componentWidget.tree.updateTreeWidget(True)
            return
        self._spaceSwitchLayoutCreated = True
        controller = HiveSpaceSwitchController(self.rigModel,
                                               self.componentModel,
                                               parent=self)
        self.spaceSwitchWidget = SpaceSwitchWidget(controller,
                                                   parent=self)

        self.spaceSwitchFrame.addWidget(self.spaceSwitchWidget)

        self.spaceSwitchWidget.spaceChanged.connect(partial(self.componentWidget.tree.updateTreeWidget, True))
        self.componentWidget.tree.updateTreeWidget(True)

    def onNamingConventionFrameOpen(self):
        if self._namingLayoutCreated:
            self.componentWidget.tree.updateTreeWidget(True)
            return

        self._namingLayoutCreated = True

        self.namingPresetWidget = presetwidget.PresetChooser(parent=self)
        self._onBeforeBrowseNamingPreset()
        self.namingPresetWidget.beforeBrowseSig.connect(self._onBeforeBrowseNamingPreset)
        self.namingPresetWidget.presetSelectedSig.connect(self._onBrowserNamingSelectionChanged)

        self.namingConventionFrame.addWidget(self.namingPresetWidget)
        self.componentWidget.tree.updateTreeWidget(True)

    def _onBeforeBrowseNamingPreset(self):
        currentCompPreset = self.componentModel.component.currentNamingPreset()
        currentRigPreset = self.rigModel.configuration.currentNamingPreset
        rootPreset = self.rigModel.configuration.namePresetRegistry().rootPreset
        self.namingPresetWidget.setPreset(rootPreset)
        if currentCompPreset == currentRigPreset:
            self.namingPresetWidget.setText("No Preset Override")
        else:
            self.namingPresetWidget.setText(currentCompPreset.name)

    def _onBrowserNamingSelectionChanged(self, presetName):
        comp = self.componentModel.component
        comp.definition.namingPreset = presetName
        comp.saveDefinition(comp.definition)

    def updateUi(self):
        logger.debug("Updating ComponentSettings: {}".format(self.componentModel.displayName()))
        self._parentWidget.updateCombo()
        if self._spaceSwitchLayoutCreated:
            self.spaceSwitchWidget.controller.rigModel = self.rigModel
            self.spaceSwitchWidget.controller.componentModel = self.componentModel
            self.spaceSwitchWidget.updateUI()
        if self._namingLayoutCreated:
            self._onBeforeBrowseNamingPreset()

    def settingStringChanged(self, widget, setting):
        value = widget.text()
        hive.updateGuideSettings(self.componentModel.component, {setting.name: value})

    def settingCheckboxChanged(self, widget, setting, value):
        hive.updateGuideSettings(self.componentModel.component, {setting.name: value})

    def settingNumericChanged(self, widget, setting, *args, **kwargs):
        """

        :param widget:
        :type widget: :class:`elements.IntEdit` or :class:`elements.FloatEdit`
        :param setting:
        :type setting:
        :return:
        :rtype: bool
        """

        value = widget.edit.convertValue(widget.text())
        existingSetting = self.componentModel.component.definition.guideLayer.guideSetting(setting.name)
        if existingSetting is not None:
            if existingSetting.value == value:
                return False
            hive.updateGuideSettings(self.componentModel.component, {setting.name: value})
            return True
        return False

    def enumChanged(self, event, widget, setting):
        """

        :type event: :class:`zoo.libs.pyqt.extended.combobox.ComboItemChangedEvent`
        :param event: 
        :param widget:
        :type widget: :class:`elements.ComboBoxRegular`
        :param setting:
        :return:
        """
        hive.updateGuideSettings(self.componentModel.component, {setting.name: event.index})

    def onParentChanged(self, parentComponent, guide):
        self.componentWidget.core.executeTool("setComponentParent", args=dict(
            parentComponent=parentComponent, parentGuide=guide,
            childComponent=self.componentModel.component))


def createRadioWidget(componentSettingsWidget, settings, names, layout, signalFunc, toolTips=None):
    group = elements.JoinedRadioButton(componentSettingsWidget,
                                       texts=names, toolTips=toolTips)
    layout.addWidget(group)
    group.buttonClicked.connect(signalFunc)
    state = 0
    for index, setting in enumerate(settings):
        if setting is  None:
            continue
        if setting.value:
            state = index
    group.setChecked(state)
    return group


def createBooleanWidget(componentSettingsWidget, setting, name, layout, signalFunc, toolTip=None):
    checkBox = elements.CheckBox(name, setting.value, boxRatio=16, labelRatio=4,
                                 right=True, parent=componentSettingsWidget, toolTip=toolTip)
    layout.addWidget(checkBox)
    checkBox.stateChanged.connect(partial(signalFunc, checkBox, setting))
    return checkBox


def createFloatWidget(componentSettingsWidget, setting, name, layout, signalFunc=None, supportsSlider=False,
                      sliderStartSignalFunc=None, sliderChangedFunc=None, sliderFinishedFunc=None, toolTip=None):
    edit = elements.FloatEdit(label=name, editText=setting.value, parent=componentSettingsWidget, toolTip=toolTip,
                              labelRatio=4)
    minValue, maxValue = setting.get("min"), setting.get("max")
    if minValue is not None:
        edit.setMinValue(minValue)
    if maxValue is not None:
        edit.setMaxValue(maxValue)
    if supportsSlider:
        edit.sliderStarted.connect(partial(sliderStartSignalFunc, edit, setting))
        edit.sliderChanged.connect(partial(sliderChangedFunc, edit, setting))
        edit.sliderFinished.connect(partial(sliderFinishedFunc, edit, setting))
    if signalFunc is not None:
        edit.textModified.connect(partial(signalFunc, edit, setting))
    layout.addWidget(edit)
    return edit


def createIntWidget(componentSettingsWidget, setting, name, layout, signalFunc, toolTip=None):
    edit = elements.IntEdit(label=name, editText=setting.value, parent=componentSettingsWidget,
                            toolTip=toolTip,
                            labelRatio=4)
    minValue, maxValue = setting.get("min"), setting.get("max")
    if minValue is not None:
        edit.setMinValue(minValue)
    if maxValue is not None:
        edit.setMaxValue(maxValue)
    edit.editingFinished.connect(partial(signalFunc, edit, setting))
    layout.addWidget(edit)
    return edit


def createEnumWidget(componentSettingsWidget, setting, name, layout, items, signalFunc, toolTip=None):
    items = items or setting.get('enums', [])
    combo = elements.ComboBoxRegular(label=name, parent=componentSettingsWidget,
                                     items=[strutils.titleCase(it) for it in items],
                                     itemData=items,
                                     setIndex=setting.value,
                                     boxRatio=16, labelRatio=4,
                                     supportMiddleMouseScroll=False, toolTip=toolTip)
    combo.itemChanged.connect(lambda value, w=combo, s=setting: signalFunc(value, w, s))
    layout.addWidget(combo)
    return combo


def createStringWidget(componentSettingsWidget, setting, name, layout, signalFunc, toolTip=None):
    edit = elements.StringEdit(label=name, editText=setting.value, parent=componentSettingsWidget,
                               toolTip=toolTip)
    edit.editingFinished.connect(partial(signalFunc, edit, setting))
    layout.addWidget(edit)
    return edit
