# -*- coding: utf-8 -*-
"""
GS File Transfer - move an FBX between DCCs, either through this machine's temp
folder (Local) or through the studio share (Server).

Maya 2022+ / Python 3 only. The pipeline no longer ships anything older, so
every FBX plug-in command used here is called directly instead of being probed
for support first.
"""

import os
import csv
import getpass
import tempfile

import maya.cmds as cmds
import maya.mel as mel

# ============================================================================
# CONFIGURATION
# ============================================================================

FBX_SETTINGS = {
    # Scale
    'import_scale_factor': 1.0,
    'export_scale_factor': 1.0,

    # Import defaults (used before the UI exists, and as the checkbox values)
    'import_smoothing_groups_default': True,
    'import_unlock_normals_default': False,
    'import_as_new_objects_default': False,

    # Export
    'export_file_version': 'FBX202000',
    'export_binary': True,

    'file_extension': '.fbx',

    # Server locations
    'server_path': r'\\192.168.1.210\Temp\File_Transfer',
    'library_path': r'\\192.168.1.210\Pipeline\Library\Data',
    'csv_filename': 'Data_Computer_Auto.csv',
    'csv_user_column': 'User',

    'local_temp_subfolder': 'fileTransferFbx',

    'supported_apps': ['Blender', 'Maya', 'Max'],
}

VERSION = '1.5'

# UI control names
WINDOW = 'GS_File_Transfer_Window'
SEARCH_FIELD = 'GS_FT_UserSearch'
USER_MENU = 'GS_FT_UserMenu'
APP_IMPORT_MENU = 'GS_FT_AppImport'
APP_EXPORT_MENU = 'GS_FT_AppExport'
STATUS_TEXT = 'GS_FT_Status'
CB_SMOOTHING = 'GS_FT_Smoothing'
CB_UNLOCK_NORMALS = 'GS_FT_UnlockNormals'
CB_ADD_NEW = 'GS_FT_AddNew'

# optionVar keys - remember the last picks between sessions
OPTVAR_USER = 'GS_FileTransfer_LastUser'
OPTVAR_APP_IMPORT = 'GS_FileTransfer_ImportApp'
OPTVAR_APP_EXPORT = 'GS_FileTransfer_ExportApp'

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


def mel_path(path):
    """MEL only accepts forward slashes inside quoted paths."""
    return path.replace('\\', '/')


def mel_bool(value):
    return 'true' if value else 'false'


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
    return os.path.join(tempfile.gettempdir(), FBX_SETTINGS['local_temp_subfolder'])


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
# FBX SETTINGS
# ============================================================================

def apply_import_settings():
    """Push the current import options into the FBX plug-in."""
    mel.eval('FBXImportScaleFactor {0};'.format(FBX_SETTINGS['import_scale_factor']))
    mel.eval('FBXImportSmoothingGroups -v {0};'.format(
        mel_bool(checkbox_value(CB_SMOOTHING, 'import_smoothing_groups_default'))))
    mel.eval('FBXImportUnlockNormals -v {0};'.format(
        mel_bool(checkbox_value(CB_UNLOCK_NORMALS, 'import_unlock_normals_default'))))

    # 'add' keeps everything already in the scene and brings the FBX contents in
    # as new nodes (Maya auto-numbers name clashes); 'merge' lets the FBX write
    # into existing nodes of the same name. These are sticky plug-in settings, so
    # set them explicitly every time rather than inheriting whatever the artist
    # last picked in Maya's own FBX import dialog.
    add_new = checkbox_value(CB_ADD_NEW, 'import_as_new_objects_default')
    mel.eval('FBXImportMode -v {0};'.format('add' if add_new else 'merge'))


def apply_export_settings():
    """Push the export options into the FBX plug-in."""
    mel.eval('FBXExportScaleFactor {0};'.format(FBX_SETTINGS['export_scale_factor']))
    mel.eval('FBXExportFileVersion -v "{0}";'.format(FBX_SETTINGS['export_file_version']))
    mel.eval('FBXExportInAscii -v {0};'.format(mel_bool(not FBX_SETTINGS['export_binary'])))


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

    apply_import_settings()
    mel.eval('FBXImport -f "{0}";'.format(mel_path(file_path)))
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

    apply_export_settings()
    mel.eval('FBXExport -f "{0}" -s;'.format(mel_path(file_path)))
    set_status('Exported {0}'.format(label))
    return True


# --- Local (this machine's temp folder) --------------------------------------

def local_file(source_app, target_app):
    name = '{0}_to_{1}{2}'.format(source_app.lower(), target_app.lower(),
                                  FBX_SETTINGS['file_extension'])
    return os.path.join(local_transfer_path(), name)


def local_import(app):
    import_fbx(local_file(app, 'maya'), 'from {0} (local)'.format(app))


def local_export(app):
    export_fbx(local_file('maya', app), 'to {0} (local)'.format(app))


# --- Server (studio share) ---------------------------------------------------

def selected_user():
    """The other artist in the transfer, or None when nothing usable is picked."""
    value = cmds.optionMenu(USER_MENU, query=True, value=True)
    if not value or value in PLACEHOLDERS:
        set_status('Pick a user first', 'warn')
        return None
    return value


