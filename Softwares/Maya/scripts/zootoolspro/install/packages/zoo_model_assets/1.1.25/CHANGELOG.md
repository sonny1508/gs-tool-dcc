=========
ChangeLog
=========


1.1.25 (2024-01-22)
-------------------

Misc
~~~~

- (Mayascenescore.Py) Import now always preserves references.


1.1.24 (2023-08-22)
-------------------

Change
~~~~~~

- (Toolpalette) Change Definition type to Action Type for better clarity in naming.


1.1.23 (2023-08-11)
-------------------

Added
~~~~~

- (Zoo_Model_Assets_Shelf.Layout) Added new tooltips for the Assets shelf icon.


1.1.22 (2023-05-03)
-------------------

Removed
~~~~~~~

- (Utils) Moved strutils from zoo_core to core.


1.1.21 (2023-04-05)
-------------------

Bug
~~~

- (Startup) Fix startup file to avoid importing modules before they exist due to later zoo version logic.


1.1.20 (2023-03-23)
-------------------

Change
~~~~~~

- (Mayascenes) Import and reference asset now asks user for namespace.
- (Preferences) Replace all prefutils use with new namespace path.
- (Preferences) Ported ControlJoints pref interface function from preferences repo.

Removed
~~~~~~~

- (Flake8) Removed flake8 file as it's no longer needed.


1.1.19 (2023-01-25)
-------------------

Change
~~~~~~

- (License) Update copyright for 2023.


1.1.18 (2022-10-26)
-------------------

Misc
~~~~

- (Mayascenes.Py) Browser always defaults to all for simplicity for the user.


1.1.17 (2022-07-25)
-------------------

Misc
~~~~

- (Mayascenes.Py) Columns in the browser set to 3 and not 1.


1.1.16 (2022-07-20)
-------------------

Change
~~~~~~

- (Browsers) Removed Redundant Image view chunk size override.
- (Minibrowser) Reduced Image loading count to 20 vs 200 to speed up UI load time.

Misc
~~~~

- (Zoo_Model_Assets_Actionplugins.Py) Added for rotation offset and intensity multiply values for the default HDRI Skydomes.


1.1.15 (2022-05-31)
-------------------

Change
~~~~~~

- (Minibrowsers) Update minibrowserpathlist import.

Removed
~~~~~~~

- (Zoopackage) Removed Redundant blender layout files.


1.1.14 (2022-04-16)
-------------------

Bug
~~~

- (Core) Incorrect function call for determining maya mode.


1.1.13 (2022-03-14)
-------------------

Added
~~~~~

- (Mayascenes.Py) Added "All" renderer and also filters our Maya shaders in other renderers to.

Change
~~~~~~

- (Mayascenes) Display user message on save.
- (Mayascenes) Ignore output message when saving a maya file.
- (Mayascenes) Provide user popup when the save path already exists.


1.1.12 (2022-02-22)
-------------------

Bug
~~~

- (Browsers) Fix maya scenes preferences not being upgraded.
- (Mayascenescore.Py) Small warning change if user imports with no thumbnails selected.

Change
~~~~~~

- (Zoopackage) Remove redundant blender specific environment.


1.1.11 (2022-02-04)
-------------------

Added
~~~~~

- (Alembicassets) Support for multiDirectory browser.

Bug
~~~

- (Scenes Browser (.Ma/.Mb) ) icon error fix.

Change
~~~~~~

- (Alembic Assets (Multi-Renderer) ) Renamed tool, from Alembic Assets.
- (Minibrowser) Re-enable infobutton in minibrowser.
- (Scene Browser (.Ma/.Mb) ) Renamed tool, from Maya Scenes.
- (Scenes Browser (.Ma/.Mb) ) now with an M icon (maya's logo).


1.1.10 (2022-01-18)
-------------------

Added
~~~~~

- (Exportabcshaderlights.Py) Added function setShaderAttrsZscnInstance() for setting shader instances.
- (Misc Shader Types) Added small functionality across all shader types.
- (Misc Uis) Now ignore "VRay" and "Maya" until they are later upgraded.
- (Rendererconstants.Py / Shdmultconstants.Py) Added various constants.

Change
~~~~~~

- (Alembic Assets) Model Assets tool has been renamed to Alembic Assets for clarity.
- (Mayascenes.Py) Now supports "Maya" and VRay as renderers.
- (Randomshaders.Py) Now uses shaderTypes for creation rather than by renderer.
- (Shaderbase.Py) Better dictionary support for attributes.


1.1.8 (2021-12-08)
------------------

Added
~~~~~

- (Change Log) Added changelog stub.
- (Maya Scenes) Choose file saving by ascii or maya binary.
- (Maya Scenes) Force original ma/mb if unknown nodes/plugins found.
- (Maya Scenes) Forced ma/mb to export selected.
- (Maya Scenes) Import help and readme to the dots menu.
- (Maya Scenes) Right click save options to the main save button. save scene (MB), save scene (MA), export selected (MB), export selected (MA).
- (Maya Scenes) Save buttons and reference buttons to mayascenes.py.

Bug
~~~

- (Change Renderer) Fix issue where changing renderer wouldn't update prefs.
- (Maya Scenes) Fix export selected error for maya scenes.

Change
~~~~~~

- (Button) Using btnWidth instead.
