"""The module deals with meta data in maya scenes by adding attributes to nodes and providing
quick and easy query features. Everything is built with the maya python 2.0 to make queries and creation
as fast as possible. Graph Traversal methods works by walking the dependency graph by message attributes.

@todo: may need to create a scene cache with a attach node callback to remove node form the cache
"""
import inspect
import os
import re

from maya.api import OpenMaya as om2
from zoo.core.util import modules
from zoo.core.util import zlogging
from zoo.core.util import classtypes
from zoo.libs.maya.api import plugs
from zoo.libs.maya.api import nodes
from zoo.libs.maya.api import attrtypes
from zoo.libs.maya import zapi
from zoovendor.six import string_types
from zoovendor import six

logger = zlogging.zooLogger

MCLASS_ATTR_NAME = "zooMClass"
MVERSION_ATTR_NAME = "zooMVersion"
MPARENT_ATTR_NAME = "zooMMetaParent"
MCHILDREN_ATTR_NAME = "zooMMetaChildren"


def findSceneRoots():
    """Finds all meta nodes in the scene that are root meta node

    :return:
    :rtype: list()
    """
    return [meta for meta in iterSceneMetaNodes() if not list(meta.iterMetaParents())]


def metaNodeByName(name):
    """Gets meta node by given name

    :param name: The name of the metanode to look for
    :type name: str
    :return: Meta node
    :rtype: MetaBase
    """
    for meta in iterSceneMetaNodes():
        if str(meta.name()) == name:
            return meta


def metaNodeByHandle(handle):
    """Gets meta node by given name

    :param handle: The MObjectHandle of the node to convert to it's meta node class if possible.
    :type handle: str
    :return: Meta node
    :rtype: :class:`MetaBase`
    """
    if isMetaNode(zapi.nodeByObject(handle.object())):
        return MetaBase(handle.object())


def filterSceneByAttributeValues(attributeNames, filter):
    """From the all scene zoo meta nodes find all attributeNames on the node if the value of the attribute is a string
    the filter acts as a regex otherwise it'll will do a value == filter op.

    :param attributeNames: a list of attribute name to find on each node
    :type attributeNames: seq(str)
    :param filter: filters the found attributes by value
    :type filter: any maya datatype
    :return: A seq of plugs
    :rtype: seq(MPlug)
    """
    for meta in iterSceneMetaNodes():
        for attr in attributeNames:
            try:
                plug = meta.attribute(attr)
            except RuntimeError:
                continue
            value = plugs.getPlugValue(plug)
            if isinstance(value, string_types):
                grp = re.search(filter, value)
                if grp:
                    yield plug
            elif value == filter:
                yield plug


def iterSceneMetaNodes():
    """Iterates all meta nodes in the maya scene.

    :rtype: collections.Iterable[MetaBase]
    """
    t = om2.MItDependencyNodes(om2.MFn.kAffect)
    while not t.isDone():
        node = t.thisNode()
        dep = om2.MFnDependencyNode(node)
        if dep.hasAttribute(MCLASS_ATTR_NAME):
            yield MetaBase(node=node)
        t.next()


def findMetaNodesByClassType(classType):
    """Finds and returns all meta nodes in the scene that are of the given class type.

    :param classType: The class type to find.
    :type classType: str
    :rtype: list[:class:`MetaBase`]
    """
    return [
        m
        for m in iterSceneMetaNodes()
        if m.attribute(MCLASS_ATTR_NAME).value() == classType
    ]


def metaFromHandles(handles):
    """Get Meta nodes from MObjectHandles

    :param handles: List of MObjectHandles to retrieve the metanodes from
    :type handles: list[om2.MObjectHandle]
    :return: List of Metanodes
    :rtype: list[zoo.libs.maya.meta.base.MetaBase]
    """
    meta = []
    for mList in [
        getConnectedMetaNodes(zapi.DGNode(node=h.object()))
        for h in handles
        if h.isValid() and h.isAlive()
    ]:
        if mList not in meta:
            meta += mList
    return meta