def server_import(*_args):
    other_user = selected_user()
    if not other_user:
        return
    source_app = cmds.optionMenu(APP_IMPORT_MENU, query=True, value=True).lower()
    # [source_user]_[source_app]_to_maya_[me].fbx, sitting in the sender's folder
    filename = '{0}_{1}_to_maya_{2}{3}'.format(other_user, source_app, current_user(),
                                               FBX_SETTINGS['file_extension'])
    import_fbx(os.path.join(FBX_SETTINGS['server_path'], other_user, filename),
               'from {0}'.format(other_user))


def server_export(*_args):
    other_user = selected_user()
    if not other_user:
        return
    me = current_user()
    target_app = cmds.optionMenu(APP_EXPORT_MENU, query=True, value=True).lower()
    # [me]_maya_to_[target_app]_[target_user].fbx, sitting in my own folder
    filename = '{0}_maya_to_{1}_{2}{3}'.format(me, target_app, other_user,
                                               FBX_SETTINGS['file_extension'])
    export_fbx(os.path.join(FBX_SETTINGS['server_path'], me, filename),
               'to {0}'.format(other_user))


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


def remember_user(value):
    if value not in PLACEHOLDERS:
        cmds.optionVar(stringValue=(OPTVAR_USER, value))


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
    cmds.checkBox(CB_SMOOTHING, label='Import Smoothing Groups',
                  value=FBX_SETTINGS['import_smoothing_groups_default'],
                  annotation='Rebuild the FBX smoothing groups as Maya soft/hard edges')
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
                     annotation="Hand off through this machine's temp folder")
    form = cmds.formLayout(numberOfDivisions=100)

    frames = []
    for app in FBX_SETTINGS['supported_apps']:
        frame = cmds.frameLayout(parent=form, collapsable=False, label=app)
        cmds.columnLayout(adjustableColumn=True, rowSpacing=4)
        cmds.separator(height=2, style='none')
        cmds.button(height=25, label='Import',
                    command=lambda _x, a=app: local_import(a),
                    annotation='Import {0}'.format(local_file(app, 'maya')))
        cmds.button(height=25, label='Export',
                    command=lambda _x, a=app: local_export(a),
                    annotation='Export selection to {0}'.format(local_file('maya', app)))
        cmds.setParent(form)
        frames.append(frame)

    # Spread the app frames evenly across the form, whatever their count.
    step = 100.0 / len(frames)
    attach_form = []
    attach_position = []
    for index, frame in enumerate(frames):
        attach_form.append((frame, 'top', 5))
        if index == 0:
            attach_form.append((frame, 'left', 5))
        else:
            attach_position.append((frame, 'left', 2, int(round(index * step))))
        if index == len(frames) - 1:
            attach_form.append((frame, 'right', 5))
        else:
            attach_position.append((frame, 'right', 2, int(round((index + 1) * step))))

    cmds.formLayout(form, edit=True, attachForm=attach_form, attachPosition=attach_position)
    cmds.setParent(parent)


def build_server_section(parent):
    cmds.frameLayout(parent=parent, collapsable=True, label='Server', marginWidth=5, marginHeight=5,
                     annotation='Hand off through the studio share')
    column = cmds.columnLayout(adjustableColumn=True, rowSpacing=4)

    # --- One user picker, shared by both import and export ---
    cmds.text(label='User', align='left')
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

    # --- Direction rows: app on the left, action button filling the rest ---
    for label, menu_name, optvar, callback, button_label in (
            ('From', APP_IMPORT_MENU, OPTVAR_APP_IMPORT, server_import, 'Import'),
            ('To', APP_EXPORT_MENU, OPTVAR_APP_EXPORT, server_export, 'Export')):
        cmds.rowLayout(numberOfColumns=3, adjustableColumn=3,
                       columnWidth3=(38, 96, 96),
                       columnAlign=(1, 'left'),
                       columnAttach=[(1, 'both', 0), (2, 'both', 2), (3, 'both', 2)])
        cmds.text(label=label, align='left')
        cmds.optionMenu(menu_name,
                        changeCommand=lambda value, key=optvar: cmds.optionVar(stringValue=(key, value)))
        for app in FBX_SETTINGS['supported_apps']:
            cmds.menuItem(label=app)
        cmds.setParent('..', menu=True)
        cmds.button(height=25, label=button_label, command=callback)
        cmds.setParent(column)

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

    window = cmds.window(WINDOW, title='GS File Transfer  v{0}'.format(VERSION), widthHeight=(320, 460),
                         minimizeButton=False, maximizeButton=False, sizeable=False)
    main = cmds.columnLayout(adjustableColumn=True, rowSpacing=4)

    build_import_settings(main)
    build_local_section(main)
    build_server_section(main)
    build_footer(main)

    # Populate the user dropdown, then restore last session's picks.
    refresh_user_menu()
    restore_menu(USER_MENU, OPTVAR_USER, ALL_USERS)
    restore_menu(APP_IMPORT_MENU, OPTVAR_APP_IMPORT, FBX_SETTINGS['supported_apps'])
    restore_menu(APP_EXPORT_MENU, OPTVAR_APP_EXPORT, FBX_SETTINGS['supported_apps'])

    if not ALL_USERS:
        set_status('User list unavailable - check the share', 'warn')

    cmds.showWindow(window)


if __name__ == '__main__':
    GS_File_Transfer_UI()
