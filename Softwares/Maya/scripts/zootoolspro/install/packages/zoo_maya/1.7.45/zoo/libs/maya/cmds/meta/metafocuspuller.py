""""
from zoo.libs.maya.cmds.meta import metafocuspuller
metafocuspuller.cleanupBrokenMetaNodes()  # removes broken setups

"""

from maya import cmds

from zoo.libs.maya import zapi
from zoo.libs.maya.meta import base
from zoo.libs.utils import output
from zoo.libs.maya.cmds.objutils import filtertypes
from zoo.libs.maya.cmds.cameras import focuspuller, cameras
from zoo.libs.maya import triggers

META_CLASS_TYPES = ["ZooFocusPullerRedshift", "ZooFocusPullerRenderman", "ZooFocusPullerArnold", "ZooFocusPuller"]

A_FOCUS_CTRL_GRP = "focusCtrlGrp"
A_FOCUS_CTRL = "focusCtrl"
A_PLANE_CTRL_GRP = "planeCtrlGrp"
A_PLANE_CTRL = "planeCtrl"
A_GRID_PLANE = "gridPlane"
A_MULT_DIV_NODE = "multiDivNode"
A_FOCUS_MASTER_GRP = "focusMasterGrp"
A_PARENT_CONSTRAINT = "parentConstraint"
A_POINT_CONSTRAINT = "pointConstraint"
A_REDSHIFT_BOKEH = "redshiftBokeh"
A_CAMERA = "camera"
A_CAMERA_SHAPE = "cameraShape"

DELETE_LIST = [A_FOCUS_CTRL_GRP, A_FOCUS_CTRL, A_PLANE_CTRL_GRP, A_PLANE_CTRL, A_MULT_DIV_NODE, A_FOCUS_MASTER_GRP,
               A_PARENT_CONSTRAINT, A_POINT_CONSTRAINT, A_REDSHIFT_BOKEH, A_GRID_PLANE]

ATTRIBUTE_LIST = DELETE_LIST + [A_CAMERA, A_CAMERA_SHAPE]


