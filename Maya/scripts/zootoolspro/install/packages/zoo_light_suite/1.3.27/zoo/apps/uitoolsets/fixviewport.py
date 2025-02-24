from collections import OrderedDict

from zoovendor.Qt import QtWidgets

from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.apps.toolsetsui import toolsetcallbacks
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements
from zoo.core.util import env

from zoo.libs.utils import output

from zoo.apps.camera_tools.cameraconstants import CLIP_PLANES_LIST

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1

MAYA_VERSION = 0
if env.isMaya():
    from zoo.libs.maya.cmds.meta import metaviewportlight
    from zoo.libs.maya.cmds.cameras import cameras
    from zoo.libs.maya.cmds.display import viewportmodes, viewportcolors
    from zoo.libs.maya.cmds.lighting import viewportlights
    from zoo.libs.maya.utils import mayaenv, mayacolors

    MAYA_VERSION = mayaenv.mayaVersion()

INTENSITY_STANDARD_SURFACE = 1.7
INTENSITY_LAMBERT = 1.0
MULTIPLIER_LIST = ["Intensity Lambert/Blinn"]
DEFAULT_MULTIPLIER = 0
if MAYA_VERSION >= 2020:
    MULTIPLIER_LIST.append("Intensity StandardSurface")
    DEFAULT_MULTIPLIER = 1

RENDERER = ["Viewport"]

DIRECTIONAL_INTENSITY = 0.55
SPECULAR_INTENSITY = 0.0
HDRI_INTENSITY = 0.14
SOFT_ANGLE = 2.0
SUPER_SOFT_ANGLE = 4.0

UI_MODE_COMPACT = 0
ANTI_ALIAS_SAMPLES_STR = ["8", "16"]
ANTI_ALIAS_SAMPLES = [8, 16]
MAX_LIGHTS = [8, 16]
MAX_LIGHTS_STR = ["8", "16"]
CLIPPING_LIST = list()
CLIPPING_LIST_STR = list()

LIGHT_CB_KEY = "lightCheckbox"
SHAD_CB_KEY = "shadowsCheckbox"
AO_CB_KEY = "screenAOCheckbox"
AA_CB_KEY = "antiAliasCheckbox"
AA_SAMPLES_KEY = "antiAliasSamples"
TEXTURES_KEY = "texturesCheckbox"
MAX_LIGHTS_I_KEY = "maxLightsInt"

BUILD_DIRECTIONAL_KEY = "buildDirectional"
BUILD_HDRI_KEY = "buildHdri"
DIR_COUNT_F_KEY = "directionCount"
DIRECTIONAL_INTENSITY_KEY = "directionalIntensity"
HDRI_INTENSITY_KEY = "hdriIntensity"
SPECULAR_INTENSITY_KEY = "specularIntensity"
SOFT_ANGLE_KEY = "softAngle"
SHADOW_COLOR_KEY = "shadowColor"
DMAP_I_KEY = "dmapInt"

PRESET_DICT = OrderedDict()
PRESET_DICT['Preset None'] = {}

PRESET_DICT['Preset Viewport Off'] = {LIGHT_CB_KEY: False,
                                      SHAD_CB_KEY: False,
                                      AO_CB_KEY: False,
                                      AA_CB_KEY: False,
                                      TEXTURES_KEY: False,
                                      AA_SAMPLES_KEY: 0,
                                      MAX_LIGHTS_I_KEY: 0,
                                      BUILD_DIRECTIONAL_KEY: False,
                                      BUILD_HDRI_KEY: False,
                                      DIR_COUNT_F_KEY: 1,
                                      DIRECTIONAL_INTENSITY_KEY: 1.0,
                                      HDRI_INTENSITY_KEY: 0.0,
                                      SPECULAR_INTENSITY_KEY: SPECULAR_INTENSITY,
                                      SOFT_ANGLE_KEY: SOFT_ANGLE,
                                      SHADOW_COLOR_KEY: (0.0, 0.0, 0.0),
                                      DMAP_I_KEY: 1024
                                      }

PRESET_DICT['Preset Low: Model'] = {LIGHT_CB_KEY: True,
                                    SHAD_CB_KEY: False,
                                    AO_CB_KEY: False,
                                    AA_CB_KEY: True,
                                    TEXTURES_KEY: False,
                                    AA_SAMPLES_KEY: 0,
                                    MAX_LIGHTS_I_KEY: 0,
                                    BUILD_DIRECTIONAL_KEY: True,
                                    BUILD_HDRI_KEY: False,
                                    DIR_COUNT_F_KEY: 1,
                                    DIRECTIONAL_INTENSITY_KEY: 1.0,
                                    HDRI_INTENSITY_KEY: 0.0,
                                    SPECULAR_INTENSITY_KEY: SPECULAR_INTENSITY,
                                    SOFT_ANGLE_KEY: SOFT_ANGLE,
                                    SHADOW_COLOR_KEY: (0.5, 0.5, 0.5),
                                    DMAP_I_KEY: 1024
                                    }

PRESET_DICT['Preset Low: Shadows'] = {LIGHT_CB_KEY: True,
                                      SHAD_CB_KEY: True,
                                      AO_CB_KEY: False,
                                      AA_CB_KEY: True,
                                      TEXTURES_KEY: False,
                                      AA_SAMPLES_KEY: 0,
                                      MAX_LIGHTS_I_KEY: 0,
                                      BUILD_DIRECTIONAL_KEY: True,
                                      BUILD_HDRI_KEY: False,
                                      DIR_COUNT_F_KEY: 1,
                                      DIRECTIONAL_INTENSITY_KEY: 1.0,
                                      HDRI_INTENSITY_KEY: 0.0,
                                      SPECULAR_INTENSITY_KEY: SPECULAR_INTENSITY,
                                      SOFT_ANGLE_KEY: SOFT_ANGLE,
                                      SHADOW_COLOR_KEY: (0.5, 0.5, 0.5),
                                      DMAP_I_KEY: 2048
                                      }

PRESET_DICT['Preset Medium: Sharp 4k'] = {LIGHT_CB_KEY: True,
                                          SHAD_CB_KEY: True,
                                          AO_CB_KEY: True,
                                          AA_CB_KEY: True,
                                          TEXTURES_KEY: True,
                                          AA_SAMPLES_KEY: 0,
                                          MAX_LIGHTS_I_KEY: 0,
                                          BUILD_DIRECTIONAL_KEY: True,
                                          BUILD_HDRI_KEY: True,
                                          DIR_COUNT_F_KEY: 1,
                                          DIRECTIONAL_INTENSITY_KEY: DIRECTIONAL_INTENSITY,
                                          HDRI_INTENSITY_KEY: HDRI_INTENSITY,
                                          SPECULAR_INTENSITY_KEY: SPECULAR_INTENSITY,
                                          SOFT_ANGLE_KEY: SOFT_ANGLE,
                                          SHADOW_COLOR_KEY: (0.0, 0.0, 0.0),
                                          DMAP_I_KEY: 4048
                                          }

PRESET_DICT['Preset Medium: Soft 1k'] = {LIGHT_CB_KEY: True,
                                         SHAD_CB_KEY: True,
                                         AO_CB_KEY: True,
                                         AA_CB_KEY: True,
                                         TEXTURES_KEY: True,
                                         AA_SAMPLES_KEY: 0,
                                         MAX_LIGHTS_I_KEY: 0,
                                         BUILD_DIRECTIONAL_KEY: True,
                                         BUILD_HDRI_KEY: True,
                                         DIR_COUNT_F_KEY: 7,
                                         DIRECTIONAL_INTENSITY_KEY: DIRECTIONAL_INTENSITY,
                                         HDRI_INTENSITY_KEY: HDRI_INTENSITY,
                                         SPECULAR_INTENSITY_KEY: SPECULAR_INTENSITY,
                                         SOFT_ANGLE_KEY: SOFT_ANGLE,
                                         SHADOW_COLOR_KEY: (0.0, 0.0, 0.0),
                                         DMAP_I_KEY: 1024
                                         }

