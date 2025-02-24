.. _buildscripting_example-reference:

Build Scripting Examples
************************

The page provides `Hive Build-Script` (python class) code examples.

`Hive Build-Scripts` are useful for modifying the rig outside of the limitations of the Hive UI.

`Build-scripts` automate the re-creation of `user-modifications` for rebuilding.

`Build-scripts` are useful for:

- Adding `manual rigging parts` from other `rig systems` to `Hive`.
- Add and `connect` new `attributes` after building.
- Create new `selection sets` for animation.
- Set `default attribute states` and `visibility`.
- Other custom modding of `Hive components`.

For instructions on setting up a build script see :ref:`Examples <buildscripting-reference>`.

User defined `build-scripts` can be created in the `folder`:

- `/zoo_preferences/assets/hive/buildscripts/`

You can copy the script `template_buildscript.py` found inside the `buildscripts folder`. Modify the `pasted file` to create a new `build-script`.


How Hive Rebuilds
************************

When `Hive modes` change from `Rig` or `Polish` modes back to `Skeleton` or `Guides`, the `rig group` is deleted but the `deformation joints` remain.

Any `objects` or `custom attributes` that belong to the `Hive controls` will be removed.

`Objects` that are `parented` or `constrained` to `deformation joints` and any `skinning` will not be deleted.



Accessing Nodes With The Hive API
####################################################

You can access `control, joint`, `selection-set` and other `node` names via the `Hive API` or with `hardcoded string names`.

The `Hive API` has the advantage that `Hive nodes names` do not matter, as our `API` accesses the `rig` via `meta-data` stored in `Maya's network nodes`.

You are welcome to use `hardcoded string names` in your `build-scripts` along with any regular `Maya cmds python code`.

We encourage more advanced `TDs` to use the `Hive API` for accessing `node names`.

.. code-block:: python

    #To access Hive controls you can use hardcoded string names such as
    footLCtrl = "leg_L:end_ik_anim"  # guide name
    # or
    footLCtrl = "leg_L_end_ik_anim" # polished name

    # You can instead use the Hive API to reliably return control names and other rig nodes regardless of names.

    self.rig  # is the rig Hive instance
    self.rig.god_M  # is the god component as a python object as per its component name in the Hive UI.

    #To retrieve the self.rig outside of the build script use the following.  r is the rig object, same as self.rig.
    from zoo.libs.hive.base import rig
    r = rig.Rig()
    r.startSession("myRigName", namespace="")  # Your rig name is found at the top left of the Hive UI.
    self.rig.god_M  # is the god component (all controls, etc) as an object, same name as in the Hive UI.

    #To get the god control use the following, returns the name as a python object
    #You can find the control name id "godnode" by selecting the god control: Attribute Editor > Extra Attributes.
    #Python objects can return string names with str(godCtrl) or godCtrl.fullPathName().
    godCtrl = self.rig.god_M.rigLayer().control("godnode")
    godCtrlStringName = str(godCtrl) # or godCtrl.fullPathName() or short name is godCtrl.name()

    #Ik foot control as a python object.
    footLCtrl = self.rig.leg_L.rigLayer().control("endik")

    #To find the root group of a component use the following code.  Useful for visibility toggles.
    legLRootGrp = self.rig.leg_L.rootTransform()

    #Retrieve deformation joints returns python object, can use str(eyeL_joint)
    eyeJnt_L = self.rig.eye_L.deformLayer().joint("fk01")
    #Retrieve the selection set for a component, returns python object, can use str(eyeL_sSet)
    eyeL_sSet = self.rig.component("eye", side="L").rigLayer().sourceNodeByName("hiveCtrlSelectionSet")

For more Hive API examples go to :ref:`Examples <hiveExamples-reference>`.

Common CMDS/Zoo Python Examples
####################################################

The following examples are common `cmds (python) Maya` functions that may be useful inside `Hive build-scripts`.

.. code-block:: python

    #Create Attribute (zoo helper) "bool", "int", "str"
    from zoo.libs.maya.cmds.objutils import attributes
    attributes.createAttribute("node", "attribute", attributeType="bool", nonKeyable=True, showChannelBox=True, defaultValue=False, minValue=None, maxValue=None)

    # Create Attribute (zoo helper) "enum"
    from zoo.libs.maya.cmds.objutils import attributes
    enumList = ["blue", "yellow", "rainbow"]
    attributes.createEnumAttrList("node", "attribute", enumList, showChannelBox=True, nonKeyable=True, defaultValue=0)

    # Create Attribute Maya
    cmds.addAttr(node, longName='attribute', defaultValue=1.0, minValue=0.001, maxValue=10000 )

    # Create Label Attribute
    from zoo.libs.maya.cmds.objutils import attributes
    attributes.labelAttr("labelAttribute", "node")

    # Create and connect attribute useful for connecting blendshapes to controls for example.
    from zoo.libs.maya.cmds.objutils import attributes
    # source, sourceAttr, target, targetAttr, default, min (can be None), max (can be None)
    attributes.createConnectAttrs("blendshape", "topLid_L", "eye_L_01_anim", "topLid", 0.0, 0.0, 0.1, "float")

    # Create Proxy Attribute
    from zoo.libs.maya.cmds.objutils import attributes
    attributes.addProxyAttribute("node", "existingNode", "existingAttr", proxyAttr="", channelBox=True, nonKeyable=False)

    # Connect Attribute
    cmds.connectAttr("driverNodeName.attributeName", "drivenNodeName.attributeName")

    # Create a new visibility attribute and connect it to many objects.  Usefull for show/hiding controls
    from zoo.libs.maya.cmds.objutils import attributes
    attributes.visibilityConnectObjs(faceVisAttr, godNode, ["faceRig_parentHead_grp"], channelBox=True, nonKeyable=True, defaultValue=True)

    # Parent Objects
    cmds.parent("childObject", "parentObject")

    # Unparent
    cmds.parent("pCube1", world=True)

    # Create Parent Constraint
    cmds.parentConstraint("cone1", "drivenObj", maintainOffset=True)

    # Create Orient Constraint
    cmds.orientConstraint("cone1", "drivenObj", maintainOffset=True)

    # Create Point Constraint
    cmds.pointConstraint("cone1", "drivenObj", maintainOffset=True)

    # Create Scale Constraint
    cmds.scaleConstraint("cone1", "drivenObj", maintainOffset=True)

    # Rename, useful for renaming "HiveDeformLayer_hrc" joints
    cmds.rename("pCube1", "newCubeName")

    # Add objects to a new or existing layer
    from zoo.libs.maya.cmds.objutils import layers
    layers.addToLayer("existingOrNewLayer", ["pCube1", "pCube2"], ref=False, playback=True)

    # Hide object
    cmds.setAttr("objectName.visibility", 0)  # hide

    # Show object
    cmds.setAttr("objectName.visibility", 1)  # unhide

    # Lock and hide attributes, or False is show and unlock
    from zoo.libs.maya.cmds.objutils import attributes
    attributes.lockHideAttr("pSphere1", "visibility", lockHide=True)

    # Set Draw Joint Hide/Show
    from zoo.libs.maya.cmds.objutils import joints
    joints.jointDrawHide(jntList, hide=True)

    # Create or add to selection sets
    face_sets = ["eye_L_ctrls_set", "eye_R_ctrls_set", "jaw_M_ctrls_set"]
    face_ctrls = selection.nodesInListSelSets(face_sets)  # gets all controls inside these sets.
    selection.addSelectionSet("anim_face_set", face_ctrls)  # Creates/adds to a new/existing selection set
