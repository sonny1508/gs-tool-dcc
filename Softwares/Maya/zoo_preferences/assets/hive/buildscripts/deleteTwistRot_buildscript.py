"""Hive post buildscript for deleting twist rotation for robots on arms and legs.

Keeps stretch on limbs but disables twist.


------------ BUILD SCRIPT UI DOCUMENTATION ----------------

More Hive Build Script documentation found at:
    https://create3dcharacters.com/zoo-dev-documentation/packages/zoo_hive/buildscripting.html

Common build script code examples:
    https://create3dcharacters.com/zoo-dev-documentation/packages/zoo_hive/buildscripting_examples.html


"""

from maya import cmds

from zoo.libs.hive import api


class DelTwistRotBuildScript(api.BaseBuildScript): 
    # unique identifier for the plugin which will be referenced by the registry.
    id = "deleteTwistRotation"

    def postPolishBuild(self, properties):
        """Executed after the polish stage.

        Useful for building space switching, optimizing the rig, binding asset meta data and
        preparing for the animator.
        """
        delTwistNodes = ["*shldr_jntTwistServer_jnt", "*TwistOffsetTwist_quatToEuler", "*TwistOffsetTwist_decomp",
                         "*TwistOffsetTwist_matMult", "*Twist*rotMult_fMath", "*Twist*offsetRot_addDoubleLinear"]
        for node in delTwistNodes:
            if cmds.objExists(node):
                cmds.delete(node)


