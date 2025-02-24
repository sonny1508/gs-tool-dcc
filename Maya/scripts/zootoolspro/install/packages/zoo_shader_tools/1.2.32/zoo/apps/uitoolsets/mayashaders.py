import os
import webbrowser
from functools import partial

from zoo.core.util import zlogging
from zoo.preferences.interfaces import coreinterfaces, shaderinterfaces
from zoo.libs import iconlib
from zoo.libs.utils import filesystem, output

from zoovendor.Qt import QtCore, QtWidgets
from zoo.apps.toolsetsui.mixins import MiniBrowserMixin
from zoo.apps.toolsetsui.widgets.toolsetwidget import ToolsetWidget
from zoo.apps.toolsetsui.ext.renderers import RendererMixin
from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.apps.toolsetsui.widgets.toolsetresizer import ToolsetResizer

from zoo.libs.pyqt.extended.imageview.models.mayafilemodel import MayaFileModel
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements

from zoo.libs.maya.cmds.shaders import shaderutils
from zoo.libs.maya.cmds.renderer.rendererconstants import RENDERER_ICONS_LIST_ALL

from zoo.apps.shader_tools import mayashaderscore

logger = zlogging.getLogger(__name__)


DFLT_RNDR_LIST = ["Arnold", "Redshift", "Renderman", "VRay"]  # only used for filtering
DFLT_RNDR_MODES = [("arnold", "Arnold"), ("redshift", "Redshift"), ("renderman", "Renderman")]
UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1

mayaShadersIcon = "mayaShaders"


