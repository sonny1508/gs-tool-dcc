# -*- coding: utf-8 -*-
"""
GS File Transfer - move an FBX between DCCs, either through this machine's temp
folder (Local) or through the studio share (Server).

Local is one shared file per machine, %TEMP%\\GSPipeline\\FileTransferFbx\\transfer.fbx,
whichever DCC wrote it or reads it - the same path the Blender and 3ds Max tools
use. Server files name only the two artists: [sender]_to_[receiver].fbx, in the
sender's folder. The window lists those files with when they were written, so a
stale one is obvious before it is imported.

Maya 2022+ / Python 3 only. The pipeline no longer ships anything older, so
every FBX plug-in command used here is called directly instead of being probed
for support first.

All FBX settings live in GSPipeline/_core/gs_fbx.py, shared with GS File
Exporter, so the two tools can no longer leak sticky plug-in state into each
other. Nothing in this file touches an FBX* command directly.
"""

import os
import sys
import csv
import datetime
import getpass
import tempfile

import maya.cmds as cmds

# GSPipeline launches tools by exec'ing scripts, so _core is not on sys.path.
# Put it there once, the same way 02_Normals reaches gs_normal_core.
_CORE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_core')
if _CORE not in sys.path:
    sys.path.append(_CORE)

import gs_fbx  # noqa: E402  (must follow the sys.path setup)

# ============================================================================
# CONFIGURATION
# ============================================================================

FBX_SETTINGS = {
    # Which gs_fbx preset this tool exports and imports with. Scale, FBX
    # version, up axis and the rest of the plug-in contract live there.
    'preset': 'transfer',

    # Import defaults (used before the UI exists, and as the checkbox values)
    'import_smoothing_groups_default': True,
    'import_unlock_normals_default': False,
    'import_as_new_objects_default': False,

    'file_extension': '.fbx',

    # Server locations
    'server_path': r'\\192.168.1.210\Temp\GSPipeline\FileTransferFbx',
    'library_path': r'\\192.168.1.210\Pipeline\Library\Data',
    'csv_filename': 'Data_Computer_Update.csv',
    'csv_user_column': 'User',

    # Local hand-off, shared with the Blender and 3ds Max tools: one file in
    # %TEMP%\GSPipeline\FileTransferFbx, whichever DCC wrote it.
    'local_subfolders': ('GSPipeline', 'FileTransferFbx'),
    'local_filename': 'transfer',
}

VERSION = '1.8'

# UI control names
WINDOW = 'GS_File_Transfer_Window'
SEARCH_FIELD = 'GS_FT_UserSearch'
USER_MENU = 'GS_FT_UserMenu'
STATUS_TEXT = 'GS_FT_Status'
# File rows: (name text, time text) per row.
LOCAL_ROW = ('GS_FT_LocalName', 'GS_FT_LocalTime')
RECEIVED_ROW = ('GS_FT_ReceivedName', 'GS_FT_ReceivedTime')
SENT_ROW = ('GS_FT_SentName', 'GS_FT_SentTime')
CB_SMOOTHING = 'GS_FT_Smoothing'
CB_UNLOCK_NORMALS = 'GS_FT_UnlockNormals'
CB_ADD_NEW = 'GS_FT_AddNew'

# optionVar keys - remember the last picks between sessions
OPTVAR_USER = 'GS_FileTransfer_LastUser'

# Placeholder entries so the dropdown is never empty (querying an empty
# optionMenu raises) and so an unusable state is obvious to the artist.
NO_MATCH = '(no match)'
NO_USERS = '(user list unavailable)'
PLACEHOLDERS = (NO_MATCH, NO_USERS)

# Footer status band. Always filled, so it reads as a field from the moment the
# tool opens; the colour is what carries the result.
STATUS_COLOURS = {
    'idle': (0.24, 0.24, 0.26),
    'ok': (0.22, 0.38, 0.24),
    'warn': (0.46, 0.31, 0.14),
}

# Full user list, loaded once when the window is built.
ALL_USERS = []


# ============================================================================
# USER LIST
# ============================================================================

