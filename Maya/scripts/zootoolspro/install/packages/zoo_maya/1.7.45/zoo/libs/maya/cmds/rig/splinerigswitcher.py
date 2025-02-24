"""
Switching Spline Rig, match switches the controls on the Spline Rig

Current Mode to FK example:

    from zoo.libs.maya.cmds.rig import splinerigswitcher
    splinerigswitcher.switchMatchSplineMode('fk', switchObj="splineRig_cog_ctrl", selectControls=True)

"""

from maya import cmds as cmds
from maya.api import OpenMaya as om2

from zoo.libs.maya.cmds.objutils import alignutils


def retrieveSpineControlList(meta):
    """Gets the current spline mode (spine, fk, float or revFk) and retrieves all control and joint settings.

    This function is for spline switching not building.

    Returns as a tuple:

    - spineList: the spine control list(str)
    - fkList: the fk control list(str)
    - floatList: the float control list(str)
    - revFkList: the revFk control list(str)
    - spineMidRot: The middle control of the Spine setup as a str, if doesn't exist will be None
    - currentMode: The current spline mode, what controls are we currently seeing? eg "revFk" string
    - controlTypesList: A list(str) of all the controls by mode that exist eg ["fk", "spline"]
    - firstJoint: The first joint full name str
    - lastJoint: The last joint full name str

    :return: A list of objects and modes that are the spline rig settings.
    :type: tuple(list(str), list(str), list(str), list(str), str, str, list(str), str, str)
    """
    spineList = [ctrl.fullPathName() for ctrl in meta.spineControlList.value() if ctrl is not None]
    fkList = [ctrl.fullPathName() for ctrl in meta.fkControlList.value() if ctrl is not None]
    floatList = [ctrl.fullPathName() for ctrl in meta.floatControlList.value() if ctrl is not None]
    revFkList = [ctrl.fullPathName() for ctrl in meta.revfkControlList.value() if ctrl is not None]
    spineMidRot = [ctrl.fullPathName() for ctrl in meta.spineRotControl.value() if ctrl is not None]
    currentMode = meta.currentHierarchyModeStr()
    controlTypesList = meta.controlTypes()
    jointList = meta.joints()
    firstJoint = jointList[0].fullPathName()
    lastJoint = jointList[-1].fullPathName()
    return spineList, fkList, floatList, revFkList, spineMidRot, currentMode, controlTypesList, firstJoint, lastJoint


def switchToSplineMode(switchMode, spineList, fkList, floatList, revFkList, spineMidRot, currentMode,
                       controlTypesList, firstJoint, lastJoint, selObjs=None, switchObj="root_ctrl",
                       selectControls=True):
    """
    Does the switching for the spline to a given mode 'spine', 'fk', 'float', 'revFk'

    :param switchMode: The spline mode to switch to, 'spine', 'fk', 'float', 'revFk'
    :type switchMode: str
    :param spineList: The spline list of controls
    :type spineList: list
    :param fkList: The fk list of controls
    :type fkList: list
    :param floatList: The floating list of controls
    :type floatList: list
    :param revFkList: The fk list of controls
    :type revFkList: list
    :param currentMode: What mode is the spline in now?
    :type currentMode: str
    :param controlTypesList: A list of all the controls by mode that exist eg ["fk", "spline"]
    :type controlTypesList: list
    :param firstJoint: first joint name in the rig
    :type firstJoint: str
    :param lastJoint: last joint name in the rig
    :type lastJoint: str
    :param selObjs: The selected objects
    :type selObjs: list
    :param switchObj: The object that controls the spline
    :type switchObj: str
    :param selectControls: Should we select the matching control on the new set and deselect the old?
    :type selectControls: bool
    """
    if switchMode not in controlTypesList:
        om2.MGlobal.displayWarning("The mode `{}` does not exist on this rig, cannot switch".format(switchMode))
        return
    if currentMode == switchMode:  # bail if no change needed
        om2.MGlobal.displayInfo("Already in `{}` mode".format(switchMode))
        return

    # get current control list
    if currentMode == "spine":
        currentControlList = list(spineList)
    elif currentMode == "fk":
        currentControlList = list(fkList)
    elif currentMode == "float":
        currentControlList = list(floatList)
    else:  # currentMode == "revFk"
        currentControlList = list(revFkList)

    # get the match/switch to list
    if switchMode == "spine":
        switchControlList = spineList
    elif switchMode == "fk":
        switchControlList = fkList
    elif switchMode == "float":
        switchControlList = floatList
    elif switchMode == "revFk":
        switchControlList = revFkList
    else:
        om2.MGlobal.displayError("The switch mode `{}` isn't valid".format(switchMode))
        return False

    # Create temp null (transforms) setup for orient aim info
    orientedNullList = switchOrientNulls(currentControlList)

    # Reorder if needed otherwise match fails for switching to revFk and spine modes
    if switchMode == "revFk":  # if switching to reversFk then reverse the order
        switchControlList.reverse()
        orientedNullList.reverse()
    if switchMode == "spine":  # If switching to spine then items need shuffling for match due to parent order in spine
        newOrder = [0, 1, 4, 3, 2]
        switchControlList = [switchControlList[i] for i in newOrder]
        orientedNullList = [orientedNullList[i] for i in newOrder]

    # Do the match -------------------------------
    for i, null in enumerate(orientedNullList):
        alignutils.matchObjTransRot(switchControlList[i], null, message=False)  # match objs
    cmds.delete(orientedNullList)
    # Switch to the new mode in the enum list attribute hierarchySwitch
    switchIndex = controlTypesList.index(switchMode)
    cmds.setAttr("{}.hierarchySwitch".format(switchObj), switchIndex)

    if selectControls:  # Select new controls -------------
        cmds.select(switchControlList, replace=True)

    om2.MGlobal.displayInfo("Success: Spine swap matched `{}` to `{}`".format(currentMode, switchMode))
    return True


