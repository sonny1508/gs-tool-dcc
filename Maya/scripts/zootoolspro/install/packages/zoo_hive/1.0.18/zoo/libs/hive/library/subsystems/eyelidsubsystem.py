import math
from zoo.libs.utils import zoomath
from zoo.libs.hive import api
from zoo.libs.hive.base import basesubsystem
from zoo.libs.hive.base import definition
from zoo.libs.hive.base.util import componentutils

from zoo.libs.maya import zapi
from zoo.libs.maya.utils import mayamath
from zoo.libs.maya.api import mesh, curves
from maya import cmds

MACRO_GUIDE_SHAPE = "sphere"
PUPIL_IRIS_GUIDE_SHAPE = "circle"
META_EXTRA_ATTR = "eyeDifferentiatorBSExtras"
DEFAULT_GUIDE_CTRL_SCALE = (0.5, 0.5, 0.5)
DEFAULT_GUIDE_SHAPE_SCALE = (0.075, 0.075, 0.075)
DEFAULT_PRIMARY_GUIDE_CTRL_SCALE = (0.55, 0.55, 0.55)
DEFAULT_PRIMARY_GUIDE_SHAPE_SCALE = (0.25, 0.125, 0.125)
DEFAULT_GUIDE_JNT_SCALE = (0.1, 0.1, 0.1)

HAS_START_END_OUTER_NAME = "hasStartEndOuter"
HAS_START_END_INNER_NAME = "hasStartEndInner"
HAS_OUTER_CTRLS_NAME = "hasOuterCtrls"
INNER_UPR_CURVE_ID = "innerUprLid"
OUTER_UPR_CURVE_ID = "outerUprLid"
INNER_LWR_CURVE_ID = "innerLwrLid"
OUTER_LWR_CURVE_ID = "outerLwrLid"

PRIMARY_CTRL_SHAPE_MAP = {
    INNER_UPR_CURVE_ID: "triangle_round",
    OUTER_UPR_CURVE_ID: "slider_square",
    INNER_LWR_CURVE_ID: "triangle_round",
    OUTER_LWR_CURVE_ID: "slider_square",
}
CURVE_COLOR_MAP = {
    INNER_UPR_CURVE_ID: (1.0, 0.182, 0.073),
    OUTER_UPR_CURVE_ID: (1.0, 0.350, 0.073),
    INNER_LWR_CURVE_ID: (0.128, 1.0, 0.073),
    OUTER_LWR_CURVE_ID: (0.755, 1.0, 0.073),
}
CURVE_STARTEND_COLOR_MAP = {
    INNER_UPR_CURVE_ID: (0.432, 0.223, 1.0),
    OUTER_UPR_CURVE_ID: (0.163, 0.073, 1.0),
}
DEFAULT_PRIMARY_CTRL_GUIDE_ROT_MAP = {
    INNER_UPR_CURVE_ID: (math.pi * -0.5, 0.0, 0.0),
    OUTER_UPR_CURVE_ID: (math.pi * -0.5, 0.0, 0.0),
    INNER_LWR_CURVE_ID: (math.pi * 0.5, 0.0, 0.0),
    OUTER_LWR_CURVE_ID: (math.pi * 0.5, 0.0, 0.0),
}

CURVE_HAS_START_END_MAP = {
    INNER_UPR_CURVE_ID: HAS_START_END_INNER_NAME,
    OUTER_UPR_CURVE_ID: HAS_START_END_OUTER_NAME,
}
CURVE_IDS = (
    INNER_UPR_CURVE_ID,
    INNER_LWR_CURVE_ID,
    OUTER_UPR_CURVE_ID,
    OUTER_LWR_CURVE_ID,
)
JOINT_COUNT_SETTING_NAMES = [
    "innerLidUprJointCount",
    "innerLidLwrJointCount",
    "outerLidUprJointCount",
    "outerLidLwrJointCount",
]
CURVE_OPPOSITES_MAP = {
    "innerUprLid": "innerLwrLid",
    "outerUprLid": "outerLwrLid",
}
CURVE_SETTINGS_ID_MAP = {
    "innerLwrLid": "innerLidLwrJointCount",
    "innerUprLid": "innerLidUprJointCount",
    "outerUprLid": "outerLidUprJointCount",
    "outerLwrLid": "outerLidLwrJointCount",
}
CURVE_JNT_SETTINGS_ID_MAP = {
    "innerLidUprJointCount": "innerUprLid",
    "innerLidLwrJointCount": "innerLwrLid",
    "outerLidUprJointCount": "outerUprLid",
    "outerLidLwrJointCount": "outerLwrLid",
}

_ROT_CONST_SETTINGS_MAP = {
    "innerLwrLidCtrl00": ("innerLid00UpDownMaxRot", "innerLid00LRMaxRot"),
    "innerUprLidCtrl00": ("innerLid00UpDownMaxRot", "innerLid00LRMaxRot"),
    "innerLwrLidCtrl01": ("innerLid01UpDownMaxRot", "innerLid01LRMaxRot"),
    "innerUprLidCtrl01": ("innerLid01UpDownMaxRot", "innerLid01LRMaxRot"),
    "innerLwrLidCtrl02": ("innerLid02LidUpDownMaxRot", "innerLid02LRMaxRot"),
    "innerUprLidCtrl02": ("innerLid02LidUpDownMaxRot", "innerLid02LRMaxRot"),
    "innerLwrLidCtrl03": ("innerLid03UpDownMaxRot", "innerLid03LRMaxRot"),
    "innerUprLidCtrl03": ("innerLid03UpDownMaxRot", "innerLid03LRMaxRot"),
    "innerLwrLidCtrl04": ("innerLid04UpDownMaxRot", "innerLid04LRMaxRot"),
    "innerUprLidCtrl04": ("innerLid04UpDownMaxRot", "innerLid04LRMaxRot"),
    "outerLwrLidCtrl00": ("outerLid00UpDownMaxRot", "outerLid00LRMaxRot"),
    "outerUprLidCtrl00": ("outerLid00UpDownMaxRot", "outerLid00LRMaxRot"),
    "outerLwrLidCtrl01": ("outerLid01UpDownMaxRot", "outerLid01LRMaxRot"),
    "outerUprLidCtrl01": ("outerLid01UpDownMaxRot", "outerLid01LRMaxRot"),
    "outerLwrLidCtrl02": ("outerLid02UpDownMaxRot", "outerLid02LRMaxRot"),
    "outerUprLidCtrl02": ("outerLid02UpDownMaxRot", "outerLid02LRMaxRot"),
    "outerUprLidCtrl03": ("outerLid03UpDownMaxRot", "outerLid03LRMaxRot"),
    "outerLwrLidCtrl03": ("outerLid03UpDownMaxRot", "outerLid03LRMaxRot"),
    "outerLwrLidCtrl04": ("outerLid04UpDownMaxRot", "outerLid04LRMaxRot"),
    "outerUprLidCtrl04": ("outerLid04UpDownMaxRot", "outerLid04LRMaxRot"),
}
EYE_CTRL_VIS_NAME = "eyeCtrlVis"
CTRL_VIS_NAME = "positionScaleCtrl"
INNER_CTRL_VIS_NAME = "innerCtrlVis"
OUTER_CTRL_VIS_NAME = "outerCtrlVis"
INNER_SECONDARY_CTRL_VIS_NAME = "innerSecondaryVis"
OUTER_SECONDARY_CTRL_VIS_NAME = "outerSecondaryVis"
PUPIL_VIS_NAME = "pupilIrisVis"
# scale multiplier difference between the guide scale and the final rig scale
# this exists because eyeScale is 0.25 for some reason
EYE_SCALE_SCALE_MULTIPLIER = 0.25


