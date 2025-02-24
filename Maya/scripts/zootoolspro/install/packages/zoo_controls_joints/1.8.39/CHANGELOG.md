=========
ChangeLog
=========


1.8.39 (2024-05-10)
-------------------

Bug
~~~

- (Brsmoothskinui.Py) Fixed bug where strength was going whack while flooding.


1.8.38 (2024-05-03)
-------------------

Added
~~~~~

- (Brshapes_32.Png) Added SHAPES icon.
- (Brsmoothskin.Py) Brave Rabbit Smooth Skin Weights tool added. Community scripts need to be installed.
- (Brtransferskincluster.Py) Added auto rename skin cluster button and tooltips.
- (Brtransferskincluster.Py) Added new tool for third party Brave Rabbit Transfer Skin Weights.
- (Skinwrangler.Py) Skjin Wrangler Support, third party script needs to be installed.
- (Studiolib_32.Png) Added studio library icon.
- (Zoo_Controls_Joints_Shelf.Layout) Added modified Brave Rabbit smooth skin weights tool, Skin Wrangler, Brave Rabbit Transfer Weights, and SHAPES to the rig menu. Third Party supported scripts.


1.8.37 (2024-02-21)
-------------------

Added
~~~~~

- (Constrainttoolbox.Py) Added Open Multi Constraint Window (Match & Bake Anim).


1.8.36 (2024-01-22)
-------------------

Added
~~~~~

- (Zoo_Controls_Joints_Shelf.Layout) Added matchBakeAnim.
- (Zoo_Controls_Joints_Menu.Layout) Added matchBakeAnim and zooRenamer.


1.8.35 (2023-09-19)
-------------------

Bug
~~~

- (Jointtool) Fix displayJointSize failure.


1.8.34 (2023-08-22)
-------------------

Bug
~~~

- (Jointtool.Py) Missing Undo decorator added to create joint functions.


1.8.33 (2023-08-11)
-------------------

Added
~~~~~

- (Blendshapetoolbox.Py) Placeholder, this tool is not working/activated yet.
- (Constrainttoolbox.Py) Added Group Zero Object and Mark Ceneter Pivot Buttons and tooltips.
- (Constrainttoolbox.Py) Added geoNormalConstraint and tooltips.
- (Constrainttoolbox.Py) Logic is now working. Still needs tooltips.
- (Constrainttoolbox.Py) UI is roughed out, logic has not been added.
- (Deformertoolbox.Py) UI is roughed out, logic has not been added.
- (Deformertooltips.Py) Added constraint tooltips.
- (Jointtool.Py) Added Create Joints Multi Parent right click option.
- (Jointtool.Py) Added Mark Center Pivot and Volume snap toggle.
- (Jointtool.Py) Added create joints from selection right click menu.
- (Jointtool.Py) Added matrix freeze and reset.
- (Twistdeform_64.Png) Added icon.
- (Zoo_Controls_Joints_Shelf.Layout) Added new shelf icon and menu "Rigging Macros", changed the Deformer icon.
- (Zoo_Controls_Joints_Shelf.Layout) Added new tooltips for the Rigging shelf icons.
- (Zoo_Controls_Joints_Toolsets.Layout) New toolset group categories Deformers and Rigging Macros added.

Bug
~~~

- (Splinebuilder) Fix rig not able to build in scene units other than centimetres.

Change
~~~~~~

- (Commands) Update commands to latest core changes.

Removed
~~~~~~~

- (Deformertoolbox.Py) Disabled wip UI.
- (Zoo_Controls_Joints_Shelf.Layout) Removed Deformer Toolbox.
- (Zoo_Controls_Joints_Shelf.Layout) Removed new shelf icons reverting back to one Controls Joints icon in the zoo menu.


1.8.32 (2023-06-22)
-------------------

Added
~~~~~

