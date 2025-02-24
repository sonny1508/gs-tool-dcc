from maya import cmds as cmds

from zoo.libs.maya.cmds.animation import animobjects, grapheditorfcurve, animconstants, animlayers

from zoo.libs.utils import output

AVERAGE_MODES = ["average", "minMaxCenter"]


# -------------------
# SCALE KEYS BY CENTER
# -------------------


class ScaleKeysCenter(object):
    """Class for dealing with scaling keys from the center pivot of each graph curve.
    """

    def __init__(self, scaleAmount=1.0, animCurves=list(), scaleCacheDict=dict(), mode=AVERAGE_MODES[0]):
        """Scales values from a given cache dictionary.

        Automatically detects the center of each curve selection and scales from that value pivot per curve.

        Useful for controlling the intensity of random noise on multiple curves, can also be used to invert curves

        self.scaleCacheDict, is a dict of curves keys with time and value lists:

            Curve (key), TimeList, ValueList
            {'pCube1_translateX': [[119.0, 120.0], [8.237586020630143, 4.889088181859329]]}

        Once the dict has been created it can be modified and reset dynamically in a UI

        self.mode modes are in the global list AVERAGE_MODES:

            "average": Finds the average of all keys for the center pivot,
            "minMaxCenter": Finds the middle value of the highest and lowest point

        Code Example:

            from zoo.libs.maya.cmds.animation.scaleretime import ScaleKeysCenter
            instance = ScaleKeysCenter()  # starts the class
            instance.setMode("minMaxCenter") # set the mid pivot type
            instance.setScaleAmount(2.0)  # set the scale amount
            instance.cacheDictFromSelected()  # starts the cache by collecting the selected key data
            if instance.scaleCacheDict:  # if curve data found
                instance.scaleKeysCenter()  # does the scale

        :param scaleAmount: The value to scale by. Can be left empty
        :type scaleAmount: float
        :param animCurves: A list of animation curve names. Can be left empty
        :type animCurves: list(str)
        :param scaleCacheDict: The cache dictionary (see description).  Can be left empty
        :type scaleCacheDict: dict()
        :param mode: "average" finds the average of all keys for the center pivot, "minMaxCenter" finds middle of hi/low
        :type mode: str
        """
        self.mode = mode
        self.animCurves = animCurves
        self.scaleAmount = scaleAmount
        self.scaleCacheDict = scaleCacheDict

    def setScaleAmount(self, scaleValueAmount):
        """Updates the scale value amount for the class.  scaleValueAmount is a float 2.0 scales double.

        :param scaleValueAmount: The value to scale by
        :type scaleValueAmount: float
        """
        self.scaleAmount = scaleValueAmount

    def setMode(self, mode):
        """Sets the mode of the scale, modes are in the global list AVERAGE_MODES:

            "average": Finds the average of all keys for the center pivot,
            "minMaxCenter": Finds the middle value of the highest and lowest point

        :param mode: "average" finds the average of all keys for the center pivot, "minMaxCenter" finds middle of hi/low
        :type mode: str
        """
        self.mode = mode
        self._updateCacheDictMidPoint()

    def clearCache(self):
        """Clears the cache values"""
        self.animCurves = list()
        self.scaleCacheDict = dict()

    def resetScale(self):
        """Resets all values to the original cached values in the scaleCacheDict.
        """
        if not self.scaleCacheDict:
            return
        for animCurve in self.animCurves:
            for i, index in enumerate(self.scaleCacheDict[animCurve][0]):
                cmds.keyframe(animCurve, index=index, valueChange=self.scaleCacheDict[animCurve][1][i])

    def buildCache(self, message=True):
        """Creates the cache ready for scaling, cache values are

        self.scaleCacheDict, is a dict of curves keys with time and value lists:

            Curve (key), TimeList, ValueList
            {'pCube1_translateX': [[119.0, 120.0], [8.237586020630143, 4.889088181859329]]}

        :param message: Report messages to the user
        :type message: bool
        """
        if not self.animCurves:
            self.clearCache()
            if message:
                output.displayWarning("Please select animation graph keys or animation curves.")
            return
        # Return from animation curves -----------------
        for curve in self.animCurves:
            keyValues = cmds.keyframe(curve, query=True, valueChange=True, selected=True)
            keyIndices = cmds.keyframe(curve, query=True, indexValue=True, selected=True)
            keyIndices = grapheditorfcurve.convertKeyIndexList(keyIndices)  # Index list must be converted
            if self.mode == AVERAGE_MODES[0]:  # Use "average" of all keys
                midPoint = sum(keyValues) / len(keyValues)
            else:  # "minMaxCenter" use the mid point of the max and min
                midPoint = (max(keyValues) + min(keyValues)) / 2  # Half way point between max and min values
            self.scaleCacheDict[curve] = [keyIndices, keyValues, midPoint]  # save dict

    def cacheDictFromSelected(self, message=True):
        """Creates the cache ready for scaling, uses the current selection. See self.buildCache() for more info

        :param message: Report messages to the user
        :type message: bool
        """
        self.animCurves = cmds.keyframe(query=True, name=True, selected=True)
        self.buildCache(message=message)

    def scaleKeysCenter(self):
        """Main function that center scales from the cache values and self.scaleValueAmount
        Note this method uses calculates the new scale values in python and sets via cmds.keyframe()
        Can be used to update the cache curves at any time.

        self.scaleCacheDict, is a dict of curves keys with time and value lists:

            Curve (key), TimeList, ValueList
            {'pCube1_translateX': [[119.0, 120.0], [8.237586020630143, 4.889088181859329]]}

        Set the scale value with:

            instance.setScaleAmount(scaleValueAmount)

        Create the self.scaleCacheDict with:

            instance.cacheDictFromSelected()

        """
        if not self.animCurves:  # rare
            return
        for animCurve in self.animCurves:
            for i, index in enumerate(self.scaleCacheDict[animCurve][0]):
                # (value - scalePivotMidPoint) *  scaleValueAmount + scalePivotMidPoint
                newValue = (self.scaleCacheDict[animCurve][1][i] - self.scaleCacheDict[animCurve][
                    2]) * self.scaleAmount + self.scaleCacheDict[animCurve][2]
                cmds.keyframe(animCurve, index=index, valueChange=newValue)

    def _updateCacheDictMidPoint(self):
        """Updates the self.scaleCacheDict to change the midpoint, depending on the given mode.

        Mode can be changed, change it with instance.setMode(mode).  Mode can be:

            "average": Finds the average of all keys for the center pivot,
            "minMaxCenter": Finds the middle value of the highest and lowest point

        """
        if not self.animCurves:
            return
        for animCurve in self.animCurves:
            keyIndices = self.scaleCacheDict[animCurve][0]
            keyValues = self.scaleCacheDict[animCurve][1]
            if self.mode == AVERAGE_MODES[0]:  # Use "average" of all keys
                midPoint = sum(keyValues) / len(keyValues)
            else:  # "minMaxCenter" use the mid point of the max and min
                midPoint = (max(keyValues) + min(keyValues)) / 2  # Half way point between max and min values
            self.scaleCacheDict[animCurve] = [keyIndices, keyValues, midPoint]


