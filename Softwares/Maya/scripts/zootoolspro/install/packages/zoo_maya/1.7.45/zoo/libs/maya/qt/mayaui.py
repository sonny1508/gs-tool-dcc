import sys

from zoovendor.Qt import QtWidgets, QtCore, QtGui
from zoovendor.Qt.QtCompat import wrapInstance

from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
import maya.OpenMayaUI as apiUI
from maya import cmds, mel

if sys.version_info > (3,):
    long = int


def dpiScale(value):
    """Get the appropriate QSize based on maya's current dpi setting

    :param value:
    :type value: int or float
    :return:
    :rtype: int
    """
    return apiUI.MQtUtil.dpiScale(value)


def sizeByDpi(size):
    """Scales the QSize by the current dpi scaling from maya.

    :param size: The QSize to Scale by the dpi setting from maya
    :type size: QSize
    :return: The newly scaled QSize
    :rtype: QSize
    """
    return QtCore.QSize(dpiScale(size.width()), dpiScale(size.height()))


def mayaWindow():
    """
    :return: instance, the mainWindow ptr as a QMainWindow widget.
    :rtype: :class:`QtWidgets.QMainWindow`
    """
    ptr = apiUI.MQtUtil.mainWindow()
    if ptr is not None:
        return wrapInstance(long(ptr), QtWidgets.QMainWindow)


getMayaWindow = mayaWindow


def mayaViewport():
    """Returns the currently active maya viewport as a widget
    :return:
    :rtype:
    """
    widget = apiUI.M3dView.active3dView().widget()
    widget = wrapInstance(long(widget), QtWidgets.QWidget)
    return widget


def fullName(widget):
    return apiUI.MQtUtil.fullName(long(widget))


def getMayaWindowName():
    """Returns the maya window objectName from Qt
    :return:
    """
    return getMayaWindow().objectName()


def toQtObject(mayaName, widgetType=QtWidgets.QWidget):
    """Convert a Maya ui path to a Qt object.

    :param mayaName: Maya UI Path to convert eg. "scriptEditorPanel1Window|TearOffPane|scriptEditorPanel1|testButton"
    :return: PyQt representation of that object
    :rtype: QtWidgets.QWidget
    """
    ptr = apiUI.MQtUtil.findControl(mayaName)
    if ptr is None:
        ptr = apiUI.MQtUtil.findLayout(mayaName)
    if ptr is None:
        ptr = apiUI.MQtUtil.findMenuItem(mayaName)
    if ptr is None:
        ptr = apiUI.MQtUtil.findMenuItem(mayaName)
    if ptr is not None:
        return wrapInstance(long(ptr), widgetType)


def outlinerPaths():
    return cmds.getPanel(typ="outlinerPanel")


def getOutliners():
    return [toQtObject(i) for i in outlinerPaths()]


def openGraphEditor():
    cmds.GraphEditor()

def refreshOutliners():
    """Refreshes all outliner panels in maya"""
    for i in cmds.getPanel(typ="outlinerPanel"):
        cmds.outlinerEditor(i, edit=True, refresh=True)

def statusLineLayout():
    """Returns the maya status line as a QLayout

    :rtype: :class:`QtWidgets.QLayout`
    """
    layout = mel.eval("string $myVar=$gStatusLine")

    w = toQtObject(layout.rpartition("|")[0], QtWidgets.QLayout)
    # if we don't walk up one widget "formLayout4" then search for flowLayout1 then adding widgets doesn't
    # append to the correct layout but starts from the beginning again, no idea while.
    return w.findChild(QtWidgets.QLayout, "flowLayout1")


def applyScriptEditorHistorySyntax(sourceType, highlighter=None, **kwargs):
    se_edit, seRepo = highlighterEditorWidget(sourceType, **kwargs)
    se_edit.setVisible(False)
    if highlighter is None:
        highlighter = se_edit.findChild(QtGui.QSyntaxHighlighter)
    highlighter.setDocument(seRepo.document())


def highlighterEditorWidget(sourceType, **kwargs):
    se_repo = toQtObject('cmdScrollFieldReporter1', widgetType=QtWidgets.QTextEdit)
    tmp = cmds.cmdScrollFieldExecuter(sourceType=sourceType, **kwargs)
    se_edit = toQtObject(tmp, widgetType=QtWidgets.QTextEdit)
    se_edit.nativeParentWidget()
    return se_edit, se_repo