def normalize_username(raw):
    """
    Normalize a CSV user value to a bare username.

    The PDQ-deployed CSV stores entries like 'GLENDASTUDIO01\\son.ha.01 (locked)'.
    Strip the leading 'DOMAIN\\' part and any trailing ' (locked)' / '(...)' marker
    so only 'son.ha.01' remains. This must match getpass.getuser() so the exported
    FBX filename is unchanged.
    """
    if not raw:
        return ''
    name = raw.strip()
    # Drop trailing parenthetical markers, e.g. ' (locked)'
    paren_idx = name.find('(')
    if paren_idx != -1:
        name = name[:paren_idx]
    name = name.strip()
    # Drop leading DOMAIN\ prefix (handle both back- and forward-slash)
    for sep in ('\\', '/'):
        if sep in name:
            name = name.rsplit(sep, 1)[-1]
    return name.strip()


def _find_user_column(fieldnames):
    """Resolve which CSV column holds usernames, tolerating header variations."""
    if not fieldnames:
        return None
    candidates = [FBX_SETTINGS['csv_user_column'].lower(),
                  'user', 'username', 'name', 'users', 'user_name']
    for candidate in candidates:
        for field in fieldnames:
            if field and field.strip().lower() == candidate:
                return field
    return None


def load_users_from_csv():
    """
    Read the PDQ-generated computer/user CSV from the library share.

    Returns a de-duplicated, alphabetically sorted list of bare usernames. On any
    failure it warns and returns an empty list rather than inventing placeholder
    names - an empty dropdown makes an unreachable share immediately obvious.
    """
    csv_path = os.path.join(FBX_SETTINGS['library_path'], FBX_SETTINGS['csv_filename'])

    if not os.path.isfile(csv_path):
        cmds.warning('GS File Transfer: user list not found at {0}'.format(csv_path))
        return []

    users = set()
    try:
        # utf-8-sig strips the BOM PDQ writes; without it the first header reads
        # as '\ufeffUser' and the column lookup silently fails.
        with open(csv_path, 'r', encoding='utf-8-sig', newline='') as csvfile:
            sample = csvfile.read(1024)
            csvfile.seek(0)
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=',;\t|')
                reader = csv.DictReader(csvfile, dialect=dialect)
            except csv.Error:
                reader = csv.DictReader(csvfile, delimiter=',')

            column = _find_user_column(reader.fieldnames)
            if not column:
                cmds.warning('GS File Transfer: no user column found in {0}'.format(csv_path))
                return []

            for row in reader:
                name = normalize_username(row.get(column, ''))
                if name:
                    users.add(name)
    except (IOError, OSError, csv.Error, UnicodeDecodeError) as exc:
        cmds.warning('GS File Transfer: could not read user list - {0}'.format(exc))
        return []

    return sorted(users, key=lambda name: name.lower())


# ============================================================================
# HELPERS
# ============================================================================

def current_user():
    return getpass.getuser()


def set_status(message, level='ok'):
    """
    Show a one-line result in the footer.

    The band is always filled so it reads as a status field on launch, and
    recolours per level so a result reads as *new* at a glance: neutral grey
    while idle, green for a completed transfer, amber for anything the artist
    has to fix. Idle stays in the plain font; a result goes bold.
    """
    if not cmds.text(STATUS_TEXT, exists=True):
        return
    cmds.text(STATUS_TEXT, edit=True,
              label='  {0}'.format(message),
              enableBackground=True,
              backgroundColor=STATUS_COLOURS.get(level, STATUS_COLOURS['idle']),
              font='plainLabelFont' if level == 'idle' else 'boldLabelFont')


def checkbox_value(name, settings_key):
    """Read a UI checkbox, falling back to the configured default when the window is closed."""
    if cmds.checkBox(name, exists=True):
        return cmds.checkBox(name, query=True, value=True)
    return FBX_SETTINGS[settings_key]


def local_transfer_path():
    return os.path.join(tempfile.gettempdir(), *FBX_SETTINGS['local_subfolders'])


def describe_time(mtime):
    """'Today 14:32', 'Yesterday 09:10' or '12 Nov 09:10' - never goes stale while the window is open."""
    when = datetime.datetime.fromtimestamp(mtime)
    today = datetime.date.today()
    if when.date() == today:
        day = 'Today'
    elif when.date() == today - datetime.timedelta(days=1):
        day = 'Yesterday'
    else:
        day = '{0} {1}'.format(when.day, when.strftime('%b'))
    return '{0} {1}'.format(day, when.strftime('%H:%M'))


def file_time(path):
    """When the file at `path` was written, as describe_time() puts it, or 'none yet'."""
    try:
        return describe_time(os.path.getmtime(path))
    except OSError:
        return 'none yet'


