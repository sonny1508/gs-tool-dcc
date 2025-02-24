import contextlib
import json
from collections import OrderedDict

from maya.api import OpenMaya as om2

from zoo.libs.hive import constants
from zoo.libs.hive.base import configuration
from zoo.libs.hive.base import errors
from zoo.libs.hive.base import hivenodes
from zoo.libs.hive.base import naming
from zoo.libs.hive.base import definition as baseDef
from zoo.libs.hive.base.util import componentutils, templateutils
from zoo.libs.maya.meta import base
from zoo.libs.maya import zapi
from zoo.libs.maya.utils import general as mayageneral
from zoo.libs.utils import filesystem
from zoo.libs.utils import profiling
from zoo.core.util import zlogging
from zoo.libs.utils import general
from zoo.core import api as zooapi

if general.TYPE_CHECKING:
    from zoo.libs.naming import naming as namingutils
    from zoo.libs.hive.base import component

logger = zlogging.getLogger(__name__)


class Rig(object):
    """Main entry class for any given rig, The class allows for the construction and deconstruction of component
    every rig will have a root node and a meta node. when the first component is built a component layer node
    wil be generated this is a child of the root and will contain all built components.

    .. code-block:: python

        r = Rig()
        r.startSession("PrototypeRig")
        r.components()
        # result: []
        proto = r.createComponent("EmptyComponent", "Prototype", "M")
        print proto
        # result: zoo.libs.hive.library.components.EmptyComponent
        r.components()
        r.rename("NewRig")

    :param config:  The local configuration to use for this rig
    :type config: :class:`configuration.Configuration` or None
    :param meta: The root hive meta node to use for this rig
    :type meta: :class:`hivenodes.HiveRig` or None
    """

    def __init__(self, config=None, meta=None):
        self._meta = meta
        # used to store a cache of the current rig component instances
        self.componentCache = set()
        if config is None:
            # local import this configuration imports rig , eek
            config = configuration.Configuration()
        self.configuration = config  # type: configuration.Configuration
        # so the client code has easy access to the application version(maya)
        self.applicationVersion = om2.MGlobal.mayaVersion()
        self._hiveVersion = ""

    @property
    def hiveVersion(self):
        """Returns the Current rigs hive version it was built in.

        :return: The hive version ie. 1.0.0
        :rtype: str
        """
        v = self._hiveVersion
        if v:
            return v
        hivePackage = zooapi.currentConfig().resolver.packageByName("zoo_hive")
        self._hiveVersion = str(hivePackage.version)
        return self._hiveVersion

    @property
    def meta(self):
        """Returns the meta Node class for this rig Instance.

        :return: The meta node that represents this rig instance.
        :rtype: :class:`hivenodes.HiveRig`
        """
        return self._meta

    @property
    def blackBox(self):
        """Returns True if any component is currently set to a blackbox.

        :rtype: bool
        """
        return any(i.blackBox for i in self.iterComponents())

    @blackBox.setter
    def blackBox(self, state):
        """Sets each component blackbox state attached to this rig instance.

        :param state: True if all components should be blackbox.
        :type state: bool
        """
        for comp in self.iterComponents():
            comp.blackBox = state

    def __repr__(self):
        """Returns The display string for the class
        :rtype: str
        """
        return "<{}> name:{}".format(self.__class__.__name__, self.name())

    def __bool__(self):
        """Returns True if this rig instance exists else False.

        :rtype: bool
        """
        return self.exists()

    def __eq__(self, other):
        return self._meta == other.meta

    def __ne__(self, other):
        return self._meta != other.meta

    def __hash__(self):
        if self._meta is None:
            return hash(id(self))
        return hash(self._meta)

    # support python2
    __nonzero__ = __bool__

    def iterComponents(self):
        """Generator function to iterate over all components in this rig, If the cache is valid then we use this
        otherwise
        the rig in the scene will be searched.

        :rtype: collections.Iterable[:class:`component.Component`]
        """
        comps = set()
        visitedMeta = set()
        for i in self.componentCache:
            # it's possible the component was deleted in another way
            # so first check to see if it exists and update the cache
            if i.exists():
                comps.add(i)
                visitedMeta.add(i.meta)
                yield i
        self.componentCache = comps
        componentLayer = self.componentLayer()
        if componentLayer is None:
            return
        compRegistry = self.configuration.componentRegistry()
        for comp in componentLayer.iterComponents():
            try:
                if comp in visitedMeta:
                    continue
                comp = compRegistry.fromMetaNode(rig=self, metaNode=comp)
                self.componentCache.add(comp)
                visitedMeta.add(comp.meta)
                yield comp
            except ValueError:
                logger.error(
                    "Failed to initialize component {}".format(comp.name()),
                    exc_info=True,
                )
                raise errors.InitializeComponentError(comp.name())

    def __contains__(self, item):
        """Determines if the component is within this rig instance

        :type item: :class:`component.Component`
        :rtype: bool
        """
        if self.component(item.name(), item.side()):
            return True
        return False

    def __len__(self):
        """Returns the number of components

        :rtype: int
        """
        return len(self.components())

    def __getattr__(self, item):
        """

        :param item: A component name_side to return, to correctly search for a component you should pass \
        in a "_" joined str of {name}_{side], eg. "_".join(component.name(), component.side())
        :type item: str
        :return:
        :rtype: :class:`component.Component`
        """
        if item.startswith("_"):
            return super(Rig, self).__getattribute__(item)
        splitter = item.split("_")
        if len(splitter) < 2:
            return super(Rig, self).__getattribute__(item)
        componentName = "_".join(splitter[:-1])
        side = splitter[-1]
        comp = self.component(componentName, side)
        if comp is not None:
            return comp
        return super(Rig, self).__getattribute__(item)

    @profiling.fnTimer
    def startSession(self, name=None, namespace=None):
        """Starts a rig session for the given rig name, if the rig already exists in the scene
        then this rig is reinitialized for this rig instanced. This happens by searching the scene meta
        root nodes

        :param name: the rig name to initialize, if it doesn't already exist one will be created
        :type name: str or HiveMeta
        :param namespace: The rig namespace
        :type: namespace: str
        :return: the root meta node for this rig
        :rtype: :class:`hivenodes.HiveRig`
        """
        meta = self._meta
        if meta is None:
            meta = rootByRigName(name, namespace)
        if meta is not None:
            self._meta = meta
            logger.debug(
                "Found rig in scene, initializing rig '{}' for session".format(
                    self.name()
                )
            )
            self.configuration.updateConfigurationFromRig(self)

            return True
        namer = self.namingConfiguration()
        meta = hivenodes.HiveRig(
            name=namer.resolve("rigMeta", {"rigName": name, "type": "meta"})
        )
        meta.attribute(constants.HNAME_ATTR).set(name)
        meta.attribute(constants.ID_ATTR).set(name)
        meta.createTransform(
            namer.resolve("rigHrc", {"rigName": name, "type": "hrc"}), parent=None
        )

        meta.createSelectionSets(namer)
        self._meta = meta

        return meta

    def rootTransform(self):
        """Returns The root transform node of the rig ie. the root HRC.

        :rtype: :class:`zapi.DagNode`
        """
        if not self.exists():
            return
        return self._meta.rootTransform()

    def exists(self):
        """Returns True or False depending on if the meta node attached to this rig exists. Without the metanode the rig
        is no longer part of hive hence False

        :rtype: bool
        """
        return self._meta is not None and self._meta.exists()

    def name(self):
        """Returns the name of the rig via the meta node

        :return: the rig name
        :rtype: str
        """
        if self.exists():
            return self._meta.rigName()
        return ""

    def rename(self, name):
        """Renames the current rig, this changes both the meta.name attribute.

        :param name: the new rig name
        :type name: str
        """
        if not self.exists():
            return
        namingObject = self.namingConfiguration()
        self._meta.attribute(constants.HNAME_ATTR).set(name)
        self._meta.rename(
            namingObject.resolve("rigMeta", {"rigName": name, "type": "meta"})
        )
        self._meta.attribute(constants.ID_ATTR).set(name)
        newName = namingObject.resolve("rigHrc", {"rigName": name, "type": "hrc"})
        self._meta.rootTransform().rename(newName)
        compLayer = self.componentLayer()
        defLayer = self.deformLayer()
        geoLayer = self.geometryLayer()
        for metaNode, layerType in zip(
            (compLayer, defLayer, geoLayer),
            (
                constants.COMPONENT_LAYER_TYPE,
                constants.DEFORM_LAYER_TYPE,
                constants.GEOMETRY_LAYER_TYPE,
            ),
        ):
            if metaNode is None:
                continue
            transform = metaNode.rootTransform()
            hrcName, metaName = naming.composeRigNamesForLayer(
                namingObject, name, layerType
            )
            if transform is not None:
                transform.rename(hrcName)
            metaNode.rename(metaName)

        sets = self._meta.selectionSets()
        for setName, setNode in sets.items():
            if setNode is None:
                continue
            if setName == "root":
                rule = "rootSelectionSet"
            else:
                rule = "selectionSet"
            setNode.rename(
                namingObject.resolve(
                    rule,
                    {"rigName": name, "selectionSet": setName, "type": "objectSet"},
                )
            )

    def namingConfiguration(self):
        """Returns the naming configuration for the current Rig instance.

        :rtype: :class:`namingutils.NameManager`
        """
        return self.configuration.findNamingConfigForType("rig")

    def buildState(self):
        """Returns the current build state which is determined by the very first component.

        :return: The hive constant. NOT_BUILT, POLISH_STATE, RIG_STATE, SKELETON_STATE, GUIDES_STATE
        :rtype: int
        """
        for c in self.iterComponents():
            if c.hasPolished():
                return constants.POLISH_STATE
            elif c.hasRig():
                return constants.RIG_STATE
            elif c.hasSkeleton():
                return constants.SKELETON_STATE
            elif c.hasGuideControls():
                return constants.CONTROL_VIS_STATE
            elif c.hasGuide():
                return constants.GUIDES_STATE
            break
        return constants.NOT_BUILT

    def isLiveLink(self):
        """Returns the livelink state for the rig.

        :rtype: bool
        """
        for comp in self.iterComponents():
            guideLayer = comp.guideLayer()
            if not guideLayer:
                return False
            return guideLayer.isLiveLink()
        return False

    def setLiveLink(self, state):
        """Sets up live linking between the guides and the deformation layer.

        :param state: True if live link should be switched on.
        :type state: bool
        """
        if self.isLiveLink() == state:
            return
        requiresGuides = False
        requiresDeform = False
        for comp in self.iterComponents():
            if not comp.hasGuide():
                requiresGuides = True
                break
            if not comp.hasSkeleton():
                requiresDeform = True
                break

        if requiresGuides:
            self.buildGuides()
        if requiresDeform:
            self.buildDeform()

        for comp in self.iterComponents():
            layer = comp.guideLayer()
            inputLayer = comp.inputLayer()
            deformLayer = comp.deformLayer()
            guideOffsetNode = inputLayer.settingNode(constants.INPUT_OFFSET_ATTR_NAME)
            layer.setLiveLink(guideOffsetNode, state)
            idMapping = {
                jntId: guideId
                for guideId, jntId in comp.idMapping()[constants.DEFORM_LAYER_TYPE]
            }
            deformLayer.setLiveLink(guideOffsetNode, idMapping, state)
            if state:
                layer.rootTransform().show()
            else:
                layer.rootTransform().hide()

    def createGroup(self, name, components=None):
        """Creates a component group on the component layer.

        :param name: The new component group
        :type name: str
        :param components: The components to add or None
        :type components: iterable(:class:`component.Component`) or None
        :return: True if the component group was added.
        :rtype: bool
        :raise: :class:`errors.ComponentGroupAlreadyExists`
        """
        return self.componentLayer().createGroup(name, components)

    def addToGroup(self, name, components):
        """Adds the components to the component group.

        :param name: The component group name
        :type name: str
        :param components: A list of component instances.
        :type components: iterable(:class:`component.Component`)
        :return: True if at least one component added.
        :rtype: bool
        """
        return self.componentLayer().addToGroup(name, components)

    def removeGroup(self, name):
        """Remove's the entire component group and it's children.

        :param name: The group name to remove.
        :type name: str
        :return: True if the group was removed.
        :rtype: bool
        """
        return self.componentLayer().addToGroup(name)

    def removeFromGroup(self, name, components):
        """Removes a list of components from the component group.

        :param name: The group name to remove the component from
        :type name: str
        :param components: A list of components to remove.
        :type components: list(:class:`component.Component`)
        :return: True if the components were removed.
        :rtype: bool
        """
        return self.componentLayer().removeFromGroup(name, components)

    def renameGroup(self, oldName, newName):
        """Renames a component group name.

        :param oldName: The old group name.
        :type oldName: str
        :param newName: The new group name.
        :type newName: str
        :return: True if the group was renamed
        :rtype: bool
        """
        return self.componentLayer().renameGroup(oldName, newName)

    def groupNames(self):
        """Returns a list of group names:

        :return: a list of str representing the group name
        :rtype: list(str)
        """
        return self.componentLayer().groupNames()

    def iterComponentsForGroup(self, name):
        """Generator function to iterate over all the component instances of a group.

        :param name: The name of the group to iterate
        :type name: str
        :rtype: Generator[:class:`component.Component`]
        """
        for name, side in self.componentLayer().iterComponentsNamesForGroup(name):
            yield self.component(name, side)

    @profiling.fnTimer
    def createComponent(
        self, componentType=None, name=None, side=None, definition=None
    ):
        """Adds a component instance to the rig and creates the root node structure for the component.
        When a component is added it will always be parented to the component Layer dag node.
        
        :param componentType: the component type this is the className of the component
        :type componentType: str
        :param name: the name to give the component
        :type name: str
        :param side: the side name to give the component
        :type side: str
        :param definition: component definition, this is set to None by default therefore it will \
        load the definition for the component from file
        :type definition: None or :class:`baseDef.ComponentDefinition`
        :return: the instance of the component
        :rtype: Component instance
        """
        if definition:
            if not componentType:
                componentType = definition.type
            if not name:
                name = definition.name
            if not side:
                side = definition.side
        else:
            definition = self.configuration.initComponentDefinition(componentType)

        comp = self.configuration.componentRegistry().findComponentByType(componentType)
        if not comp:
            raise errors.MissingComponentType(componentType)

        if name is None:
            name = definition.name
        if side is None:
            side = definition.side
        uniqueName = naming.uniqueNameForComponentByRig(self, name, side)
        componentLayer = self.getOrCreateComponentLayer()

        # component
        definition.side = side
        definition.name = uniqueName
        initComponent = comp(rig=self, definition=definition)
        initComponent.create(parent=componentLayer)
        self.componentCache.add(initComponent)
        return initComponent

    def clearComponentCache(self):
        """Clears the component cache which stores component class instances on this rig instance."""
        self.componentCache.clear()

    def _buildComponents(
        self, components, childParentRelationship, buildFuncName, **kwargs
    ):
        componentBuildOrder = _constructComponentOrder(components)
        # we grab the all current components, so we can refer to them as `_constructComponentOrder`
        # only orders the requested components.
        currentComponents = childParentRelationship
        visited = set()

        def _processComponent(comp, parentComponent):
            # we first build the parent component if any
            if parentComponent is not None and parentComponent not in visited:
                _processComponent(parentComponent, currentComponents[parentComponent])
            if comp in visited:
                return False
            visited.add(comp)
            parentDefinition = comp.definition.parent

            if parentDefinition:
                logger.debug("Component definition has parents defined, adding parents")
                # ok we are in a situation where we're rebuilding e.g. for a template where its likely
                # that parents haven't been added, but they are defined in the definition
                # so rebuild them if possible
                existingComponent = self.component(*parentDefinition.split(":"))
                if existingComponent is not None:
                    comp.setParent(existingComponent)
            try:
                logger.debug(
                    "Building component: {}, with method: {}".format(
                        comp, buildFuncName
                    )
                )
                getattr(comp, buildFuncName)(**kwargs)
                return True
            except errors.BuildComponentGuideUnknownError:
                logger.error("Failed to build for: {}".format(comp))
                return False

        for child, parentComp in componentBuildOrder.items():
            success = _processComponent(child, parentComp)
            if not success:
                return False
        return True

    # @profiling.profileit("~/zoo_preferences/logs/hive/buildGuides.profile")
    @profiling.fnTimer
    def buildGuides(self, components=None):
        """Builds all the guides for the current initialised components, if the component already has a guide then this
        component is skip, see the component base class for more info.

        :param components: The components to build, if None then all components on the rig will be built.
        :type components: list[:class:`component.Component`] or None
        """
        self.configuration.updateConfigurationFromRig(self)
        childParentRelationship = {comp: comp.parent() for comp in self.components()}
        components = components or list(childParentRelationship.keys())
        unordered = []

        def _constructUnorderedBuildList(comp):
            """Walks the component parent hierarchy gathering each component.
            This is useful for disconnectComponentsContext.

            :param comp: The current processed component
            :type comp: :class:`component.Component`
            """
            parent = childParentRelationship[comp]
            if parent is not None:
                _constructUnorderedBuildList(parent)
            unordered.append(comp)

        for comp in components:
            _constructUnorderedBuildList(comp)
        # build logic
        # gather parent hierarchy from provided components
        # detach provided components
        # loop each component
        #   get the parent and build it if needed
        with componentutils.disconnectComponentsContext(
            unordered
        ), self.buildScriptContext(constants.GUIDE_FUNC_TYPE):
            self._buildComponents(components, childParentRelationship, "buildGuide")
            modifier = zapi.dgModifier()
            for comp in components:
                comp.updateNaming(
                    layerTypes=(constants.GUIDE_LAYER_TYPE,),
                    modifier=modifier,
                    apply=False,
                )
            modifier.doIt()
            self.setGuideVisibility(
                stateType=constants.GUIDE_PIVOT_CONTROL_STATE,
                controlValue=self.configuration.guideControlVisibility,
                guideValue=self.configuration.guidePivotVisibility,
            )
            return True

    def setGuideVisibility(
        self, stateType, controlValue=None, guideValue=None, includeRoot=False
    ):
        """ Sets all component guides visibility.

        :param stateType: one of the following. `constants.GUIDE_PIVOT_STATE`, `constants.GUIDE_CONTROL_STATE` \
        `GUIDE_PIVOT_CONTROL_STATE`.
        :type stateType: int
        :param controlValue: The guide control visibility state.
        :type controlValue: bool
        :param guideValue: The guide pivot visibility state.
        :type guideValue: bool
        :param includeRoot: Whether to override the root guide visibility. By default if a component is the root\
        then the visibility state will be True.
        :type includeRoot: bool

        """
        isGuideType = stateType in (
            constants.GUIDE_PIVOT_STATE,
            constants.GUIDE_PIVOT_CONTROL_STATE,
        )
        isControlType = stateType in (
            constants.GUIDE_CONTROL_STATE,
            constants.GUIDE_PIVOT_CONTROL_STATE,
        )
        if isControlType:
            self.configuration.guideControlVisibility = controlValue
        if isGuideType:
            self.configuration.guidePivotVisibility = guideValue
        self.saveConfiguration()
        modifier = zapi.dgModifier()
        for comp in self.iterComponents():
            if not comp.hasGuide():
                continue
            guideLayer = comp.guideLayer()
            rootTransform = guideLayer.rootTransform()
            if rootTransform is not None:
                rootTransform.setVisible(True, modifier, apply=False)
            if isControlType:
                guideLayer.setGuideControlVisible(
                    controlValue, mod=modifier, apply=False
                )
            _includeRoot = (False if includeRoot is None else True) or comp.hasParent()
            if isGuideType:
                guideLayer.setGuidesVisible(
                    guideValue, includeRoot=_includeRoot, mod=modifier, apply=False
                )
        modifier.doIt()

    # @profiling.profileit("~/zoo_preferences/logs/hive/buildDeform.profile")
    @profiling.fnTimer
    def buildDeform(self, components=None):
        """Builds deform systems for the specified components.

        :param components: The list of components to build deform systems for.
                   If not specified, builds deform systems for all components.
        :type components: list[:class:`Component`]
        :return: True if successful, False otherwise.
        :rtype: bool
        """
        self.configuration.updateConfigurationFromRig(self)

        childParentRelationship = {comp: comp.parent() for comp in self.components()}
        components = components or list(childParentRelationship.keys())
        parentNode = self.getOrCreateDeformLayer().rootTransform()
        parentNode.show()  # ensure the root is visible because we hide it during polish
        self.getOrCreateGeometryLayer()
        with self.buildScriptContext(constants.DEFORM_FUNC_TYPE):
            alignGuides(self, components)
            self._meta.createSelectionSets(self.namingConfiguration())
            self._buildComponents(
                components,
                childParentRelationship,
                "buildDeform",
                parentNode=parentNode,
            )
            modifier = zapi.dgModifier()
            for comp in components:
                comp.updateNaming(
                    layerTypes=(constants.DEFORM_LAYER_TYPE,),
                    modifier=modifier,
                    apply=False,
                )
            modifier.doIt()
            return True

    # @profiling.profileit("~/zoo_preferences/logs/hive/buildRigs.profile")
    @profiling.fnTimer
    def buildRigs(self, components=None):
        """Same as buildGuides() but builds the rigs, if theres no guide currently built for the component then the
        component definition will be used.

        :todo: deal with building without the guides
        """
        self.configuration.updateConfigurationFromRig(self)
        self._meta.createSelectionSets(self.namingConfiguration())
        childParentRelationship = {comp: comp.parent() for comp in self.components()}
        components = components or list(childParentRelationship.keys())
        parentNode = None
        if not any(comp.hasSkeleton() for comp in components):
            self.buildDeform(components)
        with self.buildScriptContext(constants.RIG_FUNC_TYPE):
            success = self._buildComponents(
                components, childParentRelationship, "buildRig", parentNode=parentNode
            )
            modifier = zapi.dgModifier()
            for comp in components:
                comp.updateNaming(
                    layerTypes=(constants.RIG_LAYER_TYPE,),
                    modifier=modifier,
                    apply=False,
                )
            modifier.doIt()
            # space switches have to happen after all components have been built due to dependencies.
            _setupSpaceSwitches(components)
            if success:
                self._handleControlDisplayLayer(components)
                return True
        return False

    # @profiling.profileit("~/zoo_preferences/logs/hive/polish.profile")
    def polish(self):
        """Executes every component :meth:`component.Component.polish` function .

        Used to do a final cleanup of the rig beforehand off to animation.
        """
        requiresRig = []
        for comp in self.iterComponents():
            if not comp.hasRig():
                requiresRig.append(comp)
        if requiresRig:
            self.buildRigs(requiresRig)
        with self.buildScriptContext(constants.POLISH_FUNC_TYPE):
            success = False
            for comp in self.iterComponents():
                success_ = comp.polish()
                if success_:
                    success = success_
            return success

    def controlDisplayLayer(self):
        """Returns The display layer for the controls.

        :rtype: :class:`zapi.DisplayLayer` or None
        """
        displayLayerPlug = self.meta.attribute(constants.DISPLAY_LAYER_ATTR)
        return displayLayerPlug.sourceNode()

    def _handleControlDisplayLayer(self, components):
        """Internal method which creates, renames the primary display layer for this rig
        also adds all controls from the components to the layer.

        :param components: The components which would have its controls added to the layer.
        :type components: list[:class:`component.Component`]
        """
        namingObj = self.namingConfiguration()
        controlLayerName = namingObj.resolve(
            "controlDisplayLayerSuffix",
            {"rigName": self.name(), "type": "controlLayer"},
        )
        layer = self.meta.createDisplayLayer(controlLayerName)
        if layer.name(includeNamespace=False) != controlLayerName:
            layer.rename(controlLayerName)
        layer.playback = True
        for comp in components:
            rigLayer = comp.rigLayer()
            for control in rigLayer.iterControls():
                layer.addNode(control)
            for ann in rigLayer.annotations():
                layer.addNode(ann)

    @profiling.fnTimer
    def deleteGuides(self):
        """Deletes all guides on the rig"""
        with self.buildScriptContext(constants.DELETE_GUIDELAYER_FUNC_TYPE):
            for i in self.iterComponents():
                i.deleteGuide()

    @profiling.fnTimer
    def deleteDeform(self):
        """Deletes all component rigs"""
        with self.buildScriptContext(constants.DELETE_DEFORMLAYER_FUNC_TYPE):
            for i in self.iterComponents():
                i.deleteDeform()

    @profiling.fnTimer
    def deleteRigs(self):
        """Deletes all component rigs"""
        with self.buildScriptContext(constants.DELETE_RIGLAYER_FUNC_TYPE):
            for i in self.iterComponents():
                i.deleteRig()
            self.deleteControlDisplayLayer()
            return True

    @profiling.fnTimer
    def deleteComponents(self):
        """Deletes all components"""
        with self.buildScriptContext(constants.DELETE_COMPS_FUNC_TYPE):
            for i in self.iterComponents():
                name = i.name()
                try:
                    i.delete()
                except Exception:
                    logger.error(
                        "Failed to delete Component: {}".format(name), exc_info=True
                    )
        self.componentCache = set()

    @profiling.fnTimer
    def deleteComponent(self, name, side):
        """Deletes all the current components attached to this rig"""
        comp = self.component(name, side)
        if not comp:
            logger.warning(
                "No component by the name: {}".format(":".join((name, side)))
            )
            return False
        with self.buildScriptContext(constants.DELETE_COMP_FUNC_TYPE, component=comp):
            self._cleanupSpaceSwitches(comp)
            comp.delete()
            try:
                self.componentCache.remove(comp)
            except KeyError:
                # In the case we're the component isn't in the cache anymore so we just skip
                return False
            return True

    def _cleanupSpaceSwitches(self, component):
        """Removes all space switch drivers which use the specified component as a driver.

        :param component: The component which will be deleted
        :type component: :class:`component.Component`
        """
        logger.debug("Updating SpaceSwitching")
        oldToken = component.serializedTokenKey()
        for comp in self.iterComponents():
            if comp == component:
                continue
            requiresSave = False
            for space in comp.definition.spaceSwitching:
                newDrivers = []
                for driver in list(space.drivers):
                    driverName = driver.driver
                    if oldToken not in driverName:
                        newDrivers.append(driver)
                    else:
                        requiresSave = True
                space.drivers = newDrivers

            if requiresSave:
                comp.saveDefinition(comp.definition)

    def deleteControlDisplayLayer(self):
        """Deletes the current display layer for the rig.

        :return: Whether the deletion was successful.
        :rtype: bool
        """
        return self.meta.deleteControlDisplayLayer()

    @profiling.fnTimer
    def delete(self, deleteJoints=True):
        """Deletes all the full rig from the scene"""
        self.deleteComponents()
        with self.buildScriptContext(constants.DELETE_RIG_FUNC_TYPE):
            root = self._meta.rootTransform()
            self.deleteControlDisplayLayer()
            for layer in self.meta.layers():
                if layer.id == constants.DEFORM_LAYER_TYPE:
                    layer.delete(deleteJoints=deleteJoints)
                    continue
                layer.delete()
            root.delete()
            self._meta.delete()

    @profiling.fnTimer
    def duplicateComponent(self, component, newName, side):
        """Duplicates the given component and adds it to the rig instance

        :param component: The component to duplicate, this can be the component instance or a tuple, \
        if a tuple is supplied then the first element is the name second is the side of the component to duplicate.

        :type component: tuple[:class:`zoo.libs.hive.base.component.Component`] or  \
        :class:`zoo.libs.hive.base.component.Component`.

        :param newName: the new name for the duplicated component
        :type newName: str
        :param side: the new side for the duplicated component eg. L
        :type side: str
        :return: The new component
        :rtype: zoo.libs.hive.base.component.Component
        """
        if isinstance(component, tuple):
            name, currentSide = component
            component = self.component(name, currentSide)
            if component is None:
                raise ValueError(
                    "Can't find component with the supplied name: {} side: {}".format(
                        name, side
                    )
                )
        dup = component.duplicate(newName, side=side)
        self.componentCache.add(dup)
        return dup

    @profiling.fnTimer
    def duplicateComponents(self, componentData):
        """Duplicates the given component data and returns the new components.

        :param componentData: List of component data dicts containing the component, name, and side \
        of the component to duplicate.
        :type componentData: list[dict]
        :return: Dictionary of the new components keyed by the original name and side of the component.
        :rtype: dict
        """
        newComponents = {}
        hasSkeleton = False
        hasRig = False
        for source in componentData:
            sourceComp = source["component"]
            if sourceComp.hasSkeleton():
                hasSkeleton = True
            if sourceComp.hasRig():
                hasRig = True
            newComponent = self.duplicateComponent(
                source["component"], source["name"], source["side"]
            )
            newComponents[":".join([sourceComp.name(), sourceComp.side()])] = (
                newComponent
            )

        for originalName, component in newComponents.items():
            connections = component.definition.connections
            newConstraints = []
            for constraint in connections.get("constraints", []):
                targets = []
                for index, target in enumerate(constraint["targets"]):
                    targetLabel, targetIdMap = target
                    compName, compSide, guideId = targetIdMap.split(":")
                    parent = newComponents.get(":".join([compName, compSide]))
                    if parent is not None:
                        targets.append(
                            (
                                targetLabel,
                                ":".join([parent.name(), parent.side(), guideId]),
                            )
                        )
                        component.setParent(parent)
                if targets:
                    constData = {
                        "type": constraint["type"],
                        "kwargs": constraint["kwargs"],
                        "controller": constraint["controller"],
                        "targets": targets,
                    }
                    newConstraints.append(constData)
            compDef = component.definition
            compDef.connections = {"id": "root", "constraints": newConstraints}
            component.saveDefinition(compDef)

        self.buildGuides(newComponents.values())
        if hasSkeleton:
            self.buildDeform(newComponents.values())
        elif hasRig:
            self.buildRigs(newComponents.values())

        return newComponents

    def mirrorComponents(self, componentData):
        """Mirror the given components.

        :param componentData: A list of dictionaries containing component objects and metadata for mirroring.
        :type componentData: list[dict]
        :return: A dictionary containing the mirrored components and metadata for their transformation.
        :rtype: dict
        """
        # note: Three stage mirror:
        # 1. gather connection info i.e. constraints and un-parent
        # 2. do the mirroring.
        # 3. remap old connection info links to the new component

        skeletons = []
        rigs = []
        rig = self
        _transformData = []
        newComponents = []
        connectionInfo = {}  # type: dict[str,dict]
        visited = set()
        configNaming = self.namingConfiguration()
        existingConnectionCache = {}
        # first gather the connection info and unparent components which won't be duplicated
        # this avoids affecting the components children during the mirroring of the parent.
        for info in componentData:
            comp = info["component"]  # type: component.Component
            # dump the connections of the component for reapplying constraints post mirror
            connections = comp.serializeComponentGuideConnections()
            existingConnectionCache[comp.serializedTokenKey()] = connections
            if not info["duplicate"]:
                comp.removeAllParents()

        for info in componentData:
            # component to mirror
            originalComponent = info["component"]  # type: component.Component
            if originalComponent in visited:
                continue
            visited.add(originalComponent)
            connections = existingConnectionCache[
                originalComponent.serializedTokenKey()
            ]

            side = info["side"]
            mirrorInfo = _mirrorComponent(
                self,
                originalComponent,
                side,
                info["translate"],
                rotate=info["rotate"],
                duplicate=info["duplicate"],
            )
            newComponent = mirrorInfo["component"]
            # store the component if it needs skeleton, rig to be built after all components have been
            # mirrored
            if mirrorInfo["duplicated"]:
                if mirrorInfo["hasSkeleton"]:
                    skeletons.append(mirrorInfo["component"])
                if mirrorInfo["hasRig"]:
                    rigs.append(mirrorInfo["component"])
                newComponents.append(mirrorInfo["component"])
            # store the pre transform info for undo
            _transformData.extend(mirrorInfo["transformData"])
            tokenKey = ":".join([originalComponent.name(), newComponent.side()])
            connectionInfo[tokenKey] = dict(
                component=newComponent, connections=connections
            )

        # reapply constraints, remap the side value if needed
        symmetryField = configNaming.field("sideSymmetry")
        for _, newConnection in connectionInfo.items():
            newOrOrigComponent = newConnection["component"]
            connections = newConnection[constants.CONNECTIONS_DEF_KEY]
            # todo: this likely needs deleting once we have a better solution to component constraints
            parent, driver = None, None
            for constraint in connections.get("constraints", []):
                # note: we only need to fix connection nowadays because we no longer require a mult connection setup.
                target = constraint["targets"]
                if not target:
                    continue
                targetLabel, targetIdMap = target[0]
                compName, origCompSide, guideId = targetIdMap.split(":")
                compSide = symmetryField.valueForKey(origCompSide) or origCompSide
                tokenKey = ":".join((compName, compSide))
                # see if we mirrored the parent by remapping
                mirroredParent = connectionInfo.get(tokenKey)
                if mirroredParent:
                    parent = mirroredParent["component"]
                else:
                    parent = self.component(compName, compSide)
                if parent is not None:
                    driver = parent.guideLayer().guide(guideId)
                else:  # fall back to the existing parent, case when we mirror without duplication
                    parent = self.component(compName, origCompSide)
                break
            if parent is not None:
                # ensure connections is purged before applying the constraints
                newOrOrigComponent.connections = {}
                newOrOrigComponent.setParent(parent, driver=driver)
            else:
                # todo: Test this case of legacy connections deserialization and remove if not needed
                # before applying the constraints update the connections metaData
                compDef = newOrOrigComponent.definition
                compDef.connections = newConnection[constants.CONNECTIONS_DEF_KEY]
                newOrOrigComponent.saveDefinition(compDef)
                # now apply the constraints
                newOrOrigComponent.deserializeComponentConnections(
                    constants.GUIDE_LAYER_TYPE
                )

        if skeletons:
            rig.buildDeform(skeletons)
        if rigs:
            rig.buildRigs(rigs)

        return dict(newComponents=newComponents, transformData=_transformData)

    def components(self):
        """Returns the full list of component classes current initialized in the scene

        :rtype: list[:class:`zoo.libs.hive.base.component.Component`]
        """
        return list(self.iterComponents())

    def rootComponents(self):
        """Returns all root components as a generator.

        A component is considered the root if it has no parent.

        :rtype: list[:class:`component.Component`]
        """
        for comp in self.iterComponents():
            if not comp.hasParent():
                yield comp

    def hasComponent(self, name, side="M"):
        """Determines if the rig current

        :param name: The name of the component
        :type name: str
        :param side: the side name of the component
        :type side: str
        :return: True if the component with the name and side exists
        :rtype: bool
        """
        for i in self.iterComponents():
            if i.name() == name and i.side() == side:
                return True
        return False

    def component(self, name, side="M"):
        """Try's to find the component by name and side, First check this rig instance in the component
        cache if not there then walk the components via the meta network until one
        is found. None will be return if the component doesn't exist.

        :param name: the component name
        :type name: str
        :param side: the component side name
        :type side: str
        :returns: Returns the component or None if not found
        :rtype: :class:`zoo.libs.hive.base.component.Component` or None
        """
        for comp in self.componentCache:
            if comp.name() == name and comp.side() == side:
                return comp
        # if we got here then the component was attached to the rig without going through the instance so search the
        # metadata until we hit the specified component else just return None
        componentLayer = self.getOrCreateComponentLayer()
        if componentLayer is None:
            return
        compRegistry = self.configuration.componentRegistry()
        for comp in componentLayer.iterComponents():
            if (
                comp.attribute(constants.HNAME_ATTR).asString() == name
                and comp.attribute(constants.SIDE_ATTR).asString() == side
            ):
                compInstance = compRegistry.fromMetaNode(rig=self, metaNode=comp)
                self.componentCache.add(compInstance)
                return compInstance

    def componentsByType(self, componentType):
        """Generator Method which returns all components of the requested type name.

        :param componentType: The hive component type.
        :type componentType: str
        :return: Generator where each element is a component which has the requested type.
        :rtype: list[:class:`component.Component`]
        """
        for comp in self.iterComponents():
            if comp.componentType == componentType:
                yield comp

    def componentFromNode(self, node):
        """Returns the component for the provided node if it's part of this rig, otherwise
        Raise :class:`errors.MissingMetaNode` if the node isn't connected.

        :param node: The DG and Dag node to search for the component.
        :type node: :class:`zapi.DGNode`
        :rtype: :class:`component.Component` or None
        :raise: :class:`errors.MissingMetaNode`
        """
        metaNode = componentMetaNodeFromNode(node)
        if not metaNode:
            raise errors.MissingMetaNode(node)
        return self.component(
            metaNode.attribute(constants.HNAME_ATTR).value(),
            metaNode.attribute(constants.SIDE_ATTR).value(),
        )

    @profiling.fnTimer
    def serializeFromScene(self, components=None):
        """Ths method will run through all the current initialized component and serialize them


        :type components: list(:class:`component.Component`)
        :rtype: dict
        """
        outputComponents = components or self.components()
        data = {"name": self.name(), "hiveVersion": self.hiveVersion}
        count = len(outputComponents)
        comps = [{}] * count
        for c in range(count):
            comps[c] = outputComponents[c].serializeFromScene().toTemplate()
        data["components"] = comps
        config = self.saveConfiguration()
        if "guidePivotVisibility" in config:
            del config["guidePivotVisibility"]
        if "guideControlVisibility" in config:
            del config["guideControlVisibility"]

        data["config"] = config
        return data

    @profiling.fnTimer
    def saveConfiguration(self):
        """Serializes and saves the configuration for this rig on to the meta node.
        Use :meth:`Rig.CachedConfiguration` to retrieve the saved configuration.

        :return: The Serialized configuration.
        :rtype: dict
        """
        logger.debug("Saving Configuration")
        config = self.configuration.serialize(self)
        if config:
            configPlug = self._meta.attribute(constants.RIG_CONFIG_ATTR)
            configPlug.set(json.dumps(config))
        return config

    def cachedConfiguration(self):
        """Returns the configuration cached on the rigs meta node config attribute as a dict.

        :return: The configuration dict.
        :rtype: dict
        """
        configPlug = self._meta.attribute(constants.RIG_CONFIG_ATTR)
        try:
            cfgData = configPlug.value()
            if cfgData:
                return json.loads(cfgData)
        except ValueError:
            pass
        return {}

    def componentLayer(self):
        """Returns the component layer instance from this rig by querying the attached meta node.

        :rtype: :class:`hivenodes.HiveComponentLayer`
        """
        return self._meta.componentLayer()

    def deformLayer(self):
        """Returns the deform layer instance from this rig by querying the attached meta node.

        :rtype: :class:`hivenodes.HiveDeformLayer`
        """

        return self._meta.deformLayer()

    def geometryLayer(self):
        """Returns the Geometry layer instance from this rig by querying the attached meta node.

        :rtype: :class:`hivenodes.HiveGeometryLayer`
        """

        return self._meta.geometryLayer()

    def selectionSets(self):
        """
        :return:
        :rtype: dict[str,:class:`zapi.ObjectSet`]
        """
        return self._meta.selectionSets()

    def getOrCreateGeometryLayer(self):
        """Returns the geometry layer if it's attached to this rig or creates and attaches one

        :rtype: :class:`hivenodes.HiveGeometryLayer`
        """

        root = self._meta
        geo = root.geometryLayer()
        if not geo:
            namer = self.namingConfiguration()
            hrcName = self._hrcNodeName(namer, constants.GEOMETRY_LAYER_TYPE)
            metaName = namer.resolve(
                "layerMeta",
                {
                    "rigName": self.name(),
                    "layerType": constants.GEOMETRY_LAYER_TYPE,
                    "type": "meta",
                },
            )
            return root.createLayer(
                constants.GEOMETRY_LAYER_TYPE,
                hrcName=hrcName,
                metaName=metaName,
                parent=root.rootTransform(),
            )

        return geo

    def getOrCreateDeformLayer(self):
        """Returns the deform layer if it's attached to this rig or creates and attaches one

        :rtype: :class:`hivenodes.HiveDeformLayer`
        """

        root = self._meta
        deform = root.deformLayer()
        if not deform:
            namer = self.namingConfiguration()
            hrcName = self._hrcNodeName(namer, constants.DEFORM_LAYER_TYPE)
            metaName = namer.resolve(
                "layerMeta",
                {
                    "rigName": self.name(),
                    "layerType": constants.DEFORM_LAYER_TYPE,
                    "type": "meta",
                },
            )
            deform = root.createLayer(
                constants.DEFORM_LAYER_TYPE,
                hrcName=hrcName,
                metaName=metaName,
                parent=root.rootTransform(),
            )
        return deform

    def getOrCreateComponentLayer(self):
        """Returns the component layer if it's attached to this rig or creates and attaches one

        :rtype: :class:`layers.ComponentLayer`
        """

        meta = self._meta
        layer = meta.componentLayer()
        if layer is None:
            namer = self.namingConfiguration()
            hrcName, metaName = naming.composeRigNamesForLayer(
                namer, self.name(), constants.COMPONENT_LAYER_TYPE
            )
            layer = meta.createLayer(
                constants.COMPONENT_LAYER_TYPE,
                hrcName=hrcName,
                metaName=metaName,
                parent=meta.rootTransform(),
            )
        return layer

    def _hrcNodeName(self, namingConfiguration, name):
        """Compose a hrc name from the `name`.

        :param name: The base name of the hrc node.
        :type name: str
        :return: The new hrc name to use.
        :rtype: str
        """

        return namingConfiguration.resolve(
            "layerHrc", {"rigName": self.name(), "layerType": name, "type": "hrc"}
        )

    @contextlib.contextmanager
    def buildScriptContext(self, buildScriptType, **kwargs):
        """Executes all build scripts assigned in the configuration.buildScript.

        If each build script class registered contains a method called preGuideBuild()
        """
        preFuncName, postFuncName = constants.BUILDSCRIPT_FUNC_MAPPING.get(
            buildScriptType
        )
        scriptConfiguration = self.meta.buildScriptConfig()
        if preFuncName:
            for script in self.configuration.buildScripts:
                if hasattr(script, preFuncName):
                    scriptProperties = script.propertiesAsKeyValue()
                    logger.debug(
                        "Executing build script function: {}".format(
                            ".".join((script.__class__.__name__, preFuncName))
                        )
                    )

                    scriptProperties.update(scriptConfiguration.get(script.id, {}))
                    script.rig = self
                    getattr(script, preFuncName)(properties=scriptProperties, **kwargs)
        yield
        if postFuncName:
            for script in self.configuration.buildScripts:
                if hasattr(script, postFuncName):
                    scriptProperties = script.propertiesAsKeyValue()
                    logger.debug(
                        "Executing build script function: {}".format(
                            ".".join((script.__class__.__name__, postFuncName))
                        )
                    )
                    scriptProperties.update(scriptConfiguration.get(script.id, {}))
                    script.rig = self
                    getattr(script, postFuncName)(properties=scriptProperties, **kwargs)


