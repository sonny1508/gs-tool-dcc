import maya.cmds as cmds
import maya.api.OpenMaya as om2

ZOO_THICKNESS_ATTR = "zooCenterThickness"


def meshObjs(objList):
    """Filters only meshes

    :param objList: list of objects
    :type objList: list(str)
    :return meshList: list of meshes
    :rtype meshList: list(str)
    """
    meshList = list()
    for obj in objList:
        shapes = cmds.listRelatives(obj, shapes=True, fullPath=True, type="mesh")
        if shapes:
            meshList.append(obj)
    return meshList


def meshObjsSelected():
    """Returns meshes that are selected

    :return meshList: list of meshes
    :rtype meshList: list(str)
    """
    selObjs = cmds.ls(selection=True, long=True)
    if not selObjs:
        return selObjs
    return meshObjs(selObjs)


def extrudeCenterThickness(obj, thickness=1.0, weight=0.5, select=True):
    """Extrudes a flat object to be thick so that the extrude affects both sides, making it thicker on both sides. \

    Or as per the weight value.  0.5 is centered, 1 extrudes down, zero extrudes up.

    Also supports object lists so long as faces or mesh objects.

    :param obj: The name of the object or face list to extrude
    :type obj: list(str)
    :param thickness: The thickness of the object in Maya units usually cms
    :type thickness: float
    :param weight: Controls the direction of the extrude, 0.5 is center and the extrude will go out each side
    :type weight: float
    :param select: Select the original selection after the extrude completes?
    :type select: bool
    :return extrudeNode: The name of the extrudeNode that was created
    :rtype extrudeNode: str
    :return moveVertNode: The name of the extrudeNode that was created
    :rtype moveVertNode: str
    """
    selObjs = list()
    if not select:
        selObjs = cmds.ls(selection=True, long=True)
    moveDistance = (thickness - (thickness * weight)) * -1
    moveVertNode = cmds.polyMoveVertex(obj, localTranslateZ=moveDistance)[0]  # move verts
    extrudeNode = cmds.polyExtrudeFacet(obj, localTranslateZ=thickness)[0]  # extrude
    if select:
        cmds.select(obj, replace=True)
    else:
        cmds.select(selObjs, replace=True)
    # add identifier attributes
    cmds.addAttr(moveVertNode, longName=ZOO_THICKNESS_ATTR, attributeType='float', keyable=False)
    cmds.addAttr(extrudeNode, longName=ZOO_THICKNESS_ATTR, attributeType='float', keyable=False)
    return extrudeNode, moveVertNode


def extrudeCenterThicknessSelected(thickness=1.0, weight=0.5, select=True, message=True):
    """Extrudes selected flat object to be thick so that the extrude affects both sides, making thicker on both sides. \

    Or as per the weight value.  0.5 is centered, 1 extrudes down, zero extrudes up.

    Also supports object lists so long as faces or mesh objects.

    :param obj: The name of the object or face list to extrude
    :type obj: list(str)
    :param thickness: The thickness of the object in Maya units usually cms
    :type thickness: float
    :param weight: Controls the direction of the extrude, 0.5 is center and the extrude will go out each side
    :type weight: float
    :param select: Select the original selection after the extrude completes?
    :type select: bool
    :param message: Report the message to the user?
    :type message: bool
    """
    faceList = list()
    selObjs = cmds.ls(selection=True, long=True)
    if not selObjs:
        if message:
            om2.MGlobal.displayWarning("No polygon objects selected, please select a polygon object or face.")
        return
    for obj in selObjs:
        if ".f" in obj:
            faceList.append(obj)
    meshList = meshObjs(selObjs)
    validObjs = meshList + faceList
    if not validObjs:
        if message:
            om2.MGlobal.displayWarning("No polygon objects selected, please select a polygon object or face.")
        return
    for obj in validObjs:
        extrudeCenterThickness(obj, thickness=thickness, weight=weight, select=select)
    cmds.select(validObjs, replace=True)


def centerThicknessNode(obj, nodeType="polyExtrudeFace"):
    """Returns a legit centerThickness node related to obj, of either type:

        "polyMoveVertex"
        "polyExtrudeFace"

    :param obj: The name of the object to search the input connections
    :type obj: str
    :param nodeType: either "polyMoveVertex" or "polyExtrudeFace"
    :type nodeType: str
    :return node: returns the node name or "" if not found
    :rtype node: str
    """
    allInputs = cmds.listHistory(obj)
    nodes = cmds.ls(allInputs, exactType=nodeType)
    if not nodes:
        return ""
    for extrudeNode in nodes:
        if cmds.attributeQuery(ZOO_THICKNESS_ATTR, node=extrudeNode, exists=True):
            return extrudeNode
    return ""


