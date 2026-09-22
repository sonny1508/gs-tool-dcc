"""
GS File Exporter - FBX export for artists, as one file or one file per object.

PySide2 (Maya 2022) / PySide6 (Maya 2026) window. GSPipeline runs this file
with __name__ == '__main__', which opens the window.
"""

import contextlib
import html
import os
import sys

import maya.cmds as cmds
import maya.OpenMayaUI as omui

try:                                    # Maya 2025+
    from PySide6 import QtCore, QtWidgets
    from shiboken6 import wrapInstance
    QT_BINDING = "PySide6"
except ImportError:                     # Maya 2022-2024
    from PySide2 import QtCore, QtWidgets
    from shiboken2 import wrapInstance
    QT_BINDING = "PySide2"

# GSPipeline launches tools by exec'ing scripts, so _core is not on sys.path.
# Put it there once, the same way 02_Normals reaches gs_normal_core.
_CORE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_core')
if _CORE not in sys.path:
    sys.path.append(_CORE)

import gs_fbx  # noqa: E402  (must follow the sys.path setup)

# The FBX preset this tool exports with. gs_fbx resets the plug-in before
# applying it, so settings left behind by another tool can no longer leak in.
FBX_PRESET = 'asset'

# Name the surviving UV set gets when "Keep UVChannel2 only" is on.
UV2_NAME = "UVChannel2"

OBJECT_NAME = "GSFileExporterWindow"

# optionVars that remember the artist's settings between sessions.
_OPT_PREFIX = "gs_file_export_"


def _short(path):
    return path.split('|')[-1]


# ---------------------------------------------------------------------------
# Gathering
# ---------------------------------------------------------------------------
# Every function below takes `log(message, level="info")`; level is one of
# info / ok / warn / error and only changes how the window colours the line.

def collect(export_all, log):
    """
    Return (roots, mesh_objects) for the Selection/Everything mode.

    roots are the transforms the artist picked (or every transform in the
    scene); mesh_objects are the full paths of every mesh transform in or
    under them. Returns None, after logging why, when there is nothing to do.
    """
    if export_all:
        log("Gathering all mesh objects in the scene...")
        roots = cmds.ls(type="transform", long=True)
    else:
        log("Gathering selected mesh objects...")
        roots = cmds.ls(selection=True, long=True)

    if not roots:
        log("Nothing selected." if not export_all else "No objects found in the scene.", "warn")
        return None

    # Process groups to get all mesh objects (without inheriting names)
    mesh_objects = []
    for obj_path in roots:
        # Check if the selected object is itself a mesh
        if cmds.objectType(obj_path, isType="transform"):
            shapes = cmds.listRelatives(obj_path, shapes=True, fullPath=True, type="mesh")
            if shapes:
                mesh_objects.append(obj_path)

        # Find all mesh children but keep their full paths
        children = cmds.listRelatives(obj_path, allDescendents=True, fullPath=True, type="transform") or []
        for child_path in children:
            shapes = cmds.listRelatives(child_path, shapes=True, fullPath=True, type="mesh")
            if shapes and child_path not in mesh_objects:
                mesh_objects.append(child_path)

    # Report groups that only contribute through their children
    group_objects = []
    for obj_path in roots:
        if obj_path not in mesh_objects:
            children = cmds.listRelatives(obj_path, allDescendents=True, fullPath=True, type="transform") or []
            if any(child_path in mesh_objects for child_path in children):
                group_objects.append(_short(obj_path))

    if group_objects:
        log("Groups processed for their children:")
        for obj in group_objects:
            log("  - {}".format(obj))

    if not mesh_objects:
        log("No mesh objects to export.", "warn")
        return None

    return roots, mesh_objects


def _top_parents(mesh_objects):
    """The top-most ancestor of each mesh, deduplicated, in first-seen order."""
    top_parents = []
    for obj_path in mesh_objects:
        current = obj_path
        while True:
            parent = cmds.listRelatives(current, parent=True, fullPath=True)
            if not parent:
                break
            current = parent[0]
        if current not in top_parents:
            top_parents.append(current)
    return top_parents


# ---------------------------------------------------------------------------
# UVChannel2 only
# ---------------------------------------------------------------------------

