import os
from zoo.libs.naming import naming
from zoo.libs.utils import unittestBase


class TestNamingRules(unittestBase.BaseUnitest):

    def setUp(self):
        testDataPath = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..",
                                                    "testdata", "namingdata", "config.json"
                                                    )
                                       )
        self.namingObj = naming.NameManager.fromPath(configPath=testDataPath)

    def test_hasRules(self):
        self.assertTrue(len(list(self.namingObj.rules())) > 0)
        self.namingObj.clearRules()
        self.assertTrue(len(list(self.namingObj.rules())) == 0)

    #
    def test_findRuleByName(self):
        self.assertIsNotNone(self.namingObj.rule("object"))
        self.assertIsNone(self.namingObj.rule("myNonExistentRule"))

    #
    def test_ruleFromExpression(self):
        rule = self.namingObj.ruleFromExpression("{area}_{side}_{type}")
        self.assertIsNotNone(rule)
        self.assertEqual(rule, self.namingObj.rule("organisationNodes"))
        self.assertIsNone(self.namingObj.rule("{test}"))

    def test_resolve(self):
        # self.namingObj.setActiveRule("object")
        # {area}_{section}_{system}_{side}_{type}
        resolvedName = self.namingObj.resolve("organisationNodes", {"area": "head", "side": "L", "type": "joint"})
        self.assertEqual(resolvedName, "head_l_jnt", "Unable to resolve with user fields!")

    # def test_resolveWithCounter(self):
    #     pass

    def test_expressionFromString(self):
        self.assertEqual(self.namingObj.expressionFromString("null_index_skin_m_transform"),
                         "{area}_{section}_{system}_{side}_{type}")


#
#
class TestNamingFields(unittestBase.BaseUnitest):
    def setUp(self):
        testDataPath = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..",
                                                    "testdata", "namingdata", "config.json"
                                                    )
                                       )
        self.namingObj = naming.NameManager.fromPath(configPath=testDataPath)

    def test_addField(self):
        field = self.namingObj.addField("myToken", fields={"upr": "shldr"})
        self.assertTrue(self.namingObj.hasField("myToken"))
        self.assertEqual(field.valueForKey("upr"), "shldr")
        # test to ensure the data we added exists
        self.assertEqual(len(field), 1)

    def test_fieldValueForKey(self):
        self.assertEqual(self.namingObj.field("area").valueForKey("arm"), "arm")
        self.assertIsNone(self.namingObj.field("area").valueForKey("random"))
        self.assertEqual(self.namingObj.field("area").valueForKey("random", "defaultValue"), "defaultValue")

    def test_addTokenKeyValue(self):
        self.namingObj.addField("myToken", fields={"upr": "shldr"})
        self.assertTrue(self.namingObj.field("myToken").add("test", "tst"))
        self.assertTrue(self.namingObj.field("myToken").hasKey("test"))
        self.assertEqual(self.namingObj.field("myToken").valueForKey("test"), "tst")

    def updateTokenKeyValue(self):
        field = self.namingObj.addField("myToken", fields={"upr": "shldr"})
        field.tokenKeyValueForKey("upr").value = "hello"
        self.assertEqual(field.keyValue("upr").value, "hello")


class TestParentNamingRules(unittestBase.BaseUnitest):
    """Tests parent child hierarchy for rules ensuring only read based operations grab read from parent
    and edit based only modify child.
    """

    def setUp(self):
        childPath = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..",
                                                 "testdata", "namingdata", "config.json"
                                                 )
                                    )
        parentPath = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..",
                                                  "testdata", "namingdata", "parentconfig.json"
                                                  )
                                     )
        self.parentConfig = naming.NameManager.fromPath(configPath=parentPath)
        self.namingObj = naming.NameManager.fromPath(configPath=childPath)
        self.namingObj.parentConfig = self.parentConfig

    def test_parentHasRules(self):
        self.assertTrue(len(list(self.namingObj.rules())) > 0)
        self.namingObj.clearRules()
        self.assertTrue(len(list(self.namingObj.rules())) == 2)  # sees the parent rules

    def test_findParentRuleByName(self):
        self.assertIsNotNone(self.namingObj.rule("parentRule"))
        self.assertIsNotNone(self.namingObj.rule("organisationNodes"))
        self.assertIsNone(self.namingObj.rule("myNonExistentRule"))

    def test_parentRuleFromExpression(self):
        rule = self.namingObj.ruleFromExpression("{area}_{side}_{type}_{tokenA}")
        self.assertIsNotNone(rule)
        self.assertEqual(rule.name, "parentRule")
        self.assertIsNone(self.namingObj.rule("{test}"))

    def test_parentResolve(self):
        #  "{area}_{side}_{type}_{tokenA}"
        self.assertEqual(self.namingObj.resolve("parentRule", fields={"area": "null",
                                                                      "side": "M",
                                                                      "type": "transform",
                                                                      "tokenA": "parent"}),
                         "null_m_srt_parentA")

    def test_parentExpressionFromString(self):
        expression = self.namingObj.expressionFromString("null_index_skin_m_transform")
        self.assertEqual(expression, "{area}_{section}_{system}_{side}_{type}")
        self.assertEqual(self.namingObj.ruleFromExpression(expression).name,"object")
