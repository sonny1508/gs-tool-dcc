import contextlib
import math

from maya.api import OpenMaya as om2
from maya.api import OpenMayaAnim as om2Anim
from maya import OpenMaya as om1
from maya import cmds

from zoovendor.six.moves import range

from zoo.libs.maya.api import plugs, generic, anim
from zoo.libs.maya.api import attrtypes
from zoo.libs.maya.utils import mayamath, general
from zoo.libs.utils import zoomath
from zoo.libs.utils import path as zooPath
from zoo.core.util import zlogging

logger = zlogging.getLogger(__name__)


class MissingObjectByName(Exception):
    pass


class AttributeAlreadyExists(Exception):
    pass


def asMObject(name):
    """Returns the MObject from the given name

    :param name: The name to get from maya to convert to a mobject
    :type name: str or MObjectHandle or MDagPath
    :return: The mobject for the given str
    :rtype: MObject

    """
    sel = om2.MSelectionList()
    try:
        sel.add(name)
    except RuntimeError:
        raise MissingObjectByName(name)
    try:
        return sel.getDagPath(0).node()
    except TypeError:
        return sel.getDependNode(0)


def nameFromMObject(mobject, partialName=False, includeNamespace=True):
    """This returns the full name or partial name for a given mobject, the mobject must be valid.

    :param mobject:
    :type mobject: MObject
    :param partialName: if False then this function will return the fullpath of the mobject.
    :type partialName: bool
    :param includeNamespace: if False the namespace will be stripped
    :type includeNamespace: bool
    :return:  the name of the mobject
    :rtype: str

    .. code-block:: python

        from zoo.libs.maya.api import nodes
        node = nodes.asMobject(cmds.polyCube())
        print nodes.nameFromMObject(node, partial=False) # returns the fullpath, always prepends '|' eg '|polyCube'
        print nodes.nameFromMObject(node, partial=True) # returns the partial name eg. polyCube1

    """
    if mobject.hasFn(om2.MFn.kDagNode):
        if partialName:
            name = om2.MFnDagNode(mobject).partialPathName()
        else:
            name = om2.MFnDagNode(mobject).fullPathName()
    else:
        # dependency node
        name = om2.MFnDependencyNode(mobject).name()
    if not includeNamespace:
        name = om2.MNamespace.stripNamespaceFromName(name)

    return name


def toApiMFnSet(node):
    """
    Returns the appropriate mObject from the api 2.0

    :param node: str, the name of the node
    :type node: str, MObjectHandle
    :return: MFnDagNode, MPlug, MFnDependencyNode
    :rtype: MPlug or MFnDag or MFnDependencyNode

    .. code-block:: python

        from zoo.libs.maya.api import nodes
        node = cmds.polyCube()[0] # str
        nodes.toApiObject(node)
        # Result MFnDagNode
        node = cmds.createNode("multiplyDivide")
        nodes.toApiObject(node)
        # Result MFnDependencyNode
    """
    if isinstance(node, om2.MObjectHandle):
        node = node.object()
    elif isinstance(node, (om2.MFnDependencyNode, om2.MFnDagNode)):
        return node

    sel = om2.MSelectionList()
    sel.add(node)
    try:
        tmp = sel.getDagPath(0)
        tmp = om2.MFnDagNode(tmp)
    except TypeError:
        tmp = om2.MFnDependencyNode(sel.getDependNode(0))
    return tmp


def asDagPath(node):
    sel = om2.MSelectionList()
    sel.add(node)
    return sel.getDagPath(0)


def setNodeColour(node, colour, outlinerColour=None, useOutlinerColour=False, mod=None):
    """Set the given node mobject override color can be a mobject representing a transform or shape

    :param node: the node which you want to change the override colour of
    :type node: mobject
    :param colour: The RGB colour to set
    :type colour: MColor or tuple
    """
    colour = list(colour)
    if colour and len(colour) > 3:
        colour = colour[:-1]

    modifier = mod or om2.MDGModifier()
    dependNode = om2.MFnDependencyNode(node)
    plug = dependNode.findPlug("overrideColorRGB", False)
    enabledPlug = dependNode.findPlug("overrideEnabled", False)
    overrideRGBColors = dependNode.findPlug("overrideRGBColors", False)
    if not enabledPlug.asBool():
        modifier.newPlugValueBool(enabledPlug, True)
    if not overrideRGBColors.asBool():
        modifier.newPlugValueBool(overrideRGBColors, True)

    fnData = om2.MFnNumericData(plug.asMObject()).setData(colour)
    modifier.newPlugValue(plug, fnData.object())

    if outlinerColour and useOutlinerColour:
        outlinerColour = list(outlinerColour)
        # the outliner colour needs to be float3 not float4 but MColor is a float4
        if len(outlinerColour) > 3:
            outlinerColour = outlinerColour[:-1]

        useOutliner = dependNode.findPlug("useOutlinerColor", False)
        modifier.newPlugValueBool(useOutliner, True)
        outlinerColorPlug = dependNode.findPlug("outlinerColor", False)
        fnData = om2.MFnNumericData(outlinerColorPlug.asMObject()).setData(
            outlinerColour
        )
        modifier.newPlugValue(outlinerColorPlug, fnData.object())

    if mod is None:
        modifier.doIt()
    return modifier


def getNodeColourData(node):
    """
    :param node: The maya node mobject that you want to get the override colour from

    :type node: MObject
    :return: {"overrideEnabled": bool,
            "overrideColorRGB": plugs.getAttr(plug),
            "overrideRGBColors": plugs.getAttr(overrideRGBColors)}

    :rtype: dict
    """

    dependNode = om2.MFnDagNode(om2.MFnDagNode(node).getPath())
    plug = dependNode.findPlug("overrideColorRGB", False)
    enabledPlug = dependNode.findPlug("overrideEnabled", False)
    overrideRGBColors = dependNode.findPlug("overrideRGBColors", False)
    useOutliner = dependNode.findPlug("useOutlinerColor", False)
    return {
        "overrideEnabled": enabledPlug.asBool(),
        "overrideColorRGB": om2.MColor(plugs.getPlugValue(plug)),
        "overrideRGBColors": overrideRGBColors.asBool(),
        "useOutlinerColor": useOutliner.asBool(),
        "outlinerColor": om2.MColor(
            plugs.getPlugValue(dependNode.findPlug("outlinerColor", False))
        ),
    }


def createDagNode(name, nodeType, parent=None, modifier=None, apply=True):
    """Creates a new dag node and if there's a parent specified then parent the new node

    :param name: The new name of the created node
    :type name: str
    :param nodeType: The node type to create
    :type nodeType: str
    :param parent: The node the parent the new node to, if the parent is none or MObject.kNullObj then it will parent \
    to the world, defaults to world
    :type parent: MObject or MObject.kNullObj
    :return: The newly create nodes mobject
    :rtype: MObject
    """
    if not general.isSafeName(name):
        raise NameError("Invalid name for node: {}".format(name))

    if (
        parent is None
        or parent.isNull()
        or parent.apiType() in (om2.MFn.kInvalid, om2.MFn.kWorld)
    ):
        parent = om2.MObject.kNullObj

    mod = modifier or om2.MDagModifier()
    node = mod.createNode(nodeType, parent)
    mod.renameNode(node, name)
    if modifier is None or apply:
        mod.doIt()
    return node


def createDGNode(name, nodeType, mod=None, apply=True):
    """Creates and dependency graph node and returns the nodes mobject

    :param name: The new name of the node
    :type name: str
    :param nodeType: the node type to create
    :type nodeType: str
    :return: The mobject of the newly created node
    :rtype: :class:`om2.MObject`
    """
    modifier = mod or om2.MDGModifier()
    node = modifier.createNode(nodeType)
    modifier.renameNode(node, name)
    if mod is None or apply:
        modifier.doIt()
    return node


def lockNode(mobject, state=True, modifier=None):
    """Set the lock state of the node

    :param mobject: the node mobject to set the lock state on
    :type mobject: MObject
    :param state: the lock state for the node
    :type state: bool
    """
    if om2.MFnDependencyNode(mobject).isLocked != state:
        mod = modifier or om2.MDGModifier()
        mod.setNodeLockState(mobject, state)
        if modifier is None:
            mod.doIt()
        return mod


@contextlib.contextmanager
def lockNodeContext(mobject, state):
    fn = om2.MFnDependencyNode(mobject)
    if fn.isLocked != state:
        originalState = fn.isLocked
        fn.isLocked = state
        try:
            yield
        finally:
            fn.isLocked = originalState
    else:
        yield


