"""
gs_mirror.core - no UI, all the actual work.

History chain built on the target mesh when a mirror is created:

    origShape.outMesh
      -> transformGeometry   mesh local space -> pivot space    det +1
      -> polyMirror          mirror on local axis (+ weld)      winding handled internally
      -> transformGeometry   pivot space -> mesh local space    det +1
      -> shape.inMesh

Both transformGeometry matrices are driven by multMatrix nodes wired to the live
worldMatrix / worldInverseMatrix of the mesh and the pivot, so moving or rotating
the pivot updates the mirror interactively. Neither has a negative determinant,
so nothing in the stream is ever inside out and no polyNormal fix-up is needed.

The mirror is always driven by a dedicated GS_Mirror_Controller_NN locator - never
by the mesh itself and never by an arbitrary picked object. Picking an object only
says *where* the controller should be born: create_live_mirror() spawns a fresh
locator at that object's pivot (or at the mesh's own pivot when nothing is picked)
and drives the mirror from it, so the controller is always something the user can
move without dragging the geometry along with it. Once it exists it is an ordinary
locator, placed with Maya's own snapping and transform tools.
"""

import colorsys
import math

import maya.cmds as cmds
import maya.api.OpenMaya as om

AXES = {"x": 0, "y": 1, "z": 2}

SETTINGS_NODE = "gs_mirrorToolSettings"
TAG_ATTR = "GSMirrorNode"
PIVOT_ATTR = "GSMirrorPivot"

# Controller locators are numbered per scene: GS_Mirror_Controller_01, _02, ...
CONTROLLER_NAME = "GS_Mirror_Controller_{:02d}"

# Locator size tracks the perspective camera's far clip plane, so the pivot stays
# visible in scenes built at any scale. A far clip of 10000 (Maya's default) maps
# to localScale 1.
REFERENCE_FAR_CLIP = 10000.0
MIN_LOCATOR_SCALE = 0.01

# The polyMirrorFace *command* flags and the polyMirror *node* attributes do not
# share the same numbering, so the two are kept apart here. Measured on Maya 2022:
#   command mergeThresholdType: 0 -> threshold 2.0, 1 -> threshold 0.001
#   node mergeMode enum:        1 = merge border vertices, 2 = bridge border
#                               edges, 3 = do not merge borders (min 1, max 3)
# The command accepts mergeMode 0 and writes it straight through, but setAttr
# rejects it as out of range, so MERGE_OFF below is the in-range equivalent.
#   mirrorAxis:    0 = bounding box, 1 = object, 2 = world
#   axisDirection: 0 = negative, 1 = positive
MERGE_ON = 1
MERGE_OFF = 3
MIRROR_FLAGS = {
    "mirrorAxis": 1,
    "pivot": (0.0, 0.0, 0.0),
    "mergeThresholdType": 1,   # automatic - Maya's default threshold
    "smoothingAngle": 30.0,
    "flipUVs": False,
    "constructionHistory": True,
}

# Which component-frame axis becomes which local axis of the frame.
# Maya's own component axis orientation puts the normal on Z; if yours disagrees,
# reorder this tuple and nothing else changes.
FRAME_AXES = ("tangent", "binormal", "normal")

# Outliner colouring
COLOR_SATURATION = 0.50
COLOR_VALUE = 0.95


# ---------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------
def _shape(node):
    if cmds.nodeType(node) == "mesh":
        return node
    shapes = cmds.listRelatives(node, shapes=True, noIntermediate=True, fullPath=True) or []
    if not shapes:
        raise RuntimeError("{} has no mesh shape.".format(node))
    return shapes[0]


def _long(node):
    found = cmds.ls(node, long=True) or []
    return found[0] if found else None


def _index(component):
    return int(component.rsplit("[", 1)[-1].rstrip("]"))


def _mesh_fn(component):
    sel = om.MSelectionList()
    sel.add(component)
    dag, _ = sel.getComponent(0)
    dag.extendToShape()
    return om.MFnMesh(dag)


def _any_perpendicular(vector):
    """A deterministic unit vector perpendicular to `vector`."""
    helper = om.MVector(0.0, 1.0, 0.0)
    if abs(vector * helper) > 0.99:
        helper = om.MVector(1.0, 0.0, 0.0)
    return (helper ^ vector).normalize()


