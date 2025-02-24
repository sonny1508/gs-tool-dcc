from zoo.libs.utils import output
import maya.cmds as cmds

"""

This assumes the "fish" is facing in the positive Z direction 
Set the number of joins in the chain in 'NumOfJoints'
Select 3 objects, First being the joint chain in the first and last position and the third being the path curve

"""

LATTICE_DIVS_LIST = [[5, 2, 2], [2, 5, 2], [2, 2, 5]]
XYZ_LIST = ["x", "y", "z"]

def pathGuide(startjoint, endjoint, curve, frontAxis='x', num_of_joints=7, upAxis='y', lattice_value=5):
    """ Creates a motion/flow path rig using the joint chain and its selected curve

    :param startjoint: First Joint in Chain
    :type startjoint: Str
    :param endjoint: Last Joint in Chain
    :type endjoint: Str
    :param curve: Curve path
    :type curve: Str
    :param frontAxis: Joint chain front axis
    :type frontAxis: Str
    :param num_of_joints: Number of joints in the chain
    :type num_of_joints: int
    :param upAxis: Joint chain up axis
    :type upAxis: str
    :param lattice_value: Lattice Division Value
    :type lattice_value: int
    :return:
    :rtype:
    """
    # Creating IK spline Handle
    ikHandle, ikEffector, ikCurve = cmds.ikHandle(startJoint=startjoint, endEffector=endjoint, solver='ikSplineSolver')
    ikCurve = cmds.rebuildCurve(ikCurve, spans=(num_of_joints * 2 - 2))[0]
    cmds.xform(ikCurve, centerPivots=True)
    cmds.refresh()

    if frontAxis == "y":
        upAxis = 'x'

    # Motion Path setup
    motionpath = cmds.pathAnimation(ikCurve, curve=curve,
                                    fractionMode=True, follow=True,
                                    followAxis=frontAxis, upAxis=upAxis, worldUpType="vector",
                                    worldUpVector=[0, 1, 0], inverseUp=False, inverseFront=False,
                                    bank=False, startTimeU=0, endTimeU=120)

    cmds.cutKey("{}.u".format(motionpath))
    cmds.refresh()

    # Ik handle twist Controls
    cmds.setAttr(ikHandle + ".dTwistControlEnable", 1)

    # Flow Path
    i = XYZ_LIST.index(frontAxis)
    LATTICE_DIVS_LIST[i][i] = lattice_value

    lattice, Base = cmds.flow(ikCurve, divisions=LATTICE_DIVS_LIST[i], objectCentered=True, localCompute=False)[2:]

    output.displayInfo("Build is completed")
    returnItems = {"ikHandle": ikHandle, "ikEffector": ikEffector,
                   "ikCurve": ikCurve, "flowLattice": lattice,
                   "flowBase": Base, "motionPath": motionpath,
                   "frontAxis": frontAxis}
    return returnItems
