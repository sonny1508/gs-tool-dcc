"""Mirror related utilities.
"""

import math

from zoo.libs.maya import zapi
from zoo.libs.maya.api import nodes, curves, generic
from zoo.libs.maya.utils import mayamath
from zoo.libs.hive import constants
from maya.api import OpenMaya as om2


def mirrorDataForComponent(component, mirrorGuides, translate=("x",), rotate=None):
    """Given the component instance and the opposite component guides this will construct all
    relevant transformations and shape data for mirroring including the initial state of the `mirrorGuides`.

    Example return Data::

        ({
            'transform': OpenMaya.MTransformationMatrix object at 0x000001C14C163390>,
            'node': <Guide>leg_R:root_guide,
            'rotateOrder': 0,
            'aimVector': [-1.0, -0.0, -0.0],
            'upVector': [-0.0, -1.0, -0.0],
            'autoAlign': True
            'shapeNode': <ControlNode>leg_R:upr_guide_shape,
            'shape': {
                'transform': <OpenMaya.MTransformationMatrix object at 0x000001C14C194FB0>,
                'rotateOrder': 0,
                'shape': {...}
            },
         },

        {
            'shape': {
                'transform': <OpenMaya.MTransformationMatrix object at 0x000001C14C194FB0>,
                'rotateOrder': 0,
                'shape': {...}
            },
            'transform': <OpenMaya.MTransformationMatrix object at 0x000001C14C163030>,
            'rotateOrder': 0,
            'aimVector': maya.api.OpenMaya.MVector(-1, -0, -0),
            'upVector': maya.api.OpenMaya.MVector(-0, -1, -0),
            'autoAlign': True, 'node': <Guide>leg_R:upr_guide,
            'shapeNode': <ControlNode>leg_R:upr_guide_shape,
            'id': 'upr'
        }
        )


    :param component: The component which will be used as the data source during the setMirrorData op.
    :type component: :class:`zoo.libs.hive.base.component.Component`
    :param mirrorGuides: The opposite components guides which will be used for matching
    :type mirrorGuides: dict[str, :class:`zoo.libs.hive.base.hivenodes.hnodes.Guide`]
    :param translate: A list of axis to mirror on, defaults to ("x", )
    :type translate: tuple[str]
    :param rotate: The rotation Plane axis to rotate on defaults to "yz"
    :type rotate: str
    :return: Generator which yields two dicts first is the resulting mirror data, the second \
    is the data for Undo/resetting to previous state.

    :rtype: iterable(tuple[dict, dict])
    """
    rotate = rotate or "yz"
    guideLayer = component.guideLayer()
    parent = om2.MObject.kNullObj
    guideLayerDef = component.definition.guideLayer
    for guide in guideLayer.iterGuides():
        guideId = guide.id()
        oppositeGuide = mirrorGuides.get(guideId)
        if not oppositeGuide:
            continue
        mirroredState = {
            "shape": {}  # type: dict or None or str or zapi.DagNode
        }

        guideDefAttrs = guideLayerDef.guide(guideId).attributes
        # used only by the guide pivot transform
        mirrorBehavior = guide.attribute(constants.MIRROR_BEHAVIOUR_ATTR).value()
        oppositeGuideShape = oppositeGuide.shapeNode()

        attrsToCopy = []
        currentAttrs = []
        for attr in guideDefAttrs:
            val = attr.get("value")
            if val is None:
                continue
            existingAttr = guide.attribute(attr["name"])
            if existingAttr is None:
                continue
            attrsToCopy.append({"name": attr["name"], "value": existingAttr.value()})
            oppositeAttr = oppositeGuide.attribute(attr["name"])
            if oppositeAttr is not None:
                currentAttrs.append(
                    {"name": attr["name"], "value": oppositeAttr.value()}
                )

        mirroredState["alignBehaviour"] = mirrorBehavior
        mirroredState["node"] = oppositeGuide
        mirroredState["shapeNode"] = None
        mirroredState["id"] = guideId
        mirroredState["attributes"] = attrsToCopy
        mirroredState["mirrorPlane"] = rotate
        # used for recovery, i.e. undo
        currentState = {
            "transform": oppositeGuide.transformationMatrix(),
            "node": oppositeGuide,
            "rotateOrder": oppositeGuide.rotationOrder(),
            "aimVector": oppositeGuide.autoAlignAimVector.value(),
            "upVector": oppositeGuide.autoAlignUpVector.value(),
            "autoAlign": oppositeGuide.autoAlign.value(),
            "alignBehaviour": mirrorBehavior,
            "shapeNode": oppositeGuideShape,
            "attributes": currentAttrs,
            "mirrorPlane": rotate,
        }
        if oppositeGuideShape:
            _storeOppositeShapeData(currentState, mirroredState, oppositeGuideShape)
        if mirrorBehavior == mayamath.MIRROR_SCALE:
            translation, quat, scale, mat = nodes.mirrorTransform(
                guide.object(), parent, translate, rotate, mirrorBehavior
            )
            mirroredState["transform"] = zapi.TransformationMatrix(mat)
            mirroredState["rotateOrder"] = guide.rotationOrder()
            mirroredState["aimVector"] = guide.attribute(
                constants.AUTOALIGNAIMVECTOR_ATTR
            ).value()
            mirroredState["upVector"] = guide.attribute(
                constants.AUTOALIGNUPVECTOR_ATTR
            ).value()
            mirroredState["autoAlign"] = guide.autoAlign.asBool()
            shapeNode = guide.shapeNode()

            if shapeNode:
                shapeTranslation, shapeQuat, scale, mat = nodes.mirrorTransform(
                    shapeNode.object(),
                    parent,
                    translate,
                    rotate,
                    mayamath.MIRROR_BEHAVIOUR,
                )

                transform = zapi.TransformationMatrix()
                transform.setTranslation(shapeTranslation, zapi.kWorldSpace)
                transform.setRotation(shapeQuat)
                scale = nodes.axisNamesToNegativeVector(
                    translate, om2.MVector(shapeNode.scale(zapi.kObjectSpace))
                )
                transform.setScale(
                    scale, zapi.kObjectSpace
                )
                transform.reorderRotation(
                    generic.intToMTransformRotationOrder(shapeNode.rotationOrder())
                )
                mirroredState["shape"] = {
                    "transform": transform,
                    "rotateOrder": shapeNode.rotationOrder(),
                    "shape": curves.serializeCurve(
                        guide.shapeNode().object(), space=zapi.kObjectSpace
                    ),
                }
        else:

            _mirrorTransformTR(
                guide,
                guideId,
                mirroredState,
                mirrorBehavior,
                translate,
                rotate,
                parent,
            )

        yield mirroredState, currentState


