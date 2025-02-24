"""General light code.

.. code-block:: python

    from zoo.libs.maya.cmds.lighting import lightingutils
    lightingutils.convertExpAndIntToIntensity(1.0, 16.0)

Author: Andrew Silke
"""

import math

from zoo.core.util import env, classtypes
from zoovendor import six

if env.isMaya():
    import maya.cmds as cmds
from zoo.libs.utils import output
from zoo.libs.maya.cmds.lighting import lightconstants as lgtcn
from zoo.libs.maya.cmds.renderer import rendererload

SHAPE_ATTR_ENUM_LIST = ["rectangle", "disc", "sphere", "cylinder"]
SHAPE_ATTR_ENUM_LIST_NICE = ["Rectangle", "Disc", "Sphere", "Cylinder"]


def convertIntensityToExposure(intensity):
    """converts intensity in Arnold and Renderman to exposure
     Intensity equals 2 to the power of exposure, so this is the

    :param intensity: the .intensity attr value
    :type intensity: float
    :return exposure: the .exposure attr value if intensity were set to 1
    :rtype exposure: float
    """
    if intensity != 0:
        return math.log(intensity) / math.log(2)
    else:
        output.displayWarning("Intensity must not be zero!!!!!!!")


def convertExposureToIntensity(exposure):
    """converts exposure in Arnold and Renderman to intensity
    Intensity equals 2 to the power of exposure

    :param exposure: the .exposure attribute value
    :type exposure: float
    :return intensity: the .intensity attr value is exposure is set to 0
    :rtype intensity: float
    """
    return 2 ** exposure


def convertExpAndIntToExposure(intensity, exposure):
    """Converts light settings to mixing both intensity and exposure, can do in Renderman and Arnold
    Result will be pure exposure and intensity of 1

    :param intensity: the .intensity attr value
    :type intensity: float
    :param exposure: the .exposure attribute value
    :type exposure: float
    :return intensity: the .intensity attr value is exposure is set to 0
    :rtype intensity: float
    :return exposure: the .exposure attr value if intensity were set to 1
    :rtype exposure: float
    """
    # First work out the pure intensity
    intensityPure = convertExposureToIntensity(exposure)
    intensityPure *= intensity
    # Then work out the exposure from the pure intensity, ie exposure set to 0
    exposure = convertIntensityToExposure(intensityPure)
    intensity = 1
    return intensity, exposure


def convertExpAndIntToIntensity(intensity, exposure):
    """Converts light settings to mixing both intensity and exposure, can do in Renderman and Arnold
    Result will be pure intensity and exposure of 0

    :param intensity: the .intensity attr value
    :type intensity: float
    :param exposure: the .exposure attribute value
    :type exposure: float
    :return intensity: the .intensity attr value is exposure is set to 0
    :rtype intensity: float
    :return exposure: the .exposure attr value if intensity were set to 1
    :rtype exposure: float
    """
    intensityVal = convertExposureToIntensity(exposure)
    intensity *= intensityVal
    exposure = 0
    return intensity, exposure


def calculateCylinderLateralSurfaceArea(radiusX, heightY, radiusZ):
    """ calculates the lateral surface area of a ellipsical cylinder
    h * 2 * pi * squareRoot ((1/2) * ((A * A) + (B * B)))

    :param radiusX: radius on x
    :type radiusX: float
    :param heightY: height
    :type heightY: float
    :param radiusZ: radius on z
    :type radiusZ: float
    :return lateralSurfaceArea: the lateral surface area, not including the circular top bottom caps
    :rtype lateralSurfaceArea: float
    """
    lateralSurfaceArea = heightY * 2 * math.pi * math.sqrt((1 / 2.0) * ((radiusX * radiusX) + (radiusZ * radiusZ)))
    return lateralSurfaceArea


def calculateEllipsoidArea(radiusX, radiusY, radiusZ):
    """calculates the surface area of a sphere with xyz scale

    :param radiusX: radius (half scale) of x
    :type radiusX: float
    :param radiusY: radius (half scale) of y
    :type radiusY: float
    :param radiusZ: radius (half scale) of z
    :type radiusZ: float
    :return: surface area of the scaled sphere in cms squared
    :rtype: float
    """
    import math
    xy = math.pow(radiusX * radiusY, 1.6075)
    xz = math.pow(radiusX * radiusZ, 1.6075)
    yz = math.pow(radiusY * radiusZ, 1.6075)
    return (4.0 * math.pi) * pow((xy + xz + yz) / 3.0, 1.0 / 1.6075)


