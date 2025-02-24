import os

from maya import cmds, mel

from zoo.libs.maya import zapi
from zoo.libs.maya.utils import mayaenv

from zoo.libs.maya.cmds.lighting import lightsmultihdri, lightconstants, renderertransferlights as rtl
from zoo.libs.maya.cmds.shaders import shaderutils
from zoo.libs.maya.cmds.assets import defaultassets
from zoo.libs.maya.cmds.rig import controls, controlconstants
from zoo.libs.maya.cmds.objutils import attributes, shapenodes, namehandling, layers, connections

ARNOLD_ZERO_ATTRS = ["aiDiffuse", "aiSpecular", "aiSss", "aiIndirect", "aiVolume"]
VIEWPORT_ROT = (-13.706, -2.883, -11.653)  # rotation of the viewport light relative to the camera
VIEWPORT_TRANSLATE = (3.0, 1.3, -10.0)  # translation of the viewport light relative to the camera

MAYA_VERSION = float(mayaenv.mayaVersionNiceName())

SKYDOME_PLATZ_PATH = os.path.join(defaultassets.HDR_SKYDOMES_PATH, defaultassets.HDR_PLATZ)
SKYDOME_PLATZ_INT_MULTIPLY = 1.4
SKYDOME_PLATZ_ROT_OFFSET = -42.0

SPECULAR_MULTIPLIER = 1.0  # should remove the specular light
SETUP_SCALE = 0.25
SCALE_MIRROR_BALL = 0.95 * SETUP_SCALE
CTRL_DIRECTIONAL = controlconstants.CTRL_ARROW_THIN
COL_DIRECTIONAL = (1.0, 0.911, 0.319)  # control is light yellow
SCALE_DIRECTIONAL = 1 * SETUP_SCALE
CTRL_HDRI = controlconstants.CTRL_SPHERE
HDRI_ROT_OFFSET = (7.0, -41.0, -4.0,)
COL_HDRI = (0.319, 1.0, 1.0)  # control is light blue
SCALE_HDRI = 1 * SETUP_SCALE
CTRL_VP_LIGHT = controlconstants.CTRL_CUBE_BOUNDING
COL_VP_LIGHT = (1.0, 0.319, 0.319)  # control is light red
SCALE_VP_LIGHT = 1.66 * SETUP_SCALE

# LAYER NAMES ----------------
LAYER_CTRLS = "vpLight_ctrls_lyr"
LAYER_GEO = "vpLight_geo_lyr"
LAYER_LIGHTS = "vpLights_lyr"

# ATTRS ---------------------
ATTR_DIR_INTENSITY = "dirIntensity"
ATTR_HDRI_INTENSITY = "hdrIntensity"
ATTR_DIR_VISIBILITY = "dirVisibility"
ATTR_SPEC_VISIBILITY = "specVisibility"
ATTR_HDRI_VISIBILITY = "hdrVisibility"
ATTR_BALL_VISIBILITY = "ballVisibility"


def disableLightsRenderer(lightShape):
    """Disables a light shape for Arnold, should do for other renderers too. Useful for viewport lights

    :param lightShape: A maya light shape, usually directional viewport light
    :type lightShape: str
    """
    try:
        for attr in ARNOLD_ZERO_ATTRS:
            cmds.setAttr('.'.join([lightShape, attr]), 0)
    except RuntimeError:  # Arnold isn't loaded
        pass


def sSurfaceMultiplier(surfaceStandardMatch):
    """Function that matches the standardSurface shaders, ie all lights are 1.7 more intense, only in 2020 and above.

    :param surfaceStandardMatch: True if the user would like to adjust for standardSurface shaders in the viewport
    :type surfaceStandardMatch: bool
    :return intensityMultiplier: The intensity to multiply whether adjusting for standardSurface renderer shaders.
    :rtype intensityMultiplier: float
    """
    if MAYA_VERSION >= 2020.0 and surfaceStandardMatch:
        return 3.14
    return 1.0


def deleteViewportLayers():
    """Deletes the viewport light layers, UI should check if no meta and delete if so"""
    if cmds.objExists(LAYER_CTRLS):  # being safe as user may have deleted
        cmds.delete(LAYER_CTRLS)
    if cmds.objExists(LAYER_GEO):
        cmds.delete(LAYER_GEO)
    if cmds.objExists(LAYER_LIGHTS):
        cmds.delete(LAYER_LIGHTS)


