"""Tweener (tween machine) logic
Modified from code from the original Tween Machine by Justin Barrett.
Logic License: MIT, see zoo.libs.tweenmachine.LICENSE

Example use:

.. code-block:: python

    from zoo.libs.maya.cmds.animation import tweenmachine
    tweenInst = tweenmachine.TweenMachine()  # start instance
    tweenInst.tweenSel(self.tweenFloatSlider.value(), start=False, message=False)  # start cache & do nothing

    # tween attached to a slider
    tweenInst.tween(0.5)  # ui modification on cached data, for sliders, doesn't finish only changes active keys.
    # finalize slider released
    tweenInst.successMessage()
    tweenInst.keyStaticCurves()  # keys other curves that did not need value calculations.
    tweenInst.pressed = False

    # tween from a button
    tweenInst.tweenCachedDataOnce(0.75)  # do the tween once and finish (key static channels) based off the data

    # Reset cache mouse leaves UI
    tweenInst.clearCache()  # resets cache for next session


Author: Justin S Barrett, updates by Wade Schneider and Andrew Silke
Free Version: https://github.com/The-Maize/tweenMachine

License: MIT
https://github.com/The-Maize/tweenMachine/blob/master/LICENSE
"""

import maya.cmds as cmds
from zoo.libs.utils import output
from zoo.libs.maya.cmds.animation import animobjects