def calculateAreaShape(scaleX, scaleY, scaleZ, shape=SHAPE_ATTR_ENUM_LIST_NICE[0]):
    """Calculate the area of a rect, sphere, cylinder (uncapped) or sphere

    :param scaleX: scale on x
    :type scaleX: float
    :param scaleY: scale on y
    :type scaleY: float
    :param scaleZ: scale on z
    :type scaleZ: float
    :param shape: the string shape of the 3d object, see SHAPE_ATTR_ENUM_LIST_NICE for values ("Rectangle", "Disc" etc)
    :type shape: str
    :return area: the surface area in cm squared
    :rtype area: float
    """
    if shape == SHAPE_ATTR_ENUM_LIST_NICE[0]:  # rectangle
        area = scaleY * scaleX
    elif shape == SHAPE_ATTR_ENUM_LIST_NICE[1]:  # circle/disk
        area = round(math.pi * (scaleX / 2) * (scaleY / 2), 3)
    elif shape == SHAPE_ATTR_ENUM_LIST_NICE[2]:  # ellipsoid/sphere
        area = round(calculateEllipsoidArea(scaleX / 2, scaleY / 2, scaleZ / 2))
    elif shape == SHAPE_ATTR_ENUM_LIST_NICE[3]:  # cylinder lateral surface area not including caps
        area = calculateCylinderLateralSurfaceArea(scaleX / 2, scaleY, scaleZ / 2)
    else:
        return
    return area


def convertToNonNormalized(intensity, scaleX, scaleY, scaleZ, shape=SHAPE_ATTR_ENUM_LIST_NICE[0]):
    """converts a normalized intensity to non normalized by calculating the size of the area light and multiplying it
    by intensity

    :param intensity: light intensity normalized
    :type intensity: float
    :param scaleX: size of the light scaled on x
    :type scaleX: float
    :param scaleY: size of the light scaled on x
    :type scaleY: float
    :param shape: the string shape of the 3d object, see SHAPE_ATTR_ENUM_LIST_NICE for values ("Rectangle", "Disc" etc)
    :type shape: str
    :return intensity: the intensity value no longer normalized
    :rtype intensity: float
    """
    area = calculateAreaShape(scaleX, scaleY, scaleZ, shape=shape)
    return area * intensity


def convertToNormalized(intensity, scaleX, scaleY, scaleZ, shape=SHAPE_ATTR_ENUM_LIST_NICE[0]):
    """converts a non normalized intensity to normalized by calculating the size of the area light and dividing
    intensity by that number

    :param intensity: light intensity normalized
    :type intensity: float
    :param scaleX: size of the light scaled on x
    :type scaleX: float
    :param scaleY: size of the light scaled on x
    :type scaleY: float
    :param scaleZ: scale on z
    :type scaleZ: float
    :param shape: the string shape of the 3d object, see SHAPE_ATTR_ENUM_LIST_NICE for values ("Rectangle", "Disc" etc)
    :type shape: str
    :return intensity: the intensity value now normalized
    :rtype intensity: float
    """
    area = calculateAreaShape(scaleX, scaleY, scaleZ, shape=shape)
    return intensity / area


def convertToNormalizedIntensity(intensity, exposure, scaleX, scaleY, scaleZ, shape=SHAPE_ATTR_ENUM_LIST_NICE[0]):
    """Converts lights with no normalization to normalize.  This function works for area lights of four shape types
    Returns pure intensity

    :param intensity: The intensity value of the light (Arnold, Renderman, Redshift units)
    :type intensity: float
    :param exposure: The exposure value of the light (Arnold Renderman) zero if Redshift
    :type exposure: float
    :param scaleX: The scale x of the rectangle light
    :type scaleX: float
    :param scaleY: The scale y of the rectangle light
    :type scaleY: float
    :param scaleZ: scale on z
    :type scaleZ: float
    :param shape: the string shape of the 3d object, see SHAPE_ATTR_ENUM_LIST_NICE for values ("Rectangle", "Disc" etc)
    :type shape: str
    :return intensity: the returned intensity value, now normalized
    :rtype intensity: float
    :return exposure: the returned exposure value, will be zero
    :rtype exposure: float
    """
    # get pure intensity
    intensity, exposure = convertExpAndIntToIntensity(intensity, exposure)
    # get non normalized pure intensity
    intensity = convertToNonNormalized(intensity, scaleX, scaleY, scaleZ, shape=shape)
    return intensity, exposure


