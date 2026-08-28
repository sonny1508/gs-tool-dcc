import bpy
import bmesh
from mathutils import Vector, kdtree
from mathutils.bvhtree import BVHTree
from bpy.types import Operator
import math
from functools import wraps

# ----------------------- HELPER FUNCTIONS -----------------------
def report_validation_results(self, issue_count, affected_objects, issue_type, select_mode=None):
    """
    Standard function for reporting validation results and handling mode
    
    Parameters:
    - issue_count: Number of issues found
    - affected_objects: List of object names with issues 
    - issue_type: Description of the issue (e.g., "duplicate vertices")
    - select_mode: If issues found, what select mode to use in edit mode ('VERT', 'EDGE', 'FACE' or None)
    
    Returns:
    - Blender operator result
    """
    if issue_count > 0:
        self.report({'WARNING'}, f"Found {issue_count} {issue_type} in {len(affected_objects)} objects.")
        bpy.ops.object.mode_set(mode='EDIT')
        if select_mode:
            bpy.ops.mesh.select_mode(type=select_mode)
    else:
        self.report({'INFO'}, f"No {issue_type} found.")
        bpy.ops.object.mode_set(mode='OBJECT')  # Return to object mode if no issues
    
    return {'FINISHED'}

def validate_mesh_property(self, context, validation_func, issue_type, select_mode=None):
    """
    Generic framework for mesh property validation
    
    Parameters:
    - validation_func: Function that takes an object and returns (issue_count, has_selected_elements)
    - issue_type: Description of what's being validated
    - select_mode: Edit mode select type if issues found
    """
    # Initial setup
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    
    issue_count = 0
    affected_objects = []
    
    # Apply validation to each object
    for obj in context.selected_objects:
        if obj.type == 'MESH':
            obj_issues, has_selection = validation_func(obj)
            if obj_issues > 0:
                issue_count += obj_issues
                affected_objects.append(obj.name)
    
    return report_validation_results(self, issue_count, affected_objects, issue_type, select_mode)

def save_selection_state():
    """Save the current selection state and active object"""
    active_obj = bpy.context.active_object
    selected_objs = [obj for obj in bpy.context.selected_objects]
    return active_obj, selected_objs

def restore_selection_state(active_obj, selected_objs):
    """Restore a previously saved selection state"""
    # Ensure we're in Object mode first
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    
    bpy.ops.object.select_all(action='DESELECT')
    
    for obj in selected_objs:
        if obj.name in bpy.data.objects:
            obj.select_set(True)
            
    if active_obj and active_obj.name in bpy.data.objects:
        bpy.context.view_layer.objects.active = active_obj

# Standard poll method for mesh object validation
def standard_mesh_poll(cls, context):
    objs = context.selected_objects
    result = all(obj.type == 'MESH' for obj in objs)
    
    result2 = []
    for obj in objs:
        if context.active_object == obj:
            result2.append(obj)
    if result is True and len(objs) >= 1 and len(result2) >= 1:
        return True
    return False

# Poll method for two or more mesh objects
def two_mesh_poll(cls, context):
    objs = context.selected_objects
    result = all(obj.type == 'MESH' for obj in objs)
    
    result2 = []
    for obj in objs:
        if context.active_object == obj:
            result2.append(obj)
    if result is True and len(objs) >= 2 and len(result2) >= 1:
        return True
    return False

# ----------- Duplicate Vertex -----------
def duplicate_vertex_one_object(self, context):
    # Deselect all vertices before checking
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

    # Create a set to store vertex positions
    vertex_positions = set()
    duplicate_count = 0
    objects_with_duplicates = []
    
    # Loop through selected objects
    for obj in context.selected_objects:
        # Check if the object is a mesh
        if obj.type == 'MESH':
            obj_duplicate_count = 0
            # Loop through vertices of the object
            for vertex in obj.data.vertices:
                # Get position (x, y, z) of the vertex
                x, y, z = obj.matrix_world @ vertex.co
                
                threshold = 4  # Round to 4 decimal places
                # Create a key from vertex position
                position_key = round(x, threshold), round(y, threshold), round(z, threshold)
                # Check if vertex position already exists in the list
                if position_key in vertex_positions:
                    # If already exists, select vertex
                    vertex.select = True
                    duplicate_count += 1
                    obj_duplicate_count += 1
                else:
                    # If not exists, add position to the list
                    vertex_positions.add(position_key)
            
            if obj_duplicate_count > 0:
                objects_with_duplicates.append(obj.name)

    return report_validation_results(self, duplicate_count, objects_with_duplicates, "duplicate vertices", 'VERT')