PRESET_DICT['Preset High: Sharp 8k'] = {LIGHT_CB_KEY: True,
                                        SHAD_CB_KEY: True,
                                        AO_CB_KEY: True,
                                        AA_CB_KEY: True,
                                        TEXTURES_KEY: True,
                                        AA_SAMPLES_KEY: 0,
                                        MAX_LIGHTS_I_KEY: 0,
                                        BUILD_DIRECTIONAL_KEY: True,
                                        BUILD_HDRI_KEY: True,
                                        DIR_COUNT_F_KEY: 1,
                                        DIRECTIONAL_INTENSITY_KEY: DIRECTIONAL_INTENSITY,
                                        HDRI_INTENSITY_KEY: HDRI_INTENSITY,
                                        SPECULAR_INTENSITY_KEY: SPECULAR_INTENSITY,
                                        SOFT_ANGLE_KEY: SOFT_ANGLE,
                                        SHADOW_COLOR_KEY: (0.0, 0.0, 0.0),
                                        DMAP_I_KEY: 8192
                                        }

PRESET_DICT['Preset High: Soft 2k'] = {LIGHT_CB_KEY: True,
                                       SHAD_CB_KEY: True,
                                       AO_CB_KEY: True,
                                       AA_CB_KEY: True,
                                       TEXTURES_KEY: True,
                                       AA_SAMPLES_KEY: 1,
                                       MAX_LIGHTS_I_KEY: 1,
                                       BUILD_DIRECTIONAL_KEY: True,
                                       BUILD_HDRI_KEY: True,
                                       DIR_COUNT_F_KEY: 15,
                                       DIRECTIONAL_INTENSITY_KEY: DIRECTIONAL_INTENSITY,
                                       HDRI_INTENSITY_KEY: HDRI_INTENSITY,
                                       SPECULAR_INTENSITY_KEY: SPECULAR_INTENSITY,
                                       SOFT_ANGLE_KEY: SOFT_ANGLE,
                                       SHADOW_COLOR_KEY: (0.0, 0.0, 0.0),
                                       DMAP_I_KEY: 2048
                                       }

PRESET_DICT['Preset High: Super Soft 1k'] = {LIGHT_CB_KEY: True,
                                             SHAD_CB_KEY: True,
                                             AO_CB_KEY: True,
                                             AA_CB_KEY: True,
                                             TEXTURES_KEY: True,
                                             AA_SAMPLES_KEY: 1,
                                             MAX_LIGHTS_I_KEY: 1,
                                             BUILD_DIRECTIONAL_KEY: True,
                                             BUILD_HDRI_KEY: True,
                                             DIR_COUNT_F_KEY: 15,
                                             DIRECTIONAL_INTENSITY_KEY: DIRECTIONAL_INTENSITY,
                                             HDRI_INTENSITY_KEY: HDRI_INTENSITY,
                                             SPECULAR_INTENSITY_KEY: SPECULAR_INTENSITY,
                                             SOFT_ANGLE_KEY: SUPER_SOFT_ANGLE,
                                             SHADOW_COLOR_KEY: (0.0, 0.0, 0.0),
                                             DMAP_I_KEY: 1024
                                             }

for tple in CLIP_PLANES_LIST:  # is a dict
    CLIPPING_LIST_STR.append(tple)
    CLIPPING_LIST.append(CLIP_PLANES_LIST[tple])


