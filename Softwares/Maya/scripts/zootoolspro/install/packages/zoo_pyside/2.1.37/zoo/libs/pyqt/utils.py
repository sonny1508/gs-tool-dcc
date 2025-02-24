import contextlib
import os
import sys
from functools import partial

from zoovendor.Qt import QtWidgets, QtGui, QtCore, QtTest

from zoo.libs.pyqt import uiconstants
from zoo.core.util import zlogging
from zoo.core.util import env

logger = zlogging.getLogger(__name__)
if sys.version_info > (3,):
    long = int


def loggingMenu(name=None):
    def setRootCallback(level):
        zlogging.rootLogger().setLevel(zlogging.levelsDict()[level])

    def levelSetCallback(log, level):
        try:
            log.setLevel(zlogging.levelsDict()[level])
        except AttributeError:
            # occurs on a placeHolder logging object
            pass

    logMenu = QtWidgets.QMenu(name or "logging")
    logMenu.setTearOffEnabled(True)

    for level in zlogging.levelsDict():
        levelAction = logMenu.addAction(level)
        levelAction.triggered.connect(partial(setRootCallback, level))
    logMenu.addSeparator()

    for name, log in zlogging.iterLoggers():
        subMenu = logMenu.addMenu(name)
        for level in zlogging.levelsDict():
            levelAction = subMenu.addAction(level)
            levelAction.triggered.connect(partial(levelSetCallback, log, level))

    return logMenu


def iterParents(widget):
    """Get all the parents of the widget

    :param widget: Widget to get the parents of
    :type widget: Qt.QtWidgets.QWidget.QWidget
    :return:
    :rtype: list[Qt.QtWidgets.QWidget.QWidget]
    """

    parent = widget
    while True:
        parent = parent.parentWidget()
        if parent is None:
            break

        yield parent


def iterChildren(widget, skip=None):
    """Yields all descendant widgets depth-first

    :param widget: Widget to iterate through
    :type widget: QtWidgets.QWidget
    :param skip: If the widget has this property, it will skip it's children
    :type skip: basestring
    :return:
    """
    for child in widget.children():
        yield child

        if skip is not None and child.property(skip):
            continue

        for grandchild in iterChildren(child, skip):
            yield grandchild


def hasAncestorType(widget, ancestorType, maxIter=20):
    """Boolean version of ancestor

    :param widget: The target widget to check
    :type widget: QtWidgets.QWidget
    :param ancestorType: The type of widget to search for eg. toolsetui.ToolsetsUi
    :type ancestorType: class
    :param maxIter: Max number of iterations to check through the parent and their parents
    :type maxIter: int
    :return:
    :rtype:
    """
    return True if ancestor(widget, ancestorType, maxIter) else False


def invalidateWindow(w):
    """Invalidate window to force the window to update the sizes.
    Assumes window to be hidden

    :param w:
    :return:
    """
    w.show()
    w.layout().invalidate()
    w.hide()


def widgetVisible(widget):
    """Checks if the widget is actually visible. widget.isVisible() only checks if the visible flag is off or on.
    Even if the parent is invisible and widget is visible, this should still work correctly.

    :param widget: QtWidgets.QWidget
    :return:
    """
    if not widget.visibleRegion().isEmpty():
        return True
    return False


def updateWidgetSizes(w):
    """Update the widget sizes, especially useful for resizing and showing

    :param w:
    :return:
    """
    w.layout().update()
    w.layout().activate()


def ancestor(widget, ancestorType, maxIter=20):
    """Checks if widget has an ancestor of a certain type

    Example:

    .. code-block:: python

        class Ancestor(QtWidgets.QWidget):
            pass

        ancestor = Ancestor()
        x = QtWidgets.QWidget(ancestor)

        hasAncestorType(x, Ancestor) # True

    :param widget: The target widget to check
    :type widget: QtWidgets.QWidget
    :param ancestorType: The type of widget to search for eg. toolsetui.ToolsetsUi
    :type ancestorType: class
    :param maxIter: Max number of iterations to check through the parent and their parents
    :type maxIter: int
    :return:
    :rtype:
    """
    index = maxIter

    parent = widget.parent()
    while parent is not None and index >= 0:
        if isinstance(parent, ancestorType):
            return parent

        if callable(parent.parent):
            parent = parent.parent()

        else:
            parent = parent.parent
            logger.warning(
                "Warning {} parent() has been overridden and is not callable. Assuming self.parent attribute is the parent".format(
                    widget
                )
            )

        index -= 1

    return None


