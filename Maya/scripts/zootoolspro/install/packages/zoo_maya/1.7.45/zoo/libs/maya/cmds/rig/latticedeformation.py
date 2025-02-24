"""Code for building lattice rig setups.

Example use:

.. code-block:: python

    from zoo.libs.maya.cmds.rig import latticedeformation
    from zoo.libs.maya import zapi
    ctrlBase = zapi.nodeByName("base_ctrl")
    ctrlMid = zapi.nodeByName("mid_ctrl")
    ctrlEnd = zapi.nodeByName("end_ctrl")
    latticedeformation.ThreeJointSquashStretchRig(rigName="headSquash",
                                                  ctrlBase=ctrlBase,
                                                  ctrlMid=ctrlMid,
                                                  ctrlEnd=ctrlEnd)

"""
from maya import cmds

from zoo.libs.maya import zapi

from zoo.libs.maya.cmds.objutils import namehandling
from zoo.libs.utils import output
from zoo.libs.hive.base.hivenodes import layers


class ThreeJointSquashStretchRig(object):
    """Main base class that manages node multi setups usually for multi-renderer
    """
    suffix = ""

    def __init__(self, rigName="squashJoinRig", ctrlBase=None, ctrlMid=None, ctrlEnd=None, lattice=None, geoList=(),
                 autoSkin=True):
        """
        """
        super(ThreeJointSquashStretchRig, self).__init__()
        self.rigName = rigName
        self.ctrlBase = ctrlBase
        self.ctrlMid = ctrlMid
        self.ctrlEnd = ctrlEnd
        self.latticeTransform = lattice
        self.ctrlBase = ctrlBase
        self.geoList = geoList
        self.autoSkin = autoSkin

        if self.latticeTransform:
            self.registerLatticeParts()

        if ctrlBase:
            self.ctrlBase = ctrlBase
            self.ctrlMid = ctrlMid
            self.ctrlEnd = ctrlEnd

        if geoList:
            self.geoList = geoList

        if not self.latticeTransform and not self.ctrlBase and self.geoList:
            self.createLattice()
            self.createCtrls(matchToLattice=True)

        elif self.latticeTransform and not self.ctrlBase:
            self.createCtrls(matchToLattice=True)

        elif not self.latticeTransform and not self.ctrlBase and not self.geoList:
            output.displayWarning("This rig requires a lattice or geo list or controls to build.")
            return

        self.buildRig()

    def registerLatticeParts(self):
        """If a lattice exists, register all the nodes from the transform node.

            self.latticeTransform (must exist)
            self.latticeShape
            self.ffd
            self.latticeBaseTransform
            self.latticeBaseShape

        """
        latticeShape = cmds.listRelatives(str(self.latticeTransform), shapes=True)[0]
        self.latticeShape = zapi.nodeByName(latticeShape)
        ffd = cmds.listConnections("{}.latticeOutput".format(str(self.latticeShape)), destination=True)[0]
        self.ffd = zapi.nodeByName(ffd)
        latticeBaseTransform = cmds.listConnections("{}.baseLatticeMatrix".format(str(self.ffd)), source=True)[0]
        self.latticeBaseTransform = zapi.nodeByName(latticeBaseTransform)
        latticeBaseShape = cmds.listRelatives(str(self.latticeBaseTransform), shapes=True)[0]
        self.latticeBaseShape = zapi.nodeByName(latticeBaseShape)

    def createLattice(self, divisions=6):
        """Creates a lattice, needs geo as a zapi list

        Creates:

            self.latticeTransform
            self.latticeShape
            self.ffd
            self.latticeBaseTransform
            self.latticeBaseShape

        :param divisions: The amount of T divisions, min is 2.
        :type divisions: int
        """
        origSel = cmds.ls(selection=True, long=True)
        geoStrs = zapi.fullNames(self.geoList)
        cmds.select(geoStrs, replace=True)
        ffd, latticeTransform, latticeBaseTransform = cmds.lattice(name="{}_lattice".format(self.rigName),
                                                                   divisions=(2, divisions, 2),
                                                                   objectCentered=True)
        self.ffd = zapi.nodeByName(ffd)
        self.latticeTransform = zapi.nodeByName(latticeTransform)
        self.latticeBaseTransform = zapi.nodeByName(latticeBaseTransform)

        latticeShape = cmds.listRelatives(str(self.latticeTransform), shapes=True)[0]
        self.latticeShape = zapi.nodeByName(latticeShape)
        latticeBaseShape = cmds.listRelatives(str(self.latticeBaseTransform), shapes=True)[0]
        self.latticeBaseShape = zapi.nodeByName(latticeBaseShape)
        cmds.select(origSel, replace=True)

    def createCtrls(self, matchToLattice=True):
        """Create three controls and match to the lattice

            self.ctrlBase
            self.ctrlMid
            self.ctrlEnd

        :param matchToLattice: Match the controls to the lattice base transform.
        :type matchToLattice: bool
        """
        rigLyrInst = layers.HiveRigLayer()
        self.ctrlBase = rigLyrInst.createControl(name="{}_base_anim".format(self.rigName),
                                                 id="baseCtrl",
                                                 scale=[0.5, 0.5, 0.5],
                                                 shape="cube_boundingHalf")
        self.ctrlMid = rigLyrInst.createControl(name="{}_mid_anim".format(self.rigName),
                                                id="midCtrl",
                                                scale=[0.5, 0.5, 0.5],
                                                shape="square_target_sharp")
        self.ctrlEnd = rigLyrInst.createControl(name="{}_end_anim".format(self.rigName),
                                                id="endCtrl",
                                                scale=[0.5, 0.5, 0.5],
                                                shape="cube_boundingHalf")
        cmds.setAttr("{}.rotateX".format(str(self.ctrlEnd)), 180.0)
        cmds.makeIdentity([str(self.ctrlBase), str(self.ctrlMid), str(self.ctrlEnd)], apply=True)
        if self.latticeTransform and matchToLattice:
            self.ctrlBase.setParent(self.latticeBaseTransform, maintainOffset=False)
            self.ctrlMid.setParent(self.latticeBaseTransform, maintainOffset=False)
            self.ctrlEnd.setParent(self.latticeBaseTransform, maintainOffset=False)
            self.ctrlEnd.setAttribute("translateY", 0.5)
            self.ctrlBase.setAttribute("translateY", -0.5)
            cmds.parent(str(self.ctrlBase), world=True)
            cmds.parent(str(self.ctrlMid), world=True)
            cmds.parent(str(self.ctrlEnd), world=True)

    def createJoints(self):
        """Create three joints and match to the controls

            self.jntBase
            self.jntMid
            self.jntEnd

        """
        self.jntBase = zapi.createDag("{}_base_jnt".format(self.rigName), "joint")
        self.jntMid = zapi.createDag("{}_mid_jnt".format(self.rigName), "joint")
        self.jntEnd = zapi.createDag("{}_end_jnt".format(self.rigName), "joint")
        cmds.matchTransform([str(self.jntBase), str(self.ctrlBase)], pos=1, rot=1, scl=1, piv=0)
        cmds.matchTransform([str(self.jntMid), str(self.ctrlMid)], pos=1, rot=1, scl=1, piv=0)
        cmds.matchTransform([str(self.jntEnd), str(self.ctrlEnd)], pos=1, rot=1, scl=1, piv=0)

    def createGrps(self):
        """Creates spacer srt groups and organisational groups for the rig setup.

        Space srt:

            self.grpSpaceBase
            self.grpSpaceMid
            self.grpSpaceEnd

        Organisational groups:

            self.grpAll
            self.grpCtrl
            self.grpJnt
            self.grpMisc

        """
        # create 3 space transforms and match to the controls
        self.grpSpaceBase = zapi.createDag("{}_baseSpace_srt".format(self.rigName), "transform")
        self.grpSpaceMid = zapi.createDag("{}_midSpace_srt".format(self.rigName), "transform")
        self.grpSpaceEnd = zapi.createDag("{}_endSpace_srt".format(self.rigName), "transform")
        cmds.matchTransform([str(self.grpSpaceBase), str(self.ctrlBase)], pos=1, rot=1, scl=1, piv=0)
        cmds.matchTransform([str(self.grpSpaceMid), str(self.ctrlMid)], pos=1, rot=1, scl=1, piv=0)
        cmds.matchTransform([str(self.grpSpaceEnd), str(self.ctrlEnd)], pos=1, rot=1, scl=1, piv=0)
        # create organisational grps rig_all_srt, rig_ctrl_grp, rig_jnt_grp, rig_misc_grp
        self.grpAll = zapi.createDag("{}_all_grp".format(self.rigName), "transform")
        self.grpCtrl = zapi.createDag("{}_ctrl_srt".format(self.rigName), "transform")
        self.grpJnt = zapi.createDag("{}_jnt_srt".format(self.rigName), "transform")
        self.grpMisc = zapi.createDag("{}_misc_srt".format(self.rigName), "transform")

    def createSingleChainIk(self):
        """Creates the single chain ik setup with an aim, only one joint is in the setup.

            self.jntAim
            self.ikHandle
            self.ikEffector

        """
        #
        self.jntAim = zapi.createDag("{}_aim_jnt".format(self.rigName), "joint")
        jntSeek = zapi.createDag("{}_seek_jnt".format(self.rigName), "joint")
        jntSeek.setParent(self.jntAim)
        cmds.matchTransform([str(self.jntAim), str(self.jntBase)], pos=1, rot=1, scl=1, piv=0)
        cmds.matchTransform([str(jntSeek), str(self.jntEnd)], pos=1, rot=1, scl=1, piv=0)
        ikName = namehandling.nonUniqueNameNumber("{}_ikHandle".format(self.rigName))  # if not unique can error
        ikHandle, ikEffector = cmds.ikHandle(name=ikName,
                                             startJoint=str(self.jntAim),
                                             endEffector=str(jntSeek),
                                             solver='ikSCsolver')
        self.ikHandle = zapi.nodeByName(ikHandle)
        self.ikEffector = zapi.nodeByName(ikEffector)
        jntSeek.delete()  # not needed after building

    def parentRigParts(self, parentCntrls=True):
        """Parents the rig DAG hierarchy.

        :param parentCntrls: Also parent the controls
        :type parentCntrls: bool
        """
        self.grpSpaceBase.setParent(self.grpMisc)
        self.ikHandle.setParent(self.grpMisc)
        self.jntAim.setParent(self.grpMisc)
        self.grpSpaceBase.setParent(self.grpMisc)
        self.grpSpaceMid.setParent(self.grpSpaceBase)
        self.grpSpaceEnd.setParent(self.grpSpaceMid)

        self.grpCtrl.setParent(self.grpAll)
        self.grpJnt.setParent(self.grpAll)
        self.grpMisc.setParent(self.grpAll)

        cmds.matchTransform([str(self.grpAll), str(self.ctrlBase)], pos=1, rot=1, scl=1, piv=0)  # all goes to bot ctrl
        cmds.matchTransform([str(self.ikHandle), str(self.ctrlEnd)], pos=1, rot=1, scl=1, piv=0)  # ikHndl > top ctrl
        cmds.matchTransform([str(self.jntAim), str(self.ctrlBase)], pos=1, rot=1, scl=1, piv=0)  # ikHndl > top ctrl

        if parentCntrls:
            self.ctrlBase.setParent(self.grpCtrl)
            self.ctrlMid.setParent(self.grpCtrl)
            self.ctrlEnd.setParent(self.grpCtrl)

        self.jntBase.setParent(self.grpJnt)
        self.jntMid.setParent(self.grpJnt)
        self.jntEnd.setParent(self.grpJnt)

        self.jntBase.setParent(self.grpJnt)
        self.jntMid.setParent(self.grpJnt)
        self.jntEnd.setParent(self.grpJnt)

    def createGDNodes(self):
        """Create all the DG nodes that will be used in the rig setup.
        """
        # distanceBetween1 ( distanceBetween )
        self.distanceBetween1 = zapi.createDG("{}_distance".format(self.rigName), "distanceBetween")
        # squashStretch_mdvd (  multiplyDivide )
        self.squashStretch_mdvd = zapi.createDG("{}_squashStretch_multiply".format(self.rigName), "multiplyDivide")
        # headSquash_volume ( blendColors )
        self.headSquash_volume = zapi.createDG("{}_squashStretch_blendCol".format(self.rigName), "blendColors")

        # 3 decomposeMatrix ---------------------
        # headSquash_localInverseScale (decomposeMatrix) A__MOVE_AND_SCALE_INTO_PLACE > headSquash_relativeDistance
        self.headSquash_localInverseScale = zapi.createDG("{}_lclInverseScale_dMatrix".format(self.rigName),
                                                          "decomposeMatrix")
        # decomposeMatrix4 (decomposeMatrix)  multMatrix4 > squash_C0_mid_space2
        self.decomposeMatrix4 = zapi.createDG("{}_spaceBase_dMatrix".format(self.rigName), "decomposeMatrix")
        # headSquash_ik_srt (decomposeMatrix) headSquash_ik_mmtx > headSquash_IK
        self.headSquash_ik_srt = zapi.createDG("{}_ikPos_dMatrix".format(self.rigName), "decomposeMatrix")

        # 6 multMatrix ---------------------
        # headSquash_ik_mmtx ( multMatrix ) squash_C0_end_CTL & A__MOVE_AND_SCALE_INTO_PLACE > headSquash_ik_srt
        self.headSquash_ik_mmtx = zapi.createDG("{}_ikSrt_mMtx".format(self.rigName), "multMatrix")
        # multMatrix4 ( multMatrix ) headSquash_controls & headSquash_aim_JNT > decomposeMatrix4
        self.multMatrix4 = zapi.createDG("{}_baseSpace_mMtx".format(self.rigName), "multMatrix")
        # multMatrix5 ( multMatrix ) headSquash_joints & squash_C0_end_CTL > headSquash_end_JNT
        self.multMatrix5 = zapi.createDG("{}_jointEnd_mMtx".format(self.rigName), "multMatrix")
        # multMatrix6 ( multMatrix ) squash_C0_mid_CTL & headSquash_joints > headSquash_mid_JNT
        self.multMatrix6 = zapi.createDG("{}_jointMid_mMtx".format(self.rigName), "multMatrix")
        # multMatrix7 ( multMatrix ) headSquash_joints & squash_C0_base_CTL > headSquash_base_JNT
        self.multMatrix7 = zapi.createDG("{}_jointBase_mMtx".format(self.rigName), "multMatrix")
        # multMatrix8 ( multMatrix ) headSquash_controls & squash_C0_mid_out > squash_C0_mid_CTL
        self.multMatrix8 = zapi.createDG("{}_midCtrl_mMtx".format(self.rigName), "multMatrix")

        # 6 multDoubleLinear ---------------
        # autoCurveX ( multDoubleLinear ) squash_C0_end_CTL > multDoubleLinear1
        self.autoCurveX = zapi.createDG("{}_autoCrvSpcMidX_mDblLin".format(self.rigName), "multDoubleLinear")
        # autoCurveZ ( multDoubleLinear ) squash_C0_end_CTL > multDoubleLinear2
        self.autoCurveZ = zapi.createDG("{}_autoCrvSpcMidZ_mDblLin".format(self.rigName), "multDoubleLinear")
        # headSquash_halfRelativeDistance ( multDoubleLinear ) headSquash_relativeDistance > squash_C0_mid_space1
        self.headSquash_halfRelativeDistance = zapi.createDG("{}_halfDstnce_mDblLin".format(self.rigName),
                                                             "multDoubleLinear")
        # headSquash_relativeDistance ( multDoubleLinear ) headSquash_localInverseScale & distanceBetween1 > headSquash_halfRelativeDistance
        self.headSquash_relativeDistance = zapi.createDG("{}_dstnce_mDblLin".format(self.rigName), "multDoubleLinear")
        # multDoubleLinear1 ( multDoubleLinear ) autoCurveX > squash_C0_mid_space1
        self.multDoubleLinear1 = zapi.createDG("{}_autoXHalf_mDblLin".format(self.rigName), "multDoubleLinear")
        # multDoubleLinear2 ( multDoubleLinear ) autoCurveZ > squash_C0_mid_space1
        self.multDoubleLinear2 = zapi.createDG("{}_autoZHalf_mDblLin".format(self.rigName), "multDoubleLinear")

    def dagNodes(self):
        """Returns all DAG nodes in the setup for external management.

        :return: A list of DAG nodes as zapi objects
        :rtype: list()
        """
        self.dagNodeList = [self.jntBase, self.jntMid, self.jntEnd, self.grpSpaceBase, self.grpSpaceMid,
                            self.grpSpaceEnd, self.grpAll, self.grpCtrl, self.grpJnt, self.grpMisc, self.jntAim,
                            self.ikHandle, self.ikEffector]
        if self.latticeTransform:
            self.dagNodeList += [self.latticeTransform, self.latticeShape, self.ffd, self.latticeBaseTransform,
                                 self.latticeBaseShape]
        return self.dagNodeList

    def dgNodes(self):
        """Returns all DG nodes in the setup for external management.

        :return: A list of DG nodes as zapi objects
        :rtype: list()
        """
        self.dgNodeList = [self.distanceBetween1, self.squashStretch_mdvd, self.headSquash_volume,
                           self.headSquash_localInverseScale, self.decomposeMatrix4, self.headSquash_ik_srt,
                           self.headSquash_ik_mmtx, self.multMatrix4, self.multMatrix5, self.multMatrix6,
                           self.multMatrix7, self.multMatrix8, self.autoCurveX, self.autoCurveZ,
                           self.headSquash_halfRelativeDistance, self.headSquash_relativeDistance,
                           self.multDoubleLinear1, self.multDoubleLinear2]
        return self.dgNodeList

    def setupDgNodesConnections(self):
        # setup all the matrix connections and node networks
        pass

    def skinLattice(self):
        pass

    def rigNodeDict(self):
        # creates the node dictionary with all nodes
        pass

    def buildRig(self):
        """Creates the rig.
        """
        # Controls should exist at least before building, lattice is optional
        self.createJoints()
        self.createGrps()
        self.createSingleChainIk()
        self.parentRigParts()
        self.createGDNodes()
        self.setupDgNodesConnections()
        if self.latticeTransform and self.autoSkin:
            self.skinLattice()
        self.rigNodeDict()

    def deleteZapiObjs(self, zapiObjs):
        """Generic method that deletes a list of zapi objects.

        :param zapiObjs: A list of zapi nodes.
        :type zapiObjs: list()
        """
        delList = list()
        for zapi in zapiObjs:
            delList.append(str(zapi))
        cmds.delete(delList)

    def delete(self):
        """Deletes the rig.
        """
        self.deleteZapiObjs(self.dgNodes())
        cmds.delete(str(self.grpAll))
