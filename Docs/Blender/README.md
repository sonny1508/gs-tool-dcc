# Blender at Glenda Studio

Start here for any Blender work in this repo. This page covers which Blender versions
matter, how the repo reaches an artist's Blender, and how a change gets checked. The other
pages go deeper:

| Page                                       | Read it when you are                                                |
| ------------------------------------------ | ------------------------------------------------------------------- |
| [GS_Pipeline.md](GS_Pipeline.md)           | touching the GS Pipeline add-on at all: layout, the panel, adding a project, tool or tab, performance rules |
| [Asset_Validation.md](Asset_Validation.md) | working on Review > Asset Validation: checks, fixes, the Log        |
| [API_Notes.md](API_Notes.md)               | writing `bpy` code: what differs across 3.6 / 4.5 / 5.2, and API behaviour that has caught us out |
| [checks/](checks/)                         | done moving code around: two scripts that check a refactor without opening Blender |

Everything here was checked against the Blender builds installed on the dev machine
(`C:\Program Files\Blender Foundation\Blender <version>\`) or tested by Sonny in a
running Blender. Where something is believed but not confirmed, the page says so.

**Contents**

1. [Versions](#1-versions)
2. [Repo layout and how it reaches Blender](#2-repo-layout-and-how-it-reaches-blender)
3. [Deploying](#3-deploying)
4. [How a change gets checked](#4-how-a-change-gets-checked)
5. [Working conventions](#5-working-conventions)

---

## 1. Versions

| Blender | Python | Repo folder               | Notes                                                        |
| ------- | ------ | ------------------------- | ------------------------------------------------------------ |
| 3.6     | 3.10   | `Environment/Blender/3.6` | Main install; carries HOps, MESHmachine, ZenUV and other third-party add-ons. No extensions platform. Old auto smooth (a mesh setting). |
| 4.5     | 3.11   | `Environment/Blender/4.5` | Extensions platform (4.2+). Auto smooth is a modifier (4.1+). FBX exporter can write 3ds Max smoothing groups. |
| 5.2     | 3.13   | `Environment/Blender/5.2` | As 4.5.                                                      |

Blender 4.2 is also installed on the dev machine but is not deployed; ignore it.

**Every change to shared code must run on all three.** The Python floor is 3.10 (from
3.6). The add-on's `bl_info` says `"blender": (3, 6, 10)`.

The dev machine's own `python` is 3.9. That is fine for `py_compile`, but syntax newer than
3.9 that Blender accepts (e.g. `match`) will fail there even though it is valid in Blender.

---

## 2. Repo layout and how it reaches Blender

```
Environment/Blender/
├── common/scripts/                   shared by every version (registered as a script directory)
│   ├── addons/
│   │   ├── GS_Pipeline/              the studio's main add-on: see GS_Pipeline.md
│   │   ├── GS_Texture_Validator/
│   │   ├── GS_Camera_PNP/, Global_Material_List/, uvpackmaster3/
│   └── gs_pipeline_core/             launch-time setup, one copy for every version
│       ├── __init__.py
│       └── extensions_policy.py      4.2+ extensions repo / offline proxy policy
├── 3.6/
│   ├── config/startup.blend
│   └── scripts/
│       ├── addons/                   3.6-only third-party add-ons (HOps, MESHmachine, ZenUV, ...)
│       └── startup/gs_pipeline/      thin per-version shim
├── 4.5/scripts/startup/gs_pipeline/
└── 5.2/scripts/startup/gs_pipeline/
```

Deployed to `%APPDATA%\Blender Foundation\Blender\` (so `3.6\`, `4.5\`, `5.2\` and
`common\` sit side by side there).

### The launch chain

1. Blender auto-runs `<version>/scripts/startup/gs_pipeline/__init__.py`. That shim only
   puts `common/scripts` on `sys.path` and calls `gs_pipeline_core.register()`. **Don't
   put logic in the shims**; edit `gs_pipeline_core`.
2. `gs_pipeline_core`, once per launch:
   - enforces the extensions policy (4.2+; no-op on 3.6). Studio workstations have no
     internet; the policy points Blender's `blender_org` repository at the studio proxy
     when it is reachable, at extensions.blender.org otherwise.
   - registers `common/scripts` as a script directory named `GSTools_Common`, so Blender
     finds the shared add-ons,
   - force-disables retired add-ons (`COMMON_FORCE_DISABLE`), then enables the default ones
     (`COMMON_AUTO_ENABLE`: GS_Pipeline, GS_Texture_Validator, s4_env_tools,
     s4_vehicle_tools),
   - saves preferences only if something changed.

So: a new shared add-on goes in `common/scripts/addons/` and, if it should be on for
everyone, into `COMMON_AUTO_ENABLE`. An add-on merged into another (as GS_Asset_Validation
was merged into GS Pipeline) goes into `COMMON_FORCE_DISABLE`, because its folder stays on
artists' machines (next section).

---

## 3. Deploying

```bat
Deploy\install_server.bat                  :: repo  -> \\192.168.1.210\Pipeline\Tool\gs-tool-dcc
Deploy\Blender\blender_install_user.bat    :: share -> %APPDATA%\Blender Foundation\Blender
```

The user installer pulls from the **share**, so publish first. Both stages are an
**additive** robocopy (`/E`, newer or missing files only, `__pycache__` excluded). See
[Deploy/README.md](../../Deploy/README.md).

**The installer never deletes.** Renaming or moving a module leaves the old file on every
machine. That is harmless only while:

- nothing imports the old file, and
- no new module or package takes the old file's name (a package `foo/` next to a stale
  `foo.py` is a trap). Pick new names when you move code.

Leftovers on artists' machines right now, all unimported and harmless: from the 2026-10
GS Pipeline restructure, `projects/hw3_tools.py`, `projects/mgp27_tools.py`,
`file_io/gs_file_transfer.py` and `projects/hw3/modelling.py` (renamed `modeling.py`); the
old standalone `GS_Asset_Validation` add-on (force-disabled at launch).

---

## 4. How a change gets checked

Same rule as for Maya ([CLAUDE.md](../../CLAUDE.md) section 3): **don't launch Blender to
test a change, and don't build test scenes.** The loop is:

```
edit under Environment/  ->  deploy  ->  Sonny tests in real Blender  ->  reports  ->  fix
```

Ending a task with "implemented, ready to test on your end", plus what to look at, is
complete and correct.

What *is* worth doing without Blender:

- Read the surrounding code properly. Most bugs are a wrong assumption about a `bpy` call.
- `python -m compileall -q <folder>` for syntax.
- After moving or splitting modules, run the two scripts in [checks/](checks/). One finds
  undefined and unused names; the other imports the whole add-on against a stand-in `bpy`
  and runs register / unregister. Neither tests behaviour.
- Confirm API details against the installed Blender's own Python, not memory:
  - `...\Blender <v>\<v>\scripts\startup\bl_ui\` holds Blender's own panels. It is the
    best answer to "what does the Geometry Data panel check?" and "does 3.6 accept this
    `template_list` keyword?".
  - `...\Blender <v>\<v>\scripts\modules\bpy\` holds `bpy.ops` and friends.
  - `...\Blender <v>\<v>\python\bin\python.exe --version` gives the bundled Python.
- If a Blender MCP server is connected, its `search_api_docs` / `get_python_api_docs` tools
  read the bundled API reference without touching the running scene.

When the docs and the running application disagree, the running application is right.

---

## 5. Working conventions

These come from working with Sonny; the repo-wide ones are in [CLAUDE.md](../../CLAUDE.md)
section 4.

- **Tools are for artists.** Window text is the result and what to do next: "Removed 3
  vertex groups.", "SM_Door_L has n-gons.". No timings, no developer detail. Tooltips are
  one or two short lines.
- **Settings are grouped in boxes**, related values sharing a row. Blender can't fix a
  minimum sidebar width, so layouts adapt to the width they get (`common.is_wide`).
- **Blender buttons can't be coloured.** The studio red / orange primary buttons from the
  Maya and Max tools don't carry over. Use large plain buttons, and the log's icons for
  result levels.
- **Checks report; selecting is opt-in.** A check lists the objects with the problem.
  Selecting their faces is a button the artist presses (see Asset_Validation.md).
- **Long lists scroll.** A list that can grow (objects in a log) is a scrolling `UIList`,
  never capped with "...and 30 more".
- **Lead with the structural fix** over a runtime workaround; say plainly if it is bigger
  than what was asked.
- **An explicit instruction beats repo precedent.** Told to delete or change something
  specific: look at what it is, then do it.