def directionalCamLight(selectLight=False, intensity=1.0, specIntensity=0.0, shadowColor=(0.4, 0.4, 0.4), lightCount=1,
                        softAngle=5.0, depthMap=1024, parent="", constrain="", surfaceStandardMatch=True):
    """Creates a directional light, intended for parenting to the camLightCamGrp() setup.

    :param selectLight: select the light after building it
    :type selectLight: bool
    :param intensity:  The intensity of the light
    :type intensity: float
    :param shadowColor: Color of the shadow
    :type shadowColor: list(float)
    :param lightCount: The number of lights in the directional setup.
    :type lightCount: int
    :param softAngle: The amount of soft angle (blur)
    :type softAngle: float
    :param depthMap: The size of the depth map shadow in pixels
    :type depthMap: int
    :param parent: Parent the setup to something?  If None then will be ""
    :type parent: str

    :return lightTransformList: The name of the created light transform nodes
    :rtype lightTransformList: list(str)
    :return lightShapeList: The name of the created light shape nodes
    :rtype lightShapeList: list(str)
    :return specularTransform: The name of the specular only directional light
    :rtype specularTransform: str
    :return specularTransform: The name of the specular only directional light
    :rtype specularTransform: str
    :return lightGrp: The name of the created light group node
    :rtype lightGrp: str
    """
    specularZapi = None
    specShapeZapi = None
    # Create and set Attributes ---------------------------
    lightTransformList, lightShapeList, lightGrp, specularTransform, \
    specularShape = directionalSoftShadowLight(lightName="directional_softLight_1",
                                               intensity=intensity,
                                               softAngle=softAngle,
                                               lightCount=lightCount,
                                               dmapResolution=1024,
                                               dmapFilterSize=5,
                                               emitSpecular=True,
                                               specularIntensity=specIntensity,
                                               shadowColor=shadowColor,
                                               depthMap=depthMap,
                                               scale=0.2,
                                               surfaceStandardMatch=surfaceStandardMatch)

    # Add lights to layer -------------------
    layers.addToLayer(LAYER_LIGHTS, [lightTransformList], ref=True)

    # Parent --------------------------
    if parent:
        lightTransformsZapi = list(zapi.nodesByNames(lightTransformList))
        lightShapesZapi = list(zapi.nodesByNames(lightShapeList))
        if specularTransform:
            specularZapi = zapi.nodeByName(specularTransform)
            specShapeZapi = zapi.nodeByName(specularShape)
        lightGrpZapi = zapi.nodeByName(lightGrp)

        constrainGrp = cmds.listRelatives(constrain, parent=True, fullPath=True)[0]
        cmds.parentConstraint(constrain, lightGrp, maintainOffset=False)
        cmds.parent(lightGrp, parent)

        lightTransformList = zapi.fullNames(lightTransformsZapi)
        lightShapeList = zapi.fullNames(lightShapesZapi)
        if specularTransform:
            specularTransform = specularZapi.fullPathName()
            specularShape = specShapeZapi.fullPathName()

        lightGrp = lightGrpZapi.fullPathName()

        attributes.resetTransformAttributes(lightGrp, rotate=True, translate=True, scale=False)
        rotObj = constrainGrp
    else:
        rotObj = lightGrp
    cmds.setAttr("{}.rotate".format(rotObj), VIEWPORT_ROT[0], VIEWPORT_ROT[1], VIEWPORT_ROT[2], type="double3")

    # Select ------------------------
    if selectLight:
        cmds.select(lightGrp, replace=True)
    return lightTransformList, lightShapeList, specularTransform, specularShape, lightGrp


def viewportInternalSkydome(name="skydomeViewport", intensity=1.0, path=SKYDOME_PLATZ_PATH, rotate=0.0,
                            scale=(10.0, 10.0, 10.0), renderer="Arnold", parent="", constrain="",
                            surfaceStandardMatch=True):
    """Builds the viewport skydome and returns all nodes.  Can set Intensity and path.

    :param name: The name of the skydome
    :type name: str
    :param intensity: The brightness of the skydome
    :type intensity: float
    :param path: The location of the skydome image, fullpath
    :type path: str
    :param renderer: Usually "Arnold" as no other renderers work in the viewport
    :type renderer: str

    :return lightTransformName: The light transform name
    :rtype lightTransformName: str
    :return shapeNodeName: The name of the light shape node
    :rtype shapeNodeName: str
    :return textureNode: The name of the texture file node if Arnold otherwise ""
    :rtype textureNode: str
    :return placeTextureNode: The name of the place2dTexture node if Arnold otherwise ""
    :rtype placeTextureNode: str
    """
    intensity *= sSurfaceMultiplier(surfaceStandardMatch)  # Adjust for individualIBLs
    textureNode = ""
    placeTextureNode = ""
    hdriInstance = lightsmultihdri.createDefaultHdriRenderer(renderer,
                                                             hdriName=name,
                                                             lightGroup=False,
                                                             select=True)
    if path == SKYDOME_PLATZ_PATH:  # add rotation offset/intensity offset.  Helps while switching to other HDRIs
        hdriInstance.setIntensityMultiply(SKYDOME_PLATZ_INT_MULTIPLY)
        hdriInstance.setRotateOffset(SKYDOME_PLATZ_ROT_OFFSET)
    hdriInstance.setIntensity(intensity)
    hdriInstance.setImagePath(path)
    hdriInstance.setScale(scale)
    if rotate:
        hdriInstance.setRotate(rotate)

    lightTransformName = hdriInstance.name()
    shapeNodeName = hdriInstance.shapeName()

    # Add lights to layer -------------------
    layers.addToLayer(LAYER_LIGHTS, [lightTransformName], ref=True)

    # Parent --------------------------
    if parent:
        grp = "skydome_grp"
        cmds.group(name=grp, parent=parent)
        lightTransformName = hdriInstance.name()  # long name has changed after parent
        cmds.parentConstraint(constrain, grp, maintainOffset=False)
        attributes.resetTransformAttributes(lightTransformName, rotate=True, translate=True, scale=False)
        lightTransformName = hdriInstance.name()
        shapeNodeName = hdriInstance.shapeName()

    return lightTransformName, shapeNodeName, textureNode, placeTextureNode


