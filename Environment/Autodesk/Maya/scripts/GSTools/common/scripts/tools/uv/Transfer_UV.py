"""
GS - Transfer UV

Transfer UVs (or shape/position) from one source mesh onto one or more target
meshes using Maya's transferAttributes. Maya 2022+ (Python 3), with a Python 2
fallback kept for older hosts.

This is a rewrite of the legacy Transfer_UV.mel. Behaviour changes worth noting:
  * Source / Dist UV-set dropdowns are populated live from the selected meshes
    instead of a hardcoded map1..map4 / UVChannel_* list, so a transfer can no
    longer silently target a UV set that does not exist.
  * The whole operation runs inside a single undo chunk.
  * Construction history is only deleted on the *targets*, never on the source.
  * Per-target failures are collected and reported instead of aborting.

Sample-space values used by transferAttributes:
    0 = World, 4 = UV (component / "ID"), 5 = Topology

Usage:
    from tools.uv import Transfer_UV
    Transfer_UV.UI()
"""

import maya.cmds as cmds
import maya.mel as mel
import logging

logging.basicConfig()
logger = logging.getLogger("gs_transfer_uv")
logger.setLevel(logging.INFO)

SCRIPT_NAME = "GS - Transfer UV"
SCRIPT_VERSION = "2.0"

WINDOW_NAME = "gsTransferUvWindow"
SRC_MENU = "gsTransferUvSourceMenu"
DST_MENU = "gsTransferUvDistMenu"
REF_LABEL = "gsTransferUvRefLabel"

# Module-level source object (was the global $prUV_referenceobject in the MEL).
_reference_object = ""

_GREY = (0.4, 0.4, 0.4)

# sampleSpace values, copied verbatim from the original working MEL tool:
#   prUV_TransferUV($ref, 4) -> "Transfer UV (ID)"
#   prUV_TransferUV($ref, 5) -> "Transfer UV (Topo)"
#   prUV_TransferUV($ref, 0) -> "Project UV"
#   prUV_TransferUV($ref, -1) -> "Transfer Shape" (positions)
# These are what this Maya build accepts, so we do not second-guess them.
SAMPLE_WORLD = 0       # "Project UV"
SAMPLE_COMPONENT = 4   # "Transfer UV (ID)"
SAMPLE_TOPO = 5        # "Transfer UV (Topo)"
TYPE_SHAPE = -1        # "Transfer Shape" - position transfer


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _get_mesh_shape(node):
    """Return the first non-intermediate mesh shape under *node*, or None."""
    if cmds.nodeType(node) == "mesh":
        return node
    shapes = cmds.listRelatives(node, shapes=True, noIntermediate=True,
                                fullPath=True, type="mesh") or []
    return shapes[0] if shapes else None


def _uv_sets(node):
    """UV-set names on *node*'s mesh shape (empty list if not a mesh)."""
    shape = _get_mesh_shape(node)
    if not shape:
        return []
    return cmds.polyUVSet(shape, query=True, allUVSets=True) or []


def _selected_meshes(order=True):
    """Selected transforms/shapes that resolve to a mesh, in selection order."""
    sel = cmds.ls(orderedSelection=True, long=True) if order else \
        cmds.ls(selection=True, long=True)
    return [n for n in sel if _get_mesh_shape(n)]


def _short_name(node):
    """Leaf name of a DAG path (last '|'-separated token) for display."""
    return node.rsplit("|", 1)[-1]


def _refresh_uv_menus(*_):
    """Rebuild both UV-set dropdowns from the current selection + source.

    Preserves the current choice where the name still exists so refreshing does
    not silently move the user's selection.
    """
    names = set()
    for node in _selected_meshes():
        names.update(_uv_sets(node))
    if _reference_object and cmds.objExists(_reference_object):
        names.update(_uv_sets(_reference_object))

    ordered = sorted(names) if names else ["map1"]

    for menu in (SRC_MENU, DST_MENU):
        if not cmds.optionMenu(menu, exists=True):
            continue
        previous = cmds.optionMenu(menu, query=True, value=True)
        for item in cmds.optionMenu(menu, query=True, itemListLong=True) or []:
            cmds.deleteUI(item)
        for name in ordered:
            cmds.menuItem(label=name, parent=menu)
        if previous in ordered:
            cmds.optionMenu(menu, edit=True, value=previous)


def _set_as_source(*_):
    """Store the last selected mesh as the transfer source."""
    global _reference_object
    meshes = _selected_meshes()
    if not meshes:
        cmds.warning("Select the source object first.")
        return
    if len(meshes) > 1:
        cmds.warning("More than one object selected, using the last as source.")
    _reference_object = meshes[-1]
    if cmds.text(REF_LABEL, exists=True):
        cmds.text(REF_LABEL, edit=True, label=_short_name(_reference_object))
    _refresh_uv_menus()


