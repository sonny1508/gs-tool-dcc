import uuid

from zoo.libs import iconlib
from zoo.core.util import strutils
from zoovendor.Qt import QtWidgets, QtCore
from zoo.libs.pyqt import utils
from zoo.libs.pyqt.widgets import layouts, buttons
from zoo.libs.pyqt.widgets.frameless import window


def FileDialog_directory(windowName="", parent=None, defaultPath=""):
    """simple function for QFileDialog.getExistingDirectory, a window popup that searches for a directory

    Browses for a directory with a fileDialog window and returns the selected directory

    :param windowName: The name of the fileDialog window
    :type windowName: str
    :param parent: The parent widget
    :type parent: :class:`QtWidgets.QWidget`
    :param defaultPath: The default directory path, where to open the fileDialog window
    :type defaultPath: str
    :return directoryPath: The selected full directory path
    :rtype directoryPath: str
    """
    directoryPath = str(QtWidgets.QFileDialog.getExistingDirectory(parent, windowName, defaultPath))
    if not directoryPath:
        return
    return directoryPath


def generateName(name):
    """ Generate name

    :param name:
    :return:
    """
    return "{}_{}_".format(name, str(uuid.uuid4())[:4])


class MessageBoxBase(window.ZooWindowThin):
    # Warning = QtWidgets.QMessageBox.Warning
    # Question = QtWidgets.QMessageBox.Question
    # Info = QtWidgets.QMessageBox.Information
    # Critical = QtWidgets.QMessageBox.Critical
    # NoIcon = QtWidgets.QMessageBox.NoIcon

    Warning = "Warning"
    Question = "Question"
    Info = "Info"
    Critical = "Critical"
    NoIcon = "NoIcon"
    _questionIcon = "help"
    _criticalIcon = "xCircleMark2"
    _warningIcon = "warning"
    _infoIcon = "information"
    okIcon = "checkMark"
    cancelIcon = "xCircleMark"

    def __init__(self, parent, title="", message="", icon="Question",
                 buttonA="OK", buttonB=None, buttonC=None, buttonIconA=okIcon, buttonIconB=cancelIcon,
                 buttonIconC=None, default=0, onTop=True,
                 keyPresses=(QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return, QtCore.Qt.Key_Space)):
        """ Message box

        :param parent:
        :type parent: :class:`zoovendor.Qt.QtWidgets.QWidget`
        :param title:
        :type title:
        :param message:
        :type message:
        :param buttonA:
        :type buttonA:
        :param buttonB:
        :type buttonB:
        :param buttonC:
        :type buttonC:
        :param icon:
        :type icon:
        """
        self._args = locals()
        self.default = default
        if parent:
            parent = parent.window()

        icon = generateName(icon) if icon else generateName("MessageBox")
        super(MessageBoxBase, self).__init__(parent=parent, title=title, name=icon, resizable=False,
                                             width=100,
                                             height=100, modal=False, minimizeEnabled=False, onTop=onTop)
        self.result = None  #
        self.msgClosed = False
        self.buttons = []  # type: list[QtWidgets.QPushButton]

        self._initMessageBox()

    def _initMessageBox(self):
        """ Init message box

        :return:
        """
        self.setMaxButtonVisible(False)
        self.setMinButtonVisible(False)
        self.titleBar.setTitleAlign(QtCore.Qt.AlignCenter)

        # Label
        self.label = QtWidgets.QLabel(self._args['message'], parent=self)
        width = min(self.label.fontMetrics().boundingRect(self.label.text()).width() + 20, 400)
        self.label.setFixedWidth(width)
        self.label.setWordWrap(True)
        height = min(self.calcLabelHeight(label=self.label, text=self.label.text()), 800)
        self.label.setFixedHeight(height)

        self.imageLayout = layouts.hBoxLayout(margins=(15, 15, 15, 15), spacing=15)
        # MessageBox Image
        image = QtWidgets.QToolButton(parent=self)
        s = 32
        icon = self._args['icon'] or "NoIcon"

        if icon == "Warning":
            image.setIcon(iconlib.iconColorizedLayered(self._warningIcon, s, colors=(220, 210, 0)))
        elif icon == "Question":
            image.setIcon(iconlib.iconColorizedLayered(self._questionIcon, s, colors=(0, 192, 32)))
        elif icon == "Info":
            image.setIcon(iconlib.iconColorizedLayered(self._infoIcon, s, colors=(220, 220, 220)))
        elif icon == "Critical":
            image.setIcon(iconlib.iconColorizedLayered(self._criticalIcon, s, colors=(200, 90, 90)))
        elif icon == "NoIcon":
            image.hide()

        if icon != "NoIcon":
            image.setIconSize(utils.sizeByDpi(QtCore.QSize(s, s)))
            image.setFixedSize(utils.sizeByDpi(QtCore.QSize(s, s)))

        self.label.setAlignment(QtCore.Qt.AlignTop)
        self.messageLayout = layouts.vBoxLayout()

        self.imageLayout.addWidget(image)
        self.imageLayout.addLayout(self.messageLayout)
        self.messageLayout.addWidget(self.label)

        # Buttons
        self.buttonLayout = layouts.hBoxLayout(margins=(10, 0, 10, 10))
        self.buttonLayout.addStretch(1)

        msgButtons = [self._args['buttonA'], self._args['buttonB'], self._args['buttonC']]
        buttonIcons = [self._args['buttonIconA'], self._args['buttonIconB'], self._args['buttonIconC']]
        res = ['A', 'B', 'C']

        for i, b in enumerate(msgButtons):
            if b is not None:
                button = buttons.styledButton(parent=self.parentWidget(),
                                              text=" " + b,
                                              icon=buttonIcons[i])  # type:  buttons.ExtendedButton

                button.setMinimumWidth(80)
                button.setMinimumHeight(24)
                utils.setHSizePolicy(button, QtWidgets.QSizePolicy.MinimumExpanding)
                self.buttonLayout.addWidget(button)
                button.leftClicked.connect(lambda result=res[i]: self.close(result))
                self.buttons.append(button)

        self.buttonLayout.addStretch(1)
        layout = self.mainLayout()
        layout.addLayout(self.imageLayout)
        layout.addLayout(self.buttonLayout)

    def keyPressEvent(self, event):
        """ keyPress event

        :param event:
        :return:
        """
        if self.default >= 0:
            # The keys to use to press the default button (eg "Ok")
            keys = self._args['keyPresses']  # eg: [QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return, QtCore.Qt.Key_Space]
            if any(map(lambda y: event.key() == y, keys)):  # any of the keys pressed
                self.buttons[self.default].leftClicked.emit()

    @classmethod
    def calcLabelHeight(cls, text, label):
        """

        :param text:
        :type text:
        :param label:
        :type label: QtWidgets.QLabel
        :return:
        :rtype:
        """
        # If this is too slow should map out text
        fm = label.fontMetrics()
        width = label.size().width()
        height = fm.height()
        lines = 1
        walkWidth = 0

        for c in text:
            w = cls.horizontalAdvance(fm, c)
            walkWidth += w + 1.1  # not sure where the 1.1 comes from, will have to find out
            if walkWidth > width:
                walkWidth = w
                lines += 1

        newLines = strutils.newLines(text)
        lines += newLines

        return height * lines

    @classmethod
    def horizontalAdvance(cls, fm, c):
        """ Horizontal advance doesn't exist in 2018. eg older versions of PySide2

        :param fm:
        :param c:
        :return:
        """

        if hasattr(fm, "horizontalAdvance"):
            return fm.horizontalAdvance(c)
        else:
            return fm.width(c)

    def close(self, result=None):
        self.msgClosed = True
        self.result = result
        super(MessageBoxBase, self).close()