# ----------- Plane Overlap -----------
def meshes_overlap(self, context):
    """Check for overlapping polygons between objects using direct geometric tests"""
    # Ensure we have at least two selected mesh objects
    selected_mesh_objects = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH']
    
    if len(selected_mesh_objects) < 2:
        self.report({'WARNING'}, "Please select at least two mesh objects")
        return {'CANCELLED'}
    
    # Function to get polygon data in world space
    def get_polygon_data(obj):
        # Get a copy of the mesh
        mesh = obj.data
        world_matrix = obj.matrix_world
        
        # Create a bmesh
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bm.faces.ensure_lookup_table()
        
        polygon_data = []
        
        # Process each face
        for face_idx, face in enumerate(bm.faces):
            verts_world = [world_matrix @ v.co for v in face.verts]
            normal_world = (world_matrix.inverted().transposed() @ Vector((face.normal.x, face.normal.y, face.normal.z, 0))).xyz.normalized()
            
            # Calculate face center
            center_world = sum(verts_world, Vector((0,0,0))) / len(verts_world)
            
            # Store face plane equation: ax + by + cz + d = 0
            a, b, c = normal_world
            d = -center_world.dot(normal_world)
            
            polygon_data.append({
                'object': obj,
                'face_idx': face_idx,
                'verts': verts_world,
                'normal': normal_world,
                'center': center_world,
                'plane': (a, b, c, d),
                'original_face': face
            })
        
        bm.free()
        return polygon_data
    
    # Get face data for all objects
    all_polygon_data = []
    for obj in selected_mesh_objects:
        all_polygon_data.extend(get_polygon_data(obj))
    
    # Function to check if two polygons overlap
    def meshes_overlap(poly1, poly2):
        # First, check if polygons are roughly coplanar
        plane1 = poly1['plane']
        plane2 = poly2['plane']
        
        # Check if normals are parallel (or anti-parallel)
        normal1 = poly1['normal']
        normal2 = poly2['normal']
        
        # If from same object, skip
        if poly1['object'] == poly2['object']:
            return False
        
        dot_product = normal1.dot(normal2)
        # Allow for both parallel and anti-parallel normals
        if abs(abs(dot_product) - 1.0) > 0.01:
            return False  # Normals not parallel or anti-parallel
        
        # Check if planes are close enough
        d1 = plane1[3]
        d2 = plane2[3]
        
        # Normalize the plane equations for comparison
        norm1 = math.sqrt(plane1[0]**2 + plane1[1]**2 + plane1[2]**2)
        norm2 = math.sqrt(plane2[0]**2 + plane2[1]**2 + plane2[2]**2)
        
        # Adjust d values
        d1_norm = d1 / norm1 if norm1 != 0 else 0
        d2_norm = d2 / norm2 if norm2 != 0 else 0
        
        # If planes are too far apart, they don't overlap
        if abs(d1_norm - d2_norm) > 0.001:
            return False
            
        # Project all vertices to a common plane and check for 2D overlap
        # Use normal for projection axis
        projection_normal = normal1
        
        # If normals are in opposite directions, flip one
        if dot_product < 0:
            normal2 = -normal2
        
        # Create projection axes (an orthogonal basis in the plane)
        # Find a perpendicular vector to the normal
        if abs(projection_normal.x) > abs(projection_normal.y):
            perp1 = Vector((-projection_normal.z, 0, projection_normal.x)).normalized()
        else:
            perp1 = Vector((0, -projection_normal.z, projection_normal.y)).normalized()
        
        # Get the second perpendicular vector using cross product
        perp2 = projection_normal.cross(perp1).normalized()
        
        # Project vertices to 2D
        def project_to_2d(vertices):
            return [(v.dot(perp1), v.dot(perp2)) for v in vertices]
        
        verts1_2d = project_to_2d(poly1['verts'])
        verts2_2d = project_to_2d(poly2['verts'])
        
        # Check if 2D polygons overlap
        # Use a simple approach: check if any vertex of one polygon is inside the other
        def is_point_in_polygon(point, polygon):
            # Ray casting algorithm for point-in-polygon test
            x, y = point
            inside = False
            n = len(polygon)
            j = n - 1
            
            for i in range(n):
                (xi, yi) = polygon[i]
                (xj, yj) = polygon[j]
                
                if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
                    inside = not inside
                    
                j = i
                
            return inside
        
        # Check if any vertex of poly1 is inside poly2
        for point in verts1_2d:
            if is_point_in_polygon(point, verts2_2d):
                return True
                
        # Check if any vertex of poly2 is inside poly1
        for point in verts2_2d:
            if is_point_in_polygon(point, verts1_2d):
                return True
                
        # Check for edge intersections
        def edges_intersect(edge1, edge2):
            p1, p2 = edge1
            p3, p4 = edge2
            
            def ccw(a, b, c):
                return (c[1] - a[1]) * (b[0] - a[0]) > (b[1] - a[1]) * (c[0] - a[0])
            
            return ccw(p1, p3, p4) != ccw(p2, p3, p4) and ccw(p1, p2, p3) != ccw(p1, p2, p4)
        
        # Create edges for both polygons
        edges1 = [(verts1_2d[i], verts1_2d[(i + 1) % len(verts1_2d)]) for i in range(len(verts1_2d))]
        edges2 = [(verts2_2d[i], verts2_2d[(i + 1) % len(verts2_2d)]) for i in range(len(verts2_2d))]
        
        # Check for intersections
        for edge1 in edges1:
            for edge2 in edges2:
                if edges_intersect(edge1, edge2):
                    return True
        
        return False
    
    # Find overlapping polygons
    overlapping_polygons = {}  # object name -> list of face indices
    
    # Check each pair of faces
    num_faces = len(all_polygon_data)
    for i in range(num_faces):
        for j in range(i + 1, num_faces):
            if meshes_overlap(all_polygon_data[i], all_polygon_data[j]):
                # Add both faces to the results
                obj1 = all_polygon_data[i]['object']
                obj2 = all_polygon_data[j]['object']
                face_idx1 = all_polygon_data[i]['face_idx']
                face_idx2 = all_polygon_data[j]['face_idx']
                
                if obj1.name not in overlapping_polygons:
                    overlapping_polygons[obj1.name] = []
                if obj2.name not in overlapping_polygons:
                    overlapping_polygons[obj2.name] = []
                
                overlapping_polygons[obj1.name].append(face_idx1)
                overlapping_polygons[obj2.name].append(face_idx2)
    
    # If no overlaps found
    if not overlapping_polygons:
        self.report({'INFO'}, "No overlapping polygons found between selected objects")
        bpy.ops.object.mode_set(mode='OBJECT')  # Return to object mode if no issues
        return {'FINISHED'}
    
    # Select overlapping faces
    # First deselect all
    bpy.ops.object.mode_set(mode='OBJECT')
    
    total_overlapping_polygons = 0
    objects_with_overlaps = []
    
    for obj_name, face_indices in overlapping_polygons.items():
        # Remove duplicates
        face_indices = list(set(face_indices))
        total_overlapping_polygons += len(face_indices)
        objects_with_overlaps.append(obj_name)
        
        # Select the object
        obj = bpy.data.objects[obj_name]
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        
        # Select faces
        for face_idx in face_indices:
            if face_idx < len(obj.data.polygons):
                obj.data.polygons[face_idx].select = True
    
    # Go to edit mode to show selections
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='FACE')
    
    # Report results
    self.report({'WARNING'}, f"Found {total_overlapping_polygons} overlapping polygons in {len(objects_with_overlaps)} objects")
    
    return {'FINISHED'}

# ----------- N-GON Check -----------
obj_ngon_global = []
obj_ngon_count = -1

def ngon(self, context):
    # Store original selection
    original_active, original_selected = save_selection_state()
    
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_mode(type='FACE')
    bpy.ops.object.mode_set(mode='OBJECT')

    objs = context.selected_objects

    check_global = 0
    obj_ngon_local = []
    objects_with_ngons = []
    
    # First check all objects for N-gons
    for obj in objs:
        if obj.type == 'MESH':
            p_array = []
            for p in obj.data.polygons:
                p.select = len(p.vertices) > 4
                p_array.append(len(p.vertices))
            
            local = 0
            for k in p_array:
                if k > 4:
                    local += 1
                    check_global += 1  
            
            if local > 0:
                objects_with_ngons.append(obj)
                obj_ngon_local.append(obj.name)
    
    # Now select only objects with n-gons
    if check_global > 0:
        bpy.ops.object.select_all(action='DESELECT')
        
        # Select only the objects with N-gons and set the first one active
        for obj in objects_with_ngons:
            obj.select_set(True)
            
        if objects_with_ngons:
            context.view_layer.objects.active = objects_with_ngons[0]
        
        bpy.ops.object.mode_set(mode='EDIT')
        self.report({'WARNING'}, f"Found {check_global} N-Gons in {len(obj_ngon_local)} objects.")
    else:
        # No n-gons found, restore original selection
        restore_selection_state(original_active, original_selected)
        self.report({'INFO'}, "No N-Gons found.")
        bpy.ops.object.mode_set(mode='OBJECT')  # Return to object mode if no issues
        
    global obj_ngon_global
    global obj_ngon_count
    obj_ngon_global[:] = obj_ngon_local
    obj_ngon_count = len(obj_ngon_global)
    return {'FINISHED'}