def unlockConnectedAttributes(mobject):
    """Unlocks all connected attributes to this node

    :param mobject: MObject representing the DG node
    :type mobject: MObject
    """
    for thisNodeP, otherNodeP in iterConnections(
        mobject, source=True, destination=True
    ):
        if thisNodeP.isLocked:
            thisNodeP.isLocked = False


def unlockedAndDisconnectConnectedAttributes(mobject):
    """Unlcoks and disocnnects all attributes on the given node

    :param mobject: MObject respresenting the DG node
    :type mobject: MObject
    """
    for thisNodeP, otherNodeP in iterConnections(
        mobject, source=False, destination=True
    ):
        plugs.disconnectPlug(thisNodeP)


def containerFromNode(mobj):
    """Finds and returns the AssetContainer mobject from the give node.

    :param mobj: The om2.MObject representing the node to filter.
    :type mobj: om2.MObject
    :return: The container MObject found from the mobject else None
    :rtype: om2.MObject or None
    """
    fn = om2.MFnDependencyNode(mobj)
    messagePlug = fn.findPlug("message", False)
    for dest in messagePlug.destinations():
        node = dest.node()
        if node.hasFn(om2.MFn.kHyperLayout):
            continue
        hyperLayoutMsg = fn.setObject(dest.node()).findPlug("message", False)
        for possibleObj in hyperLayoutMsg.destinations():
            node = possibleObj.node()
            if node.hasFn(om2.MFn.kContainer):
                return node


def childPathAtIndex(path, index):
    """From the given MDagPath return a new MDagPath for the child node at the given index.

    :type path: maya.api.OpenMaya.MDagPath
    :type index: int
    :return: MDagPath, this path's child at the given index
    """

    existingChildCount = path.childCount()
    if existingChildCount < 1:
        return None
    if index < 0:
        index = path.childCount() - abs(index)
    copy = om2.MDagPath(path)
    copy.push(path.child(index))
    return copy


def childPaths(path):
    """Returns all the MDagPaths that are a child of path.

    :param path:
    :type path: maya.api.OpenMaya.MDagPath
    :return: child MDagPaths which have path as parent
    :rtype: list[maya.api.OpenMaya.MDagPath]
    """
    outPaths = [childPathAtIndex(path, i) for i in range(path.childCount())]
    return outPaths


def childPathsByFn(path, fn):
    """Get all children below path supporting the given MFn.type

    :param path: MDagpath
    :param fn: member of MFn
    :return: list(MDagPath), all matched paths below this path
    """
    return [p for p in childPaths(path) if p.hasFn(fn)]


def iterShapes(path, filterTypes=()):
    """Generator function which all the shape dagpaths directly below this dagpath

    :param path: The MDagPath to search
    :return: list(MDagPath)
    """
    for i in range(path.numberOfShapesDirectlyBelow()):
        dagPath = om2.MDagPath(path)
        dagPath.extendToShape(i)
        if not filterTypes or dagPath.apiType() in filterTypes:
            yield dagPath


def shapes(path, filterTypes=()):
    """
    :Depreciated Use IterShapes()
    """
    return list(iterShapes(path, filterTypes))


def shapeAtIndex(path, index):
    """Finds and returns the shape DagPath under the specified path for the index

    :param path: the MDagPath to the parent node that you wish to search under
    :type path: om2.MDagPath
    :param index: the shape index
    :type index: int
    :rtype: om2.MDagPath or None
    """
    if index in range(path.numberOfShapesDirectlyBelow()):
        return om2.MDagPath(path).extendToShape(index)


def childTransforms(path):
    """Returns all the child transform from the given DagPath

    :type path: om2.MDagPath
    :return: list(MDagPath) to all transforms below path
    """
    return childPathsByFn(path, om2.MFn.kTransform)


def setParent(child, newParent, maintainOffset=False, mod=None, apply=True):
    """Sets the parent for the given child

    :param child: the child node which will have its parent changed
    :type child: om2.MObject
    :param newParent: The new parent for the child
    :type newParent: om2.MObject
    :param maintainOffset: if True then the current transformation is maintained relative to the new parent
    :type maintainOffset: bool
    :param mod: The MDagModifier to add to, if none it will create one
    :type mod: om2.MDagModifier
    :param apply: Apply the modifier immediately if true, false otherwise
    :type apply: bool
    :rtype: om2.MDagModifier
    """

    newParent = newParent or om2.MObject.kNullObj
    if child == newParent:
        return
    # convert parentMObject to path
    currentParent = getParent(child) or om2.MObject.kNullObj
    if currentParent and currentParent == newParent:
        return

    mod = mod or om2.MDagModifier()
    if not maintainOffset:
        mod.reparentNode(child, newParent)
        if apply:
            mod.doIt()
        return mod
    flags = ""
    _parentPath = ""
    if newParent == om2.MObject.kNullObj:
        flags += " -world"
    else:
        _parentPath = nameFromMObject(newParent)

    mod.commandToExecute(
        "parent -a {} {} {}".format(flags, nameFromMObject(child), _parentPath)
    )
    if apply:
        mod.doIt()
    return mod


@contextlib.contextmanager
def childContext(parent):
    children = []
    for child in iterChildren(parent, False, (om2.MFn.kTransform, om2.MFn.kJoint)):
        setParent(child, om2.MObject.kNullObj)
        children.append(child)
    yield
    for i in iter(children):
        setParent(i, parent, True)


def hasParent(mobject):
    """Determines if the given MObject has a mobject

    :param mobject: the MObject node to check
    :type mobject: MObject
    :rtype: bool
    """
    parent = getParent(mobject)
    if parent is None or parent.isNull():
        return False
    return True


def rename(mobject, newName, modifier=None, apply=True):
    """Renames the given mobject node, this is undoable.

    :param mobject: the node to rename
    :type mobject: om2.MObject
    :param newName: the new unique name for the node
    :type newName: str
    :param modifier: if you pass a instance then the rename will be added to the queue then \
    returned otherwise a new  instance will be created and immediately executed.
    :type modifier: om2.MDGModifier or None
    :param apply: Apply the modifier immediately if true, false otherwise
    :type apply: bool

    .. note::
        If you pass a MDGModifier then you should call doIt() after calling this function

    """
    if not general.isSafeName(newName):
        raise NameError("Invalid name for node: {}".format(newName))
    dag = modifier or om2.MDGModifier()
    dag.renameNode(mobject, newName)
    # if a modifier is passed into the function then let the user deal with DoIt
    if modifier is None and apply:
        dag.doIt()
    return dag


def parentPath(path):
    """Returns the parent nodes MDagPath

    :param path: child DagPath
    :type path: MDagpath
    :return: MDagPath, parent of path or None if path is in the scene root.
    """
    parent = om2.MDagPath(path)
    parent.pop(1)
    if parent.length() == 0:  # ignore world !
        return
    return parent


def isValidMDagPath(dagPath):
    """Determines if the given MDagPath is valid

    :param dagPath: MDagPath
    :return: bool
    """
    return dagPath.isValid() and dagPath.fullPathName()


def iterParents(mobject):
    parent = getParent(mobject=mobject)
    while parent is not None:
        yield parent
        parent = getParent(parent)


def isSceneRoot(node):
    fn = om2.MFnDagNode(node)
    return fn.object().hasFn(om2.MFn.kDagNode) and fn.name() == "world"


def isUnderSceneRoot(node):
    """Determines if the specified node is currently parented to world.

    :param node: The maya Dag MObject
    :type node: :class:`om2.MObject`
    :rtype: bool
    """
    fn = om2.MFnDagNode(node)
    par = fn.parent(0)
    return isSceneRoot(par)


def iterChildren(mObject, recursive=False, filter=None):
    """Generator function that can recursive iterate over the children of the given MObject.

    :param mObject: The MObject to traverse must be a MObject that points to a transform
    :type mObject: MObject
    :param recursive: Whether to do a recursive search
    :type recursive: bool
    :param filter: tuple(om.MFn) or None, the node type to find, can be either 'all' for returning everything or a \
    om.MFn type constant does not include shapes
    :type filter: tuple or None
    :return: om.MObject
    """
    dagNode = om2.MDagPath.getAPathTo(mObject)
    childCount = dagNode.childCount()
    if not childCount:
        return
    filter = filter or ()

    for index in range(childCount):
        childObj = dagNode.child(index)
        if not filter or childObj.apiType() in filter:
            yield childObj
            if recursive:
                for x in iterChildren(childObj, recursive, filter):
                    yield x


def breadthFirstSearchDag(node, filter=None):
    ns = tuple(iterChildren(node, False, filter=filter))
    if not ns:
        return
    yield ns
    for i in ns:
        for t in breadthFirstSearchDag(i):
            yield t


