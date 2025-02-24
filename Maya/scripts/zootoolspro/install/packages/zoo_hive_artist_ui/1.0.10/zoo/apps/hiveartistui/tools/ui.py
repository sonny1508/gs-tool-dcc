import maya.api.OpenMaya as om2
from maya import cmds

from zoo.apps.hiveartistui import hivetool
from zoo.core.util import zlogging
from zoo.libs.hive import api
from zoovendor.Qt import QtCore

logger = zlogging.getLogger(__name__)


class MaximizeComponentTool(hivetool.HiveTool):
    id = "maximizeComponent"
    uiData = {
        "icon": "maximise",
        "label": "Maximize Component"
    }

    def execute(self):
        self.uiInterface.tree().maximizeSelected()


class MaximizeAllComponentsTool(hivetool.HiveTool):
    id = "maximizeAllComponents"
    uiData = {
        "icon": "maximise",
        "label": "Maximize All Components"
    }

    def execute(self):
        self.uiInterface.tree().maximizeAll()


class MinimizeComponentTool(hivetool.HiveTool):
    id = "minimizeComponent"
    uiData = {
        "icon": "minimise",
        "label": "Minimize Component"
    }

    def execute(self):
        self.uiInterface.tree().minimizeSelected()


class MinimizeAllComponentsTool(hivetool.HiveTool):
    id = "minimizeAllComponents"
    uiData = {
        "icon": "minimise",
        "label": "Minimize All Components"
    }

    def execute(self):
        self.uiInterface.tree().minimizeAll()


class GroupComponentsTool(hivetool.HiveTool):
    id = "groupComponents"
    uiData = {
        "icon": "openFolder01",
        "label": "Group Components"
    }

    def execute(self):
        self.uiInterface.tree().groupActionTriggered()


class HighlightFromSceneTool(hivetool.HiveTool):
    id = "highlightFromScene"
    uiData = {
        "icon": "cursorWindow",
        "label": "Highlight From Scene"
    }

    def execute(self):
        from zoo.apps.hiveartistui.views import componentwidget

        sceneComponents = api.componentsFromSelected()

        tree = self.uiInterface.tree()
        tree.clearSelection()
        for r in range(tree.model().rowCount()):
            index = tree.model().index(r, 0)
            widget = tree.indexWidget(index)

            if isinstance(widget, componentwidget.ComponentWidget) and widget.model.component in sceneComponents:
                tree.selectionModel().select(index, QtCore.QItemSelectionModel.SelectionFlag.Select)
                tree.scrollTo(index)


class SelectInSceneTool(hivetool.HiveTool):
    id = "selectInScene"
    uiData = {
        "icon": "cursorSelect",
        "label": "Select In Scene"
    }

    def execute(self):
        components = [c.component for c in self.selectedComponents()]
        if not components:
            om2.MGlobal.displayWarning("Must select component in ui")
            return

        select = []
        for c in components:
            if c.guideLayer():
                select.append(c.guideLayer().guideRoot().fullPathName())
            elif c.rigLayer():
                select += [c.fullPathName() for c in c.rigLayer().iterControls()]
        cmds.select(select)


class SelectAllTool(hivetool.HiveTool):
    id = "selectAll"
    uiData = {
        "icon": "selectAll",
        "label": "Select All"
    }

    def execute(self):
        self.uiInterface.tree().selectAll()


class InvertSelectionTool(hivetool.HiveTool):
    id = "invertSelection"
    uiData = {
        "icon": "invert",
        "label": "Invert Selection"
    }

    def execute(self):
        from zoo.apps.hiveartistui.views import componentwidget
        currentSelection = self.selectedModels

        tree = self.uiInterface.tree()
        tree.clearSelection()
        for r in range(tree.model().rowCount()):
            index = tree.model().index(r, 0)
            widget = tree.indexWidget(index)

            if isinstance(widget, componentwidget.ComponentWidget) and widget.model not in currentSelection:
                tree.selectionModel().select(index, QtCore.QItemSelectionModel.SelectionFlag.Select)