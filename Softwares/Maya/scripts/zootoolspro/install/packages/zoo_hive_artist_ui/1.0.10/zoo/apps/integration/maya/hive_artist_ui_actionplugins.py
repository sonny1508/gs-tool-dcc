from zoo.apps.toolpalette import palette
from zoo.libs.maya.utils import mayaenv
from zoo.libs.pyqt.widgets import elements
from zoo.core import engine


class HiveArtistUi(palette.ActionPlugin):
    id = "zoo.hive.artistui"
    creator = "Keen Foong"
    tags = ["hive", "rig", "ui", "artist"]
    uiData = {"icon": "menu_hive",
              "label": "Hive-artist UI",
              "iconColor": [
                  115,
                  187,
                  211
              ]
              }

    def execute(self, variant=None):
        # temp until we have a better way of handle DCC code
        from zoo.apps.hiveartistui import artistui, utils
        eng = engine.currentEngine()

        parentWindow = eng.host.qtMainWindow
        if mayaenv.mayaVersion() < 2020:
            message = "Hive Only supports Maya 2020+"
            elements.MessageBox.showWarning(title="Unsupported Version",
                                            message=message, buttonB=None, parent=parentWindow)
            return

        success = utils.checkSceneUnits(parent=parentWindow)
        if not success:
            return

        return eng.showDialog(artistui.HiveArtistUI, name="HiveArtistUI", allowsMultiple=False)


class HiveNamingConvention(palette.ActionPlugin):
    id = "hive.namingConfig"
    creator = "Create3dCharacters"
    tags = ["hive", "rig", "ui", "artist", "naming"]
    uiData = {"icon": "zoo_preferences",
              "tooltip": "Provides the ability to edit Hive Naming Conventions",
              "label": "Hive Naming Convention",
              "iconColor": [
                  115,
                  187,
                  211
              ],
              }

    def execute(self, variant=None):
        eng = engine.currentEngine()
        # temp until we have a better way of handle DCC code
        if mayaenv.mayaVersion() < 2020:
            message = "Hive Only supports Maya 2020+"
            elements.MessageBox.showWarning(title="Unsupported Version",
                                            message=message, buttonB=None, parent=eng.host.qtMainWindow)
            return
        from zoo.apps.hiveartistui import namingconvention
        eng = engine.currentEngine()
        return eng.showDialog(namingconvention.NamingConventionUI,
                              name="HiveNamingConvention",
                              title="Hive Naming Convention",
                              width=580,
                              height=440,
                              saveWindowPref=False,
                              allowsMultiple=False
                              )
