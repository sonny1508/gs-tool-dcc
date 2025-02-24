"""Code for matching objects.

Example use:

.. code-block:: python

    from zoo.libs.maya.cmds.objutils import matching
    matching.centerOfSelection()

Author: Andrew Silke

"""
import maya.cmds as cmds
import maya.mel as mel

from zoo.libs.maya import zapi
from zoo.libs.utils import output
from zoo.libs.maya.cmds.objutils import namehandling, filtertypes, attributes, selection


def matchZooAlSimpErrConstrain(obj, matchObj):
    """Tries the 2017 new match function, if it fails do the old 2017 constraint version
    cmds.delete(cmds.parentConstraint(obj, matchObj))

    :param obj: the Maya object to match to
    :type obj: str
    :param matchObj: the Maya object to match
    :type matchObj: str
    """
    try:  # 2017 and above Match
        cmds.matchTransform(([matchObj, obj]), pos=1, rot=1, scl=0, piv=0)
        return
    except:  # will fail if not 2017+ and use old style constrain match
        cmds.delete(cmds.parentConstraint(obj, matchObj))


def centerOfMultipleObjects(objs):
    """Finds the averaged center of all objects. Supports components and multiple object selection.

    Note: Face Edge selection is not accurate, better to use matchCenterCluster()
    Note: object centers are not pivot point positions but seems like bounding box centers.

    :param objs: Objects and or flattened components (components not in groups)
    :type objs: list(str)
    :return: The center of the pivot in world coords  x, y, z
    :rtype: list()
    """
    flattenObjs = selection.componentFullList(list(objs))  # flattens to make sure components aren't grouped
    count = len(flattenObjs)
    sums = [0, 0, 0]
    for item in flattenObjs:
        pos = cmds.xform(item, query=True, translation=True, worldSpace=True)
        sums[0] += pos[0]
        sums[1] += pos[1]
        sums[2] += pos[2]
    return [sums[0] / count, sums[1] / count, sums[2] / count]


def centerOfSelection():
    """Finds the averaged center of all selected objects. Supports components and multiple object selection.

    Note: Face Edge selection is not accurate, better to use matchCenterCluster()

    :return: The center of the pivot in world coords  x, y, z
    :rtype: list()
    """
    sel = cmds.ls(selection=True)
    if not sel:
        return None
    return centerOfMultipleObjects(sel)


def matchCenterCluster(obj, matchToObjs, orientToComponents=True):
    """Matches the object to the center of the selection by creating a cluster and then deleting.

    :param obj: A maya object name
    :type obj: str
    :param matchToObjs: A list of objects/components to match to their center
    :type matchToObjs: list(str)
    """
    cmds.select(matchToObjs, replace=True)  # replace orig selection
    cluster = cmds.cluster(name="tempPivot_XXX_clstr")[1]
    cmds.matchTransform(obj, cluster, position=True, rotation=True, scale=False)
    cmds.delete(cluster)


