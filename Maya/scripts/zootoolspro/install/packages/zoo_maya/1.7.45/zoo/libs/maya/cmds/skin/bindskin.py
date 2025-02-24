"""Functions for skin binding

Examples
# bindskin hierarchy (closest distance)
from zoo.libs.maya.cmds.skin import bindskin
bindskin.bindSkinSelected(toSelectedBones=False, maximumInfluences=5, maxEditLimit=5, bindMethod=0, displayMessage=True)

# bindskin selected (closest distance)
from zoo.libs.maya.cmds.skin import bindskin
bindskin.bindSkinSelected(toSelectedBones=True, maximumInfluences=5, maxEditLimit=5, bindMethod=0, displayMessage=True)

# bindskin selected rigid bind (closest distance)
from zoo.libs.maya.cmds.skin import bindskin
bindskin.bindSkinSelected(toSelectedBones=True, maximumInfluences=0, maxEditLimit=5, bindMethod=0, displayMessage=True)

# bind skin heat map
from zoo.libs.maya.cmds.skin import bindskin
bindskin.bindSkinSelected(bindMethod=2)

#bind skin geodesic
from zoo.libs.maya.cmds.skin import bindskin
bindskin.bindSkinSelected(bindMethod=3)

# mirror x to -x
from zoo.libs.maya.cmds.skin import bindskin
bindskin.mirrorSkinSelection(mirrorMode='YZ', mirrorInverse=False)

# mirror -x to x
from zoo.libs.maya.cmds.skin import bindskin
bindskin.mirrorSkinSelection(mirrorMode='YZ', mirrorInverse=True)

# remove influence
from zoo.libs.maya.cmds.skin import bindskin
bindskin.removeInfluenceSelected()

# transfer skin weights zoo
from zoo.libs.maya.cmds.skin import bindskin
bindskin.transferSkinWeightsSelected()

# add joints to skin cluster
from zoo.libs.maya.cmds.skin import bindskin
bindskin.addJointsToSkinnedSelected()

# unbind skin
from zoo.libs.maya.cmds.skin import bindskin
bindskin.unbindSkinSelected()

# duplicate mesh before bind - orig shape duplicate
from zoo.libs.maya.cmds.skin import bindskin
bindskin.duplicateSelectedBeforeBind()

# change skin method to weight belnded (dual quat)
from zoo.libs.maya.cmds.skin import bindskin
bindskin.skinClusterMethodSwitch(skinningMethod=2, displayMessage=True)

# copy skin weights to the clipboard (mesh name is cpied and must be in scene for paste)
from zoo.libs.maya.cmds.skin import bindskin
bindskin.copySkinWeightsSel()

# paste skin weights from the copied mesh, see copySkinWeightsSel()
from zoo.libs.maya.cmds.skin import bindskin
bindskin.pasteSkinWeightsSel()

"""

from zoovendor import six
from zoo.core.util import classtypes

import maya.cmds as cmds
import maya.mel as mel

from zoo.libs.utils import output
from zoo.libs.maya.utils import mayaenv
from zoo.libs.maya.cmds.objutils import shapenodes, namehandling, attributes, selection
from zoo.core.util import zlogging
from zoo.libs.maya.cmds.shaders import shaderutils

logger = zlogging.getLogger(__name__)
MAYA_VERSION = float(mayaenv.mayaVersionNiceName())


def hammerWeights():
    mel.eval("weightHammerVerts;")


"""
GET ALL
"""


def getAllSkinClusters(displayMessage=False):
    """Returns all valid skin clusters in a scene

    :param displayMessage:  Report the message inside of maya?
    :type displayMessage: bool
    :return skinClusterList: List of the skin cluster node names
    :rtype skinClusterList: list
    """
    skinClusterList = cmds.ls(type='skinCluster')  # get all skin clusters in scene
    if not skinClusterList:
        if displayMessage:
            output.displayWarning("No skinClusters Exist In The Scene")
        return
    return skinClusterList


"""
CLEAN VALIDATE
"""


def checkValidOrigShape(mesh, deleteDeadShapes=False, displayMessage=False):
    """Checks for valid orig shape nodes, by checking if multiple orig shapes are present
    or that the object isn't skinned or has no orig shape nodes
    returns the the orig shape node name or None on fail

    :param mesh: the object name to check
    :type mesh: str
    :param displayMessage: Report the message inside of maya?
    :type displayMessage: bool
    :return originalShape: The original shape node returned
    :rtype: str
    """

    mshShortName = namehandling.getUniqueShortName(mesh)
    originalShapeList = shapenodes.getOrigShapeNodes(mesh, fullPath=True)
    if not originalShapeList:
        if not getSkinCluster(mesh):
            output.displayWarning("There's no skin cluster on this object `{}`, must have "
                                  "skinning/deformation".format(mshShortName))
            return
        output.displayWarning("This object `{}` is missing an original shape node it should have one,"
                              " best to rebuild the skinning".format(mshShortName))
        return
    for i, shape in reversed(list(enumerate(originalShapeList))):  # tests for legit nodes from outgoing connections
        outputs = cmds.listConnections(shape, destination=True, source=False)
        if not outputs:
            if deleteDeadShapes:  # do Maya delete on this as it's most likely a dead origShape and worthless
                cmds.delete(originalShapeList[i])
                if displayMessage:
                    currentOriginalShape = namehandling.getUniqueShortName(originalShapeList[i])
                    output.displayInfo("Dead Original Mesh Deleted: {}".format(currentOriginalShape))
            # remove from list
            del originalShapeList[i]
    if len(originalShapeList) > 1:  # Rare cases more than one live intermediate object is found, like a UvProjection
        for orig in originalShapeList:  # Remove the end numbers and search if endsWith "Orig"
            origNumberlessEnd = ''.join([i for i in orig if not i.isdigit()])  # strip all numbers
            if origNumberlessEnd.endswith("Orig"):
                originalShapeList = [orig]  # Name found so break
                break
    if len(originalShapeList) < 1:  # This test shouldn't occur, if so very rare
        output.displayWarning("There's more than one legitimate Original Shape Node on object `{}`. A fix is to "
                              "save skin weights, unbind the skin and obj clean the object, re import"
                              " skin. Can also be planarProjection or another issue.".format(mshShortName))
        return originalShapeList[0]
    # else tests passed
    return originalShapeList[0]


