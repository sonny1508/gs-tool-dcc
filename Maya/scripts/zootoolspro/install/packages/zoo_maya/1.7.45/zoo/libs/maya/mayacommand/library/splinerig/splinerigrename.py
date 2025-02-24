from maya.api import OpenMaya as om2
from zoo.libs.maya.mayacommand import command
from zoo.libs.maya.cmds.meta import metasplinerig


class SplineRigRenameCommand(command.ZooCommandMaya):
    """This command deletes the spline rig
    """
    id = "zoo.maya.splinerig.rename"

    isUndoable = True

    _modifier = None

    def doIt(self, meta=None, name=None):
        """ Build the curve rig based on meta

        :type meta: metasplinerig.MetaSplineRig
        :return:
        
        :rtype: 

        """
        self._modifier = om2.MDGModifier()
        meta.setRigName(name, mod=self._modifier)
        self._modifier.doIt()

        return meta

    def undoIt(self):
        """ Undo Rename

        :return:
        :rtype:
        """
        if self._modifier:
            self._modifier.undoIt()
