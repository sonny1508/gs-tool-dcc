from functools import partial

from zoo.apps.toolsetsui.ext.renderers import RendererMixin
from zoo.apps.toolsetsui.mixins import MiniBrowserMixin
from zoo.apps.toolsetsui.widgets.toolsetwidget import ToolsetWidget
from zoovendor.Qt import QtWidgets, QtCore

from zoo.libs.utils import output
from zoo.apps.model_assets import mayascenescore
from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.apps.toolsetsui.widgets.toolsetresizer import ToolsetResizer

from zoo.libs.maya.cmds.renderer.rendererconstants import RENDERER_ICONS_LIST_ALL

from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements
from zoo.core.util import zlogging
from zoo.libs import iconlib
from zoo.preferences.interfaces import coreinterfaces, assetinterfaces

from zoo.libs.pyqt.extended.imageview.models import mayafilemodel

logger = zlogging.getLogger(__name__)

DFLT_RNDR_LIST = ["Arnold", "Redshift", "Renderman", "VRay"]  # only used for filtering
UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1


class MayaScenes(ToolsetWidget, RendererMixin, MiniBrowserMixin):
    id = "mayaScenes"
    uiData = {"label": "Scenes Browser (.MA/.MB)",
              "icon": "maya",
              "tooltip": "Mini browser for Maya Scenes",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-maya-scenes/"
              }

    # ------------------------------------
    # START UP
    # ------------------------------------

    def preContentSetup(self):
        """First code to run"""
        self.toolsetWidget = self  # needed for callback decorators
        self.setAssetPreferences(assetinterfaces.mayaScenesInterface().scenesAssets)
        self.generalPrefs = coreinterfaces.generalInterface()
        self.core = mayascenescore.MayaScenesCore(self)
        self.initRendererMixin(disableVray=False, disableMaya=False)  # sets the renderer
        self.properties.rendererIconMenu.value = 0  # Hardcode the renderer to always use all

    def contents(self):
        """The UI Modes to build, compact, medium and or advanced """
        return [self.initCompactWidget()]

    def initCompactWidget(self):
        """Builds the Compact GUI (self.compactWidget) """
        self.compactWidget = GuiCompact(parent=self, properties=self.properties, toolsetWidget=self,
                                        core=self.core)
        return self.compactWidget

    def postContentSetup(self):
        """Last of the initialize code"""
        self.setMiniBrowsers([w.miniBrowser for w in self.widgets()])
        self.uiconnections()  # Connects buttons and other widgets
        self.setRenderer(updateAllUIs=False)

    def currentWidget(self):
        """ Current active widget

        :return:
        :rtype:  AllWidgets
        """
        return super(MayaScenes, self).currentWidget()

    def widgets(self):
        """ List of widgets

        :return:
        :rtype: list[AllWidgets]
        """
        return super(MayaScenes, self).widgets()

    # ------------------------------------
    # PROPERTIES
    # ------------------------------------

    def initializeProperties(self):
        """Needed for setting self.properties.rendererIconMenu.value on startup before UI is built

        self.properties.rendererIconMenu.value is set with:

            self.initRendererMixin(disableVray=False, disableMaya=False)
        """
        return [{"name": "rendererIconMenu", "label": "", "value": "Arnold"}]

    # ------------------------------------
    # OPEN FUNCTIONS AND HELP/BROWSE
    # ------------------------------------

    @toolsetwidget.ToolsetWidget.undoDecorator
    def loadScene(self, assetName=""):
        """ Imports the zooScene asset given the GUI settings
        """
        self.core.loadScene(assetName)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def importScene(self, assetName=""):
        """ Imports the zooScene asset given the GUI settings
        """
        self.core.importScene(assetName)

    def browseDirectory(self):
        self.currentWidget().miniBrowser.browseSelected()

    # ------------------------------------
    # CHANGE RENDERER
    # ------------------------------------

    def global_receiveRendererChange(self, renderer, ignoreVRay=False, ignoreMaya=False):
        """Override this method as we don't want it to change when the renderer is changed in other UIs"""
        pass

    # ------------------------------------
    # CONNECTIONS
    # ------------------------------------

    def browserSelectionChanged(self, image, item):
        """Runs when the selection is changed

        :param image:
        :type image:
        :param item:
        :type item: zoo.libs.pyqt.extended.imageview.items.BaseItem
        :return:
        :rtype:
        """
        super(MayaScenes, self).browserSelectionChanged(image, item)
        self.core.selectedItem = item

    def uiconnections(self):
        """Hooks up the actual button/widgets functionality
        """
        logger.debug("connections()")
        super(MayaScenes, self).uiconnections()

        for w in self.widgets():
            # dots menu viewer
            w.miniBrowser.dotsMenu.applyAction.connect(self.loadScene)
            # w.miniBrowser.dotsMenu.createAction.connect(partial(self.setEmbedVisible, vis=True))
            w.miniBrowser.dotsMenu.createAction.connect(self.saveScene)
            w.miniBrowser.dotsMenu.refreshAction.connect(self.refreshThumbs)
            w.miniBrowser.dotsMenu.deleteAction.connect(self.deleteScene)
            w.miniBrowser.dotsMenu.actionTriggered.connect(self.actionTriggered)
            # Thumbnail viewer
            w.browserModel.doubleClicked.connect(self.loadScene)
            # w.browserModel.itemSelectionChanged.connect(self.selectionChanged)
            # Change renderer
            w.rendererIconMenu.actionTriggered.connect(self.setRenderer)
            # Buttons
            w.openSceneBtn.clicked.connect(self.loadScene)
            w.saveBtn.clicked.connect(self.saveScene)
            w.importSceneBtn.clicked.connect(self.importScene)
            w.referenceSceneBtn.clicked.connect(self.referenceScene)
            w.openReadmeBtn.clicked.connect(self.core.openReadme)
            w.openHelpBtn.clicked.connect(self.core.openHelp)
            w.browseDirBtn.clicked.connect(self.browseDirectory)
            # Right Click Save Menu ------------
            w.saveBtn.addAction("Export Selected As .MA",
                                mouseMenu=QtCore.Qt.RightButton,
                                icon=iconlib.icon("save"),
                                connect=partial(self.exportSelected, saveType="mayaAscii"))
            w.saveBtn.addAction("Export Selected As .MB",
                                mouseMenu=QtCore.Qt.RightButton,
                                icon=iconlib.icon("save"),
                                connect=partial(self.exportSelected, saveType="mayaBinary"))
            w.saveBtn.addSeparator(mouseMenu=QtCore.Qt.RightButton)
            w.saveBtn.addAction("Save Scene As .MA",
                                mouseMenu=QtCore.Qt.RightButton,
                                icon=iconlib.icon("save"),
                                connect=partial(self.saveScene, saveType="mayaAscii"))
            w.saveBtn.addAction("Save Scene As .MB",
                                mouseMenu=QtCore.Qt.RightButton,
                                icon=iconlib.icon("save"),
                                connect=partial(self.saveScene, saveType="mayaBinary"))

    @toolsetwidget.ToolsetWidget.undoDecorator
    def referenceScene(self):
        """ Reference the selected thumbnail
        """
        self.core.referenceScene()

    def actionTriggered(self, action, mouseMenu):
        """

        :param action:
        :type action: :class:`zoo.libs.pyqt.extended.searchablemenu.action.TaggedAction`
        """
        if action.data() == "import":
            self.importScene()
        elif action.data() == "reference":
            self.referenceScene()
        elif action.data() == "export":
            self.exportSelected()
        elif action.data() == "help":
            self.core.openHelp()
        elif action.data() == "readme":
            self.core.openReadme()

    def saveScene(self, saveType="mayaAscii"):
        """ Save Scene

        :param saveType: "mayaAscii" or "mayaBinary"
        :type saveType: str
        """
        directory = self.currentWidget().miniBrowser.getSaveDirectory()
        if directory:
            self.core.saveScene(directory, type_=saveType)
            self.refreshThumbs()

    def deleteScene(self):
        """Deletes specified shape/design from disk, currently Zoo internally and not to zoo_preferences"""
        designName = self.currentWidget().browserModel.currentItem

        okState = self.deleteScenePopup(designName)
        if not okState:  # Cancel
            return
        # Delete file and dependency files
        filesFullPathDeleted = self.core.deleteScene(designName)
        self.refreshThumbs()
        output.displayInfo("Success, File/Folder/s Deleted: {}".format(filesFullPathDeleted))

    def deleteScenePopup(self, shapeName):
        """Delete control curve popup window asking if the user is sure they want to delete?

        :param shapeName: The name of the shape/design to be deleted from the library on disk
        :type shapeName: zoo.libs.pyqt.extended.imageview.items.BaseItem
        :return okState: Ok button was pressed
        :rtype okState: bool
        """
        message = "Are you sure you want to delete '{0}' from the Zoo Scene Library?\n" \
                  "This will permanently delete the file '{0}' from disk.".format(shapeName.fileNameExt())
        okState = elements.MessageBox.showOK(title="Delete Scene From Library",
                                             parent=None, message=message)
        return okState

    def exportSelected(self, saveType="mayaAscii"):
        """ Export selected

        :return:
        """
        directory = self.currentWidget().miniBrowser.getSaveDirectory()
        if directory:
            self.core.exportSelected(directory, type_=saveType)
            self.refreshThumbs()


