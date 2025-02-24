from collections import namedtuple

from zoo.libs.pyqt import utils
from zoo.libs.pyqt.widgets import layouts
from zoovendor.Qt import QtWidgets, QtCore

JoinedRadioButtonEvent = namedtuple('JoinedRadioButtonEvent', 'button,text,index')


class JoinedRadioButton(QtWidgets.QFrame):
    buttonClicked = QtCore.Signal(object)  # JoinedRadioButtonEvent

    def __init__(self, parent=None, texts=None, btnHeight=20, toolTips=None):
        texts = texts or [""]
        self.btnHeight = btnHeight
        super(JoinedRadioButton, self).__init__(parent=parent)

        self._initUi(texts, toolTips=toolTips)

    def _initUi(self, texts, toolTips=None):
        """ Initialize Joined Radio button

        :param texts:
        :return:
        """
        layout = layouts.hBoxLayout()
        self.setLayout(layout)
        layout.setSpacing(0)

        self._buttonGroup = QtWidgets.QButtonGroup(parent=self)
        policy = QtWidgets.QSizePolicy.Policy.Preferred

        self.setSizePolicy(policy, self.sizePolicy().verticalPolicy())

        for i, t in enumerate(texts):
            b = QtWidgets.QPushButton(text=t, parent=self)
            if toolTips:
                try:
                    b.setToolTip(toolTips[i])
                except:
                    pass
            self._buttonGroup.addButton(b)
            b.setSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, b.sizePolicy().horizontalPolicy())
            b.setFixedHeight(utils.dpiScale(self.btnHeight))

            b.setCheckable(True)

            layout.addWidget(b, stretch=1)

            if i == 0:
                obName = "left"
            elif i == len(texts) - 1:
                obName = "right"
            else:
                obName = "center"

            b.setObjectName(obName)
            b.setStyle(b.style())

        layout.setContentsMargins(0, 0, 0, 0)

        self._buttonGroup.buttonClicked.connect(self.onButtonClicked)
        self._buttonGroup.setExclusive(True)
        self._buttonGroup.buttons()[0].setChecked(True)

    def onButtonClicked(self, button):
        """ Button Released

        :param button:
        :return:
        """
        self.buttonClicked.emit(JoinedRadioButtonEvent(button=button, text=button.text(), index=self._buttonGroup.buttons().index(button)))

    def setChecked(self, index):

        self.buttons()[index].setChecked(True)

    def buttons(self):
        return self._buttonGroup.buttons()