def checkValidOrigShapeList(meshList, deleteDeadShapes=False, displayMessage=False):
    """List version of the function checkValidOrigShape

    :param meshList: list of mesh objects
    :type meshlist: list
    :param deleteDeadShapes: delete any dead original nodes while checking?
    :type deleteDeadShapes: bool
    :param displayMessage: Report the message inside of maya?
    :type displayMessage: bool
    :return origShapeList: list of original shape nodes (intermediate objects)
    :rtype origShapeList: list
    """
    origShapeList = list()
    for mesh in meshList:
        origShapeList.append(
            checkValidOrigShape(mesh, deleteDeadShapes=deleteDeadShapes, displayMessage=displayMessage))
    return origShapeList


def cleanDeadOrigShapesSelected(displayMessage=True):
    """Cleans the unused original shape nodes from selected mesh
    Nodes are likely intermediate objects with no output connections, usually left over and unused nodes

    :param displayMessage: Report the message inside of maya?
    :type displayMessage: bool
    """
    selObj = cmds.ls(selection=True, long=True)
    checkValidOrigShapeList(selObj, deleteDeadShapes=True, displayMessage=displayMessage)
    if displayMessage:
        selObjUniqueShortNames = namehandling.getUniqueShortNameList(selObj)
        output.displayInfo("Meshes Cleaned {}, see script editor for details".format(selObjUniqueShortNames))


"""
DUPLICATE ORIGINAL
"""


def duplicateMeshBeforeBind(mesh, fullPath=True, suffix="_duplicate", message=True, deleteDeadShapes=False,
                            transferShader=True):
    """Given a mesh will duplicate it ignoring the skinning, does this via the original shape node.
    Will fail if mesh isn't skinned or no orig node

    :param mesh: The mesh name to be duplicated
    :type mesh: str
    :param fullPath: return full path names not short
    :type fullPath: bool
    :param suffix: The suffix to add to the duplicated mesh
    :type suffix: str
    :param message: Report the message inside of maya?
    :type message: bool
    :param transferShader: Transfer the shader from the skinned mesh so that the new duplicate matches?
    :type transferShader: bool
    :return duplicateMesh: the name of the duplicated mesh
    :rtype: str
    """
    mshShortUniqueName = namehandling.getUniqueShortName(mesh)
    longPrefix, namespace, mshShortUniqueName = namehandling.mayaNamePartTypes(mshShortUniqueName)
    # get orig shape
    originalShapeNode = checkValidOrigShape(mesh, deleteDeadShapes=deleteDeadShapes, displayMessage=message)
    if not originalShapeNode:
        return
    tempDuplicateMesh = cmds.duplicate(originalShapeNode, name="".join([mshShortUniqueName, "_tempDup"]),
                                       returnRootsOnly=True)
    tDupShapesList = shapenodes.filterNotOrigNodes(tempDuplicateMesh, fullPath=fullPath)  # get shape of the new mesh
    # get origShape of the new mesh
    tDupShapesOrigList = shapenodes.getOrigShapeNodes(tempDuplicateMesh, fullPath=fullPath)
    # connect outMesh to inMesh
    cmds.connectAttr('{}.outMesh'.format(tDupShapesOrigList[0]), '{}.inMesh'.format(tDupShapesList[0]))
    # duplicate again to lock in shape
    duplicateMesh = (cmds.duplicate(tempDuplicateMesh, name="".join([mshShortUniqueName, suffix]),
                                    returnRootsOnly=True))[0]
    dupShapesOrigList = shapenodes.getOrigShapeNodes(duplicateMesh, fullPath=fullPath)
    for origShape in dupShapesOrigList:
        cmds.delete(origShape)
    cmds.delete(tempDuplicateMesh)
    attributes.unlockSRTV(duplicateMesh)  # unlock attributes on duplicate
    if transferShader:  # transfer shader by topology and if not then find the first shader and use it
        shaderutils.transferShaderTopology(mesh, duplicateMesh, ignoreTopologyMismatch=True, message=True)
    if message:
        output.displayInfo("Success: The object `{}` has been duplicated to "
                           "object `{}".format(mshShortUniqueName, duplicateMesh))
    return duplicateMesh


def duplicateSelectedBeforeBind(fullPath=True, suffix="_duplicate", message=True, selectDuplicate=True,
                                transferShader=True):
    """Duplicates selected mesh/es before a skin cluster has been added, pre bind.
    Will fail if no skinning is present.
    Works by finding the original shape node and duplicating it

    :param fullPath: return full path names not short
    :type fullPath: bool
    :param suffix: The suffix to add to the duplicated mesh
    :type suffix: str
    :param message: Report the message inside of maya?
    :type message: bool
    :param transferShader: Transfer the shader from the skinned mesh so that the new duplicate matches?
    :type transferShader: bool
    :return duplicatedMeshes: a list of the duplicated mesh names
    :rtype: list
    """
    selObjList = cmds.ls(selection=True, long=True)
    if not selObjList:
        output.displayWarning("No Mesh Selected, Please Select A Skinned or Deformed Mesh")
    duplicatedMeshes = list()
    for obj in selObjList:
        duplicatedMeshes.append(duplicateMeshBeforeBind(obj, fullPath=fullPath, suffix=suffix,
                                                        message=message, transferShader=transferShader))
        duplicatedMeshes = filter(None, duplicatedMeshes)
    if selectDuplicate:
        cmds.select(duplicatedMeshes, replace=True)
    return duplicatedMeshes


"""
COMBINE SKINNING
"""


