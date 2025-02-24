from zoo.libs import iconlib
from zoo.libs.pyqt.widgets import label, spacer
from zoo.libs.pyqt.widgets.layouts import hBoxLayout, vBoxLayout
from zoovendor.Qt import QtWidgets, QtCore
from zoo.libs.pyqt import uiconstants as uic, utils
from zoo.libs.pyqt.widgets import typehinting

if typehinting:
    from zoovendor.Qt import QtGui


class QFrame(QtWidgets.QFrame):
    mouseReleased = QtCore.Signal(object)

    def __init__(self, parent=None):
        super(QFrame, self).__init__(parent)

    def mouseReleaseEvent(self, event):
        self.mouseReleased.emit(event)
        return super(QFrame, self).mouseReleaseEvent(event)


class CollapsableFrame(QtWidgets.QWidget):
    closeRequested = QtCore.Signal()
    openRequested = QtCore.Signal()
    toggled = QtCore.Signal()
    _collapsedIcon = None  # type: QtGui.QIcon or None
    _expandIcon = None  # type: QtGui.QIcon or None

    def __init__(self, title, collapsed=False, collapsable=True, contentMargins=uic.MARGINS,
                 contentSpacing=uic.SPACING, parent=None):
        """Collapsable frame layout, similar to Maya's cmds.frameLayout
        Title is inside a bg colored frame layout that can open and collapsed
        Code example for how to use is as follows...

            self.collapseLayout = layouts.CollapsableFrame("Custom Title Goes Here", parent=self)
            self.collapseLayout.addWidget(self.customWidget)  # for adding widgets
            self.collapseLayout.addLayout(self.customLayout)  # for adding layouts

        :param title: The name of the collapsable frame layout
        :type title: str
        :param collapsed: Is the default state collapsed, if False it's open
        :type collapsed: bool
        :param collapsable: Are the contents collapsable? If False the contents are always open
        :type collapsable: bool
        :param contentMargins: The margins for the collapsable contents section, left, top, right, bottom (pixels)
        :type contentMargins: tuple
        :param contentSpacing: spacing (padding) for the collapsable contents section, in pixels
        :type contentSpacing: int
        :param parent: the widget parent
        :type parent: class
        """
        super(CollapsableFrame, self).__init__(parent=parent)
        # cache the icons once globally , we can't do this before a instance is created due to
        # QApplication instance may not existing yet in a standard python session
        if CollapsableFrame._collapsedIcon is None:
            CollapsableFrame._collapsedIcon = iconlib.icon("sortClosed", size=utils.dpiScale(12))
            CollapsableFrame._expandIcon = iconlib.icon("sortDown", size=utils.dpiScale(12))

        self._layout = vBoxLayout(parent=self, margins=(0, 0, 0, 0), spacing=0)
        self.title = title
        contentMargins = utils.marginsDpiScale(*contentMargins)
        self.contentMargins = contentMargins
        self.contentSpacing = contentSpacing
        self.collapsable = collapsable
        self.collapsed = collapsed
        if not collapsable:  # if not collapsable must be open
            self.collapsed = False
        self.initUi()
        self.connections()
        utils.setStylesheetObjectName(self.titleFrame, "collapse")

    def initUi(self):
        """Builds the UI, the title and the collapsable widget that' the container for self.hiderLayout
        """
        self.buildTitleFrame()
        self.buildHiderWidget()
        self._layout.addWidget(self.titleFrame)
        self._layout.addWidget(self.widgetHider)
        self.closeRequested.connect(self.toggled.emit)
        self.openRequested.connect(self.toggled.emit)

    def buildTitleFrame(self):
        """Builds the title part of the layout with a QFrame widget
        """
        self.titleFrame = QFrame(parent=self)
        self.titleFrame.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout = hBoxLayout(self.titleFrame, margins=(0, 0, 0, 0))
        # the icon
        self.iconButton = QtWidgets.QToolButton(parent=self)

        if self.collapsed:
            self.iconButton.setIcon(self._collapsedIcon)
        else:
            self.iconButton.setIcon(self._expandIcon)
        self.iconButton.setContentsMargins(0, 0, 0, 0)
        self.titleLabel = label.Label(self.title, parent=self, bold=True)
        self.titleLabel.setContentsMargins(0, 0, 0, 0)
        self._spacerItem = QtWidgets.QSpacerItem(10, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        # add to horizontal layout
        self.horizontalLayout.addWidget(self.iconButton)
        self.horizontalLayout.addWidget(self.titleLabel)
        self.horizontalLayout.addItem(self._spacerItem)

    def addWidget(self, widget):
        self.hiderLayout.addWidget(widget)

    def addLayout(self, layout):
        self.hiderLayout.addLayout(layout)

    def buildHiderWidget(self):
        """Builds widget that is collapsable
        Widget can be toggled so it's a container for the layout
        """
        self.widgetHider = QtWidgets.QFrame(parent=self)
        self.widgetHider.setContentsMargins(0, 0, 0, 0)
        self.hiderLayout = vBoxLayout(self.widgetHider, margins=self.contentMargins,
                                      spacing=self.contentSpacing)
        self.widgetHider.setHidden(self.collapsed)

    def onCollapsed(self):

        self.setUpdatesEnabled(False)
        self.widgetHider.hide()
        self.iconButton.setIcon(self._collapsedIcon)
        utils.processUIEvents()  # Double process ui events to improve responsiveness of collapsing
        self.setUpdatesEnabled(True)
        utils.processUIEvents()
        self.closeRequested.emit()
        self.collapsed = 1

    def onExpand(self):
        self.setUpdatesEnabled(False)
        self.widgetHider.show()
        self.iconButton.setIcon(self._expandIcon)
        self.setUpdatesEnabled(True)
        self.openRequested.emit()
        self.collapsed = 0

    def showHideWidget(self, *args):
        """Shows and hides the widget `self.widgetHider` this contains the layout `self.hiderLayout`
        which will hold the custom contents that the user specifies
        """

        if not self.collapsable:
            return
        # If we're already collapsed then expand the layout
        if self.collapsed:
            self.onExpand()
            return
        self.onCollapsed()

    def connections(self):
        """ Toggle widgetHider vis
        """
        self.iconButton.clicked.connect(self.showHideWidget)
        self.titleFrame.mouseReleased.connect(self.showHideWidget)


class CollapsableFrameThin(CollapsableFrame):
    def buildTitleFrame(self):
        """ Add custom behaviour to the title frame

        :return:
        """
        super(CollapsableFrameThin, self).buildTitleFrame()
        divider = spacer.Divider()
        self._spacerItem.changeSize(utils.dpiScale(3), 0)
        divider.setToolTip(self.toolTip())
        self.horizontalLayout.addWidget(divider, 1)
