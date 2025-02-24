import os

from zoo.core.util import env
from zoo.core.plugin import pluginmanager
from zoo.libs.hive import constants
from zoo.libs import shapelib
from zoo.libs.maya.utils import general as mGeneral
from zoo.libs.hive.base import registry
from zoo.libs.hive.base import exporterplugin
from zoo.libs.hive.base import buildscript
from zoo.libs.hive.base import namingpresets
from zoo.preferences.interfaces import hiveinterfaces


class Configuration(object):
    buildScriptVar = "HIVE_BUILD_SCRIPTS_PATH"
    namingVar = "HIVE_NAMING_PATH"
    exportPluginVar = "HIVE_EXPORT_PLUGIN_PATH"
    _componentRegistry = None  # type: registry.ComponentRegistry or None
    _templateRegistry = None  # type: registry.TemplateRegistry or None
    _graphRegistry = None  # type: registry.GraphRegistry or None
    _buildScriptRegistry = None  # type: pluginmanager.PluginManager or None
    _exporterRegistry = None  # type: pluginmanager.PluginManager or None
    _namingPresetRegistry = None  # type: namingpresets.PresetManager or None

    def __init__(self):
        self.configCache = {}
        # The current hive naming convention preset.
        self.currentNamingPreset = None  # type: namingpresets.Preset or None
        # Maya supports proxy attributes, in which case if the below is true we
        # which case each component we create anim settings on every control as a proxy.
        self.useProxyAttributes = True  # type: bool
        # if this is turned off we don't generate AssetContainers for components
        self.useContainers = False  # type: bool
        # Component AssetContainer.blackBox setting
        self.blackBox = True  # type: bool
        # a list of absolute directory or python file paths which be run during build time
        # only applicable using rig.build*
        self.buildScripts = [] # type: list[buildscript.BaseBuildScript]
        # whether selection child highlighting should be on/off when building the rig controls
        self.selectionChildHighlighting = False  # type: bool
        # Whether auto alignment should be run when building the deform layer.
        self.autoAlignGuides = True  # type: bool
        # if set to True then when a component fails to build it will automatically deleted.
        self.deleteOnFail = False  # type: bool
        # On polish per component all extra nodes will has it's isHistoricallyInteresting set to this value.
        self.isHistoricallyInteresting = False  # type: bool
        # if True then on polish all control shapes will be hidden in the outliner
        self.hideControlShapesInOutliner = True  # type: bool
        self.guideScale = 1.0
        self.controlScale = 1.0
        self.guideControlVisibility = False
        self.guidePivotVisibility = True
        self.preferencesInterface = hiveinterfaces.hiveInterface()
        self.exportPluginOverrides = self.preferencesInterface.exporterPluginOverrides()
        self.buildDeformationMarkingMenu = False
        self._discoverPlugins()
        self._discoverEnvironment()

    def containerType(self):
        """Default container type, can be asset, set or None.

        :return: The container Type
        :rtype: str
        """
        return self.configCache.get("defaultContainerType", "asset")

    def _discoverPlugins(self, force=False):
        initializeComponentRegistry(reload=force)
        initializeTemplateRegistry(reload=force)
        initializeGraphRegistry(reload=force)
        initializeBuildScriptRegistry(self.preferencesInterface, reload=force)
        initializeExporterRegistry(self.preferencesInterface, reload=force)
        initializeNamingPresetManager(self.preferencesInterface, reload=force)

    def _discoverEnvironment(self):
        # load the hive preferences and setup the configuration from the settings.

        self.configCache = self.preferencesInterface.settings()["settings"]
        for p in self.configCache.get("required_maya_plugins", []):
            mGeneral.loadPlugin(p)
        self.useProxyAttributes = self.configCache.get("useProxyAttributes", self.useProxyAttributes)
        self.useContainers = self.configCache.get("useContainers", self.useContainers)
        self.blackBox = self.configCache.get("blackBox", self.blackBox)
        self.selectionChildHighlighting = self.configCache.get("selectionChildHighlighting",
                                                               self.selectionChildHighlighting)
        self.guideControlVisibility = self.configCache.get("guideControlVisibility",
                                                           self.guideControlVisibility)
        self.guidePivotVisibility = self.configCache.get("guidePivotVisibility",
                                                         self.guidePivotVisibility)
        self.hideControlShapesInOutliner = self.configCache.get("hideControlShapesInOutliner",
                                                                self.hideControlShapesInOutliner)
        self.isHistoricallyInteresting = self.configCache.get("isHistoricallyInteresting",
                                                              self.isHistoricallyInteresting)
        self.setNamingPresetByName(self.configCache.get("defaultNamingPreset", constants.DEFAULT_BUILTIN_PRESET_NAME))
        # self.naming = naming.HiveNamer("rig", namePath)
        self.setBuildScripts(self.configCache.get("buildScripts", []))

    def serialize(self, rig):
        # get the hive preferences which are the defaults
        cache = self.configCache
        overrides = {}
        buildScriptCfg = self.buildScriptConfig(rig)  # todo: adding/update/deleting buildscript should update the cache
        # now lets compare states
        for setting in ("useProxyAttributes",
                        "useContainers",
                        "blackBox",
                        "required_maya_plugins",
                        "selectionChildHighlighting",
                        "autoAlignGuides",
                        "guidePivotVisibility",
                        "guideControlVisibility",
                        "hideControlShapesInOutliner",
                        "isHistoricallyInteresting"):
            configState = cache.get(setting)
            if hasattr(self, setting):
                rigState = getattr(self, setting)
                if rigState != configState:
                    overrides[setting] = rigState

        for buildScript in self.buildScripts:
            properties = buildScriptCfg.get(buildScript.id, {})
            overrides.setdefault("buildScripts", []).append([buildScript.id, properties])
        if self.currentNamingPreset.name != constants.DEFAULT_BUILTIN_PRESET_NAME:
            overrides[constants.NAMING_PRESET_DEF_KEY] = self.currentNamingPreset.name
        return overrides

    def updateConfigurationFromRig(self, rig):
        """Updates the current configuration from the given scene rig instance.

        :param rig: The rig instance to pull the configuration from.
        :type rig: :class:`zoo.libs.hive.base.rig.Rig`
        :return: The rig configuration dict pull from the scene rig.
        :rtype: dict
        """
        cache = rig.cachedConfiguration()
        self.applySettingsState(cache)
        return cache

    def applySettingsState(self, state, rig=None):
        # todo: come with a better method of setting and updating the rig
        if rig is not None:
            blackBox = state.get("blackBox")
            if blackBox is not None:
                rig.blackBox = blackBox
            guiControlVis = state.get("guideControlVisibility")
            guiPivotVis = state.get("guidePivotVisibility")
            if guiControlVis is not None or guiPivotVis is not None:
                controlState = -1 if guiControlVis is None else constants.GUIDE_CONTROL_STATE
                guideState = -1 if guiPivotVis is None else constants.GUIDE_PIVOT_STATE
                if controlState == constants.GUIDE_CONTROL_STATE and guideState == constants.GUIDE_PIVOT_STATE:
                    visState = constants.GUIDE_PIVOT_CONTROL_STATE
                elif controlState == constants.GUIDE_CONTROL_STATE:
                    visState = constants.GUIDE_CONTROL_STATE
                else:
                    visState = constants.GUIDE_PIVOT_STATE

                rig.setGuideVisibility(visState,
                                       controlValue=guiControlVis,
                                       guideValue=guiPivotVis,
                                       includeRoot=state.get("includeRoot", False))
            try:
                shapesHidden = state["hideControlShapesInOutliner"]
                for comp in rig.iterComponents():
                    rigLayer = comp.rigLayer()
                    if rigLayer is None:
                        continue

                    for control in rigLayer.iterControls():
                        for shape in control.iterShapes():
                            shape.attribute("hiddenInOutliner").set(shapesHidden)

            except KeyError:
                pass
            try:
                isHistoricallyInteresting = state["isHistoricallyInteresting"]
                for comp in rig.iterComponents():
                    comp.setIsHistoricallyInteresting(isHistoricallyInteresting)
            except KeyError:
                pass
        try:
            preset = state["namingPreset"]
            self.setNamingPresetByName(preset)
        except KeyError:
            pass

        for setting, value in state.items():
            if setting == "buildScripts":
                self.setBuildScripts(value)
                continue
            if hasattr(self, setting):
                setattr(self, setting, value)

    def setNamingPresetByName(self, name):
        """Sets the current Naming convention preset.

        :param name: The Preset Name.
        :type name: str
        """
        preset = self._namingPresetRegistry.findPreset(name)
        if preset is None:
            preset = self._namingPresetRegistry.findPreset(constants.DEFAULT_BUILTIN_PRESET_NAME)
        self.currentNamingPreset = preset

    def findNamingConfigForType(self, hiveType, presetName=None):
        """Finds and returns the naming convention config for the hive Type.

        The Hive Type is one of three keys either "rig", "global" or the component Type.

        :param hiveType: The Hive Type to search for, ie. componentType, "rig" or "global"
        :type hiveType: str
        :param presetName: The Preset to use to find the component Type
        :type presetName: str or None
        :return: The naming configuration Manager instance
        :rtype: :class:`zoo.libs.naming.naming.NameManager`
        """
        preset = self.currentNamingPreset
        if presetName is not None:
            preset = self._namingPresetRegistry.findPreset(presetName)
        return preset.findNamingConfigForType(hiveType)

    def setBuildScripts(self, scriptIds):
        """Overrides the current build scripts applied to this configuration.

        :param scriptIds: A list of build script plugin ids
        :type scriptIds: list[str]
        """

        reg = self._buildScriptRegistry
        self.buildScripts = []
        for buildScriptId in scriptIds:
            if isinstance(buildScriptId, list):
                buildScriptId, _ = buildScriptId
            buildScript = reg.getPlugin(buildScriptId)
            if buildScript is not None:
                self.buildScripts.append(buildScript)

    def addBuildScript(self, scriptId):
        """Adds/appends the build script plugin given the id.

        :param scriptId: The build script plugin id.
        :type scriptId: str
        :return: Whether the build script was added to the configuration.
        :rtype: bool
        """
        if any(i.id == scriptId for i in self.buildScripts):
            return True
        reg = self._buildScriptRegistry
        buildScript = reg.getPlugin(scriptId)
        if buildScript is not None:
            self.buildScripts.append(buildScript)
            return True
        return False

    def buildScriptConfig(self, rig):
        return rig.meta.buildScriptConfig()

    @staticmethod
    def updateBuildScriptConfig(rig, config):
        currentConfig = rig.meta.buildScriptConfig()
        currentConfig.update(config)
        rig.meta.setBuildScriptConfig(currentConfig)

    @staticmethod
    def setBuildScriptConfig(rig, config):
        """Sets the build script configuration on the provided rig.

        .. note::

            Must be json compatible.

        The configData is in the following form.

        .. code-block:: python

            {
                "buildScriptId": {"propertyName": "propertyValue"}
            }

        :param rig: The rig instance to update.
        :type rig: :class:`zoo.libs.hive.base.rig.Rig`
        :param config: The configuration data for any/all buildscripts for the current rig.
        :type config: dict[str,dict]
        """
        rig.meta.setBuildScriptConfig(config)

    def removeBuildScript(self, scriptId):
        """Removes the build script from this rig configuration.

        .. note::

            This will not remove any script specified in userPreferences which
            act as the default for all rigs.

        :param scriptId: The script Id for the buildScript instance to remove
        :type scriptId: str
        :return: True if removed
        :rtype: bool
        """
        defaultUserScripts = self.preferencesInterface.userBuildScripts()
        for script in self.buildScripts:
            if script.id == scriptId and scriptId not in defaultUserScripts:
                self.buildScripts.remove(script)
                script.delete()
                return True
        return False

    def exportPluginForId(self, pluginId):
        """Retrieves the exporter plugin class callable by ID.

        If the plugin id has been overridden in the hive preferences then use that ID instead.

        :param pluginId: The hive exporter plugin id.
        :type pluginId: str
        :return: The plugin id which matches the request.
        :rtype: callable[:class:`zoo.libs.hive.base.exporterplugin.ExporterPlugin`] or None
        """
        overridePluginId = self.exportPluginOverrides.get(pluginId)
        if overridePluginId is None:
            overridePluginId = pluginId
        return self._exporterRegistry.getPlugin(overridePluginId)

    def componentRegistryObject(self, componentType):
        """
        :param componentType: the component type string
        :type componentType: str
        :return:
        :rtype: :class:`zoo.libs.hive.base.component.Component`
        """
        return self._componentRegistry.getComponentObject(componentType)

    def loadComponentDefinition(self, componentType):
        return self._componentRegistry.loadComponentDefinition(componentType)

    def initComponentDefinition(self, componentType):
        return self._componentRegistry.initComponentDefinition(componentType)

    def templatePaths(self):
        """Returns all current Registered search paths for Templates.

        :rtype: list[str]
        """
        return self._templateRegistry.templateRoots

    def graphPaths(self):
        return self._graphRegistry.graphRoots

    def componentPaths(self):
        """Returns all current Registered search paths for Components.

        :rtype: list[str]
        """
        return self._componentRegistry.manager.basePaths

    def definitionPaths(self):
        """Returns all folder search paths registered for the definition files.

        :rtype: list[str]
        """
        return self._componentRegistry.definitionRoots

    @staticmethod
    def buildScriptPaths():
        """Returns all current build script paths from the environment variable as a list.

        :rtype: list[str]
        """
        return [i for i in os.environ[Configuration.buildScriptVar].split(os.pathsep) if i]

    @staticmethod
    def controlShapeNames():
        """Returns all the control shape names from the shape library.

        :rtype: list(str)
        """
        return shapelib.shapeNames()

    @classmethod
    def componentRegistry(cls):
        """Returns the current component registry instance.

        :rtype: :class:`registry.ComponentRegistry`
        """

        return cls._componentRegistry

    @classmethod
    def templateRegistry(cls):
        """Returns the current template registry instance.

        :rtype: :class:`registry.TemplateRegistry`
        """
        return cls._templateRegistry

    @classmethod
    def graphRegistry(cls):
        """Returns the current graph registry instance.

        :rtype: :class:`registry.GraphRegistry`
        """
        return cls._graphRegistry

    @classmethod
    def buildScriptRegistry(cls):
        """Returns the current build script registry instance.

        :rtype: :class:`pluginmanager.PluginManager`
        """
        return cls._buildScriptRegistry

    @classmethod
    def exporterPluginRegistry(cls):
        """Returns the current build script registry instance.

        :rtype: :class:`pluginmanager.PluginManager`
        """
        return cls._exporterRegistry

    @classmethod
    def namePresetRegistry(cls):
        """

        :return:
        :rtype: :class:` namingpresets.PresetManager`
        """
        return cls._namingPresetRegistry

    def reload(self, reloadPlugins=False):
        self._discoverEnvironment()
        if reloadPlugins:
            self._discoverPlugins(force=True)


