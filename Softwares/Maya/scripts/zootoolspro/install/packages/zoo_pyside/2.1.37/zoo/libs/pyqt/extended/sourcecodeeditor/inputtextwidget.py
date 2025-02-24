from zoo.libs.pyqt import keyboardmouse
from zoo.libs.pyqt.widgets import textedit
from zoovendor.Qt import QtWidgets, QtGui, QtCore


class TextEditor(QtWidgets.QPlainTextEdit):
    """

    :Todo: Operations like duplicate line etc should all be plugins

    Standard hotkeys.

    #. "[", "Shift+{", "Shift+(", ", ', surround text with {}, [], (), ""
    #. "Return", simple new line as normal
    #. "Shift+Return", new line but only moves the cursor not the text
    #. "Shift+BackTab",  dedent or un-indent the current selected lines
    #. "Tab", indent the current selected lines
    #. "Ctrl+Return", "Ctrl+Enter", Execute selection code
    #. "Ctrl+Shift+Return", "Ctrl+Shift+Enter", Execute all code
    #. "Ctrl+/", comment out line
    #. "Ctrl+D", duplicate line
    #. "Shift+Del", delete the current line.
    """
    executed = QtCore.Signal(str)

    def __init__(self, parent=None):
        super(TextEditor, self).__init__(parent=parent)
        self.setTextInteractionFlags(QtCore.Qt.TextEditorInteraction)
        self.setWordWrapMode(QtGui.QTextOption.NoWrap)
        self.setFrameStyle(QtWidgets.QFrame.NoFrame)
        self.centerOnScroll()
        metrics = QtGui.QFontMetrics(self.document().defaultFont())
        self.setTabStopDistance(4 * metrics.horizontalAdvance(' '))
        self.cursorPositionChanged.connect(self.highlight)
        self.hotkeys = {}

        self.addHotKey("[", func=surroundTextSquareBracket, name="surroundTextSquareBracket")
        self.addHotKey("Shift+{", func=surroundTextCurlyBracket, name="surroundTextCurlyBracket")
        self.addHotKey("Shift+(", func=surroundTextBracket, name="surroundTextBracket")
        self.addHotKey("'", func=surroundSingleQuote, name="surroundSingleQuote")
        self.addHotKey("''", func=surroundDoubleSingleQuote, name="surroundDoubleSingleQuote")
        self.addHotKey('Shift+"', func=surroundDoubleQuote, name="surroundDoubleQuote")
        self.addHotKey('Return', func=hotkeyCommandInsertNewLine, name="insertNewLine")
        self.addHotKey('Shift+Return', func=hotkeyCommandToNewLine, name="newLine")
        self.addHotKey("Ctrl+/", func=hotkeyCommandCommentLine, name="commentLine")
        self.addHotKey("Shift+Backtab", func=hotkeyCommandDedent, name="dedent")
        self.addHotKey("Tab", func=hotkeyCommandIndent, name="indent")
        self.addHotKey("Ctrl+Return", func=hotkeyCommandExecuteSelection,
                       name="executeSelectionReturn")
        self.addHotKey("Ctrl+Enter", func=hotkeyCommandExecuteSelection,
                       name="executeSelectionEnter")
        self.addHotKey("Ctrl+Shift+Enter", func=hotkeyCommandExecuteAll, name="executeAllEnter")
        self.addHotKey("Ctrl+Shift+Return", func=hotkeyCommandExecuteAll, name="executeAllReturn")
        self.addHotKey('Ctrl+D', func=hotkeyCommandDuplicateLine, name="duplicateLine")
        self.addHotKey('Shift+Del', func=hotkeyCommandDeleteLine, name="deleteLine")

    def addHotKey(self, key, func, name):
        self.hotkeys[key] = {"function": func,
                             'name': name}

    def removeHotKeyByName(self, name):
        for key, value in self.hotkeys.items():
            if value['name'] == name:
                del self.hotkeys[key]
                return

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

    def highlight(self):
        hi_selection = QtWidgets.QTextEdit.ExtraSelection()
        backgroundColor = self.palette().color(self.backgroundRole())
        backgroundColor = backgroundColor.lighter(120)
        backgroundBrush = QtGui.QBrush(backgroundColor)
        hi_selection.format.setBackground(backgroundBrush)  # temp
        hi_selection.format.setProperty(QtGui.QTextFormat.FullWidthSelection, True)
        hi_selection.cursor = self.textCursor()
        hi_selection.cursor.clearSelection()

        self.setExtraSelections([hi_selection])

    def indent(self):
        cursor = self.textCursor()
        if not cursor.hasSelection():
            cursor.beginEditBlock()
            cursor.insertText(" " * (4 - cursor.positionInBlock() % 4))
            cursor.endEditBlock()
            return

        doc = self.document()
        cursor.beginEditBlock()
        nb_lines = len(cursor.selection().toPlainText().splitlines())
        c = self.textCursor()
        if c.atBlockStart() and c.position() == c.selectionEnd():
            nb_lines += 1
        block = doc.findBlock(cursor.selectionStart())
        i = 0
        cursor = QtGui.QTextCursor(block)
        # indent every lines
        while i < nb_lines:
            cursor.insertText(" " * 4)
            cursor.movePosition(cursor.NextBlock, cursor.MoveAnchor)
            cursor.movePosition(cursor.StartOfLine, cursor.MoveAnchor)
            i += 1
        cursor.endEditBlock()

    def dedent(self):
        cursor = self.textCursor()
        cursor.beginEditBlock()

        lineCount = len(self.selectedLines())
        doc = self.document()
        block = doc.findBlock(cursor.selectionStart())
        startPos = block.position()
        endPos = cursor.position()
        i = 0
        while i < lineCount:
            cursor.setPosition(block.position(), cursor.MoveAnchor)
            text = block.text()
            cursor.movePosition(cursor.StartOfLine, cursor.MoveAnchor)
            for _ in range(4):
                if len(text) and text[0] == " ":
                    cursor.deleteChar()
            endPos = block.position() + block.length()
            block = block.next()
            i += 1
        cursor.setPosition(startPos, cursor.MoveAnchor)
        cursor.setPosition(endPos, cursor.KeepAnchor)
        cursor.endEditBlock()

    def selectedLines(self):
        cursor = self.textCursor()
        selection = cursor.selection()
        if not selection.isEmpty():
            selLines = selection.toPlainText().split("\n")
            selStart = cursor.selectionStart()
            lines = []
            cursor.setPosition(selStart, cursor.MoveAnchor)
            cursor.movePosition(cursor.StartOfLine, cursor.MoveAnchor)
            for _ in range(len(selLines)):
                lines.append(cursor.block().text())
                cursor.movePosition(cursor.NextBlock, cursor.MoveAnchor)
            return lines
        return [self.lineText(cursor.blockNumber())]

    def selectionPosition(self, cursor):
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        if start > end:
            start = end
        return start, end

    def blockComment(self):

        def commentOp():
            lines = self.selectedLines()
            minIndent = 0  # space indent count
            comment = False  # whether we need to comment, basically if any line has no comment then we comment.
            for line in lines:
                strippedLine = line.lstrip(" ")
                indent = len(line) - len(strippedLine)
                if indent < minIndent:
                    minIndent = indent
                if not strippedLine.startswith("#"):
                    comment = True
            return minIndent, comment, len(lines), lines

        cursor = self.textCursor()
        indentCount, shouldComment, lineCount, selLines = commentOp()

        # multi line comment
        cursor.beginEditBlock()
        try:
            if lineCount > 1:
                selectionPosition = self.selectionPosition(cursor)

                cursor.setPosition(selectionPosition[0])
                for i in range(lineCount):
                    self.commentLine(indentCount, cursor, shouldComment, newLine=True)
                    cursor.movePosition(cursor.NextBlock)

                return
            # single line comment
            self.commentLine(indentCount, cursor, shouldComment, newLine=False)

        finally:
            cursor.endEditBlock()

    def commentLine(self, indent, cursor, comment, newLine=True):

        cursor.movePosition(cursor.StartOfLine)
        cursor.movePosition(cursor.Right, cursor.MoveAnchor, indent)
        if comment:
            cursor.insertText("# ")
            if newLine and cursor.atEnd():
                cursor.insertText("\n")
            return
        # it's already commented so delete the comment text + space
        cursor.deleteChar()
        cursor.deleteChar()

    def currentLineNum(self):
        return self.textCursor().blockNumber()

    def lineCount(self):
        return self.document().blockCount()

    def lineText(self, lineNumber):
        return self.document().findBlockByLineNumber(lineNumber).text()

    def previousLineText(self):
        currentLineNum = self.currentLineNum()
        if currentLineNum:
            return self.lineText(currentLineNum - 1)
        return ""

    def nextLineText(self):
        return self.lineText(self.currentLineNum())

    def lineIndent(self, lineNumber=None):
        lineNumber = lineNumber or self.currentLineNum()
        lineText = self.lineText(lineNumber)
        return len(lineText) - len(lineText.lstrip())

    def insertNewLine(self, includeText=False, maintainIndent=True, cursor=None):
        cursor = cursor or self.textCursor()
        lineIndent = self.lineIndent()
        cursor.beginEditBlock()
        if cursor.hasSelection():
            start, end = self.selectionPosition(cursor)
            if not includeText:
                cursor.setPosition(end)
        elif not includeText:
            cursor.movePosition(cursor.EndOfBlock)
        cursor.insertText("\n")
        if maintainIndent:
            cursor.insertText(" " * lineIndent)
        cursor.endEditBlock()
        self.setTextCursor(cursor)

    def duplicateLines(self):
        cursor = self.textCursor()
        cursor.beginEditBlock()
        lines = self.selectedLines()
        lines[0] = lines[0].lstrip()
        self.insertNewLine(False, cursor=cursor)
        self.insertPlainText("\n".join(lines))

        self.setTextCursor(cursor)
        cursor.endEditBlock()

    def removeLine(self, lineNumber=None):
        cursor = self.textCursor()
        cursor.beginEditBlock()
        lineNumber = lineNumber or self.currentLineNum()
        cursor.movePosition(cursor.Start)
        cursor.movePosition(cursor.Down, cursor.MoveAnchor, lineNumber)
        cursor.select(cursor.LineUnderCursor)
        cursor.removeSelectedText()
        cursor.deleteChar()
        self.setTextCursor(cursor)
        cursor.endEditBlock()

    def surroundText(self, text):
        cursor = self.textCursor()
        textHalfLen = int(len(text) * 0.5)
        first, last = text[:textHalfLen], text[textHalfLen:]
        if not cursor.hasSelection():
            cursor.beginEditBlock()
            cursor.insertText(first)
            cursor.insertText(last)
            cursor.movePosition(cursor.Left, cursor.MoveAnchor, 1)
            self.setTextCursor(cursor)
            cursor.endEditBlock()
            return
        cursor.beginEditBlock()
        startPos, endPos = self.selectionPosition(cursor)
        cursor.clearSelection()
        self.setTextCursor(cursor)
        cursor.setPosition(startPos)
        cursor.insertText(first)

        cursor.setPosition(endPos + 1)
        cursor.insertText(last)
        cursor.endEditBlock()

    heightForWidth = textedit.heightForWidth
    lineCountToWidgetHeight = textedit.lineCountToWidgetHeight

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
        return super(TextEditor, self).wheelEvent(event)

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

    def keyPressEvent(self, event):
        sequence = keyboardmouse.eventKeySequence(event, includeShiftForSpecialCharacters=True,
                                                  acceptedShiftCombinations=[QtCore.Qt.Key_Delete])
        keyStr = sequence.toString()
        command = self.hotkeys.get(keyStr)
        if command is not None and not command["function"](self, event):
            return
        super(TextEditor, self).keyPressEvent(event)