def getChildren(mObject, recursive=False, filter=(om2.MFn.kTransform,)):
    """This function finds and returns all children mobjects under the given transform, if recursive then including
     sub children.

    :param mObject: om.MObject, the mObject of the transform to search under
    :param recursive: bool
    :param filter: tuple(om.MFn.kTransform, the node type to filter by
    :return: list(MFnDagNode)
    """
    return tuple(iterChildren(mObject, recursive, filter))


def iterAttributes(node, skip=None, includeAttributes=()):
    skip = skip or ()
    dep = om2.MFnDependencyNode(node)
    for idx in range(dep.attributeCount()):
        attr = dep.attribute(idx)
        plug = om2.MPlug(node, attr)
        name = plug.partialName(
            includeNodeName=False,
            includeNonMandatoryIndices=True,
            includeInstancedIndices=True,
            useAlias=False,
            useFullAttributePath=True,
            useLongNames=True,
        )
        if any(i in name for i in skip):
            continue
        elif includeAttributes and not any(i in name for i in includeAttributes):
            continue
        elif plug.isElement or plug.isChild:
            continue
        yield plug
        for child in plugs.iterChildren(plug):
            yield child


def iterExtraAttributes(node, skip=None, filteredTypes=None, includeAttributes=None):
    """Generator function to iterate over all extra plugs(dynamic) of a given node.

    :param node: The DGNode or DagNode to iterate
    :type node: om2.MObject
    :param filteredTypes:
    :type filteredTypes: tuple(attrtypes.kType)
    :return: Generator function with each item equaling a om2.MPlug
    :rtype: iterable[om2.MPlug]
    """
    skip = skip or ()
    filteredTypes = filteredTypes or ()
    includeAttributes = includeAttributes or ()
    dep = om2.MFnDependencyNode(node)
    for idx in range(dep.attributeCount()):
        attr = dep.attribute(idx)
        plug = om2.MPlug(node, attr)
        if not plug.isDynamic:
            continue
        name = plug.partialName(
            includeNodeName=False,
            includeNonMandatoryIndices=False,
            includeInstancedIndices=False,
            useAlias=False,
            useFullAttributePath=False,
            useLongNames=False,
        )
        if skip and name.startswith(skip):
            continue
        elif includeAttributes and not any(i in name for i in includeAttributes):
            continue
        elif not filteredTypes or plugs.plugType(plug) in filteredTypes:
            yield plug


def iterConnections(node, source=True, destination=True):
    """Returns a generator function containing a tuple of MPlugs

    :param node: The node to search
    :type node: om2.MObject
    :param source: If true then all upstream connections are returned
    :type source: bool
    :param destination: If true all downstream connections are returned
    :type destination: bool
    :return: tuple of om2.MPlug instances, the first element is the connected MPlug of the given node(``node``) \
    The second element is the connected MPlug from the other node.
    :rtype: Generator(tuple(om2.MPlug, om2.MPlug))
    """
    dep = om2.MFnDependencyNode(node)
    for pl in iter(dep.getConnections()):
        if source and pl.isSource:
            for i in iter(pl.destinations()):
                yield pl, i
        if destination and pl.isDestination:
            yield pl, pl.source()


def iterKeyablePlugs(node):
    dep = om2.MFnDependencyNode(node)
    for i in range(dep.attributeCount()):
        attr = dep.attribute(i)
        plug = om2.MPlug(node, attr)
        if plug.isKeyable:
            yield plug


def iterChannelBoxPlugs(node):
    dep = om2.MFnDependencyNode(node)
    for i in range(dep.attributeCount()):
        attr = dep.attribute(i)
        plug = om2.MPlug(node, attr)
        if plug.isKeyable and plug.isChannelBox:
            yield plug


def getRoots(nodes):
    roots = set()
    for node in nodes:
        root = getRoot(node)
        if root:
            roots.add(root)
    return list(roots)


def getRoot(mobject):
    """Traversals the objects parent until the root node is found and returns the MObject

    :param mobject: MObject
    :return: MObject
    """
    current = mobject
    for node in iterParents(mobject):
        if node is None:
            return current
        current = node
    return current


def getParent(mobject):
    """Returns the parent MFnDagNode if it has a parent else None

    :param mobject: MObject
    :return: MObject or None
    """
    if mobject.hasFn(om2.MFn.kDagNode):
        dagpath = om2.MDagPath.getAPathTo(mobject)
        if dagpath.node().apiType() == om2.MFn.kWorld:
            return None
        dagNode = om2.MFnDagNode(dagpath).parent(0)
        if dagNode.apiType() == om2.MFn.kWorld:
            return None
        return dagNode


def isValidMObject(node):
    mo = om2.MObjectHandle(node)
    return mo.isValid() and mo.isAlive()


def delete(node):
    """Delete the given nodes

    :param node:
    """
    if not isValidMObject(node):
        return
    lockNode(node, False)
    unlockedAndDisconnectConnectedAttributes(node)

    mod = om2.MDagModifier()
    mod.deleteNode(node)
    mod.doIt()


def removeUnknownNodes():
    unknownNodes = cmds.ls(type="unknown")
    try:
        nodesToDelete = []
        for node in unknownNodes:
            if cmds.referenceQuery(node, isNodeReferenced=True):
                continue
            cmds.lockNode(node, lock=False)
            nodesToDelete.append(node)
        if nodesToDelete:
            cmds.delete(nodesToDelete)
    except RuntimeError:
        logger.error("Failed to remove Unknown Nodes", exc_info=True)
    return True


if int(om1.MGlobal.mayaVersion()) < 2020:

    def getOffsetMatrix(
        startObj, endObj, space=om2.MSpace.kWorld, ctx=om2.MDGContext.kNormal
    ):
        """Returns The offset matrix between two objects.

        :param startObj: Start Transform MObject.
        :type startObj: :class:`om2.MObject`
        :param endObj: End Transform MObject.
        :type endObj: :class:`om2.MObject`
        :param space: Coordinate space to use.
        :type space: om2.MSpace.kSpace
        :param ctx: The MDGContext to use. ie. the current frame.
        :type ctx: :class:`om2.MDGContext`
        :return: The resulting Offset MMatrix.
        :rtype: :class:`om2.MMatrix`
        """
        if space == om2.MSpace.kWorld:
            start = getWorldMatrix(startObj, ctx)
            end = getWorldMatrix(endObj, ctx)
        else:
            start = getMatrix(startObj, ctx)
            end = getMatrix(endObj, ctx)
        mOutputMatrix = end * start.inverse()
        return mOutputMatrix

else:

    def getOffsetMatrix(
        startObj, endObj, space=om2.MSpace.kWorld, ctx=om2.MDGContext.kNormal
    ):
        """Returns The offset matrix between two objects.

        :param startObj: Start Transform MObject.
        :type startObj: :class:`om2.MObject`
        :param endObj: End Transform MObject.
        :type endObj: :class:`om2.MObject`
        :param space: Coordinate space to use.
        :type space: om2.MSpace.kSpace
        :param ctx: The MDGContext to use. ie. the current frame.
        :type ctx: :class:`om2.MDGContext`
        :return: The resulting Offset MMatrix.
        :rtype: :class:`om2.MMatrix`
        """
        if space == om2.MSpace.kWorld:
            start = getWorldMatrix(startObj, ctx)
            end = getWorldMatrix(endObj, ctx)
        else:
            start = getMatrix(startObj, ctx)
            end = getMatrix(endObj, ctx)
        mOutputMatrix = (
            end
            * start.inverse()
            * plugs.getPlugValue(
                om2.MFnDependencyNode(startObj).findPlug("offsetParentMatrix", False),
                ctx,
            ).inverse()
        )
        return mOutputMatrix


def getMatrix(mobject, ctx=om2.MDGContext.kNormal):
    """Returns the MMatrix of the given mobject

    :param mobject: MObject
    :type mobject: :class:`om2.MObject`
    :param ctx: The MDGContext to use. ie. the current frame.
    :type ctx: :class:`om2.MDGContext`
    :return: :class:`om2.MMatrix`
    """
    return om2.MFnMatrixData(
        om2.MFnDependencyNode(mobject).findPlug("matrix", False).asMObject(ctx)
    ).matrix()


def worldMatrixPlug(mobject):
    wm = om2.MFnDependencyNode(mobject).findPlug("worldMatrix", False)
    return wm.elementByLogicalIndex(0)


def getWorldMatrix(mobject, ctx=om2.MDGContext.kNormal):
    """Returns the worldMatrix value as an MMatrix.

    :param mobject: the MObject that points the dagNode
    :type mobject: :class:`om2.MObject`
    :param ctx: The MDGContext to use. ie. the current frame.
    :type ctx: :class:`om2.MDGContext`
    :return: MMatrix
    """
    return om2.MFnMatrixData(worldMatrixPlug(mobject).asMObject(ctx)).matrix()


