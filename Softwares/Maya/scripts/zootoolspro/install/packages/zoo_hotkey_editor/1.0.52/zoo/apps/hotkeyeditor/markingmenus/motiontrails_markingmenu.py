"""Motion trail marking menu.

Hotkey found at zoo.libs.maya.cmds.hotkeys.definedhotkeys.py

Map to press:

.. code-block:: python

    from zoo.libs.maya.cmds.hotkeys import definedhotkeys
    definedhotkeys.motionTrailMarkingMenuPress()

Map to release:

.. code-block:: python

    from zoo.libs.maya.cmds.hotkeys import definedhotkeys
    definedhotkeys.motionTrailMarkingMenuRelease()


Authors: Cosmo Park & Andrew Silke
"""

from zoo.libs.maya.markingmenu import menu
from zoo.libs.maya.cmds.animation import motiontrail

MT_TRACKER_INST = motiontrail.ZooMotionTrailTrackerSingleton()


def secondaryFunction():
    """When the marking menu is released, run for a secondary feature

    Search for `MT_TRACKER_INST.markingMenuTriggered = True ` to see where the trigger is set to be True
    """
    MT_TRACKER_INST.markingMenuMoShapes = None
    if MT_TRACKER_INST.markingMenuTriggered:  # Ignore if the menu was triggered
        MT_TRACKER_INST.markingMenuTriggered = False
        return
    motiontrail.createMotionTrailSelBools(MT_TRACKER_INST.keyDots_bool,
                                          MT_TRACKER_INST.crosses_bool,
                                          MT_TRACKER_INST.frameSize_bool,
                                          MT_TRACKER_INST.pastFuture_bool,
                                          MT_TRACKER_INST.frameNumbers_bool,
                                          MT_TRACKER_INST.limitBeforeAfter_bool)