class MessageBox(MessageBoxBase):

    @classmethod
    def showQuestion(cls, parent=None, title="", message="", buttonA="Continue", buttonB="Cancel", buttonC=None,
                     buttonIconA=MessageBoxBase.okIcon, buttonIconB=MessageBoxBase.cancelIcon, buttonIconC=None,
                     icon="Question", default=0):
        m = MessageBoxBase(parent=parent, title=title, message=message,
                           buttonA=buttonA, buttonB=buttonB, buttonC=buttonC,
                           buttonIconA=buttonIconA, buttonIconB=buttonIconB, buttonIconC=buttonIconC,
                           icon=icon, default=default)
        m.show()
        while m.msgClosed is False:
            utils.processUIEvents()

        return m.result

    @classmethod
    def showWarning(cls, parent=None, title="", message="", buttonA="OK", buttonB="Cancel", buttonC=None,
                    icon="Warning", default=0):
        m = MessageBoxBase(parent=parent, title=title, message=message,
                           buttonA=buttonA, buttonB=buttonB, buttonC=buttonC,
                           icon=icon, default=default)
        m.show()
        while m.msgClosed is False:
            utils.processUIEvents()

        return m.result

    @classmethod
    def showCritical(cls, parent=None, title="", message="", buttonA="OK", buttonB="Cancel", buttonC=None,
                     icon="Critical", default=0):
        m = MessageBoxBase(parent=parent, title=title, message=message,
                           buttonA=buttonA, buttonB=buttonB, buttonC=buttonC,
                           icon=icon, default=default)
        m.show()
        while m.msgClosed is False:
            utils.processUIEvents()

        return m.result

    @classmethod
    def showOK(cls, title="Confirm", parent=None, message="Proceed", icon="Question",
               default=0, buttonA="OK", buttonB="Cancel", buttonC=None):
        """Simple function for ok/cancel QMessageBox.question, a window popup that with ok/cancel buttons

        :param title: The name of the ok/cancel window
        :type title: str
        :param parent: The parent widget
        :type parent: Qt.widget
        :param message: The message to ask the user
        :type message: str
        :return okPressed: True if the Ok button was pressed, False if cancelled
        :rtype okPressed: bool
        """
        m = MessageBoxBase(parent=parent, title=title, message=message,
                           buttonA=buttonA, buttonB=buttonB, buttonC=buttonC, icon=icon, default=default)
        m.show()
        while m.msgClosed is False:
            utils.processUIEvents()

        return m.result == "A"

    @classmethod
    def showSave(cls, title="Confirm", parent=None, message="Proceed?",
                 showDiscard=True, default=0):
        """Simple function for save/don't save/cancel QMessageBox.question, a window popup with buttons

        Can have two or three buttons:

            showDiscard True: Save, Discard, Cancel
            showDiscard False: Save, Cancel

        :param title: The name of the ok/cancel window
        :type title: str
        :param parent: The parent widget
        :type parent: Qt.widget
        :param message: The message to ask the user
        :type message: str
        :return buttonClicked: "cancel", "save", or "discard"
        :rtype buttonClicked: str
        """
        discard = None
        if showDiscard:
            discard = "Discard"

        m = MessageBox(parent=parent, title=title, message=message,
                       buttonA="Save", buttonB=discard, buttonC="Cancel",
                       buttonIconB="trash",
                       buttonIconC=MessageBoxBase.cancelIcon,
                       icon="Question", default=default)
        m.show()
        while m.msgClosed is False:
            utils.processUIEvents()

        if m.result == "A":
            return "save"
        elif m.result == "B":
            return "discard"

        return "cancel"

    @classmethod
    def showMultiChoice(cls, title="Confirm", parent=None, message="Proceed?", choices=None,
                        showDiscard=False, default=0, buttonB="Discard", buttonC="Cancel"):
        """A message box with multiple choice. Also has ok, cancel buttons.

        MessageBox.showMultiChoice( title="Existing shader found",
                                    message="Shader with the name name \'{}\' found.".format(shader),
                                    choices=["Replace Shader","Assign Existing", "Create New Shader"], buttonB="Cancel")

        Can have the following return results:
            # (0, "Replace Shader")
            # (1, "Assign Existing")
            # (2, "Create New Shader")
            # (-1, "cancel")

        Can have two or three buttons:

            showDiscard True: Save, Discard, Cancel
            showDiscard False: Save, Cancel



        """
        choices = choices or []
        if not showDiscard:
            buttonB = None

        m = MultiChoiceDialog(parent=parent, title=title, message=message,
                              buttonA="Ok", buttonB=buttonB, buttonC=buttonC, icon="Question", default=default,
                              choices=choices)
        m.show()
        while m.msgClosed is False:
            utils.processUIEvents()

        if m.result == "A":
            return (m.choice(), choices[m.choice()])

        return (-1, "cancel")

    @classmethod
    def showCombo(cls, title="Confirm", parent=None, message="Proceed?", items=None, data=None, icon=None,
                  defaultItem=None,
                  showDiscard=False, default=0, buttonA="OK", buttonB="Discard", buttonC="Cancel",
                  buttonIconA=MessageBoxBase.okIcon, buttonIconB=MessageBoxBase.cancelIcon, buttonIconC=None):
        """A message box with multiple choice. Also has ok, cancel buttons.

        MessageBox.showCombo( title="Existing shader found",
                                    message="Shader with the name name \'{}\' found.".format(shader),
                                    items=["Replace Shader","Assign Existing", "Create New Shader"], buttonB="Cancel")

        Can have the following return results:
            # (0, "Replace Shader", <object>)
            # (1, "Assign Existing", <object>)
            # (2, "Create New Shader", <object>)
            # (-1, "cancel", <object>)

        Where object is an element from data

        Can have two or three buttons:

            showDiscard True: Save, Discard, Cancel
            showDiscard False: Save, Cancel



        """
        items = items or []
        if not showDiscard:
            buttonB = None

        m = ComboDialog(parent=parent, title=title, message=message,
                        buttonA=buttonA, buttonB=buttonB, buttonC=buttonC, icon=icon, defaultIndex=defaultItem,
                        default=default, items=items, data=data,
                        buttonIconA=buttonIconA, buttonIconB=buttonIconB, buttonIconC=buttonIconC)
        m.show()
        while m.msgClosed is False:
            utils.processUIEvents()

        if m.result == "A":
            return m.combo.currentIndex(), m.combo.currentText(), m.selectedData()

        return -1, "cancel", None

    @classmethod
    def showCustom(cls, customWidget, title="Confirm", parent=None, message="Proceed", icon="Question",
                   default=0, buttonA="OK", buttonB="Cancel", buttonC=None):
        """Simple function for ok/cancel QMessageBox.question, a window popup that with ok/cancel buttons

        :param title: The name of the ok/cancel window
        :type title: str
        :param parent: The parent widget
        :type parent: Qt.widget
        :param message: The message to ask the user
        :type message: str
        :return okPressed: True if the Ok button was pressed, False if cancelled
        :rtype okPressed: bool
        """
        m = CustomDialog(parent, customWidget, title=title, message=message,
                         buttonA=buttonA, buttonB=buttonB, buttonC=buttonC, icon=icon, default=default)
        m.show()
        while m.msgClosed is False:
            utils.processUIEvents()

        return m.result, customWidget

    @classmethod
    def inputDialog(cls, parent=None, title="Input", message="Input:", text="", buttonA="OK", buttonB="Cancel",
                    buttonC=None, buttonIconC=None,
                    icon=None):
        """ Show the input dialog

        :param parent:
        :param title:
        :param message:
        :param buttonA:
        :param buttonB:
        :param text:
        :param icon:
        :return: Returns None if cancelled.
        """

        m = InputDialog(parent=parent, title=title, message=message, buttonA=buttonA, buttonB=buttonB,
                        buttonC=buttonC, buttonIconC=buttonIconC,
                        icon=icon, text=text)
        m.show()
        while m.msgClosed is False:
            utils.processUIEvents()

        if m.result == "A":
            return m.inputText()

        return None


