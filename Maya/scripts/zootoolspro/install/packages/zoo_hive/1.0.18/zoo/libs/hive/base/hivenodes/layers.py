"""
This module houses hive layers, hive layers are just transforms used to organize the rig/component
into chunks, each layer has its own logic to deal with its children and meta nodes. Layers
are intended to be the main access points to any node in attached to the rig, this is primarily
done by the attached meta nodes.

"""

import json
from zoovendor.six import string_types

from zoo.libs.maya.api import plugs, nodes
from zoo.libs.maya.meta import base
from zoo.core.util import zlogging
from zoo.libs.maya import zapi
from zoo.libs.maya.utils import mayamath
from zoo.libs.hive import constants
from zoo.libs.hive.base.hivenodes import hnodes
from zoo.libs.hive.base import errors
from zoo.libs.hive.base.definition import defutils
from zoo.libs.hive.base.serialization import dggraph
from maya import cmds


__all__ = (
    "HiveLayer",
    "HiveComponentLayer",
    "HiveInputLayer",
    "HiveOutputLayer",
    "HiveGuideLayer",
    "HiveRigLayer",
    "HiveDeformLayer",
    "HiveGeometryLayer",
    "HiveXGroupLayer",
    "HiveComponent",
    "HiveRig",
)

logger = zlogging.getLogger(__name__)


def _addExtraNodes(meta, extraNodes):
    """Adds a list a nodes to the layers meta node constants.EXTRANODES_ATTR

    :param meta: The Hive layer to add the metadata connections too, must have the "extraNodes" attribute..
    :type meta: :class:`HiveLayer`
    :param extraNodes: A list of hive nodes to add to the meta node.
    :type extraNodes: iterable[:class:`zapi.DagNode`]
    :return:
    :rtype:
    """
    extraArray = meta.attribute(constants.EXTRANODES_ATTR)
    for n in extraNodes:
        if not n.object():
            continue
        element = extraArray.nextAvailableDestElementPlug()
        n.message.connect(element)


def _addTaggedNode(metaNode, node, tagId):
    comp = metaNode.attribute("zooHiveTaggedNode")
    for element in comp:
        tagPlug = element.child(1)
        existingTagId = tagPlug.value()
        sourceNodePlug = element.child(0)
        if existingTagId == tagId:
            metaNode.connectToByPlug(sourceNodePlug, node)
            return
        elif not sourceNodePlug.isDestination:
            metaNode.connectToByPlug(sourceNodePlug, node)
            tagPlug.set(tagId)
            return
    else:
        newElement = comp[len(comp)]
        metaNode.connectToByPlug(newElement.child(0), node)
        newElement.child(1).set(tagId)


def _taggedNode(metaNode, tagId):
    comp = metaNode.attribute("zooHiveTaggedNode")
    for element in comp:
        existingTagId = element.child(1).value()
        if existingTagId == tagId:
            return element.child(0).sourceNode()


def _taggedNodes(metaNode):
    comp = metaNode.attribute("zooHiveTaggedNode")
    for element in comp:
        source = element.child(0).sourceNode()
        if source is not None:
            yield source


def _findTaggedNodes(metaNode, *tagIds):
    """

    :param tagIds: List of node ids to search for
    :type tagIds: list[str]
    :rtype: list[:class:`zapi.DGNode` or :class:`zapi.DagNode` or None]
    """
    results = [None] * len(tagIds)
    comp = metaNode.attribute("zooHiveTaggedNode")
    for element in comp:
        tagId = element.child(1).value()
        if tagId not in tagIds:
            continue
        source = element.child(0).sourceNode()
        if source is not None:
            results[tagIds.index(tagId)] = source
    return results


class HiveRig(base.MetaBase):
    id = "HiveRig"

    def __init__(self, node=None, name=None, initDefaults=True, lock=True, mod=None):
        super(HiveRig, self).__init__(node, name, initDefaults, lock, mod)

    def delete(self, mod=None, apply=True):
        root = self.rootTransform()
        if root:
            root.lock(False)
            root.delete()
        super(HiveRig, self).delete(mod, apply=apply)

    def displayLayer(self):
        """
        :rtype: :class:`zapi.DisplayLayer`
        """
        displayLayerPlug = self.attribute(constants.DISPLAY_LAYER_ATTR)
        return displayLayerPlug.sourceNode()

    def createDisplayLayer(self, name):
        """

        :param name:
        :type name: str
        :return:
        :rtype: :class:`zapi.DisplayLayer`
        """
        displayLayerPlug = self.attribute(constants.DISPLAY_LAYER_ATTR)
        layer = displayLayerPlug.sourceNode()
        if layer is not None:
            return layer
        layer = zapi.createDisplayLayer(name)
        layer.hideOnPlayback.set(1)
        layer.message.connect(displayLayerPlug)
        return layer

    def deleteControlDisplayLayer(self):
        """Deletes the primary control display layer for the rig instance.

        :rtype: bool
        """
        layer = self.displayLayer()
        if layer:
            return layer.delete()
        return False

    def rigName(self):
        """Returns the name for the rig via the "hName" attribute

        :rtype: str
        """
        return self.attribute(constants.HNAME_ATTR).asString()

    def setBuildScriptConfig(self, configData):
        """Sets the build script configuration not to the metaNode.

        .. note::

            Must be json compatible.

        The configData is in the following form.

        .. code-block:: python

            {
                "buildScriptId": {"propertyName": "propertyValue"}
            }

        :param configData: The configuration data for any/all buildscripts for the current rig.
        :type configData: dict[str,dict]
        """
        self.attribute(constants.BUILD_SCRIPT_CONFIG_ATTR).set(json.dumps(configData))

    def buildScriptConfig(self):
        """Returns the build scripts configuration data.

        See :func:`setBuildScriptConfig` for the structure of the data.

        :return: The build script config dict containing the buildscript id and properties.
        :rtype: dict
        """
        cfgString = self.attribute(constants.BUILD_SCRIPT_CONFIG_ATTR).value()
        try:
            data = json.loads(cfgString)
        except ValueError:
            return {}
        return data

    def metaAttributes(self):
        attrs = super(HiveRig, self).metaAttributes()
        attrs.extend(
            (
                {"name": constants.HNAME_ATTR, "Type": zapi.attrtypes.kMFnDataString},
                {"name": constants.ID_ATTR, "Type": zapi.attrtypes.kMFnDataString},
                {
                    "name": constants.ISHIVE_ATTR,
                    "value": True,
                    "Type": zapi.attrtypes.kMFnNumericBoolean,
                },
                {
                    "name": constants.ISHIVEROOT_ATTR,
                    "value": True,
                    "Type": zapi.attrtypes.kMFnNumericBoolean,
                },
                {
                    "name": constants.ROOTTRANSFORM_ATTR,
                    "Type": zapi.attrtypes.kMFnMessageAttribute,
                },
                {
                    "name": constants.RIG_CONFIG_ATTR,
                    "Type": zapi.attrtypes.kMFnDataString,
                },
                {
                    "name": constants.CONTROL_DISPLAY_LAYER_ATTR,
                    "Type": zapi.attrtypes.kMFnMessageAttribute,
                },
                {
                    "name": constants.ROOT_SELECTION_SET_ATTR,
                    "Type": zapi.attrtypes.kMFnMessageAttribute,
                },
                {
                    "name": constants.CTRL_SELECTION_SET_ATTR,
                    "Type": zapi.attrtypes.kMFnMessageAttribute,
                },
                {
                    "name": constants.DEFORM_SELECTION_SET_ATTR,
                    "Type": zapi.attrtypes.kMFnMessageAttribute,
                },
                {
                    "name": constants.BUILD_SCRIPT_CONFIG_ATTR,
                    "Type": zapi.attrtypes.kMFnDataString,
                },
            )
        )

        return attrs

    def selectionSets(self):
        """Returns the selection sets for this rig as a dict

        :rtype: dict[str, :class:`zapi.ObjectSet` or None]
        """
        ctrlSet = self.sourceNodeByName("zooCtrlSelectionSet")
        deformSet = self.sourceNodeByName("zooDeformSelectionSet")
        rootSet = self.sourceNodeByName("zooRootSelectionSet")
        return {"ctrls": ctrlSet, "deform": deformSet, "root": rootSet}

    def createSelectionSets(self, namingObject):
        existingSet = self.selectionSets()
        root = existingSet["root"]
        rigName = self.attribute(constants.HNAME_ATTR).value()
        if root is None:
            name = namingObject.resolve(
                "rootSelectionSet",
                {"rigName": rigName, "selectionSet": "rig", "type": "objectSet"},
            )
            root = zapi.createDG(name, "objectSet")
            self.connectTo("zooRootSelectionSet", root)
            existingSet["root"] = root

        if existingSet["ctrls"] is None:
            name = namingObject.resolve(
                "selectionSet",
                {"rigName": rigName, "selectionSet": "ctrls", "type": "objectSet"},
            )
            objectSet = zapi.createDG(name, "objectSet")
            root.addMember(objectSet)
            self.connectTo("zooCtrlSelectionSet", objectSet)
            existingSet["ctrls"] = objectSet

        if existingSet["deform"] is None:
            name = namingObject.resolve(
                "selectionSet",
                {"rigName": rigName, "selectionSet": "deform", "type": "objectSet"},
            )
            objectSet = zapi.createDG(name, "objectSet")
            root.addMember(objectSet)
            self.connectTo("zooDeformSelectionSet", objectSet)
            existingSet["deform"] = objectSet

        return existingSet

    def componentLayer(self):
        """Returns ComponentLayer  class instance from the meta node attached to this root

        :return: The ComponentLayer attached to this root
        :rtype: :class:`HiveComponentLayer`
        """
        return self.layer(constants.COMPONENT_LAYER_TYPE)

    def geometryLayer(self):
        """Returns GeometryLayer class instance from the meta node attached to this root.

        :return: The GeometryLayer attached to this root.
        :rtype: :class:`HiveGeometryLayer`
        """
        return self.layer(constants.GEOMETRY_LAYER_TYPE)

    def deformLayer(self):
        """Returns DeformLayer class instance from the meta node attached to this root

        :return: The DeformLayer attached to this root
        :rtype: :class:`HiveDeformLayer`
        """
        return self.layer(constants.DEFORM_LAYER_TYPE)

    def rootTransform(self):
        """Returns the root transform node for this Rig.

        :rtype: :class:`zapi.DagNode` or None
        """
        return self.sourceNodeByName(constants.ROOTTRANSFORM_ATTR)

    def createTransform(self, name, parent):
        layerTransform = zapi.createDag(name=name, nodeType="transform", parent=parent)
        layerTransform.setLockStateOnAttributes(constants.TRANSFORM_ATTRS)
        layerTransform.showHideAttributes(constants.TRANSFORM_ATTRS)

        self.connectTo(constants.ROOTTRANSFORM_ATTR, layerTransform)
        return layerTransform

    def _createLayer(self, hrcName, metaName, parent, layerType):
        newLayerMeta = base.createNodeByType(layerType, name=metaName)
        if not newLayerMeta:
            return
        newLayerMeta.createTransform(hrcName, parent=parent)
        self.addMetaChild(newLayerMeta)
        return newLayerMeta

    def layers(self):
        return [
            i
            for i in (self.geometryLayer(), self.deformLayer(), self.componentLayer())
            if i
        ]

    def layer(self, layerType):
        """Returns the layer attached to this root by type.

        :param layerType: the layer type constant.
        :type layerType: constants.LAYER_TYPE
        :rtype: :class:`layers.BaseLayer`
        """
        # only search a single level down because our 'self._meta' is the component so the layer is only one level deep
        # we use the attribute "layerType"
        meta = self.findChildrenByClassType(layerType, depthLimit=1)
        if not meta:
            return

        root = meta[0]
        if root is None:
            logger.warning("Missing Layer connection: {}".format(layerType))
            return
        return root

    def createLayer(self, layerType, hrcName, metaName, parent=None):
        """Adds Layer by constants type.

        :param layerType:
        :type layerType: constants.LAYER_TYPE
        :param hrcName: The new name for the layer transform
        :type hrcName: str
        :param metaName: The new name for the meta Node
        :type metaName: str
        :param parent: The new parent for the root or None
        :type parent: om2.MObject or None
        :return:
        :rtype: :class:`layers.BaseLayer`
        """

        existingLayer = self.layer(layerType)

        if existingLayer:
            return existingLayer

        return self._createLayer(hrcName, metaName, parent, layerType)


