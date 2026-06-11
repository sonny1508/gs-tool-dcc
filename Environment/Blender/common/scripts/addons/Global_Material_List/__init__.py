bl_info = {
    "name": "Global Material List",
    "author": "Sonny",
    "version": (1, 0, 0),
    "blender": (3, 6, 0),
    "location": "View3D > Sidebar > Global Materials",
    "description": "Manage and standardize material order across objects for export compatibility",
    "category": "Material",
}

import bpy
from bpy.props import StringProperty, EnumProperty, CollectionProperty, IntProperty, BoolProperty
from bpy.types import Panel, Operator, PropertyGroup, UIList


EMPTY_MATERIAL_PREFIX = "Empty"


def get_or_create_empty_material(object_name, slot_number):
    """Get or create a unique empty material for specific object and slot"""
    empty_name = f"{EMPTY_MATERIAL_PREFIX}_{object_name}_{slot_number:02d}"
    
    if empty_name in bpy.data.materials:
        return bpy.data.materials[empty_name]
    else:
        # Create the unique empty material
        empty_mat = bpy.data.materials.new(name=empty_name)
        empty_mat.use_fake_user = True  # Prevent automatic deletion
        return empty_mat


def is_empty_material(material_name):
    """Check if a material is an empty material based on naming convention"""
    return material_name.startswith(EMPTY_MATERIAL_PREFIX)


def remove_unused_empty_materials():
    """Remove empty materials that are no longer in use"""
    # Get all empty materials
    empty_materials = [mat for mat in bpy.data.materials if is_empty_material(mat.name)]
    
    # Check which ones are still in use
    materials_in_use = set()
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH' and obj.data.materials:
            for slot in obj.material_slots:
                if slot.material and is_empty_material(slot.material.name):
                    materials_in_use.add(slot.material.name)
    
    # Remove unused empty materials
    removed_count = 0
    for mat in empty_materials:
        if mat.name not in materials_in_use:
            bpy.data.materials.remove(mat)
            removed_count += 1
    
    return removed_count


def get_materials_from_source(context):
    """Get materials based on the selected source (Scene, Selection, or Collection)"""
    scene = context.scene
    materials = []
    
    if scene.material_source_mode == 'SCENE':
        # Get all materials in the scene
        for mat in bpy.data.materials:
            if mat.users > 0 and not is_empty_material(mat.name):
                user_count = mat.users
                materials.append((mat.name, mat, user_count))
    
    elif scene.material_source_mode == 'SELECTION':
        # Get materials from selected objects only
        material_counts = {}
        selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        
        for obj in selected_objects:
            if obj.data.materials:
                for slot in obj.material_slots:
                    if slot.material and not is_empty_material(slot.material.name):
                        mat_name = slot.material.name
                        if mat_name not in material_counts:
                            material_counts[mat_name] = 0
                        material_counts[mat_name] += 1
        
        for mat_name, count in material_counts.items():
            if mat_name in bpy.data.materials:
                mat = bpy.data.materials[mat_name]
                materials.append((mat_name, mat, count))
    
    elif scene.material_source_mode == 'COLLECTION':
        # Get materials from specified collection
        if scene.material_source_collection:
            collection = scene.material_source_collection
            material_counts = {}
            
            for obj in collection.objects:
                if obj.type == 'MESH' and obj.data.materials:
                    for slot in obj.material_slots:
                        if slot.material and not is_empty_material(slot.material.name):
                            mat_name = slot.material.name
                            if mat_name not in material_counts:
                                material_counts[mat_name] = 0
                            material_counts[mat_name] += 1
            
            for mat_name, count in material_counts.items():
                if mat_name in bpy.data.materials:
                    mat = bpy.data.materials[mat_name]
                    materials.append((mat_name, mat, count))
    
    return materials


