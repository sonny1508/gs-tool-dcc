from zoo.libs.maya.cmds.meta import metasplinerig
from zoo.libs.maya.cmds.rig import splinebuilder
from zoo.libs.maya.mayacommand import command


class SplineRigBuildJointsCommand(command.ZooCommandMaya):
    """This command Creates a meta node from the registry.
    """
    id = "zoo.maya.splinerig.buildjoints"
    isUndoable = True

    _modifier = None

    def doIt(self, rigName=None, startJoint=None, endJoint=None, controlCount=None, scale=None, buildFk=None,
             buildRevFk=None, buildSpine=None, buildFloat=None, cogUpAxis=None, buildType=None, ikHandleBuild=None):
        """ Bake the controls

        :type meta: :class:`metasplinerig.MetaSplineRig`
        :return:
        :rtype: :class:`metasplinerig.MetaSplineRig`

        """
        return splinebuilder.buildSpineJoints(rigName,
                                              startJoint=startJoint,
                                              endJoint=endJoint,
                                              controlCount=controlCount,
                                              scale=scale,
                                              buildFk=buildFk,
                                              buildRevFk=buildRevFk,
                                              buildSpine=buildSpine,
                                              buildFloat=buildFloat,
                                              cogUpAxis=cogUpAxis,
                                              message=False,
                                              buildType=buildType,
                                              ikHandleBuild=ikHandleBuild)
