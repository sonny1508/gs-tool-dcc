import maya.mel as mel

from zoo.libs.maya.markingmenu import menu
from zoo.libs.maya.cmds.renderer import multirenderersettings, rendererload
from zoo.libs.maya.cmds.hotkeys import definedhotkeys
from zoo.libs.maya.cmds.shaders import shaderutils, shadermulti, shdmultconstants as sc

from zoo.preferences.interfaces import coreinterfaces
from zoo.libs.pyqt.widgets import elements


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


class ShadersMarkingMenuCommand(menu.MarkingMenuCommand):
    """Command class for the Shaders Marking Menu

    Commands are related to the file (JSON) in the same directory:

    .. code-block:: python

        shaders.mmlayout

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
        zooMenu.MarkingMenu.buildFromLayout("markingMenu.shaders",
                                            "shadersMarkingMenu",
                                            parent=mel.eval("findPanelPopupParent"),
                                            options={"altModifier": False,
                                                     "shiftModifier": False})

    Map to hotkey release:

    .. code-block:: python

        from zoo.libs.maya.markingmenu import menu as zooMenu
        zooMenu.MarkingMenu.removeExistingMenu("shadersMarkingMenu")

    """
    id = "shadersMarkingMenu"  # a unique identifier for a class, should never be changed
    creator = "ZooTools"

    def createShader(self):
        currentRenderer = multirenderersettings.currentRenderer()
        if not checkRendererLoaded():
            return
        shadermulti.createDefaultShadRenderer(currentRenderer,
                                              shaderName="shader_01",
                                              suffixName=True,
                                              assignGeo=True,
                                              message=False)

    @staticmethod
    def uiData(arguments):
        """This method is mostly over-ridden by the associated json file"""
        ret = {"icon": "",
               "label": "",
               "bold": False,
               "italic": False,
               "optionBox": False,
               "optionBoxIcon": ""
               }
        currentRenderer = multirenderersettings.currentRenderer()

        if arguments['operation'] == 'currentRenderer':
            if currentRenderer == sc.MAYA:
                label = "Maya Viewport"
            else:
                label = "{} Renderer".format(currentRenderer)
            ret = {"icon": sc.RENDERER_ICONS_DICT[currentRenderer],
                   "label": label,
                   "bold": True
                   }
            return ret

        if arguments['operation'] == 'switchToArnold':
            if currentRenderer == sc.ARNOLD:
                ret['show'] = False
        if arguments['operation'] == 'switchToRedshift':
            if currentRenderer == sc.REDSHIFT:
                ret['show'] = False
        if arguments['operation'] == 'switchToVray':
            if currentRenderer == sc.VRAY:
                ret['show'] = False
        if arguments['operation'] == 'switchToRenderman':
            if currentRenderer == sc.RENDERMAN:
                ret['show'] = False
        if arguments['operation'] == 'switchToMayaViewport':
            if currentRenderer == sc.MAYA:
                ret['show'] = False
        return ret

    def execute(self, arguments):
        """The main execute methods for the shaders marking menu. see executeUI() for option box commands

        :type arguments: dict
        """
        operation = arguments.get("operation", "")

        if operation == "createShader":
            self.createShader()
        elif operation == "copyShader":
            shadermulti.copyShaderSelected()
        elif operation == "pasteShader":
            shadermulti.pasteShaderSelected()
        elif operation == "pasteShaderAttributes":
            shadermulti.pasteShaderAttrsSelected()
        elif operation == "shaderManager":
            definedhotkeys.open_shaderManager(advancedMode=False)
        elif operation == "selectShaderNode":
            shaderutils.selectNodeOrShaderAttrEditor()
        elif operation == "selectObjectShader":
            shaderutils.selectMeshFaceFromShaderSelection()
        elif operation == "transferShader":
            shaderutils.transferAssignSelection(message=True)
        elif operation == "hypershade":
            shaderutils.transferAssignSelection(message=True)
            mel.eval('tearOffRestorePanel "Hypershade" "hyperShadePanel" true;')
        elif operation == "shaderPresetsMultiRenderer":
            definedhotkeys.open_shaderPresetsMultRenderer(advancedMode=False)
        elif operation == "shaderPresetsMa":
            definedhotkeys.open_shaderPresetsMa(advancedMode=False)
        elif operation == "diffuseHsv":
            from zoo.apps.popupuis import hsvpopup
            hsvpopup.main()

        # Shader Preset Overrides ----------------
        elif operation.startswith("preset"):
            if operation == 'presetPlain':
                presetDict = sc.PRESET_PLAIN  # override preset dicts, not light preset dict
            elif operation == 'presetCloth':
                presetDict = sc.PRESET_CLOTH_ROUGH
            elif operation == 'presetPlasticShine':
                presetDict = sc.PRESET_PLASTIC_SHINE
            elif operation == 'presetPlasticRough':
                presetDict = sc.PRESET_PLASTIC_ROUGH
            elif operation == 'presetMetalShine':
                presetDict = sc.PRESET_METAL_SHINE
            elif operation == 'presetMetalRough':
                presetDict = sc.PRESET_METAL_ROUGH
            elif operation == 'presetMetalRough':
                presetDict = sc.PRESET_METAL_ROUGH
            else:  # operation == 'presetCarPaint':
                presetDict = sc.PRESET_CAR_PAINT
            shadermulti.assignValuesSelected(presetDict, message=True)
            return

        elif operation == "switchToArnold":
            multirenderersettings.changeRenderer(sc.ARNOLD)
        elif operation == "switchToRedshift":
            multirenderersettings.changeRenderer(sc.REDSHIFT)
        elif operation == "switchToVray":
            multirenderersettings.changeRenderer(sc.VRAY)
        elif operation == "switchToRenderman":
            multirenderersettings.changeRenderer(sc.RENDERMAN)
        elif operation == "switchToMayaViewport":
            multirenderersettings.changeRenderer(sc.MAYA)
        elif operation == "convertShaders":
            definedhotkeys.open_convertShaders(advancedMode=False)

    def executeUI(self, arguments):
        """The option box execute methods for the shaders marking menu. see execute() for main commands

        For this method to be called "optionBox": True.

        :type arguments: dict
        """
        operation = arguments.get("operation", "")
        if operation == "createShader":
            definedhotkeys.open_shaderManager(advancedMode=False)
        elif operation == "diffuseHsv":
            definedhotkeys.open_hsvOffset()
        return
