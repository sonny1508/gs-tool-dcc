from maya import cmds
from maya.api import OpenMaya as om2
from zoo.libs.maya.utils import mayatestutils
from zoo.libs.maya import zapi


class TestPlug(mayatestutils.BaseMayaTest):
    def setUp(self):
        self.base = zapi.createDag("testNode", "transform")

    def test_parent(self):
        parent = self.base.translateX.parent()
        self.assertIsNotNone(parent)
        self.assertIsInstance(parent, zapi.Plug)

    def test_apiType(self):
        self.base.apiType()

    def test_getOm2GetAttr(self):
        # test __getattr__
        plug = self.base.translate
        self.assertNotEqual(plug.name(), "")
        self.assertFalse(plug.isSource)
        # should fail with a standard python attributeError
        with self.assertRaises(AttributeError):
            plug.helloworld

    def test_standardTypeConversion(self):
        plug = self.base.translateX
        self.assertEqual(str(plug), self.base.name() + ".translateX")
        self.assertEqual(float(plug), 0.0)
        self.assertEqual(int(self.base.rotateOrder), 0.0)
        self.assertEqual(bool(self.base.visibility.value()), True)

    def test_cmdsNameCompatiblity(self):
        self.assertEqual(cmds.getAttr(str(self.base.translate)),
                          [(0.0, 0.0, 0.0)])

    def test_equality(self):
        node = zapi.createDag("testNode1", "transform")
        node.translate.set(zapi.Vector(1.0, 0.0, 0.0))
        plug = self.base.translate
        self.assertEqual(plug, plug)
        self.assertNotEquals(plug, self.base.attribute("scale"))

        self.assertIsInstance(plug.plug(), om2.MPlug)
        self.assertIsInstance(plug.node(), zapi.DGNode)

    def test_Iterables(self):
        # test compound length
        n = zapi.nodeByName("lightLinker1")
        # quick test is ensure correctness
        self.assertTrue(n.link.isArray)
        self.assertTrue(n.link.isCompound)
        self.assertEqual(len(self.base.translate), self.base.translate.plug().numChildren())

        # test array length
        self.assertEqual(len(n.link), n.mfn().findPlug("link", False).evaluateNumElements())
        # test iterator
        for child in self.base.translate:
            self.assertIsInstance(child, zapi.Plug)

        for element in n.link:
            self.assertIsInstance(element, zapi.Plug)

            self.assertTrue(element.isElement)

        for child in self.base.translate.children():
            self.assertIsInstance(child, zapi.Plug)
        # indexing
        self.assertIsInstance(self.base.translate[0], zapi.Plug)
        self.base.translate.child(0)

    def test_connect(self):
        nodeB = zapi.createDag("testNode1", "transform")
        nodeB.translate.connect(self.base.translate)
        nodeB.attribute("scale") >> self.base.attribute("scale")
        self.assertEqual(self.base.attribute("scale").source(), nodeB.attribute("scale"))
        self.assertEqual(self.base.translate.source(), nodeB.translate)
        self.assertTrue(nodeB.translate.disconnect(self.base.translate))
        nodeB.attribute("scale") // self.base.attribute("scale")
        self.assertIsNone(self.base.attribute("scale").source(), nodeB.attribute("scale"))

        nodeB.translate >> self.base.translate
        nodeB.attribute("scale") >> self.base.attribute("scale")
        self.assertTrue(len(list(nodeB.translate.destinations())), 2)
        nodeB.translate.disconnectAll()
        self.assertEqual(len(list(nodeB.translate.destinations())), 0)

    def test_get(self):
        self.assertIsInstance(self.base.translate.value(), zapi.Vector)
        self.assertIsInstance(self.base.rotate.value(), zapi.Vector)
        self.assertIsInstance(self.base.attribute("worldMatrix")[0].value(), zapi.Matrix)
        n = zapi.nodeByName("lightLinker1")
        self.assertIsInstance(n.link.value(), list)

    def test_set(self):
        self.base.translate.set((10, 0.0, 0.0))
        self.assertEqual(self.base.translate.value(), zapi.Vector(10, 0.0, 0.0))
        self.base.attribute("worldMatrix")[0].set(zapi.Matrix())

    def test_delete(self):
        p = self.base.addAttribute("test_attr", Type=zapi.attrtypes.kMFnDataString)
        self.assertTrue(self.base.hasAttribute("test_attr"))
        self.assertTrue(p.delete())
        self.assertFalse(self.base.hasAttribute("test_attr"))


