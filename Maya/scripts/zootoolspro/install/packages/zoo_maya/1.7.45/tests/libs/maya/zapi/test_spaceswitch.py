from zoo.libs.maya import zapi
from zoo.libs.maya.utils import mayatestutils
from zoo.core.util import zlogging

logger = zlogging.getLogger(__name__)


class TestSpaceSwitch(mayatestutils.BaseMayaTest):
    newSceneAfterTest = False
    _nodes = {"drivers": [],  # type: tuple[str, zapi.DagNode]
              "control": None,  # type: zapi.DagNode or None
              "driven": None  # type: zapi.DagNode  or None
              }

    @classmethod
    def setUpClass(cls):
        super(TestSpaceSwitch, cls).setUpClass()

        targets = []
        for n in ("locator1", "locator2", "locator3"):
            targets.append((n, zapi.createDag(n, "locator")))
        cls._nodes["drivers"] = targets
        cls._nodes["control"] = zapi.createDag("control", "locator")
        cls._nodes["driven"] = zapi.createDag("driven", "locator")

    def test_spaceCreationCreation(self):

        drivenNode = self._nodes["driven"]
        ctrl = self._nodes["control"]
        targets = self._nodes["drivers"]
        spaces = {"spaceNode": self._nodes["control"],
                  "attributeName": "parentSpace", "targets": targets}
        constraint, _ = zapi.buildConstraint(drivenNode, drivers=spaces)
        self.assertIsNotNone(constraint)
        self.assertEqual(constraint.id, "parent")
        ctrlAttribute = ctrl.attribute("parentSpace")
        self.assertIsNotNone(ctrlAttribute)
        self.assertEqual(ctrlAttribute.enumFields(), [i for i, _ in targets])

        self.assertEqual(constraint.driven(), drivenNode)
        self.assertEqual(constraint.controllerAttrName(), "parentSpace")
        self.assertEqual(constraint.controller()["node"], ctrl)
        self.assertEqual(list(constraint.drivers()), targets)