class EyeLidsSubsystem(basesubsystem.BaseSubsystem):
    """
    :param component: The component associated with this subsystem.
    :type component: :class:`zoo.libs.hive.base.component.Component`
    :param jointCounts:
    :type: jointCounts: dict[str, int]
    """

    def __init__(self, component, jointCounts, buildPupil=False):
        super(EyeLidsSubsystem, self).__init__(component)
        self.rootParentId = "parentSpace"
        self.buildPupil = buildPupil
        self._jointCountSettings = {
            CURVE_JNT_SETTINGS_ID_MAP[k]: v for k, v in jointCounts.items()
        }  # type:  dict[str, api.AttributeDefinition]
        self._ctrls = {}  # type: dict[str, api.ControlNode]
        self._ctrlJoints = {}  # type: dict[str, api.DagNode]
        self._parentSpaceTransform = None  # type: None or zapi.DagNode
        self._eyeScale = (1.0, 1.0, 1.0)
        self._requiresNonUniformScale = False
        self._ctrlCount = 5

    def guideCtrlIdsForCurve(self, curveId):
        """Generate a list of control IDs for a given curve.

        :param curveId: str
        :type curveId: The ID of the curve.
        :return: list
        :rtype: A list of control IDs for the given curve.
        """
        return [self.guideCtrlIdForCurve(curveId, i) for i in range(self._ctrlCount)]

    def guideJointIdsForCurve(self, curveId):
        """Generate a list of joint IDs for a given curve.

        :param curveId: str
        :type curveId: The ID of the curve.
        :return: list
        :rtype: A list of joint IDs for the given curve.
        """
        curveCount = self._jointCountSettings[curveId].value
        return [self.guideJointIdForCurve(curveId, i) for i in range(curveCount)]

    def blinkRatioParamName(self, guideId):
        """Returns the blink ratio parameter name for the given ctrl guide.

        :param guideId: The guide ctrl id.
        :type guideId: str
        :rtype: str
        """
        return guideId.replace("Ctrl", "") + "BR"

    def blinkJointRatioParams(self, curveId):
        """Returns the list of blink ratio parameter names for the given curveId.

        :param curveId: The curve id.
        :type curveId: str
        :rtype: list[str]
        """
        curveCount = self._jointCountSettings[curveId].value
        return [self.guideJntParamPosSettingName(curveId, i) for i in range(curveCount)]

    @staticmethod
    def guidePrimaryCtrlIdForCurve(curveId):
        """Generate the primary control ID for a given curve ID.

        :param curveId: str
        :type curveId: The ID of the curve.
        :return: str
        :rtype: The primary control ID for the given curve ID.
        """
        return curveId + "Primary"

    @staticmethod
    def guideCtrlIdForCurve(curveId, index):
        """Generate the control ID for a given curve and index.

        :param curveId: str
        :type curveId: The ID of the curve.
        :param index: int
        :type index: The index for the control ID.
        :return: str
        :rtype: The control ID for the given curve and index.
        """
        return curveId + "Ctrl{}".format(str(index).zfill(2))

    @staticmethod
    def guideJointIdForCurve(curveId, index):
        """Generate the joint ID for a given curve and index.

        :param curveId: str
        :type curveId: The ID of the curve.
        :param index: int
        :type index: The index for the joint ID.
        :return: str
        :rtype: The joint ID for the given curve and index.
        """
        return curveId + "Bind{}".format(str(index).zfill(2))

    @staticmethod
    def guideCtrlParamPosSettingName(curveId, index):
        """Generate the setting name for the control parameter position for a given curve and index.

        :param curveId: str
        :type curveId: The ID of the curve.
        :param index: int
        :type index: The index for the setting name.
        :return: str
        :rtype: The setting name for the control parameter position for the given curve and index.
        """
        return curveId + "Ctrl{}Pos".format(str(index).zfill(2))

    @staticmethod
    def guideJntParamPosSettingName(curveId, index):
        """Generate the setting name for the joint parameter position for a given curve and index.

        :param curveId: str
        :type curveId: The ID of the curve.
        :param index: int
        :type index: The index for the setting name.
        :return: str
        :rtype: The setting name for the joint parameter position for the given curve and index.
        """
        return curveId + "Jnt{}Pos".format(str(index).zfill(2))

    def startEndGuideCtrlIds(self, curveId):
        """Generate the control IDs for the start and end of a given curve.

        :param curveId: str
        :type curveId: The ID of the curve.
        :return: list
        :rtype: A list of control IDs for the start and end of the given curve.
        """
        hasName = CURVE_HAS_START_END_MAP.get(curveId, "")
        has = self.component.definition.guideLayer.guideSetting(hasName)
        if has and has.value:
            if "inner" in curveId:
                return ["innerStart", "innerEnd"]
            else:
                return ["outerStart", "outerEnd"]
        return []

    def startEndGuideJntIds(self, curveId):
        """Generate the joint IDs for the start and end of a given curve.

        :param curveId: str
        :type curveId: The ID of the curve.
        :return: list
        :rtype: A list of joint IDs for the start and end of the given curve.
        """
        hasName = CURVE_HAS_START_END_MAP.get(curveId, "")
        has = self.component.definition.guideLayer.guideSetting(hasName)

        if has and has.value:
            if "inner" in curveId:
                return ["innerStartBind", "innerEndBind"]
            else:
                return ["outerStartBind", "outerEndBind"]
        return []

    def _generateAnimAttributes(self, ignoreShowBlinkAttrs=False):
        guideLayerDef = self.component.definition.guideLayer
        showAttrsInChannelBox = True
        if not ignoreShowBlinkAttrs:
            showAttrsInChannelBox = guideLayerDef.guideSetting(
                "showBlinkRatioAttrs"
            ).value
        guides = [k.id for k in guideLayerDef.iterGuides()]

        settings = []
        for curveId in CURVE_IDS:
            try:
                guides.index(curveId)
            except ValueError:
                continue
            for guideId in self.guideCtrlIdsForCurve(curveId):
                paramName = self.blinkRatioParamName(guideId)
                guideSetting = guideLayerDef.guideSetting(paramName)
                value = 1.0 if "inner" in curveId else 0.1
                if guideSetting is not None:
                    value = guideSetting.value
                kwargs = {
                    "name": paramName,
                    "Type": zapi.attrtypes.kMFnNumericFloat,
                    "value": value,
                    "default": value,
                    "channelBox": showAttrsInChannelBox,
                    "keyable": False,
                }
                settings.append(api.AttributeDefinition(**kwargs))
        settings.sort(key=lambda x: x.name)
        return settings

    def createGuideLidCurve(self, meshObject, vertices, curveId):
        """Creates a guide curve for the lid curve based on the provided vertices.

        :param meshObject: The mesh object.
        :type meshObject: :class:`zapi.Mesh`
        :param vertices: The vertices to create the guide curve from.
        :type vertices: list[int]
        :param curveId: The ID of the curve.
        :type curveId: str
        :return: The created guide curve.
        :rtype: :class:`zapi.NurbsCurve`
        """
        self.deleteGuideCurve(curveId)

        topVertsGraph = mesh.constructVerticeGraph(meshObject.dagPath(), vertices)
        topVertexLoops = mesh.sortLoops(topVertsGraph)
        positions = mesh.vertexPositions(
            meshObject.dagPath(), topVertexLoops[0], sortKey="x"
        )

        guideLayer = self.component.guideLayer()
        curveGuide = guideLayer.guide(curveId)
        if not curveGuide:
            curveGuide = guideLayer.createGuide(
                id=curveId,
                translate=positions[int(len(positions) * 0.5)],
                parent="root",
                scale=(0.3, 0.3, 0.3),
                shape="cube",
                pivotShape="sphere_arrow",
            )
        else:
            curveGuide.setTranslation(
                positions[int(len(positions) * 0.5)], zapi.kWorldSpace
            )
            shapeNode = curveGuide.shapeNode()
            if shapeNode:
                shapeNode.delete()
        curve = self._generateGuideCurve(curveId, positions)

        curveGuide.setShapeNode(curve)
        curve.setParent(guideLayer.rootTransform())
        curve.setShapeColour((1.0, 0.897, 0.073), shapeIndex=-1)
        self.component.definition.guideLayer.createGuide(
            **curveGuide.serializeFromScene(
                extraAttributesOnly=True, includeNamespace=False, useShortNames=True
            )
        )
        container = self.component.container()
        if container:
            container.publishNodes([curveGuide, curveGuide.shapeNode()])
        jointCount = self.component.definition.guideLayer.guideSetting(
            CURVE_SETTINGS_ID_MAP[curveId]
        ).value
        ctrlParamMultipliers = list(zoomath.lerpCount(0, 1, self._ctrlCount))[1:-1]
        ctrlParamMultipliers.insert(0, ctrlParamMultipliers[0] * 0.25)
        ctrlParamMultipliers.append(1.0 - (1.0 - ctrlParamMultipliers[-1]) * 0.25)
        self._createGuideParamSettings(
            curveId, ctrlParamMultipliers, self.guideCtrlParamPosSettingName
        )
        self._createGuideParamSettings(
            curveId,
            list(zoomath.lerpCount(0, 1, jointCount + 2))[1:-1],
            self.guideJntParamPosSettingName,
        )
        self._createLidGuides(curve, curveId, self._ctrlCount, jointCount)
        if curveId in (INNER_UPR_CURVE_ID, OUTER_UPR_CURVE_ID):
            self._createInnerOuterGuides(
                curve.shapes()[0], "inner" if "inner" in curveId else "outer", curveId
            )
        self.component.saveDefinition(self.component.definition)
        self.component.rig.buildGuides([self.component])

        return curve

    def _generateGuideCurve(self, curveId, positions):
        curve = zapi.nurbsCurveFromPoints(
            curveId, positions, shapeData={"form": 1, "degree": 3}
        )[0]
        curve.rename(curveId)
        cmds.rebuildCurve(
            curve.fullPathName(),
            constructionHistory=False,
            replaceOriginal=True,
            rebuildType=0,
            endKnots=1,
            keepRange=0,
            keepControlPoints=0,
            keepEndPoints=1,
            keepTangents=0,
            spans=self._ctrlCount - 1,
            degree=3,
            tolerance=0.004,
        )

        return curve

    def deleteLids(self, typeName):
        """Deletes guide curves based on the provided type name.

        :param typeName: The type name to filter the guide curves.
        :type typeName: str
        """
        for curve in CURVE_IDS:
            if typeName in curve:
                self.deleteGuideCurve(curve)

    def deleteGuideCurve(self, curveId):
        """Deletes a guide curve based on the provided curve ID.

        :param curveId: The ID of the curve.
        :type curveId: str
        """
        guideLayer = self.component.guideLayer()
        jntIds = self.guideJointIdsForCurve(curveId)
        ctrlIds = self.guideCtrlIdsForCurve(curveId)
        primaryGuideId = self.guidePrimaryCtrlIdForCurve(curveId)
        ids = jntIds + ctrlIds + [curveId, primaryGuideId]
        ids.extend(self.startEndGuideCtrlIds(curveId))
        ids.extend(self.startEndGuideJntIds(curveId))
        self.component.definition.guideLayer.deleteGuides(*ids)
        guideLayer.deleteGuides(*ids)

    def preUpdateGuideSettings(self, settings):
        """First stage of updating guide settings. Intended to delete anything from
        :param settings:
        :type settings:
        :return:
        :rtype:
        """

        rebuild, runPostUpdate = False, False

        for settingName, value in settings.items():
            if settingName.endswith("Count"):
                rebuild = self._handleLidJointCountChanged(settingName, value)
            elif settingName.startswith("hasStartEnd"):
                rebuild = self._handleLidStartEndChanged(settingName, value)
            elif settingName == HAS_OUTER_CTRLS_NAME:
                rebuild = self._handleOuterLidStateChanged(value)
            elif settingName == "hasPupilIris":
                rebuild = self._handlePupilIrisStateChanged(value)
        # when we're change joint count we should purge all attributes, guides only
        # related to that specific curve
        return rebuild, runPostUpdate

    def _handleLidJointCountChanged(self, settingName, value):
        curveId = CURVE_JNT_SETTINGS_ID_MAP[settingName]
        curveGuide = self.component.guideLayer().guide(curveId)
        if not curveGuide:
            return False

        existingGuideIds = self.guideJointIdsForCurve(curveId)
        if len(existingGuideIds) == value:
            return False
        curveShapeNode = curveGuide.shapeNode()
        curveShape = curveShapeNode.shapes()[0]
        guideSettings = [
            self.guideJntParamPosSettingName(curveId, i)
            for i in range(len(existingGuideIds))
        ]
        self.component.definition.guideLayer.deleteSettings(guideSettings)
        self.component.guideLayer().deleteGuides(*existingGuideIds)
        self.component.definition.guideLayer.deleteGuides(*existingGuideIds)

        self._createGuideParamSettings(
            curveId,
            list(zoomath.lerpCount(0, 1, value + 2))[1:-1],
            self.guideJntParamPosSettingName,
        )
        self._createJointGuides(
            self.component.definition.guideLayer,
            curveShape,
            curveId,
            value,
        )
        return True

    def _handleLidStartEndChanged(self, settingName, value):
        if value:
            curveId = (
                INNER_UPR_CURVE_ID
                if settingName.endswith("Inner")
                else OUTER_UPR_CURVE_ID
            )
            curveGuide = self.component.guideLayer().guide(curveId)
            if not curveGuide:
                return False
            self._createInnerOuterGuides(
                curveGuide.shapeNode().shapes()[0],
                "inner" if settingName.endswith("Inner") else "outer",
                curveId,
            )
            return True
        guideIds = []
        if settingName.endswith("Inner"):
            guideIds.extend(self.startEndGuideJntIds(INNER_UPR_CURVE_ID))
            guideIds.extend(self.startEndGuideCtrlIds(INNER_UPR_CURVE_ID))
        else:
            guideIds.extend(self.startEndGuideJntIds(OUTER_UPR_CURVE_ID))
            guideIds.extend(self.startEndGuideCtrlIds(OUTER_UPR_CURVE_ID))

        self.component.guideLayer().deleteGuides(*guideIds)
        self.component.definition.guideLayer.deleteGuides(*guideIds)
        return True

    def _handleOuterLidStateChanged(self, value):
        if value:
            return False
        guideLayerDef = self.component.definition.guideLayer
        guideIds = self._guideIdsForCurveDeletion(OUTER_UPR_CURVE_ID)
        guideIds += self._guideIdsForCurveDeletion(OUTER_LWR_CURVE_ID)

        guideLayerDef.deleteGuides(*guideIds)
        self.component.guideLayer().deleteGuides(
            *guideIds + [OUTER_UPR_CURVE_ID, OUTER_LWR_CURVE_ID]
        )
        guideSettings = self._guideSettingsNamesForDeletion(
            OUTER_LWR_CURVE_ID, guideLayerDef
        )
        guideSettings += self._guideSettingsNamesForDeletion(
            OUTER_UPR_CURVE_ID, guideLayerDef
        )

        guideLayerDef.deleteSettings(guideSettings)
        return True

    def _guideIdsForCurveDeletion(self, lidCurve):
        guideIds = self.guideCtrlIdsForCurve(lidCurve)
        guideIds.extend(self.guideJointIdsForCurve(lidCurve))
        guideIds.extend(self.startEndGuideCtrlIds(lidCurve))
        guideIds.extend(self.startEndGuideJntIds(lidCurve))
        guideIds.append(self.guidePrimaryCtrlIdForCurve(lidCurve))
        return guideIds + [lidCurve]

    def _guideSettingsNamesForDeletion(self, curveId, guideLayerDef):
        uprJointCount = guideLayerDef.guideSetting(CURVE_SETTINGS_ID_MAP[curveId]).value
        guideSettings = [
            self.guideCtrlParamPosSettingName(curveId, i)
            for i in range(self._ctrlCount)
        ]
        guideSettings.extend(
            [self.guideJntParamPosSettingName(curveId, i) for i in range(uprJointCount)]
        )
        return guideSettings

    def _handlePupilIrisStateChanged(self, value):
        if value:
            self._createPupilGuides()
            return True

        self.component.guideLayer().deleteGuides("pupil", "iris")
        self.component.definition.guideLayer.deleteGuides("pupil", "iris")
        return True

    def _createPupilGuides(self):
        guideLayer = self.component.definition.guideLayer
        parent = "eye"
        pos = guideLayer.guide("eyeMain").translate
        rotate = guideLayer.guide("eyeMain").rotate
        scale = [i * 1.25 for i in guideLayer.guide("eyeMain").scale]
        for guideId in ("pupil", "iris"):
            guideLayer.createGuide(
                id=guideId,
                parent=parent,
                translate=list(pos),
                rotate=list(rotate),
                pivotScale=scale,
                shape=PUPIL_IRIS_GUIDE_SHAPE,
                color=(0.12800000607967377, 1, 0.0729999989271164),
                scale=DEFAULT_GUIDE_CTRL_SCALE,
                selectionChildHighlighting=self.component.configuration.selectionChildHighlighting,
                shapeTransform={
                    "translate": list(pos),
                    "scale": DEFAULT_GUIDE_SHAPE_SCALE,
                    "rotate": list(rotate),
                },
                attributes=[
                    {
                        "name": api.constants.AUTOALIGNAIMVECTOR_ATTR,
                        "value": [0, 0, 1],
                    }
                ],
            )
            parent = guideId

    def deleteLidCurve(self, lidCurve):
        guideLayerDef = self.component.definition.guideLayer
        guideIds = self._guideIdsForCurveDeletion(lidCurve)
        guideLayerDef.deleteGuides(*guideIds)
        self.component.guideLayer().deleteGuides(*guideIds)
        guideSettings = self._guideSettingsNamesForDeletion(lidCurve, guideLayerDef)

        guideLayerDef.deleteSettings(guideSettings)

    def preMirror(self, translate, rotate, parent):
        guideLayer = self.component.guideLayer()
        extraAttr = guideLayer.attribute("zooMotionPathExtras")
        # remove the connection first to avoid changes to transform
        for guide in guideLayer.iterGuides():
            offsetParent = guide.attribute("offsetParentMatrix")
            source = offsetParent.source()
            if source:
                source.disconnect(guide.attribute("offsetParentMatrix"))

        for extra in extraAttr:
            sourceNode = extra.sourceNode()
            if sourceNode:
                sourceNode.delete()

    def postMirror(self, translate, rotate, parent):
        self.postSetupGuide()

    def preAlignGuides(self):
        if not self.active():
            return [], []

        def _calculateGuideMatrix(transform, upPos, aimVector, upVector, curveMfn):
            pos = transform.translation(zapi.kWorldSpace)
            closestPoint, paramForPoint = curveMfn.closestPoint(
                zapi.Point(pos), space=zapi.kWorldSpace
            )
            worldUpVec = curveMfn.tangent(paramForPoint + 0.01, zapi.kWorldSpace)
            rotation = mayamath.lookAt(
                pos,
                upPos,
                aimVector=upVector,
                upVector=aimVector,
                worldUpVector=worldUpVec,
            )
            transform.setRotation(rotation)
            return transform.asMatrix()

        def _calculateStartEndMatrix(guide, aimGuide, multiplier=1.0):
            guideRot = mayamath.lookAt(
                guide.translation(zapi.kWorldSpace),
                aimGuide.translation(zapi.kWorldSpace),
                aimVector=guide.attribute(api.constants.AUTOALIGNAIMVECTOR_ATTR).value()
                * multiplier,
                upVector=guide.attribute(api.constants.AUTOALIGNUPVECTOR_ATTR).value(),
            )
            startGuideTransform = guide.transformationMatrix()
            startGuideTransform.setRotation(guideRot)
            return startGuideTransform.asMatrix()

        # general alignment rules
        # for each upr/lwr curve grouping we aim the top and bottom guide towards each other
        # where the upVector of the guide is aimed at the opposite guide
        # and the aimVector acts as the upVector, worldUp is the next guide in the chain
        # rule exceptions
        # start and end are aligned to each other
        # center guide has it's upVector aligned to the eye Matrix plane
        # these alignment rules give a reasonable sliding effect where translating controls around.
        guideLayer = self.component.guideLayer()
        for i in guideLayer.iterGuides(includeRoot=False):
            i.setLockStateOnAttributes(
                (zapi.localRotateAttr, zapi.localTranslateAttr), False
            )
        eyeGui, eyeMainGui, scaleGui, pupil, iris = guideLayer.findGuides(
            "eye", "eyeMain", "eyeScale", "pupil", "iris"
        )
        eyeMatrix = eyeGui.transformationMatrix()
        eyeMatrix.setScale((1, 1, 1), zapi.kWorldSpace)
        guides = [scaleGui]
        matrices = []
        scale = scaleGui.transformationMatrix().scale(zapi.kWorldSpace)
        eyeMatrix.setScale(scale, zapi.kWorldSpace)
        matrices.append(eyeMatrix.asMatrix())
        # eyeMain align
        eyeMatrix.setTranslation(
            eyeMainGui.translation(zapi.kWorldSpace), zapi.kWorldSpace
        )
        eyeMatrix.setScale(
            eyeMainGui.transformationMatrix().scale(zapi.kWorldSpace), zapi.kWorldSpace
        )
        guides.append(eyeMainGui)
        matrices.append(eyeMatrix.asMatrix())
        if pupil is not None:
            for pup in (pupil, iris):
                guides.append(pup)
                matrices.append(pup.worldMatrix())

        for curveUprId, curveLwrId in CURVE_OPPOSITES_MAP.items():
            uprCurveGuide, lwrCurveGuide = guideLayer.findGuides(curveUprId, curveLwrId)
            # ignore alignment is we have no curves set yet
            if not uprCurveGuide or not lwrCurveGuide:
                continue
            uprCurveGuideShape, lwrCurveGuideShape = (
                uprCurveGuide.shapeNode().shapes()[0],
                lwrCurveGuide.shapeNode().shapes()[0],
            )
            uprCurveGuideMfn, lwrCurveGuideMfn = (
                uprCurveGuideShape.mfn(),
                lwrCurveGuideShape.mfn(),
            )
            primaryUprGuide = guideLayer.guide(
                self.guidePrimaryCtrlIdForCurve(curveUprId)
            )
            primaryLwrGuide = guideLayer.guide(
                self.guidePrimaryCtrlIdForCurve(curveLwrId)
            )
            uprIds = self.guideCtrlIdsForCurve(curveUprId)
            lwrIds = self.guideCtrlIdsForCurve(curveLwrId)
            uprGuides = guideLayer.findGuides(*uprIds)
            lwrGuides = guideLayer.findGuides(*lwrIds)
            startEndGuides = self.startEndGuideCtrlIds(curveUprId)
            # because start and end may be turned of by the user
            if startEndGuides:
                startGuide, endGuide = guideLayer.findGuides(*startEndGuides)
                matrices.append(_calculateStartEndMatrix(startGuide, endGuide, 1.0))
                matrices.append(_calculateStartEndMatrix(endGuide, startGuide, -1.0))
                guides.append(startGuide)
                guides.append(endGuide)
            uprTransform = _calculateGuideMatrix(
                primaryUprGuide.transformationMatrix(),
                primaryLwrGuide.translation(zapi.kWorldSpace),
                primaryUprGuide.attribute(
                    api.constants.AUTOALIGNAIMVECTOR_ATTR
                ).value(),
                primaryUprGuide.attribute(api.constants.AUTOALIGNUPVECTOR_ATTR).value(),
                uprCurveGuideMfn,
            )
            lwrTransform = _calculateGuideMatrix(
                primaryLwrGuide.transformationMatrix(),
                primaryUprGuide.translation(zapi.kWorldSpace),
                primaryLwrGuide.attribute(
                    api.constants.AUTOALIGNAIMVECTOR_ATTR
                ).value(),
                primaryLwrGuide.attribute(api.constants.AUTOALIGNUPVECTOR_ATTR).value(),
                lwrCurveGuideMfn,
            )
            matrices.append(uprTransform)
            guides.append(primaryUprGuide)
            matrices.append(lwrTransform)
            guides.append(primaryLwrGuide)

            for index, [upr, lwr] in enumerate(zip(uprGuides, lwrGuides)):
                uprGuide, lwrGuide = upr, lwr
                uprPos = uprGuide.translation(zapi.kWorldSpace)
                lwrPos = lwrGuide.translation(zapi.kWorldSpace)

                uprTransform = _calculateGuideMatrix(
                    uprGuide.transformationMatrix(),
                    lwrPos,
                    uprGuide.attribute(api.constants.AUTOALIGNAIMVECTOR_ATTR).value(),
                    uprGuide.attribute(api.constants.AUTOALIGNUPVECTOR_ATTR).value(),
                    uprCurveGuideMfn,
                )
                lwrTransform = _calculateGuideMatrix(
                    lwrGuide.transformationMatrix(),
                    uprPos,
                    lwrGuide.attribute(api.constants.AUTOALIGNAIMVECTOR_ATTR).value(),
                    lwrGuide.attribute(api.constants.AUTOALIGNUPVECTOR_ATTR).value(),
                    lwrCurveGuideMfn,
                )
                matrices.append(uprTransform)
                guides.append(uprGuide)
                matrices.append(lwrTransform)
                guides.append(lwrGuide)
        return guides, matrices

    def postAlignGuides(self):
        guideLayer = self.component.guideLayer()
        for curveId in CURVE_IDS:
            guides = guideLayer.findGuides(
                *(
                    self.guideCtrlIdsForCurve(curveId)
                    + self.guideJointIdsForCurve(curveId)
                    + [self.guidePrimaryCtrlIdForCurve(curveId)]
                )
            )

            for gui in guides:
                if not gui:
                    continue
                gui.setLockStateOnAttributes(
                    (zapi.localTranslateAttr, zapi.localRotateAttr), True
                )

    def _createGuideParamSettings(self, curveId, paramMultipliers, idGenerator):
        # creates definition settings for controlGuides and joints
        guideLayer = self.component.definition.guideLayer
        for i, param in enumerate(paramMultipliers):
            attrName = idGenerator(curveId, i)
            setting = definition.AttributeDefinition(
                name=attrName,
                Type=zapi.attrtypes.kMFnNumericFloat,
                value=param,
                default=param,
                keyable=False,
                channelBox=True,
            )
            guideLayer.addGuideSetting(setting)

    def _createInnerOuterGuides(self, curve, idPrefix, curveId):
        crvMfn = curve.mfn()
        guideLayerDef = self.component.definition.guideLayer
        ctrlColor = CURVE_STARTEND_COLOR_MAP[curveId]
        upVector = [0.0, -1.0, 0.0]
        if curveId in (OUTER_LWR_CURVE_ID, INNER_LWR_CURVE_ID):
            upVector[1] = 1.0
        for n, param in zip(("Start", "End"), [0.0, 1.0]):
            param = crvMfn.findParamFromLength(crvMfn.length() * param)
            pos = zapi.Vector(crvMfn.getPointAtParam(param, space=zapi.kWorldSpace))
            guideLayerDef.createGuide(
                id=idPrefix + n,
                parent="root",
                translate=list(pos),
                pivotShape="locator",
                shape=MACRO_GUIDE_SHAPE,
                color=ctrlColor,
                pivotColor=[0.477, 1, 0.073],
                scale=DEFAULT_GUIDE_CTRL_SCALE,
                selectionChildHighlighting=self.component.configuration.selectionChildHighlighting,
                shapeTransform={
                    "translate": list(pos),
                    "scale": DEFAULT_GUIDE_SHAPE_SCALE,
                    "rotate": [math.pi * 0.5, 0, 0],
                },
                attributes=[
                    {
                        "name": api.constants.MIRROR_BEHAVIOUR_ATTR,
                        "value": mayamath.MIRROR_SCALE,
                    },
                    {
                        "name": api.constants.AUTOALIGNAIMVECTOR_ATTR,
                        "value": [1.0, 0.0, 0.0],
                    },
                    {"name": api.constants.AUTOALIGNUPVECTOR_ATTR, "value": upVector},
                ],
            )
            guideLayerDef.createGuide(
                shape={},
                id=idPrefix + n + "Bind",
                parent="root",
                translate=list(pos),
                pivotShape="sphere",
                scale=DEFAULT_GUIDE_JNT_SCALE,
                selectionChildHighlighting=self.component.configuration.selectionChildHighlighting,
            )

    def _createLidGuides(self, curve, curveId, ctrlCount, jointCount):
        curveShape = curve.shapes()[0]
        crvMfn = curveShape.mfn()
        guideLayerDef = self.component.definition.guideLayer
        upVector = [0.0, -1.0, 0.0]
        ctrlColor = CURVE_COLOR_MAP[curveId]

        if curveId in (OUTER_LWR_CURVE_ID, INNER_LWR_CURVE_ID):
            upVector[1] = 1.0
        # create control curve guides for the lid and attach to the curve
        crvLength = crvMfn.length()
        for index in range(ctrlCount):
            paramSetting = guideLayerDef.guideSetting(
                self.guideCtrlParamPosSettingName(curveId, index)
            )
            lengthParam = crvMfn.findParamFromLength(crvLength * paramSetting.value)
            pos = zapi.Vector(
                crvMfn.getPointAtParam(lengthParam, space=zapi.kWorldSpace)
            )
            guideLayerDef.createGuide(
                name=curveId,
                pivotShape="locator",
                pivotColor=[0.477, 1, 0.073],
                shape=MACRO_GUIDE_SHAPE,
                id=self.guideCtrlIdForCurve(curveId, index),
                parent="root",
                color=ctrlColor,
                translate=list(pos),
                scale=DEFAULT_GUIDE_CTRL_SCALE,
                selectionChildHighlighting=self.component.configuration.selectionChildHighlighting,
                shapeTransform={
                    "translate": list(pos),
                    "scale": DEFAULT_GUIDE_SHAPE_SCALE,
                    "rotate": [math.pi * 0.5, 0, 0],
                },
                attributes=[
                    {
                        "name": api.constants.MIRROR_BEHAVIOUR_ATTR,
                        "value": mayamath.MIRROR_SCALE,
                    },
                    {
                        "name": api.constants.AUTOALIGNAIMVECTOR_ATTR,
                        "value": [1.0, 0.0, 0.0],
                    },
                    {"name": api.constants.AUTOALIGNUPVECTOR_ATTR, "value": upVector},
                ],
            )
        self._createJointGuides(guideLayerDef, curveShape, curveId, jointCount)

        lengthParam = crvMfn.findParamFromLength(crvLength * 0.5)
        pos = zapi.Vector(crvMfn.getPointAtParam(lengthParam, space=zapi.kWorldSpace))

        guideLayerDef.createGuide(
            name=curveId,
            pivotShape="locator",
            pivotColor=[0.477, 1, 0.073],
            shape=PRIMARY_CTRL_SHAPE_MAP[curveId],
            id=self.guidePrimaryCtrlIdForCurve(curveId),
            parent="root",
            color=ctrlColor,
            translate=list(pos),
            scale=DEFAULT_PRIMARY_GUIDE_CTRL_SCALE,
            selectionChildHighlighting=self.component.configuration.selectionChildHighlighting,
            shapeTransform={
                "translate": list(pos),
                "scale": DEFAULT_PRIMARY_GUIDE_SHAPE_SCALE,
                "rotate": DEFAULT_PRIMARY_CTRL_GUIDE_ROT_MAP[curveId],
            },
            attributes=[
                {
                    "name": api.constants.MIRROR_BEHAVIOUR_ATTR,
                    "value": mayamath.MIRROR_SCALE,
                },
                {
                    "name": api.constants.AUTOALIGNAIMVECTOR_ATTR,
                    "value": [1.0, 0.0, 0.0],
                },
                {"name": api.constants.AUTOALIGNUPVECTOR_ATTR, "value": upVector},
            ],
        )
        return True

    def _createJointGuides(self, guideLayerDef, curve, curveId, count):
        curveMfn = curve.mfn()
        curveLength = curveMfn.length()
        iterator = list(zoomath.lerpCount(0, 1, count + 2))

        for index, param in enumerate(iterator[1:-1]):  # skip the first and last
            paramSetting = guideLayerDef.guideSetting(
                self.guideJntParamPosSettingName(curveId, index)
            )
            lengthParam = curveMfn.findParamFromLength(curveLength * paramSetting.value)
            pos = zapi.Vector(
                curveMfn.getPointAtParam(lengthParam, space=zapi.kWorldSpace)
            )
            guideLayerDef.createGuide(
                id=self.guideJointIdForCurve(curveId, index),
                parent="root",
                translate=list(pos),
                pivotShape="sphere",
                scale=DEFAULT_GUIDE_JNT_SCALE,
                selectionChildHighlighting=self.component.configuration.selectionChildHighlighting,
            )

    def _bindGuideToCurve(self, namingConfig, guide, curve, param, parent):
        """

        :param namingConfig:
        :type namingConfig:
        :param guide:
        :type guide: :class:`api.Guide`
        :param curve:
        :type curve: :class:`zapi.NurbsCurve`
        :param param:
        :type param:
        :return:
        :rtype:
        """
        currentMatrix = guide.worldMatrix()
        currentLocalScale = guide.scale(zapi.kObjectSpace)
        scaleName = namingConfig.resolve(
            "object",
            {
                "componentName": self.component.name(),
                "side": self.component.side(),
                "section": "aimTrsWorldScale",
                "type": "decomposeMatrix",
            },
        )
        mainCtrlScaleDecomp = zapi.createDG(scaleName, "decomposeMatrix")

        guide.setLockStateOnAttributes(
            [zapi.localTranslateAttr, zapi.localRotateAttr], False
        )
        aimVector = guide.autoAlignAimVector.value()
        upVector = guide.autoAlignUpVector.value()
        axisIndex, invert = mayamath.perpendicularAxisFromAlignVectors(
            aimVector, upVector
        )
        motionPathUpVector = mayamath.AXIS_VECTOR_BY_IDX[axisIndex]
        guideLayer = self.component.guideLayer()
        root = guideLayer.guide("root")
        root.worldMatrixPlug().connect(mainCtrlScaleDecomp.inputMatrix)
        motionPath = _bindAimToCurveMath(
            guide.id(),
            curve,
            param,
            root,
            guide,
            guideLayer,
            root,
            root,
            mainCtrlScaleDecomp,
            aimVector,
            motionPathUpVector,
        )

        guide.setWorldMatrix(currentMatrix)
        guide.setScale(currentLocalScale)
        guide.setLockStateOnAttributes(
            [zapi.localTranslateAttr, zapi.localRotateAttr], True
        )
        return [motionPath, mainCtrlScaleDecomp]

    def preSetupGuide(self):
        settings = self._generateAnimAttributes(ignoreShowBlinkAttrs=True)
        guideLayer = self.component.definition.guideLayer
        guideLayer.addGuideSettings(settings)
        if self.buildPupil:
            self._createPupilGuides()

    def postSetupGuide(self):
        if not self.active():
            return
        guideLayer = self.component.guideLayer()
        guideSettings = guideLayer.guideSettings()
        namingConfig = self.component.namingConfiguration()
        rootTranform = guideLayer.rootTransform()
        guides = {i.id(): i for i in guideLayer.iterGuides(includeRoot=False)}
        _extras = []
        extraAttrs = guideLayer.addAttribute(
            name="zooMotionPathExtras",
            Type=zapi.attrtypes.kMFnMessageAttribute,
            isArray=True,
        )
        curveSrts = zapi.createDag(
            namingConfig.resolve(
                "object",
                {
                    "componentName": self.component.name(),
                    "side": self.component.side(),
                    "section": "curveSrts",
                    "type": "hrc",
                },
            ),
            "transform",
            parent=rootTranform,
        )
        # attach guide srts to curves and maintain the offset
        for curveId in CURVE_IDS:
            try:
                curve = guides[curveId].shapeNode()
            except KeyError:
                continue
            curveShape = curve.shapes()[0]
            for index, guideId in enumerate(self.guideCtrlIdsForCurve(curveId)):
                paramSettingId = self.guideCtrlParamPosSettingName(curveId, index)
                attr = guideSettings.attribute(paramSettingId)
                extras = self._bindGuideToCurve(
                    namingConfig, guides[guideId], curveShape, attr, curveSrts
                )
                _extras.extend(extras)
            for index, guideId in enumerate(self.guideJointIdsForCurve(curveId)):
                paramSettingId = self.guideJntParamPosSettingName(curveId, index)
                attr = guideSettings.attribute(paramSettingId)
                extras = self._bindGuideToCurve(
                    namingConfig, guides[guideId], curveShape, attr, curveSrts
                )
                _extras.extend(extras)
            startEndIds = self.startEndGuideJntIds(curveId) + self.startEndGuideCtrlIds(
                curveId
            )
            for index, guideId in enumerate(startEndIds):
                guide = guides[guideId]
                extras = self._bindGuideToCurve(
                    namingConfig, guide, curveShape, index % 2, curveSrts
                )
                _extras.extend(extras)

            # curve guide primaries
            guide = guides[self.guidePrimaryCtrlIdForCurve(curveId)]
            extras = self._bindGuideToCurve(
                namingConfig, guide, curveShape, 0.5, curveSrts
            )
            _extras.extend(extras)
        guideLayer.addExtraNodes(_extras)
        for extra in _extras:
            element = extraAttrs.nextAvailableDestElementPlug()
            extra.attribute("message").connect(element)

    def setupInputs(self):
        if not self.active():
            return
        inputLayer = self.component.inputLayer()
        parentInputSpace = inputLayer.inputNode("parent")
        eyeGuideDef = self.component.definition.guideLayer.guide("eye")
        parentInputSpace.setWorldMatrix(
            eyeGuideDef.transformationMatrix(True, True, scale=False).asMatrix()
        )

    def setupDeformLayer(self, parentJoint):
        if not self.active():
            return
        compDefinition = self.component.definition
        deformLayer = compDefinition.deformLayer
        guideLayer = compDefinition.guideLayer
        eyeScaleId = "eyeScale"
        eyeGuide, eyeScaleGuide = guideLayer.findGuides("eye", eyeScaleId)
        eyeScaleLocalMtx = eyeScaleGuide.worldMatrix
        self._eyeScale = self._calculateEyeScale(
            zapi.TransformationMatrix(eyeScaleLocalMtx).scale(zapi.kWorldSpace)
        )
        deformLayer.clearJoints()
        eyeParent = None

        if self._requiresNonUniformScale:
            eyeScale = deformLayer.createJoint(
                id=eyeScaleId,
                rotateOrder=eyeGuide.get("rotateOrder", 0),
                translate=eyeGuide.get("translate", (0, 0, 0)),
                rotate=eyeGuide.rotate,
                scale=self._eyeScale,
                parent=eyeParent,
            )
            eyeParent = eyeScale.id
        deformLayer.createJoint(
            id="eye",
            rotateOrder=eyeGuide.get("rotateOrder", 0),
            translate=eyeGuide.get("translate", (0, 0, 0)),
            rotate=eyeGuide.rotate,
            scale=self._eyeScale,
            parent=eyeParent,
        )
        if self.buildPupil:
            for guide in guideLayer.findGuides("pupil", "iris"):
                deformLayer.createJoint(
                    id=guide.id,
                    rotateOrder=guide.get("rotateOrder", 0),
                    translate=guide.get("translate", (0, 0, 0)),
                    rotate=guide.get("rotate", (0, 0, 0)),
                    scale=self._eyeScale,
                    parent=guide.parent,
                )
        for curveId in CURVE_IDS:
            curve = guideLayer.guide(curveId)
            if not curve:
                continue
            jntIds = self.guideJointIdsForCurve(curveId) + self.startEndGuideJntIds(
                curveId
            )
            for index, guideId in enumerate(jntIds):
                guide = guideLayer.guide(guideId)
                deformLayer.createJoint(
                    id=guideId,
                    rotateOrder=guide.get("rotateOrder", 0),
                    translate=guide.get("translate", (0, 0, 0)),
                    rotate=guide.rotate,
                    attributes=[{"name": "radius", "value": 0.2}],
                )

    def postSetupDeform(self, parent):
        deform = self.component.deformLayer()
        eyeJnt = deform.joint("eye")
        root = deform.rootTransform()
        controllerTag = zapi.controllerTag(root)
        # because the BS node is under the root we have to tag it as well for evaluation
        naming = self.component.namingConfiguration()
        if not controllerTag:

            controllerTag = zapi.createControllerTag(
                deform.rootTransform(), naming.resolve("object", {
                    "componentName": self.component.name(),
                    "side": self.component.side(),
                    "section": "deformLayer",
                    "type": "controllerTag"})
            )
            deform.addExtraNode(controllerTag)
        self.createOutputBSNode(deform.rootTransform(), deform, eyeJnt, controllerTag, naming)

    def _calculateEyeScale(self, scaleValue):
        scaleValue = zapi.Vector(scaleValue)
        uniform = zapi.Vector(scaleValue[0], scaleValue[0], scaleValue[0])
        guideSettingOverride = self.component.definition.guideLayer.guideSetting(
            "hasNonUniformScale"
        ).value
        if uniform.isEquivalent(scaleValue, 0.001):
            if guideSettingOverride:
                self._requiresNonUniformScale = True
            else:
                self._requiresNonUniformScale = False
            return zapi.Vector(1, 1, 1)
        self._requiresNonUniformScale = True
        return scaleValue

    def preSetupRig(self, parentNode):
        if not self.active():
            return
        rigLayerDef = self.component.definition.rigLayer
        guideLayerDef = self.component.definition.guideLayer
        settings = []
        removeSettings = []
        guides = [k.id for k in guideLayerDef.iterGuides()]

        for guideId, attrNames in _ROT_CONST_SETTINGS_MAP.items():

            try:
                guides.index(guideId)
            except ValueError:
                removeSettings.extend(attrNames)
                continue

            for name in attrNames:
                settings.append(
                    api.AttributeDefinition(
                        name=name,
                        Type=zapi.attrtypes.kMFnUnitAttributeAngle,
                        value=0,
                        default=0,
                        channelBox=False,
                        keyable=True,
                    )
                )
        rigLayerDef.deleteSettings("constants", removeSettings)
        rigLayerDef.addSettings("constants", settings)
        settings = self._generateAnimAttributes()
        insertIndex = (
            rigLayerDef.settingIndex(
                api.constants.CONTROL_PANEL_TYPE, EYE_CTRL_VIS_NAME
            )
            - 1
        )
        rigLayerDef.insertSettings(
            api.constants.CONTROL_PANEL_TYPE, insertIndex, settings
        )
        rigLayerDef.insertSetting(
            api.constants.CONTROL_PANEL_TYPE,
            rigLayerDef.settingIndex(
                api.constants.CONTROL_PANEL_TYPE, "showCurveTemplate"
            ),
            api.AttributeDefinition(
                name=PUPIL_VIS_NAME,
                value=False,
                default=False,
                keyable=False,
                channelBox=True,
                Type=zapi.attrtypes.kMFnNumericBoolean,
            ),
        )

    def setupRig(self, parentNode):
        if not self.active():
            return

        compDefinition = self.component.definition
        rigLayer = self.component.rigLayer()
        controlPanel = self.component.controlPanel()
        inputLayer = self.component.inputLayer()
        deformLayer = self.component.deformLayer()
        guideLayerDef = compDefinition.guideLayer
        namingConfig = self.component.namingConfiguration()
        rigLayerRoot = rigLayer.rootTransform()
        compName, compSide = self.component.name(), self.component.side()
        eyeGuide, eyeScaleGuide = guideLayerDef.findGuides("eye", "eyeScale")
        eyeScaleLocalMtx = eyeScaleGuide.worldMatrix

        self._eyeScale = self._calculateEyeScale(
            zapi.TransformationMatrix(eyeScaleLocalMtx).scale(zapi.kWorldSpace)
        )
        self._parentSpaceTransform = componentutils.createParentSpaceTransform(
            namingConfig,
            compName,
            compSide,
            rigLayerRoot,
            parentNode,
            rigLayer,
            inputLayer.inputNode("parent"),
            maintainOffset=False,
        )
        extrasHrc = zapi.createDag(
            namingConfig.resolve(
                "object",
                {
                    "componentName": compName,
                    "side": compSide,
                    "section": "extras",
                    "type": "hrc",
                },
            ),
            "transform",
            parent=rigLayerRoot,
        )
        boundTRsHrc = zapi.createDag(
            namingConfig.resolve(
                "object",
                {
                    "componentName": compName,
                    "side": compSide,
                    "section": "outTrs",
                    "type": "hrc",
                },
            ),
            "transform",
            parent=self._parentSpaceTransform,
        )

        primaryHrc = self._createMainControls(
            rigLayer, namingConfig, guideLayerDef, compName, compSide
        )
        eyeCtrl = self._ctrls["eye"]
        eyeMain = self._ctrls["eyeMain"]
        eyeTargetCtrl = self._ctrls["eyeTarget"]

        eyeQuaternionOutput = self._createEyeQuaternionNetwork(
            rigLayer,
            namingConfig,
            eyeCtrl,
            eyeTargetCtrl,
            eyeGuide,
            eyeMain=eyeMain,
            eyeJnt=deformLayer.joint("eye"),
            eyeScaleJnt=deformLayer.joint("eyeScale"),
        )

        eyeMatrix = eyeGuide.transformationMatrix(scale=False)

        constantsNode = rigLayer.settingNode("constants")
        expressionString = ""

        startEndIds = self.startEndGuideCtrlIds(INNER_UPR_CURVE_ID)
        if guideLayerDef.guide(INNER_UPR_CURVE_ID):
            _, outputBlinkNode = self._differentiatorExtraNode(deformLayer)
            innerLidBuilder = LidCurveBuilder(
                self.component,
                self,
                uprCurveId=INNER_UPR_CURVE_ID,
                lwrCurveId=INNER_LWR_CURVE_ID,
                startEndIds=["innerStart", "innerEnd"],
                hrcs={
                    "extraHrc": extrasHrc,
                    "ctrlHrc": primaryHrc,
                },
                eyeQuaternionOutput=eyeQuaternionOutput,
                eyeTransform=eyeMatrix,
                controls=self._ctrls,
            )
            innerLidBuilder.visibilityAttrName = INNER_SECONDARY_CTRL_VIS_NAME
            innerLidBuilder.primaryAttrVisibilityName = INNER_CTRL_VIS_NAME
            innerLidBuilder.boundTRsHrc = boundTRsHrc
            innerLidBuilder.createStartEnd = len(startEndIds) != 0
            innerLidBuilder.totalBlinkAttrs = (
                outputBlinkNode.attribute("uprBlinkUpDwn"),
                outputBlinkNode.attribute("lwrBlinkUpDwn"),
            )
            innerLidBuilder.buildRig()

            expressionString += innerLidBuilder.expression
            for curveId, curveNode in innerLidBuilder.outputCurves.items():
                rigLayer.addTaggedNode(curveNode, curveId)

        if guideLayerDef.guideSetting("hasOuterCtrls").value and guideLayerDef.guide(
            OUTER_UPR_CURVE_ID
        ):
            ids = self.startEndGuideCtrlIds(OUTER_UPR_CURVE_ID)
            outerLidBuilder = LidCurveBuilder(
                self.component,
                self,
                uprCurveId=OUTER_UPR_CURVE_ID,
                lwrCurveId=OUTER_LWR_CURVE_ID,
                startEndIds=["outerStart", "outerEnd"],
                hrcs={
                    "extraHrc": extrasHrc,
                    "ctrlHrc": primaryHrc,
                },
                eyeQuaternionOutput=eyeQuaternionOutput,
                eyeTransform=eyeMatrix,
                controls=self._ctrls,
            )
            outerLidBuilder.visibilityAttrName = OUTER_SECONDARY_CTRL_VIS_NAME
            outerLidBuilder.primaryAttrVisibilityName = OUTER_CTRL_VIS_NAME
            outerLidBuilder.createStartEnd = len(ids) != 0
            outerLidBuilder.prefix = "outer"
            outerLidBuilder.boundTRsHrc = boundTRsHrc
            outerLidBuilder.visibilityAttrName = OUTER_SECONDARY_CTRL_VIS_NAME
            outerLidBuilder.primaryInnerCtrlIds = [
                self.guidePrimaryCtrlIdForCurve(INNER_UPR_CURVE_ID),
                self.guidePrimaryCtrlIdForCurve(INNER_LWR_CURVE_ID),
            ]

            outerLidBuilder.buildRig()
            expressionString += outerLidBuilder.expression
            for curveId, curveNode in outerLidBuilder.outputCurves.items():
                rigLayer.addTaggedNode(curveNode, curveId)
        if expressionString:
            expression = str(_PROCS_MEL_EXPR)
            expression += self._addExpressionControlSettings(
                constantsNode, controlPanel
            )
            expression += "\n" + _INPUTS_MEL_EXPR.format(
                controlAnimSettings=controlPanel.fullPathName(),
                quaternionInput=eyeQuaternionOutput.fullPathName(),
            )
            expression += expressionString
            exprName = namingConfig.resolve(
                "object",
                {
                    "componentName": compName,
                    "side": compSide,
                    "section": "eyeLocalRot",
                    "type": "expression",
                },
            )

            expr = cmds.expression(
                name=exprName, alwaysEvaluate=False, string=expression
            )
            rigLayer.addExtraNodes([zapi.nodeByName(expr), extrasHrc, boundTRsHrc])
        self.setControlNaming()

    def _addExpressionControlSettings(self, constantsNode, controlPanel):
        # adds attributes from constants and control panel to the expression str
        constantsName = constantsNode.name()
        guideLayerDef = self.component.definition.guideLayer
        guides = [i.id for i in guideLayerDef.iterGuides()]
        expression = ""
        visited = set()
        for guideId, attrNames in _ROT_CONST_SETTINGS_MAP.items():

            try:
                guides.index(guideId)
            except ValueError:
                continue
            for name in attrNames:
                if name in visited:
                    continue
                expression += "${name} = {panelSettings}.{name};\n".format(
                    name=name, panelSettings=constantsName
                )
        panelName = controlPanel.name()

        for curveId in CURVE_IDS:
            try:
                guides.index(curveId)
            except ValueError:
                continue
            for guideId in self.guideCtrlIdsForCurve(curveId):
                try:
                    guides.index(guideId)
                except ValueError:
                    continue
                paramName = self.blinkRatioParamName(guideId)
                expression += "${name} = {panelSettings}.{name};\n".format(
                    name=paramName, panelSettings=panelName
                )
        return expression

    def postSetupRig(self, parentNode):
        if not self.active():
            return
        eyeGuideDef = self.component.definition.guideLayer.guide("eye")

        primaryAxisIndex = mayamath.primaryAxisIndexFromVector(
            eyeGuideDef.attribute(api.constants.AUTOALIGNAIMVECTOR_ATTR).value
        )

        attrs = (
            zapi.localScaleAttrs
            + zapi.localTranslateAttrs
            + [zapi.localRotateAttrs[primaryAxisIndex], "visibility"]
        )
        eyeCtrl, eyeMain, pupil, iris = self.component.rigLayer().findControls(
            "eye", "eyeMain", "pupil", "iris"
        )
        controlPanel = self.component.controlPanel()
        controlPanel.attribute(EYE_CTRL_VIS_NAME).connect(eyeCtrl.visibility)
        controlPanel.attribute(CTRL_VIS_NAME).connect(eyeMain.visibility)
        if pupil is not None:
            controlPanel.attribute(PUPIL_VIS_NAME).connect(pupil.visibility)
            pupilHideAttrs = (
                zapi.localTranslateAttrs + zapi.localRotateAttrs + ["visibility"]
            )
            for ctrl in (pupil, iris):
                ctrl.setLockStateOnAttributes(pupilHideAttrs, True)
                ctrl.showHideAttributes(pupilHideAttrs, False)
        eyeCtrl.setLockStateOnAttributes(attrs, True)
        eyeCtrl.showHideAttributes(attrs, False)

    def _createEyeQuaternionNetwork(
        self,
        rigLayer,
        namingConfig,
        eyeCtrl,
        eyeTargetCtrl,
        eyeGuideDef,
        eyeMain,
        eyeJnt,
        eyeScaleJnt=None,
    ):
        eyeSrt = eyeCtrl.srt()
        aim = mayamath.AXIS_VECTOR_BY_IDX[
            mayamath.primaryAxisIndexFromVector(
                eyeGuideDef.attribute(api.constants.AUTOALIGNAIMVECTOR_ATTR).value
            )
        ]
        up = mayamath.AXIS_VECTOR_BY_IDX[
            mayamath.primaryAxisIndexFromVector(
                eyeGuideDef.attribute(api.constants.AUTOALIGNUPVECTOR_ATTR).value
            )
        ]
        # todo: switch to aimMatrix
        aimConst, aimUtils = zapi.buildConstraint(
            eyeSrt,
            drivers={"targets": (("", eyeTargetCtrl),)},
            constraintType="aim",
            maintainOffset=True,
            aimVector=list(list(aim)),
            upVector=list(list(up)),
        )
        drivenJnt = eyeJnt if eyeScaleJnt is None else eyeScaleJnt
        driver = eyeCtrl if eyeScaleJnt is None else eyeMain
        _, constUtils = zapi.buildConstraint(
            drivenJnt,
            drivers={"targets": (("", driver),)},
            constraintType="parent",
            maintainOffset=True,
            # decompose=True,
        )
        _, constUtils = zapi.buildConstraint(
            drivenJnt,
            drivers={"targets": (("", driver),)},
            constraintType="scale",
            maintainOffset=True,
        )

        eyeCtrl.resetTransformToOffsetParent()
        composeRot = zapi.createDG(
            namingConfig.resolve(
                "object",
                {
                    "componentName": self.component.name(),
                    "side": self.component.side(),
                    "section": "eyeRotOffset",
                    "type": "composeMatrix",
                },
            ),
            "composeMatrix",
        )
        additiveRot = zapi.createDG(
            namingConfig.resolve(
                "object",
                {
                    "componentName": self.component.name(),
                    "side": self.component.side(),
                    "section": "eyeRotaddOffset",
                    "type": "plusMinusAverage",
                },
            ),
            "plusMinusAverage",
        )
        controlPanel = self.component.controlPanel()
        controlPanel.attribute("rotOffsetX").connect(composeRot.inputRotateX)
        controlPanel.attribute("rotOffsetY").connect(composeRot.inputRotateY)
        controlPanel.attribute("rotOffsetZ").connect(composeRot.inputRotateZ)
        eyeCtrl.attribute("rotate").connect(additiveRot.input3D[0])
        controlPanel.attribute("rotOffsetX").connect(additiveRot.input3D[1][0])
        controlPanel.attribute("rotOffsetY").connect(additiveRot.input3D[1][1])
        controlPanel.attribute("rotOffsetZ").connect(additiveRot.input3D[1][2])
        if eyeScaleJnt is not None:
            additiveRot.attribute("output3D").connect(eyeJnt.attribute("rotate"))
        scaleValue = zapi.TransformationMatrix(
            eyeCtrl.offsetParentMatrix.value()
        ).scale(zapi.kWorldSpace)
        composeRot.inputScale.set(scaleValue)
        composeRot.outputMatrix.connect(eyeCtrl.offsetParentMatrix)

        # sum the local rotations from the eyeCtrl and parent(rotation comes from aimConstraint)
        # then convert to quaternion and use that for our expression input
        eyeSumQuat = zapi.createDG(
            namingConfig.resolve(
                "object",
                {
                    "componentName": self.component.name(),
                    "side": self.component.side(),
                    "section": "eyeLocalRot",
                    "type": "eulerToQuat",
                },
            ),
            "eulerToQuat",
        )

        eyeRotationSum = zapi.createPlusMinusAverage3D(
            namingConfig.resolve(
                "object",
                {
                    "componentName": self.component.name(),
                    "side": self.component.side(),
                    "section": "eyeLocalRot",
                    "type": "plusMinusAverage",
                },
            ),
            inputs=(eyeSrt.attribute("rotate"), eyeCtrl.attribute("rotate")),
        )

        eyeRotationSum.output3Dx.connect(eyeSumQuat.inputRotateX)
        eyeRotationSum.output3Dy.connect(eyeSumQuat.inputRotateY)
        eyeRotationSum.output3Dz.connect(eyeSumQuat.inputRotateZ)
        rigLayer.addExtraNodes(
            [eyeSumQuat, eyeRotationSum, composeRot, additiveRot]
            + aimUtils
            + constUtils
        )
        return eyeSumQuat

    def setControlNaming(self):
        compName, compSide = self.component.name(), self.component.side()
        namingConfig = self.component.namingConfiguration()
        for ctrlId, ctrl in self._ctrls.items():
            ctrl.rename(
                namingConfig.resolve(
                    "controlName",
                    {
                        "componentName": compName,
                        "side": compSide,
                        "id": ctrlId,
                        "type": "control",
                    },
                )
            )

    def _createMainControls(
        self, rigLayer, namingConfig, guideLayerDef, compName, compSide
    ):
        """

        :param rigLayer:
        :type rigLayer: :class:`api.HiveRigLayer`
        :param namingConfig:
        :type namingConfig:
        :param guideLayerDef:
        :type guideLayerDef:
        :param compName:
        :type compName:
        :param compSide:
        :type compSide:
        :return:
        :rtype:
        """
        scaleValues = (
            [i * EYE_SCALE_SCALE_MULTIPLIER for i in self._eyeScale],
            (1, 1, 1),
            (1, 1, 1),
            (1, 1, 1),
            (1, 1, 1),
        )
        ctrlIds = ("eyeMain", "eye", "eyeTarget", "pupil", "iris")
        eyeMain, eye, eyeTarget, pupil, iris = guideLayerDef.findGuides(*ctrlIds)
        eyeRot = mayamath.lookAt(
            zapi.Vector(eye.translate),
            zapi.Vector(eyeMain.translate),
            mayamath.ZAXIS_VECTOR,
            mayamath.YAXIS_VECTOR,
            constrainAxis=zapi.Vector(0, 1, 1),
        )
        srts = [
            [],
            [
                {
                    "name": namingConfig.resolve(
                        "object",
                        {
                            "componentName": compName,
                            "side": compSide,
                            "section": "eye",
                            "type": "srt",
                        },
                    ),
                    "id": "eye",
                }
            ],
            [],
            [],
            [],
        ]
        parents = (
            self._parentSpaceTransform,
            "eyeMain",
            self._parentSpaceTransform,
            "eye",
            "pupil",
        )
        for index, (scaleValue, guide) in enumerate(
            zip(scaleValues, (eyeMain, eye, eyeTarget, pupil, iris))
        ):
            if guide is None:
                continue
            ctrl = rigLayer.createControl(
                id=guide.id,
                translate=guide.translate,
                rotate=guide.rotate if guide.id != "eye" else eyeRot,
                scale=scaleValue,
                parent=parents[index],
                rotateOrder=guide.rotateOrder,
                shape=guide.shape,
                shapeTransform=guide.shapeTransform,
                selectionChildHighlighting=self.component.configuration.selectionChildHighlighting,
                srts=srts[index],
            )
            self._ctrls[guide.id] = ctrl
            srt = ctrl.srt()
            if srt:
                srt.resetTransformToOffsetParent()
            else:
                ctrl.resetTransformToOffsetParent()

        primaryCtrlGrp = zapi.createDag(
            namingConfig.resolve(
                "layerHrc",
                {
                    "componentName": compName,
                    "side": compSide,
                    "layerType": "ctrls",
                    "type": "hrc",
                },
            ),
            "transform",
            parent=self._ctrls["eyeMain"],
        )
        deformLayer = self.component.deformLayer()
        if self.buildPupil:
            for ctrl in (self._ctrls["pupil"], self._ctrls["iris"]):
                jnt = deformLayer.joint(ctrl.id())
                if not jnt:
                    continue
                _, scaleUtils = zapi.buildConstraint(
                    jnt,
                    drivers={"targets": (("", ctrl),)},
                    constraintType="scale",
                    maintainOffset=True,
                )
                rigLayer.addExtraNodes(scaleUtils)

        return primaryCtrlGrp

    def _differentiatorExtraNode(self, layer):
        extraAttr = layer.addAttribute(
            META_EXTRA_ATTR, Type=zapi.attrtypes.kMFnMessageAttribute, isFalse=True
        )
        return extraAttr, extraAttr.sourceNode()

    def createOutputBSNode(self, parent, layer, eyeJnt, parentTag, naming):
        namingConfig = self.component.namingConfiguration()
        compName, compSide = self.component.name(), self.component.side()
        attr, valueOutput = self._differentiatorExtraNode(layer)
        if valueOutput is None:
            # create space locator which contains attributes for blink outputs
            valueOutput = zapi.createDag(
                namingConfig.resolve(
                    "object",
                    {
                        "componentName": compName,
                        "side": compSide,
                        "section": "differentiatorBS",
                        "type": "transform",
                    },
                ),
                "locator",
            )
            n = zapi.createControllerTag(
                valueOutput, name=naming.resolve("object", {
                    "componentName": self.component.name(),
                    "side": self.component.side(),
                    "section": "differentiatorBS",
                    "type": "controllerTag"}),
                parent=parentTag
            )
            layer.addExtraNode(n)

        valueOutput.setParent(parent)
        _, utils = zapi.buildConstraint(
            valueOutput,
            drivers={"targets": (("", eyeJnt),)},
            constraintType="matrix",
        )
        layer.addExtraNodes(utils + [valueOutput])
        valueOutput.message.connect(attr)
        for attrName in (
            "uprBlinkUpDwn",
            "lwrBlinkUpDwn",
        ):
            valueOutput.addAttribute(attrName, channelBox=True)
        attrs = zapi.localTransformAttrs + ["visibility"]
        valueOutput.showHideAttributes(attrs, False)
        valueOutput.setLockStateOnAttributes(attrs, True)
        container = self.component.container()
        container.publishNode(valueOutput)


