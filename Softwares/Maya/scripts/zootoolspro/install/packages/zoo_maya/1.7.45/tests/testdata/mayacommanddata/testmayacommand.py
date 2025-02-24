from zoo.libs.maya.mayacommand import command

from zoo.libs.maya.api import nodes
from maya.api import OpenMaya as om2


class MayaSimpleCommand(command.ZooCommandMaya):
    id = "test.mayaSimpleCommand"
    isUndoable = True
    _testNode = None

    def doIt(self):
        return "hello world"

    def undoIt(self):
        return "undo"


class MayaNotUndoableCommand(command.ZooCommandMaya):
    id = "test.mayaNotUndoableCommand"
    isUndoable = False
    _testNode = None

    def doIt(self):
        return "hello world"

    def undoIt(self):
        return "undo"


class MayaTestCreateNodeCommand(command.ZooCommandMaya):
    id = "test.mayaTestCreateNodeCommand"
    isUndoable = True
    _modifier = None

    def doIt(self):
        if self._modifier is not None:
            # redo
            self._modifier.doIt()
        else:
            self._modifier = om2.MDagModifier()
            node = nodes.createDagNode("testNode", "transform", modifier=self._modifier, apply=True)
            return node

    def undoIt(self):
        self._modifier.undoIt()


class MayaTestCommandFailsOnDoIt(command.ZooCommandMaya):
    id = "test.mayaTestCommandFailsOnDoIt"
    _testNode = None
    isUndoable = False

    def doIt(self):
        raise ValueError("Failed")


class MayaTestCommandFailsOnUndoIt(command.ZooCommandMaya):
    id = "test.mayaTestCommandFailsOnUndoIt"
    _testNode = None
    isUndoable = True

    def doIt(self):
        node = nodes.createDagNode("testNode", "transform")
        self._testNode = om2.MObjectHandle(node)

    def undoIt(self):
        raise ValueError("Failed")


class MayaTestCommandFailsOnResolveArgs(command.ZooCommandMaya):
    id = "test.mayaTestCommandFailsOnResolveArgs"
    _testNode = None

    def doIt(self, test, test2=None):
        pass
