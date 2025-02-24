"""
from zoo.libs.maya.cmds.meta import metaviewportlight
metaNode = metaviewportlight.ZooViewportLight()
metaNode.createLightCamera(camera="persp")

"""

from maya import cmds

from zoo.libs.maya import zapi
from zoo.libs.maya.meta import base
from zoo.libs.utils import output

from zoo.libs.maya.cmds.lighting import viewportlights
from zoo.libs.maya.cmds.cameras import cameras
from zoo.libs.maya.cmds.display import viewportmodes
from zoo.libs.maya.utils import mayaenv
from zoo.libs.maya.cmds.objutils import connections

MAYA_VERSION = mayaenv.mayaVersion()

# NODE KEYS -------------------
K_MASTER_GRP = "masterGrp"  # the main group "vp2_light_grp"
K_CAMERA_CNSTRNT = "cameraCnstnt"  # constraint
K_CAMERA_TSFRM = "cameraTsfrm"

K_DIRECTIONAL_CTRL = "directionalCtrl"
K_HDRI_CTRL = "hdriCtrl"
K_MASTER_CTRL = "masterCtrl"
K_DIRECTIONAL_CNSTNT = "directionalCnstnt"  # constraint
K_HDRI_CNSTNT = "hdriCnstnt"
K_CAM_MATCH_GRP = "camMatchGrp"
K_PIVOT_GRP = "pivotGrp"
K_SETUP_PARENT_CNSTNT = "setupParentCnstnt"  # this constraint is modified if not locked to camera.
K_SETUP_SCALE_CNSTNT = "setupScaleCnstnt"  # constraint
K_FOCAL_PARENT_CNSTNT = "focalParentCnstnt"  # constraint
K_CONTROLS_GRP = "controlsGrpStr"

K_CAM_EXPRESSIONS = "cameraExpression"
K_FOCAL_DATA = "focalData"
K_FOCAL_ADJUSTER_GRP = "focalAdjusterGrp"

K_MIRRORBALL_TRFRM = "mirrorBallTsfrm"
K_MIRRORBALL_SHDR = "mirrorBallShdr"
K_MIRRORBALL_CNSTNT = "mirrorBallCnstnt"  # constraint

K_HDRI_TRFRM = "hdriTsfrm"
K_HDRI_SHP = "hdriShp"
K_HDRI_TXTR = "hdriTxtr"
K_HDRI_PLACE_TXTR = "hdriPlaceTxtr"

K_DIRECTIONAL_GRP = "directionalGrp"
K_DIRECTIONAL_TSFRMS = "directionalTsfrms"
K_DIRECTIONAL_SHPS = "directionalShps"
K_DIRECTIONAL_INT_MULT = "directionalIntMult"
K_SPECULAR_TSFRM = "specularTsfrm"
K_SPECULAR_SHAPE = "specularShp"
K_SPECULAR_INT_MULT = "specularIntMult"
K_DIRECTIONAL_SOFTANGLE_EXP = "directionalSoftAngleExp"

META_MESSAGE_ATTRS = [K_MASTER_GRP, K_CAMERA_CNSTRNT, K_CAMERA_TSFRM, K_DIRECTIONAL_CTRL, K_HDRI_CTRL, K_MASTER_CTRL,
                      K_DIRECTIONAL_CNSTNT, K_HDRI_CNSTNT, K_CAM_MATCH_GRP, K_PIVOT_GRP, K_SETUP_PARENT_CNSTNT,
                      K_CONTROLS_GRP, K_MIRRORBALL_TRFRM, K_MIRRORBALL_SHDR,
                      K_MIRRORBALL_CNSTNT, K_HDRI_TRFRM, K_HDRI_SHP, K_HDRI_TXTR, K_HDRI_PLACE_TXTR,
                      K_SPECULAR_TSFRM, K_SPECULAR_SHAPE, K_DIRECTIONAL_GRP, K_DIRECTIONAL_SOFTANGLE_EXP,
                      K_SPECULAR_INT_MULT, K_DIRECTIONAL_INT_MULT, K_SETUP_SCALE_CNSTNT, K_FOCAL_PARENT_CNSTNT,
                      K_FOCAL_DATA, K_FOCAL_ADJUSTER_GRP]

META_MESSAGE_ATTRS_ARRAY = [K_DIRECTIONAL_TSFRMS, K_DIRECTIONAL_SHPS, K_CAM_EXPRESSIONS]

META_DIR_LIGHT_ATTRS = [K_DIRECTIONAL_GRP, K_DIRECTIONAL_INT_MULT, K_SPECULAR_TSFRM,
                        K_SPECULAR_SHAPE, K_SPECULAR_INT_MULT, K_DIRECTIONAL_SOFTANGLE_EXP]

# NODE DICT ------------------------
NODES = {}