def absQPoint(p):
    """Get the abs() for qpoint

    :param p:
    :type p: QtCore.QPoint
    :return:
    :rtype: QtCore.QPoint
    """
    return QtCore.QPoint(abs(p.x()), abs(p.y()))


def safeTreeWidgetIterator(item, flags=QtWidgets.QTreeWidgetItemIterator.All):
    """A PyQt and PySide compatible QTreeWidgetItemIterator which handles incrementing
    the iterator on each loop to avoid the infinite loop.

    :param item:
    :type item: :class:`QtWidgets.QTreeWidget` or :class:`QtWidgets.QTreeWidgetItemIterator`
    :param flags: Qt QTreeWidgetItemIterator flags
    :type flags: int
    :return: Generator which returns each item in the tree
    :rtype: list[:class:`QtWidgets.QtTreeWidgetItem`]
    """
    iterator = QtWidgets.QTreeWidgetItemIterator(item, flags)
    while iterator.value():
        yield iterator.value()
        iterator += 1


def getWidgetTree(widget, maxIter=20):
    """Get the widget's tree from its ancestors

    :param widget:
    :return:
    """
    index = maxIter

    parent = widget.parent()
    while parent is not None and index >= 0:
        if isinstance(parent, QtWidgets.QAbstractItemView):
            return parent

        if callable(parent.parent):
            parent = parent.parent()

        else:
            parent = parent.parent
            logger.warning(
                "Warning {} parent() has been overridden and is not callable. Assuming self.parent attribute is the parent".format(
                    widget
                )
            )

        index -= 1


def isNameInChildren(widgetName, parentWidget):
    for childWid in iterChildren(parentWidget):
        if childWid.objectName() == widgetName:
            return childWid


def hsvColor(hue, sat=1.0, val=1.0, alpha=1.0):
    """Create a QColor from the hsvaValues

    .. note:: All the values must be in the range 0.0-1.0.

    :param hue:  The hue value
    :type hue: float
    :param sat: The saturation value.
    :type sat: float
    :param val: The value.
    :type val: float
    :param alpha: The alpha component of the HSV color.
    :type alpha: float
    :rtype: :class:`QtGui.QColor`
    """
    color = QtGui.QColor()
    color.setHsvF(hue, sat, val, alpha)
    return color


def colorStr(c):
    """Generate a hex string code from a QColor"""
    return ("%02x" * 4) % (c.red(), c.green(), c.blue(), c.alpha())


def hBoxLayout(parent=None, margins=(2, 2, 2, 2), spacing=2):
    layout = QtWidgets.QHBoxLayout(parent)
    layout.setContentsMargins(*margins)
    layout.setSpacing(spacing)
    return layout


def hframeLayout(parent=None):
    subFrame = QtWidgets.QFrame(parent=parent)
    layout = hBoxLayout(subFrame)
    return subFrame, layout


def vframeLayout(parent=None):
    subFrame = QtWidgets.QFrame(parent=parent)
    layout = vBoxLayout(subFrame)
    return subFrame, layout


def vBoxLayout(parent=None, margins=(2, 2, 2, 2), spacing=2):
    layout = QtWidgets.QVBoxLayout(parent)
    layout.setContentsMargins(*margins)
    layout.setSpacing(spacing)
    return layout


def hlineEdit(labelName, parent, enabled=True):
    layout = QtWidgets.QHBoxLayout()
    label = QtWidgets.QLabel(labelName, parent=parent)
    edit = QtWidgets.QLineEdit(parent=parent)
    edit.setEnabled(enabled)

    layout.addWidget(label)
    layout.addWidget(edit)
    layout.setContentsMargins(2, 2, 2, 2)
    layout.setSpacing(1)
    return label, edit, layout