class LidCurveBuilder(object):
    """
    Builds the control rig for the upr and lwr curves of an eye lid.

    :param component: The component object.
    :type component: :class:`zoo.libs.hive.base.component.Component`
    :param subsystem: The subsystem object.
    :type subsystem: :class:`EyeLidsSubsystem`
    :param uprCurveId: The ID of the upper curve.
    :type uprCurveId: string
    :param lwrCurveId: The ID of the lower curve.
    :type lwrCurveId: string
    :param hrcs: Extras hierarchy.
    :type hrcs: dict[str, :class:`zapi.DagNode`]
    """

    def __init__(
        self,
        component,
        subsystem,
        uprCurveId,
        lwrCurveId,
        startEndIds,
        hrcs,
        eyeQuaternionOutput,
        eyeTransform,
        controls,
    ):
        self.component = component
        self.subsystem = subsystem
        self.uprCurveId = uprCurveId
        self.lwrCurveId = lwrCurveId
        self.controls = controls  # type: dict[str, api.ControlNode]
        self.guideLayer = self.component.guideLayer()
        self.definition = self.component.definition
        self.guideLayerDef = self.definition.guideLayer
        self.rigLayer = self.component.rigLayer()
        self.outputCurves = {}  # type: dict[str, zapi.DagNode]
        self.controlJoints = {}  # type: dict[str, api.Joint]
        self.compName, self.compSide = self.component.name(), self.component.side()
        self.namingConfig = self.component.namingConfiguration()
        self.startId, self.endId = startEndIds if startEndIds else [None, None]
        self.extrasHrc = hrcs["extraHrc"]
        self.ctrlHrc = hrcs["ctrlHrc"]
        self.eyeQuaternionOutput = eyeQuaternionOutput
        self.invertUpVector = (True, False)
        self.expression = ""
        self.eyeTransform = eyeTransform
        self._ctrlCount = 5
        # caches distances between upr and lwr curve ctrls
        self._distances = {}
        self.createStartEnd = True
        self.prefix = "inner"
        self.constantsNode = self.rigLayer.settingNode("constants")
        # todo: refactor bind to curve to output directly to joint not a transform.
        self.boundTRsHrc = None
        self.curveVisAttrName = "showCurveTemplate"
        self.primaryAttrVisibilityName = INNER_SECONDARY_CTRL_VIS_NAME
        self.visibilityAttrName = INNER_SECONDARY_CTRL_VIS_NAME
        self.totalBlinkAttrs = []

    def buildRig(self):
        # generate the lid curves based on the guides
        self._generateCurves()
        self._generateDistances()
        self._createPrimaryControls()
        self._createMacroControls()
        self._createStartEndControls()

        # normally not required because of post running setControlName on the component
        # but mel expression requires unique shortNames
        self.setControlNaming()
        self.createExpression()
        self.bindJointsToCurve()
        self.postBuild()

    def setControlNaming(self):
        compName, compSide = self.component.name(), self.component.side()
        namingConfig = self.component.namingConfiguration()
        for ctrlId, ctrl in self.controls.items():
            ctrl.rename(
                namingConfig.resolve(
                    "controlName",
                    {
                        "componentName": compName,
                        "side": compSide,
                        "id": ctrlId,
                        "type": "control",
                    },
                )
            )

    def postBuild(self):
        guideIds = (
            self.subsystem.guideCtrlIdsForCurve(self.uprCurveId)
            + self.subsystem.guideCtrlIdsForCurve(self.lwrCurveId)
            + self.subsystem.startEndGuideCtrlIds(self.uprCurveId)
        )
        macroCtrls = self.rigLayer.findControls(*guideIds)
        attrs = zapi.localScaleAttrs + zapi.localRotateAttrs + ["visibility"]

        primaryCtrlIds = [
            self.subsystem.guidePrimaryCtrlIdForCurve(self.uprCurveId),
            self.subsystem.guidePrimaryCtrlIdForCurve(self.lwrCurveId),
        ]
        primaryCtrls = self.rigLayer.findControls(*primaryCtrlIds)

        controlPanel = self.component.controlPanel()
        curveVisAttr = controlPanel.attribute(self.curveVisAttrName)
        for curve in self.outputCurves.values():
            curveVisAttr.connect(curve.attribute("visibility"))
        # now connect visibility attributes
        macroVisAttr = controlPanel.attribute(self.visibilityAttrName)
        primaryVisAttr = controlPanel.attribute(self.primaryAttrVisibilityName)
        for ctrl in macroCtrls:
            macroVisAttr.connect(ctrl.attribute("visibility"))
            ctrl.setLockStateOnAttributes(attrs, True)
            ctrl.showHideAttributes(attrs, False)
        attrs = zapi.localScaleAttrs + [
            zapi.localRotateAttrs[0],
            zapi.localRotateAttrs[1],
            "visibility",
        ]
        for ctrl in primaryCtrls:
            primaryVisAttr.connect(ctrl.attribute("visibility"))
            ctrl.setLockStateOnAttributes(attrs, True)
            ctrl.showHideAttributes(attrs, False)

    def _createPrimaryControls(self):
        """
        Creates primary controls for the upper and lower curve based on guide information.
        """
        # Iterate through each curve to create primary controls
        for index, curveId in enumerate((self.uprCurveId, self.lwrCurveId)):
            # Get the ID of the primary guide control for the current curve
            primaryGuideId = self.subsystem.guidePrimaryCtrlIdForCurve(curveId)
            # Retrieve the guide information for the primary guide control
            primaryGuide = self.guideLayerDef.guide(primaryGuideId)
            upVector = primaryGuide.attribute(
                api.constants.AUTOALIGNUPVECTOR_ATTR
            ).value
            # Calculate the distance between the top and bottom points of the guide
            topBotDistance = self._distances[primaryGuideId]
            scale = [topBotDistance, topBotDistance, topBotDistance]
            if self.invertUpVector[index]:
                scale[mayamath.primaryAxisIndexFromVector(upVector)] *= -1.0
            isMirroredScaled = primaryGuide.attribute(
                api.constants.MIRROR_SCALED_ATTR
            ).value
            if isMirroredScaled:
                index, _ = mayamath.perpendicularAxisFromAlignVectors(
                    primaryGuide.attribute(api.constants.AUTOALIGNAIMVECTOR_ATTR).value,
                    upVector,
                )
                scale[index] *= -1.0

            # Create the control based on the guide information
            ctrl = self.rigLayer.createControl(
                id=primaryGuideId,
                translate=primaryGuide.translate,
                rotate=primaryGuide.rotate,
                scale=scale,
                parent=self.ctrlHrc,
                rotateOrder=primaryGuide.rotateOrder,
                shape=primaryGuide.shape,
                selectionChildHighlighting=self.component.configuration.selectionChildHighlighting,
            )
            # Reset the transform of the control to its offset parent
            ctrl.resetTransformToOffsetParent()
            # Store the created control in the controls dictionary
            self.controls[primaryGuide.id] = ctrl

    def _createMacroControls(self):
        for index, curveId in enumerate((self.uprCurveId, self.lwrCurveId)):
            self._createMacroControlsForCurveId(curveId, self.invertUpVector[index])

    def _createMacroControlsForCurveId(self, curveId, invertUpVector=False):
        for guideId in self.subsystem.guideCtrlIdsForCurve(curveId):
            guide = self.guideLayerDef.guide(guideId)
            topBotDistance = self._distances[guideId]
            scale = [topBotDistance, topBotDistance, topBotDistance]
            upVector = guide.attribute(api.constants.AUTOALIGNUPVECTOR_ATTR).value
            if invertUpVector:
                scale[mayamath.primaryAxisIndexFromVector(upVector)] *= -1.0

            isMirroredScaled = guide.attribute(api.constants.MIRROR_SCALED_ATTR).value
            if isMirroredScaled:
                index, _ = mayamath.perpendicularAxisFromAlignVectors(
                    guide.attribute(api.constants.AUTOALIGNAIMVECTOR_ATTR).value,
                    upVector,
                )
                scale[index] *= -1.0
            kwargs = dict(
                id=guide.id,
                translate=guide.translate,
                rotate=guide.rotate,
                scale=scale,
                parent=self.ctrlHrc,
                rotateOrder=guide.rotateOrder,
                shape=guide.shape,
                selectionChildHighlighting=self.component.configuration.selectionChildHighlighting,
            )
            kwargs["srts"] = _addBlinkSrtsToControl(
                self.namingConfig, self.compName, self.compSide, guideId
            )
            ctrl = self.rigLayer.createControl(**kwargs)
            jntName = self.namingConfig.resolve(
                "object",
                {
                    "componentName": self.compName,
                    "side": self.compSide,
                    "section": guide.id + "CrvSkin",
                    "type": "joint",
                },
            )
            curveJnt = zapi.createDag(jntName, "joint", parent=ctrl)
            curveJnt.setVisible(False)
            self.controlJoints[guide.id] = curveJnt
            self.controls[guide.id] = ctrl

    def _createStartEndControls(self):

        rigLayer = self.component.rigLayer()
        namingConfig = self.namingConfig
        compName, compSide = self.component.name(), self.component.side()
        jntParent = self.controls["eyeMain"]
        for index, guideId in enumerate((self.startId, self.endId)):
            guideDef = self.guideLayerDef.guide(guideId)
            if self.createStartEnd:
                isMirroredScaled = guideDef.attribute(
                    api.constants.MIRROR_SCALED_ATTR
                ).value
                scale = [1.0, 1.0, 1.0]
                if isMirroredScaled:
                    index, _ = mayamath.perpendicularAxisFromAlignVectors(
                        guideDef.attribute(api.constants.AUTOALIGNAIMVECTOR_ATTR).value,
                        guideDef.attribute(api.constants.AUTOALIGNUPVECTOR_ATTR).value,
                    )
                    scale[index] *= -1.0
                kwargs = dict(
                    id=guideDef.id,
                    translate=guideDef.translate,
                    rotate=guideDef.rotate,
                    scale=scale,
                    parent=self.ctrlHrc,
                    rotateOrder=guideDef.rotateOrder,
                    shape=guideDef.shape,
                    selectionChildHighlighting=self.component.configuration.selectionChildHighlighting,
                )
                ctrl = rigLayer.createControl(**kwargs)
                ctrl.resetTransformToOffsetParent()
                self.controls[guideId] = ctrl
                jntParent = ctrl
            jntName = namingConfig.resolve(
                "object",
                {
                    "componentName": compName,
                    "side": compSide,
                    "section": guideId + "CrvSkin",
                    "type": "joint",
                },
            )
            curveJnt = zapi.createDag(jntName, "joint", parent=jntParent)
            curveJnt.setVisible(False)
            self.controlJoints[guideId] = curveJnt

    def createExpression(self):
        uprCurve, lwrCurve = (
            self.outputCurves[self.uprCurveId],
            self.outputCurves[self.lwrCurveId],
        )
        eyeDef, eyeScaleGuide = self.guideLayerDef.findGuides("eye", "eyeScale")
        eyeAim = eyeDef.attribute(api.constants.AUTOALIGNAIMVECTOR_ATTR).value
        eyeUp = eyeDef.attribute(api.constants.AUTOALIGNUPVECTOR_ATTR).value
        _eyeScale = self.subsystem._calculateEyeScale(
            zapi.TransformationMatrix(eyeScaleGuide.worldMatrix).scale(zapi.kWorldSpace)
        )[mayamath.primaryAxisIndexFromVector(eyeAim)]
        eyeIsMirrored = mayamath.isVectorNegative(
            eyeAim
        )  # todo: predictably determine if component is a mirrored comp
        eyePosition = self.eyeTransform.translation(zapi.kWorldSpace)
        uprCurveShape = uprCurve.shapes()[0]
        lwrCurveShape = lwrCurve.shapes()[0]

        uprPositions = uprCurveShape.cvPositions(zapi.kWorldSpace)
        lwrPositions = lwrCurveShape.cvPositions(zapi.kWorldSpace)

        uprPrimaryCtrl = self.controls[
            self.subsystem.guidePrimaryCtrlIdForCurve(self.uprCurveId)
        ]
        lwrPrimaryCtrl = self.controls[
            self.subsystem.guidePrimaryCtrlIdForCurve(self.lwrCurveId)
        ]

        eyeAimIndex = mayamath.primaryAxisIndexFromVector(eyeAim)
        eyeUpIndex = mayamath.primaryAxisIndexFromVector(eyeUp)
        # compute eyeMatrix which all eye lid controls will be based on.
        # this give better rotations for the blink
        eyeMatrix = _computeEyeMatrix(
            uprPrimaryCtrl.translation(zapi.kWorldSpace),
            lwrPrimaryCtrl.translation(zapi.kWorldSpace),
            eyePosition,
            eyeAim,
            eyeUp,
        )
        uprPrimaryLidExprVar = "${}".format(self.uprCurveId + "Translate")
        lwrPrimaryLidExprVar = "${}".format(self.lwrCurveId + "Translate")
        innerUprPrimaryLid = "${}".format(INNER_UPR_CURVE_ID + "Translate")
        innerLwrPrimaryLid = "${}".format(INNER_LWR_CURVE_ID + "Translate")

        startPosition, endPosition = uprPositions[0], uprPositions[-1]
        startEyeVec = eyePosition - zapi.Vector(startPosition)
        endEyeVec = eyePosition - zapi.Vector(endPosition)
        startEndAngle = startEyeVec.angle(endEyeVec)
        # used for defining the worldUp direction position

        centerPositions = []
        cache = []
        for index, (uprPos, lwrPos) in enumerate(
            zip(uprPositions[1:-1], lwrPositions[1:-1])
        ):
            uprPos = zapi.Vector(uprPos)
            lwrPos = zapi.Vector(lwrPos)
            centerPositions.append(
                _createRotationPoint(
                    eyeMatrix, eyePosition, eyeAimIndex, eyeUpIndex, uprPos
                )
            )
            rotPos = centerPositions[index]
            maxAngle = (rotPos - uprPos).angle(rotPos - lwrPos)

            cache.append(
                {
                    "uprPos": uprPos,
                    "lwrPos": lwrPos,
                    "rotPos": rotPos,
                    "maxAngle": maxAngle,
                    "uprCtrlId": self.subsystem.guideCtrlIdForCurve(
                        self.uprCurveId, index
                    ),
                    "lwrCtrlId": self.subsystem.guideCtrlIdForCurve(
                        self.lwrCurveId, index
                    ),
                }
            )

        self.expression = "\n" + _LID_MEL_EXPR.format(
            primaryCtrlTranslateVar=uprPrimaryLidExprVar,
            lidPrimaryCtrlX=uprPrimaryCtrl.attribute("translateX").name(),
            lidPrimaryCtrlY=uprPrimaryCtrl.attribute("translateY").name(),
            lidPrimaryCtrlZ=uprPrimaryCtrl.attribute("translateZ").name(),
        )
        self.expression += "\n" + _LID_MEL_EXPR.format(
            primaryCtrlTranslateVar=lwrPrimaryLidExprVar,
            lidPrimaryCtrlX=lwrPrimaryCtrl.attribute("translateX").name(),
            lidPrimaryCtrlY=lwrPrimaryCtrl.attribute("translateY").name(),
            lidPrimaryCtrlZ=lwrPrimaryCtrl.attribute("translateZ").name(),
        )
        if self.totalBlinkAttrs:
            self.expression += "\n" + _LID_BLINK_OUT_ATTRS_MEL_EXPR.format(
                blinkVar="$uprBlinkIn",
                blinkRatioVar="$blinkRatio",
                startPrimaryCtrlTranslateVar=innerUprPrimaryLid,
                endPrimaryCtrlTranslateVar=innerLwrPrimaryLid,
                outputAttrName=self.totalBlinkAttrs[0],
            )
            self.expression += "\n" + _LID_BLINK_OUT_ATTRS_MEL_EXPR.format(
                blinkVar="$lwrBlinkIn",
                blinkRatioVar="$blinkRatio",
                startPrimaryCtrlTranslateVar=innerLwrPrimaryLid,
                endPrimaryCtrlTranslateVar=innerUprPrimaryLid,
                outputAttrName=self.totalBlinkAttrs[1],
            )
        firstAim, lastAim = centerPositions[0], centerPositions[-1]
        for index in range(len(cache)):
            data = cache[index]
            uprPos, lwrPos = data["uprPos"], data["lwrPos"]  # zapi.Vector(uprPos)
            rotPos, maxAngle = data["rotPos"], data["maxAngle"]
            uprCtrlId, lwrCtrlId = data["uprCtrlId"], data["lwrCtrlId"]

            uprCtrlGui, lwrCtrlGui = self.component.definition.guideLayer.findGuides(
                uprCtrlId, lwrCtrlId
            )
            uprCtrl = self.controls[uprCtrlId]
            lwrCtrl = self.controls[lwrCtrlId]

            rotationConstAttrs = _ROT_CONST_SETTINGS_MAP[uprCtrlId]
            self.constantsNode.attribute(rotationConstAttrs[0]).set(maxAngle)
            self.constantsNode.attribute(rotationConstAttrs[1]).set(startEndAngle)
            isStartEndTangent = index in (0, len(uprPositions) - 3)
            uprOutputUpDownAttr, uprOutputLRAttr = self._createMacroControlOffsets(
                primaryControl=uprPrimaryCtrl,
                control=uprCtrl,
                guide=uprCtrlGui,
                eyeMatrix=eyeMatrix,
                parentPosition=rotPos,
                aimPos=zapi.Vector(uprPos),
                worldUpPos=lastAim if index != len(centerPositions) - 1 else firstAim,
                connectPrimaryRotation=(False if isStartEndTangent else True),
                invertWorldUp=False if index != len(centerPositions) - 1 else True,
                eyeIsMirrored=eyeIsMirrored,
            )
            lwrOutputUpDownAttr, lwrOutputLRAttr = self._createMacroControlOffsets(
                primaryControl=lwrPrimaryCtrl,
                control=lwrCtrl,
                guide=lwrCtrlGui,
                eyeMatrix=eyeMatrix,
                parentPosition=rotPos,
                aimPos=zapi.Vector(lwrPos),
                worldUpPos=lastAim if index != len(centerPositions) - 1 else firstAim,
                connectPrimaryRotation=(False if isStartEndTangent else True),
                invertWorldUp=False if (index != len(centerPositions) - 1) else True,
                eyeIsMirrored=eyeIsMirrored,
            )
            self.expression += self._appendCurveCtrlExpression(
                startPrimaryLidVarName=uprPrimaryLidExprVar,
                endPrimaryLidVarName=lwrPrimaryLidExprVar,
                innerPrimaryLidVarName=innerUprPrimaryLid,
                ctrlId=uprCtrlId,
                outputUpDownAttr=uprOutputUpDownAttr,
                outputLRAttr=uprOutputLRAttr,
                rotationConstAttrs=rotationConstAttrs,
                writeLR=not isStartEndTangent,
                isMirrored=eyeIsMirrored,
            )
            self.expression += self._appendCurveCtrlExpression(
                startPrimaryLidVarName=lwrPrimaryLidExprVar,
                endPrimaryLidVarName=uprPrimaryLidExprVar,
                innerPrimaryLidVarName=innerLwrPrimaryLid,
                ctrlId=lwrCtrlId,
                outputUpDownAttr=lwrOutputUpDownAttr,
                outputLRAttr=lwrOutputLRAttr,
                rotationConstAttrs=rotationConstAttrs,
                writeLR=not isStartEndTangent,
                isMirrored=eyeIsMirrored,
            )

    def _createMacroControlOffsets(
        self,
        primaryControl,
        control,
        guide,
        eyeMatrix,
        parentPosition,
        aimPos,
        worldUpPos,
        connectPrimaryRotation=True,
        invertWorldUp=False,
        eyeIsMirrored=False,
    ):
        # compute aim matrix based on the rotation point this will be used as the initial rotation
        # offset
        parentMatrix = zapi.TransformationMatrix(eyeMatrix)
        parentMatrix.setTranslation(parentPosition, zapi.kWorldSpace)
        worldUp = parentPosition - worldUpPos
        aimVector = guide.attribute(api.constants.AUTOALIGNAIMVECTOR_ATTR).value
        upVector = guide.attribute(api.constants.AUTOALIGNUPVECTOR_ATTR).value
        perp, _ = mayamath.perpendicularAxisFromAlignVectors(aimVector, upVector)
        upVec = mayamath.AXIS_VECTOR_BY_IDX[perp]
        rotation = mayamath.lookAt(
            parentPosition,
            zapi.Vector(aimPos),
            aimVector,
            upVec * (1.0 if eyeIsMirrored else -1.0),
            worldUpVector=worldUp * -1.0 if invertWorldUp else worldUp,
        )
        parentMatrix.setRotation(rotation)

        return _createMacroOffsetNetwork(
            control,
            rootMatrix=parentMatrix,
            eyeMatrix=eyeMatrix,
            centerControl=primaryControl,
            primaryControl=primaryControl,
            aimVector=aimVector,
            upVector=upVector,
            connectPrimaryRotation=connectPrimaryRotation,
        )

    def _appendCurveCtrlExpression(
        self,
        startPrimaryLidVarName,
        endPrimaryLidVarName,
        innerPrimaryLidVarName,
        ctrlId,
        outputUpDownAttr,
        outputLRAttr,
        rotationConstAttrs,
        writeLR=True,
        isMirrored=False,
    ):
        quatMultiplier = 1.0 if "Upr" in ctrlId else -1.0
        if not writeLR:
            quatMultiplier = 0.0
        ctrlRatioAttrName = self.subsystem.blinkRatioParamName(ctrlId)
        startPrimaryCtrlTranslateVar = startPrimaryLidVarName + ".y"
        if self.prefix == "outer":
            startPrimaryCtrlTranslateVar = "({} + ({}.y * ${}))".format(
                startPrimaryCtrlTranslateVar, innerPrimaryLidVarName, ctrlRatioAttrName
            )
            lrPrimaryCtrlTranslateVar = "{}.x+{}.x".format(
                startPrimaryLidVarName, innerPrimaryLidVarName
            )
        else:
            startPrimaryCtrlTranslateVar = "{} * ${}".format(
                startPrimaryCtrlTranslateVar, ctrlRatioAttrName
            )
            lrPrimaryCtrlTranslateVar = "{}.x".format(startPrimaryLidVarName)
        upDownKwargs = {
            "startPrimaryCtrlTranslateVar": startPrimaryCtrlTranslateVar,
            "endPrimaryCtrlTranslateVar": "{}.y".format(endPrimaryLidVarName),
            "maxUpDownRotationVar": "${}".format(rotationConstAttrs[0]),
            "upDownRotOutVar": "${}".format("{}UpDownRotOut".format(ctrlId)),
            "upDownRotOutMultiplierVar": "" if "Upr" in ctrlId else "-",
            "outputUpDownAttr": outputUpDownAttr.name(),
            "upDownRotQuatMultiplier": quatMultiplier,
            "blinkRatioVar": "${} * ${}".format(
                ("blinkRatio" if "Upr" in ctrlId else "blinkRatioLwr"),
                ctrlRatioAttrName,
            ),
            "functionName": "zooCalculateLwrEyeRotationUpDown",
            "blinkVar": "${}".format("uprBlinkIn" if "Upr" in ctrlId else "lwrBlinkIn"),
            "fleshyUpDownVar": "${}{}".format(
                self.prefix, "FleshyUprUpDown" if "Upr" in ctrlId else "FleshyLwrUpDown"
            ),
        }
        lrKwargs = {
            "maxLRRotationVar": "${}".format(rotationConstAttrs[1]),
            "fleshyLRVar": "${}{}".format(
                self.prefix, "FleshyUprLR" if "Upr" in ctrlId else "FleshyLwrLR"
            ),
            "primaryCtrlTranslateVar": lrPrimaryCtrlTranslateVar,
            "outputLRAttr": outputLRAttr.name(),
            "LRRotOutVar": "${}".format("{}LRRotOut".format(ctrlId)),
            "lrMultiplier": "-1.0" if isMirrored else "1.0",
        }
        expr = "\n" + _COMPUTE_MEL_EXPR.format(**upDownKwargs)
        if writeLR:
            expr += "\n" + _COMPUTE_LR_EXPR.format(**lrKwargs)
        return expr

    def _generateDistances(self):
        # query distances between guides against opposite curves this will be used to determine
        # local scale of controls to ensure 0-1 animator translation is top to bottom

        curveGuidesA = self.subsystem.guideCtrlIdsForCurve(self.uprCurveId)
        curveGuidesB = self.subsystem.guideCtrlIdsForCurve(self.lwrCurveId)
        primaryGuideIdA = self.subsystem.guidePrimaryCtrlIdForCurve(self.uprCurveId)
        primaryGuideIdB = self.subsystem.guidePrimaryCtrlIdForCurve(self.lwrCurveId)
        for index, (guideA, guideB) in enumerate(zip(curveGuidesA, curveGuidesB)):
            guideA, guideB = self.guideLayerDef.findGuides(guideA, guideB)
            distance = (guideA.translate - guideB.translate).length()
            self._distances[guideA.id] = distance
            self._distances[guideB.id] = distance
            if index == 1:
                self._distances[primaryGuideIdA] = distance
                self._distances[primaryGuideIdB] = distance

    def _generateCurves(self):
        """
        Generates lid curves based on the guides.
        """
        for curveId in self.uprCurveId, self.lwrCurveId:
            # Retrieve shape data from the curve guide definition
            curveGuideDef = self.guideLayerDef.guide(curveId)
            shapeData = curveGuideDef.shape
            for shapeName, shape in shapeData.items():
                shape["overrideEnabled"] = False
            # Create a curve node based on the shape data and set its parent
            curve = zapi.nodeByObject(
                curves.createCurveShape(None, shapeData, space=zapi.kObjectSpace)[0]
            )
            curve.setParent(self.extrasHrc)

            # Rename the curve node according to the naming convention
            curve.rename(
                self.namingConfig.resolve(
                    "object",
                    {
                        "componentName": self.compName,
                        "side": self.compSide,
                        "section": curveId,
                        "type": "nurbsCurve",
                    },
                )
            )
            curve.template.set(1)
            # Store the created curve in the outputCurves dictionary
            self.outputCurves[curveId] = curve

    def bindJointsToCurve(self):
        mainCtrlScaleDecomp = zapi.createDG(
            self.controls["eyeMain"].name() + "_aimTrsWorldScale", "decomposeMatrix"
        )
        self.controls["eyeMain"].worldMatrixPlug().connect(
            mainCtrlScaleDecomp.inputMatrix
        )
        deformLayer = self.component.deformLayer()

        for curveId, curve in self.outputCurves.items():
            lidIds = self.subsystem.guideCtrlIdsForCurve(curveId) + [
                self.startId,
                self.endId,
            ]
            bindJntIds = self.subsystem.guideJointIdsForCurve(curveId)
            joints = [self.controlJoints[i].fullPathName() for i in lidIds]
            cmds.skinCluster(curve.fullPathName(), joints, tsb=True)
            jnts = deformLayer.findJoints(*bindJntIds)

            for index, (jntId, jnt) in enumerate(zip(bindJntIds, jnts)):
                paramName = self.subsystem.guideJntParamPosSettingName(curveId, index)
                paramValue = self.guideLayerDef.guideSetting(paramName).value
                guideDef = self.guideLayerDef.guide(jntId)
                aimVector = guideDef.attribute(
                    api.constants.AUTOALIGNAIMVECTOR_ATTR
                ).value
                upVector = guideDef.attribute(
                    api.constants.AUTOALIGNUPVECTOR_ATTR
                ).value
                bindAimToCurve(
                    jntId,
                    curve.shapes()[0],
                    paramValue,
                    self.boundTRsHrc,  # temp
                    jnts[index],
                    self.rigLayer,
                    scaleDriver=self.controls["eyeMain"],
                    worldUpObject=self.controls["eye"],
                    scaleComposeNode=mainCtrlScaleDecomp,
                    aimVector=aimVector,
                    upVector=upVector,
                )
        if not self.createStartEnd:
            return
        jntIds = self.subsystem.startEndGuideJntIds(self.uprCurveId)

        jnts = deformLayer.findJoints(*jntIds)
        for jnt, guideId in zip(jnts, (self.startId, self.endId)):
            ctrlJnt = self.controlJoints[guideId]
            const, utils = zapi.buildConstraint(
                jnt,
                drivers={"targets": (("", ctrlJnt),)},
                constraintType="matrix",
                maintainOffset=True,
                decompose=True,
            )
            self.rigLayer.addExtraNodes(utils)


