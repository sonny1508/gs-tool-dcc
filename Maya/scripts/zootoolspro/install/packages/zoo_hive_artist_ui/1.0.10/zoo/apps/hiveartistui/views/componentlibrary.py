import os
from zoo.libs import iconlib
from zoo.libs.pyqt import utils
from zoo.libs.pyqt.widgets import elements
from zoo.preferences.interfaces import coreinterfaces
from zoovendor.Qt import QtCore

from zoo.libs.pyqt.extended import treeviewplus
from zoo.libs.pyqt.models import datasources
from zoo.libs.pyqt.models import treemodel


BETA_LABEL = " (Beta)"

class ComponentLibrary(treeviewplus.TreeViewPlus):
    def __init__(
        self, componentReg=None,  title="components", parent=None, expand=True, sorting=True
    ):
        super(ComponentLibrary, self).__init__(title, parent, expand, sorting)
        self.preference = coreinterfaces.coreInterface()
        self.preference.themeUpdated.connect(self.updateTheme)
        self._core = parent.core
        self._createView = parent
        self.componentRegistry = componentReg
        self._rootSource = ComponentFolderDataSource("")

        self.treeView.setHeaderHidden(True)
        self.treeView.setFocusPolicy(
            QtCore.Qt.FocusPolicy.NoFocus
        )  # Remove dotted line on selection
        self.treeView.setIndentation(utils.dpiScale(10))
        self.setAlternatingColorEnabled(False)
        self.menuBtn = elements.IconMenuButton(parent=parent)
        self.componentModel = ComponentModel(
            self.componentRegistry, self._rootSource, parent=self
        )
        self.setModel(self.componentModel)
        self._setupLayout()
        self.refresh()
        self.expandAll()

    def updateTheme(self, event):
        """Update the theme

        :type event: preferences.interface.preference_interface.UpdateThemeEvent
        :return:
        :rtype:
        """
        iconColor = event.themeDict.MAIN_FOREGROUND_COLOR
        self.menuBtn.setIconByName("menudots", colors=iconColor, size=16)

    def refresh(self):
        self._rootSource.setUserObjects([])
        self.setSortingEnabled(False)
        self.componentModel.reloadComponents()
        self.componentModel.reload()

        self.setSortingEnabled(True)

    def _setupLayout(self):
        self.menuBtn.setFixedHeight(utils.dpiScale(20))
        self.menuBtn.setFixedWidth(utils.dpiScale(22))
        iconColour = self.preference.MAIN_FOREGROUND_COLOR
        self.menuBtn.setIconByName("menudots", colors=iconColour, size=16)
        self.toolbarLayout.setContentsMargins(*utils.marginsDpiScale(*(10, 6, 2, 0)))
        self.toolbarLayout.addWidget(self.menuBtn)
        self.treeView.itemDoubleClicked.connect(self.onDoubleClicked)

        self.menuBtn.addAction(name="Expand All",
                               connect = self.expandAll,
                               icon=iconlib.iconColorized("sortDown"),
                               )
        self.menuBtn.addAction(
            name="Collapse All",
            connect=self.collapseAll,
            icon=iconlib.iconColorized("nextSml"),
        )

    def onDoubleClicked(self, index):
        item = self.componentModel.itemFromIndex(index)
        if isinstance(item, ComponentDataSource):
            self._createView.createComponent(item.componentInfo["object"].definitionName)


class ComponentModel(treemodel.TreeModel):
    def __init__(self, componentRegistry, root, parent=None):
        """

        :param componentRegistry:
        :type componentRegistry: :class:`zoo.libs.hive.base.registry.ComponentRegistry
        :param root:
        :type root:
        :param parent:
        :type parent:
        """
        super(ComponentModel, self).__init__(root, parent)
        self.themePref = coreinterfaces.coreInterface()
        self.componentRegistry = componentRegistry

    def reloadComponents(self):
        col = self.themePref.HIVE_TEMPLATE_COLOR

        folderItems = {}
        for directory in self.componentRegistry.manager.basePaths:
            if not os.path.exists(directory):
                continue

            for root, dirs, files in os.walk(directory):
                parentItem = folderItems.get(os.path.basename(root), self.root)
                if "__pycache" in root:
                    continue

                for direct in dirs:
                    if "__pycache" in direct:
                        continue
                    if os.path.basename(direct) in folderItems:
                        continue

                    fullPath = os.path.join(root, direct).replace("\\", "/")
                    source = ComponentFolderDataSource(
                        fullPath, model=self, parent=parentItem
                    )
                    folderItems[os.path.basename(fullPath)] = source
                    parentItem.addChild(source)

                for f in files:
                    if not f.endswith(".py") or f == "__init__.py":
                        continue
                    fullPath = os.path.join(root, f).replace("\\", "/")
                    componentName, componentInfo = self.componentRegistry.componentDataByPath(fullPath)
                    if not componentInfo:
                        continue
                    uiData = componentInfo["object"].uiData
                    if not uiData["icon"]:
                        uiData["icon"] = componentInfo["object"].icon
                    if not uiData["iconColor"]:
                        uiData["iconColor"] = col
                    if not uiData["displayName"]:
                        uiData["displayName"] = componentName.replace("component", "")

                    source = ComponentDataSource(
                        name=componentName,
                        componentInfo=componentInfo,
                        uiData=uiData,
                        model=self, parent=parentItem
                    )
                    parentItem.addChild(source)

class ComponentFolderDataSource(datasources.BaseDataSource):
    _icon = None

    def __init__(self, folderPath, headerText=None, model=None, parent=None):
        super(ComponentFolderDataSource, self).__init__(headerText, model, parent)
        self.folderPath = folderPath
        self._name = os.path.basename(self.folderPath)
        if ComponentFolderDataSource._icon is None:
            ComponentFolderDataSource._icon = iconlib.iconColorized(
                "closeFolder",
                size=utils.dpiScale(16),
                color=(236, 236, 236)
            )

    def data(self, index):
        return self._name

    def icon(self, index):
        return ComponentFolderDataSource._icon

    def isEditable(self, index):
        return False


    def isFolder(self):
        return True


class ComponentDataSource(datasources.BaseDataSource):
    def __init__(self, name, componentInfo,uiData, headerText=None, model=None, parent=None):
        super(ComponentDataSource, self).__init__(headerText, model, parent)
        self.name = name
        self.componentInfo = componentInfo
        self.uiData = uiData
        self.label = uiData["displayName"]
        if self.componentInfo["object"].betaVersion:
            self.label += BETA_LABEL
        self._icon = iconlib.iconColorizedLayered(
            ["roundedsquarefilled", self.uiData["icon"]],
            size=utils.dpiScale(16),
            colors=[self.uiData["iconColor"]],
            iconScaling=[1, 0.8],
        )

    def data(self, index):
        return self.label

    def icon(self, index):
        return self._icon

    def isEditable(self, index):
        return False


    def isFolder(self):
        return False
