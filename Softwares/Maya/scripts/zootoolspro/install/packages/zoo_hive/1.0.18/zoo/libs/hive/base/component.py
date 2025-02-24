import contextlib
import copy
import json
from collections import OrderedDict

from maya.api import OpenMaya as om2

from zoo.libs.hive.base.definition import spaceswitch
from zoo.libs.hive.base.util import componentutils
from zoo.libs.maya.api import attrtypes
from zoo.libs.maya.meta import base
from zoo.libs.maya import zapi
from zoo.core.util import zlogging
from zoo.libs.utils import profiling, general as generalutils
from zoo.libs.hive import constants
from zoo.libs.hive.base import naming as namingutils
from zoo.libs.hive.base import definition as baseDef, errors
from zoo.libs.hive.base.definition import defutils
from zoo.libs.hive.base.hivenodes import layers, hnodes
from zoo.libs.hive.constants import _ATTRIBUTES_TO_SKIP_PUBLISH

if generalutils.TYPE_CHECKING:
    from zoo.libs.naming import naming
    from zoo.libs.hive.base import configuration


class Component(object):
    """Component class that encapsulates a single rigging component, This is the class that would be overridden.

    BuildSystem Methods:
        * :func:`Component.idMapping`
        * :func:`Component.preSetupGuide`
        * :func:`Component.setupGuide`
        * :func:`Component.postSetupGuide`
        * :func:`Component.alignGuides`
        * :func:`Component.setupInputs`
        * :func:`Component.setupDeformLayer`
        * :func:`Component.setupOutputs`
        * :func:`Component.postSetupDeform`
        * :func:`Component.preSetupRig`
        * :func:`Component.setupRig`
        * :func:`Component.postSetupRig`
        * :func:`Component.prePolish`
        * :func:`Component.postPolish`
        * :func:`Component.createRigControllerTags`
        * :func:`Component.createGuideControllerTags`
        * :func:`Component.spaceSwitchUiData`
        * :func:`Component.setupSelectionSet`
        * :func:`Component.setGuideNaming`
        * :func:`Component.setDeformNaming`
        * :func:`Component.setRigNaming`
        * :func:`Component.updateGuideSettings`
        * :func:`Component.preMirror`
        * :func:`Component.postMirror`

    :param rig: The rig instance attached to the component.
    :type rig: :class:`zoo.libs.hive.base.rig.Rig`
    :param definition: The component definition which is used to build the guide and rig.
    :type definition: :class:`zoo.libs.hive.base.definition.ComponentDefinition` or dict
    :param metaNode: the component meta node isinstance.
    :type metaNode: :class:`layers.HiveComponent`
    """

    #:  The name of the developer who created the component type
    creator = ""  # type: str
    #: The Name of the definition which is used to link this component to the definition file.
    #: this is the "name" key within the definition.
    definitionName = ""  # type: str
    uiData = {"icon": "hive", "iconColor": (), "displayName": ""}
    #: the Icon to use for component anytime we need GUI display
    # depreciated, use uiData
    icon = "hive"  # type: str
    # scene documentation ie. maya notes attribute and UI tooltip
    documentation = ""

    betaVersion = False

    def __init__(self, rig, definition=None, metaNode=None):
        super(Component, self).__init__()

        self._rig = rig
        self._meta = metaNode
        self._container = None  # type: zapi.ContainerAsset or None
        # the rig configuration instance
        self.configuration = rig.configuration  # type: configuration.Configuration
        # True only while we are constructing the guide system for this component
        self.isBuildingGuide = False  # type: bool
        # True only while we are constructing the anim system for this component
        self.isBuildingRig = False  # type: bool
        # True only while we are constructing the skeleton/deform system for this component
        self.isBuildingSkeleton = False  # type: bool
        # application version(maya)
        self.applicationVersion = om2.MGlobal.mayaVersion()  # type: str
        self._definition = None  # type: baseDef.ComponentDefinition or None

        # no definition passed which happens when we pull from the scene, so serialize the component from the scene
        if definition is None and metaNode is not None:
            componentType = metaNode.componentType.asString()
            raw = self._rig.configuration.initComponentDefinition(componentType)
            self._originalDefinition = (
                self._rig.configuration.componentRegistry().loadComponentDefinition(
                    componentType
                )
            )
            # self.definition returns the scene data since we have yet to set it, We also need
            # to make the scene def has been updated to the latest version if possible
            if self._meta is not None and self._meta.exists():
                data = self._meta.rawDefinitionData()
                translatedData = defutils.parseRawDefinition(data)
                sceneData = baseDef.migrateToLatestVersion(
                    translatedData, originalComponent=raw
                )
                raw.update(sceneData)
            self._definition = raw
        elif definition and metaNode:
            self._originalDefinition = copy.deepcopy(definition)
            self._definition = self._definitionFromScene()
        else:
            self._originalDefinition = definition
            self.definition = copy.deepcopy(definition)
        # The python logging instance for this component
        self.logger = zlogging.getLogger(
            ".".join([__name__, "_".join([self.name(), self.side()])])
        )
        # Build time object cache, stores commonly used object instances like hive layers for the
        # lifetime of a build stage. Once the build is completed, this will be purged
        self._buildObjectCache = {}

    def __bool__(self):
        return self.exists()

    def __eq__(self, other):
        if other is None:
            return False
        return isinstance(other, Component) and self._meta == other.meta

    def __ne__(self, other):
        if other is None:
            return False
        return isinstance(other, Component) and self._meta != other.meta

    def __hash__(self):
        return hash(self._meta)

    # support python2
    __nonzero__ = __bool__

    def __repr__(self):
        return "<{}>-{}:{}".format(self.__class__.__name__, self.name(), self.side())

    @property
    def meta(self):
        """Component meta node

        :return: Hive component meta node
        :rtype: :class:`zoo.libs.hive.base.hivenodes.layers.HiveComponent`
        """
        return self._meta

    @meta.setter
    def meta(self, value):
        """Set the component meta

        :param value: The meta node
        :type value: :class:`zoo.libs.hive.base.hivenodes.layers.HiveComponent`
        """
        self._meta = value

    @property
    def componentType(self):
        """Returns the component name which can be used do a lookup in the registry

        :rtype: str
        """
        if self.exists():
            return self._meta.componentType.asString()
        return self.__class__.__name__

    def _definitionFromScene(self):
        if self._meta is not None and self._meta.exists():
            data = self._meta.rawDefinitionData()
            translatedData = defutils.parseRawDefinition(data)
            return baseDef.loadDefinition(translatedData, self._originalDefinition)

    @property
    def isBetaVersion(self):
        """Returns whether this component is in beta.

        :rtype: bool
        """
        return self.betaVersion

    @property
    def definition(self):
        """Returns the correct definition object, if the rig is built then we grab the definition from the
        meta node attribute 'componentDefinition'

        :rtype: :class:`baseDef.ComponentDefinition`
        """
        return self._definition

    @definition.setter
    def definition(self, value):
        """Sets the component definition

        :param value:
        :type value: dict or :class:`definition.ComponentDefinition`

        .. note:: if the rig is built should we set the definition attribute as well?

        """
        if type(value) == dict:
            value = baseDef.loadDefinition(value, self._originalDefinition)
        self._definition = value

    def saveDefinition(self, value):
        """Saves the provided value as the definition cache and bakes the definition into the
        components meta node.

        :param value: The new definition instance to bake.
        :type value: :class:`baseDef.ComponentDefinition` or dict
        """
        if type(value) == dict:
            value = baseDef.loadDefinition(value, self._originalDefinition)

        self._definition = value
        self.logger.debug("Saving definition")
        self._meta.saveDefinitionData(value.toSceneData())

    @property
    def rig(self):
        """Returns the current rig instance.

        :return: The rig class instance
        :rtype: :class:`zoo.libs.hive.base.rig.Rig`
        """
        return self._rig

    @property
    def blackBox(self):
        """Convenience method,  If this component has a container object then return the container.blackBox value

        :rtype: bool
        """
        cont = self.container()
        if not cont or not cont.blackBox:
            return False
        return True

    @blackBox.setter
    def blackBox(self, state):
        """Sets the Asset containers blackbox state for this component.

        :param state: The black box state
        :type state: bool
        """
        cont = self.container()
        if cont:
            cont.blackBox = state

    def namingConfiguration(self):
        """Returns the naming configuration for the current component instance.

        :rtype: :class:`naming.NameManager`
        """
        nameCache = self._buildObjectCache.get("naming")
        if nameCache is not None:
            return nameCache
        return self.configuration.findNamingConfigForType(
            self.componentType, presetName=self.currentNamingPreset().name
        )

    def currentNamingPreset(self):
        """Returns the current naming convention preset instance for this component.

        :rtype: :class:`zoo.libs.hive.base.namingpresets.Preset`
        """
        localOverride = self.definition.namingPreset
        presetManager = self.configuration.namePresetRegistry()
        if not localOverride:
            return self.configuration.currentNamingPreset
        localPreset = presetManager.findPreset(localOverride)
        if localPreset is None:
            return self.configuration.currentNamingPreset
        return localPreset

    def container(self):
        """Returns the container hive node which is retrieved from the meta node

        :rtype: :class:`zoo.libs.maya.zapi.ContainerAsset` or None
        """
        if self._meta is not None and self._meta.exists():
            source = self._meta.container.source()
            if source is not None:
                return zapi.ContainerAsset(source.node().object())

    def isHidden(self):
        """Determines if the component is hidden in the scene.

        This is determined by both the existence of the component and the root transform
        visibility attribute.

        :rtype: bool
        """
        return self.exists() and self._meta.rootTransform().isHidden()

    def hide(self):
        """Hides the component by turning off the visibility on the root transform

        :return: Success
        :rtype: bool
        """
        if self.exists():
            return self._meta.rootTransform().hide()
        return False

    def show(self):
        """Shows the component by turning on the visibility on the root transform

        :return: Success
        :rtype: bool
        """
        if self.exists():
            return self._meta.rootTransform().show()
        return False

    def createContainer(self):
        """Creates a new AssetContainer if it's not already created and attaches it to this
        component instance.

        :note: This will not merge component nodes into the container.
        :return: The newly created containerAsset instance.
        :rtype: :class:`zapi.ContainerAsset`
        """
        cont = self.container()
        if cont is not None:
            return cont
        cont = zapi.ContainerAsset()
        name, side = self.name(), self.side()
        containerName = namingutils.composeContainerName(
            self.namingConfiguration(), name, side
        )
        cont.create(containerName)
        cont.message.connect(self._meta.container)
        self._container = cont
        return cont

    def deleteContainer(self):
        """Deletes the container and all of its contents

        :return: True if succeeded
        :rtype: bool
        """
        cont = self.container()
        if cont:
            cont.delete()
            return True
        return False

    def hasContainer(self):
        """Determines if this component has a container

        :rtype: bool
        """
        return self.container() is not None

    @profiling.fnTimer
    def create(self, parent=None):
        """Main method that creates the component in the scene excludes the actual creation of the component guides or
        rig

        :param parent: The parent component or rig layer which component will connect to via meta node.
        :type parent: :class:`Layer.HiveRig`
        :return: The hive components meta node instance.
        :rtype: :class:`layers.HiveComponent`
        """
        definition = self.definition
        side = definition.side
        self.logger.debug("Creating component stub in currentScene")
        namingConfig = self.namingConfiguration()
        compName, side = self.name(), side
        hrcName, metaName = namingutils.composeComponentRootNames(
            namingConfig, compName, side
        )
        self.logger.debug("Creating Component meta node")
        m = layers.HiveComponent(name=metaName)
        m.attribute(constants.HNAME_ATTR).set(definition.name)
        m.attribute(constants.SIDE_ATTR).set(side)
        m.attribute(constants.ID_ATTR).set(definition.name)
        m.attribute(constants.VERSION_ATTR).set(definition.version)
        m.attribute(constants.COMPONENTTYPE_ATTR).set(definition.type)
        notes = m.attribute("notes")
        if notes is None:
            m.addAttribute(
                "notes", Type=zapi.attrtypes.kMFnDataString, value=self.documentation
            )
        else:
            notes.set(self.documentation)
        parentTransform = parent.rootTransform() if parent else None
        m.createTransform(hrcName, parent=parentTransform)
        self._meta = m
        if isinstance(parent, layers.HiveComponentLayer):
            m.addMetaParent(parent)

        return m

    def rootTransform(self):
        """Returns The root transform node of the component i.e. the HRC

        :rtype: :class:`zapi.DagNode`
        """
        if not self.exists():
            return
        return self._meta.rootTransform()

    def group(self):
        if not self.exists():
            return
        sourcePlug = self._meta.componentGroup.source()
        return sourcePlug.parent().child(0)

    def setMetaNode(self, node):
        """Sets the component meta node

        :param node: the node
        :type node: MObject
        """
        meta = layers.HiveComponent(node)
        self._meta = meta
        return self._meta

    def exists(self):
        """Returns whether this component  exists in the scene, this is determined
        by the existence of the meta node and the root transform node.

        :rtype: bool
        """
        try:
            return self._meta.exists()
        except AttributeError:
            self.logger.debug(
                "Component doesn't exist: {}".format(self.definition.name),
                exc_info=True,
            )
        return False

    def serializedTokenKey(self):
        """Returns the serialized data key for this component.
        This result is the joined name, side with ":" as the separator

        :return: the name and side of the component in the format of "name:side"
        :rtype: str
        """
        if not self.exists():
            return ""
        return ":".join((self.name(), self.side()))

    def name(self):
        """returns the name of the component, if the meta node exists pull it from there else the definition

        :return: the component name
        :rtype: str
        """
        return self.definition.name

    def side(self):
        """Returns the side name of the component, if the meta node exists pull it from there else the definition

        :return: the component side name
        :rtype: str
        """
        return self.definition.side

    def setSide(self, side):
        """This set's the components side name

        :param side: the side
        :type side: str
        """
        name, oldSide = self.name(), self.side()
        self.definition.side = side
        if self._meta is None:
            return

        self._meta.attribute(constants.SIDE_ATTR).set(side)
        namingConfig = self.namingConfiguration()
        oldName = namingConfig.resolve(
            "componentName", {"componentName": name, "side": oldSide}
        )
        newName = namingConfig.resolve(
            "componentName", {"componentName": name, "side": side}
        )
        for componentNode in self.nodes():
            componentNode.rename(componentNode.name().replace(oldName, newName))
        self._meta.attribute(constants.SIDE_ATTR).set(side)
        self.saveDefinition(self.definition)
        self._updateSpaceSwitchComponentDependencies(self.name(), side)

    def rename(self, name):
        """Renames the component by setting the meta and definition name attribute as well the namespace

        :param name: the new name fpr the component
        :type name: str
        """
        oldName, side = self.name(), self.side()
        self.definition.name = name
        if self._meta is None:
            return

        namingConfig = self.namingConfiguration()
        oldName = namingConfig.resolve(
            "componentName", {"componentName": oldName, "side": side}
        )
        self._meta.attribute(constants.HNAME_ATTR).set(name)
        newName = namingConfig.resolve(
            "componentName", {"componentName": name, "side": side}
        )
        for componentNode in self.nodes():
            componentNode.rename(componentNode.name().replace(oldName, newName))
        self._meta.attribute(constants.HNAME_ATTR).set(name)
        self._meta.attribute(constants.ID_ATTR).set(name)
        self.saveDefinition(self.definition)
        self._updateSpaceSwitchComponentDependencies(name, side)

    def updateNaming(
        self,
        layerTypes=(constants.GUIDE_LAYER_TYPE, constants.DEFORM_LAYER_TYPE),
        modifier=None,
        apply=True,
    ):
        """Runs the update process to update any node names on the component from the
        current naming configuration instance.

        :param layerTypes: A tuple of layer types ie. (constants.GUIDE_LAYER_TYPE,) at this stage \
        only GUIDE_LAYER_TYPE and DEFORM_LAYER_TYPE is supported.

        :type layerTypes: tuple[str]
        :param modifier: The DGModifier instance to use when renaming a node
        :type modifier: :class:`zapi.dgModifier`
        :param apply: Whether doIt should be run on the modifier.
        :type apply: bool
        :return: The modifier instance used, if none provided then the one created will be returned
        :rtype: :class:`zapi.dgModifier`
        """
        self._generateObjectCache()
        modifier = modifier or zapi.dgModifier()
        namingConfig = self.namingConfiguration()
        meta = self._meta
        rootTransform = self.rootTransform()
        container = self.container()
        compName, side = self.name(), self.side()
        # first unlock the component root nodes before will start the renaming
        toLock = [meta, rootTransform]
        if container is not None:
            toLock.append(container)
        for n in toLock:
            n.lock(False, mod=modifier, apply=False)
        try:
            hrcName, metaName = namingutils.composeComponentRootNames(
                namingConfig, compName, side
            )
            containerName = namingutils.composeContainerName(
                namingConfig, compName, side
            )

            meta.rename(metaName, mod=modifier, apply=False)
            rootTransform.rename(hrcName, mod=modifier, apply=False)
            if container is not None:
                container.rename(containerName, mod=modifier, apply=False)

            if constants.GUIDE_LAYER_TYPE in layerTypes and self.hasGuide():
                self._setGuideNaming(namingConfig, modifier)
            if constants.DEFORM_LAYER_TYPE in layerTypes and self.hasSkeleton():
                self._setDeformNaming(namingConfig, modifier)
            if constants.RIG_LAYER_TYPE in layerTypes and self.hasRig():
                self._setRigNaming(namingConfig, modifier)
            # now lock the nodes
            for n in toLock:
                n.lock(True, mod=modifier, apply=False)
            if apply:
                modifier.doIt()
        finally:
            self._buildObjectCache = {}

        return modifier

    def _setGuideNaming(self, namingConfig, modifier):
        compName, side = self.name(), self.side()
        hrcName, metaName = namingutils.composeNamesForLayer(
            namingConfig, compName, side, constants.GUIDE_LAYER_TYPE
        )
        layer = self.guideLayer()
        transform = layer.rootTransform()
        guides = list(layer.iterGuides(True))
        guideSetting = layer.settingNode(constants.GUIDE_LAYER_TYPE)

        def _changeLockGuideLayer(state, apply=False):
            layer.lock(state, mod=modifier, apply=False)
            transform.lock(state, mod=modifier, apply=False)
            for gui in guides:
                gui.lock(state, mod=modifier, apply=False)
            guideSetting.lock(state, mod=modifier, apply=apply)

        _changeLockGuideLayer(False, apply=True)

        try:
            name = namingConfig.resolve(
                "settingsName",
                {
                    "componentName": self.name(),
                    "side": self.side(),
                    "section": constants.GUIDE_LAYER_TYPE,
                    "type": "settings",
                },
            )
            guideSetting.rename(name, mod=modifier, apply=False)
            for guide in guides:
                tag = guide.controllerTag()
                if tag is None:
                    continue
                tag.rename("_".join([guide.name(), "tag"]), mod=modifier, apply=False)

            annGrp = layer.attribute("hiveGuideAnnotationGrp").sourceNode()
            annGrp.rename(
                namingutils.composeAnnotationGrpName(namingConfig, compName, side)
            )

            layer.rename(metaName, mod=modifier, apply=False)
            transform.rename(hrcName, mod=modifier, apply=False)
            self.setGuideNaming(namingConfig, modifier)
        finally:
            _changeLockGuideLayer(True)

    def setGuideNaming(self, namingConfig, modifier):
        """Provided for subclassed components to update the naming convention for the
        GuideLayer.

        .. note:: This method is run after postSetupGuide method.

        .. note::
            Calling doIt() on the modifier is not required and will be handled by the
            caller.

        # example of implementation

        .. code-block:: python

            def setDeformNaming(self, namingConfig, modifier):
                compName, compSide = self.name(), self.side()
                for guide in self.guideLayer().iterGuides():
                    name = namingConfig.resolve("guideName", {"componentName": compName,
                                                                 "side": compSide,
                                                                 "id": guide.id(),
                                                                 "type": "guide"})
                    guide.rename(name, maintainNamespace=False, mod=modifier, apply=False)

        :param namingConfig: The naming configuration instance for this component.
        :type namingConfig: :class:`zoo.libs.naming.naming.NameManager`
        :param modifier: The DGModifier instance to use when renaming a node
        :type modifier: :class:`zapi.dgModifier`
        """
        guideLayer = self.meta.guideLayer()
        compName, compSide = self.name(), self.side()
        for guide in guideLayer.iterGuides(includeRoot=True):
            guideName = namingConfig.resolve(
                "guideName",
                {
                    "componentName": compName,
                    "side": compSide,
                    "id": guide.id(),
                    "type": "guide",
                },
            )
            guide.rename(guideName, maintainNamespace=False, mod=modifier, apply=False)
            guideShape = guide.shapeNode()
            if guideShape:
                guideShape.rename(
                    guideName + "Shape", maintainNamespace=False, mod=modifier, apply=False
                )

    def _setDeformNaming(self, namingConfig, modifier):
        compName, side = self.name(), self.side()

        layerMapping = self._meta.layersById(
            (
                constants.INPUT_LAYER_TYPE,
                constants.OUTPUT_LAYER_TYPE,
                constants.DEFORM_LAYER_TYPE,
            )
        )
        settings = []
        for layerNode in layerMapping.values():
            settings.extend(layerNode.settingsNodes())

        def _changeLockGuideLayer(state):
            for layerNode in layerMapping.values():
                try:
                    transform = layerNode.rootTransform()
                    layerNode.lock(state, mod=modifier, apply=False)
                    transform.lock(state, mod=modifier, apply=False)
                except AttributeError:
                    continue

            for settingAttr in settings:
                settingAttr.lock(state, mod=modifier, apply=False)

        try:
            _changeLockGuideLayer(False)
            for layerId, layerNode in layerMapping.items():
                hrcName, metaName = namingutils.composeNamesForLayer(
                    namingConfig, compName, side, layerId
                )
                try:
                    transform = layerNode.rootTransform()
                    layerNode.rename(metaName, mod=modifier, apply=False)
                    transform.rename(hrcName, mod=modifier, apply=False)
                except AttributeError:
                    continue

            for setting in settings:
                name = namingConfig.resolve(
                    "settingsName",
                    {
                        "componentName": compName,
                        "side": side,
                        "section": setting.id(),
                        "type": "settings",
                    },
                )
                setting.rename(name, mod=modifier, apply=False)

        finally:
            _changeLockGuideLayer(True)
        self.setDeformNaming(namingConfig, modifier)

    def setDeformNaming(self, namingConfig, modifier):
        """Provided for subclassed components to update the naming convention for the
        deformLayer, inputLayer and outputLayer.

        .. note:: This method is run after postSetupDeform method.

        # example of implementation

        .. code-block:: python

            def setDeformNaming(self, namingConfig, modifier):
                compName, compSide = self.name(), self.side()
                for jnt in self.deformLayer().iterJoints():
                    jntName = namingConfig.resolve("skinJointName", {"componentName": compName,
                                                                     "side": compSide,
                                                                     "id": jnt.id(),
                                                                     "type": "joint"})
                    jnt.rename(jntName, maintainNamespace=False, mod=modifier, apply=False)

        :param namingConfig: The naming configuration instance for this component.
        :type namingConfig: :class:`zoo.libs.naming.naming.NameManager`
        :param modifier: The DGModifier instance to use when renaming a node
        :type modifier: :class:`zapi.dgModifier`
        """
        layers = self.meta.layersById(
            (
                constants.INPUT_LAYER_TYPE,
                constants.OUTPUT_LAYER_TYPE,
                constants.DEFORM_LAYER_TYPE,
            )
        )
        compName, compSide = self.name(), self.side()
        for jnt in layers[constants.DEFORM_LAYER_TYPE].iterJoints():
            jntName = namingConfig.resolve(
                "skinJointName",
                {
                    "componentName": compName,
                    "side": compSide,
                    "id": jnt.id(),
                    "type": "joint",
                },
            )
            jnt.rename(jntName, maintainNamespace=False, mod=modifier, apply=False)
        for inputNode in layers[constants.INPUT_LAYER_TYPE].inputs():
            name = namingConfig.resolve(
                "inputName",
                {
                    "componentName": compName,
                    "side": compSide,
                    "type": "input",
                    "id": inputNode.id(),
                },
            )
            inputNode.rename(name, maintainNamespace=False, mod=modifier, apply=False)

        for outputNode in layers[constants.OUTPUT_LAYER_TYPE].outputs():
            name = namingConfig.resolve(
                "outputName",
                {
                    "componentName": compName,
                    "side": compSide,
                    "type": "output",
                    "id": outputNode.id(),
                },
            )
            outputNode.rename(name, maintainNamespace=False, mod=modifier, apply=False)

    def _setRigNaming(self, namingConfig, modifier):
        self.setRigNaming(namingConfig, modifier)

    def setRigNaming(self, namingConfig, modifier):
        pass

    def _updateSpaceSwitchComponentDependencies(self, newName, newSide):
        """Updating any components spaceSwitches which contains this component current name as a driver and updates
        it to the new name.

        :param newName: The new name for this component which all component space switches will be updated with.
        :type newName: str
        :param newSide: The new side for this component which all component space switches will be updated with.
        :type newSide: str
        """
        rig = self.rig
        if rig is None:
            return
        self.logger.debug("Updating Space Switching dependencies")
        oldToken = self.serializedTokenKey()
        newToken = ":".join((newName, newSide))
        for comp in rig.iterComponents():
            if comp == self:
                continue
            requiresSave = False
            for space in comp.definition.spaceSwitching:
                for driver in space.drivers:
                    driverExpr = driver.driver
                    if oldToken in driverExpr:
                        driver.driver = driverExpr.replace(oldToken, newToken)
                        requiresSave = True
            if requiresSave:
                comp.saveDefinition(comp.definition)

    def uuid(self):
        """Returns the UUID value for the component

        :return: the uuid4 value
        :rtype: str
        """
        if self._meta is None:
            return self.definition.uuid
        return self._meta.uuid.asString()

    def renameNamespace(self, namespace):
        """Renames the namespace which acts as the component name

        :param namespace: the new namespace
        :type namespace: str
        """
        componentNamespace = self.namespace()

        if om2.MNamespace.namespaceExists(namespace):
            return

        parentNamespace = self.parentNamespace()
        if parentNamespace == om2.MNamespace.rootNamespace:
            return
        currentNamespace = om2.MNamespace.currentNamespace()
        om2.MNamespace.setCurrentNamespace(parentNamespace)
        try:
            om2.MNamespace.renameNamespace(componentNamespace, namespace)
            om2.MNamespace.setCurrentNamespace(currentNamespace)
        except RuntimeError:
            self.logger.error(
                "Failed to Rename Namespace: {}->{}".format(
                    componentNamespace, namespace
                ),
                exc_info=True,
            )
            return

    def namespace(self):
        """Returns the namespace for this node. eg. ":namespace:nodeName"

        :rtype: str
        """
        if self._meta is None:
            return ":".join([om2.MNamespace.currentNamespace(), self.name()])
        name = om2.MNamespace.getNamespaceFromName(self._meta.fullPathName())
        root = om2.MNamespace.rootNamespace()
        if not name.startswith(root):
            name = root + name
        return name

    def parentNamespace(self):
        """Returns the parent namespace of this components namespace.

        :return: the parent namespace, eg. ":parent"
        :rtype: str
        """
        namespace = self.namespace()
        if not namespace:
            return om2.MNamespace.rootNamespace()
        currentNamespace = om2.MNamespace.currentNamespace()
        om2.MNamespace.setCurrentNamespace(namespace)
        try:
            parent = om2.MNamespace.parentNamespace()
            om2.MNamespace.setCurrentNamespace(currentNamespace)
        except RuntimeError:
            parent = om2.MNamespace.rootNamespace()
        return parent

    def removeNamespace(self):
        """Removes the namespace of the this component and moves all children to the root
        namespace

        :rtype: bool
        """
        namespace = self.namespace()
        if namespace:
            om2.MNamespace.moveNamespace(
                namespace, om2.MNamespace.rootNamespace(), True
            )
            om2.MNamespace.removeNamespace(namespace)
            return True
        return False

    def hasGuide(self):
        """Determines if the guide for this component is already been built.

        :rtype: bool
        """
        return self.exists() and self._meta.attribute(constants.HASGUIDE_ATTR).value()

    def hasGuideControls(self):
        """Determines if the guide controls for this component is already been built.

        :return: the value is returned from the meta.hasGuideControls attribute which is set by zoocommands
        :rtype: bool
        """
        return (
            self.exists()
            and self._meta.attribute(constants.HASGUIDE_CONTROLS_ATTR).value()
        )

    def hasRig(self):
        """Determines if this component has built the rig

        :return: the value is returned from the meta.hasRig attribute which is set at build time
        :rtype: bool
        """
        return self.exists() and self._meta.hasRig.asBool()

    def hasSkeleton(self):
        """Determines if this component has built the rig

        :return: the value is returned from the meta.hasRig attribute which is set at build time
        :rtype: bool
        """
        return self.exists() and self._meta.hasSkeleton.asBool()

    def hasPolished(self):
        """Determines if this component has polished

        :return: the value is returned from the meta.hasPolished attribute which is set at build time
        :rtype: bool
        """
        return self.exists() and self._meta.hasPolished.asBool()

    def _setHasGuide(self, state):
        """Sets the hasGuide attribute of the component meta node to the specified state.

        :param state: The new value of the hasGuide attribute.
        :type state: bool
        """
        self.logger.debug("Setting hasGuide to: {}".format(state))
        hasGuideAttr = self._meta.attribute(constants.HASGUIDE_ATTR)
        hasGuideAttr.isLocked = False
        hasGuideAttr.setBool(state)

    def _setHasRig(self, state):
        """Sets the hasRig attribute of the component meta node to the specified state.

        :param state: The new value of the hasRig attribute.
        :type state: bool
        """
        self.logger.debug("Setting hasRig to: {}".format(state))
        hasRigAttr = self._meta.attribute(constants.HASRIG_ATTR)
        hasRigAttr.isLocked = False
        hasRigAttr.setBool(state)

    def _setHasSkeleton(self, state):
        """Sets the hasSkeleton attribute of the component meta node to the specified state.

        :param state: The new value of the hasSkeleton attribute.
        :type state: bool
        """
        self.logger.debug("Setting hasSkeleton to: {}".format(state))
        hasSkelAttr = self._meta.attribute(constants.HASSKELETON_ATTR)
        hasSkelAttr.isLocked = False
        hasSkelAttr.setBool(state)

    def _setHasPolished(self, state):
        """Sets the hasPolished attribute of the component meta node to the specified state.

        :param state: The new value of the hasPolished attribute.
        :type state: bool
        """
        self.logger.debug("Setting hasPolished to: {}".format(state))
        hasSkelAttr = self._meta.attribute(constants.HASPOLISHED_ATTR)
        hasSkelAttr.isLocked = False
        hasSkelAttr.setBool(state)

    def parent(self):
        """Returns the parent component object.

        :rtype: :class:`Component` or None
        """
        if self._meta is None:
            return
        if self.isBuildingRig or self.isBuildingGuide or self.isBuildingSkeleton:
            return self._buildObjectCache.get("parent")
        for parentMeta in self._meta.iterMetaParents(recursive=False):
            if parentMeta.hasAttribute(constants.ISCOMPONENT_ATTR):
                return self._rig.component(
                    parentMeta.attribute(constants.HNAME_ATTR).value(),
                    parentMeta.attribute(constants.SIDE_ATTR).value(),
                )

    def hasParent(self):
        """Whether this component has a parent component.

        :rtype: bool
        """
        if self._meta is None:
            return False
        for parentMeta in self._meta.iterMetaParents():
            if parentMeta.hasAttribute(constants.ISCOMPONENT_ATTR):
                return True
        return False

    def children(self, depthLimit=256):
        """Generator method which returns all component children instances.

        :param depthLimit: The depth limit which to search within the meta network before stopping.
        :type depthLimit: int
        :return: Generator where each element is a component instance
        :rtype: list[:class:`Component`]
        """
        if not self.exists():
            return
        for childMeta in self._meta.iterMetaChildren(depthLimit=depthLimit):
            if childMeta.hasAttribute(constants.ISCOMPONENT_ATTR):
                comp = self._rig.component(
                    childMeta.attribute(constants.HNAME_ATTR).value(),
                    childMeta.attribute(constants.SIDE_ATTR).value(),
                )
                if comp:
                    yield comp

    def setParent(self, parentComponent, driver=None):
        """Sets the parent component for the current component.

        :param parentComponent: The parent component to set.
        :type parentComponent: :class:Component
        :param driver: The driver guide.
        :type driver: :class:Guide
        """
        if parentComponent == self:
            return False
        if driver:
            if not parentComponent.idMapping()[constants.DEFORM_LAYER_TYPE].get(
                driver.id()
            ):
                self.logger.warning(
                    "Setting parent to a guide which doesn't belong to a joint(Sphere shapes) isn't"
                    "allowed"
                )
                return False
        if parentComponent is None:
            self.removeAllParents()
            self._meta.addMetaParent(self.rig.componentLayer())
            return False
        didSetParent = self._setMetaParent(parentComponent)
        if not didSetParent:
            return False
        self.definition.parent = ":".join(
            [parentComponent.name(), parentComponent.side()]
        )
        if not driver:
            return False
        elif not self.hasGuide() and not self.isBuildingGuide:
            self.logger.warning("Guide system has not been built")
            return False
        guideLayer = self.guideLayer()
        rootGuide = guideLayer.guide("root")
        if not rootGuide:
            self.logger.error("No root guide on this component, unable to set parent!")
            return False
        rootSrt = rootGuide.srt(0)
        zapi.deleteConstraints(
            [rootSrt]
        )  # ensure we delete the previous constraint first
        self.removeUpstreamAnnotations(parentComponent=parentComponent)

        worldMatrix = rootGuide.worldMatrix()
        # pre-calculate the local matrix for the guide from driver otherwise we'll get double transforms
        localMatrixOffset = worldMatrix * driver.worldMatrix().inverse()
        rootSrt.setWorldMatrix(driver.worldMatrix())
        # before we do any constraining we need to move the srt to the child guide.
        driverGuideLayer = parentComponent.guideLayer()
        parentConstraint, parentUtilities = zapi.buildConstraint(
            rootSrt,
            {
                "targets": (
                    (
                        driver.fullPathName(partialName=True, includeNamespace=False),
                        driver,
                    ),
                )
            },
            constraintType="parent",
            maintainOffset=True,
            trace=True,
        )
        scaleConstraint, scaleUtilities = zapi.buildConstraint(
            rootSrt,
            {
                "targets": (
                    (
                        driver.fullPathName(partialName=True, includeNamespace=False),
                        driver,
                    ),
                )
            },
            constraintType="scale",
            maintainOffset=True,
            trace=True,
        )
        rootGuide.setMatrix(localMatrixOffset)

        name = "_".join([driver.name(includeNamespace=False), "annotation"])
        guideLayer.createAnnotation(
            name, rootGuide, driver, parent=guideLayer.rootTransform()
        )
        # setup the layer meta data on the guideLayer that way we have knowledge of the upstream guide
        # which in turn plays an important part in determining match joint which we'll parent too within
        # the deformLayer also Input connections
        driverGuidePlug = driverGuideLayer.guidePlugById(driver.id()).child(0)
        drivenGuidePlug = (
            guideLayer.guidePlugById("root").child(4).nextAvailableDestElementPlug()
        )
        destGuidePlug = drivenGuidePlug.child(0)
        destConstraintArray = drivenGuidePlug.child(1)
        driverGuidePlug.connect(destGuidePlug)
        for n in parentUtilities + scaleUtilities:
            n.message.connect(destConstraintArray.nextAvailableDestElementPlug())

    def _setMetaParent(self, component):
        if self._meta is None:
            self.logger.warning("Component has no meta node specified: {}".format(self))
            return False
        parents = list(self._meta.iterMetaParents())

        if component.meta in parents:
            return True
        self.removeAllParents()
        # by default the meta node parent is the componentLayer, if we set a new parent
        # then see if the component layer meta is connected and just disconnect.
        for p in parents:
            if (
                p.attribute(base.MCLASS_ATTR_NAME).asString()
                == constants.COMPONENT_LAYER_TYPE
            ):
                self._meta.removeParent(p)
                break
        self._meta.addMetaParent(component.meta)
        return True

    def removeParent(self, parentComponent=None):
        """Remove parent relationship between this component and the parent component.

        :param parentComponent: If None then remove all parents.
        :type parentComponent: :class:Component or None
        """
        if not self.exists():
            return
        parent = None
        if parentComponent:
            parent = parentComponent.meta
        self.removeUpstreamAnnotations(parentComponent=parentComponent)
        self._meta.removeParent(parent)
        self._meta.addMetaParent(self._rig.componentLayer())
        self.definition.parent = None
        self.definition.connections = {}
        self.saveDefinition(self.definition)

    def removeAllParents(self):
        """Removes all parent components from the current component."""
        if not self.exists():
            self.logger.warning("Current component doesn't exist")
            return
        self.disconnectAll()
        parentComp = self.parent()
        if parentComp:
            self.removeParent(parentComp)

    def disconnectAllChildren(self):
        """Disconnects all child components from the current component."""
        for childComponent in self.children(depthLimit=1):
            childComponent.disconnect(self)

    def disconnect(self, component):
        """Disconnects the specified component from the current component.

        :param component: The component to disconnect.
        :type component: :class:`Component`
        """
        if not self.hasGuide():
            self.logger.debug("Missing guide skipping disconnect")
            return
        guideLayer = self.guideLayer()
        for guide in guideLayer.iterGuides():
            parentSrt = guide.srt()
            if not parentSrt:
                continue
            for const in zapi.spaceswitching.iterConstraints(parentSrt):
                for _, driver in const.drivers():
                    if driver is None:
                        continue
                    try:
                        driverComponent = self.rig.componentFromNode(driver)
                        if driverComponent != component:
                            continue
                    except errors.MissingMetaNode:
                        continue
                    const.delete()

    def disconnectAll(self):
        """Disconnects all guides by deleting incoming constraints on all guides and
        disconnects the meta data.
        """
        if not self.hasGuide():
            return
        # to remove a parent we have to disconnect from the meta node guide sourceNodes attributes
        guideLayer = self.guideLayer()
        for guideCompoundPlug in guideLayer.iterGuideCompound():
            sourceNode = guideCompoundPlug.child(0).sourceNode()
            if sourceNode is None:
                continue
            guide = hnodes.Guide(sourceNode.object())

            parentSrt = guide.srt()
            if not parentSrt:
                continue
            for const in zapi.spaceswitching.iterConstraints(parentSrt):
                const.delete()
            # remove the meta data connections
            for sourceGuideElement in guideCompoundPlug.child(4):
                sourceGuideElement.child(0).disconnectAll()  # source guide plug

    @contextlib.contextmanager
    def disconnectComponentContext(self):
        """A context manager to pin and unpin this component and all its children"""
        try:
            self.pin()
            for child in self.children(depthLimit=1):
                child.pin()
            yield
        finally:
            self.unPin()
            for child in self.children(depthLimit=1):
                child.unPin()

    def removeUpstreamAnnotations(self, parentComponent=None):
        """Removes upstream annotations from this component's guide layer

        :param parentComponent: The parent component to remove the annotations from. \
        If None, all annotations will be removed.
        :type parentComponent: :class:`Component` or None
        """
        if not self.hasGuide():
            self.logger.debug("Component has no guide: {}".format(self))
            return
        guideLayer = self.guideLayer()
        if not guideLayer:
            self.logger.debug("No Guide Layer no component: {}".format(self))
            return
        for i in guideLayer.annotations():
            endGuide = i.endNode()
            annGuideParent = self.rig.componentFromNode(
                endGuide
            )  # todo: this isn't required or we should just get upstream metaNode to speed things up
            if parentComponent is None:
                i.delete()
            elif annGuideParent == parentComponent:
                i.delete()

    def inputLayer(self):
        """Returns the Input layer node from the component, retrieved from the components meta node

        :rtype: :class:`layers.HiveInputLayer` or None
        """
        root = self._meta
        if not root:
            return
        if self.isBuildingRig or self.isBuildingGuide or self.isBuildingSkeleton:
            return self._buildObjectCache.get(layers.HiveInputLayer.id)
        return root.layer(constants.INPUT_LAYER_TYPE)

    def outputLayer(self):
        """Returns the output layer node from the component, retrieved from the components meta node

        :rtype: :class:`layers.HiveOutputLayer` or None
        """
        root = self._meta
        if not root:
            return
        if self.isBuildingRig or self.isBuildingGuide or self.isBuildingSkeleton:
            return self._buildObjectCache.get(layers.HiveOutputLayer.id)
        return root.layer(constants.OUTPUT_LAYER_TYPE)

    def deformLayer(self):
        """Returns the deform layer node from the component, retrieved from the components meta node

        :rtype: :class:`layers.HiveDeformLayer` or None
        """
        root = self._meta
        if not root:
            return
        if self.isBuildingRig or self.isBuildingGuide or self.isBuildingSkeleton:
            return self._buildObjectCache.get(layers.HiveDeformLayer.id)
        return root.layer(constants.DEFORM_LAYER_TYPE)

    def rigLayer(self):
        """Returns the rig layer node from the component, retrieved from the components meta node

        :rtype: :class:`layers.HiveRigLayer` or None
        """
        root = self._meta
        if not root:
            return
        if self.isBuildingRig or self.isBuildingGuide or self.isBuildingSkeleton:
            return self._buildObjectCache.get(layers.HiveRigLayer.id)
        return root.layer(constants.RIG_LAYER_TYPE)

    def geometryLayer(self):
        """Returns the geometry layer node from the component, retrieved from the components meta node.

        :rtype: :class:`layers.HiveGeometryLayer` or None.
        """
        root = self._meta
        if not root:
            return
        if self.isBuildingRig or self.isBuildingGuide or self.isBuildingSkeleton:
            return self._buildObjectCache.get(layers.HiveGeometryLayer.id)
        return root.layer(constants.GEOMETRY_LAYER_TYPE)

    def guideLayer(self):
        """Returns the guide layer node from the component, retrieved from the components meta node

        :rtype: :class:`layers.HiveGuideLayer` or None
        """
        root = self._meta
        if not root:
            return
        cached = self._buildObjectCache.get(layers.HiveGuideLayer.id)
        if cached:
            return cached
        return root.layer(constants.GUIDE_LAYER_TYPE)

    def findLayer(self, layerType):
        """Finds and returns the components layer instance.

        :param layerType: The layer type ie. constants.GUIDE_LAYER_TYPES
        :type layerType: str
        :return: The Hive layer meta node instance.
        :rtype: :class:`layers.HiveLayer`
        """
        if layerType not in constants.LAYER_TYPES:
            raise ValueError(
                "Unaccepted layer type: {], acceptedTypes: {}".format(
                    layerType, constants.LAYER_TYPES
                )
            )
        if not self.exists():
            return
        meta = self._meta
        return meta.layer(layerType)

    def controlPanel(self):
        """Returns the controlPanel from the rigLayer.

        :return: The Control panel node from the scene.
        :rtype: :class:`hnodes.SettingNode` or None
        """
        rigLayer = self.rigLayer()
        if rigLayer is not None:
            return rigLayer.controlPanel()

    @profiling.fnTimer
    def duplicate(self, name, side):
        """Duplicates the current component and renames it to the new name, This is done by serializing the current
        component then creating a new instance of the class

        :param name: the new name for the component
        :type name: str
        :param side: The mirrored component side.
        :type side: str
        :rtype: :class:`Component`
        """
        currentDefinition = copy.deepcopy(self.serializeFromScene())

        initComponent = self.rig.createComponent(
            name=name,
            side=side,
            definition=baseDef.loadDefinition(
                currentDefinition, self._originalDefinition
            ),
        )
        return initComponent

    @profiling.fnTimer
    def mirror(self, translate=("x",), rotate="yz", parent=om2.MObject.kNullObj):
        """Method to override how the mirroring of component guides are performed.

        By Default all guides,guideShapes and all srts are mirror with translation and rotation(if mirror attribute is
        True).

        :note:
            Unless you need complete control over the math and all mirror behaviour it is recommended to use
            :meth:`Component.preMirror` and :meth:`Component.postMirror` instead.

        :param translate: The axis to mirror on ,default is ("x",).
        :type translate: tuple
        :param rotate: The mirror plane to mirror rotations on, supports "xy", "yz", "xz", defaults to "yz".
        :type rotate: str
        :param parent: the parent object to use as the mirror space, default is kNullObj making mirroring happen based \
        on world (0, 0, 0).
        :type parent: om2.MObject
        :return: A list of tuples with the first element of each tuple the hiveNode and the second element \
        the original world Matrix.
        :rtype: list(tuple(:class:`zapi.DagNode`, :class:`om2.MMatrix`))
        """
        if not self.hasGuide():
            return []
        guideLayer = self.guideLayer()
        self.preMirror(translate, rotate, parent)
        data = componentutils.mirror(
            self, guideLayer, translate=translate, rotate=rotate
        )
        self.postMirror(translate, rotate, parent)
        return data

    def preMirror(self, translate=("x",), rotate="yz", parent=om2.MObject.kNullObj):
        """Method to override to handle pre-mirror operations, this is used in mirror() and in the
        apply symmetry command.Useful for unlocking attributes, deleting any constraint or any live
        interactions with the guide system.

        :param translate: The axis to mirror on ,default is ("x",).
        :type translate: tuple
        :param rotate: The mirror plane to mirror rotations on, supports "xy", "yz", "xz", defaults to "yz".
        :type rotate: str
        :param parent: the parent object to use as the mirror space, default is kNullObj making mirroring happen based \
        on world (0, 0, 0).
        :type parent: om2.MObject
        :return: A list of tuples with the first element of each tuple the hiveNode and the second element \
        the original world Matrix.
        :rtype: list(tuple(:class:`zapi.DagNode`, :class:`om2.MMatrix`))
        """
        pass

    def postMirror(self, translate=("x",), rotate="yz", parent=om2.MObject.kNullObj):
        """Method to override to handle post-mirror operations, this is used in mirror() and in the
        apply symmetry command.Useful for reapplying any state to the guides eg.locking attributes.

        :param translate: The axis to mirror on ,default is ("x",).
        :type translate: tuple
        :param rotate: The mirror plane to mirror rotations on, supports "xy", "yz", "xz", defaults to "yz".
        :type rotate: str
        :param parent: the parent object to use as the mirror space, default is kNullObj making mirroring happen based \
        on world (0, 0, 0).
        :type parent: om2.MObject
        :return: A list of tuples with the first element of each tuple the hiveNode and the second element \
        the original world Matrix.
        :rtype: list(tuple(:class:`zapi.DagNode`, :class:`om2.MMatrix`))
        """
        pass

    def pin(self):
        """Pins the current component in place.

        This works by serializing all upstream connections on the guideLayer meta
        then we disconnect while maintaining parenting(metadata) then in :meth:`Component.unpin`
        We reapply the stored connections
        """
        if not self.hasGuide():
            return {}
        guideLayer = self.guideLayer()
        if not guideLayer or guideLayer.isPinned():
            return {}
        self.logger.debug("Activating pin")
        connection = self.serializeComponentGuideConnections()
        guideLayer.pinnedConstraints.set(json.dumps(connection))
        guideLayer.pinned.set(True)
        self.disconnectAll()
        return connection

    def unPin(self):
        """Unpins the component.

        :return: Whether the unpin was successful.
        :rtype: bool
        """
        if not self.hasGuide():
            return False
        guideLayer = self.guideLayer()
        if not guideLayer or not guideLayer.isPinned():
            return False
        self.logger.debug("Activating unPin")
        connection = json.loads(guideLayer.pinnedConstraints.value())
        self._definition.connections = connection
        self.saveDefinition(self._definition)
        guideLayer.pinnedConstraints.set("")
        guideLayer.pinned.set(False)
        self.deserializeComponentConnections(layerType=constants.GUIDE_LAYER_TYPE)
        return True

    @profiling.fnTimer
    def serializeFromScene(self, layerIds=None):
        """Serializes the component from the root transform down using the individual layers, each layer
        has its own logic so see those classes for information.

        :param layerIds: An iterable of Hive layer id types which should be serialized
        :type layerIds: iterable[str]
        :return:
        :rtype: :class:`baseDef.ComponentDefinition`
        """
        if not self.hasGuide() and not self.hasSkeleton() and not self.hasRig():
            try:
                self._definition.update(
                    defutils.parseRawDefinition(self._meta.rawDefinitionData())
                )
            except ValueError:
                self.logger.warning(
                    "Definition in scene isn't valid, skipping definition update"
                )
            return self._definition

        defini = self._meta.serializeFromScene(layerIds)
        data = self.serializeComponentGuideConnections()
        defini["connections"] = data
        parentComponent = self.parent()
        defini["parent"] = (
            ":".join([parentComponent.name(), parentComponent.side()])
            if parentComponent
            else ""
        )
        self._definition.update(defini)
        self.saveDefinition(self._definition)
        return self.definition

    @profiling.fnTimer
    def _mergeComponentIntoContainer(self):
        """Private method to take all connected nodes recursively and add them to the container
        if the container doesn't exist one will be created using the ::method`Component.createContainer`

        :note: this is only necessary due to container.makeCurrent not adding nodes to the container

        :rtype: :class:`zapi.ContainerAsset`
        """
        cont = self.container()
        if cont is None:
            cont = self.createContainer()
        self.logger.debug("Merging nodes which are missing from container")
        meta = self._meta
        rootTransform = meta.rootTransform()
        nodesToAdd = [rootTransform, meta]

        for i in meta.layersById(
            (
                constants.GUIDE_LAYER_TYPE,
                constants.RIG_LAYER_TYPE,
                constants.INPUT_LAYER_TYPE,
                constants.OUTPUT_LAYER_TYPE,
                constants.DEFORM_LAYER_TYPE,
                constants.XGROUP_LAYER_TYPE,
            )
        ).values():
            if not i:
                continue
            objects = [i, i.rootTransform()] + list(i.settingsNodes())
            objects.extend(list(i.extraNodes()))
            nodesToAdd.extend(obj for obj in objects if obj and obj not in nodesToAdd)
        if nodesToAdd:
            cont.addNodes(nodesToAdd)
        return cont

    def nodes(self):
        """Generator function which returns every node linked to this component.

        :rtype: Iterable[:class:`zapi.DGNode` or :class:`zapi.DagNode`]
        """
        container = self.container()
        if container is not None:
            yield container
        meta = self.meta
        if meta is not None:
            yield meta
        transform = meta.rootTransform()
        if transform is not None:
            yield transform

        for i in self._meta.layersById(
            (
                constants.GUIDE_LAYER_TYPE,
                constants.RIG_LAYER_TYPE,
                constants.INPUT_LAYER_TYPE,
                constants.OUTPUT_LAYER_TYPE,
                constants.DEFORM_LAYER_TYPE,
                constants.XGROUP_LAYER_TYPE,
            )
        ).values():
            if not i:
                continue
            yield i
            for child in i.iterChildren():
                yield child

    def componentParentGuide(self):
        """Returns the connected parent component guide node.

        :return: Tuple for the parent component and the connected parent guide node.
        :rtype: tuple[:class:`Component`, :class:`hnodes.Guide`] or tuple[None, None]
        """
        self.logger.debug("Searching for components parent guide")

        if not self.hasGuide():
            return None, None
        guideLayer = self.guideLayer()
        # |- hguides
        #     |- sourceGuides[]
        #                 |- constraintNodes
        rootGuide = guideLayer.guide("root")
        if not rootGuide:
            return None, None

        rootSrt = rootGuide.srt(0)
        if not rootSrt:
            return None, None
        for constraint in zapi.iterConstraints(rootSrt):
            for label, target in constraint.drivers():
                if target and hnodes.Guide.isGuide(target):
                    comp = self.rig.componentFromNode(target)
                    return comp, hnodes.Guide(target.object())
        return None, None

    def componentParentJoint(self, parentNode=None):
        """Returns the parent components connected joint.

        This is mostly called by the build code.

        :param parentNode: Default parent node when None exist.
        :type parentNode: :class:`hnodes.Joint` or None
        :return: The parent components joint or the provided default via `parentNode` argument.
        :rtype: :class:`hnodes.Joint` or :class:`hnodes.DagNode` or None
        """
        self.logger.debug("Searching for components parent joint")
        parentNode = parentNode or self.deformLayer().rootTransform()
        childInputLayer = self.inputLayer()
        if not childInputLayer:
            return parentNode
        parentComponent = self.parent()
        if not parentComponent:
            self.logger.debug(
                "No Parent component found returning default parent: {}".format(
                    parentNode
                )
            )
            return parentNode

        parentDeformLayer = parentComponent.deformLayer()
        if not parentDeformLayer:
            return parentNode
        inputElement = childInputLayer.rootInputPlug()
        for sourceInput in inputElement.child(3):
            hOutputNodePlug = sourceInput.child(0).source()  # hOutputs[*].outputNode
            if hOutputNodePlug is None:
                continue
            # grab the parent component output node
            parentOutputLayer = layers.HiveOutputLayer(hOutputNodePlug.node().object())
            parentOutputRootTransform = (
                parentOutputLayer.rootTransform()
            )  # used for checking iterParent limit
            outputId = (
                hOutputNodePlug.parent().child(1).value()
            )  # e.g. rootMotion outputNode if we're the spine
            parentJoint = parentDeformLayer.joint(outputId)
            if not parentJoint:
                parentJoints = {i.id(): i for i in parentDeformLayer.iterJoints()}
                totalJoints = len(list(parentJoints.keys()))
                if totalJoints == 0:
                    return parentNode
                if totalJoints == 1:
                    return list(parentJoints.values())[0]
                parentOutputNode = hOutputNodePlug.sourceNode()
                while parentJoint is None:
                    parentOutputNode = parentOutputNode.parent()
                    if parentOutputNode == parentOutputRootTransform:
                        break
                    outputId = parentOutputNode.attribute(constants.ID_ATTR).value()
                    parentJoint = parentJoints.get(outputId)

            return parentJoint or parentNode

        return parentNode

    def _generateObjectCache(self):
        self._buildObjectCache = self._meta.layerIdMapping()
        self._buildObjectCache["container"] = self.container()
        self._buildObjectCache["parent"] = self.parent()
        self._buildObjectCache["naming"] = self.namingConfiguration()
        self._buildObjectCache["subsystems"] = self.subsystems()

    def spaceSwitchUIData(self):
        """Returns the available space Switch driven and driver settings for this component.
        Drivers marked as internal will force a non-editable driver state in the UI driver column and
        only displayed in the "driver component" column.

        Below is an example function implementation.

        .. code-block:: python

            def spaceSwitchUiData(self)
                driven = [api.SpaceSwitchUIDriven(id_="myControlId", label="User DisplayLabel")]
                drivers = [api.SpaceSwitchUIDriver(id_="myControlId", label="User DisplayLabel", internal=True)]
                return {"driven": driven,
                        "drivers": drivers}

        :rtype: dict
        """
        # contains the information about what space switch controls are available for either being driven
        # or being drivers of space switches.
        return {"driven": [], "drivers": []}

    def subsystems(self):
        """Returns the subsystems for the current component, if the subsystems have already been created,
        the cached version is returned.

        :return: OrderedDict with keys of the subsystem names and values of the corresponding subsystem object
        :rtype: :class:`OrderedDict[str, :class:`basesybsystem.BaseSubsystem`]`

        Example return value::

            {
                "twists": :class:`zoo.libs.hive.library.subsystems.twistsubsystem.TwistSubSystem`,
                "bendy": :class:`zoo.libs.hive.library.subsystems.bendysubsystem.BendySubSystem`
            }

        """
        cached = self._buildObjectCache.get("subsystems")
        if cached is not None:
            return cached
        return self.createSubSystems()

    def createSubSystems(self):
        """Creates the subsystems for the current component and returns them in an OrderedDict.

        :return: OrderedDict with keys of the subsystem names and values of the corresponding subsystem object
        :rtype: OrderedDict

         Example return value::

            {
                "twists": :class:`zoo.libs.hive.library.subsystems.twistsubsystem.TwistSubSystem`,
                "bendy": :class:`zoo.libs.hive.library.subsystems.bendysubsystem.BendySubSystem`
            }
        """
        return OrderedDict()

    @profiling.fnTimer
    def buildGuide(self):
        """Builds the guide system for this component. This method is responsible for creating the guide system,
        and setting up the guide layer metadata.

        :raises: :class:`errors.ComponentDoesntExistError` if the component doesn't exist.
        :raises: :class:`errors.BuildComponentGuideUnknownError` if an unknown error occurs while building \
        the guide system
        """
        if not self.exists():
            raise errors.ComponentDoesntExistError(self.definition.name)
        self._generateObjectCache()
        if self.hasGuide():
            self.guideLayer().rootTransform().show()
        if self.hasPolished():
            self._setHasPolished(False)
        hasSkeleton = self.hasSkeleton()
        if hasSkeleton:
            self._setHasSkeleton(False)
        self.logger.debug("Building guide: {}".format(self.name()))
        self.isBuildingGuide = True
        container = self.container()
        if container is None:
            container = self.createContainer()
            self._buildObjectCache["container"] = container
        container.makeCurrent(True)
        container.lock(False)

        self.logger.debug(
            "starting guide build with namespace {}".format(self.namespace())
        )
        try:
            hrcName, metaName = namingutils.composeNamesForLayer(
                self.namingConfiguration(),
                self.name(),
                self.side(),
                constants.GUIDE_LAYER_TYPE,
            )
            guideLayer = self._meta.createLayer(
                constants.GUIDE_LAYER_TYPE,
                hrcName,
                metaName,
                parent=self._meta.rootTransform(),
            )
            guideLayer.updateMetaData(
                self._definition.guideLayer.get(constants.METADATA_DEF_KEY, [])
            )
            self._buildObjectCache[layers.HiveGuideLayer.id] = guideLayer
            self.preSetupGuide()
            self.setupGuide()
            self.postSetupGuide()
            self.saveDefinition(self._definition)
            self._setHasGuide(True)
            if hasSkeleton:
                resetJointTransforms(
                    self.deformLayer(), self.definition.guideLayer, self.idMapping()
                )
        except Exception:
            self.logger.error("Failed to setup guides", exc_info=True)
            self._setHasGuide(False)
            raise errors.BuildComponentGuideUnknownError(
                "Failed {}".format("_".join([self.name(), self.side()]))
            )
        finally:
            container.makeCurrent(False)
            self.isBuildingGuide = False
            self._buildObjectCache = {}
        return True

    @profiling.fnTimer
    def buildDeform(self, parentNode=None):
        """Internal Method used by the build system, shouldn't be overridden by subclasses unless you want full
        control of every part of the deformation layer being built.

        :param parentNode: The DeformLayer root transform node
        :type parentNode: :class:`zapi.DagNode`
        """
        if not self.exists():
            raise errors.ComponentDoesntExistError(self.definition.name)
        self._generateObjectCache()
        if self.hasPolished():
            self._setHasPolished(False)
        self.serializeFromScene(layerIds=(constants.GUIDE_LAYER_TYPE,))
        self.isBuildingSkeleton = True
        container = self.container()
        try:
            if container is None:
                container = self.createContainer()
                self._buildObjectCache["container"] = container
            container.makeCurrent(True)
            container.lock(False)
            self.setupInputs()
            self.deserializeComponentConnections(layerType=constants.INPUT_LAYER_TYPE)
            hrcName, metaName = namingutils.composeNamesForLayer(
                self.namingConfiguration(),
                self.name(),
                self.side(),
                constants.DEFORM_LAYER_TYPE,
            )
            layer = self._meta.createLayer(
                constants.DEFORM_LAYER_TYPE,
                hrcName,
                metaName,
                parent=self._meta.rootTransform(),
            )
            layer.updateMetaData(
                self._definition.deformLayer.get(constants.METADATA_DEF_KEY, [])
            )
            self._buildObjectCache[layers.HiveDeformLayer.id] = layer
            if container:
                container.addNode(layer)
            parentJoint = self.componentParentJoint(parentNode)
            self._setupGuideOffsets(parentJoint)

            self.logger.debug(
                "Parent Joint for component: {}: joint: {}".format(self, parentJoint)
            )
            self.preSetupDeformLayer()
            self.setupDeformLayer(parentJoint)
            self.setupOutputs(parentJoint)
            self.postSetupDeform(parentJoint)
            self.blackBox = False
            self.saveDefinition(self._definition)
            self._setHasSkeleton(True)

        except Exception:
            msg = "Failed to build rig for component {}".format(
                "_".join([self.name(), self.side()])
            )
            self.logger.error(msg, exc_info=True)
            self._setHasSkeleton(False)
            raise errors.BuildComponentDeformUnknownError(msg)
        finally:
            self.isBuildingSkeleton = False
            container.makeCurrent(False)
            self._buildObjectCache = {}
        return True

    @profiling.fnTimer
    def buildRig(self, parentNode=None):
        """Build the rig for the current component.

        :param parentNode: parent node for the rig to be parented to. If None, the rig will not be parented to anything.
        :type parentNode: :class:`zapi.DagNode` or None

        :raises: :exc:`ComponentDoesntExistError` if the current component doesn't exist
        :raises: :exc:`BuildComponentRigUnknownError` if building the rig fails
        """
        if not self.exists():
            raise errors.ComponentDoesntExistError(self.definition.name)
        elif self.hasRig():
            self.logger.debug(
                "Already have a rig, skipping the build: {}".format(self.name())
            )
            return True

        self._generateObjectCache()
        if self.hasPolished():
            self._setHasPolished(False)
        # pick up the data from the scene first
        self.serializeFromScene()
        resetJointTransforms(
            self.deformLayer(), self.definition.guideLayer, self.idMapping()
        )
        self.isBuildingRig = True
        container = self.container()
        try:
            self.logger.debug("Setting up component rig: {}".format(self.name()))

            if container is None:
                container = self.createContainer()
                self._buildObjectCache["container"] = container
            container.makeCurrent(True)
            container.lock(False)
            parentJoint = self.componentParentJoint(parentNode)
            self.preSetupRig(parentJoint)
            self.setupRig(parentJoint)
            self.postSetupRig(parentJoint)
            self._setHasRig(True)
            self.blackBox = self.configuration.blackBox
            self.saveDefinition(self._definition)
        except Exception:
            msg = "Failed to build rig for component {}".format(
                "_".join([self.name(), self.side()])
            )
            self.logger.error(msg, exc_info=True)
            self._setHasRig(False)
            raise errors.BuildComponentRigUnknownError(msg)
        finally:
            self.isBuildingRig = False
            container.makeCurrent(False)
            self._buildObjectCache = {}
        return True

    def idMapping(self):
        """Returns the guide ID -> layer node ID mapping acting as a lookup table.

        When live linking the joints with the guides this table is used to link the
        correct guide transform to the deform joint. This table is also used when
        determining which deformJoints should be deleted from the scene if the
        guide doesn't exist anymore. Among other aspects of the build system.


        .. note::
            This method can be overridden in subclasses, by default it maps the guide.id as a 1-1

        .. note::
            If there's no joint for the guide then it should have an empty string

        .. code-block:: python

            def idMapping():
                id = {"pelvis": "pelvis",
                        "gimbal": "",
                        "hips": "",
                        "fk01": "bind01"}
                return {constants.DEFORM_LAYER_TYPE: ids,
                        constants.INPUT_LAYER_TYPE: ids,
                        constants.OUTPUT_LAYER_TYPE: ids,
                        constants.RIG_LAYER_TYPE: ids
                }

        :return: The guideId mapped to the  ids for each layer
        :rtype: dict

        """
        ids = {
            k.id: k.id for k in self.definition.guideLayer.iterGuides(includeRoot=False)
        }
        return {
            constants.DEFORM_LAYER_TYPE: ids,
            constants.INPUT_LAYER_TYPE: ids,
            constants.OUTPUT_LAYER_TYPE: ids,
            constants.RIG_LAYER_TYPE: ids,
        }

    def preSetupGuide(self):
        """The pre setup guide is run before the buildGuide() function is run
        internally, hive will auto generate the guide structure using the definition data.
        You can override this method, but you'll either need to handle the guide and all of its
        settings yourself or call the super class first.

        """
        self.logger.debug("Running pre-setup guide")
        # guideSettings
        self._setupGuideSettings()
        guideLayer = self.guideLayer()
        self.logger.debug("Generating guides from definition")
        currentGuides = {i.id(): i for i in guideLayer.iterGuides()}
        compName, side = self.name(), self.side()
        namingConfig = self.namingConfiguration()
        # reparent existing guides if required
        postParenting = []
        for (
            data
        ) in self.definition.guideLayer.iterGuides():  # type: baseDef.GuideDefinition
            guideId = data["id"]
            currentSceneGuide = currentGuides.get(guideId)  # type: hnodes.Guide
            name = namingConfig.resolve(
                "guideName",
                {
                    "componentName": compName,
                    "side": side,
                    "id": guideId,
                    "type": "guide",
                },
            )
            if currentSceneGuide is not None:
                currentSceneGuide.createAttributesFromDict(
                    {v["name"]: v for v in data.get("attributes", [])}
                )
                currentSceneGuide.rename(name)
                _, parentId = currentSceneGuide.guideParent()
                if parentId != data["parent"]:
                    postParenting.append((currentSceneGuide, data["parent"]))
                continue

            shapeTransform = data.get("shapeTransform", {})
            self.logger.debug("Creating scene guide: {}".format(name))
            # compose the entire guide dict and create it.
            newGuide = guideLayer.createGuide(
                name=name,
                rotateOrder=data.get("rotateOrder", 0),
                shape=data.get("shape"),
                id=data["id"],
                parent=data.get("parent", "root"),
                root=data.get("root", False),
                color=data.get("color"),
                translate=data.get("translate", (0, 0, 0)),
                rotate=data.get("rotate", (0, 0, 0, 1.0)),
                scale=data.get("scale", (1.0, 1.0, 1.0)),
                worldMatrix=data.get("worldMatrix"),
                srts=data.get("srts", []),
                selectionChildHighlighting=self.configuration.selectionChildHighlighting,
                shapeTransform={
                    "rotate": shapeTransform.get("rotate", (0, 0, 0, 1)),
                    "translate": shapeTransform.get("translate", (0, 0, 0)),
                    "scale": shapeTransform.get("scale", (1.0, 1.0, 1.0)),
                },
                pivotShape=data.get("pivotShape"),
                pivotColor=data.get("pivotColor", constants.DEFAULT_GUIDE_PIVOT_COLOR),
                attributes=data.get("attributes", []),
            )

            currentGuides[guideId] = newGuide

            # added the guide constraint utilities to the metadata
            shapeNode = newGuide.shapeNode()
            if shapeNode:
                [
                    guideLayer.addExtraNodes(const.utilityNodes())
                    for const in zapi.iterConstraints(shapeNode)
                ]

        for childGuide, parentId in postParenting:
            childGuide.setParent(currentGuides[parentId])

        self.logger.debug("Completed pre setup guide")

    def updateGuideSettings(self, settings):
        """Method that allows overloading updates of the guides settings of the definition which will be change
        the state of the scene if the guides are present.

        It's  useful the overload this where changing a certain setting requires other
        per component updates ie. rebuilds.

        :param settings:
        :type settings: dict[name: value]
        :return: The Original guide settings in the same format as settings, this will be used \
        in zoo commands for handling undo.
        :rtype: dict[name: value]
        """

        definition = self._definition
        originalSettings = {}
        guideSettingsNode = None
        if self.hasGuide():
            guideLayer = self.guideLayer()
            if guideLayer is not None:
                guideSettingsNode = guideLayer.guideSettings()
                # need a better way for this
                if "manualOrient" in settings:
                    guideLayer.setManualOrient(settings["manualOrient"])

        guideLayerDef = definition.guideLayer
        for k, v in settings.items():
            originalSettings[k] = v
            guideLayerDef.guideSetting(k).value = v
            if guideSettingsNode:
                attr = guideSettingsNode.attribute(k)
                if attr.value() != v:
                    attr.set(v)

        self.saveDefinition(definition)
        return originalSettings

    def _setupGuideSettings(self):
        """Setup guide settings"""
        self.logger.debug("Creating guide settings from definition")
        guideLayer = self.guideLayer()
        compSettings = self.definition.guideLayer.settings  # type: list
        if not compSettings:
            return
        existingSettings = guideLayer.guideSettings()
        outgoingConnections = {}
        if existingSettings is not None:
            existingSettings.attribute("message").disconnectAll()

            for attr in existingSettings.iterExtraAttributes():
                if attr.isSource:
                    outgoingConnections[attr.partialName()] = list(attr.destinations())
            existingSettings.delete()

        name = self.namingConfiguration().resolve(
            "settingsName",
            {
                "componentName": self.name(),
                "side": self.side(),
                "section": constants.GUIDE_LAYER_TYPE,
                "type": "settings",
            },
        )
        settingsNode = guideLayer.createSettingsNode(
            name, attrName=constants.GUIDE_LAYER_TYPE
        )
        modifier = zapi.dgModifier()
        for setting in iter(compSettings):
            if not settingsNode.hasAttribute(setting.name):
                attr = settingsNode.addAttribute(**setting)
            else:
                attr = settingsNode.attribute(setting.name)
                attr.setFromDict(**setting)
            conns = outgoingConnections.get(setting.name, [])
            for dest in conns:
                if not dest.exists():
                    continue
                attr.connect(dest, mod=modifier, apply=False)
        modifier.doIt()

    def setupGuide(self):
        """Main Build method for the guide, do all your main logic here.

        :return: shouldn't return anything
        :rtype: None
        """
        pass

    def postSetupGuide(self):
        """Called directly after the guides have been created

        :rtype: None
        """
        self.logger.debug("Running post setup guide to handle cleanup and publish")
        guideLayer = self.guideLayer()
        guideLayerDef = self.definition.guideLayer
        guideLayerTransform = guideLayer.rootTransform()
        # delete any guides in the scene which no longer need to exist.
        sceneGuides = {i.id() for i in guideLayer.iterGuides()}
        defGuides = {i["id"] for i in self.definition.guideLayer.iterGuides()}
        toDelete = [guideId for guideId in sceneGuides if guideId not in defGuides]
        if toDelete:
            guideLayer.deleteGuides(*toDelete)

        container = self._mergeComponentIntoContainer()
        if container is not None:
            self.logger.debug("Publishing guide settings to container")
            container.lock(False)
            settings = guideLayer.settingNode(constants.GUIDE_LAYER_TYPE)
            if settings is not None:
                container.unPublishAttributes()
                container.removeUnboundAttributes()
                container.publishAttributes(
                    [
                        i
                        for i in settings.iterExtraAttributes()
                        if i.partialName(includeNodeName=False)
                        not in _ATTRIBUTES_TO_SKIP_PUBLISH
                        and not i.isChild
                        and not i.isElement
                    ]
                )

            container.blackBox = self.configuration.blackBox
        # setup annotations
        annotationGrp = guideLayer.sourceNodeByName("hiveGuideAnnotationGrp")
        namingObj = self.namingConfiguration()
        compName, compSide = self.name(), self.side()
        if annotationGrp is None:
            name = namingutils.composeAnnotationGrpName(namingObj, compName, compSide)
            annotationGrp = zapi.createDag(name, "transform")
            annotationGrp.setParent(guideLayerTransform)
            guideLayer.connectTo("hiveGuideAnnotationGrp", annotationGrp)

        self.logger.debug("Tagging and annotating guide structure")
        guides = {i.id(): i for i in guideLayer.iterGuides()}
        nodesToPublish = []
        for guideId, gui in guides.items():
            # ok now since all the guides have been generated lets generate the annotations and controller tags.
            # Each annotation will be created if the guide has a parent guide.
            guideDef = guideLayerDef.guide(guideId)
            parentGuid = None
            if guideId != "root":
                parentGuid = guides[guideDef.annotationParent]

            if parentGuid is not None:
                annName = namingObj.resolve(
                    "object",
                    {
                        "componentName": compName,
                        "side": compSide,
                        "section": gui.id(),
                        "type": "annotation",
                    },
                )
                guideLayer.createAnnotation(
                    annName, start=gui, end=parentGuid, parent=annotationGrp
                )
            gui.lock(True)
            nodesToPublish.append(gui)
            shapeNode = gui.shapeNode()
            if shapeNode:
                nodesToPublish.append(shapeNode)
        container.publishNodes(nodesToPublish)
        # todo: bring back controller tags when autodesk fixes
        # create the controller tags and add them to the meta data and container
        # tags = list(self.createGuideControllerTags(guides, None))
        #
        # guideLayer.addExtraNodes(tags)
        # try:
        #     container.addNodes(tags)
        # except AttributeError:
        #     # will happen when we have no container which is ok depending on configuration
        #     pass
        # ok now add the marking menu layout, the layout.id is stored on the definition file if the user specified
        # otherwise use the global
        layoutId = self.definition.mm_guide_Layout or "hiveDefaultGuideMenu"

        # get and store the layout on the guideLayer meta node
        self.logger.debug("Creating guide trigger attributes: {}".format(layoutId))
        componentutils.createTriggers(guideLayer, layoutId)
        self.deserializeComponentConnections(layerType=constants.GUIDE_LAYER_TYPE)

    @profiling.fnTimer
    def alignGuides(self):
        """This Method handles guide alignment for the component. This method will be run automatically
        just before the deformation layer is built. However, it can also be run on demand via rigging tools.

        .. note::
            This method is intended to be overridden however the default behaviour will
            auto align all guides to the first child found.

        When overriding this method it's important to utilise or api to help reduce the amount of code
        needed and to produce consistency across components. This includes using user defined per guide
        autoAlign settings and our batching function which updates all guide matrices in one go.

        Every guide in hive defines 3 primary attributes relating to alignment

            #. autoAlign - Determines whether the guide requires auto Alignment.
            #. autoAlignAimVector - Determines the primary Axis which to align on, the target is defined by the dev.
            #. autoAlignUpVector - Determines The local UpVector for the guide. World Up is defined either by the dev \
            or by a separate guide.

        To determine whether a guide has been set by the user to use autoAlign the below code can be used.

        .. code-block:: python

            if not guide.autoAlign.value():
                continue

        To calculate to align rotations and create a final output matrix which is always done in worldSpace.

        .. code-block:: python

            # guide.autoAlignAimVector and autoAlignUpVector are attributes which to user
            # can change
            outRotation = mayamath.lookAt(sourcePosition=source,
                                          aimPosition=target,
                                          aimVector=zapi.Vector(guide.autoAlignAimVector.value()),
                                          upVector=zapi.Vector(guide.autoAlignUpVector.value()),
                                          worldUpVector=worldUpVector
                                          )
            transform = guide.transformationMatrix()
            transform.setRotation(outRotation)

        To set all guide transforms in batch, which is far more efficient than one at a time.

        .. code-block:: python

             api.setGuidesWorldMatrix(guidesToAlign, matricesToSet, skipLockedTransforms=False)

        :return: Whether auto aligning succeeded.
        :rtype: bool
        """
        if not self.hasGuide():
            return False
        guideLayer = self.guideLayer()
        guideLayer.alignGuides()
        return True

    def setupRigSettings(self):
        """Sets up rig settings for the animation Rig."""
        rigLayer = self.rigLayer()
        settings = self.definition.rigLayer.get("settings", {})
        spaceSwitches = self.definition.spaceSwitching
        controlPanelDef = settings.get("controlPanel", [])
        spaceswitch.mergeAttributesWithSpaceSwitches(
            controlPanelDef, spaceSwitches, excludeActive=True
        )
        if controlPanelDef:
            settings["controlPanel"] = controlPanelDef
        namingConfig = self.namingConfiguration()
        compName, side = self.name(), self.side()
        for name, attrData in iter(settings.items()):
            node = rigLayer.settingNode(name)
            if node is None:
                attrName = name
                name = namingConfig.resolve(
                    "settingsName",
                    {
                        "componentName": compName,
                        "side": side,
                        "section": name,
                        "type": "settings",
                    },
                )
                node = rigLayer.createSettingsNode(name, attrName=attrName)
            for i in iter(attrData):
                node.addAttribute(**i)

    def _setupGuideOffsets(self, parentJoint):
        """Setups up the livelink nodes and attribute metadata and activates it.

        :param parentJoint:
        :type parentJoint: :class:`zapi.DagNode`
        """
        definition = self.definition
        inputLayer = self.inputLayer()

        inputOffsetNode = inputLayer.settingNode(constants.INPUT_OFFSET_ATTR_NAME)
        if inputOffsetNode is None:
            inputOffsetName = self.namingConfiguration().resolve(
                "settingsName",
                {
                    "componentName": self.name(),
                    "side": self.side(),
                    "section": constants.INPUT_GUIDE_OFFSET_NODE_NAME,
                    "type": "settings",
                },
            )
            inputOffsetNode = inputLayer.createSettingsNode(
                inputOffsetName, constants.INPUT_OFFSET_ATTR_NAME
            )

        transformAttr = inputOffsetNode.attribute("transforms")
        if transformAttr is None:
            childrenAttrs = [
                {"name": "transformId", "Type": zapi.attrtypes.kMFnDataString},
                {"name": "localMatrix", "Type": zapi.attrtypes.kMFnDataMatrix},
                {"name": "worldMatrix", "Type": zapi.attrtypes.kMFnDataMatrix},
                {"name": "parentMatrix", "Type": zapi.attrtypes.kMFnDataMatrix},
            ]
            transformAttr = inputOffsetNode.addCompoundAttribute(
                "transforms", childrenAttrs, isArray=True
            )
        existingIds = {i.child(0).asString(): i for i in transformAttr}
        arraySize = len(transformAttr)
        index = arraySize + 2
        for guide in definition.guideLayer.iterGuides():
            guideId = guide.id
            if guideId not in existingIds:
                transformAttr[index].child(0).set(guideId)
                index += 1
        guideLayer = self.guideLayer()
        if guideLayer is not None:
            guideLayer.setLiveLink(inputOffsetNode, state=True)

    def setupInputs(self):
        """Sets up the input layer for the component.

        :raises: :class:`errors.InvalidInputNodeMetaData`
        """
        compName, side = self.name(), self.side()
        self.logger.debug("Running Input layer setup for component")
        namingConfig = self.namingConfiguration()
        hrcName, metaName = namingutils.composeNamesForLayer(
            namingConfig, compName, side, constants.INPUT_LAYER_TYPE
        )
        inputLayer = self._meta.createLayer(
            constants.INPUT_LAYER_TYPE,
            hrcName,
            metaName,
            parent=self._meta.rootTransform(),
        )  # type: layers.HiveInputLayer
        rootTransform = inputLayer.rootTransform()
        if rootTransform is None:
            rootTransform = inputLayer.createTransform(
                name=hrcName, parent=self._meta.rootTransform()
            )

        self._buildObjectCache[layers.HiveInputLayer.id] = inputLayer

        def _buildInput(inputDef):
            parent = (
                rootTransform
                if inputDef.parent is None
                else inputLayer.inputNode(inputDef.parent)
            )
            try:
                inNode = inputLayer.inputNode(inputDef.id)
            except errors.InvalidInputNodeMetaData:
                inNode = None
            if inNode is None:
                inputDef.name = namingConfig.resolve(
                    "inputName",
                    {
                        "componentName": compName,
                        "side": side,
                        "type": "input",
                        "id": inputDef.id,
                    },
                )
                inNode = inputLayer.createInput(**inputDef)

            inNode.setParent(parent, maintainOffset=True)
            return inNode

        definition = self.definition
        inputLayerDef = definition.inputLayer
        currentInputs = {inputNode.id(): inputNode for inputNode in inputLayer.inputs()}
        newInputs = {}
        for n in inputLayerDef.iterInputs():
            inputNode = _buildInput(n)
            newInputs[n.id] = inputNode
        # now remove any inputs which don't exist anymore
        for inputId, inputNode in currentInputs.items():
            if inputId in newInputs:
                continue
            parentNode = inputNode.parent()
            for child in inputNode.children((zapi.kTransform,)):
                child.setParent(parentNode)
            inputLayer.deleteInput(inputId)
        # input settings
        inputSettings = inputLayerDef.settings
        for setting in iter(inputSettings):
            inputLayer.addAttribute(**setting)

    def setupOutputs(self, parentNode):
        """Sets up the output layer for the component.

        :param parentNode: Parent joint for the output layer.
        :type parentNode: :class:`zapi.DagNode`
        :raises: :class:`errors.InvalidOutputNodeMetaData`
        """
        compName, side = self.name(), self.side()
        self.logger.debug("Running Output layer setup for component")
        namingConfiguration = self.namingConfiguration()
        hrcName, metaName = namingutils.composeNamesForLayer(
            namingConfiguration, compName, side, constants.OUTPUT_LAYER_TYPE
        )
        outputLayer = self._meta.createLayer(
            constants.OUTPUT_LAYER_TYPE,
            hrcName,
            metaName,
            parent=self._meta.rootTransform(),
        )  # type: layers.HiveOutputLayer
        rootTransform = outputLayer.rootTransform()
        if rootTransform is None:
            rootTransform = outputLayer.createTransform(
                name=hrcName, parent=self._meta.rootTransform()
            )

        self._buildObjectCache[layers.HiveOutputLayer.id] = outputLayer
        rootTransform = outputLayer.rootTransform()

        def _buildOutput(outputDef):
            parent = (
                rootTransform
                if outputDef.parent is None
                else outputLayer.outputNode(outputDef.parent)
            )
            try:
                outNode = outputLayer.outputNode(outputDef.id)
            except errors.InvalidOutputNodeMetaData:
                outNode = rootTransform

            if outNode is None:
                outputDef.name = namingConfiguration.resolve(
                    "outputName",
                    {
                        "componentName": compName,
                        "side": side,
                        "type": "output",
                        "id": outputDef.id,
                    },
                )
                outNode = outputLayer.createOutput(**outputDef)
            outNode.setParent(parent, maintainOffset=True)
            return outNode

        definition = self.definition
        outputLayerDef = definition.outputLayer
        currentOutputs = {out.id(): out for out in outputLayer.outputs()}
        newOutputs = {}
        self.logger.debug("Building OutputNodes")
        for n in outputLayerDef.iterOutputs():
            out = _buildOutput(n)
            newOutputs[n.id] = out
        # now remove any outputs which don't exist anymore
        for outId, out in currentOutputs.items():
            if outId in newOutputs:
                continue
            parentNode = out.parent()
            for child in out.children((zapi.kTransform,)):
                child.setParent(parentNode)
            outputLayer.deleteOutput(outId)
        # outputSettings
        outputSettings = outputLayerDef.settings
        for setting in iter(outputSettings):
            outputLayer.addAttribute(**setting)

    def preSetupDeformLayer(self):
        """This function sets up the deform layer in the definition.

        For each guide in the guide layer definition, it checks if a corresponding deform joint
        exists in the deform layer definition. If it does, it sets the translate, rotateOrder,
        and rotate attributes of the deform joint to the values of the corresponding guide.
        If no corresponding deform joint exists, it continues to the next guide.
        """
        definition = self.definition
        deformLayerDef = definition.deformLayer
        guideLayerDef = definition.guideLayer

        guidesDefinitions = {k.id: k for k in guideLayerDef.iterGuides()}
        jointDefinitions = {k.id: k for k in deformLayerDef.iterDeformJoints()}
        for guideId, guide in guidesDefinitions.items():
            jnt = jointDefinitions.get(guideId)
            if jnt is None:
                continue
            jnt.translate = guide.get("translate", (0, 0, 0))
            jnt.rotateOrder = guide.get("rotateOrder", 0)
            jnt.rotate = guide.get("rotate", (0, 0, 0, 1))

    def setupDeformLayer(self, parentNode=None):
        """Sets up the Deform layer for the component.

        :param parentNode: The parent joint or the node which the joints will be parented too. Could \
        be the deformLayer Root.
        :type parentNode: :class:`api.Joint` or :class:`zapi.DagNode`
        """
        defLayer = self.deformLayer()
        definition = self.definition
        deformLayerDef = definition.deformLayer
        guideLayerDef = definition.guideLayer
        namingCfg = self.namingConfiguration()
        guidesDefinitions = {k.id: k for k in guideLayerDef.iterGuides()}
        existingJoints = {
            k.id(): k for k in defLayer.iterJoints()
        }  # type: dict[str, hnodes.Joint]
        deformLayerTransform = defLayer.rootTransform()
        newJointIds = {}
        primaryRootJnt = parentNode or deformLayerTransform
        idMapping = {
            v: k for k, v in self.idMapping()[constants.DEFORM_LAYER_TYPE].items()
        }  # reverse so it's jnt id:guideId
        # find the joints for don't exist anymore
        for jnt in deformLayerDef.iterDeformJoints():
            existingJoint = existingJoints.get(jnt.id)

            guide = guidesDefinitions.get(idMapping.get(jnt.id, ""))
            defParent = jnt.get("parent") or None
            if defParent is None:
                jntParent = primaryRootJnt
            else:
                jntParent = existingJoints[defParent]
            jntName = namingCfg.resolve(
                "skinJointName",
                {
                    "componentName": self.name(),
                    "side": self.side(),
                    "id": jnt.id,
                    "type": "joint",
                },
            )
            # when we have an existing joint we need to update its transforms
            if existingJoint:
                # skip the existing joint, so it gets deleted when there's no guide.
                if not guide:
                    continue
                newJointIds[jnt.id] = existingJoint
                existingJoint.rotateOrder.set(jnt.rotateOrder)
                existingJoint.segmentScaleCompensate.set(0)
                existingJoint.setParent(jntParent)
                existingJoint.rename(jntName)
                continue
            newNode = defLayer.createJoint(
                name=jntName,
                id=jnt.id,
                rotateOrder=jnt.rotateOrder,
                translate=jnt.translate,
                rotate=jnt.rotate,
                parent=jntParent,
                attributes=jnt.attributes
            )
            newNode.segmentScaleCompensate.set(0)
            existingJoints[jnt.id] = newNode
            newJointIds[jnt.id] = newNode
        # purge any joints which were removed from the definition. this can happen in dynamically generated
        # components
        for jntId, existingJoint in existingJoints.items():
            if jntId in newJointIds:
                continue
            parentNode = existingJoint.parent()
            for child in existingJoint.children((zapi.kTransform, zapi.kJoint)):
                child.setParent(parentNode)
            defLayer.deleteJoint(jntId)

        # binding components deform joints to the selection set. removing anything we don't need any more
        selectionSet = defLayer.selectionSet()
        if selectionSet is None:
            name = namingCfg.resolve(
                "selectionSet",
                {
                    "componentName": self.name(),
                    "side": self.side(),
                    "selectionSet": "componentDeform",
                    "type": "objectSet",
                },
            )
            selectionSet = defLayer.createSelectionSet(
                name, parent=self.rig.meta.selectionSets()["deform"]
            )

        bindJoints = self.setupSelectionSet(defLayer, newJointIds)
        currentSelectionSetMembers = selectionSet.members(True)
        toRemove = [i for i in currentSelectionSetMembers if i not in bindJoints]
        if toRemove:
            selectionSet.removeMembers(toRemove)
        if bindJoints:
            selectionSet.addMembers(bindJoints)
        defLayer.setLiveLink(
            self.inputLayer().settingNode(constants.INPUT_OFFSET_ATTR_NAME),
            idMapping=self.idMapping()[constants.DEFORM_LAYER_TYPE],
            state=True,
        )

    def setupSelectionSet(self, deformLayer, deformJoints):
        """Responsible for adding joints to the deform selection set.

        :param deformLayer: The deformLayer instance
        :type deformLayer: :class:`layers.HiveDeformLayer`
        :param deformJoints: The joint id to joint map.
        :type deformJoints: dict[str, :class:`hnodes.Joint`]
        """
        if deformJoints:
            return list(deformJoints.values())
        return []

    def postSetupDeform(self, parentJoint):
        # ok now add the marking menu layout, the layout.id is stored on the definition file if the user specified
        # otherwise use the global
        layoutId = self.definition.mm_deform_Layout or "hiveDefaultDeformMenu"
        deformLayer = self.deformLayer()
        guideOffset = self.inputLayer().settingNode(constants.INPUT_OFFSET_ATTR_NAME)

        deformLayer.setLiveLink(guideOffset, state=False)
        guideLayer = self.guideLayer()
        if guideLayer is not None:
            # todo: create a guideLayer offsetNode and connect that to the inputLayer offset
            guideLayer.setLiveLink(guideOffset, state=False)
        if self.configuration.buildDeformationMarkingMenu:
            # get and store the layout on the guideLayer meta node
            componentutils.createTriggers(deformLayer, layoutId)
        container = self.container()
        if container is not None:
            container.publishNodes(deformLayer.joints())
        deformLayer.rootTransform().show()

    def preSetupRig(self, parentNode):
        """Same logic as guides, inputs outputs and animation attributes are auto generated from the definition."""
        namingConfiguration = self.namingConfiguration()
        compName, side = self.name(), self.side()
        hrcName, metaName = namingutils.composeNamesForLayer(
            self.namingConfiguration(), compName, side, constants.RIG_LAYER_TYPE
        )
        rigLayer = self._meta.createLayer(
            constants.RIG_LAYER_TYPE,
            hrcName,
            metaName,
            parent=self._meta.rootTransform(),
        )
        self._buildObjectCache[layers.HiveRigLayer.id] = rigLayer
        attrName = constants.CONTROL_PANEL_TYPE
        name = namingConfiguration.resolve(
            "settingsName",
            {
                "componentName": compName,
                "side": side,
                "section": constants.CONTROL_PANEL_TYPE,
                "type": "settings",
            },
        )
        rigLayer.createSettingsNode(name, attrName)
        self.setupRigSettings()

    def setupRig(self, parentNode):
        """Main method to build the rig. You should never access the guides directly as that would limit the
        flexibility for the building processing over the farm or without a physical guide in the scene.
        Always access rig nodes through the component class(self) never access the hive node class directly as
        internal method does extra setup for internal metadata etc.

        :rtype:None
        """

        raise NotImplementedError

    def postSetupRig(self, parentNode):
        """Post rig build, me thod to take all control panel attributes and publish them to the
        container interface, control nodes are published and all nodes connected to the meta node of this
        component is added to the container but not published
        """
        controlPanel = self.controlPanel()
        rigLayer = self.rigLayer()

        # ok now loop the controls and setup controllerTags
        controllerTagPlug = controlPanel.addAttribute(
            **dict(
                name="controlMode",
                Type=attrtypes.kMFnkEnumAttribute,
                keyable=False,
                channelBox=True,
                enums=[
                    "Not Overridden",
                    "Inherit Parent Controller",
                    "Show on Mouse proximity",
                ],
            )
        )
        controls = list(rigLayer.iterControls())
        selectionSet = rigLayer.selectionSet()
        if selectionSet is None:
            selectionSet = rigLayer.createSelectionSet(
                self.namingConfiguration().resolve(
                    "selectionSet",
                    {
                        "componentName": self.name(),
                        "side": self.side(),
                        "selectionSet": "componentCtrls",
                        "type": "objectSet",
                    },
                ),
                parent=self.rig.meta.selectionSets()["ctrls"],
            )

        controllerTags = list(self.createRigControllerTags(controls, controllerTagPlug))

        selectionSet.addMembers(controls + [controlPanel])
        rigLayer.addExtraNodes(controllerTags)

        container = self._mergeComponentIntoContainer()

        # publish unique control settings
        if container is not None:
            container.publishNodes(list(rigLayer.iterControls()) + controllerTags)
            container.publishAttributes(
                [
                    i
                    for i in controlPanel.iterExtraAttributes()
                    if i.partialName(includeNodeName=False)
                    not in _ATTRIBUTES_TO_SKIP_PUBLISH
                ]
            )

        # hide all joints under the rigLayer
        for n in rigLayer.iterJoints():
            n.hide()
        # ok now add the marking menu layout, the layout.id is stored on the definition file if the user specified
        # otherwise use the global
        layoutId = self.definition.mm_rig_Layout or "hiveDefaultRigMenu"

        # get and store the layout on the guideLayer meta node
        componentutils.createTriggers(rigLayer, layoutId)

    def setupSpaceSwitches(self):
        """Method to setup space switches from the definition data, this method is called after the rig is built"""
        rig = self.rig
        rigLayer = self.rigLayer()
        existingSpaceConstraints = {
            i.controllerAttrName(): i for i in rigLayer.spaceSwitches()
        }
        for spaceSwitchDef in self.definition.spaceSwitching:
            # ignore any space switch that was deactivated, typically done in code
            if not spaceSwitchDef.active:
                continue
            # ignore any space switch that has no drivers or driven, this can happen when dependent components
            # have been removed and the space was updated but not deleted
            elif not spaceSwitchDef.drivers or not spaceSwitchDef.driven:
                continue
            # decompose spaceSwitch definition to the current scene rig
            decomposedSwitch = spaceswitch.spaceSwitchDefToScene(
                rig, self, spaceSwitchDef
            )
            # ignore spaces where the specified driven object is not found, can happen when the user changes
            # a requirement i.e settings and the node is removed by hive.
            drivenNode = decomposedSwitch.driven
            if drivenNode is None:
                self.logger.debug(
                    "Driven Node is None for space Switching '{}', skipping".format(
                        spaceSwitchDef.label
                    )
                )
                continue
            targets = []
            for driver in decomposedSwitch.drivers:
                targets.append((driver.label, driver.driver))
            constraintType = decomposedSwitch["type"]
            drivenId = drivenNode.id()
            # each space ends up with a unique constraint, so we need to check if the constraint already exists
            # and if so use it otherwise create a new SRT directly above the driven node e.g. the controls direct parent
            existingConstraint = existingSpaceConstraints.get(decomposedSwitch["label"])
            if existingConstraint is None:
                spaceSrt = rigLayer.createSrtBuffer(
                    drivenId, name="_".join([drivenNode.name(), "space"])
                )
            else:
                spaceSrt = existingConstraint.driven()
            # rig layer handles the meta data for the space switch and calls the correct method to correct the space.
            kwargs = {
                "driven": spaceSrt,
                "drivers": {
                    "attributeName": decomposedSwitch["label"],
                    "targets": targets,
                    "default": spaceSwitchDef.defaultDriver,
                },
                "constraintType": constraintType,
                "maintainOffset": decomposedSwitch.get("maintainOffset", True),
            }
            rigLayer.createSpaceSwitch(**kwargs)

    def createRigControllerTags(self, controls, visibilityPlug):
        """Creates and yields controller tags for the Anim rig layer.

        :param controls: The full list of controls from the component in order of creation.
        :type controls: iterable[:class:`hnodes.ControlNode`]
        :param visibilityPlug: The visibility plug from the control panel.
        :type visibilityPlug: :class:`zapi.Plug` or None
        :return: Iterable of  kControllerNode as a zapi DGNode
        :rtype: iterable[:class:`zapi.DGNode`]
        """
        parent = None
        for control in controls:
            yield control.addControllerTag(
                name="_".join([control.name(), "tag"]),
                parent=parent,
                visibilityPlug=visibilityPlug,
            )
            parent = control

    def createGuideControllerTags(self, guides, visibilityPlug):
        """Creates and yields controller tags for the Guide layer.

        :param guides: The full list of Guides from the component in order of creation.
        :type guides: iterable[:class:`hnodes.Guide`]
        :param visibilityPlug: The visibility plug from the Guide settings nodes if present.
        :type visibilityPlug: :class:`zapi.Plug` or None
        :return: Iterable of  kControllerNode as a zapi DGNode
        :rtype: iterable[:class:`zapi.DGNode`]
        """
        for guide in guides:
            parentGuid, idPlug = guide.guideParent()
            c = guide.controllerTag()
            if c is None:
                c = guide.addControllerTag(
                    name="_".join([guide.name(), "tag"]),
                    parent=parentGuid,
                    visibilityPlug=visibilityPlug,
                )
            yield c

    def prePolish(self):
        """First stage of the publishing is to remove Guide structure if it exists."""
        if not self.hasRig():
            return
        if self.hasGuide():
            self.deleteGuide()
        for layer in self._meta.layers():
            if layer.mClassType() == constants.RIG_LAYER_TYPE:
                # loop everything under the rigLayer
                for n in layer.iterJoints():
                    n.hide()
            else:
                layer.hide()

    def polish(self):
        """Cleanup operation of a component, used to publish attributes from the controlPanel
        to the container interface and to publish all controls to the container

        """
        try:
            self.prePolish()
            self.postPolish()
            self._setHasPolished(True)
            return True

        except Exception:
            self.logger.error(
                "Unknown Error occurred during polish of '{}'".format(
                    self.serializedTokenKey()
                ),
                exc_info=True,
            )
            return False

    def postPolish(self):
        """Post publish method is the final operation done to complete a component build.
        This is useful for cleaning up the rig, locking off attributes/nodes etc.
        """
        cont = self.container()
        if cont:
            if not self.configuration.useContainers:
                cont.delete()
            else:
                cont.blackBox = self.configuration.blackBox
                cont.lock(True)
        controlPanel = self.controlPanel()
        rigLayer = self.rigLayer()

        # todo: support user based attribute groups which link attributes to certain controls.
        if self.configuration.useProxyAttributes:
            # create the attributes on every control on the component as a proxy attribute
            for control in rigLayer.iterControls():
                for attr in controlPanel.iterExtraAttributes():
                    name = attr.partialName(includeNodeName=False)
                    if name not in _ATTRIBUTES_TO_SKIP_PUBLISH:
                        control.addProxyAttribute(attr, name)

        if self.configuration.hideControlShapesInOutliner:
            for control in rigLayer.iterControls():
                for shape in control.iterShapes():
                    shape.attribute("hiddenInOutliner").set(True)

        isHistoricallyInteresting = self.configuration.isHistoricallyInteresting
        self.setIsHistoricallyInteresting(isHistoricallyInteresting)

        # ok now add the marking_menu layout, the layout.id is stored on the definition file if the user specified
        # otherwise use the global
        layoutId = self.definition.mm_anim_Layout or "hiveDefaultAnimMenu"
        # get and store the layout on the rigLayer meta node
        componentutils.createTriggers(rigLayer, layoutId)

    def setIsHistoricallyInteresting(self, state):
        """Sets the isHistoricallyInteresting state on the component.

        :param state: Whether the component is historically interesting.
        :type state: bool
        """
        rigLayer = self.rigLayer()
        if rigLayer is None:
            return
        isHistoricallyInteresting = state
        # todo: support user based attribute groups which link attributes to certain controls.
        # create the attributes on every control on the component as a proxy attribute
        for control in rigLayer.iterControls():
            for shape in control.iterShapes():
                shape.isHistoricallyInteresting = isHistoricallyInteresting
        for extraNode in rigLayer.extraNodes():
            extraNode.isHistoricallyInteresting = isHistoricallyInteresting
        rigLayer.isHistoricallyInteresting = isHistoricallyInteresting
        selectionSet = rigLayer.selectionSet()
        if selectionSet is not None:
            selectionSet.isHistoricallyInteresting = isHistoricallyInteresting

    @profiling.fnTimer
    def deleteGuide(self):
        """This function deletes the guide system.

        :return: True if the guide system is successfully deleted
        :rtype: bool
        :raises ValueError: if the container is not valid
        """

        self.logger.debug("Deleting Guide system: {}".format(self))
        container = self.container()
        guideLayer = self.guideLayer()
        if not guideLayer:
            self._setHasGuide(False)
            return True
        toDelete = []
        self.logger.debug("GuideLayer exists start deletion process")
        childComponents = self.children()
        if childComponents:
            self.logger.debug("Child components exist, removing annotations")
            guides = guideLayer.iterGuides()
            for child in childComponents:
                layer = child.guideLayer()
                if layer is None:
                    continue
                toDelete.extend(
                    [
                        ann
                        for ann in child.guideLayer().annotations()
                        if ann.endNode() in guides
                    ]
                )
        if container is not None:
            container.lock(False)
            guideSettings = guideLayer.settingNode(constants.GUIDE_LAYER_TYPE)
            if guideSettings:
                self.logger.debug("Purging published container settings")
                for i in container.publishedAttributes():
                    try:
                        plugName = i.partialName(includeNodeName=False)
                    except RuntimeError:
                        # maya errors are shit house, RuntimeError at this point in the code
                        # is likely due to an object being deleted
                        self.logger.warning("Object does not exist: {}".format(i))
                        continue
                    if guideSettings.hasAttribute(plugName):
                        container.unPublishAttribute(plugName)
        modifier = zapi.dagModifier()
        if guideLayer is not None:
            for graph in guideLayer.namedGraphs(self.configuration.graphRegistry()):
                graph.delete(modifier)
        [i.delete(mod=modifier, apply=False) for i in toDelete if i.exists()]
        guideLayer.delete(mod=modifier, apply=True)
        self._setHasGuide(False)

        return True

    @profiling.fnTimer
    def deleteDeform(self):
        """This function deletes the deform system.

        :return: Whether the deform system is successfully deleted.
        :rtype: bool
        """
        layersTypes = self._meta.layersById(
            (
                constants.INPUT_LAYER_TYPE,
                constants.OUTPUT_LAYER_TYPE,
                constants.DEFORM_LAYER_TYPE,
            )
        )
        for layer in layersTypes.values():
            if layer is not None:
                layer.delete()
        self._setHasSkeleton(False)

        return True

    @profiling.fnTimer
    def deleteRig(self):
        """Deletes the current rig for the component if it exists, this includes the rigLayer, inputs, outputs and
        deform layer.

        :return: True if successful
        :rtype: bool
        """

        layersTypes = self._meta.layersById(
            (
                constants.RIG_LAYER_TYPE,
                constants.DEFORM_LAYER_TYPE,
                constants.INPUT_LAYER_TYPE,
                constants.OUTPUT_LAYER_TYPE,
                constants.XGROUP_LAYER_TYPE,
            )
        )
        rigLayer = layersTypes[constants.RIG_LAYER_TYPE]  # type: layers.HiveRigLayer
        xGroupLayer = layersTypes[
            constants.XGROUP_LAYER_TYPE
        ]  # type: layers.HiveXGroupLayer
        cp = self.controlPanel()
        container = self.container()
        deformLayer = layersTypes[
            constants.DEFORM_LAYER_TYPE
        ]  # type: layers.HiveDeformLayer

        # safely disconnect the deformation
        if deformLayer is not None:
            disconnectJointTransforms(deformLayer)
            resetJointTransforms(
                deformLayer, self.definition.guideLayer, self.idMapping()
            )

        if container is not None:
            container.lock(False)
            if cp is not None:
                # ok we have a control panel so first thing to do is unpublish all
                # attributes that have a connection to the panel
                for i in container.publishedAttributes():
                    plugName = i.partialName(includeNodeName=False)
                    if cp.hasAttribute(plugName):
                        container.unPublishAttribute(plugName)
            if rigLayer is not None:
                # unpublish the ctrls, note this doesn't delete the nodes
                for ctrl in rigLayer.iterControls():
                    container.unPublishNode(ctrl)
        inputLayer, outputLayer = (
            layersTypes[constants.INPUT_LAYER_TYPE],  # type: layers.HiveInputLayer
            layersTypes[constants.OUTPUT_LAYER_TYPE],  # type: layers.HiveOutputLayer
        )
        if inputLayer is not None:
            inputLayer.clearInputs()
        if outputLayer is not None:
            outputLayer.clearOutputs()
        modifier = zapi.dagModifier()
        if rigLayer is not None:
            for graph in rigLayer.namedGraphs(self.configuration.graphRegistry()):
                graph.delete(modifier)
        # # trash the layers associated with the rig
        for i in iter([i for i in (rigLayer, cp, xGroupLayer) if i is not None]):
            if i is not None:
                i.delete(mod=modifier, apply=True)
        self._setHasRig(False)

        return True

    @profiling.fnTimer
    def delete(self):
        """Deletes The entire component from the scene if this component has children
        Then those children's meta node will be re-parented to the component Layer of the rig.

        Order of deletion:

            #. rigLayer
            #. deformLayer
            #. inputLayer
            #. outputLayer
            #. guideLayer
            #. assetContainer
            #. metaNode

        :return:
        :rtype:
        """
        r = self._rig
        cont = self.container()
        currentChildren = list(self.children())
        for child in currentChildren:
            child.meta.addMetaParent(r.componentLayer())
        self.logger.debug("Starting component deletion operation")
        self.deleteRig()
        self.deleteDeform()
        self.deleteGuide()

        self.logger.debug("Rewiring child component to component layer")

        if self._meta.exists():
            self._meta.delete()
        if cont is not None:
            self.logger.debug("Deleting container")
            cont.delete()

        self._meta = None
        return True

    def deserializeComponentConnections(self, layerType=constants.GUIDE_LAYER_TYPE):
        return self._remapConnections(layerType)

    def serializeComponentGuideConnections(self):
        """Serializes the connection for this component to the parent.
        There's only ever one parent but we may have multiple constraintTypes bound
        """
        existingConnectionDef = self.definition.connections
        if not self.hasGuide():
            return existingConnectionDef
        guideLayer = self.guideLayer()
        # |- hguides
        #     |- sourceGuides[]
        #                 |- constraintNodes
        rootGuide = guideLayer.guide("root")
        if not rootGuide:
            return existingConnectionDef

        rootSrt = rootGuide.srt(0)
        if not rootSrt:
            return existingConnectionDef
        guideConstraints = []
        for constraint in zapi.iterConstraints(rootSrt):
            content = constraint.serialize()
            controller, controllerAttr = content.get("controller", (None, None))
            if controller:
                content["controller"] = (controller[0].fullPathName(), controller[1])
            targets = []
            for targetLabel, target in content.get("targets", []):
                if hnodes.Guide.isGuide(target):
                    comp = self.rig.componentFromNode(target)
                    fullName = ":".join(
                        [comp.name(), comp.side(), hnodes.Guide(target.object()).id()]
                    )
                    targets.append((targetLabel, fullName))
            content["targets"] = targets
            guideConstraints.append(content)
        if not guideConstraints:
            return existingConnectionDef
        return {"id": "root", "constraints": guideConstraints}

    def _remapConnections(self, layerType=constants.GUIDE_LAYER_TYPE):
        """

        Note: Internal use only.

        .. code-block:: python
            component._remapConnections(layerType=constants.GUIDE_LAYER_TYPE)
            # ({u'...fk01_M:fk02_guide': {"type": "transform", "name": u'...fk01_M:fk02_guide', "connections": []}},
                {u'...fk01_M:fk02_guide': <OpenMaya.MObject object at 0x000001FE30212450>,
            #   u'...fk02_M:fk00_guide': <OpenMaya.MObject object at 0x000001FE30212410>})

        """
        if not self.definition.connections:
            return [], {}

        # now build the IO mapping before transfer this basically takes the inputs/guides and output/guides nodes
        # from the targetComponent and the parent components and creates a binding, so we can inject into the connection
        # graph

        if layerType == constants.GUIDE_LAYER_TYPE:
            guideLayer = self.guideLayer()
            if guideLayer is None:
                msg = "Target Component: {} doesn't have the guide layer built, cancel OP".format(
                    self.name()
                )
                self.logger.error(msg)
                raise ValueError(msg)
            self.logger.debug("Generating connection binding for guides")
            binding, childLayer = componentutils.generateConnectionBindingGuide(self)
            constraints = self._createGuideConstraintsFromData(
                self.definition.connections,
                childLayer,
                binding,
            )
        elif layerType == constants.INPUT_LAYER_TYPE:
            inputLayer = self.inputLayer()
            if inputLayer is None:
                msg = "Target Component: {} doesn't have the rig Layer layer built, cancel OP".format(
                    self.name()
                )
                self.logger.error(msg)
                raise ValueError(msg)
            self.logger.debug("Generating connection binding for IO")
            (
                binding,
                childLayer,
                bindParentLayers,
            ) = componentutils.generateConnectionBindingIO(self)
            if not binding:
                return []
            rootNode = inputLayer.rootInput()
            constraints = self._createIOConstraintsFromData(
                self.definition.connections,
                childLayer,
                rootNode,
                rootNode.id(),
                binding,
                bindParentLayers,
            )
        else:
            raise ValueError(
                "We Currently dont support binding the connections via the layer: {}".format(
                    layerType
                )
            )

        self.logger.debug("Finished remapping connections")
        return constraints

    def _createGuideConstraintsFromData(self, constraintData, layer, nodeBinding):
        self.logger.debug("generating constraints for Layer: {}".format(layer))
        constraints = []
        parentComp = self.parent()
        # with the newer constraint system we only need to get the target node id to handle the setParent
        for constraint in constraintData["constraints"]:
            for targetLabel, targetId in constraint["targets"]:
                parentTarget = nodeBinding.get(targetId)
                if not parentTarget:
                    continue
                self.setParent(parentComp, parentTarget)
                break
            break
        return constraints

    def _createIOConstraintsFromData(
        self, constraintData, layer, rootNode, rootId, nodeBinding, parentLayers
    ):
        """Generates Constraints for the component layer(Inputs)

        :param constraintData:
        :type constraintData:
        :param layer:
        :type layer:
        :param nodeBinding:
        :type nodeBinding:
        :param parentLayers:
        :type parentLayers:
        :return:
        :rtype:
        """
        self.logger.debug("generating constraints for Layer: {}".format(layer))
        constraints = []
        compId = ":".join((self.name(), self.side()))
        parentChildRelationShip = {}

        childNode = ":".join([compId, rootId])
        parentChildRelationShip[childNode] = {"driven": (layer, rootId), "drivers": []}
        driverLayerMap = []
        for const in zapi.iterConstraints(rootNode):
            const.delete()

        for constraint in constraintData["constraints"]:
            targetsRemapped = []
            controller, controllerAttrName = constraint.get("controller", (None, None))
            constraintType = constraint.get("type")
            if constraintType is None:
                continue

            for targetLabel, targetId in constraint["targets"]:
                parentTarget = nodeBinding.get(targetId)
                if not parentTarget:
                    continue
                targetsRemapped.append((targetLabel, parentTarget))
                parentIdParts = targetId.split(":")

                parentLayer = parentLayers.get(":".join(parentIdParts[:-1]))
                driverLayerMap.append((parentLayer, parentTarget.id(), parentTarget))
            if not targetsRemapped:
                continue
            drivers = {
                "targets": targetsRemapped,
                "spaceNode": controller,
                "attributeName": controllerAttrName,
            }
            self.logger.debug(
                "Creating hive constraint: {}, driven: {}, drivers: {}".format(
                    constraintType, rootNode, drivers
                )
            )

            const, _ = zapi.buildConstraint(
                rootNode,
                drivers,
                constraintType="matrix",
                trace=True,
                maintainOffset=True,
                decompose=False,
            )
            constraints.append(const)
            break

        parentChildRelationShip[childNode]["drivers"] = driverLayerMap
        self.logger.debug("linking constraints to metadata and creating annotations")

        for currentComponentNodeId, parentMapping in parentChildRelationShip.items():
            childLayer, childId = parentMapping["driven"]
            childElementInputPlug = childLayer.inputSourcePlugById(childId)

            for index, pMap in enumerate(parentMapping["drivers"]):
                parentLayer, parentNodeId, _ = pMap
                parentElementOutputPlug = parentLayer.outputNodePlugById(parentNodeId)
                parentElementOutputPlug.connect(
                    childElementInputPlug.element(index).child(0)
                )

        return constraints