def decomposeMatrix(matrix, rotationOrder, space=om2.MSpace.kWorld):
    transformMat = om2.MTransformationMatrix(matrix)
    transformMat.reorderRotation(rotationOrder)
    rotation = transformMat.rotation(asQuaternion=(space == om2.MSpace.kWorld))
    return transformMat.translation(space), rotation, transformMat.scale(space)


def parentInverseMatrixPlug(mobject):
    wm = om2.MFnDependencyNode(mobject).findPlug("parentInverseMatrix", False)
    return wm.elementByLogicalIndex(0)


def getWorldInverseMatrix(mobject, ctx=om2.MDGContext.kNormal):
    """Returns the world inverse matrix of the given MObject

    :param mobject: MObject
    :type mobject: :class:`om2.MObject`
    :param ctx: The MDGContext to use. ie. the current frame.
    :type ctx: :class:`om2.MDGContext`
    :return: MMatrix
    """
    wm = om2.MFnDependencyNode(mobject).findPlug("worldInverseMatrix", False)
    matplug = wm.elementByLogicalIndex(0)
    return om2.MFnMatrixData(matplug.asMObject(ctx)).matrix()


def getParentMatrix(mobject, ctx=om2.MDGContext.kNormal):
    """Returns the parent matrix of the given MObject

    :param mobject: MObject
    :type mobject: :class:`om2.MObject`
    :param ctx: The MDGContext to use. ie. the current frame.
    :type ctx: :class:`om2.MDGContext`
    :return: MMatrix
    """
    wm = om2.MFnDependencyNode(mobject).findPlug("parentMatrix", False)
    matplug = wm.elementByLogicalIndex(0)
    return om2.MFnMatrixData(matplug.asMObject(ctx)).matrix()


def getParentInverseMatrix(mobject, ctx=om2.MDGContext.kNormal):
    """Returns the parent inverse matrix from the MObject

    :param mobject: MObject
    :type mobject: :class:`om2.MObject`
    :param ctx: The MDGContext to use. ie. the current frame.
    :type ctx: :class:`om2.MDGContext`
    :return: MMatrix
    """
    return om2.MFnMatrixData(parentInverseMatrixPlug(mobject).asMObject(ctx)).matrix()


def hasAttribute(node, name):
    """Searches the node for a give a attribute name and returns True or False

    :param node: MObject, the nodes MObject
    :param name: str, the attribute name to find
    :return: bool
    """
    try:
        return plugs.asMPlug(".".join((nameFromMObject(node), name))) is not None
    except RuntimeError:
        return False


def setMatrix(mobject, matrix, space=om2.MSpace.kTransform):
    """Sets the objects matrix using om2.MTransform.

    :param mobject: The transform MObject to modify
    :type mobject: :class:`om2.MObject`
    :param matrix: The maya MMatrix to set
    :type matrix: :class:`om2.MMatrix`
    :param space: The coordinate space to set the matrix by
    :type space: :class:`om2.MSpace.kWorld`
    """
    dag = om2.MFnDagNode(mobject)
    transform = om2.MFnTransform(dag.getPath())
    tMtx = om2.MTransformationMatrix(matrix)
    transform.setTranslation(tMtx.translation(space), space)
    transform.setRotation(tMtx.rotation(asQuaternion=True), space)
    transform.setScale(tMtx.scale(space))


def setTranslation(obj, position, space=None, sceneUnits=False):
    path = om2.MFnDagNode(obj).getPath()
    space = space or om2.MSpace.kTransform
    trans = om2.MFnTransform(path)
    if sceneUnits:
        position = mayamath.convertFromSceneUnits(position)
    trans.setTranslation(position, space)
    return True


def getTranslation(obj, space=None, sceneUnits=False):
    space = space or om2.MSpace.kTransform
    path = om2.MFnDagNode(obj).getPath()
    trans = om2.MFnTransform(path)
    translation = trans.translation(space)
    if sceneUnits:
        return mayamath.convertToSceneUnits(translation)
    return translation


def cvPositions(shape, space=None):
    space = space or om2.MSpace.kObject
    curve = om2.MFnNurbsCurve(shape)
    return curve.cvPositions(space)


def setCurvePositions(shape, points, space=None):
    space = space or om2.MSpace.kObject
    curve = om2.MFnNurbsCurve(shape)
    if len(points) != curve.numCVs:
        raise ValueError(
            "Mismatched current curves cv count and the length of points to modify"
        )
    curve.setCVPositions(points, space)


def setRotation(node, rotation, space=om2.MSpace.kTransform):
    path = om2.MFnDagNode(node).getPath()
    trans = om2.MFnTransform(path)
    if isinstance(rotation, (list, tuple)):
        rotation = om2.MEulerRotation(
            [om2.MAngle(i, om2.MAngle.kDegrees).asRadians() for i in rotation]
        )
    trans.setRotation(rotation, space)


def getRotation(obj, space, asQuaternion=False):
    """
    :param obj:
    :type obj: om2.MObject or om2.MDagPath
    :param space:
    :type space:
    :param asQuaternion:
    :type asQuaternion:
    :return:
    :rtype:
    """
    space = space or om2.MSpace.kTransform
    trans = om2.MFnTransform(obj)

    return trans.rotation(space, asQuaternion=asQuaternion)


def setCompoundAsProxy(compoundPlug, sourcePlug):
    # turn all the child plugs to proxy, since maya doesn't support doing this
    # at the compound level, then do the connection between the matching children
    for childIdx in range(compoundPlug.numChildren()):
        childPlug = compoundPlug.child(childIdx)
        attr = childPlug.attribute()
        # turn the proxy state on and do the connection
        plugs.getPlugFn(attr)(attr).isProxyAttribute = True
        plugs.connectPlugs(sourcePlug.child(childIdx), childPlug)


def addProxyAttribute(node, sourcePlug, **kwargs):
    """This method adds a proxy attribute to the specified node.

    :param node: The node on which the proxy attribute will be added.
    :type node: str
    :param sourcePlug: The plug from which the proxy attribute will be connected.
    :type sourcePlug: str
    :param kwargs: Additional keyword arguments.
    :type kwargs: dict
    :return: The added attribute.
    :rtype: om2.MObject

    The `kwargs` parameter should contain the following keys:
    - "Type" (attrtypes.kMFnCompoundAttribute): The type of attribute to add.
    - "children" (dict): A dictionary containing the child attributes for a compound attribute.

    Example usage::

        node = "myNode"
        sourcePlug = "myNode.sourceAttr"
        kwargs = {
            "Type": attrtypes.kMFnCompoundAttribute,
            "children": {
                "attr1": {
                    "Type": attrtypes.kMFnDoubleAttribute,
                    ...
                },
                ...
            },
            ...
        }

        addedAttr = addProxyAttribute(node, sourcePlug, **kwargs)
    """
    # numeric compound attributes ie. double3 isn't supported via addCompound as it's an
    # actual maya type mfn.kAttributeDouble3 which means we don't create it via MFnCompoundAttribute.
    # therefore we manage that for via the kwargs dict.
    if kwargs["Type"] == attrtypes.kMFnCompoundAttribute:
        attr1 = addCompoundAttribute(node, attrMap=kwargs["children"], **kwargs)
        attr1.isProxyAttribute = True
        attrPlug = om2.MPlug(node, attr1.object())
        setCompoundAsProxy(attrPlug, sourcePlug)

    else:
        attr1 = addAttribute(node, **kwargs)
        proxyPlug = om2.MPlug(node, attr1.object())
        # is it's an attribute we're adding which is a special type like double3
        # then ignore connecting the compound as maya proxy attributes require the children
        # not the parent to be connected.
        if proxyPlug.isCompound:
            attr1.isProxyAttribute = True
            setCompoundAsProxy(proxyPlug, sourcePlug)
        else:
            attr1.isProxyAttribute = True
            plugs.connectPlugs(sourcePlug, proxyPlug)

    return attr1


