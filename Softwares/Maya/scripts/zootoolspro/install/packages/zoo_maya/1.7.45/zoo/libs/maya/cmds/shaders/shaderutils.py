"""

from zoo.libs.maya.cmds.shaders import shaderutils
shaderutils.getAllShaders()

from zoo.libs.maya.cmds.shaders import shaderutils
shaderutils.assignShader(objFaceList, shader)

"""

import os
import uuid

import maya.mel as mel
import maya.api.OpenMaya as om2
from maya import cmds
from zoo.libs.maya import zapi
from zoo.libs.maya.utils.files import mayaFileType

from zoo.libs.maya.cmds.shaders import createshadernetwork
from zoo.libs.maya.cmds.objutils import namewildcards, namehandling, filtertypes, selection
from zoo.libs.maya.cmds.renderer.rendererconstants import RENDERER_SUFFIX_DICT, DEFAULT_MAYA_SHADER_TYPES
from zoo.libs.maya.utils import scene, general
from zoo.libs.pyqt.widgets import elements
from zoo.libs.utils import output, path as zpath
from zoo.core.util import zlogging, strutils

from zoo.core.util import classtypes
from zoovendor import six

logger = zlogging.getLogger(__name__)

SGKEY = "ShadingGroup"
ASSIGNKEY = "assigned"


def importAndAssignShader(filePath, shaderName="", mayaFileType="mayaAscii"):
    """Imports a maya file and finds the first shader of the current renderer and assigns it to the current selection

    :param shaderName: It will attempt to import shader with the matching name.
    :param filePath: The file path of the maya file to be imported
    :type filePath: str
    :param mayaFileType: The file type of the maya file "mayaAscii" or "mayaBinary"
    :type mayaFileType: str

    :return newNodes: A list of new nodes imported as string names
    :rtype newNodes: list(str)
    :return firstShader: The name of the first shader imported
    :rtype firstShader: str
    """

    ias = ImportAssignShader(filePath, shaderName, mayaFileType)
    return ias.doIt()


class ImportAssignShader(object):

    def __init__(self, filePath, shaderName="", mayaFileType="ma"):
        """ Import and assign shader class. Should be

        :param filePath:
        :param shaderName:
        :param mayaFileType:
        """
        self._filePath = filePath
        self._shaderName = shaderName
        self._selObjs = None

        if mayaFileType.lower() == "ma":
            self.mayaFileType = "mayaAscii"
        elif mayaFileType.lower() == "mb":
            self.mayaFileType = "mayaBinary"
        else:
            self.mayaFileType = mayaFileType
        self.namespace = general.generateUniqueNamespace("ZS")

    def doIt(self):
        """ Run the import and assign shader code

        :return:
        """
        try:
            return self._doIt()
        finally:
            try:
                # safely handle namespace removal, just use om2 as we care not for undo
                om2.MNamespace.removeNamespace(self.namespace, removeContents=False)
            except RuntimeError:
                # RuntimeError happens when the namespace doesn't exist anymore. Small edge case here.
                pass

    def _doIt(self):
        self._selObjs = cmds.ls(selection=True, long=True)
        self._newNodes = cmds.file(self._filePath, options="v=0;", ignoreVersion=1, type=self.mayaFileType, i=1,
                                   ns=self.namespace, returnNewNodes=True, resetError=True)
        if not self._newNodes:
            output.displayWarning("Nothing was imported: {}".format(self._filePath))
            self.cleanImports()
            self.reselectObjects()
            return [], ""

        # First get the shader from the imported nodes
        shaders = cmds.ls(self._newNodes, mat=True)
        firstShader = None
        if shaders:
            if self._shaderName:  # Find matching shader name
                for s in shaders:
                    if self._shaderName == self.stripNamespace(s):
                        firstShader = s
                        break
                if not firstShader:
                    firstShader = shaders[0]
            else:  # Otherwise just use the first one
                firstShader = shaders[0]
        else:
            output.displayWarning("A shader was not found in the imported file: {}".format(self._filePath))
            self.cleanImports()
            self.reselectObjects()
            return [], ""

        # A shader was found so assign it to the selection
        if shaders and self._selObjs:
            newShader = self.stripNamespace(firstShader)
            existingShader = None
            option = "ASSIGN_NEW"
            if shaderExists(newShader):
                existingShader = newShader

                option = self.duplicateChoicePopup(newShader)

            if option == "":
                self.cleanImports()
                output.displayInfo("Cancelled")
                self.reselectObjects()
                return [], ""

            elif option == "ASSIGN_EXISTING":
                self._assignExisting(existingShader)
                return self._newNodes, existingShader

            elif option == "ASSIGN_NEW":
                newName = namehandling.generateUniqueName(newShader)
                self._assignNew(newShader, firstShader)
                return self._newNodes, newName

            elif option == "REPLACE":
                # Delete and replace old shader with new
                self._replaceShader(existingShader, firstShader, newShader)
                return self._newNodes, newShader
        elif shaders:
            newShader = self.stripNamespace(firstShader)
            self.cleanNamespaces()
            return self._newNodes, newShader

        self.cleanImports()
        return [], ""

    def _replaceShader(self, existingShader, firstShader, newShader):
        replaceShader(existingShader, firstShader)
        cmds.delete(existingShader)

        renameShader(firstShader, newShader)
        assignShader(self._selObjs, newShader)
        self.cleanNamespaces()
        self.reselectObjects()

    def stripNamespace(self, shader):
        return shader.split(":")[1]

    def duplicateChoicePopup(self, newShader):
        """ Choose one of the options

        :param newShader:
        :return:
        """
        ret = elements.MessageBox.showMultiChoice(title="Existing shader found",
                                                  message="Shader with the same name \'{}\' found. What would you like to do?".format(
                                                      newShader),
                                                  showDiscard=False,
                                                  choices=["Use existing shader, don't change shader settings.",
                                                           "Create New Shader and Apply.",
                                                           "Override Shader.",
                                                           ], buttonB="Cancel")
        ops = {0: "ASSIGN_EXISTING",
               1: "ASSIGN_NEW",
               2: "REPLACE",

               -1: ""}
        option = ops[ret[0]]
        return option

    def cleanNamespaces(self):
        cleanNamespaces(self._newNodes)

    def _assignNew(self, newShader, firstShader):
        """ Create a new shader

        :param newShader:
        :param firstShader:
        :return:
        """
        newName = namehandling.generateUniqueName(newShader)
        namehandling.safeRename(firstShader, newName)
        self.reselectObjects()
        assignShader(self._selObjs, newName)
        output.displayInfo("Shader/s imported: {}".format(newName))
        self.cleanNamespaces()

    def _assignExisting(self, existingShader):
        """ Assign existing shader to selected objects

        :param existingShader:
        :return:
        """
        self.cleanImports()
        assignShader(self._selObjs, existingShader)  # new shader should be the same name as the old shader
        self.reselectObjects()
        output.displayInfo("Assigning existing shader '{}'".format(existingShader))

    def reselectObjects(self):
        """ Reselect original objects

        :return:
        """
        cmds.select(self._selObjs, replace=True)

    def cleanImports(self):
        """ Delete any of the imported data in the scene

        :return:
        """
        try:
            cmds.delete("{}*:*".format(self.namespace))
        except ValueError as e:
            if str(e) == "No object matches name: {}*:*".format(self.namespace):
                pass
            else:
                raise ValueError(e)


