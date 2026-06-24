# -*- coding: utf-8 -*-
"""
GS Normal Tools (Python / OpenMaya 2.0 rewrite).

A fast reimplementation of the MEL "DM Normal Tools" by Dmytro Lystopad.

Why this exists
---------------
The original MEL tool drove every topology/normal query through per-component
commands (polyInfo, polyListComponentConversion, polyEvaluate) inside nested
loops, and even created/destroyed a UI widget per vertex-face for set
intersection. On anything but trivial meshes that is catastrophically slow.

This version reads each mesh once through MFnMesh / the iterators, computes the
new normals in memory, and writes them back in a single setFaceVertexNormals
call. The same operation that took minutes now takes milliseconds.

Feature parity with the MEL version:
  * Align Normals: Face Weighted / Average, with optional "Keep Hard Edges".
  * Works on whole objects, multiple objects, or a component selection
    (vertices, faces, vertex-faces, or edges).
  * Lock / Unlock normals.
  * Select Hard / Soft edges.
  * Get / Set normal on the selected components.
"""

import contextlib

import maya.cmds as cmds
import maya.api.OpenMaya as om

# --- Maya 2.0 API plugin contract (harmless for a pure-Python tool module) ---
maya_useNewAPI = True


@contextlib.contextmanager
def _undo_disabled():
    """Run a block with Maya's undo queue suspended.

    The fast normal operations write through MFnMesh.setFaceVertexNormals, a
    direct DG edit Maya does not record on the undo stack. Leaving the queue
    enabled meant a later Ctrl+Z popped an unrelated/partial entry and tried to
    revert a mesh whose normals it had no record of - which corrupted or even
    cleared the normals. Suspending the queue for the whole operation makes
    these writes completely invisible to undo, so Ctrl+Z can never touch them.
    """
    prev = cmds.undoInfo(q=True, state=True)
    cmds.undoInfo(stateWithoutFlush=False)
    try:
        yield
    finally:
        cmds.undoInfo(stateWithoutFlush=prev)


# =====================================================================
#  Selection helpers
# =====================================================================

def _iter_selected_mesh_components():
    """Yield (MDagPath, MObject component) pairs for the active selection.

    The component MObject is kMeshVertComponent / kMeshPolygonComponent /
    kMeshVertFaceComponent / kMeshEdgeComponent, or a null MObject when a whole
    object (transform/shape) is selected.
    """
    sel = om.MGlobal.getActiveSelectionList()
    for i in range(sel.length()):
        dag, comp = sel.getComponent(i)
        if dag.apiType() == om.MFn.kTransform:
            try:
                dag.extendToShape()
            except RuntimeError:
                continue
        if not dag.hasFn(om.MFn.kMesh):
            continue
        yield dag, comp


def _component_vertices(mesh_fn, dag, comp):
    """Return the set of vertex ids targeted by a selection component.

    A null/empty component means "the whole mesh", so every vertex is returned.
    Faces, edges and vertex-faces are converted to their incident vertices.
    """
    if comp.isNull():
        return set(range(mesh_fn.numVertices))

    api = comp.apiType()
    if api == om.MFn.kMeshVertComponent:
        return set(om.MFnSingleIndexedComponent(comp).getElements())

    if api == om.MFn.kMeshPolygonComponent:
        faces = om.MFnSingleIndexedComponent(comp).getElements()
        verts = set()
        for f in faces:
            verts.update(mesh_fn.getPolygonVertices(f))
        return verts

    if api == om.MFn.kMeshEdgeComponent:
        edges = om.MFnSingleIndexedComponent(comp).getElements()
        verts = set()
        for e in edges:
            v2 = mesh_fn.getEdgeVertices(e)
            verts.update(v2)
        return verts

    if api == om.MFn.kMeshVertFaceComponent:
        # Double-indexed: (vertexId, faceId) pairs; we only need the vertices.
        ids = om.MFnDoubleIndexedComponent(comp).getElements()
        return set(v for v, _ in ids)

    # Unknown component kind: fall back to the whole mesh.
    return set(range(mesh_fn.numVertices))