def addCompoundAttribute(
    node,
    longName,
    shortName=None,
    attrMap=None,
    isArray=False,
    apply=True,
    mod=None,
    **kwargs
):
    """Add compound attribute.

    :param node: the node to add the compound attribute too.
    :type node: om2.MObject
    :param longName: The compound longName
    :type longName: str
    :param shortName: The compound shortName
    :type shortName: str
    :param isArray: Whether
    :type isArray: bool
    :param apply: If True then the value we be set on the Plug instance by calling doIt on the modifier.
    :type apply: bool
    :param mod: Apply the modifier instantly or leave it to the caller.
    :type mod: :class:`om2.MDGModifier`
    :param attrMap: [{"name":str, "type": attrtypes.kType, "isArray": bool}]
    :type attrMap: list(dict())
    :return: the MObject attached to the compound attribute
    :rtype: :class:`om2.MFnCompoundAttribute`

    .. code-block:: python

        attrMap = [{"name":"something", "Type": attrtypes.kMFnMessageAttribute, "isArray": False}]
        print attrMap
        # result <OpenMaya.MObject object at 0x00000000678CA790> #

    """
    exists = False
    modifier = mod or om2.MDGModifier()
    compObj = om2.MObject.kNullObj
    shortName = shortName or longName
    if hasAttribute(node, longName):
        exists = True
        compound = om2.MFnCompoundAttribute(
            plugs.asMPlug(".".join((nameFromMObject(node), longName))).attribute()
        )
    else:
        compound = om2.MFnCompoundAttribute()
        compObj = compound.create(longName, shortName)
        compound.array = isArray
    for attrData in attrMap:
        if not attrData or exists:
            continue
        if attrData["Type"] == attrtypes.kMFnCompoundAttribute:
            # When create child compounds maya only wants the root attribute to
            # created. All children will be created because we execute the addChild()
            child = addCompoundAttribute(
                node,
                attrData["name"],
                attrMap=attrData.get("children", []),
                apply=False,
                mod=modifier,
                **attrData
            )
        else:
            try:
                child = addAttribute(
                    node,
                    longName=attrData["name"],
                    attrType=attrData["Type"],
                    mod=modifier,
                    apply=exists,
                    **attrData
                )
            except AttributeAlreadyExists:
                continue
            except RuntimeError:
                raise
        if child is not None:
            attrObj = child.object()
            compound.addChild(attrObj)
    if apply and not exists:
        modifier.addAttribute(node, compObj)
        modifier.doIt()
        kwargs["children"] = attrMap
        plugs.setPlugInfoFromDict(om2.MPlug(node, compObj), **kwargs)

    return compound


def addAttributesFromList(node, data):
    """Creates an attribute on the node given a list(dict) of attribute data::

        [{
            "channelBox": true,
            "default": 3,
            "isDynamic": true,
            "keyable": false,
            "locked": false,
            "max": 9999,
            "min": 1,
            "name": "jointCount",
            "softMax": null,
            "softMin": null,
            "Type": 2,
            "value": 3
            "isArray": True
        }]

    :param data: The serialized form of the attribute
    :type data: dict
    :return: A list of create MPlugs
    :rtype: list(om2.MPlug)
    """
    created = []
    for attrData in iter(data):
        Type = attrData["Type"]
        default = attrData["default"]
        value = attrData["value"]
        name = attrData["name"]
        shortName = attrData.get("shortName", name)

        if Type == attrtypes.kMFnDataString:
            default = om2.MFnStringData().create(default)
        elif Type == attrtypes.kMFnDataMatrix:
            default = om2.MFnMatrixData().create(om2.MMatrix(default))
        elif Type == attrtypes.kMFnUnitAttributeAngle:
            default = om2.MAngle(default, om2.MAngle.kDegrees)
            value = om2.MAngle(value, om2.MAngle.kDegrees)

        plug = om2.MPlug(
            node,
            addAttribute(
                node,
                name,
                shortName,
                Type,
                isArray=data.get("array", False),
                apply=True,
            ),
        )
        plugs.setPlugDefault(plug, default)

        plug.isChannelBox = attrData["value"]
        plug.isKeyable = attrData["keyable"]
        plugs.setLockState(plug, attrData["locked"])
        plugs.setMin(plug, attrData["min"])
        plugs.setMax(plug, attrData["max"])
        plugs.setSoftMin(plug, attrData["softMin"])
        plugs.setSoftMax(plug, attrData["softMax"])
        if not plug.attribute().hasFn(om2.MFn.kMessageAttribute):
            plugs.setPlugValue(plug, value)
        created.append(plug)
    return created


def addAttribute(
    node,
    longName,
    shortName=None,
    attrType=attrtypes.kMFnNumericDouble,
    isArray=False,
    apply=True,
    mod=None,
    **kwargs
):
    """This function uses the api to create attributes on the given node, currently WIP but currently works for
    string,int, float, bool, message, matrix. if the attribute exists a ValueError will be raised.

    :param node: MObject
    :param longName: The long name for the attribute.
    :type longName: str
    :param shortName: str, the shortName for the attribute.
    :type shortName: str
    :param attrType: attribute Type, attrtypes constants.
    :type attrType: attrtypes.kConstant
    :param isArray: Is the attribute an array?.
    :type isArray: bool
    :param mod: The Undo Modifier to use.
    :type mod: :class:`om2.MDGModifier`
    :param apply: if False the attribute will be immediately created on the node else just \
    return the attribute instance.

    :type apply: bool

    :keyword channelBox(bool): Should the attribute be displayed in the Channel Box?.
    :keyword keyable(bool): Can keys be set on the attribute?.
    :keyword default: The default value for the attribute.
    :keyword value: The value for the attribute to use.
    :keyword enums: List of fields which this attribute will have, only valid for EnumAttribute.
    :keyword storable(bool): Should attr value be stored when written to file?.
    :keyword writable(bool): Is the attribute writable?.
    :keyword connectable(bool): Can connections be made to the attribute?.
    :keyword min(int,float): Returns the attribute's hard minimum value(s).
    :keyword max(int,float): Returns the attribute's hard maximum value(s).
    :keyword softMin(int,float): Returns the attribute's soft minimum value.
    :keyword softMax(int,float): Returns the attribute's soft maximum value.
    :keyword locked(bool): True if plug is locked against changes.

    :rtype: :class:`om2.MFnAttribute`

    .. code-block:: python

        # message attribute
        attrMobj = addAttribute(myNode, "testMsg", "testMsg", attrType=attrtypes.kMFnMessageAttribute,
                                 isArray=False, apply=True)
        # double angle
        attrMobj = addAttribute(myNode, "myAngle", "myAngle", attrType=attrtypes.kMFnUnitAttributeAngle,
                                 keyable=True, channelBox=False)
        # double angle
        attrMobj = addAttribute(myNode, "myEnum", "myEnum", attrType=attrtypes.kMFnkEnumAttribute,
                                 keyable=True, channelBox=True, enums=["one", "two", "three"])

    """
    # internal note: we've duplicated value setting here to avoid the extra cost of setPlugInfoFromDict
    # which requires a valid plug which is only possible if apply=True, so this softens the blow at the cost
    # of code duplication
    if hasAttribute(node, longName):
        raise AttributeAlreadyExists(
            "Node -> '{}' already has attribute -> '{}'".format(
                nameFromMObject(node), longName
            )
        )
    default = kwargs.get("default")
    channelBox = kwargs.get("channelBox")
    keyable = kwargs.get("keyable")
    shortName = shortName or longName
    numericClass, dataConstant = attrtypes.numericTypeToMayaFnType(attrType)

    if numericClass is not None:
        attr = numericClass()
        if attrType == attrtypes.kMFnNumericAddr:
            aobj = attr.createAddr(longName, shortName)
        elif attrType == attrtypes.kMFnNumeric3Float:
            aobj = attr.createPoint(longName, shortName)
        else:
            aobj = attr.create(longName, shortName, dataConstant)

    elif attrType == attrtypes.kMFnkEnumAttribute:
        attr = om2.MFnEnumAttribute()
        aobj = attr.create(longName, shortName)
        fields = kwargs.get("enums", [])
        # maya creates an invalid enumAttribute if when creating we don't create any fields
        # so this just safeguards to a single value
        if not fields:
            fields = ["None"]
        for index in range(len(fields)):
            attr.addField(fields[index], index)

    elif attrType == attrtypes.kMFnCompoundAttribute:
        attr = om2.MFnCompoundAttribute()
        aobj = attr.create(longName, shortName)
    elif attrType == attrtypes.kMFnMessageAttribute:
        attr = om2.MFnMessageAttribute()
        aobj = attr.create(longName, shortName)
    elif attrType == attrtypes.kMFnDataString:
        attr = om2.MFnTypedAttribute()
        stringData = om2.MFnStringData().create("")
        aobj = attr.create(longName, shortName, om2.MFnData.kString, stringData)
    elif attrType == attrtypes.kMFnUnitAttributeDistance:
        attr = om2.MFnUnitAttribute()
        aobj = attr.create(longName, shortName, om2.MDistance())
    elif attrType == attrtypes.kMFnUnitAttributeAngle:
        attr = om2.MFnUnitAttribute()
        aobj = attr.create(longName, shortName, om2.MAngle())
    elif attrType == attrtypes.kMFnUnitAttributeTime:
        attr = om2.MFnUnitAttribute()
        aobj = attr.create(longName, shortName, om2.MTime())
    elif attrType == attrtypes.kMFnDataMatrix:
        attr = om2.MFnMatrixAttribute()
        aobj = attr.create(longName, shortName)
    # elif attrType == attrtypes.kMFnDataFloatArray:
    #     attr = om2.MFnFloatArray()
    #     aobj = attr.create(longName, shortName)
    elif attrType == attrtypes.kMFnDataDoubleArray:
        data = om2.MFnDoubleArrayData().create(om2.MDoubleArray())
        attr = om2.MFnTypedAttribute()
        aobj = attr.create(longName, shortName, om2.MFnData.kDoubleArray, data)
    elif attrType == attrtypes.kMFnDataIntArray:
        data = om2.MFnIntArrayData().create(om2.MIntArray())
        attr = om2.MFnTypedAttribute()
        aobj = attr.create(longName, shortName, om2.MFnData.kIntArray, data)
    elif attrType == attrtypes.kMFnDataPointArray:
        data = om2.MFnPointArrayData().create(om2.MPointArray())
        attr = om2.MFnTypedAttribute()
        aobj = attr.create(longName, shortName, om2.MFnData.kPointArray, data)
    elif attrType == attrtypes.kMFnDataVectorArray:
        data = om2.MFnVectorArrayData().create(om2.MVectorArray())
        attr = om2.MFnTypedAttribute()
        aobj = attr.create(longName, shortName, om2.MFnData.kVectorArray, data)
    elif attrType == attrtypes.kMFnDataStringArray:
        data = om2.MFnStringArrayData().create()
        attr = om2.MFnTypedAttribute()
        aobj = attr.create(longName, shortName, om2.MFnData.kStringArray, data)
    elif attrType == attrtypes.kMFnDataMatrixArray:
        data = om2.MFnMatrixArrayData().create(om2.MMatrixArray())
        attr = om2.MFnTypedAttribute()
        aobj = attr.create(longName, shortName, om2.MFnData.kMatrixArray, data)

    else:
        raise TypeError(
            "Unsupported Attribute Type: {}, name: {}".format(attrType, longName)
        )

    attr.array = isArray
    storable = kwargs.get("storable", True)
    writable = kwargs.get("writable", True)
    connectable = kwargs.get("connectable", True)
    minValue = kwargs.get("min")
    maxValue = kwargs.get("max")
    softMin = kwargs.get("softMin")
    softMax = kwargs.get("softMax")
    value = kwargs.get("value")
    locked = kwargs.get("locked", False)
    attr.storable = storable
    attr.writable = writable
    attr.connectable = connectable
    if channelBox is not None:
        attr.channelBox = channelBox
    if keyable is not None:
        attr.keyable = keyable
    if default is not None:
        if attrType == attrtypes.kMFnDataString:
            default = om2.MFnStringData().create(default)
        elif attrType == attrtypes.kMFnDataMatrix:
            default = om2.MMatrix(default)
        elif attrType == attrtypes.kMFnUnitAttributeAngle:
            default = om2.MAngle(default, om2.MAngle.kRadians)
        elif attrType == attrtypes.kMFnUnitAttributeDistance:
            default = om2.MDistance(default)
        elif attrType == attrtypes.kMFnUnitAttributeTime:
            default = om2.MTime(default)
        plugs.setAttributeFnDefault(aobj, default)
    if minValue is not None:
        plugs.setAttrMin(aobj, minValue)
    if maxValue is not None:
        plugs.setAttrMax(aobj, maxValue)
    if softMin is not None:
        plugs.setAttrMin(aobj, softMin)
    if softMax is not None:
        plugs.setAttrMax(aobj, softMax)
    if aobj is not None and apply:
        modifier = mod or om2.MDGModifier()
        modifier.addAttribute(node, aobj)

        modifier.doIt()
        plug = om2.MPlug(node, aobj)
        kwargs["Type"] = attrType
        if value is not None:
            plugs.setPlugValue(plug, value)
        plug.isLocked = locked
    return attr


