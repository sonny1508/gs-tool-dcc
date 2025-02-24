=========
ChangeLog
=========


1.3.7 (2024-05-10)
------------------

Change
~~~~~~

- (Qt.Py) Update to Qt.py "1.4.0" with changes for QFont.setWeight in pyside2, QRegEx and QRegularExpression in PySide2.
- (Unreal) Update unreal to use pyside6.


1.3.6 (2024-05-03)
------------------

Bug
~~~

- (Compatibility) Fix Python2 Compatibility issue with using list.clear().
- (Mayastartup) Fix displayError occuring when logging config is > logging.ERROR.
- (Mayastartup) Fix stacktrace logging outputting twice.
- (Preferences) Fix Creation of preference folders where all would be created instead of just the user_pref.
- (Strutils) ShortenPath AttributeError occurred due to using wrong var.

Change
~~~~~~

- (Qt.Py) Added QRegularExpressionValidator.


1.3.5 (2024-02-21)
------------------

Bug
~~~

- (Plugins) Discovery of plugins would fail under OSX when the Mounted volume type doesn't support extended attributes ie. NTFS.

Change
~~~~~~

- (Assets) Added Environment variable to avoid copying assets to user preferences folder.


1.3.4 (2024-01-22)
------------------

Change
~~~~~~

- (Pip) Fixed pipInstallRequirements not passing the --upgrade flag if required.
- (Profiling) Moved profiling module from zoo_core to this package.
- (Reload) Delay garbage collection until all zoo modules are deleted, improving general reload time.


1.3.3 (2023-12-05)
------------------

Bug
~~~

- (Pip) Ensure provided package versions are passed through and allow pip arguments.


1.3.2 (2023-11-10)
------------------

Bug
~~~

- (Core) Temporary removal of core plugin manager instance until engine host has been updated to use core plugins.


1.3.1 (2023-08-11)
------------------

Added
~~~~~

- (Unreal) First pass integration of the ZooTools Menu into unreal.

Bug
~~~

- (Docs) Fix doc failuring to build due to preferences not being initialized.
- (Unreal) Fix missing python path for the engine.

Change
~~~~~~

- (Undo) Merged undo into zootools.py for better maya registration.


1.3.0 (2023-06-22)
------------------

Added
~~~~~

- (Preferences) Port Preferences core from zoo_preferences for next around of configuration updates.
- (Qt) Updated Qt.py to 1.3.8 and added QIdentityProxyModel since we don't need to support PySide.

Bug
~~~

- (Reload) Fix Preferences not correctly shutting down on reload/shutdown.

Change
~~~~~~

- (Mayazooundo) Undo now longer needs to handle internal undoqueue.
- (Preferences) ZooTools Manager instance now passed to preferenceManager as dependency.
- (Startup) Host engine implemented to allow extended Zoo tools into other Host Applications i.e unreal.
- (Tooldata) Update old tooldata imports to use zoo.core version.


1.2.29 (2023-05-03)
-------------------

Added
~~~~~

- (Utils) Moved strutils from zoo_core to core.

Change
~~~~~~

- (Processes) Added logging to calling subprocess.


1.2.28 (2023-04-06)
-------------------

Bug
~~~

- (Package) Fix Regression in package saving.


1.2.27 (2023-04-05)
-------------------

Bug
~~~

- (Package) Fix Regression in package saving.


1.2.26 (2023-04-05)
-------------------

Added
~~~~~

- (Commands) Install Package now supports installing packages from zip files.
- (Packages) Added install and uninstall package startup functions.
- (Resolver) Added support for a global site-packages folder for pip installed packages.
- (Versioning) Added helper function for incrementing a version by level ie. major,minor,patch,alphaBeta.

Bug
~~~

- (Install) Fix inPlace package install using incorrect path if custom path provided.
- (Install) Fix package install not updating descriptor cache.
- (Unittests) Fix failing unittests.

Change
~~~~~~