def selected_meshes():
    return [obj for obj in cmds.ls(selection=True, objectsOnly=True, long=True)
            if cmds.listRelatives(obj, shapes=True, noIntermediate=True, type="mesh")]


# ---------------------------------------------------------------------------
# view-dependent locator size
# ---------------------------------------------------------------------------
def _perspective_camera():
    """The scene's main perspective camera shape, or None."""
    if cmds.objExists("perspShape") and cmds.nodeType("perspShape") == "camera":
        return "perspShape"
    for camera in cmds.ls(type="camera", long=True) or []:
        try:
            if not cmds.getAttr(camera + ".orthographic"):
                return camera
        except Exception:
            continue
    return None


def locator_scale():
    """Locator localScale that keeps the pivot readable at the current view depth.

    far clip 10000 (Maya default) -> 1.0, far clip 1000000 -> 100.0.
    """
    camera = _perspective_camera()
    if not camera:
        return 1.0
    try:
        far = float(cmds.getAttr(camera + ".farClipPlane"))
    except Exception:
        return 1.0
    return max(far / REFERENCE_FAR_CLIP, MIN_LOCATOR_SCALE)


def scale_pivot_locator(locator, scale=None):
    """Push the view-derived size onto a locator's shapes. Returns the scale used."""
    scale = locator_scale() if scale is None else scale
    for shape in cmds.listRelatives(locator, shapes=True, type="locator",
                                    fullPath=True) or []:
        for axis in ("X", "Y", "Z"):
            try:
                cmds.setAttr("{}.localScale{}".format(shape, axis), scale)
            except Exception:
                pass
    return scale


# ---------------------------------------------------------------------------
# picked pivot object - stored per scene via a message connection, so it
# survives renaming and reparenting and breaks cleanly if the pivot is deleted
# ---------------------------------------------------------------------------
def settings_node(create=True):
    if cmds.objExists(SETTINGS_NODE):
        return SETTINGS_NODE
    if not create:
        return None
    node = cmds.createNode("network", name=SETTINGS_NODE, skipSelect=True)
    cmds.addAttr(node, longName="mirrorObject", attributeType="message")
    return node


def set_mirror_object(node=None):
    """Store `node` (or the current selection) as the mirror pivot source."""
    if node is None:
        selected = cmds.ls(selection=True, transforms=True, long=True)
        if not selected:
            raise RuntimeError("Select a transform to use as the mirror pivot.")
        node = selected[0]
    if _long(node) == _long(get_mirror_object()):
        return node                     # already stored; re-connecting only warns
    settings = settings_node()
    cmds.connectAttr(node + ".message", settings + ".mirrorObject", force=True)
    return node


def get_mirror_object():
    settings = settings_node(create=False)
    if not settings:
        return None
    connected = cmds.listConnections(settings + ".mirrorObject", source=True,
                                     destination=False, plugs=False) or []
    return connected[0] if connected else None


def is_pivot_locator(node):
    """True when `node` is a locator this tool created as a mirror controller."""
    if not node or not cmds.objExists(node):
        return False
    return bool(cmds.attributeQuery(PIVOT_ATTR, node=node, exists=True))


def pivot_matrix(node):
    """World matrix of `node`'s pivot: rotate pivot position, object orientation.

    Scale and shear are dropped so the locator decomposes to a clean rotation and
    the mirror plane is never skewed by the source object's transform.
    """
    position = cmds.xform(node, query=True, worldSpace=True, rotatePivot=True)
    world = om.MMatrix(cmds.xform(node, query=True, worldSpace=True, matrix=True))
    rotation = om.MTransformationMatrix(world).rotation(asQuaternion=True)

    out = om.MTransformationMatrix()
    out.setRotation(rotation)
    out.setTranslation(om.MVector(position[0], position[1], position[2]), om.MSpace.kWorld)
    return out.asMatrix()


def next_controller_name():
    """The next free GS_Mirror_Controller_NN name.

    Maya's own "#" substitution is not used: it does not zero-pad, so a scene
    would end up with a mix of _1 and _01.
    """
    index = 1
    while cmds.objExists(CONTROLLER_NAME.format(index)):
        index += 1
    return CONTROLLER_NAME.format(index)


