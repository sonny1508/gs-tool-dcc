from zoo.preferences.core import preference


def hiveArtistUiInterface():
    """ Get the Hive preferences interface instance.

    :rtype: :class:`preferences.interface.hive_artist_ui.HiveArtistUiInterface`
    """

    return preference.interface("Hive.artist.ui")


