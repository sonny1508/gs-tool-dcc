import unittest
from zoo.libs.hive import api
from zoo.libs.maya.api import nodes
from zoo.libs.maya import zapi
from zoo.libs.maya.utils import mayatestutils
from zoovendor.six import string_types
from maya.api import OpenMaya as om2


class SettingsNode(mayatestutils.BaseMayaTest):
    newSceneAfterTest = False

    def setUp(self):
        self.settings = api.SettingsNode()
        self.settings.create("TestNode", "testNode")

    def test_create(self):
        self.assertTrue(self.settings.exists())
        self.assertEqual(self.settings.typeName, "network")
        # test default type
        self.assertEqual(self.settings.object().apiType(), om2.MFn.kAffect)

    def test_serializeFromScene(self):
        self.assertIsInstance(self.settings.serializeFromScene(), list)

    def test_initFromNode(self):
        panel = api.SettingsNode(nodes.createDGNode("controlPanel", nodeType="network"))
        self.assertTrue(panel.exists())


class Guide(mayatestutils.BaseMayaTest):
    newSceneAfterTest = True

    def setUp(self):
        self.guide = api.Guide()

    def tearDown(self):
        super(Guide, self).tearDown()
        if self.guide.exists():
            self.guide.delete()

    def test_create(self):
        self.guide.create(shape="cube")
        self.assertEqual(self.guide.translation(), om2.MVector(0.0, 0.0, 0.0))
        self.assertEqual(self.guide.rotation(), om2.MQuaternion(0.0, 0.0, 0.0, 1.0))
        self.assertEqual(self.guide.scale(), om2.MVector(1.0, 1.0, 1.0))
        self.assertEqual(self.guide.shapeNode().translation(), om2.MVector(0.0, 0.0, 0.0))
        self.assertEqual(self.guide.shapeNode().rotation(), om2.MQuaternion(0.0, 0.0, 0.0, 1.0))
        self.assertEqual(self.guide.shapeNode().scale(), om2.MVector(1.0, 1.0, 1.0))

    def test_shapeNode(self):
        self.guide.create()
        self.assertIsNone(self.guide.shapeNode())
        self.guide.replaceShape({"shape": "cube", "name": "test"})
        self.assertIsNotNone(self.guide.shapeNode())
        self.assertIsInstance(self.guide.shapeNode(), api.DagNode)

    def test_isGuide(self):
        self.guide.create()
        self.assertTrue(self.guide.isGuide(self.guide))

    def test_guideParent(self):
        self.guide.create(shape="cube")
        parentResult = self.guide.guideParent()
        self.assertIsNone(parentResult[0])
        self.assertIsNone(parentResult[1])
        newGuide = api.Guide()
        newGuide.create()
        shapeParent = api.createDag("testTransform", "transform")
        self.guide.setParent(newGuide, shapeParent)
        parentResult = self.guide.guideParent()
        self.assertEqual(parentResult[0], newGuide)
        self.assertEqual(parentResult[1], newGuide.id())
        shapeParent = self.guide.shapeNode().parent()
        self.assertIsInstance(shapeParent, api.DagNode)
        self.assertEqual(shapeParent, api.DagNode(nodes.getParent(self.guide.shapeNode().object())))

    def test_serialize(self):
        self.guide.create()
        data = self.guide.shape()
        info = self.guide.serializeFromScene()
        self.assertIsInstance(data, dict)
        self.assertIsInstance(info, dict)
        # we only test for keys and values unique to guides, since other tests handle the base.
        for key, valueType in (("id", string_types),
                               ("shape", dict), ("shapeTransform", dict), ("srts", list)):
            self.assertTrue(key in info, "guide key: {} doesn't exist".format(key))
            self.assertIsInstance(info[key], valueType,
                                  "invalid type value key: {}, type: {}".format(key, str(valueType)))

    def test_iterate(self):
        self.guide.create()
        parent = self.guide
        for i in range(10):
            g = api.Guide()
            g.create(parent=parent)
            parent = g
        # test no recursion
        self.assertEqual(len(list(self.guide.iterChildGuides(recursive=False))), 1)
        children = []
        for guide in self.guide.iterChildGuides(recursive=True):
            self.assertIsInstance(guide, api.Guide)
            children.append(guide)
        self.assertEqual(len(children), 10)

    def test_delete(self):
        self.guide.create()
        self.guide.deleteShapeTransform()
        self.assertIsNone(self.guide.shapeNode())
        self.guide.delete()
        self.assertFalse(self.guide.exists())


