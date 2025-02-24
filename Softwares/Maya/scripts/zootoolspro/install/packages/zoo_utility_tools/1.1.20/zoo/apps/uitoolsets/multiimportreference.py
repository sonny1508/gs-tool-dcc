""" ---------- Multi Import Reference -------------


"""
import os

from zoovendor.Qt import QtWidgets

from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements

from zoo.libs.maya.cmds.workspace import mayaworkspace
from zoo.libs.maya.cmds.filemanage import saveexportimport
from zoo.libs.maya.cmds.hotkeys import definedhotkeys


UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1


class MultiImportReference(toolsetwidget.ToolsetWidget):
    id = "multiImportReference"
    info = "Import or reference files multiple times."
    uiData = {"label": "Multi Import Reference",
              "icon": "importZooScene",
              "tooltip": "Import or reference files multiple times.",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-multi-import-referenc/"}

    # ------------------
    # STARTUP
    # ------------------

    def preContentSetup(self):
        """First code to run, treat this as the __init__() method"""
        pass

    def contents(self):
        """The UI Modes to build, compact, medium and or advanced """
        return [self.initCompactWidget()]  # self.initAdvancedWidget()

    def initCompactWidget(self):
        """Builds the Compact GUI (self.compactWidget) """
        self.compactWidget = GuiCompact(parent=self, properties=self.properties, toolsetWidget=self)
        return self.compactWidget

    def initAdvancedWidget(self):
        """Builds the Advanced GUI (self.advancedWidget) """
        self.advancedWidget = GuiAdvanced(parent=self, properties=self.properties, toolsetWidget=self)
        return self.advancedWidget

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
        :rtype: GuiAdvanced or GuiCompact
        """
        return super(MultiImportReference, self).currentWidget()

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiAdvanced or GuiCompact]
        """
        return super(MultiImportReference, self).widgets()

    # ------------------
    # LOGIC
    # ------------------

    def loadFilePath(self):
        """Loads a Open File Window to browse for the HDRI Image on disk"""
        directory = ""
        imagePath = self.properties.filePathStr.value

        if imagePath:  # Gets the directory from the current image path, if doesn't exist then directory = ""
            directory = os.path.dirname(imagePath)
            if not os.path.exists(directory):
                directory = ""

        if not directory:  # If no directory found then sets to sourceImages in project directory
            projectDirectory = mayaworkspace.getCurrentMayaWorkspace()
            directory = os.path.join(projectDirectory, "scenes/")

        if not os.path.exists(directory):  # no directory found so use home
            directory = os.path.expanduser("~")

        # Open dialog ------------------------------------------------
        fullFilePath, filter = QtWidgets.QFileDialog.getOpenFileName(self, "Select File", directory)
        if not str(fullFilePath):
            return

        self.properties.filePathStr.value = str(fullFilePath)
        self.updateFromProperties()

    def importReference(self):
        """Import or references a file multiple times.
        """
        refImport = self.properties.refImportRadio.value
        filepath = self.properties.filePathStr.value
        namespace = self.properties.nameSpaceStr.value
        duplicates = self.properties.numberImportsReferenceInt.value
        if not filepath:
            return
        if refImport:
            saveexportimport.multipleReference(filepath, duplicates=duplicates, namespace=namespace)
        else:
            saveexportimport.multipleImport(filepath, duplicates=duplicates, namespace=namespace)

    def openNamespaceEditor(self):
        """Opens Maya's namespace editor"""
        definedhotkeys.openNamespaceEditor()

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        for widget in self.widgets():
            widget.browseBtn.clicked.connect(self.loadFilePath)
            widget.importReferenceBtn.clicked.connect(self.importReference)
            widget.namespaceBtn.clicked.connect(self.openNamespaceEditor)


class GuiWidgets(QtWidgets.QWidget):
    def __init__(self, parent=None, properties=None, uiMode=None, toolsetWidget=None):
        """Builds the main widgets for all GUIs

        properties is the list(dictionaries) used to set logic and pass between the different UI layouts
        such as compact/adv etc

        :param parent: the parent of this widget
        :type parent: QtWidgets.QWidget
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: zoo.apps.toolsetsui.widgets.toolsetwidget.PropertiesDict
        :param uiMode: 0 is compact ui mode, 1 is advanced ui mode
        :type uiMode: int
        """
        super(GuiWidgets, self).__init__(parent=parent)
        self.properties = properties
        # reference import radio buttons ---------------------------------------
        tooltipList = ["Import the file multiple times",
                       "Reference the file multiple times"]
        self.refImportRadio = elements.RadioButtonGroup(radioList=["Import", "Reference"],
                                                        default=0,
                                                        toolTipList=tooltipList)
        # Filepath ---------------------------------------
        tooltip = "Enter the full filepath of the file to be imported or referenced multiple times"
        self.filePathStr = elements.StringEdit(label="File Path",
                                               editPlaceholder="Enter full file path",
                                               labelRatio=11,
                                               editRatio=40,
                                               toolTip=tooltip)
        toolTip = "Browse to a file"
        self.browseBtn = elements.styledButton("",
                                               "browse",
                                               self,
                                               toolTip=toolTip,
                                               style=uic.BTN_DEFAULT,
                                               minWidth=uic.BTN_W_ICN_MED)
        # Number of imports ---------------------------------------
        tooltip = "The number of times to import or reference the file"
        self.numberImportsReferenceInt = elements.IntEdit(label="Duplicates",
                                                          editText=4,
                                                          labelRatio=3,
                                                          editRatio=1,
                                                          toolTip=tooltip)
        # Filepath ---------------------------------------
        tooltip = "The namespace to give to the imported or referenced files. \n" \
                  "namespace will import with incrementing numbers from 1 to the number of imports. \n" \
                  " - xxx1:pCube, xxx2:pCube, xxx3:pCube etc"
        self.nameSpaceStr = elements.StringEdit(label="Namespace",
                                                editText="xxx",
                                                labelRatio=10,
                                                editRatio=23,
                                                toolTip=tooltip)
        # Main button ---------------------------------------
        tooltip = "Run the multi import/reference, will import or reference the \n" \
                  "file multiple times. "
        self.importReferenceBtn = elements.styledButton("Multi Import/Reference",
                                                        icon="importZooScene",
                                                        toolTip=tooltip,
                                                        style=uic.BTN_DEFAULT)
        # Namespace button ---------------------------------------
        tooltip = "Open Maya's Namespace Editor "
        self.namespaceBtn = elements.styledButton("Namespace",
                                                  icon="windowBrowser",
                                                  toolTip=tooltip,
                                                  style=uic.BTN_DEFAULT)


class GuiCompact(GuiWidgets):
    def __init__(self, parent=None, properties=None, uiMode=UI_MODE_COMPACT, toolsetWidget=None):
        """Adds the layout building the compact version of the GUI:

            default uiMode - 0 is advanced (UI_MODE_COMPACT)

        :param parent: the parent of this widget
        :type parent: QtWidgets.QWidget
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: zoo.apps.toolsetsui.widgets.toolsetwidget.PropertiesDict
        """
        super(GuiCompact, self).__init__(parent=parent, properties=properties, uiMode=uiMode,
                                         toolsetWidget=toolsetWidget)
        # Main Layout ---------------------------------------
        mainLayout = elements.vBoxLayout(self, margins=(uic.WINSIDEPAD, uic.WINBOTPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SREG)
        # file path -----------------------------
        filePathLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SREG)
        filePathLayout.addWidget(self.filePathStr, 20)
        filePathLayout.addWidget(self.browseBtn, 1)
        # number namespace layout  ---------------------------------------
        namespaceNumberLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SVLRG)
        namespaceNumberLayout.addWidget(self.nameSpaceStr, 2)
        namespaceNumberLayout.addWidget(self.numberImportsReferenceInt, 1)
        # Button layout  ---------------------------------------
        btnLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SPACING)
        btnLayout.addWidget(self.importReferenceBtn, 2)
        btnLayout.addWidget(self.namespaceBtn, 1)
        # Add To Main Layout ---------------------------------------
        mainLayout.addWidget(self.refImportRadio)
        mainLayout.addLayout(filePathLayout)
        mainLayout.addLayout(namespaceNumberLayout)
        mainLayout.addLayout(btnLayout)


class GuiAdvanced(GuiWidgets):
    def __init__(self, parent=None, properties=None, uiMode=UI_MODE_ADVANCED, toolsetWidget=None):
        """Adds the layout building the advanced version of the GUI:

            default uiMode - 1 is advanced (UI_MODE_ADVANCED)

        :param parent: the parent of this widget
        :type parent: QtWidgets.QWidget
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: zoo.apps.toolsetsui.widgets.toolsetwidget.PropertiesDict
        """
        super(GuiAdvanced, self).__init__(parent=parent, properties=properties, uiMode=uiMode,
                                          toolsetWidget=toolsetWidget)
        # Main Layout ---------------------------------------
        mainLayout = elements.vBoxLayout(self, margins=(uic.WINSIDEPAD, uic.WINBOTPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SREG)
        # Add To Main Layout ---------------------------------------
        mainLayout.addWidget(self.aLabelAndTextbox)
        mainLayout.addWidget(self.aBtn)