class ZooViewportLight(base.MetaBase):
    """Class that controls the meta network node setup for zoo viewport lights

    Controls deleting, rebuilding the setups, querying and setting attributes.

    Attributes:

        lightList: A list of all the lights in the setup
        specularLight: The specular only light in the setup
        lightControl: The control of the viewport light
        masterGroup: The master group of the light, only if constrained to camera
        lightConstraint: The light constraint of the setup, only if constrained to a camera
        camera: The linked camera, only if constrain to a camera

    """
    _default_attrs = list()

    for attr in META_MESSAGE_ATTRS_ARRAY:  # Array attributes message node array
        _default_attrs.append({"name": attr,
                               "value": "",
                               "Type": zapi.attrtypes.kMFnMessageAttribute,
                               "isArray": True})

    for attr in META_MESSAGE_ATTRS:  # Straight message node attributes
        _default_attrs.append({"name": attr,
                               "value": "",
                               "Type": zapi.attrtypes.kMFnMessageAttribute})

    def metaAttributes(self):
        """Creates the dictionary as attributes if they don't already exist"""
        defaults = super(ZooViewportLight, self).metaAttributes()
        defaults.extend(ZooViewportLight._default_attrs)
        return defaults

    def connectNodesToMessageAttr(self, nodes, attr):
        """ Connect nodes

        :param nodes: a list of zapi nodes
        :type nodes: list(:class:`zapi.DGNode`)
        :param attr: Attribute name of the meta node to connect, should be a kMFnMessageAttribute array
        :type attr: str
        """
        for i, node in enumerate(nodes):
            try:
                node.message.connect(self.attribute(attr)[i])
            except AttributeError as e:
                raise AttributeError("{}, {}".format(e, node))

    # ------------------
    # CONNECT METHODS
    # ------------------

    def connectAttrString(self, nodeStr, attrName):
        """

        :param nodeStr: Node or object string name
        :type nodeStr: str
        :param attrName: The name of the attribute to connect, should be a kMFnMessageAttribute type.
        :type attrName: str
        """
        if nodeStr:
            self.connectTo(attrName, zapi.nodeByName(nodeStr))

    def connectAttrStringList(self, nodeStrList, attrName):
        """Connects a string list to a meta node attribute message array node

        :param nodeStrList: List of string maya node/object names
        :type nodeStrList: list(str)
        :param attrName: The name of the attribute to connect, should be a kMFnMessageAttribute array.
        :type attrName: str
        """
        if nodeStrList:
            self.connectNodesToMessageAttr(list(zapi.nodesByNames(nodeStrList)), attrName)

    def clearMessageAttrs(self, attr):
        """Clears the message node attribute list of an array attribute

        :param attr: Attribute name of the meta node to connect, should be a kMFnMessageAttribute array
        :type attr: str
        """
        [o.delete() for o in self.attribute(attr)]

    # ------------------
    # IS VALID
    # ------------------

    def isValid(self):
        """Checks if the light setup is valid and has a main light group and either a HDRI or directional light group

        :return validity: if the light setup is a legitimate working setup
        :rtype validity: bool
        """
        try:
            if not self.getAttrConnectionStr(self.attribute(K_MASTER_GRP)):
                return False
        except RuntimeError:  # can error
            return False
        dirLightList = self.getDirectionalTransformsStr()
        hdriLight = self.getHdrTransform()
        if not dirLightList and not hdriLight:
            return False
        return True

    # ------------------
    # GET NODES
    # ------------------

    def getAttrConnection(self, class_attr):
        """Returns the connected node of the attribute as a zapi dag node

        :return: zapi motionPath node
        :rtype: :class:`zapi.DGNode`
        """
        return class_attr.sourceNode()

    def getAttrConnectionStr(self, class_attr):
        """Returns the connected node of the attribute as a long name

        :return: the connection to the attribute as a string
        :rtype: str
        """
        node = self.getAttrConnection(class_attr)
        if node:
            return node.fullPathName()
        return ""

    def getDirectionalTransformsStr(self):
        try:
            transformsZapi = [directional.value() for directional in self.directionalTsfrms]
            return zapi.fullNames(transformsZapi)
        except:
            return list()

    def getDirectionalShapesStrs(self):
        try:
            shapesZapi = [dShape.value() for dShape in self.directionalShps]
            return zapi.fullNames(shapesZapi)
        except:
            return list()

    def getHdrTransform(self):
        return self.getAttrConnectionStr(self.attribute(K_HDRI_TRFRM))

    def getHdriShape(self):
        return self.getAttrConnectionStr(self.attribute(K_HDRI_SHP))

    def getCameraStr(self):
        return self.getAttrConnectionStr(self.attribute(K_CAMERA_TSFRM))

    def getSpecularTransformStr(self):
        return self.getAttrConnectionStr(self.attribute(K_SPECULAR_TSFRM))

    def getDirectionalCtrlStr(self):
        return self.getAttrConnectionStr(self.attribute(K_DIRECTIONAL_CTRL))

    def getDirectionalGrpStr(self):
        return self.getAttrConnectionStr(self.attribute(K_DIRECTIONAL_GRP))

    def getMasterGrpStr(self):
        return self.getAttrConnectionStr(self.attribute(K_MASTER_GRP))

    def getCameraCnstntStr(self):
        return self.getAttrConnectionStr(self.attribute(K_CAMERA_CNSTRNT))

    def getCamMatchGrpStr(self):
        return self.getAttrConnectionStr(self.attribute(K_CAM_MATCH_GRP))

    def getSetupParentCnstntStr(self):
        return self.getAttrConnectionStr(self.attribute(K_SETUP_PARENT_CNSTNT))

    def getPivotGrpStr(self):
        return self.getAttrConnectionStr(self.attribute(K_PIVOT_GRP))

    def getControlsGrpStr(self):
        return self.getAttrConnectionStr(self.attribute(K_CONTROLS_GRP))

    def getMasterCtrlStr(self):
        return self.getAttrConnectionStr(self.attribute(K_MASTER_CTRL))

    def getDirectionalIntMultStr(self):
        return self.getAttrConnectionStr(self.attribute(K_DIRECTIONAL_INT_MULT))

    def getspecularIntMultStr(self):
        return self.getAttrConnectionStr(self.attribute(K_SPECULAR_INT_MULT))

    # ------------------
    # GETTERS
    # ------------------

    def dirIntensity(self):
        """Sets the intensity of the lights
        """
        ctrl = self.getDirectionalCtrlStr()
        if not ctrl:  # No lights exist
            return
        return cmds.getAttr(".".join([ctrl, "dirIntensity"]))

    def hdrIntensity(self, standardSurface=True):
        """Sets the intensity of the lights
        """
        hdriShape = self.getHdriShape()
        if not hdriShape:  # No light exists
            return
        intensity = cmds.getAttr("{}.intensity".format(hdriShape))
        intensity /= viewportlights.sSurfaceMultiplier(standardSurface)  # adjusts for Maya version and IBL
        return intensity

    def specIntensity(self):
        """Sets the intensity of the lights
        """
        ctrl = self.getDirectionalCtrlStr()
        if not ctrl:  # No lights exist
            return
        return cmds.getAttr(".".join([ctrl, "specIntensity"]))

    def softAngle(self):
        """Sets the light spread of the directional light setup
        """
        ctrl = self.getDirectionalCtrlStr()
        if not ctrl:  # No lights exist
            return
        try:
            return cmds.getAttr(".".join([ctrl, "softAngle"]))
        except ValueError:
            return 0.0

    def shadowColor(self):
        lightShapes = self.getDirectionalShapesStrs()
        if not lightShapes:  # No lights exist
            return
        return cmds.getAttr("{}.shadowColor".format(lightShapes[0]))[0]

    def dMapRes(self):
        ctrl = self.getDirectionalCtrlStr()
        if not ctrl:  # No lights exist
            return
        return cmds.getAttr(".".join([ctrl, "depthMap"]))

    def directionalCount(self):
        if not self.getDirectionalCtrlStr():
            return None
        return len([directional.value() for directional in self.directionalTsfrms])

    def multiplierState(self):
        directionalMult = self.getDirectionalIntMultStr()
        if not directionalMult:
            return
        input2 = cmds.getAttr(".".join([directionalMult, "input2"]))
        lightCount = float(self.directionalCount())
        value = lightCount * input2
        if value > 1.6:  # rounded will be 1.7
            return True
        return False

    # ------------------
    # SETTERS
    # ------------------

    def setDirIntensity(self, intensity):
        """Sets the intensity of the lights

        :param intensity: The intensity of the directional light setup
        :type intensity: float
        """
        ctrl = self.getDirectionalCtrlStr()
        if not ctrl:  # No lights exist
            return
        cmds.setAttr(".".join([ctrl, "dirIntensity"]), intensity)

    def setHdrIntensity(self, intensity, standardSurface=True):
        """Sets the intensity of the lights

        :param intensity: The intensity of the HDR light setup
        :type intensity: float
        """
        hdriShape = self.getHdriShape()
        if not hdriShape:  # No light exists
            return
        intensity *= viewportlights.sSurfaceMultiplier(standardSurface)  # adjusts for Maya version and IBL
        cmds.setAttr("{}.intensity".format(hdriShape), intensity)

    def setSpecIntensity(self, intensity):
        """Sets the intensity of the lights

        :param intensity: The intensity of the directional light setup
        :type intensity: float
        """
        ctrl = self.getDirectionalCtrlStr()
        if not ctrl:  # No lights exist
            return
        cmds.setAttr(".".join([ctrl, "specIntensity"]), intensity)

    def setSoftAngle(self, softAngle):
        """Sets the light spread of the directional light setup

        :param softAngle: the spread in degrees
        :type softAngle: float
        """
        ctrl = self.getDirectionalCtrlStr()
        if not ctrl:  # No lights exist
            return
        cmds.setAttr(".".join([ctrl, "softAngle"]), softAngle)

    def setShadowColor(self, shadowColor):
        lightShapes = self.getDirectionalShapesStrs()
        if not lightShapes:  # No lights exist
            return
        for light in lightShapes:
            cmds.setAttr("{}.shadowColor".format(light), shadowColor[0], shadowColor[1], shadowColor[2],
                         type="double3")

    def setDMapRes(self, dMapRes):
        ctrl = self.getDirectionalCtrlStr()
        if not ctrl:  # No lights exist
            return
        cmds.setAttr(".".join([ctrl, "depthMap"]), dMapRes)

    def orientConstrained(self):
        controlsGrp = self.getControlsGrpStr()
        if controlsGrp:  # if rotateX is connected to something
            if cmds.listConnections("{}.rotateX".format(controlsGrp), destination=False, source=True, plugs=True):
                return True
        return False

    def setDirectionalCountAuto(self, newLightCount):
        """Upgrades a directional setup's light count, must have an existing light number"""
        lightCount = self.directionalCount()
        if not lightCount:
            output.displayWarning("There is no light count number. Cannot update light count")
            return
        self.setDirectionalCount(newLightCount,
                                 lightCount=lightCount,
                                 depthMap=self.dMapRes(),
                                 directionalIntensity=self.dirIntensity(),
                                 surfaceStandardMatch=self.multiplierState(),
                                 softAngle=self.softAngle(),
                                 shadowColor=self.shadowColor())

    def setDirectionalCount(self, newLightCount, lightCount=7, depthMap=1024, directionalIntensity=1.0,
                            specularIntensity=0.0, surfaceStandardMatch=True, softAngle=3.0,
                            shadowColor=(0.0, 0.0, 0.0)):
        directionals = self.getDirectionalTransformsStr()
        masterGrp = self.getMasterGrpStr()
        directionalCtrl = self.getDirectionalCtrlStr()
        if directionals:  # Count the lights
            lightCount = len(directionals)
        if newLightCount == lightCount:
            return  # light count is already correct
        # Delete and rebuild lights ----------------------------------
        self.deleteDirectionalLight()
        self.createDirectionalLight(masterGrp, directionalCtrl, softAngle, newLightCount, shadowColor,
                                    directionalIntensity, specularIntensity, depthMap, surfaceStandardMatch,
                                    connect=True)

    def setMultiplierState(self, intensity, surfaceStandardMatch=True):
        multiplierState = self.multiplierState()
        if multiplierState == surfaceStandardMatch:
            return  # already set to this value
        # Directional -----------------------
        directionalMult = self.getDirectionalIntMultStr()
        if directionalMult:  # Set the directional light
            lightCount = float(self.directionalCount())
            input2 = 1 / (lightCount / viewportlights.sSurfaceMultiplier(surfaceStandardMatch))
            cmds.setAttr(".".join([directionalMult, "input2"]), input2)

        # Specular -----------------------
        specMult = self.getspecularIntMultStr()
        if specMult:
            input2 = 1 / (viewportlights.SPECULAR_MULTIPLIER * viewportlights.sSurfaceMultiplier(surfaceStandardMatch))
            cmds.setAttr(".".join([specMult, "input2"]), input2)

        # HDRI -------------------------
        hdriShape = self.getHdriShape()
        if hdriShape:  # Set to 1.7
            multiply = viewportlights.sSurfaceMultiplier(surfaceStandardMatch)
            if surfaceStandardMatch:
                intensity *= multiply
            else:
                if intensity:
                    intensity /= multiply
                else:
                    intensity = 0.0
            cmds.setAttr(".".join([hdriShape, "intensity"]), intensity)

    # ------------------
    # REBUILD CONSTRAINTS
    # ------------------

    def switchCamera(self, newCamera):
        """Reconstrains the setup to a new camera and reconnects the focal length too

        :param newCamera: The new camera to switch the whole setup to.
        :type newCamera: str
        """
        camera = self.getCameraStr()
        camShape = cmds.listRelatives(camera, shapes=True)[0]
        if camera == newCamera:
            output.displayWarning("Light Setup is already connected to `{}`".format(camera))
            return

        # Get nodes ---------------------
        camConstraint = self.getCameraCnstntStr()
        camMatchGrp = self.getCamMatchGrpStr()
        focalConstraint = self.getAttrConnectionStr(self.attribute(K_FOCAL_PARENT_CNSTNT))
        focalAdjusterGrp = self.getAttrConnectionStr(self.attribute(K_FOCAL_ADJUSTER_GRP))
        focalDataNode = self.getAttrConnectionStr(self.attribute(K_FOCAL_DATA))

        if not focalDataNode:  # If this node is missing the setup is likely an old setup
            self.switchCameraLegacy(newCamera)
            return

        # Delete Constraints ---------------------
        if focalConstraint:  # Delete
            cmds.delete(focalConstraint)
        if camConstraint:  # Delete
            cmds.delete(camConstraint)

        # Break and focal length connections to old camera and focalDataNode ---------------------
        for attr in ["horizontalFilmAperture", "verticalFilmAperture", "focalLength", "lensSqueezeRatio"]:
            try:
                cmds.disconnectAttr(".".join([camShape, attr]), ".".join([focalDataNode, attr]))
            except RuntimeError:
                output.displayWarning("Could not disconnect {} from {}".format(camShape, focalDataNode))
                pass

        # Connect focal length to new camera to focalDataNode ---------------------
        viewportlights.connectCamToFocalData(newCamera, focalDataNode)

        # Rebuild Constraints and reposition the setup to the new camera ---------------------
        parentConstraint = cmds.parentConstraint(newCamera, camMatchGrp, maintainOffset=False)[0]
        viewportlights.positionFocalScaleGrp(newCamera, focalAdjusterGrp)
        focalAdjusterParentCnstnt = cmds.parentConstraint(newCamera, focalAdjusterGrp, maintainOffset=True)[0]

        # Connect new nodes to meta ---------------------
        self.connectAttrString(parentConstraint, K_CAMERA_CNSTRNT)  # Connect constraint to meta
        self.connectAttrString(focalAdjusterParentCnstnt, K_FOCAL_PARENT_CNSTNT)  # Connect constraint to meta
        self.connectAttrString(newCamera, K_CAMERA_TSFRM)  # Connect constraint to meta

    def switchCameraLegacy(self, newCamera):
        """Old code for the previous setup that switches cameras"""
        camera = self.getCameraStr()
        if camera == newCamera:
            output.displayWarning("Light Setup is already connected to `{}`".format(camera))
            return
        camConstraint = self.getCameraCnstntStr()
        camMatchGrp = self.getCamMatchGrpStr()
        if camConstraint:  # Delete
            cmds.delete(camConstraint)
        parentConstraint = cmds.parentConstraint(newCamera, camMatchGrp, maintainOffset=False)[0]
        self.connectAttrString(parentConstraint, K_CAMERA_CNSTRNT)  # Connect constraint to meta
        self.connectAttrString(newCamera, K_CAMERA_TSFRM)  # Connect constraint to meta

    def rotCamFollow(self, follow=True):
        """Links and unlinks the rotation camera follow on the viewport rig setup.

        :param follow: Follow rotation or unfollow/unlink?
        :type follow: bool
        """
        parentCnstnt = self.getSetupParentCnstntStr()
        pivotGrp = self.getPivotGrpStr()
        controlsGrp = self.getControlsGrpStr()
        masterCtrl = self.getMasterCtrlStr()
        matrixTRS = list()
        if not follow:
            if parentCnstnt:
                connections.breakAttr("{}.rotateX".format(controlsGrp))
                connections.breakAttr("{}.rotateY".format(controlsGrp))
                connections.breakAttr("{}.rotateZ".format(controlsGrp))
            else:
                output.displayWarning("The viewport setup is already orient disconnected.")
            return
        # Record xform of master control
        if masterCtrl:  # Record position for seamless space switch
            matrixTRS = cmds.xform(masterCtrl, query=True, matrix=True, worldSpace=True)
        if parentCnstnt:  # Delete
            cmds.delete(parentCnstnt)
        # Recreate constraint now with rotation connections
        parentConstraint = cmds.parentConstraint(pivotGrp, controlsGrp, maintainOffset=False)[0]
        if masterCtrl:
            cmds.xform(masterCtrl, matrix=matrixTRS, worldSpace=True)
        self.connectAttrString(parentConstraint, K_SETUP_PARENT_CNSTNT)  # Connect constraint to meta

    # ------------------
    # SELECT
    # ------------------

    def selectMasterControl(self):
        masterlCtrl = self.getAttrConnectionStr(self.masterCtrl)
        if not masterlCtrl:
            return
        cmds.select(masterlCtrl, replace=True)

    def selectDirectionalControl(self):
        directionalCtrl = self.getAttrConnectionStr(self.directionalCtrl)
        if not directionalCtrl:
            return
        cmds.select(directionalCtrl, replace=True)

    def selectHdriControl(self):
        hdriCtrl = self.getAttrConnectionStr(self.hdriCtrl)
        if not hdriCtrl:
            return
        cmds.select(hdriCtrl, replace=True)

    # ------------------
    # CONNECT BUILT NODES TO META ATTRIBUTES
    # ------------------

    def connectAllNodes(self):
        for attr in META_MESSAGE_ATTRS_ARRAY:
            self.connectAttrStringList(NODES[attr], attr)

        for attr in META_MESSAGE_ATTRS:
            self.connectAttrString(NODES[attr], attr)

    def connectDirectionalLights(self):
        # need to reset the array list lengths here
        for attr in META_MESSAGE_ATTRS_ARRAY:
            self.connectAttrStringList(NODES[attr], attr)
            class_attr = self.attribute(attr)
            for i in list(class_attr):  # removes empty plugs
                if not i.isDestination:
                    i.delete()

        for attr in META_DIR_LIGHT_ATTRS:
            self.connectAttrString(NODES[attr], attr)

    # ------------------
    # BUILD RIG
    # ------------------

    def createDirectionalLight(self, masterGrp, directionalCtrl, softAngle, lightCount, shadowColor,
                               directionalIntensity, specularIntensity, depthMap, surfaceStandardMatch, connect=False):
        NODES[K_DIRECTIONAL_SOFTANGLE_EXP] = ""  # might not be created
        NODES[K_DIRECTIONAL_TSFRMS], NODES[K_DIRECTIONAL_SHPS], NODES[K_SPECULAR_TSFRM], NODES[K_SPECULAR_SHAPE], \
        NODES[K_DIRECTIONAL_GRP] = viewportlights.directionalCamLight(softAngle=softAngle,
                                                                      lightCount=lightCount,
                                                                      shadowColor=shadowColor,
                                                                      parent=masterGrp,
                                                                      constrain=directionalCtrl,
                                                                      selectLight=False,
                                                                      intensity=directionalIntensity,
                                                                      depthMap=depthMap,
                                                                      surfaceStandardMatch=surfaceStandardMatch)
        intMultNode, specMultNode = viewportlights.directionalControlIntensity(NODES[K_DIRECTIONAL_TSFRMS],
                                                                               NODES[K_DIRECTIONAL_SHPS],
                                                                               NODES[K_SPECULAR_TSFRM],
                                                                               NODES[K_SPECULAR_SHAPE],
                                                                               directionalIntensity,
                                                                               specularIntensity,
                                                                               lightCount,
                                                                               directionalCtrl,
                                                                               surfaceStandardMatch)
        NODES[K_SPECULAR_INT_MULT] = specMultNode
        NODES[K_DIRECTIONAL_INT_MULT] = intMultNode
        if lightCount > 1:
            directionalSoftAngleExpStr = viewportlights.directionalControlSpread(NODES[K_DIRECTIONAL_TSFRMS],
                                                                                 lightCount,
                                                                                 directionalCtrl,
                                                                                 softAngle)
            NODES[K_DIRECTIONAL_SOFTANGLE_EXP] = directionalSoftAngleExpStr
        viewportlights.directionalDMapControls(NODES[K_DIRECTIONAL_SHPS], directionalCtrl, depthMap)
        if connect:
            self.connectDirectionalLights()

    def createLightCamera(self, camera, directional=True, hdri=True, selectLight=True,
                          directionalIntensity=1.0, specularIntensity=0.0, shadowColor=(0.4, 0.4, 0.4), lightCount=1,
                          softAngle=5.0, depthMap=1024, hdriIntensity=0.2, hdriRotate=0.0, surfaceStandardMatch=True,
                          message=True):
        """Creates the light and contraints it to a camera as the main viewport light.

        :param camera: Camera name as string
        :type camera: str
        """
        # Create Node dictionary with all the keys and empty values ---------------
        for key in META_MESSAGE_ATTRS:
            NODES[key] = ""
        for key in META_MESSAGE_ATTRS_ARRAY:
            NODES[key] = list()
        # Start --------------------
        NODES[K_CAMERA_TSFRM] = camera
        # Master group parented to camera and controls ----------------------------
        NODES[K_MASTER_GRP], NODES[K_CAMERA_CNSTRNT], cntrlList, NODES[K_MIRRORBALL_TRFRM], NODES[K_MIRRORBALL_SHDR], \
        NODES[K_CAM_MATCH_GRP], NODES[K_PIVOT_GRP], NODES[K_SETUP_PARENT_CNSTNT], \
        NODES[K_SETUP_SCALE_CNSTNT], NODES[K_FOCAL_PARENT_CNSTNT], \
        NODES[K_CAM_EXPRESSIONS], NODES[K_FOCAL_DATA], \
        NODES[K_FOCAL_ADJUSTER_GRP] = viewportlights.viewportCamGrpCtrls(camera, mirrorBall=hdri)
        # Controls ----------------------------------------------------------------
        NODES[K_DIRECTIONAL_CTRL] = cntrlList[1]
        NODES[K_HDRI_CTRL] = cntrlList[3]
        NODES[K_MASTER_CTRL] = cntrlList[5]
        NODES[K_CONTROLS_GRP] = cntrlList[4]

        # Build Lights ----------------------------------------
        if directional:  # saves to NODES global
            self.createDirectionalLight(NODES[K_MASTER_GRP], NODES[K_DIRECTIONAL_CTRL], softAngle, lightCount,
                                        shadowColor, directionalIntensity, specularIntensity, depthMap,
                                        surfaceStandardMatch,
                                        connect=False)
        if hdri:
            NODES[K_HDRI_TRFRM], NODES[K_HDRI_SHP], NODES[K_HDRI_TXTR], \
            NODES[K_HDRI_PLACE_TXTR] = viewportlights.viewportInternalSkydome(intensity=hdriIntensity,
                                                                              rotate=hdriRotate,
                                                                              parent=NODES[K_MASTER_GRP],
                                                                              constrain=NODES[K_HDRI_CTRL],
                                                                              surfaceStandardMatch=surfaceStandardMatch)
            viewportlights.hdriControlIntensity(NODES[K_HDRI_TRFRM], NODES[K_HDRI_SHP], NODES[K_HDRI_CTRL])
            viewportlights.mirrorBallControlVis(NODES[K_HDRI_CTRL], NODES[K_MIRRORBALL_TRFRM])
        # Add Proxy Attributes to Controls ---------------------
        viewportlights.addProxyAttrs(NODES[K_MASTER_CTRL], NODES[K_HDRI_CTRL], NODES[K_DIRECTIONAL_CTRL])

        self.connectAllNodes()

        if selectLight:
            cmds.select(NODES[K_MASTER_CTRL], replace=True)

        if lightCount > 7:  # sets the viewport light mode to 16 as the default of 8 is too low.
            viewportmodes.setMaxLights(16)

        if MAYA_VERSION >= 2020.0 and MAYA_VERSION <= 2022.0:  # if is a version 2020
            # Reload the viewport twice to try and fix for update issues
            viewportmodes.reloadViewport()  # cmds.ogs(reset=True)
            viewportmodes.reloadViewport()

            # Message ----------------------------------------
        if message:
            output.displayInfo("Success: Viewport light setup created and attached to camera `{}`".format(camera))

    # ------------------
    # Delete Light
    # ------------------

    def safeDelete(self, attr):
        """Deletes a zapi node if it is connected to an attribute, passes if None

        :param attr:
        :type attr:
        """
        node = attr.sourceNode()
        if not node:
            return
        node.delete()

    def safeDeleteArray(self, attr):
        try:
            for connection in attr:
                connection.value().delete()
        except:
            pass

    def deleteLight(self, deleteMeta=True, message=True):
        """Deletes the light setup.

        :param deleteMeta: Delete the meta? False if rebuilding
        :type deleteMeta: bool
        """
        deleteList = [K_DIRECTIONAL_CTRL, K_MASTER_GRP, K_HDRI_TXTR, K_HDRI_PLACE_TXTR,
                      K_SPECULAR_INT_MULT, K_DIRECTIONAL_INT_MULT, K_MIRRORBALL_SHDR]
        for attr in deleteList:
            self.safeDelete(self.attribute(attr))
        if deleteMeta:  # deletes the meta node itself
            self.delete()
        # Delete layers with safety
        for lyr in [viewportlights.LAYER_CTRLS, viewportlights.LAYER_GEO, viewportlights.LAYER_LIGHTS]:
            if cmds.objExists(lyr):
                if cmds.nodeType(lyr) == "displayLayer":
                    cmds.delete(lyr)
        if message:
            output.displayInfo("Light Setup Deleted")

    def deleteDirectionalLight(self):
        for attr in META_DIR_LIGHT_ATTRS:
            self.safeDelete(self.attribute(attr))


