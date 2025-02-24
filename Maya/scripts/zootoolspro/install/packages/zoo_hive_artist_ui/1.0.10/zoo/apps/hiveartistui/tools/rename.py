from zoo.apps.hiveartistui import hivetool
from zoo.libs.commands import hive
from zoo.libs.pyqt.widgets import elements


class RenameTool(hivetool.HiveTool):
    id = "renameRig"
    uiData = {
        "icon": "pencil",
        "label": "Rename Rig"
    }

    def execute(self):
        if self.rigExists():
            return
        text = elements.MessageBox.inputDialog(self.parentWidget,
                                               title='Rename Rig',
                                               message='Enter new rig Name:',
                                               text=self.rigModel.name)
        if text is None:
            return

        if text != self.rigModel.name:
            hive.renameRig(self.rigModel.rig, str(text))

        self.requestRefresh()
        self.parentWidget.updateRigName()


class SetComponentSide(hivetool.HiveTool):
    id = "setComponentSide"
    uiData = {"icon": "solo",
              "label": "Set Component Side"}

    def execute(self, side, componentModel=None):
        if not self._rigModel:
            return
        model = componentModel or self.selectedComponents()[0]
        model.side = side
        self.requestRefresh()
        self.refreshComponents([model])
