"""

from zoo.libs.maya.cmds.animation import bakeanim
bakeanim.bakeLimitKeysToTimerangeSel(0.0, 10.0, message=True)
"""

import maya.cmds as cmds

from zoo.libs.utils import output
from zoo.libs.maya.utils import mayaenv
from zoo.libs.maya.cmds.objutils import attributes
from zoo.libs.maya.cmds.animation import animlayers, timerange, animobjects

MAYA_VERSION = float(mayaenv.mayaVersionNiceName())

# -------------------
# BAKE KEYFRAME AND ANIMATION
# -------------------


def bakeDifferentLayers(objList, attrList, animLayer, timeRange, bakeFrequency, shapes=False):
    """Bake objects when some objects are not in the first selected animation layer.

    :param objList: A list on Maya objects
    :type objList: list(str)
    :param attrList: A list of Maya attribute names
    :type attrList: list(str)
    :param animLayer: Usually the selected animation layer name
    :type animLayer: str
    :param timeRange: The time range to bake [start frame, end frame]
    :type timeRange: list(float)
    :param bakeFrequency: Bake every nth frame
    :type bakeFrequency: float
    """
    animLayerObjList = list()
    noAnimLayerObjList = list()
    for obj in objList:
        if animlayers.isObjectInAnimLayer(obj, animLayer):
            animLayerObjList.append(obj)
        else:
            noAnimLayerObjList.append(obj)
    # Bake objects in the animation layer in one batch
    if animLayerObjList:  # May not be any objects in the list
        if not attrList:
            cmds.bakeResults(animLayerObjList, time=(timeRange[0], timeRange[-1]),
                             simulation=True, preserveOutsideKeys=True, sampleBy=bakeFrequency,
                             destinationLayer=animLayer, resolveWithoutLayer=False, shape=shapes)
        else:
            cmds.bakeResults(animLayerObjList, attribute=attrList, time=(timeRange[0], timeRange[-1]),
                             simulation=True, preserveOutsideKeys=True, sampleBy=bakeFrequency,
                             destinationLayer=animLayer, resolveWithoutLayer=False, shape=shapes)
    if noAnimLayerObjList:
        # Bake objects to the base layer in one batch
        if not attrList:
            cmds.bakeResults(noAnimLayerObjList, time=(timeRange[0], timeRange[-1]),
                             simulation=True, preserveOutsideKeys=True, sampleBy=bakeFrequency, shape=shapes)
        else:
            cmds.bakeResults(noAnimLayerObjList, attribute=attrList, time=(timeRange[0], timeRange[-1]),
                             simulation=True, preserveOutsideKeys=True, sampleBy=bakeFrequency, shape=shapes)


def keyProxiesNoKeys(objList, time):
    """Keys proxies if there are no keys on the proxy attributes.  Fix for versions earlier than 2024.

    :param objList: A list on Maya objects.
    :type objList: list(str)
    :param time: The time to set a keyframe.
    :type time: float
    """
    for obj in objList:
        proxyAttrs = attributes.proxyAttributes(obj)
        if proxyAttrs:
            for attr in proxyAttrs:
                if cmds.keyframe(obj, attribute=attr, query=True):  # check if there's already a keyframe on the attr
                    continue
                cmds.setKeyframe(obj, attribute=attr, time=time)  # set keyframe


