from zoo.apps.chatgptui import basecontroller
from zoo.libs.utils import output, execution
from zoo.libs.maya.utils import general


class MayaController(basecontroller.Controller):
    """Overridden to handle executing code in maya as an undo block.
    """
    id = "mayaController"

    def __init__(self, parent):
        super(MayaController, self).__init__(parent)

    def executeCode(self, text):
        with general.undoContext("ChatGpt"):
            executionResult = execution.execute(text, self._executionLocals, self._executionLocals)
        if executionResult["reason"] == "errored":
            output.displayError(executionResult["traceback"])
