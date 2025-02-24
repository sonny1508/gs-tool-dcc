from zoo.libs.maya.mayacommand import command
from zoo.libs.hive.base import rig as hiverig


class DeleteRigCommand(command.ZooCommandMaya):
    id = "hive.rig.delete"
    isUndoable = True
    isEnabled = True
    _rig = None

    _template = {}

    def doIt(self, rig=None):
        self._template = rig.serializeFromScene()
        rig.delete()
        return True

    def undoIt(self):
        if self._template:
            hiverig.loadFromTemplate(self._template)