def vlineEdit(labelName, parent, enabled=True):
    layout = QtWidgets.QVBoxLayout()
    label = QtWidgets.QLabel(labelName, parent=parent)
    edit = QtWidgets.QLineEdit(parent=parent)
    edit.setEnabled(enabled)
    layout.addWidget(label)
    layout.addWidget(edit)
    layout.setContentsMargins(2, 2, 2, 2)
    layout.setSpacing(1)
    return label, edit, layout


def recursivelySetActionVisiblity(menu, state):
    """Will recursively set the visible state of the QMenu actions

    :param menu: The QMenu to search
    :type menu: QMenu
    :type state: bool
    """
    for action in menu.actions():
        subMenu = action.menu()
        if subMenu:
            recursivelySetActionVisiblity(subMenu, state)
        elif action.isSeparator():
            continue
        if action.isVisible() != state:
            action.setVisible(state)
    if (
        any(action.isVisible() for action in menu.actions())
        and menu.isVisible() != state
    ):
        menu.menuAction().setVisible(state)


def desktopPixmapFromRect(rect, widget, captureDesktop=True):
    """Generates a pixmap on the specified QRectangle.

    :param rect: Rectangle to Snap
    :type rect: :class:`~PySide.QtCore.QRect`
    :param widget: widget instance to get the window id from.
    :type widget: :class:`PySide.QtWidgets.QWidget`
    :returns: Captured pixmap
    :rtype: :class:`~PySide.QtGui.QPixmap`
    """
    screen = screenFromWidget(widget)
    winId = 0  # note: 0 is valid and allows capturing of entire desktop pixels
    if not captureDesktop:  # only capture from the widget pixels
        winId = long(widget.winId())
    return screen.grabWindow(winId, rect.x(), rect.y(), rect.width(), rect.height())


def windowOffset(window):
    """Gets the window offset often not seen in frameless windows.

    :param window: the Window widget
    :type window: :class:`QtWidgets.QMainWindow`
    :return: The offset
    :rtype: QtCore.QPoint
    """
    return window.pos() - window.mapToGlobal(QtCore.QPoint(0, 0))


def widgetCenter(widget):
    """Widget Center

    :param widget: Widget to the center of
    :type widget: QtWidgets.QWidget
    :rtype: QtCore.QPoint
    :return: Center point of widget
    """
    return QtCore.QPoint(widget.width() * 0.5, widget.height() * 0.5)


def updateStyle(widget):
    """Updates a widget after a style object name change.
    eg. widget.setObjectName()

    :param widget:
    :return:
    """
    widget.setStyle(widget.style())


def squaredLength(pt):
    """Squared length of a point. Higher performance than length, at the cost of accuracy.

    :param pt:
    :type pt: Qt.QtCore.QPoint
    :return:
    :rtype: int
    """
    return pt.dotProduct(pt, pt)


def setStylesheetObjectName(widget, name, update=True):
    """Sets the widget to have the object name as set in the stylesheet

    .. code-block:: css

        #redselection {
            background-color: red;
        }

    .. code-block:: python

        btn = QtWidgets.QPushButton("Hello World")
        utils.setStylesheetObjectName(btn, "redselection")

    :param widget: Widget to apply object name to
    :param name: The object name in stylesheet without the '#'
    :return:
    """
    widget.setObjectName(name)
    if update:
        updateStyle(widget)


def widgetsAt(pos):
    """Get widgets underneath

    :param pos:
    :type pos: QtCore.QPoint
    :return: Returns list of all widgets underneath pos
    :rtype: List[Tuple[QWidget], QPoint]]
    """

    widgets = []
    widgetAt = QtWidgets.QApplication.widgetAt(pos)

    while widgetAt:
        widgets.append((widgetAt, widgetAt.mapFromGlobal(pos)))

        # Make widget invisible to further enquiries
        widgetAt.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
        widgetAt = QtWidgets.QApplication.widgetAt(pos)

    # Restore attribute
    for widget in widgets:
        widget[0].setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, False)

    return widgets