# =====================================================================
#  Core: align normals on a single mesh
# =====================================================================

def _align_mesh(dag, comp, method, keep_hard_edges):
    """Compute aligned vertex normals for one mesh.

    method          : "face_weighted" (largest-face normal) or "average"
                      (unweighted average) - matching the original tool.
    keep_hard_edges : when True, the fan around each vertex is split at hard
                      edges so they stay sharp; otherwise every vertex gets a
                      single normal across all its vertex-faces.

    Returns (mesh_fn, normals, face_ids, vert_ids) - parallel arrays ready for a
    single fast MFnMesh.setFaceVertexNormals call. Returns None if there is
    nothing to do.

    All topology/geometry is read once via the API and the write is a single
    batched API call (see align_normals). The previous version issued one
    cmds.polyNormalPerVertex per unique normal; on a smooth mesh that is ~one
    command per vertex - thousands of command round-trips - which is what made
    it slow again.
    """
    mesh = om.MFnMesh(dag)
    target_verts = _component_vertices(mesh, dag, comp)
    if not target_verts:
        return None

    # ---- read everything we need, once ----
    # Match the original tool's spaces exactly:
    #   * Face NORMAL value -> OBJECT space. getPolygonNormal(kObject) matches
    #     what polyInfo -fn returned, and setFaceVertexNormals writes object
    #     space, so the value round-trips correctly even on transformed objects.
    #   * Face AREA, used only to pick the largest face -> WORLD space, matching
    #     the original's `polyEvaluate -wfa`. Using object-space area here let a
    #     non-uniform transform flip which face "wins" on near-equal quads
    #     (e.g. around a torus), giving inconsistent results.
    #
    # getPolygonNormal() returns a fresh MVector per call - unlike the iterator's
    # getNormal(), whose result is tied to iterator state and aliases if cached.
    num_faces = mesh.numPolygons
    face_normals = [None] * num_faces   # unit geometric normal per face
    face_area = [0.0] * num_faces

    for f in range(num_faces):
        n = mesh.getPolygonNormal(f, om.MSpace.kObject)
        face_normals[f] = om.MVector(n.x, n.y, n.z).normalize()

    poly_it = om.MItMeshPolygon(dag)
    while not poly_it.isDone():
        face_area[poly_it.index()] = float(poly_it.getArea(om.MSpace.kWorld))
        poly_it.next()

    # Edges Maya marks hard, as frozenset({vtxA, vtxB}) pairs.
    hard_edge_pairs = set()
    if keep_hard_edges:
        edge_it = om.MItMeshEdge(dag)
        while not edge_it.isDone():
            if not edge_it.isSmooth:
                hard_edge_pairs.add(
                    frozenset((edge_it.vertexId(0), edge_it.vertexId(1)))
                )
            edge_it.next()

    # ---- compute parallel arrays for one batched setFaceVertexNormals call ----
    normals = om.MVectorArray()
    face_ids = om.MIntArray()
    vert_ids = om.MIntArray()

    vert_it = om.MItMeshVertex(dag)
    while not vert_it.isDone():
        v = vert_it.index()
        if v not in target_verts:
            vert_it.next()
            continue

        connected_faces = list(vert_it.getConnectedFaces())
        if not connected_faces:
            vert_it.next()
            continue

        groups = _smoothing_groups(
            v, connected_faces, mesh, hard_edge_pairs, keep_hard_edges
        )

        for group in groups:
            normal = _group_normal(group, method, face_normals, face_area)
            for f in group:
                normals.append(normal)
                face_ids.append(f)
                vert_ids.append(v)

        vert_it.next()

    if len(normals) == 0:
        return None
    return mesh, normals, face_ids, vert_ids