class HiveComponent(base.MetaBase):
    id = "HiveComponent"

    def __init__(self, node=None, name=None, initDefaults=True, lock=True, mod=None):
        super(HiveComponent, self).__init__(node, name, initDefaults, lock, mod)

    def delete(self, mod=None):
        root = self.rootTransform()
        if root:
            root.lock(False)
            root.delete()
        return super(HiveComponent, self).delete(mod)

    def serializeFromScene(self, layerIds=None):
        """Serializes the component from the root transform down using the individual layers, each layer
        has its own logic so see those classes for information.

        :param layerIds: An iterable of Hive layer id types which should be serialized
        :type layerIds: iterable[str]
        :return: The full component dict
        :rtype: dict
        """
        data = {
            "name": self.attribute(constants.HNAME_ATTR).asString(),
            "side": self.attribute(constants.SIDE_ATTR).asString(),
            "type": self.attribute(constants.COMPONENTTYPE_ATTR).asString(),
        }
        # if the rig has been built and the guide hasn't we pull the data from the metanode
        # otherwise serialize the guide structure
        if not self.hasGuide.asBool():
            raw = self.rawDefinitionData()
            return defutils.parseRawDefinition(raw)
        if layerIds:
            for layerId, layerNode in self.layerIdMapping().items():
                if layerId in layerIds:
                    data.update(layerNode.serializeFromScene())
        else:
            for i in iter(self.layers()):
                data.update(i.serializeFromScene())

        return data

    def metaAttributes(self):
        attrs = super(HiveComponent, self).metaAttributes()
        definitionAttrs = [
            {"name": i.split(".")[-1],
             "Type": zapi.attrtypes.kMFnDataString,
             "value": "",
             "default": "", "channelBox":False}
            for i in constants.DEF_CACHE_ATTR_NAMES
        ]
        attrs.extend(
            (
                dict(
                    name=constants.ISHIVEROOT_ATTR,
                    value=False,
                    Type=zapi.attrtypes.kMFnNumericBoolean,
                ),
                dict(
                    name=constants.ISCOMPONENT_ATTR,
                    value=True,
                    Type=zapi.attrtypes.kMFnNumericBoolean,
                ),
                dict(
                    name=constants.CONTAINER_ATTR,
                    Type=zapi.attrtypes.kMFnMessageAttribute,
                ),
                dict(name=constants.HNAME_ATTR, Type=zapi.attrtypes.kMFnDataString),
                dict(name=constants.SIDE_ATTR, Type=zapi.attrtypes.kMFnDataString),
                dict(name=constants.ID_ATTR, Type=zapi.attrtypes.kMFnDataString),
                dict(name=constants.VERSION_ATTR, Type=zapi.attrtypes.kMFnDataString),
                dict(
                    name=constants.COMPONENTTYPE_ATTR,
                    Type=zapi.attrtypes.kMFnDataString,
                ),
                dict(
                    name=constants.HASGUIDE_ATTR,
                    value=False,
                    Type=zapi.attrtypes.kMFnNumericBoolean,
                ),
                dict(
                    name=constants.HASGUIDE_CONTROLS_ATTR,
                    value=False,
                    Type=zapi.attrtypes.kMFnNumericBoolean,
                ),
                dict(
                    name=constants.HASSKELETON_ATTR,
                    value=False,
                    Type=zapi.attrtypes.kMFnNumericBoolean,
                ),
                dict(
                    name=constants.HASRIG_ATTR,
                    value=False,
                    Type=zapi.attrtypes.kMFnNumericBoolean,
                ),
                dict(
                    name=constants.HASPOLISHED_ATTR,
                    value=False,
                    Type=zapi.attrtypes.kMFnNumericBoolean,
                ),
                dict(
                    name=constants.COMPONENTGROUP_ATTR,
                    Type=zapi.attrtypes.kMFnMessageAttribute,
                ),
                dict(
                    name=constants.ROOTTRANSFORM_ATTR,
                    Type=zapi.attrtypes.kMFnMessageAttribute,
                ),
                dict(
                    name=constants.COMPONENTDEFINITION_ATTR,
                    Type=zapi.attrtypes.kMFnCompoundAttribute,
                    children=definitionAttrs,
                ),
            )
        )
        attrs.append(
            dict(
                name="zooHiveTaggedNode",
                Type=zapi.attrtypes.kMFnCompoundAttribute,
                isArray=True,
                children=[
                    dict(
                        name="zooHiveTaggedNodeSource",
                        Type=zapi.attrtypes.kMFnMessageAttribute,
                    ),
                    dict(
                        name="zooHiveTaggedNodeId",
                        Type=zapi.attrtypes.kMFnDataString,
                        value="",
                    ),
                ],
            )
        )
        return attrs

    def rawDefinitionData(self):
        spaceSwitching = self.attribute(name=constants.DEF_CACHE_SPACE_SWITCHING_ATTR)
        info = self.attribute(name=constants.DEF_CACHE_INFO_ATTR)
        prefix = "zooDefCache"
        layerNames = constants.LAYER_DEF_KEYS
        subKeys = (
            constants.DAG_DEF_KEY,
            constants.SETTINGS_DEF_KEY,
            constants.METADATA_DEF_KEY,
            constants.DG_GRAPH_DEF_KEY,
        )
        data = {
            constants.SPACE_SWITCH_DEF_KEY: spaceSwitching.asString() or "[]",
            "info": info.asString() or "{}",
        }

        for layerName in layerNames:
            attrName = prefix + layerName[0].upper() + layerName[1:]
            layerData = {}
            for k in subKeys:
                subAttrName = attrName + k[0].upper() + k[1:]
                try:
                    layerData[k] = self.attribute(subAttrName).asString()
                except AttributeError:  # the DG attr doesn't exist on certain layers
                    pass
            data[layerName] = layerData

        return data

    def saveDefinitionData(self, data):
        for attrName, strData in data.items():
            # include the fullPath to the attr. For some reason without this in 2025 it'll fail.
            attr = self.attribute(name=attrName)
            attr.setString(strData)

    def rootTransform(self):
        """Returns the root transform node for this component.

        :rtype: :class:`zapi.DagNode` or None
        """
        return self.sourceNodeByName(constants.ROOTTRANSFORM_ATTR)

    def createTransform(self, name, parent):
        layerTransform = zapi.createDag(name=name, nodeType="transform", parent=parent)
        layerTransform.setLockStateOnAttributes(constants.TRANSFORM_ATTRS)
        layerTransform.showHideAttributes(constants.TRANSFORM_ATTRS)

        self.connectTo(constants.ROOTTRANSFORM_ATTR, layerTransform)
        layerTransform.lock(True)
        return layerTransform

    def outputLayer(self):
        """Returns Output layer class instance from the meta node attached to this root

        :return: The outputlayer attached to this root
        :rtype: :class:`HiveOutputLayer`
        """
        return self.layer(constants.OUTPUT_LAYER_TYPE)

    def inputLayer(self):
        """Returns InputLayer class instance from the meta node attached to this root

        :return: The InputLayer attached to this root
        :rtype: :class:`HiveInputLayer`
        """
        return self.layer(constants.INPUT_LAYER_TYPE)

    def guideLayer(self):
        """Returns Guide layer class instance from the meta node attached to this root

        :return: The guidelayer attached to this root
        :rtype: :class:`HiveGuideLayer`
        """
        return self.layer(constants.GUIDE_LAYER_TYPE)

    def rigLayer(self):
        """Returns RigLayer class instance from the meta node attached to this root

        :return: The RigLayer attached to this root
        :rtype: :class:`HiveRigLayer`
        """
        return self.layer(constants.RIG_LAYER_TYPE)

    def deformLayer(self):
        """Returns DeformLayer class instance from the meta node attached to this root.

        :return: The DeformLayer attached to this root.
        :rtype: :class:`HiveDeformLayer`
        """
        return self.layer(constants.DEFORM_LAYER_TYPE)

    def geometryLayer(self):
        """Returns GeometryLayer class instance from the meta node attached to this root.

        :return: The GeometryLayer attached to this root.
        :rtype: :class:`HiveGeometryLayer`
        """
        return self.layer(constants.GEOMETRY_LAYER_TYPE)

    def xGroupLayer(self):
        """Returns XGroupLayer class instance from the meta node attached to this root.

        :return: The XGroupLayer attached to this root.
        :rtype: :class:`HiveXGroupLayer`
        """
        return self.layer(constants.XGROUP_LAYER_TYPE)

    def _createLayer(self, hrcName, metaName, parent, layerType):
        newLayerMeta = base.createNodeByType(layerType, name=metaName)
        if not newLayerMeta:
            return
        newLayerMeta.createTransform(name=hrcName, parent=parent)
        self.addMetaChild(newLayerMeta)
        return newLayerMeta

    def layers(self):
        types = (
            HiveGuideLayer.id,
            HiveOutputLayer.id,
            HiveDeformLayer.id,
            HiveInputLayer.id,
            HiveRigLayer.id,
            HiveXGroupLayer.id,
        )
        return self.findChildrenByClassTypes(types, depthLimit=1)

    def layerIdMapping(self):
        types = (
            HiveGuideLayer.id,
            HiveOutputLayer.id,
            HiveDeformLayer.id,
            HiveInputLayer.id,
            HiveRigLayer.id,
            HiveXGroupLayer.id,
        )
        return self.layersById(types)

    def layersById(self, layerIds):
        """Returns a dictionary of layerId: HiveLayer instance or None type.

        This method is preferred when you need to retrieve multiple layers at a time over the
        individual layer methods.

        :param layerIds: Layer type ids to retrieve
        :type layerIds: iterable[str]
        :return:
        :rtype: dict[str, None or :class:`HiveLayer`]
        """
        layersMap = {i: None for i in layerIds}
        for i in self.findChildrenByClassTypes(layerIds, depthLimit=1):
            layersMap[i.id] = i
        return layersMap

    def layer(self, layerType):
        """Returns the layer attached to this root by type.

        :param layerType: the layer type constant.
        :type layerType: constants.LAYER_TYPE
        :rtype: :class:`HiveLayer`
        """
        # only search a single level down because our 'self._meta' is the component so the layer is only one level deep
        # we use the attribute "layerType"
        meta = self.findChildrenByClassType(layerType, depthLimit=1)
        if not meta:
            return

        root = meta[0]
        if root is None:
            logger.warning("Missing Layer connection: {}".format(layerType))
            return
        return root

    def createLayer(self, layerType, hrcName, metaName, parent=None):
        """Creates a new hive layer for specified type if it doesn't already exist.

        :param layerType:
        :type layerType: constants.LAYER_TYPE
        :param hrcName: The new name for the layer Transform
        :type hrcName: str
        :param metaName: The new name for the layer
        :type metaName: str
        :param parent: The new parent for the root or None
        :type parent: om2.MObject or None
        :return:
        :rtype: :class:`HiveLayer`
        """
        existingLayer = self.layer(layerType)
        if existingLayer:
            return existingLayer
        return self._createLayer(hrcName, metaName, parent, layerType)

    addTaggedNode = _addTaggedNode
    taggedNode = _taggedNode
    taggedNodes = _taggedNodes
    findTaggedNodes = _findTaggedNodes


