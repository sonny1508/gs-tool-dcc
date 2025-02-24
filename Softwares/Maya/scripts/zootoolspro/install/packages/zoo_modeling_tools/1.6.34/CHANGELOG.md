=========
ChangeLog
=========


1.6.34 (2024-05-03)
-------------------

Added
~~~~~

- (Zoo_Modeling_Tools_Actionplugins.Py) Added support for the Third Party Quad Patcher Script.


1.6.33 (2023-12-05)
-------------------

Change
~~~~~~

- (Modelingtooltips.Py) Support for new marking menus, delete history, freeze transforms, bevel/boolean.


1.6.32 (2023-08-22)
-------------------

Change
~~~~~~

- (Toolpalette) Change Definition type to Action Type for better clarity in naming.


1.6.31 (2023-08-11)
-------------------

Added
~~~~~

- (Objectstoolbox.Py) Fixed missing right click menu in the advanced mode.
- (Zoo_Modeling_Tools_Shelf.Layout) Added new tooltips for the Modeling shelf icon.

Bug
~~~

- (Sculptingtoolbox.Py) Invert Freeze button is named correctly once again.

Change
~~~~~~

- (Commands) Update commands to latest core changes.


1.6.29 (2023-06-22)
-------------------

Added
~~~~~

- (Sculptingtoolbox.Py) Added right click menus for sculpt (knife) with other stamp options, added wax alternatve stamp. Added Falloff buttons. Added convert selection to freeze on Freeze button right click.
- (Sculptingtoolbox.Py) Advanced mode added to sculpting toolbox.

Bug
~~~

- (Modelingtooltips.Py) Small tweaks to sculpt tooltips.

Change
~~~~~~

- (Toolsets) Updated all instances of LeftAlignedButton with icon instance being passed including color changes.
- (Modelingtoolbox.Py) Refactored buttons, icon size and button padding is correct.
- (Objectstoolbox.Py) Refactored buttons, icon size and button padding is correct.
- (Sculptingtoolbox.Py) Refactored buttons, icon size and button padding is correct.
- (Selector.Py) Refactored buttons, icon size and button padding is correct.
- (Topologynormalstoolbox.Py) Refactored buttons, icon size and button padding is correct.


1.6.28 (2023-05-11)
-------------------

Added
~~~~~

- (Modelingtooltips.Py) Added various tooltips.


1.6.27 (2023-05-10)
-------------------

Added
~~~~~

- (Modelingtoolbox.Py) Now with advanced mode, less tools in compact.
- (Modelingtooltips.Py) Minor tweaks to modeling tooltips.
- (Objectstoolbox.Py) Now with advanced mode, less tools in compact.
- (Sculptingtoolbox.Py) Added advanced mode to sculptingtoolbox.py, added right clicks to sculpt knife and wax tools. Added falloff surface and volume to UI.
- (Selector.Py) Now with advanced mode, less tools in compact.
- (Selector.Py & Zoomirrorgeo.Py) Added missing tooltips and hotkeys in tooltips are now dynamic.
- (Topologynormalstoolbox.Py) Now with advanced mode, less tools in compact.

Bug
~~~

- (All Uis) Advanced functions were not connected correctly.

Change
~~~~~~

- (Modelingtooltips.Py) Tooltip descriptions and assorted hotkeys added for Topology and Sculpting toolsets.


1.6.26 (2023-05-03)
-------------------

Added
~~~~~

- (Grid_64.Png Sculpting_64.Png) Added icons for sculpt ui and topology ui.
- (Modelingtoolbox.Py) Modeling toolbox is now fully working, only missing right clicks.
- (Modelingtoolbox.Py) Tooltips and right click menus added.
- (Modelingtoolbox.Py) WIP Modeling Toolbox UI will be broken up into many UIs.
- (Modelingtooltips.Py) New module for managing tooltips for the modeling tools with auto generated hotkeys.
- (Objectstoolbox.Py) Added Objects Toolbox UI. WIP buttons not working yet.
- (Objectstoolbox.Py) Is mostly working, though will need a few tweaks. Right-clicks working.
- (Objectstoolbox.Py) Tooltips and right click menus added.
- (Sculptingtoolbox.Py) Added Sculpting Toolbox UI. Mostly working UI, right clicks need to be added.
- (Sculptingtoolbox.Py) Tooltips and right click menus added.
- (Selector.Py) Tooltips and right click menus added.
- (Topologynormalstoolbox.Py) Added Topology And Normals Toolbox UI. WIP buttons not working yet.
- (Topologynormalstoolbox.Py) This UI is mostly working, right-clicks are still missing and Transfer Vertex Normals too.
- (Topologynormalstoolbox.Py) Tooltips and right click menus added.

Bug
~~~

- (Topologynormalstoolbox.Py) Disabled features found in previous versions of Maya.

Change
~~~~~~

- (Modelingalign.Py) Modeling Align tool renamed to Align Toolbox.
- (Modelingalign.Py) Select tool renamed to Select Toolbox.
- (Modelingtoolbox.Py) Big changes to the Modeling Toolbox, still in WIP, buttons not working.
- (Zoo_Modeling_Tools_Toolsets.Layout) New toolsets created. Modeling has been split into Modeling Toolbox and Modeling Misc.
- (Zoomirrorgeo.Py) Zoo Mirror Geo tool renamed to Mirror Toolbox.


1.6.25 (2023-04-05)
-------------------

Change
~~~~~~

- (Preferences) Updated all prefutils module imports with new namespace.


1.6.24 (2023-03-02)
-------------------

Added
~~~~~

- (Selection Set Shelf Menu) Added Selection Sets to modeling shelf menu.


1.6.23 (2023-01-25)
-------------------

Change
~~~~~~

- (License) Update copyright for 2023.


1.6.22 (2022-12-03)
-------------------

Bug
~~~

- (Qt) Fix Layouts having the same parent causing Qt logs to be output of linux/OSX.


1.6.21 (2022-07-20)
-------------------

Misc
~~~~

- (Objectcleaner.Py) Added option to keep parent structure while obj import/export. Keeps hierarchy by default. Simplified the compact mode, import/export clean options are now only in the advanced mode.


1.6.20 (2022-05-31)
-------------------

Added
~~~~~

- (Objectcleaner.Py) Added Select Tris and NGons buttons.
- (Objectcleaner.Py) Added triangulate NGons.

Change
~~~~~~

- (Zoopackage) Removed Redundant startup commands in zoo_package.

Removed
~~~~~~~

- (Zoopackage) Removed Redundant blender layout files.


1.6.19 (2022-04-16)
-------------------

Bug
~~~

- (Core) Incorrect function call for determining maya mode.


1.6.16 (2021-12-08)
-------------------

Change
~~~~~~

- (Zoo Renamer) Move renamer into modelling tools layout Keen Foong.
