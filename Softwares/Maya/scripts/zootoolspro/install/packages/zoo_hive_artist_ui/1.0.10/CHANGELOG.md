=========
ChangeLog
=========


1.0.10 (2024-05-23)
-------------------

Bug
~~~

- (Eyelids) Fix Joint ratio widgets not being created and deleted when count changes.


1.0.9 (2024-05-10)
------------------

Bug
~~~

- (Pyside6) Fix SpaceSwitch ui failing under PySide6.


1.0.8 (2024-05-03)
------------------

Added
~~~~~

- (Hive_Artist_Ui_Shelf.Layout) Added Mocap Feet Retargeter to the Hive menu, shelf.
- (Hivemirrorcopypasteanim.Py) Added buttons for flip and mirror pose.
- (Hivemirrorcopypasteanim.Py) Added mirror animation buttons, tooltips added.

Change
~~~~~~

- (Hivemirrorcopypasteanim.Py) Small tool change name. Now called `Hive Mirror Flip Animation`.

Misc
~~~~

- (Misc) Eye component UI.


1.0.7 (2024-02-21)
------------------

Bug
~~~

- (Componentlibrary) If a folder name exists multiple times we now merge component items under the same folder.
- (Styling) Component and template library styling fixes.


1.0.6 (2024-01-22)
------------------

Added
~~~~~

- (Bendy) Added limb settings to bendy limbs.
- (Addcustomrig.Py) Added Add Custom Rig Grp UI to the Hive menus and Hive Artist UI.

Bug
~~~

- (Spineik) Fix Spine Count position sliders not updating values live.
- (Twists) Fix twist position sliders not updating values live.

Change
~~~~~~

- (Fbxexporter) Change unity fbx version to 2020 and included 2022 in preset options.

Misc
~~~~

- (Hive_Artist_Ui_Menu.Layout) Added matchBakeAnim Added ( hive_artist_ui_shelf.layout ) Added matchBakeAnim Added ( hive_toolsets.layout ) Added matchBakeAnim Added ( addcustomrig.py ) Now with help page link.
- (Hive_Toolsets.Layout) Fixed bug regarding matchBakeAnim tool not being found.


1.0.5 (2023-12-05)
------------------

Added
~~~~~

- (Rigsettings) Added isHistoricallyInteresting to Rig Settings.
- (Misc) Added tooltips for various buttons in the Hive Artist UI, minor tweaks to Hive Setting labels.

Bug
~~~

- (Exporterui) Update unreal preset to use FBX 2020.


1.0.4 (2023-11-10)
------------------

Added
~~~~~

- (Quad) Added Bendy to quad leg UI.

Bug
~~~

- (Core) Fix AttributeError when no components exist.

Change
~~~~~~

- (Jointstohive) JointsToHiveGuides updated to latest core transformsToFKGuide version.

Misc
~~~~

- (Misc) Bendy quadruped component.


1.0.3 (2023-10-05)
------------------

Bug
~~~

- (Quadleg) Foot widget using wrong attributeDefinition.

Change
~~~~~~

- (Components) Added alignIkEndToWorld to ik limb UIs.


1.0.2 (2023-09-27)
------------------

Bug
~~~

- (Componentlibrary) Fix components not displaying in 2020 for new folder display.


1.0.1 (2023-09-27)
------------------

Added
~~~~~

- (Templatelibrary) Added the basics of a folder structure to the template UI.

Bug
~~~

- (Templates) Save existing template doesn't reuse the template path but always defaults to root hive template path.

Change
~~~~~~

- (Componentlibrary) Added Basic folder support.
- (Componentlibrary) Replaced Old Component library Widget with the preferred treeview solution.


1.0.0b17 (2023-08-22)
---------------------

Bug
~~~

- (Createcomponent) Fix double up of adding components to the data model resulting in an invalid UI state.
- (Refresh) Fix regression in UI refresh detecting component count difference.

Change
~~~~~~

- (Toolpalette) Change Definition type to Action Type for better clarity in naming.


1.0.0b16 (2023-08-11)
---------------------

Added
~~~~~

