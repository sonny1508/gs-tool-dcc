"""
:todo: paste text while maintain scope
"""

from zoovendor.Qt import QtWidgets, QtGui, QtCore
from zoo.libs.pyqt.syntaxhighlighter import highlighter
from zoo.libs.pyqt.widgets import elements
from zoo.libs.pyqt.extended import tabwidget
from zoo.libs.pyqt.extended.sourcecodeeditor import numberbar, inputtextwidget


class Editor(QtWidgets.QWidget):
    outputText = QtCore.Signal(str)
    executed = QtCore.Signal(str)

    def __init__(self, language, stdoutProxy=None, parent=None):
        super(Editor, self).__init__(parent=parent)
        self.pythonHighlighter = None
        self.textEdit = inputtextwidget.TextEditor(parent=self)
        self.numberBar = numberbar.NumberBar(self.textEdit)
        self.stdProxy = stdoutProxy
        self.defaultTheme = "atomonedark"

        hbox = elements.hBoxLayout(parent=self, spacing=0, margins=(0, 0, 0, 0))
        hbox.addWidget(self.numberBar)
        hbox.addWidget(self.textEdit)
        if language:
            self.setLanguage(language)
        self.textEdit.blockCountChanged.connect(self.numberBar.adjustWidth)
        self.textEdit.updateRequest.connect(self.numberBar.adjustWidth)
        self.textEdit.executed.connect(self.executed.emit)

    def setLanguage(self, language, theme=None):
        if self.pythonHighlighter is not None:
            self.pythonHighlighter.deleteLater()
        if language:
            # todo: don't hard code the syntax theme
            self.pythonHighlighter = highlighter.highlighterForLanguage(self.textEdit.document(),
                                                                        language, theme or self.defaultTheme)

    def text(self):
        return self.textEdit.toPlainText()

    def setText(self, text):
        self.textEdit.setPlainText(text)

    def clear(self):
        self.textEdit.clear()

    def isModified(self):
        return self.textEdit.document().isModified()

    def setModified(self, modified):
        self.textEdit.document().setModified(modified)

    def setLineWrapMode(self, mode):
        self.textEdit.setLineWrapMode(mode)

    def documentMargins(self):
        format = self.textEdit.document().rootFrame().frameFormat()
        return [format.topMargin(), format.rightMargin(), format.bottomMargin(), format.leftMargin()]

    def setDocumentMargins(self, top, right, bottom, left):
        format = self.textEdit.document().rootFrame().frameFormat()
        format.setTopMargin(top)
        format.setRightMargin(right)
        format.setBottomMargin(bottom)
        format.setLeftMargin(left)
        self.textEdit.document().rootFrame().setFrameFormat(format)


class TabbedEditor(tabwidget.TabWidget):
    outputText = QtCore.Signal(str)
    # executed when the code was executed via hotkey or function
    executed = QtCore.Signal(str)
    # signal which is emitted after the QTab has been created.
    newTabAdded = QtCore.Signal(object, str)

    def __init__(self, name, parent=None):
        super(TabbedEditor, self).__init__(name, parent=parent)
        self.newTabRequested.connect(self.addNewEditor)

    def addNewEditor(self, widget=None, name=None, language=None):
        name = name or "New tab"
        edit = Editor(language, parent=self)
        self.addTab(edit, name)
        edit.executed.connect(self.executed.emit)
        edit.textEdit.moveCursor(QtGui.QTextCursor.Start)
        self.setCurrentIndex(self.count() - 1)
        self.newTabAdded.emit(edit, name)
        return edit