def metaNodeFromZApiObjects(objects):
    """Converts the specified zapi objects to meta node classes.

    :param objects:
    :type objects: list[:class:`zapi.DGNode`]
    :return:
    :rtype: list[:class:`MetaBase`]
    """
    visited = []
    for mList in [getConnectedMetaNodes(n) for n in objects]:
        for metaNode in mList:
            if metaNode not in visited:
                visited.append(metaNode)
    return visited


def findRelatedMetaNodesByClassType(relatedNodes, classType):
    """From a list of Maya zapi nodes returns the meta node classes matching by string type:

        Checks if attribute value of zooMClass matches the string MClassValue

    :param relatedNodes: any maya nodes by name, should be joints or curves related to joint setup
    :type relatedNodes: list(:class:`zapi.DGNode`)
    :param classType: The attribute value of the meta node Maya attr "zooMClass"
    :type classType: str
    :return metaNodeList: A list of metaNode objects
    :rtype metaNodeList: list(:class:`base.MetaBase`)
    """
    metaNodes = list()
    unfilteredMetaNodes = set()
    for node in relatedNodes:
        unfilteredMetaNodes.update(set(getConnectedMetaNodes(node)))
    if not unfilteredMetaNodes:
        return list()
    for m in unfilteredMetaNodes:
        if m.attribute(MCLASS_ATTR_NAME).value() == classType:
            metaNodes.append(m)

    return metaNodes


def isMetaNodeOfTypes(node, classTypes):
    """Checks whether the provided node is a meta node of the specified types.

    :param node: The node to check
    :type node: :class:`zapi.DGNode`
    :param classTypes: The meta system registered class types.
    :type classTypes: tuple[str]
    :rtype: bool
    """
    if isinstance(node, MetaBase) or issubclass(type(node), MetaBase):
        return True
    if node.hasAttribute(MCLASS_ATTR_NAME):
        if not MetaRegistry.types:
            MetaRegistry()  # ensures  the registry has been populated
        typeStr = node.attribute(MCLASS_ATTR_NAME).asString()
        if typeStr not in classTypes:
            return False
        return MetaRegistry.isInRegistry(typeStr)
    return False


def isMetaNode(node):
    """Determines if the node is a meta node by seeing if the attribute mnode exists and mclass value(classname) is
    within the current meta registry

    :param node: The node to check
    :type node: :class:`zapi.DGNode`
    :rtype: bool
    """

    if isinstance(node, MetaBase) or issubclass(type(node), MetaBase):
        return True
    if node.hasAttribute(MCLASS_ATTR_NAME):
        if not MetaRegistry.types:
            MetaRegistry()  # ensures  the registry has been populated
        return MetaRegistry.isInRegistry(node.attribute(MCLASS_ATTR_NAME).asString())
    return False


def isConnectedToMeta(node):
    """Determines if the node is directly connected to a meta node by searching upstream of the node

    :param node: :class:`zapi.DGNode`
    :rtype: bool
    """
    for dest, source in node.iterConnections(True, False):
        if isMetaNode(source.node()):
            return True
    return False


def getUpstreamMetaNodeFromNode(node):
    """Returns the upstream meta node from node expecting the node to have the metaNode attribute

    :param node: the api node to search from
    :type node: :class:`zapi.DGNode`
    :rtype: MetaBase
    """
    for dest, source in nodes.iterConnections(node, False, True):
        node = source.node()
        if isMetaNode(node):
            return dest, MetaBase(node=node, initDefaults=False)
    return None, None


