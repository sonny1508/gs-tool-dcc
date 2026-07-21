"""
This module contains different utilities related to the layer stack in
Substance 3D Painter.
"""

# Modules Import
import string
from substance_painter import textureset, layerstack, project, resource, logging, colormanagement


class LayerManager:
    """
    The `LayerManager` class provides a set of utilities for managing layers within the active texture stack in Adobe Substance 3D Painter.
    """

    def __init__(self):
        """Class Initialization"""
        self._current_stack = None
        self._layer_selection = None
        self._stack_layers = None
        self._stack_layers_count = None
        
        if project.is_open():
            self._current_stack = textureset.get_active_stack()
            self._layer_selection = layerstack.get_selected_nodes(self._current_stack)            

    @property
    def current_stack(self):
        return self._current_stack    

    @current_stack.setter
    def current_stack(self, value):
        self._current_stack = value

    @property
    def layer_selection(self):
        return self._layer_selection

    @layer_selection.setter
    def layer_selection(self, value):
        self._layer_selection = value

    @property
    def stack_layers(self):
        if self._stack_layers is None:
            self._stack_layers = layerstack.get_root_layer_nodes(self._current_stack)
        return self._stack_layers

    @property
    def stack_layers_count(self):
        if self._stack_layers_count is None:
            self._stack_layers_count = len(self.stack_layers)
        return self._stack_layers_count
    
    def refresh_layer_selection(self):
        self.layer_selection = layerstack.get_selected_nodes(self.current_stack)

    def add_layer(self, layer_type, layer_name ="New Layer", active_channels=None, layer_position="Above"):
        """Add a layer of specified type to the current stack with optional active channels"""
        
        if layer_position not in ["Above", "On Top"]:
            logging.error("layer_position parameter must be 'Above' or 'On Top'")
            return None
        
        current_layer_count = self._stack_layers_count
        if self._current_stack is None:
            logging.error("No active stack found")
            return None
        
        
        insert_position = None
        selected_layer = layerstack.get_selected_nodes(self._current_stack)
        
        if current_layer_count == 0:
            insert_position = layerstack.InsertPosition.from_textureset_stack(self._current_stack)
            
        elif layer_position == "Above":
            insert_position = layerstack.InsertPosition.above_node(selected_layer[0])
            
        elif layer_position == "On Top":
            insert_position = layerstack.InsertPosition.from_textureset_stack(self._current_stack)
        
        
        new_layer = None
        
        if layer_type == 'fill':
            new_layer = layerstack.insert_fill(insert_position)
           
        elif layer_type == 'paint':
            new_layer = layerstack.insert_paint(insert_position)
            
        else:
            logging.error("Invalid layer type")
            return
        
        if active_channels:
            if active_channels==[""]:
                pass
            else:
                new_layer.active_channels = {getattr(textureset.ChannelType, channel) for channel in active_channels}
        else:
            active_channels = self._current_stack.all_channels()
            new_layer.active_channels = set(active_channels)

        
        new_layer.set_name(layer_name)
        layerstack.set_selected_nodes([new_layer])
        
        return new_layer if new_layer else None

    def delete_stack_content(self):
        """Delete all layers in the current stack."""
        current_layers = self.stack_layers
        for layer in current_layers:
            layerstack.delete_node(layer)
            

    def generate_ref_point_layer(self):
        """Generate a reference point layer with unique naming and specific effects."""
        base_name = "REF POINT LAYER"        
        all_nodes = layerstack.get_root_layer_nodes(self.current_stack)

        ref_point_count = 1
        for node in all_nodes:
            if node.get_name().startswith(base_name):
                ref_point_count += 1
            if node.get_type() == layerstack.NodeType.GroupLayer:
                sublayers = node.sub_layers()
                for sublayer in sublayers:
                    if sublayer.get_name().startswith(base_name):
                        ref_point_count += 1

        # Fotmat the counter to be 2 digit numbers
        formatted_ref_point_count = f"_{str(ref_point_count).zfill(2)}"

        # build ref pint name
        ref_point_name = f"{base_name}{formatted_ref_point_count}"

        # Add new layer with proper name
        ref_point_layer = self.add_layer("paint", layer_position="Above")
        ref_point_layer.set_name(ref_point_name)


        for new_layer_channel in ref_point_layer.active_channels:
            normal_blending = layerstack.BlendingMode(25)
            ref_point_layer.set_blending_mode(normal_blending, new_layer_channel)

        insert_position = layerstack.InsertPosition.inside_node(ref_point_layer, layerstack.NodeStack.Content)
        layerstack.insert_anchor_point_effect(insert_position, ref_point_name)