- (Commands) Run function to return command function results.
- (Core) Moved private Script runner function to util.modules allowing for py scripts to be run by filePath.
- (Packages) Added support for managing pip install requirements per package.


1.2.25 (2023-03-02)
-------------------

Bug
~~~

- (Changeloggenerator) Fix changelog generator from git always sorting old versions.
- (Gitwrapper) Fix error when no tags exists on a repo.


1.2.24 (2023-01-25)
-------------------

Change
~~~~~~

- (License) Update copyright for 2023.


1.2.23 (2022-12-03)
-------------------

Change
~~~~~~

- (Documentation) Added docstring example to documentation.


1.2.22 (2022-11-15)
-------------------

Change
~~~~~~

- (Qt) Update Qt.py to 1.3.7.

Removed
~~~~~~~

- (Vendor) Removed unused json logging lib.


1.2.21 (2022-09-29)
-------------------

Bug
~~~

- (Logging) Ensure Maya Logger doesn't create duplicate handlers.
- (Logging) Py2 missing function fix.


1.2.20 (2022-07-20)
-------------------

Change
~~~~~~

- (Mayashutdown) Ensure internal repeat last storage is reset.
- (Pluginmanager) Better performance when registering a class.


1.2.19 (2022-06-01)
-------------------

Bug
~~~

- (Logging) Failure to set global zoo log level when the stdlib logging level name has changed.

Change
~~~~~~

- (Logging) Added error log with stacktrace to maya startup/shutdown.


1.2.18 (2022-05-31)
-------------------

Added
~~~~~

- (Libs) Added back port of mock lib for maya py2.

Bug
~~~

- (Changeloggeneration) Error occurs when a commit message contains an invalid sub expression.
- (Core) ValueError raised on OSX when import ctypes.
- (Preferences) Patching root paths doesn't support multiple languages.

Change
~~~~~~

- (Documentation) Improve readability of code-block.
- (Libs) Update six.py lib to 1.16.0.
- (Maya) Added error message to (un)initialize plugin.
- (Pluginmanager) LoadAllPlugins to pass through keyword args to all plugins.
- (Resolver) Logger error with file path when environment fails to load.


1.2.17 (2022-04-16)
-------------------

Added
~~~~~

- (Core) Added data cache folder path to zootools to allow for temp files.

Bug
~~~

- (Core) Dynamic module importing under py3 didn't add the module to sys.modules.
- (Core) Returning the dottedPath from an absolute path on unix/OSX systems returns incorrect paths for paths not under a python path.
- (Mayaplugin) Zootools doesn't load in mayapy or batch mode.
- (Qt.Py) Fix missing QWindow.

Change
~~~~~~

- (Docs) General fixes to documentation errors.
- (Documentation) Fix missing sentence in vscsetup.
- (Maya) Use updated artist palette launch code.
- (Pluginmanager) Now Supports loading modules which don't live under a python path.
- (Pluginmanager) Now supports log naming per instance, giving better informative log messages.

Misc
~~~~

- (Misc) Fix preferences path for OSX.


1.2.16 (2022-03-14)
-------------------

Change
~~~~~~

- (Documentation) Rewrote version control setup documentation for new dev installer.

Misc
~~~~

- (Misc) Shell cmd fixes.


1.2.15 (2022-02-22)
-------------------

Bug
~~~

- (Descriptors) Fix descriptor plugin for package not be reused.
- (Gitdescriptor) Fix git descriptor Package already exists error when resolving local path.
- (Logging) Modules not using zlogging module.


1.2.14 (2022-02-04)
-------------------

Added
~~~~~

- (Cachepackages) GitDescriptor install now supports maintaining the ".git" if needed.
- (Docgenerator) Added support for launching the webbrowser.
- (Documentation) Added vsc setup page.
- (Documentation) Ported Code overview page from the site.

Bug
~~~

