import maya.cmds as cmds
import maya.mel as mel
import os
import socket
import getpass
import sys
import csv

# Python version detection
PY3 = sys.version_info[0] >= 3

# Maya version detection
def get_maya_version():
    """Get Maya version as integer (e.g., 2018, 2020, 2022)"""
    try:
        maya_version = int(cmds.about(version=True))
        return maya_version
    except:
        # Fallback: try to parse from version string
        try:
            version_string = cmds.about(version=True)
            # Extract year from version string like "2018" or "Maya 2020"
            import re
            match = re.search(r'(\d{4})', version_string)
            if match:
                return int(match.group(1))
        except:
            pass
        
        return 2018

MAYA_VERSION = get_maya_version()

def check_fbx_export_file_version_support():
    """Check if FBXExportFileVersion command is supported"""
    try:
        # Try both command formats
        mel.eval('FBXExportFileVersion -q;')
        return True
    except:
        try:
            # Try older format without flags
            mel.eval('FBXExportFileVersion;')
            return True
        except:
            return False

# ============================================================================
# GLOBAL FBX SETTINGS CONFIGURATION
# ============================================================================
# All FBX import/export settings are centralized here for easy maintenance

# Version-specific FBX settings
def get_fbx_settings_for_version(maya_version):
    """Get FBX settings appropriate for the current Maya version"""
    base_settings = {
        # Scale Settings
        'import_scale_factor': 1.0,
        'export_scale_factor': 1.0,
        
        # Import Settings (when supported by Maya version)
        'import_smoothing_groups_default': True,
        'import_unlock_normals_default': False,
        'import_duplicate_mesh_default': False,
        
        # Export Settings - Add more as needed
        'export_embedded_media': False,
        'export_ascii': False,
        'export_binary': True,  # True for binary, False for ASCII
        
        # File naming convention
        'file_extension': '.fbx',
        
        # Server configuration
        'server_path': '\\\\192.168.1.210\\Temp\\File_Transfer\\',
        'library_path': '\\\\192.168.1.210\\Pipeline\\Library\\Data\\',
        
        # CSV configuration
        'csv_filename': 'Data_Computer_Auto.csv',  # Should be CSV format (.csv) for direct reading
        'csv_user_column': 'User',  # Default column name, can be changed
        
        # Local temp folder structure
        'local_temp_subfolder': 'fileTransferFbx\\',
        
        # Application mappings
        'supported_apps': ['Blender', 'Maya', 'Max'],
    }
    
    # Check actual command support rather than just version
    export_version_supported = check_fbx_export_file_version_support()
    
    # Version-specific settings
    if maya_version >= 2020 and export_version_supported:
        # Maya 2020+ supports newer FBX export file version commands
        base_settings.update({
            'export_file_version': 'FBX202000',  # FBX 2020 binary format
            'supports_export_file_version': True,
            # Other versions for 2020+: 'FBX201800', 'FBX201600', 'FBX201400'
        })
    elif maya_version >= 2018:
        # Maya 2018-2019: Try to use appropriate FBX version
        base_settings.update({
            'export_file_version': 'FBX201800',  # FBX 2018 format for older Maya
            'supports_export_file_version': export_version_supported,
        })
    else:
        # Maya 2017 and older: Limited FBX options
        base_settings.update({
            'export_file_version': 'FBX201400',  # Older FBX format
            'supports_export_file_version': export_version_supported,
        })
    
    return base_settings

FBX_SETTINGS = get_fbx_settings_for_version(MAYA_VERSION)

# ============================================================================
# CSV USER MANAGEMENT
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

