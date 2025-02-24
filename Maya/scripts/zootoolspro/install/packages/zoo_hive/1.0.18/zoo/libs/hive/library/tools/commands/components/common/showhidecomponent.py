from zoo.libs.maya.mayacommand import command
from zoo.libs.hive import api


class ShowComponentCommand(command.ZooCommandMaya):
    """Shows the Component
    """
    id = "hive.components.show"
    
    isUndoable = True
    _components = []

    def resolveArguments(self, arguments):
        components = arguments.get("components")

        if not components:
            self.displayWarning("Must supply component instance")
            return
        for comp in components:
            if not isinstance(comp, api.Component):
                self.displayWarning("Provided component is of the wrong type")
                return
        self._components = components
        return arguments

    def doIt(self, components=None):
        for comp in self._components:
            comp.show()

    def undoIt(self):
        for comp in self._components:
            comp.hide()


class HideComponentCommand(command.ZooCommandMaya):
    """Hide the component
    """
    id = "hive.components.hide"
    isUndoable = True
    

    _components = []

    def resolveArguments(self, arguments):
        components = arguments.get("components")

        if not components:
            self.displayWarning("Must supply component instance")
            return
        for comp in components:
            if not isinstance(comp, api.Component):
                self.displayWarning("Provided component is of the wrong type")
                return
        self._components = components
        return arguments

    def doIt(self, components=None):
        for comp in self._components:
            comp.hide()

    def undoIt(self):
        for comp in self._components:
            comp.show()


class ToggleComponentVisibilityCommand(command.ZooCommandMaya):
    """Toggles the Component visibility
    """
    id = "hive.component.toggleVisibility"
    
    isUndoable = True
    _components = None

    def resolveArguments(self, arguments):
        components = arguments.get("components")

        if not components:
            self.displayWarning("Must supply rig instance")
            return
        self._components = components
        return arguments

    def doIt(self, components=None):
        for comp in self._components:
            self._toggleVis(comp)

    def undoIt(self):
        if self._components:
            for comp in self._components:
                self._toggleVis(comp)

    def _toggleVis(self, comp):
        if comp.isHidden():
            comp.show()
            return
        comp.hide()
