=========
ChangeLog
=========


1.7.45 (2024-05-23)
-------------------

Added
~~~~~

- (Zapi) Added hasControllerTag helper function.
- (Zapi) ControllerTag function helper.


1.7.44 (2024-05-10)
-------------------

Bug
~~~

- (Zapi) Fix creating IKHandle would not resolve to zapi node object if the name isn't unique.


1.7.43 (2024-05-03)
-------------------

Added
~~~~~

- (Mayaapi) Helper method to create a motionPath.
- (Zapi) Added setCVPositions to nurbCurve.
- (Zapi) ResetTransformToOffsetParent method added to DagNode.
- (Zapi) Added displayLayer helper methods to add nodes.
- (Arnoldhdri.Py) Added basic support for Arnold exposure on the HDRI light, though not doing anything atm.
- (Brtransferskincluster.Py) Added auto rename skin cluster button and tooltips.
- (Definedhotkeys.Py) Added function for `Add Custom Rig Group` toolset tool.
- (Definedhotkeys.Py) Added functions for new Third Party suppoorted tools. Added Mocap Feet Retargeter Tool.
- (Filtertypes.Py) Added shapeFromTransformOrShapeTypeList() function returns shapes from give list of types and nodes.
- (Keyframes.Py) Added copy/paste keys from a source curve node.
- (Mirroranimation.Py) Added functions for flip mirroring animation for center objects and left/right sides.
- (Mirroranimation.Py) Added functions for flipping poses and animation. WIP.
- (Subdivisions.Py) Added support for nurbs surfaces and curves. Also added support for changing display smooth while in component mode.

Bug
~~~

- (Api) IterExtraAttributes skips attributes if name is partially in plug name, eg. skipVal in plugName. switched to using startswith.
- (Serialization) Serializing a Plug which is a MessageAttribute is an invalid operation due to not being json compatible, Message attributes now get skipped.
- (Zapi) Providing createPlusMinusAverage3D multiple plugs as input would only connect the last input plug.
- (Definedhotkeys.Py) Added function that handles the newer Light Editor in Maya.
- (Mirroranimation.Py) Fixes issue if the opposite control exists but the attribute does not.
- (Renderertransferlights.Py) Bugfix for errors related to Arnold's HDRI light attribute "exposure" changing to "aiExposure" from MTOA 5.3 and above.

Change
~~~~~~

- (Mirroring) Added mirroring by scale.
- (Unittest) Fix unittest fail due to message attribute no longer able to be serialized.

Misc
~~~~

- (Misc) Mesh component selection helpers.
- (Misc) Mesh docstrings.


1.7.42 (2024-02-21)
-------------------

Added
~~~~~

- (Animlayers.Py) Functions for toggling mute and deleting selected animation layers.
- (Attributes.Py) Constant with rotate and translate attrs.
- (Definedhotkeys.Py) Added Open Match And Bake UI.
- (Mocap.Py) Added functions to save motion capture data to the scene. So far only supports the match and bake tool.
- (Mocap.Py) Big additions to mocap.py now supporting the new UI in zoo_animation_tools.
- (Mocap.Py) Module for mocap setups. Added FootLocker class for locking down feet in Ik mode.
- (Mocap.Py) Renamed the class to match the UI. Setup Handles are now colored to match the controls.
- (Testuis.Py) Added a bunch of new UIs for the broad unit tests. Constraint Toolbox, Set Multiple Attributes, Match And Bake Animation, Mocap Feet Retargeter, Joints To Hive Guides, Add Custom Rig Group.

Bug
~~~

- (Markingmenu) Handle OSX special files when discovering layouts.
- (Metanode) Discovery of plugins would fail under OSX when the Mounted volume type doesn't support extended attributes ie. NTFS.
- (Twists.Py) Twists euler node parent axis must match the axis given. So y is zxy rot order, last letter is the parent. Avoids flipping hopefully.


1.7.41 (2024-01-22)
-------------------

Added
~~~~~

- (Batchconstraintbake.Py) Added misc functionality, more naming options, better handling of long names and existing namespaces. Adding scale on top of other types of constraints.
- (Batchconstraintbake.Py) Added Logic for constraint bake tool.
- (Batchconstraintbake.Py) Added selection functions.
- (Batchconstraintconstants.Py) Added biped UE5 joints to constants.
- (Batchconstraintconstants.Py) Updated constants still WIP.
- (Batchconstraintconstants.Py) Added mappings for biped skeletons. Will be moved to JSON later.
- (Timerange.Py) Added getSelectedFrameRangeOrPlayback() function which returns the selected timeslider range or playback range if nothing selected.

Bug
~~~

- (Curveserialization) Fix potential crash when serializing a curve if there's no cvs.
- (Mayaapi) Fix setParent failing when rotate attribute on a joint isn't free to change.
- (Splinebuilder) ObjectsAlongSpline not handling extras nodes created by pathAnimation.
- (Undo) Fix implicit closeChunk call closing the root chunk.

Misc
~~~~

- (Attributes.Py) Doc fix Added ( batchconstraint.py ) Added misc new functionality and error checks, some bugfixes. Changed ( batchconstraintconstants.py ) Cleaned up the ALL_MAPPINGS.
- (Batchconstraintbake.Py) Skips constraint if the target already has a constraint. Usually if the joint is in the dict twice which is valid. BugFix ( batchconstraintconstants.py ) Fixed issues with HIVE_BIPED_STRD_JOINTS, too many spine joints and typo on the middle finger.
- (Batchconstraintconstants.Py) Removing constraints now with proper right side name building, was renaming long names.
- (Batchconstraintconstants.Py) Cleaned up mapping lists, Hive UE and Light rigs supported. Advanced Skele and MGear taken out.


1.7.40 (2023-12-05)
-------------------

Added
~~~~~

- (Definedhotkeys.Py) New functions for new marking menus, bevelBool, deleteHistory and freezeTransform. Other misc tweaks.
- (Modelnodes.Py) New module for finding modeling nodes, mostly for bevel and extrude.
- (Selection.Py) Function for mesh selection warning for modelling tools.
- (Twists.Py) Added the class XyzRotDifferentiator() that builds an xyz rotation differences in angle units using quaternion math for stability. Flips at 180.

Bug
~~~

- (Mayaapi) SetPlugValue not support kByte type.
- (Shelves) Fix clear zoo shelves which use spaces in names never occurring.
- (Definedhotkeys.Py) Duplicate with offset is now working correctly.

Change
~~~~~~

- (Zapi) Added method to add utility nodes to Constraint class for tracking user node networks.


1.7.39 (2023-11-10)
-------------------

Added
~~~~~

- (Mayamath) Added helper function to get the angle between 3 points in radians.
- (Skeletonutils) Added helper function to get the mid-point vector of the hypotenuse line segment from 3 points.

Bug
~~~

- (Api) Attrtypes.mayaTypeToPythonType missing conversion of MFloatMatrix.
- (Coplanarmeta) Fix using the same warning message for both invalid hive rig and component having a worldUpVec.
- (Definedhotkeys.Py) Various modelling hotkeys now check for selection.
- (Metaviewportlight.Py) Deleting the Fix Viewport light rig now removes display layers too.
- (Renderers.Py) All browsers filter correctly once again according to the selected renderer.


1.7.37 (2023-09-27)
-------------------

Added
~~~~~

- (Assetsconstants.Py) PotsdamerPlatz texture default set to potsdamerPlatz_g.hdr, so the grey texture, no colors.
- (Potsdamerplatz_G.Hdr) Added grey potsdamerPlatz hdr texture.

Bug
~~~

- (Spaceswitching) Regression fix for error when removing metaData.

Change
~~~~~~

- (Unittest) Added flag to create new scene during tearDownClass method.


1.7.36 (2023-09-27)
-------------------

Added
~~~~~

- (Mayamath) Added functions for returning individual basis vectors.

Bug
~~~

- (Spaceswitch) Deleting constraint metaData ignores index 0.


1.7.35 (2023-09-19)
-------------------

Bug
~~~

- (Math) BezierSegments returns the wrong number of elements when the total segment count is greater than 2.
- (Meta) IterMetaChildren would return duplicates depending on the node network configuration.
- (Polevectorposition) Support inverting the direction of the poleVector.
- (Zapi) Lock function fails hard if the internal object is yet to be set.
- (Zapi) Maya Workaround fix for creating a spring solver.
- (Zapi) BuildConstraint function now supports joints when using Matrix constraintType, appropriately handles joint orients. note: no support for space switching with matrices yet.

Change
~~~~~~

- (Api) Better support for providing attribute shortnames.


1.7.34 (2023-08-22)
-------------------

Bug
~~~

- (Spaceswitching) InternalError raised during deletion.
- (Spaceswitching) RuntimeError raised during deletion of zero array element which isn't a valid operation.
- (Lookat) Math domain error raised due to Floating point precision issue when calculating the angle.

Change
~~~~~~

- (Toolpalette) Change Definition type to Action Type for better clarity in naming.

Updated
~~~~~~~

- (Definedhotkeys.Py) Updated the open_tweenMachinePopup() function for close on release functionality.


1.7.33 (2023-08-11)
-------------------

Added
~~~~~

- (Bezier) Added createBezierCurveContext function.
- (Cmds) Added sceneUnitsContext manager.
- (Issafename) Added isSafeName helper function for checking node names.
- (Mayamath) Added bezier related helper functions to mayamath module.
- (Splinebuilder) Support using a provided curve.
- (Zapi) Added kIkSpringSolveType constants to zapi.
- (Animbookmarks.Py) Added timeline bookmarks for querying and adding new bookmarks.
- (Constraints.Py) Added function selectConstraints(). Selects constraints on the selected object/s.
- (Create.Py) Added Parent option to the funciton createPrimitiveAndMatchMultiSel().
- (Create.Py) Added multi create function, builds objects at many other sel objects.
- (Create.Py) Added support for joints in createPrimitiveAndMatch().
- (Definedhotkeys.Py) Added open Maya's namespace editor hotkey.
- (Definedhotkeys.Py) Added snapToProjectedCenter().
- (Definedhotkeys.Py) Open_tweenMachinePopup() can appear slider at cursor and have popup behaviour (close when clicked off).
- (Matrix.Py) Added include children option for matrix freeze and unfreeze functions.
- (Saveexportimport.Py) Added functions for importing and referencing a file multiple times.

