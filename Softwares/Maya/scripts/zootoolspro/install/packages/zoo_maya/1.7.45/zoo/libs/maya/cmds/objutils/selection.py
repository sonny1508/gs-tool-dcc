"""selection based code

Example use:

.. code-block:: python

    from zoo.libs.maya.cmds.objutils import selection
    from maya import cmds

    selObjs = cmds.ls(selection=True)
    faces = selection.numberListToComponent(selObjs[0], numberList, componentType="faces")

Author: Andrew Silke
"""

import re
import random

import maya.mel as mel

import maya.cmds as cmds
from maya.api import OpenMaya as om2
from zoo.libs.maya.cmds.objutils import filtertypes
from zoo.libs.utils import output

"""
MESSAGE
"""


def selWarning(warningTxt="Please make a selection", message=True, long=False):
    """Basic selection function with warning if nothing is selected"""
    selList = cmds.ls(selection=True, long=long)
    if not selList:
        if message:
            om2.MGlobal.displayWarning(warningTxt)
        return list()
    return selList


"""
FILTERS
"""


def convertGeometryFaces(nodeList, individualFaces=False):
    """From a list of node string names, return only those objects that are polys, nurbs or polyfaces

    :param nodeList: list of Maya node names
    :type nodeList: list(str)
    :param individualFaces: If True then break up the faces so that each face is an individual list item
    :type individualFaces: bool
    :return geoFaceList: list of Maya poly, nurbs and polyfaces list
    :rtype geoFaceList: list(str)
    """
    faceList = list()
    meshList = filtertypes.filterTypeReturnTransforms(nodeList, shapeType="mesh")
    nurbsList = filtertypes.filterTypeReturnTransforms(nodeList, shapeType="nurbsSurface")
    for node in nodeList:
        if ".f" in node:
            faceList.append(node)
    if individualFaces and faceList:
        # Face list will be converted into individual faces, can be lots of items in face selection
        faceList = componentFullList(faceList)
    geoFaceList = nurbsList + meshList + faceList
    return geoFaceList


"""
COMPONENT SELECTION
"""


def componentByObject(componentList):
    """From a component list, return a nested list with components sorted per object:

        [pCube2.e[4], pCylinder1.e[9], pCylinder1.e[2], pCSphere[9]]

    Returns:

        [[pCube2.e[4]], [pCylinder1.e[9], pCylinder1.e[2]], [pCSphere[9]]]

    :param componentList: A list of components, can be objects too
    :type componentList: list(str)
    :return componentNestedList: a list of lists, the first list is by object name and then all components of that name
    :rtype componentNestedList: list(list(str))
    """
    nameList = list()
    componentNestedList = list()
    for c in componentList:
        objName = c.split(".")[0]
        if objName not in nameList:
            componentNestedList.append([c])
            nameList.append(objName)
        else:
            index = nameList.index(objName)
            componentNestedList[index].append(c)
    return componentNestedList


def selectObjectNoComponent(message=True):
    """If in component mode with nothing selected, return to the object mode and return those objects instead.

    Returns the potentially updated selection, and if the user is in component mode or not

    Used in a lot of UV functions when nothing is selected you still want to operate on the current object.

    :param message: Return the messages to the user?
    :type message: bool
    :return selObjs: maya selection, could be components or objects.
    :rtype selObjs: list(str)
    :return componentMode: True if in component mode eg vertex or edge mode, False if in object mode.
    :rtype componentMode: bool
    """
    componentMode = False
    selObjs = cmds.ls(selection=True)
    if not selObjs:
        if not cmds.selectMode(query=True, component=True):  # check if in component mode
            if message:
                om2.MGlobal.displayWarning("Please select an object or its components")
            return selObjs, componentMode  # [], False
        # Is in component mode
        componentMode = True
        mel.eval('SelectTool')  # some tools lock the user from returning to object mode
        cmds.selectMode(object=True)
        selObjs = cmds.ls(selection=True)
        if not selObjs:
            if message:
                om2.MGlobal.displayWarning("Please select an object or its components")
    return selObjs, componentMode