def ensure_directory(path):
    if os.path.isdir(path):
        return True
    try:
        os.makedirs(path)
        return True
    except OSError as exc:
        set_status('Could not create {0}'.format(path), 'warn')
        cmds.warning('GS File Transfer: {0}'.format(exc))
        return False


# ============================================================================
# FILE OPERATIONS
# ============================================================================

def import_fbx(file_path, label):
    if not os.path.isfile(file_path):
        cmds.confirmDialog(title='Import Error',
                           message='No file waiting at:\n{0}'.format(file_path),
                           button='OK')
        set_status('Nothing to import {0}'.format(label), 'warn')
        return False

    gs_fbx.import_file(
        file_path,
        preset=FBX_SETTINGS['preset'],
        smoothing_groups=checkbox_value(CB_SMOOTHING, 'import_smoothing_groups_default'),
        unlock_normals=checkbox_value(CB_UNLOCK_NORMALS, 'import_unlock_normals_default'),
        add_as_new=checkbox_value(CB_ADD_NEW, 'import_as_new_objects_default'))
    set_status('Imported {0}'.format(label))
    return True


def export_fbx(file_path, label):
    if not cmds.ls(selection=True):
        cmds.confirmDialog(title='Nothing Selected',
                           message='Select the objects you want to export first.',
                           button='OK')
        set_status('Nothing selected', 'warn')
        return False

    if not ensure_directory(os.path.dirname(file_path)):
        return False

    gs_fbx.export_selection(file_path, preset=FBX_SETTINGS['preset'])
    set_status('Exported {0}'.format(label))
    return True


# --- Local (this machine's temp folder) --------------------------------------

def local_file():
    return os.path.join(local_transfer_path(),
                        FBX_SETTINGS['local_filename'] + FBX_SETTINGS['file_extension'])


def local_import(*_args):
    import_fbx(local_file(), '(local)')
    refresh_files()


def local_export(*_args):
    export_fbx(local_file(), '(local)')
    refresh_files()


# --- Server (studio share) ---------------------------------------------------

def selected_user():
    """The other artist in the transfer, or None when nothing usable is picked."""
    value = cmds.optionMenu(USER_MENU, query=True, value=True)
    if not value or value in PLACEHOLDERS:
        set_status('Pick a user first', 'warn')
        return None
    return value


def server_file(sender, receiver):
    """[sender]_to_[receiver].fbx, sitting in the sender's folder. No application in the name."""
    filename = '{0}_to_{1}{2}'.format(sender, receiver, FBX_SETTINGS['file_extension'])
    return os.path.join(FBX_SETTINGS['server_path'], sender, filename)


def server_import(*_args):
    other_user = selected_user()
    if not other_user:
        return
    import_fbx(server_file(other_user, current_user()), 'from {0}'.format(other_user))
    refresh_files()


def server_export(*_args):
    other_user = selected_user()
    if not other_user:
        return
    export_fbx(server_file(current_user(), other_user), 'to {0}'.format(other_user))
    refresh_files()


# --- File rows: what is waiting where, and since when ------------------------

def _set_row(row, path):
    name_text, time_text = row
    if not cmds.text(name_text, exists=True):
        return
    cmds.text(name_text, edit=True, label=os.path.basename(path), annotation=path)
    cmds.text(time_text, edit=True, label=file_time(path), annotation=path)


def _clear_row(row, label):
    name_text, time_text = row
    if cmds.text(name_text, exists=True):
        cmds.text(name_text, edit=True, label=label, annotation='')
        cmds.text(time_text, edit=True, label='', annotation='')


def refresh_files(*_args):
    """Re-read the local file and, for the picked user, the files in both directions."""
    _set_row(LOCAL_ROW, local_file())
    if not ALL_USERS:
        # The share wasn't reachable when the window opened; don't block on it again.
        _clear_row(RECEIVED_ROW, '(server unavailable)')
        _clear_row(SENT_ROW, '')
        return
    if not cmds.optionMenu(USER_MENU, exists=True):
        return
    other_user = cmds.optionMenu(USER_MENU, query=True, value=True)
    if not other_user or other_user in PLACEHOLDERS:
        _clear_row(RECEIVED_ROW, '(pick a user)')
        _clear_row(SENT_ROW, '')
        return
    me = current_user()
    _set_row(RECEIVED_ROW, server_file(other_user, me))
    _set_row(SENT_ROW, server_file(me, other_user))


