from zoo.libs.hive.base import definition as baseDef, errors
from zoo.libs.hive.base import naming
from zoo.libs.hive import constants
from zoo.core.util import zlogging

logger = zlogging.getLogger(__name__)


def updateAndMergeComponentDefFromTemplate(template, configuration):
    # returns the template as a dict containing all update/merged component
    # definitions
    for compData in template.get("components", []):
        componentType = compData["type"]
        compDefinition = configuration.initComponentDefinition(componentType)
        # update the base definition with the template definition which should
        # only contain guide data
        migratedDefinition = baseDef.migrateToLatestVersion(compData, originalComponent=compDefinition)
        compDefinition.update(migratedDefinition)
        yield compDefinition


def updateRigConnections(components):
    # remap parents and constraints
    for oldName, newComponent in components.items():
        compDef = newComponent.definition
        # parent name and side "componentName:side"
        parent = compDef.parent  # type: str
        connections = compDef.connections  # [dict] this the serialized constraint
        remapParentName = None
        if parent is not None:
            parentComponent = components.get(parent)
            if parentComponent:
                remapParentName = parentComponent.serializedTokenKey()
                newComponent.setParent(parentComponent)
            else:
                connections = {}
        compDef.parent = remapParentName
        # now do the constraints
        for constraint in connections.get("constraints", []):
            remapTargets = []
            for index, target in enumerate(constraint["targets"]):
                targetLabel, targetId = target
                compName, compSide, id_ = targetId.split(":")
                targetKey = ":".join((compName, compSide))
                parentComponent = components.get(targetKey)
                if parentComponent:
                    remapTargets.append([targetLabel, ":".join((parentComponent.serializedTokenKey(), id_))])
            constraint["targets"] = remapTargets


def loadFromTemplate(template, rig):
    """Loads the hive template on to a rig.

    :param template: The hive Template data structure.
    :type template: dict
    :param rig: An existing rig Instance, if None a new rig will be created.
    :type rig: :class:`Rig`
    :return: A list of newly created components.
    :rtype: dict[str, :class:`component.Component`]
    """

    templateComponents = template.get("components")
    if not templateComponents:
        logger.error("No components saved in template: {}, skipping operation!".format(template["name"]))
        raise errors.TemplateMissingComponents(template["name"])

    logger.debug("Creating components from template")
    # first create the components on the rig
    # second remap the parent names to the newly create components if the parent exists there
    # else use the name from the rig.
    # third remap the constraint serialized data in the same way as the parent
    newComponents = {}
    for compDefinition in updateAndMergeComponentDefFromTemplate(template, rig.configuration):
        definitionName = ":".join((compDefinition.name, compDefinition.side))
        newComponent = rig.createComponent(compDefinition.type,
                                           compDefinition.name,
                                           compDefinition.side,
                                           definition=compDefinition)
        newComponents[definitionName] = newComponent
    # remap parents and constraints
    updateRigConnections(newComponents)
    return newComponents


def validateUpdateRigFromTemplate(rig, templateData):
    """Validates the template against the provided rig instance for any missing
    components useful for UIs.

    The returned data structure is in the form of:
        {
            "missingComponents": [:class:`zoo.libs.hive.base.component.Component`]
        }


    :param rig: The rig instance to validate.
    :type rig: `zoo.libs.hive.base.rig.Rig`
    :param templateData: The template data to validate against
    :type templateData: dict
    :rtype: dict
    """
    templateComponents = {":".join((i["name"], i["side"])) for i in templateData["components"]}
    validationData = {}
    for comp in rig.iterComponents():
        token = comp.serializedTokenKey()
        if token not in templateComponents:
            validationData.setdefault("missingComponents", []).append(comp)
    return validationData


def updateRigFromTemplate(rigInstance, templateData, remapping):
    """Updates the rig instance with the template.

    It is important to note that this function will completely wipe
    out all meta-data for each component, except for the component meta node.
    However, all deform Joints will be maintained.

    :param rigInstance:
    :type rigInstance: :class:`zoo.libs.hive.base.rig.Rig`
    :param templateData: The template dict which will override the rigInstance.
    :type templateData: dict
    :param remapping:
    :type: remapping: dict
    """
    existingComponents = {comp.serializedTokenKey(): comp for comp in rigInstance.iterComponents()}
    rigInstance.deleteRigs()
    rigInstance.deleteGuides()
    # dump the configuration from the template
    config = rigInstance.configuration
    templateConfig = templateData.get("config", {})
    config.applySettingsState(templateConfig)
    componentRemap = remapping.get("components", {})
    try:
        config.updateBuildScriptConfig(rigInstance, {k: v for k, v in templateConfig.get("buildScripts", {})})
    except ValueError:  # todo: replace once we rewrite build script save/load
        pass
    rigInstance.saveConfiguration()
    skeletonMap = {}
    logger.debug("Deleting I/O layers and create skeleton Map")
    for comp in existingComponents.values():
        layers = comp.meta.layersById((
            constants.DEFORM_LAYER_TYPE, constants.INPUT_LAYER_TYPE, constants.OUTPUT_LAYER_TYPE
        ))
        if not layers[constants.DEFORM_LAYER_TYPE]:
            continue
        token = comp.serializedTokenKey()
        componentRemapData = componentRemap.get(token, {"name": token})
        skeletonMap[componentRemapData["name"]] = [(jnt.id(), jnt) for jnt in
                                                   layers[constants.DEFORM_LAYER_TYPE].iterJoints()]
        layers[constants.DEFORM_LAYER_TYPE].disconnectAllJoints()
    rigInstance.deleteComponents()

    logger.debug("Merging/saving template as component definition and creating missing components")
    newComponents = loadFromTemplate(templateData, rig=rigInstance)

    # now update the connections from the template
    updateRigConnections(newComponents)
    logger.debug("Adding back in deform joints from the skeleton map")
    for comp in newComponents.values():
        deformLayer = comp.deformLayer()
        if not deformLayer:
            hrcName, metaName = naming.composeNamesForLayer(comp.namingConfiguration(),
                                                            comp.name(),
                                                            comp.side(),
                                                            constants.DEFORM_LAYER_TYPE)
            deformLayer = comp.meta.createLayer(constants.DEFORM_LAYER_TYPE, hrcName, metaName,
                                                parent=comp.meta.rootTransform())

        skelMap = skeletonMap.get(comp.serializedTokenKey(), [])
        for jntId, jnt in skelMap:
            deformLayer.addJoint(jnt, jntId)
