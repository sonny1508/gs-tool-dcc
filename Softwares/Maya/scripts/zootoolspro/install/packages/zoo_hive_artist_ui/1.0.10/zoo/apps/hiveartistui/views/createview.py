from zoo.apps.hiveartistui.registries import registry
from zoo.apps.hiveartistui.views import componentlibrary
from zoo.apps.hiveartistui.views import componenttree
from zoo.apps.hiveartistui.views import templatelibrary
from zoo.libs import iconlib
from zoo.libs.pyqt import utils
from zoo.libs.pyqt.widgets import elements
from zoovendor.Qt import QtCore, QtWidgets


class CreateView(QtWidgets.QWidget):
    _expandIcon = iconlib.icon("roundedsquare")
    _collapseIcon = iconlib.icon("minus")
    templateCreated = QtCore.Signal()


    def __init__(self, componentRegistry, templateRegistry, core, themePref, uiInterface, parent=None):
        """
        Maybe should move this back into artistui.py.

        :param componentRegistry:
        :param templateRegistry:
        :param core:
        :type core: :class:`zoo.apps.hiveartistui.artistuicore.HiveUICore`
        :param themePref:
        :param parent:
        :type parent: :class:`zoo.apps.hiveartistui.artistui.HiveArtistUI`
        """

        super(CreateView, self).__init__(parent)
        self.artistUi = parent

        self.componentLibraryLocked = False

        self.core = core

        self.uiInterface = uiInterface
        self.themePref = themePref

        self.componentRegistry = componentRegistry
        self.templateRegistry = templateRegistry
        self.componentMdlRegistry = registry.ComponentModelRegistry(self.componentRegistry)
        self.componentMdlRegistry.discoverComponents()

        self.componentLibraryWgt = componentlibrary.ComponentLibrary(componentReg=self.componentRegistry,
                                                                     parent=self)

        self.templateLibraryWgt = templatelibrary.TemplateLibrary(self.templateRegistry, parent=self)

        self.componentTreeView = componenttree.ComponentTreeView(self.componentRegistry, parent=self,
                                                                 componentRegistry=self.componentMdlRegistry,
                                                                 uicore=self.core)
        self.uiInterface.setTree(self.componentTreeView.treeWidget)

        self.initUi()

    def setEnabled(self, enabled):
        """ Set enabled

        :param enabled:
        :type enabled:
        :return:
        :rtype:
        """
        self.componentTreeView.setEnabled(enabled)
        self.componentLibraryWgt.setEnabled(enabled)

    def initUi(self):
        mainLayout = elements.vBoxLayout(self)
        toolbarLayout = elements.hBoxLayout()
        toolbarLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setContentsMargins(0, 0, 0, 0)

        leftLayoutSplitter = QtWidgets.QSplitter(self.parent())
        leftLayoutSplitter.setOrientation(QtCore.Qt.Vertical)
        leftLayoutSplitter.addWidget(self.componentLibraryWgt)
        leftLayoutSplitter.addWidget(self.templateLibraryWgt)
        leftLayoutSplitter.setHandleWidth(utils.dpiScale(3))

        rightWidget = QtWidgets.QWidget(self)
        rightLayout = QtWidgets.QVBoxLayout()
        rightLayout.setContentsMargins(0, 0, 0, 0)
        rightWidget.setLayout(rightLayout)

        splitter = QtWidgets.QSplitter(self.parent())
        splitter.addWidget(leftLayoutSplitter)
        splitter.addWidget(rightWidget)
        splitter.setHandleWidth(utils.dpiScale(3))

        splitter.setStretchFactor(0, 5) # Left Bar Size
        splitter.setStretchFactor(1, 10) # Middle Bar Size
        splitter.setStretchFactor(2, 5)

        toolbarLayout.addWidget(splitter)

        mainLayout.addLayout(toolbarLayout)
        rightLayout.addWidget(self.componentTreeView)

    def createComponent(self, cType="", name="", group=None, definition=None):
        """ Create Component

        Create the component in the HiveUICore and add it to the ComponentTreeView
        to see the widget visually

        :param cType:
        :param name:
        :param group:
        :return:
        """
        if not self.core.currentRigExists():
            self.core.addRig(setCurrent=True)

        self.core.addComponent(componentType=cType, definition=definition)

    def addTemplate(self, templateName):
        """ Looks for the template by templateName and adds the components in to the UI.

        :param templateName:
        :type templateName: str
        :return:
        """
        # template = self.templateRegistry.templatePath(templateName)
        try:
            self.artistUi.showLoadingWidget()
            self.core.executeTool("loadFromTemplate")
            self.templateCreated.emit()
        finally:
            self.artistUi.hideLoadingWidget()

    def clearTree(self):
        """ Clears all the tree nodes in the TreeWidget

        :return:
        """
        self.componentTreeView.treeWidget.clear()

    def applyRig(self, rig):
        """ Applies the rig to the component stack and anything else we need to do

        :param rig:
        :return:
        """
        self.componentTreeView.clear()
        self.componentTreeView.applyRig(rig)
        self.componentTreeView.sync()
