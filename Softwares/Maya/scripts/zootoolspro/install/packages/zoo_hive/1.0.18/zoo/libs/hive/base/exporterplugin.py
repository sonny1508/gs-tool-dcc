"""This module contains the base exporter plugin for hive which is used to export all
I/O operations related to assets ie. templates, FBX, .ma reference etc.
"""
import logging

from zoo.core.plugin import plugin
from zoo.core.util import zlogging

logger = zlogging.getLogger(__name__)


def _dummyCallback(progress, message):
    """Default dummy progress callback which just logs to debug.

    :param progress: The current progress to output
    :type progress: int
    :param message: The user message for the progress value.
    :type message: str
    """
    logger.debug("Progress: {}, reason: {}".format(progress, message))


class ExporterPlugin(object):
    """Plugin Interface for handling exporting of hive rigs ie. fbx and MA.
    It's the responsibility of subclasses to reimplement the following methods.

        * :func:`ExporterPlugin.exportSettings`
        * :func:`ExporterPlugin.execute`

    To Broadcast progress of the export you should call self.onProgressCallbackFunc(progress, message)
    If this plugin is being executed from the UI then the callback will be handled from there.
    However, if you're executing the plugin through code only or writing your own UI then
    you can set the callback using  myPlugin.onProgressCallbackFunc = myProgressFuncPointer.

    By default, the progress callback will simply log to debug.

    .. code-block:: python

        from zoo.libs.hive import api
        r = api.Rig()
        r.startSession("myRig")
        exporter = r.configuration.exportPluginForId("fbxExport")()
        settings = exporter.exportSettings()
        settings.outputPath = "myfbxPath.fbx"
        exporter.execute(settings)

    """
    # uuid for this plugin which we be registered in the plugin system and referenced by clients.
    id = ""

    def __init__(self):
        self.onProgressCallbackFunc = _dummyCallback  # type callable

    def exportSettings(self):
        """Method which returns the export settings instance which will be used in execute()
        """
        raise NotImplementedError("Subclasses Should implement this method")

    def execute(self, rig, exportOptions):
        """Client facing method which runs the export process.

        :param rig: The Hive rig instance to export
        :type rig: :class:`zoo.libs.hive.base.rig.Rig`
        :param exportOptions: The export options for this exporter to use.
        :type exportOptions: :class:`zoo.libs.utils.general.ObjectDict`
        """
        self.onProgressCallbackFunc(0, "Starting Export Process")
        try:
            self.export(rig, exportOptions)
        finally:
            self.onProgressCallbackFunc(100, "Finished ExportProcess")

    def export(self, rig, exportOptions):
        """Should be implemented in subclass. This is where all export logic should be contained

        :param rig: The Hive rig instance to export
        :type rig: :class:`zoo.libs.hive.base.rig.Rig`
        :param exportOptions: The export options for this exporter to use.
        :type exportOptions: :class:`zoo.libs.utils.general.ObjectDict`
        """
        raise NotImplementedError()

    def showUserMessage(self, title, messageType, message):
        from zoo.libs.pyqt.widgets import elements
        if messageType == logging.INFO:
            elements.MessageBox.showOK(title=title, parent=None, message=message, icon="",
                                       default=0, buttonA="OK", buttonB=None)
        elif messageType == logging.WARNING:
            elements.MessageBox.showWarning(title=title, parent=None, message=message,
                                            default=0, buttonA="OK", buttonB=None)
        else:
            elements.MessageBox.showCritical(title=title, parent=None, message=message,
                                             default=0, buttonA="OK", buttonB=None)
