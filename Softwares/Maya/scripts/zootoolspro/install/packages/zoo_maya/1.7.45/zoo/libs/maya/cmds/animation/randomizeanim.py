import random

import maya.cmds as cmds

from zoo.libs.utils import output
from zoo.libs.maya.cmds.animation import timerange, animlayers, bakeanim


# -------------------
# RANDOMIZE KEYS
# -------------------


def mergeTwoDicts(x, y):
    """Merges two dictionaries together

    :param x: dict A
    :type x: dict
    :param y: dict B
    :type y: dict
    :return: dict A and B now combined
    :rtype: dict
    """
    z = x.copy()
    z.update(y)
    return z


def randomizeKeyAttr(obj, attr, time, randomRange=[-1.0, 1.0]):
    """Randomizes a single key given the object and attribute

    :param obj: A Maya object/node name
    :type obj: str
    :param attr: A Maya node/object attribute name
    :type attr: str
    :param time: The time/frame to affect
    :type time: float
    :param randomRange: the lower and upper values to randomize. The randomize value range.
    :type randomRange: list(float)
    """
    oldKeyValue = cmds.keyframe(obj, attribute=attr, query=True, eval=True, time=(time, time))
    if not oldKeyValue:
        return None, None, None
    oldKeyValue = oldKeyValue[0]
    randomFloat = random.random()
    newValue = ((randomRange[-1] - randomRange[0]) * randomFloat) + \
               (oldKeyValue + randomRange[0])
    cmds.keyframe(obj, attribute=attr, valueChange=newValue, time=(time, time))
    return oldKeyValue, newValue, randomFloat


def randomizeKeyCurve(animCurve, time, randomRange=[-1.0, 1.0]):
    """Randomizes a single key given the animation curve eg 'pCube1_translateX1'

    :param animCurve:The name of an animation curve node
    :type animCurve: str
    :param time: The time/frame to affect
    :type time: float
    :param randomRange: the lower and upper values to randomize. The randomize value range.
    :type randomRange: list(float)

    :return oldValue: The old value of the keyframe
    :rtype oldValue: float
    :return newValue: The updated new value of the keyframe
    :rtype newValue: float
    """
    curList = cmds.keyframe(animCurve, query=True, eval=True, time=(time, time))
    if not curList:
        output.displayWarning("No keyframe found on curve {}".format(animCurve))
        return None
    oldValue = curList[0]
    randomFloat = random.random()
    newValue = ((randomRange[-1] - randomRange[0]) * randomFloat) + (oldValue + randomRange[0])
    cmds.keyframe(animCurve,
                  valueChange=newValue,
                  time=(time, time))  # TODO can be relative move
    return oldValue, newValue, randomFloat


def randomizeKeysAttrRange(obj, attr, timeRange=[0, 100], randomRange=[-1.0, 1.0]):
    """Randomizes keyframe attributes on an object with various options

    :param obj: A Maya object/node name
    :type obj: str
    :param attr: A Maya node/object attribute name
    :type attr: str
    :param timeRange: The time range to affect start frame/end frame
    :type timeRange: list(float)
    :param randomRange: the lower and upper values to randomize. The randomize value range.
    :type randomRange: list(float)

    :return animCurve: An animation curve name, will be "" if None.
    :rtype animCurve: str
    :return keyTimeList: A list of keyframe times
    :rtype keyTimeList: list(float)
    :return oldKeyValues: A list of keyframe values, these are the old values for the UI cache
    :rtype oldKeyValues: list(float)
    """
    animCurve = ""
    oldKeyValues = list()
    keyTimeList = list()
    randomFloats = list()
    # Iterate through all keys in the time range
    if not cmds.attributeQuery(attr, node=obj, exists=True):  # if attribute does not exist skip
        return animCurve, keyTimeList, oldKeyValues, randomFloats
    if not cmds.getAttr(".".join([obj, attr]), settable=True):  # if attr is locked or connected skip
        return animCurve, keyTimeList, oldKeyValues, randomFloats
    keyTimeList = timerange.keysInRange(obj, attr, timeRange=timeRange)
    if not keyTimeList:
        output.displayWarning("No keys found for attribute {}".format(attr))
        return animCurve, keyTimeList, oldKeyValues, randomFloats
    # Do the randomize -----------------------------------------
    for key in keyTimeList:
        oldKeyValue, newKeyValue, randomFloat = randomizeKeyAttr(obj, attr, key, randomRange=randomRange)
        oldKeyValues.append(oldKeyValue)
        randomFloats.append(randomFloat)
    # Get the anim curve name from the obj and attr
    animCurveList = cmds.keyframe(obj, attribute=attr, name=True, query=True)
    if not animCurveList:
        output.displayWarning("No curve found for {}.{}".format(obj, attr))
        return animCurve, keyTimeList, oldKeyValues, randomFloats
    return animCurveList[0], keyTimeList, oldKeyValues, randomFloats


