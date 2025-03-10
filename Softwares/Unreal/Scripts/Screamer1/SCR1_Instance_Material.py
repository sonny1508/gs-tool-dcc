from __future__ import unicode_literals, print_function
import sys
import os
import csv
import re
import traceback

print("Starting Instance Material Creator script...")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
#sys.path.extend([SCRIPT_DIR, PARENT_DIR, os.path.join(PARENT_DIR, "ThirdParty")])
python_lib = "//192.168.1.10/Softwares/Pipeline/GSTools/Library/Python/Python39/Lib/site-packages"
if os.path.exists(python_lib):
    sys.path.append(python_lib)
    print(f"Added {python_lib} to path")
else:
    print(f"Warning: {python_lib} does not exist")

try:
    print("Importing PySide6 modules...")
    from PySide6.QtWidgets import *
    from PySide6.QtGui import *
    from PySide6.QtCore import Qt
    print("PySide6 modules imported successfully")
except Exception as e:
    print(f"Error importing PySide6 modules: {str(e)}")
    traceback.print_exc()
    raise

try:
    print("Importing Unreal modules...")
    import unreal
    print("Unreal modules imported successfully")
except Exception as e:
    print(f"Error importing Unreal modules: {str(e)}")
    traceback.print_exc()
    raise

# IMPORTANT: This class needs to be defined before MaterialInstanceCreator

