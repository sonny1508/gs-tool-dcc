"""
scene_checker_ui.py — GSTools Scene Checker for 3ds Max 2023+
============================================================
UI:             PySide6 (Max 2025+) or PySide2 (Max 2023) QDialog, the binding
                picked by gs_max.qt_modules()
Max operations: scene_checker.ms backend, called via pymxs.runtime

The .mcr macro runs this file (python.ExecuteFile), and the last line hands it to
gs_max.launch() to run as a module of its own. All checking logic lives in
scene_checker.ms beside this file; it is fileIn'd fresh on every launch, so both
this UI and the backend can be edited without restarting 3ds Max.
"""
from __future__ import annotations
import os
import sys

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))

# The shared GSTools helpers live in common\gstools\_core.
_CORE = os.path.join(os.path.dirname(os.path.dirname(_THIS_DIR)), "_core")
if _CORE not in sys.path:
    sys.path.append(_CORE)

import gs_max  # noqa: E402  (must follow the sys.path setup)

# MaxScript backend lives beside this file.
_MS_PATH = os.path.join(_THIS_DIR, "scene_checker.ms")
_ms_loaded = False


# ── MaxScript bridge ──────────────────────────────────────────────────────────

def _ensure_ms() -> None:
    """Load scene_checker.ms once (idempotent within a launch)."""
    global _ms_loaded
    if _ms_loaded:
        return
    from pymxs import runtime as rt
    rt.fileIn(_MS_PATH)
    _ms_loaded = True


def _call_ms(expr: str):
    """Load the backend then evaluate a MaxScript expression, returning its value."""
    _ensure_ms()
    from pymxs import runtime as rt
    return rt.execute(expr)


def _to_str_list(result) -> list | None:
    """Convert a MaxScript array return into a Python list of strings.

    Returns None when the backend returned `undefined` (validation failed /
    nothing to do), so the caller can leave its list unchanged.
    """
    if result is None:
        return None
    try:
        return [str(x) for x in result]
    except TypeError:
        return []


def _scene_info() -> list:
    """Return the INFO panel rows as [(label, value), ...]."""
    flat = _to_str_list(_call_ms("SC_GetSceneInfo()")) or []
    return list(zip(flat[0::2], flat[1::2]))


# ── Scene callbacks (keep the INFO panel current) ─────────────────────────────

_INFO_CALLBACK_ID = "GSSceneCheckerInfo"
# Every Max event that can change what the INFO panel shows.
_INFO_EVENTS = (
    "unitsChange",
    "filePostOpen",
    "systemPostNew",
    "systemPostReset",
    "sceneNodeAdded",
    "nodePostDelete",
)
_active_dialog = None


def _on_scene_changed():
    """Max callback (takes no arguments): refresh the open dialog's INFO panel."""
    global _active_dialog
    if _active_dialog is None:
        return
    try:
        _active_dialog.schedule_info_refresh()
    except RuntimeError:  # the C++ side was deleted without finished() firing
        _active_dialog = None


def _register_info_callbacks() -> None:
    from pymxs import runtime as rt
    _unregister_info_callbacks()
    for event in _INFO_EVENTS:
        rt.callbacks.addScript(rt.Name(event), _on_scene_changed,
                               id=rt.Name(_INFO_CALLBACK_ID))


def _unregister_info_callbacks() -> None:
    from pymxs import runtime as rt
    rt.callbacks.removeScripts(id=rt.Name(_INFO_CALLBACK_ID))


# ── Dialog ────────────────────────────────────────────────────────────────────

def show() -> None:
    """Open (or re-open) the Scene Checker dialog."""
    global _active_dialog
    QtWidgets, _, _ = gs_max.qt_modules()
    parent = gs_max.main_window()

    for w in QtWidgets.QApplication.topLevelWidgets():
        if w.objectName() == "Scene Checker UI":
            w.close()
            w.deleteLater()

    DialogClass = _get_dialog_class()
    dlg = DialogClass(parent)
    _active_dialog = dlg
    _register_info_callbacks()
    dlg.show()


# _SceneCheckerDialog is built at runtime so PySide2 isn't imported at module
# load time (keeps the module importable outside Max, e.g. for tests).
_SceneCheckerDialog = None


