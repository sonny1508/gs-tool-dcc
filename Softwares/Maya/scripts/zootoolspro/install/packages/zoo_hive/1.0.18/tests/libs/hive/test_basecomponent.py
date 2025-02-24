import os.path

from zoo.libs.hive import api
from zoo.libs.maya.api import nodes
from zoo.libs.maya.utils import mayatestutils
from zoo.core.util import env


class TestBaseComponent(mayatestutils.BaseMayaTest):
    newSceneAfterTest = False
    newSceneAfterTearDownCls = True

    @classmethod
    def setUpClass(cls):
        super(TestBaseComponent, cls).setUpClass()
        testDataFolder = "../../testdata"
        abspath = os.path.abspath(
            os.path.join(os.path.dirname(__file__), testDataFolder)
        )
        env.addToEnv("HIVE_COMPONENT_PATH", [abspath])
        env.addToEnv("HIVE_DEFINITIONS_PATH", [abspath])
        api.Configuration().componentRegistry().discoverComponents()

    @classmethod
    def tearDownClass(cls):
        super(TestBaseComponent, cls).tearDownClass()
        testDataFolder = "../../testdata"
        absPath = os.path.abspath(
            os.path.join(os.path.dirname(__file__), testDataFolder)
        )
        env.removeFromEnv("HIVE_COMPONENT_PATH", [absPath])
        env.removeFromEnv("HIVE_DEFINITIONS_PATH", [absPath])
        api.Configuration().componentRegistry().refresh()

    def setUp(self):
        self.rig = api.Rig()
        self.rig.startSession("testRig")
        if not self.rig.hasComponent("fkChain", "M"):
            self.definition = api.ComponentDefinition()
            self.definition.side = "M"
            self.definition.name = "fkChain"
            self.definition.type = "fkchain"
            self.component = self.rig.createComponent(definition=self.definition)
        else:
            self.component = self.rig.fkChain_M
            self.definition = self.component.definition

    def test_create(self):
        component = self.rig.component(self.definition.name, self.definition.side)
        meta = component.meta
        self.assertIsNotNone(meta)
        self.assertIsNotNone(self.component.meta)
        self.assertIsInstance(self.component.meta, api.HiveComponent)
        # test attribute existence
        self.assertTrue(meta.hasAttribute(api.constants.SIDE_ATTR))
        self.assertTrue(meta.hasAttribute(api.constants.COMPONENTTYPE_ATTR))
        self.assertTrue(meta.hasAttribute(api.constants.HASGUIDE_ATTR))
        self.assertTrue(meta.hasAttribute(api.constants.HASRIG_ATTR))
        self.assertTrue(meta.hasAttribute(api.constants.HASSKELETON_ATTR))
        self.assertTrue(meta.hasAttribute(api.constants.HASPOLISHED_ATTR))
        self.assertTrue(meta.hasAttribute(api.constants.COMPONENTDEFINITION_ATTR))
        for attrName in api.constants.DEF_CACHE_ATTR_NAMES:
            self.assertIsInstance(
                meta.attribute(attrName),api.Plug, "missing attribute: {}".format(attrName)
            )
        self.assertFalse(self.component.hasGuide())
        self.assertFalse(self.component.hasRig())
        self.assertIsInstance(self.component.rootTransform(), api.DagNode)
        self.assertIsInstance(self.component.createContainer(), api.ContainerAsset)
        self.assertIsInstance(self.component.container(), api.ContainerAsset)

    def test_container(self):
        self.assertFalse(self.component.hasContainer())
        self.component.createContainer()
        self.assertTrue(self.component.hasContainer())
        self.assertTrue(self.component.deleteContainer())
        self.assertTrue(self.component.exists())
        self.assertIsNone(self.component.container())

    def test_setMetaNode(self):
        newMeta = nodes.createDagNode("bob", "transform")
        self.assertIsInstance(self.component.setMetaNode(newMeta), api.HiveComponent)

    def test_name(self):
        self.assertEqual(self.component.name(), "fkChain")
        self.assertEqual(self.component.meta.hName.asString(), "fkChain")
        self.assertEqual(self.component.definition.name, "fkChain")
        self.component.rename("newname")
        self.assertEqual(self.component.name(), "newname")
        self.assertEqual(self.component.meta.hName.value(), "newname")
        self.assertEqual(self.component.definition.name, "newname")
        # reset back to original
        self.component.rename("fkChain")

    def test_side(self):
        self.assertEqual(self.component.side(), "M")
        self.assertEqual(
            self.component.meta.attribute(api.constants.SIDE_ATTR).value(), "M"
        )
        self.assertEqual(self.component.definition.side, "M")
        self.component.setSide("L")
        self.assertEqual(self.component.side(), "L")
        self.assertEqual(
            self.component.meta.attribute(api.constants.SIDE_ATTR).value(), "L"
        )
        self.assertEqual(self.component.definition.side, "L")
        # reset back to original
        self.component.setSide("M")

    def test_createLayer(self):
        layerTypes = (
            api.HiveRigLayer,
            api.HiveGuideLayer,
            api.HiveDeformLayer,
            api.HiveInputLayer,
            api.HiveOutputLayer,
            api.HiveXGroupLayer,
            api.HiveComponentLayer,
            api.HiveGeometryLayer,
        )
        for i, l in enumerate(api.constants.LAYER_TYPES):
            meta = self.component.meta
            layer = meta.createLayer(
                l, l + "_hrc", l + "_meta", parent=meta.rootTransform()
            )
            self.assertIsInstance(layer, layerTypes[i])
            self.assertTrue(layer.exists())
            self.assertTrue(layer.name(), l)

    def test_duplicate(self):
        newComp = self.component.duplicate("newComponent", "R")
        self.assertEqual(newComp.name(), "newComponent")
        self.assertEqual(newComp.side(), "R")
        self.assertTrue(newComp.exists())
        self.assertIsInstance(newComp, api.Component)

    def test_createSettingsPanel(self):
        attrName = api.constants.CONTROL_PANEL_TYPE
        name = self.component.namingConfiguration().resolve(
            "settingsName",
            {
                "componentName": self.component.name(),
                "side": self.component.side(),
                "section": api.constants.CONTROL_PANEL_TYPE,
                "type": "settings",
            },
        )
        meta = self.component.meta
        rigLayer = meta.createLayer(
            api.constants.RIG_LAYER_TYPE,
            api.constants.RIG_LAYER_TYPE + "_hrc",
            api.constants.RIG_LAYER_TYPE + "_meta",
            parent=meta.rootTransform(),
        )
        panel = rigLayer.createSettingsNode(name, attrName=attrName)
        self.assertIsInstance(panel, api.SettingsNode)
        self.assertIsInstance(self.component.controlPanel(), api.SettingsNode)