class MaterialInstanceCreator(QWidget):
    def __init__(self):
        try:
            print("Initializing MaterialInstanceCreator widget...")
            super().__init__()
            self.setWindowTitle("Instance Material Creator")
            self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
            self.material_slot_widgets = []
            self.static_mesh = None
            self.load_style()  # Load the QSS style
            self.setup_ui()
            print("MaterialInstanceCreator widget initialized successfully")
        except Exception as e:
            print(f"Error initializing MaterialInstanceCreator: {str(e)}")
            traceback.print_exc()
    
    def load_style(self):
        """Load QSS style file"""
        style = ''
        for style_path in [os.path.join(dir, 'style.qss') for dir in [SCRIPT_DIR, PARENT_DIR]]:
            if os.path.exists(style_path):
                try:
                    print(f"Loading style from: {style_path}")
                    with open(style_path, 'r') as f:
                        style = f.read()
                        break
                except Exception as e:
                    print(f"Warning: Could not load style file: {e}")
                    
        if style:
            print("Style file loaded successfully")
            self.setStyleSheet(style)
        else:
            print("No style file found or loaded")

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
        self.scroll_layout.setContentsMargins(4, 4, 4, 4)  # Tighter margins
        self.scroll_layout.setSpacing(4)  # Less spacing
        scroll_area.setWidget(self.scroll_content)
        
        # Create button
        create_button = QPushButton("Create Material Instances")
        create_button.clicked.connect(self.create_material_instances)
        main_layout.addWidget(create_button)
        
        # Status label - Create this before using it in other methods
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.status_label)
        
        # Set wider fixed size
        self.resize(720, 480)

    def check_material_slots(self):
        try:
            print("Checking for material slots on selected static mesh...")
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
                print("No static mesh selected")
                return
                
            # Display static mesh info
            mesh_name = self.static_mesh.get_name()
            self.mesh_info_label.setText(f"Selected: {mesh_name}")
            print(f"Selected static mesh: {mesh_name}")
            
            # Get material slots
            try:
                material_slots = self.get_static_mesh_materials(self.static_mesh)
                
                if not material_slots:
                    self.scroll_layout.addWidget(QLabel("No material slots found in this static mesh"))
                    print("No material slots found")
                    return
                    
                print(f"Creating widgets for {len(material_slots)} material slots")
                # Create widgets for each material slot
                for i, material_slot in enumerate(material_slots):
                    slot_widget = self.create_material_slot_widget(i, material_slot)
                    self.scroll_layout.addWidget(slot_widget)
                    self.material_slot_widgets.append(slot_widget)
                    
                self.status_label.setText(f"Found {len(material_slots)} material slot(s)")
                self.status_label.setStyleSheet("color: green;")
                print(f"Created {len(material_slots)} material slot widgets")
                
            except Exception as e:
                error_msg = f"Error getting material slots: {str(e)}"
                self.status_label.setText(error_msg)
                self.status_label.setStyleSheet("color: red;")
                print(error_msg)
                traceback.print_exc()
        except Exception as e:
            print(f"Error in check_material_slots: {str(e)}")
            traceback.print_exc()
            
    def get_selected_static_mesh(self):
        """Get the first selected static mesh in the editor"""
        try:
            print("Getting selected static mesh...")
            
            # First, try to get selection from content browser
            try:
                editor_util = unreal.EditorUtilityLibrary()
                selected_assets = editor_util.get_selected_assets()
                
                print(f"Found {len(selected_assets)} selected assets in content browser")
                
                for asset in selected_assets:
                    try:
                        asset_name = asset.get_name()
                        print(f"Checking asset: {asset_name}")
                        
                        # Multiple ways to check if it's a static mesh
                        is_static_mesh = False
                        

                        
                        # Method 2: Check if has static mesh properties
                        if not is_static_mesh and hasattr(asset, 'get_editor_property'):
                            try:
                                # Try to access properties only a static mesh would have
                                for prop in ['lod_group', 'body_setup', 'static_materials']:
                                    try:
                                        asset.get_editor_property(prop)
                                        print(f"Asset has static mesh property '{prop}'")
                                        is_static_mesh = True
                                        break
                                    except:
                                        pass
                            except Exception as e:
                                print(f"Error checking static mesh properties: {str(e)}")
                        
                                
                        if is_static_mesh:
                            return asset
                    except Exception as e:
                        print(f"Error checking asset: {str(e)}")
            except Exception as e:
                print(f"Error getting content browser selection: {str(e)}")
                
            # If nothing found in content browser, try viewport selection
            try:
                # Try with EditorLevelLibrary first (more compatible across UE versions)
                editor_level = unreal.EditorLevelLibrary()
                selected_actors = editor_level.get_selected_level_actors()
                print(f"Found {len(selected_actors)} selected actors in level")
                
                for actor in selected_actors:
                    try:
                        # Print actor details for debugging
                        actor_name = actor.get_name()
                        print(f"Checking actor: {actor_name}")
                        actor_class = None
                        
                        # Get the actor's class name safely
                        if hasattr(actor, 'get_class'):
                            try:
                                actor_class = actor.get_class().get_name()
                                print(f"Actor class: {actor_class}")
                            except Exception as e:
                                print(f"Error getting actor class: {str(e)}")
                        
                        # Check if it's a StaticMeshActor by class name (most reliable method)
                        is_static_mesh_actor = False
                        if actor_class and 'StaticMeshActor' in actor_class:
                            is_static_mesh_actor = True
                            print(f"Identified as StaticMeshActor by class name")
                        
                        # Alternative check with is_a if available
                        if not is_static_mesh_actor and hasattr(actor, 'is_a'):
                            try:
                                is_static_mesh_actor = actor.is_a(unreal.StaticMeshActor)
                                print(f"is_a check result: {is_static_mesh_actor}")
                            except Exception as e:
                                print(f"Error using is_a: {str(e)}")
                        
                        if is_static_mesh_actor:
                            # Get static mesh from the actor - multiple methods
                            
                            # Method 1: Direct property access
                            if hasattr(actor, 'static_mesh_component'):
                                try:
                                    component = actor.static_mesh_component
                                    if component and hasattr(component, 'static_mesh'):
                                        static_mesh = component.static_mesh
                                        if static_mesh:
                                            print(f"Found static mesh via direct property: {static_mesh.get_name()}")
                                            return static_mesh
                                except Exception as e:
                                    print(f"Error accessing static_mesh_component: {str(e)}")
                            
                            # Method 2: Using get_editor_property
                            if hasattr(actor, 'get_editor_property'):
                                try:
                                    component = actor.get_editor_property('static_mesh_component')
                                    if component:
                                        if hasattr(component, 'static_mesh'):
                                            static_mesh = component.static_mesh
                                            if static_mesh:
                                                print(f"Found static mesh via component property: {static_mesh.get_name()}")
                                                return static_mesh
                                        
                                        if hasattr(component, 'get_editor_property'):
                                            static_mesh = component.get_editor_property('static_mesh')
                                            if static_mesh:
                                                print(f"Found static mesh via editor property: {static_mesh.get_name()}")
                                                return static_mesh
                                except Exception as e:
                                    print(f"Error with get_editor_property: {str(e)}")
                        
                        # If not identified as StaticMeshActor, look for any components with static meshes
                        components = []
                        
                        # Try with get_components_by_class if available
                        if hasattr(actor, 'get_components_by_class'):
                            try:
                                # Find all StaticMeshComponents
                                mesh_components = actor.get_components_by_class(unreal.StaticMeshComponent)
                                components.extend(mesh_components)
                                print(f"Found {len(mesh_components)} StaticMeshComponents via get_components_by_class")
                            except Exception as e:
                                print(f"Error with get_components_by_class: {str(e)}")
                        
                        # Try with get_components if available
                        if hasattr(actor, 'get_components'):
                            try:
                                all_components = actor.get_components()
                                print(f"Found {len(all_components)} total components")
                                for comp in all_components:
                                    try:
                                        # Check if component is a StaticMeshComponent
                                        is_mesh_comp = False
                                        comp_class = None
                                        
                                        # Get component class name
                                        if hasattr(comp, 'get_class'):
                                            try:
                                                comp_class = comp.get_class().get_name()
                                                is_mesh_comp = 'StaticMeshComponent' in comp_class
                                                print(f"Component class: {comp_class}, is mesh: {is_mesh_comp}")
                                            except:
                                                pass
                                        
                                        # Check with is_a if available
                                        if not is_mesh_comp and hasattr(comp, 'is_a'):
                                            try:
                                                is_mesh_comp = comp.is_a(unreal.StaticMeshComponent)
                                            except:
                                                pass
                                        
                                        # Check if component has static_mesh property
                                        if is_mesh_comp or hasattr(comp, 'static_mesh'):
                                            components.append(comp)
                                    except:
                                        pass  # Skip components that can't be checked
                                print(f"Found {len(components)} potential StaticMeshComponents")
                            except Exception as e:
                                print(f"Error with get_components: {str(e)}")
                        
                        # Check all found components for a static mesh
                        for component in components:
                            try:
                                # Direct property access
                                if hasattr(component, 'static_mesh'):
                                    static_mesh = component.static_mesh
                                    if static_mesh:
                                        print(f"Found static mesh from component: {static_mesh.get_name()}")
                                        return static_mesh
                                
                                # Get via editor property
                                if hasattr(component, 'get_editor_property'):
                                    try:
                                        static_mesh = component.get_editor_property('static_mesh')
                                        if static_mesh:
                                            print(f"Found static mesh via component editor property: {static_mesh.get_name()}")
                                            return static_mesh
                                    except:
                                        pass
                            except Exception as comp_e:
                                print(f"Error checking component for static mesh: {str(comp_e)}")
                                
                    except Exception as e:
                        print(f"Error checking actor: {str(e)}")
                        traceback.print_exc()
                        
            except Exception as e:
                print(f"Error getting level selection: {str(e)}")
                traceback.print_exc()
                
            # If we've tried everything and found nothing
            print("No static mesh found in selection")
            return None
        except Exception as e:
            print(f"Error getting selected static mesh: {str(e)}")
            traceback.print_exc()
            return None

    def get_static_mesh_materials(self, static_mesh):
        """Get material slots from a static mesh using the EditorActorSubsystem approach"""
        material_slots = []
        print(f"Getting material slots for static mesh: {static_mesh.get_name()}")
        
        try:
            # First try to find an actor in the scene using this static mesh
            editor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
            selected_actors = editor_subsystem.get_selected_level_actors()
            
            static_mesh_component = None
            component_found = False
            
            if selected_actors:
                print(f"Found {len(selected_actors)} selected actors")
                
                for actor in selected_actors:
                    actor_label = actor.get_actor_label() if hasattr(actor, 'get_actor_label') else actor.get_name()
                    print(f"\nExamining actor: {actor_label}")
                    
                    # Try to get the static mesh component
                    if hasattr(actor, "static_mesh_component"):
                        static_mesh_component = actor.static_mesh_component
                        print(f"Found static mesh component via direct access")
                        
                        # Check if this component uses our static mesh
                        if static_mesh_component and hasattr(static_mesh_component, "static_mesh"):
                            component_static_mesh = static_mesh_component.static_mesh
                            if component_static_mesh == static_mesh:
                                print(f"Component uses our target static mesh")
                                component_found = True
                                break
            
            if component_found and static_mesh_component:
                print(f"Using component from selected actor to get material slots")
                
                # Get material info
                num_materials = 0
                if hasattr(static_mesh_component, "get_num_materials"):
                    num_materials = static_mesh_component.get_num_materials()
                elif hasattr(static_mesh_component, "get_materials_num"):
                    num_materials = static_mesh_component.get_materials_num()
                else:
                    # Try to get it directly from component
                    materials = getattr(static_mesh_component, "materials", [])
                    num_materials = len(materials)
                
                print(f"Material slot count: {num_materials}")
                
                # Try different methods to get material slot names
                material_slot_names = []
                try:
                    if hasattr(static_mesh, "get_material_slot_names"):
                        material_slot_names = static_mesh.get_material_slot_names()
                    elif hasattr(static_mesh, "static_materials"):
                        material_slot_names = [mat.material_slot_name for mat in static_mesh.static_materials if hasattr(mat, 'material_slot_name')]
                except Exception as e:
                    print(f"Could not get material slot names: {e}")
                
                # Process each material slot
                for i in range(num_materials):
                    material = None
                    if hasattr(static_mesh_component, "get_material"):
                        material = static_mesh_component.get_material(i)
                    
                    # Get the slot name
                    slot_name = f"Material_{i}"
                    if i < len(material_slot_names) and material_slot_names[i]:
                        try:
                            slot_name = str(material_slot_names[i])
                            print(f"Original slot name: {slot_name}")
                        except Exception as e:
                            print(f"Error converting slot name: {e}")
                    
                    # Handle material naming
                    material_name = material.get_name() if material else "None"
                    if material:
                        try:
                            # Check if it's a Material Instance
                            if material.is_a(unreal.MaterialInstanceConstant):
                                # Rename only the Material Instance to match the slot name
                                try:
                                    material.set_name(slot_name)
                                    material_name = slot_name
                                except Exception as e:
                                    print(f"Could not rename Material Instance: {e}")
                                    # If renaming fails, keep the original name
                                    material_name = material.get_name()
                        except Exception as e:
                            print(f"Error processing material: {e}")
                    
                    print(f"Slot {i}: {slot_name} - Material: {material_name}")
                    
                    material_slots.append({
                        'index': i,
                        'name': slot_name,
                        'material': material,
                        'material_name': material_name
                    })
            
            # (Rest of the method remains the same)
            
            # If we found no material slots, return a default one
            if not material_slots:
                print("No material slots found, returning default slot")
                material_slots.append({
                    'index': 0,
                    'name': "Material_0",
                    'material': None,
                    'material_name': "None"
                })
            
            return material_slots
        
        except Exception as e:
            print(f"Error in get_static_mesh_materials: {e}")
            traceback.print_exc()
            
            # Return at least one default slot
            return [{
                'index': 0,
                'name': "Material_0",
                'material': None,
                'material_name': "None"
            }]

    def select_material_for_slot(self, material_display):
        """Select a material or material instance from the content browser"""
        try:
            print("Selecting material from content browser")
            
            # Get selected assets from content browser
            try:
                selected_assets = unreal.EditorUtilityLibrary.get_selected_assets()
                print(f"Content browser has {len(selected_assets)} selected assets")
                
                for asset in selected_assets:
                    try:
                        # Try different ways to check if it's a material or material instance
                        is_valid_material = False
                        material_name = "Unknown"
                        final_material = None
                        
                        # Print asset info for debugging
                        print(f"Checking asset: {asset.get_name()}, type: {type(asset)}")
                        if hasattr(asset, 'get_class'):
                            print(f"Class: {asset.get_class().get_name()}")
                        
                        # Method 1: Check if it's a base material or material instance
                        try:
                            if hasattr(asset, 'is_a'):
                                # Material or MaterialInstance
                                is_base_material = asset.is_a(unreal.Material)
                                is_material_instance = asset.is_a(unreal.MaterialInstanceConstant)
                                
                                # Accept both base materials and material instances
                                is_valid_material = is_base_material or is_material_instance
                                
                                print(f"Is base material: {is_base_material}, Is instance: {is_material_instance}")
                                
                                # If it's a material instance, try to get the parent base material
                                if is_material_instance:
                                    try:
                                        # Attempt to get parent material of instance
                                        if hasattr(asset, 'get_editor_property'):
                                            parent = asset.get_editor_property('parent')
                                            
                                            # If parent exists, but use the instance itself if needed
                                            final_material = parent if parent else asset
                                            final_material = final_material if final_material.is_a(unreal.Material) else asset
                                            
                                            print(f"Using material: {final_material.get_name()}")
                                    except Exception as e:
                                        print(f"Error getting parent material: {str(e)}")
                                        final_material = asset  # Fallback to the instance itself
                                else:
                                    final_material = asset
                        except Exception as e:
                            print(f"Error checking is_a: {str(e)}")
                        
                        # Method 2: class name (fallback)
                        if not is_valid_material:
                            try:
                                class_name = asset.get_class().get_name()
                                is_valid_material = class_name in ['Material', 'MaterialInstanceConstant']
                                print(f"Class name check: {class_name}, is valid: {is_valid_material}")
                                final_material = asset
                            except Exception as e:
                                print(f"Error checking class name: {str(e)}")
                        
                        if is_valid_material and final_material:
                            # Store the material and update display
                            material_name = final_material.get_name()
                            print(f"Selected material: {material_name}")
                            
                            # Store the material reference in the parent widget
                            parent_widget = material_display.parent()
                            setattr(parent_widget, "material", final_material)
                            
                            # Update the display
                            material_display.setText(material_name)
                            material_display.setStyleSheet("background-color: #c8f7c5;")  # Light green
                            return True
                    except Exception as e:
                        print(f"Error checking asset: {str(e)}")
                
                # If we get here, no valid material was found
                material_display.setText("No material selected")
                material_display.setStyleSheet("background-color: #ffcccc;")  # Light red
                
                return False
            except Exception as e:
                print(f"Error getting selection from content browser: {str(e)}")
                return False
                
        except Exception as e:
            print(f"Error in select_material_for_slot: {str(e)}")
            traceback.print_exc()
            return False

    def create_material_slot_widget(self, index, material_slot):
        try:
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
            
            # Material selection
            select_button = QPushButton("Select Material")
            select_button.setFixedWidth(100)  # Make it compact
            layout.addWidget(select_button)
            
            # Material display textbox
            material_display = QLineEdit("No material selected")
            material_display.setReadOnly(True)
            layout.addWidget(material_display)
            
            # Connect the button to material selection
            select_button.clicked.connect(lambda: self.select_material_for_slot(material_display))
            
            # Store important data
            setattr(widget, "material_display", material_display)  # Instead of drop_area
            setattr(widget, "slot_name", slot_name)
            setattr(widget, "slot_index", material_slot['index'])
            setattr(widget, "material", None)  # Store material reference here
            
            return widget
        except Exception as e:
            print(f"Error creating material slot widget: {str(e)}")
            traceback.print_exc()
            # Return a basic widget in case of error
            error_widget = QWidget()
            error_layout = QHBoxLayout(error_widget)
            error_layout.addWidget(QLabel(f"Error for slot {index}"))
            return error_widget

    def create_material_instances(self):
        # Initialize counters at the start of the function
        success_count = 0
        failure_count = 0
        skipped_count = 0
        
        print("Starting create_material_instances")
        # Check if we have a selected static mesh
        if not self.static_mesh:
            QMessageBox.warning(self, "Warning", "No static mesh selected")
            print("No static mesh selected")
            return
        
        print(f"Processing static mesh: {self.static_mesh.get_name()}")
        
        # Count how many slots need to be processed
        slots_to_process = []
        for widget in self.material_slot_widgets:
            # Include all slots that have a master material assigned in the UI
            has_material = hasattr(widget, "material") and widget.material is not None
            print(f"Slot {widget.slot_name}: Has material: {has_material}")
            
            if has_material:
                slots_to_process.append(widget)
        
        if not slots_to_process:
            QMessageBox.warning(self, "Warning", "No master materials assigned to any slot")
            print("No master materials assigned")
            return
            
        print(f"Found {len(slots_to_process)} slots to process")
            
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
                    print(f"Using static mesh path: {target_path}")
            except Exception as e:
                print(f"Error getting static mesh path: {str(e)}")
                
            # Second try: Use content browser selected path
            if target_path == "/Game/Materials/Instances":
                try:
                    content_browser_paths = unreal.EditorUtilityLibrary.get_selected_folder_paths()
                    if content_browser_paths:
                        target_path = content_browser_paths[0]
                        print(f"Using selected content browser path: {target_path}")
                    else:
                        print(f"No content browser path selected, using default: {target_path}")
                except Exception as e:
                    print(f"Error getting content browser paths: {str(e)}")
                    print(f"Using default path: {target_path}")
        except Exception as e:
            print(f"Error determining target path: {str(e)}")
            print(f"Using default path: {target_path}")
                
        # Create material instances
        for widget in slots_to_process:
            # Get data from widget
            slot_index = widget.slot_index
            slot_name = widget.slot_name
            mi_name = widget.mi_name_input.text().strip()
            parent_material = widget.material  # Now getting from widget.material instead of drop_area
            
            print(f"Processing slot {slot_index}: {slot_name}, MI name: {mi_name}")
            
            # Skip if no parent material
            if not parent_material:
                skipped_count += 1
                print(f"Skipping slot {slot_name}: No master material assigned")
                continue
            
            # Full asset path for the MI
            full_asset_path = f"{target_path}/{mi_name}"
            print(f"Target path for MI: {full_asset_path}")
            
            try:
                # Check if the MI already exists
                existing_mi = None
                try:
                    # Try to load the asset to see if it exists
                    if unreal.EditorAssetLibrary.does_asset_exist(full_asset_path):
                        print(f"Asset exists at {full_asset_path}")
                        existing_mi = unreal.EditorAssetLibrary.load_asset(full_asset_path)
                        print(f"Loaded existing asset: {existing_mi.get_name()}")
                except Exception as e:
                    print(f"Error checking if asset exists: {str(e)}")
                
                mi = None
                
                # If MI already exists
                if existing_mi:
                    # Check if it's a material instance
                    is_mi = False
                    try:
                        is_mi = existing_mi.is_a(unreal.MaterialInstanceConstant)
                        print(f"Existing asset is an MI: {is_mi}")
                    except Exception as e:
                        print(f"Error checking if existing asset is an MI: {str(e)}")
                        try:
                            class_name = existing_mi.get_class().get_name()
                            is_mi = "MaterialInstanceConstant" in class_name
                            print(f"Checked class name instead: {class_name}, is MI: {is_mi}")
                        except Exception as e2:
                            print(f"Error getting class name: {str(e2)}")
                    
                    if is_mi:
                        # Use the existing MI
                        mi = existing_mi
                        print(f"Using existing Material Instance: {mi_name}")
                        
                        # Update parent if needed
                        current_parent = None
                        try:
                            current_parent = mi.get_editor_property("parent")
                            print(f"Current parent: {current_parent.get_name() if current_parent else 'None'}")
                        except Exception as e:
                            print(f"Error getting current parent: {str(e)}")
                        
                        if current_parent != parent_material:
                            print(f"Updating parent to {parent_material.get_name()}")
                            mi.set_editor_property("parent", parent_material)
                            unreal.EditorAssetLibrary.save_asset(unreal.EditorUtilityLibrary.get_path_name(mi))
                            print(f"Updated parent of existing MI: {mi_name}")
                    else:
                        # Create a new unique name to avoid conflicts
                        unique_name = f"{mi_name}_new"
                        print(f"Asset exists but is not an MI, creating with new name: {unique_name}")
                        
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
                        
                        print(f"Created new MI: {unique_name}")
                        
                        # Set the parent material
                        mi.set_editor_property("parent", parent_material)
                        unreal.EditorAssetLibrary.save_asset(unreal.EditorUtilityLibrary.get_path_name(mi))
                        print(f"Set parent material to {parent_material.get_name()}")
                        
                else:
                    # Create new MI
                    print(f"No existing MI found, creating new one: {mi_name}")
                    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
                    mi_factory = unreal.MaterialInstanceConstantFactoryNew()
                    
                    # Ensure name is valid for UE assets
                    sanitized_name = mi_name
                    try:
                        sanitized_name = unreal.ObjectTools.get_base_name(mi_name)
                        print(f"Sanitized name: {sanitized_name}")
                    except Exception as e:
                        print(f"Error sanitizing name: {str(e)}")
                    
                    # Create the material instance
                    mi = asset_tools.create_asset(
                        sanitized_name,
                        target_path,
                        unreal.MaterialInstanceConstant,
                        mi_factory
                    )
                    
                    if not mi:
                        raise Exception(f"Failed to create material instance at {target_path}/{sanitized_name}")
                    
                    print(f"Created new MI: {sanitized_name}")
                    
                    # Set the parent material
                    mi.set_editor_property("parent", parent_material)
                    unreal.EditorAssetLibrary.save_asset(unreal.EditorUtilityLibrary.get_path_name(mi))
                    print(f"Set parent material to {parent_material.get_name()}")
                
                # Assign the material instance to the static mesh slot
                if mi:
                    print(f"Assigning MI to static mesh slot {slot_index}")
                    self.static_mesh.set_material(slot_index, mi)
                    unreal.EditorAssetLibrary.save_asset(unreal.EditorUtilityLibrary.get_path_name(self.static_mesh))
                    print(f"Applied Material Instance to slot {slot_name}")
                    success_count += 1
                
            except Exception as e:
                error_msg = f"Failed to create/assign material instance for slot {slot_name}: {str(e)}"
                print(error_msg)
                traceback.print_exc()
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
    print("This tool must be run within Unreal Engine.")
    sys.exit(1)