def bakeAnimationLayers(objList, attrList, timeRange, bakeFrequency, animLayer, shapes=True, message=True):
    """Automatically bakes animation to the given anim layer, or on the base layer if objects aren't members

    Will intelligently bake by batching objects into one bake as much as possibly to keep efficiency.

    :param objList: A list on Maya objects
    :type objList: list(str)
    :param attrList: A list of Maya attribute names
    :type attrList: list(str)
    :param timeRange: The time range to bake [start frame, end frame]
    :type timeRange: list(float)
    :param bakeFrequency: Bake every nth frame
    :type bakeFrequency: float
    :param animLayer:
    :type animLayer:
    :param message: Report the message to the user
    :type message: bool
    """
    # No attribute list so bake all attrs and check for shapes bool ----------------------------
    if not attrList:  # Then add all keyable attributes
        # Get all proxy attributes if there are any and key them.
        if MAYA_VERSION < 2024.0:  # Bugs in versions before 2024, must key all proxies before baking.
            keyProxiesNoKeys(objList, timeRange[0])

        if not animLayer:
            cmds.bakeResults(objList, shape=shapes, time=(timeRange[0], timeRange[-1]),
                             simulation=True, preserveOutsideKeys=True, sampleBy=bakeFrequency)
            return
        elif animlayers.noObjectsInAnimLayer(objList, animLayer):  # no object in the anim layer
            cmds.bakeResults(objList, shape=shapes, time=(timeRange[0], timeRange[-1]),
                             simulation=True, preserveOutsideKeys=True, sampleBy=bakeFrequency)
            return
        elif animlayers.allObjectsInAnimLayer(objList, animLayer):  # all objs are in th layer
            bakeDifferentLayers(objList, attrList, animLayer, timeRange, bakeFrequency, shapes=shapes)
            return
        else:
            if message:
                output.displayWarning("All objects are not in the same animation layer, baking individually")
            bakeDifferentLayers(objList, attrList, animLayer, timeRange, bakeFrequency, shapes=shapes)
        return

    # Attributes are specified ------------------------------------------------------
    if not animLayer:  # Then bake to the base layer (no layer)
        cmds.bakeResults(objList, attribute=attrList, time=(timeRange[0], timeRange[-1]),
                         simulation=True, preserveOutsideKeys=True, sampleBy=bakeFrequency)
        return
    # Anim Layer selected so check if all objects are in the animation layer, if so can bake to that layer
    if animlayers.allObjectsInAnimLayer(objList, animLayer):  # All objs are in the animation layer
        cmds.bakeResults(objList, attribute=attrList, time=(timeRange[0], timeRange[-1]),
                         simulation=True, preserveOutsideKeys=True, sampleBy=bakeFrequency,
                         destinationLayer=animLayer, resolveWithoutLayer=False)
        return
    # All objects are not in the current selected animation layer so will have to split the bake batches
    if animlayers.noObjectsInAnimLayer(objList, animLayer):  # no objects are in the animLayer so bake as normal
        cmds.bakeResults(objList, attribute=attrList, time=(timeRange[0], timeRange[-1]),
                         simulation=True, preserveOutsideKeys=True, sampleBy=bakeFrequency)
        return
    # Some objects are in the animLayer, so bake each set separately
    if message:
        output.displayWarning("All objects are not in the same animation layer, baking individually")
    bakeDifferentLayers(objList, attrList, animLayer, timeRange, bakeFrequency)


def bakeAnimCurves(bakeFrequency=1):
    """Bakes animation curves with frequency

    :param bakeFrequency: Bakes every nth frame
    :type bakeFrequency: float
    """
    cmds.bakeResults(simulation=False, preserveOutsideKeys=True,
                     sampleBy=bakeFrequency, sparseAnimCurveBake=False)


def bakeSelectedChannelBox(timeRange=[0, 0], timeSlider=1, bakeFrequency=1, shapes=False, message=True):
    """Intelligently bakes keyframes with a frequency option, channel selection and supports selected animation layers

        - Bakes selected objects
        - Uses channel box selection to restrict attributes, otherwise will bake all
        - Handles user selected animation layers
        - Batches objects where possible for speed

    :param timeRange: The start and end frame, only used if the timeSlider is set to 3 (use custom timerange)
    :type timeRange: list(float)
    :param timeSlider: 0 is playback range, 1 is animation range, 2 is use timeRange kwargs
    :type timeSlider: int
    :param bakeFrequency: Will bake every nth frame if bake is True
    :type bakeFrequency: float
    :param message: Return messages to the user?
    :type message: bool
    """
    selObj = cmds.ls(selection=True, long=True)
    if not selObj:
        if message:
            output.displayWarning("Please select objects to bake.")
        return
    attrs = cmds.channelBox('mainChannelBox', query=True, selectedMainAttributes=True) or \
            cmds.channelBox('mainChannelBox', query=True, selectedHistoryAttributes=True)
    # TODO also support shape node channel box selection
    if timeSlider == 0:  # Use the playback range
        timeRange = timerange.getSelectedFrameRangeOrPlayback()  # Get selected or playback range
    elif timeSlider == 1:  # Use the animation scene range
        timeRange = timerange.getRangeAnimation()
    animLayer = animlayers.firstSelectedAnimLayer(ignoreBaseLayer=True)  # get the first selected animation layer
    # Do the bake
    bakeAnimationLayers(selObj, attrs, timeRange, bakeFrequency, animLayer, shapes=shapes, message=message)


