import os, sys
import shutil

from zoo.apps.toolpalette import palette
from zoo.core.util import zlogging, version
from zoo.core import api
from zoo.core import packageresolver
from zoo.core import engine

from zoo.libs.pyqt.widgets import elements
from zoo.libs.utils import output
from zoo.libs.pyqt import utils
from zoo.apps.chatgptui import constants, installdialog

logger = zlogging.getLogger(__name__)


class ChatGPT(palette.ActionPlugin):
    id = "zoo.chatgpt.ui"
    creator = "David Sparrow"
    tags = ["OpenAI", "AI", "Chat"]
    uiData = {
        "icon": "chatGPT_shlf",
        "tooltip": "Zoo Chat GPT: \nOpens the Zoo Chat GPT Window",
        "label": "Zoo Chat GPT",
    }

    def execute(self, *args, **kwargs):

        if sys.version_info[0] < 3:
            output.displayError("Chat GPT only supports Python3 (maya2022+)")
            return
        currentEngine = engine.currentEngine()
        if not self._checkInstallation():
            installed = self._installDependenciesDialog(currentEngine, upgrade=True)
            if not installed:
                output.displayInfo(
                    "Operation Cancelled: OpenAI Python Library was not installed."
                )
            return
        import openai
        from zoo.apps.chatgptui import chatgptwin, utils as chatGptutils

        # validate the api key and show the dialog if it's not valid, dialog handles validation from the user input
        chatGptutils.setApiKeyIfFound()
        if not chatGptutils.hasApiKey() or not chatGptutils.validateKey(openai.api_key):
            win = currentEngine.showDialog(
                chatgptwin.ApiKeyDialog, "zoo.chatgpt.apikey", show=True, modal=True
            )

            while win.msgClosed is False:
                utils.processUIEvents()
            if not win.result:
                return
            chatGptutils.setAPIkey(win.result)
        win = currentEngine.showDialog(
            chatgptwin.ChatGPTWindow, "zoo.chatgpt.ui", show=True
        )

        return win

    def restartHostDialog(self, currentEngine):
        """

        :param parent:
        :type parent:
        :param currentEngine:
        :type currentEngine: :class:`zoo.core.engine.Engine`
        :return:
        :rtype:
        """
        message = constants.RESTART_HOST_MESSAGE.format(
            api.currentConfig().cacheFolderPath(), currentEngine.host.name
        )
        _showDialog(currentEngine,
                    title="Zoo Chat GPT Installed",
                    message=message,
                    buttonA="Close Window",
                    buttonB=None,
                    icon="Info"
                    )

    def _installDependenciesDialog(self, currentEngine, upgrade=False):
        m = currentEngine.showDialog(
            installdialog.InstallDialog, "zoo.chatgpt.install", show=True, modal=True
        )
        while m.msgClosed is False:
            utils.processUIEvents()
        if not m.result:
            return False
        # Install -----
        message = "Installing OpenAI Python Library, please wait..."
        pipArguments = ["-v"]
        if upgrade:
            message = "Upgrading OpenAI Python Library, please wait..."
            pipArguments.append("--force-reinstall")
        output.displayInfo(message)
        cfg = api.currentConfig()
        pkg = cfg.resolver.packageByName("zoo_chatgpt")
        pkg.runInstall()
        if pkg.pipRequirements:
            installed = self._installDependencies(
                cfg, pkg.pipRequirements, upgrade=upgrade
            )
        else:
            requirements = packageresolver.parseRequirementsFile(
                pkg.pipRequirementsPath
            )
            pkg.pipRequirements = requirements
            installed = self._installDependencies(cfg, requirements, upgrade=upgrade)
        if installed:
            self.restartHostDialog(currentEngine)
            output.displayInfo(
                "OpenAI Python Library has been installed, Please restart {}.".format(currentEngine.host.name)
            )
            return True
        return False

    def _installDependencies(self, cfg, requirements, upgrade=False, pipArguments=None):
        hostInfo =engine.currentEngine().host
        exe = engine.currentEngine().host.pythonExecutable
        if not os.path.exists(exe):
            output.displayError("{} executable not found: {}".format(hostInfo.name, exe))
            return False
        packageresolver.pipInstallRequirements(
            cfg.sitePackagesPath(),
            exe,
            requirements,
            upgrade=upgrade,
            pipArguments=pipArguments,
        )
        return True

    def _checkInstallation(self):
        try:
            from openai import version as openaiversion

            if openaiversion.VERSION:
                lVersion = version.LooseVersion(openaiversion.VERSION)
                if lVersion < version.LooseVersion(constants.OPENAI_VERSION):
                    return False
            return True
        except ImportError:
            return False


class UninstallChatGPT(palette.ActionPlugin):
    id = "zoo.uninstallChatGpt"
    creator = "David Sparrow"
    tags = ["OpenAI", "AI", "Chat"]
    uiData = {
        "icon": "chatGPTSimple",
        "tooltip": "Uninstalls Chat GPT and its dependencies",
        "label": "Uninstall Chat GPT",
        "multipleTools": False,
    }

    def execute(self, *args, **kwargs):
        cfg = api.currentConfig()
        cacheFolder = cfg.cacheFolderPath()
        if not os.path.exists(cacheFolder):
            output.displayInfo("Chat GPT is not installed, skipping uninstall.")
            return
        currentEngine = engine.currentEngine()
        result = _showDialog(currentEngine,
            title="Uninstall Chat GPT",
            message="Are you sure you want to "
                    "uninstall Chat GPT and its "
                    "dependencies?",
            buttonA="uninstall",
        )
        if result != "A":
            return
        cfg = api.currentConfig()
        pkg = cfg.resolver.packageByName("zoo_chatgpt")
        pkg.runUninstall()
        logger.info("Deleting cache folder: {}".format(cacheFolder))
        try:
            shutil.rmtree(cacheFolder)
        except (PermissionError, OSError):
            output.displayWarning(
                "Unable to delete cache folder due to permissions, "
                "please manually delete folder: {}. Close {} before deleting.".format(
                    cacheFolder, currentEngine.host.name
                )
            )
            return
        output.displayInfo("Chat GPT has been uninstalled, Please restart {}.".format(currentEngine.host.name))


def _showDialog(
        currentEngine,
        title="",
        message="",
        buttonA="Continue",
        buttonB="Cancel",
        buttonC=None,
        buttonIconA=elements.MessageBoxBase.okIcon,
        buttonIconB=elements.MessageBoxBase.cancelIcon,
        buttonIconC=None,
        icon="Question",
        default=0,
):
    """

    :param currentEngine:
    :type currentEngine: :class:`zoo.core.engine.Engine`
    """
    win = currentEngine.showDialog(
        elements.MessageBoxBase,
        show=True,
        allowsMultiple=False,
        title=title,
        message=message,
        buttonA=buttonA,
        buttonB=buttonB,
        buttonC=buttonC,
        buttonIconA=buttonIconA,
        buttonIconB=buttonIconB,
        buttonIconC=buttonIconC,
        icon=icon,
        default=default,
    )
    while win.msgClosed is False:
        utils.processUIEvents()

    return win.result
