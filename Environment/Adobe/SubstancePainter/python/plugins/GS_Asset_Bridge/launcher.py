"""Finding and starting GS Asset Manager from inside Painter."""

import os
import subprocess

import substance_painter.logging as sp_log

EXE_NAME = "GS Asset Manager.exe"

# Checked in order. The registry is consulted first because it survives the
# installer's directory page being changed at install time; the fixed paths
# cover a machine where the registry entry is missing or the app was unpacked
# by hand.
FALLBACK_DIRS = [
    r"C:\Program Files\GSApplication\GS Asset Manager",
    r"C:\Program Files\GS Asset Manager",
    r"C:\Program Files (x86)\GSApplication\GS Asset Manager",
]

UNINSTALL_ROOT = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
DISPLAY_NAME_PREFIX = "GS Asset Manager"


def _install_dir_from_key(key):
    """Best-effort install directory from one Uninstall registry key.

    InstallLocation is the obvious field but electron-builder leaves it EMPTY,
    so the path has to be recovered from UninstallString, which looks like:

        "C:\\Program Files\\GSApplication\\GS Asset Manager\\Uninstall GS Asset Manager.exe" /allusers
    """
    import winreg

    try:
        location, _ = winreg.QueryValueEx(key, "InstallLocation")
        if location and location.strip():
            return location.strip()
    except OSError:
        pass

    for field in ("QuietUninstallString", "UninstallString"):
        try:
            raw, _ = winreg.QueryValueEx(key, field)
        except OSError:
            continue
        if not raw:
            continue
        # The uninstaller path is the first quoted span, or the first token.
        uninstaller = raw.split('"')[1] if raw.startswith('"') else raw.split(" ")[0]
        if uninstaller:
            return os.path.dirname(uninstaller)

    return None


def _from_registry():
    try:
        import winreg
    except ImportError:
        return None      # not Windows

    # Scanned by DisplayName rather than by a fixed key: electron-builder's key
    # name is a GUID derived from the appId, which changes if the appId ever
    # does, whereas the display name is stable and human-checkable.
    for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        for view in (winreg.KEY_WOW64_64KEY, winreg.KEY_WOW64_32KEY):
            try:
                with winreg.OpenKey(root, UNINSTALL_ROOT, 0, winreg.KEY_READ | view) as parent:
                    count = winreg.QueryInfoKey(parent)[0]
                    for i in range(count):
                        try:
                            name = winreg.EnumKey(parent, i)
                            with winreg.OpenKey(parent, name, 0, winreg.KEY_READ | view) as key:
                                display, _ = winreg.QueryValueEx(key, "DisplayName")
                                if not display.startswith(DISPLAY_NAME_PREFIX):
                                    continue
                                directory = _install_dir_from_key(key)
                                if not directory:
                                    continue
                                candidate = os.path.join(directory, EXE_NAME)
                                if os.path.isfile(candidate):
                                    return candidate
                        except OSError:
                            continue
            except OSError:
                continue
    return None


def find_app():
    """Absolute path to the installed app, or None."""
    found = _from_registry()
    if found:
        return found

    for directory in FALLBACK_DIRS:
        candidate = os.path.join(directory, EXE_NAME)
        if os.path.isfile(candidate):
            return candidate

    # Set GS_ASSET_MANAGER_EXE to point at a dev build or a non-standard
    # install without editing this file.
    override = os.environ.get("GS_ASSET_MANAGER_EXE")
    if override and os.path.isfile(override):
        return override

    return None


def launch():
    """Start GS Asset Manager.

    Returns (ok, detail). `detail` is the path when it started, or an
    explanation of where we looked when it did not.
    """
    exe = find_app()
    if not exe:
        searched = "\n".join("    " + d for d in FALLBACK_DIRS)
        return False, (
            "GS Asset Manager does not appear to be installed on this machine.\n\n"
            "Looked in the registry and in:\n%s\n\n"
            "Install it, or set the GS_ASSET_MANAGER_EXE environment variable "
            "to the full path of %s." % (searched, EXE_NAME)
        )

    try:
        # Detached, so closing Painter does not take the app with it.
        subprocess.Popen(
            [exe],
            cwd=os.path.dirname(exe),
            creationflags=getattr(subprocess, "DETACHED_PROCESS", 0)
            | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
            close_fds=True,
        )
        sp_log.info("[GS Asset Bridge] launched %s" % exe)
        return True, exe
    except Exception as exc:
        return False, "Could not start GS Asset Manager:\n\n%s\n\n%s" % (exe, exc)
