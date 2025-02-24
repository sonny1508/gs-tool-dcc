from maya import cmds as cmds
from zoo.libs.maya import zapi
from zoo.libs.maya.cmds.rig import controls, controlconstants
from zoo.libs.maya.cmds.objutils import namehandling, filtertypes, attributes, shapenodes
from zoo.libs.maya.cmds.objutils.constraints import MOPATH_PATH_ATTR, MOPATH_FRONTTWIST_ATTR, MOPATH_UPTWIST_ATTR, \
    MOPATH_SIDETWIST_ATTR, POS_ROT_ATTRS
from zoo.libs.utils import output

WORLD_UP_TYPES = ["scene", "object", "objectrotation", "vector", "normal"]


def createGroupMatchParent(obj, suffixName="_grp", maintainOffset=False, parentObjOverride="", noParent=False):
    """Creates a grp matched to the obj, then parents it under the same parent.

    :param obj: A Maya object transform, preferably a long name string
    :type obj: str
    :param suffixName: The grp will be named the same as the object with a suffix, this is the suffix
    :type suffixName: str
    :param maintainOffset: Won't match the object to the group
    :type maintainOffset: bool
    :param parentObjOverride:
    :type parentObjOverride: str

    :return grp: The new group that was created, will be a unique name
    :rtype grp: str
    """
    grpName = "_".join([namehandling.getShortName(obj), suffixName])
    grpName = namehandling.nonUniqueNameNumber(grpName)
    grp = cmds.group(name=grpName, empty=True)
    if not maintainOffset:
        cmds.matchTransform(([grp, obj]), pos=1, rot=1, scl=1, piv=0)
    if noParent:
        return grp
    grpZapi = zapi.nodeByName(grp)
    if not parentObjOverride:
        parent = cmds.listRelatives(obj, parent=True)
    else:
        parent = cmds.listRelatives(parentObjOverride, parent=True)
    if parent:
        cmds.parent(grp, parent[0])
    return grpZapi.fullPathName()


