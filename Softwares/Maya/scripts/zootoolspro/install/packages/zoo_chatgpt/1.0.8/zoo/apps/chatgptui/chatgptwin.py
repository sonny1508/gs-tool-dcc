import os
import webbrowser

import openai, re

from zoo.core.util import zlogging
from zoo.core.plugin import pluginmanager
from zoo.libs import iconlib
from zoo.libs.pyqt.extended import treeviewplus
from zoo.libs.pyqt.extended.sourcecodeeditor import pythoneditor
from zoo.libs.pyqt.models import datasources, treemodel, constants, modelutils
from zoo.libs.pyqt.widgets import elements
from zoo.libs.utils import output
from zoo.libs.pyqt import utils, uiconstants
from zoo.apps.chatgptui import constants as gptconstants, utils as gptutils
from zoo.apps.chatgptui import basecontroller
from zoovendor.Qt import QtWidgets, QtCore, QtGui

logger = zlogging.getLogger(__name__)


class ChatGPTWindow(elements.ZooWindow):
    helpUrl = gptconstants.HELP_URL
    windowSettingsPath = "zoo/chatgpt"
    _GPT_ENV_NAME = "ZOO_CHATGPT_CONTROLLER"

    def __init__(
        self,
        name="chatgpt",
        title="ChatGPT",
        parent=None,
        resizable=True,
        width=800,
        height=900,
        modal=False,
        alwaysShowAllTitle=False,
        minButton=False,
        maxButton=False,
        onTop=False,
        saveWindowPref=True,
        titleBar=None,
        overlay=True,
        minimizeEnabled=True,
        initPos=None,
    ):
        super(ChatGPTWindow, self).__init__(
            name,
            title,
            parent,
            resizable,
            width,
            height,
            modal,
            alwaysShowAllTitle,
            minButton,
            maxButton,
            onTop,
            saveWindowPref,
            titleBar,
            overlay,
            minimizeEnabled,
            initPos,
        )
        self.controllerManager = pluginmanager.PluginManager(
            interface=[basecontroller.Controller],
            variableName="id",
            name="ChatGPTControllers",
        )
        self.controllerManager.registerByEnv(self._GPT_ENV_NAME)
        plugins = list(self.controllerManager.plugins)
        if len(plugins) == 0:
            self.controller = basecontroller.Controller(self)
        else:
            self.controller = self.controllerManager.getPlugin(
                list(self.controllerManager.plugins.keys())[0]
            )(self)
        self.initui()
        self.controller.messageReceived.connect(self.onRecievedMessage)
        self.controller.messageErrored.connect(self.displayError)
        self.controller.gptModelListReceived.connect(self.onModelListReceived)
        self.messageInput.executed.connect(self.sendMessage)
        self.sendBtn.clicked.connect(self.sendMessage)
        self.clearBtn.clicked.connect(self.clearMessages)

        gptutils.setAPIkey(os.getenv(gptconstants.OPENAI_ENV, openai.api_key))
        self.controller.updateModels()

    def initui(self):
        layout = elements.vBoxLayout()
        self.setMainLayout(layout)

        splitter = QtWidgets.QSplitter(self.parent())
        splitter.setOrientation(QtCore.Qt.Vertical)
        splitter.setHandleWidth(utils.dpiScale(3))
        titlebar = self.titleBar
        self.modelOptions = elements.ComboBoxRegular(
            label="Model:", items=[], parent=titlebar, sortAlphabetically=True
        )
        self.modelOptions.box.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)
        titlebar.contentsLayout.addWidget(self.modelOptions)
        titlebar.contentsLayout.setAlignment(self.modelOptions, QtCore.Qt.AlignCenter)
        self.messageHistory = treeviewplus.TreeViewPlus(parent=self, sorting=False)
        self.messageHistory.setToolBarVisible(False)
        self.messageHistory.treeView.header().setVisible(False)
        self.messageHistory.treeView.setVerticalScrollMode(
            QtWidgets.QAbstractItemView.ScrollPerPixel
        )
        self.messageHistory.setAlternatingColorEnabled(True)
        self.messageHistory.treeView.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarAsNeeded
        )
        self.messageHistory.treeView.setIndentation(0) # removes the rendering of the branches.

        self.messageModel = MessageHistoryModel(
            self.controller, MessageDataSource("", ""), parent=self.messageHistory
        )
        self.messageHistory.treeView.setItemDelegate(
            _Delegate(self.messageHistory.treeView)
        )
        self.messageHistory.setModel(self.messageModel)

        self.messageInput = pythoneditor.Editor("", parent=self)
        toolTip = "Send your current message to the chat thread."
        self.sendBtn = elements.regularButton(
            text="Send", icon="send", maxHeight=25, toolTip=toolTip, parent=self
        )

        toolTip = (
            "Press to start a new chat thread. \n"
            "The current chat thread will be deleted."
        )
        self.clearBtn = elements.regularButton(
            text="Clear", icon="trash", maxHeight=25, toolTip=toolTip, parent=self
        )
        toolTip = "Left click for various links to OpenAI, your quota, pricing and help"
        self.openAIBtn = elements.styledButton(
            "",
            icon="chatGPTSimple",
            toolTip=toolTip,
            minWidth=uiconstants.BTN_W_ICN_MED,
            parent=self,
        )
        splitter.addWidget(self.messageHistory)
        splitter.addWidget(self.messageInput)
        layout.addWidget(splitter)

        buttonLayout = elements.hBoxLayout(
            margins=(uiconstants.SREG, 0, uiconstants.SREG, uiconstants.SREG),
            spacing=uiconstants.SPACING,
        )
        buttonLayout.addWidget(self.sendBtn, 10)
        buttonLayout.addWidget(self.clearBtn, 10)
        buttonLayout.addWidget(self.openAIBtn, 1)
        layout.addLayout(buttonLayout)
        # setup the spliter so that the user input widget is 20% of the height
        splitter.setSizes([self.height() * 0.8, self.height() * 0.2])
        self.messageInput.textEdit.setFocus()
        # remove input hotkeys
        self.messageInput.textEdit.removeHotKeyByName(name="surroundTextSquareBracket")
        self.messageInput.textEdit.removeHotKeyByName(name="surroundTextCurlyBracket")
        self.messageInput.textEdit.removeHotKeyByName(name="surroundTextBracket")
        self.messageInput.textEdit.removeHotKeyByName(name="surroundSingleQuote")
        self.messageInput.textEdit.removeHotKeyByName(name="surroundDoubleSingleQuote")
        self.messageInput.textEdit.removeHotKeyByName(name="surroundDoubleQuote")
        self.messageInput.textEdit.removeHotKeyByName(name="commentLine")

        # Right Click OpenAI Menu ------------
        self.openAIBtn.addAction(
            "OpenAI - My Usage Quota",
            mouseMenu=QtCore.Qt.LeftButton,
            icon=iconlib.icon("webpage"),
            connect=self.webOpenQuota,
        )
        self.openAIBtn.addAction(
            "OpenAI - Pricing",
            mouseMenu=QtCore.Qt.LeftButton,
            icon=iconlib.icon("webpage"),
            connect=self.webOpenPricing,
        )
        self.openAIBtn.addAction(
            "OpenAI - API Key",
            mouseMenu=QtCore.Qt.LeftButton,
            icon=iconlib.icon("webpage"),
            connect=self.webOpenApiKey,
        )
        self.openAIBtn.addAction(
            "Create 3d Characters.com - Tool Help",
            mouseMenu=QtCore.Qt.LeftButton,
            icon=iconlib.icon("webpage"),
            connect=self.webHelp,
        )

    def webOpenQuota(self):
        webbrowser.open(gptconstants.OPENAI_USAGE_URL)

    def webOpenApiKey(self):
        webbrowser.open(gptconstants.OPEN_API_URL)

    def webOpenPricing(self):
        webbrowser.open(gptconstants.OPENAI_PRICING_URL)

    def webHelp(self):
        webbrowser.open(gptconstants.HELP_URL)

    def onModelListReceived(self, items):
        self.modelOptions.clear()
        self.modelOptions.blockSignals(True)
        self.modelOptions.addItems(items, sortAlphabetically=True)
        self.modelOptions.setToText(self.controller.chatSession.model)
        self.modelOptions.blockSignals(False)

    def close(self):
        self.controller.onClose()
        super(ChatGPTWindow, self).close()

    def onRecievedMessage(self, responseText):
        rowCount = self.messageModel.rowCount(QtCore.QModelIndex()) - 1
        currentMessageIndex = self.messageModel.index(rowCount, 0)
        self.messageModel.setData(
            currentMessageIndex, responseText, role=constants.userRoleCount + 1
        )
        self.messageHistory.treeView.resizeColumnToContents(0)
        self.messageHistory.treeView.scrollToBottom()

    def sendMessage(self):
        message = self.messageInput.text()
        if not message:
            return
        rowCount = self.messageModel.rowCount(QtCore.QModelIndex())
        self.messageModel.insertRow(rowCount, value="", userName="You")
        self.messageModel.setData(
            self.messageModel.index(rowCount, 0),
            value=message,
            role=constants.userRoleCount + 1,
        )
        rowCount = self.messageModel.rowCount(QtCore.QModelIndex())
        self.messageModel.insertRow(rowCount, value="", userName="ChatGPT")
        self.controller.send(message)
        self.messageInput.clear()

    def clearMessages(self):
        self.messageModel.root.setUserObjects([])
        self.messageModel.reload()
        self.messageHistory.refresh()
        self.controller.clearMessages()

    def displayError(self, error):
        elements.MessageBox.showCritical(
            parent=self, title=error["type"], buttonB=None, message=error["message"]
        )

    def displayApiKeyInputDialog(self):
        m = ApiKeyDialog(self.controller)
        m.show()
        while m.msgClosed is False:
            utils.processUIEvents()
        inputText = m.result
        if not inputText:
            return False
        if not gptutils.validateKey(inputText):
            output.displayWarning("Invalid API Key")
            return False
        gptutils.setAPIkey(inputText)
        self.controller.updateModels()
        return True