# ----------- Asymmetric Check -----------
def asymmetric_vert(self, context):
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

    selected_object_name = []
    for obj in bpy.context.selected_objects:
        selected_object_name.append(obj.name)
        
    bpy.ops.object.select_all(action='DESELECT')

    total_asymmetric = 0
    objects_with_asymmetric = []

    for obj_name in selected_object_name:
        obj = bpy.data.objects[obj_name]
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj

        bpy.ops.object.mode_set(mode='EDIT')
        
        positive_x = []
        negative_x = []
        positive_x_dict = {}
        negative_x_dict = {}

        me = obj.data
        bm = bmesh.from_edit_mesh(me)
        bm.verts.ensure_lookup_table() 

        for v in bm.verts:
            if v.co[0] >= 0:
                positive_x.append(v.index)

        for v in bm.verts:
            if v.co[0] <= 0:
                negative_x.append(v.index)

        for i, v in enumerate(positive_x):
            vert_pos = obj.matrix_world @ me.vertices[v].co
            
            rounded_coords = []

            for coord in vert_pos:
                rounded_coords.append(round(coord, 3))
            new_tuple = tuple(rounded_coords)

            positive_x_dict[v] = new_tuple

        for i, v in enumerate(negative_x):
            vert_pos = obj.matrix_world @ me.vertices[v].co
            vert_pos[0] = abs(vert_pos[0])
            
            rounded_coords = []

            for coord in vert_pos:
                rounded_coords.append(round(coord, 3))
            new_tuple = tuple(rounded_coords)

            negative_x_dict[v] = new_tuple
            
        different_value = []
        value_to_keys = {}
        for key, value in positive_x_dict.items():
            value_to_keys.setdefault(value, []).append(key)

        for key, value in negative_x_dict.items():
            if value in value_to_keys:
                different_value.extend(value_to_keys[value] + [key])

        obj_asymmetric = len(bm.verts) - len(different_value)
        if obj_asymmetric > 0:
            total_asymmetric += obj_asymmetric
            objects_with_asymmetric.append(obj_name)
                
        for value in different_value:
            bm.verts[value].select = True

        bpy.ops.mesh.select_all(action='INVERT')
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')

    for obj_name in selected_object_name:
        obj = bpy.data.objects[obj_name]
        obj.select_set(True)
        
    return report_validation_results(self, total_asymmetric, objects_with_asymmetric, "asymmetric vertices", 'VERT')

def asymmetric_face(self, context):
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

    selected_object_name = []
    for obj in bpy.context.selected_objects:
        selected_object_name.append(obj.name)
        
    bpy.ops.object.select_all(action='DESELECT')

    # Track if any asymmetric faces were found
    has_asymmetric_faces = False
    objects_with_asymmetric = []

    for obj_name in selected_object_name:
        obj = bpy.data.objects[obj_name]
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj

        bpy.ops.object.mode_set(mode='EDIT')
        
        # Get initial face count to compare later
        me = obj.data
        bm = bmesh.from_edit_mesh(me)
        initial_faces_selected = sum(1 for f in bm.faces if f.select)

        for v in bm.verts:
            if v.co[0] >= 0:
                v.select = True
                
        bmesh.update_edit_mesh(me)
        bpy.ops.mesh.select_mode(use_extend=True, use_expand=False, type='FACE')
        bpy.ops.mesh.select_mode(use_extend=True, use_expand=False, type='VERT')
        bpy.ops.mesh.select_mirror(extend=True)
        bpy.ops.mesh.select_all(action='INVERT')
        bpy.ops.mesh.hide(unselected=False)
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
        
        for v in bm.verts:
            if v.co[0] <= 0:
                v.select = True
            
        bmesh.update_edit_mesh(me)
        bpy.ops.mesh.select_mode(use_extend=True, use_expand=False, type='FACE')
        bpy.ops.mesh.select_mode(use_extend=True, use_expand=False, type='VERT')
        bpy.ops.mesh.select_mirror(extend=True)
        bpy.ops.mesh.select_all(action='INVERT')
        bpy.ops.mesh.hide(unselected=False)
        bpy.ops.mesh.reveal()
        
        # Check if any faces are selected now
        faces_selected = sum(1 for f in bm.faces if f.select)
        if faces_selected > initial_faces_selected:
            has_asymmetric_faces = True
            objects_with_asymmetric.append(obj_name)
        
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')

    for obj_name in selected_object_name:
        obj = bpy.data.objects[obj_name]
        obj.select_set(True)
    
    if has_asymmetric_faces:
        self.report({'WARNING'}, f"Found asymmetric faces in {len(objects_with_asymmetric)} objects.")
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='FACE')
    else:
        self.report({'INFO'}, "No asymmetric faces found.")
        bpy.ops.object.mode_set(mode='OBJECT')
        
    return {'FINISHED'}

# ----------- Normals -----------
def recalculate_normals(self, context):
    """Recalculate normals"""
    # Store current mode and selection
    current_mode = bpy.context.object.mode if bpy.context.object else 'OBJECT'
    original_active = bpy.context.active_object
    original_selected = [obj for obj in bpy.context.selected_objects]
    
    # Ensure we're in Object mode to start
    if current_mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    
    selected_objects = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH']
    
    if not selected_objects:
        self.report({'WARNING'}, "No mesh objects selected")
        return {'Cancelled'}
    
    # Process each selected mesh object
    count = 0
    for obj in selected_objects:
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        
        # Switch to edit mode
        bpy.ops.object.mode_set(mode='EDIT')
        
        # Select all faces
        bpy.ops.mesh.select_all(action='SELECT')
        
        # Recalculate normals
        bpy.ops.mesh.normals_make_consistent(inside=False)
        
        # Back to object mode
        bpy.ops.object.mode_set(mode='OBJECT')
        
        count += 1
    
    # Report success
    self.report({'INFO'}, f"Recalculated normals for {count} objects")
    
    # Make sure we're in object mode before restoring selection
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Manually restore selection without using the helper
    bpy.ops.object.select_all(action='DESELECT')
    for obj in original_selected:
        if obj.name in bpy.data.objects:
            obj.select_set(True)
    
    if original_active and original_active.name in bpy.data.objects:
        bpy.context.view_layer.objects.active = original_active
    
    # Restore original mode
    if current_mode != 'OBJECT' and bpy.context.object:
        bpy.ops.object.mode_set(mode=current_mode)
    
    return {'FINISHED'}

