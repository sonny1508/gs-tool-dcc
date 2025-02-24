"""Small window popup with the Tween Machine UI

Example use:

.. code-block:: python

    from zoo.apps.popupuis import tweenpopup
    tweenpopup.main()

Zoo UI Author: Andrew Silke
Tween Machine Logic: Justin S Barrett, mods by Wade Schneider and Andrew Silke

Free Version: https://github.com/The-Maize/tweenMachine
Logic License: MIT, see zoo.libs.tweenmachine.LICENSE
"""

from functools import partial

from maya import cmds

from zoo.core import engine
from zoo.libs.utils import output
from zoovendor.Qt import QtCore, QtGui
from zoo.libs.pyqt.widgets import elements
from zoo.libs.pyqt import uiconstants as uic, utils

try:
    from zoo.libs.tweenmachine import tweenmachine
except:
    tweenmachine = None
    output.displayWarning("Tween Machine Logic was not found in Community Scripts, so this UI cannot be used.")

WINDOW_WIDTH = 390
WINDOW_HEIGHT = 80

WINDOW_OFFSET_X = utils.dpiScale(int(-WINDOW_WIDTH / 2))
WINDOW_OFFSET_Y = utils.dpiScale(-10)
SLIDER_OFFSET_X = utils.dpiScale(int(-WINDOW_WIDTH / 2) - 30)
SLIDER_OFFSET_Y = utils.dpiScale(-40)


