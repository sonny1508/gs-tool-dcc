import math
from collections import namedtuple

from zoo.libs import iconlib
from zoo.libs.pyqt import utils, qtmath
from zoo.libs.pyqt.widgets import stringedit, layouts
from zoo.libs.pyqt.widgets.frameless.window import ZooWindow
from zoo.libs.pyqt.widgets.joinedradio import JoinedRadioButton
from zoo.libs.utils import color
from zoovendor.Qt import QtWidgets, QtCore
from zoo.libs.pyqt.widgets.frameless.widgets import TitleBar
import colorsys

PickerColors = namedtuple("PickerColors", "rgb,hsv,hex,a")




class ColorHandle(QtWidgets.QLabel):
    qicon = None

    def __init__(self, parent=None):
        """ Color Handle for the color wheel

        :param parent:
        """
        super(ColorHandle, self).__init__(parent=parent)
        if not ColorHandle.qicon:
            ColorHandle.qicon = iconlib.icon("colorwidget", size=-1)
        self.pixmap = ColorHandle.qicon.pixmap(ColorHandle.qicon.availableSizes()[0])
        self.setPixmap(self.pixmap)
        self.setFixedSize(self.pixmap.width(), self.pixmap.height())

    def move(self, pt):
        """ Move the color handle

        :param pt:
        :return:
        """
        super(ColorHandle, self).move(pt - self.centerSize())

    def centerSize(self):
        """ The Center point

        (eg. self.width() / 2, self.height / 2)

        :return:
        """
        return QtCore.QPoint(self.width() / 2, self.height() / 2)

    def handlePos(self):
        """ The handle position.

        The returned point is the center.

        :return:
        """
        return self.pos() + self.centerSize()


class ColorWheel(QtWidgets.QLabel):
    colorChanged = QtCore.Signal(object)
    qicon = None

    def __init__(self, parent=None):
        """ The rgb colour wheel picture

        :param parent:
        """
        super(ColorWheel, self).__init__(parent=parent)
        width = 150
        height = 150
        self.pressed = False
        self._imgPadX = 0
        self._imgPadY = 0
        self._color = (255, 255, 255)
        if not ColorWheel.qicon:
            ColorWheel.qicon = iconlib.icon("colorwheel", size=-1)

        self.pixmap = utils.pixmapFromIcon(ColorWheel.qicon)
        self.pixmap = self.pixmap.scaled(QtCore.QSize(width, height),
                                         QtCore.Qt.KeepAspectRatio,
                                         QtCore.Qt.SmoothTransformation)

        self.setPixmap(self.pixmap)
        self.setFixedSize(width, height)
        self.qImage = self.pixmap.toImage()

        self.colorHandle = ColorHandle(parent=self)
        initPt = QtCore.QPoint(width / 2, height / 2)
        self.colorHandle.move(initPt)
        self._radius = (self.width() - self._imgPadX * 2) / 2
        self.setPixelColor(initPt)

    def normalizedPoint(self):
        """ Normalized point (y-down is positive, eg QT UI Coordinates)

        :return:
        """
        return qtmath.normalized(self.colorHandle.handlePos() - self.centerPoint())

    def handlePos(self):
        """ Returns the handle position

        :return:
        """
        return self.colorHandle.pos()

    def mousePressEvent(self, event):
        """ Mouse press event

        :param event:
        :return:
        """
        self.pressed = True

    def pointIsInside(self, pt):
        """ Check if point is inside the circle

        :param pt:
        :return:
        """
        dx = abs(pt.x() - self.pixmap.width() / 2)
        dy = abs(pt.y() - self.pixmap.height() / 2)
        R = self.pixmap.width() / 2

        if dx + dy <= R:
            return True

        if dx > R:
            return False

        if dy > R:
            return False

        if dx ** 2 + dy ** 2 <= R ** 2:
            return True
        else:
            return False

    def mouseMoveEvent(self, event):
        """ Mouse Move event. Move handle if pressed

        :param event:
        :return:
        """
        if self.pressed:
            self.moveHandle(event.pos())

    def moveHandle(self, pt):
        self.setUpdatesEnabled(False)
        pt = self.keepInCircle(pt)
        pt = QtCore.QPoint(int(pt.x()), int(pt.y()))
        self.colorHandle.move(pt)
        self.setPixelColor(pt)

        npt = self.normalizedPoint()

        # Distance from center is saturation
        sat = min(qtmath.distance(self.centerPoint(), pt) / (self._radius - 1), 1)

        rgb = self.pointToRGB(npt.x() * sat, npt.y() * sat)

        self.setUpdatesEnabled(True)

    def rgbToPoint(self, rgb):
        normPoint = self.rgbToNormPoint(rgb)
        qtNormPoint = QtCore.QPointF(*normPoint) + QtCore.QPoint(1, 1)
        return qtNormPoint * self._radius

    def colorValue(self):
        return self._color

    def setPixelColor(self, pt):
        color = self.qImage.pixelColor(pt)
        if color.isValid():
            self._color = color.getRgb()[:-1]
            self.colorChanged.emit(self._color)

    def rgbToNormPoint(self, rgb, yUp=False):
        """ RGB to norm point (Y-Up)
        Y-Up is cartesian
        Y-Down is QT ui coordinates

        :param rgb:
        :return:
        """
        hsv = color.convertRgbToHsv(rgb)
        rad = math.radians(hsv[0]) + math.pi * 2 + math.pi * 1.5
        sat = hsv[1]

        pt = -math.cos(rad), math.sin(rad)
        if not yUp:
            pt = pt[0], -pt[1]

        pt = map(lambda x: x * sat, pt)

        return tuple(pt)

    def pointToRGB(self, x, y):
        """ Converts x,y to rgb

        :param x:
        :param y:
        :return:
        """
        y = y
        x = -x
        r = math.sqrt(x * x + y * y)
        sat = 0 if r > 1 else r
        hsv = math.degrees(math.pi * 2 - math.atan2(y, x) - math.pi * 1.5) % 360, sat, 1
        rgb = color.convertHsvToRgb(hsv)
        return rgb

    def centerPoint(self):
        return QtCore.QPoint(self._imgPadX + self._radius, self._imgPadY + self._radius)

    def keepInCircle(self, pt):
        if self.pointIsInside(pt):
            return pt
        else:  # Get the normalized pt then add the radius to keep it on the edge of the circle
            dpt = pt - self.centerPoint()  #
            return qtmath.normalized(dpt) * self._radius + QtCore.QPointF(self._radius, self._radius)

    def mouseReleaseEvent(self, event):
        self.moveHandle(event.pos())
        self.pressed = False