def _get_dialog_class():
    """Return the _SceneCheckerDialog class, creating it if necessary."""
    global _SceneCheckerDialog
    if _SceneCheckerDialog is not None:
        return _SceneCheckerDialog

    QtWidgets, QtCore, _ = gs_max.qt_modules()

    class _SceneCheckerDialog(QtWidgets.QDialog):
        def __init__(self, parent=None):
            super(_SceneCheckerDialog, self).__init__(parent)
            self.setObjectName("Scene Checker UI")
            self.setWindowTitle("Scene Checker v1.25")
            self.setWindowFlags(self.windowFlags() | QtCore.Qt.Window)
            self.resize(420, 380)

            self._current_check_type = ""
            self._info_values = {}  # INFO row label -> value QLabel
            self._build_ui()

            # Scene events arrive in bursts (a merge fires sceneNodeAdded once per
            # node), so they only restart this timer and the panel refreshes once.
            self._info_timer = QtCore.QTimer(self)
            self._info_timer.setSingleShot(True)
            self._info_timer.setInterval(100)
            self._info_timer.timeout.connect(self._refresh_info)
            # finished fires for the close button, Esc and close() alike.
            self.finished.connect(self._on_finished)
            self._refresh_info()

        # ── Layout ────────────────────────────────────────────────────────────
        def _build_ui(self):
            root = QtWidgets.QHBoxLayout(self)
            root.setContentsMargins(8, 8, 8, 8)
            root.setSpacing(8)

            # Left column — grouped check buttons
            left = QtWidgets.QVBoxLayout()
            left.setSpacing(8)
            root.addLayout(left)

            topo = QtWidgets.QGroupBox("TOPOLOGY")
            topo_l = QtWidgets.QVBoxLayout(topo)
            topo_l.addWidget(self._btn("Check Open Edges", self._on_check_openedges))
            topo_l.addWidget(self._btn("Check N-gons", self._on_check_ngons))
            topo_l.addWidget(self._btn("Check Smoothing", self._on_check_sg))
            topo_l.addWidget(self._btn("Auto Flat SG", self._on_auto_flat_sg))
            left.addWidget(topo)

            uv = QtWidgets.QGroupBox("UV")
            uv_l = QtWidgets.QVBoxLayout(uv)
            uv_l.addWidget(self._btn("Check UV Channels", self._on_check_uvchannels))
            left.addWidget(uv)

            obj = QtWidgets.QGroupBox("OBJECT")
            obj_l = QtWidgets.QVBoxLayout(obj)
            obj_l.addWidget(self._btn("Check Transform Non-zero", self._on_check_transform))
            obj_l.addWidget(self._btn("Reset XForm", self._on_reset_transform))
            obj_l.addWidget(self._btn("Reset Pivot", self._on_reset_pivot))
            left.addWidget(obj)

            left.addStretch()

            # INFO sits below the stretch so it stays pinned to the bottom.
            info = QtWidgets.QGroupBox("INFO")
            info_l = QtWidgets.QVBoxLayout(info)
            self._info_form = QtWidgets.QFormLayout()
            info_l.addLayout(self._info_form)
            self._btn_select_error = self._btn("Select Error", self._on_select_error)
            self._btn_select_error.setEnabled(False)
            info_l.addWidget(self._btn_select_error)
            left.addWidget(info)

            # Right side — results list
            self._lbx_results = QtWidgets.QListWidget()
            self._lbx_results.setMinimumWidth(200)
            self._lbx_results.itemDoubleClicked.connect(self._on_result_double_clicked)
            root.addWidget(self._lbx_results, stretch=1)

        def _btn(self, label, callback):
            b = QtWidgets.QPushButton(label)
            b.setFixedHeight(25)
            b.setMinimumWidth(160)
            b.clicked.connect(callback)
            return b

        # ── INFO panel ────────────────────────────────────────────────────────
        def schedule_info_refresh(self):
            self._info_timer.start()  # restarts if already pending

        def _refresh_info(self):
            """Rebuild the INFO rows from the backend; rows are created on first sight."""
            for name, value in _scene_info():
                lbl = self._info_values.get(name)
                if lbl is None:
                    lbl = QtWidgets.QLabel()
                    self._info_form.addRow(name + ":", lbl)
                    self._info_values[name] = lbl
                lbl.setText(value)

        def _on_finished(self, _result):
            global _active_dialog
            self._info_timer.stop()
            _unregister_info_callbacks()
            if _active_dialog is self:
                _active_dialog = None

        # ── Results plumbing ──────────────────────────────────────────────────
        def _set_results(self, check_type, items, select_enabled):
            """Populate the list and Select-Error button for a completed check."""
            self._current_check_type = check_type
            self._lbx_results.clear()
            for it in items:
                self._lbx_results.addItem(it)
            self._btn_select_error.setEnabled(select_enabled and len(items) > 0)

        # ── Button handlers ───────────────────────────────────────────────────
        def _on_check_openedges(self):
            items = _to_str_list(_call_ms("SC_CheckOpenEdges()"))
            if items is None:
                return  # validation failed — leave list unchanged
            self._set_results("openedges", items, True)

        def _on_check_ngons(self):
            items = _to_str_list(_call_ms("SC_CheckNgons()"))
            if items is None:
                return
            self._set_results("ngons", items, True)

        def _on_check_sg(self):
            items = _to_str_list(_call_ms("SC_CheckSmoothing()"))
            if items is None:
                return
            self._set_results("sg", items, True)

        def _on_auto_flat_sg(self):
            _call_ms("SC_AutoFlatSG()")

        def _on_check_uvchannels(self):
            items = _to_str_list(_call_ms("SC_CheckUVChannels()"))
            if items is None:
                return
            # UV rows are informational — no error selection.
            self._set_results("uv", items, False)

        def _on_check_transform(self):
            items = _to_str_list(_call_ms("SC_CheckTransform()"))
            if items is None:
                return
            self._set_results("transform", items, True)

        def _on_reset_transform(self):
            _call_ms("SC_ResetXForm()")

        def _on_reset_pivot(self):
            _call_ms("SC_ResetPivot()")

        def _on_select_error(self):
            _call_ms("SC_SelectError()")

        def _on_result_double_clicked(self, item):
            item_text = item.text()
            obj_name = item_text
            # UV display format is "ObjectName (NN maps)" — extract the name.
            if self._current_check_type == "uv":
                paren_pos = item_text.find(" (")
                if paren_pos != -1:
                    obj_name = item_text[:paren_pos]
            from pymxs import runtime as rt
            rt._sc_obj_name = obj_name
            _call_ms("SC_SelectByName _sc_obj_name")

    _SceneCheckerDialog = _SceneCheckerDialog
    return _SceneCheckerDialog


# ── Execution: Scene_Checker.mcr runs this file with python.ExecuteFile ──────
if __name__ == "__main__":
    gs_max.launch(__file__)