# ------------------
# Find Meta Nodes
# ------------------

def sceneMetaNodes():
    """Returns all ZooMotionPathRig meta nodes, will delete any metaNodes that are not deemed valid

    :param validMeta: A list of viewport light meta nodes
    :type validMeta: list(:class:`ZooViewportLight`)
    """
    metaNodes = base.findMetaNodesByClassType(ZooViewportLight.__name__)
    validMeta = list()
    if not metaNodes:
        return list()
    for meta in metaNodes:
        if not meta.isValid():
            name = meta.name()
            meta.delete()
            output.displayWarning("An invalid meta node `{}` was deleted".format(name))
        else:
            validMeta.append(meta)
    return validMeta


def metaNodesFromCamera(camera):
    """Returns meta nodes related to a camera

    :param camera: A camera transform name
    :type camera: str
    """
    cameraZapi = zapi.nodeByName(camera)
    metaNodes = base.findRelatedMetaNodesByClassType([cameraZapi], ZooViewportLight.__name__)
    return metaNodes


def cameraVLightMetaNodes():
    """Finds a camera viewport light in the scene and returns the meta node list

    :return metaNodes: A list of meta node python objects
    :rtype metaNodes: :class:`ZooViewportLight`
    """
    camera = cameras.getFocusCamera()
    if camera:
        metaNodes = metaNodesFromCamera(camera)
        if metaNodes:
            return metaNodes
    # No nodes found so search the scene cameras
    sceneCams = cmds.ls(type="camera", long=True)
    for cam in sceneCams:
        metaNodes = metaNodesFromCamera(cam)
        if metaNodes:
            return metaNodes


