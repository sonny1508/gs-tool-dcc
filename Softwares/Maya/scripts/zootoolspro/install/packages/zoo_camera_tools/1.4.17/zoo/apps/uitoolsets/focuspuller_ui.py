""" ---------- Focus Puller -------------
Adds a Depth Of Field Control to the camera and settings in the UI.

Author: Mitchell Marks
"""
from zoovendor.Qt import QtWidgets

from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.apps.toolsetsui import toolsetui, toolsetcallbacks
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements
from zoo.libs.maya.cmds.meta import metafocuspuller, metafocuspuller_redshift, \
    metafocuspuller_renderman, metafocuspuller_arnold
from zoo.libs.maya.cmds.cameras import cameras, focuspuller
from zoo.libs.maya.cmds.renderer import rendererload
from zoo.apps.toolsetsui.ext.renderers import RendererMixin

from zoo.libs.utils import output
import maya.cmds as cmds

from zoo.libs.maya.qt.changerendererui import globalChangeRenderer
from zoo.libs.maya.cmds.renderer.rendererconstants import (MAYA, ARNOLD, REDSHIFT, RENDERMAN,
                                                           VRAY, RENDERER_ICONS_LIST, VIEWPORT2)

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1

# Remove VRay as not supported yet
RENDERER_ICONS_LIST = [value for value in RENDERER_ICONS_LIST if value != ("vray", VRAY)]