def _setupSpaceSwitches(components):
    """Internal method which loops over the provided components and runs setupSpaceSwitches.

    :type components: list[:class:`component.Component`]
    """
    for comp in components:
        with mayageneral.namespaceContext(comp.namespace()):
            container = comp.container()  # type: zapi.ContainerAsset
            if container is not None:
                container.makeCurrent(True)
            try:
                comp.setupSpaceSwitches()
            finally:
                if container is not None:
                    container.makeCurrent(False)


def _constructComponentOrder(components):
    """Internal Method to handle ordering component by DG order.

    :type components: list or Generator
    :return:
    :rtype: dict[:class:`component.Component`, :class:`component.Component`]
    """
    unsorted = {}
    for comp in components:
        parent = comp.parent()
        unsorted[comp] = parent
    ordered = OrderedDict()
    # we ordered owe component by child: parentComponents
    # so that any component that doesn't have a parent is at the bottom of the dict
    while unsorted:
        for child, parent in list(unsorted.items()):
            if parent in unsorted:
                continue
            else:
                del unsorted[child]
                ordered[child] = parent
    return ordered


def alignGuides(rig, components):
    """Runs alignGuides for all provided guides.
    This function appropriately disconnects components before aligning.

    :param rig: The rig instance which the components belong too.
    :type rig: :class:`Rig`
    :param components:
    :type components: list[:class:`component.Component`]
    """
    rig.serializeFromScene()
    config = rig.configuration
    with componentutils.disconnectComponentsContext(components):
        for comp in components:
            if not config.autoAlignGuides or not comp.hasGuide():
                continue

            container = comp.container()
            if container:
                container.lock(False)
            comp.alignGuides()
            if container:
                container.lock(True)
    rig.serializeFromScene()


