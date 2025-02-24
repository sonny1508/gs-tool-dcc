import os

from basetest import BaseTest


class TestZooConfig(BaseTest):
    def setUp(self):
        from zoo.core import api
        self.api = api
        self.zooConfig = api.zooFromPath(os.environ["ZOOTOOLS_ROOT"])

    def testCreatePackage(self):
        outputDir = self._testFolder
        packagePath = os.path.join(outputDir, "testPackage")
        args = ["--destination", packagePath, "--name", "myPackage", "--author", "sparrow", "--displayName",
                "my Package"]
        self.zooConfig.runCommand("createPackage",
                                  arguments=args)
        self.assertTrue(os.path.exists(packagePath))
        self.assertTrue(os.path.exists(os.path.join(packagePath, "zoo_package.json")))
        self.zooConfig.runCommand("uninstallPackage",
                                  ["--name", "myPackage", "--remove"])
        self.assertFalse(os.path.exists(packagePath))
