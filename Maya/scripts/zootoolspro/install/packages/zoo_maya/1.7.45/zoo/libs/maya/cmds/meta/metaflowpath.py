from maya import cmds
import maya.api.OpenMaya as om2

from zoo.libs.maya import zapi
from zoo.libs.maya.meta import base
from zoo.libs.utils import output
from zoo.libs.maya.cmds.objutils import filtertypes, curves
from zoo.libs.maya.cmds.rig import jointsflowpath, axis

XYZ_LIST = ["x", "y", "z"]


class ZooAlongAPath(base.MetaBase):
    """Class that controls the meta network node setup for the Animate Along Path (motion path rig) functionality

    Controls deleting, rebuilding the rig, querying and setting attributes.

    Attributes:

        firstJoint: The first joint in the chain
        lastJoint: The last joint in the chain
        motionPath: The motionPath node that was created
        ikHandle: The ikHandle created using motion paths
        ikEffector: The ikEffector created using motion paths
        ikCurve: The ikCurve created using motion paths
        lattice: The lattice created using motion paths
        base: The base created using motion paths

    """
    _default_attrs = [{"name": "firstJoint", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute},
                      {"name": "lastJoint", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute},
                      {"name": "path", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute},
                      {"name": "ikHandle", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute},
                      {"name": "ikEffector", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute},
                      {"name": "ikCurve", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute},
                      {"name": "lattice", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute},
                      {"name": "base", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute},
                      {"name": "motionPath", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute},

                      {"name": "frontAxis", "value": "", "Type": zapi.attrtypes.kMFnDataString},
                      {"name": "jointMatrix", "value": None, "Type": zapi.attrtypes.kMFnDataMatrix, "isArray": True},
                      ]

    def metaAttributes(self):
        """Creates the dictionary as attributes if they don't already exist"""
        defaults = super(ZooAlongAPath, self).metaAttributes()
        defaults.extend(ZooAlongAPath._default_attrs)
        return defaults

    def connectAttributes(self, firstJoint, lastJoint, path, ikHandle,
                          ikEffector, ikCurve, lattice, base, motionPath):
        """Connects the maya nodes to the meta node

        :param firstJoint: The first joint as a zapi node
        :type firstJoint: :class:`zapi.DGNode`
        :param lastJoint: The last joint as a zapi node
        :type lastJoint: :class:`zapi.DGNode`
        :param path: The motion path node as a zapi node
        :type path: :class:`zapi.DGNode`
        :param ikHandle: The ikHandle as a zapi node
        :type ikHandle: :class:`zapi.DGNode`
        :param ikEffector: The ikEffector as a zapi node
        :type ikEffector: :class:`zapi.DGNode`
        :param ikCurve: The ikCurve as a zapi node
        :type ikCurve: :class:`zapi.DGNode`
        :param lattice: The lattice as a zapi node
        :type lattice: :class:`zapi.DGNode`
        :param base: The base as a zapi node
        :type base: :class:`zapi.DGNode`
        """
        self.connectTo("firstJoint", firstJoint)
        self.connectTo("lastJoint", lastJoint)
        self.connectTo("path", path)
        self.connectTo("ikHandle", ikHandle)
        self.connectTo("ikEffector", ikEffector)
        self.connectTo("ikCurve", ikCurve)
        self.connectTo("lattice", lattice)
        self.connectTo("base", base)
        self.connectTo("motionPath", motionPath)

    def connectAttributesStr(self, firstJoint, lastJoint, path, ikHandle, ikEffector,
                             ikCurve, lattice, base, motionPath):
        """Connects the maya string names to the meta node

        :param firstJoint: The first joint as a string
        :type firstJoint: str
        :param lastJoint: The last joint as a string
        :type lastJoint: str
        :param motionPath: The curve that the motion path follows as a string
        :type motionPath: str
        :param ikHandle: The ikHandle as a string
        :type ikHandle: str
        :param ikEffector: The ikEffector as a string
        :type ikEffector: str
        :param ikCurve: The ikCurve as a string
        :type ikCurve: str
        :param lattice: The lattice as a string
        :type lattice: str
        :param base: The base as a string
        :type base: str
        """
        self.connectAttributes(zapi.nodeByName(firstJoint),
                               zapi.nodeByName(lastJoint),
                               zapi.nodeByName(path),
                               zapi.nodeByName(ikHandle),
                               zapi.nodeByName(ikEffector),
                               zapi.nodeByName(ikCurve),
                               zapi.nodeByName(lattice),
                               zapi.nodeByName(base),
                               zapi.nodeByName(motionPath))

    # ------------------
    # GETTERS & SETTERS
    # ------------------

    def getAttrConnection(self, classAttr):
        """Returns the connected node of the attribute as a zapi dag node

        :return: zapi motionPath node
        :rtype: :class:`zapi.DGNode`
        """
        return classAttr.sourceNode()

    def getAttrConnectionStr(self, classAttr):
        """Returns the connected node of the attribute as a long name

        :return: the connection to the attribute as a string
        :rtype: str
        """
        node = self.getAttrConnection(classAttr)
        if node:
            return node.fullPathName()
        return ""

    def getFirstJointStr(self):
        """Returns the controlObj as a long name

        :return: controlObj node names
        :rtype: str
        """
        return self.getAttrConnectionStr(self.firstJoint)

    def getLastJointStr(self):
        """Returns the controlObj as a long name

        :return: controlObj node names
        :rtype: str
        """
        return self.getAttrConnectionStr(self.lastJoint)

    def getPathStr(self):
        """Returns the controlObj as a long name

        :return: controlObj node names
        :rtype: str
        """
        return self.getAttrConnectionStr(self.path)

    def getMotionPathStr(self):
        """Returns the controlObj as a long name

        :return: controlObj node names
        :rtype: str
        """
        return self.getAttrConnectionStr(self.motionPath)

    def getikHandleStr(self):
        """Returns the controlObj as a long name

        :return: controlObj node names
        :rtype: str
        """
        return self.getAttrConnectionStr(self.ikHandle)

    def getikEffectorStr(self):
        """Returns the controlObj as a long name

        :return: controlObj node names
        :rtype: str
        """
        return self.getAttrConnectionStr(self.ikEffector)

    def getikCurveStr(self):
        """Returns the controlObj as a long name

        :return: controlObj node names
        :rtype: str
        """
        return self.getAttrConnectionStr(self.ikCurve)

    def getLatticeStr(self):
        """Returns the controlObj as a long name

        :return: controlObj node names
        :rtype: str
        """
        return self.getAttrConnectionStr(self.lattice)

    def getBaseStr(self):
        """Returns the controlObj as a long name

        :return: controlObj node names
        :rtype: str
        """
        return self.getAttrConnectionStr(self.base)

    def getLatticeDivision(self):
        latticeZapi = zapi.nodeByName(self.getLatticeStr())
        latticeShapeZapi = latticeZapi.shapes()[0]

        if self.frontAxis.value() == "x":
            return latticeShapeZapi.sDivisions.value()
        elif self.frontAxis.value() == "z":
            return latticeShapeZapi.uDivisions.value()
        else:
            return latticeShapeZapi.tDivisions.value()

    def getUpAxis(self):
        motionPath = self.motionPath.sourceNode()
        if motionPath:
            return motionPath.upAxis.value()
        return 0

    def getFrontAxis(self):
        motionPath = self.motionPath.sourceNode()
        if motionPath:
            return motionPath.frontAxis.value()
        return 0

    def getSliderValue(self):
        """Returns the value of the path attribute on the controller object"""
        motionPath = self.motionPath.sourceNode()
        if motionPath:
            return motionPath.uValue.value()
        return 0.0

    def setLattice(self, value):
        """Sets the lattice attribute on the controller object"""
        latticeZapi = zapi.nodeByName(self.getLatticeStr())
        latticeShapeZapi = latticeZapi.shapes()[0]

        if self.frontAxis.value() == "x":
            cmds.setAttr("{}.sDivisions".format(latticeShapeZapi), value)
        elif self.frontAxis.value() == "z":
            cmds.setAttr("{}.uDivisions".format(latticeShapeZapi), value)
        else:
            cmds.setAttr("{}.tDivisions".format(latticeShapeZapi), value)

    def setUpAxis(self, value):
        """Sets the upAxis comboBox value"""
        name = self.getMotionPathStr()
        cmds.setAttr("{}.upAxis".format(name), value)

    def setFrontAxis(self, value):
        motionPathZapi = zapi.nodeByName(self.getMotionPathStr())
        if not value == 0:
            motionPathZapi.frontAxis.set(value - 1)
            self.frontAxis.set(XYZ_LIST[motionPathZapi.frontAxis.value()])

    # ------------------
    # KEY AND SET PATH
    # ------------------

    def keyPath(self):
        """Keys the path attribute on the control object at the current time"""
        name = self.getMotionPathStr()
        cmds.setKeyframe("{}.uValue".format(name))

    def setMotionPath(self, value):
        """Sets the path attribute on the controller object"""
        motionPath_name = self.getMotionPathStr()
        cmds.setAttr("{}.uValue".format(motionPath_name), value)

    # ------------------
    # JOINTS HELPER METHODS
    # ------------------

    def bindJointDefaults(self, firstJoint, lastJoint):
        """ Bind the defaults positions/rotations for the joints"""
        if firstJoint and lastJoint:
            for i, j in enumerate(self.joints(firstJoint, lastJoint)):
                name = j
                result = cmds.xform(name, q=True, m=True)
                self.jointMatrix[i].set(result)
            return self.joints(firstJoint, lastJoint)

    def resetJoint(self, firstjointName, lastjointName):
        """Puts backs the joints to their original positions before the rig
        :param firstjointName: First Joint Name in chain
        :type firstjointName: str
        :param lastjointName: Last Joint Name in chain
        :type lastjointName: str
        """
        joints = self.joints(firstjointName, lastjointName)
        for i, j in enumerate(joints):
            name = j
            cmds.xform(name, m=self.jointMatrix[i].value())

    def joints(self, firstJoint, lastJoint):
        """ Gets all the joints in between start and end
        :return:
        :rtype: list[zapi.DagNode]
        """
        joint_chain = []
        jointVar = lastJoint
        while jointVar != firstJoint or jointVar is None:
            joint_chain.append(jointVar)
            res = cmds.listRelatives(jointVar, allParents=True, path=True)
            if res is None:
                break
            if res:
                jointVar = res[0]
                if jointVar == firstJoint:
                    joint_chain.append(jointVar)
        joint_chain.reverse()
        return joint_chain

    # ------------------
    # SELECT CONTROL
    # ------------------

    def selectCurveObj(self, add=True, replace=False):
        """Selects the control object

        :param add: Add to the selection
        :type add: bool
        :param replace: Deselect other objects and replace with this selection
        :type replace: bool
        """
        cmds.select(self.getPathStr(), add=add, replace=replace)

    def inverseDirection(self, value=False):
        motionPathZapi = zapi.nodeByName(self.getMotionPathStr())
        motionPathZapi.inverseFront.set(value)

    # ------------------
    # CHANGE CURVES
    # ------------------

    def switchCurves(self, newCurve):
        """Changes the curve path input for the rig

        :param newCurve: The name of the new curve
        :type newCurve: str
        """
        # Disconnect existing curve
        oldCurve = self.getPathStr()
        motionPath = self.getMotionPathStr()
        if oldCurve == newCurve:  # already attached to this curve
            return
        if oldCurve:
            objectAttribute = ("{}.geometryPath".format(motionPath))
            oppositeAttrs = cmds.listConnections(objectAttribute, plugs=True)
            cmds.disconnectAttr(oppositeAttrs[1], objectAttribute)
        # connect new curve to motion path
        newCurveShape = cmds.listRelatives(newCurve, fullPath=True, shapes=True)[0]
        cmds.connectAttr("{}.worldSpace[0]".format(newCurveShape), "{}.geometryPath".format(motionPath))
        # Connect new curve to the meta
        zapi.nodeByName(newCurve).message.connect(self.path)
        cmds.select(deselect=True)
        self.selectCurveObj()

    # ------------------
    # BUILD RIG
    # ------------------

    def buildRig(self, firstJoint, lastJoint, curve, dirValue, upAxis_value, lattice_value):
        """Building the Rig using inputs from the UI
        Returns 5 values - ikHandle, ikEffector, ikCurve, lattice, base

        :param firstJoint: first joint
        :type firstJoint: str
        :param lastJoint: last joint
        :type lastJoint: str
        :param curve: path curve name
        :type curve: str
        :param dirValue: Direction of joint chain
        :type dirValue: str
        :param upAxis_value: UpAxis value of joint chain
        :type upAxis_value: str
        :param lattice_value: Lattice value for motion path
        :type lattice_value: int
        :return:
        :rtype:
        """

        joint_List = self.bindJointDefaults(firstJoint, lastJoint)
        joint_chain_size = len(joint_List)

        if dirValue == "Auto":
            dirValue = axis.autoAxisBBoxObjList(joint_List)[-1]

        dic_results = jointsflowpath.pathGuide(firstJoint, lastJoint, curve, dirValue,
                                               joint_chain_size, upAxis_value, lattice_value)
        ikHandle = dic_results["ikHandle"]
        ikEffector = dic_results["ikEffector"]
        ikCurve = dic_results["ikCurve"]
        lattice = dic_results["flowLattice"]
        base = dic_results["flowBase"]
        motionPath = dic_results["motionPath"]
        frontaxis = dic_results["frontAxis"]

        # Connecting the Attributes
        self.connectAttributesStr(firstJoint, lastJoint, curve, ikHandle, ikEffector,
                                  ikCurve, lattice, base, motionPath)

        self.frontAxis.set(frontaxis)
        cmds.select(deselect=True)
        self.selectCurveObj()

    # ------------------
    # Delete RIG
    # ------------------

    def deleteAttr(self):
        # Deleting attributes of the meta node
        cmds.delete(self.getikHandleStr())
        cmds.delete(self.getikEffectorStr())
        cmds.delete(self.getikCurveStr())
        cmds.delete(self.getBaseStr())

        self.resetJoint(self.getFirstJointStr(), self.getLastJointStr())

        # Deletes the Meta Node
        self.delete()