def suppressOutput():
    """Supresses all output to the script editor
    """
    cmds.scriptEditorInfo(e=True,
                          suppressResults=True,
                          suppressErrors=True,
                          suppressWarnings=True,
                          suppressInfo=True)


def restoreOutput():
    """Restores the script editor to include all results
    """
    cmds.scriptEditorInfo(e=True,
                          suppressResults=False,
                          suppressErrors=False,
                          suppressWarnings=False,
                          suppressInfo=False)


def setChannelBoxAtTop(channelBox, value):
    """
    :param channelBox: mainChannelBox
    :type channelBox: str
    :param value:
    :type value: bool

    .. code-block:: python

        setChannelBoxAtTop("mainChannelBox",True)
    """
    cmds.channelBox(channelBox, edit=True, containerAtTop=value)


def setChannelShowType(channelBox, value):
    """
    :param channelBox: mainChannelBox
    :type channelBox: str
    :param value:
    :type value: str

    .. code-block:: python

        setChannelShowType("mainChannelBox", "all")
    """
    cmds.optionVar(stringValue=("cbShowType", value))
    cmds.channelBox(channelBox, edit=True, update=True)


def activeModelEditor():
    """Get the model editor with focus.
    """
    panel = cmds.getPanel(withFocus=True)
    panelType = cmds.getPanel(typeOf=panel)
    if panelType != 'modelPanel':
        return ''
    return cmds.modelPanel(panel, modelEditor=True, query=True)


def modelEditors():
    """Returns all maya model editors
    """
    panels = cmds.getPanel(type='modelPanel')
    result = []
    for panel in panels:
        result.append(cmds.modelPanel(panel, query=True, modelEditor=True))
    return result


def disableColorManagement(editors=None):
    """Disables color management for modelEditors.

    :param editors: List of Model Editors to disable.
    :type editors: list of basestring
    :return: bool, True
    """
    if editors is None:
        editors = modelEditors()
    for editor in editors:
        setModelEditorColorManagement(editor, False)
    return True


def enableColorManagement(editors=None):
    """Disables color management for modelEditors.

    :param editors: List of Model Editors to disable.
    :type editors: list[str]
    :return: bool
    """
    if editors is None:
        editors = modelEditors()
    for editor in editors:
        setModelEditorColorManagement(editor, True)
    return True


def setModelEditorColorManagement(editor, value):
    cmds.modelEditor(editor, edit=True, cmEnabled=value)


# global to store the bootstrap maya widgets, {widgetuuid: :class:`BootStapWidget`}
# we use this to restore or close the bootstrap widgets
BOOT_STRAPPED_WIDGETS = {}


def rebuild(objectName):
    """If the bootstrap widget exists then we reapply it to mayas layout, otherwise do nothing.

    :param objectName: the bootStrap objectName
    :type objectName: str
    """
    global BOOT_STRAPPED_WIDGETS
    wid = BOOT_STRAPPED_WIDGETS.get(objectName)
    if wid is None:
        return False
    parent = apiUI.MQtUtil.getCurrentParent()
    mixinPtr = apiUI.MQtUtil.findControl(wid.objectName())
    apiUI.MQtUtil.addWidgetToMayaLayout(long(mixinPtr), long(parent))
    return True


def bootstrapDestroyWindow(objectName):
    """Function to destroy a bootstrapped widget, this use the maya workspaceControl objectName

    :param objectName: The bootstrap Widget objectName
    :type objectName: str
    :rtype: bool
    """
    global BOOT_STRAPPED_WIDGETS
    wid = BOOT_STRAPPED_WIDGETS.get(objectName)

    if wid is not None:
        # wid.close()
        BOOT_STRAPPED_WIDGETS.pop(objectName)
        wid.close()
        return True
    return False


