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
│   └── asset_validation/    see Asset_Validation.md
└── projects/                Projects category: one package per project
    ├── cm/
    │   ├── __init__.py      GROUP (one tab), register
    │   ├── vehicle.py       the tab: scope, LOD / custom part switching, Check Names, its Log
    │   ├── variants.py      which LOD / part version each object is; hiding the rest
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
| `Scene` PointerProperty        | saved in the .blend                     | settings that belong to the file              | `gs_hw3`, `gs_file_transfer_props`, `gs_cm` |
| `WindowManager` properties     | this Blender session only, never saved  | UI state, lists rebuilt at runtime, spec values that must not quietly stick | `gs_category`, `gs_group`, `gs_subtab`, `gs_mgp27_kerb`, `gs_person_list`, `gs_av_log`, `gs_av_log_index`, `gs_cm_parts`, `gs_cm_log` |
| `common.pref_get` / `pref_set` | across sessions (`gs_pipeline_prefs.json` in this Blender version's config folder) | an artist's own preferences; the counterpart of Maya optionVars | MGP27 up axis, measure along ground, fix mode |
| module globals                 | this session                            | caches, data RNA can't hold (numpy arrays)    | Asset Validation `log._found`              |

A list a `UIList` shows has to be a `CollectionProperty`. Keep what a click needs in the
row itself, such as a file path, so a click reads one item rather than rebuilding the list.

---

## 6. Names that must not change

- **Scene property names** (`gs_hw3`, `gs_file_transfer_props`, `gs_cm`) and their fields are
  saved in artists' .blend files.
- **CM object names** (`projects/cm/names.py`) are the client's contract (spec v.3 and
  their example car), not ours: the LOD / part tokens and the essential anchors.
- **Operator ids** may be in artists' keymaps and quick favourites.
- **GS File Transfer file names** (`<source>_to_<target>.fbx` and the per-object /
  per-user variants, built in `file_transfer/config.py` and `transfer.py` / `ui.py`) are a
  contract with the Maya and 3ds Max sides of the tool. Change all three or none.
- **HW3 payload folders** (`%TEMP%\GSApplication\...` in `hw3/payloads.py`) are where the
  Unreal and 3ds Max exporters write; they mirror the Maya HW3 tool.

Class names can change freely; nothing outside the add-on refers to them.

---

## 7. common.py and object_log.py

| Helper                                   | What for                                                  |
| ---------------------------------------- | --------------------------------------------------------- |
| `select_only`, `ensure_object_mode`      | selection and mode                                        |
| `legacy_auto_smooth`, `set_auto_smooth`  | auto smooth, which works differently in 3.6 and 4.1+ (API_Notes.md) |
| `merge_duplicate_materials`              | fold the `Name.001` copies an import made into the existing `Name` |
| `redraw_view3d`, `is_wide`, `wait_cursor`| UI: redraw after state changed outside a draw; responsive layout; long actions |
| `ToolLog`, `LOG_ICONS`, `plural`         | the short result log at the bottom of a tab; "3 parts" in its lines |
| `pref_get`, `pref_set`                   | remembered preferences (JSON, per Blender version)        |
| `register_classes`, `unregister_classes`, `register_modules`, `unregister_modules` | registration |

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
folder, **Server** through `\\192.168.1.210\Temp\File_Transfer\<user>\`. Merge (one file)
or Individual (one file per mesh).

- The server check runs on a **worker thread**, because an unreachable UNC path can block
  for tens of seconds. A main-thread timer applies the result, since `bpy` must not be
  touched off the main thread. Server buttons are greyed (with the reason, via `poll`)
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
`M:\cm\documentation\Vehicle`). One tab, three jobs on the objects in **Scope** (a
collection and everything in it; empty = the whole scene):

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
  there. Which parts and letters exist differs per file, so the global buttons (every
  part that has a letter) and the list (one part) are read from the scene. The list's
  rows aren't selectable: its active index always reads -1 and ignores clicks.
- **Check Names**: the essential anchors and wheel meshes (`names.ESSENTIAL_ANCHORS`,
  drawn from the example car) under the right parents, and spelling on everything:
  `_LOD<n>` in capitals, 0-2 and matching the objects above, part letters matching their
  part, English letters / digits / `_` only (the example had a Cyrillic С), no `.001`.
  Results go in the tab's `ObjectLog`, which LOD / part clicks don't clear.

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
