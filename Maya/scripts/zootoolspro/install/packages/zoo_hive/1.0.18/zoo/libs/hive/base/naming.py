
def uniqueNameForComponentByRig(rig, name, side):
    """Returns a unique name for the component using a rig instance.

    :param rig: The rig instance to use as the filter
    :type rig: :class:`zoo.libs.hive.base.rig.Rig`
    :param name: The new name for the component.
    :type name: str
    :param side: The component side name.
    :type side: str
    :return: A unique name will be returned eg. 'arm' may return arm001
    :rtype: str
    """
    currentName = ":".join([name, side])
    currentNames = [":".join([i.name(), i.side()]) for i in rig.iterComponents()]
    count = 1
    while currentName in currentNames:
        currentName = ":".join([name + str(count).zfill(3), side])
        count += 1
    return currentName.split(":")[0]


def uniqueNameForRig(rigs, name):
    """Returns a unique name for the component using a rig instance.

    :param rigs: The rig instance to use as the filter
    :type rigs: tuple(:class:`zoo.libs.hive.base.rig.Rig`)
    :param name: The new name for the component.
    :type name: str
    :return: A unique name will be returned eg. 'arm' may return arm001
    :rtype: str
    """
    newname = name
    currentNames = [i.name() for i in rigs]
    count = 1
    while newname in currentNames:
        newname = name + str(count).zfill(3)
        count += 1
    return newname


def composeComponentRootNames(config, compName, compSide):
    """Composes and returns the resolved node names for the component root HRC and meta nodes.

    :param config: The naming configuration instance.
    :type config: :class:`zoo.libs.naming.naming.NameManager`
    :param compName: The component name
    :type compName: str
    :param compSide: The component side name.
    :type compSide: str
    :return: first element is the root Hrc Name, second element is the Meta Node name
    :rtype: tuple[str, str]
    """
    hrcName = config.resolve("componentHrc", {"componentName": compName,
                                              "side": compSide,
                                              "type": "hrc"})
    metaName = config.resolve("componentMeta", {"componentName": compName,
                                                "side": compSide,
                                                "type": "meta"})
    return hrcName, metaName


def composeRigNamesForLayer(config, rigName, layerType):
    """Composes and returns the resolved node names for the layer root HRC and meta nodes.

    :param config: The naming configuration instance.
    :type config: :class:`zoo.libs.naming.naming.NameManager`
    :param rigName: The component name
    :type rigName: str
    :param layerType: The hive layer type name to resolve ie. api.constants.GUIDE_LAYER_TYPE.
    :return: first element is the root Hrc Name, second element is the Meta Node name
    :rtype: tuple[str, str]
    """
    hrcName = config.resolve("layerHrc", {"rigName": rigName,
                                          "type": "hrc",
                                          "layerType": layerType})
    metaName = config.resolve("layerMeta", {"rigName": rigName,
                                            "type": "meta",
                                            "layerType": layerType})
    return hrcName, metaName


def composeNamesForLayer(config, compName, compSide, layerType):
    """Composes and returns the resolved node names for the layer root HRC and meta nodes.

    :param config: The naming configuration instance.
    :type config: :class:`zoo.libs.naming.naming.NameManager`
    :param compName: The component name
    :type compName: str
    :param compSide: The component side name.
    :type compSide: str
    :param layerType: The hive layer type name to resolve ie. api.constants.GUIDE_LAYER_TYPE.
    :return: first element is the root Hrc Name, second element is the Meta Node name
    :rtype: tuple[str, str]
    """
    hrcName = config.resolve("layerHrc", {"componentName": compName,
                                          "side": compSide,
                                          "type": "hrc",
                                          "layerType": layerType})
    metaName = config.resolve("layerMeta", {"componentName": compName,
                                            "side": compSide,
                                            "type": "meta",
                                            "layerType": layerType})
    return hrcName, metaName


def composeContainerName(config, compName, compSide):
    """Composes and returns the resolved node name for the component container node.

    :param config: The naming configuration instance.
    :type config: :class:`zoo.libs.naming.naming.NameManager`
    :param compName: The component name
    :type compName: str
    :param compSide: The component side name.
    :type compSide: str
    :return: The resolved name for the container
    :rtype: str
    """
    return config.resolve("containerName", {"componentName": compName,
                                            "side": compSide,
                                            "section": "root",
                                            "type": "container"})


def composeAnnotationGrpName(config, compName, compSide):
    """Composes and returns the resolved node names for the component Annotation group transform node.

    :param config: The naming configuration instance.
    :type config: :class:`zoo.libs.naming.naming.NameManager`
    :param compName: The component name
    :type compName: str
    :param compSide: The component side name.
    :type compSide: str
    :return: Resolved name for the annotation group
    :rtype: str
    """
    return config.resolve("annotationGrp", {"componentName": compName, "side": compSide,
                                            "type": "annotationGroup"})


def composeSettingsName(config, compName, compSide, section):
    """Composes and returns the resolved node names for the component root HRC and meta nodes.

    :param config: The naming configuration instance.
    :type config: :class:`zoo.libs.naming.naming.NameManager`
    :param compName: The component name
    :type compName: str
    :param compSide: The component side name.
    :type compSide: str
    :param section: The settings unique section name ie. "controlPanel"
    :return: The resolved name for the settings node
    :rtype: str
    """
    return config.resolve("settingsName",
                          {"componentName": compName,
                           "side": compSide,
                           "section": section,
                           "type": "settings"})
