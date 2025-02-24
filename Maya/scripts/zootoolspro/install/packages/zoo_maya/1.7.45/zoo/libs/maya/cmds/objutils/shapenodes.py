import maya.cmds as cmds
from zoo.libs.maya.cmds.objutils import attributes

from zoo.libs.maya import zapi
from zoo.libs.utils import output
from zoo.libs.maya.utils import mayaenv

from zoo.libs.maya.cmds.objutils import filtertypes, namehandling, objhandling, matrix

SHAPENODES_WITH_COLOR = ["nurbsCurve", "locator", "mesh", "nurbsSurface", "camera", "light"]
SHAPENODES_WITH_COLOR += filtertypes.DEFORMER_TYPE_LIST

# TODO plugin light types SHAPENODES_WITH_COLOR += filterTypes.LIGHT_TYPE_LIST

MAYA_VERSION = float(mayaenv.mayaVersionNiceName())


def getTransform(shapeNode):
    """returns the transform node from a shape node name

    :param shapeNode: maya shape node name
    :type shapeNode: str
    :return transformNode: maya transform node name
    :rtype transformNode: str
    """
    return cmds.listRelatives(shapeNode, type="transform")


def getTransformList(shapeNodeList, eliminateDoubleNames=True):
    """returns a transformList from the shapeNodeList
    no doubled up names returned by default

    :param shapeNodeList: list of maya shape node names
    :type shapeNodeList: list
    :return transformList: list of maya transform node names
    :rtype transformList: list
    """
    transformList = list()
    for shapeNode in shapeNodeList:
        transformList.append(cmds.listRelatives(shapeNode, parent=True, type="transform")[0])
    if eliminateDoubleNames:
        transformList = list(set(transformList))  # make unique
    return transformList


def transformHasShapeOfType(node, nodeType):
    """Checks to see if the node, or shape nodes of the current node is a match to nodeType ie "nurbsCurve"

    :param node: a maya node name
    :type node: str
    :param nodeType: the nodeType to match, ie "nurbsCurve"
    :type nodeType: str
    :return shapeNodeName: The name of the shape node found, if not returns an empty string ""
    :rtype shapeNodeName: str
    """
    shapeNodeName = ""
    if cmds.nodeType(node) == nodeType:  # then this is correct
        return True
    else:  # probably a transform so check the shape nodes
        shapeNodes = cmds.listRelatives(node, shapes=True, fullPath=True)
        if not shapeNodes:
            return ""
        for shape in shapeNodes:
            if cmds.nodeType(shape) == nodeType:
                shapeNodeName = shape
                break
    if shapeNodeName:
        return shapeNodeName
    return ""


def filterShapesInList(objList, nodeTypeList=SHAPENODES_WITH_COLOR):
    """Filters a Maya object list leaving only shapes, and those shapes in the filter nodeTypeList

    :param objList: The Maya Object List
    :type objList: list
    :param nodeTypeList: Types of nodes to filter from
    :type nodeTypeList: list
    :return shapesList: The filtered shape node list
    :rtype shapesList: list
    """
    shapeObjList = list()
    for obj in objList:  # filter if objects in the list are shapes
        objType = cmds.nodeType(obj)
        if objType in nodeTypeList:
            shapeObjList.append(obj)
    shapesChildList = cmds.listRelatives(objList, shapes=True, type=(nodeTypeList),
                                         fullPath=True)  # filter child shapes
    # Since lists can be of type None check for valid lists and combine them
    if shapeObjList:
        if shapesChildList:  # if both lists valid
            shapesList = shapeObjList + shapesChildList
        else:  # only shapeObjList is valid
            shapesList = shapeObjList
    elif shapesChildList:  # only shapesChildList is valid
        shapesList = shapesChildList
    else:  # no lists are valid
        shapesList = None
    return shapesList


def translateShapeCVs(nurbsShape, translateXYZ):
    """Translate a shape node by the xyz amount [float, float, float] without affecting the transform

    :param nurbsShape: The shape node name
    :type nurbsShape: str
    :param translateXYZ: The scale in x y z [float, float, float]
    :type translateXYZ: list
    """
    cmds.move(translateXYZ[0], translateXYZ[1], translateXYZ[2], '{}.cv[*]'.format(nurbsShape),
              relative=True, objectSpace=True, worldSpaceDistance=True)


