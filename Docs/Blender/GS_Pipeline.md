# GS Pipeline add-on

The studio's master panel in Blender: 3D View sidebar (N) > **GS Pipeline**. One add-on
holds many small tools, and the Projects category is expected to grow to at least 4-5
projects. The structure below exists so that each tool is self-contained, easy to find,
and costs nothing while it isn't on screen.

Source: `Environment/Blender/common/scripts/addons/GS_Pipeline/`, one copy shared by
Blender 3.6, 4.5 and 5.2 (see [README.md](README.md)).

**Contents**

1. [Layout](#1-layout)
2. [The panel: Category > Group > Tab](#2-the-panel-category--group--tab)
3. [Registration](#3-registration)
4. [Recipes: adding things](#4-recipes-adding-things)
5. [Where data lives](#5-where-data-lives)
6. [Names that must not change](#6-names-that-must-not-change)
7. [common.py and object_log.py](#7-commonpy-and-object_logpy)
8. [The tools](#8-the-tools)
9. [Performance rules](#9-performance-rules)
10. [UI conventions](#10-ui-conventions)

---

## 1. Layout

```
GS_Pipeline/
├── __init__.py              bl_info, category bar order, register / unregister
├── panel.py                 the sidebar panel + the Category / Group / Tab descriptors
├── common.py                helpers more than one tool uses (section 7)
├── object_log.py            the Log with a list of objects that check-style tools share (section 7)
├── file_io/                 File I/O category
│   └── file_transfer/       GS File Transfer
│       ├── __init__.py      GROUP, register
│       ├── config.py        file-name contract, folders, applications, FBX settings
│       ├── transfer.py      FBX import / export, the runners Local and Server share
│       ├── smoothing_groups.py   closing open sharp edges for 3ds Max smoothing groups
│       ├── server.py        is the share reachable, the user list (worker thread)
│       └── ui.py            properties, operators, drawing the tab
├── review/                  Review category
│   ├── asset_validation/    see Asset_Validation.md
│   └── lod_check.py         LOD Check: show one LOD (0-6, numbers or letters) at a time
└── projects/                Projects category: one package per project
    ├── cm/
    │   ├── __init__.py      GROUP (one tab), register
    │   ├── vehicle.py       the tab: Quick Tools, scope, LOD / custom part switching, Check Names, Animation Check, its Log
    │   ├── quick_tools.py   Create Anchor, Rename Mesh Data (on the selection)
    │   ├── variants.py      which LOD / part version each object is; hiding the rest
    │   ├── animation.py     Animation Check: turning the LOD0 doors open and closed
    │   ├── name_check.py    the Check Names rules
    │   └── names.py         the CM naming contract: LOD / part tokens, the essential names (no bpy)
    ├── hw3/
    │   ├── __init__.py      GROUP (one Tab per tool module), register
    │   ├── materials.py     Materials tab
    │   ├── modeling.py      Modeling tab
    │   ├── props.py         lists and fields both tabs share (on the scene)
    │   └── payloads.py      pipeline folders, reading the JSON / FBX payloads
    └── mgp27/
        ├── __init__.py      GROUP, register
        ├── kerb_checker.py  Kerb Height Checker tab: settings, operators, drawing
        └── kerb_measure.py  the measuring / fixing (mirrors the Maya tool)
```

Rule of thumb: **one module per tab**. When a tool outgrows one module, split it by
concern inside its own package (as File Transfer is). A project's own helpers stay in its
package (HW3's `payloads.py`); only what several tools share goes in `common.py`.

---

## 2. The panel: Category > Group > Tab

`panel.py` defines the three descriptors and the one `bpy.types.Panel`
(`GS_PT_Pipeline`):

```python
Tab(label, draw)                  # one screen of a tool; draw(layout, context)
Group(id, label, tabs)            # a tool or project, tabs in bar order
Category(id, label, modules)      # a top-level category; modules each have GROUP + register()
```

- The panel draws a category bar, a group bar and a tab bar, each **only when it has
  more than one entry**, then calls the active tab's `draw(layout, context)` with
  `layout` being a box.
- The bars are three enums on the window manager: `gs_category` (static, so it can have
  a default), `gs_group` and `gs_subtab` (dynamic: their items depend on the level
  above). The item lists are built once in `panel.register()` and kept in module
  globals. Blender doesn't copy the strings an enum items callback returns, so a list
  made fresh on every call can be freed while the UI still shows it.
- **An items callback must never read its own enum.** Reading a dynamic enum runs its
  callback, so that loops forever and freezes Blender with no error. `_tab_enum_items`
  uses `_active_group()` (category and group only); only `draw` uses `_active()`, which
  also reads the tab. This shipped once and froze 4.5 on HW3's tab bar (see API_Notes.md).
- A tab id is its label upper-cased, so two tabs of one group can't share a label.
- **Ctrl+Shift+G** (any 3D View) runs `gs_pipeline.toggle_sidebar`: it opens the sidebar
  on the GS Pipeline tab, and closes it when GS Pipeline is already showing. The tab is
  set through `Region.active_panel_category`. A sidebar that has never drawn lists no
  tabs yet, so a timer retries the switch for half a second. Where the property is missing
  (3.6) or read-only, the shortcut opens the same panel as a pop-up at the mouse instead
  (`wm.call_panel`, keep open). The API reference lists the property as writable from 4.2,
  but an earlier session noted it as read-only in 5.2. That isn't settled at runtime yet.
  No Ctrl / Shift / Alt + G is free in Object Mode in 3.6 / 4.5 / 5.2; Ctrl+Shift+G takes
  over Blender's "Add Selected to Active Collection" there (bound in the "Object Mode"
  keymap so it wins) and is free in the other modes. Maya uses the same key for GS File
  Transfer. In a pop-up `context.region` is the 3D View it was opened from, so the panel
  draws inside `common.drawing_popup(width)` and tabs read their width through
  `common.panel_width` / `is_wide`, never `context.region.width` directly.
- Category bar order is `CATEGORIES` in the add-on's `__init__.py`; the category shown on
  launch is `DEFAULT_CATEGORY` (`"FILE_IO"`).

---

## 3. Registration

The add-on's `register()` registers every category's modules in order, then
`panel.register(CATEGORIES, DEFAULT_CATEGORY)`. `unregister()` runs in reverse.

Every tool module or package has `register()` / `unregister()`. Use the helpers in
`common.py`, not hand-written loops:

```python
CLASSES = (GS_PG_..., GS_OT_..., ...)          # dependency order: PropertyGroups first

def register():
    common.register_classes(CLASSES)
    bpy.types.Scene.gs_example = PointerProperty(type=GS_PG_Example)
    if _on_load not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(_on_load)

def unregister():
    if _on_load in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_on_load)
    if hasattr(bpy.types.Scene, "gs_example"):
        del bpy.types.Scene.gs_example
    common.unregister_classes(CLASSES)      # reverse order; skips one that never registered
```

A package registers its parts with `common.register_modules(...)` /
`common.unregister_modules(...)` (reverse order). Handlers that must survive a file load
need `@bpy.app.handlers.persistent`. Timers and handlers are removed in `unregister()`.

---

## 4. Recipes: adding things

### A tab in an existing project

1. New module `projects/<project>/<tool>.py` with a `draw(layout, context)` function,
   `TAB = Tab("Label", draw)`, `CLASSES`, `register()` / `unregister()`. Copy the shape
   of `projects/mgp27/kerb_checker.py`.
2. Add the module to `TOOLS` in `projects/<project>/__init__.py`, in tab-bar order.

### A new project

1. New package `projects/<project>/` shaped like `projects/mgp27/`:

   ```python
   from ... import common
   from ...panel import Group
   from . import kerb_checker

   TOOLS = (kerb_checker,)          # tab-bar order; each has TAB + register()
   GROUP = Group("MGP27", "MGP27", tuple(tool.TAB for tool in TOOLS))

   def register():
       common.register_modules(TOOLS)

   def unregister():
       common.unregister_modules(TOOLS)
   ```

   Data several tabs share goes in the package's own `props.py`, registered first and
   unregistered last (see `projects/hw3/__init__.py`).
2. Add the package to `Category("PROJECTS", "Projects", (...))` in
   `projects/__init__.py`, where it should sit in the group bar.
3. If the project ports a Maya tool, say so in the module docstring and keep the logic in
   step with it (as `kerb_measure.py` does).

### A tool in File I/O or Review

A module or package with a `GROUP` and `register()` / `unregister()`, added to that
category's `Category(...)` in its `__init__.py`. A check or fix inside Asset Validation
is simpler still: see [Asset_Validation.md](Asset_Validation.md).

### A new category

A package whose `__init__.py` has `CATEGORY = Category(id, label, modules)`, added to
`CATEGORIES` in the add-on's `__init__.py`.

### Naming

- Classes: `GS_OT_<TOOL>_<Name>` (operators), `GS_PG_...` / `GS_..._Props`
  (PropertyGroups), `GS_UL_...` (UIList: Blender wants `_UL_` in the name).
- Operator ids: `gs_pipeline.<tool>_<action>` (e.g. `gs_pipeline.mgp27_kerb_check`,
  `gs_pipeline.av_ngons`). GS File Transfer predates this and uses `gs.*`; leave those.
- Properties hung on Blender types: `gs_<tool>...` (e.g. `Scene.gs_hw3`).

---

## 5. Where data lives

| Where                          | Lasts                                   | Use it for                                    | In use                                     |
| ------------------------------ | --------------------------------------- | --------------------------------------------- | ------------------------------------------ |
| `Scene` PointerProperty        | saved in the .blend                     | settings that belong to the file              | `gs_hw3`, `gs_file_transfer_props`, `gs_cm`, `gs_lod_check` |
| `WindowManager` properties     | this Blender session only, never saved  | UI state, lists rebuilt at runtime, spec values that must not quietly stick | `gs_category`, `gs_group`, `gs_subtab`, `gs_mgp27_kerb`, `gs_person_list`, `gs_av_log`, `gs_av_log_index`, `gs_cm_parts`, `gs_cm_log` |
| `common.pref_get` / `pref_set` | across sessions (`gs_pipeline_prefs.json` in this Blender version's config folder) | an artist's own preferences; the counterpart of Maya optionVars | MGP27 up axis, measure along ground, fix mode |
| module globals                 | this session                            | caches, data RNA can't hold (numpy arrays)    | Asset Validation `log._found`              |

A list a `UIList` shows has to be a `CollectionProperty`. Keep what a click needs in the
row itself, such as a file path, so a click reads one item rather than rebuilding the list.

---

## 6. Names that must not change

- **Scene property names** (`gs_hw3`, `gs_file_transfer_props`, `gs_cm`, `gs_lod_check`) and their fields are
  saved in artists' .blend files.
- **CM object names** (`projects/cm/names.py`) are the client's contract (spec v.3 and
  their example car), not ours: the LOD / part tokens and the essential anchors.
- **Operator ids** may be in artists' keymaps and quick favourites.
- **GS File Transfer folders and file names** (local `%TEMP%\GSPipeline\FileTransferFbx\transfer.fbx`
  and its `individual\` folder; server `<sender>_to_<receiver>.fbx` in the sender's folder
  and its per-object variants; built in `file_transfer/config.py` and `transfer.py` / `ui.py`)
  are a contract with the Maya (`GSPipeline/Files_IO/gs_file_transfer.py`) and 3ds Max
  (`3dsMax/common/gstools/file_io/file_transfer/gs_file_transfer.py`) sides of the tool.
  Change all three or none.
- **HW3 payload folders** (`%TEMP%\GSApplication\...` in `hw3/payloads.py`) are where the
  Unreal and 3ds Max exporters write; they mirror the Maya HW3 tool.

Class names can change freely; nothing outside the add-on refers to them.

---

## 7. common.py and object_log.py

| Helper                                   | What for                                                  |
| ---------------------------------------- | --------------------------------------------------------- |
| `select_only`, `ensure_object_mode`      | selection and mode                                        |
| `scope_objects`                          | the objects in a Scope collection (empty: the scene), by default only those in this view layer (CM, LOD Check) |
| `legacy_auto_smooth`, `set_auto_smooth`  | auto smooth, which works differently in 3.6 and 4.1+ (API_Notes.md) |
| `merge_duplicate_materials`              | fold the `Name.001` copies an import made into the existing `Name` |
| `redraw_view3d`, `is_wide`, `wait_cursor`| UI: redraw after state changed outside a draw; responsive layout; long actions |
| `ToolLog`, `LOG_ICONS`, `plural`         | the short result log at the bottom of a tab; "3 parts" in its lines |
| `pref_get`, `pref_set`                   | remembered preferences (JSON, per Blender version)        |
| `register_classes`, `unregister_classes`, `register_modules`, `unregister_modules` | registration |
| `register_keymap_items`, `unregister_keymap_items` | shortcuts in Blender's add-on keyconfig (Preferences > Keymap can change them); add-on items beat Blender's own in the same keymap |
| `panel_width`, `drawing_popup`           | the width a tab draws in, sidebar or Ctrl+Shift+G pop-up (`is_wide` uses it) |

`ToolLog` levels, as in the Maya tools: `ok` done as asked, `warn` done but look at this,
`error` nothing done (the message says why), `info`. Blender can't colour label text, so
the icon carries the level and error lines draw in the alert colour. Passing the operator
to `add()` also reports the line to the status bar, warn / error as `{'WARNING'}`. An
`{'ERROR'}` report would open a pop-up.

### object_log.py

A tool whose result is a list of objects (a check) uses `object_log.ObjectLog` rather than
building its own: message lines (a `ToolLog`), a scrolling list with one row per problem,
**Select Objects**, and "N objects in the log" under it. Clicking a row selects its
object; a hidden one is made active and reported. Asset Validation and CM both use it.

```python
LOG = ObjectLog("cm", "Pick a Scope, then press Check Names.")   # list: WindowManager.gs_cm_log

LOG.register() / LOG.unregister()        # with the tool's own classes
LOG.clear(context)                       # messages and list, at the start of an action
LOG.clear_messages()                     # messages only: an action that leaves the list alone
LOG.add(message, level, op)              # a message line
LOG.show(context, rows, op, clean)       # a check's result: (object name, text, level) rows
LOG.draw(layout, context, columns)       # the Log box
```

A row with name `""` is a problem with no object to select (something missing); the count
says "N missing". Each log makes its own operators, `gs_pipeline.<id>_select_objects` and
`gs_pipeline.<id>_select_log_row`, so their ids stay what they were for Asset Validation.
The row type and UIList are shared and registered once by the add-on, before the tools.
A log that needs more subclasses it: Asset Validation's adds Select Errors (see
Asset_Validation.md).

---

## 8. The tools

### File I/O > GS File Transfer (`file_io/file_transfer/`)

Moves FBX files between Blender, Maya and 3ds Max: **Local** through this machine's temp
folder, **Server** through `\\192.168.1.210\Temp\GSPipeline\FileTransferFbx\<user>\`. Always
one file per transfer (Merge).

- **Individual mode is shelved** (Sonny, 2026-11-17): one FBX per mesh only ever worked
  Blender <-> 3ds Max, since Maya has no such mode. `config.INDIVIDUAL_MODE = False` hides
  the Mode row, and `transfer.individual_mode()` answers False, so every transfer is
  Merge, even in a .blend saved with Individual picked. The code is kept; the 3ds Max tool
  has the same switch. Everything below about Individual applies once it is back.

- **Local is one shared file per machine**, not one per application pair:
  `%TEMP%\GSPipeline\FileTransferFbx\transfer.fbx` (Merge), or every `<object>.fbx` in its
  `individual\` subfolder, which each Individual export empties first. Whatever exported
  last is what any DCC imports, like a clipboard.
- **No application in any name or picker**, Server included: `<sender>_to_<receiver>.fbx`
  in the sender's folder (`<object>_<sender>_to_<receiver>.fbx` per mesh in Individual
  mode). Settings that depend on the receiver are toggles instead: **Export Smoothing
  Groups** applies to every export, so untick it when sending to Maya or Blender.
- **File rows** show what is waiting where and when it was written ("Today 14:32"), so a
  stale file is seen before it is imported: Local shows the shared file (or the
  individual folder's count and newest), Server shows Received and Sent for the picked
  user. Local rows are read while drawing. Server rows are read on a worker thread
  (`file_status.ServerFiles`), once per user and mode, and are cleared by a server transfer
  or the refresh button, never re-read on every redraw.
  Decisions (Sonny, 2026-11-17), the same in the Maya and 3ds Max tools.
- The server check runs on a **worker thread**, because an unreachable UNC path can block
  for tens of seconds. A main-thread timer applies the result, since `bpy` must not be
  touched off the main thread. It probes the share (`\\192.168.1.210\Temp`), not
  `SERVER_DIR`: the transfer folder only exists once someone has exported to it. Server buttons are greyed (with the reason, via `poll`)
  until the share is known to be reachable. The check re-runs on file load and from the
  refresh button.
- The user list is read from two deployment CSVs on the share, de-duplicated, and copied
  into `WindowManager.gs_person_list` for the User search field.
- **3ds Max smoothing groups**: the FBX exporter's `SMOOTH_GROUP` mode exists in 4.5 and
  5.2 only; the option is greyed out in 3.6. A hard edge only survives as a smoothing-group
  border if it closes a region, so `smoothing_groups.py` walks open-ended sharp edges
  onward. It marks them on the real mesh for the length of the export only, then takes them
  out again.
  Decision (Sonny, 2026-10-19): smoothing groups travel **inside the FBX**, read by Max's
  own "Import Smoothing Groups", not as a JSON sidecar. 3.6 not supporting it was
  accepted. Don't reintroduce a sidecar without asking.
- Import post-processing: optional clear normals, merge duplicate materials, optional
  Shade Auto Smooth. On 3.6 the importer turns auto smooth on at 30°, which re-splits
  imported normals, so it is set to 180° to leave shading to the imported normals.

### Projects > CM (`projects/cm/`)

Client project Rev Match Racing (VR cars; spec and example car under
`M:\cm\documentation\Vehicle`). One tab. At the top, **Quick Tools**, the everyday
building steps, on the selection (`quick_tools.py`):

- **Create Anchor**: an empty at the active object's origin and orientation (not its
  scale), named `anchor_` + the active object's name, made the parent of the selection.
  The anchor takes the selection's place in the hierarchy: it goes under the active
  object's nearest unselected parent, in the active object's collections. Only the
  outermost selected objects are re-parented (a selected child of a selected object stays
  under it), with no parent inverse, so the active object sits at 0 under its anchor.
  Everything keeps its place in the world. The new anchor is left selected and active.
- **Rename Mesh Data**: each selected object's mesh named after the object. A mesh
  several objects use is left alone (logged); names swapped among the selection are
  sorted out in two passes rather than ending in `.001`.

Below them, four jobs on the objects in **Scope** (a collection and everything in it;
empty = the whole scene):

- **LOD**: All, LOD0, LOD1, LOD2: every CM car has exactly those (`names.LODS`); any
  other number is a mistake, shown only under All and reported by Check Names. An
  object's LOD is the `_LOD<n>` in its name (not always last:
  `l_door_handle_LOD0_highlight`), else the nearest one above it. Objects with no LOD
  anywhere above them are left alone. The buttons are an enum on the scene whose
  `update` does the hiding, so the click's own undo step covers it.
- **Custom Parts** (their versions are called Default and Part A, B...): a part is the
  outermost `_part_<X>` object (`anchor_hood_part_B_LOD0`) and everything under it; it
  swaps with the default object of the same name without `_part_<X>` and everything
  under that, at the same LOD. Swapping whole subtrees, not mesh by mesh, is deliberate
  (Sonny, 2026-10-29): a part's meshes need not match the default ones, and some parts
  have no default version. A part with no version at the LOD on show shows the default
  there. Part letters are A to E (`names.PART_LETTERS`, confirmed with the client
  2026-10-31); a car may stop earlier, so the global buttons (one per letter some part
  has) and the list (one part) are read from the scene. A `_part_` token with any other
  letter isn't a part: it shows like any object and Check Names reports it. A lowercase
  `_part_a` still switches as A, as `_lod1` does for LODs. The list's rows aren't
  selectable: its active index always reads -1 and ignores clicks.
- **Check Names**: the essential anchors and wheel meshes (`names.ESSENTIAL_ANCHORS`,
  drawn from the example car) under the right parents, and spelling on everything:
  `_LOD<n>` in capitals, 0-2 and matching the objects above, part letters A-E matching
  their part, English letters / digits / `_` only (the example had a Cyrillic С), no
  `.001`. Results go in the tab's `ObjectLog`, which LOD / part clicks don't clear.
- **Animation Check** (LOD0 only, greyed otherwise; more checks may join the doors): a
  Doors slider, 0-90°, turns the door anchors (`names.DOORS`: exterior and interior,
  pivoted at the same hinge, and their custom parts) about **world Z through their own
  origin**, left doors -angle, right doors +angle (the car faces -X). Their rotation
  isn't applied and varies, so the turn is worked out in each anchor's parent space and
  written to its rotation channel only, in its own rotation mode. The rotation each
  anchor had before opening is kept on the scene (`gs_cm.closed_doors`, an Object
  pointer per anchor, so a rename doesn't lose it); every angle is turned from there,
  and 0° writes it back exactly, so dragging never drifts. Leaving LOD0 closes the
  doors. The angle is saved with the file: a file saved with the doors open is
  delivered open.

Hiding is Blender's eye (H / Alt+H) in the current view layer, chosen so artists can see
and undo it. The choices are on the scene (`gs_cm`) and saved, like the hiding; the
part buttons and list are re-read from the scene on file load, Reload and every click.

### Projects > HW3 (`projects/hw3/`)

Port of Maya's `HW3_Tools.py`. **Materials** assigns Unreal material-instance JSON or
texture data to the active material as a Principled BSDF network, with Maya's
place2dTexture repeat / offset maths on a Mapping node. **Modeling** handles source-module
FBX in and out and the building-scene sync.

- Payload folders (`payloads.py`): `%TEMP%\GSApplication\unreal-engine\{mat-ins,textures}`
  and `%TEMP%\GSApplication\3dsmax\hw3_tools\{mesh,io}`, the same as the Maya tool.
- Material list rows store their JSON file's path; picking a row reads that one file.
  Lists saved in a .blend before 2026-10-29 stored something else there and need one
  **Refresh**.

### Projects > MGP27 (`projects/mgp27/`)

**Kerb Height Checker**: finds kerb steps off the MGP27 height spec and fixes them.
`kerb_measure.py` follows Maya's `MGP27_Kerb_Height_Checker_UI.py` line for line; change
the two together. Its docstring explains how a step is measured. Spec values (height,
tolerance, radius, ignore under) live on the window manager, so they reset each session;
the artist's preferences are remembered (`common.pref_*`, same keys as the Maya
optionVars).

### Review > Asset Validation (`review/asset_validation/`)

Checks and quick fixes before an asset moves on. See [Asset_Validation.md](Asset_Validation.md).

### Review > LOD Check (`review/lod_check.py`)

CM's LOD switching for any asset: show All or one of LOD0-LOD6 in **Scope**, hiding the
rest with Blender's eye. **Naming** picks how the names spell the level: Numbers
(`Tree_LOD0`) or Letters (`Tree_LODA`, A being LOD0, the older studio convention also
read by Maya's `gs_lod.py`). An object's LOD is read as in CM (the last `_LOD<n>` token,
else the nearest one above it; no LOD anywhere above: left alone), except that a letter
must be a capital, so a word like `_lods` is never a level. A LOD past 6 / G shows only
under All and is counted in the log. Switching Naming re-applies the choice once the panel
has hidden anything; if nothing in scope has a LOD in the chosen naming but some has one
in the other, the log says to switch. Choices are on the scene (`gs_lod_check`), saved
with the file.

Shortcuts, mouse over a 3D View: **Alt + Numpad 0-6** shows that LOD, **Alt + Numpad \***
shows all (`gs_pipeline.lod_check_show`), using the tab's Scope and Naming even when the
tab isn't on screen; the result also goes to the status bar. Numpad keys alone (and most
Ctrl / Shift + Numpad) are Blender's view keys; Alt + Numpad 0-9 and \* are free in 3.6,
4.5 and 5.2 (Alt + Numpad . is not). The tab shows the keys under the LOD buttons.

---

## 9. Performance rules

The panel redraws constantly (hover, any scene change), so draw code is the hot path.

- **Only the active tab's `draw` runs.** A tool costs nothing while it is off screen; keep
  it that way (no work in the panel itself, none at import time beyond defining things).
- **`draw()` does no disk or network I/O, no mesh iteration, and no operator-RNA lookups.**
  Work out session-constant answers once and keep them. Example:
  `smoothing_groups.fbx_supports_smoothing_groups()` asks the FBX exporter once, not on
  every redraw.
- **Clicks read only what they need.** Store the path or id in the list row (HW3 Material
  list) instead of re-reading a folder per click.
- **Slow I/O goes on a worker thread**, with results applied on the main thread by a
  `bpy.app.timers` callback (GS File Transfer's server check). Long main-thread actions
  show `common.wait_cursor`.
- **Mesh data in bulk**: `foreach_get` / `foreach_set` into numpy arrays rather than
  per-vertex Python loops (Asset Validation's n-gon, loose and zero-length checks; MGP27).

---

## 10. UI conventions

See also [README.md](README.md) section 5 and, for the rules the studio applies in every
DCC, [Docs/Maya_UI_Guidelines.md](../Maya_UI_Guidelines.md).

- Group settings in `layout.box()` sections with a titled label and icon; related values
  share a row.
- Lay out for a ~220 px sidebar (3.6's default; 5.2's is 280). Use
  `common.is_wide(context, px)` to put things side by side only when there is room. Each
  tool picks its own threshold (Asset Validation 400 px; MGP27 360 / 260 px).
- Big actions: `row.scale_y = 1.3 ... 1.6`. No custom colours (not possible).
- Results go in the tab's log (`common.ToolLog`, or `object_log.ObjectLog` when the result
  is a list of objects), not pop-ups.
- Greyed-out buttons explain why through `poll` + `cls.poll_message_set(...)`, which
  shows in the tooltip.
