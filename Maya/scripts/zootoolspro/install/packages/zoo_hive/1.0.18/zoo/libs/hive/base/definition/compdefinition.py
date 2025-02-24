import copy
import json
import pprint
from collections import OrderedDict
from zoo.libs.hive import constants

from zoo.libs.utils import profiling
from zoo.libs.hive.base.definition import definitionlayers
from zoo.libs.hive.base.definition import spaceswitch
from zoo.core.util import zlogging

__all__ = ["ComponentDefinition", "migrateToLatestVersion", "loadDefinition"]

logger = zlogging.getLogger(__name__)

# Definition keys to skip general update since we handle these explicitly
UPDATE_SKIP_KEYS = (
    constants.GUIDELAYER_DEF_KEY,
    constants.RIGLAYER_DEF_KEY,
    constants.INPUTLAYER_DEF_KEY,
    constants.OUTPUTLAYER_DEF_KEY,
    constants.DEFORMLAYER_DEF_KEY,
    constants.SPACE_SWITCH_DEF_KEY,
)
# definition keys which need to be serialized to the template
TEMPLATE_KEYS = (
    constants.NAME_DEF_KEY,
    constants.SIDE_DEF_KEY,
    constants.GUIDELAYER_DEF_KEY,
    constants.CONNECTIONS_DEF_KEY,
    constants.PARENT_DEF_KEY,
    constants.DEFINITION_VERSION_DEF_KEY,
    constants.TYPE_DEF_KEY,
    constants.GUIDE_MM_LAYOUT_DEF_KEY,
    constants.DEFORM_MM_LAYOUT_DEF_KEY,
    constants.RIG_MM_LAYOUT_DEF_KEY,
    constants.ANIM_MM_LAYOUT_DEF_KEY,
    constants.SPACE_SWITCH_DEF_KEY,
    constants.NAMING_PRESET_DEF_KEY,
)
# definition layer to scene attr mapping names. Used when we serialize
SCENE_LAYER_ATTR_TO_DEF = {
    constants.GUIDELAYER_DEF_KEY: [
        constants.DEF_CACHE_GUIDE_DAG_ATTR,
        constants.DEF_CACHE_GUIDE_SETTINGS_ATTR,
        constants.DEF_CACHE_GUIDE_METADATA_ATTR,
        constants.DEF_CACHE_GUIDE_DG_ATTR,
    ],
    constants.DEFORMLAYER_DEF_KEY: [
        constants.DEF_CACHE_DEFORM_DAG_ATTR,
        constants.DEF_CACHE_DEFORM_SETTINGS_ATTR,
        constants.DEF_CACHE_DEFORM_METADATA_ATTR,
        "",
    ],
    constants.INPUTLAYER_DEF_KEY: [
        constants.DEF_CACHE_INPUT_DAG_ATTR,
        constants.DEF_CACHE_INPUT_SETTINGS_ATTR,
        constants.DEF_CACHE_INPUT_METADATA_ATTR,
        "",
    ],
    constants.OUTPUTLAYER_DEF_KEY: [
        constants.DEF_CACHE_OUTPUT_DAG_ATTR,
        constants.DEF_CACHE_OUTPUT_SETTINGS_ATTR,
        constants.DEF_CACHE_OUTPUT_METADATA_ATTR,
        "",
    ],
    constants.RIGLAYER_DEF_KEY: [
        constants.DEF_CACHE_RIG_DAG_ATTR,
        constants.DEF_CACHE_RIG_SETTINGS_ATTR,
        constants.DEF_CACHE_RIG_METADATA_ATTR,
        constants.DEF_CACHE_GUIDE_DG_ATTR,
    ],
}


