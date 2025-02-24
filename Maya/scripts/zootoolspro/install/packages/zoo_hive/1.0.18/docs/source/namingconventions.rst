Naming Conventions
####################################################

Rigging requires a specific naming convention that is both strict and adaptable.
Hive offers a Rule-based Configuration solution that allows for the definition of naming conventions.
The solution uses presets, which can be attached to rigs and components,
including guides, joints, animation controls, and dependency nodes.
Additionally, the naming conventions can be extended to support new components at any time.
Hive also provides a user interface for modifying these conventions extensively.

Presets are hierarchical where children inherit from parent presets and at the root(Hidden in the UI)
is our default zooTools preset allowing us to roll out changes and new components without affecting
your custom presets.

.. note::
    Conventions applied to a rig is saved into the rigs meta data and the saved template making it very
    easier apply once and reuse assignments.


WalkThrough
-----------

In the following section, we will walk through how to modify the naming convention for the arm component.

First open the UI.

|

.. figure:: ./resources/namingcon_menu.png
    :align: center
    :alt: alternate text
    :figclass: align-center

    :colorlightgrayitalic:`Clicking the Cog icon will open the Naming Convention UI.`

We recommend when creating your own preset as a child of the default user preset if you're individual, but if
you're a studio then create it at the root.

Presets can be applied to the rig as a whole or to individual component you'll see in our UE presets we have specific
presets for certain components, in the case of UE their default skeleton naming isn't consistent so we had to create
custom presets that handle those cases.

.. figure:: ./resources/namingcon_defaultuserPreset.png
    :align: center
    :alt: alternate text
    :figclass: align-center


With the DefaultUserPreset selected and a new Preset in my case i called it "myCustomPreset"

.. figure:: ./resources/namingcon_createPreset.png
    :align: center
    :alt: alternate text
    :figclass: align-center


Select the newly created preset so we can modify it.

.. figure:: ./resources/namingcon_selectpreset.png
    :align: center
    :alt: alternate text
    :figclass: align-center


Now lets modify the arm component, in the UI the "HiveType" in all configurations from components, the Rig and globals.

.. figure:: ./resources/namingcon_selectHiveType.png
    :align: center
    :alt: alternate text
    :figclass: align-center

    :colorlightgrayitalic:`Select the component you wish to modify.`


Naming conventions are dealt with by Rules each rule can be modified for any component, let's modifying the name
for the skin joints which get exported if you're going to games.

.. figure:: ./resources/namingcon_selectRule.png
    :align: center
    :alt: alternate text
    :figclass: align-center

    :colorlightgrayitalic:`Select the Rule you wish to modify.`


Now lets modify the naming convention of all skin joints on this component.
The Rule Field allows you to change the order and fields to be used, typing in the field will display an autocomplete
drop down to help you determine what you have access too.

.. note:: all fields with a rule must be separated by a single '_'.

.. figure:: ./resources/namingcon_customRule.png
    :align: center
    :alt: alternate text
    :figclass: align-center


We'll change our convention to use you'll the hive joint "id" and the component side.
You'll see the Rule Preview automatically update, this is randomly generated values based on the rule convention
you provide.

.. figure:: ./resources/namingcon_ruleMod.png
    :align: center
    :alt: alternate text
    :figclass: align-center


With the rule modified you can now rebuild the skeleton and joint names after you assign the preset
:ref:`See below<AssignNamingConventions_example>` and the joint names will update.
However lets go further and modify the "end" joint of the arm component to be hand.

.. note::
    Modifying fields affects all rules on the currently active component only.

.. figure:: ./resources/namingcon_idname.png
    :align: center
    :alt: alternate text
    :figclass: align-center

    :colorlightgrayitalic:`Select the Id Field.`

Double click and type "hand", The end name refers to the hive ID which is used many sections
of a component. For flexibility the component also provides 'endfk' and 'endik' for animation controls.

