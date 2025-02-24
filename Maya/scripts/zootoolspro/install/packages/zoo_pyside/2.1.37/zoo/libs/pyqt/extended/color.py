import math
from functools import partial

from zoo.libs.pyqt import uiconstants


from zoovendor.Qt import QtCore, QtWidgets, QtGui

from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt import utils, keyboardmouse
from zoo.libs.pyqt.extended import menu, colorpopup
from zoo.libs.pyqt.widgets import layouts, label, slider, stringedit, buttons
from zoo.libs.utils import color as colorutils
from zoo.core.util import zlogging

logger = zlogging.getLogger(__name__)


class ColorButtonPressedEvent(object):
    color = (-1, -1, -1)
    index = -1
    srgb = (-1, -1, -1)

    def __init__(self, index, color, srgb):
        """ Color button pressed event for ColorPaletteColorList

        :param index:
        :type index:
        :param color:
        :type color:
        :param srgb:
        :type srgb:
        """
        self.color = color
        self.index = index
        self.srgb = srgb

    def __str__(self):
        return str(self.__dict__)


class ColorPaletteColorList(QtWidgets.QWidget):
    colorPressed = QtCore.Signal(ColorButtonPressedEvent)

    def __init__(self, colorList, parent=None, rows=2, totalHeight=70, borderRadius=0, spacing=0, toolTip=""):
        """Draws a color palette from a color list.  The list is in SRGB not linear color.
        The columns are automatically set from the row count and list length.

        .. code-block:: python

            # build widget
            self.colorPaletteHOffset = elements.ColorPaletteColorList(parent=parent)

            # setup connections
            for i, btn in enumerate(self.colorPaletteHOffset.colorBtnList):
                color = self.colorPaletteHOffset.colorListLinear[i]
                btn.clicked.connect(partial(self.colorSelected, color=color))

        See it's use in the Color Controls Toolset where palettes can be passed in and updated

        :param colorList: list of colors as SRGB float (0.5, 0.5, 0.5) is 50% grey
        :type colorList: list(tuple(float))
        :param parent: the widget parent
        :type parent: QtWidget
        :param rows: The amount of rows to draw
        :type rows: int
        :param totalHeight: The total height of the palette, button height is auto calculated from this number
        :type totalHeight: int
        """
        # TODO allow the row column counts to change so single palettes can be swithed.
        super(ColorPaletteColorList, self).__init__(parent=parent)
        self.colorListSrgb = colorList
        self.colorListLinear = list()  # Will be in Maya linear color, can be accessed through the GUI
        self.colorBtnList = list()  # buttons to connect in the GUI
        self.setToolTip(toolTip)
        gridLayout = layouts.GridLayout(parent=self, spacing=utils.dpiScale(spacing))
        btnHeight = utils.dpiScale(int(totalHeight / rows))
        columns = math.ceil(float(len(colorList)) / rows)  # ( number of colors / rows ), then round up.
        colCount = 0
        rowCount = 0
        for i, c in enumerate(colorList):
            # create button and set color
            btn = QtWidgets.QPushButton("", parent=self)
            btn.setMinimumWidth(utils.dpiScale(5))

            srgbInt = tuple(colorutils.rgbFloatToInt(c))  # Qt stylesheet needs int 255 color
            self.colorListLinear.append(colorutils.convertColorSrgbToLinear(c))
            btn.setStyleSheet(
                "background-color: rgb{}; border-radius: {}px;".format(str(srgbInt), utils.dpiScale(borderRadius)))
            btn.setProperty("color", c)
            btn.setProperty("index", i)
            btn.setProperty("srgb", srgbInt)

            self.colorBtnList.append(btn)
            # set btn height
            btn.setMaximumHeight(btnHeight)
            btn.setMinimumHeight(btnHeight)
            # add to grid layout
            if colCount >= columns:  # if columns are full then increment row and reset column
                rowCount += 1
                colCount = 0
            gridLayout.addWidget(btn, rowCount, colCount)
            colCount += 1

            btn.clicked.connect(self.emitPaletteButtonPressed)

    def emitPaletteButtonPressed(self):
        c = self.sender().property("color")
        i = self.sender().property("index")
        srgb = self.sender().property("srgb")
        self.colorPressed.emit(ColorButtonPressedEvent(i, c, srgb))

    def updatePaletteColors(self, newColorList):
        """Updates the palettes colors with the `startHsvColor` and `hueRange`

        :param newColorList: list of colors (in what colour space?)
        :type newColorList: list(tuple(float))
        """
        for i, oldCol in enumerate(self.colorListSrgb):  # loop through the original list in case of length mismatch
            newCol = newColorList[i]
            if i > len(newColorList):  # bail if new color doesn't exist, list not long enough
                break
            # set btn color
            rgbInt = colorutils.rgbFloatToInt(newCol)
            self.colorBtnList[i].setStyleSheet("background-color: rgb{}; "
                                               "border-radius: 0px;".format(str(tuple(rgbInt))))
            # replace color in list
            self.colorListSrgb[i] = newCol
            self.colorListLinear[i] = colorutils.convertColorSrgbToLinear(newCol)

    def rebuildPalette(self, rows=2, columns=10, totalHeight=70, startHsvColor=(0.0, 0.8, 0.8),
                       hueRange=280.0):
        """Currently not working???

        :param rows:
        :type rows:
        :param columns:
        :type columns:
        :param totalHeight:
        :type totalHeight:
        :param startHsvColor:
        :type startHsvColor:
        :param hueRange:
        :type hueRange:
        :return:
        :rtype:
        """
        # TODO this function is not working
        self.clear()  # delete and remake the grid layout
        QtWidgets.QWidget().setLayout(self.gridLayout)
        self.gridLayout = layouts.GridLayout(parent=self, spacing=0)  # rebuild
        self._buildWidget(rows, columns, totalHeight, hueRange, startHsvColor)
        self.mainWidget.setLayout(self.gridLayout)
        self.update()