def convertToNormalizedExposure(intensity, exposure, scaleX, scaleY, scaleZ, shape=SHAPE_ATTR_ENUM_LIST_NICE[0]):
    """Converts lights with no normalization to normalize.  This function works for area lights of four light shapes
    Returns pure exposure, intensity will be 1

    :param intensity: The intensity value of the light (Arnold, Renderman, Redshift units)
    :type intensity: float
    :param exposure: The exposure value of the light (Arnold Renderman) zero if Redshift
    :type exposure: float
    :param scaleX: The scale x of the rectangle light
    :type scaleX: float
    :param scaleY: The scale y of the rectangle light
    :type scaleY: float
    :param scaleZ: scale on z
    :type scaleZ: float
    :param shape: the string shape of the 3d object, see SHAPE_ATTR_ENUM_LIST_NICE for values ("Rectangle", "Disc" etc)
    :type shape: str
    :return intensity: the returned intensity value will be 1
    :rtype intensity: float
    :return exposure: the returned exposure value now normalized
    :rtype exposure: float
    """
    # get pure intensity
    intensity, exposure = convertExpAndIntToIntensity(intensity, exposure)
    # get non normalized pure intensity
    intensity = convertToNonNormalized(intensity, scaleX, scaleY, scaleZ, shape=shape)
    # get pure exposure
    intensity, exposure = convertExpAndIntToExposure(intensity, exposure)
    return intensity, exposure


def convertToNonNormalizedIntensity(intensity, exposure, scaleX, scaleY, scaleZ, shape=SHAPE_ATTR_ENUM_LIST_NICE[0]):
    """Converts lights with normalized to no normalization.  This function works for rectangular area lights
    Returns pure intensity, exposure will be 0

    :param intensity: The intensity value of the light (Arnold, Renderman, Redshift units)
    :type intensity: float
    :param exposure: The exposure value of the light (Arnold Renderman) zero if Redshift
    :type exposure: float
    :param scaleX: The scale x of the rectangle light
    :type scaleX: float
    :param scaleY: The scale y of the rectangle light
    :type scaleY: float
    :param scaleZ: scale on z
    :type scaleZ: float
    :param shape: the string shape of the 3d object, see SHAPE_ATTR_ENUM_LIST_NICE for values ("Rectangle", "Disc" etc)
    :type shape: str
    :return intensity: the returned intensity value now not normalized
    :rtype intensity: float
    :return exposure: the returned exposure value will be zero
    :rtype exposure: float
    """
    # get pure intensity
    intensity, exposure = convertExpAndIntToIntensity(intensity, exposure)
    # get non normalized pure intensity
    intensity = convertToNormalized(intensity, scaleX, scaleY, scaleZ, shape=shape)
    return intensity, exposure


def convertToNonNormalizedExposure(intensity, exposure, scaleX, scaleY, scaleZ, shape=SHAPE_ATTR_ENUM_LIST_NICE[0]):
    """Converts normalized lights to no normalization.  This function works for rectangular area lights
    Returns pure exposure, intensity will be 1

    :param intensity: The intensity value of the light (Arnold, Renderman, Redshift units)
    :type intensity: float
    :param exposure: The exposure value of the light (Arnold Renderman) zero if Redshift
    :type exposure: float
    :param scaleX: The scale x of the rectangle light
    :type scaleX: float
    :param scaleY: The scale y of the rectangle light
    :type scaleY: float
    :param scaleZ: scale on z
    :type scaleZ: float
    :param shape: the string shape of the 3d object, see SHAPE_ATTR_ENUM_LIST_NICE for values ("Rectangle", "Disc" etc)
    :type shape: str
    :return intensity: the returned intensity value will be 1
    :rtype intensity: float
    :return exposure: the returned exposure value now not normalized
    :rtype exposure: float
    """
    # get pure intensity
    intensity, exposure = convertExpAndIntToIntensity(intensity, exposure)
    # get non normalized pure intensity
    intensity = convertToNormalized(intensity, scaleX, scaleY, scaleZ, shape=shape)
    # get pure exposure
    intensity, exposure = convertExpAndIntToExposure(intensity, exposure)
    return intensity, exposure


def createLight(name, shapeNodeType):
    """Function that creates a shape node of type under an empty transform, useful for light creation

    :param name: Name of the light to be created, the transform
    :type name: str
    :param shapeNodeType: the shape node to be created, eg "RedshiftPhysicalLight", the node type
    :type shapeNodeType: str
    :return lightTransformName: the name of the light (transform node)
    :rtype lightTransformName: str
    :return shapeNodeName: the name of the shape node
    :rtype shapeNodeName: str
    """
    lightTransformName = cmds.shadingNode('transform', name=name, asLight=True)
    shapeNodeName = cmds.createNode(shapeNodeType, name="{}Shape".format(name), parent=name)
    return lightTransformName, shapeNodeName


