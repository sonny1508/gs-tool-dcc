from maya import cmds
from maya.api import OpenMaya as om

from zoo.libs.maya.utils import mayatestutils
from zoo.libs.maya.api import nodes, attrtypes
from maya.api import OpenMaya as om2


class TestNodes(mayatestutils.BaseMayaTest):
    application = "maya"

    @classmethod
    def tearDownClass(cls):
        super(TestNodes, cls).tearDownClass()
        if cmds.objExists("transform1"):
            cmds.delete("transform1")

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
        self.assertTrue(nodes.nameFromMObject(nodes.asMObject(self.node), partialName=False).startswith("|"))
        self.assertFalse(nodes.nameFromMObject(nodes.asMObject(self.node), partialName=True).startswith("|"))

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
    application = "maya"

    @classmethod
    def tearDownClass(cls):
        super(TestAddAttribute, cls).tearDownClass()
        if cmds.objExists("transform1"):
            cmds.delete("transform1")

    def setUp(self):
        if cmds.objExists("transform1"):
            self.node = "transform1"
        else:
            self.node = cmds.createNode("transform")

    def test_addkMFnNumericBoolean(self):
        attr = nodes.addAttribute(nodes.asMObject(self.node), "kMFnNumericBoolean", "kMFnNumericBoolean",
                                  attrType=attrtypes.kMFnNumericBoolean)
        self.assertTrue(attr)

    def test_addkMFnNumericShort(self):
        attr = nodes.addAttribute(nodes.asMObject(self.node), "kMFnNumericShort", "kMFnNumericShort",
                                  attrType=attrtypes.kMFnNumericShort)
        self.assertTrue(attr)

    def test_addkMFnNumericInt(self):
        attr = nodes.addAttribute(nodes.asMObject(self.node), "kMFnNumericInt", "kMFnNumericInt",
                                  attrType=attrtypes.kMFnNumericInt)
        self.assertTrue(attr)

    def test_addkMFnNumericLongLegacy(self):
        attr = nodes.addAttribute(nodes.asMObject(self.node), "kMFnNumericLongLegacy", "kMFnNumericLongLegacy",
                                  attrType=attrtypes.kMFnNumericLongLegacy)
        self.assertTrue(attr)

    def test_addkMFnNumericByte(self):
        attr = nodes.addAttribute(nodes.asMObject(self.node), "kMFnNumericByte", "kMFnNumericByte",
                                  attrType=attrtypes.kMFnNumericByte)
        self.assertTrue(attr)

    def test_addkMFnNumericFloat(self):
        attr = nodes.addAttribute(nodes.asMObject(self.node), "kMFnNumericFloat", "kMFnNumericFloat",
                                  attrType=attrtypes.kMFnNumericFloat)
        self.assertTrue(attr)

    def test_addkMFnNumericDouble(self):
        attr = nodes.addAttribute(nodes.asMObject(self.node), "kMFnNumericDouble", "kMFnNumericDouble",
                                  attrType=attrtypes.kMFnNumericDouble)
        self.assertTrue(attr)

    def test_addkMFnNumericAddr(self):
        attr = nodes.addAttribute(nodes.asMObject(self.node), "kMFnNumericAddr", "kMFnNumericAddr",
                                  attrType=attrtypes.kMFnNumericAddr)
        self.assertTrue(attr)

    def test_addkMFnNumericChar(self):
        attr = nodes.addAttribute(nodes.asMObject(self.node), "kMFnNumericChar", "kMFnNumericChar",
                                  attrType=attrtypes.kMFnNumericChar)
        self.assertTrue(attr)

    def test_addkMFnUnitAttributeDistance(self):
        attr = nodes.addAttribute(nodes.asMObject(self.node), "kMFnUnitAttributeDistance", "kMFnUnitAttributeDistance",
                                  attrType=attrtypes.kMFnUnitAttributeDistance)
        self.assertTrue(attr)

    def test_addkMFnUnitAttributeAngle(self):
        attr = nodes.addAttribute(nodes.asMObject(self.node), "kMFnUnitAttributeAngle", "kMFnUnitAttributeAngle",
                                  attrType=attrtypes.kMFnUnitAttributeAngle)
        self.assertTrue(attr)

    def test_addkMFnUnitAttributeTime(self):
        attr = nodes.addAttribute(nodes.asMObject(self.node), "kMFnUnitAttributeTime", "kMFnUnitAttributeTime",
                                  attrType=attrtypes.kMFnUnitAttributeTime)
        self.assertTrue(attr)

    def test_addkMFnkEnumAttribute(self):
        attr = nodes.addAttribute(nodes.asMObject(self.node), "kMFnkEnumAttribute", "kMFnkEnumAttribute",
                                  attrType=attrtypes.kMFnkEnumAttribute,
                                  enums=["field1", "field2"])
        self.assertTrue(attr)

    def test_addkMFnDataString(self):
        attr = nodes.addAttribute(nodes.asMObject(self.node), "kMFnDataString", "kMFnDataString",
                                  attrType=attrtypes.kMFnDataString)
        self.assertTrue(attr)

    def test_addkMFnDataMatrix(self):
        attr = nodes.addAttribute(nodes.asMObject(self.node), "kMFnDataMatrix", "kMFnDataMatrix",
                                  attrType=attrtypes.kMFnDataMatrix)
        self.assertTrue(attr)

    def test_addkMFnDataFloatArray(self):
        # float array isn't supported
        with self.assertRaises(TypeError):
            nodes.addAttribute(nodes.asMObject(self.node), "kMFnDataFloatArray", "kMFnDataFloatArray",
                               attrType=attrtypes.kMFnDataFloatArray,
                               isArray=True)

    def test_addkMFnDataDoubleArray(self):
        attr = nodes.addAttribute(nodes.asMObject(self.node), "kMFnDataDoubleArray", "kMFnDataDoubleArray",
                                  attrType=attrtypes.kMFnDataDoubleArray,
                                  isArray=True)
        self.assertTrue(attr)

    def test_addkMFnDataIntArray(self):
        attr = nodes.addAttribute(nodes.asMObject(self.node), "kMFnDataIntArray", "kMFnDataIntArray",
                                  attrType=attrtypes.kMFnDataIntArray,
                                  isArray=True)
        self.assertTrue(attr)

    def test_addkMFnDataPointArray(self):
        attr = nodes.addAttribute(nodes.asMObject(self.node), "kMFnDataPointArray", "kMFnDataPointArray",
                                  attrType=attrtypes.kMFnDataPointArray,
                                  isArray=True)
        self.assertTrue(attr)

    def test_addkMFnDataVectorArray(self):
        attr = nodes.addAttribute(nodes.asMObject(self.node), "kMFnDataVectorArray", "kMFnDataVectorArray",
                                  attrType=attrtypes.kMFnDataVectorArray,
                                  isArray=True)
        self.assertTrue(attr)

    def test_addkMFnDataStringArray(self):
        attr = nodes.addAttribute(nodes.asMObject(self.node), "kMFnDataStringArray", "kMFnDataStringArray",
                                  attrType=attrtypes.kMFnDataStringArray, isArray=True)
        self.assertTrue(attr)

    def test_addkMFnDataMatrixArray(self):
        attr = nodes.addAttribute(nodes.asMObject(self.node), "kMFnDataMatrixArray", "kMFnDataMatrixArray",
                                  attrType=attrtypes.kMFnDataMatrixArray, isArray=True)
        self.assertTrue(attr)

    def test_addkMFnCompoundAttribute(self):
        attr = nodes.addCompoundAttribute(nodes.asMObject(self.node), "kMFnCompoundAttribute", "kMFnCompoundAttribute",
                                          attrMap=[
                                              {"name": "testChild", "Type": attrtypes.kMFnNumericFloat},
                                              {"name": "testChild2", "Type": attrtypes.kMFnNumericFloat}
                                          ]
                                          )
        self.assertTrue(attr)

    def test_addkMFnNumericInt64(self):
        # float array isn't supported
        with self.assertRaises(TypeError):
            nodes.addAttribute(nodes.asMObject(self.node), "kMFnNumericInt64", "kMFnNumericInt64",
                               attrType=attrtypes.kMFnNumericInt64)

    def test_addkMFnNumericLast(self):
        # float array isn't supported
        with self.assertRaises(TypeError):
            attr = nodes.addAttribute(nodes.asMObject(self.node), "kMFnNumericLast", "kMFnNumericLast",
                                      attrType=attrtypes.kMFnNumericLast)

    def test_addkMFnNumeric2Double(self):
        attr = nodes.addAttribute(nodes.asMObject(self.node), "kMFnNumeric2Double", "kMFnNumeric2Double",
                                  attrType=attrtypes.kMFnNumeric2Double)
        self.assertTrue(attr)

    def test_addkMFnNumeric2Float(self):
        attr = nodes.addAttribute(nodes.asMObject(self.node), "kMFnNumeric2Float", "kMFnNumeric2Float",
                                  attrType=attrtypes.kMFnNumeric2Float)
        self.assertTrue(attr)

    def test_addkMFnNumeric2Int(self):
        attr = nodes.addAttribute(nodes.asMObject(self.node), "kMFnNumeric2Int", "kMFnNumeric2Int",
                                  attrType=attrtypes.kMFnNumeric2Int)
        self.assertTrue(attr)

    def test_addkMFnNumeric2Short(self):
        attr = nodes.addAttribute(nodes.asMObject(self.node), "kMFnNumeric2Short", "kMFnNumeric2Short",
                                  attrType=attrtypes.kMFnNumeric2Short)
        self.assertTrue(attr)

    def test_addkMFnNumeric3Double(self):
        attr = nodes.addAttribute(nodes.asMObject(self.node), "kMFnNumeric3Double", "kMFnNumeric3Double",
                                  attrType=attrtypes.kMFnNumeric3Double)
        self.assertTrue(attr)

    def test_addkMFnNumeric3Float(self):
        attr = nodes.addAttribute(nodes.asMObject(self.node), "kMFnNumeric3Float", "kMFnNumeric3Float",
                                  attrType=attrtypes.kMFnNumeric3Float)
        self.assertTrue(attr)

    def test_addkMFnNumeric3Int(self):
        attr = nodes.addAttribute(nodes.asMObject(self.node), "kMFnNumeric3Int", "kMFnNumeric3Int",
                                  attrType=attrtypes.kMFnNumeric3Int)
        self.assertTrue(attr)

    def test_addkMFnNumeric3Short(self):
        attr = nodes.addAttribute(nodes.asMObject(self.node), "kMFnNumeric3Short", "kMFnNumeric3Short",
                                  attrType=attrtypes.kMFnNumeric3Short)
        self.assertTrue(attr)

    def test_addkMFnNumeric4Double(self):
        attr = nodes.addAttribute(nodes.asMObject(self.node), "kMFnNumeric4Double", "kMFnNumeric4Double",
                                  attrType=attrtypes.kMFnNumeric4Double)
        self.assertTrue(attr)

    def test_addkMFnMessageAttribute(self):
        attr = nodes.addAttribute(nodes.asMObject(self.node), "kMFnMessageAttribute", "kMFnMessageAttribute",
                                  attrType=attrtypes.kMFnMessageAttribute)
        self.assertTrue(attr)