def getShaderFromSG(shadingGroup):
    """Returns the main shader from a shading group, this assumes only one shader is related to the shadering group
    This will have to ignore extra shaders deeper in the node network if there are many nested/layered shaders

    :param shadingGroup: The name of the shading group
    :type shadingGroup: str
    :return shader: the shader name
    :rtype shader: str
    """
    connections = cmds.listConnections(shadingGroup, source=True, destination=False)
    shaders = cmds.ls(connections, materials=True)
    if shaders:
        return shaders[0]
    return ""


def getShadersFromSGList(shadingGroupSet):
    """Returns a list of shaders from a set of shading groups

    :param shadingGroupSet: set of shading group names
    :type shadingGroupSet: set
    :return shaderList:
    :rtype shaderList:
    """
    shaderList = list()
    for shadingGroup in shadingGroupSet:
        shader = getShaderFromSG(shadingGroup)
        if not shader:
            continue
        shaderList.append(getShaderFromSG(shadingGroup))
    return shaderList


def getShadingGroupFromShader(shader):
    """Returns the Shading Group from a shader

    :param shader: the shader name
    :type shader: string
    :return shadingGroup: the shading group node (can easily be None if not assigned)
    :rtype shadingGroup: str
    """
    connectedNodes = cmds.listConnections(shader, source=False, destination=True)
    for node in connectedNodes:
        if cmds.ls(node, type="shadingEngine"):
            if node == "initialParticleSE":  # hardcoded for lambert1 which has two shading groups, ignore particlesSG
                return "initialShadingGroup"
            return node
    return ""


def getShadingGroupFromShaderList(shaderList):
    shadingGroupList = list()
    for shader in shaderList:
        shadingGroupList.append(getShadingGroupFromShader(shader))
    return shadingGroupList


def getShadingGroupsFromObj(mayaObj):
    """Returns all the Shading Groups related to a mesh or nurbsSurface object

    :param mayaObj: A transform or shape node that is or has a "mesh" or "nurbsSurface" node
    :type mayaObj: str
    :return shadingGroupList: list of shading group names
    :rtype shadingGroupList: list
    """
    # if mesh transform or shape ------------------------------
    meshList = filtertypes.filterTypeReturnTransforms([mayaObj], shapeType="mesh")
    if meshList or cmds.objectType(mayaObj) == "mesh":
        # must search on faces, shape nodes is not enough
        faces = cmds.polyListComponentConversion(mayaObj, tf=True)
        if not faces:
            return None
        return cmds.listSets(object=faces[0], type=1)
    # if nurbsSurface transform or shape ------------------------------
    nurbsSurfaceList = filtertypes.filterTypeReturnTransforms([mayaObj], shapeType="nurbsSurface")
    if nurbsSurfaceList or cmds.objectType(mayaObj) == "nurbsSurface":
        if cmds.objectType(mayaObj) == "transform":  # get it's nurbs shape node
            nurbsShape = cmds.listRelatives(mayaObj, shapes=True, fullPath=True, type="nurbsSurface")[0]
        else:
            nurbsShape = mayaObj
        return cmds.listSets(object=nurbsShape, type=1)  # returns the shading group as a list


def getShadingGroupsObjList(nodeList):
    """Returns all the Shading Groups related to an object list

    .. note::
        Only supports geometry, does not support selected shaders etc

    see function getShadingGroupsFromNodes() for all nodes

    :param nodeList: list of Maya Object names
    :type nodeList: list
    :return shadingGroupList: list of shading group names
    :rtype shadingGroupList: list
    """
    shadingGroupList = list()
    for node in nodeList:
        newShadingGroupList = getShadingGroupsFromObj(node)
        if newShadingGroupList:
            shadingGroupList += newShadingGroupList

    list(set(shadingGroupList))  # make unique list
    return shadingGroupList


def getShadersObjList(objList):
    """Gets a list of shader names related to a object list

    .. note::
        Only supports geometry, does not support selected shaders etc

    see function getShadersFromNodes() for all nodes

    Used for matte assignments only

    :param objList: List of Maya Objects as strings
    :type objList: list
    :return:
    :rtype: list
    """
    shadingGroupList = getShadingGroupsObjList(objList)
    return getShadersFromSGList(shadingGroupList)


def getShadersSelected(reportMessage=True):
    """From selection return all related shaders as a list
    This includes shape nodes, transforms, shaders (will return themselves) and shadingGroups

    :param reportMessage: report the message back to the user?
    :type reportMessage: bool
    :return shaderList: A list of shader names
    :rtype shaderList: list
    """
    nodeList = cmds.ls(selection=True, long=True)
    if not nodeList:
        if reportMessage:
            om2.MGlobal.displayWarning('Please select an object, shader or shading group')
        return
    shaders = getShadersFromNodes(nodeList)
    if not shaders:
        if reportMessage:
            om2.MGlobal.displayWarning('No shaders found in the current selection')
        return
    return shaders  # remove duplicates


