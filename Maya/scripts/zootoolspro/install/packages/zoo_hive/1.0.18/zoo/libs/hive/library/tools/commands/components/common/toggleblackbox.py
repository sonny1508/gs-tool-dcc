from zoo.libs.maya.mayacommand import command


class ToggleBlackBox(command.ZooCommandMaya):
    """Toggles the component blackbox state
    """
    id = "hive.component.blackbox.toggle"
    
    isUndoable = True
    _components = []  # type list[:class:`api.Component`]
    _save = False
    _previousState = False

    def resolveArguments(self, arguments):
        components = arguments.get("components")

        if not components:
            self.displayWarning("Must supply at least one component instance")
            return
        valid = []

        for comp in components:
            if comp.exists():
                valid.append(comp)
                self._previousState = comp.rig.configuration.blackBox
        self._save = arguments.get("save", False)
        if not valid:
            self.displayWarning("No Valid Components")
            return
        self._components = valid
        return arguments

    def doIt(self, components=None, save=False):
        for component in self._components:
            component.blackBox = not self._previousState
        if self._save:
            rig = self._components[0].rig
            rig.configuration.applySettingsState({"blackBox": not self._previousState})
            rig.saveConfiguration()

    def undoIt(self):
        for comp in self._components:
            comp.blackBox = self._previousState
        if self._save:
            rig = self._components[0].rig
            rig.configuration.applySettingsState({"blackBox": self._previousState})
            rig.saveConfiguration()