def _smoothing_groups(vertex, faces, mesh, hard_edge_pairs, keep_hard_edges):
    """Partition the faces around `vertex` into smoothing groups.

    Replicates the original tool exactly:
      * Keep Hard Edges OFF -> every connected face is one group, so the vertex
        gets a single normal across all its vertex-faces.
      * Keep Hard Edges ON  -> faces are linked only across SOFT edges incident
        to `vertex`; hard edges split the fan into separate groups, keeping the
        hard edge visually sharp.
    """
    faces = list(faces)
    if not keep_hard_edges or len(faces) == 1:
        return [faces]

    # Adjacency: link faces that meet at a soft (non-hard) edge incident here.
    adj = {f: set() for f in faces}
    for i in range(len(faces)):
        fi = faces[i]
        vi = set(mesh.getPolygonVertices(fi))
        for j in range(i + 1, len(faces)):
            fj = faces[j]
            shared = vi & set(mesh.getPolygonVertices(fj))
            if vertex not in shared:
                continue
            other = shared - {vertex}
            if len(other) != 1:
                continue
            far = next(iter(other))
            if frozenset((vertex, far)) in hard_edge_pairs:
                continue  # hard edge -> keep the two faces separate
            adj[fi].add(fj)
            adj[fj].add(fi)

    # Connected components over the soft-edge adjacency.
    groups = []
    unvisited = set(faces)
    while unvisited:
        start = unvisited.pop()
        stack = [start]
        comp = {start}
        while stack:
            cur = stack.pop()
            for nxt in adj[cur]:
                if nxt in unvisited:
                    unvisited.remove(nxt)
                    comp.add(nxt)
                    stack.append(nxt)
        groups.append(list(comp))
    return groups


def _group_normal(group, method, face_normals, face_area):
    """The normal a smoothing group's vertex-faces should receive.

    Three methods:
      * "face_weighted" -> the full normal of the SINGLE largest-area face in the
        group. This is the original tool's behaviour exactly (dmnt_getLargestFace
        + dmnt_getNormalFromFace). Great on hard-surface meshes where one face
        dominates; on curved meshes with equal-area faces (e.g. a torus) the
        tie-break is arbitrary, so prefer "area_weighted" there.
      * "area_weighted" -> sum of face normals weighted by face area. Matches
        Maya's own smooth vertex normals on curved meshes while still letting
        large faces dominate on hard-surface models.
      * "average" -> unweighted average of the group's face normals.

    Returns a fresh, normalized MVector.
    """
    if method == "face_weighted":
        largest = max(group, key=lambda f: face_area[f])
        src = face_normals[largest]
        return om.MVector(src.x, src.y, src.z)

    result = om.MVector(0.0, 0.0, 0.0)
    if method == "area_weighted":
        for f in group:
            result += face_normals[f] * face_area[f]
    else:  # "average"
        for f in group:
            result += face_normals[f]

    length = result.length()
    if length > 1e-12:
        result /= length
    else:
        src = face_normals[group[0]]
        result = om.MVector(src.x, src.y, src.z)
    return result


# =====================================================================
#  Public operations (called from the UI)
# =====================================================================

def align_normals(method, keep_hard_edges):
    """Align normals on every selected mesh / component.

    Geometry is read once via the API and written back in a single
    MFnMesh.setFaceVertexNormals call per object (milliseconds, even on smooth
    meshes). This direct API write is NOT on Maya's undo stack and the whole
    operation runs with the undo queue suspended (see _undo_disabled), so Ctrl+Z
    cannot revert - or corrupt - it. Re-run Align (or restore from history) if
    you need to change it.
    """
    sel = cmds.ls(sl=True, long=True)
    if not sel:
        cmds.warning("Please select a mesh or components.")
        return

    targets = list(_iter_selected_mesh_components())
    if not targets:
        cmds.warning("Selection is not a mesh.")
        return

    did_any = False
    with _undo_disabled():
        for dag, comp in targets:
            result = _align_mesh(dag, comp, method, keep_hard_edges)
            if result is None:
                continue
            mesh, normals, face_ids, vert_ids = result
            mesh.setFaceVertexNormals(normals, face_ids, vert_ids, om.MSpace.kObject)
            # Tell Maya the mesh changed so the viewport reshades immediately.
            # Without this the new normals are applied but the display stays
            # stale until the user re-selects the object.
            mesh.updateSurface()
            did_any = True

        if not did_any:
            cmds.warning("Nothing to align.")
            return

        cmds.select(sel, r=True)
    cmds.refresh()
    print("Vertex normals have been aligned\n")