def getShaderWildcard(wildcardName):
    """Finds all shaders in a scene with the given suffix

    :param wildcardName: The suffix name
    :type wildcardName: str
    :return shaderList: the shaders
    :rtype shaderList: list
    """
    shaderList = namewildcards.getWildcardObjs(wildcardName)  # find all nodes with suffix
    return cmds.ls(shaderList, materials=True)  # check legitimate shaders filtering out other nodes


def getShadersShadeNode(shapeNode):
    """Get the related shaders connected to the given shapeNode

    :param shapeNode: name of the shape node
    :type shapeNode: str
    :return shaderList: the shader names
    :rtype shaderList: list
    """
    if not shapeNode:
        return list()
    shadingGrps = cmds.listConnections(shapeNode, type='shadingEngine')
    if not shadingGrps:
        return list()
    shaderList = cmds.ls(cmds.listConnections(shadingGrps), materials=1)
    return shaderList


def getShadersShapeNodeList(shapeNodeList):
    """Returns the shaders attached to a list of shape nodes

    :param shapeNodeList: list of shape node names
    :type shapeNodeList: str
    :return shaderList: the shader names
    :rtype shaderList: list
    """
    shaderList = list()
    for shapeNode in shapeNodeList:
        shaderList += getShadersShadeNode(shapeNode)
    return shaderList


def shaderAndAssignmentsFromObj(objTransform, message=True):
    """Returns a shader list and a selection list from the selected mesh object, can included face selection.

    Assumes the transform only has one mesh shape node.
    Used in transferShaderTopology()

    Example 1 return::

        ["redShadingGroup"]
        [["|pSphere3"]]

    Example 2 return::

        ["redShadingGroup", "blueShadingGroup]
        [["|pSphere3.f[0:47]", "|pSphere3.f[101:222]"], ["|pSphere3.f[48:100]", "|pSphere3.f[223:228]"]]

    :param objTransform: Maya transform node name should have a mesh shape nodes as children (ie a mesh object)
    :type objTransform: str
    :param message: Return messages to the user om2.MGlobal
    :type message: bool
    :return shadingGroupList: List of shading groups assigned to the object, can be multiple if face assigned
    :rtype shadingGroupList: list(str)
    :return objectsFacesList: List of shader assignments to this object, can be face assigned, see function description
    :rtype objectsFacesList: list(list(str))
    """
    objTransformDot = "{}.".format(objTransform)  # add a fullstop for use later
    objTransformShape = cmds.listRelatives(shapes=True, fullPath=True, type="mesh")  # get shape for use later
    if not objTransformShape:
        if message:
            om2.MGlobal.displayWarning('The object `{}` does not have a mesh shape node'.format(objTransform))
        return
    objTransformShape = objTransformShape[0]  # the shape node
    objectsFacesList = list()
    shadingGroupList = getShadingGroupsFromObj(objTransform)
    if not shadingGroupList:
        if message:
            om2.MGlobal.displayWarning('The object `{}` does not have any shading groups assigned'.format(objTransform))
        return
    for i, shadingGroup in enumerate(shadingGroupList):
        assignList = getObjectsFacesAssignedToSG(shadingGroup, longName=True)  # will return all objs face in scene
        objAssignment = list()
        for assignment in assignList:  # restrict the objs and faces to the objTransform
            # if the assignment contains the name of the target object then keep it, lose all others
            if objTransformDot in assignment:  # if face assignment will match to name with fullstop "|pCube."
                objAssignment.append(assignment)
            elif objTransformShape == assignment:  # if not face assign assignment then will match to shape node name
                objAssignment.append(assignment)
                break  # if this has been triggered, no face assignments, only one will be in the list
        objectsFacesList.append(objAssignment)
    return shadingGroupList, objectsFacesList


def transferShaderTopology(sourceObject, targetObject, ignoreTopologyMismatch=True, message=True):
    """Transfers shader/s from one object to another with matching topology, handles face assignment

    Copies the shaders from the source object and copies them onto the target object

    Objects must be transforms and can have "mesh" or "nurbsSurface" shapes

    .. todo:: Nurbs does not support multiple shaders yet

    :param sourceObject: The source object name to copy the shader info from, should be a long name
    :type sourceObject: str
    :param targetObject: The target object name to copy the shader info onto, should be a long name
    :type targetObject: str
    :param ignoreTopologyMismatch: Ignores the topology difference and copies the first shader found
    :type ignoreTopologyMismatch: bool
    :param message: Return messages to the user om2.MGlobal
    :type message: bool
    :return: True if the transfer succeeded via matching topology False if not
    :rtype: bool
    """
    # Mesh --------------------------------------------------
    meshObjs = filtertypes.filterTypeReturnTransforms([sourceObject, targetObject], shapeType="mesh")
    if len(meshObjs) == 2:
        if cmds.polyCompare(sourceObject, targetObject, faceDesc=True):  # returns 0 if the faces are a topology match
            if message:
                om2.MGlobal.displayWarning('The topology of both objects does not match')
                # topology has probably changed so assign the first shader found from the skinned mesh
            if ignoreTopologyMismatch:  # assign the first shader found
                shadingGroups = getShadingGroupsFromObj(sourceObject)
                if shadingGroups:
                    assignShadingGroup([targetObject], shadingGroups[0])
                if message:
                    om2.MGlobal.displayInfo("The topology has probably changed between the skinned and orig. "
                                            "Transferring first shader found")
            return False
        # is a match so continue
        shadingGroupList, objectsFacesList = shaderAndAssignmentsFromObj(sourceObject)
        if len(shadingGroupList) == 1:  # maya weirdness, if no face assign replace the shape node names not transform
            sourceObject = cmds.listRelatives(sourceObject, shapes=True, fullPath=True, type="mesh")[0]
        for i, assignmentList in enumerate(objectsFacesList):
            for x, assignment in enumerate(assignmentList):
                objectsFacesList[i][x] = assignment.replace(sourceObject, targetObject)  # swap the assignment to target
        for i, shadingGroup in enumerate(shadingGroupList):  # do the shader assign
            assignShadingGroup(objectsFacesList[i], shadingGroup)
        return True
    # NurbsSurface --------------------------------------------------
    nurbsObjs = filtertypes.filterTypeReturnTransforms([sourceObject, targetObject], shapeType="nurbsSurface")
    if len(nurbsObjs) == 2:
        # TODO currently only supports one shader assignment
        shadingGroup = getShadingGroupsFromObj(sourceObject)[0]  # only one shader on nurbsSurfaces
        for targetObj in nurbsObjs:  # do the transfer
            nurbsShapeList = cmds.listRelatives(targetObj, shapes=True, fullPath=True, type="nurbsSurface")
            assignShadingGroup(nurbsShapeList, shadingGroup)
        return True
    # Other ------------------------------------------------------------------
    if message:
        om2.MGlobal.displayWarning('The objects are not both "nurbsSurfaces" or both "polygon meshes"')
    return False


