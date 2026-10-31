"""Animation Check: moving the parts a CM car animates, to see that they move
right. For now the doors.

Each door turns on two anchors (names.DOORS), the exterior and the interior
one, both pivoted at the hinge. Their rotation isn't applied and differs from
car to car, so a door is turned about world Z through its own origin, starting
from whatever rotation it has: left doors one way, right doors the other.

The rotation each anchor had before the doors opened is kept on the scene
(vehicle.GS_CM_ClosedDoor rows), so every angle is turned from there, and
closing writes back exactly the values it had: dragging the slider never
drifts. Only rotation is written; location and scale are left alone.
"""
from __future__ import annotations

from mathutils import Euler, Quaternion, Vector

from . import names


def keep_closed(closed, objects):
    """Note in ``closed`` (GS_CM_ClosedDoor rows) the door anchors among
    ``objects`` and their rotation, before the doors open."""
    for obj in objects:
        side = names.door_side(obj.name)
        if side is not None:
            item = closed.add()
            item.door = obj
            item.side = side
            item.mode = obj.rotation_mode
            item.rotation = _rotation(obj)


def turn_doors(closed, angle):
    """Turn every door in ``closed`` ``angle`` (radians) open from its closed
    rotation. At 0, write the closed rotation back and empty ``closed``."""
    for item in closed:
        obj = item.door
        if obj is None:         # deleted since
            continue
        rotation = _turned(obj, item, angle * item.side) if angle else item.rotation
        _set_rotation(obj, item.mode, rotation)
    if not angle:
        closed.clear()


def _turned(obj, closed, angle):
    """``closed`` (a GS_CM_ClosedDoor) turned ``angle`` about world Z, as obj's rotation values."""
    # World Z, in the space obj's own rotation is in: its parent's, after parenting.
    frame = (obj.parent.matrix_world @ obj.matrix_parent_inverse).to_quaternion() \
        if obj.parent is not None else Quaternion()
    axis = frame.inverted() @ Vector((0.0, 0.0, 1.0))
    turned = Quaternion(axis, angle) @ _quaternion(closed.mode, closed.rotation)
    if closed.mode == 'QUATERNION':
        return tuple(turned)
    if closed.mode == 'AXIS_ANGLE':
        axis, amount = turned.to_axis_angle()
        return (amount,) + tuple(axis)
    # Euler: the angles nearest the closed ones, so the values don't jump by 360°.
    return tuple(turned.to_euler(closed.mode, Euler(closed.rotation[:3], closed.mode))) + (0.0,)


# Rotation values as kept in GS_CM_ClosedDoor.rotation: Euler x, y, z and 0,
# a quaternion w, x, y, z, or axis-angle angle, x, y, z, by rotation mode.
def _rotation(obj):
    if obj.rotation_mode == 'QUATERNION':
        return tuple(obj.rotation_quaternion)
    if obj.rotation_mode == 'AXIS_ANGLE':
        return tuple(obj.rotation_axis_angle)
    return tuple(obj.rotation_euler) + (0.0,)


def _set_rotation(obj, mode, rotation):
    if obj.rotation_mode != mode:
        obj.rotation_mode = mode
    if mode == 'QUATERNION':
        obj.rotation_quaternion = rotation
    elif mode == 'AXIS_ANGLE':
        obj.rotation_axis_angle = rotation
    else:
        obj.rotation_euler = rotation[:3]


def _quaternion(mode, rotation):
    if mode == 'QUATERNION':
        return Quaternion(rotation)
    if mode == 'AXIS_ANGLE':
        return Quaternion(rotation[1:], rotation[0])
    return Euler(rotation[:3], mode).to_quaternion()