class ZooFocusPuller(base.MetaBase):
    """Class that controls the meta network node setup for the Focus Puller functionality

    Controls deleting, rebuilding the rig, querying and setting attributes.

    Attributes:

        camera: The Camera
        cameraShapeNode: The Camera shape node
        focusCtrlGrp: The focus control group that was created
        focusCtrl: The Focus control created using focus puller
        planeCtrlGrp: The focus control group that was created
        planeCtrl: The plane control created using focus puller
        parentConstraint: The parent constraint created using focus puller
        pointConstraint: The point constraint created using focus puller
        multiDivNode: The multiDiv node created using focus puller

    """
    _default_attrs = list()
    for attr in ATTRIBUTE_LIST:  # Straight message node attributes
        _default_attrs.append({"name": attr,
                               "value": "",
                               "Type": zapi.attrtypes.kMFnMessageAttribute})

    def isValid(self):
        """Tests if the current meta node is valid and not broken.

        :return valid: True if the meta node is valid, False if it is broken
        :rtype valid: bool
        """
        try:
            if not self.getCameraStr():
                return False
            if not self.getFocusCtrlStr():
                return False
            if not self.getPlaneCtrlStr():
                return False
            return True
        except:
            return False

    def metaAttributes(self):
        """Creates the dictionary as attributes if they don't already exist"""
        defaults = super(ZooFocusPuller, self).metaAttributes()
        defaults.extend(ZooFocusPuller._default_attrs)
        return defaults

    def allControls(self):
        """ All controls in the rig

        :return:
        :rtype: list[:class:`zapi.DagNode`]
        """
        ctrls = [self.focusCtrl.value()]
        ctrls += [self.planeCtrl.value()]
        return ctrls

    def setupMarkingMenus(self):
        mmNodes = self.allControls()
        layoutID = "markingMenu.focuspuller"
        triggers.createMenuTriggers(mmNodes, menuId=layoutID)

    def connectAttributes(self, camera_name, focus_ctrl_grp, focus_ctrl,
                          plane_ctrl_grp, plane_ctrl, parent_constraint,
                          point_constraint, multiDiv_node, master_grp, grid_plane):
        """Connects the maya nodes to the meta node

        :param camera_name: The camera as a zapi node
        :type camera_name: :class:`zapi.DGNode`
        :param focus_ctrl_grp: The focus control group as a zapi node
        :type focus_ctrl_grp: :class:`zapi.DGNode`
        :param focus_ctrl: The focus control as a zapi node
        :type focus_ctrl: :class:`zapi.DGNode`
        :param plane_ctrl_grp: The plane control group as a zapi node
        :type plane_ctrl_grp: :class:`zapi.DGNode`
        :param plane_ctrl: The focus control as a zapi node
        :type plane_ctrl: :class:`zapi.DGNode`
        :param parent_constraint: The parent constraint as a zapi node
        :type parent_constraint: :class:`zapi.DGNode`
        :param point_constraint: The point constraint  as a zapi node
        :type point_constraint: :class:`zapi.DGNode`
        :param multiDiv_node: The multiDiv node as a zapi node
        :type multiDiv_node: :class:`zapi.DGNode`
        """
        self.connectTo("camera", camera_name)
        cameraZapi = self.getCameraZapi()
        cameraShape = cameraZapi.shapes()[0]
        self.connectTo("cameraShape", cameraShape)
        self.connectTo("focusCtrlGrp", focus_ctrl_grp)
        self.connectTo("focusCtrl", focus_ctrl)
        self.connectTo("planeCtrlGrp", plane_ctrl_grp)
        self.connectTo("planeCtrl", plane_ctrl)
        self.connectTo("parentConstraint", parent_constraint)
        self.connectTo("pointConstraint", point_constraint)
        self.connectTo("multiDivNode", multiDiv_node)
        self.connectTo("focusMasterGrp", master_grp)
        self.connectTo("gridPlane", grid_plane)

        self.setupMarkingMenus()

    def connectAttributesStr(self, camera_name, focus_ctrl_grp, focus_ctrl,
                             plane_ctrl_grp, plane_ctrl, parent_constraint,
                             point_constraint, multiDiv_node, master_grp, grid_plane):
        """Connects the maya string names to the meta node

        :param camera_name: The Camera as a string
        :type camera_name: str
        :param focus_ctrl_grp: The focus control group as a string
        :type focus_ctrl_grp: str
        :param focus_ctrl: The focus control as a string
        :type focus_ctrl: str
        :param plane_ctrl_grp: The plane control group as a string
        :type plane_ctrl_grp: str
        :param plane_ctrl: The focus control as a string
        :type plane_ctrl: str
        :param parent_constraint: The parent constraint as a string
        :type parent_constraint: str
        :param point_constraint: The point constraint as a string
        :type point_constraint: str
        :param multiDiv_node: The multiDiv node as a string
        :type multiDiv_node: str
        """
        self.connectAttributes(zapi.nodeByName(camera_name),
                               zapi.nodeByName(focus_ctrl_grp),
                               zapi.nodeByName(focus_ctrl),
                               zapi.nodeByName(plane_ctrl_grp),
                               zapi.nodeByName(plane_ctrl),
                               zapi.nodeByName(parent_constraint),
                               zapi.nodeByName(point_constraint),
                               zapi.nodeByName(multiDiv_node),
                               zapi.nodeByName(master_grp),
                               zapi.nodeByName(grid_plane))

    # ------------------
    # Not needed Values
    # ------------------
    def renderer(self):
        return "Viewport"

    # ------------------
    # GETTERS AND SETTERS
    # ------------------

    def getAttrConnection(self, class_attr):
        """Returns the connected node of the attribute as a zapi dag node

        :return: zapi motionPath node
        :rtype: :class:`zapi.DGNode`
        """
        return class_attr.sourceNode()

    def getAttrConnectionStr(self, class_attr):
        """Returns the connected node of the attribute as a long name

        :return: the connection to the attribute as a string
        :rtype: str
        """
        node = self.getAttrConnection(class_attr)
        if node:
            return node.fullPathName()
        return ""

    def getCameraZapi(self):
        """Returns the connected node of the attribute as a long name

        :return: the connection to the attribute as a string
        :rtype: str
        """
        node = self.getAttrConnection(self.attribute(A_CAMERA))
        if node:
            return node
        return None

    def getCameraShapeNode(self):
        cameraZapi = zapi.nodeByName(self.getCameraStr())
        return cameraZapi.shapes()[0]

    def getCameraStr(self):
        """Returns the camera string"""
        return self.getAttrConnectionStr(self.attribute(A_CAMERA))

    def getCameraShapeStr(self):
        return self.getAttrConnectionStr(self.attribute(A_CAMERA_SHAPE))

    def getFocusCtrlStr(self):
        """Returns the Focus Control string"""
        return self.getAttrConnectionStr(self.attribute(A_FOCUS_CTRL))

    def getPlaneCtrlStr(self):
        """Returns the Plane Control string"""
        return self.getAttrConnectionStr(self.attribute(A_PLANE_CTRL))

    def getMultiDivStr(self):
        """Returns the Plane Control string"""
        return self.getAttrConnectionStr(self.attribute(A_MULT_DIV_NODE))

    def getFStopValue(self):
        """Returns the camera shape F Stop value"""
        cameraShape = self.getCameraShapeNode()
        return cameraShape.fStop.value()

    def getCtrlVisibility(self):
        ctrlzapi = zapi.nodeByName(self.getFocusCtrlStr())
        return not ctrlzapi.isHidden()

    def getPlaneVisibility(self):
        planeZapi = zapi.nodeByName(self.getPlaneCtrlStr())
        return not planeZapi.isHidden()

    def getRegionScale(self):
        cameraShape = self.getCameraShapeNode()
        return cameraShape.focusRegionScale.value()

    def getDOF(self):
        cameraShape = self.getCameraShapeNode()
        return cameraShape.depthOfField.value()

    def getFocusDistance(self):
        cameraShape = self.getCameraShapeNode()
        return cmds.getAttr("{}.focusDistance".format(cameraShape.fullPathName()))

    def getFocusScale(self):
        cameraZapi = zapi.nodeByName(self.getCameraStr())
        return cameraZapi.focusCtrlScale.value()

    def getGridVis(self):
        cameraZapi = zapi.nodeByName(self.getCameraStr())
        return cameraZapi.gridVis.value()

    def setFocusRegionScale(self, value):
        """Sets the fStop attribute on the camera shape object"""
        cameraShape = self.getCameraShapeNode()
        cmds.setAttr("{}.focusRegionScale".format(cameraShape.fullPathName()), value)

    def setCtrlScale(self, value):
        """Sets the fStop attribute on the camera shape object"""
        cmds.setAttr("{}.focusCtrlScale".format(self.getCameraStr()), value)

    def setFStop(self, value):
        """Sets the fStop attribute on the camera shape object"""
        cmds.setAttr("{}.fStop".format(self.getCameraStr()), value)

    def ctrlVisibility(self, value=True):
        """Sets the visibility attribute on the controls object"""
        cmds.setAttr("{}.dofCtrlVis".format(self.getCameraStr()), value)

    def planeVisibility(self, value=True):
        """Sets the visibility attribute on the controls object"""
        cmds.setAttr("{}.dofPlaneVis".format(self.getCameraStr()), value)

    def gridVisibility(self, value=True):
        cmds.setAttr("{}.gridVis".format(self.getCameraStr()), value)

    def depthOfField(self, value=True):
        """Sets the DOF attribute on the controls object"""
        cmds.setAttr("{}.depthOfField".format(self.getCameraShapeNode().fullPathName()), value)

    # ------------------
    # SELECT FOCUS CONTROL
    # ------------------

    def selectFocusCtrl(self, add=False, replace=True):
        """Selects the control object

        :param add: Add to the selection
        :type add: bool
        :param replace: Deselect other objects and replace with this selection
        :type replace: bool
        """
        cmds.select(self.getFocusCtrlStr(), add=add, replace=replace)

    # ------------------
    # SELECT CAMERA SHAPE
    # ------------------

    def selectCamera(self, add=False, replace=True):
        """Selects the Camera shape

        :param add: Add to the selection
        :type add: bool
        :param replace: Deselect other objects and replace with this selection
        :type replace: bool
        """
        cameraZapi = self.getCameraZapi()
        cmds.select(cameraZapi.fullPathName(), add=add, replace=replace)

    # ------------------
    # BUILD RIG
    # ------------------

    def buildRig(self, camera_name):
        """Builds the focus puller rig using a camera name.

        :param camera_name: The camera name
        :type camera_name: str
        :return:
        :rtype:
        """
        dic_focusPuller = focuspuller.buildSetup(camera_name)
        focus_ctrl_grp = dic_focusPuller["focusCtrlGrp"]
        focus_ctrl = dic_focusPuller["focusCtrl"]
        plane_ctrl_grp = dic_focusPuller["planeCtrlGrp"]
        plane_ctrl = dic_focusPuller["planeCtrl"]
        parent_constraint = dic_focusPuller["parentConstraint"]
        point_constraint = dic_focusPuller["pointConstraint"]
        multiDiv_node = dic_focusPuller["muiltdiv"]
        master_grp = dic_focusPuller["masterGrp"]
        grid_plane = dic_focusPuller["gridPlane"]

        self.connectAttributesStr(camera_name, focus_ctrl_grp, focus_ctrl,
                                  plane_ctrl_grp, plane_ctrl, parent_constraint,
                                  point_constraint, multiDiv_node, master_grp, grid_plane)

        self.selectFocusCtrl()

    # ------------------
    # Delete RIG
    # ------------------

    def safeDelete(self, attr):
        """Deletes a zapi node if it is connected to an attribute, passes if None

        :param attr:
        :type attr:
        """
        node = attr.sourceNode()
        if not node:
            return
        node.delete()

    def safeDeleteAttr(self, nodeStr, attr):
        try:
            cmds.deleteAttr(".".join([nodeStr, attr]))
        except ValueError:
            pass

    def deleteAddedAttr(self):
        pass

    def deleteAttr(self, ):
        """Deleting the attributes connecting to the meta node except for the camera"""
        # Deleting Nodes
        for attr in DELETE_LIST:
            self.safeDelete(self.attribute(attr))

        # Deleting Custom Attrs On the Transform Node
        focuspuller.deleteCameraFocusAttrs(self.getCameraStr())

        # Deletes the Meta Node
        self.delete()

        cmds.select(clear=True)