def create_pivot_locator(name=None, matrix=None):
    """Make a tagged controller locator, store it as the mirror pivot, return it."""
    locator = _long(cmds.spaceLocator(name=name or next_controller_name())[0])
    cmds.addAttr(locator, longName=PIVOT_ATTR, attributeType="bool", defaultValue=True)
    cmds.setAttr(locator + ".overrideEnabled", 1)
    cmds.setAttr(locator + ".overrideRGBColors", 1)
    cmds.setAttr(locator + ".overrideColorRGB", 0.105, 0.693, 0.718)
    scale_pivot_locator(locator)
    if matrix is not None:
        cmds.xform(locator, worldSpace=True, matrix=list(matrix))
    set_mirror_object(locator)
    return locator


def pivot_locator_for(source):
    """The locator that should drive a mirror born from `source`.

    `source` is whatever the user picked (or the mesh itself when nothing is
    picked). If it is already one of our pivot locators it is reused as is;
    otherwise a fresh locator is created at its pivot. The object is never used
    as the controller itself.
    """
    if is_pivot_locator(source):
        scale_pivot_locator(source)
        set_mirror_object(source)
        return source
    return create_pivot_locator(matrix=pivot_matrix(source))



# ---------------------------------------------------------------------------
# component frame - the world-space frame of a face, edge or vertex
# ---------------------------------------------------------------------------
def component_frame(components=None):
    """World-space MMatrix from the selected components.

    Translation is the component centre; the axes are an orthonormal
    (tangent, binormal, normal) frame mapped through FRAME_AXES.
    Faces, edges and vertices are all accepted; components must be on one mesh.
    """
    components = components or cmds.ls(selection=True, flatten=True) or []
    faces = cmds.filterExpand(components, sm=34, expand=True) or []
    edges = cmds.filterExpand(components, sm=32, expand=True) or []
    verts = cmds.filterExpand(components, sm=31, expand=True) or []

    centre = om.MVector()
    normal = om.MVector()
    tangent = om.MVector()
    count = 0

    if faces:
        fn = _mesh_fn(faces[0])
        ids = [_index(f) for f in faces]
        for fid in ids:
            normal += fn.getPolygonNormal(fid, om.MSpace.kWorld)
            for vid in fn.getPolygonVertices(fid):
                centre += om.MVector(fn.getPoint(vid, om.MSpace.kWorld))
                count += 1
        # tangent along the first edge of the first face
        ring = fn.getPolygonVertices(ids[0])
        tangent = om.MVector(fn.getPoint(ring[1], om.MSpace.kWorld)
                             - fn.getPoint(ring[0], om.MSpace.kWorld))

    elif edges:
        fn = _mesh_fn(edges[0])
        for eid in (_index(e) for e in edges):
            v0, v1 = fn.getEdgeVertices(eid)
            p0 = fn.getPoint(v0, om.MSpace.kWorld)
            p1 = fn.getPoint(v1, om.MSpace.kWorld)
            tangent += om.MVector(p1 - p0)
            centre += om.MVector(p0) + om.MVector(p1)
            normal += fn.getVertexNormal(v0, True, om.MSpace.kWorld)
            normal += fn.getVertexNormal(v1, True, om.MSpace.kWorld)
            count += 2

    elif verts:
        fn = _mesh_fn(verts[0])
        ids = [_index(v) for v in verts]
        for vid in ids:
            centre += om.MVector(fn.getPoint(vid, om.MSpace.kWorld))
            normal += fn.getVertexNormal(vid, True, om.MSpace.kWorld)
            count += 1
        if len(ids) > 1:
            tangent = om.MVector(fn.getPoint(ids[-1], om.MSpace.kWorld)
                                 - fn.getPoint(ids[0], om.MSpace.kWorld))
        # a single vertex has no defined tangent - in-plane rotation is arbitrary

    else:
        raise RuntimeError("Select one or more faces, edges or vertices.")

    centre /= count
    normal.normalize()

    # orthonormalise the tangent against the normal
    tangent = tangent - normal * (tangent * normal)
    if tangent.length() < 1e-6:
        tangent = _any_perpendicular(normal)
    tangent.normalize()
    binormal = normal ^ tangent

    frame = {"tangent": tangent, "binormal": binormal, "normal": normal}
    x, y, z = (frame[key] for key in FRAME_AXES)
    return om.MMatrix([x.x, x.y, x.z, 0.0,
                       y.x, y.y, y.z, 0.0,
                       z.x, z.y, z.z, 0.0,
                       centre.x, centre.y, centre.z, 1.0])

