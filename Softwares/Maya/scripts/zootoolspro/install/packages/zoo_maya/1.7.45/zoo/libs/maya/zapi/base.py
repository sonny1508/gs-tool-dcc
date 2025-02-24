__all__ = (
    "DGNode",
    "DagNode",
    "ObjectSet",
    "BlendShape",
    "AnimCurve",
    "DisplayLayer",
    "NurbsCurve",
    "Mesh",
    "Camera",
    "IkHandle",
    "SkinCluster",
    "Plug",
    "Time",
    "displayLayers",
    "createDag",
    "createDG",
    "nodeByObject",
    "nodeByName",
    "nodesByNames",
    "ls",
    "plugByName",
    "lockNodeContext",
    "lockStateAttrContext",
    "fullNames",
    "shortNames",
    "alphabetizeDagList",
    "selected",
    "select",
    "selectByNames",
    "clearSelection",
    "controllerTag",
    "hasControllerTag",
    "duplicateAsTransform",
    "ContainerAsset",
    "Matrix",
    "TransformationMatrix",
    "Vector",
    "Point",
    "Quaternion",
    "EulerRotation",
    "Plane",
    "dgModifier",
    "dagModifier",
    "DGContext",
    "namespaceContext",
    "tempNamespaceContext",
    "localTranslateAttrs",
    "localRotateAttrs",
    "localScaleAttrs",
    "localTransformAttrs",
    "localRotateAttr",
    "localTranslateAttr",
    "localScaleAttr",
    "kTransform",
    "kDependencyNode",
    "kDagNode",
    "kControllerTag",
    "kJoint",
    "kWorldSpace",
    "kTransformSpace",
    "kObjectSpace",
    "kRotateOrder_XYZ",
    "kRotateOrder_YZX",
    "kRotateOrder_ZXY",
    "kRotateOrder_XZY",
    "kRotateOrder_YXZ",
    "kRotateOrder_ZYX",
    "kNodeTypes",
    "kIkRPSolveType",
    "kIkSCSolveType",
    "kIkSplineSolveType",
    "kIkSpringSolveType",
    "kTangentGlobal",
    "kTangentFixed",
    "kTangentLinear",
    "kTangentFlat",
    "kTangentSmooth",
    "kTangentStep",
    "kTangentClamped",
    "kTangentPlateau",
    "kTangentStepNext",
    "kTangentAuto",
    "kInfinityConstant",
    "kInfinityLinear",
    "kInfinityCycle",
    "kInfinityCycleRelative",
    "kInfinityOscillate",
)

import contextlib
import logging
from functools import wraps

from maya.api import OpenMaya as om2
from maya.api import OpenMayaAnim as om2Anim
from maya import cmds
from zoovendor.six.moves import range

from zoo.libs.utils import general as generalutils
from zoo.libs.maya.api import plugs
from zoo.libs.maya.api import attrtypes
from zoo.libs.maya.api import generic
from zoo.libs.maya.api import scene
from zoo.libs.maya.api import nodes
from zoo.libs.maya.utils import general, mayamath
from zoo.libs.maya.api import constants as apiconstants
from zoo.libs.maya.zapi import errors

# MMatrix class for representing 4x4 transformation matrices
Matrix = om2.MMatrix
# MTransformationMatrix class for representing and manipulating transformations
TransformationMatrix = om2.MTransformationMatrix
# MVector class for representing 3D vectors
Vector = om2.MVector
# MPoint
Point = om2.MPoint
# MQuaternion class for representing quaternions
Quaternion = om2.MQuaternion
# MEulerRotation class for representing rotations using Euler angles
EulerRotation = om2.MEulerRotation
# MPlane class for representing planes
Plane = om2.MPlane
# MTime class for representing time values
Time = om2.MTime
# Constant representing a transform node type
kTransform = om2.MFn.kTransform
# Constant representing a dependency node type
kDependencyNode = om2.MFn.kDependencyNode
# Constant representing a DAG node type
kDagNode = om2.MFn.kDagNode
# Constant representing a controller tag node type
kControllerTag = om2.MFn.kControllerTag
# Constant representing a joint node type
kJoint = om2.MFn.kJoint
# Constant representing world space
kWorldSpace = om2.MSpace.kWorld
# Constant representing transform space
kTransformSpace = om2.MSpace.kTransform
# Constant representing object space
kObjectSpace = om2.MSpace.kObject
# MDGModifier class for modifying the DAG or DG
dgModifier = om2.MDGModifier
# MDagModifier class for modifying the DAG
dagModifier = om2.MDagModifier
# MDGContext class for representing the evaluation context of the DG
DGContext = om2.MDGContext
# Namespace context object for manipulating namespaces
namespaceContext = general.namespaceContext
# Temporary namespace context object for creating and deleting namespaces
tempNamespaceContext = general.tempNamespaceContext
# Constant representing the XYZ rotate order
kRotateOrder_XYZ = apiconstants.kRotateOrder_XYZ
# Constant representing the YZX rotate order
kRotateOrder_YZX = apiconstants.kRotateOrder_YZX
# Constant representing the ZXY rotate order
kRotateOrder_ZXY = apiconstants.kRotateOrder_ZXY
# Constant representing the XZY rotate order
kRotateOrder_XZY = apiconstants.kRotateOrder_XZY
# Constant representing the YXZ rotate order
kRotateOrder_YXZ = apiconstants.kRotateOrder_YXZ
# Constant representing the ZYX rotate order
kRotateOrder_ZYX = apiconstants.kRotateOrder_ZYX
# Module containing constants representing different node types in Maya
kNodeTypes = om2.MFn

# Constants representing different types of IK solvers
kIkRPSolveType = "ikRPsolver"
kIkSCSolveType = "ikSCsolver"
kIkSplineSolveType = "ikSplineSolver"
kIkSpringSolveType = "ikSpringSolver"

# Constants representing different types of tangents
kTangentGlobal = om2Anim.MFnAnimCurve.kTangentGlobal
kTangentFixed = om2Anim.MFnAnimCurve.kTangentFixed
kTangentLinear = om2Anim.MFnAnimCurve.kTangentLinear
kTangentFlat = om2Anim.MFnAnimCurve.kTangentFlat
kTangentSmooth = om2Anim.MFnAnimCurve.kTangentSmooth
kTangentStep = om2Anim.MFnAnimCurve.kTangentStep
kTangentClamped = om2Anim.MFnAnimCurve.kTangentClamped
kTangentPlateau = om2Anim.MFnAnimCurve.kTangentPlateau
kTangentStepNext = om2Anim.MFnAnimCurve.kTangentStepNext
kTangentAuto = om2Anim.MFnAnimCurve.kTangentAuto

# Constants representing different types of infinity
kInfinityConstant = om2Anim.MFnAnimCurve.kConstant
kInfinityLinear = om2Anim.MFnAnimCurve.kLinear
kInfinityCycle = om2Anim.MFnAnimCurve.kCycle
kInfinityCycleRelative = om2Anim.MFnAnimCurve.kCycleRelative
kInfinityOscillate = om2Anim.MFnAnimCurve.kOscillate

# List of local translate attributes
localTranslateAttrs = ["translateX", "translateY", "translateZ"]
# List of local rotate attributes
localRotateAttrs = ["rotateX", "rotateY", "rotateZ"]
# List of local scale attributes
localScaleAttrs = ["scaleX", "scaleY", "scaleZ"]
localRotateAttr = "rotate"
localTranslateAttr = "translate"
localScaleAttr = "scale"
# List of all local transform attributes
localTransformAttrs = localTranslateAttrs + localRotateAttrs + localScaleAttrs

logger = logging.getLogger(__name__)


def lockNodeContext(func):
    """Decorator function to lock and unlock the meta, designed purely for the metaclass.

    :param func: The function to decorate.
    :type func: function
    :return: The decorated function.
    :rtype: function
    """

    @wraps(func)
    def locker(*args, **kwargs):
        node = args[0]
        setLocked = False
        if node.isLocked and not node.isReferenced():
            node.lock(False)
            setLocked = True
        try:
            return func(*args, **kwargs)
        finally:
            if setLocked and node.exists():
                node.lock(True)

    return locker


def lockNodePlugContext(func):
    """Decorator function that unlocks a plug and/or node if they are locked before calling a function,
    and locks them again after the function has completed.

    :param func: The function to decorate.
    :type func: function
    :return: The decorated function.
    :rtype: function
    """

    @wraps(func)
    def locker(*args, **kwargs):
        plug = args[0]
        node = plug.node()

        setLocked = False
        setPlugLocked = False
        if node.isLocked and not node.isReferenced():
            node.lock(False)
            setLocked = True
        if plug.isLocked:
            plug.lock(False)
            setPlugLocked = True
        try:
            return func(*args, **kwargs)
        finally:
            if node.exists():
                if setPlugLocked and plug.exists():
                    plug.lock(True)
                if setLocked:
                    node.lock(True)

    return locker


@contextlib.contextmanager
def lockStateAttrContext(node, attrNames, state):
    """Context manager which handles the lock state for a list of attributes on a node.

    :param node: The Node to lock  the attributes on.
    :type node: :class:`DGNode`
    :param attrNames: The List of attribute names excluding the node name.
    :type attrNames: list[str]
    :param state: The lock state to set to while within the context scope
    :type state: bool
    """
    attributes = []
    try:
        for attrName in attrNames:
            attr = node.attribute(attrName)
            if attr is None:
                continue
            if attr.isLocked != state:
                attributes.append(attr)
                attr.lock(state)
        yield
    finally:
        for attr in attributes:
            if not attr:  # handle existence
                continue
            attr.lock(not state)