class TweenPopup(elements.ZooWindowThin):

    def __init__(self, name="", title="", parent=None, resizable=True, width=WINDOW_WIDTH, height=WINDOW_HEIGHT,
                 modal=False, alwaysShowAllTitle=False, minButton=False, maxButton=False, onTop=False,
                 saveWindowPref=False, titleBar=None, overlay=True, minimizeEnabled=True, initPos=None, qtPopup=False,
                 closeOnRelease=True):
        super(TweenPopup, self).__init__(name, title, parent, resizable, width, height, modal, alwaysShowAllTitle,
                                         minButton, maxButton, onTop, saveWindowPref, titleBar, overlay,
                                         minimizeEnabled, initPos)
        self.closeOnRelease = closeOnRelease
        if qtPopup:
            self.parentContainer.setWindowFlags(self.parentContainer.defaultWindowFlags | QtCore.Qt.Popup)
        try:
            self.tweenInstance = tweenmachine.TweenMachine()
        except:
            self.tweenInstance = None
            self.notInstalled()
        self.widgets()
        self.layout()
        self.connections()
        self.count = 0  # hack count for textModified triggering twice

    def enterEvent(self, event):
        """Update selection on enter event
        """
        if not self.tweenInstance:
            self.notInstalled()
            return
        self.tweenInstance.tweenSel(self.tweenFloatSlider.value(), start=False, message=False)  # cache & do nothing

    def leaveEvent(self, event):
        if not self.tweenInstance:
            self.notInstalled()
            return
        self.tweenInstance.clearCache()  # resets for next session

    def notInstalled(self):
        output.displayWarning("Tween Machine Logic was not found in Community Scripts, so this UI cannot be used.")

    # -------------
    # COMMANDS
    # -------------

    def tweenSliderPressed(self):
        """Start the tween"""
        cmds.undoInfo(openChunk=True)
        self.tweenInstance.pressed = True

    def tweenSliderMoved(self):
        """When the slider is moved.
        """
        self.tweenInstance.tween(self.tweenFloatSlider.value())  # main tween on the existing cache

    def tweenSliderReleased(self):
        """After the slider is released finish the instance"""
        self.tweenInstance.successMessage()
        self.tweenInstance.keyStaticCurves()  # keys other curves that did not need value calculations.
        self.tweenInstance.pressed = False
        cmds.undoInfo(closeChunk=True)
        if self.closeOnRelease:
            self.close()

    def tweenTextChanged(self):
        """Slider text changed"""
        self.count += self.count
        if self.count == 0:
            self.count = 1  # Hack as is triggering twice, will trigger on second go.
            return
        self.tweenInstance.tweenCachedDataOnce(self.tweenFloatSlider.value())

    def updateSlider(self, bias):
        """Resets all float sliders to be zero, triggered after using"""
        self.tweenFloatSlider.blockSignals(True)
        self.tweenFloatSlider.setValue(bias)
        self.tweenFloatSlider.blockSignals(False)

    def tweenSetBias(self, bias):
        """Btn ruler ticks clicked"""
        self.updateSlider(bias)
        self.tweenInstance.tweenCachedDataOnce(bias)

    # -------------
    # CONNECTIONS
    # -------------

    def connections(self):
        """Connect the ui to logic"""
        if not self.tweenInstance:
            return
        self.tweenFloatSlider.sliderPressed.connect(self.tweenSliderPressed)
        self.tweenFloatSlider.sliderReleased.connect(self.tweenSliderReleased)
        self.tweenFloatSlider.numSliderChanged.connect(self.tweenSliderMoved)
        self.tweenFloatSlider.textModified.connect(self.tweenTextChanged)
        bias = -0.25
        for btn in self.tweenTickBtns:
            btn.clicked.connect(partial(self.tweenSetBias, bias=bias))
            bias += 0.125

    # -------------
    # CREATE WIDGETS
    # -------------

    def widgets(self):
        """Build the widgets"""
        # Tween Slider ---------------------------------------
        tooltip = "Blends the selected animated object between the next & previous keyframes. \n" \
                  "Select objects with keys and run.  Keys the current frame. \n" \
                  "Tween Machine is by Justin Barrett, updated by Wade Schneider & Andrew Silke \n" \
                  "github.com/The-Maize/tweenMachine"
        self.tweenFloatSlider = elements.FloatSlider(label="Tween",
                                                     defaultValue=0.5,
                                                     toolTip=tooltip,
                                                     sliderMin=-0.2,
                                                     sliderMax=1.2,
                                                     sliderRatio=3,
                                                     labelBtnRatio=1,
                                                     labelRatio=1,
                                                     editBoxRatio=2,
                                                     dynamicMin=True,
                                                     dynamicMax=True)
        # Tick Buttons Below Slider ---------------------------------------
        startValue = -0.25
        self.tweenTickBtns = list()
        for x in range(0, 13):
            toolTip = "{}".format(str(startValue))
            icon = "verticalBarThin" if (x % 2) else "verticalBar"  # thin if odd
            if startValue in [0.0, 0.5, 1.0]:
                height = 10
            else:
                height = 6 if (x % 2) else 6  # thin if odd
            self.tweenTickBtns.append(elements.styledButton("", icon,
                                                            toolTip=toolTip,
                                                            style=uic.BTN_TRANSPARENT_BG,
                                                            iconSize=8,
                                                            maxWidth=20,
                                                            btnHeight=height))
            startValue += 0.125

    # -------------
    # LAYOUT UI
    # -------------

    def layout(self):
        """Layout the widgets into the window"""
        mainLayout = elements.vBoxLayout(spacing=0,
                                         margins=(uic.REGPAD, uic.REGPAD, uic.REGPAD, uic.REGPAD))
        # Spacer layout ---------------------
        blankLayout = elements.hBoxLayout(spacing=0)
        blankLayout.addItem(elements.Spacer(1, 1))  # nothing
        # Ticks inside layout ---------------------
        tickLayout = elements.hBoxLayout(margins=(0, 0, 0, 0), spacing=0)

        for btn in self.tweenTickBtns:
            tickLayout.addWidget(btn, 1)
            tickLayout.setAlignment(btn, QtCore.Qt.AlignTop)
        # Ticks row layout ---------------------
        tickRowLayout = elements.hBoxLayout(spacing=0)
        tickRowLayout.addLayout(blankLayout, 34)
        tickRowLayout.addLayout(tickLayout, 100)
        # Vertical layout with no spacing between slider and ticks ---------------------
        sliderLayout = elements.vBoxLayout(spacing=0)
        sliderLayout.addWidget(self.tweenFloatSlider)
        sliderLayout.addLayout(tickRowLayout)
        # Add To Main Layout ---------------------------------------
        mainLayout.addLayout(sliderLayout)
        self.setMainLayout(mainLayout)


def main(cursorOnSlider=False, clickOffClose=False, closeOnRelease=False):
    """Opens the mini popup version of the Tween Machine tool.

    :param cursorOnSlider: If True opens window with the mouse pointer on the slider instead of the window bar.
    :type cursorOnSlider: bool
    :param clickOffClose: If True clicking off the window will close it. False the window will stay open.
    :type clickOffClose: bool
    :param clickOffClose: If True releasing the slider mouse will close the window acting like a marking menu.
    :type clickOffClose: bool"""
    eng = engine.currentEngine()
    win = eng.showDialog(TweenPopup, name="tweenPopup", allowsMultiple=False, qtPopup=clickOffClose,
                         closeOnRelease=closeOnRelease)  # Zoo open and manage window.

    point = QtGui.QCursor.pos()

    if cursorOnSlider:
        point.setX(point.x() + SLIDER_OFFSET_X)
        point.setY(point.y() + SLIDER_OFFSET_Y)
    else:
        point.setX(point.x() + WINDOW_OFFSET_X)
        point.setY(point.y() + WINDOW_OFFSET_Y)
    win.show(point)
    output.displayInfo("Tween Machine Popup Opened")


if __name__ == "__main__":
    main()
