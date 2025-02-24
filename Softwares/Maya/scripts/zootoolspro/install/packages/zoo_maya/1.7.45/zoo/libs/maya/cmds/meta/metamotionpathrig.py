""""
Build Motion Path Rigs Meta
########################################

Build motion path rigs with various setups and change options.

Zoo meta nodes use Maya's "network" nodes to track and control multiple objects in node setups.

Build a single motion path rig with a meta node:

.. code-block:: python

    from zoo.libs.maya.cmds.meta import metamotionpathrig
    metaNode = metamotionpathrig.ZooMotionPathRig()
    metaNode.build(transform, curve, group=group, controlObj=controlObj, followAxis=followAxis, upAxis=upAxis,
                    worldUpVector=worldUpVector, parentConstrain=parentConstrain, message=message)

Or build multiple rigs from selection:

.. code-block:: python

    from zoo.libs.maya.cmds.meta import metamotionpathrig
    metaNodes = buildMotionPathRigsSelection(curve="", group=True, followAxis="z", upAxis="y", worldUpVector=(0, 1, 0),
                                 parentConstrain=False, message=True)

Meta nodes can be retrieved from the scene

.. code-block:: python

    metaNodes = metamotionpathrig.sceneMetaNodes()

Or retrieved via the related selection of any object in the rig setup

.. code-block:: python

    metaNodes = metamotionpathrig.selectedMetaNodes()

Rigs can be modified via the meta:

.. code-block:: python

    for meta in metaNodes:
        meta.setUpAxis("y")

Changes requiring hierarchy modifications the rigs are automatically completely rebuilt.

.. code-block:: python

    for meta in metaNodes:
        meta.setGrouped(True)

Rigs can be deleted with

.. code-block:: python

    meta.deleteRig()

Author: Andrew Silke

"""

from maya import cmds
import maya.api.OpenMaya as om2

from zoo.libs.maya import zapi
from zoo.libs.maya.meta import base
from zoo.libs.utils import output
from zoo.libs.maya.cmds.objutils import filtertypes, namehandling, attributes, curves, constraints, connections, \
    shapenodes
from zoo.libs.maya.cmds.rig import controls, motionpaths
from zoo.libs.maya.cmds.objutils.constraints import MOPATH_PATH_ATTR, MOPATH_FRONTTWIST_ATTR, MOPATH_UPTWIST_ATTR, \
    MOPATH_SIDETWIST_ATTR

META_TYPE = "ZooMotionPathRig"

XYZ_LIST = ["X", "Y", "Z", "-X", "-Y", "-Z"]
XYZ_LOWERCASE_LIST = ["x", "y", "z", "-x", "-y", "-z"]
MOPATH_TWIST_ATTRS = [MOPATH_FRONTTWIST_ATTR, MOPATH_UPTWIST_ATTR, MOPATH_SIDETWIST_ATTR]
MOPATH_UPV_VIS_ATTR = "upCtrlVis"

UPV_CTRL_SCALE = 2.0


