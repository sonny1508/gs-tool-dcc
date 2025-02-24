import os
import subprocess
import sys
from functools import partial

import unreal

from zoo.core.util import zlogging
from zoo.core import engine
from zoo.core import api
from zoo.core import packageresolver

logger = zlogging.getLogger("zoo.{}".format(__name__))


class UnrealHostApplication(engine.HostApplication):
    """Simple class for containing the current Host application information.
    Meant to be derived for the Host specifically.
    """

    def installLocation(self):
        return os.path.dirname(os.path.dirname(self.executable))

    @property
    def isHeadless(self):
        return not unreal.is_editor()

    @property
    def pythonExecutable(self):
        return unreal.get_interpreter_executable_path()


class UnrealEngine(engine.Engine):

    def __init__(self, configuration, engineName):
        super(UnrealEngine, self).__init__(configuration, engineName)
        self.qApplication = None
        self._tickHandle = None  # type: unreal._DelegateHandle

    def postInit(self):
        version = unreal.SystemLibrary.get_engine_version()
        self._host = UnrealHostApplication("unreal", version, version)  # todo: major version

    def preEnvInit(self):
        packageConfig = os.getenv(api.constants.ZOO_PACKAGE_VERSION_FILE)
        if not packageConfig:
            os.environ[api.constants.ZOO_PACKAGE_VERSION_FILE] = "package_version_unreal.config"
        # before will do anything make sure zoo tools have access to PySide2 or similar
        try:
            from zoovendor.Qt import QtWidgets
        except ImportError:
            logger.warning("Missing PySide6")
            self._setupPyside()

    def postEnvInit(self):
        """After all packages and pockage command scripts have been initialized.
        Implemented by derived class"""
        # primary steps here after we load packages ready to load maya uis
        # load the artist palette plugin
        # load the menus
        self._startQApp()
        self._createMenuAndShelf()

    def _createMenuAndShelf(self):

        try:
            if self.host.isHeadless:
                unreal.log("Not in UnrealEditor skipping zootools menu boot")
            else:
                from zoo.apps.toolpalette import run
                palette = run.show(applicationName="unreal")
                palette.createMenus()
            unreal.log("Finished Loading Zoo Tools PRO")
            unreal.log("Zoo Tools PRO")

        except Exception as er:
            logger.error("Failed To load Zoo Tools PRO due to unknown Error",
                         exc_info=True)
            unreal.log("Failed to start Zoo Tools PRO\n{}".format(er))

    def shutdownEngine(self):
        """Implemented by derived class"""
        # delete the artist palette which will delete the zootools menu and shelf, windows etc.

        unreal.log("Unloading Zoo Tools PRO, please wait!")
        if not self.host.isHeadless:  # is in the maya UI
            from zoovendor.Qt import QtWidgets
            self.closeAllDialogs()
            try:
                logger.debug("Unloading Zoo Tools PRO")
                from zoo.apps.toolpalette import run
                run.close()
            except Exception:
                logger.error("Failed to shutdown currently loaded tools", exc_info=True)
            QtWidgets.QApplication.instance().quit()

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

        win = windowCls(**clsKwargs)

        self.registerDialog(name, win)
        if show:
            win.show()
        from zoo.libs.pyqt.widgets.frameless import window
        if isinstance(win, window.ZooWindow):
            logger.debug("ZooWindow instance detected, creating close signal connection to handle registry.")
            win.closed.connect(partial(self.closeDialog, name, win))
            unreal.parent_external_window_to_slate(win.parent().winId(),
                                                   unreal.SlateParentWindowSearchMethod.MAIN_WINDOW)
        else:
            unreal.parent_external_window_to_slate(win.winId(),
                                                   unreal.SlateParentWindowSearchMethod.MAIN_WINDOW)

        return win

    def _setupPyside(self):
        packageTargetFolder = self.configuration.sitePackagesPath()
        logger.info("Installing PySide6 for unreal to  location: {}".format(packageTargetFolder))
        requirements = packageresolver.parseRequirementsFile(filePath=os.path.join(os.path.dirname(__file__),
                                                                                   "requirements.txt")
                                                             )
        packageresolver.pipInstallRequirements(packageTargetFolder, self.host.pythonExecutable,
                                               requirements=requirements,
                                               upgrade=False)

    def _startQApp(self):
        """ Start the QApplication and bind to unreal tick event
        """
        from zoovendor.Qt import QtWidgets
        self.qApplication = QtWidgets.QApplication.instance()
        if not self.qApplication:
            # create the first instance
            logger.debug("Creating QApplication instance and setting up unreal tick callback")
            self.qApplication = QtWidgets.QApplication(sys.argv)
            self.qApplication.setQuitOnLastWindowClosed(False)
            self._tickHandle = unreal.register_slate_post_tick_callback(self._QtAppTick)
            self.qApplication.aboutToQuit.connect(self._QtAppQuit)

    def _QtAppTick(self, delta_seconds):
        from zoovendor.Qt import QtWidgets
        app = QtWidgets.QApplication.instance()
        if app:
            app.processEvents()

    def _QtAppQuit(self):
        logger.debug("Quitting QApplication, unregistering unreal tick callback")
        eng = engine.currentEngine()  # type: UnrealEngine
        unreal.unregister_slate_post_tick_callback(eng._tickHandle)
