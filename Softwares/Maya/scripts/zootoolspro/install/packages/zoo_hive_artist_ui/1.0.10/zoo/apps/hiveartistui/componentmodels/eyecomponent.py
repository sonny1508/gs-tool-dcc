from functools import partial

from maya import cmds
from zoo.libs.hive.library.subsystems import eyelidsubsystem
from zoo.apps.hiveartistui import model
from zoo.apps.hiveartistui.views import componentsettings
from zoo.core.util import strutils
from zoo.libs.commands import hive
from zoo.libs.maya import zapi
from zoo.libs.maya.cmds.objutils import selection
from zoo.libs.pyqt.widgets import elements
from zoo.libs.pyqt import uiconstants
from zoo.libs.utils import output


class EyeComponentModel(model.ComponentModel):
    """Base Class for Vchain class and subclasses to support better UI
    organization.
    """

    componentType = "eyecomponent"

    def createWidget(self, componentWidget, parentWidget):
        return EyeSettingsWidget(componentWidget, parentWidget, componentModel=self)


class EyeSettingsWidget(componentsettings.ComponentSettingsWidget):
    showSpaceSwitching = False

    def __init__(self, componentWidget, parent, componentModel):
        self.ratioLayouts = {}
        self.ratioFrameLayouts = {}
        super(EyeSettingsWidget, self).__init__(componentWidget, parent, componentModel)

    def initUi(self):
        guideSettings = (
            self.componentModel.component.definition.guideLayer.guideSettings(
                "innerLidUprJointCount",
                "innerLidLwrJointCount",
                "outerLidUprJointCount",
                "outerLidLwrJointCount",
                "hasOuterCtrls",
                "hasStartEndInner",
                "hasStartEndOuter",
                "hasNonUniformScale",
                "showBlinkRatioAttrs",
                "hasPupilIris",
            )
        )
        mainLayout = self.layout()
        innerLayout = elements.hBoxLayout()
        outerLayout = elements.hBoxLayout()

        hasOuterCurve = guideSettings["hasOuterCtrls"]
        componentsettings.createBooleanWidget(
            self,
            guideSettings["hasPupilIris"],
            "Has Pupil And Iris",
            mainLayout,
            self._onLidEnabled,
        )
        componentsettings.createBooleanWidget(
            self, hasOuterCurve, "Has Outer Curve", mainLayout, self._onLidEnabled
        )
        componentsettings.createBooleanWidget(
            self,
            guideSettings["hasNonUniformScale"],
            "Has Non-Uniform Scale",
            mainLayout,
            self.settingCheckboxChanged,
        )
        componentsettings.createBooleanWidget(
            self,
            guideSettings["showBlinkRatioAttrs"],
            "Show Blink Ratio Attrs in ChannelBox",
            mainLayout,
            self.settingCheckboxChanged,
        )
        self.outerSettingsLayout = elements.CollapsableFrameThin(
            "Outer Lid Settings", parent=self, collapsed=True
        )
        self.innerSettingsLayout = elements.CollapsableFrameThin(
            "Inner Lid Settings", parent=self, collapsed=True
        )

        self.outerSettingsLayout.toggled.connect(
            partial(self.componentWidget.tree.updateTreeWidget, delay=True)
        )
        self.innerSettingsLayout.toggled.connect(
            partial(self.componentWidget.tree.updateTreeWidget, delay=True)
        )
        self.outerSettingsLayout.setEnabled(hasOuterCurve.value)
        mainLayout.addWidget(self.innerSettingsLayout)
        mainLayout.addWidget(self.outerSettingsLayout)

        eyeLidSubsys = self.componentModel.component.subsystems()["lids"]

        self._createLidUI(
            (eyelidsubsystem.INNER_UPR_CURVE_ID, eyelidsubsystem.INNER_LWR_CURVE_ID),
            ("Set Inner Upr Lid Curve", "Set Inner Lwr Lid Curve"),
            settingLabels=[
                "Upr Lid Joint  Count",
                "Lwr Lid Joint  Count",
                "Has Start/End Ctrls/Joints",
            ],
            parentLayout=self.innerSettingsLayout,
            eyeLidSubsys=eyeLidSubsys,
            guideSettings=[
                guideSettings["innerLidUprJointCount"],
                guideSettings["innerLidLwrJointCount"],
                guideSettings["hasStartEndInner"],
            ],
        )
        self._createLidUI(
            (eyelidsubsystem.OUTER_UPR_CURVE_ID, eyelidsubsystem.OUTER_LWR_CURVE_ID),
            ("Set Outer Upr Lid Curve", "Set Outer Lwr Lid Curve"),
            settingLabels=[
                "Upr Lid Joint  Count",
                "Lwr Lid Joint  Count",
                "Has Start/End Ctrls/Joints",
            ],
            parentLayout=self.outerSettingsLayout,
            eyeLidSubsys=eyeLidSubsys,
            guideSettings=[
                guideSettings["outerLidUprJointCount"],
                guideSettings["outerLidLwrJointCount"],
                guideSettings["hasStartEndOuter"],
            ],
        )

        mainLayout.addLayout(innerLayout)
        mainLayout.addLayout(outerLayout)

        if self.showSpaceSwitching:
            self.createSpaceLayout()
        self.createNamingConventionLayout()
        self.createSpaceLayout()

    def _createLidUI(
        self, curveIds, labels, settingLabels, parentLayout, guideSettings, eyeLidSubsys
    ):
        ratioSettingLayout = elements.CollapsableFrameThin(
            "Blink Ratios", parent=self, collapsed=True
        )
        self.ratioFrameLayouts[curveIds[0]] = ratioSettingLayout
        self.ratioFrameLayouts[curveIds[1]] = ratioSettingLayout
        componentsettings.createIntWidget(
            self,
            guideSettings[0],
            settingLabels[0],
            parentLayout,
            partial(self._countChanged, curveIds[0]),
            toolTip=None,
        )
        componentsettings.createIntWidget(
            self,
            guideSettings[1],
            settingLabels[1],
            parentLayout,
            partial(self._countChanged, curveIds[1]),
            toolTip=None,
        )
        componentsettings.createBooleanWidget(
            self,
            guideSettings[2],
            settingLabels[2],
            parentLayout,
            self.settingCheckboxChanged,
            toolTip=None,
        )
        for curveId, label in zip(curveIds, labels):
            layout = elements.hBoxLayout(spacing=uiconstants.SPACING)
            lidBtn = elements.styledButton(
                label,
                icon="3dManipulator",
                parent=self,
                toolTip="",
                themeUpdates=False,
            )
            lidDeleteBtn = elements.styledButton(
                "",
                icon="trash",
                parent=self,
                toolTip="",
                themeUpdates=False,
            )
            layout.addWidget(lidBtn, 2)
            layout.addWidget(lidDeleteBtn)
            parentLayout.addLayout(layout)
            lidBtn.clicked.connect(partial(self._onCreateLidCurve, curveId))
            lidDeleteBtn.clicked.connect(partial(self._deleteLidCurve, curveId))

            self._createBlinkRatios(
                ratioSettingLayout,
                curveId,
                eyeLidSubsys,
            )
        parentLayout.addWidget(ratioSettingLayout)
        ratioSettingLayout.toggled.connect(
            partial(self.componentWidget.tree.updateTreeWidget, delay=True)
        )

    def _countChanged(self, curveId, widget, setting):
        oldValue, newValue = setting.value, widget.value()
        subsystem = self.componentModel.component.subsystems()["lids"]
        paramNames = subsystem.blinkJointRatioParams(curveId)
        self.settingNumericChanged(widget, setting)

        if newValue < oldValue:
            ratioWidgets = self.ratioLayouts.get(curveId, {})
            for paramName in paramNames[newValue :]:
                wid = ratioWidgets.get(paramName)
                if wid is not None:
                    wid.deleteLater()
        else:
            self._createBlinkRatios(
                self.ratioFrameLayouts[curveId],
                curveId,
                subsystem,
            )
        self.componentWidget.tree.updateTreeWidget(delay=True)

    def _onLidEnabled(self, widget, setting, value):
        self.outerSettingsLayout.setEnabled(bool(value))
        hive.updateGuideSettings(self.componentModel.component, {setting.name: value})

    def _createBlinkRatios(self, parent, curveId, eyeLidSubSystem):
        """

        :param curveId:
        :type curveId:
        :param eyeLidSubSystem:
        :type eyeLidSubSystem: :class:``zoo.libs.hive.library.subsystems.eyelidsubsystem.EyeLidsSubsystem``
        :return:
        :rtype:
        """

        guideLayerDef = self.componentModel.component.definition.guideLayer
        for paramName in eyeLidSubSystem.blinkJointRatioParams(curveId):
            param = guideLayerDef.guideSetting(paramName)
            existingParamWidget = self.ratioLayouts.get(curveId, {}).get(paramName)
            if existingParamWidget is not None and param is None:
                existingParamWidget.deleteLater()
                del self.ratioLayouts[curveId][paramName]
                continue
            if param is None:
                continue

            if existingParamWidget is not None:
                existingParamWidget.setValue(param.value)
            else:
                settingWidget = componentsettings.createFloatWidget(
                    self,
                    param,
                    strutils.titleCase(param.name),
                    parent,
                    self.settingNumericChanged,
                    toolTip=None,
                )
                self.ratioLayouts.setdefault(curveId, {}).update(
                    {param.name: settingWidget}
                )

    def _deleteLidCurve(self, curveId):
        eyeLidSubsys = self.componentModel.component.subsystems()[
            "lids"
        ]  # type: eyelidsubsystem.EyeLidsSubsystem
        eyeLidSubsys.deleteLidCurve(curveId)
        edits = self.ratioLayouts.get(curveId, {})
        for ratioLayout in edits.values():
            ratioLayout.deleteLater()
        if edits:
            del self.ratioLayouts[curveId]

    def _onCreateLidCurve(self, curveId):
        sel = cmds.ls(orderedSelection=True, long=True)
        if not sel:
            output.displayError("No Edges selected")
            return
        selType = selection.componentSelectionType(sel)
        if selType == "object":
            output.displayError("No Edges selected")
            return
        vertices = selection.convertSelection(type="vertices")
        if not vertices:
            output.displayError("No Edges selected")
            return

        meshObj, vertexIndices = None, []
        for i in vertices:
            meshName = i.partition(".")[0]
            meshObj = zapi.nodeByName(meshName)
            vertexRange = i[i.index("[") + 1 : i.index("]")].split(":")
            if len(vertexRange) > 1:
                vertexIndices.extend(
                    list(range(int(vertexRange[0]), int(vertexRange[1]) + 1))
                )
            else:
                vertexIndices.append(int(vertexRange[0]))

        subsystems = self.componentModel.component.subsystems()
        subsystems["lids"].createGuideLidCurve(meshObj, vertexIndices, curveId)
        frameLayout = self.ratioFrameLayouts.get(curveId)
        if frameLayout:
            self._createBlinkRatios(frameLayout, curveId, subsystems["lids"])
        self.componentWidget.tree.updateTreeWidget(delay=False)
