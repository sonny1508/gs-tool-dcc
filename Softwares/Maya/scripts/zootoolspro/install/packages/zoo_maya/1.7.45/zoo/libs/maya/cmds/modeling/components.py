"""Also see cmds.objutils.selection for various functions
"""
import re
import time

import maya.cmds as cmds
from zoo.libs.utils import output
from zoo.libs.maya.cmds.objutils import filtertypes, selection


def normalListFromVtxFaces(vtxFaceList):
    normalList = list()
    for vtxFace in vtxFaceList:
        normalList.append(cmds.polyNormalPerVertex(vtxFace, query=True, xyz=True)[0])
    return normalList


def softFromEdge(edge):
    """From an edge determine if its soft or hard from the vert normals

    :param edge: A maya edge selection eg. "pSphere1.e[101]"
    :type edge: str

    :return soft: True if soft False if hard
    :rtype soft: bool
    """
    vtxFaces = cmds.polyListComponentConversion(edge, fromEdge=True, toVertexFace=True)
    vtxFaces = cmds.ls(vtxFaces, flatten=True)  # remove ":" entries
    startName = "{}]".format(vtxFaces[0].split("][")[0])
    firstList = [vtxFaces[0]]
    secondList = list()
    for vertFace in vtxFaces[1:]:
        if startName in vertFace:
            firstList.append(vertFace)
        else:
            secondList.append(vertFace)
    # check if all normals of the first list and second matches, will be soft
    if len(set(normalListFromVtxFaces(firstList))) == 1 and len(set(normalListFromVtxFaces(secondList))) == 1:
        return True
    return False


def softEdgeList(obj, time=False):
    """For each edge in a polygon object check if it's hard or soft and return as a list

    NOTE: Unused as is too slow, now using zoo.libs.buliarcacristian.lockNormals_toHS

    Annoying function to work around not being able to set vertexNormals without locking them.

    WARNING:  This takes a lot of time on dense meshes 20sec per 3k faces. Slow function

    :param obj: A maya Mesh object transform node
    :type obj: str

    :return edgeList: A list of edges of the object ["pSphere1.e[60:61]" "pSphere1.e[63:66]"]
    :rtype edgeList: list(str)
    :return softList: A list of soft edges True/False will match the edgeList [True, False]
    :rtype softList: list(bool)
    """
    if time:
        t0 = time.time()
    edgeList = cmds.ls('{}.e[*]'.format(obj), flatten=True)
    softList = list()
    for edge in edgeList:  # checks if all the vert normals match, if yes is a soft edge else is hard
        softList.append(softFromEdge(edge))
    if time:  # Because it can take ages
        t1 = time.time()
        output.displayInfo("time = {}".format(t1-t0))
    return edgeList, softList


# ------------------
# TRIS and NGONS
# ------------------

def selectFacesComponentMode(faces):
    """Selects faces while in component mode"""
    selObjs = selection.componentsToObjectList(faces)
    cmds.select(selObjs, replace=True)
    cmds.selectMode(component=True)
    cmds.selectType(polymeshFace=True)
    cmds.select(faces, replace=True)


def tris(meshList, select=True, message=True):
    """From a list of mesh shapes return the triangle faces

    :param meshList: A list of mesh shapes
    :type meshList: list(str)
    :param select: Select the faces?
    :type select: list(str)
    :param message: Report a message to the user?
    :type message: bool

    :return tris: A list of selected faces
    :rtype tris: list(str)
    """
    rememberSelection = cmds.ls(selection=True)
    cmds.select(meshList, replace=True)
    cmds.polySelectConstraint(mode=3, type=0x0008, size=1)
    cmds.polySelectConstraint(disable=True)
    tris = cmds.filterExpand(ex=True, sm=34) or []
    if not select or not tris:
        cmds.select(rememberSelection, replace=True)
    else:
        selectFacesComponentMode(tris)
    if message:
        if not tris:
            output.displayInfo("No triangles found.")
        elif select:
            output.displayInfo("Triangles selected")
    return tris


def ngons(meshList, select=True, message=True):
    """From a list of mesh shapes return the triangle faces

    :param meshList: A list of mesh shapes
    :type meshList: list(str)
    :param select: Select the faces?
    :type select: list(str)
    :param message: Report a message to the user?
    :type message: bool

    :return ngons: A list of selected faces
    :rtype ngons: list(str)
    """
    rememberSelection = cmds.ls(selection=True)
    cmds.select(meshList, replace=True)
    cmds.polySelectConstraint(mode=3, type=0x0008, size=3)
    cmds.polySelectConstraint(disable=True)
    ngons = cmds.filterExpand(ex=True, sm=34) or []
    if not select or not ngons:
        cmds.select(rememberSelection, replace=True)
    else:
        selectFacesComponentMode(ngons)
    if message:
        if not ngons:
            output.displayInfo("No ngons found.")
        elif select:
            output.displayInfo("Ngons selected")
    return ngons


def selectedMeshes(message=True):
    """Returns mesh nodes from the current selection

    :param message: Report a message to the user?
    :type message: bool

    :return meshList: A list of mesh nodes
    :rtype meshList: list(str)
    """
    selObjs = cmds.ls(selection=True)
    if not selObjs:
        if message:
            output.displayWarning("Please select some mesh objects. Nothing is selected")
        return list()
    selObjs = selection.componentsToObjectList(selObjs)  # if component selection, return only objects
    meshList = filtertypes.filterTypeReturnShapes(selObjs, children=False, shapeType="mesh")
    if not meshList:
        if message:
            output.displayWarning("No mesh objects were found in the selection")
        return list()
    return meshList


def ngonsFromSelection(select=True, message=True):
    """From the current selection return or select all the ngon faces

    :param select: Select the faces?
    :type select: list(str)
    :param message: Report a message to the user?
    :type message: bool

    :return ngons: A list of selected faces
    :rtype ngons: list(str)
    """
    meshList = selectedMeshes(message=message)
    if not meshList:  # message already reported
        return list()
    return ngons(meshList, select=select)


def trisFromSelection(select=True, message=True):
    """From the current selection return or select all the tri faces

    :param select: Select the faces?
    :type select: list(str)
    :param message: Report a message to the user?
    :type message: bool

    :return tris: A list of selected faces
    :rtype tris: list(str)
    """
    meshList = selectedMeshes(message=message)
    if not meshList:  # message already reported
        return list()
    return tris(meshList, select=select)

