__all__ = [
    "GuideLayerDefinition",
    "RigLayerDefinition",
    "InputLayerDefinition",
    "OutputLayerDefinition",
    "DeformLayerDefinition",
    "NamedGraphs",
    "NamedGraph",
]

from collections import OrderedDict

from zoo.libs.utils import general
from zoo.libs.hive import constants
from zoo.libs.maya import zapi

from zoo.libs.hive.base.definition import definitionnodes
from zoo.libs.hive.base.definition import definitionattrs
from zoo.libs.hive.base.definition import defutils


class LayerDef(general.ObjectDict):
    """Base Layer definition.

    Hive Layers are containers of organised data for a single scene structure ie. Guides, Rig, deform.

    :note: This class shouldn't be instantiate directly, use one of the subclasses
    """

    @classmethod
    def fromData(cls, layerData):
        return cls()

    def node(self, nodeId):
        """Finds and returns the node by its id.

        :param nodeId: The node id to find
        :type nodeId: str
        :return: The node definition instance i.e. guide,transform srt, joint.
        :rtype: :class:`definitionnodes.TransformDefinition` or None
        """
        for n in defutils.traverseDefinitionLayerDag(self):
            if n["id"] == nodeId:
                return n

    def findNodes(self, *nodeIds):
        """Finds and returns all nodes which match one of the provided nodeIds.

        .. note:: If a node id isn't found then None will be returned for that list index.

        :param nodeIds: List of node ids to find.
        :type nodeIds: list[str]
        :return: A list of node definition instances i.e. guide,transform srt, joint.
        :rtype: list[:class:`definitionnodes.TransformDefinition` or None]
        """
        results = [None] * len(nodeIds)
        for node in defutils.traverseDefinitionLayerDag(self):
            nodeId = node["id"]
            if nodeId in nodeIds:
                results[nodeIds.index(nodeId)] = node
        return results

    def hasNode(self, nodeId):
        """Returns True if the node by the id exists.

        :param nodeId: The node id to check
        :type nodeId:  str
        :rtype: bool
        """
        return self.node(nodeId) is not None

    def nodes(self, includeRoot=True):
        """Generator function with iterates recursively across all nodes.

        :param includeRoot: Whether to return the node with the root id
        :type includeRoot: bool
        :return: Returns each node instance.
        :rtype: list[:class:`definitionnodes.TransformDefinition`]
        """
        for n in defutils.traverseDefinitionLayerDag(self):
            if not includeRoot and n["id"] == "root":
                continue
            yield n

    def serialize(self):
        raise NotImplementedError(
            "Serialize method is required override for subclasses."
        )


