from zoo.libs import iconlib
from zoo.libs.pyqt import utils, uiconstants
from zoo.libs.pyqt.widgets import dialog, elements
from zoo.libs.pyqt.widgets.overlay import OverlayWidget
from zoovendor.Qt import QtCore, QtWidgets


class LoadingWidget(OverlayWidget):
    def __init__(self, parent):
        super(LoadingWidget, self).__init__(parent=parent, layout=QtWidgets.QHBoxLayout)

    def initUi(self):
        super(LoadingWidget, self).initUi()
        self.setStyleSheet("LoadingWidget {background-color: #77111111;}")

        label = QtWidgets.QLabel("Loading...  ", self)
        imageLabel = QtWidgets.QLabel(self)
        s = utils.dpiScale(24)
        imageLabel.setPixmap(iconlib.iconColorizedLayered("loading", size=s).pixmap(s, s))

        self.loadingFrame = LoadingFrame(self)
        self.loadingFrameLayout = elements.hBoxLayout()
        self.layout.addStretch(1)
        self.layout.addWidget(self.loadingFrame)
        self.layout.addStretch(1)

        # The loading widget with the label and text
        self.loadingFrame.setLayout(self.loadingFrameLayout)
        self.loadingFrameLayout.addWidget(imageLabel)
        self.loadingFrameLayout.addWidget(label)
        self.loadingFrameLayout.setContentsMargins(*utils.marginsDpiScale(5, 0, 5, 0))
        self.loadingFrameLayout.setStretch(0, 2)
        self.loadingFrameLayout.setStretch(1, 3)


        self.loadingFrame.setFixedSize(utils.sizeByDpi(QtCore.QSize(150, 40)))
        utils.setStylesheetObjectName(self.loadingFrame, "border")

    def update(self):
        x1 = uiconstants.FRAMELESS_HORIZONTAL_PAD
        y1 = uiconstants.FRAMELESS_VERTICAL_PAD

        xPad = uiconstants.FRAMELESS_HORIZONTAL_PAD
        yPad = uiconstants.FRAMELESS_VERTICAL_PAD

        self.setGeometry(x1, y1,
                         self.parent().geometry().width()-xPad*2,
                         self.parent().geometry().height()-yPad*2)
        super(dialog.Dialog, self).update()
    def mousePressEvent(self, event):
        """ If it can be pressed it can be hidden

        :param event:
        :type event:
        :return:
        :rtype:
        """
        super(LoadingWidget, self).mousePressEvent(event)
        self.hide()

class LoadingFrame(QtWidgets.QFrame):
    """ For CSS Purposes """

