from zoo.libs.utils import unittestBase
from zoo.apps.toolpalette import run
from zoo.apps.toolpalette import default_actions
from zoo.apps.toolpalette import palette
from zoo.core.util import zlogging

try:
    from unittest import mock
except ImportError:
    from zoovendor import mock


class TestDefaultActions(unittestBase.BaseUnitest):

    def setUp(self):
        self.instance = run.currentInstance()
        if self.instance is None:
            self.instance = run.load()

    def test_loadsDefaultActions(self):
        actions = self.instance.typeRegistry.getPlugin("action")  # type: palette.ActionType
        plugins = list(actions.plugins())
        self.assertTrue(default_actions.ToggleZooLogging.id in plugins)
        self.assertTrue(default_actions.HelpIconShelf.id in plugins)
        self.assertTrue(default_actions.ResetAllWindowPosition.id in plugins)

    def test_helpCallsWebBrowser(self):

        for variant in default_actions.HelpIconShelf._ADDRESSES:
            with mock.patch("webbrowser.open") as mockwbopen:
                self.instance.executePluginById(default_actions.HelpIconShelf.id, variant=variant)
                self.assertTrue(mockwbopen.called)

    def test_loggingTogglesDebugMode(self):
        """Tests the toggling of debug logging through the action works.
        """
        zlogging.setGlobalDebug(False)  # actual core test is in zooTools main repo
        self.instance.executePluginById(default_actions.ToggleZooLogging.id)
        self.assertTrue(zlogging.isGlobalDebug())
        self.instance.executePluginById(default_actions.ToggleZooLogging.id)
        self.assertFalse(zlogging.isGlobalDebug())
