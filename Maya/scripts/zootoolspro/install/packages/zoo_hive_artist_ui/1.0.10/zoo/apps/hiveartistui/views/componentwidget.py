from functools import partial

from zoo.apps.hiveartistui import model, hivetool
from zoo.apps.hiveartistui.views import componentsettings
from zoo.apps.hiveartistui.views.widgethelpers import SideNameWidget
from zoo.core.util import zlogging
from zoo.libs import iconlib
from zoo.libs.hive import api
from zoo.libs.pyqt import utils, uiconstants
from zoo.libs.pyqt.extended import searchablemenu
from zoo.libs.pyqt.widgets import buttons
from zoo.libs.pyqt.widgets import elements
from zoo.libs.pyqt.widgets import iconmenu, stackwidget
from zoo.preferences.interfaces import coreinterfaces
from zoovendor.Qt import QtWidgets, QtCore

logger = zlogging.getLogger(__name__)


class ComponentWidget(stackwidget.StackItem):
    syncRequested = QtCore.Signal()
    componentRenamed = QtCore.Signal(object, object)

    def __init__(self, componentModel, parent, core):
        """ A Component widget instance is used to create a custom widget container for
        a single component.


        :type core: zoo.apps.hiveartistui.artistuicore.HiveUICore
        :type parent: zoo.apps.hiveartistui.views.componenttree.ComponentTreeWidget
        :param componentModel: The component Model
        :type componentModel: model.ComponentModel
        """

        self.model = componentModel
        self.titleDefaultObjName = ""
        self.themePref = coreinterfaces.coreInterface()
        self.tree = parent
        self.core = core
        self._contextMenu = None
        self.componentMenu = None  # type: iconmenu.IconMenuButton
        self.mainFrame = None  # type: QtWidgets.QFrame
        self.hiveTools = []  # type: list[hivetool.HiveTool]
        self.componentSettings = None  # type: componentsettings.ComponentSettingsWidget

        super(ComponentWidget, self).__init__(title=componentModel.name, collapsed=False,
                                              icon=self.model.componentIcon,
                                              collapsable=True, parent=parent,
                                              startHidden=False, shiftArrowsEnabled=False,
                                              deleteButtonEnabled=True,
                                              itemIconSize=14)

        self.setItemIconColor(self.themePref.HIVE_COLOR)
        self.toggleExpandRequested.connect(self._onExpandRequested)

    def initUi(self):
        """ Init UI

        :return:
        """
        super(ComponentWidget, self).initUi()
        self.mainFrame = QtWidgets.QFrame(self)

        col = self.themePref.STACKITEM_HEADER_FOREGROUND
        self.componentMenu = iconmenu.IconMenuButton(parent=self)
        self.componentMenu.setIconByName("menudots", colors=col, size=15)
        self.componentMenu.menuAboutToShow.connect(self.updateToolIcons)

        # The main frame where component attributes are displayed
        # sideCombo = elements.ComboBoxRegular(parent=self, items=["L", "R", "Hello"])
        self.sideCombo = SideNameWidget(self.model, parent=self, showLabel=False, showArrow=False)
        self.sideCombo.renamed.connect(self._onSideNameChanged)
        self.sideCombo.setMinimumWidth(50)
        self.rigModeWarningLabel = elements.IconLabel(iconlib.iconColorizedLayered("warning", utils.dpiScale(32),
                                                                                   colors=(220, 210, 0)),
                                                      text="Edits can only be made in Guides Mode.",
                                                      parent=self, enableMenu=False,
                                                      )
        font = self.rigModeWarningLabel.font()
        font.setItalic(True)
        font.setBold(True)
        self.rigModeWarningLabel.setFont(font)
        self.rigModeWarningLabel.label.setEnabled(False)

        self.contentsLayout.addWidget(self.rigModeWarningLabel)
        self.contentsLayout.addWidget(self.mainFrame)
        # Maybe should be put into separate class
        self.titleFrame.extrasLayout.setSpacing(0)
        self.titleFrame.extrasLayout.addWidget(self.componentMenu)
        self.titleFrame.deleteBtn.setIconSize(QtCore.QSize(12, 12))
        self.titleFrame.horizontalLayout.insertWidget(4, self.sideCombo)

        self.titleDefaultObjName = self.titleFrame.objectName()
        self.buildHeaderTools()

        self.componentMenu.setMenu(self.contextMenu())
        self.toggleContents()
        self.onRigModeChanged(self.core.rigMode())

    def buildHeaderTools(self):
        """ Build the header tools seen in the widget header (ie visibility, solo etc)

        :return:
        :rtype:
        """
        tools = reversed(self.model.toolLayout())
        for toolObj, toolType, variantId in self.core.toolRegistry.iterToolsFromLayout(tools):
            if toolType == "PLUGIN":
                tool = toolObj(logger, uiInterface=self.core.uiInterface)
                self.addHeaderTool(tool, variantId)
            elif toolType == "SEPARATOR":
                pass  # todo: add vertical separator

    def addHeaderTool(self, hiveTool, variantId):
        """ Add new tool button by hive tool

        :param hiveTool:
        :type hiveTool: hivetool.HiveTool
        :return:
        :rtype:
        """
        uiData = hiveTool.uiData
        btn = elements.styledButton(parent=self, icon=uiData["icon"], style=uiconstants.BTN_TRANSPARENT_BG)
        self.titleFrame.extrasLayout.insertWidget(0, btn)
        btn.leftClicked.connect(partial(self._executeTool, hiveTool, variantId))
        hiveTool.refreshRequested.connect(self.syncRequested.emit)
        hiveTool.attachedWidget = btn

        btn.setProperty("tool", hiveTool)
        self.hiveTools.append(hiveTool)

        return btn

    def contextMenu(self):
        """ Build the context menu

        :return:
        :rtype:
        """
        if self._contextMenu is None:

            menu = searchablemenu.SearchableMenu()
            menu.setSearchVisible(False)
            for toolObj, toolType, variantId in self.core.toolRegistry.iterToolsFromLayout(self.model.menuActions()):
                if toolType == "PLUGIN":
                    tool = toolObj(logger, uiInterface=self.core.uiInterface)
                    self.addMenuActionTool(tool, menu)
                elif toolType == "SEPARATOR":
                    menu.addSeparator()

            self._contextMenu = menu

            menu.setToolTipsVisible(True)

        return self._contextMenu

    def addMenuActionTool(self, hiveTool, menu):
        """

        :param hiveTool:
        :type hiveTool: hivetool.HiveTool
        :param menu:
        :type menu: searchablemenu.SearchableMenu

        :return:
        :rtype:
        """

        uiData = hiveTool.uiData
        action = QtWidgets.QAction(self)
        action.setText(uiData["label"])

        hiveTool.refreshRequested.connect(self.syncRequested.emit)  # do we need this here?
        action.setProperty("tool", hiveTool)

        # Icon
        try:
            icon = iconlib.iconColorizedLayered(uiData["icon"])
            action.setIcon(icon)
        except AttributeError:
            pass

        menu.addAction(action)
        self.hiveTools.append(hiveTool)
        hiveTool.attachedWidget = action
        action.triggered.connect(partial(self._executeTool, hiveTool))

    def _executeTool(self, tool, variantId=None):
        """ Execute Hive tool.
        Todo bit redundant, maybe replace this with self.core version

        :param tool:
        :type tool: hivetool.HiveTool
        :return:
        :rtype:
        """
        # override the tool models to be the current selection
        tool.setSelected(self.core.selection)
        # set the current model
        tool.model = self.model
        try:
            tool.process(variantId)
        finally:
            utils.singleShotTimer(self.sync)

    def connections(self):
        self.titleFrame.lineEdit.editingFinished.connect(self.stackTitleEdited)
        self.syncRequested.connect(self.sync)
        super(ComponentWidget, self).connections()

    def onRigModeChanged(self, rigMode):

        if rigMode == api.constants.GUIDES_STATE:  # guides
            self.mainFrame.setEnabled(True)
            self.rigModeWarningLabel.setVisible(False)
        else:
            self.mainFrame.setEnabled(False)
            self.rigModeWarningLabel.setVisible(True)

    def sync(self):
        """ Synchronize the UI with the rig in the scene

        :return:
        """
        logger.debug("Syncing UI with the scene")
        self.widgetHide(self.model.isHidden())
        self.tree.updateSelectionColours()
        self.updateToolIcons()
        if self.collapsed:
            return
        self.componentSettings.updateUi()

    def updateToolIcons(self):
        """ Update the tool toggle icons

        :return:
        :rtype:
        """
        # the hive tools and their toggle expressions
        toolIcons = []  # [(basecomponenttools.ToggleVisibility, self.model.isHidden())]

        # Update tool icons
        for toolWidget, hiveTool in [(ht.attachedWidget, ht) for ht in self.hiveTools]:
            # For tool buttons
            for hiveToolType, iconToggle in toolIcons:
                if isinstance(hiveTool, hiveToolType):
                    colors = hiveTool.uiData["iconColorToggled"] if iconToggle else hiveTool.uiData["iconColor"]
                    if isinstance(toolWidget, buttons.ExtendedButton):  # Set icon differently for extended button
                        toolWidget.setIconByName(hiveTool.uiData["icon"], colors=colors)
                    elif isinstance(toolWidget, QtWidgets.QAction):  # QAction uses setIcon
                        toolWidget.setIcon(iconlib.iconColorizedLayered(hiveTool.uiData["icon"], colors=colors))

    def mousePressEvent(self, event):
        """
        Mouse press event. Let the mouse click through to the widget behind it
        :param event:
        :return:
        """
        event.ignore()

    def mouseReleaseEvent(self, event):
        """ Mouse release event
        :param event:
        :return:
        """
        event.ignore()

    def widgetHide(self, hide):
        """ The visual behaviour to show that the componentWidget is hidden

        :param hide:
        :return:
        """
        if hide:
            self.titleFrame.setObjectName("diagonalBG")
        else:
            self.titleFrame.setObjectName(self.titleDefaultObjName)

        # refreshes the style updates the style
        self.titleFrame.setStyle(self.titleFrame.style())

    def stackTitleEdited(self):
        """ Rename component on stackTitle edited
        :return:
        """
        before = self.model.name
        after = str(self.sender().text())
        self.renameComponent(after)
        self.componentRenamed.emit(before, after)

    def renameComponent(self, name):
        """ Rename component based on the LineEdit title.
        :return:
        """
        self.model.name = name

    def _onSideNameChanged(self, newSide):
        self.core.executeTool("setComponentSide", args={"componentModel": self.model, "side": newSide})

    def copy(self):
        """ Returns a copy of itself

        :return:
        :rtype: ComponentWidget
        """
        # This seems a bit hacky, use of reflection
        CurrentType = type(self)
        ret = CurrentType(self.model, self.parent(), self.core)
        ret.sync()

        return ret

    @property
    def componentType(self):
        """
        Get component type from the componentModel
        :return:
        """
        return self.model.componentType

    @property
    def name(self):
        return self.model.name

    def initSettingsWidget(self):
        """ The Component widget which will be shown within the main ui . the widget should only
        contain minimal amount of information eg. parent component, join count etc
        """
        layout = elements.hBoxLayout(parent=self.mainFrame)
        self.componentSettings = self.model.createWidget(componentWidget=self, parentWidget=self)

        if self.componentSettings is None:
            logger.debug("No Custom widget supplied by client model!")
            return
        layout.addWidget(self.componentSettings)
        return self.componentSettings

    def updateUi(self):
        """ Get all the information of the ComponentModel and update the ComponentWidget ui
        widgets.
        :return:
        """

        if self.collapsed:
            return
        if self.componentSettings is not None:
            self.componentSettings.updateUi()

    def _onExpandRequested(self, collapsed):
        """ used to bypass limitations with expandRequest signal which gets triggered before expanding
        """
        if not collapsed:
            if self.componentSettings is None:
                componentSettings = self.initSettingsWidget()
                componentSettings.updateUi()
            else:
                self.componentSettings.updateUi()


class ComponentGroupBox(QtWidgets.QGroupBox):
    """ Replaces the QGroupBox to Allow the user to select through """

    def __init__(self, title="", parent=None):
        super(ComponentGroupBox, self).__init__(title, parent)
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
        self.setAcceptDrops(False)

    def mousePressEvent(self, event):
        event.ignore()