def matchToCenterObjsComponents(obj, matchToObjs, setObjectMode=True, orientToComponents=True,
                                aimVector=(0.0, 1.0, 0.0), localUp=(0.0, 0.0, -1.0),
                                worldUp=(0.0, 1.0, 0.0)):
    """Takes an object and

    #. If no match objs do nothing
    #. If one object selected match to the rotation and translate.
    #. If multiple objects match to the center of all dag objects (bounding boxes I think)
    #. If component selection face/vert/edge match to center of selection via cluster method,
       also uses average normal (faces or verts) to orient.
    #. else do nothing

    :param obj: the object to change (matches to center)
    :type obj:
    :param matchToObjs: A list of objects/components to match to their center
    :type matchToObjs: list(str)
    :param setObjectMode: Returns to object mode if in component mode.
    :type setObjectMode: bool
    :return: True if a match was performed
    :rtype: bool
    """
    if not matchToObjs:
        return False

    # Do the match -----------------
    objOrComponent = selection.componentOrObject(matchToObjs)

    if not objOrComponent or objOrComponent == "uv":  # not a supported object or component
        return False

    dagObjs = cmds.ls(matchToObjs, dag=True)

    if not dagObjs and objOrComponent == "object":
        return False

    if objOrComponent == "object":  # Match to objects
        if len(matchToObjs) == 1:  # One object so match to its pivot
            cmds.matchTransform(([obj, matchToObjs[0]]), pos=1, rot=1, scl=0, piv=0)
            return True
        # Multiple objects so match to average center (not pivot)
        centerPos = centerOfMultipleObjects(matchToObjs)
        cmds.move(centerPos[0], centerPos[1], centerPos[2], obj, absolute=True)
        return True

    # Is components so use matchCenterCluster style, more accurate than centerOfMultipleObjects(matchToObjs)
    matchCenterCluster(obj, matchToObjs, orientToComponents=orientToComponents)

    if orientToComponents:  # does the component orient
        orientGrp = createGroupOrientFromComponents(matchToObjs,
                                                    aimVector=aimVector,
                                                    localUp=localUp,
                                                    worldUp=worldUp)
        cmds.matchTransform(([obj, orientGrp]), pos=0, rot=1, scl=0, piv=0)
        cmds.delete(orientGrp)

    if setObjectMode:
        if cmds.selectMode(query=True, component=True):  # check if in component mode
            mel.eval('SelectTool')  # some tools lock the user from returning to object mode
            cmds.selectMode(object=True)  # return to object mode
            cmds.select(obj, replace=True)
    return True


def groupZeroObj(objName, freezeScale=True, removeSuffixName=""):
    """Groups the selected object, matching the group to the object and zero's the obj.  objName can be long name.

    Will freeze scale by default, the group will not be scaled

    :param objName: The name of the control, can be a long name
    :type objName: str
    :param freezeScale: Freeze the scale of the objName?
    :type freezeScale: bool
    :param removeSuffixName: Don't include this suffix on the group if in the objName, don't include the underscore
    :type removeSuffixName: str
    :return objName: The name of the original object, if fullname the name will have changed, will be unique
    :rtype objName: str
    :return:  The name of the new group, will be a unique name
    :rtype: str
    """
    pureName = namehandling.mayaNamePartTypes(objName)[2]
    pureName = namehandling.stripSuffixExact(pureName, removeSuffixName)  # remove suffix if it exists
    grpName = "_".join([pureName, filtertypes.GROUP_SX])
    grpName = cmds.group(name=grpName, em=True)
    cmds.matchTransform([grpName, objName], pos=1, rot=1, scl=0, piv=0)
    objParent = cmds.listRelatives(objName, parent=True, fullPath=True)
    if objParent:  # then parent to the control's parent, and reset scale
        grpName = cmds.parent(grpName, objParent)[0]
        attributes.resetTransformAttributes(grpName, translate=False, rotate=False, scale=True, visibility=False)
    objName = cmds.parent(objName, grpName)[0]
    if freezeScale:
        if cmds.getAttr(".".join([objName, "scale"]))[0] != (1, 1, 1):  # if scale not 1, 1, 1
            cmds.makeIdentity(objName, apply=True, translate=False, rotate=False, scale=True)  # freeze transform scale
    return objName, grpName


def groupZeroObjList(objList, freezeScale=True, removeSuffixName=""):
    """Groups an object list, matching a new group to each object and zero's the obj.  objNames can be long names.

    Will freeze scale by default, the groups will not be scaled

    :param objList: The names of the controls, can be a long names
    :type objList: list(str)
    :param freezeScale: Freeze the scale of the objName?
    :type freezeScale: bool
    :param removeSuffixName: Don't include this suffix on the group if in the objName, don't include the underscore
    :type removeSuffixName: str
    :return updatedObjList: The names of the original objects, if fullnames the names will have changed, will be unique
    :rtype updatedObjList: list(str)
    :return: The names of the new groups, will be unique names
    :rtype: list(str)
    """
    updatedObjList = list()
    grpList = list()
    for obj in objList:
        obj, grp = groupZeroObj(obj, freezeScale=freezeScale, removeSuffixName=removeSuffixName)
        updatedObjList.append(obj)
        grpList.append(grp)
    return updatedObjList, grpList