class HiveLayer(base.MetaBase):
    """Base class for hive layer nodes this class inherits from :class:`zapi.DagNode`. Layers are simply
    for organization purposes however they are the main access points for the Dag nodes with the rig.
    """

    _jointsAttr_name = "hJoints"
    _jointsAttrs = (
        {
            "name": "joint",
            "Type": zapi.attrtypes.kMFnMessageAttribute,
            "isArray": False,
        },
        {"name": "jointId", "Type": zapi.attrtypes.kMFnDataString, "isArray": False},
    )

    def __init__(self, node=None, name=None, initDefaults=True, lock=True, mod=None):
        super(HiveLayer, self).__init__(node, name, initDefaults, lock, mod)

    def show(self, mod=None, apply=True):
        root = self.rootTransform()
        if root:
            root.show(mod, apply)

    def hide(self, mod=None, apply=True):
        root = self.rootTransform()
        if root:
            root.hide(mod, apply)

    def rootTransform(self):
        """Returns the root transform node for this layer.

        :rtype: :class:`zapi.DagNode` or None
        """
        return self.sourceNodeByName(constants.ROOTTRANSFORM_ATTR)

    def createTransform(self, name, parent):
        layerTransform = zapi.createDag(name=name, nodeType="transform", parent=parent)
        layerTransform.setLockStateOnAttributes(constants.TRANSFORM_ATTRS)
        layerTransform.showHideAttributes(constants.TRANSFORM_ATTRS)

        self.connectTo(constants.ROOTTRANSFORM_ATTR, layerTransform)
        layerTransform.lock(True)
        return layerTransform

    def delete(self, mod=None, apply=True):
        self.lock(True)
        try:
            [
                s.delete(mod=mod, apply=apply)
                for s in list(self.settingsNodes()) + list(self.extraNodes())
            ]
            transform = self.rootTransform()
            if transform:
                transform.lock(False)
                transform.delete(mod=mod, apply=apply)
        finally:
            self.lock(False)
        return super(HiveLayer, self).delete(mod, apply=apply)

    def metaAttributes(self):
        attrs = super(HiveLayer, self).metaAttributes()
        attrs.append(
            {
                "name": constants.EXTRANODES_ATTR,
                "value": None,
                "Type": zapi.attrtypes.kMFnMessageAttribute,
                "isArray": True,
            }
        )
        attrs.append(
            {
                "name": constants.ROOTTRANSFORM_ATTR,
                "Type": zapi.attrtypes.kMFnMessageAttribute,
            }
        )
        attrs.append(
            {
                "name": constants.ZOO_ANNOTATIONS_ATTR,
                "Type": zapi.attrtypes.kMFnMessageAttribute,
                "isArray": True,
            }
        )
        attrs.append(
            dict(
                name="zooSettingNodes",
                Type=zapi.attrtypes.kMFnCompoundAttribute,
                isArray=True,
                children=[
                    dict(
                        name="zooSettingNode", Type=zapi.attrtypes.kMFnMessageAttribute
                    ),
                    dict(
                        name="zooSettingName",
                        Type=zapi.attrtypes.kMFnDataString,
                        value="",
                    ),
                ],
            )
        )
        attrs.append(
            dict(
                name="zooHiveTaggedNode",
                Type=zapi.attrtypes.kMFnCompoundAttribute,
                isArray=True,
                children=[
                    dict(
                        name="zooHiveTaggedNodeSource",
                        Type=zapi.attrtypes.kMFnMessageAttribute,
                    ),
                    dict(
                        name="zooHiveTaggedNodeId",
                        Type=zapi.attrtypes.kMFnDataString,
                        value="",
                    ),
                ],
            )
        )
        return attrs

    def updateMetaData(self, metaData):
        for metaAttr in metaData:
            attribute = self.attribute(metaAttr["name"])
            if attribute is None:
                self.addAttribute(**metaAttr)
            else:
                attribute.setFromDict(**metaAttr)

    def createSettingsNode(self, name, attrName):
        """Creates a hive settings nodes and adds it to the meta node with the name value

        :param name: The name this node will have
        :type name: str
        :param attrName: The meta attribute Name, The Name will have "settings" prepended for filtering later
        :type attrName: str
        :rtype: :class:`hnodes.SettingsNode`

        """
        node = self.settingNode(attrName)
        if node is not None:
            return node
        node = hnodes.SettingsNode()
        node.create(name, id=attrName)
        compound = self.attribute("zooSettingNodes")
        newElement = compound.nextAvailableDestElementPlug()
        self.connectToByPlug(newElement.child(0), node)
        newElement.child(1).set(attrName)
        node.lock(True)
        return node

    def settingsNodes(self):
        """Returns all the attached settings nodes to the meta node

        :rtype: collections.Iterable[:class:`zoo.libs.hive.base.hivenodes.hnodes.SettingsNode`]
        """
        compound = self.attribute("zooSettingNodes")
        for element in compound:
            sourceNode = element.child(0).sourceNode()
            if sourceNode is not None:
                yield hnodes.SettingsNode(node=sourceNode.object())

    def settingNode(self, name):
        """Finds and returns the settings node if it exists, this is done via the meta node

        :param name: the full settings name
        :type name: str
        :rtype: :class:`hnodes.SettingsNode`

        """
        for settingsNode in self.settingsNodes():
            if settingsNode.id() == name:
                return settingsNode

    def createJoint(self, **kwargs):
        """Creates a joint based on the keyword arguments given.

        .. code-block.. python

            layer = Layer()
            layer.createJoint(**dict(name="myJoint",
                                     translate=om2.MVector(0,0,0),
                                     rotate = om2.MQuaternion(0,0,0,1).
                                     rotateOrder=0,
                                     parent=None,
                                     id="myJointid"
                                     ))


        :keyword name(str):
        :keyword translate(zapi.Vector):
        :keyword rotate(zapi.Quaternion):
        :keyword rotateOrder(int):
        :keyword parent(Joint):
        :keyword id(str):
        :return: The newly created joint.
        :rtype: :class:`hnodes.Joint`
        """
        jnt = hnodes.Joint()
        jnt.create(
            name=kwargs.get("name", "NO_NAME"),
            translate=kwargs.get("translate", (0, 0, 0)),
            rotate=kwargs.get("rotate", (0, 0, 0, 1.0)),
            rotateOrder=kwargs.get("rotateOrder", 0),
            parent=kwargs.get("parent"),
            id=kwargs.get("id", ""),
            attributes=kwargs.get("attributes", [])
        )
        self.addJoint(jnt, kwargs.get("id", ""))
        return jnt

    def findJoints(self, *ids):
        """Finds and returns all the joints with an id in 'ids' in the exact order of 'ids'

        :param ids: the joint ids to find
        :type ids: seq(str)
        :rtype: list[:class:`hnodes.Joint`]
        """
        results = [None] * len(ids)
        for i in self.iterJoints():
            currentId = i.attribute(constants.ID_ATTR).value()
            if currentId in ids:
                results[ids.index(currentId)] = i
        return results

    def iterJoints(self):
        """Generator function which yields the joints attached to this layer in order of the DAG

        :rtype: list[:class:`hnodes.Joint`]
        """
        for i in self.iterJointPlugs():
            source = i.child(0).source()
            if source:
                yield hnodes.Joint(source.node().object())

    def addJoint(self, node, jointId):
        meta = self
        if not meta.hasAttribute(self._jointsAttr_name):
            comp = meta.addCompoundAttribute(
                self._jointsAttr_name, self._jointsAttrs, isArray=True
            )
        else:
            comp = meta.attribute(self._jointsAttr_name)
        comp.isLocked = False
        element = comp.nextAvailableDestElementPlug()
        node.message.connect(element.child(0))
        if not node.hasAttribute(constants.ID_ATTR):
            node.addAttribute(
                name=constants.ID_ATTR,
                Type=zapi.attrtypes.kMFnDataString,
                default="",
                value=jointId,
            )
        element.child(1).set(jointId)

    def joints(self):
        """Returns all the Joints that are under this layer in order of the dag

        :return: A list of Dag ordered joints in the form of MObjects
        :rtype: list(:class:`hnodes.Joint`)
        """
        joints = []
        for element in self.iterJointPlugs():
            jntPlug = element.child(0)
            source = jntPlug.source()
            if not source:
                continue
            joints.append(hnodes.Joint(source.node().object()))
        return joints

    def disconnectAllJoints(self, modifier=None, apply=True):
        """Disconnects all joints from this layer.

        Note::

            This doesn't delete the joints but does delete the joint plug elements on this layer.

        :param modifier: Modifier to run the the set visible on
        :type modifier: :class:`maya.api.OpenMaya.MDGModifier` or :class:`maya.api.OpenMaya.MDagModifier`
        :param apply: Apply the mod automatically if true
        :type apply: bool
        """
        for element in self.iterJointPlugs():
            element.disconnectAll(modifier=modifier)
            element.delete(modifier=modifier)
        if modifier is not None and apply:
            modifier.doIt()

    def deleteJoint(self, jntId):
        jntPlug = None
        node = None
        for element in self.iterJointPlugs():
            idPlug = element.child(1)
            nodePlug = element.child(0)
            if idPlug.asString() == jntId:
                jntPlug = element
                node = nodePlug.sourceNode()
                break
        if jntPlug is not None:
            jntPlug.delete()
        if node is not None:
            node.delete()

    def iterJointPlugs(self):
        """
        :return: Generator where each element is a joint
        :rtype: iterable[:class:`hnodes.Joint`]
        """
        jointParentPlug = self.attribute(self._jointsAttr_name)
        if jointParentPlug is not None:
            for i in jointParentPlug:
                yield i

    def joint(self, name):
        """Returns the joint with the id attached to this layers meta node.

        :param name: the joint id
        :type name: str
        :rtype: :class:`hnodes.Joint` or None
        """
        for element in self.iterJointPlugs():
            idPlug = element.child(1)
            jntPlug = element.child(0)
            if idPlug.asString() == name:
                source = jntPlug.source()
                if not source:
                    return
                return hnodes.Joint(source.node().object())

    def rootJoints(self):
        currentJoints = self.joints()
        for jnt in currentJoints:
            parent = jnt.parent()
            if parent is None or parent not in currentJoints:
                yield jnt

    addExtraNodes = _addExtraNodes

    def addExtraNode(self, node):
        """Adds a single hive node to the extra nodes meta attribute.

        :param node: A hive node to add to the meta attribute.
        :type node: :class:`hivenodes.DGNode`
        """
        _addExtraNodes(self, [node])

    def extraNodes(self):
        for element in self.attribute(constants.EXTRANODES_ATTR):
            source = element.source()
            if source:
                yield source.node()

    addTaggedNode = _addTaggedNode
    taggedNode = _taggedNode
    taggedNodes = _taggedNodes
    findTaggedNodes = _findTaggedNodes

    def createAnnotation(self, name, start, end, attrHolder=None, parent=None):
        """

        :param name: The name for the annotation
        :type name: str
        :param start: The start transform that the annotation will be attached
        :type start: :class:`zapi.DagNode`
        :param end: The end transform that the annotation will be attached
        :type end: :class:`zapi.DagNode`
        :param attrHolder: the node that will have the annotation connected to by a message \
        attribute. useful for queries
        :type attrHolder: :class:`zapi.Plug`
        :rtype: :class:`hnodes.Annotation`
        """
        existingAnnotation = self.annotation(start, end)
        if existingAnnotation:
            return existingAnnotation
        ann = hnodes.Annotation()
        ann.create(name, start, end, attrHolder, parent)
        annArray = self.attribute(constants.ZOO_ANNOTATIONS_ATTR)
        ann.message.connect(annArray.nextAvailableDestElementPlug())
        if start.isHidden() or end.isHidden():
            ann.hide()
            ann.setLockStateOnAttributes(["visibility"], state=True)
        return ann

    def annotation(self, startNode, endNode):
        for ann in self.annotations():
            start = ann.startNode()
            end = ann.endNode()
            if start == startNode and end == endNode:
                return ann

    def annotations(self):
        """

        :return:
        :rtype: iterable[:class:`Annotation`]
        """

        attr = self.attribute(constants.ZOO_ANNOTATIONS_ATTR)
        for ann in attr or []:
            sourceAnn = ann.sourceNode()
            if sourceAnn:
                yield hnodes.Annotation(sourceAnn.object())

    def serializeFromScene(self):
        return {}


