# Blender API notes

Blender Python behaviour that differs across the studio's versions (3.6, 4.5, 5.2), or that
has cost a round of debugging. Each item says how it was confirmed:

- **[installed]**: read in the Blender install's own Python
  (`C:\Program Files\Blender Foundation\Blender <v>\<v>\scripts\...`) or its bundled API
  reference.
- **[running]**: tried in a running Blender, by Sonny or while building the tool.
- **[in use]**: shipped code relies on it and Sonny has used that code without trouble,
  but it wasn't tested on its own.
- **[believed]**: from reading Blender's behaviour or source, not yet confirmed.

**Contents**

1. [Version differences](#1-version-differences)
2. [Sidebar and UI](#2-sidebar-and-ui)
3. [Properties and data](#3-properties-and-data)
4. [Meshes and selection](#4-meshes-and-selection)
5. [Operators, handlers, threads](#5-operators-handlers-threads)

---

## 1. Version differences

**Auto smooth** [running]. 3.6: a mesh setting. Shade Auto Smooth there is
`bpy.ops.object.shade_smooth(use_auto_smooth=True, auto_smooth_angle=a)`, and a plain
`shade_smooth()` turns it *off*. 4.1+: `bpy.ops.object.shade_auto_smooth(angle=a)`, which
adds a "Smooth by Angle" modifier. Detect with
`"use_auto_smooth" in bpy.types.Mesh.bl_rna.properties` (`common.legacy_auto_smooth()`;
`common.set_auto_smooth()` does the right one). The 3.6 FBX importer turns auto smooth on
at 30° by itself when custom normals come in.

**FBX export of 3ds Max smoothing groups** [running]. `mesh_smooth_type='SMOOTH_GROUP'`
exists in 4.5 and 5.2, not in 3.6 (only OFF / FACE / EDGE). Feature-detect, don't
version-check:
`'SMOOTH_GROUP' in bpy.ops.export_scene.fbx.get_rna_type().properties["mesh_smooth_type"].enum_items.keys()`.

**Custom split normals** [installed]. `mesh.has_custom_normals` is exactly what the
Properties > Mesh > Geometry Data panel tests to show "Clear Custom Split Normals Data", in
3.6, 4.5 and 5.2. `bpy.ops.mesh.customdata_custom_splitnormals_clear()` clears them on the
*active* object and works in Object Mode.

**Calling operators from Python** [installed]. `bpy.ops.x.y(execution_context, undo,
**props)`: two optional positional arguments in this order, e.g.
`bpy.ops.foo.bar('EXEC_DEFAULT', True, index=3)` to get an undo step. 3.6 also accepted a
context dict as the first positional argument; 4.0+ dropped that, so use
`context.temp_override(...)` instead on every version. In 5.2, operator calls are
implemented in C (`_bpy.ops.create_function`) but take the same arguments (per the
bundled API reference).

**`Operator.poll_message_set`** [installed] exists in 3.6+ (Blender's own
`bl_operators/assets.py` uses it). Call it on the class inside `poll` to explain a
greyed-out button in its tooltip.

**`UILayout.template_list(..., item_dyntip_propname=, rows=, maxrows=)`** [installed]
all exist in 3.6 (Blender's own file browser uses them).

**Extensions platform** (4.2+) [running]. 3.6 has none; `gs_pipeline_core.extensions_policy`
is a no-op there.

**Bundled Python** [installed]: 3.6 is 3.10.13, 4.5 is 3.11.11, 5.2 is 3.13.13. numpy is
bundled in all three.

---

## 2. Sidebar and UI

**No minimum sidebar width** [running]. `Region.width` is read-only (3.6 - 5.2). Lay out
for the width you get: `common.is_wide(context, px)`. Default sidebar width is 220 px in
3.6 and 280 px in 5.2, so design for ~220.

**Scripts can't switch sidebar tabs** [running]. `Region.active_panel_category` is
read-only in 5.2 and absent in 3.6.

**No custom button or text colours** [running]. Use `row.alert = True` (red, for
errors), `row.active = False` (greyed, for secondary info), icons, and `row.scale_y` for
big buttons.

**Enum items callbacks** [believed, standard Blender advice]. Blender doesn't copy the
strings a dynamic `items` callback returns. Build the lists once and keep them referenced
(module globals); never return a list made fresh on each call.

**Lambdas in deferred annotations** [running]. With `from __future__ import annotations`,
`get=lambda self: ...` inside a PropertyGroup annotation raises `NameError` when called:
Blender evaluates the annotation where module names don't reach the lambda body. Pass
module-level functions (see `_remembered()` in `projects/mgp27/kerb_checker.py`).

**`UIList.draw_item`** [in use]. Use Blender's own signature:
`draw_item(self, context, layout, data, item, icon, active_data, active_prop, index)`.
With `item_dyntip_propname`, a row's tooltip is one of the item's string properties.
`filter_name` (the list's built-in filter) searches the item's `name`.

**Clicking a `UIList` row** sets the active-index property and runs its `update`
callback [in use]. Running an operator from that callback with `undo=True` makes the click
an undo step (Asset Validation's Log). Whether `update` also runs when the clicked row was
already active is [believed], not confirmed.

---

## 3. Properties and data

**Where a property lives decides whether it is saved** [in use]. Properties on
`bpy.types.Scene` (or any ID in the file) are saved in the .blend. Properties on
`bpy.types.WindowManager` live for the session only. Use the window manager for UI state
and for values that must not quietly stick between sessions.

**Setting a property from code runs its `update` too** [in use]. Guard callbacks that set
each other (HW3's `_SELECTING` flag), and make "nothing selected" a value the callback
ignores (index `-1`).

**Python references to datablocks don't survive undo** [believed, standard Blender
advice]. Undo rebuilds the data, so a kept `bpy.types.Object` may be freed. Anything kept
across user actions (the Asset Validation log) stores names, looks them up again, and
treats "not found" as a normal case.

**Load handlers** [in use]. A `bpy.app.handlers.load_post` handler needs the
`@bpy.app.handlers.persistent` decorator to survive the file load it is meant to react
to. It receives one positional argument. Remove it in `unregister()`.

---

## 4. Meshes and selection

**In Edit Mode, `obj.data` is stale** [in use]. The edit mesh only goes back to the
mesh on leaving Edit Mode. Leave it first (`common.ensure_object_mode`), or call
`obj.update_from_editmode()` (MGP27), or read with `bmesh.from_edit_mesh`.

**Bulk element access** [in use]. `mesh.vertices / edges / polygons / loops` support
`foreach_get` / `foreach_set` into numpy arrays: `"co"` (float32 ×3), `"vertices"` on edges
(int ×2), `"loop_total"` on polygons, `"edge_index"` on loops, and `"select"` / `"hide"`
(bool arrays). Far faster than Python loops; use them for any per-element pass.

**Selecting elements from data** [in use]. In Object Mode clear `select` on vertices,
edges and polygons, set it on the wanted elements, then `object.mode_set(mode='EDIT')`
and `mesh.select_mode(use_extend=False, use_expand=False, type='FACE' | 'EDGE' | 'VERT')`.
Setting the select mode makes the selection consistent; in face mode, exactly the flagged
faces end up selected.

**`mesh.reveal()` selects what it reveals** [in use]; `mesh.reveal(select=False)`
doesn't. `mesh.hide()` / `select_all(action='INVERT')` only touch visible elements.

**UV operators that select mesh faces** [in use]. With
`tool_settings.use_uv_select_sync = True`, `uv.select_overlap` selects the mesh faces
themselves. Save and restore the setting.

**`bmesh.new(); bm.from_mesh(mesh)`** [in use] keeps the mesh's element order, so
`face.index` is the polygon index. Call `bm.normal_update()` before relying on face
normals, and `bm.free()` when done.

**Blender's Select Loose** [believed, from Blender's source]. In vertex mode it selects
vertices on no edge; in edge mode, edges on no face (wire edges); in face mode, faces that
share no edge with another. Hidden elements are skipped.

---

## 5. Operators, handlers, threads

**`bpy` only on the main thread** [running]. Slow file-system or network work (an
unreachable UNC path can block for tens of seconds) goes on a `threading.Thread` that
touches no `bpy`. A `bpy.app.timers.register(fn, first_interval=0.2, persistent=True)`
callback polls it and applies the result on the main thread. See
`file_io/file_transfer/server.py`.

**Reports** [running]. `self.report({'WARNING'}, ...)` shows in the status bar;
`{'ERROR'}` opens a pop-up, so tools report problems as warnings and keep the detail in
their log.

**Baking for checks** [in use]. Asset Validation's Overlapping Faces bakes AO in Cycles.
`scene.cycles` doesn't exist when the Cycles add-on is disabled, so check
`hasattr(scene, "cycles")` first, and put the render engine and samples back afterwards.
