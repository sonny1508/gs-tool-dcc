from zoo.libs.maya.mayacommand import command
from zoo.libs.hive import api


class ShowRigCommand(command.ZooCommandMaya):
    """Shows all the guides in for this rig
    """
    id = "hive.rig.show"

    isUndoable = True

    _rig = None

    def resolveArguments(self, arguments):
        rig = arguments.get("rig")

        if not rig or not isinstance(rig, api.Rig):
            self.displayWarning("Must supply rig instance ")
            return
        self._rig = rig
        return arguments

    def doIt(self, rig=None):
        for comp in rig.components():
            if comp.hasRig():
                comp.rigLayer().show()

    def undoIt(self):
        if self._rig is not None:
            for comp in self._rig.components():
                if comp.hasRig():
                    comp.rigLayer().show()


class HideRigCommand(command.ZooCommandMaya):
    """Hides all the guides in for this rig
    """
    id = "hive.rig.hide"
    isUndoable = True


    _rig = None

    def resolveArguments(self, arguments):
        rig = arguments.get("rig")

        if not rig or not isinstance(rig, api.Rig):
            self.displayWarning("Must supply rig instance ")
            return
        self._rig = rig
        return arguments

    def doIt(self, rig=None):
        for comp in rig.components():
            if comp.hasRig():
                comp.rigLayer().hide()

    def undoIt(self):
        if self._rig is not None:
            for comp in self._rig.components():
                if comp.hasRig():
                    comp.rigLayer().show()


class ToggleRigVisibilityCommand(command.ZooCommandMaya):
    """toggles all the guides in for this rig
    """
    id = "hive.rig.toggleVisibility"
    isUndoable = True
    _rig = None

    def resolveArguments(self, arguments):
        rig = arguments.get("rig")

        if not rig or not isinstance(rig, api.Rig):
            self.displayWarning("Must supply rig instance ")
            return
        self._rig = rig
        return arguments

    def doIt(self, rig=None):
        for comp in rig.components():
            if comp.hasRig():
                layer = comp.rigLayer()
                self._toggleVis(layer)

    def undoIt(self):
        if self._rig is not None:
            for comp in self._rig.components():
                if comp.hasRig():
                    self._toggleVis(comp.rigLayer())

    def _toggleVis(self, layer):
        if layer.isHidden():
            layer.show()
            return
        layer.hide()


class HideShowDeformVisibilityCommand(command.ZooCommandMaya):
    """Shows or hides deformation rig
    """
    id = "hive.rig.showHideDeform"
    isUndoable = True

    _rig = None
    _state = False

    def resolveArguments(self, arguments):
        rig = arguments.get("rig")
        self._state = arguments.get("state")
        if not rig or not isinstance(rig, api.Rig):
            self.displayWarning("Must supply rig instance ")
            return
        self._rig = rig
        return arguments

    def doIt(self, rig=None, state=False):
        layer = rig.deformLayer()
        rootTransform = layer.rootTransform()
        rootTransform.attribute("visibility").set(state)
        for comp in rig.components():  # type: api.Component
            if comp.hasSkeleton():
                layer = comp.deformLayer()
                rootTransform = layer.rootTransform()
                rootTransform.attribute("visibility").set(state)

    def undoIt(self):
        if self._rig is not None:
            layer = self._rig.deformLayer()
            rootTransform = layer.rootTransform()
            rootTransform.attribute("visibility").set(not self._state)
            for comp in self._rig.components():
                layer = comp.deformLayer()
                rootTransform = layer.rootTransform()
                rootTransform.attribute("visibility").set(not self._state)