def createMotionPathRig(obj, curve, group=True, controlObj="", attrName=MOPATH_PATH_ATTR, followAxis="z", upAxis="y",
                        worldUpVector=(0, 1, 0), worldUpObject="", worldUpType=3, frontTwist=True, upTwist=True,
                        sideTwist=True, parentConstrain=False, maintainOffset=False, follow=True):
    """Creates a motion path and creates an attribute on the controlObj.  Makes motion paths a lot easier to animate.
    If no controlObj will create the attribute on the obj.

    Various options for either constraining to the motion path object or parenting under the motion path object:

        group=True, parentConstrain=True - The object is grouped and the group is parent constrained to the follow grp.
        group=False, parentConstrain=True - The object parent constrained to the follow grp which has the motion path.
        group=True, parentConstrain=False - The object is parented under the follow grp which has the motion path.
        group=False, parentConstrain=False - The object has the motion path directly connected to it and attrs added.

    Animatable attributes are always added to the main object "obj", unless a "controlObj" is specified.

    :param obj: The object to attach to a motion path
    :type obj: str
    :param curve: The curve that will be the motion path
    :type curve: str
    :param controlObj: Optional object that the attribute will be assigned to, might be a control, if empty will be obj
    :type controlObj: str
    :param attrName: The name of the attribute that will control the animation, default is "path"
    :type attrName: str
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
    :param frontTwist: Add the attr frontTwist to the controlObj?
    :type frontTwist: bool
    :param upTwist: Add the attr frontTwist to the controlObj?
    :type upTwist: bool
    :param sideTwist: Add the attr frontTwist to the controlObj?
    :type sideTwist: bool
    :param parentConstrain: parent constriain the obj, or obj's group, to a follow group which has the motion path
    :type parentConstrain: bool
    :param maintainOffset: Will keep the object in it's current location, only if parent constrained or grouped.
    :type maintainOffset: bool
    :param follow: Will rotation follow the path, if off only translation is controlled.
    :type follow: bool

    :return motionPath: The motionPath node that was created
    :rtype motionPath: str
    :return obj: The obj possible new long name because of parenting
    :rtype obj: str
    :return followGrp: The group that has the motion path on it. Created if group or parentConstrain.
    :rtype followGrp: str
    :return parentConstrainGrp: The group parent constrained to the follow group. Created if group and parentConstrain.
    :rtype parentConstrainGrp: str
    :return controlObj: The controlObj that receives the attributes. May have a new long name because of parenting.
    :rtype controlObj: str
    :return constraint: The parent constraint name. Created if parentConstrain.
    :rtype constraint: str
    """
    followGrp = ""
    parentConstrainGrp = ""
    constraint = ""
    inverseFront = False
    inverseUp = False
    if followAxis.startswith("-"):
        inverseFront = True
        followAxis = followAxis[1]
    if upAxis.startswith("-"):
        inverseUp = True
        upAxis = upAxis[1]
    if group:  # build and parent the group/s, track the names ----------------------------------------
        if controlObj:  # This may get re-parented, so track the name with zapi!
            controlZapi = zapi.nodeByName(controlObj)
        if parentConstrain:
            followGrp = createGroupMatchParent(obj, suffixName="grp", maintainOffset=maintainOffset)
        else:
            followGrp = createGroupMatchParent(obj, suffixName="follow_grp", maintainOffset=maintainOffset)
        obj = cmds.parent(obj, followGrp)[0]  # always parent as object is being grouped
        if controlObj:
            controlObj = controlZapi.fullPathName()
        if parentConstrain:  # Make the parentConstrainGrp the current followGrp, followGrp is made again later
            parentConstrainGrp = str(followGrp)

    if parentConstrain:  # Then create the parent constraints ----------------------------------------
        followGrp = createGroupMatchParent(obj, suffixName="follow_grp", parentObjOverride=curve, noParent=True)
        if group:  # parentConstrainGrp will exist
            if follow:
                constraint = cmds.parentConstraint(followGrp, parentConstrainGrp)[0]
            else:
                constraint = cmds.pointConstraint(followGrp, parentConstrainGrp)[0]
        else:
            if follow:
                constraint = cmds.parentConstraint(followGrp, obj)[0]
            else:
                constraint = cmds.pointConstraint(followGrp, obj)[0]

    # Figure the control object and the obj to set on the motion path ---------------------------------
    if not controlObj and not group and not parentConstrain:
        controlObj = str(obj)
        moPathObj = str(obj)
    elif not controlObj and not group and parentConstrain:
        controlObj = str(obj)
        moPathObj = followGrp
    elif not controlObj and group:
        controlObj = str(obj)
        moPathObj = followGrp
    elif not controlObj and parentConstrain:
        controlObj = str(obj)
        moPathObj = followGrp
    elif not parentConstrain and not group:
        controlObj = str(obj)
        moPathObj = str(obj)
    else:  # ControlObj and group
        moPathObj = str(followGrp)

    # Build and connect the motion path -------------------------------------------------------------
    if follow:
        if not worldUpObject:
            worldUpObject = None
        motionPath = cmds.pathAnimation(moPathObj, curve=curve, followAxis=followAxis, upAxis=upAxis,
                                        worldUpVector=worldUpVector, worldUpObject=worldUpObject,
                                        worldUpType=WORLD_UP_TYPES[worldUpType], fractionMode=True, follow=True)
        cmds.setAttr("{}.inverseFront".format(motionPath), inverseFront)  # cmds.pathAnimation() inverseFront bug
        cmds.setAttr("{}.inverseUp".format(motionPath), inverseUp)  # cmds.pathAnimation() inverseUp bug
    else:
        motionPath = cmds.pathAnimation(moPathObj, curve=curve, fractionMode=True, follow=False)
    cmds.cutKey(motionPath, s=True)  # delete animation

    # Add attributes and make the connections --------------------------------------------------------
    if not cmds.attributeQuery(attrName, node=controlObj, exists=True):
        cmds.addAttr(controlObj, longName=attrName, minValue=0.0, maxValue=1.0, keyable=True)
    cmds.connectAttr(".".join([controlObj, attrName]), "{}.uValue".format(motionPath))
    if not follow:
        return motionPath, obj, followGrp, parentConstrainGrp, controlObj, constraint
    if frontTwist and follow:
        if not cmds.attributeQuery(MOPATH_FRONTTWIST_ATTR, node=controlObj, exists=True):
            cmds.addAttr(controlObj, longName=MOPATH_FRONTTWIST_ATTR, keyable=True)
        cmds.connectAttr(".".join([controlObj, MOPATH_FRONTTWIST_ATTR]), ".".join([motionPath, "frontTwist"]))
    if upTwist and follow:
        if not cmds.attributeQuery(MOPATH_UPTWIST_ATTR, node=controlObj, exists=True):
            cmds.addAttr(controlObj, longName=MOPATH_UPTWIST_ATTR, keyable=True)
        cmds.connectAttr(".".join([controlObj, MOPATH_UPTWIST_ATTR]), ".".join([motionPath, "upTwist"]))
    if sideTwist and follow:
        if not cmds.attributeQuery(MOPATH_SIDETWIST_ATTR, node=controlObj, exists=True):
            cmds.addAttr(controlObj, longName=MOPATH_SIDETWIST_ATTR, keyable=True)
        cmds.connectAttr(".".join([controlObj, MOPATH_SIDETWIST_ATTR]), ".".join([motionPath, "sideTwist"]))
    return motionPath, obj, followGrp, parentConstrainGrp, controlObj, constraint