Bug
~~~

- (Api) Creating a node or renaming will now raise a NameError when the provide name is invalid.
- (Iterattributes) Skip attributes argument always ignored because partialName was always using shortName.
- (Serialization) SerializePlug not ignoring output plugs(not writable).
- (Splinebuilder) Spline builder ctrl size attributeError.
- (Zapi) When renaming a node if maintainNamespace is on and the namespace is the root namespace NameError would be raised.
- (Controls.Py) Fixed issues with all the zoo tracker attributes not being deleted, now deletes the mstrTempBreakTrack attr too.
- (Metamotionpathrig.Py) Fixed issues naming the meta node with a long object name or namespace.
- (Motionpaths.Py) Motion path can be built with negative axis alignments now. -z follow now works as expected.
- (Namehandling.Py) Shape nodes weren't being named correctly as per cmds.rename() so handling it ourselves.
- (Namehandling.Py) Shapenodes.py updates the renaming functions to mirror the namehandling functions. Shape nodes start at transformShape and then iterate up transformShape1 and transformShape2.

Change
~~~~~~

- (Naming) IsSafeName now supportin the name.
- (Undo) Merging core command code into maya command for simplicity.
- (Controls.Py) CreateControlCurve() function updates the renaming functions to mirror the namehandling functions and Maya. Shape nodes no longer are separated by an underscore so "ctrlShape" instead of the previous "ctrl_Shape".

Misc
~~~~

- (Undo) Regression on shutdown and reload not flushing undo before unloading plugin.


1.7.32 (2023-06-22)
-------------------

Added
~~~~~

- (Alignment) CoPlanar alignment functions now have support for converting to and from normal and matrix though expects the transforms to be in world.
- (Mayacommands) Added CoPlanar command basics.
- (Orientiterator) Added helper functions for orient joints using a lookat function.
- (Orientnodes) Fixed not handling leaf joints.
- (Zapi) Added MPLane to Zapi.
- (Zapi) Nodes now support the bool(Node) which returns existence including support for condition statements if node:.
- (Attributes.Py) GetLockedConnectedAttrsList() can also search for constraint connections.
- (Coplanarcommands.Py) CoPlanarCommand can skip end joints.
- (Coplanarmeta.Py) Arrow shape added to reference plane.
- (Coplanarmeta.Py) Methods for ingesting string short names from a UI.
- (Coplanarmeta.Py) Methods for validating the reference plane and start end nodes if deleted or new scene.
- (Coplanarmeta.Py) Reference plane always moves to first joint while being updated.
- (Coplanarmeta.Py) Reference plane auto scales to correct size based on distance between the start and end nodes.
- (Coplanarmeta.Py) Delete all reference planes including dead ref planes.
- (Coplanarmeta.Py) Set negative axis for World Axis Aligned mode.
- (Definedhotkeys.Py) Various stamp sculpt modes added.
- (Joints.Py) Added alignJointPlaneOrient() functions that support plane orient snap. Added ( planeorientmeta.py ) added functions related to UI helpers referencePlaneVisibility() matchRefPlaneToSel() orientRefPlaneToAxis().
- (Joints.Py) Added miscellaneous code to support the new style joint orient that supports vectors for each axis. alignJointZooSel() is the main function used by the UI.
- (Joints.Py) Added selectedStartEndJoints() function that returns first and last selected joints or transforms.
- (Joints.Py) More draw option support.
- (Joints.Py) Set scale compensate function.
- (Joints.Py) Support for orientation mirror in the mirror joint functions.
- (Joints.Py) AlignJointZoo() added maya.orientNodes() is undoable. alignJointPlaneOrient() supports skipEnd.
- (Joints.Py) Function that returns properties of a joint for UI.
- (Planeorientmeta.Py) Plane can now be an arrow for orienting up vecotr only no snap.
- (Planeorientmeta.Py) Select the reference plane.
- (Planeorientmeta.Py) Set Position Snap modes (not implimented).
- (Planeorientmeta.Py) Set start and end nodes selection.
- (Planeorientmeta.Py) ProjectAndAlign() method supports skipEnd.
- (Planeorientmeta.Py) Retrieve the normal of the arrow plane ref.
- (Renderertransferlights.Py) Added support in relevant functions for other maya unit scene types, inches, feet, yards etc while importing light presets. Mostly re scaling lights.
- (Scaleutils.Py) Added functions for setting and retrieving and converting Maya unit scales.

Bug
~~~

- (Alignnodesiterator) Incorrect behaviour when updating transformations due to hierarchy.
- (Alignment) CoPlanar createPolyPlaneFromPlane function now applies the plane normal as a rotation over passing to cmds axis flag for better user behaviour.
- (Api) SetParent doesn't support joint orient.
- (Constructplanefrompositions) Fix plane normal being incorrect when working with more than 3 points.
- (Curves) Fix linear curves not being supported when using createCurveFromPoints.
- (Projectandorientnodes) Fix End joint orientations not zeroing out.
- (Shelves) Fix Shelves only being removed on startup, now maintains the shelf by only deleting the shelf buttons.
- (Zoocommand) Maya Executor no longer needs its own undo/redo stack which was the cause of synchronization issues, reduces pythons reference counter of command, garbage collection is now easier to manage relating to maya.
- (Zoocommand) Memory leak occurs when mayas undo queue is flushed.
- (Definedhotkeys.Py) Soft select falloff functions were inverted now fixed.
- (Metaviewportlight.Py And Viewportlights.Py) Camera switching is working again with the new focal length changes.
- (Metaviewportlight.Py And Viewportlights.Py) Rotation link and unlink rotCamFollow() is working again after the focal length scale modifications.
- (Testuis.Py) Dead UI was accidentally included and is causing errors.

Change
~~~~~~

- (Alignnodesiterator) Added skipEnd argument to allow the end joint to be either aligned or not, useful for hive and co-planar behavior differences.
- (Coplanar) Basic support for hive guides.
- (Constructplanefrompositions) Explicitly handle 3 point vs N count.
- (Definitions) Update actionplugins to use new Host Engine code.
- (Definitions) Update actionplugins to use new Host Engine code.
- (Meta) Added iterMetaParents to metaBase for consistency.
- (Coplanarmeta.Py) Changed the name of the orientPlane geo and added show and hide vis methods.
- (Viewportlights.Py) Updated viewportCamGrpCtrls to account for cam focal length changes.
- (Viewportlights.Py) Updated viewportCamGrpCtrls to fix for cam focal length setup before build.

Misc
~~~~

- (Alignment) If skipEnd was specified then the returned array length was incorrect.


1.7.31 (2023-06-01)
-------------------

Bug
~~~

- (Triggers) Cycle import fix which only appeared under certain conditions.


1.7.30 (2023-05-11)
-------------------

Added
~~~~~

- (Mayaui) Added refreshOutliners helper function.
- (Zapi) Added autoKeyframe context.
- (Definedhotkeys.Py) Added hive toggle control panel nodes selected function. hiveToggleControlPanelNodesSel().
- (Grapheditorfcurve.Py) Added function for Graph Editor Expand and Collapse graphExpandConnections().
- (Viewportmodes.Py) Added function for retrieving editors from a panel type such as "graphEditor" in editorFromPanelType().

Bug
~~~

- (Bendy) Fix bendy control visiblity being connected but not hidden in channelBox.
- (Zapi) AllGimbalTolerances now handles autoKeyFrame correctly.


1.7.29 (2023-05-10)
-------------------

Added
~~~~~

- (Definedhotkeys.Py) Added sculpt brush options with alphas. Added sculpt volume/surface modes.
- (Hotkeymisc.Py) Name from hotkey function.

Bug
~~~

- (Definedhotkeys.Py) Soft select volume and surface mode round the wrong way.
- (Hotkeymisc.Py) All versions of Maya now use our own code for automatic hotkey generation from a name. Reducing potential errors with importing maya.app.TTF.

Change
~~~~~~

- (Resetattrs) Support network nodes in resetAttrs.


1.7.28 (2023-05-03)
-------------------

Added
~~~~~

- (Mayamath) Added AxisNames constant.
- (Mirrortransform) Changed transform mirroring to support scale.
- (Nodeeditor) LeftToRight and rightToLeft tools added to node editor alignment.
- (Shelves) Added shelfExists helper function.
- (Zapi) Helper methods for access transform Matrix plug elements easily with default as the first index.
- (Bindskin.Py) Added renameSelSkinClusters and hammerWeights functions.
- (Create.Py) CreatePrimitiveAndMatch() now supports most primitives.
- (Definedhotkeys.Py) Added Zoo Shelf Floating Window.
- (Definedhotkeys.Py) Added deformer hotkey entries for deformers with issues in multiple versions of Maya.
- (Definedhotkeys.Py) Added many more modelling functions for UIs and potential hotkeys later.
- (Definedhotkeys.Py) Added many more modelling functions for UIs topology and normals, still WIP.
- (Definedhotkeys.Py) Added many sculpting hotkeys.
- (Definedhotkeys.Py) Many modelling hotkeys added.
- (Definedhotkeys.Py) Modeling hotkeys for the Modeling Toolbox.
- (Duplicatemaya_32.Png) Added new colored icon.
- (Hotkeymisc.Py) New functions for finding hotkeys automatically from runtimeCommand names.
- (Hotkeymisc.Py) Hotkey code for tooltips added.
- (Normals.Py) New module for transfering vertex normals.
- (Sweepmeshmaya_32.Png) Sweep mesh icon that Maya is missing/cannot access.
- (Testuis.Py) Added many more UIs to the test ui constants.

Bug
~~~

