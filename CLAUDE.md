# CLAUDE.md — working rules for this repo

Read this before touching anything under [`Environment/`](Environment/). It covers the two
things that are *not* visible from the code: **which Maya versions actually matter**, and
**how changes get verified**.

For what the repo *is* and how it deploys, see [README.md](README.md) and
[Deploy/README.md](Deploy/README.md).

---

## 1. The studio runs Maya 2022 and Maya 2026. Only those two.

| Version | Python | Qt binding            | Status                       |
| ------- | ------ | --------------------- | ---------------------------- |
| 2022    | 3.7    | PySide2 / shiboken2   | **In production**            |
| 2026    | 3.11   | PySide6 / shiboken6   | **In production**            |
| 2023 / 2024 / 2025 / 2027 | — | — | Folders exist; nobody runs them |

`Environment/Autodesk/Maya/2023|2024|2025|2027/` are leftovers and forward-looking stubs.
Do not let them drive a design decision, do not spend effort keeping them working, and do
not add "but 2024 needs…" branches. They are not deleted, just inert.

**Every change must run on both 2022 and 2026.** That is the whole compatibility matrix.
Practically it means the code has to clear the *older* bar (Python 3.7) and the *newer*
bar (PySide6, no PyMEL) at the same time.

### Python 3.7 floor (because of 2022)

Do not use, even though 2026 would accept it:

- walrus `:=` (3.8)
- positional-only params `/` (3.8)
- `dict | dict` merge (3.9)
- `str.removeprefix` / `str.removesuffix` (3.9)
- builtin generics in annotations, `list[str]` / `dict[str, int]` (3.9)
- `match` statements (3.10)
- `X | Y` union syntax in annotations (3.10)

f-strings, dataclasses and `typing.List[...]` are fine.

### Qt: branch on the import, not on the version number

The house pattern, as used in
[gs_mirror/ui.py](Environment/Autodesk/Maya/scripts/GSTools/common/scripts/tools/modeling/gs_mirror/ui.py):

```python
try:                                    # Maya 2025+
    from PySide6 import QtCore, QtWidgets
    from shiboken6 import wrapInstance
    QT_BINDING = "PySide6"
except ImportError:                     # Maya 2022-2024
    from PySide2 import QtCore, QtWidgets
    from shiboken2 import wrapInstance
    QT_BINDING = "PySide2"
```

Watch the usual PySide6 breakages: `exec_()` → `exec()`, `QAction` moved from `QtWidgets`
to `QtGui`, `QApplication.desktop()` is gone, and enums are properly scoped
(`QtCore.Qt.AlignmentFlag.AlignLeft`, though the short spelling still resolves).

> Note: 3ds Max is the opposite case — there the binding must be picked by *Max version*,
> not by import availability, because a stray PySide6 in Max 2023 crashes `qtmax` parenting.
> That rule does not apply to Maya.

---

## 2. No PyMEL. Ever, in new code.

PyMEL does not ship with Maya 2026. **Never `import pymel` in new or edited code.** Use:

- `maya.cmds` for commands
- `maya.api.OpenMaya` (om2) for anything that needs real API access
- `maya.mel.eval` only when there is genuinely no `cmds` equivalent

### Existing PyMEL call sites

Around 20 files still import PyMEL. They are **broken on 2026** whether or not anyone has
hit it yet. When you are already editing one of these files, port it off PyMEL as part of
the work. Do not open a sweeping PyMEL-removal campaign unasked.

Current offenders (`grep -rl pymel Environment/Autodesk/Maya --include=*.py`):

```
GSPipeline/01_Modeling/Speed_Workflow/Speed_Workflow_UI.py
GSPipeline/01_Modeling/Vertex_Painter_UI.py
GSPipeline/05_Projects/GSW/gsw_vehicle_tools/uv_atlas.py
GSPipeline/05_Projects/HW3/HW3_Asset_Validation_UI.py
GSPipeline/05_Projects/MGP25/Mgp25_Asset_Checker_UI.py
GSPipeline/05_Projects/MGP25/Mgp25_Custom_Parts_Rigger_UI.py
GSPipeline/05_Projects/MGP25/Mgp25_Ultimate_Bike_Riggator_UI.py
GSPipeline/05_Projects/MGP26/MGP26_Asset_Checker_UI.py
GSPipeline/05_Projects/MGP26/MGP26_Ultimate_Bike_Riggator_UI.py
GSPipeline/05_Projects/R6/R6_Asset_Validation_UI.py
GSPipeline/05_Projects/SCR1/Scr1_Asset_Validation_UI.py
GSPipeline/_core/gs_fbx.py
GSTools/common/scripts/tools/baking/rename.py
GSTools/common/scripts/tools/modeling/set_length_edge.py
GSTools/common/scripts/tools/rigging/SkinSaverDeluxe.py
GSTools/common/scripts/tools/utilities/GS_path_manager.py
GSTools/common/scripts/tools/uv/RizomUV_tool.py
GSTools/common/scripts/vendor/nitropoly/NitroPoly.py   (handled by the shim below)
```

