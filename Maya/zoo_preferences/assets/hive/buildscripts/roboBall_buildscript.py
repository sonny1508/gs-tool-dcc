"""RoboBall Build Script for adding custom selection sets to the rig after Polish. 

Handles
- Animator selection sets


------------ BUILD SCRIPT UI DOCUMENTATION ----------------

More Hive Build Script documentation found at:
    https://create3dcharacters.com/zoo-dev-documentation/packages/zoo_hive/buildscripting.html

Common build script code examples:
    https://create3dcharacters.com/zoo-dev-documentation/packages/zoo_hive/buildscripting_examples.html


"""
from maya import cmds

from zoo.libs.hive import api
from zoo.libs.maya.cmds.sets import selectionsets


class RoboBallBuildScript(api.BaseBuildScript):
    """Tweaks the selection sets created by the selectionset_biped_buildscript
    """
    # unique identifier for the plugin which will be referenced by the registry.
    id = "roboBallBuildScript"

    def postPolishBuild(self, properties):
        """Executed after the polish stage.

        Useful for building space switching, optimizing the rig, binding asset meta data and
        preparing for the animator.
        """
        if cmds.objExists("antenna_M_sSet"):
            selectionsets.markingMenuSetup("antenna_M_sSet", icon="st_triangleOrange", visibility=True,
                                           parentSet="all_sSet", soloParent=True)
        if cmds.objExists("body_M_sSet"):
            selectionsets.markingMenuSetup("body_M_sSet", icon="st_circleOrange", visibility=False)