class DGNode(object):
    """Base Maya node class for Dependency graph nodes.

    Subclasses should implement :func:`create` :func:`serializeFromScene` methods, can be instantiated directly.

    The intention with the class is to create a thin layer around maya MObject for DGNodes to allow working with the
    maya api 2.0 easier. Much of the code here calls upon :mod:`zoo.libs.maya.api` helper functions.

    Any method which returns a node will always return a :class:`DGNode`, any method that returns an attribute
    will return a :class:`Plug` instance.

    .. code-block:: python

        from zoo.libs.maya import zapi
        multi = zapi.DGNode()
        multi.create(name="testNode", nodeType="multipleDivide")
        # set the input1 Vector by using the zoo lib helpers
        multi.input1.set(zapi.Vector(10,15,30))
        multi2 = zapi.DGNode()
        multi2.create(name="dest", Type="plusMinusAverage")
        # connect the output plug to unconnected elementPlug of the plus minus average node
        multi.connect("output", multi2.input3D.nextAvailableElementPlug())

    :param node: The maya node that this class will operate on, if None then you are expected to call create()
    :type node: om2.MObject, None
    """

    _mfnType = om2.MFnDependencyNode

    def __init__(self, node=None):
        self._node = None
        self._node = None
        self._mfn = None  # type: om2.MFnDependencyNode or None
        if node is not None:
            self.setObject(node)

    def __getitem__(self, item):
        """Attempts to retrieve the MPlug for this node. Falls back to the super class __getattribute__ otherwise.

        :param item: The attribute name
        :type item: str
        :rtype: :class:`Plug`
        """
        fn = self._mfn
        try:
            return Plug(self, fn.findPlug(item, False))
        except RuntimeError:
            raise KeyError(
                "{} has no attribute by the name: {}".format(self.name(), item)
            )

    def __getattr__(self, name):
        """Attempts to retrieve the MPlug for this node. Falls back to the super class __getattribute__ otherwise.

        :param name: The attribute name
        :type name: str
        :rtype: :class:`Plug`
        """
        attr = self.attribute(name)
        if attr is not None:
            return attr
        return super(DGNode, self).__getattribute__(name)

    def __setattr__(self, key, value):
        if key.startswith("_"):
            super(DGNode, self).__setattr__(key, value)
            return
        if self.hasAttribute(key) is not None:
            if isinstance(value, Plug):
                self.connect(key, value)
                return
            self.setAttribute(key, value)
            return
        super(DGNode, self).__setattr__(key, value)

    def __setitem__(self, key, value):
        if key.startswith("_"):
            setattr(self, key, value)
            return
        if self.hasAttribute(key) is not None:
            if isinstance(value, Plug):
                self.connect(key, value)
                return
            self.setAttribute(key, value)
            return
        else:
            raise RuntimeError(
                "Node: {} has no attribute called: {}".format(self.name(), key)
            )

    def __hash__(self):
        return self._node.hashCode()

    def __repr__(self):
        return "<{}> {}".format(self.__class__.__name__, self.fullPathName())

    def __str__(self):
        return self.fullPathName()

    def __bool__(self):
        return self.exists()

    def __ne__(self, other):
        """Compares the nodes with  != .

        :param other:
        :type other: :class:`DGNode` or :class:`DagNode`
        :rtype: bool
        """
        if not isinstance(other, DGNode):
            return True
        return self._node != other.handle()

    def __eq__(self, other):
        """Compares the two nodes with == .

        :param other:
        :type other: :class:`DGNode` or :class:`DagNode`
        :rtype: bool
        """
        if not isinstance(other, DGNode) or (
            isinstance(other, DGNode) and other.handle() is None
        ):
            return False
        return self._node == other.handle()

    def __contains__(self, key):
        return self.hasAttribute(key)

    def __delitem__(self, key):
        self.deleteAttribute(key)

    def setObject(self, mObject):
        """Set's the MObject For this :class:`DGNode` instance

        :param mObject: The maya api om2.MObject representing a MFnDependencyNode
        :type mObject: :class:`om2.MObject`
        """
        objectPath = mObject
        if isinstance(mObject, om2.MDagPath):
            mObject = mObject.node()
        if not mObject.hasFn(om2.MFn.kDependencyNode):
            raise ValueError("Invalid MObject Type {}".format(mObject.apiTypeStr))
        self._node = om2.MObjectHandle(mObject)
        self._mfn = self._mfnType(objectPath)

    def object(self):
        """Returns the object of the node

        :rtype: :class:`om2.MObject`
        """
        if self.exists():
            return self._node.object()

    def handle(self):
        """Returns the MObjectHandle instance attached to the class. Client of this function is responsible for
        dealing with object existence.

        :rtype: om2.MObjectHandle
        """
        return self._node

    def typeId(self):
        """Returns the maya typeId from the functionSet

        :return: The type id or -1. if -1 it's concerned a invalid node.
        :rtype: int
        """
        if self.exists():
            return self._mfn.typeId
        return -1

    def hasFn(self, fnType):
        """Returns whether the underlying MObject has the specified om2.MFn.kConstant type.

        :param fnType: The om2.MFn kType
        :type fnType: om2.MFn.kConstant
        :return:
        :rtype: bool
        """
        return self._node.object().hasFn(fnType)

    def apiType(self):
        """Returns the maya apiType int

        :rtype: int
        """
        return self._node.object().apiType()

    @property
    def typeName(self):
        """Returns the maya apiType int

        :rtype: int
        """
        return self._mfn.typeName

    def exists(self):
        """Returns True if the node is currently valid in the maya scene

        :rtype: bool
        """
        node = self._node
        if node is None:
            return False
        return node.isValid() and node.isAlive()

    def fullPathName(self, partialName=False, includeNamespace=True):
        """returns the nodes scene name, this result is dependent on the arguments, by default
        always returns the full path

        :param partialName: the short name of the node
        :type partialName: bool
        :param includeNamespace: True if the return name includes the namespace, default True
        :type includeNamespace: bool
        :return longName: the nodes Name
        :rtype longName: str
        """
        if self.exists():
            return nodes.nameFromMObject(self.object(), partialName, includeNamespace)

        raise RuntimeError("Current node doesn't exist!")

    def name(self, includeNamespace=True):
        """Returns the name for the node which is achieved by the name or id  use self.fullPathName for the
        nodes actually scene name
        """
        if self.exists():
            if includeNamespace:
                return self.mfn().name()
            return om2.MNamespace.stripNamespaceFromName(self.mfn().name())
        return ""

    @lockNodeContext
    def rename(self, name, maintainNamespace=False, mod=None, apply=True):
        """Renames this node, If

        :param name: the new name
        :type name: str
        :param maintainNamespace: If True then the current namespace if applicable will be maintained \
        on rename eg. namespace:newName
        :type maintainNamespace: bool
        :param mod: Modifier to add the operation to
        :type mod: om2.MDGModifier
        :param apply: Apply the modifier immediately if true, false otherwise
        :type apply: bool
        :return: True if succeeded
        :rtype: bool
        """
        if maintainNamespace:
            currentNamespace = self.namespace()
            if currentNamespace != om2.MNamespace.rootNamespace():
                name = ":".join([currentNamespace, name])
        try:
            nodes.rename(self.object(), name, modifier=mod, apply=apply)
        except RuntimeError:
            logger.error(
                "Failed to rename attribute: {}-{}".format(self.name(), name),
                exc_info=True,
            )
            return False
        return True

    @property
    def isLocked(self):
        """Returns True if the current node is locked, calls upon om2.MFnDependencyNode().isLocked

        :rtype: bool
        """
        return self.mfn().isLocked

    def lock(self, state, mod=None, apply=True):
        """Sets the lock state for this node

        :param state: the lock state to change too.
        :type state: bool
        :param mod: If None then one will be created and doIt will be called immediately
        :type mod: :class:`zapi.dgModifier`
        :param apply: Apply the modifier immediately if true, false otherwise
        :type apply: bool
        :return: True if the node was set
        :rtype: :class:`zapi.dgModifier`
        """
        if self.isLocked != state and self.object():
            modifier = mod or dgModifier()
            try:
                modifier.setNodeLockState(self.object(), state)
            except TypeError:
                raise
            if apply:
                modifier.doIt()
        return mod

    def isReferenced(self):
        """Returns true if this node is referenced.

        :rtype: bool
        """
        return self._mfn.isFromReferencedFile

    def isDefaultNode(self):
        """Returns True if this node is a default Maya node.

        :rtype: bool
        """
        return self._mfn.isDefaultNode

    def mfn(self):
        """Returns the Function set for the node

        :return: either the dag node or dependencyNode depending on the types node
        :rtype: om2.MDagNode or om2.MDependencyNode
        """
        if self._mfn is None and self._node is not None:
            mfn = self._mfnType(self.object())
            self._mfn = mfn
            return mfn

        return self._mfn

    def renameNamespace(self, namespace):
        """Renames the current namespace to the new namespace

        :param namespace: the new namespace eg. myNamespace:subnamespace
        :type namespace: str
        """
        currentNamespace = self.namespace()
        if not currentNamespace:
            return
        parentNamespace = self.parentNamespace()
        # we are at the root namespace so add a new namespace and add our node
        if currentNamespace == ":":
            om2.MNamespace.addNamespace(namespace)
            self.rename(":".join([namespace, self.name()]))
            return
        om2.MNamespace.setCurrentNamespace(parentNamespace)
        om2.MNamespace.renameNamespace(currentNamespace, namespace)
        om2.MNamespace.setCurrentNamespace(namespace)

    def setNotes(self, notes):
        """Sets the note attributes value, if the note attribute doesn't exist it'll be created.

        :param notes: The notes to add.
        :type notes: str
        :return: The note plug.
        :rtype: :class:`Plug`
        """
        note = self.attribute("notes")
        if not note:
            return self.addAttribute("notes", attrtypes.kMFnDataString, value=notes)
        note.setString(notes)
        return note

    def namespace(self):
        """Returns the current namespace for the node

        :return: the nodes namespace
        :rtype: str
        """
        name = om2.MNamespace.getNamespaceFromName(self.fullPathName()).split("|")[-1]
        root = om2.MNamespace.rootNamespace()
        if not name.startswith(root):
            name = root + name
        return name

    def parentNamespace(self):
        """returns the parent namespace from the node

        :return: The parent namespace
        :rtype: str
        """
        namespace = self.namespace()
        if namespace == ":":
            return namespace
        om2.MNamespace.setCurrentNamespace(namespace)
        parent = om2.MNamespace.parentNamespace()

        om2.MNamespace.setCurrentNamespace(namespace)
        return parent

    def removeNamespace(self, modifier=None, apply=True):
        """Removes the namespace from the node

        :param modifier: Modifier to add rename operation too.
        :type modifier: :class:`om2.MDGModifier` or :class:`om2.MDagModifier`
        :param apply: Apply the modifier immediately if true, false otherwise
        :type apply: bool
        :return: True if the namespace was removed
        :rtype: bool
        """
        namespace = self.namespace()
        if namespace:
            return self.rename(
                self.name(includeNamespace=False),
                maintainNamespace=False,
                mod=modifier,
                apply=apply,
            )
        return False

    def delete(self, mod=None, apply=True):
        """Deletes the node from the scene, subclasses should implement this method if the class creates multiple nodes

        :param mod: Modifier to add the delete operation too.
        :type mod: :class:`om2.MDGModifier` or :class:`om2.MDagModifier`
        :param apply: Apply the modifier immediately if true, false otherwise
        :type apply: bool
        :return: True if the node gets deleted successfully
        :rtype: bool
        """
        if not self.exists():
            return False
        if self.isLocked:
            self.lock(False)
        try:
            if mod:
                mod.commandToExecute("delete {}".format(self.fullPathName()))
                if apply:
                    mod.doIt()
            else:
                cmds.delete(self.fullPathName())

            self._mfn = None
            return True
        except RuntimeError:
            logger.error(
                "Failed node deletion,{}".format(self.mfn().name()), exc_info=True
            )
            raise

    def hasAttribute(self, attributeName):
        """Returns True or False if the attribute exists on this node

        :param attributeName: the attribute Name
        :type attributeName: str
        :rtype: bool
        """
        # arrays don't get picked up by hasAttribute unfortunately
        if "[" in attributeName:
            sel = om2.MSelectionList()
            try:
                sel.add(attributeName)
                return True
            except RuntimeError:
                return False
        return self.mfn().hasAttribute(attributeName)

    @lockNodeContext
    def addAttribute(
        self, name, Type=attrtypes.kMFnNumericDouble, shortName=None, mod=None, **kwargs
    ):
        """Helper function to add an attribute to this node

        :param name: the attributeName
        :type name: str
        :param Type: For full support list of types see module zoo.libs.maya.api.attrtypes or None for compound type.
        :type Type: int or None
        :param mod: The MDagModifier to add to, if none it will create one.
        :type mod: om2.MDagModifier
        :return: the MPlug for the new attribute
        :rtype: :class:`Plug`
        """

        if self.hasAttribute(name):
            return self.attribute(name)
        shortName = shortName or name
        children = kwargs.get("children")
        if children:

            plug = self.addCompoundAttribute(name, attrMap=children, mod=mod, **kwargs)
        else:
            node = self.object()
            attr = nodes.addAttribute(
                node, name, shortName, attrType=Type, mod=mod, **kwargs
            )
            plug = Plug(self, om2.MPlug(node, attr.object()))

        return plug

    @lockNodeContext
    def addProxyAttribute(self, sourcePlug, name):
        """Creates a proxy attribute where the created plug on this node will be connected to the source plug
        while still being modifiable.

        :param sourcePlug: The plug to copy to the current node which will become the primary attribute.
        :type sourcePlug: :class:`Plug`
        :param name: The name for the proxy attribute, if the attribute already exists then no proxy will \
        happen.

        :type name: str
        :return: The Proxy Plug instance.
        :rtype: :class:`Plug` or None.
        """
        if self.hasAttribute(name):
            return
        plugData = plugs.serializePlug(sourcePlug.plug())
        plugData["longName"] = name
        plugData["shortName"] = name
        plugData["attrType"] = plugData[
            "Type"
        ]  # todo: convert data to use type_ and update code
        currentObject = self.object()
        return Plug(
            self,
            om2.MPlug(
                currentObject,
                nodes.addProxyAttribute(
                    currentObject, sourcePlug.plug(), **plugData
                ).object(),
            ),
        )

    @lockNodeContext
    def createAttributesFromDict(self, data, mod=None):
        """Creates an attribute on the node given a dict of attribute data

        Data is in the form::

                    {
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
                    }

        :param data: The serialized form of the attribute
        :type data: dict
        :param mod: The MDagModifier to add to, if none it will create one
        :type mod: :class:`om2.MDGModifier`
        :return: A list of created MPlugs
        :rtype: list[:class:`Plug`]
        """
        created = []
        mfn = self._mfn
        mObject = self.object()
        for name, attrData in iter(data.items()):
            # code duplicated out of the self methods to cut some extra calls
            children = attrData.get("children")
            if children:
                compound = nodes.addCompoundAttribute(
                    mObject, name, name, attrMap=children, mod=mod, **attrData
                )
                created.append(Plug(self, om2.MPlug(mObject, compound.object())))
            else:
                if self.hasAttribute(name):
                    created.append(Plug(self, mfn.findPlug(name, False)))
                    continue
                attr = nodes.addAttribute(
                    mObject,
                    name,
                    attrType=attrData.get("Type", None),
                    mod=mod,
                    **attrData
                )
                created.append(Plug(self, om2.MPlug(mObject, attr.object())))
        return created

    @lockNodeContext
    def addCompoundAttribute(
        self, name, attrMap, shortName=None, isArray=False, mod=None, **kwargs
    ):
        """Creates a Compound attribute with the given children attributes.

        :param name: The compound longName
        :type name: str
        :param attrMap: [{"name":str, "type": attrtypes.kType, "isArray": bool}]
        :type attrMap: list(dict())
        :param isArray: Is this compound attribute an array
        :type isArray: bool
        :param mod: The MDagModifier to add to, if none it will create one.
        :type mod: om2.MDagModifier
        :return: The Compound MPlug
        :rtype: :class:`zoo.libs.maya.zapi.base.Plug`

        .. code-block:: python

            attrMap = [{"name": "something", "type": attrtypes.kMFnMessageAttribute, "isArray": False}]
            print attrMap
            # result <OpenMaya.MObject object at 0x00000000678CA790> #

        """
        node = self.object()
        shortName = shortName or name
        compound = nodes.addCompoundAttribute(
            node, name, shortName, attrMap, isArray=isArray, mod=mod, **kwargs
        )
        return Plug(self, om2.MPlug(node, compound.object()))

    def renameAttribute(self, name, newName):
        """Renames an attribute on the current node.

        :param name: The existing attribute to rename.
        :type name: str
        :param newName: The new attribute name, this will be both the short and long names.
        :type newName:  str
        :return: True if complete.
        :rtype: bool
        :raise AttributeError: When the attribute doesn't exist.
        """
        try:
            plug = self.attribute(name)
        except RuntimeError:
            raise AttributeError("No attribute named {}".format(name))
        return plug.rename(newName)

    def deleteAttribute(self, name, mod=None):
        """Remove's the attribute for this node given the attribute name

        :param name: The attribute name
        :type name: str
        :param mod: The MDagModifier to add to, if none it will create one
        :type mod: om2.MDagModifier
        :rtype: bool
        """
        attr = self.attribute(name)
        if attr is not None:
            attr.delete(modifier=mod)
            return True
        return False

    def setAttribute(self, name, value, mod=None, apply=True):
        """Sets the value of the attribute if it exists

        :param name: The attribute name to set
        :type name: str
        :param value: The value to for the attribute, see zoo.libs.maya.api.plugs.setPlugValue
        :type value: maya value type
        :param mod: The MDagModifier to add to, if none it will create one
        :type mod: om2.MDagModifier
        :param apply: Apply the modifier immediately if true, false otherwise
        :type apply: bool
        :return: True if the attribute value was changed.
        :rtype: bool
        """
        attr = self.attribute(name)
        if attr is not None:
            attr.set(value, mod=mod, apply=apply)
            return True
        return False

    def attribute(self, name):
        """Finds the attribute 'name' on the node if it exists

        :param name: the attribute Name
        :type name: str
        :rtype: :class:`Plug` or None
        """
        fn = self._mfn
        if any(i in name for i in ("[", ".")):
            sel = om2.MSelectionList()
            try:
                sel.add(".".join((self.fullPathName(), name)))
                mplug = sel.getPlug(0)
            except RuntimeError:  # raised when the plug doesn't exist.
                return
            return Plug(self, mplug)

        elif fn.hasAttribute(name):
            return Plug(self, fn.findPlug(name, False))

    def setLockStateOnAttributes(self, attributes, state=True):
        """Locks and unlocks the given attributes

        :param attributes: a list of attribute name to lock.
        :type attributes: seq(str)
        :param state: True to lock and False to unlock.
        :type state: bool
        :return: True is successful
        :rtype: bool
        """
        return nodes.setLockStateOnAttributes(self.object(), attributes, state)

    def showHideAttributes(self, attributes, state=True):
        """Shows or hides and attribute in the channel box

        :param attributes: attribute names on the given node
        :type attributes: seq(str)
        :param state: True for show False for hide, defaults to True
        :type state: bool
        :return: True if successful
        :rtype: bool
        """
        fn = self._mfn
        for attr in attributes:
            plug = fn.findPlug(attr, False)
            plug.isChannelBox = state
            plug.isKeyable = state

        return True

    def findAttributes(self, *names):
        """Searches the node for each attribute name provided and returns the plug
        instance.

        :param names:  list of attribute names without the node name
        :type names: iterable[str]
        :return: each element is the matching plug or None if not found.
        :rtype: iterable[:class:`Plug` or None]
        """
        results = [None] * len(names)

        for a in nodes.iterAttributes(self.object()):
            p = Plug(self, a)
            shortName = p.name().partition(".")[-1]
            try:
                results[names.index(shortName)] = p
            except ValueError:
                continue

        return results

    def iterAttributes(self):
        """Generator function to iterate over all the attributes on this node,
        calls on zoo.libs.maya.api.nodes.iterAttributes

        :return: A generator function containing MPlugs
        :rtype: Generator(:class:`Plug`)
        """
        for a in nodes.iterAttributes(self.object()):
            yield Plug(self, a)

    attributes = iterAttributes

    def iterExtraAttributes(
        self, skip=None, filteredTypes=None, includeAttributes=None
    ):
        """Generator function that loops all extra attributes of the node

        :rtype: Generator(:class:`Plug`)
        """
        for a in nodes.iterExtraAttributes(
            self.object(),
            skip=skip,
            filteredTypes=filteredTypes,
            includeAttributes=includeAttributes,
        ):
            yield Plug(self, a)

    def iterProxyAttributes(self):
        """Generator function which returns all proxy attributes on this node.

        :rtype: list[:class:`Plug`]
        """
        for (
            attr
        ) in (
            self.iterAttributes()
        ):  # could be iterExtraAttributes if you only want non default attrs instead
            if attr.isProxy():
                continue
            yield attr

    def iterConnections(self, source=True, destination=True):
        """
        :param source: if True then return all nodes downstream of the node
        :type source: bool
        :param destination: if True then return all nodes upstream of this node
        :type destination: bool
        :return:
        :rtype: generator
        """
        for sourcePlug, destinationPlug in nodes.iterConnections(
            self.object(), source, destination
        ):
            yield Plug(self, sourcePlug), Plug(
                nodeByObject(destinationPlug.node()), destinationPlug
            )

    def sources(self):
        """Generator Function that returns a tuple of connected MPlugs.

        :return: First element is the Plug on this node instance, the second if the connected MPlug
        :rtype: Generator(tuple(:class:`Plug`, :class:`Plug`))
        """
        for source, destination in nodes.iterConnections(
            self.object(), source=True, destination=False
        ):
            yield Plug(self, source), Plug(self, destination)

    def destinations(self):
        """Generator Function that returns a tuple of connected MPlugs.

        :return: First element is the Plug on this node instance, the second if the connected MPlug
        :rtype: Generator(tuple(:class:`Plug`, :class:`Plug`))
        """
        for source, destination in nodes.iterConnections(
            self.object(), source=False, destination=True
        ):
            yield Plug(self, source), Plug(self, destination)

    def connect(self, attributeName, destinationPlug, modifier=None, apply=True):
        """Connects the attribute on this node as the source to the destination plug

        :param attributeName: the attribute name that will be used as the source
        :type attributeName: str
        :param destinationPlug: the destinationPlug
        :type destinationPlug: :class:`Plug`
        :return: True if the connection was made
        :rtype: bool
        :param modifier: The MDagModifier to add to, if none it will create one
        :type modifier: om2.MDagModifier
        :param apply: Apply the modifier immediately if true, false otherwise
        :type apply: bool
        """
        source = self.attribute(attributeName)
        if source is not None:
            return source.connect(destinationPlug, mod=modifier, apply=apply)
        return False

    def connectDestinationAttribute(self, attributeName, sourcePlug):
        """Connects the attribute on this node as the destination to the source plug

        :param attributeName: the attribute name that will be used as the source
        :type attributeName: str
        :param sourcePlug: the sourcePlug to connect to
        :type sourcePlug: :class:`Plug`
        :return: True if the connection was made
        :rtype: bool
        """
        attr = self.attribute(attributeName)
        if attr is not None:
            return sourcePlug.connect(attr)
        return False

    def create(self, name, nodeType, mod=None):
        """Each subclass needs to implement this method to build the node into the application scene
        The default functionality is to create a maya dependencyNode

        :param name: The name of the new node
        :type name: str
        :param nodeType: the maya node type to create
        :type nodeType: str
        :param mod: The MDagModifier to add to, if none it will create one
        :type mod: om2.MDagModifier
        """
        self.setObject(nodes.createDGNode(name, nodeType=nodeType, mod=mod))
        return self

    def serializeFromScene(
        self,
        skipAttributes=(),
        includeConnections=True,
        extraAttributesOnly=False,
        useShortNames=False,
        includeNamespace=True,
    ):
        """This method is to return a dict that is compatible with JSON.

        :param skipAttributes: The list of attribute names to serialization.
        :type skipAttributes: list[str] or None
        :param includeConnections: If True find and serialize all connections where the destination is this node.
        :type includeConnections: bool
        :param extraAttributesOnly: If True then only extra attributes will be serialized
        :type extraAttributesOnly: bool
        :param useShortNames: If True only the short name of nodes will be used.
        :type useShortNames: bool
        :param includeNamespace: Whether to include the namespace as part of the node.
        :type includeNamespace: bool
        :rtype: dict
        """
        try:
            return nodes.serializeNode(
                self.object(),
                skipAttributes=skipAttributes,
                includeConnections=includeConnections,
                extraAttributesOnly=extraAttributesOnly,
                useShortNames=useShortNames,
                includeNamespace=includeNamespace,
            )
        # to protect against maya standard errors
        except RuntimeError:
            return dict()

    @staticmethod
    def sourceNode(plug):
        """Source node of the plug.

        :param plug: Plug to return the source node of
        :type plug: :class:`Plug`
        :return: Either the source node or None if it's not connected.
        :rtype: :class:`DGNode` or None
        """
        source = plug.source()
        return source.node() if source is not None else None

    def sourceNodeByName(self, plugName):
        """Source Node by name

        :param plugName: Name of the plug to return the source node of
        :type plugName: str
        :return:
        :rtype: :class:`DGNode` or None
        """
        plug = self.attribute(plugName)
        if plug is not None:
            return self.sourceNode(plug)