def viewportMirrorBall():
    """Creates a geometry poly sphere with a reflective standardSurface shader.

    :return mirrorBallGeo: The name of the sphere transform node
    :rtype mirrorBallGeo: str
    :return shader: The name of the mirror ball shader
    :rtype shader: str
    """
    mirrorBallGeo = cmds.polySphere(name="viewport_mirrorBall_geo",
                                    subdivisionsAxis=36,
                                    subdivisionsHeight=24,
                                    radius=SCALE_MIRROR_BALL)[0]
    mirrorBallShape = cmds.listRelatives(mirrorBallGeo, shapes=True, fullPath=True)[0]
    # Disable render stats ----------------------
    cmds.setAttr("{}.castsShadows".format(mirrorBallShape), False)
    cmds.setAttr("{}.receiveShadows".format(mirrorBallShape), False)
    cmds.setAttr("{}.primaryVisibility".format(mirrorBallShape), False)
    cmds.setAttr("{}.visibleInReflections".format(mirrorBallShape), False)
    cmds.setAttr("{}.visibleInRefractions".format(mirrorBallShape), False)
    cmds.setAttr("{}.doubleSided".format(mirrorBallShape), False)
    # Add to layer and make not selectable --------------------------
    layers.addToLayer(LAYER_GEO, [mirrorBallGeo], ref=True)
    # Create and assign shader --------------------------
    if MAYA_VERSION < 2020.0:  # standard surface only exists in Maya 2020 and above
        shader = cmds.shadingNode('aiStandardSurface', asShader=True, name="mirrorBall_Shad")
    else:
        shader = cmds.shadingNode('standardSurface', asShader=True, name="mirrorBall_Shad")
    cmds.setAttr("{}.baseColor".format(shader), 0.0, 0.0, 0.0, type="double3")
    cmds.setAttr("{}.specularIOR".format(shader), 20.0)
    cmds.setAttr("{}.specularRoughness".format(shader), 0.0)
    shaderutils.assignShader([mirrorBallGeo], shader)
    return mirrorBallGeo, shader


def connectCamToFocalData(cameraShape, focalDataNode):
    """Connects the camera focal length attributes to the focalDataNode

    :param cameraShape: The camera shape node
    :type cameraShape: str
    :param focalDataNode: Name of the focalDataNode, network node that connects to the focal length expressions
    :type focalDataNode: str
    :return:
    :rtype:
    """
    for attr in ["horizontalFilmAperture", "verticalFilmAperture", "focalLength", "lensSqueezeRatio"]:
        cmds.connectAttr("{}.{}".format(cameraShape, attr), "{}.{}".format(focalDataNode, attr))


def focalLengthExpression(camera):
    """Creates the expressions for the focal length scaler, that sizes the rig correctly depending on the focal length.

    :param camera: The camera to apply
    :type camera: str
    :return: focalDataNode, expressions, cameraShape
    :rtype: tuple(str, list(str), str)))
    """
    # Create a empty node with focal info, makes cam switching easier than having to retype the expression
    focalDataNode = cmds.createNode("network", name="viewportLightFocalAdjuster_focalNode")

    cmds.addAttr(focalDataNode, longName="horizontalFilmAperture", attributeType="float", defaultValue=1.41732283465)
    cmds.addAttr(focalDataNode, longName="verticalFilmAperture", attributeType="float", defaultValue=0.94488188976)
    cmds.addAttr(focalDataNode, longName="focalLength", attributeType="float", defaultValue=35.0)
    cmds.addAttr(focalDataNode, longName="lensSqueezeRatio", attributeType="float", defaultValue=1.0)

    # Set up to have viewport lights adjust accordingly to focal length
    cameraShape = cmds.listRelatives(camera, shapes=True)[0]
    expX = cmds.expression(name="viewportLightFocalAdjuster_grp_scaleX_expression",
                           string="viewportLightFocalAdjuster_grp.scaleX = 2 * 10 * "
                                  "(({0}.horizontalFilmAperture * 25.4) / (2 * {0}.focalLength)) "
                                  "* {0}.lensSqueezeRatio".format(focalDataNode),
                           alwaysEvaluate=True, unitConversion=all)
    expY = cmds.expression(name="viewportLightFocalAdjuster_grp_scaleY_expression",
                           string="viewportLightFocalAdjuster_grp.scaleY = 2 * 10 * "
                                  "(({0}.horizontalFilmAperture * 25.4) / (2 * {0}.focalLength)) * 2 / "
                                  "(({0}.horizontalFilmAperture * 25.4 * 2) / "
                                  "({0}.verticalFilmAperture * 25.4))".format(focalDataNode),
                           alwaysEvaluate=True, unitConversion=all)
    expZ = cmds.expression(name="viewportLightFocalAdjuster_grp_scaleZ_expression",
                           string="viewportLightFocalAdjuster_grp.scaleZ = "
                                  "viewportLightFocalAdjuster_grp.scaleX".format(focalDataNode),
                           alwaysEvaluate=True, unitConversion=all)

    connectCamToFocalData(cameraShape, focalDataNode)

    expressions = [expX, expY, expZ]

    return focalDataNode, expressions, cameraShape


