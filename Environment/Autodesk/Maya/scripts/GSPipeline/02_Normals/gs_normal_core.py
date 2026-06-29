# -*- coding: utf-8 -*-
"""
GS Normal Tools - core snapshot / apply / restore logic (Maya 2022+, Python 3).

This is a plain importable module (no Maya command, no plugin, no sys.modules
tricks). It owns the undo-critical primitives shared by the UI and the thin
gsNormalApiApply command:

  * capture_mesh_state(dag) -> snapshot dict (the BEFORE state of one mesh).
  * apply_after(spec)       -> write one mesh's NEW normals + restore soft edges
                               (the forward / redo direction).
  * restore_mesh_state(snap)-> re-apply a BEFORE snapshot (the undo direction).

Both the UI (GS_Normal_Tools_UI) and the plugin (plug-ins/gsNormalApiUndo)
import THIS module, so there is exactly one implementation of the read/write
math and one definition of the snapshot/spec shapes.

Everything here is pure maya.api (never maya.cmds): the restore/apply paths run
inside the command's doIt/undoIt/redoIt, and issuing a cmds.* command from there
would tunnel a second entry onto the undo stack mid-(un)do, corrupting it and
risking a crash. So lock state uses lock/unlockFaceVertexNormals and edge
softness uses setEdgeSmoothing/cleanupEdgeSmoothing, all on MFnMesh.

Data shapes
-----------
snapshot (BEFORE), from capture_mesh_state:
    {name, normals(flat [x,y,z,...]), face_ids(MIntArray), vert_ids(MIntArray),
     locked(list of (faceId,vertId)), soft(list of edge ids)}

after spec (NEW), built by the UI:
    {name, normals_flat([x,y,z,...]), face_ids(MIntArray), vert_ids(MIntArray),
     soft(list of edge ids to re-soften)}
"""

import maya.api.OpenMaya as om


# ---------------------------------------------------------------------------
#  Snapshot capture
# ---------------------------------------------------------------------------

def capture_mesh_state(dag):
    """Snapshot everything needed to exactly restore one mesh's normals.

    The normal VALUES come from the mesh-level normal table (mesh.getNormals)
    indexed by getFaceNormalIds(f)[i] - the actual stored normals, always 1:1
    with face-vertices. We deliberately do NOT use MItMeshPolygon.getNormals():
    with soft edges Maya shares one normal across several vertex-faces and that
    iterator can return fewer entries than the face has vertices, silently
    misaligning a positional zip (it restored a wrong/"blank" state).

    A face-vertex's lock flag is read with isNormalLocked(normalId) - the 2022
    Python API takes a single normal id (there is no isNormalLocked(face,vert)
    overload, and getFaceVertexNormalIndex is not exposed).
    """
    mesh = om.MFnMesh(dag)
    name = dag.fullPathName()
    mesh_normals = mesh.getNormals(om.MSpace.kObject)

    face_ids = om.MIntArray()
    vert_ids = om.MIntArray()
    flat = []
    locked = []

    it = om.MItMeshPolygon(dag)
    while not it.isDone():
        f = it.index()
        verts = it.getVertices()
        normal_ids = mesh.getFaceNormalIds(f)
        for i in range(len(verts)):
            v = verts[i]
            nid = normal_ids[i]
            n = mesh_normals[nid]
            face_ids.append(f)
            vert_ids.append(v)
            flat.append(n.x)
            flat.append(n.y)
            flat.append(n.z)
            if mesh.isNormalLocked(nid):
                locked.append((f, v))
        it.next()

    soft = []
    edge_it = om.MItMeshEdge(dag)
    while not edge_it.isDone():
        if edge_it.isSmooth:
            soft.append(edge_it.index())
        edge_it.next()

    return {
        "name": name,
        "normals": flat,
        "face_ids": face_ids,
        "vert_ids": vert_ids,
        "locked": locked,
        "soft": soft,
    }


# ---------------------------------------------------------------------------
#  Apply / restore primitives
# ---------------------------------------------------------------------------

def _resolve_dag(name):
    """Re-resolve a dag path by name (names survive across undo, objects move)."""
    sel = om.MSelectionList()
    sel.add(name)
    return sel.getDagPath(0)


