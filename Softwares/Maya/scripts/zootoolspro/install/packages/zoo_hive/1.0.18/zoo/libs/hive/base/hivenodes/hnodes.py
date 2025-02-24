"""
General Hive Nodes.
"""

import copy

from maya import cmds

from zoo.libs.hive import constants
from zoo.libs.hive.base.hivenodes import attrconstants
from zoo.libs.maya import zapi
from zoo.libs.maya.utils import mayamath
from zoo.libs.maya.zapi import attrtypes
from zoo.libs import shapelib
from zoo.libs.maya.api import curves
from zoo.libs.maya.api import nodes
from zoo.libs.maya.api import plugs
from zoo.libs.maya.api import scene
from zoo.libs.maya.api import constants as apiconstants
from zoo.libs.maya.meta import base as metabase
from zoo.core.util import zlogging
from zoovendor.six import string_types

logger = zlogging.getLogger(__name__)

__all__ = (
    "SettingsNode",
    "Guide",
    "ControlNode",
    "Joint",
    "Annotation",
    "InputNode",
    "OutputNode",
    "setGuidesWorldMatrix",
)


class SettingsNode(zapi.DGNode):
    """Main class to deal with arbitrary settings"""

    def id(self):
        """Returns the id attribute value.
        The Id value is usual added to Hivenodes to as a UUID within a given component.

        :return: The ID string.
        :rtype: str
        """
        idAttr = self.attribute(constants.ID_ATTR)
        if idAttr is not None:
            return idAttr.value()
        return ""

    def create(self, name, id, nodeType="network"):
        """Creates a network node to store animated attributes.

        :return: the settings node that was created
        :rtype: MObject
        """
        n = nodes.createDGNode(name, nodeType)
        self.setObject(n)
        self.addAttribute(
            constants.ID_ATTR, Type=attrtypes.kMFnDataString, value=id, locked=True
        )
        return self

    def serializeFromScene(self, *args, **kwargs):
        """Serializes the control panel attributes into a dict excluding connections.

        :rtype: dict

        """
        skip = (constants.ID_ATTR, "id")
        return [
            plugs.serializePlug(p.plug()) for p in self.iterExtraAttributes(skip=skip)
        ]