def positionFocalScaleGrp(camera, viewportLightFocalAdjuster):
    """Positions the focal adjuster group. Used while switching and creating new cameras.

    This group scales with the focal length of the camera.

    :param camera: The camera to position the focal adjuster to
    :type camera: str
    :param viewportLightFocalAdjuster: The group of the focal adjuster, scales with focal length
    :type viewportLightFocalAdjuster: str
    """
    focalAdjusterShortName = viewportLightFocalAdjuster.split("|")[-1]
    tempLocator = cmds.spaceLocator(name="{}_locator".format(focalAdjusterShortName))
    cmds.matchTransform(tempLocator, camera, position=True, rotation=True, scale=False, pivots=False)
    cmds.parent(tempLocator, camera)
    cmds.setAttr(".translateZ".format(tempLocator), -10)
    cmds.matchTransform(viewportLightFocalAdjuster, tempLocator, position=True, rotation=True, scale=False)
    cmds.delete(tempLocator)


def viewportCamGrpCtrls(camera, mirrorBall=True):
    """Creates a group and controls for the camera constrained viewport light.

    :param camera: The name of the camera to create the setup on.
    :type camera: str
    :param createSphereGeo: Creates a sphere with surfaceStandard if above 2020
    :type createSphereGeo: str

    :return lightGrp: The name of the main group
    :rtype lightGrp: str
    :return parentConstraint: The name of the parentConstraint
    :rtype parentConstraint: str
    :return controlList: directionalCtrlGrp, directionalCtrl, hdriCtrlGrp, hdriCtrl, masterCtrlGrp, masterCtrl
    :rtype controlList: list(str)
    """
    zapiList = list()
    mirrorShader = ""
    mirrorBallGeo = ""
    mirrorZap = None
    lightGrp = cmds.group(name="vp2_light_grp", empty=True)
    viewportLightFocalAdjuster = cmds.group(name="viewportLightFocalAdjuster_grp", empty=True)

    # Add layer, is here because later it doesn't refresh properly with cmds and the add.
    cmds.select(deselect=True)  # can add selected to layer
    if not cmds.objExists(LAYER_CTRLS):
        cmds.createDisplayLayer(name=LAYER_CTRLS)

    # Controls -----------------------
    directionalCtrlGrp, directionalCtrl = createControlGrouped("directionalLight_ctrl",
                                                               scale=SCALE_DIRECTIONAL,
                                                               designName=CTRL_DIRECTIONAL,
                                                               rgbColor=COL_DIRECTIONAL,
                                                               translateOffset=(0.0, 0.0, SCALE_DIRECTIONAL * 2))
    hdriCtrlGrp, hdriCtrl = createControlGrouped("hdri_ctrl",
                                                 scale=SCALE_HDRI,
                                                 designName=CTRL_HDRI,
                                                 rgbColor=COL_HDRI)
    masterCtrlGrp, masterCtrl = createControlGrouped("viewportLight_ctrl",
                                                     scale=SCALE_VP_LIGHT,
                                                     designName=CTRL_VP_LIGHT,
                                                     rgbColor=COL_VP_LIGHT)
    controlList = [directionalCtrlGrp, directionalCtrl, hdriCtrlGrp, hdriCtrl, masterCtrlGrp, masterCtrl]

    # Constrain pivot groups -------------------------
    camMatchGrp = cmds.group(name="constrainToCamera_grp", empty=True)
    pivotGrp = cmds.group(name="controls_pivot_grp", empty=True)
    cmds.setAttr("{}.translate".format(pivotGrp),
                 VIEWPORT_TRANSLATE[0], VIEWPORT_TRANSLATE[1], VIEWPORT_TRANSLATE[2],
                 type="double3")  # Offset
    camMatchGrpZap = zapi.nodeByName(camMatchGrp)
    pivotGrpZap = zapi.nodeByName(pivotGrp)
    cmds.parent(pivotGrp, camMatchGrp)
    cmds.parent(camMatchGrp, lightGrp)
    camMatchGrp = camMatchGrpZap.fullPathName()
    pivotGrp = pivotGrpZap.fullPathName()
    # Rotate HDRI control --------------------------------
    cmds.setAttr("{}.rotate".format(hdriCtrl), HDRI_ROT_OFFSET[0], HDRI_ROT_OFFSET[1], HDRI_ROT_OFFSET[2],
                 type="double3")

    # Lock Attrs --------------------------------
    for ctrl in [hdriCtrl, directionalCtrl]:
        attributes.unlockSRTV(ctrl, translate=True, rotate=False, scale=True, visibility=True, lock=True, keyable=False)

    # Add ctrls to layer --------------------------
    layers.addToLayer(LAYER_CTRLS, [masterCtrl], ref=False, playback=False)  # note layer already created to solve bug.

    # Create Mirror Ball -------------------
    if mirrorBall:
        mirrorBallGeo, mirrorShader = viewportMirrorBall()
        mirrorZap = zapi.nodeByName(mirrorBallGeo)
        cmds.parentConstraint(hdriCtrl, mirrorBallGeo, maintainOffset=False)
        cmds.scaleConstraint(hdriCtrl, mirrorBallGeo, maintainOffset=True)
        cmds.parent(mirrorBallGeo, lightGrp)

    # Parent -----------------------
    for node in controlList:
        zapiList.append(zapi.nodeByName(node))

    cmds.parent(masterCtrlGrp, lightGrp)
    cmds.parent([directionalCtrlGrp, hdriCtrlGrp], zapiList[5].fullPathName())  # master ctrl is zapiList[5]

    for i, node in enumerate(controlList):
        controlList[i] = zapiList[i].fullPathName()
    if mirrorBall:  # fullname name has changed
        mirrorBallGeo = mirrorZap.fullPathName()

    masterCtrlGrp = zapiList[4].fullPathName()  # master group (zapiList[4])
    parentConstraint = cmds.parentConstraint(camera, camMatchGrp, maintainOffset=False)[0]

    cmds.matchTransform(masterCtrlGrp, pivotGrp, position=True, rotation=True, scale=False)
    cmds.parent(viewportLightFocalAdjuster, lightGrp)

    positionFocalScaleGrp(camera, viewportLightFocalAdjuster)

    focalDataNode, expressions, cameraShape = focalLengthExpression(camera)  # builds the expressions

    focalLength = cmds.getAttr("{}.focalLength".format(cameraShape))  # store focal length so can be returned later
    cmds.setAttr("{}.focalLength".format(cameraShape), 35)  # needs to be 35 while building

    # Constraints -------------------------
    setupAdjusterParentCnstnt = cmds.parentConstraint(camera, viewportLightFocalAdjuster, maintainOffset=True)[0]
    setupCameraParentCnstnt = cmds.parentConstraint(viewportLightFocalAdjuster, masterCtrlGrp, maintainOffset=True)[0]
    setupScaleCnstnt = cmds.scaleConstraint(viewportLightFocalAdjuster, masterCtrlGrp, maintainOffset=True)[0]

    # Clean up and toggle focal length back to original before the build
    cmds.setAttr("{}.focalLength".format(cameraShape), focalLength)

    return lightGrp, parentConstraint, controlList, mirrorBallGeo, mirrorShader, camMatchGrp, pivotGrp, \
           setupCameraParentCnstnt, setupScaleCnstnt, setupAdjusterParentCnstnt, \
           expressions, focalDataNode, viewportLightFocalAdjuster


