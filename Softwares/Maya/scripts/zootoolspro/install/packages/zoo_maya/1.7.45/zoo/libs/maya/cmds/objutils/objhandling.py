"""functions for handling objects in Maya.

Example use:

.. code-block:: python

    from zoo.libs.maya.cmds.objutils import objhandling
    objhandling.uninstanceSelected()

"""
import maya.cmds as cmds
import maya.mel as mel
import maya.api.OpenMaya as om2
import maya.OpenMaya as om1

from zoo.libs.maya import zapi
from zoo.libs.maya.cmds.objutils import attributes
from zoo.libs.utils import output

TRANSFORM_ATTRS = attributes.MAYA_TRANSFORM_ATTRS
POS_ROT_ATTRS = attributes.MAYA_TRANSLATE_ATTRS + attributes.MAYA_ROTATE_ATTRS


def getAllParents(obj, long=True):
    """Returns all parents of the current obj.  Long will return long names

    :param obj: A Maya DAG object name
    :type obj: str
    :param long: Return long names?
    :type long: bool
    :return parents: List of the parents of this object
    :rtype parents: list(str)
    """
    parents = cmds.ls(obj, long=True)[0].split("|")[1:-1]
    if long:  # Get long names
        parents = ["|".join(parents[:i]) for i in range(1, 1 + len(parents))]
        for i, obj in enumerate(parents):  # must add "|" to the beginning of each name
            parents[i] = "|{}".format(obj)
    return parents


def getRootObjectsFromList(objsLongList):
    """Returns only the bottom hierarchy objects (roots) in an object list.

    Compares longNames and filters by the start of each string o get the lowest unique name.

    e.g. `|group1` will filter out `|group1|mesh1` and `|group1|mesh1|locator2`.

    :param objsLongList: list of maya object names, as long (full) names with "|"
    :type objsLongList: list
    :return: only the bottom objects of the hierarchy, no children included.
    :rtype: list[str]
    """
    removeList = list()
    for i, checkObj in enumerate(objsLongList):
        for obj in objsLongList:
            if checkObj == obj:
                continue
            if checkObj.startswith("{}|".format(obj)):  # True then it's a child
                removeList.append(checkObj)
                break
    rootObjs = list(set(objsLongList) - set(removeList))
    return rootObjs


def getRootObjectsFromSelection():
    """Returns only the bottom hierarchy objects in a selection,
    Compares longNames and filters byt the start.

    e.g. `|group1` will filter out `|group1|mesh1` and `|group1|mesh1|locator2`

    :return rootObjs: only the bottom objects of the hierarchy, no children included
    :rtype rootObjs: list
    """
    selObjs = cmds.ls(selection=True, long=True)
    if not selObjs:
        om2.MGlobal.displayWarning('No Objects Selected, Please Select'.format())
        return
    return getRootObjectsFromList(selObjs)


def getListTransforms(mayaShapeList, longName=True):
    """From a list of Maya shape nodes return their transforms

    :param mayaShapeList: list of maya shape node names
    :type mayaShapeList: list
    :return transformList: list of transform names related to the node list
    :rtype transformList: list
    """
    transformList = list()
    for node in mayaShapeList:
        parent = cmds.listRelatives(node, parent=True, fullPath=longName)[0]
        if cmds.objectType(parent, isType='transform'):
            transformList.append(parent)
    return list(set(transformList))


# -----------------------------
# INSTANCING
# -----------------------------


def getInstances():
    """Returns all instanced nodes in a scene

    TODO: doesn't support transforms only shape nodes.

    :return: all instance names in a scene, will be shape nodes
    :type: list(str)
    """
    instances = []
    iterDag = om1.MItDag(om1.MItDag.kBreadthFirst)
    while not iterDag.isDone():
        instanced = om1.MItDag.isInstanced(iterDag)
        if instanced:
            instances.append(iterDag.fullPathName())
        iterDag.next()
    return instances


def isInstancedTransform(transformNode):
    """Returns if a transform node is instanced? Must be a transform node.

    :param transformNode: A maya transform node, will check the first shape node to see if it's instanced.
    :type transformNode:

    :return isInstanced: Is the object an instance or not?
    :rtype isInstanced: bool
    """
    shapes = cmds.listRelatives(transformNode, fullPath=True, shapes=True)
    if shapes:  # Instanced objects usually need shapes but what about instanced groups?
        return isInstanced(shapes[0])
    return isInstanced(transformNode)  # TODO transform doesn't work yet


