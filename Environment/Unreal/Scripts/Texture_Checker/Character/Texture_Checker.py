from __future__ import unicode_literals, print_function
import sys
import os
import re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# PARENT_DIR = os.path.dirname(CURRENT_DIR)

def find_root_dir():
    # Start with the current file's directory
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

    # Keep going up until we find a directory named "scripts"
    while True:
        # Check if we've reached the root of the filesystem
        PARENT_DIR = os.path.dirname(CURRENT_DIR)
        if PARENT_DIR == CURRENT_DIR:  # We've reached the filesystem root
            return None  # or raise an exception
        
        # Check if the current directory is named "scripts"
        if os.path.basename(CURRENT_DIR) == "Scripts":
            # Return the parent directory of "scripts"
            return CURRENT_DIR
        
        # Move up one level
        CURRENT_DIR = PARENT_DIR

# Usage
ROOT_DIR = find_root_dir()

python_lib = "//192.168.1.10/Pipeline/GSTools/Library/Python/Python39/Lib/site-packages"
if os.path.exists(python_lib):
    sys.path.append(python_lib)
else:
    print(f"Warning: {python_lib} does not exist")

from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import Qt

# Import texture rules using importlib
import importlib.util
expected_path = os.path.join(SCRIPT_DIR, "Texture_Checker_Rules.py")
spec = importlib.util.spec_from_file_location("Texture_Checker_Rules", expected_path)
texture_rules_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(texture_rules_module)

TEXTURE_RULES = texture_rules_module.TEXTURE_RULES
SUFFIX_PRIORITY = texture_rules_module.SUFFIX_PRIORITY
SUFFIX_PATTERNS = texture_rules_module.SUFFIX_PATTERNS
get_final_rule_for_texture = texture_rules_module.get_final_rule_for_texture