def smooth_shading(self, context):
    for object in bpy.context.selected_objects:
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.view_layer.objects.active = object
        bpy.ops.mesh.customdata_custom_splitnormals_clear()
        bpy.ops.object.shade_smooth(use_auto_smooth=True, auto_smooth_angle=math.radians(30))
    return {'FINISHED'}

def face_orientation_toggle(self, context):
    """Toggle face orientation display on/off"""
    # Get current state
    current_state = context.space_data.overlay.show_face_orientation
    
    # Toggle to opposite state
    context.space_data.overlay.show_face_orientation = not current_state
    
    # Report the new state
    new_state = "shown" if not current_state else "hidden"
    self.report({'INFO'}, f"Face orientation {new_state}")
    
    # Must return a proper Blender operator return value
    return {'FINISHED'}

# ----------- Loose Geometry -----------
def loose_geometry_vert(self, context):
    def count_loose_vertices(obj):
        me = obj.data
        bm = bmesh.from_edit_mesh(me)
        
        # Count selected vertices
        obj_selected = sum(1 for v in bm.verts if v.select)
        return obj_selected, obj_selected > 0
    
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_loose(extend=False)
    
    # Check if anything is selected
    selected_count = 0
    objects_with_loose = []
    
    for obj in context.selected_objects:
        if obj.type != 'MESH':
            continue
            
        # Count selected vertices
        obj_selected, has_loose = count_loose_vertices(obj)
        if obj_selected > 0:
            selected_count += obj_selected
            objects_with_loose.append(obj.name)
    
    return report_validation_results(self, selected_count, objects_with_loose, "loose vertices", 'VERT')

def loose_geometry_edge(self, context):
    def count_loose_edges(obj):
        me = obj.data
        bm = bmesh.from_edit_mesh(me)
        
        # Count selected edges
        obj_selected = sum(1 for e in bm.edges if e.select)
        return obj_selected, obj_selected > 0
    
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_loose(extend=False)
    
    # Check if anything is selected
    selected_count = 0
    objects_with_loose = []
    
    for obj in context.selected_objects:
        if obj.type != 'MESH':
            continue
            
        # Count selected edges
        obj_selected, has_loose = count_loose_edges(obj)
        if obj_selected > 0:
            selected_count += obj_selected
            objects_with_loose.append(obj.name)
    
    return report_validation_results(self, selected_count, objects_with_loose, "loose edges", 'EDGE')

# ----------- Zero Length Edges -----------
def zero_length(self, context):
    def zero_length_edges(obj):
        me = obj.data
        bm = bmesh.from_edit_mesh(me)
        zero_length_edges = []
        
        for edge in bm.edges:
            if edge.calc_length() == 0.0:
                zero_length_edges.append(edge)
                edge.select_set(True)
        
        bmesh.update_edit_mesh(me)
        return len(zero_length_edges), len(zero_length_edges) > 0
    
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
    bpy.ops.mesh.select_all(action='DESELECT')
    
    found_zero_edges = 0
    objects_with_zero_edges = []
    
    for obj in bpy.context.selected_objects:
        if obj.type != 'MESH':
            continue
        
        obj_zero_edges, has_zero = zero_length_edges(obj)
        if has_zero:
            found_zero_edges += obj_zero_edges
            objects_with_zero_edges.append(obj.name)
    
    return report_validation_results(self, found_zero_edges, objects_with_zero_edges, "zero-length edges", 'VERT')

# ----------- Concave Face Check -----------
def concave(self, context):
    """Check for concave/non-planar faces with distorted geometry"""
    def face_planarity_concavity(obj):
        # Set a threshold for planarity (lower means stricter)
        planarity_threshold = 0.001
        
        me = obj.data
        bm = bmesh.from_edit_mesh(me)
        concave_count = 0
        nonplanar_count = 0
        has_issues = False
        
        for face in bm.faces:
            # Skip triangles as they're always planar
            if len(face.verts) <= 3:
                continue
                
            # Check for non-planar faces (all vertices should lie on same plane)
            is_nonplanar = False
            if len(face.verts) > 3:
                # Get the face normal and a point on the face
                normal = face.normal.copy()
                point_on_face = face.verts[0].co
                
                # Calculate the plane equation: ax + by + cz + d = 0
                a, b, c = normal
                d = -normal.dot(point_on_face)
                
                # Check if all vertices lie on this plane
                for v in face.verts:
                    # Calculate distance from point to plane
                    dist = abs(a * v.co.x + b * v.co.y + c * v.co.z + d)
                    if dist > planarity_threshold:
                        is_nonplanar = True
                        break
            
            # Check for concave faces (using angle between adjacent edges)
            is_concave = False
            vert_count = len(face.verts)
            verts = [v.co for v in face.verts]
            
            # Project vertices onto a plane for better concavity detection
            # Create a coordinate system on the face plane
            z_axis = face.normal.normalized()
            
            # Find the longest edge to use as x-axis base
            max_length = 0
            x_base = None
            for i in range(vert_count):
                v1 = verts[i]
                v2 = verts[(i + 1) % vert_count]
                edge_vec = v2 - v1
                length = edge_vec.length
                if length > max_length:
                    max_length = length
                    x_base = edge_vec.normalized()
            
            # Create coordinate system
            y_axis = z_axis.cross(x_base).normalized()
            x_axis = y_axis.cross(z_axis).normalized()
            
            # Project all vertices to 2D
            verts_2d = []
            for v in verts:
                x_proj = (v - verts[0]).dot(x_axis)
                y_proj = (v - verts[0]).dot(y_axis)
                verts_2d.append(Vector((x_proj, y_proj)))
            
            # Check for concavity in the 2D projection
            for i in range(vert_count):
                v1 = verts_2d[i]
                v2 = verts_2d[(i + 1) % vert_count]
                v3 = verts_2d[(i + 2) % vert_count]
                
                # Compute cross product to determine if the angle is concave
                edge1 = v2 - v1
                edge2 = v3 - v2
                
                # Check sign of z-component of cross product
                cross_z = edge1.x * edge2.y - edge1.y * edge2.x
                
                # If negative, we found a concave angle
                if cross_z < 0:
                    is_concave = True
                    break
            
            # Mark the face if it's concave or non-planar
            if is_concave or is_nonplanar:
                face.select_set(True)
                has_issues = True
                
                if is_concave:
                    concave_count += 1
                if is_nonplanar:
                    nonplanar_count += 1
        
        bmesh.update_edit_mesh(me)
        return concave_count, nonplanar_count, has_issues
    
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
    bpy.ops.mesh.select_all(action='DESELECT')
    
    total_concave = 0
    total_nonplanar = 0
    objects_with_issues = []
    
    for obj in bpy.context.selected_objects:
        if obj.type != 'MESH':
            continue
        
        concave_count, nonplanar_count, has_issues = face_planarity_concavity(obj)
        
        if has_issues:
            total_concave += concave_count
            total_nonplanar += nonplanar_count
            objects_with_issues.append(obj.name)
    
    # Report results
    if total_concave > 0 or total_nonplanar > 0:
        issue_message = []
        if total_concave > 0:
            issue_message.append(f"{total_concave} concave polygons")
        if total_nonplanar > 0:
            issue_message.append(f"{total_nonplanar} non-planar polygons")
        
        self.report({'WARNING'}, f"Found {' and '.join(issue_message)} in {len(objects_with_issues)} objects")
        bpy.ops.object.mode_set(mode='EDIT')
    else:
        self.report({'INFO'}, "No concave or non-planar polygons found")
        bpy.ops.object.mode_set(mode='OBJECT')  # Return to object mode if no issues
    
    return {'FINISHED'}