class ZooMotionPathRig(base.MetaBase):
    """Class that controls the meta network node setup for the Animate Along Path (motion path rig) functionality

    Controls deleting, rebuilding the rig, querying and setting attributes.

    Found in zoo.libs.maya.cmds.objutils.constraints

    Attributes:

        motionPath: The motionPath node that was created
        curve: The curve the motion path follows
        obj: The original object usually also the control object, but not always
        followGrp: The group that has the motion path on it. Created if group or parentConstrain.
        parentConstrainGrp: The group parent constrained to the follow group. Created if group and parentConstrain.
        controlObj: The controlObj that receives the attributes. May have a new long name because of parenting.
        constraint: The parent constraint name. Created if parentConstrain.

    """
    _default_attrs = [{"name": "motionPath", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute},
                      {"name": "curve", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute},
                      {"name": "obj", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute},
                      {"name": "controlObj", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute},
                      {"name": "followGrp", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute},
                      {"name": "parentConstrainGrp", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute},
                      {"name": "parentConstraint", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute},
                      {"name": "upVCtrl", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute},
                      {"name": "upVGrp", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute},
                      {"name": "upVConstraint", "value": "", "Type": zapi.attrtypes.kMFnMessageAttribute},
                      ]

    def metaAttributes(self):
        """Creates the dictionary as attributes if they don't already exist"""
        defaults = super(ZooMotionPathRig, self).metaAttributes()
        defaults.extend(ZooMotionPathRig._default_attrs)
        return defaults

    def connectAttributes(self, motionPath, curve, obj, followGrp, parentConstrainGrp, controlObj, parentConstraint):
        """Connects the maya nodes to the meta node

        :param motionPath: The motion path node as a zapi node
        :type motionPath: :class:`zapi.DGNode`
        :param curve: The curve that the motion path follows as a zapi node
        :type curve: :class:`zapi.DGNode`
        :param obj: The main object, usually also the control object as a zapi node
        :type obj: :class:`zapi.DGNode`
        :param followGrp: the optional follow group as a zapi node, can be None
        :type followGrp: :class:`zapi.DGNode`
        :param parentConstrainGrp: the optional parent constraint group as a zapi node, can be None
        :type parentConstrainGrp: :class:`zapi.DGNode`
        :param controlObj: the control object, driver object as a zapi node, can be None
        :type controlObj: :class:`zapi.DGNode`
        :param parentConstraint: the optional parent constraint a zapi node, can be None
        :type parentConstraint: :class:`zapi.DGNode`
        """
        motionPath.message.connect(self.motionPath)
        curve.message.connect(self.curve)
        obj.message.connect(self.obj)
        if followGrp:
            followGrp.message.connect(self.followGrp)
        if parentConstrainGrp:
            parentConstrainGrp.message.connect(self.parentConstrainGrp)
        if controlObj:
            controlObj.message.connect(self.controlObj)
        if parentConstraint:
            parentConstraint.message.connect(self.parentConstraint)

    def connectAttributesStr(self, motionPath, curve, obj, followGrp, parentConstrainGrp, controlObj, parentConstraint):
        """Connects the maya string names to the meta node

        :param motionPath: The motion path node as a string
        :type motionPath: str
        :param curve: The curve that the motion path follows as a string
        :type curve: str
        :param obj: The main object, usually also the control object as a string
        :type obj: str
        :param followGrp: the optional follow group as a string, can be ""
        :type followGrp: str
        :param parentConstrainGrp: the optional parent constraint group as a string, can be ""
        :type parentConstrainGrp: str
        :param controlObj: the control object, driver object as a string, can be ""
        :type controlObj: str
        :param parentConstraint: the optional parent constraint a string, can be ""
        :type parentConstraint: str
        """
        followZapi = None
        parentConstrainGrpZapi = None
        controlObjZapi = None
        parentConstraintZapi = None
        if followGrp:
            followZapi = zapi.nodeByName(followGrp)
        if parentConstrainGrp:
            parentConstrainGrpZapi = zapi.nodeByName(parentConstrainGrp)
        if controlObj:
            controlObjZapi = zapi.nodeByName(controlObj)
        if parentConstraint:
            parentConstraintZapi = zapi.nodeByName(parentConstraint)
        self.connectAttributes(zapi.nodeByName(motionPath),
                               zapi.nodeByName(curve),
                               zapi.nodeByName(obj),
                               followZapi,
                               parentConstrainGrpZapi,
                               controlObjZapi,
                               parentConstraintZapi)

    def setMetaAttributes(self):
        """Sets the setup's attributes usually from the UI"""
        # self.jointCount = jointCount
        pass

    def getMetaAttributes(self):
        """Returns a dictionary of object fullpath string names"""
        return {"motionPath": self.motionPath.asString(),
                "obj": self.motionPath.asString(),
                "followGrp": self.motionPath.asString(),
                "controlObj": self.motionPath.asString(),
                "parentConstraint": self.motionPath.asString()}

    # ------------------
    # GETTERS AND SETTERS
    # ------------------

    def _isConnected(self, attr):
        """Checks if a zapi attribute is connected to an object

        :param attr: a single zapi attribute
        :type attr: zapi.attrtypes
        :return isConnected: returns True if connected
        :rtype isConnected: bool
        """
        if attr.sourceNode():
            return True
        return False

    def isValid(self):
        """Checks if connected to a motion path, if not then the meta is dead"""
        if self.getMotionPath():
            return True
        return False

    def upVectorControl(self):
        """Returns whether the up vector control exists"""
        if self._isConnected(self.upVCtrl):
            return True
        return False

    def upVCtrlScale(self):
        """Gets the scale of the up vector control if it exists, returns None if doesn't exist"""
        if not self.upVectorControl():
            return None
        upVCtrlStr = self.upVCtrl.sourceNode().fullPathName()
        # Get control scale
        return controls.getCreateControlScale(upVCtrlStr)[0]  # is a list so returns x value

    def setUpVCtrlScale(self, scale):
        """Sets the absolute scale of the up vector control

        :param scale: The absolute scale of the control
        :type scale: float
        """
        if not self.upVectorControl():
            return
        upVCtrlStr = self.upVCtrl.sourceNode().fullPathName()
        # Set control scale
        controls.scaleControlAbsoluteList([scale, scale, scale], [upVCtrlStr], message=True)

    def setUpVCtrlRelScale(self, scaleMultiplier, reset=False):
        """Scale the up vector control relatively, ie 1.1 will make the control 10% bigger.

        :param scaleMultiplier: A multiplication value of the scale, 1.1 will make the control 10% bigger.
        :type scaleMultiplier: float
        :param reset: If True will rest the scale to the size it was created.
        :type reset: bool
        """
        if not self.upVectorControl():
            return None
        upVCtrlStr = self.upVCtrl.sourceNode().fullPathName()
        if reset:
            controls.resetScale(upVCtrlStr)
            return
        scale = self.upVCtrlScale() * scaleMultiplier
        controls.scaleControlAbsoluteList([scale, scale, scale], [upVCtrlStr], message=True)

    def setUpVectorControl(self, build):
        """Sets the state of the upVectorControl, will build or delete the control"""
        if build == self.upVectorControl():  # check if already built and exit if same
            return
        if build:
            self.buildUpVectorControl()
            return
        self.deleteUpVectorControl()

    def rotationFollow(self):
        """Returns whether the motion path controls rotation True or not False

        :return rotationFollow: True if rotation is connected False if not
        :rtype rotationFollow: bool
        """
        if cmds.listConnections("{}.rotate".format(self.getMotionPathStr())):
            return True
        return False

    def setRotationFollow(self, follow):
        """If follow then connects the objects rotation if not disconnects it.

        :param follow: If True connects the rotate of the motion path and the main object
        :type follow: bool
        """
        motionPath = self.getMotionPathStr()
        # TODO this won't work if connecting, needs a better way of tracking the obj
        obj = self.motionPathObj()
        if follow:
            cmds.connectAttr("{}.rotate".format(motionPath), "{}.rotate".format(obj))
            cmds.connectAttr("{}.rotateOrder".format(motionPath), "{}.rotateOrder".format(obj))
            return
        # Disconnect
        objList = cmds.listConnections("{}.rotate".format(motionPath))
        if objList:
            cmds.disconnectAttr("{}.rotate".format(objList[0]), "{}.rotate".format(motionPath))
            cmds.disconnectAttr("{}.rotateOrder".format(objList[0]), "{}.rotateOrder".format(motionPath))

    def worldUpType(self):
        """Gets the world up type of the motion path as an int:

            Scene Up: 0
            Object Up: 1
            Object Rotation Up: 2
            Vector: 3
            Normal: 4

        :return worldUpType: Int representing the world up type, see description for value names.
        :rtype worldUpType: int
        """
        motionPath = self.getMotionPathStr()
        return cmds.getAttr("{}.worldUpType".format(motionPath))

    def setWorldUpType(self, worldUpType):
        """Sets the world up type of the motion path as an int:

            Scene Up: 0
            Object Up: 1
            Object Rotation Up: 2
            Vector: 3
            Normal: 4

        :param worldUpType: Int representing the world up type, see description for value names.
        :type worldUpType: int
        """
        motionPath = self.getMotionPathStr()
        cmds.setAttr("{}.worldUpType".format(motionPath), worldUpType)

    def worldUpObject(self):
        """Returns the world up object connected to the attr "worldUpMatrix" on the motion path

        Or returns "" if not connected.

        :return worldUpObject: the world up object connected to the attr "worldUpMatrix" on the motion path
        :rtype worldUpObject: str
        """
        motionPath = self.getMotionPathStr()
        worldUpList = cmds.listConnections("{}.worldUpMatrix".format(motionPath))
        if not worldUpList:
            return ""
        return worldUpList[0]

    def setWorldUpObject(self, worldUpObject):
        # will need to connect the worldUpObject to the attr "worldUpMatrix" on the motion path
        motionPathStr = self.getMotionPathStr()
        if cmds.listConnections("{}.worldUpMatrix".format(motionPathStr), plugs=True):
            # Disconnect
            connections.breakAttr("{}.worldUpMatrix".format(motionPathStr))
        if worldUpObject == "":  # Disconnect, no longer an object connected
            output.displayInfo("Up Object disconnected from the motion path `{}`".format(motionPathStr))
            return
        cmds.connectAttr("{}.worldMatrix".format(worldUpObject), "{}.worldUpMatrix".format(motionPathStr))
        output.displayInfo("Up Object set as `{}`".format(worldUpObject))

    def worldUpVector(self):
        upVector = cmds.getAttr("{}.worldUpVector".format(self.getMotionPathStr()))[0]

        return upVector

    def setWorldUpVector(self, upVector):
        """Sets the world up vector

        :param upVector: The up vector for the motion path
        :type upVector: list(float)
        """
        cmds.setAttr(".".join([self.getMotionPathStr(), "worldUpVector"]),
                     upVector[0], upVector[1], upVector[2], type="double3")

    def _axisStringFromInverse(self, axisInt, invertAxis):
        upAxis = ""
        if invertAxis:
            upAxis = "-"
        if axisInt == 0:
            return "{}x".format(upAxis)
        if axisInt == 1:
            return "{}y".format(upAxis)
        if axisInt == 2:
            return "{}z".format(upAxis)

    def _inverseAxisIntFromString(self, axisString):
        """Converts a string such as "-x" or "y" into an int 0, 1, or 2 and an inverse bool True is "-"

        :param axisString: "-x", "z", "-y" etc
        :type axisString: str

        :return axisInt: x is 0 y is 1 and z is 2
        :rtype axisInt: int
        :return inverse: 1 is inverse 0 is not inversed
        :rtype inverse: int
        """
        inverse = 0
        if "-" in axisString:
            inverse = 1
        axis = axisString.replace('-', '')
        if axis == "x":
            return 0, inverse
        elif axis == "y":
            return 1, inverse
        else:  # "z"
            return 2, inverse

    def upAxis(self):
        """Returns the up axis as a string "X", "Y", "Z", "-X", "-Y", "-Z"

        :return upAxis: The up axis as a string, "X", "Y", "Z", "-X", "-Y", "-Z"
        :rtype upAxis: str
        """
        motionPath = self.getMotionPathStr()
        axisInt = cmds.getAttr("{}.upAxis".format(motionPath))
        invertAxis = cmds.getAttr("{}.inverseUp".format(motionPath))
        return self._axisStringFromInverse(axisInt, invertAxis)

    def setUpAxis(self, upAxis):
        """Sets the up axis of the motion path from lowercase "-x", "z", "-y" etc

        :param upAxis: "-x", "z", "-y" etc
        :type upAxis: str
        """
        motionPath = self.getMotionPathStr()
        axisInt, inverse = self._inverseAxisIntFromString(upAxis)
        cmds.setAttr("{}.upAxis".format(motionPath), axisInt)
        cmds.setAttr("{}.inverseUp".format(motionPath), inverse)

    def followAxis(self):
        """Returns the follow (front) axis as a string "X", "Y", "Z", "-X", "-Y", "-Z"

        :return upAxis: The follow (front) axis as a string, "X", "Y", "Z", "-X", "-Y", "-Z"
        :rtype upAxis: str
        """
        motionPath = self.getMotionPathStr()
        axisInt = cmds.getAttr("{}.frontAxis".format(motionPath))
        invertAxis = cmds.getAttr("{}.inverseFront".format(motionPath))
        return self._axisStringFromInverse(axisInt, invertAxis)

    def setFollowAxis(self, followAxis):
        """Sets the up axis of the motion path from lowercase "-x", "z", "-y" etc

        :param upAxis: "-x", "z", "-y" etc
        :type upAxis: int
        """
        motionPath = self.getMotionPathStr()
        axisInt, inverse = self._inverseAxisIntFromString(followAxis)
        cmds.setAttr("{}.frontAxis".format(motionPath), axisInt)
        cmds.setAttr("{}.inverseFront".format(motionPath), inverse)

    def grouped(self):
        """Returns True if the rig has been grouped in the UI

        :return grouped: Returns True if the rig has a group
        :rtype grouped: bool
        """
        if self._isConnected(self.parentConstrainGrp):
            return True
        elif not self._isConnected(self.parentConstraint) and self._isConnected(self.followGrp):
            return True
        return False

    def setGrouped(self, group=True):
        """Potentially rebuilds the rig by deleting and rebuilding it if differences in the group option

        If the value matches the current setting do nothing.

        :param group: potentially rebuilds the rig by deleting and rebuilding it if True
        :type group: bool
        """
        if group and self.grouped():  # is already grouped
            return
        if not group and not self.grouped():  # is already not grouped
            return
        self.rebuildRig(group=group)

    def follow(self):
        """Returns whether the rig has the follow option checked.

        :return follow: Is the rig following the path with rotation values?
        :rtype follow: bool
        """
        motionPath = self.getMotionPathStr()
        if not motionPath:
            return None  # no motion path found, unlikely
        return cmds.pathAnimation(motionPath, follow=True, query=True)

    def setFollow(self, follow, message=False):
        """Set the follow bool on the motion path.  Checks if the rotation of the target obj has keys or connections

        Also needs to remove or add the twist attributes on teh control object:

            MOPATH_FRONTTWIST_ATTR = "frontTwist"
            MOPATH_UPTWIST_ATTR = "upTwist"
            MOPATH_SIDETWIST_ATTR = "sideTwist"

        :param follow: True if the rotation follow option will be on, False if only translation
        :type follow: bool
        :param message: Report the message to the user?
        :type message: bool
        """
        motionPath = self.getMotionPathStr()
        if not motionPath:
            return  # no motion path found, unlikely
        currentFollow = cmds.pathAnimation(motionPath, follow=True, query=True)
        if currentFollow == follow:  # is already the correct value
            return

        if follow == False:  # UNFOLLOW ----------------------------
            self.rebuildRig(follow=False)
            cmds.setAttr("{}.rotate".format(self.motionPathObj()), 0.0, 0.0, 0.0, type="double3")
            cmds.setAttr("{}.rotate".format(self.getControlObjStr()), 0.0, 0.0, 0.0, type="double3")
            if self.parentConstrained() and self.grouped():
                parentConstrainGrp = self.parentConstrainGrp.sourceNode().fullPathName()
                cmds.setAttr("{}.rotate".format(parentConstrainGrp), 0.0, 0.0, 0.0, type="double3")
            self.deleteControlAttrs(keepPathAttr=True)
            if self.upVectorControl():
                self.deleteUpVectorControl()
            if message:
                output.displayInfo(
                    "Success: Rig rebuilt, rotation follow has been disconnected for {}".format(motionPath))
            return
        # FOLLOW ------------------------------------
        # Check for connections, locked attrs
        lockedNodes, lockedAttrs = attributes.getLockedConnectedAttrsList([self.motionPathObj()],
                                                                          attributes.MAYA_ROTATE_ATTRS,
                                                                          keyframes=True)
        if lockedNodes:
            if message:
                output.displayWarning("Rotation Follow not applied.  Please disconnect attrs, "
                                      "there are keys/connections on: {}".format(lockedAttrs))
            return
        self.rebuildRig(follow=True)
        # self.deleteControlAttrs(keepPathAttr=True)  # will be left behind
        self.setUpAxis("y")  # setting defaults as defaults are bad and are lost in the rebuild
        self.setFollowAxis("z")
        if message:
            output.displayInfo("Success: Rig rebuilt, rotation follow has been connected for {}".format(motionPath))

    def parentConstrained(self):
        """Returns True if the rig is parent constrained

        :return parentConstrained: Returns True if the rig is parent constrained
        :rtype parentConstrained: bool
        """
        return self._isConnected(self.parentConstraint)

    def setParentConstrained(self, parentConstrain):
        """Potentially rebuilds the rig by deleting and rebuilding it if differences in the parentConstrain option

        If the value matches the current setting do nothing.

        :param parentConstrain: potentially rebuilds the rig by deleting and rebuilding it if differences
        :type parentConstrain: bool
        """
        if parentConstrain and self.parentConstrained():  # is already parent constrained
            return
        if not parentConstrain and not self.parentConstrained():  # is already not grouped
            return
        self.rebuildRig(parentConstrain=parentConstrain)

    # ------------------
    # CONTROL IS REFERENCED?
    # ------------------

    def isControlObjReferenced(self):
        """Checks whether the control object is refernced or not.  Useful for UI greying out the ability to grp.

        :return referenced: True if the control object is referenced
        :rtype referenced: bool
        """
        return cmds.referenceQuery(self.getControlObjStr(), isNodeReferenced=True)

    # ------------------
    # KEY AND SET PATH
    # ------------------

    def keyPath(self):
        """Keys the path attribute on the control object at the current time"""
        cmds.setKeyframe(self.getControlObjStr(), attribute='path', time=cmds.currentTime(query=True))

    def getPath(self):
        """Returns the value of the path attribute on the controller object"""
        return cmds.getAttr("{}.path".format(self.getControlObjStr()))

    def setPath(self, value):
        """Sets the path attribute on the controller object"""
        cmds.setAttr("{}.path".format(self.getControlObjStr()), value)

    # ------------------
    # REVERSE CURVE
    # ------------------

    def reverseCurve(self):
        """Reverses the curve of the motion path"""
        curves.reverseCurves([self.getCurveStr()], replaceOriginal=True)

    # ------------------
    # GET OBJECTS
    # ------------------

    def motionPathObj(self):
        """Returns the object driven by the motion path node from the motion path via the zCoordinate attr

        :return motionPathObj: the object driven by the motion path node
        :rtype motionPathObj: str
        """
        addDoubleNodes = cmds.listConnections("{}.zCoordinate".format(self.getMotionPathStr()))
        if addDoubleNodes:
            objList = cmds.listConnections("{}.output".format(addDoubleNodes[0]))
            if objList:
                return objList[0]
        return ""

    def getMotionPath(self):
        """Returns the motionPath as a zapi dag node

        :return: zapi motionPath node
        :rtype: :class:`zapi.DGNode`
        """
        source = self.motionPath.source()
        if source:  # handles None
            return source.node()

    def getMotionPathStr(self):
        """Returns the motionPath as a long name

        :return: motionPath node names
        :rtype: str
        """
        return self.getMotionPath().fullPathName()


    def getControlObj(self):
        """Returns the controlObj as a zapi dag node

        :return: zapi motionPath node
        :rtype: :class:`zapi.DGNode`
        """
        return self.controlObj.sourceNode()

    def getControlObjStr(self):
        """Returns the controlObj as a long name

        :return: controlObj node names
        :rtype: str
        """
        controlObjZapi = self.getControlObj()
        if controlObjZapi:
            return controlObjZapi.fullPathName()
        return ""

    def getCurve(self):
        """Returns the curve as a zapi dag node

        :return: zapi curve node
        :rtype: :class:`zapi.DGNode`
        """
        return self.curve.sourceNode()

    def getCurveStr(self):
        """Returns the curve as a long name

        :return: curve node names
        :rtype: str
        """
        curveZapi = self.getCurve()
        if curveZapi:
            return curveZapi.fullPathName()
        return ""

    # ------------------
    # SELECT CONTROL
    # ------------------

    def selectControlObj(self, add=True, replace=False):
        """Selects the control object

        :param add: Add to the selection
        :type add: bool
        :param replace: Deselect other objects and replace with this selection
        :type replace: bool
        """
        cmds.select(self.getControlObjStr(), add=add, replace=replace)

    # ------------------
    # BUILD RIG
    # ------------------

    def buildUpVectorControl(self, controlScale=UPV_CTRL_SCALE):
        """Builds the upVector control and connects to the meta node"""
        controlObj = self.getControlObjStr()
        # build and group arrow control
        ctrlName = "{}_upVector_ctrl".format(namehandling.getShortName(controlObj))
        ctrlName = namehandling.nonUniqueNameNumber(ctrlName)
        upVGrp, upVCtrl = motionpaths.createArrowControl(ctrlName=ctrlName, controlScale=controlScale)
        # point constrain to the control Obj
        upVConstraint = cmds.pointConstraint(controlObj, upVGrp)[0]
        # connect the upVector control, group and point constraint to the meta node
        zapi.nodeByName(upVGrp).message.connect(self.upVGrp)
        zapi.nodeByName(upVCtrl).message.connect(self.upVCtrl)
        zapi.nodeByName(upVConstraint).message.connect(self.upVConstraint)
        # Add the attributes on the control object for visibility and connect
        if not cmds.attributeQuery(MOPATH_UPV_VIS_ATTR, node=controlObj, exists=True):
            cmds.addAttr(controlObj, longName=MOPATH_UPV_VIS_ATTR, keyable=False,
                         defaultValue=1, attributeType='bool')
            cmds.setAttr(".".join([controlObj, MOPATH_UPV_VIS_ATTR]), channelBox=True)  # Show in channel box
        cmds.connectAttr(".".join([controlObj, MOPATH_UPV_VIS_ATTR]), ".".join([upVGrp, "visibility"]))
        # Connect the new up vector object to the motionPath node
        self.setWorldUpVector([0, 1, 0])
        self.setWorldUpObject(upVCtrl)
        self.setWorldUpType(2)

    def build(self, obj, curve, group=True, controlObj="", followAxis="z", upAxis="y", worldUpVector=(0, 1, 0),
              worldUpObject="", worldUpType=3, parentConstrain=False, follow=True, message=True):
        """Builds the rig for the meta node

        :param obj: The object to attach to a motion path
        :type obj: str
        :param curve: The curve that will be the motion path
        :type curve: str
        :param controlObj: Optional object that the attribute will be assigned to, might be a control, if empty will be obj
        :type controlObj: str
        :param followAxis: The axis to follow, default is "z", can be "x", "y", "z", "-x", "-y", "-z"
        :type followAxis: str
        :param upAxis: The up vector axis
        :type upAxis:
        :param worldUpVector: The up vector x, y, z as a list or tuple (0, 1, 0)
        :type worldUpVector: tuple(float)
        :param worldUpObject: The object for the object up rotation or object up (aim).
        :type worldUpObject: str
        :param worldUpType: 0 "scene", 1 "object", 2 "objectrotation", 3 "vector", or 4 "normal"
        :type worldUpType: int
        :param parentConstrain: parent constriain the obj, or obj's group, to a follow group which has the motion path
        :type parentConstrain: bool
        :param follow: Will rotation follow the path, if off only translation is controlled.
        :type follow: bool
        :param message: Report any messages to the user?
        :type message: bool
        """
        motionPath, \
        obj, \
        followGrp, \
        parentConstrainGrp, \
        controlObj, \
        parentConstraint = motionpaths.createMotionPathRig(obj,
                                                           curve,
                                                           group=group,
                                                           controlObj=controlObj,
                                                           attrName=MOPATH_PATH_ATTR,
                                                           followAxis=followAxis,
                                                           upAxis=upAxis,
                                                           worldUpVector=worldUpVector,
                                                           worldUpObject=worldUpObject,
                                                           worldUpType=worldUpType,
                                                           parentConstrain=parentConstrain,
                                                           follow=follow)

        if not motionPath:
            if message:
                output.displayWarning("Rig was not created for object: {}".format(obj))
            return controlObj
        if message:
            output.displayInfo("Success: Motion Path Rig created for object: {}".format(obj))

        return motionPath, obj, followGrp, parentConstrainGrp, controlObj, parentConstraint

    def buildUI(self, obj, curve, group=True, controlObj="", followAxis="z", upAxis="y", worldUpVector=(0, 1, 0),
                worldUpObject="", worldUpType=3, parentConstrain=False, follow=True, message=True):
        """See self.build for docs
        This version connects up the meta attributes to the meta node and returns the control object.
        """
        motionPath, \
        obj, \
        followGrp, \
        parentConstrainGrp, \
        controlObj, \
        parentConstraint = self.build(obj, curve, group=group, controlObj=controlObj, followAxis=followAxis,
                                      upAxis=upAxis, worldUpVector=worldUpVector, worldUpObject=worldUpObject,
                                      worldUpType=worldUpType, parentConstrain=parentConstrain,
                                      follow=follow, message=message)
        # Connect attrs to meta
        self.connectAttributesStr(motionPath, curve, obj, followGrp, parentConstrainGrp, controlObj, parentConstraint)
        return controlObj

    # ------------------
    # CHANGE CURVES
    # ------------------

    def switchCurves(self, newCurve):
        """Changes the curve path input for the rig

        :param newCurve: The name of the new curve
        :type newCurve: str
        """
        # Disconnect existing curve
        oldCurve = self.getCurveStr()
        motionPath = self.getMotionPathStr()
        if oldCurve == newCurve:  # already attached to this curve
            return
        if oldCurve:
            connections.breakAttr("{}.geometryPath".format(motionPath))
        # connect new curve to motion path
        newCurveShape = cmds.listRelatives(newCurve, fullPath=True, shapes=True)[0]
        cmds.connectAttr("{}.worldSpace[0]".format(newCurveShape), "{}.geometryPath".format(motionPath))
        # Connect new curve to the meta
        zapi.nodeByName(newCurve).message.connect(self.curve)

    # ------------------
    # DELETE RIG
    # ------------------

    def deleteUpVectorControl(self):
        # Delete the constraint, up control and group
        self.safeDelete(self.upVConstraint.sourceNode())
        self.safeDelete(self.upVCtrl.sourceNode())
        self.safeDelete(self.upVGrp.sourceNode())
        # Remove the vis attribute from the control object if it exists
        controlObjStr = self.getControlObjStr()
        if cmds.attributeQuery(MOPATH_UPV_VIS_ATTR, node=controlObjStr, exists=True):
            cmds.deleteAttr(controlObjStr, attribute=MOPATH_UPV_VIS_ATTR)
        # set to vector 0, 1, 0
        if self.getMotionPath():
            self.setWorldUpVector([0, 1, 0])
            self.setWorldUpType(3)

    def deleteEmptyMeta(self):
        """Deletes the meta node if it is not attached to a motionPath node

        :return deleted: True if the rig was deleted
        :rtype deleted: bool
        """
        if not self.isValid():
            self.delete()
            return True
        return False

    def deleteControlAttrs(self, keepPathAttr=False):
        """Deletes the attributes on the control object:

            MOPATH_PATH_ATTR = "path"
            MOPATH_FRONTTWIST_ATTR = "frontTwist"
            MOPATH_UPTWIST_ATTR = "upTwist"
            MOPATH_SIDETWIST_ATTR = "sideTwist"

        """
        controlObjStr = self.getControlObjStr()
        if cmds.attributeQuery(MOPATH_PATH_ATTR, node=controlObjStr, exists=True) and not keepPathAttr:
            cmds.deleteAttr(controlObjStr, attribute=MOPATH_PATH_ATTR)
        # Remove the unitConversion nodes left behind still connected to the motionPath ---------------
        for attr in MOPATH_TWIST_ATTRS:
            if cmds.attributeQuery(attr, node=controlObjStr, exists=True):
                cmds.deleteAttr(controlObjStr, attribute=attr)
            oppositeAttrList = cmds.listConnections(".".join([self.getMotionPathStr(), attr]), plugs=True)
            if oppositeAttrList:  # delete left over unitConversion nodes still connected
                delNode = oppositeAttrList[0].split(".")[0]
                if cmds.objectType(delNode) == "unitConversion":
                    cmds.delete(delNode)

    def createControlAttrs(self):
        """Creates and connects the control attributes on the rig, for setting follow to be true.

            MOPATH_FRONTTWIST_ATTR = "frontTwist"
            MOPATH_UPTWIST_ATTR = "upTwist"
            MOPATH_SIDETWIST_ATTR = "sideTwist"

        """
        controlObj = self.getControlObjStr()
        motionPath = self.getMotionPathStr()
        # Unlock motion path attributes that are locked by unfollow and add connect attrs on the control obj
        for attr in [MOPATH_FRONTTWIST_ATTR, MOPATH_UPTWIST_ATTR, MOPATH_SIDETWIST_ATTR]:
            cmds.setAttr(".".join([motionPath, attr]), lock=False)
            if not cmds.attributeQuery(attr, node=controlObj, exists=True):
                cmds.addAttr(controlObj, longName=attr, keyable=True)
            cmds.connectAttr(".".join([controlObj, attr]), ".".join([motionPath, attr]))

    def safeDelete(self, node):
        """Deletes a zapi node and passes if None"""
        if node:
            node.delete()

    def _deleteGrouped(self, controlObjStr, group):
        """Deletes the group that the control object is a child and handles parent cases."""
        children = cmds.listRelatives(group, children=True, shapes=False)
        if len(children) > 1:
            if not (len(children) == 2 and self.parentConstraint.sourceNode()):
                return  # is not parent constrained so don't delete as the user has likely added other objects
        parent = cmds.listRelatives(group, parent=True)  # Get the parent of the group
        if parent:  # Parent to the parent of the control object or world
            cmds.parent(controlObjStr, parent)
        else:
            cmds.parent(controlObjStr, world=True)
        cmds.delete(group)

    def deleteRig(self, keepMeta=False, keepPathAttrs=False, message=True):
        """Deletes the rig, can be multiple types of rig"""
        controlObjStr = self.getControlObjStr()  # for messages
        if self.deleteEmptyMeta():  # Delete node if not attached to anything
            return  # empty node was deleted

        # Delete generic parts of the rig ---------------------------
        if not keepPathAttrs:
            self.deleteControlAttrs()
        self.safeDelete(self.getMotionPath())

        # Delete specific parts of the rig ----------------------------
        if self.grouped():  # Then is grouped
            if self.parentConstraint.sourceNode():
                if controlObjStr:
                    # "grouped and parent constrained"
                    group = self.parentConstrainGrp.sourceNode().fullPathName()
                    self._deleteGrouped(controlObjStr, group)  # Delete the control group safely
                self.safeDelete(self.followGrp.sourceNode())  # the follow group should be empty
            else:
                # "grouped and not parent constrained"
                if controlObjStr:
                    # get the parent of the group
                    group = self.followGrp.sourceNode().fullPathName()
                    self._deleteGrouped(controlObjStr, group)  # Delete the control group safely
        else:  # Not grouped
            if self.parentConstraint.sourceNode():  # Is Parent Constrained
                # "not grouped and parent constrained"
                # delete the parent constraint then the follow group
                self.safeDelete(self.parentConstraint.sourceNode())
                self.safeDelete(self.followGrp.sourceNode())

        controlObjStr = self.getControlObjStr()  # update as might have changed

        # Delete meta node ------------------------------------------------
        if not keepMeta:  # rebuilding so keep
            if self.upVectorControl():
                self.deleteUpVectorControl()
            self.delete()

        # Delete the meta and parts of the rig ----------------------------
        if message:
            output.displayInfo("Success: Motion Path Rig deleted for {}".format(controlObjStr))

        return controlObjStr

    # ------------------
    # REBUILD RIG
    # ------------------

    def rebuildRig(self, parentConstrain=None, group=None, follow=None, message=True):
        """Rebuilds the rig by deleting and building with the new settings.

        Handles individual updates of parentConstrain and group

        :param parentConstrain: Is the rig parent constrained?
        :type parentConstrain: bool
        :param group: Is the control object grouped?
        :type group: bool
        :param message: Report a message to the user
        :type message: bool
        """
        # get the variables ----------------------------
        if parentConstrain is None:
            parentConstrain = self.parentConstrained()  # bool
        if group is None:
            group = self.grouped()  # bool
        if follow is None:
            follow = self.follow()
        # Get current values required for the rebuild ------------------
        curve = self.getCurveStr()
        followAxis = self.followAxis()
        upAxis = self.upAxis()
        worldUpVector = self.worldUpVector()
        worldUpObject = self.worldUpObject()
        worldUpType = self.worldUpType()
        # Delete the current setup -------------------------
        controlObj = self.deleteRig(keepMeta=True, keepPathAttrs=True)  # control object fullname can change

        # Rebuild with the current settings -------------------------
        motionPath, \
        obj, \
        followGrp, \
        parentConstrainGrp, \
        controlObj, \
        parentConstraint = self.build(controlObj, curve, group=group, controlObj=controlObj, followAxis=followAxis,
                                      upAxis=upAxis, worldUpVector=worldUpVector, worldUpObject=worldUpObject,
                                      worldUpType=worldUpType, parentConstrain=parentConstrain, follow=follow,
                                      message=message)
        # Connect attrs to meta ---------------------------------------------------
        self.connectAttributesStr(motionPath, curve, obj, followGrp, parentConstrainGrp, controlObj, parentConstraint)
        # Report Messages
        if message:
            output.displayInfo("Success: Motion Path Rig Rebuilt for {}".format(self.getControlObjStr()))


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


