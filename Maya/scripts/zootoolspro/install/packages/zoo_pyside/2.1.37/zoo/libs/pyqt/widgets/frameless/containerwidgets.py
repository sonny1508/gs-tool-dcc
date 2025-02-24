# The two container widgets that will hold our frameless widget.
# The "frameless window" and the "docking widget container"
import uuid
import webbrowser
from zoo.libs.utils import general, output
from zoovendor.Qt import QtWidgets, QtCore, QtGui
from zoovendor.Qt.QtCompat import wrapInstance
from zoo.libs import iconlib

from zoo.libs.pyqt import utils, uiconstants
from zoo.libs.pyqt.widgets import iconmenu
from zoo.core.util import env, zlogging

logger = zlogging.getLogger(__name__)

isMaya = env.isMaya()

if isMaya:
    from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
    from zoo.libs.maya.utils import tooltips
    from maya import cmds, OpenMayaUI as omui

    if env.isPy3():
        long = int

    DockableMixin = MayaQWidgetDockableMixin

else:
    class DockableMixin(object):
        pass

if general.TYPE_CHECKING:
    from zoo.libs.pyqt.widgets.frameless.window import ZooWindow


class ContainerType:
    CT_DockingContainer = 1
    CT_FramelessWindow = 2


class ContainerWidget(object):
    """ An abstract class that can be used in both container types, FramelessWindow and DockingContainer.

    """
    def __init__(self, *args, **kwargs):
        pass

    def isDockingContainer(self):
        """ Container widget can be either `DockingContainer` or `FramelessWindow`

        :return:
        """
        return isinstance(self, DockingContainer)

    def isFramelessWindow(self):
        """ Container widget can be either `DockingContainer` or `FramelessWindow`

        :return:
        """
        return isinstance(self, FramelessWindow)

    def setOnTop(self):
        pass

    def containerType(self):
        """ Return container type

        :return: ContainerType.CT_FramelessWindow or ContainerType.CT_DockingContainer
        :rtype: int
        """

        return ContainerType.CT_FramelessWindow if self.isFramelessWindow() else ContainerType.CT_DockingContainer

    def setWidget(self , widget):
        self.setObjectName(widget.objectName())


class FramelessWindow(QtWidgets.QMainWindow, ContainerWidget):

    def __init__(self, parent=None, width=None, height=None, saveWindowPref=True, onTop=False):
        """ The Frameless window.
        The container that holds the FramelessWidget

        :param parent: 
        :type parent:
        :param width: 
        :type width:
        :param height:
        :type height:
        :param saveWindowPref: Restores to the saved positions and sizes. Defaults to True.
        :type saveWindowPref:
        """
        self._onTop = onTop
        super(FramelessWindow, self).__init__(parent=parent)

        if env.isMac():  # Mac needs it the saveWindowPref all the time otherwise it will be behind the other windows
            self.saveWindowPref()
            utils.singleShotTimer(lambda: self._initSize(width, height))  # Force the size back
        else:
            if saveWindowPref:  # We only need to use restore for the magic save window pref setting.
                self.saveWindowPref()
            self._initSize(width, height)
        self.defaultWindowFlags = self.windowFlags()
        self._initUi()

    def _initUi(self):
        """ Initialize Ui

        :return:
        :rtype:
        """

        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        windowFlags = self.defaultWindowFlags | QtCore.Qt.FramelessWindowHint | QtCore.Qt.NoDropShadowWindowHint
        if self._onTop:
            windowFlags = windowFlags | QtCore.Qt.WindowStaysOnTopHint
        self.defaultWindowFlags = windowFlags ^ QtCore.Qt.WindowMinMaxButtonsHint
        self.setWindowFlags(self.defaultWindowFlags)

        self.layout().setContentsMargins(0, 0, 0, 0)

    def setOnTop(self, onTop):
        """ Set window on top

        :param onTop:
        :return:
        """
        flags = self.windowFlags()
        if onTop:
            flags = flags | QtCore.Qt.WindowStaysOnTopHint
        else:
            flags = flags ^ QtCore.Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.hide()
        self.show()

    def saveWindowPref(self):
        """ Magic property for the frameless window to parent to the maya window for macs
        Also saves the size and position
        """
        self.setProperty("saveWindowPref", True)

    def _initSize(self, width, height):
        """ Initialize window size

        :param width:
        :type width:
        :param height:
        :type height:
        :return:
        :rtype:
        """
        if not (width is None and height is None):
            if width is None:
                width = utils.dpiScale(self.size().width())
            elif height is None:
                height = utils.dpiScale(self.size().height())
            self.resize(width, height)

    def setTransparency(self, enabled):
        """ Set transparency

        :param enabled:
        :type enabled:
        :return:
        :rtype:
        """
        window = self.window()
        if enabled:
            window.setAutoFillBackground(False)
        else:
            window.setAttribute(QtCore.Qt.WA_NoSystemBackground, False)

        window.setAttribute(QtCore.Qt.WA_TranslucentBackground, enabled)
        window.repaint()

    def setShadowEffectEnabled(self, enabled):
        """ Set the shadow effect of the zoo window

        :param enabled:
        :return:
        """
        try:
            utils.setShadowEffectEnabled(self.zooWindow, enabled)
        except AttributeError as e:
            if str(e) == "'NoneType' object has no attribute 'property'":
                raise AttributeError("'zooWindow' must not be `None`.")

    def setWidget(self, widget):
        """ Set widget. Same as the DockingContainer.

        :param widget:
        :type widget: QtWidgets.QWidget
        :return:
        :rtype:
        """
        self.setCentralWidget(widget)
        self.setShadowEffectEnabled(True)

        if not env.isMac():  # Disable for mac as it seems to create an invisible window in front
            self.setNewObjectName(widget)

    @property
    def zooWindow(self):
        return self.centralWidget()

    def setNewObjectName(self, widget):
        """ Set new name based on widget

        :param widget:
        :type widget: QtWidgets.QWidget
        """

        self.setObjectName(widget.objectName() + "Frameless")