class ComponentDefinition(object):
    """This class describes the component, this is used by the component setup methods and is the fallback data
    for when the component has yet to be created in maya, the guides instance variable is a list of Guide objects which
    deal with the creation and serialization of each guide. when accessing the internal data of a guide. you should
    always refer to the internal "id" key as this will never change but users can rename so use "name" to get the
    user modified name.

    :param data:
    :type data: dict
    :param originalDefinition:
    :type originalDefinition: :class:`ComponentDefinition`
    :param path:
    :type path: str or None
    """

    # definition version which all components are using. definitions get migrated upon load.
    definitionVersion = "2.0"

    def __init__(self, data=None, originalDefinition=None, path=None):
        data = data or {}
        # The raw data provided to the class.
        self.data = data
        # Absolute file path to this definition.
        self.path = path or ""
        # The name of the definition.
        self.name = data.get("name", "")
        # The side name of the definition.
        self.side = data.get("side", "")
        # The component type which this definition is attached too.
        self.type = data.get("type", "")
        self.version = ""
        # The parent component for this attached component in the form of {componentName:side}.
        self.parent = data.get(constants.PARENT_DEF_KEY, [])
        # The connections types to the parent component.
        self.connections = data.get(constants.CONNECTIONS_DEF_KEY, {})
        # The guide system marking menu for the component.
        self.mm_guide_Layout = data.get("mm_guide_Layout", "")
        # The deformation system marking menu for the component.
        self.mm_deform_Layout = data.get("mm_deform_Layout", "")
        # The rig system marking menu for the component.
        self.mm_rig_Layout = data.get("mm_rig_Layout", "")
        # The animation rig system marking menu for the component.
        self.mm_anim_Layout = data.get("mm_anim_Layout", "")
        # the naming preset name the component is using.
        self.namingPreset = data.get("namingPreset", "")
        self.guideLayer = definitionlayers.GuideLayerDefinition.fromData(
            data.get(constants.GUIDELAYER_DEF_KEY, {})
        )
        self.rigLayer = definitionlayers.RigLayerDefinition.fromData(
            data.get(constants.RIGLAYER_DEF_KEY, {})
        )
        self.outputLayer = definitionlayers.OutputLayerDefinition.fromData(
            data.get(constants.OUTPUTLAYER_DEF_KEY, {})
        )
        self.inputLayer = definitionlayers.InputLayerDefinition.fromData(
            data.get(constants.INPUTLAYER_DEF_KEY, {})
        )
        self.deformLayer = definitionlayers.DeformLayerDefinition.fromData(
            data.get(constants.DEFORMLAYER_DEF_KEY, {})
        )
        self.spaceSwitching = [
            spaceswitch.SpaceSwitchDefinition(i)
            for i in data.get(constants.SPACE_SWITCH_DEF_KEY, [])
        ]
        self.uuid = data.get("uuid", "")
        if originalDefinition is not None:
            # the base definition in its unmodified state. Used for comparing changes.
            self.originalDefinition = ComponentDefinition(originalDefinition)
        else:
            # the base definition in its unmodified state. Used for comparing changes.
            self.originalDefinition = {}

    def serialize(self):
        data = {
            constants.NAME_DEF_KEY: self.name,
            constants.SIDE_DEF_KEY: self.side,
            constants.TYPE_DEF_KEY: self.type,
            constants.PARENT_DEF_KEY: self.parent,
            constants.DEFINITION_VERSION_DEF_KEY: self.definitionVersion,
            constants.CONNECTIONS_DEF_KEY: self.connections,
            constants.GUIDE_MM_LAYOUT_DEF_KEY: self.mm_guide_Layout,
            constants.RIG_MM_LAYOUT_DEF_KEY: self.mm_rig_Layout,
            constants.DEFORM_MM_LAYOUT_DEF_KEY: self.mm_deform_Layout,
            constants.ANIM_MM_LAYOUT_DEF_KEY: self.mm_anim_Layout,
            constants.NAMING_PRESET_DEF_KEY: self.namingPreset,
            constants.GUIDELAYER_DEF_KEY: copy.deepcopy(self.guideLayer),
            constants.DEFORMLAYER_DEF_KEY: copy.deepcopy(self.deformLayer),
            constants.INPUTLAYER_DEF_KEY: copy.deepcopy(self.inputLayer),
            constants.OUTPUTLAYER_DEF_KEY: copy.deepcopy(self.outputLayer),
            constants.RIGLAYER_DEF_KEY: copy.deepcopy(self.rigLayer),
        }

        spaces = []

        for i in self.spaceSwitching:
            existingSpace = self.originalDefinition.spaceSwitchByLabel(i["label"])
            if not existingSpace:
                spaces.append(i)
            else:
                difference = i.difference(existingSpace)
                if difference:
                    spaces.append(difference)
        data[constants.SPACE_SWITCH_DEF_KEY] = spaces
        return data

    def pprint(self):
        """Pretty prints the current definition"""
        pprint.pprint(dict(self.serialize()))

    def __repr__(self):
        return "<{}> {}".format(self.__class__.__name__, self.name)

    def toJson(self, template=False):
        """Returns the string version of the definition.

        :return: json converted string of the current definition
        :rtype: str
        """
        if template:
            return json.dumps(self.toTemplate())
        return json.dumps(self.serialize())

    def toSceneData(self):
        serializedData = self.serialize()
        outputData = {}
        for layerKey, [
            dagLayerAttrName,
            settingsAttrName,
            metaDataAttrName,
            dgAttrName,
        ] in SCENE_LAYER_ATTR_TO_DEF.items():
            layer = serializedData.get(layerKey, {})
            outputData[dagLayerAttrName] = json.dumps(
                layer.get(constants.DAG_DEF_KEY, [])
            )
            outputData[settingsAttrName] = json.dumps(
                layer.get(
                    constants.SETTINGS_DEF_KEY,
                    [] if layerKey != constants.RIGLAYER_DEF_KEY else {},
                )
            )
            outputData[metaDataAttrName] = json.dumps(
                layer.get(constants.METADATA_DEF_KEY, [])
            )
            if dgAttrName:
                outputData[dgAttrName] = json.dumps(
                    layer.get(constants.DG_GRAPH_DEF_KEY, [])
                )

        spaceSwitchingData = serializedData.get(constants.SPACE_SWITCH_DEF_KEY, {})
        outputData[constants.DEF_CACHE_SPACE_SWITCHING_ATTR] = json.dumps(
            spaceSwitchingData
        )
        infoData = {}
        for k in (
            constants.NAME_DEF_KEY,
            constants.SIDE_DEF_KEY,
            constants.CONNECTIONS_DEF_KEY,
            constants.PARENT_DEF_KEY,
            constants.DEFINITION_VERSION_DEF_KEY,
            constants.TYPE_DEF_KEY,
            constants.GUIDE_MM_LAYOUT_DEF_KEY,
            constants.DEFORM_MM_LAYOUT_DEF_KEY,
            constants.RIG_MM_LAYOUT_DEF_KEY,
            constants.ANIM_MM_LAYOUT_DEF_KEY,
            constants.NAMING_PRESET_DEF_KEY,
        ):
            infoData[k] = serializedData.get(k, "")
        outputData[constants.DEF_CACHE_INFO_ATTR] = json.dumps(infoData)
        return outputData

    def toTemplate(self):
        """Returns a dict only containing the necessary information for template storage which should only
        be the guide information, all rig related keys are skipped since this isn't required and if
        included would reduce too much data complexity into updates.

        :returns: a dict contains the keys ("name", "side", "guideLayer", \
        constants.CONNECTIONS_DEF_KEY, constants.PARENT_DEF_KEY, "type")
        :rtype: dict

        """
        data = self.serialize()
        raw = copy.deepcopy({n: info for n, info in data.items() if n in TEMPLATE_KEYS})
        ignoreMetaAttrs = ("guideVisibility", "guideControlVisibility")
        metaData = []
        for metaAttr in raw[constants.GUIDELAYER_DEF_KEY].get(
            constants.SETTINGS_DEF_KEY
        ):
            if metaAttr not in ignoreMetaAttrs:
                metaData.append(metaAttr)
        raw[constants.GUIDELAYER_DEF_KEY][constants.METADATA_DEF_KEY] = metaData
        return raw

    def updateFromDict(self, kwargs):
        self.name = kwargs.get("name", self.name)
        self.side = kwargs.get("side", self.side)
        self.parent = kwargs.get("parent", self.parent)
        self.connections = kwargs.get("connections", self.connections)
        self.namingPreset = kwargs.get("namingPreset", self.namingPreset)
        self.mm_rig_Layout = kwargs.get("mm_rig_Layout", self.mm_rig_Layout)
        self.mm_anim_Layout = kwargs.get("mm_anim_Layout", self.mm_anim_Layout)
        self.mm_guide_Layout = kwargs.get("mm_guide_Layout", self.mm_guide_Layout)
        self.mm_deform_Layout = kwargs.get("mm_deform_Layout", self.mm_deform_Layout)
        self.guideLayer.update(kwargs.get(constants.GUIDELAYER_DEF_KEY, {}))
        self.rigLayer.update(kwargs.get(constants.RIGLAYER_DEF_KEY, {}))
        self.inputLayer.update(kwargs.get(constants.INPUTLAYER_DEF_KEY, {}))
        self.outputLayer.update(kwargs.get(constants.OUTPUTLAYER_DEF_KEY, {}))
        self.deformLayer.update(kwargs.get(constants.DEFORMLAYER_DEF_KEY, {}))
        self.updateSpaceSwitching(kwargs.get(constants.SPACE_SWITCH_DEF_KEY, []))

    def updateFromDefinition(self, kwargs):
        self.name = kwargs.name or self.name
        self.side = kwargs.side or self.side
        self.parent = kwargs.parent or self.parent
        self.connections = kwargs.connections or self.connections
        self.namingPreset = kwargs.namingPreset or self.namingPreset
        self.mm_rig_Layout = kwargs.mm_rig_Layout or self.mm_rig_Layout
        self.mm_anim_Layout = kwargs.mm_anim_Layout or self.mm_anim_Layout
        self.mm_guide_Layout = kwargs.mm_guide_Layout or self.mm_guide_Layout
        self.mm_deform_Layout = kwargs.mm_deform_Layout or self.mm_deform_Layout
        if kwargs.guideLayer:
            self.guideLayer.update(kwargs.guideLayer)
        if kwargs.rigLayer:
            self.rigLayer.update(kwargs.rigLayer)
        if kwargs.inputLayer:
            self.inputLayer.update(kwargs.inputLayer)
        if kwargs.outputLayer:
            self.outputLayer.update(kwargs.outputLayer)
        if kwargs.deformLayer:
            self.deformLayer.update(kwargs.deformLayer)
        if kwargs.spaceSwitching:
            self.updateSpaceSwitching(kwargs.spaceSwitching)

    def update(self, kwargs):
        """Overridden to convert any attributes to Setting objects

        :param kwargs:
        :type kwargs: :class:`ComponentDefinition` or dict
        """
        if isinstance(kwargs, ComponentDefinition):
            self.updateFromDefinition(kwargs)
        else:
            self.updateFromDict(kwargs)

    def spaceSwitchByLabel(self, label):
        """

        :param label:
        :type label: str
        :return:
        :rtype: :class:`spaceswitch.SpaceSwitchDefinition`
        """
        for i in self.spaceSwitching:
            if i.label == label:
                return i

    def removeSpacesByLabel(self, labels):
        """

        :param labels: The space switch labels to remove
        :type labels: list[str]
        """
        removed = []
        for label in labels:
            space = self.spaceSwitchByLabel(label)
            if space is not None:
                removed.append(label)
                self.spaceSwitching.remove(space)
        if removed:
            logger.debug("Removed SpaceSwitches: {}".format(removed))

    def removeSpaceSwitch(self, label):
        for i, space in enumerate(self.spaceSwitching):
            if space.label == label:
                logger.debug("Removing SpaceSwitch: {}".format(label))
                del self.spaceSwitching[i]
                return True
        return False

    def createSpaceSwitch(
        self, label, drivenId, constraintType, controlPanelFilter, permissions, drivers
    ):
        existingSpace = self.spaceSwitchByLabel(label)
        if existingSpace:
            existingSpace.controlPanelFilter = controlPanelFilter
            existingSpace.permissions = permissions
            existingSpace["drivers"] = [
                spaceswitch.SpaceSwitchDriverDefinition(i) for i in drivers
            ]
            return existingSpace
        logger.debug("Creating Space Switching Definition: {}".format(label))
        space = {
            "label": label,
            "controlPanelFilter": controlPanelFilter,
            "driven": drivenId,
            "type": constraintType,
            "permissions": permissions,
            "drivers": drivers,
        }
        spaceDef = spaceswitch.SpaceSwitchDefinition(space)
        self.spaceSwitching.append(spaceDef)
        return spaceDef

    def updateSpaceSwitching(self, spaces):
        """merges incoming space switches with the current.

        #. Merges any missing spaces.


        """
        if not spaces:
            return
        existingSpaces = OrderedDict((k["label"], k) for k in self.spaceSwitching)
        for space in spaces:
            label = space["label"]
            panelFilter = space.get("controlPanelFilter", {})
            default = panelFilter.get("default", "")
            drivers = space.get("drivers", [])
            existingSpace = existingSpaces.get(label)
            if not existingSpace:
                existingSpaces[label] = space
                continue

            existingDrivers = {i.label: i for i in existingSpace.drivers}
            # merged based on the incoming drivers not the existing.
            mergedDrivers = []
            for driver in drivers:
                existingDriver = existingDrivers.get(driver["label"])
                if existingDriver:
                    mergedDrivers.append(existingDriver)
                else:
                    mergedDrivers.append(
                        spaceswitch.SpaceSwitchDriverDefinition(**driver)
                    )
            existingSpace.drivers = mergedDrivers
            existingSpace.defaultDriver = default

        self.spaceSwitching = [
            spaceswitch.SpaceSwitchDefinition(i) for i in existingSpaces.values()
        ]