def rootByRigName(name, namespace=None):
    """Finds the root meta node with the name attribute value set to "name"

    :param name: the rig name
    :type name: str
    :param namespace: the namespace to search for the hive rig root meta node. must be valid namespace
    :type namespace: str
    :rtype: :class:`hivenodes.HiveRig`
    """
    rigs = []
    rigNames = []
    for m in iterSceneRigMeta():
        rigs.append(m)
        rigNames.append(m.attribute(constants.HNAME_ATTR).value())
    if not rigs:
        return None
    if not namespace:
        dupes = general.getDuplicates(rigNames)
        if dupes:
            raise errors.HiveRigDuplicateRigsError(dupes)
        for r in rigs:
            if r.attribute(constants.HNAME_ATTR).value() == name:
                return r
    if namespace:
        if not namespace.startswith(":"):
            namespace = ":{}".format(namespace)
        for m in rigs:
            rigNamespace = m.namespace()
            if (
                rigNamespace == namespace
                and m.attribute(constants.HNAME_ATTR).value() == name
            ):
                return m


def iterSceneRigMeta():
    """Generator function that iterates over every Hive rig Meta node in the scene.

    :return: Returns the rig instance
    :rtype: collections.Iterator[:class:`hivenodes.HiveRig`]
    """
    for m in base.findMetaNodesByClassType(constants.RIG_TYPE):
        yield m


