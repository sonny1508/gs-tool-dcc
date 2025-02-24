import os
from functools import partial

from zoo.apps.toolsetsui.mixins import MiniBrowserMixin
from zoo.libs.pyqt.extended.imageview import model
from zoo.libs.pyqt.uiconstants import QT_SUPPORTED_EXTENSIONS

from zoovendor.Qt import QtWidgets, QtCore

from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.apps.toolsetsui.widgets.toolsetresizer import ToolsetResizer
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements
from zoo.libs.utils import output
from zoo.core.util import zlogging
from zoo.preferences.interfaces import camerainterfaces, coreinterfaces
from zoo.libs.zooscene import zooscenefiles

from zoo.libs.maya.cmds.cameras import imageplanes
from zoo.libs.maya.cmds.objutils import attributes
from zoo.apps.toolsetsui import toolsetcallbacks

logger = zlogging.getLogger(__name__)

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1


class ImagePlaneTool(toolsetwidget.ToolsetWidget, MiniBrowserMixin):
    id = "imagePlaneTool"
    uiData = {"label": "Image Plane Tool",
              "icon": "imagePlane",
              "tooltip": "Mini browser for image planes",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-image-plane-tool/"
              }

    # ------------------------------------
    # START UP
    # ------------------------------------

    def preContentSetup(self):
        """First code to run"""
        self.toolsetWidget = self  # needed for callback decorators
        self.cameraPrefs = camerainterfaces.cameraToolInterface()
        self.setAssetPreferences(self.cameraPrefs.imagePlaneAssets)

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

        self.ignoreInstantApply = False
        self.refreshUpdateUIFromSelection(update=True)  # update GUI from current in scene selection
        self.setMiniBrowsers([w.miniBrowser for w in self.widgets()])
        self.uiconnections()
        self.startSelectionCallback()  # start selection callback

    def currentWidget(self):
        """ Current active widget

        :return:
        :rtype:  AllWidgets
        """
        return super(ImagePlaneTool, self).currentWidget()

    def widgets(self):
        """ List of widgets

        :return:
        :rtype: list[AllWidgets]
        """
        return super(ImagePlaneTool, self).widgets()

    # ------------------------------------
    # PROPERTIES
    # ------------------------------------

    def initializeProperties(self):
        return [{"name": "rotate", "label": "Rotate", "value": 0.0},
                {"name": "scale", "label": "Scale", "value": 1.0},
                {"name": "offsetX", "label": "Offset X", "value": 0.0},
                {"name": "offsetY", "label": "Offset Y", "value": 0.0},
                {"name": "opacity", "label": "Opacity", "value": 1.0}]

    def updateFromProperties(self):
        """ Runs update properties from the base class.

        Widgets will auto update from self.properties if linked via:

            self.linkProperty(widget, "propertyKey")
            or
            self.toolsetWidget.linkProperty(widget, "propertyKey")

        Add code after super() useful for changes such as forcing UI decimal places
        or manually adding unsupported widgets
        """
        self.properties.offsetLeftRightFloatSldr.value = round(self.properties.offsetLeftRightFloatSldr.value, 3)
        self.properties.offsetUpDownFloatSldr.value = round(self.properties.offsetUpDownFloatSldr.value, 3)
        self.properties.opacityFloatSldr.value = round(self.properties.opacityFloatSldr.value, 3)
        super(ImagePlaneTool, self).updateFromProperties()


    def renameAsset(self):
        """Renames the asset on disk, can fail if alembic animation. Alembic animation must not be loaded"""
        currentImageNoExt = self.currentWidget().browserModel.currentImage
        self.zooScenePath = self.currentWidget().miniBrowser.itemFilePath()
        if not currentImageNoExt or self.zooScenePath is None:  # no image has been selected
            output.displayWarning("Please select an image to rename.")
            return

        currentImageNoExt = os.path.splitext(currentImageNoExt)[0]
        message = "Rename '{}' and related dependencies as:".format(currentImageNoExt)
        renameText = elements.MessageBox.inputDialog(title="Rename Model Asset",
                                                     text=currentImageNoExt, parent=None,
                                                     message=message)
        if not renameText:
            return
        # Do the rename
        fileRenameList = zooscenefiles.renameZooSceneOnDisk(renameText, self.zooScenePath)
        if not fileRenameList:
            output.displayWarning("Files could not be renamed, they are probably in use by the current scene. "
                                  "Do not have the images active in the scene, or check your file permissions.")
            return
        output.displayInfo("Success: Files `{}*` Have Been Renamed To `{}*`".format(currentImageNoExt, renameText))
        self.refreshThumbs()

    def deletePresetPopup(self):
        """Popup window that asks the user if they want to delete the currently selected asset from disk?"""
        filenameNoSuffix = self.currentWidget().browserModel.currentImage
        if not filenameNoSuffix:
            output.displayWarning("Nothing selected. Please select an image to delete.")

        fullImagePath = self.currentWidget().miniBrowser.selectedMetadata()['zooFilePath']
        # Build popup window
        browserModel = self.currentWidget().browserModel
        item = browserModel.currentItem
        filenameWithExt = item.fileNameExt()
        message = "Warning: Delete the preset `{}` and it's dependencies?  " \
                  "This will permanently delete these file/s from disk?".format(filenameWithExt)
        result = elements.MessageBox.showOK(title="Delete Image From Disk?",
                                            message=message)  # None will parent to Maya
        # After answering Ok or cancel
        if result:  # Ok was pressed
            fullImagePath = os.path.join(item.directory, item.fileNameExt())
            filesFullPathDeleted = zooscenefiles.deleteZooSceneFiles(fullImagePath, message=True)

            self.refreshThumbs()
            output.displayInfo("Success, File/s Deleted: {}".format(filesFullPathDeleted))

    # ------------------------------------
    # CALLBACKS
    # ------------------------------------

    def mayaSelectionChanged(self, selection):
        """Run when the callback selection changes, updates the GUI if an object is selected


        Callbacks are handled automatically by toolsetcallbacks.py which this class inherits"""
        if not selection:  # then don't update
            return
        self.refreshUpdateUIFromSelection()  # will update the GUI

    # ------------------------------------
    # LOGIC
    # ------------------------------------

    def refreshUpdateUIFromSelection(self, update=True):
        """Gets all the attributes (properties) from the first selected imagePlane and updates the scene

        :param update: if False will skip updating the UI, used on startup because it's auto
        :type update: bool
        """
        self.attrDict = imageplanes.getImagePlaneAttrsWithScaleAuto(message=False)
        if not self.attrDict:  # no image plane found
            return
        self.properties.opacityFloatSldr.value = self.attrDict["alphaGain"]
        self.properties.offsetLeftRightFloatSldr.value = self.attrDict["offsetX"]
        self.properties.offsetUpDownFloatSldr.value = self.attrDict["offsetY"]
        self.properties.scaleFloatSldr.value = self.attrDict["scale"]
        self.properties.rotateFloatSldr.value = self.attrDict["rotate"]
        if update:
            self.updateFromProperties()

    def setAttrsImagePlane(self):
        """Sets the attributes on an image plane from the current values in the GUI
        """
        attrDict = dict()
        attrDict["alphaGain"] = self.properties.opacityFloatSldr.value
        attrDict["rotate"] = self.properties.rotateFloatSldr.value
        attrDict["scale"] = self.properties.scaleFloatSldr.value
        attrDict["offsetX"] = self.properties.offsetLeftRightFloatSldr.value
        attrDict["offsetY"] = self.properties.offsetUpDownFloatSldr.value
        iPShape, iPTransform, camShape = imageplanes.autoImagePlaneInfo()
        if iPShape:
            attributes.setFloatAttrsDict(iPShape, attrDict)
            imageplanes.scaleImagePlaneAuto(self.properties.scale.value)

    @toolsetwidget.ToolsetWidget.undoDecorator
    @toolsetcallbacks.ignoreCallbackDecorator
    def createImagePlane(self, image="", forceNew=False):
        """Main method, creates/modified the selected image plane.
        Creates an image plane if one is not already selected or attached to the current active viewport

        :param forceNew: if True will create a new image plane on the camera, even if one already exists
        :type forceNew: bool
        """
        currentImage = self.currentWidget().miniBrowser.itemFilePath()
        if not currentImage:
            output.displayWarning("Please select an image to create.")
            return
        fullImagePath = self.currentWidget().miniBrowser.currentItem().fullPath()
        iPShape, created = imageplanes.createImagePlaneAuto(iPPath=fullImagePath, forceCreate=forceNew)
        if created and not forceNew:  # sets attrs from GUI if not being built as new
            pass
            # self.setAttrsImagePlane()
        else:  # refresh the GUI with the defaults of the new image plane
            self.refreshUpdateUIFromSelection()

    @toolsetwidget.ToolsetWidget.undoDecorator
    @toolsetcallbacks.ignoreCallbackDecorator
    def moveImageplane(self, position="center"):
        """Moves the image plane to one of 5 preset values, will offset and scale.

        :param position: The position to move to, is a string "topLeft", "botLeft", "center" etc
        :type position: str
        """
        if position == "topLeft":
            values = (-0.45, 0.3, 0.4)  # x, y, scale
        elif position == "topRight":
            values = (0.45, 0.3, 0.4)  # x, y, scale
        elif position == "botLeft":
            values = (-0.45, -0.3, 0.4)  # x, y, scale
        elif position == "botRight":
            values = (0.45, -0.3, 0.4)  # x, y, scale
        else:  # position == "center"
            values = (0.0, 0.0, 1.0)  # x, y, scale
        self.properties.scale.value = values[2]
        self.properties.offsetLeftRightFloatSldr.value = values[0]
        self.properties.offsetUpDownFloatSldr.value = values[1]
        imageplanes.moveScaleImagePlaneAuto(values[2], values[0], values[1])  # scale, x, y
        self.updateFromProperties()  # updates the sliders & GUI

    @toolsetcallbacks.ignoreCallbackDecorator
    def setImagePlaneOffsetX(self):
        """Slider Offset Left Right """
        imageplanes.offsetXImagePlaneAuto(self.properties.offsetLeftRightFloatSldr.value, message=False)
        self.properties.offsetX.value = self.properties.offsetLeftRightFloatSldr.value  # not needed?

    @toolsetcallbacks.ignoreCallbackDecorator
    def setImagePlaneOffsetY(self):
        """Slider Offset Up Down """
        imageplanes.offsetYImagePlaneAuto(self.properties.offsetUpDownFloatSldr.value, message=False)
        self.properties.offsetY.value = self.properties.offsetUpDownFloatSldr.value  # not needed?

    @toolsetcallbacks.ignoreCallbackDecorator
    def setImagePlaneScale(self):
        """Slider Scale """
        imageplanes.scaleImagePlaneAuto(self.properties.scaleFloatSldr.value)

    @toolsetcallbacks.ignoreCallbackDecorator
    def setImagePlaneRotate(self):
        """Slider Rotate """
        imageplanes.rotImagePlaneAuto(self.properties.rotateFloatSldr.value)

    @toolsetcallbacks.ignoreCallbackDecorator
    def setImagePlaneOpacity(self):
        """Slider Offset Opacity """
        imageplanes.opacityImagePlaneAuto(self.properties.opacityFloatSldr.value, message=False)

    @toolsetwidget.ToolsetWidget.undoDecorator
    @toolsetcallbacks.ignoreCallbackDecorator
    def placeInFront(self):
        imageplanes.placeInFrontAuto()

    @toolsetwidget.ToolsetWidget.undoDecorator
    @toolsetcallbacks.ignoreCallbackDecorator
    def placeBehind(self):
        imageplanes.placeBehindAuto()

    @toolsetwidget.ToolsetWidget.undoDecorator
    @toolsetcallbacks.ignoreCallbackDecorator
    def toggleLayerVis(self):
        """Vis toggles any layer containing the string `imagePlanes_lyr`"""
        imageplanes.toggleVisImagePlaneLayer()

    @toolsetwidget.ToolsetWidget.undoDecorator
    @toolsetcallbacks.ignoreCallbackDecorator
    def toggleLayerRef(self):
        """Vis toggles any layer containing the string `imagePlanes_lyr`"""
        imageplanes.toggleRefImagePlaneLayer()

    def getImagePlaneAttrs(self):
        """Retrieves attribute values from the active image plane, selected or camera with focus
        """
        imagePlaneDict = imageplanes.getImagePlaneAttrsAuto()
        if not imagePlaneDict:
            return
        self.properties.rotFloatSldr.value = imagePlaneDict["rotate"]

    # ------------------------------------
    # Slider events
    # ------------------------------------

    def clamp(self, value):
        if value > 1.0:
            value = 1.0
        elif value < 0.0:
            value = 0.0
        return value

    def sliderPressed(self):
        """Get the image plane shape, and open the undo chunk if found
        """
        self.refreshUpdateUIFromSelection(update=False)
        self.ipShape, iPTransform, camShape = imageplanes.autoImagePlaneInfo(message=False)
        self.openUndoChunk()

    def sliderScrolled(self, event):
        """Slider scrolled

        :param event: A tuple x and y offset of the virtual slider (21.0, 1.0021)
        :type event: :class:`zoo.libs.pyqt.extended.imageview.thumbnail.virtualslider.MouseSlideEvent`
        """
        x, y = event.value

        # Rotate ctrl + shift
        if event.modifiers == QtCore.Qt.ControlModifier | QtCore.Qt.ShiftModifier:
            rotate = self.properties.rotateFloatSldr.value + x * 50
            imageplanes.rotImagePlane(self.ipShape, rotate)
            # output.inViewMessage("<hl>Rotate</hl>: {}".format(rotate))

        # Opacity ctrl + alt
        elif event.modifiers == QtCore.Qt.ControlModifier | QtCore.Qt.AltModifier:
            alphaGain = self.clamp(self.properties.opacityFloatSldr.value + x)
            imageplanes.opacityImagePlane(self.ipShape, alphaGain)
            output.inViewMessage("<hl>Alpha Gain</hl>: {}".format("{:.2f}".format(alphaGain)))  # Is helpful

        # Scale shift
        elif event.modifiers == QtCore.Qt.ShiftModifier:
            if event.direction == elements.VirtualSlider.Horizontal:
                offsetX = self.properties.offsetLeftRightFloatSldr.value + x
                imageplanes.offsetXImagePlane(self.ipShape, offsetX)
            else:
                offsetY = self.properties.offsetUpDownFloatSldr.value + y
                imageplanes.offsetYImagePlane(self.ipShape, offsetY)

        # Scale ctrl
        elif event.modifiers == QtCore.Qt.ControlModifier:
            scale = self.properties.scaleFloatSldr.value + x
            imageplanes.scaleImagePlane(self.ipShape, scale)

        # Position
        else:
            offsetX = self.properties.offsetLeftRightFloatSldr.value + x
            offsetY = self.properties.offsetUpDownFloatSldr.value + y
            imageplanes.offsetXImagePlane(self.ipShape, offsetX)
            imageplanes.offsetYImagePlane(self.ipShape, offsetY)

    def sliderReleased(self, event):
        """ Save all the settings into the properties

        :param event: A tuple x and y offset of the virtual slider (21.0, 1.0021)
        :type event: :class:`zoo.libs.pyqt.extended.imageview.thumbnail.virtualslider.MouseSlideEvent`
        """
        self.refreshUpdateUIFromSelection(update=True)
        self.closeUndoChunk()

    # ------------------------------------
    # CONNECTIONS
    # ------------------------------------

    def uiconnections(self):
        """Hooks up the actual button/widgets functionality
        """
        super(ImagePlaneTool, self).uiconnections()
        for uiInstance in self.widgets():
            # Create New
            uiInstance.createNewBtn.clicked.connect(partial(self.createImagePlane, forceNew=True))
            # Dots menu viewer
            uiInstance.browserModel.doubleClicked.connect(self.createImagePlane)
            # Dots menu viewer
            uiInstance.miniBrowser.dotsMenu.applyAction.connect(self.createImagePlane)
            uiInstance.miniBrowser.dotsMenu.renameAction.connect(self.renameAsset)
            uiInstance.miniBrowser.dotsMenu.deleteAction.connect(self.deletePresetPopup)

            # Place buttons
            uiInstance.placeTopLeftBtn.clicked.connect(partial(self.moveImageplane, position="topLeft"))
            uiInstance.placeTopRightBtn.clicked.connect(partial(self.moveImageplane, position="topRight"))
            uiInstance.placeBotLeftBtn.clicked.connect(partial(self.moveImageplane, position="botLeft"))
            uiInstance.placeBotRightBtn.clicked.connect(partial(self.moveImageplane, position="botRight"))
            uiInstance.placeCenterBtn.clicked.connect(partial(self.moveImageplane, position="center"))

            # Offset Sliders ------------------------------------------
            uiInstance.offsetLeftRightFloatSldr.numSliderChanged.connect(self.setImagePlaneOffsetX)
            uiInstance.offsetUpDownFloatSldr.numSliderChanged.connect(self.setImagePlaneOffsetY)
            # Scale Slider
            uiInstance.scaleFloatSldr.numSliderChanged.connect(self.setImagePlaneScale)
            # Rotate Slider
            uiInstance.rotateFloatSldr.numSliderChanged.connect(self.setImagePlaneRotate)
            # Opacity Slider
            uiInstance.opacityFloatSldr.numSliderChanged.connect(self.setImagePlaneOpacity)
            sliderList = [uiInstance.offsetLeftRightFloatSldr, uiInstance.offsetUpDownFloatSldr,
                          uiInstance.opacityFloatSldr, uiInstance.scaleFloatSldr, uiInstance.rotateFloatSldr]
            for slider in sliderList:
                slider.sliderPressed.connect(self.openUndoChunk)
                slider.sliderReleased.connect(self.closeUndoChunk)

            # Place front back -----------------------------------
            uiInstance.placeFrontBtn.clicked.connect(self.placeInFront)
            uiInstance.placeBehindBtn.clicked.connect(self.placeBehind)
            # toggle Vis Layer
            uiInstance.toggleLyrVisBtn.clicked.connect(self.toggleLayerVis)
            uiInstance.toggleLyrSelBtn.clicked.connect(self.toggleLayerRef)
            uiInstance.miniBrowser.sliderPressed.connect(self.sliderPressed)
            uiInstance.miniBrowser.sliderReleased.connect(self.sliderReleased)  # closeUndoChunk run in slider released
            uiInstance.miniBrowser.sliderChanged.connect(self.sliderScrolled)

        # callback connections
        self.selectionCallbacks.callback.connect(self.mayaSelectionChanged)  # monitor selection
        self.toolsetActivated.connect(self.startSelectionCallback)
        self.toolsetDeactivated.connect(self.stopSelectionCallback)


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
        :type toolsetWidget: qtObject
        """
        super(AllWidgets, self).__init__(parent=parent)
        self.savedThumbHeight = None
        self.toolsetWidget = toolsetWidget
        self.properties = properties
        self.uiMode = uiMode
        # Thumbnail Viewer --------------------------------------------
        self.themePref = coreinterfaces.coreInterface()
        # viewer widget and model
        self.prefs = camerainterfaces.cameraToolInterface()
        uniformIcons = self.prefs.imagePlaneAssets.browserUniformIcons()
        self.miniBrowser = elements.MiniBrowser(parent=self,
                                                toolsetWidget=self.toolsetWidget,
                                                columns=3,
                                                fixedHeight=382,
                                                uniformIcons=uniformIcons,
                                                itemName="Image",
                                                applyIcon="imagePlane",
                                                snapshotActive=False,
                                                snapshotNewActive=True,
                                                clipboardActive=True,
                                                newActive=False,
                                                selectDirectoriesActive=True,
                                                virtualSlider=True)
        speed = 0.006
        self.miniBrowser.setSliderSettings(directions=elements.VirtualSlider.Both,
                                           slowSpeed=speed, speed=speed, fastSpeed=speed,
                                           step=2)
        self.miniBrowser.dotsMenu.setDirectoryActive(False) # todo: remove this, we dont need this now that we have the directory popups

        self.browserModel = model.MiniBrowserFileModel(self.miniBrowser, extensions=QT_SUPPORTED_EXTENSIONS,
                                                       directories=self.prefs.imagePlaneAssets.browserFolderPaths(),
                                                       uniformIcons=uniformIcons,
                                                       assetPref=self.prefs.imagePlaneAssets)

        self.miniBrowser.setModel(self.browserModel)
        self.resizerWidget = ToolsetResizer(toolsetWidget=self.toolsetWidget, target=self.miniBrowser, fixedHeight=11)
        # Top Icons --------------------------------------------
        toolTip = "Move the selected or current image plane to the top left position."
        self.placeTopLeftBtn = elements.styledButton("", icon="moveTopLeft",
                                                     toolTip=toolTip,
                                                     style=uic.BTN_TRANSPARENT_BG,
                                                     minWidth=uic.BTN_W_ICN_SML)
        toolTip = "Move the selected or current image plane to the top right position."
        self.placeTopRightBtn = elements.styledButton("", "moveTopRight",
                                                      toolTip=toolTip,
                                                      style=uic.BTN_TRANSPARENT_BG,
                                                      minWidth=uic.BTN_W_ICN_SML)
        toolTip = "Move the selected or current image plane to the bot left position."
        self.placeBotLeftBtn = elements.styledButton("", "moveBotLeft",
                                                     toolTip=toolTip,
                                                     style=uic.BTN_TRANSPARENT_BG,
                                                     minWidth=uic.BTN_W_ICN_SML)
        toolTip = "Move the selected or current image plane to the bot right position."
        self.placeBotRightBtn = elements.styledButton("", "moveBotRight",
                                                      toolTip=toolTip,
                                                      style=uic.BTN_TRANSPARENT_BG,
                                                      minWidth=uic.BTN_W_ICN_SML)
        toolTip = "Move the selected or current image plane to the center position."
        self.placeCenterBtn = elements.styledButton("", "moveCenter",
                                                    toolTip=toolTip,
                                                    style=uic.BTN_TRANSPARENT_BG,
                                                    minWidth=uic.BTN_W_ICN_SML)
        # Offset Up Down Slider --------------------------------------------------------
        toolTip = "Offset the image plane up and down"
        self.offsetUpDownFloatSldr = elements.FloatSlider(label="Up/Down",
                                                          defaultValue=0.0,
                                                          toolTip=toolTip,
                                                          sliderMin=-1.0,
                                                          sliderMax=1.0,
                                                          decimalPlaces=3,
                                                          labelRatio=1,
                                                          editBoxRatio=1,
                                                          sliderRatio=1)
        # Offset Left Right Slider --------------------------------------------------------
        toolTip = "Offset the selected image plane left and right"
        self.offsetLeftRightFloatSldr = elements.FloatSlider(label="Left/Right",
                                                             defaultValue=0.0,
                                                             toolTip=toolTip,
                                                             sliderMin=-1.0,
                                                             sliderMax=1.0,
                                                             decimalPlaces=3,
                                                             labelRatio=1,
                                                             editBoxRatio=1,
                                                             sliderRatio=1)
        # Scale Slider --------------------------------------------------------
        toolTip = "Scale the selected image plane"
        self.scaleFloatSldr = elements.FloatSlider(label="Scale",
                                                    defaultValue=1.0,
                                                    toolTip=toolTip,
                                                    sliderMin=0.0,
                                                    sliderMax=1.5,
                                                    dynamicMax=True,
                                                    dynamicMin=True,
                                                    decimalPlaces=3,
                                                    labelRatio=1,
                                                    editBoxRatio=1,
                                                    sliderRatio=1)
        # Rotate Slider --------------------------------------------------------
        toolTip = "Rotate the selected image plane"
        self.rotateFloatSldr = elements.FloatSlider(label="Rotate",
                                                             defaultValue=0.0,
                                                             toolTip=toolTip,
                                                             sliderMin=-90,
                                                             sliderMax=90,
                                                             dynamicMax=True,
                                                             dynamicMin=True,
                                                             decimalPlaces=3,
                                                             labelRatio=1,
                                                             editBoxRatio=1,
                                                             sliderRatio=1)
        # Opacity Slider --------------------------------------------------------
        toolTip = "Opacity (transparency) value of the selected image plane"
        self.opacityFloatSldr = elements.FloatSlider(label="Opacity",
                                                     defaultValue=1.0,
                                                     toolTip=toolTip,
                                                     sliderMin=0.0,
                                                     sliderMax=1.0,
                                                     decimalPlaces=3,
                                                     labelRatio=1,
                                                     editBoxRatio=1,
                                                     sliderRatio=1)
        # Place Front Behind Button ---------------------------------------
        toolTip = "Move image plane to the camera near plane"
        self.placeFrontBtn = elements.styledButton("Place Front/Behind",
                                                   "arrowMoveFront",
                                                   toolTip=toolTip,
                                                   style=uic.BTN_LABEL_SML)
        toolTip = "Move image plane to the camera far plane"
        self.placeBehindBtn = elements.styledButton("",
                                                    "arrowMoveBack",
                                                    toolTip=toolTip,
                                                    style=uic.BTN_LABEL_SML)
        # Create New Button ---------------------------------------
        toolTip = "Creates a new image plane. Use to add multiple image planes. \n\n" \
                  "Tip: Browser Icon Virtual Sliders \n\n" \
                  " MMB (Middle Mouse Button Click) + Drag - Position \n" \
                  " MMB Shift + Drag - Position single axis \n" \
                  " MMB Ctrl + Drag - Scale \n" \
                  " MMB Shift + Ctrl + Drag - Rotate \n" \
                  " MMB Alt + Ctrl + Drag - Opacity"
        self.createNewBtn = elements.styledButton("Create New",
                                                  "imagePlane",
                                                  toolTip=toolTip,
                                                  style=uic.BTN_DEFAULT)
        # Toggle Layer Vis Button ---------------------------------------
        toolTip = "Toggles the visibility of the `imagePlanes_lyr` if it exists."
        self.toggleLyrVisBtn = elements.styledButton("Toggle Layer",
                                                     "visible",
                                                     toolTip=toolTip,
                                                     style=uic.BTN_LABEL_SML)
        # Toggle Layer Ref Button ---------------------------------------
        toolTip = "Toggles the selectability (reference) of the `imagePlanes_lyr` if it exists."
        self.toggleLyrSelBtn = elements.styledButton("",
                                                     "reference",
                                                     toolTip=toolTip,
                                                     style=uic.BTN_LABEL_SML)


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
        # Slider Layout
        sliderLayout = elements.vBoxLayout(margins=(0, uic.SMLPAD, 0, uic.REGPAD), spacing=uic.SREG)
        sliderLayout.addWidget(self.offsetLeftRightFloatSldr)
        sliderLayout.addWidget(self.offsetUpDownFloatSldr)
        sliderLayout.addWidget(self.scaleFloatSldr)
        sliderLayout.addWidget(self.rotateFloatSldr)
        sliderLayout.addWidget(self.opacityFloatSldr)
        # Place Front Back Btns
        placeCamPlanesLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SMLPAD)
        placeCamPlanesLayout.addWidget(self.placeFrontBtn, 5)
        placeCamPlanesLayout.addWidget(self.placeBehindBtn, 1)
        # Layer Toggle Btns
        layerBtnsLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SMLPAD)
        layerBtnsLayout.addWidget(self.toggleLyrVisBtn, 5)
        layerBtnsLayout.addWidget(self.toggleLyrSelBtn, 1)
        # layer and front/back Btns
        layerPlaceBtnLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SLRG)
        layerPlaceBtnLayout.addLayout(layerBtnsLayout, 1)
        layerPlaceBtnLayout.addLayout(placeCamPlanesLayout, 1)
        # top buttons
        pesetsLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SREG)
        pesetsLayout.addWidget(self.placeTopLeftBtn, 1)
        pesetsLayout.addWidget(self.placeTopRightBtn, 1)
        pesetsLayout.addWidget(self.placeBotLeftBtn, 1)
        pesetsLayout.addWidget(self.placeBotRightBtn, 1)
        pesetsLayout.addWidget(self.placeCenterBtn, 1)
        topBtnLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SREG)
        topBtnLayout.addWidget(self.createNewBtn, 1)
        topBtnLayout.addLayout(pesetsLayout, 1)
        # Add to main layout
        mainLayout.addWidget(self.miniBrowser)
        mainLayout.addWidget(self.resizerWidget)
        mainLayout.addLayout(topBtnLayout)
        mainLayout.addLayout(sliderLayout)
        mainLayout.addLayout(placeCamPlanesLayout)
        mainLayout.addLayout(layerPlaceBtnLayout)

        mainLayout.addStretch(1)


class GuiAdvanced(AllWidgets):
    def __init__(self, parent=None, properties=None, uiMode=UI_MODE_ADVANCED, toolsetWidget=None):
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
                                          uiMode=uiMode, toolsetWidget=toolsetWidget)
        # Main Layout
        mainLayout = elements.vBoxLayout(self, margins=(uic.WINSIDEPAD, uic.WINTOPPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=0)
        # Slider Layout
        sliderLayout = elements.vBoxLayout(margins=(0, uic.SMLPAD, 0, uic.REGPAD), spacing=uic.SREG)
        sliderLayout.addWidget(self.offsetLeftRightFloatSldr)
        sliderLayout.addWidget(self.offsetUpDownFloatSldr)
        sliderLayout.addWidget(self.scaleFloatSldr)
        sliderLayout.addWidget(self.rotateFloatSldr)
        sliderLayout.addWidget(self.opacityFloatSldr)
        # Place Front Back Btns
        placeCamPlanesLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SMLPAD)
        placeCamPlanesLayout.addWidget(self.placeFrontBtn, 5)
        placeCamPlanesLayout.addWidget(self.placeBehindBtn, 1)
        # Layer Toggle Btns
        layerBtnsLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SMLPAD)
        layerBtnsLayout.addWidget(self.toggleLyrVisBtn, 5)
        layerBtnsLayout.addWidget(self.toggleLyrSelBtn, 1)
        # layer and front/back Btns
        layerPlaceBtnLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SLRG)
        layerPlaceBtnLayout.addLayout(layerBtnsLayout, 1)
        layerPlaceBtnLayout.addLayout(placeCamPlanesLayout, 1)
        # top buttons
        pesetsLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SREG)
        pesetsLayout.addWidget(self.placeTopLeftBtn, 1)
        pesetsLayout.addWidget(self.placeTopRightBtn, 1)
        pesetsLayout.addWidget(self.placeBotLeftBtn, 1)
        pesetsLayout.addWidget(self.placeBotRightBtn, 1)
        pesetsLayout.addWidget(self.placeCenterBtn, 1)
        topBtnLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SREG)
        topBtnLayout.addLayout(pesetsLayout, 1)
        topBtnLayout.addWidget(self.createNewBtn, 1)
        # Add to main layout
        mainLayout.addWidget(self.miniBrowser)
        mainLayout.addWidget(self.resizerWidget)
        mainLayout.addLayout(topBtnLayout)
        mainLayout.addLayout(sliderLayout)
        mainLayout.addLayout(placeCamPlanesLayout)
        mainLayout.addLayout(layerPlaceBtnLayout)

        mainLayout.addStretch(1)
