# -*- coding: utf-8 -*-
"""
GS File Transfer - move an FBX between DCCs, either through this machine's temp
folder (Local) or through the studio share (Server).

The 3ds Max side of the tool Maya (GSPipeline/Files_IO/gs_file_transfer.py) and
Blender (GS_Pipeline/file_io/file_transfer) also have. The folders and file
names below are a contract between the three; change all three or none:

  Local   one shared file per machine, whichever DCC wrote it or reads it:
          %TEMP%\\GSPipeline\\FileTransferFbx\\transfer.fbx (All), or one
          <object>.fbx per mesh in its individual\\ folder (Individual,
          shelved for now: see INDIVIDUAL_MODE).
  Server  \\\\192.168.1.210\\Temp\\GSPipeline\\FileTransferFbx\\<sender>\\
          <sender>_to_<receiver>.fbx
          - no application in the name: it's plain FBX whatever DCC either side runs.

The window lists those files with when they were written, so a stale one is
obvious before it is imported.

One file for every Max version (Python 3.9+, PySide2 or PySide6):
GS_File_Transfer.mcr in each version folder runs it.
"""

import csv
import datetime
import getpass
import html
import os
import sys
import tempfile
import traceback

import pymxs
from pymxs import runtime as rt

# Tools in the common tree reach the shared helpers in _core the way the Maya
# GSPipeline tools reach theirs.
_HERE = os.path.dirname(os.path.abspath(__file__))
_CORE = os.path.join(os.path.dirname(os.path.dirname(_HERE)), "_core")
if _CORE not in sys.path:
    sys.path.append(_CORE)

import gs_max    # noqa: E402  (must follow the sys.path setup)
import gs_style  # noqa: E402

QtWidgets, QtCore, QtGui = gs_max.qt_modules()

OBJECT_NAME = "GSFileTransferWindow"
WINDOW_TITLE = "GS File Transfer"

# ---------------------------------------------------------------------------
# Locations and names (the contract with the Maya and Blender tools)
# ---------------------------------------------------------------------------
LOCAL_DIR = os.path.join(tempfile.gettempdir(), "GSPipeline", "FileTransferFbx")
LOCAL_DIR_INDIVIDUAL = os.path.join(LOCAL_DIR, "individual")
LOCAL_FILE = os.path.join(LOCAL_DIR, "transfer.fbx")

# Individual mode (one FBX per object, Local only) is shelved: Maya can't send or
# receive it. Off, the Mode row is hidden and every transfer is All, whatever was
# remembered. The code stays; turn this on (here and in the Blender add-on's
# config.py) to bring it back.
INDIVIDUAL_MODE = False

SERVER_DIR = r"\\192.168.1.210\Temp\GSPipeline\FileTransferFbx"
# Combined into one user list, as in the Blender tool.
USER_CSVS = (
    r"\\192.168.1.210\Pipeline\Library\Data\Data_Computer_Update.csv",
    r"\\192.168.1.210\Pipeline\Library\Data\Data_Computer_Manual.csv",
)

# Characters Windows won't take in a file name, replaced in Individual mode.
_BAD_NAME_CHARS = ' :\\/*?"<>|'

# FBX ConvertUnit codes, by units.SystemType.
_UNIT_CODES = {"meters": "m", "inches": "in", "centimeters": "cm", "millimeters": "mm",
               "kilometers": "km", "miles": "mi", "feet": "ft"}

# Preferences remembered between sessions.
_PREF_PREFIX = "gs_file_transfer_"


class TransferError(Exception):
    """Something the artist can put right (selection, missing file): shown without a traceback."""


def current_user():
    return getpass.getuser()


# ---------------------------------------------------------------------------
# User list
# ---------------------------------------------------------------------------
def _normalize_user(raw):
    """'GLENDASTUDIO01\\son.ha.01 (locked)' -> 'son.ha.01', to match getpass.getuser()."""
    name = (raw or "").strip()
    paren = name.find("(")
    if paren != -1:
        name = name[:paren]
    for sep in ("\\", "/"):
        name = name.rsplit(sep, 1)[-1]
    return name.strip()