def selected_components():
    """The component part of the current selection (faces, edges or vertices)."""
    return [item for item in (cmds.ls(selection=True, flatten=True) or [])
            if "." in item]


def _component_object(components):
    """The transform owning `components`."""
    node = components[0].split(".")[0]
    full = _long(node)
    if not full:
        raise RuntimeError("Cannot resolve the object for {}.".format(components[0]))
    if cmds.nodeType(full) == "mesh":
        parents = cmds.listRelatives(full, parent=True, fullPath=True) or []
        if not parents:
            raise RuntimeError("{} has no transform.".format(full))
        full = parents[0]
    return full


def _transform_points(shape, matrix):
    """Multiply every point of `shape` by `matrix`, in object space."""
    sel = om.MSelectionList()
    sel.add(shape)
    fn = om.MFnMesh(sel.getDagPath(0))
    fn.setPoints([point * matrix for point in fn.getPoints(om.MSpace.kObject)],
                 om.MSpace.kObject)


def move_pivot_to_selected(obj=None, components=None):
    """Align the object's pivot with the selected face, without moving it.

    The pivot jumps to the component centre and its axes line up with the face
    normal, so an object whose rotate channels were frozen to zero gets a
    meaningful local frame back - rotate it afterwards and it turns about the
    face normal.

    Nothing moves in world and the rotate channels stay as they were: the
    orientation is baked into rotateAxis and the mesh points are counter-
    transformed by exactly the amount that introduces, which is the trade
    Maya's own Modify > Bake Pivot makes.
    """
    components = components or selected_components()
    if not components:
        raise RuntimeError("Select one or more faces (or edges, or vertices) first.")

    obj = obj or _component_object(components)
    shape = _shape(obj)
    if cmds.listConnections(shape + ".inMesh", source=True, destination=False):
        raise RuntimeError(
            "{} has construction history feeding its shape. Baking the pivot edits "
            "the points, which history would overwrite - delete history first."
            .format(obj.split("|")[-1]))

    frame = component_frame(components)
    centre = (frame[12], frame[13], frame[14])
    parent_inverse = om.MMatrix(cmds.getAttr(obj + ".parentInverseMatrix[0]"))

    # Points run through rotateAxis and *then* the rotate channels, so the local
    # frame is rotateAxis * rotate. Any rotation already on the object therefore
    # has to be divided back out, or it would tilt the frame off the face - which
    # is not hypothetical: parenting bakes the parent's inverse rotation into the
    # child's rotate channels.
    target = om.MTransformationMatrix(frame * parent_inverse).rotation(
        asQuaternion=True).asMatrix()
    rotate = om.MEulerRotation(
        [math.radians(v) for v in cmds.getAttr(obj + ".rotate")[0]],
        cmds.getAttr(obj + ".rotateOrder")).asMatrix()
    euler = om.MTransformationMatrix(target * rotate.inverse()).rotation(asQuaternion=False)

    cmds.undoInfo(openChunk=True, chunkName="gs_mirrorMovePivot")
    try:
        before = om.MMatrix(cmds.xform(obj, query=True, matrix=True))
        cmds.setAttr(obj + ".rotateAxis",
                     math.degrees(euler.x), math.degrees(euler.y), math.degrees(euler.z))
        cmds.xform(obj, worldSpace=True, pivots=centre)
        after = om.MMatrix(cmds.xform(obj, query=True, matrix=True))
        _transform_points(shape, before * after.inverse())
    finally:
        cmds.undoInfo(closeChunk=True)
    return obj


# ---------------------------------------------------------------------------
# the mirror
# ---------------------------------------------------------------------------
def _mult_matrix(pairs, name):
    node = cmds.createNode("multMatrix", name=name, skipSelect=True)
    for i, (src, attr) in enumerate(pairs):
        cmds.connectAttr("{}.{}".format(src, attr), "{}.matrixIn[{}]".format(node, i))
    return node