class DockingContainer(DockableMixin, QtWidgets.QWidget, ContainerWidget):
    def __init__(self, parent=None, workspaceControlName=None,
                 *args, **kwargs):
        """ The Z-Icon floating widget that will be dragged and docked.

            FramelessWidget will also be attached to this when docked.

            """
        super(DockingContainer, self).__init__(parent=parent, *args, **kwargs)
        self.prevFloating = True
        self.widgetFlags = None
        self.detaching = False
        self.workspaceControl = parent  # type: QtWidgets.QMainWindow
        self.workspaceControlName = workspaceControlName
        self.detachCounter = 0
        self.logoIcon = QtWidgets.QToolButton(self)

        self._initUi()

    def _initUi(self):
        """ Init ui

        :return:
        :rtype:
        """
        uiLayout = utils.vBoxLayout(parent=self, margins=(0, 0, 0, 0))
        uiLayout.addWidget(self.logoIcon)
        # uiLayout.setContentsMargins(0, 0, 0, 0)
        # self.setLayout(uiLayout)

        size = 24
        self.logoIcon.setIcon(iconlib.iconColorizedLayered("zooToolsZ", size=size))
        self.logoIcon.setIconSize(utils.sizeByDpi(QtCore.QSize(size, size)))
        self.logoIcon.clicked.connect(self.close)
        self.win = self.window()

    def deleteControl(self):
        """ Delete control
        """
        cmds.deleteUI(self.workspaceControlName)

    def moveToMouse(self):
        """ Move the window to the mouse
        """
        pos = QtGui.QCursor.pos()
        window = self.win

        if self.win == utils.mainWindow() and self.win is not None:
            logger.error("{}. Found Maya window instead of DockingContainer.".format(self.workspaceControlName))
            return

        offset = utils.windowOffset(window)
        half = utils.widgetCenter(window)
        pos += offset - half

        window.move(pos)
        window.setWindowOpacity(0.8)

    def setWidget(self, widget):  # type: (ZooWindow) -> None
        """ Set the main widget

        :param widget:
        :type widget: :class:`ZooWindow`
        :return:
        :rtype: 
        """
        self.mainWidget = widget
        self.origWidgetSize = QtCore.QSize(self.mainWidget.size())

        self.layout().addWidget(widget)

        super(DockingContainer, self).setWidget(widget)
        self.setMinimumWidth(0)
        self.setMinimumHeight(0)

    def resizeEvent(self, event):
        """

        :param event:
        :type event: QtGui.QResizeEvent
        :return:
        """
        # Only save the size if it's not floating
        if not self.detaching and not self.isFloating():  # isFloating is in MayaDockableMixin
            self.containerSize = self.size()

        return super(DockingContainer, self).resizeEvent(event)

    def showEvent(self, event):
        """ Docking container show event.

        :param event:
        :return:
        """
        if not self.isFloating():
            self.logoIcon.hide()

        if not self.prevFloating and self.isFloating():  # Just got undocked
            self.detaching = True  # Set detaching to true to run the detaching code

        self.prevFloating = self.isFloating()

    def close(self):
        """ Close windows
        """
        super(DockingContainer, self).close()

    def moveEvent(self, event):  # type: (QtGui.QMoveEvent) -> None
        """ Move event

        :param event: 
        :type event: :class:`QtGui.QMoveEvent`
        """

        if self.detaching:
            # Use detach counter to workaround issue where detaching would prematurely run the undock command
            self.detachCounter += 1
            newSize = QtCore.QSize(self.containerSize.width(), self.origWidgetSize.height())
            self.setFixedSize(newSize)

            # We need to see the detach event twice before undocking, sometimes when you drag off
            # the window doesn't stay on the mouse. Set this higher if the window doesn't stay on the mouse
            # when dragging. May need to be tweaked on mac.
            count = 2
            if self.detachCounter == count:
                self.undock()

    def enterEvent(self, event):
        """ The enter event

        :param event: 
        :type event: 
        """
        if self.detaching:
            self.undock()

    def undock(self):
        """ For when the window is undocked

        :return:
        :rtype:
        """
        self.detachCounter = 0
        self.detaching = False  # Set back to false

        if self.isFloating():  # If it's undocked re-attach itself to the frameless window
            frameless = self.mainWidget.attachFramelessWindow(saveWindowPref=False)
            pt = self.mapToGlobal(QtCore.QPoint())

            w = self.containerSize.width()

            frameless.show()
            frameless.setGeometry(pt.x(), pt.y(),
                                  w,
                                  self.origWidgetSize.height())
            self.mainWidget.titleBar.logoButton.deleteControl()  # todo move this to a better place
            self.mainWidget.undocked.emit()  # todo: Maybe docking container should have its own signal here
            self.detaching = False
            self.workspaceControl = None