def createMotionPathRigSel(curve="", group=True, attrName=MOPATH_PATH_ATTR, followAxis="z", upAxis="y",
                           worldUpVector=(0, 1, 0), worldUpObject="", worldUpType=3, frontTwist=True, upTwist=True,
                           sideTwist=True, parentConstrain=False, maintainOffset=False, follow=True, message=True):
    """Creates a motion path and creates an attribute on the controlObj from the current selection and a potential UI.
    Makes motion paths a lot easier to create and animate by copying the driving attributes onto the object itself.

    Supports multiple object selection, the curve path object should be selected last if it not given directly.

    :param curve: The curve that will be the motion path
    :type curve: str
    :param group: Group the object so that the motion path is on the group, not on the selected objects
    :type group: bool
    :param attrName: The name of the attribute that will control the animation, default is "path"
    :type attrName: str
    :param followAxis: The axis to follow, default is "z", can be "x", "y" or "z"
    :type followAxis: str
    :param upAxis: The up vector axis
    :type upAxis:
    :param worldUpVector: The up vector x, y, z as a list or tuple (0, 1, 0)
    :type worldUpVector: tuple(float)
    :param frontTwist: Add the attr frontTwist to the controlObj?
    :type frontTwist: bool
    :param upTwist: Add the attr frontTwist to the controlObj?
    :type upTwist: bool
    :param sideTwist: Add the attr frontTwist to the controlObj?
    :type sideTwist: bool
    :param parentConstrain: parent constrain the obj, or obj's group, to a follow group which has the motion path
    :type parentConstrain: bool
    :param maintainOffset: Will keep the object in it's current location, only if parent constrained or grouped.
    :type maintainOffset: bool
    :param follow: Will rotation follow the path, if off only translation is controlled.
    :type follow: bool
    :param message: Report a message to the user?
    :type message: bool

    :return motionPaths: The motionPath node that was created
    :rtype motionPaths: str
    :return objs: The obj possible new long name because of parenting
    :rtype objs: str
    :return followGrps: The group that has the motion path on it. Created if group or parentConstrain.
    :rtype followGrps: str
    :return parentConstrainGrps: The group parent constrained to the follow group. Created if group and parentConstrain.
    :rtype parentConstrainGrps: str
    :return controlObjs: The controlObj that receives the attributes. May have a new long name because of parenting.
    :rtype controlObjs: str
    :return constraints: The parent constraint name. Created if parentConstrain.
    :rtype constraints: str
    """
    # TODO: Check referenced
    # TODO: Auto create controls and add upvector control
    # TODO: Add meta and UI interactivity
    # TODO: Add no rotate option (if constrained) for cameras
    controlObjs = list()
    newObjs = list()
    objs = list()
    followGrps = list()
    parentConstrainGrps = list()
    constraints = list()
    motionPaths = list()
    objList = cmds.ls(selection=True)
    # Error checking ----------------------------------
    if not objList:
        if message:
            output.displayInfo("Please select objects to add motion paths.  Select the object/s then the path curve.")
        return motionPaths, newObjs, followGrps, parentConstrainGrps, controlObjs, constraints
    if not curve:
        curve = objList[-1]
        objList.pop(-1)
    if not objList:
        if message:
            output.displayInfo(
                "Please select at least two objects to create a motion path, only one object is selected.")
        return motionPaths, objs, followGrps, controlObjs, constraints
    if not filtertypes.filterTypeReturnTransforms([curve]):
        if message:
            output.displayWarning("The object `{}` is not a nurbsCurve, please select a curve.".format(curve))
        return motionPaths, newObjs, followGrps, parentConstrainGrps, controlObjs, constraints
    transformList = filtertypes.filterExactTypeList(objList, type="transform")
    if not objList:
        if message:
            output.displayWarning("The objects `{}` do not contain transforms, please select objects that can be "
                                  "attached to motion paths.".format(objList))
        return motionPaths, newObjs, followGrps, parentConstrainGrps, controlObjs, constraints
    if group:
        for transform in transformList():
            if cmds.referenceQuery(transform, isNodeReferenced=True):
                if message:
                    output.displayWarning(
                        "The object `{}` is referenced and cannot be grouped. "
                        "Please uncheck `Group Control Obj`.".format(objList))
                return motionPaths, newObjs, followGrps, parentConstrainGrps, controlObjs, constraints

    # Check for connections, locked attrs ------------------
    lockedNodes, lockedAttrs = attributes.getLockedConnectedAttrsList(transformList, POS_ROT_ATTRS, keyframes=True)
    if lockedAttrs and not group:
        if message:
            output.displayWarning("Motion paths cannot be created as these attributes are "
                                  "locked, animated or connected: {}".format(lockedAttrs))
        return motionPaths, newObjs, followGrps, parentConstrainGrps, controlObjs, constraints

    # Create the motion paths ---------------------------------------------
    for transform in transformList:
        controlObj = str(transform)
        motionPath, obj, followGrp, \
        parentConstrainGrp, controlObj, constraint = createMotionPathRig(transform, curve,
                                                                         group=group,
                                                                         attrName=attrName,
                                                                         followAxis=followAxis,
                                                                         upAxis=upAxis,
                                                                         controlObj=controlObj,
                                                                         worldUpVector=worldUpVector,
                                                                         worldUpObject=worldUpObject,
                                                                         worldUpType=worldUpType,
                                                                         frontTwist=frontTwist,
                                                                         upTwist=upTwist,
                                                                         sideTwist=sideTwist,
                                                                         follow=follow,
                                                                         parentConstrain=parentConstrain,
                                                                         maintainOffset=maintainOffset)
        motionPaths.append(motionPath)
        controlObjs.append(controlObj)
        followGrps.append(followGrp)
        parentConstrainGrps.append(parentConstrainGrp)
        newObjs.append(obj)
        constraints.append(constraint)

    if controlObjs:
        cmds.select(controlObjs, replace=True)

    if message:
        shortNames = namehandling.getShortNameList(controlObjs)
        output.displayInfo("Success: Objects are now connected to motion paths `{}`".format(shortNames))
    return motionPaths, newObjs, followGrps, parentConstrainGrps, controlObjs, constraints


