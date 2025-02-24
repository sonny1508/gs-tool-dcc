from zoo.apps.hiveartistui import hivetool
from zoo.core.util import zlogging
from zoo.libs.hive.library.tools.toolui import mirrorwidget
from zoo.libs.hive import api
from zoo.libs.utils import output

logger = zlogging.getLogger(__name__)


class MirrorComponentsTool(hivetool.HiveTool):
    id = "mirrorComponents"
    uiData = {
        "icon": "mirrorComponent",
        "label": "Mirror Selected Components"
    }
    _originalSettings = dict(translate=("x",), rotate="yz", parent=None,
                             side="r", duplicate=True)

    def execute(self, duplicate=True, allComponents=False):
        comps = []
        rig = self.rigModel.rig
        if allComponents:
            components = rig.components()
        else:
            components = [c.component for c in self.selectedModels]

        for c in components:
            arguments = dict(**self._originalSettings)
            arguments["component"] = c
            arguments["duplicate"] = duplicate
            comps.append(arguments)
        win = mirrorwidget.launchMirrorWidget(comps, parent=self.parentWidget)
        win.onFinishedMirroring.connect(self.requestRefresh)

    def variants(self):
        v = [
            {"id": "selected",
             "name": "Mirror Selected Components", "icon": "mirrorComponent",
             "args": {}},
            {"id": "all",
             "name": "Mirror All Components", "icon": "mirrorComponent",
             "args": {"allComponents": True}},
            {"id": "duplicate",
             "name": "Mirror & Duplicate Selected Components", "icon": "mirrorComponent",
             "args": {"duplicate": True}}

        ]
        return v


class SymmetrizeComponentTool(hivetool.HiveTool):
    id = "applySymmetry"
    uiData = {
        "icon": "symmetryTri",
        "label": "Symmetrize Component"
    }

    def execute(self):
        rig = self.rigModel.rig

        components = [c.component for c in self.selectedModels]
        if not components:
            return
        api.commands.applySymmetry(rig, components)
        output.displayInfo("Success: Applied Symmetry")