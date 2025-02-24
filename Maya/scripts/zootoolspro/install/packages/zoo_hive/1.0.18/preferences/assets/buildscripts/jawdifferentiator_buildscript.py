from maya import cmds

from zoo.libs.hive import api
from zoo.libs.maya.cmds.rig import twists
from zoo.libs.maya import zapi
from zoo.libs.maya.utils import mayamath

HEAD_LOCATOR_NODE_NAME = "jawOffset_headLocator"
ATTR_NAMES = ["headTopLipRot", "botTopLipRot", "chinBotLipRot", "chinHeadRot"]
TRANSLATE_ATTR_NAMES = ["headTopLipPos", "botTopLipPos", "chinBotLipPos", "chinHeadPos"]
META_EXTRA_ATTR = "jawDifferentiatorBSExtras"
OFFSET_NODE_NAME = "jawBlendshapeOffsets"

class JawDifferentiatorBuildScript(api.BaseBuildScript):
    """Creates a locator with differences between the rotate and translate of the top lip, bottom lip, chin and head.
    This is useful for creating mouth and jaw blendshapes on the Hive Jaw component.
    """
    # unique identifier for the plugin which will be referenced by the registry.
    id = "jaw_differentiator_bs"  # change id to name that will appear in the hive UI.

    def postPolishBuild(self, properties):
        """Build the setup if it does not exist.
        """
        # if cmds.objExists(HEAD_LOCATOR_NODE_NAME):
        #     return False  # setup has already been created.
        # find the jaw component if it exists otherwise exist early
        jawComponents = list(self.rig.componentsByType("jaw"))
        if not jawComponents:
            return
        jaw = jawComponents[0]
        deform = jaw.deformLayer()
        if not deform:
            return
        joints = {i.id(): i for i in deform.findJoints("topLip", "botLip", "chin")}
        # find the head joint if it exists
        parentJoint = jaw.componentParentJoint(None)

        if parentJoint:
            joints["parentJoint"] = parentJoint
        extraAttr = self.rig.meta.addAttribute(META_EXTRA_ATTR, Type=zapi.attrtypes.kMFnMessageAttribute,
                                               isArray=True)
        self.createHeadLocator(joints, extraAttr)
        self.createBlendshapeLocator(jaw, joints, extraAttr)

    def createBlendshapeLocator(self, jawComponent, joints, extraAttr):
        """Creates the jaw blendshape locator that measures accurate differences in rotation and translation between
        joints."""
        offsetNode = OFFSET_NODE_NAME
        if not cmds.objExists(offsetNode):
            offsetNode = cmds.spaceLocator(name=OFFSET_NODE_NAME)[0]
        outputNode = zapi.nodeByName(offsetNode)
        if not zapi.hasControllerTag(outputNode):
            zapi.createControllerTag(outputNode, OFFSET_NODE_NAME+"Tag")
        chinJoint = joints["chin"].fullPathName()
        topLipJoint = joints["topLip"].fullPathName()
        botLipJoint = joints["botLip"].fullPathName()
        const = cmds.parentConstraint(chinJoint, outputNode.fullPathName(), maintainOffset=False)
        zapi.nodeByName(const[0]).message.connect(extraAttr.nextAvailableDestElementPlug())

        for attr in zapi.localTransformAttrs:
            outputNode.attribute(attr).setKeyable(False)

        for attr in ATTR_NAMES + TRANSLATE_ATTR_NAMES:
            outputNode.addAttribute(attr, Type=zapi.attrtypes.kMFnNumeric3Float,
                                    keyable=True)
        rigLayer = jawComponent.rigLayer()
        controls = {i.id(): i for i in rigLayer.findControls("rotAll", "topLip", "botLip", "chin", "jaw")}
        graphRegistry = self.rig.configuration.graphRegistry()
        dataGraphRep = graphRegistry.graph("jawDifferentiatorBS")
        jawDiffPosGraph = api.serialization.NamedDGGraph.create(dataGraphRep)
        jawDiffPosGraph.connectFromOutput("botTopLipPos", [outputNode.attribute("botTopLipPos")])
        jawDiffPosGraph.connectFromOutput("chinBotLipPos", [outputNode.attribute("chinBotLipPos")])
        jawDiffPosGraph.connectFromOutput("headTopLipPos", [outputNode.attribute("headTopLipPos")])
        jawDiffPosGraph.connectFromOutput("chinHeadPos", [outputNode.attribute("chinHeadPos")])
        jawDiffPosGraph.connectToInput("topLipWorldMatrix", controls["topLip"].worldMatrixPlug())
        jawDiffPosGraph.connectToInput("botLipWorldMatrix", controls["botLip"].worldMatrixPlug())
        jawDiffPosGraph.connectToInput("chinWorldMatrix", controls["chin"].worldMatrixPlug())
        jawDiffPosGraph.connectToInput("rotAllWorldMatrix", controls["rotAll"].worldInverseMatrixPlug())
        jawDiffPosGraph.connectToInput("rotAllSrtWorldMatrix", controls["rotAll"].srt().worldInverseMatrixPlug())
        for n in jawDiffPosGraph.nodes().values():
            n.message.connect(extraAttr.nextAvailableDestElementPlug())

        for index, [inputNodeA, inputNodeB] in enumerate(((topLipJoint, self.headLoc),
                                                          (botLipJoint, topLipJoint),
                                                          (chinJoint, botLipJoint),
                                                          (self.headLoc, chinJoint))):
            rotAttrs = [ATTR_NAMES[index] + axis for axis in mayamath.AXIS_NAMES]
            differentiator = twists.XyzRotDifferentiator(inputNode1=inputNodeA, inputNode2=inputNodeB,
                                                         outputNode=outputNode.fullPathName(),
                                                         attrs=rotAttrs)
            for n in (differentiator.multMatrix,
                      differentiator.decomposeMatrix,
                      differentiator.quatToEulerX,
                      differentiator.quatToEulerY,
                      differentiator.quatToEulerZ):
                zapi.nodeByName(n).message.connect(extraAttr.nextAvailableDestElementPlug())

    def createHeadLocator(self, joints, extraAttr):
        """Creates the head locator that will be orient matched to the jaw joint then parent constrained
        with maintain offset to the head joint."""
        self.headLoc = HEAD_LOCATOR_NODE_NAME
        if not cmds.objExists(HEAD_LOCATOR_NODE_NAME):
            self.headLoc = cmds.spaceLocator(name=HEAD_LOCATOR_NODE_NAME)[0]
        cmds.matchTransform(self.headLoc, joints["topLip"].fullPathName(), rotation=True)
        parentJoint = joints.get("parentJoint")
        if parentJoint:
            cmds.matchTransform(self.headLoc, parentJoint.fullPathName(), position=True)
            const = zapi.nodeByName(cmds.parentConstraint(parentJoint.fullPathName(),
                                                          self.headLoc,
                                                          maintainOffset=True)[0])
            const.message.connect(extraAttr.nextAvailableDestElementPlug())
        cmds.hide(self.headLoc)

    def preDeleteRigLayer(self, properties):
        self._deleteExtras()

    def preDeleteRig(self, properties):
        self._deleteExtras()
        if cmds.objExists(HEAD_LOCATOR_NODE_NAME):
            cmds.delete(HEAD_LOCATOR_NODE_NAME)
        if cmds.objExists(OFFSET_NODE_NAME):
            cmds.delete(OFFSET_NODE_NAME)

    def _deleteExtras(self):
        extraAttr = self.rig.meta.attribute(META_EXTRA_ATTR)
        if extraAttr is None:
            return
        for plug in extraAttr:
            n = plug.sourceNode()
            if n:
                n.delete()
        offsetNode = zapi.nodeByName(OFFSET_NODE_NAME)
        for attrName in ATTR_NAMES + TRANSLATE_ATTR_NAMES:
            offsetNode.attribute(attrName).set(zapi.Vector())
