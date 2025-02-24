"""Node base is used as a base class for multiple node type (usually multi-renderer) setups

Designed to be inherited by other classes.

Includes but is not restricted to:

    - Shaders
    - Lights
    - Textures etc

Author: Andrew Silke
"""


from maya import cmds

from zoo.libs.maya.cmds.objutils import namehandling
from zoo.libs.utils import color


class NodeMultiBase(object):
    """Main base class that manages node multi setups usually for multi-renderer
    """
    suffix = ""

    def __init__(self):
        """
        """
        super(NodeMultiBase, self).__init__()
        self.node = None  # needs to be overridden

    def exists(self):
        """Tests to see if the node connected to the instance exists

        :return shaderExists: True if the shader exists in the scene, False if not.
        :rtype shaderExists: bool
        """
        try:
            self.node.fullPathName()
            return True
        except (AttributeError, RuntimeError) as e:  # shader has been deleted or not created
            return False

    def create(self, message=True):
        """Should be overridden"""
        pass

    def delete(self):
        """Deletes the main node

        Can be overridden if multiple nodes"""
        if self.exists():
            cmds.delete(self.name())  # deletes the transform node and attached shape node

    def _renameUniqueSuffixName(self, newName):
        """Needs to be overridden
        """
        return newName

    def setName(self, newName, uniqueNumberSuffix=True):
        """Renames the node, auto handles suffixing with the shader type and unique names:

            shader_01_ARN if not unique becomes shader_02_ARN

        :param newName: The name to rename the current shader
        :type newName: str
        :param uniqueNumberSuffix: shader_01_ARN if not unique becomes shader_02_ARN or next unique name
        :type uniqueNumberSuffix:

        :return newName: The new name of the node
        :rtype newName: str
        """
        if self.exists():
            if newName == self.node.name():
                return newName
            if uniqueNumberSuffix and self.suffix:
                if newName.endswith(self.suffix):
                    newName = self._renameUniqueSuffixName(newName)
            shaderName = cmds.rename(self.node.fullPathName(), newName)
            self.shaderNameVal = shaderName
        else:
            if uniqueNumberSuffix:
                newName = self._renameUniqueSuffixName(newName)
            self.shaderNameVal = newName
        return newName

    def rename(self, name, uniqueNumberSuffix=True):
        """Renames the node, auto handles suffixing with the shader type and unique names:

            shader_01_ARN if not unique becomes shader_02_ARN

        See also self.setName()

        :param newName: The name to rename the current shader
        :type newName: str
        :param uniqueNumberSuffix: shader_01_ARN if not unique becomes shader_02_ARN or next unique name
        :type uniqueNumberSuffix:

        :return newName: The new name of the node
        :rtype newName: str
        """
        return self.setName(name, uniqueNumberSuffix=uniqueNumberSuffix)

    def name(self):
        """Returns the fullpath name of the node if it exists

        :return nodeName: The name of main node
        :rtype nodeName: str
        """
        if self.exists():
            self.nameVal = self.node.fullPathName()
            return self.nameVal
        else:
            return self.nameVal

    def nodeZapi(self):
        """Returns the name of the main node as a zapi object.

        :return: Zapi node object or None if does not exist
        :rtype: :class:`zapi.DGNode`
        """
        return self.node

    def shortName(self):
        """Returns the short name of the node if it exists

        :return shortName: The shortened name if a DAG node
        :rtype shortName: str
        """
        longName = self.name()
        return namehandling.getShortName(longName)

    def shapeName(self):
        """Returns the shape node name (str) of the current node, will return "" if it doesn't exist.

        Is not used by DG nodes and will return None.

        :return shapeNodeName: the name of the lights shape node, returns "" if doesn't exist
        :rtype shapeNodeName: str
        """
        transform = self.name()
        if not cmds.objExists(transform):
            return ""  # doesn't exist
        shapes = cmds.listRelatives(transform, shapes=True, fullPath=True)
        if not shapes:
            return ""  # doesn't exist
        return shapes[0]

    def _setDictSingle(self, genAttrDict, dictKey, classValue, defaultValue, noneIsDefault):
        """Method for handling None or missing keys in a genAttrDict

        :param genAttrDict: The generic attr dict
        :type genAttrDict: dict
        :param dictKey: dictionary keys eg "gDiffuse"
        :type dictKey: str
        :param classValue: the current class value eg. self.diffuseVal
        :type classValue: float or list(float)
        :param defaultValue: the default value for this attribute
        :type defaultValue: float or list(float)
        :param noneIsDefault: If None or not found then set the attribute to it's default value, if not leave it.
        :type noneIsDefault: bool
        :return classValue: The value of the attribute now potentially corrected.
        :rtype classValue: float or list(float)
        """
        if dictKey in genAttrDict:
            if genAttrDict[dictKey] is not None:
                classValue = genAttrDict[dictKey]
            elif noneIsDefault:
                classValue = defaultValue
        elif noneIsDefault:
            classValue = defaultValue
        return classValue

    def renderer(self):
        """Returns the current renderer as a string.

        Should be overridden.  If Unknown returns "".

        :return renderer: "Arnold", "Maya" "Redshift" etc.
        :rtype renderer: str
        """
        return ""

    # -------------------
    # Color
    # -------------------

    def _srgbColor(self, linearColor):
        """Converts linear color to SRGB and handles potential None values.

        returns:
            srgbColor float eg [0.0, 0.5, 1.0]

        :param linearColor: Float color in linear space eg [0.0, 0.5, 1.0]
        :type linearColor: list(float)
        :return srgbColor: Color now converted to srgb space or None if was no color given. eg [0.0, 0.6, 0.9]
        :rtype srgbColor: list(float)
        """
        if linearColor:
            return color.convertColorLinearToSrgb(linearColor)
        return None

    # -------------------
    # Attributes
    # -------------------

    def _setAttrVector(self, attributeName, vector, node=""):
        """Sets a 3x vector attribute, returns None if textured or unusable

        :param attributeName: The maya attribute name
        :type attributeName: str
        :param vector: A float vector (0.5, 0.5, 0.5)
        :type vector: list(float)
        :param node: An optional Maya node as a string name, if left empty will use the default node
        :type node: str

        :return attributeSet: True if the attribute was set, False if not due to textured or locked
        :rtype attributeSet: bool
        """
        if not self._attrSettable(attributeName, node=node):
            return False
        if node:  # If overriding the base node
            cmds.setAttr(".".join([node, attributeName]),
                         vector[0], vector[1], vector[2],
                         type="double3")
        else:  # Otherwise use the default node
            cmds.setAttr(".".join([self.node.fullPathName(), attributeName]),
                         vector[0], vector[1], vector[2],
                         type="double3")
        return True

    def _setAttrScalar(self, attributeName, value, node="", type=""):
        """Sets a scalar single value attribute, returns None if textured/connected

        :param attributeName: The maya attribute name
        :type attributeName: str
        :param value: A single float value
        :type value: float
        :param node: An optional Maya node as a string name, if left empty will use the default node
        :type node: str
        :param node: The attribute type, leave empty for numerical attributes use "string" for text
        :type node: str

        :return attributeSet: True if the attribute was set, False if not due to textured or locked
        :rtype attributeSet: bool
        """
        if not self._attrSettable(attributeName, node=node):
            return False

        if not node:
            node = self.node.fullPathName()
        if type == "string":
            cmds.setAttr(".".join([node, attributeName]), value, type=type)
        else:
            cmds.setAttr(".".join([node, attributeName]), value)
        return True

    def _getAttrVector(self, attributeName, node=""):
        """Gets the 3x vector of an attribute

        :param attributeName: The maya attribute name
        :type attributeName: str
        :param node: An optional Maya node as a string name, if left empty will use the default node
        :type node: str

        :return vector:  The vector returned [1.0, 0.0, 0.1], if connected or locked returns None
        :rtype vector: list(float)
        """
        if not node:  # Use base node
            node = self.node.fullPathName()
        return cmds.getAttr(".".join([node, attributeName]))[0]

    def _getAttrScalar(self, attributeName, node=""):
        """Gets the value of an float or int attribute

        :param attributeName: The maya attribute name
        :type attributeName: str
        :param node: An optional Maya node as a string name, if left empty will use the default node
        :type node: str

        :return value: The value returned, if textured of locked returns None
        :rtype value: float or int
        """
        if not node:  # Use base node
            node = self.node.fullPathName()
        return cmds.getAttr(".".join([node, attributeName]))

    def _attrSettable(self, attributeName, node=""):
        """Tests if the attribute name is settable, if False it's textured or locked

        :param attributeName: The maya attribute name
        :type attributeName: str
        :param node: An optional Maya node as a string name, if left empty will use the default node
        :type node: str

        :return settable: True and the attribute is settable, False and the attribute is locked or textured
        :rtype settable: str
        """
        if not node:  # Use base node
            node = self.node.fullPathName()
        return cmds.getAttr(".".join([node, attributeName]), settable=True)