def getConnectedMetaNodes(node):
    """Returns all the downStream connected meta nodes of 'mObj'

    :param node: The meta node MObject to search
    :type node: :class:`zapi.DGNode`
    :return: A list of MetaBase instances, each node will have its own subclass of metabase returned.
    :rtype: list[:class:`MetaBase`]
    """
    if isMetaNode(node):
        if isinstance(node, zapi.DGNode):
            return [MetaBase(node=node.object(), initDefaults=False)]
        return [node]
    mNodes = []
    for dest in node.message.destinations():
        obj = dest.node()
        if isMetaNode(obj):
            mNodes.append(MetaBase(node=obj.object(), initDefaults=False))
    return mNodes


def createNodeByType(typeName, *args, **kwargs):
    """Creates and returns the type class instance from the meta registry this will also
    create the node in the scene.

    :param typeName: The Class Type name in the registry
    :type typeName: str
    :param args: The args to pass to the class.__init__
    :type args: tuple
    :param kwargs: keywords to pass to the class.__init__
    :type kwargs: dict
    :return: MetaBase, subclass of MetaBase for the type
    :rtype: :class:`MetaBase` or None
    """
    classType = MetaRegistry().getType(typeName)
    if classType is not None:
        return classType(*args, **kwargs)


@six.add_metaclass(classtypes.Singleton)
class MetaRegistry(object):
    """Singleton class to handle global registration to meta classes"""

    metaEnv = "ZOO_META_PATHS"
    types = {}

    def __init__(self):
        try:
            self.reload()
        except ValueError:
            logger.error("Failed to registry environment", exc_info=True)

    def reload(self):
        self.registryByEnv(MetaRegistry.metaEnv)

    @classmethod
    def isInRegistry(cls, typeName):
        """Checks to see if the type is currently available in the registry"""
        return typeName in cls.types

    @classmethod
    def getType(cls, typeName):
        """Returns the class of the type

        :param typeName: the class name
        :type typeName: str
        :return: returns the class object for the given type name
        :rtype: MetaBase
        """
        return cls.types.get(typeName)

    @classmethod
    def registerMetaClasses(cls, paths):
        """This function is helper function to register a list of paths.

        :param paths: A list of module or package paths, see registerByModule() and \
        registerByPackage() for the path format.
        :type paths: list(str)
        """
        for p in paths:
            if os.path.isdir(p):
                cls.registerByPackage(p)
                continue
            elif os.path.isfile(p):
                if not modules.validModulePath(p):
                    continue
                importedModule = modules.importModule(
                    modules.asDottedPath(os.path.normpath(p))
                )
                if importedModule:
                    cls.registerByModule(importedModule)
                    continue

    @classmethod
    def registerByModule(cls, module):
        """This function registry a module by search all class members of the module and registers any class that is an
        instance of the plugin class

        :param module: the module path to registry
        :type module: str
        """
        if inspect.ismodule(module):
            for member in modules.iterMembers(module, predicate=inspect.isclass):
                cls.registerMetaClass(member[1])

    @classmethod
    def registerByPackage(cls, pkg):
        """This function is similar to registerByModule() but works on packages, this is an expensive operation as it
        requires a recursive search by importing all sub modules and and searching them.

        :param pkg: The package path to register eg. zoo.libs.apps
        :type pkg: str
        """
        visited = set()
        for subModule in modules.iterModules(pkg):
            filename = os.path.splitext(os.path.basename(subModule))[0]
            if filename in visited or not modules.validModulePath(subModule):
                continue
            visited.add(filename)
            subModuleObj = modules.importModule(subModule)
            for member in modules.iterMembers(subModuleObj, predicate=inspect.isclass):
                cls.registerMetaClass(member[1])

    @classmethod
    def registryByEnv(cls, env):
        """Register a set of meta class by environment variable

        :param env:  the environment variable name
        :type env: str
        """
        environmentPaths = os.getenv(env)
        if environmentPaths is None:
            raise ValueError(
                "No environment variable with the name -> {} exists".format(env)
            )
        environmentPaths = environmentPaths.split(os.pathsep)
        return cls.registerMetaClasses(environmentPaths)

    @classmethod
    def registerMetaClass(cls, classObj):
        """Registers a plugin instance to the manager

        :param classObj: the metaClass to registry
        :type classObj: Plugin
        """

        if issubclass(classObj, MetaBase) or isinstance(classObj, MetaBase):
            registryName = registryNameForClass(classObj)
            if registryName in cls.types:
                return
            logger.debug("registering metaClass -> {}".format(registryName))
            cls.types[registryName] = classObj


