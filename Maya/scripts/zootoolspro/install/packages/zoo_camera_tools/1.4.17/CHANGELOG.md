=========
ChangeLog
=========


1.4.17 (2023-08-22)
-------------------

Change
~~~~~~

- (Toolpalette) Change Definition type to Action Type for better clarity in naming.


1.4.16 (2023-08-11)
-------------------

Added
~~~~~

- (Zoo_Camera_Tools_Shelf.Layout) Added new tooltips for the Camera shelf icon.


1.4.15 (2023-04-05)
-------------------

Change
~~~~~~

- (Preferences) Ported camera pref interface function from preferences repo.


1.4.14 (2023-01-25)
-------------------

Change
~~~~~~

- (License) Update copyright for 2023.


1.4.13 (2022-12-03)
-------------------

Bug
~~~

- (Qt) Fix Layouts having the same parent causing Qt logs to be output of linux/OSX.


1.4.12 (2022-11-17)
-------------------

Change
~~~~~~

- (Icons) Moved windowBrowser icon to zoo_core.


1.4.11 (2022-11-16)
-------------------

Change
~~~~~~

- (Icons) Moved windowBrowser icon to zoo_core.


1.4.9 (2022-07-20)
------------------

Bug
~~~

- (Focuspuller_Ui.Py) Checks to see if focusDistance attribute is already connected or keyed.
- (Focuspuller_Ui.Py) Cleanup no longer fails on deleted meta names it can't retrieve.

Change
~~~~~~

- (Browsers) Removed Redundant Image view chunk size override.
- (Minibrowser) Reduced Image loading count to 20 vs 200 to speed up UI load time.

Misc
~~~~

- (Focuspuller_Ui.Py) Fixed a UI error while trying to pull data from a broken meta node setup.


1.4.8 (2022-05-31)
------------------

Change
~~~~~~

- (Minibrowsers) Update minibrowserpathlist import.
- (Zoopackage) Removed Redundant startup commands in zoo_package.

Removed
~~~~~~~

- (Zoopackage) Removed Redundant blender layout files.


1.4.7 (2022-04-16)
------------------

Bug
~~~

- (Core) Incorrect function call for determining maya mode.

Change
~~~~~~

- (Cameramanager) Camera name combo to use shortname.


1.4.6 (2022-03-14)
------------------

Remove
~~~~~~

- (Imageplanetool) Remove Snapshot Replace action.


1.4.5 (2022-02-22)
------------------

Added
~~~~~

- (Focuspuller_Ui.Py) Auto cleans the scene for broken nodes, while deleting and while creating setups.
- (Imageplanetool.Py) Added new virtual slider capabilities.
- (Imageplanetool.Py) Added rotate and scale sliders.
- (Virtualslider) Add virtual slider code.

Bug
~~~

- (Focuspuller) Fix Maya focus camera using incorrect enable states for distance/fstop/region.
- (Focuspuller_Ui.Py) Main checkboxes now work with nothing selected.
- (Imageplanetool.Py) Virtual slider reset issues fixed.

Change
~~~~~~

- (Doc) Minor doc for image plane tool.
- (Imageplanetool.Py) Faster code added, inViewMessage for opacity. Documentation tweaked.
- (Imageplanetool.Py) Removed rotate and scale buttons.
- (Imageplanetool.Py) UI layout tweaks.
- (Virtualslider) Switch to constants instead of strings for directions.


1.4.3 (2022-01-18)
------------------

Change
~~~~~~

- (Mayascenes.Py) Now supports "Maya" and VRay as renderers.


1.4.1 (2021-11-3)
-----------------

Bug
~~~

- (Layout) Fix color button widths.
