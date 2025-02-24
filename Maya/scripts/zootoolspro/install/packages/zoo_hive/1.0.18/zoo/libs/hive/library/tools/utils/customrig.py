"""Module for adding user made custom rigs to Hive.  Creates a group that you can parent custom rigs to.

Example use:

.. code-block:: python

    # Select a Hive joint a run, builds a group that you can parent custom rigs to.
    from zoo.libs.hive.library.tools.utils import customrig
    customrig.parentGrpToHiveJointSel()

    # Select a custom rig to delete, will also delete the target group.
    from zoo.libs.hive.library.tools.utils import customrig
    customrig.deleteCustomRigGrpSel()

"""

from maya import cmds

from zoo.libs.utils import output
from zoo.libs.maya.cmds.objutils import namehandling


def parentGrpToHiveJoint(hiveJoint):
    """Builds two groups, one that you can parent custom rigs to and one that is parented to the Hive joint.

        customRigGrp: This is the group that you can parent custom rigs to.
        constraintTarget: This is the group that the customRigGrp is constrained to, parented to the Hivejoint.

    :param hiveJoint: A single Hive joint name
    :type hiveJoint: str
    :return: The customRigGrp and constrainToGrp as string names
    :rtype: tuple(str, str)
    """
    # create groups
    nameTarget = namehandling.generateUniqueName("{}_customTarget".format(hiveJoint))
    nameRigGrp = namehandling.generateUniqueName("{}_customGrp".format(hiveJoint))
    constraintTarget = cmds.group(empty=True, name=nameTarget, parent=hiveJoint)
    customRigGrp = cmds.group(empty=True, name=nameRigGrp.format(hiveJoint))
    # constraints
    cmds.parentConstraint(constraintTarget, customRigGrp, maintainOffset=False)
    cmds.scaleConstraint(constraintTarget, customRigGrp, maintainOffset=True)
    # add message attrs for future deletion on either node
    cmds.addAttr(customRigGrp, longName="targetObj", attributeType="message")
    cmds.connectAttr("{}.message".format(constraintTarget), "{}.targetObj".format(customRigGrp))
    cmds.addAttr(constraintTarget, longName="targetObj", attributeType="message")
    cmds.connectAttr("{}.message".format(customRigGrp), "{}.targetObj".format(constraintTarget))
    # message
    output.displayInfo("Created custom rig group for joint {}".format(hiveJoint))
    return customRigGrp, constraintTarget


def parentGrpToHiveJointSel():
    """Creates a group or many groups that you can parent custom rigs to Hive.

    Builds two groups, one that you can parent custom rigs to and one that is parented to the selected Hive joint.

        customRigGrp: This is the group that you can parent custom rigs to.
        constrainToGrp: This is the group that the customRigGrp is constrained to, parented to the Hivejoint.

    :return: The customRigGrp and constrainToGrp as string names
    :rtype: tuple(str, str)
    """
    selJoints = cmds.ls(selection=True, type="joint")
    if not selJoints:
        output.displayWarning("Please select a Hive joint.")
        return
    for jnt in selJoints:
        parentGrpToHiveJoint(jnt)


def deleteCustomRigGrp(customRigGroup):
    """Deletes the customRigGrp and the constraintTarget grp if they exist and are valid

    :param customRigGroup: A maya group with the attribute "targetObj" connected to the constraintTarget group
    :type customRigGroup: str
    :return: Returns the names of the deleted groups, if not found are empty strings.
    :rtype: tuple(str, str)
    """
    if not cmds.attributeQuery("targetObj", node=customRigGroup, exists=True):
        output.displayWarning("{} is not a custom rig group, skipping.".format(customRigGroup))
        return "", ""
    targetObjs = cmds.listConnections("{}.targetObj".format(customRigGroup), source=True, destination=False)
    if targetObjs:
        cmds.delete([targetObjs[0], customRigGroup])
        output.displayInfo("Deleted custom rig group {} and its target {}".format(customRigGroup, targetObjs[0]))
        return customRigGroup, targetObjs[0]
    cmds.delete(customRigGroup)
    output.displayWarning("Deleted custom rig group {}, its target was not found".format(customRigGroup))
    return customRigGroup, ""


def deleteCustomRigGrpSel():
    """Deletes the customRigGrp and constrainToGrp if they exist.

    Can have multiple selected"""
    sel = cmds.ls(selection=True)
    if not sel:
        output.displayWarning("Please select a customRigGroup.")
        return False
    for node in sel:
        deleteCustomRigGrp(node)