def loadDefinition(definitionData, originalDefinition, path=None):
    """

    :param definitionData:
    :type definitionData: dict
    :param path:
    :type path: str
    :return:
    :rtype: :class:`ComponentDefinition`
    """
    if isinstance(definitionData, dict):
        # in this case we need to upgrade the definition for the old to the new
        # for now something hardcode to go between 1.0 and 2.0
        latestData = migrateToLatestVersion(definitionData)
        return ComponentDefinition(
            data=latestData,
            originalDefinition=copy.deepcopy(originalDefinition),
            path=path,
        )

    latestData = migrateToLatestVersion(definitionData)
    ComponentDefinition(
        data=latestData.serialize(),
        originalDefinition=copy.deepcopy(originalDefinition),
        path=path,
    )
    return latestData


def migrateToLatestVersion(definitionData, originalComponent=None):
    """Function which migrates definition schema from an old version to latest.

    :param definitionData: The definition data as a raw dict
    :type definitionData: dict
    :param originalComponent: The unmodified component definition, usually this is the \
    base definition for the component.
    :type originalComponent: :class:`ComponentDefinition`
    :return: Translated definition data to the latest schema
    :rtype: :class:`ComponentDefinition`
    """
    if originalComponent:
        # We expect that the rigLayer comes from the base definition not the scene so maintain the
        # original.
        if isinstance(definitionData, dict):
            definitionData["rigLayer"] = copy.deepcopy(originalComponent.rigLayer)
        else:
            definitionData.rigLayer = copy.deepcopy(originalComponent.rigLayer)
    return definitionData
    # raise NotImplementedError("UnSupported definition version: {}".format(requestedVersion))
