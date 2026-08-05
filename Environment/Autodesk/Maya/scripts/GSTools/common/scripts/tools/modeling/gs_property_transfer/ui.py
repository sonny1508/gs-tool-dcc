"""
gs_property_transfer.ui - PySide2 (Maya 2022-2024) / PySide6 (2025+) window.

    from gs_property_transfer import ui
    ui.show()

Layout is one shared "Source Object" header plus a stack of transfer sections.
A new section is a TransferSection subclass added to SECTIONS - it inherits the
picked source, the status line and the error guard, and needs nothing else.
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

OBJECT_NAME = "GSPropertyTransferToolWindow"


def _maya_main_window():
    pointer = omui.MQtUtil.mainWindow()
    return wrapInstance(int(pointer), QtWidgets.QWidget)


# ---------------------------------------------------------------------------
# sections
# ---------------------------------------------------------------------------
class TransferSection(QtWidgets.QGroupBox):
    """Base for one transfer feature.

    Subclasses set TITLE and implement build(); use self.report() for user
    feedback and self.guarded() to call core functions without a traceback
    killing the window.
    """

    TITLE = "Section"

    def __init__(self, window, parent=None):
        super(TransferSection, self).__init__(self.TITLE, parent)
        self.window = window
        body = QtWidgets.QVBoxLayout(self)
        body.setSpacing(4)
        self.build(body)

    def build(self, body):
        raise NotImplementedError

    def report(self, message, error=False):
        self.window.report(message, error=error)

    def guarded(self, function, *args, **kwargs):
        return self.window.guarded(function, *args, **kwargs)

    def refresh(self):
        """Called when the picked source changes. Override if needed."""


class PivotSection(TransferSection):
    """Move the selected objects' pivots onto the source object."""

    TITLE = "Pivot"

    COMPONENTS = (
        ("translate", "Translate", True,
         "Put the pivot on the source object's pivot.\n"
         "Non-destructive: nothing but the pivot attributes change."),
        ("rotate", "Rotate", True,
         "Align the object's local axes to the source object's.\n\n"
         "A pivot's orientation IS the object's local axes, so this re-authors\n"
         "the object's local space: it is baked into the new frame. Geometry\n"
         "stays put, but Freeze Transformations has to be able to run on it -\n"
         "no construction history, no locked or connected transform channels."),
        ("scale", "Scale", False,
         "Take the source object's scale as well. Goes through the same bake."),
    )

    def build(self, body):
        row = QtWidgets.QHBoxLayout()
        self.components = {}
        for key, label, default, tooltip in self.COMPONENTS:
            check = QtWidgets.QCheckBox(label)
            check.setChecked(default)
            check.setToolTip(tooltip)
            self.components[key] = check
            row.addWidget(check)
        body.addLayout(row)

        self.freeze_check = QtWidgets.QCheckBox("Freeze transforms")
        self.freeze_check.setChecked(False)
        self.freeze_check.setToolTip(
            "Zero translate / rotate / scale on the target first, so it starts from\n"
            "clean channels with no old pivot offsets.\n\n"
            "Translate only - the object ends at 0 / 0 / 1 with its pivot on the source.\n"
            "With Rotate or Scale - the matched frame has to live in the channels,\n"
            "so they hold that frame instead of zero; a rotated pivot is a rotation,\n"
            "and a fully frozen transform has none.")
        body.addWidget(self.freeze_check)

        button = QtWidgets.QPushButton("Move Selected Pivots to Source")
        button.setToolTip("Move the pivot of every selected object onto the source object.")
        button.clicked.connect(self._on_match)
        body.addWidget(button)

    def _on_match(self):
        flags = {key: check.isChecked() for key, check in self.components.items()}
        result = self.guarded(core.match_pivots,
                              freeze=self.freeze_check.isChecked(), **flags)
        if result is None:
            return
        moved, failed = result
        if moved:
            cmds.select(moved, replace=True)     # reparenting can drop the selection

        parts = [label for key, label, _, _ in self.COMPONENTS if flags[key]]
        source = core.short_name(core.get_source_object())
        message = "{} of {} pivot{} moved to {}.".format(
            " + ".join(parts) if parts else "Freeze",
            len(moved), "" if len(moved) == 1 else "s", source)
        for node, error in failed:
            cmds.warning("gs_property_transfer: {} - {}".format(
                core.short_name(node), error))
        if failed:
            node, error = failed[0]
            message = "{} of {} failed - {}: {}{}".format(
                len(failed), len(failed) + len(moved), core.short_name(node), error,
                "" if len(failed) == 1 else " (see Script Editor for the rest)")
        self.report(message, error=bool(failed))


