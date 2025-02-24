from zoo.preferences.core import preference


def cameraToolInterface():
    """ Get the general settings

    :return: Returns the preference interface "camera_tools_interface"
    :rtype: :class:`preferences.interface.cameratoolsinterface.CameraToolsPreferences`
    """
    return preference.interface("camera_tools_interface")
