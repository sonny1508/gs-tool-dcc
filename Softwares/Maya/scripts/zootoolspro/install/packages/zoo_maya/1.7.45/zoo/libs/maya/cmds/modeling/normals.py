
from maya import cmds
from zoo.libs.utils import output
from zoo.libs.maya.cmds.objutils import filtertypes

def transferVertexNormals(sourceObj, objects, space="world"):
    """

    :param sourceObj: The object to transfer the vertex normals from
    :type sourceObj: str
    :param objects: The objects to transfer the vertex normals to
    :type objects: list(str)
    :param space: The space to transfer the vertex normals in.  Valid values are "world", "local", "uv", "component"
    :type space: str
    :return:
    :rtype:
    """
    if space == "world":
        sampleSpace = 0
    elif space == "local":
        sampleSpace = 1
    elif space == "uv":
        sampleSpace = 4
    elif space == "component":
        sampleSpace = 5
    for obj in objects:
        cmds.transferAttributes(sourceObj, obj, transferNormals=True,
                                transferUVs=0,
                                transferColors=0,
                                transferPositions=0,
                                sampleSpace=sampleSpace)

def transferVertexNormalsSel(space="world"):
    """ Transfers vertex normals from the first selected object to the rest of the selected objects.

    :param space:
    :type space:
    :return:
    :rtype:
    """
    sel = cmds.ls(selection=True, long=True)
    if not sel:
        output.displayWarning("Please select a source object and then the objects to transfer to.")
        return
    meshes = filtertypes.filterTypeReturnTransforms(sel, shapeType="mesh")
    if not meshes or len(meshes) < 2:
        output.displayWarning("Please select a source mesh and then the meshes to transfer to.")
        return
    sourceObj = meshes[0]
    objects = meshes[1:]
    transferVertexNormals(sourceObj, objects, space=space)

