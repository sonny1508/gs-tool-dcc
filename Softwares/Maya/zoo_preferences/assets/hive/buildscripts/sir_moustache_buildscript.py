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
from zoo.libs.maya.cmds.objutils import attributes


class SirMoustacheBuildScript(api.BaseBuildScript):
    """Tweaks the selection sets created by the selectionset_biped_buildscript
    """
    # unique identifier for the plugin which will be referenced by the registry.
    id = "sirMoustacheBuildScript"

    def postPolishBuild(self, properties):
        """Executed after the polish stage.

        Useful for building space switching, optimizing the rig, binding asset meta data and
        preparing for the animator.
        """
        validSets = list()
        faceSets = ["eye_L_sSet", "eye_R_sSet", "facePivot_M_sSet", "moustache_L_sSet", "moustache_R_sSet",
                    "moustache_M_sSet", "brow_L_sSet", "brow_R_sSet", "hatPivot_M_sSet", "hat_M_sSet"]

        # Validate and hide sets ----------------------------
        for sset in faceSets:  # validate sets exist
            if cmds.objExists(sset):
                selectionsets.setMarkingMenuVis(sset, False)
                selectionsets.unParentAll(sset)
                validSets.append(sset)
        faceSets = validSets

        # Create and parent sets correctly ----------------
        if faceSets:
            selectionsets.addSSetZooOptions("face_sSet",
                                            [],
                                            icon="st_circleOrange",
                                            visibility=True,
                                            parentSet="all_sSet",
                                            soloParent=True)
            selectionsets.addSSetZooOptions("eyes_sSet",
                                            ["eye_L_sSet", "eye_R_sSet"],
                                            visibility=False,
                                            parentSet="face_sSet",
                                            soloParent=True)
            selectionsets.addSSetZooOptions("brow_M_sSet",
                                            ["brow_L_sSet", "brow_R_sSet"],
                                            visibility=False,
                                            parentSet="face_sSet",
                                            soloParent=True)
            cmds.sets("moustache_M_sSet", forceElement="face_sSet")
            cmds.sets("moustache_L_sSet", forceElement="moustache_M_sSet")
            cmds.sets("moustache_R_sSet", forceElement="moustache_M_sSet")
            cmds.sets("facePivot_M_sSet", forceElement="face_sSet")
            cmds.sets("hatPivot_M_sSet", forceElement="all_sSet")
            cmds.sets("hat_M_sSet", forceElement="hatPivot_M_sSet")
            selectionsets.setMarkingMenuVis("hatPivot_M_sSet", True)

        footLNode = self.rig.leg_L.rigLayer().control("endik").fullPathName()
        footRNode = self.rig.leg_R.rigLayer().control("endik").fullPathName()

        # Foot break attributes default values to 65.0 -----------------------------------
        cmds.addAttr('{}.footBreak'.format(footLNode), edit=True, defaultValue=65.0)
        cmds.addAttr('{}.footBreak'.format(footRNode), edit=True, defaultValue=65.0)
        cmds.setAttr('{}.footBreak'.format(footLNode), 65.0)
        cmds.setAttr('{}.footBreak'.format(footRNode), 65.0)

        # Auto bendy default to be on -----------------------------
        cmds.addAttr('{}.roundnessAuto'.format(footLNode), edit=True, defaultValue=1.0)
        cmds.addAttr('{}.roundnessAuto'.format(footRNode), edit=True, defaultValue=1.0)
        cmds.setAttr('{}.roundnessAuto'.format(footLNode), 1.0)
        cmds.setAttr('{}.roundnessAuto'.format(footRNode), 1.0)

        if cmds.objExists("arm_L_rigLayer_hrc"):  # if arm ctrl exists
            armLNode = self.rig.arm_L.rigLayer().control("endik").fullPathName()
            armRNode = self.rig.arm_R.rigLayer().control("endik").fullPathName()
            cmds.addAttr('{}.roundnessAuto'.format(armLNode), edit=True, defaultValue=1.0)
            cmds.addAttr('{}.roundnessAuto'.format(armRNode), edit=True, defaultValue=1.0)
            cmds.setAttr('{}.roundnessAuto'.format(armLNode), 1.0)
            cmds.setAttr('{}.roundnessAuto'.format(armRNode), 1.0)

        # Visibility Toggles, face, hat, and arms --------------------------------------------
        browGrps = ["brow_L_00_anim_space", "brow_R_00_anim_space"]
        eyeGrps = ["eye_L_00_anim_space", "eye_R_00_anim_space"]
        moGrps = ["moustache_L_00_anim_space", "moustache_R_00_anim_space", "moustache_M_00_anim_space"]
        hatGrps = ["hat_M_00_anim_space", "hatPivot_M_00_anim_space"]
        armsGrps = ["arm_L_rigLayer_hrc", "arm_R_rigLayer_hrc", "finger_thumb_L_rigLayer_hrc",
                    "finger_thumb_R_rigLayer_hrc", "finger_pointer_L_hrc", "finger_pointer_R_hrc", "finger_ring_L_hrc",
                    "finger_ring_R_hrc", "finger_pinky_L_hrc", "finger_pinky_R_hrc"]
        facePivotGrp = ["facePivot_M_00_anim_space"]

        eyeGeo = ["eyes_geo"]
        browsGeo = ["brows_geo"]
        moustacheGeo = ["moustache_L_geo", "moustache_R_geo"]
        hatGeo = ["hat_geo", "hat_band_geo"]
        armsGeo = ["arm_geo_L", "arm_geo_R"]

        godNode = self.rig.god_M.rigLayer().control("godnode").fullPathName()  # fullPathName() returns a string name
        headNode = self.rig.body_M.rigLayer().control("fk00").fullPathName()

        # Ctrls visibility -------
        attributes.visibilityConnectObjs("hatCtrls", headNode, hatGrps,
                                         nonKeyable=True, defaultValue=True)
        attributes.visibilityConnectObjs("facePivCtrl", headNode, facePivotGrp,
                                         nonKeyable=True, defaultValue=True)
        attributes.visibilityConnectObjs("browCtrls", headNode, browGrps,
                                         nonKeyable=True, defaultValue=True)

        attributes.visibilityConnectObjs("eyeCtrls", headNode, eyeGrps,
                                         nonKeyable=True, defaultValue=True)

        attributes.visibilityConnectObjs("moCtrls", headNode, moGrps,
                                         nonKeyable=True, defaultValue=True)
        attributes.addProxyAttribute(godNode, headNode, "hatCtrls", proxyAttr="")
        attributes.addProxyAttribute(godNode, headNode, "facePivCtrl", proxyAttr="")
        attributes.addProxyAttribute(godNode, headNode, "browCtrls", proxyAttr="")
        attributes.addProxyAttribute(godNode, headNode, "eyeCtrls", proxyAttr="")
        attributes.addProxyAttribute(godNode, headNode, "moCtrls", proxyAttr="")

        # Arm Ctrls visibility -------
        if cmds.objExists("arm_L_rigLayer_hrc"):  # if arm ctrl exists
            attributes.visibilityConnectObjs("armCtrls", headNode, armsGrps,
                                             nonKeyable=True, defaultValue=True)
            attributes.addProxyAttribute(godNode, headNode, "armCtrls", proxyAttr="")

        # Geo visibility -------
        if cmds.objExists("toonBallLegs_geo"):  # if arm ctrl exists
            attributes.labelAttr("VIS GEO", headNode)
            attributes.labelAttr("VIS GEO", godNode)
            attributes.visibilityConnectObjs("moGeo", headNode, moustacheGeo,
                                             nonKeyable=True, defaultValue=True)
            attributes.visibilityConnectObjs("eyeGeo", headNode, eyeGeo,
                                             nonKeyable=True, defaultValue=True)
            attributes.visibilityConnectObjs("browGeo", headNode, browsGeo,
                                             nonKeyable=True, defaultValue=True)
            attributes.visibilityConnectObjs("hatGeo", headNode, hatGeo,
                                             nonKeyable=True, defaultValue=True)
            attributes.addProxyAttribute(godNode, headNode, "hatGeo", proxyAttr="")
            attributes.addProxyAttribute(godNode, headNode, "browGeo", proxyAttr="")
            attributes.addProxyAttribute(godNode, headNode, "eyeGeo", proxyAttr="")
            attributes.addProxyAttribute(godNode, headNode, "moGeo", proxyAttr="")

        # Arm Geo visibility -------
        if cmds.objExists("arm_geo_L"):  # if arm geo exists
            attributes.visibilityConnectObjs("armGeo", headNode, armsGeo,
                                             nonKeyable=True, defaultValue=True)

            attributes.addProxyAttribute(godNode, headNode, "armGeo", proxyAttr="")