def switchCurvesSelection():
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
    metaNodes = base.findRelatedMetaNodesByClassType(nodes, ZooMotionPathRig.__name__)  # the metaNodes
    if not metaNodes:
        output.displayWarning("No motion path rigs found in the initial selection.")
        return
    switchCurves(newCurve, metaNodes)


def reverseCurvesMetaNodes(metaNodes, message=True):
    """Reverses curves for all given meta nodes, handles doubles, ie each curve is only reversed once.

    :param metaNodes: Any motion path meta nodes
    :type metaNodes: list(obj)
    :param message: Report the message to the user?
    :type message: bool
    """
    curveList = list()
    for meta in metaNodes:
        curveList.append(meta.getCurveStr())
    curveList = list(set(curveList))
    if not curveList:
        if message:
            output.displayWarning("No curves found to reverse.")
        return
    curves.reverseCurves(curveList, replaceOriginal=True)
    if message:
        output.displayInfo("Curves Reversed: {}".format(curveList))


def deselectRigs():
    """Deselect for UI"""
    cmds.select(deselect=True)


def selectControlObjs(metaNodes):
    """Selects the control objects of all rigs

    :param metaNodes: Any motion path meta nodes
    :type metaNodes: list(obj)
    """
    if not metaNodes:
        return
    cmds.select(deselect=True)
    for meta in metaNodes:
        meta.selectControlObj()