def randomizeKeysAttrRangeCurve(animCurve, timeRange=[0, 100], randomRange=[-1.0, 1.0], message=False):
    """Randomizes keyframe attributes on an object with various options

    :param obj: A Maya object/node name
    :type obj: str
    :param attr: A Maya node/object attribute name
    :type attr: str
    :param timeRange: The time range to affect start frame/end frame
    :type timeRange: list(float)
    :param randomRange: the lower and upper values to randomize. The randomize value range.
    :type randomRange: list(float)

    :return keyTimesList: A list of all keyframes in time
    :rtype keyTimesList: list(float)
    :return oldKeyValuesList: A list of the original not changed values, for caching UI purposes
    :rtype oldKeyValuesList: list(float)
    """
    oldKeyValuesList = list()
    randomFloatList = list()
    keyTimesList = timerange.keysInRangeCurve(animCurve, timeRange=timeRange)
    if not keyTimesList:  # Iterate through all keys in the time range
        if message:
            output.displayWarning("No keys found for animation curve `{}`".format(animCurve))
        return keyTimesList, oldKeyValuesList
    for time in keyTimesList:
        oldValue, newValue, randomFloat = randomizeKeyCurve(animCurve, time, randomRange=randomRange)
        oldKeyValuesList.append(oldValue)
        randomFloatList.append(randomFloat)
    return keyTimesList, oldKeyValuesList, randomFloatList


def randomizeKeysObj(obj, attrList, timeRange=[0, 100], randomRange=[-1.0, 1.0], animLayer=""):
    """Randomizes a node given the node name (obj) and the attribute list.

    returns objCurveDict, all the curves of this object and their time and value lists within the range:

        Curve (key), TimeList, ValueList
        {'pCube1_translateX': [[119.0, 120.0], [8.237586020630143, 4.889088181859329]]}

    :param obj: A Maya object/node name
    :type obj: str
    :param attrList: A list of node/object attribute names
    :type attrList: list(str)
    :param timeRange: The time range to affect start frame/end frame
    :type timeRange: list(float)
    :param randomRange: the lower and upper values to randomize. The randomize value range.
    :type randomRange: list(float)
    :param animLayer: A name of a single animation layer
    :type animLayer: str

    :return objCurveDict: Dict of the original animation curves with two lists time and value
    :rtype objCurveDict: dict(str)
    """
    objCurveDict = dict()

    # No animation layers ---------------------
    if not animLayer:  # easy just do the random
        for attr in attrList:
            animCurve, keyTimes, oldKeyValues, randomFloats = randomizeKeysAttrRange(obj, attr, timeRange=timeRange,
                                                                                     randomRange=randomRange)
            if animCurve:
                objCurveDict[animCurve] = [keyTimes, oldKeyValues, randomFloats]
        return objCurveDict

    # Yes selected animation layer -------------------------------
    if not animlayers.isObjectInAnimLayer(obj, animLayer):  # If object is not in the animation layer
        for attr in attrList:
            animCurve, keyTimes, oldKeyValues, randomFloats = randomizeKeysAttrRange(obj, attr, timeRange=timeRange,
                                                                                     randomRange=randomRange)
            if animCurve:
                objCurveDict[animCurve] = [keyTimes, oldKeyValues, randomFloats]
        return objCurveDict

    # Object is a member of the animation layer, so work on animCurves rather than obj/attr --------------------
    for attr in attrList:  # get the anim curve from the object
        animCurve = animlayers.getAnimCurveForLayer(obj, attr, animLayer)
        if not animCurve:  # No anim curve so do nothing
            continue
        # Randomize the animation curve range
        keyTimes, oldKeyValues, randomFloats = randomizeKeysAttrRangeCurve(animCurve, timeRange=timeRange,
                                                                           randomRange=randomRange)
        objCurveDict[animCurve] = [keyTimes, oldKeyValues, randomFloats]

    return objCurveDict


