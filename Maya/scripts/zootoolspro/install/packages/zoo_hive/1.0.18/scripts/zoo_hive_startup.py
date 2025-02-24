
def startup(package):
    """ Set up environmental variables depending on DCC
    """
    from zoo.preferences.interfaces import hiveinterfaces
    hiveInterface = hiveinterfaces.hiveInterface()
    hiveInterface.upgradePreferences()
    hiveInterface.upgradeAssets()