class HiveRigLayer(HiveLayer):
    id = "HiveRigLayer"
    _controlsAttr_name = "hControls"

    def controlPanel(self):
        """Returns the controlPanel settings node.

        :return: The Control panel node from the scene.
        :rtype: :class:`hnodes.SettingNode` or None
        """
        return self.settingNode(constants.CONTROL_PANEL_TYPE)

    def metaAttributes(self):
        attrs = super(HiveRigLayer, self).metaAttributes()
        attrs.append(
            {
                "name": HiveRigLayer._controlsAttr_name,
                "isArray": True,
                "children": (
                    {
                        "name": "controlNode",
                        "Type": zapi.attrtypes.kMFnMessageAttribute,
                        "isArray": False,
                    },
                    {
                        "name": "controlId",
                        "Type": zapi.attrtypes.kMFnDataString,
                        "isArray": False,
                    },
                    {
                        "name": "srts",
                        "Type": zapi.attrtypes.kMFnMessageAttribute,
                        "isArray": True,
                    },
                ),
            }
        )
        attrs.append(
            dict(
                name="zooSpaceSwitching",
                Type=zapi.attrtypes.kMFnCompoundAttribute,
                isArray=True,
                children=[
                    dict(
                        name="zooSpaceControlAttrName",
                        Type=zapi.attrtypes.kMFnDataString,
                        value="",
                    ),
                    dict(
                        name="zooSpaceDrivenNode",
                        Type=zapi.attrtypes.kMFnMessageAttribute,
                    ),
                ],
            )
        )
        attrs.append(
            dict(name="hiveCtrlSelectionSet", Type=zapi.attrtypes.kMFnMessageAttribute)
        )
        attrs.append(
            dict(
                name="hiveDGGraph",
                children=(
                    {"name": "hiveDGGraphId", "Type": zapi.attrtypes.kMFnDataString},
                    {
                        "name": "hiveDGGraphNodes",
                        "Type": zapi.attrtypes.kMFnCompoundAttribute,
                        "isArray": True,
                        "children": [
                            {
                                "name": "hiveDGGraphNodeId",
                                "Type": zapi.attrtypes.kMFnDataString,
                            },
                            {
                                "name": "hiveDGGraphNode",
                                "Type": zapi.attrtypes.kMFnMessageAttribute,
                            },
                        ],
                    },
                    {"name": "hiveDGGraphName", "Type": zapi.attrtypes.kMFnDataString},
                    {
                        "name": "hiveDGGraphMetaData",
                        "Type": zapi.attrtypes.kMFnDataString,
                    },
                    {
                        "name": "hiveDGGraphInputNode",
                        "Type": zapi.attrtypes.kMFnMessageAttribute,
                    },
                    {
                        "name": "hiveDGGraphOutputNode",
                        "Type": zapi.attrtypes.kMFnMessageAttribute,
                    },
                ),
                isArray=True,
                locked=False,
            )
        )
        return attrs

    def createSelectionSet(self, name, parent):
        """Creates a selection set control node."

        :param name: The node name to use.
        :type name: str
        :param parent: The parent object set to parent too.
        :type parent: :class:`zapi.ObjectSet`
        :return: Returns the newly create selectionSet or the existing one
        :rtype: :class:`zapi.ObjectSet`
        """
        existingSet = self.sourceNodeByName("hiveCtrlSelectionSet")
        if existingSet is not None:
            return existingSet
        objectSet = zapi.createDG(name, "objectSet")
        if parent is not None:
            parent.addMember(objectSet)
        self.connectTo("hiveCtrlSelectionSet", objectSet)
        return objectSet

    def selectionSet(self):
        """Returns the selection set  control node."

        :rtype: :class:`zapi.ObjectSet` or None
        """
        return self.sourceNodeByName("hiveCtrlSelectionSet")

    def createSpaceSwitch(self, **constraintKwargs):
        """Creates a space switch constraint and sets up the metadata on the rigLayer

        :param constraintKwargs: The space kwargs as :func:`zoo.libs.maya.zapi.spaceswitching.buildConstraint`
        :type constraintKwargs: dict
        :return: The created constraint as a :class:`zoo.libs.maya.zapi.spaceswitching.Constraint`
        :rtype: :class:`zoo.libs.maya.zapi.spaceswitching.Constraint`
        """
        driverInfo = constraintKwargs["drivers"]
        drivenNode = constraintKwargs["driven"]
        name = driverInfo["attributeName"]
        controlPanel = self.settingNode(constants.CONTROL_PANEL_TYPE)
        driverInfo["spaceNode"] = controlPanel
        self.addSpaceSwitchNode(drivenNode, name)
        const, constUtilities = zapi.buildConstraint(**constraintKwargs)
        self.addExtraNodes(constUtilities)
        return const

    def addSpaceSwitchNode(self, driven, name):
        """Adds the specified driven node with the name as the id/attributeName for a spaceSwitch.

        :param driven: The driven transform which contains the constraint.
        :type driven: :class:`zapi.DagNode`
        :param name: The attribute name for the spaceSwitch.
        :type name: str
        """
        spacesAttr = self.attribute("zooSpaceSwitching")
        spaceElement = spacesAttr.nextAvailableDestElementPlug()
        spaceElement.child(0).set(name)
        self.connectToByPlug(spaceElement.child(1), driven)

    def spaceSwitches(self):
        """Iterates the spaces switches on the rigLayer and returns each constraint class.

        :rtype: list[:class:`zoo.libs.maya.zapi.spaceswitching.Constraint`]
        """
        for element in self.zooSpaceSwitching:
            sourceNode = element.child(1).sourceNode()
            if sourceNode is None:
                continue
            for constraint in zapi.iterConstraints(sourceNode):
                yield constraint

    def createControl(self, **kwargs):
        """Create control on the RigLayer

        :rtype: :class:`hnodes.ControlNode`
        """
        cont = hnodes.ControlNode()
        controlParent = kwargs.get("parent", "")

        if not controlParent:
            kwargs["parent"] = self.rootTransform()
        elif isinstance(controlParent, string_types):
            if controlParent == "root":
                kwargs["parent"] = self.rootTransform()
            else:
                kwargs["parent"] = self.control(controlParent)
        cont.create(**kwargs)
        self.addControl(cont)
        for srtDef in kwargs.get("srts", []):
            self.createSrtBuffer(kwargs["id"], srtDef["name"])

        return cont

    def control(self, name):
        """Returns the control node with the given id.

        :param name: The control id to find.
        :type name: str
        :return: The control node.
        :rtype: :class:`hnodes.ControlNode`
        :raises: :class:`zoo.libs.maya.zapi.errors.MissingControlError`
        """
        for element in self.iterControlPlugs():
            idPlug = element.child(1)
            ctrlPlug = element.child(0)
            if idPlug.asString() != name:
                continue
            source = ctrlPlug.source()
            if source is not None:
                return hnodes.ControlNode(source.node().object())
        raise errors.MissingControlError("No controls by the name: {}".format(name))

    def controlForSrt(self, srt):
        """Finds and returns the rig control for the given SRT node.

        :param srt: The srt node to filter.
        :type srt: :class:`zapi.DagNode`
        :return: Either the found control Node or None
        :rtype: :class:`hnodes.ControlNode` or None
        """
        for element in self.iterControlPlugs():
            for srtPlug in element.child(2):
                source = srtPlug.sourceNode()
                if source == srt:
                    return element.child(0).sourceNode()

    def srts(self):
        """Generator function which returns all srts of the rigLayer

        :return: Each srt node on the RigLayer
        :rtype: generator[:class:`zapi.DagNode`]
        """
        for element in self.iterControlPlugs():
            for srtPlug in element.child(2):
                source = srtPlug.sourceNode()
                if source is not None:
                    yield source

    def srt(self, name, index=0):
        """Returns the srt for the given control id.

        :param name: The control Id ie. "upr"
        :type name: str
        :param index: The srt index for the control, defaults to 0 being the root srt.
        :type index: int
        :return: The srt node in the form of a :class:`zapi.DagNode`
        :rtype: :class:`zapi.DagNode`
        """
        for element in self.iterControlPlugs():
            idPlug = element.child(1)
            if idPlug.asString() != name:
                continue
            srtArrayPlug = element.child(2)
            if index in srtArrayPlug.getExistingArrayAttributeIndices():
                source = srtArrayPlug.element(index).sourceNode()
                if source is not None:
                    return source

    def createSrtBuffer(self, controlId, name):
        """Generates a new transform node directly above this control.

        :param name: the shortname for the new srt transform
        :type name: str
        :param controlId: The hive control id to add the srt too.
        :type controlId: str
        :return: the created srt
        :rtype: :class:`zapi.DagNode`
        """
        hControlElement = self.controlPlugById(controlId)
        if hControlElement is None:
            return
        # get the control node so we can parent it to the new srt
        controlSource = hControlElement.child(0).source()  # type: zapi.Plug
        controlNode = hnodes.ControlNode(controlSource.node().object())
        srtPlug = hControlElement[2]
        nextElement = srtPlug.nextAvailableDestElementPlug()
        ctrlParent = controlNode.parent()
        newSrt = zapi.createDag(name, "transform")
        newSrt.setParent(ctrlParent)
        newSrt.setWorldMatrix(controlNode.worldMatrix())
        newSrt.attribute("shear").set((0, 0, 0))
        controlNode.setParent(newSrt, useSrt=False)
        newSrt.message.connect(nextElement)
        return newSrt

    def addControl(self, control):
        """Adds the give ControlNode instance to the rigLayer.

        :param control: The control to add. Should not already be attached to the layer.
        :type control: :class:`hnodes.ControlNode`
        """
        comp = self.attribute(self._controlsAttr_name)
        comp.isLocked = False
        element = comp.nextAvailableDestElementPlug()
        control.message.connect(element.child(0))
        element.child(1).set(control.id())
        srt = control.srt()
        if srt is not None:
            srt.message.connect(element.child(2))

    def iterControlPlugs(self):
        """Generator function which returns all control attribute plugs on the rigLayer.

        :rtype: iterator[:class:`zapi.Plug`]
        """
        # _controlsAttr_name is an array component plug
        controlParentPlug = self.attribute(self._controlsAttr_name)

        if controlParentPlug is not None:
            for i in controlParentPlug:
                yield i

    def iterControls(self, recursive=False):
        """Generator function which returns all controls on the rigLayer.

        :param recursive: Whether to recursively search for controls in child rig layer layers e.g. child components.
        :type recursive: bool
        :rtype: iterable[:class:`hnodes.ControlNode`]
        """
        for element in self.iterControlPlugs():
            ctrlPlug = element.child(0)
            source = ctrlPlug.source()
            if not source:
                continue
            yield hnodes.ControlNode(source.node().object())
        if recursive:
            for mChild in self.findChildrenByClassType(
                constants.RIG_LAYER_TYPE, depthLimit=1
            ):
                childLayer = HiveRigLayer(node=mChild)
                for c in childLayer.iterControls():
                    yield c

    def findControls(self, *ids):
        """Returns all the controls with the given ids in the specified order, if the control
        isn't found, then None is returned in its place.

        :param ids: The control unique ids to search for.
        :type ids: iterable[str]
        :rtype: list[:class:`hnodes.ControlNode` or None]
        """
        results = [None] * len(ids)

        for ctrl in self.iterControls(recursive=False):
            ctrlId = ctrl.id()
            if ctrlId not in ids:
                continue
            results[ids.index(ctrlId)] = ctrl
        return results

    def controlPlugById(self, name):
        """Returns the control Plug for the given control id.

        :param name: The control id to search for.
        :type name: str
        :rtype: :class:`zapi.Plug`
        """
        for element in self.iterControlPlugs():
            idPlug = element.child(1)
            if idPlug.asString() == name:
                return element

    def serializeFromScene(self):
        data = {}
        for i in self.settingsNodes():
            data[i.id()] = i.serializeFromScene()

        return {
            constants.RIGLAYER_DEF_KEY: {
                constants.SETTINGS_DEF_KEY: data,
                constants.DAG_DEF_KEY: [],
                constants.DG_GRAPH_DEF_KEY: [],
            }
        }

    createNamedGraph = dggraph.createNamedGraph
    hasNamedGraph = dggraph.hasNamedGraph
    namedGraph = dggraph.namedGraph
    namedGraphs = dggraph.namedGraphs
    deleteNamedGraph = dggraph.deleteNamedGraph
    findNamedGraphs = dggraph.findNamedGraphs