def isInstancedShape(shape):
    selectionList = om1.MSelectionList()
    selectionList.add(shape)
    dagPath = om1.MDagPath()
    selectionList.getDagPath(0, dagPath)
    return dagPath.isInstanced()


def isInstanced(obj):
    """Returns if a transform or shape node is instanced.

    :param obj: The fullpath of a maya DAG object `|grpX|cube1`, can be a shape or transform
    :type obj: str
    :return: Is the object an instance or not?.
    :rtype: bool
    """
    instanced = False
    if not cmds.objExists(obj):
        return None
    # Test shape node is instanced -----------
    if cmds.objectType(obj) == "transform":
        shapes = cmds.listRelatives(obj, shapes=True, fullPath=True)
        if shapes:
            instanced = isInstancedShape(shapes[0])
    else:  # Could be a shape already so test ---------
        instanced = isInstancedShape(obj)
    if instanced:
        return instanced
    # Instanced is False so try to see if any children have multiple parents, ie checks for instanced groups -------
    children = cmds.listRelatives(obj, type="transform", children=True, fullPath=True)
    if not children:
        return False
    for child in children:
        # Check if child has two parents, if so the parent is an instance so return True
        if zapi.nodeByName(child).mfn().parentCount() > 1:
            return True


def rootInstance(obj):
    """Find if an object is an instance and if so, walk up the hierarchy and return the top instance object.

    Returns "" if no objects are instances.

    :param obj: A Maya DAG object
    :type obj: str

    :return rootInstanceObj: The top most parent (root) object that is an instance from the given object.
    :rtype rootInstanceObj: str
    """
    current = str(obj)
    walk = list()
    while current:
        if isInstanced(current):
            walk.append(current)
            current = cmds.listRelatives(current, parent=True, fullPath=True)
        else:  # Not instanced
            current = None
        if current:
            current = current[0]  # parent object
    if not walk:  # No objects instanced
        return ""
    return walk[-1]  # Return last in the hierarchy ie the top parent


# -----------------------------
# UN-INSTANCE
# -----------------------------


def uninstanceObj(obj):
    """Uninstances a single maya transform node (and shapes contained) by duplicating and deleting the original.
    Connections are maintained. Accepts transforms only and newly created objects are returned.

    This function is similar to the mel that works on selection:

        mel.eval('convertInstanceToObject;')

    The mel also duplicates geo, but badly renames new transforms, doesn't return names, or support connections.

    :param obj: A name of a transform node
    :type obj: str
    :return obj: The newly created object
    :rtype obj: str
    """
    # Check for any connections --------------------------------------------------------
    duplicatedObjAttrs = list()
    from zoo.libs.maya.cmds.objutils.connections import getDestinationSourceAttrs  # can't import `connections` cycle
    sourceObAttrs, destinationObjAttrs = getDestinationSourceAttrs(obj, message=False)

    # Duplicate the object -------------------------------------------------------------
    dupObj = str((cmds.duplicate(obj))[0])

    # Reconnect if connections ---------------------------------------------------------
    if sourceObAttrs:
        for objAttr in destinationObjAttrs:  # New duplicate destinations
            attr = objAttr.split(".")[-1]
            duplicatedObjAttrs.append(".".join([dupObj, attr]))

        for i, dupAttr in enumerate(duplicatedObjAttrs):  # Reconnect
            cmds.connectAttr(sourceObAttrs[i], dupAttr)

    # Delete orig and rename the new object --------------------------------------------------
    shortObjName = (obj.split('|'))[-1]
    cmds.delete(obj)
    return cmds.rename(dupObj, shortObjName)


def uninstanceObjs(objs):
    """Uninstances an obj list by duplicating and deleting the original objects. New names are returned.
    Connections are maintained. Accepts transforms only and newly created objects are returned.

    This function is similar to the mel that works on selection:

        mel.eval('convertInstanceToObject;')

    The mel also duplicates geo, but badly renames new transforms, doesn't return names, or support connections.

    :param objs: A list of transform node names.
    :type objs: list(str)

    :return objs: A list of transform node names, now updated with the non instanced transforms.
    :rtype objs: list(str)
    """
    newObjs = list()
    for obj in objs:
        newObjs.append(uninstanceObj(obj))
    objs = newObjs
    return objs