def combineSkinnedMeshes(objList, constructionHistory=False, centerPivot=True, mergeUVSets=True):
    """Combines meshes that have been skinned, joins them into one skinned object.

    :param objList: A list of mesh objects
    :type objList: list(str)
    :param constructionHistory: Delete the construction history?
    :type constructionHistory: bool
    :param centerPivot: Center the pivot after combine
    :type centerPivot: bool
    :param mergeUVSets: Merge the UV sets?
    :type mergeUVSets: bool

    :return mesh: The combined mesh name
    :rtype mesh: str
    :return skinCluster: The combined skin cluster name
    :rtype skinCluster: str
    """
    nodeList = cmds.polyUniteSkinned(objList,
                                     constructionHistory=constructionHistory,
                                     centerPivot=centerPivot,
                                     mergeUVSets=mergeUVSets)
    return nodeList[0], nodeList[1]


def combineSkinnedMeshesSelected(constructionHistory=False, centerPivot=True, mergeUVSets=True, message=True):
    """Combines selected meshes that have been skinned, joins them into one skinned object.

    :param constructionHistory: Delete the construction history?
    :type constructionHistory: bool
    :param centerPivot: Center the pivot after combine
    :type centerPivot: bool
    :param mergeUVSets: Merge the UV sets?
    :type mergeUVSets: bool
    :param message: Report a message to the user?
    :type message: True
    :return:
    :rtype:
    """
    meshes = filterMeshes(cmds.ls(selection=True, long=True), skinned=False)
    skinnedMeshes = filterMeshes(cmds.ls(selection=True, long=True), skinned=True)
    if not meshes:
        if message:
            output.displayWarning("No polygon meshes selected, please select meshes")
        return
    if not skinnedMeshes:
        if message:
            output.displayWarning("No skinned polygon meshes selected, please at least one skinned mesh")
        return
    if len(meshes) == 1:
        if message:
            output.displayWarning("Only one mesh selected, please select "
                                  "multiple. {}".format(namehandling.getShortNameList(meshes)))
        return
    combineSkinnedMeshes(meshes,
                         constructionHistory=constructionHistory,
                         centerPivot=centerPivot,
                         mergeUVSets=mergeUVSets)


"""
GET AND FILTER
"""


def getSkinCluster(obj):
    """Checks if the given object has a skin cluster using mel, (doesn't have a python equivalent).
    Long or short names must be converted to unique names, see namehandling.getUniqueShortName() documentation
    Returns empty string if no skin cluster found on object

    :param obj: Maya obj name, usually a transform node, best if a long or unique name
    :type obj: str
    :return skinCluster: The name of the skin cluster, or if not found/skinned will be an empty string ""
    :rtype skinned: str
    """
    objUniqueName = namehandling.getUniqueShortName(obj)
    return mel.eval('findRelatedSkinCluster {}'.format(objUniqueName))


def getSkinClusterList(objList):
    """Returns a list of skin clusters from an objList

    :param objList: Maya obj name list
    :type objList: list
    :return skinClusterList: list of skin clusters
    :rtype skinClusterList: list
    """
    skinClusterList = list()
    for obj in objList:
        skinCluster = getSkinCluster(obj)
        if skinCluster:
            skinClusterList.append(skinCluster)
    return skinClusterList


def getSkinClustersSelected():
    """Find all the skin clusters related to selected objects (transforms)
    Works off the first shape node and selected must be the transform/s
    """
    objList = cmds.ls(selection=True, long=True)
    skinClusterList = getSkinClusterList(objList)
    return skinClusterList


def getJnts(objList):
    """returns only joints from an object list

    :param objList: list of object names
    :type objList: list
    :return jntList: List of joint names
    :rtype jntList: list
    """
    jntList = list()
    for obj in objList:
        if cmds.objectType(obj, isType='joint'):
            jntList.append(obj)
    return jntList


def getSkinClusterFromJoint(joint):
    """Returns all skin clusters connected to a single joint

    :param joint: A single joint name
    :type joint: str
    :return skinClusterList: A list of skin clusters, will be empty if none found
    :rtype skinClusterList: list(str)
    """
    skinClusterList = list()
    jointAttr = ".".join([joint, "worldMatrix"])
    destinationAttrs = cmds.listConnections(jointAttr, destination=True, source=True, plugs=True)
    if destinationAttrs:
        for attr in destinationAttrs:
            node = attr.split(".")[0]
            if cmds.nodeType(node) == "skinCluster":
                skinClusterList.append(node)
    return skinClusterList


def getSkinClustersFromJoints(jointList):
    """Returns all skin clusters connected to a joint list

    :param jointList: A list of Maya joint names
    :type jointList: list(str)
    :return skinClusterList: A list of skin clusters, will be empty if none found
    :rtype skinClusterList: list(str)
    """
    skinClusterList = list()
    for jnt in jointList:
        skinClusterList += getSkinClusterFromJoint(jnt)
    return list(set(skinClusterList))


def filterSkinnedJoints(jointList):
    """Returns all skinned joints from a joint list.  Found by seeing connected skin clusters to joint.worldMatrix

    :param jointList: A list of joints
    :type jointList: list(str)
    :return skinnedJointList: A list of skinned joints
    :rtype skinnedJointList: list(str)
    """
    skinnedJointList = list()
    for jnt in jointList:
        if getSkinClusterFromJoint(jnt):
            skinnedJointList.append(jnt)
    return skinnedJointList


def filterSkinnedMeshes(objList):
    """Returns meshes that are skinned from a list

    :param objList: list of Maya object names
    :type objList: list
    :return skinnedMeshes: list of skinned meshes
    :rtype skinnedMeshes: list
    """
    skinnedMeshes = list()
    for obj in objList:
        if getSkinCluster(obj):
            skinnedMeshes.append(obj)
    return skinnedMeshes


def filterMeshes(objList, skinned=False):
    """Returns meshes/surfaces and joints that are ready for skinning from the list of objects

    Tests for issues and reports errors

    :param objList: list of maya objects/nodes
    :type objList: list(str)

    :return meshList: list of mesh names, empty list if none
    :rtype meshList: list(str)
    """
    meshes = list()
    for obj in objList:
        shapes = cmds.listRelatives(obj, shapes=True, fullPath=True)
        if shapes:
            for shape in shapes:
                if cmds.objectType(shape, isType='mesh'):
                    if skinned:
                        if getSkinCluster(obj):
                            meshes.append(obj)
                            break
                    else:
                        meshes.append(obj)
                        break
    return meshes