def widgetsUnderCursor():
    """Gets the widgets underneath the cursor

    :return:
    :rtype: List[Tuple[QWidget, QPoint]]
    """
    return widgetsAt(QtGui.QCursor.pos())


def clickUnder(
    pos,
    under=1,
    button=QtCore.Qt.LeftButton,
    modifier=QtCore.Qt.KeyboardModifier.NoModifier,
):
    """Clicks under the widget

    :param pos:
    :type pos: QtCore.QPoint
    :param under: Number of iterations under
    :type under: int

    :return:
    """
    widgets = widgetsAt(pos)
    QtTest.QTest.mouseClick(widgets[under][0], button, modifier, widgets[under][1])


def widgetAttributesString(widget, trueOnly=True):
    """

    :param widget:
    :type widget: QtWidgets.QWidget
    :return:
    :rtype:
    """
    attrs = [
        getattr(QtCore.Qt.WidgetAttribute, attr)
        for attr in dir(QtCore.Qt.WidgetAttribute)
        if "WA" in attr
    ]
    ret = ""
    for a in attrs:
        isTrue = widget.testAttribute(a)
        if isTrue:
            ret += "{}: {}\n".format(a, widget.testAttribute(a))

    return ret


def windowFlagsString(windowFlags):
    """Returns a nice string that describes what's inside a windowFlags object

    .. code-block:: python

        print(windowFlagsString(self.windowFlags()))

    Prints out:

    .. code-block:: python

        QtCore.Qt.Dialog
            | QtCore.Qt.WindowTitleHint
            | QtCore.Qt.WindowSystemMenuHint
            | QtCore.Qt.WindowCloseButtonHint
            | QtCore.Qt.WindowContextHelpButtonHint

    :param windowFlags:
    :return:
    """
    flagTypes = [
        QtCore.Qt.Window,
        QtCore.Qt.Dialog,
        QtCore.Qt.Sheet,
        QtCore.Qt.Drawer,
        QtCore.Qt.Popup,
        QtCore.Qt.Tool,
        QtCore.Qt.ToolTip,
        QtCore.Qt.SplashScreen,
    ]

    # Window Flag types
    windowFlagTypes = [
        QtCore.Qt.MSWindowsFixedSizeDialogHint,
        QtCore.Qt.X11BypassWindowManagerHint,
        QtCore.Qt.FramelessWindowHint,
        QtCore.Qt.WindowTitleHint,
        QtCore.Qt.WindowSystemMenuHint,
        QtCore.Qt.WindowMinimizeButtonHint,
        QtCore.Qt.WindowMaximizeButtonHint,
        QtCore.Qt.WindowCloseButtonHint,
        QtCore.Qt.WindowContextHelpButtonHint,
        QtCore.Qt.WindowShadeButtonHint,
        QtCore.Qt.WindowStaysOnTopHint,
        QtCore.Qt.WindowStaysOnBottomHint,
        QtCore.Qt.CustomizeWindowHint,
    ]
    text = ""

    # Add to text if flag type found
    flagType = windowFlags & QtCore.Qt.WindowType_Mask
    for t in flagTypes:
        if t == flagType:
            text += str(t)
            break

    # Add to text if the flag is found
    for wt in windowFlagTypes:
        if windowFlags & wt:
            text += "\n| {}".format(str(wt))

    return text


def keyboardModifiers():
    """Keyboard modifiers

    :return:
    :rtype: Qt.QtCore.Qt.KeyboardModifier
    """
    return QtWidgets.QApplication.keyboardModifiers()