class TweenMachine(object):
    """Class for managing the tweener logic.
    """

    def __init__(self):
        """
        """
        super(TweenMachine, self).__init__()
        self.currentFrame = 0.0
        self.pressed = False
        self.bias = 0.5
        self.nodes = list()
        self.curves = list()
        self.staticCurves = list()
        self.values_prev = list()
        self.values_next = list()
        self.out_tans_new = list()
        self.in_tans_new = list()

    def getCurves(self):
        """Gets all the animation curves in the scene based on selection and channel box filtering.

        :param nodes: A list of maya node names
        :type nodes: str()
        :return: a list of animation curves
        :rtype: list(str)
        """
        # Check for anim curve selection ---------------------
        animCurves = cmds.keyframe(q=True, name=True, selected=True)
        if animCurves:
            self.curves = animCurves
            return

        if isinstance(self.nodes, list) and not self.nodes:
            self.nodes = None

        # Figure out which nodes to pull from
        if self.nodes is not None:
            pullfrom = self.nodes
        else:
            pullfrom = cmds.ls(sl=True)
            if not pullfrom:
                return

        # If attributes are selected in channel box, use them to build curve node list
        attributes = cmds.channelBox("mainChannelBox", q=True, sma=True)
        if attributes:
            self.curves = []
            for attr in attributes:
                for node in pullfrom:
                    nameAttr = ".".join([node, attr])
                    if not cmds.objExists(nameAttr):
                        continue
                    tmp = cmds.keyframe(nameAttr, q=True, name=True)
                    if not tmp:
                        continue
                    self.curves += tmp
        # Otherwise get curves for all nodes
        else:
            self.curves = cmds.keyframe(pullfrom, q=True, name=True)

    def _findInOutTangents(self, curve, time_prev, time_next):
        """Returns the in and out tangent types (strings) of the new key to be created at the current time.

        :param curve: A single animation curve name to extract the data.
        :type curve: str
        :param time_prev: the key on the previous frame
        :type time_prev: float
        :param time_next: the key on the next frame
        :type time_next: float
        :return: The incoming new tangent and the outgoing tangent types.
        :rtype: tuple(str, str)
        """
        in_tan_prev = cmds.keyTangent(curve, time=(time_prev,), q=True, itt=True)[0]
        out_tan_prev = cmds.keyTangent(curve, time=(time_prev,), q=True, ott=True)[0]
        in_tan_next = cmds.keyTangent(curve, time=(time_next,), q=True, itt=True)[0]
        out_tan_next = cmds.keyTangent(curve, time=(time_next,), q=True, ott=True)[0]
        # Set new in and out tangent types
        in_tan_new = out_tan_prev
        out_tan_new = in_tan_next
        # However, if any of the types (previous or next) is "fixed", use the global (default) tangent instead
        if "fixed" in [in_tan_prev, out_tan_prev, in_tan_next, out_tan_next]:
            in_tan_new = cmds.keyTangent(q=True, g=True, itt=True)[0]
            out_tan_new = cmds.keyTangent(q=True, g=True, ott=True)[0]
        elif out_tan_next == "step":
            out_tan_new = out_tan_next
        return in_tan_new, out_tan_new

    def cacheCurveData(self):
        """From self.curves, find the keyframes either side and their tangent types.

        Sets four lists with each entry matching each animation curve:

            self.values_prev: the values of the previous keyframes: list(float or None)
            self.values_next: the values of the next keyframes: list(float or None)
            self.out_tans_new: the tangent types of the out keyframes: list(str or None)
            self.in_tans_new: the tangent types of the in keyframes: list(str or None)

        Also separates curves into two lists:

            self.curves: Matches the data, prev/next frame values don't match. These need to be tweened.
            self.staticCurves: Curves where the prev/next frames match, so handle them on release, no need for tween.

        """
        validCurves = list()
        for i, curve in enumerate(self.curves):
            # Find time for next and previous keys...
            time_prev = cmds.findKeyframe(curve, which="previous")
            time_next = cmds.findKeyframe(curve, which="next")

            # Find previous and next key values
            value_prev = cmds.keyframe(curve, time=(time_prev,), q=True, valueChange=True)[0]
            value_next = cmds.keyframe(curve, time=(time_next,), q=True, valueChange=True)[0]
            if value_prev == value_next:
                self.staticCurves.append(curve)
                continue
            validCurves.append(curve)
            self.values_prev.append(value_prev)
            self.values_next.append(value_next)

            # Find previous and next tangent types ------------------------------------------
            in_tan_new, out_tan_new = self._findInOutTangents(curve, time_prev, time_next)
            self.in_tans_new.append(in_tan_new)
            self.out_tans_new.append(out_tan_new)

        self.curves = validCurves

    def clearCache(self):
        """Resets all variables to be None or defaults.
        """
        self.currentFrame = 0.0
        self.pressed = False
        self.bias = 0.5
        self.nodes = list()
        self.curves = list()
        self.staticCurves = list()
        self.values_prev = list()
        self.values_next = list()
        self.out_tans_new = list()
        self.in_tans_new = list()

    def tween(self, bias, setInbetweenKey=False):
        """Main method that performs the tween based on the bias amount. Operates on cached data matching lists:

            self.currentFrame: the current time in the timelsider
            self.curves: The curve list with value differences between prev and next keys
            self.values_prev: the values of the previous keyframes: list(float or None)
            self.values_next: the values of the next keyframes: list(float or None)
            self.out_tans_new: the tangent types of the out keyframes: list(str or None)
            self.in_tans_new: the tangent types of the in keyframes: list(str or None)

        :param bias: The value of the tween, 0.5 sets a value halfway between the last and next keyframe values
        :type bias: float
        """
        if not self.pressed or not self.nodes:  # self.pressed is for disabling while caching, nodes must be present.
            return
        self.bias = bias
        for i, curve in enumerate(self.curves):
            value_new = self.values_prev[i] + ((self.values_next[i] - self.values_prev[i]) * self.bias)
            # Set new keyframe and tangents
            cmds.setKeyframe(curve, t=(self.currentFrame,), v=value_new, ott=self.out_tans_new[i])
            if self.in_tans_new[i] == "step" or self.in_tans_new[i]:
                continue
            cmds.keyTangent(curve, t=(self.currentFrame,), itt=self.in_tans_new[i])
            if setInbetweenKey:  # set the key tick to be green
                cmds.keyframe(curve, tds=True, t=(self.currentFrame,))  # key tick green
        cmds.currentTime(self.currentFrame, update=True)  # update viewport

    def keyStaticCurves(self):
        """Keys any curves that need no changes, keys at current value and with correct tangent types

            keys curves at current frame: self.staticCurves

        """
        if not self.staticCurves:
            return
        for curve in self.staticCurves:
            time_prev = cmds.findKeyframe(curve, which="previous")
            time_next = cmds.findKeyframe(curve, which="next")
            in_tan_new, out_tan_new = self._findInOutTangents(curve, time_prev, time_next)
            cmds.setKeyframe(curve, t=(self.currentFrame,), ott=out_tan_new)
            if in_tan_new == "step":
                continue
            cmds.keyTangent(curve, t=(self.currentFrame,), itt=in_tan_new)

    def successMessage(self):
        """Success message should be called just before clearing the cache"""
        if self.curves or self.staticCurves:
            output.displayInfo("Success: Keys tweened by {}".format(str(self.bias)))

    def tweenNodes(self, start=True, message=True):
        """Do the tween on the self.nodes list, uses self.bias (float) as the driver value.

        :param start: Start the tween, if False can be used for caching data. Mouse enter of a UI.
        :type start: bool
        :param message: Report a message to the user?
        :type message: bool
        """
        self.currentFrame = cmds.currentTime(query=True)
        # cmds.waitCursor(state=True)
        self.getCurves()  # sets self.curves
        self.cacheCurveData()  # sets self.values_prev, self.values_next, self.out_tans_new, self.in_tans_new
        if not start:
            # cmds.waitCursor(state=False)
            return
        # Wrap the main operation in a try/except to prevent the waitcursor from sticking if something should fail
        if self.curves is None:
            if message:
                output.displayWarning("No animation curves were found to operate on.")
            return
        try:
            self.pressed = True
            self.tween(self.bias)
        except:
            raise
        finally:
            # cmds.waitCursor(state=False)
            cmds.currentTime(self.currentFrame, update=True)

    def tweenSel(self, bias, start=True, message=True):
        """Do the tween on the selected items, uses self.bias (float) as the driver value.

        :param start: Start the tween, if False can be used for caching data. Eg. When the mouse enters the UI.
        :type start: bool
        :param message: Report a message to the user?
        :type message: bool
        """
        self.bias = bias
        self.nodes = cmds.ls(selection=True)
        if not self.nodes:
            if message:
                output.displayWarning("Nothing is selected, please select animated objects.")
            return
        self.nodes = animobjects.filterAnimatedNodes(self.nodes)
        if not self.nodes:
            if message:
                output.displayWarning("Selected nodes do not contain animation, please select animated objects.")
            return
        self.tweenNodes(start=start, message=True)

    def tweenCachedDataOnce(self, bias):
        """Method that applies the cached data once, useful for UIs and buttons or text changed, not sliders"""
        self.bias = bias
        self.currentFrame = cmds.currentTime(query=True)
        try:
            # cmds.waitCursor(state=True)
            self.pressed = True
            self.tween(self.bias)  # main tween on the existing cache
            self.keyStaticCurves()  # keys other curves that did not need value calculations.
        except:
            raise
        finally:
            self.pressed = False
            # cmds.waitCursor(state=False)
            cmds.currentTime(self.currentFrame, update=True)