def uninstanceSelected(uninstanceRoot=True, message=True):
    """Uninstances the selected transform and shape nodes by duplicating and deleting the original objects.
    Connections are maintained. Accepts transforms only and newly created objects are returned.

    If uninstanceRoot is True then will uninstance the top parent that is instanced in the hierarchy of the selection.

    This function improves on the mel:

        mel.eval('convertInstanceToObject;')

    The mel also duplicates geo, but badly renames new transforms, doesn't return names, or support connections.

    :param uninstanceRoot: Will uninstance the top parent that is instanced in the hierarchy of the selection.
    :type uninstanceRoot: bool
    :param message: Report messages to the user?
    :type message: bool

    :return instancedTranforms: The new instanced transform names
    :rtype instancedTranforms: list(str)
    """
    newSelTransforms = list()
    instancedTranforms = list()
    newTransforms = list()

    selShapes = cmds.ls(selection=True, long=True, shapes=True)
    selTransforms = cmds.ls(selection=True, long=True, transforms=True)

    if not selShapes and not selTransforms:
        if message:
            output.displayWarning("Please select objects")
        return

    if selShapes:  # add the transforms of the shapes
        for shape in selShapes:
            newTransforms = cmds.listRelatives(shape, parent=True)[0]

    selTransforms = list(set(selTransforms + newTransforms))

    # Do the Uninstance here ------------------------------------------------------
    if selTransforms:
        for transform in selTransforms:
            if uninstanceRoot:  # Find the related root instance and uninstance it
                rootObj = rootInstance(transform)
                if rootObj:
                    transform = uninstanceObj(rootObj)
                    instancedTranforms.append(transform)
                    newSelTransforms.append(transform)
                    continue  # Found and uninstanced
                continue  # No instance
            if not isInstanced(transform):  # Not an instance
                continue
            # Uninstance as is an instance (ignores hierarchy)
            transform = uninstanceObj(transform)
            instancedTranforms.append(transform)
            newSelTransforms.append(transform)
        cmds.select(newSelTransforms, replace=True)

    # Report messages -----------------------------------------------------------------
    if message and instancedTranforms:
        if len(instancedTranforms) > 4:
            output.displayInfo("Success: Objects uninstanced: {}".format(instancedTranforms))
            output.displayInfo("Success: Many objects have been uninstanced, see the script editor.")
        else:
            output.displayInfo("Success: Objects have been uninstanced: {}".format(instancedTranforms))
    elif message and not instancedTranforms:
        output.displayWarning("No instanced objects found to uninstance.")
    return instancedTranforms


def uninstanceAll(message=True):
    """Uninstances all objects in a scene.  Works by duplicating the instance and deletes it while maintaining names.

    This function is similar to the mel that works on selection:

        mel.eval('convertInstanceToObject;')

    The mel also duplicates geo, but can badly rename new transform nodes, doesn't return names, or support connections.

    :return parentInstanceList: The Instanced Parents in the scene that were uninstanced
    :rtype parentInstanceList: list
    """
    instances = getInstances()
    parentInstanceList = []
    while len(instances):
        parent = cmds.listRelatives(instances[0], parent=True, fullPath=True)[0]
        parent = uninstanceObj(parent)
        parentInstanceList.append(parent)
        instances = getInstances()
    if message:
        om2.MGlobal.displayInfo('Success: Instance Objects Removed: {}'.format(parentInstanceList))
    return parentInstanceList


# -----------------------------
# CONNECTIONS
# -----------------------------


def cleanConnections(objName, keyframes=True):
    """Cleans an object of all connections, keys/connections constraints
    currently only works for keys

    :param objName: name of the obj to clean
    :type objName: str
    :param keyframes: do you want to clean keyframes?
    :type keyframes: bool
    :return:
    """
    if keyframes:
        cmds.cutKey(objName, s=True)  # delete key command


# -----------------------------
# GET BY TYPE
# -----------------------------