def _createMacroOffsetNetwork(
    control,
    rootMatrix,
    eyeMatrix,
    centerControl,
    primaryControl,
    aimVector,
    upVector,
    connectPrimaryRotation=True,
):
    control.setParent(None, useSrt=False)
    root = control.srt(1)
    fleshLROffset = control.srt()
    primaryRotOffset = control.srt(2)
    perpAxis = mayamath.perpendicularAxisFromAlignVectors(aimVector, upVector)[0]
    newVector = zapi.Vector()
    newVector[perpAxis] = mayamath.primaryAxisIndexFromVector(upVector)
    fleshLROffset.setWorldMatrix(eyeMatrix)
    root.setWorldMatrix(rootMatrix)

    fleshLROffset.resetTransformToOffsetParent()
    primaryRotOffset.setWorldMatrix(centerControl.worldMatrix())
    primaryRotOffset.resetTransformToOffsetParent()
    scaleAttr = primaryControl.attribute("scaleX")
    if connectPrimaryRotation:
        primaryControl.attribute("rotate").connect(primaryRotOffset.attribute("rotate"))
        primaryControl.attribute("translateZ").connect(
            primaryRotOffset.attribute("translateZ")
        )
    scaleAttr.connect(primaryRotOffset.attribute("scaleX"))
    scaleAttr.connect(primaryRotOffset.attribute("scaleY"))
    scaleAttr.connect(primaryRotOffset.attribute("scaleZ"))

    control.setParent(primaryRotOffset, useSrt=False)
    control.resetTransformToOffsetParent()
    root.resetTransformToOffsetParent()
    return root.attribute("rotateZ"), fleshLROffset.attribute("rotateY")


