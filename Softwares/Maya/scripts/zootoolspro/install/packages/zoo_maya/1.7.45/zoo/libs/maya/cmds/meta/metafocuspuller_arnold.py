from maya import cmds

from zoo.libs.maya import zapi
from zoo.libs.utils import output
from zoo.libs.maya.cmds.meta import metafocuspuller
from zoo.libs.maya.cmds.objutils import attributes

ATTRIBUTE_LIST = metafocuspuller.DELETE_LIST


class ZooFocusPullerArnold(metafocuspuller.ZooFocusPuller):
    """
    """

    def renderer(self):
        return "Arnold"

    def proxyAttribute(self):
        camera_name = self.getCameraStr()
        camera_shape = self.getCameraShapeStr()

        attributes.addProxyAttribute(camera_name, camera_shape, "aiApertureSize", proxyAttr="ArAperture", channelBox=True)
        attributes.addProxyAttribute(camera_name, camera_shape, "aiApertureAspectRatio", proxyAttr="ArAspect",
                                     channelBox=True)
        attributes.addProxyAttribute(camera_name, camera_shape, "aiApertureBlades", proxyAttr="ArBladeCount",
                                     channelBox=True)
        attributes.addProxyAttribute(camera_name, camera_shape, "aiApertureBladeCurvature", proxyAttr="ArBladeAngle",
                                     channelBox=True)
        attributes.addProxyAttribute(camera_name, camera_shape, "aiApertureRotation", proxyAttr="ArBladeRotation",
                                     channelBox=True)

    def buildRig(self, camera_name):
        """Builds the focus puller rig using a camera name.

        Overridden method.

        :param camera_name: The camera name
        :type camera_name: str
        :return:
        :rtype:
        """
        super(ZooFocusPullerArnold, self).buildRig(camera_name)
        # adding proxy attributes to camera
        self.proxyAttribute()
        camera_shape = self.getCameraShapeStr()
        multiDiv_node = self.getMultiDivStr()
        try:
            cmds.connectAttr("{}.outputX".format(multiDiv_node), "{}.aiFocusDistance".format(camera_shape))
        except RuntimeError:
            pass

    # ------------------
    # GETTERS
    # ------------------
    def getFocusDistance(self):
        cameraShape = self.getCameraShapeNode()
        return cameraShape.aiFocusDistance.value()

    def getAperture(self):
        cameraShape = self.getCameraShapeNode()
        return cameraShape.aiApertureSize.value()

    def getAspect(self):
        cameraShape = self.getCameraShapeNode()
        return cameraShape.aiApertureAspectRatio.value()

    def getBladeCount(self):
        cameraShape = self.getCameraShapeNode()
        return cameraShape.aiApertureBlades.value()

    def getBladeAngle(self):
        cameraShape = self.getCameraShapeNode()
        return cameraShape.aiApertureBladeCurvature.value()

    def getRotation(self):
        cameraShape = self.getCameraShapeNode()
        return cameraShape.aiApertureRotation.value()

    def getDOF(self):
        cameraShape = self.getCameraShapeNode()
        return cameraShape.aiEnableDOF.value()

    # ------------------
    # SETTERS
    # ------------------

    def setFocusDistance(self, value):
        cameraShapeStr = self.getCameraShapeStr()
        cmds.setAttr("{}.aiFocusDistance".format(cameraShapeStr), value)

    def setAperture(self, value):
        cameraShapeStr = self.getCameraShapeStr()
        cmds.setAttr("{}.aiApertureSize".format(cameraShapeStr), value)

    def setAspect(self, value):
        cameraShapeStr = self.getCameraShapeStr()
        cmds.setAttr("{}.aiApertureAspectRatio".format(cameraShapeStr), value)

    def setBladeCount(self, value):
        cameraShapeStr = self.getCameraShapeStr()
        cmds.setAttr("{}.aiApertureBlades".format(cameraShapeStr), value)

    def setBladeAngle(self, value):
        cameraShapeStr = self.getCameraShapeStr()
        cmds.setAttr("{}.aiApertureBladeCurvature".format(cameraShapeStr), value)

    def setBladeRotation(self, value):
        cameraShapeStr = self.getCameraShapeStr()
        cmds.setAttr("{}.aiApertureRotation".format(cameraShapeStr), value)

    def depthOfField(self, value=True):
        cameraShapeStr = self.getCameraShapeStr()
        if value:
            cmds.setAttr("{}.aiEnableDOF".format(cameraShapeStr), 1)
            cmds.setAttr("{}.depthOfField".format(cameraShapeStr), 1)
        else:
            cmds.setAttr("{}.aiEnableDOF".format(cameraShapeStr), 0)
            cmds.setAttr("{}.depthOfField".format(cameraShapeStr), 0)

    def deleteAddedAttr(self):
        """Deleting the attributes connecting to the meta node except for the camera"""
        camera_name = self.getCameraStr()
        self.safeDeleteAttr(camera_name, "ArAperture")
        self.safeDeleteAttr(camera_name, "ArAspect")
        self.safeDeleteAttr(camera_name, "ArBladeCount")
        self.safeDeleteAttr(camera_name, "ArBladeAngle")
        self.safeDeleteAttr(camera_name, "ArBladeRotation")