class ApiKeyDialog(elements.ZooWindowThin):

    def __init__(
        self,
        name="KeyRequired",
        title="`Open AI` Key Required",
        parent=None,
        resizable=True,
        width=340,
        height=80,
        modal=False,
        alwaysShowAllTitle=False,
        minButton=False,
        maxButton=False,
        onTop=False,
        saveWindowPref=False,
        titleBar=None,
        overlay=True,
        minimizeEnabled=True,
        initPos=None,
    ):
        super(ApiKeyDialog, self).__init__(
            name,
            title,
            parent,
            resizable,
            width,
            height,
            modal,
            alwaysShowAllTitle,
            minButton,
            maxButton,
            onTop,
            saveWindowPref,
            titleBar,
            overlay,
            minimizeEnabled,
            initPos,
        )
        self.result = ""
        self.msgClosed = False
        iconSize = 32
        image = QtWidgets.QToolButton(parent=self)
        image.setIcon(
            iconlib.iconColorizedLayered("help", iconSize, colors=(0, 192, 32))
        )
        image.setIconSize(utils.sizeByDpi(QtCore.QSize(iconSize, iconSize)))
        image.setFixedSize(utils.sizeByDpi(QtCore.QSize(iconSize, iconSize)))

        titleLabel = elements.Label(
            "Please Enter Your `Open AI` API Key", bold=True, parent=self
        )
        textLabel = elements.Label(
            gptconstants.API_KEY_DIALOG_MESSAGE, bold=False, parent=self
        )
        okBtn = elements.styledButton("OK", "checkMark", parent=self)
        cancelBtn = elements.styledButton("Cancel", "xCircleMark", parent=self)
        tooltip = "Get your free API key from OpenAI.com \n" "{}".format(
            gptconstants.OPEN_API_URL
        )
        apiBtn = elements.styledButton(
            "Get Free Api Key", "key", toolTip=tooltip, parent=self
        )
        helpBtn = elements.styledButton("Help", "help", toolTip=tooltip, parent=self)
        self.inputEdit = elements.StringEdit(
            parent=self,
            editPlaceholder="Enter Code: sk-MXRT3B1LD3MJWTEtF3B1LD3MJWTYFsDFGScs",
        )

        # Layout --------------------------------
        mainLayout = elements.vBoxLayout(
            spacing=0,
            margins=(
                uiconstants.REGPAD,
                uiconstants.REGPAD,
                uiconstants.REGPAD,
                uiconstants.REGPAD,
            ),
        )

        iconLayout = elements.vBoxLayout(spacing=uiconstants.SREG, margins=(0, 0, 0, 0))
        iconLayout.addWidget(image)

        messageLayout = elements.vBoxLayout(
            spacing=uiconstants.SLRG, margins=(0, 0, 0, 0)
        )
        messageLayout.addWidget(titleLabel)
        messageLayout.addWidget(textLabel)

        topLayout = elements.hBoxLayout(
            spacing=uiconstants.SVLRG2,
            margins=(
                uiconstants.WINSIDEPAD,
                uiconstants.BOTPAD,
                uiconstants.WINSIDEPAD,
                uiconstants.TOPPAD,
            ),
        )
        topLayout.addLayout(iconLayout, 1)
        topLayout.addLayout(messageLayout, 2)

        inputLayout = elements.hBoxLayout(
            spacing=uiconstants.SREG,
            margins=(
                uiconstants.WINSIDEPAD,
                uiconstants.TOPPAD,
                uiconstants.WINSIDEPAD,
                uiconstants.TOPPAD,
            ),
        )
        inputLayout.addWidget(self.inputEdit)

        buttonLayout = elements.hBoxLayout(
            spacing=uiconstants.SREG, margins=(0, uiconstants.TOPPAD, 0, 0)
        )
        buttonLayout.addWidget(okBtn)
        buttonLayout.addWidget(cancelBtn)
        buttonLayout.addWidget(apiBtn)
        buttonLayout.addWidget(helpBtn)

        # Add To Main Layout ---------------------
        mainLayout.addLayout(topLayout)
        mainLayout.addLayout(inputLayout)
        mainLayout.addLayout(buttonLayout)
        self.setMainLayout(mainLayout)

        # Connections -------------------------------
        okBtn.clicked.connect(self.okPressed)
        cancelBtn.clicked.connect(self.cancelPressed)
        apiBtn.clicked.connect(self._onApiKey)
        helpBtn.clicked.connect(self._help)

    def _onApiKey(self):
        output.displayInfo(
            "Opening OpenAI website: {}".format(gptconstants.OPEN_API_URL)
        )
        webbrowser.open(gptconstants.OPEN_API_URL)

    def _help(self):
        output.displayInfo("Opening help webpage: {}".format(gptconstants.HELP_URL))
        webbrowser.open(gptconstants.HELP_URL)

    def cancelPressed(self):
        self.result = ""
        self.msgClosed = True
        self.close()

    def okPressed(self):
        """Open the dialog"""
        key = self.inputEdit.text()
        if not key:
            output.displayWarning("No API Key entered")
            return

        if not gptutils.validateKey(key):
            output.displayWarning("Provide API Key isn't Authorized")
            return
        self.result = key
        self.msgClosed = True

        self.close()


