import math

import maya.cmds as cmds
import maya.mel as mel

from zoo.libs.maya.utils import mayaenv
from zoo.libs.utils import output
from zoo.libs.maya.cmds.animation import grapheditorfcurve, timerange, keyframes, animobjects, resetattrs, bakeanim, \
    motiontrail, animconstants
from zoo.libs.maya.cmds.display import viewportmodes
from zoo.libs.maya import zapi

from zoovendor import six
from zoo.core.util import classtypes


def changeRotOrder(nodes=None, newRotOrder=zapi.kRotateOrder_XYZ,
                   bakeEveryFrame=False,
                   timeline=True):
    """Sets the rotation order of the specified nodes or the selected nodes.

    :param nodes: If None then the current selection will be used.
    :type nodes: list[:class:`zapi.DagNode`] or None
    :param newRotOrder: The rotation order number between 0-5.
    :type newRotOrder: int
    :param bakeEveryFrame: Whether all frames either on the timeline or between the start and end frame keys \
    for the nodes should be baked.
    :type bakeEveryFrame: bool
    :param timeline: Whether the current active timeline should be used as a key filter.
    :type timeline: bool
    """
    nodes = nodes or list(zapi.selected(filterTypes=(zapi.kNodeTypes.kTransform,)))
    if not nodes:
        output.displayWarning('No objects selected. Please make a selection.')
        return
    frameRange = None
    if timeline:
        frameRange = list(map(int, timerange.getSelectedOrCurrentFrameRange()))
    # todo: isolate views
    zapi.setRotationOrderOverFrames(nodes, rotationOrder=newRotOrder,
                                    bakeEveryFrame=bakeEveryFrame,
                                    frameRange=frameRange)


def allGimbalTolerancesForKeys(node=None, currentFrameRange=False, message=False):
    """Returns the tolerances for each rotation order for the given nodes keyframes.

    :param node: The node to query or None if you want to use the first selected node.
    :type node: :class:`zapi.DagNode` or None
    :param currentFrameRange: if the current active frame range is be used.
    :type currentFrameRange: bool
    :param message: report a message to the user?
    :type message: bool
    :return: The list of tolerances.
    :rtype: list[float]
    """
    if not node:
        selected = list(zapi.selected(filterTypes=(zapi.kNodeTypes.kTransform,)))
        if selected:
            node = selected[0]
    if not node:
        if message:
            output.displayWarning("No objects selected. Please make a selection.")
        return []
    nodeFullPath = node.fullPathName()
    if currentFrameRange:
        frameRange = timerange.getSelectedOrCurrentFrameRange()
        keys = cmds.keyframe(nodeFullPath, time=tuple(frameRange), attribute='rotate', timeChange=True, query=True)
    else:
        keys = cmds.keyframe(nodeFullPath, attribute="rotate", timeChange=True, query=True)
    stepCount = 1
    if keys:
        keys = sorted(set(keys))

        keysCount = len(keys)

        if keysCount >= 100:
            stepCount = int(math.floor(keysCount / 100.0) * 100 / 50.0)
        elif keysCount >= 50:
            stepCount = 2
    return zapi.allGimbalTolerances(node, keys, step=stepCount)


def gimbalTolerancesToLabels(tolerances):
    """Given a list of tolerance values return the appropriate labels. Useful for UIs.

    :param tolerances: The tolerance values ie. list(0.0,48.0,99.0)
    :type tolerances: list[float]
    :rtype: list[str]
    """
    # Build the combo names list ----------------------------------------
    percentages = [(int(percent * 100)) for index, percent in enumerate(tolerances)]
    minPercent = min(percentages)
    labels = [""] * len(zapi.constants.kRotateOrderNames)
    for i, rotOrder in enumerate(zapi.constants.kRotateOrderNames):
        name = "{} {}% Gimballed".format(rotOrder.upper(), percentages[i])
        if percentages[i] == minPercent:
            name = "{} (recommended)".format(name)
        labels[i] = name
    return labels


# -------------------
# SELECT
# -------------------


def selectAnimNodes(mode=0):
    """
    0 Select all animated nodes under the selected hierarchy.
    1 Select all animated nodes in the scene.
    2 Select all animated nodes in the selection.

    :param mode: Hierarchy 0, scene 1, from selected, 2
    :type mode: int
    """
    if mode == 0:  # hierarchy
        animobjects.getAnimatedNodes(selectFlag="hierarchy", select=True, message=True)
    elif mode == 1:  # scene (all)
        animobjects.getAnimatedNodes(selectFlag="all", select=True, message=True)
    else:
        animobjects.getAnimatedNodes(selectFlag="selected", select=True, message=True)