def componentFullList(componentSelection):
    """Converts a component selection list into a full list

    Example:
        ["pSphere4.e[22:24]"]
        becomes
        ["pSphere4.e[22]", "pSphere4.e[23]", "pSphere4.e[24]"]

    :param componentSelection: A selection of Maya components eg ["pSphere4.e[1438:1439]", "pSphere4.e[23:25]"]
    :type componentSelection: list(str)
    """
    return cmds.ls(componentSelection, flatten=True)  # remove ":" entries


def componentNumberList(componentSelection):
    """Converts a component selection list into number list

    Assumes only components are from a single object

    Example:
        ["pSphere4.e[22:24]"]
        becomes
        [22, 23, 24]

    :param componentSelection: A selection of Maya components eg ["pSphere4.e[1438:1439]", "pSphere4.e[23:25]"]
    :type componentSelection: list(str)
    """
    componentFullList = list()
    flattenedList = cmds.ls(componentSelection, flatten=True)
    for component in flattenedList:
        m = re.search(r"(?<=\[).+?(?=\])", component)
        componentValue = m.group(0)  # will be something like "23:25".  Note will fail if no square brackets [23:25]
        componentFullList.append(int(componentValue))
    return componentFullList


def countComponentsInSelection(componentSelection):
    """Counts the amount of components in a selection, should be filtered to only one component type ie only edges

    :param componentSelection: A selection of Maya components eg ["pSphere4.e[1438:1439]", "pSphere4.e[23:25]"]
    :type componentSelection: list(str)
    :return componentCount: The exact numbers of components in the selection
    :rtype componentCount: int
    """
    return len(cmds.ls(componentSelection, flatten=True))


def numberListToComponent(obj, numberList, componentType="uvs"):
    """Takes a number list and makes it into a component selection

    Example:
        "pSphere", [22, 23, 24], "edges"
        becomes
        ["pSphere.e[22]", "pSphere.e[23]", "pSphere.e[24]"]

    :param obj: A maya object
    :type obj: str
    :param numberList: a list of numbers that represent component numbers
    :type numberList: list(int)
    :param componentType: the type of component "uvs", "edges", "faces", "vtx"
    :type componentType:
    :return componentSelection: The component list now created
    :rtype componentSelection: list(str)
    """
    componentSelection = list()
    if componentType == "uvs":
        type = "map"
    elif componentType == "edges":
        type = "e"
    elif componentType == "faces":
        type = "f"
    else:  # "vertices"
        type = "vtx"
    for n in numberList:
        componentSelection.append("{}.{}[{}]".format(obj, type, n))
    return componentSelection


def componentsToObjectList(componentSelection):
    """From a list of components return only the objects in the selection. Handles long or short names and namespaces

    Example:
        ["pSphere.e[22]", "pSphere.e[23]", "pCube.e[24]"]
        becomes
        ["pSphere", "pCube"]

    :param componentSelection: A list of components or objects or both
    :type componentSelection: list(str)
    :return objectList: A list of objects now filtered
    :rtype objectList: list(str)
    """
    objList = list()
    for sel in componentSelection:
        objList.append(sel.split(".")[0])
    return list(set(objList))  # Remove duplicates


def componentSelectionFilterType(selectedComponents, selectType):
    """Pass in a selection and will return the single selection list specified by selectType:

        selectType can be "faces", "vertices", or "edges"

    :param selectedComponents: Regular Maya selection list
    :type selectedComponents: list(str)
    :param selectType: The selection to return can be "faces", "vertices", or "edges"
    :type selectType: str
    :return fileteredSelection: The selection now filtered by type
    :rtype fileteredSelection: list(str)
    """
    filteredSelection = list()
    if selectType == "edges":
        for sel in selectedComponents:
            if ".e[" in sel:
                filteredSelection.append(sel)
    elif selectType == "faces":
        for sel in selectedComponents:
            if ".f[" in sel:
                filteredSelection.append(sel)
    elif selectType == "vertices":
        for sel in selectedComponents:
            if ".vtx[" in sel:
                filteredSelection.append(sel)
    return filteredSelection


