import maya.cmds as cmds
from zoo.libs.maya.cmds.rig import controls
from zoo.libs.maya.cmds.objutils.attributes import MAYA_TRANSFORM_ATTRS, MAYA_SCALE_ATTRS
from zoo.libs.maya import zapi, triggers
from zoo.libs.maya.cmds.objutils import attributes, namehandling


def deleteCameraFocusAttrs(cameraTransform):
    """ Removes attributes in case they already exist on a focus puller camera.

    :param cameraTransform: A maya camera name
    :type cameraTransform: str
    """
    attrList = ["_", "__", "dofCtrlVis", "dofPlaneVis", "dofVis", "dofFocusDistance", "dofFStop",
                "dofFocusRegionScale", "focusCtrlScale", "gridVis"]
    for attr in attrList:
        try:
            cmds.setAttr(".".join([cameraTransform, attr]), lock=False)  # Unlock
            cmds.deleteAttr(".".join([cameraTransform, attr]))
        except ValueError:
            return
        except RuntimeError:
            return


def focusDistanceConnected(camera_name):
    """Checks to see if the focusDistance attribute has keys or connections

    :param camera_name: Transform name of a maya camera
    :type camera_name: str
    :return isConnected: True if the focusDistance attr of the shape node is connected.
    :rtype isConnected: bool
    """
    cameraShape = cmds.listRelatives(camera_name, fullPath=True)[0]
    if cmds.listConnections("{}.focusDistance".format(cameraShape), destination=False, source=True):
        return True
    return False