def buildMotionPathRigsSelection(curve="", group=True, followAxis="z", upAxis="y", worldUpVector=(0, 1, 0),
                                 worldUpObject="", worldUpType=3, parentConstrain=False, autoCleanMeta=True,
                                 follow=True, upVectorControl=False, upVScale=UPV_CTRL_SCALE, message=True):
    """Creates a motion path rigs from the current selection with ZooMotionPathRig meta nodes.
    Makes motion paths a lot easier to create and animate by copying the driving attributes onto the object itself.

    Supports multiple object selection, the curve path object should be selected last if it not given directly.

    :param curve: The curve that will be the motion path
    :type curve: str
    :param group: Group the object so that the motion path is on the group, not on the selected objects
    :type group: bool
    :param followAxis: The axis to follow, default is "z", can be "x", "y", "z", "-x", "-y", "-z"
    :type followAxis: str
    :param upAxis: The up vector axis
    :type upAxis:
    :param worldUpVector: The up vector x, y, z as a list or tuple (0, 1, 0)
    :type worldUpVector: tuple(float)
    :param parentConstrain: parent constrain the obj, or obj's group, to a follow group which has the motion path
    :type parentConstrain: bool
    :param autoCleanMeta: If True delete any unused meta nodes and unused motion path nodes
    :type autoCleanMeta: bool
    :param follow: Will rotation follow the path, if off only translation is controlled.
    :type follow: bool
    :param message: Report a message to the user?
    :type message: bool

    :return metaList: The motionPath node that was created list of zoo metaNodes
    :rtype metaList: list(objects)
    """
    # TODO: Auto create controls and add upvector control
    controlObjs = list()
    metaList = list()
    objList = cmds.ls(selection=True, long=True)
    # Error checking ----------------------------------
    if not objList:
        if message:
            output.displayWarning(
                "Please select objects to add motion paths.  Select the object/s then the path curve.")
        return metaList
    if not curve:
        curve = objList.pop(-1)
    if not objList:
        if message:
            output.displayWarning(
                "Please select at least two objects to create a motion path, only one object is selected.")
        return metaList
    if not filtertypes.filterTypeReturnTransforms([curve]):
        if message:
            output.displayWarning("The object `{}` is not a nurbsCurve, please select a curve.".format(curve))
        return metaList
    transformList = filtertypes.filterExactTypeList(objList, type="transform")
    if not objList:
        if message:
            output.displayWarning("The objects `{}` do not contain transforms, please select objects that can be "
                                  "attached to motion paths.".format(objList))
        return metaList

    # Check for connections, locked attrs ------------------
    lockedNodes, lockedAttrs = attributes.getLockedConnectedAttrsList(transformList, constraints.POS_ROT_ATTRS,
                                                                      keyframes=True)
    if lockedAttrs and not group:
        if message:
            output.displayWarning("Motion paths cannot be created as these attributes are "
                                  "locked, animated or connected: {}".format(lockedAttrs))
        return metaList
    if group:
        for transform in transformList:
            if cmds.referenceQuery(transform, isNodeReferenced=True):
                if message:
                    output.displayWarning(
                        "The object `{}` is referenced and cannot be grouped. "
                        "Please uncheck `Group Control Obj`.".format(objList))
                return metaList
    if curve in transformList:  # remove the curve in the transform list, can cause errors.
        transformList = [value for value in transformList if value != curve]
        if not transformList:
            if message:
                output.displayWarning("No transforms found, please deselect the curve path.".format(lockedAttrs))
            return metaList
    # Create the motion paths ---------------------------------------------
    for transform in transformList:
        controlObj = str(transform)
        meta = ZooMotionPathRig()
        controlObjShortName = controlObj.split("|")[-1].split(":")[-1]
        meta.rename("{}_zooMotionPathRig".format(controlObjShortName)[0])
        controlObj = meta.buildUI(transform, curve, group=group, controlObj=controlObj, followAxis=followAxis,
                                  upAxis=upAxis, worldUpVector=worldUpVector, worldUpObject=worldUpObject,
                                  worldUpType=worldUpType, parentConstrain=parentConstrain, follow=follow,
                                  message=message)
        if upVectorControl:
            meta.buildUpVectorControl(controlScale=upVScale)
            meta.setWorldUpVector(worldUpVector)  # Set again as gets overridden
        if meta.isValid():
            metaList.append(meta)
            controlObjs.append(controlObj)

    if controlObjs:
        cmds.select(controlObjs, replace=True)

    if autoCleanMeta:
        autoCleanEmptyMotionPathMeta(cleanMotionPaths=True)

    if message:
        shortNames = namehandling.getShortNameList(controlObjs)
        output.displayInfo("Success: Objects are now connected to motion paths `{}`".format(shortNames))
    return metaList