# ------------------
# Create / Change Cam / Delete Light Setup
# ------------------


def createViewportLight(camera, selectLight=True, directionalIntensity=0.55, specularIntensity=0.0,
                        shadowColor=(0.0, 0.0, 0.0), hdriIntensity=0.14, lightCount=7, softAngle=2.0,
                        surfaceStandardMatch=True, depthMap=1024, setViewportModes=True, message=True):
    """Creates a viewport light setup.

    :param camera: Camera name
    :type camera: str
    :param selectLight: Select the light after building?
    :type selectLight: bool
    :param directionalIntensity: Set the intensity of the directional light
    :type directionalIntensity: float
    :param specularIntensity: Set the intensity of the specular light, usually zero.
    :type specularIntensity: float
    :param shadowColor: Set the shadow color of the directional light, usually black.
    :type shadowColor: list(float)
    :param hdriIntensity: Set the HDRI intensity
    :type hdriIntensity: float
    :param lightCount: the amount of directional lights in the soft shadow setup.
    :type lightCount: int
    :param softAngle: The angle of the soft shadow
    :type softAngle: float
    :param surfaceStandardMatch: Match to standardSurface True or lambert/blinn False
    :type surfaceStandardMatch: bool
    :param depthMap: The size of the depth map in pixels ie 1024
    :type depthMap: int
    :param setViewportModes: turn on all the viewport modes, lights, AO, textures and shadows.
    :type setViewportModes: bool
    :param message: Report messages to the user?
    :type message: bool

    :return metaNode: A viewport light meta node
    :rtype metaNode: :class:`ZooViewportLight`
    """
    metaNode = ZooViewportLight()
    metaNode.createLightCamera(camera,
                               selectLight=selectLight,
                               directionalIntensity=directionalIntensity,
                               specularIntensity=specularIntensity,
                               hdriIntensity=hdriIntensity,
                               shadowColor=shadowColor,
                               lightCount=lightCount,
                               softAngle=softAngle,
                               surfaceStandardMatch=surfaceStandardMatch,
                               depthMap=depthMap,
                               message=message)
    if setViewportModes:
        viewportmodes.setViewportSettingsAll(True)
    return metaNode


