import logging

from zoo.libs.hive import api
from zoo.libs.maya import zapi
from zoo.libs.maya.mayacommand import command

logger = logging.getLogger(__name__)


class MirrorGuidesCommand(command.ZooCommandMaya):
    """Mirrors the components guides
    """
    id = "hive.component.guide.mirror"
    
    isUndoable = True
    disableQueue = True
    isEnabled = True
    _originalComponents = []
    _currentSelection = []
    _rig = None
    _newComponents = []
    _transformedData = []

    def resolveArguments(self, arguments):
        super(MirrorGuidesCommand, self).resolveArguments(arguments)
        components = arguments.get("components")
        if not components:
            self.displayWarning("At least one component must be specified")
        self._rig = arguments.rig
        visited = set()
        parsed = []
        for compInfo in components:
            comp = compInfo["component"]
            if comp in visited:
                continue
            visited.add(comp)
            rotate = compInfo.get("rotate", "yz")
            if not isinstance(comp, api.Component):
                self.displayWarning("Component instance must be supplied to the command: {}".format(comp))
                return
            if rotate not in ("xy", "yz", "xz"):
                self.displayWarning(
                    "Value for argument 'rotate':{} must be one of the following, 'xy', 'yz', 'xz'".format(rotate))
                return
            duplicate = compInfo.get("duplicate", False)
            translate = compInfo.get("translate", ("x",))
            side = compInfo.get("side")
            parsed.append(dict(component=comp,
                               duplicate=duplicate,
                               translate=translate,
                               rotate=rotate,
                               side=side))

            for child in comp.children():
                if child in visited:
                    continue
                visited.add(child)
                parsed.append(dict(
                    component=child,
                    duplicate=duplicate,
                    translate=translate,
                    rotate=rotate,
                    side=side
                ))
        self._currentSelection = list(zapi.selected())
        self._originalComponents = parsed
        return arguments

    def doIt(self, rig=None, components=None):
        mirrorResult = rig.mirrorComponents(self._originalComponents)

        self._transformedData = mirrorResult["transformData"]
        self._newComponents = mirrorResult["newComponents"]
        api.alignGuides(rig, mirrorResult["newComponents"])
        # find the parent for selection
        selectables = []
        for comp in self._newComponents:
            parent = comp.parent()
            if parent is None or parent not in self._newComponents:
                selectables.append(comp.guideLayer().guideRoot())
        if selectables:
            zapi.select(selectables)
        return True

    def undoIt(self):
        if self._newComponents:
            for comp in self._newComponents:
                self._rig.deleteComponent(comp.name(), comp.side())
        else:
            for t in iter(self._transformedData):
                t["node"].setWorldMatrix(t["transform"].asMatrix())
        zapi.select(self._currentSelection)
