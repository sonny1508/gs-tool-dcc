from zoo.libs.maya.mayacommand import command
from zoo.libs.maya import zapi
from zoo.libs.hive import api


class AlignGuides(command.ZooCommandMaya):
    """Realigns all guides based on auto align settings on the guide node.
    Implementation of auto align is on the component instance.
    """
    id = "hive.components.guides.alignGuides"
    
    isUndoable = True
    isEnabled = True
    useUndoChunk = True  # Chunk all operations in doIt()
    disableQueue = True  # If true, disable the undo queue in doIt()
    _changes = []

    def resolveArguments(self, arguments):

        requestedComponents = arguments.get("components")
        if not requestedComponents:
            self.displayWarning("Command requires component instances to be provided")
            return
        validComponents = []

        for component in requestedComponents:
            if not component.hasGuide():
                continue
            guideLayer = component.guideLayer()
            if not guideLayer.guideSettings().manualOrient.value():
                validComponents.append(component)
        if not validComponents:
            self.displayWarning("No Valid components with auto align support provided")
            return
        arguments["components"] = validComponents
        return arguments

    def doIt(self, components=None):
        """
        :param components: The list of hive components which support twists.
        :type components: list[:class:`api.Component`]
        """
        rig = None
        for component in components:
            guideLayer = component.guideLayer()
            rig = component.rig
            changes = []
            for guide in guideLayer.iterGuides(includeRoot=False):
                for srt in guide.iterSrts():
                    changes.append({"node": srt, "translation": srt.translation(),
                                    "rotation": srt.rotation(zapi.kWorldSpace)})
                changes.append({"node": guide, "translation": guide.translation(),
                                "rotation": guide.rotation(zapi.kWorldSpace)})
            self._changes.append((component, changes))
        api.alignGuides(rig, components)

    def undoIt(self):
        for component, changes in self._changes:
            with component.disconnectComponentContext():
                for change in changes:
                    guide = change["node"]
                    if not guide.exists():
                        continue
                    guide.setTranslation(change["translation"], zapi.kWorldSpace)
                    guide.setRotation(change["rotation"])