class InputDialog(MessageBoxBase):
    def __init__(self, parent, title="Input", message="Input:", buttonA="OK", buttonB="Cancel",
                 buttonC=None, buttonIconC=None,
                 width=280, icon=None,
                 text=""):
        """ Input dialog

        use the function:

        .. code-block:: python
            renameText = elements.MessageBox.inputDialog(title="Rename Model Asset",
                                                 text=currentImageNoExt, parent=None,
                                                 message=message)

        :param parent:
        :param title:
        :param message:
        :param buttonA:
        :param buttonB:
        :param width:
        :param icon:
        :param text:
        """
        self._inputWidth = utils.dpiScale(width)
        self._initialText = text
        super(InputDialog, self).__init__(parent=parent, title=title, message=message, buttonA=buttonA, buttonB=buttonB,
                                          buttonC=buttonC, buttonIconC=buttonIconC,
                                          icon=icon, keyPresses=(QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return))

    def _initMessageBox(self):
        """ Initialize the message box and ui

        :return:
        """
        super(InputDialog, self)._initMessageBox()
        self.inputEdit = QtWidgets.QLineEdit(parent=self)
        self.messageLayout.addSpacing(utils.dpiScale(5))
        self.messageLayout.addWidget(self.inputEdit)
        self.inputEdit.setMinimumWidth(self._inputWidth)
        self.inputEdit.setText(self._initialText)
        self.inputEdit.selectAll()

    def inputText(self):
        """ Get the input text

        :return:
        """
        return self.inputEdit.text()


