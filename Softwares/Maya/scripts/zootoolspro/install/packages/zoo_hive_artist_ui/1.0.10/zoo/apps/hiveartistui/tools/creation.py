from zoo.apps.hiveartistui import hivetool, utils
from zoo.core.util import zlogging
from zoo.libs.commands import hive

logger = zlogging.getLogger(__name__)


class CreateComponent(hivetool.HiveTool):
    id = "createComponent"
    uiData = {"icon": "add",
              "label": "Create Component"}

    def execute(self, componentType, name, side, definition=None):
        if not self.rigModel:
            return
        success = utils.checkSceneUnits(parent=self.uiInterface.artistUi())
        if not success:
            return
        if definition is not None:
            side = definition.get("side", side)
            name = definition.get("name", name)
        components = hive.createComponents(self.rigModel.rig,
                                           components=[{"type": componentType,
                                                        "name": name,
                                                        "side": side,
                                                        "definition": definition
                                                        }],
                                           buildGuides=True)

        self.requestRefresh(False)
        if components:
            return components[0]


class CreateRig(hivetool.HiveTool):
    id = "createRig"
    uiData = {"icon": "add",
              "label": "Create rig instance"}

    def execute(self, name):
        success = utils.checkSceneUnits(parent=self.uiInterface.artistUi())
        if not success:
            return

        r = hive.createRig(name=name)
        self.requestRefresh(False)
        return r


class DeleteRig(hivetool.HiveTool):
    id = "deleteRig"
    uiData = {"icon": "add",
              "label": "Delete rig instance"}

    def execute(self, rig=None):
        if not self.rigModel:
            return

        hive.deleteRig(rig=rig or self.rigModel.rig)
        self.requestRefresh(False)


class DeleteComponent(hivetool.HiveTool):
    id = "deleteComponent"
    uiData = {"icon": "trash",
              "label": "Delete Components"}

    def execute(self):
        if not self.rigModel:
            return
        selection = self.selectedModels
        if not selection:
            return
        r = self.rigModel.rig
        r.clearComponentCache()
        hive.deleteComponents(r, [i.component for i in selection])
        self.requestRefresh(False)


class DeleteAllComponents(hivetool.HiveTool):
    id = "deleteAllComponents"
    uiData = {"icon": "trash",
              "label": "Delete All"}

    def execute(self):
        r = self.rigModel.rig
        r.clearComponentCache()
        components = self.rigModel.rig.components()
        if not components:
            return

        hive.deleteComponents(r, components)


class DuplicateComponent(hivetool.HiveTool):
    id = "duplicateComponent"
    uiData = {"icon": "duplicate",
              "label": "Duplicate Components"}

    def execute(self):
        if not self.rigModel:
            return
        compInfo = []
        for sel in self.selectedModels:
            comp = sel.component
            compInfo.append({"component": comp,
                             "name": comp.name(),
                             "side": comp.side()})
        r = self.rigModel.rig
        r.clearComponentCache()
        hive.duplicateComponents(r,
                                 sources=compInfo
                                 )
        self.requestRefresh(False)


class BuildGuides(hivetool.HiveTool):
    id = "buildGuides"
    uiData = {"icon": "add",
              "label": "Builds all guides on the rig"}

    def execute(self):
        if not self.rigModel:
            return
        success = utils.checkSceneUnits(parent=self.uiInterface.artistUi())
        if not success:
            return
        r = self.rigModel.rig
        r.clearComponentCache()
        hive.buildGuides(rig=r)
        self.requestRefresh(False)


class BuildGuideControls(hivetool.HiveTool):
    id = "buildGuideControls"
    uiData = {"icon": "add",
              "label": "Builds all guides controls on the rig"}

    def execute(self):
        if not self.rigModel:
            return
        success = utils.checkSceneUnits(parent=self.uiInterface.artistUi())
        if not success:
            return
        r = self.rigModel.rig
        r.clearComponentCache()
        hive.buildGuideControls(r)
        self.requestRefresh(False)

class BuildSkeleton(hivetool.HiveTool):
    id = "buildSkeleton"
    uiData = {"icon": "add",
              "label": "Builds skeleton for rig"}

    def execute(self):
        if not self.rigModel:
            return
        r = self.rigModel.rig
        r.clearComponentCache()
        hive.buildDeform(rig=r)
        self.requestRefresh(False)


class BuildRig(hivetool.HiveTool):
    id = "buildRig"
    uiData = {"icon": "add",
              "label": "Builds all the component rigs on the rig"}

    def execute(self):
        if not self.rigModel:
            return
        r = self.rigModel.rig
        r.clearComponentCache()
        hive.buildRigs(r)


class PolishRig(hivetool.HiveTool):
    id = "polishRig"
    uiData = {"icon": "add",
              "label": "Polish Rig"}

    def execute(self):
        if not self.rigModel:
            return
        r = self.rigModel.rig
        r.clearComponentCache()
        polished = hive.polishRig(rig=r)
        if polished:
            self.requestRefresh(False)
