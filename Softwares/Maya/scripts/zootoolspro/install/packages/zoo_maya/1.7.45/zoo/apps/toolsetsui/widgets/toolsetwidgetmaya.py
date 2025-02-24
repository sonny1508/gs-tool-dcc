import contextlib

from maya import cmds
from zoo.apps.toolsetsui.toolsetcallbacks import SelectionCallbacksMaya
from zoo.apps.toolsetsui.widgets.toolsetwidget import ToolsetWidgetBase
from zoo.libs.maya.cmds.general import undodecorator

undoDecorator = undodecorator.undoDecorator


@contextlib.contextmanager
def blockToolsetCallbacksContext(widget):
    try:
        widget.blockCallbacks(True)
        yield
    finally:
        widget.blockCallbacks(False)


class ToolsetWidgetMaya(ToolsetWidgetBase):
    """ Maya specific code for toolset widgets

    """

    def __init__(self, *args, **kwargs):
        super(ToolsetWidgetMaya, self).__init__(*args, **kwargs)
        self.selectionCallbacks = SelectionCallbacksMaya()

    def updateFromProperties(self):
        """ Fill in the widgets based on the properties.  Will affect widgets linked in the toolset UI via:

        For Maya block callbacks as well

        :return:
        :rtype:
        """
        with blockToolsetCallbacksContext(self):
            super(ToolsetWidgetMaya, self).updateFromProperties()

    @staticmethod
    def undoDecorator(func):
        """ Allows all cmds,mel commands perform by the  the wrapped `func` into
        a single undo operation

        @undoDecorator
        def myoperationFunc():
            pass
        """

        import functools
        @functools.wraps(func)
        def inner(*args, **kwargs):
            try:
                cmds.undoInfo(openChunk=True, chunkName=func.__name__)
                return func(*args, **kwargs)
            finally:
                cmds.undoInfo(closeChunk=True)

        return inner

    def stopCallbacks(self):
        """ Stop all callbacks

        :return:
        :rtype:
        """
        self.stopSelectionCallback()

    def blockCallbacks(self, block):
        self.selectionCallbacks.blockCallbacks(block)

    def startSelectionCallback(self):
        self.selectionCallbacks.startSelectionCallback()

    def stopSelectionCallback(self):
        self.selectionCallbacks.stopSelectionCallback()

    # ------------------------------------
    # UNDO CHUNKS
    # ------------------------------------
    def openUndoChunk(self, name=None):
        """Opens the Maya undo chunk"""
        name = self.id or name
        undodecorator.openUndoChunk(name)

    def closeUndoChunk(self, name=None):
        """Opens the Maya undo chunk"""
        name = self.id or name
        undodecorator.closeUndoChunk(name)

    def connections(self):
        """ Stop callbacks

        :return:
        :rtype:
        """
        super(ToolsetWidgetMaya, self).connections()
        self.deletePressed.connect(self.stopCallbacks)
