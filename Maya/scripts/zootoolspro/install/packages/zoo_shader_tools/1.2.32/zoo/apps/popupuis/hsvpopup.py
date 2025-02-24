"""

from zoo.apps.popupuis import hsvpopup
hsvpopup.main()

"""

from maya import cmds

from zoovendor.Qt import QtCore, QtGui
from zoo.libs.pyqt.widgets import elements
from zoo.libs.pyqt import uiconstants as uic
from zoo.apps.toolsetsui.toolsetcallbacks import SelectionCallbacksMaya

from zoo.libs.maya.utils import general
from zoo.libs.maya.cmds.shaders import shaderhsv, shadermulti, shdmultconstants as sc

WINDOW_WIDTH = 340
WINDOW_HEIGHT = 180

WINDOW_OFFSET_X = int(-WINDOW_WIDTH / 2)
WINDOW_OFFSET_Y = -10


class HsvPopop(elements.ZooWindowThin):

    def __init__(self, name="", title="", parent=None, resizable=True, width=WINDOW_WIDTH, height=WINDOW_HEIGHT,
                 modal=False, alwaysShowAllTitle=False, minButton=False, maxButton=False, onTop=False,
                 saveWindowPref=False, titleBar=None, overlay=True, minimizeEnabled=True, initPos=None, qtPopup=False):
        super(HsvPopop, self).__init__(name, title, parent, resizable, width, height, modal, alwaysShowAllTitle,
                                       minButton, maxButton, onTop, saveWindowPref, titleBar, overlay,
                                       minimizeEnabled, initPos)
        if qtPopup:
            self.parentContainer.setWindowFlags(self.parentContainer.defaultWindowFlags | QtCore.Qt.Popup)

        self.shaderAttrs = list()
        self.shadersSet = False  # state tracker for the hsv instance
        self.widgets()
        self.diffuseColorSldr.setColorLinearFloat(self.firstShaderColor())  # sets color as rendering space color.
        self.layout()
        self.connections()

    def firstShaderColor(self):
        """Returns the first color from the selection, or mid grey in rendering space"""
        shdrInsts = shadermulti.shaderInstancesFromSelected(message=False)
        if not shdrInsts:
            return [0.5, 0.5, 0.5]
        for shdrInst in shdrInsts:
            shaderDict = shdrInst.connectedAttrs()
            if shaderDict:
                if sc.DIFFUSE in shaderDict:
                    continue
            return shdrInst.diffuse()  # returns the first legit diffuse col found
        return [0.5, 0.5, 0.5]  # no legit colors found

    def resetSliders(self):
        """Resets all float sliders to be zero, triggered after using"""
        for slider in self.floatSliderList:
            slider.blockSignals(True)
            slider.setValue(0.0)
            slider.blockSignals(False)

    def selectionChanged(self, selection):
        """Triggered when the selection changes, update the color slider"""
        if not selection:  # then still may be a component face selection
            selection = cmds.ls(selection=True)
            if not selection:  # then nothing is selected
                return
        self.diffuseColorSldr.setColorLinearFloat(self.firstShaderColor())  # sets with rendering space color.

    def startSelectionCallback(self):
        """Starts selection callback"""
        self.selectionCallbacks.startSelectionCallback()

    def closeEvent(self, event):
        """Starts selection callback on window close"""
        self.selectionCallbacks.stopSelectionCallback()
        super(HsvPopop, self).closeEvent(event)

    # -------------
    # COMMANDS
    # -------------

    def setDiffuseColor(self):
        """Sets the diffuse color for all selected objects/shaders"""
        shdrInsts = shadermulti.shaderInstancesFromSelected(message=False)
        if not shdrInsts:
            return list()
        for shdrInst in shdrInsts:
            shdrInst.setDiffuse(self.diffuseColorSldr.colorLinearFloat())

    def startupHsvInstance(self):
        """Starts th HSV instance, selects shaders"""
        self.openUndoChunk()
        self.hsvInstance = shaderhsv.ShaderHSV()  # sets the shader instances and start colors.
        if self.hsvInstance.shdrInsts:
            self.shadersSet = True

    def shutdownHsvInstance(self):
        """After the slider is released finish the instance"""
        self.closeUndoChunk()
        self.resetSliders()
        if not self.shadersSet:
            return
        self.hsvInstance.shdrInsts = list()
        self.shadersSet = False

    def setHueOffset(self):
        """Offset the hue"""
        if not self.shadersSet:
            return
        col = self.hsvInstance.setHueOffset(self.hueFloatSlider.value())
        self.diffuseColorSldr.setColorLinearFloat(col)

    def setSaturationOffset(self):
        """Offset the saturation"""
        if not self.shadersSet:
            return
        col = self.hsvInstance.setSaturationOffset(self.saturationFloatSlider.value())
        self.diffuseColorSldr.setColorLinearFloat(col)

    def setValueOffset(self):
        """Offset the value"""
        if not self.shadersSet:
            return
        col = self.hsvInstance.setValueOffset(self.valueFloatSlider.value())
        self.diffuseColorSldr.setColorLinearFloat(col)

    # ------------------------------------
    # UNDO CHUNKS
    # ------------------------------------

    def openUndoChunk(self):
        """Opens the Maya undo chunk"""
        name = "hsvPopup"
        general.openUndoChunk(name)

    def closeUndoChunk(self):
        """Opens the Maya undo chunk"""
        name = "hsvPopup"
        general.closeUndoChunk(name)

    # -------------
    # CONNECTIONS
    # -------------

    def connections(self):
        """Connect the ui to logic"""
        self.diffuseColorSldr.colorSliderChanged.connect(self.setDiffuseColor)
        self.diffuseColorSldr.sliderPressed.connect(self.openUndoChunk)
        self.diffuseColorSldr.sliderReleased.connect(self.closeUndoChunk)

        self.floatSliderList = list()  # reset in case of advanced UI
        self.floatSliderList.append(self.hueFloatSlider)
        self.floatSliderList.append(self.saturationFloatSlider)
        self.floatSliderList.append(self.valueFloatSlider)
        # Connect the float and color sliders correctly
        for floatSlider in self.floatSliderList:
            floatSlider.sliderPressed.connect(self.startupHsvInstance)
            floatSlider.sliderReleased.connect(self.shutdownHsvInstance)

        self.hueFloatSlider.numSliderChanged.connect(self.setHueOffset)
        self.saturationFloatSlider.numSliderChanged.connect(self.setSaturationOffset)
        self.valueFloatSlider.numSliderChanged.connect(self.setValueOffset)

        # Callback methods
        self.selectionCallbacks = SelectionCallbacksMaya()
        self.startSelectionCallback()
        self.selectionCallbacks.callback.connect(self.selectionChanged)  # monitor selection
        # callbacks are stopped in self.closeEvent()

    # -------------
    # CREATE WIDGETS
    # -------------

    def widgets(self):
        """Build the widgets"""
        # Diffuse Color Slider ---------------------------------------
        toolTip = "Change to set diffuse color of all the selected objects/shaders"
        self.diffuseColorSldr = elements.ColorSlider(label="Col",
                                                     color=(0.5, 0.5, 0.5),
                                                     toolTip=toolTip,
                                                     labelBtnRatio=1,
                                                     sliderRatio=3,
                                                     labelRatio=1,
                                                     colorBtnRatio=2)
        # Hue Range Float Tuple ---------------------------------------
        tooltip = "Offset hue for all selected shaders diffuse value. \n" \
                  "Select shader nodes or geo with shaders. "
        self.hueFloatSlider = elements.FloatSlider(label="Hue",
                                                   defaultValue=0.0,
                                                   toolTip=tooltip,
                                                   sliderMin=-90.0,
                                                   sliderMax=90.0,
                                                   sliderRatio=3,
                                                   labelBtnRatio=1,
                                                   labelRatio=1,
                                                   editBoxRatio=2)
        # Value Range Float Tuple ---------------------------------------
        tooltip = "Offset value (brightness) for all selected shaders diffuse value. \n" \
                  "Select shader nodes or geo with shaders. "
        self.valueFloatSlider = elements.FloatSlider(label="Val",
                                                     defaultValue=0.0,
                                                     toolTip=tooltip,
                                                     sliderMin=-.5,
                                                     sliderMax=0.5,
                                                     dynamicMax=True,
                                                     sliderRatio=3,
                                                     labelBtnRatio=1,
                                                     labelRatio=1,
                                                     editBoxRatio=2)
        # Saturation Range Float Tuple ---------------------------------------
        tooltip = "Offset saturation (brightness) for all selected shaders diffuse value. \n" \
                  "Select shader nodes or geo with shaders. "
        self.saturationFloatSlider = elements.FloatSlider(label="Sat",
                                                          defaultValue=0.0,
                                                          toolTip=tooltip,
                                                          sliderMin=-0.5,
                                                          sliderMax=0.5,
                                                          dynamicMax=True,
                                                          sliderRatio=3,
                                                          labelBtnRatio=1,
                                                          labelRatio=1,
                                                          editBoxRatio=2)

    # -------------
    # LAYOUT UI
    # -------------

    def layout(self):
        """Layout the widgets into the window"""
        self.mainLayout = elements.vBoxLayout(spacing=0,
                                              margins=(uic.REGPAD, uic.REGPAD, uic.REGPAD, uic.REGPAD))
        self.mainLayout.addWidget(self.diffuseColorSldr)
        self.mainLayout.addWidget(self.hueFloatSlider)
        self.mainLayout.addWidget(self.saturationFloatSlider)
        self.mainLayout.addWidget(self.valueFloatSlider)

        self.setMainLayout(self.mainLayout)


def main():
    """Open the window"""
    win = HsvPopop()
    point = QtGui.QCursor.pos()
    point.setX(point.x() + WINDOW_OFFSET_X)
    point.setY(point.y() + WINDOW_OFFSET_Y)
    win.show(point)


if __name__ == "__main__":
    main()