- (Hivejointstoguides_64.Png) Added Joints To Hive Guides tool icon.
- (Hive_Artist_Ui_Toolsets.Layout) Added Plane Orient tool to the Hive Artist UI side toolbar.
- (Hive_Toolsets.Layout) Added new tooltips for the Hive shelf icon.
- (Hiverigexportwidget.Py) Added save and load UI methods and assorted documentation.
- (Hiverigexportwidget.Py) Logic should be all working now, and error checking in place.
- (Hiverigexportwidget.Py) UI can populate from the scene for multiple rig names and frame ranges from timeline bookmarks and the game exporter UI data.
- (Hiverigexportwidget.Py) UI now supports multi batch export. New modes are not connected to logic WIP.
- (Jointstohiveguides.Py) Added ability to create a new rig if none exists in the scene while creating guide chains.
- (Jointstohiveguides.Py) Added help page link.
- (Jointstohiveguides.Py) Added new tool Joints To Hive Guides, mostly working, still needs a new icon. Added to shelves, menu and Hive UI.
- (Jointstohiveguides.Py) Added scale float box, joint create options and open Joint Tool window buttons. Tweaked tooltips.
- (Jointstohiveguides.Py) Added side combo properly which dynamically pulls from the Hive API.

Bug
~~~

- (Fkcomponent) Fix control creation failing if the parent control was yet to be created.
- (Window) Closing Hive UI wouldn't remove toolsetFrame from registry causing c++ error when accessing toolset frames in other tools.
- (Hiverigexportwidget.Py) Combo box now has namespaces in the name to differentiate between multiple rigs in the scene.
- (Jointstohiveguides.Py) Bug fixed sorting if hierarchy and added name so the component is named correctly.
- (Jointstohiveguides.Py) If only one joint is selected and hierarchy is checked will no longer fail.

Change
~~~~~~

- (Transformstofkguides) Added guide scale to transformsToFkGuides function.
- (Hive_Toolsets.Layout) Changed the name of the Hive toolset group to be "Rigging Hive Auto-rigger" to match other rigging toolsets.

Igore
~~~~~

- (Hiverigexportwidget.Py) Scene save UI settings node name changed to "zooHiveExportFbxUiSettings".


1.0.0b15 (2023-06-22)
---------------------

Bug
~~~

- (Vchain) Twist DGGraph had debug nodes being created.

Change
~~~~~~

- (Build) Building Guides which already display control vis will now just hide them.
- (Buildmodes) Added Guide Control visibility build state.
- (Actions) Update actionplugins to use new Host Engine code.
- (Rename) Renaming the rig will now autofill dialog with current rig name.


1.0.0b14 (2023-05-11)
---------------------

Added
~~~~~

- (Settings) Added Shapes hidden in outliner.

Bug
~~~

- (Blackbox) Added outliner refresh to live sync blackbox state change.


1.0.0b13 (2023-05-03)
---------------------

Added
~~~~~

- (Hiveguidealign.Py) Correct help web link.

Bug
~~~

- (Guidealign) Fix toggle Local LRA not being connected.
- (Naming) Changes made to field values never result in the config being saved.
- (Naming) Configuration not deleted from disk when there's no difference between the original and UI changes.

Change
~~~~~~

- (Pathwidget) FbxExport browser folder to be current scene directory.

Misc
~~~~

- (Misc) Added Guide alignment Toolset.

Removed
~~~~~~~

- (Utils) Moved strutils from zoo_core to core.


1.0.0b12 (2023-04-05)
---------------------

Added
~~~~~

- (Componentwidget) Added applySymmetry to component dotsMenu.
- (Templatelibrary) Added "Update Rig from Template" to templateLibrary.

Change
~~~~~~

- (Templates) UpdateFromTemplate will now to a validation pass and provide a user warning dialog if it failed.

Remove
~~~~~~

- (Core) Removed redundant placeholder tools.


1.0.0b11 (2023-03-16)
---------------------

Added
~~~~~

- (Applysymmetry) Added apply symmetry to component Widget dotsMenu.
- (Tools) Added force refresh for tools when requesting for a refresh.

Remove
~~~~~~

