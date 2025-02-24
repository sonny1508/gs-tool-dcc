from zoo.preferences.core import preference


def hiveInterface():
    """ Get the Hive preferences interface instance.

    :rtype: :class:`preferences.interface.hive.HiveInterface`
    """

    return preference.interface("Hive")