def buildSetup(camera_name):
    """
    :param camera_name: The Camera that will used
    :type camera_name: str
    :return:
    :rtype: dict
    """
    cameraShape = cmds.listRelatives(camera_name, fullPath=True)[0]
    rotAxis = cmds.getAttr("{}.rotateAxis".format(camera_name))[0]
    # Creating focus control visual
    camShort = namehandling.getShortName(camera_name)
    myControl = controls.createControlCurve(folderpath="",
                                            ctrlName="{}_focus_ctrl".format(camShort),
                                            curveScale=(0.25, 0.25, 0.25),
                                            designName="locator",
                                            addSuffix=False,
                                            shapeParent=None,
                                            rotateOffset=(90.0, 0.0, 0.0),
                                            trackScale=True,
                                            lineWidth=-1,
                                            rgbColor=(0.893, 0.408, 0.545),
                                            addToUndo=True)
    focus_ctrl_grp, focus_ctrl, focus_ctrl_grpUuid, focus_ctrl_objUuid = controls.groupInPlace(myControl[0])

    # Creating focus plane visual
    myPlane = controls.createControlCurve(folderpath="",
                                          ctrlName="{}_focus_plane".format(camShort),
                                          curveScale=(1.0, 1.0, 1.0),
                                          designName="square_focus",
                                          addSuffix=False,
                                          shapeParent=None,
                                          rotateOffset=(90.0, 0.0, 0.0),
                                          trackScale=True,
                                          lineWidth=-1,
                                          rgbColor=(0.893, 0.408, 0.545),
                                          addToUndo=True)
    plane_ctrl_grp, plane_ctrl, plane_ctrl_grpUuid, plane_ctrl_objUuid = controls.groupInPlace(myPlane[0])

    focusZapi = zapi.nodeByName(focus_ctrl)
    focusGrpZapi = zapi.nodeByName(focus_ctrl_grp)
    planeZapi = zapi.nodeByName(plane_ctrl)
    planeGrpZapi = zapi.nodeByName(plane_ctrl_grp)

    # Cameras can have rotation offsets so match the focusGrpZapi to match
    cmds.setAttr("{}.rotate".format(focus_ctrl_grp), rotAxis[0], rotAxis[1], rotAxis[2], type="double3")

    # Grouping the groups
    groupList = [focus_ctrl_grp, plane_ctrl_grp]
    master_grp = cmds.group(groupList, name="{}_focus_puller_grp".format(camShort))

    # Get full path names of controls after group
    focus_ctrl = focusZapi.fullPathName()
    focus_ctrl_grp = focusGrpZapi.fullPathName()
    plane_ctrl = planeZapi.fullPathName()
    plane_ctrl_grp = planeGrpZapi.fullPathName()

    # Matching Plane to Camera
    cmds.matchTransform(plane_ctrl_grp, camera_name, position=True, rotation=True)
    parent_constraint = cmds.parentConstraint(camera_name, plane_ctrl_grp)[0]
    # cameras can have rotation offsets (from UE) so match the constraint offset too.
    cmds.setAttr("{}.target[0].targetOffsetRotate".format(parent_constraint),
                 rotAxis[0], rotAxis[1], rotAxis[2],
                 type="double3")
    point_constraint = cmds.pointConstraint(focus_ctrl, plane_ctrl)[0]

    # Removing connection with translateX and translateY; locking and hiding everything expect translateZ
    onlyZTranslate(point_constraint, plane_ctrl)

    # Setup depth of Field
    multiDiv_node = setDepthOfField(camera_name, plane_ctrl)

    # Adding Plane
    focusPlane_obj = creatingObjPlane(plane_ctrl, plane_ctrl_grp)
    cmds.setAttr("{}.template".format(focusPlane_obj), 1)

    # Remove any existing attrs as they may already exist from a previous setup
    deleteCameraFocusAttrs(camera_name)

    # Add Title DOF Settings
    attributes.labelAttr("DOF", camera_name, checkExists=False)
    attributes.addProxyAttribute(camera_name, cameraShape, "focusDistance", proxyAttr="dofFocusDistance", channelBox=True)
    attributes.addProxyAttribute(camera_name, cameraShape, "fStop", proxyAttr="dofFStop", channelBox=True)
    attributes.addProxyAttribute(camera_name, cameraShape, "focusRegionScale", proxyAttr="dofFocusRegionScale",
                                 channelBox=True)

    # Add Title DOF Ctrl Scale
    attributes.labelAttr("Controls", camera_name, checkExists=False)

    # Add Control Visibility Attributes, make non-keyable in the channel box
    attributes.addProxyAttribute(camera_name, focus_ctrl, "visibility", proxyAttr="dofCtrlVis", channelBox=False)
    cmds.setAttr("{}.dofCtrlVis".format(camShort), channelBox=True)

    attributes.addProxyAttribute(camera_name, plane_ctrl, "visibility", proxyAttr="dofPlaneVis", channelBox=True)
    cmds.setAttr("{}.dofPlaneVis".format(camera_name), channelBox=True)

    attributes.addProxyAttribute(camera_name, focusPlane_obj, "visibility", proxyAttr="gridVis", channelBox=True)
    cmds.setAttr("{}.gridVis".format(camera_name), channelBox=True)

    attributes.addProxyAttribute(camera_name, cameraShape, "depthOfField", proxyAttr="dofVis", channelBox=True)
    cmds.setAttr("{}.dofVis".format(camera_name), channelBox=True)

    attributes.addProxyAttribute(focus_ctrl, plane_ctrl, "visibility", proxyAttr="planeVis", channelBox=True)
    cmds.setAttr("{}.planeVis".format(focus_ctrl), channelBox=True)

    attributes.addProxyAttribute(plane_ctrl, focus_ctrl, "visibility", proxyAttr="ctrlVis", channelBox=True)
    cmds.setAttr("{}.ctrlVis".format(plane_ctrl), channelBox=True)

    attributes.addProxyAttribute(plane_ctrl, focusPlane_obj, "visibility", proxyAttr="gridVis", channelBox=True)
    cmds.setAttr("{}.gridVis".format(plane_ctrl), channelBox=True)

    cmds.addAttr(camera_name, longName="focusCtrlScale", niceName="Focus Ctrl Scale", minValue=0.1, defaultValue=1,
                 keyable=False)
    cmds.setAttr("{}.focusCtrlScale".format(camera_name), channelBox=True)

    # Connecting Attributes -----------------------
    for attr in MAYA_SCALE_ATTRS:
        cmds.connectAttr("{}.{}".format(focus_ctrl, attr), "{}.{}".format(plane_ctrl, attr))

    for attr in MAYA_SCALE_ATTRS:
        cmds.connectAttr("{}.{}".format(camera_name, "focusCtrlScale"), "{}.{}".format(focus_ctrl, attr))

    for attr in MAYA_SCALE_ATTRS:
        cmds.connectAttr("{}.{}".format(plane_ctrl, attr), "{}.{}".format(focusPlane_obj, attr))

    # Quality of Life changes ---------------
    cmds.matchTransform(focus_ctrl, camera_name, position=True, rotation=True, scale=False)

    cmds.move(0, 0, -50, focus_ctrl, relative=True, localSpace=True, worldSpaceDistance=True)
    triggerSelection(plane_ctrl, focus_ctrl)
    for attr in MAYA_SCALE_ATTRS:
        cmds.setAttr("{}.{}".format(focus_ctrl, attr), lock=True, keyable=False, channelBox=False)

    cmds.setAttr("{}.gridVis".format(camera_name), 0)

    focusPullerDict = {"focusCtrlGrp": focus_ctrl_grp, "focusCtrl": focus_ctrl,
                       "planeCtrlGrp": plane_ctrl_grp, "planeCtrl": plane_ctrl,
                       "parentConstraint": parent_constraint, "pointConstraint": point_constraint,
                       "muiltdiv": multiDiv_node, "masterGrp": master_grp, "gridPlane": focusPlane_obj}

    return focusPullerDict


