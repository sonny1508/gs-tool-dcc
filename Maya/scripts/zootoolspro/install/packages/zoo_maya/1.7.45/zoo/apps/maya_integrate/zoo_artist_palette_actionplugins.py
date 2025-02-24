import os
from maya import cmds
from zoo.apps.toolpalette import palette
from zoo.core import engine

from zoo.core import api
from zoo.libs.maya.qt import mayaui
from zoovendor.Qt import QtWidgets
from zoo.apps.toolpalette import run
from zoo.libs.utils import output


class InstallPackageZip(palette.ActionPlugin):
    id = "zoo.packages.installZip"
    creator = "David Sparrow"
    tags = ["package"]
    uiData = {"icon": "downloadCircle",
              "tooltip": "Allows Install zoo packages from Zip",
              "label": "Install Zoo Package",
              }

    def execute(self, *args, **kwargs):
        filePath, _ = QtWidgets.QFileDialog.getOpenFileName(mayaui.getMayaWindow(),
                                                            "Set the Zip file to load",
                                                            os.path.expanduser("~"),
                                                            "*.zip")
        if filePath:
            installed = api.currentConfig().runCommand("installPackage", ["--path", filePath])
            if not installed:
                output.displayWarning("No Zoo packages found in {}".format(filePath))
                return
            run.currentInstance().executePluginById(Reload.id)

class TriggerStateToggle(palette.ActionPlugin):
    id = "zoo.triggers.state"
    creator = "David Sparrow"
    tags = ["triggers"]
    _requiresAutoStartup = bool(int(os.getenv("ZOO_TRIGGERS_STARTUP", "1")))
    uiData = {"icon": "menu_reload",
              "tooltip": "Toggles the state of triggers, if off then marking menus will no longer operate",
              "label": "Trigger Toggle",
              "color": "",
              "backgroundColor": "",
              "isCheckable": True,
              "isChecked": _requiresAutoStartup,
              "multipleTools": False,
              "loadOnStartup": _requiresAutoStartup
              }

    def execute(self, state):
        from zoo.libs.maya.markingmenu import markingmenuoverride
        from zoo.libs.maya import triggers
        if state:
            # turn on the triggers
            markingmenuoverride.setup()
            triggers.createSelectionCallback()
            return
        # remove the triggers
        markingmenuoverride.reset()
        triggers.removeSelectionCallback()

    def teardown(self):
        from zoo.libs.maya.markingmenu import markingmenuoverride
        from zoo.libs.maya import triggers
        # remove the triggers
        markingmenuoverride.reset()
        triggers.removeSelectionCallback()


class MayaToolTipsToggle(palette.ActionPlugin):
    id = "zoo.help.tooltips"
    creator = "Keen Foong"
    tags = ["toggle"]
    uiData = {"icon": "menu_reload",
              "tooltip": "Toggle Maya Tooltips",
              "label": "Toggle Maya Tooltips",
              "color": "",
              "backgroundColor": "",
              "isCheckable": True,
              "isChecked": True,
              "multipleTools": False,
              "loadOnStartup": True
              }

    def __init__(self, *args, **kwargs):
        from zoo.libs.maya.utils import tooltips
        self.uiData['isChecked'] = tooltips.tooltipState()
        super(MayaToolTipsToggle, self).__init__(*args, **kwargs)

    def execute(self, state):
        """ Execute toggle

        :param state:
        :return:
        """
        from zoo.libs.maya.utils import tooltips
        tooltips.setMayaTooltipState(state)


class UninstallerUi(palette.ActionPlugin):
    id = "zoo.uninstaller"
    creator = "Keen Foong"
    tags = ["toggle"]
    uiData = {"icon": "trash",
              "tooltip": "Uninstall ZooToolsPro",
              "label": "Uninstall ZooToolsPro",
              "color": "",
              "backgroundColor": "",
              }

    def execute(self, *args, **kwargs):
        from zoo.apps.uninstallerui import uninstaller
        eng = engine.currentEngine()
        return eng.showDialog(uninstaller.UninstallerUi)


class Reload(palette.ActionPlugin):
    id = "zoo.reload"
    creator = "David Sparrow"
    tags = ["reload"]
    uiData = {"icon": "menu_zoo_reload",
              "tooltip": "Reloads zootools by reloading the zootools.py plugin",
              "label": "Reload",
              "color": "",
              "multipleTools": False,
              "backgroundColor": ""
              }

    def execute(self, *args, **kwargs):
        cmds.evalDeferred('from maya import cmds;cmds.flushUndo();cmds.unloadPlugin("zootools.py")\ncmds.loadPlugin("zootools.py")')


class Shutdown(palette.ActionPlugin):
    id = "zoo.shutdown"
    creator = "David Sparrow"
    tags = ["menu_shutdown"]
    uiData = {"icon": "zoo_shutdown",
              "tooltip": "shutdown zootools by unloading the zootools.py plugin",
              "label": "Shutdown",
              "color": "",
              "multipleTools": False,
              "backgroundColor": ""
              }

    def execute(self):
        cmds.evalDeferred('from maya import cmds;cmds.flushUndo();cmds.unloadPlugin("zootools.py")')


class ReloadViewport(palette.ActionPlugin):
    id = "zoo.reloadViewport"
    creator = "David Sparrow"
    tags = ["viewport", "reload"]
    uiData = {"icon": "reload2",
              "tooltip": "Forces mayas viewport to refresh",
              "label": "Refresh Viewport",
              "multipleTools": False,
              }

    def execute(self, *args, **kwargs):
        """Reload/refreshes the viewport, fixing various update issues"""
        from zoo.libs.maya.cmds.display import viewportmodes
        viewportmodes.reloadViewport(message=True)  # cmds.ogs(reset=True)
