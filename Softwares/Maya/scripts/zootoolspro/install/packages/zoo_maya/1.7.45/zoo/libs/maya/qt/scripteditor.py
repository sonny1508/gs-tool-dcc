from maya import cmds


class ScriptEditorState(object):
    """Provides methods to suppress and restore script editor output."""

    # Used to restore logging states in the script editor
    suppress_results = None
    suppress_errors = None
    suppress_warnings = None
    suppress_info = None

    @classmethod
    def suppress_output(cls):
        """Hides all script editor output."""
        cls.suppress_results = cmds.scriptEditorInfo(q=True, suppressResults=True)
        cls.suppress_errors = cmds.scriptEditorInfo(q=True, suppressErrors=True)
        cls.suppress_warnings = cmds.scriptEditorInfo(q=True, suppressWarnings=True)
        cls.suppress_info = cmds.scriptEditorInfo(q=True, suppressInfo=True)
        cmds.scriptEditorInfo(e=True,
                              suppressResults=True,
                              suppressInfo=True,
                              suppressWarnings=True,
                              suppressErrors=True)

    @classmethod
    def restore_output(cls):
        """Restores the script editor output settings to their original values."""
        if None not in {cls.suppress_results, cls.suppress_errors, cls.suppress_warnings, cls.suppress_info}:
            cmds.scriptEditorInfo(e=True,
                                  suppressResults=cls.suppress_results,
                                  suppressInfo=cls.suppress_info,
                                  suppressWarnings=cls.suppress_warnings,
                                  suppressErrors=cls.suppress_errors)
