from __future__ import unicode_literals, print_function
import sys
import os
import csv
import re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
#sys.path.extend([SCRIPT_DIR, PARENT_DIR, os.path.join(PARENT_DIR, "ThirdParty")])
python_lib = "//192.168.1.10/Pipeline/GSTools/Library/Python/Python39/Lib/site-packages"
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
            "BC": {
                "compression_settings": "TC_DEFAULT", 
                "srgb": True,
                "brightness_curve": 1.0
            },
            "E": {
                "compression_settings": "TC_DEFAULT", 
                "srgb": True,
                "brightness_curve": 1.0
            },
            "PBR": {
                "compression_settings": "TC_MASKS", 
                "srgb": False,
                "brightness_curve": 1.0
            },
            "M": {
                "compression_settings": "TC_ALPHA", 
                "srgb": False,
                "brightness_curve": 2.2
            },
            "IC_M": {
                "compression_settings": "TC_ALPHA", 
                "srgb": False,
                "brightness_curve": 1.0
            },
            "N": {
                "compression_settings": "TC_NORMALMAP", 
                "srgb": False,
                "brightness_curve": 1.0
            }
        }
        
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
        # Updated to include brightness_curve column
        self.texture_tree.setColumnCount(5)  # 0/1 checkbox + 4 columns
        self.texture_tree.setHeaderLabels(["0/1", "name", "compression_settings", "srgb", "brightness_curve"])
        self.texture_tree.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.texture_tree.setIndentation(5)
        self.texture_tree.setAlternatingRowColors(True)
        
        # Set column behaviors
        header = self.texture_tree.header()
        for i in range(5):  # Adjusted for new column count
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
        csv_path = os.path.join(PARENT_DIR, "SCR1_Texture_Property.csv")
        properties = []
        
        if os.path.exists(csv_path):
            try:
                with open(csv_path) as f:
                    reader = csv.DictReader(f)
                    properties = [row for row in reader]
                    
                # Convert TRUE/FALSE strings to Python booleans
                for prop in properties:
                    for key in prop:
                        if key not in ["name"] and prop[key] in ["TRUE", "FALSE"]:
                            prop[key] = prop[key] == "TRUE"
            except Exception as e:
                print(f"Warning: Could not load properties: {e}")
                self.status_label.setText(f"Error loading CSV: {e}")
        else:
            print(f"Warning: CSV file not found at {csv_path}")
            self.status_label.setText(f"CSV file not found at {csv_path}")
                    
        return properties

    def get_rule_from_name(self, texture_name):
        """Determine texture properties based on file name suffix"""
        texture_name_lower = texture_name.lower()
        
        # Order suffixes from most specific to least specific to avoid substring matching issues
        suffix_priority = ["IC_M", "PBR", "BC", "E", "N", "M"]
        
        # Check each suffix in priority order
        for suffix in suffix_priority:
            suffix_lower = suffix.lower()
            
            # For simple suffixes like M, N, E, ensure they're actually suffixes
            # or pattern matches, not just substrings
            if suffix in ["M", "N", "E", "BC"]:
                # Check if it appears at the end or is followed by numbers
                if (texture_name_lower.endswith(suffix_lower) or 
                    re.search(f"{suffix_lower}\\d+", texture_name_lower)):
                    return self.texture_rules[suffix]
            # For compound suffixes, a simple contains check is usually sufficient
            # but we still need to be careful
            elif suffix == "IC_M":
                if "ic_m" in texture_name_lower:
                    return self.texture_rules[suffix]
            elif suffix == "PBR":
                if "pbr" in texture_name_lower:
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
            
            # First pass: Check all textures and determine their rules
            for tex in texture_list:
                tex_name = tex.get_name()
                
                # Default color is white, but will be changed below if needed
                color = "white"
                
                # Get the rule that should be applied based on the texture name
                rule = self.get_rule_from_name(tex_name)
                
                # Initialize value dictionary
                value_dict = {
                    "name": tex_name,
                    "0/1": "0"
                }
                
                # Get current properties
                current_compression = str(tex.get_editor_property("compression_settings")).split(".",1)[1].split(":",1)[0]
                value_dict["compression_settings"] = current_compression
                
                current_srgb = tex.get_editor_property("srgb")
                value_dict["srgb"] = current_srgb
                
                # Get brightness curve value - using the correct property name "adjust_brightness_curve"
                try:
                    current_brightness_curve = tex.get_editor_property("adjust_brightness_curve")
                except Exception:
                    # Property might not exist, default to 0
                    current_brightness_curve = 0.0
                
                value_dict["brightness_curve"] = current_brightness_curve
                
                # Create metadata for fixing
                meta_data = {
                    "path": tex.get_path_name()
                }
                
                # Color dictionary for highlighting
                color_dict = {}
                
                # If we have a rule, check if properties need fixing
                if rule is not None:
                    # Add rule values to metadata
                    meta_data["compression_settings"] = rule["compression_settings"]
                    meta_data["srgb"] = rule["srgb"]
                    meta_data["brightness_curve"] = rule["brightness_curve"]
                    
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
                    except Exception:
                        # Skip comparison if there's an issue
                        pass
                else:
                    # No matching rule - don't mark for fixing
                    color = "red"
                
                # Group by pattern for similar naming convention
                prefix = re.match(r'([a-zA-Z]+)', tex_name.lower())
                prefix = prefix.group(1) if prefix else ""
                
                # Create pattern key for grouping
                if rule is None:
                    pattern_key = f"{prefix}_zero_match"
                else:
                    # Define suffix priority for consistent matching
                    suffix_priority = ["IC_M", "PBR", "BC", "E", "N", "M"]
                    # Find which rule matched
                    matched_suffix = "unknown"
                    for suffix in self.texture_rules:
                        if suffix.lower() in tex_name.lower():
                            matched_suffix = suffix
                            break
                    pattern_key = f"{prefix}_{matched_suffix}"
                
                if pattern_key not in textures_by_pattern:
                    textures_by_pattern[pattern_key] = []
                
                textures_by_pattern[pattern_key].append((rule, color_dict, value_dict, meta_data, tex_name))
            
            # Second pass: Create items
            items_to_add = []
            
            for pattern_key, textures in textures_by_pattern.items():
                for rule, color_dict, value_dict, meta_data, tex_name in textures:
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
            
            # Resize columns
            for i in range(self.texture_tree.columnCount()):
                self.texture_tree.resizeColumnToContents(i)
            
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
            
        fixed_count = 0
        
        # Process each item
        for fix_item in fix_items:
            tex = unreal.load_asset(fix_item["path"])
            modified = False
            
            # Update sRGB if present in fix_item
            if "srgb" in fix_item and fix_item["srgb"] != tex.get_editor_property("srgb"):
                tex.set_editor_property("srgb", fix_item["srgb"])
                modified = True
                print(f"Updated sRGB for {fix_item['path']} to {fix_item['srgb']}")
            
            # Update compression settings if present in fix_item
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
                        
            # Update brightness curve if present in fix_item
            if "brightness_curve" in fix_item:
                try:
                    current_brightness = tex.get_editor_property("adjust_brightness_curve")
                    # Use a small epsilon (0.001) for floating-point comparison to avoid precision issues
                    if abs(fix_item["brightness_curve"] - current_brightness) > 0.001:
                        tex.set_editor_property("adjust_brightness_curve", fix_item["brightness_curve"])
                        modified = True
                        print(f"Updated brightness curve for {fix_item['path']} to {fix_item['brightness_curve']}")
                except Exception as e:
                    print(f"Error setting brightness curve: {e}")
                
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