def _computeEyeMatrix(uprPos, lwrPos, eyePos, aimVector, upVector):
    # compute midPosition in world space so we have an aim location
    aimPoint = ((uprPos - lwrPos) * 0.5) + lwrPos

    rot = mayamath.lookAt(
        eyePos,
        aimPoint,
        aimVector,
        upVector,
        uprPos - lwrPos,
    )
    transform = zapi.TransformationMatrix()
    transform.setTranslation(eyePos, zapi.kWorldSpace)
    transform.setRotation(rot)

    return transform.asMatrix()


def _createRotationPoint(
    eyeMatrix, eyePosition, aimVectorIndex, upVectorIndex, sourcePosition
):
    """Computes the position for the lid ctrl rotation at the center plane of the eye. This
    isn't likely to be the center of the eye but center given 2 normals from the eye matrix.

    :param eyeMatrix:
    :type eyeMatrix:
    :param eyePosition:
    :type eyePosition:
    :param aimVectorIndex:
    :type aimVectorIndex:
    :param upVectorIndex:
    :type upVectorIndex:
    :param sourcePosition:
    :type sourcePosition:
    :return:
    :rtype:
    """
    normals = mayamath.basisVectorsFromMatrix(eyeMatrix)
    plane = zapi.Plane()
    plane.setPlane(normals[aimVectorIndex], -normals[aimVectorIndex] * eyePosition)

    point = mayamath.closestPointOnPlane(sourcePosition, plane)
    plane.setPlane(normals[upVectorIndex], -normals[upVectorIndex] * eyePosition)
    return mayamath.closestPointOnPlane(point, plane)