class DagNode(DGNode):
    """Base node for DAG nodes, contains functions for parenting, iterating the Dag etc"""

    _mfnType = om2.MFnDagNode

    def serializeFromScene(
        self,
        skipAttributes=(),
        includeConnections=True,
        includeAttributes=(),
        extraAttributesOnly=True,
        useShortNames=False,
        includeNamespace=True,
    ):
        """This method is to return a dict that is compatible with JSON

        :rtype: dict
        """
        rotationOrder = self.rotationOrder()
        worldMatrix = self.worldMatrix()
        trans, rot, scale = nodes.decomposeMatrix(
            worldMatrix, generic.intToMTransformRotationOrder(rotationOrder)
        )
        try:

            data = nodes.serializeNode(
                self.object(),
                skipAttributes=skipAttributes,
                includeConnections=includeConnections,
                includeAttributes=includeAttributes,
                extraAttributesOnly=extraAttributesOnly,
                useShortNames=useShortNames,
                includeNamespace=includeNamespace,
            )
            data.update(
                {
                    "rotate": tuple(rot),
                    "translate": tuple(trans),
                    "scale": tuple(scale),
                    "rotateOrder": rotationOrder,
                    "matrix": list(self.matrix()),
                    "worldMatrix": list(worldMatrix),
                }
            )
            return data
        # to protect against maya standard errors
        except RuntimeError:
            return dict()

    def create(self, name, nodeType, parent=None, mod=None):
        """Each subclass needs to implement this method to build the node into the application scene
        The default functionality is to create a maya DagNode

        :param name: The name of the new node
        :type name: str
        :param nodeType: the maya node type to create
        :type nodeType: str
        :param parent: The parent object
        :type parent: :class:`om2.MObject`
        :param mod: The MDagModifier to add to, if none it will create one
        :type mod: om2.MDagModifier
        """
        if isinstance(parent, DagNode):
            parent = parent.object()
        n = nodes.createDagNode(name, nodeType=nodeType, parent=parent, modifier=mod)
        self.setObject(n)
        return self

    def dagPath(self):
        """Returns the MDagPath of this node. Calls upon om2.MFnDagNode().getPath()

        :rtype: om2.MDagPath
        """
        return self.mfn().getPath()

    def depth(self):
        """Returns the depth level this node sits within the hierarchy.

        :rtype: int
        """
        return self.fullPathName().count("|") - 1

    def parent(self):
        """Returns the parent nodes as an MObject

        :rtype: om2.MObject or DagNode or None
        """
        obj = self.object()
        if obj is not None:
            parent = nodes.getParent(obj)
            if parent:
                return nodeByObject(parent)
            return parent

    def root(self):
        """Returns the Root DagNode Parent from this node instance

        :rtype: :class:`DagNode`
        """
        return nodeByObject(nodes.getRoot(self.object))

    def child(self, index, nodeTypes=()):
        """Finds the immediate child object given the child index

        :param index: the index of the child to find
        :type index: int
        :param nodeTypes: Node mfn type eg. om2.MFn.kTransform
        :type nodeTypes: tuple(om2.MFn.kType)
        :return: Returns the object as a DagNode instance
        :rtype: :class:`DagNode`
        """

        path = self.dagPath()
        currentIndex = 0
        for i in range(path.childCount()):
            child = path.child(i)
            if (
                not nodeTypes or child.apiType() in nodeTypes
            ) and currentIndex == index:
                return nodeByObject(child)

    def children(self, nodeTypes=()):
        """Returns all the children nodes immediately under this node

        :return: A list of mObjects representing the children nodes
        :rtype: list[:class:`DagNode`]
        """
        path = self.dagPath()
        children = []
        for i in range(path.childCount()):
            child = path.child(i)
            if not nodeTypes or child.apiType() in nodeTypes:
                children.append(nodeByObject(child))
        return children

    def shapes(self):
        """Finds and returns all shape nodes under this dagNode instance

        :rtype: list[:class:`DagNode` | :class:`NurbsCurve` | :class:`Mesh`]
        """
        return list(self.iterShapes())

    def iterShapes(self):
        """Generator function which iterates all shape nodes directly below this node

        :return:
        :rtype: list[:class:`DagNode`]
        """
        path = self.dagPath()
        for i in range(path.numberOfShapesDirectlyBelow()):
            dagPath = om2.MDagPath(path)
            dagPath.extendToShape(i)
            yield nodeByObject(dagPath.node())

    def deleteShapeNodes(self):
        """Deletes all shape nodes on this node."""
        for shape in self.shapes():
            shape.delete()

    def iterParents(self):
        """Generator function to iterate each parent until to root has been reached.

        :rtype: Generator(:class`DagNode`)
        """
        for parent in nodes.iterParents(self.object()):
            yield nodeByObject(parent)

    def iterChildren(self, node=None, recursive=True, nodeTypes=None):
        """kDepthFirst generator function that loops the Dag under this node

        :param node: The maya object to loop under , if none then this node will be used,
        :type node: :class:`DagNode`
        :param recursive: If true then will recursively loop all children of children
        :type recursive: bool
        :param nodeTypes:
        :type nodeTypes: tuple(om2.MFn.kType)
        :return:
        :rtype: collections.Iterable[DagNode or DGNode]
        """
        nodeTypes = nodeTypes or ()
        selfObject = node.object() if node is not None else self.object()

        fn = om2.MDagPath.getAPathTo(selfObject)
        path = fn.getPath()
        for i in range(path.childCount()):
            child = path.child(i)
            if not nodeTypes or child.apiType() in nodeTypes:
                yield nodeByObject(child)
            if recursive:
                for c in self.iterChildren(nodeByObject(child), recursive, nodeTypes):
                    yield c

    def addChild(self, node):
        """Child object to re-parent to this node

        :param: node: the child node
        :type node: :class:`DagNode`
        """
        node.setParent(self)

    def siblings(self, nodeTypes=(kTransform,)):
        """Generator function to return all sibling nodes of the current node.
        This requires this node to have a parent node.

        :param nodeTypes: A tuple of om2.MFn.kConstants
        :type nodeTypes: tuple
        :return:
        :rtype: Generator(:class:`DagNode`)
        """
        parent = self.parent()
        if parent is None:
            return
        for child in parent.iterChildren(recursive=False, nodeTypes=nodeTypes):
            if child != self:
                yield child

    @lockNodeContext
    def setParent(self, parent, maintainOffset=True, mod=None, apply=True):
        """Sets the parent of this dag node

        :param parent: the new parent node
        :type parent: :class:`DagNode` or None
        :param maintainOffset: Whether to maintain its current position in world space.
        :type maintainOffset: bool
        :param mod: The MDagModifier to add to, if none it will create one
        :type mod: om2.MDagModifier
        :param apply: Apply the modifier immediately if true, false otherwise
        :type apply: bool
        :return: The maya MDagModifier either provided via mod argument or a new instance.
        :rtype: :class:`dagModifier`
        """
        parentLock = False
        setLocked = False
        newParent = None
        if parent is not None:
            newParent = parent.object()
            parentLock = parent.isLocked
            if parentLock:
                setLocked = True
                parent.lock(False)
        try:
            result = nodes.setParent(
                self.object(),
                newParent,
                maintainOffset=maintainOffset,
                mod=mod,
                apply=apply,
            )
        finally:
            if setLocked:
                parent.lock(parentLock)
        return result

    def hide(self, mod=None, apply=True):
        """Sets the current node visibility to False

        :param mod: The mdg modifier to use
        :type mod: :class:`om2.MDGModifier` or :class:`om2.MDagModifier`
        :param apply: Apply instantly if true, false otherwise
        :type apply: bool
        :return:
        :rtype: bool
        """
        self.setVisible(False, mod, apply)

    def isHidden(self):
        """Returns whether this node is visible
        :rtype: bool
        """
        return not self._mfn.findPlug("visibility", False).asBool()

    def show(self, mod=None, apply=True):
        """Sets the current node visibility to 1.0

        :param mod: The mdg modifier to use
        :type mod: :class:`om2.MDGModifier` or :class:`om2.MDagModifier`
        :param apply: Apply instantly if true, false otherwise
        :type apply: bool
        :return:
        :rtype: bool
        """
        return self.setVisible(True, mod=mod, apply=apply)

    def setVisible(self, vis, mod=None, apply=True):
        """Set visibility of node

        :param vis: Set visibility on or off
        :type vis: bool
        :param mod: MDG Modifier
        :type mod: :class:`om2.MDGModifier` or :class:`om2.MDagModifier`
        :param apply: Apply immediately or later
        :type apply: bool
        :return:
        :rtype:
        """

        visPlug = self.attribute("visibility")
        if visPlug.isLocked or visPlug.isConnected and not visPlug.isProxy():
            return False
        visPlug.set(vis, mod, apply=apply)
        return True

    def transformationMatrix(self, rotateOrder=None, space=kWorldSpace):
        """Returns the current nodes matrix in the form of a MTransformationMatrix.

        :param rotateOrder: The Rotation order to use. zapi.kRotateOrder_XYZ
        :type rotateOrder: int
        :param space: The coordinate space to use, either kWorldSpace or kObjectSpace
        :type space: :class:`om2.MSpace`
        :return: The maya TransformationMatrix instance
        :rtype: :class:`TransformationMatrix`
        """
        transform = TransformationMatrix(
            self.worldMatrix() if space == kWorldSpace else self.matrix()
        )
        if rotateOrder is None:
            rotateOrder = self.rotationOrder()
        rotateOrder = generic.intToMTransformRotationOrder(rotateOrder)
        transform.reorderRotation(rotateOrder)
        return transform

    def translation(self, space=om2.MSpace.kWorld, sceneUnits=False):
        """Returns the translation for this node.

        :param space: The coordinate system to use
        :type space: om2.MFn.type
        :param sceneUnits: Whether the translation vector needs to be converted to sceneUnits .ie meters \
        Maya stores distances i.e. translation in centimeters regardless on scene units. default False.

        :type sceneUnits: bool
        :return: the object translation in the form om2.MVector
        :rtype: om2.MVector
        """
        return nodes.getTranslation(self.object(), space, sceneUnits=sceneUnits)

    def rotation(self, space=kTransformSpace, asQuaternion=True):
        """Returns the rotation for the node

        :param space: The coordinate system to use
        :type space: om2.MFn.type
        :param asQuaternion: If True then rotations will be return in Quaternion form
        :type asQuaternion: bool
        :return: the rotation in the form of euler rotations
        :rtype: om2.MEulerRotation or om2.MQuaternion
        """
        return nodes.getRotation(self.dagPath(), space, asQuaternion=asQuaternion)

    def scale(self, space=kTransformSpace):
        """Return the scale for this node in the form of a MVector.

        :param space: the coordinate space to retrieve ,either
        :type space: :class:`zapi.MSpace`
        :return: The object scale
        :rtype: :class:`om2.MVector`
        """
        transform = self.transformationMatrix(space=space)
        return Vector(transform.scale(space))

    def setWorldMatrix(self, matrix):
        """Sets the world matrix of this node.

        :param matrix: The world matrix to set
        :type matrix: MMatrix
        """
        nodes.setMatrix(self.object(), matrix, space=om2.MSpace.kWorld)

    def worldMatrix(self, ctx=DGContext.kNormal):
        """Returns the world matrix of this node in the form of MMatrix.

        :param ctx: The MDGContext to use. ie. the current frame.
        :type ctx: :class:`om2.MDGContext`
        :return: The world matrix
        :rtype: :class:`om2.MMatrix`
        """
        wm = self._mfn.findPlug("worldMatrix", False).elementByLogicalIndex(0)
        return om2.MFnMatrixData(wm.asMObject(ctx)).matrix()

    def worldMatrixPlug(self, index=0):
        """Returns the world matrix plug of this node.

        :param index: The index of the world matrix to return.
        :type index: int
        :return: The world matrix plug
        :rtype: :class:`Plug`
        """
        return Plug(
            self, self._mfn.findPlug("worldMatrix", False).elementByLogicalIndex(index)
        )

    def worldInverseMatrixPlug(self, index=0):
        """Returns the world matrix plug of this node, by default returns the first element which
        is typically what you want.

        :param index: The index of the world matrix to return.
        :type index: int
        :return: The world inverse matrix plug.
        :rtype: :class:`Plug`
        """
        return Plug(
            self,
            self._mfn.findPlug("worldInverseMatrix", False).elementByLogicalIndex(
                index
            ),
        )

    def matrix(self, ctx=DGContext.kNormal):
        """Returns the local MMatrix for this node.

        :param ctx: The MDGContext to use. ie. the current frame.
        :type ctx: :class:`om2.MDGContext`
        :rtype: :class:`MMatrix`
        """
        wm = self._mfn.findPlug("matrix", False)
        return om2.MFnMatrixData(wm.asMObject(ctx)).matrix()

    def setMatrix(self, matrix):
        """Sets the local matrix for this node.

        :param matrix: The local matrix to set.
        :type matrix: :class:`om2.MMatrix`
        """
        nodes.setMatrix(self.object(), matrix, space=om2.MSpace.kTransform)

    def parentInverseMatrix(self, ctx=DGContext.kNormal):
        """Returns the parent inverse matrix.

        :param ctx: The MDGContext to use. ie. the current frame.
        :type ctx: :class:`om2.MDGContext`
        :return: the parent inverse matrix
        :rtype: om2.MMatrix
        """
        wm = self._mfn.findPlug("parentInverseMatrix", False)
        return om2.MFnMatrixData(wm.elementByLogicalIndex(0).asMObject(ctx)).matrix()

    def parentInverseMatrixPlug(self, index=0):
        """Returns the parent inverse matrix plug, by default returns the first element which
        is typically what you want.

        :param index: The index of the world matrix to return.
        :type index: int
        :return: The parent inverse matrix Plug instance
        :rtype: :class:`Plug`
        """
        return Plug(
            self,
            self._mfn.findPlug("parentInverseMatrix", False).elementByLogicalIndex(
                index
            ),
        )

    def offsetMatrix(self, targetNode, space=kWorldSpace, ctx=DGContext.kNormal):
        """Returns the offset Matrix between this node and the targetNode.

        :param targetNode: The Target Transform Node to diff.
        :type targetNode: :class:`zapi.DagNode`
        :param space: The coordinate space.
        :type space: om2.MSpace.kWorld
        :param ctx: The MDGContext to use. ie. the current frame.
        :type ctx: :class:`om2.MDGContext`
        """
        return nodes.getOffsetMatrix(
            self.object(), targetNode.object(), space=space, ctx=ctx
        )

    def decompose(self, ctx=DGContext.kNormal):
        """Returns the world matrix decomposed for this node.

        :param ctx: The MDGContext to use. ie. the current frame.
        :type ctx: :class:`om2.MDGContext`
        :rtype: tuple[:class:`om2.MVector`, :class:`om2.MQuaternion`, tuple[float, float, float]]
        """
        return nodes.decomposeMatrix(
            self.worldMatrix(ctx),
            generic.intToMTransformRotationOrder(self.rotationOrder()),
            space=om2.MSpace.kWorld,
        )

    def resetTransform(self, translate=True, rotate=True, scale=True):
        """Resets the local translate, rotate, scale attributes to 0, 0, 0

        :param translate: Whether to reset translate attributes.
        :type translate: bool
        :param rotate: Whether to reset rotate attributes.
        :type rotate: bool
        :param scale: Whether to reset scale attributes.
        :type scale: bool
        """
        translateAttr = self.attribute("translate")
        rotateAttr = self.attribute("rotate")
        scaleAttr = self.attribute("scale")
        if (
            translate
            and not self.translate.isDestination
            and translateAttr.numConnectedChildren() == 0
        ):
            self.setTranslation((0, 0, 0))
        if (
            rotate
            and not self.rotate.isDestination
            and rotateAttr.numConnectedChildren() == 0
        ):
            self.setRotation(Quaternion(), space=kTransformSpace)
        if (
            scale
            and not self.attribute("scale").isDestination
            and scaleAttr.numConnectedChildren() == 0
        ):
            self.setScale((1, 1, 1))

    def resetTransformToOffsetParent(self):
        """Resets the local translate, rotate, scale attributes to the offset parent matrix"""
        parent = self.parent()
        world = self.worldMatrix()
        parentInv = Matrix()
        if parent is not None:
            parentInv = parent.worldMatrix().inverse()
        self.offsetParentMatrix.set(world * parentInv)
        self.resetTransform()

    def setTranslation(self, translation, space=None, sceneUnits=False):
        """Sets the translation component of this control, if cvs is True then translate the cvs instead.

        :param translation: The MVector that represent the position based on the space given. Default False.
        :type translation: :class:`om2.MVector`
        :param space: the space to work on eg.MSpace.kObject or MSpace.kWorld
        :type space: int
        :param sceneUnits: Whether the translation vector needs to be converted to sceneUnits .ie meters \
        Maya stores distances i.e. translation in centimeters regardless on scene units.
        :type sceneUnits: bool
        """
        space = space or kTransformSpace
        nodes.setTranslation(
            self.object(), om2.MVector(translation), space, sceneUnits=sceneUnits
        )

    def setRotation(self, rotation, space=kWorldSpace):
        """Set's the rotation on the transform control using the space.

        :param rotation: the eulerRotation to rotate the transform by
        :type rotation: :class:`om2.MEulerRotation` or :class:`om2.MQuaternion` or seq
        :param space: the space to work on
        :type space: om2.MSpace
        """
        trans = om2.MFnTransform(self._mfn.getPath())
        if isinstance(rotation, Quaternion):
            trans.setRotation(rotation, space)
            return
        elif isinstance(rotation, (tuple, list)):
            if space == kWorldSpace and len(rotation) > 3:
                rotation = om2.MQuaternion(rotation)
            else:
                rotation = om2.MEulerRotation(rotation)
        if space != kTransformSpace and isinstance(rotation, EulerRotation):
            space = kTransformSpace

        trans.setRotation(rotation, space)

    def setScale(self, scale):
        """Applies the specified scale vector to the transform or the cvs

        :type scale: sequence
        """
        trans = om2.MFnTransform(self._mfn.getPath())
        trans.setScale(scale)

    def rotationOrder(self):
        """Returns the rotation order for this node

        :return: The rotation order
        :rtype: int
        """
        return self.rotateOrder.value()

    def setRotationOrder(
        self, rotateOrder=apiconstants.kRotateOrder_XYZ, preserve=True
    ):
        """Sets rotation order for this instance.

        :param rotateOrder: zoo.libs.maya.api.constants.kRotateOrder defaults to XYZ
        :type rotateOrder: int
        :param preserve: Sets the transform's rotation order. \
        If True then the X,Y, Z rotations will be modified \
        so that the resulting rotation under the new order is the same as it \
        was under the old. If False then the X, Y, Z rotations are unchanged.
        :type: bool
        """
        rotateOrder = generic.intToMTransformRotationOrder(rotateOrder)
        trans = om2.MFnTransform(self._mfn.getPath())
        trans.setRotationOrder(rotateOrder, preserve)

    def setPivot(self, vec, type_=("t", "r", "s"), space=None):
        """Sets the pivot point of the object given the MVector

        :param vec: float3
        :type vec: om.MVector
        :param type_: t for translate, r for rotation, s for scale
        :type type_: sequence(str)
        :param space: the coordinate space
        :type space: om2.MSpace
        """
        space = space or om2.MSpace.kObject
        transform = om2.MFnTransform(self._mfn.getPath())
        if "t" in type_:
            transform.setScalePivotTranslation(vec, space)
        if "r" in type_:
            transform.setRotatePivot(vec, space)
        if "s" in type_:
            transform.setScalePivot(vec, space)

    def connectLocalTranslate(self, driven, axis=(True, True, True), force=True):
        """Connect's the local translate plugs to the driven node.

        :param driven: The node that will be driven by the current instance
        :type driven:  :class:`DGNode`
        :param axis: A 3Tuple consisting of bool if True then the translate(element) will be connected
        :type axis: tuple(bool)
        :param force: IF True the connections will be forced by first disconnecting any existing connections.
        :type force: bool
        """
        self.attribute("translate").connect(
            driven.attribute("translate"), axis, force=force
        )

    def connectLocalRotate(self, driven, axis=(True, True, True), force=True):
        """Connect's the local Rotate plugs to the driven node.

        :param driven: The node that will be driven by the current instance
        :type driven:  :class:`DGNode`
        :param axis: A 3Tuple consisting of bool if True then the rotate(element) will be connected
        :type axis: tuple(bool)
        :param force: IF True the connections will be forced by first disconnecting any existing connections.
        :type force: bool
        """
        self.attribute("rotate").connect(driven.attribute("rotate"), axis, force=force)

    def connectLocalScale(self, driven, axis=(True, True, True), force=True):
        """Connect's the local scale plugs to the driven node.

        :param driven: The node that will be driven by the current instance
        :type driven:  :class:`DGNode`
        :param axis: A 3Tuple consisting of bool if True then the scale (element) will be connected
        :type axis: tuple(bool)
        :param force: IF True the connections will be forced by first disconnecting any existing connections.
        :type force: bool
        """
        self.attribute("scale").connect(driven.attribute("scale"), axis, force=force)

    def connectLocalSrt(
        self,
        driven,
        scaleAxis=(True, True, True),
        rotateAxis=(True, True, True),
        translateAxis=(True, True, True),
        force=True,
    ):
        """Connect's the local translate, rotate, scale plugs to the driven node.

        :param driven: The node that will be driven by the current instance
        :type driven: :class:`DGNode`
        :param translateAxis: A 3Tuple consisting of bool if True then the translate(element) will be connected
        :type translateAxis: tuple(bool)
        :param rotateAxis: A 3Tuple consisting of bool if True then the rotate(element) will be connected
        :type rotateAxis: tuple(bool)
        :param scaleAxis: A 3Tuple consisting of bool if True then the rotate(element) will be connected
        :type scaleAxis: tuple(bool)
        :param force: IF True the connections will be forced by first disconnecting any existing connections.
        :type force: bool
        """
        self.connectLocalTranslate(driven, axis=translateAxis, force=force)
        self.connectLocalRotate(driven, axis=rotateAxis, force=force)
        self.connectLocalScale(driven, axis=scaleAxis, force=force)

    def aimToChild(self, aimVector, upVector):
        """Aims this node to first child transform in the hierarchy, if theres no children then the rotation
        we be reset to 0,0,0.

        :param aimVector: The directional vector to aim at the child.
        :type aimVector: :class:`Vector`
        :param upVector: The UpVector.
        :type upVector: :class:`Vector`
        """
        child = self.child(0, nodeTypes=(om2.MFn.kTransform,))
        # if its the leaf then set the rotation to zero, is this ideal?
        if child is None:
            self.setRotation(om2.MQuaternion())
            return
        scene.aimNodes(
            targetNode=child.object(),
            driven=[self.object()],
            aimVector=aimVector,
            upVector=upVector,
        )

    def boundingBox(self):
        """Returns the Bounding information for this node.

        :rtype: :class:`om2.MBoundingBox`
        """
        return self._mfn.boundingBox

    def setShapeColour(self, colour, shapeIndex=None):
        """Sets the color of this node transform or the node shapes.  if shapeIndex is None
        then the transform colour will be set, if -1 then all shapes

        :param colour:
        :type colour: tuple(float)
        :param shapeIndex:
        :type shapeIndex: int or None
        """

        if shapeIndex is not None:
            # do all shapes
            if shapeIndex == -1:
                shapes = nodes.shapes(self.dagPath())
                for shape in iter(shapes):
                    nodes.setNodeColour(shape.node(), colour)
            else:
                shape = nodes.shapeAtIndex(self.object(), shapeIndex)
                nodes.setNodeColour(shape.node, colour)
            return
        if len(colour) == 3:
            nodes.setNodeColour(self.object(), colour)

    connectLocalTrs = connectLocalSrt


