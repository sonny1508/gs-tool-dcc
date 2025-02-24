from functools import partial

from zoovendor.Qt import QtCore, QtWidgets, QtGui

import maya.OpenMayaUI as om1
import maya.cmds as cmds

from zoo.libs.maya.qt import mayaui
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt import utils, keyboardmouse
from zoo.libs.pyqt.extended import menu
from zoo.libs.pyqt.widgets import layouts, label, slider, stringedit, buttons
from zoo.libs.utils import color as colorutils
from zoo.core.util import zlogging
from zoo.libs.maya.utils import mayacolors

logger = zlogging.getLogger(__name__)


class MayaColorBtn(QtWidgets.QWidget, menu.MenuCreateClickMethods):
    colorChanged = QtCore.Signal(object)
    colorDragged = QtCore.Signal(object)
    colorClicked = QtCore.Signal()

    def __init__(self, text="", color=(1, 1, 1), parent=None, colorWidth=None, colorHeight=22, toolTip="",
                 labelRatio=50, btnRatio=50, margins=(0, 0, 0, 0), spacing=uic.SREG, colorWidgetRatio=1, key=None,):
        """Custom embedded cmds widget. This widget is Maya's cmds.colorSliderGrp with the (slider disabled)

        Thanks to Chris Zurbrigg for the slider solution see his tutorials http://zurbrigg.com/tutorials
        Additional code Andrew Silke.

        See also the subclass ColorHsvBtns() which adds hue saturation value buttons

        :param text: The color button label name
        :type text: str
        :param color: The start color of the color button in srbg float (0.1, 1.0, 0.5) Color is srgb not linear
        :type color: tuple
        :param parent: The parent widegt
        :type parent: QtWidget
        :param colorWidth: The width of the color button in pixels (dpi handled)
        :type colorWidth: int
        :param colorHeight:  The height of the color button in pixels (dpi handled)
        :type colorHeight: QtWidget
        :param toolTip: the tooltip on hover
        :type toolTip: str
        :param labelRatio: the width column ratio of the label/button corresponds to the ratios of labelRatio/btnRatio
        :type labelRatio: int
        :param btnRatio: the width column ratio of the label/button corresponds to the ratios of labelRatio/btnRatio
        :type btnRatio: int
        :param margins: Margins of the MayaColorBtn (label and button) (dpi handled)
        :type margins: tuple
        :param spacing: The spacing size of the MayaColorBtn (label and button) (dpi handled)
        :type spacing: int
        :param colorWidgetRatio: The label/color ratio only applicable when subclassed
        :type colorWidgetRatio: int
        :param key: Special dict key used for stylesheets, the stylesheet pref key eg. "FRAMELESS_TITLELABEL_COLOR"
        :type key: basestring
        """
        super(MayaColorBtn, self).__init__(parent)
        self.colorHeight = colorHeight
        self.setObjectName("CustomColorButton")
        self.btnRatio = btnRatio
        self.colorWidth = colorWidth
        # create widgets
        if text:
            self.label = label.Label(text, parent, toolTip=toolTip)  # supports menu
        else:
            self.label = None
        self.main_layout = layouts.hBoxLayout(parent=self, spacing=0)  # self.sub_layout hack when sub-classed
        self.sub_layout = layouts.hBoxLayout(margins=margins, spacing=spacing)
        self.main_layout.addLayout(self.sub_layout, colorWidgetRatio)
        if text:
            self.sub_layout.addWidget(self.label, labelRatio)
            self.label.setToolTip(toolTip)
        self._createControl()  # creates self._color_widget which is the color picker and adds it to the layout

        self._color_widget.setToolTip(toolTip)
        # color widget setup
        self._colorLinear = color
        self._updateColor()
        self.key = key

        self.setColorMinimumWidth(colorHeight)

        if self.colorHeight:
            self.setColorFixedHeight(self.colorHeight)

        if self.colorWidth:
            self.setColorFixedWidth(self.colorWidth)

    def setColorMinimumWidth(self, width):
        """ Set the minimum width of the color widget

        :param width:
        :return:
        """
        self._color_widget.setMinimumWidth(utils.dpiScale(width-1))
        self._color_slider_widget.setMinimumWidth(utils.dpiScale(width))

    def setColorMinimumHeight(self, height):
        """ Set the minimum height of the color widget

        :param width:
        :return:
        """
        self._color_widget.setMinimumHeight(utils.dpiScale(height - 1))
        self._color_slider_widget.setMinimumHeight(utils.dpiScale(height))

    def text(self):
        """returns the label name as a string

        :return labelName: the text name of the label
        :rtype labelName: str
        """
        if self.label:
            return self.label.text()
        return ""

    def _createControl(self):
        """Creates the Maya color slider control, hides the slider and converts the widget so it can be Qt embedded

        Credit to Chris Zurbrigg see his tutorials http://zurbrigg.com/tutorials for solving various embed issues
        Additional code Andrew Silke
        """

        # Create the colorSliderGrp """
        window = cmds.window()
        # color_slider_name
        #  width=1 is the pixel width of the slider which is hidden,
        #  columnWidth specifies col 1 width from the kwargs
        color_slider_name = cmds.colorSliderGrp(width=1, columnWidth=[1, self.colorWidth or 122])

        # Find the colorSliderGrp widget
        self._color_slider_obj = om1.MQtUtil.findControl(color_slider_name)
        if self._color_slider_obj:
            self._color_slider_widget = mayaui.toQtObject(color_slider_name)

            # Reparent the colorSliderGrp widget to this widget
            self.sub_layout.addWidget(self._color_slider_widget, self.btnRatio)

            # Identify/store the colorSliderGrp's child widgets (and hide if necessary)
            self._slider_widget = self._color_slider_widget.findChild(QtWidgets.QWidget, "slider")
            if self._slider_widget:
                self._slider_widget.hide()

            self._color_widget = self._color_slider_widget.findChild(QtWidgets.QWidget, "port") # type: QtWidgets.QWidget

            cmds.colorSliderGrp(self.fullName(), e=True, changeCommand=partial(self._onColorChanged))
            cmds.colorSliderGrp(self.fullName(), e=True, dragCommand=partial(self._onColorDragged))

        logger.debug("create control: {}".format(self._color_slider_widget))

        cmds.deleteUI(window, window=True)

    def fullName(self):
        return mayaui.fullName(self._color_slider_obj)

    def _updateColor(self):
        """Updates the color on the color picker widget, usually Maya will perform this auto but Zoo stylesheeting
        causes issues so we overwrite the widget directly with self._color_widget.setStyleSheet()
        """
        colorSrgbFloat = mayacolors.renderingColorToDisplaySpace(self._colorLinear, setCurrentViewSpace=True)
        colorSrgbInt = colorutils.rgbFloatToInt(colorSrgbFloat)
        colorSlider = cmds.colorSliderGrp(self.fullName(), edit=True, rgbValue=(self._colorLinear[0],
                                                                                self._colorLinear[1],
                                                                                self._colorLinear[2]))
        # Must update self._color_slider_widget and self._color_widget as might have changed with drag and dropping UIs
        self._color_slider_widget = mayaui.toQtObject(colorSlider)
        self._color_widget = self._color_slider_widget.findChild(QtWidgets.QWidget, "port")
        # Now set the color of the color button (QLabel)
        self._color_widget.setStyleSheet("QLabel {} background-color: rgb{} {}; ".format("{", str(colorSrgbInt), "}"))

    def _onColorChanged(self, *args):
        """Gets the current color slider color and emits it by emtting a linear float color
        """
        self._colorLinear = self.colorLinearFloat()
        self._updateColor()
        self.colorChanged.emit(self._colorLinear)
        self.colorClicked.emit()

    def _onColorDragged(self, *args):
        self._colorLinear = self.colorLinearFloat()
        self._updateColor()
        self.colorDragged.emit(self._colorLinear)

    def setColorFixedWidth(self, width):
        """Sets the size of the color widget, dpi scale handled

        :param width: Width in pixels of the color btn
        :type width: int
        """
        self.colorWidth = width
        self._color_widget.setFixedWidth(utils.dpiScale(width - 1))
        self._color_slider_widget.setFixedWidth(utils.dpiScale(width))

    def setColorFixedHeight(self, height):
        """sets the size of the color widget, dpi scale handled"""
        self.colorHeight = height
        self._color_widget.setFixedHeight(utils.dpiScale(height-1))
        self._color_slider_widget.setFixedHeight(utils.dpiScale(height))

    def setDisabled(self, disabled=True):
        # disables the color widget so it cannot be clicked
        enabled = not disabled
        cmds.colorSliderGrp(self.fullName(), e=True, enable=enabled)
        if self.label:
            self.label.setDisabled(disabled)

    def setEnabled(self, enabled=True):
        # enables the color widget so it can be clicked
        cmds.colorSliderGrp(self.fullName(), e=True, enable=enabled)
        self.label.setDisabled(not enabled)

    def setDisabledLabel(self, disabled=True):
        # disables the color widget label only, the color picker will work as per normal
        self.label.setDisabled(disabled)

    def setColorLinearFloat(self, color, noEmit=True):
        """Sets the color as renderspace color (or linear) in 0-1.0 float ranges Eg (1.0, .5, .6666)

        emits the color as a Srgb Int color Eg (0, 255, 134)
        """
        cmds.colorSliderGrp(self.fullName(), edit=True, rgbValue=(color[0], color[1], color[2]))
        self._colorLinear = color
        self._updateColor()
        if not noEmit:
            self._onColorChanged()  # emits and updates the color swatch

    def setColorSrgbFloat(self, color, noEmit=True):
        """sets the color as display tuple with 0-1.0 float ranges Eg (1.0, .5, .6666)
        emits the color as a display Int color Eg (0, 255, 134)

        Note: Maya 2023 and above this now supports Display Color as SRGB.  2022 and below is SRGB only.

        :param color: Color as display color float 0-1.0
        :type color: list(float)
        :param noEmit: Emit the color?
        :type noEmit: bool
        """
        self._colorLinear = mayacolors.displayColorToCurrentRenderingSpace(color, setCurrentViewSpace=True)
        self._updateColor()
        if not noEmit:
            self._onColorChanged()  # emits and updates the color swatch

    def setColorSrgbInt(self, color, noEmit=True):
        """Sets the color as srgb Int tuple with 0-255 integer ranges Eg (0, 255, 134)

        Emits the color as a Srgb Int color Eg (0, 255, 134)

        Note: Maya 2023 and above this now supports Display Color as SRGB.  2022 and below is SRGB only.

        :param color: Color as display color 0-255 integer.  Always srgb in 2022 and below.
        :type color: list(int)
        :param noEmit: Emit the color?
        :type noEmit: bool
        """
        colorSrgbFloat = colorutils.rgbIntToFloat(color)
        self._colorLinear = mayacolors.displayColorToCurrentRenderingSpace(colorSrgbFloat, setCurrentViewSpace=True)
        self._updateColor()
        if not noEmit:
            self._onColorChanged()  # emits and updates the color swatch

    def colorLinearFloat(self):
        """returns the color of the color picker in linear color
        With 0-1.0 float ranges Eg (1.0, .5, .6666), the color is in Linear color, not SRGB
        """
        self._colorLinear = cmds.colorSliderGrp(self.fullName(), q=True, rgbValue=True)
        return self._colorLinear

    def colorSrgbInt(self):
        """returns rgb tuple with 0-255 ranges Eg (128, 255, 12)
        """
        return colorutils.rgbFloatToInt(self.colorSrgbFloat())

    def colorSrgbFloat(self):
        """returns rgb tuple with 0-1.0 float ranges Eg (1.0, .5, .6666)
        """
        return mayacolors.renderingColorToDisplaySpace(self._colorLinear, setCurrentViewSpace=True)

    def data(self):
        """Returns the stored dictionary key (None by default) and a hex color.
        The key is usually a dictionary key that is passed in on creation of the instance, used in stylesheets
        This method is pretty specific to stylesheets and could be moved, method must be named data

        :return self.key: the dict key passed into the initialise function, stylesheet key "FRAMELESS_TITLELABEL_COLOR"
        :rtype self.key: str
        :return hexColor: the color as hex, 6 letters eg ffffff
        :rtype hexColor: str
        """
        hexColor = colorutils.RGBToHex(self.colorSrgbInt())
        return {self.key: hexColor}

    # ----------
    # MENUS
    # ----------

    def setMenu(self, menu, modeList=None, mouseButton=QtCore.Qt.RightButton):
        """Add the left/middle/right click menu by passing in a QMenu,

        .. note::

            Only works on the label currently.

        If a modeList is passed in then create/reset the menu to the modeList:

        .. code-block:: python

            [("icon1", "menuName1"), ("icon2", "menuName2")]

        If no modelist the menu won't change.

        :param menu: The Qt menu to show on middle click.
        :type menu: QtWidgets.QMenu
        :param modeList: Menu modes. eg [("icon1", "menuName1"), ("icon2", "menuName2")]
        :type modeList: list(tuple(str))
        :param mouseButton: the mouse button clicked QtCore.Qt.LeftButton, QtCore.Qt.RightButton, QtCore.Qt.MiddleButton
        :type mouseButton: QtCore.Qt.ButtonClick
        """
        # TODO: add menu to color picker button
        self.label.setMenu(menu, modeList=modeList, mouseButton=mouseButton)

    def addActionList(self, modes, mouseButton=QtCore.Qt.RightButton):
        """resets the appropriate mouse click menu with the incoming modes

        Note: only works on the label currently

        modeList: [("icon1", "menuName1"), ("icon2", "menuName2"), ("icon3", "menuName3")]

        resets the lists and menus:

            self.menuIconList: ["icon1", "icon2", "icon3"]
            self.menuIconList: ["menuName1", "menuName2", "menuName3"]

        :param modes: a list of menu modes (tuples) eg [("icon1", "menuName1"), ("icon2", "menuName2")]
        :type modes: list(tuple(str))
        :param mouseButton: the mouse button clicked QtCore.Qt.LeftButton, QtCore.Qt.RightButton, QtCore.Qt.MiddleButton
        :type mouseButton: QtCore.Qt.ButtonClick
        """
        # TODO: add menu to color picker button
        if self.label:
            self.label.addActionList(modes, mouseButton=mouseButton)


