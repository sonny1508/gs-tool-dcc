from zoo.libs.maya.utils import mayatestutils
from zoo.libs.hive import api


class TestNamingPresets(mayatestutils.BaseMayaTest):
    newSceneAfterTest = False

    def setUp(self):
        self.presetManager = api.namingpresets.PresetManager()
        hierarchy = self.presetManager.prefInterface.namingPresetHierarchy()
        self.presetManager.loadFromEnv(hierarchy)

    def test_allRulesHaveValidExampleFields(self):
        for n, config in self.presetManager.namingConfigs.items():
            for rule in config.rules(False):
                expressionFields = rule.fields()
                exampleFields = rule.exampleFields
                self.assertTrue(all(i in exampleFields for i in expressionFields),
                                "Missing exampleFields for rule {}".format(rule.name))

