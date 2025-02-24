from zoo.apps.hiveartistui import uiinterface
from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.libs.hive import api as hiveapi
from zoo.libs.maya.cmds.filemanage import saveexportimport
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements
from zoo.libs.utils import output
from zoovendor.Qt import QtWidgets


UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1


class HiveRigExportToolset(toolsetwidget.ToolsetWidget):
    id = "hiveMayaReferenceExport"
    info = "Hive Maya Reference export tool."
    uiData = {"label": "Hive Reference Model Skeleton",
              "icon": "referenceModelSkeleton",
              "tooltip": "Provides a Maya exporter for a hive rig to be referenced with a skeleton and geometry .",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-hive-reference-model-skeleton"}

    def contents(self):
        """The UI Modes to build, compact, medium and or advanced """
        return [self.initCompactWidget()]

    def initCompactWidget(self):
        """Builds the Compact GUI (self.compactWidget) """
        self.compactWidget = GuiCompact(parent=self, properties=self.properties, toolsetWidget=self)
        return self.compactWidget

    def postContentSetup(self):
        """Last of the initialize code"""
        self.uiConnections()
        # Update a rig list done in post because we have signals getting emitted by
        # hive UI which require a reload of the list as well.
        self._rigStateChanged()

    def initializeProperties(self):
        """Used to store and update UI data

        For use in the GUI use:
            current value: self.properties.itemName.value
            default value (automatic): self.properties.itemName.default

        To connect Qt widgets to property methods use:
            self.toolsetWidget.linkProperty(self.widgetQtName, "itemName")

        :return properties: special dictionary used to save and update all GUI widgets
        :rtype properties: list(dict)
        """
        return [
            {"name": "filePathEdit", "value": 1}
        ]

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiAdvanced or GuiCompact]
        """
        return super(HiveRigExportToolset, self).widgets()

    # ------------------
    # ENTER
    # ------------------

    def enterEvent(self, event):
        """When the cursor enters the UI update it"""
        self._rigStateChanged()

    # -------------------
    # HIVE CORE SIGNALS
    # -------------------
    def _rigStateChanged(self):
        self._sceneRigs = list(hiveapi.iterSceneRigs())
        for widget in self.widgets():
            widget.updateRigs(self._sceneRigs)

    def _currentRigChanged(self, rigName):
        for widget in self.widgets():
            widget.setCurrentRig(rigName)


    # ------------------
    # LOGIC
    # ------------------
    def _ensureFileSaved(self):
        """Checks if the file has already been saved. Return True or False so we know if we should
        continue exporting

        If not saved opens "save", or "cancel" window.  Returns the button pressed if "cancel"

        If "save" is clicked it will try to save the current file, if cancelled will return False

        :return buttonClicked: Whether or not to continue exporting
        :rtype buttonClicked: str
        """
        # TODO move this into elements under maya cmds
        sceneModified = saveexportimport.fileModified()

        if not sceneModified:  # Has been saved already so continue
            return True
        # Open dialog window with Save/Discard/Cancel buttons
        fullMessage = "Save the current file?"
        buttonPressed = elements.MessageBox.showSave(title="Save File", parent=self, message=fullMessage,
                                                     showDiscard=True)
        if buttonPressed == "save":
            if saveexportimport.saveAsDialogMaMb():  # file saved
                return True
            return False
        elif buttonPressed == "discard":
            return True
        return False

    def sceneRigs(self):
        """

        :return:
        :rtype: list[:class:`hiveapi.HiveRig`]
        """

        return self._sceneRigs

    def _uiRigModel(self):
        """Query from Hive UI the rig model instance. This is so we can sync between the UIs
        """
        hiveUICore = uiinterface.instance().core()
        # todo: support running without the artist ui
        if hiveUICore is None:
            output.displayWarning("Hive Artist UI needs to be open")
            return
        container = hiveUICore.currentRigContainer
        if container is None:
            output.displayWarning("Hive Artist UI needs to have a active rig")
            return
        rigModel = container.rigModel
        if rigModel is None:
            output.displayError("Hive Artist UI needs a active rig")
            return
        return rigModel

    def onExport(self):
        currentWidget = self.currentWidget()
        rigInstance = None
        for rig in self.sceneRigs():
            if rig.name() == currentWidget.rigListCombo.currentText():
                rigInstance = rig
                break
        if rigInstance is None:
            output.displayError("No valid Rig Selected in the UI")
            return
        compatWidget = self.widgets()[0]
        outputPath = compatWidget.filePathEdit.path()
        if not outputPath:
            output.displayError("Invalid export path: {}".format(outputPath))
            return
        if not self._ensureFileSaved():
            return
        exporter = rigInstance.configuration.exportPluginForId("mayaReference")()
        exportSettings = exporter.exportSettings()
        exportSettings.outputPath = outputPath
        exportSettings.updateRig = True
        exporter.execute(rigInstance, exportSettings)

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        hiveUICore = uiinterface.instance()
        for widget in self.widgets():
            widget.exportBtn.clicked.connect(self.onExport)
        if hiveUICore is not None:
            hiveUICore = hiveUICore.core()
            hiveUICore.rigRenamed.connect(self._rigStateChanged)
            hiveUICore.rigsChanged.connect(self._rigStateChanged)
            hiveUICore.currentRigChanged.connect(self._currentRigChanged)


class GuiWidgets(QtWidgets.QWidget):
    def __init__(self, parent=None, properties=None, uiMode=None, toolsetWidget=None):
        """Builds the main widgets for all GUIs

        properties is the list(dictionaries) used to set logic and pass between the different UI layouts
        such as compact/adv etc

        :param parent: the parent of this widget
        :type parent: :class:`QtWidgets.QWidget`
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: :class:`zoo.apps.toolsetsui.widgets.toolsetwidget.PropertiesDict`
        :param uiMode: 0 is compact ui mode, 1 is advanced ui mode
        :type uiMode: int
        :type toolsetWidget: :class:`HiveRigExportToolset`
        """
        super(GuiWidgets, self).__init__(parent=parent)
        self.properties = properties
        # File Path Widget -------------------------------------------
        toolTip = "Set the filepath of where the model/skeleton will be saved on disk. "
        self.filePathEdit = elements.PathWidget(parent=self, toolTip=toolTip)
        self.filePathEdit.setSearchFilter("*.ma *.mb")
        self.filePathEdit.pathText.setPlaceHolderText("Set the path where the file will be referenced...")
        # Rig List Combo -------------------------------------------
        toolTip = "Select the Hive rig from the scene to reference it's model/skeleton. "
        self.rigListCombo = elements.ComboBoxRegular("",
                                                     items=[],
                                                     parent=self,
                                                     toolTip=toolTip)

        # Export Button -------------------------------------------
        toolTip = "Export the model/skeleton to disk and then reference it into the scene/Hive rig. \n"\
                  "File should be saved before proceeding. "
        self.exportBtn = elements.styledButton("Export And Reference Model/Skeleton",
                                               icon="referenceModelSkeleton",
                                               toolTip=toolTip,
                                               minWidth=uic.BTN_W_ICN_MED,
                                               parent=self)

    def updateRigs(self, rigs):
        oldPropertyValue = self.rigListCombo.currentText()
        self.rigListCombo.clear()
        self.rigListCombo.addItems([i.name() for i in rigs])
        self.rigListCombo.setToText(oldPropertyValue)

    def setCurrentRig(self, rigName):
        self.rigListCombo.setToText(rigName)


class GuiCompact(GuiWidgets):
    def __init__(self, parent=None, properties=None, uiMode=UI_MODE_COMPACT, toolsetWidget=None):
        """Adds the layout building the compact version of the GUI:

            default uiMode - 0 is advanced (UI_MODE_COMPACT)

        :param parent: the parent of this widget
        :type parent: QtWidgets.QWidget
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: :class:`toolsetwidget.PropertiesDict`
        """
        super(GuiCompact, self).__init__(parent=parent, properties=properties, uiMode=uiMode,
                                         toolsetWidget=toolsetWidget)
        # Main Layout ---------------------------------------
        mainLayout = elements.vBoxLayout(self,
                                         margins=(uic.WINSIDEPAD, uic.WINBOTPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SLRG)
        rigDivider = elements.LabelDivider(text="Select Hive Rig", parent=self)
        filePathDivider = elements.LabelDivider(text="File Path", parent=self)
        saveDivider = elements.LabelDivider(text="Save And Reference", parent=self)
        # Rig Layout -----------------------
        rigLayout = elements.hBoxLayout(spacing=uic.SLRG, margins=(uic.REGPAD, 0, uic.REGPAD, 0))
        rigLayout.addWidget(self.rigListCombo, 1)
        # File Path Layout -----------------------
        filePathLayout = elements.hBoxLayout(spacing=uic.SLRG, margins=(uic.REGPAD, 0, uic.REGPAD, 0))
        filePathLayout.addWidget(self.filePathEdit, 1)
        # Button Layout -----------------------
        buttonLayout = elements.hBoxLayout(spacing=uic.SLRG, margins=(uic.SMLPAD, 0, uic.SMLPAD, 0))
        buttonLayout.addWidget(self.exportBtn, 1)
        # Main Layout ---------------------------------------
        mainLayout.addWidget(rigDivider)
        mainLayout.addLayout(rigLayout)
        mainLayout.addWidget(filePathDivider)
        mainLayout.addLayout(filePathLayout)
        mainLayout.addWidget(saveDivider)
        mainLayout.addLayout(buttonLayout)