class ControlNode(zapi.DagNode):
    def id(self):
        """Returns the id attribute value.
        The Id value is usual added to Hivenodes to as a UUID within a given component.

        :return: The ID string.
        :rtype: str
        """
        idAttr = self.attribute(constants.ID_ATTR)
        if idAttr is not None:
            return idAttr.value()
        return ""

    def _attachedMetaNode(self):
        metaNodeSourcePlug = self.message.source()
        if metaNodeSourcePlug is None:
            return
        return metabase.MetaBase(metaNodeSourcePlug.node())

    def controllerTag(self):
        """Returns the attached controllerTag if any.

        :rtype: :class:`zapi.DGNode` or None
        """
        for dest in self.attribute("message").destinations():
            node = dest.node()
            if node.apiType() == zapi.kControllerTag:
                return node

    def addControllerTag(self, name, parent=None, visibilityPlug=None):
        """Creates and attaches a maya kControllerTag Node.

        :param name: The name of the newly created controller tag
        :type name: str
        :param parent: The parent control node
        :type parent: :class:`ControlNode`
        :param visibilityPlug: The visibility Mode plug to connect to
        :type visibilityPlug: :class:`om2.MPlug`
        :return: The kControllerNode as a hive DGNode
        :rtype: :class:`zapi.DGNode`
        """
        if parent is not None:
            parent = parent.controllerTag()

        return zapi.createControllerTag(
            self, name=name, parent=parent, visibilityPlug=visibilityPlug or None
        )

    def srt(self, index=0):
        """SRT (Scale-Rotate-Translate) node

        :param index:
        :type index:
        :return:
        :rtype: :class:`zapi.DagNode`
        """
        messagePlug = self.attribute("message")
        for destination in messagePlug.destinations():
            if not destination.partialName().endswith(("controlNode", "guideNode")):
                continue
            node = destination.node()
            if not metabase.isMetaNodeOfTypes(
                node, (constants.GUIDE_LAYER_TYPE, constants.RIG_LAYER_TYPE)
            ):
                continue
            hControlsElement = destination.parent()
            srtArray = hControlsElement[2]
            if index not in srtArray.getExistingArrayAttributeIndices():
                continue
            srtElement = srtArray.element(index)
            sourceNode = srtElement.sourceNode()
            if sourceNode is not None:
                return sourceNode

    def iterSrts(self):
        messagePlug = self.attribute("message")
        for destination in messagePlug.destinations():
            if not destination.partialName().endswith(("controlNode", "guideNode")):
                continue
            node = destination.node()
            if not metabase.isMetaNodeOfTypes(
                node, (constants.GUIDE_LAYER_TYPE, constants.RIG_LAYER_TYPE)
            ):
                continue
            hControlsElement = destination.parent()
            for srtElement in hControlsElement[2]:
                source = srtElement.sourceNode()
                if source is not None:
                    yield source

    def setParent(self, node, maintainOffset=True, useSrt=True):
        if useSrt:
            srt = self.srt()
            if srt is not None:
                srt.setParent(
                    node if node is not None else None, maintainOffset=maintainOffset
                )
                return
        return super(ControlNode, self).setParent(node, maintainOffset=maintainOffset)

    def create(self, **kwargs):
        """Create control with args
        kwargs is in the format of::

            {"color": (1.0, 1.0, 1.0),
              constants.ID_ATTR: "godnode",
              "name": "godnode",
              "rotate": [0.0, 0.0, 0.0], # radians
              "rotateOrder": 0,
              "shape": "godnode",
              "translate": [0.0,0.0,0.0] # or om2.MVector
            }

        :param kwargs:
        :type kwargs:
        :return:
        :rtype: :class:`ControlNode`

        """
        shape = kwargs.get("shape")
        parent = kwargs.get("parent")  # type: zapi.DagNode
        kwargs["type"] = "transform"
        kwargs["name"] = kwargs.get("name", "Control")
        kwargs["parent"] = None
        try:
            n = nodes.deserializeNode(kwargs)[0]
        except SystemError:
            logger.error(
                "Failed to deserialize node: {} from structure".format(kwargs["name"]),
                exc_info=True,
                extra={"data": kwargs},
            )
            raise
        self.setObject(n)

        with zapi.lockStateAttrContext(
            self,
            ["rotateOrder"]
            + zapi.localTransformAttrs
            + ["translate", "rotate", "scale"],
            state=False,
        ):
            self.setRotationOrder(kwargs.get("rotateOrder", zapi.kRotateOrder_XYZ))

            worldMtx = kwargs.get("worldMatrix")
            if worldMtx is None:

                self.setTranslation(
                    zapi.Vector(kwargs.get("translate") or (0, 0, 0)),
                    space=zapi.kWorldSpace,
                )
                self.setRotation(
                    kwargs.get("rotate") or (0, 0, 0, 1.0), space=zapi.kWorldSpace
                )
                self.setScale(kwargs.get("scale") or (1, 1, 1))
            else:
                self.setWorldMatrix(zapi.Matrix(worldMtx))
            if parent is not None:
                self.setParent(parent, maintainOffset=True)
            self.attribute("shear").set(zapi.Vector(0, 0, 0))
        if shape:
            if isinstance(shape, string_types):
                self.addShapeFromLib(shape, replace=True)
                colour = kwargs.get("color")
                if colour:
                    self.setShapeColour(colour, shapeIndex=-1)
            elif shape:
                self.addShapeFromData(shape, space=zapi.kWorldSpace, replace=True)
        self.addAttribute(
            constants.ID_ATTR,
            attrtypes.kMFnDataString,
            value=kwargs.get("id", kwargs["name"]),
            default="",
            locked=True,
        )
        childHighlighting = kwargs.get("selectionChildHighlighting")
        if childHighlighting is not None:
            self.attribute("selectionChildHighlighting").set(childHighlighting)
        rotateOrder = self.rotateOrder  # type: zapi.Plug
        rotateOrder.show()
        rotateOrder.setKeyable(True)
        return self

    def addShapeFromLib(self, shapeName, replace=False, maintainColors=False):
        if shapeName not in shapelib.shapeNames():
            return
        colorData = {}
        if maintainColors:
            # To maintain colors grab the first shape color data and reapply it in post
            for shape in self.iterShapes():
                colorData = nodes.getNodeColourData(shape.object())
                break
        if replace:
            self.deleteShapeNodes()
        shapes = list(
            map(
                zapi.nodeByObject,
                shapelib.loadAndCreateFromLib(shapeName, parent=self.object())[1],
            )
        )
        if maintainColors:
            for shape in shapes:
                nodes.setNodeColour(
                    shape.object(),
                    colorData.get("overrideColorRGB"),
                    outlinerColour=colorData.get("outlinerColor"),
                    useOutlinerColour=colorData.get("useOutlinerColor", False),
                )
        return self, shapes

    def addShape(
        self, shape, space=zapi.kObjectSpace, replace=False, maintainColors=False
    ):
        if isinstance(shape, dict):
            return self.addShapeFromData(
                shape, space=space, replace=replace, maintainColors=maintainColors
            )
        else:
            return self.addShapeFromLib(
                shape, replace=replace, maintainColors=maintainColors
            )

    def addShapeFromData(
        self, shapeData, space=zapi.kObjectSpace, replace=False, maintainColors=False
    ):
        colorData = {}
        if maintainColors:
            # To maintain colors grab the first shape color data and reapply it in post
            for shape in self.iterShapes():
                colorData = nodes.getNodeColourData(shape.object())
                break

        if replace:
            self.deleteShapeNodes()

        shapes = list(
            map(
                zapi.nodeByObject,
                curves.createCurveShape(self.object(), shapeData, space=space)[1],
            )
        )
        if maintainColors:
            for shape in shapes:
                nodes.setNodeColour(
                    shape.object(),
                    colorData.get("overrideColorRGB"),
                    outlinerColour=colorData.get("outlinerColor"),
                    useOutlinerColour=colorData.get("useOutlinerColor", False),
                )
        return self, shapes

    def annotation(self):
        """Returns the connected annotation node if it has one

        :rtype: Annotation
        """
        try:
            destinations = self.attribute("annotation").source()
        except (RuntimeError, AttributeError):
            return
        if not destinations:
            return
        return Annotation(destinations.node().object())

    def deleteAnnotation(self, mod=None, apply=True):
        ann = self.annotation()
        if ann is not None:
            ann.delete(mod=mod, apply=apply)

    def delete(self, mod=None, apply=True):
        controllerTag = self.controllerTag()
        if controllerTag:
            controllerTag.delete(mod=mod, apply=apply)
        return super(ControlNode, self).delete(mod=mod, apply=apply)

    def serializeFromScene(
        self,
        skipAttributes=(),
        includeConnections=True,
        includeAttributes=(),
        extraAttributesOnly=True,
        useShortNames=True,
        includeNamespace=False,
    ):
        if self._node is None:
            return {}
        baseData = super(ControlNode, self).serializeFromScene(
            skipAttributes=skipAttributes,
            includeConnections=includeConnections,
            includeAttributes=includeAttributes,
            extraAttributesOnly=extraAttributesOnly,
            useShortNames=useShortNames,
            includeNamespace=includeNamespace,
        )
        mobject = self.object()
        baseData.update(
            {
                "id": self.attribute(constants.ID_ATTR).value(),
                "name": baseData["name"].replace("_guide", ""),
                "shape": curves.serializeCurve(mobject, space=zapi.kObjectSpace),
                "hiveType": "control",
            }
        )
        return baseData