class ValueStrip(QtWidgets.QLabel):
    valueChanged = QtCore.Signal(object)
    qicon = None

    def __init__(self, parent=None):
        super(ValueStrip, self).__init__(parent=parent)
        width, height = 16, 152
        self.pressed = None
        self._vpad = 3

        if not ValueStrip.qicon:
            ValueStrip.qicon = iconlib.icon("valuestrip", size=-1)

        self.pixmap = utils.pixmapFromIcon(ValueStrip.qicon)
        self.pixmap = self.pixmap.scaled(QtCore.QSize(width, height),
                                         QtCore.Qt.KeepAspectRatio,
                                         QtCore.Qt.SmoothTransformation)

        self.setPixmap(self.pixmap)
        self.setFixedSize(width, height)
        self.pixmap.toImage()
        self.handle = ColorHandle(parent=self)
        self.setValue(1.0)

    def mousePressEvent(self, event):
        """ Mouse press event

        :param event:
        :return:
        """
        self.pressed = True

    def setValue(self, val):
        """ Set the value of the value strip. Will move the handle to the correct position

        :param val:
        :return:
        """
        yPos = ((1 - val) * (self.pixmap.height() - self._vpad * 2) + 2)
        self.handle.move(QtCore.QPoint(self.width() / 2, yPos))
        self._value = val

    def mouseMoveEvent(self, event):
        """ Mouse move event

        :param event:
        :return:
        """
        if self.pressed:
            self.setUpdatesEnabled(False)
            self.handle.move(
                QtCore.QPoint(self.width() / 2, max(min(event.y(), self.height() - self._vpad), self._vpad)))
            self.setUpdatesEnabled(True)
            self.valueChanged.emit(self.value())

    def mouseReleaseEvent(self, event):
        self.pressed = False

    def value(self):
        """ Get Value

        :return:
        """
        return 1.0 - (self.handle.y() + 2) / (self.pixmap.height() - self._vpad * 2)