def unlock_normals():
    """Unlock normals on the selected object(s) or only the selected components.

    Works in both contexts from the one button: converting the selection to
    vertex-faces expands a whole-object selection to every vertex-face, and a
    component selection (vertices, faces, edges, vertex-faces) to just those.
    Unlocking restores Maya's stored softness, so we leave edge hardness as-is.
    """
    sel = cmds.ls(sl=True, long=True)
    if not sel:
        cmds.warning("Please select a mesh or components.")
        return
    vtx_faces = cmds.polyListComponentConversion(sel, tvf=True)
    if not vtx_faces:
        cmds.warning("Please select a mesh or components.")
        return

    cmds.undoInfo(openChunk=True)
    try:
        cmds.polyNormalPerVertex(vtx_faces, ufn=True)
    finally:
        cmds.undoInfo(closeChunk=True)

    cmds.select(sel, r=True)
    print("Vertex normals have been unlocked\n")


def lock_normals():
    """Lock vertex normals at their current values."""
    sel = cmds.ls(sl=True, long=True)
    vtx_faces = cmds.polyListComponentConversion(tvf=True)
    if not vtx_faces:
        cmds.warning("Please select a mesh or components.")
        return

    cmds.undoInfo(openChunk=True)
    try:
        cmds.polyNormalPerVertex(vtx_faces, freezeNormal=True)
    finally:
        cmds.undoInfo(closeChunk=True)

    if sel:
        cmds.select(sel, r=True)
    print("Vertex normals have been locked\n")


def select_edges(get_hard):
    """Select hard (get_hard=1) or soft (get_hard=0) edges from the selection.

    Uses MItMeshEdge.isSmooth - a single in-memory pass per mesh, no per-edge
    polyInfo calls.
    """
    result = []
    for dag, comp in _iter_selected_mesh_components():
        name = dag.fullPathName()
        edge_it = om.MItMeshEdge(dag)
        while not edge_it.isDone():
            is_hard = not edge_it.isSmooth
            if (get_hard and is_hard) or (not get_hard and not is_hard):
                result.append("{0}.e[{1}]".format(name, edge_it.index()))
            edge_it.next()

    if result:
        cmds.select(result, r=True)
    else:
        cmds.warning("No matching edges found.")


def get_normal_to_ui():
    """Read the average normal of the selected components into the UI fields."""
    sel = cmds.ls(sl=True, fl=True, long=True)
    if not sel:
        cmds.warning("Select a component first.")
        return
    n = cmds.polyNormalPerVertex(
        cmds.polyListComponentConversion(sel, tvf=True), q=True, xyz=True
    )
    if not n:
        return
    avg = om.MVector(0, 0, 0)
    for i in range(0, len(n), 3):
        avg += om.MVector(n[i], n[i + 1], n[i + 2])
    avg.normalize()
    cmds.floatField("dmnt_nx", e=True, v=avg.x)
    cmds.floatField("dmnt_ny", e=True, v=avg.y)
    cmds.floatField("dmnt_nz", e=True, v=avg.z)


def set_normal_from_ui():
    """Apply the UI's normal vector to the selected components."""
    sel = cmds.ls(sl=True, fl=True, long=True)
    if not sel:
        cmds.warning("Select a component first.")
        return
    x = cmds.floatField("dmnt_nx", q=True, v=True)
    y = cmds.floatField("dmnt_ny", q=True, v=True)
    z = cmds.floatField("dmnt_nz", q=True, v=True)
    vtf = cmds.ls(cmds.polyListComponentConversion(sel, tvf=True), fl=True, long=True)
    cmds.polyNormalPerVertex(vtf, xyz=(x, y, z))
    cmds.select(sel, r=True)


