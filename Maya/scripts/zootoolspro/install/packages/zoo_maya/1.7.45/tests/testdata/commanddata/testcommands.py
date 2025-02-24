from zoo.libs.maya.mayacommand import command


class TestCommandReg(command.ZooCommandMaya):
    id = "test.testCommand"
    isUndoable = False
    isEnabled = True

    def doIt(self, value="hello"):
        return value


class FailCommandArguments(command.ZooCommandMaya):
    id = "test.failCommandArguments"
    isUndoable = False
    isEnabled = True

    def doIt(self, value):
        pass


class TestCommandUndoable(command.ZooCommandMaya):
    id = "test.testCommandUndoable"
    isUndoable = True
    isEnabled = True
    value = ""

    def doIt(self, value="hello"):
        self.value = value
        return value

    def undoIt(self):
        self.value = ""


class TestCommandNotUndoable(command.ZooCommandMaya):
    id = "test.testCommandNotUndoable"
    isUndoable = False
    isEnabled = True
    value = ""

    def doIt(self, value="hello"):
        self.value = value
        return value

    def undoIt(self):
        self.value = ""
