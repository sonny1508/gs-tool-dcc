import webbrowser

from zoo.apps.toolpalette import palette
from zoo.libs.pyqt.widgets.frameless import window
from zoo.core.util import zlogging
from zoo.apps.toolpalette import qtshelf
from zoo.core import engine


logger = zlogging.getLogger(__name__)


class QtShelf(palette.ActionPlugin):
    id = "zoo.qt_shelf"
    creator = "David Sparrow"
    tags = ["unittest", "test"]
    uiData = {"icon": "checkOnly",
              "tooltip": "Opens the Zootools Qt Shelf",
              "label": "Shelf Pop Up",
              }

    def execute(self, *args, **kwargs):
        return engine.currentEngine().showDialog(qtshelf.ShelfWindow, name="zooShelf", show=True)


class HelpIconShelf(palette.ActionPlugin):
    id = "zoo.shelf.help"
    creator = "Andrew Silke"
    tags = ["shelf", "icon"]
    uiData = {"icon": "helpMenu_shlf",
              "label": "Help Menu"
              }
    _ADDRESSES = dict(create3dcharacters="https://create3dcharacters.com",
                      latestNews="https://create3dcharacters.com/latest-news",
                      zooToolsHelpContents="https://create3dcharacters.com/zoo2",
                      zooToolsGettingStarted="https://create3dcharacters.com/zootools-getting-started",
                      zooToolsInstallUpdate="https://create3dcharacters.com/maya-zoo-tools-pro-installer",
                      zooToolsAssetsPresets="https://create3dcharacters.com/maya-zoo-tools-pro-installer",
                      zooChangelog="https://create3dcharacters.com/maya-zoo-tools-pro-changelog",
                      zooIssuesFixes="https://create3dcharacters.com/maya-zoo-tools-pro-known-issues",
                      coursesByOrder="https://create3dcharacters.com/package-courses",
                      coursesByPopularity="https://create3dcharacters.com/package-by-popularity",
                      coursesByDateAdded="https://create3dcharacters.com/package-by-date-added",
                      intermediateCourse="https://create3dcharacters.com/package-maya-generalist-intermediate",
                      advancedCourse="https://create3dcharacters.com/package-maya-generalist-advanced",
                      mayaHotkeyList="https://create3dcharacters.com/maya-hotkeys-zoo2",
                      developerDocumentation="https://create3dcharacters.com/zoo-dev-documentation/index.html")

    def execute(self, *args, **kwargs):
        name = kwargs["variant"]
        address = HelpIconShelf._ADDRESSES.get(name)
        if address:
            webbrowser.open(address)


class ZooShelfFloatingWindow(palette.ActionPlugin):
    id = "zoo.shelf.zooFloatingShelf"
    creator = "ZooTools"
    tags = ["shelf", "icon"]
    uiData = {"icon": "zooToolsZ",
              "tooltip": "Floating Shelf For Zoo Tools",
              "label": "Zoo Floating Shelf (shift+alt+Q)"
              }

    def execute(self, *args, **kwargs):
        from zoo.apps.popupuis import zooshelfpopup
        zooshelfpopup.main()


class ResetAllWindowPosition(palette.ActionPlugin):
    id = "zoo.shelf.resetAllWindows"
    creator = "ZooTools"
    tags = ["shelf", "icon"]
    uiData = {"icon": "reloadWindows",
              "tooltip": "Resets all Zoo windows to be at the center of the host application",
              "label": "Reset All Zoo Windows"

              }

    def execute(self, *args, **kwargs):
        for i in window.getZooWindows():
            win = i.zooWindow
            if win is not None:
                win.centerToParent()


class ToggleZooLogging(palette.ActionPlugin):
    id = "zoo.logging"
    creator = "Zootools"
    tags = ["debug", "logging"]
    uiData = {"icon": "",
              "tooltip": "Sets Zoo tools logging to either DEBUG or INFO",
              "label": "Debug Logging",
              "isCheckable": True,
              "isChecked": zlogging.isGlobalDebug(),
              }

    def execute(self, *args, **kwargs):
        state = not zlogging.isGlobalDebug()
        if zlogging.isGlobalDebug():
            zlogging.setGlobalDebug(False)
        else:
            zlogging.setGlobalDebug(True)

        return state