def bindAimToCurve(
    name,
    curveShape,
    param,
    parentNode,
    outJoint,
    hiveLayer,
    scaleDriver,
    worldUpObject,
    scaleComposeNode,
    aimVector,
    upVector,
):
    outTransform = zapi.createDag(name + "_" + "aimTrs", "transform", parent=parentNode)

    motionPath = _bindAimToCurveMath(
        name,
        curveShape,
        param,
        parentNode,
        outTransform,
        hiveLayer,
        scaleDriver,
        worldUpObject,
        scaleComposeNode,
        aimVector,
        upVector,
        worldUpType=1,  # objectUp
    )
    motionPath.frontAxis.set(mayamath.primaryAxisIndexFromVector(aimVector))
    motionPath.upAxis.set(
        mayamath.perpendicularAxisFromAlignVectors(aimVector, upVector)[0]
    )
    motionPath.inverseUp.set(not mayamath.isVectorNegative(upVector))
    # todo: switch to use matrix
    const, parentUtils = zapi.buildConstraint(
        outJoint,
        drivers={"targets": (("", outTransform),)},
        constraintType="parent",
        maintainOffset=True,
    )
    const, utils = zapi.buildConstraint(
        outJoint,
        drivers={"targets": (("", outTransform),)},
        constraintType="scale",
        maintainOffset=True,
    )
    hiveLayer.addExtraNodes(utils + parentUtils)
    return motionPath, outTransform