- (Coplanar) Added CoPlanar toolset.
- (Jointtool.Py) Added Mirror Orientation and Behaviour options to the advanced UI.
- (Jointtool.Py) Added Scale Compensate On and Off to the advanced UI.
- (Jointtool.Py) Added draw styles floating joint and multi-box to advance UI.
- (Jointtool.Py) Added plane and up ctrl modes the world up combo.
- (Jointtool.Py) Added reset UI button.
- (Jointtool.Py) New style orient which supports vectors and API code. No undo support yet. No up arrow control yet.
- (Jointtool.Py) Now correctly uses the plane to pos snap if multiple braches, with minor issues.
- (Jointtool.Py) Options to change aim, up and world up axis for the joint orient.
- (Jointtool.Py) Picks up meta node ref plane from other UIs.
- (Jointtool.Py) Plane and Arrow modes are working but have bugs.
- (Jointtool.Py) Position right-click menu added and working.
- (Jointtool.Py) UI updates joint size and scale compensate while changing selection. Also on startup.
- (Plainorient.Py) Improved tooltips.
- (Plainorient.Py) Inital selection is remembered while starting the tool.
- (Plainorient.Py) New tool icon.
- (Plainorient.Py) Self validates if reference plain or start/end joints or meta has been deleted while mouse enters the tool.
- (Plainorient.Py) Support for typing names into the UI, checks for name clashes etc.
- (Plainorient.Py) UI has been simplified, LRA buttons added. This tool should be fully working with assorted functionality tooltips and help page.
- (Planeorient.Py) Picks up meta node ref plane from other UIs.

Bug
~~~

- (Jointtool.Py) Rotate buttons change axis to match the aim axis setting in the compact UI.

Change
~~~~~~

- (Jointtool.Py) Tweaked tooltips.
- (Jointtool.Py) Tooltip tweaks.
- (Plainorient.Py) Merged with daves new code for populating UI with the initial selection.
- (Plainorient.Py) Refactored previously coplanar.py.
- (Zoo_Controls_Joints_Toolsets.Layout) Order in toolset changed for coplanar.

Misc
~~~~

- (Typeerror) Oops tooltip argument spelling.

Removed
~~~~~~~

- (Preferences) Removed redundant code.


1.8.31 (2023-05-03)
-------------------

Added
~~~~~

- (Skinningutilities.Py) Added new buttons autoRenameSkinCluster and weightHammer.

Change
~~~~~~

- (Twistsui.Py) Removed beta status.


1.8.30 (2023-04-05)
-------------------

Added
~~~~~

- (Skinningutilities.Py) Tooltips to copy and paste icons.

Change
~~~~~~

- (Preferences) Ported ControlJoints pref interface function from preferences repo.


1.8.29 (2023-03-07)
-------------------

Bug
~~~

- (Twistsui.Py) Twist Extractor now warns the user while using in Maya 2019 and below.


1.8.28 (2023-03-02)
-------------------

Added
~~~~~

- (Controlcreator.Py) Added a button for Deleting the Zoo Tracker Attributes from the selected controls.
- (Editcontrols.Py) Added a menu item (lower dots menu) for Deleting the Zoo Tracker Attributes from the selected controls.
- (Riggingmiscui.Py) Added right-click menu on the Mark Center Pivot button. Can now create locators, and also many markers matched to all selected objects.
- (Skinningutilities.Py) Added copy and paste skin weights which allows for pasting onto selected components, faces/verts etc.
- (Twistsui.Py) Added new tool Twist Extractor for creating a quaternion node setup that measures twists between two objects.

Bug
~~~

- (Twistsui.Py) Fixed issues when the driven attribute is left blank.


1.8.27 (2023-01-25)
-------------------

Added
~~~~~

- (Editcontrols.Py) Added "X-Ray Curves" Checkbox, functionaity is working.

Change
~~~~~~

- (License) Update copyright for 2023.


1.8.26 (2022-12-03)
-------------------

Added
~~~~~

- (Riggingmiscui.Py) Added "Match Objects" combo and button to Rigging Misc UI.
- (Skinningutilities.Py) Added different skinning options to the skin button > right-click.