- (Core) Remove redundant tool plugins.


1.0.0b10 (2023-03-13)
---------------------

Added
~~~~~

- (Rigconfigui) Added use proxy Attributes checkbox to rig config.


1.0.0b9 (2023-03-02)
--------------------

Added
~~~~~

- (Armlegcomponent) Added bendy settings to arm and leg component UI.

Bug
~~~

- (Buildscript) BuildScript with multiple properties would override all properties for that buildScript.

Change
~~~~~~

- (Components) Updated arm/leg components with bendy option.


1.0.0b8 (2023-01-25)
--------------------

Bug
~~~

- (Creation) Ensure rig component cache is cleared before running build methods so the instance is synced to the scene.

Change
~~~~~~

- (Core) Fix addRig, addComponent not using ui tool plugins.
- (License) Update copyright for 2023.
- (Sceneunits) Check Scene units before building or creating to ensure scene is in cm until will support other units.
- (Tools) Tool plugin now supports return statement from the execute function.


1.0.0b7 (2022-12-03)
--------------------

Bug
~~~

- (Fbxexporter) Change save Scene pop up message to make it clearer.
- (Fbxexporter) Marking fbxExport as interactive for user messages as popups.

Change
~~~~~~

- (Namingconvention) Added HelpUrl.


1.0.0b6 (2022-11-17)
--------------------

Bug
~~~

- (Presetchooser) Fix incorrect PresetChooser icon.


1.0.0b5 (2022-11-16)
--------------------

Bug
~~~

- (Qt) Fix Pyqt5 compatibility issues.


1.0.0b4 (2022-10-26)
--------------------

Added
~~~~~

- (Mirrorconstants.Py) Added all Hive rig components and ids to mirrorconstants.py.
- (Mirrorconstants.Py) Control flip curve related constants for mirroring tools (will be meta data later).
- (Natalie_Buildscript.Py) Added custom animator selection sets to the natalie build script.

Bug
~~~

- (Components) Fix toggleLra failing.
- (Ikfk) Fix ikfk default combobox labels being reverse order.
- (Spaceswitching) Fix AttributeError raised when a constraint no longer exists but attempting to change the UI.

Change
~~~~~~

- (Mainwindow) Removed show argument from init function due to visual artifacts it can cause due to events.
- (Toolsets) Added rigging Misc to toolbar.
- (Window) Updated height to a better default size.
- (Windows) Fix window position saving.

Misc
~~~~

- (Templates) Various templates upgraded. Robots support stretch and new build scripts. Natalie has tweaks. Arms have auto-align off for fingers.
- (Hive_Artist_Ui_Shelf.Layout) Added tool Hive Mirror Paste Anim to the animation shelf.
- (Icons) Checkbox name fixed that was causing error.
- (Mirroranim.Py) Functions for copy/paste mirroring selected Hive controls for cycles and other.
- (Mirroranim.Py) Selection now restricted to transforms only for Hive mirror animation.
- (Selection.Py) Misc selection set helper functions added.
- (Hive_Artist_Ui_Shelf.Layout) Added tool Hive Mirror Paste Anim to the animation shelf.
- (Hivemirrorcopypasteanim.Py) Tool added auto set start end from timeline on tool open. Small refactoring.
- (Mirroranim.Py) Added some documentation and small refactor pass.
- (Hivemirrorcopypasteanim.Py) Added new tool UI Hive Mirror Paste Animation. All basics are working. Added to shelves.
- (Hivemirrorcopypasteanim.Py) Minor variable name refactor.
- (Icons) Checkbox name fixed that was causing error.

Remove
~~~~~~

- (Toollayout) Removed Legacy toolLayout code.


1.0.0b3 (2022-09-29)
--------------------

Added
~~~~~

- (Components) SpineIk now has a custom component UI.

Bug
~~~

- (Componentlibrary) Available components are now sorted.
- (Components) Fix missing HasStretch setting on vchain/arm/leg components.
- (Namingconvention) Fix typeError raised in Maya2020 due to py version differences for dict type.
- (Settings) Min/max not applied unless both have a value.
- (Templatelibrary) Available templates are now sorted.
- (Templates) Save Template required first selecting an existing template before saving.
- (Twists) Fix twist widgets not refreshing.

