from maya import cmds

from zoo.libs.maya import zapi
from zoo.libs.utils import output
from zoo.libs.maya.cmds.meta import metafocuspuller
from zoo.libs.maya.cmds.objutils import attributes

ATTRIBUTE_LIST = metafocuspuller.DELETE_LIST


class ZooFocusPullerRenderman(metafocuspuller.ZooFocusPuller):
    """
    """

    def renderer(self):
        return "Renderman"

    def proxyAttribute(self):
        # Add Proxy Attribute to Camera
        camera_name = self.getCameraStr()
        camera_shape = self.getCameraShapeStr()

        attributes.addProxyAttribute(camera_name, camera_shape, "rman_dofaspect", proxyAttr="RmAspect", channelBox=True)
        attributes.addProxyAttribute(camera_name, camera_shape, "rman_apertureRoundness", proxyAttr="RmRoundness",
                                     channelBox=True)
        attributes.addProxyAttribute(camera_name, camera_shape, "rman_apertureDensity", proxyAttr="RmDensity",
                                     channelBox=True)
        attributes.addProxyAttribute(camera_name, camera_shape, "rman_apertureSides", proxyAttr="RmBladeCount",
                                     channelBox=True)
        attributes.addProxyAttribute(camera_name, camera_shape, "rman_apertureAngle", proxyAttr="RmBladeAngle",
                                     channelBox=True)

    def buildRig(self, camera_name):
        """Builds the focus puller rig using a camera name.

        Overridden method.

        :param camera_name: The camera name
        :type camera_name: str
        :return:
        :rtype:
        """
        super(ZooFocusPullerRenderman, self).buildRig(camera_name)
        # adding proxy attributes to camera
        self.proxyAttribute()

    # ------------------
    # GETTERS AND SETTERS
    # ------------------
    def getAspect(self):
        cameraShape = self.getCameraShapeNode()
        return cameraShape.rman_dofaspect.value()

    def getBladeCount(self):
        cameraShape = self.getCameraShapeNode()
        return cameraShape.rman_apertureSides.value()

    def getBladeAngle(self):
        cameraShape = self.getCameraShapeNode()
        return cameraShape.rman_apertureAngle.value()

    def getRoundness(self):
        cameraShape = self.getCameraShapeNode()
        return cameraShape.rman_apertureRoundness.value()

    def getDensity(self):
        cameraShape = self.getCameraShapeNode()
        return cameraShape.rman_apertureDensity.value()

    def setAspect(self, value):
        cameraShapeStr = self.getCameraShapeStr()
        cmds.setAttr("{}.rman_dofaspect".format(cameraShapeStr), value)

    def setBladeCount(self, value):
        cameraShapeStr = self.getCameraShapeStr()
        cmds.setAttr("{}.rman_apertureSides".format(cameraShapeStr), value)

    def setBladeAngle(self, value):
        cameraShapeStr = self.getCameraShapeStr()
        cmds.setAttr("{}.rman_apertureAngle".format(cameraShapeStr), value)

    def setRoundness(self, value):
        cameraShapeStr = self.getCameraShapeStr()
        cmds.setAttr("{}.rman_apertureRoundness".format(cameraShapeStr), value)

    def setDensity(self, value):
        cameraShapeStr = self.getCameraShapeStr()
        cmds.setAttr("{}.rman_apertureDensity".format(cameraShapeStr), value)

    def deleteAddedAttr(self):
        """Deleting the attributes connecting to the meta node except for the camera"""
        self.safeDeleteAttr(self.getCameraStr(), "RmAspect")
        self.safeDeleteAttr(self.getCameraStr(), "RmRoundness")
        self.safeDeleteAttr(self.getCameraStr(), "RmDensity")
        self.safeDeleteAttr(self.getCameraStr(), "RmBladeCount")
        self.safeDeleteAttr(self.getCameraStr(), "RmBladeAngle")

# ------------------
# Updating Values with no meta;
# ------------------

def aspect(camera, value):
    cameraShape = zapi.nodeByName(camera).shapes()[0]
    cmds.setAttr("{}.rman_dofaspect".format(cameraShape.fullPathName()), value)

def roundness(camera, value):
    cameraShape = zapi.nodeByName(camera).shapes()[0]
    cmds.setAttr("{}.rman_apertureRoundness".format(cameraShape.fullPathName()), value)

def density(camera, value):
    cameraShape = zapi.nodeByName(camera).shapes()[0]
    cmds.setAttr("{}.rman_apertureDensity".format(cameraShape.fullPathName()), value)

def bladeCount(camera, value):
    cameraShape = zapi.nodeByName(camera).shapes()[0]
    cmds.setAttr("{}.rman_apertureSides".format(cameraShape.fullPathName()), value)

def bladeAngle(camera, value):
    cameraShape = zapi.nodeByName(camera).shapes()[0]
    cmds.setAttr("{}.rman_apertureAngle".format(cameraShape.fullPathName()), value)

def getAspect(camera):
    cameraShape = zapi.nodeByName(camera).shapes()[0]
    return cameraShape.rman_dofaspect.value()

def getRoundness(camera):
    cameraShape = zapi.nodeByName(camera).shapes()[0]
    return cameraShape.rman_apertureRoundness.value()

def getDensity(camera):
    cameraShape = zapi.nodeByName(camera).shapes()[0]
    return cameraShape.rman_apertureDensity.value()

def getBladeCount(camera):
    cameraShape = zapi.nodeByName(camera).shapes()[0]
    return cameraShape.rman_apertureSides.value()

def getBladeAngle(camera):
    cameraShape = zapi.nodeByName(camera).shapes()[0]
    return cameraShape.rman_apertureAngle.value()

# --------- #
# FUNCTIONS #
# --------- #

def buildRigSetup(camera_name):
    """Builds the rig setup for Renderman

    :param camera_name: Camera Name
    :type camera_name: Str
    """
    if not metafocuspuller.checkingInputs(camera_name):
        return
    metaNodes = metafocuspuller.getMetasFromName(camera_name)
    if metaNodes:
        output.displayWarning("This camera: {}; already has a Focus Distance rig. ".format(camera_name))
        return

    meta = ZooFocusPullerRenderman()
    meta.buildRig(camera_name)
    output.displayInfo("Success: Focus Distance rig created. ")
