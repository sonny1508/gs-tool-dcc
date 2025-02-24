"""

from zoo.libs.maya.cmds.rig import follicles
follicles.connectFollicleToSelMesh()

"""

from maya import cmds

from zoo.libs.utils import output
from zoo.libs.maya.cmds.objutils import attributes, filtertypes, namehandling


def connectFollicleToShape(shape, follicleShape):
    """Connects a follicle to a new mesh shape node.

    :param shape: A mesh/nurbs shape node
    :type shape: str
    :param follicleShape: a maya hair follicle
    :type follicleShape: str
    """
    attributes.disconnectAttr(follicleShape, "inputMesh")  # will break the connection if connected.
    attributes.disconnectAttr(follicleShape, "inputWorldMatrix")
    cmds.connectAttr("{}.outMesh".format(shape), "{}.inputMesh".format(follicleShape))
    cmds.connectAttr("{}.worldMatrix[0]".format(shape), "{}.inputWorldMatrix".format(follicleShape))


def connectFollicleToSelMesh(message=True):
    """Transfers a follicle onto another mesh.

    Select one or multiple follicles and then the single mesh to transfer to and run.
    """
    selObjs = cmds.ls(selection=True)

    # Do error checks ---------------------------------------------
    if not selObjs:
        if message:
            output.displayWarning("No objects are selected.  Please select follicle/s and then a mesh.")
            return
    if len(selObjs) < 2:
        if message:
            output.displayWarning("Only one object is selected.  Please select follicle/s and then a mesh.")
        return

    # Check for correct node types --------------------------------
    mesh = selObjs[-1]
    meshObjs = filtertypes.filterGeoOnly([mesh])
    if not meshObjs:
        if message:
            output.displayWarning("The last selected object is not a mesh.")
        return
    meshShape = cmds.listRelatives(mesh, shapes=True)[0]
    follicleShapes = filtertypes.filterTypeReturnShapes(selObjs[:-1], children=False, shapeType="follicle")
    if not follicleShapes:
        if message:
            output.displayWarning("First selected objects should be follicles, none found.")
        return

    # Checks passed do the follicle transfer ----------------------
    for f in follicleShapes:
        connectFollicleToShape(meshShape, f)

    if message:
        fShapes = namehandling.getShortNameList(follicleShapes)
        meshShort = namehandling.getShortName(mesh)
        output.displayInfo("Success: Follicles transferred to mesh `{}`, {}.".format(meshShort, fShapes))
