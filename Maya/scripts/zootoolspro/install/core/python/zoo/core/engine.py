import sys
from zoo.core.util import zlogging


logger = zlogging.getLogger(__name__)


class HostApplication(object):
    """Simple class for containing the current Host application information.
    Meant to be derived for the Host specifically.

    :param name: The name of the host application.
    :type name: str
    :param version: The version of the host application.
    :type version: str
    :param versionYear: The version year of the host application.
    :type versionYear: int
    """

    def __init__(self, name, version, versionYear):
        self.name = name
        self.version = version
        self.versionYear = versionYear

    @property
    def executable(self):
        """The executable path of the host application.

        :return: The executable path.
        :rtype: str
        """
        return sys.executable

    @property
    def installLocation(self):
        """The installation location of the host application.

        :return: The installation location.
        :rtype: str
        """
        raise NotImplementedError()

    @property
    def isHeadless(self):
        """Checks if the host application is running in headless mode.

        :return: True if headless, False otherwise.
        :rtype: bool
        """
        return False

    @property
    def qtMainWindow(self):
        """Returns the main window of the host application.

        :return: The main window.
        :rtype: QMainWindow
        """
        raise NotImplementedError()

    @property
    def pythonExecutable(self):
        """The path of the Python executable used by the host application.

        :return: The Python executable path.
        :rtype: str
        """
        return self.executable


class Engine(object):
    """Base class for a host engine.

    When a DCC integration is created it should derive from this base class and reimplement the required methods.
    It's designed to load zootools in a DCC specific way,
    loading menus, shelf, callback management, launching dialogs (docking, etc.), retrieve host information (version).
    The usersetup.py (maya, houdini), blender addon, maya plugin would create the specific engine by name.

    :param configuration: The configuration object.
    :type configuration: Configuration
    :param engineName: The name of the engine.
    :type engineName: str
    """

    def __init__(self, configuration, engineName):
        self.configuration = configuration
        self.engineName = engineName
        self._host = None
        self._dialogs = {}  # str, list[QtWidget]
        self._initialized = False

    def init(self):
        """Initializes the engine. Called immediately after the engine is created.
        """
        if self._initialized:
            return
        self.configuration.resolver.callbacks.setdefault("preStartupCommands", []).append(self._preStartupCommandsCallback)
        logger.debug("Running post init initialization")
        self.postInit()
        # todo: run pre engine initialization plugin which is global plugin living in config/plugins/core
        logger.debug("Running pre environment Init engine initialization")
        self.preEnvInit()
        self.configuration.resolver.resolveFromPath(self.configuration.resolver.environmentPath())
        # todo: load the zootools environment ie. packages
        logger.debug("Running post environment engine initialization")
        self.postEnvInit()
        # todo: run post engine initialization plugin which is global living in config/plugins/core
        self._initialized = True

    def _preStartupCommandsCallback(self):
        """Internal use only. Called by the configuration resolver before the startup commands for the
        packages are called.
        """
        from zoo.preferences import core
        core.setInstance(core.PreferenceManager(self.configuration))

    @property
    def initialized(self):
        """Checks if the engine has been initialized.

        :return: True if initialized, False otherwise.
        :rtype: bool
        """
        return self._initialized

    @property
    def host(self):
        """Returns the current host application information.

        :return: The host application information.
        :rtype: :class:`HostApplication`
        """
        return self._host

    def postInit(self):
        """Post-initialization method. called after the engine has been created but before any packages have been setup.
        """
        pass

    def preEnvInit(self):
        """Before any packages have been set up but after postInit.

        Implemented by derived class
        """
        pass

    def postEnvInit(self):
        """After all packages and package command scripts have been initialized.

        Implemented by derived class
        """
        pass

    def shutdownEngine(self):
        """Shuts down the engine.

        Implemented by derived class
        """
        pass

    def showDialog(self, windowCls, name="", show=True, allowsMultiple=False, *clsArgs, **clsKwargs):
        """Shows a dialog window.

        :param windowCls: The class of the dialog window.
        :type windowCls: type
        :param name: The name of the dialog.
        :type name: str
        :param show: Flag indicating whether to show the dialog.
        :type show: bool
        :param allowsMultiple: Flag indicating whether multiple instances of the dialog are allowed.
        :type allowsMultiple: bool
        :param clsArgs: Additional arguments to pass to the dialog class constructor.
        :type clsArgs: tuple
        :param clsKwargs: Additional keyword arguments to pass to the dialog class constructor.
        :type clsKwargs: dict
        """
        pass

    def closeDialog(self, name, widget):
        """Closes a dialog window.

        :param name: The name of the dialog.
        :type name: str
        :param widget: The widget of the dialog to close.
        :type widget: QWidget
        """
        self.unregisterDialog(name, widget)
        widget.deleteLater()

    def closeAllDialogs(self):
        """Closes all registered dialog windows.
        """
        for dialogInstances in self._dialogs.values():
            for instance in dialogInstances:
                instance.close()
                instance.deleteLater()

        self._dialogs = {}

    def registerDialog(self, name, dialog):
        """Registers a dialog window.

        :param name: The name of the dialog.
        :type name: str
        :param dialog: The dialog window to register.
        :type dialog: QWidget
        """
        logger.debug("Registering dialog instance: {}".format(name, dialog))
        self._dialogs.setdefault(name, []).append(dialog)

    def unregisterDialog(self, name, dialog):
        """Unregisters a dialog window.

        :param name: The name of the dialog.
        :type name: str
        :param dialog: The dialog window to unregister.
        :type dialog: QWidget
        """
        logger.debug("Unregistering dialog instance: {}".format(name, dialog))
        widgets = []
        for win in self._dialogs.get(name, []):
            if win != dialog:
                widgets.append(win)
        self._dialogs[name] = widgets

    def dialogsByName(self, name):
        """Returns all dialogs which have been registered with the given name.

        :param name: The name of the registered dialog
        :type name: str
        :return: A list of Dialogs, windows, zoo windows which match the  registered name
        :rtype: list[:class:`QtWidgets.QMainWindow`]
        """
        return self._dialogs.get(name, [])

    def setStyleSheet(self, style):
        """Sets the style sheet for all registered dialogs.

        :param style: The style sheet to apply.
        :type style: str
        """
        for dialogInstances in self._dialogs.values():
            for dialogInstance in dialogInstances:
                try:
                    dialogInstance.setStyleSheet(style)
                except AttributeError:
                    logger.error("Dialog instance missing 'setStyleSheet method'")


def currentEngine():
    """Retrieves the current engine.

    :return: The current engine.
    :rtype: :class:`Engine`
    """
    global _currentEngine
    return _currentEngine


def setCurrentEngine(engine):
    """Sets the current engine.

    :param engine: The engine to set as current.
    :type engine: Engine
    """
    global _currentEngine
    _currentEngine = engine


def startEngine(config, engineCls, engineName):
    """Starts the engine.

    :param config: The configuration object.
    :type config: Configuration
    :param engineCls: The engine class.
    :type engineCls: type
    :param engineName: The name of the engine.
    :type engineName: str
    :return: The initialized engine.
    :rtype: Engine
"""
    logger.info("Loading Zoo Tools PRO, please wait!")
    engineCls = engineCls(config, engineName)
    setCurrentEngine(engineCls)
    engineCls.init()
    return engineCls


def shutdownEngine():
    """Shuts down the current engine.
    """
    eng = currentEngine()
    eng.shutdownEngine()
    setCurrentEngine(None)
