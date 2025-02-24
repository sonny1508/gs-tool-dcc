=========
ChangeLog
=========


1.3.27 (2024-05-03)
-------------------

Bug
~~~

- (Arealights.Py) Now opens the correct (newer) Light Editor.
- (Directionallights.Py) Now opens the correct (newer) Light Editor.


1.3.26 (2023-08-22)
-------------------

Change
~~~~~~

- (Toolpalette) Change Definition type to Action Type for better clarity in naming.


1.3.25 (2023-08-11)
-------------------

Added
~~~~~

- (Zoo_Light_Suite_Shelf.Layout) Added new tooltips for the Lighting shelf icon.


1.3.24 (2023-06-22)
-------------------

Added
~~~~~

- (Lightpresets.Py) Added support for other maya unit scene types, inches, feet, yards etc.


1.3.23 (2023-04-05)
-------------------

Change
~~~~~~

- (Preferences) Ported LightSuites pref interface function from preferences repo.


1.3.21 (2023-01-25)
-------------------

Added
~~~~~

- (Fixviewport.Py) Now turns the viewport light mode off when deleting the light rig.

Bug
~~~

- (Hdriskydomelights.Py) Fixed name issue while changing renderer but it was still naming with the incorrect renderer suffix.

Change
~~~~~~

- (License) Update copyright for 2023.
- (Hdriskydomelights.Py) Now created skydomes named hdriSkydome_SUFFIX not skydomeLight_SUFFIX which is an Arnold term.
- (Licence) Fix licence copyright date.


1.3.20 (2022-10-26)
-------------------

Added
~~~~~

- (Shelf) Added Refresh viewport action to shelf menu.

Change
~~~~~~

- (Minibrowsers) Removed Redundant item model arguments.


1.3.19 (2022-07-20)
-------------------

Added
~~~~~

- (Hdriskydomelights.Py) Added Advanced mode back for HDRI Skydomes.
- (Hdriskydomelights.Py) Added the name textbox in advanced mode.
- (Hdriskydomelights.Py) Linked UI Rotation and Intensity settings to middle click virtual sliders.
- (Hdriskydomelights.Py) Load and save multiply and offset info to zooInfo files. Data is remembered.
- (Hdriskydomelights.Py) Uses new methods for setting and getting rotateOffset and intensityMultiply values. Creating new lights simplified code.
- (Hdriskydomelights.Py) Intensity and rotation multipliers to the UI and for getters and setters.
- (Hdriskydomelights.Py) Offset and multiply data is handled in the UI sliders.
- (Hdriskydomelights.Py) Refresh button to reset the offset and multiply info.
- (Hdriskydomelights.Py) Tooltips on buttons.

Change
~~~~~~

- (Browsers) Removed Redundant Image view chunk size override.
- (Hdriskydomes) Default image load count.
- (Minibrowser) Reduced Image loading count to 20 vs 200 to speed up UI load time.

Misc
~~~~

- (Hdriskydomelights.Py) Support for connected attributes. UI will be disabled if the attributes are connected. Added ( hdriskydomelights.py ) Added rename, delete and refresh functionality, now works in the dots menu.
- (Hdriskydomelights.Py) Tweaks for rotation offset and intensity multiply values for the HDRI Skydomes. BugFix ( hdriskydomelights.py ) Save rot int offsets retuns if no image selected.


1.3.18 (2022-05-31)
-------------------

Added
~~~~~

- (Hdriskydomelights_New.Py) New UI for the class based Skydome browser WIP. First pass. Only Redshift and Renderman are working roughly.
- (Hdriskydomelights_New.Py) Overall tweaks, new buttons and more functionality added. UI now refreshes from scene. Auto selection from scene. Still WIP.

Bug
~~~

- (Hdriskydomelights_New.Py) Better creation methods and now sets and retrieves all UI attributes.
- (Hdriskydomelights_New.Py) Better path checks while browsing for skydome images.
- (Hdriskydomelights_New.Py) No longer shows the Maya renderer (though could make this reference Arnold).
- (Hdriskydomelights_New.Py) Now supports undo on the sliders properly.
- (Hdriskydomelights_New.Py) Sets the renderer globaly when changed.

Change
~~~~~~

- (Hdriskydomelights.Py) Renamed old Skydome UI to _old and new to hdriskydomelights.py. Removed old UI from the menu and shelves. New UI with sliders and supports VRay.
- (Hdriskydomelights_New.Py) Removed the advanced widget.
- (Zoopackage) Removed Redundant startup commands in zoo_package.

Removed
~~~~~~~

- (Zoopackage) Removed Redundant blender layout files.


1.3.17 (2022-04-16)
-------------------

Bug
~~~

- (Core) Incorrect function call for determining maya mode.
- (Fixviewport.Py) New light intensities for Fix Viewport to correctly match Maya.

Change
~~~~~~

- (Fixviewport.Py) Disabling specualr intensity for the defaults.


1.3.16 (2022-03-14)
-------------------

Bug
~~~

- (Hdriskydomes) Refresh after deleting a hdri doesn't occur.


1.3.15 (2022-02-22)
-------------------

Added
~~~~~

- (Hdriskydomelights.Py) Virtual slider added for skydome rotation.

Change
~~~~~~

- (Lightpresets) Update light presets to use multi directories.
- (Shelf) Update to use supported shelf button type.
- (Skydomes) Update skydomes to use multi directories.
- (Zoopackage) Added zoo_preferences as dependency so package commands will run first.

Remove
~~~~~~

- (Core) Removed now redundant prefsdata and assetdirectories modules. Replaced with preference interface.


1.3.13 (2022-01-18)
-------------------

Added
~~~~~

- (Hdriskydomelights.Py) Now ignores "VRay" and "Maya" until they are later upgraded.

Change
~~~~~~

- (Fix Viewport) Main create button now acts as the preset 1k soft. Creates the light setup and switches on the viewport settings.
- (Various Uis) Now ignore VRay and Maya renderers on open and while changining renderers.


1.3.11 (2021-12-08)
-------------------

Added
~~~~~

- (Change Log) Added changelog stub.

Bug
~~~

- (Change Renderer) Fix issue where changing renderer wouldn't update prefs.