# ----------- Overlapping Faces -----------
def overlapping_faces(self, context):
    """Check for interior faces in a mesh using Ambient Occlusion baking"""
    selected_objects = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH']
    
    if not selected_objects:
        self.report({'WARNING'}, "No mesh objects selected")
        return {'CANCELLED'}
    
    # Remember original selection
    original_active = bpy.context.active_object
    original_selected = [obj for obj in bpy.context.selected_objects]
    original_mode = bpy.context.object.mode if bpy.context.object else 'OBJECT'
    
    # Ensure we're in object mode
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Initialize counters
    total_interior_faces = 0
    objects_with_interior = []
    
    # Set up rendering settings
    original_engine = bpy.context.scene.render.engine
    original_samples = bpy.context.scene.cycles.samples if hasattr(bpy.context.scene, 'cycles') else None
    
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.samples = 8  # Low sample count for speed
    
    resolution = 1024  # Reduced for better performance
    pref_margin_div = 0.02
    
    # Function to test if a UV area has AO (interior faces will have little to no AO)
    def hit_test_area(pixels, resolution, xpos_min, ypos_min, xpos_max, ypos_max):
        if xpos_min > xpos_max or ypos_min > ypos_max:
            return False  # Invalid area
            
        # Make sure coordinates are within bounds
        xpos_min = max(0, min(xpos_min, resolution-1))
        xpos_max = max(0, min(xpos_max, resolution-1))
        ypos_min = max(0, min(ypos_min, resolution-1))
        ypos_max = max(0, min(ypos_max, resolution-1))
        
        # Check for dark areas (interior faces)
        pixel_count = 0
        dark_pixels = 0
        
        for i in range(xpos_min, xpos_max + 1):
            for j in range(ypos_min, ypos_max + 1):
                idx = 4 * (i + resolution * j)
                if idx + 3 < len(pixels):  # Check if index is valid
                    r = pixels[idx]
                    # Interior faces will be dark with AO
                    if r < 0.05:  # Very dark threshold
                        dark_pixels += 1
                    pixel_count += 1
        
        # If most pixels are dark, we have an interior face
        dark_ratio = dark_pixels / pixel_count if pixel_count > 0 else 0
        return dark_ratio > 0.8  # Consider interior if >80% dark
    
    # Process each selected object
    for obj in selected_objects:
        # Deselect all objects and select only this one
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        
        # Make sure we're in object mode for material operations
        bpy.ops.object.mode_set(mode='OBJECT')
        
        # Create a temporary UV layer for AO baking
        me = obj.data
        temp_uv_name = "__TEMP_AO_UV__"
        temp_uv = me.uv_layers.get(temp_uv_name)
        if temp_uv:
            me.uv_layers.remove(temp_uv)
        temp_uv = me.uv_layers.new(name=temp_uv_name)
        temp_uv.active = True
        
        # Switch to edit mode for unwrapping
        bpy.ops.object.mode_set(mode='EDIT')
        
        # Create a lightmap UV layout
        try:
            # Modern Blender uses different parameter names
            try:
                bpy.ops.uv.lightmap_pack(
                    PREF_CONTEXT='ALL_FACES', 
                    PREF_PACK_IN_ONE=True, 
                    PREF_NEW_UVLAYER=False, 
                    PREF_IMG_PX_SIZE=resolution, 
                    PREF_BOX_DIV=12, 
                    PREF_MARGIN_DIV=pref_margin_div
                )
            except TypeError:
                # Fall back to newer parameter names
                bpy.ops.uv.lightmap_pack(
                    context='ALL_FACES', 
                    pack_in_one=True, 
                    new_uvlayer=False, 
                    image_size=resolution, 
                    box_div=12, 
                    margin_div=pref_margin_div
                )
        except Exception as e:
            # If lightmap_pack fails, try a simple unwrap
            bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.02)
        
        # Back to object mode for material operations
        bpy.ops.object.mode_set(mode='OBJECT')
        
        # Create new material for baking
        bake_material = bpy.data.materials.new(name=f"{obj.name}_AO_BAKE_MAT")
        bake_material.use_nodes = True
        
        # Clear default nodes
        node_tree = bake_material.node_tree
        for node in node_tree.nodes:
            node_tree.nodes.remove(node)
        
        # Create image texture node for baking
        image_texture_node = node_tree.nodes.new(type='ShaderNodeTexImage')
        image_texture_node.select = True
        node_tree.nodes.active = image_texture_node
        
        # Create AO image
        ao_image = bpy.data.images.new(name=f"{obj.name}_AO", width=resolution, height=resolution)
        image_texture_node.image = ao_image
        
        # Store original materials
        original_materials = []
        for i, slot in enumerate(obj.material_slots):
            if slot.material:
                original_materials.append((i, slot.material))
        
        # Remove existing materials
        while len(obj.material_slots) > 0:
            bpy.ops.object.material_slot_remove()
        
        # Add bake material
        obj.data.materials.append(bake_material)
        
        # Bake AO
        try:
            bpy.ops.object.bake(type='AO', pass_filter={'DIRECT', 'INDIRECT'}, 
                                width=resolution, height=resolution, margin=1)
        except Exception as e:
            self.report({'ERROR'}, f"Baking failed for {obj.name}: {str(e)}")
            continue
        
        # Switch to edit mode to select interior faces
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        
        # Get the mesh data in edit mode
        bm = bmesh.from_edit_mesh(me)
        
        # Make sure face indices are updated
        bm.faces.ensure_lookup_table()
        
        # Get the UV layer
        uv_layer = bm.loops.layers.uv.get(temp_uv_name)
        if not uv_layer:
            self.report({'ERROR'}, f"Could not find UV layer for {obj.name}")
            continue
        
        # Get pixel data from the baked image
        pixels = list(ao_image.pixels[:])
        
        # Check each face
        obj_interior_faces = 0
        
        for face in bm.faces:
            # Get UV bounds for this face
            xpos_min = float("inf")
            xpos_max = float("-inf")
            ypos_min = float("inf")
            ypos_max = float("-inf")
            
            for loop in face.loops:
                uv = loop[uv_layer].uv
                xpos = int(uv.x * (resolution - 1))
                ypos = int(uv.y * (resolution - 1))
                
                xpos_min = min(xpos_min, xpos)
                xpos_max = max(xpos_max, xpos)
                ypos_min = min(ypos_min, ypos)
                ypos_max = max(ypos_max, ypos)
            
            # Test if face is interior by checking AO values
            is_interior = hit_test_area(pixels, resolution, xpos_min, ypos_min, xpos_max, ypos_max)
            
            if is_interior:
                face.select_set(True)
                obj_interior_faces += 1
        
        # Update the mesh
        bmesh.update_edit_mesh(me)
        
        # Must go to object mode for cleanup operations
        bpy.ops.object.mode_set(mode='OBJECT')
        
        # Clean up the image
        bpy.data.images.remove(ao_image)
        
        # Remove temp material slot
        if len(obj.material_slots) > 0:
            bpy.ops.object.material_slot_remove()
        
        # Clean up material
        if bake_material.name in bpy.data.materials:
            bpy.data.materials.remove(bake_material)
        
        # Restore original materials
        for slot_idx, mat in original_materials:
            obj.data.materials.append(mat)
        
        # Remove temp UV layer
        temp_uv = me.uv_layers.get(temp_uv_name)
        if temp_uv:
            me.uv_layers.remove(temp_uv)
        
        # If interior faces found, track them
        if obj_interior_faces > 0:
            total_interior_faces += obj_interior_faces
            objects_with_interior.append(obj.name)
            
            # Go back to edit mode to keep selection visible
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_mode(type='FACE')
    
    # Restore original selection
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    
    for obj in original_selected:
        if obj.name in bpy.data.objects:
            obj.select_set(True)
    
    if original_active and original_active.name in bpy.data.objects:
        bpy.context.view_layer.objects.active = original_active
    
    # Restore render settings
    if original_engine:
        bpy.context.scene.render.engine = original_engine
    if original_samples:
        bpy.context.scene.cycles.samples = original_samples
    
    # Report results
    if total_interior_faces > 0:
        self.report({'WARNING'}, f"Found {total_interior_faces} interior faces in {len(objects_with_interior)} objects")
        # Go to edit mode to show the selection for objects with interior faces
        if len(objects_with_interior) > 0:
            obj = bpy.data.objects.get(objects_with_interior[0])
            if obj:
                bpy.context.view_layer.objects.active = obj
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_mode(type='FACE')
    else:
        self.report({'INFO'}, "No interior faces found")
        # Stay in object mode as no issues were found
        bpy.ops.object.mode_set(mode='OBJECT')
    
    return {'FINISHED'}