class HiveComponentLayer(HiveLayer):
    id = "HiveComponentLayer"

    def metaAttributes(self):
        attrs = super(HiveComponentLayer, self).metaAttributes()
        attrs.append(
            {
                "name": "componentGroups",
                "isArray": True,
                "locked": False,
                "children": [
                    {"name": "groupName", "Type": zapi.attrtypes.kMFnDataString},
                    {
                        "name": "groupComponents",
                        "Type": zapi.attrtypes.kMFnMessageAttribute,
                        "locked": False,
                        "isArray": True,
                    },
                ],
            }
        )

        return attrs

    def components(self, depthLimit=256):
        """Returns all the components in order as a list this uses the meta node attached to this layer

        :rtype: list(Component)
        """
        return list(self.iterComponents(depthLimit=depthLimit))

    def iterComponents(self, depthLimit=256):
        """Generator function that iterates the components and returns it's meta node.

        :param depthLimit: The depth limit to search for components.
        :type depthLimit: int
        :return:
        :rtype: :class:`HiveComponent`
        """
        for cp in self.iterMetaChildren(depthLimit=depthLimit):
            if cp.hasAttribute("componentType"):
                yield cp

    def iterGroupPlugs(self):
        """Generator function that iterates the componentGroups plug elements on the component layer.

        :return:
        :rtype: generator(om2.MPlug)
        """
        groupPlug = self.componentGroups
        for element in groupPlug:
            yield element

    def groupElementPlug(self, name):
        """Returns the Component group element Plug from the component Layer.

        :param name: The group name to find.
        :type name: str
        :return: None if the group name can't be found.
        :rtype: om2.Plug or None
        """
        for groupElement in self.iterGroupPlugs():
            groupName = groupElement.child(0).asString()
            if groupName == name:
                return groupElement

    def groupNames(self):
        """Returns a list of group names:

        :return: a list of str representing the group name
        :rtype: list(str)
        """
        for groupElement in self.iterGroupPlugs():
            name = groupElement.child(0).asString()
            if name:
                yield name

    def removeFromGroup(self, name, components):
        """Removes a list of components from the component group.

        :param name: The group name to remove the component from
        :type name: str
        :param components: A list of components to remove.
        :type components: list(:class:`component.Component`)
        :return: True if the components were removed.
        :rtype: bool
        """
        existingGroup = self.groupElementPlug(name)
        if existingGroup is None:
            return False
        childGroupPlug = existingGroup.child(1)
        componentsMeta = [i.meta for i in components]
        elementsToRemove = []
        for element in childGroupPlug:
            connectedComponentMeta = element.source()
            if (
                connectedComponentMeta
                and connectedComponentMeta.node() in componentsMeta
            ):
                element.disconnectAll()
                elementsToRemove.append(element)
        for element in elementsToRemove:
            element.delete()
        return True

    def createGroup(self, name, components=None):
        """Creates a component group on the component layer.

        :param name: The new component group
        :type name: str
        :param components: The components to add or None
        :type components: iterable(:class:`Component`) or None
        :return: True if the component group was added.
        :rtype: bool
        :raise: :class:`errors.ComponentGroupAlreadyExists`
        """
        components = components or []
        # pre-flight check for an existing groupName
        existingGroup = self.groupElementPlug(name)
        if existingGroup is not None:
            raise errors.ComponentGroupAlreadyExists(name)
        groupPlug = self.componentGroups

        # find the first available group solely based on whether the group has an empty name,
        # since its valid to have a group without a set of components attached
        if len(groupPlug) != 0:
            for group in groupPlug:
                if group.child(0).value() == "":
                    availableElement = group
                    break
            else:
                return
        else:
            availableElement = groupPlug[0]

        if components:
            for i in components:
                componentElement = availableElement.child(
                    1
                ).nextAvailableDestElementPlug()
                i.meta.componentGroup.connect(componentElement)

        availableElement.child(0).setString(name)

        return True

    def addToGroup(self, name, components):
        """Adds the components to the component group.

        :param name: The component group name
        :type name: str
        :param components: A list of component instances.
        :type components: iterable(:class:`component.Component`)
        :return: True if at least one component added.
        :rtype: bool
        """
        existingGroup = self.groupElementPlug(name)
        if existingGroup is None:
            return False
        childGroupPlug = existingGroup.child(1)

        added = False
        for i in components:
            newElement = childGroupPlug.nextAvailableDestElementPlug()
            i.meta.componentGroup.connect(newElement)
            added = True
        return added

    def removeGroup(self, name):
        """Remove's the entire component group and it's children.

        :param name: The group name to remove.
        :type name: str
        :return: True if the group was removed.
        :rtype: bool
        """
        groupElement = self.groupElementPlug(name)
        if not groupElement:
            return False
        groupElement.child(0).set("")
        for element in groupElement.child(1):
            element.disconnectAll()
        groupElement.delete()
        return True

    def iterComponentsNamesForGroup(self, name):
        """Generator function to iterate over all the component instances of a group.

        :param name: The name of the group to iterate
        :type name: str
        :rtype: Generator[:class:`component.Component`]
        """
        existingGroup = self.groupElementPlug(name)
        if existingGroup is None:
            return
        childGroupPlug = existingGroup.child(1)
        for element in childGroupPlug:
            source = element.source()
            if source is None:
                continue
            meta = source.node()
            name = meta.attribute(constants.HNAME_ATTR).asString()
            side = meta.atrtibute(constants.SIDE_ATTR).asString()
            yield name, side


