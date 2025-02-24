=========
ChangeLog
=========


1.1.19 (2023-08-22)
-------------------

Added
~~~~~

- (Multiimportreference.Py) Help page added to the Multi Import Reference tool.

Change
~~~~~~

- (Toolpalette) Change Definition type to Action Type for better clarity in naming.


1.1.18 (2023-08-11)
-------------------

Added
~~~~~

- (Multiimportreference.Py) Added new tool to import or reference a file multiple times.
- (Zoo_Utility_Tools_Shelf.Layout) Added new tooltips for the Utilities shelf icon.

Bug
~~~

- (Zooshelfpopup.Py) Fixed bug where the tooltips were not showing on the main shelf icons.

Misc
~~~~

- (Commands) Update imports from commands.


1.1.17 (2023-06-22)
-------------------

Misc
~~~~

- (Hostengine) Switch to using HostEngine.


1.1.16 (2023-05-03)
-------------------

Added
~~~~~

- (Nodeeditor) LeftToRight and rightToLeft tools added to node editor alignment.
- (Default_Definitions.Py) Added Zoo Shelf (Floating Window) to default definitions.
- (Zooshelfpopup.Py) Single line floating Zoo shelf UI.

Change
~~~~~~

- (Selectionsets.Py) Selection Sets UI is now out of beta status.


1.1.15 (2023-04-05)
-------------------

Added
~~~~~

- (Selseticonpopup.Py) Addeed the ability to open the popup window as both a create selection set window as well as an icon window.
- (Selseticonpopup.Py) Moved the selection set popup ui to the correct location in this repository.


1.1.14 (2023-03-02)
-------------------

Added
~~~~~

- (Selectionsets.Py) Added new tool "Zoo Selection Sets", mostly working.
- (Selectionsets.Py) Added support for setting icons.

Change
~~~~~~

- (Selectionsets.Py) UI changed to have a popup window for icons. Still a WIP.


1.1.13 (2023-01-25)
-------------------

Added
~~~~~

- (Setattributemultiple.Py) Added tool for setting attributes on multiple objects at once. Only supports float at the moment.

Change
~~~~~~

- (License) Update copyright for 2023.


1.1.12 (2022-12-03)
-------------------

Bug
~~~

- (Qt) Fix Layouts having the same parent causing Qt logs to be output of linux/OSX.


1.1.11 (2022-05-31)
-------------------

Change
~~~~~~

- (Zoopackage) Removed Redundant startup commands in zoo_package.


1.1.10 (2022-04-16)
-------------------

Added
~~~~~

- (Attributes.Createattribute() ) Helper function for creating attributes with non-keyable settings.
- (Attributes.Visibilityconnectobjs() ) Added function for connecting a control visibility attribute to control the visibility of many other nodes.
- (Joints.Jointdrawhide() ) To show/hide a joint list.
- (Layers.Py) Added a dedicated module to render layers and refactored existing code.

Bug
~~~

- (Core) Incorrect function call for determining maya mode.

Change
~~~~~~

- (Attributes.Addproxyattribute() ) Better handling of non-keyable setting in the channelbox and refacotr to many files.
- (Attributes.Addproxyattribute() ) To better handle non-keyable settings.
- (Attributes.Createenumattrlist() ) Changed function to be consistent with others and better handling of non-keyable settings.

Removed
~~~~~~~

- (Convertrotateuplist() ) Removed function convertRotateUpList() and replaced with a dictionary in zoocore, refactor for many files.


1.1.9 (2022-03-14)
------------------

Added
~~~~~

- (Reloadwindows_64.Png) Icon added for `Reset All Zoo Windows` and separator added in the shelf menu.
- (Shelf) Added reset all Windows to Shelf.

Change
~~~~~~

- (Channelboxmanager.Py) Title no longer contains "beta".


1.1.8 (2022-02-22)
------------------

Change
~~~~~~

- (Shelf) Migrate shelf button to new button type.


1.1.7 (2022-02-04)
------------------

Added
~~~~~

- (Channel Box Manager) Added functionality for all buttons. Tool is fully operational.
- (Channel Box Manager) Added more options and larger UI with options for opening windows, adding separator attrs and proxies. WIP UI, half done.
- (Channel Box Manager) New tool added with icon.

Change
~~~~~~

- (Channel Box Manager) Tool renamed with (beta) at end.
- (Zoo Renamer) Big refactor of self.properties UI now pulls from self.properties.widget.value and removed old link code.

Enhancement
~~~~~~~~~~~

- (Zoo Renamer) Added Force Rename with padding.
- (Zoo Renamer) Added constraints support for suffixing.


1.1.6 (2022-01-18)
------------------

Added
~~~~~

- (Matrix Tool) Added help URL to tool.


1.1.5 (2021-12-08)
------------------

Added
~~~~~

- (Matrix Tool) New modeling freeze button added.
- (Matrix Tool) New tool matrixtool.py adds various matrix related tools for artists. Added freeze to matrix and unfreeze from matrix tools.