# ------------------
# Updating Values with no meta;
# ------------------

def depthOfField(camera, value):
    cameraShape = zapi.nodeByName(camera).shapes()[0]
    if value:
        cmds.setAttr("{}.aiEnableDOF".format(cameraShape.fullPathName()), 1)
    else:
        cmds.setAttr("{}.aiEnableDOF".format(cameraShape.fullPathName()), 0)

def focusDistance(camera, value):
    cameraShape = zapi.nodeByName(camera).shapes()[0]
    cmds.setAttr("{}.aiFocusDistance".format(cameraShape.fullPathName()), value)

def aperture(camera, value):
    cameraShape = zapi.nodeByName(camera).shapes()[0]
    cmds.setAttr("{}.aiApertureSize".format(cameraShape.fullPathName()), value)

def aspect(camera, value):
    cameraShape = zapi.nodeByName(camera).shapes()[0]
    cmds.setAttr("{}.aiApertureAspectRatio".format(cameraShape.fullPathName()), value)

def bladeCount(camera, value):
    cameraShape = zapi.nodeByName(camera).shapes()[0]
    cmds.setAttr("{}.aiApertureBlades".format(cameraShape.fullPathName()), value)

def bladeAngle(camera, value):
    cameraShape = zapi.nodeByName(camera).shapes()[0]
    cmds.setAttr("{}.aiApertureBladeCurvature".format(cameraShape.fullPathName()), value)

def bladeRotate(camera, value):
    cameraShape = zapi.nodeByName(camera).shapes()[0]
    cmds.setAttr("{}.aiApertureRotation".format(cameraShape.fullPathName()), value)

def getDOF(camera):
    cameraShape = zapi.nodeByName(camera).shapes()[0]
    return cameraShape.aiEnableDOF.value()

def getFocusDistance(camera):
    cameraShape = zapi.nodeByName(camera).shapes()[0]
    return cameraShape.aiFocusDistance.value()

def getAperture(camera):
    cameraShape = zapi.nodeByName(camera).shapes()[0]
    return cameraShape.aiApertureSize.value()

def getAspect(camera):
    cameraShape = zapi.nodeByName(camera).shapes()[0]
    return cameraShape.aiApertureAspectRatio.value()

def getBladeCount(camera):
    cameraShape = zapi.nodeByName(camera).shapes()[0]
    return cameraShape.aiApertureBlades.value()

def getBladeAngle(camera):
    cameraShape = zapi.nodeByName(camera).shapes()[0]
    return cameraShape.aiApertureBladeCurvature.value()

def getRotation(camera):
    cameraShape = zapi.nodeByName(camera).shapes()[0]
    return cameraShape.aiApertureRotation.value()

# --------- #
# FUNCTIONS #
# --------- #


def buildRigSetup(camera_name):
    """Builds the rig setup for Arnold

    :param camera_name: Camera Name
    :type camera_name: Str
    """
    if not metafocuspuller.checkingInputs(camera_name):
        return
    metaNodes = metafocuspuller.getMetasFromName(camera_name)
    if metaNodes:
        output.displayWarning("This camera: {}; already has a Focus Distance rig. ".format(camera_name))
        return

    meta = ZooFocusPullerArnold()
    meta.buildRig(camera_name)
    output.displayInfo("Success: Focus Distance rig created. ")