def initializeComponentRegistry(reload=False):
    if reload or Configuration._componentRegistry is None:
        # componentRegistry, definitions
        reg = registry.ComponentRegistry()
        reg.refresh()
        Configuration._componentRegistry = reg


def initializeTemplateRegistry(reload=False):
    if reload or Configuration._templateRegistry is None:
        # Templates
        reg = registry.TemplateRegistry()
        reg.discoverTemplates()
        Configuration._templateRegistry = reg


def initializeGraphRegistry(reload=False):
    if reload or Configuration._graphRegistry is None:
        # Templates
        reg = registry.GraphRegistry()
        reg.discoverTemplates()
        Configuration._graphRegistry = reg


def initializeBuildScriptRegistry(preferenceInterface, reload=False):
    if reload or Configuration._buildScriptRegistry is None:
        # buildScripts
        reg = pluginmanager.PluginManager(interface=[buildscript.BaseBuildScript], variableName="id",
                                          name="HiveBuildScript")
        paths = os.getenv(Configuration.buildScriptVar, "").split(os.pathsep)
        paths += preferenceInterface.userBuildScriptPaths()

        env.addToEnv("ZOO_BASE_PATHS", paths)
        reg.registerByEnv(Configuration.buildScriptVar)
        reg.registerPaths(preferenceInterface.userBuildScriptPaths())
        reg.loadAllPlugins()

        Configuration._buildScriptRegistry = reg


def initializeExporterRegistry(preferenceInterface, reload=False):
    if reload or Configuration._exporterRegistry is None:
        reg = pluginmanager.PluginManager(interface=[exporterplugin.ExporterPlugin], variableName="id",
                                          name="HiveExporter")
        reg.registerByEnv(Configuration.exportPluginVar)
        reg.registerPaths(preferenceInterface.exporterPluginPaths())
        Configuration._exporterRegistry = reg


def initializeNamingPresetManager(preferencesInterface, reload=False):
    if reload or Configuration._namingPresetRegistry is None:
        manager = namingpresets.PresetManager()
        hierarchy = preferencesInterface.namingPresetHierarchy()
        manager.loadFromEnv(hierarchy)
        Configuration._namingPresetRegistry = manager