class HiveGuideLayer(HiveLayer):
    id = "HiveGuideLayer"
    _guideAttr_name = "hguides"

    def serializeFromScene(
        self, skipAttributes=(), includeConnections=True, extraAttributesOnly=False
    ):
        root = self.guideRoot()
        dag = []
        if root:
            dag.append(
                root.serializeFromScene(
                    extraAttributesOnly=True, includeNamespace=False, useShortNames=True
                )
            )
        sd = []
        for se in iter(self.settingsNodes()):
            sd.extend(
                se.serializeFromScene(
                    extraAttributesOnly=True, includeNamespace=False, useShortNames=True
                )
            )
        metaData = []
        for attrName in (
            "guideVisibility",
            "guideControlVisibility",
            "pinnedConstraints",
            "pinned",
        ):
            metaData.append(self.attribute(attrName).serializeFromScene())
        data = {
            constants.GUIDELAYER_DEF_KEY: {
                constants.DAG_DEF_KEY: dag,
                constants.SETTINGS_DEF_KEY: sd,
                constants.METADATA_DEF_KEY: metaData,
                constants.DG_GRAPH_DEF_KEY: [],
            }
        }
        return data

    def metaAttributes(self):
        attrs = super(HiveGuideLayer, self).metaAttributes()

        attrs.append(
            dict(
                name=self._guideAttr_name,
                children=(
                    {
                        "name": "guideNode",
                        "Type": zapi.attrtypes.kMFnMessageAttribute,
                        "isArray": False,
                    },
                    {
                        "name": "guideId",
                        "Type": zapi.attrtypes.kMFnDataString,
                        "isArray": False,
                    },
                    {
                        "name": "srts",
                        "Type": zapi.attrtypes.kMFnMessageAttribute,
                        "isArray": True,
                    },
                    {
                        "name": "shapeNode",
                        "Type": zapi.attrtypes.kMFnMessageAttribute,
                        "isArray": False,
                    },
                    {
                        "name": "sourceGuides",
                        "Type": zapi.attrtypes.kMFnCompoundAttribute,
                        "isArray": True,
                        "children": [
                            {
                                "name": "sourceGuide",
                                "Type": zapi.attrtypes.kMFnMessageAttribute,
                                "isArray": False,
                            },
                            {
                                "name": "constraintNodes",
                                "Type": zapi.attrtypes.kMFnMessageAttribute,
                                "isArray": True,
                            },
                        ],
                    },
                    {
                        "name": "guideMirrorRotation",
                        "Type": zapi.attrtypes.kMFnNumericBoolean,
                    },
                    {
                        "name": "guideAutoAlign",
                        "Type": zapi.attrtypes.kMFnNumericBoolean,
                    },
                    {
                        "name": "guideAimVector",
                        "Type": zapi.attrtypes.kMFnNumeric3Float,
                    },
                    {"name": "guideUpVector", "Type": zapi.attrtypes.kMFnNumeric3Float},
                ),
                isArray=True,
                locked=False,
            )
        )
        attrs.append(
            dict(
                name="guideVisibility",
                Type=zapi.attrtypes.kMFnNumericBoolean,
                default=True,
                value=True,
            )
        )
        attrs.append(
            dict(
                name="guideControlVisibility",
                Type=zapi.attrtypes.kMFnNumericBoolean,
                default=False,
                value=False,
            )
        )
        attrs.append(
            dict(
                name="pinSettings",
                children=[
                    dict(name="pinned", Type=zapi.attrtypes.kMFnNumericBoolean),
                    dict(name="pinnedConstraints", Type=zapi.attrtypes.kMFnDataString),
                ],
            )
        )
        attrs.append(
            {
                "name": "hiveLiveLinkNodes",
                "Type": zapi.attrtypes.kMFnMessageAttribute,
                "isArray": True,
            }
        )
        attrs.append(
            {
                "name": "hiveIsLiveLinkActive",
                "Type": zapi.attrtypes.kMFnNumericBoolean,
                "value": False,
                "default": False,
            }
        )
        attrs.append(
            {
                "name": "hiveGuideAnnotationGrp",
                "Type": zapi.attrtypes.kMFnMessageAttribute,
            }
        )
        attrs.append(
            {
                "name": "hiveDGGraph",
                "children": (
                    {"name": "hiveDGGraphId", "Type": zapi.attrtypes.kMFnDataString},
                    {
                        "name": "hiveDGGraphNodes",
                        "Type": zapi.attrtypes.kMFnCompoundAttribute,
                        "isArray": True,
                        "children": [
                            {
                                "name": "hiveDGGraphNodeId",
                                "Type": zapi.attrtypes.kMFnDataString,
                            },
                            {
                                "name": "hiveDGGraphNode",
                                "Type": zapi.attrtypes.kMFnMessageAttribute,
                            },
                        ],
                    },
                    {"name": "hiveDGGraphName", "Type": zapi.attrtypes.kMFnDataString},
                    {
                        "name": "hiveDGGraphMetaData",
                        "Type": zapi.attrtypes.kMFnDataString,
                    },
                    {
                        "name": "hiveDGGraphInputNode",
                        "Type": zapi.attrtypes.kMFnMessageAttribute,
                    },
                    {
                        "name": "hiveDGGraphOutputNode",
                        "Type": zapi.attrtypes.kMFnMessageAttribute,
                    },
                ),
                "isArray": True,
                "locked": False,
            }
        )
        return attrs

    def isPinned(self):
        if not self.exists():
            return False
        return self.pinned.value()

    def alignGuides(self):
        guides = list(self.iterGuides(includeRoot=False))
        if not guides:
            return
        matrices = []
        alignGuides = []
        newTransforms = {}
        for guide in guides:
            aimState = guide.autoAlign.asBool()
            if not aimState:
                continue
            upVector = guide.autoAlignUpVector.value()
            aimVector = guide.autoAlignAimVector.value()

            child = None  # type: hnodes.Guide or None
            for child in guide.iterChildGuides(recursive=False):
                break
            if child is None:
                parentGuide, _ = guide.guideParent()

                parentMatrix = newTransforms.get(parentGuide.id(), guide.worldMatrix())
                transform = zapi.TransformationMatrix(parentMatrix)
                transform.setTranslation(
                    guide.translation(zapi.kWorldSpace), zapi.kWorldSpace
                )
                transform.setScale(guide.scale(zapi.kWorldSpace), zapi.kWorldSpace)
                matrix = transform.asMatrix()
            else:
                transform = guide.transformationMatrix()
                rot = mayamath.lookAt(
                    guide.translation(),
                    child.translation(),
                    zapi.Vector(aimVector),
                    zapi.Vector(upVector),
                )
                transform.setRotation(rot)
                matrix = transform.asMatrix()
            newTransforms[guide.id()] = matrix
            matrices.append(matrix)
            alignGuides.append(guide)
        if alignGuides and matrices:
            hnodes.setGuidesWorldMatrix(alignGuides, matrices)

    def iterGuideCompound(self):
        guidePlug = self.attribute(self._guideAttr_name)
        for i in range(guidePlug.evaluateNumElements()):
            yield guidePlug.elementByPhysicalIndex(i)

    def _addGuideToMeta(self, guide):
        """Add guide to Meta

        :param guide: The guide to add
        :type guide: zoo.libs.hive.base.hivenodes.hnodes.Guide
        :return: The compound plug
        :rtype: :class:`Plug`
        """
        comp = self.attribute(self._guideAttr_name)
        comp.isLocked = False
        element = comp.nextAvailableDestElementPlug()
        guide.message.connect(element.child(0))
        element.child(1).set(guide.id())
        shapeNode = guide.shapeNode()
        if shapeNode is not None:
            shapeNode.message.connect(element.child(3))
        element.child(5).setAsProxy(guide.attribute(constants.MIRROR_ATTR))
        element.child(6).setAsProxy(guide.attribute(constants.AUTOALIGN_ATTR))
        element.child(7).setAsProxy(guide.attribute(constants.AUTOALIGNAIMVECTOR_ATTR))
        element.child(8).setAsProxy(guide.attribute(constants.AUTOALIGNUPVECTOR_ATTR))
        return comp

    def addChildGuide(self, guide):
        """Attaches a guide node to this layer.

        :param guide: The guide to attach to this layer
        :type guide: :class:`hnodes.Guide`
        """
        if not isinstance(guide, zapi.DagNode):
            raise ValueError("Child node must be a DagNode instance")
        self._addGuideToMeta(guide)

    def createGuide(self, **kwargs):
        """Creates a guide node and attaches it to the guideLayer

        :keyword id (str): The guide unique identifier relative to the guideLayer instance.
        :keyword name (dict): The guide name.
        :keyword translate (list[float]): The translate x,y,z in world space.
        :keyword rotate (list[float]): The rotation x,y,z in world space.
        :keyword scale (list[float]): The scale x,y,z in world space.
        :keyword: rotateOrder (int): The rotate order using the attrtypes.kConstant value.
        :keyword shape (str or dict): If str then the shape name in the shapelib else the serialized shapes.
        :keyword color (list[float]): The shape color to use in the case where 'shape' is a string.
        :keyword shapeTransform (dict): The shape pivot transform, same transform keys as this method.
        :keyword parent (str or zapi.DagNode):
        :keyword root (bool): Whether this guide is the root guide of the the component.
        :keyword worldMatrix (list[float] or zapi.Matrix): The worldMatrix for the guide which takes priority over the \
                                                           local transform.
        :keyword matrix (list[float] or zapi.Matrix): The local matrix for the guide
        :keyword srts (list[dict]):
        :keyword selectionChildHighlighting ():
        :keyword pivotShape (str):
        :keyword pivotColor (list[float]):
        :keyword attributes (list[dict]):
        :rtype: :class:`hnodes.Guide`

        .. code-block:: python

            g= GuideLayer().create()
            g.createGuide({"name": "godnode",
            ...                "translate": [0.0, 0.0, 0.0],
            ...                "rotate": [0.0, 0.0, 0.0],
            ...                "rotateOrder": 0,
            ...                "shape": "godnode",
            ...                "id": "godnode",
            ...                "children": [],
            ...                "color": [],
            ...                "selectionChildHighlighting": False
            ...                "autoAlign": True,
            ...                "shapeTransform": {"translate": [0.0,0.0,0.0], "scale": [1,1,1],
            ...                                 "rotate": [0.0,0.0,0.0],
            ...                "rotateOrder": 0}
            ...                })

        """
        parent = kwargs.get("parent")
        parent = self.rootTransform() if parent is None else self.guide(parent)
        kwargs["parent"] = parent
        guid = hnodes.Guide()
        guid.create(**kwargs)
        self.addChildGuide(guid)
        guidePlug = self.guidePlugById(kwargs.get("id", ""))

        if guidePlug is None:
            return guid
        srtPlug = guidePlug.child(2)
        guid.setShapeParent(self.rootTransform())
        # now loop the srts in order of index and create them
        parentNode = guid.parent() or self.rootTransform()
        srts = kwargs.get("srts", [])
        for srt in srts:
            if parentNode is not None:
                parentNode = parentNode.object()
            newSrt = zapi.DagNode(nodes.deserializeNode(srt, parent=parentNode)[0])
            parentNode = newSrt
            srtElement = srtPlug.nextAvailableDestElementPlug()
            newSrt.message.connect(srtElement)

        guid.setParent(parentNode, useSrt=False)
        return guid

    def duplicateGuide(self, guide, name, guideId, parent=None):
        guideData = guide.serializeFromScene()
        guideData["parent"] = parent or guide
        guideData["name"] = name
        guideData["id"] = guideId
        newGuide = self.createGuide(**guideData)
        return newGuide

    def guideSettings(self):
        """Guide settings node

        :rtype: :class:`hnodes.SettingsNode`
        """
        return self.settingNode(constants.GUIDE_LAYER_TYPE)

    def createSrtBuffer(self, controlId, name):
        """Generates a new transform node directly above this control.

        :param name: the shortname for the new srt transform
        :type name: str
        :return: the created srt
        :rtype: :class:`zapi.DagNode`
        """
        hControlElement = self.guidePlugById(controlId)
        if hControlElement is None:
            return
        controlNode = hnodes.ControlNode(hControlElement.child(0).sourceNode().object())
        srtPlug = hControlElement.child(2)
        srtElement = srtPlug.nextAvailableDestElementPlug()
        ctrlParent = controlNode.parent()

        newSrt = zapi.createDag(name, "transform")
        newSrt.setRotationOrder(controlNode.rotationOrder())
        newSrt.setWorldMatrix(controlNode.worldMatrix())
        newSrt.setParent(ctrlParent)
        controlNode.setParent(newSrt, useSrt=False)
        newSrt.message.connect(srtElement)
        return newSrt

    @zapi.lockNodeContext
    def deleteGuides(self, *guideIds):
        """Deletes all guides from the layer

        The method loops through each plug element of the hguides compound gathering
        every node along the way then deleting them all before clearing the array attribute
        of it's indices.
        """
        logger.debug("Deleting guides from layer: {}".format(self))
        if not self.exists() or not self.hasAttribute(self._guideAttr_name):
            return
        guides = {}
        annotations = set()
        for i in self.iterGuides():
            guideId = i.id()
            i.lock(False)

            if guideId not in guideIds:
                continue
            parentGuide = i.guideParent()[0]
            guides[i.id()] = (i, i.shapeNode())
            annotation = self.annotation(i, parentGuide)
            if annotation:
                annotations.add(annotation)
        for i in annotations:
            i.delete()
        for guide, guideShape in guides.values():
            if guideShape is not None:
                guideShape.delete()
            guide.delete()

        for element in list(self.iterGuideCompound()):
            guideId = element.child(1).asString()
            if guideId not in guideIds:
                continue
            del guides[guideId]
            element.delete()

        for i, _ in guides.values():
            i.lock(True)

    def srt(self, name, index=0):
        for element in self.iterControlPlugs():
            idPlug = element.child(1)
            if idPlug.asString() != name:
                continue
            srtArrayPlug = element.child(2)
            if index in srtArrayPlug.getExistingArrayAttributeIndices():
                source = srtArrayPlug.getElementByLogicalIndex[index].sourceNode()
                if source is not None:
                    return source

    def findGuides(self, *guideIds):
        """
        :param guideIds:
        :type guideIds: iterable[str]
        :return:
        :rtype: list[:class:`hnodes.Guide`]
        """
        if not self.exists():
            return []
        results = [None] * len(guideIds)
        for guide in self.iterGuides():
            guideId = guide.id()
            if guideId in guideIds:
                results[guideIds.index(guideId)] = guide
        return results

    def isGuidesVisible(self):
        return self.guideVisibility.value()

    def isGuideControlVisible(self):
        """

        :return:
        :rtype:
        """
        return self.guideControlVisibility.value()

    def setGuideControlVisible(self, state, mod=None, apply=True):
        """Sets all controls visible state.

        :param state: Visible if True, false otherwise
        :type state: bool
        :param mod: Modifier to run the the set visible on
        :type mod: :class:`maya.api.OpenMaya.MDGModifier` or :class:`maya.api.OpenMaya.MDagModifier`
        :param apply: Apply the mod automatically if true
        :type apply: bool
        """
        for guide in self.iterGuides():
            shape = guide.shapeNode()
            if shape is None:
                continue
            shape.setVisible(state, mod=mod, apply=apply)
        self.guideControlVisibility.set(state)

    def setGuidesVisible(self, state, includeRoot=True, mod=None, apply=True):
        """Set Guides Pivots visible

        :param state: Visible if True, false otherwise
        :type state: bool
        :param includeRoot: Whether the root guide should be included.
        :type includeRoot: bool
        :param mod: Modifier to run the the set visible on
        :type mod: :class:`maya.api.OpenMaya.MDGModifier` or :class:`maya.api.OpenMaya.MDagModifier`
        :param apply: Apply the mod automatically if true
        :type apply: bool
        """
        modifier = mod or zapi.dgModifier()
        annotations = self.annotations()
        for guide in self.iterGuides(includeRoot=includeRoot):
            if guide.visibility.isLocked:
                continue
            guide.setVisible(state, mod=modifier, apply=False)
        for ann in annotations:
            if ann.visibility.isLocked:
                continue

            ann.setVisible(state, mod=modifier, apply=False)
        self.guideVisibility.set(state, mod=modifier, apply=apply)
        if mod or apply:
            modifier.doIt()
        return modifier

    def guide(self, name):
        """Returns the guide hiveNode for the given name, this will use the meta node connections to find the correct
        guide.

        :param name: shortname eg. upr  do not provide the prefix GUIDE as this is done internally
        :type name: str
        :return: :class:`hnodes.Guide` instance
        :rtype: :class:`hnodes.Guide` or None
        """
        if not self.exists():
            return
        for gui in self.iterGuides():
            if gui.id() == name:
                return gui

    def iterGuides(self, includeRoot=True):
        """Iterate through the guides which are connected to this layer.

        Iteration order is based on the order the guides were added to the layer
        regardless of Dag order.

        :return: Generator where each element is a guide.
        :rtype: Iterable[:class:`hnodes.Guide`]
        """
        if not self.exists() or not self.hasAttribute(self._guideAttr_name):
            return
        for element in self.iterGuideCompound():
            guidePlug = element.child(0)
            source = guidePlug.sourceNode()
            if source is None:
                continue
            if not includeRoot and element.child(1).asString() == "root":
                continue
            if hnodes.Guide.isGuide(source):
                yield hnodes.Guide(source.object())

    def guideCount(self):
        guidePlug = self.attribute(self._guideAttr_name)
        return guidePlug.evaluateNumElements()

    def guidePlugById(self, name):
        for element in self.iterGuideCompound():
            idPlug = element.child(1)
            if idPlug.asString() == name:
                return element

    def guideNodePlugById(self, name):
        guideElementPlug = self.guidePlugById(name)
        if not guideElementPlug:
            return
        return guideElementPlug.child(0)

    def sourceGuidePlugById(self, guideId, sourceIndex):
        guideElement = self.guidePlugById(guideId)
        if not guideElement:
            return
        return guideElement.child(4)[sourceIndex]

    def guideRoot(self):
        """Returns the guide which contains the isRoot attribute as True.

        :rtype: :class:`hnodes.Guide`
        """
        if not self.exists() or not self.hasAttribute(self._guideAttr_name):
            return
        for element in self.iterGuideCompound():
            isRootFlag = element.child(2)
            if not isRootFlag:
                continue
            source = element.child(0).sourceNode()
            if source is not None:
                return hnodes.Guide(source.object())

    def isLiveLink(self):
        """Determines if the current layer is set to be linked to the live guiding system

        :rtype: bool
        """
        return self.attribute("hiveIsLiveLinkActive").asBool()

    def setLiveLink(self, offsetNode, state=True):
        """Live links the guides on the current guideLayer to the provided offsetNode.

        This is done by directly connected the worldInverseMatrix plug to the skin clusters
        bindPreMatrix. By Doing this we allow the joints transforms to move without effect
        the skin.

        :param offsetNode: The input guide offset node which contains the local matrices
        :type offsetNode: :class:`hnodes.SettingsNode`
        :param state: if True then the joints will be connected to the bindPreMatrix and \
        the offsetNode matrices will be connected to the local transform of the joint.
        :type state: bool
        """
        currentState = self.isLiveLink()
        if state == currentState:
            return
        metaDataAttr = self.attribute("hiveLiveLinkNodes")
        for source, dest in offsetNode.iterConnections(source=False, destination=True):
            if plugs.plugType(dest) == zapi.attrtypes.kMFnDataMatrix:
                dest.disconnect(source)
        sourceNodesToDelete = []
        for element in metaDataAttr:
            source = element.sourceNode()
            if source is not None:
                sourceNodesToDelete.append(source.fullPathName())
        if sourceNodesToDelete:
            cmds.delete(sourceNodesToDelete)
        self.attribute("hiveIsLiveLinkActive").set(state)
        if not state:
            return
        transformArray = offsetNode.attribute("transforms")
        transformElements = {i.child(0).asString(): i for i in transformArray}
        for guide in self.iterGuides():
            guideTransformPlug = transformElements.get(guide.id())  # type: zapi.Plug
            if not guideTransformPlug:
                continue
            localMatrixPlug = guideTransformPlug.child(1)
            worldMatrixPlug = guideTransformPlug.child(2)
            parentMatrixPlug = guideTransformPlug.child(3)
            parentGuide, guideParentId = guide.guideParent()
            metaDataPlug = metaDataAttr.nextAvailableDestElementPlug()
            metaDataIndex = metaDataPlug.logicalIndex()
            guide.attribute("worldMatrix")[0].connect(worldMatrixPlug)

            if guideParentId is None:
                localMatrix = guide.attribute("matrix")
            else:
                pickMatDest = parentGuide
                if guideParentId == "root":
                    pickMatDest = parentGuide.srt()
                    if (
                        pickMatDest is None
                    ):  # should be temp as why should be removing srts from the root guide
                        pickMatDest = parentGuide
                guide.attribute("parentMatrix")[0].connect(parentMatrixPlug)
                liveMult = zapi.createDG(
                    "_".join([parentGuide.name(), "liveGuideMult"]), "multMatrix"
                )
                worldMatrix = guide.attribute("worldMatrix")[0]
                worldInverse = pickMatDest.attribute("worldInverseMatrix")[0]
                pickMatrix = zapi.createDG(
                    "_".join([parentGuide.name(), "pickScale"]), "pickMatrix"
                )
                pickMatrix.useRotate = False
                pickMatrix.useTranslate = False
                pickMatrix.useShear = False

                worldMatrix.connect(liveMult.matrixIn[0])
                worldInverse.connect(liveMult.matrixIn[1])
                pickMatrix.outputMatrix.connect(liveMult.matrixIn[2])
                localMatrix = liveMult.matrixSum
                liveMult.message.connect(metaDataPlug)
                pickMatrix.message.connect(metaDataAttr[metaDataIndex + 1])
                pickMatDest.attribute("worldMatrix")[0].connect(pickMatrix.inputMatrix)

            localMatrix.connect(localMatrixPlug)

    def setManualOrient(self, state):
        for guide in self.iterGuides(includeRoot=False):
            guide.attribute(constants.AUTOALIGN_ATTR).set(not state)
            if not state:
                guide.setDisplayAxisShapeVis(state)

    def delete(self, mod=None, apply=True):
        for guide in self.iterGuides():
            guide.lock(False)

        return super(HiveGuideLayer, self).delete(mod, apply=apply)

    createNamedGraph = dggraph.createNamedGraph
    hasNamedGraph = dggraph.hasNamedGraph
    namedGraph = dggraph.namedGraph
    namedGraphs = dggraph.namedGraphs
    deleteNamedGraph = dggraph.deleteNamedGraph
    findNamedGraphs = dggraph.findNamedGraphs