class MetaFactory(type):
    """MetaClass for metabase class to create the correct metaBase subclass based on class plug name if a meta
    node(MObject) exists in the arguments"""

    def __call__(cls, *args, **kwargs):
        """Custom constructor to pull the cls type from the node if it exists and recreates the class instance
        from the registry. If that class doesnt exist then the normal __new__ behaviour will be used
        """
        node = kwargs.get("node")
        if args:
            node = args[0]
        # if the user doesn't pass a node it means they want to create it
        reg = MetaRegistry

        registryName = registryNameForClass(cls)
        if registryName not in reg.types:
            reg.registerMetaClass(cls)
        if not node:
            return type.__call__(cls, *args, **kwargs)
        classType = MetaBase.classNameFromPlug(node)
        if classType == registryName:
            return type.__call__(cls, *args, **kwargs)

        registeredType = MetaRegistry().getType(classType)
        if registeredType is None:
            return type.__call__(cls, *args, **kwargs)
        return type.__call__(registeredType, *args, **kwargs)


def registryNameForClass(classType):
    """Returns the registry name for the class type, this is the class name or the id if it exists.
    The ID is preferred of the class name.

    :param classType: The class object or instance to get the registry name for.
    :type classType: :class:`MetaBase`
    :return: The class type id.
    :rtype: str
    """
    return classType.id or classType.__name__