def bakeSelected(timeRange=[0, 0], timeSlider=1, bakeFrequency=1, shapes=False, message=True):
    """Bakes animation keyframes using bake curves or bake simulation depending on the selection and settings.

    Bake Animation based on selection:

        1. Graph keyframe selection. (Time Range is ignored)
        2. Channel Box selection.
        3. If nothing is selected will bake all attributes.

    :param timeRange: The start and end frame, only used if the timeSlider is set to 3 (use custom timerange)
    :type timeRange: list(float)
    :param timeSlider: 0 is playback range, 1 is animation range, 2 is use timeRange kwargs
    :type timeSlider: int
    :param bakeFrequency: Will bake every nth frame if bake is True
    :type bakeFrequency: float
    :param message: Return messages to the user?
    :type message: bool
    """
    selObj = cmds.ls(selection=True, long=True)
    if not selObj:
        if message:
            output.displayWarning("Please select objects to bake.")
        return
    animCurves = cmds.keyframe(query=True, name=True, selected=True)
    # Do the bake ---------------------
    if animCurves:
        bakeAnimCurves(bakeFrequency=bakeFrequency)
        return
    # No curves selected so work on the channel box or all attributes.
    bakeSelectedChannelBox(timeRange=timeRange, timeSlider=timeSlider, bakeFrequency=bakeFrequency,
                           shapes=shapes, message=message)


def bakeLimitKeysToTimerange(start, end, objAttrList):
    """Limits keys to timerange (deletes keys outside) cmds.bakeResults gives incorrect results on the in/out tangents.

    objAttrList: can be ["object.attribute"] or the animation curves themselves ["object_attribute"]

    :param start: The start frame of the time range
    :type start: float
    :param end: The end frame of the time range
    :type end: float
    :param objAttrList: A list of obj.attr animation curves. ["pCube1.translateX", "pCube1.translateY"]
    :type objAttrList: list(str)
    """
    # bake results two times before and after start end to be safe.
    cmds.bakeResults(objAttrList,
                     sampleBy=1,
                     time=(start - end * 2, end * 3),
                     preserveOutsideKeys=True,
                     sparseAnimCurveBake=True)
    # set keys on the start and end frames
    cmds.setKeyframe(objAttrList, insert=True, time=(start, end))
    # remove keys before the start and end
    cmds.cutKey(objAttrList, time=("{}:".format(str(end + .001)),))
    cmds.cutKey(objAttrList, time=(":{}".format(str(start - .001)),))


def bakeLimitKeysToTimerangeSel(start, end, message=True):
    """

    :param start:
    :type start:
    :param end:
    :type end:
    :param message:
    :type message:
    :return:
    :rtype:
    """
    animCurves, objAttrs, selObjs = animobjects.animSelection()
    if not selObjs:
        if message:
            output.displayWarning("Nothing selected.  Please select objects, nodes, curves or channel box selection.")
        return
    if animCurves:
        bakeLimitKeysToTimerange(start, end, animCurves)
    elif objAttrs:
        bakeLimitKeysToTimerange(start, end, objAttrs)
    elif selObjs:
        if message:
            output.displayWarning("No animation found on the selected nodes/objects.")
        return
    if message:
        output.displayInfo("Success: Animation curves baked and limited start frame {} to {}".format(start, end))