class FocusPuller(toolsetwidget.ToolsetWidget, RendererMixin):
    id = "focusPuller"
    info = "Easily manage camera Depth of Field."
    uiData = {"label": "Focus Puller",
              "icon": "focusAim",
              "tooltip": "Easily manage camera Depth of Field.",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-focus-puller/"
              }

    # ------------------
    # STARTUP
    # ------------------

    def preContentSetup(self):
        """First code to run, treat this as the __init__() method"""
        self.toolsetWidget = self  # needed for callback decorators
        self.initRendererMixin(disableVray=True)  # sets the renderer

    def contents(self):
        """The UI Modes to build, compact, medium and or advanced """
        return [self.initCompactWidget()]  # self.initAdvancedWidget()

    def initCompactWidget(self):
        """Builds the Compact GUI (self.compactWidget) """
        self.compactWidget = GuiCompact(parent=self, properties=self.properties, toolsetWidget=self)
        return self.compactWidget

    def postContentSetup(self):
        """Last of the initialize code"""
        self.metaNodes = list()
        self.cameraZapi = None
        self.updateSelection()
        self.uiConnections()
        self.startSelectionCallback()  # start selection callback
        self.compactWidget.selectedCameraTxt.setEnabled(False)

    def defaultAction(self):
        """Double Click
        Double clicking the tools toolset icon will run this method
        Be sure "defaultActionDoubleClick": True is set inside self.uiData (meta data of this class)"""
        pass

    def currentWidget(self):
        """ Currently active widget

        :return:
        :rtype: GuiCompact
        """
        return super(FocusPuller, self).currentWidget()

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiCompact]
        """
        return super(FocusPuller, self).widgets()

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
    # RENDERER - AND SEND/RECEIVE ALL TOOLSETS
    # ------------------------------------

    @toolsetcallbacks.ignoreCallbackDecorator
    def global_receiveRendererChange(self, renderer, ignoreVRay=True, ignoreMaya=False):
        """Receives from other GUIs, changes the renderer when it is changed
        Overridden method to disable VRay and Maya renderers as they are not supported"""
        super(FocusPuller, self).global_receiveRendererChange(renderer,
                                                              ignoreVRay=ignoreVRay,
                                                              ignoreMaya=ignoreMaya)
        if renderer == VRAY:
            return
        self.updateUI()
        self.updateTree(delayed=False)  # dodgy needs to refresh again

    # ------------------
    # UI Disable/Enable
    # ------------------

    def diableWidgets(self, widgets):
        for widget in widgets:
            widget.setEnabled(False)

    def enableWidgets(self, widgets):
        for widget in widgets:
            widget.setEnabled(True)

    def enableDisableWidgets(self):
        gl_widgets = [self.compactWidget.aspectSlider]
        ar_widgets = [self.compactWidget.apertureSlider, self.compactWidget.bladeRotateSlider,
                      self.compactWidget.bladeCountSlider, self.compactWidget.bladeAngleSlider]
        rs_widgets = [self.compactWidget.cocRadiusSlider, self.compactWidget.powerSlider,
                      self.compactWidget.bladeCountSliderRS, self.compactWidget.bladeAngleSliderRS]
        rm_widgets = [self.compactWidget.roundnessSlider, self.compactWidget.densitySlider,
                      self.compactWidget.bladeCountSliderRM, self.compactWidget.bladeAngleSliderRM]
        vp_widgets = [self.compactWidget.fStopSlider, self.compactWidget.focusRegionScaleSlider]
        vis_widgets = [self.compactWidget.ctrlVisibilityCheckBox, self.compactWidget.targetVisibilityCheckBox,
                       self.compactWidget.gridVisibilityCheckBox]
        all_widgets = gl_widgets + ar_widgets + rs_widgets + rm_widgets + vp_widgets + vis_widgets
        rendererUI = self.properties.rendererIconMenu.value
        meta = self.getMeta()
        if not meta:
            self.compactWidget.distanceSlider.setEnabled(False)
            self.compactWidget.ctrlScaleSlider.setEnabled(False)
            self.diableWidgets(all_widgets)
            if rendererUI == MAYA:
                self.enableWidgets(vp_widgets)
                self.compactWidget.distanceSlider.setEnabled(True)
            elif rendererUI == ARNOLD:
                if rendererload.getRendererIsLoaded(ARNOLD):
                    self.enableWidgets(ar_widgets)
                    self.enableWidgets(gl_widgets)
                    self.compactWidget.distanceSlider.setEnabled(True)
            elif rendererUI == REDSHIFT:
                if rendererload.getRendererIsLoaded(REDSHIFT):
                    pass
            elif rendererUI == RENDERMAN:
                if rendererload.getRendererIsLoaded(RENDERMAN):
                    self.enableWidgets(rm_widgets)
                    self.enableWidgets(vp_widgets)
                    self.enableWidgets(gl_widgets)
                    self.compactWidget.distanceSlider.setEnabled(True)
            return
        metaType = metafocuspuller.metaRenderer(meta[0])
        if metaType == VIEWPORT2:
            self.enableWidgets(vp_widgets)
            self.compactWidget.distanceSlider.setEnabled(False)
        elif metaType != rendererUI:
            self.diableWidgets(all_widgets)
            return
        if rendererUI == ARNOLD:
            self.enableWidgets(ar_widgets)
            self.enableWidgets(gl_widgets)
            self.compactWidget.distanceSlider.setEnabled(False)
        elif rendererUI == REDSHIFT:
            self.enableWidgets(rs_widgets)
            self.enableWidgets(gl_widgets)
        elif rendererUI == RENDERMAN:
            self.enableWidgets(rm_widgets)
            self.enableWidgets(gl_widgets)
            self.enableWidgets(vp_widgets)
            self.compactWidget.distanceSlider.setEnabled(False)
        self.compactWidget.ctrlScaleSlider.setEnabled(True)
        self.enableWidgets(vis_widgets)

    def showHideWidgets(self):
        rendererUI = self.properties.rendererIconMenu.value
        if rendererUI == ARNOLD:
            self.compactWidget.fStopSlider.setVisible(False)
            self.compactWidget.focusRegionScaleSlider.setVisible(False)
            self.compactWidget.apertureSlider.setVisible(True)
            self.compactWidget.bladeRotateSlider.setVisible(True)
            self.compactWidget.cocRadiusSlider.setVisible(False)
            self.compactWidget.powerSlider.setVisible(False)
            self.compactWidget.roundnessSlider.setVisible(False)
            self.compactWidget.densitySlider.setVisible(False)
            self.compactWidget.aspectSlider.setVisible(True)
            self.compactWidget.bladeCountSlider.setVisible(True)
            self.compactWidget.bladeCountSliderRS.setVisible(False)
            self.compactWidget.bladeCountSliderRM.setVisible(False)
            self.compactWidget.bladeAngleSlider.setVisible(True)
            self.compactWidget.bladeAngleSliderRS.setVisible(False)
            self.compactWidget.bladeAngleSliderRM.setVisible(False)
        elif rendererUI == REDSHIFT:
            self.compactWidget.fStopSlider.setVisible(False)
            self.compactWidget.focusRegionScaleSlider.setVisible(False)
            self.compactWidget.apertureSlider.setVisible(False)
            self.compactWidget.bladeRotateSlider.setVisible(False)
            self.compactWidget.cocRadiusSlider.setVisible(True)
            self.compactWidget.powerSlider.setVisible(True)
            self.compactWidget.roundnessSlider.setVisible(False)
            self.compactWidget.densitySlider.setVisible(False)
            self.compactWidget.aspectSlider.setVisible(True)
            self.compactWidget.bladeCountSlider.setVisible(False)
            self.compactWidget.bladeCountSliderRS.setVisible(True)
            self.compactWidget.bladeCountSliderRM.setVisible(False)
            self.compactWidget.bladeAngleSlider.setVisible(False)
            self.compactWidget.bladeAngleSliderRS.setVisible(True)
            self.compactWidget.bladeAngleSliderRM.setVisible(False)
        elif rendererUI == RENDERMAN:
            self.compactWidget.fStopSlider.setVisible(True)
            self.compactWidget.focusRegionScaleSlider.setVisible(True)
            self.compactWidget.apertureSlider.setVisible(False)
            self.compactWidget.bladeRotateSlider.setVisible(False)
            self.compactWidget.cocRadiusSlider.setVisible(False)
            self.compactWidget.powerSlider.setVisible(False)
            self.compactWidget.roundnessSlider.setVisible(True)
            self.compactWidget.densitySlider.setVisible(True)
            self.compactWidget.aspectSlider.setVisible(True)
            self.compactWidget.bladeCountSlider.setVisible(False)
            self.compactWidget.bladeCountSliderRS.setVisible(False)
            self.compactWidget.bladeCountSliderRM.setVisible(True)
            self.compactWidget.bladeAngleSlider.setVisible(False)
            self.compactWidget.bladeAngleSliderRS.setVisible(False)
            self.compactWidget.bladeAngleSliderRM.setVisible(True)
        else:  # MAYA
            self.compactWidget.distanceSlider.setVisible(True)
            self.compactWidget.fStopSlider.setVisible(True)
            self.compactWidget.focusRegionScaleSlider.setVisible(True)
            self.compactWidget.apertureSlider.setVisible(False)
            self.compactWidget.bladeRotateSlider.setVisible(False)
            self.compactWidget.cocRadiusSlider.setVisible(False)
            self.compactWidget.powerSlider.setVisible(False)
            self.compactWidget.roundnessSlider.setVisible(False)
            self.compactWidget.densitySlider.setVisible(False)
            self.compactWidget.aspectSlider.setVisible(False)
            self.compactWidget.bladeCountSlider.setVisible(False)
            self.compactWidget.bladeCountSliderRS.setVisible(False)
            self.compactWidget.bladeCountSliderRM.setVisible(False)
            self.compactWidget.bladeAngleSlider.setVisible(False)
            self.compactWidget.bladeAngleSliderRS.setVisible(False)
            self.compactWidget.bladeAngleSliderRM.setVisible(False)
        if rendererUI == MAYA:
            self.compactWidget.bokehDivider.setVisible(False)
        else:
            self.compactWidget.bokehDivider.setVisible(True)

    # ------------------
    # SELECTION CALLBACKS
    # ------------------

    def refreshUI(self):
        self.showHideWidgets()
        self.enableDisableWidgets()
        self.updateFromProperties()
        self.updateTree(delayed=False)

    def updateUI(self):
        """Pulls from the first selected meta node and pulls data into the UI"""
        if self.metaNodes:
            # Uses the first meta node found ------------------
            try:
                self.cameraZapi = self.metaNodes[0].getCameraZapi()
                self.properties.selectedCameraTxt.value = self.cameraZapi.name()
                self.properties.dofCheckBox.value = self.metaNodes[0].getDOF()
                self.properties.ctrlVisibilityCheckBox.value = self.metaNodes[0].getCtrlVisibility()
                self.properties.targetVisibilityCheckBox.value = self.metaNodes[0].getPlaneVisibility()
                self.properties.gridVisibilityCheckBox.value = self.metaNodes[0].getGridVis()
                self.properties.distanceSlider.value = self.metaNodes[0].getFocusDistance()
                self.properties.ctrlScaleSlider.value = self.metaNodes[0].getFocusScale()
            except:  # can be errors while pulling in data from broken setups
                pass
            # todo fix the try except
            try:
                self.properties.aspectSlider.value = self.metaNodes[0].getAspect()
            except AttributeError:
                pass
            try:
                self.properties.cocRadiusSlider.value = self.metaNodes[0].getCOCRadius()
                self.properties.powerSlider.value = self.metaNodes[0].getPower()
            except AttributeError:
                pass
            try:
                self.properties.fStopSlider.value = self.metaNodes[0].getFStopValue()
                self.properties.focusRegionScaleSlider.value = self.metaNodes[0].getRegionScale()
            except AttributeError:
                pass
            try:
                self.properties.roundnessSlider.value = self.metaNodes[0].getRoundness()
                self.properties.densitySlider.value = self.metaNodes[0].getDensity()
            except AttributeError:
                pass
            try:
                self.properties.apertureSlider.value = self.metaNodes[0].getAperture()
                self.properties.bladeRotateSlider.value = self.metaNodes[0].getRotation()
            except AttributeError:
                pass
            try:
                if self.metaNodes[0].renderer() == ARNOLD:
                    self.properties.bladeCountSlider.value = self.metaNodes[0].getBladeCount()
                    self.properties.bladeAngleSlider.value = self.metaNodes[0].getBladeAngle()
                if self.metaNodes[0].renderer() == REDSHIFT:
                    self.properties.bladeCountSliderRS.value = self.metaNodes[0].getBladeCount()
                    self.properties.bladeAngleSliderRS.value = self.metaNodes[0].getBladeAngle()
                if self.metaNodes[0].renderer() == RENDERMAN:
                    self.properties.bladeCountSliderRM.value = self.metaNodes[0].getBladeCount()
                    self.properties.bladeAngleSliderRM.value = self.metaNodes[0].getBladeAngle()
            except AttributeError:
                pass
        if self.cameraZapi:
            try:
                camera = self.cameraZapi.fullPathName()
            except RuntimeError:
                self.properties.selectedCameraTxt.value = ""
                self.cameraZapi = None
                camera = cameras.getFocusCamera()
                if not camera:
                    self.refreshUI()
                    return
        else:
            camera = cameras.getFocusCamera()
            if not camera:
                self.refreshUI()
                return

        rendererUI = self.properties.rendererIconMenu.value
        if rendererUI == MAYA or rendererUI == RENDERMAN:
            self.properties.dofCheckBox.value = metafocuspuller.getDOF(camera)
            self.properties.distanceSlider.value = metafocuspuller.getFocusDistance(camera)
            self.properties.fStopSlider.value = metafocuspuller.getFStopValue(camera)
            self.properties.focusRegionScaleSlider.value = metafocuspuller.getRegionScale(camera)
            if rendererUI == RENDERMAN:
                if rendererload.getRendererIsLoaded(RENDERMAN):
                    self.properties.aspectSlider.value = metafocuspuller_renderman.getAspect(camera)
                    self.properties.roundnessSlider.value = metafocuspuller_renderman.getRoundness(camera)
                    self.properties.densitySlider.value = metafocuspuller_renderman.getDensity(camera)
                    self.properties.bladeCountSliderRM.value = metafocuspuller_renderman.getBladeCount(camera)
                    self.properties.bladeAngleSliderRM.value = metafocuspuller_renderman.getBladeAngle(camera)
        elif rendererUI == ARNOLD:
            if rendererload.getRendererIsLoaded(ARNOLD):
                self.properties.dofCheckBox.value = metafocuspuller_arnold.getDOF(camera)
                self.properties.distanceSlider.value = metafocuspuller_arnold.getFocusDistance(camera)
                self.properties.apertureSlider.value = metafocuspuller_arnold.getAperture(camera)
                self.properties.aspectSlider.value = metafocuspuller_arnold.getAspect(camera)
                self.properties.bladeCountSlider.value = metafocuspuller_arnold.getBladeCount(camera)
                self.properties.bladeAngleSlider.value = metafocuspuller_arnold.getBladeAngle(camera)
                self.properties.bladeRotateSlider.value = metafocuspuller_arnold.getRotation(camera)
        self.refreshUI()

    def updateSelection(self):
        """ Update metanode based on selection
        """
        metas = list(metafocuspuller.selectedMetaNodes())
        if metas:
            self.metaNodes = metas
        self.updateUI()

    def selectionChanged(self, selection):
        """ Selection Changed callback event

        :param selection:  The selection from zapi
        :type selection: selected objects, only dag objects not components
        """
        if not selection:  # then still may be a selection
            selection = cmds.ls(selection=True)  # catches component and node selections
            if not selection:  # then nothing is selected
                self.metaNodes = list()
                return
        self.updateSelection()

    # ------------------
    # MOUSE OVER UI
    # ------------------

    def enterEvent(self, event):
        """Update selection on enter event
        """
        # disabled as easily causes issues.
        self.updateSelection()

    # ------------------------------------
    # RENDERER - AND SEND/RECEIVE ALL TOOLSETS
    # ------------------------------------

    def global_changeRenderer(self):
        """Updates all GUIs with the current renderer"""
        toolsets = toolsetui.toolsetsByAttr(attr="global_receiveRendererChange")
        renderer = self.properties.rendererIconMenu.value
        globalChangeRenderer(renderer, toolsets)

    # ------------------
    # LOGIC
    # ------------------

    def getCamera(self):
        "Get the camera full path"
        if not self.cameraZapi:
            return cameras.getFocusCamera()
        return self.cameraZapi.fullPathName()

    def getMeta(self):
        """Sets the FStop value from the UI value for the focus puller rig"""
        if not self.metaNodes:
            if not self.cameraZapi:
                camera = cameras.getFocusCamera()
                if not camera:
                    return
                return metafocuspuller.getMetasFromName(camera)
            return metafocuspuller.getMetaFromZapi(self.cameraZapi)
        return self.metaNodes

    def rendererLoad(self, currRenderer):
        if not rendererload.getRendererIsLoaded(currRenderer):  # the renderer is not loaded open window
            if not elements.checkRenderLoaded(currRenderer):
                return False
        return True

    def renderBuild(self, camera):
        if focuspuller.focusDistanceConnected(camera):  # focus distance is connected
            output.displayWarning("The focusDistance attribute is already keyed or connected.  "
                                  "Please disconnect. Cam: `{}`".format(camera))
            return
        rendererUI = self.properties.rendererIconMenu.value
        if rendererUI == MAYA:
            metafocuspuller.buildRigSetup(camera_name=camera)
        elif rendererUI == ARNOLD:
            if not self.rendererLoad(ARNOLD):
                return
            metafocuspuller_arnold.buildRigSetup(camera_name=camera)
        elif rendererUI == REDSHIFT:
            if not self.rendererLoad(REDSHIFT):
                return
            metafocuspuller_redshift.buildRigSetup(camera_name=camera)
        elif rendererUI == RENDERMAN:
            if not self.rendererLoad(RENDERMAN):
                return
            metafocuspuller_renderman.buildRigSetup(camera_name=camera)

    def postBuildValues(self):
        self.setDOF()
        self.setCtrlVisibility()
        self.setTargetVisibility()
        self.setGridVisibility()
        self.updateSelection()

    @toolsetwidget.ToolsetWidget.undoDecorator
    @toolsetcallbacks.ignoreCallbackDecorator
    def createFocusRig(self):
        """Creates focus rig on button clicked"""
        metafocuspuller.cleanupBrokenMetaNodes(message=True)  # runs a cleanup of broken nodes before create as safety
        if not self.cameraZapi:
            camera = cameras.getFocusCamera()
            if not camera:
                return
        else:
            camera = self.cameraZapi.fullPathName()
        self.renderBuild(camera)
        self.postBuildValues()

    def updatingTextbox(self):
        """display the selected object name into the UI
        """
        self.properties.selectedCameraTxt.value = self.cameraZapi.name()
        self.updateUI()

    def loadCameraName(self):
        """Checks to see if selected objects is right before updating UI"""
        self.cameraZapi = metafocuspuller.checkLoadedCamera()
        if not self.cameraZapi:
            return
        self.updatingTextbox()

    def textTyped(self):
        self.cameraZapi = None
        camera = cameras.getFocusCamera()
        if not camera:
            return
        self.metaNodes = metafocuspuller.getMetasFromName(camera)

    def clearCameraName(self):
        self.properties.selectedCameraTxt.value = ""
        self.textTyped()
        self.updateUI()

    def selectFocusCtrl(self):
        """Selects the the focus ctrl from the selected camera rig"""
        if not self.metaNodes:
            output.displayWarning("There is no Rig. Can't select Focus Control")
            return
        for meta in self.metaNodes:
            meta.selectFocusCtrl()

    def selectCam(self):
        """Selects the the focus ctrl from the selected camera rig"""
        metas = self.getMeta()
        if metas:
            for meta in metas:
                meta.selectCamera()
                return
        camera = self.getCamera()
        if not camera:
            return
        metafocuspuller.selectCamera(camera)

    # SETTERS
    def setDOF(self):
        """Sets the DOF of the focus puller rig controls"""
        metas = self.getMeta()
        if metas:
            for meta in metas:
                dof_Value = self.properties.dofCheckBox.value
                meta.depthOfField(dof_Value)
                return
        camera = self.getCamera()
        if not camera:
            return
        rendererUI = self.properties.rendererIconMenu.value
        if rendererUI == MAYA or rendererUI == RENDERMAN:
            metafocuspuller.depthOfField(camera, self.properties.dofCheckBox.value)
        elif rendererUI == ARNOLD:
            if rendererload.getRendererIsLoaded(ARNOLD):
                metafocuspuller_arnold.depthOfField(camera, self.properties.dofCheckBox.value)

    def setCtrlVisibility(self):
        """Sets the visibility of the focus puller rig controls"""
        metas = self.getMeta()
        if not metas:
            return
        for meta in metas:
            checkbox_Value = self.properties.ctrlVisibilityCheckBox.value
            meta.ctrlVisibility(checkbox_Value)

    def setTargetVisibility(self):
        """Sets the visibility of the focus puller rig controls"""
        metas = self.getMeta()
        if not metas:
            return
        for meta in metas:
            checkbox_Value = self.properties.targetVisibilityCheckBox.value
            meta.planeVisibility(checkbox_Value)

    def setGridVisibility(self):
        metas = self.getMeta()
        if not metas:
            return
        for meta in metas:
            checkbox_Value = self.properties.gridVisibilityCheckBox.value
            meta.gridVisibility(checkbox_Value)

    def setFocusDistance(self):
        """Keys the FStop value from the UI value for the focus puller rig"""
        metas = self.getMeta()
        if metas:
            for meta in metas:
                meta.setFocusDistance(self.properties.distanceSlider.value)
                return
        camera = self.getCamera()
        if not camera:
            return
        rendererUI = self.properties.rendererIconMenu.value
        if rendererUI == MAYA or rendererUI == RENDERMAN:
            metafocuspuller.setFocusDistance(camera, self.properties.distanceSlider.value)
        if rendererUI == ARNOLD:
            if rendererload.getRendererIsLoaded(ARNOLD):
                metafocuspuller_arnold.focusDistance(camera, self.properties.distanceSlider.value)

    def setCtrlScale(self):
        """Sets the DOF of the focus puller rig controls"""
        metas = self.getMeta()
        if not metas:
            return
        for meta in metas:
            meta.setCtrlScale(self.properties.ctrlScaleSlider.value)

    # MAYA
    def setFStop(self):
        """Sets the FStop value from the UI value for the focus puller rig"""
        metas = self.getMeta()
        if metas:
            for meta in metas:
                meta.setFStop(self.properties.fStopSlider.value)
                return
        camera = self.getCamera()
        if not camera:
            return
        metafocuspuller.setFStop(camera, self.properties.fStopSlider.value)

    def setRegionScale(self):
        """Sets the DOF of the focus puller rig controls"""
        metas = self.getMeta()
        if metas:
            for meta in metas:
                meta.setFocusRegionScale(self.properties.focusRegionScaleSlider.value)
                return
        camera = self.getCamera()
        if not camera:
            return
        metafocuspuller.setFocusRegionScale(camera, self.properties.focusRegionScaleSlider.value)

    # ARNOLD
    def setAperture(self):
        if not self.metaNodes:
            camera = self.getCamera()
            if not camera:
                return
            if rendererload.getRendererIsLoaded(ARNOLD):
                metafocuspuller_arnold.aperture(camera, self.properties.apertureSlider.value)
            return
        for meta in self.metaNodes:
            try:
                meta.setAperture(self.properties.apertureSlider.value)
            except AttributeError:
                pass

    # REDSHIFT
    def setCOCRadius(self):
        if not self.metaNodes:
            return
        for meta in self.metaNodes:
            try:
                meta.setCOCRadius(self.properties.cocRadiusSlider.value)
            except AttributeError:
                pass

    def setPower(self):
        if not self.metaNodes:
            return
        for meta in self.metaNodes:
            try:
                meta.setPower(self.properties.powerSlider.value)
            except AttributeError:
                pass

    # BOKEH
    def setAspect(self):
        if not self.metaNodes:
            camera = self.getCamera()
            if not camera:
                return
            rendererUI = self.properties.rendererIconMenu.value
            if rendererUI == ARNOLD:
                if rendererload.getRendererIsLoaded(ARNOLD):
                    metafocuspuller_arnold.aspect(camera, self.properties.aspectSlider.value)
            if rendererUI == RENDERMAN:
                if rendererload.getRendererIsLoaded(RENDERMAN):
                    metafocuspuller_renderman.aspect(camera, self.properties.aspectSlider.value)
            return
        for meta in self.metaNodes:
            try:
                meta.setAspect(self.properties.aspectSlider.value)
            except AttributeError:
                pass

    def setBladeCount(self):
        if not self.metaNodes:
            camera = self.getCamera()
            if not camera:
                return
            rendererUI = self.properties.rendererIconMenu.value
            if rendererUI == ARNOLD:
                if rendererload.getRendererIsLoaded(ARNOLD):
                    metafocuspuller_arnold.bladeCount(camera, self.properties.bladeCountSlider.value)
            if rendererUI == RENDERMAN:
                if rendererload.getRendererIsLoaded(RENDERMAN):
                    metafocuspuller_renderman.bladeCount(camera, self.properties.bladeCountSliderRM.value)
            return
        for meta in self.metaNodes:
            try:
                if meta.renderer() == ARNOLD:
                    meta.setBladeCount(self.properties.bladeCountSlider.value)
                if meta.renderer() == REDSHIFT:
                    meta.setBladeCount(self.properties.bladeCountSliderRS.value)
                if meta.renderer() == RENDERMAN:
                    meta.setBladeCount(self.properties.bladeCountSliderRM.value)
            except AttributeError:
                pass

    def setBladeAngle(self):
        if not self.metaNodes:
            camera = self.getCamera()
            if not camera:
                return
            rendererUI = self.properties.rendererIconMenu.value
            if rendererUI == ARNOLD:
                if rendererload.getRendererIsLoaded(ARNOLD):
                    metafocuspuller_arnold.bladeAngle(camera, self.properties.bladeAngleSlider.value)
            if rendererUI == RENDERMAN:
                if rendererload.getRendererIsLoaded(RENDERMAN):
                    metafocuspuller_renderman.bladeAngle(camera, self.properties.bladeAngleSliderRM.value)
            return
        for meta in self.metaNodes:
            try:
                if meta.renderer() == ARNOLD:
                    meta.setBladeAngle(self.properties.bladeAngleSlider.value)
                if meta.renderer() == REDSHIFT:
                    meta.setBladeAngle(self.properties.bladeAngleSliderRS.value)
                if meta.renderer() == RENDERMAN:
                    meta.setBladeAngle(self.properties.bladeAngleSliderRM.value)
            except AttributeError:
                pass

    def setRoundness(self):
        if not self.metaNodes:
            camera = self.getCamera()
            if not camera:
                return
            if rendererload.getRendererIsLoaded(RENDERMAN):
                metafocuspuller_renderman.roundness(camera, self.properties.roundnessSlider.value)
            return
        for meta in self.metaNodes:
            try:
                meta.setRoundness(self.properties.roundnessSlider.value)
            except AttributeError:
                pass

    def setDensity(self):
        if not self.metaNodes:
            camera = self.getCamera()
            if not camera:
                return
            if rendererload.getRendererIsLoaded(RENDERMAN):
                metafocuspuller_renderman.density(camera, self.properties.densitySlider.value)
            return
        for meta in self.metaNodes:
            try:
                meta.setDensity(self.properties.densitySlider.value)
            except AttributeError:
                pass

    def setBladeRotation(self):
        if not self.metaNodes:
            camera = self.getCamera()
            if not camera:
                return
            rendererUI = self.properties.rendererIconMenu.value
            if rendererUI == ARNOLD:
                if rendererload.getRendererIsLoaded(ARNOLD):
                    metafocuspuller_arnold.bladeRotate(camera, self.properties.bladeRotateSlider.value)
            return
        for meta in self.metaNodes:
            try:
                meta.setBladeRotation(self.properties.bladeRotateSlider.value)
            except AttributeError:
                pass

    @toolsetwidget.ToolsetWidget.undoDecorator
    @toolsetcallbacks.ignoreCallbackDecorator
    def deleteBtnClicked(self):
        """Deletes the focus puller rig and empties UI inputs"""
        brokenFound = False
        if metafocuspuller.cleanupBrokenMetaNodes():  # removes broken setups (Cleanup)
            brokenFound = True
        if not self.metaNodes:
            if not self.cameraZapi:
                if not brokenFound:
                    output.displayWarning("There is no rig to delete")
                return
            metas = metafocuspuller.getMetaFromZapi(self.cameraZapi)
            if not metas:
                if not brokenFound:
                    output.displayWarning("There is no rig to delete")
                return
            self.metaNodes = metas
        for meta in self.metaNodes:
            focusdistanceValue = self.properties.distanceSlider.value
            cameraName = meta.getCameraStr()
            metaType = metafocuspuller.metaRenderer(meta)
            meta.deleteAddedAttr()
            meta.deleteAttr()
            self.metaNodes = list()
            self.clearCameraName()
            self.properties.ctrlScaleSlider.value = 1
            self.properties.dofCheckBox.value = 0
            if metaType == ARNOLD:
                metafocuspuller_arnold.focusDistance(cameraName, focusdistanceValue)
            else:
                metafocuspuller.setFocusDistance(cameraName, focusdistanceValue)
            output.displayInfo("Rig Deleted Successfully")
        self.updateSelection()

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        for widget in self.widgets():
            widget.selectedCameraBtn.clicked.connect(self.loadCameraName)
            widget.clearCameraBtn.clicked.connect(self.clearCameraName)
            widget.dofCheckBox.stateChanged.connect(self.setDOF)
            widget.ctrlVisibilityCheckBox.stateChanged.connect(self.setCtrlVisibility)
            widget.targetVisibilityCheckBox.stateChanged.connect(self.setTargetVisibility)
            widget.gridVisibilityCheckBox.stateChanged.connect(self.setGridVisibility)
            widget.createBtn.clicked.connect(self.createFocusRig)
            widget.deleteBtn.clicked.connect(self.deleteBtnClicked)
            widget.selectFocusCtrl.clicked.connect(self.selectFocusCtrl)
            widget.selectCameraShape.clicked.connect(self.selectCam)
            # widget.rendererIconMenu.actionTriggered.connect(self.updateUI)
            widget.rendererIconMenu.actionTriggered.connect(self.global_changeRenderer)

            # Sliders -------------------------
            widget.distanceSlider.numSliderChanged.connect(self.setFocusDistance)
            widget.distanceSlider.sliderPressed.connect(self.openUndoChunk)
            widget.distanceSlider.sliderReleased.connect(self.closeUndoChunk)

            widget.ctrlScaleSlider.numSliderChanged.connect(self.setCtrlScale)
            widget.ctrlScaleSlider.sliderPressed.connect(self.openUndoChunk)
            widget.ctrlScaleSlider.sliderReleased.connect(self.closeUndoChunk)

            # Blur Sliders
            widget.apertureSlider.numSliderChanged.connect(self.setAperture)
            widget.apertureSlider.sliderPressed.connect(self.openUndoChunk)
            widget.apertureSlider.sliderReleased.connect(self.closeUndoChunk)

            widget.fStopSlider.numSliderChanged.connect(self.setFStop)
            widget.fStopSlider.sliderPressed.connect(self.openUndoChunk)
            widget.fStopSlider.sliderReleased.connect(self.closeUndoChunk)

            widget.focusRegionScaleSlider.numSliderChanged.connect(self.setRegionScale)
            widget.focusRegionScaleSlider.sliderPressed.connect(self.openUndoChunk)
            widget.focusRegionScaleSlider.sliderReleased.connect(self.closeUndoChunk)

            widget.cocRadiusSlider.numSliderChanged.connect(self.setCOCRadius)
            widget.cocRadiusSlider.sliderPressed.connect(self.openUndoChunk)
            widget.cocRadiusSlider.sliderReleased.connect(self.closeUndoChunk)

            widget.powerSlider.numSliderChanged.connect(self.setPower)
            widget.powerSlider.sliderPressed.connect(self.openUndoChunk)
            widget.powerSlider.sliderReleased.connect(self.closeUndoChunk)

            # Bokeh Sliders
            widget.bladeRotateSlider.numSliderChanged.connect(self.setBladeRotation)
            widget.bladeRotateSlider.sliderPressed.connect(self.openUndoChunk)
            widget.bladeRotateSlider.sliderReleased.connect(self.closeUndoChunk)

            widget.aspectSlider.numSliderChanged.connect(self.setAspect)
            widget.aspectSlider.sliderPressed.connect(self.openUndoChunk)
            widget.aspectSlider.sliderReleased.connect(self.closeUndoChunk)

            widget.bladeCountSlider.numSliderChanged.connect(self.setBladeCount)
            widget.bladeCountSlider.sliderPressed.connect(self.openUndoChunk)
            widget.bladeCountSlider.sliderReleased.connect(self.closeUndoChunk)

            widget.bladeCountSliderRS.numSliderChanged.connect(self.setBladeCount)
            widget.bladeCountSliderRS.sliderPressed.connect(self.openUndoChunk)
            widget.bladeCountSliderRS.sliderReleased.connect(self.closeUndoChunk)

            widget.bladeCountSliderRM.numSliderChanged.connect(self.setBladeCount)
            widget.bladeCountSliderRM.sliderPressed.connect(self.openUndoChunk)
            widget.bladeCountSliderRM.sliderReleased.connect(self.closeUndoChunk)

            widget.bladeAngleSlider.numSliderChanged.connect(self.setBladeAngle)
            widget.bladeAngleSlider.sliderPressed.connect(self.openUndoChunk)
            widget.bladeAngleSlider.sliderReleased.connect(self.closeUndoChunk)

            widget.bladeAngleSliderRS.numSliderChanged.connect(self.setBladeAngle)
            widget.bladeAngleSliderRS.sliderPressed.connect(self.openUndoChunk)
            widget.bladeAngleSliderRS.sliderReleased.connect(self.closeUndoChunk)

            widget.bladeAngleSliderRM.numSliderChanged.connect(self.setBladeAngle)
            widget.bladeAngleSliderRM.sliderPressed.connect(self.openUndoChunk)
            widget.bladeAngleSliderRM.sliderReleased.connect(self.closeUndoChunk)

            widget.roundnessSlider.numSliderChanged.connect(self.setRoundness)
            widget.roundnessSlider.sliderPressed.connect(self.openUndoChunk)
            widget.roundnessSlider.sliderReleased.connect(self.closeUndoChunk)

            widget.densitySlider.numSliderChanged.connect(self.setDensity)
            widget.densitySlider.sliderPressed.connect(self.openUndoChunk)
            widget.densitySlider.sliderReleased.connect(self.closeUndoChunk)

        # connect callbacks
        self.selectionCallbacks.callback.connect(self.selectionChanged)
        self.toolsetActivated.connect(self.startSelectionCallback)
        self.toolsetDeactivated.connect(self.stopSelectionCallback)


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

        # Camera Text and Button ----------------------------------------
        tooltip = "Leave empty to affect the active camera in the scene.  \n" \
                  "Type or add with the triangle button to add to a specific camera."
        self.selectedCameraLabel = elements.Label(text="Camera: ")

        self.selectedCameraTxt = elements.StringEdit(label="",
                                                     editPlaceholder="Active Camera",
                                                     editText="",
                                                     toolTip=tooltip)
        tooltip = "Add the selected or active camera"
        self.selectedCameraBtn = elements.styledButton("",
                                                       "arrowLeft",
                                                       style=uic.BTN_TRANSPARENT_BG,
                                                       minWidth=15,
                                                       toolTip=tooltip)

        self.clearCameraBtn = elements.styledButton("",
                                                    "xMark",
                                                    style=uic.BTN_TRANSPARENT_BG,
                                                    minWidth=15,
                                                    toolTip=tooltip)

        # Visibility CheckBox --------------------------------------
        tooltip = "Show/hide the focus-control in the scene, if it exists. "
        self.ctrlVisibilityCheckBox = elements.CheckBox(label="Ctrl Vis",
                                                        checked=True,
                                                        toolTip=tooltip)
        tooltip = "Show/hide the target Target control visibility in the scene."
        self.targetVisibilityCheckBox = elements.CheckBox(label="Target Vis",
                                                          checked=True,
                                                          toolTip=tooltip)

        # DOF CheckBox --------------------------------------
        tooltip = "Activate/deactivate depth-of-field, blur setting."
        self.dofCheckBox = elements.CheckBox(label="DOF",
                                             checked=True,
                                             toolTip=tooltip)


        # Slider ----------------------------------------
        tooltip = "Primary blur setting that adjusts Maya's `FStop` camera attribute. \n" \
                  "Lower `FStop` values will increase the out of focus effect. \n" \
                  "Note: Use the `Region` slider to blur more if the minimum \n" \
                  "value of 1.0 is not low enough."
        self.pathSlider = elements.FloatSlider(label="F Stop",
                                               defaultValue=5.6,
                                               sliderMin=1.0,
                                               sliderMax=21.0,
                                               labelBtnRatio=12,
                                               sliderRatio=24,
                                               labelRatio=10,
                                               editBoxRatio=14,
                                               decimalPlaces=3,
                                               dynamicMax=True,
                                               toolTip=tooltip)


        # Grid Vis checkbox --------------------------------------
        tooltip = "Shows a templated grid representing the plane that has clear focus. "
        self.gridVisibilityCheckBox = elements.CheckBox(label="Grid Vis",
                                                        checked=False,
                                                        toolTip=tooltip)

        # Select Focus Control Button --------------------------------------
        tooltip = "Select the focus control in the scene."
        self.selectFocusCtrl = elements.styledButton("",
                                                     icon="locator",
                                                     style=uic.BTN_DEFAULT,
                                                     toolTip=tooltip)
        # Select Camera Shape Button --------------------------------------
        tooltip = "Select the related camera shape node."
        self.selectCameraShape = elements.styledButton("",
                                                       icon="movieCamera",
                                                       style=uic.BTN_DEFAULT,
                                                       toolTip=tooltip)
        # Create Rig Button ---------------------------------------
        tooltip = "Creates a `Focus Distance` control rig for setting the distance attribute. \n" \
                  "- Leave the `Camera` textbox empty to build on the currently active camera. \n" \
                  "- Or select a camera and enter it into the textbox. \n" \
                  "Run and a `Focus Distance` rig will attach to the current camera."
        self.createBtn = elements.styledButton("Create Distance Rig",
                                               icon="focusAim",
                                               style=uic.BTN_DEFAULT,
                                               toolTip=tooltip)
        # Delete Button ---------------------------------------
        tooltip = "Deletes the current focus puller rig/controls.  \n" \
                  "Select any part of the rig or camera and press. \n" \
                  "The focus controls will be removed. "
        self.deleteBtn = elements.styledButton("",
                                               "trash",
                                               parent=self,
                                               minWidth=uic.BTN_W_ICN_MED,
                                               toolTip=tooltip)

        # Renderer Button --------------------------------------
        toolTip = "Change renderer"
        self.rendererIconMenu = elements.iconMenuButtonCombo(RENDERER_ICONS_LIST,
                                                             self.properties.rendererIconMenu.value,
                                                             toolTip=toolTip)

        # Bokeh Label Divider --------------------------------------
        self.bokehDivider = elements.LabelDivider("Bokeh")

        # ----------------
        # GLOBAL SLIDERS
        # ----------------

        # Distance Slider ----------------------------------------
        tooltip = "The distance at which objects appear in perfect focus. \n" \
                  "When the Distance Rig has been created, use the `persp_focus_ctrl` \n" \
                  "scene to adjust. "
        self.distanceSlider = elements.FloatSlider(label="Distance",
                                                   defaultValue=5.0,
                                                   sliderMin=0.1,
                                                   sliderMax=20.0,
                                                   labelBtnRatio=12,
                                                   sliderRatio=24,
                                                   labelRatio=15,
                                                   editBoxRatio=14,
                                                   decimalPlaces=2,
                                                   dynamicMax=True,
                                                   toolTip=tooltip)

        # Ctrl Scale Slider ----------------------------------------
        tooltip = "If the Focus Distance rig exists this setting controls the scale of \n" \
                  "the rig controls and grid plane in the scene. "
        self.ctrlScaleSlider = elements.FloatSlider(label="Ctrl Scale",
                                                    defaultValue=1.0,
                                                    sliderMin=0.1,
                                                    sliderMax=20.0,
                                                    labelBtnRatio=12,
                                                    sliderRatio=24,
                                                    labelRatio=15,
                                                    editBoxRatio=14,
                                                    decimalPlaces=2,
                                                    dynamicMax=True,
                                                    toolTip=tooltip)

        # Aspect Slider ----------------------------------------
        tooltip = "Values bigger than one produce an elongated defocusing effect, like an \n" \
                  "anamorphic lens while a value less than one will squash it. "
        self.aspectSlider = elements.FloatSlider(label="Aspect",
                                                 defaultValue=1.0,
                                                 sliderMin=0.0,
                                                 sliderMax=4.0,
                                                 labelBtnRatio=12,
                                                 sliderRatio=24,
                                                 labelRatio=15,
                                                 editBoxRatio=14,
                                                 decimalPlaces=3,
                                                 dynamicMax=True,
                                                 toolTip=tooltip)

        # ----------------
        # MAYA SLIDERS
        # ----------------

        # FStop Slider ----------------------------------------
        tooltip = "Like a real camera lens, this setting controls the strength of the blur effect. \n" \
                  "Lower values increase blur while higher values decrease blur."
        self.fStopSlider = elements.FloatSlider(label="F Stop",
                                                defaultValue=5.6,
                                                sliderMin=1.0,
                                                sliderMax=64.0,
                                                labelBtnRatio=12,
                                                sliderRatio=24,
                                                labelRatio=15,
                                                editBoxRatio=14,
                                                decimalPlaces=3,
                                                dynamicMax=False,
                                                toolTip=tooltip)

        # Focus Region Scale --------------------------------------
        tooltip = "This non-physical control allows the user to increase or decrease the blur effect. \n" \
                  "This is helpful to create incredibly thin slices of focus artificially."
        self.focusRegionScaleSlider = elements.FloatSlider(label="Region",
                                                           defaultValue=1.0,
                                                           sliderMin=0.001,
                                                           sliderMax=4.0,
                                                           labelBtnRatio=12,
                                                           labelRatio=15,
                                                           editBoxRatio=14,
                                                           sliderRatio=24,
                                                           decimalPlaces=3,
                                                           dynamicMax=True,
                                                           toolTip=tooltip)

        # ----------------
        # ARNOLD SLIDERS
        # ----------------

        # Blade Count Slider ----------------------------------------
        tooltip = "The number of blades (or polygon sides) of the highlighted shapes. \n" \
                  "Zero is considered a circle aperture, three triangle, six is a hexagon etc."
        self.bladeCountSlider = elements.IntSlider(label="Blade Count",
                                                   defaultValue=0,
                                                   sliderMin=0,
                                                   sliderMax=40,
                                                   labelBtnRatio=12,
                                                   sliderRatio=24,
                                                   labelRatio=15,
                                                   editBoxRatio=14,
                                                   decimalPlaces=3,
                                                   dynamicMax=False,
                                                   dynamicMin=True,
                                                   toolTip=tooltip)

        # Aperture Slider ----------------------------------------
        tooltip = "The radius of the aperture in world units. The smaller the aperture, \n" \
                  "the sharper the images (shallower depth of field). A size of zero\n" \
                  "produces no depth of field blurring."
        self.apertureSlider = elements.FloatSlider(label="Aperture",
                                                   defaultValue=0.0,
                                                   sliderMin=0.0,
                                                   sliderMax=20.0,
                                                   labelBtnRatio=12,
                                                   sliderRatio=24,
                                                   labelRatio=15,
                                                   editBoxRatio=14,
                                                   decimalPlaces=3,
                                                   dynamicMax=False,
                                                   toolTip=tooltip)

        # Blade Angle Slider ----------------------------------------
        tooltip = "The curvature of the polygonal sides on the bokeh highlight. \n" \
                  "A value of 0 means hard straight sides. Increasing this value \n" \
                  "all the way to 1.0 which produces a perfect disk. \n" \
                  "Negative values produce a `pinched` or `star-shaped` aperture."
        self.bladeAngleSlider = elements.FloatSlider(label="Curvature",
                                                     defaultValue=0.0,
                                                     sliderMin=0.0,
                                                     sliderMax=20.0,
                                                     labelBtnRatio=12,
                                                     sliderRatio=24,
                                                     labelRatio=15,
                                                     editBoxRatio=14,
                                                     decimalPlaces=3,
                                                     dynamicMax=False,
                                                     toolTip=tooltip)

        # Blade Rotation Slider ----------------------------------------
        tooltip = "Rotates the aperture by the specified number of degrees."
        self.bladeRotateSlider = elements.FloatSlider(label="Rotation",
                                                      defaultValue=0.0,
                                                      sliderMin=0.0,
                                                      sliderMax=50.0,
                                                      labelBtnRatio=12,
                                                      sliderRatio=24,
                                                      labelRatio=15,
                                                      editBoxRatio=14,
                                                      decimalPlaces=3,
                                                      dynamicMax=True,
                                                      toolTip=tooltip)

        # ------------------
        # REDSHIFT SLIDERS
        # ------------------

        # CoC Radius Slider ----------------------------------------
        tooltip = "`CoC` stands for `circle of confusion`. This parameter controls how \n" \
                  "strong the Depth-Of-Field effect will be. Smaller values keep a larger \n" \
                  "range around `Focus Distance` in focus, i.e. more of the image is in focus. \n" \
                  "Larger values make the effect stronger - only parts of the image exactly at a \n" \
                  "`Focus Distance` will be sharp, everything else will be blurry.\n\n" \
                  "circleOfConfusion = focalLength / fStop / 2 / (mm in scene units)"
        self.cocRadiusSlider = elements.FloatSlider(label="CoC Radius",
                                                    defaultValue=1.0,
                                                    sliderMin=0.0,
                                                    sliderMax=100.0,
                                                    labelBtnRatio=12,
                                                    sliderRatio=24,
                                                    labelRatio=15,
                                                    editBoxRatio=14,
                                                    decimalPlaces=3,
                                                    dynamicMax=True,
                                                    toolTip=tooltip)

        # Power Slider ----------------------------------------
        tooltip = "You can think of out-of-focus pixels as blurry disks. The blurrier a pixel \n" \
                  "is, the larger the disk. The `Power` parameter controls how these disks appear.\n\n" \
                  "1.0 is the default value, values of 10.0 give a double vision effect."
        self.powerSlider = elements.FloatSlider(label="Power",
                                                defaultValue=1.0,
                                                sliderMin=0.0,
                                                sliderMax=100.0,
                                                labelBtnRatio=12,
                                                sliderRatio=24,
                                                labelRatio=15,
                                                editBoxRatio=14,
                                                decimalPlaces=3,
                                                dynamicMax=True,
                                                toolTip=tooltip)

        tooltip = "Rotates the highlights bokeh effect."
        self.bladeAngleSliderRS = elements.FloatSlider(label="Rotation",
                                                       defaultValue=0.0,
                                                       sliderMin=0.0,
                                                       sliderMax=1.0,
                                                       labelBtnRatio=12,
                                                       sliderRatio=24,
                                                       labelRatio=15,
                                                       editBoxRatio=14,
                                                       decimalPlaces=3,
                                                       dynamicMax=False,
                                                       toolTip=tooltip)

        tooltip = "The number of blades (or polygon sides) of the highlighted shapes. \n" \
                  "Zero is considered a circle aperture, three triangle, six is a hexagon etc."
        self.bladeCountSliderRS = elements.IntSlider(label="Blade Count",
                                                     defaultValue=0,
                                                     sliderMin=0,
                                                     sliderMax=64,
                                                     labelBtnRatio=12,
                                                     sliderRatio=24,
                                                     labelRatio=15,
                                                     editBoxRatio=14,
                                                     decimalPlaces=3,
                                                     dynamicMax=False,
                                                     dynamicMin=True,
                                                     toolTip=tooltip)

        # -------------------
        # RENDERMAN SLIDERS
        # -------------------

        # Roundness Slider --------------------------------------
        tooltip = "The roundness will curve the edges of our aperture blades in order to \n " \
                  "give them a more rounded appearance. Thus giving your highlights a more \n" \
                  "rounded shape. \n\n" \
                  "Negative values produce a `pinched` or `star-shaped` aperture."
        self.roundnessSlider = elements.FloatSlider(label="Roundness",
                                                    defaultValue=0.0,
                                                    sliderMin=-1.0,
                                                    sliderMax=1.0,
                                                    labelBtnRatio=12,
                                                    sliderRatio=24,
                                                    labelRatio=15,
                                                    editBoxRatio=14,
                                                    decimalPlaces=3,
                                                    dynamicMax=True,
                                                    toolTip=tooltip)

        tooltip = "Rotates the aperture by the specified number of degrees."
        self.bladeAngleSliderRM = elements.FloatSlider(label="Angle",
                                                       defaultValue=0.0,
                                                       sliderMin=0.0,
                                                       sliderMax=360.0,
                                                       labelBtnRatio=12,
                                                       sliderRatio=24,
                                                       labelRatio=15,
                                                       editBoxRatio=14,
                                                       decimalPlaces=3,
                                                       dynamicMax=True,
                                                       toolTip=tooltip)

        # Density Slider --------------------------------------
        tooltip = "`Good bokeh` is classed as having a brighter center and a falloff towards the \n" \
                  "edges in each de-focused point of light. However not every lens has good bokeh. \n" \
                  "You are able to mimic the good (or bad) light falloff in your lens by using this \n" \
                  "control. The default of 0 gives a constant brightness (neutral bokeh), -1 is \n" \
                  "brighter at the center and a falloff towards the edge (good bokeh). and 1 gives \n" \
                  "you a bright rim (bad bokeh)."
        self.densitySlider = elements.FloatSlider(label="Density",
                                                  defaultValue=0.0,
                                                  sliderMin=-1.0,
                                                  sliderMax=1.0,
                                                  labelBtnRatio=12,
                                                  sliderRatio=24,
                                                  labelRatio=15,
                                                  editBoxRatio=14,
                                                  decimalPlaces=3,
                                                  dynamicMax=True,
                                                  toolTip=tooltip)

        tooltip = "The number of blades (or polygon sides) of the highlighted shapes. \n" \
                  "Zero is considered a circle aperture, three triangle, six is a hexagon etc."
        self.bladeCountSliderRM = elements.IntSlider(label="Blade Count",
                                                     defaultValue=0,
                                                     sliderMin=0,
                                                     sliderMax=20,
                                                     labelBtnRatio=12,
                                                     sliderRatio=24,
                                                     labelRatio=15,
                                                     editBoxRatio=14,
                                                     decimalPlaces=3,
                                                     dynamicMax=True,
                                                     dynamicMin=True,
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

        # Text/Visibility Layout -----------------------------------------
        subLayoutCamera = elements.hBoxLayout(spacing=uic.SLRG)
        subLayoutCamera.addWidget(self.selectedCameraLabel)
        subLayoutCamera.addWidget(self.selectedCameraTxt)
        subLayoutCamera.addWidget(self.selectedCameraBtn)
        subLayoutCamera.addWidget(self.clearCameraBtn)

        # CheckBox Layout -----------------------------------------
        subLayoutCheckBox = elements.hBoxLayout(spacing=uic.SPACING, margins=(uic.SREG, uic.SSML, uic.SREG, 0))
        subLayoutCheckBox.addWidget(self.dofCheckBox)
        subLayoutCheckBox.addWidget(self.ctrlVisibilityCheckBox)
        subLayoutCheckBox.addWidget(self.targetVisibilityCheckBox)
        subLayoutCheckBox.addWidget(self.gridVisibilityCheckBox)

        # Button Layout ------------------------------------------
        buttonLayout = elements.hBoxLayout(spacing=uic.SPACING)
        buttonLayout.addWidget(self.selectFocusCtrl)
        buttonLayout.addWidget(self.selectCameraShape)
        buttonLayout.addWidget(self.createBtn, 1)
        buttonLayout.addWidget(self.deleteBtn)
        buttonLayout.addWidget(self.rendererIconMenu)

        # Add To Main Layout ---------------------------------------
        mainLayout.addLayout(subLayoutCamera)
        mainLayout.addLayout(subLayoutCheckBox)
        mainLayout.addWidget(elements.LabelDivider("Focus Distance"))
        mainLayout.addWidget(self.distanceSlider)
        mainLayout.addWidget(elements.LabelDivider("Blur Amount"))
        mainLayout.addWidget(self.apertureSlider)
        mainLayout.addWidget(self.fStopSlider)
        mainLayout.addWidget(self.focusRegionScaleSlider)
        mainLayout.addWidget(self.cocRadiusSlider)
        mainLayout.addWidget(self.powerSlider)
        mainLayout.addWidget(self.bokehDivider)  # Bokeh Divider
        mainLayout.addWidget(self.aspectSlider)
        mainLayout.addWidget(self.roundnessSlider)
        mainLayout.addWidget(self.densitySlider)
        mainLayout.addWidget(self.bladeCountSlider)
        mainLayout.addWidget(self.bladeCountSliderRS)
        mainLayout.addWidget(self.bladeCountSliderRM)
        mainLayout.addWidget(self.bladeAngleSlider)
        mainLayout.addWidget(self.bladeAngleSliderRS)
        mainLayout.addWidget(self.bladeAngleSliderRM)
        mainLayout.addWidget(self.bladeRotateSlider)
        mainLayout.addWidget(elements.LabelDivider("Rig"))
        mainLayout.addWidget(self.ctrlScaleSlider)
        mainLayout.addLayout(buttonLayout)
