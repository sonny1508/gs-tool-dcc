"""Hive post buildscript template.  Blueprint for creating Hive buildscripts.


------------ TO CREATE YOUR NEW BUILD SCRIPT ----------------
Copy/paste this file and rename the `filename`, `class name` and the `id` ( id = "example" )

To enable the buildscript:

Change:

    class ExampleBuildScript(object):

To:

    class YourBuildScript(api.BaseBuildScript):

To assign to your rig in the Hive UI, reload Zoo Tools:

    ZooToolsPro (shelf) > Dev (purple icon) > Reload (menu item)

Open Hive UI and set the build script under:

    Settings (right top cog icon) >  Scripts > Build Scripts (dropdown combo box)

Be sure to reload Zoo Tools with any script changes.


------------ BUILD SCRIPT DOCUMENTATION ----------------

More Hive Build Script documentation found at:
    https://create3dcharacters.com/zoo-dev-documentation/packages/zoo_hive/buildscripting.html

Common build script code examples:
    https://create3dcharacters.com/zoo-dev-documentation/packages/zoo_hive/buildscripting_examples.html

"""

from maya import cmds
from zoo.libs.hive import api
from zoo.libs.maya.cmds.sets import selectionsets


class DinoCarnivoreBuildscript(api.BaseBuildScript):
    """

    .. note::

        Best to read the properties method in the base class :func:`api.BaseBuildScript.properties`

    """
    # unique identifier for the plugin which will be referenced by the registry.
    id = "dinoCarnivore_buildscript"  # change id to name that will appear in the hive UI.

    def postPolishBuild(self, properties):
        """Manages Selection Sets for carnivore dinosaurs.
        """
        # Delete neckBase_M_sSet ----------------------------
        if cmds.objExists("neckBase_M_sSet"):
            cmds.delete("neckBase_M_sSet")

        # Disable selection sets from marking menu ----------------------------
        disableMenuSets = ["tongue_M_sSet", "jaw_M_sSet"]
        for sSet in disableMenuSets:
            if cmds.objExists(sSet):
                selectionsets.markingMenuSetup(sSet, icon="", visibility=False, parentSet="")

        # Parent fingers_*_sSet to armClavHand_*_sSet, remove hand_*_sSet ----------------------------
        for side in ["L", "R"]:
            if cmds.objExists("fingers_{}_sSet".format(side)):
                selectionsets.unParentAll("fingers_{}_sSet".format(side))
                selectionsets.parentSelectionSets(["fingers_{}_sSet".format(side)], "armClavHand_{}_sSet".format(side))
                cmds.delete("hand_{}_sSet".format(side))
            if cmds.objExists("toe_back_{}_sSet".format(side)):
                selectionsets.unParentAll("toe_back_{}_sSet".format(side))
                selectionsets.parentSelectionSets(["toe_back_{}_sSet".format(side)], "leg_{}_sSet".format(side))

        # Add neckBase_M_00_anim to head_M_sSet ----------------------------
        if cmds.objExists("neckBase_M_00_anim"):
            selectionsets.addSelectionSet("head_M_sSet", ["neckBase_M_00_anim"])

        # Tail set icon to circleAqua ----------------------------
        if cmds.objExists("tail_M_sSet"):
            selectionsets.setIcon("tail_M_sSet", "st_circleAqua")