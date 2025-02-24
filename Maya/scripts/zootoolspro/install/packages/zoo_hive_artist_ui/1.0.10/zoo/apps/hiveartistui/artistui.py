from functools import wraps

from zoo.apps.hiveartistui import artistuicore, uiinterface
from zoo.apps.hiveartistui.registries import toolregistry
from zoo.apps.hiveartistui.views import createview, verticaltoolbar
from zoo.apps.hiveartistui.views import rigbox
from zoo.apps.hiveartistui.views.loadingwidget import LoadingWidget
from zoo.apps.hiveartistui.views.visibilitybutton import VisibilityButton
from zoo.apps.toolsetsui import toolsetui
from zoo.apps.uitoolsets import hiveartistsettings
from zoo.core.util import zlogging
from zoo.libs.hive import api as hiveapi
from zoo.libs.pyqt import uiconstants
from zoo.libs.pyqt import utils
from zoo.libs.pyqt.widgets import elements
from zoo.libs.pyqt.widgets import resizerwidget
from zoo.libs.utils import profiling
from zoo.preferences.interfaces import coreinterfaces
from zoo.preferences.interfaces import hiveartistuiinterfaces
from zoovendor.Qt import QtCore, QtWidgets

logger = zlogging.getLogger(__name__)


class HiveRigMode(QtWidgets.QFrame):
    """ Stylesheet purposes """