def load_users_from_csv():
    """Load users from CSV file on the server"""
    csv_path = os.path.join(FBX_SETTINGS['library_path'], FBX_SETTINGS['csv_filename'])
    users_list = []
    
    try:
        if os.path.exists(csv_path):
            # Read as CSV file
            with open(csv_path, 'r') as csvfile:
                # Try to detect the delimiter
                sample = csvfile.read(1024)
                csvfile.seek(0)
                
                # Use csv.Sniffer to detect delimiter
                try:
                    dialect = csv.Sniffer().sniff(sample, delimiters=',;\t|')
                    reader = csv.DictReader(csvfile, dialect=dialect)
                except:
                    # Fallback to comma delimiter
                    reader = csv.DictReader(csvfile, delimiter=',')
                
                # Find the correct column name (case-insensitive)
                fieldnames = reader.fieldnames
                user_column = None
                
                if fieldnames:
                    # Look for exact match first
                    if FBX_SETTINGS['csv_user_column'] in fieldnames:
                        user_column = FBX_SETTINGS['csv_user_column']
                    else:
                        # Look for case-insensitive match
                        for field in fieldnames:
                            if field.lower() == FBX_SETTINGS['csv_user_column'].lower():
                                user_column = field
                                break
                        
                        # If still not found, try common variations
                        if not user_column:
                            common_user_columns = ['user', 'username', 'name', 'users', 'user_name']
                            for field in fieldnames:
                                if field.lower() in common_user_columns:
                                    user_column = field
                                    break
                
                if user_column:
                    for row in reader:
                        user = normalize_username(row.get(user_column, ''))
                        if user and user not in users_list:  # Avoid duplicates and empty entries
                            users_list.append(user)
                            
    except Exception as e:
        pass
    
    # If no users loaded, provide fallback
    if not users_list:
        users_list = ['user01', 'user02', 'user03']  # Fallback users
    
    return users_list

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def safe_mel_path(path):
    """
    Make a path safe for MEL commands in both Python 2 and 3.
    MEL requires paths to use forward slashes and proper quoting.
    """
    normalized = path.replace('\\', '/')
    return normalized

def check_fbx_command_support(command):
    """
    Generic function to check if an FBX MEL command is supported.
    Returns True if supported, False otherwise.
    """
    try:
        mel.eval(command + ' -q;')
        return True
    except:
        return False

def get_system_info():
    """Get current user and system information"""
    username = getpass.getuser()
    computer_name = socket.gethostname()
    return username, computer_name

def construct_local_path():
    """Construct the local temporary export path based on settings"""
    import tempfile
    temp_dir = tempfile.gettempdir()
    return os.path.join(temp_dir, FBX_SETTINGS['local_temp_subfolder'])

# ============================================================================
# FBX SETTINGS MANAGEMENT
# ============================================================================

class FBXSettingsManager:
    """Centralized FBX settings management"""
    
    def __init__(self):
        # Check what FBX features are supported in this Maya version
        self.smoothing_groups_supported = check_fbx_command_support('FBXImportSmoothingGroups')
        self.unlock_normals_supported = check_fbx_command_support('FBXImportUnlockNormals')
        
    def apply_import_settings(self, smoothing_enabled=None, unlock_normals_enabled=None):
        """
        Apply FBX import settings with compatibility for different Maya versions
        If parameters are None, use defaults from FBX_SETTINGS
        """
        if smoothing_enabled is None:
            smoothing_enabled = FBX_SETTINGS['import_smoothing_groups_default']
        if unlock_normals_enabled is None:
            unlock_normals_enabled = FBX_SETTINGS['import_unlock_normals_default']
        
        # Apply scale factor (should be available in all versions)
        try:
            scale_cmd = 'FBXImportScaleFactor {0};'.format(FBX_SETTINGS["import_scale_factor"])
            mel.eval(scale_cmd)
        except:
            pass
        
        # Apply smoothing groups if supported
        if self.smoothing_groups_supported:
            try:
                smoothing_cmd = 'FBXImportSmoothingGroups -v {0};'.format(str(smoothing_enabled).lower())
                mel.eval(smoothing_cmd)
            except:
                pass
        
        # Apply unlock normals if supported
        if self.unlock_normals_supported:
            try:
                normals_cmd = 'FBXImportUnlockNormals -v {0};'.format(str(unlock_normals_enabled).lower())
                mel.eval(normals_cmd)
            except:
                pass
    
    def apply_export_settings(self):
        """Apply FBX export settings based on global configuration and Maya version"""
        # Set scale factor (available in all Maya versions)
        try:
            scale_cmd = 'FBXExportScaleFactor {0};'.format(FBX_SETTINGS["export_scale_factor"])
            mel.eval(scale_cmd)
        except:
            pass
        
        # Set FBX file version (version-dependent)
        if FBX_SETTINGS.get('supports_export_file_version', False):
            try:
                # Try the newer command format first (Maya 2020+)
                version_cmd = 'FBXExportFileVersion -v "{0}";'.format(FBX_SETTINGS["export_file_version"])
                mel.eval(version_cmd)
            except:
                try:
                    # Try older command format without -v flag (Maya 2018-2019)
                    version_cmd = 'FBXExportFileVersion "{0}";'.format(FBX_SETTINGS["export_file_version"])
                    mel.eval(version_cmd)
                except:
                    pass
        
        # Set binary/ASCII format (available in most Maya versions)
        try:
            ascii_setting = not FBX_SETTINGS['export_binary']  # Invert because MEL uses ASCII flag
            ascii_cmd = 'FBXExportInAscii -v {0};'.format(str(ascii_setting).lower())
            mel.eval(ascii_cmd)
        except:
            pass
    
    def get_ui_smoothing_setting(self):
        """Get smoothing groups setting from UI if available"""
        if self.smoothing_groups_supported and cmds.checkBox("smoothing_groups_toggle", exists=True):
            return cmds.checkBox("smoothing_groups_toggle", query=True, value=True)
        return FBX_SETTINGS['import_smoothing_groups_default']
    
    def get_ui_unlock_normals_setting(self):
        """Get unlock normals setting from UI if available"""
        if self.unlock_normals_supported and cmds.checkBox("unlock_normals_toggle", exists=True):
            return cmds.checkBox("unlock_normals_toggle", query=True, value=True)
        return FBX_SETTINGS['import_unlock_normals_default']
    
    def get_ui_duplicate_mesh_setting(self):
        """Get duplicate mesh setting from UI if available"""
        if cmds.checkBox("duplicate_mesh_toggle", exists=True):
            return cmds.checkBox("duplicate_mesh_toggle", query=True, value=True)
        return FBX_SETTINGS['import_duplicate_mesh_default']