- (Saveexportimport) IsCurrentSceneUntitled would always return False.
- (Definedhotkeys.Py) Tool settings no longer goes away when the sculpt knife brush is selected if it is already open.
- (Hotkeymisc.Py) Removed unicode keys with issues in python 2.

Change
~~~~~~

- (Core) Removed all uses of chdir.
- (Resetattrs) Split resetNodes into another function to handle resetting a list of specific attrs.
- (Toolpalette) Small safety improvement to avoid cache shelf instances inside the metadata of the internal shelfItem to allow better reuse.
- (Definedhotkeys.Py) Create primitives now also match.

Removed
~~~~~~~

- (Utils) Moved strutils from zoo_core to core.


1.7.27 (2023-04-05)
-------------------

Added
~~~~~

- (Assets) Added findMayaSceneByName helper function.
- (Menu) Added install package from zip to maya preferences menu.
- (Spaceswitching) Support for default space.
- (Uninstaller) Added deleting zoo tools cache folder during uninstaller.
- (Definedhotkeys.Py) Added modifier keys for animation and graph marking menus.
- (Grapheditorfcurve.Py) Make hold now gives a single message instead of reporting every curve.
- (Selectionsets.Py) Added the ability to set the priority attribute for the markingMenuSetup() function and others.
- (Selectionsets.Py) Addeed createSelectionSetsZooSel() function, that will create selection sets and increment the name if a set already exists.
- (Skelemirror.Py) WIP. Module for mirroring FBX skeletons and using them as skin cages.

Bug
~~~

- (Importfile) Fix utils importFile function error due to incorrect argument.
- (Lookat) LookAt function fails if a om2.MFloatVector is provided.
- (Maya2024) Zapi setting visibility with a float errors.
- (Mayacommandqueue) Fix Executor Raising IndexError when the first command ever runs errors on a command which isn't undoable.
- (Bakeanim.Py) Baking objects with proxy attributes Maya bug workaround, keys before baking non-keyed channels.
- (Bindskin.Py) Can copy skin weights from a component selection.
- (Bindskin.Py) Multiple skin clusters can be assigned in 2024, should probably add a warning popup later.
- (Shaderutils.Py) Selecting a shader with marking menu and hotkeys now factors in component selection.

Change
~~~~~~

- (Mayaenv) GetMayaLocation to support passing the version as an int.
- (Preferences) Updated all prefutils module imports with new namespace.
- (Definedhotkeys.Py) Added press and release for animation and graph editor marking menus.
- (Generalanimation.Py) Added variable in animation singleton.
- (Generalanimation.Py) Added variable in animation singleton.
- (Generalanimation.Py) Added variable in animation singleton.
- (Saveasdialogmamb) Now uses the users maya preferences setting for fileDialog style.
- (Uninstaller.Py) Changed uninstaller text to better reflect the uninstall options.

Removed
~~~~~~~

- (Prefs) Removed redundant prefs interface and prefs file.


1.7.26 (2023-03-23)
-------------------

Bug
~~~

- (Resetnodes) Reset nodes doesn't ignore Visibility attribute.

Change
~~~~~~

- (Resetnodes) Reset nodes now skip rotateOrder.
- (Resetnodes) Reset nodes now support skipping proxy attributes.


1.7.25 (2023-03-16)
-------------------

Bug
~~~

- (Bindskin.Py) Bindskin() now will apply correct settings to all skinClusters.
- (Bindskin.Py) PasteSkinWeightsSel() now pastes onto faces with and without skinning. No longer blocks from meshes/curves not found.

Change
~~~~~~

- (Bindskin.Py) FilterObjectsForSkin() added option to include returning skinned meshes.


1.7.24 (2023-03-13)
-------------------

Added
~~~~~

- (Zapi) Added helper method to return all proxyAttriubutes on a node.
- (Definedhotkeys.Py) Added the ability to change all marking menu hotkeys with ctrl/shift and alt kwargs.

Bug
~~~

- (Bindskin.Py) Paste Skin weights now filters to only support mesh/surface/curves.
- (Bindskin.Py) Paste Skin weights supports objects with no existing skin weights.
- (Bindskin.Py) Skinning can be assigned to nurbs curves.


1.7.23 (2023-03-07)
-------------------

Added
~~~~~

- (Definedhotkeys.Py) Added a new SubD Marking Menu.
- (Subdivisions.Py) Added functions for the new subD marking menu. For setting subDs on off hull or toggle. Also a tracker for the marking menu.

Bug
~~~

- (Bindskin.Py) CopiedSkinMesh was not a class variable and so was erroring if nothing had been copied while pasting.


1.7.22 (2023-03-02)
-------------------

Added
~~~~~

- (Nodeeditor) Add context manager to temporarily disable nodeEditor add to graph on create.
- (Bakeanim.Py) Bake now affects selected time range if there is a selection otherwise playback range.
- (Bindskin.Py) Added copy and paste skin weights which allows for pasting onto selected components, faces/verts etc.
- (Controls.Py) Function deleteTrackAttrsSel() for removing zoo tracker attributes in UIs.
- (Definedhotkeys.Py) Added missing open_animationPaths() tool.
- (Definedhotkeys.Py) Added new toolset tools to hotkeys Twist Extractor, Tween Machine, HSV Offset tools. Also popup versions of Tween Machine and HSV Offset.
- (Definedhotkeys.Py) Added open "Zoo Selection Set" toolset window.
- (Definedhotkeys.Py) Added open_iconLibrary() function to definded hotkeys.
- (Definedhotkeys.Py) Added the secondary function to selectionset markingmenu.
- (Definedhotkeys.Py & Motiontrail.Py) CreateMotionTrail() now rebuilds selected motion paths as well as building new motion paths on objects.
- (Filtertypes.Py) Added VRay shader and light node types to AUTO_SUFFIX_DICT.
- (Latticedeformation.Py) New module for creating squash and stretch setups/rigs with lattices. WIP.
- (Locators.Py) Added the ability to create many locators on many selected objects.
- (Motiontrail.Py) Added function selectMotionTrails().
- (Motiontrail.Py) Added motion trail set functions, and a number of small tweaks to have the UI and marking menus fully synced.
- (Motiontrail.Py) Functions for toggling display of motion trails and delete motion trail function.
- (Motiontrail.Py) Many changes and tweaks added createMotionTrailSelBools(), resetMoTrialDefaultDisplay(), return display state functions, and singleton class for tracking data.
- (Namehandling.Py) Added a couple more namespace functions.
- (Namehandling.Py) Added getUniqueNamePadded will approve the given name if unique or rename with padded numbers if not unique.
- (Natalie_Buildscript.Py) Minor tweaks, proxy attributes for hair vis now on the head and hips.
- (Selectionsets.Py) Ability to filter sets if they are hidden with the Zoo Vis Attribute.
- (Selectionsets.Py) Added a lot of code for the Zoo Selection Set Marking Menu and UI.
- (Selectionsets.Py) Added convinience function that sets up the marking menu for selection sets in a single function.
- (Selectionsets.Py) Added icon support for the sets list. Each set can be assigned an icon with new functions.
- (Selectionsets.Py) Added singleton tracker class with the ability to loop over selection sets related to the first selected object.
- (Selectionsets.Py) Added support for priority listing selection sets either by the set hierarchy in the outliner and a tag priority attribute. Affects default marking menu press while cycling through selection sets.
- (Selectionsets.Py) Numerous functions for managing selection sets and their contents and hierarchies.
- (Selectionsets.Py) While looping objects with the cycle sets feature, there are now checks to see if the selection has changed based on counting the selection at the beginning and end of each cycle.
- (Selectionsets.Py) SelectFirstRelatedSelSet() Selects the first set related to the current selection and added other related functions.
- (Shaderhsv.Py) Added methods for setting color in display space rather than only rendering space.
- (Twists.Py) Added cmds.rigging.twists for setting up twist joints. Measures the twist value between two options, can change the axis and invert, and set a destination attr.

Bug
~~~

- (Serialization) Serializing a maya node with external dependencies stores full path to the plugin resulting in errors between maya versions.
- (Zapi) ObjectSet.removeMembers raised AttributeError.
- (Curves.Py) XRay curve mode now reports message as info and not as a warning.
- (Definedhotkeys.Py) All marking menus now support floating windows (torn off).
- (Filtertypes.Py) FilterShapesFromList() function was mistaking custom nodes for shape nodes, now fixed. Affects the Renamer tool.
- (Motiontrail.Py) Fixed issues with the scale of the keyframe dots size and keyframe dots visibility when used from marking menu or UI. Now with custom trackable attributes.
- (Selection.Py) AddToSelectionSet() now creates a selection set and not an object set.
- (Selectionsets.Py) Fixed issue returning nodes inside selection sets.
- (Selectionsets.Py) SetsInScene() now correctly returns the selection sets in the scene and no longer includes deformers and tweak sets etc.
- (Viewportcolors.Py) Bugfix on Linux possibly OSX for alt b (cycle through background colors), returned list varies in order.

Change
~~~~~~

- (Unittest) Added unittests for add attribute.
- (Zapi) Supports setting a plug as a proxy attribute.
- (Generalanimation.Py) CreateMotionTrail() now syncs with UI and marking menu settings.
- (Motiontrail.Py) KeyFrameDotValue method and keyDotsValue_int variable added for Keyframe Dot Display Toggle.
- (Motiontrail.Py) Better name support and options for motion trails, new look and will rebuild if already exists too.
- (Shaderhsv.Py) SetValueOffset now calculates in display space rather than rendering space.


1.7.21 (2023-01-25)
-------------------

Added
~~~~~

