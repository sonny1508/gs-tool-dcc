from zoo.libs.maya.mayacommand import command
from zoo.libs.hive.base import rig as hiverig
from zoo.libs.maya import zapi


class BuildRigCommand(command.ZooCommandMaya):
    """Builds the provided rig instance Rig Layer.
    """
    id = "hive.rig.global.buildRigs"

    isUndoable = True
    isEnabled = True
    _rig = None
    deleteGuides = False

    def resolveArguments(self, arguments):
        rig = arguments.get("rig")
        if rig is None or not isinstance(rig, hiverig.Rig):
            self.displayWarning("Must supply the rig instance to the command")
            return
        return {"rig": rig}

    def doIt(self, rig=None):
        """
        :param rig: The rig instance to build
        :type rig: :class:`api.Rig`
        :return: True if succeeded.
        :rtype: bool
        """
        success = rig.buildRigs()
        zapi.clearSelection()

        self._rig = rig
        return success

    def undoIt(self):
        if self._rig.exists():
            self._rig.deleteRigs()