class ComboDialog(MessageBoxBase):
    def __init__(self, parent, title="", message="", icon="Question",
                 buttonA="OK", buttonB="Cancel", buttonC=None,
                 default=0, onTop=True, items=None, data=None, defaultIndex=None,
                 buttonIconA=MessageBoxBase.okIcon, buttonIconB=MessageBoxBase.cancelIcon, buttonIconC=None):
        self.items = items
        self.defaultIndex = defaultIndex
        self.data = data
        super(ComboDialog, self).__init__(parent=parent, title=title, message=message, icon=icon, buttonA=buttonA,
                                          buttonB=buttonB, buttonC=buttonC, default=default, onTop=onTop,
                                          buttonIconA=buttonIconA, buttonIconB=buttonIconB, buttonIconC=buttonIconC)

    def _initMessageBox(self):
        super(ComboDialog, self)._initMessageBox()
        self.messageLayout.addSpacing(utils.dpiScale(5))
        self._buttonGroup = QtWidgets.QButtonGroup()
        self.combo = QtWidgets.QComboBox()
        self.combo.addItems(self.items)
        if self.defaultIndex:
            self.combo.setCurrentIndex(self.defaultIndex)

        self.messageLayout.addWidget(self.combo)

    def selectedItem(self):
        """ Get the choice

        :return:
        """
        return self.combo.currentText()

    def selectedData(self):
        if self.data:
            return self.data[self.combo.currentIndex()]


