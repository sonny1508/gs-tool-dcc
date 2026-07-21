"""
GSTools - Maya tool suite (data-driven menu + shelf).

Public entry points (called from GSTools.mel and shelf_GSTools.mel):
    gstools.build_menu()        build/rebuild the GSTools menu
    gstools.launch(id, source)  run a tool by id (telemetry chokepoint)
    gstools.reload_package()    drop gstools.* from sys.modules for a clean reload

Layout (under .../GSTools/common/scripts):
    gstools/    this core package (config, builder, launcher, telemetry, utils)
    tools/      in-house tools grouped by discipline
    vendor/     third-party tools kept as-is
ensure_paths() puts the scripts root + every tools/* and vendor/* subfolder on
sys.path so tool modules import by their plain name regardless of where they live.
"""
import os
import sys
import importlib
import logging

PACKAGE_VERSION = "2.0.0"

logging.basicConfig()
logger = logging.getLogger("gstools")
logger.setLevel(logging.INFO)

_PKG_DIR = os.path.dirname(__file__)                 # .../scripts/gstools
SCRIPTS_ROOT = os.path.dirname(_PKG_DIR)             # .../scripts


def _tool_dirs():
    """The scripts root, this package, and every tools/*, vendor/*, operations/* dir."""
    dirs = [SCRIPTS_ROOT, _PKG_DIR]
    for base in ("tools", "vendor", "operations"):
        base_dir = os.path.join(SCRIPTS_ROOT, base)
        if not os.path.isdir(base_dir):
            continue
        dirs.append(base_dir)
        for name in sorted(os.listdir(base_dir)):
            sub = os.path.join(base_dir, name)
            if os.path.isdir(sub):
                dirs.append(sub)
    return dirs


def _ensure_mel_script_path(dirs):
    """Add `dirs` to Maya's MAYA_SCRIPT_PATH so MEL `source "x.mel"` (including the
    relative source statements *inside* tool MEL files, e.g. CreasePlus sourcing its
    extension) and proc auto-sourcing resolve. No-op outside Maya."""
    try:
        import maya.mel as mel
    except Exception:
        return
    current = mel.eval('getenv "MAYA_SCRIPT_PATH"') or ""
    parts = current.split(os.pathsep)
    add = [d for d in dirs if d not in parts]
    if not add:
        return
    new_value = (current + os.pathsep if current else "") + os.pathsep.join(add)
    # forward slashes keep the MEL string literal clean on Windows
    mel.eval('putenv "MAYA_SCRIPT_PATH" "%s";' % new_value.replace("\\", "/"))


def ensure_paths():
    """Put the scripts root + tool folders on sys.path (Python) and MAYA_SCRIPT_PATH (MEL)."""
    dirs = _tool_dirs()
    for path in dirs:
        if path not in sys.path:
            sys.path.insert(0, path)
    _ensure_mel_script_path(dirs)


def build_menu():
    """Build/rebuild the GSTools menu."""
    ensure_paths()
    from gstools import menu_builder
    importlib.reload(menu_builder)
    return menu_builder.build_menu()


def launch(tool_id, source="menu"):
    """Run a tool by id. Single dispatch + telemetry chokepoint."""
    ensure_paths()
    from gstools import launcher
    return launcher.launch(tool_id, source=source)


def run_startup():
    """Register the startup extras (standalone menus + hotkey operations).
    Each piece is isolated so one failure can't abort the others."""
    ensure_paths()
    from gstools import startup
    importlib.reload(startup)
    return startup.run()


def start_session():
    """Open the telemetry session for this Maya process.

    A no-op (and thread-free, socket-free) unless GS_TELEMETRY_URL is set, so
    this costs nothing outside the studio. Isolated in its own try/except: usage
    reporting must never be able to stop Maya from booting the tools.
    """
    try:
        from gstools import telemetry
        telemetry.session_start()
        _register_quit_hook(telemetry)
    except Exception as exc:
        logger.debug("telemetry session_start failed: %s", exc)


def _register_quit_hook(telemetry):
    """Flush telemetry when Maya quits.

    telemetry.session_start() already registers an atexit handler; this adds
    Maya's own quitApplication event as a belt-and-braces second trigger, since
    atexit does not always run on every Maya shutdown path. _on_exit() guards
    against running twice.
    """
    try:
        import maya.cmds as cmds
        cmds.scriptJob(event=["quitApplication", telemetry._on_exit], protected=True)
    except Exception as exc:
        logger.debug("telemetry quit hook not registered: %s", exc)


def boot():
    """Full GSTools boot: open the telemetry session, build the menu, then
    register startup extras. This is what GSTools.mel calls at Maya startup."""
    start_session()
    build_menu()
    run_startup()


def execute_script(import_name, entry_point_function, reload=True):
    """
    Backwards-compatible helper: import `import_name`, optionally reload, then call
    `entry_point_function`(). Retained for any tool/code still calling it.
    """
    ensure_paths()
    try:
        module = importlib.import_module(import_name)
        if reload:
            importlib.reload(module)
    except Exception as exc:
        logger.warning('"%s" could not be imported: %s', import_name, exc)
        raise
    return getattr(module, entry_point_function)()


def reload_package():
    """Unload gstools.* modules so they are re-imported fresh on next use."""
    ensure_paths()
    from gstools import gs_utilities
    gs_utilities.unload_packages(silent=False, packages=["gstools"])


# Make tool folders importable as soon as the package is imported.
ensure_paths()