def _read_users(path):
    """Usernames from one deployment CSV: any column order, header 'User' (or 'Users')."""
    # utf-8-sig: the Update CSV starts with a BOM.
    with open(path, "r", newline="", encoding="utf-8-sig") as fh:
        reader = csv.reader(fh)
        header = next(reader, None) or []
        column = next((i for i, name in enumerate(header)
                       if name.strip().lower() in ("user", "users")), None)
        if column is None:
            raise ValueError("no 'User' column")
        return [_normalize_user(row[column]) for row in reader if len(row) > column]


def read_user_list():
    """Every user from all USER_CSVS, de-duplicated and sorted. An unreadable file is skipped."""
    users = {}
    for path in USER_CSVS:
        try:
            for name in _read_users(path):
                if name:
                    users.setdefault(name.lower(), name)
        except (OSError, ValueError, csv.Error, UnicodeDecodeError) as exc:
            print("[{}] Could not read the user list {}: {}".format(WINDOW_TITLE, path, exc))
    return sorted(users.values(), key=str.lower)


# ---------------------------------------------------------------------------
# FBX import / export
# ---------------------------------------------------------------------------
def _ensure_dir(path):
    try:
        os.makedirs(path, exist_ok=True)
    except OSError:
        raise TransferError("Couldn't create {}.".format(path))


def import_fbx(path, smoothing_groups):
    """Import one FBX into the scene, scaled to the system unit. Returns True."""
    if not os.path.isfile(path):
        raise TransferError("Nothing to import: no file at {}.".format(path))
    kind = str(rt.units.SystemType).lstrip("#").lower()
    rt.pluginManager.loadClass(rt.FBXIMP)
    rt.FBXImporterSetParam("Mode", rt.Name("create"))
    rt.FBXImporterSetParam("SmoothingGroups", bool(smoothing_groups))
    rt.FBXImporterSetParam("ScaleFactor", 1.0 / float(rt.units.SystemScale))
    rt.FBXImporterSetParam("ConvertUnit", _UNIT_CODES.get(kind, "cm"))
    rt.FBXImporterSetParam("Animation", False)
    if not rt.importFile(path, rt.Name("noPrompt"), using=rt.FBXIMP):
        raise TransferError("Max couldn't import {}.".format(path))
    return True


def import_folder(directory, smoothing_groups):
    """Import every FBX in `directory` (a local Individual transfer). Returns how many."""
    try:
        names = sorted(name for name in os.listdir(directory) if name.lower().endswith(".fbx"))
    except OSError:
        names = []
    if not names:
        raise TransferError("Nothing to import: no FBX files in {}.".format(directory))
    for name in names:
        import_fbx(os.path.join(directory, name), smoothing_groups)
    return len(names)


def _exportable(node):
    return rt.superClassOf(node) == rt.GeometryClass and rt.classOf(node) != rt.TargetObject


def _set_export_params():
    rt.pluginManager.loadClass(rt.FBXEXP)
    for name, value in (("Animation", False),
                        ("SmoothingGroups", True),
                        ("SmoothMeshExport", False),
                        ("Shape", False),
                        ("Skin", False),
                        ("Triangulate", False),
                        ("PreserveEdgeOrientation", True),
                        ("Preserveinstances", True),
                        ("EmbedTextures", False),
                        ("ASCII", False),
                        ("FileVersion", "FBX202000")):
        rt.FBXExporterSetParam(name, value)


