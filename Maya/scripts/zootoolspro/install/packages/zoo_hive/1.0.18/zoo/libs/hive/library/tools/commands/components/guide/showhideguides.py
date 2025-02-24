from zoo.libs.maya.mayacommand import command
from zoo.libs.hive import api
from zoo.libs.maya.api import scene
from maya.api import OpenMaya as om2
from zoo.libs.maya import zapi


class ShowGuidesCommand(command.ZooCommandMaya):
    """Shows all the guides for this component
    """
    id = "hive.component.guide.show"
    description = __doc__
    
    isUndoable = True
    _components = []
    _rig = None

    def resolveArguments(self, arguments):
        components = arguments.get("components")
        rig = arguments.get("rig")
        validComponents = []
        if rig and not components:
            validComponents = list(rig.components())
        else:
            for component in components:
                if not component or not isinstance(components, api.Component):
                    self.displayWarning("Must supply component instance")
                    return
                if not component.hasGuide():
                    continue
                validComponents.append(component)
        self._components = validComponents
        self._rig = arguments.get("rig")
        return arguments

    def doIt(self, rig=None, components=None):
        for component in self._components:
            layer = component.guideLayer()
            if layer is not None:
                layer.show()

    def undoIt(self):
        for component in self._components:
            layer = component.guideLayer()
            if layer is not None:
                layer.hide()


class HideGuidesCommand(command.ZooCommandMaya):
    """Shows all the guides in for this component
    """
    id = "hive.component.guide.hide"
    description = __doc__
    isUndoable = True
    
    _components = []
    _rig = None

    def resolveArguments(self, arguments):
        components = arguments.get("components")
        rig = arguments.get("rig")
        validComponents = []
        if rig and not components:
            validComponents = list(rig.components())
        else:
            for component in components:
                if not component or not isinstance(components, api.Component):
                    self.displayWarning("Must supply component instance")
                    return
                if not component.hasGuide():
                    continue
                validComponents.append(component)
        self._components = validComponents
        self._rig = arguments.get("rig")
        return arguments

    def doIt(self, rig=None, components=None):
        for component in self._components:
            layer = component.guideLayer()
            if layer is not None:
                layer.hide()

    def undoIt(self):
        for component in self._components:
            layer = component.guideLayer()
            if layer is not None:
                layer.show()


class ToggleGuideVisibilityCommand(command.ZooCommandMaya):
    id = "hive.component.guide.toggleVisibility"
    description = __doc__
    
    isUndoable = True

    _rig = None
    _visible = False

    def resolveArguments(self, arguments):
        """ Resolve the rig. Also visible if visible is not given

        :param arguments:
        :type arguments:
        :return:
        :rtype:
        """
        rig = arguments.get("rig")
        if not rig or not isinstance(rig, api.Rig):
            self.displayWarning("Must supply rig instance")
            return
        self._rig = rig

        visible = arguments.get("visible")
        # Get first if toggleChecked is empty
        if not visible:
            arguments['visible'] = rig.configuration.guideControlVisibility
        self._visible = arguments['visible']
        return arguments

    def doIt(self, rig=None, visible=None):
        """ Do it

        :param rig:
        :type rig:
        :param visible:
        :type visible:
        :return:
        :rtype:
        """
        self._toggleVis(rig, visible)

    def undoIt(self):
        """ Undo it

        :return:
        :rtype:
        """
        if self._rig is not None:
            layer = self._rig
            self._toggleVis(layer, not self._visible)

    def _toggleVis(self, rig, visible):
        """

        :param rig:
        :type rig: zoo.libs.hive.base.rig.Rig
        :return:
        :rtype:
        """
        rig.configuration.applySettingsState({"guidePivotVisibility": not visible}, rig=rig)
        rig.saveConfiguration()


