from maya import cmds
from maya.api import OpenMaya as om

from zoo.libs.maya.utils import mayatestutils
from zoo.libs.maya.api import nodes,attrtypes,plugs
from zoo.libs.maya import zapi
from maya.api import OpenMaya as om2


class TestNodes(mayatestutils.BaseMayaTest):
    def setUp(self):
        self.node = cmds.createNode("transform")

    def test_isValidMDagPath(self):
        obj = om.MFnDagNode(nodes.asMObject(self.node)).getPath()
        self.assertTrue(nodes.isValidMDagPath(obj))

    def test_toApiObjectReturnsDagNode(self):
        obj = nodes.toApiMFnSet(self.node)
        self.assertIsInstance(obj, om.MFnDagNode)

    def test_toApiObjectReturnsDependNode(self):
        node = cmds.createNode("multiplyDivide")
        self.assertIsInstance(nodes.toApiMFnSet(node), om.MFnDependencyNode)

    def test_asMObject(self):
        self.assertIsInstance(nodes.asMObject(self.node), om.MObject)

    def test_hasParent(self):
        obj = nodes.asMObject(self.node)
        self.assertFalse(nodes.hasParent(obj))
        transform = cmds.createNode("transform")
        nodes.setParent(obj, nodes.asMObject(transform))
        self.assertTrue(nodes.hasParent(obj))

    def test_setParent(self):
        obj = nodes.asMObject(self.node)
        self.assertFalse(nodes.hasParent(obj))
        transform = nodes.asMObject(cmds.createNode("transform"))
        nodes.setParent(transform, obj)
        self.assertTrue(nodes.hasParent(transform))

    def test_getParent(self):
        obj = nodes.asMObject(self.node)
        self.assertFalse(nodes.hasParent(obj))
        transform = nodes.asMObject(cmds.createNode("transform"))
        nodes.setParent(transform, obj)
        parent = nodes.getParent(transform)
        self.assertEqual(parent, obj)

    def test_getChildren(self):
        parent = nodes.asMObject(cmds.group(self.node))
        children = nodes.getChildren(parent)
        self.assertEqual(len(children), 1)
        self.assertIsInstance(children[0], om.MObject)
        secondChild = nodes.asMObject(cmds.createNode("transform"))
        nodes.setParent(secondChild, parent)
        children = nodes.getChildren(parent)

        self.assertEqual(len(children), 2)
        thirdChild = nodes.asMObject(cmds.createNode("transform"))
        nodes.setParent(thirdChild, parent)
        children = nodes.getChildren(parent, recursive=True)
        self.assertEqual(len(children), 3)

    def test_iterParent(self):
        cmds.group(self.node)
        cmds.group(self.node)
        cmds.group(self.node)
        parents = [i for i in nodes.iterParents(nodes.asMObject(self.node))]
        self.assertEqual(len(parents), 3)

    def test_childPathAtIndex(self):
        nodeParent = nodes.asMObject(cmds.group(self.node))
        child1 = nodes.asMObject(cmds.createNode("transform"))
        nodes.setParent(child1, nodeParent)
        dagPath = om.MFnDagNode(nodeParent).getPath()
        self.assertEqual(nodes.childPathAtIndex(dagPath, 0).partialPathName(), self.node)

    def test_childPaths(self):
        nodeParent = nodes.asMObject(cmds.group(self.node))
        child1 = nodes.asMObject(cmds.createNode("transform"))
        nodes.setParent(child1, nodeParent)
        dagPath = om.MFnDagNode(nodeParent).getPath()
        self.assertEqual(len(nodes.childPaths(dagPath)), 2)
        self.assertTrue(all(isinstance(i, om.MDagPath) for i in nodes.childPaths(dagPath)))

    def test_childPathsByFn(self):
        nodeParent = nodes.asMObject(cmds.polyCube(ch=False)[0])
        nodes.setParent(nodes.asMObject(self.node), nodeParent)

        child1 = nodes.asMObject(cmds.createNode("transform"))
        child2 = nodes.asMObject(cmds.createNode("transform"))
        nodes.setParent(child1, nodeParent)
        nodes.setParent(child2, nodeParent)
        dagPath = om.MFnDagNode(nodeParent).getPath()
        results = nodes.childPathsByFn(dagPath, om2.MFn.kTransform)
        self.assertEqual(len(results), 3)
        results = nodes.childPathsByFn(dagPath, om2.MFn.kMesh)
        self.assertEqual(len(results), 1)

    def test_childTransforms(self):
        nodeParent = nodes.asMObject(cmds.group(self.node))
        child1 = nodes.asMObject(cmds.createNode("transform"))
        nodes.setParent(child1, nodeParent)
        dagPath = om.MFnDagNode(nodeParent).getPath()
        self.assertEqual(len(nodes.childTransforms(dagPath)), 2)
        self.assertTrue(all(isinstance(i, om.MDagPath) for i in nodes.childPaths(dagPath)))
        self.assertTrue(all(i.apiType() == om.MFn.kTransform for i in nodes.childPaths(dagPath)))

    def test_getShapes(self):
        node = nodes.asMObject(cmds.polyCube(ch=False)[0])
        self.assertEqual(len(nodes.shapes(om.MFnDagNode(node).getPath())), 1)
        self.assertIsInstance(nodes.shapes(om.MFnDagNode(node).getPath())[0], om.MDagPath)

    def test_nameFromMObject(self):
        self.assertTrue(nodes.toApiMFnSet(self.node).fullPathName().startswith("|"))
        self.assertFalse(zapi.nodeByName(self.node).fullPathName(partialName=True, includeNamespace=False).startswith("|"))

    def test_parentPath(self):
        group = nodes.toApiMFnSet(cmds.createNode("transform"))
        self.assertIsNone(nodes.parentPath(group.getPath()))
        cmds.group(nodes.nameFromMObject(group.object()))
        parent = nodes.parentPath(group.getPath())
        self.assertIsInstance(parent, om.MDagPath)
        self.assertTrue(parent.partialPathName().startswith("group"))

    def test_deleteNode(self):
        node = om2.MObjectHandle(nodes.createDagNode("testTransform", "transform"))

        self.assertTrue(node.isValid() and node.isAlive())
        nodes.delete(node.object())
        self.assertFalse(node.isValid() and node.isAlive())

    def test_getObjectMatrix(self):
        node = nodes.asMObject(self.node)
        matrix = nodes.getMatrix(node)
        self.assertIsInstance(matrix, om2.MMatrix)
        matPl = om2.MFnDagNode(node).findPlug("matrix", False)
        self.assertEqual(matrix, om2.MFnMatrixData(matPl.asMObject()).matrix())

    def test_getParentMatrix(self):
        node = nodes.asMObject(self.node)
        matrix = nodes.getParentMatrix(node)
        self.assertIsInstance(matrix, om2.MMatrix)
        parentPlug = om2.MFnDagNode(node).findPlug("parentMatrix", False)
        parentPlug.evaluateNumElements()
        matPl = parentPlug.elementByPhysicalIndex(0)
        self.assertEqual(matrix, om2.MFnMatrixData(matPl.asMObject()).matrix())

    def test_getParentInverseMatrix(self):
        node = nodes.asMObject(self.node)
        matrix = nodes.getParentInverseMatrix(node)
        self.assertIsInstance(matrix, om2.MMatrix)
        parentPlug = om2.MFnDagNode(node).findPlug("parentInverseMatrix", False)
        parentPlug.evaluateNumElements()
        matPl = parentPlug.elementByPhysicalIndex(0)
        self.assertEqual(matrix, om2.MFnMatrixData(matPl.asMObject()).matrix())

    def test_getWorldMatrix(self):
        node = nodes.asMObject(self.node)
        matrix = nodes.getWorldMatrix(node)
        self.assertIsInstance(matrix, om2.MMatrix)
        parentPlug = om2.MFnDagNode(node).findPlug("worldMatrix", False)
        parentPlug.evaluateNumElements()
        matPl = parentPlug.elementByPhysicalIndex(0)
        self.assertEqual(matrix, om2.MFnMatrixData(matPl.asMObject()).matrix())

    def test_getWorldInverseMatrix(self):
        node = nodes.asMObject(self.node)
        matrix = nodes.getWorldInverseMatrix(node)
        self.assertIsInstance(matrix, om2.MMatrix)
        parentPlug = om2.MFnDagNode(node).findPlug("worldInverseMatrix", False)
        parentPlug.evaluateNumElements()
        matPl = parentPlug.elementByPhysicalIndex(0)
        self.assertEqual(matrix, om2.MFnMatrixData(matPl.asMObject()).matrix())

    def test_getTranslation(self):
        node = nodes.asMObject(self.node)
        om2.MFnTransform(node).setTranslation(om2.MVector(10, 10, 10), om2.MSpace.kObject)
        translation = nodes.getTranslation(node, om2.MSpace.kObject)
        self.assertIsInstance(translation, om2.MVector)
        self.assertEqual(translation, om2.MVector(10, 10, 10))

    def test_setTranslation(self):
        node = nodes.asMObject(self.node)
        nodes.setTranslation(node, om2.MVector(0, 10, 0))
        self.assertEqual(nodes.getTranslation(node, space=om2.MSpace.kObject), om2.MVector(0, 10, 0))

    def test_iterAttributes(self):
        node = nodes.asMObject(self.node)
        for i in nodes.iterAttributes(node):
            self.assertIsInstance(i, om2.MPlug)
            self.assertFalse(i.isNull)

    def test_createDagNode(self):
        node = nodes.createDagNode("new", "transform")
        self.assertIsInstance(node, om2.MObject)

    def test_createDGNode(self):
        node = nodes.createDGNode("new", "network")
        self.assertIsInstance(node, om2.MObject)

    def test_lockNode(self):
        node = nodes.createDGNode("new", "network")
        nodes.lockNode(node, True)
        fn = om2.MFnDependencyNode(node)
        self.assertTrue(fn.isLocked)
        nodes.lockNode(node, False)
        self.assertFalse(fn.isLocked)
        with nodes.lockNodeContext(node, True):
            self.assertTrue(fn.isLocked)
        self.assertFalse(fn.isLocked)

    def test_lockAttributes(self):
        node = nodes.createDagNode("new", "transform")
        fn = om2.MFnDependencyNode(node)
        nodes.setLockStateOnAttributes(node, ("translateX", "rotate"))
        tx = fn.findPlug("translateX", False)
        rotate = fn.findPlug("rotate", False)
        self.assertTrue(tx.isLocked)
        self.assertTrue(rotate.isLocked)
        nodes.setLockStateOnAttributes(node, ("translateX", "rotate"), state=False)
        self.assertFalse(rotate.isLocked)



