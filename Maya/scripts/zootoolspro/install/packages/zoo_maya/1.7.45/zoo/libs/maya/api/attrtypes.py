"""This module contains a centralized way of handling the many maya attribute types
which are spread across many attribute classes and these constant values
tend to conflict with each other. By using the kConstant type in this
module in conjunction with :mod:`zoo.libs.maya.api.plugs` and
:func:`zoo.libs.maya.api.nodes.addAttribute` functions you will have a single entry
point in manipulating maya attributes.

"""
from maya.api import OpenMaya as om2

#: kMFnNumericBoolean
kMFnNumericBoolean = 0
#: kMFnNumericShort
kMFnNumericShort = 1
#: kMFnNumericInt
kMFnNumericInt = 2
#: kMFnNumericLong
kMFnNumericLong = kMFnNumericInt
kMFnNumericLongLegacy = 3
#: kMFnNumericByte
kMFnNumericByte = 4
#: kMFnNumericFloat
kMFnNumericFloat = 5
#: kMFnNumericDouble
kMFnNumericDouble = 6
#: kMFnNumericAddr
kMFnNumericAddr = 7
#: kMFnNumericChar
kMFnNumericChar = 8
#: kMFnUnitAttributeDistance
kMFnUnitAttributeDistance = 9
#: kMFnUnitAttributeAngle
kMFnUnitAttributeAngle = 10
#: kMFnUnitAttributeTime
kMFnUnitAttributeTime = 11
#: kMFnkEnumAttribute
kMFnkEnumAttribute = 12
#: kMFnDataString
kMFnDataString = 13
#: kMFnDataMatrix
kMFnDataMatrix = 14
#: kMFnDataFloatArray
kMFnDataFloatArray = 15
#: kMFnDataDoubleArray
kMFnDataDoubleArray = 16
#: kMFnDataIntArray
kMFnDataIntArray = 17
#: kMFnDataPointArray
kMFnDataPointArray = 18
#: kMFnDataVectorArray
kMFnDataVectorArray = 19
#: kMFnDataStringArray
kMFnDataStringArray = 20
#: kMFnDataMatrixArray
kMFnDataMatrixArray = 21
#: kMFnCompoundAttribute
kMFnCompoundAttribute = 22
#: kMFnNumericInt64
kMFnNumericInt64 = 23
#: kMFnNumericLast
kMFnNumericLast = 24
#: kMFnNumeric2Double
kMFnNumeric2Double = 25
#: kMFnNumeric2Float
kMFnNumeric2Float = 26
#: kMFnNumeric2Int
kMFnNumeric2Int = 27
#: kMFnNumeric2Long
kMFnNumeric2Long = kMFnNumeric2Int
#: kMFnNumeric2Short
kMFnNumeric2Short = 29
#: kMFnNumeric3Double
kMFnNumeric3Double = 30
#: kMFnNumeric3Float
kMFnNumeric3Float = 31
#: kMFnNumeric3Int
kMFnNumeric3Int = 32
#: kMFnNumeric3Long
kMFnNumeric3Long = kMFnNumeric3Int
#: kMFnNumeric3Short
kMFnNumeric3Short = 34
#: kMFnNumeric4Double
kMFnNumeric4Double = 35
#: kMFnMessageAttribute
kMFnMessageAttribute = 36

