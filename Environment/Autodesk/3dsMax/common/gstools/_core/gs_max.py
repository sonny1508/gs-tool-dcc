# -*- coding: utf-8 -*-
"""
gs_max - helpers shared by the GSTools Python tools in 3ds Max.

Lives in the version-less common tree, so it runs on every Max version the
studio deploys: Python 3.9 (2023) to 3.13 (2027), PySide2 or PySide6. pymxs
and qtmax are imported inside the functions that use them, so the module
also imports outside Max.

A tool in common/gstools reaches it by putting _core on sys.path, and ends
with the launch line:

    import gs_max
    QtWidgets, QtCore, QtGui = gs_max.qt_modules()
    ...
    if __name__ == "__main__":
        gs_max.launch(__file__)
"""
import importlib.util
import json
import os
import sys


# ---------------------------------------------------------------------------
# Qt and launching
# ---------------------------------------------------------------------------
def qt_modules():
    """
    (QtWidgets, QtCore, QtGui) of the Qt binding this Max runs.

    Picked by Max version, not by what imports: a stray PySide6 can be
    importable in Max 2023, and a PySide6 window parented to that Max's
    PySide2 main window crashes. The Python version tracks the Max version:
    2025+ ships 3.11+ with PySide6, 2023 ships 3.9 with PySide2.
    """
    if sys.version_info >= (3, 11):
        from PySide6 import QtCore, QtGui, QtWidgets
    else:
        from PySide2 import QtCore, QtGui, QtWidgets
    return QtWidgets, QtCore, QtGui


def main_window():
    """The Max main window, to parent tool windows to."""
    import qtmax
    return qtmax.GetQMaxMainWindow()


def launch(path):
    """
    Call show() in the tool file at `path`, loaded as a module of its own.

    A tool's macro runs its file with python.ExecuteFile, which executes it in
    Max's __main__: one namespace shared by every file run that way. A window
    running from there looks its functions up in that namespace, where a tool
    opened later can replace them with its own of the same name (Scene Checker
    and HW3 Tools already share several). Loading the file again as a module
    keeps the window on its own code, and fresh each launch, so a redeployed
    tool needs no Max restart.
    """
    name = "gstools_" + os.path.splitext(os.path.basename(path))[0]
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module.show()


# ---------------------------------------------------------------------------
# Units
# ---------------------------------------------------------------------------
# Max's system unit types, as units.SystemType names them: the singular name
# for a label, and centimetres in one.
_UNITS = {
    "inches": ("Inch", 2.54),
    "feet": ("Foot", 30.48),
    "miles": ("Mile", 160934.4),
    "millimeters": ("Millimeter", 0.1),
    "centimeters": ("Centimeter", 1.0),
    "meters": ("Meter", 100.0),
    "kilometers": ("Kilometer", 100000.0),
}


def _system_unit():
    from pymxs import runtime as rt
    return str(rt.units.SystemType).lstrip("#").lower(), float(rt.units.SystemScale)


def cm_per_unit():
    """Centimetres in one system unit, the unit vertex positions are in."""
    kind, scale = _system_unit()
    return scale * _UNITS[kind][1]


def scene_unit():
    """The system unit for a label: 'Centimeter', or 'Inch × 2' for a scaled unit."""
    kind, scale = _system_unit()
    name = _UNITS[kind][0]
    if abs(scale - 1.0) > 1e-6:
        name += u" × {:g}".format(scale)
    return name


# ---------------------------------------------------------------------------
# Remembered preferences
# ---------------------------------------------------------------------------
# Preferences that last between sessions (the Maya tools keep these in
# optionVars), in one JSON file beside common\ and the version folders, so
# every Max version shares them. Keys are prefixed by the tool. Values a
# project spec defines don't belong here.
_PREFS_FILE = "gstools_prefs.json"
_prefs = None


def max_root():
    """...\\Autodesk\\3dsMax: the folder that holds common\\ and every version folder."""
    from pymxs import runtime as rt
    # #userScripts is ...\3dsMax\<year> - 64bit\ENU\scripts.
    scripts = os.path.normpath(rt.getDir(rt.Name("userScripts")))
    return os.path.dirname(os.path.dirname(os.path.dirname(scripts)))


def _prefs_path():
    return os.path.join(max_root(), _PREFS_FILE)


def _load_prefs():
    global _prefs
    if _prefs is None:
        try:
            with open(_prefs_path(), "r", encoding="utf-8") as fh:
                data = json.load(fh)
            _prefs = data if isinstance(data, dict) else {}
        except (OSError, ValueError):
            _prefs = {}
    return _prefs


def pref_get(key, default):
    value = _load_prefs().get(key, default)
    return value if isinstance(value, type(default)) else default


def pref_set(key, value):
    prefs = _load_prefs()
    if prefs.get(key) == value:
        return
    prefs[key] = value
    path = _prefs_path()
    try:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(prefs, fh, indent=2, sort_keys=True)
    except OSError as exc:
        print("[GSTools] Could not save preferences to {}: {}".format(path, exc))
