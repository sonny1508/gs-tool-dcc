from zoo.libs.maya.mayacommand import command
from zoo.libs.hive import api
from zoo.libs.maya import zapi
from zoo.libs.utils import output


class PolishRigCommand(command.ZooCommandMaya):
    """Runs polishRig() on the provide rig instance.

    .. note::

        Currently this isn't undoable.

    """
    id = "hive.rig.global.polishRig"

    isUndoable = False
    useUndoChunk = True  # Chunk all operations in doIt()
    disableQueue = True  # If true, disable the undo queue in doIt()
    isEnabled = True
    _rig = None
    deleteGuides = False

    def resolveArguments(self, arguments):
        rig = arguments["rig"]
        if not isinstance(rig, api.Rig):
            self.displayWarning("Rig argument must be of type 'Rig'")
            return
        return arguments

    def doIt(self, rig=None):
        """

        :param rig:
        :type rig: :class:`api.Rig`
        :return: Returns True if successful
        :rtype: bool
        """

        success = rig.polish()
        zapi.clearSelection()
        return success