def filterObjsForSkin(objList):
    """Returns meshes/surfaces/curves and joints that are ready for skinning from the list of objects

    Tests for issues and reports errors

    :param skinningMethod: 0 = classic linear, 1 = dual quaternion, 2 = weight blended
    :type skinningMethod: int
    :return: List of joint names and a list of mesh/surface or nurbs curve names
    :rtype: tuple(list(str), list(str))
    """
    skinClusters = list()
    meshesSurfacesCurves = list()
    joints = list()
    for obj in objList:
        if cmds.objectType(obj, isType='joint'):
            joints.append(obj)  # add because joint
            continue
        shapes = cmds.listRelatives(obj, shapes=True, fullPath=True)
        if shapes:
            for shape in shapes:
                cluster = getSkinCluster(obj)
                if cmds.objectType(shape, isType='mesh') or cmds.objectType(shape, isType='nurbsSurface') \
                        or cmds.objectType(shape, isType='nurbsCurve'):
                    meshesSurfacesCurves.append(obj)
                    if cluster:
                        skinClusters.append(cluster)
    return joints, list(set(meshesSurfacesCurves)), list(set(skinClusters))


def skinClusterMethodSwitch(skinningMethod=2, displayMessage=True):
    """Switches the attribute .skinningMethod for all skinClusters on selected objects

    :param skinningMethod: 0 = classic linear, 1 = dual quaternion, 2 = weight blended
    :type skinningMethod: int
    :param displayMessage: Report the message inside of maya?
    :type displayMessage: bool
    """
    skinClusterList = getSkinClustersSelected()
    if not skinClusterList:
        output.displayWarning("No skin clusters found on selected")
        return
    for skinCluster in skinClusterList:
        cmds.setAttr("{}.skinningMethod".format(skinCluster), skinningMethod)
    if skinningMethod == 0:
        skinMethodName = "Classic Linear"
    elif skinningMethod == 1:
        skinMethodName = "Dual Quaternion"
    else:
        skinMethodName = "Weight Blended"
    if displayMessage:
        skinClusterNames = ", ".join(skinClusterList)
        output.displayInfo("Skin Clusters Changed to '{}': {}".format(skinMethodName, skinClusterNames))


"""
UNBIND SKINNING
"""


def unbindSkinObjs(objList):
    """Python version of Maya's unbind skin, this function is for an object list
    """
    for obj in objList:
        skinCluster = getSkinCluster(obj)
        if skinCluster:  # then mesh is skinned
            cmds.skinCluster(skinCluster, edit=True, unbind=True)
            output.displayInfo("Skin Cluster `{}` Deleted".format(skinCluster))


def unbindSkinSelected():
    """python version of unbind skin on selected
    """
    selObj = cmds.ls(selection=True, long=True)
    if not selObj:
        output.displayWarning("No Objects Selected:  Please Selected Skinned Objects")
    unbindSkinObjs(selObj)


"""
BIND SKIN
"""


def bindSkin(joints, meshes, toSelectedBones=True, maximumInfluences=5, maxEditLimit=5, bindMethod=0,
             displayMessage=True):
    """Skins meshes to joints based with skin variables

    :param toSelectedBones: on binds to selected off binds to hierarchy
    :type toSelectedBones: bool
    :param maxInfluences: 5 is default, 1 is a rigid bind, limits the amount of joint influences
    :type maxInfluences: int
    :param maxEditLimit:  is after the weights have been assigned so influences can be set differently for skin editing
    :type maxEditLimit: int
    :param bindMethod: closest distance = 0, hierarchy = 1, heat = 2 and geodesic = 3
    :type bindMethod: int
    :param displayMessage: Report the message inside of maya?
    :type displayMessage: bool
    """
    skinClusters = list()
    geodesic = False
    if bindMethod == 3:  # is geodesic with unique options, must be bound then switched with cmds.geomBind
        bindMethod = 0
        geodesic = True
    for mesh in meshes:
        if MAYA_VERSION >= 2024.0:  # Maya 2024 and up can have multiple skin clusters
            skinClusters.append((cmds.skinCluster(joints, mesh, toSelectedBones=toSelectedBones,
                                                  maximumInfluences=maximumInfluences, bindMethod=bindMethod,
                                                  multi=True))[0])
        else:
            skinClusters.append((cmds.skinCluster(joints, mesh, toSelectedBones=toSelectedBones,
                                                  maximumInfluences=maximumInfluences, bindMethod=bindMethod))[0])

    for skinCluster in skinClusters:
        if geodesic:  # if geodesic bind this is needed
            cmds.geomBind(skinCluster, bindMethod=3, falloff=0.2, maxInfluences=maximumInfluences,
                          geodesicVoxelParams=(256, True))
        cmds.setAttr("{}.maintainMaxInfluences".format(skinCluster), 1)
        cmds.setAttr("{}.maxInfluences".format(skinCluster), maxEditLimit)
    if displayMessage:
        meshes = namehandling.getUniqueShortNameList(meshes)
        joints = namehandling.getUniqueShortNameList(joints)
        meshesStr = ", ".join(meshes)
        jointsStr = ", ".join(joints)
        hierarchyMessage = ""
        if not toSelectedBones:
            hierarchyMessage = "And It's Hierarchy"
        output.displayInfo("Success: Mesh `{}` Bound To Joints: {} {}".format(meshesStr, jointsStr,
                                                                              hierarchyMessage))