class TestAddProxyAttribute(mayatestutils.BaseMayaTest):
    masterNode = None
    targetNode = None
    attributes = {}

    @classmethod
    def setUpClass(cls):
        super(TestAddProxyAttribute)
        cls.masterNode = zapi.createDag("masterNode", "transform")
        cls.targetNode = zapi.createDag("targetNode", "transform")
        cls.attributes = generateAllSupportAttributes(cls.masterNode)

    def test_addProxyBooleanAttributes(self):
        proxy = self.targetNode.addProxyAttribute(self.attributes["testBoolean"], "testBoolean")
        self.assertTrue(proxy.isProxy())

    def test_addProxyShortAttribute(self):
        plug = self.targetNode.addProxyAttribute(self.attributes["testShort"], "testShort")
        self.assertTrue(plug.isProxy())

    def test_addProxyIntAttribute(self):
        plug = self.targetNode.addProxyAttribute(self.attributes["testInt"], "testInt")
        self.assertTrue(plug.isProxy())

    def test_addProxyLongAttribute(self):
        plug = self.targetNode.addProxyAttribute(self.attributes["testLong"], "testLong")
        self.assertTrue(plug.isProxy())

    def test_addProxyByteAttribute(self):
        plug = self.targetNode.addProxyAttribute(self.attributes["testByte"], "testByte")
        self.assertTrue(plug.isProxy())

    def test_addProxyFloatAttribute(self):
        plug = self.targetNode.addProxyAttribute(self.attributes["testFloat"], "testFloat")
        self.assertTrue(plug.isProxy())

    def test_addProxyDoubleAttribute(self):
        plug = self.targetNode.addProxyAttribute(self.attributes["testDouble"], "testDouble")
        self.assertTrue(plug.isProxy())

    def test_addProxyAddrAttribute(self):
        plug = self.targetNode.addProxyAttribute(self.attributes["testAddr"], "testAddr")
        self.assertTrue(plug.isProxy())

    def test_addProxyCharAttribute(self):
        plug = self.targetNode.addProxyAttribute(self.attributes["testChar"], "testChar")
        self.assertTrue(plug.isProxy())

    def test_addProxyDistanceAttribute(self):
        plug = self.targetNode.addProxyAttribute(self.attributes["testDistance"], "testDistance")
        self.assertTrue(plug.isProxy())

    def test_addProxyAngleAttribute(self):
        plug = self.targetNode.addProxyAttribute(self.attributes["testAngle"], "testAngle")
        self.assertTrue(plug.isProxy())

    def test_addProxyTimeAttribute(self):
        plug = self.targetNode.addProxyAttribute(self.attributes["testTime"], "testTime")
        self.assertTrue(plug.isProxy())

    def test_addProxyEnumAttribute(self):
        plug = self.targetNode.addProxyAttribute(self.attributes["testEnum"], "testEnum")
        self.assertTrue(plug.isProxy())

    def test_addProxyStringAttribute(self):
        plug = self.targetNode.addProxyAttribute(self.attributes["testString"], "testString")
        self.assertTrue(plug.isProxy())

    def test_addProxyMatrixAttribute(self):
        plug = self.targetNode.addProxyAttribute(self.attributes["testMatrix"], "testMatrix")
        self.assertTrue(plug.isProxy())

    def test_addProxyDoubleArrayAttribute(self):
        plug = self.targetNode.addProxyAttribute(self.attributes["testDoubleArray"], "testDoubleArray")
        self.assertTrue(plug.isProxy())

    def test_addProxyIntArrayAttribute(self):
        plug = self.targetNode.addProxyAttribute(self.attributes["testIntArray"], "testIntArray")
        self.assertTrue(plug.isProxy())

    def test_addProxyPointArrayAttribute(self):
        plug = self.targetNode.addProxyAttribute(self.attributes["testPointArray"], "testPointArray")
        self.assertTrue(plug.isProxy())

    def test_addProxyVectorArrayAttribute(self):
        plug = self.targetNode.addProxyAttribute(self.attributes["testVectorArray"], "testVectorArray")
        self.assertTrue(plug.isProxy())

    def test_addProxyStringArrayAttribute(self):
        plug = self.targetNode.addProxyAttribute(self.attributes["testStringArray"], "testStringArray")
        self.assertTrue(plug.isProxy())

    def test_addProxyMatrixArrayAttribute(self):
        plug = self.targetNode.addProxyAttribute(self.attributes["testMatrixArray"], "testMatrixArray")
        self.assertTrue(plug.isProxy())

    def test_addProxyCompoundAttribute(self):
        plug = self.targetNode.addProxyAttribute(self.attributes["testCompound"], "testCompound")
        self.assertTrue(plug.isProxy())
        for child in plug:
            self.assertTrue(child.isProxy())

    def test_addProxy2DoubleAttribute(self):
        plug = self.targetNode.addProxyAttribute(self.attributes["test2Double"], "test2Double")
        self.assertTrue(plug.isProxy())
        for child in plug:
            self.assertTrue(child.isProxy())

    def test_addProxy2FloatAttribute(self):
        plug = self.targetNode.addProxyAttribute(self.attributes["test2Float"], "test2Float")
        self.assertTrue(plug.isProxy())
        for child in plug:
            self.assertTrue(child.isProxy())

    def test_addProxy2IntAttribute(self):
        plug = self.targetNode.addProxyAttribute(self.attributes["test2Int"], "test2Int")
        self.assertTrue(plug.isProxy())
        for child in plug:
            self.assertTrue(child.isProxy())

    def test_addProxy2LongAttribute(self):
        plug = self.targetNode.addProxyAttribute(self.attributes["test2Long"], "test2Long")
        self.assertTrue(plug.isProxy())
        for child in plug:
            self.assertTrue(child.isProxy())

    def test_addProxy2ShortAttribute(self):
        plug = self.targetNode.addProxyAttribute(self.attributes["test2Short"], "test2Short")
        self.assertTrue(plug.isProxy())
        for child in plug:
            self.assertTrue(child.isProxy())

    def test_addProxy3DoubleAttribute(self):
        plug = self.targetNode.addProxyAttribute(self.attributes["test3Double"], "test3Double")
        self.assertTrue(plug.isProxy())
        for child in plug:
            self.assertTrue(child.isProxy())

    def test_addProxy3FloatAttribute(self):
        plug = self.targetNode.addProxyAttribute(self.attributes["test3Float"], "test3Float")
        self.assertTrue(plug.isProxy())
        for child in plug:
            self.assertTrue(child.isProxy())

    def test_addProxy3IntAttribute(self):
        plug = self.targetNode.addProxyAttribute(self.attributes["test3Int"], "test3Int")
        self.assertTrue(plug.isProxy())
        for child in plug:
            self.assertTrue(child.isProxy())

    def test_addProxy3LongAttribute(self):
        plug = self.targetNode.addProxyAttribute(self.attributes["test3Long"], "test3Long")
        self.assertTrue(plug.isProxy())
        for child in plug:
            self.assertTrue(child.isProxy())

    def test_addProxy4ShortAttribute(self):
        plug = self.targetNode.addProxyAttribute(self.attributes["test4Short"], "test4Short")
        self.assertTrue(plug.isProxy())
        for child in plug:
            self.assertTrue(child.isProxy())

    def test_addProxy4DoubleAttribute(self):
        plug = self.targetNode.addProxyAttribute(self.attributes["test4Double"], "test4Double")
        self.assertTrue(plug.isProxy())
        for child in plug:
            self.assertTrue(child.isProxy())