### Two porting patterns, both already in the repo

1. **Rewrite to cmds/om2** — the default. See commit `a6301b8` (`GS_File_Export_UI.py`).
2. **Shim, for large vendored third-party code not worth rewriting.** See
   [pymel_nitro.py](Environment/Autodesk/Maya/scripts/GSTools/common/scripts/vendor/nitropoly/pymel_nitro.py):
   a PyMEL-shaped facade over cmds + om2 covering exactly the slice NitroPoly uses. The key
   rule baked into it — **the shim is used on every Maya version and never falls back to
   real PyMEL even where PyMEL exists**, so the path artists exercise daily is the same path
   that ships to 2026.

Reach for the shim only when a rewrite would mean touching thousands of lines of code that
isn't ours.

---

## 3. How work gets verified: deploy, don't simulate

**Do not launch Maya. Do not run `mayapy`. Do not build scene-generating test harnesses to
prove a change works.** `mayapy` for 2022 and 2026 is installed on this machine, and it is
deliberately not the loop we use: it burns a lot of time, it cannot exercise the UI (no
`QApplication` under `mayapy`), and it proves less than thirty seconds in the real
application does.

The actual loop is:

```
edit under Environment/  →  deploy  →  Sonny tests in real Maya  →  reports what broke  →  fix
```

So: **make the change, say what you changed and what to look at, then stop.** Finishing with
"implemented — ready to test on your end" is a complete and correct way to end a task here.
The person running the tool finds the bug faster and more accurately than any harness you
can write.

### What verification *is* appropriate

- Read the surrounding code properly before editing. Most bugs here are a wrong flag or a
  wrong assumption about a `cmds` signature, and reading catches those.
- Syntax-check when a file is large or heavily edited: `python -m py_compile <file>` — cheap,
  catches typos, no Maya needed. It validates *syntax* against the local interpreter, not
  3.7 compatibility; for that, check the 3.7 floor list above by eye.
- Confirm `cmds` flag names against the Maya docs or the local `Maya20XX/scripts` MEL
  sources instead of guessing. Flags and signatures do drift between versions, and the
  docs are occasionally wrong about API behaviour — the runtime wins.

### Deploying for a test

```bat
Deploy\install_server.bat                      :: repo  → \\192.168.1.210\Pipeline\Tool\gs-tool-dcc
Deploy\Autodesk\Maya\maya_install_user.bat     :: share → %USERPROFILE%\Documents\maya
```

The user installer pulls from the **share**, not from this working copy, so publish first or
the test runs against stale files. Both stages are additive robocopy (`/E /XO`) and safe to
re-run. For a tighter loop, point Maya's script paths straight at the working copy instead.

---

## 4. Conventions worth knowing

- **Where things live.** `GSTools/` = artist tools (shelves, modeling/UV/rigging utilities).
  `GSPipeline/` = pipeline menu and project tools, numbered by department stage
  (`01_Modeling`, `03_Files_IO`, `04_Review`, `05_Projects/<PROJECT>`). Shared helpers go in
  `_core/` or `common/`, never copy-pasted between tools.
- **Version-agnostic by default.** Tool code lives in the version-less `scripts/` tree and is
  shared by every Maya version; only `Maya.env` and `prefs` are per-version. Keep it that
  way — don't fork a tool per Maya version to dodge a compatibility problem, fix the
  compatibility problem.
- **Stray `.pyc` files** are committed in a couple of `__pycache__/` folders. Ignore them;
  they are not source.
- **Prefer the clean structural fix** over a runtime workaround. If the clean fix is bigger
  than what was asked, say so plainly — scoping down is the user's call — but lead with the
  right design.
- **Explicit instruction beats repo precedent.** If asked to delete, change or replace
  something specific, do it; don't go researching prior art first.
