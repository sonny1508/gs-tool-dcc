from __future__ import unicode_literals, print_function
import sys
import os
import csv
import re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
#sys.path.extend([SCRIPT_DIR, PARENT_DIR, os.path.join(PARENT_DIR, "ThirdParty")])
python_lib = "Z:/Pipeline/GSTools/Library/Python/Python39/Lib/site-packages"
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
        self.texture_tree.setColumnCount(3)
        self.texture_tree.setHeaderLabels(["0/1", "name", "type"])
        self.texture_tree.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.texture_tree.setIndentation(5)
        self.texture_tree.setAlternatingRowColors(True)
        
        # Set column behaviors
        header = self.texture_tree.header()
        for i in range(3):
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
        csv_path = os.path.join(PARENT_DIR, "R6_TextureProperty.csv")
        with open(csv_path) as f:
            reader = csv.DictReader(f)
            properties = [row for row in reader]
            
        # Convert TRUE/FALSE strings to Python booleans
        for prop in properties:
            for key in prop:
                if prop[key] in ["TRUE", "FALSE"]:
                    prop[key] = str(prop[key] == "TRUE")
                    
        return properties

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
        
        # Set special properties
        if value_dict["type"] == "zero match":
            item.setForeground(2, QBrush(QColor("red")))
        elif value_dict["type"] == "multiple matches":
            item.setForeground(2, QBrush(QColor("yellow")))
        # Set checkbox state
        item.setCheckState(0, Qt.Checked if value_dict["0/1"] == "1" else Qt.Unchecked)
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
                return
            
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
            check_dict = self.get_texture_property()
            key_list = list(check_dict[0].keys())
            
            # Update tree widget headers
            self.texture_tree.clear()
            header_labels = ["0/1"] + key_list
            self.texture_tree.setHeaderLabels(header_labels)
            
            # First pass: Do normal matching and store results
            initial_matches = []
            for tex in texture_list:
                value_dict = {}
                color_dict = {}
                
                # Get basic texture info
                tex_name = tex.get_name()
                value_dict["name"] = tex_name
                
                # Get tag values
                tag_list = unreal.EditorAssetLibrary.get_tag_values(tex.get_path_name())
                value_dict["size"] = tag_list["Dimensions"]
                
                # Get current properties
                value_dict["compression_settings"] = str(tex.get_editor_property("compression_settings")).split(".",1)[1].split(":",1)[0]
                lod_group = tex.get_editor_property("lod_group")
                value_dict["texture_group"] = lod_group.get_display_name()
                value_dict["mip_gen_settings"] = str(tex.get_editor_property("mip_gen_settings")).split(".",1)[1].split(":",1)[0]
                value_dict["srgb"] = tex.get_editor_property("srgb")
                
                # Find matching rule
                matched_rule = None
                matched_index = -1
                
                for idx, rule in enumerate(check_dict):
                    patterns = [p.strip().lower() for p in rule["name"].split("|")]
                    tex_name_lower = tex_name.lower()
                    
                    if any(tex_name_lower == pattern for pattern in patterns):
                        matched_rule = rule
                        matched_index = idx
                        break
                    
                    if not matched_rule:
                        for pattern in patterns:
                            if "*" in pattern:
                                pattern = pattern.replace("*", ".*")
                                if re.match(f"^{pattern}$", tex_name_lower):
                                    matched_rule = rule
                                    matched_index = idx
                                    break
                
                if matched_rule:
                    meta_data = dict(matched_rule)
                    meta_data["lod_group_enum"] = str(lod_group)
                    color = "white"
                    value_dict["0/1"] = "0"
                    value_dict["type"] = matched_rule["type"]
                    
                    # Check properties against rule
                    self.check_texture_properties(value_dict, matched_rule, color_dict)
                else:
                    color = "red"
                    value_dict["0/1"] = "0"
                    value_dict["type"] = "zero match"
                    meta_data = {"path": tex.get_path_name(), "lod_group_enum": str(lod_group)}
                
                meta_data["path"] = tex.get_path_name()
                initial_matches.append((matched_index, color, value_dict, color_dict, meta_data, tex_name))

            # Second pass: Check for similar prefix/suffix patterns
            similar_groups = {}  # Dictionary to store groups of similar items
            
            for i, (idx1, _, value_dict1, _, _, name1) in enumerate(initial_matches):
                # Get prefix and suffix
                prefix1 = re.match(r'([a-zA-Z]+)', name1.lower()).group(1)
                suffix1 = name1[name1.rindex('_'):] if '_' in name1 else ''
                
                # Create a key for this pattern
                pattern_key = f"{prefix1}{suffix1}"
                
                # Add to similar groups
                if pattern_key not in similar_groups:
                    similar_groups[pattern_key] = []
                similar_groups[pattern_key].append(i)

            # Create final items list
            items_to_add = []
            for pattern_key, indices in similar_groups.items():
                if len(indices) > 1:  # If there are multiple items with same pattern
                    # Add all items from the group as multiple matches
                    for idx in indices:
                        matched_index, _, value_dict, color_dict, meta_data, _ = initial_matches[idx]
                        value_dict["type"] = "multiple matches"
                        item = self.create_custom_widget_item("yellow", value_dict, color_dict, meta_data)
                        items_to_add.append((matched_index, item))
                else:  # Single item with this pattern
                    idx = indices[0]
                    matched_index, color, value_dict, color_dict, meta_data, _ = initial_matches[idx]
                    item = self.create_custom_widget_item(color, value_dict, color_dict, meta_data)
                    items_to_add.append((matched_index, item))
            
            # Sort and add items
            items_to_add.sort(key=lambda x: (x[0] if x[0] >= 0 else float('inf')))
            for _, item in items_to_add:
                self.texture_tree.addTopLevelItem(item)
            
            # Resize columns
            for i in range(self.texture_tree.columnCount()):
                self.texture_tree.resizeColumnToContents(i)
                
        except ImportError:
            print("Unreal Engine module not available")
            
    def check_texture_properties(self, value_dict, rule, color_dict):
        """Check texture properties against rules"""

        # Check size if both values exist
        if "size" in rule and "size" in value_dict:
            if str(value_dict["size"]) != str(rule["size"]):
                color_dict["size"] = "yellow"
            
        # Check main properties
        for prop in ["compression_settings", "texture_group", "mip_gen_settings", "srgb"]:
            if prop in rule and prop in value_dict:
                if str(value_dict[prop]) != str(rule[prop]):
                    color_dict[prop] = "red"
                    value_dict["0/1"] = "1"           
            
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
            
        # Cache for texture group mappings
        display_to_enum = {}
        
        # Process each item
        for fix_item in fix_items:
            tex = unreal.load_asset(fix_item["path"])
            
            # Update sRGB
            if fix_item["srgb"] != str(tex.get_editor_property("srgb")):
                tex.set_editor_property("srgb", fix_item["srgb"] == "True")
            
            # Update compression settings
            if fix_item["compression_settings"] != str(tex.get_editor_property("compression_settings")).split(".",1)[1].split(":",1)[0]:
                new_compression = eval(f"unreal.TextureCompressionSettings.{fix_item['compression_settings']}")
                tex.set_editor_property("compression_settings", new_compression)
            
            # Update texture group
            current_group = tex.get_editor_property("lod_group")
            target_group = fix_item["texture_group"]
            
            if current_group.get_display_name() != target_group:
                if target_group not in display_to_enum:
                    for attr in dir(unreal.TextureGroup):
                        if attr.startswith("TEXTUREGROUP_"):
                            enum_value = getattr(unreal.TextureGroup, attr)
                            if enum_value.get_display_name() == target_group:
                                display_to_enum[target_group] = enum_value
                                break
                
                if target_group in display_to_enum:
                    tex.set_editor_property("lod_group", display_to_enum[target_group])
            
            # Update mip gen settings
            if fix_item["mip_gen_settings"] != str(tex.get_editor_property("mip_gen_settings")).split(".",1)[1].split(":",1)[0]:
                new_mip = eval(f"unreal.TextureMipGenSettings.{fix_item['mip_gen_settings']}")
                tex.set_editor_property("mip_gen_settings", new_mip)
        
        # Refresh the UI
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