def flagTypes(flag):
    """Extracts the flag states as strings eg:

    flagTypes(QtWidgets.QStyle.StateFlag)

    [QtWidgets.QStyle.StateFlag.State_HasFocus, QtWidgets.QStyle.StateFlag.State_AutoRaise,
    QtWidgets.QStyle.StateFlag.State_Bottom, QtWidgets.QStyle.StateFlag.State_Children, etc]

    :param flag:
    :return:
    """

    flags = [
        s
        for s in dir(flag)
        if not s.startswith("__")
        and not s.endswith("__")
        and s not in ["name", "values"]
    ]

    ret = []
    for f in flags:
        try:
            flag = getattr(flag, f)
            int(flag)  # Check if it is actually a flag
        except TypeError:
            continue
        ret.append(flag)

    return ret


def flagString(value, flag, fullPath=False):
    """Returns a string with all the flags associated with the value, based on flag

    eg.
    flags = flagString(option.state, QtWidgets.QStyle.StateFlag)
    # flags: ["QtWidgets.QStyle.StateFlag.State_On", "QtWidgets.QStyle.StateFlag.State_HasFocus"

    If fullPath is false, it will just return the last part of the flag name:

        # flags: ["State_On", "State_HasFocus"]


    :param value:
    :param flag:
    :param fullPath: Return the last state instead eg ["State_On", State_HasFocus]
    :return:
    """

    ftypes = flagTypes(flag)

    ret = []

    # Add to text if the flag is found
    for wt in ftypes:
        if value & wt:
            if fullPath:
                ret.append(str(wt.split(".")))
            else:
                ret.append(str(wt).split(".")[-1])

    return ret


def alignmentString(alignmentFlags):
    """Returns a nice string that describes what's inside a alignment object

    :param alignmentFlags: Alignment flags
    :return:
    """
    # Window Flag types
    windowFlagTypes = [
        QtCore.Qt.AlignLeft,
        QtCore.Qt.AlignHCenter,
        QtCore.Qt.AlignRight,
        QtCore.Qt.AlignTop,
        QtCore.Qt.AlignVCenter,
        QtCore.Qt.AlignBottom,
    ]
    text = ""

    # Add to text if the flag is found
    for wt in windowFlagTypes:
        if alignmentFlags & wt:
            text += "{} | ".format(str(wt))

    return text


def dpiMult():
    # todo: Replace with a Host agnostic version
    #  Maya has a different way of getting DPI compared to QT where it doesn't modify QT
    # or at least it's undocumented.
    scaleFactor = os.getenv("ZOO_QT_SCALE_FACTOR")
    if scaleFactor is not None:
        return float(scaleFactor)
    try:
        from maya import cmds

        dpi = cmds.mayaDpiSetting(query=True, realScaleValue=True)
    # AttributeError is raised on OSX because mayaDPISetting doesn't exist, ImportError for non maya
    except (ImportError, AttributeError):
        screen = currentScreen()
        logicalY = uiconstants.DEFAULT_DPI
        if screen is not None:
            logicalY = screen.logicalDotsPerInch()
        dpi = max(1, float(logicalY) / float(uiconstants.DEFAULT_DPI))
    os.environ["ZOO_QT_SCALE_FACTOR"] = str(dpi)
    return dpi


def dpiScale(value):
    """Resize by value based on current DPI

    :param value: the default 2k size in pixels
    :type value: int
    :return value: the size in pixels now dpi monitor ready (4k 2k etc)
    :rtype value: int
    """
    mult = dpiMult()
    return value * mult


def dpiScaleDivide(value):
    """Inverse resize by value based on current DPI, for values that may get resized twice

    :param value: the size in pixels
    :type value: int
    :return value: the divided size in pixels
    :rtype value: int
    """
    mult = dpiMult()

    if value != 0:
        return float(value) / float(mult)
    else:
        return value


def pixmapFromIcon(image):
    """Returns the first available size for a QImage

    :param image:
    :type image: QtGui.QIcon
    :return:
    """
    return image.pixmap(image.availableSizes()[0])


def marginsDpiScale(left, top, right, bottom):
    """Convenience function to return contents margins

    :param left:
    :param top:
    :param right:
    :param bottom:
    :return:
    """

    if type(left) == tuple:
        margins = left
        return (
            dpiScale(margins[0]),
            dpiScale(margins[1]),
            dpiScale(margins[2]),
            dpiScale(margins[3]),
        )
    return (dpiScale(left), dpiScale(top), dpiScale(right), dpiScale(bottom))


