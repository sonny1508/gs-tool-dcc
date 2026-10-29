-- Bulk mesh access for the MGP27 Kerb Height Checker (kerb_height_checker.py).
--
-- The measuring is Python. These functions move a whole mesh's worth of data
-- across in one call, where pymxs alone would cross into MAXScript once per
-- vertex. kerb_height_checker.py loads this file each time the window opens.
--
-- Each function takes a node and works on its Editable Poly base object: the
-- mesh's own vertices, under any modifiers, since those are what Fix moves.
-- Vertex ids are MAXScript's, counted from 1.

-- World position of every vertex, flat: #(x1, y1, z1, x2, ...), in system units.
fn gsKerbWorldPoints node =
(
    local base = node.baseObject
    local count = polyop.getNumVerts base
    local flat = #()
    if count > 0 do
    (
        -- Without node:, polyop works in object space.
        local tm = node.objectTransform
        local pts = polyop.getVerts base #{1..count}
        flat[count * 3] = 0.0
        for i = 1 to count do
        (
            local p = pts[i] * tm
            flat[3 * i - 2] = p.x
            flat[3 * i - 1] = p.y
            flat[3 * i] = p.z
        )
    )
    flat
)

-- The vertices of the selection at sub-object `level` (1 Vertex, 2 Edge,
-- 3 Border, 4 Polygon, 5 Element), as an array of vertex ids.
fn gsKerbSelectedVerts node level =
(
    local base = node.baseObject
    local verts = case of
    (
        (level == 1): polyop.getVertSelection base
        (level <= 3): polyop.getVertsUsingEdge base (polyop.getEdgeSelection base)
        default: polyop.getVertsUsingFace base (polyop.getFaceSelection base)
    )
    verts as array
)

-- The edges joining two of `verts`, flat: #(a1, b1, a2, b2, ...).
fn gsKerbJoined node verts =
(
    local base = node.baseObject
    local inside = verts as bitArray
    local flat = #()
    for e in polyop.getEdgesUsingVert base inside do
    (
        local ends = polyop.getEdgeVerts base e
        if inside[ends[1]] and inside[ends[2]] do join flat ends
    )
    flat
)

-- Move vertex verts[i] offsets[i] system units along world Y (up 1) or Z
-- (up 2). verts must be in ascending order: polyop pairs the positions with
-- the vertices in index order. One setVert per mesh, rather than a moveVert
-- per vertex (each piece moves by its own offset), keeps Fix to one edit, and
-- one undo record, per mesh.
fn gsKerbMoveUp node verts offsets up =
(
    local base = node.baseObject
    -- The world up axis in object space: that row of the inverse transform.
    local inv = inverse node.objectTransform
    local axis = if up == 1 then inv.row2 else inv.row3
    local pts = polyop.getVerts base verts
    for i = 1 to verts.count do pts[i] += axis * offsets[i]
    polyop.setVert base verts pts
)