def transferShaderTopologySelected(message=True):
    """Transfers shader/s from one object to another with matching topology, handles face assignment

    The first object in the selection's shader/s are copied to all other selected objects

    Objects must be transforms and can have "mesh" or "nurbsSurface" shapes
    TODO: Nurbs does not support multiple shaders yet

    :param message: Return messages to the user om2.MGlobal
    :type message: bool
    """
    selObjs = cmds.ls(selection=True, long=True, type="transform")
    if len(selObjs) < 2:
        if message:
            om2.MGlobal.displayWarning("Please select two or more mesh, or nurbsSurface objects.")
    sourceObj = selObjs.pop(0)  # the source obj is the first selected object and remove from selObj list
    for targetObj in selObjs:  # do the transfer
        transferShaderTopology(sourceObj, targetObj, message=message)


def getAllShadersAndObjectFaceAssigns(filterOnlyUsed=False, filterShaderType=None):
    """Gets all shaders, shading groups and their face assignments in the scene
    if filterOnlyUsed then return only those with scene assignments, ie not unused shaders

    :param filterOnlyUsed: only return used shaders, shaders that contain assignments, obj or face etc
    :type filterOnlyUsed: bool
    :return shaderList: list of shader names
    :rtype shaderList: list
    :return shadingGroupList: list of shading group names
    :rtype shadingGroupList: list
    :return: list of face/obj assignements
    :rtype: list
    """
    shadersAllList = getAllShaders()
    shaderAssignmentDict = dict()
    deleteShaderList = list()
    for shader in shadersAllList:
        shaderAssignmentDict[shader] = dict()
        if shader == "particleCloud1":  # ignore the primary particleCloud1
            shaderAssignmentDict[shader][SGKEY] = "initialParticleSE"
            shaderAssignmentDict[shader][ASSIGNKEY] = getObjectsFacesAssignedToSG("initialParticleSE")
            continue
        shadingGroup = getShadingGroupFromShader(shader)
        shaderAssignmentDict[shader][SGKEY] = shadingGroup
        shaderAssignmentDict[shader][ASSIGNKEY] = getObjectsFacesAssignedToSG(shadingGroup)
    if filterOnlyUsed:
        for shaderName in shaderAssignmentDict:
            if shaderAssignmentDict[shaderName][ASSIGNKEY] is None:  # record index to remove
                deleteShaderList.append(shaderName)  # shader to delete from dict
    if filterShaderType:
        for shaderName in shaderAssignmentDict:
            nodeType = cmds.objectType(shaderName)
            if filterShaderType != nodeType:
                deleteShaderList.append(shaderName)  # shader to delete from
    deleteShaderList = list(set(deleteShaderList))  # no duplicates
    for shader in deleteShaderList:
        shaderAssignmentDict.pop(shader, None)
    return shaderAssignmentDict


def getAllShaders():
    """return all shaders types that could be created in a scene

    :return: list of shader names
    :rtype: list
    """
    return cmds.ls(materials=True)


def getObjectsFacesAssignedToSG(shadingGroup, longName=True):
    """gets objects and faces of the given shading group

    :param shadingGroup: the shading group name
    :type shadingGroup: str
    :param longName: return all longnames, will return only clashing nodes as long if false
    :type longName: str
    :return: list of objects and faces as names with [1:233]
    :rtype: list
    """
    objectFaceList = cmds.sets(shadingGroup, query=True)
    if longName and objectFaceList:
        objectFaceList = namehandling.getLongNameList(objectFaceList)
    return objectFaceList


def getObjectsFacesAssignedToShader(shader, longName=True):
    """gets objects and faces of the given shader

    :param shader: the shader name
    :type shader: str
    :return: list of objects and faces as names with [1:233]
    :rtype: list
    """
    shadingGroup = getShadingGroupFromShader(shader)
    if not shadingGroup:
        return None
    objectFaceList = getObjectsFacesAssignedToSG(shadingGroup, longName=longName)
    return objectFaceList


def assignShadingGroup(objFaceList, shadingGroup):
    """Assigns the shader to an object/face list

    :param objFaceList: list of objects and faces for the assignment
    :type objFaceList: list
    :param shadingGroup: the shading group name to assign
    :type shadingGroup: str
    :return: the shading group name assigned
    :rtype: str
    """
    for objFace in objFaceList:
        cmds.sets(objFace, e=True, forceElement=shadingGroup)
    return shadingGroup


def assignShader(objFaceList, shader):
    """Assigns the shader to an object/face list

    :param objFaceList: list of objects and faces for the assignment
    :type objFaceList: list
    :param shader: the shader name to assign
    :type shader: str
    :return: the shading group name assigned
    :rtype: str
    """
    shadingGroup = getShadingGroupFromShader(shader)
    if not shadingGroup:  # create one
        shadingGroup = createshadernetwork.createSGOnShader(shader)
    return assignShadingGroup(objFaceList, shadingGroup)


def assignShaderCheck(objFaceList, shader):
    """Assigns the shader to an object/face list, checks to see if the object exists before assigning

    :param objFaceList: list of objects and faces for the assignment
    :type objFaceList: list
    :param shader: the shader name to assign
    :type shader: str
    """
    shadingGroup = getShadingGroupFromShader(shader)
    if not shadingGroup:  # create one
        shadingGroup = createshadernetwork.createSGOnShader(shader)
    for objFace in objFaceList:  # gets the shader assignment list
        if ".f" in objFace:  # could be a face selection so split to get object
            object = objFace.split(".f")[0]
        else:
            object = objFace
        if cmds.objExists(object):  # assign the shader
            cmds.sets(objFace, e=True, forceElement=shadingGroup)