class LabelColorBtn(QtWidgets.QWidget):
    """Creates a label and a color button (with no text) which opens a QT color picker,
    returns both rgb (0-255) and rgbF (0-1.0) values
    """
    colorChanged = QtCore.Signal(object)

    def __init__(self, label="Color:", initialRgbColor=None, initialRgbColorF=None, contentsMargins=(0, 0, 0, 0),
                 parent=None, labelWeight=1, colorWeight=1, colorWidth=None):
        """Initialize variables

        :param label: The name of the label, usually "Color:"
        :type label: str
        :param initialRgbColor: The initial rgb color in 0-255 ranges, overridden if there's a initialRgbColorF value
        :type initialRgbColor: tuple
        :param initialRgbColorF: The initial rgb color in 0-1.0 ranges, if None defaults to initialRgbColor values
        :type initialRgbColorF: tuple
        :param parent: the widget parent
        :type parent: class
        """
        initialRgbColorF = initialRgbColorF or []
        super(LabelColorBtn, self).__init__(parent=parent)

        self.layout = layouts.hBoxLayout(parent=self, margins=utils.marginsDpiScale(*contentsMargins),
                                         spacing=utils.dpiScale(uiconstants.SPACING))
        if label:
            self.layout.addWidget(QtWidgets.QLabel(label, parent=self), labelWeight)
        self.colorPickerBtn = QtWidgets.QPushButton("", parent=self)
        # use initialRgbColor (255 range) or initialRgbColorF (float range 0-1)
        # if no color given then default to red

        self.storedRgbColor = initialRgbColor or tuple([i * 255 for i in initialRgbColorF]) or tuple([255, 0, 0])
        self.colorPickerBtn.setStyleSheet("background-color: rgb{}".format(str(self.storedRgbColor)))
        if colorWidth:
            self.colorPickerBtn.setFixedWidth(colorWidth)
        self.layout.addWidget(self.colorPickerBtn, colorWeight)
        self.connections()

    def setColorSrgbInt(self, rgbList):
        """Sets the color of the button as per a rgb list in 0-255 range

        :param rgbList: r g b color in 255 range eg [255, 0, 0]
        :type rgbList: list
        """
        # if the user hits cancel the returned color is invalid, so don't update
        self.storedRgbColor = rgbList
        color = QtGui.QColor(self.storedRgbColor[0], self.storedRgbColor[1], self.storedRgbColor[2], 255)
        self.colorPickerBtn.setStyleSheet("background-color: {}".format(color.name()))

    def setColorSrgbFloat(self, rgbList):
        """Sets the color of the button as per a rgb list in 0-1 range, colors are not rounded

        :param rgbList: r g b color in float range eg [1.0, 0.0, 0.0]
        :type rgbList: list
        """
        self.setColorSrgbInt([color * 255 for color in rgbList])

    def pickColor(self):
        """Opens the color picker window
        If ok is pressed then the new color is returned in 0-255 ranges Eg (128, 255, 12)
        If Cancel is pressed the color is invalid and nothing happens
        """
        initialPickColor = QtGui.QColor(self.storedRgbColor[0], self.storedRgbColor[1], self.storedRgbColor[2], 255)
        color = QtWidgets.QColorDialog.getColor(initialPickColor)  # expects 255 range
        if QtGui.QColor.isValid(color):
            rgbList = (color.getRgb())[0:3]
            self.setColorSrgbInt(rgbList)
            self.colorChanged.emit(color)

    def rgbColor(self):
        """returns rgb tuple with 0-255 ranges Eg (128, 255, 12)
        """
        return self.storedRgbColor

    def rgbColorF(self):
        """returns rgb tuple with 0-1.0 float ranges Eg (1.0, .5, .6666)
        """
        return tuple(float(i) / 255 for i in self.storedRgbColor)

    def connections(self):
        """Open the color picker when the button is pressed
        """
        self.colorPickerBtn.clicked.connect(self.pickColor)