def disconnectJointTransforms(deformLayer):
    """Disconnects all joint transform attribute which have a incoming connection.

    :param deformLayer: The component deformLayer instance
    :type deformLayer: :class:`layers.HiveDeformLayer`
    """
    disconnectAttrNames = zapi.localTransformAttrs + [
        "translate",
        "rotate",
        "scale",
        "offsetParentMatrix",
        "worldMatrix",
        "matrix",
    ]
    for joint in deformLayer.iterJoints():
        for attr in disconnectAttrNames:
            transformPlug = joint.attribute(attr)
            if transformPlug.isDestination:
                transformPlug.disconnectAll()


def resetJointTransforms(deformLayer, guideDefLayer, idMapping):
    """Resets all joints on the deformLayer to match the guide definition.

    :param deformLayer: The component deformLayer instance
    :type deformLayer: :class:`layers.HiveDeformLayer`
    :param guideDefLayer: The component definition guideLayer instance.
    :type guideDefLayer: :class:`baseDef.GuideLayerDefinition`
    :param idMapping:
    :type idMapping:
    """
    defIdMap = idMapping[constants.DEFORM_LAYER_TYPE]
    jointMapping = {v: k for k, v in defIdMap.items()}
    guideDefinitions = {
        i.id: i for i in guideDefLayer.findGuides(*defIdMap.keys()) if i is not None
    }
    for joint in deformLayer.iterJoints():
        guideId = jointMapping.get(joint.id())
        if not guideId:
            continue
        guideDef = guideDefinitions.get(guideId)  # type: baseDef.GuideDefinition
        # can happen if the component was deleted but this method was called before we've deleted the joints
        if guideDef is None:
            continue
        worldMtx = guideDef.transformationMatrix(scale=False)
        worldMtx.setScale((1, 1, 1), zapi.kWorldSpace)
        joint.resetTransform()
        joint.setWorldMatrix(worldMtx.asMatrix())


