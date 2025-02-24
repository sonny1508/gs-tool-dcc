"""Constraint related code.

Example use:

.. code-block:: python

    from zoo.libs.maya.cmds.objutils import constraints
    constraints.constrainMatchList()

Author: Andrew Silke

"""

import maya.cmds as cmds

from zoo.libs.utils import output
from zoo.libs.maya.cmds.objutils import filtertypes, attributes
from zoovendor import six
from zoo.core.util import classtypes

POS_ROT_ATTRS = attributes.MAYA_TRANSLATE_ATTRS + attributes.MAYA_ROTATE_ATTRS

MOPATH_PATH_ATTR = "path"
MOPATH_FRONTTWIST_ATTR = "frontTwist"
MOPATH_UPTWIST_ATTR = "upTwist"
MOPATH_SIDETWIST_ATTR = "sideTwist"

"""
DELETE CONSTRAINTS 
"""


def deleteConstraintsFromObjList(objList, message=True):
    """Deletes any constraints attached to any object in an object list

    :param objList: list of maya objects or nodes
    :type objList: list
    :param message: report the message to the user?
    :type message: bool
    :return constrainList: the constraints deleted, will be empty list if none found
    :rtype constrainList: list(str)
    """
    constrainList = cmds.listRelatives(objList, children=True, type="constraint", allDescendents=False)
    if not constrainList:
        output.displayWarning("No constraints found attached to these objects")
        return list()
    cmds.delete(list(set(constrainList)))
    if message:
        output.displayInfo("Success: Deleted constraints: {}".format(", ".join(constrainList)))
    return constrainList


def deleteConstraintsFromSelObj(message=True):
    """Deletes any constraints attached to any object from the current selection

    :param message: report the message to the user?
    :type message: bool
    :return constrainList: the constraints deleted, will be empty list if none found
    :rtype constrainList: list(str)
    """
    selObj = cmds.ls(selection=True)
    constrainList = deleteConstraintsFromObjList(selObj, message=message)
    return constrainList


def selectConstraints():
    """Selects all constraints connected to the selected objects."""
    selObjs = cmds.ls(selection=True)
    if not selObjs:
        output.displayWarning("Nothing is selected, please select objects with constraints.")
        return
    constrainList = cmds.listConnections(selObjs, t="constraint")
    constrainList = list(set(constrainList))  # remove duplicates
    if not constrainList:
        output.displayWarning("No constraints found attached to these objects")
        return
    cmds.select(constrainList, replace=True)
    output.displayInfo("Constraints selected {}".format(constrainList))


"""
BATCH SURFACE CONSTRAINT 
"""


def constrainObjsToSurface(surface, objs, deleteConstraint=True):
    """Constrains an object list to a surface with surface constraints.

    If deleteConstraint is True acts as a snap for objects, snaps pivot points.

    :param surface: A mesh or nubsSurface object
    :type surface: str
    :param objs: A list of objects to constrain/snap
    :type objs: list(str)
    :param deleteConstraint: Delete the constraints after created?  If True is a snap function.
    :type deleteConstraint: bool

    :return constraintList: A list of constraint nodes if created, otherwise will be an empty list.
    :rtype constraintList: list(str)
    """
    constraintList = list()
    for obj in objs:
        constraint = cmds.geometryConstraint(surface, obj)
        if deleteConstraint:
            cmds.delete(constraint)
        else:
            constraintList.append(constraint)
    return constraintList


def constrainObjsToSurfaceSelection(surface="", deleteConstraint=True):
    """Constrains selected objects to a surface with surface constraints.

    If no surface object is given the surface object will be the last in the selection list.

    If deleteConstraint is True acts as a snap for objects, snaps pivot points.

    :param surface: A mesh or nubsSurface object
    :type surface: str
    :param deleteConstraint: Delete the constraints after created?  If True is a snap function.
    :type deleteConstraint: bool

    :return constraintList: A list of constraint nodes if created, otherwise will be an empty list.
    :rtype constraintList: list(str)
    """
    if surface:
        if not cmds.objExists(surface):
            output.displayWarning("The surface object {} not found in the scene".format(surface))
            return
    selObjs = cmds.ls(selection=True, transforms=True)
    if not selObjs:
        output.displayWarning("Please select objects to snap to surface")
        return
    if not surface:  # then use the last object
        surface = selObjs[-1]
        selObjs.pop(-1)
    return constrainObjsToSurface(surface, selObjs, deleteConstraint=deleteConstraint)


def setSurfaceObj():
    """Returns the surface object for UI code. Must be a mesh or nurbsSurface object.

    :return surfaceObject: The first selected mesh or nurbsSurface object.
    :rtype surfaceObject: str
    """
    selObjs = cmds.ls(selection=True, transforms=True)
    if not selObjs:
        output.displayWarning("Nothing selected. Please select a geometry object.")
        return list()
    for obj in selObjs:
        if filtertypes.shapeTypeFromTransformOrShape([obj], shapeType="mesh"):
            return obj
        if filtertypes.shapeTypeFromTransformOrShape([obj], shapeType="nurbsSurface"):
            return obj
    output.displayWarning("Geometry object not found in selection, please select a mesh or nurbsSurface")
    return list()


def constrainMatchList(prefix="SCXX", message=True):
    """Constrains one object to another with prefixing, object to be constrained is prefixed

    Prefix is constrained to non prefix:

        "SCXX_head" is constrained to "head"

    :param prefix: The prefix of the objects to search for their counter parts
    :type prefix: str
    :param message: Report a message to the user?
    :type message: bool
    """
    joints = cmds.ls("{}_*".format(prefix), transforms=True)
    for jnt in joints:
        if not cmds.objectType(jnt) == "joint":
            continue
        masterJnt = jnt.replace("{}_".format(prefix), "")
        cmds.parentConstraint(masterJnt, jnt, maintainOffset=False)
        cmds.scaleConstraint(masterJnt, jnt, maintainOffset=False)
        if message:
            output.displayInfo("Constrained: {} is constrained to {}".format(jnt, masterJnt))


@six.add_metaclass(classtypes.Singleton)
class ZooConstraintsTrackerSingleton(object):
    """Used by the animation marking menu & UI, tracks data for animation between UIs and marking menus.
    """

    def __init__(self):
        # Marking Menu ----------------
        self.markingMenuTriggered = False
        self.markingMenuMoShapes = None