def randomizeKeysObjList(objList, attrList, timeRange=[0, 100], randomRange=[-1.0, 1.0], bake=False,
                         bakeFrequency=1, animLayer=""):
    """Randomizes keyframes on an object list given and attribute list.  Will skip missing, connected or locked attrs.

    Returns objCurveDict, all the curves of this object and their time and value lists within the range:

        Curve (key), TimeList, ValueList
        {'pCube1_translateX': [[119.0, 120.0], [8.237586020630143, 4.889088181859329]]}

    :param objList: A list of Maya object/node names
    :type objList: list(str)
    :param attrList: A list of node/object attribute names
    :type attrList: list(str)
    :param timeRange: The time range to affect start frame/end frame
    :type timeRange: list(float)
    :param randomRange: the lower and upper values to randomize. The randomize value range.
    :type randomRange: list(float)
    :param bake: Bake the time range before randomizing?
    :type bake: bool
    :param bakeFrequency: Every nth frame to bake if bake is True
    :type bakeFrequency: bool
    :param animLayer: A name of a single animation layer
    :type animLayer: str

    :return graphCurveDict: Dict of the original animation curves with two lists time and value
    :rtype graphCurveDict: dict(str)
    """
    graphCurveDict = dict()
    if bake:  # Bake supporting selected animation layers
        bakeanim.bakeAnimationLayers(objList, attrList, timeRange, bakeFrequency, animLayer, message=True)
    for obj in objList:  # Do the randomize
        objCurveDict = randomizeKeysObj(obj, attrList, timeRange=timeRange, randomRange=randomRange,
                                        animLayer=animLayer)
        graphCurveDict = mergeTwoDicts(graphCurveDict, objCurveDict)
    return graphCurveDict


def getKeyValueList(animCurve, keyTimeList):
    """Given a list of times representing keyframes on an animation curve return their values as a matching list

    :param animCurve: An animation curve node name
    :type animCurve: str
    :param keyTimeList: A list of times representing keyframes, will return their values
    :type keyTimeList: list(str)

    :return keyValueList: A list of the original values of the animCurve to match the keyTimList
    :rtype keyValueList: list(float)
    """
    keyValueList = list()
    for keyTime in keyTimeList:
        keyValueList.append(cmds.keyframe(animCurve, query=True, eval=True, time=(keyTime, keyTime))[0])
    return keyValueList


def randomizeKeysGraphCurves(animCurves, randomRange=[-1.0, 1.0]):
    """Randomizes selected animation curve nodes with the given value range (random range)

    :param animCurves: A list of animation curve node names
    :type animCurves: list(str)
    :param randomRange: The value range to randomize
    :type randomRange: list(float)

    :return graphCurveDict: Dict of the original animation curves with two lists time and value
    :rtype graphCurveDict: dict(str)
    """
    graphCurveDict = dict()
    for curve in animCurves:
        randomFloatList = list()
        keyTimeList = cmds.keyframe(curve, query=True, timeChange=True, selected=True)
        keyValueList = getKeyValueList(curve, keyTimeList)
        for time in keyTimeList:
            oldValue, newValue, randomFloat = randomizeKeyCurve(curve, time, randomRange=randomRange)
            randomFloatList.append(randomFloat)
        graphCurveDict[curve] = [keyTimeList, keyValueList, randomFloatList]
    return graphCurveDict


def getCurveDictsKeyTimesSelection(animCurves):
    """Given a list of animation curves will return a startEndCurveDict with curves as keys and key times listed.

    curveKeyTimeDict:
        Curve (key): [TimeList]

    :param animCurves: A list of animation curve node names
    :type animCurves: list(str)

    :return startEndCurveDict: A dictionary of curves as keys and key times as the value
    :rtype: dict(str: list)
    """
    curveKeyTimeDict = dict()
    for curve in animCurves:
        curveKeyTimeDict[curve] = cmds.keyframe(curve, query=True, timeChange=True, selected=True)
    return curveKeyTimeDict


