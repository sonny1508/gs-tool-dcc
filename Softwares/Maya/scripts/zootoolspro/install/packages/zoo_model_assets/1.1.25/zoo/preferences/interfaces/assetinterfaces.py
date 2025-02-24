from zoo.preferences.core import preference


def mayaScenesInterface():
    """ Get the Model assets preferences

    :return: Returns the preference interface "maya_scenes_interface"
    :rtype: :class:`preferences.interface.maya_scenes_interface.MayaScenesPreference`
    """
    return preference.interface("maya_scenes_interface")


def modelAssetsInterface():
    """ Get the Model assets preferences

    :return: Returns the preference interface "model_assets_interface"
    :rtype: :class:`preferences.interface.model_assets_interface.ModelAssetsPreference`
    """
    return preference.interface("model_assets_interface")
