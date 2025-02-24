from zoo.libs.hive import api
from zoo.libs.maya.utils import mayatestutils


class TestRig(mayatestutils.BaseMayaTest):
    def setUp(self):
        self.rig = api.Rig()

    def test_create(self):
        meta = self.rig.startSession("HiveRig")
        self.assertIsNotNone(meta)
        self.assertIsNotNone(self.rig.meta)
        self.assertIsInstance(self.rig.meta, api.HiveRig)
        # test attribute existence
        self.assertIsInstance(self.rig.rootTransform(), api.DagNode)

    def test_defaults(self):
        self.rig.startSession("HiveRig")
        self.assertEqual(self.rig.meta.hName.asString(), "HiveRig")
        self.assertEqual(self.rig.meta.attribute(api.constants.ID_ATTR).value(), "HiveRig")
        self.assertTrue(self.rig.meta.attribute("isHive").asBool())
        self.assertTrue(self.rig.meta.attribute(api.constants.ISHIVEROOT_ATTR).asBool())

    def test_name(self):
        self.rig.startSession("HiveRig")
        metaNode = self.rig.meta
        rootTransform = metaNode.rootTransform()
        nameConfig = self.rig.namingConfiguration()
        selectionSets = self.rig.selectionSets()
        self.assertEqual(self.rig.name(), "HiveRig")
        self.assertEqual(self.rig.meta.attribute(api.constants.HNAME_ATTR).value(), "HiveRig")
        self.assertEqual(metaNode.name(), nameConfig.resolve("rigMeta", {"rigName": "HiveRig", "type": "meta"}))
        self.assertEqual(rootTransform.name(), nameConfig.resolve("rigHrc", {"rigName": "HiveRig", "type": "hrc"}))
        self._testSelectionSetNames(selectionSets, nameConfig, "HiveRig")
        self.rig.rename("ROBOT")

        self.assertEqual(self.rig.name(), "ROBOT")
        self.assertEqual(self.rig.meta.attribute(api.constants.HNAME_ATTR).value(), "ROBOT")
        self.assertEqual(metaNode.name(), nameConfig.resolve("rigMeta", {"rigName": "ROBOT", "type": "meta"}))
        self.assertEqual(rootTransform.name(), nameConfig.resolve("rigHrc", {"rigName": "ROBOT", "type": "hrc"}))
        self._testSelectionSetNames(selectionSets, nameConfig, "ROBOT")

    def _testSelectionSetNames(self, selectionSets, config, name):
        # check selection set names
        self.assertEqual(selectionSets["ctrls"].name(),
                         config.resolve("selectionSet", {"rigName": name,
                                                         "selectionSet": "ctrls",
                                                         "type": "objectSet"}))
        self.assertEqual(selectionSets["deform"].name(),
                         config.resolve("selectionSet", {"rigName": name,
                                                         "selectionSet": "deform",
                                                         "type": "objectSet"}))
        self.assertEqual(selectionSets["root"].name(),
                         config.resolve("rootSelectionSet", {"rigName": name,
                                                             "selectionSet": "rig",
                                                             "type": "objectSet"}))

    def test_createRigLayers(self):
        self.rig.startSession("HiveRig")

        compLayer = self.rig.getOrCreateComponentLayer()
        deformLayer = self.rig.getOrCreateDeformLayer()
        geoLayer = self.rig.getOrCreateGeometryLayer()
        namer = self.rig.namingConfiguration()
        rigName = self.rig.name()
        for layer, layerType in zip((compLayer, deformLayer, geoLayer),
                                    (api.constants.COMPONENT_LAYER_TYPE,
                                     api.constants.DEFORM_LAYER_TYPE,
                                     api.constants.GEOMETRY_LAYER_TYPE)):
            hrcName, metaName = api.naming.composeRigNamesForLayer(namer, rigName, layerType)
            self.assertEqual(layer.name(), metaName)
            self.assertEqual(layer.rootTransform().name(), hrcName)