def bindSkinSelected(toSelectedBones=True, maximumInfluences=5, maxEditLimit=5, bindMethod=0, displayMessage=True):
    """Binds skin to mesh or meshes based off selection similar to the regular Maya behaviour.  No in built cmds version

    :param toSelectedBones: on binds to selected off binds to hierarchy
    :type toSelectedBones: bool
    :param maxInfluences: 5 is default, 1 is a rigid bind, limits the amount of joint influences
    :type maxInfluences: int
    :param maxEditLimit: is after the weights have been assigned so influences can be set differently for skin editing
    :type maxEditLimit: int
    :param: bindMethod: 0 = distance = 1 = hierarchy, 2 = heat, 3 = geodesic
    :type bindMethod: int
    :param displayMessage: Report the message inside of maya?
    :type displayMessage: bool
    """
    selObjs = cmds.ls(selection=True, long=True)
    joints, meshesSurfacesCurves, skinClusters = filterObjsForSkin(selObjs)
    if not meshesSurfacesCurves or not joints:
        output.displayWarning("The selection does not contain both joints and unskinned meshes/surfaces, "
                              "please select and try again")
        return
    elif skinClusters and MAYA_VERSION < 2024.0:
        output.displayWarning("Some of the selected objects are already skinned, please select and try again.")
        return

    bindSkin(joints, meshesSurfacesCurves, toSelectedBones=toSelectedBones, maximumInfluences=maximumInfluences,
             maxEditLimit=maxEditLimit, bindMethod=bindMethod, displayMessage=displayMessage)


"""
INFLUENCES
"""


def setMaxInfluencesOnSkinCluster(skinCluster, maxInfluences=4):
    """for a skin cluster set the max influences and turn maintain on

    :param skinCluster: skin cluster name
    :type skinCluster: str
    :param maxInfluences: the max influences
    :type maxInfluences: bool
    """
    cmds.setAttr("{}.maintainMaxInfluences".format(skinCluster), 1)
    cmds.setAttr("{}.maxInfluences".format(skinCluster), maxInfluences)


def setMaxInfluencesOnSkinClusterList(skinClusterList, maxInfluences=4):
    for skinCluster in skinClusterList:
        setMaxInfluencesOnSkinCluster(skinCluster, maxInfluences=maxInfluences)


def setMaxInfluencesOnSkinSelected(maxInfluences=4):
    selObjs = cmds.ls(selection=True, long=True)
    skinClusterList = getSkinClusterList(selObjs)
    if not skinClusterList:
        output.displayWarning("The selection does not contain objects with skin clusters, "
                              "please select and try again")
        return
    setMaxInfluencesOnSkinClusterList(skinClusterList, maxInfluences=maxInfluences)
    output.displayInfo("Success: Max Influences Set To '{}' on {}".format(maxInfluences, skinClusterList))


def checkInfluenceObj(obj, skinCluster):
    """Checks if an object is an influece of a skin cluster

    :param obj: Maya obj name
    :type obj: str
    :param skinCluster: skin cluster name
    :type skinCluster: str
    :return influence: True if the object is an influence
    :rtype influence: bool
    """
    skinInfluences = cmds.skinCluster(skinCluster, query=True, influence=True)
    obj = namehandling.getUniqueShortName(obj)
    for influenceObj in skinInfluences:
        if obj == influenceObj:
            return True


def renameSelSkinClusters(suffix="skin"):
    """Renames the skin clusters based off the selected object

    :param suffix: skin cluster of pCube1 will be named pCube1_skin
    :type suffix: str
    """
    sel = cmds.ls(selection=True)
    if not sel:
        output.displayWarning("Please select object/s to rename their skin clusters.")
        return
    skinClusters = list()
    for obj in sel:
        skinCluster = getSkinCluster(obj)
        if skinCluster:
            cluster = cmds.rename(skinCluster, "_".join([namehandling.getShortName(obj), suffix]))
            skinClusters.append(cluster)
    if skinClusters:
        output.displayInfo("Success: Skin Clusters Renamed: {}".format(skinClusters))
    else:
        output.displayWarning("No skin clusters found on the selected objects")
    return skinClusters


"""
ADD REMOVE JOINTS
"""


def removeInfluence(objList, skinCluster):
    """Removes Influence Objects from a Skin Cluster
    Checks if influences are valid
    Returns object list of influences removed


    :param objList: the list of influence objects to be removed
    :type objList:
    :param skinCluster: The skin luster name
    :type skinCluster: str
    :return removedInfluenceList: list of influence objects removed
    :rtype: list
    """
    removedInfluenceList = list()
    for obj in objList:
        if checkInfluenceObj(obj, skinCluster):
            cmds.skinCluster(skinCluster, removeInfluence=obj, edit=True)
            removedInfluenceList.append(obj)
    return removedInfluenceList


def removeInfluenceSelected():
    """Removes influence objects from a skinned mesh.
    Last selected object should be the skinned mesh, other objects are the influences
    Will check for user error
    """
    objList = cmds.ls(selection=True, long=True)
    if not objList:
        output.displayWarning("No joints/meshes are selected.  Please select joint/s and then a mesh.")
        return
    if len(objList) < 2:
        output.displayWarning("Only one object was selected.  Please select joint/s and then a mesh.")
        return
    # get obj and joint list
    lastObj = objList[-1]
    del objList[-1]
    skinCluster = getSkinCluster(lastObj)
    if not skinCluster:
        lastObj = namehandling.getUniqueShortName(lastObj)
        output.displayWarning(
            "Last obj in selection `{}` is not a skinned mesh. Please select in order.".format(lastObj))
        return
    removedInfluenceList = removeInfluence(objList, skinCluster)
    if not removedInfluenceList:
        output.displayWarning("No Influence Objects found of Skin Cluster `{}`".format(skinCluster))
        return
    removedInfluenceList = namehandling.getUniqueShortNameList(removedInfluenceList)
    output.displayInfo("Success: Influences removed `{}`".format(removedInfluenceList))


