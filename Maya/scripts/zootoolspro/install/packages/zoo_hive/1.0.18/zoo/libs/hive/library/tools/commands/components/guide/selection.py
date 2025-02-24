from zoo.libs.hive import api as hiveapi
from zoo.libs.maya.mayacommand import command
from zoo.libs.maya.api import scene, nodes
from maya import cmds

from maya.api import OpenMaya as om2


class SelectGuidePivotCommand(command.ZooCommandMaya):
    """Select's The component guide pivot transforms
    """
    id = "hive.component.guide.select.pivot"
    
    isUndoable = True
    isEnabled = True
    _oldSelection = om2.MSelectionList()

    def resolveArguments(self, arguments):
        super(SelectGuidePivotCommand, self).resolveArguments(arguments)
        # first check if the client passed in components
        comps = arguments.get("components", [])
        if not comps:
            # ok no components , what about selection?
            selection = scene.getSelectedNodes()
            for mobj in selection:
                component = hiveapi.componentFromNode(mobj)
                # ok we have a component but we only operate on the guides so check
                if component and component.hasGuide():
                    comps.append(component)
            if not comps:
                self.displayWarning("No components found!")
                return
        else:
            newComps = []
            for comp in comps:
                if comp.hasGuide():
                    newComps.append(comp)
            return {"components": newComps}
        return {"components": comps}

    def doIt(self, components=None):
        self._oldSelection = om2.MGlobal.getActiveSelectionList()
        newSelection = set()
        for component in components:
            for guide in component.guideLayer().iterGuides():
                newSelection.add(guide.fullPathName())
        if newSelection:
            cmds.select(list(newSelection), replace=True)

    def undoIt(self):
        if self._oldSelection.length() > 0:
            cmds.select([nodes.nameFromMObject(i.object()) for i in self._oldSelection], deselect=True)


class SelectAllGuideShapesCommand(command.ZooCommandMaya):
    """Select's The component guide shape transforms
    """
    id = "hive.component.guide.selectAll.shapes"
    
    isUndoable = True
    isEnabled = True
    _oldSelection = om2.MSelectionList()

    def resolveArguments(self, arguments):
        super(SelectAllGuideShapesCommand, self).resolveArguments(arguments)
        # first check if the client passed in components
        comps = arguments.get("components", [])
        if not comps:
            # ok no components , what about selection?
            selection = scene.getSelectedNodes()
            for mobj in selection:
                component = hiveapi.componentFromNode(mobj)
                # ok we have a component but we only operate on the guides so check
                if component and component.hasGuide():
                    comps.append(component)
            if not comps:
                self.displayWarning("No components found!")
                return
        else:
            newComps = []
            for comp in comps:
                if comp.hasGuide():
                    newComps.append(comp)
            return {"components": newComps}
        return {"components": comps}

    def doIt(self, components=None):
        self._oldSelection = om2.MGlobal.getActiveSelectionList()
        newSelection = set()
        for component in components:
            for guide in component.guideLayer().iterGuides():
                shapeNode = guide.shapeNode()
                if shapeNode:
                    newSelection.add(shapeNode.fullPathName())
        if newSelection:
            cmds.select(list(newSelection), replace=True)

    def undoIt(self):
        if self._oldSelection.length() > 0:
            names = [nodes.nameFromMObject(self._oldSelection.getDependNode(i))
                     for i in range(self._oldSelection.length())]
            cmds.select(names, deselect=True)


class SelectGuideShapesCommand(command.ZooCommandMaya):
    """Select's The component guide shape transforms
    """
    id = "hive.component.guide.select.shapes"
    
    isUndoable = True
    isEnabled = True

    _oldSelection = om2.MSelectionList()

    def resolveArguments(self, arguments):
        super(SelectGuideShapesCommand, self).resolveArguments(arguments)
        # first check if the client passed in components
        guides = arguments.get("guides", [])
        if not guides:
            for mobj in scene.getSelectedNodes():
                if hiveapi.Guide.isGuide(hiveapi.nodeByObject(mobj.object())):
                    guides.append(hiveapi.Guide(mobj.object()))

        if not guides:
            self.displayWarning("No guides found!")
            return
        self._oldSelection = om2.MGlobal.getActiveSelectionList()
        return {"guides": guides}

    def doIt(self, guides=None):
        newSelection = set()
        for guide in guides:
            shapeNode = guide.shapeNode()
            if shapeNode:
                newSelection.add(shapeNode.fullPathName())
        if newSelection:
            cmds.select(list(newSelection), replace=True)

    def undoIt(self):
        if self._oldSelection.length() > 0:
            cmds.select([nodes.nameFromMObject(i.object()) for i in self._oldSelection], deselect=True)


class SelectGuideRootsCommand(command.ZooCommandMaya):
    """Select's The component guide root pivots
    """
    id = "hive.component.guide.select.rootPivots"
    
    isUndoable = True
    isEnabled = True
    _oldSelection = om2.MSelectionList()

    def resolveArguments(self, arguments):
        super(SelectGuideRootsCommand, self).resolveArguments(arguments)
        # first check if the client passed in components
        comps = arguments.get("components", [])
        selection = scene.getSelectedNodes()
        self._oldSelection = map(om2.MObjectHandle, selection)
        if not comps:
            # ok no components , what about selection?
            for mobj in selection:
                component = hiveapi.componentFromNode(mobj)
                # ok we have a component but we only operate on the guides so check
                if component and component.hasGuide():
                    comps.append(component)
            if not comps:
                self.displayWarning("No components found!")
                return
        else:
            newComps = []
            for comp in comps:
                if comp.hasGuide():
                    newComps.append(comp)
            return {"components": newComps}
        return {"components": comps}

    def doIt(self, components=None):

        newSelection = set()
        for component in components:
            root = component.guideLayer().guideRoot()
            if root is not None:
                newSelection.add(root.fullPathName())
        if newSelection:
            cmds.select(list(newSelection), replace=True)

    def undoIt(self):
        if self._oldSelection:
            cmds.select([nodes.nameFromMObject(i.object()) for i in self._oldSelection], deselect=True)