def createViewportLightAuto(selectLight=True, directionalIntensity=0.55, specularIntensity=0.0,
                            shadowColor=(0.0, 0.0, 0.0), hdriIntensity=0.14, lightCount=7, softAngle=2.0,
                            surfaceStandardMatch=True, depthMap=1024, setViewportModes=True, message=True):
    """Creates a viewport light setup and auto assigns to the active camera.

    :param selectLight: Select the light after building?
    :type selectLight: bool
    :param directionalIntensity: Set the intensity of the directional light
    :type directionalIntensity: float
    :param specularIntensity: Set the intensity of the specular light, usually zero.
    :type specularIntensity: float
    :param shadowColor: Set the shadow color of the directional light, usually black.
    :type shadowColor: list(float)
    :param hdriIntensity: Set the HDRI intensity
    :type hdriIntensity: float
    :param lightCount: the amount of directional lights in the soft shadow setup.
    :type lightCount: int
    :param softAngle: The angle of the soft shadow
    :type softAngle: float
    :param surfaceStandardMatch: Match to standardSurface True or lambert/blinn False
    :type surfaceStandardMatch: bool
    :param depthMap: The size of the depth map in pixels ie 1024
    :type depthMap: int
    :param setViewportModes: turn on all the viewport modes, lights, AO, textures and shadows.
    :type setViewportModes: bool
    :param message: Report messages to the user?
    :type message: bool

    :return metaNode: A viewport light meta node
    :rtype metaNode: :class:`ZooViewportLight`
    """
    camera = cameras.getFocusCamera()
    if not camera:
        output.displayWarning("No active camera found, select a 3d viewport to make it active")
        return
    createViewportLight(camera=camera, selectLight=selectLight, directionalIntensity=directionalIntensity,
                        specularIntensity=specularIntensity, shadowColor=shadowColor, hdriIntensity=hdriIntensity,
                        lightCount=lightCount, softAngle=softAngle, surfaceStandardMatch=surfaceStandardMatch,
                        depthMap=depthMap, setViewportModes=setViewportModes, message=message)