def scaleShapeCVs(nurbsShape, scaleXYZ):
    """Scales a shape node by the xyz amount [float, float, float] without affecting the transform

    :param nurbsShape: The shape node name
    :type nurbsShape: str
    :param scaleXYZ: The scale in x y z [float, float, float]
    :type scaleXYZ: list
    """
    cmds.scale(scaleXYZ[0], scaleXYZ[1], scaleXYZ[2], '{}.cv[*]'.format(nurbsShape))


def rotateShapeCVs(nurbsShape, rotateXYZ, relative=True, objectCenterPivot=True):
    """Rotates a shape node by the xyz amount [float, float, float] without affecting the transform

    :param nurbsShape: the name of the shape node, should have cvs
    :type nurbsShape: str
    :param rotateXYZ: how to rotate the cvs
    :type rotateXYZ: list
    :param relative: rotate relative to the object space, recommended
    :type relative: bool
    :param objectCenterPivot: rotate are the the objects center pivot, recommended, will be worls if False
    :type objectCenterPivot: bool
    """
    cmds.rotate(rotateXYZ[0], rotateXYZ[1], rotateXYZ[2], '{}.cv[*]'.format(nurbsShape),
                objectCenterPivot=objectCenterPivot, relative=relative)


def translateObjListCVs(mayaObjList, translateXYZ):
    """Translates an object list, usually transform nodes of nurbsCurves by the xyz amount [float, float, float]
    Doesn't affect the transform scale, scales CVs

    :param mayaObjList: List of maya object names, will filter the shape nodes from the transforms
    :type mayaObjList: list
    :param translateXYZ: The scale in x y z [float, float, float]
    :type translateXYZ: list
    """
    shapesList = filtertypes.shapeTypeFromTransformOrShape(mayaObjList, shapeType="nurbsCurve")
    for shape in shapesList:
        translateShapeCVs(shape, translateXYZ)


def scaleObjListCVs(mayaObjList, scaleXYZ):
    """Scales an object list, usually transform nodes of nurbsCurves by the xyz amount [float, float, float]
    Doesn't affect the transform scale, scales CVs

    :param mayaObjList: List of maya object names, will filter the shape nodes from the transforms
    :type mayaObjList: list
    :param scaleXYZ: The scale in x y z [float, float, float]
    :type scaleXYZ: list
    """
    shapesList = filtertypes.shapeTypeFromTransformOrShape(mayaObjList, shapeType="nurbsCurve")
    for shape in shapesList:
        scaleShapeCVs(shape, scaleXYZ)


def scaleObjListCVsSelected(scaleXYZ, message=True):
    """Scales the selection (transform nodes of nurbsCurves shapes) by the xyz amount [float, float, float]
    Doesn't affect the transform scale, scales CVs

    :param scaleXYZ: The scale in x y z [float, float, float]
    :type scaleXYZ: list
    :param message: Report the message to the user?
    :type message: bool
    """
    selObjs = cmds.ls(selection=True, long=True)
    if not selObjs:
        if message:
            output.displayWarning("Please select an object")
        return
    scaleObjListCVs(selObjs, scaleXYZ)


def rotateObjListCVs(mayaObjList, rotateXYZ, relative=True, objectCenterPivot=True):
    """Rotates an object list, usually transform nodes of nurbsCurves by the xyz amount [float, float, float]
    Doesn't affect the transform rotation, rotates CVs

    :param nurbsShape: List of maya object names, will filter the shape nodes from the transforms
    :type nurbsShape: list
    :param rotateXYZ: how to rotate the cvs
    :type rotateXYZ: list
    :param relative: rotate relative to the object space, recommended
    :type relative: bool
    :param objectCenterPivot: rotate are the the objects center pivot, recommended, will be worls if False
    :type objectCenterPivot: bool
    """
    shapesList = filtertypes.shapeTypeFromTransformOrShape(mayaObjList, shapeType="nurbsCurve")
    for shape in shapesList:
        rotateShapeCVs(shape, rotateXYZ, relative=relative, objectCenterPivot=objectCenterPivot)


def scaleSelectedObjCVs(scaleXYZ):
    """Scales selected Maya object lists cvs
    filters the nurbsCurve shapes and scales by the xyz amount [float, float, float]
    Doesn't affect the transform scale, scales CVs

    :param scaleXYZ: The scale in x y z [float, float, float]
    :type scaleXYZ: list
    """
    selobjs = cmds.ls(selection=True, long=True)
    scaleObjListCVs(selobjs, scaleXYZ)