class Guide(ControlNode):
    _attrsToSkip = (
        constants.ID_ATTR,
        zapi.CONSTRAINT_ATTR_NAME,
        zapi.ZOOCONSTRAINT_TYPE_ATTR_NAME,
        zapi.ZOOCONSTRAINT_KWARGS_ATTR_NAME,
        zapi.ZOOCONSTRAINT_CONTROLLER_ATTR_NAME,
        zapi.ZOOCONSTRAINT_CONTROL_ATTR_NAME,
        zapi.ZOOCONSTRAINT_TARGETS_ATTR_NAME,
        zapi.ZOOCONSTRAINT_SPACELABEL_ATTR_NAME,
        zapi.ZOOCONSTRAINT_SPACETARGET_ATTR_NAME,
        zapi.ZOOCONSTRAINT_NODES_ATTR_NAME,
        constants.GUIDESHAPE_ATTR,
        constants.ISGUIDE_ATTR,
        constants.PIVOTSHAPE_ATTR,
        constants.PIVOTCOLOR_ATTR,
        constants.GUIDESNAP_PIVOT_ATTR,
        constants.DISPLAYAXISSHAPE_ATTR,
        constants.GUIDE_SHAPE_PRIMARY_ATTR
    )
    _defaultPivotShapeMultiplier = 0.25

    @staticmethod
    def isGuide(node):
        """Determines if the node is a guide node. To determine if a node is a guide the node must an attribute called
        'isGuide'

        :param node:
        :type node: :class:`zoo.libs.hive.zapi.hivenodes.zapi.DGNode`
        :return: True if the node is a guide
        :rtype: bool
        """
        return node.hasAttribute(constants.ISGUIDE_ATTR)

    def id(self):
        """Returns the id attribute value.
        The Id value is usual added to Hivenodes to as a UUID within a given component.

        :return: The ID string.
        :rtype: str
        """
        idAttr = self.attribute(constants.ID_ATTR)
        if idAttr is not None:
            return idAttr.value()
        return ""

    def aimToChild(self, aimVector, upVector, worldUpVector=None):
        child = None  # type: Guide or None
        for child in self.iterChildGuides(recursive=False):
            break
        # if its the leaf then set the rotation to zero, is this ideal?
        if child is None:
            currentParent = self.parent()
            srt = self.srt()
            guideParent, _ = self.guideParent()
            if guideParent is None:
                return
            shapeNode = self.shapeNode()
            if shapeNode:
                shapeTransform = shapeNode.worldMatrix()
            if srt is None:
                self.setRotation(
                    guideParent.rotation(space=zapi.kWorldSpace), space=zapi.kWorldSpace
                )
            else:
                self.setParent(None, useSrt=False)
                srt.resetTransform(scale=False)
                self.setParent(currentParent, useSrt=False)
                self.resetTransform(translate=False, rotate=True, scale=False)
            if shapeNode:
                shapeNode.setMatrix(
                    shapeTransform * shapeNode.offsetParentMatrix.value().inverse()
                )
            return
        self.aimToGuide(child, aimVector, upVector, worldUpVector)

    @zapi.lockNodeContext
    def aimToGuide(self, target, aimVector, upVector, worldUpVector=None):
        guideParent, _ = self.guideParent()
        shapeNode = self.shapeNode()
        for srt in self.iterSrts():
            children = list(
                srt.iterChildren(
                    recursive=False, nodeTypes=(zapi.kNodeTypes.kTransform,)
                )
            )
            for child in children:
                child.setParent(None)
            srt.resetTransform(scale=False)
            for child in children:
                child.setParent(srt)

        if shapeNode is not None:
            currentTransform = shapeNode.worldMatrix()
            scene.aimNodes(
                targetNode=target.object(),
                driven=[self.object()],
                aimVector=aimVector,
                upVector=upVector,
                worldUpVector=worldUpVector,
            )
            shapeNode.setMatrix(
                currentTransform * shapeNode.offsetParentMatrix.value().inverse()
            )
        else:
            scene.aimNodes(
                targetNode=target.object(),
                driven=[self.object()],
                aimVector=aimVector,
                upVector=upVector,
                worldUpVector=worldUpVector,
            )

    def shape(self):
        """Returns the serialized form of the guide shapes

        :rtype: dict
        """
        return curves.serializeCurve(self.object())

    def setShapeNode(self, shapeNode):
        existingShapeNode = self.shapeNode()
        if existingShapeNode:
            existingShapeNode.delete()
        shapeNode.addAttribute(
            constants.ID_ATTR,
            attrtypes.kMFnDataString,
            value=self.id(),
            default="",
            locked=True,
        )
        self._connectPivotToShape(shapeNode)

    def shapeNode(self):
        """Returns the control shape guide node.

        :rtype: :class:`ControlNode`
        """
        for dest in self.attribute("guideShape").destinations():
            return ControlNode(dest.node().object())

    def setShapeParent(self, parent):
        """Sets the parent of the separate shape transform node

        :param parent: the new parent node
        :type parent: :class:`zapi.DagNode`
        :rtype: bool
        """
        shape = self.shapeNode()
        if shape is not None:
            shape.setParent(parent, maintainOffset=True)
            return True
        return False

    def setParent(self, parent, shapeParent=None, useSrt=True, maintainOffset=True):
        """Sets the guide parent node

        :param parent: new parent node for the guide, can be an MObject to a transform or any hive node
        :type parent: om2.MObject or hivenode
        :param shapeParent:
        :type shapeParent: :class:`DagNode`
        :param useSrt: IF True then the srt will be parented instead of the pivot node
        :type useSrt: True
        :param maintainOffset: If True then the current world Transform will be maintained
        :type maintainOffset: bool
        :return: True if succeeded else False
        :rtype: bool
        """
        if shapeParent is not None:
            self.setShapeParent(shapeParent)

        return super(Guide, self).setParent(
            parent, maintainOffset=maintainOffset, useSrt=useSrt
        )

    def guideParent(self):
        """This iterates the parent nodes until it finds the first parent guide then returns it and the parentId.

        :rtype: tuple(:class:`Guide`, str)
        """
        for parent in self.iterParents():
            if parent.hasAttribute(constants.ISGUIDE_ATTR):
                return (
                    Guide(parent.object()),
                    parent.attribute(constants.ID_ATTR).value(),
                )
        return None, None

    def iterGuideParents(self):
        for parent in self.iterParents():
            if parent.hasAttribute(constants.ISGUIDE_ATTR):
                yield Guide(parent.object()), parent.attribute(
                    constants.ID_ATTR
                ).value()

    def isRoot(self):
        return self.guideParent()[0] is None

    def create(self, **settings):
        """Creates a pivot and shape transforms in the scene

        :param settings:
        :type settings: dict
        :return: The pivot transform node
        :rtype: om2.MObject

        """
        # combine the default and user guide settings
        data = {}
        data.update(settings)

        # compose the pivot color and settings.
        color = data.get("pivotColor", constants.DEFAULT_GUIDE_PIVOT_COLOR)
        data["color"] = color
        newShape = data.get("shape")
        requiresPivotShape = data.get("requiresPivotShape", True)
        attrs = data.get("attributes", [])
        if requiresPivotShape:
            pivotShape = (
                data.get(constants.PIVOTSHAPE_ATTR) or "sphere"
            )  # pivot shape can be empty not just None
            data["shape"] = pivotShape
            attrs.append(
                {
                    "name": constants.PIVOTSHAPE_ATTR,
                    "value": pivotShape,
                    "Type": zapi.attrtypes.kMFnDataString,
                }
            )
            attrs.append(
                {
                    "name": constants.PIVOTCOLOR_ATTR,
                    "value": color,
                    "Type": zapi.attrtypes.kMFnNumeric3Float,
                }
            )
        data["attributes"] = self._mergeUserGuideAttributes(data, attrs)

        super(Guide, self).create(**data)

        # generate the pick locator
        cvScale = self._defaultPivotShapeMultiplier
        # hack for maya vertex snap which obviously doesn't snap to cvs.
        # This nodes shape gets parented to self
        snapPivot = zapi.createDag(
            "_".join((self.name(includeNamespace=False), "pick")),
            "locator",
            parent=self,
        )
        snapPivot.message.connect(self.attribute(constants.GUIDESNAP_PIVOT_ATTR))
        if color:
            self.setShapeColour(color)
        self.scalePivotComponents(cvScale, cvScale, cvScale)
        snapPivot.attribute("localScale").set(zapi.Vector(0.001, 0.001, 0.001))
        self._trackShapes(
            list(self.iterShapes()) + list(snapPivot.iterShapes()), replace=True
        )

        axisParent, axisShapes = self.addShapeFromLib("axis")
        for shape in axisShapes:
            self.connect(constants.DISPLAYAXISSHAPE_ATTR, shape.attribute("visibility"))
        cmds.scale(4, 4, 4, [".".join((i.fullPathName(), "cv[*]")) for i in axisShapes])
        if newShape:
            shapeTransform = data.get("shapeTransform", {})
            shapeTransform["selectionChildHighlighting"] = data.get(
                "selectionChildHighlighting"
            )
            shapeTransform["id"] = data.get("id", "ZOO_RENAME")
            shapeTransform["rotateOrder"] = data.get(
                "rotateOrder", zapi.kRotateOrder_XYZ
            )
            shapeTransform["shape"] = newShape
            shapeTransform["name"] = data.get("name", "ZOO_RENAME")
            shapeTransform["color"] = settings.get("color")

            self._createShapeTransform(shapeTransform)

        return self

    def snapPivot(self):
        """Returns the locator shape node which is used for interactive viewport snapping.

        Guides contain a locator shape due to the fact that our guides are curves which
        the user can't snap to without change the snap settings. So this snapPivot is
        added for convenience.

        :rtype: :class:`zapi.DagNode`
        """
        return self.sourceNodeByName(constants.GUIDESNAP_PIVOT_ATTR)

    def scalePivotComponents(self, x, y, z):
        if not self.exists():
            return
        nurbsShapes = []
        for shape in self.shapes():
            if shape.hasFn(zapi.kNodeTypes.kLocator):
                shape.localScale.set(zapi.Vector(x, y, z))
                continue
            nurbsShapes.append(shape.fullPathName() + ".cv[*]")
        if nurbsShapes:
            cmds.scale(x, y, z, nurbsShapes)

    def scaleAxisComponents(self, x, y, z):
        if not self.exists():
            return
        shapes = [dest.node() for dest in self.displayAxisShape.destinations()]
        if shapes:
            cmds.scale(x, y, z, [".".join((i.fullPathName(), "cv[*]")) for i in shapes])

    def scaleShapeComponents(self, x, y, z):
        shape = self.shapeNode()
        if not shape:
            return
        cmds.scale(x, y, z, ".".join((shape.fullPathName(), "cv[*]")))

    def replaceShape(self, settings):
        """Replaces the shape for this guide by removing the shape nodes from the shape transform
        before creating new ones.

        :param settings:
        :type settings: dict
        :return:
        :rtype:
        """
        currentShape = self.shapeNode()
        if currentShape is not None:
            # delete the current shape nde
            self.deleteShapeTransform()
        return self._createShapeTransform(settings)

    def pivotShapes(self):
        for element in self.attribute(constants.GUIDE_SHAPE_PRIMARY_ATTR):
            source = element.sourceNode()
            if source is not None:
                yield source

    def addShape(self, shapeData):
        shapeNode = self.shapeNode()
        if not shapeNode:
            raise ValueError("shape node not attached")
        # if a base string load from the internal library else its a dict
        ctrl = ControlNode(node=shapeNode)
        if isinstance(shapeData, string_types):
            ctrl.addShapeFromLib(shapeData)
        else:
            ctrl.addShapeFromData(shapeData)
        return ctrl.object()

    def setDisplayAxisShapeVis(self, vis):
        """Set the display axis shape visibility

        :param vis:
        :type vis: bool
        :return:
        :rtype:
        """

        self.attribute(constants.DISPLAYAXISSHAPE_ATTR).set(int(vis))

    def displayAxisShapeVis(self):
        """The value of displayAxisShape visibility

        :return:
        :rtype: bool
        """
        return self.attribute(constants.DISPLAYAXISSHAPE_ATTR).value()

    def iterChildGuides(self, recursive=False):
        """Generator Function which returns the immediate child guides

        :rtype: Generator(:class:`Guide`)
        """
        return self._childGuides(self, recursive=recursive)

    def pivotShapeInfo(self):
        return curves.serializeCurve(self.object(), space=zapi.kWorldSpace)

    def serializeFromScene(
        self,
        skipAttributes=(),
        includeConnections=False,
        includeAttributes=(),
        extraAttributesOnly=True,
        useShortNames=True,
        includeNamespace=False,
    ):
        """Serializes this guide to dict.

        :rtype: dict
        """
        if not self.exists():
            return {}
        baseData = super(Guide, self).serializeFromScene(
            skipAttributes=self._attrsToSkip,
            includeConnections=includeConnections,
            includeAttributes=includeAttributes,
            extraAttributesOnly=extraAttributesOnly,
            useShortNames=useShortNames,
            includeNamespace=includeNamespace,
        )
        children = [
            child.serializeFromScene(
                self._attrsToSkip,
                includeConnections=includeConnections,
                includeAttributes=includeAttributes,
                extraAttributesOnly=extraAttributesOnly,
                useShortNames=useShortNames,
                includeNamespace=includeNamespace,
            )
            for child in self.iterChildGuides()
        ]
        shape = self.shapeNode()
        shapeTrans, shapeRot, shapeScale = [], [], []
        if shape:
            shapeTrans, shapeRot, shapeScale = shape.decompose()

        guideParent, parentId = self.guideParent()
        baseData.update(
            {
                "id": self.id(),
                "children": children,
                "srts": [
                    srt.serializeFromScene(
                        skipAttributes=self._attrsToSkip,
                        includeConnections=includeConnections,
                        includeAttributes=includeAttributes,
                        extraAttributesOnly=extraAttributesOnly,
                        useShortNames=useShortNames,
                        includeNamespace=includeNamespace,
                    )
                    for srt in self.iterSrts()
                ],
                "shape": (
                    {}
                    if not shape
                    else curves.serializeCurve(shape.object(), space=zapi.kWorldSpace)
                ),
                "pivotShape": self.attribute(constants.PIVOTSHAPE_ATTR).value(),
                "pivotColor": plugs.getPythonTypeFromPlugValue(
                    self.attribute(constants.PIVOTCOLOR_ATTR)
                ),
                "parent": parentId,
                "shapeTransform": {
                    "translate": list(shapeTrans),
                    "rotate": list(shapeRot),
                    "scale": list(shapeScale),
                },
                "hiveType": "guide",
            }
        )
        return baseData

    def deleteShapeTransform(self):
        shapeNode = self.shapeNode()
        if shapeNode is not None and shapeNode.exists():
            return shapeNode.delete()
        return False

    @zapi.lockNodeContext
    def delete(self):
        # delete the child first
        self.deleteShapeTransform()
        # delete the srts
        rootSrt = self.srt(0)

        if rootSrt:
            controllerTag = self.controllerTag()
            if controllerTag:
                controllerTag.delete()
            return rootSrt.delete()
        return super(Guide, self).delete()

    def _connectPivotToShape(self, shapeNode):
        shapePivAttr = shapeNode.addAttribute(
            constants.PIVOTNODE_ATTR, attrtypes.kMFnMessageAttribute
        )
        self.attribute(constants.GUIDESHAPE_ATTR).connect(shapePivAttr)
        self.rotateOrder.connect(shapeNode.rotateOrder)
        zapi.buildConstraint(
            shapeNode,
            {"targets": (("", self),)},
            constraintType="matrix",
            maintainOffset=True,
            trace=False,
        )

    def _createShapeTransform(self, settings):
        """Creates a new shape transform for this guide

        :param settings: {"shape": str or dict, "color":tuple(), "name":str}
        :type settings: dict
        :return:
        :rtype: :class:`control.Control`
        """
        currentShapeNode = self.shapeNode()
        if currentShapeNode:
            raise ValueError("Shape Transform node already exists")
        name = "_".join([settings["name"], "shape"])
        shapeCtrl = ControlNode()

        transformInfo = settings
        transformInfo["name"] = name
        transformInfo["parent"] = None
        transformInfo["shape"] = settings.get("shape")
        shapeCtrl.create(**transformInfo)
        self._connectPivotToShape(shapeCtrl)
        return shapeCtrl

    def _trackShapes(self, shapes, replace=False):
        attr = self.attribute(constants.GUIDE_SHAPE_PRIMARY_ATTR)
        if replace:
            modifier = zapi.dgModifier()
            for i in attr:
                i.delete(modifier=modifier, apply=False)
            modifier.doIt()

        for index, shape in enumerate(shapes):
            shape.message.connect(attr.nextAvailableDestElementPlug())

    @staticmethod
    def _mergeUserGuideAttributes(settings, userAttributes=None):
        userAttributes = userAttributes or []
        data = copy.deepcopy(attrconstants.GUIDE_ATTRS)
        data[constants.ID_ATTR]["value"] = settings.get("id", "GUIDE_RENAME")
        data[constants.DISPLAYAXISSHAPE_ATTR]["value"] = settings.get(
            constants.DISPLAYAXISSHAPE_ATTR, False
        )
        data[constants.AUTOALIGN_ATTR]["value"] = settings.get(
            constants.AUTOALIGN_ATTR, True
        )
        data[constants.MIRROR_ATTR]["value"] = settings.get(constants.MIRROR_ATTR, True)
        data[constants.MIRROR_BEHAVIOUR_ATTR]["value"] = settings.get(
            constants.MIRROR_BEHAVIOUR_ATTR, 0
        )
        data[constants.AUTOALIGNUPVECTOR_ATTR]["value"] = settings.get(
            constants.AUTOALIGNUPVECTOR_ATTR, constants.DEFAULT_UP_VECTOR
        )
        data[constants.AUTOALIGNAIMVECTOR_ATTR]["value"] = settings.get(
            constants.AUTOALIGNAIMVECTOR_ATTR, constants.DEFAULT_AIM_VECTOR
        )
        data[constants.PIVOTSHAPE_ATTR]["value"] = settings.get(
            constants.PIVOTSHAPE_ATTR, ""
        )
        data[constants.PIVOTCOLOR_ATTR]["value"] = settings.get(
            constants.PIVOTCOLOR_ATTR, (0, 0, 0)
        )

        for userAttr in userAttributes:
            name = userAttr["name"]
            if name in data:
                data[name]["value"] = userAttr.get("value")
            else:
                data[name] = userAttr

        return data.values()

    @classmethod
    def _childGuides(cls, guide, recursive=False):
        # we treat recursion different, since without it we may need to traverse multiple depths
        # to get to a child guide
        if not recursive:
            for child in guide.iterChildren(
                recursive=False, nodeTypes=(zapi.kTransform,)
            ):
                if cls.isGuide(child):
                    yield cls(child.object())
                else:
                    for child in cls._childGuides(child):
                        yield child
        else:
            for child in guide.iterChildren(
                recursive=recursive, nodeTypes=(zapi.kTransform,)
            ):
                if cls.isGuide(child):
                    yield cls(child.object())