Change
~~~~~~

- (Components) Sort component side combobox.
- (Components) Support for flagging a component as beta.
- (Naming) Sort rule type combobox.
- (Spineik) Added squash profile edit button.
- (Templatelibrary) Rewrite of the template library widget to simplify behaviour.


1.0.0b2 (2022-07-25)
--------------------

Bug
~~~

- (Polishrig) Regression polishing rig disables UI.


1.0.0b1 (2022-07-20)
--------------------

Added
~~~~~

- (Namingconvention) First Pass Naming convention UI and component/rig config override widget.

Bug
~~~

- (Exportui) AttributeError raised when hive artist UI isn't open during export.
- (Mayareferencetoolset) AttributeError raised if hive artist UI isn't open.
- (Uiinterface) UiInterface memory leak due to dangling UI widget references not being removed.

Change
~~~~~~

- (Armcomponent) Replace VChainComponent custom widget for arm component.
- (Cleanup) Imports auto cleaned up.
- (Components) Renamed Advanced settings to General settings.
- (Core) Core global instance removed, access now through uiinterface class.
- (Preferences) Added hive interface frontend function to preferences.interfaces.hiveartistuiinterfaces.
- (Window) Updated window title for beta.

Misc
~~~~

- (Misc) Added Naming Configuration UI.

Remove
~~~~~~

- (Componentsettings) Remove Side widget from component settings since it already exists on the item header.


1.0.0a15 (2022-06-05)
---------------------

Change
~~~~~~

- (Shelf) Hive UI Icon color is now blue to match the other menu items.


1.0.0a14 (2022-05-31)
---------------------

Added
~~~~~

- (Spaceswitching) Added Support for user defined space switching per component.

Bug
~~~

- (Hiveartistui) Delay show event til after all contents has initialized to avoid flicker.
- (Loadtemplate) Add or remove rig dialog displays even if there's no rig.
- (Loadtemplate) Results in multiple core reloads.
- (Refresh) Fix rename not update component UIs.
- (Ui) Fix retrieving UI instance corrupting all zoo windows.

Change
~~~~~~

- (Components) Disable editing of component settings when not in guide mode.
- (Stylesheet) Fix Side name widget having a different stylesheet not displayed in the component titlebar.
- (Ui) Better Support for display UI arguments into MainWindow.
- (Uilayer) Better component settings widget spacing.


1.0.0a13 (2022-04-16)
---------------------

Bug
~~~

- (Core) Fixed numerous Qt warnings related to multiple layouts being parented to the same QWidget.

Change
~~~~~~

- (Componentwidget) Delay creation of component settings widget until expansion happens, speeding up load times.
- (Core) Fix syntax warnings in python 3.9+.
- (Resizer) Removed the use of QApplication.RestoreCursor as QT handles this now in the base.


1.0.0a12 (2022-03-14)
---------------------

Bug
~~~

- (Componentsettings) Legacy maya attribute type long not supported in the UI.
- (Fbxexport) Ensure FBX Plugin is Loaded.

Change
~~~~~~

- (Components) Swapped vchaincomponent advanced settings layout to use CollapsableFrameThin widget.
- (Hive_Artist_Ui_Toolsets.Layout) Hive title now has been renamed to "Hive Auto.
- (Mayareferencewidget.Py) Title no longer contains "beta".
- (Rigexportwidget.Py) Title no longer contains "beta".


1.0.0a11 (2022-02-22)
---------------------

Bug
~~~

- (Logging) Layered stack traces are output when an error occurs instead of one.

Change
~~~~~~

- (Shelf) Migrate shelf button to new button type.

Remove
~~~~~~

- (Package) Removed redundant flake8 file.


1.0.0a10 (2022-02-04)
---------------------

Added
~~~~~