# -------------------
# SCALE KEYS: FPS, PERCENTAGE, MAYA FLOAT
# -------------------


def MayaFloatToPercentage(timeScale):
    """Convert time scale: Maya Float to Percentage

    :param timeScale: new time scale in the new time mode
    :type timeScale: float
    """
    return 1 / timeScale * 100  # 1 / .5 * 100 = 200%


def MayaFloatToFPS(timeScale):
    """Convert time scale: Maya Float to Frames Per Second

    :param timeScale: new time scale in the new time mode
    :type timeScale: float
    """
    return animconstants.getSceneFPS() / timeScale  # 24 / .5 = 48


def percentageToMayaFloat(timeScale):
    """Convert time scale: Percentage to Maya Float

    :param timeScale: new time scale in the new time mode
    :type timeScale: float
    """
    return 100 / timeScale  # 100 / 50 = 2.0


def percentageToFPS(timeScale):
    """Convert time scale: Percentage to Frames Per Second

    :param timeScale: new time scale in the new time mode
    :type timeScale: float
    """
    return (timeScale / 100) * animconstants.getSceneFPS()


def FPStoMayaFloat(timeScale):
    """Convert time scale: Frames Per Second to Maya Float

    :param timeScale: new time scale in the new time mode
    :type timeScale: float
    """
    return 1 / (timeScale / animconstants.getSceneFPS())  # 1 / (48 / 24) = 0.5  or twice as fast for this section


def FPStoPercentage(timeScale):
    """Convert time scale: Frames Per Second to Percentage

    :param timeScale: new time scale in the new time mode
    :type timeScale: float
    """
    return 1 / (animconstants.getSceneFPS() / timeScale) * 100  # 1 / (48 / 24) * 100 = 200


def convertTimeScale(timeScale, oldType=0, newType=1, message=True):
    """Converts a scale in one time type to another

    Types:

        #. Maya Float, Maya float style twice as fast is 0.5.
        #. Percentage, Scales time as a percentage similar to an edit program.  Twice as fast is 200%.
        #. Frames Per Second, Scales time as `frames per second` similar to an edit program. Twice as fast is 48 if 24fps.

    :param timeScale: The timeScale float to convert.
    :type timeScale: float
    :param oldType: 0 - Maya Float, 1 - Percentage, 2 - Frames Per Second
    :type oldType: int
    :param newType: 0 - Maya Float, 1 - Percentage, 2 - Frames Per Second
    :type newType: int
    :param message: Report a message to the user?
    :type message: bool
    """
    if oldType == 0 and newType == 1:
        return MayaFloatToPercentage(timeScale)
    elif oldType == 0 and newType == 2:
        return MayaFloatToFPS(timeScale)
    elif oldType == 1 and newType == 0:
        return percentageToMayaFloat(timeScale)
    elif oldType == 1 and newType == 2:
        return percentageToFPS(timeScale)
    elif oldType == 2 and newType == 0:
        return FPStoMayaFloat(timeScale)
    elif oldType == 2 and newType == 1:
        return FPStoPercentage(timeScale)
    if message:
        output.displayWarning("Could not convert scale time")
    return None