def setCurveObj(obj):
    """Checks the curve given in the UI is a curve and it exists with a unique name.

    :param obj: An object name from the UI
    :type obj: str
    :return: nurbs curve object, empty string if not found or not a curve.
    :rtype: str
    """
    if not cmds.objExists(obj):
        output.displayWarning("Object `{}` not found in the scene.".format(obj))
        return ""
    if not namehandling.nameIsUnique(obj):
        output.displayWarning("This object name is not unique `{}`. "
                              "Use shift-select and the button to enter the selected object.".format(obj))
        return ""
    if not filtertypes.shapeTypeFromTransformOrShape([obj], shapeType="nurbsCurve"):
        output.displayWarning("The object `{}` is not a nurbs curve.".format(obj))
        return ""
    return obj


def setCurveObjSelection():
    """Returns the curve for UI code. Must be a nurbsCurve object.

    :return surfaceObject: The first selected nurbsCurve object.
    :rtype surfaceObject: str
    """
    selObjs = cmds.ls(selection=True, transforms=True)
    if not selObjs:
        output.displayWarning("Nothing selected. Please select a nurbsCurve object.")
        return ""
    selObjs.reverse()
    for obj in selObjs:
        if filtertypes.shapeTypeFromTransformOrShape([obj], shapeType="nurbsCurve"):
            return obj
    output.displayWarning("NurbsSurface object not found in selection, please select a nurbsCurve")
    return ""


def setUpObj(obj):
    """Checks the object given in the UI is a transform and it exists with a unique name.

    :param obj: An object name from the UI
    :type obj: str
    :return: a transform node object, empty string if not found or not a transform.
    :rtype: str
    """
    if not cmds.objExists(obj):
        output.displayWarning("Object `{}` not found in the scene.".format(obj))
        return ""
    if not namehandling.nameIsUnique(obj):
        output.displayWarning("This object name is not unique `{}`. "
                              "Use the button to enter the selected object.".format(obj))
        return ""
    if not cmds.nodeType(obj) == "transform":
        output.displayWarning("The object `{}` is not a transform.  Please select an object".format(obj))
        return ""
    return obj


def setUpObjSelection(selectLast=True):
    """Returns an object for UI code. Must be a transform node.

    :return surfaceObject: The first selected object (transfrom node)
    :rtype surfaceObject: str
    """
    selObjs = cmds.ls(selection=True, transforms=True)
    if not selObjs:
        output.displayWarning("Nothing selected. Please select an object (transform).")
        return ""
    if selectLast:
        return selObjs[-1]
    return selObjs[0]


# ---------------
# CONTROLS
# ---------------


def createArrowControl(ctrlName, controlScale):
    """Creates an arrow control for the up vector, with pivot correctly placed.

    :param ctrlName: The name of the arrow control
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
                                           rgbColor=None,
                                           addToUndo=True)[0]
    shapenodes.translateObjListCVs([upVArrow], [0.0, controlScale, 0.0])
    upVGrp, upVArrow, grpUuid, objUuid = controls.groupInPlace(upVArrow, grpSwapSuffix=True)
    return upVGrp, upVArrow
