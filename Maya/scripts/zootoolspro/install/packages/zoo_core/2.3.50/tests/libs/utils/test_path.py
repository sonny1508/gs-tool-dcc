import os
import logging

from zoo.libs.utils import unittestBase, path


logger = logging.getLogger(__name__)


class TestPathing(unittestBase.BaseUnitest):
    def test_withExtension(self):
        noExt = os.path.expanduser("~/test_noExtension")
        withExt = os.path.expanduser("~/test_noExtension.json")
        sameExt = os.path.expanduser("~/test_noExtension.config")
        self.assertTrue(path.withExtension(noExt, "config").endswith(".config"))
        self.assertTrue(path.withExtension(withExt, "config").endswith(".config"))
        self.assertTrue(path.withExtension(sameExt, "config").endswith(".config"))
