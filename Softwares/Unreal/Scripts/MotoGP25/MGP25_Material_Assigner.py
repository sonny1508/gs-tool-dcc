from __future__ import unicode_literals, print_function
import sys
import os
import re
import csv

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
python_lib = "//192.168.1.10/Softwares/Pipeline/GSTools/Library/Python/Python39/Lib/site-packages"
if os.path.exists(python_lib):
    sys.path.append(python_lib)

from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import Qt
import unreal


class MaterialAssigner(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Material Assigner")
        self.setWindowFlags(Qt.Window)
        self.skeletal_mesh = None
        self.material_slots = []
        self.material_mapping = []
        self.livery_materials = []
        self.variant_widgets = []
        self.material_instances_dir = ""
        self.initialize_special_variants()
        self.load_material_mapping()
        self.load_style()
        self.setup_ui()
        self.resize(800, 600)
    
    def load_material_mapping(self):
        """Load material mapping data from CSV file"""
        # Try both script directory and parent directory
        for dir_path in [SCRIPT_DIR, PARENT_DIR]:
            csv_path = os.path.join(dir_path, "MGP25_Material_Library.csv")
            if os.path.exists(csv_path):
                try:
                    with open(csv_path, 'r', encoding='utf-8') as f:
                        self.material_mapping = list(csv.DictReader(f))
                    return
                except Exception as e:
                    QMessageBox.warning(self, "Warning", f"Failed to load material mapping: {str(e)}")
                    return
        
        QMessageBox.warning(self, "Warning", "Material mapping CSV file not found")
    
    def load_style(self):
        """Load QSS style file"""
        for style_path in [os.path.join(dir_path, 'style.qss') for dir_path in [SCRIPT_DIR, PARENT_DIR]]:
            if os.path.exists(style_path):
                try:
                    with open(style_path, 'r') as f:
                        self.setStyleSheet(f.read())
                        return
                except:
                    pass

    def setup_ui(self):
        # Create main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(main_layout)
        
        # Add header
        header_label = QLabel("Material Assigner")
        header_label.setProperty("headerLabel", True)
        header_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header_label)
        
        # Add select mesh button
        select_button = QPushButton("Select Mesh")
        select_button.clicked.connect(self.select_skeletal_mesh)
        main_layout.addWidget(select_button)
        
        # Mesh info label
        self.mesh_info_label = QLabel("No skeletal mesh selected")
        self.mesh_info_label.setProperty("boldLabel", True)
        main_layout.addWidget(self.mesh_info_label)
        
        # Separator
        main_layout.addWidget(self.create_separator())
        
        # Livery and variant selection section
        selection_form = QFormLayout()
        selection_form.setContentsMargins(0, 0, 0, 0)
        
        # Create selection dropdowns
        self.livery_combo = self.create_combo_box("Select Livery", self.on_livery_selected)
        self.variant_combo = self.create_combo_box("Select Variant", self.on_variant_selected)
        self.variant_combo.setEnabled(False)
        
        self.id_combo = self.create_combo_box("Select ID", self.on_id_selected)
        self.id_combo.addItem("001")  # Currently only one option
        self.id_combo.setEnabled(False)
        
        # Add dropdowns to form layout
        selection_form.addRow("Livery:", self.livery_combo)
        selection_form.addRow("Variant:", self.variant_combo)
        selection_form.addRow("ID:", self.id_combo)
        main_layout.addLayout(selection_form)
        
        # Separator
        main_layout.addWidget(self.create_separator())
        
        # Material slots section
        slots_header = QLabel("Preview")
        slots_header.setProperty("boldLabel", True)
        main_layout.addWidget(slots_header)
        
        # Scrollable area for material slots preview
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        main_layout.addWidget(scroll_area)
        
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(4, 4, 4, 4)
        self.scroll_layout.setSpacing(4)
        scroll_area.setWidget(self.scroll_content)
        
        # Assign button
        assign_button = QPushButton("Assign Materials")
        assign_button.clicked.connect(self.assign_materials)
        main_layout.addWidget(assign_button)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.status_label)
    
    def create_separator(self):
        """Create a horizontal separator line"""
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        return line
    
    def create_combo_box(self, default_text, slot):
        """Create and style a combo box"""
        combo = QComboBox()
        combo.addItem(default_text)
        combo.currentIndexChanged.connect(slot)
        combo.setProperty("materialAssigner", True)
        return combo
    
    def select_skeletal_mesh(self):
        """Select and analyze the current skeletal mesh"""
        # Clear existing state
        self.material_slots = []
        self.livery_materials = []
        self.clear_variant_widgets()
        self.reset_ui_state()
        
        # Get selected skeletal mesh
        self.skeletal_mesh = self.get_selected_skeletal_mesh()
        
        if not self.skeletal_mesh:
            self.mesh_info_label.setText("No skeletal mesh selected")
            self.set_status("Please select a skeletal mesh in the Content Browser or Viewport", "error")
            return
                
        # Display skeletal mesh info
        self.mesh_info_label.setText(f"Selected: {self.skeletal_mesh.get_name()}")
        
        # Get material slots
        self.material_slots = self.get_skeletal_mesh_materials(self.skeletal_mesh)
        
        if not self.material_slots:
            self.set_status("No material slots found in this skeletal mesh", "error")
            return
        
        # Find available livery materials
        self.find_livery_materials()
        
        # Populate livery dropdown
        self.populate_livery_dropdown()
        
        # Display current materials immediately
        self.display_current_materials()
        
        self.set_status(f"Found {len(self.material_slots)} material slot(s)", "success")
    
    def reset_ui_state(self):
        """Reset UI components to their initial state"""
        self.status_label.setText("")
        self.status_label.setProperty("status", "")
        
        # Reset dropdowns
        self.livery_combo.clear()
        self.livery_combo.addItem("Select Livery")
        self.variant_combo.clear()
        self.variant_combo.addItem("Select Variant")
        self.variant_combo.setEnabled(False)
        self.id_combo.setEnabled(False)
    
    def set_status(self, message, status_type=""):
        """Set status message with appropriate styling"""
        self.status_label.setText(message)
        self.status_label.setProperty("status", status_type)
        
        # Force style update
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)
    
    def initialize_special_variants(self):
        """Initialize special variant mappings for specific chassis and liveries"""
        # Format: {chassis_suffix: {livery_id: [variants_list]}}
        self.special_variant_mappings = {
            "201": {
                "009": ["022", "023", "024"],
                "010": ["025", "026", "027"],
                "011": ["028", "029", "030"],
                "013": ["034", "035", "036"],
                # Add more special case liveries as needed
            },
            # Add more chassis types as needed
        }

    def extract_chassis_id(self, skeletal_mesh):
        """Extract chassis ID from the skeletal mesh name"""
        if not skeletal_mesh:
            return None
        
        mesh_name = skeletal_mesh.get_name()
        # Look for "chassis" followed by numbers in the mesh name
        match = re.search(r'chassis(\d+)', mesh_name, re.IGNORECASE)
        if match:
            return match.group(1)
        
        return None

    def get_selected_skeletal_mesh(self):
        """Get the first selected skeletal mesh in the editor"""
        # Try content browser selection first
        editor_util = unreal.EditorUtilityLibrary()
        selected_assets = editor_util.get_selected_assets()
        
        for asset in selected_assets:
            # Check if it's a skeletal mesh
            if hasattr(asset, 'is_a') and asset.is_a(unreal.SkeletalMesh):
                return asset
            
            # Alternative method to check skeletal mesh
            if hasattr(asset, 'get_editor_property'):
                try:
                    for prop in ['skeleton', 'reference_skeleton', 'skeletal_materials']:
                        try:
                            asset.get_editor_property(prop)
                            return asset
                        except:
                            pass
                except:
                    continue
        
        # Try viewport selection if content browser failed
        try:
            editor_level = unreal.EditorLevelLibrary()
            selected_actors = editor_level.get_selected_level_actors()
            
            for actor in selected_actors:
                # Try to identify skeletal mesh actors
                is_skeletal_mesh_actor = False
                if hasattr(actor, 'get_class'):
                    actor_class = actor.get_class().get_name()
                    is_skeletal_mesh_actor = 'SkeletalMeshActor' in actor_class
                
                if hasattr(actor, 'is_a') and not is_skeletal_mesh_actor:
                    is_skeletal_mesh_actor = actor.is_a(unreal.SkeletalMeshActor)
                
                # If it's a skeletal mesh actor, get the mesh
                if is_skeletal_mesh_actor:
                    # Try different ways to access the mesh
                    if hasattr(actor, 'skeletal_mesh_component'):
                        component = actor.skeletal_mesh_component
                        if component and hasattr(component, 'skeletal_mesh'):
                            return component.skeletal_mesh
                    
                    if hasattr(actor, 'get_editor_property'):
                        component = actor.get_editor_property('skeletal_mesh_component')
                        if component:
                            if hasattr(component, 'skeletal_mesh'):
                                return component.skeletal_mesh
                            if hasattr(component, 'get_editor_property'):
                                return component.get_editor_property('skeletal_mesh')
                
                # Look for any components with skeletal meshes
                components = []
                
                if hasattr(actor, 'get_components_by_class'):
                    components.extend(actor.get_components_by_class(unreal.SkeletalMeshComponent))
                
                if hasattr(actor, 'get_components'):
                    for comp in actor.get_components():
                        is_mesh_comp = False
                        if hasattr(comp, 'get_class'):
                            try:
                                comp_class = comp.get_class().get_name()
                                is_mesh_comp = 'SkeletalMeshComponent' in comp_class
                            except:
                                pass
                        
                        if hasattr(comp, 'is_a'):
                            try:
                                is_mesh_comp = comp.is_a(unreal.SkeletalMeshComponent)
                            except:
                                pass
                        
                        if is_mesh_comp or hasattr(comp, 'skeletal_mesh'):
                            components.append(comp)
                
                # Check found components for skeletal meshes
                for component in components:
                    if hasattr(component, 'skeletal_mesh'):
                        skeletal_mesh = component.skeletal_mesh
                        if skeletal_mesh:
                            return skeletal_mesh
                    
                    if hasattr(component, 'get_editor_property'):
                        try:
                            skeletal_mesh = component.get_editor_property('skeletal_mesh')
                            if skeletal_mesh:
                                return skeletal_mesh
                        except:
                            pass
        except:
            pass
                
        return None
    
    def get_skeletal_mesh_materials(self, skeletal_mesh):
        """Get materials from skeletal mesh and match with CSV entries"""
        material_slots = []
        
        # Get materials directly from the skeletal mesh
        skeletal_materials = []
        if hasattr(skeletal_mesh, "materials"):
            skeletal_materials = skeletal_mesh.materials
        
        # Create lookup dict for CSV material mappings
        csv_slot_mappings = {}
        for i, mapping in enumerate(self.material_mapping):
            slot_name = mapping.get('material_slot', '')
            if slot_name:
                csv_slot_mappings[slot_name.strip().lower()] = {
                    'csv_index': i,
                    'material_instance': mapping.get('material_instance', ''),
                    'material_instance_path': mapping.get('material_instance_path', ''),
                    'parent_material': mapping.get('parent_material', ''),
                    'parent_material_path': mapping.get('parent_material_path', '')
                }
        
        # Process each material from the skeletal mesh
        for i, mat in enumerate(skeletal_materials):
            # Get the slot name
            slot_name = "Unknown"
            if hasattr(mat, 'material_slot_name'):
                try:
                    slot_name = str(mat.material_slot_name)
                except:
                    slot_name = "Unknown"
            
            # Get the material name
            material_name = "None"
            material = None
            
            if hasattr(mat, 'material_interface') and mat.material_interface:
                material = mat.material_interface
                try:
                    material_name = str(material.get_name())
                except:
                    material_name = "None"
            elif hasattr(mat, 'get_name'):
                try:
                    material_name = str(mat.get_name())
                except:
                    material_name = "None"
            
            # Create slot info dictionary
            slot_info = {
                'index': i,
                'name': slot_name,
                'original_name': slot_name,
                'material': material,
                'material_name': material_name,
                'material_interface': mat.material_interface if hasattr(mat, 'material_interface') else None,
                'csv_index': -1  # Will be set if matched with CSV
            }
            
            # Match with CSV entries
            normalized_name = str(slot_name).strip().lower()
            if normalized_name in csv_slot_mappings:
                csv_info = csv_slot_mappings[normalized_name]
                slot_info.update({
                    'csv_index': csv_info['csv_index'],
                    'material_instance': csv_info['material_instance'],
                    'material_instance_path': csv_info['material_instance_path'],
                    'parent_material': csv_info['parent_material'],
                    'parent_material_path': csv_info['parent_material_path']
                })
            
            material_slots.append(slot_info)
        
        return material_slots

    def find_livery_materials(self):
        """Find available livery materials in the materials folder"""
        self.livery_materials = []
        
        if not self.skeletal_mesh:
            return
        
        # Determine material instances directory
        mesh_path = self.skeletal_mesh.get_path_name()
        self.material_instances_dir = self.get_material_instances_dir(mesh_path)
        
        # Get all assets in the directory
        if unreal.EditorAssetLibrary.does_directory_exist(self.material_instances_dir):
            assets = unreal.EditorAssetLibrary.list_assets(self.material_instances_dir, recursive=True)
            
            # Filter for livery materials
            for asset_path in assets:
                asset_name = os.path.basename(asset_path).split('.')[0]
                
                # Check if it's a livery material (contains "mat_livery" but not "mat_livery_lod")
                if "mat_livery" in asset_name.lower() and "mat_livery_lod" not in asset_name.lower():
                    # Extract the number from the material name
                    match = re.search(r'(\d+)', asset_name)
                    if match:
                        livery_number = match.group(1)
                        self.livery_materials.append({
                            'name': asset_name,
                            'path': asset_path,
                            'number': livery_number
                        })
    
    def get_material_instances_dir(self, mesh_path):
        """Determine the material_instances directory from mesh path"""
        # Split the path
        path_parts = mesh_path.split('/')
        
        # Remove the last two parts (filename and 'skeletal_meshes')
        base_path = '/'.join(path_parts[:-2])
        
        # Construct the material_instances path
        material_instances_dir = f"{base_path}/material_instances"
        
        # Verify the path exists
        if not unreal.EditorAssetLibrary.does_directory_exist(material_instances_dir):
            # Fallback: create the directory if it doesn't exist
            try:
                unreal.EditorAssetLibrary.make_directory(material_instances_dir)
                return material_instances_dir
            except:
                # If directory creation fails, try alternate paths
                # Try with a Materials directory
                materials_dir = f"{base_path}/Materials"
                if unreal.EditorAssetLibrary.does_directory_exist(materials_dir):
                    return materials_dir
                
                # Try one more level up
                parent_path = '/'.join(path_parts[:-3])
                alt_dir = f"{parent_path}/material_instances"
                if unreal.EditorAssetLibrary.does_directory_exist(alt_dir):
                    return alt_dir
                
                # Last resort - try to find material_instances under the cat folder
                cat_idx = -1
                for i, part in enumerate(path_parts):
                    if part.startswith('cat'):
                        cat_idx = i
                        break
                        
                if cat_idx > 0:
                    # Reconstruct the path up to cat folder
                    cat_path = '/'.join(path_parts[:cat_idx+1])
                    
                    # Try to find material_instances folder
                    assets = unreal.EditorAssetLibrary.list_assets(cat_path, recursive=True)
                    for asset in assets:
                        if "material_instances" in asset:
                            material_dir = os.path.dirname(asset)
                            if unreal.EditorAssetLibrary.does_directory_exist(material_dir):
                                return material_dir
                
                # If all else fails, use the default content dir
                return "/Game/Materials"
        
        return material_instances_dir
    
    def populate_livery_dropdown(self):
        """Populate the livery dropdown with available livery materials"""
        self.livery_combo.clear()
        self.livery_combo.addItem("Select Livery")
        
        # Sort by number
        sorted_liveries = sorted(self.livery_materials, key=lambda x: x['number'])
        
        for livery in sorted_liveries:
            self.livery_combo.addItem(livery['name'])
    
    def on_livery_selected(self, index):
        """Handle livery selection from dropdown"""
        self.clear_variant_widgets()
        self.variant_combo.clear()
        self.variant_combo.addItem("Select Variant")
        
        if index <= 0:  # Skip "Select Livery" item
            self.variant_combo.setEnabled(False)
            return
        
        # Get selected livery
        livery_name = self.livery_combo.currentText()
        selected_livery = next((livery for livery in self.livery_materials 
                            if livery['name'] == livery_name), None)
        
        if not selected_livery:
            return
        
        # Extract livery number
        livery_number = selected_livery['number']
        variants = []
        
        # Check for special case variants based on chassis ID in mesh name
        if self.skeletal_mesh:
            chassis_id = self.extract_chassis_id(self.skeletal_mesh)
            
            if chassis_id and chassis_id in self.special_variant_mappings:
                if livery_number in self.special_variant_mappings[chassis_id]:
                    variants = self.special_variant_mappings[chassis_id][livery_number]
                    # Add a debug message to console (optional)
                    print(f"Using special variants for chassis {chassis_id}, livery {livery_number}: {variants}")
        
        # If no special variants were found, use the standard calculation
        if not variants:
            base_variant = ((int(livery_number) - 1) * 3) + 1
            variants = [f"{base_variant + i:03d}" for i in range(3)]
        
        # Add variants to dropdown
        for variant in variants:
            self.variant_combo.addItem(variant)
        
        self.variant_combo.setEnabled(True)
    
    def on_variant_selected(self, index):
        """Handle variant selection from dropdown"""
        self.clear_variant_widgets()
        
        if index <= 0:  # Skip "Select Variant" item
            self.id_combo.setEnabled(False)
            return
        
        # Enable ID selection
        self.id_combo.setEnabled(True)
        
        # If ID is already selected, update the preview
        if self.id_combo.currentIndex() > 0:
            self.on_id_selected(self.id_combo.currentIndex())
            
    def on_id_selected(self, index):
        """Handle ID selection from dropdown"""
        self.clear_variant_widgets()
        
        if index <= 0:  # Skip "Select ID" item
            return
        
        # Get selected livery, variant, and ID
        livery_name = self.livery_combo.currentText()
        variant_number = self.variant_combo.currentText()
        id_number = self.id_combo.currentText()
        
        # Create preview widgets
        self.update_material_preview(livery_name, variant_number, id_number)
    
    def clear_variant_widgets(self):
        """Clear existing material preview widgets"""
        for widget in self.variant_widgets:
            self.scroll_layout.removeWidget(widget)
            widget.deleteLater()
        self.variant_widgets = []
        
    def display_current_materials(self):
        """Display the current materials without any selection"""
        self.clear_variant_widgets()
        
        if not self.material_slots:
            return
                
        # Create header for current materials
        header = QLabel("Current Materials:")
        header.setProperty("boldLabel", True)
        self.scroll_layout.addWidget(header)
        self.variant_widgets.append(header)
        
        # Display all material slots in order
        for slot in self.material_slots:
            widget = self.create_current_material_widget(slot)
            self.scroll_layout.addWidget(widget)
            self.variant_widgets.append(widget)
    
    def create_current_material_widget(self, slot):
        """Create a widget showing current material for a slot"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)
        
        # Material slot info
        slot_name = slot['name']
        slot_index = slot['index']
        
        # Slot name label
        slot_label = QLabel(f"Slot: {slot_name}")
        slot_label.setFixedWidth(240)
        layout.addWidget(slot_label)
        
        # Display material name
        current_material_name = slot['material_name']
        if current_material_name == "None":
            current_material_name = "Empty"
            
        current_label = QLabel(f"Current: {current_material_name}")
        current_label.setFixedWidth(300)
        layout.addWidget(current_label)
        
        # Show CSV match status
        has_csv_match = slot['csv_index'] >= 0
        
        if not has_csv_match:
            # Use property-based styling
            current_label.setProperty("materialPreview", "unknown")
            current_label.style().unpolish(current_label)
            current_label.style().polish(current_label)
        
        # Store data in widget for later use
        setattr(widget, "slot_index", slot_index)
        setattr(widget, "slot_name", slot_name)
        
        # Store CSV information if available
        if has_csv_match:
            setattr(widget, "material_instance", slot['material_instance'])
            setattr(widget, "material_instance_path", slot['material_instance_path'])
            setattr(widget, "parent_material", slot['parent_material'])
            setattr(widget, "parent_material_path", slot['parent_material_path'])
        
        return widget
    
    def update_material_preview(self, livery_name, variant_number, id_number):
        """Update material preview based on selected livery, variant, and ID"""
        if not self.material_slots:
            return
        
        # Create widgets for all slots
        for slot in self.material_slots:
            # Only create material preview widgets for slots that have CSV mappings
            if slot['csv_index'] >= 0:
                widget = self.create_material_preview_widget(slot, livery_name, variant_number, id_number)
            else:
                widget = self.create_unknown_slot_widget(slot)
                
            self.scroll_layout.addWidget(widget)
            self.variant_widgets.append(widget)
    
    def create_material_preview_widget(self, slot, livery_name, variant_number, id_number):
        """Create a widget showing material preview for a slot"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)
        
        # Material slot info
        slot_name = slot['name']
        slot_index = slot['index']
        
        # Get material reference and path from slot
        parent_material = slot.get('parent_material', "")
        parent_material_path = slot.get('parent_material_path', "")
        material_instance_pattern = slot.get('material_instance', "")
        material_instance_path = slot.get('material_instance_path', "")
        
        # Extract the livery number from livery_name
        livery_number = ""
        match = re.search(r'(\d+)', livery_name)
        if match:
            livery_number = match.group(1)
            
        # Create target material name with replacements
        target_material_name = material_instance_pattern
        if target_material_name:
            # Apply replacements: # is for livery, $ is for variant, * is for ID
            target_material_name = target_material_name.replace("#", livery_number)
            target_material_name = target_material_name.replace("$", variant_number)
            target_material_name = target_material_name.replace("*", id_number)
        
        # Slot name label
        slot_label = QLabel(f"Slot: {slot_name}")
        slot_label.setFixedWidth(240)
        layout.addWidget(slot_label)
        
        # Current material name
        current_material_name = slot['material_name']
        if current_material_name == "None":
            current_material_name = "Empty"
            
        current_label = QLabel(f"Current: {current_material_name}")
        current_label.setFixedWidth(200)
        current_label.setProperty("materialPreview", "current")
        layout.addWidget(current_label)
        
        # Arrow indicator
        arrow_label = QLabel("→")
        arrow_label.setFixedWidth(20)
        arrow_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(arrow_label)
        
        # Target material label
        target_label = QLabel(f"Target: {target_material_name}")
        target_label.setProperty("materialPreview", "target")
        layout.addWidget(target_label)
        
        # Store data in widget for later use
        setattr(widget, "slot_index", slot_index)
        setattr(widget, "slot_name", slot_name)
        setattr(widget, "target_material_name", target_material_name)
        setattr(widget, "material_instance_path", material_instance_path)
        setattr(widget, "parent_material", parent_material)
        setattr(widget, "parent_material_path", parent_material_path)
        
        return widget
    
    def create_unknown_slot_widget(self, slot):
        """Create a widget for a slot without CSV mapping"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)
        
        # Slot info
        slot_name = slot['name']
        slot_index = slot['index']
        
        # Slot name label with red styling
        slot_label = QLabel(f"Slot: {slot_name}")
        slot_label.setFixedWidth(240)
        layout.addWidget(slot_label)
        
        # Current material label
        current_material_name = slot['material_name']
        if current_material_name == "None":
            current_material_name = "Empty"
            
        current_label = QLabel(f"Current: {current_material_name}")
        current_label.setProperty("materialPreview", "unknown")
        layout.addWidget(current_label)
        
        # Store data in widget for later use
        setattr(widget, "slot_index", slot_index)
        setattr(widget, "slot_name", slot_name)
        setattr(widget, "unknown", True)
        
        return widget

    def find_material_asset(self, target_material_name, custom_path=""):
        """Find a material asset by name in standard locations"""
        # Check in custom path first if provided
        potential_paths = []
        
        if custom_path and not custom_path.lower() == "default":
            potential_paths.append(f"{custom_path}/{target_material_name}.{target_material_name}")
        
        # Add standard locations
        potential_paths.extend([
            f"{self.material_instances_dir}/{target_material_name}.{target_material_name}",
            f"/Game/Materials/{target_material_name}.{target_material_name}",
            f"/Game/{target_material_name}.{target_material_name}"
        ])
        
        # Try to find and load the material asset
        for path in potential_paths:
            if unreal.EditorAssetLibrary.does_asset_exist(path):
                material_asset = unreal.EditorAssetLibrary.load_asset(path)
                if material_asset:
                    return material_asset, path
        
        return None, None
    
    def find_parent_material(self, parent_material, parent_material_path):
        """Find parent material using multiple strategies"""
        # Try different paths to find the parent material
        potential_paths = [
            parent_material_path,  # Direct path
            f"/Game/{parent_material_path}",  # With Game prefix
            f"/Game/Materials/{parent_material}",  # In standard materials folder
            parent_material if parent_material.startswith("/") else None  # If it's already a path
        ]
        
        # Try all potential paths
        for path in potential_paths:
            if path and unreal.EditorAssetLibrary.does_asset_exist(path):
                parent_material = unreal.EditorAssetLibrary.load_asset(path)
                if parent_material:
                    return parent_material
        
        # If still not found, search by name
        search_paths = ["/Game/Materials", "/Game", self.material_instances_dir]
        for search_path in search_paths:
            if unreal.EditorAssetLibrary.does_directory_exist(search_path):
                assets = unreal.EditorAssetLibrary.list_assets(search_path, recursive=True)
                for asset_path in assets:
                    asset_name = os.path.basename(asset_path).split('.')[0]
                    if asset_name == parent_material:
                        parent_material = unreal.EditorAssetLibrary.load_asset(asset_path)
                        if parent_material:
                            return parent_material
        
        return None
    
    def get_save_directory(self, custom_path):
        """Get the appropriate directory to save material instances based on the custom path"""
        if not custom_path or custom_path.lower() == "default":
            return self.material_instances_dir
        
        # Ensure custom path exists, create if it doesn't
        if not unreal.EditorAssetLibrary.does_directory_exist(custom_path):
            try:
                unreal.EditorAssetLibrary.make_directory(custom_path)
            except:
                # Fallback to default if directory creation fails
                return self.material_instances_dir
        
        return custom_path

    def assign_materials(self):
        """Assign materials to the skeletal mesh by modifying the materials array"""
        # Initial validation checks
        if not self.skeletal_mesh:
            QMessageBox.warning(self, "Warning", "No skeletal mesh selected")
            return
        
        if self.livery_combo.currentIndex() <= 0 or self.variant_combo.currentIndex() <= 0 or self.id_combo.currentIndex() <= 0:
            QMessageBox.warning(self, "Warning", "Please select livery, variant, and ID")
            return
        
        if not self.variant_widgets:
            QMessageBox.warning(self, "Warning", "No material assignments to apply")
            return
        
        # Initialize counters
        success_count = 0
        failure_count = 0
        skipped_count = 0
        created_count = 0
        missing_materials = []
        
        # Get selected values
        livery_name = self.livery_combo.currentText()
        variant_number = self.variant_combo.currentText()
        id_number = self.id_combo.currentText()
        
        # Extract the livery number from livery_name
        livery_number = ""
        match = re.search(r'(\d+)', livery_name)
        if match:
            livery_number = match.group(1)
        
        # Process variant widgets to gather material assignments
        materials_to_check = []
        
        for widget in self.variant_widgets:
            # Skip widgets without needed attributes or header widgets
            if (not hasattr(widget, 'slot_name') or 
                not hasattr(widget, 'target_material_name') or 
                hasattr(widget, 'unknown') and widget.unknown):
                continue
            
            materials_to_check.append({
                'slot_name': widget.slot_name,
                'slot_index': widget.slot_index if hasattr(widget, 'slot_index') else -1,
                'target_material_name': widget.target_material_name,
                'material_instance_path': widget.material_instance_path if hasattr(widget, 'material_instance_path') else '',
                'parent_material': widget.parent_material if hasattr(widget, 'parent_material') else '',
                'parent_material_path': widget.parent_material_path if hasattr(widget, 'parent_material_path') else ''
            })
        
        # Check for missing materials and build creation list
        materials_to_create = []
        
        for material_info in materials_to_check:
            target_material_name = material_info['target_material_name']
            material_instance_path = material_info['material_instance_path']
            parent_material = material_info['parent_material']
            parent_material_path = material_info['parent_material_path']
            
            # Get the appropriate save directory
            save_dir = self.get_save_directory(material_instance_path)
            
            # Check if material exists
            material_asset, _ = self.find_material_asset(target_material_name, material_instance_path)
            
            if not material_asset:
                if parent_material and parent_material_path:
                    # Material doesn't exist and we have parent info, add to creation list
                    target_asset_path = f"{save_dir}/{target_material_name}"
                    materials_to_create.append({
                        'target_material_name': target_material_name,
                        'save_dir': save_dir,
                        'parent_material': parent_material,
                        'parent_material_path': parent_material_path,
                        'target_asset_path': target_asset_path,
                        'slot_name': material_info['slot_name']
                    })
                else:
                    missing_materials.append(f"{target_material_name} (missing parent material info)")
        
        # Prompt user for creating missing materials
        if materials_to_create:
            # Create message with missing materials
            material_list = "\n".join([f"• {item['target_material_name']}" for item in materials_to_create[:10]])
            if len(materials_to_create) > 10:
                material_list += f"\n...and {len(materials_to_create) - 10} more"
            
            # Ask the user if they want to create the missing materials
            reply = QMessageBox.question(self, "Create Missing Materials", 
                                        f"The following materials are missing and need to be created:\n\n{material_list}\n\nDo you want to create them?",
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            
            # If the user clicks "No", cancel the operation
            if reply != QMessageBox.Yes:
                self.set_status("Material assignment canceled by user", "info")
                return
            
            # Create the missing materials
            for item in materials_to_create:
                target_material_name = item['target_material_name']
                save_dir = item['save_dir']
                parent_material_name = item['parent_material']
                parent_material_path = item['parent_material_path']
                target_asset_path = item['target_asset_path']
                
                # Find parent material
                parent_material_asset = self.find_parent_material(parent_material_name, parent_material_path)
                
                if parent_material_asset:
                    # Create material instance
                    factory = unreal.MaterialInstanceConstantFactoryNew()
                    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
                    new_material = asset_tools.create_asset(
                        target_material_name, 
                        save_dir, 
                        unreal.MaterialInstanceConstant, 
                        factory
                    )
                    
                    if new_material:
                        # Set the parent and save
                        new_material.set_editor_property('parent', parent_material_asset)
                        unreal.EditorAssetLibrary.save_asset(target_asset_path)
                        created_count += 1
                    else:
                        missing_materials.append(f"{target_material_name} (creation failed)")
                else:
                    missing_materials.append(f"{target_material_name} (parent not found: {parent_material_name})")
        
        # Now assign the materials
        # Get the existing material array from the skeletal mesh
        existing_materials = None
        if hasattr(self.skeletal_mesh, 'get_editor_property'):
            existing_materials = self.skeletal_mesh.get_editor_property('materials')
        elif hasattr(self.skeletal_mesh, 'materials'):
            existing_materials = self.skeletal_mesh.materials
        
        if not existing_materials:
            QMessageBox.warning(self, "Error", "Failed to get materials array from skeletal mesh")
            return
        
        # Create a dictionary to store materials that need to be changed
        materials_to_change = {}
        
        # Process the material assignments to find the materials to change
        for material_info in materials_to_check:
            slot_name = material_info['slot_name']
            target_material_name = material_info['target_material_name']
            material_instance_path = material_info['material_instance_path']
            
            # Find and load the material
            material_asset, _ = self.find_material_asset(target_material_name, material_instance_path)
            
            # If found, add to change dictionary
            if material_asset:
                materials_to_change[str(slot_name)] = material_asset
                success_count += 1
            else:
                missing_materials.append(f"{target_material_name} (not found)")
                failure_count += 1
        
        # Apply material changes if any were found
        if materials_to_change:
            # Create a new array of skeletal materials
            new_material_array = unreal.Array(unreal.SkeletalMaterial)
            
            # For each existing material, either keep it or replace it
            for material in existing_materials:
                # Create a new skeletal material
                new_sk_material = unreal.SkeletalMaterial()
                
                # Get properties from the existing material
                slot_name = material.get_editor_property("material_slot_name")
                material_interface = material.get_editor_property("material_interface")
                
                # If we have a replacement for this slot, use it
                if materials_to_change.get(str(slot_name)):
                    material_interface = materials_to_change[str(slot_name)]
                
                # Set properties on the new skeletal material
                new_sk_material.set_editor_property("material_slot_name", slot_name)
                new_sk_material.set_editor_property("material_interface", material_interface)
                
                # Add to the new array
                new_material_array.append(new_sk_material)
            
            # Set the new array on the skeletal mesh
            self.skeletal_mesh.set_editor_property("materials", new_material_array)
            
            # Mark the skeletal mesh as modified
            if hasattr(self.skeletal_mesh, 'modify'):
                self.skeletal_mesh.modify()
            
            # Save the skeletal mesh
            asset_path = self.skeletal_mesh.get_path_name()
            unreal.EditorAssetLibrary.save_loaded_asset(self.skeletal_mesh)
            unreal.EditorAssetLibrary.save_asset(asset_path)
        
        # Build status message
        status_message = ""
        
        if created_count > 0:
            status_message += f"• Created {created_count} material instance(s)\n"
        
        if success_count > 0:
            status_message += f"• Assigned {success_count} material(s) successfully\n"
        
        if skipped_count > 0:
            status_message += f"• Skipped {skipped_count} slot(s) without CSV mapping\n"
        
        if missing_materials:
            status_message += f"• Missing materials ({len(missing_materials)}):\n"
            # Limit to avoid overwhelming the message box
            for i, mat in enumerate(missing_materials[:5]):
                status_message += f"  - {mat}\n"
            if len(missing_materials) > 5:
                status_message += f"  - ... and {len(missing_materials) - 5} more\n"
                
        if failure_count > 0:
            status_message += f"• Failed to assign {failure_count} material(s)\n"
        
        # Show appropriate message based on results
        if (success_count > 0 or created_count > 0) and failure_count == 0:
            QMessageBox.information(self, "Success", status_message)
        elif (success_count > 0 or created_count > 0) and failure_count > 0:
            QMessageBox.warning(self, "Partial Success", status_message)
        elif success_count == 0 and created_count == 0 and failure_count == 0 and skipped_count > 0:
            QMessageBox.information(self, "No Changes", "No materials were assigned.")
        else:
            QMessageBox.critical(self, "Error", status_message)
        
        # Refresh to show the new materials
        self.select_skeletal_mesh()


# Main application entry point
try:
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
        font = QFont("Meiryo UI")
        font.setPointSize(10)
        app.setFont(font)
    
    widget = MaterialAssigner()
    widget.show()
    unreal.parent_external_window_to_slate(widget.winId())
except ImportError:
    sys.exit(1)