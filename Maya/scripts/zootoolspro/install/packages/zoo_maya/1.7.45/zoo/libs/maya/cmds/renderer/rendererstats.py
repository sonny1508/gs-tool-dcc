""" ---------- Render Stats -------------
Enables the user to easily toggle the following modes for render visibility

Example:

    from zoo.libs.maya.cmds.renderer import renderstats
    renderstats.renderStatsSel(vis=False, attr=RS_PRIMARY_VIS)


TODO: Add renderer specific attributes

Author:  Andrew Silke
"""

from maya import cmds
from zoo.libs.utils import output
from zoo.libs.maya.cmds.objutils import filtertypes, namehandling

RS_PRIMARY_VIS = "primaryVisibility"
RS_CASTS_SHADOWS = "castsShadows"
RE_RECEIVE_SHADOWS = "receiveShadows"
RS_HOLDOUT = "holdOut"
RS_MOTION_BLUR = "motionBlur"
RS_REFLECTION_VIS = "visibleInReflections"
RS_REFRACTION_VIS = "visibleInRefractions"
RS_DOUBLE_SIDED = "doubleSided"
RS_OPPOSITE = "opposite"


def renderStats(shapeList, vis=False, attr=RS_PRIMARY_VIS, message=True):
    """Sets an attribute to be true or false, used for setting Render Stats though could be used for anything

    see globals for attrs to set

    :param shapeList: A list of nurbsSurface or mesh shapes
    :type shapeList: list(str)
    :param vis: State to set, True/False
    :type vis: bool
    :param attr: The attribute to set
    :type attr: str
    :param message: Report a message to the user?
    :type message: bool
    """
    for shape in shapeList:
        cmds.setAttr(".".join([shape, attr]), vis)
    if message:
        shortNames = namehandling.getShortNameList(shapeList)
        output.displayInfo("{} set {}: `{}`".format(attr, vis, shortNames))


def renderStatsSel(vis=False, attr=RS_PRIMARY_VIS, message=True):
    """Sets an render stat attribute to be true or false, see globals for attrs to set.

    :param vis: State to set, True/False
    :type vis: bool
    :param attr: The attribute to set
    :type attr: str
    :param message: Report a message to the user?
    :type message: bool
    """
    selGeo = cmds.ls(selection=True, geometry=True)
    selTransforms = cmds.ls(selection=True, transforms=True)
    if selTransforms:
        selGeo += filtertypes.filterTypeReturnShapes(selTransforms, children=False, shapeType="mesh")
        selGeo += filtertypes.filterTypeReturnShapes(selTransforms, children=False, shapeType="nurbsSurface")
    if not selGeo:
        output.displayWarning("Please select geometry.")
        return
    renderStats(selGeo, vis=vis, attr=attr, message=message)