def assignShaderSelected(shader):
    """Assigns the given shader to current selection

    :param shader: The shader name
    :type shader: str
    """
    cmds.hyperShade(assign=shader)


def getShadingGroupsFromNodes(nodeList):
    """Finds shaders assigned to current node list,
    Includes shape nodes, transforms, shaders and shadingGroups (will return themselves)

    :param nodeList: list of maya node names, can be any nodes
    :type nodeList: list
    :return shadingGroupList: List of shading group names associated with the given nodes
    :rtype shadingGroupList: list
    """
    shadingGroupList = list()
    meshShadingGroups = list()
    # check if nodes are shading groups themselves
    for node in nodeList:
        if "." not in node:  # could be a component, if "." then skip
            if cmds.objectType(node) == "shadingEngine":
                shadingGroupList.append(node)
    # check shaders and shapes for connecting Shading Groups and add to main list
    shadingGroupShaderList = cmds.listConnections(nodeList, type='shadingEngine')
    if shadingGroupShaderList:
        shadingGroupList = list(set(shadingGroupList + shadingGroupShaderList))
    # check for shaders on shape or transform nodes, this also checks faces too, add to main list
    for node in nodeList:
        shaderList = getShadingGroupsFromObj(node)
        if shaderList:
            meshShadingGroups += shaderList
    if meshShadingGroups:
        shadingGroupList = list(set(shadingGroupList + meshShadingGroups))
    return shadingGroupList


def getShadingGroupsFromSelectedNodes():
    """finds shaders assigned to current selection of nodes
    This includes shape nodes, transforms, shaders and shadingGroups (will return themselves)

    :return shadingGroupList: List of shading group names associated with the given nodes
    :rtype shadingGroupList: list
    """
    selObj = cmds.ls(selection=True, long=True)
    return getShadingGroupsFromNodes(selObj)


def getShadersFromNodes(nodeList):
    """Will return a shader list from given nodes,
    This includes shape nodes, transforms, shaders (will return themselves) and shadingGroups

    :param nodeList: list of maya node names, can be any nodes
    :type nodeList: list
    :return shaderList: List of Shader Names associated with the nodeList
    :rtype shaderList: list
    """
    shadingGroupList = getShadingGroupsFromNodes(nodeList)
    shaderList = getShadersFromSGList(set(shadingGroupList))
    return shaderList


def getShadersFromSelectedNodes(allDescendents=False, reportSelError=False):
    """Will return a shader list from given selection of nodes,
    This includes shape nodes, transforms, shaders (will return themselves) and shadingGroups
    Also can retrieve shaders on all descendents of the selected objects

    :param allDescendents: will include allDescendants of the selection, children and grandchildren etc
    :type allDescendents: bool
    :param reportSelError: Report selection issues to the user
    :type reportSelError: bool
    :return shaderList: List of Shader Names associated with the selected nodeList
    :rtype shaderList: list
    """
    allChildren = list()
    shaderRetrieveObjs = cmds.ls(selection=True, long=True)
    if not shaderRetrieveObjs:
        if reportSelError:
            om2.MGlobal.displayWarning('Nothing Selected Please Select Node/s')
        return
    if allDescendents:
        for obj in shaderRetrieveObjs:
            allChildren += cmds.listRelatives(obj, allDescendents=True, shapes=False, fullPath=True)
        shaderRetrieveObjs = list(set(shaderRetrieveObjs + allChildren))
    shaderList = getShadersFromNodes(shaderRetrieveObjs)
    return shaderList


def selectMeshFaceFromShaderName(shaderName):
    """Selects objects and faces assigned from a shader

    :param shaderName: The name of a Maya shader
    :type shaderName: str
    """
    if not cmds.objExists(shaderName):
        return
    cmds.select(shaderName)
    cmds.hyperShade(shaderName, objects="")  # Select function


def selectMeshFaceFromShaderNames(shaderNames):
    """Selects objects and faces assigned to multiple shaders

    :param shaderNames: A list of Maya shader names
    :type shaderNames: list(str)
    """
    cmds.select(clear=True)
    for shader in shaderNames:
        originalSel = cmds.ls(selection=True)
        selectMeshFaceFromShaderName(shader)
        cmds.select(originalSel, add=True)  # so add back the previous selection
    return cmds.ls(selection=True)


def selectMeshFaceFromShaderSelection(message=True):
    """Selects objects and faces assigned to multiple shaders found in either mesh face or shader selection.

    :param message: report a message to the user?
    :type message: bool
    """
    shaderNames = getShadersSelected()
    if not shaderNames:
        output.displayWarning("No shaders were found from the selected objects.")
        return
    meshesFaces = selectMeshFaceFromShaderNames(shaderNames)
    if message:
        output.displayInfo("Meshes selected from shader/s `{}`".format(shaderNames))
    return meshesFaces


def getMeshFaceFromShaderNodes(nodeList, selectMesh=True, objectsOnly=False):
    """Will return a mesh shape node list from given nodeList,
    This includes shape nodes, transforms, shaders (will return themselves) and shadingGroups

    :param nodeList: list of maya node names, can be any nodes
    :type nodeList: list
    :param selectMesh: Select the returned meshes and potential faces?
    :type selectMesh: bool
    :param objectsOnly: Only return (and potentially select) meshes, not faces
    :type objectsOnly: bool
    :return meshList: List of mesh node names, can be transforms (needs fixing possibly to be only shapes)
    :rtype meshList: list
    """
    if not selectMesh:
        selObj = cmds.ls(selection=True, long=True)
    # get all related shaders from node selection
    shaderList = getShadersFromNodes(nodeList)
    objFaceList = list()
    if shaderList:
        for shader in shaderList:
            cmds.select(shader, replace=True)
            cmds.hyperShade(shader, objects="")
            objFaceList += cmds.ls(selection=True, long=True)
    om2.MGlobal.displayInfo('selected: '.format(objFaceList))
    if objectsOnly:  # return only shape nodes and not potential face selection
        for i, objFace in enumerate(objFaceList):
            if ".f[" in objFace:  # save only the object names not face list
                objFaceList[i] = objFace.split('.f[')[0]
    objFaceList = list(set(objFaceList))  # make unique list
    if not selectMesh:
        cmds.select(selObj, replace=True)
    else:
        cmds.select(objFaceList, replace=True)
    return objFaceList