class MaskManager:
    """
    The `MaskManager` class provides utilities for managing masks within the active texture stack in Adobe Substance 3D Painter.
    """

    def __init__(self, layer_manager):
        self.layer_manager = layer_manager

    def add_mask(self, mask_bkg_color=None):
        """Adds a mask to the currently selected layer with optional background color."""
        
        color_map = {
            'Black': layerstack.MaskBackground.Black,  
            'White': layerstack.MaskBackground.White  
        }

        if mask_bkg_color and mask_bkg_color not in color_map:
            logging.error("Invalid mask color. Choose 'Black' or 'White'.")
            return

        if self.layer_manager.current_stack:
            current_layer = layerstack.get_selected_nodes(self.layer_manager.current_stack)

            for selectedLayer in current_layer:
                if selectedLayer.has_mask():
                    if mask_bkg_color:
                        selectedLayer.remove_mask()
                        selectedLayer.add_mask(color_map[mask_bkg_color])
                    else:
                        current_mask_background = selectedLayer.get_mask_background()
                        new_mask_background = (layerstack.MaskBackground.White if current_mask_background == layerstack.MaskBackground.Black 
                                            else layerstack.MaskBackground.Black)
                        selectedLayer.remove_mask()
                        selectedLayer.add_mask(new_mask_background)
                else:
                    mask_to_add = color_map.get(mask_bkg_color, layerstack.MaskBackground.Black)
                    selectedLayer.add_mask(mask_to_add)

    def add_black_mask_with_ao_generator(self):
        """Adds a black mask with an ambient occlusion generator to the currently selected layer."""
        self.add_mask('Black')
        
        if self.layer_manager.current_stack:
            current_layer = layerstack.get_selected_nodes(self.layer_manager.current_stack)
            generator_resource = resource.search("s:starterassets u:generator n:Ambient Occlusion")[0]
            
            insertion_positions = [
                layerstack.InsertPosition.inside_node(layer, layerstack.NodeStack.Mask)
                for layer in current_layer
            ]
            for pos in insertion_positions:
                layerstack.insert_generator_effect(pos, generator_resource.identifier())

    def add_black_mask_with_curvature_generator(self):
        """Adds a black mask with a curvature generator to the currently selected layer."""
        self.add_mask('Black')
        
        if self.layer_manager.current_stack:
            current_layer = layerstack.get_selected_nodes(self.layer_manager.current_stack)
            generator_resource = resource.search("s:starterassets u:generator n:Curvature")[0]
            
            insertion_positions = [
                layerstack.InsertPosition.inside_node(layer, layerstack.NodeStack.Mask)
                for layer in current_layer
            ]
            for pos in insertion_positions:
                layerstack.insert_generator_effect(pos, generator_resource.identifier())

    def add_mask_with_fill(self):
        """Adds a black mask with a fill layer to the currently selected layer.
        """
        current_layer = layerstack.get_selected_nodes(self.layer_manager.current_stack)
        self.add_mask()
        
        inside_mask = layerstack.InsertPosition.inside_node(current_layer[0], layerstack.NodeStack.Mask)
        my_fill_effect_mask = layerstack.insert_fill(inside_mask)
        
        pure_white = colormanagement.Color(1.0, 1.0, 1.0)
        my_fill_effect_mask.set_source(channeltype=None, source=pure_white)

