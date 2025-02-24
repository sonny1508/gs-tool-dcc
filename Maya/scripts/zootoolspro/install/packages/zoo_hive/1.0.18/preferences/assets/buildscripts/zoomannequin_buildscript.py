"""Build script for the Zoo Mannequin rig.


------------ BUILD SCRIPT DOCUMENTATION ----------------

More Hive Build Script documentation found at:
    https://create3dcharacters.com/zoo-dev-documentation/packages/zoo_hive/buildscripting.html

Common build script code examples:
    https://create3dcharacters.com/zoo-dev-documentation/packages/zoo_hive/buildscripting_examples.html

"""

from maya import cmds

from zoo.libs.hive import api
from zoo.libs.maya.cmds.sets import selectionsets
from zoo.libs.maya.cmds.objutils import attributes


class ZooMannequinBuildScript(api.BaseBuildScript):
    id = "zooMannequinBuildScript"

    def postPolishBuild(self, properties):
        """Polish Zoo Mannequin
        """
        breakValue = 65.0
        # Foot break attributes default values to 65.0 -----------------------------------
        for leg in self.rig.componentsByType("legcomponent"):
            panel = leg.controlPanel()
            panel.footBreak.setDefault(breakValue)
            panel.footBreak.set(breakValue)
        if not cmds.objExists("visor_M_sSet"):
            # old template so ignore
            return
        # Custom Selection Sets -----------------------------------------
        selectionsets.addSSetZooOptions("face_sSet",
                                        [],
                                        icon="st_circlePink",
                                        visibility=True,
                                        parentSet="all_sSet",
                                        soloParent=True)
        selectionsets.markingMenuSetup("visor_M_sSet", visibility=False, parentSet="face_sSet", soloParent=True)
        if cmds.objExists("heel_bend_L_00_anim_space"):
            selectionsets.markingMenuSetup("heel_bend_L_sSet", visibility=False, parentSet="leg_L_sSet", soloParent=True)
            selectionsets.markingMenuSetup("heel_bend_R_sSet", visibility=False, parentSet="leg_R_sSet", soloParent=True)
        # Visibility Toggles, Visor Geo & Ctrl, Feet Bendy FK --------------------------------------------

        # Visor Ctrl Vis
        headNode = self.rig.head_M.rigLayer().control("head").fullPathName()
        attributes.visibilityConnectObjs("visorCtrl", headNode, ["visor_M_00_anim_space"],
                                         nonKeyable=True, defaultValue=True)
        # Visor Geo Vis
        attributes.visibilityConnectObjs("visorGeo", headNode, ["visor_geo"],
                                         nonKeyable=True, defaultValue=True)
        attributes.addProxyAttribute("visor_M_00_anim", headNode, "visorGeo", proxyAttr="")

        # Heel Bendy Vis
        if not cmds.objExists("heel_bend_L_00_anim_space"):
            return

        hellBendVisAttr = "heelBendVis"
        legLNode = self.rig.leg_L.rigLayer().control("endik").fullPathName()
        legRNode = self.rig.leg_R.rigLayer().control("endik").fullPathName()

        if legLNode:
            attributes.visibilityConnectObjs(hellBendVisAttr, legLNode, ["heel_bend_L_00_anim_space"],
                                             nonKeyable=True, defaultValue=False)
            attributes.visibilityConnectObjs(hellBendVisAttr, legRNode, ["heel_bend_R_00_anim_space"],
                                             nonKeyable=True, defaultValue=False)