- (Changelogparser) Fix IndexError when parsing a commit message which doesn't fit our syntax.
- (Gitchangelog) Fix several errors related to commit message parsing.

Change
~~~~~~

- (Docstrings) Updated changelog.py docstrings.
- (Documentation) Added missing changelog.rst to api reference page.
- (Pluginmanager) Remove old interface argument supporting a non-iterable.


1.2.13 (2022-01-2022)
---------------------

Bug
~~~



1.2.12 (2021-12-17)
-------------------

Added
~~~~~

- (Core) Added Rst Zoo Changelog parser utilities.
- (Docs) Added descriptor plugins to docs.
- (Gitcore) Support finding commits between 2 commits not just to HEAD.
- (Gitcore) Support for converting git commits into a formatted Changelog.

Change
~~~~~~

- (Descriptors) Moved descriptor plugins into separate folder.


1.2.11 (2021-12-8)
------------------

Change
~~~~~~

- (Misc) Port actions and descriptor types to use Plugin Manager.
- (Misc) Port all logging to use zoo tools logging manager.


1.2.10 (2021-11-15)
-------------------

Added
~~~~~

- (Misc) Added optional flag for cprofiler on startup via environment variables.
- (Misc) Docgenerator command to now includes changelog per package.

Change
~~~~~~

- (Misc) Package startup/shutdown no longer uses importlib.


1.2.9 (2021-10-26)
------------------

Change
~~~~~~

- (Misc) Qt.py vendor lib updated to version 1.3.6 .


1.2.8 (2021-09-21)
------------------

Bug
~~~

- (Misc) Docs folder missing from installed packages.
- (Misc) Maya undo stack not support nested zoocommands.
- (Misc) Source code being embed in documentation generator.


1.2.7 (2021-08-02)
------------------

Change
~~~~~~

- (Misc) Added Sphinx Documentation Generator CLI Command.
- (Misc) Fix importError where zoo_core has yet to be loaded. Ported required modules.
- (Misc) Helper function.
- (Misc) Support for skipping package startup script execution in the API.


1.2.6 (2021-05-22)
------------------

Bug
~~~

- (Misc) Fix issue where startup scripts wasn't being found.
- (Misc) Ignore plugins which don't have a valid name.

Change
~~~~~~

- (Misc) Port of the following modules to zoo.core: zlogging, plugin, pluginmanager,modules,classtypes,envregistry.
- (Misc) Provide package helper to resolve an environment variable in package context.
- (Misc) Support platform and self tokens in package.json expressions.


1.2.5 (2021-05-22)
------------------

Bug
~~~

- (Misc) Fixing failing unittests.

Change
~~~~~~

- (Misc) Support for environment variables in path descriptors.


1.2.4 (2021-05-16)
------------------

Bug
~~~

- (Misc) Unicode environment variables causing subprocessing to fail.


1.2.3 (2021-05-10)
------------------

Bug
~~~

- (Misc) Fix package version config being empty as a fallback when not loading in maya.
- (Misc) Maya 2022 startup security handling.
- (Misc) Maya plugin unable to load without user setup script.

Change
~~~~~~

- (Misc) Ported zooundo from zoo_maya.
- (Zoo_Core) .
- (Zoo_Core) .
- (Zoo_Core) .


1.2.2 (2021-04-05)
------------------

Bug
~~~

- (Misc) Cmd fixing exit codes.
- (Misc) Fix linux shell command.
- (Misc) Fix zoo_cmd exitcode.
- (Misc) Py3 update fixes.

Change
~~~~~~

- (Misc) Fix .pyc being included on package release and copying.
- (Misc) Jsonlogger update to latest.
- (Misc) Six update to latest.
- (Misc) Support {install} token in package descriptor paths.


1.2.1 (2020-12-29)
------------------

Change
~~~~~~

- (Misc) Basic update to documentation formatting.
- (Misc) Qt.py updated to 1.3.3.


1.2.0 (2020-12-22)
------------------

Change
~~~~~~

