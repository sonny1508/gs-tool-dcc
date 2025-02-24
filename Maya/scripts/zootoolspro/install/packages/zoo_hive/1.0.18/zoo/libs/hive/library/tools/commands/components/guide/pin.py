from zoo.libs.hive import api as hiveapi
from zoo.libs.maya.mayacommand import command
from zoo.libs.maya import zapi


class PinComponentGuides(command.ZooCommandMaya):
    """Pin's the components in place
    """
    id = "hive.component.guide.pin"
    
    isUndoable = True
    isEnabled = True

    _components = []

    def resolveArguments(self, arguments):
        super(PinComponentGuides, self).resolveArguments(arguments)
        # first check if the client passed in components
        comps = arguments.get("components", [])
        if not comps:
            # ok no components , what about selection?
            selection = zapi.selected()
            for mobj in selection:
                component = hiveapi.componentFromNode(mobj)
                # ok we have a component but we only operate on the guides so check
                if component and component.hasGuide() and component not in comps:
                    comps.append(component)
            if not comps:
                self.displayWarning("No components found!")
                return
            self._components = comps
        else:
            newComps = [comp for comp in comps if comp.hasGuide()]
            arguments.components = newComps
            self._components = newComps
        return arguments

    def doIt(self, components=None):
        for component in self._components:
            component.pin()
        return True

    def undoIt(self):
        for component in self._components:
            component.unPin()


class UnPinComponentGuides(command.ZooCommandMaya):
    """Pin's the components in place
    """
    id = "hive.component.guide.unpin"
    
    isUndoable = True
    isEnabled = True
    _components = []

    def resolveArguments(self, arguments):
        super(UnPinComponentGuides, self).resolveArguments(arguments)
        # first check if the client passed in components
        comps = arguments.get("components", [])
        if not comps:
            # ok no components , what about selection?
            selection = zapi.selected()
            for mobj in selection:
                component = hiveapi.componentFromNode(mobj)
                # ok we have a component but we only operate on the guides so check
                if component and component.hasGuide() and component not in comps:
                    comps.append(component)
            if not comps:
                self.displayWarning("No components found!")
                return
            self._components = comps
        else:
            newComps = [comp for comp in comps if comp.hasGuide()]
            arguments.components = newComps
            self._components = newComps
        return arguments

    def doIt(self, components=None):

        for component in self._components:
            component.unPin()

    def undoIt(self):
        for component in self._components:
            component.pin()