# -------------------
# NUMERIC RE-TIME KEYS
# -------------------


def animRetimer(startRange=0, endRange=100, timeScale=1.0, snapKeys=True, selectType=0, timeScaleOptions=0,
                ripple=True, allAnimLayers=True, message=True):
    """Numeric time scale of keyframes within a time range, will ripple offset the keys after the endRange

    The timeScale will be scale as per the timeScaleOptions

        0 - Maya float style twice as fast is 0.5
        1 - Scales time as a percentage similar to an edit program.  Twice as fast is 200%
        2 - Scales time as `frames per second` similar to an edit program. Twice as fast is 48 if 24fps.

    The selectType can affect various objects:

        0 - selection: use the current selection
        1 - hierarchy: use the current selection and all animated objects in the hierarchy under the selection
        2 - all: use all animated objects in the scene

    :param startRange: The start frame of the section to re-time
    :type startRange: float
    :param endRange: The end frame of the section to re-time
    :type endRange: float
    :param timeScale: The scale value to affect time, see timeScaleOptions for how time will be scaled
    :type timeScale: bool
    :param snapKeys: True if the user wants to snap keyframes to whole frames after scaling
    :type snapKeys: bool
    :param selectType: 0 is Affect selected objs. 1 is selected and anim hierarchy. 2 is select all anim in scene
    :type selectType: int
    :param timeScaleOptions: 0 is maya float, 1 is percentage, 2 is fps.  See description for more info.
    :type timeScaleOptions: int
    :param ripple: move the keys outside of the range being scaled?
    :type ripple: bool
    :param message: report the message back to the user?
    :type message: bool
    """
    endOfTime = 1000000000
    animObjs = cmds.ls(selection=True, long=True)

    # Calculate timeScale --------------------------------------------------------
    if timeScaleOptions == 1:  # Percentage
        timeScale = percentageToMayaFloat(timeScale)
    elif timeScaleOptions == 2:  # FPS
        timeScale = FPStoMayaFloat(timeScale)
    animRange = endRange - startRange
    moveKeys = (animRange - (animRange * timeScale)) * -1  # Move key amount

    # Which objects to affect? --------------------------------
    if selectType == 0:
        if not animObjs:
            output.displayWarning("Please select some objects.")
    elif selectType == 1:  # Animated hierarchy
        rememberSelection = cmds.ls(selection=True)
        animObjs = animobjects.getAnimatedNodes(selectFlag="hierarchy", message=False, select=True)  # select hi anim
        if not animObjs:
            output.displayWarning("No animated were found in this hierarchy")
            cmds.select(rememberSelection, replace=True)
            return
    elif selectType == 2:  # Whole Scene
        rememberSelection = cmds.ls(selection=True)
        animObjs = animobjects.getAnimatedNodes(selectFlag="all", message=False, select=True)  # select all anim objs
        if not animObjs:
            output.displayWarning("No animated objects in the scene were found")
            cmds.select(rememberSelection, replace=True)
            return

    # Check the curves/keyframe data -----------------------------
    if allAnimLayers:
        curvesActive = animlayers.animCurvesAllLayers(animObjs)
    else:  # only work on selected layers
        curvesActive = cmds.keyframe(animObjs, query=True, name=True)  # selects all curves on the selected objects

    if selectType == 0:  # Is "selected" mode so see if there's a Graph key selection, work on it if so.
        selCurves = cmds.keyframe(query=True, name=True, selected=True)
        if selCurves:
            curvesActive = selCurves
        if not curvesActive:  # then bail no keys found
            if message:
                output.displayWarning("No FCurves active, please select objects with keyframes")
            return

    # Do the logic ----------------------------------------------------------
    if moveKeys > 0:  # If move keys is a positive value
        for curve in curvesActive:  # Move and then scale
            if ripple:  # move the keys before
                cmds.keyframe(curve, time=((endRange + 1), endOfTime), edit=True, relative=True, timeChange=moveKeys)
            cmds.scaleKey(curve, time=(startRange, endRange), timeScale=timeScale, timePivot=startRange)
    else:  # If move keys is negative switch order: Scale, then move
        for curve in curvesActive:  # Scale and then move
            cmds.scaleKey(curve, time=(startRange, endRange), timeScale=timeScale, timePivot=startRange)
            if ripple:  # move the keys after
                cmds.keyframe(curve, time=((endRange + 1), endOfTime), edit=True, relative=True, timeChange=moveKeys)

    # Snap ----------------------------------------------------------------------
    if snapKeys:  # Snap keys to integer time
        for curve in curvesActive:
            cmds.snapKey(curve, timeMultiple=True)
    if selectType == 1 or selectType == 2:  # return to original selection
        cmds.select(rememberSelection, replace=True)
