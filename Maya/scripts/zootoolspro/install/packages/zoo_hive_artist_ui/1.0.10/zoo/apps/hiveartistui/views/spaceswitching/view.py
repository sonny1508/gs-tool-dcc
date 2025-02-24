from zoo.apps.hiveartistui.views.spaceswitching import model
from zoo.core.util import zlogging
from zoo.libs import iconlib
from zoo.libs.pyqt import uiconstants, utils
from zoo.libs.pyqt.extended import tableviewplus
from zoo.libs.pyqt.models import tablemodel
from zoo.libs.pyqt.widgets import elements
from zoovendor.Qt import QtWidgets, QtCore

logger = zlogging.getLogger(__name__)


class SpaceSwitchWidget(QtWidgets.QWidget):
    """Reusable widget for space switching

    :param controller: The Space Switch controller instance.
    :type controller: :class:`zoo.apps.hiveartistui.views.spaceswitching.controller.HiveSpaceSwitchController`
    """
    spaceChanged = QtCore.Signal()

    def __init__(self, controller, parent):
        super(SpaceSwitchWidget, self).__init__(parent)
        self.controller = controller
        self.initUi()
        self.controller.bindView(self)

    def initUi(self):
        mainLayout = elements.vBoxLayout(self)
        topHLayout = elements.hBoxLayout(spacing=1)
        self.spaceNameEdit = elements.ComboEditRename(label="Space Name", parent=self, mainStretch=14, labelStretch=4,
                                                      items=self.controller.spaceLabels())
        self.spaceOptionsBtn = elements.ExtendedButton(parent=self, icon=iconlib.icon("menudots"))
        self.createSpaceAction = self.spaceOptionsBtn.addAction("Create Space", icon="chain")
        self.removeSpaceAction = self.spaceOptionsBtn.addAction("Remove Space", icon="trash")

        self.spaceWidgetContainer = SpaceWidgetContainer(self.controller, parent=self)

        topHLayout.addWidget(self.spaceNameEdit)
        topHLayout.addWidget(self.spaceOptionsBtn)
        mainLayout.addLayout(topHLayout)
        mainLayout.addWidget(self.spaceWidgetContainer)
        mainLayout.addLayout(topHLayout)
        self.spaceWidgetContainer.hide()

    def updateUI(self):
        """Handles updating any current space switch content ie. space names.
        """
        logger.debug("Updating space switching")
        self.controller.reload()


class SpaceWidgetContainer(QtWidgets.QWidget):
    """Encapsulates a space Attribute settings ie. the main enumeration options etc.
    """

    def __init__(self, controller, parent):
        super(SpaceWidgetContainer, self).__init__(parent)
        self.controller = controller
        self.initUI()

    def initUI(self):
        spaceEditLayout = elements.hBoxLayout(spacing=uiconstants.SPACING)
        drivenData = self.controller.drivenLabels()
        self.driven = elements.ComboBoxRegular("Driven", parent=self, boxRatio=16,
                                               labelRatio=4,
                                               items=[i.label for i in drivenData],
                                               itemData=[i.id for i in drivenData])
        self.constraintType = elements.ComboBoxRegular("Type", parent=self, boxRatio=16,
                                                       labelRatio=4,
                                                       items=self.controller.constraintTypes.values())
        self.defaultDriver = elements.ComboBoxRegular("Default Driver", parent=self, boxRatio=16,
                                                      labelRatio=4)
        self.constraintType.setToText(self.controller.constraintType())
        self.addDriverLabelBtn = elements.ExtendedButton(parent=self, icon=iconlib.icon("plusHollow"))
        self.removeDriverLabelBtn = elements.ExtendedButton(parent=self, icon=iconlib.icon("minusHollow"))
        self.spaceDriverView = tableviewplus.TableViewPlus(manualReload=False, parent=self)

        self.spaceDriverView.setMaximumHeight(utils.dpiScale(150))
        self.spaceDriverView.tableView.verticalHeader().hide()
        self.spaceModel = tablemodel.TableModel(parent=self)
        self.spaceDriverView.setModel(self.spaceModel)
        self.spaceDriverView.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self.spaceDriverView.tableView.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.spaceDriverView.tableView.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        self.spaceDriverView.registerRowDataSource(model.SpaceLabelDataSource(self.controller, headerText="Label"))
        self.spaceDriverView.registerColumnDataSources([model.DriverComponentDataSource(headerText="Driver Component"),
                                                        model.DriverDataSource(headerText="Driver")])

        layout = elements.vBoxLayout(self)
        spaceEditLayout.addStretch(0)
        spaceEditLayout.addWidget(self.addDriverLabelBtn)
        spaceEditLayout.addWidget(self.removeDriverLabelBtn)
        layout.addWidget(self.driven)
        layout.addWidget(self.constraintType)
        layout.addWidget(self.defaultDriver)
        layout.addWidget(self.spaceDriverView)
        layout.addLayout(spaceEditLayout)
        self.refresh()

    def refresh(self):
        self.spaceModel.reload()
        self.spaceDriverView.refresh()
        tableModel = self.spaceDriverView.model()  # this is the proxy model
        for row in range(tableModel.rowCount()):
            index = tableModel.index(row, 1)
            if tableModel.flags(index) & QtCore.Qt.ItemIsEditable:
                self.spaceDriverView.openPersistentEditor(index)
