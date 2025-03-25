from __future__ import unicode_literals, print_function
import sys
import os
import csv
import re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
#sys.path.extend([SCRIPT_DIR, PARENT_DIR, os.path.join(PARENT_DIR, "ThirdParty")])
python_lib = "//192.168.1.10/Softwares/Pipeline/GSTools/Library/Python/Python39/Lib/site-packages"
if os.path.exists(python_lib):
    sys.path.append(python_lib)
else:
    print(f"Warning: {python_lib} does not exist")

from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import Qt

class TextureCheckerGUI(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.load_style()
        # Define texture type rules based on suffix
        self.texture_rules = {
            "_d": {
                "type": "diffuse", 
                "compression_settings": "TC_DEFAULT", 
                "srgb": True
            },
            "_l": {
                "type": "colormask", 
                "compression_settings": "TC_MASKS", 
                "srgb": False
            },
            "_n": {
                "type": "normal", 
                "compression_settings": "TC_NORMALMAP", 
                "srgb": False
            },
            "_m": {
                "type": "mask", 
                "compression_settings": "TC_ALPHA", 
                "srgb": False
            },
            "_mask": {
                "type": "mask", 
                "compression_settings": "TC_MASKS", 
                "srgb": False
            },
            "inc": {
                "type": "mask", 
                "compression_settings": "TC_MASKS", 
                "srgb": False
            }
        }
        
    def setup_ui(self):
        """Initialize the main UI components"""
        self.setWindowTitle("R6 Texture Checker")
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
        self.texture_tree.setColumnCount(7)
        self.texture_tree.setHeaderLabels(["0/1", "name", "type", "size", "compression_settings", "texture_group", "srgb"])
        self.texture_tree.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.texture_tree.setIndentation(5)
        self.texture_tree.setAlternatingRowColors(True)
        
        # Set column behaviors
        header = self.texture_tree.header()
        for i in range(7):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
            
        self.texture_tree.itemDoubleClicked.connect(self.open_asset)
        
    def load_style(self):
        """Load QSS style file"""
        style = ''
        for style_path in [os.path.join(dir, 'style.qss') for dir in [SCRIPT_DIR, PARENT_DIR]]:
            if os.path.exists(style_path):
                try:
                    with open(style_path, 'r') as f:
                        style = f.read()
                        break
                except Exception as e:
                    print(f"Warning: Could not load style file: {e}")
                    
        self.setStyleSheet(style)
        
    def get_texture_property(self):
        """Load and parse texture properties from CSV"""
        csv_path = os.path.join(SCRIPT_DIR, "R6_TextureProperty.csv")
        properties = []
        
        if os.path.exists(csv_path):
            try:
                with open(csv_path) as f:
                    reader = csv.DictReader(f)
                    properties = [row for row in reader]
                    
                # Convert TRUE/FALSE strings to Python booleans
                # But keep texture_group and prefix_check as strings for exact matching
                for prop in properties:
                    for key in prop:
                        if key not in ["texture_group", "prefix_check"] and prop[key] in ["TRUE", "FALSE"]:
                            prop[key] = prop[key] == "TRUE"
            except Exception as e:
                print(f"Warning: Could not load properties: {e}")
                self.status_label.setText(f"Error loading CSV: {e}")
        else:
            print(f"Warning: CSV file not found at {csv_path}")
            self.status_label.setText(f"CSV file not found at {csv_path}")
                    
        return properties

    def get_rule_from_name(self, texture_name, csv_prefixes=None):
        """Determine texture properties based on file name suffix and prefix check"""
        texture_name_lower = texture_name.lower()
        
        # Check prefix first - extract prefix (text part before any numbers)
        prefix_match = re.match(r'^([a-zA-Z_]+)', texture_name_lower)
        prefix = prefix_match.group(1) if prefix_match else ""
        
        # If we have CSV prefixes, check if our prefix is allowed
        if csv_prefixes and prefix:
            prefix_allowed = False
            for allowed_prefix in csv_prefixes:
                if allowed_prefix and allowed_prefix.lower() in prefix:
                    prefix_allowed = True
                    break
            
            # If prefix not in allowed list, return None (zero match)
            if not prefix_allowed:
                return None
        
        # Check for inc* pattern (ending with inc followed by numbers)
        if re.search(r'inc\d+$', texture_name_lower):
            return self.texture_rules["inc"]
        
        # Check for each suffix pattern in order of specificity
        for suffix in ["_mask", "_d", "_l", "_n", "_m"]:
            if texture_name_lower.endswith(suffix):
                return self.texture_rules[suffix]
        
        # If no known suffix found, return None to mark as zero match
        return None

    def get_column_from_header(self, widget, match_text):
        """Get column index from header text"""
        header_item = widget.headerItem()
        for i in range(header_item.columnCount()):
            if header_item.text(i) == match_text:
                return i
        return None

    def create_custom_widget_item(self, color, value_dict, color_dict, meta_data):
        """Create a custom tree widget item"""
        item = QTreeWidgetItem()
        
        # Set text values
        for key, value in value_dict.items():
            column = self.get_column_from_header(self.texture_tree, key)
            if column is not None:
                item.setText(column, str(value))
        
        # Set colors
        for key, color_value in color_dict.items():
            column = self.get_column_from_header(self.texture_tree, key)
            if column is not None:
                item.setForeground(column, QBrush(QColor(color_value)))
        
        # Set special properties based on type
        if "type_match" in value_dict:
            if value_dict["type_match"] == "zero match":
                item.setForeground(2, QBrush(QColor("red")))
            elif value_dict["type_match"] == "multiple matches":
                item.setForeground(2, QBrush(QColor("yellow")))
        
        # Set checkbox state
        item.setCheckState(0, Qt.Checked if value_dict.get("0/1") == "1" else Qt.Unchecked)
        item.setText(0, "")
        
        # Set metadata and color
        item.setText(20, str(meta_data))
        item.setForeground(1, QBrush(QColor(color)))
        
        return item

    def check_texture(self):
        """Check textures and update UI"""
        try:
            import unreal
            
            texture_paths = self.get_texture_paths_from_selected_actors()
            if not texture_paths:
                self.texture_tree.clear()
                self.status_label.setText("No textures found in selected actors")
                return
            
            self.status_label.setText(f"Checking textures in {len(texture_paths)} paths...")
            
            unique_assets = {}
            for path in texture_paths:
                assets = unreal.EditorAssetLibrary.list_assets(path)
                for asset in assets:
                    unique_assets[asset] = True
            
            load_list = [unreal.load_asset(i) for i in unique_assets.keys()]
            texture_dict = {}
            
            for tex in unreal.EditorFilterLibrary.by_class(load_list, unreal.Texture2D):
                path = tex.get_path_name()
                texture_dict[path] = tex
            
            texture_list = list(texture_dict.values())
            
            # Update tree widget headers
            self.texture_tree.clear()
            
            # Extract all allowed prefixes from CSV
            csv_properties = self.get_texture_property()
            allowed_prefixes = []
            for prop in csv_properties:
                if "prefix_check" in prop and prop["prefix_check"]:
                    prefixes = [p.strip() for p in str(prop["prefix_check"]).split("|")]
                    allowed_prefixes.extend(prefixes)
            
            # Track textures by similar naming patterns
            textures_by_pattern = {}
            
            # First pass: Check all textures and determine their rules
            for tex in texture_list:
                tex_name = tex.get_name()
                
                # Default color is white, but will be changed below if needed
                color = "white"
                
                # Get the rule that should be applied based on the texture name and allowed prefixes
                rule = self.get_rule_from_name(tex_name, allowed_prefixes)
                
                # Initialize value dictionary
                value_dict = {
                    "name": tex_name,
                    "0/1": "0"
                }
                
                if rule is None:
                    # No matching rule - mark as zero match
                    value_dict["type"] = "zero match"
                    value_dict["type_match"] = "zero match"
                    value_dict["0/1"] = "0"  # Don't mark for fixing
                    color = "red"
                else:
                    value_dict["type"] = rule["type"]
                
                # Get tag values if available
                try:
                    tag_list = unreal.EditorAssetLibrary.get_tag_values(tex.get_path_name())
                    if "Dimensions" in tag_list:
                        value_dict["size"] = tag_list["Dimensions"]
                except:
                    # Fallback method to get texture dimensions
                    try:
                        width = tex.get_editor_property("blueprint_get_size_x")
                        height = tex.get_editor_property("blueprint_get_size_y")
                        value_dict["size"] = f"{width}x{height}"
                    except:
                        value_dict["size"] = "Unknown"
                
                # Get current properties
                current_compression = str(tex.get_editor_property("compression_settings")).split(".",1)[1].split(":",1)[0]
                value_dict["compression_settings"] = current_compression
                
                lod_group = tex.get_editor_property("lod_group")
                value_dict["texture_group"] = lod_group.get_display_name()
                
                current_mip = str(tex.get_editor_property("mip_gen_settings")).split(".",1)[1].split(":",1)[0]
                value_dict["mip_gen_settings"] = current_mip
                
                current_srgb = tex.get_editor_property("srgb")
                value_dict["srgb"] = current_srgb
                
                # Create metadata for fixing
                meta_data = {
                    "path": tex.get_path_name(),
                    "lod_group_enum": str(lod_group),
                    "mip_gen_settings": value_dict["mip_gen_settings"]  # Keep existing mip settings
                }
                # Color dictionary for highlighting
                color_dict = {}
            
                # Check size - should be 4096x4096, but we only highlight it as it can't be fixed in Unreal
                if "size" in value_dict:
                    if value_dict["size"] != "4096x4096":
                        color_dict["size"] = "yellow"
                
                # Add type, compression settings and sRGB if we have a valid rule
                if rule is not None:
                    meta_data["type"] = rule["type"]
                    meta_data["compression_settings"] = rule["compression_settings"]
                    meta_data["srgb"] = rule["srgb"]
                
                # Check if properties need to be updated (only if we have a rule)
                if rule is not None:
                    # Check for CSV override for compression settings
                    for prop in csv_properties:
                        if not prop.get("name") or not prop.get("compression_settings"):
                            continue
                            
                        csv_name_patterns = [p.strip().lower() for p in prop.get("name", "").split("|")]
                        tex_name_lower = tex_name.lower()
                        
                        # Try exact match first
                        if any(tex_name_lower == pattern for pattern in csv_name_patterns):
                            meta_data["compression_settings"] = prop.get("compression_settings")
                            break
                        
                        # Try wildcard pattern match
                        for pattern in csv_name_patterns:
                            if "*" in pattern:
                                pattern_regex = pattern.replace("*", ".*")
                                try:
                                    if re.match(f"^{pattern_regex}$", tex_name_lower):
                                        meta_data["compression_settings"] = prop.get("compression_settings")
                                        break
                                except re.error:
                                    continue
                    
                    # Check if compression settings need to be updated
                    if current_compression != meta_data["compression_settings"]:
                        color_dict["compression_settings"] = "red"
                        value_dict["0/1"] = "1"
                    
                    # Check sRGB - UNTOUCHED FROM ORIGINAL
                    if current_srgb != rule["srgb"]:
                        color_dict["srgb"] = "red"
                        value_dict["0/1"] = "1"
                
                # Find matching entry in CSV for overrides
                csv_override = None
                for prop in csv_properties:
                    if not prop.get("name"):
                        continue
                        
                    csv_name_patterns = [p.strip().lower() for p in prop.get("name", "").split("|")]
                    tex_name_lower = tex_name.lower()
                    
                    # Try exact match first
                    if any(tex_name_lower == pattern for pattern in csv_name_patterns):
                        csv_override = prop
                        break
                    
                    # Try wildcard pattern match
                    for pattern in csv_name_patterns:
                        if "*" in pattern:
                            pattern_regex = pattern.replace("*", ".*")
                            try:
                                if re.match(f"^{pattern_regex}$", tex_name_lower):
                                    csv_override = prop
                                    break
                            except re.error:
                                continue
                    
                    if csv_override:
                        break
                
                # Apply CSV overrides if found (this is the new part)
                if csv_override:
                    # Override compression settings if specified in CSV
                    if "compression_settings" in csv_override and csv_override["compression_settings"]:
                        compression_from_csv = csv_override["compression_settings"]
                        meta_data["compression_settings"] = compression_from_csv
                        
                        # Highlight if different from current
                        if current_compression != compression_from_csv:
                            color_dict["compression_settings"] = "red"
                            value_dict["0/1"] = "1"
                
                # Find texture group from CSV (keep original logic)
                texture_group_from_csv = None
                
                # Try to find matching entry in CSV
                for prop in csv_properties:
                    csv_name_patterns = [p.strip().lower() for p in prop.get("name", "").split("|")]
                    tex_name_lower = tex_name.lower()
                    
                    # Try exact match first
                    if any(tex_name_lower == pattern for pattern in csv_name_patterns):
                        texture_group_from_csv = prop.get("texture_group")
                        break
                    
                    # Try wildcard pattern match
                    for pattern in csv_name_patterns:
                        if "*" in pattern:
                            pattern_regex = pattern.replace("*", ".*")
                            try:
                                if re.match(f"^{pattern_regex}$", tex_name_lower):
                                    texture_group_from_csv = prop.get("texture_group")
                                    break
                            except re.error:
                                continue
                    
                    if texture_group_from_csv:
                        break
                
                # Only check texture group if we found one in the CSV
                if texture_group_from_csv:
                    current_texture_group = lod_group.get_display_name()
                    if str(current_texture_group) != str(texture_group_from_csv):
                        color_dict["texture_group"] = "red"
                        value_dict["0/1"] = "1"
                        meta_data["texture_group"] = texture_group_from_csv
                
                # Group by pattern for similar naming convention
                prefix = re.match(r'([a-zA-Z]+)', tex_name.lower())
                prefix = prefix.group(1) if prefix else ""
                
                # Find the suffix used for categorization
                found_suffix = None
                if re.search(r'inc\d+$', tex_name.lower()):
                    found_suffix = "inc"
                else:
                    for suffix in ["_mask", "_d", "_l", "_n", "_m"]:
                        if tex_name.lower().endswith(suffix):
                            found_suffix = suffix
                            break
                
                # Create pattern key for grouping
                if rule is None:
                    pattern_key = f"{prefix}_zero_match"
                else:
                    pattern_key = f"{prefix}_{found_suffix if found_suffix else 'other'}"
                
                if pattern_key not in textures_by_pattern:
                    textures_by_pattern[pattern_key] = []
                
                textures_by_pattern[pattern_key].append((rule, color_dict, value_dict, meta_data, tex_name))
            
            # Second pass: Create items and check for multiple matches
            items_to_add = []
            
            for pattern_key, textures in textures_by_pattern.items():
                # Filter out textures with "custom" or "rain" in their name for special handling
                special_textures = []
                regular_textures = []
                
                for tex_info in textures:
                    rule, color_dict, value_dict, meta_data, tex_name = tex_info
                    if "custom" in tex_name.lower() or "rain" in tex_name.lower():
                        special_textures.append(tex_info)
                    else:
                        regular_textures.append(tex_info)
                
                # Process special textures individually
                for rule, color_dict, value_dict, meta_data, tex_name in special_textures:
                    # For zero match, color should be red
                    if rule is None:
                        item_color = "red"
                    else:
                        item_color = "white"
                    
                    item = self.create_custom_widget_item(item_color, value_dict, color_dict, meta_data)
                    
                    # Use CSV-like ordering for sorting (preserve original sorting)
                    suffix_priority = {"_d": 1, "_l": 2, "_n": 3, "_m": 4, "_mask": 5, "inc": 6}
                    
                    # Determine suffix
                    suffix_found = None
                    if re.search(r'inc\d+$', tex_name.lower()):
                        suffix_found = "inc"
                    else:
                        for suffix in suffix_priority:
                            if tex_name.lower().endswith(suffix):
                                suffix_found = suffix
                                break
                    
                    # Determine priority - zero match gets highest priority to appear at top
                    if rule is None:
                        priority = 0  # Zero match
                    else:
                        priority = suffix_priority.get(suffix_found, 7)  # Default priority if no match
                    
                    items_to_add.append((priority, item))
                
                # Process remaining textures
                if len(regular_textures) > 1:  # Multiple textures with same pattern
                    # Check if they should all have the same properties
                    for rule, color_dict, value_dict, meta_data, tex_name in regular_textures:
                        # For zero match textures, don't add multiple matches flag, just mark them individually
                        if rule is None:
                            item_color = "red"
                        else:
                            value_dict["type_match"] = "multiple matches"
                            item_color = "yellow"
                        
                        item = self.create_custom_widget_item(item_color, value_dict, color_dict, meta_data)
                        
                        # Use CSV-like ordering for sorting
                        suffix_priority = {"_d": 1, "_l": 2, "_n": 3, "_m": 4, "_mask": 5, "inc": 6}
                        
                        # Determine suffix
                        suffix_found = None
                        if re.search(r'inc\d+$', tex_name.lower()):
                            suffix_found = "inc"
                        else:
                            for suffix in suffix_priority:
                                if tex_name.lower().endswith(suffix):
                                    suffix_found = suffix
                                    break
                        
                        # Determine priority - zero match gets highest priority
                        if rule is None:
                            priority = 0  # Zero match
                        else:
                            priority = suffix_priority.get(suffix_found, 7)  # Default priority if no match
                        
                        items_to_add.append((priority, item))
                        
                elif len(regular_textures) == 1:  # Single texture with this pattern
                    rule, color_dict, value_dict, meta_data, tex_name = regular_textures[0]
                    
                    # For zero match, color should be red
                    if rule is None:
                        item_color = "red"
                    else:
                        item_color = "white"
                        
                    item = self.create_custom_widget_item(item_color, value_dict, color_dict, meta_data)
                    
                    # Use CSV-like ordering for sorting
                    suffix_priority = {"_d": 1, "_l": 2, "_n": 3, "_m": 4, "_mask": 5, "inc": 6}
                    
                    # Determine suffix
                    suffix_found = None
                    if re.search(r'inc\d+$', tex_name.lower()):
                        suffix_found = "inc"
                    else:
                        for suffix in suffix_priority:
                            if tex_name.lower().endswith(suffix):
                                suffix_found = suffix
                                break
                    
                    # Determine priority - zero match gets highest priority
                    if rule is None:
                        priority = 0  # Zero match
                    else:
                        priority = suffix_priority.get(suffix_found, 7)  # Default priority if no match
                    
                    items_to_add.append((priority, item))
            
            # Sort items by the assigned priority (CSV-like order)
            items_to_add.sort(key=lambda x: x[0])
            for _, item in items_to_add:
                self.texture_tree.addTopLevelItem(item)
            
            # Resize columns
            for i in range(self.texture_tree.columnCount()):
                self.texture_tree.resizeColumnToContents(i)
            
            # Update status label with count of textures needing fixing and zero matches
            needs_fixing = sum(1 for _, item in items_to_add if item.checkState(0) == Qt.Checked)
            zero_matches = sum(1 for _, item in items_to_add if "zero match" in item.text(2))
            self.status_label.setText(f"Found {len(texture_list)} textures. {needs_fixing} need fixing. {zero_matches} have no matching suffix/prefix.")
                
        except ImportError:
            self.status_label.setText("Unreal Engine module not available")
            print("Unreal Engine module not available")

    def get_texture_paths_from_selected_actors(self):
        """Get texture paths from selected actors in Unreal Engine"""
        import unreal
        texture_paths = set()
        
        actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        selected_actors = actor_subsystem.get_selected_level_actors()
        
        for actor in selected_actors:
            if isinstance(actor, (unreal.SkeletalMeshActor, unreal.StaticMeshActor)):
                mesh_component = (actor.skeletal_mesh_component 
                                if isinstance(actor, unreal.SkeletalMeshActor) 
                                else actor.static_mesh_component)
                                
                if mesh_component:
                    mesh = (mesh_component.get_skeletal_mesh_asset() 
                           if isinstance(actor, unreal.SkeletalMeshActor) 
                           else mesh_component.static_mesh)
                    
                    if mesh:
                        mesh_path = mesh.get_path_name()
                        parent_dir = "/".join(mesh_path.split("/")[:-2])
                        texture_paths.add(f"{parent_dir}/textures")
                        
        return list(texture_paths)
        
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
            
        # Cache for texture group mappings
        display_to_enum = {}
        fixed_count = 0
        
        # Process each item
        for fix_item in fix_items:
            tex = unreal.load_asset(fix_item["path"])
            modified = False
            
            # Update sRGB
            if "srgb" in fix_item and fix_item["srgb"] != tex.get_editor_property("srgb"):
                tex.set_editor_property("srgb", fix_item["srgb"])
                modified = True
                print(f"Updated sRGB for {fix_item['path']} to {fix_item['srgb']}")
            
            # Update compression settings
            if "compression_settings" in fix_item:
                current_compression = str(tex.get_editor_property("compression_settings")).split(".",1)[1].split(":",1)[0]
                if fix_item["compression_settings"] != current_compression:
                    try:
                        new_compression = eval(f"unreal.TextureCompressionSettings.{fix_item['compression_settings']}")
                        tex.set_editor_property("compression_settings", new_compression)
                        modified = True
                        print(f"Updated compression for {fix_item['path']} to {fix_item['compression_settings']}")
                    except Exception as e:
                        print(f"Error setting compression: {e}")
            
            # Update texture group (if needed)
            if "texture_group" in fix_item:
                current_group = tex.get_editor_property("lod_group")
                target_group = fix_item.get("texture_group")
                
                if target_group and current_group.get_display_name() != target_group:
                    if target_group not in display_to_enum:
                        # Try direct mapping first
                        enum_found = False
                        for attr in dir(unreal.TextureGroup):
                            if attr.startswith("TEXTUREGROUP_"):
                                enum_value = getattr(unreal.TextureGroup, attr)
                                if enum_value.get_display_name() == target_group:
                                    display_to_enum[target_group] = enum_value
                                    enum_found = True
                                    break
                        
                        # If not found, try case-insensitive matching
                        if not enum_found:
                            target_lower = target_group.lower()
                            for attr in dir(unreal.TextureGroup):
                                if attr.startswith("TEXTUREGROUP_"):
                                    enum_value = getattr(unreal.TextureGroup, attr)
                                    if enum_value.get_display_name().lower() == target_lower:
                                        display_to_enum[target_group] = enum_value
                                        enum_found = True
                                        print(f"Found texture group match: {target_group} -> {enum_value}")
                                        break
                    
                    if target_group in display_to_enum:
                        tex.set_editor_property("lod_group", display_to_enum[target_group])
                        modified = True
                        print(f"Updated texture group for {fix_item['path']} to {target_group}")
                    else:
                        print(f"Warning: Could not find texture group enum for {target_group}")
            
            # Update mip gen settings (if needed)
            if "mip_gen_settings" in fix_item:
                current_mip = str(tex.get_editor_property("mip_gen_settings")).split(".",1)[1].split(":",1)[0]
                target_mip = fix_item.get("mip_gen_settings")
                
                if target_mip and current_mip != target_mip:
                    try:
                        new_mip = eval(f"unreal.TextureMipGenSettings.{target_mip}")
                        tex.set_editor_property("mip_gen_settings", new_mip)
                        modified = True
                        print(f"Updated mip settings for {fix_item['path']} to {target_mip}")
                    except Exception as e:
                        print(f"Error setting mip settings: {e}")
                
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