class ContainerAsset(DGNode):
    """Maya Asset container class"""

    _mfnType = om2.MFnContainerNode

    def members(self):
        """Returns the current members of this container.

        :rtype: :class:`map[:class:`DGNode`]`
        """
        return map(nodeByObject, self.mfn().getMembers())

    def isCurrent(self):
        """Returns whether this current container is the current active container.

        If True this means all new nodes will automatically be added to this container.

        :rtype: bool
        """
        return self._mfn.isCurrent()

    @contextlib.contextmanager
    def makeCurrentContext(self, value):
        """Context manager "with" which makes this container temporarily active.

        :param value: Active state.
        :type value: bool
        """
        currentState = self.isCurrent()

        if currentState == value:
            yield
        else:
            try:
                self.makeCurrent(value)
                yield
            finally:
                self.makeCurrent(currentState)

    def makeCurrent(self, value):
        """Set this container to be currently active.

        :param value: Whether to make the container currently active
        :type value: bool
        """
        self._mfn.makeCurrent(value)

    @property
    def blackBox(self):
        """Returns the current black box attribute value

        :return: True if the contents of the container is public
        :rtype: bool
        """
        return self.attribute("blackBox").asBool()

    @blackBox.setter
    def blackBox(self, value):
        """Set the current black box attribute value

        :param value: boolean
        :type value: bool
        """
        mfn = self.mfn()
        if not mfn:
            return
        self.attribute("blackBox").set(value)

    def setObject(self, mObject):
        """Set's the MObject For this :class:`DGNode` instance

        :param mObject: The maya api om2.MObject representing a MFnDependencyNode
        :type mObject: om2.MObject
        """
        if not mObject.hasFn(om2.MFn.kDependencyNode):
            raise ValueError(
                "Invalid MObject Type {}".format(
                    om2.MFnDependencyNode(mObject).typeName
                )
            )
        self._node = om2.MObjectHandle(mObject)
        self._mfn = self._mfnType(mObject)

    def create(self, name, parent=None):
        """Creates the MFn Container node and sets this instance MObject to the new node

        :param name: the name for the container
        :type name: str
        :return: Instance to self
        :rtype: :class:`ContainerAsset`
        """
        container = nodes.createDGNode(name, "container")
        self.setObject(container)
        return self

    def addNodes(self, objects, force=False):
        """Adds the provided nodes to the container without publishing them

        :param objects:  The nodes the add to this container
        :type objects: list[:class:`DGNode`]
        :param force: If True then nodes will be disconnected from their current containers before they are added.
        :type force: bool
        """
        containerPath = self.fullPathName(False, True)

        for i in iter(objects):
            if i == self:
                continue
            cmds.container(
                containerPath,
                e=True,
                addNode=i.fullPathName(),
                includeHierarchyBelow=True,
                force=force,
            )

    def addNode(self, node, force=False):
        """Adds the provided node to the container without publishing it.

        :param node:  The node the add to this container
        :type node: :class:`DGNode`
        :param force: If True then nodes will be disconnected from their current containers before they are added.
        :type force: bool
        """
        mObject = node.object()
        if mObject != self._node.object():
            try:
                cmds.container(
                    self.fullPathName(),
                    e=True,
                    addNode=node.fullPathName(),
                    includeHierarchyBelow=True,
                    force=force,
                )
            except RuntimeError:
                raise
            return True
        return False

    def publishAttributes(self, attributes):
        """Publishes the provided attributes to the container.

        :param attributes: The attributes to publish to this containers interface.
        :type attributes: list[:class:`Plug`]
        """
        containerName = self.fullPathName()
        currentPublishes = self.publishedAttributes()
        for plug in attributes:
            # ignore already publish attributes and plugs which are children/elements
            if plug in currentPublishes or plug.isChild or plug.isElement:
                continue
            name = plug.name()
            shortName = plug.partialName()
            try:
                cmds.container(
                    str(containerName),
                    edit=True,
                    publishAndBind=[str(name), str(shortName)],
                )
            except RuntimeError:
                pass

    def publishAttribute(self, plug):
        """Publishes the provided plug to the container.

        :param plug: The plug to publish
        :type plug: :class:`Plug`
        """
        self.publishAttributes([plug])

    def publishNode(self, node):
        """Publishes the given node to the container.

        :param node: The Node to publish.
        :type node: :class:`DGNode`
        """
        containerName = self.fullPathName()
        nodeName = node.fullPathName()
        shortName = nodeName.split("|")[-1].split(":")[-1]
        try:
            cmds.containerPublish(
                containerName, publishNode=[shortName, node.mfn().typeName]
            )
        except RuntimeError:
            pass
        try:
            cmds.containerPublish(containerName, bindNode=[shortName, nodeName])
        except RuntimeError:
            pass

    def publishNodes(self, publishNodes):
        """Publishes the given nodes to the container.

        :param publishNodes: The Nodes to publish.
        :type publishNodes: list[:class:`DGNode`]
        """
        for i in iter(publishNodes):
            self.publishNode(i)

    def publishNodeAsChildParentAnchor(self, node):
        """Publishes the node as child and parent anchor to container.

        :param node: node to be published as child and parent anchor
        :type node: class object
        """
        nodeName = node.fullPathName()
        shortName = nodeName.split("|")[-1].split(":")[-1]
        parentName = "_".join([shortName, "parent"])
        childName = "_".join([shortName, "child"])
        containerName = self.fullPathName()
        cmds.container(containerName, e=True, publishAsParent=(nodeName, parentName))
        cmds.container(containerName, e=True, publishAsChild=(nodeName, childName))

    def setParentAncher(self, node):
        """Set the node as a parent anchor to the container.

        :param node: node to be set as parent anchor
        :type node: class object
        """
        nodeName = node.fullPathName()
        shortName = nodeName.split("|")[-1].split(":")[-1]
        parentName = "_".join([shortName, "parent"])
        containerName = self.fullPathName()
        cmds.container(containerName, e=True, publishAsParent=(nodeName, parentName))

    def setChildAnchor(self, node):
        """Sets the specified child node as the anchor for the container asset.

        :param node: The child node to set as the anchor.
        :type node: :class:`DagNode`
        """
        nodeName = node.fullPathName()
        shortName = nodeName.split("|")[-1].split(":")[-1]
        childName = "_".join([shortName, "child"])
        containerName = self.fullPathName()
        cmds.container(containerName, e=True, publishAsChild=(nodeName, childName))

    def childAnchor(self):
        """Gets the child anchor node of the ContainerAsset.

        :return: The child anchor node.
        :rtype: :class:`DGNode`
        """
        child = cmds.container(self.fullPathName(), q=True, publishAsChild=True)
        if child:
            return nodeByName(child[1])

    def parentAnchor(self):
        """This method returns the parent anchor of a ContainerAsset.

        :return: The parent anchor of the ContainerAsset.
        :rtype: :class:`DGNode`
        """
        parent = cmds.container(self.fullPathName(), q=True, publishAsParent=True)
        if parent:
            return nodeByName(parent[1])

    def unPublishAttributes(self):
        """Unpublishes the attributes of the ContainerAsset."""
        for p in self.publishedAttributes():
            self.unPublishAttribute(p.partialName(useLongNames=False))

    def unPublishAttribute(self, attributeName):
        """Removes the specified attribute from being published as an input or output on the node's container.

        :param attributeName: Name of the attribute to be unpublished, exclude the node name.
        :type attributeName: str
        :return: returns True if the attribute is successfully unpublished, False otherwise
        :rtype: bool
        """
        containerName = self.fullPathName()
        try:
            cmds.container(
                containerName,
                e=True,
                unbindAndUnpublish=".".join([containerName, attributeName]),
            )
        except RuntimeError:
            return False
        return True

    def unPublishNode(self, node):
        """Remove a node from the container and break any connections to other published attributes.

        :param node: The node to be removed
        :type node: :class:`DGNode`
        """
        messagePlug = node.attribute("message")
        containerName = self.fullPathName()
        for destPlug in messagePlug.destinations():
            node = destPlug.node().object()
            if node.hasFn(om2.MFn.kContainer):
                parentName = destPlug.parent().partialName(useAlias=True)
                cmds.containerPublish(containerName, unbindNode=parentName)
                cmds.containerPublish(containerName, unpublishNode=parentName)
                break

    def removeUnboundAttributes(self):
        """Remove any unbound attributes from the container"""
        containerName = self.fullPathName()
        for unbound in (
            cmds.container(containerName, q=True, publishName=True, unbindAttr=True)
            or []
        ):
            cmds.container(containerName, e=True, unpublishName=unbound)

    def subContainers(self):
        """Returns a Generator containing all sub containers.

        :rtype: list[:class:`Container`]
        """
        return map(nodeByObject, self.mfn().getSubcontainers())

    getSubContainers = subContainers

    def publishedNodes(self):
        """Returns a list of node objects that are published by the current container node.

        :rtype: list[:class:`DGNode` or :class:`DagNode`]
        """
        return [
            nodeByObject(node[1])
            for node in self.mfn().getPublishedNodes(om2.MFnContainerNode.kGeneric)
            if not node[0].isNull()
        ]

    def publishedAttributes(self):
        """Returns a list of attribute plugs that are published by the current container node.

        :rtype: :class:`Plug`
        """
        # using cmds here instead of mfn.getPublishedPlugs as for some odd reason crashes OSX in maya 2020 only
        # when access mfn methods like .name()
        results = cmds.container(self.fullPathName(), query=True, bindAttr=True)
        # because cmds returns a None type instead of the empty list.
        if not results:
            return []
        # cmds returns a flat list of attribute name, published name so we chunk as pairs
        return [plugByName(attr) for attr, _ in generalutils.chunks(results, 2)]

    def serializeFromScene(
        self,
        skipAttributes=(),
        includeConnections=True,
        includeAttributes=(),
        useShortNames=False,
        includeNamespace=False,
    ):
        members = self.members()
        publishAttributes = self.publishedAttributes()
        publishedNodes = self.publishedNodes()
        if not members:
            return {}
        return {
            "graph": scene.serializeNodes(members),
            "attributes": publishAttributes,
            "nodes": publishedNodes,
        }

    def delete(self, removeContainer=True):
        """Deletes the current container

        :param removeContainer: If True then the container will be deleted, false and the members will \
        be removed but the container won't be deleted.

        :type removeContainer: bool
        """
        containerName = self.fullPathName()
        self.lock(False)
        cmds.container(containerName, edit=True, removeContainer=removeContainer)