# ----------- UV Tools -----------
def self_penetrating_uvs(self, context):
    """Check for self-penetrating UVs with more accurate detection"""
    count = 0
    objects_with_overlaps = []
    
    # Helper function to check if two triangles actually overlap
    def triangles_intersect(tri1, tri2, tolerance=0.00001):
        # Helper function to check if a point is inside a triangle
        def point_in_triangle(pt, v1, v2, v3):
            def sign(p1, p2, p3):
                return (p1.x - p3.x) * (p2.y - p3.y) - (p2.x - p3.x) * (p1.y - p3.y)
            
            d1 = sign(pt, v1, v2)
            d2 = sign(pt, v2, v3)
            d3 = sign(pt, v3, v1)
            
            has_neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
            has_pos = (d1 > 0) or (d2 > 0) or (d3 > 0)
            
            # If all same sign or on edge (very close to 0), point is in triangle
            return not (has_neg and has_pos)
        
        # Check if any point of triangle 1 is inside triangle 2
        for point in tri1:
            if point_in_triangle(point, tri2[0], tri2[1], tri2[2]):
                return True
                
        # Check if any point of triangle 2 is inside triangle 1
        for point in tri2:
            if point_in_triangle(point, tri1[0], tri1[1], tri1[2]):
                return True
                
        # Helper to check if two lines intersect
        def lines_intersect(l1_start, l1_end, l2_start, l2_end):
            def ccw(A, B, C):
                return (C.y - A.y) * (B.x - A.x) > (B.y - A.y) * (C.x - A.x)
            
            # Return true if the lines intersect
            return ccw(l1_start, l2_start, l2_end) != ccw(l1_end, l2_start, l2_end) and \
                   ccw(l1_start, l1_end, l2_start) != ccw(l1_start, l1_end, l2_end)
        
        # Check if any edges intersect
        # Triangle 1 edges
        edges1 = [(tri1[0], tri1[1]), (tri1[1], tri1[2]), (tri1[2], tri1[0])]
        # Triangle 2 edges
        edges2 = [(tri2[0], tri2[1]), (tri2[1], tri2[2]), (tri2[2], tri2[0])]
        
        for e1 in edges1:
            for e2 in edges2:
                if lines_intersect(e1[0], e1[1], e2[0], e2[1]):
                    return True
        
        return False
    
    for obj in bpy.context.selected_objects:
        if obj.type != 'MESH' or not obj.data.uv_layers:
            continue
            
        # Select the object and enter edit mode
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        
        # Store the current state
        current_face_select_mode = bpy.context.tool_settings.mesh_select_mode[2]
        
        # Set face selection mode
        bpy.context.tool_settings.mesh_select_mode = (False, False, True)
        
        # Get the mesh data
        me = obj.data
        bm = bmesh.from_edit_mesh(me)
        
        if not bm.loops.layers.uv:
            continue
            
        uv_layer = bm.loops.layers.uv.active
        
        # Create a list of faces and their UV coordinates
        faces_with_overlaps = set()
        
        # Build a dictionary of UV triangles for each face
        face_uv_triangles = {}
        
        # Get adjacent faces (sharing an edge in 3D)
        adjacent_faces = {}
        for edge in bm.edges:
            for face1 in edge.link_faces:
                if face1.index not in adjacent_faces:
                    adjacent_faces[face1.index] = set()
                for face2 in edge.link_faces:
                    if face1 != face2:
                        adjacent_faces[face1.index].add(face2.index)
        
        # Triangulate faces in memory (not affecting the actual mesh)
        for face in bm.faces:
            face_uvs = []
            
            for loop in face.loops:
                face_uvs.append(loop[uv_layer].uv)
            
            # Skip faces with less than 3 vertices
            if len(face_uvs) < 3:
                continue
            
            # Create triangles from the face
            triangles = []
            for i in range(1, len(face_uvs) - 1):
                tri_uvs = [face_uvs[0], face_uvs[i], face_uvs[i+1]]
                triangles.append(tri_uvs)
            
            face_uv_triangles[face.index] = triangles
        
        # Check for UV face overlaps
        for face1_idx, face1_triangles in face_uv_triangles.items():
            for face2_idx, face2_triangles in face_uv_triangles.items():
                # Skip comparing a face to itself
                if face1_idx >= face2_idx:
                    continue
                
                # Skip adjacent faces - they can share UV edges legitimately
                if (face1_idx in adjacent_faces and face2_idx in adjacent_faces[face1_idx]):
                    continue
                
                # Check each triangle pair for overlaps
                found_overlap = False
                for tri1 in face1_triangles:
                    if found_overlap:
                        break
                    for tri2 in face2_triangles:
                        # Quick bounding box check first
                        min_x1 = min(tri1[0].x, tri1[1].x, tri1[2].x)
                        max_x1 = max(tri1[0].x, tri1[1].x, tri1[2].x)
                        min_y1 = min(tri1[0].y, tri1[1].y, tri1[2].y)
                        max_y1 = max(tri1[0].y, tri1[1].y, tri1[2].y)
                        
                        min_x2 = min(tri2[0].x, tri2[1].x, tri2[2].x)
                        max_x2 = max(tri2[0].x, tri2[1].x, tri2[2].x)
                        min_y2 = min(tri2[0].y, tri2[1].y, tri2[2].y)
                        max_y2 = max(tri2[0].y, tri2[1].y, tri2[2].y)
                        
                        # If bounding boxes overlap, do precise check
                        if (max_x1 >= min_x2 and max_x2 >= min_x1 and
                            max_y1 >= min_y2 and max_y2 >= min_y1):
                            
                            # More accurate triangle intersection test
                            if triangles_intersect(tri1, tri2):
                                faces_with_overlaps.add(face1_idx)
                                faces_with_overlaps.add(face2_idx)
                                found_overlap = True
                                break
        
        # Select faces with overlaps
        overlap_count = len(faces_with_overlaps)
        if overlap_count > 0:
            count += overlap_count
            objects_with_overlaps.append(obj.name)
            
            # Select the problematic faces
            for face in bm.faces:
                if face.index in faces_with_overlaps:
                    face.select = True
            
            # Update the mesh
            bmesh.update_edit_mesh(me)
        
        # Restore face selection mode
        bpy.context.tool_settings.mesh_select_mode = (False, False, current_face_select_mode)
    
    # Reselect all previously selected objects
    for obj in context.selected_objects:
        obj.select_set(True)
    
    if count > 0:
        self.report({'WARNING'}, f"Found {count} faces with overlapping UVs in {len(objects_with_overlaps)} objects")
        bpy.ops.object.mode_set(mode='EDIT')
    else:
        bpy.ops.object.mode_set(mode='OBJECT')
        self.report({'INFO'}, "No self-penetrating UVs found in selected objects.")
    
    return {'FINISHED'}