class CustomDialog(MessageBoxBase):
    def __init__(self, parent, customWidget, title="", message="", icon="Question",
                 buttonA="OK", buttonB="Cancel", buttonC=None,
                 default=0, onTop=True, items=None, data=None, defaultIndex=None,
                 buttonIconA=MessageBoxBase.okIcon, buttonIconB=MessageBoxBase.cancelIcon, buttonIconC=None):
        self.items = items
        self.defaultIndex = defaultIndex
        self.data = data
        self.customWidget = customWidget
        super(CustomDialog, self).__init__(parent=parent, title=title, message=message, icon=icon,
                                           buttonA=buttonA,
                                           buttonB=buttonB, buttonC=buttonC, default=default, onTop=onTop,
                                           buttonIconA=buttonIconA, buttonIconB=buttonIconB, buttonIconC=buttonIconC)

    def _initMessageBox(self):
        super(CustomDialog, self)._initMessageBox()
        self.messageLayout.addSpacing(utils.dpiScale(5))
        self.messageLayout.addWidget(self.customWidget)


class MultiChoiceDialog(MessageBoxBase):
    def __init__(self, parent, title="", message="", icon="Question",
                 buttonA="OK", buttonB="Cancel", buttonC=None, default=0, onTop=True, choices=None, defaultChoice=0):
        self.choices = choices
        self.defaultChoice = defaultChoice
        super(MultiChoiceDialog, self).__init__(parent=parent, title=title, message=message, icon=icon, buttonA=buttonA,
                                                buttonB=buttonB, buttonC=buttonC, default=default, onTop=onTop)

    def _initMessageBox(self):
        super(MultiChoiceDialog, self)._initMessageBox()
        self.messageLayout.addSpacing(utils.dpiScale(5))
        self._buttonGroup = QtWidgets.QButtonGroup()
        largest = 0
        for i, c in enumerate(self.choices):
            radio = QtWidgets.QRadioButton(c, parent=self)
            if i == self.defaultChoice:
                radio.setChecked(True)
            self.messageLayout.addWidget(radio)
            self._buttonGroup.addButton(radio)
            width = radio.fontMetrics().boundingRect(radio.text()).width() + utils.dpiScale(50)
            largest = width if width > largest else largest

        self.label.setFixedWidth(max(self.label.width(), largest))

    def choice(self):
        """ Get the choice

        :return:
        """
        return self._buttonGroup.buttons().index(self._buttonGroup.checkedButton())