def getExtrudeThickness(obj):
    """Search for the first extrude node found and if it has a ZOO_THICKNESS_ATTR attribute then return it's \
    localTranslateZ

    :param obj: A polygon object
    :type obj: str
    :return thickness: The thickness of the extrudeCenterThickness operation in Maya units, None if not found
    :rtype thickness: float
    """
    extrudeNode = centerThicknessNode(obj, nodeType="polyExtrudeFace")  # look for marked polyExtrudeFace in the inputs
    if not extrudeNode:
        return None, None
    moveVertNode = centerThicknessNode(obj, nodeType="polyMoveVertex")  # look for marked polyExtrudeFace in the inputs
    if not extrudeNode:
        return None, None
    thickness = cmds.getAttr("{}.localTranslateZ".format(extrudeNode))
    weightTransZ = cmds.getAttr("{}.localTranslateZ".format(moveVertNode))
    if weightTransZ:
        weight = 1.0 - (1.0 / (thickness / -weightTransZ))
    else:
        weight = 1.0
    return thickness, weight


def getExtrudeThicknessSelected(message=True):
    """Of selected meshes search for the first extrude node found and if it has a ZOO_THICKNESS_ATTR attribute then \
    return it's localTranslateZ value (thickness)

    :param message: Report the message to the user?
    :type message: bool
    :return thickness: The thickness of the extrudeCenterThickness operation in Maya units, None if not found
    :rtype thickness: float
    """
    meshList = meshObjsSelected()
    if not meshList:
        if message:
            om2.MGlobal.displayWarning("No polygon objects selected, please select a polygon mesh object.")
        return None, None
    return getExtrudeThickness(meshList[0])


def setExtrudeThickness(obj, thickness=1.0, weight=0.5):
    """Sets the center thickness extrude by affecting two nodes, the polyExtrudeFace node and polyMoveVertex.

    Both nodes if a legitimate object with this setup will be marked with the attribute ZOO_THICKNESS_ATTR

    :param obj: The name of the object or face list to extrude
    :type obj: list(str)
    :param thickness: The thickness of the object in Maya units usually cms
    :type thickness: float
    :param weight: Controls the direction of the extrude, 0.5 is center and the extrude will go out each side
    :type weight: float
    :return success: True if completed setting both nodes, False if not
    :rtype success: bool
    """
    # Set the Extrude Node
    extrudeNode = centerThicknessNode(obj, nodeType="polyExtrudeFace")  # look for marked polyExtrudeFace in the inputs
    if extrudeNode:
        cmds.setAttr("{}.localTranslateZ".format(extrudeNode), thickness)
    # Set the PolyMove Node
    polyMoveNode = centerThicknessNode(obj, nodeType="polyMoveVertex")  # look for marked polyMoveVertex in the inputs
    if polyMoveNode:
        moveDistance = (thickness - (thickness * weight)) * -1
        cmds.setAttr("{}.localTranslateZ".format(polyMoveNode), moveDistance)
    if extrudeNode and polyMoveNode:
        return True
    return False


def setExtrudeThicknessSelected(thickness=1.0, weight=0.5, message=True):
    """Sets the center thickness extrude by setting two nodes, the polyExtrudeFace node and polyMoveVertex.

    Based on the selection filters for mesh objects in the selection.

    Both nodes if a legitimate object with this setup will be marked with the attribute ZOO_THICKNESS_ATTR

    :param thickness: The thickness of the object in Maya units usually cms
    :type thickness: float
    :param weight: Controls the direction of the extrude, 0.5 is center and the extrude will go out each side
    :type weight: float
    """
    meshList = meshObjsSelected()
    if not meshList:
        if message:
            om2.MGlobal.displayWarning("No polygon objects selected, please select a polygon mesh object.")
        return
    for obj in meshList:
        setExtrudeThickness(obj, thickness=thickness, weight=weight)


def deleteThickness(obj, message=True):
    """Deletes the thickness setup from an object

    :param obj: The name of the object or face list to extrude
    :type obj: list(str)
    :param message: Report messages to the user
    :type message: bool
    """
    extrudeNode = centerThicknessNode(obj, nodeType="polyExtrudeFace")
    moveVertNode = centerThicknessNode(obj, nodeType="polyMoveVertex")
    if extrudeNode:
        cmds.delete(extrudeNode)
    if moveVertNode:
        cmds.delete(moveVertNode)
    if message:
        if extrudeNode and moveVertNode:
            om2.MGlobal.displayInfo("Thickness deleted: {}".format(obj))
        elif extrudeNode or moveVertNode:
            om2.MGlobal.displayInfo("Thickness partially deleted: {}".format(obj))
        else:
            om2.MGlobal.displayWarning("Thickness not found and could not be deleted: {}".format(obj))


def deleteThicknessSelected(message=True):
    """Deletes the thickness setup from the selected objects

    :param message: Report messages to the user
    :type message: bool
    """
    meshList = meshObjsSelected()
    if not meshList:
        if message:
            om2.MGlobal.displayWarning("No polygon objects selected, please select a polygon mesh object.")
        return
    for obj in meshList:
        deleteThickness(obj, message=message)