def export_nodes(nodes, path):
    """
    Export the geometry in `nodes` to `path`.

    Exports copies, named as the originals, so neither the hierarchy around them
    nor anything else selected comes along. The copies and the selection juggling
    stay out of the undo history; the selection is put back afterwards.
    """
    geometry = [node for node in nodes if _exportable(node)]
    if not geometry:
        raise TransferError("Select some geometry to export.")
    _ensure_dir(os.path.dirname(path))
    saved = list(rt.getCurrentSelection())
    copies = []
    with pymxs.undo(False):
        try:
            for node in geometry:
                duplicate = rt.copy(node)
                duplicate.name = node.name
                copies.append(duplicate)
            rt.clearSelection()
            rt.select(copies)
            _set_export_params()
            ok = rt.exportFile(path, rt.Name("noPrompt"), selectedOnly=True, using=rt.FBXEXP)
        finally:
            for duplicate in copies:
                if rt.isValidNode(duplicate):
                    rt.delete(duplicate)
            rt.clearSelection()
            if saved:
                rt.select(saved)
    if not ok:
        raise TransferError("Max couldn't export to {}.".format(path))
    return len(geometry)


def _safe_name(name):
    for char in _BAD_NAME_CHARS:
        name = name.replace(char, "_")
    return name or "object"


def export_individual(nodes, directory):
    """One <object>.fbx per geometry node, in a folder emptied first. Returns how many."""
    geometry = [node for node in nodes if _exportable(node)]
    if not geometry:
        raise TransferError("Select some geometry to export.")
    _ensure_dir(directory)
    # The folder holds one transfer only, so the receiver never picks up
    # objects from an older send.
    for name in os.listdir(directory):
        try:
            os.remove(os.path.join(directory, name))
        except OSError as exc:
            print("[{}] Could not delete {}: {}".format(WINDOW_TITLE, name, exc))
    for node in geometry:
        export_nodes([node], os.path.join(directory, _safe_name(str(node.name)) + ".fbx"))
    return len(geometry)


def server_file(sender, receiver):
    """<sender>_to_<receiver>.fbx, sitting in the sender's folder."""
    return os.path.join(SERVER_DIR, sender, "{}_to_{}.fbx".format(sender, receiver))


# ---------------------------------------------------------------------------
# What is waiting where
# ---------------------------------------------------------------------------
def describe_time(mtime):
    """'Today 14:32', 'Yesterday 09:10' or '12 Nov 09:10' - never goes stale while the window is open."""
    when = datetime.datetime.fromtimestamp(mtime)
    today = datetime.date.today()
    if when.date() == today:
        day = "Today"
    elif when.date() == today - datetime.timedelta(days=1):
        day = "Yesterday"
    else:
        day = "{} {}".format(when.day, when.strftime("%b"))
    return "{} {}".format(day, when.strftime("%H:%M"))


def file_info(path):
    """(name, when written or 'none yet') for one file."""
    try:
        return os.path.basename(path), describe_time(os.path.getmtime(path))
    except OSError:
        return os.path.basename(path), "none yet"


def folder_info(directory):
    """(name, when) for a local Individual transfer: how many files, and the newest."""
    try:
        times = [os.path.getmtime(os.path.join(directory, name))
                 for name in os.listdir(directory) if name.lower().endswith(".fbx")]
    except OSError:
        times = []
    label = "individual\\ ({} file{})".format(len(times), "" if len(times) == 1 else "s")
    return label, describe_time(max(times)) if times else "none yet"


# ---------------------------------------------------------------------------
# Window
# ---------------------------------------------------------------------------
def _pref_get(name, default):
    return gs_max.pref_get(_PREF_PREFIX + name, default)


def _pref_set(name, value):
    gs_max.pref_set(_PREF_PREFIX + name, value)


