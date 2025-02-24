"""cmds functions related to Offset Parent Matrix in Maya 2020 and above.

Example use:

.. code-block:: python

    from zoo.libs.maya.cmds.objutils import matrix

Author: Andrew Silke

"""
from maya import cmds

from zoo.libs.maya import zapi

from zoo.libs.maya.cmds.objutils import attributes
from zoo.libs.utils import output
from zoo.libs.maya.utils import mayaenv

MAYA_VERSION = float(mayaenv.mayaVersionNiceName())
DEFAULT_MATRIX = [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0]


def hasMatrixOffset(transform):
    """Checks to see if a transforms Offset Parent Matrix (Composition) has been modified at all.

    Attribute: offsetParentMatrix

    :param transform: A maya transform node
    :type transform: str
    :return hasOffset: True if there is an offset, False if no offset
    :rtype hasOffset: bool
    """
    if cmds.getAttr("{}.offsetParentMatrix".format(transform)) == DEFAULT_MATRIX:  # no need to do anything
        return False
    return True


def selectionMatrixCheck(message=True):
    if MAYA_VERSION <= 2020.0:
        if message:
            output.displayWarning("The Offset Matrix settings are only in Maya 2020 and above. \n"
                                  "You will need to upgrade to use this tool.")
        return list()
    selObjs = cmds.ls(selection=True, type="transform")
    if not selObjs:
        if message:
            output.displayWarning("No transform objects are selected, please select an object/s")
        return list()
    return selObjs


# -----------------------
# Zero/Reset Matrix Offset
# -----------------------


def zeroMatrixOffset(transform, unlockAttrs=True):
    """Resets/zeros the Offset Parent Matrix (Composition) ".offsetParentMatrix" attr of a single object.
    Maintains the current position/rotation/scale.

    :param transform: A maya transform node
    :type transform: str
    :param unlockAttrs: If True will unlock/del keys/disconnect any connected SRT attributes
    :type unlockAttrs: str
    """
    if not hasMatrixOffset(transform):
        return
    if unlockAttrs:  # Unlocks/del keys/disconnects any connected SRT attributes
        attributes.unlockDisconnectSRT(transform)
    matrixTRS = cmds.xform(transform, q=True, matrix=True, worldSpace=True)
    cmds.setAttr("{}.offsetParentMatrix".format(transform), DEFAULT_MATRIX, type="matrix")
    cmds.xform(transform, matrix=matrixTRS, worldSpace=True)


def resetMatrixOffsetList(transformList, unlockAttrs=True):
    """Resets/zeros the Offset Parent Matrix (Composition) ".offsetParentMatrix" attr of a list of objects.
    Maintains the current position/rotation/scale.

    :param transformList: A list of A maya transform node names
    :type transformList: list(str)
    :param unlockAttrs: If True will unlock/del keys/disconnect any connected SRT attributes
    :type unlockAttrs: str
    """
    for transform in transformList:
        zeroMatrixOffset(transform, unlockAttrs=unlockAttrs)


def zeroMatrixOffsetSel(unlockAttrs=True, children=False, nodeType=None, message=True):
    """Resets/zeros the Offset Parent Matrix (Composition) ".offsetParentMatrix" attr of the selected objects.
    Maintains the current position/rotation/scale.

    :param unlockAttrs: If True will unlock/del keys/disconnect any connected SRT attributes
    :type unlockAttrs: str
    :param children: If True will also reset the children of the selected objects
    :type children: bool
    :param nodeType: If children is True will only reset the children of the selected objects of this nodeType
    :type nodeType: str
    :param message: report a message to the user?
    :type message: bool
    """
    selObjs = selectionMatrixCheck(message=message)
    if not selObjs:  # message already given
        return
    if children:
        selObjs = childrenByNodeType(selObjs, nodeType=nodeType)
    resetMatrixOffsetList(selObjs, unlockAttrs=unlockAttrs)
    if message:
        output.displayInfo("The Offset Matrix of the selected objects has been reset to zero.")