class ColorBtn(QtWidgets.QWidget, menu.MenuCreateClickMethods):
    colorChanged = QtCore.Signal(tuple)
    colorDragged = QtCore.Signal(tuple)
    colorClicked = QtCore.Signal()

    def __init__(self, text="", color=(1, 1, 1), parent=None, colorWidth=120, colorHeight=22, toolTip="",
                 labelRatio=50, btnRatio=50, margins=(0, 0, 0, 0), spacing=uic.SREG, colorWidgetRatio=1, key=None):
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
        super(ColorBtn, self).__init__(parent)
        return
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
        # self.setLayout(self.main_layout)
        self.key = key
        self.setColorFixedHeight(self.colorHeight)

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
        return
        # Create the colorSliderGrp """
        window = cmds.window()
        # color_slider_name
        #  width=1 is the pixel width of the slider which is hidden,
        #  columnWidth specifies col 1 width from the kwargs
        color_slider_name = cmds.colorSliderGrp(width=1, columnWidth=[1, self.colorWidth])

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

            self._color_widget = self._color_slider_widget.findChild(QtWidgets.QWidget, "port")

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
        colorSrgbFloat = colorutils.convertColorLinearToSrgb(self._colorLinear)
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

    def setWidth(self, width):
        """Sets the size of the color widget, dpi scale handled

        :param width: Width in pixels of the color btn
        :type width: int
        """
        self.colorWidth = width
        self._color_widget.setFixedWidth(utils.dpiScale(width - 1))
        self._color_slider_widget.setFixedWidth(utils.dpiScale(width))

    def setHeight(self, height):
        """sets the size of the color widget, dpi scale handled"""
        self.colorHeight = height
        self._color_widget.setFixedHeight(utils.dpiScale(height - 1))
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
        """Sets the color as linear color in 0-1.0 float ranges Eg (1.0, .5, .6666)
        emits the color as a Srgb Int color Eg (0, 255, 134)"""
        cmds.colorSliderGrp(self.fullName(), edit=True, rgbValue=(color[0], color[1], color[2]))
        self._colorLinear = color
        self._updateColor()
        if not noEmit:
            self._onColorChanged()  # emits and updates the color swatch

    def setColorSrgbFloat(self, col, noEmit=True):
        """sets the color as srgb tuple with 0-1.0 float ranges Eg (1.0, .5, .6666)
        emits the color as a Srgb Int color Eg (0, 255, 134)"""
        colorLinearFloat = colorutils.convertColorSrgbToLinear(col)
        self._colorLinear = colorLinearFloat
        self._updateColor()
        if not noEmit:
            self._onColorChanged()  # emits and updates the color swatch

    def setColorSrgbInt(self, col, noEmit=True):
        """sets the color as srgb Int tuple with 0-255 float ranges Eg (0, 255, 134)
        emits the color as a Srgb Int color Eg (0, 255, 134)"""
        colorSrgbFloat = colorutils.rgbIntToFloat(col)
        colorLinearFloat = colorutils.convertColorSrgbToLinear(colorSrgbFloat)
        self._colorLinear = colorLinearFloat
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
        return colorutils.convertColorLinearToSrgb(self._colorLinear)

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

        .. Note:: only works on the label currently.

        If a modeList is passed in then create/reset the menu to the modeList::

            [("icon1", "menuName1"), ("icon2", "menuName2")]

        If no modeList the menu won't change

        :param menu: the Qt menu to show on middle click
        :type menu: QtWidgets.QMenu
        :param modeList: a list of menu modes (tuples) eg [("icon1", "menuName1"), ("icon2", "menuName2")]
        :type modeList: list(tuple(str))
        :param mouseButton: the mouse button clicked QtCore.Qt.LeftButton, QtCore.Qt.RightButton, QtCore.Qt.MiddleButton
        :type mouseButton: QtCore.Qt.ButtonClick
        """
        # TODO: add menu to color picker button
        self.label.setMenu(menu, modeList=modeList, mouseButton=mouseButton)

    def addActionList(self, modes, mouseButton=QtCore.Qt.RightButton):
        """resets the appropriate mouse click menu with the incoming modes

        .. Note::
            Only works on the label currently.
            modeList: [("icon1", "menuName1"), ("icon2", "menuName2"), ("icon3", "menuName3")]

        Resets the lists and menus::

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