class TestAddAttribute(mayatestutils.BaseMayaTest):
    def setUp(self):
        self.node = nodes.createDagNode("testNode", "transform")

    def test_addKMFnNumericBoolean(self):
        newAttr = nodes.addAttribute(self.node, "testBoolean", "testBoolean", attrtypes.kMFnNumericBoolean)
        self.assertEqual(newAttr.object().apiType(), om2.MFn.kNumericAttribute)
        self.assertEqual(plugs.plugType(om2.MPlug(self.node, newAttr.object())), attrtypes.kMFnNumericBoolean)

    def test_addKMFnNumericShort(self):
        newAttr = nodes.addAttribute(self.node, "testShort", "testShort", attrtypes.kMFnNumericShort)
        self.assertEqual(newAttr.object().apiType(), om2.MFn.kNumericAttribute)
        self.assertEqual(plugs.plugType(om2.MPlug(self.node, newAttr.object())), attrtypes.kMFnNumericShort)

    def test_addKMFnNumericInt(self):
        newAttr = nodes.addAttribute(self.node, "testInt", "testInt", attrtypes.kMFnNumericInt)
        self.assertEqual(newAttr.object().apiType(), om2.MFn.kNumericAttribute)
        self.assertEqual(plugs.plugType(om2.MPlug(self.node, newAttr.object())), attrtypes.kMFnNumericInt)

    def test_addKMFnNumericLong(self):
        newAttr = nodes.addAttribute(self.node, "testLong", "testLong", attrtypes.kMFnNumericLong)
        self.assertEqual(newAttr.object().apiType(), om2.MFn.kNumericAttribute)
        self.assertEqual(plugs.plugType(om2.MPlug(self.node, newAttr.object())), attrtypes.kMFnNumericInt)

    def test_addKMFnNumericByte(self):
        newAttr = nodes.addAttribute(self.node, "testByte", "testByte", attrtypes.kMFnNumericByte)
        self.assertEqual(newAttr.object().apiType(), om2.MFn.kNumericAttribute)
        self.assertEqual(plugs.plugType(om2.MPlug(self.node, newAttr.object())), attrtypes.kMFnNumericByte)

    def test_addKMFnNumericFloat(self):
        newAttr = nodes.addAttribute(self.node, "testFloat", "testFloat", attrtypes.kMFnNumericFloat)
        self.assertEqual(newAttr.object().apiType(), om2.MFn.kNumericAttribute)
        self.assertEqual(plugs.plugType(om2.MPlug(self.node, newAttr.object())), attrtypes.kMFnNumericFloat)

    def test_addKMFnNumericDouble(self):
        newAttr = nodes.addAttribute(self.node, "testDouble", "testDouble", attrtypes.kMFnNumericDouble)
        self.assertEqual(newAttr.object().apiType(), om2.MFn.kNumericAttribute)
        self.assertEqual(plugs.plugType(om2.MPlug(self.node, newAttr.object())), attrtypes.kMFnNumericDouble)

    def test_addKMFnNumericAddr(self):
        newAttr = nodes.addAttribute(self.node, "testAddr", "testAddr", attrtypes.kMFnNumericAddr)
        self.assertEqual(newAttr.object().apiType(), om2.MFn.kNumericAttribute)
        self.assertEqual(plugs.plugType(om2.MPlug(self.node, newAttr.object())), attrtypes.kMFnNumericAddr)

    def test_addKMFnNumericChar(self):
        newAttr = nodes.addAttribute(self.node, "testChar", "testChar", attrtypes.kMFnNumericChar)
        self.assertEqual(newAttr.object().apiType(), om2.MFn.kNumericAttribute)
        self.assertEqual(plugs.plugType(om2.MPlug(self.node, newAttr.object())), attrtypes.kMFnNumericChar)

    def test_addKMFnUnitAttributeDistance(self):
        newAttr = nodes.addAttribute(self.node, "testDistance", "testDistance", attrtypes.kMFnUnitAttributeDistance)
        self.assertEqual(newAttr.object().apiType(), om2.MFn.kDoubleLinearAttribute)
        self.assertEqual(plugs.plugType(om2.MPlug(self.node, newAttr.object())), attrtypes.kMFnUnitAttributeDistance)

    def test_addKMFnUnitAttributeAngle(self):
        newAttr = nodes.addAttribute(self.node, "testAngle", "testAngle", attrtypes.kMFnUnitAttributeAngle)
        self.assertEqual(newAttr.object().apiType(), om2.MFn.kDoubleAngleAttribute)
        self.assertEqual(plugs.plugType(om2.MPlug(self.node, newAttr.object())), attrtypes.kMFnUnitAttributeAngle)

    def test_addKMFnUnitAttributeTime(self):
        newAttr = nodes.addAttribute(self.node, "testTime", "testTime", attrtypes.kMFnUnitAttributeTime)
        self.assertEqual(newAttr.object().apiType(), om2.MFn.kTimeAttribute)
        self.assertEqual(plugs.plugType(om2.MPlug(self.node, newAttr.object())), attrtypes.kMFnUnitAttributeTime)

    def test_addKMFnkEnumAttribute(self):
        newAttr = nodes.addAttribute(self.node, "testEnum", "testEnum", attrtypes.kMFnkEnumAttribute)
        self.assertEqual(newAttr.object().apiType(), om2.MFn.kEnumAttribute)
        self.assertEqual(plugs.plugType(om2.MPlug(self.node, newAttr.object())), attrtypes.kMFnkEnumAttribute)

    def test_addKMFnDataString(self):
        newAttr = nodes.addAttribute(self.node, "testString", "testString", attrtypes.kMFnDataString)
        self.assertEqual(newAttr.object().apiType(), om2.MFn.kTypedAttribute)
        self.assertEqual(plugs.plugType(om2.MPlug(self.node, newAttr.object())), attrtypes.kMFnDataString)

    def test_addKMFnDataMatrix(self):
        newAttr = nodes.addAttribute(self.node, "testMatrix", "testMatrix", attrtypes.kMFnDataMatrix)
        self.assertEqual(newAttr.object().apiType(), om2.MFn.kMatrixAttribute)
        self.assertEqual(plugs.plugType(om2.MPlug(self.node, newAttr.object())), attrtypes.kMFnDataMatrix)

    def test_addKMFnDataDoubleArray(self):
        newAttr = nodes.addAttribute(self.node, "testDoubleArray", "testDoubleArray", attrtypes.kMFnDataDoubleArray)
        self.assertEqual(newAttr.object().apiType(), om2.MFn.kTypedAttribute)
        self.assertEqual(plugs.plugType(om2.MPlug(self.node, newAttr.object())), attrtypes.kMFnDataDoubleArray)

    def test_addKMFnDataIntArray(self):
        newAttr = nodes.addAttribute(self.node, "testIntArray", "testIntArray", attrtypes.kMFnDataIntArray)
        self.assertEqual(newAttr.object().apiType(), om2.MFn.kTypedAttribute)
        self.assertEqual(plugs.plugType(om2.MPlug(self.node, newAttr.object())), attrtypes.kMFnDataIntArray)

    def test_addKMFnDataPointArray(self):
        newAttr = nodes.addAttribute(self.node, "testPointArray", "testPointArray", attrtypes.kMFnDataPointArray)
        self.assertEqual(newAttr.object().apiType(), om2.MFn.kTypedAttribute)
        self.assertEqual(plugs.plugType(om2.MPlug(self.node, newAttr.object())), attrtypes.kMFnDataPointArray)

    def test_addKMFnDataVectorArray(self):
        newAttr = nodes.addAttribute(self.node, "testVectorArray", "testVectorArray", attrtypes.kMFnDataVectorArray)
        self.assertEqual(newAttr.object().apiType(), om2.MFn.kTypedAttribute)
        self.assertEqual(plugs.plugType(om2.MPlug(self.node, newAttr.object())), attrtypes.kMFnDataVectorArray)

    def test_addKMFnDataStringArray(self):
        newAttr = nodes.addAttribute(self.node, "testStringArray", "testStringArray", attrtypes.kMFnDataStringArray)
        self.assertEqual(newAttr.object().apiType(), om2.MFn.kTypedAttribute)
        self.assertEqual(plugs.plugType(om2.MPlug(self.node, newAttr.object())), attrtypes.kMFnDataStringArray)

    def test_addKMFnDataMatrixArray(self):
        newAttr = nodes.addAttribute(self.node, "testMatrixArray", "testMatrixArray", attrtypes.kMFnDataMatrixArray)
        self.assertEqual(newAttr.object().apiType(), om2.MFn.kTypedAttribute)
        self.assertEqual(plugs.plugType(om2.MPlug(self.node, newAttr.object())), attrtypes.kMFnDataMatrixArray)

    def test_addKMFnCompoundAttribute(self):
        newAttr = nodes.addCompoundAttribute(self.node, "testCompound", "testCompound",
                                             attrMap=[{"name": "testCompoundChild", "Type": attrtypes.kMFnDataString}])
        plug = om2.MPlug(self.node, newAttr.object())
        self.assertEqual(newAttr.object().apiType(), om2.MFn.kCompoundAttribute)
        self.assertEqual(plugs.plugType(plug), attrtypes.kMFnCompoundAttribute)
        self.assertTrue(plug.numChildren(), 1)

    def test_addKMFnNumericInt64(self):
        with self.assertRaises(TypeError):
            nodes.addAttribute(self.node, "testInt64", "testInt64", attrtypes.kMFnNumericInt64)

    def test_addKMFnNumericLast(self):
        with self.assertRaises(TypeError):
            nodes.addAttribute(self.node, "testLast", "testLast", attrtypes.kMFnNumericLast)

    def test_addKMFnNumeric2Double(self):
        newAttr = nodes.addAttribute(self.node, "test2Double", "test2Double", attrtypes.kMFnNumeric2Double)
        self.assertEqual(newAttr.object().apiType(), om2.MFn.kAttribute2Double)
        self.assertEqual(plugs.plugType(om2.MPlug(self.node, newAttr.object())), attrtypes.kMFnNumeric2Double)

    def test_addKMFnNumeric2Float(self):
        newAttr = nodes.addAttribute(self.node, "test2Float", "test2Float", attrtypes.kMFnNumeric2Float)
        self.assertEqual(newAttr.object().apiType(), om2.MFn.kAttribute2Float)
        self.assertEqual(plugs.plugType(om2.MPlug(self.node, newAttr.object())), attrtypes.kMFnNumeric2Float)

    def test_addKMFnNumeric2Int(self):
        newAttr = nodes.addAttribute(self.node, "test2Int", "test2Int", attrtypes.kMFnNumeric2Int)
        self.assertEqual(newAttr.object().apiType(), om2.MFn.kAttribute2Int)
        self.assertEqual(plugs.plugType(om2.MPlug(self.node, newAttr.object())), attrtypes.kMFnNumeric2Int)

    def test_addKMFnNumeric2Long(self):
        newAttr = nodes.addAttribute(self.node, "test2Long", "test2Long", attrtypes.kMFnNumeric2Long)
        self.assertEqual(newAttr.object().apiType(), om2.MFn.kAttribute2Int)
        self.assertEqual(plugs.plugType(om2.MPlug(self.node, newAttr.object())), attrtypes.kMFnNumeric2Int)

    def test_addKMFnNumeric2Short(self):
        newAttr = nodes.addAttribute(self.node, "test2Short", "test2Short", attrtypes.kMFnNumeric2Short)
        self.assertEqual(newAttr.object().apiType(), om2.MFn.kAttribute2Short)
        self.assertEqual(plugs.plugType(om2.MPlug(self.node, newAttr.object())), attrtypes.kMFnNumeric2Short)

    def test_addKMFnNumeric3Double(self):
        newAttr = nodes.addAttribute(self.node, "test3Double", "test3Double", attrtypes.kMFnNumeric3Double)
        self.assertEqual(newAttr.object().apiType(), om2.MFn.kAttribute3Double)
        self.assertEqual(plugs.plugType(om2.MPlug(self.node, newAttr.object())), attrtypes.kMFnNumeric3Double)

    def test_addKMFnNumeric3Float(self):
        newAttr = nodes.addAttribute(self.node, "test3Float", "test3Float", attrtypes.kMFnNumeric3Float)
        self.assertEqual(newAttr.object().apiType(), om2.MFn.kAttribute3Float)
        self.assertEqual(plugs.plugType(om2.MPlug(self.node, newAttr.object())), attrtypes.kMFnNumeric3Float)

    def test_addKMFnNumeric3Int(self):
        newAttr = nodes.addAttribute(self.node, "test3Int", "test3Int", attrtypes.kMFnNumeric3Int)
        self.assertEqual(newAttr.object().apiType(), om2.MFn.kAttribute3Int)
        self.assertEqual(plugs.plugType(om2.MPlug(self.node, newAttr.object())), attrtypes.kMFnNumeric3Int)

    def test_addKMFnNumeric3Long(self):
        newAttr = nodes.addAttribute(self.node, "test3Long", "test3Long", attrtypes.kMFnNumeric3Long)
        self.assertEqual(newAttr.object().apiType(), om2.MFn.kAttribute3Int)
        self.assertEqual(plugs.plugType(om2.MPlug(self.node, newAttr.object())), attrtypes.kMFnNumeric3Long)

    def test_addKMFnNumeric3Short(self):
        newAttr = nodes.addAttribute(self.node, "test4Short", "test4Short", attrtypes.kMFnNumeric3Short)
        self.assertEqual(newAttr.object().apiType(), om2.MFn.kAttribute3Short)
        self.assertEqual(plugs.plugType(om2.MPlug(self.node, newAttr.object())), attrtypes.kMFnNumeric3Short)

    def test_addKMFnNumeric4Double(self):
        newAttr = nodes.addAttribute(self.node, "test4Double", "test4Double", attrtypes.kMFnNumeric4Double)
        self.assertEqual(newAttr.object().apiType(), om2.MFn.kAttribute4Double)
        self.assertEqual(plugs.plugType(om2.MPlug(self.node, newAttr.object())), attrtypes.kMFnNumeric4Double)

    def test_addKMFnMessageAttribute(self):
        newAttr = nodes.addAttribute(self.node, "testMessage", "testMessage", attrtypes.kMFnMessageAttribute)
        self.assertEqual(newAttr.object().apiType(), om2.MFn.kMessageAttribute)
        self.assertEqual(plugs.plugType(om2.MPlug(self.node, newAttr.object())), attrtypes.kMFnMessageAttribute)


