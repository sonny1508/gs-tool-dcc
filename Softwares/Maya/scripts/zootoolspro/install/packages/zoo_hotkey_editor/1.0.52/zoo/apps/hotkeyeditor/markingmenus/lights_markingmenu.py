import maya.mel as mel
import maya.cmds as cmds

from zoo.libs.maya.markingmenu import menu
from zoo.libs.maya.cmds.lighting import lightsmultihdri, lightingutils, lightsmultiarea, lightconstants, \
    lightsmultidirectional
from zoo.libs.maya.cmds.renderer import multirenderersettings, rendererload
from zoo.libs.maya.cmds.meta import metaviewportlight
from zoo.libs.maya.cmds.assets import defaultassets
from zoo.libs.maya.cmds.hotkeys import definedhotkeys
from zoo.apps.toolsetsui.run import openToolset

from zoo.preferences.interfaces import coreinterfaces
from zoo.libs.pyqt.widgets import elements

LIGHT_TRACKER_INST = lightingutils.ZooLightsTrackerSingleton()  # tracks LIGHT_TRACKER_INST.lightCreateOption (bool)


def checkRendererLoaded(renderer=""):
    """Checks if the given renderer is loaded, if so returns True, if not opens a popup window.

    Cancel returns False.

    :param renderer: The nice name of the renderer eg "Arnold"
    :type renderer: str
    :return loaded: Is the renderer loaded or not?
    :rtype loaded: bool
    """
    if not renderer:
        renderer = coreinterfaces.generalInterface().primaryRenderer()
    if not rendererload.getRendererIsLoaded(renderer):  # the renderer is not loaded open window
        if not elements.checkRenderLoaded(renderer):
            return False
    return True


def openLightEditor():
    """Opens Maya's Light Editor"""
    import zoo.libs.maya.cmds.hotkeys.definedhotkeys as hk
    hk.open_mayLightEditor()