def getTypeTransformsHierarchy(objList, nodeType="mesh"):
    """Returns the nodes of a certain type under the current hierarchy (maya list)

    :param objList: list of maya objects
    :type objList: list
    :param nodeType: the type of node to filter
    :type nodeType: str
    :return: a list of maya node names, the nodes now filtered
    :rtype: list
    """
    meshShapes = cmds.listRelatives(objList, allDescendents=True, fullPath=True, type=nodeType)
    selMeshShapes = cmds.listRelatives(objList, shapes=True, fullPath=True, type=nodeType)
    if selMeshShapes:  # if the selection has shapes of type
        return cmds.listRelatives((meshShapes + selMeshShapes), parent=True, fullPath=True)
    return cmds.listRelatives(meshShapes, parent=True, fullPath=True)


def selectTypeUnderHierarchy(type="mesh"):
    """Select objects of a given type as a child of the selected objects

    :param type:
    :type type:
    :return:
    :rtype:
    """
    objList = cmds.ls(selection=True)
    typeTransformList = getTypeTransformsHierarchy(objList, nodeType=type)
    cmds.select(typeTransformList, replace=True)


def returnSelectLists(selectFlag="all", long=False):
    """Based on a selectFlag will return nodes of three types::

        #. "all" : All in scene
        #. "selected" : only selected
        #. "hierarchy" : search selected hierarchy

    .. todo::  Selected should include shape nodes

    :param selectFlag: "all", "selected", "hierarchy".
    :type selectFlag: str
    :return: the nodes to be processed, True if nothing is selected and needs to be
    :type: tuple[list[str], bool]
    """
    nodeList = []
    selectionWarning = False
    if selectFlag == "all":
        nodeList = cmds.ls(dag=True, long=long)  # allDagNodes
    elif selectFlag == "selected":  # selected only
        nodeList = cmds.ls(sl=True, long=long)
        if not nodeList:
            selectionWarning = True
    elif selectFlag == "hierarchy":  # all descendents children
        nodeList = cmds.ls(sl=True, long=long)
        if nodeList:
            nodeList = nodeList + cmds.listRelatives(nodeList, allDescendents=True, fullPath=True)
        else:
            selectionWarning = True
    return nodeList, selectionWarning


def selectHierarchyFilterType(nodeType='transform'):
    """Filters the select hierarchy command by a node type, usually transform type so it doesn't select the shape nodes

    :param nodeType: type of object or nde to be filtered in the selection
    :type nodeType: str
    :return: the objs to be selected
    :rtype: list
    """
    cmds.select(hi=True)
    objs = cmds.ls(sl=True)
    filterList = cmds.ls(objs, type=nodeType)
    cmds.select(filterList, r=True)
    return filterList


def findParentObjList(objectList):
    """Find the parent from list world is a none type, check for it and add as None
    * no idea what this does anymore, leaving it as hotkeys may reference, old code

    :param objectList:
    :type objectList:
    :return:
    :rtype:
    """
    matchObjsParent = []
    for obj in objectList:
        matchParent = cmds.listRelatives(obj, p=1)
        if matchParent is None:
            matchObjsParent.append(None)
        else:
            matchObjsParent.append(matchParent[-1])
    return (matchObjsParent)


def getAllTansformsInWorld(long=True):
    """Returns all transforms in world, are not parented to anything

    :return rootTransforms: transform node names that are in world
    :rtype rootTransforms: list
    """
    return cmds.ls(assemblies=True, long=long)


def getTheWorldParentOfObj(objLongName):
    """Returns the bottom most object of a hierarchy given the object as a child.  (assembly)
    Will return the same object if in world

    :param objLongName: maya object dag node name, must be long name
    :type objLongName: str
    :return worldParent: the
    :rtype worldParent:
    """
    worldParent = objLongName.split('|')[1]  # take the 1 element is the first root obj
    worldParent = "|{}".format(worldParent)  # worldParent as long name
    return worldParent


def getTheWorldParentOfObjList(objLongNameList):
    worldParentList = list()
    for obj in objLongNameList:
        worldParentList.append(getTheWorldParentOfObj(obj))
    return list(set(worldParentList))


