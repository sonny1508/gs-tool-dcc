# -*- coding: utf-8 -*-
"""UV Shell Scaler - scale every selected UV shell about its own centre.

Select meshes (or groups), faces, edges, vertices or UVs. Every UV shell they
touch is scaled about the centre of its own bounding box, so shells grow or
shrink in place instead of spreading out around one shared pivot.

Uniform scales both axes by one factor. With Uniform off, X (U) and Y (V) are
scaled independently. A negative factor mirrors each shell in place.

Works on each mesh's current UV set; the selection is left untouched and the
whole operation is a single undo step.
maya.cmds + maya.api.OpenMaya only, no pymel.
"""

from collections import defaultdict, namedtuple

import maya.api.OpenMaya as om
import maya.cmds as cmds

TITLE = "UV Shell Scaler"
WINDOW_ID = "gsUvShellScalerWindow"
UNDO_CHUNK = "gsUvShellScaler"
OPTION_PREFIX = "gsUvShellScaler_"

MIN_SCALE = 1e-6        # anything smaller collapses the shell to a point

LABEL_WIDTH = 80
FIELD_WIDTH = 110

Shell = namedtuple("Shell", "mesh uv_set components pivot_u pivot_v")


# --------------------------------------------------------------------------
# finding shells
# --------------------------------------------------------------------------

def _selected_uv_ids():
    """{shape uuid: (MDagPath, set of UV ids)} for the current selection.

    Components convert to the UVs they own; whole objects, groups included,
    contribute every UV. Keyed by shape so instances of one shape - or a mesh
    picked both as an object and as components - are only scaled once.
    """
    selection = cmds.ls(selection=True, long=True)
    components = [item for item in selection if "." in item]
    objects = [item for item in selection if "." not in item]
    # ls() with an empty list returns every mesh in the scene - guard it.
    meshes = cmds.ls(objects, dag=True, type="mesh", noIntermediate=True, long=True) if objects else []

    targets = components + meshes
    if not targets:
        return {}

    selection_list = om.MSelectionList()
    for uv in cmds.polyListComponentConversion(targets, toUV=True) or []:
        selection_list.add(uv)

    found = {}
    for index in range(selection_list.length()):
        dag, component = selection_list.getComponent(index)
        if not dag.hasFn(om.MFn.kMesh):
            dag.extendToShape()
        key = om.MFnDependencyNode(dag.node()).uuid().asString()
        _, uv_ids = found.setdefault(key, (dag, set()))
        uv_ids.update(om.MFnSingleIndexedComponent(component).getElements())
    return found


def _components(mesh_path, uv_ids):
    """UV component strings for sorted ids, consecutive runs collapsed to ranges."""
    components = []
    start = previous = uv_ids[0]
    for uv_id in uv_ids[1:]:
        if uv_id != previous + 1:
            components.append("{}.map[{}:{}]".format(mesh_path, start, previous))
            start = uv_id
        previous = uv_id
    components.append("{}.map[{}:{}]".format(mesh_path, start, previous))
    return components


def collect_shells():
    """Every UV shell the selection touches, with its bounding-box centre."""
    shells = []
    for dag, selected_ids in _selected_uv_ids().values():
        fn = om.MFnMesh(dag)
        uv_set = fn.currentUVSetName()
        u_values, v_values = (list(values) for values in fn.getUVs(uv_set))
        _, shell_ids = fn.getUvShellsIds(uv_set)
        shell_ids = list(shell_ids)

        wanted = {shell_ids[uv_id] for uv_id in selected_ids}
        members = defaultdict(list)
        for uv_id, shell_id in enumerate(shell_ids):
            if shell_id in wanted:
                members[shell_id].append(uv_id)

        mesh_path = dag.fullPathName()
        for uv_ids in members.values():
            us = [u_values[uv_id] for uv_id in uv_ids]
            vs = [v_values[uv_id] for uv_id in uv_ids]
            shells.append(Shell(
                mesh=mesh_path,
                uv_set=uv_set,
                components=_components(mesh_path, uv_ids),
                pivot_u=(min(us) + max(us)) * 0.5,
                pivot_v=(min(vs) + max(vs)) * 0.5,
            ))
    return shells


# --------------------------------------------------------------------------
# scaling
# --------------------------------------------------------------------------

def scale_shells(shells, scale_u, scale_v):
    """Scale each shell about its own pivot. One undo chunk for the lot.

    polyEditUV rather than MFnMesh.setUVs: the om2 write is not undoable.
    """
    cmds.undoInfo(openChunk=True, chunkName=UNDO_CHUNK)
    try:
        for shell in shells:
            cmds.polyEditUV(
                shell.components,
                pivotU=shell.pivot_u,
                pivotV=shell.pivot_v,
                scaleU=scale_u,
                scaleV=scale_v,
                uvSetName=shell.uv_set,
            )
    finally:
        cmds.undoInfo(closeChunk=True)