class ColorButton(QtWidgets.QLabel):
    colorChanged = QtCore.Signal(object)

    def __init__(self, parent=None, initialColor=(255, 255, 255), width=100):
        super(ColorButton, self).__init__(parent)
        self.setMinimumWidth(utils.dpiScale(30))
        utils.setHSizePolicy(self, QtWidgets.QSizePolicy.Minimum)
        self.setWidth(width)

        if width:
            self.setFixedWidth(width)
        self.setFixedHeight(utils.dpiScale(30))
        self.setStyleSheet("border-radius: 2px;")
        self._color = initialColor
        self._initColorPicker()

    def _initColorPicker(self):
        self.colorPicker = colorpopup.ColorPicker(parent=self)
        self.colorPicker.colorPickerClosed.connect(self.pickerClosed)
        self.colorPicker.colorChanged.connect(self.pickerColorChanged)
        utils.singleShotTimer(lambda: self.setRGBColor(self._color))

    def mousePressEvent(self, event):
        self.colorPicker.show()

    def setWidth(self, width):
        self.resize(utils.dpiScale(width), self.height())

    def setRGBColor(self, rgb):
        """

        :param rgb:
        :return:
        """
        # self.setStyleSheet("border-radius: 2px;")
        self.setAutoFillBackground(True)
        palette = self.palette()
        color = QtGui.QColor(*rgb)
        palette.setColor(self.backgroundRole(), color)
        self.setPalette(palette)
        self._color = rgb

    def color(self):
        return self._color

    def pickerColorChanged(self, colorEvent):
        """

        :param colorEvent:
        :type colorEvent: :class:`zoo.libs.pyqt.extended.colors.colorpopup.PickerColors`
        :return:
        """

        self.setRGBColor(colorEvent.rgb)

    def pickerClosed(self, colorEvent):
        """

        :param colorEvent:
        :type colorEvent: :class:`zoo.libs.pyqt.extended.colors.colorpopup.PickerColors`
        :return:
        """
        self.setRGBColor(colorEvent.rgb)
        self.colorChanged.emit(colorEvent.rgb)