_INTERNAL_TYPE_TO_MAYA_NUMERIC_TYPE = {
    kMFnNumericBoolean: (om2.MFnNumericAttribute, om2.MFnNumericData.kBoolean),
    kMFnNumericByte: (om2.MFnNumericAttribute, om2.MFnNumericData.kByte),
    kMFnNumericShort: (om2.MFnNumericAttribute, om2.MFnNumericData.kShort),
    kMFnNumericInt: (om2.MFnNumericAttribute, om2.MFnNumericData.kInt),
    kMFnNumericLongLegacy: (om2.MFnNumericAttribute, om2.MFnNumericData.kLong),  # backwards compatible with kLong
    kMFnNumericDouble: (om2.MFnNumericAttribute, om2.MFnNumericData.kDouble),
    kMFnNumericFloat: (om2.MFnNumericAttribute, om2.MFnNumericData.kFloat),
    kMFnNumericAddr: (om2.MFnNumericAttribute, om2.MFnNumericData.kAddr),
    kMFnNumericChar: (om2.MFnNumericAttribute, om2.MFnNumericData.kChar),
    kMFnNumeric2Double: (om2.MFnNumericAttribute, om2.MFnNumericData.k2Double),
    kMFnNumeric2Float: (om2.MFnNumericAttribute, om2.MFnNumericData.k2Float),
    kMFnNumeric2Int: (om2.MFnNumericAttribute, om2.MFnNumericData.k2Int),
    kMFnNumeric2Long: (om2.MFnNumericAttribute, om2.MFnNumericData.k2Long),
    kMFnNumeric2Short: (om2.MFnNumericAttribute, om2.MFnNumericData.k2Short),
    kMFnNumeric3Double: (om2.MFnNumericAttribute, om2.MFnNumericData.k3Double),
    kMFnNumeric3Float: (om2.MFnNumericAttribute, om2.MFnNumericData.k3Float),
    kMFnNumeric3Int: (om2.MFnNumericAttribute, om2.MFnNumericData.k3Int),
    kMFnNumeric3Long: (om2.MFnNumericAttribute, om2.MFnNumericData.k3Long),
    kMFnNumeric3Short: (om2.MFnNumericAttribute, om2.MFnNumericData.k3Short),
    kMFnNumeric4Double: (om2.MFnNumericAttribute, om2.MFnNumericData.k4Double)
}

_MAYATYPEFROMTYPE = {
    kMFnNumericBoolean: (om2.MFnNumericAttribute, om2.MFnNumericData.kBoolean),
    kMFnNumericByte: (om2.MFnNumericAttribute, om2.MFnNumericData.kByte),
    kMFnNumericShort: (om2.MFnNumericAttribute, om2.MFnNumericData.kShort),
    kMFnNumericInt: (om2.MFnNumericAttribute, om2.MFnNumericData.kInt),
    kMFnNumericLongLegacy: (om2.MFnNumericAttribute, om2.MFnNumericData.kLong),  # backwards compatible with kLong
    kMFnNumericDouble: (om2.MFnNumericAttribute, om2.MFnNumericData.kDouble),
    kMFnNumericFloat: (om2.MFnNumericAttribute, om2.MFnNumericData.kFloat),
    kMFnNumericAddr: (om2.MFnNumericAttribute, om2.MFnNumericData.kAddr),
    kMFnNumericChar: (om2.MFnNumericAttribute, om2.MFnNumericData.kChar),
    kMFnNumeric2Double: (om2.MFnNumericAttribute, om2.MFnNumericData.k2Double),
    kMFnNumeric2Float: (om2.MFnNumericAttribute, om2.MFnNumericData.k2Float),
    kMFnNumeric2Int: (om2.MFnNumericAttribute, om2.MFnNumericData.k2Int),
    kMFnNumeric2Long: (om2.MFnNumericAttribute, om2.MFnNumericData.k2Long),
    kMFnNumeric2Short: (om2.MFnNumericAttribute, om2.MFnNumericData.k2Short),
    kMFnNumeric3Double: (om2.MFnNumericAttribute, om2.MFnNumericData.k3Double),
    kMFnNumeric3Float: (om2.MFnNumericAttribute, om2.MFnNumericData.k3Float),
    kMFnNumeric3Int: (om2.MFnNumericAttribute, om2.MFnNumericData.k3Int),
    kMFnNumeric3Long: (om2.MFnNumericAttribute, om2.MFnNumericData.k3Long),
    kMFnNumeric3Short: (om2.MFnNumericAttribute, om2.MFnNumericData.k3Short),
    kMFnNumeric4Double: (om2.MFnNumericAttribute, om2.MFnNumericData.k4Double),
    kMFnUnitAttributeDistance: (om2.MFnUnitAttribute, om2.MFnUnitAttribute.kDistance),
    kMFnUnitAttributeAngle: (om2.MFnUnitAttribute, om2.MFnUnitAttribute.kAngle),
    kMFnUnitAttributeTime: (om2.MFnUnitAttribute, om2.MFnUnitAttribute.kTime),
    kMFnkEnumAttribute: (om2.MFnEnumAttribute, om2.MFn.kEnumAttribute),
    kMFnDataString: (om2.MFnTypedAttribute, om2.MFnData.kString),
    kMFnDataMatrix: (om2.MFnTypedAttribute, om2.MFnData.kMatrix),
    kMFnDataFloatArray: (om2.MFnTypedAttribute, om2.MFnData.kFloatArray),
    kMFnDataDoubleArray: (om2.MFnTypedAttribute, om2.MFnData.kDoubleArray),
    kMFnDataIntArray: (om2.MFnTypedAttribute, om2.MFnData.kIntArray),
    kMFnDataPointArray: (om2.MFnTypedAttribute, om2.MFnData.kPointArray),
    kMFnDataVectorArray: (om2.MFnTypedAttribute, om2.MFnData.kVectorArray),
    kMFnDataStringArray: (om2.MFnTypedAttribute, om2.MFnData.kStringArray),
    kMFnDataMatrixArray: (om2.MFnTypedAttribute, om2.MFnData.kMatrixArray),
    kMFnMessageAttribute: (om2.MFnMessageAttribute, om2.MFn.kMessageAttribute)
}

