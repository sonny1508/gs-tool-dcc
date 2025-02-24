=========
ChangeLog
=========


1.2.32 (2023-11-10)
-------------------

Bug
~~~

- (Shadermanager.Py) Emmision weight slider can now go above one.


1.2.31 (2023-08-22)
-------------------

Change
~~~~~~

- (Toolpalette) Change Definition type to Action Type for better clarity in naming.


1.2.30 (2023-08-11)
-------------------

Added
~~~~~

- (Zoo_Shader_Tools_Shelf.Layout) Added new tooltips for the Shader shelf icon.


1.2.29 (2023-04-05)
-------------------

Change
~~~~~~

- (Preferences) Ported shader tools pref interface function from preferences repo.


1.2.28 (2023-03-02)
-------------------

Added
~~~~~

- (Hsvoffsettool.Py) Added new tool HSV Offset tool for offsetting hue saturation and value on all selected objects/shaders.

Bug
~~~

- (Shadermanager.Py) RenameShaderEvent() is working again if renaming shaders that don't have suffixes.

Removed
~~~~~~~

- (Colortester.Py) Removed test UI colorTester.py should not be in Zoo.


1.2.27 (2023-01-25)
-------------------

Added
~~~~~

- (Hsvpopup.Py) Small popup window dedicated to setting diffuse color and offsetting HSV on multiple shaders. Called by marking menu or a hotkey, draws at mouse pointer location.

Bug
~~~

- (__Init__.Py) Popupuis not found in python 2 because of missing init module.

Change
~~~~~~

- (License) Update copyright for 2023.


1.2.26 (2022-12-03)
-------------------

Bug
~~~

- (Qt) Fix Layouts having the same parent causing Qt logs to be output of linux/OSX.


1.2.25 (2022-10-26)
-------------------

Misc
~~~~

- (Matchswatchcolorspace.Py) Tooltips for the UI added.
- (Mayashaders.Py) Browser always defaults to all for simplicity for the user.
- (Zoo_Shader_Tools_Shelf.Layout) Removed extra seperator in the shader shelf menu.


1.2.24 (2022-09-29)
-------------------

Misc
~~~~

- (Default Multi Renderer Materials) Added missing shader thumbnails for defaults.
- (Matchswatchcolorspace.Py) New tool for converting shader swatches in the current scene from an old rendering color space. Eg Linear to ACES or ACES to Linear.
- (Shader Preset Multirenderer Defaults) Shaders are now all metalness, thumbnails and info files all updated.
- (Shaderbuilderui.Py) Disabled the shaderBuilder ui temporarily for release.
- (Shaderbuilderui.Py) Is active again in the Zoo menus.
- (Shadermanager.Py) Shadermanager now supports ACES and other color spaces and swatches are correctly displayed as SRGB in the Qt UI.
- (Shaderpresets.Py) Save button is now in the main UI. Added ( shaderpresets.py ) Now supports ACES ie rendering and display spaces with changes made in Zoo Maya.


1.2.23 (2022-07-25)
-------------------

Misc
~~~~

- (Mayashaders.Py) Columns in the browser set to 3 and not 1.
- (Shaderbuilderui.Py) Added a rough working version of Shader Builder (Alpha). Only supports PolyHaven.com preset. Text and Checkboxes are not hooked up yet.
- (Shaderbuilderui.Py) Enabled the UI.
- (Shaderbuilderui.Py) Shader Builder Alpha tool is disabled in the menus for 2.7.0 release. BugFix ( shadermanager.py ) renameShaderEvent() method no longer renames itself if the event is triggered twice.


1.2.22 (2022-07-20)
-------------------

Change
~~~~~~

- (Browsers) Removed Redundant Image view chunk size override.
- (Minibrowser) Reduced Image loading count to 20 vs 200 to speed up UI load time.


1.2.21 (2022-05-31)
-------------------

Bug
~~~

- (Shadermanager) Updating combo doesn't update shader list combobox.
- (Shadermanager.Py) Colors from the UI are correctly applied as srgb. Swatches are srgb from the UI not linear.
- (Shadermanager.Py) Preset is applies as SRGB color previously was applying as linear color.
- (Shaderpresets.Py) Paste Attrs is now working correctly from the new shaderInstances code.
- (Shaderpresets.Py) Select the shader now selects the shader in component mode.

Change
~~~~~~

- (Minibrowsers) Update minibrowserpathlist import.
- (Shaderpresets.Py) Multi-Renderer Shader Presets. Advanced UI has been removed and buttons are now in the compact mode. Transfer, Copy/Paste/Paste Attrs/ Select Shader and Select objects.


1.2.19 (2022-03-14)
-------------------

Added
~~~~~

- (Convertshadersui.Py) Maintains connections to supported texture attributes while converting shader of different types.
- (Mayashaders.Py) Added "All" renderer and also filters our Maya shaders in other renderers to.

Bug
~~~

- (Definedhotkeys.Py) Adding open_alembicAssets() hotkey fix due to name change.
- (Rendermanpxrsurface.Py) PXR surface is working again and added emission too.
- (Shadermanager.Py) Color is correctly converted to SRGB space so color swatches better match the shader colors.
- (Shaderpresets.Py) Tooltip changed to correctly explain sliders.

Change
~~~~~~

- (Mayashaders) Remove redundant code.
- (Shadermanager.Py) Handles new texture connections code.

Remove
~~~~~~

- (Shadertools) Removed Legacy Code.


1.2.18 (2022-02-22)
-------------------