def componentSelectionType(componentSelection):
    """Returns "object", "vertices", "edges", "faces" or "uvs" depending on the first selection type.

    Will return None if unknown

    :param componentSelection: a Maya selection
    :type componentSelection: list(str)
    :return componentType: the type of component as the first selection, eg. "vertices"
    :rtype componentType: str
    """
    if not componentSelection:  # nothing selected
        return None
    if "." not in componentSelection[0]:
        return "object"
    elif ".vtx[" in componentSelection[0]:
        return "vertices"
    elif ".e[" in componentSelection[0]:
        return "edges"
    elif ".f[" in componentSelection[0]:
        return "faces"
    elif ".map[" in componentSelection[0]:
        return "uvs"
    return None


def componentOrObject(componentSelection):
    """Returns either "object" or "component" or "uv" depending on the first selection type.

    Return None if unknown

    :param componentSelection: a Maya selection
    :type componentSelection: list(str)
    :return componentType: "component", "object" or None
    :rtype componentType: str
    """
    if not componentSelection:  # nothing selected
        return None
    elif "." not in componentSelection[0]:
        return "object"
    elif ".vtx[" in componentSelection[0]:
        return "component"
    elif ".e[" in componentSelection[0]:
        return "component"
    elif ".f[" in componentSelection[0]:
        return "component"
    elif ".map[" in componentSelection[0]:
        return "uv"
    return None


def selectComponentSelectionMode(componentType="vertices"):
    """Selects a component mode "vertices", "edges", "faces" or "uvs"

    :param componentType: The component mode to enter "vertices", "edges", "faces" or "uvs"
    :type componentType: str
    """
    # todo add object mode
    if not componentType:
        return
    elif componentType == "vertices":
        cmds.selectType(smp=1, pv=1)  # vert selection
    elif componentType == "edges":
        cmds.selectType(sme=1, pe=1)  # edge selection
    elif componentType == "faces":
        cmds.selectType(smf=1, pf=1)  # face selection
    elif componentType == "uvs":
        cmds.selectType(smu=1, puv=1)  # face selection


def convertSelection(type="faces"):
    """Converts a selection to either edges, faces, vertices, or uvs

    selectType can be:
        "faces"
        "vertices"
        "edges"
        "edgeLoop"
        "edgeRing"
        "edgePerimeter"
        "uvs"
        "uvShell"
        "uvShellBorder"

    :param type: The selection to convert to "faces", "vertices", "edges", "edgeRing" etc see function documentation
    :type type: str
    """
    if type == "faces":
        mel.eval('ConvertSelectionToFaces;')
    elif type == "vertices":
        mel.eval('ConvertSelectionToVertices;')
    elif type == "edges":
        mel.eval('ConvertSelectionToEdges;')
    elif type == "uvs":
        mel.eval('ConvertSelectionToUVs;')
    elif type == "edgeLoop":
        mel.eval("SelectEdgeLoopSp;")
    elif type == "edgeRing":
        mel.eval("SelectEdgeRingSp;")
    elif type == "edgePerimeter":
        mel.eval("ConvertSelectionToEdgePerimeter;")
    elif type == "uvShell":
        mel.eval("ConvertSelectionToUVShell;")
    elif type == "uvShellBorder":
        mel.eval("ConvertSelectionToUVShellBorder;")

    return cmds.ls(selection=True)


"""
INVERT
"""


def invertSelection():
    mel.eval('invertSelection;')


"""
HIERARCHY
"""


def selectHierarchy(nodeType='transform'):
    """Filters the select hierarchy command by a node type, usually transform type so it doesn't select the shape nodes

    :param nodeType: type of node to be filtered in the selection, usually transform
    :type nodeType: str
    :return: objsFiltered: the objs selected
    :type filterList: list
    """
    cmds.select(hierarchy=True, replace=True)
    objsAllHierachy = cmds.ls(selection=True, long=True)
    objsFiltered = cmds.ls(objsAllHierachy, type=nodeType)
    cmds.select(objsFiltered, replace=True)
    return objsFiltered


"""
GROW/SHRINK
"""


def growSelection():
    """Standard maya grow component selection ">" hotkey """
    mel.eval('PolySelectTraverse 1;')


def shrinkSelection():
    """Standard maya grow component selection "<" hotkey """
    mel.eval('PolySelectTraverse 2;')


"""
RANDOM SELECTION
"""