def _bindAimToCurveMath(
    name,
    curveShape,
    param,
    parentNode,
    outNode,
    hiveLayer,
    scaleDriver,
    worldUpObject,
    scaleComposeNode,
    aimVector,
    upVector,
    worldUpType=2,
):
    worldMatrix = zapi.createDG(name + "_aimTrsComposeT", "composeMatrix")
    localOffset = zapi.createDG(name + "_aimTrsLocalOffset", "multMatrix")

    motionPath = zapi.nodeByObject(
        curves.createMotionPath(
            curve=curveShape.object(), param=0.0, name=name, fractionMode=False
        )
    )
    if isinstance(param, zapi.Plug):
        param.connect(motionPath.attribute("uValue"))
    else:
        motionPath.attribute("uValue").set(param)
    # print(name, worldUpObject, outNode)
    motionPath.worldUpType.set(worldUpType)  # object rotation up
    motionPath.follow.set(True)  # object rotation up
    motionPath.worldUpVector.set(upVector)
    scaleDriver.worldMatrixPlug().connect(scaleComposeNode.inputMatrix)
    worldUpObject.worldMatrixPlug().connect(motionPath.worldUpMatrix)
    motionPath.allCoordinates.connect(worldMatrix.inputTranslate)
    motionPath.rotate.connect(worldMatrix.inputRotate)
    scaleComposeNode.outputScale.connect(worldMatrix.inputScale)
    worldMatrix.outputMatrix.connect(localOffset.matrixIn[0])
    parentNode.worldInverseMatrixPlug().connect(localOffset.matrixIn[1])
    localOffset.matrixSum.connect(outNode.offsetParentMatrix)
    outNode.resetTransform()

    hiveLayer.addExtraNodes([motionPath, worldMatrix, localOffset, scaleComposeNode])
    return motionPath