def iterSceneRigs():
    """Generator Function that iterates over every Hive rig in the scene.

    This is done by looping the metaNode roots(Network Nodes) and
    check if it has an attribute called "isHiveRoot"

    :return: Returns the rig instance
    :rtype: collections.Iterator[:class:`Rig`]
    """
    for rigMeta in iterSceneRigMeta():
        newSession = Rig(meta=rigMeta)
        newSession.startSession()
        yield newSession


def loadFromTemplateFile(filePath, name=None, rig=None):
    """

    :param filePath: The absolute path to the template json file to load.
    :type filePath: str
    :param name: The name for the new rig instance if created, defaults to "HiveRig".
    :type name: str
    :param rig: The rig to load the components from template on to. if no rig provided \
    then a new instance will be created.
    :type rig: :class:`Rig` or None
    :return: Returns the rig instance
    :rtype: collections.Iterator[:class:`Rig`]
    """
    template = filesystem.loadJson(filePath)
    if not template:
        logger.error("Failed to read template file: {}".format(template))
        return
    logger.debug("Loading template from path: {}".format(filePath))
    return loadFromTemplate(template, name=name, rig=rig)


@profiling.fnTimer
def loadFromTemplate(template, name=None, rig=None):
    """Loads the hive template on to a rig.

    :param template: The hive Template data structure.
    :type template: dict
    :param name: New rig Name, Only used if a rig isn't provided.
    :type name: str
    :param rig: An existing rig Instance, if None a new rig will be created.
    :type rig: :class:`Rig` or None
    :return: The New or provided rig instance and a list of newly created components.
    :rtype: tuple[:class:`Rig`, dict[str, :class:`component.Component`]
    """

    if rig is None:
        configData = template.get("config", {})
        buildScripts = configData.get("buildScripts")
        config = configuration.Configuration()
        config.applySettingsState(configData)

        rig = Rig(config=config)
        hasCreated = rig.startSession(name or template["name"])
        try:
            config.updateBuildScriptConfig(rig, {k: v for k, v in buildScripts})
        except ValueError:  # todo: replace once we rewrite build script save/load
            pass
        if not hasCreated:
            logger.error(
                "Can't create template with a name that already exists, "
                "at least for now!, skipping"
            )
            return
    return rig, templateutils.loadFromTemplate(template, rig)