- (Area And Directionallights) Assorted template code for directional and area lights for all renderers. Mostly stubs and not implimented yet.
- (Area Lights) Redshift and Arnold area lights basics are working and tested.
- (Areabase.Py) Added misc functions for supporting intensity and exposure for renderers that don't have exposure.
- (Areabase.Py) Adding support for exposure/intensity and normalize conversions.
- (Areabase.Py) Starting to add area light classes to zoo early WIP.
- (Areabase.Py & Renderers) Added scale compatibility between renderers.
- (Areabase.Py & Renderers) Adding intensity compatibility between renderers (vray still wip).
- (Assetsconstants.Py) Added light preset dictionaries including HDRI information for the internal light presets.
- (Assetsconstants.Py) Solves looped code issues, and keeps all the constants in one place.
- (Assorted) All classes and lightmulti modules now support suffixing and auto-suffixing.
- (Create.Py) Added nurbs circle to createPrimitiveAndMatch().
- (Curves) Added createBezierCurve() function.
- (Curves.Py) Added XRay Curves toggle functions.
- (Defaultassets.Py) Added importLightPresetAutoRenderer() method, imports lights and automatically uses the set renderer.
- (Definedhotkeys.Py) Added createSelectionSet hotkey with warning for earlier versions of Maya with Maya related bug.
- (Definedhotkeys.Py) Added marking menus and create nurbs cirlce and create CV Tool to defined hotkeys.
- (Definedhotkeys.Py) All toolset hotkeys now have the advancedMode option in the kwargs to open in advanced mode rather than compact.
- (Directional Lights) Redshift and Arnold directional lights basics are working and tested.
- (Directionalbase.Py) Directionalbase is mostly ready for testing, converted from areabase class.
- (Directionalbase.Py & Shader Types) Adding generic intensities so all lights match. VRay needs to be vraySun type.
- (Directionalbase.Py & Subclasses) Can now create with auto suffix.
- (Duplicates.Py) Added duplicateToComponentCenter() function for duplicating objects to verts or faces etc.
- (Lightconstants.Py) Added default paths to internal HDRI skydomes.
- (Lightconstants.Py) Added default value dict for area and directional lights.
- (Lightconstants.Py) Internal HDRI and light preset constants now included.
- (Lightconstants.Py) Maya viewport supported for Area and Directional lights types.
- (Lightingutils.Py) Added ZooLightsTrackerSingleton() class for tracking misc light data in the Maya session.
- (Lightingutils.Py) Added function for place reflection.
- (Lightsbase.Py) New base class for lights, added commonly used light code for area, directional and hdri.
- (Lightsmultiarea.Py) Maya viewport light supported.
- (Lightsmultiarea.Py) Support for passing in a dictionary while creating area lights.
- (Lightsmultiarea.Py) Supports creation with autorenderer.
- (Lightsmultidirectional.Py) Can now create with auto suffix and position while creating by renderer.
- (Lightsmultidirectional.Py) Maya viewport light supported.
- (Lightsmultihdri.Py) Added createDefaultHdriAutoRenderer() method which auto creates a HDRI skydome from the renderer set within Zoo Tools.
- (Lightsmultihdri.Py) Arnold HDRI created if Maya viewport set.
- (Lightsmultihdri.Py) Create now supports an image path including "auto" which uses the Zoo internal default HDRI skydome.
- (Matching.Py) Ability to set the up and aim vectors for matchToCenterObjsComponents().
- (Mayaarea.Py) Added support for Maya viewport area lights.
- (Mayaarea.Py & Vrayarea.Py) Added psuedo support for exposure/intensity as they don't exist natively.
- (Mayadirectional.Py) Added support for Maya viewport directional lights.
- (Metaviewportlight.Py) Added functions for creating, deleting and switch cams for light rigs and auto create delete functions.
- (Metaviewportlight.Py) Added setting of viewport modes to the create and delete functions.
- (Nodeeditor) Added LeftToRight RightToLeft Diagonal alignment.
- (Rendererconstants.Py, Shdmultconstants.Py, Lightconstants.Py) Added rendererIcons dictionary.
- (Rendererload.Py) Added function for returning zoo's primary renderer.
- (Renderertransferlights.Py) Added functions for easily creating area, directional and hdri lights for each renderer.
- (Renderertransferlights.Py) Added renderer checks in the create light functions, can auto create lights in Zoo's primary set renderer and dialogs for checking if the renderer isn't loaded.
- (Renderertransferlights.Py) Added support for Maya renderer, will create directional and hdri lights in Arnold.
- (Renderertransferlights.Py) Area and directional lights can now be created from component selection (vert, edge, face).
- (Renderertransferlights.Py) Directional light can be created with position flag. "selected", "camera" etc.
- (Sceneunits) Added helpers to determine which scene units maya is currently in.
- (Selectionset_Markingmenu.Py) Added a working version of the selection set marking menu, WIP but sets work and create.
- (Selectionsets.Py) Added selection set related code to maya.cmds.sets.selectionsets.py.
- (Setattrshapeautosel.Py) Function for automatically setting an attribute on the selected object/s or their shape nodes.
- (Shaderhsv.Py) Module designed to work with a UI for offsetting HSV on shader instances.
- (Shadermulti.Py) Added assign selected ability to createDefaultShadRenderer() functions.
- (Shadermulti.Py) Added copy shader from selection, paste shader selection and paste shader from attribute dict functions.
- (Shadermulti.Py) Added createDefaultShadRendererAuto() method for creating default shaders for the Zoo set renderer.
- (Shadermulti.Py) Added function assignValuesSelected() for setting preset overrides to selected shaders.
- (Shadermulti.Py And Shadertype Classes) Added automatic suffixing. Adds the shader type as a suffix auto as option on build and can add and remove the suffix at anytime with shadInst.addSuffix() or shadInst.removeSuffix().
- (Shdmultconstants.Py) Added Shader preset dict overrides for marking menu.
- (Toolsetui.Run.Py) ToolsetSetMode() function can now set a toolset UI to be in compact 0 or advanced 1 mode. openToolset() function now has advancedMode=True kwarg.
- (Viewportmodes.Py) Added function for turning all viewport mode settings on off, lights, AO, textures and aliasing.
- (Vrayarea.Py) Light scale is supported with uvSize.
- (Vrayarea.Py) Supports VRay light types intensities, exposure and normalization.
- (Zapi) Added MPoint to zapi.

Bug
~~~

- (Attributes.Py) SetAttrsShapeAuto() now reports success message correctly, added kwargs.
- (Cmdswidgets.Py) MayaColorSlider() emit blockers not getting passed through for setting colors.
- (Lightsmultiarea.Py) Added master module for creating and ingesting area lights of any renderer type. Tweaks on related files.
- (Lightsmultiarea.Py) All renderers and area light types are now successfully building and can be ingested.
- (Lightsmultiarea.Py) Short name issues solved regarding cmds.listRelatives().
- (Lightsmultidirectional.Py) Added master module for creating and ingesting directional lights of any renderer type. Tweaks on related files.
- (Lightsmultidirectional.Py) All renderers and light types are now successfully building and can be ingested.
- (Lightsmultidirectional.Py) Short name issues solved regarding cmds.listRelatives().
- (Lightsmultihdri.Py) Short name issues solved regarding cmds.listRelatives().
- (Lightsmultihdri.Py) Warnings for missing renderers muted by checking if the renderer is loaded in hdriInstancesFromScene().
- (Markingmenudynamic) No longer errors due to incorrect class resolve.
- (Markingmenuexample) Fix dynamic marking menu example.
- (Mayaapi) HasAttribute to work in full plug path ie. arrays.
- (Mayastandardsurface.Py) Bug fix when values are below zero for spec roughness.
- (Nodeeditor) Fix getting the current node Editor not supporting multiple tabs.
- (Nodemultibase.Py) Fixed issue with setting the name when it is already matching, and incorrectly adding a unique number to the name. Also only gets a unique suffix if there is a suffix.
- (Rendermanarea.Py) Renderman area is building, basics done, more work still needed.
- (Selectionsets.Py) SetsInScene() No longer returns other sets such as shadingGroups.
- (Viewportlights.Py) Fixed issue not finding the skydome light name after parent, added documentation.
- (Vrayarea.Py) VRay area is building, basics done, more work still needed.
- (Vraydirectional.Py) VRay directional is building, basics done, more work still needed.

Change
~~~~~~

- (Areabase.Py) Areabase is mostly ready for testing, converted from hdri base class.
- (Areabase.Py & Renderers) Assorted small changes VRay Area light is still a WIP.
- (Curves) CreateBezierCurve to generate knots as mayas default isn't great.
- (Defaultassets.Py) Now pull from assetsconstants.py.
- (Hdribase.Py & Renderers) Now all lights use the self.scaleMultiply value for setting generic scale.
- (Importlightpresetautorenderer.Py) Now uses a dict for its input rather than multiple values.
- (License) Update copyright for 2023.
- (Lightconstants.Py) Area and directional light defaults are bigger.
- (Mayaarea.Py) Supports exposure and intensity.
- (Mayamath) Added AXIS_IDX_BY_NAME for easy lookup.
- (Rendermandirectional.Py) Light scale is divided by 5 to match other renderers.
- (Vraydirectional.Py) Now builds as a VRaySunShape type.

Removed
~~~~~~~

- (Hdribase.Py, Areabase.Py, Directionalbase.Py) Removed code that is now in lightsbase.py.
- (Meta) Removed legacy meta rig classes.
- (Nodemultibase.Py) _renameUniqueSuffixName() method has been removed as shouldn't be used by any subclasses.


1.7.20 (2022-12-03)
-------------------

Added
~~~~~

- (Libs.Cmds.Objectutils Modules) Added author and python example documentation.
- (Libs.Cmds.Shader.Shadertypes Modules) Added author and python example documentation.
- (Locators.Py) With function for create and matching a locator to objects or component selection.
- (Matching.Py) Various functions for matching.py for matching objects to components.
- (Selection.Py) New function added componentOrObject() which returns whether the first object in the selection is an object or component.
- (Shelf) Added triggerToggle to developer shelf menu.
- (Zapi) Plug.deleteElements() method added to batch delete array elements.

Bug
~~~