class MayaColorHsvBtns(MayaColorBtn):
    offsetClicked = QtCore.Signal(tuple, bool)  # linear (hue, saturation, value), resetClicked (bool)

    def __init__(self, text="", color=(1, 1, 1), parent=None, colorWidth=None, colorHeight=22, toolTip="",
                 labelRatio=50, btnRatio=50, margins=(0, 0, 0, 0), spacing=uic.SREG, showHue=True, showSat=True,
                 showValue=True, hsvMargins=(0, 0, 0, 0), colorVsHsvSpacing=uic.SREG, hsvPairSpacing=uic.SSML,
                 middleSpacing=uic.SREG, colorWidgetRatio=1, hsvRatio=1, resetColor=(1.0, 1.0, 1.0)):
        """MayaColorBtn (slider disabled) with hsv buttons, hsv btns can be hidden.  Hsv btns affect the color, \
        and emit the color

        See the class MayaColorBtn for more

        :param text: The color button label name
        :type text: str
        :param color: The start color of the color button in rbg 255 (255, 255, 255) Color is srgb not linear
        :type color: tuple
        :param parent: The parent widget
        :type parent: QtWidget
        :param colorWidth: The width of the color button in pixels (dpi handled)
        :type colorWidth: int
        :param colorHeight:  The height of the color button in pixels (dpi handled)
        :type colorHeight: QtWidget
        :param toolTip: The tooltip on hover, the label and color only
        :type toolTip: str
        :param labelRatio: The width column ratio of the label/button corresponds to the ratios of labelRatio/btnRatio
        :type labelRatio: int
        :param btnRatio: The width column ratio of the label/button corresponds to the ratios of labelRatio/btnRatio
        :type btnRatio: int
        :param margins: Margins of the MayaColorBtn (label and button) (dpi handled)
        :type margins: tuple
        :param spacing: The spacing size of the MayaColorBtn (label and button) (dpi handled)
        :type spacing: int
        :param showHue: Show the hue button pair?
        :type showHue: bool
        :param showSat: Show the sat button pair?
        :type showSat: bool
        :param showValue: Show the value button pair?
        :type showValue: bool
        :param hsvMargins: The margins of hsv button section
        :type hsvMargins: int
        :param colorVsHsvSpacing: The spacing of hsv button section
        :type colorVsHsvSpacing: int
        :param hsvPairSpacing: The spacing of each button pair, eg between the two hue buttons and two sat buttons
        :type hsvPairSpacing: int
        :param middleSpacing: The spacing between the label/color and the hsv buttons
        :type middleSpacing: int
        :param colorWidgetRatio: The label/color ratio (the label/color vs the hsv buttons)
        :type colorWidgetRatio: int
        :param hsvRatio: The hsv buttons ratio (the label/color vs the hsv buttons)
        :type hsvRatio: int
        """
        super(MayaColorHsvBtns, self).__init__(text=text, color=color, parent=parent, colorWidth=colorWidth,
                                               colorHeight=colorHeight, toolTip=toolTip, labelRatio=labelRatio,
                                               btnRatio=btnRatio, margins=margins, spacing=spacing,
                                               colorWidgetRatio=colorWidgetRatio)
        self.resetColor = resetColor
        self._buildHueSatBtns(parent)
        self._buildHueSatLayouts(parent, hsvMargins, colorVsHsvSpacing, hsvPairSpacing)
        self.hsvShowHide(showHue=showHue, showSat=showSat, showValue=showValue)
        self.main_layout.addLayout(self.hsvLayout, hsvRatio)  # inherits self.sub_layout which contains lbl/col layout
        self.main_layout.setSpacing(middleSpacing)
        self._hsvConnections()

    def hsvShowHide(self, showHue=True, showSat=True, showValue=True):
        """Hide/show the hue saturation buttons

        :param showHue: Show/hide the hues buttons
        :type showHue: bool
        :param showSat: Show/hide the hues buttons
        :type showSat: bool
        :param showValue: Show/hide the hues buttons
        :type showValue: bool
        """
        if not showHue:
            self.hueWidget.hide()
        else:
            self.hueWidget.show()
        if not showSat:
            self.satWidget.hide()
        else:
            self.satWidget.show()
        if not showValue:
            self.valueWidget.hide()
        else:
            self.valueWidget.show()

    def _buildHueSatBtns(self, parent):
        toolTip = "Hue: Decrease (shift faster, ctrl slower, alt reset)"
        self.colHueBtnNeg = buttons.styledButton("", "previousSml",
                                                 parent,
                                                 toolTip,
                                                 style=uic.BTN_TRANSPARENT_BG,
                                                 minWidth=uic.BTN_W_ICN_SML)
        toolTip = "Hue: Increase (shift faster, ctrl slower, alt reset)"
        self.colHueBtnPos = buttons.styledButton("", "nextSml",
                                                 parent,
                                                 toolTip,
                                                 style=uic.BTN_TRANSPARENT_BG,
                                                 minWidth=uic.BTN_W_ICN_SML)
        toolTip = "Saturation: Decrease (shift faster, ctrl slower, alt reset)"
        self.colSatBtnNeg = buttons.styledButton("", "previousSml",
                                                 parent,
                                                 toolTip,
                                                 style=uic.BTN_TRANSPARENT_BG,
                                                 minWidth=uic.BTN_W_ICN_SML)
        toolTip = "Saturation: Increase (shift faster, ctrl slower, alt reset)"
        self.colSatBtnPos = buttons.styledButton("", "nextSml",
                                                 parent,
                                                 toolTip,
                                                 style=uic.BTN_TRANSPARENT_BG,
                                                 minWidth=uic.BTN_W_ICN_SML)
        toolTip = "Brightness: Decrease (shift faster, ctrl slower, alt reset)"
        self.colValueBtnNeg = buttons.styledButton("", "previousSml",
                                                   parent,
                                                   toolTip,
                                                   style=uic.BTN_TRANSPARENT_BG,
                                                   minWidth=uic.BTN_W_ICN_SML)
        toolTip = "Brightness: Increase (shift faster, ctrl slower, alt reset)"
        self.colValueBtnPos = buttons.styledButton("", "nextSml",
                                                   parent,
                                                   toolTip,
                                                   style=uic.BTN_TRANSPARENT_BG,
                                                   minWidth=uic.BTN_W_ICN_SML)

    def _buildHueSatLayouts(self, parent, hsvMargins, hsvSpacing, hsvProximity):
        """Layout the hue sat and value buttons, add pair layouts to widgets so can be hidden/shown

        :param parent: The parent widget
        :type parent: object
        :param hsvMargins: The margins of overall hsv buttons
        :type hsvMargins: list(int)
        :param hsvSpacing: The spacing of the hsv button pairs
        :type hsvSpacing: int
        :param hsvProximity: The spacing of each button pair
        :type hsvProximity: int
        """
        self.hsvLayout = layouts.hBoxLayout(margins=hsvMargins, spacing=hsvSpacing)
        # hue
        hueLayout = layouts.hBoxLayout(spacing=hsvProximity)
        hueLayout.addWidget(self.colHueBtnNeg)
        hueLayout.addWidget(self.colHueBtnPos)
        self.hueWidget = QtWidgets.QWidget(self)
        self.hueWidget.setLayout(hueLayout)
        # sat
        satLayout = layouts.hBoxLayout(spacing=hsvProximity)
        satLayout.addWidget(self.colSatBtnNeg)
        satLayout.addWidget(self.colSatBtnPos)
        self.satWidget = QtWidgets.QWidget(self)
        self.satWidget.setLayout(satLayout)
        # value
        valueLayout = layouts.hBoxLayout(spacing=hsvProximity)
        valueLayout.addWidget(self.colValueBtnNeg)
        valueLayout.addWidget(self.colValueBtnPos)
        self.valueWidget = QtWidgets.QWidget(self)
        self.valueWidget.setLayout(valueLayout)
        # main
        self.hsvLayout.addWidget(self.hueWidget)
        self.hsvLayout.addWidget(self.satWidget)
        self.hsvLayout.addWidget(self.valueWidget)

    def _hsvOffset(self, offsetHue=False, offsetSat=False, offsetValue=False, neg=False):
        """The Hue, Saturation and Value logic, does the math in linear color

        :param offsetHue: do you want to offset the hue?
        :type offsetHue: bool
        :param offsetSat: do you want to offset the saturation?
        :type offsetSat: bool
        :param offsetValue: do you want to offset the value (brightness)?
        :type offsetValue: bool
        :param neg: reverse the offset in the negative (lower) values
        :type neg: bool
        """
        hsvColor = colorutils.convertRgbToHsv(self._colorLinear)
        multiplier, resetClicked = keyboardmouse.ctrlShiftMultiplier()  # for alt shift and ctrl keys with left click
        # do the offset
        offsetHsv = (0.0, 0.0, 0.0)
        if offsetHue:
            if resetClicked:
                hsvColor = colorutils.convertRgbToHsv(self.resetColor)
            else:
                offset = 18.0 * multiplier
                if neg:
                    offset = -offset
                hsvColor = colorutils.offsetHueColor(hsvColor, offset)
                offsetHsv = (offset, 0.0, 0.0)
        elif offsetSat:
            if resetClicked:
                hsvColor = colorutils.convertRgbToHsv(self.resetColor)
            else:
                offset = .05 * multiplier
                if neg:
                    offset = -offset
                hsvColor = colorutils.offsetSaturation(hsvColor, offset)
                offsetHsv = (0.0, offset, 0.0)
        elif offsetValue:
            if resetClicked:
                hsvColor = colorutils.convertRgbToHsv(self.resetColor)
            else:
                offset = .05 * multiplier
                if neg:
                    offset = -offset
                hsvColor = colorutils.offsetValue(hsvColor, offset)
                offsetHsv = (0.0, 0.0, offset)
        # change the color swatch
        self.setColorLinearFloat(colorutils.convertHsvToRgb(hsvColor), noEmit=True)  # change the swatch don't emit
        self.offsetClicked.emit(offsetHsv, resetClicked)  # emit. linear (hue, saturation, value), resetClicked (bool)

    def _hsvConnections(self):
        """Hookup the hsv buttons"""
        self.colHueBtnNeg.clicked.connect(partial(self._hsvOffset, offsetHue=True, neg=True))
        self.colHueBtnPos.clicked.connect(partial(self._hsvOffset, offsetHue=True, neg=False))
        self.colSatBtnNeg.clicked.connect(partial(self._hsvOffset, offsetSat=True, neg=True))
        self.colSatBtnPos.clicked.connect(partial(self._hsvOffset, offsetSat=True, neg=False))
        self.colValueBtnNeg.clicked.connect(partial(self._hsvOffset, offsetValue=True, neg=True))
        self.colValueBtnPos.clicked.connect(partial(self._hsvOffset, offsetValue=True, neg=False))


