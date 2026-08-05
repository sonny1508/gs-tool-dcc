"""
gs_property_transfer.core - no UI, all the actual work.

One source object is picked and stored per scene; every transfer section then
pushes some property from that source onto the current selection (the targets).

The source is held by a message connection on a small network node rather than
by name, so it survives renaming and reparenting and breaks cleanly - back to
"no source picked" - if the object is deleted.

Pivot matching
--------------
The selected objects' pivots are moved onto the source object. A pivot is
treated as a frame - a position, an orientation and a scale - and each component
is taken from the source or left as the target's own. The target's geometry
never moves in world space, whichever components are matched.

Translate on its own is cheap and non-destructive: `xform -piv -preserve` writes
rotatePivot / scalePivot and compensates through the pivot translates, so the
target's channels and its geometry are untouched. This always works.

Rotate and scale cannot work that way. A pivot's orientation *is* the
object's local axes, so changing it means re-authoring the object's local space:
the target is baked into the new frame (parent under a temporary transform of
that frame -> makeIdentity -> reparent). Afterwards the target's
translate/rotate/scale channels describe the new frame and rotatePivot is zero.

That bake rests on makeIdentity, which *warns instead of raising* when it will
not run - construction history, locked or connected transform channels, an
instanced shape. Left unchecked that reads as a successful no-op, so the bake
is pre-flighted (is there geometry to bake into?) and verified afterwards (did
the frame actually take?), and turns into a real error when it did nothing.

Freeze
------
`freeze=True` runs makeIdentity on the target *before* the match, so
translate/rotate/scale read 0/0/1 and any old pivot offsets are gone; the
wanted frame is measured first, then applied on top. Translate-only matches
therefore end at 0/0/1 with the pivot sitting on the source. When rotate or
scale is also matched the frame has to live in the channels, so those end up
holding the matched frame rather than 0/0/1 - a rotated frame is a rotation,
and a fully frozen transform has none.
"""

import maya.cmds as cmds
import maya.api.OpenMaya as om

SETTINGS_NODE = "gs_propertyTransferToolSettings"
SOURCE_ATTR = "sourceObject"


# ---------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------
def short_name(node):
    """Leaf name of a dag path, for messages and UI labels."""
    return node.split("|")[-1] if node else ""


def _long_name(node):
    found = cmds.ls(node, long=True) or []
    return found[0] if found else node


# ---------------------------------------------------------------------------
# picked source object - stored per scene on a network node
# ---------------------------------------------------------------------------
def settings_node(create=True):
    """The scene's settings node, created on demand."""
    node = SETTINGS_NODE if cmds.objExists(SETTINGS_NODE) else None
    if node is None:
        if not create:
            return None
        node = cmds.createNode("network", name=SETTINGS_NODE, skipSelect=True)
    if not cmds.attributeQuery(SOURCE_ATTR, node=node, exists=True):
        cmds.addAttr(node, longName=SOURCE_ATTR, attributeType="message")
    return node


def set_source_object(node=None):
    """Store `node` (or the first selected transform) as the source object."""
    if node is None:
        selected = cmds.ls(selection=True, transforms=True, long=True)
        if not selected:
            raise RuntimeError("Select a transform to use as the source object.")
        node = selected[0]
    node = _long_name(node)
    settings = settings_node()
    cmds.connectAttr(node + ".message", settings + "." + SOURCE_ATTR, force=True)
    return node


def get_source_object():
    """The picked source object as a full dag path, or None."""
    settings = settings_node(create=False)
    if not settings or not cmds.attributeQuery(SOURCE_ATTR, node=settings, exists=True):
        return None
    connected = cmds.listConnections(settings + "." + SOURCE_ATTR,
                                     source=True, destination=False) or []
    return _long_name(connected[0]) if connected else None


def clear_source_object():
    """Forget the picked source object."""
    settings = settings_node(create=False)
    if not settings or not cmds.attributeQuery(SOURCE_ATTR, node=settings, exists=True):
        return None
    plug = settings + "." + SOURCE_ATTR
    for src in cmds.listConnections(plug, source=True, destination=False, plugs=True) or []:
        cmds.disconnectAttr(src, plug)
    return None


def resolve_source(source=None):
    """The source to operate on, with a readable error if there isn't one."""
    source = source or get_source_object()
    if not source:
        raise RuntimeError("Pick a source object first.")
    if not cmds.objExists(source):
        raise RuntimeError("The source object no longer exists - pick a new one.")
    return source


def resolve_targets(targets=None, source=None):
    """Selected transforms to receive the transfer, minus the source itself."""
    if targets is None:
        targets = cmds.ls(selection=True, transforms=True, long=True) or []
    else:
        targets = [_long_name(t) for t in targets]

    source = _long_name(source) if source else None
    targets = [t for t in targets if t != source]
    if not targets:
        raise RuntimeError("Select one or more target objects "
                           "(the source itself is ignored).")
    return targets


# ---------------------------------------------------------------------------
# pivot transfer
# ---------------------------------------------------------------------------
def pivot_position(node):
    """World-space rotate pivot of `node` - where its manipulator sits."""
    return cmds.xform(node, query=True, worldSpace=True, rotatePivot=True)


def freeze_transforms(node):
    """Freeze translate / rotate / scale into the shape below `node`."""
    cmds.makeIdentity(node, apply=True, translate=True, rotate=True, scale=True,
                      normal=0, preserveNormals=True)