class ObjectSet(DGNode):
    """Maya Object Set Wrapper Class"""

    _mfnType = om2.MFnSet

    def create(self, name, mod=None, members=None):
        """Creates the MFnSet node and sets this instance MObject to the new node

        :param name: the name for the ObjectSet
        :type name: str
        :param mod: The MDagModifier to add to, if none it will create one
        :type mod: om2.MDagModifier
        :param members: A list of nodes to add as members
        :type members: list[:class:`DGNode`]
        :return: Instance to self
        :rtype: :class:`ContainerAsset`
        """
        obj = nodes.createDGNode(name, "objectSet", mod=mod)
        self.setObject(obj)
        if members is not None:
            self.addMembers(members)
        return self

    def addMember(self, node):
        """Add a new Node to the set.

        :param node: The Node to add as a new member to this set.
        :type node: :class:`DGNode`
        :return: True if the node was added, False if not. usually False if the provided node doesn't exist
        """
        if not node.exists():
            return False
        elif node.hasFn(kDagNode):
            if self in node.instObjGroups[0].destinationNodes():
                return False
            node.instObjGroups[0].connect(
                self.dagSetMembers.nextAvailableDestElementPlug()
            )
        else:
            if self in node.attribute("message").destinationNodes():
                return False
            node.message.connect(self.dnSetMembers.nextAvailableDestElementPlug())

        return True

    def addMembers(self, newMembers):
        """Add a list of new objects to the set.

        :param newMembers: A list of Nodes to add as new members to this set.
        :type newMembers: iterable[:class:`DGNode`]
        """
        # mfn.addMembers is not the same as manually connecting the instObjGroups ie. it doesn't
        # correctly handle Dag objects
        # seems to me that MFnSet is pretty badly implemented
        for n in newMembers:
            self.addMember(n)

    def isMember(self, node):
        """Returns true if the given object is a member of this set.

        :param node: The Node to check for membership
        :type node: :class:`DGNode`
        :return: Returns true if the given object is a member of this set.

        :rtype: bool
        """
        if not node.exists():
            return False
        return self._mfn.isMember(self.object())

    def members(self, flatten=False):
        """Get the members of this set as a list.

        It is possible to ask for the returned list to be flattened.
        This means that all sets that exist inside this set will be expanded into a list of their contents.

        :param flatten: whether to flatten the returned list.
        :type flatten: bool
        :return: A list of all members in this set, if flatten is True then the result will contain \
        it's child sets members as well.

        :rtype: list[:class:`DGNode`]
        """
        members = self._mfn.getMembers(flatten).getSelectionStrings()

        return list(map(nodeByName, members))

    def union(self, otherSets):
        """This method calculates the union of two or more sets.

        The result will be the union of this set and the set passed into the method.

        :param otherSets: The other ObjectSets to unionize.
        :type otherSets: list[:class:`ObjectSet`]
        :return: union of this set and the set passed into the method.
        :rtype: list[:class:`DGNode`]
        """
        result = self._mfn.getUnion(
            [i.object() for i in otherSets if i.exists()]
        ).getSelectionStrings()
        return list(map(nodeByName, result))

    def intersectsWith(self, otherSet):
        """Returns true if this set intersects with the given set.

        An intersection occurs if there are any common members between the two sets.

        :param otherSet: The other ObjectSet to intersect.
        :type otherSet: :class:`ObjectSet`
        :return: True if the other ObjectSet intersects
        :rtype: bool
        """
        return self._mfn.intersectsWith(otherSet.object())

    def removeMember(self, member):
        """Remove an object from the set.

        :param member: The Member node to remove
        :type member: :class:`DGNode`
        """
        if member.exists():
            self.removeMembers(
                [member]
            )  # removeMember Raises a Runtime while removeMembers work. BUG?

    def removeMembers(self, members):
        """Remove items of the list from the set.

        :param members: The member nodes to remove
        :type members: list[:class:`DGNode`]
        """
        memberList = om2.MSelectionList()
        for member in members:
            if member.exists():
                memberList.add(member.fullPathName())
        self._mfn.removeMembers(memberList)

    def clear(self):
        """Removes all members from this ObjectSet"""
        self._mfn.clear()

    def intersection(self, otherSet):
        """This method calculates the intersection of two sets.

        The result will be the intersection of this set and the set passed into the method.

        :param otherSet: The other ObjectSet instance to intersect
        :type otherSet: :class:`ObjectSet`
        :return: Resulting list of intersected members
        :rtype: list[:class:`DGNode`]
        """
        if otherSet.exists():
            return self._mfn.getIntersection(otherSet.object())
        return False

    def parent(self):
        """Returns the parent ObjectSet

        :return: The Attached parent object
        :rtype: :class:`ObjectSet` or None
        """
        for n in self.attribute("message").destinationNodes():
            if isinstance(n, ObjectSet):
                return n

    def memberSets(self, flatten=False):
        """Returns the child objectSets.

        :param flatten: If True then this functions recursively walks through the hierarchy
        :type flatten: bool
        :return: A list of object sets which have this set as it's parent
        :rtype: list[:class`ObjectSet`]
        """
        members = self.members(flatten)
        objectSets = []
        for member in members:
            if isinstance(member, ObjectSet):
                objectSets.append(member)
        return objectSets

    getIntersection = intersection
    getMembers = members
    getUnion = union


class BlendShape(DGNode):
    """Abstracts maya's blendShape node and adds some high level functionality"""

    def primaryBaseObject(self):
        """Returns the primary driven mesh object ie. the first shape.

        :rtype: :class:`DagNode`
        """
        objs = list(self.baseObjects())
        if objs:
            return objs[0]

    def baseObjects(self):
        """Generator functions which returns all current base objects

        :rtype: Iterable[:class:`DagNode`
        """
        geomPlug = self.attribute("outputGeometry")
        for element in geomPlug:
            if not element.isConnected:
                continue
            destinations = element.destinationNodes()
            for n in destinations:
                yield n

    def targetCount(self):
        """Returns the total number of target shapes.

        :rtype: int
        """
        return len(list(self.targets()))

    def envelope(self):
        """Returns the envelope attributes value.

        :rtype: float
        """
        return float(self.attribute("envelope"))

    def setEnvelope(self, value):
        """Sets the blender envelope value.

        :param value: envelope value.
        :type value: float
        :return: whether setting the value succeeded.
        :rtype: bool
        """
        return self.attribute("envelope").set(value)

    def renameTarget(self, name, newName):
        """Renames the target weight alias to the new Name.

        :param name: The current weight name i.e. browUp
        :type name: str
        :param newName: The newName from the weight, Any space will be converted to "_"
        :type newName: str
        :return: The new Name which was created.
        :rtype:  str
        """
        newName = newName.replace(" ", "_")
        idx = self.targetIdxByName(name)
        plug = self.attribute("weight")[idx]
        self._mfn.setAlias(newName, "weight[{}]".format(idx), plug.plug())
        return newName

    def iterTargetIndexPairs(self):
        """Iterates over the target index pairs of the BlendShape node.

        :return: A generator that yields each target index pair as a tuple containing the alias and index.
        :rtype: generator
        """
        weightArrayPlug = self._mfn.getAliasList()
        for alias, plugName in weightArrayPlug:
            yield alias, int(plugName.split("weight[")[-1][:-1])

    def targets(self, baseObjectIndex=0):
        """returns the mesh object for all connected targets"""
        inputTargetGroup = (
            self.attribute("inputTarget")
            .elementByPhysicalIndex(baseObjectIndex)
            .child(0)
        )
        targets = set()
        for targetBasePlug in inputTargetGroup:
            inputTargetItem = targetBasePlug.child(0)
            for i in inputTargetItem:
                targetItemPlug = i.child(0)
                targetNode = targetItemPlug.sourceNode()
                if targetNode in targets:
                    continue
                yield targetNode
                targets.add(targetNode)

    def targetGroupPlug(self, targetIndex, baseObjectIndex=0):
        """Method to get the target group plug of a blend shape node.

        :param targetIndex: The index of the target group.
        :type targetIndex: int
        :param baseObjectIndex: The index of the base object (default is 0).
        :type baseObjectIndex: int
        :return: The target group plug.
        :rtype: maya.api.OpenMaya.MPlug
        """
        inputTargetGroup = (
            self.attribute("inputTarget")
            .elementByPhysicalIndex(baseObjectIndex)
            .child(0)
        )
        if targetIndex < len(inputTargetGroup):
            return inputTargetGroup.elementByPhysicalIndex(targetIndex)

    def targetInbetweenPlug(self, targetIndex, logicalIndex, baseObjectIndex=0):
        """Returns the plug representing the in-between value for the target item.

        :param targetIndex: The index of the target shape in the blend shape node.
        :type targetIndex: int
        :param logicalIndex: The logical index of the target item in the target shape.
        :type logicalIndex: int
        :param baseObjectIndex: The index of the base object in the blend shape node. Default is 0.
        :type baseObjectIndex: int
        :return: The plug representing the in-between value for the target item.
        :rtype: :class:`om2.MPlug`
        """
        targetItemGroup = self.targetGroupPlug(targetIndex, baseObjectIndex).child(0)
        indices = targetItemGroup.getExistingArrayAttributeIndices()
        if logicalIndex in indices:
            return targetItemGroup.elementByLogicalIndex(logicalIndex)

    def targetIdxByName(self, name):
        """Get the index of a target by its name.

        :param name: The name of the target.
        :type name: str
        :return: The index of the target.
        :rtype: int
        :raises AttributeError: If the target doesn't exist.
        """
        name = name
        for alias, idx in self.iterTargetIndexPairs():
            if alias == name:
                return idx
        raise AttributeError("target doesn't exist")

    def targetInbetweenName(self, targetIndex, logicalIndex):
        """Returns the target in-between name for the given target index and logical index.

        :param targetIndex: The index of the target
        :type targetIndex: int
        :param logicalIndex: The logical index of the inbetween
        :type logicalIndex: int
        :return: The name of the inbetween
        :rtype: str
        """
        infoGroupPlug = self.attribute("inbetweenInfoGroup")
        existingInbetweenIndices = infoGroupPlug.getExistingArrayAttributeIndices()
        if targetIndex in existingInbetweenIndices:
            inbetweenInfoPlug = infoGroupPlug.elementByLogicalIndex(targetIndex).child(
                0
            )
            inbetweenLogicalIndices = (
                inbetweenInfoPlug.getExistingArrayAttributeIndices()
            )
            if logicalIndex in inbetweenLogicalIndices:
                namePlug = inbetweenInfoPlug.elementByLogicalIndex(logicalIndex).child(
                    1
                )
                return namePlug.asString()
        return ""

    def targetIndexWeights(self, targetIndex, baseObjectIndex=0):
        """Returns the target index weights for a given target index and base object index.

        :param targetIndex: The index of the target.
        :type targetIndex: int
        :param baseObjectIndex: The index of the base object. Default is 0.
        :type baseObjectIndex: int
        :return: The target index weights.
        :rtype: generator
        """
        groupPlug = self.targetGroupPlug(targetIndex, baseObjectIndex)
        inputTargetItemPlug = groupPlug.child(0)
        for plug in inputTargetItemPlug:
            yield (plug.logicalIndex() - 5000) * 0.001

    def targetWeights(self):
        """
        Returns the target weights of the blend shape node.

        :return: A generator that yields tuples containing the logical index and weight of each target weight plug.
        :rtype: generator[int, float]
        """
        weightPlug = self._mfn.findPlug("weight", False)
        for plug in weightPlug:
            yield plug.logicalIndex(), plug.asFloat()

    def targetPaintWeights(self, targetIndex, baseObjectIndex=0):
        """Returns the paint weights for a given target index and base object index.

        :param targetIndex: Index of the target shape.
        :type targetIndex: int
        :param baseObjectIndex: Index of the base object.
        :type baseObjectIndex: int
        :return: A set of weight indices and their associated float values.
        :rtype: set
        """
        groupPlug = self.targetGroupPlug(targetIndex, baseObjectIndex)
        weightArray = groupPlug.child(1)
        weights = set()
        for i in weightArray.getExistingArrayAttributeIndices():
            weights.add((i, weightArray[i].asFloat()))

        return weights

    def basePaintWeights(self, baseObjectIndex=0):
        """Returns the paint weights for a given base object index.

        :param baseObjectIndex: The index of the base object to paint weights for.
        :type baseObjectIndex: int
        :return: A set of tuples containing the weight index and weight value.
        :rtype: set
        """
        inputTargetPlug = self._mfn.findPlug(
            "inputTarget", False
        ).elementByPhysicalIndex(baseObjectIndex)
        weightsPlug = inputTargetPlug.child(1)
        weights = set()
        for i in weightsPlug.getExistingArrayAttributeIndices():
            weights.add((i, weightsPlug[i].asFloat()))
        return weights

    def setTargetInbetweenName(self, name, targetIndex, logicalIndex):
        """Sets the name of the target inbetween.

        :param name: The name of the target inbetween to set
        :type name: str
        :param targetIndex: The index of the target in the inbetween array
        :type targetIndex: int
        :param logicalIndex: The logical index of the inbetween to set
        :type logicalIndex: int
        :return: An empty string indicating success
        :rtype: str
        """
        infoGroupPlug = self._mfn.findPlug("inbetweenInfoGroup", False)
        existingInbetweenIndices = infoGroupPlug.getExistingArrayAttributeIndices()
        if targetIndex in existingInbetweenIndices:
            inbetweenInfoPlug = infoGroupPlug.elementByLogicalIndex(targetIndex).child(
                0
            )
            inbetweenLogicalIndices = (
                inbetweenInfoPlug.getExistingArrayAttributeIndices()
            )
            if logicalIndex in inbetweenLogicalIndices:
                namePlug = inbetweenInfoPlug[logicalIndex].child(1)
                namePlug.setString(name)
        return ""

    def setTargetWeights(self, weightList):
        """Sets the target weights for the blend shape node.

        :param weightList: A list of tuples containing index and weight values to set for the target weights.
        :type weightList: list[tuple]
        """
        weightPlug = self._mfn.findPlug("weight", False)
        logicalIndices = weightPlug.getExistingArrayAttributeIndices()
        if not logicalIndices:
            return
        for idx, value in weightList:
            if idx in logicalIndices:
                weightPlug.elementByLogicalIndex(idx).setFloat(value)

    def setTargetWeightValue(self, targetIndex, value):
        """Sets the target weight value for the given target index.

        :param targetIndex: Index of the target weight to set.
        :type targetIndex: int
        :param value: Value to set the target weight to.
        :type value: float
        """
        weightPlug = self._mfn.findPlug("weight", False)
        if targetIndex in range(weightPlug.evaluateNumElements()):
            targetPlug = weightPlug.elementByPhysicalIndex(targetIndex)
            if not targetPlug.isDefaultValue():
                weightPlug.elementByLogicalIndex(targetIndex).setFloat(value)

    def setBasePaintWeights(self, weightList, baseObjectIndex=0):
        """Set the paint weights for the base object in the blend shape node.

        :param weightList: The list of weights to set. Each item in the list should be a tuple containing the index and value of the weight.
        :type weightList: list(tuple(int, float))
        :param baseObjectIndex: The index of the base object in the blend shape node. Defaults to 0.
        :type baseObjectIndex: int
        """
        inputTargetPlug = self._mfn.findPlug(
            "inputTarget", False
        ).elementByPhysicalIndex(baseObjectIndex)
        weightsPlug = inputTargetPlug.child(1)
        for index, value in weightList:
            weightsPlug = weightsPlug.elementByLogicalIndex(index)
            weightsPlug.setFloat(value)

    def setTargetPaintWeights(self, weightList, targetIndex, baseObjectIndex=0):
        """This method sets the paint weights for the specified target index and base object index in
        the blend shape node. The paint weights are provided as a list of tuples,
        where each tuple contains the weight index and value to set.
        The weight index represents the specific vertex or control point to set the weight on,
        and the value represents the weight value to set.

        :param weightList: A list of tuples containing the weight index and value to set.
        :type weightList: list[(int, float)]
        :param targetIndex: The index of the target blend shape node.
        :type targetIndex: int
        :param baseObjectIndex: The index of the base object. Default is 0.
        :type baseObjectIndex: int

        Example usage:

        .. code-block:: python

            # Assuming 'blendShapeNode' is a valid 'BlendShape' object
            blendShapeNode.setTargetPaintWeights([(0, 1.0), (1, 0.8), (2, 0.2), ...], 0, 0)

        """
        groupPlug = self.targetGroupPlug(targetIndex, baseObjectIndex)
        weightArray = groupPlug.child(1)
        for index, value in weightList:
            weightsPlug = weightArray.elementByLogicalIndex(index)
            weightsPlug.setFloat(value)


class NurbsCurve(DagNode):
    """Wrapper class for OpenMaya Api 2.0 MFnNurbsCurve function set providing
    common set of methods.
    """

    _mfnType = om2.MFnNurbsCurve

    def length(self, tolerance=om2.MFnNurbsCurve.kPointTolerance):
        """Returns the arc length of this curve or 0.0 if it cannot be computed.

        :param tolerance: Max error allowed in the calculation.
        :type tolerance: float
        :rtype: float
        """
        return self._mfn.length(tolerance)

    def cvPositions(self, space=kObjectSpace):
        """Returns the positions of all the curve's control vertices.

        :param space: A MSpace constant giving the coordinate space in which the point is given.
        :type space: int
        :rtype: :class:`om2.MPointArray`
        """
        return self._mfn.cvPositions(space)

    def setCVPositions(self, points, space=kObjectSpace):
        """Sets the positions of all the curve's control vertices.

        :param points: The positions to set.
        :type points: :class:`om2.MPointArray`
        :param space: A MSpace constant giving the coordinate space in which the point is given.
        :type space: int
        """
        self._mfn.setCVPositions(points, space)