# ---------------------------------------------------------------------------
# Core transfer
# ---------------------------------------------------------------------------
def _transfer(transfer_type):
    """Run a transfer from the stored source onto every selected mesh.

    transfer_type: TYPE_SHAPE for a position transfer, otherwise a sampleSpace
    value (SAMPLE_WORLD / SAMPLE_COMPONENT / SAMPLE_TOPO) for a UV transfer.
    """
    if not _reference_object or not cmds.objExists(_reference_object):
        cmds.error("Source object does not exist. Set a source first.")
        return

    targets = [m for m in _selected_meshes(order=False)
               if m != _reference_object]
    if not targets:
        cmds.error("No target objects selected.")
        return

    src_uv = cmds.optionMenu(SRC_MENU, query=True, value=True)
    dst_uv = cmds.optionMenu(DST_MENU, query=True, value=True)

    # Query the maya default progress bar once, outside the loop.
    main_bar = mel.eval("$tmp = $gMainProgressBar")
    cmds.progressBar(main_bar, edit=True, beginProgress=True,
                     isInterruptable=True, status="UV Transfer...",
                     minValue=0, maxValue=len(targets))

    errors = []
    cmds.undoInfo(openChunk=True, chunkName="GS Transfer UV")
    try:
        for target in targets:
            if cmds.progressBar(main_bar, query=True, isCancelled=True):
                break
            try:
                # Run the exact transferAttributes call the original working
                # MEL tool used, via mel.eval. This guarantees identical
                # behaviour to the legacy tool - the flag names (-sourceUvSet /
                # -targetUvSet) and sampleSpace values are whatever this Maya
                # build accepts, which cmds keyword args did not honour.
                if transfer_type == TYPE_SHAPE:
                    cmd = (
                        'transferAttributes -transferPositions 1 '
                        '-transferNormals 0 -transferUVs 0 -transferColors 0 '
                        '-sampleSpace 3 -searchMethod 3 -flipUVs 0 '
                        '-colorBorders 0 "{src}" "{tgt}";'
                    ).format(src=_reference_object, tgt=target)
                else:
                    cmd = (
                        'transferAttributes -transferPositions 0 '
                        '-transferNormals 0 -transferUVs 1 -transferColors 0 '
                        '-sampleSpace {space} -sourceUvSet "{suv}" '
                        '-targetUvSet "{tuv}" -searchMethod 3 -flipUVs 0 '
                        '-colorBorders 0 "{src}" "{tgt}";'
                    ).format(space=transfer_type, suv=src_uv, tuv=dst_uv,
                             src=_reference_object, tgt=target)
                mel.eval(cmd)
                # Bake the result and clean history on the target only.
                cmds.delete(target, constructionHistory=True)
            except Exception as exc:  # noqa: BLE001 - report, keep going
                errors.append("{0}: {1}".format(target, exc))
                logger.debug(str(exc))
            cmds.progressBar(main_bar, edit=True, step=1)
    finally:
        cmds.progressBar(main_bar, edit=True, endProgress=True)
        cmds.undoInfo(closeChunk=True, chunkName="GS Transfer UV")

    if errors:
        cmds.warning("{0} target(s) failed. See script editor for details."
                     .format(len(errors)))
        for err in errors:
            print(err)


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
def UI():
    """Build and show the Transfer UV window."""
    if cmds.window(WINDOW_NAME, exists=True):
        cmds.deleteUI(WINDOW_NAME, window=True)

    window = cmds.window(WINDOW_NAME,
                         title="{0}  (v{1})".format(SCRIPT_NAME, SCRIPT_VERSION),
                         sizeable=False, resizeToFitChildren=True,
                         widthHeight=(320, 100))

    cmds.columnLayout(rowSpacing=4, adjustableColumn=True)

    ref_text = _reference_object or "(Please select the source object)"
    cmds.text(REF_LABEL, label=ref_text, width=300, font="boldLabelFont",
              wordWrap=True, height=20)

    cmds.button(label="Set as source", width=300, height=25, bgc=_GREY,
                command=_set_as_source)

    cmds.rowLayout(numberOfColumns=2, columnWidth2=(255, 55),
                   columnAttach=[(1, "both", 0), (2, "both", 0)])
    cmds.optionMenu(SRC_MENU, label="Source UV", width=250)
    cmds.button(label="Refresh", width=55, height=20, command=_refresh_uv_menus)
    cmds.setParent("..")

    cmds.optionMenu(DST_MENU, label="Dist UV", width=300)

    cmds.rowLayout(numberOfColumns=2, columnWidth2=(150, 150))
    cmds.button(label="Transfer UV (ID)", width=149, height=25, bgc=_GREY,
                command=lambda *_: _transfer(SAMPLE_COMPONENT),
                annotation="Component/spatial match. Use when source and target "
                           "have DIFFERENT topology. Note: UV shells split at "
                           "seams because connectivity can't be reconstructed.")
    cmds.button(label="Transfer UV (Topo)", width=149, height=25, bgc=_GREY,
                command=lambda *_: _transfer(SAMPLE_TOPO),
                annotation="Exact copy by topology. Use when source and target "
                           "have IDENTICAL topology (duplicate / re-import). "
                           "Shells, seams and overlapping UVs are preserved.")
    cmds.setParent("..")

    cmds.rowLayout(numberOfColumns=2, columnWidth2=(150, 150))
    cmds.button(label="Project UV", width=149, height=25, bgc=_GREY,
                command=lambda *_: _transfer(SAMPLE_WORLD))
    cmds.button(label="Transfer Shape", width=149, height=25, bgc=_GREY,
                command=lambda *_: _transfer(TYPE_SHAPE))
    cmds.setParent("..")

    cmds.separator(height=10, width=320)

    _refresh_uv_menus()
    cmds.showWindow(window)


if __name__ == "__main__":
    UI()
