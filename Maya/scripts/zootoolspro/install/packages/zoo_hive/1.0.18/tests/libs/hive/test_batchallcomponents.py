from zoo.libs.hive import api
from zoo.libs.maya import zapi
from zoo.libs.maya.utils import mayatestutils
from maya.api import OpenMaya as om2


class TestFkComponent(mayatestutils.BaseMayaTest):
    """Test a basic fk component build so we can test all other query methods"""

    keepPluginsLoaded = True
    newSceneAfterTest = True

    @classmethod
    def setUpClass(cls):
        super(TestFkComponent, cls).setUpClass()

    def setUp(self):
        cfg = api.Configuration()
        cfg.blackBox = True
        self.rig = api.Rig(cfg)
        self.rig.startSession("TestRig")
        self.component = self.rig.createComponent("fkchain", "testfk", "M")

    def test_buildGuide(self):
        self.rig.buildGuides([self.component])
        self.assertTrue(self.component.buildGuide())
        self.assertTrue(self.component.hasGuide())
        self.assertFalse(self.component.hasRig())
        self.assertIsInstance(self.component.guideLayer(), api.HiveGuideLayer)
        self.assertIsInstance(self.component.container(), api.ContainerAsset)
        self.assertEqual(
            self.component.container().blackBox, self.rig.configuration.blackBox
        )

    def test_buildRigWithGuide(self):
        self.rig.buildGuides([self.component])
        self.assertFalse(self.component.hasRig())
        self.rig.buildRigs([self.component])
        self.assertIsInstance(self.component.rigLayer(), api.HiveRigLayer)
        self.assertIsInstance(self.component.inputLayer(), api.HiveInputLayer)
        self.assertIsInstance(self.component.outputLayer(), api.HiveOutputLayer)
        self.assertIsInstance(self.component.deformLayer(), api.HiveDeformLayer)
        self.assertTrue(self.component.hasRig())

    def test_parent(self):
        newComponent = self.rig.createComponent("fkchain", "testcomp", "M")
        self.rig.buildGuides([self.component, newComponent])
        self.assertIsNone(self.component.parent())
        self.component.setParent(newComponent)
        self.assertIsNotNone(self.component.parent())
        self.assertIsInstance(self.component.parent(), api.Component)

    def test_deserialize(self):
        self.rig.buildGuides([self.component])
        deff = self.component.serializeFromScene()
        self.rig.deleteComponent(self.component.name(), self.component.side())
        self.rig.createComponent(definition=deff)

    def test_deleteGuide(self):
        self.rig.buildGuides([self.component])
        self.assertTrue(self.component.deleteGuide())
        self.assertIsNone(self.component.guideLayer())

    def test_deleteRig(self):
        self.rig.buildGuides([self.component])
        self.rig.buildRigs([self.component])
        self.assertTrue(self.rig.deleteRigs())
        for i in (self.component.rigLayer(),):
            self.assertIsNone(i)

    def test_delete(self):
        self.rig.buildGuides([self.component])
        self.rig.buildRigs([self.component])
        self.rig.deleteComponent(self.component.name(), self.component.side())
        self.component.rootTransform()
        self.assertFalse(self.component.exists())

    def test_polish(self):
        self.rig.buildGuides([self.component])
        self.rig.buildRigs([self.component])
        self.rig.polish()
        self.assertIsNone(self.component.guideLayer())
        self.assertIsNone(self.component.container())

    def test_polishWithContainers(self):
        self.rig.configuration.useContainers = True
        self.rig.buildGuides([self.component])
        self.rig.buildRigs([self.component])
        self.rig.polish()
        self.assertIsNone(self.component.guideLayer())
        self.assertIsNotNone(self.component.container())
        self.assertTrue(
            self.component.container().blackBox, self.rig.configuration.blackBox
        )


def _testTwistsCountForComponent(test, comp, twistSettingNames, twistSegmentIdPrefix):
    countSettings = comp.definition.guideLayer.guideSettings(*twistSettingNames)
    twists = {}
    guides = {guide.id(): guide for guide in comp.guideLayer().iterGuides()}
    for settingName, segmentPrefix in zip(twistSettingNames, twistSegmentIdPrefix):
        for guideId, guide in guides.items():
            if guideId.startswith(segmentPrefix) and "TwistOffset" not in guideId:
                twists.setdefault(settingName, []).append(guide)
    for settingName, segmentGuides in twists.items():
        count = countSettings[settingName].value
        test.assertTrue(
            count == len(segmentGuides),
            "UprTwists do not much settings: Scene Count: {}, setting: {}".format(
                len(segmentGuides), count
            ),
        )


class TestArmComponent(mayatestutils.BaseMayaTest):
    newSceneAfterTest = False
    newSceneAfterTearDownCls = True
    keepPluginsLoaded = True

    def setUp(self):
        self.rig = api.Rig()
        self.rig.startSession("hiveTest")

    def testBuild(self):
        comp = self.rig.createComponent("armcomponent", "arm", "L")
        self.rig.buildGuides([comp])
        _testTwistsCountForComponent(
            self,
            comp,
            ["uprSegmentCount", "lwrSegmentCount"],
            twistSegmentIdPrefix=["uprTwist", "lwrTwist"],
        )
        api.commands.updateGuideSettings(
            comp, {"uprSegmentCount": 4, "lwrSegmentCount": 3}
        )
        _testTwistsCountForComponent(
            self,
            comp,
            ["uprSegmentCount", "lwrSegmentCount"],
            twistSegmentIdPrefix=["uprTwist", "lwrTwist"],
        )
        self.rig.buildDeform([comp])
        self.rig.buildRigs([comp])
        self.rig.polish()