# ============================================================================
# USER DROPDOWN + SEARCH
# ============================================================================

def refresh_user_menu(*_args):
    """Rebuild the user dropdown from the search box, keeping the selection if it survives."""
    query = cmds.textField(SEARCH_FIELD, query=True, text=True).strip().lower()
    matches = [user for user in ALL_USERS if query in user.lower()] if query else list(ALL_USERS)

    # Querying the value of an empty optionMenu raises, so only ask once it is populated.
    existing = cmds.optionMenu(USER_MENU, query=True, itemListLong=True) or []
    previous = cmds.optionMenu(USER_MENU, query=True, value=True) if existing else None

    for item in existing:
        cmds.deleteUI(item)

    cmds.setParent(USER_MENU, menu=True)
    if matches:
        for user in matches:
            cmds.menuItem(label=user)
    else:
        cmds.menuItem(label=NO_MATCH if ALL_USERS else NO_USERS)
    cmds.setParent('..', menu=True)

    if previous in matches:
        cmds.optionMenu(USER_MENU, edit=True, value=previous)
    refresh_files()


def remember_user(value):
    if value not in PLACEHOLDERS:
        cmds.optionVar(stringValue=(OPTVAR_USER, value))
    refresh_files()


def restore_menu(menu, optvar, valid_values):
    """Re-select whatever was picked last session, if it is still a valid entry."""
    if not cmds.optionVar(exists=optvar):
        return
    saved = cmds.optionVar(query=optvar)
    if saved in valid_values:
        cmds.optionMenu(menu, edit=True, value=saved)


# ============================================================================
# UI
# ============================================================================

def build_import_settings(parent):
    cmds.frameLayout(parent=parent, collapsable=True, label='Import Settings',
                     marginWidth=5, marginHeight=5)
    cmds.columnLayout(adjustableColumn=True, rowSpacing=2)
    cmds.checkBox(CB_SMOOTHING, label='Smoothing Groups',
                  value=FBX_SETTINGS['import_smoothing_groups_default'],
                  annotation='Rebuild the soft/hard edges from the FBX smoothing groups. '
                             'Maya and 3ds Max exports carry them; Blender exports do not')
    cmds.checkBox(CB_UNLOCK_NORMALS, label='Unlock Normals',
                  value=FBX_SETTINGS['import_unlock_normals_default'],
                  annotation='Unlock the imported vertex normals so Maya recomputes them')
    cmds.checkBox(CB_ADD_NEW, label='Add As New Objects',
                  value=FBX_SETTINGS['import_as_new_objects_default'],
                  annotation='On: keep what is already in the scene, bring the FBX in as new nodes.\n'
                             'Off: let the FBX merge into existing nodes with the same name.')
    cmds.setParent(parent)


def build_local_section(parent):
    cmds.frameLayout(parent=parent, collapsable=True, label='Local', marginWidth=5, marginHeight=5,
                     annotation="Hand off through this machine's temp folder, to or from any DCC")
    # One shared file, so no app picker: whatever exported last is what imports.
    cmds.columnLayout(adjustableColumn=True, rowSpacing=4)
    build_two_buttons('Import', local_import, 'Import the last local export, from any DCC',
                      'Export', local_export, 'Export the selection for any DCC on this machine')
    build_file_row(LOCAL_ROW, 'File', 'The shared local file and when it was last exported')
    cmds.setParent(parent)


def build_two_buttons(left_label, left_command, left_tip, right_label, right_command, right_tip):
    """Two equal buttons side by side, filling the row."""
    form = cmds.formLayout(numberOfDivisions=100)
    left = cmds.button(height=25, label=left_label, command=left_command, annotation=left_tip)
    right = cmds.button(height=25, label=right_label, command=right_command, annotation=right_tip)
    cmds.formLayout(form, edit=True,
                    attachForm=[(left, 'top', 0), (left, 'left', 0),
                                (right, 'top', 0), (right, 'right', 0)],
                    attachPosition=[(left, 'right', 2, 50), (right, 'left', 2, 50)])
    cmds.setParent('..')


def build_file_row(row, label, tip):
    """One file line: what it is, its name, and when it was written."""
    name_text, time_text = row
    cmds.rowLayout(numberOfColumns=3, adjustableColumn=2,
                   columnWidth3=(58, 140, 92),
                   columnAlign3=('left', 'left', 'right'),
                   columnAttach=[(1, 'both', 0), (2, 'both', 2), (3, 'both', 0)],
                   annotation=tip)
    cmds.text(label=label, align='left', annotation=tip)
    cmds.text(name_text, label='', align='left', font='smallPlainLabelFont')
    cmds.text(time_text, label='', align='right', font='smallBoldLabelFont')
    cmds.setParent('..')


