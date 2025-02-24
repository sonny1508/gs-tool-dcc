import logging
import sys

from zoovendor.Qt import QtGui, QtWidgets, QtCore
from zoo.core.util import zlogging

if sys.version_info.major == 2:
    from cgi import escape
elif sys.version_info.major == 3:
    from html import escape as escape

logger = zlogging.getLogger(__name__)


def shiftColor(c1, c1Strength, c2, c2Strength):
    total = c1Strength + c2Strength

    r = ((c1.red() * c1Strength) + (c2.red() * c2Strength)) / total
    g = ((c1.green() * c1Strength) + (c2.green() * c2Strength)) / total
    b = ((c1.blue() * c1Strength) + (c2.blue() * c2Strength)) / total

    return QtGui.QColor(r, g, b)


class OutputLogDialog(QtWidgets.QPlainTextEdit):
    """Output text edit

    ::example:
        wid = OutputLogDialog("MyLogWindow")
        wid.show()
        wid.logInfo("helloworld")
        wid.logDebug("helloworld")
        wid.logWarning("helloworld")
        wid.logError("helloworld")
        wid.logCritical("helloworld")

    """
    infoColor = QtGui.QColor(QtCore.Qt.white)
    debugColor = QtGui.QColor("#f4f4f4")
    warningColor = QtGui.QColor("#ffe700")
    errorColor = QtGui.QColor("#CC0000")
    criticalColor = QtGui.QColor("#CC0000")

    def __init__(self, title, parent=None):
        super(OutputLogDialog, self).__init__(parent)
        self.setReadOnly(True)
        self.setWordWrapMode(QtGui.QTextOption.NoWrap)
        self.setObjectName('{}OutputLog'.format(title))
        self.createLayout()
        # use the built logging module for the levels since that would be more consistent
        self.outputType = logging.INFO

    def createLayout(self):
        """Sets up the layout for the dialog."""

        self.setWordWrapMode(QtGui.QTextOption.NoWrap)
        self.setReadOnly(True)

    def logInfo(self, msg):
        _input_color = shiftColor(self.palette().base().color(), 1, self.infoColor, 2)
        self.write(msg, _input_color)

    def logDebug(self, msg):
        _input_color = shiftColor(self.palette().base().color(), 1, self.debugColor, 2)
        self.write(msg, _input_color)

    def logWarning(self, msg):
        _input_color = shiftColor(self.palette().base().color(), 1, self.warningColor, 2)
        self.write(msg, _input_color)

    def logError(self, msg):
        _input_color = shiftColor(self.palette().base().color(), 1, self.errorColor, 3)
        self.write(msg, _input_color)

    def logCritical(self, msg):
        _input_color = shiftColor(self.palette().base().color(), 1, self.criticalColor, 3)
        self.write(msg, _input_color)

    def keyEvent(self, event):
        if event.key() == QtCore.Qt.Key_Delete:
            self.clear()

    def write(self, msg, color=QtGui.QColor(QtCore.Qt.white)):
        msg = escape(msg)
        # deal with multi line strings ie. stacktraces
        msg = msg.replace(" ", "&nbsp;")
        msg = msg.replace("\n", "<br/>")
        html = """<font color="{}">{}</font>""".format(color.name(), msg)
        self.appendHtml(html)

    def factoryLog(self, msg, level):
        if level == logging.INFO:
            self.logInfo(msg)
        elif level == logging.DEBUG:
            self.logDebug(msg)
        elif level == logging.WARNING:
            self.logWarning(msg)
        elif level == logging.ERROR:
            self.logError(msg)
        elif level == logging.CRITICAL:
            self.logCritical(msg)

    def wheelEvent(self, event):
        """
        Handles zoom in/out of the text.
        """
        if event.modifiers() & QtCore.Qt.ControlModifier:
            delta = event.angleDelta().y()
            if delta < 0:
                self.zoom(-1)
            elif delta > 0:
                self.zoom(1)
            return True
        return super(OutputLogDialog, self).wheelEvent(event)

    def zoom(self, direction):
        """
        Zoom in on the text.
        """

        font = self.font()
        size = font.pointSize()
        if size == -1:
            size = font.pixelSize()

        size += direction

        if size < 7:
            size = 7
        if size > 50:
            return

        style = """
        QWidget {
            font-size: %spt;
        }
        """ % (size,)
        self.setStyleSheet(style)

    def contextMenuEvent(self, event):
        """Creates a context menu for the log window"""
        menu = self.createStandardContextMenu()
        clearAction = menu.addAction("Clear")
        clearAction.triggered.connect(self.clear)
        menu.exec_(event.globalPos())

class QWidgetHandler(logging.Handler):
    """Custom Qt Logging Handler for Sending Messages to child Widgets"""

    def __init__(self):
        super(QWidgetHandler, self).__init__()
        self._widgets = []

    def addWidget(self, widget):
        if widget not in self._widgets:
            self._widgets.append(widget)

    def removeWidget(self, widget):
        if widget in self._widgets:
            self._widgets.remove(widget)

    def clearWidgets(self):
        self._widgets = []

    def emit(self, record):
        msg = self.format(record)

        for widget in self._widgets:
            widget.factoryLog(msg, record.levelno)
