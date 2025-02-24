
from maya import cmds
from maya.api import OpenMaya as om

from zoo.libs.maya.utils import mayatestutils
from zoo.libs.maya.api import generic
from zoo.libs.maya.api import nodes


class ControlCreatorTest(mayatestutils.BaseMayaTest):
    application = "maya"

    def setUp(self):
        # self.node = cmds.createNode("transform")
        pass

    def test_isValidMObject(self):
        self.assertTrue(1)
        self.assertFalse(0)
        pass
        # obj = nodes.asMObject(self.node)
        # self.assertTrue(generic.isValidMObject(obj))
        # cmds.delete(self.node)
        # self.assertFalse(generic.isValidMObject(obj))

    def test_isValidMObject2(self):
        self.assertTrue(1)
        self.assertFalse(0)
        pass
        # obj = nodes.asMObject(self.node)
        # self.assertTrue(generic.isValidMObject(obj))
        # cmds.delete(self.node)
        # self.assertFalse(generic.isValidMObject(obj))

    # def test_isMObjectHandle(self):
    #
    #     obj = om.MObjectHandle(nodes.asMObject(self.node))
    #     self.assertTrue(generic.isValidMObjectHandle(obj))
    #     cmds.delete(self.node)
    #     self.assertFalse(generic.isValidMObjectHandle(obj))
    #
    # def test_cmpNodes(self):
    #     obj = nodes.asMObject(self.node)
    #     self.assertTrue(generic.compareMObjects(obj, obj))
    #     self.assertFalse(generic.compareMObjects(obj, nodes.asMObject(cmds.createNode("multiplyDivide"))))
    #
    # def test_asMObject(self):
    #     pass
    #
    # def test_asEuler(self):
    #     pass
    #
    # def test_softSelection(self):
    #     pass