def _frame_matrix(source, target, translate, rotate, scale):
    """World matrix of the frame `target` should end up with.

    Each component comes from the source when its flag is on, and from the
    target's own current frame when it is off.
    """
    source_xform = om.MTransformationMatrix(
        om.MMatrix(cmds.xform(source, query=True, worldSpace=True, matrix=True)))
    target_xform = om.MTransformationMatrix(
        om.MMatrix(cmds.xform(target, query=True, worldSpace=True, matrix=True)))

    origin = pivot_position(source if translate else target)
    rotation = (source_xform if rotate else target_xform).rotation()
    scaling = (source_xform if scale else target_xform).scale(om.MSpace.kWorld)

    frame = om.MTransformationMatrix()
    frame.setScale(scaling, om.MSpace.kWorld)
    frame.setRotation(rotation)
    frame.setTranslation(om.MVector(origin), om.MSpace.kWorld)
    return frame.asMatrix()


def _bakeable_geometry(node):
    """Shapes under `node` that makeIdentity can actually bake a transform into.

    A locator or an empty group has none: freezing it would move the object
    instead of re-framing it, so the bake has to refuse rather than damage it.
    """
    shapes = cmds.listRelatives(node, allDescendents=True, shapes=True,
                                noIntermediate=True, fullPath=True) or []
    return [s for s in shapes
            if cmds.nodeType(s) in ("mesh", "nurbsSurface", "nurbsCurve", "subdiv")]


def _blockers(node):
    """Readable reasons makeIdentity is likely to refuse `node`."""
    reasons = []
    if cmds.listHistory(node, pruneDagObjects=True) or []:
        reasons.append("construction history")
    locked = [a for a in ("translate", "rotate", "scale")
              if cmds.getAttr(node + "." + a, lock=True)
              or cmds.listConnections(node + "." + a, source=True,
                                      destination=False, plugs=True)]
    if locked:
        reasons.append("locked or connected " + "/".join(locked))
    for shape in _bakeable_geometry(node):
        if len(cmds.listRelatives(shape, allParents=True, fullPath=True) or []) > 1:
            reasons.append("instanced shape")
            break
    return reasons


def _matches(left, right, tolerance=1e-4):
    return all(abs(a - b) <= tolerance for a, b in zip(left, right))


def _bake_into_frame(node, matrix):
    """Give `node` the local space described by world `matrix`, geometry unmoved.

    Parenting under a temporary transform of that frame and freezing there bakes
    the difference into the shape; reparenting back leaves the frame in the
    node's own channels. The node is always pulled back out of the temporary
    transform, so a failed makeIdentity cannot leave it stranded (or deleted).

    Raises if the frame did not take - makeIdentity only warns when it declines,
    which would otherwise look like a successful no-op.
    """
    if not _bakeable_geometry(node):
        raise RuntimeError("no geometry to bake the new axes into (a locator or "
                           "empty group has none) - use Translate only")

    original_parent = cmds.listRelatives(node, parent=True, fullPath=True)
    frame = cmds.createNode("transform", name="gs_ptFrame#", skipSelect=True)
    cmds.xform(frame, worldSpace=True, matrix=list(matrix))

    node = _long_name(cmds.parent(node, frame)[0])
    try:
        freeze_transforms(node)
    finally:
        if original_parent:
            node = _long_name(cmds.parent(node, original_parent[0])[0])
        else:
            node = _long_name(cmds.parent(node, world=True)[0])
        cmds.delete(frame)

    result = cmds.xform(node, query=True, worldSpace=True, matrix=True)
    if not _matches(result, list(matrix)):
        reasons = _blockers(node)
        raise RuntimeError(
            "Freeze Transformations declined it{} - delete history / unlock the "
            "channels, or use Translate only".format(
                " (" + ", ".join(reasons) + ")" if reasons else ""))
    return node


def match_pivots(source=None, targets=None, translate=True, rotate=True,
                 scale=False, freeze=False):
    """Move the targets' pivots onto the source object.

    source    -- transform to match to; defaults to the picked source
    targets   -- transforms whose pivots move; defaults to the current selection
    translate -- put the pivot on the source object's pivot
    rotate    -- align the local axes to the source object's
    scale     -- take the source object's scale
    freeze    -- zero the target's transforms before applying the frame

    Returns (moved, failed): `moved` holds the targets' paths after the change,
    `failed` a list of (node, message) pairs, so one bad object in a big
    selection does not abort the rest.
    """
    source = resolve_source(source)
    targets = resolve_targets(targets, source=source)
    if not (translate or rotate or scale or freeze):
        raise RuntimeError("Nothing to do - tick Translate, Rotate, "
                           "Scale or Freeze.")

    bake = bool(rotate or scale)
    moved, failed = [], []
    cmds.undoInfo(openChunk=True, chunkName="gs_propertyTransferPivot")
    try:
        for target in targets:
            try:
                # Measure first: freezing sends the target's own pivot to the
                # origin, which would poison the components it keeps.
                if bake:
                    wanted = _frame_matrix(source, target, translate, rotate, scale)
                elif translate:
                    wanted = pivot_position(source)

                if freeze:
                    freeze_transforms(target)

                if bake:
                    target = _bake_into_frame(target, wanted)
                elif translate:
                    cmds.xform(target, worldSpace=True, preserve=True, pivots=wanted)
                moved.append(target)
            except Exception as exc:
                failed.append((target, str(exc)))
    finally:
        cmds.undoInfo(closeChunk=True)

    return moved, failed