# ------------------
# Helper functions
# ------------------

def reverseCurvesMetaNodes(metaNodes, message=True):
    """Reverses curves for all given meta nodes, handles doubles, ie each curve is only reversed once.

    :param metaNodes: Any motion path meta nodes
    :type metaNodes: list(obj)
    :param message: Report the message to the user?
    :type message: bool
    """
    curveList = list()
    for meta in metaNodes:
        curveList.append(meta.getPathStr())
    curveList = list(set(curveList))
    if not curveList:
        if message:
            output.displayWarning("No curves found to reverse.")
        return
    curves.reverseCurves(curveList, replaceOriginal=True)
    if message:
        output.displayInfo("Curves Reversed: {}".format(curveList))
    selectCurveObjs(metaNodes)


def selectCurveObjs(metaNodes):
    """Selects the control objects of all rigs

    :param metaNodes: Any motion path meta nodes
    :type metaNodes: list(obj)
    """
    if not metaNodes:
        return
    cmds.select(deselect=True)
    for meta in metaNodes:
        meta.selectCurveObj()


# ------------------
# ERROR CHECKING
# ------------------

# Checking if selected object is valid for input
def checkLoadObject(objecttype):
    """
    :param objecttype: The object type you want the select object to be
    :type objecttype: Str
    :return: selected obj
    :rtype: str
    """
    selectedobj = cmds.ls(selection=True, transforms=True)[0]
    if objecttype == "nurbsCurve":
        if not filtertypes.shapeTypeFromTransformOrShape([selectedobj], shapeType=objecttype):
            output.displayWarning("Please select a nurbsCurve Object")
            return
        return selectedobj
    if not cmds.objectType(selectedobj, isType=objecttype):
        output.displayWarning("Please select the correct object type: {}".format(objecttype))
        return
    return selectedobj