- (Alembic) Fix UserAttr and UserAttrPrefix using incorrect types.
- (Controllertags) Fix Missing prepopulate connection from parent controller tag.
- (Mayacolors.Py) Fixed full crash related to om2 errors with opening old Redshift scenes in 2022 and above and anything color ACES conversion related.
- (Mayastandardsurface.Py) Fixed issues converting Lamberts/Blinns etc to standardSurface with no clearCoat values.
- (Qt) Fix Layouts having the same parent causing Qt logs to be output of linux/OSX.
- (Riggingmisc.Py) MarkCenterPivot works with objects and if nothing is selected.
- (Zapi) Fix deleting element not applying.
- (Zapi) Plug disconnect doesn't apply if you provide a Modifier and apply is True.

Change
~~~~~~

- (Create.Py) CreatePrimiveAndMatch() function changed to no support matching to component and multi-object selection.
- (Curves) Optimize applying shape colors to improve performance.
- (Polevectorposition) PoleVectorPosition to raise not error when the angle is 0.
- (Riggingmisc.Py) MarkCenterPivot() function now uses new code and will create a locator at worldcenter if nothing is selected, also supports multi-object selection.
- (Shelf) Shelf now supports checkboxes.


1.7.19 (2022-11-17)
-------------------

Added
~~~~~

- (Attributes.Py) Added max and min kwargs to createAttribute helper function.
- (Attributes.Py) Create attribute and connect helper function added used in blendshape hive build scripts.

Bug
~~~

- (Arnoldhdri.Py) Fixed legacy scenes 2022+ error/warnings with 'scene-linear Rec.709-sRGB' could not be found. HDRI color space fix.
- (Cmdsattributes) Fix py3 syntax warning when creating attribute.
- (Mayacolorbtn) Qt Error when calling MayaColorBtn signal with PyQt5.

Change
~~~~~~

- (Zapi) Added show method for attributes.
- (Zapi) Setting an attribute to hidden changes keyable state.

Misc
~~~~

- (Docs) DocString fixes.


1.7.18 (2022-11-15)
-------------------

Bug
~~~

- (Qt) Fix wrapInstance usages not support PyQt.


1.7.17 (2022-10-26)
-------------------

Added
~~~~~

- (Math) Support converting to and from scene units.
- (Shelf) Added Refresh viewport action to shelf menu.
- (Attributes.Py) Added animatableAttrs() function for returning all the animatable attr names on a node/object.
- (Attributes.Py) Added channelBoxAttrs() function for returning all the attributes in the channelbox with options.
- (Bakeanim.Py) Added bakeLimitKeysToTimerangeSel() function that limits a cycle to the in and out frame, whilst maintaining the cycle.
- (Keyframes.Py) Added copyPaste keyframe helper function for copying keys from one object/node to another.
- (Keyframes.Py) CopyPasteKeys() function now supports basic static keyframe support.
- (Mirrorpasteanimattrs.Py) Mirror functions now support static values and limit time range options.
- (Mirroranimation.Py) Added new module for mirror copy/pasting animation between objects.
- (Mirroranimation.Py) MirrorPasteAnimSel() function for mirroring generic animation using a UI.
- (Selection.Py) Added helper function for returning pair lists with multiple object selection. Options for oddEven or first half/second half.

Bug
~~~

- (Markingmenu) Regression fix for supporting builtin maya icons.
- (Spaceswitching) When adding a Point constraint space the constraint offset is incorrect(done by maya), this change we do this ourselves.

Change
~~~~~~

- (Mainwindow) Removed show argument from init function due to visual artifacts it can cause due to events.
- (Renderer) Updated depreciated call to preference coreInterfaces.
- (Uninstaller) Fix window position saving.
- (Zoo_Tools_Default.Mhk) Reverted animation step keys to fully support Maya functionality.
- (Grapheditorfcurve.Py) Improved autotangentCycle functions for selection and other.
- (Keysets.Py) Incremented version number.

Misc
~~~~

- (Animobjects.Py) Added a function that returns objects and graph editor curves and channel box selection, useful for selection based animation tools.
- (Attributes.Py) Added proxyAttributes() function for returning all the attributes in the channelbox with options.
- (Attributes.Py) ChannelBoxAttrs was erroring when returning no keyable or channelbox attributes. Now fixed.
- (Bakeanim.Py) BakeLimitKeysToTimerange() function that converts a cycle into start end range with good tangents.
- (Definedhotkeys.Py) Added new Zoo windows to hotkeys, Hive Mirror Copy Paste, Cycle Animation Tools, Hive Naming Convention, Match Swatch Color Space.
- (Grapheditorfcurve.Py) Added functions for autoTangentCycle() which corrects start/end tangents so they loop on cycles.
- (Keyframes.Py) Paste could fail if start and end frame were both zero, now only provide the start frame on the paste.
- (Selection.Py) Comments added Ignore ( shaderutils.py ) Comments added.
- (Selection.Py) Misc selection set helper functions added.


1.7.16 (2022-09-29)
-------------------

Added
~~~~~

- (Math) Added Axis vector by index constant for convenience.
- (Mayaapi) Support for anim curve (de)serialization.
- (Nodeeditor) Added methods to graph upstream and downstream nodes by UI plug.
- (Nurbscurve) Added rotationsAlongCurve function.
- (Shapelib) Added perpendicularAxisFromAlignVectors, primaryAxisNameFromVector, nonPrimaryAxisNamesFromVector functions.
- (Zapi) Added ikHandle vector helper functions which convert between a vector and ikHandle Vector enum.
- (Zapi) Added nurbsCurveFromPoints helper function.
- (Zapi) Delete Constraints helper function added to purge zoo constraints including the meta data.
- (Zapi) New wrapper classes DisplayLayer, AnimCurve, SkinCluster, IkHandle, Camera, Mesh, NurbsCurve.

Bug
~~~

- (Nurbscurves) Fix createCurveFromPoints doubling up the "shape" Name suffix.
- (Skinreplacejoints) Fix replaceJointsMatrixSuffix filtering for transforms instead of joints.
- (Toolpalette) Fix bug where a missing plugin icon would stop zootools from loading.
- (Zapi) Fix reset transform using isConnected instead of is Destination for safely checks.
- (Zapi) Ls function raised TypeError.
- (Zapi) RuntimeError maya error raised when attempting to reset local transform when it's connected.
- (Zapi) RuntimeError raised when setting visibility when it's plug is connected.
- (Zapi) SetDefault on a plug never gets set.

Change
~~~~~~

- (Mayaapi) Attribute serialization now ignore default flag values.
- (Mayaapi) Support for adding missing compound attribute children. Note: ordering existing children to align to structure isn't currently supported.
- (Mayaapi) Support fractionMode for motion paths.
- (Mayanodeeditor) Support for setting the node view mode.
- (Zapi) Added Time class Type.
- (Zapi) BuildConstraint to now return created nodes.
- (Zapi) Convert DagNodes to DagPaths to better support geometry world space queries.
- (Zapi) Search for a plug now supports children and arrays.

Misc
~~~~

- (Arnoldhdri.Py) HDRI skydomes in Arnold now set as scene-linear Rec.709-sRGB instead of raw which fixes ACES color space issues.
- (Bgcycg.Zoogshad) Shader name is now correct Changed ( defaultassets.py ) Duplicated kwargs fixed.
- (Cmdswidgets.Py) MayaColorBtn (color picker) now accounts for Rendering and Display Space in 2023. 2022 and below defaults to srgb > linear as previously. Added ( mayacolors.py ) Added viewspace control for displayColorToCurrentRenderingSpace() and renderingColorToDisplaySpace() BugFix ( mayacolors.py ) Depreciated renderingColorToDisplaySpaceLegacy() and replaced with a new function renderingColorToDisplaySpace() that correctly handles viewspaces in 2023. cmds version is broke now in 2023.
- (Default Alembic Cyc Models) Better UVd cyc models as defaults.
- (Exportabcshaderlights.Py) SetShaderAttrsZscnInstance function now can set as display space instead of a hardcoded srgb conversion. Supports ACES. Changed ( shaderbase.py ) shadervalues() method changed kwarg to convertToDisplay. Supports ACES instead of hardcoded srgb conversion. Bugfix ( shaderbase.py ) convertDict() methods now check if the emmision dict key exists, will work again on older presets.
- (Mayacolors.Py) Fixed bug re API color code not working in 2022.
- (Normalarnold.Py) Arnold normal map support added Added ( normalredshift.py ) Redshift normal map support added Changed ( normalmaya.py ) most methods moved to normalbase.py as shared with redshift.
- (Normalrenderman.Py) Support for renderman normal and bump maps. Basic functions supported.
- (Redshiftredshiftmaterial.Py) Setting metalness would not reset the fresnel mode and reflective color. Now fixed.
- (Shaderbase.Py) Added methods for converting rendering to display space colors and back again.
- (Shaderbase.Py) New methods for setting and getting colors in display space. Added ( convertshaders.py ) Added functions for converting swatch colors between different render spaces. Added ( mayacolors.py ) Added functions for converting display and rendering colors back and forth. Added ( rendererconstants.py ) new lists with default render and display spaces.
- (Shaderbuilder.Py) More options for picking up diffuse color. Added ( shaderutils.py ) Recognises the main shader types if no shading group.
- (Shaderbuilder.Py) Removed redundant code.
- (Shadertypes) All shader types now have normal and outColor attributes Added ( shadertypes ) All shader types now inherit NodeMultiBase Changed ( shadertypes ) self.shaderNode is now self.node, has been refactored on all shader types.
- (Unlockunhideall.Py) Unlocks and unhides everything under a hierarchy selection.
- (Viewportmodes.Py) Look through selected command. Panels (viewport menu) > Look Through Selected.


1.7.15 (2022-07-25)
-------------------

Misc
~~~~

