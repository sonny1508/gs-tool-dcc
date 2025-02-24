from functools import partial

from zoo.libs.maya import zapi

from zoo.apps.controlsjoints import controlsjointsconstants as cc, api
from zoo.apps.controlsjoints.mixins import ControlsJointsMixin
from zoo.apps.controlsjoints.modelcontrolcurves import ControlCurvesViewerModel
from zoo.apps.toolsetsui.mixins import MiniBrowserMixin

from zoo.preferences.interfaces import controljointsinterfaces
from zoovendor.Qt import QtCore, QtWidgets

from zoo.libs.utils import output
from zoo.apps.toolsetsui.widgets.toolsetresizer import ToolsetResizer
from zoo.apps.toolsetsui.widgets import toolsetwidget

from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements

# Dots Menu
from zoo.libs.pyqt.widgets.iconmenu import IconMenuButton
from zoo.libs import iconlib
from zoo.libs.pyqt import utils
from zoo.libs.maya.cmds.rig import controls

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1

COMBO_UP_LIST = list()
for x in cc.ORIENT_UP_LIST:
    COMBO_UP_LIST.append("Up Axis {}".format(x))


class ControlCreator(toolsetwidget.ToolsetWidget, MiniBrowserMixin, ControlsJointsMixin):
    directory = None  # type: object
    uniformIcons = None  # type: object

    id = "controlCreator"
    uiData = {"label": "Control Creator",
              "icon": "starControl",
              "tooltip": "GUI for creating control curves",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-control-creator/"
              }

    # ------------------------------------
    # START UP
    # ------------------------------------

    def preContentSetup(self):
        """First code to run"""

        self.selObjs = list()  # Remember the last objects selected if nothing selected
        self.breakObj = ""  # the break object, useful for replace
        self.copyCtrl = ""
        self.copyTranslate = None
        self.copyRotate = None
        self.copyScale = None
        self.copyColor = None
        self.copyShape = ""
        self.core = api.ControlsCore(self)

    def contents(self):

        """The UI Modes to build, compact, medium and or advanced """
        return [self.initCompactWidget()]

    def initCompactWidget(self):
        """Builds the Compact GUI (self.compactWidget) """
        self.compactWidget = GuiCompact(parent=self, properties=self.properties, toolsetWidget=self)

        return self.compactWidget

    def initAdvancedWidget(self):
        """Not used, legacy"""
        self.advancedWidget = GuiAdvanced(parent=self, properties=self.properties, toolsetWidget=self)
        return self.advancedWidget

    def postContentSetup(self):
        """Last of the initialize code"""
        self.setAssetPreferences(self.core.controlPrefs.controlAssets)
        self.setMiniBrowsers([w.miniBrowser for w in self.widgets()])
        self.uiconnections()

    def currentWidget(self):
        """ Current active widget

        :return:
        :rtype:  AllWidgets
        """
        return super(ControlCreator, self).currentWidget()

    def widgets(self):
        """ List of widgets

        :return:
        :rtype: list[AllWidgets]
        """
        return super(ControlCreator, self).widgets()

    # ------------------------------------
    # POPUP WINDOWS
    # ------------------------------------

    def saveCurvesPopupWindow(self, newControlName):
        """Save control curve popup window with a new name text entry

        :param newControlName: The name of the selected curve transform
        :type newControlName: str
        :return newControlName: The name of the control curve that will be saved to disk *.shape
        :rtype newControlName: str
        """
        message = "Save Selected Curve Control?"
        # TODO need to specify a parent as the Maya window, current stylesheet issues with self.parent
        newControlName = elements.MessageBox.inputDialog(title="Save Curve Control", text=newControlName,
                                                         parent=None, message=message)
        return newControlName

    def deleteCurvesPopupWindow(self, shapeName):
        """Delete control curve popup window asking if the user is sure they want to delete?

        :param shapeName: The name of the shape/design to be deleted from the library on disk
        :type shapeName: str
        :return okState: Ok button was pressed
        :rtype okState: bool
        """
        message = "Are you sure you want to delete `{0}` from the Zoo Curve Library?\n" \
                  "This will permanently delete the file `{0}.shape` from disk.".format(shapeName)
        # TODO need to specify a parent as the Maya window, current stylesheet issues with self.parent
        okState = elements.MessageBox.showOK(title="Delete Curve From Library",
                                             parent=None, message=message)
        return okState

    def renameCurvesPopupWindow(self, existingControlName):
        """Rename control curve popup window with a new name text entry

        :param existingControlName: The name of the name of the shape to be renamed
        :type existingControlName: str
        :return newControlName: The name of the control to be renamed, without the file extension
        :rtype newControlName: str
        """
        message = "Rename `{}` in the Zoo library to a new name.\n" \
                  "File will be renamed on disk".format(existingControlName)
        # TODO need to specify a parent as the Maya window, current stylesheet issues with self.parent
        newControlName = elements.MessageBox.inputDialog(title="Rename Curve/Design In Library",
                                                         text=existingControlName,
                                                         parent=None, message=message)
        return newControlName

    # ------------------------------------
    # MAIN LOGIC - EDIT
    # ------------------------------------

    @toolsetwidget.ToolsetWidget.undoDecorator
    def colorSelected(self, color):
        """Change the selected control color (and potential children) when the color is changed if a selection"""
        self.global_sendCntrlColor()
        self.core.colorSelected(color)

    def replaceWithShapeDesign(self, event=None):
        """Replaces the curves from the combo box shape design list

        Note: Undo is built into this function

        :param event:
        :type event: zoo.libs.pyqt.extended.combobox.ComboItemChangedEvent
        """
        designName, directory = self.directoryDesignName()
        if not designName:
            return

        self.core.replaceWithShapeDesign(designName, directory)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def scaleCVs(self, positive=True):
        """UI function that scales nurbs curve objects based on their CVs, will not affect transforms

        :param positive: is the scale bigger positive=True, or smaller positive=False
        :type positive: bool
        """
        self.core.scaleCVs(positive)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def absoluteScale(self, nullTxt=""):
        self.core.absoluteScale(nullTxt)

    def absoluteScaleSlider(self, nullTxt=""):
        self.core.absoluteScale(nullTxt)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def rotateCVs(self, positive=True):
        """Rotates CVs by local space rotation"""
        self.core.rotateCVs(positive)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def offsetColorSelected(self, offsetTuple, resetClicked):
        """Offset the selected control color (and potential children) when the color is changed if there's a selection

        :param offsetTuple: The offset as (hue, saturation, value)
        :type offsetTuple: tuple
        :param resetClicked: Has the reset been activated (alt clicked)
        :type resetClicked: bool
        """
        self.properties.colorSwatchBtn.value = self.compactWidget.colorSwatchBtn.colorLinearFloat()
        self.core.offsetColorSelected(offsetTuple, resetClicked)
        self.global_sendCntrlColor()

    def setColor(self):
        """Sets the color to the control based on the GUI"""
        self.colorSelected(self.properties.colorSwatchBtn.value)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def getColorSelected(self, selectMode=False):
        """From selection get the color of the current control curve and change the GUI to that color"""
        color = self.core.getColorSelected()
        if selectMode:  # select similar objects
            if self.core.selectControlsByColor(color=color, verbose=False) is None:
                output.displayWarning("No curve objects found in the scene")
        else:  # just update the GUI
            if color is None:
                output.displayWarning("Please select a curve object (transform)")
                return
            self.properties.colorSwatchBtn.value = color
            self.updateFromProperties()  # Update the swatch in the GUI
            self.global_sendCntrlColor()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def delZooTrackerAttrs(self):
        """Deletes/Cleans the zoo tracker attribtutes on the selected control curves. """
        controls.deleteTrackAttrsSel()

    # ------------------
    # GLOBAL METHODS - SEND/RECEIVE ALL TOOLSETS.
    # ------------------

    def global_receiveCntrlColor(self, color):
        """Receives from all GUIs, changes the color"""
        self.properties.colorSwatchBtn.value = color
        self.updateFromProperties()

    def global_sendCntrlColor(self):
        """Updates all GUIs with the current color"""
        from zoo.apps.toolsetsui import toolsetui
        toolsets = toolsetui.toolsetsById("controlCreator")  # type: list[ControlCreator]
        for tool in toolsets:
            tool.global_receiveCntrlColor(self.properties.colorSwatchBtn.value)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def selectControlsByColor(self, color=None):
        """Selects the controls that match the GUI color"""
        self.core.selectControlsByColor(color)

    def selectSimilar(self):
        """Select Similar"""
        self.getColorSelected(selectMode=True)  # select similar to the selected object

    @toolsetwidget.ToolsetWidget.undoDecorator
    def freezeControlTracker(self):
        """Freezes the scale tracker attributes setting them to a scale of 1.0 no matter the current scale"""
        self.core.freezeControlTracker()

    # ------------------
    # LOGIC - SAVE RENAME DEL SHAPE LIB
    # ------------------

    def directoryDesignName(self):
        designName = self.currentWidget().browserModel.currentImage
        if not designName:
            output.displayWarning("No image/item is selected in the browser, please select.")
            return "", ""
        return designName, self.currentWidget().browserModel.currentItem.directory

    def saveControlsToLibrary(self, newControlName=None, directory=None):
        """Saves the selected control to disk, currently Zoo internally and not to zoo_preferences"""
        if not len(list(zapi.selected(filterTypes=zapi.kTransform))):
            output.displayWarning("A curve must be selected")
            return

        pureName = self.core.pureName()
        newControlName = self.saveCurvesPopupWindow(pureName)
        if newControlName:  # Save confirmation from the GUI
            directory = self.currentWidget().miniBrowser.getSaveDirectory()
            if directory:
                self.core.saveControlsToLibrary(newControlName, directory)
                self.refreshThumbs()  # refresh shape/design thumbs

    def deleteShapeDesignFromDisk(self):
        """Deletes specified shape/design from disk, currently Zoo internally and not to zoo_preferences"""
        designName, directory = self.directoryDesignName()
        if not designName:
            return

        okState = self.deleteCurvesPopupWindow(designName)
        if not okState:  # Cancel
            return
        # Delete file and dependency files
        filesFullPathDeleted = self.core.deleteShapeDesignFromDisk(designName, directory)
        self.refreshThumbs()
        output.displayInfo("Success, File/s Deleted: {}".format(filesFullPathDeleted))

    def buildControlsAll(self, forceCreate=False):
        """ Build all selected controls

        :param forceCreate:
        :return:
        """
        designName, directory = self.directoryDesignName()
        if not designName:
            return

        freeze = self.compactWidget.toolDotsMenu.freezeState.isChecked()
        group = self.compactWidget.toolDotsMenu.groupState.isChecked()
        self.core.buildControlsAll(designName, forceCreate=forceCreate, freeze=freeze, group=group,
                                   folderPath=directory)

    # ------------------------------------
    # CONNECTIONS
    # ------------------------------------

    def renameShapeDesignOnDisk(self):
        designName, directory = self.directoryDesignName()
        if not designName:
            return

        renameText = self.renameCurvesPopupWindow(designName)
        if not renameText:
            return

        fileRenameList = self.core.renameShapeDesignOnDisk(designName, renameText, directory)
        if fileRenameList:  # message handled inside function
            self.refreshThumbs()  # refresh shape/design thumbs
            output.displayInfo("Success Files Renamed: {}".format(fileRenameList))

    def uiconnections(self):
        """Hooks up the actual button/widgets functionality
        """
        super(ControlCreator, self).uiconnections()
        for uiInstance in self.widgets():
            # thumbnail viewer
            uiInstance.browserModel.doubleClicked.connect(lambda: self.buildControlsAll())
            # build
            uiInstance.changeBtn.clicked.connect(lambda: self.buildControlsAll())
            uiInstance.buildMatchBtn.clicked.connect(partial(self.buildControlsAll, forceCreate=True))
            # dots menu viewer

            uiInstance.miniBrowser.applyAction.connect(lambda: self.buildControlsAll())
            uiInstance.miniBrowser.createAction.connect(self.saveControlsToLibrary)
            uiInstance.miniBrowser.renameAction.connect(self.renameShapeDesignOnDisk)
            uiInstance.miniBrowser.deleteAction.connect(self.deleteShapeDesignFromDisk)

            # color
            uiInstance.colorSwatchBtn.colorChanged.connect(self.colorSelected)
            uiInstance.colorSwatchBtn.offsetClicked.connect(self.offsetColorSelected)
            # edit
            uiInstance.orientVectorComboBox.itemChanged.connect(self.replaceWithShapeDesign)
            # uiInstance.scaleFloat.sliderStarted.connect(lambda: self.openUndoChunk("slider"))
            # uiInstance.scaleFloat.sliderChanged.connect(self.absoluteScale)
            # uiInstance.scaleFloat.sliderFinished.connect(lambda: self.closeUndoChunk("slider"))
            uiInstance.scaleFloat.textModified.connect(self.absoluteScale)
            uiInstance.scaleFloat.sliderStarted.connect(self.openUndoChunk)
            uiInstance.scaleFloat.sliderChanged.connect(self.absoluteScaleSlider)
            uiInstance.scaleFloat.sliderFinished.connect(self.closeUndoChunk)
            # offset
            uiInstance.scaleDownBtn.clicked.connect(partial(self.scaleCVs, positive=False))
            uiInstance.scaleUpBtn.clicked.connect(partial(self.scaleCVs, positive=True))
            uiInstance.rotatePosBtn.clicked.connect(partial(self.rotateCVs, positive=True))
            uiInstance.rotateNegBtn.clicked.connect(partial(self.rotateCVs, positive=False))
            # Tool Dots Menu
            uiInstance.toolDotsMenu.getColor.connect(self.getColorSelected)
            uiInstance.toolDotsMenu.selectSimilar.connect(self.selectSimilar)
            uiInstance.toolDotsMenu.selectColor.connect(self.selectControlsByColor)
            uiInstance.toolDotsMenu.setDefaultScale.connect(self.freezeControlTracker)
            uiInstance.toolDotsMenu.delZooTrackerAttrs.connect(self.delZooTrackerAttrs)