def setSoftAngle(softAngle, lightTransformList, lightCount):
    """Sets the angle soft spread of the directional viewport light

    :param softAngle: The amount of soft angle (blur)
    :type softAngle: float
    :param lightTransformList: All the light transforms
    :type lightTransformList: list(str)
    :param lightCount: Number of directional lights in the setup.
    :type lightCount: int
    """
    softAngle /= 2.0  # divide by two to make raytrace lights
    squares = [1, 4, 9, 16]
    rowsColCount = 1
    for square in squares:
        if lightCount <= square:
            rowsColCount = square ** 0.5  # square root, so 9 will return 3, 16 will return 4
            break
    if rowsColCount == 1:
        angleOffset = 0.0
    else:
        angleOffset = softAngle / (rowsColCount - 1)
    xCount = 1
    yCount = 1
    for light in lightTransformList:
        cmds.setAttr("{}.rotateX".format(light), xCount * angleOffset - softAngle)
        cmds.setAttr("{}.rotateY".format(light), yCount * angleOffset - softAngle)
        yCount += 1
        if yCount == rowsColCount + 1:
            yCount = 1
            xCount += 1


# -------------------
# CONNECT TO CONTROLS
# -------------------


def directionalControlSpread(lightTransformList, lightCount, cntrl, softAngle, attr="softAngle"):
    """Controls the spread of a viewport directional light.  Adds an expression node.

    :param lightTransformList: All the light transforms
    :type lightTransformList: list(str)
    :param lightCount: Number of directional lights in the setup.
    :type lightCount: int
    :param cntrl: The name of the directional control
    :type cntrl: str
    :param softAngle: The amount of soft angle (blur)
    :type softAngle: float
    :param attr: Attribute to create if not already built
    :type attr: str

    :return softAngleExpr: The expression node name that was created
    :rtype softAngleExpr: string
    """
    exprLines = list()

    if not cmds.attributeQuery(attr, node=cntrl, exists=True):
        cmds.addAttr(cntrl, longName=attr, attributeType='float', keyable=1, defaultValue=softAngle)

    squares = [1, 4, 9, 16]
    rowsColCount = 1
    for square in squares:
        if lightCount <= square:
            rowsColCount = square ** 0.5  # square root, so 9 will return 3, 16 will return 4
            break
    rowMult = (rowsColCount - 1)
    xCount = 1
    yCount = 1
    cntrlName = namehandling.getUniqueShortName(cntrl)

    for light in lightTransformList:
        lightName = namehandling.getUniqueShortName(light)
        exprLines.append("{0}.rotateX = {1} * ({3}.{4} / {2}) - ({3}.{4} / 2);".format(lightName,
                                                                                       xCount, rowMult,
                                                                                       cntrlName,
                                                                                       attr))
        exprLines.append("{0}.rotateY = {1} * ({3}.{4}/ {2}) - ({3}.{4} / 2) * 2;".format(lightName,
                                                                                          yCount, rowMult,
                                                                                          cntrlName,
                                                                                          attr))
        yCount += 1
        if yCount == rowsColCount + 1:
            yCount = 1
            xCount += 1
    # Create expression ------------------------
    softAngleExpr = cmds.expression(string="\n".join(exprLines), name="softAngleExpr")
    return softAngleExpr