- (Lightpresets.Json) Accidentally added Ignore ( postdamerPlatz.tx ) Accidentally added.
- (Redshifthdri.Py) Redshift HDRIs no longer turn black while cycling through HDRIs. The intensity is now returned correctly.
- (Renderertransferlights.Py) HDRIs correctly search for HDRIs in all paths if the HDRI path isn't found for light presets etc. Changed ( shaderbuilder.py ) texturebuilder.py has been renamed to shaderbuilder.py Added ( shaderbuilder.py ) Various improvements, version one is basically working but rough and a WIP. Added ( mayafiletexture.py ) Support for plugging in scalar textures Added ( mayastandardsurface.py ) Added normal attribute, should be added to other shaders too.
- (Shaderbase.Py) SetShaderName returns the renamed name properly. BugFix ( shaderbuilderui.py ) Loads the lookdev toolkit plugin automatically if not loaded.
- (Shaderbuilder.Py) Added some defaults to the SUBSTANCE dict naiming conventions.


1.7.14 (2022-07-20)
-------------------

Added
~~~~~

- (Focuspuller.Py) New function for checking if the focusDistance attribute already has keys or connections.
- (General) Helper function for determining if the current scene is untitled.
- (Hdribase.Py) Added methods for setting and getting intensityMultiply and rotateOffset attrs.
- (Lightsmultihdri.Py) Added functions for saving and loading the intensity multiplier and rotation offset info to the zooInfo file.
- (Lightsmultihdri.Py) CreateDefaultRenderer() function has options for creating/adding to a light group and selecting the light after creation.
- (Repeatcommand) Added support for maya Repeat last command with a decorator.
- (Zapi) Added clearSelection function.

Bug
~~~

- (Focuspuller.Py) Handles offsets on the camera's rotateAxis attributes. Was affecting cams brought back from Unreal.
- (Metafocuspuller.Py) Cleanup no longer fails on meta trying to pull names that no longer exist.
- (Renderermixin) Renderer filter incorrectly sets data model filter.
- (Rotateorder) Baking rotateOrders doesn't respect existing rotateOrder key frames.
- (Zapi) PlugByName doesn't convert plug node to zapi.

Change
~~~~~~

- (Meta) Reduced calls to initialize meta attributes when iterating the network.
- (Polevector) Support providing pole vector distance.
- (Zapi) Added apply modifier argument for undo renaming.

Misc
~~~~

- (Assorted) Doc strings fixed to be sphinx compatible. Added ( assorted ) Assorted doc strings added and tweaked.
- (Cleanup.Py) LockNormals_toHS no longer reloads Added ( cleanup.py ) objClean() now keeps parent structure bt default while importing objects back into Maya.
- (Cmds.Rst) Doc strings changed to avoid using zoo maya commands.
- (Defaultassets.Py) Support for rotation offset and intensity multiply values for the HDRI Skydomes. Switched build to new code. Changed ( viewportlights.py ) Skydome Platz hardcoded rot offset to be -42 to match with latest assets.
- (Hdribase.Py) ConnectedAttrs() method which returns the main attributes that have connections. Changed ( nodemultibase.py ) removed connection check while returning scalar and vector values. Connections should be checked elsewhere. Changed ( shaderbase.py ) removed connection check while returning scalar and vector values. Connections should be checked elsewhere. Changed ( viewportlights.py ) HDRI builds from new hdribase code with class instances. Added ( viewportlights.py ) HDRI handles rot offset and multiply intensity info. Callibrates with new HDRI library.
- (Metasplinerig.Py) Spline rig marking menu no longer fails when there is only one set of controls eg FK only.
- (Rendererconstants.Py) Added the suffix _RAMP to be filtered in the browsers as a supported Maya shader. Added ( texturebuilder.py ) First pass texture builder module, heavy WIP.
- (Uvmacros.Py) Support for various function with repeat last command "g" hotkey.
- (Vrayrendersettings.Py) Added VRay render settings for opening the frame buffer. Changed ( multirenderersettings.py ) If the Maya renderer is set open the Arnold renderview. Added ( multirenderersettings.py ) support for opening VRays render view.


1.7.13 (2022-05-31)
-------------------

Added
~~~~~

- (Arnoldhdri.Py) SetImagePath() method is now working.
- (Arnoldhdri.Py) Texture support via class instance to Arnold HDRI lights.
- (Cleanup.Py) Added triangulate ngons function.
- (Cleanup.Py.Py) Select Tris and NGons function.
- (Components.Py) Added a number of functions related to triangle faces and nGon faces.
- (Exportabcshaderlights.Py) SaveShaderInstanceZooScene() can now save as srgb color.
- (Filetexturebase.Py) Added checks to validate the texture network, small doc fixes.
- (Filetexturebase.Py) Base class for file textures.
- (Hdribase.Py) - can select the shape node and transform node directly in the class for UIs.
- (Hdribase.Py) Delete and suffix methoda added.
- (Hdribase.Py) HDRI Skydomes added calibration between renderers for scale and rotate, subclasses tweaked as well.
- (Hdribase.Py) ParentZooLightGroup method, to add the light to a renderer group for cleanup.
- (Hdribase.Py) The shape node of the HDRI light can now be accessed from self.shapeNode (zapi).
- (Lightconstants.Py) New dictionaries/lists for retrieving hdri information.
- (Lightingutils.Py) New function filterAllLightTypesFromNodes() to retrieve specific light tytpes from a node string list.
- (Lightsmultidhri.Py) The entry point for creating and ingesting hdri skydomes with multi-renderer support.
- (Lightsmultihdri.Py) Added better support for finding HDRI instances via renderer and in the scene. Added ( mayafiletexture.py ) Added the ability to ingest a texture network tweaks and docs added.
- (Lightsmultihdri.Py) File renamed and better handling of shape vs tranform nodes.
- (Mayafiletexture.Py) Class for Maya native file textures.
- (Nodemultibase.Py) ShortName() method added for light names.
- (Shaderbase.Py) Method setFromDict() now can be applied in SRGB Color using the flag colorsAreSrgb=True.
- (Shaderbase.Py) Method shaderValues() can be converted to SRGB with the kwarg convertToSrgb.
- (Shdmultconstants.Py) Constant modified was 'gEmission_srgb' now 'gEmission'. Causes some backward compatibility issues, should be ok.
- (Splinebuilder.Py, Splines.Py) Added up vector controls (work in progress).
- (Subdivisions.Py) Added polysmooth objects, will be used later.
- (Vrayhdri.Py) Support for VRay HDRI image and texture network.
- (Zapi) Added default and setDefault plug methods.
- (Zapi) Basic support for blendShape nodes.

Bug
~~~

- (Assorted) Changes to shader code to calibrate shader presets (multi-renderer) which were not importing and saving as SRGB color.
- (Assorted Files) Assorted bug fixes with the new hdri classes.
- (Defaultassets.Py) Sets renderer to Arnold for shelf light presets if "Maya" is set as the renderer.
- (Hdribase.Py) Select transform no longer selects the shape node.
- (Lightingutils.Py) Function getAllLightShapesInScene() was returning duplicates, now fixed.
- (Mayaapi) Incorrect maya attribute type created when enum fields is [].
- (Mayaapi) Setting default to last index of an enum never happens.
- (Mayastandardsurface.Py) Fixed clear coat being applied as grey and clouding the color of standardSurface shaders.
- (Metasplinerig.Py) Duplicate the spline rig wasn't including skinned geo in 2022 and 2023. Fixed bug.
- (Metasplinerig.Py) Exporting a spline rig now supports multiple meshes.
- (Nodemultibase.Py) Self.shapeName() method grabs the transform name correctly now with self.name().
- (Rendermanhdri.Py) Intensity sets as scalar instead of vector.
- (Spaceswitching) Applying multiple constraint types on the same node would result in metadata being overridden.
- (Spaceswitching) Drivers returning incorrect element when there's no data.
- (Spaceswitching) Space Index isn't ignored when the targetNode isn't valid.
- (Splinerig) Creating a SplineRig MetaNode without a name results in a TypeError.
- (Splinerigswitcher.Py) Was erroring on None types in retrieveSpineControlList() and breaking space switching if missing spline rig parts. Fix and handles the missing parts now.
- (Toolpalette) Shelf variants not being passed to plugin execution.
- (Toolsetwidget) UpdateProperties doesn't unblock signals when an error occurs.
- (Vrayhdri.Py) Intensity sets as scalar instead of vector.
- (Zapi) Calling value() on a Message plug array which contains connections doesn't convert MObjects to Zapi Nodes.
- (Zapi) Missing registration of BlendShape Node class.

Change
~~~~~~

- (Broadunittests) Remove Unused Preferences access.
- (Defaultassets.Py) Replaced om2 messages with output.
- (Mayatoolpalette) Rewrote Shelf logic to Match the latest tool palette code.
- (Renderermixin) Avoid loading preferences on module import.
- (Splinebuilder.Py) Disabled the new up vector controls temporarily for release as they are a WIP and are not finished.
- (Toolpalette) Migrate menu logic to the latest changes in toolPalette.
- (Toolpalette) Shelf menu items are now QT based.
- (Zooicons) ZooIcons toolset moved to zootoolsets repo.

Remove
~~~~~~

- (Scripteditor) Removed Redundant maya script editor dialog Replaced with source code editor.


1.7.12 (2022-04-16)
-------------------

Added
~~~~~

- (Arnoldhdri.Py) Added Arnold HDRIs subclass to the new HDRI light code.
- (Attributes.Createattribute() ) Helper function for creating attributes with non-keyable settings.
- (Attributes.Py) DisableNonUniformScale() function for disabling non-uniform scale on an object.
- (Attributes.Py) New functions hideAttr() and hideAttrs() while supporting non-keyable attributes.
- (Attributes.Visibilityconnectobjs() ) Added function for connecting a control visibility attribute to control the visibility of many other nodes.
- (Commands) Added MatchTransformsBakeCommand.
- (Commands) Added match transforms command.
- (Convertshaders.Py) Added convertShaderScene() and convert save scene functions for batch converting of full scenes to a new shader type.
- (Convertshaderscene.Py) Script run for converting shaders in scene when run standalone.
- (Hdribase.Py) First pass base class for HDRI Skydomes, new code.
- (Joints.Jointdrawhide() ) To show/hide a joint list.
- (Keyframes.Py) Added transferAnimationSelected() and transferAnimationLists() for transferring animation outside of Hive. Added ( renderertransferlights.py ) Basic header documentation examples for building lights without UIs.
- (Layers.Py) Added a dedicated module to render layers and refactored existing code.
- (Lightconstants.Py) Added VRay renderer string to lightconstants.py.
- (Lightconstants.Py) New module for light constants for all lights and renderers.
- (Nodemultibase.Py) Base class mostly for handling different renderers for lights, shaders, textures etc.
- (Redshifthdri.Py) First pass class for Redshift HDRI Skydomes, new code.
- (Rendermanhdri.Py) Added Renderman HDRIs subclass to the new HDRI light code.
- (Skinreplacejoints.Py) Added function replaceJointsMatrixSel() replace skin joints by selection.
- (Standalone_Runconvert.Py) Module that runs convertshaderscene.py via mayapy in standalone mode.
- (Vrayhdri.Py) Added VRay HDRIs subclass to the new HDRI light code.

