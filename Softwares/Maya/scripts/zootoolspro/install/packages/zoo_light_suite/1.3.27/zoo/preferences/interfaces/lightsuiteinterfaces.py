from zoo.preferences.core import preference


def lightSuiteInterface():
    """ Get the general settings

    :return: Returns the preference interface "camera_tools_interface"
    :rtype: :class:`preferences.interface.zoo_light_suite_interface.LightSuitePreference`
    """
    return preference.interface("light_suite_interface")

