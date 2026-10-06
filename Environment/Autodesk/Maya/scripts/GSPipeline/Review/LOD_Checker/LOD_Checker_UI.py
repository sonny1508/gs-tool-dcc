"""
LOD Checker - build LOD groups from mesh names, then review one LOD group at a time.

PySide2 (Maya 2022) / PySide6 (Maya 2026) window. GSPipeline runs this file
with __name__ == '__main__', which opens the window.

  * Create / Update puts the selected <asset>_LOD<n> meshes into one lodGroup
    per asset, every level set to Display: Show (see _core/gs_lod.py).
  * Pick takes the lodGroup at or above the selection. The review controls
    work on that group alone, so a scene can hold any number of LOD groups.

Reviewing only previews. Levels are switched through the group's Display
setting (meshes are never hidden), nothing goes into the undo queue, and the
group is put back the way it was picked on Reset, on picking another group,
and when the window closes.
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
# Put it there once, the same way 03_Files_IO reaches gs_fbx.
_CORE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '_core')
if _CORE not in sys.path:
    sys.path.append(_CORE)

import gs_lod  # noqa: E402  (must follow the sys.path setup)

OBJECT_NAME = "GSLODCheckerWindow"

# The window is not resizable sideways; height follows the content.
WINDOW_WIDTH = 520

# Translate spread range: level n moves n times this, in scene units.
TRANSLATE_MAX = 2000


def _maya_main_window():
    pointer = omui.MQtUtil.mainWindow()
    return wrapInstance(int(pointer), QtWidgets.QWidget)


@contextlib.contextmanager
def _no_undo():
    """
    Review edits are previews the window puts back itself, so keep them out of
    the undo queue - otherwise Ctrl+Z walks back through every slider tick.
    """
    state = cmds.undoInfo(q=True, stateWithoutFlush=True)
    cmds.undoInfo(stateWithoutFlush=False)
    try:
        yield
    finally:
        cmds.undoInfo(stateWithoutFlush=state)


def _set_translate(slot, translate, offset=None):
    """Put a level at its picked translate, then shift it in world space."""
    try:
        cmds.setAttr(slot + ".translate", *translate)
        if offset and any(offset):
            cmds.move(offset[0], offset[1], 0, slot, relative=True, worldSpace=True)
    except RuntimeError:
        pass  # locked or connected translate: leave this level where it is


def _clear_layout(layout):
    while layout.count():
        widget = layout.takeAt(0).widget()
        if widget:
            widget.deleteLater()


class LODCheckerWindow(QtWidgets.QDialog):

    LOG_COLOURS = {"ok": "#7ec87e", "warn": "#e0b64c", "error": "#e06c6c"}

    def __init__(self, parent=None):
        super(LODCheckerWindow, self).__init__(parent or _maya_main_window())
        self.setObjectName(OBJECT_NAME)
        self.setWindowTitle("LOD Checker")
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.Tool)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        # The picked group, held by UUID so renaming or reparenting it while
        # the window is open does not lose it.
        self._group_uuid = None
        self._levels = []          # [(level index, slot uuid)] in slider order
        self._display_state = {}   # level index -> displayLevel when picked
        self._translates = {}      # slot uuid -> translate when picked
        self._layer_state = None   # display layer uuid -> visibility, once touched
        self._show_after = True    # which side SWITCH shows next

        self._build()
        self._set_review_enabled(False)
        self.setFixedWidth(WINDOW_WIDTH)
        self.resize(WINDOW_WIDTH, self.sizeHint().height())

        # A new or opened scene takes the picked group with it.
        self._jobs = [cmds.scriptJob(event=[event, self._on_scene_changed])
                      for event in ("SceneOpened", "NewSceneOpened")]

    # -- layout -------------------------------------------------------------
    def _build(self):
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        # Build LOD groups, and pick the one to review.
        group_box = QtWidgets.QGroupBox("LOD Group")
        group_layout = QtWidgets.QVBoxLayout(group_box)

        create_button = self._big_button(
            "Create / Update LOD Groups from Selection",
            "One LOD group per asset name: Tree_LOD0..Tree_LOD4 -> Tree | LOD_0..LOD_4.\n"
            "If a LOD group with that name already exists it is updated: each selected\n"
            "level replaces that level's old content, other levels are kept.\n"
            "Every level is set to Display: Show.")
        create_button.clicked.connect(self._on_create)
        group_layout.addWidget(create_button)

        pick_row = QtWidgets.QHBoxLayout()
        pick_row.setSpacing(4)
        self.group_edit = QtWidgets.QLineEdit()
        self.group_edit.setReadOnly(True)
        self.group_edit.setPlaceholderText("No LOD group picked")
        pick_row.addWidget(self.group_edit, 1)
        pick_button = QtWidgets.QPushButton("Pick")
        pick_button.setToolTip("Review the selected LOD group, or the one holding the selection.")
        pick_button.clicked.connect(self._on_pick)
        pick_row.addWidget(pick_button)
        group_layout.addLayout(pick_row)
        root.addWidget(group_box)

        # Everything below works on the picked group.
        self.reset_button = QtWidgets.QPushButton("RESET")
        self.reset_button.setFixedHeight(30)
        self.reset_button.setStyleSheet(
            "QPushButton { background-color: #6b0914; color: white; font-weight: bold; }")
        self.reset_button.setToolTip("Put the picked LOD group back the way it was when picked.")
        self.reset_button.clicked.connect(self._on_reset)
        root.addWidget(self.reset_button)

        lod_box = QtWidgets.QGroupBox("Select LOD")
        lod_layout = QtWidgets.QHBoxLayout(lod_box)
        self.lod_spin = QtWidgets.QSpinBox()
        self.lod_spin.setFixedWidth(55)
        lod_layout.addWidget(self.lod_spin, 0, QtCore.Qt.AlignTop)
        slider_column = QtWidgets.QVBoxLayout()
        slider_column.setSpacing(2)
        self.lod_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.lod_slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.lod_slider.setTickInterval(1)
        self.lod_slider.setPageStep(1)
        slider_column.addWidget(self.lod_slider)
        self.tick_labels = QtWidgets.QHBoxLayout()
        slider_column.addLayout(self.tick_labels)
        lod_layout.addLayout(slider_column, 1)
        self.lod_spin.valueChanged.connect(self.lod_slider.setValue)
        self.lod_slider.valueChanged.connect(self._on_lod_slider)
        root.addWidget(lod_box)

        translate_box = QtWidgets.QGroupBox("Slider Translate LOD")
        translate_form = QtWidgets.QFormLayout(translate_box)
        self.x_spin, self.x_slider = self._axis_row(translate_form, "X Axis")
        self.y_spin, self.y_slider = self._axis_row(translate_form, "Y Axis")
        root.addWidget(translate_box)

        # Level buttons are built per picked group, see _rebuild_level_controls.
        picker_box = QtWidgets.QGroupBox("Picker Before After")
        picker_form = QtWidgets.QFormLayout(picker_box)
        self.before_row = QtWidgets.QHBoxLayout()
        self.before_row.setSpacing(2)
        self.after_row = QtWidgets.QHBoxLayout()
        self.after_row.setSpacing(2)
        picker_form.addRow("Before:", self.before_row)
        picker_form.addRow("After:", self.after_row)
        self.before_buttons = QtWidgets.QButtonGroup(self)
        self.after_buttons = QtWidgets.QButtonGroup(self)
        root.addWidget(picker_box)

        self.switch_button = QtWidgets.QPushButton("SWITCH")
        self.switch_button.setFixedHeight(40)
        self.switch_button.setStyleSheet(
            "QPushButton { background-color: #f6921e; color: white; font-weight: bold; }")
        self.switch_button.clicked.connect(self._on_switch)
        root.addWidget(self.switch_button)

        show_row = QtWidgets.QHBoxLayout()
        show_button = QtWidgets.QPushButton("Show All LODs")
        show_button.clicked.connect(lambda: self._set_all(gs_lod.SHOW))
        hide_button = QtWidgets.QPushButton("Hide All LODs")
        hide_button.clicked.connect(lambda: self._set_all(gs_lod.HIDE))
        show_row.addWidget(show_button)
        show_row.addWidget(hide_button)
        root.addLayout(show_row)

        self._review_widgets = [self.reset_button, lod_box, translate_box, picker_box,
                                self.switch_button, show_button, hide_button]

        log_box = QtWidgets.QGroupBox("Log")
        log_layout = QtWidgets.QVBoxLayout(log_box)
        self.log_view = QtWidgets.QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setFixedHeight(110)
        self.log_view.setPlaceholderText(
            "Select <asset>_LOD<n> meshes and Create, or select a LOD group and Pick.")
        log_layout.addWidget(self.log_view)
        root.addWidget(log_box)

    @staticmethod
    def _big_button(text, tooltip):
        button = QtWidgets.QPushButton(text)
        button.setToolTip(tooltip)
        button.setMinimumHeight(36)
        font = button.font()
        font.setBold(True)
        button.setFont(font)
        return button

    def _axis_row(self, form, label):
        row = QtWidgets.QHBoxLayout()
        spin = QtWidgets.QSpinBox()
        spin.setRange(0, TRANSLATE_MAX)
        spin.setFixedWidth(70)
        slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        slider.setRange(0, TRANSLATE_MAX)
        spin.valueChanged.connect(slider.setValue)
        slider.valueChanged.connect(spin.setValue)
        slider.valueChanged.connect(self._apply_translate)
        row.addWidget(spin)
        row.addWidget(slider, 1)
        form.addRow(label, row)
        return spin, slider

    def _rebuild_level_controls(self):
        """Size the slider and the Before/After buttons to the picked group's levels."""
        count = len(self._levels)
        for widget in (self.lod_slider, self.lod_spin):
            widget.blockSignals(True)
            widget.setRange(0, max(count - 1, 0))
            widget.setValue(0)
            widget.blockSignals(False)

        # Labels under the slider: the ends pinned to the edges, even gaps between.
        _clear_layout(self.tick_labels)
        for position, (index, _) in enumerate(self._levels):
            if position:
                self.tick_labels.addStretch(1)
            self.tick_labels.addWidget(QtWidgets.QLabel(str(index)))

        for buttons, row in ((self.before_buttons, self.before_row),
                             (self.after_buttons, self.after_row)):
            for button in buttons.buttons():
                buttons.removeButton(button)
            _clear_layout(row)
            for position, (index, _) in enumerate(self._levels):
                button = QtWidgets.QPushButton(str(index))
                button.setCheckable(True)
                buttons.addButton(button, position)
                row.addWidget(button)

        # Start on the most common comparison: the top level against the next.
        if count:
            self.before_buttons.button(0).setChecked(True)
            self.after_buttons.button(min(1, count - 1)).setChecked(True)

    def _set_review_enabled(self, enabled):
        for widget in self._review_widgets:
            widget.setEnabled(enabled)

    # -- log ----------------------------------------------------------------
    def log(self, message, level="info"):
        colour = self.LOG_COLOURS.get(level)
        if colour:
            self.log_view.appendHtml('<span style="color:{}">{}</span>'.format(
                colour, html.escape(message)))
        else:
            self.log_view.appendPlainText(message)

    # -- create / pick ------------------------------------------------------
    def _on_create(self):
        self.log_view.clear()
        # Put the picked group back first, so a preview (hidden levels, the
        # translate spread) is never baked into a group being rebuilt. Then
        # drop the pick: its snapshot no longer matches a rebuilt group, and
        # restoring it later would undo the build's Display: Show.
        previous = self._group_uuid
        self._restore()
        self._forget()
        try:
            groups = gs_lod.build_lod_groups(log=self.log)
        except Exception as error:
            self.log("Building LOD groups failed: {}".format(error), "error")
            raise

        # Review what was just built; otherwise carry on with the old pick.
        if groups:
            self._pick(groups[0])
        elif previous and gs_lod.path_of(previous):
            self._pick(gs_lod.path_of(previous))

    def _on_pick(self):
        groups = []
        for node in cmds.ls(selection=True, long=True, objectsOnly=True) or []:
            group = gs_lod.lod_group_of(node)
            if group and group not in groups:
                groups.append(group)
        if not groups:
            self.log("Select a LOD group, or anything inside one, then Pick.", "warn")
            return
        self._pick(groups[0])
        if len(groups) > 1:
            self.log("{} LOD groups in the selection, picked the first.".format(len(groups)), "warn")

    def _pick(self, group):
        self._restore()
        levels = gs_lod.levels(group)
        if not levels:
            self.log("{} has no levels to review.".format(gs_lod.short_name(group)), "warn")
            return

        self._group_uuid = gs_lod.uuid_of(group)
        self._levels = [(index, gs_lod.uuid_of(slot)) for index, slot in levels]
        self._display_state = {index: cmds.getAttr("{}.displayLevel[{}]".format(group, index))
                               for index, _ in levels}
        self._translates = {gs_lod.uuid_of(slot): cmds.getAttr(slot + ".translate")[0]
                            for _, slot in levels}
        self._show_display_layers()

        self.group_edit.setText("{}   ({} levels)".format(gs_lod.short_name(group), len(levels)))
        self.group_edit.setToolTip(group)
        self._rebuild_level_controls()
        self._set_review_enabled(True)
        self.log("Picked {}.".format(gs_lod.short_name(group)), "ok")

    def _group(self):
        """The picked group's long name; None, and the pick dropped, once it is gone."""
        if not self._group_uuid:
            return None
        group = gs_lod.path_of(self._group_uuid)
        if not group:
            self._forget()
            self.log("The picked LOD group no longer exists - Pick again.", "warn")
        return group

    def _forget(self):
        """Drop the pick without touching the scene."""
        self._group_uuid = None
        self._levels, self._display_state, self._translates = [], {}, {}
        self.group_edit.clear()
        self.group_edit.setToolTip("")
        self._rebuild_level_controls()
        self._reset_controls()
        self._set_review_enabled(False)

    # -- review -------------------------------------------------------------
    def _set_display(self, group, values):
        """values: level index -> displayLevel."""
        with _no_undo():
            for index, value in values.items():
                cmds.setAttr("{}.displayLevel[{}]".format(group, index), value)

    def _show_only(self, position):
        group = self._group()
        if not group or position >= len(self._levels):
            return
        shown = self._levels[position][0]
        self._set_display(group, {index: gs_lod.SHOW if index == shown else gs_lod.HIDE
                                  for index, _ in self._levels})

    def _set_all(self, value):
        group = self._group()
        if group:
            self._set_display(group, {index: value for index, _ in self._levels})

    def _on_lod_slider(self, position):
        self.lod_spin.blockSignals(True)
        self.lod_spin.setValue(position)
        self.lod_spin.blockSignals(False)
        self._show_only(position)

    def _apply_translate(self, *_):
        """Spread the levels out: level n moves n times the X/Y offset."""
        if not self._group():
            return
        x, y = self.x_slider.value(), self.y_slider.value()
        with _no_undo():
            for position, (_, uuid) in enumerate(self._levels):
                slot = gs_lod.path_of(uuid)
                if slot:
                    _set_translate(slot, self._translates[uuid], (x * position, y * position))

    def _on_switch(self):
        before, after = self.before_buttons.checkedId(), self.after_buttons.checkedId()
        if before < 0 or after < 0:
            self.log("Pick a Before and an After level first.", "warn")
            return

        side = "After" if self._show_after else "Before"
        position = after if self._show_after else before
        self._show_after = not self._show_after

        for widget in (self.lod_slider, self.lod_spin):
            widget.blockSignals(True)
            widget.setValue(position)
            widget.blockSignals(False)
        self._show_only(position)
        self.switch_button.setText("SWITCH   ({}: LOD {})".format(side, self._levels[position][0]))

    def _on_reset(self):
        self._restore()
        self.log("Reset.")

    def _restore(self):
        """Put the picked group back how it was when picked, and zero the controls."""
        group = self._group()
        if group:
            self._set_display(group, self._display_state)
            with _no_undo():
                for uuid, translate in self._translates.items():
                    slot = gs_lod.path_of(uuid)
                    if slot:
                        _set_translate(slot, translate)
        self._reset_controls()

    def _reset_controls(self):
        for widget in (self.lod_slider, self.lod_spin, self.x_slider, self.x_spin,
                       self.y_slider, self.y_spin):
            widget.blockSignals(True)
            widget.setValue(0)
            widget.blockSignals(False)
        self._show_after = True
        self.switch_button.setText("SWITCH")

    # -- display layers -----------------------------------------------------
    def _show_display_layers(self):
        """
        Turn every display layer on the first time a group is picked, so no
        level stays hidden by its layer while reviewing. Put back on close.
        """
        if self._layer_state is not None:
            return
        self._layer_state = {}
        with _no_undo():
            for layer in cmds.ls(type="displayLayer") or []:
                if layer.split(":")[-1] == "defaultLayer":
                    continue
                self._layer_state[gs_lod.uuid_of(layer)] = cmds.getAttr(layer + ".visibility")
                try:
                    cmds.setAttr(layer + ".visibility", True)
                except RuntimeError:
                    pass  # locked, e.g. from a reference

    def _restore_display_layers(self):
        if not self._layer_state:
            return
        with _no_undo():
            for uuid, visible in self._layer_state.items():
                layer = gs_lod.path_of(uuid)
                if layer:
                    try:
                        cmds.setAttr(layer + ".visibility", visible)
                    except RuntimeError:
                        pass
        self._layer_state = None

    # -- lifetime -----------------------------------------------------------
    def _on_scene_changed(self):
        # The old scene's nodes are gone with it - nothing left to put back.
        try:
            self._layer_state = None
            if self._group_uuid:
                self._forget()
                self.log("New scene - Pick a LOD group again.", "warn")
        except RuntimeError:
            pass  # the Qt side of the window is already deleted

    def closeEvent(self, event):
        for job in self._jobs:
            if cmds.scriptJob(exists=job):
                cmds.scriptJob(kill=job, force=True)
        self._jobs = []
        self._restore()
        self._restore_display_layers()
        super(LODCheckerWindow, self).closeEvent(event)


def show():
    for widget in _maya_main_window().findChildren(QtWidgets.QDialog, OBJECT_NAME):
        widget.close()
        widget.deleteLater()
    window = LODCheckerWindow()
    window.show()
    return window


if __name__ == "__main__":
    show()