class GuideLayerDefinition(LayerDef):
    @classmethod
    def fromData(cls, layerData):
        """Transforms the provided data in to a set of guide and attribute classes. Each class created
        inherits from dict

        :param layerData: The guide layer data
        :type layerData:  dict
        :return: Returns a new GuideLayer definition
        :rtype: :class:`GuideLayerDefinition`
        """
        newSettings = cls.mergeDefaultSettings(
            layerData.get(constants.SETTINGS_DEF_KEY, [])
        )
        newMetaData = cls.mergeDefaultMetaData(
            layerData.get(constants.METADATA_DEF_KEY, [])
        )

        data = {
            constants.DAG_DEF_KEY: [],
            constants.SETTINGS_DEF_KEY: newSettings,
            constants.METADATA_DEF_KEY: newMetaData,
            constants.DG_GRAPH_DEF_KEY: [],
        }
        instance = cls(data)
        instance.update(
            {
                constants.DG_GRAPH_DEF_KEY: layerData.get(
                    constants.DG_GRAPH_DEF_KEY, []
                ),
                constants.DAG_DEF_KEY: layerData.get(constants.DAG_DEF_KEY, []),
            }
        )
        return cls(data)

    def update(self, kwargs):
        settings = self.get(constants.SETTINGS_DEF_KEY, [])

        consolidatedSettings = OrderedDict((i["name"], i) for i in settings)
        for i in kwargs.get(constants.SETTINGS_DEF_KEY, []):
            existing = consolidatedSettings.get(i["name"])
            if existing is not None and i.get("value") is not None:
                existing["value"] = i["value"]
            else:
                consolidatedSettings[i["name"]] = definitionattrs.attributeClassForDef(
                    i
                )

        self[constants.SETTINGS_DEF_KEY] = list(consolidatedSettings.values())
        currentGuides = {i["id"]: i for i in self.iterGuides()}
        newOrUpdated = []
        for ioNode in defutils.traverseDefinitionLayerDag(kwargs):
            newOrUpdated.append(ioNode["id"])
            # note: will relookup against the layer each loop so we retrieve any new guides as well.
            # we don't update 'currentGuides' because we do a diff later using this to purge any guides
            # which no longer exist
            currentNode = self.guide(ioNode["id"])
            # merge the IO node inplace
            if currentNode is not None:
                ioNode["pivotColor"] = currentNode.get("pivotColor")
                ioNode["pivotShape"] = currentNode.get("pivotShape")
                # Guide Definition class handles the update including its children
                currentNode.update(ioNode)
            # a IO node won't exist in the definition when it's been dynamically generated
            else:
                self.createGuide(**ioNode)
        toPurge = [
            i
            for i, g in currentGuides.items()
            if i not in newOrUpdated and not g.get("internal", False)
        ]
        if toPurge:
            self.deleteGuides(*toPurge)
        self[constants.METADATA_DEF_KEY] = [
            definitionattrs.attributeClassForDef(s)
            for s in kwargs.get(constants.METADATA_DEF_KEY, [])
        ] or self.get(constants.METADATA_DEF_KEY, [])
        DGGraphs = kwargs.get(constants.DG_GRAPH_DEF_KEY)
        if DGGraphs is not None:
            self[constants.DG_GRAPH_DEF_KEY] = NamedGraphs.fromData(DGGraphs)

    def __getattr__(self, item):
        """Loop for guide objects and return the first guide object that has the name

        :param item: the name of the guide
        :type item: str
        :rtype: :class:`definitionnodes.GuideDefinition`
        """
        key = self.get(item)
        if key is not None:
            return key
        guid = self.guide(item)
        if guid is not None:
            return guid

        return super(GuideLayerDefinition, self).__getattribute__(item)

    @classmethod
    def defaultGuideSettings(cls):
        """Default guide settings

        :rtype: list[:class:`baseDef.AttributeDefinition`]
        """
        data = [
            {
                "name": "manualOrient",
                "value": False,
                "isArray": False,
                "locked": False,
                "default": False,
                "channelBox": True,
                "Type": zapi.attrtypes.kMFnNumericBoolean,
                "keyable": False,
            }
        ]

        return [definitionattrs.attributeClassForDef(d) for d in data]

    @classmethod
    def mergeDefaultSettings(cls, newState):
        defaultSettings = OrderedDict(
            (i["name"], i) for i in cls.defaultGuideSettings()
        )
        for s in newState:
            existingAttr = defaultSettings.get(s["name"])
            if existingAttr is not None:
                existingAttr["value"] = s["value"]
            else:
                defaultSettings[s["name"]] = definitionattrs.attributeClassForDef(s)
        return list(defaultSettings.values())

    @classmethod
    def defaultMetadataSettings(cls):
        """Default guide settings

        :rtype: list[:class:`baseDef.AttributeDefinition`]
        """
        data = [
            dict(
                name="guideVisibility",
                Type=zapi.attrtypes.kMFnNumericBoolean,
                default=True,
                value=True,
            ),
            dict(
                name="guideControlVisibility",
                Type=zapi.attrtypes.kMFnNumericBoolean,
                default=False,
                value=False,
            ),
            dict(
                name="pinSettings",
                children=[
                    dict(name="pinned", Type=zapi.attrtypes.kMFnNumericBoolean),
                    dict(name="pinnedConstraints", Type=zapi.attrtypes.kMFnDataString),
                ],
            ),
        ]
        return [definitionattrs.attributeClassForDef(d) for d in data]

    @classmethod
    def mergeDefaultMetaData(cls, newState):
        defaultSettings = {i["name"]: i for i in cls.defaultMetadataSettings()}
        for s in newState:
            defaultSettings[s["name"]] = s
        return [
            definitionattrs.attributeClassForDef(s) for s in defaultSettings.values()
        ]

    def iterGuides(self, includeRoot=True):
        """Generator Function that iterates all guides.

        :rtype: Generator(:class:`definitionnodes.GuideDefinition`)
        """
        for guide in iter(self.get(constants.DAG_DEF_KEY, [])):
            if not includeRoot and guide.id == "root":
                for child in guide.iterChildren():
                    yield child
            else:
                yield guide
                for child in guide.iterChildren():
                    yield child

    def hasGuides(self):
        return len(self.get(constants.DAG_DEF_KEY, [])) != 0

    def guideCount(self, includeRoot=True):
        return len(list(self.iterGuides(includeRoot)))

    def guide(self, guideId):
        """Returns the :class:`definitionnodes.GuideDefinition` instance that is attached to this
        Definition instance.

        :param guideId: The guide id value
        :type guideId: str
        :rtype: :class:`definitionnodes.GuideDefinition` or None
        """
        return self.node(guideId)

    def findGuides(self, *ids):
        """Finds and returns all guides with the specified ids.

        :param ids: The guide Ids
        :type ids: iterable[str]
        :return: The guides requested in the order provided.
        :rtype: generator[:class:`definitionnodes.GuideDefinition`]
        """
        return self.findNodes(*ids)

    def hasGuideSetting(self, name):
        """Returns True if the guide Setting by its already exists.

        :param name: The Guide Setting name
        :type name: str
        :rtype: bool
        """
        for i in self.iterGuideSettings():
            if i.name == name:
                return True
        return False

    def addGuideSetting(self, setting):
        """Appends a new guide setting to this definition

        :param setting: Setting object describing the guide setting
        :type setting: :class:`definitionattrs.AttributeDefinition`
        """
        if not self.hasGuideSetting(setting.name):
            self[constants.SETTINGS_DEF_KEY].append(setting)

    def addGuideSettings(self, settings):
        """Appends new guide settings to this definition

        :param settings: A list of Setting objects describing the guide setting.
        :type settings: list[:class:`definitionattrs.AttributeDefinition`]
        """
        existingSettings = {i.name: i for i in self[constants.SETTINGS_DEF_KEY]}
        for setting in settings:
            if not existingSettings.get(setting.name):
                self[constants.SETTINGS_DEF_KEY].append(setting)

    def guideSetting(self, name):
        """Returns the guide setting with the given name.

        :param name: the guide setting to return
        :type name: str
        :return: Returns the guide setting
        :rtype: :class:`definitionattrs.AttributeDefinition` or None
        """
        for i in iter(self[constants.SETTINGS_DEF_KEY]):
            if i.name == name:
                return i

    def iterGuideSettings(self):
        return iter(self[constants.SETTINGS_DEF_KEY])

    def guideSettings(self, *names):
        """Returns all matching guide settings attributes as a dict.

        :param names: The Guide Settings attribute names to retrieve.
        :type names: iterable[str]
        :return: attributeName: attributeDefinition
        :rtype: dict[str, :class:`definitionattrs.AttributeDefinition`]
        """
        settings = general.ObjectDict()
        for i in iter(self[constants.SETTINGS_DEF_KEY]):
            name = i.name
            if name in names:
                settings[name] = i
        return settings

    def deleteGuides(self, *guideIds):
        root = self.guide("root")
        success = False
        for guide in self.iterGuides():
            guideId = guide.id
            if guideId not in guideIds:
                continue
            guideParentId = guide.parent
            parent = self.guide(guideParentId) if guideParentId is not None else root
            if not parent:
                continue
            deleted = parent.deleteChild(guideId)
            if deleted:
                success = deleted
        return success

    def deleteSettings(self, attributeNames):
        """Deletes all guide settings based on the provided attributeNames.

        :param attributeNames: The list of attribute names to delete.
        :type attributeNames: iterable[str]
        """
        valid = []
        for i in self.get(constants.SETTINGS_DEF_KEY):
            if i.name not in attributeNames:
                valid.append(i)
        self[constants.SETTINGS_DEF_KEY] = valid

    def deleteSetting(self, name):
        """Deletes a group of setting by name from the layer node.

        :param name: The Settings name to remove.
        :type name: str
        :return: Whether deletion was successful.
        :rtype: bool
        """
        try:
            nodeSettings = self[constants.SETTINGS_DEF_KEY]

            for i in nodeSettings:
                if i.name == name:
                    nodeSettings.remove(i)
                    return True
            return False
        except KeyError:
            return False

    def addGuide(self, guide):
        """Appends a new :class:`definitionnodes.GuideDefinition` to this definition

        :param guide: The guide definition to add
        :type guide: :class:`definitionnodes.GuideDefinition`

        """
        guide["hiveType"] = "guide"
        parent = guide.get("parent")
        if parent is None:
            self.setdefault(constants.DAG_DEF_KEY, []).append(guide)
            return
        parentGuide, child = None, None
        for g in self.iterGuides():
            if g["id"] == parent:
                parentGuide, child = g, guide
                break
        if parentGuide is not None:
            parentGuide["children"].append(child)

    def hasGuide(self, guideId):
        return self.hasNode(guideId)

    def createGuide(self, **info):
        existingGuide = self.guide(info["id"])
        if existingGuide is not None:
            return existingGuide
        gui = definitionnodes.GuideDefinition.deserialize(
            info, parent=info.get("parent")
        )
        self.addGuide(gui)
        return gui

    def setGuideParent(self, child, parent):
        if child.parent == parent:
            return False
        currentParent = self.guide(child.parent)
        # remove self from the current parent
        if currentParent is not None:
            del currentParent.children[currentParent.children.index(child)]
        # add self the new parent
        parent.children.append(child)
        child.parent = parent.id
        return True


