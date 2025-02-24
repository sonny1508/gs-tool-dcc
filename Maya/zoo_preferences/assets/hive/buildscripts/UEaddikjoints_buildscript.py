from zoo.libs.hive import api
from maya import cmds
from zoo.core.util import zlogging
from zoo.libs.maya import zapi

logger = zlogging.getLogger(__name__)


class UEAddIKJoints(api.BaseBuildScript):
    """Build script for adding the UE ikJoints to the UE rig template ie. hand L, hand_gun, hand/foot root etc.

    postDeformBuild creates the joints and updates their worldMatrix to match the deformation skeleton.
    postRigBuild constrains the ikJoints to the deformSkeleton.
    """

    _ikJointExpr = "ik_{area}_{side}"
    # main ikjoints structure, source is where the transform is matched
    _topLevelJnts = (
        (
            "ik_hand_root",
            {"id": "ueIkHandRoot", "source": "root", "parent": "root"},
        ),
        (
            "ik_hand_gun",
            {"id": "ueIkHandGun", "source": "handR", "parent": "ueIkHandRoot"},
        ),
        (
            "ik_foot_root",
            {"id": "ueIkFootRoot", "source": "root", "parent": "root"},
        ),
        (
            "ik_hand_l",
            {"id": "ueIkHandL", "source": "handL", "parent": "ueIkHandGun"},
        ),
        (
            "ik_hand_r",
            {"id": "ueIkHandR", "source": "handR", "parent": "ueIkHandGun"},
        ),
        (
            "ik_foot_l",
            {"id": "ueIkFootL", "source": "footL", "parent": "ueIkFootRoot"},
        ),
        (
            "ik_foot_r",
            {"id": "ueIkFootR", "source": "footR", "parent": "ueIkFootRoot"},
        ),
    )
    id = "ueAddIkJoints"

    def delete(self):
        deformLayer = self.rig.deformLayer()
        # would happen if it's the first build a rig does ever
        if not deformLayer:
            return
        # delete the constraints on the ikJoints allowing the joints to be updated in post
        jnts = self.rig.deformLayer().findJoints(
            "ueIkHandL",
            "ueIkFootL",
            "ueIkHandGun",
            "ueIkFootR",
            "ueIkHandRoot",
            "ueIkFootRoot",
        )
        for jnt in jnts:
            if jnt is not None:
                zapi.deleteConstraints([jnt])
        for jnt in jnts:
            if jnt:
                deformLayer.deleteJoint(jnt.id())
                jnt.delete()

    def preDeleteDeformLayer(self, properties):
        # delete the root joints if they exist
        deformLayer = self.rig.deformLayer()
        for jntId in ("ueIkHandRoot", "ueIkFootRoot"):
            deformLayer.deleteJoint(jntId)

    def postDeformBuild(self, properties):
        """Overridden to create the ikJoints for UE and update their worldMatrix to match the deformSkeleton"""

        godNode = self.rig.componentsByType("godnodecomponent")
        if not godNode:
            # this is debug as it's not really an error, the user may just have removed the component
            logger.debug("Missing GodNode component, unable to create ikJoints for UE")
            return
        rootJnt = list(godNode)[0].deformLayer().joint("godnode")
        # rig deformLayer used for creating and discovery of our joints.
        rigDeform = self.rig.deformLayer()
        jnts = {
            "root": rootJnt,
            "handL": None,
            "handR": None,
            "footL": None,
            "footR": None,
        }
        # update the jnts dict with the end joints for the arms and legs aka hand and foot
        for arm in self.rig.componentsByType("armcomponent"):
            jnts["hand{}".format(arm.side().upper())] = arm.deformLayer().joint("end")
        for leg in list(self.rig.componentsByType("legcomponent")) + list(
            self.rig.componentsByType("quadLeg")
        ):
            jnts["foot{}".format(leg.side().upper())] = leg.deformLayer().joint("end")
        for leg in self.rig.componentsByType("quadLeg"):
            jnts["foot{}".format(leg.side().upper())] = leg.deformLayer().joint("end")
        # create if needed and update worldMatrix to match the source
        for name, info in self._topLevelJnts:
            source = info.get("source")
            jnt = jnts[source]
            if jnt is None:
                logger.warning("Missing source joint for: {}".format(name))
                continue
            transform = zapi.TransformationMatrix(jnt.worldMatrix())
            rotateOrder = jnts[source].rotationOrder()
            existingJnt = rigDeform.joint(info["id"])
            if not existingJnt:
                jnts[info["id"]] = rigDeform.createJoint(
                    name=name,
                    id=info["id"],
                    parent=jnts[info["parent"]],
                    rotateOrder=rotateOrder,
                    translate=transform.translation(zapi.kWorldSpace),
                    rotate=transform.rotation(asQuaternion=True),
                )
            else:
                existingJnt.setRotationOrder(rotateOrder)
                existingJnt.setWorldMatrix(transform.asMatrix())
                jnts[info["id"]] = existingJnt
            # basically zero out the joint, i could do this with zapi but it's a bit more verbose
            try:
                cmds.makeIdentity(
                    jnts[info["id"]].fullPathName(),
                    apply=True,
                    scale=True,
                    rotate=True,
                    translate=True,
                )
            # typical mayaerror which we can ignore
            # error: Freeze Transform or Reset Transform was not applied because node ik_hand_root is a joint and has skin attached.
            except RuntimeError:
                pass

    def preDeleteRigLayer(self, properties):
        """Overridden to delete the constraints on the ikJoints"""
        deformLayer = self.rig.deformLayer()
        # would happen if it's the first build a rig does ever
        if not deformLayer:
            return
        # delete the constraints on the ikJoints allowing the joints to be updated in post
        jnts = self.rig.deformLayer().findJoints(
            "ueIkHandGun", "ueIkHandL", "ueIkFootL", "ueIkFootR"
        )
        for jnt in jnts:
            if jnt is not None:
                zapi.deleteConstraints([jnt])

    def postRigBuild(self, properties):
        """Overridden to constraint the ikJoints to the deformSkeleton"""
        rigDeform = self.rig.deformLayer()
        # constraint the ik joints to the bind skeleton note we only constraint the handGun for the right hand
        # as that needs to follow the wrist as well and the hand_r is a child of the handGun anyways.
        # note: not sure if there a use case to constrain both.
        for arm in self.rig.componentsByType("armcomponent"):
            deformLayer = arm.deformLayer()
            endJnt = deformLayer.joint("end")
            if (
                arm.side().lower() == "r"
            ):  # in the case of the right arm only the handGun jnt gets constrained
                ikJnt = rigDeform.joint("ueIkHandGun")
            else:
                ikJnt = rigDeform.joint("ueIkHand{}".format(arm.side().upper()))
            if ikJnt is None:
                continue
            # by using zapi constraint framework, it creates metadata on the joint to allow for easy discovery
            zapi.buildConstraint(
                ikJnt,
                {"targets": (("", endJnt),)},
                constraintType="parent",
                maintainOffset=False,
            )

        for leg in list(self.rig.componentsByType("legcomponent")) + list(
            self.rig.componentsByType("quadLeg")
        ):
            deformLayer = leg.deformLayer()
            endJnt = deformLayer.joint("end")
            ikJnt = rigDeform.joint("ueIkFoot{}".format(leg.side().upper()))
            if ikJnt is None:
                continue
            zapi.buildConstraint(
                ikJnt,
                {"targets": (("", endJnt),)},
                constraintType="parent",
                maintainOffset=False,
            )