def hotkeyCommandDuplicateLine(editor, event):
    """

    :param editor:
    :type editor: :class:`InputEditor`
    :param event:
    :type event: :class:`QtCore.QKeyPressEvent`
    :return: Whether to call super on the base class.
    :rtype: bool
    """
    editor.duplicateLines()
    event.accept()
    return False


def hotkeyCommandDeleteLine(editor, event):
    """

    :param editor:
    :type editor: :class:`InputEditor`
    :param event:
    :type event: :class:`QtCore.QKeyPressEvent`
    :return: Whether to call super on the base class.
    :rtype: bool
    """
    if not editor.textCursor().hasSelection():
        editor.removeLine()
        event.accept()
        return False
    return True


def surroundTextSquareBracket(editor, event):
    editor.surroundText("[]")
    event.accept()
    return False


def surroundTextCurlyBracket(editor, event):
    editor.surroundText("{}")
    event.accept()
    return False


def surroundTextBracket(editor, event):
    editor.surroundText("()")
    event.accept()
    return False


def surroundSingleQuote(editor, event):
    editor.surroundText("'")
    event.accept()
    return False


def surroundDoubleSingleQuote(editor, event):
    editor.surroundText("''")
    event.accept()
    return False


def surroundDoubleQuote(editor, event):
    editor.surroundText('""')
    event.accept()
    return False


def hotkeyCommandInsertNewLine(editor, event):
    editor.insertNewLine(includeText=True)
    event.accept()
    return False


def hotkeyCommandToNewLine(editor, event):
    editor.insertNewLine()
    event.accept()
    return False


def hotkeyCommandCommentLine(editor, event):
    editor.blockComment()
    event.accept()
    return False


def hotkeyCommandDedent(editor, event):

    editor.dedent()
    event.accept()
    return False


def hotkeyCommandIndent(editor, event):
    print("indent")
    editor.indent()
    event.accept()
    return False


def hotkeyCommandExecuteSelection(editor, event):
    editor.executed.emit(editor.textCursor().selectedText())
    return False


def hotkeyCommandExecuteAll(editor, event):
    editor.executed.emit(editor.toPlainText().strip())
    return False