# ============================================================================
# FILE OPERATIONS
# ============================================================================

class FileOperations:
    """Handle all file import/export operations"""
    
    def __init__(self):
        self.fbx_manager = FBXSettingsManager()
        self.local_export_path = construct_local_path()
        self.username, _ = get_system_info()
        
        # Ensure local directory exists
        self._ensure_directory_exists(self.local_export_path)
    
    def _ensure_directory_exists(self, path):
        """Create directory if it doesn't exist"""
        if not os.path.exists(path):
            try:
                os.makedirs(path)
            except:
                cmds.warning("Failed to create directory: {0}".format(path))
    
    def _get_unique_suffix(self, base_name):
        """
        Find the next available numeric suffix (_001, _002, etc.) for a given base name.
        """
        suffix_num = 1
        while suffix_num < 1000:  # Safety limit
            new_name = "{0}_{1:03d}".format(base_name, suffix_num)
            if not cmds.objExists(new_name):
                return new_name
            suffix_num += 1
        
        # Fallback
        import time
        return "{0}_{1}".format(base_name, int(time.time()))

    def _safe_import(self, file_path):
        """Safely import FBX file with current settings"""
        if os.path.exists(file_path):
            # Apply import settings
            smoothing_enabled = self.fbx_manager.get_ui_smoothing_setting()
            unlock_normals_enabled = self.fbx_manager.get_ui_unlock_normals_setting()
            duplicate_mesh_enabled = self.fbx_manager.get_ui_duplicate_mesh_setting()
            self.fbx_manager.apply_import_settings(smoothing_enabled, unlock_normals_enabled)
            
            safe_path = safe_mel_path(file_path)
            
            if duplicate_mesh_enabled:
                # Strategy: Backup existing meshes, let Maya update, then swap names
                # This preserves originals while adding imported meshes with suffixes
                
                backup_mapping = {}  # {original_name: backup_name}
                
                # Get all top-level mesh transforms (meshes that have shape nodes)
                all_meshes = cmds.ls(type='mesh', long=True) or []
                mesh_transforms = list(set([cmds.listRelatives(m, parent=True, fullPath=True)[0] for m in all_meshes]))
                
                # Only backup top-level transforms (not nested in hierarchies we might duplicate)
                top_level_transforms = []
                for t in mesh_transforms:
                    # Get short name
                    short_name = t.split('|')[-1]
                    # Skip if it's already a backup
                    if '_TEMP_BACKUP' in short_name:
                        continue
                    top_level_transforms.append(t)
                
                # Create backups of existing meshes
                for transform in top_level_transforms:
                    short_name = transform.split('|')[-1]
                    backup_name = "{0}_TEMP_BACKUP".format(short_name)
                    
                    try:
                        # Duplicate the mesh and its children
                        duplicated = cmds.duplicate(transform, name=backup_name, returnRootsOnly=True)
                        if duplicated:
                            backup_mapping[short_name] = duplicated[0]
                    except Exception as e:
                        cmds.warning("Could not backup {0}: {1}".format(short_name, str(e)))
                
                # Now import - Maya will update the original meshes
                mel.eval('FBXImport -f "{0}";'.format(safe_path))
                
                # Swap names: originals get suffix, backups get original names
                for original_name, backup_node in backup_mapping.items():
                    if cmds.objExists(original_name) and cmds.objExists(backup_node):
                        try:
                            # Rename the updated original to have a suffix
                            suffixed_name = self._get_unique_suffix(original_name)
                            cmds.rename(original_name, suffixed_name)
                            
                            # Rename backup to original name
                            cmds.rename(backup_node, original_name)
                        except Exception as e:
                            cmds.warning("Could not swap names for {0}: {1}".format(original_name, str(e)))
                    elif cmds.objExists(backup_node):
                        # Original was deleted or doesn't exist, just remove backup suffix
                        try:
                            cmds.rename(backup_node, original_name)
                        except:
                            pass
            else:
                # Standard import (may merge with existing meshes)
                mel.eval('FBXImport -f "{0}";'.format(safe_path))
        else:
            cmds.confirmDialog(
                title="Import Error", 
                message="File does not exist: {0}".format(file_path), 
                button="OK"
            )

    def _safe_export(self, file_path):
        """Safely export selected objects to FBX with current settings"""
        if not cmds.ls(sl=True):
            cmds.confirmDialog(
                title="Warning", 
                message="Please select objects to export!", 
                button="OK"
            )
            return False
        
        # Ensure export directory exists
        self._ensure_directory_exists(os.path.dirname(file_path))
        
        # Apply export settings
        self.fbx_manager.apply_export_settings()
        
        # Export file
        safe_path = safe_mel_path(file_path)
        mel.eval('FBXExport -f "{0}" -s;'.format(safe_path))
        
        return True
    
    # Local file operations
    def import_from_blender(self):
        """Import from Blender via local temp file"""
        import_file = os.path.join(self.local_export_path, "blender_to_maya{0}".format(FBX_SETTINGS['file_extension']))
        self._safe_import(import_file)
    
    def export_to_blender(self):
        """Export to Blender via local temp file"""
        export_file = os.path.join(self.local_export_path, "maya_to_blender{0}".format(FBX_SETTINGS['file_extension']))
        self._safe_export(export_file)
    
    def import_from_max(self):
        """Import from Max via local temp file"""
        import_file = os.path.join(self.local_export_path, "max_to_maya{0}".format(FBX_SETTINGS['file_extension']))
        self._safe_import(import_file)
    
    def export_to_max(self):
        """Export to Max via local temp file"""
        export_file = os.path.join(self.local_export_path, "maya_to_max{0}".format(FBX_SETTINGS['file_extension']))
        self._safe_export(export_file)

    def import_from_maya(self):
        """Import from another local Maya session via shared local temp file"""
        import_file = os.path.join(self.local_export_path, "maya_to_maya{0}".format(FBX_SETTINGS['file_extension']))
        self._safe_import(import_file)

    def export_to_maya(self):
        """Export to another local Maya session via shared local temp file"""
        export_file = os.path.join(self.local_export_path, "maya_to_maya{0}".format(FBX_SETTINGS['file_extension']))
        self._safe_export(export_file)

    # Server file operations
    def import_from_server(self):
        """Import from server based on UI selections"""
        source_app = cmds.optionMenu("APP_IMPORT", query=True, value=True).lower()
        source_user = cmds.optionMenu("USER_IMPORT", query=True, value=True)
        target_app = "maya"
        
        # Filename format: [source_user]_[source_app]_to_[target_app]_[current_user].fbx
        filename = "{0}_{1}_to_{2}_{3}{4}".format(source_user, source_app, target_app, self.username, FBX_SETTINGS['file_extension'])
        file_path = os.path.join(FBX_SETTINGS['server_path'], source_user, filename)
        
        self._safe_import(file_path)
    
    def export_to_server(self):
        """Export to server based on UI selections"""
        source_app = "maya"
        target_app = cmds.optionMenu("APP_EXPORT", query=True, value=True).lower()
        target_user = cmds.optionMenu("USER_EXPORT", query=True, value=True)
        
        # Filename format: [current_user]_[source_app]_to_[target_app]_[target_user].fbx
        filename = "{0}_{1}_to_{2}_{3}{4}".format(self.username, source_app, target_app, target_user, FBX_SETTINGS['file_extension'])
        file_path = os.path.join(FBX_SETTINGS['server_path'], self.username, filename)
        
        self._safe_export(file_path)