class lightsMarkingMenuCommand(menu.MarkingMenuCommand):
    """Command class for the Light Marking Menu

    Commands are related to the file (JSON) in the same directory:

    .. code-block:: python

        lights.mmlayout

    Zoo paths must point to this directory, usually on zoo startup inside the repo root package.json file.

    Example add to package.json:

    .. code-block:: python

        "ZOO_MM_COMMAND_PATH": "{self}/zoo/libs/maya/cmds/hotkeys",
        "ZOO_MM_MENU_PATH": "{self}/zoo/libs/maya/cmds/hotkeys",
        "ZOO_MM_LAYOUT_PATH": "{self}/zoo/libs/maya/cmds/hotkeys",

    Or if not on startup, run in the script editor, with your path:

    .. code-block:: python

        os.environ["ZOO_MM_COMMAND_PATH"] = r"D:\repos\zootools_pro\zoocore_pro\zoo\libs\maya\cmds\hotkeys"
        os.environ["ZOO_MM_MENU_PATH"] = r"D:\repos\zootools_pro\zoocore_pro\zoo\libs\maya\cmds\hotkeys"
        os.environ["ZOO_MM_LAYOUT_PATH"] = r"D:\repos\zootools_pro\zoocore_pro\zoo\libs\maya\cmds\hotkeys"

    Map the following code to a hotkey press. Note: Change the key modifiers if using shift alt ctrl etc:

    .. code-block:: python

        import maya.mel as mel
        from zoo.libs.maya.markingmenu import menu as zooMenu
        zooMenu.MarkingMenu.buildFromLayout("markingMenu.lights",
                                            "lightsMarkingMenu",
                                            parent=mel.eval("findPanelPopupParent"),
                                            options={"altModifier": False,
                                                     "shiftModifier": False})

    Map to hotkey release:

    .. code-block:: python

        from zoo.libs.maya.markingmenu import menu as zooMenu
        zooMenu.MarkingMenu.removeExistingMenu("lightsMarkingMenu")

    """
    id = "lightsMarkingMenu"  # a unique identifier for a class, should never be changed
    creator = "ZooTools"

    def createHdri(self):
        if not checkRendererLoaded():
            return
        renderer = coreinterfaces.generalInterface().primaryRenderer()
        if renderer == lightconstants.MAYA:  # Maya uses the Arnold Skydome Light type
            if not checkRendererLoaded(renderer="Arnold"):
                return
        lightInst = lightsmultihdri.createDefaultHdriAutoRenderer(imagePath=lightconstants.DEFAULT_SKYDOME_PATH,
                                                                  suffixName=True)
        lightInst.setIntensityAndMultiply(1.0, lightconstants.PRESET_CITYPLATZ["intMult"])
        lightInst.setRotateAndOffset([0.0, 0.0, 0.0], lightconstants.PRESET_CITYPLATZ["rotOffset"])

    def createArea(self, position):
        if not checkRendererLoaded():
            return
        lightsmultiarea.createDefaultAreaAutoRenderer(suffixName=True, genAttrDict=None, position=position)

    def createDirectional(self, position):
        if not checkRendererLoaded():
            return
        lightsmultidirectional.createDefaultDirectionalRendererAuto(suffixName=True, position=position)

    @staticmethod
    def uiData(arguments):
        """This method uses the json file for layout but is used for dynamic display of marking menu elements"""
        ret = {"icon": "",
               "label": "",
               "bold": False,
               "italic": False,
               "optionBox": False,
               "optionBoxIcon": ""
               }
        currRenderer = multirenderersettings.currentRenderer()

        if arguments['operation'] == 'currentRenderer':
            label = "{} Renderer".format(currRenderer)
            if currRenderer == 'Arnold':
                ret = {"icon": "arnold",
                       "label": label,
                       "bold": True
                       }
            elif currRenderer == 'Redshift':
                ret = {"icon": "redshift",
                       "label": ("{} Renderer".format(currRenderer)),
                       "bold": True
                       }
            elif currRenderer == 'VRay':
                ret = {"icon": "vray",
                       "label": label,
                       "bold": True
                       }
            elif currRenderer == 'Renderman':
                ret = {"icon": "renderman",
                       "label": label,
                       "bold": True
                       }
            elif currRenderer == 'Maya':
                ret = {"icon": "maya",
                       "label": label.replace("Renderer", "Viewport"),
                       "bold": True
                       }

        elif arguments['operation'] == 'createLightsFromCamera':

            if LIGHT_TRACKER_INST.lightCreateOption:
                ret['checkBox'] = True
            else:
                ret['checkBox'] = False

        elif arguments['operation'] == 'fixViewport':
            if metaviewportlight.sceneMetaNodes():
                ret['show'] = False
        elif arguments['operation'] == 'deleteFixViewport':
            if not metaviewportlight.sceneMetaNodes():
                ret['show'] = False
        elif arguments['operation'] == 'switchViewportCam':
            if not metaviewportlight.sceneMetaNodes():
                ret['show'] = False

        elif arguments['operation'].startswith('preset'):
            if currRenderer == 'Maya' or currRenderer == 'VRay':
                ret['show'] = False

        elif arguments['operation'] == 'switchToArnold':
            if currRenderer == 'Arnold':
                ret['show'] = False
        elif arguments['operation'] == 'switchToRedshift':
            if currRenderer == 'Redshift':
                ret['show'] = False
        elif arguments['operation'] == 'switchToVray':
            if currRenderer == 'VRay':
                ret['show'] = False
        elif arguments['operation'] == 'switchToRenderman':
            if currRenderer == 'Renderman':
                ret['show'] = False
        elif arguments['operation'] == 'switchToMayaViewport':
            if currRenderer == 'Maya':
                ret['show'] = False

        return ret

    def execute(self, arguments):
        """The main execute methods for the light marking menu. see executeUI() for option box commands

        :type arguments: dict
        """
        operation = arguments.get("operation", "")

        if LIGHT_TRACKER_INST.lightCreateOption:
            position = "camera"
        else:
            position = "selected"

        # Top NSEW Dial Items ----------------
        if operation == "areaLight":
            self.createArea(position)
        elif operation == "directionalLight":
            self.createDirectional(position)
        elif operation == "hdriSkydome":
            self.createHdri()
        elif operation == "lightEditorWindow":
            openLightEditor()
        elif operation == "zooEditLights":
            definedhotkeys.open_editLights(advancedMode=False)
        elif operation == "mayaLightEditor":
            mel.eval("lightLinkingEditor;")
        elif operation == "breakLightLinks":
            cmds.lightlink(b=True, useActiveLights=True, useActiveObjects=True)
        elif operation == "makeLightLinks":
            cmds.lightlink(make=True, useActiveLights=True, useActiveObjects=True)

        # Place Lights ----------------
        elif operation == "placeReflection":
            lightingutils.placeReflection()

        elif operation == "createLightsFromCamera":
            # os.environ["ZOO_LIGHT_CREATEOPTION"] = str(int(not int(os.environ["ZOO_LIGHT_CREATEOPTION"])))
            LIGHT_TRACKER_INST.lightCreateOption = not LIGHT_TRACKER_INST.lightCreateOption  # reverse tracker bool

        # Fix Viewport Light rig ----------------
        elif arguments['operation'] == 'fixViewport':
            if checkRendererLoaded("Arnold"):
                metaviewportlight.createViewportLightAuto()
        elif arguments['operation'] == 'deleteFixViewport':
            metaviewportlight.deleteViewportLights()
        elif arguments['operation'] == 'switchViewportCam':
            metaviewportlight.switchCamViewportLightsAuto()
        elif arguments['operation'] == 'lightPresets':
            definedhotkeys.open_lightPresets(advancedMode=False)

        # Light Presets ----------------
        elif operation.startswith("preset"):
            if not checkRendererLoaded():
                return
            if operation == 'presetDefault':
                presetDict = defaultassets.PRESET_DEFAULT  # internal preset dicts, not light preset dict
            elif operation == 'presetThreePoint':
                presetDict = defaultassets.PRESET_THREEPOINT
            elif operation == 'presetThreePointDrk':
                presetDict = defaultassets.PRESET_THREEPOINTDRK
            elif operation == 'presetSoftTop':
                presetDict = defaultassets.PRESET_SOFTTOP
            elif operation == 'presetRedAqua':
                presetDict = defaultassets.PRESET_REDAQUA
            elif operation == 'presetFactoryColor':
                presetDict = defaultassets.PRESET_FACTORYCOLOR
            elif operation == 'presetFactoryGrey':
                presetDict = defaultassets.PRESET_FACTORYGREY
            else:  # operation == 'presetWinter'
                presetDict = defaultassets.PRESET_WINTER
            defaultassets.importLightPresetAutoRenderer(internalLightDict=presetDict, showIbl=False, message=True)

        # Renderers ----------------
        elif operation == "switchToArnold":
            multirenderersettings.changeRenderer("Arnold")
        elif operation == "switchToRedshift":
            multirenderersettings.changeRenderer("Redshift")
        elif operation == "switchToVray":
            multirenderersettings.changeRenderer("VRay")
        elif operation == "switchToRenderman":
            multirenderersettings.changeRenderer("Renderman")
        elif operation == "switchToMayaViewport":
            multirenderersettings.changeRenderer("Maya")

    def executeUI(self, arguments):
        """The option box execute methods for the lights marking menu. see execute() for main commands

        For this method to be called "optionBox": True.

        :type arguments: dict
        """
        operation = arguments.get("operation", "")
        if operation == "areaLight":
            openToolset("areaLights", advancedMode=False)
        elif operation == "directionalLight":
            openToolset("directionalLights", advancedMode=False)
        elif operation == "hdriSkydome":
            openToolset("hdriSkydomeLights", advancedMode=False)
        elif operation == "placeReflection":
            definedhotkeys.open_placeReflection(advancedMode=False)
        elif operation == "fixViewport":
            definedhotkeys.open_fixViewport(advancedMode=False)
        elif operation.startswith('preset'):
            definedhotkeys.open_lightPresets(advancedMode=False)