def rotateSelectedObjCVs(rotateXYZ, relative=True, objectCenterPivot=True, message=True):
    """Rotates selected Maya object lists cvs
    filters the nurbsCurve shapes and rotates by the xyz amount [float, float, float]
    Doesn't affect the transform scale, scales CVs

    :param rotateXYZ: how to rotate the cvs
    :type rotateXYZ: list
    :param relative: rotate relative to the object space, recommended
    :type relative: bool
    :param objectCenterPivot: rotate are the the objects center pivot, recommended, will be worls if False
    :type objectCenterPivot: bool
    """
    selobjs = cmds.ls(selection=True, long=True)
    if not selobjs:
        if message:
            output.displayWarning("No objects selected, please select an object")
        return
    rotateObjListCVs(selobjs, rotateXYZ, relative=relative, objectCenterPivot=objectCenterPivot)


# ---------------------------
# SHAPE NODE PARENT
# ---------------------------


def shapeNodeParent(masterObj, sourceObj, replace=False, deleteMaster=True, objSpaceParent=False,
                    renameShapes=True, delShapeType="", ogsReset=True, instance=False):
    """Shape node parents/replaces a single object to another object.

    :param masterObj: The master object from which the shapes are parented
    :type masterObj: str
    :param sourceObj: The target object that the shapes will be parented to
    :type sourceObj: str
    :param replace: replace will replace the shape nodes of the sourObj with the nodes of the masterObj
    :type replace: bool
    :param deleteMaster: Will delete the masterObj, usually True as it's an empty transform
    :type deleteMaster: bool
    :param objSpaceParent: if True parents in local/object space, if False will parent in world space
    :type objSpaceParent: bool
    :param renameShapes: Will rename all existing shape nodes to match the transform name as per Maya
    :type renameShapes: bool
    :param delShapeType: If deleteOriginal True the shape type can be specified eg "nurbsCurve". "" empty deletes all
    :type delShapeType: str
    :param ogsReset: runs cmds.ogs(reset=True) which is a force refresh in Maya 2022.0 as it's buggy
    :type ogsReset: bool

    :return sourceObj: The object now with the new shape nodes
    :rtype sourceObj: str
    """
    if MAYA_VERSION >= 2020.0:  # check for matrix offsets
        matrix.zeroMatrixOffset(masterObj, unlockAttrs=True)
    if replace:  # Delete all the original shapes in the target object
        if objhandling.isInstancedTransform(sourceObj):  # Uninstance before deleting as may affect other instances.
            sourceObj = objhandling.uninstanceObj(sourceObj)  # source obj may bne renamed
        if not delShapeType:
            deleteShapes = cmds.listRelatives(sourceObj, fullPath=True, shapes=True)
        else:
            deleteShapes = cmds.listRelatives(sourceObj, fullPath=True, shapes=True, type=delShapeType)
        if deleteShapes:
            cmds.delete(deleteShapes)
    if not deleteMaster:  # duplicates the object so it is not deleted
        masterObj = cmds.duplicate(masterObj, instanceLeaf=instance)[0]
    if not objSpaceParent:  # Then parent in world space
        masterObj = cmds.parent(masterObj, sourceObj)
        cmds.makeIdentity(masterObj, apply=True, scale=True, rotate=True, translate=True)  # freeze
        masterObj = cmds.parent(masterObj, world=True)
    sourceShapes = cmds.listRelatives(masterObj, fullPath=True, shapes=True)
    if sourceShapes:
        for shape in sourceShapes:  # do the parent
            cmds.parent(shape, sourceObj, shape=True, relative=True)
        cmds.delete(masterObj)  # Delete the now empty transform
    if ogsReset:  # This is a bugfix in Maya 2022.0
        if MAYA_VERSION == 2022.0 or MAYA_VERSION == 2022.2:
            cmds.ogs(reset=True)  # Force refresh in Maya 2022.0 as it's buggy
    if renameShapes:
        renameShapeNodes(sourceObj)
    return sourceObj


