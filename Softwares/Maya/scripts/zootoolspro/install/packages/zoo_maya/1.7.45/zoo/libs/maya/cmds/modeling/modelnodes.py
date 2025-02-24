""""Code related to modeling functions in Maya. focusing on modelling nodes. Bevels extrudes etc.

.. code-block:: python

    from zoo.libs.maya.cmds.modeling import modelnodes
    modelnodes.selectModelNodes(nodeType="polyBevel3", returnAllNodes=False, showPopup=True, message=False)

"""

import maya.cmds as cmds
import maya.mel as mel

from zoo.libs.utils import output
from zoo.libs.maya.cmds.objutils import selection


def modelNodes(objs, nodeType="polyBevel3", returnAllNodes=False):
    """Returns modeling nodes, like bevel or extrude nodes attached to the given mesh transforms.

    If returnAllNodes is False, returns the first node type found for each object.

    :param objs: Transform nodes of meshes to search for bevel nodes
    :type objs: list(str)
    :param returnAllNodes: Returns all bevel nodes attached to objs, otherwise returns the first of each object.
    :type returnAllNodes: bool
    :return nodes: All found modelling nodes, empty list if None. Eg a list of bevel node names.
    :rtype: list(str)
    """
    nodes = list()
    for obj in objs:
        shapeNodes = cmds.listRelatives(obj, fullPath=True, shapes=True, type="mesh")
        if not shapeNodes:
            continue
        newBevNodes = cmds.listConnections(shapeNodes[0], source=True, type=nodeType)
        if not newBevNodes:
            continue
        if len(newBevNodes) > 1 and not returnAllNodes:
            nodes.append(newBevNodes[0])  # appends the first node in the history, these are most recent.
        else:
            nodes += list(set(newBevNodes))  # order doesn't matter, so remove duplicates and add
    return nodes


def selectModelNodes(meshTransforms, nodeType="polyBevel3", returnAllNodes=False, showPopup=True, message=False):
    """Select all modelling nodes (example bevel or extrude) attached to mesh transforms

    If returnAllNodes is False, returns the first model node found for each object.
    If showPopup is True, shows the manipulator popup window with node information if the nodes are found.

    :param meshTransforms: meshTransforms to search for the modeling nodes, eg bevel nodes.
    :type meshTransforms: bool
    :param nodeType: the node type to look for eg "polyBevel3" are the bevel nodes.
    :type nodeType: str
    :param returnAllNodes: Returns all model nodes attached to objs, otherwise returns the first of each object.
    :type returnAllNodes: bool
    :param showPopup: Shows the manipulator popup window with model node information if the nodes are found.
    :type showPopup: bool
    :param message: Show messages to the user?
    :type message: bool
    :return success: True if successful
    :rtype: bool
    """
    nodes = modelNodes(meshTransforms, nodeType=nodeType, returnAllNodes=returnAllNodes)
    if not nodes:
        if message:
            output.displayWarning("No {} nodes found related to the current selection.".format(nodeType))
        return False, nodes

    cmds.select(nodes, add=True)

    if showPopup:
        mel.eval('setToolTo ShowManips')
    return True, nodes


def selectModelNodesSel(nodeType="polyBevel3", returnAllNodes=False, showPopup=True, message=False):
    """Select all modelling nodes (example type polyBevel3) attached to the current selection, uses mesh transform selection.

    If returnAllNodes is False, returns the first model node found for each object.
    If showPopup is True, shows the manipulator popup window with bevel information if bevels are found.

    :param nodeType: the node type to look for eg "polyBevel3" are the bevel nodes.
    :type nodeType: str
    :param returnAllNodes: Returns all bevel nodes attached to objs, otherwise returns the first of each object.
    :type returnAllNodes: bool
    :param showPopup: Shows the manipulator popup window with model node information if node is found.
    :type showPopup: bool
    :param message: Show messages to the user?
    :type message: bool
    :return success: True if successful
    :rtype: bool
    """
    selectedObjs = cmds.ls(selection=True)
    if not selection.meshSelectionWarning(selectedObjs):  # checks if the selection is a mesh or component selection
        return  # error message already displayed
    return selectModelNodes(selectedObjs, nodeType=nodeType, returnAllNodes=returnAllNodes, showPopup=showPopup,
                            message=message)


def prepCreate():
    """Prepares the selection for the create bevel or extrude functions.
    Gets selected objects and checks component selection.

    :return:
    :rtype: tuple(list(str), bool, str)
    """
    selectedObjs = cmds.ls(selection=True)
    if not selectedObjs:
        output.displayWarning("Please select an object/s.")
        return False, None, None
    mode = selection.componentOrObject(selectedObjs)  # returns "object", "component", "uv" or None
    if not selection.meshSelectionWarning(selectedObjs):  # checks if the selection is a mesh or component selection
        return False, mode  # error message already displayed
    return selectedObjs, True, mode


def selectPostCreateNodes(selectedObjs, mode, nodeType="polyBevel3"):
    """Select the newly created bevel or extrude nodes after creation.
    Show a popup if showPopup window so all can be edited.

    :param selectedObjs: The selected nodes as strings.  Should be mesh transform nodes.
    :type selectedObjs: list(str)
    :param mode:
    :type mode: str
    :param nodeType: The type of node to search for bevel extrude etc. Bevel nodes are "polyBevel3"
    :type nodeType: str
    :return: successfully completed or not?
    :rtype: bool
    """

    objs = selectedObjs
    if mode == "component":  # Then is a component selection, so convert to objs to find shapes.
        objs = selection.componentsToObjectList(selectedObjs)  # Get the objects from component selection.

    # select the bevel nodes.
    success = selectModelNodes(objs, returnAllNodes=False, nodeType=nodeType, showPopup=True, message=False)
    return success


def createBevel(chamfer=True, segments=1, message=True):
    """Creates a bevel/chamfer based on the selection according to Maya UI settings and the mel

    .. code-block:: mel

        performBevelOrChamfer;

    Select the newly created bevel nodes after creation and show a popup if showPopup window so all can be edited.

    :param chamfer: Chamfer the object (bevel) False will add loops but not bevel.
    :type chamfer: bool
    :param segments: The amount of segments affects roundness
    :type segments: int
    :param message: Show messages to the user?
    :type message: bool
    """
    selectedObjs, success, mode = prepCreate()
    if not success:
        return

    mel.eval("performBevelOrChamfer;")  # Does the bevel according to Maya UI settings.

    finalSuccess, nodes = selectPostCreateNodes(selectedObjs, mode, nodeType="polyBevel3")

    for node in nodes:
        cmds.setAttr("{}.segments".format(node), segments)
        cmds.setAttr("{}.chamfer".format(node), chamfer)

    if finalSuccess and message:
        output.displayInfo("Success: Bevel/chamfer created.")


def createExtrude(message=True):
    """Creates an extrude based on the selection according to Maya UI settings and the mel

    .. code-block:: mel

        performPolyExtrude 0;

    Select the newly created bevel nodes after creation and show a popup if showPopup window so all can be edited.

    :param message: Show messages to the user?
    :type message: bool
    """
    selectedObjs, success, mode = prepCreate()
    if not success:
        return

    mel.eval("performPolyExtrude 0;")  # Does the extrude according to Maya UI settings.

    finalSuccess, nodes = selectPostCreateNodes(selectedObjs, mode, nodeType="polyExtrudeFace")

    if finalSuccess and message:
        output.displayInfo("Success: Extrude created.")