_TYPE_TO_STRING = {
    kMFnNumericBoolean: "kMFnNumericBoolean",
    kMFnNumericByte: "kMFnNumericByte",
    kMFnNumericShort: "kMFnNumericShort",
    kMFnNumericInt: "kMFnNumericInt",
    kMFnNumericDouble: "kMFnNumericDouble",
    kMFnNumericFloat: "kMFnNumericFloat",
    kMFnNumericAddr: "kMFnNumericAddr",
    kMFnNumericChar: "kMFnNumericChar",
    kMFnNumeric2Double: "kMFnNumeric2Double",
    kMFnNumeric2Float: "kMFnNumeric2Float",
    kMFnNumeric2Int: "kMFnNumeric2Int",
    kMFnNumeric2Long: "kMFnNumeric2Long",
    kMFnNumeric2Short: "kMFnNumeric2Short",
    kMFnNumeric3Double: "kMFnNumeric3Double",
    kMFnNumeric3Float: "kMFnNumeric3Float",
    kMFnNumeric3Int: "kMFnNumeric3Int",
    kMFnNumeric3Long: "kMFnNumeric3Long",
    kMFnNumeric3Short: "kMFnNumeric3Short",
    kMFnNumeric4Double: "kMFnNumeric4Double",
    kMFnUnitAttributeDistance: "kMFnUnitAttributeDistance",
    kMFnUnitAttributeAngle: "kMFnUnitAttributeAngle",
    kMFnUnitAttributeTime: "kMFnUnitAttributeTime",
    kMFnkEnumAttribute: "kMFnkEnumAttribute",
    kMFnDataString: "kMFnDataString",
    kMFnDataMatrix: "kMFnDataMatrix",
    kMFnDataFloatArray: "kMFnDataFloatArray",
    kMFnDataDoubleArray: "kMFnDataDoubleArray",
    kMFnDataIntArray: "kMFnDataIntArray",
    kMFnDataPointArray: "kMFnDataPointArray",
    kMFnDataVectorArray: "kMFnDataVectorArray",
    kMFnDataStringArray: "kMFnDataStringArray",
    kMFnDataMatrixArray: "kMFnDataMatrixArray",
    kMFnMessageAttribute: "kMFnMessageAttribute"
}

