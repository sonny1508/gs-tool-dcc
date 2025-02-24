"""
Creates and toggles parenting of groups containing '_zooParentToRig' into and out of _zooParentToRig
Based on first object being in world or not
"""

import maya.cmds as cmds
import maya.api.OpenMaya as om2

from zoo.libs.maya.cmds.objutils import namewildcards, namehandling

REPARENT_SUFFIX = "_zooParentToRig"


# ---------------------------------------------
# CREATE GRP
# ---------------------------------------------


def createGroupToRig(parentName, wildcardSuffix=REPARENT_SUFFIX, matchObject=True, message=True):
    """Creates a group with the name of a unique parentName short name and the wildcard suffix.
    Will match the new group to the parent.

    Creates and matches new group:

        "parentName_zooParentToRig"

    :param parentName: The short name name of the parent obj, will create "parentName_zooParentToRig"
    :type parentName: str
    :param wildcardSuffix: The suffix of the group name, needs this name for toggling
    :type wildcardSuffix: str
    :param matchObject: If True then match the objects only if parenting
    :type matchObject: bool
    :param message: Report the success message to the user?
    :type message: bool
    :return groupName: The name of the group that was created
    :rtype groupName: str
    """
    groupName = "".join([parentName, wildcardSuffix])
    if cmds.objExists(groupName):
        om2.MGlobal.displayWarning('The grp `{}` already exists'.format(groupName))
        return ""
    groupName = cmds.group(name=groupName, empty=True)
    if matchObject:  # Match group to selected object
        cmds.matchTransform(([groupName, parentName]), pos=True, rot=True, scl=False, piv=False)
    cmds.select(groupName, replace=True)  # Select new group
    if message:
        om2.MGlobal.displayInfo("Success: `{}` created".format(groupName))
    return groupName


def createGroupToRigSelected(wildcardSuffix=REPARENT_SUFFIX, matchObject=True, message=True):
    """Creates a group with the name of the selected obj and the wildcard suffix.
    Will match the new group to the parent. Only one object should be selected and must be a transform or a joint.

    Creates and matches new group:

        "parentName_zooParentToRig"

    :param wildcardSuffix: The suffix of the group name, needs this name for toggling
    :type wildcardSuffix: str
    :param matchObject: If True then match the objects only if parenting
    :type matchObject: bool
    :param message: Report the success message to the user?
    :type message: bool
    :return groupName: The name of the group that was created
    :rtype groupName: str
    """
    errorState = False
    grpList = list()
    selObjs = cmds.ls(selection=True)
    if not selObjs:
        om2.MGlobal.displayWarning("Please select an object")
        return ""
    parentList = cmds.ls(selObjs, type="transform")  # also includes joints
    if not parentList:
        om2.MGlobal.displayWarning("Please select either a joint or an object (transform node)")
        return

    # Build groups ---------------------------
    for parent in parentList:
        parentName = namehandling.getShortName(parent)  # Force short name
        if namehandling.nodeListIsUniqueName(parentList):  # Check short name is unique
            om2.MGlobal.displayWarning("The name `{}` is not unique to the scene. Please rename.  "
                                       "Can use Zoo Renamer > Make Unique".format(parentName))
            errorState = True
            continue
        grp = createGroupToRig(parent, wildcardSuffix=wildcardSuffix, matchObject=matchObject, message=False)
        if grp:
            grpList.append(grp)
            if message:
                om2.MGlobal.displayInfo("Success: Group created {}".format(grp))
    if len(parentList) == 1:  # if only one object the messages already reported
        return grpList
    if errorState:
        if message:
            om2.MGlobal.displayWarning("Possible warnings see the script editor: {}".format(grpList))
        return grpList
    if message:
        om2.MGlobal.displayInfo("Groups created: {}".format(grpList))
    return grpList


# ---------------------------------------------
# PARENT REPARENT GROUP
# ---------------------------------------------


def parentReparentGrp(reparentGrp, parent=True, wildcardSuffix=REPARENT_SUFFIX, matchObject=True, message=True):
    """Either "Parents and matches" or "Unparents" a single reparent grp

    :param reparentGrp:  The name of the reparent group
    :type reparentGrp: str
    :param parent:  If True will parent, if False will parent to world (unparent)
    :type parent: bool
    :param wildcardSuffix: The suffix of the group name, needs this name for toggling
    :type wildcardSuffix: str
    :param matchObject: If True then match the objects only if parenting
    :type matchObject: bool
    :param message: Report a message to the user?
    :type message: bool
    :return success: True if the parent or unparent was successful
    :rtype success: list(str)
    """
    # Do the checks ----------------------------------------------------------
    targetParent = reparentGrp.replace(wildcardSuffix, "")
    if not cmds.objExists(targetParent):
        if message:
            om2.MGlobal.displayWarning("The parent object {} does not exit".format(targetParent))
        return False
    if namehandling.nodeListIsUniqueName([targetParent]):
        if message:
            om2.MGlobal.displayWarning("The target parent object {} is not unique in the scene.".format(targetParent))
        return False
    # Checks passed so either "parent and match" or "unparent" --------------------------
    if parent:
        parentCheckList = cmds.listRelatives(reparentGrp, parent=True)
        if parentCheckList:
            if parentCheckList[0] == targetParent:
                if message:
                    om2.MGlobal.displayInfo("`{}` is already parented to `{}`".format(reparentGrp, targetParent))
                return True
        cmds.parent(reparentGrp, targetParent)
        if matchObject:
            cmds.matchTransform(([reparentGrp, targetParent]), pos=True, rot=True, scl=False, piv=False)
        if message:
            om2.MGlobal.displayInfo("`{}` has been parented to `{}`".format(reparentGrp, targetParent))
        return True
    # Unparent --------------------------------------------
    if cmds.listRelatives(reparentGrp, parent=True) is None:  # if the first obj is in world
        om2.MGlobal.displayInfo("Object is already parented to world: {}".format(reparentGrp))
        return
    cmds.parent(reparentGrp, world=True)
    if message:
        om2.MGlobal.displayInfo("`{}` has been unparented".format(reparentGrp))
    return True