def _tag(node):
    if not cmds.attributeQuery(TAG_ATTR, node=node, exists=True):
        cmds.addAttr(node, longName=TAG_ATTR, attributeType="message")


def existing_mirror(mesh):
    """Return the polyMirror node already in this mesh's history, if any."""
    history = cmds.listHistory(_shape(mesh), pruneDagObjects=True) or []
    for node in history:
        if cmds.nodeType(node) == "polyMirror" and \
                cmds.attributeQuery(TAG_ATTR, node=node, exists=True):
            return node
    return None


def _mirror_graph(mesh):
    """(gs_mirror nodes, controller) for `mesh`, or ([], None).

    Walks out from the tagged polyMirror to the spliced transformGeometry nodes
    and back up their multMatrix inputs, so the graph is found no matter how it
    has been renamed since it was built.
    """
    node = existing_mirror(mesh)
    if not node:
        return [], None

    mesh_paths = set(cmds.ls(mesh, long=True) or [])
    mesh_paths.update(cmds.ls(_shape(mesh), long=True) or [])

    nodes = [node]
    pivot = None

    neighbours = (cmds.listConnections(node + ".inputPolymesh", source=True,
                                       destination=False) or [])
    neighbours += (cmds.listConnections(node + ".output", source=False,
                                        destination=True) or [])

    for tg in neighbours:
        if cmds.nodeType(tg) != "transformGeometry":
            continue
        if not cmds.attributeQuery(TAG_ATTR, node=tg, exists=True):
            continue
        nodes.append(tg)
        for mm in cmds.listConnections(tg + ".transform", source=True,
                                       destination=False) or []:
            if cmds.nodeType(mm) != "multMatrix":
                continue
            if not cmds.attributeQuery(TAG_ATTR, node=mm, exists=True):
                continue
            nodes.append(mm)
            for src in cmds.listConnections(mm + ".matrixIn", source=True,
                                            destination=False) or []:
                full = _long(src)
                if not full or full in mesh_paths or pivot:
                    continue
                if cmds.objectType(full, isAType="transform"):
                    pivot = full

    unique = []
    for item in nodes:                  # listConnections can hand back duplicates
        if item not in unique:
            unique.append(item)
    return unique, pivot


def mirror_nodes(mesh):
    """Every gs_mirror DG node in this mesh's history."""
    return _mirror_graph(mesh)[0]


def mirror_pivot(mesh):
    """The controller locator driving `mesh`'s gs_mirror setup, or None."""
    return _mirror_graph(mesh)[1]


def mirror_pivot_of_selection():
    """(mesh, controller) for the first selected mesh carrying a gs_mirror setup."""
    for mesh in selected_meshes():
        pivot = mirror_pivot(mesh)
        if pivot:
            return mesh, pivot
    return None, None


def selected_mirrored_meshes():
    """Every selected mesh that carries a gs_mirror setup."""
    return [mesh for mesh in selected_meshes() if existing_mirror(mesh)]


