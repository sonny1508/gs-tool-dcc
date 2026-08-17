"""GS Pipeline shared startup logic.

This module lives once under ``common/scripts`` and is loaded by the tiny
per-version shim at ``<version>/scripts/startup/gs_pipeline/__init__.py``.

Responsibilities, run ONCE per Blender launch (not per file open):
  1. Register the common scripts folder as a named script directory so Blender
     discovers the shared addons under ``common/scripts/addons``.
  2. Enable the GS pipeline addons that should be on by default.
  3. Persist preferences only if something actually changed.

Works on Blender 3.6 and 4.x (the ``filepaths.script_directories`` collection
exists in both).
"""

import os
import bpy

# Stable label for the script directory we manage, so we can find/upsert it
# without disturbing any directory an artist added themselves.
MANAGED_DIR_NAME = "GSTools_Common"

# Addons enabled automatically on launch. Kept version-aware for future
# 3.6-vs-4.x divergence even though the current set is uniform across versions.
COMMON_AUTO_ENABLE = [
    "GS_Pipeline",
    "GS_Asset_Validation",
    "GS_Texture_Validator",
    "s4_env_tools",
    "s4_vehicle_tools",
]

# Addons that were merged elsewhere and must be force-disabled on launch so they
# don't double-register operators/properties that now live in GS_Pipeline.
COMMON_FORCE_DISABLE = [
    "S4_Veh_Validator",
    "S4_Env_Validator",
]


def _common_scripts_dir():
    """Absolute path to common/scripts (the parent of this package's folder)."""
    # This file: <...>/common/scripts/gs_pipeline_core/__init__.py
    return os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))


def _auto_enable_list():
    """Return the addon module names to auto-enable for the running version."""
    addons = list(COMMON_AUTO_ENABLE)
    # Example hook for future divergence:
    #   if bpy.app.version[:2] == (3, 6):
    #       addons += ["Some_36_Only_Addon"]
    return addons


def _ensure_script_directory(common_dir):
    """Idempotently ensure the common scripts dir is registered. Returns True if added."""
    filepaths = bpy.context.preferences.filepaths
    target = os.path.normpath(common_dir)

    for sd in filepaths.script_directories:
        if os.path.normpath(sd.directory) == target or sd.name == MANAGED_DIR_NAME:
            # Already present (refresh the fields in case the path moved).
            sd.name = MANAGED_DIR_NAME
            sd.directory = target
            return False

    sd = filepaths.script_directories.new()
    sd.name = MANAGED_DIR_NAME
    sd.directory = target

    # Make addons under the freshly-registered path importable this session.
    if hasattr(bpy.utils, "refresh_script_paths"):
        bpy.utils.refresh_script_paths()
    return True


def _setup():
    """One-shot setup. Returns None so the timer never repeats."""
    print("[GS Pipeline] Running startup setup...")
    changed = False

    try:
        changed |= _ensure_script_directory(_common_scripts_dir())
    except Exception as e:  # never let setup break Blender startup
        print(f"[GS Pipeline] Failed to register script directory: {e}")

    # Disable retired addons first so their operators/properties free up before
    # GS_Pipeline re-registers the merged versions.
    for addon_name in COMMON_FORCE_DISABLE:
        try:
            if addon_name in bpy.context.preferences.addons:
                bpy.ops.preferences.addon_disable(module=addon_name)
                changed = True
                print(f"[GS Pipeline] Disabled retired add-on: {addon_name}")
        except Exception as e:
            print(f"[GS Pipeline] Could not disable {addon_name}: {e}")

    for addon_name in _auto_enable_list():
        try:
            if addon_name not in bpy.context.preferences.addons:
                bpy.ops.preferences.addon_enable(module=addon_name)
                changed = True
                print(f"[GS Pipeline] Enabled add-on: {addon_name}")
        except Exception as e:
            print(f"[GS Pipeline] Could not enable {addon_name}: {e}")

    if changed:
        try:
            bpy.ops.wm.save_userpref()
            print("[GS Pipeline] Preferences saved.")
        except Exception as e:
            print(f"[GS Pipeline] Could not save preferences: {e}")
    else:
        print("[GS Pipeline] Nothing changed; preferences left untouched.")

    return None


def register():
    """Schedule setup to run once when the event loop is ready."""
    print("[GS Pipeline] Registering (scheduling one-shot setup).")
    # A one-shot timer runs once at launch with full context available, instead
    # of a load_post handler that would re-run on every file open.
    bpy.app.timers.register(_setup, first_interval=0.0)


def unregister():
    print("[GS Pipeline] Unregistering.")
    if bpy.app.timers.is_registered(_setup):
        bpy.app.timers.unregister(_setup)
