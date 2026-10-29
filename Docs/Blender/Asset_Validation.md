# Review > Asset Validation

Checks and quick fixes for an asset before it moves on, in GS Pipeline > Review. Merged
from the old standalone `GS_Asset_Validation` add-on, which `gs_pipeline_core` now
force-disables at launch.

Source: `GS_Pipeline/review/asset_validation/`. For the add-on around it, see
[GS_Pipeline.md](GS_Pipeline.md).

**Contents**

1. [Layout](#1-layout)
2. [Buttons: checks and fixes](#2-buttons-checks-and-fixes)
3. [Writing a check](#3-writing-a-check)
4. [Writing a fix](#4-writing-a-fix)
5. [The Log](#5-the-log)
6. [What is on the tab](#6-what-is-on-the-tab)
7. [Decisions and open points](#7-decisions-and-open-points)

---

## 1. Layout

```
asset_validation/
├── __init__.py    turns every Tool into an operator, runs it into the log, draws the tab
├── _shared.py     Tool, ValidationError, selection helpers, @check, clear_custom_normals
├── log.py         Found (what a check returns), the Log list, Select Objects / Errors, row click
├── geometry.py    one module per section of the tab, in tab order:
├── normals.py         each has TITLE, ICON and TOOLS
├── symmetry.py
├── uv.py
└── cleanup.py
```

---

## 2. Buttons: checks and fixes

Every button is a `Tool(name, label, description, run)` in its section's `TOOLS`.
`__init__.py` makes each one an operator `gs_pipeline.av_<name>` (with undo), so **adding
a button never touches `__init__.py`**. Buttons sit in two columns when the sidebar is at
least 400 px wide, one column otherwise.

`run(context)` does the work. Each run clears the Log first, and what `run` returns
decides what the Log shows:

| `run` returns / raises            | It is a | The Log shows                                       |
| --------------------------------- | ------- | --------------------------------------------------- |
| `log.Found`                       | check   | one row per object with the problem, or one "No ... found." line |
| `(level, message)`                | fix (or a check with nothing to check) | one line; level is `"ok"`, `"warn"`, `"info"` or `"error"` |
| `raise ValidationError(message)`  | either  | the message as an error line, no traceback. For what the artist can put right, usually the selection |
| any other exception               | either  | "Something went wrong: ... Details in the System Console." and the traceback is printed |

---

## 3. Writing a check

```python
from ._shared import Tool, check, selected_meshes
from .log import Found


@check
def ngons(context):
    """Faces with five or more vertices."""
    found = Found("n-gons", 'FACE')
    for obj in selected_meshes(context):
        polygons = obj.data.polygons
        sizes = np.empty(len(polygons), dtype=np.int32)
        polygons.foreach_get("loop_total", sizes)
        found.add(obj, np.flatnonzero(sizes > 4))
    return found

TOOLS = (..., Tool("ngons", "N-Gons", "Find faces with 5 or more vertices", ngons), ...)
```

**`@check`** (`_shared.py`) runs the check in Object Mode, so `obj.data` holds what the
artist sees even when they were in Edit Mode. Afterwards it puts the scene back: the
selected objects and active one, the mode (Edit Mode included), the selected and hidden
vertices / edges / faces of the selected meshes, and the mesh select mode. So a check may
use Blender's selection operators as a way to compute the answer
(`uv.select_overlap`, `mesh.select_mirror` / `hide` / `reveal`) and read the result back.
The artist never sees that happen.

**`Found(problem, element=None, clean=None)`** (`log.py`):

- `problem` finishes the sentence "SM_Door_L has ___." and should be plural:
  `"overlapping UVs"`, `"n-gons"`, `"no UVs"`.
- `element` is `'VERT'`, `'EDGE'` or `'FACE'`, saying what the indices are, or `None` when
  the problem is the whole mesh (no UVs, custom normals). Only element checks enable
  Select Errors.
- `clean` is the line when nothing is found; it defaults to `"No <problem> found."`. Give
  one when that reads wrong: `Found("no UVs", clean="All selected meshes have UVs.")`.
- `found.add(obj, indices=None, problem=None)` flags an object. For an element check it
  is skipped when `indices` is empty, so pass every mesh and let it decide. `problem`
  overrides the wording for one object: Concave Faces says "concave", "non-planar" or
  both per mesh.
- The status bar gets one summary: `"N-gons on 3 meshes."`.

How to compute the answer, cheapest first:

1. **numpy over mesh data**: `foreach_get` into an array (n-gons, loose vertices / edges,
   zero-length edges).
2. **`bmesh.new()` + `bm.from_mesh(mesh)`** for per-face geometry tests (concave /
   non-planar). Call `bm.normal_update()` before using face normals, and `bm.free()` after.
3. **A Blender operator** only when its behaviour *is* the definition (Select Overlap for
   overlapping UVs, Select Mirror for asymmetric faces). `@check` cleans up after it.

Loose Vertices / Loose Edges reproduce Blender's Select Loose from the data: vertices on
no edge, edges on no face. Unlike the operator, they include hidden elements.

---

## 4. Writing a fix

A fix returns `(level, message)` and handles its own selection:

```python
def custom_normals_data(context):
    meshes = selected_meshes(context)
    saved = save_selection(context)
    common.ensure_object_mode(context)
    try:
        cleared = clear_custom_normals(context, meshes)
    finally:
        restore_selection(context, saved)
    if not cleared:
        return "ok", "No custom split normals found."
    return "ok", "Cleared custom split normals from {}.".format(plural(cleared, "mesh", "meshes"))
```

Wording follows the existing fixes: "Removed 3 vertex groups." / "No vertex groups
found.". If two buttons do the same work, put it in `_shared.py` and call it from both:
`clear_custom_normals` is used by Normals > Apply Smooth Shading and Cleanup > Custom
Normals Data.

---

## 5. The Log

`log.py` owns everything about the Log at the bottom of the tab:

- **Message lines** (a `common.ToolLog`) above **a scrolling list**: a `UIList`
  (`GS_UL_AV_Log`) over `WindowManager.gs_av_log`, 8 rows before it scrolls. The artist
  can drag it taller and filter it by name, and hovering a row shows its full text, which
  matters in a narrow sidebar. Under the list are **Select Objects** / **Select Errors**,
  then the count, "50 objects in the log".
- **Rows hold object names, not objects.** The log outlives undo, which frees Python
  references to objects. A renamed or deleted object is reported, not crashed on.
- **`_found`** (module global) keeps the last `Found`: per object, the element indices
  (numpy) and how many of that element the mesh had. Select Errors skips, with a
  warning, a mesh whose element count changed since the check, because its indices no
  longer mean anything.
- **Select Objects** selects every listed object (Object Mode). **Select Errors** selects the
  found elements on them in Edit Mode, in the right select mode. Both grey out through
  `poll`, with the reason as the tooltip ("Run a check first.", "This check is about
  whole meshes: use Select Objects.").
- **Clicking a row** selects that object. The list's active index
  (`WindowManager.gs_av_log_index`) has an `update` callback that runs
  `bpy.ops.gs_pipeline.av_select_log_row('EXEC_DEFAULT', True, index=i)`. It goes through
  an operator, with `undo=True`, so the click is an undo step like an Outliner click and a
  missing object shows in the status bar. Ctrl + mouse wheel over the list steps through
  the rows.
- Emptied at the start of every button press and when a file is opened (`load_post`).

---

## 6. What is on the tab

| Section    | Button                     | Kind  | Log wording ("X has ___") / element               |
| ---------- | -------------------------- | ----- | ------------------------------------------------- |
| Geometry   | Duplicate Vertices         | check | duplicate vertices, VERT (across all selected meshes) |
|            | Meshes Overlap             | check | faces overlapping another mesh, FACE (needs 2+ meshes) |
|            | N-Gons                     | check | n-gons, FACE                                      |
|            | Loose Vertices             | check | loose vertices, VERT                              |
|            | Loose Edges                | check | loose edges, EDGE                                 |
|            | Zero Length Edges          | check | zero-length edges, VERT (the edges' vertices, which show where an edge can't) |
|            | Concave Faces              | check | concave / non-planar faces, FACE                  |
|            | Overlapping Faces          | check | interior faces, FACE (quick AO bake in Cycles)    |
| Normals    | Recalculate Normals        | fix   |                                                   |
|            | Apply Smooth Shading       | fix   | clears custom normals, then auto smooth 30°       |
|            | Toggle Face Orientation    | fix   | viewport overlay                                  |
|            | Check Custom Normals Data  | check | custom split normals, whole mesh                  |
| Symmetry X | Asymmetric Vertices        | check | asymmetric vertices, VERT                         |
|            | Asymmetric Faces           | check | asymmetric faces, FACE                            |
| UV         | Self Penetrating UVs       | check | overlapping UVs, FACE                             |
|            | Missing UVs                | check | no UVs, whole mesh                                |
|            | Sharp Edges to UV Seams    | fix   |                                                   |
| Cleanup    | Vertex Colors              | fix   |                                                   |
|            | Vertex Groups              | fix   |                                                   |
|            | Custom Normals Data        | fix   | Clear Custom Split Normals Data                   |
|            | Unused Materials           | fix   |                                                   |
|            | Cameras                    | fix   | every camera in the file                          |
|            | Apply Transforms           | fix   |                                                   |

"Custom split normals" is what Blender's Geometry Data panel tests (`mesh.has_custom_normals`)
to show "Clear Custom Split Normals Data", in 3.6, 4.5 and 5.2 alike.

---

## 7. Decisions and open points

Decided with Sonny, 2026-10-29:

- **Checks don't select.** Selecting faces on every check was "pretty strict"; most of
  the time the object's name is enough. Element selection is the opt-in Select Errors.
- **The Log scrolls.** A list capped at 20 names with "...and 30 more" was rejected:
  every flagged object must be reachable.
- **Rows read "SM_Mesh_A has overlapping UVs."**, one per object, with no counts.
- **Clicking a row selects that object.**

Not yet confirmed in Blender:

- Clicking the row that is already active should select its object again. That relies
  on Blender running the index's `update` callback when the value doesn't change. This
  is believed from Blender's UI code but hasn't been tried separately. If it fails, have
  the callback reset the index to -1 after selecting, at the cost of the row highlight.