class MATERIAL_UL_scene_list(UIList):
    """UI List for scene materials (Column 1)"""
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        scene = context.scene
        gml = scene.global_material_list
        
        # Check if this material is in the global list
        is_in_global = any(global_item.material_ref == item.material_ref for global_item in gml.global_material_list)
        
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            # Highlight background if material is in global list
            if is_in_global:
                layout.alert = True  # This gives a red highlight, we'll use a different approach
            
            # Create a row with selection checkbox
            row = layout.row(align=True)
            
            # Selection checkbox
            row.prop(item, "selected", text="")
            
            # Select objects button
            select_op = row.operator("material.select_objects_with_material", text="", icon='RESTRICT_SELECT_OFF')
            select_op.material_name = item.material_ref
            
            # Material name with index
            if is_in_global:
                # Use orange text color for materials in global list
                text_row = row.row()
                text_row.alert = True  # This will make the text orange
                text_row.label(text=f"{item.index:02d}. {item.name}")
            else:
                row.label(text=f"{item.index:02d}. {item.name}")
            
            # User count with icon (double digits)
            user_row = row.row(align=True)
            user_row.alignment = 'RIGHT'
            user_row.label(text=f"{item.user_count:02d}", icon='FAKE_USER_OFF')
            
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.prop(item, "selected", text="")


class MATERIAL_UL_global_list(UIList):
    """UI List for global material order (Column 2)"""
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            # Create a row with selection checkbox
            row = layout.row(align=True)
            
            # Selection checkbox
            row.prop(item, "selected", text="")
            
            # Select objects button
            select_op = row.operator("material.select_objects_with_material", text="", icon='RESTRICT_SELECT_OFF')
            select_op.material_name = item.material_ref
            
            # Material name with index
            row.label(text=f"{item.index:02d}. {item.name}")
            
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.prop(item, "selected", text="")


class MaterialListItem(PropertyGroup):
    """Property group for material list items"""
    name: StringProperty(name="Material Name")
    index: IntProperty(name="Index", default=0)
    user_count: IntProperty(name="User Count", default=0)
    material_ref: StringProperty(name="Material Reference")
    selected: BoolProperty(name="Selected", default=False)


class MATERIAL_OT_select_objects_with_material(Operator):
    """Select all objects that use this material"""
    bl_idname = "material.select_objects_with_material"
    bl_label = "Select Objects with Material"
    bl_description = "Select all objects that use this material"
    
    material_name: StringProperty()
    
    def execute(self, context):
        if self.material_name not in bpy.data.materials:
            self.report({'ERROR'}, f"Material '{self.material_name}' not found")
            return {'CANCELLED'}
        
        material = bpy.data.materials[self.material_name]
        selected_count = 0
        
        # Deselect all first
        bpy.ops.object.select_all(action='DESELECT')
        
        # Select objects using this material
        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH' and obj.data.materials:
                for slot in obj.material_slots:
                    if slot.material == material:
                        obj.select_set(True)
                        selected_count += 1
                        break
        
        self.report({'INFO'}, f"Selected {selected_count} objects using material '{self.material_name}'")
        return {'FINISHED'}


class MATERIAL_OT_add_selected_to_global(Operator):
    """Add selected materials to global list"""
    bl_idname = "material.add_selected_to_global"
    bl_label = "Add Selected to Global List"
    bl_description = "Add all selected materials to the global material list"
    
    def execute(self, context):
        scene = context.scene
        gml = scene.global_material_list
        
        # Get selected materials from scene list
        selected_materials = [item for item in scene.scene_material_list if item.selected]
        
        if not selected_materials:
            self.report({'WARNING'}, "No materials selected")
            return {'CANCELLED'}
        
        added_count = 0
        
        for item in selected_materials:
            # Check if already in global list
            already_exists = any(global_item.material_ref == item.material_ref for global_item in gml.global_material_list)
            
            if not already_exists:
                # Add to global list
                new_item = gml.global_material_list.add()
                new_item.name = item.name
                new_item.material_ref = item.material_ref
                new_item.index = len(gml.global_material_list)
                added_count += 1
            
            # Deselect the item
            item.selected = False
        
        # Update indices
        for i, item in enumerate(gml.global_material_list):
            item.index = i + 1
        
        self.report({'INFO'}, f"Added {added_count} materials to global list")
        return {'FINISHED'}


