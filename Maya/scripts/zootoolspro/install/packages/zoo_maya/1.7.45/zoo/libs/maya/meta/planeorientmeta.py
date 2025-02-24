import math

from zoo.libs.maya.meta import base as meta
from zoo.libs.maya import zapi
from zoo.libs.maya.rig import align
from maya import cmds

from zoo.libs.maya.cmds.rig import controls, controlconstants
from zoo.libs.maya.cmds.objutils import shapenodes
from zoo.libs.maya.utils import mayamath
from zoo.libs.utils import output

try:
    from zoo.libs.hive import api as hiveapi
except:
    hiveapi = None

WORLD_UP_VECTOR_FOUND_MSG = "Start Node or EndNode uses a World Up Vector Guide on the component," \
                       "Please use that instead."
MISSING_RIG_WARN_MSG = "Unable to find Hive Rig from node: {}"
GRID_PLANE_COLOR = (0.073, 0.948, 1.0)


class CoPlanarMeta(meta.MetaBase):
    id = "zooPlaneOrient"
    POSITION_MODE = 0
    AXIS_ALIGNED_MODE = 1

    def metaAttributes(self):
        base = super(CoPlanarMeta, self).metaAttributes()
        base.extend([
            {"name": "zooCoPlanarRefPlane", "value": None, "Type": zapi.attrtypes.kMFnMessageAttribute},
            {"name": "zooCoPlanarStartNode", "value": None, "Type": zapi.attrtypes.kMFnMessageAttribute},
            {"name": "zooCoPlanarEndNode", "value": None, "Type": zapi.attrtypes.kMFnMessageAttribute},
            {"name": "zooCoPlanarMode", "value": 0, "Type": zapi.attrtypes.kMFnkEnumAttribute,
             "enums": ["Position", "AxisAligned"]},
            {"name": "zooCoPlanarPrimaryAxis", "value": 0, "Type": zapi.attrtypes.kMFnkEnumAttribute,
             "enums": ["X", "Y", "Z"]},
            {"name": "zooCoPlanarSecondaryAxis", "value": 2, "Type": zapi.attrtypes.kMFnkEnumAttribute,
             "enums": ["X", "Y", "Z"]},
            {"name": "zooCoPlanarNegatePrimaryAxis", "value": 0, "Type": zapi.attrtypes.kMFnNumericBoolean},
            {"name": "zooCoPlanarNegateSecondaryAxis", "value": 0, "Type": zapi.attrtypes.kMFnNumericBoolean},
            {"name": "zooCoPlanarAxisAlignedAxis", "value": 2, "Type": zapi.attrtypes.kMFnkEnumAttribute,
             "enums": ["X", "Y", "Z"]},
            {"name": "zooCoPlanarNegateAxisAlignedAxis", "value": 0, "Type": zapi.attrtypes.kMFnNumericBoolean},
            {"name": "zooCoplanarPositionSnap", "value": 0, "Type": zapi.attrtypes.kMFnNumericBoolean},
        ])
        return base

    def createReferencePlane(self, createPlane=True):
        """Creates the reference plane for the plane orient meta node.  If createPlane False, only creates up arrow.

        :param createPlane: If True creates a plane, if False creates only the up arrow control
        :type createPlane: bool
        """
        if createPlane:
            ctrl = zapi.createPolyPlane("OrientPlane_Reference_Zoo", createUVs=False, constructionHistory=False,
                                        width=100, height=100,
                                        subdivisionsWidth=10,
                                        subdivisionsHeight=10)[0]
            ctrl.setShapeColour(GRID_PLANE_COLOR, -1)
        else:  # don't create plane just transform/group
            ctrl = zapi.nodeByName(cmds.group(name="OrientPlane_Reference_Zoo", empty=True))
        # Build arrow cntrl --------------------------------
        arrowCtrl = zapi.nodeByName(createArrowControl("tempCtrlZooDelMe", 10.0))
        cmds.parent(arrowCtrl.shapes()[0].fullPathName(), ctrl.fullPathName(), shape=True, relative=True)
        cmds.delete(arrowCtrl.fullPathName())
        cmds.select(deselect=True)

        for shape in ctrl.shapes():
            shape.overrideEnabled.set(True)
            shape.overrideTexturing.set(False)
            shape.overrideShading.set(False)
            shape.overridePlayback.set(False)

        ctrl.setRotation(align.worldAxisToRotation(mayamath.ZAXIS))

        self.connectTo("zooCoPlanarRefPlane", ctrl)

    def referencePlane(self):
        return self.zooCoPlanarRefPlane.sourceNode()

    def showReferencePlane(self):
        refPlane = self.referencePlane()
        if refPlane:
            refPlane.visibility.set(True)

    def hideReferencePlane(self):
        refPlane = self.referencePlane()
        if refPlane:
            refPlane.visibility.set(False)

    def referencePlaneVisibility(self):
        refPlane = self.referencePlane()
        if refPlane:
            return refPlane.visibility.value()

    def matchRefPlaneToSel(self, position=False, rotation=False, scale=False):
        """Matches the reference plane to the first selected object.

        :param position: Match Position?
        :type position: bool
        :param rotation: Match Rotation?
        :type rotation: bool
        :param scale: Match Scale?
        :type scale: bool
        """
        refPlane = self.referencePlane()
        if not refPlane:
            return
        # cmds is undoable ---
        sel = cmds.ls(selection=True)
        if not sel:
            output.displayWarning("Nothing selected: Please select a joint/object")
            return
        cmds.matchTransform([refPlane.fullPathName(), sel[0]], pos=position, rot=rotation, scl=scale, piv=False)

    def orientRefPlaneToAxis(self, axis="X"):
        """Rotates the reference plane to the given axis.

        :param axis: "X", "Y", "Z"
        :type axis: str
        """
        refPlane = self.referencePlane()
        if not refPlane:
            return
        # cmds is undoable ---
        if axis == "X":
            cmds.setAttr("{}.rotate".format(refPlane.fullPathName()), 0, 0, -90)
        elif axis == "Y":
            cmds.setAttr("{}.rotate".format(refPlane.fullPathName()), 0, 0, 0)
        else:
            cmds.setAttr("{}.rotate".format(refPlane.fullPathName()), 90.0, 0, 0)

    def deleteReferencePlane(self):
        ref = self.referencePlane()
        if ref:
            ref.delete()

    def deleteAllReferencePlanesScene(self):
        """Deletes all reference planes in the scene, unrelated to the current meta node."""
        allReferencePlanes = cmds.ls("OrientPlane_Reference_Zoo*")
        if allReferencePlanes:
            cmds.delete(allReferencePlanes)

    def setStartNode(self, jnt, updateRefPlane=True):
        """

        :param jnt:
        :type jnt: :class:`zapi.DagNode`
        :return:
        :rtype:
        """
        self.connectTo("zooCoPlanarStartNode", jnt)
        if updateRefPlane:
            ref = self.referencePlane()
            if ref:
                cmds.xform(ref.fullPathName(), translation=jnt.translation(), worldSpace=True)

    def setEndNode(self, jnt):
        """

        :param jnt:
        :type jnt: :class:`zapi.DagNode`
        :return:
        :rtype:
        """
        self.connectTo("zooCoPlanarEndNode", jnt)

    def setStartEndNodes(self, startJnt, endJnt):
        """Sets the start and end nodes for the coplanar meta node.

        :param startJnt: The start joint, node or Hive guide
        :type startJnt: :class:`zapi.DagNode`
        :param endJnt:  The end joint, node or Hive guide
        :type endJnt: :class:`zapi.DagNode`
        """
        self.setStartNode(startJnt)
        self.setEndNode(endJnt)
        self.updateReferencePlane()

    def setStartEndNodesSel(self, message=True):
        """Sets the start and end nodes for the coplanar meta node.

        :param startJnt: The start joint, node or Hive guide
        :type startJnt: :class:`zapi.DagNode`
        :param endJnt:  The end joint, node or Hive guide
        :type endJnt: :class:`zapi.DagNode`
        """
        sel = list(zapi.selected())
        if not sel:
            if message:
                message.displayError("Please select one or two nodes to set as the start and end nodes.")
            return
        elif len(sel) == 1:
            self.setStartNode(sel[0])
        else:
            self.setStartEndNodes(sel[0], sel[-1])

    def selectReferencePlane(self):
        ref = self.referencePlane()
        if ref:
            cmds.select(ref.fullPathName())

    def startNode(self):
        return self.zooCoPlanarStartNode.sourceNode()

    def endNode(self):
        return self.zooCoPlanarEndNode.sourceNode()

    def nodes(self):
        endNode = self.endNode()
        startNode = self.startNode()
        if not endNode or not startNode:
            return []
        nodes = [endNode]

        if hiveapi is not None and hiveapi.Guide.isGuide(endNode) and hiveapi.Guide.isGuide(startNode):
            try:
                # handle case where the hive component has a worldUp vector already, todo: support updating the worldUp
                if hiveapi.componentFromNode(startNode).definition.guideLayer.guide(hiveapi.constants.WORLD_UP_VEC_ID):
                    output.displayWarning(WORLD_UP_VECTOR_FOUND_MSG)
                    return []
            # small edge case where the rig is missing or can't be detected #todo: Fix this detection error
            except hiveapi.MissingRigForNode:
                output.displayWarning(MISSING_RIG_WARN_MSG.format(startNode.name()))
                return []
            if startNode == endNode:
                nodes = [startNode]
            else:
                nodes = _resolveHiveGuideHierarchy(startNode, endNode)
        elif startNode == endNode:
            nodes = [startNode]
        else:
            for parent in endNode.iterParents():
                if parent == startNode:
                    nodes.append(startNode)
                    break
                nodes.append(parent)
        nodes.reverse()
        return nodes

    def referencePlaneExists(self):
        refPlane = self.referencePlane()
        if not refPlane:
            return False
        return True

    def validateStartEndNodes(self):
        """Returns the start and end nodes if they are valid, checks if they still exist.

        :return: Start and end nodes
        :rtype: tuple(:class:`zapi.DagNode`, :class:`zapi.DagNode`)
        """
        startNode = self.startNode()
        endNode = self.endNode()
        if not startNode and not endNode:
            return None, None
        if startNode:
            if not startNode.exists():
                startNode = None
        if endNode:
            if not endNode.exists():
                startNode = None
        return startNode, endNode

    def stringToStartNode(self, startNodeStr):
        """Converts a string name (UI short names) to start zapi node if it exists and is unique.

        :param startNodeStr: Start node as a string, can be short name for UIs
        :type startNodeStr: str
        :return: startNode as a zapi node
        :rtype: :class:`zapi.DagNode`
        """
        return self._stringToNode(startNodeStr)

    def stringToEndNode(self, endNodeStr):
        """Converts a string name (UI short names) to end zapi node if it exists and is unique.

        :param endNodeStr: Start node as a string, can be short name for UIs
        :type endNodeStr: str
        :return: startNode as a zapi node
        :rtype: :class:`zapi.DagNode`
        """
        return self._stringToNode(endNodeStr)

    def _stringToNode(self, nameStr):
        """Converts a string name (UI short names) to zapi node if it exists and is unique.

        :param nameStr: Start node as a string, can be short name for UIs
        :type nameStr: str
        :return: startNode as a zapi node
        :rtype: :class:`zapi.DagNode`
        """
        if not cmds.objExists(nameStr):
            return
        uniqueName = cmds.ls(nameStr, shortNames=True)[0]
        if "|" in uniqueName:
            return  # not unique
        endNode = zapi.nodeByName(nameStr)
        self.setEndNode(endNode)
        return endNode

    def setMode(self, mode):
        self.zooCoPlanarMode.set(mode)

    def mode(self):
        return self.zooCoPlanarMode.value()

    def setPositionSnap(self, state):
        self.zooCoplanarPositionSnap.set(state)

    def positionSnap(self):
        return self.zooCoplanarPositionSnap.value()

    def arrowPlaneNormal(self):
        refNode = self.referencePlane()
        if not refNode:
            return None
        plane = align.matrixToPlane(refNode.worldMatrix())
        return plane.normal()

    def setPrimaryAxis(self, state):
        self.zooCoPlanarPrimaryAxis.set(state)

    def setSecondaryAxis(self, state):
        self.zooCoPlanarSecondaryAxis.set(state)

    def setNegatePrimaryAxis(self, state):
        self.zooCoPlanarNegatePrimaryAxis.set(state)

    def setNegateSecondaryAxis(self, state):
        self.zooCoPlanarNegateSecondaryAxis.set(state)

    def setNegateAxisAlignedAxis(self, state):
        return self.zooCoPlanarNegateAxisAlignedAxis.set(state)

    def setAxisAligned(self, state):
        self.zooCoPlanarAxisAlignedAxis.set(state)

    def primaryAxis(self):
        return self.zooCoPlanarPrimaryAxis.value()

    def secondaryAxis(self):
        return self.zooCoPlanarSecondaryAxis.value()

    def negatePrimaryAxis(self):
        return self.zooCoPlanarNegatePrimaryAxis.value()

    def negateSecondaryAxis(self):
        return self.zooCoPlanarNegateSecondaryAxis.value()

    def axisAligned(self):
        return self.zooCoPlanarAxisAlignedAxis.value()

    def negateAxisAlignedAxis(self):
        return self.zooCoPlanarNegateAxisAlignedAxis.value()

    def updateReferencePlane(self):
        refNode = self.referencePlane()
        if not refNode:
            return
        # get mode ie. axisAligned or position based
        mode = self.mode()
        if mode == CoPlanarMeta.POSITION_MODE:
            nodes = self.nodes()
            if len(nodes) < 1:
                return
            positions = [i.translation(space=zapi.kWorldSpace) for i in nodes]
            newPlane = align.constructPlaneFromPositions(positions, nodes)
            # convert to degrees because cmds
            rotation = [math.degrees(i) for i in align.planeNormalToRotation(positions[0], newPlane).asEulerRotation()]

            cmds.xform(refNode.fullPathName(), rotation=rotation, worldSpace=True)

        elif mode == CoPlanarMeta.AXIS_ALIGNED_MODE:
            worldRotation = align.worldAxisToRotation(self.axisAligned(), invert=self.negateAxisAlignedAxis())

            # convert to degrees because cmds
            rotation = [math.degrees(i) for i in worldRotation]

            cmds.xform(refNode.fullPathName(), rotation=rotation, worldSpace=True)

        startNode = self.startNode()
        endNode = self.endNode()

        # Update position of first node as it may have moved
        if startNode:
            cmds.xform(refNode.fullPathName(), translation=self.startNode().translation(), worldSpace=True)

        # Auto set scale of the plane based on the distance * 2 of the start and end nodes
        if startNode and endNode:
            distance = (endNode.translation(zapi.kWorldSpace) - startNode.translation(zapi.kWorldSpace)).length()
            if distance > 0.001:
                refNode.setScale((distance * .025, distance * .025, distance * .025))

    def projectAndAlign(self, skipEnd=False):
        refNode = self.referencePlane()
        nodes = self.nodes()
        if not refNode or not nodes:
            return
        primaryAxis = self.primaryAxis()
        secondaryAxis = self.secondaryAxis()
        aimVector = mayamath.AXIS_VECTOR_BY_IDX[primaryAxis] * (-1 if self.negatePrimaryAxis() else 1.0)
        upVector = mayamath.AXIS_VECTOR_BY_IDX[secondaryAxis] * (-1 if self.negateSecondaryAxis() else 1.0)
        # convert the reference plane worldMatrix to a plane for projection
        plane = align.matrixToPlane(refNode.worldMatrix())
        if hiveapi is not None and hiveapi.Guide.isGuide(nodes[0]):
            hiveapi.alignGuidesToPlane(nodes, plane, aimVector, upVector,
                                       updateVectors=True,
                                       skipEnd=skipEnd)
        else:
            align.projectAndOrientNodes(nodes, plane, aimVector, upVector, skipEnd=skipEnd)


