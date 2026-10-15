"""
hw3_tools_ui.py — GSTools HW3 Tools for 3ds Max 2023 / 2025
============================================================
UI:            PySide6 (Max 2025, Qt6) or PySide2 (Max 2023, Qt5) QDialog
Max operations: pymxs.runtime (imported at call time — not at module load)

Qt binding is resolved lazily via _qt_modules(): PySide6 is preferred (3ds Max
2025+, Python 3.11) and falls back to PySide2 (3ds Max 2023, Python 3.9). This
keeps a single file working across both Max versions. Import is deferred to call
time so the module stays importable under pytest where no Qt binding exists.
"""
from __future__ import annotations
import json
import os
import sys

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

temp_dir = os.environ["TEMP"]
_UE_ROOT = os.path.join(temp_dir, "GSApplication", "unreal-engine")
MAT_ROOT  = os.path.join(_UE_ROOT, "mat-ins")
TEX_ROOT  = os.path.join(_UE_ROOT, "textures")

_HW3_ROOT = os.path.join(temp_dir, "GSApplication", "3dsmax", "hw3_tools")
MESH_ROOT = os.path.join(_HW3_ROOT, "mesh")
IO_ROOT   = os.path.join(_HW3_ROOT, "io")

_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".tga", ".tif", ".tiff", ".exr", ".hdr", ".bmp"}


# ── Pure-Python data helpers (no Maya / Max dependency) ───────────────────────

def _resolve_texture_path(ue_path: str, root: str) -> str | None:
    """Convert a UE asset path (/Game/.../T_Foo.T_Foo) to an absolute file path."""
    dot_idx = ue_path.rfind(".")
    if dot_idx != -1:
        ue_path = ue_path[:dot_idx]
    local = os.path.join(root, ue_path.lstrip("/").replace("/", os.sep))
    for ext in (".png", ".jpg", ".jpeg", ".tga", ".tif", ".tiff",
                ".exr", ".hdr", ".bmp"):
        candidate = local + ext
        if os.path.isfile(candidate):
            return candidate
    return None


