from zoo.preferences.core import preference


def controlJointsInterface():
    """ Get the general settings

    :return: Returns the preference interface "control_joints_interface"
    :rtype: :class:`preferences.interface.controljointspreferences.ControlJointsPreferences`
    """
    return preference.interface("control_joints_interface")