def directionalDMapControls(directionalShapeList, cntrl, dMapValue=1024, dMapAttr="depthMap"):
    """

    :param directionalShapeList: List of directional light shapes.
    :type directionalShapeList: list(str)
    :param cntrl: The name of the directional control
    :type cntrl: str
    :param dMapValue:
    :type dMapValue:
    :param dMapAttr:
    :type dMapAttr:

    :return:
    :rtype:
    """
    # Depth map shadows ------------------------
    if not cmds.attributeQuery(dMapAttr, node=cntrl, exists=True):
        cmds.addAttr(cntrl, longName=dMapAttr, attributeType='long', keyable=1, defaultValue=dMapValue, maxValue=8192,
                     minValue=16)
    for shape in directionalShapeList:
        cmds.connectAttr('.'.join([cntrl, dMapAttr]), '{}.dmapResolution'.format(shape))


def directionalControlIntensity(directionalTsfrmsStr, directionalShapeList, specularTsfrmStr, specularShape, intensity,
                                specularIntensity, lightCount, cntrl, surfaceStandardMatch=True,
                                intensityAttr=ATTR_DIR_INTENSITY, specAttr="specIntensity"):
    """

    :param directionalTsfrmsStr:
    :type directionalTsfrmsStr:
    :param directionalShapeList:
    :type directionalShapeList:
    :param specularTsfrmStr:
    :type specularTsfrmStr:
    :param specularShape:
    :type specularShape:
    :param intensity:
    :type intensity:
    :param specularIntensity:
    :type specularIntensity:
    :param lightCount:
    :type lightCount:
    :param cntrl:
    :type cntrl:
    :param surfaceStandardMatch:
    :type surfaceStandardMatch:
    :param intensityAttr:
    :type intensityAttr:
    :param specAttr:
    :type specAttr:

    :return:
    :rtype:
    """
    # TODO set intensity callibrated for StndardSurface
    intMultNode = ""
    specMultNode = ""
    attributes.labelAttr("Directional", cntrl, checkExists=True)

    # Directional Intensity -----------------------------------------
    if directionalShapeList:  # Might be being rebuilt
        if not cmds.attributeQuery(intensityAttr, node=cntrl, exists=True):
            cmds.addAttr(cntrl, longName=intensityAttr, attributeType='float', keyable=1, defaultValue=1, minValue=0.0)
        if intensity:
            cmds.setAttr('.'.join([cntrl, ATTR_DIR_INTENSITY]), intensity)
        intMultNode = cmds.createNode('multDoubleLinear', n="vpLightIntMult")
        cmds.connectAttr('.'.join([cntrl, intensityAttr]), '{}.input1'.format(intMultNode))
        cmds.setAttr('{}.input2'.format(intMultNode), 1 / (lightCount / sSurfaceMultiplier(surfaceStandardMatch)))
        for shape in directionalShapeList:
            cmds.connectAttr('{}.output'.format(intMultNode), '{}.intensity'.format(shape))
        # Connect visibility ---------------
        if not cmds.attributeQuery(ATTR_DIR_VISIBILITY, node=cntrl, exists=True):
            cmds.addAttr(cntrl, longName=ATTR_DIR_VISIBILITY, attributeType='bool', keyable=1, defaultValue=True)
        for transform in directionalTsfrmsStr:
            cmds.connectAttr('.'.join([cntrl, ATTR_DIR_VISIBILITY]), '{}.visibility'.format(transform))

    # Specular Intensity -----------------------------------------
    if specularShape:  # Might be being rebuilt
        if not cmds.attributeQuery(specAttr, node=cntrl, exists=True):
            cmds.addAttr(cntrl, longName=specAttr, attributeType='float', keyable=1, defaultValue=specularIntensity,
                         minValue=0.0)
        specMultNode = cmds.createNode('multDoubleLinear', n="vpLightSpecMult")
        cmds.setAttr('{}.input2'.format(specMultNode),
                     1 / (SPECULAR_MULTIPLIER * sSurfaceMultiplier(surfaceStandardMatch)))
        cmds.connectAttr('.'.join([cntrl, specAttr]), '{}.input1'.format(specMultNode))
        cmds.connectAttr('{}.output'.format(specMultNode), '{}.intensity'.format(specularShape))
        # Connect visibility ---------------
        if not cmds.attributeQuery(ATTR_DIR_VISIBILITY, node=cntrl, exists=True):
            cmds.addAttr(cntrl, longName=ATTR_DIR_VISIBILITY, attributeType='bool', keyable=1, defaultValue=True)
        cmds.connectAttr('.'.join([cntrl, ATTR_DIR_VISIBILITY]), '{}.visibility'.format(specularTsfrmStr))

    return intMultNode, specMultNode