class RigLayerDefinition(LayerDef):
    @classmethod
    def fromData(cls, layerData):
        """Transforms the provided data in to a set of Rig and attribute classes. Each class created
        inherits from dict

        :param layerData: The rig layer data
        :type layerData:  dict
        :return: Returns a new RigLayer definition
        :rtype: :class:`RigLayerDefinition`
        """
        data = {
            constants.DAG_DEF_KEY: [
                definitionnodes.ControlDefinition.deserialize(i)
                for i in iter(layerData.get(constants.DAG_DEF_KEY, []))
            ],
            constants.SETTINGS_DEF_KEY: {
                name: list(map(definitionattrs.attributeClassForDef, v))
                for name, v in iter(
                    layerData.get(constants.SETTINGS_DEF_KEY, {}).items()
                )
            },
            constants.DG_GRAPH_DEF_KEY: NamedGraphs.fromData(
                layerData.get(constants.DG_GRAPH_DEF_KEY, [])
            ),
        }
        return cls(data)

    def update(self, kwargs):
        self._updateSettings(kwargs)
        rigLayerInfo = kwargs.get(constants.DAG_DEF_KEY)
        if rigLayerInfo is not None:
            self[constants.DAG_DEF_KEY] = list(
                map(definitionnodes.ControlDefinition.deserialize, iter(rigLayerInfo))
            )
        DGGraphs = kwargs.get(constants.DG_GRAPH_DEF_KEY)
        if DGGraphs is not None:
            self[constants.DG_GRAPH_DEF_KEY] = NamedGraphs.fromData(DGGraphs)

    def _updateSettings(self, kwargs):
        settings = self[constants.SETTINGS_DEF_KEY]
        kwargsSettings = kwargs.get(constants.SETTINGS_DEF_KEY, {})
        for nodeType, attributes in settings.items():
            # override ie. from the scene
            kwargsNodeSettings = kwargsSettings.get(nodeType, [])
            kwargsNodeSettings = {
                i["name"]: definitionattrs.attributeClassForDef(i)
                for i in kwargsNodeSettings
            }
            consolidatedSettings = OrderedDict(
                (i["name"], i) for i in attributes
            )  # current attributes
            for name, newAttr in kwargsNodeSettings.items():
                existingAttr = consolidatedSettings.get(name)
                if not existingAttr:
                    consolidatedSettings[name] = newAttr

            settings[nodeType] = list(consolidatedSettings.values())

    def setSettingValue(self, nodeName, name, value):
        """Sets the value for a setting.

        :param name: The settings name
        :type name: str
        :param value: The json compatible value to set
        :type value: int, float, string, list, dict
        :type nodeName: str

        """
        sets = self.setting(nodeName, name)
        if sets:
            sets.value = value

    def addSetting(self, nodeName, **kwargs):
        """Adds a setting(attribute) for the node to the definition.

        :param nodeName: The node name to attach the setting to, if the node already exists \
        in the definition then it will be appended else a new entry will be added.
        :type nodeName: str
        :param kwargs: dict  see :class:`definitionattrs.AttributeDefinition` for more information.
        :type kwargs: dict
        :return: The new settings instance.
        :rtype: :class:`definitionattrs.AttributeDefinition` or None
        :keyword name (str): The Name for the setting.
        :keyword value (int or float or str or string or iterable): The json supported python value.
        :keyword default (int or float or str or iterable): The json supported python value.
        :keyword Type (int): The attribute type int, see: :mod:`zoo.libs.maya.api.attrtypes`
        :keyword softMin (float): The softMin(UI) for the attribute, only valid for numeric Attrs
        :keyword softMax (float): The softMax(UI) for the attribute, only valid for numeric Attrs
        :keyword min (float or int): The min for the attribute, only valid for numeric Attrs
        :keyword max (float or int): The max for the attribute, only valid for numeric Attrs
        :keyword locked (bool): Whether this attribute should be locked.
        :keyword channelBox (bool): Whether this attribute should be displayed in the channelBox.
        :keyword keyable (bool): Whether this attribute should be keyable by an animator.
        """
        exists = self.setting(nodeName, kwargs.get("name", ""))
        if exists:
            exists.value = kwargs.get("value", exists.value)
            exists.default = kwargs.get("default", exists.default)
            exists.min = kwargs.get("min", exists.min)
            exists.max = kwargs.get("min", exists.max)
            exists.softMin = kwargs.get("softMin", exists.softMin)
            exists.softMax = kwargs.get("softMax", exists.softMax)
            return
        s = definitionattrs.attributeClassForDef(kwargs)
        self[constants.SETTINGS_DEF_KEY].setdefault(nodeName, []).append(s)
        return s

    def addSettings(self, nodeName, settingsDefs):
        for setting in settingsDefs:
            self.addSetting(nodeName, **setting)

    def insertSettingByName(self, nodeName, name, settingDef, before=False):
        """Inserts a setting either before or after the existing setting by the given name.

        :param nodeName: The node name to attach the setting to, if the node already exists \
        in the definition then it will be appended else a new entry will be added.
        :type nodeName: str
        :param name: The name of existing setting.
        :type name: str
        :param settingDef: The new Setting to insert.
        :type settingDef: :class:`definitionattrs.AttributeDefinition` or Dict
        :param before: If True then the Setting will be added before the found Setting
        :type before: bool
        :return: Whether the attribute was successfully inserted.
        :rtype: bool
        """
        if nodeName not in self[constants.SETTINGS_DEF_KEY]:
            return False
        s = definitionattrs.attributeClassForDef(settingDef)
        for index, attrDef in enumerate(self[constants.SETTINGS_DEF_KEY][nodeName]):
            if attrDef.name == name:
                insertIndex = index if before else index + 1
                self[constants.SETTINGS_DEF_KEY][nodeName].insert(insertIndex, s)
                return True
        return False

    def insertSetting(self, nodeName, index, settingDef):
        """Inserts a setting either before or after the existing setting by the given name.

        :param nodeName: The node name to attach the setting to, if the node already exists \
        in the definition then it will be appended else a new entry will be added.
        :type nodeName: str
        :param index: The index to insert the Setting:
        :type index: int
        :param settingDef: The new Setting to insert.
        :type settingDef: :class:`definitionattrs.AttributeDefinition` or Dict
        :return: Whether or not the attribute was successfully inserted.
        :rtype: bool
        """
        if nodeName not in self[constants.SETTINGS_DEF_KEY]:
            return False
        s = definitionattrs.attributeClassForDef(settingDef)
        self[constants.SETTINGS_DEF_KEY][nodeName].insert(index, s)

    def insertSettings(self, nodeName, index, settingDefs):
        if nodeName not in self[constants.SETTINGS_DEF_KEY]:
            return False
        existing = {i.name for i in self[constants.SETTINGS_DEF_KEY][nodeName]}
        currentIndex = 0
        for i, setting in enumerate(settingDefs):
            if setting["name"] in existing:
                continue
            s = definitionattrs.attributeClassForDef(setting)
            self[constants.SETTINGS_DEF_KEY][nodeName].insert(index + currentIndex, s)
            currentIndex += 1

    def settingIndex(self, nodeName, name):
        try:
            nodeSettings = self[constants.SETTINGS_DEF_KEY][nodeName]
            for index, i in enumerate(iter(nodeSettings)):
                if i.name == name:
                    return index
            return -1
        except KeyError:
            return -1

    def deleteSettings(self, nodeName, names):
        """Deletes a group of settings from the layer node.

        :param nodeName: The setting node name to search for settings.
        :type nodeName: str
        :param names: A list of setting names to search and remove.
        :type names: list[str]
        :return: Whether deletion was successful.
        :rtype: bool
        """
        try:
            nodeSettings = self[constants.SETTINGS_DEF_KEY][nodeName]
            maintain = [i for i in nodeSettings if i.name not in names]
            self[constants.SETTINGS_DEF_KEY][nodeName] = maintain
            return len(maintain) != len(nodeSettings)
        # only occurs if the nodeName doesn't exist in the layer settings
        except KeyError:
            return False

    def deleteSetting(self, nodeName, name):
        """Deletes a group of setting by name from the layer node.

        :param nodeName: The setting node name to search for the setting.
        :type nodeName: str
        :param name: The Settings name to remove.
        :type name: str
        :return: Whether deletion was successful.
        :rtype: bool
        """
        try:
            nodeSettings = self[constants.SETTINGS_DEF_KEY][nodeName]

            for i in nodeSettings:
                if i.name == name:
                    nodeSettings.remove(i)
                    return True
            return False
        except KeyError:
            return False

    def setting(self, nodeName, name):
        """Return's the :class:`definitionattrs.AttributeDefinition` instance attached to the node in this definition
        if it exists.

        :param nodeName: the node that the setting is part of
        :type nodeName: str
        :param name: the settings name
        :type name: str
        :rtype: :class:`definitionattrs.AttributeDefinition`
        """
        try:
            nodeSettings = self[constants.SETTINGS_DEF_KEY][nodeName]
            for i in iter(nodeSettings):
                if i.name == name:
                    return i
        except KeyError:
            return