class MATERIAL_OT_remove_selected_from_global(Operator):
    """Remove selected materials from global list"""
    bl_idname = "material.remove_selected_from_global"
    bl_label = "Remove Selected from Global List"
    bl_description = "Remove all selected materials from the global material list"
    
    def execute(self, context):
        scene = context.scene
        gml = scene.global_material_list
        
        # Get selected materials (in reverse order to avoid index issues)
        selected_indices = []
        for i, item in enumerate(gml.global_material_list):
            if item.selected:
                selected_indices.append(i)
        
        if not selected_indices:
            self.report({'WARNING'}, "No materials selected")
            return {'CANCELLED'}
        
        # Remove in reverse order
        for idx in reversed(selected_indices):
            gml.global_material_list.remove(idx)
        
        # Update indices
        for i, item in enumerate(gml.global_material_list):
            item.index = i + 1
        
        # Adjust active index
        if gml.global_material_active_index >= len(gml.global_material_list):
            gml.global_material_active_index = len(gml.global_material_list) - 1
        
        self.report({'INFO'}, f"Removed {len(selected_indices)} materials from global list")
        return {'FINISHED'}


class MATERIAL_OT_select_all_scene_materials(Operator):
    """Select/Deselect all scene materials"""
    bl_idname = "material.select_all_scene_materials"
    bl_label = "Select/Deselect All"
    bl_description = "Toggle selection of all scene materials"
    
    def execute(self, context):
        scene = context.scene
        
        # Check if any are selected
        any_selected = any(item.selected for item in scene.scene_material_list)
        
        # If any selected, deselect all; otherwise select all
        new_state = not any_selected
        
        for item in scene.scene_material_list:
            item.selected = new_state
        
        action = "Selected" if new_state else "Deselected"
        self.report({'INFO'}, f"{action} all scene materials")
        return {'FINISHED'}


class MATERIAL_OT_select_all_global_materials(Operator):
    """Select/Deselect all global materials"""
    bl_idname = "material.select_all_global_materials"
    bl_label = "Select/Deselect All"
    bl_description = "Toggle selection of all global materials"
    
    def execute(self, context):
        scene = context.scene
        gml = scene.global_material_list
        
        # Check if any are selected
        any_selected = any(item.selected for item in gml.global_material_list)
        
        # If any selected, deselect all; otherwise select all
        new_state = not any_selected
        
        for item in gml.global_material_list:
            item.selected = new_state
        
        action = "Selected" if new_state else "Deselected"
        self.report({'INFO'}, f"{action} all global materials")
        return {'FINISHED'}


class MATERIAL_OT_move_global_item(Operator):
    """Move item in global list"""
    bl_idname = "material.move_global_item"
    bl_label = "Move Global Item"
    bl_description = "Move item up or down in the global material list"
    
    direction: EnumProperty(
        items=[('UP', 'Up', ''), ('DOWN', 'Down', '')],
        default='UP'
    )
    
    def execute(self, context):
        scene = context.scene
        gml = scene.global_material_list
        active_index = gml.global_material_active_index
        
        if self.direction == 'UP' and active_index > 0:
            gml.global_material_list.move(active_index, active_index - 1)
            gml.global_material_active_index -= 1
        elif self.direction == 'DOWN' and active_index < len(gml.global_material_list) - 1:
            gml.global_material_list.move(active_index, active_index + 1)
            gml.global_material_active_index += 1
        
        # Update indices
        for i, item in enumerate(gml.global_material_list):
            item.index = i + 1
        
        return {'FINISHED'}


class MATERIAL_OT_auto_refresh(Operator):
    """Auto refresh when source mode changes"""
    bl_idname = "material.auto_refresh"
    bl_label = "Auto Refresh"
    bl_description = "Automatically refresh material list when source changes"
    
    def execute(self, context):
        bpy.ops.material.refresh_scene_list()
        return {'FINISHED'}