class BootStrapWidget(MayaQWidgetDockableMixin, QtWidgets.QWidget):
    """ Class to wrap mayas workspace dockable mixin into something useful,

    .. code-block:: python

        customWidget = QtWidget()
        boostrap = BootStrapWidget(customWidget, "customWidget")
        boostrap.show(dockable=True, retain=False, width=size.width(), widthSizingProperty='preferred',
                     minWidth=minSize.width(),
                     height=size.height(), x=250, y=200)

    """
    width = cmds.optionVar(query='workspacesWidePanelInitialWidth') * 0.75
    INITIAL_SIZE = QtCore.QSize(width, 600)
    PREFERRED_SIZE = QtCore.QSize(width, 420)
    MINIMUM_SIZE = QtCore.QSize((width * 0.95), 220)

    def __del__(self, *args, **kwargs):
        """Overriding to do nothing due to autodesk's implemention causing an internal error (c++ object already deleted),
        since they try to destroy the workspace after its QObject has already been deleted , thanks guys!!!
        """
        pass

    def __init__(self, widget, title, uid=None, parent=None):

        # maya internals workouts the parent if None
        super(BootStrapWidget, self).__init__(parent=parent)
        # self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        self.preferredSize = self.PREFERRED_SIZE
        # bind this instance globally so the maya callback can talk to it
        global BOOT_STRAPPED_WIDGETS
        uid = uid or title
        self.setObjectName(uid)
        BOOT_STRAPPED_WIDGETS[uid] = self

        self.setWindowTitle(title)
        # create a QMainWindow frame that other windows can dock into.
        self.dockingFrame = QtWidgets.QMainWindow(self)
        self.dockingFrame.layout().setContentsMargins(0, 0, 0, 0)
        self.dockingFrame.setWindowFlags(QtCore.Qt.Widget)
        self.dockingFrame.setDockOptions(QtWidgets.QMainWindow.AnimatedDocks)

        self.centralWidget = widget
        self.dockingFrame.setCentralWidget(self.centralWidget)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.dockingFrame, 0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)
        widget.setProperty('bootstrapWidget', self)

    def setSizeHint(self, size):
        self.preferredSize = size

    def close(self, *args, **kwargs):
        """Overridden to call the bootstrap user widget.close()
        """
        self.centralWidget.close()
        super(BootStrapWidget, self).close(*args, **kwargs)

    def show(self, **kwargs):
        name = self.objectName()
        name = name + "WorkspaceControl"
        if cmds.workspaceControl(name, query=True, exists=True):
            cmds.deleteUI(name)
            cmds.workspaceControlState(name, remove=True)
        kwargs["retain"] = False
        # create the ui script which launches the custom widget, autodesk decided that string are god eeekkkkk!
        kwargs[
            "uiScript"] = 'try: import zoo.libs.maya.qt.mayaui as zoomayaui;zoomayaui.rebuild("{}")\nexcept ImportError: pass'.format(
            self.objectName())
        # create the close callback string autodesk wacky design decisions again
        kwargs[
            "closeCallback"] = 'try: import zoo.libs.maya.qt.mayaui as zoomayaui;zoomayaui.bootstrapDestroyWindow("{}")\nexcept ImportError: pass'.format(
            self.objectName())
        super(BootStrapWidget, self).show(**kwargs)

        # self.dockableShow(**kwargs)

    def dockableShow(self, *args, **kwargs):
        """ Copied from mayaMixin.MayaQWidgetDockableMixin().show() so we can tweak the docking settings.

        """
        # Update the dockable parameters first (if supplied)
        if len(args) or len(kwargs):
            self.setDockableParameters(*args, **kwargs)
        elif self.parent() is None:
            # Set parent to Maya main window if parent=None and no dockable parameters provided
            self._makeMayaStandaloneWindow()

        # Handle the standard setVisible() operation of show()
        QtWidgets.QWidget.setVisible(self,
                                     True)  # NOTE: Explicitly calling QWidget.setVisible() as using super() breaks in PySide: super(self.__class__, self).show()

        # Handle special case if the parent is a QDockWidget (dockControl)
        parent = self.parent()
        if parent:
            parentName = parent.objectName()
            if parentName and len(parentName) and cmds.workspaceControl(parentName, q=True, exists=True):
                if cmds.workspaceControl(parentName, q=True, visible=True):
                    cmds.workspaceControl(parentName, e=True, restore=True)
                else:
                    if kwargs['dockable']:
                        cmds.workspaceControl(parentName, e=True, visible=True)
                    else:
                        # Create our own so we can have our own transparent background
                        ptr = apiUI.MQtUtil.getCurrentParent()
                        mw = wrapInstance(long(ptr), QtWidgets.QMainWindow)
                        mw.show()
