import copy
import inspect
import os

from zoo.libs.utils import filesystem
from zoo.libs.hive.base import definition as baseDef
from zoo.libs.hive.base import errors
from zoo.libs.hive.base import component
from zoo.libs.hive import constants
from zoo.preferences.interfaces import hiveinterfaces
from zoo.core.plugin import pluginmanager
from zoo.core.util import classtypes, modules
from zoo.core.util import zlogging
from zoovendor import six


logger = zlogging.getLogger(__name__)


@six.add_metaclass(classtypes.Singleton)
class ComponentRegistry(object):
    """This class manages and stores a collection of component objects from the component library, this class is a
    singleton
    and is responsible for returning the creation of component objects and definitions.
    """

    def __init__(self):
        # {Type: {"object": clsObj,
        #         "path": path,
        #         "definition": clsObj.definitionName}}
        self.components = {}
        self.definitions = {}
        self.manager = None  # type: pluginmanager.PluginManager or None
        self.definitionRoots = []
        self._prefInterface = hiveinterfaces.hiveInterface()

    def refresh(self):
        """Refreshes the library by clearing the registry then rediscovering the component plugins"""
        self.components = {}
        self.definitions = {}
        self.manager = pluginmanager.PluginManager(
            interface=[component.Component],
            variableName="definitionName",
            name="HiveComponentRegistry",
        )
        self.discoverComponents()

    def initComponentDefinition(self, name):
        """Creates and returns a new ComponentDefinition instance based on the name parameter

        :param name: the componentType
        :type name: str
        :rtype: :class:`baseDef.ComponentDefinition` or None
        """
        data = self.loadComponentDefinition(name)
        compInfo = self.componentData(name)
        if data and compInfo:
            return baseDef.loadDefinition(data, data, path=compInfo["path"])

    def fromMetaNode(self, rig, metaNode):
        """Create a new component of a specified type and attach it to a rig.

        :param rig: The rig to which the new component will be attached.
        :type rig: :class:`Rig`
        :param metaNode: The metadata for the new component.
        :type metaNode: :class:`zoo.libs.hive.base.hivenodes.HiveComponent`
        :raises MissingRootTransform: If the provided `metaNode` does not have a root transform.
        :returns: A new component of the specified type, initialized with the provided `rig` and `metaNode`.
        :rtype: :class:`zoo.libs.hive.base.component.Component`
        """
        root = metaNode.rootTransform

        if not root:
            raise errors.MissingRootTransform(metaNode.fullPathName())
        componentType = metaNode.componentType.asString()
        newComponent = self.findComponentByType(componentType)
        newComponent = newComponent(rig, metaNode=metaNode)
        return newComponent

    def findComponentByType(self, name):
        """Find and return the component class object from the registry.

        :param name: the component name, currently the class name
        :type name: str
        :return: callable[:class:`zoo.libs.hive.base.component.Component`]
        """
        try:
            return self.components[name]["object"]
        except KeyError:
            raise ValueError(
                "Component requested is not available. requested: '{}', \navailable: {}".format(
                    name, self.components.keys()
                )
            )

    def loadComponentDefinition(self, componentName):
        """Loads the definition file for the component in the registry using json.

        :param componentName: the component name currently the class name
        :type componentName: str
        :return: the definition dict
        :rtype: dict
        """
        if componentName in self.components:
            try:
                definitionInfo = self.definitions[
                    self.components[componentName]["definition"]
                ]
                return copy.deepcopy(definitionInfo["data"])
            except ValueError:
                logger.error(
                    "Failed to load component definition: {}".format(componentName),
                    exc_info=True,
                )
                raise ValueError(
                    "Failed to load component definition: {}".format(componentName)
                )
        raise ValueError(
            "Component requested is not available. requested: {}, \navailable: {}".format(
                componentName, self.definitions.keys()
            )
        )

    def saveComponentDefinition(self, definition):
        """Saves the definition object by overwrite the existing one.

        :param definition: The definition object to save.
        :type definition: :class:`baseDef.ComponentDefinition`
        :rtype: bool
        """
        componentInfo = self.componentData(definition.type)
        definitionName = componentInfo["definition"]
        baseDefinition = self.definitions[definitionName]
        physicalPath = baseDefinition["path"]
        filesystem.saveJson(definition.serialize(), physicalPath)
        self.definitions[baseDefinition["data"]["type"]] = {
            "path": physicalPath,
            "data": definition,
        }
        return True

    def componentData(self, name):
        """returns the registry component dict

        :param name: the component type to get
        :type name: str
        :return: {"object": object(), \
                 "path": str, \
                 "definition": str } # the definition name \
        :rtype: dict
        """
        return self.components.get(name)

    def componentDataByPath(self, path):
        """Returns the component data and name from the registry based on the provided filePath

        :param path: The component file path including the extension
        :type path: str
        :return: The component name and register info containing "object", "path" amd "definition" keys
        :rtype: tuple[str, dict]
        """
        normPath = path.replace("\\", "/").rpartition(os.extsep)[0]
        for name, componentInfo in self.components.items():
            if componentInfo["path"].rpartition(os.extsep)[0] == normPath:
                return name, componentInfo
        return "", {}

    def discoverComponents(self):
        """Searches the component library specfied by the environment variable "ZOO_HIVE_COMPONENT_PATH" """
        self.manager.registerByEnv(constants.ENV_COMPONENT_KEY)
        componentsPaths = self._prefInterface.userComponentPaths()
        self.manager.registerPaths(componentsPaths)
        # discover the definitions and store them in self.definitions
        definitionPaths = os.environ[constants.ENV_DEFINITION_KEY].split(os.pathsep)
        self.definitionRoots = definitionPaths + componentsPaths
        for p in definitionPaths + componentsPaths:
            for root, dirs, files in os.walk(p):
                for f in files:
                    if not f.endswith(constants.DEFINITION_EXT):
                        continue
                    if f.startswith(modules.MODULE_EXCLUDE_PREFIXES):
                        continue
                    defBaseName = f.split(os.extsep)[0]
                    if defBaseName in self.definitions:
                        continue
                    path = os.path.join(root, f)
                    cache = self._loadComponentFromPath(path)
                    self.definitions[cache["type"]] = {
                        "path": path.replace("\\", "/"),
                        "data": cache,
                    }
        for name, clsObj in iter(self.manager.plugins.items()):
            path = inspect.getfile(clsObj)
            if name in self.components:
                continue
            self.components[name] = {
                "object": clsObj,
                "path": path.replace("\\", "/"),
                "definition": clsObj.definitionName,
            }

    def _loadComponentFromPath(self, path):
        try:
            return filesystem.loadJson(path)
        except ValueError:
            logger.error(
                "Failed to load component definition: {}".format(path), exc_info=True
            )
            raise ValueError("Failed to load component definition: {}".format(path))


