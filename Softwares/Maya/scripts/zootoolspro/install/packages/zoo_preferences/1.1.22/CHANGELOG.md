=========
ChangeLog
=========


1.1.22 (2024-05-10)
-------------------

Change
~~~~~~

- (Qt.Py) PySide6 compatibility updates.


1.1.21 (2024-02-21)
-------------------

Bug
~~~

- (Stylesheets) Fix QCheckbox Disabled checked state image being displayed in unchecked state.
- (Stylesheets) Improvements to treeview styling with different themes, though not 100% complete.

Change
~~~~~~

- (Assets) Take into account of the global option to avoid copying default assets to user assets.


1.1.20 (2023-11-10)
-------------------

Added
~~~~~

- (Prefui) Added "Load ZooTools Shelf on Start Up" to Preferences UI.

Bug
~~~

- (Stylesheetui) Fix incorrect use of MayaColorBtn and color space conversion.


1.1.19 (2023-08-22)
-------------------

Change
~~~~~~

- (Toolpalette) Change Definition type to Action Type for better clarity in naming.


1.1.18 (2023-08-11)
-------------------

Added
~~~~~

- (Zoo_Preferences_Actions.Py) Added new tooltips for the Zoo Preferences Window.


1.1.17 (2023-06-22)
-------------------

Change
~~~~~~

- (Actions) Update actionplugins to use new Host Engine code.
- (Prefswidget) Only show startup options in maya.
- (Tooldata) Update old tooldata imports to use zoo.core version.

Remove
~~~~~~

- (Core) Moved Preferences core into zootools main, left behind constants, assets and stylesheet due to dependencies.


1.1.16 (2023-05-10)
-------------------

Change
~~~~~~

- (Preferenceswidget) Temporary hide stylesheet edit and add buttons.


1.1.15 (2023-05-03)
-------------------

Bug
~~~

- (Preferencesui) Manually settings the preferences path through the lineEdit will now correctly setting the zoo preferences json file.
- (Preferencesui) Setting new preferences Location will no longer always append "zoo_preferences" path to user specified folder, to avoid any double ups and to allow custom folder names.

Change
~~~~~~

- (Preferencesui) Delayed requesting for moving/setting the preferences folder until save or apply is clicked.
- (Preferencesui) Moving a folder to an existing location will now request whether to delete it before moving or simply cancel.


1.1.14 (2023-04-05)
-------------------

Added
~~~~~

- (Prefs) Added autoLoad plugin to prefs.
- (General_Prefswidget.Py) Added tooltips to new prefs checkbox start up buttons.

Bug
~~~

- (Startup) Fix startup file to avoid importing modules before they exist due to later zoo version logic.

Change
~~~~~~

- (Preferences) Removed prefutils module because individual interface access function has moved into their specific repo.


1.1.13 (2023-01-25)
-------------------

Bug
~~~

- (Window) Fix window dpi scaling issues on main window.
- (Preferencesui.Py) Fixed 4k double sized zoo preferences window.

Change
~~~~~~

- (License) Update copyright for 2023.


1.1.12 (2022-10-26)
-------------------

Change
~~~~~~

- (Mainwindow) Removed show argument from init function due to visual artifacts it can cause due to events.
- (Preferenceui) Fix window position saving.


1.1.10 (2022-07-20)
-------------------

Change
~~~~~~

- (Stylesheet) Halved treeview item padding.
- (Interfaces) Moved coreInterface function to interfaces.coreInterfaces and depreciated prefutils to decouple preferences from other packages.


1.1.9 (2022-05-31)
------------------

Bug
~~~

- (Gui) Delay show event til after all contents has been initialized.
- (Stylesheet) Fix changing stylesheet via preferences causing UIs to go transparent.
- (Stylesheet) General fixes to Zoo window styling.
- (Stylesheet) QAbstractItemView disabled items not changing color.
- (Stylesheet) QComboBox dropdown icon in disabled state continues to display white icon, now removes the icon.
- (Stylesheet) QHeaderView disabled state continues to display white icon.
- (Stylesheet) Removed redundant Forced QTextEdit and QLineEdit style.
- (Stylesheet) StackItem QLineEdit style overriding all child line edits which disabled tableviews edit styling.
- (Stylesheet) TreeView branch style not matching item style.
- (Themedict) Poor initialization of themedict.

Change
~~~~~~

- (Minibrowser) Moved minibrowser to zoo_pyside.
- (Stylesheet) Initial Color Pass on TabWidget style.
- (Stylesheet) Merged DirectoryTitlebar and titleBar style keys to avoid extra complexity.
- (Stylesheet) Merged directoriesTree and QTreeView style to avoid extra complexity.
- (Stylesheet) Updated QMenu styling and added numberLine widget to styling.


1.1.8 (2022-04-16)
------------------

Bug
~~~

- (Core) Fix Widget already has a layout warnings.
- (Core) Fix defaultPreferencePath hard coding the root.
- (Core) Incorrect function call for determining maya mode.
- (Coreinterface) Fix userPreferences method hardcoding paths.

Change
~~~~~~

- (Assets) Asset browser currentPackagePath to use inspect module lib instead of flaky work around.
- (Core) Reading user_preference root path from installation now comes from zoo manager class.
- (Core) Reduced the time it takes to load the UI.
- (Pluginmanager) Added name to plugin manager for logging.
- (Prefutils) Removed redundant local imports.
- (Stylesheet) Added table view up/down arrow icons.
- (Stylesheet) Fix missing QMenu selection and background colors in stylesheet.

Remove
~~~~~~

- (Core) Removed flake8.


1.1.7 (2022-03-14)
------------------

Bug
~~~

- (Core) Fix specific use of ntpath instead use os.path.

Misc
~~~~

- (Misc) Support for category folders in asset preferences.


1.1.6 (2022-02-22)
------------------

Bug
~~~

- (Assets) Fix Preferences being saved multiple times when creating directories.
- (Browsers) Fix sub folders which are prefixed with "." getting included.
- (Browsers) Temporarily force a preferences save.
- (Core) Settings method to correctly handle settings key queries.

Change
~~~~~~

- (Shelf) Moved preferences tool action from zoo_maya.


1.1.5 (2022-02-04)
------------------

Added
~~~~~

- (Collapsableframethin) Styling for CollapsableFrameThin.
- (Styling) Added Disabled colors for JoinedRadiobutton.

Bug
~~~

- (Assets) FileNotFoundError raised when assets pref folder doesn't exist and the folder was deleted between 2 session.

Change
~~~~~~

- (Collapsableframelayout) Rename to CollapsableFrame.
- (Core) Move pluginManager interface initialization to iterable.
- (Doc) Additional doc for preferences.
- (Qss) Style changes for JoinedRadioButton and Divider.

Fix
~~~

- (Styling) Apply disable style only on disable.
- (Styling) Json issue for styling.


1.1.4 (2022-01-18)
------------------

Change
~~~~~~

- (Preferencesconstants.Py) Added "VRay" and "Maya" as optional renderers to Zoo > General Preferences.


1.1.3 (2021-12-18)
------------------

Added
~~~~~

- (Joined Radio) Joined radio button styling.


1.1.1 (2021-12-08)
------------------

Added
~~~~~

- (Change Log) Add change log stub.
- (Logging) Add additional debug logging for assets preferences.
- (Preferences) More debug messages for preferences.

Bug
~~~

- (Minibrowser) Fix incorrect signal parameters for minibrowsers.
- (Minibrowser) Fix issue where empty asset folders can clear preferences.