class InputLayerDefinition(LayerDef):

    @classmethod
    def fromData(cls, layerData):
        """Transforms the provided data in to a set of InputNode and attribute classes. Each class created
        inherits from dict

        :param layerData: The input layer data
        :type layerData:  dict
        :return: Returns a new InputLayer definition
        :rtype: :class:`InputLayerDefinition`
        """
        data = {
            constants.SETTINGS_DEF_KEY: list(
                map(
                    definitionattrs.attributeClassForDef,
                    layerData.get(constants.SETTINGS_DEF_KEY, []),
                )
            ),
            constants.DAG_DEF_KEY: list(
                map(
                    definitionnodes.InputDefinition.deserialize,
                    iter(layerData.get(constants.DAG_DEF_KEY, [])),
                )
            ),
        }

        return cls(data)

    def update(self, kwargs):
        self[constants.SETTINGS_DEF_KEY] = (
            list(
                map(
                    definitionattrs.attributeClassForDef,
                    kwargs.get(constants.SETTINGS_DEF_KEY, []),
                )
            )
            or self[constants.SETTINGS_DEF_KEY]
        )
        for ioNode in defutils.traverseDefinitionLayerDag(kwargs):
            self.createInput(**ioNode)

    def input(self, name):
        """Returns the input node.

        :param name: the id of the input node.
        :type name: str
        :return: the input
        :rtype: :class:`definitionnodes.InputDefinition`
        """
        for data in self.iterInputs():
            if data["id"] == name:
                return data

    def iterInputs(self):
        """Generator Function that iterates all input definitions.

        :rtype: Generator(:class:`definitionnodes.InputDefinition`)
        """
        for inputDef in iter(self.get(constants.DAG_DEF_KEY, [])):
            yield inputDef
            for child in inputDef.iterChildren():
                yield child

    def clearInputs(self):
        """Deletes all input nodes from this definition"""
        self[constants.DAG_DEF_KEY] = []

    def addInput(self, inputDef):
        """Adds an input to this definition.

        :param inputDef: The InputDefinition for the input
        :type inputDef: :class:`definitionnodes.InputDefinition`
        """
        inputDef["hiveType"] = "input"
        if inputDef.parent is None:
            self[constants.DAG_DEF_KEY].append(inputDef)
            return

        for g in self.iterInputs():
            if g.id == inputDef.parent:
                g.children.append(inputDef)
                break

    def createInput(self, **info):
        existingInput = self.input(info["id"])
        if existingInput is not None:
            return existingInput
        parent = info.get("parent")
        if parent == "root":
            parent = None
        inputDef = definitionnodes.InputDefinition.deserialize(info, parent=parent)
        self.addInput(inputDef)
        return inputDef

    def inputSetting(self, name):
        """Returns the input setting from this definition

        :param name: the input name
        :type name: str
        :rtype: :class:`definitionattrs.AttributeDefinition` or None
        """
        for setting in iter(self[constants.SETTINGS_DEF_KEY]):
            if setting.name == name:
                return setting

    def addInputSetting(self, **kwargs):
        """Appends a new input setting to this definition

        :param kwargs: the input Setting instance
        :rtype: :class:`definitionattrs.AttributeDefinition` or None
        """
        self[constants.SETTINGS_DEF_KEY].append(
            definitionattrs.attributeClassForDef(kwargs)
        )

    def deleteInputs(self, *inputIds):
        topLevelNodesToDelete = []
        for inputNode in self.iterInputs():
            if inputNode.id not in inputIds:
                continue
            elif inputNode.parent is None:
                topLevelNodesToDelete.append(inputNode)
                continue
            parent = self.input(inputNode.parent)
            parent.deleteChild(inputNode.id)
        for node in topLevelNodesToDelete:
            self[constants.DAG_DEF_KEY].remove(node)


