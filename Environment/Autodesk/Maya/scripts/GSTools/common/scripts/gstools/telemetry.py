"""
GSTools - Telemetry

Single chokepoint for "a tool was launched" events. Every GSTools menu item and
shelf button is dispatched through gstools.launch(), which calls log_launch()
here. That makes this the ONE place to wire up external/remote logging later -
no tool or menu_config change will be required.

Current behaviour: writes a local line (Script Editor + optional local log file).
FUTURE: replace the body of _emit() with the real external sink (network share,
HTTP endpoint, database, ...). Keep it wrapped so a telemetry failure can never
break a tool launch.
"""
import os
import sys
import getpass
import datetime
import logging

logging.basicConfig()
logger = logging.getLogger("gstools.telemetry")
logger.setLevel(logging.INFO)

# Toggle local file logging. The external sink is intentionally not implemented
# yet - see module docstring.
WRITE_LOCAL_LOG = False
_LOCAL_LOG_NAME = "gstools_usage.log"


def _local_log_path():
    """Return a path for the optional local usage log (next to this package)."""
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), _LOCAL_LOG_NAME)


def _maya_version():
    try:
        import maya.cmds as cmds
        return cmds.about(version=True)
    except Exception:
        return "unknown"


def _emit(event):
    """
    Send a telemetry event. `event` is a plain dict.

    FUTURE: this is the only function to change when wiring up the external
    logging destination. Today it just prints and (optionally) appends locally.
    """
    line = "[GSTools] {ts} | {tool} | src={source} | user={user} | maya={maya}".format(**event)
    print(line)

    if WRITE_LOCAL_LOG:
        try:
            with open(_local_log_path(), "a") as fh:
                fh.write(line + "\n")
        except Exception as exc:
            logger.debug("local telemetry write failed: %s", exc)


def log_launch(tool_id, label=None, source="menu", **extra):
    """
    Record that a tool was launched. Never raises - telemetry must not be able
    to block a tool from running.

    Args:
        tool_id (str): stable id of the tool from menu_config.
        label (str): human label, if known.
        source (str): "menu", "shelf", or other surface that triggered it.
        **extra: any additional context to record.
    """
    try:
        event = {
            "ts": datetime.datetime.now().isoformat(timespec="seconds"),
            "tool": tool_id,
            "label": label or tool_id,
            "source": source,
            "user": getpass.getuser(),
            "maya": _maya_version(),
            "py": "%d.%d" % (sys.version_info[0], sys.version_info[1]),
        }
        event.update(extra)
        _emit(event)
    except Exception as exc:
        logger.debug("telemetry log_launch failed: %s", exc)