def groupZeroObjSelection(freezeScale=True, message=True, removeSuffixName=""):
    """Groups selected objs, matching a new group to each object and zero's the obj.  objNames can be long names.

    Will freeze scale by default, the groups will not be scaled

    :param freezeScale: Freeze the scale of the objName?.
    :type freezeScale: bool
    :param removeSuffixName: Don't include this suffix on the group if in the objName, don't include the underscore.
    :type removeSuffixName: str
    :param message: Return a message to the user.
    :type message: bool
    :return: First Element is the names of the original objects, if fullnames the names \
             will have changed, will be unique. \
             Second Element is the names of the new groups, will be unique names.
    :rtype: tuple[list(str), list(str)]
    """
    selObjs = cmds.ls(selection=True, long=True)
    if not selObjs:
        if message:
            output.displayWarning("Please select an object/s to group")
        return list(), list()
    return groupZeroObjList(selObjs, freezeScale=freezeScale, removeSuffixName=removeSuffixName)


# ---------------
# COMPONENT ORIENTATION - AVERAGE NORMALS
# ---------------


def grouper(it, n):
    """Uses zip py3 r izip py2 to pack a list into groups of n

    :param it: List to group
    :type it: list()
    :param n: Group via n
    :type n: int
    :return: A list of groups now grouped into batches of n
    :rtype: tuple(tuple())
    """
    try:
        from itertools import izip
        return izip(*(iter(it),) * n)
    except ImportError:  # will be 3.x series so fine
        return zip(*(iter(it),) * n)


def averageNormals(normals):
    """Given many normals [[0.1, 0.9, 0.0], [0.0, 0.5, 0.5]] return the average, [0.5, 0.75, 0.25]

    :param normals: A list of three values (normals)
    :type normals: list(list(float))
    :return: The normals all averaged.
    :rtype: list(float)
    """
    addedVectors = [0, 0, 0]
    for x, y, z in normals:
        addedVectors[0] += x
        addedVectors[1] += y
        addedVectors[2] += z
    amountDivisor = float(len(normals))
    return [x / amountDivisor for x in addedVectors]


def averageVertNormals(verts):
    """Given a list of vertices return their averaged normals.

    :param verts: A list of Maya vertices
    :type verts: list(str)
    :return: The normals all averaged.
    :rtype: list(float)
    """
    # Get the normals
    normals = cmds.polyNormalPerVertex(verts, query=True, xyz=True)
    # Group normals so nice lists
    normals = list(grouper(normals, 3))
    return averageNormals(normals)


def faceNormals(faces):
    """Returns a list of face normals from a list of faces.

    :param faces: A list of Maya faces
    :type faces: list(str)
    :return: A list of face normals
    :rtype: list(list(float))
    """
    fNormals = list()
    normStrList = cmds.polyInfo(faces, faceNormals=True)
    for nStr in normStrList:
        fN = nStr.split()
        del fN[0:2]
        fN = [float(x) for x in fN]
        fNormals.append(fN)
    return fNormals


def averageFaceNormals(faces):
    """Given a list of faces return their averaged normals.

    :param faces: A list of Maya faces
    :type faces: list(str)
    :return: The normals all averaged.
    :rtype: list(float)
    """
    normals = faceNormals(faces)
    return averageNormals(normals)


