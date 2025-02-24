from maya import cmds

from zoo.libs.maya import zapi
from zoo.libs.utils import output
from zoo.libs.maya.cmds.meta import metafocuspuller
from zoo.libs.maya.cmds.meta.metafocuspuller import A_REDSHIFT_BOKEH
from zoo.libs.maya.cmds.objutils import attributes

ATTRIBUTE_LIST = metafocuspuller.DELETE_LIST
ATTRIBUTE_LIST.append("redshiftBokeh")


class ZooFocusPullerRedshift(metafocuspuller.ZooFocusPuller):
    """
    """

    def renderer(self):
        return "Redshift"

    def proxyAttribute(self):
        # Add Proxy Attribute to Camera
        camera_name = self.getCameraStr()
        bokeh_node = self.getBokehStr()

        attributes.addProxyAttribute(camera_name, bokeh_node, "dofRadius", proxyAttr="RsRadius", channelBox=True)
        attributes.addProxyAttribute(camera_name, bokeh_node, "dofPower", proxyAttr="RsPower", channelBox=True)
        attributes.addProxyAttribute(camera_name, bokeh_node, "dofAspect", proxyAttr="RsAspect", channelBox=True)
        attributes.addProxyAttribute(camera_name, bokeh_node, "dofBladeCount", proxyAttr="RsBladeCount", channelBox=True)
        attributes.addProxyAttribute(camera_name, bokeh_node, "dofBladeAngle", proxyAttr="RsBladeAngle", channelBox=True)

    def buildRig(self, camera_name):
        """Builds the focus puller rig using a camera name.

        Overridden method.

        :param camera_name: The camera name
        :type camera_name: str
        :return:
        :rtype:
        """
        super(ZooFocusPullerRedshift, self).buildRig(camera_name)
        # create RS node
        bokehNode = cmds.shadingNode("RedshiftBokeh", asUtility=True, name="{}_bokehNode".format(self.getCameraStr()))
        cmds.connectAttr("{}.message".format(bokehNode), "{}.rsLensShader".format(self.getCameraShapeStr()))
        # connect to meta
        self.connectTo(A_REDSHIFT_BOKEH, zapi.nodeByName(bokehNode))
        # adding proxy attributes to camera
        self.proxyAttribute()

    # ------------------
    # GETTERS AND SETTERS
    # ------------------

    def getBokehStr(self):
        return self.getAttrConnectionStr(self.attribute(A_REDSHIFT_BOKEH))

    def getBokehZapi(self):
        return self.getAttrConnection(self.attribute(A_REDSHIFT_BOKEH))

    #def getFocusDistance(self):
    #    bokehZapi = self.getBokehZapi()
    #    return bokehZapi.dofFocusDistance.value()

    def getCOCRadius(self):
        bokehZapi = self.getBokehZapi()
        return bokehZapi.dofRadius.value()

    def getPower(self):
        bokehZapi = self.getBokehZapi()
        return bokehZapi.dofPower.value()

    def getAspect(self):
        bokehZapi = self.getBokehZapi()
        return bokehZapi.dofAspect.value()

    def getBladeCount(self):
        bokehZapi = self.getBokehZapi()
        return bokehZapi.dofBladeCount.value()

    def getBladeAngle(self):
        bokehZapi = self.getBokehZapi()
        return bokehZapi.dofBladeAngle.value()

    def getDOF(self):
        bokehZapi = self.getBokehZapi()
        return bokehZapi.dofOn.value()

    def setFocusDistance(self, value):
        bokenNode = self.getBokehStr()
        cmds.setAttr("{}.dofFocusDistance".format(bokenNode), value)

    def setCOCRadius(self, value):
        bokenNode = self.getBokehStr()
        cmds.setAttr("{}.dofRadius".format(bokenNode), value)

    def setPower(self, value):
        bokenNode = self.getBokehStr()
        cmds.setAttr("{}.dofPower".format(bokenNode), value)

    def setAspect(self, value):
        bokenNode = self.getBokehStr()
        cmds.setAttr("{}.dofAspect".format(bokenNode), value)

    def setBladeCount(self, value):
        bokenNode = self.getBokehStr()
        cmds.setAttr("{}.dofBladeCount".format(bokenNode), value)

    def setBladeAngle(self, value):
        bokenNode = self.getBokehStr()
        cmds.setAttr("{}.dofBladeAngle".format(bokenNode), value)

    def depthOfField(self, value=True):
        bokenNode = self.getBokehStr()
        if value:
            cmds.setAttr("{}.dofOn".format(bokenNode), 1)
        else:
            cmds.setAttr("{}.dofOn".format(bokenNode), 0)

    def deleteAddedAttr(self):
        """Deleting the attributes connecting to the meta node except for the camera"""
        self.safeDeleteAttr(self.getCameraStr(), "RsDistance")
        self.safeDeleteAttr(self.getCameraStr(), "RsRadius")
        self.safeDeleteAttr(self.getCameraStr(), "RsPower")
        self.safeDeleteAttr(self.getCameraStr(), "RsAspect")
        self.safeDeleteAttr(self.getCameraStr(), "RsBladeCount")
        self.safeDeleteAttr(self.getCameraStr(), "RsBladeAngle")

# --------- #
# FUNCTIONS #
# --------- #

def buildRigSetup(camera_name):
    """Builds the rig setup for Redshift

    :param camera_name: Camera Name
    :type camera_name: Str
    """
    if not metafocuspuller.checkingInputs(camera_name):
        return

    metaNodes = metafocuspuller.getMetasFromName(camera_name)
    if metaNodes:
        output.displayWarning("This camera: {}; already has a Focus Distance rig. ".format(camera_name))
        return

    meta = ZooFocusPullerRedshift()
    meta.buildRig(camera_name)
    output.displayInfo("Success: Focus Distance rig created. ")
