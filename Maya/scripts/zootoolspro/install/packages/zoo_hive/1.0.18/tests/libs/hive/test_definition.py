from zoo.libs.maya.utils import mayatestutils
from zoo.libs.hive.base.definition import spaceswitch
from zoo.libs.hive.base import definition
from zoo.libs.hive import constants
from zoo.libs.maya import zapi

_GUIDE_TEST_DATA = {
    "id": "root",
    "name": "root",
    "children": [{"id": "child", "name": "child"}]
}
_ATTR_TEST_DATA = {
    "channelBox": False,
    "default": 6,
    "isDynamic": True,
    "keyable": False,
    "locked": False,
    "max": 9999,
    "min": 3,
    "name": "testAttr",
    "softMax": None,
    "softMin": None,
    "Type": 2,
    "value": 6
}




class TestGuideLayerDefinition(mayatestutils.BaseMayaTest):
    newSceneAfterTest = False

    def setUp(self):
        self.definition = definition.GuideLayerDefinition()
        self.testData = {constants.DAG_DEF_KEY: [_GUIDE_TEST_DATA],
                         constants.SETTINGS_DEF_KEY: [_ATTR_TEST_DATA]}



    def test_updateGuides(self):
        self.definition.update(self.testData)
        # test guides were added
        self.assertTrue(self.definition.hasGuide("root"))
        self.assertTrue(self.definition.hasGuide("child"))
        self.assertIsInstance(self.definition.guide("child"), definition.GuideDefinition)

    def test_updateAttributes(self):
        self.definition.update(self.testData)
        # test attributes
        self.assertIsInstance(self.definition.guideSetting("testAttr"), definition.AttributeDefinition)

        attrUpdateData = dict(_ATTR_TEST_DATA)
        attrUpdateData["value"] = 100
        attrUpdateData["Type"] = zapi.attrtypes.kMFnNumericFloat
        attrUpdateData["default"] = "fail"

        newData = {constants.SETTINGS_DEF_KEY: [attrUpdateData]}
        self.definition.update(newData)
        # test flags only come from the base ie. the component base definition not the template/scene which overrides
        self.assertEqual(self.definition.guideSetting("testAttr").value, 100)
        self.assertNotEqual(self.definition.guideSetting("testAttr").default, "fail")
        self.assertNotEqual(self.definition.guideSetting("testAttr").Type, zapi.attrtypes.kMFnNumericFloat)

    def test_fromData(self):
        defini = definition.GuideLayerDefinition.fromData(self.testData)

        # ensure we've added the default attributes
        for defaultSetting in defini.defaultGuideSettings():
            self.assertTrue(defini.guideSetting(defaultSetting.name))


class TestSpaceSwitching(mayatestutils.BaseMayaTest):
    newSceneAfterTest = False

    def setUp(self):
        self.data = {
            "label": "ikSpace",
            "driven": "endik",
            "type": "parent",
            "permissions": {
                "value": True,
                "allowRename": True,
            },
            "drivers": [
                {
                    "label": "parent",
                    "driver": "@{self.inputLayer.upr}",
                    "component": "@{self}",
                },
                {
                    "label": "world",
                    "driver": "@{leg:L.rigLayer.uprik}",
                    "component": "@{self}",
                    "permissions": {"value": True, "allowRename": False},
                }
            ]
        }
        self.spaceDef = spaceswitch.SpaceSwitchDefinition(self.data)

    def test_isProtected(self):
        self.assertTrue(self.spaceDef.isProtected)
        self.spaceDef.isProtected = False
        self.assertFalse(self.spaceDef.isProtected)

    def test_rename(self):
        self.assertTrue(self.spaceDef.renameAllowed)

        self.spaceDef.renameAllowed = False
        self.assertFalse(self.spaceDef.renameAllowed)

    def test_driversOfCorrectType(self):
        for i in self.spaceDef.drivers:
            self.assertIsInstance(i, spaceswitch.SpaceSwitchDriverDefinition)

    def test_driverPermissions(self):
        permittedDriver, notPermittedDriver = self.spaceDef.drivers
        self.assertFalse(permittedDriver.isProtected)
        self.assertTrue(notPermittedDriver.isProtected)
        self.assertTrue(permittedDriver.renameAllowed)
        self.assertFalse(notPermittedDriver.renameAllowed)

    def test_serializationMaintainsNewOrdering(self):
        newData = {
            "label": "ikSpace",
            "driven": "endik",
            "type": "parent",
            "permissions": {
                "value": True,
                "allowRename": True,
            },
            "drivers": [
                {
                    "label": "world",
                    "driver": "@{ChangeTest}",
                    "component": "@{self.change}",
                    "permissions": {"value": True, "allowRename": False},
                },
                {
                    "label": "parent",
                    "driver": "@{change}",
                    "component": "@{self}",
                }

            ]
        }

        data = spaceswitch.SpaceSwitchDefinition(newData)
        serializedData = data.difference(self.spaceDef)
        diff = spaceswitch.SpaceSwitchDefinition(serializedData)

        # repeat previous test to ensure we also maintain the drivers
        self.assertEqual(len(diff.drivers), 2)
        self.assertIsNotNone(diff.driver("parent"))
        self.assertIsNotNone(diff.driver("world"))
        # case where there's no difference at all
        self.assertEqual(self.spaceDef.difference(self.spaceDef), {},
                         "Serializing the identical structure doesn't result in and empty structure")
        # when an ordering difference is calculated we only keep the label and merging original and new will combine.
        self.assertEqual(diff.drivers[0].label, "world", "Ordering isn't maintained")
        self.assertEqual(diff.drivers[1].label, "parent", "Ordering isn't maintained")
        self.assertEqual(len(diff.drivers[0].keys()), 1, "Number of keys kept during ordering difference isn't 1")
