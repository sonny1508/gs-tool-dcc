from zoo.libs.maya.mayacommand import command

from zoo.libs.hive import api
from zoo.libs.maya import zapi


class DeleteComponentSkeletonCommand(command.ZooCommandMaya):
    """Builds the component rig

    """
    id = "hive.component.skeleton.delete"
    
    description = __doc__
    isUndoable = True
    isEnabled = True
    useUndoChunk = True  # Chunk all operations in doIt()
    _rig = None  # type: api.Rig

    def doIt(self, rig=None):
        self._rig = rig
        rig.deleteDeform()

    def undoIt(self):
        if self._rig.exists():
            self._rig.buildDeform()


class BuildComponentSkeletonCommand(command.ZooCommandMaya):
    """Builds the rigs Deformation Layer
    """
    id = "hive.component.skeleton.build"
    
    description = __doc__
    isUndoable = True
    isEnabled = True
    useUndoChunk = True  # Chunk all operations in doIt()
    _rig = None  # type: api.Rig

    def doIt(self, rig=None):
        """

        :param rig: The rig instance to build
        :type rig: :class:`rig.Rig`
        :return: True if the build succeeded.
        :rtype: bool
        """
        self._rig = rig
        success = rig.buildDeform()
        zapi.clearSelection()
        return success


    def undoIt(self):
        if self._rig.exists():
            self._rig.deleteDeform()
            self._rig.buildGuides()