class MotionTrailsMarkingMenuCommand(menu.MarkingMenuCommand):
    """Command class for the Motion Paths Marking Menu

    Commands are related to the file (JSON) in the same directory:

    .. code-block:: python

        motionTrails.mmlayout

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
        zooMenu.MarkingMenu.buildFromLayout("markingMenu.motionTrails",
                                            "motionTrailsMarkingMenu",
                                            parent=mel.eval("findPanelPopupParent"),
                                            options={"altModifier": False,
                                                     "shiftModifier": False})

    Map to hotkey release:

    .. code-block:: python

        from zoo.libs.maya.markingmenu import menu as zooMenu
        zooMenu.MarkingMenu.removeExistingMenu("motionTrailsMarkingMenu")

    """
    id = "motionTrailsMarkingMenu"  # a unique identifier for a class, should never be changed
    creator = "ZooTools"

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
        # Returns all moTrail shapes in selection or scene. Only does it once per marking menu.
        if MT_TRACKER_INST.markingMenuMoShapes is None:
            moTShapes = motiontrail.moTrailShapes(scene=True, selected=True)
            MT_TRACKER_INST.markingMenuMoShapes = moTShapes
        else:
            moTShapes = MT_TRACKER_INST.markingMenuMoShapes

        # Set checkboxes ------------------------
        if arguments['operation'] == 'pastFutureAlternating':
            MT_TRACKER_INST.markingMenuTriggered = True
            ret['checkBox'] = motiontrail.pastFutureToggleValue(moTShapes)
        elif arguments['operation'] == 'visibility':
            ret['checkBox'] = motiontrail.visibilityToggleValue(moTShapes)
        elif arguments['operation'] == 'frameCrosses':
            ret['checkBox'] = motiontrail.frameCrossesToggleValue(moTShapes)
        elif arguments['operation'] == 'keyframeSize':
            ret['checkBox'] = motiontrail.frameSizeToggleValue(moTShapes)
        elif arguments['operation'] == 'keyframeDots':
            ret['checkBox'] = motiontrail.keyDotsVisibility(moTShapes)
        elif arguments['operation'] == 'showFrameNumbers':
            ret['checkBox'] = motiontrail.frameNumbersToggleValue(moTShapes)
        elif arguments['operation'] == 'limitBeforeAfter':
            ret['checkBox'] = motiontrail.limitBeforeAfterToggleValue(moTShapes)

        return ret

    def execute(self, arguments):
        """The main execute methods for the motion trail marking menu. see executeUI() for option box commands

        :type arguments: dict
        """
        operation = arguments.get("operation", "")

        if operation == "createMotionTrails":
            motiontrail.createMotionTrailSelBools(MT_TRACKER_INST.keyDots_bool,
                                                  MT_TRACKER_INST.crosses_bool,
                                                  MT_TRACKER_INST.frameSize_bool,
                                                  MT_TRACKER_INST.pastFuture_bool,
                                                  MT_TRACKER_INST.frameNumbers_bool,
                                                  MT_TRACKER_INST.limitBeforeAfter_bool,
                                                  limitFrames=MT_TRACKER_INST.limitAmount)
        elif operation == "deleteAllMotionTrails":
            motiontrail.deleteMotionTrails(scene=True, selected=False)
        elif operation == "selectAll":
            motiontrail.selectMotionTrails()
        elif operation == "resetDisplayDefaults":
            motiontrail.resetMoTrialDefaultDisplay(scene=True, selected=True)
            MT_TRACKER_INST.resetDisplayDefaults()
        elif operation == "pastFutureAlternating":
            tglState = motiontrail.toggleDisplaySetting("trailDrawMode", valueOne=2, valueTwo=1)
            if tglState is not None:
                MT_TRACKER_INST.pastFuture_bool = tglState
        elif operation == "visibility":
            motiontrail.toggleDisplaySetting("visibility", transform=True)
        elif operation == "frameCrosses":
            tglState = motiontrail.toggleDisplaySetting("showFrameMarkers")
            if tglState is not None:
                MT_TRACKER_INST.crosses_bool = tglState
        elif operation == "keyframeSize":
            tglState = motiontrail.toggleDisplaySetting("frameMarkerSize", valueOne=3.0, valueTwo=0.1)
            if tglState is not None:
                MT_TRACKER_INST.frameSize_bool = tglState
            motiontrail.setKeyDotsSize(MT_TRACKER_INST.markingMenuMoShapes, tglState)
        elif operation == "keyframeDots":
            vis = motiontrail.keyDotsVisibility(MT_TRACKER_INST.markingMenuMoShapes)
            motiontrail.setKeyDotsVis(MT_TRACKER_INST.markingMenuMoShapes, not vis)
            if vis is not None:
                MT_TRACKER_INST.keyDots_bool = not vis
        elif operation == "showFrameNumbers":
            tglState = motiontrail.toggleDisplaySetting("showFrames")
            if tglState is not None:
                MT_TRACKER_INST.frameNumbers_bool = tglState
        elif operation == "limitBeforeAfter":
            currentVal = motiontrail.limitBeforeAfterToggleValue(MT_TRACKER_INST.markingMenuMoShapes)
            motiontrail.setLimitBeforeAfterBool(MT_TRACKER_INST.markingMenuMoShapes, not currentVal,
                                                framesOut=MT_TRACKER_INST.limitAmount,
                                                framesIn=MT_TRACKER_INST.limitAmount)
            MT_TRACKER_INST.limitBeforeAfter_bool = not currentVal
        elif operation == "openOptionsWindow":
            from zoo.apps.toolsetsui.run import openToolset
            openToolset("animationPaths", advancedMode=False)

    def executeUI(self, arguments):
        """The option box execute methods for the motion paths marking menu. see execute() for main commands

        For this method to be called "optionBox": True.

        :type arguments: dict
        """
        operation = arguments.get("operation", "")
        if operation == "resetDisplayDefaults" or operation == "createMotionTrails" or operation == "limitBeforeAfter":
            from zoo.apps.toolsetsui.run import openToolset
            openToolset("animationPaths", advancedMode=False)
