from zoovendor.Qt import QtWidgets, QtGui, QtCore


class NumberBar(QtWidgets.QWidget):

    def __init__(self, edit):
        super(NumberBar, self).__init__(edit)

        self.editor = edit
        self.adjustWidth()

    def paintEvent(self, event):
        super(NumberBar, self).paintEvent(event)
        if not self.isVisible():
            return
        editor = self.editor
        fontMetrics = editor.fontMetrics()
        current_line = editor.document().findBlock(editor.textCursor().position()).blockNumber() + 1

        rect = event.rect()
        painter = QtGui.QPainter(self)
        painter.fillRect(event.rect(), QtGui.QColor(49, 51, 53))
        painter.setPen(QtGui.QColor(49, 51, 53))
        painter.setBrush(QtGui.QBrush(QtGui.QColor(0, 0, 0)))
        font = editor.font()

        block = editor.firstVisibleBlock()
        blockNumber = block.blockNumber()
        blockTop = editor.blockBoundingGeometry(block).translated(editor.contentOffset()).top()
        bottom = blockTop + int(editor.blockBoundingGeometry(block).height())
        width = self.width()
        height = fontMetrics.height()
        # Iterate over all visible text blocks in the document.
        while block.isValid() and blockTop <= rect.bottom():
            if block.isVisible() and bottom >= rect.top():
                num = str(blockNumber + 1)
                # We want the line number for the selected line to be bold.
                if num == current_line:
                    font.setBold(True)
                else:
                    font.setBold(False)
                painter.setFont(font)
                painter.setPen(QtGui.QColor(96, 99, 102))
                painter.drawText(
                    -2,
                    blockTop,
                    width,
                    height,
                    QtCore.Qt.AlignRight,
                    num,
                )

            block = block.next()
            blockTop = bottom
            bottom = blockTop + int(editor.blockBoundingRect(block).height())
            blockNumber += 1

        painter.end()

    def adjustWidth(self):
        width = 6 + self.editor.fontMetrics().horizontalAdvance(str(self.editor.blockCount()))

        if self.width() != width:
            self.setFixedWidth(width)
        self.update()

    def updateContents(self, rect, scroll):
        self.adjustWidth()
