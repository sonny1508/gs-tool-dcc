"""
GSTools - Launcher / dispatcher

Every menu item and shelf button runs through launch(tool_id). This is where:
  1. the tool is resolved from menu_config (single source of truth),
  2. telemetry is recorded (telemetry.log_launch),
  3. the tool is actually executed, dispatched by its "type".

Supported tool types (see menu_config):
  - "python"      import `module`, reload it, call `function`() if given
                  (if `function` is None the module body itself is the action).
  - "mel"         eval the raw `command` MEL (proc already on the script path).
  - "mel_source"  source the file at `source` (relative to the scripts root, which
                  is on MAYA_SCRIPT_PATH) then eval `command` if given.
  - "special"     built-in actions: about / rebuild / version.
"""
import importlib
import logging

import maya.cmds as cmds
import maya.mel as mel

from gstools import menu_config
from gstools import telemetry

logging.basicConfig()
logger = logging.getLogger("gstools.launcher")
logger.setLevel(logging.INFO)


def launch(tool_id, source="menu"):
    """
    Resolve, record, and run the tool registered under `tool_id`.

    Args:
        tool_id (str): id from menu_config.
        source (str): surface that triggered it ("menu" / "shelf").

    Returns:
        Whatever the dispatched tool returns, or None.
    """
    tool = menu_config.get_tool(tool_id)
    if tool is None:
        cmds.warning("GSTools: unknown tool id '%s'" % tool_id)
        return None

    telemetry.log_launch(tool_id, label=tool.get("label"), source=source)

    ttype = tool.get("type")
    try:
        if ttype == "python":
            return _run_python(tool)
        if ttype == "mel":
            return mel.eval(tool["command"])
        if ttype == "mel_source":
            return _run_mel_source(tool)
        if ttype == "special":
            return _run_special(tool)
        cmds.warning("GSTools: tool '%s' has unknown type '%s'" % (tool_id, ttype))
    except Exception as exc:
        logger.warning("Tool '%s' failed: %s", tool_id, exc)
        cmds.warning("GSTools: '%s' failed - see Script Editor." % tool.get("label", tool_id))
        raise
    return None


def _run_python(tool):
    name = tool["module"]
    module = importlib.import_module(name)
    importlib.reload(module)
    # Older cmds-based tools build UIs with string callbacks like
    # "MyModule.someFunc()" that Maya evaluates in __main__. The old menu ran
    # `import MyModule` in __main__, so bind the module there too to preserve that.
    import __main__
    setattr(__main__, name, module)
    function = tool.get("function")
    if not function:
        # No entry function: importing/reloading the module is the action.
        return None
    return getattr(module, function)()


def _run_mel_source(tool):
    src = tool["source"]
    command = tool.get("command", "")
    # Scripts root is on MAYA_SCRIPT_PATH, so a relative source path resolves.
    mel.eval('source "%s";' % src)
    if command:
        return mel.eval(command)
    return None


def _run_special(tool):
    action = tool.get("action")
    if action == "rebuild":
        from gstools import menu_builder
        importlib.reload(menu_config)
        importlib.reload(menu_builder)
        return menu_builder.build_menu()
    if action == "about":
        import gs_maya_utilities
        importlib.reload(gs_maya_utilities)
        return gs_maya_utilities.build_gui_about_gs_tools()
    if action == "version":
        return None
    cmds.warning("GSTools: unknown special action '%s'" % action)
    return None