def shapeNodeParentList(objectList, replace=False, message=False, renameShapes=True, delShapeType="",
                        deleteMaster=True, objSpaceParent=False, instance=False):
    """Shape parents from an objectList, objects must be transform nodes

    The parent object is the last obj in objectList and is returned, all other objects are shape parented and removed.

    If deleteOriginal then the combine works more like a replace where the last object is over-ridden by the new shapes
    Otherwise default `replace=False` works as `combine curves`

    Note 1: This function requires the parent to objects (objectList[:-1]) to have free attrs, ie not locked or connected.
    See shapeNodeParentLockedAttrs() for version which handles locked/connected attrs, or shapeNodeParentSafe() \
    is useful if the locked/connected attrs are unknown.

    :param objectList: The object list to be shape parented (should be checked for parent order)
    :type objectList: list
    :param replace: delete the shape nodes of the last selected object
    :type replace: bool
    :param message: report the success message to Maya
    :type message: bool
    :param renameShapes: Will rename all existing shape nodes to match the transform name as per Maya
    :type renameShapes: bool
    :param delShapeType: If deleteOriginal True the shape type can be specified eg "nurbsCurve". "" empty deletes all
    :type delShapeType: str

    :return combinedObjectList: List of combined objects
    :rtype: list(str)
    """
    masterObj = objectList[0]
    objs = objectList[1:]
    if len(objs) == 1:  # One object to be parented ------------------------
        combinedObject = shapeNodeParent(masterObj, objs[0],
                                         deleteMaster=deleteMaster,
                                         objSpaceParent=objSpaceParent,
                                         renameShapes=renameShapes,
                                         replace=replace,
                                         delShapeType=delShapeType,
                                         ogsReset=True,
                                         instance=instance)
        if message:  # report
            if not replace:
                output.displayInfo('Success shape nodes parented to `{}`'.format(combinedObject))
            else:
                output.displayInfo('Success shape nodes switched on `{}`'.format(combinedObject))
        return [combinedObject]

    # Multiple objects to be parented ------------------------
    combinedObjects = list()
    for obj in objs:
        if deleteMaster:  # Must duplicate the master if deleting it since there are multiple objects
            masterObj_safe = cmds.duplicate(masterObj, instanceLeaf=instance)[0]
        else:
            masterObj_safe = masterObj
        combinedObject = shapeNodeParent(masterObj_safe, obj,
                                         deleteMaster=deleteMaster,
                                         objSpaceParent=objSpaceParent,
                                         renameShapes=renameShapes,
                                         replace=replace,
                                         delShapeType=delShapeType,
                                         ogsReset=False,
                                         instance=instance)
        combinedObjects.append(combinedObject)
    if deleteMaster:  # can delete the master now
        cmds.delete(masterObj)
    if MAYA_VERSION == 2022.0 or MAYA_VERSION == 2022.2:
        cmds.ogs(reset=True)  # Force refresh in Maya 2022.0 as it's buggy
    if message:  # Report
        if not replace:
            output.displayInfo('Success shape nodes parented to `{}`'.format(combinedObjects))
        else:
            output.displayInfo('Success shape nodes switched on `{}`'.format(combinedObjects))
    return combinedObjects


def shapeNodeParentLockedAttrs(objectList, replace=False, message=False, renameShapes=True,
                               delShapeType="", deleteMaster=True, objSpaceParent=False, instance=False):
    """Shape parents from an objectList, objects must be transform nodes

    The parent object is the last obj in objectList and is returned, all other objects are shape parented and removed
    If deleteOriginal then the combine works more like a replace where the last object is over-ridden by the new shapes
    Otherwise default `replace=False` works as `combine curves`

    Note 1: This function should be used if the "parent to" objs have locked attrs or connections or parent issue

    Note 2: Will not delete the other objs if they have children

    :param objectList: A list of Maya transform node string names
    :type objectList: list(str)
    :param replace: delete the shape nodes of the last selected object
    :type replace: bool
    :param message: report the success message to Maya
    :type message: bool
    :param renameShapes: Will rename all existing shape nodes to match the transform name as per Maya
    :type renameShapes: bool
    :param delShapeType: If deleteOriginal True the shape type can be specified eg "nurbsCurve". "" empty deletes all
    :type delShapeType: str

    :return combinedObjectList: List of combined objects
    :rtype: list(str)
    """
    for i, obj in enumerate(objectList[:-1]):  # clean the parent to objects
        # duplicate without children each obj, will clean any connections or locked attributes
        newObj = duplicateWithoutChildren(obj, deleteNodeShapes=True)
        if not cmds.listRelatives(obj, children=True):  # cleanup the old obj if no children
            cmds.delete(objectList[i])
        objectList[i] = newObj

    # Now do the shape parent to the tempNode now that the to parent objects are clean
    return shapeNodeParentList(objectList, replace=replace, message=message,
                               renameShapes=renameShapes, delShapeType=delShapeType, deleteMaster=deleteMaster,
                               objSpaceParent=objSpaceParent, instance=instance)


