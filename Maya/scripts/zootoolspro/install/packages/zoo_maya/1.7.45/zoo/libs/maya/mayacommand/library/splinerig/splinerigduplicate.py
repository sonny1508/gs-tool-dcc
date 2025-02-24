from zoo.libs.maya.mayacommand import command
from zoo.libs.maya.cmds.meta import metasplinerig


class SplineRigDuplicateCommand(command.ZooCommandMaya):
    """This command switches the controls of the rig
    """
    id = "zoo.maya.splinerig.duplicate"
    isUndoable = True

    _modifier = None
    _selected = []
    _meta = None

    def doIt(self, meta=None):
        """ Switches the controls of the rig

        :param meta:
        :type meta: metasplinerig.MetaSplineRig
        :type switchTo: str
        :return: True if successful, false otherwise
        :rtype: bool
        """
        self._meta = meta.duplicateRig()

    def undoIt(self):
        if self._meta:
            self._meta.deleteRig(deleteAll=True)
