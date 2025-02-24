from maya.api import OpenMaya as om2

from zoo.libs.maya.mayacommand import command
from zoo.libs.maya.cmds.meta import metasplinerig


class SplineRigMeshMarkingMenuCommand(command.ZooCommandMaya):
    """This command switches the controls of the rig
    """
    id = "zoo.maya.splinerig.meshMarkingMenuActive"
    isUndoable = True

    _modifier = None
    _selected = []
    _meta = None

    def doIt(self, meta=None, active=True):
        """ Switches the controls of the rig

        :param meta:
        :type meta: metasplinerig.MetaSplineRig
        :type active: bool
        :param active: Set to active or not

        """
        self._meta = meta
        self._modifier = om2.MDGModifier()
        meta.setMeshMarkingMenuActive(active, mod=self._modifier)

    def undoIt(self):
        if self._modifier:
            self._modifier.undoIt()