def shapeNodeCombine(objectList, delShapeType="nurbsCurve", select=False, message=True):
    """Combines shape nodes into one object with multiple shape nodes, usually used for combining controls

    :param objectList: A list of transforms to be combined.
    :type objectList: list(str)
    :param delShapeType: The type of shape node to delete on the objects to be deleted
    :type delShapeType: str
    :param select: Select the combined object?
    :type select: bool
    :param message: Report a message to the user?
    :type message: bool
    :return combinedObj: The transform of the combined object
    :rtype combinedObj: str
    """
    lastObj = objectList[0]
    objs = objectList[1:]
    for obj in objs:
        combinedObject = shapeNodeParent(lastObj, obj,
                                         deleteMaster=True,
                                         objSpaceParent=False,
                                         renameShapes=True,
                                         replace=False,
                                         delShapeType=delShapeType,
                                         ogsReset=True,
                                         instance=False)
        lastObj = combinedObject
    if MAYA_VERSION == 2022.0 or MAYA_VERSION == 2022.2:
        cmds.ogs(reset=True)  # Force refresh in Maya 2022.0 as it's buggy
    if message:  # Report
        output.displayInfo('Success shape nodes combined to `{}`'.format(combinedObject))
    if select:
        cmds.select(combinedObject, replace=True)
    return combinedObject


def shapeNodeParentSafe(objectList, replace=False, message=False, selectObj=False, delShapeType="",
                        deleteMaster=True, objSpaceParent=False, instance=False):
    """Shape parents from an objectList, objects must be transform nodes

    The parent object is the last obj in objectList and is returned, all other objects are shape parented and removed
    If deleteOriginal then the combine works more like a replace where the last object is over-ridden by the new shapes
    Otherwise default `replace=False` works as `combine curves`

    Note: This is a safe function which accounts for connections/locked attributes or parent issues

    :param objectList: A list of Maya transform node string names
    :type objectList: list(str)
    :param replace: delete the shape nodes of the last selected object
    :type replace: bool
    :param message: report the success message to Maya
    :type message: bool
    :param selectObj: Will select the remaining object after finishing
    :type selectObj: bool
    :param delShapeType: If deleteOriginal True the shape type can be specified eg "nurbsCurve". "" empty deletes all
    :type delShapeType: str

    :return combinedObjects: List of combined objects
    :rtype: list(str)
    """
    useLockedAttrParent = False
    objParents = objhandling.getAllParents(objectList[-1])  # check if objectList[-1] is a child of other objs

    for obj in objectList[:-1]:  # every obj but the last

        objUnsettableAttributes = attributes.getLockedConnectedAttrs(obj)  # check for locked connected attributes
        if objUnsettableAttributes:
            useLockedAttrParent = True
            break
        if obj in objParents:  # obj is the parent of objectList[-1], so must use shapeNodeParentLockedAttrs()
            useLockedAttrParent = True  # shapeNodeParentLockedAttrs() solves parent issues
            break
        if cmds.listRelatives(obj, children=True, type="transform"):  # has children use shapeNodeParentLockedAttrs()
            useLockedAttrParent = True
            break

    if instance:  # Uninstance any instanced objects before replacing.  Might be faster to do the uninstance here?
        objhandling.uninstanceObjs(objectList[:-1])

    if useLockedAttrParent:  # If found locked/connected attributes of parent issues then use lockedAttr function
        combinedObj = shapeNodeParentLockedAttrs(objectList, replace=replace, message=message,
                                                 renameShapes=True, delShapeType=delShapeType,
                                                 deleteMaster=deleteMaster, objSpaceParent=objSpaceParent,
                                                 instance=instance)
    else:  # Use the faster function
        combinedObj = shapeNodeParentList(objectList, replace=replace, message=message,
                                          delShapeType=delShapeType, deleteMaster=deleteMaster,
                                          objSpaceParent=objSpaceParent,
                                          instance=instance)[0]
    if selectObj:
        cmds.select(combinedObj, replace=True)
    return combinedObj