Bug
~~~

- (Attributes.Createenumlist() ) returns the attribute again.
- (Controls.Py) Needed to have global ROT_AXIS_DICT.
- (Convertshaders.Py) Handles conversion of shaders that are not assigned to geo.
- (Core) Incorrect function call for determining maya mode.
- (Core) Triggers commands fail if a None type is Passed. Now filters out None Type.
- (Mayaunittest) Globally needed plugins are turned off after a test.
- (Metaviewportlight.Py) Will set specularIntensity value now.
- (Renderertransferlights.Py) Changed path in docstring to avoid unicode errors.
- (Shelve) Fix py3.9 syntax warning.
- (Splinerig) AttributeError raised when retrieving controls which aren't connected yet.
- (Splinerigrebuild.Py) Added back the imports.
- (Viewportlights.Py) SPECULAR_MULTIPLIER back to 1.0 its correct value, can set specularIntensity.
- (Zapi) Adding DG nodes to objectSet raises a runtimeError.
- (Zapi) Maya2023 fix for iterating over a plug array not returning the first index when the plug array has no used indices.
- (Zapi) OSX Crashes when querying asset container published attributes.
- (Zapi) Space switch attribute channel box is set to true leading to an un-keyable attribute.
- (Zapi) When retrieving keyframes for baking every frame the last frame is missing.

Change
~~~~~~

- (Artistpalette) Reuse base code for command execution strings.
- (Attributes.Addproxyattribute() ) Better handling of non-keyable setting in the channelbox and refacotr to many files.
- (Attributes.Addproxyattribute() ) To better handle non-keyable settings.
- (Attributes.Createenumattrlist() ) Changed function to be consistent with others and better handling of non-keyable settings.
- (Commands) Import statement cleanup to avoid incorrect class registration.
- (Documentation) Fix doc string typos and continued work on adding docstrings.
- (Documentation) Package title typo fix.
- (Hdribase.Py) More generic code added to the HDRI base class.
- (Mayaapi) Better support for retrieving MPlug from the full path.
- (Redshifthdri.Py) Redshift class changed reusable code moved to hdribase.py.
- (Viewportlights.Py) Disabling specular lights and setting the dirctional light intensity correctly (WIP).
- (Zapi) Casting Node to str will return the full path name not the short name.
- (Zapi) DagNode.create Type argument renamed to nodeType.
- (Zapi) Error classes moved to zapi/errors.py.
- (Zapi) Space switching initial support for both decompose and offset Parent Matrix in the same maya version.
- (Zapi) Zapi __repr__ for nodes will now return the fullPathName so passing to cmds is possible.

Removed
~~~~~~~

- (Convertrotateuplist() ) Removed function convertRotateUpList() and replaced with a dictionary in zoocore, refactor for many files.


1.7.11 (2022-03-14)
-------------------

Added
~~~~~

- (Convertshaders.Py) Handles supported texture connections while converting. Maintains connections.
- (Definedhotkeys.Py) Added newer Zoo Tools open hotkeys as unbound hotkeys. Old tools now renamed correctly with newer functions.
- (Normalbase.Py) Starting texture support for normal/bump maps.
- (Rendererconstants.Py) Added RENDERER_BROWSER_FILTERS and ALL renderer as globals. Also RENDERER_ICONS_LIST_ALL as a list of renderers including ALL.
- (Renderers.Py) Added handling of "All" renderer and more filtering options for .MA/.MB image browsers via the renderer names.
- (Shaderbase.Py) Better supports setting and getting color values in srgb space, for example from UIs.
- (Shaderbase.Py) Documentation added.
- (Shaderbase.Py) Supports returning texture connections and reconnecting textures, useful while converting between shader types.

Bug
~~~

- (Core) Fix specific use of ntpath instead use os.path.
- (Definedhotkeys.Py) Adding open_alembicAssets() hotkey fix due to name change.
- (Mayaapi) Fix previous git commit incorrectly merging.
- (Mirror.Py) Uninstance selected now supports mirror objects that are deep in hierarchies.
- (Rendermanpxrsurface.Py) PXR surface is working again and added emission too.
- (Shaderexport) Handle support for shaders which aren't connected to a shading group.
- (Shaderloading) Ensure Temporarily namespace is removed post import of a shader.
- (Shaderpresets.Py) Tooltip changed to correctly explain sliders.
- (Shaderutils.Py) Blocked "not .ma or .mb" message while saving shaders when it should not be triggered.
- (Unittest) Increase maya unittests several fold.
- (Vraymtl.Py) Vray no longer updates while querying IOR values if they are already set correctly with lockFresnelIORToRefractionIOR = False.

Change
~~~~~~

- (Files.Py) Added ability to block warning message "not .ma or .mb".


1.7.10 (2022-02-22)
-------------------

Added
~~~~~

- (Imageplanes.Py) Added faster direct functions for rotation, scale, opacity and offsets.
- (Metafocuspuller.Py) Code for cleaning up (deleting) broken focus puller meta setups.
- (Metafocuspuller.Py) Docs.
- (Metafocuspuller.Py) IsValid() method for checking if the meta is broken.
- (Multirendererconnecttest.Py) Added tests code for multirenderer shaders.
- (Renderertransferlights.Py) Added faster direct functions for set and get IBL rotations. Will be rewritten later with classes.
- (Scripteditor) Ported scripteditor state machine for unittesting.
- (Unittest) Added basic attribute and proxyAttribute creation tests.
- (Zapi) IsProxy method added to Plug class.

Bug
~~~

- (Bindskin.Py) RemoveInfluenceSelected() has better error checks.
- (Cleanup.Py) Checks if there is an object selection while freezing transforms.
- (Controls.Py) Freezing transforms while creating controls is now checks for skinning, and exits if skinning is present.
- (Focuspuller.Py) Now handles non-unique names.
- (Focuspuller.Py) Will remove any existing attributes on cameras from previous rigs not deleted properly.
- (Keyframes.Py) Toggle Visibility now checks if the attribute is settable.
- (Logging) Layered stack traces are output when an error occurs instead of one.
- (Mayaapi) Adding Compound attribute as a proxy causes crash.
- (Mayaapi) Fix AttributeError when getting plug min/max value on compounds.
- (Mayaapi) Fix Float3 attributes not using correct api call resulting in crashes.
- (Mayaapi) Fix adding compoundAttribute not handling numeric compounds which require separate behaviour.
- (Mayaapi) Fix long attribute type being deprecated in maya but not handle correctly on the zoo side.
- (Mayaapi) Incorrect Compound Attribute connections when creating a proxyAttribute.
- (Mayaapi) Serializing Plugs resulted in using shortnames.
- (Spaceswitching) Fix pre maya 2020 matrix constraint TypeError.
- (Uvtransfer.Py) Transferring shaders without UVs no longer tells the user it's failed, even though it succeeded.

Change
~~~~~~

- (Bindskin.Py) Om2 switched to output for all messages.
- (Cleanup.Py) All info and warning messages switched to output not om.
- (Focuspuller.Py) Attributes are categorized better and nonkeyable when created on the camera.
- (Imageplanetool) Add function to do all image plane transformation settings for VirtualSlider.
- (Metafocuspuller.Py) Cleaned up lengthy code sections.
- (Rendertransferlights) Update changeIBLTextureFound function with new multidirectories.
- (Shelf) Removed redundant tool definitions.
- (Triggersmm) Marking menu no longer merges the layout from all nodes now just the last selected.


1.7.9 (2022-02-04)
------------------

Added
~~~~~

- (Attributes.Py) Ability to move channel box attributes up and down in the channel box.
- (Attributes.Py) Added addProxyAttributeSel() for adding proxy attributes to selected objects with error checks.
- (Attributes.Py) Added deleteAttributeSel() deletes attributes from channel box selection.
- (Attributes.Py) Added functions for getting the selected object and attributes for Channel Box Manager UI.
- (Attributes.Py) Added labelAttrSel() for adding dividers to selected objects.
- (Attributes.Py) Added open window functions for Maya's attr windows.
- (Buildtexturedshader.Py) First pass at creating a shader from a folder of textures WIP.
- (Constraints.Py) Added constrainMatchList() hardcoded function to constrain prefixed objects to their master obj.
- (Fbx) Helper utilities for Fbx Version queries.
- (Filtertypes.Py) Added constraints to filter types, auto suffix etc.
- (Filtertypes.Py) Support for constraints in filtertypes.py, helps fix rename tool issues naming constraints.
- (Follicles.Py) Added follicles module, only follicle transfer added at the moment.
- (Mayareference) Added helper function to import all references.
- (Namespace) Added a namespace context manager which temporarily creates a namespace and deletes it on exit.
- (Shaderbase.Py) Added setTexture() methods for building basic textures. WIP.
- (Skinreplacejoints.Py) Added replaceJointsMatrixSuffix() so joints can be replaced by suffix/prefixes.
- (Spaceswitching) Added helper function to delete constraint metaData.
- (Testuis.Py) Added the four new tools replacejointweights, channelBoxManager, hiveFbxRigExport, hiveMayaReferenceExport.
- (Textures) Added maya.cmds.textures package.
- (Uninstaller) Added uninstall zootools to dev shelf icon button.
- (Zapi) Added displayLayers function wrapper to only return non deletable nodes.
- (Zapi) Ls cmd function.
- (Zapi) Now supports a namespace context manager.