# -----------------------
# SRT to Matrix Offset And Back
# -----------------------
def childrenByNodeType(objList, nodeType="transform"):
    """retrieves all objs under the obj list in the hierarchy, all child joints

    :param objList: a list of Maya objects DAG nodes
    :type objList: list(str)
    :return allObjs: an obj list now including children
    :rtype allObjs: list(str)
    """
    allJoints = list()
    for obj in objList:
        allJoints.append(obj)
        if type:
            tempJntList = cmds.listRelatives(obj, allDescendents=True, type=nodeType, fullPath=True)
        else:
            tempJntList = cmds.listRelatives(obj, allDescendents=True, fullPath=True)
        if tempJntList:
            allJoints += tempJntList
    return list(set(allJoints))  # remove duplicates


def srtToMatrixOffset(transform, unlockAttrs=True):
    """Sets the transforms translate, rotate to be zero and the scale to be one and passes the information into \
    the Offset Parent Matrix (Composition) ".offsetParentMatrix" attr
    For a single transform
    Maintains the current position/rotation/scale.

    # TODO could possibly be done by simple math on the scale/rot/trans values not sure

    :param transform: A maya transform node
    :type transform: str
    :param unlockAttrs: If True will unlock/del keys/disconnect any connected SRT attributes
    :type unlockAttrs: str
    """
    if attributes.srtIsZeroed(transform):  # already frozen so bail
        return
    if unlockAttrs:  # Unlocks/del keys/disconnects any connected SRT attributes
        attributes.unlockDisconnectSRT(transform)
    if hasMatrixOffset(transform):  # if offset already then zero offsetParentMatrix values
        matrixTRS = cmds.xform(transform, q=True, matrix=True, worldSpace=True)
        cmds.setAttr("{}.offsetParentMatrix".format(transform), DEFAULT_MATRIX, type="matrix")
        cmds.xform(transform, matrix=matrixTRS, worldSpace=True)
    # Now switch vales back to the offsetParentMatrix
    matrixTRS = cmds.xform(transform, q=True, matrix=True, worldSpace=False)
    attributes.resetTransformAttributes(transform)  # zero SRT
    cmds.setAttr("{}.offsetParentMatrix".format(transform), matrixTRS, type="matrix")
    if cmds.objectType(transform) == "joint":
        cmds.setAttr("{}.jointOrient".format(transform), 0.0, 0.0, 0.0, type="float3")


def srtToMatrixOffsetList(transformList, unlockAttrs=True):
    """Sets the transforms translate, rotate to be zero and the scale to be one and passes the information into \
    the Offset Parent Matrix (Composition) ".offsetParentMatrix" attr
    For a list of tranforms
    Maintains the current position/rotation/scale.

    :param transformList: A list of A maya transform node names
    :type transformList: list(str)
    :param unlockAttrs: If True will unlock/del keys/disconnect any connected SRT attributes
    :type unlockAttrs: str
    """
    for transform in transformList:
        srtToMatrixOffset(transform, unlockAttrs=unlockAttrs)


def srtToMatrixOffsetSel(unlockAttrs=True, children=False, nodeType=None, message=True):
    """Sets the transforms translate, rotate to be zero and the scale to be one and passes the information into \
    the Offset Parent Matrix (Composition) ".offsetParentMatrix" attr
    For a the selected transforms
    Maintains the current position/rotation/scale.


    :param unlockAttrs: If True will unlock/del keys/disconnect any connected SRT attributes
    :type unlockAttrs: str
    :param children: If True will also reset the children of the selected objects
    :type children: bool
    :param nodeType: If children is True will only reset the children of the selected objects of this nodeType
    :type nodeType: str
    :param message: report a message to the user?
    :type message: bool
    """
    selObjs = selectionMatrixCheck(message=message)
    if not selObjs:  # message already given
        return
    if children:
        selObjs = childrenByNodeType(selObjs, nodeType=nodeType)
    srtToMatrixOffsetList(selObjs, unlockAttrs=unlockAttrs)
    if message:
        output.displayInfo("The Offset Matrix is now handling the selected objects offsets. "
                           "Translate, rotate and scale have been zeroed")