def parentReparentGrpScene(parent=True, wildcardSuffix=REPARENT_SUFFIX, matchObject=True, message=True):
    """Either "Parents and matches" or "Unparents" a single reparent grp for the entire scene

    :param parent:  If True will parent, if False will parent to world (unparent)
    :type parent: bool
    :param wildcardSuffix: The suffix of the group name, needs this name for toggling
    :type wildcardSuffix: str
    :param matchObject: If True then match the objects only if parenting
    :type matchObject: bool
    :param message: Report a message to the user?
    :type message: bool
    :return success: True if the parent or unparent was successful
    :rtype success: list(str)
    """
    grpParentList = list()
    errorState = False
    # Find all objects in scene with suffix '_zooParentToRig'
    reparentGrps = namewildcards.getWildcardObjs(wildcardSuffix, underscoreInWildCard=True, suffix="suffix")
    if not reparentGrps:
        om2.MGlobal.displayWarning("No Objects With Wildcard {} Found".format(wildcardSuffix))
        return
    for grp in reparentGrps:
        succeeded = parentReparentGrp(grp, parent=parent, wildcardSuffix=wildcardSuffix, matchObject=matchObject,
                                      message=message)
        if not succeeded:
            errorState = False
        else:
            grpParentList.append(grp)
    if errorState:
        if parent:
            om2.MGlobal.displayWarning("Objects parented with warnings, see script editor: {}".format(grpParentList))
        else:
            om2.MGlobal.displayWarning("Objects unparented with warnings, see script editor: {}".format(grpParentList))
        return
    if parent:
        om2.MGlobal.displayInfo("Success objects parented: {}".format(grpParentList))
    else:
        om2.MGlobal.displayInfo("Success objects uparented: {}".format(grpParentList))


def toggleReparentGrps(reparentGrps, wildcardSuffix=REPARENT_SUFFIX, matchObject=True, selectGrps=True, message=True):
    """Toggles a list of reparent grps either in or out of their parent targets/world

    :param reparentGrps: A list of reparent groups, can be parented or unparented
    :type reparentGrps: list(str)
    :param wildcardSuffix: The suffix of the group name, needs this name for toggling
    :type wildcardSuffix: str
    :param matchObject: Will match the grp to its parent, False will skip
    :type matchObject: bool
    :param selectGrps: Selects all reparent groups after finishing, False does not select
    :type selectGrps: bool
    :param message: Report messages to the user?
    :type message: bool
    :return reparentGrps: A list of all the reparent objects that were toggled.
    :rtype reparentGrps: list(str)
    :return successList: A list of booleans confirming if the parent or reparent was successful
    :rtype successList: list(bool)
    """
    parent = False
    successList = list()

    if cmds.listRelatives(reparentGrps[0], parent=True) is None:  # if the first obj is in world
        parent = True

    for obj in reparentGrps:
        successList.append(parentReparentGrp(obj,
                                             parent=parent,
                                             wildcardSuffix=wildcardSuffix,
                                             matchObject=matchObject,
                                             message=message))
    if selectGrps:
        cmds.select(reparentGrps, replace=True)
    if parent:
        if message:
            om2.MGlobal.displayInfo("Objects have been parented.  "
                                    "See script editor for full details. {}".format(reparentGrps))
    else:
        if message:
            om2.MGlobal.displayInfo("Objects have been unparented.  "
                                    "See script editor for full details. {}".format(reparentGrps))
    return reparentGrps, successList


def toggleReparentGrpsScene(wildcardSuffix=REPARENT_SUFFIX, matchObject=True, selectGrps=True, message=True):
    """Toggles all reparent grps in the scene either in or out of their parent targets/world

    :param reparentGrps: A list of reparent groups, can be parented or unparented
    :type reparentGrps: list(str)
    :param wildcardSuffix: The suffix of the group name, needs this name for toggling
    :type wildcardSuffix: str
    :param matchObject: Will match the grp to its parent, False will skip
    :type matchObject: bool
    :param selectGrps: Selects all reparent groups after finishing, False does not select
    :type selectGrps: bool
    :param message: Report messages to the user?
    :type message: bool
    :return reparentGrps: A list of all the reparent objects that were toggled.
    :rtype reparentGrps: list(str)
    :return successList: A list of booleans confirming if the parent or reparent was successful
    :rtype successList: list(bool)
    """
    # Find all objects in scene with suffix '_zooParentToRig'
    reparentGrps = namewildcards.getWildcardObjs(wildcardSuffix, underscoreInWildCard=True, suffix="suffix")
    if not reparentGrps:
        om2.MGlobal.displayWarning("No Objects With Wildcard {} Found".format(wildcardSuffix))
        return list(), list()
    return toggleReparentGrps(reparentGrps,
                              wildcardSuffix=wildcardSuffix,
                              matchObject=matchObject,
                              selectGrps=selectGrps,
                              message=message)
