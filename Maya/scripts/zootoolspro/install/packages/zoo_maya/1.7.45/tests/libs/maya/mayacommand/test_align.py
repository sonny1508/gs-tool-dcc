from zoo.libs.maya import meta, zapi
from zoo.libs.maya.utils import mayatestutils, mayamath

from zoo.libs.commands import maya
from zoo.libs.maya.meta import base as meta


class TestCoPlanar(mayatestutils.BaseMayaTest):
    def test_create(self):
        n = maya.coPlanarAlign(create=True, align=False)
        self.assertIsInstance(n, meta.MetaBase)
        n.delete()

    def test_align(self):
        n = maya.coPlanarAlign(create=True, align=False)
        result = maya.coPlanarAlign(create=False, align=True, metaNode=n)
        self.assertFalse(result)  # when no nodes are attached to the metaNode

        startNode = zapi.createDag("startNode", "transform")
        midNode = zapi.createDag("midNode", "transform", parent=startNode)
        endNode = zapi.createDag("endNode", "transform", parent=midNode)
        midNode.setTranslation((5.0, 1.0, 1.0))
        endNode.setTranslation((10.0, 0.0, 1.0))
        n.setStartNode(startNode)
        n.setEndNode(endNode)
        self.assertTrue(maya.coPlanarAlign(create=False, align=True, metaNode=n))
        n.delete()

    def test_wrongArguments(self):
        with self.assertRaises(ValueError):
            maya.coPlanarAlign(create=False, align=False)
        with self.assertRaises(ValueError):
            maya.coPlanarAlign(create=False, align=True, metaNode=None)


class TestNodeOrient(mayatestutils.BaseMayaTest):

    def test_align(self):
        startNode = zapi.createDag("startNode", "joint")
        midNode = zapi.createDag("midNode", "joint", parent=startNode)
        endNode = zapi.createDag("endNode", "joint", parent=midNode)
        midNode.setTranslation((5.0, 1.0, 1.0))
        endNode.setTranslation((10.0, 0.0, 1.0))
        self.assertTrue(maya.orientNodes([startNode, midNode, endNode],
                                         mayamath.XAXIS_VECTOR,
                                         mayamath.YAXIS_VECTOR,
                                         None),
                        "Failed to orient 3 joints in a chain")
        self.assertTrue(maya.orientNodes([startNode, midNode],
                                         mayamath.XAXIS_VECTOR,
                                         mayamath.YAXIS_VECTOR,
                                         None, skipEnd=False),
                        "Failed to orient 2 joints in a chain")
        self.assertTrue(maya.orientNodes([midNode, startNode],
                                         mayamath.XAXIS_VECTOR,
                                         mayamath.YAXIS_VECTOR,
                                         None, skipEnd=False),
                        "Failed to orient 2 joints in reverse order")