class OutputLayerDefinition(LayerDef):
    @classmethod
    def fromData(cls, layerData):
        """Transforms the provided data in to a set of OutputNode and attribute classes. Each class created
        inherits from dict

        :param layerData: The output layer data
        :type layerData:  dict
        :return: Returns a new OutputLayer definition
        :rtype: :class:`OutputLayerDefinition`
        """
        data = {
            constants.SETTINGS_DEF_KEY: list(
                map(
                    definitionattrs.attributeClassForDef,
                    layerData.get(constants.SETTINGS_DEF_KEY, []),
                )
            ),
            constants.DAG_DEF_KEY: list(
                map(
                    definitionnodes.OutputDefinition.deserialize,
                    iter(layerData.get(constants.DAG_DEF_KEY, [])),
                )
            ),
        }
        return cls(data)

    def update(self, kwargs):
        self[constants.SETTINGS_DEF_KEY] = (
            list(
                map(
                    definitionattrs.attributeClassForDef,
                    kwargs.get(constants.SETTINGS_DEF_KEY, []),
                )
            )
            or self[constants.SETTINGS_DEF_KEY]
        )
        for ioNode in defutils.traverseDefinitionLayerDag(kwargs):
            currentNode = self.output(ioNode["id"])
            # merge the IO node inplace
            if currentNode is not None:
                children = ioNode.get("children")
                if children:
                    ioNode["children"] = [
                        definitionnodes.OutputDefinition.deserialize(i, ioNode["id"])
                        for i in children
                    ]
                currentNode.update(ioNode)
            # a IO node won't exist in the definition when it's been dynamically generated
            else:
                self.createOutput(**ioNode)

    def output(self, name):
        for data in self.iterOutputs():
            if data["id"] == name:
                return data

    def iterOutputs(self):
        """Generator Function that iterates all input definitions.

        :rtype: iterable(:class:`definitionnodes.OutputDefinition`)
        """
        for outputDef in iter(self.get(constants.DAG_DEF_KEY, [])):
            yield outputDef
            for child in outputDef.iterChildren():
                yield child

    def clearOutputs(self):
        """Deletes all output nodes from this definition"""
        self[constants.DAG_DEF_KEY] = []

    def createOutput(self, **info):
        existingOutput = self.output(info["id"])
        if existingOutput is not None:
            existingOutput.parent = info.get("parent", existingOutput.parent)
            return existingOutput
        parent = info.get("parent", None)
        # root is a reverse ID purely for the guides so here we remap to None as root
        # won't exist in outputs and root == root Layer == outputLayer == None
        if parent == "root":
            parent = None
        outputDef = definitionnodes.OutputDefinition.deserialize(info, parent=parent)
        self.addOutput(outputDef)
        return outputDef

    def addOutput(self, outputDef):
        """Adds an output to this definition.

        :param outputDef: The output definition
        :type outputDef: :class:`definitionnodes.OutputDefinition`
        """
        outputDef["hiveType"] = "output"
        if outputDef.parent is None:
            self[constants.DAG_DEF_KEY].append(outputDef)
            return

        for g in self.iterOutputs():
            if g.id == outputDef.parent:
                g.children.append(outputDef)
                break

    def outputSetting(self, name):
        """Returns the output setting from this definition

        :param name: the output name
        :type name: str
        :rtype: :class:`definitionattrs.AttributeDefinition` or None
        """
        for setting in iter(self[constants.SETTINGS_DEF_KEY]):
            if setting.name == name:
                return setting

    def addOutputSetting(self, **kwargs):
        """Appends a new output setting to this definition

        :param kwargs: the output Setting instance
        :type kwargs: :class:`definitionattrs.AttributeDefinition`
        """
        self[constants.SETTINGS_DEF_KEY].append(
            definitionattrs.attributeClassForDef(kwargs)
        )

    def deleteOutputs(self, *outputIds):
        topLevelNodesToDelete = []
        for output in self.iterOutputs():
            if output.id not in outputIds:
                continue
            elif output.parent is None:
                topLevelNodesToDelete.append(output)
                continue
            parent = self.output(output.parent)
            parent.deleteChild(output.id)
        for node in topLevelNodesToDelete:
            self[constants.DAG_DEF_KEY].remove(node)