class MayaShaders(ToolsetWidget, RendererMixin, MiniBrowserMixin):
    id = "mayaShaders"
    uiData = {"label": "Shader Presets (.MA/.MB)",
              "icon": mayaShadersIcon,
              "tooltip": "Mini browser for Maya Shaders",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-maya-shaders/"
              }

    # ------------------------------------
    # START UP
    # ------------------------------------

    def preContentSetup(self):
        """First code to run"""
        self.toolsetWidget = self  # needed for callback decorators and resizer
        self.generalPrefs = coreinterfaces.generalInterface()
        self.initRendererMixin()
        self.properties.rendererIconMenu.value = 0  # Hardcode the renderer to always use all

        self.setAssetPreferences(shaderinterfaces.shaderInterface().mayaShaderAssets)

        self.copiedAttributes = dict()  # for copy paste shaders
        self.copiedShaderName = ""  # for copy paste shaders
        self.shadersCore = mayashaderscore.MayaShadersCore(self)

    def contents(self):
        """The UI Modes to build, compact, medium and or advanced """
        return [self.initCompactWidget()]

    def initCompactWidget(self):
        """Builds the Compact GUI (self.compactWidget) """
        self.compactWidget = GuiCompact(parent=self, properties=self.properties, toolsetWidget=self)
        return self.compactWidget

    def postContentSetup(self):
        """Last of the initialize code"""
        self.setRenderer(updateAllUIs=False)  # Updates the renderer filtering on startup.
        self.setMiniBrowsers([w.miniBrowser for w in self.widgets()])
        self.uiconnections()  # Connects buttons and other widgets

    def currentWidget(self):
        """ Current active widget

        :return:
        :rtype:  AllWidgets
        """
        return super(MayaShaders, self).currentWidget()

    def widgets(self):
        """ List of widgets

        :return:
        :rtype: list[AllWidgets]
        """
        return super(MayaShaders, self).widgets()

    # ------------------------------------
    # PROPERTIES
    # ------------------------------------

    def initializeProperties(self):
        return [{"name": "rendererIconMenu", "label": "", "value": "Arnold"}]

    # ------------------------------------
    # CHANGE RENDERER
    # ------------------------------------

    def global_receiveRendererChange(self, renderer, ignoreVRay=False, ignoreMaya=False):
        """Override this method as we don't want it to change when the renderer is changed in other UIs"""
        pass

    # ------------------------------------
    # PATH HELPER FUNCTIONS
    # ------------------------------------

    def filePath(self, message=True):
        """Returns the file path of the currently selected thumbnails' corresponding .ma or .mb image eg:

            C:\\Users\\name\\Documents\\zoo_preferences\\assets\\maya_scenes\\croc_rig\\animation_croc_walkAndTurn.ma

        :param message: Report any messages to the user?
        :type message: bool
        :return filePath: the full path of the file of the selected thumb, will be "" if none selected
        :rtype filePath: str
        """
        try:
            return self.currentWidget().miniBrowser.currentItem().filePath
        except AttributeError:
            if message:
                output.displayWarning("No thumbnail is selected in the browser.  Please select an image.")
            return ""

    def thumbDirectory(self, message=True):
        """Returns the directory path of the currently selected thumb

        :param message: Report any messages to the user?
        :type message: bool
        :return directory: the path of the directory of the currenlty selected thumb, will be "" if none selected
        :rtype directory: str
        """
        path = self.filePath(message=message)
        if not path:
            return ""
        directory = os.path.dirname(path)
        return directory

    # ------------------------------------
    # OPEN FUNCTIONS AND HELP/BROWSE
    # ------------------------------------

    @toolsetwidget.ToolsetWidget.undoDecorator
    def importScene(self, assetName=""):
        """ Imports the zooScene asset given the GUI settings
        """
        path = self.filePath(message=False)
        if not path:
            logger.debug("File path not found: {}".format(path))
            output.displayWarning("No thumbnail is selected in the browser.  Please select an image.")
            return
        if path.lower().endswith(".ma"):
            mayaType = "mayaAscii"
        elif path.lower().endswith(".mb"):
            mayaType = "mayaBinary"
        else:
            output.displayWarning("This path has an unknown file type, not .ma or .mb")
            return
        # cmds.file(filePath, force=1, options="v=0;", ignoreVersion=1, type=mayaFileType, i=1)
        shaderutils.importAndAssignShader(path, shaderName=assetName, mayaFileType=mayaType)

    def openReadme(self):
        """Opens the readMe.pdf stored with the thumbnail selection if it exists
        """
        directory = self.thumbDirectory()
        if not directory:
            return
        readMeFile = os.path.join(directory, "readMe.pdf")
        if not os.path.exists(readMeFile):
            output.displayWarning("No readme.pdf was found for this file.")
            return
        webbrowser.open(readMeFile)
        output.displayInfo("ReadMe.pdf opened {}".format(readMeFile))

    def openHelp(self):
        """The help file url will be stored in a text file in the same directory as the maya file called "helpUrl.txt"

        The contents of that file is the url to the help location.
        """
        directory = self.thumbDirectory()
        if not directory:
            return
        helpTxtFile = os.path.join(directory, "helpUrl.txt")
        if not os.path.exists(helpTxtFile):
            output.displayWarning("No help url was found for this file.")
            return
        url = filesystem.loadFileTxt(helpTxtFile)
        webbrowser.open(url)
        output.displayInfo("Help page opened {}".format(url))

    def deleteShader(self):
        item = self.currentWidget().miniBrowser.currentItem()
        self.shadersCore.deleteShader(item)
        self.refreshThumbs()

    def saveShader(self, saveType="auto"):
        """Saves the selected shader.

        :param saveType: "auto" saves ma and if unknown nodes saves mb, "ma" saves .ma and "mb" saves .mb
        :type saveType: str
        """
        directory = self.currentWidget().miniBrowser.getSaveDirectory()
        if directory:
            self.shadersCore.saveShader(directory, saveType=saveType)
            self.refreshThumbs()

    def browseDirectory(self):
        self.currentWidget().miniBrowser.browseSelected()

    def actionTriggered(self, action, mouseMenu):
        """

        :param action:
        :type action: :class:`zoo.libs.pyqt.extended.searchablemenu.action.TaggedAction`
        """
        if action.data() == "help":
            self.openHelp()
        elif action.data() == "readme":
            self.openReadme()

    # ------------------------------------
    # CONNECTIONS
    # ------------------------------------

    def uiconnections(self):
        """Hooks up the actual button/widgets functionality
        """
        logger.debug("connections()")
        super(MayaShaders, self).uiconnections()
        for w in self.widgets():
            # dots menu viewer
            w.miniBrowser.dotsMenu.applyAction.connect(self.importScene)
            w.miniBrowser.dotsMenu.createAction.connect(partial(self.saveShader, saveType="auto"))
            w.miniBrowser.dotsMenu.deleteAction.connect(self.deleteShader)
            w.miniBrowser.dotsMenu.actionTriggered.connect(self.actionTriggered)
            # Thumbnail viewer
            w.browserModel.doubleClicked.connect(self.importScene)
            # Change renderer
            w.rendererIconMenu.actionTriggered.connect(self.setRenderer)
            # Buttons
            w.importSelectedBtn.clicked.connect(self.importScene)
            w.saveShaderBtn.clicked.connect(partial(self.saveShader, saveType="auto"))
            w.browseDirBtn.clicked.connect(self.browseDirectory)
            w.openReadmeBtn.clicked.connect(self.openReadme)
            w.openHelpBtn.clicked.connect(self.openHelp)

            # w.browseDirBtn.clicked.connect(w.miniBrowser.browseSelected)

            # Right Click Save Menu ------------
            w.saveShaderBtn.addAction("Save Shader As .MA",
                                mouseMenu=QtCore.Qt.RightButton,
                                icon=iconlib.icon("save"),
                                connect=partial(self.saveShader, saveType="ma"))
            w.saveShaderBtn.addAction("Save Shader As .MB",
                                mouseMenu=QtCore.Qt.RightButton,
                                icon=iconlib.icon("save"),
                                connect=partial(self.saveShader, saveType="mb"))


