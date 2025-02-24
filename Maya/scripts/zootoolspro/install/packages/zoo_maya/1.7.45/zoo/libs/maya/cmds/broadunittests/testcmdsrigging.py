import maya.api.OpenMaya as om2
from maya import cmds

from zoo.libs.maya.mayacommand import mayaexecutor as executor
from zoo.libs.maya import zapi


def testSplineRig():
    om2.MGlobal.displayInfo("\n\n---------- SPLINE RIG - START -----------")

    # Create
    curve1 = zapi.nodeByName(cmds.curve(p=[(0, 0, 0), (3, 5, 6), (5, 6, 7), (9, 9, 9), (10, 10, 6)]))
    om2.MGlobal.displayInfo("log ---> NURBS Curve Created: {}".format(curve1.fullPathName()))

    metaAttrs = {'buildRevFk': True, 'upAxis': 0, 'scale': 1.0, 'controlSpacing': 2, 'name': 'splineRig',
                 'ikHandleBuild': None, 'orientRoot': 0, 'spacingWeight': 0.0, 'jointCount': 12,
                 'jointsSpline': curve1, 'buildAdditiveFk': False, 'buildFk': True, 'controlCount': 5,
                 'startJoint': None, 'buildFloat': True, 'hierarchySwitch': 'spine', 'buildSpine': False,
                 'reverseDirection': False, 'endJoint': None}

    splineRigMeta = executor.execute("zoo.maya.splinerig.build", metaAttrs=metaAttrs, buildType=0)  # type: metasplinerig.MetaSplineRig
    om2.MGlobal.displayInfo("log ---> Spline Rig Created: {}".format(splineRigMeta.name()))

    # Rebuild
    metaAttrs = {'buildRevFk': True, 'upAxis': 0, 'scale': 1.0, 'controlSpacing': 2,
                 'ikHandleBuild': None, 'orientRoot': 0, 'spacingWeight': 0.0, 'jointCount': 12, 'jointsSpline': None,
                 'buildAdditiveFk': False, 'buildFk': True, 'controlCount': 6,
                 'buildFloat': True, 'hierarchySwitch': 'fk', 'buildSpine': False, 'reverseDirection': False,
                 'startJoint': splineRigMeta.startJoint.value(),
                 'endJoint': splineRigMeta.endJoint.value(),
                 'name': splineRigMeta.name()}

    splineRigMeta = executor.execute("zoo.maya.splinerig.rebuild", meta=splineRigMeta, metaAttrs=metaAttrs, bake=False)
    om2.MGlobal.displayInfo("log ---> Spline Rig Rebuilt: {}".format(splineRigMeta.name()))

    # Additive FK
    addFkRig = executor.execute("zoo.maya.splinerig.buildAdditiveFk",
                                meta=splineRigMeta,
                                controlSpacing=2)
    om2.MGlobal.displayInfo("log ---> Additive FK Built: {}".format(splineRigMeta.name()))

    # Rename Spline Rig
    splineRigMeta.setRigName("testNameSpline")
    om2.MGlobal.displayInfo("log ---> Spline Rig Renamed: {}".format(splineRigMeta.name()))

    # Del Additive FK
    addFkName = addFkRig.rigName.value()
    executor.execute("zoo.maya.additiveFk.delete", meta=addFkRig)
    om2.MGlobal.displayInfo("log ---> Additive FK Deleted: {}".format(addFkName))

    # Delete Spline Ik Rig completely
    executor.execute("zoo.maya.splinerig.delete", meta=splineRigMeta, deleteAll=True)
    om2.MGlobal.displayInfo("log ---> Spline Rig Deleted: {}".format(addFkName))

    # Delete spline curve
    curveName = curve1.fullPathName()
    cmds.delete(curveName)
    om2.MGlobal.displayInfo("log ---> NURBS Curve Deleted: {}".format(curveName))

    om2.MGlobal.displayInfo("#### SUCCESS SPLINE RIG FINISHED TESTING -  PLEASE CHECK FOR ERRORS ABOVE ####\n\n\n")