class DeformLayerDefinition(LayerDef):
    @classmethod
    def fromData(cls, layerData):
        """Transforms the provided data in to a set of Joint and attribute classes. Each class created
        inherits from dict

        :param layerData: The Deform layer data
        :type layerData:  dict
        :return: Returns a new DeformLayer definition
        :rtype: :class:`DeformLayerDefinition`
        """
        data = {
            constants.SETTINGS_DEF_KEY: list(
                map(
                    definitionattrs.attributeClassForDef,
                    layerData.get(constants.SETTINGS_DEF_KEY, []),
                )
            ),
            constants.DAG_DEF_KEY: list(
                map(
                    definitionnodes.JointDefinition.deserialize,
                    iter(layerData.get(constants.DAG_DEF_KEY, [])),
                )
            ),
        }
        return cls(data)

    def update(self, kwargs):
        self[constants.SETTINGS_DEF_KEY] = (
            list(
                map(
                    definitionattrs.attributeClassForDef,
                    kwargs.get(constants.SETTINGS_DEF_KEY, []),
                )
            )
            or self[constants.SETTINGS_DEF_KEY]
        )
        deformLayerInfo = kwargs.get(constants.DAG_DEF_KEY)
        if deformLayerInfo:
            self[constants.DAG_DEF_KEY] = list(
                map(definitionnodes.JointDefinition.deserialize, iter(deformLayerInfo))
            )

    def clearJoints(self):
        self[constants.DAG_DEF_KEY] = []

    def createJoint(self, **info):
        existingJoint = self.joint(info["id"])
        if existingJoint is not None:
            return existingJoint
        parent = info.get("parent", "")
        if parent == "root":
            parent = None
        jointDef = definitionnodes.JointDefinition.deserialize(info, parent=parent)
        self.addJoint(jointDef)
        return jointDef

    def joint(self, jointId):
        """Returns the JointDefinition instance by the provided the id.

        :param jointId: The joint id to filter.
        :type jointId: str
        :rtype: :class:`definitionnodes.JointDefinition` or None
        """
        for g in self.iterDeformJoints():
            if g.id == jointId:
                return g

    def findJoints(self, *ids):
        """Returns the JointDefinition instance by the provided the id.

        :param ids: The joint ids to filter.
        :type ids: tuple[str]
        :rtype: list[:class:`definitionnodes.JointDefinition`]
        """
        results = [None] * len(ids)
        for jnt in self.iterDeformJoints():
            jntId = jnt.id
            if jntId in ids:
                results[ids.index(jntId)] = jnt
        return results

    def addJoint(self, jointDef):
        """Adds a joint to this definition.

        :param jointDef: The output definition
        :type jointDef: :class:`definitionnodes.JointDefinition`
        """
        jointDef["hiveType"] = "joint"
        if not jointDef.parent:
            self[constants.DAG_DEF_KEY].append(jointDef)
            return

        for g in self.iterDeformJoints():
            if g.id == jointDef.parent:
                g.children.append(jointDef)
                break

    def iterDeformJoints(self):
        """Returns the :class:`definitionnodes.JointDefinition` instance that is attached to this
        Definition instance.

        :rtype: :class:`definitionnodes.JointDefinition` or None
        """
        for joint in iter(self.get(constants.DAG_DEF_KEY, [])):
            yield joint
            for child in joint.iterChildren():
                yield child

    def deleteJoints(self, *jointIds):
        """Deletes the joints from the layer based on the provided joint ids.

        :param jointIds: The joint ids to search for.
        :type jointIds: tuple[str]
        """
        topLevelNodesToDelete = []
        for jnt in self.iterDeformJoints():
            if jnt.id not in jointIds:
                continue
            elif jnt.parent is None:
                topLevelNodesToDelete.append(jnt)
                continue
            parent = self.joint(jnt.parent)
            parent.deleteChild(jnt.id)
        for node in topLevelNodesToDelete:
            self[constants.DAG_DEF_KEY].remove(node)