def serializeNode(
    node,
    skipAttributes=None,
    includeConnections=True,
    includeAttributes=(),
    extraAttributesOnly=False,
    useShortNames=False,
    includeNamespace=True,
):
    """This function takes an om2.MObject representing a maya node and serializes it into a dict,
    This iterates through all attributes, serializing any extra attributes found, any default attribute has not changed
    (defaultValue) and not connected or is an array attribute will be skipped.
    if `arg` includeConnections is True then all destination connections are serialized as a dict per connection.

    :param node: The node to serialize
    :type node: om2.MObject
    :param skipAttributes: The list of attribute names to serialization.
    :type skipAttributes: list or None
    :param includeConnections: If True find and serialize all connections where the destination is this node.
    :type includeConnections: bool
    :param includeAttributes: If Provided then only these attributes will be serialized
    :type includeAttributes: iterable
    :param extraAttributesOnly: If True then only extra attributes will be serialized
    :type extraAttributesOnly: bool
    :param useShortNames: If True only the short name of nodes will be used.
    :type useShortNames: bool
    :param includeNamespace: Whether to include the namespace as part of the node.
    :type includeNamespace: bool
    :rtype: dict

    Returns values::

        {
                    "attributes": [
                    {
                      "Type": 10,
                      "channelBox": false,
                      "default": 0.0,
                      "isArray": false,
                      "isDynamic": true,
                      "keyable": true,
                      "locked": false,
                      "max": null,
                      "min": null,
                      "name": "toeRest",
                      "softMax": 3.14,
                      "softMin": -1.7,
                      "value": 0.31353071143768485
                    },
                  ],
                  "connections": [
                    {
                      "destination": "|legGlobal_L_cmpnt|control|configParameters",
                      "destinationPlug": "plantLength",
                      "source": "|legGlobal_L_guide_heel_ctrl|legGlobal_L_guide_tip_ctrl",
                      "sourcePlug": "translateZ"
                    },
                  ],
                  "name": "|legGlobal_L_cmpnt|control|configParameters",
                  "parent": "|legGlobal_L_cmpnt|control",
                  "type": "transform"
        }

    """
    data = {}
    # for dag nodes the naming interface in maya is different(grr) also handle that and
    # handle grabbing the parent node
    if node.hasFn(om2.MFn.kDagNode):
        dep = om2.MFnDagNode(node)
        name = (
            dep.fullPathName().split("|")[-1] if useShortNames else dep.fullPathName()
        )
        parentDep = om2.MFnDagNode(dep.parent(0))
        parentDepName = (
            parentDep.fullPathName().split("|")[-1]
            if useShortNames
            else parentDep.fullPathName()
        )
        if not includeNamespace:
            name = name.split("|")[-1].split(":")[-1]
            if parentDepName:
                parentDepName = parentDepName.split("|")[-1].split(":")[-1]
        else:
            name = name.replace(
                om2.MNamespace.getNamespaceFromName(name).split("|")[-1] + ":", ""
            )
            if parentDepName:
                parentDepName = parentDepName.replace(
                    om2.MNamespace.getNamespaceFromName(parentDepName).split("|")[-1]
                    + ":",
                    "",
                )
        data["parent"] = parentDepName

    else:
        dep = om2.MFnDependencyNode(node)
        name = dep.name()
        if not includeNamespace:
            name = name.split("|")[-1].split(":")[-1]
        else:
            name = name.replace(
                om2.MNamespace.getNamespaceFromName(name).split("|")[-1] + ":", ""
            )

    data["name"] = name
    data["type"] = dep.typeName

    req = dep.pluginName
    if req:
        data["requirements"] = zooPath.getFileNameNoExt(req)
    attributes = []
    visited = []
    if node.hasFn(om2.MFn.kAnimCurve):
        data.update(anim.serializeAnimCurve(node))
    else:
        if extraAttributesOnly:
            iterator = iterExtraAttributes(
                node, skip=skipAttributes, includeAttributes=includeAttributes
            )
        else:
            iterator = iterAttributes(
                node, skip=skipAttributes, includeAttributes=includeAttributes
            )
        for pl in iterator:
            if (pl.isDefaultValue() and not pl.isDynamic) or pl.isChild:
                continue
            attrData = plugs.serializePlug(pl)
            if attrData:
                attributes.append(attrData)
            visited.append(pl)
        if attributes:
            data["attributes"] = attributes
    if includeConnections:
        connections = []
        for destination, source in iterConnections(
            node, source=False, destination=True
        ):
            connections.append(plugs.serializeConnection(destination))
        if connections:
            data["connections"] = connections

    return data


