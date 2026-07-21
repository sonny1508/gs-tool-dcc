# -*- coding: utf-8 -*-
"""
GSPipeline - launch chokepoint

Every GSPipeline menu item and shelf button routes through launch(), which
records the launch and then runs the tool. This mirrors what GSTools already
does via gstools.launch(), and gives GSPipeline the single instrumentation point
it previously lacked - GSPipeline.py used to bake a raw exec() string straight
into each menu item, so there was nowhere to hook.

Telemetry is delegated to gstools.telemetry, so there is exactly one sink,
one session id and one config story across both menus. If GSTools isn't
installed the import fails and launch() silently degrades to a plain dispatch.

Module name note: the GSPipeline folder goes onto sys.path flat (see
userSetup.py), so this must NOT be called launcher.py / telemetry.py or it
would shadow the GSTools modules of those names.
"""

import os

import maya.mel as mel

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Surface tag so GSPipeline launches stay distinguishable from GSTools ones in
# reports, even when both menus expose a tool of the same name.
SURFACE = "gspipeline"


def tool_id(script):
    """Stable id for a tool, derived from its script path.

    Uses the path rather than the display name so an id survives a rename in
    tool_config.py, which keeps historical data joinable.
    """
    stem = os.path.splitext(script.replace("\\", "/"))[0]
    return "gspipeline/" + stem.strip("/").lower()


def _log(script, name):
    """Record the launch. Never raises - a telemetry problem must not stop a
    tool from opening."""
    try:
        from gstools import telemetry
        telemetry.log_launch(
            tool_id(script),
            label=name,
            source="menu",
            surface=SURFACE,
            script=script,
        )
    except Exception:
        pass


def _dispatch(script):
    """Run the tool. Moved verbatim out of GSPipeline._build_command().

    Python files are run with __name__ == '__main__' so tools guarded by
    `if __name__ == "__main__":` fire, while tools that build their UI at
    module level also work. MEL files are sourced.
    """
    path = os.path.join(SCRIPT_DIR, script).replace("\\", "/")
    if path.lower().endswith(".mel"):
        return mel.eval('source "{0}";'.format(path))
    with open(path, encoding="utf-8") as handle:
        code = compile(handle.read(), path, "exec")
    exec(code, {"__name__": "__main__", "__file__": path})
    return None


def launch(script, name=None):
    """Record and run the tool at `script` (relative to this folder)."""
    _log(script, name or script)
    return _dispatch(script)
