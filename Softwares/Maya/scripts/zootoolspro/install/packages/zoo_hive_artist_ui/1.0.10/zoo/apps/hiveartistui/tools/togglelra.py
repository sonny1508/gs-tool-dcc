from zoo.apps.hiveartistui import hivetool
from zoo.libs.commands import hive


class ToggleLRATool(hivetool.HiveTool):
    id = "toggleLra"
    uiData = {
        "icon": "axis",
        "label": "Toggle LRA"
    }

    def execute(self):
        componentModel = self.selectedComponents()[0]
        component = componentModel.component
        guideLayer = component.guideLayer()
        if guideLayer is not None:
            for g in guideLayer.iterGuides(includeRoot=False):
                hive.setGuideLRA(components=[componentModel.component], visibility=not g.displayAxisShapeVis())
                break