def _keep_uv2_only(mesh_objects, state, log):
    """
    Reduce every mesh to a single UV set named UVChannel2, holding what was in
    the *second* UV set by position. Meshes with one UV set keep it, renamed.

    The second set is copied into the first rather than the others simply
    deleted, because Maya refuses to delete a mesh's first (default) UV set.

    Edits the meshes in place: only call it through _uv2_only(), which undoes
    the whole thing once the export is written. Sets state["changed"] before
    the first edit, so a failure part-way through still gets undone.
    """
    moved = single = empty = 0
    seen = set()
    for obj_path in mesh_objects:
        shapes = cmds.listRelatives(obj_path, shapes=True, noIntermediate=True,
                                    fullPath=True, type="mesh") or []
        for shape in shapes:
            if shape in seen:
                continue
            seen.add(shape)

            uv_sets = cmds.polyUVSet(shape, query=True, allUVSets=True) or []
            if not uv_sets:
                empty += 1
                log("  {} has no UV sets, left as-is.".format(_short(obj_path)), "warn")
                continue

            state["changed"] = True
            first = uv_sets[0]
            if len(uv_sets) >= 2:
                cmds.polyUVSet(shape, copy=True, uvSet=uv_sets[1], newUVSet=first)
                moved += 1
            else:
                single += 1

            cmds.polyUVSet(shape, currentUVSet=True, uvSet=first)
            for uv_set in uv_sets[1:]:
                cmds.polyUVSet(shape, delete=True, uvSet=uv_set)
            if first != UV2_NAME:
                cmds.polyUVSet(shape, rename=True, uvSet=first, newUVSet=UV2_NAME)

    log("Kept {} only: {} meshes from UV set 2, {} with a single UV set kept as-is{}.".format(
        UV2_NAME, moved, single,
        ", {} without UVs".format(empty) if empty else ""))


@contextlib.contextmanager
def _uv2_only(mesh_objects, enabled, log):
    """
    Strip the meshes down to UVChannel2 for the duration of the block, then
    put the original UV sets back by undoing the edit as one chunk.

    Working on the originals, not duplicates, keeps the node names in the FBX
    identical to the scene.
    """
    if not enabled:
        yield
        return

    state = {"changed": False}
    cmds.undoInfo(openChunk=True, chunkName="gs_file_export_uv2")
    try:
        _keep_uv2_only(mesh_objects, state, log)
        yield
    finally:
        cmds.undoInfo(closeChunk=True)
        # Only undo when the chunk actually holds our edits - undoing an
        # empty chunk would undo the artist's previous action instead.
        if state["changed"]:
            cmds.undo()
            log("Original UV sets restored.")


def uv2_allowed(log):
    """The UV2 option needs undo to put the scene back afterwards."""
    if cmds.undoInfo(q=True, state=True):
        return True
    log("Undo is disabled in this scene, so the original UV sets could not be "
        "restored after export. Turn undo on, or untick '{} only'.".format(UV2_NAME), "error")
    return False


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

def _export(file_path, log):
    label = os.path.basename(file_path)
    try:
        gs_fbx.export_selection(file_path, preset=FBX_PRESET)
        log("Exported: {}".format(label), "ok")
        return True
    except Exception as e:
        log("Error exporting {}: {}".format(label, str(e)), "error")
        return False


def _log_settings(uv2_only, log):
    log("")
    log("Export settings: FBX 2020, Z up, centimeters, smoothing groups.")
    log("Excluded: animation, cameras, lights, audio, embedded media.")
    if uv2_only:
        log("UVs: {} only.".format(UV2_NAME))


@contextlib.contextmanager
def _keep_selection():
    selection = cmds.ls(selection=True, long=True)
    try:
        yield
    finally:
        if selection:
            cmds.select(selection, replace=True)
        else:
            cmds.select(clear=True)


def export_single(collected, export_all, file_path, uv2_only, log):
    """Export everything collected together into one FBX file."""
    roots, mesh_objects = collected

    # Selecting the roots with their hierarchy keeps the groups in the file.
    if export_all:
        roots = _top_parents(mesh_objects)

    log("Exporting {} mesh objects to: {}".format(len(mesh_objects), file_path))
    with _keep_selection():
        with _uv2_only(mesh_objects, uv2_only, log):
            cmds.select(roots, hierarchy=True, replace=True)
            ok = _export(file_path, log)

    log("Export complete." if ok else "Export failed.", "ok" if ok else "error")
    _log_settings(uv2_only, log)