class AllWidgets(QtWidgets.QWidget):
    """Create all the widgets for all GUIs, compact and advanced etc"""

    def __init__(self, parent=None, properties=None, uiMode=None, toolsetWidget=None):
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
        :type toolsetWidget: :class:`MayaShaders`
        """
        super(AllWidgets, self).__init__(parent=parent)
        self.savedThumbHeight = None
        self.toolsetWidget = toolsetWidget
        self.properties = properties
        self.uiMode = uiMode
        # Thumbnail Viewer --------------------------------------------
        # viewer widget and model
        prefs = shaderinterfaces.shaderInterface()
        uniformIcons = prefs.mayaShaderAssets.browserUniformIcons()

        self.miniBrowser = elements.MiniBrowser(parent=self,
                                                toolsetWidget=self.toolsetWidget,
                                                columns=3,
                                                fixedHeight=382,
                                                uniformIcons=uniformIcons,
                                                itemName="Shader",
                                                applyText="Import",
                                                applyIcon=mayaShadersIcon,
                                                createText="Save",
                                                snapshotActive=True,
                                                selectDirectoriesActive=True
                                                )
        self.miniBrowser.dotsMenu.insertActionIndex(1,
                                                    "Open Help - Web Page",
                                                    icon="help",
                                                    data="help")
        self.miniBrowser.dotsMenu.insertActionIndex(2,
                                                    "Open Readme - PDF",
                                                    icon="information",
                                                    data="readme")
        self.miniBrowser.dotsMenu.setDeleteActive(True)
        self.miniBrowser.dotsMenu.setCreateActive(True)
        self.miniBrowser.dotsMenu.setRenameActive(False)
        self.miniBrowser.dotsMenu.setDirectoryActive(False)  # todo: remove


        directories = prefs.mayaShaderAssets.browserFolderPaths()
        self.browserModel = MayaFileModel(self.miniBrowser,
                                          directories=directories,
                                          uniformIcons=uniformIcons,
                                          assetPreference=prefs.mayaShaderAssets)
        self.miniBrowser.setModel(self.browserModel)
        self.resizerWidget = ToolsetResizer(toolsetWidget=self.toolsetWidget, target=self.miniBrowser)
        # Open File Button --------------------------------------
        tooltip = "Imports the shader and assigns to selected geometry (also double-click)."
        self.importSelectedBtn = elements.styledButton("Import Selected",
                                                       icon="checkMark",
                                                       toolTip=tooltip,
                                                       style=uic.BTN_DEFAULT)
        # Save Shader Button --------------------------------------
        tooltip = "Saves the selected shader. \n" \
                  "If geometry is selected then saves the first related shader."
        self.saveShaderBtn = elements.styledButton("Save Shader",
                                                   icon="save",
                                                   toolTip=tooltip,
                                                   style=uic.BTN_DEFAULT)
        # Open Readme Button --------------------------------------
        tooltip = "Opens the readMe.pdf for the selected file."
        self.openReadmeBtn = elements.styledButton("",
                                                   icon="information",
                                                   toolTip=tooltip,
                                                   style=uic.BTN_DEFAULT)
        self.openReadmeBtn.hide()
        # Open Help Button --------------------------------------
        tooltip = "Opens the help file for the selected file."
        self.openHelpBtn = elements.styledButton("",
                                                 icon="help",
                                                 toolTip=tooltip,
                                                 style=uic.BTN_DEFAULT)
        self.openHelpBtn.hide()
        # Open Directory Browse Button --------------------------------------
        tooltip = "Browse the scene file/s on disk for the selected file."
        self.browseDirBtn = elements.styledButton("",
                                                  icon="globe",
                                                  toolTip=tooltip,
                                                  style=uic.BTN_DEFAULT)
        # Renderer Button --------------------------------------
        toolTip = "Show only files of this renderer type, note that files unrelated to a renderer are kept. \n\n" \
                  "Files are excluded by their file suffix `*_redshift` \n" \
                  "Renderer of the file suffix should be all lowercase."
        self.rendererIconMenu = elements.iconMenuButtonCombo(RENDERER_ICONS_LIST_ALL,
                                                             self.properties.rendererIconMenu.value,
                                                             toolTip=toolTip)

    def embedWindowVisChanged(self, visibility):
        self.toolsetWidget.updateTree(delayed=True)


class GuiCompact(AllWidgets):
    def __init__(self, parent=None, properties=None, uiMode=UI_MODE_COMPACT, toolsetWidget=None):
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
                                         uiMode=uiMode, toolsetWidget=toolsetWidget)
        # Main Layout
        mainLayout = elements.vBoxLayout(self, margins=(uic.WINSIDEPAD, uic.WINTOPPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=0)
        # Renderer layout
        rendererLayout = elements.hBoxLayout()
        rendererLayout.addWidget(self.importSelectedBtn, 10)
        rendererLayout.addWidget(self.saveShaderBtn, 10)
        rendererLayout.addWidget(self.openReadmeBtn, 1)
        rendererLayout.addWidget(self.openHelpBtn, 1)
        rendererLayout.addWidget(self.browseDirBtn, 1)
        rendererLayout.addWidget(self.rendererIconMenu, 1)
        # Add to main layout
        mainLayout.addWidget(self.miniBrowser)
        mainLayout.addWidget(self.resizerWidget)
        mainLayout.addLayout(rendererLayout)
        mainLayout.addStretch(1)
