"""

from zoo.libs.maya.cmds.skin import skinreplacejoints
skinreplacejoints.replaceJointsMatrixSuffix(boundText="oldJnt", replaceText="newJnt", prefix=False, message=True)


"""

import maya.cmds as cmds

from zoo.libs.utils import output
from zoo.libs.maya.cmds.objutils import namehandling, connections
from zoo.libs.maya.cmds.skin import bindskin

REPLACE_SKIN_ATTRS = ["worldMatrix", "objectColorRGB", "lockInfluenceWeights", "bindPose", "message"]
SKIN_DEST_TYPES = ["skinCluster", "dagPose"]


def replaceSkinMatrixJoint(boundJoint, replaceJoint, message=True):
    """Swaps the binding of a joint and replaces the bind to another joint.

    Useful while swapping the skinning from one skeleton to another.

    The skinning is swapped based on the matrix positions, so if the joint is in new locations the mesh may move.

    :param boundJoint: The joint with the skinning, to be replaced
    :type boundJoint: str
    :param replaceJoint: The new joint that will receive the skinning
    :type replaceJoint: str
    """
    if not bindskin.getSkinClusterFromJoint(boundJoint):
        if message:
            b = namehandling.getShortName(boundJoint)
            r = namehandling.getShortName(replaceJoint)
            output.displayWarning("The joint `{} >> {}` was skipped as it is not bound to geometry.".format(b, r))
        return

    if not cmds.attributeQuery('lockInfluenceWeights', node=replaceJoint, exists=True):
        cmds.addAttr(replaceJoint, longName='lockInfluenceWeights', attributeType='bool')  # New joints need this attr
    for attr in REPLACE_SKIN_ATTRS:  # "worldMatrix", "objectColorRGB" etc
        connections.swapDriverConnectionAttr(boundJoint, replaceJoint, attr, checkDestNodeTypes=SKIN_DEST_TYPES)


def replaceSkinJointMatrixList(boundJoints, replaceJoints, filterSkinnedJoints=True, message=False):
    """Swaps the binding of a list of joints and replaces the bind to another list of joints.

    Useful while swapping the skinning from one skeleton to another.

    The skinning is swapped based on the matrix positions, so if joints are in new locations the mesh may move.

    :param boundJoints: A list of joints bound to a skin cluster
    :type boundJoints: list(str)
    :param replaceJoints: A list of joints to be switched to connect to the skin cluster
    :type replaceJoints: list(str)
    :param message: Report the message to the user
    :type message: bool
    """
    if filterSkinnedJoints:
        boundJoints = bindskin.filterSkinnedJoints(boundJoints)
        # TODO check not referenced joints
        if not boundJoints:
            return
    for i, boundJnt in enumerate(boundJoints):
        replaceSkinMatrixJoint(boundJnt, replaceJoints[i])
    if message:
        shortNames = namehandling.getShortNameList(replaceJoints)
        output.displayInfo("Skinning transferred to: {}".format(shortNames))


def replaceSkinJoints(obj, old_jnts, new_jnts):
    """Swaps the binding of a list of joints and replaces the bind to another list of joints. (untested)

    Uses maya's cmds.skinPercent("skinCluster1", tmw=[old, new]) to do the transfer

    from
    https://stackoverflow.com/questions/53635659/how-to-transfer-skin-weights-from-one-bone-to-another-via-python
    """
    # Select all vertexes from the mesh
    cmds.select("{}.vtx[*]".format(obj))

    # Use zip to loop through both old and new joints.
    for old_jnt, new_jnt in zip(old_jnts, new_jnts):
        cmds.skinPercent("skinCluster1", tmw=[old_jnt, new_jnt])  # Transfer weights from the old joint to the new one.

    # Clear vertex selection.
    cmds.select(obj, replace=True)


def replaceJointsMatrixSuffix(boundText="oldJnt", replaceText="newJnt", prefix=False, message=True):
    """Swaps the binding of a list of joints and replaces the bind to another list of joints from scene suffix/prefix.

    :param boundText: The suffix/prefix of the existing joints
    :type boundText: str
    :param replaceText: The suffix/prefix of the new joints
    :type replaceText: str
    :param prefix: If True will be the prefix otherwise suffix
    :type prefix: bool
    :param message: Report a message to the user?
    :type message: bool

    :return success: True if the transfer was successful
    :rtype success: bool
    """
    if prefix:
        bndText = str("{}_*".format(boundText))
        rplText = str("{}_*".format(replaceText))
    else:
        bndText = str("*_{}".format(boundText))
        rplText = str("*_{}".format(replaceText))
    boundJoints = sorted(cmds.ls(bndText, type="joint"))
    replaceJoints = sorted(cmds.ls(rplText, type="joint"))

    if not boundJoints or not replaceJoints:  # bail
        insertTxt = "suffix"
        if prefix:
            insertTxt = "prefix"
        if not boundJoints:
            if message:
                output.displayWarning("Skin Transfer Failed: No bind joints found with {}: {}.".format(insertTxt,
                                                                                                       boundText))
            return False
        if not replaceText:
            if message:
                output.displayWarning("Skin Transfer Failed: No replace joints found with {}: {}.".format(insertTxt,
                                                                                                          replaceText))
            return False

    if message:
        for i, jnt in enumerate(boundJoints):
            try:
                output.displayInfo("Skin Transfer: {} >> {}".format(jnt, replaceJoints[i]))
            except:
                pass

    if len(boundJoints) != len(replaceJoints):  # bail
        if message:
            output.displayWarning("Skin Transfer Failed: Uneven joint count in lists, see script editor.")
        return False

    replaceSkinJointMatrixList(boundJoints, replaceJoints, filterSkinnedJoints=False, message=message)

    if message:
        output.displayInfo("Skin Transfer Succeeded: See script editor for matches.")
    return False


def replaceJointsMatrixSel(message=True):
    """Swaps the binding of the first half of selected joints and replaces them with the binding of the second half.

    :param message: Report a message to the user?
    :type message: bool
    """
    selJnts = cmds.ls(selection=True, type="joint")

    if not selJnts:
        output.displayWarning("No joints were selected")
        return False

    if (len(selJnts) % 2) != 0:  # not even
        output.displayWarning("There is an odd number of joints selected, must be even")
        return False

    boundJoints = selJnts[:len(selJnts) // 2]
    replaceJoints = selJnts[len(selJnts) // 2:]

    if message:
        for i, jnt in enumerate(boundJoints):
            try:
                output.displayInfo("Skin Transfer: {} >> {}".format(jnt, replaceJoints[i]))
            except:
                pass

    replaceSkinJointMatrixList(boundJoints, replaceJoints, filterSkinnedJoints=False, message=message)