class AllWidgets(QtWidgets.QWidget):
    """Create all the widgets for all GUIs, compact and advanced etc"""

    def __init__(self, parent=None, properties=None, uiMode=None, toolsetWidget=None, core=None):
        """Builds the main widgets for the IBL light UIs, no layouts and no connections:

            uiMode - 0 is compact (UI_MODE_COMPACT)
            uiMode - 1 is medium (UI_MODE_MEDIUM)
            ui mode - 2 is advanced (UI_MODE_ADVANCED)

        properties is the list(dictionaries) used to set logic and pass between the different UI layouts
        such as compact/adv etc

        :param parent: the parent of this widget
        :type parent: qtObject
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: list[dict]
        :param uiMode: 0 is compact ui mode, 1 is medium ui mode, 2 is advanced ui mode
        :type uiMode: int
        :param toolsetWidget: the widget of the toolset
        :type toolsetWidget: qtObject
        :param core: directory path of the light preset zooScene files
        :type core: `zoo.apps.model_assets.mayascenescore.MayaScenesCore`
        """
        super(AllWidgets, self).__init__(parent=parent)
        self.savedThumbHeight = None
        self.toolsetWidget = toolsetWidget
        self.properties = properties
        self.uiMode = uiMode
        self.core = core
        # Thumbnail Viewer --------------------------------------------
        # viewer widget and model
        sceneAssets = self.core.mayaScenesPrefs.scenesAssets
        uniformIcons = sceneAssets.browserUniformIcons()
        directories = sceneAssets.browserFolderPaths()

        self.miniBrowser = elements.MiniBrowser(parent=self,
                                                toolsetWidget=self.toolsetWidget,
                                                columns=3,
                                                fixedHeight=382,
                                                uniformIcons=uniformIcons,
                                                itemName="Scene",
                                                applyText="Load Scene",
                                                createText="Save",
                                                applyIcon="maya",
                                                snapshotActive=True,
                                                clipboardActive=True,
                                                newActive=False,
                                                selectDirectoriesActive=True,

                                                )
        self.miniBrowser.dotsMenu.setDirectoryActive(False)  # todo: remove this since we use multi directories now
        self.miniBrowser.dotsMenu.insertActionIndex(1,
                                                    "Import Scene",
                                                    icon="arrowCircleDown",
                                                    data="import")
        self.miniBrowser.dotsMenu.insertActionIndex(2,
                                                    "Reference Scene",
                                                    icon="arrowCircleDown",
                                                    data="reference")
        self.miniBrowser.dotsMenu.insertActionIndex(3,
                                                    "Open Help - Web Page",
                                                    icon="help",
                                                    data="help")
        self.miniBrowser.dotsMenu.insertActionIndex(4,
                                                    "Open Readme - PDF",
                                                    icon="information",
                                                    data="readme")

        self.miniBrowser.dotsMenu.setDeleteActive(True)
        self.miniBrowser.dotsMenu.setCreateActive(True)
        self.miniBrowser.dotsMenu.insertActionIndex(6,
                                                    "Export Selected",
                                                    icon="save",
                                                    data="export")
        self.miniBrowser.dotsMenu.setRenameActive(False)
        # self.miniBrowser.dotsMenu.setDirectoryActive(True)
        self.miniBrowser.dotsMenu.setSnapshotActive(True)
        self.miniBrowser.filterMenu.setEnabled(False)

        self.miniBrowser.filterMenu.hide()

        self.browserModel = mayafilemodel.MayaFileModel(self.miniBrowser,
                                                        directories=directories,
                                                        uniformIcons=uniformIcons,
                                                        assetPreference=self.core.mayaScenesPrefs.scenesAssets)

        self.miniBrowser.setModel(self.browserModel)
        self.resizerWidget = ToolsetResizer(toolsetWidget=self.toolsetWidget, target=self.miniBrowser)
        # Open File Button --------------------------------------
        tooltip = "Opens the selected file (also double-click)."
        self.openSceneBtn = elements.styledButton("Open",
                                                  icon="checkMark",
                                                  toolTip=tooltip,
                                                  style=uic.BTN_DEFAULT)
        # Import File Button --------------------------------------
        tooltip = "Imports the selected file into the current scene."
        self.importSceneBtn = elements.styledButton("Import",
                                                    icon="arrowCircleDown",
                                                    toolTip=tooltip,
                                                    style=uic.BTN_DEFAULT)
        # Open File Button --------------------------------------
        tooltip = "Reference the selected file into the current scene."
        self.referenceSceneBtn = elements.styledButton("Ref",
                                                       icon="arrowCircleDown",
                                                       toolTip=tooltip,
                                                       style=uic.BTN_DEFAULT)
        # Open Readme Button --------------------------------------
        tooltip = "Opens the readMe.pdf for the selected file."
        self.openReadmeBtn = elements.styledButton("",
                                                   icon="information",
                                                   toolTip=tooltip,
                                                   style=uic.BTN_DEFAULT)
        self.openReadmeBtn.setVisible(False)  # hidden
        # Open Help Button --------------------------------------
        tooltip = "Opens the help file for the selected file."
        self.openHelpBtn = elements.styledButton("",
                                                 icon="help",
                                                 toolTip=tooltip,
                                                 style=uic.BTN_DEFAULT)
        self.openHelpBtn.setVisible(False)  # hidden
        # Open Directory Browse Button --------------------------------------
        tooltip = "Browse the scene file/s on disk for the selected file."
        self.browseDirBtn = elements.styledButton("",
                                                  icon="globe",
                                                  toolTip=tooltip,
                                                  style=uic.BTN_DEFAULT)
        # Save Scene Button --------------------------------------
        tooltip = "Saves the current scene to disk and creates a new thumbnail."
        self.saveBtn = elements.styledButton("",
                                             icon="save",
                                             toolTip=tooltip,
                                             style=uic.BTN_DEFAULT)
        # Renderer Button --------------------------------------
        toolTip = "Show only files of this renderer type, note that files unrelated to a renderer are kept. \n\n" \
                  "Files are excluded by their file suffix `*_redshift` \n" \
                  "Renderer of the file suffix should be all lowercase."
        self.rendererIconMenu = elements.iconMenuButtonCombo(RENDERER_ICONS_LIST_ALL,
                                                             self.properties.rendererIconMenu.value,
                                                             toolTip=toolTip)
        # self.rendererIconMenu.setEnabled(False)

    def embedWindowVisChanged(self, visibility):
        self.toolsetWidget.updateTree(delayed=True)