class TextureCheckerGUI(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.load_style()
        # Use the imported rules
        self.texture_rules = TEXTURE_RULES
        self.suffix_priority = SUFFIX_PRIORITY
        self.suffix_patterns = SUFFIX_PATTERNS
        
        # Initialize dictionaries for texture group mapping but don't populate yet
        self.enum_to_display = {}
        self.display_to_enum = {}
        
    def setup_ui(self):
        """Initialize the main UI components"""
        self.setWindowTitle("Texture Checker")
        self.resize(1000, 800)
        
        # Set font
        self.setFont(QFont("Meiryo UI", 10))
        
        # Create central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)
        
        # Create texture checker tab
        self.setup_texture_checker_tab()
        
    def setup_texture_checker_tab(self):
        """Setup the texture checker tab and its components"""
        self.texture_tab = QWidget()
        self.texture_layout = QVBoxLayout(self.texture_tab)
        
        # Top section
        top_layout = QHBoxLayout()
        self.status_label = QLabel("")
        self.check_button = QPushButton("Check Texture")
        self.check_button.clicked.connect(self.check_texture)
        
        top_layout.addWidget(self.status_label)
        top_layout.addWidget(self.check_button)
        top_layout.addSpacerItem(QSpacerItem(1000, 1000, QSizePolicy.Preferred, QSizePolicy.Preferred))
        
        # Tree widget
        self.texture_tree = QTreeWidget()
        self.setup_tree_widget()
        
        # Bottom section
        bottom_layout = QHBoxLayout()
        self.fix_button = QPushButton("Fix Texture Property")
        self.fix_button.clicked.connect(self.fix_texture_property)
        
        bottom_layout.addSpacerItem(QSpacerItem(1000, 1000, QSizePolicy.Preferred, QSizePolicy.Preferred))
        bottom_layout.addWidget(self.fix_button)
        
        # Add all components to main layout
        self.texture_layout.addLayout(top_layout)
        self.texture_layout.addWidget(self.texture_tree)
        self.texture_layout.addLayout(bottom_layout)
        
        # Add tab to main tab widget
        self.tab_widget.addTab(self.texture_tab, "Texture Checker")
        
    def setup_tree_widget(self):
        """Configure the tree widget settings"""
        # Updated to include target_size and texture_group columns
        self.texture_tree.setColumnCount(8)  # 0/1 checkbox + 7 columns
        self.texture_tree.setHeaderLabels(["0/1", "name", "current_size", "target_size", "compression_settings", "srgb", "brightness_curve", "texture_group"])
        self.texture_tree.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.texture_tree.setIndentation(5)
        self.texture_tree.setAlternatingRowColors(True)
        
        # Set all columns to resize to contents (making them responsive)
        header = self.texture_tree.header()
        for i in range(self.texture_tree.columnCount()):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        
        # Disable user ability to move columns
        header.setSectionsMovable(False)
        
        # Connect to handle window resize events
        self.texture_tree.itemDoubleClicked.connect(self.open_asset)

    def adjust_columns(self):
        """Ensure columns maintain their responsive sizing with additional margin"""
        if self.texture_tree.topLevelItemCount() > 0:
            header = self.texture_tree.header()
            
            # First apply ResizeToContents to get the content width
            for i in range(self.texture_tree.columnCount()):
                header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
            
            # Now add margin by setting an explicit width (content width + margin)
            for i in range(self.texture_tree.columnCount()):
                # Get the current width that fits the content
                content_width = header.sectionSize(i)
                # Set a new width with additional margin
                margin = 10  # 10 pixel margin
                header.setSectionResizeMode(i, QHeaderView.Interactive)  # Temporarily switch to allow explicit sizing
                header.resizeSection(i, content_width + margin)
                
            # Disable user resizing by fixing the section sizes
            header.setSectionsClickable(True)
            header.setSectionResizeMode(QHeaderView.Fixed)

    def resizeEvent(self, event):
        """Handle window resize events"""
        super().resizeEvent(event)
        
    def load_style(self):
        """Load QSS style file"""
        style = ''
        for style_path in [os.path.join(dir, 'style.qss') for dir in [ROOT_DIR]]:
            if os.path.exists(style_path):
                try:
                    with open(style_path, 'r') as f:
                        style = f.read()
                        break
                except Exception as e:
                    print(f"Warning: Could not load style file: {e}")
                    
        self.setStyleSheet(style)

    def get_matching_suffix(self, texture_name):
        """Find the matching suffix for a texture name using regex patterns"""
        texture_name_lower = texture_name.lower()
        
        # Check each suffix in priority order using the regex patterns
        for suffix in self.suffix_priority:
            pattern = self.suffix_patterns.get(suffix)
            if pattern and re.search(pattern, texture_name_lower):
                return suffix
                
        # No matching suffix found
        return None
        
    def get_rule_from_name(self, texture_name):
        """Determine texture properties based on file name suffix including special cases"""
        matching_suffix = self.get_matching_suffix(texture_name)
        
        # If we found a matching suffix, return the corresponding rule
        if matching_suffix and matching_suffix in self.texture_rules:
            # Get the base rule for this suffix
            base_rule = self.texture_rules[matching_suffix]
            # Apply any special case logic based on the texture name
            return get_final_rule_for_texture(base_rule, matching_suffix, texture_name), matching_suffix
        
        # No matching rule found
        return None, matching_suffix

    def get_column_from_header(self, widget, match_text):
        """Get column index from header text"""
        header_item = widget.headerItem()
        for i in range(header_item.columnCount()):
            if header_item.text(i) == match_text:
                return i
        return None

    def get_texture_group_mapping(self, needed_groups=None):
        """Create a mapping between texture group display names and enum values
        Optimized to only map groups that are needed"""
        import unreal
        
        # Get all TextureGroup enum values
        texture_group_enum = unreal.TextureGroup
        
        # If mappings are already populated and we don't need specific groups, return the existing mappings
        if self.enum_to_display and self.display_to_enum and not needed_groups:
            return
            
        # Create bidirectional mappings using string keys
        if not self.enum_to_display:
            self.enum_to_display = {}
        if not self.display_to_enum:
            self.display_to_enum = {}
        
        # If we have specific groups to map, handle those
        if needed_groups:
            for group_name in needed_groups:
                # Skip if we already have this mapping
                if group_name in self.display_to_enum:
                    continue
                    
                # Try to find the enum value for this group name
                for attr in dir(texture_group_enum):
                    if not attr.startswith('_') and attr.startswith('TEXTUREGROUP_'):
                        try:
                            enum_value = getattr(texture_group_enum, attr)
                            if isinstance(enum_value, unreal.TextureGroup):
                                display_name = enum_value.get_display_name()
                                
                                # If this matches what we need, store it
                                if display_name == group_name:
                                    enum_str = str(enum_value)
                                    self.enum_to_display[enum_str] = display_name
                                    self.display_to_enum[display_name] = enum_value
                                    break
                        except:
                            # Skip errors silently
                            pass
            return
        
        # Otherwise, populate all mappings (but quietly)
        # This should only happen the first time we need a complete mapping
        for attr in dir(texture_group_enum):
            if not attr.startswith('_') and attr.startswith('TEXTUREGROUP_'):
                try:
                    enum_value = getattr(texture_group_enum, attr)
                    if isinstance(enum_value, unreal.TextureGroup):
                        display_name = enum_value.get_display_name()
                        
                        # Store mappings using string identifiers instead of enum objects
                        enum_str = str(enum_value)
                        self.enum_to_display[enum_str] = display_name
                        self.display_to_enum[display_name] = enum_value
                except:
                    # Skip errors silently
                    pass

    def create_custom_widget_item(self, color, value_dict, color_dict, meta_data):
        """Create a custom tree widget item"""
        item = QTreeWidgetItem()
        
        # Set text values
        for key, value in value_dict.items():
            column = self.get_column_from_header(self.texture_tree, key)
            if column is not None:
                # Format floating point values to be more readable
                if isinstance(value, float):
                    # Format float to 1 decimal place if it's an integer value (like 1.0)
                    # or 2 decimal places otherwise
                    if value == int(value):
                        formatted_value = f"{value:.1f}"
                    else:
                        formatted_value = f"{value:.2f}"
                    item.setText(column, formatted_value)
                else:
                    item.setText(column, str(value))
        
        # Set colors
        for key, color_value in color_dict.items():
            column = self.get_column_from_header(self.texture_tree, key)
            if column is not None:
                item.setForeground(column, QBrush(QColor(color_value)))
        
        # Set checkbox state
        item.setCheckState(0, Qt.Checked if value_dict.get("0/1") == "1" else Qt.Unchecked)
        item.setText(0, "")
        
        # Set metadata and color
        item.setText(20, str(meta_data))
        item.setForeground(1, QBrush(QColor(color)))
        
        return item

    def check_texture(self):
        """Check textures and update UI based on content browser selection"""
        try:
            import unreal
            
            # Get selected assets from the content browser
            editor_utility = unreal.EditorUtilityLibrary()
            selected_assets = editor_utility.get_selected_assets()
            
            # Filter for Texture2D objects
            texture_list = unreal.EditorFilterLibrary.by_class(selected_assets, unreal.Texture2D)
            
            if not texture_list:
                self.texture_tree.clear()
                self.status_label.setText("No textures selected in content browser")
                return
            
            self.status_label.setText(f"Checking {len(texture_list)} selected textures...")
            
            # Update tree widget
            self.texture_tree.clear()
            
            # Track textures by similar naming patterns
            textures_by_pattern = {}
            
            # Collect needed texture groups for lazy loading
            needed_texture_groups = set()
            
            # First pass: Check all textures and determine their rules
            for tex in texture_list:
                tex_name = tex.get_name()
                
                # Default color is white, but will be changed below if needed
                color = "white"
                
                # Get the matching suffix and rule
                rule, matching_suffix = self.get_rule_from_name(tex_name)
                
                # Initialize value dictionary
                value_dict = {
                    "name": tex_name,
                    "0/1": "0"
                }
                
                # Initialize metadata
                meta_data = {
                    "path": tex.get_path_name()
                }
                
                # Get current properties
                current_compression = str(tex.get_editor_property("compression_settings")).split(".",1)[1].split(":",1)[0]
                value_dict["compression_settings"] = current_compression
                
                current_srgb = tex.get_editor_property("srgb")
                value_dict["srgb"] = current_srgb
                
                # Get brightness curve value - using the correct property name "adjust_brightness_curve"
                try:
                    current_brightness_curve = tex.get_editor_property("adjust_brightness_curve")
                except:
                    # Property might not exist, default to 0
                    current_brightness_curve = 0.0
                
                value_dict["brightness_curve"] = current_brightness_curve
                
                # Get texture size
                try:
                    # Get dimensions from properties
                    tag_list = unreal.EditorAssetLibrary.get_tag_values(tex.get_path_name())
                    if "Dimensions" in tag_list:
                        value_dict["current_size"] = tag_list["Dimensions"]
                except:
                    value_dict["current_size"] = "Unknown"

                # Get texture group/LOD group
                try:
                    lod_group = tex.get_editor_property("lod_group")
                    # Store the enum value in metadata for setting later
                    meta_data["lod_group_enum"] = str(lod_group) # Convert enum to string
                    # Get the display name for UI
                    lod_group_display = lod_group.get_display_name()
                    value_dict["texture_group"] = lod_group_display
                except:
                    value_dict["texture_group"] = "None"
                
                # Color dictionary for highlighting
                color_dict = {}
                
                # If we have a rule, check if properties need fixing
                if rule is not None:
                    # Add rule values to metadata
                    meta_data["compression_settings"] = rule["compression_settings"]
                    meta_data["srgb"] = rule["srgb"]
                    meta_data["brightness_curve"] = rule["brightness_curve"]
                    
                    # Add new size property if present
                    if "size" in rule:
                        target_width, target_height = rule["size"]
                        target_size = f"{target_width}x{target_height}"
                        # Always display the target size
                        value_dict["target_size"] = target_size
                        
                        # Compare with current size if known
                        current_size = value_dict.get("current_size", "Unknown")
                        # Highlight mismatch but don't mark for fixing
                        if current_size != "Unknown" and current_size != target_size:
                            color_dict["current_size"] = "red"
                    else:
                        # If no size rule, indicate that there's no target size
                        value_dict["target_size"] = "Not specified"
                    
                    # Check if compression settings need to be updated
                    if current_compression != rule["compression_settings"]:
                        color_dict["compression_settings"] = "red"
                        value_dict["0/1"] = "1"
                    
                    # Check sRGB
                    if current_srgb != rule["srgb"]:
                        color_dict["srgb"] = "red"
                        value_dict["0/1"] = "1"
                        
                    # Check brightness curve with a small epsilon for floating point comparison
                    try:
                        # Use a small epsilon (0.001) for floating-point comparison to avoid precision issues
                        if abs(current_brightness_curve - rule["brightness_curve"]) > 0.001:
                            color_dict["brightness_curve"] = "red"
                            value_dict["0/1"] = "1"
                    except:
                        # Skip comparison if there's an issue
                        pass

                    # Handle texture group rules (if present)
                    if "texture_group" in rule:
                        # Add to needed groups for lazy loading
                        needed_texture_groups.add(rule["texture_group"])
                        
                        # Store target texture group
                        meta_data["texture_group"] = rule["texture_group"]
                        
                        # Check if they don't match against current
                        current_texture_group = value_dict["texture_group"]
                        if current_texture_group != rule["texture_group"]:
                            color_dict["texture_group"] = "red"
                            value_dict["0/1"] = "1"
                    else:
                        # No texture group rule
                        meta_data["texture_group"] = "Not specified"
                            
                else:
                    # No matching rule - don't mark for fixing
                    color = "red"
                
                # Group by pattern for similar naming convention
                prefix = re.match(r'([a-zA-Z]+)', tex_name.lower())
                prefix = prefix.group(1) if prefix else ""
                
                # Create pattern key for grouping
                if matching_suffix is None:
                    pattern_key = f"{prefix}_zero_match"
                else:
                    # Use the detected suffix for consistent grouping
                    pattern_key = f"{prefix}_{matching_suffix}"
                
                if pattern_key not in textures_by_pattern:
                    textures_by_pattern[pattern_key] = []
                
                textures_by_pattern[pattern_key].append((rule, color_dict, value_dict, meta_data, tex_name, matching_suffix))
            
            # Lazy-load only the texture groups we need
            if needed_texture_groups:
                self.get_texture_group_mapping(needed_texture_groups)
                
            # Second pass: Create items
            items_to_add = []
            
            for pattern_key, textures in textures_by_pattern.items():
                for rule, color_dict, value_dict, meta_data, tex_name, matching_suffix in textures:
                    # For zero match, color should be red
                    if rule is None:
                        item_color = "red"
                    else:
                        item_color = "white"
                    
                    item = self.create_custom_widget_item(item_color, value_dict, color_dict, meta_data)
                    items_to_add.append((0, item))  # All items have same priority
            
            # Add items to tree
            for _, item in items_to_add:
                self.texture_tree.addTopLevelItem(item)
            
            # Resize columns and ensure proper sizing
            self.adjust_columns()
            
            # Update status label with count of textures needing fixing
            needs_fixing = sum(1 for _, item in items_to_add if item.checkState(0) == Qt.Checked)
            no_rule = sum(1 for _, item in items_to_add if item.foreground(1).color().name() == "#ff0000")
            self.status_label.setText(f"Checked {len(texture_list)} textures. {needs_fixing} need fixing. {no_rule} have no matching rule.")
                
        except ImportError:
            self.status_label.setText("Unreal Engine module not available")
            print("Unreal Engine module not available")
            
    def open_asset(self, item):
        """Open selected asset in Unreal Editor"""
        import unreal
        text = eval(item.text(20))
        asset = [unreal.load_asset(text["path"])]
        
        # Get the asset editor subsystem and use it to open the assets
        editor_subsystem = unreal.get_editor_subsystem(unreal.AssetEditorSubsystem)
        editor_subsystem.open_editor_for_assets(asset)
            
    def fix_texture_property(self):
        """Fix texture properties for selected items"""
        import unreal
        
        # Get checked items
        iterator = QTreeWidgetItemIterator(self.texture_tree)
        fix_items = []
        while iterator.value():
            item = iterator.value()
            if item.checkState(0) == Qt.Checked:
                fix_items.append(eval(item.text(20)))
            iterator += 1
            
        if not fix_items:
            self.status_label.setText("No textures selected for fixing")
            return
            
        # Collect needed texture groups for lazy loading
        needed_texture_groups = set()
        for fix_item in fix_items:
            if "texture_group" in fix_item and fix_item["texture_group"] != "Not specified":
                needed_texture_groups.add(fix_item["texture_group"])
        
        # Lazy-load only the texture groups we need
        if needed_texture_groups:
            self.get_texture_group_mapping(needed_texture_groups)
            
        fixed_count = 0
        
        # Process each item
        for fix_item in fix_items:
            tex = unreal.load_asset(fix_item["path"])
            modified = False
            
            # Update sRGB if present in fix_item
            if "srgb" in fix_item and fix_item["srgb"] != tex.get_editor_property("srgb"):
                tex.set_editor_property("srgb", fix_item["srgb"])
                modified = True
            
            # Update compression settings if present in fix_item
            if "compression_settings" in fix_item:
                current_compression = str(tex.get_editor_property("compression_settings")).split(".",1)[1].split(":",1)[0]
                if fix_item["compression_settings"] != current_compression:
                    try:
                        new_compression = eval(f"unreal.TextureCompressionSettings.{fix_item['compression_settings']}")
                        tex.set_editor_property("compression_settings", new_compression)
                        modified = True
                    except:
                        pass
                        
            # Update brightness curve if present in fix_item
            if "brightness_curve" in fix_item:
                try:
                    current_brightness = tex.get_editor_property("adjust_brightness_curve")
                    # Use a small epsilon (0.001) for floating-point comparison to avoid precision issues
                    if abs(fix_item["brightness_curve"] - current_brightness) > 0.001:
                        tex.set_editor_property("adjust_brightness_curve", fix_item["brightness_curve"])
                        modified = True
                except:
                    pass
                
            # Update texture group if present in fix_item
            if "texture_group" in fix_item and fix_item["texture_group"] != "Not specified":
                try:
                    target_group = fix_item["texture_group"]
                    
                    # Find the matching enum value for the target group display name
                    target_enum = self.display_to_enum.get(target_group)
                    
                    if target_enum:
                        # Set the property using the enum value
                        tex.set_editor_property("lod_group", target_enum)
                        modified = True
                    else:
                        # If not found in our mapping, try direct lookup in the enum
                        for attr in dir(unreal.TextureGroup):
                            if attr.startswith('TEXTUREGROUP_'):
                                enum_value = getattr(unreal.TextureGroup, attr)
                                if enum_value.get_display_name() == target_group:
                                    tex.set_editor_property("lod_group", enum_value)
                                    modified = True
                                    break
                except:
                    pass

            if modified:
                fixed_count += 1
        
        # Refresh the UI
        self.status_label.setText(f"Fixed {fixed_count} textures")
        self.check_texture()

try:
    import unreal
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
        font = QFont("Meiryo UI")
        font.setPointSize(10)
        app.setFont(font)
    
    widget = TextureCheckerGUI()
    widget.show()
    unreal.parent_external_window_to_slate(widget.winId())
except ImportError:
    print("This tool must be run within Unreal Engine.")
    sys.exit(1)