=========
ChangeLog
=========


2.3.50 (2024-05-03)
-------------------

Added
~~~~~

- (Exportarrow_64.Png) Added import and export arrow icons.


2.3.49 (2024-01-22)
-------------------

Added
~~~~~

- (Checklistdel_64.Png) Added generic icon for deleting a list.

Removed
~~~~~~~

- (Profiling) Moved profiling module from zoo_core to zooTools Main.


2.3.48 (2023-09-19)
-------------------

Change
~~~~~~

- (Naming) Added support for empty field values which remove field value from resolved string.


2.3.47 (2023-08-11)
-------------------

Remove
~~~~~~

- (Commands) Moved commands into maya commands due to depreciation of standalone usage.


2.3.46 (2023-06-22)
-------------------

Added
~~~~~

- (Iconlib) Add support for passing qrc resource path.

Bug
~~~

- (Zoocommand) Changed command _calldoIt exception handling to defer exception raise to a higher level to avoid trace double up.
- (Zoocommand) Updated py3 depreciated methods.

Change
~~~~~~

- (Naming) If expression doesn't exist a ValueError is now raised.
- (Utils) Moved path.py into zootools main and deprecated functions.

Remove
~~~~~~

- (Tooldata) Removed tooldata py package which is now part of the zoo.core.


2.3.45 (2023-05-03)
-------------------

Bug
~~~

- (Naming) Resolving config changes on rules always adds the same unchanged rules.

Change
~~~~~~

- (Core) Removed all uses of chdir.

Removed
~~~~~~~

- (Utils) Moved strutils from zoo_core to core.


2.3.44 (2023-04-05)
-------------------

Added
~~~~~

- (Execution) Added the ability to execute a string as python code.
- (Send_64.Png) Added simple send icon.

Bug
~~~

- (Naming) Fix naming unitest failure.

Change
~~~~~~

- (Preferences) Updated all prefutils module imports with new namespace.


2.3.43 (2023-03-09)
-------------------

Added
~~~~~

- (Icons) Missing cubeWire_64.png icon for the subd marking menu.


2.3.42 (2023-03-07)
-------------------

Bug
~~~

- (Openlocation) OSX erroring when only folder in finder.


2.3.41 (2023-03-02)
-------------------

Added
~~~~~

- (Icons Assorted) Added vertical bar icons for slider ruler ticks as per Tween Machine UI.
- (New Control Shapes) Added two new control shapes to the internal library. cube_boundingHalf and square_target_sharp.
- (Square_Target.Shape) Added new control curve shape "square_target".


2.3.40 (2023-01-25)
-------------------

Change
~~~~~~

- (License) Update copyright for 2023.


2.3.39 (2022-12-03)
-------------------

Added
~~~~~

- (Shapelib) Added sphere_arrow to shapeLib.
- (Tracing) Added Helper function to find crash points.

Bug
~~~

- (Profiling) Failure to output profile due to folder not existing.
- (Qt) Fix iconLib set alpha channel not available in pyqt 5.13.2.

Change
~~~~~~

- (Sphere_Arrow.Shape) Tweaked the guide shape slightly.


2.3.38 (2022-11-17)
-------------------

Bug
~~~

- (Crash) Crash when incorrect iconName in iconColorizedLayered for PyQt5.
- (Iconlib) Replaced Depreciated method QImage.alphaChannel which doesn't exist in PyQt5.

Change
~~~~~~

- (Icons) Added windowBrowser icon.


2.3.37 (2022-11-16)
-------------------

Change
~~~~~~

- (Icons) Added windowBrowser icon.


2.3.36 (2022-10-26)
-------------------

Change
~~~~~~

- (Application) Avoid local imports.


2.3.35 (2022-09-29)
-------------------

Added
~~~~~

- (Math) Added lerpCount to iterate between to two numbers.
- (Shapelib) Added circleLipRaiseEdge, circleTriangleUp, pin4_tri_round shapes.
- (Shapes) Added arrow thin shape.

Bug
~~~

- (Naming) Creating a diff resulted in missing local fields and rules when diffing against itselfs original unchanged state.

Misc
~~~~

- (Paintroller_64.Png) New paint icon paintroller.


2.3.34 (2022-07-20)
-------------------

Added
~~~~~

- (Zooscenefiles.Py) Added functionality to writeZooInfo() so that existing keys not being updated are kept while saving zooScene files.

Misc
~~~~

- (Misc) Naming config Refactor.


2.3.33 (2022-05-31)
-------------------

Bug
~~~

