from __future__ import unicode_literals, print_function
import sys
import os
import re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
python_lib = "//192.168.1.10/Pipeline/GSTools/Library/Python/Python39/Lib/site-packages"
if os.path.exists(python_lib):
    sys.path.append(python_lib)

from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import Qt, QSize
import unreal


class DynamicsToggle(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dynamics Toggle")
        self.setWindowFlags(Qt.Window)
        self.skeletal_mesh = None
        self.material_slots = []
        
        # Material slots to modify - defined by developer
        self.dynamics_config = {
            "DynamicDirt": {
                "display_name": "Dynamic Dirt",
                "parameters": {
                    "toggle_param": "UniformDirt_Enabled",
                    "values_param": "UniformDirtLevels"
                },
                "material_slots": ["mat_livery", "mat_mechanics", "mat_glass", "mat_innerglass"]
            }
            # Additional dynamics sections can be added here
        }
        
        self.load_style()
        self.setup_ui()
        self.resize(500, 400)
    
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
        """Setup the user interface"""
        # Create main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(main_layout)
        
        # Add header
        header_label = QLabel("MGP25 Dynamics Toggle")
        header_label.setProperty("headerLabel", True)
        header_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header_label)
        
        # Add Select Skeletal Mesh button
        select_button = QPushButton("Select Skeletal Mesh")
        select_button.clicked.connect(self.select_skeletal_mesh)
        main_layout.addWidget(select_button)
        
        # Mesh info label
        self.mesh_info_label = QLabel("No skeletal mesh selected")
        self.mesh_info_label.setProperty("boldLabel", True)
        main_layout.addWidget(self.mesh_info_label)
        
        # Separator
        main_layout.addWidget(self.create_separator())
        
        # Create dynamics sections
        self.dynamics_groups = {}
        
        # Create collapsible section for Dynamic Dirt
        dirt_config = self.dynamics_config["DynamicDirt"]
        self.create_dynamics_section(main_layout, "DynamicDirt", dirt_config)
        
        # Add spacer
        main_layout.addStretch()
        
        # Separator
        main_layout.addWidget(self.create_separator())
        
        # Toggle button
        self.toggle_button = QPushButton("Toggle Dynamics")
        self.toggle_button.clicked.connect(self.toggle_dynamics)
        self.toggle_button.setEnabled(False)  # Disabled until a mesh is selected
        main_layout.addWidget(self.toggle_button)
        
        # Reset to Default button
        self.reset_button = QPushButton("Reset to Default")
        self.reset_button.clicked.connect(self.reset_dynamics_to_default)
        self.reset_button.setEnabled(False)  # Disabled until a mesh is selected
        main_layout.addWidget(self.reset_button)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.status_label)
    
    def create_dynamics_section(self, parent_layout, dynamics_key, config):
        """Create a collapsible section for a dynamics type"""
        # Create standard group box (not collapsible)
        group_box = QGroupBox(config["display_name"])
        
        # Create layout for group contents
        group_layout = QVBoxLayout(group_box)
        
        # Container for material slot checkboxes
        slots_container = QWidget()
        slots_layout = QVBoxLayout(slots_container)
        slots_layout.setContentsMargins(15, 0, 0, 0)  # Add indentation
        group_layout.addWidget(slots_container)
        
        # Store references
        self.dynamics_groups[dynamics_key] = {
            "group_box": group_box,
            "slots_container": slots_container,
            "slots_layout": slots_layout,
            "checkboxes": {}
        }
        
        # Add to parent layout
        parent_layout.addWidget(group_box)
        
        return group_box
    
    def create_separator(self):
        """Create a horizontal separator line"""
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        return line
    
    def select_skeletal_mesh(self):
        """Select and analyze the current skeletal mesh"""
        # Clear existing state
        self.material_slots = []
        self.clear_material_slot_checkboxes()
        
        # Get selected skeletal mesh
        self.skeletal_mesh = self.get_selected_skeletal_mesh()
        
        if not self.skeletal_mesh:
            self.mesh_info_label.setText("No skeletal mesh selected")
            self.set_status("Please select a skeletal mesh in the Content Browser or Viewport", "error")
            self.toggle_button.setEnabled(False)
            self.reset_button.setEnabled(False)
            return
        
        # Display skeletal mesh info
        self.mesh_info_label.setText(f"Selected: {self.skeletal_mesh.get_name()}")
        
        # Get material slots
        self.material_slots = self.get_skeletal_mesh_materials(self.skeletal_mesh)
        
        if not self.material_slots:
            self.set_status("No material slots found in this skeletal mesh", "error")
            self.toggle_button.setEnabled(False)
            self.reset_button.setEnabled(False)
            return
        
        # Update UI with relevant material slots
        self.update_material_slot_ui()
        
        # Enable toggle button
        self.toggle_button.setEnabled(True)
        self.reset_button.setEnabled(True)
        
        self.set_status(f"Found {len(self.material_slots)} material slot(s)", "success")
    
    def clear_material_slot_checkboxes(self):
        """Clear all material slot checkboxes"""
        for dynamic_key, dynamic_group in self.dynamics_groups.items():
            slots_layout = dynamic_group["slots_layout"]
            checkboxes = dynamic_group["checkboxes"]
            
            # Remove existing checkboxes
            for checkbox in checkboxes.values():
                slots_layout.removeWidget(checkbox)
                checkbox.deleteLater()
            
            # Reset checkboxes dictionary
            dynamic_group["checkboxes"] = {}
    
    def update_material_slot_ui(self):
        """Update UI with relevant material slots only"""
        # Clear existing checkboxes
        self.clear_material_slot_checkboxes()
        
        # For each dynamics type
        for dynamic_key, dynamic_group in self.dynamics_groups.items():
            slots_layout = dynamic_group["slots_layout"]
            checkboxes = dynamic_group["checkboxes"]
            
            # Get configured material slots for this dynamic
            configured_slots = self.dynamics_config[dynamic_key]["material_slots"]
            
            # Create checkboxes only for the configured material slots
            for slot in self.material_slots:
                slot_name = slot['name']
                material_name = slot['material_name']
                
                # Only create checkbox if slot is in the configured list
                if slot_name in configured_slots:
                    # Create checkbox
                    checkbox = QCheckBox(f"{slot_name} ({material_name})")
                    checkbox.setChecked(True)  # Default to checked
                    
                    # Add to layout and store reference
                    slots_layout.addWidget(checkbox)
                    checkboxes[slot_name] = checkbox
            
            # If no matching slots were found, show a message
            if len(checkboxes) == 0:
                no_slots_label = QLabel("No matching material slots found")
                no_slots_label.setStyleSheet("color: gray; font-style: italic;")
                slots_layout.addWidget(no_slots_label)
    
    def select_all_slots(self, dynamic_key, checked=True):
        """Select all material slots for a dynamics type"""
        if dynamic_key in self.dynamics_groups:
            dynamic_group = self.dynamics_groups[dynamic_key]
            
            for checkbox in dynamic_group["checkboxes"].values():
                checkbox.setChecked(checked)
    
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
        """Get materials from skeletal mesh"""
        material_slots = []
        
        # Get materials directly from the skeletal mesh
        skeletal_materials = []
        if hasattr(skeletal_mesh, "materials"):
            skeletal_materials = skeletal_mesh.materials
        
        # Process each material from the skeletal mesh
        for i, mat in enumerate(skeletal_materials):
            # Get the slot name
            slot_name = "Unknown"
            if hasattr(mat, 'material_slot_name'):
                try:
                    slot_name = str(mat.material_slot_name)
                except:
                    slot_name = "Unknown"
            
            # Get the material name and object
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
                'material': material,
                'material_name': material_name,
                'material_interface': mat.material_interface if hasattr(mat, 'material_interface') else None
            }
            
            material_slots.append(slot_info)
        
        return material_slots
    
    def set_status(self, message, status_type=""):
        """Set status message with appropriate styling"""
        self.status_label.setText(message)
        self.status_label.setProperty("status", status_type)
        
        # Force style update
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)
    
    def toggle_dynamics(self):
        """Toggle dynamics on selected materials"""
        if not self.skeletal_mesh or not self.material_slots:
            QMessageBox.warning(self, "Warning", "No skeletal mesh selected")
            return
        
        # Process each dynamics type
        success_count = 0
        failure_count = 0
        
        for dynamic_key, dynamic_group in self.dynamics_groups.items():
            # Get checkboxes for this dynamic type
            checkboxes = dynamic_group["checkboxes"]
            
            # Get selected slots
            selected_slots = []
            for slot_name, checkbox in checkboxes.items():
                if checkbox.isChecked():
                    # Find the slot info
                    slot_info = next((slot for slot in self.material_slots if slot['name'] == slot_name), None)
                    if slot_info:
                        selected_slots.append(slot_info)
            
            # Skip if no slots selected for this dynamic
            if not selected_slots:
                continue
            
            # Get parameter names from config
            params = self.dynamics_config[dynamic_key]["parameters"]
            toggle_param = params.get("toggle_param", "")
            values_param = params.get("values_param", "")
            
            # Apply to each selected slot
            for slot in selected_slots:
                material = slot['material']
                slot_name = slot['name']
                
                if not material:
                    failure_count += 1
                    continue
                
                # Apply the toggle
                if self.toggle_material_parameter(material, toggle_param, values_param):
                    success_count += 1
                else:
                    failure_count += 1
        
        # After updating all materials, try to refresh the mesh and viewports
        try:
            # Try to update the skeletal mesh
            if hasattr(self.skeletal_mesh, 'post_edit_change'):
                self.skeletal_mesh.post_edit_change()
            
            # Try various editor library methods to refresh
            try:
                unreal.EditorLevelLibrary.redraw_all_viewports()
            except:
                pass
                
            # Try to update any selected actors
            try:
                editor_level = unreal.EditorLevelLibrary()
                actors = editor_level.get_selected_level_actors()
                
                for actor in actors:
                    try:
                        if hasattr(actor, 'skeletal_mesh_component'):
                            comp = actor.skeletal_mesh_component
                            if comp:
                                if hasattr(comp, 'recreate_render_state'):
                                    comp.recreate_render_state()
                                if hasattr(comp, 'update_materials'):
                                    comp.update_materials()
                    except:
                        pass
            except:
                pass
                
        except:
            pass
        
        # Show results
        message = ""
        if success_count > 0 and failure_count == 0:
            message = f"Successfully toggled dynamics for {success_count} material(s)"
            self.set_status(message, "success")
        elif success_count > 0 and failure_count > 0:
            message = f"Toggled dynamics for {success_count} material(s), {failure_count} failed"
            self.set_status(message, "warning")
        else:
            message = f"Failed to toggle dynamics for any materials"
            self.set_status(message, "error")
        
        # Show message box with details
        # if success_count > 0:
        #     QMessageBox.information(self, "Toggle Complete", message + "\n\nChanges have been applied but not saved. Use the Content Browser to save modifications." +
        #                            "\n\nIf changes are not visible in the viewport, try closing and reopening the Material Editor.")
        # else:
        #     QMessageBox.warning(self, "Toggle Failed", message)
    
    def toggle_material_parameter(self, material, toggle_param, values_param):
        """Toggle a parameter on a material instance"""
        if not material or not toggle_param:
            return False
        
        try:
            # Check if it's a material instance
            is_material_instance = False
            if hasattr(material, 'get_class'):
                class_name = material.get_class().get_name()
                is_material_instance = 'MaterialInstanceConstant' in class_name
            
            if not is_material_instance:
                print(f"Material {material.get_name()} is not a MaterialInstanceConstant")
                return False
            
            # Initialize Material Editing Library
            material_util = unreal.MaterialEditingLibrary()
            
            # Try to get the current value as a static switch parameter
            found_param = False
            current_value = False
            
            try:
                # Try to get the current value
                result = material_util.get_material_instance_static_switch_parameter_value(material, toggle_param)
                if isinstance(result, tuple):
                    current_value = result[0]
                    found_param = result[1]
                else:
                    current_value = result
                    found_param = True
                
                if found_param:
                    print(f"Found parameter: {toggle_param} = {current_value}")
                    
                    # Toggle the boolean value
                    new_value = not current_value
                    material_util.set_material_instance_static_switch_parameter_value(material, toggle_param, new_value)
                    print(f"Toggled to {new_value}")
            except:
                # If failed as static switch, try as scalar (0.0/1.0)
                try:
                    # Try to get the current value
                    result = material_util.get_material_instance_scalar_parameter_value(material, toggle_param)
                    if isinstance(result, tuple):
                        current_value_scalar = result[0]
                        found_param = result[1]
                    else:
                        current_value_scalar = result
                        found_param = True
                    
                    if found_param:
                        current_value = current_value_scalar > 0.5
                        print(f"Found parameter: {toggle_param} = {current_value}")
                        
                        # Toggle between 0.0 and 1.0
                        new_value = 0.0 if current_value else 1.0
                        material_util.set_material_instance_scalar_parameter_value(material, toggle_param, new_value)
                        print(f"Toggled to {new_value}")
                except:
                    # Parameter not found or can't be modified
                    pass
            
            # Always set the vector parameter regardless of whether we found toggle param
            if values_param:
                try:
                    # Create color vector with R=1.0, G=1.0, B=1.0, A=0.0
                    color = unreal.LinearColor(1.0, 1.0, 1.0, 0.0)
                    material_util.set_material_instance_vector_parameter_value(material, values_param, color)
                except:
                    pass
            
            # Force material to update - try methods quietly
            try:
                # Method 1: Update material instance
                try:
                    material_util.update_material_instance(material)
                except:
                    pass
                
                # Method 2: Force parameter update
                try:
                    material_util.set_material_instance_scalar_parameter_value(material, "ForceUpdate", 1.0)
                    material_util.set_material_instance_scalar_parameter_value(material, "ForceUpdate", 0.0)
                except:
                    pass
                
                # Method 3: Try update_resource or post_edit_change if available
                try:
                    if hasattr(material, 'update_resource'):
                        material.update_resource()
                    elif hasattr(material, 'post_edit_change'):
                        material.post_edit_change()
                except:
                    pass
            except:
                pass
                
            return found_param
            
        except Exception as e:
            print(f"Error toggling parameter: {str(e)}")
            return False

    def reset_material_parameters(self, material, toggle_param, values_param):
        """Reset parameters on a material instance to default values"""
        if not material:
            return False
        
        try:
            # Check if it's a material instance
            is_material_instance = False
            if hasattr(material, 'get_class'):
                class_name = material.get_class().get_name()
                is_material_instance = 'MaterialInstanceConstant' in class_name
            
            if not is_material_instance:
                print(f"Material {material.get_name()} is not a MaterialInstanceConstant")
                return False
            
            # Initialize Material Editing Library
            material_util = unreal.MaterialEditingLibrary()
            success = False
            
            # Reset the toggle parameter to False
            if toggle_param:
                try:
                    # Try to set as static switch parameter
                    material_util.set_material_instance_static_switch_parameter_value(material, toggle_param, False)
                    print(f"Reset parameter: {toggle_param} = False")
                    success = True
                except:
                    # Try to set as scalar parameter
                    try:
                        material_util.set_material_instance_scalar_parameter_value(material, toggle_param, 0.0)
                        print(f"Reset parameter: {toggle_param} = 0.0")
                        success = True
                    except:
                        pass
            
            # Reset the vector parameter to 0,0,0,0
            if values_param:
                try:
                    # Set to all zeros
                    color = unreal.LinearColor(0.0, 0.0, 0.0, 0.0)
                    material_util.set_material_instance_vector_parameter_value(material, values_param, color)
                    print(f"Reset parameter: {values_param} = (0,0,0,0)")
                    success = True
                except:
                    pass
            
            # Force material to update - try methods quietly
            try:
                # Update material instance
                try:
                    material_util.update_material_instance(material)
                except:
                    pass
                
                # Force dummy update
                try:
                    material_util.set_material_instance_scalar_parameter_value(material, "ForceUpdate", 1.0)
                    material_util.set_material_instance_scalar_parameter_value(material, "ForceUpdate", 0.0)
                except:
                    pass
                
                # Try update methods if available
                try:
                    if hasattr(material, 'update_resource'):
                        material.update_resource()
                    elif hasattr(material, 'post_edit_change'):
                        material.post_edit_change()
                except:
                    pass
            except:
                pass
                
            return success
            
        except Exception as e:
            print(f"Error resetting parameters: {str(e)}")
            return False
            
    def reset_dynamics_to_default(self):
        """Reset dynamics parameters to default values for ALL configured material slots"""
        if not self.skeletal_mesh or not self.material_slots:
            QMessageBox.warning(self, "Warning", "No skeletal mesh selected")
            return
        
        # Process each dynamics type
        success_count = 0
        failure_count = 0
        
        for dynamic_key, dynamic_group in self.dynamics_groups.items():
            # Get parameter names from config
            params = self.dynamics_config[dynamic_key]["parameters"]
            toggle_param = params.get("toggle_param", "")
            values_param = params.get("values_param", "")
            
            # Get all configured slots for this dynamic type
            configured_slots = self.dynamics_config[dynamic_key]["material_slots"]
            
            # Find all matching slots regardless of checkbox state
            matching_slots = []
            for slot in self.material_slots:
                if slot['name'] in configured_slots:
                    matching_slots.append(slot)
            
            # Apply to each matching slot
            for slot in matching_slots:
                material = slot['material']
                
                if not material:
                    failure_count += 1
                    continue
                
                # Reset the parameters
                if self.reset_material_parameters(material, toggle_param, values_param):
                    success_count += 1
                else:
                    failure_count += 1
            
            # Uncheck all checkboxes in the UI
            for checkbox in dynamic_group["checkboxes"].values():
                checkbox.setChecked(False)
        
        # After updating all materials, try to refresh the mesh and viewports
        try:
            # Try to update the skeletal mesh
            if hasattr(self.skeletal_mesh, 'post_edit_change'):
                self.skeletal_mesh.post_edit_change()
            
            # Try to refresh viewports
            try:
                unreal.EditorLevelLibrary.redraw_all_viewports()
            except:
                pass
                
            # Try to update any selected actors
            try:
                editor_level = unreal.EditorLevelLibrary()
                actors = editor_level.get_selected_level_actors()
                
                for actor in actors:
                    try:
                        if hasattr(actor, 'skeletal_mesh_component'):
                            comp = actor.skeletal_mesh_component
                            if comp:
                                if hasattr(comp, 'recreate_render_state'):
                                    comp.recreate_render_state()
                                if hasattr(comp, 'update_materials'):
                                    comp.update_materials()
                    except:
                        pass
            except:
                pass
                
        except:
            pass
        
        # Show results
        message = ""
        if success_count > 0 and failure_count == 0:
            message = f"Successfully reset dynamics for {success_count} material(s)"
            self.set_status(message, "success")
        elif success_count > 0 and failure_count > 0:
            message = f"Reset dynamics for {success_count} material(s), {failure_count} failed"
            self.set_status(message, "warning")
        else:
            message = f"Failed to reset dynamics for any materials"
            self.set_status(message, "error")
        
        # Show message box with details
        # if success_count > 0:
        #     QMessageBox.information(self, "Reset Complete", message + "\n\nChanges have been applied but not saved. Use the Content Browser to save modifications." +
        #                            "\n\nIf changes are not visible in the viewport, try closing and reopening the Material Editor.")
        # else:
        #     QMessageBox.warning(self, "Reset Failed", message)

# Main application entry point
try:
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
        font = QFont("Meiryo UI")
        font.setPointSize(10)
        app.setFont(font)
    
    widget = DynamicsToggle()
    widget.show()
    unreal.parent_external_window_to_slate(widget.winId())
except ImportError:
    sys.exit(1)