class Joint(zapi.DagNode):
    def id(self):
        """Returns the id attribute value.
        The Id value is usual added to Hivenodes to as a UUID within a given component.

        :return: The ID string.
        :rtype: str
        """
        idAttr = self.attribute(constants.ID_ATTR)
        if idAttr is not None:
            return idAttr.value()
        return ""

    def serializeFromScene(
        self,
        skipAttributes=(),
        includeConnections=True,
        includeAttributes=(),
        extraAttributesOnly=True,
        useShortNames=True,
        includeNamespace=False,
    ):
        data = super(Joint, self).serializeFromScene(
            skipAttributes=skipAttributes,
            includeConnections=includeConnections,
            includeAttributes=includeAttributes,
            extraAttributesOnly=extraAttributesOnly,
            useShortNames=useShortNames,
            includeNamespace=includeNamespace,
        )
        data.update(
            {
                "name": self.fullPathName(partialName=True, includeNamespace=False),
                "id": self.id(),
                "hiveType": "joint",
            }
        )
        return data

    def setParent(self, parent, maintainOffset=True, mod=None, apply=True):
        rotation = self.rotation(space=zapi.kWorldSpace)
        super(Joint, self).setParent(parent, maintainOffset=True)
        if parent is None:
            return
        parentQuat = parent.rotation(zapi.kWorldSpace, asQuaternion=True)
        newRotation = rotation * parentQuat.inverse()
        self.jointOrient.set(newRotation.asEulerRotation())
        # reset the local rotations of the joint since reparenting will add rotations
        self.setRotation((0, 0, 0), zapi.kTransformSpace)
        if parent.apiType() == zapi.kJoint:
            parent.attribute("scale").connect(self.inverseScale)

    def create(self, **kwargs):
        kwargs["type"] = "joint"
        kwargs["name"] = kwargs.get("name", "joint")
        kwargs["parent"] = kwargs.get("parent", None)
        jnt, _ = nodes.deserializeNode(kwargs, parent=None, includeAttributes=True)
        self.setObject(jnt)
        rotateOrder = kwargs.get("rotateOrder", 0)
        self.setRotationOrder(rotateOrder)
        worldMat = zapi.TransformationMatrix()
        worldMat.setTranslation(
            zapi.Vector(kwargs.get("translate", zapi.Vector())), zapi.kWorldSpace
        )
        worldMat.setRotation(zapi.Quaternion(kwargs.get("rotate", zapi.Quaternion())))
        worldMat.reorderRotation(apiconstants.kRotateOrders[rotateOrder])
        self.setWorldMatrix(worldMat)

        self.setParent(kwargs["parent"], maintainOffset=True)

        # reset the local rotations of the joint since parenting will add rotations
        self.addAttribute(
            name=constants.ID_ATTR,
            Type=attrtypes.kMFnDataString,
            value=kwargs.get("id", ""),
            default="",
            keyable=False,
            channelBox=False,
            locked=True,
        )
        self.segmentScaleCompensate.set(0)
        return self

    def aimToChild(self, aimVector, upVector, useJointOrient=True):
        child = self.child(0)
        if child is None:
            self.setRotation(zapi.Quaternion())
            return
        scene.aimNodes(
            targetNode=child.object(),
            driven=[self.object()],
            aimVector=aimVector,
            upVector=upVector,
        )
        if useJointOrient:
            self.jointOrient.set(self.rotation())
            self.setRotation(zapi.Quaternion())