Bug
~~~

- (Qt) Fix Layouts having the same parent causing Qt logs to be output of linux/OSX.


1.8.25 (2022-09-29)
-------------------

Removed
~~~~~~~

- (Modelcontrolcurves) Removed item priority sorting temporarily due to i/o bugs it causes.


1.8.24 (2022-07-20)
-------------------

Change
~~~~~~

- (Browsers) Removed Redundant Image view chunk size override.
- (Minibrowser) Reduced Image loading count to 20 vs 200 to speed up UI load time.

Remove
~~~~~~

- (Filemodel) Removed Redundant FileModel import statement.


1.8.23 (2022-05-31)
-------------------

Change
~~~~~~

- (Minibrowsers) Update minibrowserpathlist import.
- (Splinerig) Rig combobox italic to be set via the font() instead of the stylesheet.
- (Zoopackage) Removed Redundant startup commands in zoo_package.

Removed
~~~~~~~

- (Zoopackage) Removed Redundant blender layout files.


1.8.22 (2022-04-16)
-------------------

Added
~~~~~

- (Replacejointweights.Py) Added button self.transferSelBtn for transferring skin weights between selected joints.

Bug
~~~

- (Core) Fixed numerous Qt warnings related to multiple layouts being parented to the same QWidget.
- (Core) Incorrect function call for determining maya mode.
- (Splinerig.Py) RebuildAdditiveFk needed a kwarg to avoid errors.

Removed
~~~~~~~

- (Convertrotateuplist() ) Removed function convertRotateUpList() and replaced with a dictionary in zoocore, refactor for many files.


1.8.21 (2022-03-14)
-------------------

Change
~~~~~~

- (Replacejointweights.Py) Title no longer contains "beta".


1.8.20 (2022-02-22)
-------------------

Bug
~~~

- (Controlcreator.Py) Warns the user if no thumbnails are selected for misc functions.
- (Editcontrols.Py) Better error checks for combine and replace curves.

Change
~~~~~~

- (Shelf) Migrate shelf button to new button type.
- (Smooth Skin - Brave Rabbit) Disable tool as not public yet.
- (Zoo_Controls_Joints_Toolsets.Layout) Removed "smoothSkin" from the toolsets layout.

Removed
~~~~~~~

- (Api) Remove redundant maya/blender conditional.


1.8.19 (2022-02-04)
-------------------

Added
~~~~~

- (Replace Joint Weights) Icon added.
- (Replace Joint Weights) New tool that can replace joint skin weights between joints by suffix/prefix.
- (Rigging Misc Ui) Added follicles transfer button.

Change
~~~~~~

- (Replace Joint Weights) Tool renamed with (beta) at end.
- (Smooth Skin Ui) Temporarily enabled in Zoo dev again.


1.8.18 (2022-01-18)
-------------------

Added
~~~~~

- (Riggin Miscellaneous) Added help URL to tool.

Bug
~~~

- (Preferences) ControlJointsInterface being initialized on module load causes issues with Doc Gen.


1.8.16 (2021-12-18)
-------------------

Added
~~~~~

- (Bakenamespaces) For Rigging Miscellaneous UI.
- (Obj Selection Highlight) Buttons for Rigging Miscellaneous UI.
- (Rigging Misc) New tool called `Rigging Misc` with mark center pivot and more later.
- (Smoothskinui.Py) Inital support for braverabbits smooth skin tool. Must separately install smoothweights plugin. Will be moved to a new repo later.

Change
~~~~~~

- (Rigging Miscellaneous) Tool name renamed to Miscellaneous.


1.8.15 (2021-12-08)
-------------------

Change
~~~~~~

- (Zoo Renamer) Move renamer into controls joints from zoo maya.


1.8.14 (2021-11-16)
-------------------

Bug
~~~

- (Editcontrols) Fixed bug where CombineSelectedCurves was not working in the editcontrols.py UI.
- (Layout) Fix color button widths.
