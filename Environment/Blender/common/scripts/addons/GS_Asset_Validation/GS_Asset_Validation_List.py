import bpy
from bpy.types import Operator

# Define categories and operators for validation tools
# This makes it easier to maintain and extend the add-on

# Operator metadata dictionary
# Format:
# - category: The category this operator belongs to (used for UI organization)
# - operators: List of operator definitions for this category
#   - id: The operator ID (bl_idname)
#   - label: Display name for the button
#   - description: Tooltip description
#   - poll: Whether this operator should have a custom poll method (True/False)
#   - props: Additional properties to add to the operator class
#   - is_action: Whether this is an action button (True) or check button (False)

VALIDATION_OPERATORS = [
    {
        "category": "Geometry",
        "operators": [
            {
                "id": "object.gs_duplicate_vertex",
                "label": "Duplicate Vertices",
                "description": "Find duplicate vertices on a single object",
                "poll": True,
                "is_action": False
            },
            {
                "id": "object.gs_meshes_overlap",
                "label": "Meshes Overlap",
                "description": "Check for overlapping planes between objects",
                "poll": True,  # Change to False to use the standard poll
                "is_action": False
            },
            {
                "id": "object.gs_ngon",
                "label": "N-Gon",
                "description": "Find faces with 5 or more vertices",
                "poll": True,
                "is_action": False
            },
            {
                "id": "object.gs_loose_geometry_vert",
                "label": "Loose Vertices",
                "description": "Find disconnected vertices",
                "poll": True,
                "is_action": False
            },
            {
                "id": "object.gs_loose_geometry_edge",
                "label": "Loose Edges",
                "description": "Find disconnected edges",
                "poll": True,
                "is_action": False
            },
            {
                "id": "object.gs_zero_length",
                "label": "Zero Length Edges",
                "description": "Find edges with zero length",
                "poll": True,
                "is_action": False
            },
            {
                "id": "object.gs_concave",
                "label": "Concave Faces",
                "description": "Find non-convex faces",
                "poll": True,
                "is_action": False
            },
            {
                "id": "object.gs_overlapping_faces",
                "label": "Overlapping Faces",
                "description": "Find hidden overlapping faces",
                "poll": True,
                "is_action": False
            },
        ]
    },
    {
        "category": "Normals",
        "operators": [
            {
                "id": "object.gs_recalculate_normals",
                "label": "Recalculate Normals",
                "description": "Recalculate normals",
                "poll": True,
                "is_action": True
            },
            {
                "id": "object.gs_smooth_shading",
                "label": "Apply Smooth Shading",
                "description": "Apply smooth shading with 30° auto smooth",
                "poll": True,
                "is_action": True
            },
            {
                "id": "object.gs_face_orientation_toggle",
                "label": "Toggle Face Orientation",
                "description": "Enable face orientation display",
                "poll": True,
                "is_action": True
            },
        ]
    },
    {
        "category": "Symmetry X",
        "operators": [
            {
                "id": "object.gs_asymmetric_vert",
                "label": "Asymmetric Vertices",
                "description": "Find vertices that break symmetry across X axis",
                "poll": True,
                "is_action": False
            },
            {
                "id": "object.gs_asymmetric_face",
                "label": "Asymmetric Faces",
                "description": "Find faces that break symmetry across X axis",
                "poll": True,
                "is_action": False
            },
        ]
    },
    {
        "category": "UV",
        "operators": [
            {
                "id": "object.gs_self_penetrating_uvs",
                "label": "Self Penetrating UVs",
                "description": "Check for self-penetrating UVs",
                "poll": True,
                "is_action": False
            },
            {
                "id": "object.gs_missing_uvs",
                "label": "Missing UVs",
                "description": "Check for objects with missing UVs",
                "poll": True,
                "is_action": False
            },
            {
                "id": "object.gs_sharp_edges_to_uvs",
                "label": "Sharp Edges to UV Seams",
                "description": "Convert sharp edges to UV seams and unwrap",
                "poll": True,
                "is_action": True
            },
        ]
    },
    {
        "category": "Cleanup",
        "operators": [
            {
                "id": "object.gs_vertexcolor",
                "label": "Vertex Colors",
                "description": "Delete all vertex color layers",
                "poll": True,
                "is_action": True
            },
            {
                "id": "object.gs_vertexgroup",
                "label": "Vertex Groups",
                "description": "Delete all vertex groups",
                "poll": True,
                "is_action": True
            },
            {
                "id": "object.gs_unused_materials",
                "label": "Unused Materials",
                "description": "Delete unused material slots",
                "poll": True,
                "is_action": True
            },
            {
                "id": "object.gs_remove_cameras",
                "label": "Cameras",
                "description": "Delete all cameras in the scene",
                "poll": False,
                "is_action": True
            },
            {
                "id": "object.gs_apply_transforms",
                "label": "Apply Transforms",
                "description": "Apply location, rotation and scale to selected objects",
                "poll": True,
                "is_action": True
            },
        ]
    },
]

# List of all operator classes (populated by the Function module)
operator_classes = []

# This is just a placeholder - actual registration happens in GS_Asset_Validation_Function.py
def register():
    pass

def unregister():
    pass