def getAllMeshTransformsInScene(longName=True):
    """Returns all meshes (poly geo) in a scene as a list

    :param longName: names will be in long format
    :type longName: bool
    :return allMeshTransforms: list of all the mesh transform names in the scene
    :rtype allMeshTransforms: list
    """
    meshShapes = cmds.ls(type='mesh')
    if meshShapes:
        return getListTransforms(meshShapes, longName=longName)


def getTransformListFromShapeNodes(shapeList, fullPath=True):
    """Given a lit of shapes find their parents (transforms)

    :param shapeList: list of shape nodes by name
    :type shapeList: list
    :param fullPath: do you want to return the fullpath name?
    :type fullPath: bool
    :return transformList: a list of transform names
    :rtype transformList: list
    """
    transformList = list()
    for shape in shapeList:
        try:
            transformList.append(cmds.listRelatives(shape, parent=True, fullPath=fullPath)[0])
        except:
            pass
    return transformList


def templateObject(obj):
    """Sets an object to be templated

    :param obj: maya object
    :type obj: str
    """
    cmds.setAttr(('{}.overrideEnabled'.format(obj)), 1)
    cmds.setAttr(('{}.overrideDisplayType'.format(obj)), 1)
    # find shapes and turn enable override off
    shapesList = cmds.listRelatives(obj, shapes=True)
    om2.MGlobal.displayInfo('Shape nodes: {}'.format(shapesList))
    for shapeNode in shapesList:
        cmds.setAttr(('{}.overrideDisplayType'.format(shapeNode)), 1)


def getParentHierarchyOfObjList(sceneRootsLongName):
    """Returns the parentHierarchy of an object list (long names)
    will filter out world or empty "" returns.

    :param sceneRootsLongName: a list of long names in Maya `["|group1|object", "|group1|object2"]`
    :type sceneRootsLongName: list
    :return: the parent hierarchy as a long name list.
    :rtype: list
    """
    parentHierarchyList = list()
    for obj in sceneRootsLongName:
        hierarchyList = obj.split("|")
        del hierarchyList[-1]
        parent = "|".join(hierarchyList)
        if parent:
            parentHierarchyList.append("|".join(hierarchyList))
    return parentHierarchyList


def removePrefixLists(parentHierarchy, objectLongName):
    """From a single object and single parent hierarchy remove it if there's a prefix match

    :param parentHierarchy: the potential parent hierarchy
    :type parentHierarchy: str
    :param objectLongName: the maya object long name
    :type objectLongName: str
    :return objectLongName: the maya object long name now with the parent removed if there's a match
    :rtype objectLongName: str
    """
    if objectLongName.startswith(parentHierarchy):
        return objectLongName[len(parentHierarchy):]  # the shortened name
    return objectLongName  # name didn't change


def removeParentHierarchyObj(objectLongName, parentHierarchyList):
    """For an objectLongName remove possible parent hierarchies from the name in parentHierarchyList

    :param objectLongName: the maya object long name
    :type objectLongName: str
    :param parentHierarchyList: the potential parent hierarchy
    :type parentHierarchyList: list[str]
    :rtype: str
    """
    for parentHierarchy in parentHierarchyList:
        objectLongName = removePrefixLists(parentHierarchy, objectLongName)
    return objectLongName


def removeRootParentListObj(objectLongName, sceneRootsLongName):
    """For an objectLongName remove possible parent hierarchies of sceneRootsLongName list

    :param objectLongName: the maya object long name
    :type objectLongName: str
    """
    parentHierarchyList = getParentHierarchyOfObjList(sceneRootsLongName)
    for parentHierarchy in parentHierarchyList:
        objectLongName = removePrefixLists(parentHierarchy, objectLongName)
    return objectLongName


def removeRootParentListObjList(objectListLongName, sceneRootsLongName):
    """Function that is useful for exporting alembic selected which export from the selected top root node
    when exported recorded objects will have incorrect long names so this will fix that and remove the
    parent hierarchies from the longnames.

    :param objectListLongName: a list of maya object long names `["|group1|object|objC", "|group1|object2|objA"]`
    :type objectListLongName: list[str]
    :param sceneRootsLongName: root object list long names `["|group1|object", "|group1|object2"]`
    :type sceneRootsLongName: list[str]
    :return: the fixed names with roots hierarchies eliminated
    :rtype: list
    """
    fixObjectListLongName = objectListLongName
    parentHierarchyList = getParentHierarchyOfObjList(sceneRootsLongName)
    for i, objectLongName in enumerate(objectListLongName):
        fixObjectListLongName[i] = removeParentHierarchyObj(objectLongName, parentHierarchyList)
    return fixObjectListLongName


