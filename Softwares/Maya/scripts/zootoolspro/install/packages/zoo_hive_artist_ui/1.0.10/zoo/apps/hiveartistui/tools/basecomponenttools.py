
from zoo.apps.hiveartistui import hivetool

from zoo.libs.commands import hive
from zoo.libs.maya.utils import general


class SoloComponent(hivetool.HiveTool):
    id = "soloComponent"
    uiData = {"icon": "solo",
              "label": "Solo Component"}

    def execute(self):
        if not self._rigModel:
            return
        selectedComponents = [i.component for i in self.selectedModels]
        if not selectedComponents:
            return

        componentsToShow = []
        componentsToHide = []
        for component in self._rigModel.rig.iterComponents():
            if component in selectedComponents:
                componentsToShow.append(component)
            else:
                componentsToHide.append(component)

        if componentsToHide or componentsToShow:
            with general.undoContext("HiveIsolateSelected"):
                if componentsToHide:
                    hive.hideComponents(componentsToHide)
                if componentsToShow:
                    hive.showComponents(componentsToShow)


class UnSoloComponent(hivetool.HiveTool):
    id = "unSoloComponentAll"
    uiData = {"icon": "solo",
              "label": "UnSolo Component"}

    def execute(self):
        if not self._rigModel:
            return
        componentsToShow = []
        for component in self._rigModel.rig.iterComponents():
            if component.isHidden():
                componentsToShow.append(component)

        if componentsToShow:
            hive.showComponents(componentsToShow)


class ToggleGuidePivotVisibility(hivetool.HiveTool):
    id = "toggleGuidePivotVisibility"
    uiData = {"icon": "eye",
              "iconToggle": "eye",
              "iconColorToggled": (96, 96, 96),
              "label": "Toggle Guide Pivots"}

    def execute(self):
        if not self._rigModel:
            return
        state = False
        for comp in self._rigModel.rig.iterComponents():
            if not comp.hasGuide():
                return
            layer = comp.guideLayer()
            if layer is None:
                return
            state = not layer.isGuidesVisible()

        settings = {"guidePivotVisibility": state}

        hive.updateRigConfiguration(self.rigModel.rig,
                                    settings=settings)
        self.requestRefresh()


class ToggleGuideShapeVisibility(hivetool.HiveTool):
    id = "toggleGuideShapeVisibility"
    uiData = {"icon": "eye",
              "iconToggle": "eye",
              "iconColorToggled": (96, 96, 96),
              "label": "Toggle Guide Controls"}

    def execute(self, state=None):
        # if state was overridden by the UI then force the state to hive
        if state is None:
            state = False
            for comp in self._rigModel.rig.iterComponents():
                if not comp.hasGuide():
                    return
                layer = comp.guideLayer()
                if layer is None:
                    return
                state = not layer.isGuideControlVisible()
        settings = {"guideControlVisibility": bool(state)}
        hive.updateRigConfiguration(self.rigModel.rig,
                                    settings=settings)


class BlackBoxToggle(hivetool.HiveTool):
    id = "toggleBlackToggle"
    uiData = {"icon": "blackBox",
              "label": "Toggle BlackBox"}

    def execute(self):
        if not self._rigModel:
            return
        hive.toggleBlackBox([model.component for model in self.selectedComponents()])


class SetComponentParent(hivetool.HiveTool):
    id = "setComponentParent"
    uiData = {
        "icon": "",
        "label": "Set Parent of Component"
    }

    def execute(self, parentComponent=None, parentGuide=None, childComponent=None):
        """ Sets the parent

        :param parentComponent:
        :type parentComponent: zoo.libs.hive.base.component.Component
        :param parentGuide:
        :type parentGuide: zoo.libs.hive.base.hivenodes.hnodes.Guide
        :param childComponent:
        :type childComponent: zoo.libs.hive.base.component.Component

        :return:
        :rtype:
        """
        hive.setComponentParent(parentComponent=parentComponent, parentGuide=parentGuide,
                                childComponent=childComponent)