def average_from_edge():
    """Average the normals of each selected edge's two faces onto its vertices.

    Replicates the original dmnt_setAverageNormalFromEdges: for every selected
    edge, average the normals of the faces connected to that edge and assign that
    single normal to both of the edge's vertices (across all of their
    vertex-faces). Useful for softening shading across a specific edge loop.
    """
    if not cmds.filterExpand(cmds.ls(sl=True, fl=True), sm=32):
        cmds.warning("Select at least one edge to perform Average From Edge.")
        return

    sel = cmds.ls(sl=True, long=True)
    did_any = False

    # Like align_normals, this writes through setFaceVertexNormals (a direct DG
    # edit Maya does not record), so suspend the undo queue for the whole pass -
    # otherwise a later Ctrl+Z corrupts normals it has no record of.
    with _undo_disabled():
        # Per selected mesh, collect that mesh's selected edge ids from the
        # component.
        for dag, comp in _iter_selected_mesh_components():
            if comp.isNull() or comp.apiType() != om.MFn.kMeshEdgeComponent:
                continue
            edge_ids = om.MFnSingleIndexedComponent(comp).getElements()
            if not edge_ids:
                continue

            mesh = om.MFnMesh(dag)
            face_normals = {}

            def _face_normal(f):
                if f not in face_normals:
                    n = mesh.getPolygonNormal(f, om.MSpace.kObject)
                    face_normals[f] = om.MVector(n.x, n.y, n.z).normalize()
                return face_normals[f]

            normals = om.MVectorArray()
            face_ids = om.MIntArray()
            vert_ids = om.MIntArray()

            edge_it = om.MItMeshEdge(dag)
            vert_it = om.MItMeshVertex(dag)
            for eid in edge_ids:
                edge_it.setIndex(eid)
                conn_faces = list(edge_it.getConnectedFaces())
                if not conn_faces:
                    continue

                avg = om.MVector(0.0, 0.0, 0.0)
                for f in conn_faces:
                    avg += _face_normal(f)
                if avg.length() <= 1e-12:
                    continue
                avg.normalize()

                # Assign to both edge vertices across all their vertex-faces, as
                # the original (polyNormalPerVertex on the whole vertex) did.
                for v in (edge_it.vertexId(0), edge_it.vertexId(1)):
                    vert_it.setIndex(v)
                    for f in vert_it.getConnectedFaces():
                        normals.append(avg)
                        face_ids.append(f)
                        vert_ids.append(v)

            if len(normals):
                mesh.setFaceVertexNormals(normals, face_ids, vert_ids,
                                          om.MSpace.kObject)
                mesh.updateSurface()
                did_any = True

        if not did_any:
            cmds.warning("Nothing to average.")
            return

        cmds.select(sel, r=True)
    cmds.refresh()
    print("Average normal from edges applied\n")


def switch_to_normal_edit_tool():
    cmds.setToolTo("polyVertexNormalEdit")


def on_settings_changed(*_):
    show = cmds.checkBox("dmnt_showNormalsCB", q=True, v=True)
    size = cmds.floatSliderGrp("dmnt_normalSizeFSG", q=True, v=True)
    cmds.polyOptions(dn=show, pt=True, sn=size, gl=True)


# =====================================================================
#  UI
# =====================================================================

WINDOW = "GSNormalToolsWin"


# radioButton control name -> method name.
_METHOD_BUTTONS = (
    ("dmnt_rbFaceWeighted", "face_weighted", "Face Weighted"),
    ("dmnt_rbAreaWeighted", "area_weighted", "Area Weighted"),
    ("dmnt_rbAverage",      "average",       "Average"),
)
_BUTTON_TO_METHOD = {ctrl: name for ctrl, name, _ in _METHOD_BUTTONS}


def _align_cb(*_):
    # radioCollection -q -select returns the selected button's name; depending on
    # Maya version this can be the full path or just the short name, so match on
    # the trailing control name to be safe.
    selected = cmds.radioCollection("dmnt_methodRC", q=True, select=True) or ""
    short = selected.split("|")[-1]
    method = _BUTTON_TO_METHOD.get(short, "face_weighted")
    keep_hard = cmds.checkBox("dmnt_keepHardCB", q=True, v=True)
    align_normals(method, keep_hard)