class MATERIAL_OT_refresh_scene_list(Operator):
    """Refresh the scene material list"""
    bl_idname = "material.refresh_scene_list"
    bl_label = "Refresh Scene Materials"
    bl_description = "Refresh the list of materials in the scene"
    
    def execute(self, context):
        scene = context.scene
        scene.scene_material_list.clear()
        
        # Get materials based on selected source
        materials = get_materials_from_source(context)
        
        if not materials:
            if scene.material_source_mode == 'SELECTION':
                self.report({'WARNING'}, "No materials found in selected objects")
            elif scene.material_source_mode == 'COLLECTION':
                if scene.material_source_collection:
                    self.report({'WARNING'}, f"No materials found in collection '{scene.material_source_collection.name}'")
                else:
                    self.report({'WARNING'}, "No collection selected")
            else:
                self.report({'WARNING'}, "No materials found in scene")
            return {'FINISHED'}
        
        # Sort based on preference
        if scene.material_sort_mode == 'ALPHABETICAL':
            materials.sort(key=lambda x: x[0].lower())
        elif scene.material_sort_mode == 'USER_COUNT':
            materials.sort(key=lambda x: x[2], reverse=True)
        
        # Populate the list
        for i, (name, mat, user_count) in enumerate(materials):
            item = scene.scene_material_list.add()
            item.name = name
            item.index = i + 1
            item.user_count = user_count
            item.material_ref = mat.name
            item.selected = False
        
        # Update UI feedback
        source_text = {
            'SCENE': 'scene',
            'SELECTION': 'selected objects', 
            'COLLECTION': f"collection '{scene.material_source_collection.name}'" if scene.material_source_collection else 'collection'
        }
        self.report({'INFO'}, f"Found {len(materials)} materials in {source_text[scene.material_source_mode]}")
        
        return {'FINISHED'}


class MATERIAL_OT_rearrange_to_global(Operator):
    """Rearrange materials in selected objects to match global list"""
    bl_idname = "material.rearrange_to_global"
    bl_label = "Rearrange to Global Material List"
    bl_description = "Rearrange material slots in selected objects to match the global material list order"
    
    def execute(self, context):
        scene = context.scene
        gml = scene.global_material_list
        
        if not gml.global_material_list:
            self.report({'ERROR'}, "Global material list is empty")
            return {'CANCELLED'}
        
        selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        
        if not selected_objects:
            self.report({'ERROR'}, "No mesh objects selected")
            return {'CANCELLED'}
        
        # Create material reference dictionary
        global_materials = {}
        for i, item in enumerate(gml.global_material_list):
            if item.material_ref in bpy.data.materials:
                global_materials[item.material_ref] = i
        
        processed_objects = 0
        
        for obj in selected_objects:
            if not obj.data.materials:
                continue
            
            # Store current material assignments per face
            face_materials = []
            if obj.data.polygons:
                for poly in obj.data.polygons:
                    face_materials.append(poly.material_index)
            
            # Get current materials
            current_materials = [slot.material for slot in obj.material_slots]
            
            # Create mapping from old index to new index and find which global materials this object uses
            old_to_new_index = {}
            used_global_indices = set()
            
            # First pass: identify which global materials are used by this object
            for old_idx, mat in enumerate(current_materials):
                if mat and mat.name in global_materials:
                    new_idx = global_materials[mat.name]
                    old_to_new_index[old_idx] = new_idx
                    used_global_indices.add(new_idx)
            
            # Find the highest used index (smart cutoff)
            if not used_global_indices:
                continue  # Object doesn't use any materials from global list
            
            max_used_index = max(used_global_indices)
            
            # Create new material list only up to the highest used index
            new_materials = [None] * (max_used_index + 1)
            
            # Fill in the materials
            for old_idx, mat in enumerate(current_materials):
                if mat and mat.name in global_materials:
                    new_idx = global_materials[mat.name]
                    if new_idx <= max_used_index:  # Only add if within our cutoff
                        new_materials[new_idx] = mat
            
            # Fill empty slots with unique empty materials
            for i in range(len(new_materials)):
                if new_materials[i] is None:
                    # Create unique empty material for this object and slot
                    empty_material = get_or_create_empty_material(obj.name, i + 1)
                    new_materials[i] = empty_material
            
            # Clear existing material slots
            obj.data.materials.clear()
            
            # Add materials in global order
            for mat in new_materials:
                obj.data.materials.append(mat)
            
            # Update face material indices
            if face_materials:
                for poly_idx, old_mat_idx in enumerate(face_materials):
                    if old_mat_idx in old_to_new_index:
                        obj.data.polygons[poly_idx].material_index = old_to_new_index[old_mat_idx]
                    else:
                        obj.data.polygons[poly_idx].material_index = 0  # Default to first slot
            
            processed_objects += 1
        
        self.report({'INFO'}, f"Rearranged materials for {processed_objects} objects")
        return {'FINISHED'}