def hdriControlIntensity(hdriTsfrmStr, hdriShape, cntrl, intensityAttr=ATTR_HDRI_INTENSITY):
    """

    :param hdriTsfrmStr:
    :type hdriTsfrmStr:
    :param hdriShape:
    :type hdriShape:
    :param cntrl:
    :type cntrl:
    :param intensityAttr:
    :type intensityAttr:
    :return:
    :rtype:
    """
    attributes.labelAttr("Hdri", cntrl, checkExists=True)
    if not cmds.attributeQuery(intensityAttr, node=cntrl, exists=True):
        attributes.addProxyAttribute(cntrl, existingAttr="intensity", existingNode=hdriShape, proxyAttr=intensityAttr)
    if not cmds.attributeQuery(ATTR_HDRI_VISIBILITY, node=cntrl, exists=True):
        cmds.addAttr(cntrl, longName=ATTR_HDRI_VISIBILITY, attributeType='bool', keyable=1, defaultValue=True)
    cmds.connectAttr('.'.join([cntrl, ATTR_HDRI_VISIBILITY]), '{}.visibility'.format(hdriTsfrmStr))


def mirrorBallControlVis(hdriCntrl, mirrorBall):
    """

    :param hdriCntrl:
    :type hdriCntrl:
    :param mirrorBall:
    :type mirrorBall:
    :return:
    :rtype:
    """
    if not cmds.attributeQuery(ATTR_BALL_VISIBILITY, node=hdriCntrl, exists=True):
        cmds.addAttr(hdriCntrl, longName=ATTR_BALL_VISIBILITY, attributeType='bool', keyable=1, defaultValue=True)
    cmds.connectAttr('.'.join([hdriCntrl, ATTR_BALL_VISIBILITY]), '{}.visibility'.format(mirrorBall))


# -------------------
# PROXY CONTROLS
# -------------------


def addDirectionalProxies(proxyCtrl, directionalCtrl):
    """

    :param proxyCtrl:
    :type proxyCtrl:
    :param directionalCtrl:
    :type directionalCtrl:
    :return:
    :rtype:
    """
    if not cmds.attributeQuery(ATTR_DIR_INTENSITY, node=proxyCtrl, exists=True):
        attributes.labelAttr("Directional", proxyCtrl, checkExists=True)
        attributes.addProxyAttribute(proxyCtrl, directionalCtrl, ATTR_DIR_INTENSITY, channelBox=True)
        attributes.addProxyAttribute(proxyCtrl, directionalCtrl, ATTR_DIR_VISIBILITY, channelBox=True)
        attributes.addProxyAttribute(proxyCtrl, directionalCtrl, "specIntensity", channelBox=True)
        if cmds.attributeQuery("softAngle", node=directionalCtrl, exists=True):
            attributes.addProxyAttribute(proxyCtrl, directionalCtrl, "softAngle", channelBox=True)
        attributes.addProxyAttribute(proxyCtrl, directionalCtrl, "depthMap", channelBox=True)


def addHdrProxies(proxyCtrl, hdrCtrl):
    """

    :param proxyCtrl:
    :type proxyCtrl:
    :param hdrCtrl:
    :type hdrCtrl:
    :return:
    :rtype:
    """
    if not cmds.attributeQuery(ATTR_HDRI_INTENSITY, node=proxyCtrl, exists=True):
        attributes.labelAttr("Hdri", proxyCtrl, checkExists=True)
        attributes.addProxyAttribute(proxyCtrl, hdrCtrl, ATTR_HDRI_INTENSITY, channelBox=True)
        attributes.addProxyAttribute(proxyCtrl, hdrCtrl, ATTR_HDRI_VISIBILITY, channelBox=True)
        attributes.addProxyAttribute(proxyCtrl, hdrCtrl, ATTR_BALL_VISIBILITY, channelBox=True)


def addProxyAttrs(masterCtrl, hdriCntrl, directionalCtrl):
    """

    :param masterCtrl:
    :type masterCtrl:
    :param hdriCntrl:
    :type hdriCntrl:
    :param directionalCtrl:
    :type directionalCtrl:

    :return:
    :rtype:
    """
    if hdriCntrl and directionalCtrl:  # add proxies to both controls and master
        # Master
        addDirectionalProxies(masterCtrl, directionalCtrl)
        addHdrProxies(masterCtrl, hdriCntrl)
        # Individual Controls
        addDirectionalProxies(hdriCntrl, directionalCtrl)
        addHdrProxies(directionalCtrl, hdriCntrl)
    elif hdriCntrl:  # Hdri only
        addHdrProxies(masterCtrl, hdriCntrl)
    elif directionalCtrl:  # Directional only
        addDirectionalProxies(masterCtrl, directionalCtrl)


# -------------------
# CREATE DIRECTIONAL SETUP
# -------------------


