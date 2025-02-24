__all__ = ["AttributeDefinition",
           "VectorAttributeDefinition",
           "attributeClassForDef"]

from zoo.libs.utils import general
from zoo.libs.maya.api import attrtypes
from zoo.libs.maya import zapi


class AttributeDefinition(general.ObjectDict):
    """Wrapper class to handle maya type to dict storage. Each key which requires a maya
    data type will be either returned or converted back to a json compatible datatype.

    i.e. Matrices will be MMatrix when getting a value but a list will be serialized for json.

    :keyword name (str): The name of the attribute.
    :keyword value (int or float or str or iterable): The current value matching that of the type.
    :keyword default (int or float or str or iterable): The default value matching that of the type.
    :keyword Type (int): the attribute mfn number. see: :ref:`zooMayaApi-attrtypes`.
    :keyword softMin (float):
    :keyword softMax (float):
    :keyword min (float or int): If this is a numeric attribute then it's the min number.
    :keyword max (float or int): If this is a numeric attribute then it's the max number.
    :keyword locked (bool): Lock state.
    :keyword channelBox (bool): Whether this attribute displays in the channel box.
    :keyword keyable (bool): Whether this attribute  can be keyed.
    """
    @property
    def typeStr(self):
        return attrtypes.typeToString(self.get("Type", -1))

    @property
    def value(self):
        return self.get("value")

    @value.setter
    def value(self, value):
        self["value"] = value

    @property
    def default(self):
        return self.get("default")

    @default.setter
    def default(self, value):
        self["default"] = value

    @property
    def softMin(self):
        return self.get("softMin")

    @softMin.setter
    def softMin(self, value):
        self["softMin"] = value

    @property
    def softMax(self):
        return self.get("softMax")

    @softMax.setter
    def softMax(self, value):
        self["softMax"] = value

    @property
    def min(self):
        return self.get("min")

    @min.setter
    def min(self, value):
        self["min"] = value

    @property
    def max(self):
        return self.get("max")

    @max.setter
    def max(self, value):
        self["max"] = value


class VectorAttributeDefinition(AttributeDefinition):

    @property
    def value(self):
        return zapi.Vector(self.get("value", (0.0, 0.0, 0.0)))

    @value.setter
    def value(self, value):
        self["value"] = tuple(value)

    @property
    def default(self):
        return zapi.Vector(self.get("default", zapi.Vector(0.0, 0.0, 0.0)))

    @default.setter
    def default(self, value):
        self["default"] = tuple(value)

    @property
    def softMin(self):
        return zapi.Vector(self.get("softMin", zapi.Vector(0.0, 0.0, 0.0)))

    @softMin.setter
    def softMin(self, value):
        self["softMin"] = tuple(value)

    @property
    def softMax(self):
        return zapi.Vector(self.get("softMax", zapi.Vector(0.0, 0.0, 0.0)))

    @softMax.setter
    def softMax(self, value):
        self["softMax"] = tuple(value)

    @property
    def min(self):
        return zapi.Vector(self.get("min", zapi.Vector(0.0, 0.0, 0.0)))

    @min.setter
    def min(self, value):
        self["min"] = tuple(value)

    @property
    def max(self):
        return zapi.Vector(self.get("max", zapi.Vector(0.0, 0.0, 0.0)))

    @max.setter
    def max(self, value):
        self["max"] = tuple(value)


def attributeClassForType(attrType):
    return ATTRIBUTE_TYPES.get(attrType, AttributeDefinition)


def attributeClassForDef(definition):
    defType = definition.get("Type", -1)
    instance = attributeClassForType(defType)
    return instance(definition)


# Attribute registry for each zoo attribute api type.
ATTRIBUTE_TYPES = {
    attrtypes.kMFnNumericBoolean: AttributeDefinition,
    attrtypes.kMFnNumericByte: AttributeDefinition,
    attrtypes.kMFnNumericShort: AttributeDefinition,
    attrtypes.kMFnNumericInt: AttributeDefinition,
    attrtypes.kMFnNumericDouble: AttributeDefinition,
    attrtypes.kMFnNumericFloat: AttributeDefinition,
    attrtypes.kMFnNumericAddr: AttributeDefinition,
    attrtypes.kMFnNumericChar: AttributeDefinition,
    attrtypes.kMFnNumeric2Double: AttributeDefinition,
    attrtypes.kMFnNumeric2Float: AttributeDefinition,
    attrtypes.kMFnNumeric2Int: AttributeDefinition,
    attrtypes.kMFnNumeric2Short: AttributeDefinition,
    attrtypes.kMFnNumeric3Double: VectorAttributeDefinition,
    attrtypes.kMFnNumeric3Float: VectorAttributeDefinition,
    attrtypes.kMFnNumeric3Int: AttributeDefinition,
    attrtypes.kMFnNumeric3Short: AttributeDefinition,
    attrtypes.kMFnNumeric4Double: AttributeDefinition,
    attrtypes.kMFnUnitAttributeDistance: AttributeDefinition,
    attrtypes.kMFnUnitAttributeAngle: AttributeDefinition,
    attrtypes.kMFnUnitAttributeTime: AttributeDefinition,
    attrtypes.kMFnkEnumAttribute: AttributeDefinition,
    attrtypes.kMFnDataString: AttributeDefinition,
    attrtypes.kMFnDataMatrix: AttributeDefinition,
    attrtypes.kMFnDataFloatArray: AttributeDefinition,
    attrtypes.kMFnDataDoubleArray: AttributeDefinition,
    attrtypes.kMFnDataIntArray: AttributeDefinition,
    attrtypes.kMFnDataPointArray: AttributeDefinition,
    attrtypes.kMFnDataVectorArray: AttributeDefinition,
    attrtypes.kMFnDataStringArray: AttributeDefinition,
    attrtypes.kMFnDataMatrixArray: AttributeDefinition,
    attrtypes.kMFnMessageAttribute: AttributeDefinition
}