# --------------------------
# REMOVE FREEZE TRANSFORM
# --------------------------


def zeroFrozenTransform(obj, freeze=True, buildLocator=True, parentToWorld=True):
    """Resets a frozen object to be zero in the world, will move and rotate back to world zero, and remove the \
    local rotate/scale pivot offset

    Can build a locator to mark the original position/rotation so the object can be snapped back later.

    :param obj: Name of the transform node
    :type obj: str
    :param freeze: Freeze the object at zero?
    :type freeze: bool
    :param buildLocator: Build a locator at the original object's location
    :type buildLocator: bool

    :return loc: Locator name that marks the position of the object, can be none, will be an empty string ""
    :rtype loc: str
    """
    objZapi = zapi.nodeByName(obj)
    loc = ""
    if cmds.getAttr("{}.rotatePivot".format(obj))[0] == (0.0, 0.0, 0.0):
        return ""
    if buildLocator:
        loc = cmds.spaceLocator(name="zoo_mirror_delMe")[0]
        cmds.matchTransform([loc, obj], pos=1, rot=1, scl=1, piv=0)

    # Unparent to world ------------------------
    objParent = cmds.listRelatives(obj, parent=True)
    if objParent is not None and parentToWorld:
        cmds.parent(obj, world=True)[0]
        obj = objZapi.fullPathName()

    # Do the zero ----------------------
    translate = cmds.getAttr("{}.translate".format(obj))[0]
    worldRotPivot = cmds.xform(obj, sp=True, q=True, ws=True)
    # Set Rotate zero
    cmds.setAttr("{}.rotate".format(obj), 0.0, 0.0, 0.0, type="double3")
    # Set Translate from the worldRotPivot to move back to world zero
    cmds.setAttr("{}.translate".format(obj),
                 translate[0] - worldRotPivot[0],
                 translate[1] - worldRotPivot[1],
                 translate[2] - worldRotPivot[2], type="double3")
    if freeze:
        cmds.makeIdentity(obj, apply=True, translate=True, rotate=True, scale=False)

    # reparent -----------------------
    if objParent is not None and parentToWorld:
        cmds.parent(obj, objParent[0])
        obj = objZapi.fullPathName()

    return loc


def removeFreezeTransform(obj, message=True):
    """Removes the freeze local pivot info from an object while maintaining it's position.

    :param obj: Name of the transform node
    :type obj: str
    :param message: Report the messages to the user?
    :type message: bool

    :return success: True if the freeze was successfully removed. False if not.
    :rtype success: bool
    """
    if not checkForFrozenGeometry(obj):  # Already not frozen so bail
        return True
    lockedNodes, lockedAttrs = attributes.getLockedConnectedAttrsList([obj], TRANSFORM_ATTRS, keyframes=True)
    if lockedAttrs:
        if message:
            output.displayWarning("Cannot remove the frozen transform on `{}` because of "
                                  "attribute connections {}".format(obj, lockedAttrs))
        return False
    loc = zeroFrozenTransform(obj, freeze=True, buildLocator=True)
    if loc:
        cmds.matchTransform([obj, loc], pos=1, rot=1, scl=1, piv=0)
        cmds.delete(loc)
    return True


def removeFreezeTransformList(transformNodes, message=True):
    """Removes the freeze local pivot info from an object list while maintaining their positions.

    :param transformNodes: List of names of transform nodes (objects)
    :type transformNodes: list(str)
    :param message: Report the messages to the user?
    :type message: bool

    :return success: True if the freeze was successfully removed on all objects. False if some failed.
    :rtype success: bool
    """
    rememberSel = cmds.ls(selection=True)
    success = True
    for obj in transformNodes:
        successState = removeFreezeTransform(obj, message=message)
        if not successState:
            success = False
    cmds.select(rememberSel, replace=True)  # Retain original selection
    if message and success is False:
        output.displayWarning("Some frozen transforms could not be removed, see the script editor for information.")

    return success