def addJointsToSkinned(jointList, skinClusterList):
    """Adds joints as new influences to a skin cluster
    Select the mesh/es with skin cluster and the joints to assign
    jnts are assigned with zero weighting and do not affect existing weights

    should check this no need for try
    """
    for skinCluster in skinClusterList:
        try:
            cmds.skinCluster(skinCluster, edit=True, addInfluence=jointList, weight=0, lockWeights=1)
        except RuntimeError:
            output.displayWarning("Influence object `{}` is already attached".format(skinCluster))
        for jnt in jointList:  # unlock weights that were previously locked to be safe while adding
            cmds.skinCluster(skinCluster, influence=jnt, edit=True, lockWeights=0)


def addJointsToSkinnedSelected(displayMessage=True):
    """Adds joints to a skinned mesh, keeps the joints with a zero influence value

    :param displayMessage: Report the message inside of maya?
    :type displayMessage: bool
    """
    objList = cmds.ls(selection=True, long=True)
    jointList = getJnts(objList)
    skinClusterList = getSkinClusterList(objList)
    if not skinClusterList or not jointList:  # error
        output.displayWarning("The selection does not contain both joints and meshes/surfaces with skinClusters, "
                              "please select and try again")
        return
    addJointsToSkinned(jointList, skinClusterList)
    if displayMessage:
        skinClustersStr = ", ".join(skinClusterList)
        output.displayInfo("Success: Selected joints are now bound to "
                           "SkinCluster/s: '{}' ".format(skinClustersStr))


"""
DISABLE ENABLE TOGGLE SKIN CLUSTERS
"""


def disableSkinCluster(skinCluster):
    """Disables a single skin cluster

    :param skinCluster: A single skin cluster name
    :type skinCluster: str
    """
    cmds.setAttr("{}.nodeState".format(skinCluster), 1)


def disableSkinClusterList(skinClusterList, displayMessage=True):
    """Disables a skin cluster list turning the node state to hasNoEffect (1)

    :param skinClusterList: List of the skin cluster node names
    :type skinClusterList: list
    :param displayMessage: Report the message inside of maya?
    :type displayMessage: bool
    """
    for skinCluster in skinClusterList:  # disable all skin clusters
        cmds.setAttr("{}.nodeState".format(skinCluster), 1)
    if displayMessage:
        output.displayInfo("Skin Clusters Disabled: {}".format(skinClusterList))


def renableSkinCluster(skinCluster):
    """Renables a disabled skin cluster by rebinding it, only works in mel, Maya trick.

    Might be able to use resetInfluenceMatrices(skinCluster) instead

    :param skinCluster: A single skin cluster name
    :type skinCluster: str
    """
    selobjs = cmds.ls(selection=True, long=True)
    jointsBound = cmds.skinCluster(skinCluster, query=True, inf=True)
    geometryBound = cmds.skinCluster(skinCluster, query=True, g=True)
    cmds.select(jointsBound, geometryBound, replace=True)  # needs to select as only works in mel
    mel.eval('SmoothBindSkin')
    cmds.select(selobjs, replace=True)


def resetInfluenceMatrices(skinCluster):
    """Set bindPreMatrix the same as current worldInverseMatrix
    for each influence of given skinCluster

    Credit http://syntetik.blogspot.com/2010/10/bindprematrix-in-skincluster.html

    :param skinCluster: A single skin cluster name
    :type skinCluster: str
    """
    infs = cmds.listConnections("{}.matrix".format(skinCluster))
    for i, inf in enumerate(infs):
        m = cmds.getAttr("{}.worldInverseMatrix".format(inf))
        cmds.setAttr("{}.bindPreMatrix[{}]".format(skinCluster, str(i)), m[0], m[1], m[2], m[3], m[4], m[5], m[6], m[7],
                     m[8], m[9], m[10], m[11], m[12], m[13], m[14], m[15], type="matrix")


def renableSkinClusterList(skinClusterList, displayMessage=True, keepSelection=True):
    """Re enables a skin cluster list that have previously had their nodestate set to hasNoEffect (1)

    :param skinClusterList: List of the skin cluster node names
    :type skinClusterList: list
    :param displayMessage: Report the message inside of maya?
    :type displayMessage: bool
    :param keepSelection: Keep the selection?  Needed as te .mel eval requires selection
    :type keepSelection: bool
    """
    if keepSelection:
        selobjs = cmds.ls(selection=True, long=True)
    for skinClstr in skinClusterList:  # rebind all skin clusters
        jointsBound = cmds.skinCluster(skinClstr, query=True, inf=True)
        geometryBound = cmds.skinCluster(skinClstr, query=True, g=True)
        cmds.select(jointsBound, geometryBound,
                    replace=True)  # needs to select as need to run the mel eval, only works in mel
        mel.eval('SmoothBindSkin')
    if displayMessage:
        output.displayInfo("Skin Clusters Enabled: {}".format(skinClusterList))
    if keepSelection:
        cmds.select(selobjs, replace=True)


def toggleSkinCluster(skinCluster):
    """Toggles a single skin cluster node

    :param skinCluster: A single skin cluster name
    :type skinCluster: str
    """
    if cmds.getAttr(skinCluster + '.nodeState') == 1:  # re enable clusters
        renableSkinCluster(skinCluster)  # Renable
    else:
        disableSkinCluster(skinCluster)  # Disable


def toggleSkinClusterList(skinClusterList, displayMessage=True):
    """Toggles on/off a skin cluster list.  Toggles off the state of the first skin cluster.

    :param skinClusterList: A list of skinCluster names
    :type skinClusterList: list(str)
    :param displayMessage: Report the message to the user?
    :type displayMessage: bool
    """
    if cmds.getAttr(skinClusterList[0] + '.nodeState') == 1:  # re enable all clusters
        renableSkinClusterList(skinClusterList, displayMessage=displayMessage, keepSelection=True)
    else:  # disable all clusters
        disableSkinClusterList(skinClusterList, displayMessage=displayMessage)  # disable


def toggleSkinClusterListSelected(displayMessage=True):
    """Toggles on/off the selected skin clusters from a mesh selection.

    Toggles off the state of the first skin cluster.

    :param displayMessage: Report the message to the user?
    :type displayMessage: bool
    """
    objList = cmds.ls(selection=True, long=True)
    if not objList:
        if displayMessage:
            output.displayWarning("Please select skinned meshes or joints")
        return
    skinClusterList = getSkinClusterList(objList)

    if not skinClusterList:
        if displayMessage:
            output.displayWarning("No skinned clusters found. Please select skinned meshes")
        return
    toggleSkinClusterList(skinClusterList, displayMessage=displayMessage)