def deserializeNode(data, parent=None, includeAttributes=True):
    """Given the data from serializeNode() this will create a new node and set the attributes and connections.

    .. code-block: json

        {
                "attributes": [
                {
                  "Type": 10,
                  "channelBox": false,
                  "default": 0.0,
                  "isArray": false,
                  "isDynamic": true,
                  "keyable": true,
                  "locked": false,
                  "max": null,
                  "min": null,
                  "name": "toeRest",
                  "softMax": 3.14,
                  "softMin": -1.7,
                  "value": 0.31353071143768485
                },
              ],
              "name": "|legGlobal_L_cmpnt|control|configParameters",
              "parent": "|legGlobal_L_cmpnt|control",
              "type": "transform"
        }

    :param data: Same data as serializeNode()
    :type data: dict
    :param parent: The parent of the newly created node if any defaults to None which is the same as the world node
    :type parent: om2.MObject
    :param includeAttributes: If True  the attributes within the data struct will be created or updated, default True.
    :type includeAttributes: bool
    :return: The created node MObject, a list of created attributes
    :rtype: tuple(MObject, list(om2.MPlug))
    """
    nodeName = data["name"].split("|")[-1]
    nodeType = data.get("type")
    if nodeType is None:
        return None, []
    req = data.get("requirements", "")
    if req and not cmds.pluginInfo(req, loaded=True, query=True):
        try:
            cmds.loadPlugin(req)
        except RuntimeError:
            logger.error("Could not load plugin->{}".format(req), exc_info=True)
            return None, []

    if "parent" in data:
        newNode = createDagNode(nodeName, nodeType, parent)
        mfn = om2.MFnDagNode(newNode)
        nodeName = mfn.fullPathName()
    else:
        newNode = createDGNode(nodeName, nodeType)
        if newNode.hasFn(om2.MFn.kAnimCurve):
            mfn = om2Anim.MFnAnimCurve(newNode)
            mfn.setPreInfinityType(data["preInfinity"])
            mfn.setPostInfinityType(data["postInfinity"])
            mfn.setIsWeighted(data["weightTangents"])
            mfn.addKeysWithTangents(
                data["frames"],
                data["values"],
                mfn.kTangentGlobal,
                mfn.kTangentGlobal,
                data["inTangents"],
                data["outTangents"],
            )
            for i in range(len(data["frames"])):
                mfn.setAngle(i, om2.MAngle(data["inTangentAngles"][i]), True)
                mfn.setAngle(i, om2.MAngle(data["outTangentAngles"][i]), False)
                mfn.setWeight(i, data["inTangentWeights"][i], True)
                mfn.setWeight(i, data["outTangentWeights"][i], False)
                mfn.setInTangentType(i, data["inTangents"][i])
                mfn.setOutTangentType(i, data["outTangents"][i])
        else:
            mfn = om2.MFnDependencyNode(newNode)
        nodeName = mfn.name()
    createdAttributes = []
    if not includeAttributes:
        return newNode, createdAttributes
    for attrData in data.get("attributes", ()):
        name = attrData["name"]
        try:
            plug = mfn.findPlug(name, False)
            found = True
        except RuntimeError:
            found = False
            plug = None
        if found:
            try:
                if plug.isLocked:
                    continue
                plugs.setPlugInfoFromDict(plug, **attrData)
            except RuntimeError:
                fullName = ".".join([nodeName, name])
                logger.error(
                    "Failed to set plug data: {}".format(fullName), exc_info=True
                )
        else:
            if attrData.get("isChild", False):
                continue
            shortName = name.split(".")[-1]
            children = attrData.get("children")
            try:
                if children:
                    attr = addCompoundAttribute(
                        newNode, shortName, shortName, attrMap=children, **attrData
                    )
                elif attrData.get("isElement", False):
                    continue
                else:
                    attr = addAttribute(
                        newNode, shortName, shortName, attrData["Type"], **attrData
                    )
            except AttributeAlreadyExists:
                continue
            createdAttributes.append(om2.MPlug(newNode, attr.object()))
    return newNode, createdAttributes


def setLockStateOnAttributes(node, attributes, state=True):
    """Locks and unlocks the given attributes

    :param node: the node that have its attributes locked
    :type node: MObject
    :param attributes: a list of attribute name to lock
    :type attributes: seq(str)
    :param state: True to lock and False to unlcck
    :type state: bool
    :return: True is successful
    :rtype: bool
    """
    dep = om2.MFnDependencyNode(node)
    for attr in attributes:
        try:
            plug = dep.findPlug(attr, False)
        except RuntimeError:  # missing plug
            continue
        if plug.isLocked != state:
            plug.isLocked = state
    return True


def showHideAttributes(node, attributes, state=True):
    """Shows or hides and attribute in the channelbox

    :param node: The MObject representing the DG node
    :type node: MObject
    :param attributes: attribute names on the given node
    :type attributes: seq(str)
    :param state: True for show False for hide, defaults to True
    :type state: bool
    :return: True if successful
    :rtype: bool
    """
    dep = om2.MFnDependencyNode(node)
    for attr in attributes:
        plug = dep.findPlug(attr, False)
        if plug.isChannelBox != state:
            plug.isChannelBox = state
    return True


def mirrorJoint(
    node, parent, translate, rotate, mirrorFunction=mayamath.MIRROR_BEHAVIOUR
):
    """Mirror the joint's translation and rotation attributes based on the mirrorFunction.

    :param node: The joint to be mirrored.
    :type node: om2.MObject
    :param parent: The parent joint of the joint being mirrored.
    :type parent: om2.MObject
    :param translate: The translation values to be mirrored.
    :type translate: tuple or list
    :param rotate: The rotation values to be mirrored.
    :type rotate: tuple or list
    :param mirrorFunction: The behavior of the mirroring operation. Defaults to mayamath.MIRROR_BEHAVIOUR.
    :type mirrorFunction: int
    """
    nFn = om2.MFnDependencyNode(node)
    rotateOrder = nFn.findPlug("rotateOrder", False).asInt()
    transMatRotateOrder = generic.intToMTransformRotationOrder(rotateOrder)
    translation, rotMatrix = mirrorTransform(
        node, parent, translate, rotate, mirrorFunction
    )  # MVector, MMatrix
    jointOrder = om2.MEulerRotation(
        plugs.getPlugValue(nFn.findPlug("jointOrient", False))
    )
    # deal with joint orient
    jo = om2.MTransformationMatrix().setRotation(jointOrder).asMatrixInverse()
    # applyRotation and translation
    rot = mayamath.toEulerFactory(rotMatrix * jo, transMatRotateOrder)
    setRotation(node, rot)
    setTranslation(node, translation)


def mirrorTranslation(transformationMatrix, translateAxis):
    """Mirrors the translation of a transformation matrix.

    :param transformationMatrix: The transformation matrix to mirror.
    :type transformationMatrix: :class:`om2.MTransformationMatrix`
    :param translateAxis: The axis or axes to mirror the translation along. Can be any combination of "x", "y", and "z".
    :type translateAxis: str or list[str]
    :return: The mirrored transformation matrix.
    :rtype: :class:`om2.MTransformationMatrix`
    """
    translation = transformationMatrix.translation(om2.MSpace.kWorld)

    if len(translateAxis) == 3:
        translation *= -1
    else:
        for i in translateAxis:
            index = zoomath.AXIS[i]
            translation[index] *= -1

    transformationMatrix.setTranslation(translation, om2.MSpace.kWorld)
    return transformationMatrix


def axisNamesToNegativeVector(axisNames, vector):
    """This method takes a list of axis names and a vector as parameters. It modifies the vector by setting the specified
    axis names to -1. If no vector is provided, a default zero vector is used. The modified vector is then returned.

    :param axisNames: List of strings representing axis names. eg. ["x", "y", "z"]
    :type axisNames: list[str]
    :param vector: The vector to modify. If not provided, a default zero vector will be used.
    :type vector: :class:`OpenMaya.MVector` or None
    :return: The modified vector with the specified axis names set to -1.
    :rtype: :class:`OpenMaya.MVector`
    """
    translationVector = vector or om2.MVector()
    for i in axisNames:
        index = zoomath.AXIS[i]
        translationVector[index] *= -1
    return translationVector