def pointByDpi(point):
    """Scales the QPoint by the current dpi scaling from maya.

    :param point: The QPoint to Scale by the current dpi settings
    :type point: QtCore.QPoint
    :return: The newly scaled QPoint
    :rtype: QtCore.QPoint
    """

    return QtCore.QPoint(dpiScale(point.x()), dpiScale(point.y()))


def sizeByDpi(size):
    """Scales the QSize by the current dpi scaling from maya.

    :param size: The QSize to Scale by the current dpi settings
    :type size: QSize
    :return: The newly scaled QSize
    :rtype: QSize
    """
    return QtCore.QSize(dpiScale(size.width()), dpiScale(size.height()))


def clearLayout(layout):
    """Clear the elements of a layout

    :param layout: The QT Layout instance.
    :type layout: :class:`QtWidgets.QLayout`
    """

    item = layout.takeAt(0)
    while item:
        widget = item.widget()
        if widget is not None:
            widget.deleteLater()

        item = layout.takeAt(0)


def layoutItems(layout):
    """Retrieves the items from the layout and returns it as a list

    :param layout: The layout to retrieve the items from
    :return: List of items from layout
    :rtype: list of QtWidgets.QLayoutItem
    """

    return (layout.itemAt(i) for i in range(layout.count()))


def layoutItem(widget):
    """Get the widgets layout item

    :param widget: The Widget instance.
    :type widget: :class:`QWidget`
    :return:
    :rtype: QtWidgets.QWidget
    """
    for it in layoutItems(widget.parent().layout()):
        if it.widget() == widget:
            return it


def layoutIndex(widget):
    """Get the layout index of the widget in its layout

    :param widget:
    :type widget:
    :return:
    :rtype: int
    """
    for i, it in enumerate(layoutItems(widget.parent().layout())):
        if it.widget() == widget:
            return i


def layoutWidgets(layout):
    """Retrieves the widgets from the layout and returns it as a list

    :param layout: The layout to retrieve the widgets from
    :return: List of widgets from layout
    :rtype: list
    """
    return [layout.itemAt(i).widget() for i in range(layout.count())]

# Modify starts
def screensContainPoint(point):
    """Checks if point is within the screens.
    Works in both Qt4 (Python 2.7) and Qt5 (Python 3.x)

    :param point: QPoint to check
    :return: bool
    """
    try:
        # Qt5 method
        for screen in QtWidgets.QApplication.screens():
            if screen.geometry().contains(point):
                return True
    except AttributeError:
        # Qt4 fallback
        desktop = QtWidgets.QApplication.desktop()
        for i in range(desktop.screenCount()):
            if desktop.screenGeometry(i).contains(point):
                return True
    return False


def currentScreenGeometry():
    """Gets the current screen geometry.
    Works in both Qt4 (Python 2.7) and Qt5 (Python 3.x)

    :rtype: :class:`QtCore.QRect`
    """
    try:
        # Qt5 method
        screen = QtWidgets.QApplication.screenAt(QtGui.QCursor.pos())
        if screen:
            return screen.geometry()
    except AttributeError:
        # Qt4 fallback
        desktop = QtWidgets.QApplication.desktop()
        return desktop.screenGeometry(desktop.screenNumber(QtGui.QCursor.pos()))
    
    # Fallback to primary screen if all else fails
    try:
        return QtWidgets.QApplication.primaryScreen().geometry()
    except AttributeError:
        return QtWidgets.QApplication.desktop().screenGeometry(0)


def currentScreen():
    """Gets current screen.
    Works in both Qt4 (Python 2.7) and Qt5 (Python 3.x)
    
    :rtype: :class:`QRect`
    """
    # Try Qt5 method first
    try:
        return QtWidgets.QApplication.screenAt(QtGui.QCursor.pos())
    except AttributeError:
        # Fallback for Qt4
        desktop = QtWidgets.QApplication.desktop()
        return desktop.screenGeometry(desktop.screenNumber(QtGui.QCursor.pos()))