def create_live_mirror(mesh=None, pivot=None, axis="x", negative=False, merge=True):
    """Mirror `mesh` across a plane through a pivot locator, normal to its local `axis`.

    axis     -- "x" | "y" | "z", in the pivot locator's local space
    negative -- which side of the plane the geometry is mirrored toward
    merge    -- weld border vertices at Maya's automatic threshold

    The controller is always a gs_mirror pivot locator. When `pivot` is not
    already one, a fresh locator is created at the picked object's pivot - or at
    the mesh's own pivot when nothing is picked - and drives the mirror instead.
    """
    axis = axis.lower()
    if axis not in AXES:
        raise ValueError("axis must be x, y or z")

    if mesh is None:
        meshes = selected_meshes()
        if len(meshes) != 1:
            raise RuntimeError("Select exactly one polygon mesh to mirror.")
        mesh = meshes[0]

    if pivot is None:
        pivot = get_mirror_object()

    # Whatever was picked only seeds the locator's placement; the mesh itself is
    # the fallback seed so the mirror plane starts on the mesh's own pivot.
    source = pivot if pivot and cmds.objExists(pivot) else mesh

    if existing_mirror(mesh):
        raise RuntimeError("{} already has a gs_mirror setup. Remove it before "
                           "mirroring again, or re-target its pivot."
                           .format(mesh.split("|")[-1]))

    base = mesh.split("|")[-1]
    flags = dict(MIRROR_FLAGS)
    flags.update(axis=AXES[axis],
                 axisDirection=0 if negative else 1,
                 mergeMode=MERGE_ON if merge else MERGE_OFF)

    cmds.undoInfo(openChunk=True, chunkName="gs_mirrorCreate")
    try:
        pivot = pivot_locator_for(source)

        mirror_node = cmds.polyMirrorFace(mesh, **flags)[0]
        _tag(mirror_node)

        upstream = cmds.listConnections(mirror_node + ".inputPolymesh",
                                        plugs=True, source=True, destination=False)
        downstream = cmds.listConnections(mirror_node + ".output",
                                          plugs=True, source=False, destination=True)
        if not upstream or not downstream:
            raise RuntimeError("Unexpected history on {} - cannot splice.".format(base))

        tg_in = cmds.createNode("transformGeometry", name=base + "_mirrorInto",
                                skipSelect=True)
        tg_out = cmds.createNode("transformGeometry", name=base + "_mirrorBack",
                                 skipSelect=True)

        cmds.connectAttr(upstream[0], tg_in + ".inputGeometry", force=True)
        cmds.connectAttr(tg_in + ".outputGeometry", mirror_node + ".inputPolymesh",
                         force=True)
        cmds.connectAttr(mirror_node + ".output", tg_out + ".inputGeometry", force=True)
        cmds.connectAttr(tg_out + ".outputGeometry", downstream[0], force=True)

        into = _mult_matrix([(mesh, "worldMatrix[0]"),
                             (pivot, "worldInverseMatrix[0]")],
                            base + "_intoPivotSpace")
        back = _mult_matrix([(pivot, "worldMatrix[0]"),
                             (mesh, "worldInverseMatrix[0]")],
                            base + "_backToLocal")
        cmds.connectAttr(into + ".matrixSum", tg_in + ".transform")
        cmds.connectAttr(back + ".matrixSum", tg_out + ".transform")

        for node in (tg_in, tg_out, into, back):
            _tag(node)
    finally:
        cmds.undoInfo(closeChunk=True)

    return mirror_node


def set_merge(mesh, merge):
    """Toggle the weld on an existing mirror setup."""
    node = existing_mirror(mesh)
    if not node:
        raise RuntimeError("No gs_mirror setup found on {}.".format(mesh.split("|")[-1]))
    cmds.setAttr(node + ".mergeMode", MERGE_ON if merge else MERGE_OFF)
    return node


# ---------------------------------------------------------------------------
# tearing a mirror down - either way the mesh ends up an ordinary object with
# no gs_mirror nodes left on it; they differ only in which shape it keeps
# ---------------------------------------------------------------------------
def _delete_unused_controller(pivot):
    """Delete `pivot` unless it still drives another mesh's mirror."""
    if not pivot or not cmds.objExists(pivot) or not is_pivot_locator(pivot):
        return False
    pivot_path = _long(pivot)
    for other in mirror_pairs().values():
        if other and _long(other) == pivot_path:
            return False
    cmds.delete(pivot)
    return True


def remove_mirror(mesh):
    """Delete the setup and let the mesh spring back to its un-mirrored half.

    Only the gs_mirror nodes are deleted; Maya reconnects the history stream
    across the gap, so any other construction history on the mesh survives.
    """
    nodes, pivot = _mirror_graph(mesh)
    if not nodes:
        raise RuntimeError("No gs_mirror setup found on {}.".format(mesh.split("|")[-1]))

    cmds.undoInfo(openChunk=True, chunkName="gs_mirrorRemove")
    try:
        cmds.delete([node for node in nodes if cmds.objExists(node)])
        removed = _delete_unused_controller(pivot)
    finally:
        cmds.undoInfo(closeChunk=True)
    return removed


