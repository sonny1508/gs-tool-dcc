import re, os
from functools import partial

from maya import cmds
from maya.api import OpenMaya as om2
from maya import OpenMaya as om1

from zoo.core.util import zlogging
from zoo.core import engine

logger = zlogging.getLogger(__name__)


class MayaHostApplication(engine.HostApplication):
    """Simple class for containing the current Host application information.
    Meant to be derived for the Host specifically.
    """

    def installLocation(self):
        return os.path.dirname(os.path.dirname(self.executable))

    @property
    def isHeadless(self):
        return om1.MGlobal.mayaState() != om1.MGlobal.kInteractive

    @property
    def qtMainWindow(self):
        from zoo.libs.maya.qt import mayaui
        return mayaui.mayaWindow()

    @property
    def pythonExecutable(self):
        from zoo.libs.maya.utils import mayaenv
        return mayaenv.mayapy(self.version)


class MayaEngine(engine.Engine):
    def postInit(self):
        version = cmds.about(installedVersion=True)
        matches = re.search(
            r"(maya)\s+([a-zA-Z]+)?\s*(.*)",
            version,
            re.IGNORECASE,
        )
        self._host = MayaHostApplication("maya", version, matches.group(3))
        self.name = "maya"

    def postEnvInit(self):
        """After all packages and pockage command scripts have been initialized.
        Implemented by derived class"""
        self._createMenuAndShelf()

    def _createMenuAndShelf(self):
        # load the artist palette plugin
        # load the menus
        try:

            if self.host.isHeadless:
                logger.debug("Not in maya.exe skipping zootools menu boot")
            else:
                from zoo.apps.toolpalette import run
                run.load(applicationName="maya")
            logger.debug("Finished Loading Zoo Tools PRO")
            om2.MGlobal.displayInfo("Zoo Tools PRO")

        except Exception as er:
            logger.error("Failed To load Zoo Tools PRO due to unknown Error",
                         exc_info=True)
            om2.MGlobal.displayError("Failed to start Zoo Tools PRO\n{}".format(er))

    def shutdownEngine(self):
        """Implemented by derived class"""
        # delete the artist palette which will delete the zootools menu and shelf, windows etc.

        om2.MGlobal.displayInfo("Unloading Zoo Tools PRO, please wait!")
        if not self.host.isHeadless:  # is in the maya UI
            self.closeAllDialogs()
            try:
                logger.debug("Unloading Zoo Tools PRO")
                from zoo.apps.toolpalette import run
                run.close(deleteMenu=True, deleteShelves=True)
            except Exception:
                logger.error("Failed to shutdown currently loaded tools", exc_info=True)

        cmds.flushUndo()

    def showDialog(self, windowCls, name="", show=True, allowsMultiple=False, **clsKwargs):
        # theory here is to specifically handle any dcc related showing of dialogs.
        # there are times when a Dcc requires special handling. The underlying tools like toolsets
        # would call this instead.
        # todo: handle workspaces
        matchingWindowInstances = self._dialogs.get(name, [])
        if not allowsMultiple:

            for i in matchingWindowInstances:
                logger.warning("Only one instance of '{}' allowed. Bringing to front.".format(i.objectName()))
                i.activateWindow()
                i.show()
                return i
        if "parent" not in clsKwargs:
            clsKwargs["parent"] = self.host.qtMainWindow
        win = windowCls(**clsKwargs)
        from zoo.libs.pyqt.widgets.frameless import window
        if isinstance(win, window.ZooWindow):
            logger.debug("ZooWindow instance detected, creating close signal connection to handle registry.")
            win.closed.connect(partial(self.closeDialog, name, win))
        self.registerDialog(name, win)
        if show:
            win.show()
        return win
