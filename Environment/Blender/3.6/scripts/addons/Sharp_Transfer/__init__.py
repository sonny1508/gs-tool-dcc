bl_info = {
    "name": "Sharp Transfer",
    "author": "Your Name",
    "version": (1, 0, 0),
    "blender": (3, 6, 0),
    "location": "View3D > N-Panel > Sharp Transfer",
    "description": "Transfer sharp edges between Blender and 3ds Max via UV channels",
    "category": "Mesh",
    "support": "COMMUNITY",
}

import bpy
import bmesh
from bpy.types import Panel, Operator
import re


def get_highest_numbered_uv_channel(obj):
    """Find the highest numbered UV channel (UVChannel_x) and return the number"""
    highest_num = 0
    pattern = re.compile(r'UVChannel_(\d+)')
    
    for uv_layer in obj.data.uv_layers:
        match = pattern.match(uv_layer.name)
        if match:
            num = int(match.group(1))
            highest_num = max(highest_num, num)
    
    return highest_num


def get_next_uv_channel_name(obj):
    """Get the next available UV channel name based on total UV channel count"""
    total_channels = len(obj.data.uv_layers)
    
    # If we have less than 8 channels, create the next numbered channel
    if total_channels < 8:
        next_num = total_channels + 1
    else:
        # If we have 8 channels (maximum), we'll replace the last one with UVChannel_8
        next_num = 8
    
    return f"UVChannel_{next_num}"


def find_highest_numbered_uv_layer(obj):
    """Find the UV layer with the highest number and return the layer and its index"""
    highest_num = 0
    highest_layer = None
    highest_index = -1
    pattern = re.compile(r'UVChannel_(\d+)')
    
    for i, uv_layer in enumerate(obj.data.uv_layers):
        match = pattern.match(uv_layer.name)
        if match:
            num = int(match.group(1))
            if num > highest_num:
                highest_num = num
                highest_layer = uv_layer
                highest_index = i
    
    return highest_layer, highest_index


class MESH_OT_sharp_to_uv(Operator):
    """Convert sharp edges to UV seams and store in numbered UV channel"""
    bl_idname = "mesh.sharp_to_uv"
    bl_label = "Sharp to UV"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.mode == 'OBJECT' and 
                context.selected_objects and 
                any(obj.type == 'MESH' for obj in context.selected_objects))

    def execute(self, context):
        processed_objects = 0
        failed_objects = []
        no_sharp_objects = []
        
        # Store original active object
        original_active = context.view_layer.objects.active
        
        mesh_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        
        for obj in mesh_objects:
            try:
                # Set as active and enter edit mode
                context.view_layer.objects.active = obj
                bpy.ops.object.mode_set(mode='EDIT')
                
                # Get bmesh from edit mesh
                bm = bmesh.from_edit_mesh(obj.data)
                bm.edges.ensure_lookup_table()
                
                # Count sharp edges first
                sharp_count = sum(1 for edge in bm.edges if not edge.smooth)
                
                if sharp_count == 0:
                    no_sharp_objects.append(obj.name)
                    bpy.ops.object.mode_set(mode='OBJECT')
                    continue
                
                # Store original seams FIRST (before any UV operations)
                original_seam_keys = set()
                for edge in bm.edges:
                    if edge.seam:
                        key = tuple(sorted([v.index for v in edge.verts]))
                        original_seam_keys.add(key)
                
                # Store original UV layer name (not reference, as it might get deleted)
                original_uv_name = obj.data.uv_layers.active.name if obj.data.uv_layers.active else None
                
                # Determine the UV channel management strategy
                total_channels = len(obj.data.uv_layers)
                next_uv_name = get_next_uv_channel_name(obj)
                
                # Remove existing numbered UV layer with the same name if it exists
                existing_numbered_layer = obj.data.uv_layers.get(next_uv_name)
                if existing_numbered_layer:
                    obj.data.uv_layers.remove(existing_numbered_layer)
                    total_channels -= 1
                
                # If we have 8 channels (maximum), delete the last one to make room
                if total_channels >= 8:
                    last_uv_layer = obj.data.uv_layers[-1]
                    obj.data.uv_layers.remove(last_uv_layer)
                
                # Create new numbered UV layer (will be at the highest index now)
                numbered_uv_layer = obj.data.uv_layers.new(name=next_uv_name)
                obj.data.uv_layers.active = numbered_uv_layer
                
                # Clear all seams and set sharp edges as seams
                for edge in bm.edges:
                    edge.seam = not edge.smooth  # Sharp edges become seams
                
                # Update edit mesh
                bmesh.update_edit_mesh(obj.data)
                
                # Select all for unwrapping
                bpy.ops.mesh.select_all(action='SELECT')
                
                # Unwrap to numbered UV layer
                try:
                    bpy.ops.uv.unwrap()
                except Exception as e:
                    failed_objects.append(f"{obj.name} (unwrap failed)")
                
                # Find and switch back to original UV layer by name (if it still exists)
                original_uv_layer = None
                if original_uv_name:
                    original_uv_layer = obj.data.uv_layers.get(original_uv_name)
                
                if original_uv_layer:
                    obj.data.uv_layers.active = original_uv_layer
                elif len(obj.data.uv_layers) > 1:
                    # If original UV was deleted, switch to the first available UV layer (not numbered)
                    for uv_layer in obj.data.uv_layers:
                        if not re.match(r'UVChannel_\d+', uv_layer.name):
                            obj.data.uv_layers.active = uv_layer
                            break
                
                # Refresh bmesh and restore original seams
                bm = bmesh.from_edit_mesh(obj.data)
                bm.edges.ensure_lookup_table()
                bm.verts.ensure_lookup_table()
                
                # Clear all seams
                for edge in bm.edges:
                    edge.seam = False
                
                # Restore original seams using the stored vertex keys
                for edge in bm.edges:
                    key = tuple(sorted([v.index for v in edge.verts]))
                    if key in original_seam_keys:
                        edge.seam = True
                
                bmesh.update_edit_mesh(obj.data)
                
                # Return to object mode
                bpy.ops.object.mode_set(mode='OBJECT')
                
                processed_objects += 1
                
            except Exception as e:
                failed_objects.append(f"{obj.name} ({str(e)})")
                try:
                    bpy.ops.object.mode_set(mode='OBJECT')
                except:
                    pass
        
        # Restore original active object
        if original_active:
            context.view_layer.objects.active = original_active
        
        # Report results
        if processed_objects > 0:
            message = f"Processed {processed_objects}/{len(mesh_objects)} objects"
            if no_sharp_objects:
                message += f". {len(no_sharp_objects)} had no sharp edges"
            if failed_objects:
                message += f". {len(failed_objects)} failed"
            self.report({'INFO'}, message)
        else:
            if no_sharp_objects and not failed_objects:
                self.report({'WARNING'}, f"No sharp edges found on {len(no_sharp_objects)} objects")
            elif failed_objects:
                self.report({'ERROR'}, f"Failed to process objects. Errors: {', '.join(failed_objects[:3])}")
            
        return {'FINISHED'}