def randomSelection(randomPercent):
    """From the current selection objs or components, select random objects given the randomAmount:

        50.0  will select 50% of objects in the selection
        10.0 will select 10% of the objects in the selection

    :param randomPercent: A value between 0 and 1.  0.5 selects 50% of objects 0.1 selects 10%
    :type randomPercent: float
    :return newSelection: A list of the randomly selected objects
    :rtype newSelection: list(str)
    """
    selObj = cmds.ls(selection=True)
    newSelection = list()
    if not selObj:
        output.displayWarning("No objects selected, please select objects.")
        return newSelection
    if componentSelectionType(newSelection) != "object":  # selection is a component
        # select each component separately.
        selObj = componentFullList(selObj)  # make sure each individual component is selected.
    random.shuffle(selObj)
    listLen = len(selObj)
    selLen = int(round(float(listLen) * (randomPercent / 100)))
    for i in range(selLen):
        newSelection.append(selObj[i])
    cmds.select(newSelection, replace=True)
    return newSelection


def selectionPairs(oddEven=False, forceEvenSelection=True, type="transform"):
    """Returns selection pairs usually "transforms"

    ["objA", "objB", "objC", "objD"]

    oddEven True returns:
        ["objA", "objC"], ["objB", "objD"]

    oddEven False returns:
        ["objA", "objB"], ["objC", "objD"]

    :param oddEven: If true the returned lists will be odd and even, False will be first half then second half
    :type oddEven: bool
    :param type: Type of node to filter ie "transform" can be None.
    :type type: str
    :return twoLists: Returns two matching object lists based off the selection.
    :rtype twoLists: tuple(list(str), list(str))
    """
    if type:
        selObjs = cmds.ls(selection=True, type=type)
    else:
        selObjs = cmds.ls(selection=True)
    if not selObjs:
        if type:
            output.displayInfo("Please select objects of type `{}`".format(type))
        else:
            output.displayInfo("Please select objects")
        return list(), list()
    if (len(selObjs) % 2) != 0 and forceEvenSelection:  # not even
        output.displayWarning("There is an odd number of objects selected, must be even.")
        return list(), list()
    if oddEven:  # returns odd and even selection ------------
        evenSel = selObjs[::2]  # starts at 0
        oddSel = selObjs[1::2]
        return evenSel, oddSel
    # Return first half of the selection and second half ------------
    firstHalfSel = selObjs[:len(selObjs) // 2]
    secondHalfSel = selObjs[len(selObjs) // 2:]
    return firstHalfSel, secondHalfSel


"""
SELECTION SETS
"""


def addSelectionSet(selectSetName, objs):
    """Adds to an existing selection set, or if it doesn't exist then create

    :param selectSetName: The name of the select set
    :type selectSetName: str
    :param objs: A list of objects or nodes or components
    :type objs: list(str)
    :return selSet: The selection set name, if created could be a duplicate though unlikely
    :rtype selSet: str
    """
    if not cmds.objExists(selectSetName):
        selSet = cmds.sets(objs, name=selectSetName)
        cmds.sets(selSet, e=True, text="gCharacterSet")
    else:
        cmds.sets(objs, addElement=selectSetName)
        selSet = str(selectSetName)
    return selSet


def nodesInListSelSets(selectionSets):
    """Returns the objects in a selection set list, ignores sets if they do not exist.

    :param selectionSets: A list of selection set names.
    :type selectionSets: list(str)
    :return objs: A list of object/node/component names
    :rtype objs: list(str)
    """
    objs = list()
    for selSet in selectionSets:
        if not cmds.objExists(selSet):
            continue
        objs += cmds.sets(selSet, query=True)
    return objs


def meshSelectionWarning(nodes):
    """Warns the user if the selection is not a mesh

    :return: Selection contains mesh objects.
    :rtype: bool
    """
    if not nodes:
        output.displayWarning("Please select a mesh object. Nothing is selected.")
        return False
    if not filtertypes.filterTypeReturnShapes(nodes, children=False, shapeType="mesh"):
        # check for face edge or vertex selection
        if componentOrObject(nodes) == "component":
            return True
        output.displayWarning("Please select a mesh object. No mesh objects found.")
        return False
    return True