def rigFromNode(node):
    """Get rig from node

    :param node: The dag node to find the rig from
    :type node: :class:`zapi.DGNode`
    :return: The rig
    :rtype: :class:`Rig`
    """
    metaNodes = base.getConnectedMetaNodes(node)
    if not metaNodes:
        raise errors.MissingMetaNode("No metaNode attached to this node")
    try:
        for m in metaNodes:
            r = parentRig(m)
            if r:
                return r
        else:
            raise AttributeError()
    except AttributeError:
        raise errors.MissingMetaNode("Attached meta node is not a valid hive node")


def parentRig(metaNode):
    """Returns the meta node representing the parent rig.

    :param metaNode: The meta base class.
    :type metaNode: :class:`base.MetaBase`
    :return: The Rig instance found to be the parent of the metanode
    :rtype: :class:`Rig` or None
    """
    for parent in metaNode.iterMetaParents(recursive=True):
        hiveRootAttr = parent.attribute(constants.ISHIVEROOT_ATTR)
        if hiveRootAttr and hiveRootAttr.value():
            newSession = Rig(meta=parent)
            newSession.startSession()
            return newSession


def componentFromNode(node, rig=None):
    """Attempts to find and return the attached component class of the node.

    :param node: The node to find the component from
    :type node: :class:`zapi.DGNode`
    :param rig: If a Rig instance has been passed then the component will be searched \
    on that Rig.
    :type: :class:`Rig` or None
    :rtype: Component
    :raises: ValueError, Will raise when it cant find a meta node or the metanode is not \
    a valid hive node.
    """
    if rig is None:
        rig = rigFromNode(node)
        if not rig:
            raise errors.MissingRigForNode(node.fullPathName())
    return rig.componentFromNode(node)


