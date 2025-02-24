import os

from zoo.libs import iconlib
from zoo.libs.pyqt.extended import treeviewplus
from zoo.libs.pyqt.widgets import elements
from zoo.libs.pyqt.models import datasources
from zoo.libs.pyqt.models import treemodel
from zoo.libs.pyqt import utils
from zoo.libs.utils import output
from zoo.libs.utils import filesystem
from zoo.preferences.interfaces import coreinterfaces
from zoovendor.Qt import QtCore


class TemplateLibrary(treeviewplus.TreeViewPlus):
    def __init__(
        self, templateReg, title="templates", parent=None, expand=True, sorting=True
    ):
        super(TemplateLibrary, self).__init__(title, parent, expand, sorting)
        self.preference = coreinterfaces.coreInterface()
        self.preference.themeUpdated.connect(self.updateTheme)
        self._core = parent.core
        self._createView = parent
        self.templateRegistry = templateReg
        self._rootSource = TemplateDataSource({}, iconColor=[])

        self.treeView.setHeaderHidden(True)
        self.treeView.setFocusPolicy(
            QtCore.Qt.FocusPolicy.NoFocus
        )  # Remove dotted line on selection
        self.treeView.setIndentation(utils.dpiScale(10))
        self.setAlternatingColorEnabled(False)
        self.menuBtn = elements.IconMenuButton(parent=parent)
        self.templateModel = TemplateModel(
            self.templateRegistry, self._rootSource, parent=self
        )
        self.setModel(self.templateModel)
        self._setupLayout()
        self.refresh()
        self.contextMenuRequested.connect(self.onContextMenu)

    def updateTheme(self, event):
        """Update the theme

        :type event: preferences.interface.preference_interface.UpdateThemeEvent
        :return:
        :rtype:
        """
        iconColor = event.themeDict.MAIN_FOREGROUND_COLOR
        self.menuBtn.setIconByName("menudots", colors=iconColor, size=16)

    def _setupLayout(self):
        self.menuBtn.setFixedHeight(utils.dpiScale(20))
        self.menuBtn.setFixedWidth(utils.dpiScale(22))
        iconColour = self.preference.MAIN_FOREGROUND_COLOR
        self.menuBtn.setIconByName("menudots", colors=iconColour, size=16)
        self.toolbarLayout.setContentsMargins(*utils.marginsDpiScale(*(10, 6, 2, 0)))
        self.toolbarLayout.addWidget(self.menuBtn)

        self.menuBtn.addAction(
            "Save Rig As Template",
            connect=self.onSaveAll,
            icon=iconlib.iconColorized("hive_save"),
        )
        self.menuBtn.addAction(
            "Save Selected Components",
            connect=self.onSaveSelected,
            icon=iconlib.iconColorized("hive_save"),
        )
        self.menuBtn.addAction(
            "Rename Template",
            connect=self.onRenameTemplate,
            icon=iconlib.iconColorized("pencil"),
        )
        self.menuBtn.addAction(
            "Delete Template",
            connect=self.onDeleteTemplate,
            icon=iconlib.iconColorized("trash"),
        )
        self.menuBtn.addAction(
            "Update Rig from Template",
            connect=self.onUpdateFromTemplate,
            icon=iconlib.iconColorized("upload"),
        )
        self.menuBtn.addAction(
            "Open Template Location",
            connect=self.onBrowserToTemplates,
            icon=iconlib.iconColorized("globe"),
        )
        self.menuBtn.addSeparator()
        self.menuBtn.addAction(
            "Refresh",
            connect=self.onRefreshTemplates,
            icon=iconlib.iconColorized("reload"),
        )
        self.menuBtn.addAction(name="Expand All",
                               connect = self.expandAll,
                               icon=iconlib.iconColorized("sortDown"),
                               )
        self.menuBtn.addAction(
            name="Collapse All",
            connect=self.collapseAll,
            icon=iconlib.iconColorized("nextSml"),
        )

        self.treeView.itemDoubleClicked.connect(self.onDoubleClicked)

    def refresh(self):
        self._rootSource.setUserObjects([])
        self.setSortingEnabled(False)
        self.templateModel.reloadTemplates()
        self.templateModel.reload()

        self.setSortingEnabled(True)

    def onShowInExplorer(self, dataSource):
        filesystem.openLocation(dataSource.template["path"])
        output.displayInfo(
            "OS window opened to the Path: `{}` folder location".format(
                dataSource.template["path"]
            )
        )

    def onContextMenu(self, selection, menu):
        menu.setSearchVisible(False)
        menu.addActionExtended(
            "Rename",
            connect=self.onRenameTemplate,
            icon=iconlib.iconColorized("pencil"),
        )
        menu.addActionExtended(
            "Delete", connect=self.onDeleteTemplate, icon=iconlib.iconColorized("trash")
        )
        menu.addActionExtended(
            "Update Rig from Template",
            connect=self.onUpdateFromTemplate,
            icon=iconlib.iconColorized("upload"),
        )
        menu.addSeparator()
        menu.addActionExtended(
            "Open Folder Location",
            connect=self.onBrowserToTemplates,
            icon=iconlib.iconColorized("globe"),
        )

    def onBrowserToTemplates(self):
        selection = self.selectedItems()
        if not selection:
            output.displayWarning("Please Select at least one template.")
            return
        for selectedItem in selection:
            if isinstance(selectedItem, TemplateDataSource):
                path = selectedItem.template["path"]
            else:
                path = selectedItem.folderPath
            filesystem.openLocation(path)
            output.displayInfo(
                "OS window opened to the Path: `{}` folder location".format(
                    path
                )
            )

    def onDoubleClicked(self, index):
        item = self.templateModel.itemFromIndex(index)
        if isinstance(item, TemplateDataSource):
            self._createView.addTemplate(item.template["name"])

    def onSaveAll(self):
        self._core.executeTool("saveTemplate", {"exportAll": True})
        self.refresh()

    def onSaveSelected(self):
        self._core.executeTool("saveTemplate")
        self.refresh()

    def onDeleteTemplate(self):
        self._core.executeTool("deleteTemplate")
        self.refresh()

    def onRenameTemplate(self):
        self._core.executeTool("renameTemplate")
        self.refresh()

    def onRefreshTemplates(self):
        self._core.executeTool("refreshTemplates")
        self.refresh()

    def onUpdateFromTemplate(self):
        self._core.executeTool("updateRigUpdateTemplate")