def _addBlinkSrtsToControl(namingConfig, compName, compSide, guideId):
    srts = []
    for i in ("_FleshyLROffset", "_RootParent", "_PrimaryRotOffset"):
        srts.append(
            {
                "name": namingConfig.resolve(
                    "object",
                    {
                        "componentName": compName,
                        "side": compSide,
                        "section": guideId + i,
                        "type": "control",
                    },
                )
                + "_srt"
            }
        )
    return srts


# mel procedures for fleshy eyelids and rotation calculations
_PROCS_MEL_EXPR = """
/*Simple utility to remap one range to another*/
proc float zooRemap(float $n, float $oldMin,float $oldMax, float $newMin, float $newMax)
{
	// Avoid division by zero.
	if ($oldMin == $oldMax)
		return $oldMin;
    return(($newMax-$newMin) * ($n-$oldMin) / ($oldMax-$oldMin) + $newMin);
}
proc float zooLerp(float $current, float $goal, float $weight)
{

    //return (1.0 - $val) * $v0 + $val * $v1;
    return ($goal * $weight) + ((1.0 - $weight) * $current);
}

proc float zooCalculateLwrEyeRotationUpDown(float $eyeQuaternion,
                                        float $blinkValue,
                                        float $globalBlinkRatioValue,
                                        float $maxRot,
                                        float $fleshUpDown,
                                        float $ctrlTranslation,
                                        float $endCtrlTranslation,
                                        float $quatMultiplier)
{
    float $endPos = ($endCtrlTranslation * -1.0) + 1.0;
    // position of blink taking translation into account
    float $blend = zooLerp($ctrlTranslation, $endPos, $globalBlinkRatioValue);
    float $translation = zooLerp($ctrlTranslation, $blend, $blinkValue) * $maxRot;

    // handle flesh up - up rotation
    float $fleshyUpDownRemap = zooRemap($fleshUpDown, 0.0, 10.0, 0.0, 1.0);
    float $eyeFleshMax = ($eyeQuaternion * $quatMultiplier) * $fleshyUpDownRemap * $maxRot;
    return $translation + $eyeFleshMax;
}
proc float zooEyeLidTotalDiffUpDown(float $blinkValue,
                                    float $globalBlinkRatioValue,
                                    float $ctrlTranslation,
                                    float $endCtrlTranslation
                                    )
{
    float $endPos = ($endCtrlTranslation * -1.0) + 1.0;
    // position of blink taking translation into account
    float $blend = zooLerp($ctrlTranslation, $endPos, $globalBlinkRatioValue);
    float $translation = zooLerp($ctrlTranslation, $blend, $blinkValue);
    return $translation;
}

/*Handles left to right rotation for fleshy eyelids based on the incoming eye quaternion.y
and primary ctrl translate.x. 
If the axis needs changing then modify the incoming vectors to handle that case
ie. 
instead if 
<<{quaternionInput}.outputQuatX, {quaternionInput}.outputQuatY, {quaternionInput}.outputQuatZ>>;
something like would change the axis
<<{quaternionInput}.outputQuatZ, {quaternionInput}.outputQuatY, {quaternionInput}.outputQuatX>>;
*/
proc float zooCalculateEyeLidRotationsFlesh(vector $eyeQuaternion, 
                                    float $maxLRRot,
                                    float $fleshLR,
                                    float $translate,
                                    float $lrMultiplier
                                    )
{
    // remap fleshy input attributes to 0-1 from 0-10 
    float $fleshyLRRemap = zooRemap($fleshLR, 0.0, 10.0, 0.0, 1.0);
    // take the eye quaternion Y rotation
    float $eyeFleshLRMax = ($eyeQuaternion.y * $fleshyLRRemap)*$lrMultiplier;
    float $outTranslate = $translate * $fleshyLRRemap;
    // sum both the fleshy LR and the primary control translate X(left and right movement)
    return ($eyeFleshLRMax*$maxLRRot) + (($outTranslate * $maxLRRot));
}
"""

# input attributes for the mel expressions
_INPUTS_MEL_EXPR = """
// control panel inputs , reverse blink ratio for upr or lwr ie. 1.0-0.8 ==0.2 for the lwrlid

float $blinkRatio = 1.0 - {controlAnimSettings}.blinkRatio;
float $blinkRatioLwr = {controlAnimSettings}.blinkRatio;
float $uprBlinkIn = {controlAnimSettings}.uprBlink;
float $lwrBlinkIn = {controlAnimSettings}.lwrBlink;

// fleshy settings
float $innerFleshyUprUpDown = {controlAnimSettings}.uprInnerFleshyUpDwn;
float $innerFleshyUprLR = {controlAnimSettings}.uprInnerFleshyLR;
float $innerFleshyLwrUpDown = {controlAnimSettings}.lwrInnerFleshyUpDwn;
float $innerFleshyLwrLR = {controlAnimSettings}.lwrInnerFleshyLR;

float $outerFleshyUprUpDown = {controlAnimSettings}.uprOuterFleshyUpDwn;
float $outerFleshyUprLR = {controlAnimSettings}.uprOuterFleshyLR;
float $outerFleshyLwrUpDown = {controlAnimSettings}.lwrOuterFleshyUpDwn;
float $outerFleshyLwrLR = {controlAnimSettings}.lwrOuterFleshyLR;

// eye quaternion rotation split to x,y,z and w
vector $quatRotIn = <<{quaternionInput}.outputQuatZ, {quaternionInput}.outputQuatY, {quaternionInput}.outputQuatX>>;
"""
_LID_MEL_EXPR = """
vector {primaryCtrlTranslateVar} = <<{lidPrimaryCtrlX}, {lidPrimaryCtrlY}, {lidPrimaryCtrlZ}>>;
"""
_LID_BLINK_OUT_ATTRS_MEL_EXPR = """
{outputAttrName} = zooEyeLidTotalDiffUpDown({blinkVar},
                                    {blinkRatioVar},
                                    {startPrimaryCtrlTranslateVar},
                                    {endPrimaryCtrlTranslateVar}
                                    );
"""
# Mel expression appended for each eye lid control
_COMPUTE_MEL_EXPR = """
float {upDownRotOutVar} = {functionName}(
                         $quatRotIn.z,  //eye RotationQuaternion
                         {blinkVar}, // blink value
                         {blinkRatioVar},
                         {maxUpDownRotationVar}, // max rotation up/down
                         {fleshyUpDownVar}, //fleshy up down multiplier
                         {startPrimaryCtrlTranslateVar}, // primary control for the lid
                         {endPrimaryCtrlTranslateVar}, // primary control for the lid
                         {upDownRotQuatMultiplier}
                         );
{outputUpDownAttr} = {upDownRotOutMultiplierVar}{upDownRotOutVar};
"""
_COMPUTE_LR_EXPR = """
float {LRRotOutVar} = zooCalculateEyeLidRotationsFlesh($quatRotIn, 
                                    {maxLRRotationVar},
                                    {fleshyLRVar}, //fleshy left/right multiplier
                                    {primaryCtrlTranslateVar}, // primary control for the lid
                                    {lrMultiplier}
                                    );
{outputLRAttr} = {LRRotOutVar};
"""
