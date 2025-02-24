from zoovendor.Qt import QtGui, QtCore
from zoovendor import Qt


class UpperCaseValidator(QtGui.QValidator):
    """Validator that keeps the text upper case
    todo: untested

    """

    def validate(self, string, pos):
        return QtGui.QValidator.Acceptable, string.upper(), pos


if Qt.__qt_version__ <= "5.12.5":

    def createRegexValidator(strValue, parent):
        return QtGui.QRegExpValidator(QtCore.QRegExp(strValue), parent)

else:

    def createRegexValidator(strValue, parent):
        return QtGui.QRegularExpressionValidator(
            QtCore.QRegularExpression(strValue), parent
        )
