from zoovendor.Qt import QtWidgets
from zoo.libs.pyqt.extended.menu import MenuCreateClickMethods

class CheckBox(QtWidgets.QWidget, QtWidgets.QCheckBox, MenuCreateClickMethods):
    def __init__(self, label, checked=False, parent=None, toolTip="", enableMenu=True, menuVOffset=20, right=False,
                 labelRatio=0, boxRatio=0): ...
