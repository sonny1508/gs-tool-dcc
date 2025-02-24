from zoo.libs.maya.mayacommand import command


class DeleteComponentCommand(command.ZooCommandMaya):
    id = "hive.component.delete"

    isUndoable = True
    isEnabled = True
    useUndoChunk = True
    disableQueue = True
    _serializedComponentData = []
    _components = []
    _rig = None

    def resolveArguments(self, arguments):
        self._serializedComponentData = []
        for comp in arguments["components"]:
            self._serializedComponentData.append((comp.serializeFromScene(),
                                                  comp.hasGuide(),
                                                  comp.hasSkeleton(),
                                                  comp.hasRig()))
        self._rig = arguments["rig"]
        self._components = arguments["components"]
        if arguments["children"]:
            childComponents = []
            for component in self._components:
                children = list(component.children())
                childComponents.extend(children)
            self._components.extend(childComponents)

        return arguments

    def doIt(self, rig=None, components=None, children=True):
        for comp in self._components:
            self._rig.deleteComponent(name=comp.name(), side=comp.side())

    def undoIt(self):
        self._components = []
        if self._rig is not None and self._rig.exists():
            guidesToBuild = []
            rigsToBuild = []
            skeletonsToBuild = []
            for data, guide, skel, rig in self._serializedComponentData:
                comp = self._rig.createComponent(data["type"], data["name"], data["side"],
                                                 definition=data)

                if guide:
                    guidesToBuild.append(comp)
                if skel:
                    skeletonsToBuild.append(comp)
                if rig:
                    rigsToBuild.append(comp)
                self._components.append(comp)
            if guidesToBuild:
                self._rig.buildGuides(guidesToBuild)
            if skeletonsToBuild:
                self._rig.buildDeform(skeletonsToBuild)
            if rigsToBuild:
                self._rig.buildRig(rigsToBuild)
