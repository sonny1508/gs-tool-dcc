from zoo.preferences import core


def coreInterface():
    """ Get the core interface

    :return: Returns the preference interface "core_interface"
    :rtype: :class:`preferences.interface.preference_interface.ZooToolsPreference`
    """

    return core.preference.interface("core_interface")


def generalInterface():
    """ Get the general settings

    :return: Returns the preference interface "general_interface"
    :rtype: :class:`preferences.interface.general_interface.GeneralPreferences`
    """
    return core.preference.interface("general_interface")
