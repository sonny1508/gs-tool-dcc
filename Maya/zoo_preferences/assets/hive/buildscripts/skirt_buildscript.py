"""Skirt Build Script for adding visibility attributes to the rig.

.. note::
    Hardcoded to "skirt" component names change in the code (line 43) if renaming attributes.
    Eg. skirt_M, skirtTierA_L, skirtTierA_R, skirtTierAFrnt_M, skirtTierABck_M

Handles:
#. Control visibility attributes
#. Control visibility connections
#. Handles user modified (add/delete) tier layers in the rig


------------ BUILD SCRIPT DOCUMENTATION ----------------

More Hive Build Script documentation found at:
    https://create3dcharacters.com/zoo-dev-documentation/packages/zoo_hive/buildscripting.html

Common build script code examples:
    https://create3dcharacters.com/zoo-dev-documentation/packages/zoo_hive/buildscripting_examples.html

Author: Andrew Silke
"""

import string

from maya import cmds
from zoo.libs.hive import api
from zoo.libs.maya.cmds.objutils import attributes


class SkirtBuildScript(api.BaseBuildScript):
    """
    """
    id = "skirt"  # appears in the Hive UI.

    def postPolishBuild(self, properties):
        """Executed after the polish stage.

        Useful for building space switching, optimizing the rig, binding asset meta data and
        preparing for the animator.
        """
        baseName = "skirt"  # can be renamed, duplicate script and rename along with the id (above and class name)
        middle = "M"
        left = "L"
        right = "R"
        back = "Bck"
        front = "Frnt"
        tier = "Tier"

        rig = self.rig

        tertiaryComponents = list()
        leftRightComp = list()

        primaryShapes = list()
        secondaryShapes = list()
        tertiaryShapes = list()
        lockHideShapes = list()

        teritaryControls = list()
        lockHideControls = list()

        mainComp = rig.component(baseName, middle)  # is skirt_M, None if not found
        if not mainComp:  # skirt not found so bail
            return
        mainCompLayer = mainComp.rigLayer()

        # Get all the tertiary component layers as python objects. Can be many tiers -------------------
        for letter in string.ascii_uppercase:  # return all the tiered components
            # Eg. skirtTierA_L, skirtTierA_R, skirtTierAFrnt_M, skirtTierABck_M
            leftComponent = rig.component("".join([baseName, tier, letter]), left)
            if leftComponent:
                tertiaryComponents.append(leftComponent.rigLayer())
                leftRightComp.append(leftComponent.rigLayer())
            rightComponent = rig.component("".join([baseName, tier, letter]), right)
            if rightComponent:
                tertiaryComponents.append(rightComponent.rigLayer())
                leftRightComp.append(rightComponent.rigLayer())
            frontComponent = rig.component("".join([baseName, tier, letter, front]), middle)
            if frontComponent:
                tertiaryComponents.append(frontComponent.rigLayer())
            backComponent = rig.component("".join([baseName, tier, letter, back]), middle)
            if backComponent:
                tertiaryComponents.append(backComponent.rigLayer())
            # Break if none found, tier limit exceeded
            if not leftComponent and not leftComponent and not leftComponent and not leftComponent:
                break

        if not tertiaryComponents:  # None found so bail
            return

        # Get tertiary control shapes list --------------------------------------
        for component in tertiaryComponents:
            for ctrl in component.iterControls():
                ctrlStr = ctrl.fullPathName()
                teritaryControls.append(ctrlStr)
                shapes = cmds.listRelatives(ctrlStr, shapes=True)
                if shapes:
                    tertiaryShapes += shapes

        allControls = list(teritaryControls)

        for ctrl in mainCompLayer.iterControls():
            allControls.append(ctrl.fullPathName())

        # Lock and hide first control in the left right components --------------------------------------
        for comp in leftRightComp:  # Find first control of each left right component record its shapes to be hidden.
            ctrl = comp.control("fk00").fullPathName()
            lockHideControls.append(ctrl)
            shapes = cmds.listRelatives(ctrl, shapes=True)
            if shapes:
                lockHideShapes += shapes

        if lockHideShapes:
            cmds.hide(lockHideShapes)
            for shape in lockHideShapes:
                attributes.lockHideAttr(shape, "visibility", lockHide=True)

        # Get the shapes for the primary and secondary controls --------------------------------------
        for i, ctrl in enumerate(mainCompLayer.iterControls()):
            shapes = cmds.listRelatives(ctrl.fullPathName(), shapes=True)
            if shapes and (i % 2) == 0 and i != 0:  # Even numbered controls and skip zero, 02, 04, 06 etc
                primaryShapes += shapes
            if shapes and (i % 2):  # Odd numbered controls 01, 03, 04 etc
                if i == 0:
                    continue
                secondaryShapes += shapes

        # Create attrs on the skirt_M_controlPanel_settings ----------------------------
        controlPanel = mainCompLayer.controlPanel().fullPathName()
        cmds.lockNode(controlPanel, lock=False)
        attributes.labelAttr("VISIBILITY", controlPanel)
        attributes.createAttribute(controlPanel,
                                   "primaryVis",
                                   attributeType="bool",
                                   nonKeyable=True,
                                   channelBox=True,
                                   defaultValue=True)
        attributes.createAttribute(controlPanel,
                                   "secondaryVis",
                                   attributeType="bool",
                                   nonKeyable=True,
                                   channelBox=True,
                                   defaultValue=False)
        attributes.createAttribute(controlPanel,
                                   "tertiaryVis",
                                   attributeType="bool",
                                   nonKeyable=True,
                                   channelBox=True,
                                   defaultValue=False)
        cmds.lockNode(controlPanel, lock=True)

        # Remove lockHideShapes from tertiaryShapes, lockHide aren't connected --------------------------
        tertiaryConnectShapes = [x for x in tertiaryShapes if x not in lockHideShapes]
        allControls = [x for x in allControls if x not in lockHideControls]

        # Make connections control panel > vis attrs ----------------------------
        for shape in primaryShapes:
            cmds.connectAttr("{}.primaryVis".format(controlPanel), "{}.visibility".format(shape))
        for shape in secondaryShapes:
            cmds.connectAttr("{}.secondaryVis".format(controlPanel), "{}.visibility".format(shape))
        for shape in tertiaryConnectShapes:
            cmds.connectAttr("{}.tertiaryVis".format(controlPanel), "{}.visibility".format(shape))

        # Add proxy attrs to controls ----------------------------------------
        for ctrl in allControls:
            attributes.labelAttr("_VISIBILITY", ctrl)
            for attr in ["primaryVis", "secondaryVis", "tertiaryVis"]:
                attributes.addProxyAttribute(ctrl, controlPanel, attr, nonKeyable=True)