def mirrorTransform(
    node, parent, translate, rotate, mirrorFunction=mayamath.MIRROR_BEHAVIOUR
):
    """Mirror's the translation and rotation of a node relative to another unless the parent
    is specified as om2.MObject.kNullObj in which case world.

    :param node: the node transform the mirror
    :type node: om2.MObject
    :param parent: the parent Transform to mirror relative too.
    :type parent: om2.MObject or om2.MObject.kNullObj
    :param translate: the axis to mirror, can be one or more
    :type translate: tuple(str)
    :param rotate: "xy", "yz" or "xz"
    :type rotate: str
    :param mirrorFunction:
    :type mirrorFunction: int
    :return: mirrored translation vector and the mirrored rotation matrix
    :rtype: om2.MVector, om2.MMatrix
    """
    currentMat = getWorldMatrix(node)

    transMat = om2.MTransformationMatrix(currentMat)
    # mirror the rotation on a plane
    quaternion = transMat.rotation(asQuaternion=True)
    # behavior
    if mirrorFunction == mayamath.MIRROR_BEHAVIOUR:
        if rotate == "xy":
            quaternion = om2.MQuaternion(
                quaternion.y * -1, quaternion.x, quaternion.w, quaternion.z * -1
            )
        elif rotate == "yz":
            quaternion = om2.MQuaternion(
                quaternion.w * -1, quaternion.z, quaternion.y * -1, quaternion.x
            )
        else:
            quaternion = om2.MQuaternion(
                quaternion.z, quaternion.w, quaternion.x * -1, quaternion.y * -1
            )
        transMat = mirrorTranslation(transMat, translate)
        transMat.setRotation(quaternion)
    elif mirrorFunction == mayamath.MIRROR_RELATIVE:
        originalScale = transMat.scale(om2.MSpace.kWorld)
        # if not rotate then we scale without rotating
        resultTransform = om2.MTransformationMatrix()
        scaleVector = axisNamesToNegativeVector(translate, om2.MVector(originalScale))
        resultTransform.setScale(scaleVector, om2.MSpace.kWorld)
        # rotate the source if we provided a rotated axis
        if rotate:
            euler = transMat.rotation(asQuaternion=False)
            if rotate == "xz":
                euler.y += math.pi
            elif rotate == "yz":
                euler.x += math.pi
            else:
                euler.z += math.pi
            transMat.setRotation(euler)
        transMat = om2.MTransformationMatrix(
            transMat.asMatrix() * resultTransform.asMatrix()
        )
        if rotate:
            transMat.setScale(originalScale, om2.MSpace.kWorld)
    elif mirrorFunction == mayamath.MIRROR_SCALE:
        scaleVector = axisNamesToNegativeVector(
            translate, om2.MVector(transMat.scale(om2.MSpace.kWorld))
        )
        mirrorTranslation(transMat, translate)
        transMat.setScale(scaleVector, om2.MSpace.kWorld)
    else:
        transMat = mirrorTranslation(transMat, translate)
    # put the mirror rotationMat in the space of the parent
    if parent != om2.MObject.kNullObj:
        rot = transMat.asRotateMatrix()
        parentMatInv = getParentInverseMatrix(parent)
        rot *= parentMatInv
        quaternion = om2.MTransformationMatrix(rot).rotation(asQuaternion=True)

    return (
        transMat.translation(om2.MSpace.kWorld),
        quaternion,
        transMat.scale(om2.MSpace.kWorld),
        transMat.asMatrix(),
    )


def mirrorNode(
    node, parent, translate, rotate, mirrorFunction=mayamath.MIRROR_BEHAVIOUR
):
    """Mirrors the given node with respect to the specified parent, translation, and rotation parameters.

    :param node: The node to mirror.
    :type node: str
    :param parent: The parent node of the node to mirror.
    :type parent: str
    :param translate: Whether to mirror the translation of the node.
    :type translate: bool
    :param rotate: Whether to mirror the rotation of the node.
    :type rotate: bool
    :param mirrorFunction: The mirror function to use for mirroring. Defaults to mayamath.MIRROR_BEHAVIOUR.
    :type mirrorFunction: int
    """
    translation, quat, scale, matrix = mirrorTransform(
        node, parent, translate, rotate, mirrorFunction
    )  # MVector, MMatrix
    setMatrix(node, matrix, space=om2.MSpace.kWorld)


def matchTransformMulti(
    targetPaths,
    source,
    translation=True,
    rotation=True,
    scale=True,
    space=om2.MSpace.kWorld,
    pivot=False,
):
    """Matches the transform(SRT) for a list of nodes to another node.

    :param targetPaths: A list om2.MDagPaths to snap to the source
    :type targetPaths: list(om2.MDagPath)
    :param source: The source transform node switch the target nodes will match
    :type source: om2.MObject
    :param translation: True to match translation
    :type translation: bool
    :param rotation: True to match rotation
    :type rotation: bool
    :param scale: True to match scale
    :type scale: bool
    :param space: coordinate space
    :type space: int
    :param pivot:
    :type pivot: True to match pivot
    :return: True if passed
    :rtype: bool
    """
    # get the proper matrix of source
    if space == om2.MSpace.kWorld:
        sourceMatrix = getWorldMatrix(source)
        srcTfm = om2.MTransformationMatrix(sourceMatrix)
        tfm = srcTfm
    else:
        sourceMatrix = getMatrix(source)
        srcTfm = om2.MTransformationMatrix(sourceMatrix)
        tfm = srcTfm
    # source pos
    pos = srcTfm.translation(space)

    # source pivot
    srcPivot = srcTfm.scalePivot(space)

    fn = om2.MFnTransform()
    for targetPath in targetPaths:
        targetNode = targetPath.node()
        fn.setObject(targetNode)
        if space != om2.MSpace.kWorld:
            invParent = getParentInverseMatrix(targetNode)
            tfm = om2.MTransformationMatrix(sourceMatrix * invParent)
        # rotation
        rot = tfm.rotation()
        # scale
        scl = tfm.scale(space)
        # set Scaling
        if scale:
            fn.setScale(scl)
        # set Rotation
        if rotation:
            fn.setRotation(rot, om2.MSpace.kTransform)
        # set Translation
        if translation:
            if pivot:
                nodePivot = fn.scalePivot(space)
                pos += srcPivot - nodePivot
            fn.setTranslation(pos, space)
    return True


def matchTransformSingle(
    targetPath,
    source,
    translation=True,
    rotation=True,
    scale=True,
    space=om2.MSpace.kWorld,
    pivot=False,
):
    """Matches the transform(SRT) for a list of nodes to another node.

    :param targetPath: om2.MDagPath to snap to the source
    :type targetPath: om2.MDagPath
    :param source: The source transform node switch the target nodes will match
    :type source: om2.MObject
    :param translation: True to match translation
    :type translation: bool
    :param rotation: True to match rotation
    :type rotation: bool
    :param scale: True to match scale
    :type scale: bool
    :param space: coordinate space
    :type space: int
    :param pivot:
    :type pivot: True to match pivot
    :return: True if passed
    :rtype: bool
    """
    targetNode = targetPath.node()
    # get the proper matrix of source
    if space == om2.MSpace.kWorld:
        sourceMatrix = getWorldMatrix(source)
        srcTfm = om2.MTransformationMatrix(sourceMatrix)
        # multiply the global scale and rotation by the nodes parent inverse world matrix to get local rot & scl
        invParent = getParentInverseMatrix(targetNode)
        tfm = om2.MTransformationMatrix(sourceMatrix * invParent)
    else:
        srcTfm = om2.MTransformationMatrix(getMatrix(source))
        tfm = srcTfm
    # source pos
    pos = srcTfm.translation(space)

    # source pivot
    srcPivot = srcTfm.scalePivot(space)

    # rotation
    rot = tfm.rotation()
    # scale
    scl = tfm.scale(space)
    fn = om2.MFnTransform(targetPath)
    # set Scaling
    if scale:
        fn.setScale(scl)
    # set Rotation
    if rotation:
        fn.setRotation(rot, om2.MSpace.kTransform)
    # set Translation
    if translation:
        if pivot:
            nodePivot = fn.scalePivot(space)
            pos += srcPivot - nodePivot
        fn.setTranslation(pos, space)
    return True


def swapOutgoingConnections(source, destination, plugs=None):
    """Swap outgoing connections from one node to another.

    :param source: The source node to swap outgoing connections from.
    :type source: `str`
    :param destination: The destination node to swap outgoing connections to.
    :type destination: `str`
    :param plugs: Optional list of plugs to filter connections. Only connections from these plugs will be swapped.
    :type plugs: `list[str]`
    :return: The Maya dependency graph modifier object used to make the connections.
    :rtype: :class:`maya.api.OpenMaya.MDGModifier`
    """
    plugs = plugs or []
    destFn = om2.MFnDependencyNode(destination)
    mod = om2.MDGModifier()
    for sourcePlug, destinationPlug in iterConnections(source, True, False):
        if plugs and sourcePlug not in plugs:
            continue
        name = sourcePlug.partialName(
            includeNonMandatoryIndices=True,
            useLongNames=True,
            includeInstancedIndices=True,
        )

        if not destFn.hasAttribute(name):
            continue
        targetPlug = destFn.findPlug(sourcePlug.attribute(), False)
        if destinationPlug.isLocked:
            destinationPlug.isLocked = False
        mod.disconnect(sourcePlug, destinationPlug)
        mod.connect(targetPlug, destinationPlug)

    return mod
