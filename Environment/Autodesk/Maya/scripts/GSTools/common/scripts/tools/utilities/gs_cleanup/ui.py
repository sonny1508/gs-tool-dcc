"""
gs_cleanup.ui - PySide2 (Maya 2022-2024) / PySide6 (2025+) window.

    from gs_cleanup import ui
    ui.show()

Layout is a stack of clean-up sections over one shared status line. A new
section is a CleanupSection subclass added to SECTIONS - it inherits the status
line and the error guard, and needs nothing else.
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

OBJECT_NAME = "GSCleanUpToolWindow"


def _maya_main_window():
    pointer = omui.MQtUtil.mainWindow()
    return wrapInstance(int(pointer), QtWidgets.QWidget)


def _plural(count, word):
    return "{} {}{}".format(count, word, "" if count == 1 else "s")


# ---------------------------------------------------------------------------
# sections
# ---------------------------------------------------------------------------
class CleanupSection(QtWidgets.QGroupBox):
    """Base for one clean-up feature.

    Subclasses set TITLE and implement build(); use self.report() for user
    feedback and self.guarded() to call core functions without a traceback
    killing the window.
    """

    TITLE = "Section"

    def __init__(self, window, parent=None):
        super(CleanupSection, self).__init__(self.TITLE, parent)
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


class MaterialSection(CleanupSection):
    """Find materials that are copies of each other by name and merge them."""

    TITLE = "Materials"

    def build(self, body):
        # (group item, QButtonGroup, [(QRadioButton, core.MaterialInfo), ...])
        self._groups = []

        find = QtWidgets.QPushButton("Find Duplicate Materials")
        find.setToolTip(
            "Group materials whose names match once the namespace, any pasted__\n"
            "prefix and any number suffix are ignored: materialA, materialA_001,\n"
            "materialA1, ns:materialA, pasted__materialA, pasted__pasted__materialA.\n\n"
            "Groups where one material is named exactly the base (materialA) are\n"
            "ticked for you. Numbered series with no such base (Tire_01, Tire_02)\n"
            "are listed but left unticked - they may well be different materials.\n\n"
            "Pasted copies always pair with their original: Tire_01 and\n"
            "pasted__Tire_01 are a ticked group of their own, and the rest of the\n"
            "series shows up again on the next Find.")
        find.clicked.connect(self.scan)
        body.addWidget(find)

        self.tree = QtWidgets.QTreeWidget()
        self.tree.setHeaderLabels(["Material", "Type", "Objects"])
        self.tree.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        header = self.tree.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        self.tree.itemChanged.connect(self._on_item_changed)
        self.tree.itemDoubleClicked.connect(self._on_double_clicked)
        body.addWidget(self.tree)

        hint = QtWidgets.QLabel(
            "Tick the groups to merge and pick the material to keep in each. "
            "Double-click a material to select it.")
        hint.setWordWrap(True)
        body.addWidget(hint)

        row = QtWidgets.QHBoxLayout()
        select = QtWidgets.QPushButton("Select Objects")
        select.setToolTip("Select the objects (and faces) using the highlighted\n"
                          "material, or every material in the highlighted group.")
        select.clicked.connect(self._on_select_objects)
        row.addWidget(select)

        merge = QtWidgets.QPushButton("Merge Ticked Groups")
        merge.setToolTip(
            "In every ticked group, move everything assigned to the other materials\n"
            "onto the one picked to keep, then delete the others together with their\n"
            "shading groups and any texture nodes left feeding nothing.\n\n"
            "Default, referenced and locked materials are never deleted.\n"
            "One Ctrl+Z undoes the whole merge.")
        merge.clicked.connect(self._on_merge)
        row.addWidget(merge)
        body.addLayout(row)

    # -- list ---------------------------------------------------------------
    def scan(self):
        groups = self.guarded(core.find_duplicate_materials)
        if groups is None:
            return
        self._populate(groups)
        if groups:
            ticked = sum(1 for group in groups if group.obvious)
            self.report("{} with matching names found, {} ticked.".format(
                _plural(len(groups), "group"), ticked))
        else:
            self.report("No duplicate material names found.")

    def _populate(self, groups):
        self.tree.blockSignals(True)
        try:
            self.tree.clear()
            for _, buttons, _ in self._groups:
                buttons.deleteLater()
            self._groups = []
            for group in groups:
                self._add_group(group)
            self.tree.expandAll()
        finally:
            self.tree.blockSignals(False)
        self._sync_enabled()

    def _add_group(self, group):
        item = QtWidgets.QTreeWidgetItem(self.tree)
        item.setText(0, "{}  ({})".format(group.base, len(group.members)))
        item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
        item.setCheckState(0, QtCore.Qt.Checked if group.obvious else QtCore.Qt.Unchecked)
        item.setToolTip(0, "Ticked groups are merged by Merge Ticked Groups."
                        if group.obvious else
                        "Unticked: no material is named exactly '{}', so these may be\n"
                        "a deliberate numbered series. Tick to merge them anyway.".format(
                            group.base))
        font = item.font(0)
        font.setBold(True)
        item.setFont(0, font)

        # Radios in different rows share the viewport as parent, so a button
        # group is what keeps the choice exclusive per group, not tree-wide.
        buttons = QtWidgets.QButtonGroup(self)
        radios = []
        for info in group.members:
            child = QtWidgets.QTreeWidgetItem(item)
            child.setData(0, QtCore.Qt.UserRole, info.name)
            child.setText(1, "{} - {}".format(info.type, info.protected)
                          if info.protected else info.type)
            child.setText(2, str(info.objects))

            radio = QtWidgets.QRadioButton(info.name)
            radio.setChecked(info.name == group.keeper)
            radio.setToolTip("{}: can be kept, but is never deleted.".format(
                info.protected.capitalize()) if info.protected else
                "Keep this material - the others in the group merge into it.")
            radio.clicked.connect(
                lambda checked=False, row=child: self.tree.setCurrentItem(row))
            buttons.addButton(radio)
            self.tree.setItemWidget(child, 0, radio)
            child.setSizeHint(0, radio.sizeHint())
            radios.append((radio, info))
        self._groups.append((item, buttons, radios))

    def _sync_enabled(self):
        """Grey out the keeper choice of groups that are not ticked."""
        for item, _, radios in self._groups:
            ticked = item.checkState(0) == QtCore.Qt.Checked
            for radio, _ in radios:
                radio.setEnabled(ticked)

    def _materials_of(self, item):
        if item.parent() is None:
            return [item.child(i).data(0, QtCore.Qt.UserRole)
                    for i in range(item.childCount())]
        return [item.data(0, QtCore.Qt.UserRole)]

    # -- callbacks ----------------------------------------------------------
    def _on_item_changed(self, item, column):
        if item.parent() is None and column == 0:
            self._sync_enabled()

    def _on_double_clicked(self, item, column):
        name = item.data(0, QtCore.Qt.UserRole)
        if not name:
            return                          # group row: Qt expands / collapses it
        if not cmds.objExists(name):
            self.report("{} no longer exists - run Find again.".format(name), error=True)
            return
        cmds.select(name, replace=True)
        self.report("Selected material {}.".format(name))

    def _on_select_objects(self):
        item = self.tree.currentItem()
        if item is None:
            self.report("Click a material or a group in the list first.", error=True)
            return
        names = [name for name in self._materials_of(item) if cmds.objExists(name)]
        members = []
        for name in names:
            members.extend(core.assigned_members(name))
        label = names[0] if len(names) == 1 else "the {} materials in the group".format(
            len(names))
        if not members:
            cmds.select(clear=True)
            self.report("Nothing is assigned to {}.".format(label))
            return
        cmds.select(members, replace=True)
        self.report("Selected {} using {}.".format(
            _plural(len(core.distinct_objects(members)), "object"), label))

    def _on_merge(self):
        merges = []
        for item, _, radios in self._groups:
            if item.checkState(0) != QtCore.Qt.Checked:
                continue
            keepers = [info.name for radio, info in radios if radio.isChecked()]
            if keepers:
                merges.append((keepers[0], [info.name for _, info in radios
                                            if info.name != keepers[0]]))
        if not merges:
            self.report("Nothing ticked - tick the groups to merge first.", error=True)
            return

        result = self.guarded(core.merge_materials, merges)
        if result is None:
            return
        for name, reason in result.skipped:
            cmds.warning("gs_cleanup: {} skipped - {}".format(name, reason))

        groups = self.guarded(core.find_duplicate_materials)
        if groups is not None:
            self._populate(groups)

        message = "Removed {}, reassigned {}, deleted {}.".format(
            _plural(len(result.removed), "duplicate material"),
            _plural(result.reassigned, "object"),
            _plural(len(result.cleaned), "unused texture node"))
        if result.skipped:
            message += " {} skipped (see Script Editor).".format(len(result.skipped))
        self.report(message, error=bool(result.skipped) and not result.removed)


SECTIONS = (MaterialSection,)


# ---------------------------------------------------------------------------
# window
# ---------------------------------------------------------------------------
class CleanUpWindow(QtWidgets.QDialog):

    def __init__(self, parent=None):
        super(CleanUpWindow, self).__init__(parent or _maya_main_window())
        self.setObjectName(OBJECT_NAME)
        self.setWindowTitle("GS Clean Up v0.1.0")
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.Tool)
        self.sections = []
        self._build()

    # -- layout -------------------------------------------------------------
    def _build(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(6)

        for section_type in SECTIONS:
            section = section_type(self)
            self.sections.append(section)
            layout.addWidget(section)

        self.status = QtWidgets.QLabel("")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

        self.setMinimumWidth(360)
        self.resize(440, 520)

    # -- state --------------------------------------------------------------
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


def show():
    for widget in _maya_main_window().findChildren(QtWidgets.QDialog, OBJECT_NAME):
        widget.close()
        widget.deleteLater()
    window = CleanUpWindow()
    window.show()
    return window