class Mesh(DagNode):
    """Wrapper class for OpenMaya Api 2.0 MFnMesh function set providing
    common set of methods.
    """

    _mfnType = om2.MFnMesh

    def assignedUVs(self, uvSet):
        """Returns a tuple containing all the UV assignments for the specified
        UV set.

        The first element of the returned tuple is an array of counts giving
        the number of UVs assigned to each face of the mesh. The count will
        either be zero, indicating that that face's vertices do not have UVs
        assigned, or else it will equal the number of the face's vertices.
        The second element of the tuple is an array of UV IDs for all the
        face-vertices which have UVs assigned.

        :param uvSet: The UvSet to return the Uvs for.
        :type: uvSet: str
        :rtype: tuple[list[int], list[int]]
        """
        return self._mfn.getAssignedUVs(uvSet=uvSet)


class Camera(DagNode):
    """Wrapper class for OpenMaya Api 2.0 MFnCamera function set providing
    common set of methods.
    """

    _mfnType = om2.MFnCamera

    def aspectRatio(self):
        """Returns the aspect ratio for the camera.

        :rtype: float
        """
        return self._mfn.aspectRatio()

    def centerOfInterestPoint(self, space=kObjectSpace):
        """Returns the center of interest point for the camera.

        :param space: Specifies the coordinate system for this operation.
        :type space: int
        :rtype: :class:`om2.MPoint`
        """
        return self._mfn.centerOfInterestPoint(space)

    def eyePoint(self, space=kObjectSpace):
        """Returns the eye point for the camera.

        :param space: Specifies the coordinate system for this operation
        :type space: int
        :rtype: :class:`om2.MPoint`
        """
        return self._mfn.eyePoint(space)

    def aspectRatioLimits(self):
        """Returns the minimum and maximum aspect ratio limits for the camera.

        :rtype tuple[float, float]
        """
        return self._mfn.getAspectRatioLimits()

    def filmApertureLimits(self):
        """Returns the maximum and minimum film aperture limits for the camera.

        :rtype: tuple[float, float]
        """
        return self._mfn.getFilmApertureLimits()

    def filmFrustum(self, distance, applyPanZoom=False):
        """Returns the film frustum for the camera (horizontal size, vertical size, horizontal offset and
        vertical offset). The frustum defines the projective transformation.

        :param distance: Specifies the focal length.
        :type distance: float
        :param applyPanZoom: Specifies whether to apply 2D pan/zoom.
        :type applyPanZoom: bool
        :rtype: tuple[float, float, float, float]
        """
        return self._mfn.getFilmFrustum(distance, applyPanZoom)

    def filmFrustumCorners(self, distance, applyPanZoom=False):
        """Returns the film frustum for the camera. The frustum defines the projective transformation.

         element 0 is the bottom left
         element 1 is the top left
         element 2 is the top right
         element 3 is the bottom right

        :param distance Specifies the focal length.
        :type distance: float
        :param applyPanZoom specifies whether to apply 2D pan/zoom.
        :type applyPanZoom: bool

        :rtype: :class:`om2.MPointArray`
        """
        return self._mfn.getFilmFrustumCorners(distance, applyPanZoom)

    def focalLengthLimits(self):
        """Returns the maximum and minimum focal length limits for the camera.

        :rtype: tuple[float, float]
        """
        return self._mfn.getFocalLengthLimits()

    def portFieldOfView(self, width, height):
        """Returns the horizontal and vertical field of view in radians from the given viewport width and height.

        :param width: width of viewport.
        :type width: int
        :param height: height of viewport.
        :type width: int
        :rtype: tuple[float, float]
        """
        return self._mfn.getPortFieldOfView(width, height)

    def renderingFrustum(self, windowAspect):
        """Returns the rendering frustum (left, right, bottom and top) for the camera.
        This is the frustum that the maya renderer uses.

        :param windowAspect: windowAspect.
        :type windowAspect: float
        :rtype: tuple[float, float, float, float]
        """
        return self._mfn.getRenderingFrustum(windowAspect)

    def viewParameters(
        self, windowAspect, applyOverscan=False, applySqueeze=False, applyPanZoom=False
    ):
        """Returns the intermediate viewing frustum (apertureX, apertureY, offsetX and offsetY)
        parameters for the camera.

        The aperture and offset are used by getViewingFrustum() and getRenderingFrustum()
        to compute the extent (left, right, top, bottom) of the frustum in the following manner::

             left = focal_to_near * (-0.5*apertureX + offsetX)
             right = focal_to_near * (0.5*apertureX + offsetX)
             bottom = focal_to_near * (-0.5*apertureY + offsetY)
             top = focal_to_near * (0.5*apertureY + offsetY)

        Here, focal_to_near is equal to cameraScale if the camera is orthographic,
        or it is equal to ((nearClippingPlane / (focalLength * MM_TO_INCH)) * cameraScale)
        where MM_TO_INCH equals 0.03937.
        :param windowAspect: windowAspect.
        :type windowAspect: float
        :param applyOverscan Specifies whether to apply overscan.
        :type applyOverscan: bool
        :param applySqueeze Specifies whether to apply the lens squeeze ratio of the camera.
        :type applySqueeze: bool
        :param applyPanZoom Specifies whether to apply 2D pan/zoom.
        :type applyPanZoom: bool
        :rtype: tuple[float, float, float, float]
        """
        return self._mfn.getViewParameters(
            windowAspect, applyOverscan, applySqueeze, applyPanZoom
        )

    def viewingFrustum(
        self, windowAspect, applyOverscan=False, applySqueeze=False, applyPanZoom=False
    ):
        """Returns the viewing frustum (left, right, bottom and top) for the camera.

        :param windowAspect: windowAspect.
        :type windowAspect: float
        :param applyOverscan: Specifies whether to apply overscan.
        :type applyOverscan: bool
        :param applySqueeze: Specifies whether to apply the lens squeeze ratio of the camera.
        :type applySqueeze: bool
        :param applyPanZoom: Specifies whether to apply 2D pan/zoom.
        :type applyPanZoom: bool
        :rtype: tuple[float, float, float, float]
        """
        return self._mfn.getViewingFrustum(
            windowAspect, applyOverscan, applySqueeze, applyPanZoom
        )

    def horizontalFieldOfView(self):
        """Returns the horizontal field of view for the camera.

        :rtype: float
        """
        return self._mfn.horizontalFieldOfView()

    def isOrtho(self):
        """Returns True if the camera is in orthographic mode.

        :rtype: bool
        """
        return self._mfn.isOrtho()

    def postProjectionMatrix(self, context=None):
        """Returns the post projection matrix used to compute film roll on the film back plane.

        :param context: DG time-context to specify time of evaluation.
        :type context: :class:`om2.MDGContext`
        :rtype: :class:`om2.MFloatMatrix`
        """
        if context:
            return self._mfn.postProjectionMatrix(context)
        return self._mfn.postProjectionMatrix()

    def projectionMatrix(self, context):
        """Returns the orthographic or perspective projection matrix for the camera.

        The projection matrix that maya's software renderer uses is almost
        identical to the OpenGL projection matrix. The difference is that maya uses
        a left-hand coordinate system and so the entries [2][2] and [3][2] are negated.

        :param context: DG time-context to specify time of evaluation.
        :type context: :class:`om2.MDGContext`
        :rtype: :class:`om2.MFloatMatrix`
        """
        if context:
            return self._mfn.projectionMatrix(context)
        return self._mfn.projectionMatrix()

    def rightDirection(self, space=kObjectSpace):
        """Returns the right direction vector for the camera.

        :param space: Specifies the coordinate system for this operation.
        :type space: int
        :type: :class:`om2.MVector`
        """
        return self._mfn.rightDirection(space)

    def set(
        self,
        wsEyeLocation,
        wsViewDirection,
        wsUpDirection,
        horizFieldOfView,
        aspectRatio,
    ):
        """Convenience routine to set the camera viewing parameters.

        The specified values should be in world space where applicable.

        This method will only work when the world space information for the camera is available,
        i.e. when the function set has been initialized with a DAG path.

        :param wsEyeLocation: Eye location to set in world space.
        :type wsEyeLocation: :class:`MPoint`
        :param wsViewDirection: View direction to set in world space.
        :type wsViewDirection: :class:`MVector`
        :param wsUpDirection: Up direction to set in world space.
        :type wsUpDirection: :class:`MVector`
        :param horizFieldOfView: The horizontal field of view to set.
        :type horizFieldOfView: float
        :param aspectRatio: The aspect ratio to set.
        :type aspectRatio: float
        """
        self._mfn.set(
            wsEyeLocation, wsViewDirection, wsUpDirection, horizFieldOfView, aspectRatio
        )

    def setAspectRatio(self, aspectRatio):
        """Set the aspect ratio of the View.

        The aspect ratio is expressed as width/height.

        ..note::
            This also modifies the entity's scale transformation to reflect the new aspect ratio.

        :param aspectRatio: The aspect ratio to be set.
        :type aspectRatio: float
        """
        self._mfn.setAspectRatio(aspectRatio)

    def setCenterOfInterestPoint(self, centerOfInterest, space=kObjectSpace):
        """Positions the center-of-interest of the camera keeping the eye-point fixed in space.

        This method changed the orientation and translation of the camera's transform attributes
        as well as the center-of-interest distance.

        This method will only work when the world space information for the camera is available,
        i.e. when the function set has been initialized with a DAG path.

        :param centerOfInterest: Center of interest point to be set.
        :type centerOfInterest: :class:`om2.MPoint` or :class:`om2.MVector`
        :param space: Specifies the coordinate system for this operation.
        :type space: int
        """
        self._mfn.setCenterOfInterestPoint(om2.MPoint(centerOfInterest), space)

    def setEyePoint(self, eyeLocation, space=kObjectSpace):
        """Positions the eye-point of the camera keeping the center of interest fixed in space.

        This method changed the orientation and translation of the camera's transform attributes
         as well as the center-of-interest distance.

        This method will only work when the world space information for the camera is available,
         i.e. when the function set has been initialized with a DAG path.

        :param eyeLocation: The eye location to set.
        :type eyeLocation: :class:`om2.MPoint`
        :param space: Specifies the coordinate system for this operation.
        :type space: int
        """
        self._mfn.setEyePoint(eyeLocation, space)

    def setHorizontalFieldOfView(self, fov):
        """Sets the horizontal field of view for the camera.

        :param fov: The horizontal field of view value to be set.
        :type fov: float
        """
        self._mfn.setHorizontalFieldOfView(fov)

    def setNearFarClippingPlanes(self, near, far):
        """Set the distances to the Near and Far Clipping Planes.

        :param near: The near clipping plane value to be set.
        :type near: float
        :param far: The far clipping plane value to be set.
        :type far: float
        """
        self.setNearFarClippingPlanes(near, far)

    def setVerticalFieldOfView(self, fov):
        """Sets the vertical field of view for the camera.

        :param fov: The vertical field of view value to be set.
        :type fov: float
        """
        self._mfn.setVerticalFieldOfView(fov)

    def upDirection(self, space=kObjectSpace):
        """Returns the up direction vector for the camera.

        :param space: Specifies the coordinate system for this operation.
        :type space: int
        :type: :class:`om2.MVector`
        """
        return self._mfn.upDirection(space=space)

    def verticalFieldOfView(self):
        """Returns the vertical field of view for the camera.

        :rtype: float
        """
        return self._mfn.verticalFieldOfView()

    def viewDirection(self, space=kObjectSpace):
        """Returns the view direction for the camera

        :param space: Specifies the coordinate system for this operation.
        :type space: int
        :type: :class:`om2.MVector`
        """
        return self._mfn.viewDirection(space)


class IkHandle(DagNode):
    _apiType = om2.MFn.kIkHandle
    # twist controls scene worldUpType enum value
    SCENE_UP = 0
    # twist controls object up worldUpType enum value
    OBJECT_UP = 1
    # twist controls object up start/end worldUpType enum value
    OBJECT_UP_START_END = 2
    # twist controls object rotation up worldUpType enum value
    OBJECT_ROTATION_UP = 3
    # twist controls object rotation up start/end worldUpType enum value
    OBJECT_ROTATION_UP_START_END = 4
    # twist controls Vector worldUpType enum value
    VECTOR = 5
    # twist controls Vector start/end worldUpType enum value
    VECTOR_START_END = 6
    # twist controls relative worldUpType enum value
    RELATIVE = 7

    FORWARD_POSITIVE_X = 0
    FORWARD_NEGATIVE_X = 1
    FORWARD_POSITIVE_Y = 2
    FORWARD_NEGATIVE_Y = 3
    FORWARD_POSITIVE_Z = 4
    FORWARD_NEGATIVE_Z = 5

    UP_POSITIVE_Y = 0
    UP_NEGATIVE_Y = 1
    UP_CLOSET_Y = 2
    UP_POSITIVE_Z = 3
    UP_NEGATIVE_Z = 4
    UP_CLOSET_Z = 5
    UP_POSITIVE_X = 6
    UP_NEGATIVE_X = 7
    UP_CLOSET_X = 8

    def vectorToForwardAxisEnum(self, vec):
        """This method takes a vector and determines the forward axis direction based on the values of the vector.
        The vector should be a list or tuple of three floats representing the x, y, and z values respectively.
        The method will return an enum value indicating the forward axis direction.

        The forward axis direction is determined by finding the axis with the largest magnitude in the vector.
        If the sum of the values in the vector is negative, the method will return the corresponding negative
        forward axis enum value.

        The available forward axis enum values are:

            - IkHandle.FORWARD_NEGATIVE_X: The negative X axis
            - IkHandle.FORWARD_NEGATIVE_Y: The negative Y axis
            - IkHandle.FORWARD_NEGATIVE_Z: The negative Z axis

        If the sum of the values in the vector is not negative, the method will return the axis index
        corresponding to the forward axis direction.

        The possible axis indexes are:

            - mayamath.XAXIS: The X axis
            - mayamath.YAXIS: The Y axis
            - mayamath.ZAXIS: The Z axis

        :param vec: A vector representing the forward axis
        :type vec: list or tuple (3 floats)
        :return: An enum value representing the forward axis direction
        :rtype: int

        Example usage:

            vec = [1.0, 0.0, 0.0]
            result = vectorToForwardAxisEnum(vec)
            # result should be mayamath.XAXIS

            vec = [-1.0, 0.0, 0.0]
            result = vectorToForwardAxisEnum(vec)
            # result should be IkHandle.FORWARD_NEGATIVE_X

        """
        axisIndex = mayamath.XAXIS
        isNegative = sum(vec) < 0.0

        for axisIndex, value in enumerate(vec):
            if int(value) != 0:
                break

        if isNegative:
            axisMapping = {
                mayamath.XAXIS: IkHandle.FORWARD_NEGATIVE_X,
                mayamath.YAXIS: IkHandle.FORWARD_NEGATIVE_Y,
                mayamath.ZAXIS: IkHandle.FORWARD_NEGATIVE_Z,
            }
            return axisMapping[axisIndex]
        return axisIndex

    def vectorToUpAxisEnum(self, vec):
        """This method takes a vector and determines the Up axis direction based on the values of the vector.
        The vector should be a list or tuple of three floats representing the x, y, and z values respectively.
        The method will return an enum value indicating the up axis direction.

        The up axis direction is determined by finding the axis with the largest magnitude in the vector.
        If the sum of the values in the vector is negative, the method will return the corresponding negative
        up axis enum value.

        The available up axis enum values are:

            - IkHandle.UP_NEGATIVE_X: The negative X axis
            - IkHandle.UP_POSITIVE_Y: The negative Y axis
            - IkHandle.UP_NEGATIVE_Z: The negative Z axis

        If the sum of the values in the vector is not negative, the method will return the axis index
        corresponding to the forward axis direction.

        The possible axis indexes are:

            - mayamath.XAXIS: The X axis
            - mayamath.YAXIS: The Y axis
            - mayamath.ZAXIS: The Z axis

        Example usage:

            ik_handle = IkHandle()
            vec = [0.0, 1.0, 0.0]
            up_axis_enum = ik_handle.vectorToUpAxisEnum(vec)
            print(up_axis_enum)  # Output: 2 (IkHandle.UP_POSITIVE_Y)

        """
        axisIndex = mayamath.XAXIS
        isNegative = sum(vec) < 0.0

        for axisIndex, value in enumerate(vec):
            if int(value) != 0:
                break
        axisMapping = {
            mayamath.XAXIS: IkHandle.UP_POSITIVE_X,
            mayamath.YAXIS: IkHandle.UP_POSITIVE_Y,
            mayamath.ZAXIS: IkHandle.UP_POSITIVE_Z,
        }
        if isNegative:
            axisMapping = {
                mayamath.XAXIS: IkHandle.UP_NEGATIVE_X,
                mayamath.YAXIS: IkHandle.UP_NEGATIVE_Y,
                mayamath.ZAXIS: IkHandle.UP_NEGATIVE_Z,
            }
        return axisMapping[axisIndex]


class SkinCluster(DGNode):
    _mfnType = om2Anim.MFnSkinCluster

    def recacheBindMatrices(self, modifier=None, apply=True):
        preBindMatrixCompound = self.bindPreMatrix
        mod = modifier or dgModifier
        for matrixElement in self.matrix:
            logicalIndex = matrixElement.logicalIndex
            preBind = preBindMatrixCompound.element(logicalIndex)
            if preBind.isConnected():
                continue
            sourceNode = matrixElement.sourceNode()
            if not sourceNode:
                continue
            preBind.set(mod=mod, apply=False)
        if apply:
            mod.doIt()
        return mod