@six.add_metaclass(classtypes.Singleton)
class TemplateRegistry(object):
    """Class to handle hive templates, templates are the serialized form of a rig."""

    def __init__(self):
        self._templates = {}
        self.templateRoots = []
        self._prefInterface = hiveinterfaces.hiveInterface()

    @property
    def templates(self):
        """A property that returns a dictionary of templates in the form of {"templateName": "templatePath"}.

        :returns: A dictionary where the keys are template names and the values are template file paths.
        :rtype: dict
        """
        # validate and update the cache if any of the templates get deleted off disk
        _valid = {}
        for tempName, templatePath in self._templates.items():
            if not os.path.exists(templatePath):
                continue
            _valid[tempName] = templatePath
        self._templates = _valid

        return self._templates

    def refresh(self):
        """Refreshes the library by clearing the registry then rediscovering the component plugins"""
        self._templates = {}
        self.discoverTemplates()

    def saveLocation(self):
        """Returns the current save folder path from the zoo preferences.

        :rtype: str
        """
        return self._prefInterface.userTemplateSavePath()

    def saveTemplate(self, name, template, templateRootPath=None, overwrite=False):
        """Save a template to the specified location on the file system.

        :param name: The name of the template.
        :type name: str
        :param template: The template data to be saved.
        :type template: dict
        :param templateRootPath: The root directory where the template should be saved. \
        If not specified, the default save location will be used.
        :type templateRootPath: str, optional
        :param overwrite: Indicates whether to overwrite an existing template with the same name. \
        If `False` and a template with the same name already exists, a `TemplateAlreadyExistsError` will be raised.
        :type overwrite: bool, optional
        :raises TemplateAlreadyExistsError: If a template with the same name already exists and `overwrite` is `False`.
        :raises IOError: If there was an error writing the template to the specified file path.
        :returns: The file path where the template was saved.
        :rtype: str
        """
        template["name"] = name
        root = templateRootPath
        if root is None:
            root = self.saveLocation()

        newTemplatePath = os.path.join(root, name + constants.TEMPLATE_EXT)
        if os.path.exists(newTemplatePath) and not overwrite:
            logger.error("Template path: {} already exists".format(newTemplatePath))
            raise errors.TemplateAlreadyExistsError(newTemplatePath)
        filesystem.ensureFolderExists(os.path.dirname(newTemplatePath))
        saved = filesystem.saveJson(template, newTemplatePath, message=False)
        if not saved:
            raise IOError(
                "Failed to write template for unknown reasons to file: {}".format(
                    newTemplatePath
                )
            )
        self.addTemplate(newTemplatePath)
        return newTemplatePath

    def saveComponentsAsTemplate(
        self, rig, components, name, templateRootPath, overwrite
    ):
        """Save the specified components as a template.

        :param rig: The rig containing the components.
        :type rig: Rig
        :param components: The components to be saved as a template.
        :type components: list
        :param name: The name of the template.
        :type name: str
        :param templateRootPath: The root directory where the template should be saved.
        :type templateRootPath: str
        :param overwrite: Indicates whether to overwrite an existing template with the same name. \
        If `False` and a template with the same name already exists, a `TemplateAlreadyExistsError` will be raised.
        :type overwrite: bool
        :returns: The file path where the template was saved.
        :rtype: str
        """
        data = rig.serializeFromScene(components)
        return self.saveTemplate(
            name, data, templateRootPath=templateRootPath, overwrite=overwrite
        )

    def renameTemplate(self, name, newName):
        """Rename a template.

        :param name: The current name of the template.
        :type name: str
        :param newName: The new name for the template.
        :type newName: str
        :raises OSError: If there was an error renaming the template file.
        """
        template = self.templatePath(name)
        if template is not None and os.path.exists(template):
            try:
                newTemplatePath = os.path.join(
                    os.path.dirname(template), newName + constants.TEMPLATE_EXT
                ).replace("\\", "/")
                os.rename(template, newTemplatePath)
                currentData = filesystem.loadJson(newTemplatePath)
                currentData["name"] = newName
                filesystem.saveJson(currentData, newTemplatePath)
                self.templates[newName.lower()] = newTemplatePath
            except OSError:
                logger.error(
                    "Failed to rename template: {}".format(name), exc_info=True
                )
                raise

    def deleteTemplate(self, name):
        """Delete a template with the specified name.

        :param name: The name of the template to delete.
        :type name: str
        :raises OSError: If there was an error deleting the template file.
        :returns: `True` if the template was successfully deleted, `False` otherwise.
        :rtype: bool
        """
        template = self.templatePath(name)
        if template is not None and os.path.exists(template):
            try:
                os.remove(template)
                del self._templates[name.lower()]
                return True
            except OSError:
                logger.error(
                    "Failed to remove template: {}".format(template), exc_info=True
                )
                raise

    def hasTemplate(self, name):
        """Checks whether the registry contains the template with the name.

        :param name: The template name to check.
        :type name: str
        :return: Returns True if the template exists in the registry.
        :rtype: bool
        """
        return self.templatePath(name) != ""

    def template(self, name):
        """Returns the rig template dict from the registry

        :param name: the template name
        :type name: str
        :return: The loaded template dict
        :rtype: dict
        """
        return filesystem.loadJson(self.templatePath(name))

    def templatePath(self, name):
        """Get the file path for the template with the specified name.

        :param name: The name of the template.
        :type name: str
        :return: The file path for the template with the specified name, \
        or an empty string if no template with the given name was found.
        :rtype: str
        """

        return self.templates.get(name.lower(), "")

    def addTemplate(self, path):
        """Add a template to the registry.

        :param path: The file path for the template.
        :type path: str
        """
        if not path.endswith(constants.TEMPLATE_EXT):
            return
        if path.startswith(modules.MODULE_EXCLUDE_PREFIXES):
            return
        self.templates[
            os.path.splitext(os.path.basename(path))[0].lower()
        ] = path.replace("\\", "/")

    def templateByPath(self, path):
        """Returns the template data from the registry based on the provided filePath

        :param path: The template file path including the extension
        :type path: str
        :return:
        :rtype: dict
        """
        normPath = path.replace("\\", "/")
        for name, templatePath in self.templates.items():
            if templatePath == normPath:
                return self.template(name)
        return {}

    def discoverTemplates(self):
        """Discovers all templates in the given paths and stores them in the registry."""
        paths = os.getenv(constants.ENV_TEMPLATES_KEY, "").split(os.pathsep)
        paths += self._prefInterface.userTemplatePaths()
        if not paths:
            return False
        self.templateRoots = paths
        for p in paths:
            if not os.path.exists(p):
                continue
            elif os.path.isfile(p):
                self.addTemplate(p)
            for root, dirs, files in os.walk(p):
                for f in iter(files):
                    self.addTemplate(os.path.join(root, f))