class MessageBoxQt(object):
    @classmethod
    def showQuestion(cls, parent, windowName, message, buttonA="Continue", buttonB="Cancel", buttonC=None,
                     icon="Question"):
        """Simple function for a dialog window with two or three buttons with changeable button names.

        buttonC=None will not show the third button.

        Icons are "NoIcon", "Warning", "Question", "Information" or "Critical"

        Returns strings "A", "B" or "C" depending on the button pressed.

        :param parent: The parent widget, can leave as None and will parent to Maya
        :type parent: object
        :param windowName: The name title of the window
        :type windowName: str
        :param message: The message/question as presented to the user inside the window
        :type message: str
        :param buttonA: The string name of the first button
        :type buttonA: str
        :param buttonB: The string name of the second button
        :type buttonB: str
        :param buttonC: The string name of the third (optional) button, if None is ignored
        :type buttonC: str

        :return buttonPressed: The button pressed, either "A", "B" or "C"
        :rtype buttonPressed: str
        """
        box = QtWidgets.QMessageBox(parent=parent)
        if icon == "Warning":
            box.setIcon(QtWidgets.QMessageBox.Warning)
        elif icon == "Question":
            box.setIcon(QtWidgets.QMessageBox.Question)
        elif icon == "Information":
            box.setIcon(QtWidgets.QMessageBox.Information)
        elif icon == "Critical":
            box.setIcon(QtWidgets.QMessageBox.Critical)
        elif icon == "NoIcon":
            box.setIcon(QtWidgets.QMessageBox.NoIcon)
        box.setWindowTitle(windowName)
        box.setText(message)
        buttonA_pressed = box.addButton(buttonA, QtWidgets.QMessageBox.YesRole)
        buttonB_pressed = box.addButton(buttonB, QtWidgets.QMessageBox.NoRole)
        if buttonC:
            buttonC_pressed = box.addButton(buttonC, QtWidgets.QMessageBox.NoRole)
        else:
            buttonC_pressed = None
        box.exec_()
        if box.clickedButton() == buttonA_pressed:
            return "A"
        elif box.clickedButton() == buttonB_pressed:
            return "B"
        elif box.clickedButton() == buttonC_pressed:
            return "C"
        else:
            return None

    @classmethod
    def showOK(cls, windowName="Confirm", parent=None, message="Proceed?", okButton=QtWidgets.QMessageBox.Ok):
        """Simple function for ok/cancel QMessageBox.question, a window popup that with ok/cancel buttons

        :param windowName: The name of the ok/cancel window
        :type windowName: str
        :param parent: The parent widget
        :type parent: Qt.widget
        :param message: The message to ask the user
        :type message: str
        :return okPressed: True if the Ok button was pressed, False if cancelled
        :rtype okPressed: bool
        """
        result = QtWidgets.QMessageBox.question(parent, windowName, message, QtWidgets.QMessageBox.Cancel | okButton)
        if result != QtWidgets.QMessageBox.Cancel:
            return True
        return False

    @classmethod
    def showSave(cls, windowName="Confirm", parent=None, message="Proceed?", showDiscard=True):
        """Simple function for save/don't save/cancel QMessageBox.question, a window popup with buttons

        Can have two or three buttons:

            showDiscard True: Save, Discard, Cancel
            showDiscard False: Save, Cancel

        :param windowName: The name of the ok/cancel window
        :type windowName: str
        :param parent: The parent widget
        :type parent: Qt.widget
        :param message: The message to ask the user
        :type message: str
        :return buttonClicked: "cancel", "save", or "discard"
        :rtype buttonClicked: str
        """
        if showDiscard:
            result = QtWidgets.QMessageBox.question(parent, windowName, message,
                                                    QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Discard
                                                    | QtWidgets.QMessageBox.Cancel)

        else:
            result = QtWidgets.QMessageBox.question(parent, windowName, message,
                                                    QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Cancel)

        if result == QtWidgets.QMessageBox.Cancel:
            return "cancel"
        if result == QtWidgets.QMessageBox.Save:
            return "save"
        if result == QtWidgets.QMessageBox.Discard:
            return "discard"


