# -*- coding: utf-8 -*-
"""
GS Normal Tools - undoable API write command (Maya 2022+, Python 3).

A thin MPxCommand, gsNormalApiApply, that puts GS Normal Tools' fast
MFnMesh.setFaceVertexNormals writes (Align Normals, Average From Edge) onto
Maya's native undo stack. All the actual read/write/restore math lives in the
importable gs_normal_core module, which both this plugin and the UI share - so
there is one source of truth and no sys.modules handoff tricks.

Why a command at all
--------------------
setFaceVertexNormals is a direct DG edit Maya does NOT record on the undo stack.
Wrapping it in a command makes the operation a single, exact, fully-undoable
entry: each invocation captures the touched meshes' BEFORE state and carries it,
together with the NEW normals, ON THE COMMAND INSTANCE. Maya keeps every command
instance alive on the undo stack, so aligning A, then B, then A again leaves
three independent entries - undo walks them in reverse, each restoring its own
mesh. There is no shared/global snapshot to clobber.

How data reaches the command
-----------------------------
cmds.gsNormalApiApply() builds a fresh instance via creator(), and command
arguments can't carry MVectorArrays. So the UI STAGES the (before, after) job via
core.stage_job(...) immediately before calling cmds.gsNormalApiApply(); doIt()
consumes it with core.take_job() onto self. The slot lives in gs_normal_core -
the one module both sides import - so there's exactly one slot, no token map and
no shared-module lookup.

Deployment
----------
Deployed to ~/Documents/maya/plug-ins (a Maya DEFAULT TRUSTED location, also on
MAYA_PLUG_IN_PATH via Maya.env) and loaded BY NAME so there is no "untrusted
location" prompt. The UI puts the 02_Normals folder on sys.path before loading
this plugin, so the top-level `import gs_normal_core` below resolves.
"""

import maya.api.OpenMaya as om

import gs_normal_core as core

maya_useNewAPI = True

COMMAND_NAME = "gsNormalApiApply"


class GSNormalApiApply(om.MPxCommand):
    """Undoable wrapper around gs_normal_core's normal write.

    A job is a tuple (before, after):
        before : list of snapshots (core.capture_mesh_state) - one per mesh.
        after  : list of after-specs - the NEW normals + soft edges per mesh.
    """

    def __init__(self):
        om.MPxCommand.__init__(self)
        self._before = None
        self._after = None

    @staticmethod
    def creator():
        return GSNormalApiApply()

    def doIt(self, _args):
        job = core.take_job()
        if job is None:
            raise RuntimeError(
                "gsNormalApiApply called with nothing staged - call "
                "core.stage_job(before, after) immediately before it.")
        self._before, self._after = job
        self.redoIt()

    def redoIt(self):
        for spec in self._after:
            core.apply_after(spec)

    def undoIt(self):
        for snapshot in self._before:
            core.restore_mesh_state(snapshot)

    def isUndoable(self):
        return True


# ---------------------------------------------------------------------------
#  Maya plugin entry points
# ---------------------------------------------------------------------------

def initializePlugin(plugin):
    fn = om.MFnPlugin(plugin, "Glenda Studio", "1.0", "Any")
    try:
        fn.registerCommand(COMMAND_NAME, GSNormalApiApply.creator)
    except Exception:
        # Already registered (e.g. reloaded): deregister then re-add so edits to
        # the command class take effect.
        fn.deregisterCommand(COMMAND_NAME)
        fn.registerCommand(COMMAND_NAME, GSNormalApiApply.creator)


def uninitializePlugin(plugin):
    fn = om.MFnPlugin(plugin)
    fn.deregisterCommand(COMMAND_NAME)