class ToggleRigGuideShapeVisibilityCommand(command.ZooCommandMaya):
    id = "hive.component.guide.toggleShapeVisibilityRig"
    description = __doc__
    
    isUndoable = True

    _rig = None
    _visible = False

    def resolveArguments(self, arguments):
        """ Resolve the rig. Also visible if visible is not given

        :param arguments:
        :type arguments:
        :return:
        :rtype:
        """
        rig = arguments.get("rig")
        if not rig or not isinstance(rig, api.Rig):
            self.displayWarning("Must supply rig instance")
            return
        self._rig = rig

        visible = arguments.get("visible")
        # Get first if toggleChecked is empty
        if not visible:
            arguments['visible'] = rig.configuration.guideControlVisibility
        self._visible = arguments['visible']
        return arguments

    def doIt(self, rig=None, visible=None):
        """ Do it

        :param rig:
        :type rig:
        :param visible:
        :type visible:
        :return:
        :rtype:
        """
        self._toggleVis(rig, visible)

    def undoIt(self):
        """ Undo it

        :return:
        :rtype:
        """
        if self._rig is not None:
            layer = self._rig
            self._toggleVis(layer, not self._visible)

    def _toggleVis(self, rig, visible):
        """

        :param rig:
        :type rig: zoo.libs.hive.base.rig.Rig
        :return:
        :rtype:
        """
        rig.configuration.applySettingsState({"guideControlVisibility": not visible}, rig=rig)
        rig.saveConfiguration()


class ToggleRigGuideVisibilityCommand(command.ZooCommandMaya):
    id = "hive.component.guide.toggleVisibilityRig"
    description = __doc__
    
    isUndoable = True

    _rig = None
    _visible = None

    def resolveArguments(self, arguments):
        rig = arguments.get("rig")
        if not rig or not isinstance(rig, api.Rig):
            self.displayWarning("Must supply rig instance")
            return
        self._rig = rig

        # Get first if toggleChecked is empty
        arguments['visible'] = self.rigVisible(rig)
        self._visible = arguments['visible']
        return arguments

    def rigVisible(self, rig):
        """ Returns the visible guide from either:
            - First Component, second guide OR
            - Second Component

        Currently the first should always be on till we put a custom shape so we can still use the marking menu.

        :param rig:
        :type rig:
        :return:
        :rtype:
        """
        return rig.configuration.guidePivotVisibility

    def doIt(self, rig=None, visible=None):
        self._toggleVis(rig, self._visible)

    def undoIt(self):
        if self._rig is not None:
            layer = self._rig
            self._toggleVis(layer, not self._visible)

    def _toggleVis(self, rig, visible):
        """

        :param rig:
        :type rig: zoo.libs.hive.base.rig.Rig
        :return:
        :rtype:
        """
        rig.configuration.applySettingsState({"guidePivotVisibility": not visible}, rig=rig)
        rig.saveConfiguration()



class SetComponentLRACommand(command.ZooCommandMaya):
    """ Sets all LRA shape visibility on the guides for the given components.
    """
    id = "hive.component.guide.lra"
    description = __doc__
    
    isUndoable = True

    _components = []
    _vis = True

    def resolveArguments(self, arguments):
        """ Resolve arguments

        :param arguments:
        :type arguments:
        :return:
        :rtype:
        """
        try:
            _components = arguments["components"]
        except KeyError:
            self.displayWarning("Must Supply Components")
            return

        self._components = _components
        self._vis = arguments.get("visibility", True)
        return arguments

    def doIt(self, components=None, visibility=True):
        """

        :param components: The components to set the LRA on
        :type components: iterable[:class:`zoo.libs.hive.base.component.Component`]
        :return: True if successful
        :rtype: bool
        """
        for comp in self._components:
            self._setDisplayAxisVis(comp, visibility)

    def _setDisplayAxisVis(self, component, vis):
        """Set display axis vis for component"""
        for g in component.guideLayer().iterGuides(includeRoot=False):
            g.setDisplayAxisShapeVis(vis)

    def undoIt(self):
        vis = self._vis
        for comp in self._components:
            self._setDisplayAxisVis(comp, not vis)