def getMeshFaceFromShaderSelection(selectMesh=True, objectsOnly=False):
    """Will return a mesh (shape) node list from given selection of nodes,
    This includes shape nodes, transforms, shaders (will return themselves) and shadingGroups

    :param selectMesh: Select the returned meshes and potential faces?
    :type selectMesh: bool
    :param objectsOnly: Only return and potentially select meshes, not faces
    :type objectsOnly: bool
    :return meshFaceList: List of mesh node names, and potentially face names, not transforms
    :rtype meshFaceList: list
    """
    selObj = cmds.ls(selection=True, long=True)
    if not selObj:
        om2.MGlobal.displayWarning('Nothing Selected Please Select Node/s')
        return
    objFaceList = getMeshFaceFromShaderNodes(selObj, selectMesh=selectMesh, objectsOnly=objectsOnly)
    return objFaceList


def transferAssign(objFaceList):
    """from a list take the first objects shader (it can be a shader or shading group too) and assign it to the
    remaining list objects

    :param objFaceList: list of maya objects and or face selection
    :type objFaceList: list
    """
    # get first selection, and remove it from the list
    fromObj = objFaceList[0]
    del objFaceList[0]
    fromObjList = [fromObj]
    fromShader = (getShadersFromNodes(fromObjList))[0]  # get fromShader, this is the first shader it finds
    assignShader(objFaceList, fromShader)  # assign shader to remaining selection
    return fromShader


def transferAssignSelection(message=True):
    """from a selection take the first object's shader (it can be a shader or shading group itself too) and assign it
    to the remaining list objects, this is like copy shader from an object to objects

    :param message: report warnings to the user
    :type message: bool
    """
    selObjs = cmds.ls(selection=True, long=True)
    if not selObjs:
        return False
    geoFaceList = selection.convertGeometryFaces(selObjs, individualFaces=True)
    if len(geoFaceList) < 2:
        om2.MGlobal.displayWarning("Transfer requires at least two geometry or polygon faces selected")
        return False
    fromShader = transferAssign(geoFaceList)
    if message:
        output.displayInfo("Shader assigned `{}`".format(fromShader))
    return True


def removeShaderSuffix(shaderName):
    """Removes the shader suffix from a shader name, will remove all shader suffix names for any renderer

    Will remove suffix for all renderers

    :param shaderName: the Maya shader name
    :type shaderName: str
    :return shaderName:  the Maya shader name now with suffix removed
    :rtype shaderName: str
    """
    suffix = shaderName.split('_')[-1]
    for key in RENDERER_SUFFIX_DICT:
        if RENDERER_SUFFIX_DICT[key] == suffix:
            shaderName = shaderName.replace("_{}".format(suffix), "")
    return shaderName


def removeShaderSuffixRenderer(shaderName, renderer):
    """Removes the shader suffix from a shader name, will remove all shader suffix names for any renderer

    Will remove on for the given renderer.

    :param shaderName: A Maya shader name
    :type shaderName: str
    :return shaderName:  the Maya shader name now with suffix removed
    :rtype shaderName: str
    """
    suffix = shaderName.split('_')[-1]
    if RENDERER_SUFFIX_DICT[renderer] == suffix:
        shaderName = shaderName.replace("_{}".format(suffix), "")
    return shaderName


def removeShaderSuffixList(shaderNameList, renderer):
    """

    :param shaderNameList: List of shader names
    :type shaderNameList: list(str)
    :param renderer: A renderer nicename
    :type renderer: str
    :return shaderRenamedList: Shader list now renamed
    :rtype shaderRenamedList:
    """
    shaderRenamedList = list()
    for shader in shaderNameList:
        shaderRenamedList.append(removeShaderSuffix(shader, renderer))
    return shaderRenamedList


def getShaderNameFromNode(node, removeSuffix=False):
    """from the given node return the shader name that's attached to it
    can remove the suffix if it's in the dict rendererManage.ALLRENDERERSUFFIX

    :param node: any maya node, should be shader related but is ok if not, will just fail to find a shader
    :type node: str
    :param removeSuffix: removes the suffix name if it's in the rendererManage.ALLRENDERERSUFFIX dict
    :type removeSuffix: bool
    :return shaderName: the shader name
    :rtype shaderName: str
    """
    shaderName = getShadersFromNodes([node])
    if not shaderName:
        if cmds.nodeType(node) not in DEFAULT_MAYA_SHADER_TYPES:
            return ""
        shaderName = node
    else:
        shaderName = shaderName[0]
    if removeSuffix:
        shaderName = removeShaderSuffix(shaderName)
    return shaderName


def getShaderNameFromNodeSelected(removeSuffix=False):
    """from the first selected object return the shader name that's attached to it
    can remove the suffix if it's in the dict rendererManage.ALLRENDERERSUFFIX

    :param removeSuffix: removes the suffix name if it's in the rendererManage.ALLRENDERERSUFFIX dict
    :type removeSuffix: bool
    :return shaderName: the shader name
    :rtype shaderName: str
    """
    selbObj = cmds.ls(selection=True, long=True)
    if not selbObj:
        return ""
    shaderName = getShaderNameFromNode(selbObj[0], removeSuffix=removeSuffix)
    return shaderName


def connectSurfaceShaderToViewportShader(surfaceShader, viewportShadingGroup, renderer, connectedCount=0):
    """Connects the surface shader (usually the renderer shader) to the viewport shaders shading group
    Usually via the surface attribute.
    Useful while rendering in an engine whilst having the shaders looking nice in the viewport.
    This is a single shader setup

    :param surfaceShader:  the renderers shader to be connected to the viewport shaders shading group
    :type surfaceShader: str
    :param viewportShadingGroup: the viewport shaders shading group name
    :type viewportShadingGroup: str
    :param connectedCount: useful for looping and messaging, usually used by another function for counting connections
    :type connectedCount: int
    :param renderer: which renderer are you using "redshift", "arnold", "vray", mentalRay", "renderman".  Only Redshift is supported
    :type renderer: str
    :return connectedCount:  Was the connection made, if so return this number as a +1
    :rtype connectedCount: int
    """
    if renderer == "redshift":
        try:
            cmds.connectAttr("{}.outColor".format(surfaceShader), "{}.rsSurfaceShader".format(viewportShadingGroup))
            connectedCount += 1
        except RuntimeError:
            om2.MGlobal.displayWarning(
                'The Shading Group `{}` is probably already connected. Skipping.'.format(viewportShadingGroup))
    elif renderer == "arnold":
        try:
            cmds.connectAttr("{}.outColor".format(surfaceShader), "{}.aiSurfaceShader".format(viewportShadingGroup))
            connectedCount += 1
        except RuntimeError:
            om2.MGlobal.displayWarning(
                'The Shading Group `{}` is probably already connected. Skipping.'.format(viewportShadingGroup))
    elif renderer == "mentalRay":
        pass
    elif renderer == "vRay":
        pass
    elif renderer == "renderman":
        pass
    return connectedCount