# ------------------------
# Helper Functions
# ------------------------

def onlyZTranslate(point_constraint, plane_ctrl, visible=True):
    """Hides all attrs on the plane control except for translateZ and visibility.

    :param point_constraint: The point constraint between the camera and the plane control group
    :type point_constraint: str
    :param plane_ctrl: The plane control
    :type plane_ctrl: str
    :param visible: Are the controls visible
    :type visible: bool
    :return:
    :rtype:
    """
    cmds.disconnectAttr("{}.constraintTranslateX".format(point_constraint),
                        "{}.{}".format(plane_ctrl, MAYA_TRANSFORM_ATTRS[0]))
    cmds.disconnectAttr("{}.constraintTranslateY".format(point_constraint),
                        "{}.{}".format(plane_ctrl, MAYA_TRANSFORM_ATTRS[1]))
    cmds.setAttr("{}.{}".format(plane_ctrl, MAYA_TRANSFORM_ATTRS[0]), 0)
    cmds.setAttr("{}.{}".format(plane_ctrl, MAYA_TRANSFORM_ATTRS[1]), 0)

    for attr in MAYA_TRANSFORM_ATTRS:  # TODO can be far simpler
        if attr == "translateZ":
            cmds.setAttr("{}.{}".format(plane_ctrl, attr), lock=True)
            continue
        if attr.__contains__("scale"):
            cmds.setAttr("{}.{}".format(plane_ctrl, attr), keyable=False, channelBox=False)
            continue
        cmds.setAttr("{}.{}".format(plane_ctrl, attr), lock=True, keyable=False, channelBox=False)

    if not visible:
        cmds.setAttr("{}.visibility".format(plane_ctrl), keyable=False, channelBox=False)


def gettingShape(camera_name):
    """ Returning the Camera shape node
    :param camera_name: the camera name
    :type camera_name: str
    :return: camera shape node
    :rtype: str
    """
    return cmds.listRelatives(camera_name, allDescendents=True, path=True)[0]


def setDepthOfField(camera_name, plane_ctrl):
    """
    :param camera_name: The camera name
    :type camera_name: str
    :param plane_ctrl: the plane control name
    :type plane_ctrl: str
    :return: multiply divide node
    :rtype: node
    """
    camera_shapeNode = gettingShape(camera_name)
    cmds.setAttr("{}.depthOfField".format(camera_shapeNode), 1)

    multiplyDivide_node = cmds.shadingNode("multiplyDivide", asUtility=True)
    cmds.connectAttr("{}.translateZ".format(plane_ctrl), "{}.input1.input1X".format(multiplyDivide_node))
    cmds.setAttr("{}.input2X".format(multiplyDivide_node), -1)

    cmds.connectAttr("{}.output.outputX".format(multiplyDivide_node), "{}.focusDistance".format(camera_shapeNode))

    return multiplyDivide_node


def creatingObjPlane(focusPlane, focusPlaneGrp):
    """Creates the grid plane object

    :param focusPlane: The focus plane control
    :type focusPlane: str
    :param focusPlaneGrp: The focus plane control's group
    :type focusPlaneGrp: str
    :return objPlane_name: The grid plane's transform node
    :rtype objPlane_name: str
    """
    objPlane_name = cmds.polyPlane(width=50, height=50, subdivisionsX=20, subdivisionsY=20)[0]
    cmds.parent(objPlane_name, focusPlane)
    cmds.matchTransform(objPlane_name, focusPlane, position=True, rotation=True, scale=False)
    cmds.setAttr("{}.rotateX".format(objPlane_name), 90)
    cmds.makeIdentity(objPlane_name, apply=True)
    cmds.parent(objPlane_name, focusPlaneGrp)
    cmds.parentConstraint(focusPlane, objPlane_name, maintainOffset=False)
    return objPlane_name


def triggerSelection(triggerName, selectName):
    _testNode = zapi.nodeByName(triggerName)
    selectableNode = zapi.nodeByName(selectName)
    triggers.createSelectionTrigger([_testNode], connectables=[selectableNode])