@six.add_metaclass(MetaFactory)
class MetaBase(zapi.DGNode):
    # for persistent ui icons
    icon = "networking"
    id = ""

    @staticmethod
    def classNameFromPlug(node):
        """Given the MObject node or metaClass return the associated class name which should exist on the maya node
        as an attribute

        :param node: the node to find the class name for
        :type node: MObject or MetaBase instance
        :return:  the mClass name
        :rtype: str
        """
        if isinstance(node, MetaBase):
            return node.attribute(MCLASS_ATTR_NAME).value()
        dep = om2.MFnDependencyNode(node)
        try:
            return dep.findPlug(MCLASS_ATTR_NAME, False).asString()
        except RuntimeError as er:
            return er

    def __init__(self, node=None, name=None, initDefaults=True, lock=False, mod=None):
        """Meta base class

        :param node: Build the meta node based on this node
        :type node: :class:`zapi.DagNode or zapi.DGNode`
        :param name: Name of the meta node
        :type name: str
        :param initDefaults: Initialise meta defaults
        :type initDefaults: bool
        :param lock: Lock after building if true, false otherwise
        :type lock: bool
        :param mod: The maya modifier to add to
        :type mod: :class:`maya.api.OpenMaya.MDagModifier`
        """
        super(MetaBase, self).__init__(node=node)
        if node is None:
            self.create(
                name or "_".join([registryNameForClass(self.__class__), "meta"]),
                nodeType="network",
                mod=mod,
            )
        if initDefaults and not self.isReferenced():
            if mod:
                mod.doIt()
            self._initMeta(mod=mod)
            if lock and not self._mfn.isLocked:
                self.lock(True, mod=mod)

    def _initMeta(self, mod=None):
        """Initializes the standard attributes for the meta nodes."""
        return self.createAttributesFromDict(
            {k["name"]: k for k in self.metaAttributes()}, mod=mod
        )

    def purgeMetaAttributes(self):
        attrs = []
        for attr in self.metaAttributes():
            attrs.append(plugs.serializePlug(self.attribute(attr["name"])))
            self.deleteAttribute(attr["name"])
        return attrs

    def metaAttributes(self):
        className = registryNameForClass(self.__class__)

        return [
            {
                "name": MCLASS_ATTR_NAME,
                "value": className,
                "Type": attrtypes.kMFnDataString,
                "locked": True,
                "storable": True,
                "writable": True,
                "connectable": False,
            },
            {
                "name": MVERSION_ATTR_NAME,
                "value": "1.0.0",
                "Type": attrtypes.kMFnDataString,
                "locked": True,
                "storable": True,
                "writable": True,
                "connectable": False,
            },
            {
                "name": MPARENT_ATTR_NAME,
                "value": None,
                "Type": attrtypes.kMFnMessageAttribute,
                "isArray": True,
                "locked": False,
            },
            {
                "name": MCHILDREN_ATTR_NAME,
                "value": None,
                "Type": attrtypes.kMFnMessageAttribute,
                "locked": False,
                "isArray": True,
            },
        ]

    def metaAttributeValues(self):
        """Get the Meta attributes values

        :return: Meta attribute values
        :rtype: dict
        """
        return {
            a: self.attribute(a).value()
            for a in [attr["name"] for attr in self.metaAttributes()]
        }

    def isRoot(self):
        for i in self.iterMetaParents():
            return True
        return False

    def mClassType(self):
        return self.attribute(MCLASS_ATTR_NAME).value()

    def delete(self, mod=None, apply=True):
        """Overloaded function to disconnect child meta nodes before deleting

        :param mod: Modifier to add the delete to
        :type mod: :class:`om2.MDGModifier` or `om2.MDagModifier`
        :param apply: Apply the modifier immediately if true, false otherwise
        :type apply: bool
        """
        childPlug = self.attribute(MCHILDREN_ATTR_NAME)

        for element in childPlug:
            element.disconnectAll(modifier=mod)
        return super(MetaBase, self).delete(mod, apply)

    def findConnectedNodesByAttributeName(self, filter, recursive=False):
        plugList = self.findPlugsByFilteredName(filter)
        results = [p.source().node() for p in plugList if p.isDestination]
        if recursive:
            for m in iter(self.iterMetaChildren()):
                for p in iter(m.findPlugsByFilteredName(filter)):
                    if p.isDestination:
                        results.extend(p.source().node())
        return results

    def findPlugsByFilteredName(self, filter=""):
        """Finds all plugs with the given filter with in name

        :param filter: the string the search the names by
        :type filter: str
        :return: A seq of MPlugs
        :rtype: seq(MPlug)
        """
        plugList = []
        for i in self.iterAttributes():
            grp = re.search(filter, i.name())
            if grp:
                plugList.append(i)
        return plugList

    def connectTo(self, attributeName, node):
        """Connects one plug to another by attribute name

        :param attributeName: the meta attribute name to connect from, if it doesn't exist it will be created
        :type attributeName: str
        :param node: the destination node
        :type node: MObject
        :return: the destination plug
        :rtype: om2.MPlug
        """
        nodeAttributeName = "message"
        sourcePlug = node.attribute(nodeAttributeName)

        if self.hasAttribute(attributeName):
            # we should have been disconnected from the destination control above
            destinationPlug = self.attribute(attributeName)
        else:
            newAttr = self.addAttribute(
                attributeName, value=None, Type=attrtypes.kMFnMessageAttribute
            )
            if newAttr is not None:
                destinationPlug = newAttr
            else:
                destinationPlug = self.attribute(attributeName)
        sourcePlug.connect(destinationPlug)
        return destinationPlug

    def connectToByPlug(self, destinationPlug, node):
        sourcePlug = node.attribute("message")
        sourcePlug.connect(destinationPlug)
        return destinationPlug

    def metaRoot(self):
        for currentParent in self.iterMetaParents(recursive=True):
            parents = list(currentParent.iterMetaParents(recursive=False))
            if not parents:
                return currentParent

    def metaParents(self, recursive=False):
        return list(self.iterMetaParents(recursive=recursive))

    def iterMetaParents(self, recursive=False):
        parentPlug = self.attribute(MPARENT_ATTR_NAME)
        for childElement in parentPlug:
            for dest in childElement.destinations():
                parentMeta = MetaBase(dest.node().object(), initDefaults=False)
                yield parentMeta
                if recursive:
                    for i in parentMeta.iterMetaParents(recursive=recursive):
                        yield i

    def iterChildren(self, fnFilters=None, includeMeta=False):
        filterTypes = fnFilters or ()
        for source, destination in self.iterConnections(False, True):
            destNode = destination.node()
            if not filterTypes or any(destNode.hasFn(i) for i in filterTypes):
                if not includeMeta and isMetaNode(destNode):
                    continue
                yield destNode

    def iterMetaChildren(self, depthLimit=256, visited=None):
        """This function iterates the meta children by the metaChildren Plug and returns the metaBase instances

        :param depthLimit: The traversal depth limit
        :type depthLimit: int
        :return: A list of Metabase instances
        :rtype: list(MetaBase)
        """
        childPlug = self.attribute(MCHILDREN_ATTR_NAME)
        visited = visited or set()
        for element in childPlug:
            if depthLimit < 1:
                return
            child = element.source()
            if child is None:
                continue
            child = child.node()
            if not child.hasAttribute(MCHILDREN_ATTR_NAME) or child in visited:
                continue
            visited.add(child)
            childMeta = MetaBase(child.object(), initDefaults=False)
            yield childMeta

            for subChild in childMeta.iterMetaChildren(
                depthLimit=depthLimit - 1, visited=visited
            ):
                yield subChild

    metaChildren = iterMetaChildren

    def iterMetaTree(self, depthLimit=256):
        """This function traverses the meta tree pulling out any meta node this is done by checking each node
        has the mclass Attribute. This function can be slow depending on the size of the tree

        :param depthLimit:
        :type depthLimit: int
        :rtype: generator(MetaBase)
        """
        if depthLimit < 1:
            return
        for source, destination in nodes.iterConnections(self.object(), False, True):
            node = destination.node()
            if isMetaNode(node):
                m = MetaBase(node, initDefaults=False)
                yield m
                for i in m.iterMetaTree(depthLimit=depthLimit - 1):
                    yield i

    def addMetaChild(self, child, mod=None):
        """Add meta child

        :param child:
        :type child: :class:`MetaBase`
        :param mod:
        :type mod: :class:`maya.api.OpenMaya.MDagModifier or maya.api.OpenMaya.MDGModifier`
        """
        child.removeParent(mod=mod)
        child.addMetaParent(self, mod=mod)

    def addMetaParent(self, parent, mod=None):
        """Sets the parent meta node for this node, removes the previous parent if its attached

        :param parent: The meta node to add as the parent of this meta node
        :type parent: MetaBase
        :param mod:
        :type mod: :class:`maya.api.OpenMaya.MDagModifier or maya.api.OpenMaya.MDGModifier`
        """
        parentPlug = self.attribute(MPARENT_ATTR_NAME)
        nextElement = parentPlug.nextAvailableElementPlug()
        nextElement.connect(
            parent.attribute(MCHILDREN_ATTR_NAME).nextAvailableDestElementPlug(),
            mod=mod,
        )

    def attributeNodes(self, attrPlug):
        """Returns a list of dag/dg nodes from the given meta attribute plug.

        :type attrPlug: zapi.Plug
        :return: list of zapi nodes
        :rtype: list(:class:`zapi.DGNode`)
        """
        return [plug.sourceNode() for plug in attrPlug if plug]

    def findChildrenByFilter(self, filter, plugName=None, depthLimit=256):
        children = []
        for child in self.iterMetaChildren(depthLimit):
            if not plugName:
                grp = re.search(filter, nodes.nameFromMObject(child))
            else:
                try:
                    plug = child._mfn.findPlug(plugName, False)
                    grp = re.search(filter, plugs.getPlugValue(plug))
                except RuntimeError:
                    continue
            if grp:
                children.append(child)
        return children

    def findChildrenByClassType(self, classType, depthLimit=1):
        """Find's all meta children of a certain type.

        :param classType: The zoo meta class type name.
        :type classType: str
        :param depthLimit: The recursive depth limit, defaults to a depth of 1.
        :type depthLimit: int
        :return: An iterable of metaBase instances.
        :rtype: iterable[:class:`MetaBase`]
        """
        return [
            child
            for child in self.iterMetaChildren(depthLimit=depthLimit)
            if child.mClassType() == classType
        ]

    def findChildrenByClassTypes(self, classTypes, depthLimit=1):
        """Find's all meta children of a certain type.

        :param classTypes: The zoo meta class type name.
        :type classTypes: iterable[str]
        :param depthLimit: The recursive depth limit, defaults to a depth of 1.
        :type depthLimit: int
        :return: An iterable of metaBase instances.
        :rtype: iterable[:class:`MetaBase`]
        """
        return [
            child
            for child in self.iterMetaChildren(depthLimit=depthLimit)
            if child.mClassType() in classTypes
        ]

    def findChildByType(self, Type):
        return [
            child
            for child in self.iterMetaChildren(depthLimit=1)
            if child.apiType() == Type
        ]

    def allChildrenNodes(self, recursive=False, includeMeta=False):
        children = []
        for source, destination in self.iterConnections(False, True):
            node = destination.node()
            if node not in children:
                if includeMeta and node.hasAttribute(MCLASS_ATTR_NAME):
                    continue
                children.append(node)
        if recursive:
            for child in self.iterMetaChildren():
                children.extend(
                    [
                        i
                        for i in child.allChildrenNodes(
                            recursive=recursive, includeMeta=includeMeta
                        )
                        if i not in children
                    ]
                )
        return children

    def removeParent(self, parent=None, mod=None):
        """Remove Parent

        :param parent: The meta class to remove, if set to None then all parents will be removed
        :type parent: :class:`MetaBase` or None
        :rtype: bool
        """
        modifier = mod or zapi.dgModifier()
        parentPlug = self.attribute(MPARENT_ATTR_NAME)
        for element in parentPlug:
            for dest in element.destinations():
                n = dest.node()
                if parent is None or n == parent:
                    element.disconnect(dest, modifier=modifier, apply=False)
        if mod is None:
            modifier.doIt()
        return True

    def removeAllParents(self):
        parentPlug = self.attribute(MPARENT_ATTR_NAME)
        for element in parentPlug:
            for dest in element.destinations():
                element.disconnect(dest)
                try:
                    element.delete()
                except RuntimeError:
                    pass
        return True

    @classmethod
    def metaNodesInScene(cls):
        """List of metanodes of same type

        :return:
        :rtype: list[:class:`MetaBase`]
        """
        return findMetaNodesByClassType(registryNameForClass(cls))

    @classmethod
    def connectedMetaNodes(cls, node):
        """Returns the meta nodes if it's the same class type

        :param node:
        :type node: :class:`zapi.DagNode`
        """
        metaNodes = getConnectedMetaNodes(node)

        if metaNodes:
            retNodes = [
                m
                for m in metaNodes
                if registryNameForClass(m.__class__) == registryNameForClass(cls)
            ]
            if retNodes:
                return retNodes[-1]

    def isClassType(self, metaBase):
        """Returns true if is class type

        :param metaBase:
        :type metaBase: Type[MetaBase]
        :return:
        :rtype:
        """
        return self.mClassType() == registryNameForClass(metaBase)