def saveSelectedShader(directory, saveType="auto"):
    """Saves selected shader

    :param directory: The directory to save the shader
    :type directory: str
    :param saveType: "auto" saves ma and if unknown nodes saves mb, "ma" saves .ma and "mb" saves .mb
    :type saveType: str
    :return:
    :rtype:
    """
    sel = list(zapi.selected())
    if len(sel) > 0:
        firstSelected = sel[0]
        shaderInSceneName = getShaderNameFromNode(firstSelected.fullPathName(), removeSuffix=False)
        # there's an edge where the shader may not be connected to a shading group so in this
        # case request from the user whether forcing an exporting by simple exporting the selected will be
        # ok.
        if not shaderInSceneName:
            sceneShader = firstSelected
            shaderInSceneName = sceneShader.name(includeNamespace=True)
            message = """
            No shading group was found. 
            We can't be certain that this node is a shader. 
            The incoming network to this node will be saved. 
            Proceed?
            """
            forceExport = elements.MessageBox.showQuestion(parent=None, title="No Shading Group Found",
                                                           message=message)
            if forceExport == "A":
                pass
            elif forceExport == "B":
                return
        else:
            sceneShader = zapi.nodeByName(shaderInSceneName)
        shaderName = elements.MessageBox.inputDialog(title="Save Shaders", text=shaderInSceneName,
                                                     parent=None, message="New shader name:")
        if shaderName:
            # If the hypershade is open while we rename something that is selected it will give a
            # random object not found error.
            cmds.select("lambert1")  # We select lambert instead so that doesn't happen

            shaderName = strutils.fileSafeName(shaderName)
            newDir = zpath.normpath(os.path.join(directory, shaderName))
            if os.path.isdir(newDir):
                output.displayInfo("Warning: '{}' already exists. The file will be saved there".format(newDir))
            else:
                os.makedirs(newDir)
            # Get a file name that doesn't exist yet
            newName = shaderName
            if saveType == "auto":
                saveType = "ma"
                if mayaFileType(message=False) == "mayaBinary" and (
                        scene.hasUnknownPlugins() or scene.hasUnknownNodes()):
                    saveType = "mb"
                    logger.debug("Saving Shader as Binary")

            path = os.path.normpath(os.path.join(newDir, "{}.{}".format(newName, saveType)))
            if os.path.exists(path):
                uniqueName = uniqueFileName(dirPath=newDir, name=shaderName, ext=saveType)
                choice = elements.MessageBox.showMultiChoice(title="Existing file found",
                                                             message="File already exists. Override?",
                                                             choices=["Override.", "Rename to '{}'".format(uniqueName)],
                                                             buttonB="Cancel")
                if choice[0] == 0:
                    os.remove(path)
                elif choice[0] == 1:
                    newName = uniqueName
                    path = os.path.normpath(os.path.join(newDir, "{}.{}".format(newName, saveType)))
                else:
                    return

            # If new name already exists in scene, temporarily rename the clashing shader
            clashingNode = None
            if cmds.objExists(newName):
                clashingNode = zapi.nodeByName(newName)
                if clashingNode != sceneShader:
                    randomName = "shader" + str(uuid.uuid4())[:6].replace("-", "")
                    clashingNode.rename(randomName)

            sceneShader.rename(newName)

            exportShader(newName, path, type_=saveType)

            # There are two objects to rename, the shader that had the same name as the chosen name if it exists,
            # and the actual shader.

            sceneShader.rename(shaderInSceneName)

            if clashingNode:  # Rename the clashing shader back to the original
                clashingNode.rename(newName)

            cmds.select(zapi.fullNames(sel))

            return True
        else:
            output.displayInfo("Cancelled or invalid name")

    else:
        output.displayWarning("Object or shader must be selected")


def uniqueFileName(dirPath, name, ext="ma"):
    """ Generates a unique file name based on the directory path

    :param dirPath:
    :param name:
    :param ext:
    :return:
    """
    uniqueName = name
    os.path.exists(os.path.join(dirPath, "{}.{}".format(uniqueName, ext)))
    # Get a file name that doesn't exist
    while os.path.exists(os.path.join(dirPath, "{}.{}".format(uniqueName, ext))):
        uniqueName = namehandling.incrementName(uniqueName)

    return uniqueName


def exportShader(shader, path, type_="ma"):
    """ Export shader to file path

    :param shader:
    :param path:
    :return:
    """
    sel = cmds.ls(selection=True, long=True)
    cmds.select(shader)
    if type_ == "mb":
        typ = "mayaBinary"
    else:
        typ = "mayaAscii"
    cmds.file(path, op="v=0;p=17;f=0", typ=typ, pr=1, exportSelected=1)
    logger.debug("Shader exported to: '{}'".format(path))
    cmds.select(sel)


