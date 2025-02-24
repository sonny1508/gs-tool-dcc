""" ---------- Toolset Boiler Plate (Multiple UI Modes) -------------
The following code is a template (boiler plate) for building Zoo Toolset GUIs that multiple UI modes.

Multiple UI modes include compact and medium or advanced modes.

This UI will use Compact and Advanced Modes.

The code gets more complicated while dealing with UI Modes.

"""

from zoovendor.Qt import QtWidgets

from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements

from zoo.libs.maya.cmds.hotkeys import definedhotkeys
from zoo.libs.maya.cmds.skin import bindskin

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1


class BrTransferSkinCluster(toolsetwidget.ToolsetWidget):
    id = "brSkinTransferExport"
    info = "braverabbit Export/Import Skin Weights."
    uiData = {"label": "Export/Import Skinning - brave rabbit",
              "icon": "importArrow",
              "tooltip": "Transfer Skin Weights. brave rabbit",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-third-party/#transferskin"
              }

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
        return super(BrTransferSkinCluster, self).currentWidget()

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiAdvanced or GuiCompact]
        """
        return super(BrTransferSkinCluster, self).widgets()

    def enterEvent(self, event):
        """Updates the UI by pulling in the strength and size values to the sliders"""
        pass

    # ------------------
    # LOGIC
    # ------------------

    @toolsetwidget.ToolsetWidget.undoDecorator
    def autoRenameSkinCluster(self):
        bindskin.renameSelSkinClusters()

    def exportSkinWeights(self):
        """Exports Selected Objects Skin Weights"""
        definedhotkeys.brTransferSkinWeights(export=True)

    def importSkinWeights(self):
        """Opens the Import Skin Weights UI"""
        definedhotkeys.brTransferSkinWeights(export=False)

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        for widget in self.widgets():
            # Buttons ---------
            widget.exportBtn.clicked.connect(self.exportSkinWeights)
            widget.importBtn.clicked.connect(self.importSkinWeights)
            widget.autoNameBtn.clicked.connect(self.autoRenameSkinCluster)


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
        # Auto Rename From Meshes ---------------------------------------
        tooltip = "Automatically renames the selected mesh's skin cluster \n" \
                  "Will match the mesh eg. - `meshName_skin`"
        self.autoNameBtn = elements.AlignedButton("",
                                                  icon="editText",
                                                  toolTip=tooltip)
        # Export ---------------------------------------
        tooltip = ("Select a mesh with skinning to export its skin weights.  \n"
                   "Weights will be saved to a file in the current maya project `data` directory.\n"
                   "The file will be named after the skin cluster name.\n"
                   "Supports only one skin cluster per mesh.\n\n"
                   "Tool by: brave rabbit (braverabbit.com)")
        self.exportBtn = elements.AlignedButton("Export Mesh Skin Weights",
                                                icon="save",
                                                toolTip=tooltip)
        # Import ---------------------------------------
        tooltip = ("Opens a UI to import a previously exported skin cluster. \n"
                   "Skin Clusters are found in the current Maya Project under the `data` directory.\n"
                   "Meshes, joints names and vertex numbers must be identical to the exported data. \n"
                   "Supports only one skin cluster per mesh.\n\n"
                   "Tool by: brave rabbit (braverabbit.com)")
        self.importBtn = elements.AlignedButton("Open Import Window",
                                                icon="window",
                                                toolTip=tooltip)


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
        btnLayout = elements.hBoxLayout(spacing=uic.SPACING)
        btnLayout.addWidget(self.autoNameBtn, 1)
        btnLayout.addWidget(self.exportBtn, 12)
        btnLayout.addWidget(self.importBtn, 10)

        # Add To Main Layout ---------------------------------------
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
        pass
