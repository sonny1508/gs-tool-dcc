from maya.api import OpenMaya as om2
from zoo.libs.maya import zapi
from zoo.libs.maya.cmds.meta import metasplinerig
from zoo.libs.maya.cmds.objutils import joints
from zoo.libs.maya.cmds.rig import splinebuilder
from zoo.libs.maya.mayacommand import command
from zoo.core.util import strutils

from zoo.libs.maya.mayacommand.library import jointsalongcurvecommand


class SplineRigBuildCommand(command.ZooCommandMaya):
    """This command Creates a meta node from the registry.
    """
    id = "zoo.maya.splinerig.build"
    isUndoable = True
    useUndoChunk = True
    _modifier = None
    disableQueue = True
    jointList = None
    jointCmd = None

    def resolveArguments(self, arguments):
        """

        :param arguments:
        :type arguments:
        :return:
        :rtype:
        """

        metaAttrs = arguments['metaAttrs']
        if arguments['buildType'] == splinebuilder.BT_STARTENDJOINT:
            valid = None
            # Check if start/end joint is valid

            startJoint = metaAttrs['startJoint']

            if strutils.isStr(startJoint):
                metaAttrs['startJoint'] = zapi.nodeByName(startJoint)
            endJoint = arguments['metaAttrs']['endJoint']
            if strutils.isStr(endJoint):
                metaAttrs['endJoint'] = zapi.nodeByName(endJoint)

            if startJoint and endJoint:
                valid = splinebuilder.validStartEndJoint(metaAttrs['startJoint'].fullPathName(),
                                                         metaAttrs['endJoint'].fullPathName())
            if not valid:
                self.cancel("Invalid start or end joint")

        if arguments['buildType'] == splinebuilder.BT_SPLINE and not metaAttrs.get('jointsSpline'):
            self.cancel("'jointsSpline' must be filled if build type is set to 'SPLINE'")

        self._modifier = om2.MDGModifier()
        return {"metaAttrs": arguments['metaAttrs']}

    def doIt(self, metaAttrs=None, meta=None, buildType=splinebuilder.BT_STARTENDJOINT):
        """ Build the curve rig based on meta

        :return:
        :rtype: metasplinerig.MetaSplineRig

        """
        if buildType == splinebuilder.BT_SPLINE:
            curve = metaAttrs["jointsSpline"]
            upAxis = joints.AUTO_UP_VECTOR_WORDS_LIST[metaAttrs["upAxis"]]

            self.jointCmd = jointsalongcurvecommand.JointsAlongCurveCommand()
            self.jointList = self.jointCmd.runArguments(splineCurve=curve.fullPathName(),
                                                        jointCount=metaAttrs["jointCount"],
                                                        jointName=metaAttrs["name"],
                                                        spacingWeight=metaAttrs["spacingWeight"],
                                                        secondaryAxisOrient=upAxis,
                                                        buildMetaNode=False,
                                                        reverseDirection=metaAttrs['reverseDirection'],
                                                        hideCurve=True)

            metaAttrs["startJoint"] = self.jointList[0]
            metaAttrs["endJoint"] = self.jointList[-1]

        metaAttrs['buildType'] = buildType

        self._meta = metasplinerig.MetaSplineRig(mod=self._modifier, **metaAttrs)
        self._meta.build(buildType=buildType, bindDefaultJoints=False, mod=self._modifier)
        self._modifier.doIt()
        om2.MGlobal.displayInfo("Success: Spline Rig Built")
        return self._meta

    def undoIt(self):
        """ Undo it

        :return:
        :rtype:
        """
        if self._modifier:
            # self._modifier.undoIt()
            self._meta.deleteRig()

        if self.jointCmd:
            self.jointCmd.undoIt()