def _mirrorTransformTR(
    guide,
    guideId,
    mirrorState,
    mirrorBehavior,
    translateAxis,
    rotateAxis,
    parent,
):
    """Mirrors a guide either translation or rotation+translation depending on behaviour

    :param guide:
    :type guide:
    :return:
    :rtype:
    """
    # worldUpVec requires special handling due to it needing to be invert 180 on the primary axis
    # we're also forcing mirror on here
    if guideId == "worldUpVec":
        mirrorRotations = True
    else:
        mirrorRotations = guide.attribute(constants.MIRROR_ATTR).asBool()
    autoAlignAimVector = guide.attribute(constants.AUTOALIGNAIMVECTOR_ATTR)
    autoAlignUpVector = guide.attribute(constants.AUTOALIGNUPVECTOR_ATTR)
    shapeNode = guide.shapeNode()
    aimMultiplier = -1 if mirrorBehavior == mayamath.MIRROR_BEHAVIOUR else 1
    upMultiplier = 1 if mirrorBehavior == mayamath.MIRROR_RELATIVE else -1
    newMirroredUpAimVector = zapi.Vector(autoAlignAimVector.value()) * aimMultiplier
    newMirroredUpVector = zapi.Vector(autoAlignUpVector.value()) * upMultiplier

    # compute the shape orientations but don't set the transform
    if shapeNode is not None and mirrorRotations:
        shapeTranslation, shapeQuat, scale, _ = nodes.mirrorTransform(
            shapeNode.object(),
            parent,
            translateAxis,
            rotateAxis,
            mayamath.MIRROR_BEHAVIOUR,
        )
        transform = zapi.TransformationMatrix()
        transform.setTranslation(shapeTranslation, zapi.kWorldSpace)
        transform.setRotation(shapeQuat)
        transform.setScale(shapeNode.scale(zapi.kObjectSpace), zapi.kObjectSpace)
        transform.reorderRotation(
            generic.intToMTransformRotationOrder(shapeNode.rotationOrder())
        )
        shapeData = {
            "transform": transform,
            "rotateOrder": shapeNode.rotationOrder(),
            "shape": curves.serializeCurve(shapeNode.object(), space=zapi.kObjectSpace),
        }
        mirrorState["shape"] = shapeData
    translation, quat, scale, mat = nodes.mirrorTransform(
        guide.object(), parent, translateAxis, rotateAxis, mirrorBehavior
    )
    rotation = quat if mirrorRotations else guide.rotation(zapi.kWorldSpace)
    if guideId == "worldUpVec":
        rotation = (
            zapi.Quaternion(math.pi, zapi.Vector(autoAlignAimVector.value())) * rotation
        )

    transform = zapi.TransformationMatrix()
    transform.setTranslation(translation, zapi.kWorldSpace)
    transform.setRotation(rotation)
    transform.setScale(guide.scale(zapi.kWorldSpace), zapi.kWorldSpace)
    transform.reorderRotation(
        generic.intToMTransformRotationOrder(guide.rotationOrder())
    )
    mirrorState["transform"] = transform
    mirrorState["rotateOrder"] = guide.rotationOrder()
    mirrorState["aimVector"] = newMirroredUpAimVector
    mirrorState["upVector"] = newMirroredUpVector
    mirrorState["autoAlign"] = guide.autoAlign.asBool()


