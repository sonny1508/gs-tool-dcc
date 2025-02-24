"""Natalie Hive build script.

Handles
- Animator selection sets
- Custom Face integration on polish, skeleton and guides mode
- Visibility attributes for switching hair, toes, face etc
- Disables the ability to non-uniform scale certain rig parts.


------------ BUILD SCRIPT DOCUMENTATION ----------------

More Hive Build Script documentation found at:
    https://create3dcharacters.com/zoo-dev-documentation/packages/zoo_hive/buildscripting.html

Common build script code examples:
    https://create3dcharacters.com/zoo-dev-documentation/packages/zoo_hive/buildscripting_examples.html


"""

from maya import cmds

from zoo.libs.maya import zapi
from zoo.libs.hive import api
from zoo.libs.maya.cmds.objutils import attributes, layers, connections, joints
from zoo.libs.maya.cmds.sets import selectionsets


class NatalieBuildScript(api.BaseBuildScript):
    """Post polish buildscript for Natalie rig.  Handles visibility and extra attributes and the custom face rig

    .. note::

        Best to read the properties method in the base class :func:`api.BaseBuildScript.properties`

    """
    # Unique identifier which will seen in the Hive settings UI drop-down.
    id = "natalie_buildscript"

    # Show/Hide attributes
    jawHideAttrs = ["headNoseRX", "headNoseRY", "headNoseRZ", "NoseLipRX", "NoseLipRY", "NoseLipRZ", "TopLipBotLipRX",
                    "TopLipBotLipRY", "TopLipBotLipRZ", "botLipChinRX", "botLipChinRY", "botLipChinRZ", "chinHeadRX",
                    "chinHeadRY", "chinHeadRZ", "HeadNoseTX", "HeadNoseTY", "HeadNoseTZ", "nosLipTX", "nosLipTY",
                    "nosLipTZ", "topLipBotLipTX", "topLipBotLipTY", "topLipBotLipTZ", "botLipChinTX", "botLipChinTY",
                    "botLipChinTZ", "chinHeadTX", "chinHeadTY", "chinHeadTZ", "topLipBank", "botLipBank", "chinBank",
                    "AllUpDwn", "AllLR", "AllBank", "___", "____"]
    eyeHideAttrs = ["topLidRotInfoX", "topLidRotInfoY", "topLidRotInfoZ", "botLidRotInfoX", "botLidRotInfoY",
                    "botLidRotInfoZ", "topInAdjX", "topInAdjY", "topInAdjZ", "topAdjX", "topAdjY", "topAdjZ",
                    "topOutAdjX", "topOutAdjY", "topOutAdjZ", "botInAdjX", "botInAdjY", "botInAdjZ", "botAdjX",
                    "botAdjY", "botAdjZ", "botOutAdjX", "botOutAdjY", "botOutAdjZ", "topInOffsetX", "topInOffsetY",
                    "topInOffsetZ", "topOffsetX", "topOffsetY", "topOffsetZ", "topOutOffsetX", "topOutOffsetY",
                    "topOutOffsetZ", "botInOffsetX", "botInOffsetY", "botInOffsetZ", "botOffsetX", "botOffsetY",
                    "botOffsetZ", "botOutOffsetX", "botOutOffsetY", "botOutOffsetZ", "TopIn_OutIn", "Top_posOutIn",
                    "TopOut_posInOut", "BotIn_posInOut", "Bot_posInOut", "BotOut_posInOut", "Top_posLR", "TopIn_posLR",
                    "TopOut_posLR", "BotIn_posLR", "Bot_posLR", "BotOut_posLR", "TopIn_posUpDwn", "Top_posUpDwn",
                    "TopOut_posUpDwn", "BotIn_posUpDwn", "Bot_posUpDwn", "BotOut_posUpDwn", "topLidDwn", "____",
                    "_____", "______"]

    # ------------------------
    # Helper Methods
    # ------------------------

    def _faceExists(self):
        return cmds.objExists("jaw_cntrl")

    def _unlockSetVis(self, node, show=True):
        """Sets visibility, locks-hides or unlocks-show depending on the state

        :param node: object or node name
        :type node: str
        :param show: If True sets visibility on, if False visibility off.
        :type show: bool
        """
        cmds.setAttr(".".join([node, "visibility"]), lock=False)
        cmds.setAttr(".".join([node, "visibility"]), show)
        attributes.lockHideAttr(node, "visibility", lockHide=not show)

    def _hideFaceRig(self, hideJntsFollis=True, hideControls=False):
        """Hides the custom face rig in two states:

            - Joints and Follicles of the face rig (not deformation)
            - Face Controls

        :param hideJntsFollis: Hides the custom face non-deformation joints and follicles, False will show.
        :type hideJntsFollis: bool
        :param hideControls: Hides the custom face controls (in skeleton mode).  False will show the controls
        :type hideControls: bool
        """
        # Rig Joints & Follicles
        # Names here are from the custom face rig and are hardcoded names
        self._unlockSetVis("follicleGroup", not hideJntsFollis)
        self._unlockSetVis("HeadCutoffJoints_NoParent", not hideJntsFollis)
        self._unlockSetVis("faceJnts_grp", not hideJntsFollis)
        self._unlockSetVis("eyeJnts_zeroGroup_L", not hideJntsFollis)
        self._unlockSetVis("eyeJnts_zeroGroup_R", not hideJntsFollis)
        # Controls whole rig
        connections.breakAttr("faceRig_parentHead_grp.visibility")  # break connections as stays connected sometimes
        self._unlockSetVis("faceRig_parentHead_grp", not hideControls)
        self._unlockSetVis("faceRig", not hideControls)

    def _drawFaceRigJoints(self, hide=True):
        """Sets the draw state of the custom face rig non-deformation joints on the custom rig (not deformation joints)

        :param hide: If True hides the joints, False shows the joints
        :type hide: bool
        """
        jntList = ["teethTop_jnt", "teethBot_jnt", "tongue_jnt_01", "tongue_jnt_02", "tongue_jnt_03", "tongue_jnt_04"]
        joints.jointDrawHide(jntList, hide=hide)

    def _hideFaceAttrs(self, hide):
        """Show or hide the face attributes

        :param hide: if True hide, if False show
        :type hide: bool
        """
        attributes.hideAttrs("jaw_cntrl", self.jawHideAttrs, hide=hide)
        attributes.hideAttrs("eye_cntrl_L", self.eyeHideAttrs, hide=hide)
        attributes.hideAttrs("eye_cntrl_R", self.eyeHideAttrs, hide=hide)

    # ------------------------
    # Build Script Methods
    # ------------------------

    def postGuideBuild(self, properties):
        """Executed once all guides on all components have been built into the scene.
        """
        # Skip if face rig doesn't exist
        if not self._faceExists():
            return
        self._hideFaceRig(hideJntsFollis=False, hideControls=False)
        self._drawFaceRigJoints(hide=False)
        self._hideFaceAttrs(hide=False)

    def postDeformBuild(self, properties):
        """ Hides the custom face rig, and will show the single chain deformation joints.

        Executed after the deformation and I/O layers has been built for all components
        including all joints.
        """
        # Skip if face rig doesn't exist
        if not self._faceExists():
            return
        self._hideFaceRig(hideJntsFollis=True, hideControls=True)
        self._drawFaceRigJoints(hide=True)
        self._hideFaceAttrs(hide=False)

    def preDeleteRigLayer(self, properties):
        if not self._faceExists():
            return

        faceParentGrp = zapi.nodeByName("faceRig_parentHead_grp")
        scaleAttr = faceParentGrp.attribute("scale")

        scaleConstraint = scaleAttr.sourceNode()
        if scaleConstraint is not None and scaleConstraint.apiType() == zapi.kNodeTypes.kScaleConstraint:
            scaleAttr.disconnectAll(source=True)
            scaleConstraint.delete()
        self._ensureParentConstraintIsRemoved(faceParentGrp)
        sourceAttr = scaleAttr.source()
        if sourceAttr:
            sourceAttr.disconnect(scaleAttr)
        scaleAttr.set((1, 1, 1))

    def _ensureParentConstraintIsRemoved(self, node):
        """Backwards Compatibility for removing parent constraint on face rig which
        previously was manually added.
        :param node:
        :type node: :class:`zapi.DagNode`
        """
        translateAttr = node.attribute("translateX")
        parentConstraint = translateAttr.sourceNode()

        if parentConstraint is not None and parentConstraint.apiType() == zapi.kNodeTypes.kParentConstraint:
            parentConstraint.delete()

    def postRigBuild(self, properties):
        # Skip if face rig doesn't exist
        if not self._faceExists():
            return

        # connect the head local scale to the face rig
        headOutputLayer = self.rig.head_M.outputLayer()
        faceParentGrp = zapi.nodeByName("faceRig_parentHead_grp")
        self._ensureParentConstraintIsRemoved(faceParentGrp)
        zapi.buildConstraint(faceParentGrp,
                             drivers={"targets": (("", headOutputLayer.outputNode("head")),)
                                      },
                             constraintType="parent",
                             trace=False,
                             maintainOffset=True)
        zapi.buildConstraint(faceParentGrp,
                             drivers={"targets": (("", headOutputLayer.outputNode("head")),)
                                      },
                             constraintType="scale",
                             trace=False,
                             maintainOffset=True)

    def postPolishBuild(self, properties):
        """Executed after the polish stage.

        Adds:
            - Hair, face, toeL and toeR visibility toggle attributes on the controls.
            - Face controls to the "natalie_ctrlLayer"
            - Hides non deformation joints and follicles on the face rig
            - Adds custom animator selection sets
        """
        rig = self.rig  # The current rig object from the hive API, in this case the Natalie rig.
        faceExists = self._faceExists()
        toesExist = cmds.objExists("toe01_L_00_anim")
        hairExists = cmds.objExists("hairTop_C_00_anim")

        if faceExists:  # Skip if face rig doesn't exist
            # Lock and hide face rig joints and follicles -----------------------
            self._hideFaceRig(hideJntsFollis=True, hideControls=False)
            self._drawFaceRigJoints(hide=True)
            self._hideFaceAttrs(hide=True)

        # Get Hive Controls ------------------------
        # Control name ID's are found on the control transform: Attribute Editor > Extra Attributes > Zoo Hive ID
        godNode = rig.god_M.rigLayer().control("godnode").fullPathName()  # fullPathName() returns a string name
        hipsNode = rig.spine_M.rigLayer().control("cog").fullPathName()
        headNode = rig.head_M.rigLayer().control("head").fullPathName()
        footLNode = rig.leg_L.rigLayer().control("endik").fullPathName()
        footRNode = rig.leg_R.rigLayer().control("endik").fullPathName()

        # Create visibility label attributes ----------------------------
        attributes.labelAttr("Visibility", godNode)
        attributes.labelAttr("Visibility", hipsNode)
        attributes.labelAttr("Visibility", headNode)

        # Create face visibility attribute and connections ----------------------------
        if faceExists:
            faceVisAttr = "faceVis"
            attributes.visibilityConnectObjs(faceVisAttr, godNode, ["faceRig_parentHead_grp"],
                                             nonKeyable=True, defaultValue=True)
            # Add face group to ctrl layer -------------------------
            displayLayerName = rig.controlDisplayLayer().fullPathName()
            layers.addToLayer(displayLayerName, ["faceRig_parentHead_offset"], ref=False, playback=False)
            layers.addToLayer(displayLayerName, ["eyes_parentTo_MoveAll_grp"], ref=False, playback=False)

        # Create hair visibility attribute and connections ----------------------------
        if hairExists:
            hairVisAttr = "hairVis"
            hairRoots = list()  # Root transform node of each hair component, there are 13 hair components.
            for comp in rig.iterComponents():  # Find all root transforms of components with "hair" in the name
                if "hair" in comp.name().lower():
                    hairRoots.append(comp.rootTransform().fullPathName())  # fullPathName() returns a string
            if hairRoots:
                attributes.visibilityConnectObjs(hairVisAttr, str(godNode), hairRoots,
                                                 channelBox=True, nonKeyable=True, defaultValue=True)
                attributes.addProxyAttribute(str(headNode), str(godNode), hairVisAttr, proxyAttr="")
                attributes.addProxyAttribute(str(hipsNode), str(godNode), hairVisAttr, proxyAttr="")

        # Create toes visibility attribute and connections ----------------------------
        if toesExist:
            toeLVisAttr = "toesVis"
            toeLObjs = [rig.toe01_L.rootTransform().fullPathName(), rig.toe02_L.rootTransform().fullPathName(),
                        rig.toe03_L.rootTransform().fullPathName(), rig.toe04_L.rootTransform().fullPathName(),
                        rig.toe05_L.rootTransform().fullPathName()]
            attributes.visibilityConnectObjs(toeLVisAttr, footLNode, toeLObjs,
                                             channelBox=True, nonKeyable=True, defaultValue=True)

            toeRVisAttr = "toesVis"
            toeRObjs = [rig.toe01_R.rootTransform().fullPathName(), rig.toe02_R.rootTransform().fullPathName(),
                        rig.toe03_R.rootTransform().fullPathName(), rig.toe04_R.rootTransform().fullPathName(),
                        rig.toe05_R.rootTransform().fullPathName()]
            attributes.visibilityConnectObjs(toeRVisAttr, footRNode, toeRObjs,
                                             channelBox=True, nonKeyable=True, defaultValue=True)

        # Custom animator selection sets ----------------------------
        # hair sets should already exist from the sel set biped build script.
        if hairExists:
            hair_sets = ["hairBack2_L_sSet", "hairBack2_R_sSet", "hairBack_C_sSet", "hairFront1_C_sSet",
                         "hairFront2_L_sSet", "hairFront2_R_sSet", "hairFront3_L_sSet", "hairFront3_R_sSet",
                         "hairSide1_L_sSet", "hairSide1_R_sSet", "hairSide2_L_sSet", "hairSide2_R_sSet",
                         "hairTop_C_sSet"]
            validSets = list()
            for sset in hair_sets:
                if cmds.objExists(sset):
                    validSets.append(sset)
                    selectionsets.setMarkingMenuVis(sset, visibility=False)
                    selectionsets.setIcon(sset, "st_squarePink")
                    selectionsets.unParentAll(sset)  # unparent the set, usually from the body set
            hair_sets = validSets
            selectionsets.addSSetZooOptions("hair_sSet", hair_sets,
                                            icon="st_trianglePink",
                                            visibility=True,
                                            parentSet="all_sSet", soloParent=True)

        # Face ---------------------------------------
        if faceExists:
            # Add proxy attrs hips ----------------------------
            attributes.addProxyAttribute(str(hipsNode), str(godNode), faceVisAttr, proxyAttr="", nonKeyable=True)
            # Add proxy attrs head ----------------------------
            attributes.addProxyAttribute(str(headNode), str(godNode), faceVisAttr, proxyAttr="", nonKeyable=True)

            # Eye-aim vis proxy attr on hips, head and god controls -----------------------------
            attributes.addProxyAttribute(headNode, "eye_cntrl_L", "showSeek", proxyAttr="eyeAimVis", nonKeyable=True)
            attributes.addProxyAttribute(godNode, "eye_cntrl_L", "showSeek", proxyAttr="eyeAimVis", nonKeyable=True)
            attributes.addProxyAttribute(hipsNode, "eye_cntrl_L", "showSeek", proxyAttr="eyeAimVis", nonKeyable=True)

        # Add proxy attrs feet ----------------------------
        if toesExist:
            attributes.addProxyAttribute(godNode, footLNode, toeLVisAttr, proxyAttr="toesLVis", nonKeyable=True)
            attributes.addProxyAttribute(godNode, footRNode, toeRVisAttr, proxyAttr="toesRVis", nonKeyable=True)

        # Turn off .prepopulate attribute, solved cycle issues related to disabling non uniform scale ----------------
        for i in zapi.nodesByNames(cmds.ls(type="controller")):
            pre = i.prepopulate
            if not pre.isDestination:
                pre.set(0)

        # Foot break attributes default values to 65.0 -----------------------------------
        cmds.addAttr('{}.footBreak'.format(footLNode), edit=True, defaultValue=65.0)
        cmds.addAttr('{}.footBreak'.format(footRNode), edit=True, defaultValue=65.0)
        cmds.setAttr('{}.footBreak'.format(footLNode), 65.0)
        cmds.setAttr('{}.footBreak'.format(footRNode), 65.0)

        # Disable non-uniform scale ---------------------------
        attributes.disableNonUniformScale(headNode)
        attributes.disableNonUniformScale(godNode)
        attributes.disableNonUniformScale(footLNode)
        attributes.disableNonUniformScale(footRNode)
