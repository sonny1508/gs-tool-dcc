=========
ChangeLog
=========


1.3.32 (2024-05-10)
-------------------

Bug
~~~

- (Iconview) Fix setting ViewMode for pyside6.
- (Toolsetresizer) Fix Resizer activating when mouse button isn't pressed.

Change
~~~~~~

- (Qt.Py) PySide6 compatibility updates.


1.3.31 (2024-01-22)
-------------------

Added
~~~~~

- (Toolsetresizer.Py) Added margins options for the resizer.


1.3.30 (2023-11-10)
-------------------

Bug
~~~

- (Displaymodebutton) Ensure DisplayModeButton mousePressEvent is forced down.


1.3.29 (2023-08-22)
-------------------

Change
~~~~~~

- (Toolpalette) Change Definition type to Action Type for better clarity in naming.


1.3.28 (2023-06-22)
-------------------

Change
~~~~~~

- (Action) Update actionplugins to use new Host Engine code.
- (Action) Update actionplugins to use new Host Engine code.
- (Toolsetlaunch) Update to use new Host Engine code when launching toolset UIs.
- (Toolsetlaunch) Update to use new Host Engine code when launching toolset UIs.

Remove
~~~~~~

- (Prefs) Removed redundant pref widget.


1.3.27 (2023-03-02)
-------------------

Bug
~~~

- (Zooicons) Fix zooIcon ui load time.

Change
~~~~~~

- (Zooicons) Support for searching.


1.3.26 (2023-01-25)
-------------------

Added
~~~~~

- (Definedhotkeys.Py) All toolset hotkeys now have the advancedMode option in the kwargs to open in advanced mode rather than compact.
- (Toolsetui.Run.Py) ToolsetSetMode() function can now set a toolset UI to be in compact 0 or advanced 1 mode. openToolset() function now has advancedMode=True kwarg.

Bug
~~~

- (Toolsetcache) Fix toolset frames not being removed from cache.

Change
~~~~~~

- (License) Update copyright for 2023.


1.3.25 (2022-12-03)
-------------------

Bug
~~~

- (Crash) Fix Crash when dragging a toolset on linux with PyQt5.
- (Qt) Fix QT depreciated methods for treeItem for better interoperability.


1.3.24 (2022-11-17)
-------------------

Bug
~~~

- (Crash) Fix crash when using PyQt5 and Disconnecting signals.
- (Crash) Fix crash when using PyQt5 and initializing ToolsetWidgetItem.
- (Qt) Fix Pyqt5 compatibility issues.
- (Toolseticonpopup) IndexError raised when determining size when there's no buttons.


1.3.23 (2022-11-16)
-------------------

Bug
~~~

- (Qt) Fix Pyqt5 compatibility issues.


1.3.22 (2022-10-26)
-------------------

Change
~~~~~~

- (Toolseticonpopup) Replaced QDialog with ZooWindow.
- (Toolsetui) Moved responsibility of window position management to core.
- (Toolsetui) Removed show argument from init function due to visual artifacts it can cause due to events.


1.3.21 (2022-05-31)
-------------------

Added
~~~~~

- (Toolpalette) Added toolset type plugin.

Bug
~~~

- (Toolsetui) Delay show event til after all contents has been initialized.
- (Properties) ComboEditRename property type to only store the text not the value to avoid blindly casting datatypes to text which can result in errors or crashes.
- (Properties) Temp solution for properties failing when hit a maya object that no longer exists, This should really be handled by the toolset instance.

Change
~~~~~~

- (Toolsetui) Reorder initialize code and culled duplicate calls to resize, applyStylesheet.
- (Toolsetsui) Port zoo icons toolsets from zoo_core.


1.3.20 (2022-04-16)
-------------------

Bug
~~~

- (Core) Incorrect function call for determining maya mode.
- (Toolsetui) Use of dpiscaling before a QApplication instance has been created resulted in silent failure in batch or mayapy.

Change
~~~~~~

- (Core) Remove redundant typing hinting.
- (Icon) Move sortDown,sortUp icons to zoo_core.
- (Pluginmanager) Added name to plugin manager for logging.
- (Resizer) Removed the use of QApplication.setOverrideCursor instead now uses widget.setCursor.


1.3.19 (2022-03-14)
-------------------

Change
~~~~~~

- (Mixins) Remove redundant savePopup method in mixin in favor of the minibrowser version.
- (Properties) If setting a property value errors, provide better information about the property.

Removed
~~~~~~~

- (Minibrowsermixin) Removed redundant methods and signals due to minibrowser updates.


1.3.18 (2022-02-22)
-------------------

Added
~~~~~

- (Minibrowserthumbnail) Add extra supported class to Toolset.

Change
~~~~~~

- (Minibrowserthumbnail) Move out of maya only for toolsets.
- (Shelf) Migrate shelf button to new button type.


1.3.17 (2022-02-04)
-------------------

Added
~~~~~

- (Core) Add additional skipChildren code.

Bug
~~~

- (Registry) Toolsets no longer fails zootools startup if a toolset layout path is invalid.
- (Registry) Toolsets registry being initialized on import causes import errors depending on what package get loaded.
- (Toolseticonpopup) Fix Qt complaining about layout iconPopup already having a layout.

Change
~~~~~~

- (Core) Fix local import statements in ActionPlugin.
- (Core) Move pluginManager interface initialization to iterable.
- (Doc) Code documentation and clean up for Toolsets.

Fix
~~~

- (2017) Error on update code for 2017.
- (Core) Move skipChildren back into autoLinkProperties.


1.3.16 (2022-01-18)
-------------------

Change
~~~~~~

- (Ignore) ToolsetRightClickMenu to use partial instead of lambda.


1.3.15 (2021-12-08)
-------------------

Added
~~~~~

- (Toolsets) Toolsets startup.

Change
~~~~~~

- (Toolsets) Move toolset actionplugins.