def createGroupFromVector(vector, aimVector=(0.0, 1.0, 0.0), localUp=(0.0, 0.0, -1.0), worldUp=(0.0, 1.0, 0.0),
                          relativeObject=""):
    """Creates a group oriented along a vector, builds and aim constraint and deletes.

    If a relative object is given uses the objects world space and not local space.

    :param vector: A vector direction, list with three floats.
    :type vector: list(float)
    :param aimVector: The direction to aim the group
    :type aimVector: list(float)
    :param localUp: The direction to aim the group up
    :type localUp: list(float)
    :param worldUp: The world up of the aim
    :type worldUp: list(float)
    :param relativeObject: Take into consideration the relative rotation of a given object.
    :type relativeObject: str
    :return: The group/transform now oriented as per the vector.
    :rtype: str
    """
    aimObj = zapi.nodeByName(cmds.group(empty=True))
    aimGroup = zapi.nodeByName(cmds.group(empty=True))

    if relativeObject:  # parent and zero
        cmds.parent(str(aimObj), relativeObject)
        cmds.parent(str(aimGroup), relativeObject)
        attributes.resetTransformAttributes(str(aimObj))
        attributes.resetTransformAttributes(str(aimGroup))

    cmds.setAttr("{}.translate".format(str(aimGroup)), vector[0], vector[1], vector[2], type="float3")

    if relativeObject:
        cmds.delete(cmds.aimConstraint(str(aimGroup), str(aimObj), aimVector=aimVector, upVector=localUp,
                                       worldUpVector=worldUp, worldUpObject=relativeObject,
                                       worldUpType="objectrotation"))
    else:
        cmds.delete(cmds.aimConstraint(str(aimGroup), str(aimObj), aimVector=aimVector, upVector=localUp,
                                       worldUpVector=worldUp))

    cmds.delete(str(aimGroup))
    return str(aimObj)


def createGroupOrientFromVertices(verts, aimVector=(0.0, 1.0, 0.0), localUp=(0.0, 0.0, -1.0), worldUp=(0.0, 1.0, 0.0)):
    """Creates a group oriented to the average vector of the selected vertices, uses vertex normals.

    :param verts: Maya components needs to be vertices only.
    :type verts: list(str)
    :param aimVector: The direction to aim the group
    :type aimVector: list(float)
    :param localUp: The direction to aim the group up
    :type localUp: list(float)
    :param worldUp: The world up of the aim
    :type worldUp: list(float)
    :return: The group/transform now oriented as per the vector.
    :rtype: str
    """
    aveNormal = averageVertNormals(verts)
    relativeObject = verts[0].split(".")[0]
    return createGroupFromVector(aveNormal, aimVector=aimVector, localUp=localUp, worldUp=worldUp,
                                 relativeObject=relativeObject)


def createGroupOrientFromFaces(faces, aimVector=(0.0, 1.0, 0.0), localUp=(0.0, 0.0, -1.0), worldUp=(0.0, 1.0, 0.0)):
    """Creates a group oriented to the average vector of the selected faces, uses face normals.

    :param faces: Maya components needs to be faces only.
    :type faces: list(str)
    :param aimVector: The direction to aim the group
    :type aimVector: list(float)
    :param localUp: The direction to aim the group up
    :type localUp: list(float)
    :param worldUp: The world up of the aim
    :type worldUp: list(float)
    :return: The group/transform now oriented as per the vector.
    :rtype: str
    """
    aveNormal = averageFaceNormals(faces)
    relativeObject = faces[0].split(".")[0]
    return createGroupFromVector(aveNormal, aimVector=aimVector, localUp=localUp, worldUp=worldUp,
                                 relativeObject=relativeObject)


def createGroupOrientFromComponents(components, aimVector=(0.0, 1.0, 0.0), localUp=(0.0, 0.0, -1.0),
                                    worldUp=(0.0, 1.0, 0.0)):
    """Creates a group oriented to the average vector of the selected verts/edges/faces::

        Edges are converted to verts.
        Verts use vertex normals.
        Faces use face normals.

    :param components: Maya components needs to be edges, verts or faces.
    :type components: list(str)
    :param aimVector: The direction to aim the group
    :type aimVector: list(float)
    :param localUp: The direction to aim the group up
    :type localUp: list(float)
    :param worldUp: The world up of the aim
    :type worldUp: list(float)
    :return: The group/transform now oriented as per the vector.
    :rtype: str
    """
    selType = selection.componentSelectionType(components)

    if selType == "edges":  # convert to verts, edges don't have normals
        cmds.select(components, replace=True)
        components = selection.convertSelection(type="vertices")
        selType = "vertices"

    if selType == "vertices":
        return createGroupOrientFromVertices(components, aimVector=aimVector, localUp=localUp, worldUp=worldUp)
    elif selType == "faces":
        return createGroupOrientFromFaces(components, aimVector=aimVector, localUp=localUp, worldUp=worldUp)