- (Fbxexport) Support for mesh and skin options.
- (Fbxexporttoolset) New Fbx export toolset.
- (Hive Export Fbx) Added "Mesh" and "Skinning" checkboxes and disable/enable behaviour. No logic yet.
- (Hive Export Fbx Tool) New icon added.
- (Hive Toolset Shelf) Hive is now visible in toolsets with the two tools specific to Hive.
- (Hiveartistuicore) New signals added to the core model. rigRenamed, rigDeleted, currentRigChanged, rigsChanged.
- (Mayareferencetoolset) New MayaReference export toolset.
- (Reference Model Skeleton Tool) New icon added.

Bug
~~~

- (Exportwidgets) Enforce correct file extensions for path widgets.
- (Fbxexport) Bindpose exporting DisplayLayers.
- (Loader) Ensure Hive artist UI only loads for 2020+, includes popup.
- (Rigmode) Fix Polish never being enabled on open.

Change
~~~~~~

- (Buildscripting) Support for buildscript properties.
- (Collapsableframelayout) Rename to CollapsableFrame.
- (Exporters) Handle scene requiring saving before exporting.
- (Hive Export Fbx) Small layout tweak.
- (Hive Reference Model Skeleton) Layout of UI upgraded.
- (Hive Reference Model Skeleton) Reference Model Skeleton renamed to Hive Reference Model Skeleton. Help link added.
- (Mayareferencewidget.Py) Added icon renamed tool, still wip.
- (Messagebox) Remove old qt message box.
- (Rigexportwidget.Py.Py) Large change to UI, renamed tool added presets and large UI layout changes.
- (Rigmodebutton) Tweak margins and spacing.
- (Rigmodebuttons) Shift spacing of buttons.
- (Rigmodebuttons) Switch to new JoinedRadioButton.


1.0.0a9 (2022-01-18)
--------------------

Change
~~~~~~

- (Hive Artist Ui) Slightly better refresh behaviour for hasTwist.


1.0.0a8 (2021-12-18)
--------------------

Added
~~~~~

- (Templatelibrary) Refresh template Library action.

Bug
~~~

- (Templatelibrary) Save template overrides without warning or request.

Change
~~~~~~

- (Templatelibrary) Save As to use currently select template name as the default field value.


1.0.0a7 (2021-12-8)
-------------------

Bug
~~~

- (Core) AttributeError when UI has been destroyed but signal still in effect.
- (Core) Creating a new rig was forced to use name "Rig" instead of hive internal defaults.
- (Templatelibrary) Open template location doesn't display warning.
- (Templatelibrary) Save select component as template display no warning when theres no selection.

Change
~~~~~~

- (Componentlibrary) Use components default name instead of the component type on creation.
- (Ui/Ux) Polish button replaced with radio button for better workflow.


1.0.0a6 (2021-11-16)
--------------------

Added
~~~~~

- (Componenttree) "Select From Scene" and "Highlight From Selection" actions to component tree.

Bug
~~~

- (Componentwidget) Fix AttributeError when changing component side name.
- (Componentwidget) Fix Hive guide settings min/max value not being set in the UI.
- (Componentwidget) Fixed parent widget not displaying component side label.
- (Core) Potential fix to c++ widget deleted error.
- (Ux) Legcomponent UI settings not having the same advanced settings option similar to vchain.


1.0.0a5 (2021-11-2)
-------------------

Added
~~~~~

- (Componentwidget) Added "Highlight from scene" action to component tree header.

Bug
~~~

- (Componentwidget) Fix AttributeError when changing component side name.
- (Componentwidget) Fix Hive guide settings min/max value not being set in the UI.
- (Componentwidget) Fixed legcomponent UI settings not having the same advanced settings option similar to vchain.
- (Componentwidget) Fixed parent widget not displaying component side label.
- (Core) Potential fix to c++ widget deleted error.
- (Shelf) Correct Hive Artist UI Shelf position.


1.0.0a4 (2021-11-3)
-------------------

Bug
~~~

- (Core) Fix enum widgets triggering event on construct.
- (Core) Fix numeric widget change with the same value triggering a hive change.


1.0.0 (2023-09-19)
------------------

Added
~~~~~

- (Quadleg) Added component Model Widget.

Remove
~~~~~~

- (Quadleg) Removed redundant component library item widget.