def autoCleanEmptyMotionPathMeta(cleanMotionPaths=True):
    """Cleans/deletes out any empty meta nodes and optionally deletes disconnected motion paths
    """
    # TODO could be part of meta, and the delete rig methods
    if cleanMotionPaths:
        motionPaths = cmds.ls(type="motionPath")
        if not motionPaths:
            return
        # Delete motion paths if they are missing a curve connection or an object connection (zCoordinate) -----------
        for mp in motionPaths:  # Check for valid motion paths
            curveConnections = cmds.listConnections("{}.geometryPath".format(mp), plugs=True)  # curve
            if not curveConnections:
                cmds.delete(mp)
                continue
            addDoubleNodes = cmds.listConnections("{}.zCoordinate".format(mp))  # object or double linear node
            if not addDoubleNodes:
                cmds.delete(mp)

    metaNodes = base.findMetaNodesByClassType(ZooMotionPathRig.__name__)
    for meta in metaNodes:
        meta.deleteEmptyMeta()  # kills meta nodes if not connected to a rig


def deleteMotionPathRigs(nodes, message=False):
    """Deletes all motionPath rigs and the meta node setup related to the selection

    :param nodes: any zapi nodes, can be any node related to joint setup
    :type nodes:  list(:class:`zapi.DGNode`)
    :param message: report the message to the user
    :type message: bool

    :return success: True if joints were deleted
    :rtype success: bool
    """
    metaNodes = base.findRelatedMetaNodesByClassType(nodes, ZooMotionPathRig.__name__)
    if not metaNodes:
        if message:
            relatedObjs = list(zapi.fullNames(nodes))
            om2.MGlobal.displayWarning("No `{}` meta nodes found related to objects "
                                       "{}".format(ZooMotionPathRig.__name__, relatedObjs))
        return False
    for metaNode in metaNodes:  # Delete the joints
        metaNode.deleteRig()
        metaNode.delete()
    if message:
        om2.MGlobal.displayInfo("Success Motion Path Rigs deleted")
    return True


def sceneMetaNodes():
    """Returns all ZooMotionPathRig meta nodes"""
    return base.findMetaNodesByClassType(ZooMotionPathRig.__name__)


def selectedMetaNodes():
    """Returns meta nodes of type ZooMotionPathRig.__name__"""
    selectedNodes = list(zapi.selected())
    return base.findRelatedMetaNodesByClassType(selectedNodes, ZooMotionPathRig.__name__)


def referenceSelectionCheck():
    """Checks if a control object under the selected metas, but not the last (curve) is a referenced obj

    :return referenced: True if a referenced object was found
    :rtype referenced: bool
    """
    selObjs = cmds.ls(selection=True, long=True)
    if not selObjs:
        return
    selObjs.pop(-1)
    if cmds.ls(selObjs, referencedNodes=True):
        return True
    return False