class FixViewport(toolsetwidget.ToolsetWidget):
    """
    """
    id = "fixViewport"
    uiData = {"label": "Fix Viewport",
              "icon": "bandAid",
              "tooltip": "Adjusts Maya's viewport with a light HUD and viewport options.",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-fix-viewport/"
              }

    # ------------------
    # STARTUP
    # ------------------

    def preContentSetup(self):
        """First code to run"""
        self.toolsetWidget = self  # needed for callback decorators

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
        self.metaNode = None
        self.updateUI()
        self.uiConnections()

    def defaultAction(self):
        """Double Click"""
        pass

    def currentWidget(self):
        """ Current active widget

        :return:
        :rtype:  GuiWidgets
        """
        return super(FixViewport, self).currentWidget()

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiAdvanced or GuiCompact]
        """
        return super(FixViewport, self).widgets()

    # ------------------
    # RIGHT CLICKS
    # ------------------

    def actions(self):
        """Right click menu and actions
        """
        return []

    # ------------------
    # UPDATE UI
    # ------------------

    def checkClipPlanesMatch(self):
        """Sets self.properties.clippingCombo.value from the current camera if a match, if not leave."""
        camera = cameras.getFocusCamera()
        if not camera:
            return
        currentClipTuple = cameras.camClipPlanes(camera)
        if currentClipTuple in CLIPPING_LIST:
            self.properties.clippingCombo.value = CLIPPING_LIST.index(currentClipTuple)  # set the matching index

    def uiUpdateMaxLightsAA(self):
        """Sets the UI for the two comboboxes AA Samples and Max Lights"""
        # Max lights ---------------------
        maxLights = viewportmodes.maxLights()
        if maxLights > 8:  # then set to 16
            if maxLights != 16:
                viewportmodes.setMaxLights(16)
            self.properties.maxLightsCombo.value = 1
        else:
            self.properties.maxLightsCombo.value = 0
        # AA Samples ---------------------
        aaSamples = viewportmodes.antiAliasVPSamples()
        if aaSamples <= 8:  # then set to 16
            viewportmodes.setAntiAliasVPSamples(8)
            self.properties.aaSamplesCombo.value = 0
        else:
            viewportmodes.setAntiAliasVPSamples(16)
            self.properties.aaSamplesCombo.value = 1

    def updateLightSetupUI(self):
        """Updates the Light section of the UI"""
        metaNodes = metaviewportlight.sceneMetaNodes()
        self.showHideOrientCButton(metaNodes)
        if not metaNodes:  # setup already exists so parent to new camera
            return
        dirIntensity = metaNodes[0].dirIntensity()
        if dirIntensity is not None:
            self.properties.lightFloatSlider.value = dirIntensity
        hdrIntensity = metaNodes[0].hdrIntensity(self.properties.multiplierCombo.value)
        if hdrIntensity is not None:
            self.properties.hdriFloatSlider.value = hdrIntensity
        specIntensity = metaNodes[0].specIntensity()
        if specIntensity is not None:
            self.properties.specularSlider.value = specIntensity
        softAngle = metaNodes[0].softAngle()
        if softAngle is not None:
            self.properties.lightAngleSlider.value = softAngle
        shadowColor = metaNodes[0].shadowColor()
        if shadowColor is not None:
            self.properties.shadowColorSlider.value = shadowColor
        dMapRes = metaNodes[0].dMapRes()
        if dMapRes is not None:
            self.properties.dMapResSlider.value = dMapRes
        directionalCount = metaNodes[0].directionalCount()
        if directionalCount is not None:
            self.properties.lightCountSlider.value = directionalCount
        multiplierValue = metaNodes[0].multiplierState()
        if multiplierValue is not None:
            self.properties.multiplierCombo.value = multiplierValue

    def showHideOrientCButton(self, metaNodes):
        """Show/Hide the link orient button in the light section"""
        orientConstrained = True
        if metaNodes:  # setup already exists so parent to new camera
            orientConstrained = metaNodes[0].orientConstrained()
        for widget in self.widgets():
            widget.unlinkConstraintBtn.setVisible(orientConstrained)
            widget.linkConstraintBtn.setVisible(not orientConstrained)

    def updateVPCheckboxes(self):
        textures = viewportmodes.displayTextureMode(message=False)
        if textures is not None:
            self.properties.texturesCheckbox.value = textures
        vpLights = viewportmodes.displayLightingMode(message=False)
        if vpLights is not None:
            self.properties.lightsCheckbox.value = vpLights
        vpShadows = viewportmodes.displayShadowMode(message=False)
        if vpShadows is not None:
            self.properties.shadowsCheckbox.value = vpShadows
        vpAo = viewportmodes.displayOcclusion()
        if vpAo is not None:
            self.properties.aoCheckbox.value = vpAo
        vpAntiAliasing = viewportmodes.displayAntiAlias()
        if vpAntiAliasing is not None:
            self.properties.antiAliasCheckbox.value = vpAntiAliasing

    def updateUI(self):
        """Updates the entire UI"""
        self.updateVPCheckboxes()  # Update the viewport checkboxes
        self.uiUpdateMaxLightsAA()  # Max Lights and AA Samples
        self.checkClipPlanesMatch()  # Clipping Planes
        self.updateLightSetupUI()  # Pull Light Setup
        self.properties.bgColorSlider.value = viewportcolors.backgroundColorLinear()

        # Update the UI ------------------------------------
        self.updateFromProperties()

    # ------------------
    # MOUSE OVER UI
    # ------------------

    def enterEvent(self, event):
        """Update selection on enter event
        """
        self.updateUI()

    def checkRenderLoaded(self, renderer="Arnold"):
        """Checks that the renderer is loaded, if not opens a window asking the user to load it

        :param renderer: the nice name of the renderer "Arnold" or "Redshift" etc
        :type renderer: str
        :return rendererLoaded: True if the renderer is loaded
        :rtype rendererLoaded: bool
        """
        return elements.checkRenderLoaded(renderer)

    # ------------------
    # LOGIC - PRESETS
    # ------------------

    @toolsetwidget.ToolsetWidget.undoDecorator
    @toolsetcallbacks.ignoreCallbackDecorator
    def applyPreset(self, index):
        """Creates lights and UI settinsg from the preset combo box"""
        dict = list(PRESET_DICT.items())[self.properties.presetCombo.value][1]
        if not dict:  # is Preset None
            return
        # Apply presets to the UI
        self.applyPresetDict(dict)
        # Build/Delete/Update -----------------------
        if not self.properties.autoLightCheckbox.value:  # don't create the light
            return
        metaNodes = metaviewportlight.sceneMetaNodes()
        if not dict[BUILD_DIRECTIONAL_KEY] and not dict[BUILD_HDRI_KEY]:  # Ignore lights as viewport will be off
            return
        if not metaNodes:
            self.createViewportLight()  # Build the viewport light setup with UI settings
            return
        # Update the light setup -----------------------
        for meta in metaNodes:
            meta.setHdrIntensity(self.properties.hdriFloatSlider.value)
            meta.setSpecIntensity(self.properties.specularSlider.value)
            if not meta.directionalCount() == self.properties.lightCountSlider.value:  # will rebuild the dir lights
                meta.setDMapRes(256)  # temp set very low to save video ram in case of updating lots of lights
                meta.setDirectionalCountAuto(self.properties.lightCountSlider.value)
            else:
                meta.setDirIntensity(self.properties.lightFloatSlider.value)
                meta.setShadowColor(self.properties.shadowColorSlider.value)
            meta.setDMapRes(self.properties.dMapResSlider.value)
            meta.setSoftAngle(self.properties.lightAngleSlider.value)

    def applyPresetDict(self, dict):
        """Creates light and UI/Viewport settings from a dict preset

        :param dict: PRESET_DICT dictionary eg PRESET_DICT['Preset Low: Model']
        :type dict: dict
        """
        # Viewport Settings --------------------------
        self.properties.lightsCheckbox.value = dict[LIGHT_CB_KEY]
        self.properties.shadowsCheckbox.value = dict[SHAD_CB_KEY]
        self.properties.aoCheckbox.value = dict[AO_CB_KEY]
        self.properties.antiAliasCheckbox.value = dict[AA_CB_KEY]
        self.properties.texturesCheckbox.value = dict[TEXTURES_KEY]
        self.properties.aaSamplesCombo.value = dict[AA_SAMPLES_KEY]
        self.properties.maxLightsCombo.value = dict[MAX_LIGHTS_I_KEY]
        # Set Light Properties ---------------------------
        self.properties.lightCheckbox.value = dict[BUILD_DIRECTIONAL_KEY]
        self.properties.specularCheckbox.value = dict[BUILD_DIRECTIONAL_KEY]
        self.properties.hdriCheckbox.value = dict[BUILD_HDRI_KEY]
        self.properties.lightCountSlider.value = dict[DIR_COUNT_F_KEY]
        self.properties.lightFloatSlider.value = dict[DIRECTIONAL_INTENSITY_KEY]
        self.properties.hdriFloatSlider.value = dict[HDRI_INTENSITY_KEY]
        self.properties.specularSlider.value = dict[SPECULAR_INTENSITY_KEY]
        self.properties.lightAngleSlider.value = dict[SOFT_ANGLE_KEY]
        self.properties.shadowColorSlider.value = dict[SHADOW_COLOR_KEY]
        self.properties.dMapResSlider.value = dict[DMAP_I_KEY]
        # Update UI ---------------------------
        self.updateFromProperties()
        # Set Viewport settings --------------------
        viewportmodes.setDisplayLightingMode(self.properties.lightsCheckbox.value)
        viewportmodes.setDisplayShadowMode(self.properties.shadowsCheckbox.value)
        viewportmodes.setDisplayOcclusion(self.properties.aoCheckbox.value)
        viewportmodes.setDisplayAntiAlias(self.properties.antiAliasCheckbox.value)
        viewportmodes.setDisplayTextureMode(self.properties.texturesCheckbox.value)
        viewportmodes.setAntiAliasVPSamples(ANTI_ALIAS_SAMPLES[self.properties.aaSamplesCombo.value])
        viewportmodes.setMaxLights(MAX_LIGHTS[self.properties.maxLightsCombo.value])

    # ------------------
    # DIRECTIONAL LIGHT LOGIC
    # ------------------

    @toolsetwidget.ToolsetWidget.undoDecorator
    @toolsetcallbacks.ignoreCallbackDecorator
    def createViewportLightUndo(self):
        dict = PRESET_DICT['Preset Medium: Soft 1k']
        self.applyPresetDict(dict)
        self.createViewportLight()  # Build the viewport light setup with UI settings

    def createViewportLight(self):
        """Creates the viewport light and constrains to the current camera in the GUI
        """
        camera = self.properties.nameTxt.value
        if not camera:
            camera = cameras.getFocusCamera()
            if not camera:
                return
        if not self.checkRenderLoaded():
            return

        metaNodes = metaviewportlight.sceneMetaNodes()
        if metaNodes:  # setup already exists so parent to new camera
            metaNodes[0].switchCamera(camera)
            return

        # Create -------------------------------
        metaNode = metaviewportlight.ZooViewportLight()

        # Adjust for standardSurface intensity
        driectionalIntensity = self.properties.lightFloatSlider.value
        hdriIntensity = self.properties.hdriFloatSlider.value

        metaNode.createLightCamera(camera,
                                   selectLight=True,
                                   directionalIntensity=driectionalIntensity,
                                   specularIntensity=self.properties.specularSlider.value,
                                   hdriIntensity=hdriIntensity,
                                   shadowColor=self.properties.shadowColorSlider.value,
                                   lightCount=self.properties.lightCountSlider.value,
                                   softAngle=self.properties.lightAngleSlider.value,
                                   surfaceStandardMatch=self.properties.multiplierCombo.value,
                                   depthMap=self.properties.dMapResSlider.value,
                                   message=True)
        self.metaNode = metaNode
        self.uiUpdateMaxLightsAA()  # max lights might have changed so update UI
        self.updateFromProperties()

    @toolsetwidget.ToolsetWidget.undoDecorator
    @toolsetcallbacks.ignoreCallbackDecorator
    def deleteViewportLights(self):
        """Deletes all camera viewport lights in the scene"""
        metaviewportlight.deleteViewportLights()  # Delete the lights
        viewportmodes.setDisplayLightingMode(False)  # Set UI
        self.updateFromProperties()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def setDirectionalIntensity(self):
        metaNodes = metaviewportlight.cameraVLightMetaNodes()
        if not metaNodes:
            return
        metaNodes[0].setDirIntensity(self.properties.lightFloatSlider.value)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def setSoftAngle(self):
        metaNodes = metaviewportlight.cameraVLightMetaNodes()
        if not metaNodes:
            return
        metaNodes[0].setSoftAngle(self.properties.lightAngleSlider.value)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def setHdrIntensity(self):
        metaNodes = metaviewportlight.cameraVLightMetaNodes()
        if not metaNodes:
            return
        metaNodes[0].setHdrIntensity(self.properties.hdriFloatSlider.value)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def setSpecIntensity(self):
        metaNodes = metaviewportlight.cameraVLightMetaNodes()
        if not metaNodes:
            return
        metaNodes[0].setSpecIntensity(self.properties.specularSlider.value)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def setSoftAngleUndo(self):
        self.setSoftAngle()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def setShadowColor(self):
        metaNodes = metaviewportlight.cameraVLightMetaNodes()
        if not metaNodes:
            return
        metaNodes[0].setShadowColor(self.properties.shadowColorSlider.value)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def setDMap(self):
        metaNodes = metaviewportlight.cameraVLightMetaNodes()
        if not metaNodes:
            return
        metaNodes[0].setDMapRes(self.properties.dMapResSlider.value)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def deleteViewportLight(self):
        """Deletes all camera viewport lights in the scene with undo"""
        self.deleteViewportLights()
        metaNodes = metaviewportlight.sceneMetaNodes()
        if metaNodes:  # another setup still exists so bail
            return
        viewportlights.deleteViewportLayers()

    def getCameraName(self):
        """Gets the camera name in the current panel or in focus and adds it to the GUI"""
        self.properties.nameTxt.value = cameras.getFocusCamera()
        self.updateFromProperties()

    @toolsetwidget.ToolsetWidget.undoDecorator
    @toolsetcallbacks.ignoreCallbackDecorator
    def rotCamFollow(self):
        metaNodes = metaviewportlight.cameraVLightMetaNodes()
        if not metaNodes:
            return
        metaNodes[0].rotCamFollow(follow=True)
        self.showHideOrientCButton(metaNodes)
        self.updateFromProperties()

    @toolsetwidget.ToolsetWidget.undoDecorator
    @toolsetcallbacks.ignoreCallbackDecorator
    def rotCamUnfollow(self):
        metaNodes = metaviewportlight.cameraVLightMetaNodes()
        if not metaNodes:
            return
        metaNodes[0].rotCamFollow(follow=False)
        self.showHideOrientCButton(metaNodes)
        self.updateFromProperties()

    @toolsetwidget.ToolsetWidget.undoDecorator
    @toolsetcallbacks.ignoreCallbackDecorator
    def setLightCount(self):
        metaNodes = metaviewportlight.cameraVLightMetaNodes()
        if not metaNodes:
            return
        metaNodes[0].setDirectionalCount(self.properties.lightCountSlider.value,
                                         lightCount=self.properties.lightCountSlider.value,
                                         depthMap=self.properties.dMapResSlider.value,
                                         directionalIntensity=self.properties.lightFloatSlider.value,
                                         surfaceStandardMatch=self.properties.multiplierCombo.value,
                                         softAngle=self.properties.lightAngleSlider.value,
                                         shadowColor=self.properties.shadowColorSlider.value)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def setMultiplier(self, comboInt=0):
        metaNodes = metaviewportlight.cameraVLightMetaNodes()
        if not metaNodes:
            return
        metaNodes[0].setMultiplierState(self.properties.hdriFloatSlider.value,
                                        self.properties.multiplierCombo.value)
        self.updateUI()

    # ------------------
    # SELECT LIGHTS
    # ------------------

    @toolsetwidget.ToolsetWidget.undoDecorator
    @toolsetcallbacks.ignoreCallbackDecorator
    def selectMasterControl(self):
        metaNodes = metaviewportlight.cameraVLightMetaNodes()
        if not metaNodes:
            return
        metaNodes[0].selectMasterControl()

    @toolsetwidget.ToolsetWidget.undoDecorator
    @toolsetcallbacks.ignoreCallbackDecorator
    def selectDirectionalControl(self):
        metaNodes = metaviewportlight.cameraVLightMetaNodes()
        if not metaNodes:
            return
        metaNodes[0].selectDirectionalControl()

    @toolsetwidget.ToolsetWidget.undoDecorator
    @toolsetcallbacks.ignoreCallbackDecorator
    def selectHdriSkydomeControl(self):
        metaNodes = metaviewportlight.cameraVLightMetaNodes()
        if not metaNodes:
            return
        metaNodes[0].selectHdriControl()

    # ------------------
    # VIEWPORT LOGIC
    # ------------------

    def setTextureMode(self):
        """Displays Textures on/off in the viewport"""
        viewportmodes.setDisplayTextureMode(self.properties.texturesCheckbox.value)

    def showUdimTextures(self):
        """Displays UDIM Textures in the viewport"""
        viewportmodes.regenerateUdimTextures()

    def setBgColor(self):
        viewportcolors.setBackgroundColorLinear(self.properties.bgColorSlider.value)

    def setLightMode(self):
        viewportmodes.setDisplayLightingMode(self.properties.lightsCheckbox.value)

    def setShadowMode(self):
        viewportmodes.setDisplayShadowMode(self.properties.shadowsCheckbox.value)

    def setAoMode(self):
        viewportmodes.setDisplayOcclusion(self.properties.aoCheckbox.value)

    def setAntiAliasMode(self):
        viewportmodes.setDisplayAntiAlias(self.properties.antiAliasCheckbox.value)

    def setAntiAliasSamples(self):
        viewportmodes.setAntiAliasVPSamples(ANTI_ALIAS_SAMPLES[self.properties.aaSamplesCombo.value])

    def setClipPlanes(self):
        clipPlanes = CLIPPING_LIST[self.properties.clippingCombo.value]
        cameras.setCurrCamClipPlanes(clipPlanes[0], clipPlanes[1])

    def setMaxLights(self):
        viewportmodes.setMaxLights(MAX_LIGHTS[self.properties.maxLightsCombo.value])

    def renderingSpaceLinear(self):
        """Sets rendering space to be linear sRGB"""
        mayacolors.setRenderingSpace(renderSpace="linear")

    def renderingSpaceAces(self):
        """Sets rendering space to be aces sRGB"""
        mayacolors.setRenderingSpace(renderSpace="aces")

    def viewTransformNone(self):
        """Sets the view transform to be none (No Tone Map)"""
        mayacolors.setViewTransform(view="noToneMap")

    def viewTransformSDRVideo(self):
        """Sets the view transform to be SDR Video"""
        mayacolors.setViewTransform(view="sdrVideo")

    def viewTransformUnity(self):
        """Sets the view transform to be SDR Video"""
        mayacolors.setViewTransform(view="unity")

    def exposureContrast(self):
        viewportmodes.setViewportContrastGamma(exposure=self.properties.exposureSlider.value,
                                               gamma=1.0,
                                               contrast=self.properties.contrastSlider.value)

    def reloadRefreshViewport(self):
        """Reload/refreshes the viewport, fixing various update issues"""
        viewportmodes.reloadViewport(message=True)  # cmds.ogs(reset=True)

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        for widget in self.widgets():
            # Buttons Changed -----------------
            widget.createLightBtn.clicked.connect(self.createViewportLightUndo)
            widget.deleteVPLightBtn.clicked.connect(self.deleteViewportLight)
            widget.getCameraBtn.clicked.connect(self.getCameraName)

            widget.selectMasterCtrlBtn.clicked.connect(self.selectMasterControl)
            widget.selectDirectionalBtn.clicked.connect(self.selectDirectionalControl)
            widget.selectHdriBtn.clicked.connect(self.selectHdriSkydomeControl)
            widget.reloadViewportBtn.clicked.connect(self.reloadRefreshViewport)
            widget.unlinkConstraintBtn.clicked.connect(self.rotCamUnfollow)
            widget.linkConstraintBtn.clicked.connect(self.rotCamFollow)
            if MAYA_VERSION >= 2022:
                widget.renderSpaceLinearBtn.clicked.connect(self.renderingSpaceLinear)
                widget.renderSpaceAcesBtn.clicked.connect(self.renderingSpaceAces)
                widget.toneMapNoneBtn.clicked.connect(self.viewTransformNone)
                widget.toneMapSDRVideoBtn.clicked.connect(self.viewTransformSDRVideo)
                widget.toneMapUnityBtn.clicked.connect(self.viewTransformUnity)

            # Checkbox Changed -----------------
            widget.texturesCheckbox.stateChanged.connect(self.setTextureMode)
            widget.lightsCheckbox.stateChanged.connect(self.setLightMode)
            widget.shadowsCheckbox.stateChanged.connect(self.setShadowMode)
            widget.antiAliasCheckbox.stateChanged.connect(self.setAntiAliasMode)
            widget.aoCheckbox.stateChanged.connect(self.setAoMode)

            # Combo --------------------
            widget.aaSamplesCombo.itemChanged.connect(self.setAntiAliasSamples)
            widget.clippingCombo.itemChanged.connect(self.setClipPlanes)
            widget.maxLightsCombo.itemChanged.connect(self.setMaxLights)
            widget.presetCombo.itemChanged.connect(self.applyPreset)
            widget.multiplierCombo.itemChanged.connect(self.setMultiplier)

            # Text Changed ------------------
            widget.lightAngleSlider.numSliderChanged.connect(self.setSoftAngle)
            widget.lightAngleSlider.sliderPressed.connect(self.openUndoChunk)
            widget.lightAngleSlider.sliderReleased.connect(self.closeUndoChunk)

            widget.shadowColorSlider.colorSliderChanged.connect(self.setShadowColor)
            widget.shadowColorSlider.sliderPressed.connect(self.openUndoChunk)
            widget.shadowColorSlider.sliderReleased.connect(self.closeUndoChunk)

            widget.dMapResSlider.numSliderChanged.connect(self.setDMap)
            widget.dMapResSlider.sliderPressed.connect(self.openUndoChunk)
            widget.dMapResSlider.sliderReleased.connect(self.closeUndoChunk)

            # Sliders -------------------
            widget.exposureSlider.numSliderChanged.connect(self.exposureContrast)
            widget.exposureSlider.sliderPressed.connect(self.openUndoChunk)
            widget.exposureSlider.sliderReleased.connect(self.closeUndoChunk)

            widget.contrastSlider.numSliderChanged.connect(self.exposureContrast)
            widget.contrastSlider.sliderPressed.connect(self.openUndoChunk)
            widget.contrastSlider.sliderReleased.connect(self.closeUndoChunk)

            widget.lightFloatSlider.numSliderChanged.connect(self.setDirectionalIntensity)
            widget.lightFloatSlider.sliderPressed.connect(self.openUndoChunk)
            widget.lightFloatSlider.sliderReleased.connect(self.closeUndoChunk)

            widget.specularSlider.numSliderChanged.connect(self.setSpecIntensity)
            widget.specularSlider.sliderPressed.connect(self.openUndoChunk)
            widget.specularSlider.sliderReleased.connect(self.closeUndoChunk)

            widget.hdriFloatSlider.numSliderChanged.connect(self.setHdrIntensity)
            widget.hdriFloatSlider.sliderPressed.connect(self.openUndoChunk)
            widget.hdriFloatSlider.sliderReleased.connect(self.closeUndoChunk)

            widget.lightCountSlider.numSliderMajorChange.connect(self.setLightCount)

            # Color Slider ----------------------------------------
            widget.bgColorSlider.colorSliderChanged.connect(self.setBgColor)
            widget.hdriFloatSlider.sliderPressed.connect(self.openUndoChunk)
            widget.hdriFloatSlider.sliderReleased.connect(self.closeUndoChunk)

        self.advancedWidget.udimBtn.clicked.connect(self.showUdimTextures)


class GuiWidgets(QtWidgets.QWidget):
    def __init__(self, parent=None, properties=None, uiMode=None, toolsetWidget=None):
        """Builds the main widgets for all GUIs

        properties is the list(dictionaries) used to set logic and pass between the different UI layouts
        such as compact/adv etc

        :param parent: the parent of this widget
        :type parent: qtObject
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: object
        :param uiMode: 0 is compact ui mode, 1 is advanced ui mode
        :type uiMode: int
        """
        super(GuiWidgets, self).__init__(parent=parent)
        self.properties = properties
        # Preset Combo -----------------------------------------------------
        toolTip = "Viewport light presets. \n\n" \
                  " None: Does nothing \n" \
                  " Viewport Off: Removes any light rig and turns all viewport settings off. \n" \
                  " Low Model: Modeling single directional/spec light that matches Standard Surface shaders. \n" \
                  " Low Shadows: Shadows on with `Low Model` settings. \n" \
                  " Medium Sharp 4k: Single directional with 4k shadows and HDRI Skydome. " \
                  "Viewport settings medium. \n" \
                  " Medium Soft 1k: Seven directional lights with a single 1k soft shadow with " \
                  "specular and HDRI light. \n" \
                  " High Sharp 8k: Single directional with 8k shadows and HDRI Skydome.  Viewport settings high. \n" \
                  " High Soft 2k: Fifteen directionals with a single 2k shadows each with specular and HDRI Skydome."
        self.presetCombo = elements.ComboBoxRegular(label="",
                                                    items=list(PRESET_DICT.keys()),
                                                    toolTip=toolTip)
        # Build Light Auto Checkbox -----------------------------------------------------
        toolTip = "Creates a viewport light rig and attaches it to the current camera with preset changes. "
        self.autoLightCheckbox = elements.CheckBox(label="Create Light Automatically",
                                                   checked=True,
                                                   right=False,
                                                   toolTip=toolTip)

        # Light Multiplier Combo -----------------------------------------------------
        toolTip = "Multiply the viewport light rig intensity to match: \n" \
                  " - Standard Surface shaders (1.7) \n" \
                  " - Lambert/Blinn/Phong shaders (1.0) "
        self.multiplierCombo = elements.ComboBoxRegular(label="",
                                                        items=MULTIPLIER_LIST,
                                                        setIndex=DEFAULT_MULTIPLIER,
                                                        toolTip=toolTip)
        # Renderer Combo -----------------------------------------------------
        toolTip = "Currently only supports viewport lights, renderer support coming."
        self.rendererCombo = elements.ComboBoxRegular(label="Renderer",
                                                      items=RENDERER,
                                                      setIndex=0,
                                                      toolTip=toolTip)
        # Textures Checkbox -----------------------------------------------------
        toolTip = "Toggle viewport textures on/off."
        self.texturesCheckbox = elements.CheckBox(label="Textures",
                                                  checked=False,
                                                  right=False,
                                                  toolTip=toolTip)
        # Build Light Auto Checkbox -----------------------------------------------------
        toolTip = "Display the viewport grid on/off. "
        self.gridCheckbox = elements.CheckBox(label="Grid",
                                              checked=True,
                                              right=False,
                                              toolTip=toolTip)
        # Shadow Opacity Slider --------------------------------------------
        toolTip = "Change the background color.  \n" \
                  "Reset with `alt b` to cycle through default colors. "
        self.bgColorSlider = elements.ColorSlider(label="Background Color",
                                                  color=(0.0, 0.0, 0.0),
                                                  toolTip=toolTip)
        if uiMode == UI_MODE_ADVANCED:  # adjust ratio
            # UDIM btn ---------------------------------------
            toolTip = "Show UDIM (multi-tile) texture in the viewport, default is off. "
            self.udimBtn = elements.styledButton(text="Show UDIM Textures",
                                                 icon="checker",
                                                 toolTip=toolTip,
                                                 parent=self,
                                                 style=uic.BTN_LABEL_SML)
        # Lights Checkbox -----------------------------------------------------
        toolTip = "Toggle viewport lights, lights on/off in the scene."
        self.lightsCheckbox = elements.CheckBox(label="Lights",
                                                checked=False,
                                                toolTip=toolTip)
        # Shadows Checkbox -----------------------------------------------------
        toolTip = "Toggle depth map shadows on/off in the scene. "
        self.shadowsCheckbox = elements.CheckBox(label="Shadows",
                                                 checked=False,
                                                 toolTip=toolTip)
        # Screen AO Checkbox -----------------------------------------------------
        toolTip = "Toggle ambient occlusion on/off in the viewport. "
        self.aoCheckbox = elements.CheckBox(label="Screen AO",
                                            checked=False,
                                            toolTip=toolTip)
        # Anti Alias Checkbox -----------------------------------------------------
        toolTip = "Toggle anti-aliasing on/off in the viewport. "
        self.antiAliasCheckbox = elements.CheckBox(label="Anti-Alias",
                                                   checked=False,
                                                   toolTip=toolTip)

        # AA Samples -----------------------------------------------------
        toolTip = "Set the AA samples to 8 (low) or 16 (high) samples. "
        self.aaSamplesCombo = elements.ComboBoxRegular(items=ANTI_ALIAS_SAMPLES_STR,
                                                       toolTip=toolTip)

        # Max Lights -----------------------------------------------------
        toolTip = "Set the maximum viewport lights to be 8 or 16.  \n" \
                  "Maya does not include Skydome lights in this count.  \n" \
                  "Extra lights above the limit won't affect the viewport. "
        self.maxLightsCombo = elements.ComboBoxRegular(label="Max Lights",
                                                       items=MAX_LIGHTS_STR,
                                                       toolTip=toolTip)
        # Clip Planes -----------------------------------------------------
        toolTip = "Set the near and far clipping planes on the active viewport's camera.  \n" \
                  "Recommended to `Medium` in most cases. \n" \
                  "Reduces viewport flicker of objects/surfaces close together. "
        self.clippingCombo = elements.ComboBoxRegular(label="Clip",
                                                      items=CLIPPING_LIST_STR,
                                                      toolTip=toolTip)
        # Light Count Slider --------------------------------------------
        toolTip = "Set the number of lights in the viewport light rig. \n" \
                  "More lights will create accurate softness but may slow the scene. \n" \
                  "Auto-updates existing setups. Max light count is 15. "
        self.lightCountSlider = elements.IntSlider(label="Light Count",
                                                   defaultValue=7,
                                                   sliderMax=15,
                                                   sliderMin=1,
                                                   toolTip=toolTip)
        # Light Spread Slider --------------------------------------------
        toolTip = "Adjusts the softness of shadows on setups with more than one light. \n" \
                  "Auto-updates existing setups. "
        self.lightAngleSlider = elements.FloatSlider(label="Soft Angle",
                                                     defaultValue=SOFT_ANGLE,
                                                     sliderMax=8.0,
                                                     dynamicMax=True,
                                                     toolTip=toolTip)
        # DMap Res Slider --------------------------------------------
        toolTip = "Adjusts the depth map shadow pixel resolution setting for directional lights. \n" \
                  "Shadows are calculated based on the entire scene from the angle of each light. \n" \
                  "Sharp shadows are created with larger maps, will depend on scene scale. \n" \
                  "Softer shadows are created with smaller maps but may also introduce pixelation. \n" \
                  "Auto-updates existing setups. "
        self.dMapResSlider = elements.IntSlider(label="DMap Res",
                                                defaultValue=1024,
                                                sliderMin=16,
                                                sliderMax=4096,
                                                dynamicMax=True,
                                                toolTip=toolTip)
        # Light Checkbox Slider -----------------------------------------------------
        toolTip = "Adjust the intensity of the directional light rig.  \n" \
                  "All lights will combine to equal this setting.  \n" \
                  "Intensity is automatically multiplied by 1.7 if set to Standard Surface. \n" \
                  "Auto-updates existing setups."
        self.lightCheckbox = elements.CheckBox(label="Directional",
                                               checked=True,
                                               toolTip=toolTip,
                                               right=True,
                                               labelRatio=5,
                                               boxRatio=1)
        self.lightCheckbox.setVisible(False)  # Todo Temp
        self.lightFloatSlider = elements.FloatSlider(label="Directional",
                                                     defaultValue=DIRECTIONAL_INTENSITY,
                                                     toolTip=toolTip,
                                                     dynamicMax=True,
                                                     sliderMax=2.0)  # sliderRatio=40, labelBtnRatio=19
        # HDRI Checkbox Slider -----------------------------------------------------
        toolTip = "Adjust the intensity of the HDRI Skydome.  \n" \
                  "This light must be an Arnold Skydome to affect the viewport. \n" \
                  "Auto-updates existing setups."
        self.hdriCheckbox = elements.CheckBox(label="HDRI Arnold",
                                              checked=True,
                                              toolTip=toolTip,
                                              right=True,
                                              labelRatio=5,
                                              boxRatio=1)
        self.hdriCheckbox.setVisible(False)  # Todo Temp
        self.hdriFloatSlider = elements.FloatSlider(label="HDRI Arnold",
                                                    defaultValue=HDRI_INTENSITY,
                                                    toolTip=toolTip,
                                                    dynamicMax=True,
                                                    sliderMax=2.0)  # sliderRatio=40, labelBtnRatio=19
        # Specular Slider --------------------------------------------
        toolTip = "The intensity of the specular contribution to the viewport light. \n" \
                  "This setting is multiplied (overblown) to better match rendered settings. \n" \
                  "Auto-updates existing setups. "
        self.specularCheckbox = elements.CheckBox(label="Specular",
                                                  checked=True,
                                                  toolTip=toolTip,
                                                  right=True,
                                                  labelRatio=5,
                                                  boxRatio=1)
        self.specularCheckbox.setVisible(False)
        self.specularSlider = elements.FloatSlider(label="Specular",
                                                   defaultValue=SPECULAR_INTENSITY,
                                                   sliderMax=2.0,
                                                   dynamicMax=True,
                                                   toolTip=toolTip)  # sliderRatio=40, labelBtnRatio=19
        # Shadow Opacity Slider --------------------------------------------
        toolTip = "Set the shadow color of the directional light.  \n" \
                  "Default is black. Auto-updates existing setups. "
        self.shadowColorSlider = elements.ColorSlider(label="Shadow Color",
                                                      color=(0.0, 0.0, 0.0),
                                                      toolTip=toolTip)
        # Camera Name -----------------------------------------------------
        toolTip = "The name of the camera that the light will be constrained to. \n" \
                  "Leave empty to set to the active camera."
        self.nameTxt = elements.StringEdit(label="Camera",
                                           editPlaceholder="active viewport",
                                           editText="",
                                           toolTip=toolTip,
                                           labelRatio=40,
                                           editRatio=107)
        # Get Camera Name -----------------------------------------------------
        toolTip = "Select the camera name from the active panel or panel in focus. "
        self.getCameraBtn = elements.styledButton("",
                                                  "arrowLeft",
                                                  self,
                                                  toolTip=toolTip,
                                                  style=uic.BTN_TRANSPARENT_BG,
                                                  minWidth=15)
        # Create Btn --------------------------------------------
        toolTip = "Creates or reparents a viewport light rig with soft shadows, specular and HDRI Skydome controls. \n" \
                  "Uses the medium Soft 1k setting and adjusts UI settings to match.  " \
                  "Maya 2020+: Adjusts to compensate for darker Arnold and surfaceStandard shaders in Maya 2020.\n\n" \
                  "If a light rig already exists will switch the light rigs to a new viewport camera. "
        self.createLightBtn = elements.styledButton("Create/Reparent Light",
                                                    icon="bandAid",
                                                    toolTip=toolTip,
                                                    style=uic.BTN_DEFAULT)
        # Delete Viewport Light Button ------------------------------------
        toolTip = "Deletes the viewport light rig setup, including controls and chrome ball. "
        self.deleteVPLightBtn = elements.styledButton("",
                                                      "trash",
                                                      toolTip=toolTip,
                                                      parent=self,
                                                      minWidth=uic.BTN_W_ICN_MED)
        # Select Viewport Master Ctrl Button ------------------------------------
        toolTip = "Selects the master light control. "
        self.selectMasterCtrlBtn = elements.styledButton("",
                                                         "cursorSelect",
                                                         toolTip=toolTip,
                                                         parent=self,
                                                         minWidth=uic.BTN_W_ICN_MED)
        # Select Directional Light Button ------------------------------------
        toolTip = "Selects the directional light control. "
        self.selectDirectionalBtn = elements.styledButton("",
                                                          "lightarrows",
                                                          toolTip=toolTip,
                                                          parent=self,
                                                          minWidth=uic.BTN_W_ICN_MED)
        # Select Directional Light Button ------------------------------------
        toolTip = "Selects the hdri skydome light control."
        self.selectHdriBtn = elements.styledButton("",
                                                   "sky",
                                                   toolTip=toolTip,
                                                   parent=self,
                                                   minWidth=uic.BTN_W_ICN_MED)
        # Refresh Viewport Button ------------------------------------
        toolTip = "Refresh/restart the viewport. \n" \
                  "Fixes many issues related to the Maya's viewport including \n" \
                  "Maya 2020 round hole after building the light rig."
        self.reloadViewportBtn = elements.styledButton("",
                                                       "reload2",
                                                       toolTip=toolTip,
                                                       parent=self,
                                                       minWidth=uic.BTN_W_ICN_MED)
        # Link Unlink Button ------------------------------------
        toolTip = "Breaks or links the rotation of the viewport light from the camera. \n" \
                  " - Broken: The light rig will not rotate with the camera viewport. \n" \
                  " - Linked: The light rig will rotate with the camera viewport. "
        self.unlinkConstraintBtn = elements.styledButton("",
                                                         "linkConnected",
                                                         toolTip=toolTip,
                                                         parent=self,
                                                         minWidth=uic.BTN_W_ICN_MED)
        # Select Directional Light Button ------------------------------------
        self.linkConstraintBtn = elements.styledButton("",
                                                       "linkBroken",
                                                       toolTip=toolTip,
                                                       parent=self,
                                                       minWidth=uic.BTN_W_ICN_MED)
        # Contrast Factory Grey Btn --------------------------------------------
        toolTip = "Faked contrast using the both the viewport's `Exposure` and `Gamma` settings. \n" \
                  "Default is 0.0 "
        self.contrastSlider = elements.FloatSlider(label="Contrast",
                                                   defaultValue=-0.0,
                                                   sliderMax=1.0,
                                                   sliderMin=-1.0,
                                                   dynamicMax=True,
                                                   toolTip=toolTip)
        # Exposure Slider --------------------------------------------
        toolTip = "Set Maya's Exposure viewport setting to have brighter/darker exposure. \n" \
                  "Default is 0.0 "
        self.exposureSlider = elements.FloatSlider(label="Exposure",
                                                   defaultValue=0.0,
                                                   sliderMax=1.0,
                                                   sliderMin=-1.0,
                                                   toolTip=toolTip)
        if MAYA_VERSION >= 2022:
            # Linear btn ---------------------------------------
            toolTip = "Set Linear Color Space. \n" \
                      "Matches older versions of Maya and Zoo Tools. \n" \
                      "Assumes a sRGB monitor."
            self.renderSpaceLinearBtn = elements.styledButton("Linear (sRGB)",
                                                              icon="clapperBoard",
                                                              toolTip=toolTip,
                                                              style=uic.BTN_DEFAULT)
            # ACES btn ---------------------------------------
            toolTip = "Set ACES Color Space. \n" \
                      "Newer color space and default in 2022.  \n" \
                      "May not match some compositing programs like After Effects \n" \
                      "Assumes a sRGB monitor."
            self.renderSpaceAcesBtn = elements.styledButton("Aces (sRGB)",
                                                            icon="clapperBoard",
                                                            toolTip=toolTip,
                                                            style=uic.BTN_DEFAULT)
            # No Tone-map btn ---------------------------------------
            toolTip = "Removes the tone-map, so no grade is applied. \n" \
                      "Matches 2020 and below, also fixes wireframe aliasing in 2022. "
            self.toneMapNoneBtn = elements.AlignedButton("No Tone-Map",
                                                         icon="graphLinear",
                                                         toolTip=toolTip)
            # SDR Video btn ---------------------------------------
            toolTip = "Use the SDR-Video view transform (Grade/Tone-Map) \n" \
                      "Default for 2022, also distorts wireframes."
            self.toneMapSDRVideoBtn = elements.AlignedButton("SDR-Video",
                                                             icon="graphGrade",
                                                             toolTip=toolTip)
            # SDR Video btn ---------------------------------------
            toolTip = "Use the Unity Neutral view transform (Grade/Tone-Map) \n" \
                      "Also distorts wireframe aliasing."
            self.toneMapUnityBtn = elements.AlignedButton("Unity Neutral",
                                                          icon="graphGrade",
                                                          toolTip=toolTip)


class GuiCompact(GuiWidgets):
    def __init__(self, parent=None, properties=None, uiMode=UI_MODE_COMPACT, toolsetWidget=None):
        """Adds the layout building the compact version of the GUI:

            default uiMode - 0 is advanced (UI_MODE_COMPACT)

        :param parent: the parent of this widget
        :type parent: qtObject
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: list[dict]
        """
        super(GuiCompact, self).__init__(parent=parent, properties=properties, uiMode=uiMode,
                                         toolsetWidget=toolsetWidget)
        # Main Layout ---------------------------------------
        contentsLayout = elements.vBoxLayout(parent=self,
                                             margins=(uic.WINSIDEPAD, uic.WINTOPPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                             spacing=uic.SVLRG)
        # Light Settings layout -----------------------------
        topLayout = elements.hBoxLayout(spacing=uic.SLRG, margins=(0, 0, 0, uic.SREG))
        topLayout.addWidget(self.presetCombo, 1)
        topLayout.addWidget(self.clippingCombo, 1)
        # Light Settings layout -----------------------------
        lightSettingsLayout = elements.hBoxLayout(spacing=uic.SLRG)
        lightSettingsLayout.addWidget(self.lightCountSlider, 1)
        lightSettingsLayout.addWidget(self.lightAngleSlider, 1)
        # Light Slider layout -----------------------------
        lightSliderLayout = elements.hBoxLayout(spacing=uic.SREG)
        lightSliderLayout.addWidget(self.lightCheckbox, 26)
        lightSliderLayout.addWidget(self.lightFloatSlider, 80)
        # HDRI Slider layout -----------------------------
        hdriSliderLayout = elements.hBoxLayout(spacing=uic.SREG)
        hdriSliderLayout.addWidget(self.hdriCheckbox, 26)
        hdriSliderLayout.addWidget(self.hdriFloatSlider, 80)
        # Viewport Light Trash layout -----------------------------
        vpButtonBottomLayout = elements.hBoxLayout(spacing=uic.SPACING, margins=(0, uic.SREG, 0, 0))
        vpButtonBottomLayout.addWidget(self.selectMasterCtrlBtn, 1)
        vpButtonBottomLayout.addWidget(self.selectDirectionalBtn, 1)
        vpButtonBottomLayout.addWidget(self.selectHdriBtn, 1)
        vpButtonBottomLayout.addWidget(self.createLightBtn, 9)
        vpButtonBottomLayout.addWidget(self.reloadViewportBtn, 1)
        vpButtonBottomLayout.addWidget(self.unlinkConstraintBtn, 1)
        vpButtonBottomLayout.addWidget(self.linkConstraintBtn, 1)
        vpButtonBottomLayout.addWidget(self.deleteVPLightBtn, 1)
        if MAYA_VERSION >= 2022:
            # View Grade map buttons x 2 -----------------------------
            viewButtonLayout = elements.hBoxLayout(spacing=uic.SPACING,
                                                   margins=(0, uic.SREG, 0, 0))
            viewButtonLayout.addWidget(self.renderSpaceLinearBtn, 1)
            viewButtonLayout.addWidget(self.renderSpaceAcesBtn, 1)
            # tone map buttons x 3 -----------------------------
            toneMapButtonLayout = elements.hBoxLayout(spacing=uic.SPACING,
                                                      margins=(0, 0, 0, uic.SREG))
            toneMapButtonLayout.addWidget(self.toneMapNoneBtn, 1)
            toneMapButtonLayout.addWidget(self.toneMapUnityBtn, 1)
            toneMapButtonLayout.addWidget(self.toneMapSDRVideoBtn, 1)

        # Grid Layout -----------------------------
        gridLayout = elements.GridLayout(spacing=uic.SPACING)
        row = 0
        gridLayout.addLayout(topLayout, row, 0, 1, 2)
        row += 1
        gridLayout.addWidget(self.exposureSlider, row, 0, 1, 2)
        row += 1
        gridLayout.addWidget(self.contrastSlider, row, 0, 1, 2)
        if MAYA_VERSION >= 2022:
            row += 1
            gridLayout.addLayout(viewButtonLayout, row, 0, 1, 2)
            row += 1
            gridLayout.addLayout(toneMapButtonLayout, row, 0, 1, 2)
        row += 1
        gridLayout.addWidget(elements.LabelDivider("Camera Viewport Light - Intensity"), row, 0, 1, 2)
        row += 1
        gridLayout.addLayout(lightSliderLayout, row, 0, 1, 2)
        row += 1
        gridLayout.addLayout(hdriSliderLayout, row, 0, 1, 2)
        row += 1
        gridLayout.addLayout(vpButtonBottomLayout, row, 0, 1, 2)

        gridLayout.setColumnStretch(0, 1)
        gridLayout.setColumnStretch(1, 1)
        # Add To Main Layout ---------------------------------------
        contentsLayout.addLayout(gridLayout)


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
        contentsLayout = elements.vBoxLayout(parent=self,
                                             margins=(uic.WINSIDEPAD, uic.WINTOPPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                             spacing=uic.SVLRG)
        # Light Settings layout -----------------------------
        topLayout = elements.hBoxLayout(spacing=uic.SLRG, margins=(0, 0, 0, uic.SREG))
        topLayout.addWidget(self.presetCombo, 1)
        topLayout.addWidget(self.autoLightCheckbox, 1)
        # Checkbox Layout --------------------------------
        checkboxLayout = elements.hBoxLayout(spacing=uic.SLRG, margins=(uic.SREG, 0, uic.SREG, uic.SREG))
        checkboxLayout.addWidget(self.lightsCheckbox, 1)
        checkboxLayout.addWidget(self.shadowsCheckbox, 1)
        checkboxLayout.addWidget(self.aoCheckbox, 1)
        checkboxLayout.addWidget(self.antiAliasCheckbox, 1)
        checkboxLayout.addWidget(self.aaSamplesCombo, 1)
        # Cam Viewport Light Title Layout --------------------------------
        rendererComboLayout = elements.hBoxLayout(spacing=uic.SREG, margins=(0, 0, 0, 0))
        rendererComboLayout.addWidget(self.rendererCombo, 1)
        rendererComboLayout.addWidget(self.multiplierCombo, 1)
        # Texture Settings layout -----------------------------
        textureSettingsLayout = elements.hBoxLayout(spacing=uic.SLRG, margins=(uic.SREG, 0, uic.SREG, uic.SREG))
        textureSettingsLayout.addWidget(self.gridCheckbox, 1)
        textureSettingsLayout.addWidget(self.texturesCheckbox, 1)
        textureSettingsLayout.addWidget(self.udimBtn, 2)
        # Light Settings layout -----------------------------
        lightSettingsLayout = elements.hBoxLayout(spacing=uic.SLRG)
        lightSettingsLayout.addWidget(self.lightCountSlider, 1)
        lightSettingsLayout.addWidget(self.lightAngleSlider, 1)
        # Max Lights Clip Layout  -----------------------------
        clipLayout = elements.hBoxLayout(spacing=uic.SLRG, margins=(0, uic.SLRG, 0, 0))
        clipLayout.addWidget(self.maxLightsCombo, 1)
        clipLayout.addWidget(self.clippingCombo, 1)
        # Light Slider layout -----------------------------
        lightSliderLayout = elements.hBoxLayout(spacing=uic.SREG)
        lightSliderLayout.addWidget(self.lightCheckbox, 26)
        lightSliderLayout.addWidget(self.lightFloatSlider, 80)
        # HDRI Slider layout -----------------------------
        hdriSliderLayout = elements.hBoxLayout(spacing=uic.SREG)
        hdriSliderLayout.addWidget(self.hdriCheckbox, 26)
        hdriSliderLayout.addWidget(self.hdriFloatSlider, 80)
        # Light Settings 2 layout -----------------------------
        specSliderLayout = elements.hBoxLayout(spacing=uic.SREG)
        specSliderLayout.addWidget(self.specularCheckbox, 26)
        specSliderLayout.addWidget(self.specularSlider, 80)
        # Top Combo Layout ---------------------------------------
        nameLayout = elements.hBoxLayout(spacing=uic.SREG)
        nameLayout.addWidget(self.nameTxt, 9)
        nameLayout.addWidget(self.getCameraBtn, 1)
        # Viewport Light Trash layout -----------------------------
        vpButtonBottomLayout = elements.hBoxLayout(spacing=uic.SPACING, margins=(0, uic.SREG, 0, 0))
        vpButtonBottomLayout.addWidget(self.selectMasterCtrlBtn, 1)
        vpButtonBottomLayout.addWidget(self.selectDirectionalBtn, 1)
        vpButtonBottomLayout.addWidget(self.selectHdriBtn, 1)
        vpButtonBottomLayout.addWidget(self.createLightBtn, 9)
        vpButtonBottomLayout.addWidget(self.reloadViewportBtn, 1)
        vpButtonBottomLayout.addWidget(self.unlinkConstraintBtn, 1)
        vpButtonBottomLayout.addWidget(self.linkConstraintBtn, 1)
        vpButtonBottomLayout.addWidget(self.deleteVPLightBtn, 1)
        if MAYA_VERSION >= 2022:
            # tone map buttons x 3 -----------------------------
            toneMapButtonLayout = elements.hBoxLayout(spacing=uic.SPACING,
                                                      margins=(0, 0, 0, uic.SLRG))
            toneMapButtonLayout.addWidget(self.toneMapNoneBtn, 1)
            toneMapButtonLayout.addWidget(self.toneMapUnityBtn, 1)
            toneMapButtonLayout.addWidget(self.toneMapSDRVideoBtn, 1)

        # Grid Layout -----------------------------
        gridLayout = elements.GridLayout(spacing=uic.SPACING)
        row = 0
        gridLayout.addLayout(topLayout, row, 0, 1, 2)
        row += 1
        gridLayout.addLayout(textureSettingsLayout, row, 0, 1, 2)
        row += 1
        gridLayout.addWidget(self.bgColorSlider, row, 0, 1, 2)
        row += 1
        gridLayout.addWidget(elements.LabelDivider("Viewport 2.0 Settings"), row, 0, 1, 2)
        row += 1
        gridLayout.addLayout(checkboxLayout, row, 0, 1, 2)
        row += 1
        gridLayout.addWidget(self.exposureSlider, row, 0, 1, 2)
        row += 1
        gridLayout.addWidget(self.contrastSlider, row, 0, 1, 2)
        row += 1
        gridLayout.addLayout(clipLayout, row, 0, 1, 2)
        if MAYA_VERSION >= 2022:
            row += 1
            gridLayout.addWidget(elements.LabelDivider("Rendering & View Space 2022+",
                                                       margins=[0, uic.SLRG, 0, uic.SSML]),
                                 row, 0, 1, 2)
            row += 1
            gridLayout.addWidget(self.renderSpaceLinearBtn, row, 0)
            gridLayout.addWidget(self.renderSpaceAcesBtn, row, 1)
            row += 1
            gridLayout.addLayout(toneMapButtonLayout, row, 0, 1, 2)
        row += 1
        gridLayout.addWidget(elements.LabelDivider("Camera Viewport Light - Intensity"), row, 0, 1, 2)
        row += 1
        gridLayout.addLayout(rendererComboLayout, row, 0, 1, 2)
        row += 1
        gridLayout.addLayout(lightSliderLayout, row, 0, 1, 2)
        row += 1
        gridLayout.addLayout(hdriSliderLayout, row, 0, 1, 2)
        row += 1
        gridLayout.addLayout(specSliderLayout, row, 0, 1, 2)
        row += 1
        gridLayout.addWidget(elements.LabelDivider("Camera Viewport Light - Settings"), row, 0, 1, 2)
        row += 1
        gridLayout.addWidget(self.lightCountSlider, row, 0, 1, 2)
        row += 1
        gridLayout.addWidget(self.lightAngleSlider, row, 0, 1, 2)
        row += 1
        gridLayout.addWidget(self.dMapResSlider, row, 0, 1, 2)
        row += 1
        gridLayout.addWidget(self.shadowColorSlider, row, 0, 1, 2)
        row += 1
        gridLayout.addLayout(nameLayout, row, 0, 1, 2)
        row += 1
        gridLayout.addLayout(vpButtonBottomLayout, row, 0, 1, 2)

        gridLayout.setColumnStretch(0, 1)
        gridLayout.setColumnStretch(1, 1)
        # Add To Main Layout ---------------------------------------
        contentsLayout.addLayout(gridLayout)