class SpawnerIcon(iconmenu.IconMenuButton):
    docked = QtCore.Signal(object)
    undocked = QtCore.Signal()
    spawnSize = 35  # size of the dragged out icon

    def __init__(self, zooWindow, parent=None):
        """ The zoo logo icon where it can spawn the docking widget as well. Usually located
        on the top-left corner of the ZooWindow

        :param zooWindow:
        :type zooWindow: :class:`ZooWindow` 
        :param parent:
        :type parent:
        """
        super(SpawnerIcon, self).__init__(parent=parent)
        self.dockingContainer = None  # type: DockingContainer
        self._docked = False
        self.pressedPos = None  # type: QtCore.QPoint

        self.workspaceControlName = None
        self.zooWindow = zooWindow  # type: ZooWindow

        self.setLogoHighlight(True)
        self._initLogoButton()
        self.spawnEnabled = True
        self.initDock = False

    def mousePressEvent(self, event):
        """ Mouse Press event

        :param event:
        :type event:
        """
        # If it's already docked, disable the spawner icon
        # in the future we may want to use this to undock as well
        if self.zooWindow.isDocked() or event.button() == QtCore.Qt.RightButton:
            return

        if event.button() == QtCore.Qt.LeftButton and self.spawnEnabled:
            self.initDock = True  # Start the docking
            self.pressedPos = QtGui.QCursor.pos()  # Get the mouse pressed position

        if isMaya and self.tooltipAction:  # separate for maya
            from zoo.libs.maya.utils.tooltips import tooltipState
            self.tooltipAction.setChecked(tooltipState())

    def updateTheme(self, event):
        """ Override update theme to ignore

        :param event:
        :return:
        """
        pass

    def name(self):
        """ Name should match frameless name.

        If nothing found though, just generate a random one.

        :return:
        :rtype:
        """
        return self.zooWindow.title or self.zooWindow.name or "{} [{}]".format("Window", str(uuid.uuid4())[:4])

    def dockLocked(self):
        return cmds.optionVar(q="workspacesLockDocking")

    def initDockingContainer(self):
        """ Initialize the docking container.

        What this does is it creates a maya workspaceControl and moves the window into it.
        WorkspaceControls are used because it has docking functionality built-in.

        It creates a small icon window, which can then be used to drag into a docked position in Maya.


        :return:
        :rtype:
        """

        locked = self.dockLocked()
        if locked:
            output.displayWarning('Maya docking is locked. You can unlock it on the top right of Maya.')

        size = self.spawnSize

        # Create a small icon sized window to use to drag into maya
        self.workspaceControlName = cmds.workspaceControl("{} [{}]".format(self.name(), str(uuid.uuid4())[:4]),
                                                          # should revisit this, maybe shouldn't be randomly generated to be able to save
                                                          loadImmediately=True,
                                                          label=self.name(),
                                                          retain=False,
                                                          initialWidth=self.zooWindow.width(),
                                                          initialHeight=self.zooWindow.height(),
                                                          vis=True)
        ptr = omui.MQtUtil.getCurrentParent()
        self.workspaceControl = wrapInstance(long(ptr), QtWidgets.QMainWindow)  # type: QtWidgets.QMainWindow

        # Make the window small and icon sized
        w = self.workspaceControl.window()
        w.setFixedSize(utils.sizeByDpi(QtCore.QSize(size, size)))
        w.layout().setContentsMargins(0, 0, 0, 0)

        # Setting window opacity to hide the random flickering that happens
        w.setWindowOpacity(0)
        windowFlags = w.windowFlags() | QtCore.Qt.FramelessWindowHint
        w.setWindowFlags(windowFlags)
        cmds.workspaceControl(self.workspaceControlName,
                              resizeWidth=size, resizeHeight=size, e=1)  # Create the workspace control
        w.show()
        w.setWindowOpacity(1)  # Show UI again after elements have changed

        self.dockingContainer = DockingContainer(self.workspaceControl, self.workspaceControlName)
        # Attach it to the workspaceControl
        widgetPtr = omui.MQtUtil.findControl(self.dockingContainer.objectName())
        omui.MQtUtil.addWidgetToMayaLayout(long(widgetPtr), long(ptr))

        # Move it to the mouse
        self.moveToMouse()

    def workspaceFloating(self):
        """ Is floating or not

        :return:
        :rtype:
        """

        if self.spawnEnabled:
            return cmds.workspaceControl(self.workspaceControlName, floating=True, q=1)

    def mouseMoveEvent(self, event):
        """ Mouse move event

        :param event:
        :type event: QtGui.QMouseEvent
        :return:
        :rtype:
        """
        # Disable creating the docking container if it's already docked
        if self.zooWindow.isDocked():
            return

        # If the user clicks and drags initialize the docking container.
        # We do this so we can still allow click events to go through for the button menu
        if self.pressedPos:
            sqLen = utils.squaredLength((self.pressedPos - QtGui.QCursor.pos()))

        # Only start the docking function if dragged away from pressed position
        if self.initDock and sqLen > 1:
            self.initDockingContainer()
            self.initDock = False

        # If it already exists move workspaceControl to the mouse
        if self.workspaceControlName is not None:
            self.moveToMouse()

    def moveToMouse(self):
        """ Move the window to the mouse

        :return:
        :rtype:
        """

        if self.dockingContainer:
            self.dockingContainer.moveToMouse()

    def mouseReleaseEvent(self, event):
        """ Mouse Release event

        :param event:
        :type event:
        :return:
        :rtype:
        """
        if self.zooWindow.isDocked():
            return

        # Pass through the mouseReleaseEvent so we can drop the window into maya
        if not self.spawnEnabled or self.initDock:
            super(SpawnerIcon, self).mouseReleaseEvent(event)
            return

        if event.button() == QtCore.Qt.RightButton:
            # self.parent().close()
            return

        # If not floating any more should mean it has successfully docked.
        if not self.workspaceFloating():
            self.dockedEvent()
        else:  # If it's still floating delete the workspace control
            self.deleteControl()
        # if not self._docked:
        #     print ("undocking with logo")

    def dockedEvent(self):
        """ The dockedEvent when docked into Maya.

        :return:
        :rtype:
        """
        frameless = self.zooWindow.parentContainer
        self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred))

        # Set the workspace control width and height
        w = self.zooWindow.width()
        h = self.zooWindow.height()
        cmds.workspaceControl(self.workspaceControlName, e=1, initialWidth=w, initialHeight=h)

        # Move the zoo window into the docking container
        self.dockingContainer.setWidget(self.zooWindow)

        # Emit
        self.docked.emit(self.dockingContainer)

        # For splitters
        self.arrangeSplitters(w)

        # Close old window and clear
        self.dockingContainer = None  # docking is finished so we clear this out
        self._docked = True

        frameless.close()

    def arrangeSplitters(self, w):
        """ If docked into splitter widgets, fix the splitter sizes

        :param w:
        :return:
        """

        dc = self.dockingContainer

        child, splitter = self.splitterAncestor(dc)
        if child and isinstance(child, QtWidgets.QTabWidget):
            return

        if child and splitter:
            pos = splitter.indexOf(child) + 1
            if pos == splitter.count():
                sizes = splitter.sizes()
                sizes[-2] = (sizes[-2] + sizes[-1]) - w  # the last two elements  minus width
                sizes[-1] = w
                splitter.setSizes(sizes)
            else:
                splitter.moveSplitter(w, pos)

    def splitterAncestor(self, w):
        """ Get the widgets splitter ancestors

        :param w:
        :return:
        """
        if w is None:
            return None, None
        child = w
        parent = child.parentWidget()
        if parent is None:
            return None, None

        while parent is not None:
            if isinstance(parent, QtWidgets.QSplitter) and parent.orientation() == QtCore.Qt.Horizontal:
                return child, parent
            child = parent
            parent = parent.parentWidget()

        return None, None

    def deleteControl(self):
        """ Delete workspace control

        :return:
        :rtype:
        """

        if self.workspaceControlName:
            cmds.deleteUI(self.workspaceControlName)
            self.workspaceControl = None
            self.workspaceControlName = None
            self.dockingContainer = None
            self._docked = False

    def setLogoHighlight(self, highlight):
        """ Set the logo highlight

        :param highlight:
        :type highlight: bool
        :return:
        :rtype:
        """
        minSize = 0.55 if self.zooWindow.isMinimized() else 1
        size = uiconstants.TITLE_LOGOICON_SIZE * minSize

        if highlight:
            self.setIconByName(["zooToolsZ"],
                               colors=[None, None],
                               size=size,
                               iconScaling=[1],
                               colorOffset=40)
        else:
            self.setIconByName(["zooToolsZ"],
                               colors=[None],
                               tint=(0, 200, 0, 50),
                               tintComposition=QtGui.QPainter.CompositionMode_Plus,
                               size=size,
                               iconScaling=[1],
                               colorOffset=40, grayscale=True)

    def _initLogoButton(self):
        """Initialise logo button settings
        """
        self.setIconSize(QtCore.QSize(24, 24))
        self.setFixedSize(QtCore.QSize(30, 24))
        self.addAction("Create 3D Characters", connect=self.zooToolsProHelp)
        self.addAction("Zoo Tools Pro Help", connect=self.zooToolsProHelp)
        self.tooltipAction = self.addAction("Toggle Tooltips",
                                            connect=self.toggleToolTips,
                                            checkable=True)

        self.setMenuAlign(QtCore.Qt.AlignLeft)

    def toggleToolTips(self, taggedAction):
        """

        :param taggedAction:
        :type: zoo.libs.pyqt.extended.searchablemenu.action.TaggedAction
        :return:
        """

        tooltips.setMayaTooltipState(taggedAction.isChecked())

    def zooToolsProHelp(self):
        """ Zoo Tools pro help

        """
        webbrowser.open("http://create3dcharacters.com")

    def create3dCharactersAction(self):
        """ The menu button to open to create 3d characters webpage

        :return:
        :rtype:
        """
        webbrowser.open("http://create3dcharacters.com")
