from zoovendor.Qt import QtWidgets, QtCore
from zoo.libs.pyqt import uiconstants
from zoo.libs.pyqt.widgets import layouts


class RadioButtonGroup(QtWidgets.QWidget):
    """Creates a horizontal group of radio buttons

    Build widget example:
        self.radioWidget = elements.RadioButtonGroup(radioList=radioNameList, toolTipList=radioToolTipList,
                                                            default=0, parent=parent)

    Query the checked selection example:
        nameChecked = radioWidget.getChecked().text()  # returns the text name of the checked item
        numberChecked = radioWidget.getCheckedIndex() # returns the list number of the checked item

    Return Selection Changed example:
        radioWidget.toggled.connect(self.doSomething)
    """
    toggled = QtCore.Signal(int)

    def __init__(self, radioList=None, toolTipList=None, default=0, parent=None, vertical=False,
                 margins=(uiconstants.REGPAD, uiconstants.REGPAD, uiconstants.REGPAD, 0), spacing=uiconstants.SREG,
                 alignment=None):
        """Horizontal group of radio buttons

        :param radioList: a list of radio button names (strings)
        :type radioList: list[str]
        :param toolTipList: A list of tooltips, one for each radio button.
        :type toolTipList: list[str]
        :param default: the default button to be checked as on, starts at 0 matching the list
        :type default: int
        :param parent: the parent widget
        :type parent: obj
        :param margins: override the margins with this value (left, top, right, bottom)
        :type margins: obj
        :param spacing: override the spacing with this pixel value
        :type spacing: obj
        :param alignment: radio button layout alignment.
        :type alignment: QtCore.Qt.Align
        """
        super(RadioButtonGroup, self).__init__(parent=parent)
        if radioList is None:
            radioList = []
        self.radioButtons = []  # type: list[QtWidgets.QRadioButton]
        self.group = QtWidgets.QButtonGroup(parent=self)
        if not vertical:
            radioLayout = layouts.hBoxLayout(parent=self, margins=margins, spacing=spacing)
        else:
            radioLayout = layouts.vBoxLayout(parent=self, margins=margins, spacing=spacing)
        for i, radioName in enumerate(radioList):
            newRadio = QtWidgets.QRadioButton(radioName, self)
            if toolTipList:
                newRadio.setToolTip(toolTipList[i])
            self.group.addButton(newRadio)
            radioLayout.addWidget(newRadio)
            self.radioButtons.append(newRadio)
        if default is not None and default < len(self.radioButtons):
            self.radioButtons[default].setChecked(True)
        if alignment is not None:
            for btn in self.radioButtons:
                radioLayout.setAlignment(btn, alignment)
        self.group.buttonClicked.connect(lambda x: self.toggled.emit(self.checkedIndex()))

    def checked(self):
        """ Returns the widget that is checked.

        :return: The widget that is checked
        :rtype: QtWidgets.QRadioButton()
        """
        for radioBtn in self.radioButtons:
            if radioBtn.isChecked():
                return radioBtn

    def checkedIndex(self):
        """ Returns the widget number that is checked

        :return: the widget list number that is checked
        :rtype: int
        """
        for i, radioBtn in enumerate(self.radioButtons):
            if radioBtn.isChecked():
                return i

    def setChecked(self, index):
        """ Checks the radio button at index.

        :param index: The radio button index within the group.
        :type index: int
        """
        index = index or 0
        self.radioButtons[index].setChecked(True)