def export_separate(collected, export_all, export_folder, by_parent, uv2_only, log):
    """Export one FBX file per mesh (or per top-level parent) into a folder."""
    roots, mesh_objects = collected

    with _keep_selection():
        with _uv2_only(mesh_objects, uv2_only, log):
            if by_parent:
                # Everything mode: one file per top-level parent. Selection
                # mode: the selected objects are the parents.
                items = _top_parents(mesh_objects) if export_all else roots
                log("Exporting {} parents to: {}".format(len(items), export_folder))
            else:
                items = mesh_objects
                log("Exporting {} individual mesh objects to: {}".format(len(items), export_folder))

            done = 0
            for path in items:
                cmds.select(path, hierarchy=by_parent, replace=True)
                if _export(os.path.join(export_folder, "{}.fbx".format(_short(path))), log):
                    done += 1

    failed = len(items) - done
    if failed:
        log("Export finished: {} written, {} failed.".format(done, failed), "error")
    else:
        log("Export complete: {} files written.".format(done), "ok")
    _log_settings(uv2_only, log)


# ---------------------------------------------------------------------------
# Window
# ---------------------------------------------------------------------------

def _maya_main_window():
    pointer = omui.MQtUtil.mainWindow()
    return wrapInstance(int(pointer), QtWidgets.QWidget)


def _opt_get(name, default):
    key = _OPT_PREFIX + name
    if cmds.optionVar(exists=key):
        return cmds.optionVar(q=key)
    return default


def _opt_set(name, value):
    key = _OPT_PREFIX + name
    if isinstance(value, str):
        cmds.optionVar(stringValue=(key, value))
    else:
        cmds.optionVar(intValue=(key, int(value)))


