from zoo.libs.maya.mayacommand import command
from zoo.libs.hive import api
from zoo.libs.maya import zapi


class DuplicateCommand(command.ZooCommandMaya):
    id = "hive.component.duplicate"
    
    isUndoable = True
    isEnabled = True
    # name side tuple
    _newComponents = []
    _currentSelection = []
    _rig = None  # type: api.Rig

    def resolveArguments(self, arguments):
        super(DuplicateCommand, self).resolveArguments(arguments)
        # {"component": component, "name": component.name(),
        # "side": component.side(), "parent": None}
        sources = arguments.get("sources")
        rig = arguments.get("rig")
        if not rig:
            self.displayWarning("No valid rig instance provided")
            return
        self._rig = rig
        # We Need to traverse all children and add them to the source list
        # so this dict contains a simple "componentKey": SourceData
        consolidatedSources = {}
        for source in sources:
            component = source["component"]
            key = component.serializedTokenKey()
            consolidatedSources[key] = source
        # traverse all children and add to consolidated sources
        for source in sources:
            component = source["component"]
            for child in component.children(depthLimit=len(self._rig)):
                childKey = child.serializedTokenKey()
                if childKey in consolidatedSources:
                    continue
                data = {
                    "component": child, "name": child.name(),
                    "side": child.side(), "parent": child.parent()
                }
                consolidatedSources[childKey] = data
            newName = source.get("name", source["component"].name())
            source["name"] = newName
        sources = list(consolidatedSources.values())
        if not sources:
            self.displayWarning("Source Components must be provided")
            return
        arguments["sources"] = sources
        self._currentSelection = list(zapi.selected())
        return arguments

    def doIt(self, rig=None, sources=None):
        newComponents = self._rig.duplicateComponents(sources)
        self._newComponents = [(i.name(), i.side()) for i in newComponents.values()]
        selectables = []
        compObjects = newComponents.values()
        for comp in compObjects:
            parent = comp.parent()
            if parent is None or parent not in compObjects:
                selectables.append(comp.guideLayer().guideRoot())
        if selectables:
            zapi.select(selectables)
        return newComponents.values()

    def undoIt(self):
        for source in self._newComponents:
            self._rig.deleteComponent(*source)
        zapi.select(self._currentSelection)
