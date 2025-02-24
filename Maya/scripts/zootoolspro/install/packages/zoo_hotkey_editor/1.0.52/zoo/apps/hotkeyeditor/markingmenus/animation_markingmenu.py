"""Animation marking menu.

Hotkey found at zoo.libs.maya.cmds.hotkeys.definedhotkeys.py

Map to press:

.. code-block:: python

    from zoo.libs.maya.cmds.hotkeys import definedhotkeys
    definedhotkeys.animationMarkingMenuPress()

Map to release:

.. code-block:: python

    from zoo.libs.maya.cmds.hotkeys import definedhotkeys
    definedhotkeys.animationMarkingMenuRelease()


Authors: Cosmo Park & Andrew Silke
"""

from zoo.libs.maya.markingmenu import menu
from zoo.libs.maya.cmds.animation import generalanimation
from zoo.libs.maya.cmds.hotkeys import definedhotkeys
from zoo.apps.toolsetsui.run import openToolset
import maya.cmds as cmds
from zoo.libs.maya.cmds.animation import bakeanim
from zoo.libs.maya.cmds.animation import timerange
from zoo.libs.maya.cmds.animation import motiontrail
from zoo.libs.utils import output


MT_TRACKER_INST = motiontrail.ZooMotionTrailTrackerSingleton()
ANIM_TRACKER_INST = generalanimation.ZooAnimationTrackerSingleton()


def secondaryFunction():
    """When the marking menu is released, run for a secondary feature

    Search for `ANIM_TRACKER_INST.markingMenuTriggered = True ` to see where the trigger is set to be True
    """
    ANIM_TRACKER_INST.markingMenuMoShapes = None
    if ANIM_TRACKER_INST.markingMenuTriggered:  # Ignore if the menu was triggered
        ANIM_TRACKER_INST.markingMenuTriggered = False
        return