def shapeNodeParentSelected(masterObj="", replace=False, message=True, selectLastObj=True, deleteMaster=True,
                            objSpaceParent=False, instance=False):
    """Shape parents from a selection.

    Optional masterObj from a UI, if this is an empty string then uses the first object as the masterObj

    The parent object is the last obj in objectList and is returned, all other objects are shape parented and removed
    If deleteOriginal then the combine works more like a replace where the last object is over-ridden by the new shapes
    Otherwise default `replace=False` works as `combine curves`

    :param masterObj: Optional master object, if this is an empty string then uses the first object as the masterObj
    :type masterObj: str
    :param replace: delete the shape nodes of the last selected object
    :type replace: bool
    :param message: report the success message to Maya
    :type message: bool
    :param selectLastObj: Will select the remaining object after finishing
    :type selectLastObj: bool
    :param deleteMaster: Deletes the master object from the scene
    :type deleteMaster: bool
    :param objSpaceParent: If False tries to preserve postion of the parent in world space
    :type objSpaceParent: bool
    :param instance: If True will instance if duplicating the shape node
    :type instance: bool

    :return combinedObjectList: List of combined objects
    :rtype: list(str)
    """
    objectList = cmds.ls(selection=True, long=True)
    if masterObj:  # remove masterObj if in the list and add it as the first entry
        zapiObjList = list(zapi.nodesByNames(objectList))
        zapiMasterObj = zapi.nodeByName(masterObj)
        if zapiMasterObj in zapiObjList:  # Check if the master obj is in the selection. If so remove it.
            zapiObjList.remove(zapiMasterObj)
        objectList = zapi.fullNames(zapiObjList)
        objectList.insert(0, masterObj)  # Append at the start of the list
    if not objectList:
        output.displayWarning("No objects selected.  Please select two or more objects.")
        return list()
    if len(objectList) == 1:
        output.displayWarning("Only one object selected.  Please select two or more objects.")
        return list()
    return shapeNodeParentSafe(objectList, replace=replace, message=message, selectObj=selectLastObj,
                               deleteMaster=deleteMaster, objSpaceParent=objSpaceParent, instance=instance)


def setShapeReparentObj():
    """Returns the object for Replace Shape nodes for UI code. Must be transform with a shape node.

    :return surfaceObject: The first selected mesh or nurbsSurface object.
    :rtype surfaceObject: str
    """
    selObjs = cmds.ls(selection=True, transforms=True)
    if not selObjs:
        output.displayWarning("Please select an object with a shape node.")
        return list()
    for obj in selObjs:
        if cmds.listRelatives(obj, shapes=True):
            return obj
    output.displayWarning("The object does not contain shape nodes, please select an object with shape nodes.")
    return list()


# ---------------------------
# DUPLICATE WITHOUT CHILDREN USE SHAPE NODES
# ---------------------------


def matchTransformForShapeReparent(node):
    """Function used by duplicateWithoutChildren(), creates a group (transform nodes) and handles the rotOffset of a \
    for matching.

    :param node: Name of the node to match, should be a transform or joint.
    :type node:
    :return nodeShortName: The short name of the node
    :rtype nodeShortName: str
    :return tempNode: The node returned, an empty transform node, now matched. Will be a unique name.
    :rtype tempNode: str
    :return rotOffset:  xyz rotation information from the rotatePivot attribute, otherwise an empty list
    :rtype rotOffset: list(float)
    """
    rotOffset = list()
    # If transform record rotOffset in case of freeze transforms ---------------------------------------
    if cmds.objectType(node) == "transform":
        rotOffset = cmds.getAttr("{}.rotatePivot".format(node))[0]

    # Get short name of node ---------------------------------------------------------------------------
    nodeShortName = namehandling.getShortName(node)

    # Create empty transform and match -----------------------------------------------------------------
    tempNode = cmds.group(empty=True, name="{}_tempZooXX".format(nodeShortName))
    cmds.matchTransform([tempNode, node], pos=True, rot=True, scl=True, piv=False)
    return nodeShortName, tempNode, rotOffset


