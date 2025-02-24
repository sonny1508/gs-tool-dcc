from zoo.libs.maya.mayacommand import command
from zoo.libs.maya import zapi


class ToggleBuildComponentGuideCommand(command.ZooCommandMaya):
    """Toggles the component guides build/delete
    """
    id = "hive.component.rig.build.toggle"

    isUndoable = True
    isEnabled = True
    _components = []
    _rig = None
    _deletedGuides = []
    _createdGuides = []


    def resolveArguments(self, arguments):
        super(ToggleBuildComponentGuideCommand, self).resolveArguments(arguments)
        components = arguments.get("components", [])
        rig = arguments.get("rig", None)
        if not rig:
            self.displayWarning("The Rig doesn't exists")
            return
        for i in components:
            if not i.exists():
                self.displayWarning("The Component doesn't exist!")
                return
        return {"components": components}

    def doIt(self, rig=None, components=None):
        componentsNeedingGuides = []
        componentsNeedingDeletedGuides = []

        for component, func in self._components:
            if not component.hasGuide():
                componentsNeedingGuides.append(component)
            else:
                componentsNeedingDeletedGuides.append(component)
        if componentsNeedingGuides:
            self._rig.buildGuides(componentsNeedingGuides)
        else:
            self._rig.deleteGuides(componentsNeedingDeletedGuides)
        self._deletedGuides = componentsNeedingDeletedGuides
        self._createdGuides = componentsNeedingGuides

    def undoIt(self):
        if self.rig:
            self._rig.deleteGuides(self._createdGuides)
            self._rig.buildGuides(self._deletedGuides)


class BuildComponentRigCommand(command.ZooCommandMaya):
    """Builds the component rig

    """
    id = "hive.component.rig.build"

    isUndoable = True
    isEnabled = True

    _rig = None

    def resolveArguments(self, arguments):
        super(BuildComponentRigCommand, self).resolveArguments(arguments)
        self._rig = arguments.rig
        return arguments

    def doIt(self, rig=None):
        success = self._rig.buildRigs()
        zapi.clearSelection()
        return success

    def undoIt(self):
        if self._rig.exists():
            self._rig.deleteRigs()


class DeleteComponentRigCommand(command.ZooCommandMaya):
    """Builds the component rig

    """
    id = "hive.component.rig.delete"

    isUndoable = False
    isEnabled = True

    _rig = None

    def resolveArguments(self, arguments):
        super(DeleteComponentRigCommand, self).resolveArguments(arguments)
        self._rig = arguments.rig
        return arguments

    def doIt(self, rig=None):
        success = rig.deleteRigs()
        return success
