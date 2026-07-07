# gs-tool-dcc

GlendaStudio's DCC (Digital Content Creation) tooling — the Python/MEL/MaxScript
scripts, plugins, shelves and configs that get deployed into artists' Maya, 3ds Max,
Blender and Substance Painter installs.

The repo is split into two halves:

| Folder          | Role                                                                 |
| --------------- | -------------------------------------------------------------------- |
| [`Environment/`](Environment/) | **The payload.** Mirrors each DCC's real user-config folder layout. This is what ends up on an artist's machine. |
| [`Deploy/`](Deploy/)      | **The machinery.** Batch scripts that copy the payload to the server and from the server into each user's profile. See [Deploy/README.md](Deploy/README.md). |

---

## The deployment flow

```
   this repo (dev machine)
        │
        │  Deploy/install_server.bat        (run once by an admin, on change)
        ▼
   \\192.168.1.210\Pipeline\Tool\gs-tool-dcc   (the "server" / Pipeline share)
        │
        │  Deploy/<DCC>/<dcc>_install_user.bat  (run on each artist login by the
        ▼                                        domain controller)
   %USERPROFILE%\...   (the artist's Maya / Max / Blender / Substance folders)
```

Two stages, both one-way additive [robocopy](https://learn.microsoft.com/windows-server/administration/windows-commands/robocopy) syncs (newer/missing files only, existing personal files untouched):

1. **Publish to server** — `Deploy/install_server.bat` copies the *entire repo* to the
   Pipeline share. An admin runs this after changes are ready to ship.
2. **Install to user** — the per-DCC `*_install_user.bat` wrappers copy the relevant
   `Environment/<DCC>` subtree from the share into the matching folder in the user's
   profile. These run automatically on login (pushed by the domain controller).

Because both stages skip older/identical files, they are safe to re-run and safe to
merge into folders that also contain an artist's own files.

---

## `Environment/` layout

Each subtree is shaped like the destination it installs into, so the copy is a
straight mirror — no path rewriting at install time.

```
Environment/
├── Autodesk/
│   ├── Maya/                         → %USERPROFILE%\Documents\maya
│   │   ├── 2022/ 2023/ 2024/ 2025/   per-version prefs (Maya.env, modules, scripts)
│   │   ├── scripts/                  shared across versions
│   │   │   ├── userSetup.py          bootstrap: runs on Maya startup
│   │   │   ├── GSTools/              artist tools (shelves, icons, mel/py)
│   │   │   ├── GSPipeline/           pipeline menu + project tools
│   │   │   └── launcher_config.ini   user type / project / dev-user config
│   │   └── plug-ins/                 e.g. gsNormalApiUndo.py
│   └── 3dsMax/
│       ├── 2023 - 64bit/ENU/         → %USERPROFILE%\AppData\Local\Autodesk\3dsMax\...
│       └── 2025 - 64bit/ENU/         scripts, usermacros, usericons, startup
├── Blender/                          → %USERPROFILE%\AppData\Roaming\Blender Foundation\Blender
│   ├── 3.6/ 4.2/ 4.5/                per-version scripts
│   └── common/scripts/addons/        GS_* addons shared across versions
└── Adobe/
    └── SubstancePainter/             → %USERPROFILE%\Documents\Adobe\Adobe Substance 3D Painter
        ├── python/plugins/           MGP_Exporter, Material_Manager, GS_Pipeline_Menu
        ├── python/modules/gs_utils/  shared helpers (export, baking, project info)
        └── assets/effects/           GS_PBR_Validator .sbsar variants
```

### How each DCC finds the tools at runtime

- **Maya** — `Maya.env` (per version) points `GSTOOLS`, `GSPIPELINE`, `MAYA_PLUG_IN_PATH`,
  `XBMLANGPATH`, `MAYA_SHELF_PATH` at the installed folders; `scripts/userSetup.py` runs on
  startup and wires up the pipeline menu.
- **3ds Max** — scripts/macros drop into the version's `ENU` tree; `startup/` scripts
  auto-run.
- **Blender** — addons live under the version `scripts/addons` and `common/scripts/addons`.
- **Substance Painter** — Painter auto-loads everything under its `python/plugins` folder
  on launch.

---

## Working on the tools

Edit files under `Environment/`. To test on your own machine you can run the relevant
`Deploy/<DCC>/<dcc>_install_user.bat` (it will pull from the *server*, so publish first
with `install_server.bat` if you want your local edits picked up), or point the DCC at
your working copy directly.

See [Deploy/README.md](Deploy/README.md) for how the installers are wired.