class MESH_OT_uv_to_sharp(Operator):
    """Convert numbered UV channel seams back to sharp edges"""
    bl_idname = "mesh.uv_to_sharp"
    bl_label = "UV to Sharp"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.mode == 'OBJECT' and 
                context.selected_objects and 
                any(obj.type == 'MESH' for obj in context.selected_objects))

    def execute(self, context):
        processed_objects = 0
        failed_objects = []
        no_numbered_uv = []
        
        # Store original active object
        original_active = context.view_layer.objects.active
        
        mesh_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        
        for obj in mesh_objects:
            # Find the highest numbered UV layer
            numbered_layer, numbered_index = find_highest_numbered_uv_layer(obj)
            
            if not numbered_layer:
                no_numbered_uv.append(obj.name)
                continue
                
            try:
                # Set as active and enter edit mode
                context.view_layer.objects.active = obj
                bpy.ops.object.mode_set(mode='EDIT')
                
                # Get bmesh from edit mesh
                bm = bmesh.from_edit_mesh(obj.data)
                bm.edges.ensure_lookup_table()
                bm.faces.ensure_lookup_table()
                
                # Get the specific numbered UV layer by index
                if numbered_index >= len(bm.loops.layers.uv):
                    failed_objects.append(f"{obj.name} (UV index out of range)")
                    bpy.ops.object.mode_set(mode='OBJECT')
                    continue
                
                # Access numbered UV layer directly by index
                uv_layer = bm.loops.layers.uv[numbered_index]
                
                if not uv_layer:
                    failed_objects.append(f"{obj.name} (no UV data in numbered channel)")
                    bpy.ops.object.mode_set(mode='OBJECT')
                    continue
                
                # Clear all sharp edges first
                for edge in bm.edges:
                    edge.smooth = True
                
                # Detect UV boundaries and make them sharp (no seam manipulation)
                sharp_count = 0
                for edge in bm.edges:
                    if len(edge.link_faces) == 2:  # Internal edge
                        face1, face2 = edge.link_faces
                        
                        # Get UV coordinates for this edge from both faces
                        edge_verts = edge.verts
                        
                        # Find loops for these vertices in each face
                        face1_uvs = []
                        face2_uvs = []
                        
                        for vert in edge_verts:
                            # Find UV coordinates for this vertex in face1
                            for loop in face1.loops:
                                if loop.vert == vert:
                                    face1_uvs.append(loop[uv_layer].uv[:])
                                    break
                            
                            # Find UV coordinates for this vertex in face2
                            for loop in face2.loops:
                                if loop.vert == vert:
                                    face2_uvs.append(loop[uv_layer].uv[:])
                                    break
                        
                        # Check if UV coordinates are different (discontinuous)
                        if len(face1_uvs) == 2 and len(face2_uvs) == 2:
                            uv_diff_threshold = 0.0001
                            uv1_diff = (abs(face1_uvs[0][0] - face2_uvs[0][0]) > uv_diff_threshold or 
                                       abs(face1_uvs[0][1] - face2_uvs[0][1]) > uv_diff_threshold)
                            uv2_diff = (abs(face1_uvs[1][0] - face2_uvs[1][0]) > uv_diff_threshold or 
                                       abs(face1_uvs[1][1] - face2_uvs[1][1]) > uv_diff_threshold)
                            
                            if uv1_diff or uv2_diff:
                                edge.smooth = False  # Make sharp directly
                                sharp_count += 1
                
                # Update edit mesh
                bmesh.update_edit_mesh(obj.data)
                
                # Return to object mode
                bpy.ops.object.mode_set(mode='OBJECT')
                
                if sharp_count == 0:
                    failed_objects.append(f"{obj.name} (no UV boundaries found)")
                else:
                    processed_objects += 1
                
            except Exception as e:
                failed_objects.append(f"{obj.name} ({str(e)})")
                try:
                    bpy.ops.object.mode_set(mode='OBJECT')
                except:
                    pass
        
        # Restore original active object
        if original_active:
            context.view_layer.objects.active = original_active
        
        # Report results
        total_attempted = len(mesh_objects) - len(no_numbered_uv)
        if processed_objects > 0:
            message = f"Processed {processed_objects}/{total_attempted} objects"
            if no_numbered_uv:
                message += f". {len(no_numbered_uv)} had no numbered UV channels"
            if failed_objects:
                message += f". {len(failed_objects)} failed"
            self.report({'INFO'}, message)
        else:
            if no_numbered_uv:
                self.report({'WARNING'}, f"No numbered UV channels found on {len(no_numbered_uv)} objects")
            if failed_objects:
                self.report({'ERROR'}, f"Failed: {', '.join(failed_objects[:3])}")
            
        return {'FINISHED'}


