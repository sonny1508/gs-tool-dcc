import os
from basetest import BaseTest


class TestZooVersion(BaseTest):
    def setUp(self):
        from zoo.core import api
        from zoo.core.util import version
        self.versionModule = version
        self.api = api
        self.zooConfig = api.zooFromPath(os.environ["ZOOTOOLS_ROOT"])

    def test_incrementMajorVersion(self):
        versionStr = "0.9.0"
        newVersion = self.versionModule.incrementVersion(versionStr, self.versionModule.MAJOR_VERSION)
        self.assertEqual(newVersion, "1.0.0")

    def test_incrementMajorVersionWithShortVersionString(self):
        versionStr = "0.10"
        newVersion = self.versionModule.incrementVersion(versionStr, self.versionModule.MAJOR_VERSION)
        self.assertEqual(newVersion, "1.0")

    def test_incrementMinorVersion(self):
        versionStr = "0.9.0"
        newVersion = self.versionModule.incrementVersion(versionStr, self.versionModule.MINOR_VERSION)
        self.assertEqual(newVersion, "0.10.0")

    def test_incrementMinorVersionWithShortVersionString(self):
        versionStr = "0.10"
        newVersion = self.versionModule.incrementVersion(versionStr, self.versionModule.MINOR_VERSION)
        self.assertEqual(newVersion, "0.11")

    def test_incrementPatchVersion(self):
        versionStr = "0.9.0"
        newVersion = self.versionModule.incrementVersion(versionStr, self.versionModule.PATCH_VERSION)
        self.assertEqual(newVersion, "0.9.1")

    def test_incrementPatchVersionWithAlphaBeta(self):
        versionStr = "0.9.0dev15"
        newVersion = self.versionModule.incrementVersion(versionStr, self.versionModule.PATCH_VERSION)
        self.assertEqual(newVersion, "0.9.1")

    def test_incrementAlphaBetaVersion(self):
        versionStr = "0.9.0dev15"
        newVersion = self.versionModule.incrementVersion(versionStr, self.versionModule.ALPHABETA_VERSION)
        self.assertEqual(newVersion, "0.9.0dev16")