_MAYA_NUMERIC_TYPE_TO_INTERNAL_TYPE = {
    om2.MFnNumericData.kBoolean: kMFnNumericBoolean,
    om2.MFnNumericData.kByte: kMFnNumericByte,
    om2.MFnNumericData.kShort: kMFnNumericShort,
    om2.MFnNumericData.kInt: kMFnNumericInt,
    om2.MFnNumericData.kDouble: kMFnNumericDouble,
    om2.MFnNumericData.kFloat: kMFnNumericFloat,
    om2.MFnNumericData.kAddr: kMFnNumericAddr,
    om2.MFnNumericData.kChar: kMFnNumericChar,
    om2.MFnNumericData.k2Double: kMFnNumeric2Double,
    om2.MFnNumericData.k2Float: kMFnNumeric2Float,
    om2.MFnNumericData.k2Int: kMFnNumeric2Int,
    om2.MFnNumericData.k2Long: kMFnNumeric2Long,
    om2.MFnNumericData.k2Short: kMFnNumeric2Short,
    om2.MFnNumericData.k3Double: kMFnNumeric3Double,
    om2.MFnNumericData.k3Float: kMFnNumeric3Float,
    om2.MFnNumericData.k3Int: kMFnNumeric3Int,
    om2.MFnNumericData.k3Long: kMFnNumeric3Long,
    om2.MFnNumericData.k3Short: kMFnNumeric3Short,
    om2.MFnNumericData.k4Double: kMFnNumeric4Double,
    om2.MFn.kAttribute2Int: kMFnNumeric2Int,
    om2.MFn.kAttribute3Int: kMFnNumeric3Int,
    om2.MFn.kAttribute2Short: kMFnNumeric2Short,
    om2.MFn.kAttribute3Short: kMFnNumeric3Short,
    om2.MFn.kAttribute2Double: kMFnNumeric2Double,
    om2.MFn.kAttribute3Double: kMFnNumeric3Double,
    om2.MFn.kAttribute4Double: kMFnNumeric4Double,
    om2.MFn.kAttribute2Float: kMFnNumeric2Float,
    om2.MFn.kAttribute3Float: kMFnNumeric3Float

}
_MAYA_UNIT_TYPE_TO_INTERNAL_TYPE = {
    om2.MFnUnitAttribute.kDistance: kMFnUnitAttributeDistance,
    om2.MFnUnitAttribute.kAngle: kMFnUnitAttributeAngle,
    om2.MFnUnitAttribute.kTime: kMFnUnitAttributeTime
}
_MAYA_MFNDATA_TYPE_TO_INTERNAL_TYPE = {
    om2.MFnData.kString: kMFnDataString,
    om2.MFnData.kMatrix: kMFnDataMatrix,
    om2.MFnData.kFloatArray: kMFnDataFloatArray,
    om2.MFnData.kDoubleArray: kMFnDataDoubleArray,
    om2.MFnData.kIntArray: kMFnDataIntArray,
    om2.MFnData.kPointArray: kMFnDataPointArray,
    om2.MFnData.kVectorArray: kMFnDataVectorArray,
    om2.MFnData.kStringArray: kMFnDataStringArray,
    om2.MFnData.kMatrixArray: kMFnDataMatrixArray,
}
_MAYATYPE_TO_INTERNAL_TYPE = {
    om2.MFn.kEnumAttribute: kMFnkEnumAttribute,
    om2.MFn.kMessageAttribute: kMFnMessageAttribute,
    om2.MFn.kMatrixAttribute: kMFnDataMatrix
}
mayaNumericMultiTypes = (om2.MFnNumericData.k2Double, om2.MFnNumericData.k2Float, om2.MFnNumericData.k2Int,
                         om2.MFnNumericData.k2Long, om2.MFnNumericData.k2Short, om2.MFnNumericData.k3Double,
                         om2.MFnNumericData.k3Float, om2.MFnNumericData.k3Int, om2.MFnNumericData.k3Long,
                         om2.MFnNumericData.k3Short, om2.MFnNumericData.k4Double)


def mayaNumericTypeToInternalType(mayaType):
    """Returns the zoo internal attribute type for the maya numeric type

    :param mayaType: The maya attribute type
    :type mayaType: om2.MFnNumericData.kBoolean
    :return: One of our internal types ie. kMFnNumericBoolean
    :rtype: int
    """
    return _MAYA_NUMERIC_TYPE_TO_INTERNAL_TYPE.get(mayaType)


