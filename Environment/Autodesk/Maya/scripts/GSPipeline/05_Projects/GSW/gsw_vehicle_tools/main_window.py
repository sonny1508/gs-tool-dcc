# -*- coding: utf-8 -*-
"""GSW Vehicle Tools main window.

A tabbed host for the GSW project's Maya tools. Each sub-tool is a module in
this package exposing:

    LABEL          - the tab label
    build(parent)  - returns a QWidget

To add a tool, drop the module in beside uv_atlas.py and add it to _tools().

Also home to ErrorLog, the shared results widget every sub-tool uses.
"""

import maya.cmds as cmds
import maya.OpenMayaUI as omui

# PySide6 from Maya 2025 on, PySide2 below it. Version first so a wrong
# assumption fails loudly instead of silently binding to whatever imports.
if int(cmds.about(apiVersion=True) / 10000) >= 2025:
    from PySide6 import QtCore, QtGui, QtWidgets
    from shiboken6 import wrapInstance
else:
    from PySide2 import QtCore, QtGui, QtWidgets
    from shiboken2 import wrapInstance

WINDOW_OBJECT_NAME = "gswVehicleToolsWindow"
WINDOW_TITLE = "GSW Vehicle Tools"

# Fixed size - the window is deliberately not resizable. Long entries scroll
# inside the error list rather than stretching the panel.
WINDOW_WIDTH = 480
WINDOW_HEIGHT = 440


def _tools():
    """Sub-tool modules, in tab order.

    Imported here rather than at module level: the sub-tools import ErrorLog
    from this module, so a top-level import would be circular.
    """
    from gsw_vehicle_tools import uv_atlas
    return [uv_atlas]


def maya_main_window():
    return wrapInstance(int(omui.MQtUtil.mainWindow()), QtWidgets.QWidget)


class ErrorLog(QtWidgets.QGroupBox):
    """List of problems plus a Select Errors button.

    Fed a list of (message, targets) pairs, where targets is a list of node or
    component names to select. Shared by every sub-tool in this package.
    """

    def __init__(self, title="Errors", parent=None):
        super(ErrorLog, self).__init__(title, parent)
        self._targets = []

        self.list_widget = QtWidgets.QListWidget()
        self.list_widget.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self.list_widget.setAlternatingRowColors(True)

        self.status_label = QtWidgets.QLabel("")
        self.status_label.setWordWrap(True)

        self.select_button = QtWidgets.QPushButton("Select Errors")
        self.select_button.clicked.connect(self.select_errors)
        self.clear_button = QtWidgets.QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear)

        buttons = QtWidgets.QHBoxLayout()
        buttons.addWidget(self.select_button)
        buttons.addWidget(self.clear_button)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.status_label)
        layout.addWidget(self.list_widget)
        layout.addLayout(buttons)

        self._refresh_buttons()

    def set_status(self, text, is_error=False):
        self.status_label.setText(text)
        self.status_label.setStyleSheet("color: #d96060;" if is_error else "")

    def set_errors(self, records):
        """records: list of (message, [target names]) tuples."""
        self.list_widget.clear()
        self._targets = []
        for message, targets in records:
            self.list_widget.addItem(message)
            self._targets.extend(targets)
        self._refresh_buttons()

    def clear(self):
        self.list_widget.clear()
        self._targets = []
        self.set_status("")
        self._refresh_buttons()

    def select_errors(self):
        if not self._targets:
            return
        existing = [t for t in self._targets if cmds.objExists(t.split(".")[0])]
        if not existing:
            self.set_status("Nothing left to select - the scene has changed.", True)
            return
        cmds.select(existing, replace=True)
        # UV components land you in component mode; make the UV mask explicit
        # so the shells are actually visible in the UV editor.
        if any("." in t for t in existing):
            cmds.selectMode(component=True)
            cmds.selectType(polymeshUV=True)

    def _refresh_buttons(self):
        has_targets = bool(self._targets)
        self.select_button.setEnabled(has_targets)
        self.clear_button.setEnabled(self.list_widget.count() > 0)


class GSWVehicleTools(QtWidgets.QDialog):

    def __init__(self, parent=None):
        super(GSWVehicleTools, self).__init__(parent or maya_main_window())
        self.setObjectName(WINDOW_OBJECT_NAME)
        self.setWindowTitle(WINDOW_TITLE)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowType.Window)
        self.setFixedSize(WINDOW_WIDTH, WINDOW_HEIGHT)

        tabs = QtWidgets.QTabWidget()
        for module in _tools():
            tabs.addTab(module.build(self), module.LABEL)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(tabs)


def show():
    """Close any existing instance, then open a fresh one."""
    for widget in maya_main_window().findChildren(QtWidgets.QDialog, WINDOW_OBJECT_NAME):
        widget.close()
        widget.deleteLater()

    dialog = GSWVehicleTools()
    dialog.show()
    return dialog