class ShowGuidesFromSelectedCommand(command.ZooCommandMaya):
    """Shows all the guides in for this component
    """
    id = "hive.component.guide.selection.show"
    description = __doc__
    
    isUndoable = True

    _components = []

    def resolveArguments(self, arguments):
        selection = arguments.get("nodes")
        if not selection:
            selection = scene.getSelectedNodes()

        if not selection:
            self.displayWarning("Must supply component instance")
            return
        validNodes = set()
        for s in selection:
            if arguments.get("fullRig", False):
                rig = api.rigFromNode(s)
                if not rig:
                    continue
                for comp in rig.components():
                    validNodes.add(comp)
            else:
                try:
                    comp = api.componentFromNode(s)
                except ValueError:
                    continue
                validNodes.add(comp)
        if not validNodes:
            self.displayWarning("No valid components attached to selected nodes")
            return
        arguments.components = list(validNodes)
        self._components = validNodes
        return arguments

    def doIt(self, components=None, fullRig=False):
        """
        :param components: A list of components to show guides for
        :type components: :class:`list`(:class:`zoo.libs.hive.base.component.Component`)
        :return: True if successful
        :rtype: bool
        """

        for i in self._components:
            layer = i.guideLayer().rootTransform()
            layer.show()
        return True

    def undoIt(self):
        for i in self._components:
            layer = i.guideLayer().rootTransform()
            layer.hide()


class HideGuidesFromSelectedCommand(command.ZooCommandMaya):
    """Shows all the guides in for this component
    """
    id = "hive.component.guide.selection.hide"
    description = __doc__
    isUndoable = True
    

    _components = []

    def resolveArguments(self, arguments):
        selection = arguments.get("nodes")
        if not selection:
            selection = scene.getSelectedNodes()

        if not selection:
            self.displayWarning("Must supply component instance")
            return
        validNodes = set()
        for s in selection:
            try:
                comp = api.componentFromNode(zapi.nodeByObject(s))
            except ValueError:
                continue
            validNodes.add(comp)
        if not validNodes:
            self.displayWarning("No valid components attached to selected nodes")
            return
        arguments.components = list(validNodes)
        self._components = validNodes
        return arguments

    def doIt(self, components=None):
        """
        :param components: A list of components to show guides for
        :type components: :class:`list`(:class:`zoo.libs.hive.base.component.Component`)
        :return: True if successful
        :rtype: bool
        """

        for i in self._components:
            layer = i.guideLayer().rootTransform()
            layer.hide()
        return True

    def undoIt(self):
        for i in self._components:
            layer = i.guideLayer().rootTransform()
            layer.show()


class ToggleGuideVisibilityFromSelectedCommand(command.ZooCommandMaya):
    """Shows all the guides in for this component
    """
    id = "hive.component.guide.selection.toggleVisibility"
    isUndoable = True
    _components = []

    def resolveArguments(self, arguments):
        selection = arguments.get("nodes")
        if not selection:
            selection = scene.getSelectedNodes()
        if not selection:
            self.displayWarning("Must supply at least one selected node")
            return
        validNodes = set()
        for s in selection:
            s = s if isinstance(s, om2.MObject) else s.object()
            try:
                comp = api.componentFromNode(zapi.nodeByObject(s))
            except ValueError:
                continue
            validNodes.add(comp)
        if not validNodes:
            self.displayWarning("No valid components attached to selected nodes")
            return
        arguments.components = list(validNodes)
        self._components = validNodes
        return arguments

    def doIt(self, components=None):
        """
        :param components: A list of components to show guides for
        :type components: :class:`list`(:class:`zoo.libs.hive.base.component.Component`)
        :return: True if successful
        :rtype: bool
        """

        for i in self._components:
            layer = i.guideLayer().rootTransform()
            self._toggleVis(layer)
        return True

    def undoIt(self):
        for i in self._components:
            layer = i.guideLayer().rootTransform()
            self._toggleVis(layer)

    def _toggleVis(self, layer):
        if layer.isHidden():
            layer.show()
            return
        layer.hide()
