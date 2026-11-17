"""Quick Tools: the everyday building steps at the top of the CM tab.

    Create Anchor       an empty at the active object's origin, named
                        anchor_<active>, made the parent of the selection
    Rename Mesh Data    each selected object's mesh named after the object

The operators and their log lines are in vehicle.py; this is the work.
"""
from __future__ import annotations

from mathutils import Matrix

from . import names

# Temporary mesh names while renaming (see rename_mesh_data).
_TEMP_NAME = "gs_cm_rename_{}"


def anchor_name(active):
    return names.ANCHOR_PREFIX + active.name


def create_anchor(context, active, selected):
    """Add an empty at ``active``'s origin and orientation (not its scale),
    named anchor_<active>, and parent ``selected`` to it, keeping where
    everything is in the world. Returns the empty.

    The anchor takes the place of the selection in the hierarchy: it goes under
    the active object's nearest parent that isn't selected, in the active
    object's collections. Only the outermost selected objects are re-parented;
    one whose parent is selected too stays under it.
    """
    chosen = set(selected)
    parent = active.parent
    while parent is not None and parent in chosen:
        parent = parent.parent

    empty = context.blend_data.objects.new(anchor_name(active), None)
    empty.empty_display_type = 'PLAIN_AXES'
    empty.rotation_mode = active.rotation_mode
    for collection in active.users_collection:
        collection.objects.link(empty)
    empty.parent = parent
    location, rotation, _scale = active.matrix_world.decompose()
    empty.matrix_world = Matrix.Translation(location) @ rotation.to_matrix().to_4x4()

    for obj in selected:
        if obj.parent in chosen:
            continue
        world = obj.matrix_world.copy()
        obj.parent = empty
        obj.parent_type = 'OBJECT'
        obj.matrix_parent_inverse = Matrix.Identity(4)
        obj.matrix_world = world        # the anchor's matrix_world is already set: no depsgraph update needed
    return empty


def rename_mesh_data(objects):
    """Name each mesh among ``objects`` after its object.

    Returns (renamed, shared, taken): how many were renamed, how many were
    left alone because several objects use the mesh, and how many came out as
    <name>.001 because another mesh outside the selection holds the name.
    """
    users = {}
    for obj in objects:
        if obj.type == 'MESH':
            users.setdefault(obj.data, []).append(obj)

    targets = []
    shared = 0
    for mesh, objs in users.items():
        if mesh.users - mesh.use_fake_user > 1:
            shared += 1
        elif mesh.name != objs[0].name:
            targets.append((mesh, objs[0].name))

    # Two passes, so meshes swapping names among the selection (A's mesh named
    # "B", B's named "A") both get theirs instead of a .001.
    for number, (mesh, _name) in enumerate(targets):
        mesh.name = _TEMP_NAME.format(number)
    taken = 0
    for mesh, name in targets:
        mesh.name = name
        if mesh.name != name:
            taken += 1
    return len(targets), shared, taken