def componentMetaNodeFromNode(node):
    """This method attempts to resolve the component meta node by walking the DG downstream
    of the given node.

    .. note:: Internal use only.

    :param node: The zapi node instance.
    :type node: :class:`zapi.DGNode`
    :return: The Meta node class or None.
    :rtype: :class:`base.MetaBase` or None
    """

    if base.isMetaNode(node):
        metaNodes = [base.MetaBase(node.object())]
    else:
        metaNodes = base.getConnectedMetaNodes(node)

    if not metaNodes:
        raise ValueError("No metaNode attached to this node")
    actual = metaNodes[0]
    if actual.hasAttribute(constants.COMPONENTTYPE_ATTR):
        return actual
    for m in actual.iterMetaParents():
        if m.hasAttribute(constants.COMPONENTTYPE_ATTR):
            return m


def componentsFromSelected():
    """Components from selected in the scene

    :rtype: dict[:class:`component.Component`, list[:class:`zapi.DagNode`]]
    """

    return componentsFromNodes(zapi.selected())


def componentsFromNodes(nodes):
    """Components from selected in the scene

    :rtype: dict[:class:`component.Component`, list[:class:`zapi.DagNode`]]
    """

    components = {}
    for s in nodes:
        try:
            comp = componentFromNode(s)
        except (errors.MissingMetaNode, errors.MissingRigForNode):
            continue
        components.setdefault(comp, []).append(s)

    return components