def show_ui():
    if cmds.window(WINDOW, exists=True):
        cmds.deleteUI(WINDOW)

    cmds.window(WINDOW, title="GS Normal Tools 2.0", sizeable=False, rtf=True,
                width=300)
    cmds.columnLayout(adj=True, rs=4, co=("both", 4))

    cmds.frameLayout(label="Align Normals", bgs=True, mh=6, mw=6)
    cmds.rowLayout(nc=2, cl2=("left", "center"),
                   ct2=("both", "both"), cw2=(136, 136))

    # Left: vertical list of method options + Keep Hard Edges.
    cmds.columnLayout(adj=True, rs=2, w=136)
    cmds.radioCollection("dmnt_methodRC")
    for ctrl, _name, label in _METHOD_BUTTONS:
        cmds.radioButton(ctrl, l=label)
    cmds.radioCollection("dmnt_methodRC", e=True, select="dmnt_rbFaceWeighted")
    cmds.separator(h=4, style="none")
    cmds.checkBox("dmnt_keepHardCB", l="Keep Hard Edges", v=False,
                  ann="Preserve shading on hard edges so they still appear "
                      "sharp.")
    cmds.setParent("..")

    # Right: Align button matches the other buttons' width, fills the height.
    cmds.button(l="Align Normals", c=_align_cb, w=136, h=100,
                ann="Align vertex normals on the selected object(s) or "
                    "components using the chosen method.")
    cmds.setParent("..")
    cmds.setParent("..")

    cmds.frameLayout(label="Adjust Normals", bgs=True, mh=6, mw=6)
    cmds.columnLayout(adj=True, rs=4)
    # X/Y/Z: three equal-width fields filling the row; Get/Set equal sized.
    # Widths sum to ~262 (= the 136+136 button columns) so the row fills across.
    cmds.rowLayout(nc=5, cw5=(59, 59, 59, 45, 45),
                   ct5=("both", "both", "both", "both", "both"))
    cmds.floatField("dmnt_nx", v=0, pre=4, ann="Normal X")
    cmds.floatField("dmnt_ny", v=0, pre=4, ann="Normal Y")
    cmds.floatField("dmnt_nz", v=0, pre=4, ann="Normal Z")
    cmds.button(l="Get", c=lambda *_: get_normal_to_ui())
    cmds.button(l="Set", c=lambda *_: set_normal_from_ui())
    cmds.setParent("..")
    cmds.rowLayout(nc=2, cw2=(136, 136))
    cmds.button(l="Average From Edge", w=136, c=lambda *_: average_from_edge(),
                ann="Apply the average normal of each selected edge's connected "
                    "faces to that edge's vertices.")
    cmds.button(l="Vertex Normal Edit Tool", w=136,
                c=lambda *_: switch_to_normal_edit_tool())
    cmds.setParent("..")
    cmds.rowLayout(nc=2, cw2=(136, 136))
    cmds.button(l="Unlock Normals", w=136, c=lambda *_: unlock_normals())
    cmds.button(l="Lock Normals", w=136, c=lambda *_: lock_normals())
    cmds.setParent("..")
    cmds.setParent("..")
    cmds.setParent("..")

    cmds.frameLayout(label="Selection", bgs=True, mh=6, mw=6)
    cmds.rowLayout(nc=2, cw2=(136, 136))
    cmds.button(l="Select Hard Edges", w=136, c=lambda *_: select_edges(1))
    cmds.button(l="Select Soft Edges", w=136, c=lambda *_: select_edges(0))
    cmds.setParent("..")
    cmds.setParent("..")

    cmds.frameLayout(label="Display options", bgs=True, mh=6, mw=6)
    cmds.columnLayout(adj=True)
    cmds.checkBox("dmnt_showNormalsCB", l="Show Vertex Normals",
                  cc=on_settings_changed, v=False)
    cmds.floatSliderGrp("dmnt_normalSizeFSG", l="Normal Size:", field=True,
                        min=0.1, max=25, fieldMinValue=0.1, fieldMaxValue=500,
                        value=5.0, cw3=(70, 70, 50),
                        cc=on_settings_changed, dc=on_settings_changed)
    cmds.setParent("..")
    cmds.setParent("..")

    cmds.separator(h=8)
    cmds.text(l="GS Normal Tools - Better Performance", en=False)

    cmds.showWindow(WINDOW)


if __name__ == "__main__":
    show_ui()
