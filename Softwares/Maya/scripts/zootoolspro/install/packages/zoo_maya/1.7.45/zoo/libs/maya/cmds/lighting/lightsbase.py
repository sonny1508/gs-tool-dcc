"""Lights base is used as a base class for multiple light (multi-renderer) types

Misc methods designed to be inherited by classes:

    - area lights
    - directional light
    - hdri lights

Author: Andrew Silke
"""
from maya import cmds

from zoo.libs.maya import zapi

from zoo.libs.utils import output
from zoo.libs.maya.cmds.objutils import nodemultibase, matching, namehandling
from zoo.libs.maya.cmds.cameras import cameras
from zoo.libs.maya.cmds.lighting.lightconstants import LIGHTS_GROUP_NAME

LIGHT_SUFFIX = ""


class LightsBase(nodemultibase.NodeMultiBase):
    """Lights base class that applies to area, directional and hdri lights

    Used by lights in sub packages hdritypes, areatypes and directionaltypes
    """
    lightSuffix = LIGHT_SUFFIX

    translateAttr = "translate"
    rotateAttr = "rotate"
    scaleAttr = "scale"

    scaleMultiply = 1.0

    def __init__(self):
        """
        """
        super(LightsBase, self).__init__()
        self.node = None  # needs to be overridden

    # -------------------
    # Transforms
    # -------------------

    def _setShapeNode(self):
        """Sets the self.shapeNode from the first shape node in self.node (zapi)"""
        shapes = cmds.listRelatives(self.node.fullPathName(), shapes=True, fullPath=True)
        if shapes:
            self.shapeNode = zapi.nodeByName(shapes[0])
        else:
            self.shapeNode = None

    def renderer(self):
        return None

    def selectTransform(self):
        transform = self.name()
        if transform:
            cmds.select(transform, replace=True)

    def selectShape(self):
        shape = self.shapeName()
        if shape:
            cmds.select(shape, replace=True)

    def delete(self):
        """Deletes the transform node"""
        if self.node:
            if self.node.exists():
                cmds.delete(self.node.fullPathName())

    def matchTo(self, position="selected"):  # or "camera"
        """Matches the current light to either "selected" or "camera"

        Selection supports object, objects or components (vert/edge/faces)

        :param position: Can match to "selection" or "camera"
        :type position: str
        """
        lightTransform = self.node.fullPathName()
        selobjs = cmds.ls(selection=True, long=True)
        if position == "selected":  # create by matching to the first selected object
            if selobjs and selobjs != lightTransform:
                matching.matchToCenterObjsComponents(self.node.fullPathName(), selobjs,
                                                     aimVector=(0.0, 0.0, 1.0),
                                                     localUp=(0.0, 1.0, 0.0),
                                                     worldUp=(0.0, 1.0, 0.0))
        elif position == "camera":  # create by dropping the light at the camera position and rotation
            cam = cameras.getFocusCamera()
            if cam:
                matching.matchZooAlSimpErrConstrain(cam, self.node.fullPathName())
            else:
                output.displayWarning("No camera found. Set a 3d viewport to be active by clicking on it.")

    # -------------------
    # Zoo Lights Group
    # -------------------

    def parentZooLightGroup(self):
        """Parents the current light to the light group "ArnoldLights_grp"
        Will create the folder if it doesn't exist in the scene.

        :param renderer: Nice name of the current renderer. Subclasses can use super()
        :type renderer: str
        """
        renderer = self.renderer()
        if not renderer:
            return
        grp = "".join([renderer, LIGHTS_GROUP_NAME])
        if not cmds.objExists(grp):
            cmds.group(empty=True, name=grp)
        # Parent if not already parented -----------------------
        try:
            cmds.parent(self.name(), grp)
        except RuntimeError:  # already parented
            pass

    # -------------------
    # Renderer Suffixing
    # -------------------

    def addSuffix(self):
        """Adds the automatic suffix of the renderer eg _ARN to the lights name, suffixes are per renderer

        :return renamed: True if the name was changed, False if not.
        :rtype renamed: bool
        """
        name = self.node.fullPathName()
        if name.endswith("_{}".format(self.lightSuffix)):  # already suffixed
            return ""
        newNameUnique = self._renameUniqueSuffixName(self.node.name())
        newUniqueName = cmds.rename(self.node.fullPathName(), newNameUnique)
        return newUniqueName

    def removeSuffix(self):
        """Removes the auto suffix on a light name:

            light_01_ARN if not unique becomes light_01

        :return shaderName: The potentially changed shader name
        :rtype shaderName: str
        """
        if not self.lightSuffix:  # is ""
            return self.node.fullPathName()
        name = self.node.fullPathName()
        name = name.removesuffix("_{}".format(self.lightSuffix))
        lightName = cmds.rename(self.node.fullPathName(), name)
        return lightName

    def _renameUniqueSuffixName(self, newName):
        """Auto handles suffixing and unique names, name should already have a suffix:

            light_01_ARN if not unique becomes light_02_ARN

        :param newName: The name to rename the current light
        :type newName: ste
        :return: The new name of the light with auto suffix handled
        :rtype: str
        """
        if not self.lightSuffix:  # is ""
            return newName
        if not newName.endswith("_{}".format(self.lightSuffix)):  # not suffixed so add
            newName = "_".join([self.node.name(), self.lightSuffix])
        return namehandling.getUniqueNameSuffix(newName, self.lightSuffix, paddingDefault=2, nameAlreadySuffixed=True)

    # --------------------------
    # SET ATTRS
    # --------------------------

    def setRotate(self, rotate):
        """Sets the rotation of the Directional light.

        Note values are in generic units to account for offsets between renderers.

        :param rotate: The rotation values in degrees [0.0, 90.0, 0.0]
        :type rotate: list(float)
        """
        self._setAttrVector(self.rotateAttr, rotate)

    def rotate(self):
        return self._getAttrVector(self.rotateAttr)

    def setTranslate(self, translate):
        self._setAttrVector(self.translateAttr, translate)

    def translate(self):
        return self._getAttrVector(self.translateAttr)

    def setScale(self, scale):
        self._setAttrVector(self.scaleAttr, [scale[0]*self.scaleMultiply,
                                             scale[1]*self.scaleMultiply,
                                             scale[2]*self.scaleMultiply])

    def scale(self):
        scale = self._getAttrVector(self.scaleAttr)
        for i, axis in enumerate(scale):
            if scale[i]:  # not 0.0
                scale[i] /= self.scaleMultiply
        return scale

    # --------------------------
    # CONNECTIONS
    # --------------------------

    def shapeAttributeNames(self):
        """Should be overridden"""
        return list()

    def transformAttributeNames(self):
        """Should be overridden"""
        return list()

    def connectedAttrs(self):
        """Checks if any of the supported attributes have connections, if so returns:

        connectionDict: generic attributes as the keys and "node.attr" as connection values.

        :return connectionDict: Dictionary with generic attributes as the keys and "node.attr" as connection values
        :rtype connectionDict: dict(str)
        """
        connectionDict = dict()

        shape = self.shapeName()
        transform = self.name()
        if not transform:
            return None

        shapeAttrDict = self.shapeAttributeNames()
        transformAttrDict = self.transformAttributeNames()

        # Check Shape node attributes intensity, bgVis etc -----------
        for key in shapeAttrDict:
            attr = shapeAttrDict[key]
            if not attr:
                continue
            if cmds.listConnections(".".join([shape, attr]), destination=False, source=True):
                connectionDict[key] = cmds.listConnections(".".join([shape, attr]), plugs=True)[0]

        # Check transforms so Rotation and Scale -----------
        for key in transformAttrDict:
            attr = transformAttrDict[key]
            if not attr:
                continue
            # test vector is connected
            if cmds.listConnections(".".join([transform, attr]), destination=False, source=True):
                connectionDict[key] = cmds.listConnections(".".join([transform, attr]), plugs=True)[0]
            # test each axis of the vector is connected
            for axis in ("X", "Y", "Z"):  # must check each axis for constraint connections.
                if cmds.listConnections(".".join([transform, "".join([attr, axis])]),
                                        destination=False, source=True):
                    connectionDict[key] = cmds.listConnections(".".join([transform, "".join([attr, axis])]),
                                                               plugs=True)[0]
                    break

        return connectionDict

