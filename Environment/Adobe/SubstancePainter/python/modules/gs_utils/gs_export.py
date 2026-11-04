##########################################################################
#
# Copyright 2010-2024 Vincent GAULT - Adobe
# All Rights Reserved.
#
##########################################################################

# Modules Import
import os, time

from substance_painter import export, textureset, resource, layerstack, logging
from gs_utils import gs_layerstack, gs_project_info

class TextureImporter:
    """
    Responsible for importing textures from the file paths.
    """

    def import_textures(self, textures_to_import):
        """
        Import the textures from the specified paths.

        Args:
            textures_to_import (object): The exported textures to be imported.

        Returns:
            dict: A dictionary with the imported texture resources keyed by their respective paths.
        """
        imported_textures = {}
        texture_paths = []

        for texture_list_key in textures_to_import.textures.keys():
            current_texture_list = textures_to_import.textures[texture_list_key]

            for texture_path in current_texture_list:
                texture_paths.append(texture_path)  # Collect texture paths for cleanup later
                texture_resource = resource.import_project_resource(texture_path, resource.Usage.TEXTURE)
                imported_textures[texture_path] = texture_resource

        return imported_textures, texture_paths


class ChannelTypeExtractor:
    """
    Responsible for extracting the channel type from the texture file path.
    """

    def extract_channel_type(self, texture_path):
        """
        Extract the channel type from the texture file path.

        Args:
            texture_path (str): The file path of the texture.

        Returns:
            str: The extracted channel type.
        """
        file_name = os.path.basename(texture_path)
        last_underscore_index = file_name.rfind("_")
        if last_underscore_index != -1:
            # Drops the extension (png or exr) and any .$udim
            channel_type_string = file_name[last_underscore_index + 1:].split(".")[0]
            if channel_type_string == 'ambientOcclusion':
                channel_type_string = 'AO'
            return channel_type_string
        return None


class LayerTextureAssigner:
    """
    Responsible for assigning imported textures to the correct channels in a fill layer.
    """

    def assign_textures_to_layer(self, new_layer, imported_textures):
        """
        Assign the imported textures to the correct channels in the new fill layer.

        Args:
            new_layer (object): The fill layer where the textures will be assigned.
            imported_textures (dict): A dictionary of imported texture resources keyed by their file paths.
        """
        extractor = ChannelTypeExtractor()

        for texture_path, texture_resource in imported_textures.items():
            channel_type_string = extractor.extract_channel_type(texture_path)

            if channel_type_string:
                print(f"Assigning texture to channel: {channel_type_string}")
                channel_type = getattr(layerstack.ChannelType, channel_type_string)
                new_layer.set_source(channel_type, texture_resource.identifier())

        print("Textures imported and assigned to the new fill layer.")
        


class ResourceCleaner:
    """
    Manages the cleanup of texture files after they are imported and assigned.
    """
    
    def delete_texture_files(self, texture_paths):
        """
        Deletes the texture files from disk after they have been imported.

        Args:
            texture_paths (list): List of texture file paths to delete.
        """
        for texture_path in texture_paths:
            try:
                os.remove(texture_path)
                print(f"Deleted file: {texture_path}")
            except Exception as e:
                print(f"Error deleting file {texture_path}: {e}")


class TextureAssignmentManager:
    """
    Manages the process of importing exported textures into a new fill layer and assigning them to the appropriate channels.
    """

    def __init__(self):
        self.texture_importer = TextureImporter()
        self.layer_assigner = LayerTextureAssigner()
        #self.resource_cleaner = ResourceCleaner()

    def import_and_assign_textures(self, new_layer, textures_to_import):
        """
        Import the exported textures into a new fill layer and assign them to the correct channels.

        Args:
            new_layer (object): The fill layer where the textures will be assigned.
            textures_to_import (object): The exported textures to be imported.
        """
        imported_textures, texture_paths = self.texture_importer.import_textures(textures_to_import)
        self.layer_assigner.assign_textures_to_layer(new_layer, imported_textures)
        #self.resource_cleaner.delete_texture_files(texture_paths)                                #do not uncomment


