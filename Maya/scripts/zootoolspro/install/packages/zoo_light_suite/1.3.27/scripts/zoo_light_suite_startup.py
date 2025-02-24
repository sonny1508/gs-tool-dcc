"""
Startup function:

    builds the default asset directories if they don't exist

"""

from zoo.preferences.interfaces import lightsuiteinterfaces


def startup(package):
    """Creates the assets folders if they don't exist
    1. Creates folder if it doesn't exist:
        userPath/zoo_preferences/assets/light_suite_ibl_skydomes
        userPath/zoo_preferences/assets/light_suite_light_presets

    2. Upgrades .pref to "settings" if upgrading from 2.2.3 or lower

    3. Updates .pref dictionary keys if any are missing
    """


    interface = lightsuiteinterfaces.lightSuiteInterface()
    interface.updatePrefsKeys()




