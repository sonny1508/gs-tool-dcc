import unittest
from zoo.libs.maya.utils import mayatestutils
from zoo.libs.hive import api
from zoo.libs.hive.base.hivenodes import layers


class TestBaseLayer(mayatestutils.BaseMayaTest):
    def setUp(self):
        self.layer = layers.HiveLayer()

    def test_create(self):
        self.assertTrue(self.layer.exists())
        transform = self.layer.createTransform(name="root", parent=None)
        self.assertIsNotNone(transform)
        self.assertEqual(self.layer.rootTransform(), transform)
        self.assertTrue(self.layer.hasAttribute("rootTransform"))
        self.assertTrue(self.layer.hasAttribute("extraNodes"))

    def test_delete(self):
        self.layer.delete()
        self.assertFalse(self.layer.exists())

    def test_settings(self):
        sett = self.layer.createSettingsNode("testMe", "constants")
        self.assertIsNotNone(sett)
        nodes = list(self.layer.settingsNodes())
        self.assertEqual(len(nodes), 1)
        n = self.layer.settingNode("constants")
        self.assertIsNotNone(n)
        self.assertEqual(n, sett)

    def test_joints(self):
        jnt = self.layer.createJoint()
        self.assertIsNotNone(jnt)
        jnts = self.layer.joints()
        self.assertEqual(len(jnts), 1)
        newJnt = self.layer.createJoint(**dict(id="testJnt", name="newName"))
        self.assertEqual(len(self.layer.joints()), 2)
        self.assertEqual(self.layer.joint("testJnt"), newJnt)

    def test_extraNodes(self):
        n = api.DagNode().create("transform", nodeType="transform")
        n2 = api.DagNode().create("transform", nodeType="transform")
        n3 = api.DagNode().create("transform", nodeType="transform")
        self.layer.addExtraNode(n)
        self.layer.addExtraNodes([n2, n3])
        self.assertEqual(len(list(self.layer.extraNodes())), 3)
        self.layer.delete()
        for i in (n, n2, n3):
            self.assertFalse(i.exists())

    @unittest.skip("Not implemented")
    def test_annotations(self):
        raise NotImplementedError()

    @unittest.skip("Not implemented")
    def test_serialize(self):
        raise NotImplementedError()


class TestComponentLayer(mayatestutils.BaseMayaTest):
    def setUp(self):
        self.layer = api.HiveComponentLayer()

    def test_create(self):
        transform = self.layer.createTransform(name="layer", parent=None)
        self.assertTrue(self.layer.exists())
        self.assertEqual(self.layer.rootTransform(), transform)

    @unittest.skip("Not implemented")
    def test_components(self):
        raise NotImplementedError()

    @unittest.skip("Not implemented")
    def test_serialize(self):
        raise NotImplementedError()


class TestInputLayer(mayatestutils.BaseMayaTest):
    def setUp(self):
        self.layer = api.HiveInputLayer()

    def test_create(self):
        transform = self.layer.createTransform(name="layer", parent=None)
        self.assertTrue(self.layer.exists())
        self.assertEqual(self.layer.rootTransform(), transform)

    def test_createInputNode(self):
        inNode = self.layer.createInput(name="in", id="in00")
        self.assertTrue(inNode.exists())
        n = self.layer.inputNode("in00")
        self.assertIsNotNone(n)
        self.assertEqual(inNode, n)
        self.assertIsNone(self.layer.inputNode("NonexistentInput"))

    @unittest.skip("Not implemented")
    def test_serialize(self):
        raise NotImplementedError()


class TestOutputLayer(mayatestutils.BaseMayaTest):
    def setUp(self):
        self.layer = api.HiveOutputLayer()

    def test_create(self):
        transform = self.layer.createTransform(name="layer", parent=None)
        self.assertTrue(self.layer.exists())
        self.assertEqual(self.layer.rootTransform(), transform)

    @unittest.skip("Not implemented")
    def test_serialize(self):
        raise NotImplementedError()


class TestGuideLayer(mayatestutils.BaseMayaTest):

    def setUp(self):
        self.layer = api.HiveGuideLayer()

    def test_create(self):
        transform = self.layer.createTransform(name="layer", parent=None)
        self.assertTrue(self.layer.exists())
        self.assertEqual(self.layer.rootTransform(), transform)

    def test_deleteGuides(self):
        testGuide = self.layer.createGuide(id="testGuide", name="testGuide")
        testGuideA = self.layer.createGuide(id="testGuideA", name="testGuideA")
        self.layer.deleteGuides("testGuide")
        self.assertIsNone(self.layer.guide("testGuide"))
        self.assertFalse(testGuide.exists())
        self.assertEqual(self.layer.guide("testGuideA"), testGuideA)
        self.assertTrue(testGuideA.exists())

    @unittest.skip("Not implemented")
    def test_serialize(self):
        raise NotImplementedError()


class TestRigLayer(mayatestutils.BaseMayaTest):
    def setUp(self):
        self.layer = api.HiveRigLayer()

    def test_create(self):
        transform = self.layer.createTransform(name="layer", parent=None)
        self.assertTrue(self.layer.exists())
        self.assertEqual(self.layer.rootTransform(), transform)

    @unittest.skip("Not implemented")
    def test_serialize(self):
        raise NotImplementedError()


class TestDeformLayer(mayatestutils.BaseMayaTest):
    def setUp(self):
        self.layer = api.HiveDeformLayer()

    def test_create(self):
        transform = self.layer.createTransform(name="layer", parent=None)
        self.assertTrue(self.layer.exists())
        self.assertEqual(self.layer.rootTransform(), transform)

    @unittest.skip("Not implemented")
    def test_serialize(self):
        raise NotImplementedError()


class TestGeometryLayer(mayatestutils.BaseMayaTest):
    def setUp(self):
        self.layer = api.HiveGeometryLayer()

    def test_create(self):
        transform = self.layer.createTransform(name="layer", parent=None)
        self.assertTrue(self.layer.exists())
        self.assertEqual(self.layer.rootTransform(), transform)

    @unittest.skip("Not implemented")
    def test_serialize(self):
        raise NotImplementedError()


class TestXGroupLayer(mayatestutils.BaseMayaTest):
    def setUp(self):
        self.layer = api.HiveXGroupLayer()

    def test_create(self):
        transform = self.layer.createTransform(name="layer", parent=None)
        self.assertTrue(self.layer.exists())
        self.assertEqual(self.layer.rootTransform(), transform)

    @unittest.skip("Not implemented")
    def test_serialize(self):
        raise NotImplementedError()