SECTIONS = (PivotSection,)


# ---------------------------------------------------------------------------
# window
# ---------------------------------------------------------------------------
class PropertyTransferWindow(QtWidgets.QDialog):

    def __init__(self, parent=None):
        super(PropertyTransferWindow, self).__init__(parent or _maya_main_window())
        self.setObjectName(OBJECT_NAME)
        self.setWindowTitle("GS Property Transfer v0.1.0")
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.Tool)
        self.sections = []
        self._build()
        self.refresh()

    # -- layout -------------------------------------------------------------
    def _build(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(6)

        source_box = QtWidgets.QGroupBox("Source Object")
        source_layout = QtWidgets.QVBoxLayout(source_box)

        self.source_label = QtWidgets.QLineEdit()
        self.source_label.setReadOnly(True)
        self.source_label.setPlaceholderText("<none picked>")
        self.source_label.setToolTip("The object every section below reads from.")
        source_layout.addWidget(self.source_label)

        row = QtWidgets.QHBoxLayout()
        for label, tooltip, callback in (
                ("Pick", "Store the selected transform as the source object.",
                 self._on_pick),
                ("Select", "Select the current source object.",
                 self._on_select),
                ("Clear", "Forget the current source object.",
                 self._on_clear)):
            button = QtWidgets.QPushButton(label)
            button.setToolTip(tooltip)
            button.clicked.connect(callback)
            row.addWidget(button)
        source_layout.addLayout(row)
        layout.addWidget(source_box)

        for section_type in SECTIONS:
            section = section_type(self)
            self.sections.append(section)
            layout.addWidget(section)

        layout.addStretch()

        self.status = QtWidgets.QLabel("")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

        self.setMinimumWidth(300)

    # -- state --------------------------------------------------------------
    def refresh(self):
        source = core.get_source_object()
        self.source_label.setText(core.short_name(source))
        for section in self.sections:
            section.refresh()

    def report(self, message, error=False):
        """Status line + an in-view message, so a failure cannot go unnoticed."""
        colour = "#ff6b6b" if error else "#9fd3a8"
        self.status.setText(message)
        self.status.setStyleSheet("color: {};".format(colour))
        try:
            cmds.inViewMessage(assistMessage='<span style="color:{}">{}</span>'.format(
                colour, message), position="midCenterBot", fade=True, fadeOutTime=2.0)
        except Exception:
            pass                            # in-view messages are a nicety only
        if error:
            cmds.warning(message)

    def guarded(self, function, *args, **kwargs):
        try:
            return function(*args, **kwargs)
        except Exception as exc:            # keep the UI alive on user error
            self.report(str(exc), error=True)
            return None

    # -- callbacks ----------------------------------------------------------
    def _on_pick(self):
        node = self.guarded(core.set_source_object)
        self.refresh()
        if node:
            self.report("Source object: {}".format(core.short_name(node)))

    def _on_select(self):
        source = core.get_source_object()
        if source:
            cmds.select(source, replace=True)
        else:
            self.report("No source object picked.", error=True)

    def _on_clear(self):
        core.clear_source_object()
        self.refresh()
        self.report("Source object cleared.")


def show():
    for widget in _maya_main_window().findChildren(QtWidgets.QDialog, OBJECT_NAME):
        widget.close()
        widget.deleteLater()
    window = PropertyTransferWindow()
    window.show()
    return window