def _storeOppositeShapeData(currentState, mirrorState, oppositeGuideShape):
    mirrorShape = curves.serializeCurve(
        oppositeGuideShape.object(), space=zapi.kObjectSpace
    )
    shapeTransform = zapi.TransformationMatrix()
    shapeTransform.setTranslation(
        oppositeGuideShape.translation(space=zapi.kWorldSpace), zapi.kWorldSpace
    )
    shapeTransform.setRotation(oppositeGuideShape.rotation(space=zapi.kWorldSpace))
    shapeTransform.setScale(
        oppositeGuideShape.scale(zapi.kObjectSpace), zapi.kObjectSpace
    )
    shapeTransform.reorderRotation(
        generic.intToMTransformRotationOrder(oppositeGuideShape.rotationOrder())
    )
    currentState["shape"] = {
        "transform": shapeTransform,
        "rotateOrder": oppositeGuideShape.rotationOrder(),
        "shape": mirrorShape,
    }
    mirrorState["shapeNode"] = oppositeGuideShape


def setMirrorData(guideData, mirrorCurve=True):
    """Sets all guides contained in the `guideData`.
    This function was design as a pair to :func:`mirrorDataForComponent`.

    Example GuideData::

        [{
            'shape': {
                'transform': <OpenMaya.MTransformationMatrix object at 0x000001C14C194FB0>,
                'rotateOrder': 0,
                'shape': {...}
            },
            'transform': <OpenMaya.MTransformationMatrix object at 0x000001C14C163030>,
            'rotateOrder': 0,
            'aimVector': maya.api.OpenMaya.MVector(-1, -0, -0),
            'upVector': maya.api.OpenMaya.MVector(-0, -1, -0),
            'autoAlign': True, 'node': <Guide>leg_R:upr_guide,
            'shapeNode': <ControlNode>leg_R:upr_guide_shape,
            'id': 'upr'
        }]

    :param guideData: An iterable containing scene state in the same form as :func:`mirrorDataForComponent` per \
    element return.

    :type guideData: iterable[dict]
    :param mirrorCurve: Whether or not the shape cvs should be mirrored. Default is True.
    :type mirrorCurve: bool
    """
    lockStateAttributes = []
    for guideInfo in guideData:
        if not guideInfo:
            continue
        guide = guideInfo["node"]
        for attrName in ["rotate", "translate", "scale"] + zapi.localTransformAttrs:
            attr = guide.attribute(attrName)
            state = attr.isLocked
            if state:
                attr.lock(False)
                lockStateAttributes.append(attr)
    guidesToReset = []
    for guideInfo in guideData:
        if not guideInfo:
            continue
        guide = guideInfo["node"]
        currentParent = guide.parent()

        srts = guide.iterSrts()
        children = list(
            guide.iterChildren(recursive=False, nodeTypes=(zapi.kNodeTypes.kTransform,))
        )
        for child in children:
            child.setParent(None)
        # for now just reset the guide if the offsetParentMatrix is connected.
        # todo: handle offsetParent matrix relative transform when mirroring
        if guide.offsetParentMatrix.isDestination:
            guidesToReset.append(guide)
        guide.setParent(parent=None, useSrt=False)
        guide.setRotationOrder(guideInfo["rotateOrder"])
        guide.setWorldMatrix(guideInfo["transform"].asMatrix())
        # push the attributes from original to the mirrored guides so we get custom attrs
        for attr in guideInfo.get("attributes", []):
            guideAttr = guide.attribute(attr["name"])
            if guideAttr is None:
                continue
            guideAttr.set(attr["value"])
        guide.attribute(constants.AUTOALIGNAIMVECTOR_ATTR).set(guideInfo["aimVector"])
        guide.attribute(constants.AUTOALIGNUPVECTOR_ATTR).set(guideInfo["upVector"])
        guide.attribute(constants.AUTOALIGN_ATTR).set(guideInfo["autoAlign"])
        guide.attribute(constants.MIRROR_BEHAVIOUR_ATTR).set(
            guideInfo["alignBehaviour"]
        )
        scaledAttr = guide.attribute(constants.MIRROR_SCALED_ATTR)
        if scaledAttr is not None:
            currentValue = scaledAttr.value()
            if guideInfo["alignBehaviour"] != mayamath.MIRROR_SCALE:
                scaledAttr.set(False)
            else:
                scaledAttr.set(not currentValue)
        mirrorPlaneAttr = guide.attribute(constants.MIRROR_PLANE_ATTR)
        if mirrorPlaneAttr is not None:
            mirrorPlaneAttr.set(
                mayamath.MIRROR_PLANE_INDEX_BY_NAME[guideInfo["mirrorPlane"]]
            )

        for srt in srts:
            srt.resetTransform(scale=False)
        guide.setParent(currentParent, useSrt=False)
        for child in children:
            child.setParent(guide)

    for g in guidesToReset:
        g.resetTransform(scale=False)
    # do shape nodes last due to custom guide node math may depend on child guides being set
    # first i.e. distributed twists
    for guideInfo in guideData:
        if not guideInfo:
            continue
        shapeNode = guideInfo.get("shapeNode")
        shapeData = guideInfo.get("shape")

        if shapeNode and shapeData:
            transform = shapeData["transform"]
            # handle offset parent matrix
            shapeNode.resetTransform(scale=False)
            transformScale = transform.scale(zapi.kWorldSpace)
            parentOffset = shapeNode.offsetParentMatrix.value()
            localTransform = transform.asMatrix() * parentOffset.inverse()
            tra = zapi.TransformationMatrix(localTransform)
            # apply the original scale back to the mat.
            tra.setScale(transformScale, zapi.kWorldSpace)
            shapeNode.setMatrix(tra)
            if shapeData:
                shapeNode.addShapeFromData(
                    shapeData["shape"], replace=True, maintainColors=True
                )
            if mirrorCurve:
                curves.mirrorCurveCvs(
                    shapeNode.object(), axis="xyz", space=om2.MSpace.kObject
                )

    for attr in lockStateAttributes:
        attr.lock(True)