class MESH_OT_clear_uvsharp(Operator):
    """Clear highest numbered UV channel from selected objects"""
    bl_idname = "mesh.clear_uvsharp"
    bl_label = "Clear UV Channel"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.mode == 'OBJECT' and 
                context.selected_objects and 
                any(obj.type == 'MESH' for obj in context.selected_objects))

    def execute(self, context):
        processed_objects = 0
        mesh_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        
        for obj in mesh_objects:
            # Find the highest numbered UV layer
            numbered_layer, numbered_index = find_highest_numbered_uv_layer(obj)
            
            if numbered_layer:
                obj.data.uv_layers.remove(numbered_layer)
                processed_objects += 1
        
        if processed_objects > 0:
            self.report({'INFO'}, f"Cleared numbered UV channels from {processed_objects}/{len(mesh_objects)} objects")
        else:
            self.report({'INFO'}, "No numbered UV channels found to clear")
            
        return {'FINISHED'}


class VIEW3D_PT_sharp_transfer(Panel):
    """Sharp Transfer Panel"""
    bl_label = "Sharp Transfer"
    bl_idname = "VIEW3D_PT_sharp_transfer"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Sharp Transfer"

    def draw(self, context):
        layout = self.layout
        
        # Main buttons
        col = layout.column(align=True)
        col.scale_y = 1.5
        
        col.operator("mesh.sharp_to_uv", text="Sharp to UV", icon='UV_DATA')
        col.operator("mesh.uv_to_sharp", text="UV to Sharp", icon='MESH_DATA')
        
        layout.separator()
        
        # Clear button
        layout.operator("mesh.clear_uvsharp", text="Clear UV Channel", icon='X')


# Registration
classes = (
    MESH_OT_sharp_to_uv,
    MESH_OT_uv_to_sharp,
    MESH_OT_clear_uvsharp,
    VIEW3D_PT_sharp_transfer,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()