# Testing if UI inputs are valid
def checkInputs(firstJoint, lastJoint, curve, lattice_value):
    """
    :param firstJoint: First joint in chain
    :type firstJoint: str
    :param lastJoint: Last joint in chain
    :type lastJoint: str
    :param curve: path that the joint chain is following
    :type curve: str
    :param lattice_value: UI lattice value
    :type lattice_value: int
    :return:
    :rtype: bool
    """
    if not cmds.objExists(firstJoint):
        output.displayWarning("{} does not exists in scene".format(firstJoint))
        return False
    if not cmds.objExists(lastJoint):
        output.displayWarning("{} does not exists in scene".format(lastJoint))
        return False
    # TODO: Check if joints full names
    if not areJointsRelated(firstJoint, lastJoint):
        output.displayWarning("The joints not apart of the same chain")
        return False
    if not cmds.objExists(curve):
        output.displayWarning("{} does not exists in scene".format(curve))
        return False
    if not checkingLatticeValue(lattice_value):
        output.displayWarning("Minimum Value is 2")
        return False
    return True


def checkingLatticeValue(value):
    """
    :param value: Checking input Lattice Value
    :type value: int
    :return:
    :rtype: bool
    """
    if value < 2:
        return False
    return True


# Checking if the joints are apart of the same chain
def areJointsRelated(firstJoint, lastJoint):
    """
    :param firstJoint: First joint in chain
    :type firstJoint: str
    :param lastJoint: last joint in chain
    :type lastJoint: str
    :return:
    :rtype: bool
    """
    res = cmds.listRelatives(firstJoint, allDescendents=True, path=True)
    for obj in res:
        if lastJoint == obj:
            return True
    return False


