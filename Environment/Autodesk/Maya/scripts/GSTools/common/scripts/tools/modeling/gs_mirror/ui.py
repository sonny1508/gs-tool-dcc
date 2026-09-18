"""
gs_mirror.ui - PySide2 (Maya 2022-2024) / PySide6 (2025+) window.

    from gs_mirror import ui
    ui.show()
"""

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

from . import core

OBJECT_NAME = "GSMirrorToolWindow"
VERSION = "0.2.0"


def _maya_main_window():
    pointer = omui.MQtUtil.mainWindow()
    return wrapInstance(int(pointer), QtWidgets.QWidget)


class MirrorToolWindow(QtWidgets.QDialog):

    # The window is not resizable, so this is the width, full stop - widen the
    # tool by changing this number. Height is derived from the laid-out content.
    WINDOW_WIDTH = 300

    AXIS_BUTTONS = (("+X", "x", False), ("-X", "x", True),
                    ("+Y", "y", False), ("-Y", "y", True),
                    ("+Z", "z", False), ("-Z", "z", True))

    def __init__(self, parent=None):
        super(MirrorToolWindow, self).__init__(parent or _maya_main_window())
        self.setObjectName(OBJECT_NAME)
        self.setWindowTitle("GS Mirror Tool v{}".format(VERSION))
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.Tool)
        self.setSizeGripEnabled(False)
        self._selection_job = None
        self._build()
        self.setFixedWidth(self.WINDOW_WIDTH)
        self._lock_height()
        self._start_selection_job()
        self.refresh()

    def _lock_height(self):
        """Pin the height to the laid-out content.

        Re-run whenever the status line changes: the label wraps, so a long
        message needs a taller window and a fixed height would clip it.
        """
        self.layout().activate()
        self.setFixedHeight(self.sizeHint().height())

    # -- layout -------------------------------------------------------------
    def _build(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(6)

        # the controller locator that drives the mirror
        pivot_box = QtWidgets.QGroupBox("Mirror Controller")
        pivot_layout = QtWidgets.QVBoxLayout(pivot_box)

        self.pivot_label = QtWidgets.QLineEdit()
        self.pivot_label.setReadOnly(True)
        self.pivot_label.setPlaceholderText("<none - a controller is created on mirror>")
        pivot_layout.addWidget(self.pivot_label)

        row = QtWidgets.QHBoxLayout()
        self.pick_button = QtWidgets.QPushButton("Pick")
        self.pick_button.setToolTip(
            "Store the selected transform as the seed for the controller.\n"
            "Mirroring creates a controller locator at that object's pivot -\n"
            "the object itself is never used as the controller.")
        self.pick_button.clicked.connect(self._on_pick)
        row.addWidget(self.pick_button)

        self.select_button = QtWidgets.QPushButton("Select")
        self.select_button.setToolTip("Select the currently stored mirror controller.")
        self.select_button.clicked.connect(self._on_select_pivot)
        row.addWidget(self.select_button)

        pivot_layout.addLayout(row)

        self.find_button = QtWidgets.QPushButton("Find Controller")
        self.find_button.setToolTip(
            "Select the controller locator driving the selected mesh's mirror.\n"
            "Enabled only while a mirrored mesh is selected.")
        self.find_button.clicked.connect(self._on_find_pivot)
        pivot_layout.addWidget(self.find_button)

        teardown_row = QtWidgets.QHBoxLayout()
        self.remove_button = QtWidgets.QPushButton("Remove Mirror")
        self.remove_button.setToolTip(
            "Delete the mirror and spring the mesh back to its un-mirrored half.\n"
            "Other construction history on the mesh is kept.\n"
            "The controller is deleted unless it still drives another mesh.")
        self.remove_button.clicked.connect(self._on_remove_mirror)
        teardown_row.addWidget(self.remove_button)

        self.apply_button = QtWidgets.QPushButton("Apply Mirror")
        self.apply_button.setToolTip(
            "Freeze the mirrored result: the mesh keeps the shape it has now and\n"
            "becomes an ordinary object. Baking collapses the history stream, so\n"
            "all construction history on the mesh goes, not just the mirror.\n"
            "The controller is deleted unless it still drives another mesh.")
        self.apply_button.clicked.connect(self._on_apply_mirror)
        teardown_row.addWidget(self.apply_button)
        pivot_layout.addLayout(teardown_row)

        # nothing relevant is selected yet
        self._set_mirror_buttons_enabled(False)

        layout.addWidget(pivot_box)

        # object pivot - unrelated to the mirror, but the same component frame
        object_box = QtWidgets.QGroupBox("Object Pivot")
        object_layout = QtWidgets.QVBoxLayout(object_box)

        self.object_pivot_button = QtWidgets.QPushButton("Move Pivot to Selected Face")
        self.object_pivot_button.setToolTip(
            "Select a face (or edges, or vertices) and click to align that\n"
            "object's own pivot with it: the pivot moves to the component centre\n"
            "and its axes line up with the face normal.\n\n"
            "The object does not move and its rotate channels are left alone -\n"
            "the orientation is baked into rotateAxis, so a frozen object gets a\n"
            "local frame back. Needs a mesh with no construction history.")
        self.object_pivot_button.clicked.connect(self._on_move_pivot)
        object_layout.addWidget(self.object_pivot_button)

        layout.addWidget(object_box)

        # mirror axes
        axis_box = QtWidgets.QGroupBox("Mirror Axis (pivot local)")
        grid = QtWidgets.QGridLayout(axis_box)
        for i, (label, axis, negative) in enumerate(self.AXIS_BUTTONS):
            button = QtWidgets.QPushButton(label)
            button.setMinimumWidth(52)
            button.clicked.connect(
                lambda *_, a=axis, n=negative: self._on_mirror(a, n))
            grid.addWidget(button, i // 2, i % 2)
        layout.addWidget(axis_box)

        self.merge_check = QtWidgets.QCheckBox("Merge border vertices")
        self.merge_check.setChecked(True)
        self.merge_check.setToolTip(
            "Weld the seam at Maya's automatic threshold.\n"
            "Toggling this updates an existing mirror on the selected mesh.")
        self.merge_check.toggled.connect(self._on_merge_toggled)
        layout.addWidget(self.merge_check)

        # outliner colouring
        color_box = QtWidgets.QGroupBox("Display")
        color_layout = QtWidgets.QHBoxLayout(color_box)

        self.colorize_button = QtWidgets.QPushButton("Colorize Mirrors")
        self.colorize_button.setToolTip(
            "Tint every mirrored mesh and its controller in the outliner,\n"
            "one colour per controller.")
        self.colorize_button.clicked.connect(self._on_colorize)
        color_layout.addWidget(self.colorize_button)

        self.clear_color_button = QtWidgets.QPushButton("Reset Colors")
        self.clear_color_button.setToolTip(
            "Clear the outliner colours on mirrored meshes and their controllers.\n"
            "Other nodes in the scene are left alone.")
        self.clear_color_button.clicked.connect(self._on_reset_colors)
        color_layout.addWidget(self.clear_color_button)

        layout.addWidget(color_box)

        self.status = QtWidgets.QLabel("")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

    # -- state --------------------------------------------------------------
    def _start_selection_job(self):
        """Keep the Find button in step with the scene selection."""
        self._selection_job = cmds.scriptJob(
            event=["SelectionChanged", self._on_selection_changed],
            killWithScene=False)

    def _kill_selection_job(self):
        if self._selection_job is None:
            return
        try:
            if cmds.scriptJob(exists=self._selection_job):
                cmds.scriptJob(kill=self._selection_job, force=True)
        except Exception:
            pass
        self._selection_job = None

    def closeEvent(self, event):
        self._kill_selection_job()
        super(MirrorToolWindow, self).closeEvent(event)

    def _on_selection_changed(self):
        try:
            self._refresh_mirror_buttons()
        except Exception:
            pass

    def _set_mirror_buttons_enabled(self, enabled):
        for button in (self.find_button, self.remove_button, self.apply_button):
            button.setEnabled(enabled)

    def _refresh_mirror_buttons(self):
        """Find / Remove / Apply only mean anything on a mirrored mesh, and the
        pivot bake only on a component selection."""
        self._set_mirror_buttons_enabled(bool(core.selected_mirrored_meshes()))
        self.object_pivot_button.setEnabled(bool(core.selected_components()))

    def refresh(self):
        pivot = core.get_mirror_object()
        self.pivot_label.setText(pivot.split("|")[-1] if pivot else "")
        self._refresh_mirror_buttons()

    def _report(self, message, error=False):
        self.status.setText(message)
        self._lock_height()
        if error:
            cmds.warning(message)

    def _guarded(self, function, *args, **kwargs):
        try:
            return function(*args, **kwargs)
        except Exception as exc:            # keep the UI alive on user error
            self._report(str(exc), error=True)
            return None

    # -- callbacks ----------------------------------------------------------
    def _on_pick(self):
        node = self._guarded(core.set_mirror_object)
        self.refresh()
        if node:
            self._report("Mirror controller seed: {}".format(node.split("|")[-1]))

    def _on_select_pivot(self):
        pivot = core.get_mirror_object()
        if pivot:
            cmds.select(pivot, replace=True)
            self._report("Selected {}".format(pivot.split("|")[-1]))
        else:
            self._report("No mirror controller picked.", error=True)

    def _on_find_pivot(self):
        mesh, pivot = core.mirror_pivot_of_selection()
        if not pivot:
            self._report("Selected object is not using a gs_mirror setup.", error=True)
            self._refresh_mirror_buttons()
            return
        cmds.select(pivot, replace=True)
        self._guarded(core.set_mirror_object, pivot)
        self.refresh()
        self._report("{} is mirrored by {}".format(mesh.split("|")[-1],
                                                   pivot.split("|")[-1]))

    def _on_move_pivot(self):
        node = self._guarded(core.move_pivot_to_selected)
        if node:
            self._report("Pivot of {} aligned to the selection.".format(
                node.split("|")[-1]))

    def _teardown(self, function, verb):
        meshes = core.selected_mirrored_meshes()
        if not meshes:
            self._report("Select a mirrored mesh first.", error=True)
            self._refresh_mirror_buttons()
            return

        done, controllers = 0, 0
        for mesh in meshes:
            result = self._guarded(function, mesh)
            if result is None:
                continue                # the failure is already on the status line
            done += 1
            controllers += 1 if result else 0

        self.refresh()
        if done:
            self._report("{} on {} mesh(es); {} controller(s) deleted."
                         .format(verb, done, controllers))

    def _on_remove_mirror(self):
        self._teardown(core.remove_mirror, "Removed mirror")

    def _on_apply_mirror(self):
        self._teardown(core.apply_mirror, "Applied mirror")

    def _on_mirror(self, axis, negative):
        node = self._guarded(core.create_live_mirror,
                             axis=axis, negative=negative,
                             merge=self.merge_check.isChecked())
        self.refresh()
        if node:
            pivot = core.get_mirror_object() or "?"
            self._report("Mirrored on {}{} of {}".format(
                "-" if negative else "+", axis.upper(), pivot.split("|")[-1]))

    def _on_merge_toggled(self, state):
        for mesh in core.selected_meshes():
            if core.existing_mirror(mesh):
                self._guarded(core.set_merge, mesh, state)

    def _on_colorize(self):
        count = self._guarded(core.colorize_mirrors)
        if count is not None:
            self._report("Colorized {} node(s).".format(count))

    def _on_reset_colors(self):
        count = self._guarded(core.reset_mirror_colors)
        if count is not None:
            self._report("Cleared colours on {} node(s).".format(count))


def show():
    for widget in _maya_main_window().findChildren(QtWidgets.QDialog, OBJECT_NAME):
        widget.close()
        widget.deleteLater()
    window = MirrorToolWindow()
    window.show()
    return window