class ControlNode(mayatestutils.BaseMayaTest):
    newSceneAfterTest = True

    def setUp(self):
        self.control = api.ControlNode()
        self.control.create()

    def test_create(self):
        self.assertTrue(self.control.exists())
        self.assertEqual(self.control.typeName, "transform")
        self.assertEqual(self.control.name(), "Control")
        self.assertEqual(self.control.id(), "Control")
        self.assertEqual(self.control.rotationOrder(), api.kRotateOrder_XYZ)
        self.assertEqual(self.control.translation(), api.Vector(0, 0, 0))

        self.assertEqual(self.control.rotation(), api.Quaternion(0, 0, 0, 1.0))
        self.assertEqual(self.control.scale(), api.Vector(1.0, 1.0, 1.0))
        ctrl = api.ControlNode()
        ctrl.create(translate=api.Vector(10, 0, 0),
                    scale=(2, 2, 2),
                    rotateOrder=api.kRotateOrder_YZX)
        self.assertEqual(ctrl.translation(), api.Vector(10, 0, 0))
        self.assertEqual(ctrl.rotation(), api.Quaternion(0, 0, 0, 1.0))
        self.assertEqual(ctrl.scale(), api.Vector(2.0, 2.0, 2.0))
        self.assertEqual(ctrl.rotationOrder(), api.kRotateOrder_YZX)

    def test_controllerTag(self):
        visPlug = self.control.addAttribute("test_vis", api.attrtypes.kMFnNumericBoolean)
        tag = self.control.addControllerTag("testCtrl", parent=None, visibilityPlug=visPlug)
        self.assertIsInstance(tag, api.DGNode)
        newTag = self.control.controllerTag()
        self.assertEqual(tag, newTag)

    @unittest.skip("Not implemented")
    def test_shaping(self):
        raise NotImplementedError()

    @unittest.skip("Not implemented")
    def test_serializeFromScene(self):
        raise NotImplementedError()


class Joint(mayatestutils.BaseMayaTest):
    newSceneAfterTest = False

    def setUp(self):
        self.jnt = api.Joint()


    def test_create(self):
        self.jnt.create(rotateOrder=zapi.kRotateOrder_XZY)
        self.assertEqual(self.jnt.rotationOrder(), zapi.kRotateOrder_XZY)
        self.assertTrue(self.jnt.exists())
        self.assertEqual(self.jnt.typeName, "joint")

    @unittest.skip("Not implemented")
    def test_serializeFromScene(self):
        raise NotImplementedError()

    @unittest.skip("Not implemented")
    def test_aimToChild(self):
        raise NotImplementedError()


class Annotation(mayatestutils.BaseMayaTest):
    newSceneAfterTest = True

    def setUp(self):
        self.annotation = api.Annotation()
        self.start = api.createDag("test1", "transform")
        self.end = api.createDag("test2", "transform")

    def test_create(self):
        self.annotation.create("testAnnotation",
                               self.start,
                               self.end,
                               attrHolder=self.start,
                               parent=None)
        self.assertTrue(self.annotation.exists())
        self.assertEqual(self.annotation.startNode(), self.start)
        self.assertEqual(self.annotation.endNode(), self.end)

    @unittest.skip("Not implemented")
    def test_serializeFromScene(self):
        raise NotImplementedError()


class InputNode(mayatestutils.BaseMayaTest):
    newSceneAfterTest = False

    def setUp(self):
        self.input = api.InputNode()
        self.input.create()

    def test_create(self):
        self.assertTrue(self.input.exists())

    @unittest.skip("Not implemented")
    def test_attachedNode(self):
        raise NotImplementedError()

    @unittest.skip("Not implemented")
    def test_serializeFromScene(self):
        raise NotImplementedError()


class OutputNode(mayatestutils.BaseMayaTest):
    newSceneAfterTest = False

    def setUp(self):
        self.out = api.OutputNode()
        self.out.create()

    def test_create(self):
        self.assertTrue(self.out.exists())

    @unittest.skip("Not implemented")
    def test_attachedNode(self):
        raise NotImplementedError()

    @unittest.skip("Not implemented")
    def test_serializeFromScene(self):
        raise NotImplementedError()