# -----------------------
# Zero SRT Model Matrix Offset
# -----------------------


def zeroSrtModelMatrix(transform, unlockAttrs=True):
    """Modeller Matrix Zero SRT, this will zero SRT and move offsets to the offsetParentMatrix but will freeze \
    transforms for scale so the object can be rotated nicely.

    # TODO record the scale values so the freeze can be undone?

    :param transform: A maya transform node name
    :type transform: str
    :param unlockAttrs: If True will unlock/del keys/disconnect any connected SRT attributes
    :type unlockAttrs: str
    """

    if attributes.srtIsZeroed(transform):  # already frozen so bail
        return
    if unlockAttrs:  # Unlocks/del keys/disconnects any connected SRT attributes
        attributes.unlockDisconnectSRT(transform)

    matrixTRS = cmds.xform(transform, q=True, matrix=True, worldSpace=True)

    # Zero the scale of the matrix ------------------
    node = zapi.nodeByName(transform)
    offsetTransform = zapi.TransformationMatrix(node.offsetParentMatrix.value())
    offsetTransform.setScale((1.0, 1.0, 1.0), zapi.kWorldSpace)
    cmds.setAttr("{}.offsetParentMatrix".format(transform), offsetTransform.asMatrix(), type="matrix")

    # return object to original position.
    cmds.xform(transform, matrix=matrixTRS, worldSpace=True)

    curScale = cmds.getAttr("{}.scale".format(transform))[0]
    cmds.setAttr("{}.scale".format(transform), 1.0, 1.0, 1.0, type="float3")

    # now move all values to the offset matrix
    srtToMatrixOffset(transform)

    # return the scale values and freeze scale
    cmds.setAttr("{}.scale".format(transform), curScale[0], curScale[1], curScale[2], type="float3")
    cmds.makeIdentity(transform, apply=True, translate=False, rotate=False, scale=True, normal=2)  # freeze scale


def zeroSrtModelMatrixList(transformList, unlockAttrs=True):
    """Modeller Matrix Zero SRT, this will zero SRT and move offsets to the offsetParentMatrix but will freeze \
    transforms for any scale so the object can be rotated nicely.

    Works on a list of transforms.

    :param transformList: A list of A maya transform node names
    :type transformList: list(str)
    :param unlockAttrs: If True will unlock/del keys/disconnect any connected SRT attributes
    :type unlockAttrs: str
    """
    for transform in transformList:
        zeroSrtModelMatrix(transform, unlockAttrs=unlockAttrs)


def zeroSrtModelMatrixSel(unlockAttrs=True, children=False, nodeType=None, message=True):
    """Modeller Matrix Zero SRT, this will zero SRT and move offsets to the offsetParentMatrix but will freeze \
    transforms for any scale so the object can be rotated nicely.

    Works on selected transform objects.

    :param unlockAttrs: If True will unlock/del keys/disconnect any connected SRT attributes
    :type unlockAttrs: str
    :param children: If True will also reset the children of the selected objects
    :type children: bool
    :param nodeType: If children is True will only reset the children of the selected objects of this nodeType
    :type nodeType: str
    :param message: report a message to the user?
    :type message: bool
    """
    selObjs = selectionMatrixCheck(message=message)
    if not selObjs:  # message already given
        return
    if children:
        selObjs = childrenByNodeType(selObjs, nodeType=nodeType)
    zeroSrtModelMatrixList(selObjs, unlockAttrs=unlockAttrs)
    if message:
        output.displayInfo("The Offset Matrix is now handling the selected objects translation and rotation offsets. "
                           "Translate, rotate have been zeroed and scale has been frozen.")