def duplicateWithoutChildren(node, name="", deleteNodeShapes=False, duplicateShapeType=""):
    """Duplicates transforms without their children, keeping the shape nodes intact. Maya is bad at doing this.

    Note: This will temporarily parent the original shape nodes out of the original object and then parent back again.
    Note: Joints will become transforms  TODO: add support for joints.
    Note: User attributes are not included and will be lost, transform is rebuilt from scratch

    :param node: A Maya node name, should be a dag object and possible a transform.
    :type node: str
    :param name: Name of the new node
    :type name: str
    :param deleteNodeShapes: Delete the shape nodes of the original object?
    :type deleteNodeShapes: bool
    :param duplicateShapeType: Delete the shape nodes of this type only eg "nurbsCurve" or leave empty "" if all
    :type duplicateShapeType: str
    :return dup: The duplicated node
    :rtype dup: str
    """
    # match new transform, record the rotOffset if one and get the shortname of the node
    nodeShortName, tempNode, rotOffset = matchTransformForShapeReparent(node)

    # Shape parent the shapes to the new node, note: removes the shapes from the first obj (node) ------
    if duplicateShapeType:
        shapeList = cmds.listRelatives(node, shapes=True, type=duplicateShapeType, fullPath=True)
    else:
        shapeList = cmds.listRelatives(node, shapes=True, fullPath=True)
    if shapeList:
        for i, shape in enumerate(shapeList):
            shapeList[i] = cmds.parent(shape, tempNode, shape=True, relative=True)[0]
    shapeList = cmds.listRelatives(tempNode, shapes=True, fullPath=True)  # remake, parent is terrible wth long-names
    # Duplicate the temp object, so we can re-parent back the shapes to the first object (node) --------
    if not deleteNodeShapes:  # if True skip this step, we don't want the original shapes
        dup = cmds.duplicate(tempNode, name="{}_duplicate".format(nodeShortName), renameChildren=True)[0]
        if shapeList:  # Re-parent orig shapes back  -------------------------------------------------------
            for i, shape in enumerate(shapeList):
                shapeList[i] = cmds.parent(shape, node, shape=True, relative=True)[0]
        cmds.delete(tempNode)  # Delete the temp node now empty  -------------------------------------------
    else:
        dup = tempNode
        if not name:
            dup = cmds.rename(dup, "{}_duplicate".format(nodeShortName))

    if rotOffset:  # Add back the local rotOffset which is important for matching ----------------------
        if rotOffset[0] or rotOffset[1] or rotOffset[2]:
            cmds.move(-rotOffset[0], -rotOffset[1], -rotOffset[2], dup, relative=True, objectSpace=True)
            cmds.matchTransform([dup, node], pos=False, rot=False, scl=False, piv=True)  # and match pivot as moved

    if name:  # rename if name passed in  ---------------------------------------------------------------
        dup = cmds.rename(dup, namehandling.getShortName(name))

    renameShapeNodes(dup)  # Update shape node names
    return dup


# ---------------------------
# DELETE SHAPE NODES
# ---------------------------


def deleteShapeNodes(obj, type=None):
    """Deletes all shape nodes given the transform.  Can assign a type, Eg. "nurbsCurve"

    :param obj: A Maya object or node name
    :type obj: str
    :param type: Type of nodes to filter from in Maya names, Eg. "nurbsCurve"
    :type type: list
    :return shapeList: a list of the shape nodes deleted
    :rtype shapeList: list
    """
    if type:
        deleteShapes = cmds.listRelatives(obj, fullPath=True, shapes=True, type=type)
    else:
        deleteShapes = cmds.listRelatives(obj, fullPath=True, shapes=True)
    cmds.delete(deleteShapes)
    return deleteShapes


def deleteShapeNodesList(objList, type=None):
    """Deletes all shape nodes given a transform list.  Can assign a type, Eg. "nurbsCurve"

    :param objList: The Maya Object List
    :type objList: list
    :param type: Type of nodes to filter from in Maya names, Eg. "nurbsCurve", if None will delete all shapes.
    :type type: str
    :return shapeList: a list of list of shape nodes deleted from each object
    :rtype shapeList: list(list(str))
    """
    delShapeList = list()
    for obj in objList:
        delShapeList.append(deleteShapeNodes(obj, type=type))
    return delShapeList


def deleteShapeNodesSelected(type=None):
    """Deletes all shape nodes given a selection.  Can assign a type, Eg. "nurbsCurve"

    :param type: Type of nodes to filter from in Maya names, Eg. "nurbsCurve"
    :type type: list
    :return shapeList: a list of list of shape nodes deleted from each object
    :rtype shapeList: list(list(str))
    """
    selObjs = cmds.ls(selection=True, long=True)
    if not selObjs:
        return list()
    return deleteShapeNodesList(selObjs, type=type)


# ---------------------------
# OTHER MISC
# ---------------------------


def getOrigShapeNodes(mesh, fullPath=True, inverse=False):
    """Returns a list of shape nodes, filtering the original shape nodes
    Or if inverted will filter out the original shape nodes
    This is queried through the checkbox attr intermediateObject

    :param mesh: mesh object's name
    :type mesh: str
    :param fullPath: do you want to return the long name (True=fullpath) or short
    :type fullPath: bool
    :param inverse: Will filter out the original shape nodes
    :type inverse:
    :return shapeReturnList: A list of original shape nodes, or not orig nodes if inverted
    :rtype: list
    """
    oMeshShapes = cmds.listRelatives(mesh, shapes=True, fullPath=fullPath)
    shapeReturnList = list()
    for shape in oMeshShapes:
        # check if original shape with intermediateObject checkbox
        if not inverse:
            if cmds.getAttr("{}.intermediateObject".format(shape)):
                #  yes this is an original node
                shapeReturnList.append(shape)
        else:
            if not cmds.getAttr("{}.intermediateObject".format(shape)):
                #  no this is not an original node
                shapeReturnList.append(shape)
    return shapeReturnList