class MATERIAL_OT_delete_empty_slots(Operator):
    """Delete empty material slots from selected objects"""
    bl_idname = "material.delete_empty_slots"
    bl_label = "Delete Empty Material Slots"
    bl_description = "Remove empty material slots from selected objects and clean up unused empty materials"
    
    def execute(self, context):
        selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        
        if not selected_objects:
            self.report({'ERROR'}, "No mesh objects selected")
            return {'CANCELLED'}
        
        total_removed = 0
        
        for obj in selected_objects:
            if not obj.data.materials:
                continue
            
            # Collect non-empty materials and their old indices (excluding empty materials)
            non_empty_materials = []
            old_to_new_index = {}
            
            for old_idx, slot in enumerate(obj.material_slots):
                if slot.material is not None and not is_empty_material(slot.material.name):
                    new_idx = len(non_empty_materials)
                    old_to_new_index[old_idx] = new_idx
                    non_empty_materials.append(slot.material)
            
            removed_count = len(obj.material_slots) - len(non_empty_materials)
            total_removed += removed_count
            
            if removed_count > 0:
                # Store face material assignments
                face_materials = []
                if obj.data.polygons:
                    for poly in obj.data.polygons:
                        face_materials.append(poly.material_index)
                
                # Clear and rebuild material slots
                obj.data.materials.clear()
                for mat in non_empty_materials:
                    obj.data.materials.append(mat)
                
                # Update face material indices
                if face_materials:
                    for poly_idx, old_mat_idx in enumerate(face_materials):
                        if old_mat_idx in old_to_new_index:
                            obj.data.polygons[poly_idx].material_index = old_to_new_index[old_mat_idx]
                        else:
                            obj.data.polygons[poly_idx].material_index = 0
        
        # Clean up unused empty materials
        removed_empty_count = remove_unused_empty_materials()
        
        total_message = f"Removed {total_removed} empty material slots"
        if removed_empty_count > 0:
            total_message += f" and cleaned up {removed_empty_count} unused empty materials"
        
        self.report({'INFO'}, total_message)
        return {'FINISHED'}


class MATERIAL_OT_cleanup_empty_materials(Operator):
    """Clean up all unused empty materials in the scene"""
    bl_idname = "material.cleanup_empty_materials"
    bl_label = "Cleanup Unused Empty Materials"
    bl_description = "Remove all empty materials that are not being used by any objects"
    
    def execute(self, context):
        removed_count = remove_unused_empty_materials()
        
        if removed_count > 0:
            self.report({'INFO'}, f"Cleaned up {removed_count} unused empty materials")
        else:
            self.report({'INFO'}, "No unused empty materials found")
        
        return {'FINISHED'}


class GlobalMaterialListProperties(PropertyGroup):
    """Properties for the Global Material List"""
    global_material_list: CollectionProperty(type=MaterialListItem)
    global_material_active_index: IntProperty(default=0)