Added
~~~~~

- (Virtualslider) Virtual slider to shader presets.

Bug
~~~

- (Shaderpresets.Py) Fixed bug where the specular color wasn't being set properly on the thumbnail virtual sliders.

Change
~~~~~~

- (Minibrowser) Unhide filter button.
- (Shaderpresets.Py) Large changes to the virtual sliders, rearranging modifier keys, added inViewMessages. Documentation and tooltips.
- (Shelf) Migrate shelf button to new button type.
- (Virtualslider) Add to minibrowser.
- (Virtualslider) Switch to consts and extra documentation.


1.2.17 (2022-02-04)
-------------------

Change
~~~~~~

- (Collapsableframelayout) Rename to CollapsableFrame.
- (Convert Shaders) Renamed to "Universal Convert Shaders".
- (Convert Shaders (Multi-Renderer) ) Renamed tool, from Convert Shaders.
- (Maya Shaders) Renamed to "Maya Shader Presets".
- (Minibrowser) Unhide info button.
- (Shader Manager) Renamed to "Universal Shader Manager".
- (Shader Manager (Multi-Renderer) )Renamed tool, from Universal Shader Manager.
- (Shader Presets) Renamed to "Universal Shader Presets".
- (Shader Presets (.Ma/.Mb) ) Renamed tool, from Maya Shader Presets.
- (Shader Presets (Multi-Renderer) ) Renamed tool, from Universal Shader Presets.
- (Shadermanager) Use new CollapsableFrameThin.


1.2.16 (2022-01-18)
-------------------

Added
~~~~~

- (Convert Shaders) Added help URL to tool.
- (Exportabcshaderlights.Py) Added function setShaderAttrsZscnInstance() for setting shader instances.
- (Misc Shader Types) Added small functionality across all shader types.
- (Rendererconstants.Py / Shdmultconstants.Py) Added various constants.
- (Shader Manager) Added `Affect Multiple` functionality to shader manger. Multiple shaders can now be changed by the UI.
- (Shader Manager) Supports unknown shader types, setting assign and copy paste. Attrs are disabled though.
- (Shadermixin.Py) Now supports shaderTypes being changed with the shaderTypeCombo.
- (Shaderpresets_Legacy.Py) Is the old Shader Preset UI, will be deleted soon.
- (Shaderpresets_Legacy.Py) Is the old Shader Preset UI, will be deleted soon.

Bug
~~~

- (Shader Manager) Setting from presets resets None attributes to defaults.
- (Shader Manager) Undo works for all sliders and delete.
- (Shader Manager And Shadr Presets) Better handle unique name suffixing internally in the instance.

Change
~~~~~~

- (Convertshadersui.Py) UI now has a renderer icon menu and conforms and updates all other renderer UIs.
- (Menu Items) Shader icons/menu items have been rearranged in the shelf, toolsets and Zoo menu.
- (Randomize Shaders) Upgrade now supports VRay and Maya shader types.
- (Randomshaders.Py) Now uses shaderTypes for creation rather than by renderer.
- (Shader Manager) Shadermanager_new.py has been updated and is now shadermanager.py, the old shadermanager.py is now shadermanager_legacy.py and will be removed.
- (Shader Manager) UI Layout rearranged to better show Create by type.
- (Shader Presets) Large upgrade of Shader Presets to match the new backend, new shader support VRay and Maya, new attribute support metalness and emission.
- (Shader Suffix, Displacement Manager) Ignore "VRay" and "Maya" renderers until they are later supported.
- (Shaderbase.Py) Better dictionary support for attributes.
- (Shaderpresets.Json) Grey shader presets renamed to _grey to appear at the top of the list in Shader Manager.
- (Shaderpresets.Py) Shader Presets now saves the shader via a zoo shaderInstance object. Metalness etc now supported on save.
- (Shaderswapsuffix.Py) Now supports "Maya" as a renderer, still more to do.
- (Shaderswapsuffix.Py) Shader Swap UI now supports all new shader types as suffixes.
- (Shdmultconstants.Py) Removes standardSurface shader in versions 2019 and below.
- (Swap Shader By Suffix) Renamed Shader Swap tool to Swap Shader By Suffix, avoids confusion with Convert Shaders.
- (Swap Shader By Suffix, Convert Shaders) Icons switched as works better.


1.2.14 (2021-12-18)
-------------------

Added
~~~~~

- (Convert Shaders) Added functional new UI and layouts.
- (Convert Shaders) Auto switches zoo preferences renderers.
- (Convert Shaders) Phong, PhongE, RedshiftMaterial, Lambert, PXRSurface, Blinn.
- (Convert Shaders) Prompts to load renderers.

Change
~~~~~~

- (Maya Shaders) More descript errors if no shaders selected.


1.2.11 (2021-12-08)
-------------------

Added
~~~~~

- (Blender) Get python code runnable in blender.
- (Change Log) Change log stub.
- (Maya Shaders) Help and readme to the dots menu in mayashaders.py.
- (Maya Shaders) Options to save as either MA or MB.
- (Maya Shaders) Right-click on the save button in mayashaders.py UI.

Bug
~~~

- (Change Renderer) Fix issue where changing renderer wouldn't update prefs.
- (Color Buttons) Fix colour button width.
- (Maya Shaders) Fix issue where shaders not saving properly.

Change
~~~~~~

- (Blender) Get code runnable in blender temp.
- (Blender) Remove maya toolsets from blender toolsets.
- (Zoo Package) Empty zoo_package settings and set in startup instead.