class HiveArtistUI(elements.ZooWindow):
    TOOLSET_GROUP = "hiveArtistUi"
    helpUrl = "https://create3dcharacters.com/maya-hive-autorigger"
    windowSettingsPath = "zoo/hiveartistui"

    def __init__(self, title="Hive",
                 width=580,
                 height=600, parent=None, **kwargs):

        super(HiveArtistUI, self).__init__(title=title, name="HiveWindow",
                                           width=width, height=height, parent=parent,
                                           saveWindowPref=False, **kwargs)
        self.rigBoxWgt = None  # type: rigbox.RigBoxWidget

        self.uiPreferences = hiveartistuiinterfaces.hiveArtistUiInterface()
        self.uiInterface = uiinterface.createInstance(parent=self)
        self.uiInterface.setArtistUi(self)
        self.hiveConfig = hiveapi.Configuration()
        self.componentRegistry = self.hiveConfig.componentRegistry()
        self.toolRegistry = toolregistry.ToolRegistry()
        self.core = artistuicore.HiveUICore(self.componentRegistry, self.toolRegistry, self.uiInterface)

        # UI
        self.mainLayout = elements.hBoxLayout()

        self.themePref = coreinterfaces.coreInterface()
        self.loadingWidget = LoadingWidget(parent=self)
        self.sidePanel = QtWidgets.QStackedWidget(parent=self)
        self.createUi = createview.CreateView(self.componentRegistry, self.hiveConfig.templateRegistry(),
                                              self.core, self.themePref, self.uiInterface, parent=self)

        self.resizerWidget = resizerwidget.ResizerWidget(self, layoutDirection=resizerwidget.ResizerWidget.RightToLeft,
                                                         buttonAlign=QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom,
                                                         buttonOffset=QtCore.QPoint(0, -75),
                                                         collapseDirection=resizerwidget.ResizerWidget.Parallel,
                                                         autoButtonUpdate=False)  # We'll do it manually in this class

        self.verticalToolbar = verticaltoolbar.VerticalToolBar(self, themePref=self.themePref, sidePanel=self.sidePanel,
                                                               core=self.core, toolsetGroup=self.TOOLSET_GROUP,
                                                               startShown=True)

        self.setWindowTitle(title)

        self.initUi()
        self.connections()
        rigs = list(hiveapi.iterSceneRigs())
        # if there's no rig in the scene and the preferences state we default to a rig
        # then make sure one is created.
        if not rigs and self.uiPreferences.onOpenCreateRig():
            self.addRig()
        self.refreshUi()

    def initUi(self):
        """ Initialise the ui
        """
        self.rigBoxWgt = rigbox.RigBoxWidget(parent=self)

        self.setMainLayout(self.mainLayout)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)

        self.titleContentsLayout.addWidget(self.rigBoxWgt)
        self.titleContentsLayout.setContentsMargins(*utils.marginsDpiScale(0, 2, 0, 2))

        self.resizerWidget.addWidget(self.verticalToolbar)
        self.resizerWidget.addWidget(self.sidePanel, external=True, target=False, defaultHidden=True,
                                     initialSize=utils.sizeByDpi(
                                         QtCore.QSize(toolsetui.TOOLSETUI_WIDTH, toolsetui.TOOLSETUI_HEIGHT)))
        self.verticalToolbar.setResizerWidget(self.resizerWidget)
        self.resizerWidget.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)

        # Majority of the create UI
        splitter = QtWidgets.QSplitter(self)
        buildButtons = self.initBottomBar()
        createWidget = QtWidgets.QWidget(self)
        tabLayout = elements.vBoxLayout(createWidget, spacing=0)
        tabLayout.addWidget(self.createUi)
        tabLayout.addLayout(buildButtons)

        splitter.addWidget(createWidget)
        splitter.addWidget(self.sidePanel)

        self.mainLayout.addWidget(splitter)
        self.mainLayout.addWidget(self.resizerWidget)

        self.resizerWidget.updateButtonPosition()

    def initBottomBar(self):
        """ Initialize build buttons

        :return:
        """

        bottomBarLayout = elements.hBoxLayout(margins=(4, 4, 4, 4), spacing=0)
        self.rigModeLayout = elements.hBoxLayout(margins=(5, 5, 5, 5), spacing=uiconstants.SREG / 2)  # , spacing=0)

        # Button group
        self.rigMode = HiveRigMode(parent=self)
        self.rigMode.setFixedHeight(utils.dpiScale(30))
        guideToolTip = "Place the pivots for the rig, modify or add components"
        controlToolTip = "Scale and change the design shapes and colors of the rig's controls."
        skeletonToolTip = "Skin the rig, add correctives, check the skeleton."
        rigToolTip = "Build the rig."
        polishToolTip = "The rig will be built and animator right-click functionality is also added."
        self.rigModeButtons = elements.JoinedRadioButton(texts=["GUIDES", "CONTROLS", "SKELETON", "RIG", "POLISH"],
                                                         toolTips=[guideToolTip, controlToolTip, skeletonToolTip,
                                                                   rigToolTip, polishToolTip],
                                                         parent=self)
        self.viewButton = VisibilityButton(parent=self)

        self.rigMode.setLayout(self.rigModeLayout)
        self.rigModeLayout.addWidget(self.rigModeButtons)
        self.rigModeLayout.addWidget(self.viewButton)

        bottomBarLayout.addWidget(self.rigMode)
        self.setRigPolishedUi(False)
        self.disable()
        return bottomBarLayout

    def resizeEvent(self, *args, **kwargs):
        """ Resize Event

        :param args:
        :type args:
        :param kwargs:
        :type kwargs:
        :return:
        :rtype:
        """
        if hasattr(self, "resizerWidget"):
            self.resizerWidget.updateButtonPosition()

        return super(HiveArtistUI, self).resizeEvent(*args, **kwargs)

    def connections(self):
        """ Connections

        :return:
        """
        self.createUi.templateCreated.connect(self.refreshUi)
        self.rigModeButtons.buttonClicked.connect(self.rigModeToggled)

        self.verticalToolbar.toolsetFrame.toolsetToggled.connect(self.toolsetToggled)
        self.verticalToolbar.hiveTools.requestRefresh.connect(self.refreshUi)

        self.rigBoxWgt.addRigClicked.connect(self.addRig)
        self.rigBoxWgt.renameClicked.connect(self.renameRigClicked)
        self.rigBoxWgt.deleteRigClicked.connect(lambda: self.deleteRig(name=self.rigBoxWgt.currentText()))

        self.core.rigAdded.connect(self.rigAddedEvent)
        self.closed.connect(self._onClose)

    def _onClose(self):
        from zoo.apps.hiveartistui import uiinterface
        uiinterface.destroyInstance()
        try:
            toolsetui._TOOLSETFRAME_INSTANCES.remove(self.toolsetFrame())
        except ValueError:
            pass

    def toolsetToggled(self):
        self.updateHiveSettings()

    def updateHiveSettings(self):
        """ Update hive settings

        :return:
        :rtype:
        """
        settingsToolset = self.toolsetFrame().toolsetById(
            "hiveArtistSettings")  # type: hiveartistsettings.HiveArtistSettings
        if settingsToolset:
            if self.core.currentRigExists():
                settingsToolset.setEnabled(True)
                settingsToolset.setRig(self.core.currentRigContainer.rigModel.rig)
                settingsToolset.rigRenamed.connect(self.updateRigName)
            else:
                settingsToolset.resetUi()
                settingsToolset.setEnabled(False)

    def updateRigName(self):
        """ Renamed through toolset

        :return:
        :rtype:
        """

        rigNames = self.core.rigNames()
        self.rigBoxWgt.updateList(rigNames, setTo=self.core.currentRigContainer.rigModel.rig.name())
        self.core.rigRenamed.emit()

    def openToolset(self, toolsetId):
        self.verticalToolbar.openToolset(toolsetId)

    def openSettings(self):
        self.openToolset("hiveArtistSettings")

    def toolsetFrame(self):
        return self.verticalToolbar.toolsetFrame

    def componentTreeView(self):
        """

        :return:
        :rtype: :class:`zoo.apps.hiveartistui.views.componenttree.ComponentTreeView`
        """
        return self.createUi.componentTreeView

    def componentTreeWidget(self):
        return self.createUi.componentTreeView.treeWidget

    def mousePressEvent(self, event):
        utils.clearFocusWidgets()
        return super(HiveArtistUI, self).mousePressEvent(event)

    def enterEvent(self, event):
        self.checkRefresh()

        return super(HiveArtistUI, self).enterEvent(event)

    def checkRefresh(self):
        """ Check for refresh. Refresh if needed

        :return:
        """
        if self.core.needsRefresh():
            self.refreshUi()

    def rigModeToggled(self, buttonEvent):

        index = buttonEvent.index
        if index == 0:  # guides
            self.core.buildGuides()
        elif index == 1:
            self.core.toggleGuideControls()
        elif index == 2:
            self.core.buildSkeleton()
        elif index == 3:
            self.core.buildRigs()
        elif index == 4:
            self.core.polishRig()
        self.updateRigMode()

    def renameRigClicked(self):
        """ Rename

        :return:
        :rtype:
        """
        self.core.executeTool('renameRig')

    @staticmethod
    def loadingDecorator(func):
        """ Use this when you need a loading screen for the operation. Only works for HiveArtistUI instance..

        :return:
        :rtype:
        """

        @wraps(func)
        def _undofunc(self, *args, **kwargs):
            try:
                self.showLoadingWidget()
                return func(self, *args, **kwargs)
            finally:
                self.hideLoadingWidget()

        return _undofunc

    def showLoadingWidget(self):
        """ Show the loading widget

        :return:
        :rtype:
        """
        if self.loadingWidget:
            self.loadingWidget.show()
            utils.processUIEvents()

    def hideLoadingWidget(self):
        """ Hide loading widget

        :return:
        :rtype:
        """
        if self.loadingWidget:
            self.loadingWidget.hide()
            utils.processUIEvents()

    @profiling.fnTimer
    def refreshUi(self):
        """ Refreshes the UI.

        Clears out the rig and queries Hive for all the rigs and components.

        This is pretty process intensive so use sparingly. If we want to use this a little more
        often we'll have to optimize this.

        :return:
        """

        self.showLoadingWidget()
        try:
            self.core.refresh()
            rigNames = self.core.rigNames()
            if not self.rigBoxWgt:
                return

            currentText = self.rigBoxWgt.updateList(rigNames, keepSame=True)

            if currentText == "":
                self.rigBoxWgt.setCurrentIndex(0,
                                               update=False)  # We disable update here so we can do it manually later on
                currentText = self.rigBoxWgt.currentText()
                self.createUi.clearTree()

            rig = self.core.getRigModelByName(currentText)

            if rig is None:
                self.updateRigMode()
                self.updateHiveSettings()
                return

            self.core.setCurrentRig(rig)
            self.createUi.applyRig(rig)
            self.createUi.update()
            self.updateHiveSettings()
            self.updateRigMode()
        finally:
            self.setRigPolishedUi(False)  # temp
            self.hideLoadingWidget()

    def softRefreshComponents(self, componentModels):
        """

        :param componentModels:
        :return:
        """
        componentTree = self.uiInterface.tree()
        logger.debug("Soft refreshing components: '{}'".format(componentModels))

        for model in componentModels:
            componentWidget = componentTree.componentWidgetByModel(model)
            if componentWidget:
                componentWidget.updateUi()

    def enable(self):
        """ Enable the ui

        :return:
        """
        self.createUi.setEnabled(True)
        self.createUi.clearTree()

        self.rigModeButtons.setEnabled(True)
        self.verticalToolbar.hiveTools.setEnabled(True)

    def disable(self):
        """ Disable the ui

        :return:
        """
        self.createUi.setEnabled(False)
        self.createUi.clearTree()
        self.rigModeButtons.setEnabled(False)
        self.verticalToolbar.hiveTools.setEnabled(False)

    def addRig(self):
        """
        Adds a new rig to the scene and names it the default name given by Hive.

        :return:
        """

        rigModel = self.core.addRig(setCurrent=True)
        self.updateHiveSettings()
        self.setRigPolishedUi(False)

        return rigModel

    def rigAddedEvent(self):
        rigNames = self.core.rigNames()
        rigModel = self.core.currentRigContainer.rigModel
        if not rigModel:
            currentName = ""
        else:
            currentName = rigModel.name
        self.rigBoxWgt.updateList(rigNames, setTo=currentName)
        self.refreshUi()

    def deleteRig(self, name=""):
        """
        Prompts the user to confirm if we want to delete the current rig or not

        :param name:
        :return:
        """

        if not name:
            return

        ret = elements.MessageBox.showQuestion(title='Delete \'{}\'?'.format(name),
                                               message='Are you sure you want to delete \"{}\"?'.format(name),
                                               icon="Warning", buttonA="Yes", buttonB="Cancel")

        if ret == "A":
            # Get the rig to delete
            delRig = self.core.getRigContainerByName(name)

            if delRig != self.core.currentRigContainer:
                logger.warning("These two should be the same!")
                self.hideLoadingWidget()
                return None

            try:
                self.showLoadingWidget()
                self.core.deleteRig(delRig)
                self.refreshUi()
                self.updateHiveSettings()
            finally:
                self.hideLoadingWidget()
            return True

    def onComponentAdded(self):
        self.updateRigMode()

    def componentRemoved(self):
        self.updateRigMode()
        self.softRefreshComponents(self.core.currentRigContainer.componentModels.values())

    def resizeWindow(self):
        self.resize(self.width(), self.minimumSizeHint().height())

    def setRig(self, name, apply=True):
        """
        Set the current rig by name string
        :param name:
        :type name: basestring
        :return:
        """
        rigModel = self.core.setCurrentRigByName(name)
        if name != "" and apply:
            self.createUi.applyRig(rigModel)
            self.updateHiveSettings()
            self.updateRigMode()
            self.setRigPolishedUi(False)

    def updateRigMode(self):
        """ Updates the rig mode radio buttons

        :return:
        :rtype:
        """
        rigMode = self.core.rigMode()
        if rigMode == hiveapi.constants.GUIDES_STATE:
            self.rigModeButtons.setChecked(0)
            self.rigModeButtons.setEnabled(True)
            self.viewButton.setEnabled(True)
            self.rigModeButtons.buttons()[-2].setEnabled(True)
        elif rigMode == hiveapi.constants.CONTROL_VIS_STATE:
            self.rigModeButtons.setChecked(1)
            self.rigModeButtons.setEnabled(True)
            self.viewButton.setEnabled(True)
            self.rigModeButtons.buttons()[-2].setEnabled(True)
        elif rigMode == hiveapi.constants.SKELETON_STATE:
            self.rigModeButtons.setChecked(2)
            self.rigModeButtons.setEnabled(True)
            self.viewButton.setEnabled(True)
            self.rigModeButtons.buttons()[-2].setEnabled(True)
        elif rigMode == hiveapi.constants.RIG_STATE:
            self.rigModeButtons.setChecked(3)
            self.rigModeButtons.setEnabled(True)
            self.viewButton.setEnabled(True)
        elif rigMode == hiveapi.constants.POLISH_STATE:
            self.rigModeButtons.setChecked(4)
            self.rigModeButtons.setEnabled(True)
            self.viewButton.setEnabled(True)
            self.rigModeButtons.buttons()[-2].setEnabled(False)
        else:
            self.rigModeButtons.setChecked(0)
            self.rigModeButtons.setEnabled(False)

            self.viewButton.setEnabled(False)
        self.componentTreeView().onRigModeChanged(rigMode)

    def setRigPolishedUi(self, polished):
        """ Sets polished (Only the ui aspect!)

        :param polished:
        :type polished:
        :return:
        :rtype:
        """
        enabled = not polished
        try:
            self.rigMode.setEnabled(enabled)
        except AttributeError:
            return

        self.createUi.setEnabled(enabled)
        self.createUi.templateLibraryWgt.setEnabled(enabled)