class GuiCompact(AllWidgets):
    def __init__(self, parent=None, properties=None, uiMode=UI_MODE_COMPACT, toolsetWidget=None, core=None):
        """Builds the compact version of GUI, sub classed from AllWidgets() which creates the widgets:

            default uiMode - 1 is compact (UI_MODE_COMPACT)

        :param parent: the parent of this widget
        :type parent: qtObject
        :param properties: Special dictionary which tracks the properties of each widget for the GUI
        :type properties: list[dict]
        :param uiMode: The UI mode to build, either UI_MODE_COMPACT = 0 or UI_MODE_ADVANCED = 1
        :type uiMode: int
        :param toolsetWidget: The instance of the toolsetWidget class, needed for setting properties.
        :type toolsetWidget: object
        """
        super(GuiCompact, self).__init__(parent=parent, properties=properties,
                                         uiMode=uiMode, toolsetWidget=toolsetWidget, core=core)
        # Main Layout
        mainLayout = elements.vBoxLayout(self, margins=(uic.WINSIDEPAD, uic.WINTOPPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=0)
        # Renderer layout
        rendererLayout = elements.hBoxLayout(spacing=uic.SPACING)
        rendererLayout.addWidget(self.openSceneBtn, 10)
        rendererLayout.addWidget(self.importSceneBtn, 10)
        rendererLayout.addWidget(self.referenceSceneBtn, 10)
        rendererLayout.addWidget(self.openReadmeBtn, 1)
        rendererLayout.addWidget(self.saveBtn, 1)
        rendererLayout.addWidget(self.openHelpBtn, 1)
        rendererLayout.addWidget(self.browseDirBtn, 1)
        rendererLayout.addWidget(self.rendererIconMenu, 1)
        # Add to main layout
        mainLayout.addWidget(self.miniBrowser)
        mainLayout.addWidget(self.resizerWidget)
        mainLayout.addLayout(rendererLayout)
        mainLayout.addStretch(1)
