import functools
import locale
import os
from functools import partial, wraps


from zoovendor.Qt import QtCore, QtWidgets

from zoo.apps.light_suite import lightconstants as lc
from zoo.apps.light_suite import modelhdrskydome

from maya import cmds
from zoo.libs.maya.cmds.lighting import renderertransferlights
from zoo.libs.maya.cmds.objutils import namehandling
from zoo.libs.maya.cmds.renderer import rendererload
from zoo.libs.maya.cmds.workspace import mayaworkspace
from zoo.libs.maya.cmds.lighting.renderertransferlights import INTENSITY, LIGHTVISIBILITY, SCALE, IBLTEXTURE, \
    ROTATE, \
    IBLSKYDOMES
import zoo.libs.maya.cmds.hotkeys.definedhotkeys as hk

from zoo.preferences.interfaces import lightsuiteinterfaces
from zoo.libs.zooscene import zooscenefiles
from zoo.apps.toolsetsui.widgets.toolsetresizer import ToolsetResizer
from zoo.apps.toolsetsui import toolsetcallbacks
from zoo.apps.toolsetsui.widgets import toolsetwidget

from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt import utils
from zoo.libs.pyqt.widgets import elements

from zoo.libs.utils import output
from zoo.core.util import zlogging

logger = zlogging.getLogger(__name__)

DFLT_RNDR_MODES = [("arnold", "Arnold"), ("redshift", "Redshift"), ("renderman", "Renderman")]
UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1


def ignoreInstantApplyDecorator(method):
    """ Decorator to temporarily ignore instant apply in a GUI.

    @undoDecorator
    def lightUIMethod():
        pass
    """

    @wraps(method)
    def _disableMethod(self, *args, **kwargs):
        try:
            rememberInstantApply = self.ignoreInstantApply
            self.ignoreInstantApply = True  # bool that tells other stuff to activate
            return method(self, *args, **kwargs)  # run the method
        finally:
            self.ignoreInstantApply = rememberInstantApply

    return _disableMethod