def selectKeysBetweenMinMaxTimes(curveKeyTimeDict):
    """Selects all keys between the min and max times, handy for after baking curves and returning new values.

    curveKeyTimeDict:
        Curve (key): [TimeList]

    :param startEndCurveDict: A dictionary of curves as keys and key times as the value
    :type startEndCurveDict: dict(str: list)
    :return animCurves: The newly selected animation curves in case of changes
    :rtype animCurves: list(str)
    """
    for curve in curveKeyTimeDict.keys():
        cmds.selectKey(curve, time=(curveKeyTimeDict[curve][0], curveKeyTimeDict[curve][-1]), addTo=True)
    animCurves = cmds.keyframe(query=True, name=True, selected=True)
    return animCurves


def randomizeBakeAnimCurves(animCurves, randomRange=[-1.0, 1.0], bake=False, bakeFrequency=1):
    """Randomize with bake option for animation curves only.

    Returns a graphCurveDict of the original key values that the UI can use to recalculate and update the noise:

        Curve (key): [TimeList, ValueList, RandomFloatList]
        {'pCube1_translateX': [[119.0, 120.0], [8.237586020630143, 4.889088181859329], [0.234, 0.932]]}

    :param animCurves: A list of animation curve node names
    :type animCurves: list(str)
    :param randomRange: The min and max range of the randomize value
    :type randomRange: list(float)
    :param bake: Will bake the animation if set to True
    :type bake: bool
    :param bakeFrequency: Will bake every nth frame if bake is True
    :type bakeFrequency: float

    :return graphCurveDict: Dict of the original animation curves with two lists time and value
    :rtype graphCurveDict: dict(str)
    """
    if bake:
        curveKeyTimeDict = getCurveDictsKeyTimesSelection(animCurves)
        bakeanim.bakeAnimCurves(bakeFrequency=bakeFrequency)
        animCurves = selectKeysBetweenMinMaxTimes(curveKeyTimeDict)  # selects the baked keys so they can be randomized
    graphCurveDict = randomizeKeysGraphCurves(animCurves, randomRange=randomRange)
    return graphCurveDict


def randomizeKeyframesSelection(timeRange=[0, 100], randomRange=[-1.0, 1.0], timeSlider=1, bake=False, bakeFrequency=1,
                                message=True):
    """Randomizes keys frames based on selected Channel Box attributes or selected animation curves with bake options.

    Will skip missing, connected or locked attributes.

    Returns a graphCurveDict of the original key values that the UI can use to recalculate and update the noise:

        Curve (key): [TimeList, ValueList, RandomFloatList]
        {'pCube1_translateX': [[119.0, 120.0], [8.237586020630143, 4.889088181859329], [0.234, 0.932]]}

    :param timeRange: The start and end frame, only used if the timeSlider is set to 3 (use custom timerange)
    :type timeRange: list(float)
    :param randomRange: The min and max range of the randomize value
    :type randomRange: list(float)
    :param timeSlider: 0 is playback range, 1 is animation range, 2 is use timeRange kwargs
    :type timeSlider: int
    :param bake: Will bake the animation if set to True
    :type bake: bool
    :param bakeFrequency: Will bake every nth frame if bake is True
    :type bakeFrequency: float
    :param message: Return messages to the user?
    :type message: bool

    :return graphCurveDict: Dict of the original animation curves with two lists time and value
    :rtype graphCurveDict: dict(str)
    """
    selAttrs = list()
    selObj = cmds.ls(selection=True, long=True)
    if not selObj:
        if message:
            output.displayWarning("Please select objects to randomize")
        return dict()
    animCurves = cmds.keyframe(query=True, name=True, selected=True)
    # Do the bake ---------------------
    if animCurves:
        graphCurveDict = randomizeBakeAnimCurves(animCurves, randomRange=randomRange, bake=bake,
                                                 bakeFrequency=bakeFrequency)
        return graphCurveDict
    selShortAttrs = cmds.channelBox('mainChannelBox', query=True, selectedMainAttributes=True) or \
                    cmds.channelBox('mainChannelBox', query=True, selectedHistoryAttributes=True)
    # TODO also support shape node channel box selection
    # Convert Attrs to long attribute names
    if selShortAttrs:
        for i, attr in enumerate(selShortAttrs):  # convert to long names
            selAttrs.append(cmds.attributeName(".".join([selObj[-1], attr]), long=True))
    if not selAttrs:
        if message:
            output.displayWarning("Please select curves or attributes in the channel box to randomize")
        return dict()
    if timeSlider == 0:  # Use the playback range
        timeRange = timerange.getRangePlayback()
    elif timeSlider == 1:  # Use the animation scene range
        timeRange = timerange.getRangeAnimation()
    animLayer = animlayers.firstSelectedAnimLayer(ignoreBaseLayer=True)  # the first selected animation layer if one
    # Do the randomize ---------------------
    graphCurveDict = randomizeKeysObjList(selObj, selAttrs, timeRange=timeRange,
                                          randomRange=randomRange, bake=bake, bakeFrequency=bakeFrequency,
                                          animLayer=animLayer)
    return graphCurveDict


