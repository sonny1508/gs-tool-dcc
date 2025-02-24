from maya.api import OpenMaya as om2
from zoo.libs.maya.cmds.meta import metasplinerig
from zoo.libs.maya.mayacommand import command


class SplineRigDeleteCommand(command.ZooCommandMaya):
    """This command deletes the spline rig
    """
    id = "zoo.maya.splinerig.delete"
    isUndoable = True

    _modifier = None
    useUndoChunk = False

    def resolveArguments(self, arguments):
        self._modifier = om2.MDagModifier()
        return arguments

    def doIt(self, meta=None, deleteAll=None, keepMeta=False, showSpline=False, message=True):
        """ Build the curve rig based on meta

        :type meta: metasplinerig.MetaSplineRig
        :return:
        
        :rtype: 

        """
        if deleteAll:
            meta.deleteRig(deleteAll=deleteAll, mod=self._modifier, keepMeta=keepMeta, showSpline=showSpline)
        else:
            meta.deleteRig(mod=self._modifier, keepMeta=keepMeta, showSpline=showSpline)

        if deleteAll and message:
            om2.MGlobal.displayInfo("Success: Spline Rig Deleted")
        return meta

    def undoIt(self):
        if self._modifier:
            self._modifier.undoIt()