def _mirrorComponent(rig, comp, side, translate, rotate, duplicate=True):
    """Mirrors the provided component.

    A new component will be created only if `duplicate=True` is set which is the default.
    When duplicate is False then the provided component will be mirrored in place.

    :param comp: The component to mirror.
    :type comp: :class:`component.Component`
    :param side: The side name for the component only when duplicating.
    :type side: str
    :param translate: The axis to mirror on ,default is ("x",).
    :type translate: tuple
    :param rotate: The mirror plane to mirror rotations on, supports "xy", "yz", "xz", defaults to "yz".
    :type rotate: str
    :param duplicate: Whether the component should be duplicated then mirrored.
    :type duplicate: bool
    :rtype: dict
    """
    if duplicate:
        comp = rig.duplicateComponent(comp, comp.name(), side)

    # ensure we have the guides built, technically we should be able to do this without the guides but for now
    # it'll do
    if not comp.hasGuide():
        rig.buildGuides((comp,))
    container = comp.container()
    if container is not None:
        container.lock(False)
    originalData = comp.mirror(translate=translate, rotate=rotate)
    if container is not None:
        container.lock(True)
    return dict(
        duplicated=duplicate,
        hasRig=comp.hasRig(),
        hasSkeleton=comp.hasSkeleton(),
        transformData=originalData,
        component=comp,
    )