# ============================================================================
# UI CREATION
# ============================================================================

def GS_File_Transfer_UI():
    """Create the File Transfer UI"""
    
    # Initialize file operations
    file_ops = FileOperations()
    fbx_manager = file_ops.fbx_manager
    username, _ = get_system_info()
    
    # Load users from CSV
    users_list = load_users_from_csv()
    
    # Callback functions for UI buttons
    def Import_From_Blender(*args):
        file_ops.import_from_blender()
    
    def Export_To_Blender(*args):
        file_ops.export_to_blender()
    
    def Import_From_Max(*args):
        file_ops.import_from_max()
    
    def Export_To_Max(*args):
        file_ops.export_to_max()

    def Import_From_Maya(*args):
        file_ops.import_from_maya()

    def Export_To_Maya(*args):
        file_ops.export_to_maya()

    def Import_From_Server(*args):
        file_ops.import_from_server()
    
    def Export_To_Server(*args):
        file_ops.export_to_server()
    
    # Check if window exists and delete it
    if cmds.window("GS_File_Transfer_Window", exists=True):
        cmds.deleteUI("GS_File_Transfer_Window")

    # Create window with responsive layout
    window = cmds.window("GS_File_Transfer_Window", title='GS File Transfer', widthHeight=(300, 420), minimizeButton=False, maximizeButton=False, sizeable=False)
    
    # Main column layout
    main_layout = cmds.columnLayout(adjustableColumn=True, width=140)
    
    # Import Settings Section (only if at least one setting is supported)
    if fbx_manager.smoothing_groups_supported or fbx_manager.unlock_normals_supported:
        cmds.frameLayout('settingsFrame', parent=main_layout, collapsable=False, label='Import Settings', marginWidth=5, marginHeight=5)
        settings_column = cmds.columnLayout(adjustableColumn=True)
        cmds.separator(height=5, style='none')
        
        # Add smoothing groups toggle if supported
        if fbx_manager.smoothing_groups_supported:
            cmds.checkBox("smoothing_groups_toggle", label='Import Smoothing Groups', 
                          value=FBX_SETTINGS['import_smoothing_groups_default'], 
                          annotation='Enable/disable smoothing groups when importing FBX files')
        
        # Add unlock normals toggle if supported
        if fbx_manager.unlock_normals_supported:
            cmds.checkBox("unlock_normals_toggle", label='Unlock Normals', 
                          value=FBX_SETTINGS['import_unlock_normals_default'], 
                          annotation='Enable/disable unlock normals when importing FBX files')

        # Add duplicate mesh toggle (always available)
        cmds.checkBox("duplicate_mesh_toggle", label='Duplicate Mesh', 
                      value=FBX_SETTINGS['import_duplicate_mesh_default'], 
                      annotation='When enabled, preserves existing meshes and imports FBX meshes with suffix (_001, _002, etc.)')
        
        cmds.separator(height=5, style='none')
        
        cmds.setParent(main_layout)
        cmds.separator(height=5)
    
    # Local section
    cmds.frameLayout('localFrame', parent=main_layout, collapsable=True, label='Local', marginWidth=5, marginHeight=5)
    local_form = cmds.formLayout(parent='localFrame', numberOfDivisions=100)
    
    # Blender group
    blender_frame = cmds.frameLayout(parent=local_form, collapsable=False, label='Blender', width=80)
    cmds.columnLayout(adjustableColumn=True)
    cmds.separator(height=10, style='none')
    cmds.button(height=25, label='Import', c=Import_From_Blender)
    cmds.separator(height=5, style='none')
    cmds.button(height=25, label='Export', c=Export_To_Blender)
    
    # Max group
    max_frame = cmds.frameLayout(parent=local_form, collapsable=False, label='Max', width=80)
    cmds.columnLayout(adjustableColumn=True)
    cmds.separator(height=10, style='none')
    cmds.button(height=25, label='Import', c=Import_From_Max)
    cmds.separator(height=5, style='none')
    cmds.button(height=25, label='Export', c=Export_To_Max)

    # Maya group (Maya-to-Maya transfer between local sessions)
    maya_frame = cmds.frameLayout(parent=local_form, collapsable=False, label='Maya', width=80)
    cmds.columnLayout(adjustableColumn=True)
    cmds.separator(height=10, style='none')
    cmds.button(height=25, label='Import', c=Import_From_Maya,
                annotation='Import FBX exported from another local Maya session')
    cmds.separator(height=5, style='none')
    cmds.button(height=25, label='Export', c=Export_To_Maya,
                annotation='Export selection for another local Maya session to import')

    # Layout the three frames side by side with responsive positioning
    cmds.formLayout(
        local_form, edit=True,
        attachForm=[(blender_frame, 'left', 5), (blender_frame, 'top', 5),
                   (max_frame, 'top', 5),
                   (maya_frame, 'right', 5), (maya_frame, 'top', 5)],
        attachPosition=[(blender_frame, 'right', 2, 33),
                        (max_frame, 'left', 2, 33), (max_frame, 'right', 2, 66),
                        (maya_frame, 'left', 2, 66)]
    )
    
    cmds.setParent(main_layout)
    cmds.separator(height=5)
    
    # Server section
    cmds.frameLayout('serverFrame', parent=main_layout, collapsable=True, label='Server', marginWidth=5, marginHeight=5)
    server_column = cmds.columnLayout(adjustableColumn=True)
    
    cmds.separator(height=5, style='none')
    
    # Import section - using formLayout for responsive behavior
    import_form = cmds.formLayout(numberOfDivisions=100)
    
    # Create application and user dropdowns
    app_import = cmds.optionMenu("APP_IMPORT")
    for app in FBX_SETTINGS['supported_apps']:
        cmds.menuItem(label=app)
    
    user_import = cmds.optionMenu("USER_IMPORT")
    for user in users_list:
        cmds.menuItem(label=user)
    
    # Position the dropdowns side by side
    cmds.formLayout(
        import_form, edit=True,
        attachForm=[
            (app_import, 'left', 0),
            (app_import, 'top', 0),
            (user_import, 'right', 0),
            (user_import, 'top', 0)
        ],
        attachPosition=[
            (app_import, 'right', 5, 50),
            (user_import, 'left', 5, 50)
        ]
    )
    
    # Import button - full width
    cmds.setParent(server_column)
    cmds.separator(height=5, style='none')
    cmds.button(height=25, label='Import', c=Import_From_Server)
    
    # Separator between import and export sections
    cmds.separator(height=10)
    
    # Export section - using formLayout for responsive behavior
    export_form = cmds.formLayout(numberOfDivisions=100)
    
    # Create application and user dropdowns
    app_export = cmds.optionMenu("APP_EXPORT")
    for app in FBX_SETTINGS['supported_apps']:
        cmds.menuItem(label=app)
    
    user_export = cmds.optionMenu("USER_EXPORT")
    for user in users_list:
        cmds.menuItem(label=user)
    
    # Position the dropdowns side by side
    cmds.formLayout(
        export_form, edit=True,
        attachForm=[
            (app_export, 'left', 0),
            (app_export, 'top', 0),
            (user_export, 'right', 0),
            (user_export, 'top', 0)
        ],
        attachPosition=[
            (app_export, 'right', 5, 50),
            (user_export, 'left', 5, 50)
        ]
    )
    
    # Export button - full width
    cmds.setParent(server_column)
    cmds.separator(height=5, style='none')
    cmds.button(height=25, label='Export', c=Export_To_Server)
    
    # User information at the bottom
    cmds.setParent(main_layout)
    cmds.separator(height=10)
    
    # Create a form layout for better alignment
    user_form = cmds.formLayout(parent=main_layout, width=140)
    user_label = cmds.text(label="Current User: ", align="left", width=105)
    user_name = cmds.text(label=username, align="left")
    
    # Position the text fields to be fully aligned with main layout
    cmds.formLayout(
        user_form, edit=True,
        attachForm=[
            (user_label, 'left', 10),
            (user_label, 'top', 0),
            (user_name, 'top', 0),
            (user_name, 'right', 5)
        ],
        attachControl=[
            (user_name, 'left', 0, user_label)
        ]
    )
    
    # Show window and adjust size to content
    cmds.showWindow(window)

# Run the UI
GS_File_Transfer_UI()