def build_server_section(parent):
    cmds.frameLayout(parent=parent, collapsable=True, label='Server', marginWidth=5, marginHeight=5,
                     annotation='Hand off through the studio share')
    column = cmds.columnLayout(adjustableColumn=True, rowSpacing=4)

    # --- One user picker, shared by both import and export ---
    cmds.rowLayout(numberOfColumns=2, adjustableColumn=1,
                   columnAttach=[(1, 'both', 0), (2, 'both', 0)])
    cmds.text(label='User', align='left')
    cmds.symbolButton(image='refresh.png', width=20, height=20, command=refresh_files,
                      annotation='Check the files again')
    cmds.setParent(column)
    user_form = cmds.formLayout(numberOfDivisions=100)
    search = cmds.textField(SEARCH_FIELD,
                            placeholderText='Search users...',
                            textChangedCommand=refresh_user_menu,
                            annotation='Filter the list below - case-insensitive, matches anywhere in the name')
    menu = cmds.optionMenu(USER_MENU, changeCommand=remember_user,
                           annotation='Who you are sending to / receiving from')
    cmds.setParent('..', menu=True)
    # Both attached left and right, so the field and the dropdown share one width.
    cmds.formLayout(user_form, edit=True,
                    attachForm=[(search, 'left', 0), (search, 'right', 0), (search, 'top', 0),
                                (menu, 'left', 0), (menu, 'right', 0)],
                    attachControl=[(menu, 'top', 4, search)])
    cmds.setParent(column)

    cmds.separator(height=6, style='in')

    # --- What is waiting in each direction, then the two actions ---
    # No application picker: the file is plain FBX, whatever DCC either side runs.
    build_file_row(RECEIVED_ROW, 'Received', 'What the selected user sent you, and when')
    build_file_row(SENT_ROW, 'Sent', 'What you last sent the selected user, and when')
    cmds.separator(height=4, style='none')
    build_two_buttons('Import', server_import, 'Import what the selected user sent you',
                      'Export', server_export, 'Send the selection to the selected user')

    cmds.setParent(parent)


def build_footer(parent):
    cmds.separator(height=8, style='in')

    # Status band first, current user underneath it.
    cmds.rowLayout(numberOfColumns=1, adjustableColumn=1, columnAttach=[(1, 'both', 6)])
    cmds.text(STATUS_TEXT, label='  Ready', align='left', height=22,
              font='plainLabelFont',
              enableBackground=True, backgroundColor=STATUS_COLOURS['idle'])
    cmds.setParent(parent)

    cmds.rowLayout(numberOfColumns=2, adjustableColumn=2,
                   columnWidth2=(90, 200), columnAlign2=('left', 'left'),
                   columnAttach=[(1, 'both', 6), (2, 'both', 0)])
    cmds.text(label='Current user:', align='left')
    cmds.text(label=current_user(), align='left')
    cmds.setParent(parent)


def GS_File_Transfer_UI():
    """Build and show the File Transfer window."""
    global ALL_USERS
    ALL_USERS = load_users_from_csv()

    if cmds.window(WINDOW, exists=True):
        cmds.deleteUI(WINDOW)

    # Drop the remembered size, so the window always opens at what its content needs.
    if cmds.windowPref(WINDOW, exists=True):
        cmds.windowPref(WINDOW, remove=True)

    window = cmds.window(WINDOW, title='GS File Transfer  v{0}'.format(VERSION), width=320,
                         resizeToFitChildren=True,
                         minimizeButton=False, maximizeButton=False, sizeable=False)
    main = cmds.columnLayout(adjustableColumn=True, rowSpacing=4)

    build_import_settings(main)
    build_local_section(main)
    build_server_section(main)
    build_footer(main)

    # Populate the user dropdown, then restore last session's picks.
    refresh_user_menu()
    restore_menu(USER_MENU, OPTVAR_USER, ALL_USERS)
    refresh_files()

    if not ALL_USERS:
        set_status('User list unavailable - check the share', 'warn')

    cmds.showWindow(window)


if __name__ == '__main__':
    GS_File_Transfer_UI()