class MATERIAL_PT_global_material_list(Panel):
    """Main panel for Global Material List"""
    bl_label = "Global Material List"
    bl_idname = "MATERIAL_PT_global_material_list"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Global Materials"
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        gml = scene.global_material_list
        
        # Header info
        # row = layout.row()
        # row.label(text="Global Material Order for Export")
        
        # Two-column layout for controls
        split = layout.split(factor=0.5)
        
        # Controls constrained to first column width
        controls_col = split.column()
        
        # Material source and sort options
        row = controls_col.row()
        row.prop(scene, "material_source_mode", text="Materials")
        
        row = controls_col.row()
        row.prop(scene, "material_sort_mode", text="Sort by")

        row = controls_col.row()
        row.label(text="")
        row.operator("material.refresh_scene_list", text="Refresh", icon='FILE_REFRESH')

        row = controls_col.row()
        row.label(text="")
        # layout.seperator()
        
        # Show collection picker when Collection mode is selected
        if scene.material_source_mode == 'COLLECTION':
            row = controls_col.row()
            row.prop(scene, "material_source_collection", text="Collection")
        
        # Empty second column for spacing
        split.column()
        
        # Main two-column layout for material lists
        split = layout.split(factor=0.5)
        
        # Column 1: Scene Materials
        col1 = split.column()
        
        # Dynamic label based on source
        source_labels = {
            'SCENE': "Scene Materials",
            'SELECTION': "Selection Materials", 
            'COLLECTION': f"Collection Materials" + (f" ({scene.material_source_collection.name})" if scene.material_source_collection else "")
        }
        col1.label(text=source_labels[scene.material_source_mode])
        col1.template_list(
            "MATERIAL_UL_scene_list",
            "",
            scene,
            "scene_material_list",
            scene,
            "scene_material_active_index",
            rows=8
        )
        
        # Scene materials controls
        row = col1.row(align=True)
        row.operator("material.select_all_scene_materials", text="Select All/None", icon='CHECKBOX_HLT')
        
        row = col1.row(align=True)
        row.operator("material.add_selected_to_global", text="Add Selected to Global →", icon='ADD')
        
        # Column 2: Global Material List
        col2 = split.column()
        col2.label(text=f"Global List ({len(gml.global_material_list)} materials)")
        col2.template_list(
            "MATERIAL_UL_global_list",
            "",
            gml,
            "global_material_list",
            gml,
            "global_material_active_index",
            rows=8
        )
        
        # Global list controls
        row = col2.row(align=True)
        row.operator("material.select_all_global_materials", text="Select All/None", icon='CHECKBOX_HLT')
        
        row = col2.row(align=True)
        row.operator("material.move_global_item", text="↑", icon='TRIA_UP').direction = 'UP'
        row.operator("material.move_global_item", text="↓", icon='TRIA_DOWN').direction = 'DOWN'
        row.operator("material.remove_selected_from_global", text="Remove Selected", icon='REMOVE')
        
        # Action buttons
        layout.separator()
        row = layout.row(align=True)
        row.scale_y = 1.5
        row.operator("material.rearrange_to_global", text="Rearrange to Global Material List", icon='SORTBYEXT')
        
        row = layout.row(align=True)
        row.operator("material.delete_empty_slots", text="Delete Empty Material Slots", icon='TRASH')
        
        # Cleanup button
        row = layout.row(align=True)
        row.operator("material.cleanup_empty_materials", text="Cleanup Unused Empty Materials", icon='BRUSH_DATA')
        
        # Info box
        # box = layout.box()
        # box.label(text="Instructions:", icon='INFO')
        # box.label(text="• Choose material source: Scene/Selection/Collection")
        # box.label(text="• Select materials using checkboxes")
        # box.label(text="• Click select icon to select objects with material")
        # box.label(text="• Orange text = material in global list")
        # box.label(text="• Select objects and rearrange to match global order")