class ColorPicker(ZooWindow):
    colorPickerClosed = QtCore.Signal(object)  # PickerColors
    colorChanged = QtCore.Signal(object)

    def __init__(self, parent=None):
        super(ColorPicker, self).__init__(parent=parent)

    def _initUi(self):
        """ Initialize UI

        :return:
        """
        super(ColorPicker, self)._initUi()

        self.closed.connect(self.popupClosed)

        self.setFixedWidth(220)
        self.setFixedHeight(335)
        self.setTitleStyle(TitleBar.TitleStyle.Thin)

        self.mainLayout = layouts.vBoxLayout(spacing=5)
        self.mainLayout.setContentsMargins(5, 8, 5, 5)
        self.colorWheel = ColorWheel()
        self.valueStrip = ValueStrip()

        self._colorLayoutInit()
        self.colorTabs = JoinedRadioButton(texts=["RGB", "HSV", "HEX"])
        self.colorTabs.buttonClicked.connect(self.colorTabClicked)
        self.mainLayout.addWidget(self.colorTabs)

        self.colorInputLayout = layouts.hBoxLayout()
        self.colorTextLayout = layouts.vBoxLayout(margins=(5, 0, 5, 0))
        self.colorTextLayout.setSpacing(2)

        self.dropperButton = QtWidgets.QPushButton("")
        self.dropperButton.setIcon(iconlib.icon("eyedropper"))
        self.dropperButton.setFixedWidth(self.dropperButton.sizeHint().height())

        self.alphaEdit = stringedit.FloatEdit("A", editRatio=10)
        self.alphaEdit.setValue(1.0)
        self.stackedWidget = self.stackedWidgetColors()
        self.colorTextLayout.addWidget(self.stackedWidget)
        self.colorTextLayout.addWidget(self.alphaEdit)
        self.colorInputLayout.addLayout(self.colorTextLayout)

        dropperLayout = layouts.vBoxLayout(margins=(0, 0, 0, 0), spacing=0)
        dropperLayout.addWidget(self.dropperButton)
        dropperLayout.addStretch()
        self.colorInputLayout.addLayout(dropperLayout)

        self.mainLayout.addSpacing(2)
        self.mainLayout.addLayout(self.colorInputLayout)
        self.mainLayout.addStretch()

        self.setMainLayout(self.mainLayout)
        self._color = (255, 255, 255)
        self._alpha = 1.0
        self._value = 1.0

        self.colorWheel.colorChanged.connect(self.colorWheelChanged)
        self.alphaEdit.textChanged.connect(self.alphaChanged)
        self.valueStrip.valueChanged.connect(self.valueChanged)

    def popupClosed(self):
        """ Popup closed
        
        :return: 
        """
        self.colorPickerClosed.emit(self.colors())

    def colors(self):
        """ Converts all the values and turns it into a colour picker event

        :return:
        """
        # Convert to hsv as we need the value
        hsv = color.convertRgbToHsv(self._color)
        hsv = hsv[0], hsv[1], self._value

        rgb = tuple(map(round, color.hsv2rgb(*hsv)))
        hex = color.RGBToHex(rgb)
        return PickerColors(rgb=rgb, hsv=hsv, hex=hex, a=self._alpha)

    def rgb(self):
        """ Gets the rgb from the color picker
        
        :return: 
        """
        return self.colors().rgb

    def hsv(self):
        """ Returns the HSV from the color picker

        :return:
        """
        return self.colors().hsv

    def hexColor(self):
        """ Returns the hex color

        :return:
        """
        return self.colors().hex

    def _colorLayoutInit(self):
        """ Initialize Layout init

        :return:
        """
        self.colorLayout = layouts.hBoxLayout(margins=(0, 0, 0, 8))

        self.colorLayout.addWidget(self.colorWheel)
        self.colorLayout.addWidget(self.valueStrip)
        self.mainLayout.addLayout(self.colorLayout)

    def valueChanged(self, value):
        """ Value changed

        :param value:
        :return:
        """
        self._value = value

        self.valLineEdit.edit.setText(str(self.valueStrip.value()))

        self.colorWheelChanged(self._color)
        self.colorChanged.emit(self.colors())

    def alphaChanged(self, text):
        """ Alpha Changed

        :param text:
        :return:
        """
        self._alpha = min(max(0, float(text)), 1.0)

    def colorWheelChanged(self, col):
        """ Color wheel changed

        :param color:
        :return:
        """
        self._color = col

        # Convert to hsv as we need the value
        hsv = color.convertRgbToHsv(col)
        hsv = hsv[0], hsv[1], self._value
        self.setHSVEdit(hsv)
        self.setHexEditHSV(hsv)
        self.setRGBEdits(tuple(map(round, color.hsv2rgb(*hsv))))

        self.colorChanged.emit(self.colors())

    def setHSVEdit(self, hsv):
        """ Set the HSV Edit

        :param hsv:
        :return:
        """
        self.hueLineEdit.setValue(hsv[0])
        self.satLineEdit.setValue(hsv[1])
        self.valLineEdit.setValue(hsv[2])

    def setHexEditRGB(self, rgb):
        """ Set the Hex edit based on RGB

        :param rgb:
        :return:
        """
        self.hexLineEdit.edit.setText(str(color.RGBToHex(rgb)))

    def setHexEditHSV(self, hsv):
        """ Set the Hex edit based on HSV

        :param hsv:
        :return:
        """
        rgb = tuple(map(int, color.hsv2rgb(*hsv)))
        self.setHexEditRGB(rgb)

    def setRGBEdits(self, rgb):
        """ Set the RGB edit widgets

        :param rgb:
        :return:
        """
        self.redLineEdit.setValue(rgb[0])
        self.greenLineEdit.setValue(rgb[1])
        self.blueLineEdit.setValue(rgb[2])

    def colorTabClicked(self, event):
        """ Color tab clicked

        :param event:
        :return:
        """
        index = {"RGB": 0,
                 "HSV": 1,
                 "HEX": 2
                 }
        self.stackedWidget.setCurrentIndex(index[event.text])

    def stackedWidgetColors(self):
        """ Initialize stacked widget colors

        :return:
        """
        wgt = QtWidgets.QStackedWidget()
        rgbWidget = QtWidgets.QWidget()

        rgbLayout = layouts.vBoxLayout()
        rgbLayout.setSpacing(2)
        rgbLayout.setContentsMargins(0, 0, 0, 0)
        editLength = 20
        self.redLineEdit = stringedit.IntEdit("R", editRatio=10)
        self.greenLineEdit = stringedit.IntEdit("G", editRatio=10)
        self.blueLineEdit = stringedit.IntEdit("B", editRatio=10)
        self.redLineEdit.label.setFixedWidth(editLength)
        self.greenLineEdit.label.setFixedWidth(editLength)
        self.blueLineEdit.label.setFixedWidth(editLength)
        self.alphaEdit.label.setFixedWidth(editLength)

        rgbLayout.addWidget(self.redLineEdit)
        rgbLayout.addWidget(self.greenLineEdit)
        rgbLayout.addWidget(self.blueLineEdit)
        rgbLayout.addStretch()
        rgbWidget.setLayout(rgbLayout)

        hsvWidget = QtWidgets.QWidget()
        hsvLayout = layouts.vBoxLayout()
        hsvLayout.setSpacing(2)
        hsvLayout.setContentsMargins(0, 0, 0, 0)
        self.hueLineEdit = stringedit.FloatEdit("H", editRatio=10)
        self.satLineEdit = stringedit.FloatEdit("S", editRatio=10)
        self.valLineEdit = stringedit.FloatEdit("V", editRatio=10)
        self.hueLineEdit.label.setFixedWidth(editLength)
        self.satLineEdit.label.setFixedWidth(editLength)
        self.valLineEdit.label.setFixedWidth(editLength)

        hsvLayout.addWidget(self.hueLineEdit)
        hsvLayout.addWidget(self.satLineEdit)
        hsvLayout.addWidget(self.valLineEdit)
        hsvLayout.addStretch()
        hsvWidget.setLayout(hsvLayout)

        hexWidget = QtWidgets.QWidget()
        hexLayout = layouts.vBoxLayout()
        hexLayout.setSpacing(0)
        hexLayout.setContentsMargins(0, 0, 0, 0)
        self.hexLineEdit = stringedit.FloatEdit("Hex:")
        self.hexLineEdit.label.setFixedWidth(editLength)
        hexLayout.addWidget(self.hexLineEdit)
        hexLayout.addStretch()
        hexWidget.setLayout(hexLayout)

        wgt.addWidget(rgbWidget)
        wgt.addWidget(hsvWidget)
        wgt.addWidget(hexWidget)

        wgt.setFixedHeight(60)
        wgt.setCurrentIndex(0)
        return wgt