class FilterManager:

    def __init__(self, layer_manager):
        self.layer_manager = layer_manager

    def new_gs_pbr_validator(self):
        """Adds a new paint layer with Passthrough blending mode and GS_PBR_Validator filter effect to its content."""
        # Create a new paint layer
        new_layer = self.layer_manager.add_layer(layer_type='paint', layer_name="GS_PBR_Validator")
        
        if new_layer and self.layer_manager.current_stack:
            # Set PassThrough blending mode for each channel
            passthrough_blending = layerstack.BlendingMode.Passthrough  # Use the enum directly
            
            # Apply the blending mode to each active channel
            for channel in new_layer.active_channels:
                new_layer.set_blending_mode(passthrough_blending, channel)
                
            # Get the filter resource
            filter_resource = resource.search("s:yourassets u:filter n:GS_PBR_Validator")[0]
            
            # Create insertion position for the content of the new layer (not its mask)
            insert_position = layerstack.InsertPosition.inside_node(new_layer, layerstack.NodeStack.Content)
            
            # Insert the filter effect
            layerstack.insert_filter_effect(insert_position, filter_resource.identifier())

    def batch_gs_pbr_validator(self, validator_type="GS_PBR_Validator"):
        """Adds a new paint layer with Passthrough blending mode and specified PBR validator filter effect to all texture sets.
        
        Args:
            validator_type (str): The type of validator to use. Options: "GS_PBR_Validator", "GS_PBR_Validator_HW3", "GS_PBR_Validator_MGP25"
        """
        # Get all texture sets in the project
        all_texture_sets = textureset.all_texture_sets()
        
        # Process each texture set
        for ts in all_texture_sets:
            # Get the default stack for this texture set
            stack = ts.get_stack()
            
            # Set this stack as active so we can work with it
            textureset.set_active_stack(stack)
            
            # Update the layer manager with the current stack
            self.layer_manager.current_stack = stack
            
            # Create a new paint layer at the very top of the stack
            new_layer = self.layer_manager.add_layer(
                layer_type='paint', 
                layer_name=validator_type, 
                layer_position="On Top"  # This ensures it's at the top, outside any folder
            )
            
            if new_layer:
                # Set Passthrough blending mode for each channel
                passthrough_blending = layerstack.BlendingMode.Passthrough
                
                # Apply the blending mode to each active channel
                for channel in new_layer.active_channels:
                    new_layer.set_blending_mode(passthrough_blending, channel)
                    
                # Get the filter resource - use the validator_type to find the correct filter
                filter_resource = resource.search(f"s:yourassets u:filter n:{validator_type}")[0]
                
                # Create insertion position for the content of the new layer
                insert_position = layerstack.InsertPosition.inside_node(new_layer, layerstack.NodeStack.Content)
                
                # Insert the filter effect
                layerstack.insert_filter_effect(insert_position, filter_resource.identifier())
            
            logging.info(f"Added {validator_type} to texture set: {ts.name}")

    def batch_gs_pbr_validator_r6(self):
        """Adds GS_PBR_Validator_R3 filter layer to all texture sets in the project."""
        self.batch_gs_pbr_validator("GS_PBR_Validator_R6")

    def batch_gs_pbr_validator_hw3(self):
        """Adds GS_PBR_Validator_HW3 filter layer to all texture sets in the project."""
        self.batch_gs_pbr_validator("GS_PBR_Validator_HW3")

    def batch_gs_pbr_validator_mgp25(self):
        """Adds GS_PBR_Validator_MGP25 filter layer to all texture sets in the project."""
        self.batch_gs_pbr_validator("GS_PBR_Validator_MGP25")

    def remove_gs_pbr_validator(self):
        """Removes all PBR validator layers from all texture sets."""
        # Define all validator layer names to remove
        validator_names = ["GS_PBR_Validator", "GS_PBR_Validator_R6","GS_PBR_Validator_HW3", "GS_PBR_Validator_MGP25"]
        
        # Get all texture sets in the project
        all_texture_sets = textureset.all_texture_sets()
        
        for ts in all_texture_sets:
            # Get all stacks for this texture set
            stacks = ts.all_stacks()
            
            for stack in stacks:
                # Get all layers in the stack
                root_layers = layerstack.get_root_layer_nodes(stack)
                
                # Find and delete any layer with validator names
                for layer in root_layers:
                    layer_name = layer.get_name()  # Get the name before deletion
                    if layer_name in validator_names:
                        layerstack.delete_node(layer)
                        logging.info(f"Removed {layer_name} from stack {stack}")  # Use stored name