CHANNEL_EXPORT_FORMATS = {
    "sRGB8": ("png", "8"),
    "L8": ("png", "8"),
    "RGB8": ("png", "8"),
    "L16": ("png", "16"),
    "RGB16": ("png", "16"),
    "L16F": ("exr", "16f"),
    "RGB16F": ("exr", "16f"),
    "L32F": ("exr", "32f"),
    "RGB32F": ("exr", "32f"),
}
"""File format and bit depth that hold each textureset.ChannelFormat without loss."""


class ExportConfigGenerator:
    """
    Generates the export configuration for the active texture set.

    With `faithful`, each channel is written at its own format and areas the layers do not cover stay
    transparent, so the result can stand in for those layers. Otherwise: 8-bit PNG, padded everywhere.
    `file_tag` goes in the file names, ahead of the channel name.
    """

    def __init__(self, export_path, preset_name="Current channels Export", faithful=False, file_tag=None):
        self.export_path = export_path
        self.preset_name = preset_name
        self.faithful = faithful
        self.file_tag = file_tag

    def generate_current_channels_maps_export(self):
        current_stack = textureset.get_active_stack()
        texture_set_info_manager = gs_project_info.TextureSetInfo(current_stack)
        current_textureset_info = texture_set_info_manager.fetch_texture_set_info_from_stack()

        udim_suffix = ""
        current_texture_set = current_textureset_info["Texture Set"]
        if current_texture_set.has_uv_tiles():
            udim_suffix = '.$udim'

        current_channels_info = []

        for channel_type, channel in current_textureset_info["Channels"].items():
            channel_name = 'ambientOcclusion' if channel_type.name == 'AO' else channel_type.name
            file_format, bit_depth = CHANNEL_EXPORT_FORMATS[channel.format().name] if self.faithful else ('png', '8')

            channels_info = [
                {
                    "destChannel": channel,
                    "srcChannel": channel,
                    "srcMapType": "DocumentMap",
                    "srcMapName": channel_name
                } for channel in "RGBA"
            ]

            file_tag = f'{self.file_tag}_' if self.file_tag else ''
            current_filename = f'$mesh_$textureSet_{file_tag}{channel_name}'
            current_filename = current_filename + udim_suffix

            current_channels_info.append({
                'fileName': current_filename,
                'channels': channels_info,
                'parameters': {
                    'bitDepth': bit_depth,
                    'dithering': False,
                    'fileFormat': file_format
                }
            })

        return current_channels_info

    def generate_export_config(self):
        current_channels_export_preset = {
            "name": self.preset_name,
            "maps": self.generate_current_channels_maps_export()
        }

        texture_set_info_manager = gs_project_info.TextureSetInfo()
        current_textureset_info = texture_set_info_manager.fetch_texture_set_info_from_stack()

        if self.faithful:
            export_parameters = {"dithering": False, "paddingAlgorithm": "transparent", "dilationDistance": 1}
        else:
            export_parameters = {"dithering": True, "paddingAlgorithm": "infinite"}

        export_config = {
            "exportPath": self.export_path,
            "exportShaderParams": False,
            "defaultExportPreset": self.preset_name,
            "exportPresets": [current_channels_export_preset],
            "exportList": [{"rootPath": current_textureset_info["Name"]}],
            "exportParameters": [
                {"parameters": export_parameters}
            ],
            "uvTiles": current_textureset_info["UV Tiles coordinates"],
        }
        return export_config


class TextureExporter:
    """
    Handles the export of textures using a given export configuration.
    """

    def export_textures(self, export_config):
        try:
            export_result = export.export_project_textures(export_config)

            if export_result.status == export.ExportStatus.Error:
                print("Error during texture export:", export_result.message)
                return None
            else:
                print("Export successful!")
                return export_result

        except Exception as e:
            print(f"Error during texture export: {e}")
            return None


##### FUNCTIONS USING THE CLASSES #####