class AnimCurve(DGNode):
    _mfnType = om2Anim.MFnAnimCurve

    def addKeysWithTangents(
        self,
        times,
        values,
        tangentInType=kTangentGlobal,
        tangentOutType=kTangentGlobal,
        tangentInTypeArray=None,
        tangentOutTypeArray=None,
        tangentInXArray=None,
        tangentInYArray=None,
        tangentOutXArray=None,
        tangentOutYArray=None,
        tangentsLockedArray=None,
        weightsLockedArray=None,
        convertUnits=True,
        keepExistingKeys=False,
        change=None,
    ):
        """Add a set of new keys with the given corresponding values and tangent types at the specified times.

        .. note::
            This method only works for Anim Curves of type kAnimCurveTA, kAnimCurveTL and kAnimCurveTU.

        :param times: Times at which keys are to be added
        :type times: :class:`om2.MTimeArray`
        :param values: Values to which the keys is to be set
        :type values: list[float]
        :param tangentInType: In tangent type for all the added keys ie. `kTangentGlobal`
        :type tangentInType: int
        :param tangentOutType: Out tangent type for all the added keys ie. `kTangentGlobal`
        :type tangentOutType: int
        :param tangentInTypeArray: In tangent types for individual added keys
        :type tangentInTypeArray: list[int]
        :param tangentOutTypeArray: Out tangent types for individual added keys
        :type tangentOutTypeArray: list[int]
        :param tangentInXArray: Absolute x value of the slope of in tangent
        :type tangentInXArray: list[float]
        :param tangentInYArray: Absolute y value of the slope of in tangent
        :type tangentInYArray: list[float]
        :param tangentOutXArray: Absolute x value of the slope of out tangent
        :type tangentOutXArray: list[float]
        :param tangentOutYArray: Absolute y value of the slope of out tangent
        :type tangentOutYArray: list[float]
        :param tangentsLockedArray: Lock or unlock the tangents
        :type tangentsLockedArray: list[int]
        :param weightsLockedArray: Lock or unlock the weights
        :type weightsLockedArray: list[int]
        :param convertUnits: Whether to convert to UI units before setting
        :type convertUnits: bool
        :param keepExistingKeys: Specifies whether the new keys should be merged with existing keys, \
        or if they should be cut prior to adding the new keys

        :type keepExistingKeys: bool
        :param change: Cache to store undo/redo information.
        :type change: MAnimCurveChange
        """
        arguments = [
            times,
            values,
            tangentInType,
            tangentOutType,
            tangentInTypeArray or [],
            tangentOutTypeArray or [],
            tangentInXArray or [],
            tangentInYArray or [],
            tangentOutXArray or [],
            tangentOutYArray or [],
            tangentsLockedArray or [],
            weightsLockedArray or [],
            convertUnits,
            keepExistingKeys,
        ]

        # maya api doesn't like if you pass None even though the default implementation is None by the api lol
        if change is not None:
            arguments.append(change)

        self._mfn.addKeysWithTangents(*arguments)

    def setPrePostInfinity(self, pre, post, change=None):
        """Set the behaviour of the curve for the range occurring before the first key and after the last Key.

        .. code-block:: python

            undoChange = om2Anim.MAnimCurveChange()
            curve = zapi.DGNode("myCurve", "animCurveTU")
            curve.setPrePostInfinity(zapi.kInfinityConstant, zapi.kInfinityConstant, undoChange)

        :param pre: Sets the behaviour of the curve for the range occurring before the first key.
        :type pre: int
        :param post: Set the behaviour of the curve for the range occurring after the last Key.
        :type post: int
        :param change:
        :type change: :class:`om2Anim.MAnimCurveChange`

        """
        mfn = self.mfn()
        if change:
            mfn.setPreInfinityType(pre, change)
            mfn.setPostInfinityType(post, change)
        else:
            mfn.setPreInfinityType(pre)
            mfn.setPostInfinityType(post)


class DisplayLayer(DGNode):
    def addNodes(self, displayNodes):
        """Attaches the specified nodes to this displayLayer

        :param displayNodes: the dag nodes to attach to this displayLayer
        :type displayNodes: list[:class:`DagNode`]
        """
        drawInfoPlug = self.drawInfo
        for n in displayNodes:
            drawInfoPlug.connect(n.drawOverride)

    def addNode(self, node):
        """Attaches the specified node to this displayLayer

        :param node: the dag node to attach to this displayLayer
        :type node: :class:`DagNode`
        """
        self.drawInfo.connect(node.drawOverride)


class Plug(object):
    """Plug class which represents a maya MPlug but providing an easier solution to
    access connections and values.

    :param node: The DGNode or DagNode instance for this Plug
    :type node: :class:`DGNode` or :class:`DagNode`
    :param mPlug: The Maya plug
    :type mPlug: :class:`om2.MPlug`
    """

    def __init__(self, node, mPlug):
        self._mplug = mPlug
        self._node = node

    def __repr__(self):
        """Returns the name"""
        if self.exists():
            return self._mplug.name()
        return ""

    def __str__(self):
        if self.exists():
            return self._mplug.name()
        return ""

    def __eq__(self, other):
        return self._mplug == other.plug()

    def __ne__(self, other):
        return self._mplug != other.plug()

    def __getitem__(self, index):
        """[0] syntax, The method indexes into the array or compound children by index.

        :param index: Element or child index to get
        :type index: int
        :rtype: :class:`Plug`
        """
        if self._mplug.isArray:
            return self.element(index)
        if self._mplug.isCompound:
            return self.child(index)

        raise TypeError("{} does not support indexing".format(self.name()))

    def __getattr__(self, item):

        if hasattr(self._mplug, item):
            return getattr(self._mplug, item)
        return super(Plug, self).__getattribute__(item)

    def __setattr__(self, key, value):
        if key.startswith("_"):
            super(Plug, self).__setattr__(key, value)
            return

        elif hasattr(self._mplug, key):
            return setattr(self._mplug, key, value)

        elif isinstance(value, Plug):
            value.connect(self)

        super(Plug, self).__setattr__(key, value)

    def __abs__(self):
        return abs(self.value())

    def __int__(self):
        return self._mplug.asInt()

    def __float__(self):
        return self._mplug.asFloat()

    def __neg__(self):
        return -self.value()

    def __bool__(self):
        return self.exists()

    # support py2
    __nonzero__ = __bool__

    def __rshift__(self, other):
        """>> syntax, provides the ability to connect to downstream plug.

        :param other: The downstream plug ie. destination.
        :type other: :class:`Plug`
        """
        self.connect(other)

    def __lshift__(self, other):
        """<< syntax, provides the ability to connect to upstream plug.

        :param other: The upstream plug ie. destination.
        :type other: :class:`Plug`
        """
        other.connect(self)

    def __floordiv__(self, other):
        self.disconnect(other)

    def __iter__(self):
        """Loops the array or compound plug.

        :return: Each element within the generator is a plug.
        :rtype: Generator(:class:`Plug`)
        """
        mPlug = self._mplug
        if mPlug.isArray:
            indices = mPlug.getExistingArrayAttributeIndices()
            # case in maya 2023 where num of indices is zero but 2022 is [0]
            # for consistency and because 0 is usually a valid logical index to bind to(connection,setattr)
            for p in indices or [0]:
                yield Plug(self._node, mPlug.elementByLogicalIndex(p))
        elif mPlug.isCompound:
            for p in range(mPlug.numChildren()):
                yield Plug(self._node, mPlug.child(p))

    def __len__(self):
        """Length of the compound or array, 0 is returned for non iterables.

        :return: The length of the array of compound.
        :rtype: int
        """
        if self._mplug.isArray:
            return self._mplug.evaluateNumElements()
        elif self._mplug.isCompound:
            return self._mplug.numChildren()
        return 0

    def exists(self):
        """Whether this plug is valid, same as `MPlug.isNull`.

        :rtype: bool
        """
        return not self._mplug.isNull

    def partialName(
        self,
        includeNodeName=False,
        includeNonMandatoryIndices=True,
        includeInstancedIndices=True,
        useAlias=False,
        useFullAttributePath=True,
        useLongNames=True,
    ):
        """Returns the partial name for the plug. by default This method will always return the long name excluding
        the node name.

        :type includeNodeName: bool
        :type includeNonMandatoryIndices: bool
        :type includeInstancedIndices: bool
        :type useAlias: bool
        :type useFullAttributePath: bool
        :type useLongNames: bool
        :rtype: str
        """
        return self._mplug.partialName(
            includeNodeName,
            includeNonMandatoryIndices,
            includeInstancedIndices,
            useAlias,
            useFullAttributePath,
            useLongNames,
        )

    def isProxy(self):
        """Whether this plug is a proxy attribute.

        :rtype: bool
        """
        return om2.MFnAttribute(self._mplug.attribute()).isProxyAttribute

    def setAsProxy(self, sourcePlug):
        """Sets the current attribute as a proxy attribute and connects to the sourcePlug.

        :param sourcePlug: The source plug to connect to this plug.
        :type sourcePlug: :class:`Plug`
        """
        if self._mplug.isCompound:
            nodes.setCompoundAsProxy(self.plug(), sourcePlug.plug())
            return
        om2.MFnAttribute(self._mplug.attribute()).isProxyAttribute = True
        sourcePlug.connect(self)

    def array(self):
        """Returns the plug array for this array element.

        :rtype: :class:`Plug`
        """
        assert self._mplug.isElement, "Plug: {} is not an array element".format(
            self.name()
        )
        return Plug(self._node, self._mplug.array())

    def parent(self):
        """Returns the parent Plug if this plug is a compound.

        :return: The parent Plug.
        :rtype: :class:`Plug`
        """
        assert self._mplug.isChild, "Plug {} is not a child".format(self.name())
        return Plug(self._node, self._mplug.parent())

    def children(self):
        """Returns all the child plugs of this compound plug.

        :return: A list of child plugs.
        :rtype: iterable(:class:`Plug`)
        """

        return [
            Plug(self._node, self._mplug.child(i))
            for i in range(self._mplug.numChildren())
        ]

    def child(self, index):
        """Returns the child plug by index.

        :param index: The child index
        :type index: int
        :return: The child plug.
        :rtype: :class:`Plug`
        """
        assert self._mplug.isCompound, "Plug: {} is not a compound".format(self.name())
        if index < 0:
            newIndex = max(
                0, len(self) + index
            )  # index is negative so it will minus from len
            return Plug(self._node, self._mplug.child(newIndex))
        return Plug(self._node, self._mplug.child(index))

    def element(self, index):
        """Returns the logical element plug if this plug is an array.

        :param index: The element index
        :type index: int
        :return: The Element Plug.
        :rtype: :class:`Plug`
        """
        assert self._mplug.isArray, "Plug: {} is not an array".format(self.name())
        if index < 0:
            newIndex = max(
                0, len(self) + index
            )  # index is negative so it will minus from len
            return Plug(self._node, self._mplug.elementByLogicalIndex(newIndex))

        return Plug(self._node, self._mplug.elementByLogicalIndex(index))

    def elementByPhysicalIndex(self, index):
        """Returns the element plug by the physical index if this plug is an array.

        :param index: the physical index.
        :type index: int
        :return: The element Plug.
        :rtype: :class:`Plug`
        """
        assert self._mplug.isArray, "Plug: {} is not an array".format(self.name())
        return Plug(self._node, self._mplug.elementByPhysicalIndex(index))

    def nextAvailableElementPlug(self):
        """Returns the next available output plug for this array.

        Availability is based and connections of element plug and their children

        :rtype: :class:`Plug`
        """
        assert self._mplug.isArray, "Plug: {} is not an array".format(self.name())
        return Plug(self._node, plugs.nextAvailableElementPlug(self._mplug))

    def nextAvailableDestElementPlug(self):
        """Returns the next available input plug for this array.

        Availability is based and connections of element plug and their children

        :rtype: :class:`Plug`
        """
        assert self._mplug.isArray, "Plug: {} is not an array".format(self.name())
        return Plug(self._node, plugs.nextAvailableDestElementPlug(self._mplug))

    def plug(self):
        """Returns the maya MPlug object.

        :return: The maya MPlug object
        :rtype: :class:`om2.MPlug`
        """
        return self._mplug

    def node(self):
        """Returns the attached Node class for this plug.

        :return: The DGNode class or DagNode for this Plug.
        :rtype: :class:`DagNode` or :class:`DGNode`
        """
        return self._node

    def apiType(self):
        """Returns the internal zoo attribute type constant

        :rtype: `int`
        """
        return plugs.plugType(self._mplug)

    @lockNodePlugContext
    def connect(self, plug, children=None, force=True, mod=None, apply=True):
        if self.isCompound and children:
            children = children or []
            selfLen = len(self)
            childLen = len(children)

            if childLen == 0:
                plugs.connectPlugs(self._mplug, plug.plug(), force=force, mod=mod)
            if childLen > selfLen:
                children = children[:selfLen]
            elif childLen < selfLen:
                children += [False] * (selfLen - childLen)
            return plugs.connectVectorPlugs(
                self.plug(), plug.plug(), children, force, modifier=mod, apply=apply
            )
        return plugs.connectPlugs(
            self._mplug, plug.plug(), mod=mod, force=force, apply=apply
        )

    @lockNodePlugContext
    def disconnect(self, plug, modifier=None, apply=True):
        """ Disconnect destination plug

        :param plug: Destination
        :type plug: Plug or om2.MPlug
        :param modifier: The DGModifier to add to, if none it will create one
        :type modifier: :class:`om2.DGModifier`
        :param apply: If True then the plugs value will be set immediately with the Modifier \
        if False it's the client responsibility to call modifier.doIt()
        :type apply: bool
        :return: Returns the provided Modifier or a new Modifier instance
        :rtype: :class:`om2.MDGModifier`
        """
        mod = modifier or om2.MDGModifier()
        mod.disconnect(self._mplug, plug.plug())
        if modifier is None or apply:
            mod.doIt()
        return mod

    @lockNodePlugContext
    def disconnectAll(self, source=True, destination=True, modifier=None):
        """Disconnects all plugs from the current plug

        :param source: if true disconnect from the connected source plug if it has one
        :type source: bool
        :param destination: if true disconnect from the connected destination plug if it has one
        :type destination: bool
        :param modifier: The MDGModifier to add to, if none it will create one
        :type modifier: :class:`om2.MDGModifier`
        :return:
        :rtype: tuple[bool, :class:`om2.MDGModifier`]
        """
        return plugs.disconnectPlug(self._mplug, source, destination, modifier)

    def source(self):
        """Returns the source plug from this plug or None if it's not connected

        :rtype: `Plug` or None
        """
        source = self._mplug.source()
        if source.isNull:
            return

        return Plug(nodeByObject(source.node()), source)

    def sourceNode(self):
        """Returns the source node from this plug or None if it's not connected

        :rtype: :class:`DGNode` or None
        """
        source = self.source()
        if not source:
            return
        return source.node()

    def destinationNodes(self):
        """Generator function which returns all destination nodes in the form of one of our zapi node types.

        :rtype: iterable[:class:`DGNode`]
        """
        dest = self.destinations()

        for d in dest:
            yield d.node()

    def destinations(self):
        """Returns all destination plugs connected to this plug

        :rtype: collections.Iterable[:class:`Plug`]
        """
        for dest in self._mplug.destinations():
            yield Plug(nodeByObject(dest.node()), dest)

    def mfn(self):
        """Returns the maya function set for this plug

        :return: Returns the subclass of MFnBase for this attribute type ie. MFnTypeAttribute
        :rtype: :class:`om2.MFnBase`
        """
        attr = self._mplug.attribute()
        return plugs.getPlugFn(attr)(attr)

    def mfnType(self):
        """Returns the maya MFn attribute type"""
        return plugs.getPlugFn(self._mplug.attribute())

    def value(self, ctx=DGContext.kNormal):
        """Get value of the plug, if mObject is returned the DG/Dag node

        :return: The value of the plug
        """
        value = plugs.getPlugValue(self._mplug, ctx)
        value = Plug._convertValueType(value)
        return value

    @staticmethod
    def _convertValueType(value):
        isMObject = type(value) == om2.MObject
        if isMObject and nodes.isValidMObject(value):
            return nodeByObject(value)
        elif isMObject and not nodes.isValidMObject(value):
            return None
        elif isinstance(value, (list, tuple)):
            value = [Plug._convertValueType(val) for val in value]

        return value

    def default(self):
        """Returns the default value of this plug.

        :rtype:str or int or float
        """
        if not self.exists():
            return
        return plugs.plugDefault(self._mplug)

    def setDefault(self, value):
        """Sets the default for this plug if supported.

        :param value: The default value to set
        :type value: int or flaat or string
        :return: Whether the default was set.
        :rtype: bool
        """
        if self.exists():
            return plugs.setPlugDefault(self._mplug, value)
        return False

    @lockNodePlugContext
    def setFromDict(self, **plugInfo):
        plugs.setPlugInfoFromDict(self._mplug, **plugInfo)

    @lockNodePlugContext
    def set(self, value, mod=None, apply=True):
        """Sets the value of this plug

        :param value: The om2 value type, bool, float,str, MMatrix, MVector etc
        :type value: maya data type.
        :param mod: The zapi.kModifier instance or None.
        :type mod: :class:`zapi.dgModifier` or :class:`zapi.dagModifier`
        :param apply: If True then the plugs value will be set immediately with the Modifier \
        if False it's the client responsibility to call modifier.doIt()
        :type apply: bool
        :raise: :class:`ReferenceObjectError`, in the case where the plug is not dynamic and is referenced.
        """
        if self.node().isReferenced() and self.isLocked:
            raise errors.ReferenceObjectError(
                "Plug: {} is a reference and locked".format(self.name())
            )
        return plugs.setPlugValue(self._mplug, value, mod=mod, apply=apply)

    def isAnimated(self):
        """Returns true when the current plug is animated.

        :rtype: bool
        :raise: :class:`ObjectDoesntExistError` When the current Plug doesn't exist.
        """
        if not self.exists():
            raise errors.ObjectDoesntExistError("Current Plug doesn't exist")
        return om2Anim.MAnimUtil.isAnimated(self._mplug)

    def findAnimation(self):
        """
        Find the animCurve(s) that are animating a given attribute (MPlug).

        In most cases an attribute is animated by a single animCurve and so
        just that animCurve will be returned.  It is possible to setup a
        series of connections where an attribute is animated by more than
        one animCurve, although Maya does not currently offer a UI to do so.
        Compound attributes are not expanded to include any child attributes.

        :rtype: list[:class:`AnimCurve`]
        """
        if not self.exists():
            raise errors.ObjectDoesntExistError("Current Plug doesn't exist")
        return [nodeByObject(i) for i in om2Anim.MAnimUtil.findAnimation(self._mplug)]

    def isFreeToChange(self):
        return self._mplug.isFreeToChange() == self._mplug.kFreeToChange

    @lockNodePlugContext
    def addEnumFields(self, fields):
        """Adds a list of field names to the plug, if a name already exists it will be skipped.
        Adding a field will always be added to the end.

        :param fields: A list of field names to add.
        :type fields: list[str]
        :raise: :class:`ReferenceObjectError`, in the case where the plug is not dynamic and is referenced.
        """
        if self.node().isReferenced() and self.isLocked:
            raise errors.ReferenceObjectError(
                "Plug: {} is a reference and locked".format(self.name())
            )
        existingFieldNames = self.enumFields()
        mayaAttr = self.attribute()
        spaceAttr = om2.MFnEnumAttribute(mayaAttr)
        # add any missing fields to enumAttribute
        index = 0
        for field in fields:
            if field not in existingFieldNames:
                spaceAttr.addField(field, len(existingFieldNames) + index)
                index += 1

    def enumFields(self):
        """Returns a list of the enum fields for this plug. A :class:`InvalidTypeForPlugError`
        error will be raised if the plug isn't compatible.

        :raise: :class:`InvalidTypeForPlugError` when the plug isn't an enum type.
        """
        plugType = self.apiType()

        if plugType != attrtypes.kMFnkEnumAttribute:
            raise errors.InvalidTypeForPlugError(
                "Required type: 'Enum', current type: {}".format(
                    attrtypes.typeToString(plugType)
                )
            )
        return plugs.enumNames(self.plug())

    def setFields(self, fields):
        """Sets the list fields for this plug

        :param fields: The list of fields to set for this plug
        :type fields: list[str]
        :raise: :class:`errors.InvalidTypeForPlugError`, raised when the plug isn't an Enum attribute.
        """
        defaultValue = self.default()

        try:
            cmds.addAttr(self.name(), edit=True, enumName=":".join(fields))
        except RuntimeError:
            raise errors.InvalidTypeForPlugError(
                "Plug: {} is not of type Enum".format(self)
            )
        if defaultValue is not None and defaultValue < len(self.enumFields()):
            self.setDefault(defaultValue)

    @lockNodePlugContext
    def delete(self, modifier=None, apply=True):
        """Deletes the plug from the attached Node. If batching is needed then use the modifier
        parameter to pass a base.MDGModifier, once all operations are done call modifier.doIt()

        :param modifier: The DGModifier to add to, if none it will create one
        :type modifier: :class:`om2.DGModifier`
        :param apply: If True then the plugs value will be set immediately with the Modifier \
        if False it's the client responsibility to call modifier.doIt()
        :type apply: bool
        :return: Maya DGModifier
        :rtype: :class:`om2.MDGModifier`
        :raise: :class:`ReferenceObjectError`, in the case where the plug is not dynamic and is referenced
        """
        if not self.isDynamic and self.node().isReferenced():
            raise errors.ReferenceObjectError(
                "Plug: {} is reference and locked".format(self.name())
            )
        mod = modifier or om2.MDGModifier()
        if self._mplug.isElement:
            logicalIndex = self._mplug.logicalIndex()
            mod = plugs.removeElementPlug(
                self._mplug.array(), logicalIndex, mod=mod, apply=apply
            )
        else:
            mod.removeAttribute(self.node().object(), self.attribute())
        if modifier is None or apply:
            mod.doIt()
        return mod

    @lockNodePlugContext
    def deleteElements(self, modifier=None, apply=True):
        """Deletes all array elements from this plug. If batching is needed then use the modifier
        parameter to pass a base.MDGModifier, once all operations are done call modifier.doIt().

        :param modifier: The DGModifier to add to, if none it will create one.
        :type modifier: :class:`om2.DGModifier`
        :param apply: If True then the plugs value will be set immediately with the Modifier \
        if False it's the client responsibility to call modifier.doIt().
        :type apply: bool
        :return: Maya DGModifier.
        :rtype: :class:`om2.MDGModifier`
        :raise: :class:`ReferenceObjectError`, in the case where the plug is not dynamic and is referenced.
        :raise: :class:`TypeError`, in case this plug is not an array.
        """
        if not self.isDynamic and self.node().isReferenced():
            raise errors.ReferenceObjectError(
                "Plug: {} is reference and locked".format(self.name())
            )
        if not self._mplug.isArray:
            raise TypeError("InValid plug type to delete, must be of type Array")
        mod = modifier or om2.MDGModifier()
        for element in self:
            logicalIndex = element.logicalIndex()
            mod = plugs.removeElementPlug(
                self._mplug, logicalIndex, mod=mod, apply=apply
            )
        if modifier is None or apply:
            mod.doIt()
        return mod

    @lockNodePlugContext
    def rename(self, name, mod=None):
        """Renames the current plug.

        :param name: The new name of the plug
        :type name: str
        :param mod: The DagModifier instance to use or None.
        :type mod: :class:`maya.api.OpenMaya.MDGModifier`
        :return: True if renamed.
        :rtype: bool
        """
        with plugs.setLockedContext(self._mplug):
            mod = mod or om2.MDGModifier()
            mod.renameAttribute(self.node().object(), self.attribute(), name, name)
            mod.doIt()
        return True

    def lockAndHide(self):
        """Locks the plug and  hides the attribute from the channel box"""
        self._mplug.isLocked = True
        self._mplug.isChannelBox = False
        self._mplug.isKeyable = False

    def hide(self):
        """Hides the attribute from the channel box and makes the attribute non-keyable"""
        self._mplug.isChannelBox = False
        self._mplug.isKeyable = False

    def show(self):
        """Displays the attribute in the channelBox"""
        self._mplug.isChannelBox = True

    def setKeyable(self, state):
        """Sets the keyable state of the attribute"""
        self._mplug.isKeyable = state

    def lock(self, state):
        """Sets the current plugs lock state.

        :param state: True if the plug is to be locked.
        :type state: bool
        """
        self._mplug.isLocked = state

    def serializeFromScene(self):
        if not self.exists():
            return {}
        return plugs.serializePlug(self._mplug)


