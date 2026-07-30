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


def _maya_main_window():
    pointer = omui.MQtUtil.mainWindow()
    return wrapInstance(int(pointer), QtWidgets.QWidget)


class MirrorToolWindow(QtWidgets.QDialog):

    AXIS_BUTTONS = (("+X", "x", False), ("-X", "x", True),
                    ("+Y", "y", False), ("-Y", "y", True),
                    ("+Z", "z", False), ("-Z", "z", True))

    def __init__(self, parent=None):
        super(MirrorToolWindow, self).__init__(parent or _maya_main_window())
        self.setObjectName(OBJECT_NAME)
        self.setWindowTitle("GS Mirror Tool v0.1.0")
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.Tool)
        self._build()
        self.refresh()

    # -- layout -------------------------------------------------------------
    def _build(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(6)

        # picked pivot
        pivot_box = QtWidgets.QGroupBox("Mirror Pivot")
        pivot_layout = QtWidgets.QVBoxLayout(pivot_box)

        self.pivot_label = QtWidgets.QLineEdit()
        self.pivot_label.setReadOnly(True)
        self.pivot_label.setPlaceholderText("<none - mirroring in object space>")
        pivot_layout.addWidget(self.pivot_label)

        row = QtWidgets.QHBoxLayout()
        self.pick_button = QtWidgets.QPushButton("Pick")
        self.pick_button.setToolTip("Store the selected transform as the mirror pivot.")
        self.pick_button.clicked.connect(self._on_pick)
        row.addWidget(self.pick_button)

        self.new_button = QtWidgets.QPushButton("New Locator")
        self.new_button.setToolTip("Create a locator and use it as the mirror pivot.")
        self.new_button.clicked.connect(self._on_new_locator)
        row.addWidget(self.new_button)

        self.select_button = QtWidgets.QPushButton("Select")
        self.select_button.setToolTip("Select the current mirror pivot.")
        self.select_button.clicked.connect(self._on_select_pivot)
        row.addWidget(self.select_button)
        pivot_layout.addLayout(row)

        self.snap_button = QtWidgets.QPushButton("Snap Pivot to Component")
        self.snap_button.setToolTip(
            "Select a face, edge or vertices, then click to move and orient the\n"
            "pivot to that component's frame. Creates a pivot locator if none exists.")
        self.snap_button.clicked.connect(self._on_snap)
        pivot_layout.addWidget(self.snap_button)

        layout.addWidget(pivot_box)

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

        self.status = QtWidgets.QLabel("")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

    # -- state --------------------------------------------------------------
    def refresh(self):
        pivot = core.get_mirror_object()
        self.pivot_label.setText(pivot.split("|")[-1] if pivot else "")

    def _report(self, message, error=False):
        self.status.setText(message)
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
            self._report("Mirror pivot: {}".format(node.split("|")[-1]))

    def _on_new_locator(self):
        node = self._guarded(core.create_pivot_locator)
        self.refresh()
        if node:
            self._report("Created {}".format(node.split("|")[-1]))

    def _on_select_pivot(self):
        pivot = core.get_mirror_object()
        if pivot:
            cmds.select(pivot, replace=True)
        else:
            self._report("No mirror pivot picked.", error=True)

    def _on_snap(self):
        node = self._guarded(core.snap_pivot_to_component)
        self.refresh()
        if node:
            self._report("Snapped {} to component frame.".format(node.split("|")[-1]))

    def _on_mirror(self, axis, negative):
        node = self._guarded(core.create_live_mirror,
                             axis=axis, negative=negative,
                             merge=self.merge_check.isChecked())
        if node:
            self._report("Mirrored on {}{} of {}".format(
                "-" if negative else "+", axis.upper(),
                (core.get_mirror_object() or "object space").split("|")[-1]))

    def _on_merge_toggled(self, state):
        meshes = [obj for obj in cmds.ls(selection=True, objectsOnly=True, long=True)
                  if cmds.listRelatives(obj, shapes=True, noIntermediate=True, type="mesh")]
        for mesh in meshes:
            if core.existing_mirror(mesh):
                self._guarded(core.set_merge, mesh, state)


def show():
    for widget in _maya_main_window().findChildren(QtWidgets.QDialog, OBJECT_NAME):
        widget.close()
        widget.deleteLater()
    window = MirrorToolWindow()
    window.show()
    return window
