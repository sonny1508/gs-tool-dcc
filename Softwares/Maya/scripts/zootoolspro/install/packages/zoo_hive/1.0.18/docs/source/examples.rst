.. _hiveExamples-reference:

Examples
########

.. contents:: Table of Contents
   :local:
   :depth: 2

Add A Rig
---------

.. code-block:: python

    # first initialise an empty rig instance
    from zoo.libs.hive import api
    char = api.Rig()
    # now either create or initialise a pre-existing rig(searches by name)
    char.startSession("characterName") # populates the rig instance for meta etc

Add a Component to a Rig
------------------------


.. code-block:: python

    # createComponent but dont build guides or rig
    godNode = char.createComponent("godnodecomponent", "godnode", "M")
    arm = char.createComponent("vchaincomponent", "arm", "L")
    # get the full component list from the registry
    char.configuration.componentRegistry().components # dict()
    # get the current attached rig components
    char.components()
    # or by name
    char.component("arm", "L") # searches by name and side
    # or use "." syntax
    char.arm_L == godNode # False
    char.godnode_M == godNode # True

Build Component Guides & Rig
----------------------------


.. code-block:: python

    # build component guides and rigs
    char.buildGuides()
    char.buildRigs()

    # lets do some queries and see what we have
    # get the guide controls
    arm.guideLayer().iterGuides()
    #get a certain guide by id(we always use the id  as it should never change(death is the punishment))
    endGuide = arm.guideLayer().guide("end")# this is the wrist guide
    endGuide.translation() # api.Vector
    endGuide.rotation(space=api.kTransformSpace, asQuaternion=False)# api.EulerRotation
    endGuide.rotation(space=api.kWorldSpace, asQuaternion=True) # api.Quaternion
    endGuide.serializeFromScene() # get a dict() version of the guide which is necessary to recreate it
    endGuide.parent() # Guide Parent instance

Query Controls from a component
-------------------------------

.. code-block:: python

    # what about the rig?
    # same  as the guides
    arm.rigLayer().control("endfk")
    endControl = arm.rigLayer().control("uprfk")
    endControl.translation()
    #what about special animation attributes?
    # we use separate nodes to store anim for a number reasons but heres the code for the arm
    arm.controlPanel().ikfk
    #returns a api.Plug instance
    # settings nodes can be on any layer but these dont show up to animators only
    #controlPanel does. Well unless your component has custom overrides
    rigLayer = arm.rigLayer()
    rigLayer.settingsNodes() # [:class:`api.SettingsNode`]
    # creation
    settingInstance = rigLayer.createSettingsNode("myCustomSettings")
    settingInstance.addAttribute("myHiddenSetting", value=10, default=0, Type=api.kMFnNumericFloat)
    # skin joints?
    # same stuff just different name
    arm.deformLayer().joint("end").translation()

    print(settingInstance)
    # get the meta node instances
    print(char.meta)
    print(arm.meta)
    print(rigLayer)
    # get the root transform of the arm  component
    print(arm.rootTransform())

Update guides transform to match existing Hive Joints
-----------------------------------------------------

This example leverages the idMapping method  on components to match guides to joints. This method provide access
to ids which match between the guide layer and other layers on the component ie. guides->joints.

.. code-block:: python

    from zoo.libs.hive import api

    for rig in api.iterSceneRigs():
        for comp in rig.iterComponents():
            mapping = comp.idMapping()
            deformLayer, guideLayer = comp.deformLayer(), comp.guideLayer()
            deformMap = mapping[api.constants.DEFORM_LAYER_TYPE]
            joints = deformLayer.findJoints(*deformMap.values())
            guides = guideLayer.findGuides(*deformMap.keys())

            for guide, joint in zip(guides, joints):
                transformMat = joint.transformationMatrix()
                transformMat.setScale(guide.scale(zapi.kTransformSpace), zapi.kTransformSpace)
                guide.setWorldMatrix(transformMat.asMatrix())

Create a guide programmatically.
--------------------------------

.. code-block:: python

    # creation is just as easy but more information is needed if you don't want the defaults
    #create a guide
    data = {
                "name": "godnode",
                "translate": [
                    0.0,
                    10.0,
                    0.0],
                "rotate": [   # rotation are in quaternions
                    0.0,
                    0.0,
                    0.0,
                    1.0],
                "rotationOrder": 0,
                "shape": "godnode", # can be a string for a shape in the library or a dict
                "id": "godnode",  # hive internal id to set
                "parent": arm.guideLayer().guide("mid"), # must be a hiveclass
                "children": [],
            }
    arm.guideLayer().createGuide(**data)  # done, adds a new guide and all the meta data etc
    # same with the rigLayer, deformLayer inputs and outputs all the same jazz

    # lets now parent the two components the arm is driven by the godnode
    arm.setParent(godNode, godNode.guideLayer().guide("godnode"))


Casting Scene Objects to Hive Objects.
--------------------------------------


.. code-block:: python

    from zoo.libs.maya import zapi
    for i in zapi.selected():
        component = api.componentFromNode(i) # returns the attached component if any or None
        rig = api.rigFromNode(i)# same but grabs a rig instance instead

        print(component, rig)


Grouping components
--------------------

.. code-block:: python

    char.createGroup("myGroup", components=ri.components())
    # current group names
    rig.groupNames()
    # retrieve components of a group is a generate function
    rig.iterComponentsForGroup("myGroup")
    # delete a group
    rig.removeGroup("myGroup")

Upgrading Rigs via the commandline or terminal.
-----------------------------------------------

This script shows how you could use a mayapy/batch session to upgrade a hive rig.

With the below Commandline script make sure you change the paths for your setup.::

    set MAYA_MODULE_PATH=zootoolspro/install/core/extensions/maya;
    set ZOO_LOG_LEVEL=DEBUG
    mayapy.exe upgrade_hive_rig_cli.py --scene my_rig_scene.ma --outputPath my_rig_scene_upgraded.ma


upgrade_hive_rig_cli.py

.. literalinclude:: ./resources/upgrade_hive_rig_cli.py
    :language: python
    :lines: 13-
