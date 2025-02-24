"""Tortoise Hive Build Script.

Handles
- Animator selection sets
- Squished eye mod
- Setting default attribute settings on the spline spines components
- Blendshape Attribute Connections onto jaw and eye controls


------------ BUILD SCRIPT UI DOCUMENTATION ----------------

More Hive Build Script documentation found at:
    https://create3dcharacters.com/zoo-dev-documentation/packages/zoo_hive/buildscripting.html

Common build script code examples:
    https://create3dcharacters.com/zoo-dev-documentation/packages/zoo_hive/buildscripting_examples.html

"""

from maya import cmds

from zoo.libs.hive import api
from zoo.libs.maya.cmds.objutils import attributes
from zoo.libs.maya.cmds.sets import selectionsets


class TortoiseBuildScript(api.BaseBuildScript):
    """

    .. note::

        Best to read the properties method in the base class :func:`api.BaseBuildScript.properties`

    """
    # unique identifier for the plugin which will be referenced by the registry.
    id = "tortoise_buildScript"
    neckShowAttrs = ["tweaker00Vis", "tweaker01Vis", "tweaker02Vis", "upVectorVis"]
    neckHideAttrs = ["ctrl01Vis", "hipsVis", "hipSwingVis"]
    legHideAttrs = ["ctrl00Vis", "ctrl01Vis", "hipsVis", "hipSwingVis"]
    legShowAttrs = ["tweaker01Vis"]
    selSetSuffix = "sSet"

    def postPolishBuild(self, properties):
        """Executed after the polish stage.
        """
        # CTRL NAMES from Hive API ------------------
        footFront_L = self.rig.legFront_L.rigLayer().control("ctrl02")  # python object, for string: str(footFront_L)
        footFront_R = self.rig.legFront_R.rigLayer().control("ctrl02")
        footBack_L = self.rig.legBack_L.rigLayer().control("ctrl02")
        footBack_R = self.rig.legBack_R.rigLayer().control("ctrl02")
        neckTop_M = self.rig.neck_M.rigLayer().control("ctrl02")
        head_M = self.rig.head_M.rigLayer().control("fk00")
        eye_L = self.rig.eye_L.rigLayer().control("fk01")
        eye_R = self.rig.eye_R.rigLayer().control("fk01")
        eye0_L = self.rig.eye_L.rigLayer().control("fk00")
        eye0_R = self.rig.eye_R.rigLayer().control("fk00")
        jaw_M = self.rig.jaw_M.rigLayer().control("fk00")

        eyeJnt_L = self.rig.eye_L.deformLayer().joint("fk01")
        eyeJnt_R = self.rig.eye_R.deformLayer().joint("fk01")

        # ATTR VISIBILITY --------------------------------------
        # Neck Vis
        for attr in self.neckShowAttrs:
            attributes.attributeDefault(str(neckTop_M), attr, 1)
        for attr in self.neckHideAttrs:
            attributes.attributeDefault(str(neckTop_M), attr, 0)

        # Leg Vis
        feetCtrls = [str(footFront_L), str(footFront_R), str(footBack_L), str(footBack_R)]

        for footCtrl in feetCtrls:
            for attr in self.legHideAttrs:
                attributes.attributeDefault(str(footCtrl), attr, 0)
            for attr in self.legShowAttrs:
                attributes.attributeDefault(str(footCtrl), attr, 1)
            attributes.attributeDefault(str(footCtrl), "ctrl02_space", 1)

        # Head in world --------------------------
        attributes.attributeDefault(str(head_M), "fk00_space", 1)

        # SQUISH NON-UNIFORM EYES --------------------------------------
        eyeJoints = [eyeJnt_L, eyeJnt_R]
        for jnt in eyeJoints:
            cmds.setAttr("{}.segmentScaleCompensate".format(str(jnt)), 0)
            cmds.disconnectAttr(cmds.listConnections("{}.scale".format(str(jnt)),
                                                     source=True,
                                                     plugs=True)[0],
                                "{}.scale".format(str(jnt))
                                )
        cmds.setAttr("{}.scaleY".format(str(eye0_L)), 0.5)
        cmds.setAttr("{}.scaleY".format(str(eye0_R)), 0.5)
        # Del eye00 control shape nodes
        cmds.delete(cmds.listRelatives(str(eye0_L), shapes=True))
        cmds.delete(cmds.listRelatives(str(eye0_R), shapes=True))

        # BLENDSHAPES ---------------------------------------------
        blendshapeNode = "headBlendShape"  # the name of the tortoise head blendshape on the head mesh.
        if cmds.objExists(blendshapeNode):  # no blendshape found so skip
            attributes.labelAttr("Shapes", str(eye_L))
            attributes.labelAttr("Shapes", str(eye_R))
            attributes.labelAttr("Shapes", str(jaw_M))
            # source, sourceAttr, target, targetAttr, default, min (can be None), max (can be None)
            attributes.createConnectAttrs(blendshapeNode, "topLid_L", str(eye_L), "topLid", 0.0, 0.0, 1.0)
            attributes.createConnectAttrs(blendshapeNode, "topLid_R", str(eye_R), "topLid", 0.0, 0.0, 1.0)
            attributes.createConnectAttrs(blendshapeNode, "botLid_L", str(eye_L), "botLid", 0.0, 0.0, 1.0)
            attributes.createConnectAttrs(blendshapeNode, "botLid_R", str(eye_R), "botLid", 0.0, 0.0, 1.0)
            attributes.createConnectAttrs(blendshapeNode, "eyeSmile_L", str(eye_L), "eyeSmile", 0.0, 0.0, 1.0)
            attributes.createConnectAttrs(blendshapeNode, "eyeSmile_R", str(eye_R), "eyeSmile", 0.0, 0.0, 1.0)
            attributes.createConnectAttrs(blendshapeNode, "topLidFix_L", str(eye_L), "topLidFix", 0.0, 0.0, 1.0)
            attributes.createConnectAttrs(blendshapeNode, "topLidFix_R", str(eye_R), "topLidFix", 0.0, 0.0, 1.0)
            attributes.createConnectAttrs(blendshapeNode, "smileMouthOpen_L", str(jaw_M), "smileOpen_L", 0.0, 0.0, 1.0)
            attributes.createConnectAttrs(blendshapeNode, "smileMouthOpen_R", str(jaw_M), "smileOpen_R", 0.0, 0.0, 1.0)

        # SELECTION SETS --------------------------------------------------------
        # Create All and Body sets -------------------------------
        allSSet = selectionsets.addSSetZooOptions("all_sSet",
                                                  [],
                                                  icon="st_starYellow",
                                                  visibility=True)
        bodySet = selectionsets.addSSetZooOptions("body_sSet",
                                                  [],
                                                  icon="st_starOrange",
                                                  visibility=True,
                                                  parentSet=allSSet)
        faceSet = selectionsets.addSSetZooOptions("face_sSet",
                                                  [],
                                                  icon="st_circleRed",
                                                  visibility=True,
                                                  parentSet=allSSet)
        headNeckSet = selectionsets.addSSetZooOptions("headNeck_sSet",
                                                      [],
                                                      icon="st_squarePink",
                                                      visibility=False,
                                                      parentSet=bodySet)
        eyesSet = selectionsets.addSSetZooOptions("eyes_sSet",
                                                  [],
                                                  icon="st_squarePink",
                                                  visibility=False,
                                                  parentSet=faceSet)

        components = list(self.rig.iterComponents())
        autoSets = list()
        for comp in components:
            ctrlSet = comp.rigLayer().selectionSet()
            sel = selectionsets.addSelectionSet("_".join([comp.name(), comp.side(), self.selSetSuffix]),
                                                [ctrlSet.fullPathName()], flattenSets=True)
            if sel in ["tail_M_sSet", "god_M_sSet", "body_M_sSet"]:
                selectionsets.markingMenuSetup(sel, icon="st_squarePink", visibility=False, parentSet=bodySet)
            elif sel in ["head_M_sSet", "neck_M_sSet"]:
                selectionsets.markingMenuSetup(sel, icon="st_squarePink", visibility=False, parentSet=headNeckSet)
            elif "legBack" in sel:
                selectionsets.markingMenuSetup(sel, icon="st_trianglePink", visibility=True, parentSet=bodySet)
            elif "legFront" in sel:
                selectionsets.markingMenuSetup(sel, icon="st_trianglePurple", visibility=True, parentSet=bodySet)
            elif "eye" in sel:
                selectionsets.markingMenuSetup(sel, icon="st_squarePink", visibility=False, parentSet=eyesSet)
            elif "jaw_M_sSet" == sel:
                selectionsets.markingMenuSetup(sel, icon="st_squarePink", visibility=False, parentSet=faceSet)
            autoSets.append(sel)

        cmds.sets(str(eye0_L), remove="eye_L_sSet")  # remove eye00 as not used by animator
        cmds.sets(str(eye0_R), remove="eye_R_sSet")

    def preDeleteRig(self, properties):
        """Executed when the entire hive rig gets deleted.

        .. Note::

            :func:`preDeleteComponents` gets run before this method.

        """
        eyeL = self.rig.component("eye", "L")
        eyeR = self.rig.component("eye", "R")
        for eyeComp in (eyeL, eyeR):
            if eyeComp is None:
                continue
            rigLayer = eyeComp.rigLayer()
            if rigLayer:
                eye0_L = rigLayer.control("fk00")
                eye0_L.attribute("scaleY").set(1.0)
            deformLayer = eyeComp.deformLayer()
            if deformLayer:
                eyeJnt_L = deformLayer.joint("fk01")
                eyeJnt_L.attribute("scaleY").set(1.0)
                eyeJnt_L.attribute("segmentScaleCompensate").set(1)