def getOrigShapeNodesSelected(fullPath=True, inverse=False, message=True):
    """Returns a list of shape nodes, filtering the original shape nodes
    Or if inverted will filter out the original shape nodes
    This is queried through the checkbox attr intermediateObject

    :param message: Report a message to the user
    :type message: bool
    :return shapeNodeList: A list of intermediate shape node names
    :rtype shapeNodeList: list(str)
    """
    shapeNodeList = list()
    objs = cmds.ls(selection=True)
    if not objs:
        if message:
            output.displayWarning("No objects selected, please select an object.")
        return shapeNodeList
    for obj in objs:
        shapeNodeList += getOrigShapeNodes(obj, fullPath=fullPath, inverse=inverse)
    if not shapeNodeList:
        if message:
            output.displayWarning("No shape original nodes found")
        return shapeNodeList
    return shapeNodeList


def deleteOrigShapeNodesSelected():
    """Deletes all shape original nodes (intermediate objects) associated with the current selection.

    :return shapeNodeList: A list of the shape nodes deleted
    :rtype shapeNodeList: list(str)
    """
    shapeNodeList = getOrigShapeNodesSelected(message=True)
    if not shapeNodeList:
        return shapeNodeList  # error messages already given.
    cmds.delete(shapeNodeList)
    output.displayInfo("Shape original nodes deleted {}".format(shapeNodeList))
    return shapeNodeList


def filterNotOrigNodes(mesh, fullPath=True):
    """Returns a list of shape nodes, filtering the out the original shape nodes
    This is queried through the checkbox attr intermediateObject

    :param mesh: mesh object's name
    :type mesh: str
    :param fullPath: do you want to return the long name (True=fullpath) or short
    :type fullPath: bool
    :return shapeReturnList: A list of shape nodes without orig nodes
    :rtype: list
    """
    shapeReturnList = getOrigShapeNodes(mesh, fullPath=fullPath, inverse=True)
    return shapeReturnList


def renameShapeNodes(objectTransform):
    """Renames all shape nodes under a transform
    Name becomes `objectTransformShape` and increments numbers higher `objectTransformShape1` (second shape)

    :param objectTransform: the object who's shape nodes need renaming
    :type objectTransform: str
    :return controlShapeNodeList: list of new shape nodes with new names
    :rtype controlShapeNodeList: list
    """
    return namehandling.renameShapeNodes(objectTransform)


def renameShapeNodeList(objectList):
    """Renames all shape nodes under a list of transforms
    Name becomes `objectTransformShape` and increments numbers higher `objectTransformShape1` (second shape)

    :param objectList: list of Maya objs to rename their associated shapes
    :type objectList: list
    """
    return namehandling.renameShapeNodesList(objectList)


def renameShapeNodeSelected():
    """Renames all shape nodes under a selected transform
    Name becomes `objectTransformShape` and increments numbers higher `objectTransformShape1` (second shape)
    """
    objList = cmds.ls(selection=True)
    return namehandling.renameShapeNodesList(objList)


def templateRefShapeNodes(transform, template=True, message=False, unTemplateRef=False):
    """Templates or references the shape nodes of a transform.  Un-template/un-reference with `unTemplateRef=False`

    :param transform: A maya transform node
    :type transform: str
    :param template: True if templating, False if referencing
    :type template: bool
    :param message: Report the message to the user
    :type message: bool
    :param unTemplateRef: If True will template/reference if False will un-template/un-reference
    :type unTemplateRef: bool
    """
    if template:
        templateRefVal = 1
    else:  # reference in the dropdown list
        templateRefVal = 2
    shapeNodes = cmds.listRelatives(transform, shapes=True, fullPath=True)
    if not shapeNodes:
        if message:
            output.displayWarning("Shape node not found for {}".format(transform))
        return list()
    if not unTemplateRef:
        for shape in shapeNodes:
            cmds.setAttr("{}.overrideEnabled".format(shape), True)
            cmds.setAttr("{}.overrideDisplayType".format(shape), templateRefVal)
    else:  # un-template/un-reference
        for shape in shapeNodes:  # set the display type to normal
            cmds.setAttr("{}.overrideDisplayType".format(shape), 0)