Bug
~~~

- (Attributes.Py) CheckRemoveAttr() checks parent attributes and deletes those, errored on vector attrs etc.
- (Attributes.Py) CheckRemoveAttr() supports removing locked attributes.
- (Attributes.Py) Fixed addProxyAttribute() handles parent names properly.
- (Attributes.Py) GetChannelBoxAttrs() no longer errors if the attribute doesn't exist on multi selected objects.
- (Attributes.Py) MoveAttrBottomList() supports locked attributes.
- (Metanodes) Fix RuntimeError when initializing a referenced node.
- (Namehandling.Py) ForceRenameListSel() double renames now to avoid issues while renaming flat hierarchies.
- (Namespaces) Namespace context manager would fail if the namespace already exists instead of reusing it.
- (Randomshaders.Py) Fixed bug where known shaders wouldn't be assigns if adding shaders with self.useShaders().
- (Randomshaders.Py) Fixed bug where textures would fail if adding shaders with self.useShaders().
- (Spaceswitching) Creating a constraint with trace=False raise AttributeError due to attribute no longer being created.
- (Testrenderers.Py) Fixed alembic assets that now have folders in the default prefs.
- (Zapi) KeyFramesForNodes ignores last frame on nodes.
- (Zapi) RemoveNamespace on a node would remove the namespace from the scene.

Change
~~~~~~

- (Constraints.Py) Function constrainMatchList() is now more generic and can be reused.
- (Core) Move pluginManager interface initialization to iterable.
- (Namehandling.Py) Improved the function renumberListSingleName(), handles long names.
- (Shelves) Ported generic shelf base code from maya palette into base.
- (Textures) Moved cmds.shaders.textures.py to cmds.textures.textures.py.

Enhancement
~~~~~~~~~~~

- (Namehandling.Py) Added forceRenameListSel for new UI enhancement.


1.7.8 (2022-01-19)
------------------

Bug
~~~

- (Shader Types) Method where it was missing in shader types.


1.7.7 (2022-01-18)
------------------

Bug
~~~

- (Gimbaltolerances) TypeError on Py2/maya2020.


1.7.6 (2022-01-18)
------------------

Added
~~~~~

- (Broad Unit Tests) Included newer UIs to the test.
- (Cmds) Added functions for retrieving selected frame range.
- (Definedhotkeys.Py) Added missing open tool hotkeys.
- (Exportabcshaderlights.Py) Can now save a shader as a zoo scene from a Zoo shaderInstance object.
- (Exportabcshaderlights.Py) For setting shader instances.
- (Fbxexport) Fbx Triangulation option support.
- (Fbxexport) Support tangents, smoothMesh, instances as arguments.
- (Generalanimation) Added function allGimbalTolerancesForKeys.
- (Misc Shader Types) Added small functionality across all shader types.
- (Namehandling.Py) GetUniqueNameSuffix now supports already suffixed names.
- (Objhandling.Py) Checks if shape nodes only are instanced.
- (Objhandling.Py) Supports transforms that are instanced and can now pass in transforms and shapes.
- (Rendererconstants.Py / Shdmultconstants.Py) Added various constants.
- (Renderers.Py) Now added option for disabling "Maya" and "VRay".
- (Rootinstance.Py) Finds the top node of the hierarchy of instanced objects.
- (Shaderbase.Py) Can apply while setting default shader values.
- (Shaderbase.Py) Now supports uniquely numbered names with end suffixing.
- (Shaderutils.Py) To shaderutils.py. Selects objects and faces assigned to multiple shaders.
- (Uninstance) Uninstance selected now supports root instanced nodes. Ie if the selected is a child of an instanced network will uninstance the root.
- (Vraymtl.Py) Shader support for glossiness if roughness is not checked on. No longer defaults to roughness on create.
- (Zapi) AllGimbalTolerances function.
- (Zapi) SetRotationOrder to support preserve flag for rotations.
- (Zapi) SetRotationOrderOverFrames function.
- (Zapirotationorder) Support for bake every Frame.

Bug
~~~

- (Broad Unit Tests) ModelAssets is now alembicAssets name change.
- (Fbxexport) Passing a bool to smoothing groups or hardEdges would raise a TypeError.
- (Generalanimation) AllGimbalTolerancesForKeys typeError raised when objects have no keys.
- (Markingmenu) Passing no icon to a menu item results in maya using whichever previous image loaded last.
- (Mayaapi) IterSelectedNodes with a filter tuple would always return Nothing.
- (Shaderbase.Py) Shader name doesn't error if built without a shader in place.
- (Shdmultconstants.Py) MAYA_DEFAULT_SHADER incorrect, changed to MAYA_SHADER_LIST.
- (Zapi) AllGimbalTolerances typeError.

Change
~~~~~~

- (Allgimbaltolerances) Now supports provide sampling by steps.
- (Arnoldstandardsurface.Py) Method.
- (Cmdsrotationorder) ChangeRotOrder now use new rotationOrder code.
- (Convertshadersui.Py) UI now has a renderer icon menu and conforms and updates all other renderer UIs.
- (Docs) Updated docs for creating triggers. Fixing some formatting and missing modules for zapi docs.
- (Docstrings) Updated docstrings for zapi and triggers.
- (Fbxexport) Allow Ascii format.
- (Generalanimation.Py) By default, kwarg option.
- (Keyframesfornodes) Now supports a list of attributes to query.
- (Maya Api) Support get plug values with MDGContext instance.
- (Randomshaders.Py) Now uses shaderTypes for creation rather than by renderer.
- (Rendererconstants.Py) Cleaned up renderer constants a little.
- (Renderers.Py.Py) On UI load refresh the preferences if the renderer has been changed.
- (Shaderbase.Py) Better dictionary support for attributes.
- (Shdmultconstants.Py) Removes standardSurface shader in versions 2019 and below.
- (Shdmultconstants.Py) Tidied up constants, VRay prefix fix.
- (Zoo Scene) Zoo Scene version is now 1.1.0 with new attributes available in the shaderbase.py.


1.7.4 (2021-12-18)
------------------

Added
~~~~~

- (Bakenamespaces) Renames ":" into "_".
- (Convert Shaders) Module and support for the Convert Shaders UI.
- (Maya Shaders) Phong and PhongE shader types.
- (Mayaapi) Serialization now supports ignore color data.
- (Nodeeditor) Add methods to change "addNewNodes" editor option.
- (Obj Selection Highlight) Functions for UI.
- (Prefsselection.Py) Includes option to save selection if the preferences window is open and the selection section triggered.
- (Riggingmisc.Py) New module for random rigging tools, added mark center pivot for the related UI.
- (Shader Instance Support) Metalness, emission, emissionWeight, diffuseRoughness.
- (Vraymtl.Py) VRayMtl shader support.
- (Zapi) Added local transform attributes constants.

Bug
~~~

- (Core) PythonCommandToExecute usages not importing cmds causing ImportError on occasion.
- (Curves) SetNodeColour fails if MColor is provided which contains a float4.
- (Maya Shaders) Fix not found error when trying to save shader.
- (Nodeeditor) Fixed "runtimeError" when adding nodes to the editor.

Change
~~~~~~

- (Docs) Moved ZApi api docs into it's own file.
- (Mayaapi) SerializeNode to support shortNames and ignore namespaces if requested.


1.7.3 (2021-12-8)
-----------------

Added
~~~~~

- (Core) Added cmds functions for handling offParentMatrix.
- (Core) Has unknown nodes helper functions .
- (Ui) Adds options to save as either MA or MB.
- (Ui) Right-click on the save button in mayashaders.py .

Bug
~~~

- (Maya Api) MayaTypeFromType returning incorrect result.
- (Mayaapi) Plugs.setPlugDefault Error when default index/name doesn't exist.
- (Zapi) Fails due to node type differences ie. Dag vs DG.
- (Zapi) Fix addEnumFields not adding fields at the end of the list.
- (Zapi) Fix showHideAttributes not hiding a keyable attribut.
- (Zapi) SetObject RuntimeError raised when mobject isn't a node.

Change
~~~~~~

- (Cmds) Matrix.py with new code for better supporting freeze and unfreeze offsetParentMatrix, Now support modeling and joints.
- (Core) Matrix is supported for replacing shapes.
- (Maya Api) Added option to exclude Attributes when deserializing node.
- (Maya Api) Plug value wrapper to speed up colour retrieval with curves.
- (Maya Api) Plugs setting default,min,max,value split out to support passing attribute mobject.
- (Mayaapi) General speed improvements for mayas api wrappers.
- (Mayaapi) GetPythonTypeFromPlugValue to return compound attribute values ie .translate.
- (Metanode) Delete to take modifier .
- (Shaders) Added class variables to all shaders so string attribute names can be accessed in the shader instances easily.
- (Shaders) Shaders save to binary if there are unknown nodes .
- (Spaceswitching) Spaceswitching to support passing None as the driver, useful to reduce the amount of targets when you just need a on/off switch ie. 2 enum fields.
- (Triggers) Allow triggers to be turned off by default via environment variables.
- (Zapi) Added makeCurrentContext on a container asset.
- (Zapi) Added scale space argument to support world and transform space query.
- (Zapi) Port maya api transform query directly into zapi to avoid extra object casting.


1.7.2 (2021-11-1)
-----------------

Bug
~~~

- (Maya Api) Fix serializePlug skipping min,max when attr isDefaultValue.
- (Maya Ui) Fix color button widths.
- (Triggers) Fixed selection callback context manager AttributeError when no theres no callback active.
- (Zapi) Added method to clear unbound container published attributes.
- (Zapi) Remove unbound container attributes support.

Change
~~~~~~

- (Markingmenu) Multi marking menu layout support.
