"""Edge Length Tool.

Reads the world-space length of an edge and sets the selected edges to a given length,
by moving the first vertex (Left), the second vertex (Right) or both ends (Center) along
the edge.

Pure maya.cmds / om2: no PyMEL, so it runs on Maya 2022 and 2026 alike.
"""
import math

import maya.api.OpenMaya as om2
from maya import cmds

WINDOW = "setEdgeWindow"
LENGTH_FIELD = "setEdgeLength_value"
DIRECTION_COLLECTION = "setEdgeLength_direction"
DIRECTION_BUTTONS = {
    "setEdgeLength_left": "left",
    "setEdgeLength_center": "center",
    "setEdgeLength_right": "right",
}
STEP = 0.001


# --------------------------------------------------------------------------- geometry

def _selected_edges():
    """Flattened list of the selected mesh edges."""
    return cmds.filterExpand(selectionMask=32, expand=True) or []


def _edge_vertices(edge):
    """The two vertices of an edge, in index order."""
    return cmds.ls(cmds.polyListComponentConversion(edge, toVertex=True), flatten=True)


def _edge_points(edge):
    v1, v2 = _edge_vertices(edge)
    return v1, v2, cmds.pointPosition(v1, world=True), cmds.pointPosition(v2, world=True)


def _distance(p1, p2):
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(p1, p2)))


def getLength(edge):
    """World-space edge length, rounded to the 3 decimals the field shows."""
    _, _, p1, p2 = _edge_points(edge)
    return round(_distance(p1, p2), 3)


def _move(vertex, unit, amount):
    cmds.move(unit[0] * amount, unit[1] * amount, unit[2] * amount,
              vertex, relative=True, worldSpace=True)


def setEdgeLength(target, direction="center"):
    """Set every selected edge to ``target`` length.

    left   - move the first vertex, the second stays put
    right  - move the second vertex, the first stays put
    center - move both ends by half
    """
    edges = _selected_edges()
    if not edges:
        om2.MGlobal.displayError("Select one or more edges.")
        return

    cmds.undoInfo(openChunk=True, chunkName="setEdgeLength")
    try:
        for edge in edges:
            # Re-read per edge: edges sharing a vertex see the previous move.
            v1, v2, p1, p2 = _edge_points(edge)
            current = _distance(p1, p2)
            if current < 1e-9:
                continue  # zero-length edge has no direction
            unit = [(a - b) / current for a, b in zip(p1, p2)]  # points from v2 to v1
            delta = target - current

            if direction == "left":
                _move(v1, unit, delta)
            elif direction == "right":
                _move(v2, unit, -delta)
            else:
                _move(v1, unit, delta * 0.5)
                _move(v2, unit, -delta * 0.5)
    finally:
        cmds.undoInfo(closeChunk=True)


# --------------------------------------------------------------------------- UI callbacks

def lengthToField():
    edges = _selected_edges()
    if len(edges) != 1:
        om2.MGlobal.displayError("Select one edge.")
        return
    cmds.floatField(LENGTH_FIELD, edit=True, value=getLength(edges[0]))


def setLength():
    value = cmds.floatField(LENGTH_FIELD, query=True, value=True)
    selected = cmds.radioCollection(DIRECTION_COLLECTION, query=True, select=True)
    setEdgeLength(value, direction=DIRECTION_BUTTONS.get(selected, "center"))


def nudgeValue(amount):
    value = cmds.floatField(LENGTH_FIELD, query=True, value=True)
    cmds.floatField(LENGTH_FIELD, edit=True, value=value + amount)


# --------------------------------------------------------------------------- window

def Gui():
    if cmds.window(WINDOW, query=True, exists=True):
        cmds.deleteUI(WINDOW)
    if cmds.windowPref(WINDOW, query=True, exists=True):
        cmds.windowPref(WINDOW, remove=True)

    cmds.window(WINDOW, title="Edge Length Tool", widthHeight=(160, 130),
                minimizeButton=False, maximizeButton=False, resizeToFitChildren=True)

    layout = cmds.columnLayout(adjustableColumn=True)

    cmds.button(label="Get Length", command=lambda *_: lengthToField(), parent=layout)
    cmds.button(label=chr(0x1e), command=lambda *_: nudgeValue(STEP), parent=layout)
    cmds.floatField(LENGTH_FIELD, minValue=-1, maxValue=10000, precision=3, step=STEP,
                    parent=layout)
    cmds.button(label=chr(0x1f), command=lambda *_: nudgeValue(-STEP), parent=layout)

    row = cmds.rowLayout(columnWidth=(80, 80), height=40, numberOfColumns=3,
                         adjustableColumn=2, columnAlign=(1, "right"), parent=layout)
    cmds.radioCollection(DIRECTION_COLLECTION, parent=row)
    cmds.radioButton("setEdgeLength_left", label="Left", parent=row)
    cmds.radioButton("setEdgeLength_center", label="Center", select=True, parent=row)
    cmds.radioButton("setEdgeLength_right", label="Right", parent=row)

    cmds.button(label="Set Length", command=lambda *_: setLength(), parent=layout)

    cmds.showWindow(WINDOW)
