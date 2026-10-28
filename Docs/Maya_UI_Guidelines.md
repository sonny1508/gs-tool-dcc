# Maya tool UI guidelines

How a GSTools / GSPipeline window should look and behave. Most in-house tools already
share one look: Maya's own palette, group boxes, short labels, a log at the bottom. Tools
brought in from outside often don't, and they stand out. This page writes that shared look
down, so new tools match it and imported tools have something to be brought in line with.

Reference implementations, in order of how closely they follow this page:

- [MGP27_Kerb_Height_Checker_UI.py](../Environment/Autodesk/Maya/scripts/GSPipeline/Projects/MGP27/MGP27_Kerb_Height_Checker_UI.py): settings grouped by category, two actions, short log, fixed size
- [gs_mirror/ui.py](../Environment/Autodesk/Maya/scripts/GSTools/common/scripts/tools/modeling/gs_mirror/ui.py): small fixed-size window with a status line
- [gs_file_export.py](../Environment/Autodesk/Maya/scripts/GSPipeline/Files_IO/gs_file_export.py): settings, two actions, log, remembered settings (but resizable; see §9)
- [gs_cleanup/ui.py](../Environment/Autodesk/Maya/scripts/GSTools/common/scripts/tools/utilities/gs_cleanup/ui.py): sections over one shared status line

**Contents**