# -------------------
# GENERAL
# -------------------


def setKeyChannel():
    """Set Key on all attributes, but if any Channel Box attributes are
    selected then key only those channels."""
    selAttrs = mel.eval('selectedChannelBoxAttributes')
    if not selAttrs:
        mel.eval('setKeyframe;')  # default set keyframe
        return
    cmds.setKeyframe(breakdown=False, attribute=selAttrs)


def setKeyAll():
    """Sets a key on all attributes ignoring any Channel Box selection."""
    mel.eval('setKeyframe;')


def animHold():
    """Make an animation hold.
    Place the timeline between two keys and run.
    The first key will be copied to the second with flat tangents.
    Zoo Hotkey: alt a
    """
    grapheditorfcurve.animHold(message=True)


def deleteCurrentFrame():
    """Deletes keys at the current time, or the selected timeline range. """
    mel.eval('timeSliderClearKey;')


def keyToggleVis():
    """Keys and inverts the visibility of the selected objects.
    Visibility of True will become False"""
    keyframes.toggleAndKeyVisibility()


def resetAttrsBtn():
    """Resets the selected object/s attributes to default values."""
    resetattrs.resetSelection()


def toggleControlCurveVis():
    """Toggles Curve visibility in the current viewport"""
    currentPanel = viewportmodes.panelUnderPointerOrFocus()
    if not currentPanel:
        return
    visInvertState = not cmds.modelEditor(currentPanel, query=True, nurbsCurves=True)
    cmds.modelEditor(currentPanel, edit=True, nurbsCurves=visInvertState)
    if visInvertState:
        visStr = "VISIBLE"
    else:
        visStr = "HIDDEN"
    output.displayInfo("Controls visibility set to: {}".format(visStr))


def bakeKeys():
    """Bakes animation keyframes using bake curves or bake simulation depending on the selection

    Hardcoded hotkey settings.  Bakes every frame of the selected range or if none selected the playback range.

    Bake Animation based on selection:

        1. Graph keyframe selection. (Time Range is ignored)
        2. Channel Box selection.
        3. If nothing is selected will bake all attributes.

    """
    bakeanim.bakeSelected(timeSlider=0, bakeFrequency=1)


def eulerFilter():
    """Perform Maya's Euler Filter on selected objects rotation values"""
    mel.eval('filterCurve;')


def createMotionTrail():
    """Creates a motion trail on the selected object/s

    Displays settings from the ZooMotionTrailTrackerSingleton() data as shared across UIs and marking menus.
    """
    MT_TRACKER_INST = motiontrail.ZooMotionTrailTrackerSingleton()
    motiontrail.createMotionTrailSelBools(MT_TRACKER_INST.keyDots_bool,
                                          MT_TRACKER_INST.crosses_bool,
                                          MT_TRACKER_INST.frameSize_bool,
                                          MT_TRACKER_INST.pastFuture_bool,
                                          MT_TRACKER_INST.frameNumbers_bool,
                                          MT_TRACKER_INST.limitBeforeAfter_bool,
                                          limitFrames=MT_TRACKER_INST.limitAmount)


def openGhostEditor():
    """Opens Maya's Ghost Editor Window"""
    if mayaenv.mayaVersion() >= 2022:
        mel.eval('OpenGhostEditor')
    else:
        output.displayWarning("The Ghost Editor Window is only available in 2022")


# -------------------
# GRAPH EDITOR
# -------------------


def snapKeysWholeFrames():
    """Snaps the selected keys to whole frames."""
    mel.eval('snapKey -timeMultiple 1 ;')


def snapKeysCurrent():
    """Snaps the selected graph keys to the current time.
    """
    grapheditorfcurve.moveKeysSelectedTime()


def cycleAnimation(cycleMode=0, pre=True, post=True, displayInfinity=True):
    """Cycles the selected objects, options for the scale mode and pre and post.

    Cycle modes are ints:

        Cycle: 0
        Cycle With Offset: 1
        Oscillate: 2
        Linear: 3
        Constant: 4

    :param cycleMode: The type of cycle to set. See description for settings.
    :type cycleMode: int
    :param pre: True cycles pre infinity
    :type pre: bool
    :param post: True cycles post infinity
    :type post: bool
    """
    if pre:
        mel.eval('setInfinity - pri {};'.format(animconstants.GRAPH_CYCLE[cycleMode]))
    if post:
        mel.eval('setInfinity - poi {};'.format(animconstants.GRAPH_CYCLE[cycleMode]))
    showInfinity(displayInfinity)