class HdriSkydomeLights(object): # toolsetwidget.ToolsetWidget, RendererMixin, MiniBrowserMixin
    ignoreInstantApply = None  # type: object
    id = "hdriSkydomeLights_old"
    uiData = {"label": "HDRI Skydomes",
              "icon": "sun",
              "tooltip": "Create and manage HDRI Skydome IBL attributes with this tool",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-create-hdr-skydomes/"
              }

    # ------------------------------------
    # START UP
    # ------------------------------------

    def preContentSetup(self):
        """First code to run"""
        self.toolsetWidget = self  # needed for callback decorators
        self.lightSuitePrefInterface = lightsuiteinterfaces.lightSuiteInterface()
        self.setAssetPreferences(self.lightSuitePrefInterface.skydomesPreference)
        self.initRendererMixin(disableVray=True, disableMaya=True)

    def contents(self):
        """The UI Modes to build, compact, medium and or advanced """
        return [self.initCompactWidget(), self.initAdvancedWidget()]

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
        self.ignoreInstantApply = False  # for instant apply directional lights and switching ui modes
        self.setMiniBrowsers([w.miniBrowser for w in self.widgets()])
        self.uiconnections()
        self.listeningForRenderer = True  # if True the renderer can be set from other windows or toolsets
        self.refreshUpdateUIFromSelection(update=True)  # update GUI from current in scene selection
        self.startSelectionCallback()  # start selection callback

    def currentWidget(self):
        """ Current active widget

        :return:
        :rtype:  AllWidgets
        """
        return super(HdriSkydomeLights, self).currentWidget()

    def widgets(self):
        """ List of widgets

        :return:
        :rtype: list[AllWidgets]
        """
        return super(HdriSkydomeLights, self).widgets()

    # ------------------------------------
    # PROPERTIES
    # ------------------------------------

    def initializeProperties(self):
        # TODO should be automated
        return [{"name": "name", "label": "Name", "value": "skyDomeLight",
                 "longName": "|ArnoldLights_grp|skyDomeLight_ARN"},
                {"name": "suffix", "label": "Suffix", "value": True},
                {"name": "intensity", "label": "Intensity", "value": 1.0},
                {"name": "rotate", "label": "Rotate", "value": [0.0, 0.0, 0.0]},
                {"name": "scale", "label": "Scale", "value": [1.0, 1.0, 1.0]},
                {"name": "scaleInvert", "label": "Invert", "value": False},
                {"name": "imagePath", "label": "HDRI Image", "value": ""},
                {"name": "bgVisCheckBx", "label": "Background Vis", "value": True},
                {"name": "instantApply", "label": "Instant Apply", "value": True},
                {"name": "rendererIconMenu", "label": "", "value": "Arnold"}]

    # ------------------
    # MOUSE OVER UI
    # ------------------

    def enterEvent(self, event):
        """Update selection on enter event
        """
        self.refreshUpdateUIFromSelection(update=True)  # update GUI from current in scene selection

    # ------------------------------------
    # POPUP WINDOWS
    # ------------------------------------

    def ui_loadRenderer(self):
        message = "The {} renderer isn't loaded. Load now?".format(self.properties.rendererIconMenu.value)
        # parent is None to parent to Maya to fix stylesheet issues
        okPressed = elements.MessageBox.showOK(title="Load Renderer", parent=None, message=message)
        return okPressed

    # ------------------------------------
    # CALLBACKS
    # ------------------------------------

    def selectionChanged(self, selection):
        """Run when the callback selection changes, updates the GUI if an object is selected

        Callbacks are handled automatically by toolsetcallbacks.py which this class inherits"""
        if not selection:  # then don't update
            return
        logger.debug(">>>>>>>>>>>>>>> SELECTION CHANGED UPDATING 'CREATE IBL GUI'  <<<<<<<<<<<<<<<<<<<<")
        self.refreshUpdateUIFromSelection()  # will update the GUI

    # ------------------------------------
    # RECEIVE RENDERER FROM OTHER UIS
    # ------------------------------------

    def global_receiveRendererChange(self, renderer):
        """Receives from other GUIs, changes the renderer when it is changed Overridden"""
        if renderer == "VRay" or renderer == "Maya":
            return  # Ignore as this UI doesn't support VRay or Maya yet.
        super(HdriSkydomeLights, self).global_receiveRendererChange(renderer)

    # ------------------------------------
    # UTILS
    # ------------------------------------

    def loadHDRSkydomeImage(self):
        if not self.checkRenderLoaded(self.properties.rendererIconMenu.value):
            return
        # should filter by file extensions
        projectDirectory = mayaworkspace.getCurrentMayaWorkspace()
        projectDirectory = os.path.join(projectDirectory, "sourceImages/")
        # should check if this directory exists
        fullFilePath, filter = QtWidgets.QFileDialog.getOpenFileName(self, "Open File", projectDirectory)
        if not str(fullFilePath):
            return
        # should check file extensions here
        self.properties.imagePath.value = str(fullFilePath)
        self.toolsetWidget.updateFromProperties()
        self.instantSetIBL()  # if instant apply is on then apply

    @ignoreInstantApplyDecorator
    def applyImageUI(self):
        """When the image is selected by the combo drop down menu apply it into the HDRI image UI full path

        :return imageApplied: Was the image index set correctly?  False if failed
        :rtype imageApplied: bool
        """
        logger.debug("applyImageUI()")
        imageIndex = self.properties.imageList.value  # get current image as an index
        if imageIndex > len(self.iblQuickDirImageList) - 1:
            imageIndex = 0
        self.properties.imageList.value = imageIndex
        if imageIndex == 0:  # is "select..." and not an image
            self.updateFromProperties()
            output.displayInfo("No image:  'select...'")
            return False
        fileName = self.iblQuickDirImageList[imageIndex]  # find the extension version
        hdrImagePath = os.path.join(
            os.path.join(self.lightSuitePrefsData["settings"][lc.PREFS_KEY_IBL], fileName))  # add directory
        # apply the image to the UI
        self.properties.imagePath.value = hdrImagePath
        self.updateFromProperties()
        return True

    def renameSkydome(self):
        """Renames the asset on disk"""
        currentFileNoExt = self.currentWidget().browserModel.currentImage
        skydomeFullPath = self.currentWidget().miniBrowser.selectedMetadata()['zooFilePath']
        if not currentFileNoExt:  # no image has been selected
            output.displayWarning("Please select an thumbnail image to rename.")
            return
        # Get the current directory
        message = "Rename Related `{}` Files As:".format(currentFileNoExt)
        renameText = elements.MessageBox.inputDialog(title="Rename Shader Preset", text=currentFileNoExt,
                                                     parent=None,
                                                     message=message)
        if not renameText:
            return
        # Do the rename
        fileRenameList = zooscenefiles.renameZooSceneOnDisk(renameText, skydomeFullPath)
        if not fileRenameList:  # shouldn't happen for Skydomes?
            output.displayWarning("Files could not be renamed, they are probably in use by the current scene. "
                                  "Do not have the renamed assets loaded in the scene, "
                                  "or check your file permissions.")
            return
        output.displayInfo("Success: Files `{}*` Have Been Renamed To `{}*`".format(currentFileNoExt, renameText))
        self.currentWidget().miniBrowser.refreshThumbs()

    def deleteSkydomePopup(self):
        """Popup window that asks the user if they want to delete the currently selected asset from disk?"""
        filenameNoExt = self.currentWidget().browserModel.currentImage
        if not filenameNoExt:
            output.displayWarning("Nothing selected. Please select an image to delete.")
        fullImagePath = self.currentWidget().miniBrowser.selectedMetadata()['zooFilePath']
        filenameWithExt = os.path.basename(fullImagePath)
        # Build popup window
        message = "Warning: Delete the preset `{}` and it's dependencies?  " \
                  "This will permanently delete these file/s from disk?".format(filenameWithExt)
        result = elements.MessageBox.showOK(title="Delete Image From Disk?",
                                            message=message)  # None will parent to Maya
        # After answering Ok or cancel
        if result:  # Ok was pressed
            filesFullPathDeleted = zooscenefiles.deleteZooSceneFiles(fullImagePath, message=True)
            output.displayInfo("Success, File/s Deleted: {}".format(filesFullPathDeleted))
            self.refreshThumbs()

    # ------------------------------------
    # MENUS - RIGHT CLICK
    # ------------------------------------

    @toolsetcallbacks.ignoreCallbackDecorator
    def setLightNameMenuModes(self):
        """Retrieves all ibl lights in the scene and creates the self.lightNameMenu menu so the user can switch

        Does a bunch of name handling to account for the UI LongName (self.properties.name.longName)
        Auto compares the long name to see if it is the first obj selected

        The current light in the ui is removed from the menu list if selected
        """
        logger.debug("setLightNameMenuModes()")
        modeList = list()
        currentNameUnique = None
        # area light list will be long names
        lightListLong = renderertransferlights.getAllIblSkydomeLightsInScene(self.properties.rendererIconMenu.value)[0]
        currentUiNameLong = self.properties.name.longName  # already has suffix
        currentNameExits = cmds.objExists(currentUiNameLong)
        if currentNameExits:  # then get the display name
            currentNameUnique = namehandling.getUniqueShortName(currentUiNameLong)
        if lightListLong:  # There are other ibl lights in the scene
            for i, obj in enumerate(lightListLong):
                if currentUiNameLong == obj:
                    lightListLong.pop(i)  # is the UI name so remove
                    break
        selObjs = cmds.ls(selection=True, long=True)
        if not selObjs and currentNameExits:
            modeList.append(("cursorSelect", "Select {}".format(currentNameUnique)))  # user can select the light
            modeList.append((None, "separator"))
        elif selObjs and currentNameExits:
            objLongName = selObjs[0]
            if currentUiNameLong != objLongName:  # current light is not selected
                modeList.append(("cursorSelect", "Select {}".format(currentNameUnique)))  # user can select the light
        if lightListLong:
            locale.setlocale(locale.LC_ALL, '')  # needed for sorting unicode
            sorted(lightListLong, key=functools.cmp_to_key(locale.strcoll))  # alphabetalize
            for light in lightListLong:
                modeList.append(("sky", namehandling.getUniqueShortName(light)))
        else:
            modeList.append(("", "No Other Skydome Lights"))
        modeList.append((None, "separator"))
        modeList.append(("windowBrowser", "Open Light Editor"))
        self.currentWidget().lightNameMenu.actionConnectList(modeList)

    def selectCurrentLight(self):
        """Selects the current light from the UI Light Name text box as called by a right click menu
        """
        logger.debug("selectCurrentLight()")
        lightNameLong = self.properties.name.longName
        if not cmds.objExists(lightNameLong):
            currentUIName = self.returnLightNameSuffixed(self.properties.name.value)
            if not cmds.objExists(currentUIName):
                output.displayWarning("Area Light `{}` or `{}` does not exist in the scene".format(lightNameLong,
                                                                                                   currentUIName))
                return
        cmds.select(lightNameLong, replace=True)

    @toolsetcallbacks.ignoreCallbackDecorator
    def menuSwitchToAreaLight(self):
        """Runs the light logic called from the drop-down right-click menu on the Light Name lineEdit (name text):

            - Select Current Light
            - Select Other Lights from scene
            - Open the Mayas Light Editor

        """
        logger.debug("menuSwitchToAreaLight()")
        lightTransformName = self.currentWidget().lightNameMenu.currentMenuItem()
        if lightTransformName == "No Other Area Lights":
            return
        elif "Select " in lightTransformName:  # then is the select object
            self.selectCurrentLight()
            return
        elif lightTransformName == "Open Light Editor":
            hk.open_mayLightEditor() # opens Maya's Light Editor
            return
        cmds.select(lightTransformName, replace=True)
        self.refreshUpdateUIFromSelection()

    # ------------------------------------
    # CREATE LIGHTS
    # ------------------------------------

    @toolsetcallbacks.ignoreCallbackDecorator
    @toolsetwidget.ToolsetWidget.undoDecorator
    def createSkydomeLight(self):
        """Creates the skydome light
        """
        newName = str(self.properties.name.value)  # something weird is happening with object variables
        renderer = self.properties.rendererIconMenu.value
        if not self.checkRenderLoaded(renderer):
            return
        lightApplyAttrDict = renderertransferlights.getSkydomeLightDictAttributes()  # dict with keys but empty values
        lightApplyAttrDict[INTENSITY] = self.properties.intensity.value
        scale = self.properties.scale.value
        invertScale = self.properties.scaleInvert.value
        if invertScale:
            scaleX = scale[0] * -1
        else:
            scaleX = scale[0]
        lightApplyAttrDict[SCALE] = (scaleX, scale[1], scale[2])
        lightApplyAttrDict[IBLTEXTURE] = self.currentWidget().miniBrowser.itemFilePath()
        lightApplyAttrDict[LIGHTVISIBILITY] = self.properties.bgVisCheckBx.value
        # create
        lightTransform, lightShape, warning = renderertransferlights.createSkydomeLightRenderer("tempIblNameXyy",
                                                                                                renderer,
                                                                                                warningState=False,
                                                                                                cleanup=True)
        if warning:
            return
        # rename with suffix compatibility
        lightTransform, lightShape = renderertransferlights.renameLight(lightTransform,
                                                                        newName,
                                                                        addSuffix=self.properties.suffix.value,
                                                                        renderer=renderer)
        renderertransferlights.setIblAttr(lightShape, lightApplyAttrDict, invertScaleZ=invertScale)  # set attrs
        return lightTransform, lightShape

    # ------------------------------------
    # SET (APPLY) LIGHTS
    # ------------------------------------

    def findUILightSelection(self, prioritizeNameBool=True, findUnselected=True, returnFirstObj=False):
        """Finds all the ibl lights in the scene intelligently, also uses GUI name too

        See rendererTransferLights.getIblLightSelected() for full docs

        :param prioritizeNameBool: a name, usually from the GUI to affect even if it's not selected
        :type prioritizeNameBool: bool
        :return iblLightTransforms: a list of light transform names
        :rtype iblLightTransforms: list
        :return iblLightShapes: a list of light shape names
        :rtype iblLightShapes: list
        """
        logger.debug("findUILightSelection()")
        rendererNiceName = self.properties.rendererIconMenu.value
        if prioritizeNameBool:
            prioritizeName = self.properties.name.longName
        iblLightTransforms, iblLightShapes = \
            renderertransferlights.getIblLightSelected(rendererNiceName,
                                                       prioritizeName=prioritizeName,
                                                       findUnselected=findUnselected,
                                                       returnFirstObj=returnFirstObj)
        return iblLightTransforms, iblLightShapes

    def skydomeApplyThumbnail(self):
        """Applies the thumbnail view image
        """
        try:
            self.properties.imagePath.value = self.currentWidget().miniBrowser.itemFilePath()
            self.setSkydomeLight()
        except AttributeError:
            output.displayWarning("Please select an image")

    @toolsetcallbacks.ignoreCallbackDecorator
    @toolsetwidget.ToolsetWidget.undoDecorator
    def setSkydomeLight(self, message=True, createIfNoneFound=True):
        """Sets the skydome from the GUI settings, creates skydome light if none exists

        :param message: report the message to the user?
        :type message: bool
        :param createIfNoneFound: Creates a light instantly if no lights are in the scene
        :type createIfNoneFound: bool
        """
        rememberSelection = cmds.ls(selection=True)  # selection lost so remember, could check functions as shouldn't
        invert = self.properties.scaleInvert.value
        lightApplyAttrDict = renderertransferlights.getSkydomeLightDictAttributes()  # dict with keys but empty values
        lightApplyAttrDict[INTENSITY] = self.properties.intensity.value
        lightApplyAttrDict[SCALE] = self.properties.scale.value
        lightApplyAttrDict[ROTATE] = self.properties.rotate.value
        lightApplyAttrDict[IBLTEXTURE] = self.properties.imagePath.value
        lightApplyAttrDict[LIGHTVISIBILITY] = self.properties.bgVisCheckBx.value
        iblLightShapes = self.findUILightSelection()[1]

        os.environ[lc.ZOO_PREFS_IBLS_ENV] = os.pathsep.join(self.lightSuitePrefInterface.skydomeDirectories())
        if iblLightShapes:
            renderertransferlights.setIBLAttrList(lightApplyAttrDict,
                                                  iblLightShapes,
                                                  invertScaleZ=invert)
            shapeListUnique = namehandling.getUniqueShortNameList(iblLightShapes)
            if message:
                output.displayInfo("Success: IBL Updated: {}".format(shapeListUnique))
            self.updateFromProperties()
        elif createIfNoneFound:  # if no IBLs create one automatically
            allIblList = renderertransferlights.getAllIblSkydomeLightsInScene(self.properties.rendererIconMenu.value)
            if not allIblList[0]:  # no lights
                self.createSkydomeLight()
                self.refreshUpdateUIFromSelection()
        cmds.select(rememberSelection, replace=True)

    # ------------------------------------
    # INSTANT SET (APPLY) LIGHTS
    # ------------------------------------

    def instantApply(self):
        """when the image is selected in the quick dir area instant apply it when changed
        Note: This is not instant apply all attributes, only the image path
        """
        if not self.properties.instantApply.value:
            return
        if self.applyImageUI():
            self.setSkydomeLight()

    def instantIBLRename(self):
        """Renames the light when the GUI is changed"""
        self.instantSetIBLFunction(rename=True)

    def instantSetIBL(self):
        """Sets the IBLs settings, but not rename"""
        self.instantSetIBLFunction(rename=False)

    def instantSetIBLFunction(self, rename=False):
        """Instant apply for all IBL attributes in the UI

        :param rename: if True will only rename, won't set other attributes, if False will not rename but set all attr
        :type rename: bool
        """
        if not self.properties.instantApply:
            return
        if not rename:
            self.setSkydomeLight()
        else:  # rename
            self.renameLight()

    # ------------------------------------
    # GET (RETRIEVE) LIGHTS
    # ------------------------------------

    def refreshUpdateUIFromSelection(self, update=True):
        """Gets all the attributes (properties) from the first selected light and updates the GUI

        :param update: if False will skip updating the UI, not used
        :type update: bool
        """
        logger.debug("refreshUpdateUIFromSelection()")
        if not rendererload.getRendererIsLoaded(self.properties.rendererIconMenu.value):
            return  # the renderer is not loaded so don't update from scene
        rememberInstantApply = self.ignoreInstantApply
        self.ignoreInstantApply = True
        self.getSkydomeLight(message=False, update=False)  # get intensity/exposure as per the light
        self.getLightName(message=False, update=False)
        if update:
            self.updateFromProperties()
        self.ignoreInstantApply = rememberInstantApply

    @toolsetcallbacks.ignoreCallbackDecorator
    def getLightName(self, message=False, update=True):
        """Pulls the name of the selected directional light

        :param message: report the message to the user?
        :type message: bool
        :param update: if False will skip updating the UI, refreshUpdateUIFromSelection otherwise updates too much
        :type update: bool
        """
        logger.debug("getLightName()")
        rendererNiceName = self.properties.rendererIconMenu.value
        removeSuffix = self.properties.suffix.value
        newName, suffixRemoved = renderertransferlights.getLightNameSelected(removeSuffix=removeSuffix,
                                                                             lightFamily=IBLSKYDOMES,
                                                                             rendererNiceName=rendererNiceName,
                                                                             message=message)
        if not newName:
            return
        # incoming newName is long and has no suffix
        self.properties.suffix.value = suffixRemoved
        newLongWithSuffix = self.returnLightNameSuffixed(newName)  # must add potential suffix for long name
        newShortName = namehandling.getShortName(newName)  # is the short name for the GUI
        self.properties.name.value = newShortName
        self.properties.name.longName = newLongWithSuffix
        if update:
            self.updateFromProperties()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def getSkydomeLight(self, message=True, update=True):
        """Gets all attributes from the selected ibl light, with intelligent selection.

        :param message: Report the message to the user?
        :type message: bool
        :param update: if False will skip updating the UI, refreshUpdateUIFromSelection otherwise updates too much
        :type update: bool
        """
        rendererNiceName = self.properties.rendererIconMenu.value
        attrValDict = renderertransferlights.getIblAttrSelected(rendererNiceName, getIntensity=True, getExposure=False,
                                                                getColor=False, getLightVisible=True,
                                                                getIblTexture=True, getTranslation=False,
                                                                getRotation=True, getScale=True, message=message)
        if not attrValDict:  # update properties
            return
        self.properties.intensity.value = attrValDict[INTENSITY]
        scale = attrValDict[SCALE]
        inverted = False
        if scale[2] < 0:
            inverted = True
        self.properties.scale.value = scale
        self.properties.rotate.value = attrValDict[ROTATE]
        self.properties.imagePath.value = attrValDict[IBLTEXTURE]

        self.properties.bgVisCheckBx.value = bool(attrValDict[LIGHTVISIBILITY])
        self.properties.scaleInvert.value = inverted
        if update:
            self.updateFromProperties()

    # ------------------------------------
    # OFFSET ATTRIBUTES
    # ------------------------------------

    def offsetMultiplier(self):
        """For offset functions multiply shift and minimise if ctrl is held down
        If alt then call the reset option

        :return multiplier: multiply value, .2 if ctrl 5 if shift 1 if None
        :rtype multiplier: float
        :return reset: reset becomes true for resetting
        :rtype reset: bool
        """
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        if modifiers == QtCore.Qt.ShiftModifier:
            return 5.0, False
        elif modifiers == QtCore.Qt.ControlModifier:
            return 0.2, False
        elif modifiers == QtCore.Qt.AltModifier:
            return 1, True
        return 1.0, False

    @toolsetwidget.ToolsetWidget.undoDecorator
    def iblRotOffset(self, offset=15.0, neg=False, message=True):
        """Rotates the IBL on y axis by an offset amount

        :param offset: the offset of the y rotation
        :type offset: float
        """
        multiplier, reset = self.offsetMultiplier()
        rotate = self.properties.rotate.value
        rotX = rotate[0]
        rotY = rotate[1]
        rotZ = rotate[2]
        if neg:
            offset = -offset
        if reset:
            rotate = self.properties.rotate.default
            self.properties.rotate.value = rotate
        else:
            if multiplier > 1:
                multiplier = 2.0  # dim faster value as 5.0 is too fast
            offset = offset * multiplier
            rotate = (rotX, rotY + offset, rotZ)
            self.properties.rotate.value = rotate
        # set GUI and lights
        iblShapes = self.findUILightSelection(prioritizeNameBool=True)[1]
        if iblShapes:
            lightApplyAttrDict = renderertransferlights.getSkydomeLightDictAttributes()  # dict with keys but empty
            lightApplyAttrDict[ROTATE] = rotate
            renderertransferlights.setIBLAttrList(lightApplyAttrDict, iblShapes, invertScaleZ=False)
            shapeListUnique = namehandling.getUniqueShortNameList(iblShapes)
            if message:
                output.displayInfo("Success: IBL Updated: {}".format(shapeListUnique))
        self.updateFromProperties()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def iblIntensityOffset(self, percentage=10.0, neg=False, message=True):
        """adjusts the intensity of the IBL light by a given offset

        :param percentage: light intensity offset as a percentage
        :type percentage: float
        """
        multiplier, reset = self.offsetMultiplier()
        if reset:  # alt button pressed reset the attr
            intensity = self.properties.intensity.default
            self.properties.intensity.value = intensity
        else:
            if multiplier > 1:
                multiplier = 2.0  # dim faster value as 10.0 is too fast
            if neg:
                percentage = -percentage
            intensity = self.properties.intensity.value
            intensity += ((intensity * (percentage / 100)) * multiplier)  # 1 becomes 1.1 * the multiplier
            self.properties.intensity.value = intensity
        # set UI and lights
        iblShapes = self.findUILightSelection(prioritizeNameBool=True)[1]
        if iblShapes:
            lightApplyAttrDict = renderertransferlights.getSkydomeLightDictAttributes()  # dict with keys but empty
            lightApplyAttrDict[INTENSITY] = intensity
            renderertransferlights.setIBLAttrList(lightApplyAttrDict, iblShapes, invertScaleZ=False)
            shapeListUnique = namehandling.getUniqueShortNameList(iblShapes)
            if message:
                output.displayInfo("Success: IBL Updated: {}".format(shapeListUnique))
        self.updateFromProperties()

    # ------------------------------------
    # LIGHT NAME/RENAME
    # ------------------------------------

    def returnLightNameNoSuffix(self, lightName):
        """Returns the light name now without it's suffix matching any renderer eg "lightName_ARN" > "lightName"

        :param lightName: the string name of the light potentially with the suffix
        :type lightName: str
        :return lightName: the light renamed now without it's suffix
        :rtype lightName: str
        """
        if self.properties.suffix.value:
            return renderertransferlights.removeRendererSuffix(lightName)[0]
        return lightName

    def returnLightNameSuffixed(self, lightName):
        """Returns the light name now with a suffix matching the renderer eg "lightName" > "lightName_ARN" (Arnold)

        :param lightName: the string name of the light before the suffix
        :type lightName: str
        :return lightName: the light renamed now with a suffix
        :rtype lightName: str
        """
        if not self.properties.suffix.value:
            return lightName
        suffix = renderertransferlights.RENDERER_SUFFIX[self.properties.rendererIconMenu.value]
        return "_".join([lightName, suffix])

    @toolsetcallbacks.ignoreCallbackDecorator
    @ignoreInstantApplyDecorator
    @toolsetwidget.ToolsetWidget.undoDecorator
    def renameLight(self):
        """rename the ibl light
        """
        logger.debug("renameLight()")
        newName = self.properties.name.value
        renameLight = self.properties.name.longName
        if not cmds.objExists(renameLight):
            output.displayWarning("Skydome light does not exist: {}".format(renameLight))
            return
        lightTransform, lightShape = renderertransferlights.renameLight(renameLight,
                                                                        newName,
                                                                        addSuffix=self.properties.suffix.value,
                                                                        lightFamily=renderertransferlights.IBLSKYDOMES)
        # lightTransform is always unique so can longname it
        self.properties.name.longName = namehandling.getLongNameFromShort(lightTransform)
        # see whether to update the ui name
        lightTransformNoSuffix = self.returnLightNameNoSuffix(namehandling.getShortName(lightTransform))
        if lightTransformNoSuffix != newName:  # then the UI needs to update
            self.properties.name.value = lightTransformNoSuffix
            self.updateFromProperties()

    def sliderPressed(self):
        """ Get the skydome information and open the undo chunk if found
        """
        self.refreshUpdateUIFromSelection(update=False)
        transforms, shapes = self.findUILightSelection(prioritizeNameBool=True)
        if transforms:
            self._skydomeTransform = transforms[0]
            self._skydomeShape = shapes[0]
        else:
            self._skydomeTransform = None
            self._skydomeShape = None
            output.displayWarning("No HDRI Skydomes found, please build or select a skydome.")
            return

        self._skydomeRot = renderertransferlights.iblRotate(self._skydomeTransform,
                                                            renderer=self.properties.rendererIconMenu.value)
        self.openUndoChunk()

    def sliderScrolled(self, event):
        """ Slider scrolled

        :param event: A tuple x and y offset of the virtual slider (21.0, 1.0021)
        :type event: :class:`zoo.libs.pyqt.extended.imageview.thumbnail.virtualslider.MouseSlideEvent`
        """
        if not self._skydomeShape:
            return
        x, y = event.value
        rotY = self._skydomeRot[1] + x
        renderertransferlights.setIblRotate(self._skydomeTransform,
                                            [self._skydomeRot[0], rotY, self._skydomeRot[2]],
                                            renderer=self.properties.rendererIconMenu.value)
        # TODO: Add intensity on up down slider

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
        super(HdriSkydomeLights, self).uiconnections()
        for uiInstance in self.widgets():
            # dots menu viewer
            uiInstance.miniBrowser.dotsMenu.applyAction.connect(self.skydomeApplyThumbnail)
            uiInstance.miniBrowser.dotsMenu.renameAction.connect(self.renameSkydome)
            uiInstance.miniBrowser.dotsMenu.deleteAction.connect(self.deleteSkydomePopup)
            # thumbnail viewer
            uiInstance.browserModel.doubleClicked.connect(self.skydomeApplyThumbnail)
            # offsets
            uiInstance.rotNegBtn.clicked.connect(partial(self.iblRotOffset, neg=True))
            uiInstance.rotPosBtn.clicked.connect(partial(self.iblRotOffset, neg=False))
            uiInstance.darkenBtn.clicked.connect(partial(self.iblIntensityOffset, neg=True))
            uiInstance.brightenBtn.clicked.connect(partial(self.iblIntensityOffset, neg=False))
            # Instant Apply IBL Lights
            uiInstance.intensityTxt.edit.textModified.connect(self.instantSetIBL)
            uiInstance.rotVEdit.textModified.connect(self.instantSetIBL)
            uiInstance.bgVisCheckBx.stateChanged.connect(self.instantSetIBL)
            # change renderer
            uiInstance.rendererLoaded.actionTriggered.connect(self.global_changeRenderer)
            # Virtual Sliders
            uiInstance.miniBrowser.sliderChanged.connect(self.sliderScrolled)
            uiInstance.miniBrowser.sliderPressed.connect(self.sliderPressed)
            uiInstance.miniBrowser.sliderReleased.connect(self.sliderReleased)
        # menu
        self.advancedWidget.lightNameMenu.aboutToShow.connect(self.setLightNameMenuModes)
        self.advancedWidget.lightNameMenu.menuChanged.connect(self.menuSwitchToAreaLight)
        # instant apply
        self.advancedWidget.suffixChkBx.stateChanged.connect(self.instantIBLRename)
        self.advancedWidget.nameTxt.edit.textModified.connect(self.instantIBLRename)
        self.advancedWidget.imagePathTxt.edit.textModified.connect(self.instantSetIBL)
        self.advancedWidget.browseBtn.clicked.connect(self.loadHDRSkydomeImage)
        self.advancedWidget.scaleInvertChkBx.stateChanged.connect(self.instantSetIBL)
        self.advancedWidget.scaleVEdit.textModified.connect(self.instantSetIBL)
        # callback connections
        self.selectionCallbacks.callback.connect(self.selectionChanged)  # monitor selection
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

        self.toolsetWidget = toolsetWidget
        self.properties = properties
        self.uiMode = uiMode
        # Rename Delete Dots Menu  ------------------------------------

        # Thumbnail Viewer ---------------------------------------
        lightSuitePref = self.toolsetWidget.lightSuitePrefInterface.skydomesPreference
        uniformIcons = lightSuitePref.browserUniformIcons()
        # viewer widget and model
        self.miniBrowser = elements.MiniBrowser(toolsetWidget=toolsetWidget, columns=3,
                                                fixedHeight=382,
                                                uniformIcons=uniformIcons,
                                                itemName="IBL",
                                                applyIcon="sun", parent=self,
                                                selectDirectoriesActive=True,
                                                virtualSlider=True)
        self.miniBrowser.setSliderSettings(slowSpeedXY=(.2, 0.01), speedXY=(2, 0.02), fastSpeedXY=(20, 0.05))
        self.miniBrowser.dotsMenu.setSnapshotActive(True)
        self.miniBrowser.dotsMenu.setCreateActive(False)
        self.miniBrowser.dotsMenu.setDirectoryActive(False)

        self.browserModel = modelhdrskydome.HdrSkydomeViewerModel(self.miniBrowser,
                                                                  directories=lightSuitePref.browserFolderPaths(),
                                                                  uniformIcons=uniformIcons,
                                                                  assetPreference=lightSuitePref)
        self.miniBrowser.setModel(self.browserModel)
        self.resizerWidget = ToolsetResizer(toolsetWidget=self.toolsetWidget, target=self.miniBrowser)
        # Intensity --------------------------------------
        toolTip = "The skydome's intensity"
        if self.uiMode == UI_MODE_COMPACT:  # adjust ratio
            editRatio = 3
        elif self.uiMode == UI_MODE_ADVANCED:  # adjust ratio
            editRatio = 5

        self.intensityTxt = elements.FloatEdit(self.properties.intensity.label,
                                               self.properties.intensity.default,
                                               parent=self,
                                               editWidth=None,
                                               labelRatio=2,
                                               rounding=3,
                                               editRatio=editRatio,
                                               toolTip=toolTip)

        self.toolsetWidget.linkProperty(self.intensityTxt, "intensity")
        toolTip = "Darken the selected, or the only skydome in the scene\n(Shift faster, ctrl slower, alt reset)"
        self.darkenBtn = elements.styledButton("", "darkenBulb",
                                               self,
                                               toolTip=toolTip,
                                               style=uic.BTN_TRANSPARENT_BG,
                                               minWidth=uic.BTN_W_ICN_LRG)
        toolTip = "Brighten the selected, or the only skydome in the scene\n(Shift faster, ctrl slower, alt reset)"
        self.brightenBtn = elements.styledButton("",
                                                 "brightenBulb",
                                                 self,
                                                 toolTip=toolTip,
                                                 style=uic.BTN_TRANSPARENT_BG,
                                                 minWidth=uic.BTN_W_ICN_LRG)
        if self.uiMode == UI_MODE_COMPACT:  # make the button width smaller
            self.darkenBtn.setMinimumWidth(utils.dpiScale(30))
            self.brightenBtn.setMinimumWidth(utils.dpiScale(30))

        # Rotation --------------------------------------
        toolTip = "The rotation of the skydome light\nMay differ from the actual settings depending on the renderer"
        if self.uiMode == UI_MODE_COMPACT:  # adjust ratio
            editRatio = 3
        elif self.uiMode == UI_MODE_ADVANCED:  # adjust ratio
            editRatio = 5
        self.rotVEdit = elements.VectorLineEdit(self.properties.rotate.label,
                                                self.properties.rotate.default,
                                                axis=("x", "y", "z"),
                                                parent=self,
                                                toolTip=toolTip,
                                                labelRatio=2,
                                                rounding=2,
                                                editRatio=editRatio,
                                                spacing=uic.SREG,
                                                updateOnSlideTick=True)
        self.toolsetWidget.linkProperty(self.rotVEdit, "rotate")
        if self.uiMode == UI_MODE_COMPACT:  # hide the x and the z rot lineEdits
            self.rotVEdit.hideLineEdit(0)
            self.rotVEdit.hideLineEdit(2)
        toolTip = "Rotate the selected, or the only skydome in the scene\n(Shift faster, ctrl slower, alt reset)"
        self.rotPosBtn = elements.styledButton("",
                                               "arrowRotLeft",
                                               self,
                                               toolTip=toolTip,
                                               style=uic.BTN_TRANSPARENT_BG,
                                               minWidth=uic.BTN_W_ICN_LRG)
        self.rotNegBtn = elements.styledButton("", "arrowRotRight",
                                               self,
                                               toolTip=toolTip,
                                               style=uic.BTN_TRANSPARENT_BG,
                                               minWidth=uic.BTN_W_ICN_LRG)
        if self.uiMode == UI_MODE_COMPACT:  # make the button width smaller
            self.rotNegBtn.setMinimumWidth(30)
            self.rotPosBtn.setMinimumWidth(30)
        # Bottom Checkbox Section --------------------------------------
        toolTip = "Render the skydome background visibility on/off\n" \
                  "When checked off, the skydome lights the scene as usual, but it's image is not seen by the camera."
        self.bgVisCheckBx = elements.CheckBox(self.properties.bgVisCheckBx.label,
                                              self.properties.bgVisCheckBx.value,
                                              self,
                                              toolTip=toolTip)
        # Renderer Button --------------------------------------
        toolTip = "Set the default renderer"
        self.rendererLoaded = elements.iconMenuButtonCombo(DFLT_RNDR_MODES,
                                                           self.properties.rendererIconMenu.value,
                                                           toolTip=toolTip)
        self.toolsetWidget.linkProperty(self.rendererLoaded, "rendererIconMenu")
        self.rendererLabel = elements.Label("Renderer", self, toolTip=toolTip)
        if self.uiMode != UI_MODE_ADVANCED:  # widgets that only exist in the advanced mode
            return
        # Name --------------------------------------
        toolTip = "The name of the skydome light"
        self.nameTxt = elements.StringEdit(self.properties.name.label,
                                           self.properties.name.default,
                                           parent=self,
                                           editWidth=None,
                                           labelRatio=2,
                                           editRatio=5,
                                           toolTip=toolTip)
        self.toolsetWidget.linkProperty(self.nameTxt, "name")

        self.lightNameMenu = elements.ExtendedMenu(searchVisible=True)
        self.nameTxt.setMenu(self.lightNameMenu)  # right click. Menu items are dynamic self.setLightNameMenuModes()
        self.nameTxt.setMenu(self.lightNameMenu, mouseButton=QtCore.Qt.LeftButton)  # left click
        toolTip = "Automatically add a suffix to the light name Eg. skydome_ARN\n" \
                  "Arnold: _ARN\nRedshift: _RS\nRenderman: _PXR"
        self.suffixChkBx = elements.CheckBox(self.properties.suffix.label,
                                             self.properties.suffix.default,
                                             self,
                                             toolTip=toolTip)
        self.toolsetWidget.linkProperty(self.suffixChkBx, "suffix")
        # HDRI Image Location --------------------------------------
        toolTip = "The path of the skydome image"
        self.imagePathTxt = elements.StringEdit(self.properties.imagePath.label,
                                                self.properties.imagePath.default,
                                                parent=self,
                                                editWidth=None,
                                                labelRatio=115,
                                                editRatio=400,
                                                toolTip=toolTip)
        self.toolsetWidget.linkProperty(self.imagePathTxt, "imagePath")
        toolTip = "Browse to load a skydome image"
        self.browseBtn = elements.styledButton("...",
                                               None,
                                               self,
                                               toolTip=toolTip,
                                               style=uic.BTN_DEFAULT,
                                               minWidth=uic.BTN_W_ICN_REG)
        # Scale --------------------------------------
        toolTip = "The size/scale of the skydome light\nDoes not affect the render unless inverted"
        self.scaleVEdit = elements.VectorLineEdit(self.properties.scale.label,
                                                  self.properties.scale.default,
                                                  axis=("x", "y", "z"),
                                                  parent=self,
                                                  toolTip=toolTip,
                                                  labelRatio=2,
                                                  editRatio=5,
                                                  rounding=2,
                                                  spacing=uic.SREG)
        self.toolsetWidget.linkProperty(self.scaleVEdit, "scale")
        # invert
        toolTip = "Inverts the size/scale of the skydome light\nReverses the image direction"
        self.scaleInvertChkBx = elements.CheckBox(self.properties.scaleInvert.label,
                                                  self.properties.scaleInvert.default,
                                                  self,
                                                  toolTip=toolTip)
        self.toolsetWidget.linkProperty(self.scaleInvertChkBx, "scaleInvert")


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
        mainLayout = elements.vBoxLayout(self,
                                         margins=(uic.WINSIDEPAD, uic.WINTOPPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=0)
        # Renderer layout
        rendererLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SREG)
        rendererLayout.addWidget(self.rendererLoaded)
        rendererLayout.addWidget(self.rendererLabel)
        # IBL Intensity/Rotation section
        gridLayout = elements.GridLayout(margins=(0, 0, 0, 0), spacing=uic.SREG)
        gridLayout.addWidget(self.rotVEdit, 0, 0)
        gridLayout.addWidget(self.rotPosBtn, 0, 1)
        gridLayout.addWidget(self.rotNegBtn, 0, 2)
        gridLayout.addWidget(self.bgVisCheckBx, 0, 3)
        gridLayout.addWidget(self.intensityTxt, 1, 0)
        gridLayout.addWidget(self.darkenBtn, 1, 1)
        gridLayout.addWidget(self.brightenBtn, 1, 2)
        gridLayout.addLayout(rendererLayout, 1, 3)

        gridLayout.setColumnStretch(1, 5)
        gridLayout.setColumnStretch(2, 1)
        gridLayout.setColumnStretch(3, 1)
        gridLayout.setColumnStretch(4, 8)

        # Add to main layout
        mainLayout.addWidget(self.miniBrowser)
        mainLayout.addWidget(self.resizerWidget)
        mainLayout.addLayout(gridLayout)
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
        mainLayout = elements.vBoxLayout(self,
                                         margins=(uic.WINSIDEPAD, uic.WINTOPPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=0)
        # Suffix Layout ---------------------------
        suffixLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=0)
        suffixLayout.addItem(elements.Spacer(13, 0))
        suffixLayout.addWidget(self.suffixChkBx)
        # Invert Layout ---------------------------
        invertLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=0)
        invertLayout.addItem(elements.Spacer(13, 0))
        invertLayout.addWidget(self.scaleInvertChkBx)
        # Intensity buttons Layout ---------------------------
        intensityBtnLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SSML)
        intensityBtnLayout.addWidget(self.darkenBtn)
        intensityBtnLayout.addWidget(self.brightenBtn)
        # Rot buttons Layout ---------------------------
        rotBtnLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SSML)
        rotBtnLayout.addWidget(self.rotPosBtn)
        rotBtnLayout.addWidget(self.rotNegBtn)
        # Grid Layout ---------------------------
        gridLayout = elements.GridLayout(margins=(0, 0, 0, uic.REGPAD), spacing=uic.SREG)
        gridLayout.addWidget(self.nameTxt, 0, 0)
        gridLayout.addLayout(suffixLayout, 0, 1)
        gridLayout.addWidget(self.intensityTxt, 1, 0)
        gridLayout.addLayout(intensityBtnLayout, 1, 1)
        gridLayout.addWidget(self.rotVEdit, 2, 0)
        gridLayout.addLayout(rotBtnLayout, 2, 1)
        gridLayout.addWidget(self.scaleVEdit, 3, 0)
        gridLayout.addLayout(invertLayout, 3, 1)
        # HDRI Image location section -----------------------------
        hdriImageLayout = elements.hBoxLayout(margins=(0, 0, 0, uic.REGPAD), spacing=uic.SREG)
        hdriImageLayout.addWidget(self.imagePathTxt, 9)
        hdriImageLayout.addWidget(self.browseBtn, 1)
        # Bottom Checkbox Layout ---------------------------
        bottomCheckBoxLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=uic.SREG)
        bottomCheckBoxLayout.addWidget(self.bgVisCheckBx, 4)
        bottomCheckBoxLayout.addWidget(self.rendererLoaded, 1)
        bottomCheckBoxLayout.addWidget(self.rendererLabel, 1)
        # Main Layout -------------------------
        mainLayout.addWidget(self.resizerWidget)

        mainLayout.addWidget(self.miniBrowser)
        mainLayout.addWidget(self.resizerWidget)
        mainLayout.addLayout(gridLayout)
        mainLayout.addLayout(hdriImageLayout)
        mainLayout.addLayout(bottomCheckBoxLayout)
        mainLayout.addStretch(1)