class Annotation(zapi.DagNode):
    _annotation_extraAttr = "zooAnnotationExtras"

    @staticmethod
    def isAnnotation(node):
        """Determines if the provided node has an annotation attached. This is simply checking whether the node
        has the annotation attribute.

        :param node: The node to check.
        :type node: :class:`zapi.DagNode`
        :rtype: bool
        """
        return node.hasAttribute("zooAnnotation")

    def id(self):
        """Returns the id attribute value.
        The Id value is usual added to Hive nodes to as a UUID within a given component.

        :return: The ID string.
        :rtype: str
        """
        idAttr = self.attribute(constants.ID_ATTR)
        if idAttr is not None:
            return idAttr.value()
        return ""

    def setParent(self, parent, maintainOffset=False, mod=None, apply=True):
        """Sets the parent of this dag node to a hive layer node

        :param parent: the new parent node
        :type parent: :class:`DagNode`
        :param maintainOffset: Whether to maintain its current position in world space.
        :type maintainOffset: bool
        :param mod: The MDagModifier to add to, if none it will create one
        :type mod: om2.MDagModifier
        :param apply: Apply the modifier immediately if true, false otherwise
        :type apply: bool
        :rtype: om2.MDagModifier
        """
        # allows us to batch the parenting based on to apply state.
        internalApply = False if mod is not None else apply
        for extraNode in self.extraNodes():
            extraNode.setParent(parent, maintainOffset, mod, internalApply)
        super(Annotation, self).setParent(parent, maintainOffset, mod, apply)

    def delete(self, mod=None, apply=True):
        for extraNode in self.attribute(self._annotation_extraAttr):
            sourceNode = extraNode.sourceNode()
            if sourceNode is not None:
                sourceNode.delete(mod=mod, apply=apply)

        super(Annotation, self).delete(mod=mod, apply=apply)

    def create(self, name, start, end, attrHolder=None, parent=None):
        shapeInfo = copy.deepcopy(curves.shapeInfo)
        shapeInfo["degree"] = 1
        splineCurveTransform, _ = zapi.nurbsCurveFromPoints(
            "annotation", [zapi.Vector(), zapi.Vector()], shapeInfo
        )
        splineCurveTransform.setParent(parent)
        splineCurveTransform.rename(name)
        # connect the start and end via decompose matrices
        startDecompose = zapi.createDG(
            name=name + "startDecompose", nodeType="decomposeMatrix"
        )
        endDecompose = zapi.createDG(
            name=name + "endDecompose", nodeType="decomposeMatrix"
        )
        start.worldMatrixPlug().connect(startDecompose.inputMatrix)
        end.worldMatrixPlug().connect(endDecompose.inputMatrix)
        for shape in splineCurveTransform.iterShapes():
            startDecompose.outputTranslate.connect(shape.controlPoints[0])
            endDecompose.outputTranslate.connect(shape.controlPoints[1])
        self.setObject(splineCurveTransform.object())

        self.addCompoundAttribute(
            "zooAnnotation",
            [
                {
                    "name": self._annotation_extraAttr,
                    "isArray": True,
                    "Type": zapi.attrtypes.kMFnMessageAttribute,
                },
                {"name": "zooAnnStart", "Type": zapi.attrtypes.kMFnMessageAttribute},
                {"name": "zooAnnEnd", "Type": zapi.attrtypes.kMFnMessageAttribute},
                {
                    "name": "zooAttrHolder",
                    "Type": zapi.attrtypes.kMFnMessageAttribute,
                    "value": None,
                },
            ],
        )
        start.message >> self.attribute("zooAnnStart")
        end.message >> self.attribute("zooAnnEnd")
        extrasAttr = self.attribute(self._annotation_extraAttr)
        startDecompose.message.connect(extrasAttr[0])
        startDecompose.message.connect(extrasAttr[1])
        attrHolder = attrHolder if attrHolder else start
        if attrHolder is not None:
            attrHolder.message >> self.attribute("zooAttrHolder")
        self.template = True
        return self

    def setStartEnd(self, startNode, endNode):
        startNode.message >> self.attribute("zooAnnStart")
        endNode.message >> self.attribute("zooAnnEnd")
        endNode.attribute("worldMatrix")[0].connect(self.offsetParentMatrix)
        for extra in self.attribute(self._annotation_extraAttr):
            sourceNode = extra.source()
            if not sourceNode:
                continue
            startNode.attribute("worldMatrix")[0].connect(
                sourceNode.node().offsetParentMatrix
            )

    def extraNodes(self):
        """

        :return:
        :rtype: :iterable[:class:`zapi.DagNode`]
        """
        extrasAttr = self.attribute(self._annotation_extraAttr)
        for extra in extrasAttr:
            sourceNode = extra.sourceNode()
            if sourceNode is not None:
                yield sourceNode

    def startNode(self):
        return self.sourceNodeByName("zooAnnStart")

    def endNode(self):
        return self.sourceNodeByName("zooAnnEnd")

    def attrHolder(self):
        return self.sourceNodeByName("zooAttrHolder")

    def serializeFromScene(self, *args, **kwargs):
        data = {
            "start": self.startNode(),
            "end": self.endNode(),
            "attrHolder": self.attrHolder(),
            "hiveType": "annotation",
        }
        return data


