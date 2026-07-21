import bpy
from bpy.types import Panel

# Import the list module to access operator definitions
from . import GS_Asset_Validation_List

class GS_PT_AssetValidation(Panel):
    bl_label = "GS Asset Validation"
    bl_idname = "GS_PT_AssetValidation"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "GS Asset Validation"

    def draw(self, context):
        layout = self.layout
        # No additional labels needed

class GS_PT_AssetValidationSubPanel(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "GS Asset Validation"
    # Remove the DEFAULT_CLOSED option to keep panels open by default
    bl_options = set()
    
    @classmethod
    def poll(cls, context):
        return True

# Generate dynamic UI panels based on categories
panels = []

# Override the poll methods for all the operators to make them always available
def override_poll_methods():
    for cls_name in dir(bpy.types):
        if cls_name.startswith('GS_'):
            cls = getattr(bpy.types, cls_name)
            if hasattr(cls, 'poll'):
                # Create a new poll method that always returns True
                def always_available(cls, context):
                    return True
                
                # Replace the poll method
                setattr(cls, 'poll', classmethod(always_available))

def generate_panels():
    # Clear existing panels
    global panels
    for panel in panels:
        try:
            bpy.utils.unregister_class(panel)
        except:
            pass
    panels = []
    
    # Create a panel for each category
    for i, category in enumerate(GS_Asset_Validation_List.VALIDATION_OPERATORS):
        category_name = category["category"]
        # Create panel class
        panel_idname = f"GS_PT_AssetValidation_{category_name.replace(' ', '')}"
        panel_attrs = {
            "bl_label": category_name,
            "bl_idname": panel_idname,
            "bl_parent_id": "GS_PT_AssetValidation",
        }
        
        # Create a closure to properly capture the category
        def make_draw_func(category_data):
            def draw(self, context):
                layout = self.layout
                
                # Add all operators for this category
                for op in category_data["operators"]:
                    row = layout.row(align=True)
                    
                    # Use operator_context to ensure buttons are always enabled
                    row.operator_context = 'EXEC_DEFAULT'
                    
                    # Add the operator
                    op_props = row.operator(op["id"], text=op["label"])
                    
                    # Add any properties to the operator if defined
                    if "props" in op:
                        for prop in op["props"]:
                            prop_name = prop["name"]
                            # Set property values if needed
                            if hasattr(op_props, prop_name):
                                setattr(op_props, prop_name, prop.get("default", getattr(op_props, prop_name)))
            
            return draw
        
        panel_attrs["draw"] = make_draw_func(category)
        
        # Create panel class dynamically
        PanelClass = type(
            panel_idname, 
            (GS_PT_AssetValidationSubPanel,), 
            panel_attrs
        )
        
        panels.append(PanelClass)
        bpy.utils.register_class(PanelClass)

def register():
    # Debug output
    print("Registering GS Asset Validation UI")
    bpy.utils.register_class(GS_PT_AssetValidation)
    
    # Generate the panels
    generate_panels()
    
    # Override poll methods to make all buttons always available
    override_poll_methods()
    
    print("UI Registration complete")

def unregister():
    print("Unregistering GS Asset Validation UI")
    bpy.utils.unregister_class(GS_PT_AssetValidation)
    for panel in panels:
        try:
            bpy.utils.unregister_class(panel)
        except:
            pass
    print("UI Unregistration complete")