def rendererFromNodeType(lightType):
    """Returns the renderer of the given node type if it is supported by Zoo Tools.

    :param lightType: The node type of the light eg. "aiAreaLight"
    :type lightType: str

    :return: The name of the renderer "Redshift" "Arnold", "VRay" etc.  Returns "" if unknown.
    :rtype: str
    """
    lightRenderTypeDictList = [lgtcn.RENDERERSKYDOMELIGHTS, lgtcn.RENDERERDIRECTIONALLIGHTS, lgtcn.RENDERERAREALIGHTS]
    for lightRendererDict in lightRenderTypeDictList:
        for renderer in lightRendererDict:
            if type(lightRendererDict[renderer]) == list:  # some entries can have multiple lights
                for nodeType in lightRendererDict[renderer]:
                    if nodeType == lightType:
                        return renderer
            else:  # node type is a string is a string
                if lightRendererDict[renderer] == lightType:
                    return renderer
    return ""


def getAllLightShapesInScene(lightTypeList, checkRendererLoaded=False):
    """Returns any lights in the scene that may be in the global list lightTypeList

    :param lightTypeList: a list of node type names to search for
    :type lightTypeList: list
    :param checkRendererLoaded: Check the renderer is loaded matching the light type if known. Avoids warning prints.
    :type checkRendererLoaded: bool

    :return allLightShapes: all the area lights in the scene as shapeNode names
    :rtype allLightShapes: list
    """
    allLightShapes = list()
    for lightType in lightTypeList:
        if checkRendererLoaded:  # avoids prints if the renderer is not loaded
            renderer = rendererFromNodeType(lightType)
            if not renderer:
                continue  # skip as the node type is unknown
            if not rendererload.getRendererIsLoaded(renderer):
                continue  # renderer is not loaded therefor no lights will be found.
        shapesOfType = cmds.ls(type=lightType, long=True)
        if shapesOfType:  # could be empty
            for shape in shapesOfType:
                allLightShapes.append(shape)
    return list(set(allLightShapes))


def getAllLightTransformsInScene(lightTypeList):
    """Returns all the transforms of lights from lightTypeList in the scene

    :param lightTypeList: a list of node type names to search for
    :type lightTypeList: list
    :return lightsTransformList:  Light Name List of Transforms
    :rtype lightsTransformList: list
    """
    lightsShapeList = getAllLightShapesInScene(lightTypeList)
    lightsTransformList = list()
    for lightShape in lightsShapeList:  # find the transform names version of the light list
        lightsTransformList.append(cmds.listRelatives(lightShape, parent=True)[0])
    return lightsTransformList


def deleteAllLightTypes(lightTypeList):
    """deletes all lights of types lightTypeList in the scene

    :param lightTypeList: a list of node type names to search for
    :type lightTypeList: list(str)

    :return lightsTransformList:  Light Name List of Transforms
    :rtype lightsTransformList: list(str)
    """
    allLights = getAllLightTransformsInScene(lightTypeList)
    if allLights:
        cmds.delete(allLights)
    return allLights


def filterAllLightTypesFromNodes(nodes, lightTypeList):
    """filters all the lights of types lightTypeList from the selected list

    :param nodes: A list of maya node names (strings) to be filtered for lights of lightTypeList
    :type nodes: list(str)
    :param lightTypeList: a list of node type names to search for
    :type lightTypeList: list(str)

    :return lightsTransformList:  Light Name List of Transforms
    :rtype lightsTransformList: list(str)
    """
    allLightsInScene = getAllLightShapesInScene(lightTypeList)
    allLightTransforms = list()
    if allLightsInScene:
        for lightShape in allLightsInScene:
            allLightTransforms.append(cmds.listRelatives(lightShape, parent=True)[0])
    lightsInSelection = set(nodes) & set(allLightTransforms)
    return list(lightsInSelection)


def filterAllLightTypesFromSelection(lightTypeList):
    """filters all the lights of types lightTypeList from the selected list

    :param lightTypeList: a list of node type names to search for
    :type lightTypeList: list(str)

    :return lightsTransformList:  Light Name List of Transforms
    :rtype lightsTransformList: list(str)
    """
    selObj = cmds.ls(selection=True)
    return filterAllLightTypesFromNodes(selObj, lightTypeList)


def placeReflection():
    """placeReflection by braverabbit https://github.com/IngoClemens/placeReflection"""
    try:  # Place reflection is a community tool and may not be installed with the light suite
        from zoo.apps.braverabbit_place_reflection import placeReflection
        placeReflectionTool = placeReflection.PlaceReflection()
        placeReflectionTool.create()
    except ImportError:
        output.displayWarning("The package `third_party_community` must be installed for "
                              "Place Reflection by Braverabbit.")


@six.add_metaclass(classtypes.Singleton)
class ZooLightsTrackerSingleton(object):
    """Used by the lights marking menu possibly other, add light tracking data here such as copy/paste light data

    """

    def __init__(self):
        self.lightCreateOption = False