def removeFreezeTransformSelected(message=True):
    """Removes the freeze local pivot info from selected transforms while maintaining their positions.

    :param message: Report the messages to the user?
    :type message: bool

    :return success: True if the freeze was successfully removed on all objects. False if some failed.
    :rtype success: bool
    """
    selTranforms = cmds.ls(selection=True, type="transform")
    if not selTranforms:
        if message:
            output.displayWarning("No objects (transform nodes) selected.  Please select an object")
        return
    return removeFreezeTransformList(selTranforms, message=message)


# --------------------------
# FIND/CHECK FOR FREEZE TRANSFORMS
# --------------------------


def checkSmallNumbers(number, toleranceNumber=.001):
    """Tests if a number is smaller than the toleranceNumber.  True if so.

    :param number: The given number to test
    :type number: float
    :param toleranceNumber: The max number before becomes True
    :type toleranceNumber: float

    :return isSmaller:  True if smaller
    :rtype isSmaller: bool
    """
    if number < toleranceNumber:
        return True
    return False


def checkCloseToNumber(number, targetNumber, toleranceRange=.001):
    halfRange = toleranceRange / 2
    if number > targetNumber + halfRange:
        return False
    if number < targetNumber - halfRange:
        return False
    return True


def checkForFrozenGeometry(obj):
    """Checks to see if the geometry has been frozen, ie it's rotate pivot is not zeroed.

    Uses a tolerance threshold.

    :param obj: A maya object name
    :type obj: str

    :return frozen: True if the object was frozen
    :rtype frozen: bool
    """
    rotPivotList = cmds.getAttr("{}.rotatePivot".format(obj))[0]
    for number in rotPivotList:
        if not checkSmallNumbers(number, toleranceNumber=.001):
            return True
    return False


def checkForMatchVector(obj, targetVector, attribute="rotatePivot", toleranceRange=.001):
    """Checks to see if an double3 attribute matches a vector (list with three entries).

    Uses a tolerance threshold.

    :param obj: A maya object name
    :type obj: str
    :param targetVector: A list with three floats [0.12, 0.1, 1.34]
    :type targetVector: list(float)
    :param attribute: The attribute to check
    :type attribute: str
    :param toleranceRange: The acceptable tolernace range
    :type toleranceRange: float

    :return match: True if the vector matches, False if not
    :rtype match: bool
    """
    currentList = cmds.getAttr(".".join([obj, attribute]))[0]
    for i, number in enumerate(currentList):
        if not checkCloseToNumber(number, targetVector[i], toleranceRange=toleranceRange):
            return False
    return True


def checkFrozenTransformOffsetList(transformList, message=True):
    """Checks if an object list's transforms have been frozen, ie the Local Rotate Pivot attribute is not zeroed.

    Returns any objects that are frozen as an object list.

    :param transformList: A list of objects (transform nodes)
    :type transformList: list(str)
    :param message: Report messages to the user?
    :type message: bool

    :return frozenObjs: A list of objects that have been frozen, ie their rotatePivot attribute is not zeroed.
    :rtype frozenObjs: list(str)
    """
    frozenObjs = list()
    for transform in transformList:
        if checkForFrozenGeometry(transform):
            frozenObjs.append(transform)
    if frozenObjs and message:
        output.displayWarning("Objects have had their transforms frozen: {}".format(frozenObjs))
    return frozenObjs


def checkFrozenTransformOffsetSelected(extraObjects=[], message=True):
    """Checks if an object list's transforms have been frozen, ie the Local Rotate Pivot attribute is not zeroed.

    Returns any objects that are frozen as an object list.

    :param message: Report messages to the user?
    :type message: bool

    :return frozenObjs: A list of objects that have been frozen, ie their rotatePivot attribute is not zeroed.
    :rtype frozenObjs: list(str)
    """
    selTranforms = cmds.ls(selection=True, type="transform")

    if extraObjects:  # extra object checks for UI convenience
        extraObjects = cmds.ls(extraObjects, type="transform")
        if extraObjects:
            for obj in extraObjects:
                if cmds.objExists(obj):
                    selTranforms.append(obj)

    if not selTranforms:
        if message:
            output.displayWarning("No objects (transform nodes) selected.  Please select an object/s.")
        return
    frozenObjs = checkFrozenTransformOffsetList(selTranforms, message=True)
    return frozenObjs