class AllWidgets(QtWidgets.QWidget):
    """Create all the widgets for all GUIs, compact and advanced etc"""

    def __init__(self, parent=None, properties=None, uiMode=None, toolsetWidget=None, directories=None):
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
        :type toolsetWidget: ControlCreator
        :param directories: directory path of the light preset zooScene files
        :type directories: str
        """
        super(AllWidgets, self).__init__(parent=parent)
        self.controlsPrefs = controljointsinterfaces.controlJointsInterface()
        self.toolsetWidget = toolsetWidget
        self.properties = properties
        self.uiMode = uiMode
        # Thumbnail Viewer ---------------------------------------
        # viewer widget and model

        uniformIcons = self.controlsPrefs.controlAssets.browserUniformIcons()
        self.miniBrowser = elements.MiniBrowser(parent=self, columns=4, toolsetWidget=self.toolsetWidget,
                                                fixedHeight=382,
                                                uniformIcons=uniformIcons,
                                                applyIcon="starControl",
                                                itemName="Shape Control",
                                                createText="Save New",
                                                applyText="Change/Build Ctrl",
                                                selectDirectoriesActive=True)
        self.miniBrowser.dotsMenu.setSnapshotActive(True)
        self.miniBrowser.dotsMenu.setDirectoryActive(False)  # todo: remove this since we use multi browsers now
        directories = self.toolsetWidget.core.directories

        self.browserModel = ControlCurvesViewerModel(self.miniBrowser,
                                                     directories=directories,
                                                     activeDirs=self.toolsetWidget.core.activeDirectories,
                                                     uniformIcons=uniformIcons,
                                                     assetPreference=self.controlsPrefs.controlAssets)

        self.miniBrowser.setModel(self.browserModel)
        self.resizerWidget = ToolsetResizer(toolsetWidget=self.toolsetWidget, target=self.miniBrowser)

        # Tool Dots Menu
        self.toolDotsMenu = DotsMenu()
        # Rotate --------------------------------------
        toolTip = "Rotate the selected curves controls on this axis.\n" \
                  "The rotation is performed in the shape's object space\n" \
                  "not in its local space.\n" \
                  "Does not affect channel box rotate values."
        self.rotateComboBox = elements.ComboBoxRegular("",
                                                       cc.ROTATE_LIST,
                                                       toolTip=toolTip,
                                                       setIndex=0)
        toolTip = "Rotate the selected control\n(Shift faster, ctrl slower, alt reset)"
        self.rotatePosBtn = elements.styledButton("",
                                                  "arrowRotLeft",
                                                  self,
                                                  toolTip=toolTip,
                                                  style=uic.BTN_TRANSPARENT_BG,
                                                  minWidth=uic.BTN_W_ICN_SML)
        self.rotateNegBtn = elements.styledButton("", "arrowRotRight",
                                                  self,
                                                  toolTip=toolTip,
                                                  style=uic.BTN_TRANSPARENT_BG,
                                                  minWidth=uic.BTN_W_ICN_SML)
        # Orient Up Vector --------------------------------------
        toolTipUpAxis = "Select the up axis orientation. \n" \
                        "+X for joints \n" \
                        "+Y for world controls flat on ground\n" \
                        "+Z for front facing in world"
        self.orientVectorComboBox = elements.ComboBoxRegular("",
                                                             COMBO_UP_LIST,
                                                             toolTip=toolTipUpAxis,
                                                             setIndex=0,
                                                             boxRatio=1,
                                                             labelRatio=2)
        # Color label/color cmds widget  ----------------------------------------------------------------------
        # Color Section  ------------------------------------
        toolTip = "The color of the control to be created or selected controls."
        if self.uiMode == UI_MODE_COMPACT:  # build compact color widget
            self.colorSwatchBtn = elements.ColorHsvBtns(text="",
                                                        color=cc.CONTROL_DEFAULT_COLOR,
                                                        parent=self,
                                                        toolTip=toolTip,
                                                        btnRatio=4,
                                                        labelRatio=2,
                                                        colorWidgetRatio=21,
                                                        hsvRatio=15,
                                                        middleSpacing=uic.SMLPAD,
                                                        resetColor=cc.CONTROL_DEFAULT_COLOR)
        elif self.uiMode == UI_MODE_ADVANCED:  # build hsv buttons
            self.colorSwatchBtn = elements.ColorHsvBtns(text="Color",
                                                        color=cc.CONTROL_DEFAULT_COLOR,
                                                        parent=self,
                                                        toolTip=toolTip,
                                                        btnRatio=4,
                                                        labelRatio=2,
                                                        colorWidgetRatio=21,
                                                        hsvRatio=15,
                                                        middleSpacing=uic.SVLRG,
                                                        resetColor=cc.CONTROL_DEFAULT_COLOR)
            self.colorBtnMenuModeList = [("paintLine", "Get Color From Obj"),
                                         ("cursorSelect", "Select Similar"),
                                         ("cursorSelect", "Select With Color")]
            self.colorBtnMenu = elements.ExtendedMenu(searchVisible=True)
            self.colorSwatchBtn.setMenu(self.colorBtnMenu, modeList=self.colorBtnMenuModeList)  # right click
            self.colorSwatchBtn.setMenu(self.colorBtnMenu,
                                        mouseButton=QtCore.Qt.LeftButton)  # left click, modes set already
            toolTip = "Apply the GUI color to the selected controls."
            self.applyColorBtn = elements.styledButton("",
                                                       "paintLine",
                                                       toolTip=toolTip,
                                                       parent=self,
                                                       minWidth=uic.BTN_W_ICN_MED,
                                                       maxWidth=uic.BTN_W_ICN_MED)
        # Scale --------------------------------------
        toolTip = "The radius scale size of the control"
        editRatio = 2
        if self.uiMode == UI_MODE_ADVANCED:  # change the ratio for advanced
            editRatio = 1

        self.scaleFloat = elements.FloatEdit("Scale",
                                             "2.0",
                                             labelRatio=1,
                                             editRatio=editRatio,
                                             toolTip=toolTip)
        toolTip = "Scale controls smaller\n(Shift faster, ctrl slower, alt reset)"
        self.scaleDownBtn = elements.styledButton("", "scaleDown",
                                                  toolTip=toolTip,
                                                  style=uic.BTN_TRANSPARENT_BG,
                                                  minWidth=uic.BTN_W_ICN_SML)
        toolTip = "Scale controls larger\n(Shift faster, ctrl slower, alt reset)"
        self.scaleUpBtn = elements.styledButton("", "scaleUp",
                                                toolTip=toolTip,
                                                style=uic.BTN_TRANSPARENT_BG,
                                                minWidth=uic.BTN_W_ICN_SML)
        # Hierarchy Radio ------------------------------------
        radioNameList = ["Selected", "Hierarchy"]
        radioToolTipList = ["Affect only the selected joints/controls.",
                            "Affect the selection and all of its child joints/controls."]
        self.selHierarchyRadio = elements.RadioButtonGroup(radioList=radioNameList,
                                                           toolTipList=radioToolTipList,
                                                           default=0,
                                                           margins=(0, 0, 0, 0))
        # Build Type Combo --------------------------------------
        toolTip = "The build type of the controls. \n" \
                  "Match Selection Only: Will match controls only to the selected objects. \n" \
                  "Joint Shape Parent: Will attempt to shape parent the controls to selected joints. \n" \
                  "Constrain Obj Ctrl:  Will constrain the joints to the new controls, and controls to each other.  \n" \
                  "Constrain Obj Parent Ctrl:  Controls are parented to each other, joints are constrained to the controls. \n" \
                  "Constrain Obj Float Ctrls: Joints are constrained to the controls, the controls are not related to each other. "

        self.buildComboBox = elements.ComboBoxRegular("",
                                                      items=api.CONTROL_BUILD_TYPE_LIST,
                                                      setIndex=1,
                                                      toolTip=toolTip)
        # Change Button ----------------------------------
        toolTip = "Changes all selected controls to the thumbnail. \n" \
                  "If nothing is selected will create at world center. "
        self.changeBtn = elements.styledButton("Change",
                                               "starControl",
                                               self,
                                               toolTip=toolTip,
                                               style=uic.BTN_DEFAULT)
        # Create Button ----------------------------------
        toolTip = "Builds new control curves, will match to selected object/s. "
        self.buildMatchBtn = elements.styledButton("Create",
                                                   "starControl",
                                                   self,
                                                   toolTip=toolTip,
                                                   style=uic.BTN_DEFAULT)
        if self.uiMode == UI_MODE_ADVANCED:  # widgets that only exist in the advanced mode
            # Scale Combo ------------------------------------
            toolTip = "Scale the selected curves by all or a single axis\n" \
                      "The scale is performed in the shape's object space\n" \
                      "not in its local space.\n" \
                      "Does not affect channel box scale values."
            self.scaleComboBx = elements.ComboBoxRegular("",
                                                         cc.SCALE_LIST,
                                                         self,
                                                         toolTip=toolTip,
                                                         setIndex=0)
            # Line Width ------------------------------------
            toolTip = "Sets the thickness of the control curve lines.\n" \
                      "A line thickness of -1 uses the global preferences setting, usually 1."
            self.lineWidthTxt = elements.IntEdit(label="Line Width",
                                                 editText="-1",
                                                 labelRatio=1,
                                                 editRatio=1,
                                                 toolTip=toolTip)
            # Select Color Button ------------------------------------
            toolTip = "Select all controls with the current color."
            self.selectColorBtn = elements.styledButton(text="Select From Color",
                                                        icon="cursorSelect",
                                                        toolTip=toolTip,
                                                        parent=self,
                                                        style=uic.BTN_LABEL_SML)
            # Get Color Button ------------------------------------
            toolTip = "Get color from the first selected object."
            self.getColorBtn = elements.styledButton(text="Get Color",
                                                     icon="arrowLeft",
                                                     toolTip=toolTip,
                                                     parent=self,
                                                     style=uic.BTN_LABEL_SML)
            # Orient Up Axis ------------------------------------
            self.upAxisLabel = elements.Label(text="Up Axis", toolTip=toolTipUpAxis)
            # Set Default Scale Button ------------------------------------
            toolTip = "Set the current scale of the control to be it's default scale.\n" \
                      "Useful while resetting. To reset alt-click the scale elements."
            self.setScaleBtn = elements.styledButton(text="Set Default Scale",
                                                     icon="freezeSrt",
                                                     toolTip=toolTip,
                                                     parent=self,
                                                     style=uic.BTN_LABEL_SML)
            # Group ------------------------------------
            toolTip = "Add groups to zero out the controls/joints (recommended)"
            self.grpJointsCheckBx = elements.CheckBox("Group",
                                                      checked=True,
                                                      parent=self,
                                                      toolTip=toolTip)
            # Freeze Joints ------------------------------------
            toolTip = "Freeze transform joints only, while adding `Joint Controls` (recommended)"
            self.freezeJntsCheckBx = elements.CheckBox("Freeze Jnt",
                                                       checked=True,
                                                       parent=self,
                                                       toolTip=toolTip)

    def selectionChanged(self, image, item):
        """ Set the infoEmbedWindow nameEdit to disabled if its one of the default controls

        :param image:
        :type image:
        :param item:
        :type item:
        :return:
        :rtype:
        """
        thumbView = self.sender()  # type: elements.MiniBrowser
        thumbView.infoEmbedWindow.nameEdit.setEnabled(
            not (item.name in self.toolsetWidget.core.controlPrefs.controlAssets.defaultAssetItems()))


class DotsMenu(IconMenuButton):
    menuIcon = "menudots"

    groupEnabled = QtCore.Signal(object)
    freezeEnabled = QtCore.Signal(object)

    getColor = QtCore.Signal()
    selectSimilar = QtCore.Signal()
    selectColor = QtCore.Signal()

    setDefaultScale = QtCore.Signal()
    delZooTrackerAttrs = QtCore.Signal()

    def __init__(self, parent=None):
        """
        """
        super(DotsMenu, self).__init__(parent=parent)
        self.setIconByName(self.menuIcon, size=16)
        self.setMenuAlign(QtCore.Qt.AlignRight)
        self.setToolTip("File menu. Control Creator")
        # Build the static menu
        # Enable Checkboxes --------------------------------------
        self.groupState = self.addAction("Group New Controls",
                                         connect=lambda x: self.groupEnabled.emit(x),
                                         checkable=True,
                                         checked=True)
        self.freezeState = self.addAction("Freeze New Controls",
                                          connect=lambda x: self.freezeEnabled.emit(x),
                                          checkable=True,
                                          checked=True)
        # Reset To Defaults --------------------------------------
        self.addSeparator()
        colorIcon = iconlib.iconColorized("paintLine", utils.dpiScale(16))
        self.addAction("Get Color", connect=lambda: self.getColor.emit(), icon=colorIcon)

        cursorIcon = iconlib.iconColorized("cursorSelect", utils.dpiScale(16))
        self.addAction("Select Similar Color", connect=lambda: self.selectSimilar.emit(), icon=cursorIcon)

        self.addAction("Select From Color", connect=lambda: self.selectColor.emit(), icon=cursorIcon)
        # Reset To Defaults --------------------------------------
        self.addSeparator()
        scaleIcon = iconlib.iconColorized("freezeSrt", utils.dpiScale(16))
        self.addAction("Set Default Scale", connect=lambda: self.setDefaultScale.emit(), icon=scaleIcon)
        delAttrIcon = iconlib.iconColorized("xCircleMark2", utils.dpiScale(16))
        self.addAction("Delete Zoo Tracker Attrs", connect=lambda: self.delZooTrackerAttrs.emit(), icon=delAttrIcon)


class GuiCompact(AllWidgets):
    def __init__(self, parent=None, properties=None, uiMode=UI_MODE_COMPACT, toolsetWidget=None, directory=None):
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
                                         uiMode=uiMode, toolsetWidget=toolsetWidget, directories=directory)
        # Main Layout
        mainLayout = elements.vBoxLayout(self,
                                         margins=(uic.WINSIDEPAD, uic.WINTOPPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=0)
        # Rotate Layout -------------------------------
        rotateLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SLRG)
        rotateLayout.addWidget(self.rotateComboBox, 4)
        rotateLayout.addWidget(self.rotatePosBtn, 1)
        rotateLayout.addWidget(self.rotateNegBtn, 1)
        # Color Layout -------------------------------
        colorLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SLRG)
        colorLayout.addWidget(self.colorSwatchBtn, 1)
        # Combo Dots Layout -------------------------------
        comboDotsLayout = elements.hBoxLayout(spacing=uic.SLRG)
        comboDotsLayout.addWidget(self.orientVectorComboBox, 4)
        comboDotsLayout.addItem(elements.Spacer(32, 5))
        comboDotsLayout.addWidget(self.toolDotsMenu, 1)
        # Scale Layout -------------------------------
        scaleLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SLRG)
        scaleLayout.addWidget(self.scaleFloat, 4)
        scaleLayout.addWidget(self.scaleDownBtn, 1)
        scaleLayout.addWidget(self.scaleUpBtn, 1)
        # Bottom Grid Layout -------------------------------
        gridLayout = elements.GridLayout(margins=(0, 0, 0, 0), spacing=uic.SPACING)
        gridLayout.addLayout(colorLayout, 0, 0)
        gridLayout.addLayout(comboDotsLayout, 0, 1)
        gridLayout.addLayout(scaleLayout, 1, 0)
        gridLayout.addLayout(rotateLayout, 1, 1)
        gridLayout.addWidget(self.buildComboBox, 2, 0)
        gridLayout.addWidget(self.selHierarchyRadio, 2, 1)
        gridLayout.setColumnStretch(0, 1)
        gridLayout.setColumnStretch(1, 1)
        # Button Layout -------------------------------
        buttonLayout = elements.hBoxLayout(margins=(0, uic.SSML, 0, 0), spacing=uic.SPACING)
        buttonLayout.addWidget(self.changeBtn, 1)
        buttonLayout.addWidget(self.buildMatchBtn, 1)
        # Add to main layout -------------------------------
        mainLayout.addWidget(self.miniBrowser)
        mainLayout.addWidget(self.resizerWidget)
        mainLayout.addLayout(gridLayout)
        mainLayout.addLayout(buttonLayout)
        mainLayout.addStretch(1)


class GuiAdvanced(AllWidgets):
    def __init__(self, parent=None, properties=None, uiMode=UI_MODE_ADVANCED, toolsetWidget=None, directory=None):
        """Builds the advanced version of GUI, subclassed from AllWidgets() which creates the widgets:

            default uiMode - 1 is advanced (UI_MODE_ADVANCED)

        :param parent: the parent of this widget
        :type parent: qtObject
        :param properties: Special dictionary which tracks the properties of each widget for the GUI
        :type properties: list[dict]
        :param uiMode: The UI mode to build, either UI_MODE_COMPACT = 0 or UI_MODE_ADVANCED = 1
        :type uiMode: int
        :param toolsetWidget: The instance of the toolsetWidget class, needed for setting properties.
        :type toolsetWidget: object
        """
        super(GuiAdvanced, self).__init__(parent=parent, properties=properties,
                                          uiMode=uiMode, toolsetWidget=toolsetWidget, directories=directory)
        # Main Layout
        mainLayout = elements.vBoxLayout(self,
                                         margins=(uic.WINSIDEPAD, uic.WINTOPPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=0)
        # Rotate Layout
        rotateLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SLRG)
        rotateLayout.addWidget(self.rotateComboBox, 4)
        rotateLayout.addWidget(self.rotatePosBtn, 1)
        rotateLayout.addWidget(self.rotateNegBtn, 1)
        # Scale Layout
        scaleLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SLRG)
        scaleLayout.addWidget(self.scaleComboBx, 4)
        scaleLayout.addWidget(self.scaleDownBtn, 1)
        scaleLayout.addWidget(self.scaleUpBtn, 1)
        # Color Layout
        colorLayout = elements.hBoxLayout(margins=(0, uic.SSML, 0, uic.SREG), spacing=uic.SLRG)
        colorLayout.addWidget(self.colorSwatchBtn, 8)
        colorLayout.addWidget(self.applyColorBtn, 1)
        # Up Axis Layout
        upAxisLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SLRG)
        upAxisLayout.addWidget(self.orientVectorComboBox, 1)
        # Top Grid Layout
        gridLayout1 = elements.GridLayout(margins=(0, 0, 0, 0), hSpacing=uic.SLRG, vSpacing=uic.SREG)
        gridLayout1.addWidget(self.scaleFloat, 0, 0)
        gridLayout1.addLayout(scaleLayout, 0, 1)
        gridLayout1.addWidget(self.lineWidthTxt, 1, 0)
        gridLayout1.addLayout(rotateLayout, 1, 1)
        gridLayout1.setColumnStretch(0, 1)
        gridLayout1.setColumnStretch(1, 1)
        # Bottom Grid Layout
        gridLayout2 = elements.GridLayout(margins=(0, 0, 0, 0), hSpacing=uic.SLRG, vSpacing=uic.SREG)
        gridLayout2.addWidget(self.selectColorBtn, 0, 0)
        gridLayout2.addWidget(self.getColorBtn, 0, 1)
        gridLayout2.addLayout(upAxisLayout, 1, 0)
        gridLayout2.addWidget(self.setScaleBtn, 1, 1)
        gridLayout2.addWidget(self.grpJointsCheckBx, 3, 0)
        gridLayout2.addWidget(self.freezeJntsCheckBx, 3, 1)
        gridLayout2.addWidget(self.buildComboBox, 2, 0)
        gridLayout2.addWidget(self.selHierarchyRadio, 2, 1)
        gridLayout2.addWidget(self.changeBtn, 4, 0)
        gridLayout2.addWidget(self.buildMatchBtn, 4, 1)

        gridLayout2.setColumnStretch(0, 1)
        gridLayout2.setColumnStretch(1, 1)

        # Add to main layout
        mainLayout.addWidget(self.miniBrowser)
        mainLayout.addWidget(self.resizerWidget)
        mainLayout.addLayout(gridLayout1)
        mainLayout.addLayout(colorLayout)
        mainLayout.addLayout(gridLayout2)
        mainLayout.addStretch(1)