def screenFromWidget(widget):
    """Gets screen containing the widget.
    Works in both Qt4 (Python 2.7) and Qt5 (Python 3.x)
    
    :param widget: The widget to get screen for
    :rtype: :class:`QRect`
    """
    try:
        return QtWidgets.QApplication.screenAt(widget.mapToGlobal(widget.pos()))
    except AttributeError:
        # Fallback for Qt4
        desktop = QtWidgets.QApplication.desktop()
        return desktop.screenGeometry(desktop.screenNumber(widget.mapToGlobal(widget.pos())))

# Modify ends
def containWidgetInScreen(widget, pos=None):
    """Forces the provided  widget to be within the screen and returns the resulting position

    :param widget: The Widget to change.
    :type widget: QtWidgets.QWidget
    :rtype: :class:`QtCore.QPoint`
    """
    if not pos:
        pos = widget.mapToGlobal(QtCore.QPoint(0, 0))
    else:
        pos = QtCore.QPoint(pos)
    geo = currentScreenGeometry()
    pos.setX(min(max(geo.x(), pos.x()), geo.right() - widget.width()))
    pos.setY(min(max(geo.y(), pos.y()), geo.bottom() - widget.height()))
    return pos


def resetFixedHeight(widget, policy=QtWidgets.QSizePolicy.Preferred):
    """Reset the fixed width

    :param widget:The widget to affect
    :type widget: QtWidgets.QWidget
    :param policy: Policy to change back to (from Fixed)
    :type policy: QtWidgets.QSizePolicy
    """
    widget.setMinimumHeight(0)
    widget.setMaximumHeight(uiconstants.QWIDGETSIZE_MAX)
    if policy is not None:
        setVSizePolicy(widget, policy)


def resetFixedWidth(widget, policy=QtWidgets.QSizePolicy.Preferred):
    """Reset the fixed width

    :param widget: The widget to affect
    :type widget: QtWidgets.QWidget
    :param policy: Policy to change back to (from Fixed)
    :type policy: QtWidgets.QSizePolicy
    """
    widget.setMinimumWidth(0)
    widget.setMaximumWidth(uiconstants.QWIDGETSIZE_MAX)
    if policy is not None:
        setHSizePolicy(widget, policy)


def resetFixedSize(
    widget,
    policy=QtWidgets.QSizePolicy(
        QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred
    ),
):
    """Reset the fixed size

    :param widget: The widget to affect
    :type widget: QtWidgets.QWidget
    :param policy: Policy to change back to (from Fixed)
    :type policy: QtWidgets.QSizePolicy
    """
    widget.setMinimumSize(QtCore.QSize(0, 0))
    widget.setMaximumSize(
        QtCore.QSize(uiconstants.QWIDGETSIZE_MAX, uiconstants.QWIDGETSIZE_MAX)
    )
    if policy is not None:
        widget.setSizePolicy(policy)


def singleShotTimer(func, time=0):
    """Shorthand for QtCore.QTimer.singleShot()

    :param time: Time in milliseconds to run the function
    :type time: int
    :param func: Function to pass through to the single shot timer
    :type func: callable
    """
    QtCore.QTimer.singleShot(time, func)


def setCursor(cursor):
    """Set cursor

    :param cursor: Cursor
    :type: QtCore.Qt.CursorShape
    :return:
    """

    QtWidgets.QApplication.setOverrideCursor(cursor)


def restoreCursor():
    """Resets the cursor back to default

    :return:
    """
    QtWidgets.QApplication.restoreOverrideCursor()
    singleShotTimer(QtWidgets.QApplication.restoreOverrideCursor)


def setVSizePolicy(widget, p):
    """Less painful way of setting the size policies of widgets

    :type widget: QtWidgets.QWidget
    :param p: The new size policy to put into the vertical policy
    :type p: QtWidgets.QSizePolicy
    :return:
    :rtype:
    """
    sizePolicy = widget.sizePolicy()
    sizePolicy.setVerticalPolicy(p)
    widget.setSizePolicy(sizePolicy)