class CodeBlockWidget(QtWidgets.QFrame):
    _iconCopyCache = None
    _iconRunCache = None

    def __init__(self, model, language, parent=None):
        super(CodeBlockWidget, self).__init__(parent)
        self._layout = elements.vBoxLayout(self, spacing=0)
        self.model = model
        self.headerLayout = elements.hBoxLayout(
            margins=(uiconstants.SSML, uiconstants.SSML, 0, uiconstants.SSML),
            spacing=uiconstants.SPACING,
        )
        self.titleLabel = elements.Label(language, self)
        if CodeBlockWidget._iconCopyCache is None:
            CodeBlockWidget._iconCopyCache = iconlib.icon("copy")
        if CodeBlockWidget._iconRunCache is None:
            CodeBlockWidget._iconRunCache = iconlib.icon("play")
        self.copyButton = elements.styledButton(
            style=uiconstants.BTN_TRANSPARENT_BG,
            icon="copy",
            parent=self,
            toolTip="Copies the Code block to the clipboard",
            maxWidth=24,
        )
        self.runButton = elements.styledButton(
            style=uiconstants.BTN_TRANSPARENT_BG,
            icon="play",
            parent=self,
            toolTip="Executes either the selected Code or the entire code block",
            maxWidth=24,
        )

        self.headerLayout.addWidget(self.titleLabel)
        self.headerLayout.addItem(
            elements.Spacer(
                0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum
            )
        )
        self.headerLayout.addWidget(self.runButton)
        self.headerLayout.addWidget(self.copyButton)

        self.code = pythoneditor.Editor("python", parent=self)
        self.code.textEdit.setWordWrapMode(QtGui.QTextOption.WordWrap)
        self.code.textEdit.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.code.textEdit.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.code.textEdit.setReadOnly(True)
        self._layout.addLayout(self.headerLayout)
        self._layout.addWidget(self.code)
        self.setFixedHeight(utils.dpiScale(60))
        self.copyButton.clicked.connect(self.onCopy)
        self.runButton.clicked.connect(self.onRun)

        self.code.textEdit.textChanged.connect(self.onTextChanged)

        margins = self.code.documentMargins()
        margin = utils.dpiScale(10)
        margins[0] = margin
        margins[-1] = margin
        self.code.setDocumentMargins(*margins)
        self._executionLocals = {
            "__name__": "__main__",
            "__doc__": None,
            "__package__": None,
        }

    def onCopy(self):
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(self.code.text())

    def onRun(self):
        text = self.code.textEdit.textCursor().selectedText()

        if not text:
            text = self.code.textEdit.toPlainText().strip()
        if not text:
            return
        modelutils.dataModelFromProxyModel(self.model).executeCode(text)

    def textCursor(self):
        return self.code.textEdit.textCursor()

    def onTextChanged(self):
        width = self.size().width()
        doc = self.code.textEdit.document()
        doc.adjustSize()
        doc.setTextWidth(width)
        self.setFixedHeight(self.code.textEdit.heightForWidth(width))


