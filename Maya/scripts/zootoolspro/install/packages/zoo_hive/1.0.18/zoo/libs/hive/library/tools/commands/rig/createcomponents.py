from zoo.libs.maya.mayacommand import command
from zoo.libs.hive import api
from zoo.libs.maya import zapi


class CreateComponents(command.ZooCommandMaya):
    # {"type": "", "name": "", "side": "", "definition": {}}
    id = "hive.rig.create.components"
    isUndoable = True
    isEnabled = True
    useUndoChunk = True
    disableQueue = True

    _rigName = []
    _rig = None
    _components = []
    _parentNode = None  # type: zapi.DagNode

    def resolveArguments(self, arguments):
        rig = arguments.get("rig")
        componentData = arguments.get("components")
        if not componentData:
            self.displayWarning("Must supply component list")
            return
        if rig is None or not isinstance(rig, api.Rig):
            self.displayWarning("Must supply the rig instance to the command")
            return
        if not rig.exists():
            self.displayWarning("Rig does not exist in the scene.")
            return

        selection = list(zapi.selected(filterTypes=zapi.kTransform))
        if selection:
            sel = selection[0]
            arguments["parentNode"] = sel
        self._rig = rig
        self._components = componentData
        self._parentNode = arguments.get("parentNode")

        return arguments

    def doIt(self, rig=None, components=None, buildGuides=False, buildRigs=False, parentNode=None):
        comps = []
        for component in self._components:
            newComponent = rig.createComponent(component["type"], component["name"], component["side"],
                                               definition=component.get("definition"))
            component["name"] = newComponent.name()
            component["side"] = newComponent.side()
            if newComponent:
                comps.append(newComponent)
        if buildGuides:
            self._rig.buildGuides(comps)
            rootGuides = []
            for comp in comps:
                layer = comp.guideLayer()
                root = layer.guideRoot()
                if root is not None:
                    rootGuides.append(root)

            if self._parentNode:
                parentTransform = self._parentNode.translation()
                for comp in comps:
                    root = comp.guideLayer().guideRoot()
                    if root:
                        root.setTranslation(parentTransform, space=zapi.kWorldSpace)

            if rootGuides:
                zapi.select(rootGuides)
        if buildRigs:
            self._rig.buildRigs(comps)
        return comps

    def undoIt(self):
        if self._rig.exists():
            for comp in self._components:
                self._rig.deleteComponent(comp["name"], comp["side"])
