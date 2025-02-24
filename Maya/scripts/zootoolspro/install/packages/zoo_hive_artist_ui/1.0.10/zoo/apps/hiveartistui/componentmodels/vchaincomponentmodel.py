import itertools

from zoo.apps.hiveartistui import model
from zoo.apps.hiveartistui.views import componentsettings
from zoo.libs.maya import zapi
from zoo.libs.maya.qt import mayaui
from zoo.libs.pyqt import uiconstants
from zoo.libs.pyqt.widgets import elements
from zoo.core.util import strutils
from functools import partial
from zoo.libs.commands import hive
from zoo.libs.maya.utils import general


class ArmComponentModel(model.ComponentModel):
    """Base Class for Vchain class and subclasses to support better UI
    organization.
    """
    componentType = "armcomponent"

    def createWidget(self, componentWidget, parentWidget):
        return VChainSettingsWidget(componentWidget,
                                    parentWidget,
                                    componentModel=self)


class LegComponentModel(ArmComponentModel):
    componentType = "legcomponent"


class VChainSettingsWidget(componentsettings.ComponentSettingsWidget):
    def __init__(self, componentWidget, parent, componentModel):
        self.twistSegmentWidgets = []
        self.bendySettingWidgets = []
        self.volumeSettingWidgets = []
        super(VChainSettingsWidget, self).__init__(componentWidget, parent, componentModel)

    def initUi(self):
        self.advancedSettingsLayout = elements.CollapsableFrameThin("Advanced Settings", parent=self,
                                                                    collapsed=True)
        self.twistSettingsLayout = elements.CollapsableFrameThin("Twist Settings", parent=self.advancedSettingsLayout,
                                                                 collapsed=True)
        self.bendySettingsLayout = elements.CollapsableFrameThin("Bendy Settings", parent=self.advancedSettingsLayout,
                                                                 collapsed=True)
        self.volumeSettingsLayout = elements.CollapsableFrameThin("Volume Settings", parent=self.advancedSettingsLayout,
                                                                  collapsed=True)
        self.advancedSettingsLayout.addWidget(self.twistSettingsLayout)
        self.advancedSettingsLayout.addWidget(self.bendySettingsLayout)
        self.advancedSettingsLayout.addWidget(self.volumeSettingsLayout)
        layout = self.layout()

        guideLayerDef = self.componentModel.component.definition.guideLayer
        primarySettings = guideLayerDef.guideSettings("hasStretch", "ikfk_default",
                                                      "hasTwists", "hasBendy", "uprSegmentCount",
                                                      "lwrSegmentCount", "distributionType", "alignIkEndToWorld")
        self._createIKFKWidget(primarySettings, layout)
        hasTwists = primarySettings["hasTwists"]
        hasBendy = primarySettings["hasBendy"]
        hasStretch = primarySettings["hasStretch"]

        alignIkEndToWorld = primarySettings["alignIkEndToWorld"]
        switchesLayout = elements.hBoxLayout()
        hasStretchWidget = componentsettings.createBooleanWidget(
            self, hasStretch, "Has Stretch", switchesLayout, self.onSwitchChanged
        )
        alignIkEndToWorldWidget = componentsettings.createBooleanWidget(
            self, alignIkEndToWorld, "Align IkEnd To World", switchesLayout, self.onSwitchChanged
        )
        layout.addLayout(switchesLayout)
        twistsBendyWidget = componentsettings.createRadioWidget(self, [None, hasTwists, hasBendy],
                                                                ["No Twists", "Twists", "Twists & Bendy(Beta)"], layout,
                                                                self.onTwistsBendyChanged)
        self.settingsWidgets.append((hasStretch, hasStretchWidget))
        self.settingsWidgets.append((alignIkEndToWorld, alignIkEndToWorldWidget))
        self.settingsWidgets.append((hasTwists, twistsBendyWidget))

        layout.addWidget(self.advancedSettingsLayout)
        self.createSpaceLayout()

        self.advancedSettingsLayout.toggled.connect(partial(self.componentWidget.tree.updateTreeWidget, delay=True))
        self.twistSettingsLayout.toggled.connect(partial(self.componentWidget.tree.updateTreeWidget, delay=True))
        self.bendySettingsLayout.toggled.connect(self._onToggleBendyWidget)
        self.volumeSettingsLayout.toggled.connect(self._volumeSettingsToggled)
        self.advancedSettingsLayout.setEnabled(hasTwists.value or hasBendy.value)
        self.twistSettingsLayout.setEnabled(hasTwists.value)
        self.bendySettingsLayout.setEnabled(hasBendy.value)
        self.volumeSettingsLayout.setEnabled(hasBendy.value)

        if hasTwists.value:
            self._createTwistWidgets(guideLayerDef, primarySettings, self.twistSettingsLayout)

        self.createNamingConventionLayout()

    def onSwitchChanged(self, checkbox, guideSetting, state):
        self.settingCheckboxChanged(checkbox, guideSetting, state)

    def onTwistsBendyChanged(self, event):
        """

        :param event:
        :type event: :class:`zoo.libs.pyqt.widgets.joinedRadio.JoinedRadioButtonEvent`
        """
        hasTwists = False
        hasBendy = False
        if event.index == 0:  # None
            self.advancedSettingsLayout.setEnabled(False)
            if not self.advancedSettingsLayout.collapsed:
                # Hack to hide the flickering on collapse. Updates are re-enabled on tree.updateTreeWidget
                self.componentWidget.tree.setUpdatesEnabled(False)
                self.advancedSettingsLayout.onCollapsed()
        elif event.index == 1:  # hasTwists
            hasTwists = True
            self.advancedSettingsLayout.setEnabled(True)
            self.twistSettingsLayout.setEnabled(True)
            self.bendySettingsLayout.setEnabled(False)
            self.volumeSettingsLayout.setEnabled(False)
        else:  # bendy + twists
            hasBendy = True
            hasTwists = True
            self.twistSettingsLayout.setEnabled(True)
            self.bendySettingsLayout.setEnabled(True)
            self.advancedSettingsLayout.setEnabled(True)
            self.volumeSettingsLayout.setEnabled(True)

        self.componentWidget.tree.updateTreeWidget(delay=True)
        hive.updateGuideSettings(self.componentModel.component, {"hasTwists": hasTwists,
                                                                 "hasBendy": hasBendy})

    def _createIKFKWidget(self, primarySettings, layout):
        """ creates the enum attribute to choose the default state for the ik fk switch.

        :param primarySettings: The list of guide settings for twists.
        :type primarySettings: dict[str, :class:`zoo.libs.hive.api.AttributeDefinition`]
        :param layout: The parent widget for the widget.
        :type layout: :class:`QtWidgets.QVBoxLayout`
        """
        ikfkDefault = primarySettings["ikfk_default"]
        combo = componentsettings.createEnumWidget(self, ikfkDefault, strutils.titleCase("Ikfk Default"),
                                                   layout, ["IK", "FK"], self.enumChanged)
        self.settingsWidgets.append((primarySettings["ikfk_default"], combo))
        layout.addWidget(combo)

    def _createTwistWidgets(self, guideLayerDefinition, primarySettings, layout):
        """
        :param guideLayerDefinition: The current components guide layer definition instance
        :type guideLayerDefinition: :class:`zoo.libs.hive.api.GuideLayerDefinition`
        :param primarySettings: The list of guide settings for twists.
        :type primarySettings: dict[str, :class:`zoo.libs.hive.api.AttributeDefinition`]
        :param layout: The collapsableFrame Layout which is a widget but has layout methods.
        :type layout: :class:`elements.CollapsableFrame`
        """
        self._clearTwistSettings()
        uprSegment = primarySettings["uprSegmentCount"]
        lwrSegment = primarySettings["lwrSegmentCount"]
        distributionType = primarySettings["distributionType"]
        componentsettings.createEnumWidget(self, distributionType, "Distribution Type",
                                           layout, None, self._onDistributionChanged)
        self.uprTwistSegmentWidget = componentsettings.createIntWidget(self, uprSegment, "Upr Segment Count",
                                                                       layout, self._onSegmentValueChanged)

        self.lwrTwistSegmentWidget = componentsettings.createIntWidget(self, lwrSegment, "Lwr Segment Count",
                                                                       layout, self._onSegmentValueChanged)
        minValue = 0 if distributionType.value == 0 else 3
        self.uprTwistSegmentWidget.setMinValue(minValue)
        self.lwrTwistSegmentWidget.setMinValue(minValue)

        self.settingsWidgets.append((uprSegment, self.uprTwistSegmentWidget))
        self.settingsWidgets.append((lwrSegment, self.lwrTwistSegmentWidget))
        # segment count change
        self._createSegmentWidgets(itertools.chain(*self.componentModel.component.twistIds()),
                                   guideLayerDefinition, layout)

    def _onToggleBendyWidget(self):
        if self.bendySettingsLayout.collapsed:
            self._createBendyWidgets(self.componentModel.component.definition.guideLayer, self.bendySettingsLayout)
        self.componentWidget.tree.updateTreeWidget(delay=True)

    def _createBendyWidgets(self, guideLayerDef, layout):
        self._clearBendySettings()

        for bendyCtrlId in self.componentModel.component.bendyIds():
            settingDef = guideLayerDef.guideSetting("{}Position".format(bendyCtrlId))
            if settingDef is None:
                continue

            bendyWidget = componentsettings.createFloatWidget(self, settingDef,
                                                              strutils.titleCase(settingDef.name),
                                                              layout, self.settingNumericChanged)
            bendyWidget.setMinValue(0.0)
            bendyWidget.setMaxValue(1.0)
            self.bendySettingWidgets.append(bendyWidget)

    def _onDistributionChanged(self, event, widget, setting):
        """Called when the twist distribution type has changed.

        :type event:  :class:`zoo.libs.pyqt.extended.combobox.ComboItemChangedEvent`
        :param widget: The combo box for the enum attribute.
        :type widget: :class:`elements.ComboBoxRegular`
        :param setting: The guide setting
        :type setting: :class:`zao.libs.hive.api.AttributeDefinition`
        """
        self.enumChanged(event, widget, setting)
        minValue = 0 if event.index == 0 else 3
        self.uprTwistSegmentWidget.setMinValue(minValue)
        self.lwrTwistSegmentWidget.setMinValue(minValue)

    def _createSegmentWidgets(self, guideIds, guideLayerDefinition, layout):
        """Generates All widgets for a single twist Segment.

        Note you need to handle refresh the treewidget for size hinting . We don't
        handle this here for optimisation.

        :param guideIds: The list of guide ids for twists to display in the UI.
        :type guideIds: list[str]
        :param guideLayerDefinition: The current components guide layer definition instance
        :type guideLayerDefinition: :class:`zoo.libs.hive.api.GuideLayerDefinition`
        :param layout: The collapsableFrame Layout which is a widget but has layout methods.
        :type layout: :class:`elements.CollapsableFrame`
        """
        for twistSetting in sorted(guideLayerDefinition.guideSettings(*guideIds).values(),
                                   key=lambda x: x.name):
            edit = componentsettings.createFloatWidget(self, twistSetting,
                                                       strutils.titleCase(twistSetting.name),
                                                       layout,
                                                       supportsSlider=True,
                                                       sliderFinishedFunc=self._twistSliderFinished,
                                                       sliderStartSignalFunc=self._twistSliderStarted,
                                                       sliderChangedFunc=self._twistSliderValueChanged,
                                                       signalFunc=self._twistValueChanged, )
            self.settingsWidgets.append((twistSetting, edit))
            self.twistSegmentWidgets.append(edit)

    def _setTwistValue(self, setting, value):
        existingSetting = self.componentModel.component.definition.guideLayer.guideSetting(setting.name)
        if existingSetting is not None:
            if existingSetting.value == value:
                return False
            hive.updateGuideSettings(self.componentModel.component, {setting.name: value})
            return True
        return False

    def _twistSliderStarted(self, widget, setting, *args, **kwargs):
        """ Called when the twist slider has started to be changed and opens a maya undo chunk, closed
        by _twistSliderFinished.
        """
        general.openUndoChunk("HiveTwistSlider_{}".format(setting.name))

    def _twistSliderValueChanged(self, widget, setting, value, **kwargs):
        existingSetting = self.componentModel.component.definition.guideLayer.guideSetting(setting.name)
        if existingSetting is None:
            return False
        ret = self._setTwistValue(setting, widget.edit.convertValue(value))
        return ret

    def _twistSliderFinished(self, widget, setting, *args, **kwargs):
        value = widget.edit.convertValue(widget.text())
        ret = self._setTwistValue(setting, value)
        general.closeUndoChunk("HiveTwistSlider_{}".format(setting.name))
        return ret

    def _twistValueChanged(self, widget, setting, *args, **kwargs):
        value = widget.edit.convertValue(widget.text())
        ret = self._setTwistValue(setting, value)
        return ret

    def _onSegmentValueChanged(self, widget, setting):
        """Called when the twist segment count has changed.

        Updates hive component which will handle scene state.
        Purges current twist widgets and rebuilds from new count and then lets the treewidget
        know to handle the size hint.

        :param widget: The zoo tools integer edit widget
        :type widget: :class:`elements.IntEdit`
        :param setting: The guide setting
        :type setting: :class:`zao.libs.hive.api.AttributeDefinition`
        """

        changed = self.settingNumericChanged(widget, setting)
        if not changed:
            return
        guideLayerDef = self.componentModel.component.definition.guideLayer
        for twistWidget in self.twistSegmentWidgets:
            twistWidget.deleteLater()
        self.twistSegmentWidgets = []
        self._createSegmentWidgets(itertools.chain(*self.componentModel.component.twistIds()),
                                   guideLayerDef, self.twistSettingsLayout)
        self.componentWidget.tree.updateTreeWidget()

    def _clearTwistSettings(self):
        for edit in self.twistSegmentWidgets:
            edit.deleteLater()
        self.twistSegmentWidgets = []
        self.settingsWidgets = []

    def _clearBendySettings(self):
        for edit in self.bendySettingWidgets:
            edit.deleteLater()
        self.bendySettingWidgets = []

    def _volumeSettingsToggled(self):
        if self.volumeSettingsLayout.collapsed:
            self._createVolumeWidgets(self.volumeSettingsLayout)
        self.componentWidget.tree.updateTreeWidget(delay=True)

    def _onSquashBtnClicked(self):
        mayaui.openGraphEditor()
        component = self.componentModel.component
        zapi.select([component.squashCurve()])

    def _createVolumeWidgets(self, layout):
        for edit in self.volumeSettingWidgets:
            edit.deleteLater()
        self.volumeSettingWidgets = []
        tooltip = ""
        curveBtn = elements.styledButton("Edit Squash Profile",
                                         icon="graphEditor",
                                         toolTip=tooltip,
                                         style=uiconstants.BTN_DEFAULT, parent=self)
        setting = self.componentModel.component.definition.guideLayer.guideSetting("displayVolumeAttrsChannelBox")
        showInChannelBox = componentsettings.createBooleanWidget(self,
                                                                 setting,
                                                                    "Show Volume Attrs in Channel Box",
                                                                 layout,
                                                                 self.settingCheckboxChanged)
        layout.addWidget(curveBtn)
        self.volumeSettingWidgets.append(curveBtn)
        self.volumeSettingWidgets.append(showInChannelBox)

        curveBtn.clicked.connect(self._onSquashBtnClicked)
        self.componentWidget.tree.updateTreeWidget(True)
