from maya.api import OpenMaya as om2

kRotateOrder_XYZ = 0
kRotateOrder_YZX = 1
kRotateOrder_ZXY = 2
kRotateOrder_XZY = 3
kRotateOrder_YXZ = 4
kRotateOrder_ZYX = 5

kRotateOrderNames = ("xyz", "yzx", "zxy", "xzy", "yxz", "zyx")

kRotateOrders = {
    kRotateOrder_XYZ: om2.MTransformationMatrix.kXYZ,
    kRotateOrder_YZX: om2.MTransformationMatrix.kYZX,
    kRotateOrder_ZXY: om2.MTransformationMatrix.kZXY,
    kRotateOrder_XZY: om2.MTransformationMatrix.kXZY,
    kRotateOrder_YXZ: om2.MTransformationMatrix.kYXZ,
    kRotateOrder_ZYX: om2.MTransformationMatrix.kZYX
}
kMayaToRotateOrder = {
    om2.MTransformationMatrix.kXYZ: kRotateOrder_XYZ,
    om2.MTransformationMatrix.kYZX: kRotateOrder_YZX,
    om2.MTransformationMatrix.kZXY: kRotateOrder_ZXY,
    om2.MTransformationMatrix.kXZY: kRotateOrder_XZY,
    om2.MTransformationMatrix.kYXZ: kRotateOrder_YXZ,
    om2.MTransformationMatrix.kZYX: kRotateOrder_ZYX
}