class ChatTextEdit(elements.TextEdit):

    def __init__(
        self,
        text="",
        parent=None,
        placeholderText="",
        toolTip="",
        editWidth=None,
        minimumHeight=None,
        maximumHeight=None,
        fixedWidth=None,
        fixedHeight=None,
    ):
        super(ChatTextEdit, self).__init__(
            text,
            parent,
            placeholderText,
            toolTip,
            editWidth,
            minimumHeight,
            maximumHeight,
            fixedWidth,
            fixedHeight,
        )
        self.setAcceptRichText(True)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.viewport().setAutoFillBackground(False)
        self.setReadOnly(True)
        self.setFixedHeight(30)
        self.setStyleSheet("background-color: transparent;")
        self.textChanged.connect(self.onTextChanged)

        margins = self.documentMargins()
        margin = utils.dpiScale(10)
        margins[0] = margin
        margins[-1] = margin
        self.setDocumentMargins(*margins)

    def onTextChanged(self):
        width = self.size().width()
        doc = self.document()
        doc.adjustSize()
        doc.setTextWidth(width)
        self.setFixedHeight(self.heightForWidth(width))


class DelegateWidget(QtWidgets.QFrame):
    def __init__(self, model, parent=None):
        super(DelegateWidget, self).__init__(parent)
        self.userLabel = elements.Label(
            "Chat GPT", bold=True, enableMenu=False, parent=self
        )
        self._layout = elements.vBoxLayout(self, margins=(0, 10, 0, 0), spacing=0)
        self._layout.addWidget(self.userLabel)
        self.model = model
        self.widgets = []

        self.currentWidget = None  # type: QtWidgets.QTextEdit or CodeBlockWidget
        self.lines = ""
        self.foundBlock = False

    def setUserName(self, name):
        self.userLabel.setText(name)

    def processIncomingText(self, text):
        # text is streamed in so we detect the start/end of a code
        # if it's the start of the code block we create a code widget
        # if it's the end we create a new label widget
        # any text while in a code block will be added to the code widget
        self.lines += text
        if not self.foundBlock:
            for match in re.finditer(r"((```\w+\n)|(```\n))", self.lines):
                cursor = self.currentWidget.textCursor()
                cursor.select(QtGui.QTextCursor.LineUnderCursor)
                cursor.removeSelectedText()
                cursor.deleteChar()
                self.lines = "```python\n"
                self.foundBlock = True
                self.currentWidget = CodeBlockWidget(self.model, "Python", self)
                self.widgets.append(self.currentWidget)
                self._layout.addWidget(self.currentWidget)
                return
            # standard text chat
            if self.currentWidget is None:
                self.currentWidget = ChatTextEdit(parent=self)
                self.widgets.append(self.currentWidget)
                self._layout.addWidget(self.currentWidget)
            cursor = self.currentWidget.textCursor()
            cursor.movePosition(QtGui.QTextCursor.End)
            cursor.insertText(text)

        else:
            # if we're at the end of the code block
            for match in re.finditer(r"```(?:\w+\n)?([\s\S]+?)```", self.lines):
                cursor = self.currentWidget.textCursor()
                cursor.select(QtGui.QTextCursor.LineUnderCursor)
                cursor.removeSelectedText()
                cursor.deleteChar()
                self.lines = ""
                self.foundBlock = False
                self.currentWidget = None
                return
            # otherwise just add the text to the code block
            cursor = self.currentWidget.textCursor()
            cursor.movePosition(QtGui.QTextCursor.End)
            cursor.insertText(text)


