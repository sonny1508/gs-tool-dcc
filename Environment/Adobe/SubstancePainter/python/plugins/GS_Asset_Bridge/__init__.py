"""GS Asset Bridge — receives assets from GS Asset Manager into Painter.

Installation
------------
Copy the whole GS_Asset_Bridge folder to:
    %USERPROFILE%\\Documents\\Adobe\\Adobe Substance 3D Painter\\python\\plugins\\

Then enable "GS_Asset_Bridge" under Python > Plugins.

Toolbar
-------
Enabling the plugin adds a "GS Asset Bridge" toolbar with one button, which
shows the panel. Icons live in GS_Asset_Bridge/icons/ — see icons/README.md.

Requires Substance 3D Painter 2021.3+ for fill-layer import (the studio is on
12.1.0 / Python API 0.3.5). Older versions degrade to shelf-only import.
"""

from pathlib import Path

import substance_painter as sp
import substance_painter.logging as sp_log
import substance_painter.project as sp_project
import substance_painter.ui as sp_ui

try:
    from PySide2 import QtGui, QtWidgets
except ImportError:
    from PySide6 import QtGui, QtWidgets

from .bridge import BridgeSignals, BridgeThread
from .importer import handle_request
from .launcher import launch
from .panel import BridgePanel


ICON_DIR = Path(__file__).parent / "icons"
TOOLBAR_LABEL = "GS Asset Bridge"
TOOLBAR_ID = "gsAssetBridgeToolbar"

# Drop a PNG with this name into icons/ and the toolbar button uses it;
# without one the button falls back to text. See icons/README.md.
TOOLBAR_ICON = "icon.png"

# ── Surviving a module reload ────────────────────────────────────────────────
# Painter reloads the plugin MODULE, which resets every global in this file. The
# original code kept its instance in a module global, so a reload silently
# discarded the reference while the old thread kept running — each toggle
# permanently stacked another ticker. The handle is parked on the
# `substance_painter` package instead, which outlives our module, so a reload
# can always find and stop whatever it is replacing.
_INSTANCE_ATTR = "_gs_asset_bridge_instance"


def _get_live_instance():
    return getattr(sp, _INSTANCE_ATTR, None)


def _set_live_instance(instance):
    if instance is None:
        if hasattr(sp, _INSTANCE_ATTR):
            delattr(sp, _INSTANCE_ATTR)
    else:
        setattr(sp, _INSTANCE_ATTR, instance)


def _load_icon(name):
    path = ICON_DIR / name
    if not path.is_file():
        return None
    pixmap = QtGui.QPixmap(str(path))
    return None if pixmap.isNull() else QtGui.QIcon(pixmap)