def missing_uvs(self, context):
    missing_uv_objects = []
    valid_objects = []
    
    for obj in bpy.context.selected_objects:
        if obj.type == 'MESH':
            if not obj.data.uv_layers or len(obj.data.uv_layers) == 0:
                missing_uv_objects.append(obj.name)
            else:
                valid_objects.append(obj.name)
    
    # Report results with specific counts
    if missing_uv_objects:
        self.report({'WARNING'}, f"Found {len(missing_uv_objects)} objects missing UVs: {', '.join(missing_uv_objects)}")
        # Stay in current mode - since missing UVs is an object-level property
    else:
        self.report({'INFO'}, f"All {len(valid_objects)} selected objects have UV maps.")
        bpy.ops.object.mode_set(mode='OBJECT')  # Return to object mode if no issues
        
    return {'FINISHED'}

def sharp_edges_to_uvs(self, context):
    # First clear all seams in edit mode
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.mark_seam(clear=True)
    
    # Switch to object mode to select sharp edges
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Select sharp edges and mark as seams
    sharp_edge_count = 0
    for obj in context.selected_objects:
        if obj.type == 'MESH':
            for edge in obj.data.edges:
                if edge.use_edge_sharp:
                    edge.select = True
                    edge.use_seam = True
                    sharp_edge_count += 1
                else:
                    edge.select = False
    
    # Only perform unwrap if we found sharp edges
    if sharp_edge_count > 0:
        # Switch to edit mode for unwrapping
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
        
        # Select all faces connected to the selected edges and unwrap
        bpy.ops.mesh.select_mode(type='FACE')
        bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.001)
        
        self.report({'INFO'}, f"Converted {sharp_edge_count} sharp edges to UV seams and unwrapped")
    else:
        bpy.ops.object.mode_set(mode='EDIT')
        self.report({'WARNING'}, "No sharp edges found to convert to seams")
    
    # Deselect all to clean up
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    return {'FINISHED'}

# ----------- Cleanup Tools -----------
def vertexcolor(self, context):
    count = 0
    obj_names = []
    
    for obj in bpy.context.selected_objects:
        if obj.type == 'MESH':
            vertex_colors = obj.data.vertex_colors
            initial_count = len(vertex_colors)
            
            while (len(vertex_colors) > 0):
                vertex_color = vertex_colors[0]
                obj.data.vertex_colors.remove(vertex_color)
                count += 1
                
            if initial_count > 0:
                obj_names.append(obj.name)
    
    if count > 0:
        self.report({'INFO'}, f"Removed {count} vertex color layers from {len(obj_names)} objects.")
    else:
        self.report({'INFO'}, "No vertex color layers found.")
    return {'FINISHED'}