class InputNode(zapi.DagNode):
    _attrsToSkip = (
        constants.ID_ATTR,
        zapi.CONSTRAINT_ATTR_NAME,
        constants.ISINPUT_ATTR,
    )

    @staticmethod
    def isInput(node):
        """Determines if the node is a Input node. To determine if a node is a Input the node must an attribute called
        'isInput'

        :param node:
        :type node: :class:`zoo.libs.hive.zapi.hivenodes.zapi.DGNode`
        :return: True if the node is a guide
        :rtype: bool
        """
        return node.hasAttribute(constants.ISINPUT_ATTR)

    def inputParent(self):
        for parent in self.iterParents():
            if parent.hasAttribute(constants.ISINPUT_ATTR):
                return (
                    InputNode(parent.object()),
                    parent.attribute(constants.ID_ATTR).value(),
                )
        return None, None

    def isRoot(self):
        return self.inputParent()[0] is None

    @classmethod
    def _childInputs(cls, inputNode, recursive=False):
        # we treat recursion different, since without it we may need to traverse multiple depths
        # to get to a child Input Node
        if not recursive:
            for child in inputNode.iterChildren(
                recursive=False, nodeTypes=(zapi.kTransform,)
            ):
                if cls.isInput(child):
                    yield cls(child.object())
                else:
                    for child in cls._childInputs(child):
                        yield child
        else:
            for child in inputNode.iterChildren(
                recursive=recursive, nodeTypes=(zapi.kTransform,)
            ):
                if cls.isInput(child):
                    yield cls(child.object())

    def iterChildInputs(self, recursive=False):
        """Generator Function which returns the immediate child guides

        :rtype: Generator(:class:`InputNode`)
        """
        return self._childInputs(self, recursive=recursive)

    def id(self):
        """Returns the id attribute value.
        The Id value is usual added to Hivenodes to as a UUID within a given component.

        :return: The ID string.
        :rtype: str
        """
        idAttr = self.attribute(constants.ID_ATTR)
        if idAttr is not None:
            return idAttr.value()
        return ""

    def attachedNode(self):
        driven = self.drivenNode
        results = []
        if driven.isSource():
            return driven.destinations()
        return results

    def create(self, **kwargs):
        name = kwargs.get("name", "input")
        node = nodes.createDagNode(name, "transform", self.parent())
        self.setObject(node)
        self.setRotationOrder(kwargs.get("rotateOrder", zapi.kRotateOrder_XYZ))
        self.setTranslation(
            zapi.Vector(kwargs.get("translate", [0.0, 0.0, 0.0])),
            space=zapi.kWorldSpace,
        )
        self.setRotation(zapi.Quaternion(kwargs.get("rotate", (0.0, 0.0, 0.0, 1.0))))
        self.addAttribute(
            constants.ID_ATTR, attrtypes.kMFnDataString, value=kwargs.get("id", name)
        )
        self.addAttribute(
            constants.ISINPUT_ATTR, attrtypes.kMFnNumericBoolean, value=True
        )
        return self

    def serializeFromScene(
        self,
        skipAttributes=(),
        includeConnections=False,
        includeAttributes=(),
        extraAttributesOnly=True,
        useShortNames=True,
        includeNamespace=False,
    ):
        baseData = super(InputNode, self).serializeFromScene(
            skipAttributes=self._attrsToSkip,
            includeConnections=includeConnections,
            includeAttributes=includeAttributes,
            extraAttributesOnly=extraAttributesOnly,
            useShortNames=useShortNames,
            includeNamespace=includeNamespace,
        )
        parent, parentId = self.inputParent()
        children = [
            child.serializeFromScene(
                skipAttributes=self._attrsToSkip,
                includeConnections=includeConnections,
                includeAttributes=(),
                extraAttributesOnly=extraAttributesOnly,
                useShortNames=useShortNames,
                includeNamespace=includeNamespace,
            )
            for child in self.iterChildInputs()
        ]
        baseData["parent"] = parentId
        baseData["children"] = children
        baseData["id"] = self.id()
        return baseData


