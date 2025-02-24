import logging
from collections import OrderedDict

from zoo.core.tooldata import tooldata
from zoo.libs.utils import unittestBase


logger = logging.getLogger(__name__)


class TestToolData(unittestBase.BaseUnitest):
    @classmethod
    def setUpClass(cls):
        super(TestToolData, cls).setUpClass()
        cls.rootOne = cls.mkdtemp()
        cls.rootTwo = cls.mkdtemp()
        cls.rootThree = cls.mkdtemp()

    def setUp(self):
        self.toolset = tooldata.ToolSet()
        self.roots = OrderedDict({"internal": self.rootOne,
                                  "user": self.rootTwo,
                                  "network": self.rootThree})
        self.workspaceSetting = "prefs/hotkeys/workspace1"
        self.shaderEditorSetting = "prefs/tools/shaderEditor/uiState.json"

    def _bindRoots(self):
        for name, root in self.roots.items():
            self.toolset.addRoot(root, name)

    def test_addRoots(self):
        self._bindRoots()
        self.assertEqual(len(self.toolset.roots.keys()), 3)

        # check to make sure order is kept
        for i in range(len(self.roots.keys())):
            testRoot = self.roots[list(self.roots.keys())[i]]
            self.assertTrue(self.toolset.roots[list(self.toolset.roots.keys())[i]], testRoot)
        with self.assertRaises(tooldata.RootAlreadyExistsError):
            self.toolset.addRoot(self.toolset.root("internal"), "internal")

    def test_createSetting(self):
        self.toolset.addRoot(self.roots["user"], "user")
        toolsSetting = self.toolset.createSetting(self.workspaceSetting, root="user",
                                                  data={"testdata": {"bob": "hello"}})
        self.assertEqual(self.toolset.rootNameForPath(toolsSetting.rootPath()), "user")
        toolsSetting.save()
        self.assertTrue(toolsSetting.isValid(), msg="Path doesn't exist: {}".format(toolsSetting.path()))
        self.assertTrue(self.toolset.findSetting(self.workspaceSetting, root="user").isValid())
        newSettings = self.toolset.open(toolsSetting.root, toolsSetting.relativePath)
        self.assertEqual(newSettings["relativePath"], toolsSetting["relativePath"])
        self.assertEqual(newSettings["root"], toolsSetting["root"])
        self.assertEqual(newSettings["testdata"], {"bob": "hello"})
