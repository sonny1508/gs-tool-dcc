"""
scene_checker_ui.py — GSTools Scene Checker for 3ds Max 2023 / 2025
============================================================
UI:             PySide6 (Max 2025, Qt6) or PySide2 (Max 2023, Qt5) QDialog
Max operations: scene_checker.ms backend, called via pymxs.runtime

The Qt binding is resolved lazily via _qt_modules(): PySide6 is preferred (Max
2025+, Python 3.11) and falls back to PySide2 (Max 2023, Python 3.9). Both expose
the same widget/enum names used here, so this one file serves both Max versions.

The .mcr macro only loads this file (python.ExecuteFile). All checking logic
lives in scene_checker.ms beside this file; it is fileIn'd fresh on every launch,
so both this UI and the backend can be edited without restarting 3ds Max.
"""
from __future__ import annotations
import os
import sys

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

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


# ── Qt binding shim (PySide6 for Max 2025, PySide2 for Max 2023) ──────────────

def _qt_modules():
    """Return (QtWidgets, QtCore, QtGui) for the Qt binding this Max version uses.

    The binding MUST match the one 3ds Max itself runs: the parent window comes
    from qtmax, and mixing bindings (e.g. a PySide2 QMainWindow into a PySide6
    QDialog) crashes with "wrong argument types". So we choose by Max version,
    not by "what happens to be importable" — a stray PySide6 can sit on sys.path
    in a Max 2023 install even though its real Qt is PySide2.

    3ds Max 2025+ ships Python 3.11 + PySide6/Qt6; 2024 and earlier ship an older
    Python + PySide2/Qt5. Both expose the same widget/enum names used here.
    """
    if sys.version_info >= (3, 11):
        try:
            from PySide6 import QtWidgets, QtCore, QtGui
        except ImportError:
            from PySide2 import QtWidgets, QtCore, QtGui
    else:
        try:
            from PySide2 import QtWidgets, QtCore, QtGui
        except ImportError:
            from PySide6 import QtWidgets, QtCore, QtGui
    return QtWidgets, QtCore, QtGui


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


# ── Dialog ────────────────────────────────────────────────────────────────────

def show() -> None:
    """Open (or re-open) the Scene Checker dialog."""
    global _ms_loaded
    _ms_loaded = False  # always reload scene_checker.ms so edits take effect
    QtWidgets, _, _ = _qt_modules()
    try:
        import qtmax
        parent = qtmax.GetQMaxMainWindow()
    except Exception:
        try:
            import MaxPlus
            parent = MaxPlus.GetQMaxMainWindow()
        except Exception:
            parent = None

    for w in QtWidgets.QApplication.topLevelWidgets():
        if w.objectName() == "Scene Checker UI":
            w.close()
            w.deleteLater()

    DialogClass = _get_dialog_class()
    dlg = DialogClass(parent)
    dlg.show()


# _SceneCheckerDialog is built at runtime so PySide2 isn't imported at module
# load time (keeps the module importable outside Max, e.g. for tests).
_SceneCheckerDialog = None


def _get_dialog_class():
    """Return the _SceneCheckerDialog class, creating it if necessary."""
    global _SceneCheckerDialog
    if _SceneCheckerDialog is not None:
        return _SceneCheckerDialog

    QtWidgets, QtCore, _ = _qt_modules()

    class _SceneCheckerDialog(QtWidgets.QDialog):
        def __init__(self, parent=None):
            super(_SceneCheckerDialog, self).__init__(parent)
            self.setObjectName("Scene Checker UI")
            self.setWindowTitle("Scene Checker v1.2")
            self.setWindowFlags(self.windowFlags() | QtCore.Qt.Window)
            self.resize(420, 380)

            self._current_check_type = ""
            self._build_ui()

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

            sel = QtWidgets.QGroupBox("SELECT")
            sel_l = QtWidgets.QVBoxLayout(sel)
            self._btn_select_error = self._btn("Select Error", self._on_select_error)
            self._btn_select_error.setEnabled(False)
            sel_l.addWidget(self._btn_select_error)
            left.addWidget(sel)

            left.addStretch()

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


# ── Execution: show the dialog when the MacroScript calls ExecuteFile ─────────
try:
    show()
except Exception as e:
    print(f"[Scene Checker] Error showing dialog: {e}")