.. figure:: ./resources/namingcon_idmodhand.png
    :align: center
    :alt: alternate text
    :figclass: align-center

    :colorlightgrayitalic:`Change the end field name to be hand.`

There are times where ids won't exist in the UI these come from procedurally generated elements of a components
like twists, bendy, spine joints etc. In this we can create a new field name and value. Here we'll create a
new name referring to the uprTwist00 id.

.. figure:: ./resources/namingcon_customfield.png
    :align: center
    :alt: alternate text
    :figclass: align-center

    :colorlightgrayitalic:`Adding a missing field name and value for dynamic ids.`

Now simply save and any modifications you've made across any and all components, presets,rules will appropriately be
saved out. Saving will only save the modification in a component.

.. _AssignNamingConventions_example:

Assigning Naming Conventions.
-----------------------------

Since we've now created a new preset, made some changes lets update a rig with this preset and see the new changes.

For demo purposes i've created a single arm component but you might have a full character rig.

To Assign a preset go to the rig settings.

.. figure:: ./resources/namingcon_rigsettings.png
    :align: center
    :alt: alternate text
    :figclass: align-center

    :colorlightgrayitalic:`Click the rig settings cog icon.`

Now under the "Naming" section click the "ZooToolsPro" button which displays the currently active preset.

.. figure:: ./resources/namingcon_assignbtn.png
    :align: center
    :alt: alternate text
    :figclass: align-center

    :colorlightgrayitalic:`Clicking the naming button popups the preset view.`

Select our preset which will apply the assign the preset to the rig but won't apply the configuration until
next build.

.. figure:: ./resources/namingcon_assignpreset.png
    :align: center
    :alt: alternate text
    :figclass: align-center

    :colorlightgrayitalic:`Selecting our preset to make active.`

Once assigned click build skeleton since we've modified the "skinJointName" rule.

.. figure:: ./resources/namingcon_buildskel.png
    :align: center
    :alt: alternate text
    :figclass: align-center

    :colorlightgrayitalic:`Build the skeleton to apply the naming convention.`

Now in the outliner if you check the joint names for the "end" and "uprTwist00" id joints as well
as the convention used for arm joints you'll see that the "end" has been named "hand" and uprTwist00 has been
named "awesometwist00". You'll also see that the rule had affect where the shldr joint was renamed from
"arm_L_shldr_jnt" to "shldr_L".

.. figure:: ./resources/namingcon_checkskel.png
    :align: center
    :alt: alternate text
    :figclass: align-center

    :colorlightgrayitalic:`Check the skeleton for a naming changes`


Technical Details
-----------------

.. note:: This section is a WIP.

In this section we're explain how naming conventions work from more of a technical point of view.

First thing to know is naming conventions like many parts of Zoo is saved as JSON data and can be queried,
modified, deleted and saved via the API.

We have two configuration files defined as different file format extensions.

#. Presets(".namingpreset")
#. Configurations(".namingcfg")

Presets are kept quite simple they just determine which configurations we have modified in the preset
for the preset hierarchy we store that as part of the zoo hive preferences.

Preset JSON data structure

.. code-block:: json

    {
        "name": "ZooToolsPro",
        "configs": [
            {
                "name": "zootoolsProGlobalVChainComponent",
                "hiveType": "vchaincomponent"
            },
        ]
    }

The preset config in the above example links the "vchaincomponent" hive type, the hive type is
used internal in hive to retrieve the appropriate configuration for the component or rig. Before
any api calls require the naming access.
The name refers the uniquely named(typically autogenerated) configuration.

Configuration Data Structure

Configurations are much more detailed and can contain only changes made over the top of the parent component
configuration based on the preset hierarchy or it can contain everything. Naming configuration structure and core
api isn't Hive specific only presets and hierarchy plus resolver are. You can find out about naming conventions
:ref:`here <zoocore_naming>`.

Hive Naming Convention API Example
----------------------------------
# Docs coming soon