# Property registration
def register():
    bpy.utils.register_class(MaterialListItem)
    bpy.utils.register_class(GlobalMaterialListProperties)
    bpy.utils.register_class(MATERIAL_UL_scene_list)
    bpy.utils.register_class(MATERIAL_UL_global_list)
    bpy.utils.register_class(MATERIAL_OT_select_objects_with_material)
    bpy.utils.register_class(MATERIAL_OT_add_selected_to_global)
    bpy.utils.register_class(MATERIAL_OT_remove_selected_from_global)
    bpy.utils.register_class(MATERIAL_OT_select_all_scene_materials)
    bpy.utils.register_class(MATERIAL_OT_select_all_global_materials)
    bpy.utils.register_class(MATERIAL_OT_move_global_item)
    bpy.utils.register_class(MATERIAL_OT_auto_refresh)
    bpy.utils.register_class(MATERIAL_OT_refresh_scene_list)
    bpy.utils.register_class(MATERIAL_OT_rearrange_to_global)
    bpy.utils.register_class(MATERIAL_OT_delete_empty_slots)
    # bpy.utils.register_class(MATERIAL_OT_cleanup_empty_materials)
    bpy.utils.register_class(MATERIAL_PT_global_material_list)
    
    # Scene properties
    bpy.types.Scene.global_material_list = bpy.props.PointerProperty(type=GlobalMaterialListProperties)
    bpy.types.Scene.scene_material_list = CollectionProperty(type=MaterialListItem)
    bpy.types.Scene.scene_material_active_index = IntProperty(default=0)
    bpy.types.Scene.material_sort_mode = EnumProperty(
        name="Sort Mode",
        items=[
            ('ALPHABETICAL', 'Alphabetical', 'Sort materials alphabetically'),
            ('USER_COUNT', 'User Count', 'Sort by number of users (descending)')
        ],
        default='ALPHABETICAL'
    )
    bpy.types.Scene.material_source_mode = EnumProperty(
        name="Material Source",
        items=[
            ('SCENE', 'Scene', 'Show all materials in the scene'),
            ('SELECTION', 'Selection', 'Show materials from selected objects only'),
            ('COLLECTION', 'Collection', 'Show materials from a specific collection')
        ],
        default='SCENE',
        description="Choose which materials to display",
        update=lambda self, context: bpy.ops.material.auto_refresh()
    )
    bpy.types.Scene.material_source_collection = bpy.props.PointerProperty(
        type=bpy.types.Collection,
        name="Collection", 
        description="Collection to get materials from",
        update=lambda self, context: bpy.ops.material.auto_refresh() if context.scene.material_source_mode == 'COLLECTION' else None
    )


def unregister():
    bpy.utils.unregister_class(MATERIAL_PT_global_material_list)
    # bpy.utils.unregister_class(MATERIAL_OT_cleanup_empty_materials)
    bpy.utils.unregister_class(MATERIAL_OT_delete_empty_slots)
    bpy.utils.unregister_class(MATERIAL_OT_rearrange_to_global)
    bpy.utils.unregister_class(MATERIAL_OT_refresh_scene_list)
    bpy.utils.unregister_class(MATERIAL_OT_auto_refresh)
    bpy.utils.unregister_class(MATERIAL_OT_move_global_item)
    bpy.utils.unregister_class(MATERIAL_OT_select_all_global_materials)
    bpy.utils.unregister_class(MATERIAL_OT_select_all_scene_materials)
    bpy.utils.unregister_class(MATERIAL_OT_remove_selected_from_global)
    bpy.utils.unregister_class(MATERIAL_OT_add_selected_to_global)
    bpy.utils.unregister_class(MATERIAL_OT_select_objects_with_material)
    bpy.utils.unregister_class(MATERIAL_UL_global_list)
    bpy.utils.unregister_class(MATERIAL_UL_scene_list)
    bpy.utils.unregister_class(GlobalMaterialListProperties)
    bpy.utils.unregister_class(MaterialListItem)
    
    del bpy.types.Scene.material_source_collection
    del bpy.types.Scene.material_source_mode
    del bpy.types.Scene.material_sort_mode
    del bpy.types.Scene.scene_material_active_index
    del bpy.types.Scene.scene_material_list
    del bpy.types.Scene.global_material_list


if __name__ == "__main__":
    register()