def _write_normals(dag, normals_flat, face_ids, vert_ids):
    """Write a flat (x,y,z...) normal list onto the given face-vertices.

    setFaceVertexNormals LOCKS every face-vertex it writes (they become user
    normals). Callers fix up lock state afterwards as needed.
    """
    mesh = om.MFnMesh(dag)
    varr = om.MVectorArray()
    for i in range(0, len(normals_flat), 3):
        varr.append(om.MVector(normals_flat[i],
                               normals_flat[i + 1],
                               normals_flat[i + 2]))
    mesh.setFaceVertexNormals(varr, face_ids, vert_ids, om.MSpace.kObject)
    mesh.updateSurface()


def _soften(dag, soft_ids):
    """Re-soften exactly the given (previously-soft) edges, leaving hard ones.

    setFaceVertexNormals hardens the edges around any normal it writes, so we
    re-soften the edges that were soft before. Hard edges are never touched - we
    only set the listed edges smooth, then cleanup once. No-op when empty.
    """
    if not soft_ids:
        return
    mesh = om.MFnMesh(dag)
    for e in soft_ids:
        mesh.setEdgeSmoothing(e, True)
    mesh.cleanupEdgeSmoothing()
    mesh.updateSurface()


def _restore_locks(dag, locked_pairs, all_face_ids, all_vert_ids):
    """Restore lock state by UNLOCKING only what was unlocked before.

    Key fact: an UNLOCKED face-vertex normal has no stored value - Maya
    recomputes it on the fly as the average of adjacent face normals. A LOCKED
    ("user") normal stores an explicit value.

    _write_normals wrote our captured values AND locked everything it touched. To
    reproduce the original we:
      * leave the originally-LOCKED face-vertices locked (they keep the exact
        restored value - correct, they were user normals); and
      * UNLOCK the originally-unlocked ones, so Maya drops our written value and
        recomputes the natural average - their true original look.

    Unlocking ALL then re-locking the locked set would re-lock them at the
    RECOMPUTED average, losing the user value (the wrong/"blank" undo). So we
    unlock strictly the complement of locked_pairs.
    """
    mesh = om.MFnMesh(dag)
    locked_set = set(locked_pairs)

    uf = om.MIntArray()
    uv = om.MIntArray()
    for i in range(len(all_face_ids)):
        f = all_face_ids[i]
        v = all_vert_ids[i]
        if (f, v) not in locked_set:
            uf.append(f)
            uv.append(v)

    if len(uf):
        mesh.unlockFaceVertexNormals(uf, uv)


# ---------------------------------------------------------------------------
#  Public directions
# ---------------------------------------------------------------------------

def apply_after(spec):
    """Forward / redo: write one mesh's NEW normals and restore its soft edges.

    Align/Average intend the written normals to become locked user normals (the
    original tool's behaviour), so we leave them locked here - only the soft
    edges that were soft before are re-softened.
    """
    dag = _resolve_dag(spec["name"])
    _write_normals(dag, spec["normals_flat"], spec["face_ids"], spec["vert_ids"])
    _soften(dag, spec["soft"])


def restore_mesh_state(snapshot):
    """Undo: re-apply a BEFORE snapshot from capture_mesh_state, exactly."""
    dag = _resolve_dag(snapshot["name"])
    _write_normals(dag, snapshot["normals"],
                   snapshot["face_ids"], snapshot["vert_ids"])
    _restore_locks(dag, snapshot["locked"],
                   snapshot["face_ids"], snapshot["vert_ids"])
    _soften(dag, snapshot["soft"])


# ---------------------------------------------------------------------------
#  Job staging (one shared slot)
# ---------------------------------------------------------------------------
#
# cmds.gsNormalApiApply() builds a fresh command instance whose doIt cannot
# receive Python objects through command args. The UI stages the (before, after)
# job HERE - in this one shared module both the UI and the plugin import - and the
# command's doIt consumes it. Keeping the slot in core (rather than on the command
# class, which lives in the separately-loaded plugin) means there is exactly one
# slot instance, with no sys.modules lookup. Only ever one job is in flight: the
# UI stages then immediately runs the command synchronously.

_staged_job = [None]  # list-of-one so module-level mutation is simple


def stage_job(before, after):
    """Stage the (before, after) job the next gsNormalApiApply will consume."""
    _staged_job[0] = (before, after)


def take_job():
    """Pop and return the staged (before, after) job, or None if nothing staged."""
    job = _staged_job[0]
    _staged_job[0] = None
    return job