def randomizeKeysGraphSel(randomRange=[-1.0, 1.0], message=True):
    """Randomize selected keys in the graph editor between the randomRange of values.

    Returns a graphCurveDict of the original key values that the UI can use to recalculate and update the noise:

        Curve (key): [TimeList, ValueList, RandomFloatList]
        {'pCube1_translateX': [[119.0, 120.0], [8.237586020630143, 4.889088181859329], [0.234, 0.932]]}

    :param randomRange: The min and max range of the randomize value
    :type randomRange: list(float)
    :param message: Return messages to the user?
    :type message: bool

    :return graphCurveDict: Dict of the original animation curves with two lists time and value
    :rtype graphCurveDict: dict(str)
    """
    selObj = cmds.ls(selection=True, long=True)
    if not selObj:
        if message:
            output.displayWarning("Please select objects to randomize")
        return dict()
    animCurves = cmds.keyframe(query=True, name=True, selected=True)
    if not animCurves:
        if message:
            output.displayWarning("Please select curves or attributes in the channel box to randomize")
        return dict()
    # Do the randomize ---------------------
    graphCurveDict = randomizeKeysGraphCurves(animCurves, randomRange=randomRange)
    return graphCurveDict


class RandomizeKeyframes(object):
    """Class for dealing with scaling keys from the center pivot of each graph curve. Used by UIs
    """

    def __init__(self):
        """Class for dealing with scaling keys from the center pivot of each graph curve. Used by UIs

        Code example:

            from zoo.libs.maya.cmds.animation import randomizeanimation
            instance = randomizeanimation.RandomizeKeyframes()

            instance.setRandomizeScale(2.0) # the value scale of the noise gets converted to [-1.0, 1.0]
            instance.setRandomizeRange([-1.0, 1.0])  # the value scale of the noise
            instance.setTimeSliderMode(3)  # 3 is custom
            instance.setTimeRange([0.0-100.0])  # time in and out, only for channel box randomize

            instance.randomizeAnimCurvesSelection()  # randomizes based on the selected curves
            or
            instance.randomizeChannelBoxSelection()  # randomizes based on the channel box selection

        """
        self.timeRange = [0.0, 100.0]
        self.timeSliderMode = 0
        self.randomizeRange = [-1.0, 1.0]
        self.bakeState = False
        self.bakeFrequency = 1.0
        # auto
        self.cacheDict = dict()
        self.animCurves = list()

    def setRandomizeScale(self, randomizeScale):
        """Sets the range of the value scale as one float value

        :param randomizeScale: The scale value of the randomize 2.0 gets converted to [-1.0, 1.0]
        :type randomizeScale: float
        """
        self.randomizeRange = [-randomizeScale / 2, randomizeScale / 2]

    def setRandomizeRange(self, randomizeRange):
        """The min and max range of the value scale

        :param randomizeRange: Min and max range of the value scale [min, max]
        :type randomizeRange: list(float)
        """
        self.randomizeRange = randomizeRange

    def setBakeFrequency(self, bakeFrequency):
        """Set the bake frequency in frames as a float.  Can only be used with self.bakeState = True

        :param bakeFrequency: Bake every nth frame
        :type bakeFrequency: float
        """
        self.bakeFrequency = bakeFrequency

    def setTimeRange(self, timeRange):
        """Set the time range as two floats. [frameIn, frameOut]
        Note: Only used if self.setTimeSliderMode = 3  # custom frame range

        :param timeRange: Set the frame in and out [frameIn, frameOut]
        :type timeRange: list(float)
        """
        self.timeRange = timeRange

    def setBakeState(self, bakeState):
        """Set the bake state as a boolean. True or False

        :param bakeState: True if to bake in channel box, False is no bake.
        :type bakeState: bool
        """
        self.bakeState = bakeState

    def setTimeSliderMode(self, timeSliderMode):
        """Set the time slider mode options.

        :param timeSliderMode: 0 is playback range, 1 is animation range, 2 is use timeRange kwargs
        :type timeSliderMode: int
        """
        self.timeSliderMode = timeSliderMode

    def clearCache(self):
        """Clears the self.cacheDict and self.animCurves"""
        self.cacheDict = dict()
        self.animCurves = list()

    def cacheExists(self):
        """Returns True if the self.cacheDict contains values, False if not"""
        if self.cacheDict:
            return True
        return False

    def _buildCacheCurves(self):
        """Creates the self.cacheDict from self.animCurves
        """
        randomFloats = list()
        for curve in self.animCurves:
            keyTimeList = cmds.keyframe(curve, query=True, timeChange=True, selected=True)
            keyValueList = getKeyValueList(curve, keyTimeList)
            if keyValueList:
                for v in keyValueList:
                    randomFloats.append(random.random())
            self.cacheDict[curve] = [keyTimeList, keyValueList, randomFloats]

    def buildCacheCurvesSel(self, message=True):
        """Creates the self.cacheDict from the selected animation curves

        :param message: Report a message to the user?
        :type message: bool
        """
        selObj = cmds.ls(selection=True, long=True)
        if not selObj:
            if message:
                output.displayWarning("Please select objects to randomize")
            self.clearCache()
            return
        self.animCurves = cmds.keyframe(query=True, name=True, selected=True)
        if not self.animCurves:
            if message:
                output.displayWarning("Please select curves or attributes in the channel box to randomize")
            self.clearCache()
            return
        self._buildCacheCurves()

    def randomizeAnimCurvesSelection(self):
        """Randomizes the animation curves based on selected animation curves"""
        self.cacheDict = randomizeKeysGraphSel(randomRange=self.randomizeRange, message=True)
        self.animCurves = self.cacheDict.keys()

    def randomizeKeysSelection(self):
        """Main function that randomizes animation based on the selected objects/attr or curves"""
        self.cacheDict = randomizeKeyframesSelection(timeRange=self.timeRange,
                                                     randomRange=self.randomizeRange,
                                                     timeSlider=self.timeSliderMode,
                                                     bake=self.bakeState,
                                                     bakeFrequency=self.bakeFrequency,
                                                     message=True)
        if self.cacheDict:
            self.animCurves = self.cacheDict.keys()
        else:
            self.animCurves = list()

    def resetKeys(self):
        """Resets all keys to original positions in the cache"""
        if not self.cacheDict:
            return
        for animCurve in self.animCurves:
            for i, keyTime in enumerate(self.cacheDict[animCurve][0]):
                # return to old values
                cmds.keyframe(animCurve, valueChange=self.cacheDict[animCurve][1][i], time=(keyTime, keyTime))

    def randomizeKeysFromCache(self):
        """Randomizes the current cache based on the current settings"""
        if not self.cacheDict:
            return
        rangeDiff = self.randomizeRange[-1] - self.randomizeRange[0]
        minRange = self.randomizeRange[0]
        for animCurve in self.animCurves:
            for i, keyTime in enumerate(self.cacheDict[animCurve][0]):
                randomFloat = self.cacheDict[animCurve][2][i]
                origValue = self.cacheDict[animCurve][1][i]
                newValue = (rangeDiff * randomFloat) + (origValue + minRange)
                cmds.keyframe(animCurve, valueChange=newValue, time=(keyTime, keyTime))

    def reSeedKeys(self):
        """Performs the randomize again with a new random seed"""
        if not self.cacheDict:
            return
        for animCurve in self.animCurves:  # for all the random values recalculate the random seed
            for i, v in enumerate(self.cacheDict[animCurve][2]):
                self.cacheDict[animCurve][2][i] = random.random()
        self.randomizeKeysFromCache()  # Perform the randomize