def generateAllSupportAttributes(node):
    """Generates all currently supported attributes  on to the provided node.

    :param node: The zapi node to generate attributes for.
    :type node: :class:`zapi.DagNode`
    :return: dict of attribute name : zapi plug instance.
    :rtype: dict[str, :class:`zapi.Plug`]
    """
    testBoolean = node.addAttribute("testBoolean", Type=zapi.attrtypes.kMFnNumericBoolean)
    testShort = node.addAttribute("testShort", Type=zapi.attrtypes.kMFnNumericShort)
    testInt = node.addAttribute("testInt", Type=zapi.attrtypes.kMFnNumericInt)
    testLong = node.addAttribute("testLong", Type=zapi.attrtypes.kMFnNumericLong)
    testByte = node.addAttribute("testByte", Type=zapi.attrtypes.kMFnNumericByte)
    testFloat = node.addAttribute("testFloat", Type=zapi.attrtypes.kMFnNumericFloat)
    testDouble = node.addAttribute("testDouble", Type=zapi.attrtypes.kMFnNumericDouble)
    testAddr = node.addAttribute("testAddr", Type=zapi.attrtypes.kMFnNumericAddr)
    testChar = node.addAttribute("testChar", Type=zapi.attrtypes.kMFnNumericChar)
    testDistance = node.addAttribute("testDistance", Type=zapi.attrtypes.kMFnUnitAttributeDistance)
    testAngle = node.addAttribute("testAngle", Type=zapi.attrtypes.kMFnUnitAttributeAngle)
    testTime = node.addAttribute("testTime", Type=zapi.attrtypes.kMFnUnitAttributeTime)
    testEnum = node.addAttribute("testEnum", Type=zapi.attrtypes.kMFnkEnumAttribute)
    testString = node.addAttribute("testString", Type=zapi.attrtypes.kMFnDataString)
    testMatrix = node.addAttribute("testMatrix", Type=zapi.attrtypes.kMFnDataMatrix)
    testDoubleArray = node.addAttribute("testDoubleArray", Type=zapi.attrtypes.kMFnDataDoubleArray)
    testIntArray = node.addAttribute("testIntArray", Type=zapi.attrtypes.kMFnDataIntArray)
    testPointArray = node.addAttribute("testPointArray", Type=zapi.attrtypes.kMFnDataPointArray)
    testVectorArray = node.addAttribute("testVectorArray", Type=zapi.attrtypes.kMFnDataVectorArray)
    testStringArray = node.addAttribute("testStringArray", Type=zapi.attrtypes.kMFnDataStringArray)
    testMatrixArray = node.addAttribute("testMatrixArray", Type=zapi.attrtypes.kMFnDataMatrixArray)
    testCompound = node.addCompoundAttribute("testCompound", Type=zapi.attrtypes.kMFnCompoundAttribute,
                                             attrMap=[{"name": "testCompoundChild",
                                                       "Type": zapi.attrtypes.kMFnDataString}])
    test2Double = node.addAttribute("test2Double", Type=zapi.attrtypes.kMFnNumeric2Double)
    test2Float = node.addAttribute("test2Float", Type=zapi.attrtypes.kMFnNumeric2Float)
    test2Int = node.addAttribute("test2Int", Type=zapi.attrtypes.kMFnNumeric2Int)
    test2Long = node.addAttribute("test2Long", Type=zapi.attrtypes.kMFnNumeric2Long)
    test2Short = node.addAttribute("test2Short", Type=zapi.attrtypes.kMFnNumeric2Short)
    test3Double = node.addAttribute("test3Double", Type=zapi.attrtypes.kMFnNumeric3Double)
    test3Float = node.addAttribute("test3Float", Type=zapi.attrtypes.kMFnNumeric3Float)
    test3Int = node.addAttribute("test3Int", Type=zapi.attrtypes.kMFnNumeric3Int)
    test3Long = node.addAttribute("test3Long", Type=zapi.attrtypes.kMFnNumeric3Long)
    test4Short = node.addAttribute("test4Short", Type=zapi.attrtypes.kMFnNumeric3Short)
    test4Double = node.addAttribute("test4Double", Type=zapi.attrtypes.kMFnNumeric4Double)
    testMessage = node.addAttribute("testMessage", Type=zapi.attrtypes.kMFnMessageAttribute)
    return {
        "testBoolean": testBoolean,
        "testShort": testShort,
        "testInt": testInt,
        "testLong": testLong,
        "testByte": testByte,
        "testFloat": testFloat,
        "testDouble": testDouble,
        "testAddr": testAddr,
        "testChar": testChar,
        "testDistance": testDistance,
        "testAngle": testAngle,
        "testTime": testTime,
        "testEnum": testEnum,
        "testString": testString,
        "testMatrix": testMatrix,
        "testDoubleArray": testDoubleArray,
        "testIntArray": testIntArray,
        "testPointArray": testPointArray,
        "testVectorArray": testVectorArray,
        "testStringArray": testStringArray,
        "testMatrixArray": testMatrixArray,
        "testCompound": testCompound,
        "test2Double": test2Double,
        "test2Float": test2Float,
        "test2Int": test2Int,
        "test2Long": test2Long,
        "test2Short": test2Short,
        "test3Double": test3Double,
        "test3Float": test3Float,
        "test3Int": test3Int,
        "test3Long": test3Long,
        "test4Short": test4Short,
        "test4Double": test4Double,
        "testMessage": testMessage,
    }