def apply_mirror(mesh):
    """Freeze the mirrored result into the mesh and delete the setup.

    The mesh keeps exactly the shape it has on screen. Baking the mirror means
    collapsing the whole history stream it sits in, so this deletes all of the
    mesh's construction history, not only the gs_mirror nodes - the same trade
    Maya's own Edit > Delete by Type > History makes.
    """
    nodes, pivot = _mirror_graph(mesh)
    if not nodes:
        raise RuntimeError("No gs_mirror setup found on {}.".format(mesh.split("|")[-1]))

    cmds.undoInfo(openChunk=True, chunkName="gs_mirrorApply")
    try:
        cmds.delete(mesh, constructionHistory=True)
        # the multMatrix nodes hang off transformGeometry.transform rather than
        # the mesh stream, so deleting history leaves them orphaned
        leftovers = [node for node in nodes if cmds.objExists(node)]
        if leftovers:
            cmds.delete(leftovers)
        removed = _delete_unused_controller(pivot)
    finally:
        cmds.undoInfo(closeChunk=True)
    return removed


# ---------------------------------------------------------------------------
# outliner colouring - one hue per pivot, shared by the pivot and every mesh
# it drives (adapted from modeling/instance_utility.OutlinerColorizer)
# ---------------------------------------------------------------------------
def _hsv_colors(count, saturation=COLOR_SATURATION, value=COLOR_VALUE):
    if count <= 0:
        return []
    colors = []
    for i in range(count):
        hue = (i / float(count)) if count > 1 else 0.0
        colors.append(colorsys.hsv_to_rgb(hue, saturation, value))
    return colors


def _set_outliner_color(node, rgb):
    if not cmds.objExists(node):
        return False
    try:
        cmds.setAttr("{}.useOutlinerColor".format(node), 1)
        cmds.setAttr("{}.outlinerColor".format(node), rgb[0], rgb[1], rgb[2],
                     type="double3")
        return True
    except Exception:
        return False


def _clear_outliner_color(node):
    if not cmds.objExists(node):
        return False
    try:
        if not cmds.attributeQuery("useOutlinerColor", node=node, exists=True):
            return False
        if not cmds.getAttr("{}.useOutlinerColor".format(node)):
            return False
        cmds.setAttr("{}.useOutlinerColor".format(node), 0)
        cmds.setAttr("{}.outlinerColor".format(node), 0, 0, 0, type="double3")
        return True
    except Exception:
        return False


def mirror_pairs():
    """{mesh transform: pivot or None} for every gs_mirror setup in the scene."""
    pairs = {}
    for node in cmds.ls(type="polyMirror", long=True) or []:
        if not cmds.attributeQuery(TAG_ATTR, node=node, exists=True):
            continue
        for shape in cmds.listHistory(node, future=True, allFuture=True) or []:
            if cmds.nodeType(shape) != "mesh":
                continue
            try:
                if cmds.getAttr(shape + ".intermediateObject"):
                    continue
            except Exception:
                continue
            parents = cmds.listRelatives(shape, parent=True, fullPath=True) or []
            if not parents or parents[0] in pairs:
                continue
            pairs[parents[0]] = mirror_pivot(parents[0])
    return pairs


def _all_pivot_locators():
    return cmds.ls("*." + PIVOT_ATTR, objectsOnly=True, long=True) or []


def colorize_mirrors():
    """Paint every mirrored mesh and its pivot, one colour per pivot."""
    pairs = mirror_pairs()
    if not pairs:
        raise RuntimeError("No gs_mirror setups found in the scene.")

    groups = {}
    for mesh, pivot in pairs.items():
        group = groups.setdefault(pivot or mesh, set())
        group.add(mesh)
        if pivot:
            group.add(pivot)

    keys = sorted(groups)
    colors = _hsv_colors(len(keys))

    count = 0
    cmds.undoInfo(openChunk=True, chunkName="gs_mirrorColorize")
    try:
        for key, color in zip(keys, colors):
            for node in sorted(groups[key]):
                if _set_outliner_color(node, color):
                    count += 1
    finally:
        cmds.undoInfo(closeChunk=True)
    return count


def reset_mirror_colors():
    """Clear outliner colours on mirrored meshes and gs_mirror pivots only."""
    nodes = set(_all_pivot_locators())
    for mesh, pivot in mirror_pairs().items():
        nodes.add(mesh)
        if pivot:
            nodes.add(pivot)

    count = 0
    cmds.undoInfo(openChunk=True, chunkName="gs_mirrorResetColors")
    try:
        for node in sorted(nodes):
            if _clear_outliner_color(node):
                count += 1
    finally:
        cmds.undoInfo(closeChunk=True)
    return count
