from zoo.libs.maya.mayacommand import command
from zoo.libs.hive import api


class UpdateConfiguration(command.ZooCommandMaya):
    """Updates a set of rig configuration settings.
    """
    id = "hive.configuration.update"
    
    isUndoable = True
    isEnabled = True
    _rig = None
    _settings = {}
    _originalSettings = {}

    def resolveArguments(self, arguments):
        rig = arguments.get("rig")

        if rig is None or not isinstance(rig, api.Rig):
            self.displayWarning("Must supply the rig instance to the command")
            return
        self._rig = rig
        self._settings = arguments["settings"]
        return arguments

    def doIt(self, rig=None, settings=None):
        """

        :param rig: The rig instance to modify
        :type rig: :class:`api.Rig`
        :param settings: The configuration setting name and value.
        :type settings: dict[str, value]
        :return: True when successful.
        :rtype: bool
        """
        originalConfig = self._rig.cachedConfiguration()
        if not originalConfig:
            originalConfig = self._rig.configuration.serialize()
        self._rig.configuration.applySettingsState(self._settings, rig=self._rig)
        self._originalSettings = originalConfig
        self._rig.saveConfiguration()
        return True

    def undoIt(self):
        if self._rig.exists():
            self._rig.configuration.applySettingsState(self._originalSettings)
            self._rig.saveConfiguration()