class TestLegComponent(mayatestutils.BaseMayaTest):
    newSceneAfterTest = False
    newSceneAfterTearDownCls = True
    keepPluginsLoaded = True

    def setUp(self):
        self.rig = api.Rig()
        self.rig.startSession("hiveTest")

    def testBuild(self):
        comp = self.rig.createComponent("legcomponent", "arm", "L")
        self.rig.buildGuides([comp])
        _testTwistsCountForComponent(
            self,
            comp,
            ["uprSegmentCount", "lwrSegmentCount"],
            twistSegmentIdPrefix=["uprTwist", "lwrTwist"],
        )
        api.commands.updateGuideSettings(
            comp, {"uprSegmentCount": 4, "lwrSegmentCount": 3}
        )
        _testTwistsCountForComponent(
            self,
            comp,
            ["uprSegmentCount", "lwrSegmentCount"],
            twistSegmentIdPrefix=["uprTwist", "lwrTwist"],
        )
        self.rig.buildDeform([comp])
        self.rig.buildRigs([comp])
        self.rig.polish()


class TestQuadComponent(mayatestutils.BaseMayaTest):
    newSceneAfterTest = False
    newSceneAfterTearDownCls = True
    keepPluginsLoaded = True

    def setUp(self):
        self.rig = api.Rig()
        self.rig.startSession("hiveTest")

    def testBuild(self):
        comp = self.rig.createComponent("quadLeg", "quad", "L")
        self.rig.buildGuides([comp])
        _testTwistsCountForComponent(
            self,
            comp,
            ["uprSegmentCount", "lwrSegmentCount", "ankleSegmentCount"],
            twistSegmentIdPrefix=["uprTwist", "lwrTwist", "ankleTwist"],
        )
        # self._testTwistCounts(comp)
        api.commands.updateGuideSettings(
            comp, {"uprSegmentCount": 4, "lwrSegmentCount": 3, "ankleSegmentCount": 3}
        )
        # self._testTwistCounts(comp)
        _testTwistsCountForComponent(
            self,
            comp,
            ["uprSegmentCount", "lwrSegmentCount", "ankleSegmentCount"],
            twistSegmentIdPrefix=["uprTwist", "lwrTwist", "ankleTwist"],
        )
        self.rig.buildDeform([comp])
        self.rig.buildRigs([comp])
        self.rig.polish()


class TestComponentAll(mayatestutils.BaseMayaTest):
    newSceneAfterTest = True
    keepPluginsLoaded = True
    # ignore because these are manually tested
    ignoredComponents = ["armComponent", "legComponent", "quadLeg", "fkchain"]

    def setUp(self):
        self.rig = api.Rig()
        self.rig.startSession("hiveTest")

    def test_buildAllComponentGuides(self):
        comps = self.rig.configuration.componentRegistry().components
        for n, data in comps.items():
            self.rig.createComponent(n, n, "M")
        self.rig.buildGuides()
        for comp in self.rig.components():
            self.assertIsInstance(comp.meta, api.HiveComponent)
            self.assertIsInstance(comp.guideLayer(), api.HiveGuideLayer)

    def test_buildAllComponentRigs(self):
        comps = self.rig.configuration.componentRegistry().components
        for n, data in comps.items():
            self.rig.createComponent(n, n, "M")
        self.rig.buildGuides()
        self.rig.buildDeform()
        self.rig.buildRigs()

        for comp in self.rig.components():
            rigLayer = comp.rigLayer()
            self.assertIsInstance(rigLayer, api.HiveRigLayer)
            self.assertIsInstance(comp.deformLayer(), api.HiveDeformLayer)
            self.assertIsInstance(comp.inputLayer(), api.HiveInputLayer)
            self.assertIsInstance(comp.outputLayer(), api.HiveOutputLayer)
            # now test to make sure that if we have a controlPanel
            # that all anim attributes from the panel is published on the container
            # or as a proxy on each control

            container = comp.container()
            publishNames = [
                i.partialName(
                    includeNonMandatoryIndices=True,
                    useLongNames=False,
                    includeInstancedIndices=True,
                )
                for i in container.publishedAttributes()
            ]
        self.rig.polish()
        for comp in self.rig.components():
            rigLayer = comp.rigLayer()
            animsettings = comp.definition.rigLayer.settings.get(api.constants.CONTROL_PANEL_TYPE, [])
            if not animsettings:
                continue
            controlPanel = rigLayer.settingNode(api.constants.CONTROL_PANEL_TYPE)
            if controlPanel is None:
                continue
            controls = rigLayer.iterControls()
            for animSetting in animsettings:
                # make sure the settings exist
                #todo: check value, default, min/max etc
                self.assertTrue(controlPanel.hasAttribute(animSetting["name"]))
                if self.rig.configuration.useProxyAttributes:
                    for ctrl in controls:
                        self.assertTrue(ctrl.hasAttribute(animSetting["name"]))
                elif (
                    not self.rig.configuration.useProxyAttributes
                    and self.rig.configuration.useContainers
                ):
                    self.assertTrue(animSetting["name"] in publishNames)