# ------------------
# Finding Meta Nodes to selected
# ------------------


def selectedMetaNodes():
    """Returns all meta nodes related to the selection

    :param zapiNodes: Maya nodes as zapi objects
    :type zapiNodes: list(object)
    """
    return getMetaClass(zapi.selected())


def getMetaFromZapi(zapiNode):
    """Returns all meta nodes related to a single zapiNode of any renderer type

    :param zapiNodes: Maya nodes as zapi objects
    :type zapiNodes: list(object)
    """
    return getMetaClass([zapiNode])


def getMetasFromName(camera_name):
    """Returns the meta nodes related to the camera string name

    :param camera_name: Maya camera string name
    :type camera_name: str
    :param zapiNodes: Maya nodes as zapi objects
    :type zapiNodes: list(object)
    """
    return getMetaClass([zapi.nodeByName(camera_name)])


def getMetaClass(zapiNodes):
    """Returns all meta nodes related to zapiNodes of any renderer type

    :param zapiNodes: Maya nodes as zapi objects
    :type zapiNodes: list(object)
    """
    return [i for i in base.metaNodeFromZApiObjects(zapiNodes) if i.mClassType() in META_CLASS_TYPES]


def metaRenderer(meta):
    """Returns the renderer as a string from a meta node

    :param meta: A focus puller meta node
    :type meta: ZooFocusPuller
    :return renderer: The renderer type of the meta node eg "Arnold"
    :rtype renderer: str
    """
    classType = meta.mClassType()
    if classType == "ZooFocusPullerArnold":
        return "Arnold"
    elif classType == "ZooFocusPullerRedshift":
        return "Redshift"
    elif classType == "ZooFocusPullerRenderman":
        return "Renderman"
    else:  # ZooFocusPuller
        return "Viewport"