class MayaColorSlider(QtWidgets.QWidget):
    colorChanged = QtCore.Signal(tuple)
    sliderChanged = QtCore.Signal()  # self.sliderChanged.connect(funcNoUndo) use to connect to no undo function
    sliderPressed = QtCore.Signal()  # self.sliderPressed.connect(openUndoChunk) use to open the undo chunk
    sliderReleased = QtCore.Signal()  # self.sliderPressed.connect(closeUndoChunk) use to close the undo chunk
    colorSliderChanged = QtCore.Signal()  # A change to the color btn or slider, sliderChanged or colorChanged

    def __init__(self, label="", color=(0.0, 0.0, 1.0), parent=None, toolTip="", sliderAccuracy=200, editWidth=None,
                 enableMenu=False, labelRatio=1, colorBtnRatio=1, sliderRatio=1, labelBtnRatio=1, colorBtnWidth=None,
                 colorBtnHeight=None, margins=(0, 0, 0, 0), spacing=uic.SREG):
        """A color btn, and slider with optional label

        Label is bypassed if there is no label
        Slider and cannot be bypassed, use MayaColorBtn() if you do not need a slider.

        :param label: The name of the label, if empty "" will not build a label
        :type label: str
        :param color: The start color of the color button in srbg float (0.1, 1.0, 0.5) Color is srgb not linear
        :type color: tuple
        :param parent:  The parent Widget
        :type parent: object
        :param toolTip: The tooltip on all widgets
        :type toolTip: str
        :param sliderAccuracy: The accuracy of the slider, is an int with the steps of the slider
        :type sliderAccuracy: int
        :param editWidth:  The width in pixels of the lineEdit, None is auto
        :type editWidth: int
        :param enableMenu: Enable the right click menu on the label and lineEdit?  See StringEdit() documentation
        :type enableMenu: bool
        :param labelRatio: The ratio size for laying out the label compared to other widgets, default is 1 which is 1/4
        :type labelRatio: int
        :param colorBtnRatio: The ratio size for laying out the MayaColorBtn default is 1 which is 1/4
        :type colorBtnRatio: int
        :param sliderRatio: The ratio size for laying out the slider half default is 1 which is 1/2
        :type sliderRatio: int
        :param labelBtnRatio: The ratio size for the label and color btn layout, default is 1 which is 1/2
        :type labelBtnRatio: int
        :param colorBtnWidth: The width of the color button in pixels, None will use defaults.
        :type colorBtnWidth: int
        :param colorBtnHeight: The height of the color button in pixels, None will use defaults.
        :type colorBtnHeight: int
        :param margins: The margins of the main layout, left top, right, bottom, values are in pixels, DPI is handled
        :type margins: tuple(int)
        :param spacing: The spacing between widgets in pixels, DPI is handled
        :type spacing: int
        """
        super(MayaColorSlider, self).__init__(parent=parent)
        self.layout = layouts.hBoxLayout(self, margins, spacing=spacing)
        self.labelBool = False
        labelBtnLayout = layouts.hBoxLayout(margins=(0, 0, 0, 0), spacing=spacing)
        # Build Label -------------------
        if label:
            self.labelBool = True
            self.label = stringedit.Label(label, parent=parent, toolTip=toolTip, enableMenu=enableMenu)
            labelBtnLayout.addWidget(self.label, labelRatio)
        # Build Maya Color Button with no label -------------------
        self.colorBtn = MayaColorBtn(color=color, parent=parent, toolTip=toolTip)
        if colorBtnWidth:
            self.setColorBtnWidth(colorBtnWidth)
        if colorBtnHeight:
            self.setColorBtnHeight(colorBtnHeight)
        labelBtnLayout.addWidget(self.colorBtn, colorBtnRatio)
        self.layout.addLayout(labelBtnLayout, labelBtnRatio)
        defaultValue = colorutils.convertRgbToHsv(color)[2]
        # Build Slider -------------------
        self.slider = slider.Slider(defaultValue=defaultValue, parent=parent, toolTip=toolTip, minValue=0.0,
                                    maxValue=1.0, sliderAccuracy=sliderAccuracy, decimalPlaces=4,
                                    orientation=QtCore.Qt.Horizontal)
        self.layout.addWidget(self.slider, sliderRatio)

        # Connections for emitting signals -------------------
        self.uiConnections()

    def text(self):
        """returns the label name as a string

        :return labelName: the text name of the label
        :rtype labelName: str
        """
        return self.colorBtn.text()

    def _updateSlider(self):
        """While setting the textbox update the slider position
        """
        colorSrgbFloat = self.colorBtn.colorSrgbFloat()
        hsv = colorutils.convertRgbToHsv(colorSrgbFloat)
        self.slider.blockSignals(True)
        self.slider.setValue(hsv[2])  # set value (hue saturation value)
        self.slider.blockSignals(False)

    def _onColorChanged(self, *args):
        """Gets the current color button color and emits it by emitting a linear float color.

        Also updates the slider widget.
        """
        color = self.colorBtn.colorLinearFloat()
        self.colorChanged.emit(color)
        # Update the slider
        self._updateSlider()
        self.colorSliderChanged.emit()

    def _onColorClicked(self, *args):
        """Emit colorClicked.  Not working."""
        pass

    def setColorBtnWidth(self, width):
        """Sets the color button widget width, dpi scale handled, will scale with cmds as pyside has issues overriding.

        Not Tested should work.

        :param width: pixel width of the color button.
        :type width: int
        """
        self.colorBtn.setColorFixedWidth(width)

    def setColorBtnHeight(self, height):
        """Sets the size of the color button widget, dpi scale handled"""
        self.colorBtn.setColorFixedHeight(height)

    def setDisabled(self, disabled=True):
        """Disables the color button, slider and label so it cannot be clicked"""
        self.colorBtn.setDisabled(disabled)
        self.slider.setDisabled(disabled)
        self.label.setDisabled(disabled)

    def setEnabled(self, enabled=True):
        """Enables the color button, slider and label so it cannot be clicked"""
        self.colorBtn.setDisabled(not enabled)
        self.slider.setDisabled(not enabled)
        self.label.setDisabled(not enabled)

    def setDisabledLabelSlider(self, disabled=True):
        """Disables the color widget label and slider, the color picker and slider will work as per normal"""
        self.label.setDisabled(disabled)
        self.slider.setDisabled(disabled)

    def setColorLinearFloat(self, color, noEmit=True):
        """Sets the color as rendering space color in 0-1.0 float ranges Eg (1.0, .5, .6666)
        emits the color as a Srgb Int color Eg (0, 255, 134)

        :param color: color as rendering space Float (1.0, .5, .6666)
        :type color: tuple(float)
        :param noEmit: Block the signals so no emit takes place
        :type noEmit: bool
        """
        self.colorBtn.setColorLinearFloat(color, noEmit=noEmit)
        self._updateSlider()

    def setColorSrgbFloat(self, color, noEmit=True):
        """Sets the color as srgb tuple with 0-1.0 float ranges Eg (1.0, .5, .6666)
        emits the color as a Srgb Int color Eg (0, 255, 134)

        :param color: color as srgbFloat (1.0, .5, .6666)
        :type color: tuple(float)
        :param noEmit: Block the signals so no emit takes place
        :type noEmit: bool
        """
        self.colorBtn.setColorSrgbFloat(color, noEmit=noEmit)
        self._updateSlider()

    def setColorSrgbInt(self, color, noEmit=True):
        """Sets the color as srgb Int tuple with 0-255 int ranges Eg (0, 255, 134)
        emits the color as a Srgb Int color Eg (0, 255, 134)

        :param color: color as srgbInt (0, 255, 134)
        :type color: tuple(int)
        :param noEmit: Block the signals so no emit takes place
        :type noEmit: bool
        """
        self.colorBtn.setColorSrgbInt(color, noEmit=noEmit)
        self._updateSlider()

    def colorLinearFloat(self):
        """Returns the color of the color picker in linear color
        With 0-1.0 float ranges Eg (1.0, .5, .6666), the color is in Linear color, not srgb

        :return colorLinearFloat: color in linear float range, eg (1.0, .5, .6666)
        :rtype colorLinearFloat: tuple(float)
        """
        return self.colorBtn.colorLinearFloat()

    def colorSrgbInt(self):
        """Returns rgb tuple with 0-255 ranges Eg (128, 255, 12)

        :return colorSrgbInt: color in srgb int range, eg (128, 255, 12)
        :rtype colorSrgbInt: tuple(int)
        """
        return self.colorBtn.colorSrgbInt()

    def colorSrgbFloat(self):
        """Returns rgb tuple with 0-1.0 float ranges Eg (1.0, .5, .6666)

        :return colorSrgbFloat: color in srgb float range, eg (1.0, .5, .6666)
        :rtype colorSrgbFloat: tuple(float)
        """
        return self.colorBtn.colorSrgbFloat()

    def _sliderUpdated(self):
        """Updates the color on the color btn from the slider replacing value (hue saturation value)"""
        value = self.slider.value()  # is a float because zoo Slider
        # Do the math on the current color and adjust value
        colorSrgbFloat = self.colorBtn.colorSrgbFloat()
        hsv = colorutils.convertRgbToHsv(colorSrgbFloat)
        newHsv = [hsv[0], hsv[1], value]
        newSrgbFloat = colorutils.convertHsvToRgb(newHsv)
        self.colorBtn.setColorSrgbFloat(newSrgbFloat, noEmit=True)
        self.sliderChanged.emit()
        self.colorSliderChanged.emit()

    def _sliderPressed(self):
        """Emits when the slider is pressed, useful for opening the undo stack"""
        self.sliderPressed.emit()

    def _sliderReleased(self):
        """Emits when the slider is released"""
        self.sliderChanged.emit()  # be sure to update as slider lags
        self.colorSliderChanged.emit()
        self.sliderReleased.emit()  # Useful for closing the undo stack

    def uiConnections(self):
        """Setup the emit signals"""
        self.colorBtn.colorClicked.connect(self._onColorClicked)
        self.colorBtn.colorChanged.connect(self._onColorChanged)
        self.slider.valueChanged.connect(self._sliderUpdated)
        self.slider.sliderPressed.connect(self._sliderPressed)
        self.slider.sliderReleased.connect(self._sliderReleased)
