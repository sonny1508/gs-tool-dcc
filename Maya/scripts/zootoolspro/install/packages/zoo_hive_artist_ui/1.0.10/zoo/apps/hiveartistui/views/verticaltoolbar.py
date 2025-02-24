from zoo.apps.hiveartistui.views import hivetoolbar
from zoo.apps.toolsetsui import registry
from zoo.apps.toolsetsui.widgets import toolsetframe
from zoo.libs import iconlib
from zoo.libs.pyqt import utils
from zoo.libs.pyqt.widgets import elements
from zoo.libs.pyqt.widgets import roundbutton
from zoovendor.Qt import QtWidgets, QtCore


class VerticalToolBar(QtWidgets.QFrame):
    def __init__(self, parent=None, core=None, themePref=None, sidePanel=None, resizerWidget=None, toolsetGroup="",
                 startShown=False):
        """ Vertical toolbar

        :param parent:
        :type parent:
        :param core:
        :type core:
        :param themePref:
        :type themePref:
        :param sidePanel:
        :type sidePanel: :class:`QtWidgets.QStackedWidget`
        :param resizerWidget:
        :type resizerWidget: :class:`zoo.libs.pyqt.widgets.resizerwidget.ResizerWidget`
        :param toolsetGroup:
        :type toolsetGroup:
        """

        super(VerticalToolBar, self).__init__(parent=parent)

        self.mainLayout = elements.hBoxLayout(self)
        self.verticalToolbarLayout = elements.vBoxLayout()
        self.setLayout(self.mainLayout)
        self.themePref = themePref
        self.sidePanel = sidePanel
        self.toolsetRegistry = registry.instance()
        self.core = core
        self.resizerWidget = resizerWidget
        self._startShown = startShown

        if resizerWidget is not None:
            self.setResizerWidget(resizerWidget)

        self.toolsetFrame = toolsetframe.ToolsetFrame(self, self.toolsetRegistry, window=parent, iconSize=16, iconPadding=0,
                                                      showMenuBtn=False, initialGroup=toolsetGroup, switchOnClick=False)


        self.initUi()
        self.connections()
        self.setFixedWidth(utils.dpiScale(40))

    def initUi(self):
        """ Init UI

        :return:
        """
        iconColour = self.themePref.HIVE_TOOLBAR_ICON_COLOR
        hueShift = self.themePref.HIVE_TOOLBAR_ICON_HUESHIFT

        self.hiveTools = hivetoolbar.HiveToolbar(self.core, parent=self, iconColor=iconColour, hueShift=hueShift)


        self.verticalSliderBtn = roundbutton.RoundButton(icon=iconlib.iconColorized("arrowSingleLeft", 10,
                                                                                    color=(0, 0, 0)))
        self.verticalSliderBtn.setFixedSize(utils.sizeByDpi(QtCore.QSize(22, 22)))

        self.toolsetFrame.toolbar.setContentsMargins(0, 0, 0, 0)
        self.toolsetFrame.toolbar.mainLayout.setContentsMargins(0, 0, 0, 0)

        self.toolsetFrame.toolbar.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)

        self.verticalToolbarLayout.addWidget(self.hiveTools)
        self.verticalToolbarLayout.addWidget(self.toolsetFrame)
        self.sidePanel.addWidget(self.toolsetFrame.tree)

        self.verticalToolbarLayout.addWidget(self.verticalSliderBtn)
        self.verticalToolbarLayout.setSpacing(utils.dpiScale(10))
        self.verticalToolbarLayout.setContentsMargins(*utils.marginsDpiScale(0, 5, 4, 10))

        toolbarSpacing = VerticalToolBarPad(self)
        toolbarSpacing.setFixedWidth(utils.dpiScale(2))

        self.mainLayout.addWidget(toolbarSpacing)
        self.mainLayout.addLayout(self.verticalToolbarLayout)

    def setResizerWidget(self, resizerWidget):
        """

        :param resizerWidget:
        :type resizerWidget:  zoo.libs.pyqt.widgets.resizerwidget.ResizerWidget
        :return:
        :rtype:
        """
        self.resizerWidget = resizerWidget
        self.resizerWidget.resizerBtn.clicked.connect(self.updateResizerVis)

        if self._startShown:
            self.resizerWidget.resizerBtn.hide()
        else:
            self.resizerWidget.resizerBtn.flipArrowDirection()
            self.hide()

    def connections(self):
        """ Connections

        :return:
        """
        self.verticalSliderBtn.clicked.connect(self.sliderButtonClicked)
        self.toolsetFrame.toolsetToggled.connect(self.toolsetToggledEvent)
        self.toolsetFrame.toolsetClosed.connect(self.toolsetToggledEvent)

    def toolsetToggledEvent(self):
        """ Toggle event

        :return:
        :rtype:
        """
        self.resizerWidget.setWidgetVisible(self.sidePanel, True)
        self.sidePanel.setCurrentWidget(self.toolsetFrame.tree)

        #anyItemsActive = any([item[1] == ToolsetTreeWidget.ActiveItem_Active for item in self.toolsetFrame.tree.activeItems()])
        if not self.toolsetFrame.tree.itemsVisible():
            self.resizerWidget.setWidgetVisible(self.sidePanel, False)




    def sliderButtonClicked(self):
        """ Hide or show the floating button for this toolbar

        :return:
        """

        self.resizerWidget.toggleWidget()
        self.updateResizerVis()

    def expand(self):
        """ Show all the widgets

        :return:
        :rtype:
        """
        self.resizerWidget.showAllWidgets()
        self.updateResizerVis()

    def toggleToolset(self, toolsetId, expand=True):
        """ Toggle the toolset with ID

        :param toolsetId:
        :type toolsetId:
        :param expand:
        :type expand:
        :return:
        :rtype:
        """
        if expand:
            self.expand()
        self.toolsetFrame.toggleToolset(toolsetId)

    def openToolset(self, toolsetId):
        """ Opens the toolset with ID

        :param toolsetId:
        :type toolsetId:
        :return:
        :rtype:
        """
        self.expand()
        self.toolsetFrame.openToolset(toolsetId)

    def updateResizerVis(self):
        """ Show resizerBtn if self is hidden, else hide it

        :return:
        """
        if self.isHidden():
            self.resizerWidget.resizerBtn.show()
        else:
            self.resizerWidget.resizerBtn.hide()


class VerticalToolBarPad(QtWidgets.QFrame):
    pass