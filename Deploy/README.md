# Deploy/

The batch scripts that move the [`Environment/`](../Environment/) payload around.
Everything here is a thin wrapper over one shared engine, [`_core/install_core.bat`](_core/install_core.bat).

## Files

```
Deploy/
├── install_server.bat                        publish whole repo → Pipeline share
├── _core/
│   └── install_core.bat                      the shared robocopy engine
├── Autodesk/
│   ├── Maya/maya_install_user.bat            server → %USERPROFILE%\Documents\maya
│   └── 3dsMax/3dsmax_install_user.bat        server → %USERPROFILE%\AppData\Local\Autodesk\3dsMax
├── Blender/blender_install_user.bat          server → %USERPROFILE%\AppData\Roaming\Blender Foundation\Blender
└── Adobe/
    └── SubstancePainter/substance_install_user.bat  → %USERPROFILE%\Documents\Adobe\Adobe Substance 3D Painter
```

## How it works

`install_core.bat` takes two arguments — a **source subpath** under the repo root and a
**destination directory** — and robocopies one into the other:

```bat
call "<path>\_core\install_core.bat" "Environment\Autodesk\Maya" "%USERPROFILE%\Documents\maya"
```

It finds the repo root itself by walking *up* from its own location until it hits a folder
containing an `Environment/` subfolder, so wrappers never hard-code a depth to the root.
The copy uses `robocopy /E /XO` (all subdirs, skip files older than dest) — one-way,
additive, safe to re-run. robocopy exit codes 0–7 are treated as success; ≥8 is a failure.

Each per-DCC wrapper just supplies its two arguments and forwards the exit code.

## The one thing to get right: the `..\` count to `_core`

A wrapper reaches the shared engine relative to **its own** folder via `%~dp0`. The number
of `..\` must climb back up to `Deploy\` (where `_core` lives) — no more, no less:

| Wrapper                                | Depth below `Deploy\` | Correct prefix     |
| -------------------------------------- | --------------------- | ------------------ |
| `Blender\blender_install_user.bat`     | 1                     | `..\_core\`        |
| `Autodesk\Maya\maya_install_user.bat`  | 2                     | `..\..\_core\`     |
| `Autodesk\3dsMax\3dsmax_install_user.bat` | 2                  | `..\..\_core\`     |
| `Adobe\SubstancePainter\substance_install_user.bat` | 2        | `..\..\_core\`     |

If the count is wrong, `call` resolves to a path that doesn't exist and the installer fails
silently with a nonzero exit code (no visible sync happens). This is exactly the bug that
was in the Substance Painter wrapper: it sat two levels deep (`Adobe\SubstancePainter\`) but
used a single `..\`, resolving to the nonexistent `Deploy\Adobe\_core\`. Fixed by using
`..\..\_core\`.

**When adding a new DCC:** place its wrapper, count how many folders deep it is below
`Deploy\`, and use that many `..\` before `_core\`.

## Publishing to the server

`install_server.bat` calls the same engine with source `"\"` (the whole repo root) and
destination `\\192.168.1.210\Pipeline\Tool\gs-tool-dcc`. Run it after changes are ready to
ship; the per-user installers pull from that share on login.