class NamedGraphs(list):
    """List of :class:`NamedGraph` instances."""

    @classmethod
    def fromData(cls, layerData):
        """Transforms the provided data in to a set of Joint and attribute classes. Each class created
        inherits from dict

        :param layerData: List of dicts where each dict is a named graph
        :type layerData:  dict
        :return: Returns a new DeformLayer definition
        :rtype: :class:`NamedGraphs`
        """

        return cls([NamedGraph.fromData(i) for i in layerData])

    def graph(self, graphId):
        """Returns the graph instance.

        :param graphId: The graph id to search for.
        :type graphId: str
        :rtype: :class:`NamedGraph` or None
        """
        for g in self:
            if g.id == graphId:
                return g


class NamedGraph(general.ObjectDict):
    """Contains a network of Dependency graph nodes, and it's internal connections"""

    @classmethod
    def fromData(cls, graphData):
        """Parses the provided graphData and creates a :class:`NamedGraph` instance.

        :param graphData: The Raw Graph data to parse into a :class:`NamedGraph`
        :type graphData: dict
        :return: The newly created :class:`NamedGraph` instance.
        :rtype: :class:`NamedGraph`
        """
        graphId = graphData.get("id", "")
        return cls(
            {
                "id": graphId,
                "name": graphData.get("name", graphId),
                "nodes": [
                    definitionnodes.DGNode(i) for i in graphData.get("nodes", [])
                ],
                "connections": graphData.get("connections", []),
                "inputs": graphData.get("inputs", {}),
                "outputs": graphData.get("outputs", {}),
                "metaData": graphData.get("metaData", {}),
            }
        )

    @property
    def graphId(self):
        """Returns the graph id,

        :rtype: str
        """
        return self["id"]

    @graphId.setter
    def graphId(self, newName):
        """Sets the name on this graph.

        :param newName: The new name.
        :type newName: str
        """
        self["id"] = newName

    @property
    def name(self):
        """Returns the graph id,

        :rtype: str
        """
        return self["name"]

    @name.setter
    def name(self, newName):
        """Sets the name on this graph.

        :param newName: The new name.
        :type newName: str
        """
        self["name"] = newName

    @property
    def nodes(self):
        """Returns the DG nodes for this graph.

        :rtype: list[:class:`definitionnodes.DGNode`]
        """
        return self["nodes"]

    def node(self, nodeId):
        """Returns the node instance in the graph for the provided nodeId

        :param nodeId: The node id to search for
        :type nodeId: str
        :return:
        :rtype: :class:`definitionnodes.DGNode` or None
        """
        for i in self.nodes:
            if i.id == nodeId:
                return i

    @property
    def connections(self):
        """Returns the graph internal connections

        :rtype: list[dict]
        """
        return self["connections"]

    def inputs(self):
        return self.get("inputs", {})

    def outputs(self):
        return self.get("outputs", {})