class _Delegate(QtWidgets.QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        widget = DelegateWidget(index.model(), parent)
        widget.index = QtCore.QPersistentModelIndex(index)
        return widget

    def eventFilter(self, editor, event):
        if event.type() == QtCore.QEvent.LayoutRequest:
            persistent = editor.index
            index = persistent.model().index(
                persistent.row(), persistent.column(), persistent.parent()
            )
            self.sizeHintChanged.emit(index)
        return super().eventFilter(editor, event)

    def paint(self, painter, option, index):
        self.initStyleOption(option, index)
        viewer = self.parent()
        if not viewer.isPersistentEditorOpen(index):
            viewer.openPersistentEditor(index)

    def setEditorData(self, editor, index):
        if not index.isValid():
            return

        editor.processIncomingText(index.data(constants.userRoleCount + 1))
        editor.setUserName(index.data(constants.userRoleCount + 2))

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)


class MessageDataSource(datasources.BaseDataSource):

    def __init__(self, text, userName, headerText=None, model=None, parent=None):
        super(MessageDataSource, self).__init__(headerText, model, parent)
        self._text = text
        self.lastTextStream = ""
        self.userName = userName

    def isSelectable(self, index):
        return False

    def setData(self, index, value):
        self.userObjects()[index] = value

    def toolTip(self, index):
        return ""

    def data(self, index):
        return self._text

    def insertRowDataSource(self, index, value=None, userName=None):
        self.insertChild(index + 1, MessageDataSource(value, userName, parent=self))

    def delegate(self, parent):
        return _Delegate(parent)

    def setDataByCustomRole(self, index, data, role):

        if role == constants.userRoleCount + 1:
            self.lastTextStream = data
            return True
        elif role == constants.userRoleCount + 2:
            self.userName = data
            return True
        return False

    def dataByRole(self, index, role):
        if role == constants.userRoleCount + 1:
            return self.lastTextStream
        elif role == constants.userRoleCount + 2:
            return self.userName
        return ""

    def customRoles(self, index):
        return [
            constants.userRoleCount + 1,
            constants.userRoleCount + 2,
        ]  # +1 is for add text


class MessageHistoryModel(treemodel.TreeModel):

    def __init__(self, controller, root, parent=None):
        super(MessageHistoryModel, self).__init__(root, parent)
        self.controller = controller

    def executeCode(self, text):
        self.controller.executeCode(text)
