import sys, os
from functools import partial

from zoo.apps.toolpalette import palette
from zoo.core.util import zlogging
from zoo.core.engine import currentEngine

logger = zlogging.getLogger(__name__)


class UnittestUI(palette.ActionPlugin):
    id = "zoo.unittest.ui"
    creator = "David Sparrow"
    tags = ["unittest", "test"]
    uiData = {"icon": "checkOnly",
              "tooltip": "Opens the Zootools Unittest UI",
              "label": "Unit Test UI",
              "color": "",
              "backgroundColor": "",
              }

    def execute(self, *args, **kwargs):
        from zoo.apps.unittestui import unittestui
        engine = currentEngine()
        return engine.showDialog(windowCls=unittestui.TestRunnerDialog,
                                 name="UnittestUI",
                                 allowsMultiple=False)


class SourceCodeEditor(palette.ActionPlugin):
    id = "zoo.sourceCodeEditor"
    creator = "David Sparrow"
    tags = ["script", "python", "code"]
    uiData = {"icon": "python",
              "tooltip": "Opens the Zootools Script Editor",
              "label": "Source Code Editor",
              "multipleTools": False,
              "frameless": {"frameless": True, "force": False},
              }

    def execute(self, *args, **kwargs):
        from zoo.apps.sourcecodeeditor import editorui
        engine = currentEngine()
        return engine.showDialog(windowCls=editorui.SourceCodeUI,
                                 name="SourceCodeEditorUI",
                                 allowsMultiple=False)


class PyCharmDebugger(palette.ActionPlugin):
    """
    The PyCharmDebugger class prompts the user for a port number, creates a PyCharm debugger connection,
    and logs the connection status.

    ..note: This requires pycharm Professional edition and for a debug server to be active.
    """
    id = "pycharm.debug"
    creator = "David Sparrow"
    tags = ["pycharm", "debug"]
    uiData = {"icon": "pycharm",
              "tooltip": "Connects to port 9001 pycharm remote debugger.\nUse Env var 'PYCHARM_PORT' to override to port",
              "label": "Connect to PyCharm debugger",
              "color": "",
              "backgroundColor": "",
              }

    def execute(self, *args, **kwargs):
        from zoo.libs.pyqt.widgets import elements
        from zoo.core import engine

        win = engine.currentEngine().showDialog(elements.InputDialog,
                                                name="PycharmDebug",
                                                show=False,
                                                allowsMultiple=False,
                                                title="Pycharm Debug", message="Debug Port Number:",
                                                text=os.getenv("PYCHARM_PORT", "9001"), buttonA="OK",
                                                buttonB="Cancel"
                                                )
        win.closed.connect(partial(self._onClose, win))
        win.show()

    def _onClose(self, window):
        if window.result == "A":
            os.environ["PYCHARM_PORT"] = str(window.inputText())
            self._connect()

    def _connect(self):
        # This should be the path your PyCharm installation
        pydevdEgg = os.path.expanduser(os.path.expandvars(os.getenv("PYCHARM_EGG", "")))
        pydevdPort = os.getenv("PYCHARM_PORT", "9001")
        try:
            pydevdPort = int(pydevdPort)
        except ValueError:
            logger.error("Invalid Port Number: {}".format(pydevdPort))
            return
        if not os.path.isdir(pydevdEgg):
            logger.error("Pycharm folder doesn't exist: {}".format(pydevdEgg))
            return
        if pydevdEgg not in sys.path:
            sys.path.append(pydevdEgg)

        import pydevd
        # This clears out any previous connection in case you restarted the debugger from PyCharm
        pydevd.stoptrace()
        try:
            # 9001 matches the port number that I specified in my configuration
            pydevd.settrace('localhost', port=pydevdPort, stdoutToServer=True, stderrToServer=True, suspend=False)
            logger.info("Connected to Pycharm on Port: {}".format(pydevdPort))
        except ConnectionRefusedError:
            logger.error("Unable to connect Pycharm on port: {}".format(pydevdPort))

    def teardown(self):
        try:
            import pydevd
            # This clears out any previous connection in case you restarted the debugger from PyCharm
            pydevd.stoptrace()

        except ImportError:
            # case we're the library hasn't been imported yet
            pass