def switchOrientNulls(currentControlList, matchExact=False):
    """This creates a bunch of group nulls and positions and orients them to match the objectList.

    The up vector of all joints is based off the first joint (z up) and the last control off the lastJoint (z up).

    :param currentControlList: A list of objects likely the switch from controls
    :type currentControlList: list(str)
    :param matchExact: Will leave the first and last controls exactly as they are, not nice but exact for twists
    :type matchExact: bool
    :return nullList: A list of nulls that have been created to match the new control positions to
    :rtype nullList: list(str)
    """
    # Create the nulls
    nullList = list()
    for i, obj in enumerate(currentControlList):
        nullList.append(cmds.group(name="tempNull_{}".format(i), empty=1, world=1))
    # Get the Z vector of the first and last joint, X is switchObjMatrix[:3]  Y is switchObjMatrix[4:7]
    firstZVector = cmds.xform(currentControlList[0], worldSpace=True, matrix=True, query=True)[8:11]
    lastZVector = cmds.xform(currentControlList[-1], worldSpace=True, matrix=True, query=True)[8:11]
    # Aim the nulls at each other and set correct twist (world up axis) with twist offsets for middle nulls (controls)
    nullLen = len(nullList)
    vectorOffset = ((lastZVector[0] - firstZVector[0]) / (nullLen - 1),
                    (lastZVector[1] - firstZVector[1]) / (nullLen - 1),
                    (lastZVector[2] - firstZVector[2]) / (nullLen - 1),)
    for i, null in enumerate(nullList[1:-1]):  # Ignore first and last
        # Add the offset to the world up vector, will mess up if over 180 angle dif between the start and end.
        v = ((vectorOffset[0] * (i + 1)) + firstZVector[0],
             (vectorOffset[1] * (i + 1)) + firstZVector[1],
             (vectorOffset[2] * (i + 1)) + firstZVector[2])
        # Match to the previous control, not the correct match so that the aim is previous to next control
        cmds.matchTransform([null, currentControlList[i]], pos=1, rot=1, scl=0, piv=0)
        # Do the aim
        cmds.delete(cmds.aimConstraint([currentControlList[i + 2], null], worldUpVector=v, upVector=(0.0, 0.0, 1.0),
                                       aimVector=(0.0, 1.0, 0.0), maintainOffset=False))
        # Match back to correct control
        cmds.matchTransform([null, currentControlList[i + 1]], pos=1, rot=0, scl=0, piv=0)
    # Match first and last null
    cmds.matchTransform([nullList[0], currentControlList[0]], pos=1, rot=1, scl=0, piv=0)
    cmds.matchTransform([nullList[-1], currentControlList[-1]], pos=1, rot=1, scl=0, piv=0)
    if not matchExact:  # This has small match errors in the twist, but orients overall better with start/end aiming
        # Aim first null
        cmds.delete(cmds.aimConstraint([nullList[1], nullList[0]], worldUpVector=firstZVector, upVector=(0.0, 0.0, 1.0),
                                       aimVector=(0.0, 1.0, 0.0), maintainOffset=False))
        # Aim last null
        cmds.delete(cmds.aimConstraint([nullList[-2], nullList[-1]], worldUpVector=lastZVector, upVector=(0.0, 0.0, 1.0),
                                       aimVector=(0.0, -1.0, 0.0), maintainOffset=False))
    return nullList


def switchMatchSplineMode(switchMode, meta, switchObj="root_ctrl", selectControls=True):
    """
    Main function for spline space switching.  Switch the spline to a mode can be...
    'spine', 'fk', 'float', 'revFk'

    :param switchMode: The spline mode to switch to, 'spine', 'fk', 'float', 'revFk'
    :type switchMode: str
    :param meta:
    :type meta: zoo.libs.maya.cmds.meta.metasplinerig.MetaSplineRig
    :param switchObj: The object that controls the spine with the enum attribute
    :type switchObj: str
    :param selectControls: Select the switched controls after the switch?
    :type selectControls: bool
    """
    selObjs = cmds.ls(selection=True)  # will select equivalent controls of new mode if selectControls=True
    # Get obj lists and state info
    spineList, fkList, floatList, revFkList, \
    spineMidCtrl, currentMode, controlTypesList, firstJoint, lastJoint = retrieveSpineControlList(meta)

    if not currentMode:
        om2.MGlobal.displayWarning("Cannot switch as there is only one hierarchy mode on this spline rig.")
        return

    # Switch and match
    switchToSplineMode(switchMode, spineList, fkList, floatList, revFkList, spineMidCtrl, currentMode, controlTypesList,
                       firstJoint, lastJoint, selObjs=selObjs, switchObj=switchObj, selectControls=selectControls)
