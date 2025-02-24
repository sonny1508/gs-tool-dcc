import os

from zoo.libs.hive import api
from zoo.libs.maya import zapi
from zoo.libs.utils import output
from maya import cmds


class MayaReferenceBuildScript(api.BaseBuildScript):
    """References a maya file which contains a hive skeleton, geometry and connects it to the provided
    Rig.
    """
    id = "mayaReference"

    # todo: check existing joints, delete or keep depending on whether is a reference and the same path.
    @staticmethod
    def properties():
        """Defines the maya reference filePath. For more information about properties see
        :func:`zoo.libs.hive.base.buildscript.BaseBuildScript.properties`

        :rtype: list[dict]
        """
        return [{"name": "filePath",
                 "value": "",
                 "type": "filePath",
                 "layout": [0, 0]}
                ]

    def preDeformBuild(self, properties):

        filePath = properties.get("filePath", "")
        if not os.path.exists(filePath):
            output.displayWarning("Requested Maya Skeletal Reference but specified File Path doesn't exist. Skipping")
            return
        namespace = self.rig.name()
        deformLayer = self.rig.deformLayer()
        deformRoot = deformLayer.rootTransform()
        if deformRoot:
            hasReferencedSkel = any(
                i.isReferenced() for i in deformRoot.iterChildren(nodeTypes=(zapi.kNodeTypes.kJoint,)))
            if hasReferencedSkel:
                # check to see if the path is the same otherwise replace it completely by first
                # removing the reference then load the new one, this is avoid reference edits which may
                # become more of a problem after constant loading
                return
            else:
                # purge any existing joints since the reference should have this, Note this doesn't delete
                # the rig deformLayer
                for comp in self._rig.iterComponents():
                    try:
                        comp.deformLayer().delete()
                    except AttributeError:
                        pass

        geo = self._rig.geometryLayer()
        if geo is not None:
            geoTransform = geo.rootTransform()
            if geoTransform:
                geoTransform.delete()
        importedNodes = map(zapi.nodeByName, cmds.file(filePath, reference=True, type='mayaAscii',
                                                       namespace=namespace,
                                                       returnNewNodes=True)
                            )

        joints = []
        rootJoints = []
        rootGeoGrp = None  # contains geometry
        # sort nodes into lists based on types, ie rootJoint, jonts and root transform for geometry
        for n in importedNodes:
            apiType = n.apiType()
            if apiType == zapi.kJoint:
                if n.parent() is None:
                    rootJoints.append(n)
                joints.append(n)
            elif apiType == zapi.kTransform:
                if n.parent() is None:
                    rootGeoGrp = n
        if rootGeoGrp:
            geo.connectTo(api.constants.ROOTTRANSFORM_ATTR, rootGeoGrp)
            rootGeoGrp.setParent(self.rig.rootTransform())
        # now translate the joints into the current rig components metadata.
        # this requires some manipulation of the scenes meta data
        # {(componentType, name, side): {jntId: jnt} }
        translatedJointData = api.skeletonutils.extractSkeletalMetaData(joints)
        # update the components with the incoming joints
        for comp in self.rig.iterComponents():

            compType = comp.componentType
            name = comp.name()
            side = comp.side()
            compData = translatedJointData.get((compType, name, side))
            deformLayer = comp.deformLayer()
            if deformLayer is None:
                hrcName, metaName = api.naming.composeNamesForLayer(comp.namingConfiguration(),
                                                                    name,
                                                                    side,
                                                                    api.constants.DEFORM_LAYER_TYPE)
                deformLayer = comp.meta.createLayer(api.constants.DEFORM_LAYER_TYPE, hrcName, metaName,
                                                    parent=comp.meta.rootTransform())
            for jntId, jnt in compData.items():
                deformLayer.addJoint(jnt, jntId)

        for jnt in rootJoints:
            jnt.setParent(deformRoot)