def deleteViewportLights(turnOffLightViewportMode=True):
    """Deletes all camera viewport lights in the scene

    :param turnOffLightViewportMode: Turns off the viewport light mode after deleting.
    :type turnOffLightViewportMode: bool
    """
    metaNodes = sceneMetaNodes()
    if not metaNodes:
        output.displayWarning("No viewport light setups found")
        return
    for meta in metaNodes:
        meta.deleteLight()
    if turnOffLightViewportMode:
        viewportmodes.setDisplayLightingMode(False)


def switchCamViewportLights(metaNodes, camera):
    """Switch a list of light setups to a new camera.

    :param metaNodes: A list of viewport light meta nodes
    :type metaNodes: list(:class:`ZooViewportLight`)
    :param camera: The camera name string
    :type camera: str
    """
    for meta in metaNodes:
        meta.switchCamera(camera)


def switchCamViewportLightsAuto():
    """Switch all light setups to the active camera
    """
    metaNodes = sceneMetaNodes()
    camera = cameras.getFocusCamera()
    if not metaNodes:
        output.displayWarning("No viewport light rigs found in the scene.")
        return
    if not camera:
        output.displayWarning("No active camera found, select a 3d viewport to make it active")
        return
    for meta in metaNodes:
        meta.switchCamera(camera)