@six.add_metaclass(classtypes.Singleton)
class GraphRegistry(object):
    """Class to handle hive DependencyGraphs.

    This class is a singleton, meaning that there will always be only one instance of it.
    """

    def __init__(self):
        self._graphs = {}
        self._cache = {}
        self.graphsRoots = []

    @property
    def graphs(self):
        """Get the dictionary of graph names to file paths for all graphs in the registry.

        :return: A dictionary of graph names to file paths.
        :rtype: dict
        """
        return self._graphs

    def refresh(self):
        """Refreshes the library by clearing the registry then rediscovering the component plugins"""
        self._graphs = {}
        self._cache = {}
        self.discoverTemplates()

    def saveGraph(self, name, namedGraph):
        """Save a graph with the specified name.

        :param name: The name of the graph.
        :type name: str
        :param namedGraph: The graph to be saved.
        :type namedGraph: :class:`zoo.libs.hive.base.serialization.dggraph.NamedDGGraph`
        :return: The file path where the graph was saved.
        :rtype: str
        """
        namedGraph.rename(name)
        data = namedGraph.serialize()
        outPath = self.graphPath(name)
        if not outPath:
            outPath = os.path.normpath(os.environ[constants.ENV_GRAPHS_KEY])
            outPath = os.path.join(outPath, name + constants.GRAPH_EXT)
        filesystem.ensureFolderExists(os.path.dirname(outPath))
        saved = filesystem.saveJson(data, outPath, message=False)
        if not saved:
            raise IOError(
                "Failed to write template for unknown reasons to file: {}".format(
                    outPath
                )
            )
        self.addGraph(outPath)
        if name in self._cache:
            del self._cache[name]
        return outPath

    def renameGraph(self, name, newName):
        """Rename a graph in the registry.

        :param name: The current name of the graph.
        :type name: str
        :param newName: The new name for the graph.
        :type newName: str
        """
        graph = self.graphPath(name)
        if graph is not None and os.path.exists(graph):
            try:
                newTemplatePath = os.path.join(
                    os.path.dirname(graph), newName + constants.GRAPH_EXT
                )
                os.rename(graph, newTemplatePath)
                currentData = filesystem.loadJson(newTemplatePath)
                currentData["id"] = newName
                filesystem.saveJson(currentData, newTemplatePath)
                self._graphs[newName] = newTemplatePath
            except OSError:
                logger.error("Failed to rename Graph: {}".format(name), exc_info=True)
                raise

    def hasGraph(self, name):
        """Checks whether the registry contains the graph with the name.

        :param name: The graph name to check.
        :type name: str
        :return: Returns True if the template exists in the registry.
        :rtype: bool
        """
        return self.graphPath(name) != ""

    def graph(self, name):
        """Returns the rig template dict from the registry

        :param name: the graph name
        :type name: str
        :return:
        :rtype: :class:`baseDef.NamedGraph`
        """
        cached = self._cache.get(name)
        if cached:
            return baseDef.NamedGraph.fromData(cached)
        path = self.graphPath(name)
        if not os.path.exists(path):
            raise ValueError(
                "Graph requested is not available. requested: {}, \navailable: {}".format(
                    name, self._graphs.keys()
                )
            )
        data = filesystem.loadJson(path)
        self._cache[name] = data
        return baseDef.NamedGraph.fromData(data)

    def graphPath(self, name):
        """Returns the file path of the graph with the given name.

        :param name: The name of the graph to find.
        :type name: str
        :return: The file path of the graph.
        :rtype: str
        """
        return self._graphs.get(name, "")

    def addGraph(self, path):
        """Add a graph to the registry.

        :param path: The file path of the graph to add.
        :type path: str
        """
        if not path.endswith(constants.GRAPH_EXT):
            return
        if path.startswith(modules.MODULE_EXCLUDE_PREFIXES):
            return
        self._graphs[os.path.splitext(os.path.basename(path))[0]] = path.replace(
            "\\", "/"
        )

    def discoverTemplates(self):
        """Find all graph files in the graph roots and add them to the registry."""
        paths = os.getenv(constants.ENV_GRAPHS_KEY, "").split(os.pathsep)
        if not paths:
            return False
        self.graphsRoots = paths
        for p in paths:
            if not os.path.exists(p):
                continue
            elif os.path.isfile(p):
                self.addGraph(p)
            for root, dirs, files in os.walk(p):
                for f in iter(files):
                    self.addGraph(os.path.join(root, f))