class OutputNode(zapi.DagNode):
    _attrsToSkip = (
        constants.ID_ATTR,
        zapi.CONSTRAINT_ATTR_NAME,
        constants.ISOUTPUT_ATTR,
    )

    @staticmethod
    def isOutput(node):
        """Determines if the node is an Input node. To determine if a node is an Input the node must an attribute called
        'isInput'

        :param node:
        :type node: :class:`zoo.libs.hive.zapi.hivenodes.zapi.DGNode`
        :return: True if the node is a guide
        :rtype: bool
        """
        return node.hasAttribute(constants.ISOUTPUT_ATTR)

    def id(self):
        """Returns the id attribute value.
        The Id value is usual added to Hivenodes to as a UUID within a given component.

        :return: The ID string.
        :rtype: str
        """
        idAttr = self.attribute(constants.ID_ATTR)
        if idAttr is not None:
            return idAttr.value()
        return ""

    def isRoot(self):
        return self.outputParent()[0] is None

    def outputParent(self):
        for parent in self.iterParents():
            if parent.hasAttribute(constants.ISOUTPUT_ATTR):
                return (
                    OutputNode(parent.object()),
                    parent.attribute(constants.ID_ATTR).value(),
                )
        return None, None

    @classmethod
    def _childOutputs(cls, outputNode, recursive=False):
        # we treat recursion different, since without it we may need to traverse multiple depths
        # to get to a child outputNode
        if not recursive:
            for child in outputNode.iterChildren(
                recursive=False, nodeTypes=(zapi.kTransform,)
            ):
                if cls.isOutput(child):
                    yield cls(child.object())
                else:
                    for child in cls._childOutputs(child):
                        yield child
        else:
            for child in outputNode.iterChildren(
                recursive=recursive, nodeTypes=(zapi.kTransform,)
            ):
                if cls.isOutput(child):
                    yield cls(child.object())

    def iterChildOutputs(self, recursive=False):
        """Generator Function which returns the immediate child Output nodes

        :rtype: Generator(:class:`OutputNode`)
        """
        return self._childOutputs(self, recursive=recursive)

    def create(self, **kwargs):
        name = kwargs.get("name", "output")
        node = nodes.createDagNode(name, "transform", self.parent())
        self.setObject(node)
        worldMat = kwargs.get("worldMatrix")
        if worldMat is not None:
            transMat = zapi.TransformationMatrix(zapi.Matrix(worldMat))
            transMat.setScale((1, 1, 1), zapi.kWorldSpace)
            self.setWorldMatrix(transMat.asMatrix())
        else:
            self.setTranslation(
                zapi.Vector(kwargs.get("translate", (0.0, 0.0, 0.0))),
                space=zapi.kWorldSpace,
            )
            self.setRotation(
                zapi.Quaternion(kwargs.get("rotate", (0.0, 0.0, 0.0, 1.0)))
            )
        self.setRotationOrder(kwargs.get("rotateOrder", zapi.kRotateOrder_XYZ))
        self.addAttribute(
            constants.ID_ATTR, attrtypes.kMFnDataString, value=kwargs.get("id", name)
        )
        self.addAttribute(
            constants.ISOUTPUT_ATTR, attrtypes.kMFnNumericBoolean, value=True
        )
        return self

    def serializeFromScene(
        self,
        skipAttributes=(),
        includeConnections=False,
        includeAttributes=(),
        extraAttributesOnly=True,
        useShortNames=True,
        includeNamespace=False,
    ):
        baseData = super(OutputNode, self).serializeFromScene(
            skipAttributes=self._attrsToSkip,
            includeConnections=includeConnections,
            includeAttributes=includeConnections,
            extraAttributesOnly=extraAttributesOnly,
            useShortNames=useShortNames,
            includeNamespace=includeNamespace,
        )
        parent, parentId = self.outputParent()
        children = [
            child.serializeFromScene(
                skipAttributes=self._attrsToSkip,
                includeConnections=includeConnections,
                includeAttributes=includeAttributes,
                extraAttributesOnly=extraAttributesOnly,
                useShortNames=useShortNames,
                includeNamespace=includeNamespace,
            )
            for child in self.iterChildOutputs()
        ]
        baseData["parent"] = parentId
        baseData["children"] = children
        baseData["id"] = self.id()

        return baseData


