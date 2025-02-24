from zoovendor.Qt import QtWidgets, QtGui
from zoo.libs.pyqt import utils


def heightForWidth(textEdit, width):
    margins = textEdit.documentMargins()
    # Cloning the whole document only to check its size at different width seems wasteful
    # but apparently it's the only and preferred way to do this in Qt >= 4. QTextDocument does not
    # provide any means to get height for specified width (as some QWidget subclasses do).
    # Neither does QTextEdit. In Qt3 Q3TextEdit had working implementation of heightForWidth()
    # but it was allegedly just a hack and was removed.
    #
    # The performance probably won't be a problem here because the application is meant to
    # work with a lot of small notes rather than few big ones. And there's usually only one
    # editor that needs to be dynamically resized - the one having focus.
    document = textEdit.document().clone()
    document.setTextWidth(width)

    return margins[0] + document.size().height() + margins[2]


def lineCountToWidgetHeight(textEdit, num_lines):
    """ Returns the number of pixels corresponding to the height of specified number of lines
        in the default font. """

    assert num_lines >= 0

    widget_margins = textEdit.contentsMargins()
    document_margin = textEdit.document().documentMargin()
    font_metrics = QtGui.QFontMetrics(textEdit.document().defaultFont())

    return (
            widget_margins.top() +
            document_margin +
            max(num_lines, 1) * font_metrics.height() +
            document_margin +
            widget_margins.bottom()
    )


class TextEdit(QtWidgets.QTextEdit):
    def __init__(self, text="", parent=None, placeholderText="", toolTip="", editWidth=None, minimumHeight=None,
                 maximumHeight=None, fixedWidth=None, fixedHeight=None):
        super(TextEdit, self).__init__(parent=parent)

        if fixedHeight:
            self.setFixedHeight(utils.dpiScale(fixedHeight))
        if minimumHeight:
            self.setMinimumHeight(utils.dpiScale(minimumHeight))
        if maximumHeight:
            self.setMaximumHeight(utils.dpiScale(maximumHeight))
        if fixedWidth:
            self.setFixedWidth(utils.dpiScale(fixedWidth))
        self.setPlaceholderText(placeholderText)
        self.setPlainText(text)
        self.setToolTip(toolTip)

    def documentMargins(self):
        format = self.document().rootFrame().frameFormat()
        return [format.topMargin(), format.rightMargin(), format.bottomMargin(), format.leftMargin()]

    def setDocumentMargins(self, top, right, bottom, left):
        format = self.document().rootFrame().frameFormat()
        format.setTopMargin(top)
        format.setRightMargin(right)
        format.setBottomMargin(bottom)
        format.setLeftMargin(left)
        self.document().rootFrame().setFrameFormat(format)

    heightForWidth = heightForWidth
    lineCountToWidgetHeight = lineCountToWidgetHeight