def vertexgroup(self, context):
    count = 0
    obj_names = []
    
    for obj in bpy.context.selected_objects:
        if obj.type == 'MESH':
            vertex_groups = obj.vertex_groups
            initial_count = len(vertex_groups)
            
            while (len(vertex_groups) > 0):
                vertex_group = vertex_groups[0]
                obj.vertex_groups.remove(vertex_group)
                count += 1
                
            if initial_count > 0:
                obj_names.append(obj.name)
    
    if count > 0:
        self.report({'INFO'}, f"Removed {count} vertex groups from {len(obj_names)} objects.")
    else:
        self.report({'INFO'}, "No vertex groups found.")
    return {'FINISHED'}

def unused_materials(self, context):
    removed_count = 0
    objects_modified = []
    
    for obj in bpy.context.selected_objects:
        if obj.type != 'MESH':
            continue
            
        # Check if object has any materials
        if not obj.material_slots:
            continue
            
        bpy.context.view_layer.objects.active = obj
        obj_materials_removed = 0
        
        # Check each polygon to see which materials are used
        used_material_indices = set()
        for poly in obj.data.polygons:
            used_material_indices.add(poly.material_index)
        
        # Get a list of unused material slots (in reverse order to avoid reindexing issues)
        unused_slots = sorted([i for i in range(len(obj.material_slots)) 
                              if i not in used_material_indices], reverse=True)
        
        # Remove unused material slots
        for slot_idx in unused_slots:
            obj.active_material_index = slot_idx
            bpy.ops.object.material_slot_remove()
            obj_materials_removed += 1
            removed_count += 1
            
        if obj_materials_removed > 0:
            objects_modified.append(obj.name)
    
    if removed_count > 0:
        self.report({'INFO'}, f"Removed {removed_count} unused materials from {len(objects_modified)} objects.")
    else:
        self.report({'INFO'}, "No unused materials found in selected objects.")
        
    return {'FINISHED'}

def remove_cameras(self, context):
    camera_count = 0
    camera_names = []
    
    # Find all cameras in the scene
    for obj in bpy.data.objects:
        if obj.type == 'CAMERA':
            camera_names.append(obj.name)
            camera_count += 1
    
    # Delete all cameras
    for name in camera_names:
        camera = bpy.data.objects.get(name)
        if camera:
            bpy.data.objects.remove(camera)
    
    if camera_count > 0:
        self.report({'INFO'}, f"Removed {camera_count} cameras: {', '.join(camera_names)}")
    else:
        self.report({'INFO'}, "No cameras found in the scene.")
        
    return {'FINISHED'}

def apply_transforms(self, context):
    # Store current selection and active object
    original_active, original_selected = save_selection_state()
    
    count = 0
    obj_names = []
    
    for obj in original_selected:
        # Skip non-mesh objects and linked objects (which can't have transforms applied)
        if obj.type not in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT', 'ARMATURE', 'LATTICE', 'EMPTY'} or obj.library:
            continue
            
        # Make this the active object
        bpy.context.view_layer.objects.active = obj
        
        # Apply location, rotation, and scale
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        count += 1
        obj_names.append(obj.name)
    
    # Restore original selection and active object
    restore_selection_state(original_active, original_selected)
    
    if count > 0:
        self.report({'INFO'}, f"Applied transforms to {count} objects.")
    else:
        self.report({'INFO'}, "No valid objects found to apply transforms.")
        
    return {'FINISHED'}

# Dictionary to map operator IDs to their function implementations
FUNCTION_MAP = {
    "object.gs_duplicate_vertex": duplicate_vertex_one_object,
    "object.gs_meshes_overlap": meshes_overlap,
    "object.gs_ngon": ngon,
    "object.gs_asymmetric_vert": asymmetric_vert,
    "object.gs_asymmetric_face": asymmetric_face,
    "object.gs_smooth_shading": smooth_shading,
    "object.gs_recalculate_normals": recalculate_normals,
    "object.gs_face_orientation_toggle": face_orientation_toggle,
    "object.gs_loose_geometry_vert": loose_geometry_vert,
    "object.gs_loose_geometry_edge": loose_geometry_edge,
    "object.gs_zero_length": zero_length,
    "object.gs_concave": concave,
    "object.gs_overlapping_faces": overlapping_faces,
    "object.gs_self_penetrating_uvs": self_penetrating_uvs,
    "object.gs_missing_uvs": missing_uvs,
    "object.gs_vertexcolor": vertexcolor,
    "object.gs_vertexgroup": vertexgroup,
    "object.gs_unused_materials": unused_materials,
    "object.gs_remove_cameras": remove_cameras,
    "object.gs_apply_transforms": apply_transforms,
    "object.gs_sharp_edges_to_uvs": sharp_edges_to_uvs,
}

# Dictionary to map poll conditions
POLL_MAP = {
    "object.gs_meshes_overlap": two_mesh_poll,
    # All other operators use standard_mesh_poll by default
}

# Generate operator classes
operator_classes = []

def register():
    from . import GS_Asset_Validation_List
    
    # Create operator classes dynamically
    for category in GS_Asset_Validation_List.VALIDATION_OPERATORS:
        for op in category["operators"]:
            op_id = op["id"]
            
            # Create a new operator class
            attrs = {
                "bl_idname": op_id,
                "bl_label": op["label"],
                "bl_description": op["description"],
                "execute": FUNCTION_MAP[op_id]
            }
            
            # Add custom poll method if needed
            if op.get("poll", True):
                if op_id in POLL_MAP:
                    attrs["poll"] = classmethod(POLL_MAP[op_id])
                else:
                    attrs["poll"] = classmethod(standard_mesh_poll)
            
            # Add properties if defined
            if "props" in op:
                for prop in op["props"]:
                    prop_name = prop["name"]
                    prop_type = prop["type"]
                    prop_args = prop["args"]
                    
                    # Create property
                    if prop_type == "FloatProperty":
                        attrs[prop_name] = bpy.props.FloatProperty(**prop_args)
                    elif prop_type == "IntProperty":
                        attrs[prop_name] = bpy.props.IntProperty(**prop_args)
                    elif prop_type == "BoolProperty":
                        attrs[prop_name] = bpy.props.BoolProperty(**prop_args)
                    # Add more property types as needed
            
            # Create the class and check if it already exists
            class_name = f"GS_{op_id.split('.')[-1].upper()}"
            
            # Skip if class already exists
            if class_name in globals():
                continue
                
            # Create the class and register it
            OpClass = type(class_name, (Operator,), attrs)
            operator_classes.append(OpClass)
            
            # Register operator class
            bpy.utils.register_class(OpClass)
            
            # Add to module namespace for reference
            globals()[class_name] = OpClass
            
            # Add to list module for UI to use
            GS_Asset_Validation_List.operator_classes.append(OpClass)

def unregister():
    for cls in reversed(operator_classes):
        bpy.utils.unregister_class(cls)
    operator_classes.clear()