class TemplateModel(treemodel.TreeModel):
    def __init__(self, templateRegistry, root, parent=None):
        super(TemplateModel, self).__init__(root, parent)
        self.themePref = coreinterfaces.coreInterface()
        self.templateRegistry = templateRegistry

    def reloadTemplates(self):
        col = self.themePref.HIVE_TEMPLATE_COLOR
        folderCol = (236, 236, 236)
        directories = self.templateRegistry.templateRoots
        folderItems = {}  # path: item
        for directory in directories:
            if not os.path.exists(directory):
                continue

            for root, dirs, files in os.walk(directory):
                parentItem = folderItems.get(root, self.root)
                for direct in dirs:
                    fullPath = os.path.join(root, direct)
                    source = TemplateFolderDataSource(
                        fullPath, model=self, parent=parentItem, iconColor=folderCol
                    )
                    folderItems[fullPath] = source
                    parentItem.addChild(source)
                    # add the folder to the tree
                for f in files:
                    fullPath = os.path.join(root, f)
                    template = self.templateRegistry.templateByPath(fullPath)
                    if not template:
                        continue
                    templateInfo = {
                        "name": template["name"],
                        "path": fullPath,
                        "icon": template.get("icon", ""),
                    }
                    source = TemplateDataSource(
                        templateInfo, model=self, parent=parentItem, iconColor=col
                    )
                    parentItem.addChild(source)


class TemplateFolderDataSource(datasources.BaseDataSource):
    _icon = None

    def __init__(self, folderPath, iconColor, headerText=None, model=None, parent=None):
        super(TemplateFolderDataSource, self).__init__(headerText, model, parent)
        self.folderPath = folderPath
        self._name = os.path.basename(self.folderPath)
        if TemplateFolderDataSource._icon is None:
            TemplateFolderDataSource._icon = iconlib.iconColorized(
                "closeFolder",
                size=utils.dpiScale(16),
                color=iconColor
            )

    def data(self, index):
        return self._name

    def icon(self, index):
        return TemplateFolderDataSource._icon

    def isEditable(self, index):
        return False

    def foregroundColor(self, index):
        """
        :param index: the column index
        :type index: int
        """
        return self.enabledColor

    def isFolder(self):
        return True


class TemplateDataSource(datasources.BaseDataSource):
    def __init__(self, template, iconColor, headerText=None, model=None, parent=None):
        super(TemplateDataSource, self).__init__(headerText, model, parent)
        self.template = template
        _icon = template.get("icon") or "template"
        iconName = _icon or "template"

        self._icon = iconlib.iconColorizedLayered(
            ["roundedsquarefilled", iconName],
            size=utils.dpiScale(16),
            colors=[iconColor],
            iconScaling=[1, 0.8],
        )

    def data(self, index):
        return self.template["name"].replace("component", "")

    def icon(self, index):
        return self._icon

    def isEditable(self, index):
        return False

    def foregroundColor(self, index):
        """
        :param index: the column index
        :type index: int
        """
        return self.enabledColor

    def isFolder(self):
        return False