def allMetaScene():
    """Returns all meta nodes in the scene of all renderer types.

    :return metaNodes: All metaNodes in the scene, all renderer types
    :rtype metaNodes: list(ZooFocusPuller)
    """
    metaNodes = list()
    for classType in META_CLASS_TYPES:
        metaNodes += base.findMetaNodesByClassType(classType)
    return metaNodes


def cleanupBrokenMetaNodes(message=True):
    """ Deletes any invalid or broken meta nodes in the scene. Cleanup function

    :param message: Report a message to the user?
    :type message: bool

    :return deletedMeta: All meta nodes that were deleted
    :rtype deletedMeta: list(ZooFocusPuller)
    """
    rememberSelection = cmds.ls(selection=True)
    metaNodes = allMetaScene()
    deletedMeta = list()
    if not metaNodes:
        return
    for meta in metaNodes:
        name = meta.fullPathName()
        if deleteInvalidMeta(meta, message=False):
            deletedMeta.append(name)
    if deletedMeta and message:
        output.displayInfo("{} broken Focus Puller node/s deleted: {}".format(len(deletedMeta), deletedMeta))
    cmds.select(rememberSelection, replace=True)
    return deletedMeta

# ------------------
# Checking UI inputs
# ------------------


def checkLoadedCamera():
    """Returns the first selected camera or if not selected then the focus camera.

    :return: camera name
    :rtype: :class:`zoo.libs.maya.zapi.base.DagNode`
    """
    selList = cmds.ls(selection=True, transforms=True, long=True)
    if selList:
        cams = filtertypes.filterTypeReturnTransforms(selList, shapeType="camera")
        if cams:
            return zapi.nodeByName(cams[0])
    # No cams selected so continue ------------
    camera = cameras.getFocusCamera()
    if not camera:
        output.displayWarning("Please select a camera")
        return None
    return zapi.nodeByName(camera)