class FileTransferWindow(QtWidgets.QDialog):

    # Wide enough for a server file name ('<user>_to_<user>.fbx') of the longest
    # user on the list, within these bounds.
    MIN_WIDTH = 380
    MAX_WIDTH = 620
    CAPTION_WIDTH = 56

    def __init__(self, parent=None):
        super(FileTransferWindow, self).__init__(parent or gs_max.main_window())
        self.setObjectName(OBJECT_NAME)
        self.setWindowTitle(WINDOW_TITLE)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.Tool)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setSizeGripEnabled(False)
        self.users = read_user_list()
        self._build()
        self._load_settings()
        self._lock_size()
        if self.users:
            self.set_status("Ready.")
        else:
            self.set_status("User list unavailable - check the server.", "warn")

    def _lock_size(self):
        """Fix the window to its laid-out size, widened so the file names fit."""
        self.ensurePolished()   # Max's style sheet changes font sizes on polish
        self.layout().activate()
        hint = self.sizeHint()
        width = max(hint.width(), min(self._file_row_width(), self.MAX_WIDTH), self.MIN_WIDTH)
        self.setFixedSize(width, hint.height())

    def _file_row_width(self):
        """Window width that shows '<longest user>_to_<me>.fbx' and its time in full."""
        longest = max(self.users, key=len) if self.users else "firstname.lastname.01"
        name, when = self.sent_row
        name_width = name.fontMetrics().horizontalAdvance(
            "{}_to_{}.fbx".format(longest, current_user()))
        when_width = when.fontMetrics().horizontalAdvance("Yesterday 00:00")
        # Plus row spacing, the group box's margins and the window's.
        return self.CAPTION_WIDTH + name_width + when_width + 70

    # -- layout -------------------------------------------------------------
    def _build(self):
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        # Settings
        box = QtWidgets.QGroupBox("Settings")
        rows = QtWidgets.QVBoxLayout(box)
        mode_widget = QtWidgets.QWidget()
        mode_row = QtWidgets.QHBoxLayout(mode_widget)
        mode_row.setContentsMargins(0, 0, 0, 0)
        mode_row.addWidget(QtWidgets.QLabel("Mode:"))
        self.all_radio = QtWidgets.QRadioButton("All")
        self.all_radio.setToolTip("Transfer the whole selection as one FBX.")
        self.individual_radio = QtWidgets.QRadioButton("Individual")
        self.individual_radio.setToolTip("Transfer each selected object as its own FBX (Local only).")
        mode_group = QtWidgets.QButtonGroup(self)
        mode_group.addButton(self.all_radio)
        mode_group.addButton(self.individual_radio)
        mode_row.addWidget(self.all_radio)
        mode_row.addWidget(self.individual_radio)
        mode_row.addStretch(1)
        rows.addWidget(mode_widget)
        mode_widget.setVisible(INDIVIDUAL_MODE)     # shelved: see INDIVIDUAL_MODE
        self.smoothing_check = QtWidgets.QCheckBox("Import Smoothing Groups")
        self.smoothing_check.setToolTip(
            "Rebuild the FBX's smoothing groups on import.\n"
            "Tick it for a Blender export made with Export Smoothing Groups.")
        rows.addWidget(self.smoothing_check)
        root.addWidget(box)

        # Local: one shared file, so no app picker - whatever exported last imports.
        box = QtWidgets.QGroupBox("Local")
        box.setToolTip("Hand off through this machine's temp folder, to or from any DCC.")
        column = QtWidgets.QVBoxLayout(box)
        column.addLayout(self._button_pair(
            ("Import", self._on_local_import, "Import the last local export, from any DCC."),
            ("Export", self._on_local_export, "Export the selection for any DCC on this machine.")))
        self.local_row = self._file_row(column, "File", "The shared local file, and when it was "
                                                        "last exported.")
        root.addWidget(box)

        # Server: one user picker shared by both directions. No application
        # picker: the file is plain FBX, whatever DCC either side runs.
        box = QtWidgets.QGroupBox("Server")
        box.setToolTip("Hand off to another artist through the studio share.")
        column = QtWidgets.QVBoxLayout(box)
        user_row = QtWidgets.QHBoxLayout()
        user_row.addWidget(QtWidgets.QLabel("User:"))
        self.user_combo = QtWidgets.QComboBox()
        self.user_combo.setEditable(True)
        self.user_combo.setInsertPolicy(QtWidgets.QComboBox.NoInsert)
        self.user_combo.addItems(self.users)
        self.user_combo.lineEdit().setPlaceholderText("Type to search...")
        self.user_combo.setToolTip("Who you are sending to / receiving from. Type to search.")
        completer = self.user_combo.completer()
        completer.setFilterMode(QtCore.Qt.MatchContains)
        completer.setCompletionMode(QtWidgets.QCompleter.PopupCompletion)
        completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        user_row.addWidget(self.user_combo, 1)
        refresh = QtWidgets.QToolButton()
        refresh.setText(u"↻")
        refresh.setToolTip("Check the files again.")
        refresh.clicked.connect(self.refresh_files)
        user_row.addWidget(refresh)
        column.addLayout(user_row)

        self.received_row = self._file_row(column, "Received",
                                           "What the selected user sent you, and when.")
        self.sent_row = self._file_row(column, "Sent",
                                       "What you last sent the selected user, and when.")
        column.addLayout(self._button_pair(
            ("Import", self._on_server_import, "Import what the selected user sent you."),
            ("Export", self._on_server_export, "Send the selection to the selected user.")))
        root.addWidget(box)

        # Footer: one-line result, then who this machine is.
        self.status_label = QtWidgets.QLabel()
        self.status_label.setWordWrap(True)
        root.addWidget(self.status_label)
        root.addWidget(QtWidgets.QLabel("Current user: {}".format(current_user())))

    @staticmethod
    def _action_button(text, colour, slot, tooltip):
        button = QtWidgets.QPushButton(text)
        button.setToolTip(tooltip)
        button.setMinimumHeight(28)
        gs_style.style_button(button, colour)
        button.clicked.connect(slot)
        return button

    def _button_pair(self, first, second):
        """Import (studio red) and Export (studio orange), side by side."""
        row = QtWidgets.QHBoxLayout()
        for (text, slot, tooltip), colour in ((first, gs_style.STUDIO_RED),
                                              (second, gs_style.STUDIO_ORANGE)):
            row.addWidget(self._action_button(text, colour, slot, tooltip), 1)
        return row

    @staticmethod
    def _file_row(column, label, tooltip):
        """One file line: what it is, its name, and when it was written. Returns the two value labels."""
        row = QtWidgets.QHBoxLayout()
        caption = QtWidgets.QLabel(label)
        caption.setFixedWidth(FileTransferWindow.CAPTION_WIDTH)
        caption.setToolTip(tooltip)
        name = QtWidgets.QLabel()
        name.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        # A long user name is clipped, not allowed to widen the fixed window;
        # the tooltip holds the full path.
        name.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Preferred)
        when = QtWidgets.QLabel()
        when.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        font = when.font()
        font.setBold(True)
        when.setFont(font)
        row.addWidget(caption)
        row.addWidget(name, 1)
        row.addWidget(when)
        column.addLayout(row)
        return name, when

    # -- settings -----------------------------------------------------------
    def _load_settings(self):
        (self.individual_radio if _pref_get("individual", 0) else self.all_radio).setChecked(True)
        self.smoothing_check.setChecked(bool(_pref_get("import_smoothing_groups", 0)))
        user = _pref_get("user", "")
        self.user_combo.setCurrentIndex(self.user_combo.findText(user) if user in self.users else -1)
        if user not in self.users:
            self.user_combo.setEditText("")
        # Connected after the restore, so it doesn't fire once per setting.
        self.user_combo.currentTextChanged.connect(self._on_user_changed)
        self.individual_radio.toggled.connect(lambda *_args: self.refresh_files())
        self.refresh_files()

    def _save_settings(self):
        _pref_set("individual", int(self.individual_radio.isChecked()))
        _pref_set("import_smoothing_groups", int(self.smoothing_check.isChecked()))
        user = self.user_combo.currentText().strip()
        if user in self.users:
            _pref_set("user", user)

    def _individual(self):
        """True when Local transfers go one FBX per object. Always False while shelved."""
        return INDIVIDUAL_MODE and self.individual_radio.isChecked()

    # -- file rows ----------------------------------------------------------
    def _on_user_changed(self, text):
        # Typing to search changes the text on every key; only a real user is looked up.
        if text.strip() in self.users or not text.strip():
            self.refresh_files()

    @staticmethod
    def _show(row, info, tooltip=""):
        name, when = row
        name.setText(info[0])
        when.setText(info[1])
        name.setToolTip(tooltip)
        when.setToolTip(tooltip)

    def refresh_files(self):
        """Re-read the local file and, for the picked user, the files in both directions."""
        if self._individual():
            self._show(self.local_row, folder_info(LOCAL_DIR_INDIVIDUAL), LOCAL_DIR_INDIVIDUAL)
        else:
            self._show(self.local_row, file_info(LOCAL_FILE), LOCAL_FILE)
        if not self.users:
            # The share wasn't reachable when the window opened; don't block on it again.
            self._show(self.received_row, ("(server unavailable)", ""))
            self._show(self.sent_row, ("", ""))
            return
        other = self.user_combo.currentText().strip()
        if other not in self.users:
            self._show(self.received_row, ("(pick a user)", ""))
            self._show(self.sent_row, ("", ""))
            return
        me = current_user()
        for row, path in ((self.received_row, server_file(other, me)),
                          (self.sent_row, server_file(me, other))):
            self._show(row, file_info(path), path)

    # -- status -------------------------------------------------------------
    def set_status(self, message, level=None):
        colour = gs_style.LOG_COLOURS.get(level)
        text = html.escape(message)
        if colour:
            text = '<span style="color:{}; font-weight:bold">{}</span>'.format(colour, text)
        self.status_label.setText(text)

    def _run(self, function, *args):
        """Call `function` with a wait cursor; show its failure instead of raising."""
        self._save_settings()
        QtWidgets.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
        try:
            return function(*args)
        except TransferError as exc:
            self.set_status(str(exc), "error")
            print("[{}] {}".format(WINDOW_TITLE, exc))
        except Exception as exc:            # keep the window alive, keep the traceback
            traceback.print_exc()
            self.set_status("Something went wrong: {}. Details in the MAXScript Listener."
                            .format(exc), "error")
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()
            rt.redrawViews()
            self.refresh_files()
        return None

    def _selected_user(self):
        user = self.user_combo.currentText().strip()
        if user not in self.users:
            self.set_status("Pick a user first.", "warn")
            return None
        return user

    # -- actions ------------------------------------------------------------
    def _on_local_import(self):
        smoothing = self.smoothing_check.isChecked()
        if self._individual():
            count = self._run(import_folder, LOCAL_DIR_INDIVIDUAL, smoothing)
            if count:
                self.set_status("Imported {} object file(s) (local).".format(count), "ok")
        elif self._run(import_fbx, LOCAL_FILE, smoothing):
            self.set_status("Imported (local).", "ok")

    def _on_local_export(self):
        nodes = list(rt.getCurrentSelection())
        if self._individual():
            count = self._run(export_individual, nodes, LOCAL_DIR_INDIVIDUAL)
            if count:
                self.set_status("Exported {} object(s) individually (local).".format(count), "ok")
        elif self._run(export_nodes, nodes, LOCAL_FILE):
            self.set_status("Exported (local).", "ok")

    def _on_server_import(self):
        sender = self._selected_user()
        if not sender:
            return
        path = server_file(sender, current_user())
        if self._run(import_fbx, path, self.smoothing_check.isChecked()):
            self.set_status("Imported from {}.".format(sender), "ok")

    def _on_server_export(self):
        receiver = self._selected_user()
        if not receiver:
            return
        path = server_file(current_user(), receiver)
        if self._run(export_nodes, list(rt.getCurrentSelection()), path):
            self.set_status("Sent to {}.".format(receiver), "ok")


def show():
    """Open the window, closing any copy already open."""
    parent = gs_max.main_window()
    for widget in parent.findChildren(QtWidgets.QDialog, OBJECT_NAME):
        widget.close()
        widget.deleteLater()
    window = FileTransferWindow(parent)
    window.show()
    return window


if __name__ == "__main__":
    gs_max.launch(__file__)
