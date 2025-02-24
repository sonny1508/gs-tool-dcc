from maya.api import OpenMaya as om2
from zoo.libs.maya.mayacommand import command


class SplineRigBuildAdditiveFKCommand(command.ZooCommandMaya):
    """This command rebuilds the spline rig
    """
    id = "zoo.maya.splinerig.buildAdditiveFk"
    isUndoable = True

    useUndoChunk = False
    _modifier = None
    additiveRigCmd = None
    disableQueue = True

    def doIt(self, meta=None, controlSpacing=1, rigName="additive"):
        """ Rebuilds the curve rig based on meta

        :type meta: metasplinerig.MetaSplineRig
        :param meta:
        :type meta:
        :param controlSpacing: Build the controls on every nth joint
        :type controlSpacing: int
        :param rigName: 
        :return:
        :rtype:

        """
        self._modifier = om2.MDagModifier()
        meta, self.additiveRigCmd = meta.buildAdditiveFkRig(mod=self._modifier, controlSpacing=controlSpacing,
                                                            rigName=rigName)
        self._modifier.doIt()
        return meta

    def undoIt(self):
        if self._modifier:
            self._modifier.undoIt()

        if self.additiveRigCmd:
            self.additiveRigCmd.undoIt()