class ColorHsvBtns(ColorBtn):
    offsetClicked = QtCore.Signal(tuple, bool)  # linear (hue, saturation, value), resetClicked (bool)

    def __init__(self, text="", color=(1, 1, 1), parent=None, colorWidth=120, colorHeight=22, toolTip="",
                 labelRatio=50, btnRatio=50, margins=(0, 0, 0, 0), spacing=uic.SREG, showHue=True, showSat=True,
                 showValue=True, hsvMargins=(0, 0, 0, 0), colorVsHsvSpacing=uic.SREG, hsvPairSpacing=uic.SSML,
                 middleSpacing=uic.SREG, colorWidgetRatio=1, hsvRatio=1, resetColor=(1.0, 1.0, 1.0)):
        """ColorBtn (slider disabled) with hsv buttons, hsv btns can be hidden.  Hsv btns affect the color, \
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
        super(ColorHsvBtns, self).__init__(text=text, color=color, parent=parent, colorWidth=colorWidth,
                                           colorHeight=colorHeight, toolTip=toolTip, labelRatio=labelRatio,
                                           btnRatio=btnRatio, margins=margins, spacing=spacing,
                                           colorWidgetRatio=colorWidgetRatio)
        self.resetColor = resetColor

        self.colorButton = ColorButton(parent=self)

        return
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


class ColorSlider(QtWidgets.QWidget):
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
        super(ColorSlider, self).__init__(parent=parent)
        self.layout = layouts.hBoxLayout(self, margins, spacing=spacing)
        self.labelBool = False
        labelBtnLayout = layouts.hBoxLayout(self, (0, 0, 0, 0), spacing=spacing)
        # Build Label -------------------
        if label:
            self.labelBool = True
            self.label = stringedit.Label(label, parent=parent, toolTip=toolTip, enableMenu=enableMenu)
            labelBtnLayout.addWidget(self.label, labelRatio)
        # Build Maya Color Button with no label -------------------
        self.colorBtn = ColorBtn(color=color, parent=parent, toolTip=toolTip)
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
        """Gets the current color button color and emits it by emitting a linear float color

        Also updates the slider widget
        """
        color = self.colorBtn.colorLinearFloat()
        self.colorChanged.emit(color)
        # Update the slider
        self._updateSlider()
        self.colorSliderChanged.emit()

    def _onColorClicked(self, *args):
        """Emit colorClicked"""
        pass

    def setColorBtnWidth(self, width):
        """Sets the color button widget width, dpi scale handled, will scale with cmds as pyside has issues overriding.

        :param width: pixel width of the color button.
        :type width: int
        """
        self.colorBtn.setWidth(width)

    def setColorBtnHeight(self, height):
        """Sets the size of the color button widget, dpi scale handled"""
        self.colorBtn.setHeight(height)

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
        """Sets the color as linear color in 0-1.0 float ranges Eg (1.0, .5, .6666)
        emits the color as a Srgb Int color Eg (0, 255, 134)

        :param color: color as linearFloat (1.0, .5, .6666)
        :type color: tuple(float)
        :param noEmit: Block the signals so no emit takes place
        :type noEmit: bool
        """
        self.colorBtn.setColorLinearFloat(color, noEmit=True)
        self._updateSlider()

    def setColorSrgbFloat(self, color, noEmit=True):
        """Sets the color as srgb tuple with 0-1.0 float ranges Eg (1.0, .5, .6666)
        emits the color as a Srgb Int color Eg (0, 255, 134)

        :param color: color as srgbFloat (1.0, .5, .6666)
        :type color: tuple(float)
        :param noEmit: Block the signals so no emit takes place
        :type noEmit: bool
        """
        self.colorBtn.setColorSrgbFloat(color, noEmit=True)
        self._updateSlider()

    def setColorSrgbInt(self, color, noEmit=True):
        """Sets the color as srgb Int tuple with 0-255 int ranges Eg (0, 255, 134)
        emits the color as a Srgb Int color Eg (0, 255, 134)

        :param color: color as srgbInt (0, 255, 134)
        :type color: tuple(int)
        :param noEmit: Block the signals so no emit takes place
        :type noEmit: bool
        """
        self.colorBtn.setColorSrgbInt(color, noEmit=True)
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