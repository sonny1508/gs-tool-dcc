"""
gs_mirror.core - no UI, all the actual work.

History chain built on the target mesh when a pivot object is picked:

    origShape.outMesh
      -> transformGeometry   mesh local space -> pivot space    det +1
      -> polyMirror          mirror on local axis (+ weld)      winding handled internally
      -> transformGeometry   pivot space -> mesh local space    det +1
      -> shape.inMesh

Both transformGeometry matrices are driven by multMatrix nodes wired to the live
worldMatrix / worldInverseMatrix of the mesh and the pivot, so moving or rotating
the pivot updates the mirror interactively. Neither has a negative determinant,
so nothing in the stream is ever inside out and no polyNormal fix-up is needed.

With no pivot picked, the mirror runs in the mesh's own object space, which is
Maya's default Mesh > Mirror behaviour.
"""

import maya.cmds as cmds
import maya.api.OpenMaya as om

AXES = {"x": 0, "y": 1, "z": 2}

SETTINGS_NODE = "gs_mirrorToolSettings"
TAG_ATTR = "GSMirrorNode"

# One place to tweak if the flag semantics differ in your Maya build.
#   mirrorAxis:         0 = bounding box, 1 = object, 2 = world
#   axisDirection:      0 = negative, 1 = positive
#   mergeMode:          0 = none, 1 = merge border vertices, 2 = bridge
#   mergeThresholdType: 0 = custom (uses mergeThreshold), 1 = automatic
MIRROR_FLAGS = {
    "mirrorAxis": 1,
    "pivot": (0.0, 0.0, 0.0),
    "mergeThresholdType": 1,   # automatic - Maya's default threshold
    "smoothingAngle": 30.0,
    "flipUVs": False,
    "constructionHistory": True,
}

# Which component-frame axis becomes which local axis of the pivot object.
# Maya's own component axis orientation puts the normal on Z; if yours disagrees,
# reorder this tuple and nothing else changes.
FRAME_AXES = ("tangent", "binormal", "normal")


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
    """Store `node` (or the current selection) as the mirror pivot."""
    if node is None:
        selected = cmds.ls(selection=True, transforms=True, long=True)
        if not selected:
            raise RuntimeError("Select a transform to use as the mirror pivot.")
        node = selected[0]
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


def create_pivot_locator(name="gs_mirrorPivot#"):
    """Make a locator, store it as the mirror pivot, and return it."""
    locator = cmds.spaceLocator(name=name)[0]
    cmds.setAttr(locator + ".overrideEnabled", 1)
    cmds.setAttr(locator + ".overrideRGBColors", 1)
    cmds.setAttr(locator + ".overrideColorRGB", 0.105, 0.693, 0.718)
    set_mirror_object(locator)
    return locator


# ---------------------------------------------------------------------------
# component frame -> pivot orientation
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


def snap_pivot_to_component(pivot=None, components=None):
    """Move and orient the pivot object to match the selected component's frame.

    With no pivot picked yet, one is created. Determinant is +1, so the matrix
    decomposes cleanly to rotation with unit scale regardless of rotate order.
    """
    components = components or cmds.ls(selection=True, flatten=True) or []
    matrix = component_frame(components)

    pivot = pivot or get_mirror_object()
    cmds.undoInfo(openChunk=True, chunkName="gs_mirrorSnapPivot")
    try:
        if not pivot:
            pivot = create_pivot_locator()
        cmds.xform(pivot, worldSpace=True, matrix=list(matrix))
    finally:
        cmds.undoInfo(closeChunk=True)
    return pivot


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


def create_live_mirror(mesh=None, pivot=None, axis="x", negative=False, merge=True):
    """Mirror `mesh` across a plane through `pivot`, normal to the pivot's local `axis`.

    axis     -- "x" | "y" | "z", in the pivot object's local space
    negative -- which side of the plane the geometry is mirrored toward
    merge    -- weld border vertices at Maya's automatic threshold
    """
    axis = axis.lower()
    if axis not in AXES:
        raise ValueError("axis must be x, y or z")

    if mesh is None:
        meshes = [obj for obj in cmds.ls(selection=True, objectsOnly=True, long=True)
                  if cmds.listRelatives(obj, shapes=True, noIntermediate=True, type="mesh")]
        if len(meshes) != 1:
            raise RuntimeError("Select exactly one polygon mesh to mirror.")
        mesh = meshes[0]

    if pivot is None:
        pivot = get_mirror_object()
    if pivot and cmds.ls(pivot, long=True) == cmds.ls(mesh, long=True):
        raise RuntimeError("The mirror pivot cannot be the mesh being mirrored.")

    if existing_mirror(mesh):
        raise RuntimeError("{} already has a gs_mirror setup. Remove it before "
                           "mirroring again, or re-target its pivot."
                           .format(mesh.split("|")[-1]))

    base = mesh.split("|")[-1]
    flags = dict(MIRROR_FLAGS)
    flags.update(axis=AXES[axis],
                 axisDirection=0 if negative else 1,
                 mergeMode=1 if merge else 0)

    cmds.undoInfo(openChunk=True, chunkName="gs_mirrorCreate")
    try:
        mirror_node = cmds.polyMirrorFace(mesh, **flags)[0]
        _tag(mirror_node)

        if pivot:
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
    cmds.setAttr(node + ".mergeMode", 1 if merge else 0)
    return node