class HiveInputLayer(HiveLayer):
    id = "HiveInputLayer"
    _primaryAttr_name = "hInputs"

    def metaAttributes(self):
        attrs = super(HiveInputLayer, self).metaAttributes()
        attrs.append(
            {
                "name": HiveInputLayer._primaryAttr_name,
                "isArray": True,
                "children": [
                    {
                        "name": "inputNode",
                        "Type": zapi.attrtypes.kMFnMessageAttribute,
                        "isArray": False,
                    },
                    {
                        "name": "inputId",
                        "Type": zapi.attrtypes.kMFnDataString,
                        "isArray": False,
                    },
                    {
                        "name": "isInputRoot",
                        "Type": zapi.attrtypes.kMFnNumericBoolean,
                        "isArray": False,
                    },
                    {
                        "name": "sourceInputs",
                        "Type": zapi.attrtypes.kMFnCompoundAttribute,
                        "isArray": True,
                        "children": [
                            {
                                "name": "sourceInput",
                                "Type": zapi.attrtypes.kMFnMessageAttribute,
                            },
                            {
                                "name": "constraintNodes",
                                "Type": zapi.attrtypes.kMFnMessageAttribute,
                                "isArray": True,
                            },
                        ],
                    },
                ],
            }
        )
        return attrs

    def rootInput(self):
        """Returns the root Input node which is determined by the isRoot flag.

        :rtype: :class:`hnodes.InputNode`
        """
        rootInputPlug = self.rootInputPlug()
        if rootInputPlug is not None:
            source = rootInputPlug.child(0).sourceNode()
            return hnodes.InputNode(source.object())

    def rootIONodes(self):
        for inputNode in self.inputs():
            if inputNode.isRoot():
                yield inputNode

    def rootInputPlug(self):
        inputPlug = self.attribute(self._primaryAttr_name)
        for element in inputPlug:
            isRoot = element.child(2).value()
            if not isRoot:
                continue
            return element

    def createInput(self, name, **kwargs):
        assert not self.hasInput(name)
        inNode = hnodes.InputNode()
        inNode.create(name=name, **kwargs)
        inNode.setParent(self.rootTransform(), True)
        self.addInputNode(inNode, asRoot=kwargs.get("root", False))
        return inNode

    def addInputNode(self, inputNode, asRoot=False):
        inputPlug = self.attribute(self._primaryAttr_name)
        nextElement = inputPlug.nextAvailableDestElementPlug()
        inputNode.message.connect(nextElement.child(0))
        nextElement.child(1).setString(inputNode.id())
        nextElement.child(2).setBool(asRoot)

    def deleteInput(self, inputId):
        inputPlug = self.inputPlugById(inputId)
        if not inputPlug:
            return
        node = inputPlug.child(0).sourceNode()
        if node is not None:
            node.delete()

        inputPlug.delete()

    def clearInputs(self):
        """Clears all output nodes from the layer and clears the outputs array plug.

        :return: Returns the undo dg modifier.
        :rtype: :class:`zapi.dgModifier`
        """
        inputArray = self.attribute(self._primaryAttr_name)
        mod = zapi.dgModifier()
        rootTransform = self.rootTransform()
        for element in inputArray:
            source = element.child(0).sourceNode()
            # only delete the root parents under the layer root
            if source is not None and source.parent() == rootTransform:
                source.delete(mod=mod, apply=False)
        mod.doIt()
        inputArray.deleteElements(mod, apply=True)

    def inputPlugById(self, inputId):
        """Returns the input plug by its node ID. If not input exists none will be returned.

        :param inputId: The input node id to find.
        :type inputId: str
        :return:
        :rtype: :class:`zapi.Plug` or None
        """
        inputPlug = self.attribute(self._primaryAttr_name)
        for element in inputPlug:
            if element.child(1).asString() == inputId:
                return element

    def inputSourcePlugById(self, inputId):
        inputElement = self.inputPlugById(inputId)
        if not inputElement:
            return
        return inputElement.child(3)

    def inputNode(self, name):
        element = self.inputPlugById(name)
        if element is None:
            return
        source = element.child(0).source()
        if not source:
            raise errors.InvalidInputNodeMetaData(
                "-".join([name, element.child(1).asString()])
            )
        return hnodes.InputNode(source.node().object())

    def findInputNodes(self, *ids):
        """Finds and returns the input nodes from the layer which match the provide ids.

        :param ids: A list of input node ids to find.
        :type ids: iterable(str)
        :return: Returns a list of InputNodes which match the ids list
        :rtype: list(:class:`hnodes.InputNode`)
        """
        inputPlug = self.attribute(self._primaryAttr_name)
        validNodes = [None] * len(ids)
        for element in inputPlug:
            inputId = element.child(1).asString()
            if inputId not in ids:
                continue
            source = element.child(0).source()
            if source:
                validNodes[ids.index(inputId)] = hnodes.InputNode(
                    source.node().object()
                )

        return validNodes

    def hasInput(self, name):
        try:
            return self.inputNode(name) is not None
        except errors.InvalidInputNodeMetaData:
            return False

    def inputs(self):
        inputPlug = self.attribute(self._primaryAttr_name)
        for element in inputPlug:
            source = element.child(0).source()
            if source is not None:
                yield hnodes.InputNode(source.node().object())

    def serializeFromScene(self):
        rootTransform = self.rootTransform()
        return {
            constants.INPUTLAYER_DEF_KEY: {
                constants.SETTINGS_DEF_KEY: (
                    [
                        plugs.serializePlug(plug)
                        for plug in rootTransform.iterExtraAttributes()
                    ]
                    if rootTransform
                    else []
                ),
                constants.DAG_DEF_KEY: [
                    i.serializeFromScene(includeNamespace=False, useShortNames=True)
                    for i in self.rootIONodes()
                ],
            }
        }


