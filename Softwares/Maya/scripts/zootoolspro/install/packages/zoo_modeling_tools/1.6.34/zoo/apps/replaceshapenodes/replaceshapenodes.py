
from zoo.core.util import env
if env.isMaya(): # todo: remove this
    from maya import cmds

    from zoo.libs.maya.cmds.objutils import shapenodes, filtertypes
    from zoo.libs.maya.cmds.shaders import shaderutils


def shapeNodeParentSelected(masterObj="", replace=False, message=True, selectLastObj=True, deleteMaster=True,
                            objSpaceParent=False, instance=False, keepShaders=False):
    """Shape parents from a selection and optional UI master object.  Various options.

    Optional masterObj from a UI, if this is an empty string then uses the first object as the masterObj

    Can keep shaders, uses only the first shader found, only supports geo

    The parent object is the last obj in objectList and is returned, all other objects are shape parented and removed
    If deleteOriginal then the combine works more like a replace where the last object is over-ridden by the new shapes
    Otherwise default `replace=False` works as `combine curves`

    :param masterObj: Optional master object, if this is an empty string then uses the first object as the masterObj
    :type masterObj: str
    :param replace: delete the shape nodes of the last selected object
    :type replace: bool
    :param message: report the success message to Maya
    :type message: bool
    :param selectLastObj: Will select the remaining object after finishing
    :type selectLastObj: bool
    :param deleteMaster: Deletes the master object from the scene
    :type deleteMaster: bool
    :param objSpaceParent: If False tries to preserve postion of the parent in world space
    :type objSpaceParent: bool
    :param instance: If True will instance if duplicating the shape node
    :type instance: bool
    :param keepShaders: Will attempt to keep shaders, uses only the first shader found, only supports geo
    :type keepShaders: bool
    """
    shaderObjs = list()
    shaderList = list()
    if keepShaders:
        selObjs = cmds.ls(selection=True, long=True)
        if not masterObj and selObjs:
            del selObjs[0]
        nurbs = filtertypes.filterTypeReturnTransforms(selObjs, children=False, shapeType="nurbsSurface")
        meshes = filtertypes.filterTypeReturnTransforms(selObjs, children=False, shapeType="mesh")
        shaderObjs = nurbs + meshes
        # Record the first found shaders
        for obj in shaderObjs:  # find the first shader
            shaders = shaderutils.getShadersObjList([obj])
            if shaders:
                shaderList.append(shaders[0])
            else:
                shaderList.append("")

    # Replace the shape nodes -------------------------------------
    objs = shapenodes.shapeNodeParentSelected(masterObj=masterObj, replace=replace, message=message,
                                              selectLastObj=selectLastObj, deleteMaster=deleteMaster,
                                              objSpaceParent=objSpaceParent, instance=instance)

    # Keep shaders ------------------------------
    if keepShaders and objs:
        for i, obj in enumerate(shaderObjs):
            if shaderList[i]:
                shaderutils.assignShader([obj], shaderList[i])