class AnimationMarkingMenuCommand(menu.MarkingMenuCommand):
    """Command class for the Animation Marking Menu

    Commands are related to the file (JSON) in the same directory:

    .. code-block:: python

        animation.mmlayout

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
        zooMenu.MarkingMenu.buildFromLayout("markingMenu.animation",
                                            "animationMarkingMenu",
                                            parent=mel.eval("findPanelPopupParent"),
                                            options={"altModifier": False,
                                                     "shiftModifier": False})

    Map to hotkey release:

    .. code-block:: python

        from zoo.libs.maya.markingmenu import menu as zooMenu
        zooMenu.MarkingMenu.removeExistingMenu("animationMarkingMenu")

    """
    id = "animationMarkingMenu"  # a unique identifier for a class, should never be changed
    creator = "ZooTools"

    def locatorBake(self):

        timeRange = timerange.getSelectedFrameRange()
        selection = cmds.ls(selection=True)
        locatorList = list()
        for selected in selection:
            if selected.count("_LOC"):
                duplicateNameCheck = "{}_LOC".format(selected.split("_LOC")[0])
                suffix = str(len(cmds.ls("{}*".format(duplicateNameCheck), type="transform")))
                locatorName = duplicateNameCheck + "_" + suffix
                locatorList.append(locatorName)
            else:
                locatorName = "{}_LOC".format(selected)
                locatorList.append(locatorName)
            locConstraintName = "{}_parentConstraint".format(selected)
            if cmds.objExists(locatorName):
                cmds.delete(locatorName)
                locatorBaked = cmds.spaceLocator(name=locatorName)
            else:
                locatorBaked = cmds.spaceLocator(name=locatorName)
            locatorConstraint = cmds.parentConstraint(selected, locatorBaked, weight=1, name=locConstraintName)
        clear = cmds.select(clear=True)
        selectLocators = cmds.select(locatorList)
        if timeRange[1] - timeRange[0] <= 1:
            bakeanim.bakeSelected(timeSlider=0, bakeFrequency=1)
        else:
            bakeanim.bakeSelected(timeRange=timeRange, timeSlider=2, bakeFrequency=1)
        for selected in selection:
            locConstraintName = "{}_parentConstraint".format(selected)
            cmds.delete(locConstraintName)

    def ctrlConstraint(self):
        selection = cmds.ls(selection=True)
        if ANIM_TRACKER_INST.constraintChecker:
            for selected in selection:
                if selected.count("_LOC"):
                    ctrlName = selected.split("_LOC")[0]
                    ctrlConstraintName = "{}_parentConstraint".format(ctrlName)
                    if cmds.objExists(ctrlConstraintName):
                        cmds.delete(ctrlConstraintName)
                else:
                    ctrlConstraintName = "{}_parentConstraint".format(selected)
                    if cmds.objExists(ctrlConstraintName):
                        cmds.delete(ctrlConstraintName)
        else:
            for selected in selection:
                if selected.count("_LOC"):
                    ctrlName = selected.split("_LOC")[0]
                    ctrlConstraintName = "{}_parentConstraint".format(ctrlName)
                    cmds.parentConstraint(selected, ctrlName, weight=1, name=ctrlConstraintName)
                else:
                    ctrlConstraintName = "{}_parentConstraint".format(selected)
                    try:
                        cmds.parentConstraint("{}_LOC".format(selected), selected, weight=1, name=ctrlConstraintName)
                    except ValueError:
                        output.displayWarning("{}_LOC Locator Missing. Locator Parent Constraint Cancelled.".format(selected))

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
        if arguments['operation'] == 'locatorParentConstraint':
            selection = cmds.ls(selection=True)
            if len(selection) == 0:
                ANIM_TRACKER_INST.constraintChecker = False
            for selected in selection:
                if selected.count("_LOC"):
                    ctrlName = selected.split("_LOC")[0]
                    ctrlConstraintName = "{}_parentConstraint".format(ctrlName)
                    if cmds.objExists(ctrlConstraintName):
                        ANIM_TRACKER_INST.constraintChecker = True
                        break
                    else:
                        ANIM_TRACKER_INST.constraintChecker = False
                else:
                    ctrlConstraintName = "{}_parentConstraint".format(selected)
                    if cmds.objExists(ctrlConstraintName):
                        ANIM_TRACKER_INST.constraintChecker = True
                        break
                    else:
                        ANIM_TRACKER_INST.constraintChecker = False
            if ANIM_TRACKER_INST.constraintChecker:
                ret['label'] = "Delete Loc Parent Constrain"
            else:
                ret['label'] = "Locator Parent Constrain"
        ANIM_TRACKER_INST.markingMenuTriggered = True
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
        elif operation == "locatorBake":
            self.locatorBake()
        elif operation == "bakeAnimation":
            generalanimation.bakeKeys()
        elif operation == "animHold":
            generalanimation.animHold()
        elif operation == "openAnimationToolbox":
            openToolset("generalAnimationTools", advancedMode=False)
        elif operation == "openGhostEditor":
            generalanimation.openGhostEditor()
        elif operation == "matchBakeAnim":
            openToolset("matchBakeAnim")
        elif operation == "delKeyCurrentTime":
            generalanimation.deleteCurrentFrame()
        elif operation == "resetAttributes":
            generalanimation.resetAttrsBtn()
        elif operation == "randomizeKeyframes":
            definedhotkeys.open_keyRandomizer(advancedMode=False)
        elif operation == "numericRetimer":
            definedhotkeys.open_numericRetimer(advancedMode=False)
        elif operation == "tweenMachine":
            definedhotkeys.open_tweenMachinePopup(cursorOnSlider=False, clickOffClose=False, closeOnRelease=False)
        elif operation == "selectAnimatedNodesAll":
            generalanimation.selectAnimNodes(mode=1)
        elif operation == "selectAnimatedNodesHierachy":
            generalanimation.selectAnimNodes(mode=0)
        elif operation == "selectAnimatedNodesSelected":
            generalanimation.selectAnimNodes(mode=2)
        elif operation == "deleteAllMotionTrails":
            motiontrail.deleteMotionTrails(scene=True, selected=False)
        elif operation == "changeRotationOrder":
            definedhotkeys.open_graphEditorTools(advancedMode=False)
        elif operation == "locatorParentConstraint":
            self.ctrlConstraint()
        return

    def executeUI(self, arguments):
        """The option box execute methods for the motion paths marking menu. see execute() for main commands

        For this method to be called "optionBox": True.

        :type arguments: dict
        """
        operation = arguments.get("operation", "")
        if operation == "locatorBake":
            pass
        elif operation == "createMotionTrails":
            openToolset("animationPaths", advancedMode=False)
        elif operation == "bakeAnimation":
            openToolset("bakeAnimation", advancedMode=False)
        elif operation == "tweenMachine":
            openToolset("tweenMachine", advancedMode=False)
        return
