""" ---------- Zoo Icons -------------
Zoo Icon Library UI for developers, click the icons name copied to the clipboard

"""

from zoovendor.Qt import QtWidgets, QtCore

from zoo.libs.utils import output
from zoo.libs.iconlib import iconlib
from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.apps.toolsetsui import toolsetui
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt import utils
from zoo.libs.pyqt.widgets import elements
from zoo.libs.pyqt.models import datasources, listmodel, constants, modelutils
from zoo.libs.pyqt.extended import listviewplus


SIZES_TEXT = ["16 - Menu/Button Icon Size",
              "20 - Toolset Tool Icon Size",
              "24 - Medium Icon Size",
              "32 - Maya Shelf Icon Size",
              "64 - Large Icons"]
SIZES = [16, 20, 24, 32, 64]
DEFAULT_ICON_SIZE = 16
SEARCH_ROLE = constants.userRoleCount + 1


class ZooIcons(toolsetwidget.ToolsetWidget):
    id = "zooIcons"
    info = "Icon library for Zoo Tools Pro"
    uiData = {"label": "Zoo Icon Library",
              "icon": "image",
              "tooltip": "Icon library for Zoo Tools Pro",
              "defaultActionDoubleClick": False}

    # ------------------
    # STARTUP
    # ------------------

    def preContentSetup(self):
        """First code to run, treat this as the __init__() method"""
        pass

    def contents(self):
        """The UI Modes to build, compact, medium and or advanced """
        return [self.initCompactWidget()]

    def initCompactWidget(self):
        """Builds the Compact GUI (self.compactWidget) """
        self.compactWidget = IconViewWidget(parent=self)
        return self.compactWidget

    def postContentSetup(self):
        """Last of the initialize code"""
        self.uiConnections()

    def defaultAction(self):
        """Double Click
        Double clicking the tools toolset icon will run this method
        Be sure "defaultActionDoubleClick": True is set inside self.uiData (meta data of this class)"""
        pass

    def currentWidget(self):
        """ Currently active widget

        :return:
        :rtype: list[:class:``]
        """
        return super(ZooIcons, self).currentWidget()

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[:class:``]
        """
        return super(ZooIcons, self).widgets()

    # ------------------
    # LOGIC
    # ------------------

    def sendIconName(self, iconName):
        """Sends the icon to toolset UIs (selection set)

        :param iconName: The name of the icon
        :type iconName: str
        """
        toolsets = toolsetui.toolsetsByAttr(attr="global_receiveIcon")
        for tool in toolsets:
            tool.global_receiveIcon(iconName)

    def iconPressed(self, index):
        """After an icon is pressed, send the message to the user and copy to clipboard
        """
        # index is from the proxy model ie. handles search, so we remap to our model before
        # getting values.
        sourceIndex, sourceModel = modelutils.dataModelIndexFromIndex(index)
        iconData = sourceModel.data(sourceIndex, role=constants.userObject)
        if not iconData:
            return
        text = iconData["label"]
        self.sendIconName(text)
        app = QtCore.QCoreApplication.instance()
        app.clipboard().setText(text)
        output.displayInfo("Icon name copied to the clipboard: `{}`".format(text))

    def iconSize(self):
        size = SIZES[self.properties.sizeCombo.value]
        size = utils.dpiScale(size)
        self.compactWidget.model.rowDataSource.setIconSize(QtCore.QSize(size, size))
        self.compactWidget.iconView.listview.setIconSize(QtCore.QSize(size, size))
        # a bit of a workaround due to icon.pixmap limits, will investigate
        for iconData in self.compactWidget.model.rowDataSource.userObjects():
            iconData["icon"] = iconlib.Icon.icon(iconData["label"], size=size)

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        self.compactWidget.iconView.listview.pressed.connect(self.iconPressed)
        self.compactWidget.sizeCombo.itemChanged.connect(self.iconSize)


class AllWidgets(QtWidgets.QWidget):
    """Create all the widgets for all GUIs, compact and advanced etc"""


class IconViewWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(IconViewWidget, self).__init__(parent)
        mainLayout = elements.vBoxLayout(self, margins=(uic.WINSIDEPAD, uic.WINBOTPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SREG)

        tooltip = "Change the display icons size"
        self.sizeCombo = elements.ComboBoxRegular(label="Display Icon Sizes", items=SIZES_TEXT,
                                                  toolTip=tooltip,
                                                  labelRatio=1,
                                                  boxRatio=3, parent=self)
        self.iconView = listviewplus.ListViewPlus(searchable=True, parent=self)
        self.iconView.setToolBarSearchSlidingActive(False)
        self.iconView.setListViewSpacing(5)
        self.iconView.setMainSpacing(8)
        self.iconView.setSearchMargins(2, 0, 10, 0)
        self._setViewState()

        mainLayout.addWidget(self.sizeCombo)
        mainLayout.addWidget(elements.Divider())
        mainLayout.addWidget(self.iconView)
        self._refresh()

    def _setViewState(self):
        """Sets up the listview options just to keep code cleaner
        """
        self.iconView.listview.setMouseTracking(True)
        self.iconView.listview.setViewMode(QtWidgets.QListView.IconMode)
        self.iconView.listview.setResizeMode(QtWidgets.QListView.Adjust)
        self.iconView.listview.setSelectionMode(QtWidgets.QListView.SingleSelection)
        self.iconView.listview.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.iconView.listview.setUniformItemSizes(True)

        self.iconView.listview.setDragEnabled(False)
        self.iconView.listview.setAcceptDrops(False)
        self.iconView.listview.setUpdatesEnabled(True)
        self.iconView.listview.verticalScrollBar().setSingleStep(5)  # scroll sensitivity
        # this is so we override with our custom role for search since our delegate as minor issues with text.
        self.iconView.setSearchRole(SEARCH_ROLE)
        self.iconView.listview.setIconSize(QtCore.QSize(DEFAULT_ICON_SIZE, DEFAULT_ICON_SIZE))

    def _refresh(self):
        self.model = IconModel(parent=self)
        self.iconView.setModel(self.model)
        self.model.refresh()  # delegate requires access to the dataSource
        # sets the view for all icons to use our custom item delegate to only draw the icon
        delegate = self.model.rowDataSource.delegate(self.iconView)
        self.iconView.listview.setItemDelegate(delegate)

        self.iconView.refresh()


class IconModel(listmodel.ListModel):
    """Overridden to provide a refresh
    """

    def __init__(self, parent=None):
        super(IconModel, self).__init__(parent)

    def refresh(self):
        icons = []
        for index, iconName in enumerate(sorted(iconlib.Icon.iconCollection)):
            iconSize = utils.dpiScale(16)
            icon = iconlib.Icon.icon(iconName, size=iconSize)
            icons.append({"label": iconName, "icon": icon,
                          "toolTip": iconName})
        self.rowDataSource = IconDataSource(icons, model=self)
        self.reload()


class IconDataSource(datasources.IconRowDataSource):
    """Encapsulates icons as a list and the IconModel internals access the methods when it's internally
    needed. To Access this source use model.rowDataSource, to access individual icons by modelIndex
    use model.data(QModelIndex, role=constants.userObject)
    """

    def __init__(self, icons, headerText=None, model=None, parent=None):
        super(IconDataSource, self).__init__(headerText, model, parent)
        self._icons = icons
        self._iconSize = QtCore.QSize(DEFAULT_ICON_SIZE, DEFAULT_ICON_SIZE)

    def setIconSize(self, size):
        self._iconSize = size

    def userObjects(self):
        return self._icons

    def setUserObjects(self, objects):
        self._icons = objects

    def rowCount(self):
        return len(self._icons)

    def isEditable(self, index):
        return False

    def isSelectable(self, index):
        return False

    def toolTip(self, index):
        return self._icons[index]["label"]

    def icon(self, index):
        return self._icons[index]["icon"]

    def iconSize(self, index):
        return self._iconSize

    def customRoles(self, index):
        """Overridden for searching, this is a workaround due to the icon delegate displaying
        text when the data() method is overridden.
        """
        return [SEARCH_ROLE]

    def dataByRole(self, index, role):
        """Overridden for search
        """
        if role == SEARCH_ROLE:
            return self._icons[index]["label"]