def switchSelectedCurves():
    """Switches curves on all selected motion path rigs, select the motion path objs first and then the new curve last.
    """
    objList = cmds.ls(selection=True, long=True)
    if not objList:
        output.displayWarning("Nothing selected, please select a motion path object/s, then the new curve.")
        return
    if len(objList) < 2:
        output.displayWarning("Only one object is selected, please select motion path object/s, then the new curve.")
        return
    newCurve = objList.pop(-1)
    if not filtertypes.filterTypeReturnTransforms([newCurve], children=False, shapeType="nurbsCurve"):
        output.displayWarning("The last selected object needs to be a nurbsCurve")
        return
    nodes = list(zapi.nodesByNames(objList))  # convert objList to zapi nodes
    metaNodes = base.findRelatedMetaNodesByClassType(nodes, ZooAlongAPath.__name__)  # the metaNodes
    if not metaNodes:
        output.displayWarning("No motion path rigs found in the initial selection.")
        return
    switchCurves(newCurve, metaNodes)


def switchCurves(newCurve, metaNodes):
    """Switches curves of motion path rigs

    :param newCurve: the curve to switch to
    :type newCurve: str
    :param metaNodes: the meta node list of rigs to switch
    :type metaNodes: list(obj)
    """
    for meta in metaNodes:
        meta.switchCurves(newCurve)
    output.displayInfo("Success: Curves switched to {}".format(newCurve))


# Selecting all meta nodes that are this one
def selectedMetaNodes():
    """Returns meta nodes of type ZooMotionPathRig.__name__"""
    selectedNodes = list(zapi.selected())
    return base.findRelatedMetaNodesByClassType(selectedNodes, ZooAlongAPath.__name__)


def buildRigSetup(firstJoint, lastJoint, curve, dirValue, upAxis_value, lattice_value):
    """ Testing Inputs before building flow path rig
    :param firstJoint: first joint name in UI
    :type firstJoint: str
    :param lastJoint: last joint name in UI
    :type lastJoint: str
    :param curve: curve name in UI
    :type curve: str
    :param dirValue: which way the chain is facing in UI
    :type dirValue: str
    :param upAxis_value: Joint chain upAxis value in UI
    :type upAxis_value: str
    :param lattice_value: Lattice in UI value
    :type lattice_value: int
    :return:
    :rtype:
    """
    if not checkInputs(firstJoint, lastJoint, curve, lattice_value):
        return

    meta = ZooAlongAPath()
    meta.buildRig(firstJoint, lastJoint, curve, dirValue, upAxis_value, lattice_value)