1. [Principles](#1-principles)
2. [Window](#2-window)
3. [Layout](#3-layout)
4. [Colour](#4-colour)
5. [Text](#5-text)
6. [Behaviour](#6-behaviour)
7. [Code layout](#7-code-layout)
8. [Bringing in an outside tool](#8-bringing-in-an-outside-tool)
9. [Tools that don't follow this yet](#9-tools-that-dont-follow-this-yet)

---

## 1. Principles

- **Write for artists, not developers.** Say what happened and what to do next, in as few
  words as that takes. Timings, mesh counts, per-item lists and how the tool works inside
  are for developers. Those go in the code, or in the Script Editor when something breaks.
- **Look like Maya.** Use Maya's Qt palette and fonts as they are. A tool should read as part
  of Maya, not as an app running inside it.
- **Keep colour to the studio scheme.** Primary action buttons get the studio red and orange,
  and log text gets the three status colours. Everything else is Maya's own palette.
- **Group settings by what they're for.** Each category gets its own box, and related values
  share a row. Don't stack every setting in one long column.
- **Keep the window a fixed size.** It opens at the size its content needs and stays that
  size.
- **Report in the window, not in pop-ups.** Results go to a log or status line. A dialog
  only appears when the tool needs an answer.
- **Make every action one undo step.**

## 2. Window

New windows are PySide `QDialog`s, using the Qt import pattern in
[CLAUDE.md](../CLAUDE.md#qt-branch-on-the-import-not-on-the-version-number):

```python
OBJECT_NAME = "GSExampleWindow"


def _maya_main_window():
    pointer = omui.MQtUtil.mainWindow()
    return wrapInstance(int(pointer), QtWidgets.QWidget)


class ExampleWindow(QtWidgets.QDialog):

    # Fixed size: at least this wide, wider if the content needs it.
    MIN_WIDTH = 420

    def __init__(self, parent=None):
        super(ExampleWindow, self).__init__(parent or _maya_main_window())
        self.setObjectName(OBJECT_NAME)
        self.setWindowTitle("GS Example")
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.Tool)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setSizeGripEnabled(False)
        self._build()
        self._lock_size()

    def _lock_size(self):
        self.layout().activate()
        self.setFixedWidth(max(self.MIN_WIDTH, self.sizeHint().width()))
        self.setFixedHeight(self.sizeHint().height())


def show():
    for widget in _maya_main_window().findChildren(QtWidgets.QDialog, OBJECT_NAME):
        widget.close()
        widget.deleteLater()
    window = ExampleWindow()
    window.show()
    return window
```

- **Title.** Use the plain tool name: `GS <Name>` for studio tools, `<PROJECT> <Name>` for
  project tools (`MGP27 Kerb Height Checker`). A version is optional; if you add one, use the
  form `v1.2.0`.
- **Size.** Windows are fixed-size: lock them to their laid-out content, as above. If a
  status line wraps onto more lines, call `_lock_size()` again (gs_mirror does this). Only
  make a window resizable when its content uses the room, such as a long list or tree the
  artist scrolls through (Model Checker, GS Clean Up). A log isn't a reason to make a window
  resizable; give it a fixed height instead.
- **Width.** Make the window wide enough to put related values side by side (§3). 420–520 is
  typical. With two-column settings the columns set the width, so lock the window to
  `sizeHint()` with no `MIN_WIDTH` on top. Any spare width would push the second column off
  centre.
- **Spacing.** Root margins 10. 8 between boxes, 6–12 between controls.
- **`maya.cmds` windows** are fine for a small single-purpose tool (UV Shell Scaler, GS Normal
  Tools). Make them `sizeable=False`, and everything below still applies: `frameLayout`
  labels are the group titles, and buttons get no `backgroundColor`.

## 3. Layout

Lay the window out top to bottom: **settings → actions → output**.

```
            first column                │           second column
┌ Axis & Selection ─────────────────────┼──────────────────────────┐
│ Up Axis:      (•) Z  ( ) Y            │ Select:       [x] Too High  [x] Too Low │
└───────────────────────────────────────┼──────────────────────────┘
┌ Kerb Spec ────────────────────────────┼──────────────────────────┐
│ Height:       [ 2.00 cm ]             │ Tolerance:    [ ± 0.050 cm ]   │
└───────────────────────────────────────┼──────────────────────────┘
┌ Search ───────────────────────────────┼──────────────────────────┐
│ Radius:       [ 15.0 cm ]             │ Ignore Under: [ 0.20 cm ]      │
│               [ ] Measure along the ground                       │
└───────────────────────────────────────┼──────────────────────────┘
                                   middle of the window
[       Check Selection       ] [        Fix Selected        ]
┌ Log ────────────────────────────────────────────────────┐
│ Checked 38 vertices, Z up.                                       │
│ 38 too high - selected.                                          │
└─────────────────────────────────────────────────────────┘
```

- **One group box per category.** Title it with a short Title Case noun: *Kerb Spec*,
  *Search*, *Export*, *Log*. Don't number the boxes ("1. Search & Spatial Parameters"), use
  ALL CAPS, or add a banner or subtitle line at the top of the window. Remember that `&` in a
  `QGroupBox` title has to be written `&&`.
- **Put the most important settings at the top** (or bottom) edge, not buried in the middle.
  These are the ones that change what the action means, such as the up axis or what gets
  selected.
- **Lay settings out in two equal columns**, one label / field pair in each. Values that
  belong together share a row (*Height* and *Tolerance*). An option that qualifies a value
  sits under it, lined up with the fields (*Measure along the ground* under *Radius*).
  Labels are left-aligned, Title Case, and end in a colon.
- **The second column starts at the middle of the window, in every box.** Fix both columns
  to the same width: the longest label, plus the widest field, plus a gap of about 24 px.
  Make the window exactly two columns wide, so there's no spare width left over to push the
  second column off centre. Fix every label to the longest label's width, so the fields
  start on one line in both columns. These go wrong:
  - right-aligned labels, because each label in the second column then starts wherever its
    text length puts it
  - letting each box size its own columns, because the boxes drift apart
  - sizing the second column to its content, because it then starts just after the first
    pair instead of mid-window

  The kerb checker's `_add_row()` / `_align_columns()` do this.
- **Measure after polishing.** Maya's style sheet only reaches a widget when it's polished,
  and it changes the widget's size. Call `self.ensurePolished()` before reading any
  `sizeHint()` to lay things out, or the numbers will be for the unstyled widget.
- **A `QFormLayout`** (one setting per row) is fine for a few settings with no categories,
  such as GS File Export's three.
- **Numbers** use `QDoubleSpinBox` / `QSpinBox` with the unit as a suffix (`" cm"`). Use a
  slider only when dragging the value and watching the result live is the point (LOD
  Checker's translate).
- **Choices.** Two or three options are radio buttons in one row. More than that is a
  `QComboBox`. An on/off option is a `QCheckBox` whose label says what *on* does.
- **Primary actions** are bold, at least 36 px tall, filled with a studio colour (§4), and
  sit side by side in equal columns:

  ```python
  @staticmethod
  def _big_button(text, tooltip):
      button = QtWidgets.QPushButton(text)
      button.setToolTip(tooltip)
      button.setMinimumHeight(36)
      font = button.font()
      font.setBold(True)
      button.setFont(font)
      return button

  check_button = self._big_button("Check Selection", "...")
  gs_style.style_button(check_button, gs_style.STUDIO_RED)
  ```

  Secondary actions (Browse..., Pick, Select) are plain `QPushButton`s at the default height,
  with no colour.
- **Output** goes in a *Log* box at the bottom: a read-only `QPlainTextEdit` with a fixed
  height of about four lines. Its placeholder text says how to start. Small tools use one
  word-wrapped status `QLabel` instead.

## 4. Colour

The palette is Maya's, plus the studio colour scheme below. Never type these colours into a
tool. They live in one module,
[_core/gs_style.py](../Environment/Autodesk/Maya/scripts/GSPipeline/_core/gs_style.py),
so changing the scheme there changes every window. GSPipeline tools reach `_core` with the
`sys.path` snippet at the top of `LOD_Checker_UI.py`. A GSTools tool can reach it through
the `GSPIPELINE` environment variable that `Maya.env` sets.

**Primary action buttons** are filled with the studio colours, in reading order:

| Button          | Colour                     | Constant                 | Examples                  |
| --------------- | -------------------------- | ------------------------ | ------------------------- |
| first           | `#6b0914` studio red       | `gs_style.STUDIO_RED`    | Check Selection, RESET    |
| second          | `#f6921e` studio orange    | `gs_style.STUDIO_ORANGE` | Fix Selected, SWITCH      |

`gs_style.style_button(button, colour)` sets the fill and white bold text, and adds the
hover, pressed and disabled looks. A window with one primary action uses studio red. Only
primary actions are coloured; secondary buttons keep Maya's grey. In a `maya.cmds` window
use `backgroundColor=gs_style.rgb(gs_style.STUDIO_RED)`.

**Log and status text** uses these three colours, from `gs_style.LOG_COLOURS`:

| Level | Colour    | Use                                                    |
| ----- | --------- | ------------------------------------------------------ |
| ok    | `#7ec87e` | the action did what was asked; a check passed          |
| warn  | `#e0b64c` | done, but look at this (items flagged, some skipped)   |
| error | `#e06c6c` | nothing was done; the message says why and what to do |

Plain information stays in the default text colour.

```python
LOG_COLOURS = gs_style.LOG_COLOURS

def log(self, message, level="info"):
    colour = self.LOG_COLOURS.get(level)
    if colour:
        self.log_view.appendHtml('<span style="color:{}">{}</span>'.format(
            colour, html.escape(message)))
    else:
        self.log_view.appendPlainText(message)
```

**Don't** use:

- hex codes or RGB values typed into the tool, instead of taken from `gs_style`
- `setStyleSheet` on anything other than a primary button through `gs_style`
- `backgroundColor=` on anything other than a primary `cmds.button`
- a `THEME` dict or a dark theme of the tool's own
- per-category or per-section colours
- emoji, or Unicode symbols used as icons (▶ 🔧 ✔)

**Destructive actions** don't get a colour of their own. The studio red is a brand colour,
not a warning. Make destructive actions undoable and say in the tooltip what they delete. Ask with a `confirmDialog` only when undo can't bring it back, such as
files on disk.

**`maya.cmds` status lines** can't colour their text. A status line may use the subdued
backgrounds GS File Transfer uses: idle `(0.24, 0.24, 0.26)`, ok `(0.22, 0.38, 0.24)` and
warn `(0.46, 0.31, 0.14)`. That's the only place a tool sets a background colour.

## 5. Text

Artists read this text, so keep it short and plain. Detail is welcome in the code and its
docstrings, which developers read.

- **Case.** Group titles, buttons and form labels use Title Case. Tooltips, the log and hints
  use sentence case.
- **Labels.** Use as few words as needed, and don't repeat the box title: in a *Kerb Spec* box
  it's *Height:*, not *Kerb Height:*.
- **Buttons** start with a verb and say what they act on: *Check Selection*, *Fix
  Selected*, *Export as ONE FBX*, *Merge Ticked Groups*. A single word is fine when the
  window has only one thing it could act on (*Pick*, *Browse...*).
- **Units** go in the spin-box suffix, not the label: `Height: [2.00 cm]`, not
  `Standard Height (cm):`.
- **Tooltips** are one or two short lines: what it does, plus a hint when there's a common
  trap. *"Smaller drops count as track slope, not a kerb. Raise it if sloped track gets
  flagged."* Not a paragraph on how it works.
- **Log messages** give the result the artist acts on, and nothing else:

  | Write                         | Not                                                                  |
  | ----------------------------- | -------------------------------------------------------------------- |
  | Checked 38 vertices, Z up.    | Checked 38 vertices on 1 mesh, Z up (0.01 s).                        |
  | 38 too high - selected.       | 38 sit on top of a step, 38 of them off 2 ± 0.05 cm: 38 too high, 0 too low. |
  | Fixed 38 vertices to 2 cm.    | one line per vertex with its old and new height                      |
  | Couldn't fix 3 vertices: no kerb step found. They're selected. | a list of the 3 vertex names |

  Leave out counts that are zero, run times, mesh counts and per-item rows. If the artist
  needs to find specific items, select them and say so.
- **On failure**, say what to do next: *Select the kerbs to check first.*, *Pick a valid
  Export To folder first.* Unexpected errors print their traceback to the Script Editor and
  log one line pointing there.
- Don't use exclamation marks, *Successfully*, *EXCELLENT*, *Please*, or shouting
  ("DETECTED 37 VIOLATING VERTICES!").
- Get plurals right: `_plural(count, "vertex", "vertices")` style helpers, not
  "1 vertices".

## 6. Behaviour

- **Feedback.** Results go to the log or status line. Errors also go to `cmds.warning` so they
  reach the command line. Never use a `confirmDialog` to report a result.
- **Errors never close the window.** Route callbacks through a guard. A user error (bad
  selection, bad setting) becomes one log line. An unexpected error prints its traceback to
  the Script Editor and logs one line pointing there.
- **Undo.** One click is one undo step: `cmds.undoInfo(openChunk=True, chunkName=...)` with
  `closeChunk` in a `finally`. Previews that the window puts back itself stay out of the
  undo queue (LOD Checker's `_no_undo`).
- **Selection.** Leave the artist's selection alone unless selecting is the result. A checker
  selects what it flags. On a clean result it leaves the selection as it was.
- **Settings.** Remember preferences between sessions with `optionVar`, prefixed by the tool
  (`gs_file_export_`). Don't remember values a project spec defines (kerb height,
  tolerances). Those reopen at spec, so a value changed for one check never quietly sticks.
- **Long operations** show the wait cursor (`cmds.waitCursor`).
- **scriptJobs** are killed in `closeEvent`.
- **Units.** Say which unit a value is in. The API works in centimetres whatever the scene's
  working unit is. `cmds` works in the working unit, so convert at the boundary.

## 7. Code layout

- **Put the logic first and the window last.** Logic functions take arguments and return
  results. They never read widgets. The window gathers its settings, calls the logic and
  reports the result. Keep it so a check could run from the Script Editor without the
  window.
- **GSPipeline tools** are exec'd as `__main__` by [GSPipeline.py](../Environment/Autodesk/Maya/scripts/GSPipeline/GSPipeline.py),
  so end with `if __name__ == "__main__": show()`. Register the tool in
  [tool_config.py](../Environment/Autodesk/Maya/scripts/GSPipeline/tool_config.py). Shared
  helpers live in `_core/` and are reached with the `sys.path` snippet at the top of
  `LOD_Checker_UI.py`.
- **GSTools packages** are `core.py` + `ui.py`, with an `__init__.show()` that reloads both
  (see gs_mirror).
- Write to the Python 3.7 floor and use no PyMEL; see [CLAUDE.md](../CLAUDE.md).

## 8. Bringing in an outside tool

Before an imported or generated tool goes on the menu:

- [ ] Remove custom colours, themes, stylesheets and `backgroundColor=`. Colour the primary
      buttons through `gs_style` instead.
- [ ] Replace result pop-ups and "show dialog" options with a short log.
- [ ] Turn numbered, ALL CAPS or banner headers into short group titles.
- [ ] Regroup one long column of settings into category boxes, with related values sharing a
      row.
- [ ] Shorten labels and tooltips. Move units into suffixes. Cut log output down to the
      result.
- [ ] Make the window fixed-size.
- [ ] Drop options that do the same thing as another option, or that only make sense in a
      case the project doesn't have.
- [ ] Wrap each action in one undo chunk.
- [ ] Use cmds / om2 instead of PyMEL, PySide2/6 via the import pattern, and nothing above
      Python 3.7.
- [ ] Follow the naming for the window title and `objectName`.
- [ ] Register the tool in `tool_config.py`.

## 9. Tools that don't follow this yet

None of these are broken. They just look different from the rest. Bring one in line when
you're already working on it. Vendored third-party code (NitroPoly, `Qt.py`) is exempt.

| Tool | What's off |
| ---- | ---------- |
| Texel Density Visualizer | Its own dark theme (a `THEME` dict of ~20 colours) |
| Edge Sensei | Coloured buttons throughout |
| Speed Workflow | Coloured `cmds` buttons, one colour per section |
| MGP25 / MGP26 Ultimate Bike Riggator | Coloured `cmds` buttons |
| Model Checker | Category colours, coloured action labels and Revert button |
| HW3 Tools | Red / green / blue `cmds` buttons |
| LOD Checker | ALL CAPS button labels (RESET, SWITCH). Its button colours are the studio scheme. |
| GS File Export | Resizable, though nothing in it needs the room |
| GS Clean Up | Status colours slightly off the table (`#9fd3a8` / `#ff6b6b`) |
| GSTools utilities: GS Faster Startup, Instance Utility, Cable Create, GS Renamer, GS Transfer Transforms, GS Outliner Sorter, GS Path Manager | Coloured buttons and frames |