def _resolveHiveGuideHierarchy(startNode, endNode):
    nodes = [hiveapi.Guide(endNode.object())]
    for parent in endNode.iterParents():
        if not hiveapi.Guide.isGuide(parent):
            continue
        if parent == startNode:
            nodes.append(hiveapi.Guide(startNode.object()))
            break
        nodes.append(hiveapi.Guide(parent.object()))
    return nodes


def createArrowControl(ctrlName, controlScale):
    """Creates an arrow control for the plane orient up, with pivot correctly placed.

    :param ctrlName: The name of the control
    :type ctrlName: str
    :param controlScale: The size of the control
    :type controlScale: float

    :return upVGrp: The arrow group
    :rtype upVGrp: str
    :return upVArrow: The arrow ctrl
    :rtype upVArrow: str
    """
    upVArrow = controls.createControlCurve(folderpath="",
                                           ctrlName=ctrlName,
                                           curveScale=(controlScale, controlScale, controlScale),
                                           designName=controlconstants.CTRL_ARROW_THIN,
                                           addSuffix=False,
                                           shapeParent=None,
                                           rotateOffset=(90.0, 0.0, 0.0),
                                           trackScale=True,
                                           lineWidth=-1,
                                           rgbColor=GRID_PLANE_COLOR,
                                           addToUndo=True)[0]
    shapenodes.translateObjListCVs([upVArrow], [0.0, controlScale, 0.0])
    return upVArrow