class SpaceSwitchUIDriver(object):
    """SpaceSwitch UI Driver control data.

    :param id_: The Internal component rigLayer control id to link too.
    :type id_: str
    :param label: The Display label for the control id
    :type label: str
    :param internal: Whether this control id is internally linked i.e. to the inputLayer.
    :type internal: bool
    """

    def __init__(self, id_, label, internal=False):
        self.id = id_
        self.label = label
        self.internal = internal

    def serialize(self):
        """Serialize the object's attributes into a dictionary.

        :return: a dictionary with the keys `id_`, `label`, and `internal`, and values equal \
        to the id, label, and internal attributes of the object, respectively.
        :rtype: dict
        """
        return {"id_": self.id, "label": self.label, "internal": self.internal}


class SpaceSwitchUIDriven(object):
    """SpaceSwitch UI Driven control data.

    :param id_: The Internal component rigLayer control id to link too.
    :type id_: str
    :param label: The Display label for the control id
    :type label: str
    """

    def __init__(self, id_, label):
        self.id = id_
        self.label = label

    def serialize(self):
        """Serialize the object's attributes into a dictionary.

        :return: a dictionary with the keys `id_` and `label`, and values equal to the id \
        and label attributes of the object, respectively.
        :rtype: dict
        """
        return {"id_": self.id, "label": self.label}