def directionalSoftShadowLight(lightName="directionalVpLight1", intensity=1.0, softAngle=6.0,
                               lightCount=2, dmapResolution=256, dmapFilterSize=5, emitSpecular=True,
                               shadowColor=(0.0, 0.0, 0.0),
                               depthMap=1024, scale=0.2, specularLight=True, specularIntensity=0.0,
                               surfaceStandardMatch=True):
    """

    :param lightName:
    :type lightName:
    :param intensity:
    :type intensity:
    :param softAngle:
    :type softAngle:
    :param lightCount:
    :type lightCount:
    :param dmapResolution:
    :type dmapResolution:
    :param dmapFilterSize:
    :type dmapFilterSize:
    :param emitSpecular:
    :type emitSpecular:
    :param shadowColor:
    :type shadowColor:
    :param depthMap:
    :type depthMap:
    :param scale:
    :type scale:
    :param specularLight:
    :type specularLight:
    :param specularIntensity:
    :type specularIntensity:
    :param surfaceStandardMatch:
    :type surfaceStandardMatch:

    :return:
    :rtype:
    """
    lightTransformList = list()
    lightShapeList = list()
    lightIntensity = (intensity * sSurfaceMultiplier(surfaceStandardMatch)) / lightCount
    specularTransform = ""
    specularShape = ""
    specularZapi = None
    specShapeZapi = None
    # Create soft angle lights ---------------
    for x in range(lightCount):
        lightShapeList.append(cmds.directionalLight(name=lightName, intensity=lightIntensity))

    for i, shape in enumerate(lightShapeList):
        lightTransformList.append(cmds.listRelatives(shape, parent=True, fullPath=True)[0])
        cmds.setAttr("{}.useDepthMapShadows".format(shape), True)
        cmds.setAttr("{}.dmapResolution".format(shape), dmapResolution)
        cmds.setAttr("{}.dmapFilterSize".format(shape), dmapFilterSize)
        cmds.setAttr("{}.dmapResolution".format(shape), depthMap)
        cmds.setAttr("{}.emitSpecular".format(shape), emitSpecular)
        cmds.setAttr('{}.shadowColor'.format(shape), shadowColor[0], shadowColor[1], shadowColor[2], type="double3")
        cmds.setAttr('{}.scale'.format(lightTransformList[i]), scale, scale, scale, type="double3")

    setSoftAngle(softAngle, lightTransformList, float(lightCount))

    # Create specular Light ----------------
    if specularLight:
        specularIntensity *= (specularIntensity * SPECULAR_MULTIPLIER)
        specularShape = cmds.directionalLight(name="directional_specularLight", intensity=specularIntensity)
        specularTransform = (cmds.listRelatives(specularShape, parent=True, fullPath=True)[0])
        cmds.setAttr("{}.emitDiffuse".format(specularShape), False)  # disable diffuse as not needed
        cmds.setAttr('{}.scale'.format(specularTransform), scale, scale, scale, type="double3")
        specularZapi = zapi.nodeByName(specularTransform)
        specShapeZapi = zapi.nodeByName(specularShape)

    # Group lights ------------------
    lightNamesZapi = list(zapi.nodesByNames(lightTransformList))
    lightShapesZapi = list(zapi.nodesByNames(lightShapeList))
    grp = cmds.group(lightTransformList + [specularTransform], name='sofLight_grp')
    lightTransformList = zapi.fullNames(lightNamesZapi)
    lightShapeList = zapi.fullNames(lightShapesZapi)
    if specularLight:
        specularTransform = specularZapi.fullPathName()
        specularShape = specShapeZapi.fullPathName()

    # Disable lights in renderer/s -------------------------
    for lightShape in lightShapeList + [specularTransform]:
        disableLightsRenderer(lightShape)
    # todo create attributes on main control
    return lightTransformList, lightShapeList, grp, specularTransform, specularShape


# ---------------
# CREATE CONTROLS
# ---------------


def createControlGrouped(ctrlName, scale, designName=controlconstants.CTRL_ARROW_THIN, rgbColor=(1.0, 0.0, 0.0),
                         translateOffset=()):
    """Creates an arrow control for the directionalLight.

    :param ctrlName: The name of the arrow control
    :type ctrlName: str
    :param scale: The size of the control
    :type scale: float
    :param designName: The shape of the main control
    :type designName: str
    :param rgbColor: The color
    :type rgbColor: tuple(float)
    :param translateOffset: Translate the CVs of the control
    :type translateOffset: tuple(float)

    :return grp: The control group
    :rtype grp: str
    :return control: The control transform
    :rtype control: str
    """
    ctrl = controls.createControlCurve(folderpath="",
                                       ctrlName=ctrlName,
                                       curveScale=(scale, scale, scale),
                                       designName=designName,
                                       addSuffix=False,
                                       shapeParent="",
                                       rotateOffset=(0.0, 0.0, 0.0),
                                       trackScale=True,
                                       lineWidth=-1,
                                       rgbColor=rgbColor,
                                       addToUndo=True)[0]
    if translateOffset:
        shapenodes.translateObjListCVs([ctrl], [translateOffset[0], translateOffset[1], translateOffset[2]])
    grp, control, grpUuid, objUuid = controls.groupInPlace(ctrl, grpSwapSuffix=True)
    return grp, control