def setGuidesWorldMatrix(guides, matrices, skipLockedTransforms=True):
    """

    :param guides:
    :type guides: list[:class:`Guide`]
    :param matrices:
    :type matrices: list[:class:`zapi.Matrix`]
    :return:
    :rtype:
    """
    assert len(guides) == len(matrices), "Guides and matrices lists must be same length"
    tempCache = {}
    for guide, matrix in zip(guides, matrices):
        shapeNode = guide.shapeNode()
        shapeTransform = None
        if shapeNode:
            shapeTransform = shapeNode.worldMatrix()
        tempCache[guide] = {
            "shapeNode": shapeNode,
            "shapeTransform": shapeTransform,
        }
    for guide, matrix in zip(guides, matrices):
        cache = tempCache[guide]
        srt = guide.srt()
        shapeNode = cache["shapeNode"]
        shapeTransform = cache["shapeTransform"]
        # parent = guide.parent()
        # children = list(
        #     guide.iterChildren(recursive=False, nodeTypes=(zapi.kNodeTypes.kTransform,))
        # )
        # for child in children:
        #     child.setParent(None)
        # guide.setParent(None, useSrt=False)
        if srt:
            srt.resetTransform(scale=False)

        if not skipLockedTransforms:
            with zapi.lockStateAttrContext(guide, zapi.localTransformAttrs, False):
                cmds.xform(guide.fullPathName(), matrix=list(matrix), ws=True)
                # guide.setWorldMatrix(matrix)
                # guide.setParent(parent, useSrt=False)
        else:
            cmds.xform(guide.fullPathName(), matrix=list(matrix), ws=True)
            # guide.setWorldMatrix(matrix)
            # guide.setParent(parent, useSrt=False)

        # for child in children:
        #     child.setParent(guide)
        if shapeNode and not shapeTransform.isEquivalent(shapeNode.worldMatrix()):
            shapeNode.setMatrix(
                shapeTransform * shapeNode.offsetParentMatrix.value().inverse()
            )


def alignGuidesToPlane(
    guides, plane, aimVector, upVector, updateVectors=True, skipEnd=False
):
    """Aligns the guides along the plane.

    :param guides: The guides to align along the plane.
    :type guides: list[:class:`Guide`]
    :param plane: The plane to align the guides to.
    :type plane: :class:`zapi.Plane`
    :param aimVector: The aim vector to use for the guides.
    :type aimVector: :class:`zapi.Vector`
    :param upVector: The up vector for the guides to align along the normal. eg. Z is Up then the guide Up attribute \
    will be set to Y. This is because the plane normal is the world Up Vector.
    :type upVector: :class:`zapi.Vector`
    :param updateVectors: Whether to update the aim and up vectors of the guides.
    :type updateVectors: bool
    :param skipEnd: Whether to skip the end guide.
    :type skipEnd: bool
    """
    nodeArray = guides[:-1] if skipEnd else guides  # skip the end node
    changeMap = []
    lastIndex = len(nodeArray) - 1
    matrices = []
    planeNormal = plane.normal()
    attributeUpVector, _ = mayamath.perpendicularAxisFromAlignVectors(
        aimVector, upVector
    )
    attributeUpVector = mayamath.axisVectorByIdx(attributeUpVector)
    isUpNegative = mayamath.isVectorNegative(upVector)
    if isUpNegative:
        attributeUpVector *= -1
    # loop over the guides and find the closest point on the plane
    for index, currentNode in enumerate(nodeArray):
        translation = currentNode.translation(space=zapi.kWorldSpace)
        if index == lastIndex:
            targetNode = guides[index + 1] if skipEnd else None
            newTranslation = (
                translation
                if skipEnd
                else mayamath.closestPointOnPlane(translation, plane)
            )
        else:
            targetNode = guides[index + 1]
            # re position the node to ensure it's on the plane
            newTranslation = mayamath.closestPointOnPlane(translation, plane)

        changeMap.append((currentNode, targetNode, newTranslation))
    # now compute the rotations which is based on the new positions
    for index, (currentNode, targetNode, newTranslation) in enumerate(changeMap):
        targetTranslation = (
            changeMap[index + 1][-1] if targetNode is not None else newTranslation
        )

        # update guide vectors if requested then use for lookat
        if updateVectors:
            currentNode.attribute(constants.AUTOALIGNAIMVECTOR_ATTR).set(aimVector)
            currentNode.attribute(constants.AUTOALIGNUPVECTOR_ATTR).set(
                attributeUpVector
            )
            guideAimVector = aimVector
            guideUpVector = upVector
        else:
            guideAimVector = currentNode.attribute(
                constants.AUTOALIGNAIMVECTOR_ATTR
            ).value()
            guideUpVector = currentNode.attribute(
                constants.AUTOALIGNUPVECTOR_ATTR
            ).value()

        transform = currentNode.transformationMatrix()
        transform.setTranslation(newTranslation, zapi.kWorldSpace)
        if targetNode is not None:
            rot = mayamath.lookAt(
                newTranslation,
                targetTranslation,
                guideAimVector,
                guideUpVector,
                worldUpVector=planeNormal,
            )
            transform.setRotation(rot)
        else:
            # set the leaf to the same rotation as the previous node
            transform.setRotation(
                zapi.TransformationMatrix(matrices[-1]).rotation(asQuaternion=True)
            )
        matrices.append(transform.asMatrix())

    setGuidesWorldMatrix(guides, matrices, skipLockedTransforms=True)