def removeCycleAnimation():
    """Removes any cycling animation on the selected objects for both pre and post."""
    cycleAnimation(cycleMode=4, pre=True, post=True, displayInfinity=False)


def showInfinity(show):
    """Show Infinity in the graph editor.

    :param show: True will show, False will hide.
    :type show: bool
    """
    #  cmds.animCurveEditor('graphEditor1GraphEd', edit=True, displayInfinities=show)  # cmds is broken?
    mel.eval("animCurveEditor -edit -displayInfinities {} graphEditor1GraphEd;".format(int(show)))


def toggleInfinity():
    """Toggles infinity on and off in the Graph Editor"""
    infinityState = cmds.animCurveEditor('graphEditor1GraphEd', query=True, displayInfinities=True)
    showInfinity(not infinityState)


def selObjGraph():
    """Select an object from a graph curve selection. """
    grapheditorfcurve.selectObjFromFCurve()


def timeToKey():
    """Moves the time slider to the closest selected keyframe."""
    grapheditorfcurve.jumpToSelectedKey()


def insertKey():
    """Maya's Insert Key Tool.
    Select a fCurve and middle click drag to insert a key."""
    mel.eval('insertKey')


def copyKeys():
    """Copy Keyframes in the Graph Editor."""
    mel.eval('performCopyKeyArgList 1 {"3", "graphEditor1GraphEd", "1"}')


def pasteKeys():
    """Paste Keyframes in the Graph Editor."""
    curTime = cmds.currentTime(query=True)
    cmds.pasteKey(time=(curTime, curTime),
                  float=(curTime, curTime),
                  option="merge",
                  copies=1,
                  connect=0,
                  timeOffset=0,
                  floatOffset=0,
                  valueOffset=0)


# -------------------
# PLAY STEP
# -------------------


def playPause():
    """Play/Pause animation toggle."""
    mel.eval('togglePlayback')


def reverse():
    """Reverse/Pause animation toggle."""
    if cmds.play(q=True, state=True):
        cmds.play(state=False)
        return
    cmds.play(forward=False)


def stepNextFrame():
    """Step to the next frame in the timeline."""
    timerange.animMoveTimeForwardsBack(1)


def stepLastFrame():
    """Step to the last frame in the timeline."""
    timerange.animMoveTimeForwardsBack(-1)


def stepNextKey():
    """Step to the next Key Frame in the timeline."""
    mel.eval('undoInfo - swf off;')
    mel.eval('currentTime -edit `findKeyframe -timeSlider -which next`;')
    mel.eval('undoInfo - swf on;')


def stepLastKey():
    """Step to the last Key Frame in the timeline."""
    mel.eval('undoInfo - swf off;')
    mel.eval('currentTime -edit `findKeyframe -timeSlider -which previous`;')
    mel.eval('undoInfo - swf on;')


def step5framesForwards():
    """Step forward five frames in time."""
    timerange.animMoveTimeForwardsBack(5)


def step5framesBackwards():
    """Step backwards five frames in time. """
    timerange.animMoveTimeForwardsBack(-5)


# -------------------
# TIMELINE
# -------------------


def playRangeStart():
    """Sets the playback start to the current time."""
    timerange.playbackRangeStartToCurrentFrame(animationStartTime=False)


def playRangeEnd():
    """Sets the playback end to the current time."""
    timerange.playbackRangeEndToCurrentFrame(animationEndTime=False)


def timeRangeStart():
    """Sets the time-range start to the current time."""
    timerange.playbackRangeStartToCurrentFrame()


def timeRangeEnd():
    """Sets the time-range end to the current time."""
    timerange.playbackRangeEndToCurrentFrame()


# ---------------------------
# ANIMATION TRACK DATA ACROSS MULTIPLE UIS AND MARKING MENUS
# ---------------------------


@six.add_metaclass(classtypes.Singleton)
class ZooAnimationTrackerSingleton(object):
    """Used by the animation marking menu & UI, tracks data for animation between UIs and marking menus.
    """

    def __init__(self):
        # Marking Menu ----------------
        self.markingMenuTriggered = False
        self.markingMenuMoShapes = None

        self.constraintChecker = False


@six.add_metaclass(classtypes.Singleton)
class ZooGraphEditorTrackerSingleton(object):
    """Used by the animation marking menu & UI, tracks data for animation between UIs and marking menus.
    """

    def __init__(self):
        # Marking Menu ----------------
        self.markingMenuTriggered = False
        self.markingMenuMoShapes = None

        # Cycle Toggle
        self.cycleToggle = False

        # Isolate Curve Toggle
        self.isolateCurveToggle = False