def createDG(name, nodeType, mod=None):
    """Creates a maya dg node and returns a :class::`DGNode` instance

    :param name: The name for the node, must be unique
    :type name: str
    :param nodeType: The maya Dg node type
    :type nodeType: str
    :param mod: The DagModifier instance to use or None.
    :type mod: :class:`maya.api.OpenMaya.MDGModifier`
    :rtype: :class:`DGNode`
    """
    return nodeByObject(nodes.createDGNode(name, nodeType=nodeType, mod=mod))


def createDag(name, nodeType, parent=None, mod=None):
    """Creates a maya dag node and returns a :class::`DagNode` instance

    :param name: The name for the node, must be unique
    :type name: str
    :param nodeType: The maya Dag node type
    :type nodeType: str
    :param parent: The parent Node or None
    :type parent: :class:`DagNode` or None
    :param mod: The DagModifier instance to use or None.
    :type mod: :class:`maya.api.OpenMaya.MDGModifier`
    :rtype: :class:`DagNode`
    """
    if isinstance(parent, DagNode):
        parent = parent.object()
    return nodeByObject(
        nodes.createDagNode(name, nodeType=nodeType, parent=parent, modifier=mod)
    )


def nodeByObject(node):
    """Given a MObject return the correct Hive base node class

    :param node: The maya om2 api MObject to cast.
    :type node: om2.MObject
    :rtype: :class:`DagNode` or :class:`DGNode`
    """
    if node.hasFn(om2.MFn.kDagNode):
        dagPath = om2.MDagPath.getAPathTo(node)
        if node.hasFn(om2.MFn.kNurbsCurve):
            sup = NurbsCurve
        elif node.hasFn(om2.MFn.kMesh):
            sup = Mesh
        elif node.hasFn(om2.MFn.kCamera):
            sup = Camera
        elif node.hasFn(om2.MFn.kIkHandle):
            sup = IkHandle
        else:
            sup = DagNode
        objectToSet = dagPath
    else:
        if node.hasFn(om2.MFn.kContainer):
            sup = ContainerAsset

        elif node.hasFn(om2.MFn.kAnimCurve):
            sup = AnimCurve
        elif node.hasFn(om2.MFn.kSkinClusterFilter):
            sup = SkinCluster
        elif node.hasFn(om2.MFn.kControllerTag):
            sup = DGNode
        elif node.hasFn(om2.MFn.kSet):
            sup = ObjectSet
        elif node.hasFn(om2.MFn.kBlendShape):
            sup = BlendShape
        elif node.hasFn(om2.MFn.kDisplayLayer):
            sup = DisplayLayer
        else:
            sup = DGNode
        objectToSet = node
    return sup(objectToSet)


def nodeByName(nodeName):
    """Returns a dag node instance given the maya node name, expecting fullPathName.

    :param nodeName: The maya node name
    :type nodeName: str
    :rtype: :class:`DGNode` or :class:`DagNode`
    """
    mObj = nodes.asMObject(nodeName)
    if mObj.hasFn(om2.MFn.kDagNode):
        dagPath = om2.MDagPath.getAPathTo(mObj)

        if mObj.hasFn(om2.MFn.kNurbsCurve):
            sup = NurbsCurve
        elif mObj.hasFn(om2.MFn.kMesh):
            sup = Mesh
        elif mObj.hasFn(om2.MFn.kCamera):
            sup = Camera
        elif mObj.hasFn(om2.MFn.kIkHandle):
            sup = IkHandle
        else:
            sup = DagNode
        objectToSet = dagPath
    else:
        if mObj.hasFn(om2.MFn.kContainer):
            sup = ContainerAsset

        elif mObj.hasFn(om2.MFn.kAnimCurve):
            sup = AnimCurve
        elif mObj.hasFn(om2.MFn.kSkinClusterFilter):
            sup = SkinCluster
        elif mObj.hasFn(om2.MFn.kControllerTag):
            sup = DGNode
        elif mObj.hasFn(om2.MFn.kSet):
            sup = ObjectSet
        elif mObj.hasFn(om2.MFn.kBlendShape):
            sup = BlendShape
        elif mObj.hasFn(om2.MFn.kDisplayLayer):
            sup = DisplayLayer
        else:
            sup = DGNode
        objectToSet = mObj
    return sup(objectToSet)


def nodesByNames(nodeNameList):
    """nodeByName except uses a list

    :param nodeNameList: List of maya node names
    :type nodeNameList: list[str]
    :return: a list of maya node paths to convert to zapi nodes
    :rtype: collections.Iterable[DagNode]
    """
    for n in nodeNameList:
        yield nodeByName(n)


def plugByName(path):
    """Returns the :class:`Plug` instance for the provided path to the plug

    :param path: The fullPath to the plug.
    :type path: str
    :raise: :class:`InvalidPlugPathError`
    :return: The Plug instance matching the plug path.
    :rtype: :class:`Plug`
    """
    if "." not in path:
        raise errors.InvalidPlugPathError(path)
    plug = plugs.asMPlug(path)
    return Plug(nodeByObject(plug.node()), plug)


def fullNames(dagNodes):
    """Helper function to get full names of dagNodes

    :param dagNodes: DagNodes
    :type dagNodes: list[:class:`DagNode`] or Iterable[:class:`DagNode`]
    :return: a list of fullPaths
    :rtype: list[str]
    """
    return [d.fullPathName() for d in dagNodes if d.exists()]


def shortNames(dagNodes):
    """Helper function to get the short names of DGNode

    :param dagNodes: An iterable of DGNodes/DagNodes.
    :type dagNodes: list[:class:`DGNode`] or collections.Iterable[:class:`DGNode`]
    :return: A list of short names for the provided nodes.
    :rtype: list[str]
    """
    return [d.name() for d in dagNodes if d.exists()]


def alphabetizeDagList(dagList):
    """Sorts a dag API object list by lowercase short names

    :param dagList: A list of API dag objects
    :type dagList: list[DagNode]
    :return: A list of API dag objects now sorted alphabetically
    :type dagList: list[DagNode]
    """
    if not dagList:
        return dagList
    names = shortNames(dagList)
    names = [x.lower() for x in names]  # lowercase for sorting later
    zippedList = sorted(zip(names, dagList))
    return [x for y, x in zippedList]  # now alphabetical


def selected(filterTypes=()):
    """Get dag nodes from selected objects in maya

    :param filterTypes: a tuple of om2.MFn types to filter selected Nodes
    :type filterTypes: tuple(om2.MFn.kConstant)
    :return: A list of DGNode nodes
    :rtype: iterable[:class:`DGNode`]
    """
    return map(nodeByObject, scene.iterSelectedNodes(filterTypes))


def select(objects, mod=None, apply=True):
    """Selects all nodes in `objects`, this uses cmds.select.

    :param objects: DG Nodes to select
    :type objects: iterable[:class:`DGNode`]
    :param mod: The Dag/DG modifier to run the command in
    :type mod: :class:`maya.api.OpenMaya.MDagModifier` or :class:`maya.api.OpenMaya.MDGModifier`
    :rtype mod: :class:`maya.api.OpenMaya.MDGModifier`
    :param apply: Apply the modifier immediately if true, false otherwise
    :type apply: bool
    """
    mod = mod or om2.MDGModifier()

    mod.pythonCommandToExecute(
        "from maya import cmds;cmds.select({})".format(
            [i.fullPathName() for i in objects]
        )
    )
    if apply:
        mod.doIt()

    return mod


def clearSelection(mod=None, apply=True):
    mod = mod or om2.MDGModifier()

    mod.pythonCommandToExecute("from maya import cmds;cmds.select(clear=True)")
    if apply:
        mod.doIt()

    return mod


def selectByNames(names, mod=None, apply=True):
    """Same as select(), except it uses the names instead

    :param names: Names of the nodes
    :type names: iterable[:class:`str`]
    :param apply: Apply the MDagModifier immediately
    :param mod: The Dag/DG modifier
    :type mod: :class:`maya.api.OpenMaya.MDagModifier` or :class:`maya.api.OpenMaya.MDGModifier`
    :rtype mod: :class:`maya.api.OpenMaya.MDGModifier`
    """
    mod = mod or om2.MDGModifier()

    mod.pythonCommandToExecute("from maya import cmds;cmds.select({})".format(names))
    if apply:
        mod.doIt()

    return mod


def ls(*args, **kwargs):
    """The zapi version of cmds.ls.

    :rtype: list[:class:`DGNode`]
    """
    return list(map(nodeByName, cmds.ls(*args, **kwargs)))


def duplicateAsTransform(source, name, parent=None, mod=None):
    """Creates a new Transform from the source but maintains the transform and rotationOrder

    :param source: The source node to copy the transform from
    :type source: :class:`zapi.DagNode`
    :param name: The node name to use
    :type name: str
    :param parent: The parent Node or None
    :type parent: :class:`DagNode` or None
    :param mod: The DagModifier instance to use or None.
    :type mod: :class:`maya.api.OpenMaya.MDGModifier`
    :return: The newly created Transform node
    :rtype: :class:`DagNode`
    """
    newNode = createDag(name, "transform", parent=parent, mod=mod)
    transform = source.transformationMatrix()
    newNode.setRotationOrder(source.rotationOrder(), False)
    newNode.setWorldMatrix(transform)
    return newNode


def displayLayers(default=False):
    """Returns all displays in the scene.

    :param default: If True then default layers will be included in the result.
    :type default: bool
    :return: The scene display layers.
    :rtype: list[:class:`DagNode`]
    """
    allLayers = cmds.ls(
        type="displayLayer", defaultNodes=False, long=True, undeletable=False
    )
    if default:
        return list(map(nodeByName, allLayers))

    deletableLayers = cmds.ls(
        type="displayLayer", defaultNodes=False, long=True, undeletable=True
    )
    return list(map(nodeByName, set(allLayers) - set(deletableLayers)))


def hasControllerTag(node):
    """Returns the attached controllerTag if any.

    :rtype: :class:`zapi.DGNode` or None
    """
    for dest in node.attribute("message").destinations():
        node = dest.node()
        if node.apiType() == kControllerTag:
            return True
    return False

def controllerTag(self):
    """Returns the attached controllerTag if any.

    :rtype: :class:`zapi.DGNode` or None
    """
    for dest in self.attribute("message").destinations():
        node = dest.node()
        if node.apiType() == kControllerTag:
            return node