def bake_layers_to_fill(stack_manager, layers, layer_name):
    """Bake `layers` into a new fill layer above them, then hide them.

    Returns the new layer, or None if the export failed or was cancelled, leaving the stack as it was.
    """

    # Generate the export configuration. Every bake gets its own file names, so that importing one
    # can never touch the textures of an earlier one.
    export_path = export.get_default_export_path()
    config_generator = ExportConfigGenerator(export_path, faithful=True, file_tag=str(time.time_ns()))
    export_config = config_generator.generate_export_config()

    # Perform the export with only these layers showing: export renders what is visible
    exporter = TextureExporter()
    with gs_layerstack.isolated_layers(stack_manager.current_stack, layers):
        exported_textures = exporter.export_textures(export_config)

    # A cancelled export only wrote some of the channels
    if not exported_textures or exported_textures.status == export.ExportStatus.Cancelled:
        return None

    # Import the textures to a new layer
    texture_manager = TextureAssignmentManager()

    # At root level: the export already includes the masks and opacity of any group around the
    # layers, and inside that group they would apply a second time.
    # The fill keeps its default blending: forcing Normal would make its height and normal replace
    # what is below instead of adding to it.
    above_layer = gs_layerstack.root_layer(layers[0])
    new_layer = stack_manager.add_layer("fill", layer_name=layer_name, above_layer=above_layer)
    texture_manager.import_and_assign_textures(new_layer, exported_textures)

    with layerstack.ScopedModification(f"Hide baked layers: {layer_name}"):
        for layer in layers:
            layer.set_visible(False)

    return new_layer


def merge_selected_layers():
    """Merge the selected layers into a new fill layer above them, then hide them."""

    current_stack_manager = gs_layerstack.LayerManager()
    selected_layers = current_stack_manager.selected_layers()
    if not selected_layers:
        logging.warning("Select the layers to merge first")
        return

    bake_layers_to_fill(current_stack_manager, selected_layers, "Merged layers")


def flatten_selected_groups():
    """Flatten each selected group into its own fill layer above it, then hide the group."""

    current_stack_manager = gs_layerstack.LayerManager()
    selected_groups = [
        layer for layer in current_stack_manager.selected_layers()
        if layer.get_type() == layerstack.NodeType.GroupLayer
    ]
    # A group inside another selected group is already part of that group's result
    groups = [
        group for group in selected_groups
        if not any(parent in selected_groups for parent in gs_layerstack.iter_ancestors(group))
    ]
    if not groups:
        logging.warning("Select the groups to flatten first")
        return

    # Bottom-up: groups nested in the same root group all land above it, and this keeps their order
    flattened = 0
    for group in reversed(groups):
        if not bake_layers_to_fill(current_stack_manager, [group], f"{group.get_name()} (flattened)"):
            logging.warning(f"Stopped at group '{group.get_name()}': its export did not finish")
            break
        flattened += 1

    logging.info(f"Flattened {flattened}/{len(groups)} group(s)")


def flatten_stack():
    """Flatten the stack by exporting and importing textures."""
    
    export_path = export.get_default_export_path()
    config_generator = ExportConfigGenerator(export_path)

    # Generate the export configuration
    export_config = config_generator.generate_export_config()

    # Perform the export
    exporter = TextureExporter()
    stack_manager = gs_layerstack.LayerManager()
    exported_textures = exporter.export_textures(export_config)
    
    stack_manager.delete_stack_content() #delete before to reimport

    # Import the textures to a new layer
    if exported_textures:
        texture_manager = TextureAssignmentManager()
        new_layer = stack_manager.add_layer("fill", layer_position="On Top", layer_name="Stack layer")
        new_layer.active_channels = set(new_layer.active_channels)
        
        for new_layer_channel in new_layer.active_channels:
            normal_blending = layerstack.BlendingMode(2)
            new_layer.set_blending_mode(normal_blending, new_layer_channel)
        
        texture_manager.import_and_assign_textures(new_layer, exported_textures)
        

#####################################

if __name__ == "__main__":
    # Initialize the export configuration generator
    export_path = export.get_default_export_path()
    config_generator = ExportConfigGenerator(export_path)

    # Generate the export configuration
    export_config = config_generator.generate_export_config()

    # Perform the export
    exporter = TextureExporter()
    exported_textures = exporter.export_textures(export_config)

    # Import the textures to a new layer
    if exported_textures:
        texture_manager = TextureAssignmentManager()
        current_stack_manager = gs_layerstack.LayerManager()
        new_layer = current_stack_manager.add_layer("fill", layer_position="On Top", layer_name="Stack layer")
        new_layer.active_channels = set(new_layer.active_channels)
        
        for new_layer_channel in new_layer.active_channels:
            normal_blending = layerstack.BlendingMode(2)
            new_layer.set_blending_mode(normal_blending, new_layer_channel)
        
        texture_manager.import_and_assign_textures(new_layer, exported_textures)
