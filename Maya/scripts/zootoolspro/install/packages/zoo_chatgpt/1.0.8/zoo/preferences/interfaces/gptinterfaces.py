from zoo.preferences.core import preference


def gptInterface():
    """ Get the Hive preferences interface instance.

    :rtype: :class:`preferences.interface.gptinterfaces.ChatGptInterface`
    """

    return preference.interface("chatGpt")