class GSAssetBridgePlugin:
    def __init__(self):
        self.signals = BridgeSignals()
        self.thread = BridgeThread(self.signals)
        self.panel = BridgePanel(
            on_launch_app=self.launch_app,
            on_check_connection=self.thread.retry_now,
        )
        self._toolbar = None
        self._actions = []
        self._dock = None

        self.signals.state_changed.connect(self._on_state_changed)
        self.signals.request.connect(self._on_request)

        sp_ui.add_dock_widget(self.panel)
        self._build_toolbar()
        self._locate_dock()
        self.thread.start()

    # -- toolbar --------------------------------------------------------------

    def _build_toolbar(self):
        try:
            self._toolbar = sp_ui.add_toolbar(TOOLBAR_LABEL, TOOLBAR_ID)
        except Exception as exc:
            sp_log.warning("[GS Asset Bridge] could not add toolbar: %s" % exc)
            return

        icon = _load_icon(TOOLBAR_ICON)
        action = (self._toolbar.addAction(icon, TOOLBAR_LABEL) if icon
                  else self._toolbar.addAction(TOOLBAR_LABEL))
        action.setToolTip("Show the GS Asset Bridge panel")
        action.triggered.connect(self.show)
        self._actions.append(action)

    # -- slots (main thread) --------------------------------------------------

    def _on_state_changed(self, connected):
        self.panel.set_connected(connected)
        # One line per transition, not one per retry.
        sp_log.info("[GS Asset Bridge] %s" % ("connected" if connected else "disconnected"))

    def _on_request(self, message):
        """Queue an import behind whatever Painter is already doing.

        A project that has just been created or opened leaves the engine BUSY
        for a while: the texture sets are still being built, and the resource
        and layerstack calls the import makes are rejected until they are. That
        is the reported "a fresh file does not export properly" — the first
        import into a new project arrives during exactly that window, fails,
        and the next one a minute later works, which makes the whole thing look
        intermittent when it is precisely timed.

        execute_when_not_busy() is Painter's own answer: it runs the callable
        on the main thread once the engine is idle. Reached through getattr
        because it is not in every API version this plugin has to load under,
        and an older Painter is better served by trying immediately than by not
        importing at all.
        """
        defer = getattr(sp_project, "execute_when_not_busy", None)
        if defer is None:
            self._run_import(message)
            return

        try:
            defer(lambda: self._run_import(message))
        except Exception as exc:
            sp_log.warning("[GS Asset Bridge] could not defer import (%s); running now" % exc)
            self._run_import(message)

    def _run_import(self, message):
        result = handle_request(message)
        label = message.get("label", "asset")
        ok = result.get("status") == "ok"

        self.panel.add_entry(label, result.get("detail", result.get("error", "")), ok)
        if not ok:
            sp_log.warning("[GS Asset Bridge] %s: %s" % (label, result.get("error")))

        # Ack only now that the import has actually run, so the app reports the
        # real outcome instead of "the socket write succeeded". `id` echoes the
        # request so the app can match the reply to the right asset.
        result["id"] = message.get("id")
        result["label"] = label
        self.thread.send(result)

    def launch_app(self):
        ok, detail = launch()
        if ok:
            # The app takes a couple of seconds to come up and start listening.
            # Asking now costs one refused connect and means the panel turns
            # green as soon as it is up, rather than after the backoff that is
            # already running.
            self.thread.retry_now()
            return
        box = QtWidgets.QMessageBox(sp_ui.get_main_window())
        box.setWindowTitle("GS Asset Manager not found")
        box.setIcon(QtWidgets.QMessageBox.Warning)
        box.setText("Could not open GS Asset Manager.")
        box.setInformativeText(detail)
        box.exec_() if hasattr(box, "exec_") else box.exec()

    # -- ui plumbing ----------------------------------------------------------

    def _locate_dock(self):
        parent = self.panel.parent()
        while parent is not None:
            if isinstance(parent, QtWidgets.QDockWidget):
                self._dock = parent
                return
            parent = parent.parent()

    def show(self):
        if self._dock is None:
            self._locate_dock()
        target = self._dock if isinstance(self._dock, QtWidgets.QDockWidget) else self.panel
        target.show()
        target.raise_()

    def stop(self):
        self.thread.stop()
        # join() so a reload cannot leave the old socket thread running
        # alongside its replacement. Bounded, because a thread blocked in recv()
        # is released by the socket close in stop().
        self.thread.join(timeout=2.0)

        if self._toolbar is not None:
            try:
                sp_ui.delete_ui_element(self._toolbar)
            except Exception:
                pass
            self._toolbar = None
        self._actions = []

        try:
            target = self._dock if isinstance(self._dock, QtWidgets.QDockWidget) else self.panel
            sp_ui.delete_ui_element(target)
        except Exception:
            pass


# ── Plugin entry points (called by Substance Painter) ────────────────────────

def start_plugin():
    existing = _get_live_instance()
    if existing is not None:
        # A module reload lands here with the previous instance still alive.
        # Stopping it is what prevents tickers stacking up on every toggle.
        try:
            existing.stop()
        except Exception as exc:
            sp_log.warning("[GS Asset Bridge] could not stop previous instance: %s" % exc)
        _set_live_instance(None)

    _set_live_instance(GSAssetBridgePlugin())
    sp_log.info("[GS Asset Bridge] started")


def close_plugin():
    instance = _get_live_instance()
    if instance is None:
        return
    instance.stop()
    _set_live_instance(None)
    sp_log.info("[GS Asset Bridge] stopped")


__plugin_name__ = "GS Asset Bridge"
__plugin_version__ = "1.0.0"
__plugin_author__ = "Glenda Studio"
__plugin_description__ = "Receives assets from GS Asset Manager into the open project."