def numericTypeToMayaFnType(Type):
    """Returns the numeric attribute function object and the data type numericData.ktype
    for the provided zoo type or None,None.

    :param Type: attr types constant
    :type Type: int
    :return: variation of om2.MFnNumericAttribute, om2.MFnNumericData.k2Int
    :rtype: tuple[None or callable, None or int]
    """
    typeConversion = _INTERNAL_TYPE_TO_MAYA_NUMERIC_TYPE.get(Type)
    if not typeConversion:
        return None, None
    return typeConversion


def mayaUnitTypeToInternalType(mayaType):
    """Returns the zoo internal attribute type for the maya unit attribute type

    :param mayaType: The maya attribute type
    :type mayaType: om2.MFnUnitAttribute.kDistance
    :return: One of our internal types ie. kMFnUnitAttributeDistance
    :rtype: int
    """
    return _MAYA_UNIT_TYPE_TO_INTERNAL_TYPE.get(mayaType)


def mayaMFnDataTypeToInternalType(mayaType):
    """Returns the zoo internal attribute type for the maya TypeAttribute type.

    :param mayaType: The maya attribute type
    :type mayaType: om2.MFnData.kString
    :return: One of our internal types ie. kMFnDataString
    :rtype: int
    """
    return _MAYA_MFNDATA_TYPE_TO_INTERNAL_TYPE.get(mayaType)


def mayaTypeToInternalType(mayaType):
    """Returns the zoo internal attribute type for the maya attribute type

    :param mayaType: The maya attribute type
    :type mayaType: om2.MFn.kEnumAttribute, om2.MFn.kMessageAttribute , om2.MFn.kMatrixAttribute
    :return: One of our internal types ie. kMFnkEnumAttribute, kMFnMessageAttribute, kMFnDataMatrix
    :rtype: int
    """
    return _MAYATYPE_TO_INTERNAL_TYPE.get(mayaType)


def typeToString(attrType, default=None):
    """Returns the zoo attribute type as as a string name
    .. example:

        typeToString(attrtypes.kMFnNumericBoolean) # "kMFnNumericBoolean"
    """
    return _TYPE_TO_STRING.get(attrType, default)


def mayaTypeFromType(Type):
    """Converts the zoo attribute constant type to the maya type.

    :param Type: the zooType eg. kMFnMessageAttribute
    :type Type: int
    :return: the maya attribute object and maya data kConstant
    :rtype: tuple(Maya Attribute, int)
    """
    typeConversion = _MAYATYPEFROMTYPE.get(Type)
    if not typeConversion:
        return None, None
    return typeConversion


def mayaTypeToPythonType(mayaType):
    """From the maya data type return the same type but as a python type ie. MMatrix -> list

    :param mayaType: The maya attribute data type ie. om2.MDistance, om2.MMatrix
    :type mayaType:  any maya attribute data type
    :rtype: list, float, int, string
    """
    if isinstance(mayaType, (om2.MDistance, om2.MTime, om2.MAngle)):
        return mayaType.value
    elif isinstance(mayaType, (om2.MMatrix, om2.MVector, om2.MPoint, om2.MFloatMatrix,
                               om2.MQuaternion, om2.MEulerRotation)):
        return list(mayaType)
    return mayaType


def pythonTypeToMayaType(dataType, value):
    """Converts a Python data type to a Maya data type.

    :param dataType: The type of the data in the Maya API format.
    :type dataType: int
    :param value: The value to convert.
    :type value: Any
    :return: The converted value.
    :rtype: Any
    """
    if dataType == kMFnDataMatrixArray:
        return list(map(om2.MMatrix, value))
    elif dataType == kMFnDataVectorArray:
        return list(map(om2.MVector, value))
    elif dataType == kMFnUnitAttributeDistance:
        return om2.MDistance(value)
    elif dataType == kMFnUnitAttributeAngle:
        return om2.MAngle(value, om2.MAngle.kDegrees)
    elif dataType == kMFnUnitAttributeTime:
        return om2.MTime(value)
    return value
