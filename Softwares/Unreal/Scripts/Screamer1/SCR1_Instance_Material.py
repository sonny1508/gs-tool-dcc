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

class MaterialInstanceCreator(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Instance Material Creator")
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        self.material_slot_widgets = []
        self.static_mesh = None
        self.material_library = []
        self.load_material_library()
        self.load_style()
        self.setup_ui()
    
    def load_material_library(self):
        """Load material data from CSV file"""
        csv_path = os.path.join(SCRIPT_DIR, "SCR1_Material_Library.csv")
        if not os.path.exists(csv_path):
            csv_path = os.path.join(PARENT_DIR, "SCR1_Material_Library.csv")
        
        if os.path.exists(csv_path):
            try:
                with open(csv_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    self.material_library = list(reader)
            except Exception as e:
                QMessageBox.warning(self, "Warning", f"Failed to load material library: {str(e)}")
        else:
            QMessageBox.warning(self, "Warning", "Material library CSV file not found")
    
    def load_style(self):
        """Load QSS style file"""
        style = ''
        for style_path in [os.path.join(dir, 'style.qss') for dir in [SCRIPT_DIR, PARENT_DIR]]:
            if os.path.exists(style_path):
                try:
                    with open(style_path, 'r') as f:
                        style = f.read()
                        break
                except Exception:
                    pass
                    
        if style:
            self.setStyleSheet(style)

    def setup_ui(self):
        # Create layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(main_layout)
        
        # Add header
        header_label = QLabel("Instance Material Creator")
        header_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        header_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header_label)
        
        # Add check button
        check_button = QPushButton("Check Material Slots")
        check_button.clicked.connect(self.check_material_slots)
        main_layout.addWidget(check_button)
        
        # Static mesh info section
        self.mesh_info_label = QLabel("No static mesh selected")
        self.mesh_info_label.setStyleSheet("font-weight: bold;")
        main_layout.addWidget(self.mesh_info_label)
        
        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line)
        
        # Material slots section header
        slots_header = QLabel("Material Slots")
        slots_header.setStyleSheet("font-weight: bold;")
        main_layout.addWidget(slots_header)
        
        # Scrollable area for material slots
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        main_layout.addWidget(scroll_area)
        
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(4, 4, 4, 4)
        self.scroll_layout.setSpacing(4)
        scroll_area.setWidget(self.scroll_content)
        
        # Create button
        create_button = QPushButton("Create Material Instances")
        create_button.clicked.connect(self.create_material_instances)
        main_layout.addWidget(create_button)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.status_label)
        
        # Set wider fixed size
        self.resize(720, 480)

    def check_material_slots(self):
        # Clear existing material slot widgets
        for widget in self.material_slot_widgets:
            self.scroll_layout.removeWidget(widget)
            widget.deleteLater()
        self.material_slot_widgets = []
        
        self.status_label.setText("")
        self.status_label.setStyleSheet("")
        
        # Get selected static mesh
        self.static_mesh = self.get_selected_static_mesh()
        
        if not self.static_mesh:
            self.mesh_info_label.setText("No static mesh selected")
            self.status_label.setText("Please select a static mesh in the Content Browser or Viewport")
            self.status_label.setStyleSheet("color: red;")
            return
                
        # Display static mesh info
        mesh_name = self.static_mesh.get_name()
        self.mesh_info_label.setText(f"Selected: {mesh_name}")
        
        # Get material slots
        material_slots = self.get_static_mesh_materials(self.static_mesh)
        
        if not material_slots:
            self.scroll_layout.addWidget(QLabel("No material slots found in this static mesh"))
            return
            
        # Create widgets for each material slot
        for i, material_slot in enumerate(material_slots):
            slot_widget = self.create_material_slot_widget(i, material_slot)
            self.scroll_layout.addWidget(slot_widget)
            self.material_slot_widgets.append(slot_widget)
            
        self.status_label.setText(f"Found {len(material_slots)} material slot(s)")
        self.status_label.setStyleSheet("color: green;")
            
    def get_selected_static_mesh(self):
        """Get the first selected static mesh in the editor"""
        # First, try to get selection from content browser
        editor_util = unreal.EditorUtilityLibrary()
        selected_assets = editor_util.get_selected_assets()
        
        for asset in selected_assets:
            # Check if it's a static mesh
            if hasattr(asset, 'is_a') and asset.is_a(unreal.StaticMesh):
                return asset
                
            # Alternative method to check static mesh
            if hasattr(asset, 'get_editor_property'):
                try:
                    for prop in ['lod_group', 'body_setup', 'static_materials']:
                        try:
                            asset.get_editor_property(prop)
                            return asset
                        except:
                            pass
                except:
                    continue
        
        # Try with viewport selection
        try:
            editor_level = unreal.EditorLevelLibrary()
            selected_actors = editor_level.get_selected_level_actors()
            
            for actor in selected_actors:
                # Check if it's a StaticMeshActor
                is_static_mesh_actor = False
                if hasattr(actor, 'get_class'):
                    actor_class = actor.get_class().get_name()
                    if 'StaticMeshActor' in actor_class:
                        is_static_mesh_actor = True
                
                if hasattr(actor, 'is_a') and not is_static_mesh_actor:
                    is_static_mesh_actor = actor.is_a(unreal.StaticMeshActor)
                
                if is_static_mesh_actor:
                    # Get static mesh from actor
                    if hasattr(actor, 'static_mesh_component'):
                        component = actor.static_mesh_component
                        if component and hasattr(component, 'static_mesh'):
                            return component.static_mesh
                    
                    if hasattr(actor, 'get_editor_property'):
                        component = actor.get_editor_property('static_mesh_component')
                        if component:
                            if hasattr(component, 'static_mesh'):
                                return component.static_mesh
                            
                            if hasattr(component, 'get_editor_property'):
                                return component.get_editor_property('static_mesh')
                
                # Look for any components with static meshes
                components = []
                
                if hasattr(actor, 'get_components_by_class'):
                    components.extend(actor.get_components_by_class(unreal.StaticMeshComponent))
                
                if hasattr(actor, 'get_components'):
                    all_components = actor.get_components()
                    for comp in all_components:
                        is_mesh_comp = False
                        if hasattr(comp, 'get_class'):
                            try:
                                comp_class = comp.get_class().get_name()
                                is_mesh_comp = 'StaticMeshComponent' in comp_class
                            except:
                                pass
                        
                        if hasattr(comp, 'is_a'):
                            try:
                                is_mesh_comp = comp.is_a(unreal.StaticMeshComponent)
                            except:
                                pass
                        
                        if is_mesh_comp or hasattr(comp, 'static_mesh'):
                            components.append(comp)
                
                for component in components:
                    if hasattr(component, 'static_mesh'):
                        static_mesh = component.static_mesh
                        if static_mesh:
                            return static_mesh
                    
                    if hasattr(component, 'get_editor_property'):
                        try:
                            static_mesh = component.get_editor_property('static_mesh')
                            if static_mesh:
                                return static_mesh
                        except:
                            pass
        except:
            pass
                
        return None

    def get_static_mesh_materials(self, static_mesh):
        """Get material slots from a static mesh"""
        material_slots = []
        
        try:
            # First try to get material slots directly from the static mesh
            material_slot_names = []
            original_slot_names = []
            
            # Method 1: Try to get material slot names directly
            if hasattr(static_mesh, "get_material_slot_names"):
                try:
                    original_slot_names = static_mesh.get_material_slot_names()
                    material_slot_names = list(original_slot_names)  # Make a copy to preserve originals
                except:
                    pass
                    
            # Method 2: Try to get them from static_materials
            if not material_slot_names and hasattr(static_mesh, "static_materials"):
                try:
                    static_materials = static_mesh.static_materials
                    if static_materials:
                        for mat in static_materials:
                            if hasattr(mat, 'material_slot_name'):
                                material_slot_names.append(mat.material_slot_name)
                            else:
                                material_slot_names.append("")
                        original_slot_names = list(material_slot_names)
                except:
                    pass
            
            # Method 3: Get from the static mesh component in a selected actor
            if not material_slot_names:
                editor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
                selected_actors = editor_subsystem.get_selected_level_actors()
                
                for actor in selected_actors:
                    # Try to get the static mesh component
                    if hasattr(actor, "static_mesh_component"):
                        component = actor.static_mesh_component
                        if component and hasattr(component, "static_mesh"):
                            component_static_mesh = component.static_mesh
                            if component_static_mesh == static_mesh:
                                # Try to get material slot names from the component
                                if hasattr(component, "get_material_slot_names"):
                                    try:
                                        original_slot_names = component.get_material_slot_names()
                                        material_slot_names = list(original_slot_names)
                                    except:
                                        pass
                                break
            
            # Get number of materials directly from static mesh
            num_materials = 0
            if hasattr(static_mesh, "get_num_materials"):
                num_materials = static_mesh.get_num_materials()
            elif hasattr(static_mesh, "get_materials_num"):
                num_materials = static_mesh.get_materials_num()
            elif hasattr(static_mesh, "static_materials"):
                num_materials = len(static_mesh.static_materials)
            else:
                # Last resort - try to get number of sections
                if hasattr(static_mesh, "get_num_sections"):
                    try:
                        num_materials = static_mesh.get_num_sections(0)  # LOD 0
                    except:
                        pass
            
            # Make sure we have enough slot names for all materials
            while len(material_slot_names) < num_materials:
                material_slot_names.append(f"Material_{len(material_slot_names)}")
            
            # Process each material slot
            for i in range(num_materials):
                # Get material at this slot
                material = None
                try:
                    if hasattr(static_mesh, "get_material"):
                        material = static_mesh.get_material(i)
                except:
                    pass
                
                # Get the slot name
                slot_name = f"Material_{i}"
                if i < len(material_slot_names) and material_slot_names[i]:
                    slot_name = str(material_slot_names[i])
                
                # Get material name without modifying it
                material_name = "None"
                if material:
                    try:
                        material_name = material.get_name()
                    except:
                        pass
                
                # Store slot info
                material_slots.append({
                    'index': i,
                    'name': slot_name,
                    'original_name': original_slot_names[i] if i < len(original_slot_names) else slot_name,
                    'material': material,
                    'material_name': material_name
                })
            
            # If we found no material slots, return a default one
            if not material_slots:
                material_slots.append({
                    'index': 0,
                    'name': "Material_0",
                    'original_name': "Material_0",
                    'material': None,
                    'material_name': "None"
                })
            
            return material_slots
        
        except Exception as e:
            # For debugging, uncomment this line
            # QMessageBox.warning(self, "Error", f"Error getting material slots: {str(e)}")
            
            # Return at least one default slot
            return [{
                'index': 0,
                'name': "Material_0",
                'original_name': "Material_0",
                'material': None,
                'material_name': "None"
            }]

    def on_material_selected(self, combo_box, index):
        """Handle material selection from the dropdown"""
        if index <= 0:  # Skip the "Select Material" item
            # Reset to default style
            combo_box.setStyleSheet("""
                QComboBox {
                    background-color: #333333;
                    color: #DDDDDD;
                    border: 1px solid #555555;
                    border-radius: 3px;
                    padding: 2px 8px;
                }
                QComboBox:focus {
                    border: 1px solid #666666;
                    outline: none;
                }
                QComboBox::drop-down {
                    subcontrol-origin: padding;
                    subcontrol-position: right;
                    width: 20px;
                    border-left: 1px solid #555555;
                }
                QComboBox QAbstractItemView {
                    background-color: #333333;
                    color: #DDDDDD;
                    selection-background-color: #444444;
                    selection-color: #FFFFFF;
                }
            """)
            return
            
        try:
            # Get the parent widget
            parent_widget = combo_box.parent()
            
            # Get the material info from the library
            material_info = self.material_library[index - 1]  # -1 because index 0 is "Select Material"
            material_name = material_info.get('name', '')
            material_path = material_info.get('directory', '')
            
            # Ensure the path has the proper UE format
            if not material_path.startswith('/Game/'):
                material_path = f"/Game/{material_path}"
            
            # Create the full asset path
            full_path = f"{material_path}/{material_name}"
            if not full_path.endswith('.{0}'.format(material_name)):
                full_path = f"{full_path}.{material_name}"
            
            # Load the material asset
            material = unreal.EditorAssetLibrary.load_asset(full_path)
            
            if material:
                # Store the material reference in the parent widget
                setattr(parent_widget, "material", material)
                
                # Update the display with success style while preserving dropdown styling
                combo_box.setStyleSheet("""
                    QComboBox {
                        background-color: #386e36;
                        color: #FFFFFF;
                        border: 1px solid #555555;
                        border-radius: 3px;
                        padding: 2px 8px;
                    }
                    QComboBox:focus {
                        border: 1px solid #666666;
                        outline: none;
                    }
                    QComboBox::drop-down {
                        subcontrol-origin: padding;
                        subcontrol-position: right;
                        width: 20px;
                        border-left: 1px solid #555555;
                    }
                    QComboBox QAbstractItemView {
                        background-color: #333333;
                        color: #DDDDDD;
                        selection-background-color: #444444;
                        selection-color: #FFFFFF;
                    }
                """)
            else:
                # Update with error style while preserving dropdown styling
                combo_box.setStyleSheet("""
                    QComboBox {
                        background-color: #8e3636;
                        color: #FFFFFF;
                        border: 1px solid #555555;
                        border-radius: 3px;
                        padding: 2px 8px;
                    }
                    QComboBox:focus {
                        border: 1px solid #666666;
                        outline: none;
                    }
                    QComboBox::drop-down {
                        subcontrol-origin: padding;
                        subcontrol-position: right;
                        width: 20px;
                        border-left: 1px solid #555555;
                    }
                    QComboBox QAbstractItemView {
                        background-color: #333333;
                        color: #DDDDDD;
                        selection-background-color: #444444;
                        selection-color: #FFFFFF;
                    }
                """)
                setattr(parent_widget, "material", None)
        except Exception as e:
            # Update with error style while preserving dropdown styling
            combo_box.setStyleSheet("""
                QComboBox {
                    background-color: #8e3636;
                    color: #FFFFFF;
                    border: 1px solid #555555;
                    border-radius: 3px;
                    padding: 2px 8px;
                }
                QComboBox:focus {
                    border: 1px solid #666666;
                    outline: none;
                }
                QComboBox::drop-down {
                    subcontrol-origin: padding;
                    subcontrol-position: right;
                    width: 20px;
                    border-left: 1px solid #555555;
                }
                QComboBox QAbstractItemView {
                    background-color: #333333;
                    color: #DDDDDD;
                    selection-background-color: #444444;
                    selection-color: #FFFFFF;
                }
            """)
            setattr(parent_widget, "material", None)
            QMessageBox.warning(self, "Warning", f"Error loading material: {str(e)}")

    def create_material_slot_widget(self, index, material_slot):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)  # Very small margins
        
        # Material slot index and name
        slot_name = material_slot['name']
        
        # Create a simple label showing just the slot name
        name_label = QLabel(f"Slot: {slot_name}")
        name_label.setFixedWidth(240)  # Fixed width for uniformity
        layout.addWidget(name_label)
        
        # MI name input
        mi_name_label = QLabel("MI Name:")
        mi_name_label.setFixedWidth(60)  # Make it compact
        layout.addWidget(mi_name_label)
        
        # Suggest a name based on the static mesh and slot name
        mesh_name = self.static_mesh.get_name()
        suggested_name = f"{slot_name}"
        
        # Ensure the name is valid for UE assets (remove spaces, special chars)
        suggested_name = re.sub(r'[^a-zA-Z0-9_]', '_', suggested_name)
        if suggested_name[0].isdigit():
            suggested_name = f"M_{suggested_name}"
            
        mi_name_input = QLineEdit(suggested_name)
        layout.addWidget(mi_name_input)
        setattr(widget, "mi_name_input", mi_name_input)
        
        # Material dropdown
        material_combo = QComboBox()
        material_combo.addItem("Select Material")
        
        # Add materials from the library
        for material_info in self.material_library:
            material_name = material_info.get('name', '')
            material_combo.addItem(material_name)
        
        # Set minimum width for dropdown
        material_combo.setMinimumWidth(200)
        
        # Improve dropdown styling - remove orange focus box
        material_combo.setStyleSheet("""
            QComboBox {
                background-color: #333333;
                color: #DDDDDD;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 2px 8px;
            }
            QComboBox:focus {
                border: 1px solid #666666;
                outline: none;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: right;
                width: 20px;
                border-left: 1px solid #555555;
            }
            QComboBox QAbstractItemView {
                background-color: #333333;
                color: #DDDDDD;
                selection-background-color: #444444;
                selection-color: #FFFFFF;
            }
        """)
        
        # Connect dropdown selection change
        material_combo.currentIndexChanged.connect(
            lambda index: self.on_material_selected(material_combo, index)
        )
        
        layout.addWidget(material_combo)
        
        # Store important data
        setattr(widget, "material_combo", material_combo)
        setattr(widget, "slot_name", slot_name)
        setattr(widget, "slot_index", material_slot['index'])
        setattr(widget, "material", None)  # Store material reference here
        
        return widget

    def create_material_instances(self):
        # Initialize counters
        success_count = 0
        failure_count = 0
        skipped_count = 0
        
        # Check if we have a selected static mesh
        if not self.static_mesh:
            QMessageBox.warning(self, "Warning", "No static mesh selected")
            return
        
        # Count how many slots need to be processed
        slots_to_process = []
        for widget in self.material_slot_widgets:
            # Include all slots that have a master material assigned in the UI
            has_material = hasattr(widget, "material") and widget.material is not None
            
            if has_material:
                slots_to_process.append(widget)
        
        if not slots_to_process:
            QMessageBox.warning(self, "Warning", "No master materials assigned to any slot")
            return
            
        # Get the path of the static mesh to create MIs there
        target_path = "/Game/Materials/Instances"  # Default path
        
        try:
            # First try: Use the path of the static mesh
            try:
                asset_path = unreal.EditorUtilityLibrary.get_path_name(self.static_mesh)
                
                # Handle both formats: /Game/Path/AssetName and /Game/Path/AssetName.AssetName
                if "." in asset_path:
                    asset_path = asset_path.split(".")[0]
                
                mesh_dir = os.path.dirname(asset_path)
                if mesh_dir:
                    target_path = mesh_dir
            except:
                pass
                
            # Second try: Use content browser selected path
            if target_path == "/Game/Materials/Instances":
                try:
                    content_browser_paths = unreal.EditorUtilityLibrary.get_selected_folder_paths()
                    if content_browser_paths:
                        target_path = content_browser_paths[0]
                except:
                    pass
        except:
            pass
                
        # Create material instances
        for widget in slots_to_process:
            # Get data from widget
            slot_index = widget.slot_index
            slot_name = widget.slot_name
            mi_name = widget.mi_name_input.text().strip()
            parent_material = widget.material
            
            # Skip if no parent material
            if not parent_material:
                skipped_count += 1
                continue
            
            # Full asset path for the MI
            full_asset_path = f"{target_path}/{mi_name}"
            
            try:
                # Check if the MI already exists
                existing_mi = None
                try:
                    # Try to load the asset to see if it exists
                    if unreal.EditorAssetLibrary.does_asset_exist(full_asset_path):
                        existing_mi = unreal.EditorAssetLibrary.load_asset(full_asset_path)
                except:
                    pass
                
                mi = None
                
                # If MI already exists
                if existing_mi:
                    # Check if it's a material instance
                    is_mi = False
                    try:
                        is_mi = existing_mi.is_a(unreal.MaterialInstanceConstant)
                    except:
                        try:
                            class_name = existing_mi.get_class().get_name()
                            is_mi = "MaterialInstanceConstant" in class_name
                        except:
                            pass
                    
                    if is_mi:
                        # Use the existing MI
                        mi = existing_mi
                        
                        # Update parent if needed
                        current_parent = None
                        try:
                            current_parent = mi.get_editor_property("parent")
                        except:
                            pass
                        
                        if current_parent != parent_material:
                            mi.set_editor_property("parent", parent_material)
                            unreal.EditorAssetLibrary.save_asset(unreal.EditorUtilityLibrary.get_path_name(mi))
                    else:
                        # Create a new unique name to avoid conflicts
                        unique_name = f"{mi_name}_new"
                        
                        # Create new MI with unique name
                        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
                        mi_factory = unreal.MaterialInstanceConstantFactoryNew()
                        mi = asset_tools.create_asset(
                            unique_name,
                            target_path,
                            unreal.MaterialInstanceConstant,
                            mi_factory
                        )
                        
                        if not mi:
                            raise Exception(f"Failed to create material instance at {target_path}/{unique_name}")
                        
                        # Set the parent material
                        mi.set_editor_property("parent", parent_material)
                        unreal.EditorAssetLibrary.save_asset(unreal.EditorUtilityLibrary.get_path_name(mi))
                        
                else:
                    # Create new MI
                    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
                    mi_factory = unreal.MaterialInstanceConstantFactoryNew()
                    
                    # Ensure name is valid for UE assets
                    sanitized_name = mi_name
                    try:
                        sanitized_name = unreal.ObjectTools.get_base_name(mi_name)
                    except:
                        pass
                    
                    # Create the material instance
                    mi = asset_tools.create_asset(
                        sanitized_name,
                        target_path,
                        unreal.MaterialInstanceConstant,
                        mi_factory
                    )
                    
                    if not mi:
                        raise Exception(f"Failed to create material instance at {target_path}/{sanitized_name}")
                    
                    # Set the parent material
                    mi.set_editor_property("parent", parent_material)
                    unreal.EditorAssetLibrary.save_asset(unreal.EditorUtilityLibrary.get_path_name(mi))
                
                # Assign the material instance to the static mesh slot
                if mi:
                    self.static_mesh.set_material(slot_index, mi)
                    unreal.EditorAssetLibrary.save_asset(unreal.EditorUtilityLibrary.get_path_name(self.static_mesh))
                    success_count += 1
                
            except:
                failure_count += 1
        
        # Show final status
        status_message = ""
        
        if success_count > 0:
            status_message += f"• Created/Updated {success_count} material instance(s) successfully\n"
        
        if skipped_count > 0:
            status_message += f"• Skipped {skipped_count} slot(s) (no master material assigned)\n"
            
        if failure_count > 0:
            status_message += f"• Failed to create {failure_count} material instance(s)\n"
            status_message += "• Check the output log for details\n"
            
        if success_count > 0 and failure_count == 0:
            QMessageBox.information(self, "Success", status_message)
        elif success_count > 0 and failure_count > 0:
            QMessageBox.warning(self, "Partial Success", status_message)
        elif success_count == 0 and failure_count == 0 and skipped_count > 0:
            QMessageBox.information(self, "No Changes", "No material instances were created or updated.")
        else:
            QMessageBox.critical(self, "Error", 
                                f"Failed to create any material instances\n"
                                f"Check the output log for details")

        # Refresh to show the new materials
        self.check_material_slots()

try:
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
        font = QFont("Meiryo UI")
        font.setPointSize(10)
        app.setFont(font)
    
    widget = MaterialInstanceCreator()
    widget.show()
    unreal.parent_external_window_to_slate(widget.winId())
except ImportError:
    sys.exit(1)