def assignSurfaceShaderWildcard(surfaceSuffix="RS", viewportSuffix="VP2", renderer="redshift"):
    """Connects the surface shader (usually the renderer shader) to the viewport shader via the surface attribute.
    Useful while rendering in an engine whilst having the shaders looking nice in the viewport.
    works off matching suffix shader names eg skin_RS => skin_VP2's shading group
    To Do
    1. checks if the shader is already connected, if not disconnects the current connection and reconnects
    2. disconnect

    :param surfaceSuffix: The user defined suffix of the renderer shader
    :type surfaceSuffix: str
    :param viewportSuffix: The user defined suffix of the viewport shader
    :type viewportSuffix: str
    :param renderer: which renderer are you using "redshift", "arnold", "vray", mentalRay", "renderman".  Only Redshift is supported
    :type renderer: str
    """
    connectedCount = 0
    surfaceShaderList = getShaderWildcard(surfaceSuffix)  # find all potential surface shaders
    if not surfaceShaderList:
        om2.MGlobal.displayWarning('No Surface Shaders Found With Suffix `{}`'.format(surfaceSuffix))
        return
    for surfaceShader in surfaceShaderList:
        viewportShader = surfaceShader.replace(surfaceSuffix, viewportSuffix)
        if cmds.objExists(viewportShader):  # do the connection
            viewportShadingGroup = getShadingGroupFromShader(viewportShader)  # get the shading group
            if not viewportShadingGroup:
                om2.MGlobal.displayWarning('The Shader `{}` has no Shading Group Skipping'.format(viewportShader))
            # Main function
            connectedCount = connectSurfaceShaderToViewportShader(surfaceShader, viewportShadingGroup, renderer,
                                                                  connectedCount=connectedCount)
    if not connectedCount:
        om2.MGlobal.displayWarning('No Shaders Connected')
        return
    om2.MGlobal.displayInfo('Success: {} Shaders Connected'.format(connectedCount))


def cleanNamespaces(objs, prefix=""):
    """ Remove the namespace
    
    :param objs: 
    :param prefix: 
    :return: 
    """
    for ob in objs:
        if ":" in ob and cmds.objExists(ob):
            newName = ob.split(":")[-1]
            if prefix != "":
                newName = "{}_{}".format(prefix, newName)

            namehandling.safeRename(ob, newName)


def renameShader(shader, newName, shaderGroup=True):
    """ Rename the shader and the shader group

    :param shader:
    :param newName:
    :param shaderGroup:
    :return:
    """

    sg = getShadingGroupFromShader(shader)
    namehandling.safeRename(shader, newName)
    if sg and shaderGroup:
        namehandling.safeRename(sg, namehandling.generateUniqueName(newName + "SG"))


def replaceShader(oldShader, newShader):
    """ Replaces all objects with the old shader with the new shader

    :param oldShader:
    :param newShader:
    :return:
    """
    # Get selected shaders, replace with new shader
    sel = cmds.ls(sl=1)
    cmds.select(oldShader, replace=True)
    cmds.hyperShade(objects="")
    oldShaderSel = cmds.ls(sl=1)
    assignShader(oldShaderSel, newShader)
    cmds.select(sel, replace=True)


def shaderExists(name):
    """ Returns True if shader exists

    :param name:
    :return:
    """
    return len(cmds.ls(name, mat=True)) > 0


def deleteShaderNetwork(shaderName):
    """deletes the shader network of a shader

    :param shaderName: the name of the shader
    :type shaderName: str
    :return shaderNodes: all nodes deleted
    :rtype shaderNodes: list
    """
    shaderNodes = cmds.hyperShade(listUpstreamNodes=shaderName)
    shadingGroup = getShadingGroupFromShader(shaderName)
    shaderNodes = shaderNodes + [shaderName, shadingGroup]
    for node in shaderNodes:
        if cmds.objExists(node):
            cmds.delete(node)
    return shaderNodes


def deleteShaderNetworkList(shaderList):
    """Deletes the shading network of a shading node

    :param shaderList: a list of maya shader names
    :type shaderList: list
    :return shaderNodeDeletedList:
    :rtype shaderNodeDeletedList:
    """
    shaderNodeDeletedList = list()
    for shader in shaderList:
        shaderNodesDeleted = deleteShaderNetwork(shader)
        shaderNodeDeletedList += shaderNodesDeleted
    return shaderNodeDeletedList


"""
SELECTION MACROS
"""


def shaderOpenAttrEditor():
    """Selects the shader of the selected object and opens the attribute editor.

    :return:
    :rtype:
    """
    shaderList = getShadersSelected()
    if shaderList:
        cmds.select(shaderList, replace=True)
        mel.eval('openAEWindow')  # attribute editor
        return shaderList
    return []


def selectNodeOrShaderAttrEditor():
    """This script selects the shader or the selected nodes:

        1. Selects the node if selected in the channel box and opens the attribute editor
        2. Or if a transform node is selected, select the shaders of the current selection and open attr editor

    :return selectedReturn: A list of the currently selected objects/shader nodes
    :rtype selectedReturn: list
    """
    selectedObjs = cmds.ls(selection=True, long=True)
    if not selectedObjs:
        return
    firstObj = selectedObjs[0]
    if cmds.objectType(firstObj, isType='transform'):  # then select the shader of this object
        return shaderOpenAttrEditor()
    elif selection.componentSelectionType([firstObj]) is not None and selection.componentSelectionType(
            [firstObj]) != 'object':  # is not object or None
        shaderOpenAttrEditor()
    else:  # select the current node and open attr editor
        cmds.select(firstObj, replace=True)
        mel.eval('openAEWindow')
        selectedReturn = [firstObj]
        return selectedReturn
    return selectedObjs


"""
RENAME SHADING GROUPS FROM SHADER NAMES
"""


def renameShadingGroup(shaderName):
    shadingGroup = getShadingGroupFromShader(shaderName)
    if shadingGroup:
        shadingGroup = namehandling.safeRename(shadingGroup, "{}_SG".format(shadingGroup))
    return shadingGroup


def renameShadingGroupsScene():
    dontRename = [u'lambert1', u'standardSurface1', u'particleCloud1']
    shadingGroupList = list()
    shaderList = getAllShaders()

    for shdr in dontRename:
        try:
            shaderList.remove(shdr)
        except:
            pass

    for shdr in shaderList:
        sg = renameShadingGroup(shdr)
        if sg:
            shadingGroupList.append(sg)

    om2.MGlobal.displayInfo("Shading groups renamed: {}".format(shadingGroupList))
    return shadingGroupList


"""
SHADER SINGLETON INSTANCE FOR COPYING DATA
"""


@six.add_metaclass(classtypes.Singleton)
class ZooShaderTrackerSingleton(object):
    """Used by the shader marking menu other UIs

    """

    def __init__(self):
        self.copiedShaderName = ""
        self.copiedShaderAttrs = dict()