def scale_selected_shells(scale_u, scale_v):
    """Scale every shell the selection touches. Returns the number scaled."""
    if abs(scale_u) < MIN_SCALE or abs(scale_v) < MIN_SCALE:
        cmds.warning("[{}] A scale of 0 collapses the shells - use a non-zero value.".format(TITLE))
        return 0
    if scale_u == 1.0 and scale_v == 1.0:
        cmds.warning("[{}] Scale is 1 on both axes - nothing to do.".format(TITLE))
        return 0

    shells = collect_shells()
    if not shells:
        cmds.warning("[{}] Select meshes or polygon components with UVs first.".format(TITLE))
        return 0

    scale_shells(shells, scale_u, scale_v)

    mesh_count = len({shell.mesh for shell in shells})
    cmds.inViewMessage(
        assistMessage="Scaled {} UV shell(s) on {} mesh(es)".format(len(shells), mesh_count),
        position="midCenter",
        fade=True,
    )
    return len(shells)


# --------------------------------------------------------------------------
# UI
# --------------------------------------------------------------------------

def _load_option(name, default):
    key = OPTION_PREFIX + name
    return cmds.optionVar(query=key) if cmds.optionVar(exists=key) else default


def _save_option(name, value):
    key = OPTION_PREFIX + name
    if isinstance(value, float):
        cmds.optionVar(floatValue=(key, value))
    else:
        cmds.optionVar(intValue=(key, int(value)))


class ShellScalerWindow(object):

    def __init__(self):
        if cmds.window(WINDOW_ID, exists=True):
            cmds.deleteUI(WINDOW_ID)
        if cmds.windowPref(WINDOW_ID, exists=True):
            cmds.windowPref(WINDOW_ID, remove=True)

        cmds.window(
            WINDOW_ID,
            title=TITLE,
            sizeable=False,
            resizeToFitChildren=True,
            minimizeButton=False,
            maximizeButton=False,
        )
        cmds.columnLayout(adjustableColumn=True, rowSpacing=6, columnAttach=("both", 10))
        cmds.separator(height=4, style="none")

        columns = dict(columnWidth2=(LABEL_WIDTH, FIELD_WIDTH), columnAlign=(1, "right"))
        self.uniform_box = cmds.checkBoxGrp(
            label="Uniform",
            numberOfCheckBoxes=1,
            value1=bool(_load_option("uniform", True)),
            changeCommand=self._on_uniform_changed,
            **columns
        )
        self.u_field = cmds.floatFieldGrp(
            label="Scale X (U)",
            numberOfFields=1,
            precision=3,
            value1=_load_option("scaleU", 1.0),
            changeCommand=self._on_u_changed,
            **columns
        )
        self.v_field = cmds.floatFieldGrp(
            label="Scale Y (V)",
            numberOfFields=1,
            precision=3,
            value1=_load_option("scaleV", 1.0),
            **columns
        )

        cmds.button(label="Scale Each Shell", height=30, command=self._on_scale)
        cmds.separator(height=4, style="none")

        self._sync()
        cmds.showWindow(WINDOW_ID)

    def _uniform(self):
        return cmds.checkBoxGrp(self.uniform_box, query=True, value1=True)

    def _scale(self):
        """(scale_u, scale_v) as the user means it - Uniform ignores the Y field."""
        scale_u = cmds.floatFieldGrp(self.u_field, query=True, value1=True)
        if self._uniform():
            return scale_u, scale_u
        return scale_u, cmds.floatFieldGrp(self.v_field, query=True, value1=True)

    def _sync(self):
        """Uniform mirrors X into Y and locks the Y field."""
        uniform = self._uniform()
        if uniform:
            scale_u, _ = self._scale()
            cmds.floatFieldGrp(self.v_field, edit=True, value1=scale_u)
        cmds.floatFieldGrp(self.v_field, edit=True, enable=not uniform)

    def _save(self):
        scale_u, scale_v = self._scale()
        _save_option("uniform", self._uniform())
        _save_option("scaleU", scale_u)
        _save_option("scaleV", scale_v)

    def _on_uniform_changed(self, *_):
        self._sync()
        self._save()

    def _on_u_changed(self, *_):
        self._sync()

    def _on_scale(self, *_):
        self._save()
        scale_selected_shells(*self._scale())


def show():
    return ShellScalerWindow()


if __name__ == "__main__":
    show()