def setHSizePolicy(widget, p):
    """Less painful way of setting the size policies of widgets

    :type widget: QtWidgets.QWidget
    :param p: The new size policy to put into the horizontal policy
    :type p: QtWidgets.QSizePolicy
    :return:
    :rtype:
    """
    sizePolicy = widget.sizePolicy()
    sizePolicy.setHorizontalPolicy(p)
    widget.setSizePolicy(sizePolicy)


def setSizeHint(widget, size):
    """Possibly hacky approach to set the size hint. Monkey-patch

    :param widget:
    :type widget: QtWidgets.QWidget
    :param size:
    :type size: QtCore.QSize
    :return:
    :rtype:
    """
    widget.sizeHint = lambda: size


def mainWindow():
    """Returns the main window depending on program

    :return:
    :rtype: QtWidgets.QWidget
    """
    if env.isMaya():
        from zoo.libs.maya.qt import mayaui

        return mayaui.getMayaWindow()
    return


def processUIEvents():
    """Shorthand for QtWidgets.QApplication.processEvents()"""
    QtWidgets.QApplication.processEvents()


def forceWindowUpdate(w):
    """Forces a window update. Fairly hacky so use when everything else fails

    :param w: The window to force
    :type w: QtWidgets.QMainWindow
    """
    oldGeo = w.geometry()
    geo = w.geometry()
    geo.setHeight(geo.height() - 1)
    w.setGeometry(geo)
    processUIEvents()
    w.setGeometry(oldGeo)


def firstVisibleChild(w):
    """Get first visible child

    :param w: Widget
    :type w: QtWidgets.QWidget
    :return:
    :rtype: QtWidgets.QWidget
    """
    if not w.isVisible():
        return
    for c in iterChildren(w):
        if isinstance(c, QtWidgets.QWidget):
            return c


def clearFocusWidgets():
    """Clear focus if it has the "clearFocus" property set by the developer"""
    focusWidget = QtWidgets.QApplication.focusWidget()
    if focusWidget is not None and focusWidget.property("clearFocus"):
        focusWidget.clearFocus()


def setForcedClearFocus(w, active=True):
    """Set widget to have forced clearFocus. Some widgets need this

    :param active:
    :type active:
    :param w:
    :type w: QtWidgets.QWidget
    """

    w.setProperty("clearFocus", active)


# Obscure functions
def qTreeViewRemoveDottedLines(tree):
    """Removes the dotted lines on selection for tree widget

    https://stackoverflow.com/questions/15830383/get-rid-of-qts-dotted-outline-on-qlistview-items

    :param tree:
    :type tree: QtWidgets.QTreeWidget
    """
    tree.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)


def setShadowEffectEnabled(widget, enabled):
    """Set shadow effect for a widget

    :param widget:
    :type widget: QtWidgets.QWidget
    :param enabled:
    """
    if enabled:
        shadowEffect = widget.property("shadowEffect")
        if shadowEffect is None:
            shadowEffect = QtWidgets.QGraphicsDropShadowEffect(widget)
            widget.setProperty("shadowEffect", shadowEffect)
            shadowEffect.setBlurRadius(dpiScale(15))
            shadowEffect.setColor(QtGui.QColor(0, 0, 0, 150))
            shadowEffect.setOffset(dpiScale(0))
        widget.setGraphicsEffect(shadowEffect)
    else:
        widget.setGraphicsEffect(None)


@contextlib.contextmanager
def blockSignalsContext(qtObjects):
    """Context Manager(with) statement which temporarily disables signals for the provided QObjects.

    :param qtObjects: Iterable of QObjects which will have their signals temporarily blocked.
    :type qtObjects: :class:`QtCore.QObject`

    .. code-block:: python

        wid = QtWidgets.QtWidget()
        with blockSignalsContext((wid,)):
            # do something

    """
    for widget in qtObjects:
        widget.blockSignals(True)
    try:
        yield
    finally:
        for widget in qtObjects:
            widget.blockSignals(False)
