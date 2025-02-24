=========
ChangeLog
=========

1.0.5 (2024-05-03)
------------------

Bug
~~~

- (Compatibility) Fix Python2 Compatibility issue with using list.clear().

1.0.3 (2024-01-22)
------------------

Bug
~~~

- (Sourcecodeeditor) Fixed new tabs not have language syntax highlighter set.


1.0.2 (2023-11-10)
------------------

Bug
~~~

- (Debugger) Fix dialog being registered with zoo as a string.
- (Sourcecodeeditor) Fix root output directory not being created before use.

1.0.0 (2023-10-05)
------------------

Added
~~~~~

- (Sourcecodeeditor) Added basic automatic saving of tabs to preferences under prefs/assets/scriptEditor.


1.0.12.dev (2023-08-22)
-----------------------

Change
~~~~~~

- (Toolpalette) Change Definition type to Action Type for better clarity in naming.


1.0.11dev (2023-08-11)
----------------------

Added
~~~~~

- (Zoo_Dev_Utilities_Shelf.Layout) Added new tooltips for the Dev utilities shelf icon.


1.0.10dev (2023-06-22)
----------------------

Bug
~~~

- (Unittestui) Fix status look up failure when testClass doesn't exist in the internal cache.

Change
~~~~~~

- (Actions) Update actionplugins to use new Host Engine code.


1.0.10.dev (2023-06-22)
-----------------------

Bug
~~~

- (Unittestui) Fix status look up failure when testClass doesn't exist in the internal cache.

Change
~~~~~~

- (Actions) Update actionplugins to use new Host Engine code.


1.0.8ev (2023-03-02)
--------------------

Added
~~~~~

- (Icons) Added 32 pixel icons made specifically for selection sets.

Change
~~~~~~

- (Unittestui) Replaces model and treeview to TreeViewPlus, for searching and standardized zoo behaviour.


1.0.7dev (2023-01-25)
---------------------

Bug
~~~

- (Unittest) Fix main window dpi scaling issues.

Change
~~~~~~

- (Pycharmdebugger) Added InputDialog to change the port number.


1.0.6.dev (2022-11-17)
----------------------

Bug
~~~

- (Crash) Fix crash when creating a QSplitter when using PyQt5.


1.0.5.dev (2022-11-16)
----------------------

Bug
~~~

- (Qt) Fix Pyqt5 compatibility issues.


1.0.4.dev (2022-10-26)
----------------------

Change
~~~~~~

- (Mainwindow) Removed show argument from init function due to visual artifacts it can cause due to events.
- (Windows) Fix window position saving.


1.0.2.dev (2022-01-18)
----------------------

Added
~~~~~

- (Pycharm) Added Remote debug to menu.


1.0.2.dev (2022-05-31)
----------------------

Added
~~~~~

- (Pycharm) Added Remote debug to menu.
- (Sourcecodeeditor) Source code editor which contains python execution and log output window added.

Bug
~~~

- (Core) DataChanged.emit raises error due to incorrect number of arguments in maya 2017.
- (Sourcecodeeditor) Compiling which results in a syntax error wouldn't log into the output widget.
- (Unittestui) Reuses scripteditor state from zoo_maya. rely on unittest to handle new scenes.

Change
~~~~~~

- (Menus) Remove Redundant menu icon.
- (Menus) Update for new menu code.
- (Shelf) Added back in shelf layout.
- (Unittest) Removed latest maya dependency from UI.
- (Unittestui) Removed icons which no longer work.

Misc
~~~~

- (Misc) - fix error handling for py3/2.
- (Misc) Ability to run unit test from script editor.
- (Misc) Ability to run unit test from script editor.
- (Misc) Changed all Qt imports to zoovendor.Qt.
- (Misc) Port of the following modules to zoo.core: zlogging, plugin, pluginmanager,modules,classtypes,envregistry.
- (Misc) Port to ZooWindow base class.
- (Misc) Renamed unittest class definition.
- (Misc) Replace runner with zootools runner.
- (Misc) Top level package test suite display with package name.


1.0.1.b.8 (2023-04-05)
----------------------

Bug
~~~

- (Core) Fix addSkip and AddFailure using wrong core method.

Removed
~~~~~~~

- (Selseticonpopup.Py) Moved the selection set popup ui to the correct location in the zoo_utility_tools repo.