def _load_json_materials() -> list[dict]:
    """Load and sort all .json material instance files from MAT_ROOT."""
    result: list[dict] = []
    try:
        for fname in os.listdir(MAT_ROOT):
            if fname.lower().endswith(".json"):
                fpath = os.path.join(MAT_ROOT, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as fh:
                        result.append(json.load(fh))
                except Exception:
                    pass
    except Exception as e:
        print(f"[HW3 Tools] Could not read MAT_ROOT ({MAT_ROOT}): {e}")
    result.sort(key=lambda d: d.get("name", "").lower())
    return result


def _load_textures() -> list[dict]:
    """Return sorted list of {name, path} dicts from TEX_ROOT."""
    json_results: list[dict] = []
    image_results: list[dict] = []
    try:
        for fname in os.listdir(TEX_ROOT):
            fpath = os.path.join(TEX_ROOT, fname)
            ext = os.path.splitext(fname)[1].lower()
            if ext == ".json":
                try:
                    with open(fpath, "r", encoding="utf-8") as fh:
                        data = json.load(fh)
                    resolved = _resolve_texture_path(data.get("path", ""), TEX_ROOT)
                    if resolved:
                        json_results.append({
                            "name": data.get("name", os.path.splitext(fname)[0]),
                            "path": resolved,
                        })
                except Exception:
                    pass
            elif ext in _IMAGE_EXTS:
                image_results.append({
                    "name": os.path.splitext(fname)[0],
                    "path": fpath,
                })
    except Exception as e:
        print(f"[HW3 Tools] Could not read TEX_ROOT ({TEX_ROOT}): {e}")
    results = json_results if json_results else image_results
    results.sort(key=lambda d: d["name"].lower())
    return results


def _find_mat_textures(mat_data: dict,
                       root: str = MAT_ROOT) -> tuple[str | None, str | None]:
    """Return (bc_path, n_path) for _BC and _N textures from a material JSON."""
    bc_path: str | None = None
    n_path:  str | None = None
    for _, tex_info in mat_data.get("textures", {}).items():
        if not tex_info.get("exported", False):
            continue
        tex_name = tex_info.get("name", "")
        path = _resolve_texture_path(tex_info.get("path", ""), root)
        upper = tex_name.upper()
        if upper.endswith("_BC"):
            bc_path = path
        elif upper.endswith("_N"):
            n_path = path
    return bc_path, n_path


def _uv_params(r: float, g: float,
               b: float, a: float) -> tuple[float, float, float, float]:
    """Convert UE UV-ScaleOffset (R,G,B,A) to 3ds Max bitmap tiling/offset."""
    r = r if r != 0.0 else 1e-6
    g = g if g != 0.0 else 1e-6
    return r, g, -((b + (r - 1.0) * 0.5) / r), ((a + (g - 1.0) * 0.5) / g)


# ── Max material operations (require pymxs — only available inside 3ds Max) ───

def _get_color_slot(mat) -> tuple[str | None, str | None]:
    """Return (color_slot, bump_slot) attribute names for supported material types."""
    from pymxs import runtime as rt
    cls = rt.classOf(mat)
    if cls == rt.StandardMaterial:
        return "diffuseMap", "bumpMap"
    if cls == rt.PhysicalMaterial:
        return "base_color_map", "bump_map"
    return None, None


def _list_scene_materials() -> list[tuple[str, any]]:
    """Return (display_name, mat_object) for scene materials.

    Top-level Standard and Physical materials are listed by name.
    Multi/Sub-Object materials are listed with their sub-materials
    expanded beneath them (indented with └).
    Sub-materials that are Standard or Physical are selectable for assignment.
    Top-level Multi/Sub-Object rows are headers only and return None.
    """
    from pymxs import runtime as rt
    top: list[tuple[str, any]] = []
    for mat in rt.sceneMaterials:
        cls = rt.classOf(mat)
        if cls in (rt.StandardMaterial, rt.PhysicalMaterial, rt.Multimaterial):
            top.append((mat.name, mat))
    top.sort(key=lambda x: x[0].lower())

    result: list[tuple[str, any]] = []
    for display_name, mat in top:
        if rt.classOf(mat) == rt.Multimaterial:
            result.append((display_name, None))
        else:
            result.append((display_name, mat))
        if rt.classOf(mat) == rt.Multimaterial:
            try:
                for sub in mat.materialList:
                    if sub is None:
                        continue
                    sub_cls = rt.classOf(sub)
                    if sub_cls in (rt.StandardMaterial, rt.PhysicalMaterial):
                        result.append((f"  └ {sub.name}", sub))
            except Exception:
                pass
    return result


def _create_bitmap(path: str, u_tiling: float, v_tiling: float,
                   u_offset: float, v_offset: float):
    from pymxs import runtime as rt
    bm = rt.Bitmaptexture()
    bm.filename = path
    bm.coords.U_Tiling = u_tiling
    bm.coords.V_Tiling = v_tiling
    bm.coords.U_Offset = u_offset
    bm.coords.V_Offset = v_offset
    return bm


def _create_normal_bump(path: str, u_tiling: float, v_tiling: float,
                        u_offset: float, v_offset: float):
    from pymxs import runtime as rt
    nb = rt.Normal_Bump()
    nb.normal_map = _create_bitmap(path, u_tiling, v_tiling, u_offset, v_offset)
    return nb


def _assign(mat, bc_path: str | None, n_path: str | None,
            r: float, g: float, b: float, a: float) -> None:
    from pymxs import runtime as rt
    color_slot, bump_slot = _get_color_slot(mat)
    if color_slot is None:
        rt.messageBox(f"Hotwheel Tools: unsupported material type for '{mat.name}'.")
        return
    u_t, v_t, u_o, v_o = _uv_params(r, g, b, a)
    if bc_path:
        setattr(mat, color_slot, _create_bitmap(bc_path, u_t, v_t, u_o, v_o))
    if n_path:
        setattr(mat, bump_slot, _create_normal_bump(n_path, u_t, v_t, u_o, v_o))


def _is_update_mode(mat, tex_path: str) -> bool:
    """True when the material's color slot already holds this exact texture path."""
    from pymxs import runtime as rt
    try:
        color_slot, _ = _get_color_slot(mat)
        if color_slot is None:
            return False
        existing = getattr(mat, color_slot, None)
        if existing is None or rt.classOf(existing) != rt.Bitmaptexture:
            return False
        return existing.filename.replace("\\", "/") == tex_path.replace("\\", "/")
    except Exception:
        return False


def _update_uv(mat, r: float, g: float, b: float, a: float) -> None:
    """Update only the tiling/offset coords on the already-assigned bitmap."""
    from pymxs import runtime as rt
    color_slot, _ = _get_color_slot(mat)
    if color_slot is None:
        return
    bm = getattr(mat, color_slot, None)
    if bm is None or rt.classOf(bm) != rt.Bitmaptexture:
        return
    u_t, v_t, u_o, v_o = _uv_params(r, g, b, a)
    bm.coords.U_Tiling = u_t
    bm.coords.V_Tiling = v_t
    bm.coords.U_Offset = u_o
    bm.coords.V_Offset = v_o


# ── Modelling — thin Python wrappers calling hw3_tools.ms ────────────────

_ms_loaded = False

# MaxScript backend lives beside this file as hw3_tools.ms.
_MS_PATH = os.path.join(_THIS_DIR, "hw3_tools.ms")


def _ensure_ms() -> None:
    """Load hw3_tools.ms once (idempotent)."""
    global _ms_loaded
    if _ms_loaded:
        return
    from pymxs import runtime as rt
    rt.fileIn(_MS_PATH)
    _ms_loaded = True

def _call_ms(fn_call: str) -> None:
    """Load hw3_tools.ms once then call the given MaxScript expression."""
    _ensure_ms()
    from pymxs import runtime as rt
    rt.execute(fn_call)


def _load_fbx_list() -> dict:
    """Return {display_name: full_path} for all .fbx files in MESH_ROOT."""
    result = {}
    try:
        for fname in sorted(os.listdir(MESH_ROOT), key=str.lower):
            if fname.lower().endswith(".fbx"):
                result[os.path.splitext(fname)[0]] = os.path.join(MESH_ROOT, fname)
    except Exception:
        pass
    return result


# ── Qt binding shim (PySide6 for Max 2025, PySide2 for Max 2023) ──────────────

def _qt_modules():
    """Return (QtWidgets, QtCore, QtGui) from PySide6, falling back to PySide2.

    PySide6 (Qt6) ships with 3ds Max 2025+; PySide2 (Qt5) with Max 2023. Both
    expose the same widget/enum names used here, so callers are binding-agnostic.
    """
    try:
        from PySide6 import QtWidgets, QtCore, QtGui
    except ImportError:
        from PySide2 import QtWidgets, QtCore, QtGui
    return QtWidgets, QtCore, QtGui


# ── UI helpers ────────────────────────────────────────────────────────────────

def _hsep():
    QtWidgets, _, _ = _qt_modules()
    line = QtWidgets.QFrame()
    line.setFrameShape(QtWidgets.QFrame.HLine)
    line.setFrameShadow(QtWidgets.QFrame.Sunken)
    return line


# ── Dialog ────────────────────────────────────────────────────────────────────

def show() -> None:
    """Open (or re-open) the Hotwheel Tools dialog."""
    global _ms_loaded
    _ms_loaded = False  # always reload hw3_tools.ms so changes take effect
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
        if w.objectName() == "HW3 Tools UI":
            w.close()
            w.deleteLater()

    DialogClass = _get_dialog_class()
    dlg = DialogClass(parent)
    dlg.show()


# _HotwheelDialog is defined as a factory function that creates the actual class
# at runtime to avoid loading PySide2 at module import time (which breaks pytest).
_HotwheelDialog = None


def _get_dialog_class():
    """Return the _HotwheelDialog class, creating it if necessary."""
    global _HotwheelDialog
    if _HotwheelDialog is not None:
        return _HotwheelDialog

    QtWidgets, QtCore, _ = _qt_modules()

    class _HotwheelDialog(QtWidgets.QDialog):
        def __init__(self, parent=None):
            super(_HotwheelDialog, self).__init__(parent)
            self.setObjectName("HW3 Tools UI")
            self.setWindowTitle("HW3 Tools")
            self.resize(570, 530)
            self.setWindowFlags(self.windowFlags() | QtCore.Qt.Window)

            # State — initialised before _build_ui so callbacks can reference them safely
            self._json_mats:        list[dict] = []
            self._json_texs:        list[dict] = []
            self._selected_tex:     str        = ""
            self._json_uv_defaults: dict       = {"R": 1.0, "G": 1.0, "B": 0.0, "A": 0.0}

            # Widget references set to None until _build_ui creates them,
            # so callbacks called before Task 5/6 are implemented don't raise AttributeError.
            self._tex_list = None
            self._mat_list = None

            self._build_ui()
            self._refresh_json()
            self._refresh_textures()
            self._refresh_materials()

        def _build_ui(self):
            root = QtWidgets.QVBoxLayout(self)
            tabs = QtWidgets.QTabWidget()
            root.addWidget(tabs)

            mat_widget = QtWidgets.QWidget()
            tabs.addTab(mat_widget, "Material")
            mat_root = QtWidgets.QVBoxLayout(mat_widget)

            self._btn_check_id = QtWidgets.QPushButton("Check Multi/Sub with non-matching ID")
            self._btn_check_id.setFixedHeight(34)
            self._btn_check_id.setStyleSheet("font-weight: bold;")
            self._btn_check_id.setToolTip(
                "Check each selected object's Multi/Sub-Object material: every "
                "sub-material name must end with its slot ID zero-padded to two "
                "digits (ID 4 -> '...04'). Lists any master materials that don't "
                "fully match. Single materials are skipped.")
            self._btn_check_id.clicked.connect(lambda: _call_ms("HW_CheckNonMatchingID()"))
            mat_root.addWidget(self._btn_check_id)

            outer = QtWidgets.QHBoxLayout()
            mat_root.addLayout(outer)
            self._build_left(outer)
            self._build_right(outer)

            mod_widget = QtWidgets.QWidget()
            tabs.addTab(mod_widget, "Modelling")
            self._build_modelling(mod_widget)

        def _build_left(self, outer):
            QtWidgets, _, _ = _qt_modules()
            left = QtWidgets.QVBoxLayout()
            outer.addLayout(left, stretch=3)

            # ── JSON material list ──────────────────────────────────────────
            hdr = QtWidgets.QHBoxLayout()
            hdr.addWidget(QtWidgets.QLabel("<b>Material:</b>"))
            hdr.addStretch()
            self._btn_refresh_json = QtWidgets.QPushButton("Refresh")
            self._btn_refresh_json.setFixedHeight(22)
            self._btn_refresh_json.setToolTip(
                "Reload the material-instance (.json) list from the matins folder.")
            self._btn_clear_mat = QtWidgets.QPushButton("Clear")
            self._btn_clear_mat.setFixedHeight(22)
            self._btn_clear_mat.setStyleSheet("")
            self._btn_clear_mat.setToolTip(
                "Delete all files in the matins folder (asks for confirmation).")
            hdr.addWidget(self._btn_refresh_json)
            hdr.addWidget(self._btn_clear_mat)
            left.addLayout(hdr)

            self._mat_json_list = QtWidgets.QListWidget()
            self._mat_json_list.setMaximumHeight(110)
            left.addWidget(self._mat_json_list)

            left.addWidget(_hsep())

            # ── UV ScaleOffset ──────────────────────────────────────────────
            uv_hdr = QtWidgets.QHBoxLayout()
            uv_hdr.addWidget(QtWidgets.QLabel("<b>UV - ScaleOffset</b>"))
            uv_hdr.addStretch()
            self._btn_reset_uv = QtWidgets.QPushButton("Reset")
            self._btn_reset_uv.setFixedHeight(22)
            self._btn_reset_uv.setToolTip(
                "Reset R/G/B/A UV ScaleOffset to the selected material's defaults "
                "(or 1/1/0/0).")
            uv_hdr.addWidget(self._btn_reset_uv)
            left.addLayout(uv_hdr)

            self._uv_fields: dict = {}
            for lbl, default in (("R", 1.0), ("G", 1.0), ("B", 0.0), ("A", 0.0)):
                row = QtWidgets.QHBoxLayout()
                lbl_w = QtWidgets.QLabel(lbl)
                lbl_w.setFixedWidth(20)
                row.addWidget(lbl_w)
                spin = QtWidgets.QDoubleSpinBox()
                spin.setDecimals(4)
                spin.setSingleStep(0.1)
                spin.setRange(-9999.0, 9999.0)
                spin.setValue(default)
                row.addWidget(spin)
                left.addLayout(row)
                self._uv_fields[lbl] = spin

            left.addWidget(_hsep())

            # ── Texture list ────────────────────────────────────────────────────────────────────
            tex_hdr = QtWidgets.QHBoxLayout()
            tex_hdr.addWidget(QtWidgets.QLabel("<b>Textures:</b>"))
            tex_hdr.addStretch()
            self._btn_refresh_tex = QtWidgets.QPushButton("Refresh")
            self._btn_refresh_tex.setFixedHeight(22)
            self._btn_refresh_tex.setToolTip(
                "Reload the texture list from the textures folder.")
            self._btn_clear_tex = QtWidgets.QPushButton("Clear")
            self._btn_clear_tex.setFixedHeight(22)
            self._btn_clear_tex.setStyleSheet("")
            self._btn_clear_tex.setToolTip(
                "Delete all files in the textures folder (asks for confirmation).")
            tex_hdr.addWidget(self._btn_refresh_tex)
            tex_hdr.addWidget(self._btn_clear_tex)
            left.addLayout(tex_hdr)

            self._tex_list = QtWidgets.QListWidget()
            self._tex_list.setMaximumHeight(110)
            left.addWidget(self._tex_list)

            left.addStretch()

            self._btn_assign = QtWidgets.QPushButton("Assign")
            self._btn_assign.setFixedHeight(36)
            self._btn_assign.setStyleSheet("font-weight: bold;")
            self._btn_assign.setToolTip(
                "Apply the selected Material or Texture to the selected Max material, "
                "using the R/G/B/A UV ScaleOffset above. Becomes 'Update' (tweaks only "
                "tiling/offset) when that texture is already assigned.")
            left.addWidget(self._btn_assign)

            self._left_bottom = left

            # ── Wire ────────────────────────────────────────────────────────
            self._btn_refresh_json.clicked.connect(self._refresh_json)
            self._btn_clear_mat.clicked.connect(self._on_clear_mat)
            self._btn_reset_uv.clicked.connect(self._on_reset_uv)
            self._mat_json_list.itemSelectionChanged.connect(self._on_json_mat_select)
            self._btn_refresh_tex.clicked.connect(self._refresh_textures)
            self._btn_clear_tex.clicked.connect(self._on_clear_tex)
            self._tex_list.itemSelectionChanged.connect(self._on_tex_select)
            self._btn_assign.clicked.connect(self._on_assign)

        def _build_right(self, outer):
            QtWidgets, _, _ = _qt_modules()
            right = QtWidgets.QVBoxLayout()
            outer.addLayout(right, stretch=2)

            hdr = QtWidgets.QHBoxLayout()
            hdr.addWidget(QtWidgets.QLabel("<b>Max Material:</b>"))
            hdr.addStretch()
            self._btn_refresh_mats = QtWidgets.QPushButton("Refresh")
            self._btn_refresh_mats.setFixedHeight(22)
            self._btn_refresh_mats.setToolTip(
                "Rescan the scene for Standard / Physical / Multi-Sub materials. "
                "Multi-Sub materials show their sub-materials indented beneath them.")
            hdr.addWidget(self._btn_refresh_mats)
            right.addLayout(hdr)

            self._mat_list = QtWidgets.QListWidget()
            self._mat_list.setSelectionMode(
                QtWidgets.QAbstractItemView.SingleSelection)
            right.addWidget(self._mat_list)

            self._btn_refresh_mats.clicked.connect(self._refresh_materials)
            self._mat_list.itemSelectionChanged.connect(self._refresh_assign_btn)

        def _build_modelling(self, parent_widget):
            QtWidgets, QtCore, _ = _qt_modules()

            layout = QtWidgets.QVBoxLayout(parent_widget)
            layout.setContentsMargins(8, 8, 8, 8)
            layout.setSpacing(6)

            def _btn(label, callback, height=34, tip=""):
                b = QtWidgets.QPushButton(label)
                b.setFixedHeight(height)
                if tip:
                    b.setToolTip(tip)
                b.clicked.connect(callback)
                return b

            def _collapsible(title, parent_layout, expanded=True):
                """Add a collapsible section; returns the inner QVBoxLayout."""
                hdr = QtWidgets.QPushButton(("▼  " if expanded else "▶  ") + title)
                hdr.setCheckable(True)
                hdr.setChecked(expanded)
                hdr.setStyleSheet(
                    "QPushButton { text-align: left; padding: 4px 6px; font-weight: bold; "
                    "background-color: #4a4a4a; color: #cccccc; border: none; } "
                    "QPushButton:hover { background-color: #565656; }"
                )
                inner = QtWidgets.QWidget()
                inner_layout = QtWidgets.QVBoxLayout(inner)
                inner_layout.setContentsMargins(4, 4, 4, 4)
                inner_layout.setSpacing(6)
                inner.setVisible(expanded)
                def _toggle(checked, _h=hdr, _w=inner, _t=title):
                    _w.setVisible(checked)
                    _h.setText(("▼  " if checked else "▶  ") + _t)
                hdr.toggled.connect(_toggle)
                parent_layout.addWidget(hdr)
                parent_layout.addWidget(inner)
                return inner_layout

            # ── Top modelling buttons ───────────────────────────────────────
            layout.addWidget(_btn(
                "Rename / Sort", lambda: _call_ms("HW_RenameSort()"),
                tip="Sort the selected objects by their trailing number and renumber "
                    "each name group as base_01, base_02… Then renames their "
                    "references/instances by layer to match."))
            layout.addWidget(_btn(
                "Collapse Modifier", lambda: _call_ms("HW_CollapseModifier()"),
                tip="Collapse the modifier stack of each selected geometry object to "
                    "an editable base. Selection must be mesh/geometry."))

            row1 = QtWidgets.QHBoxLayout()
            row1.addWidget(_btn(
                "Attach", lambda: _call_ms("HW_Attach()"),
                tip="Attach all selected geometry into the first selected object, "
                    "converting it to Editable Poly and keeping its name."))
            row1.addWidget(_btn(
                "Detach", self._on_detach,
                tip="Detach the current face/polygon selection of one Editable Poly "
                    "object — as a separate element or as a clone (asks which)."))
            layout.addLayout(row1)

            row2 = QtWidgets.QHBoxLayout()
            row2.addWidget(_btn(
                "Select Ref / Inst", lambda: _call_ms("HW_SelectRefInst()"),
                tip="Select all geometry that references or instances the single "
                    "selected source object."))
            row2.addWidget(_btn(
                "Check Non-reference", lambda: _call_ms("HW_CheckNonReference()"),
                tip="From the selected objects, keep only those that are neither a "
                    "reference/instance of another object nor referenced by one "
                    "(stand-alone geometry), and update the selection to just those."))
            layout.addLayout(row2)

            layout.addWidget(_btn(
                "Create Windows Glass", lambda: _call_ms("HW_CreateWindowsGlass()"),
                tip="Detach Material-ID-1 faces of each selected Editable Poly into a "
                    "'_glass' object, then re-create matching glass on every "
                    "reference/instance. Objects must be collapsed Editable Poly."))

            layout.addWidget(_hsep())

            # ── Source Replace (collapsible) ────────────────────────────────
            sr_inner = _collapsible("Source Replace", layout)

            sr_row = QtWidgets.QHBoxLayout()

            repl_layout = QtWidgets.QVBoxLayout()
            repl_layout.addWidget(QtWidgets.QLabel("<b>Replacer:</b>"))
            self._replacer_list = QtWidgets.QListWidget()
            self._replacer_list.setMaximumHeight(90)
            repl_layout.addWidget(self._replacer_list)
            repl_btns = QtWidgets.QHBoxLayout()
            btn_pick  = QtWidgets.QPushButton("Pick")
            btn_rclr  = QtWidgets.QPushButton("Clear")
            btn_pick.setFixedHeight(22)
            btn_rclr.setFixedHeight(22)
            btn_pick.setToolTip(
                "Add the objects currently selected in the viewport to the replacer "
                "list (these are the objects that will be swapped).")
            btn_rclr.setToolTip("Empty the replacer list.")
            repl_btns.addWidget(btn_pick)
            repl_btns.addWidget(btn_rclr)
            repl_layout.addLayout(repl_btns)
            btn_export = QtWidgets.QPushButton("Export Source Modules")
            btn_export.setFixedHeight(22)
            btn_export.setToolTip(
                "Export each selected geometry object to its own .fbx in the mesh "
                "folder (one file per object, named after the object).")
            repl_layout.addWidget(btn_export)
            repl_layout.addStretch()
            sr_row.addLayout(repl_layout, stretch=2)

            fbx_layout = QtWidgets.QVBoxLayout()
            fbx_hdr = QtWidgets.QHBoxLayout()
            fbx_hdr.addWidget(QtWidgets.QLabel("<b>FBX Mesh:</b>"))
            fbx_hdr.addStretch()
            btn_fbx_refresh = QtWidgets.QPushButton("Refresh")
            btn_fbx_clear   = QtWidgets.QPushButton("Clear")
            btn_fbx_refresh.setFixedHeight(22)
            btn_fbx_clear.setFixedHeight(22)
            btn_fbx_refresh.setToolTip(
                "Reload the .fbx list from the mesh folder.")
            btn_fbx_clear.setToolTip(
                "Delete the selected .fbx files, or all of them if none are selected "
                "(asks for confirmation).")
            fbx_hdr.addWidget(btn_fbx_refresh)
            fbx_hdr.addWidget(btn_fbx_clear)
            fbx_layout.addLayout(fbx_hdr)
            self._fbx_list  = QtWidgets.QListWidget()
            self._fbx_list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
            self._fbx_paths = {}
            fbx_layout.addWidget(self._fbx_list)
            sr_row.addLayout(fbx_layout, stretch=3)

            sr_inner.addLayout(sr_row)

            btn_replace = QtWidgets.QPushButton("Replace")
            btn_replace.setFixedHeight(34)
            btn_replace.setStyleSheet("font-weight: bold;")
            btn_replace.setToolTip(
                "Swap each picked object's geometry with its name-matched FBX file "
                "(counts must be equal and every picked name must have a matching "
                "FBX). Instances/references and material IDs are preserved.")
            sr_inner.addWidget(btn_replace)

            layout.addWidget(_hsep())

            # ── File I/O (collapsible) ──────────────────────────────────────
            fio_inner = _collapsible("File I/O", layout)

            btn_export_scene = QtWidgets.QPushButton("Export Building Scene")
            btn_export_scene.setFixedHeight(40)
            btn_export_scene.setStyleSheet("font-weight: bold;")
            btn_export_scene.setToolTip(
                "Bake Array-modifier references in '_Part_Divisions' into real "
                "instances of their Source_Modules originals, tidy the layers, then "
                "export all visible objects to io\\temp_building_scene.fbx.")
            fio_inner.addWidget(btn_export_scene)

            row_io = QtWidgets.QHBoxLayout()
            btn_import     = QtWidgets.QPushButton("Import")
            btn_export_sel = QtWidgets.QPushButton("Export Selected")
            btn_import.setFixedHeight(30)
            btn_export_sel.setFixedHeight(30)
            btn_import.setToolTip(
                "Import io\\temp.fbx and re-assign matching pre-existing scene "
                "materials (by name) to the imported objects, remapping face IDs.")
            btn_export_sel.setToolTip(
                "Export the current selection to io\\temp.fbx (instances preserved, "
                "no triangulation).")
            row_io.addWidget(btn_import)
            row_io.addWidget(btn_export_sel)
            fio_inner.addLayout(row_io)

            layout.addStretch()

            # Wire callbacks
            btn_pick.clicked.connect(self._on_pick_replacers)
            btn_rclr.clicked.connect(self._on_clear_replacer)
            btn_export.clicked.connect(self._on_export_source_modules)
            btn_fbx_refresh.clicked.connect(self._refresh_fbx)
            btn_fbx_clear.clicked.connect(self._on_clear_fbx)
            btn_replace.clicked.connect(self._on_source_replace)
            btn_export_scene.clicked.connect(self._on_export_building_scene)
            btn_import.clicked.connect(lambda: _call_ms("HW_ImportTemp()"))
            btn_export_sel.clicked.connect(lambda: _call_ms("HW_ExportSelected()"))

            self._refresh_fbx()

        def _on_export_building_scene(self):
            from pymxs import runtime as rt
            _ensure_ms()
            result = rt.execute("HW_ExportBuildingScene()")
            if result is False:
                pass  # MaxScript already showed messageBox on error

        def _on_detach(self):
            QtWidgets, QtCore, _ = _qt_modules()
            dlg = QtWidgets.QDialog(self)
            dlg.setWindowTitle("Detach")
            dlg.setWindowFlags(dlg.windowFlags() | QtCore.Qt.Window)
            dlg.resize(200, 70)
            row = QtWidgets.QHBoxLayout(dlg)
            btn_elem  = QtWidgets.QPushButton("Element")
            btn_clone = QtWidgets.QPushButton("Clone")
            btn_elem.setFixedHeight(34)
            btn_clone.setFixedHeight(34)
            btn_elem.setToolTip(
                "Detach the selected faces as a new object, removing them from the "
                "source mesh.")
            btn_clone.setToolTip(
                "Detach a copy of the selected faces as a new object, leaving the "
                "source mesh intact.")
            row.addWidget(btn_elem)
            row.addWidget(btn_clone)
            btn_elem.clicked.connect(lambda: (_call_ms("HW_Detach false"), dlg.accept()))
            btn_clone.clicked.connect(lambda: (_call_ms("HW_Detach true"),  dlg.accept()))
            dlg.exec()

        def _refresh_fbx(self):
            self._fbx_paths = _load_fbx_list()
            self._fbx_list.clear()
            for name in self._fbx_paths:
                self._fbx_list.addItem(name)

        def _on_pick_replacers(self):
            from pymxs import runtime as rt
            nodes = list(rt.selection)
            if not nodes:
                return
            existing = {self._replacer_list.item(i).text()
                        for i in range(self._replacer_list.count())}
            for node in nodes:
                name = str(node.name)
                if name not in existing:
                    self._replacer_list.addItem(name)
                    existing.add(name)

        def _on_clear_replacer(self):
            self._replacer_list.clear()

        def _on_clear_fbx(self):
            QtWidgets, _, _ = _qt_modules()
            selected = self._fbx_list.selectedItems()
            if selected:
                # Delete only selected FBX files
                reply = QtWidgets.QMessageBox.question(
                    self, "Clear FBX",
                    f"Delete {len(selected)} selected file(s)?",
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                )
                if reply != QtWidgets.QMessageBox.Yes:
                    return
                for item in selected:
                    path = self._fbx_paths.get(item.text(), "")
                    try:
                        if path and os.path.isfile(path):
                            os.remove(path)
                    except Exception:
                        pass
            else:
                # No selection — delete all
                reply = QtWidgets.QMessageBox.question(
                    self, "Clear FBX folder",
                    "Delete all files?",
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                )
                if reply != QtWidgets.QMessageBox.Yes:
                    return
                if os.path.isdir(MESH_ROOT):
                    for entry in os.listdir(MESH_ROOT):
                        full = os.path.join(MESH_ROOT, entry)
                        try:
                            if os.path.isfile(full):
                                os.remove(full)
                        except Exception:
                            pass
            self._refresh_fbx()

        def _on_export_source_modules(self):
            QtWidgets, _, _ = _qt_modules()
            from pymxs import runtime as rt
            _ensure_ms()
            mesh_root_ms = MESH_ROOT.replace("\\", "\\\\")
            count = rt.execute(f'HW_ExportSourceModules @"{MESH_ROOT}"')
            self._refresh_fbx()
            if count and int(str(count)) > 0:
                QtWidgets.QMessageBox.information(
                    self, "Export Source Modules",
                    f"Exported {count} object(s)."
                )

        def _on_source_replace(self):
            QtWidgets, _, _ = _qt_modules()
            from pymxs import runtime as rt

            n_rep = self._replacer_list.count()
            if n_rep == 0:
                QtWidgets.QMessageBox.warning(self, "Source Replace", "No objects picked.")
                return

            selected_fbx = self._fbx_list.selectedItems()
            n_fbx = len(selected_fbx)
            if n_fbx == 0:
                QtWidgets.QMessageBox.warning(self, "Source Replace", "No FBX files selected.")
                return

            replacer_names = [self._replacer_list.item(i).text() for i in range(n_rep)]
            fbx_names      = {item.text() for item in selected_fbx}

            # Count must match
            if n_rep != n_fbx:
                QtWidgets.QMessageBox.warning(
                    self, "Source Replace",
                    f"{n_rep} object(s) picked but {n_fbx} FBX file(s) selected.\n"
                    "Counts must be equal."
                )
                return

            # Every picked object must have a matching FBX by name
            unmatched = [n for n in replacer_names if n not in fbx_names]
            if unmatched:
                QtWidgets.QMessageBox.warning(
                    self, "Source Replace",
                    "No matching FBX for:\n" + "\n".join(f"  {n}" for n in unmatched)
                )
                return

            # Execute — one replacement per name-matched pair
            _ensure_ms()
            for rep_name in replacer_names:
                fbx_path = self._fbx_paths.get(rep_name, "")
                if not fbx_path:
                    continue
                rt._mgc_obj_name = rep_name
                rt.execute("HW_ReplacerNode = getNodeByName _mgc_obj_name")
                rt._mgc_fbx_path = fbx_path
                rt.execute("HW_SourceReplace _mgc_fbx_path")

            self._replacer_list.clear()
            self._fbx_list.clearSelection()

        def _refresh_json(self):
            self._json_mats = _load_json_materials()
            self._mat_json_list.clear()
            for m in self._json_mats:
                self._mat_json_list.addItem(m.get("name", "???"))
            self._refresh_assign_btn()

        def _on_clear_mat(self):
            QtWidgets, _, _ = _qt_modules()
            import shutil
            reply = QtWidgets.QMessageBox.question(
                self, "Clear Material folder",
                "Delete all files?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            )
            if reply != QtWidgets.QMessageBox.Yes:
                return
            if not os.path.isdir(MAT_ROOT):
                self._refresh_json()
                return
            for entry in os.listdir(MAT_ROOT):
                full = os.path.join(MAT_ROOT, entry)
                try:
                    if os.path.isfile(full):
                        os.remove(full)
                    elif os.path.isdir(full):
                        shutil.rmtree(full)
                except Exception:
                    pass
            self._refresh_json()

        def _on_reset_uv(self):
            for lbl, val in self._json_uv_defaults.items():
                self._uv_fields[lbl].setValue(val)

        def _on_json_mat_select(self):
            if self._tex_list is not None:
                self._tex_list.clearSelection()
            self._selected_tex = ""
            items = self._mat_json_list.selectedItems()
            if not items:
                self._refresh_assign_btn()
                return
            idx = self._mat_json_list.row(items[0])
            if not (0 <= idx < len(self._json_mats)):
                self._refresh_assign_btn()
                return
            uv_vec = self._json_mats[idx].get("vectors", {}).get("UV - ScaleOffset") or {}
            defaults = {
                "R": uv_vec.get("r", 1.0), "G": uv_vec.get("g", 1.0),
                "B": uv_vec.get("b", 0.0), "A": uv_vec.get("a", 0.0),
            }
            self._json_uv_defaults = defaults
            for lbl, val in defaults.items():
                self._uv_fields[lbl].setValue(val)
            self._refresh_assign_btn()

        def _refresh_textures(self):
            self._json_texs = _load_textures()
            self._tex_list.clear()
            for t in self._json_texs:
                self._tex_list.addItem(t["name"])
            self._selected_tex = ""
            self._refresh_assign_btn()

        def _on_clear_tex(self):
            QtWidgets, _, _ = _qt_modules()
            import shutil
            reply = QtWidgets.QMessageBox.question(
                self, "Clear Textures folder",
                "Delete all files?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            )
            if reply != QtWidgets.QMessageBox.Yes:
                return
            if not os.path.isdir(TEX_ROOT):
                self._refresh_textures()
                return
            for entry in os.listdir(TEX_ROOT):
                full = os.path.join(TEX_ROOT, entry)
                try:
                    if os.path.isfile(full):
                        os.remove(full)
                    elif os.path.isdir(full):
                        shutil.rmtree(full)
                except Exception:
                    pass
            self._refresh_textures()

        def _on_tex_select(self):
            self._mat_json_list.clearSelection()
            self._selected_tex = ""
            items = self._tex_list.selectedItems()
            if items:
                idx = self._tex_list.row(items[0])
                if 0 <= idx < len(self._json_texs):
                    self._selected_tex = self._json_texs[idx]["path"]
            self._refresh_assign_btn()

        def _selected_mat_obj(self):
            """Return the mat object for the currently selected Max Material item."""
            _, QtCore, _ = _qt_modules()
            if self._mat_list is None:
                return None
            sel = self._mat_list.selectedItems()
            if not sel:
                return None
            return sel[0].data(QtCore.Qt.UserRole)

        def _on_assign(self):
            QtWidgets, _, _ = _qt_modules()
            mat = self._selected_mat_obj()
            if mat is None:
                QtWidgets.QMessageBox.warning(
                    self, "Hotwheel Tools", "Select a Max material first.")
                return

            json_sel = self._mat_json_list.selectedItems()
            tex_sel  = self._tex_list.selectedItems()

            if not json_sel and not tex_sel:
                QtWidgets.QMessageBox.warning(
                    self, "Hotwheel Tools", "Select a Material or Texture first.")
                return

            r = self._uv_fields["R"].value()
            g = self._uv_fields["G"].value()
            b = self._uv_fields["B"].value()
            a = self._uv_fields["A"].value()

            if json_sel:
                idx = self._mat_json_list.row(json_sel[0])
                bc_path, n_path = _find_mat_textures(self._json_mats[idx])
                if not bc_path and not n_path:
                    QtWidgets.QMessageBox.warning(
                        self, "Hotwheel Tools", "No textures found in material JSON.")
                    return
                _assign(mat, bc_path, n_path, r, g, b, a)
            else:
                path = self._selected_tex
                if not path or not os.path.isfile(path):
                    QtWidgets.QMessageBox.warning(
                        self, "Hotwheel Tools", "Texture file not found.")
                    return
                if _is_update_mode(mat, path):
                    _update_uv(mat, r, g, b, a)
                else:
                    _assign(mat, path, None, r, g, b, a)

            self._refresh_assign_btn()

        def _refresh_materials(self):
            QtWidgets, QtCore, _ = _qt_modules()
            self._mat_list.clear()
            for display_name, mat_obj in _list_scene_materials():
                item = QtWidgets.QListWidgetItem(display_name)
                item.setData(QtCore.Qt.UserRole, mat_obj)
                if mat_obj is None:
                    item.setFlags(item.flags() & ~QtCore.Qt.ItemIsSelectable)
                self._mat_list.addItem(item)
            self._refresh_assign_btn()

        def _refresh_assign_btn(self):
            mat = self._selected_mat_obj()
            if (mat is not None and self._selected_tex
                    and _is_update_mode(mat, self._selected_tex)):
                self._btn_assign.setText("Update")
            else:
                self._btn_assign.setText("Assign")
            self._btn_assign.setStyleSheet("font-weight: bold;")

    _HotwheelDialog = _HotwheelDialog
    return _HotwheelDialog


# ── Execution: Show dialog when MacroScript calls ExecuteFile ────────────────
# This is called by HW3_Tools.mcr via python.ExecuteFile
try:
    show()
except Exception as e:
    print(f"[HW3 Tools] Error showing dialog: {e}")
