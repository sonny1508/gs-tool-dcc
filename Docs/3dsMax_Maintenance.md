# 3ds Max tool maintenance

How the GSTools 3ds Max setup is put together, and the API behaviour that has actually
caused breakages. Autodesk's online MAXScript docs are incomplete for the newer APIs, so
everything below was checked against the installed 3ds Max builds or in a running Max
session. Where something has not been confirmed, it says so.

**Contents**

1. [Version matrix](#1-version-matrix)
2. [Repo layout and deployment](#2-repo-layout-and-deployment)
3. [Menus: 2025 replaced the whole menu system](#3-menus-2025-replaced-the-whole-menu-system)
4. [MAXScript gotchas](#4-maxscript-gotchas)
5. [Python and Qt inside Max](#5-python-and-qt-inside-max)
6. [Compiled and encrypted third-party plugins](#6-compiled-and-encrypted-third-party-plugins)
7. [Finding answers when the docs don't have them](#7-finding-answers-when-the-docs-dont-have-them)
8. [Testing a change](#8-testing-a-change)

---

## 1. Version matrix

| Max  | `(maxVersion())[1]` | Python | Qt binding | Menu API              | Repo folder    |
| ---- | ------------------- | ------ | ---------- | --------------------- | -------------- |
| 2023 | 25000               | 3.9    | PySide2    | legacy `menuMan`      | `2023 - 64bit` |
| 2024 | 26000               | —      | —          | legacy `menuMan`      | none (unused)  |
| 2025 | 27000               | 3.11   | PySide6    | CUI menu manager      | `2025 - 64bit` |
| 2026 | 28000               | 3.11 * | PySide6 *  | CUI menu manager      | `2026 - 64bit` |
| 2027 | 29000               | 3.13   | PySide6    | CUI menu manager      | `2027 - 64bit` |

\* 2026 is not installed on the dev machine, so its Python and Qt versions have not been
checked there.

**2025 is the breaking release.** It moved to Python 3.11, from Qt5/PySide2 to
Qt6/PySide6, and removed the old menu API. A tool that works on 2023 and has never been
run on 2025+ should be treated as untested.

Branch on the version number when you need to:

```maxscript
if (maxVersion())[1] >= 27000 then ( -- 2025+
) else ( -- 2023-2024
)
```

---

## 2. Repo layout and deployment

```
Environment/Autodesk/3dsMax/
├── common/                      → %LOCALAPPDATA%\Autodesk\3dsMax\common\
│   └── gstools/                 our tool code, one copy for every Max version
└── <year> - 64bit/ENU/          → %LOCALAPPDATA%\Autodesk\3dsMax\<year> - 64bit\ENU\
    ├── scripts/startup/         auto-run at every Max launch (gs_menu_startup.ms lives here)
    ├── scripts/<vendor>/        third-party tools (NikScripts, PolySmoother)
    ├── usermacros/<folder>/     *.mcr macroScripts, all category:"GSTools"
    └── usericons/
```

### Tool code in `common/`, thin macros per version

Max only reads its own version folder, so anything Max loads by itself has to sit in every
version tree: `.mcr` macros, startup scripts, icons and compiled plugins. Tool code does not.
A macro can load a script from anywhere, so the code lives once in `common/` and each
version's `.mcr` is a thin wrapper that points at it:

```maxscript
-- #userScripts is ...\3dsMax\<year> - 64bit\ENU\scripts; three leaves up is ...\3dsMax
local maxRoot = pathConfig.removePathLeaf (pathConfig.removePathLeaf (pathConfig.removePathLeaf (getDir #userScripts)))
local p = pathConfig.appendPath maxRoot "common\\gstools\\review\\scene_checker\\scene_checker_ui.py"
if doesFileExist p then python.ExecuteFile p
```

The user installer copies the whole `Environment\Autodesk\3dsMax` tree, so `common\` lands
next to the version folders on every machine with no installer change.

Code in `common/` runs on every Max version, so it has to clear all of their bars at once:

- **Python 3.9 floor** (Max 2023). No `match`, and no `X | Y` unions outside annotations
  (inside them they're fine only under `from __future__ import annotations`).
- **No 3.12/3.13-removed stdlib modules** (Max 2027): `imp`, `distutils`, `cgi`, …
- **Qt binding picked by Max version** ([§5](#5-python-and-qt-inside-max)).
- **Never compiled plugins** (`.dlx`, `.dlo`, `.dll`): those are per-version by nature
  ([§6](#6-compiled-and-encrypted-third-party-plugins)) and stay in the version trees.

All our tool code is in `common/` now: `review/scene_checker`, `normals/N00BY_Scripts`
(Custom Normals Tool), `projects/hw3_tools` and `projects/mgp27` (MGP27 Kerb Height
Checker, macro in 2025+ only). The version folders no longer have a `scripts/gstools/`.
New tools go straight into `common/`.

### Python tools in `common/`

Shared helpers live in `common/gstools/_core/`, and a tool reaches them by putting that
folder on `sys.path`, the way Maya's GSPipeline tools reach their `_core`:

- `gs_max.py`: `qt_modules()` (binding by Max version, [§5](#5-python-and-qt-inside-max)),
  `main_window()`, `launch()`, `cm_per_unit()` / `scene_unit()`, and `pref_get()` /
  `pref_set()`, which remember settings in `%LOCALAPPDATA%\Autodesk\3dsMax\gstools_prefs.json`
  for every Max version at once.
- `gs_style.py`: the studio colours. It's a copy of Maya's `_core/gs_style.py`, since the
  two deploy separately, so keep the values in step.

`python.ExecuteFile` runs a file in Max's `__main__`, **one namespace shared by every file
run that way**. A window whose code runs there looks its functions up in `__main__` when
a button is clicked, so a tool opened later can replace them with its own of the same name.
Scene Checker and HW3 Tools both define `_call_ms`, `_ensure_ms`, `_ms_loaded` and
`_MS_PATH`, so they did exactly that. Every Python tool in `common/` ends with:

```python
if __name__ == "__main__":
    gs_max.launch(__file__)
```

`launch()` loads the file again as a module of its own and calls its `show()`, so the window
keeps its own code. The module is loaded fresh on every launch, so a redeployed tool takes
effect without restarting Max. MGP27 Kerb Height Checker
(`common/gstools/projects/mgp27/`) is the reference: Python logic and window in
`kerb_height_checker.py`, with the per-mesh bulk reads and writes in
`kerb_height_checker.ms` so pymxs doesn't cross into MAXScript once per vertex.

### What still lives per version, kept in sync

The `.mcr` wrappers, `gs_menu_startup.ms` and the icons still exist once per version and
must stay **byte-identical across the version folders**. `gs_menu_startup.ms` is written to
run correctly on every version, branching on `maxVersion()` itself.

Workflow: edit the 2025 copy, then copy the changed file into the other version folders.
Don't let a tree drift; per-version forks get out of sync quickly. Once a tool's code is in
`common/`, its `.mcr` only changes if the entry-point path does.

### Deploying

```bat
Deploy\install_server.bat                         :: repo  → \\192.168.1.210\Pipeline\Tool\gs-tool-dcc
Deploy\Autodesk\3dsMax\3dsmax_install_user.bat    :: share → %LOCALAPPDATA%\Autodesk\3dsMax
```

The user installer copies from the **share**, not the working copy. Publish first, or the
machine gets whatever was on the share last time.

### The installer never deletes

Both stages are additive robocopy (`/E /XO`). Renaming or removing a file in the repo does
**not** remove the old one from the share or from artists' machines. This matters most
for macros:

- If a `.mcr` folder is renamed (e.g. `03_Review` → `04_Review`), the old folder stays on
  every machine that installed it. Max loads both, and two macroScripts with the same name
  and category overwrite each other. You don't control which one wins, so an outdated
  copy can replace the current tool.
- Old experiments stay on disk on machines that ever installed them.

When you rename or remove deployed files, also clean the share and tell people to delete
the stale copies from their local folder.

Moving a tool into `common/` leaves its old per-version copy on disk too (for example
`<year> - 64bit\ENU\scripts\gstools\review\scene_checker\`). That one is harmless, since no
macro points at it any more, but delete it when debugging so you aren't reading the wrong
file.

---

## 3. Menus: 2025 replaced the whole menu system

### Symptom

```
CRITICAL ERROR in createGSToolsMenu: -- Unknown property: "getMainMenuBar" in undefined
```

`menuMan` does not exist on 2025+. The name still compiles (see
[§4](#undeclared-names-compile-fine)) and evaluates to `undefined`, so the error only
appears when a property is accessed on it.

### How the 2025+ menu system works

Menus are no longer edited in place. Each time Max loads its menus (at startup, on a
workspace switch, or when the menu editor is reset), it **rebuilds the whole menu tree from
its config** and fires the `#cuiRegisterMenus` callback. Scripts add their items inside that
callback. Nothing a script added survives to the next rebuild, so there is nothing to purge
and no duplicate menus to clean up. The callback runs again on every rebuild.

```maxscript
fn buildMyMenu =
(
    local menuMgr = callbacks.notificationParam()           -- the CuiMenuMgr
    local myMenu = menuMgr.mainMenuBar.CreateSubMenu "<menu-guid>" "GSTools"
    local folder = myMenu.CreateSubMenu "<folder-guid>" "01_General"
    folder.CreateAction "<item-guid>" 647394 "Texel_Density`GSTools"
)
callbacks.removeScripts id:#GSToolsMenu
callbacks.addScript #cuiRegisterMenus buildMyMenu id:#GSToolsMenu
```

The rules:

- **IDs are GUID strings and must never change.** Max saves users' menu customisations
  against these IDs. Give each new menu or item a fresh GUID and leave existing ones alone.
  To generate one: `python -c "import uuid; print(uuid.uuid4())"` or PowerShell
  `[guid]::NewGuid()`.
- **Macro actions use table `647394`**, with the action id ``"MacroName`Category"``: macro
  name first, then a backtick, then the category.
- `CreateSubMenu` returns the new submenu, and works the same on the menu bar and on
  submenus.
- With no `beforeId:`, the new item goes at the end. To insert before an item, pass
  `beforeId:"<id>"`. For example, the Help menu's id is
  `cee8f758-2199-411b-81e7-d3ff4a80d143` (taken from Autodesk's Civil View plugin).
- Call `callbacks.removeScripts id:` before `addScript`. Otherwise running the script twice
  registers the callback twice.
- Registering from `scripts/startup` works on 2025 and 2027. `gs_menu_startup.ms` also
  has a `#postSystemStartup` safety net that
  reloads the menus if the callback never fired. Whether `CuiMenuMgr` is reachable as a
  global outside the callback is unconfirmed; if the log ever says
  `Could not reload menus`, that is the part that failed.
- Methods on the menu manager and on menus (listed from `MenuMan.dll`, see
  [§7](#7-finding-answers-when-the-docs-dont-have-them)):
  - **Menu manager:** `mainMenuBar`, `GetMenuById`, `GetMenuItemById`,
    `CreateTopLevelMenu`, `LoadConfiguration`, `GetCurrentConfiguration`.
  - **Menus:** `CreateSubMenu`, `CreateAction`, `CreateSeparator`, `DeleteItem`, `Move`,
    `isFlat`.
- Quad menus have the matching `#cuiRegisterQuadMenus` callback and a `CuiQuadMenuMgr`.

### Legacy `menuMan` (2023-2024)

Here menus *are* edited in place, and they persist across sessions, so the startup script
has to clean up after previous launches:

- `menuMan.unRegisterMenu` does **not** remove the visible entry from the menu bar. Without
  extra cleanup, every restart adds another "GSTools". Remove the bar entry by position:
  iterate in reverse and re-scan, because positions shift.
- `menuMan.findMenu` returns only the first match, so loop until it returns `undefined`.

### Adding a tool to the GSTools menu

1. Put the tool code under `common/gstools/<area>/<tool>/`. A Python tool uses the
   `_core` helpers and ends with the launch line
   (see [§2](#python-tools-in-common)).
2. Write a thin `.mcr` under `usermacros/<folder>/` with `category:"GSTools"` that loads it
   (see [§2](#tool-code-in-common-thin-macros-per-version)).
3. Add `#("MacroName", "<new guid>")` to the right folder in `gsMenuLayout` in
   `scripts/startup/gs_menu_startup.ms`. A new folder also needs its own GUID.
4. Copy the `.mcr` and `gs_menu_startup.ms` into every version folder.

### Dead end: patching the Qt menu bar from Python

Before the callback approach, we tried adding a `QMenu` directly to
`qtmax.GetQMaxMainWindow().menuBar()` from Python. It does not work: Max recreates the menu
bar, so held references die (`Internal C++ object already deleted`), and anything added is
wiped on the next rebuild. Use `#cuiRegisterMenus`.

---

## 4. MAXScript gotchas

### Reserved keywords cannot be variable names

```
-- MAXScript Auto-load Script Error Exception:
-- Syntax error: at tool, expected name
--  In line:             for tool i
```

`tool` declares a mouse tool, so `for tool in tools` won't parse. The reserved words:

> about, and, animate, as, at, by, case, catch, collect, continue, coordsys, do, else,
> exit, fn, for, from, function, global, if, in, local, macroscript, mapped, max, not, of,
> off, on, or, parameters, persistent, plugin, rcmenu, return, rollout, set, struct, then,
> throw, to, tool, try, undo, utility, when, where, while, with

The easy ones to trip on as variable names are `tool`, `set`, `max`, `on`, `off`, `at`,
`from`, `to`, `by`, `of`, `where`, `when`, `with`, `undo`, `collect` and `rollout`.

**A syntax error anywhere in a startup script stops the whole file.** None of it runs,
including the parts before the error. For the menu script, that means no menu at all.

### Undeclared names compile fine

Referencing a global that doesn't exist (like `menuMan` on 2025) is not a compile error. It
evaluates to `undefined` at runtime, and the failure only shows up when you call a method or
read a property on it:

```
Unknown property: "<something>" in undefined
```

When you see that message after a version upgrade, first check whether the interface or
global still exists in that version.

### Macros can't rely on startup-script globals

A macro body should not depend on globals that a startup script defines, because macros and
startup scripts load at different points during startup. Our macros resolve their own
paths, from `getDir #userScripts` (the pattern is in
[§2](#tool-code-in-common-thin-macros-per-version)).

### Startup scripts run once

Editing a deployed startup script has no effect until Max restarts, or until you `fileIn`
it from the Listener. On 2025+, re-running the menu script only re-registers the callback.
The menu itself doesn't change until Max reloads its menus; switching workspaces triggers
a reload.

---

## 5. Python and Qt inside Max

### Pick the Qt binding by Max version, not by what imports

A stray PySide6 can be importable inside **Max 2023**, even though Max itself runs
PySide2. A `try: import PySide6 / except: import PySide2` shim then loads the wrong
binding. Parenting a PySide6 dialog to Max's PySide2 main window crashes with
`wrong argument types`.

Choose by Python version, which tracks the Max version:

```python
if sys.version_info >= (3, 11):      # Max 2025+  → PySide6
    from PySide6 import QtWidgets, QtCore, QtGui
else:                                # Max 2023   → PySide2
    from PySide2 import QtWidgets, QtCore, QtGui
```

The shared implementation is `qt_modules()` in `common/gstools/_core/gs_max.py`, which
returns `(QtWidgets, QtCore, QtGui)`. Every Python tool in `common/` gets its binding from
it.

This is the opposite of the Maya rule (where the repo branches on the import); see
[CLAUDE.md](../CLAUDE.md).

Other notes:

- Parent tool windows to `qtmax.GetQMaxMainWindow()`.
- Import `pymxs` inside the functions that use it, not at module top level, so the UI
  module can still be imported outside Max.
- **2027 ships Python 3.13.** The `>= (3, 11)` gate still picks PySide6. But modules
  removed from the standard library in 3.12 and 3.13 (`imp`, `distutils`, `cgi`, `pipes`,
  `telnetlib`, …) no longer exist, so older helper code that imports them will fail.

---

## 6. Compiled and encrypted third-party plugins

- **`.dlx` / `.dlo` / `.dlm` / `.gup` / plugin `.dll` files are built for one Max major
  version.** Copying them into another version's folder doesn't make them work there.
  NikScripts UVTools ships only `extension/2023/nikUvMxsExtension_2023x64.dlx`, and that
  same file sits in the 2025-2027 folders. `PolySmoother/polysmoother.dll` has the same
  question. Neither has been checked on 2025+. If one of these tools misbehaves on a newer
  Max, look for a vendor build for that version first.
- **`.mse` is encrypted MAXScript.** It cannot be read or edited. Fixes mean getting an
  updated version from the vendor.

---

## 7. Finding answers when the docs don't have them

No offline MAXScript help is installed (the install's `help/` folder has no help files), and the
online docs for newer APIs are thin. These sources were more reliable:

- **Autodesk's own scripts shipped with Max.** Search the install for the API name:

  ```bash
  grep -rl cuiRegisterMenus "/c/Program Files/Autodesk/3ds Max 2025"
  ```

  `ApplicationPlugins/CivilViewIO/scripts/CivilView.Plugins.ms` was the only working
  example of the 2025 menu API anywhere.

- **The DLLs themselves.** Names of interfaces exposed to MAXScript are stored as UTF-16
  strings inside the DLLs. `strings` ships with Git Bash:

  ```bash
  strings -el "/c/Program Files/Autodesk/3ds Max 2025/MenuMan.dll" | less
  ```

- **Every callback event name** is listed in
  `scripts/PythonSamples/Python3/pymxs/notifications.py` in the install.
- **In a running Max, from the Listener:** `apropos "menu"` lists matching globals.
  `showInterfaces <obj>`, `showMethods <obj>` and `showProperties <obj>` list what an
  object actually exposes. Inside a callback, run them on
  `callbacks.notificationParam()`.

When the docs and the running application disagree, the running application is right.

---

## 8. Testing a change

Edit the repo, publish, install, then test in real Max. Startup-script errors appear as a
*MAXScript Auto-load Script Error* popup and in the MAXScript Listener. Our scripts log
lines prefixed with `[GSTools]`. Test on every version folder you changed. A change that
works on 2023 says nothing about 2025+, and the reverse is also true.