def InputDialogQt(windowName="Add Name", textValue="", parent=None, message="Rename?", windowWidth=270,
                  windowHeight=100):
    """Opens a simple QT window that locks the program asking the user to input a string into a text box

    Useful for renaming etc.

    :param windowName: The name of the ok/cancel window
    :type windowName: str
    :param textValue: The initial text in the textbox, eg. The name to be renamed
    :type textValue: str
    :param parent: The parent widget
    :type parent: Qt.widget
    :param message: The message to ask the user
    :type message: str
    :return newTextValue: The new text name entered
    :rtype newTextValue: str
    """
    dialog = QtWidgets.QInputDialog(parent)
    dialog.setInputMode(QtWidgets.QInputDialog.TextInput)
    dialog.setTextValue(textValue)
    dialog.setWindowTitle(windowName)
    dialog.setLabelText(message)
    dialog.resize(utils.dpiScale(windowWidth), utils.dpiScale(windowHeight))
    ok = dialog.exec_()
    newTextValue = dialog.textValue()
    if not ok:
        return ""
    return newTextValue


def SaveDialog(directory, fileExtension="", nameFilters="", parent=None):
    """Opens a Qt save window with options for saving a file.

    Returns the path of the file to be created, or "" if the cancel button was clicked.

    Also see MessageBox.showSave() which has the option for saving the current scene. With save, cancel or discard.

    :param directory: The path of the directory to default when the dialog window appears.
    :type directory: str
    :param fileExtension: Optional fileExtension eg ".zooScene".
    :type fileExtension: str
    :param nameFilters: Optional list of filters, example `["ZOOSCENE (*.zooScene)"]`.
    :type nameFilters: list[str]
    :return: The fullPath of the file to be saved, else "" if cancelled.
    :rtype: str
    """
    saveDialog = QtWidgets.QFileDialog(parent=parent)
    if fileExtension:
        saveDialog.setDefaultSuffix(fileExtension)
    saveDialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
    saveDialog.setDirectory(directory)
    if nameFilters:
        saveDialog.setNameFilters(nameFilters)
    if saveDialog.exec_() == QtWidgets.QDialog.Accepted:
        return saveDialog.selectedFiles()[0]
    return ""
