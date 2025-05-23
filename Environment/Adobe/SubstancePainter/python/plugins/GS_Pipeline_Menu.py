"""
This module creates a menu to host various tools for Substance Painter.
"""
# Modules import
from PySide6 import QtWidgets, QtGui
from PySide6.QtGui import QKeySequence
import importlib

from substance_painter import ui, logging
from gs_utils import gs_baking, gs_export, gs_layerstack, gs_project_info

plugin_menus_widgets = []
"""Keeps track of added UI elements for cleanup."""

######## PBR VALIDATOR FUNCTIONS ########

def new_gs_pbr_validator():
    """Create a new paint layer with GS_PBR_Validator filter effect."""
    layer_manager = gs_layerstack.LayerManager()
    filter_manager = gs_layerstack.FilterManager(layer_manager)
    filter_manager.new_gs_pbr_validator()

def batch_gs_pbr_validator():
    """Create GS_PBR_Validator filter layer on all texture sets in the project."""
    layer_manager = gs_layerstack.LayerManager()
    filter_manager = gs_layerstack.FilterManager(layer_manager)
    filter_manager.batch_gs_pbr_validator()

def remove_gs_pbr_validator():
    """Remove GS_PBR_Validator filter layers from all texture sets in the project."""
    layer_manager = gs_layerstack.LayerManager()
    filter_manager = gs_layerstack.FilterManager(layer_manager)
    filter_manager.remove_gs_pbr_validator()

######## FILL LAYER FUNCTIONS ########

def new_fill_layer_base():
    """Create a new fill layer with Base Color activated."""
    layer_manager = gs_layerstack.LayerManager()
    layer_manager.add_layer(layer_type='fill', active_channels=["BaseColor"], layer_name="New fill layer")

def new_fill_layer_height():
    """Create a new fill layer with Height channel activated."""
    layer_manager = gs_layerstack.LayerManager()
    layer_manager.add_layer(layer_type='fill', active_channels=["Height"], layer_name="New fill layer")

def new_fill_layer_all():
    """Create a new fill layer with all channels activated."""
    layer_manager = gs_layerstack.LayerManager()
    layer_manager.add_layer(layer_type='fill', layer_name="New fill layer")
    

def new_fill_layer_empty():
    """Create a new fill layer with no channels activated."""
    layer_manager = gs_layerstack.LayerManager()
    layer_manager.add_layer(layer_type='fill', active_channels=[""], layer_name="New fill layer")


######## PAINT LAYER FUNCTIONS ########    

def new_paint_layer():
    """Create a new paint layer."""
    layer_manager = gs_layerstack.LayerManager()
    layer_manager.add_layer(layer_type='paint', layer_name="New Paint layer")

######## MASK FUNCTIONS ########

def add_mask():
    """Add a black mask to the selected layer."""
    layer_manager = gs_layerstack.LayerManager()
    mask_manager = gs_layerstack.MaskManager(layer_manager)
    mask_manager.add_mask()

def add_ao_mask():
    """Add a black mask with AO Generator."""
    layer_manager = gs_layerstack.LayerManager()
    mask_manager = gs_layerstack.MaskManager(layer_manager)
    mask_manager.add_black_mask_with_ao_generator()

def add_curvature_mask():
    """Add a black mask with Curvature Generator."""
    layer_manager = gs_layerstack.LayerManager()
    mask_manager = gs_layerstack.MaskManager(layer_manager)
    mask_manager.add_black_mask_with_curvature_generator()

def add_mask_with_fill_effect():
    """Add a mask with a fill effect."""
    layer_manager = gs_layerstack.LayerManager()
    mask_manager = gs_layerstack.MaskManager(layer_manager)
    mask_manager.add_mask_with_fill()

################ GENERATE CONTENT FROM STACK #######################    

def create_layer_from_stack():
    """Generate a layer from the visible content in the stack."""
    gs_export.create_layer_from_stack()
    

def flatten_stack():
    """Flatten the stack by exporting and importing textures."""    
    gs_export.flatten_stack()


############## CREATE REFERENCE POINT LAYER ####################### 

def create_ref_point_layer():
    """Create a reference point layer."""
    stack_manager = gs_layerstack.LayerManager()
    stack_manager.generate_ref_point_layer()


########################### QUICK BAKE ########################### 

def launch_quick_bake():
    """Quickly bake mesh maps of the current texture set."""
    gs_baking.quick_bake()
    
    
#################################################################

def create_menu():    
    """Create and populate the menu with actions."""
    # Get the main window
    main_window = ui.get_main_window()    

    # Create a new menu
    gs_utilities_menu = QtWidgets.QMenu("GS Pipeline", main_window)
    ui.add_menu(gs_utilities_menu)
    plugin_menus_widgets.append(gs_utilities_menu)

    # Define actions, shortcuts, and separators
    actions_with_separators = [
        ("New Paint Layer with GS_PBR_Validator Filter Effect", new_gs_pbr_validator, "Ctrl+P"),
        ("Batch GS_PBR_Validator for all Texture Sets", batch_gs_pbr_validator, None),
        ("Remove GS_PBR_Validator from all Texture Sets", remove_gs_pbr_validator, None),
        None,  # Separator
        ("New Fill Layer with Base Color", new_fill_layer_base, "Ctrl+F"),
        ("New Fill Layer with Height", new_fill_layer_height, "Ctrl+Alt+F"),
        ("New Fill Layer with All Channels", new_fill_layer_all, "Ctrl+Shift+F"),
        ("New Fill Layer, no channel", new_fill_layer_empty, "Alt+F"),
        None,  # Separator
        ("Add Mask to Selected Layer", add_mask, "Ctrl+M"),
        ("Add Mask with Fill Effect", add_mask_with_fill_effect, "Shift+M"),
        ("Add Mask with AO Generator", add_ao_mask, "Ctrl+Shift+M"),
        ("Add Mask with Curvature Generator", add_curvature_mask, "Ctrl+Alt+M"),
        None,  # Separator
        ("Create New Layer from Visible Stack", create_layer_from_stack, "Ctrl+Shift+G"),
        ("Flatten Stack", flatten_stack, None),
        None,  # Separator
        ("Create Reference Point Layer", create_ref_point_layer, "Ctrl+R"),
        None,  # Separator
        ("Quick Bake", launch_quick_bake, "Ctrl+B"),
    ]

    # Add actions and separators to the menu
    for item in actions_with_separators:
        if item is None:
            gs_utilities_menu.addSeparator()
        else:
            text, func, shortcut = item
            action = QtGui.QAction(text, gs_utilities_menu)
            action.triggered.connect(func)
            if shortcut:
                action.setShortcut(QKeySequence(shortcut))
            gs_utilities_menu.addAction(action)



def start_plugin():
    """Called when the plugin is started."""
    create_menu()
    logging.info("GS Pipeline Activated") 
    

def close_plugin():
    """Called when the plugin is stopped."""
    # Remove all added widgets from the UI.
    for widget in plugin_menus_widgets:
        ui.delete_ui_element(widget)
    plugin_menus_widgets.clear()
    logging.info("GS Pipeline deactivated")  

def reload_plugin():
    """Reload plugin modules."""
    importlib.reload(gs_layerstack)
    importlib.reload(gs_export)
    importlib.reload(gs_baking)
    importlib.reload(gs_project_info)

if __name__ == "__main__":
    importlib.reload(gs_layerstack)
    importlib.reload(gs_export)
    importlib.reload(gs_baking)
    importlib.reload(gs_project_info)

    start_plugin()