def checkRotatePivMatchSelection(extraObjects=[], message=True):
    """This function compares the first selected rotate pivot attribute with all others.

    It checks if the pivots match and returns True if they match and False if they don't match.

    :param extraObjects:
    :type extraObjects:
    :param message:
    :type message:
    :return:
    :rtype:
    """
    selTranforms = cmds.ls(selection=True, type="transform")

    if extraObjects:  # extra object checks for UI convenience
        extraObjects = cmds.ls(extraObjects, type="transform")
        if extraObjects:
            for obj in extraObjects:
                if cmds.objExists(obj):
                    selTranforms.append(obj)

    if not selTranforms:
        if message:
            output.displayWarning("No objects (transform nodes) selected.  Please select an object/s.")
        return

    roationPivList = cmds.getAttr(".rotatePivot".format(selTranforms[0]))[0]
    for transform in selTranforms:
        if not checkForMatchVector(transform, roationPivList, attribute="rotatePivot"):
            return False
    return True


# --------------------------
# MATCH PIVOT SPACE
# --------------------------


def matchPivotSpace(objChange, target, message=True):
    """This function will match an object to the other object's rotate and scale pivot space.

    Useful in replace shapes where the shape nodes must match after being frozen.

    The changeObj will change pivot info but will not move in 3d space.

    The change object must be able to be frozen on translate and rotate, no connections.

    :param objChange: The object to change space and pivot info
    :type objChange: str
    :param target: The target object to match
    :type target: str
    """
    # Duplicate obj
    dupObj = cmds.duplicate(objChange)[0]

    # Parent duplicate original under parent of target
    currentParent = cmds.listRelatives(objChange, parent=True)
    targetParent = cmds.listRelatives(target, parent=True)

    # Match pivot information
    removeFreezeTransform(objChange)
    rotPivot = cmds.getAttr("{}.rotatePivot".format(target))[0]
    # cmds.matchTransform([objChange, target], pos=False, rot=False, scl=True, piv=False)
    cmds.setAttr("{}.translate".format(objChange), rotPivot[0], rotPivot[1], rotPivot[2], type="double3")
    cmds.setAttr("{}.rotate".format(objChange), 0.0, 0.0, 0.0, type="double3")
    cmds.setAttr("{}.scale".format(objChange), 1.0, 1.0, 1.0, type="double3")
    cmds.makeIdentity(objChange, apply=True, translate=True, rotate=True, scale=True)

    # Match to duplicate
    cmds.matchTransform([objChange, dupObj], pos=True, rot=True, scl=True, piv=False)

    # Delete duplicate
    cmds.delete(dupObj)

    if message:
        output.displayInfo(
            "Success: The object `{}` has been pivot matched to matched to `{}`.".format(objChange, target))


def matchPivotSpaceSelection():
    """This function will match the first sel object to the second sel object's rotate and scale pivot space.

    Useful in Replace Shapes where the shape nodes must match in pivot space after being frozen.

    The changeObj will change pivot info but will not move in 3d space.

    The change object must be able to be frozen on translate and rotate, no connections.
    """
    objList = cmds.ls(selection=True, type="transform")
    if not objList:
        output.displayWarning("No transform objects selected, please select two objects")
        return
    if len(objList) == 1 or len(objList) > 2:
        output.displayWarning("Please select two objects")
        return
    # Check for connections, locked attrs ------------------
    lockedNodes, lockedAttrs = attributes.getLockedConnectedAttrsList([objList[0]], POS_ROT_ATTRS, keyframes=True)
    if lockedAttrs:
        output.displayWarning("Object `{}` cannot be matched as it has attributes that are locked, "
                              "animated or connected: {}".format(objList[0], lockedAttrs))
        return
    if cmds.referenceQuery(objList[0], isNodeReferenced=True):
        output.displayWarning("The object `{}` is referenced and cannot be matched.".format(objList[0]))
        return
    matchPivotSpace(objList[0], objList[1])
    cmds.select(objList, replace=True)  # return selection