def toggleAllSkinClusters(displayMessage=True):
    """Toggles all skin clusters in a scene
    Handy for quick move pivots on joints
    Uses the `nodeState` attribute on the cluster

    1. Switching the nodestate to 1 (hasNoEffect) disables the skin cluster like a temp skin unbind without data loss
    2. Maya trick by selecting any joint and the mesh of the existing skin cluster and > `bind skin`
    3. Will return the cluster on skinning essentially skinning it at the current mesh/joint position
    """
    skinClusterList = getAllSkinClusters(displayMessage=False)
    if not skinClusterList:
        if displayMessage:
            output.displayWarning("No skinClusters Exist In The Scene")
        return
    if cmds.getAttr(skinClusterList[0] + '.nodeState') == 1:  # re enable clusters
        renableSkinClusterList(skinClusterList, displayMessage=displayMessage, keepSelection=True)
    else:
        disableSkinClusterList(skinClusterList, displayMessage=displayMessage)  # disable


"""
COPY/PASTE/TRANSFER SKINNING
"""


def copySkinWeightsSel(message=True):
    """Copies a skinned mesh and tracks it with a class singleton so it can be pasted later.

    :param message: Report a message to the user?
    :type message: bool
    :return: The skinned mesh as a transform node. If None found returns ""
    :rtype: str
    """
    selObjs = cmds.ls(selection=True)
    selObjs = selection.componentsToObjectList([selObjs[0]])  # Converts potential component to object
    firstObj = selObjs[0]
    if not selObjs:
        if message:
            output.displayWarning("No objects selected, please select a single mesh with a skin cluster to copy from.")
        return ""
    if not getSkinCluster(firstObj):
        if message:
            output.displayWarning("The object {} does not have a skin cluster.".format(firstObj))
        return ""
    skinInstance = ZooSkinTrackerSingleton()
    skinInstance.copiedSkinMesh = selObjs[0]
    if message:
        output.displayInfo("Success: Skinned mesh copied: {}".format(firstObj))
    return firstObj


def pasteSkinWeightsSel(message=True):
    """Pastes the skinning from the copied mesh (in singleton skinInstance.copiedSkinMesh) to selected geo.

    The new selection can be meshes or faces/verts/edges.

    :param message: Report messages to the user?
    :type message: bool
    :return: The pasted skin cluster names, or empty list if failed.
    :rtype: list(str)
    """
    # Copied Mesh -------------------------
    skinInstance = ZooSkinTrackerSingleton()
    copiedMesh = skinInstance.copiedSkinMesh
    if not copiedMesh:
        if message:
            output.displayWarning("There is no skin mesh to copy from in the clipboard")
        return list()
    if not cmds.objExists(copiedMesh):  # object exists
        if message:
            output.displayWarning("The mesh `{}` no longer exists in this scene please "
                                  "copy an existing mesh.".format(copiedMesh))
        return list()
    copiedSkinCluster = getSkinCluster(copiedMesh)
    if not copiedSkinCluster:
        if message:
            output.displayWarning("The copied mesh `{}` no longer has a skin cluster, "
                                  "this mesh must be skinned.".format(copiedMesh))
        return list()
    copiedInfluences = cmds.skinCluster(copiedSkinCluster, q=True, inf=True)

    # Pasted mesh/s -------------------------
    selObjsComponents = cmds.ls(selection=True)
    if not selObjsComponents:
        if message:
            output.displayWarning("Nothing is selected, please select a mesh or face/vert components to paste onto")
        return list()
    pastedSkinClusters = list()
    objList = selection.componentsToObjectList(selObjsComponents)  # could be components in the list
    objList = filterObjsForSkin(objList)[1]  # filters only mesh/surface/nurbs

    if not objList:
        if message:
            output.displayWarning("Selected objects must be either meshes/surfaces or nurbs curves.")
        return
    if copiedMesh in objList:
        objList = [value for value in objList if value != copiedMesh]  # remove original if still selected.
    influences = cmds.skinCluster(copiedSkinCluster, q=True, inf=True)  # in case needed
    for obj in objList:
        # get the skin cluster if there is one
        pastedSkinCluster = getSkinCluster(obj)
        if not pastedSkinCluster:
            pastedSkinCluster = cmds.skinCluster(obj, influences, toSelectedBones=True)[0]
        pastedSkinClusters.append(pastedSkinCluster)
        pastedInfluences = cmds.skinCluster(pastedSkinCluster, q=True, inf=True)
        # Be sure the joints of the copied cluster exist on the pasted skin cluster. If missing assign.
        missingJnts = list()
        for jointInfluence in copiedInfluences:
            if jointInfluence not in pastedInfluences:
                missingJnts.append(jointInfluence)
        if missingJnts:
            addJointsToSkinned(missingJnts, [pastedSkinCluster])

    if not pastedSkinClusters:
        if message:
            output.displayWarning("No skin clusters could be added to the selected meshes.".format(copiedMesh))

    # Checks passed so do the transfer using selection ----------------------
    rememberSel = cmds.ls(selection=True)
    cmds.select([copiedMesh] + selObjsComponents, replace=True)
    cmds.copySkinWeights(noMirror=True, surfaceAssociation='closestPoint', normalize=True)
    cmds.select(rememberSel, replace=True)
    if message:
        output.displayInfo("Success: Skin clusters pasted from `{}` to `{}`".format(copiedMesh, objList))
    return pastedSkinClusters


