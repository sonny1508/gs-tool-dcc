import maya.mel as mel

from zoo.libs.maya.markingmenu import menu
from zoo.apps.toolsetsui import run
from zoo.libs.maya.cmds.hotkeys import definedhotkeys


class DeformersMarkingMenuCommand(menu.MarkingMenuCommand):
    """Command class for the deformers marking menu.

    Commands are related to the file (JSON) in the same directory:

    .. code-block:: python

        deformers.mmlayout

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
        zooMenu.MarkingMenu.buildFromLayout("markingMenu.deformers",
                                            "markingMenuDeformers",
                                            parent=mel.eval("findPanelPopupParent"),
                                            options={"altModifier": False,
                                                     "shiftModifier": True})

    Map to hotkey release:

    .. code-block:: python

        from zoo.libs.maya.markingmenu import menu as zooMenu
        zooMenu.MarkingMenu.removeExistingMenu("markingMenuDeformers")

    """
    id = "deformersMarkingMenu"  # a unique identifier for a class, should never be changed
    creator = "Zootools"

    @staticmethod
    def uiData(arguments):
        """This method is mostly over ridden by the associated json file"""
        return {"icon": "",
                "label": "",
                "bold": False,
                "italic": False,
                "optionBox": False,
                "optionBoxIcon": ""
                }

    def execute(self, arguments):
        """The main execute methods for the deformers marking menu. see executeUI() for option box commands

        :type arguments: dict
        """
        operation = arguments.get("operation", "")
        if operation == "blendshapeEditor":
            mel.eval("ShapeEditor;")
        elif operation == "wire":
            mel.eval("setToolTo wireCtx")
        elif operation == "blendshapeCreate":
            mel.eval("performBlendShape 0 1;")
        elif operation == "addBlendshape":
            mel.eval("performBlendShapeAdd 0")
        elif operation == "clusterCreate":
            mel.eval("performCluster 0")
        elif operation == "controlsOnCurve":
            run.openToolset("controlsOnCurve")
        elif operation == "latticeCreate":
            definedhotkeys.createLatticeMel()
        elif operation == "softMod":
            mel.eval("setToolTo ShowManips; performSoftMod 0 0 0 {0.0, 0.0, 0.0}")
        elif operation == "bend":
            definedhotkeys.createBendDeformerMel()
        elif operation == "wrapCreate":
            mel.eval("performCreateWrap 0")
        elif operation == "sculptDeformerCreate":
            mel.eval("performSculpt 0")
        elif operation == "twist":
            definedhotkeys.createTwistDeformerMel()
        elif operation == "wave":
            definedhotkeys.createWaveDeformerMel()
        elif operation == "flare":
            definedhotkeys.createFlareDeformerMel()
        elif operation == "jiggle":
            mel.eval("performJiggle 0")

    def executeUI(self, arguments):
        """The option box execute methods for the deformers marking menu. see execute() for main commands

        For this method to be called "optionBox": True.

        :type arguments: dict
        """
        operation = arguments.get("operation", "")
        if operation == "wire":
            mel.eval("setToolTo wireCtx; toolPropertyWindow")
        elif operation == "blendshapeCreate":
            mel.eval("performBlendShape 1 1;")
        elif operation == "addBlendshape":
            mel.eval("performBlendShapeAdd 1")
        elif operation == "clusterCreate":
            mel.eval("performCluster 1")
        elif operation == "latticeCreate":
            definedhotkeys.createLatticeMelOptions()
        elif operation == "softMod":
            mel.eval("performSoftMod 1 0 0 {0.0, 0.0, 0.0}")
        elif operation == "bend":
            definedhotkeys.createBendDeformerMelOptions()
        elif operation == "wrapCreate":
            mel.eval("performCreateWrap 1")
        elif operation == "sculptDeformerCreate":
            mel.eval("performSculpt 1")
        elif operation == "twist":
            definedhotkeys.createTwistDeformerMelOptions()
        elif operation == "wave":
            definedhotkeys.createWaveDeformerMelOptions()
        elif operation == "flare":
            definedhotkeys.createFlareDeformerMelOptions()
        elif operation == "jiggle":
            mel.eval("performJiggle 1")