def checkingInputs(camera_name, message=True):
    """ Does the object exist in the scene

    :param camera_name: Camera Name
    :type camera_name: Str
    :return exists: True if it exists, False if not
    :rtype exists: bool
    """
    if not cmds.objExists(camera_name):
        if message:
            output.displayWarning("{} does not exists in scene".format(camera_name))
        return False
    return True


def checkObjType(name, object_type="camera"):
    if not filtertypes.shapeTypeFromTransformOrShape([name], shapeType=object_type):
        return False
    return True


def deleteInvalidMeta(metaNode, message=True):
    """Checks and deletes a broken meta setup.  Returns True if deleted

    :param metaNode: A focus puller network node
    :type metaNode: ZooFocusPuller
    :return deleted: True if the setup was broken and deleted
    :rtype deleted: bool
    """
    if not metaNode.isValid():  # Delete the meta ---------
        metaNode.deleteAddedAttr()
        metaNode.deleteAttr()
        if message:
            output.displayWarning("MetaNode Deleted: {}".format(metaNode))
        return True
    return False


def buildRigSetup(camera_name):
    """ Builds the setup for Maya (no renderer)

    :param camera_name: Camera Name
    :type camera_name: Str
    """
    metaNodes = list()
    if not checkingInputs(camera_name):
        return
    metaNodesCheck = getMetasFromName(camera_name)

    if metaNodesCheck:
        for meta in metaNodesCheck:
            if not deleteInvalidMeta(meta):
                metaNodes.append(meta)
        if metaNodes:
            renderer = metaRenderer(metaNodes[0])
            if renderer == "Viewport":
                output.displayWarning("This camera: {}; already has a Focus Distance rig. ".format(camera_name))
                return
            output.displayWarning("This camera: {}; has a Focus Distance rig in another renderer. "
                                  "Please delete and rebuild.".format(camera_name))
            return

    meta = ZooFocusPuller()
    meta.buildRig(camera_name)
    output.displayInfo("Success: Focus Distance rig created. ")


# ------------------
# Updating Values with no meta;
# ------------------


def selectCamera(camera_name):
    cameraZapi = zapi.nodeByName(camera_name)
    cmds.select(cameraZapi.fullPathName())


def depthOfField(camera, value):
    cameraShape = zapi.nodeByName(camera).shapes()[0]
    cmds.setAttr("{}.depthOfField".format(cameraShape.fullPathName()), value)


def setFocusRegionScale(camera, value):
    cameraShape = zapi.nodeByName(camera).shapes()[0]
    cmds.setAttr("{}.focusRegionScale".format(cameraShape.fullPathName()), value)


def setFStop(camera, value):
    cameraShape = zapi.nodeByName(camera).shapes()[0]
    cmds.setAttr("{}.fStop".format(cameraShape.fullPathName()), value)


def setFocusDistance(camera, value):
    cameraShape = zapi.nodeByName(camera).shapes()[0]
    cmds.setAttr("{}.focusDistance".format(cameraShape.fullPathName()), value)


def getDOF(camera):
    cameraShape = zapi.nodeByName(camera).shapes()[0]
    return cameraShape.depthOfField.value()


def getFocusDistance(camera):
    cameraShape = zapi.nodeByName(camera).shapes()[0]
    return cmds.getAttr("{}.focusDistance".format(cameraShape.fullPathName()))


def getFStopValue(camera):
    cameraShape = zapi.nodeByName(camera).shapes()[0]
    return cameraShape.fStop.value()


def getRegionScale(camera):
    cameraShape = zapi.nodeByName(camera).shapes()[0]
    return cameraShape.focusRegionScale.value()