class HiveOutputLayer(HiveLayer):
    id = "HiveOutputLayer"
    _primaryAttr_name = "hOutputs"

    def metaAttributes(self):
        attrs = super(HiveOutputLayer, self).metaAttributes()
        attrs.append(
            {
                "name": HiveOutputLayer._primaryAttr_name,
                "isArray": True,
                "children": [
                    {
                        "name": "outputNode",
                        "Type": zapi.attrtypes.kMFnMessageAttribute,
                        "isArray": False,
                    },
                    {
                        "name": "outputId",
                        "Type": zapi.attrtypes.kMFnDataString,
                        "isArray": False,
                    },
                ],
            }
        )
        return attrs

    def rootIONodes(self):
        for outputNode in self.outputs():
            if outputNode.isRoot():
                yield outputNode

    def addOutputNode(self, outputNode):
        inputPlug = self.attribute(self._primaryAttr_name)
        nextElement = inputPlug.nextAvailableDestElementPlug()
        outputNode.message.connect(nextElement.child(0))
        nextElement.child(1).setString(outputNode.id())

    def outputPlugById(self, outputId):
        """Returns the output plug by its ID. If not input exists none will be returned

        :param outputId: The Output node id to find
        :type outputId: str
        :return:
        :rtype: :class:`zapi.Plug` or None
        """
        outputPlug = self.attribute(self._primaryAttr_name)

        for element in outputPlug:
            if element.child(1).asString() == outputId:
                return element

    def outputNodePlugById(self, outputId):
        outputPlugElement = self.outputPlugById(outputId)
        if not outputPlugElement:
            return
        return outputPlugElement.child(0)

    def findOutputNodes(self, *ids):
        outputPlug = self.attribute(self._primaryAttr_name)
        validNodes = [None] * len(ids)
        for element in outputPlug:
            outputId = element.child(1).asString()
            if outputId not in ids:
                continue
            source = element.child(0).source()
            if source:
                validNodes[ids.index(outputId)] = hnodes.OutputNode(
                    source.node().object()
                )

        return validNodes

    def outputs(self):
        outputPlug = self.attribute(self._primaryAttr_name)
        for element in outputPlug:
            source = element.child(0).source()
            if source:
                yield hnodes.OutputNode(source.node().object())

    def hasOutput(self, name):
        try:
            return self.outputNode(name) is not None
        except errors.InvalidOutputNodeMetaData:
            return False

    def outputNode(self, name):
        matchedOutputElement = self.outputPlugById(name)
        if not matchedOutputElement:
            return None
        source = matchedOutputElement.child(0).source()
        if source is not None:
            return hnodes.OutputNode(source.node().object())
        raise errors.InvalidOutputNodeMetaData(
            "-".join([name, matchedOutputElement.child(1).asString()])
        )

    def createOutput(self, name, **kwargs):
        assert not self.hasOutput(name)
        outNode = hnodes.OutputNode()
        outNode.create(name=name, **kwargs)
        outNode.setParent(self.rootTransform())
        self.addOutputNode(outNode)
        return outNode

    def deleteOutput(self, outputId):
        outputPlug = self.outputPlugById(outputId)
        if not outputPlug:
            return
        node = outputPlug.child(0).sourceNode()
        if node is not None:
            node.delete()

        outputPlug.delete()

    def clearOutputs(self):
        """Clears all output nodes from the layer and clears the outputs array plug.

        :return: Returns the undo dg modifier
        :rtype: :class:`zapi.dgModifier`
        """
        outputArray = self.attribute(self._primaryAttr_name)
        mod = zapi.dgModifier()
        rootTransform = self.rootTransform()
        for element in outputArray:
            source = element.child(0).sourceNode()
            # only delete the root parents under the layer root
            if source is not None and source.parent() == rootTransform:
                source.delete(mod=mod, apply=False)
        mod.doIt()
        outputArray.deleteElements(mod, apply=True)
        return mod

    def serializeFromScene(self):
        rootTransform = self.rootTransform()
        return {
            constants.OUTPUTLAYER_DEF_KEY: {
                constants.SETTINGS_DEF_KEY: (
                    [
                        plugs.serializePlug(plug)
                        for plug in rootTransform.iterExtraAttributes()
                    ]
                    if rootTransform
                    else []
                ),
                constants.DAG_DEF_KEY: [
                    i.serializeFromScene() for i in self.rootIONodes()
                ],
            }
        }


class HiveXGroupLayer(HiveLayer):
    id = "HiveXGroupLayer"

    def serializeFromScene(self):
        return {}


class HiveDeformLayer(HiveLayer):
    id = "HiveDeformLayer"

    def metaAttributes(self):
        baseAttrs = super(HiveDeformLayer, self).metaAttributes()
        baseAttrs.extend(
            (
                {
                    "name": "hiveLiveLinkNodes",
                    "Type": zapi.attrtypes.kMFnMessageAttribute,
                    "isArray": True,
                },
                {
                    "name": "hiveIsLiveLinkActive",
                    "Type": zapi.attrtypes.kMFnNumericBoolean,
                },
                {
                    "name": "hiveJointSelectionSet",
                    "Type": zapi.attrtypes.kMFnMessageAttribute,
                },
            )
        )
        return baseAttrs

    def isLiveLink(self):
        """Determines if the current layer is set to be linked to the live guiding system

        :rtype: bool
        """
        return self.attribute("hiveIsLiveLinkActive").asBool()

    def createSelectionSet(self, name, parent):
        """Creates and parent a new objectSet and attaches it to this layer via
        "hiveJointSelectionSet" attribute.

        :param name: The name for the new objectSet
        :type name: str
        :param parent: The parent objectSet.
        :type parent: :class:`zapi.ObjectSet`
        :return: The new selection set
        :rtype: :class:`zapi.ObjectSet`
        """
        existingSet = self.sourceNodeByName("hiveJointSelectionSet")
        if existingSet is not None:
            return existingSet
        objectSet = zapi.createDG(name, "objectSet")
        if parent is not None:
            parent.addMember(objectSet)
        self.connectTo("hiveJointSelectionSet", objectSet)
        return objectSet

    def selectionSet(self):
        """Returns the selection set attached to this layer via  "hiveJointSelectionSet" attr.

        :return: The selection set for the layer if Any
        :rtype: :class:`zapi.ObjectSet` or None
        """
        return self.sourceNodeByName("hiveJointSelectionSet")

    def delete(self, mod=None, apply=True, deleteJoints=True):
        if not deleteJoints:
            return super(HiveDeformLayer, self).delete(mod, apply=apply)
        joints = self.joints()
        success = super(HiveDeformLayer, self).delete(mod, apply=apply)
        for j in joints:
            j.delete(mod, apply=apply)
        return success

    def setLiveLink(self, offsetNode, idMapping=None, state=True, modifier=None):
        """Live links the joints on the current deformLayer to the bound skin clusters.

        This is done by directly connected the worldInverseMatrix plug to the skin clusters
        bindPreMatrix. By Doing this we allow the joints transforms to move without effect
        the skin.
        :param offsetNode: The input guide offset node which contains the local matrices
        :type offsetNode: :class:`hnodes.SettingsNode`
        :param state: if True then the joints will be connected to the bindPreMatrix and \
        the offsetNode matrices will be connected to the local transform of the joint.
        :type state: bool
        :return: The maya dgModifier which handles undo
        :rtype: :class:`zapi.dgModifier`
        """
        currentState = self.isLiveLink()
        if state == currentState:
            return
        modifier = modifier or zapi.dgModifier()
        liveGuideNodesAttr = self.attribute("hiveLiveLinkNodes")
        # purge any joints which were removed from the definition. this can happen in dynamically generated
        # components
        for plug in liveGuideNodesAttr:
            source = plug.sourceNode()
            if source is not None:
                source.outputTranslate.disconnectAll()
                source.outputRotate.disconnectAll()
                source.delete()
        if state:
            self.activateLiveLink(offsetNode, modifier, idMapping or {}, apply=False)
        else:
            self.deactivateLiveLink(modifier, apply=False)
        self.attribute("hiveIsLiveLinkActive").set(state, mod=modifier, apply=False)
        modifier.doIt()
        return modifier

    def activateLiveLink(self, offsetNode, modifier, idMapping, apply=False):
        liveGuideNodesAttr = self.attribute("hiveLiveLinkNodes")
        offsetNodeTransformAttr = offsetNode.attribute("transforms")
        transformElements = {i.child(0).asString(): i for i in offsetNodeTransformAttr}
        joints = {jnt.id(): jnt for jnt in self.iterJoints()}
        # idMapping is the jntId: guideId defined by the component allowing us to correctly retrieve
        # the link.
        for guideId, jntId in idMapping.items():
            sceneJoint = joints.get(jntId)
            if not sceneJoint:
                continue
            guideOffsetElement = transformElements.get(guideId)

            worldMatrixPlug = sceneJoint.attribute("worldMatrix")[0]
            for worldMatDest in worldMatrixPlug.destinations():
                n = worldMatDest.node()
                if not n.hasFn(zapi.kNodeTypes.kSkinClusterFilter):
                    continue

                influenceIndex = worldMatDest.logicalIndex()
                preBindMat = n.attribute("bindPreMatrix").element(influenceIndex)
                sceneJoint.attribute("worldInverseMatrix")[0].connect(
                    preBindMat, mod=modifier, apply=False
                )

            matrix = guideOffsetElement.child(1)  # localMatrix
            parentNode = sceneJoint.parent()
            parentNodeIsJnt = parentNode.hasFn(zapi.kNodeTypes.kJoint)
            if parentNode is not None and parentNodeIsJnt:
                matrixCache = guideOffsetElement.child(2)  # worldMatrix
                multMatrix = zapi.createMultMatrix(
                    "{}_liveGuide_matrixLocal".format(worldMatrixPlug.name()),
                    [matrixCache, parentNode.worldInverseMatrix[0]],
                    output=None,
                )
                matrix = multMatrix.matrixSum
            elif parentNode is None or not parentNodeIsJnt:
                matrix = guideOffsetElement.child(2)  # worldMatrix
            decomp = zapi.createDecompose(
                "{}_liveGuide_matrix".format(worldMatrixPlug.name()),
                None,
                inputMatrixPlug=matrix,
            )

            decomp.outputTranslate.connect(sceneJoint.translate)
            decomp.outputRotate.connect(sceneJoint.jointOrient)
            decomp.message.connect(liveGuideNodesAttr.nextAvailableDestElementPlug())

        self.attribute("hiveIsLiveLinkActive").set(True, mod=modifier, apply=False)
        if apply:
            modifier.doIt()

        return modifier

    def deactivateLiveLink(self, modifier, apply=True):
        for jnt in self.iterJoints():
            for worldMatDest in jnt.attribute("worldMatrix")[0].destinations():
                n = worldMatDest.node()
                if not n.hasFn(zapi.kNodeTypes.kSkinClusterFilter):
                    continue
                influenceIndex = worldMatDest.logicalIndex()
                preBindMat = n.attribute("bindPreMatrix").element(influenceIndex)
                preBindMatrixValue = preBindMat.value()
                jnt.attribute("worldInverseMatrix")[0].disconnect(
                    preBindMat, modifier=modifier, apply=False
                )
                preBindMat.set(preBindMatrixValue, mod=modifier)
        self.attribute("hiveIsLiveLinkActive").set(False, mod=modifier, apply=False)
        if apply:
            modifier.doIt()
        return modifier

    def serializeFromScene(self):
        # supportedTypes = (om2.MFn.kJoint,)
        # rootTransform = self.rootTransform()
        # children = []
        # for child in rootTransform.iterChildren(rootTransform, recursive=True, nodeTypes=supportedTypes):
        #     children.append(hnodes.Joint(child.object()).serializeFromScene(includeConnections=False,
        #                                                                     skipAttributes=constants.ATTRIBUTES_SERIALIZE_SKIP))
        # return {"deformLayer": children}
        return {}


class HiveGeometryLayer(HiveLayer):
    id = "HiveGeometryLayer"

    def metaAttributes(self):
        attrs = super(HiveGeometryLayer, self).metaAttributes()

        attrs.append(
            {
                "name": "geometry",
                "children": (
                    {
                        "name": "geo",
                        "Type": zapi.attrtypes.kMFnMessageAttribute,
                        "isArray": False,
                    },
                    {
                        "name": "cache",
                        "Type": zapi.attrtypes.kMFnNumericBoolean,
                        "isArray": False,
                    },
                ),
                "isArray": True,
            }
        )
        return attrs

    def addGeometry(self, geo):
        element = self.attribute("geometry").nextAvailableElementPlug()
        geo.message.connect(element)
        return True

    def serializeFromScene(self):
        return {constants.GEOMETRY_LAYER_TYPE: {}}

    def geometryPlugs(self):
        return self.attribute("geometry")

    def geometry(self):
        return self.geometry()