class ExporterWindow(QtWidgets.QDialog):

    LOG_COLOURS = {"ok": "#7ec87e", "warn": "#e0b64c", "error": "#e06c6c"}

    def __init__(self, parent=None):
        super(ExporterWindow, self).__init__(parent or _maya_main_window())
        self.setObjectName(OBJECT_NAME)
        self.setWindowTitle("GS File Exporter")
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.Tool)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self._build()
        self._load_settings()
        self.resize(560, 520)
        self.setMinimumWidth(460)

    # -- layout -------------------------------------------------------------
    def _build(self):
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(10)

        # Settings shared by both export buttons. A form layout keeps the
        # labels right-aligned in one column and the fields in another.
        settings_box = QtWidgets.QGroupBox("Settings")
        form = QtWidgets.QFormLayout(settings_box)
        form.setLabelAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        form.setFieldGrowthPolicy(QtWidgets.QFormLayout.AllNonFixedFieldsGrow)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(8)

        dir_row = QtWidgets.QHBoxLayout()
        dir_row.setSpacing(4)
        self.dir_edit = QtWidgets.QLineEdit()
        self.dir_edit.setPlaceholderText("Folder for separate FBXs (also where 'One FBX' starts)")
        dir_row.addWidget(self.dir_edit, 1)
        browse_button = QtWidgets.QPushButton("Browse...")
        browse_button.clicked.connect(self._on_browse)
        dir_row.addWidget(browse_button)
        form.addRow("Export To:", dir_row)

        mode_row = QtWidgets.QHBoxLayout()
        mode_row.setSpacing(16)
        self.selection_radio = QtWidgets.QRadioButton("Selection")
        self.everything_radio = QtWidgets.QRadioButton("Everything")
        self.selection_radio.setChecked(True)
        mode_group = QtWidgets.QButtonGroup(self)
        mode_group.addButton(self.selection_radio)
        mode_group.addButton(self.everything_radio)
        mode_row.addWidget(self.selection_radio)
        mode_row.addWidget(self.everything_radio)
        mode_row.addStretch(1)
        form.addRow("Export:", mode_row)

        self.uv2_check = QtWidgets.QCheckBox("Keep {} only".format(UV2_NAME))
        self.uv2_check.setToolTip(
            "Export only the 2nd UV set (by position), renamed {}.\n"
            "Your scene is left untouched.".format(UV2_NAME))
        form.addRow("UVs:", self.uv2_check)

        root.addWidget(settings_box)

        # The two exports, in two equal columns.
        export_box = QtWidgets.QGroupBox("Export")
        grid = QtWidgets.QGridLayout(export_box)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(6)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        self.one_button = self._big_button(
            "Export as ONE FBX", "All meshes into a single FBX file. Asks for a file name.")
        self.one_button.clicked.connect(self._on_export_one)
        grid.addWidget(self.one_button, 0, 0)

        self.separate_button = self._big_button(
            "Export SEPARATE FBXs", "One FBX per object, written to the Export To folder.")
        self.separate_button.clicked.connect(self._on_export_separate)
        grid.addWidget(self.separate_button, 0, 1)

        self.by_parent_check = QtWidgets.QCheckBox("Group by top-level parent")
        self.by_parent_check.setToolTip(
            "One FBX per parent (with all its children) instead of one per mesh.")
        grid.addWidget(self.by_parent_check, 1, 1)

        root.addWidget(export_box)

        # Log fills whatever height is left.
        log_box = QtWidgets.QGroupBox("Log")
        log_layout = QtWidgets.QVBoxLayout(log_box)
        self.log_view = QtWidgets.QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
        log_layout.addWidget(self.log_view)
        root.addWidget(log_box, 1)

    @staticmethod
    def _big_button(text, tooltip):
        button = QtWidgets.QPushButton(text)
        button.setToolTip(tooltip)
        button.setMinimumHeight(36)
        font = button.font()
        font.setBold(True)
        button.setFont(font)
        return button

    # -- settings -----------------------------------------------------------
    def _load_settings(self):
        self.dir_edit.setText(_opt_get("dir", ""))
        (self.everything_radio if _opt_get("everything", 0) else self.selection_radio).setChecked(True)
        self.uv2_check.setChecked(bool(_opt_get("uv2", 0)))
        self.by_parent_check.setChecked(bool(_opt_get("by_parent", 0)))

    def _save_settings(self):
        _opt_set("dir", self.dir_edit.text().strip())
        _opt_set("everything", self.everything_radio.isChecked())
        _opt_set("uv2", self.uv2_check.isChecked())
        _opt_set("by_parent", self.by_parent_check.isChecked())

    # -- log ----------------------------------------------------------------
    def log(self, message, level="info"):
        colour = self.LOG_COLOURS.get(level)
        if colour:
            self.log_view.appendHtml('<span style="color:{}">{}</span>'.format(
                colour, html.escape(message)))
        else:
            self.log_view.appendPlainText(message)
        # Paint now, so long exports show progress rather than a frozen log.
        self.log_view.repaint()

    # -- actions ------------------------------------------------------------
    def _export_folder(self):
        folder = self.dir_edit.text().strip()
        return folder if folder and os.path.isdir(folder) else ""

    def _begin(self):
        """Common start of both exports; returns the collected meshes or None."""
        self.log_view.clear()
        self._save_settings()
        if self.uv2_check.isChecked() and not uv2_allowed(self.log):
            return None
        return collect(self.everything_radio.isChecked(), self.log)

    def _on_browse(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select Export Folder", self._export_folder())
        if folder:
            self.dir_edit.setText(os.path.normpath(folder))
            self._save_settings()

    def _on_export_one(self):
        collected = self._begin()
        if not collected:
            return

        # Start the save dialog in the Export To folder, named after the scene.
        scene = cmds.file(q=True, sceneName=True, shortName=True)
        default_name = "{}.fbx".format(os.path.splitext(scene)[0] if scene else "export")
        start = os.path.join(self._export_folder(), default_name)

        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Export as One FBX", start, "FBX (*.fbx)")
        if not file_path:
            self.log("Export canceled.", "warn")
            return
        if not file_path.lower().endswith(".fbx"):
            file_path += ".fbx"

        export_single(collected, self.everything_radio.isChecked(),
                      os.path.normpath(file_path), self.uv2_check.isChecked(), self.log)

    def _on_export_separate(self):
        folder = self._export_folder()
        if not folder:
            self.log_view.clear()
            self.log("Pick a valid Export To folder first.", "warn")
            return

        collected = self._begin()
        if not collected:
            return

        export_separate(collected, self.everything_radio.isChecked(), folder,
                        self.by_parent_check.isChecked(), self.uv2_check.isChecked(), self.log)


def show():
    for widget in _maya_main_window().findChildren(QtWidgets.QDialog, OBJECT_NAME):
        widget.close()
        widget.deleteLater()
    window = ExporterWindow()
    window.show()
    return window


if __name__ == "__main__":
    show()