def transferSkinning(sourceMesh, targetMesh):
    """Transfers skin weights from the source mesh to the target,
    if the target already has a skin cluster will use the current

    :param sourceMesh: the mesh that already has the skin weights
    :type sourceMesh: str
    :param targetMesh: the mesh that will have the skin weights copied onto it
    :type targetMesh: str
    :return targetSkinCluster: the skinCluster created or transferred onto
    :rtype targetSkinCluster: str
    """
    sourceSkinCluster = getSkinCluster(sourceMesh)
    if not sourceSkinCluster:
        output.displayWarning("Cannot Transfer: No skin cluster found on `{}`".format(sourceMesh))
        return
    # if there isn't a skin cluster already, create one
    targetSkinCluster = getSkinCluster(targetMesh)
    if not targetSkinCluster:
        influences = cmds.skinCluster(sourceSkinCluster, q=True, inf=True)
        targetSkinCluster = cmds.skinCluster(targetMesh, influences, toSelectedBones=True)[0]
    cmds.copySkinWeights(sourceSkin=sourceSkinCluster,
                         destinationSkin=targetSkinCluster,
                         noMirror=True,
                         surfaceAssociation='closestPoint',
                         smooth=True)
    return targetSkinCluster


def transferSkinWeightsSelected():
    """Transfers skin weights from the first selected object to other objects
    iterates through a list so the transfer is from the first object selected to all other objects
    """
    objList = cmds.ls(selection=True, long=True)
    if not objList:
        output.displayWarning("Nothing Selected: Please select two meshes.")
        return
    if len(objList) == 1:
        output.displayWarning("Only one mesh selected. Please select multiple meshes.")
        return
    if not getSkinCluster(objList[0]):
        sourceMesh = namehandling.getUniqueShortName(objList[0])
        output.displayWarning("Cannot Transfer: No skin cluster found on `{}`".format(sourceMesh))
        return
    for obj in objList[1:]:
        transferSkinning(objList[0], obj)


"""
MIRROR SKINNING
"""


def mirrorSkinClusterList(skinClusterList, surfaceAssociation="closestPoint", influenceAssociation="closestJoint",
                          mirrorMode='YZ',
                          mirrorInverse=False):
    """Mirrors Skin Clusters

    :param surfaceAssociation: which surface style to mirror, "closestPoint", "rayCast", or "closestComponent"
    :type surfaceAssociation: str
    :param influenceAssociation: choose joint style to mirror "closestJoint", "closestBone", "label", "name", "oneToOne"
    :type influenceAssociation: str
    :param mirrorMode: which plane to mirror over, XY, YZ, or XZ
    :type mirrorMode: str
    :param mirrorInverse: Reverse the direction of the mirror. if true - to +
    :type mirrorInverse: bool
    """
    if len(skinClusterList) == 2:  # then try to mirror the skin cluster from source to destination
        cmds.copySkinWeights(sourceSkin=skinClusterList[0], destinationSkin=skinClusterList[1], mirrorMode=mirrorMode,
                             mirrorInverse=mirrorInverse, influenceAssociation=influenceAssociation,
                             surfaceAssociation=surfaceAssociation)
    else:
        for skinCluster in skinClusterList:
            cmds.copySkinWeights(sourceSkin=skinCluster, destinationSkin=skinCluster, mirrorMode=mirrorMode,
                                 mirrorInverse=mirrorInverse, influenceAssociation=influenceAssociation,
                                 surfaceAssociation=surfaceAssociation)


def mirrorSkinMeshList(objList, surfaceAssociation="closestPoint", influenceAssociation="closestJoint", mirrorMode='YZ',
                       mirrorInverse=False):
    """Mirrors Skin Weights from skin clusters connected to the objects in the objList

    :param objList: List of Maya Object Names
    :type objList: list
    :param surfaceAssociation: which surface style to mirror, "closestPoint", "rayCast", or "closestComponent"
    :type surfaceAssociation: str
    :param influenceAssociation: choose joint style to mirror "closestJoint", "closestBone", "label", "name", "oneToOne"
    :type influenceAssociation: str
    :param mirrorMode: which plane to mirror over, XY, YZ, or XZ
    :type mirrorMode: str
    :param mirrorInverse: Reverse the direction of the mirror. if true - to +
    :type mirrorInverse: bool
    :return skinClusterList: list of the skin clusters mirrored
    :rtype skinClusterList: list
    """
    skinClusterList = getSkinClusterList(objList)
    if not skinClusterList:
        return
    mirrorSkinClusterList(skinClusterList, surfaceAssociation=surfaceAssociation,
                          influenceAssociation=influenceAssociation,
                          mirrorMode=mirrorMode, mirrorInverse=mirrorInverse)
    return skinClusterList


def mirrorSkinSelection(surfaceAssociation="closestPoint", influenceAssociation="closestJoint", mirrorMode='YZ',
                        mirrorInverse=False):
    """Mirrors Skin Weights from skin clusters assigned to the current meshes or joints
    Selections as object transforms

    :param surfaceAssociation: which surface style to mirror, "closestPoint", "rayCast", or "closestComponent"
    :type surfaceAssociation: str
    :param influenceAssociation: choose joint style to mirror "closestJoint", "closestBone", "label", "name", "oneToOne"
    :type influenceAssociation: str
    :param mirrorMode: which plane to mirror over, XY, YZ, or XZ
    :type mirrorMode: str
    :param mirrorInverse: Reverse the direction of the mirror. if true - to +
    :type mirrorInverse: bool
    """
    objList = cmds.ls(selection=True, long=True)
    skinClusterList = mirrorSkinMeshList(objList, surfaceAssociation=surfaceAssociation,
                                         influenceAssociation=influenceAssociation, mirrorMode=mirrorMode,
                                         mirrorInverse=mirrorInverse)
    if not skinClusterList:
        output.displayWarning("No skin clusters found on selected")
        return
    skinClusterNames = ", ".join(skinClusterList)
    output.displayInfo("Skin Clusters Mirrored: '{}'".format(skinClusterNames))


# -----------------
# TRACK SKIN CLUSTERS
# -----------------


@six.add_metaclass(classtypes.Singleton)
class ZooSkinTrackerSingleton(object):
    """Keeps track of copied skin data.
    """

    def __init__(self):
        self.copiedSkinMesh = ""