- (Core) ValueError raised on OSX when import ctypes.
- (Tooldata) Patching root paths doesn't support multiple languages.

Change
~~~~~~

- (Logging) Remove Redundant blender logging code.

Remove
~~~~~~

- (Documentation) Fix failing documentation parser for iconui which has been ported to a toolset.
- (Iconlib) Remove Redundant blender icon lib.
- (Iconlib) Removed Redundant iconUi widget which has been replaced with toolsets.


2.3.32 (2022-04-16)
-------------------

Added
~~~~~

- (Exportglobals.Py) Added more renderer strings to constants.

Bug
~~~

- (Core) CopyDirectoryContents function not overwriting files in subfolders folders.
- (Core) Incorrect function call for determining maya mode.
- (Exportglobals.Py) Returned GENERIC key which was stopping Zoo Tools from loading.
- (Tooldata) False positive conditional when retrieving settings from a given root.
- (Tooldata) Patch resolving root path between maya 2022- and 2023+.
- (Tooldata) When specifying a settings path to load without an extension would return an invalid object.

Change
~~~~~~

- (Commands) Light update to the command viewer to make it display.
- (Commands) Removed redundant command library folder.
- (Core) Dict merge to support only merge missing keys in dicts.
- (Core) RelativeTo function to support the direct child of root.
- (Documentation) Package title typo fix.
- (Icon) Move sortDown,sortUp icons to zoo_core.
- (Pluginmanager) Added name to plugin manager for logging.
- (Unittest) Fix slow test timings being printed to stdout when there's no slow tests.

Misc
~~~~

- (Misc) Fix preferences path for OSX.

Removed
~~~~~~~

- (Controls.__Init__.Py) Removed function convertRotateUpList() and replaced with a dictionary.


2.3.31 (2022-03-14)
-------------------

Added
~~~~~

- (Icons) BoxAdd, boxRemove and triangleDownTiny.

Bug
~~~

- (Core) Fix specific use of ntpath instead use os.path.
- (Zooscenes) Failure to delete file dependencies folder when it's not empty.

Change
~~~~~~

- (Core) Move trailingNumber function into strutils for better organisation.
- (Directorypath) Convert class to inherent from ObjectDict for better serialization.


2.3.30 (2022-02-22)
-------------------

Added
~~~~~

- (Output.Py) Support for inViewMessages in Maya.

Bug
~~~

- (Logging) Layered stack traces are output when an error occurs instead of one.
- (Tooldata) Fix ValueError not displaying filePath.

Change
~~~~~~

- (Doc) Color documentation extra information.
- (Objectdict) ObjectDict now property overrides not just "." syntax.


2.3.29 (2022-02-04)
-------------------

Added
~~~~~

- (Icon) Added Checklist icon, list with two ticks.

Change
~~~~~~

- (Command) Remove redundant blender code.
- (Core) Move pluginManager interface initialization to iterable.


2.3.28 (2022-01-18)
-------------------

Added
~~~~~

- (Exportabcshaderlights.Py) Can now save a shader as a zoo scene from a Zoo shaderInstance object.
- (Settingsliders_64.Png) Sliders icon.
- (Shaderbase.Py) Can query the shader name while removing type suffix shaderbase.shaderNameNoSuffix().
- (Zoomath) Added mean function to zoomath because only py3 has a stdlib function for it.

Bug
~~~

- (Naming) Fix Error on save when folders don't exist.
- (Naming) Fix KeyError being raised due to typo.

Change
~~~~~~

- (Naming) Support for parent child config hierarchy.
- (Naming) Support for passing fields to resolve method.
- (Naming) Update Unittests to cover naming hierarchy.
- (Naming) Updated Docstrings.
- (Zoo Scene) Zoo Scene version is now 1.1.0 with new attributes available in the shaderbase.py.

Removed
~~~~~~~

- (Ignore) Removed Old CI files.


2.3.25 (2021-12-18)
-------------------

Added
~~~~~

- (Color) Hsv 2 rgb helper function.


2.3.24 (2021-12-08)
-------------------

Change
~~~~~~

- (Core) Dict merge to support lists.
- (Core) ObjectDict to pass through __init__ to avoid unnecessary override.
- (Shapelib) Now caches shapes data which was loaded within the library. reduces IO and increases loadFromLib speeds.
- (Shapelib) Now caches shapes into memory for faster loading and reduced File I/O.


2.3.23 (2021-11-16)
-------------------

Added
~~~~~

- (Icon) Added cursorWindow_64.png icon.

Change
~~~~~~

- (Core) Dict merge to support lists.