- (Misc) Removal of pathlib2 and scandir thirdparty libraries.


1.1.21 (2020-11-07)
-------------------

Added
~~~~~

- (Misc) Support to turn off maya plugin autoload.


1.1.20 (2020-09-13)
-------------------

Added
~~~~~

- (Misc) Added env command to embed zoo into current process.
- (Misc) Running zoo_cmd with no arguments displays help instead of embedding environment.


1.1.18 (2020-04-11)
-------------------

Added
~~~~~

- (Misc) Added createPackage command.


1.1.17 (2020-03-22)
-------------------

Added
~~~~~

- (Misc) Config property to set admin mode.
- (Misc) Descriptor can now be serialized to dict.
- (Misc) Ported reload function from zoo_core.

Bug
~~~

- (Misc) Fix python namespacing.
- (Misc) ReleasePackage command enforces version argument.


1.1.15 (2020-03-01)
-------------------

Added
~~~~~

- (Misc) Added support for build version as part of the api and setup commands.


1.1.14 (2020-02-23)
-------------------

Bug
~~~

- (Misc) Maya Extension Plugin to avoid loading menu when running through mayabatch or mayapy.


1.1.13 (2020-02-09)
-------------------

Added
~~~~~

- (Misc) Added displayName and description to package.py.
- (Misc) Provide the ability to return all repo commits after a certain tag.

Bug
~~~

- (Misc) Adding Author, email, description to zoo_package.json.
- (Misc) Fix package class not maintaining original data as a cache.
- (Misc) Fix string_types check argument error.
- (Misc) Refactor artistpalette boot to be in artist palette repo instead of plugin.


1.1.12 (2020-01-12)
-------------------

Bug
~~~

- (Misc) Fix regression where packageInstall command name was changed.
- (Misc) Support for git descriptor ssh.


1.1.11 (2019-12-15)
-------------------

Bug
~~~

- (Misc) Standardized commands.


1.1.10 (2019-12-02)
-------------------

Bug
~~~

- (Misc) Zoo_cmd syntax command not found.


1.1.9 (2019-12-01)
------------------

Bug
~~~

- (Misc) TypeError when loading json.


1.1.8 (2019-11-16)
------------------

Bug
~~~

- (Misc) Fix typeError when running setup command.
- (Misc) Removed windows specific error when running setup command.


1.1.7 (2019-11-15)
------------------

Bug
~~~

- (Misc) Fixed IOError when running setupcommand when backup folder already exists.


1.1.6 (2019-11-14)
------------------

Bug
~~~

- (Misc) Fixed maya plugin log display a false positive.
- (Misc) Removed redundant packages.
- (Misc) Zootools fails to load when dynamically loading packages into the environment.


1.1.5 (2019-10-27)
------------------

Bug
~~~

- (Misc) Import Naming fix when running custom package startup.


1.1.4 (2019-10-27)
------------------

Bug
~~~

- (Misc) Removed Git dependency to bundle zootools packages.


1.1.2 (2019-09-15)
------------------

Bug
~~~

- (Misc) Maya module scripts directory not being detected on linux.
- (Misc) Preferences default path using double forward slash.
- (Misc) ReleasePackage command not install package when specified.


1.1.1 (2019-09-15)
------------------

Bug
~~~

- (Misc) Fix bundlePackages using old install package command args.


1.1.0 (2019-09-15)
------------------

Added
~~~~~

- (Misc) Added CHANGELOG.md.
- (Misc) Descriptors can now support uninstalling.
- (Misc) Docstring updates.
- (Misc) Providing example on creating a Rez package for zootoolspro.
- (Misc) Setup CLI Command option for supporting copying .git folder.
- (Misc) Updated CLI Commands to use subParsers which provides better validation, grouping and less code.

Bug
~~~

- (Misc) Fix importlib importError on py2.
- (Misc) Package.delete method no longer errors due to the use of os.rmdir, now uses shutil.rmtree.
