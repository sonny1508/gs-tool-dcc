from functools import partial

from zoovendor.Qt import QtWidgets, QtCore, QtGui, QtCompat
from zoo.libs.pyqt.extended import combobox
from zoo.libs.pyqt.widgets import buttons, layouts
from zoo.libs.pyqt.models import constants
from zoo.libs.pyqt import utils, uiconstants
from zoo.preferences.interfaces import coreinterfaces


def drawRect(painter, option, color):
    points = (QtCore.QPoint(option.rect.x() + 5, option.rect.y()),
              QtCore.QPoint(option.rect.x(), option.rect.y()),
              QtCore.QPoint(option.rect.x(), option.rect.y() + 5))
    polygonTriangle = QtGui.QPolygon.fromList(points)

    painter.save()
    painter.setRenderHint(painter.Antialiasing)
    painter.setBrush(QtGui.QBrush(color))
    painter.setPen(QtGui.QPen(color))
    painter.drawPolygon(polygonTriangle)
    painter.restore()


def paintHtml(delegate, painter, option, index):
    """
    :param delegate:
    :type delegate: :class:`QtWidgets.QStyledItemDelegate`
    :param painter:
    :type painter: :class:`QtGui.QPainter`
    :param option:
    :type option:  :class:`QStyleOptionViewItem`
    :param index:
    :type index: :class:`QtCore.QModelIndex`
    :rtype: bool
    """
    delegate.initStyleOption(option, index)
    if not option.text:
        return False
    model = index.model()
    textColor = model.data(index, QtCore.Qt.ForegroundRole)
    textMargin = model.data(index, constants.textMarginRole)
    style = option.widget.style() if option.widget else QtWidgets.QApplication.style()
    textOption = QtGui.QTextOption()
    textOption.setWrapMode(
        QtGui.QTextOption.WordWrap if QtWidgets.QStyleOptionViewItem.WrapText else QtGui.QTextOption.ManualWrap)

    textOption.setTextDirection(option.direction)

    doc = QtGui.QTextDocument()
    doc.setDefaultTextOption(textOption)
    doc.setHtml('<font color=\"{}\">{}</font>'.format(textColor.name(QtGui.QColor.HexRgb), option.text))
    doc.setDefaultFont(option.font)
    doc.setDocumentMargin(textMargin)
    doc.setTextWidth(option.rect.width())
    doc.adjustSize()

    if doc.size().width() > option.rect.width():
        # Elide text
        cursor = QtGui.QTextCursor(doc)
        cursor.movePosition(QtGui.QTextCursor.End)

        elidedPostfix = "..."
        metric = QtGui.QFontMetrics(option.font)
        postfixWidth = metric.horizontalAdvance(elidedPostfix)

        while doc.size().width() > option.rect.width() - postfixWidth:
            cursor.deletePreviousChar()
            doc.adjustSize()

        cursor.insertText(elidedPostfix)

    # Painting item without text (this takes care of painting e.g. the highlighted for selected
    # or hovered over items in an ItemView)
    option.text = ""
    style.drawControl(QtWidgets.QStyle.CE_ItemViewItem, option, painter, option.widget)

    # Figure out where to render the text in order to follow the requested alignment
    textRect = style.subElementRect(QtWidgets.QStyle.SE_ItemViewItemText, option)
    documentSize = QtCore.QSize(doc.size().width(), doc.size().height())  # Convert QSizeF to QSize
    layoutRect = QtWidgets.QStyle.alignedRect(QtCore.Qt.LayoutDirectionAuto,
                                              option.displayAlignment,
                                              documentSize,
                                              textRect)

    painter.save()

    # Translate the painter to the origin of the layout rectangle in order for the text to be
    # rendered at the correct position
    painter.translate(layoutRect.topLeft())
    doc.drawContents(painter, QtCore.QRectF(textRect.translated(-textRect.topLeft())))

    painter.restore()
    return True


class NumericDoubleDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent):
        super(NumericDoubleDelegate, self).__init__(parent)

    def createEditor(self, parent, option, index):
        model = index.model()
        widget = QtWidgets.QDoubleSpinBox(parent=parent)
        widget.setMinimum(model.data(index, constants.minValue))
        widget.setMaximum(constants.maxValue)
        return widget

    def setEditorData(self, widget, index):
        value = index.model().data(index, QtCore.Qt.EditRole)
        widget.setValue(value)

    def setModelData(self, widget, model, index):
        value = widget.value()
        model.setData(index, value, QtCore.Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

    def paint(self, painter, option, index):
        if not paintHtml(self, painter, option, index):
            return super(NumericDoubleDelegate, self).paint(painter, option, index)
        model = index.model()
        color = model.data(index, constants.editChangedRole)
        if color is None:
            return
        drawRect(painter, option, color)


class NumericIntDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent):
        super(NumericIntDelegate, self).__init__(parent)

    def createEditor(self, parent, option, index):
        model = index.model()
        widget = QtWidgets.QSpinBox(parent=parent)
        widget.setMinimum(model.data(index, constants.minValue))
        widget.setMaximum(model.data(index, constants.maxValue))
        return widget

    def setEditorData(self, widget, index):
        widget.blockSignals(True)
        value = index.model().data(index, QtCore.Qt.EditRole)
        widget.setValue(value)
        widget.blockSignals(False)

    def setModelData(self, widget, model, index):
        value = widget.value()
        model.setData(index, int(value), QtCore.Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

    def paint(self, painter, option, index):
        if not paintHtml(self, painter, option, index):
            return super(NumericIntDelegate, self).paint(painter, option, index)
        model = index.model()
        color = model.data(index, constants.editChangedRole)
        if color is None:
            return
        drawRect(painter, option, color)


class EnumerationDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent):
        super(EnumerationDelegate, self).__init__(parent)
        self.requiresPopup = False

    def createEditor(self, parent, option, index):
        model = index.model()
        combo = combobox.ExtendedComboBox(model.data(index, constants.enumsRole), parent)
        return combo

    def editorEvent(self, event, model, option, index):

        if event.type() == QtCore.QEvent.MouseButtonRelease and \
                event.button() == QtCore.Qt.LeftButton \
                and (model.flags(index) & QtCore.Qt.ItemIsEditable):
            view = option.widget
            if view is None:
                return True
            view.setCurrentIndex(index)
            view.edit(index)
            self.requiresPopup = True
        return super(EnumerationDelegate, self).editorEvent(event, model, option, index)

    def setEditorData(self, editor, index):
        editor.blockSignals(True)
        text = index.model().data(index, QtCore.Qt.DisplayRole)
        enums = index.model().data(index, constants.enumsRole)
        index = editor.findText(text, QtCore.Qt.MatchFixedString)
        if index >= 0:
            editor.clear()
            editor.addItems(enums)
            editor.setCurrentIndex(index)
        if self.requiresPopup:
            self.requiresPopup = False
            editor.showPopup()
        editor.blockSignals(False)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentIndex(), role=QtCore.Qt.EditRole)

    def paint(self, painter, option, index):
        if not paintHtml(self, painter, option, index):
            return super(EnumerationDelegate, self).paint(painter, option, index)
        model = index.model()
        color = model.data(index, constants.editChangedRole)
        if color is None:
            return
        drawRect(painter, option, color)


class ButtonEnumerationDelegate(QtWidgets.QStyledItemDelegate):
    """Delegate which displays a combobox and button. Designed to be persistent on the view.

    The combobox will be visible when the users mouse enters the cell only.

    """

    def __init__(self, parent):
        super(ButtonEnumerationDelegate, self).__init__(parent=parent)
        # only initialized once for the view so cache here.
        self.btnColorStr = coreinterfaces.coreInterface().stylesheetSetting("$TBL_TREE_BG_COLOR")

    def createEditor(self, parent, option, index):
        """Returns the editor to be used for editing the data item with the given index.
        Contains both a comboBox(leftSide) and a button(right side).

        :param parent: The parent widget for the editor
        :type parent: :class:`QtWidgets.QWidget`
        :param option: The styling instance for the cell.
        :type option: :class:`QtWidgets.QStyleOptionViewItem`
        :param index: The cell Model index
        :type index: :class:`QtCore.QModelIndex`
        :return: The created custom editor.
        :rtype: :class:`ButtonEnumerationWidget`
        """
        self.initStyleOption(option, index)
        model = index.model()
        enums = model.data(index, constants.enumsRole)
        rect = option.rect  # type: QtCore.QRect
        widget = ButtonEnumerationWidget(enums, rect.size(), parent)
        widget.setEnabled(bool(model.flags(index) & QtCore.Qt.ItemIsEditable))
        widget.enableEnterLeavePopup = bool(model.flags(index) & QtCore.Qt.ItemIsEditable)
        widget.btn.setStyleSheet("background-color: #{};".format(self.btnColorStr))
        widget.buttonClicked.connect(partial(self._onButtonClicked, model, widget, index))
        widget.combo.currentIndexChanged.connect(partial(self._commitAndCloseEditor, widget))
        return widget

    def _commitAndCloseEditor(self, widget, index):
        self.commitData.emit(widget)
        self.closeEditor.emit(widget, QtWidgets.QAbstractItemDelegate.NoHint)

    def _onButtonClicked(self, model, widget, index):
        dataChanged = model.data(index, constants.buttonClickedRole)
        if not dataChanged:
            return
        QtCompat.dataChanged(model, index, index)
        widget.combo.blockSignals(True)
        widget.combo.clear()
        widget.combo.addItems(model.data(index, constants.enumsRole))
        widget.combo.blockSignals(False)
        self.setEditorData(widget, index)

    def setEditorData(self, editor, index):
        model = index.model()
        text = model.data(index, QtCore.Qt.DisplayRole)
        enums = model.data(index, constants.enumsRole)
        matchIndex = editor.combo.findText(text, QtCore.Qt.MatchFixedString)
        if matchIndex >= 0:
            editor.combo.blockSignals(True)
            editor.combo.clear()
            editor.combo.addItems(enums)
            editor.combo.setCurrentIndex(matchIndex)
            editor.combo.blockSignals(False)

    def setModelData(self, editor, model, index):
        model.setData(index, int(editor.combo.currentIndex()), role=QtCore.Qt.EditRole)

    def paint(self, painter, option, index):
        if not paintHtml(self, painter, option, index):
            return super(ButtonEnumerationDelegate, self).paint(painter, option, index)
        model = index.model()
        color = model.data(index, constants.editChangedRole)

        if color is None:
            return
        drawRect(painter, option, color)


class LineEditButtonDelegate(QtWidgets.QStyledItemDelegate):
    """Delegate which displays a combobox and button. Designed to be persistent on the view.

    The combobox will be visible when the users mouse enters the cell only.

    """

    def __init__(self, parent):
        super(LineEditButtonDelegate, self).__init__(parent=parent)
        # only initialized once for the view so cache here.
        self.btnColorStr = coreinterfaces.coreInterface().stylesheetSetting("$TBL_TREE_BG_COLOR")

    def createEditor(self, parent, option, index):
        """Returns the editor to be used for editing the data item with the given index.
        Contains both a comboBox(leftSide) and a button(right side).

        :param parent: The parent widget for the editor
        :type parent: :class:`QtWidgets.QWidget`
        :param option: The styling instance for the cell.
        :type option: :class:`QtWidgets.QStyleOptionViewItem`
        :param index: The cell Model index
        :type index: :class:`QtCore.QModelIndex`
        :return: The created custom editor.
        :rtype: :class:`LineEdit`
        """
        self.initStyleOption(option, index)
        model = index.model()
        text = model.data(index, QtCore.Qt.DisplayRole)
        rect = option.rect  # type: QtCore.QRect
        widget = LineEditButtonWidget(text, rect.size(), parent)
        widget.setEnabled(bool(model.flags(index) & QtCore.Qt.ItemIsEditable))
        widget.btn.setStyleSheet("background-color: #{};".format(self.btnColorStr))
        widget.buttonClicked.connect(partial(self._onButtonClicked, model, widget, index))
        widget.lineEdit.editingFinished.connect(partial(self._commitAndCloseEditor, widget, index))
        return widget

    def _commitAndCloseEditor(self, widget, index):
        self.commitData.emit(widget)
        self.closeEditor.emit(widget, QtWidgets.QAbstractItemDelegate.NoHint)

    def _onButtonClicked(self, model, widget, index):
        """

        :param model:
        :type model:
        :param widget:
        :type widget: :class:`LineEditButtonWidget`
        :param index:
        :type index: :class:`QtCore.QModelIndex`
        """
        dataChanged = model.data(index, constants.buttonClickedRole)
        if not dataChanged:
            return
        QtCompat.dataChanged(model, index, index)
        widget.lineEdit.blockSignals(True)
        widget.lineEdit.setText(model.data(index, QtCore.Qt.DisplayRole))
        widget.lineEdit.blockSignals(False)
        self.setEditorData(widget, index)

    def setEditorData(self, editor, index):
        model = index.model()
        text = model.data(index, QtCore.Qt.DisplayRole)
        editor.lineEdit.setText(text)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.lineEdit.text(), role=QtCore.Qt.EditRole)

    def paint(self, painter, option, index):
        if not paintHtml(self, painter, option, index):
            return super(LineEditButtonDelegate, self).paint(painter, option, index)
        model = index.model()
        color = model.data(index, constants.editChangedRole)
        if color is None:
            return
        drawRect(painter, option, color)


class ButtonDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent):
        super(ButtonDelegate, self).__init__(parent)

    def createEditor(self, parent, option, index):
        model = index.model()
        widget = buttons.regularButton(text=str(model.data(index, QtCore.Qt.DisplayRole)),
                                       parent=parent)
        widget.clicked.connect(partial(self.setModelData, widget, model, index))
        return widget

    def setEditorData(self, widget, index):
        text = index.model().data(index, QtCore.Qt.DisplayRole)
        widget.setText(str(text))

    def setModelData(self, widget, model, index):
        model.setData(index, None, QtCore.Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

    def paint(self, painter, option, index):
        if not paintHtml(self, painter, option, index):
            return super(ButtonDelegate, self).paint(painter, option, index)
        model = index.model()
        color = model.data(index, constants.editChangedRole)
        if color is None:
            return
        drawRect(painter, option, color)


class CheckBoxDelegate(QtWidgets.QStyledItemDelegate):
    """
    A delegate that places a fully functioning QCheckBox in every
    cell of the column to which it's applied
    """

    def __init__(self, parent):
        super(CheckBoxDelegate, self).__init__(parent)

    def createEditor(self, parent, option, index):
        """
        Important, otherwise an editor is created if the user clicks in this cell.
        ** Need to hook up a signal to the model
        """
        return None

    def paint(self, painter, option, index):
        """
        Paint a checkbox without the label.
        """

        checked = bool(index.data())
        check_box_style_option = QtWidgets.QStyleOptionButton()
        isEnabled = (index.flags() & QtCore.Qt.ItemIsEditable) > 0 and (index.flags() & QtCore.Qt.ItemIsEnabled) > 0
        if isEnabled:
            check_box_style_option.state |= QtWidgets.QStyle.State_Enabled
        else:
            check_box_style_option.state |= QtWidgets.QStyle.State_ReadOnly

        if checked:
            check_box_style_option.state |= QtWidgets.QStyle.State_On
        else:
            check_box_style_option.state |= QtWidgets.QStyle.State_Off
        check_box_style_option.rect = self.getCheckBoxRect(option)

        check_box_style_option.state |= QtWidgets.QStyle.State_Enabled

        QtWidgets.QApplication.style().drawControl(QtWidgets.QStyle.CE_CheckBox, check_box_style_option, painter)
        model = index.model()
        color = model.data(index, constants.editChangedRole)
        if color is None:
            return
        drawRect(painter, option, color)

    def editorEvent(self, event, model, option, index):
        """
        Change the data in the model and the state of the checkbox
        if the user presses the left mousebutton or presses
        Key_Space or Key_Select and this cell is editable. Otherwise do nothing.
        """
        if index.flags() & QtCore.Qt.ItemIsEditable < 1:
            return False

        # Do not change the checkbox-state
        if event.type() == QtCore.QEvent.MouseButtonPress or event.type() == QtCore.QEvent.MouseMove or event.type() == QtCore.QEvent.KeyPress:
            return False
        elif event.type() == QtCore.QEvent.MouseButtonRelease or event.type() == QtCore.QEvent.MouseButtonDblClick:
            if event.button() != QtCore.Qt.LeftButton or not self.getCheckBoxRect(option).contains(event.pos()):
                return False
            if event.type() == QtCore.QEvent.MouseButtonDblClick:
                return True

        # Change the checkbox-state
        self.setModelData(None, model, index)
        return True

    def setModelData(self, editor, model, index):
        """
        The user wanted to change the old state in the opposite.
        """
        newValue = not index.data()
        model.setData(index, newValue, QtCore.Qt.EditRole)

    def getCheckBoxRect(self, option):
        check_box_style_option = QtWidgets.QStyleOptionButton()
        check_box_rect = QtWidgets.QApplication.style().subElementRect(QtWidgets.QStyle.SE_CheckBoxIndicator,
                                                                       check_box_style_option, None)
        check_box_point = QtCore.QPoint(option.rect.x() +
                                        option.rect.width() * 0.5 -
                                        check_box_rect.width() * 0.5,
                                        option.rect.y() +
                                        option.rect.height() * 0.5 -
                                        check_box_rect.height() * 0.5)
        return QtCore.QRect(check_box_point, check_box_rect.size())


class PixmapDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent):
        super(PixmapDelegate, self).__init__(parent)

    def paint(self, painter, option, index):
        model = index.model()
        icon = model.data(index, role=QtCore.Qt.DecorationRole)
        if not icon:
            return super(PixmapDelegate, self).paint(painter, option, index)
        pixmap = icon.pixmap(model.data(index, role=constants.iconSizeRole))
        painter.drawPixmap(option.rect.topLeft(), pixmap)

        color = model.data(index, constants.editChangedRole)
        if color is None:
            return
        drawRect(painter, option, color)
        super(PixmapDelegate, self).paint(painter, option, index)


class DateColumnDelegate(QtWidgets.QStyledItemDelegate):

    def __init__(self, dateFormat="yyyy-MM-dd", parent=None):
        super(DateColumnDelegate, self).__init__(parent)
        self.format = dateFormat

    def createEditor(self, parent, option, index):
        model = index.model()
        dateedit = QtWidgets.QDateEdit(parent)
        dateedit.setDateRange(model.data(index, constants.minValue), model.data(index, constants.maxValue))
        dateedit.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        dateedit.setDisplayFormat(self.format)
        dateedit.setCalendarPopup(True)
        return dateedit

    def setEditorData(self, editor, index):
        value = index.model().data(index, QtCore.Qt.DisplayRole)
        editor.setDate(value)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.date())

    def paint(self, painter, option, index):
        super(DateColumnDelegate, self).paint(painter, option, index)
        model = index.model()
        color = model.data(index, constants.editChangedRole)
        if color is None:
            return
        drawRect(painter, option, color)


class HtmlDelegate(QtWidgets.QStyledItemDelegate):
    def paint(self, painter, option, index):
        if not paintHtml(self, painter, option, index):
            return super(HtmlDelegate, self).paint(painter, option, index)

    def sizeHint(self, option, index):
        self.initStyleOption(option, index)
        if not option.text:
            return super(HtmlDelegate, self).sizeHint(option, index)
        model = index.model()
        textMargin = model.data(index, constants.textMarginRole)
        if not textMargin:
            return super(HtmlDelegate, self).sizeHint(option, index)
        doc = QtGui.QTextDocument()
        doc.setHtml(option.text)
        doc.setDefaultFont(option.font)
        doc.setDocumentMargin(textMargin)
        return QtCore.QSize(doc.idealWidth(), doc.size().height())


class ButtonEnumerationWidget(QtWidgets.QWidget):
    """Combobox with a button to the Right side.

    This widget has overrides for the enter and leave events to handle visibility of the combo.
    """
    buttonClicked = QtCore.Signal()

    def __init__(self, enums, size, parent):
        super(ButtonEnumerationWidget, self).__init__(parent=parent)

        self.setContentsMargins(0, 0, 0, 0)
        layout = layouts.hBoxLayout(self, spacing=0, margins=(0, 0, 0, 0))
        self.btn = buttons.regularButton(text="", icon="arrowSingleLeft",
                                         iconSize=utils.dpiScale(uiconstants.BTN_W_ICN_SML),
                                         maxWidth=utils.dpiScale(uiconstants.BTN_W_ICN_REG),
                                         maxHeight=size.height(),
                                         parent=self)
        self.combo = combobox.ExtendedComboBox(enums, parent)
        self.combo.setMinimumHeight(size.height())
        policy = self.combo.sizePolicy()
        policy.setRetainSizeWhenHidden(True)
        self.combo.setSizePolicy(policy)
        self.combo.setHidden(True)
        self.enableEnterLeavePopup = True
        self._currentComboIsFocused = False
        layout.addWidget(self.combo)
        layout.addWidget(self.btn)
        self.btn.clicked.connect(self.buttonClicked.emit)

        # monkey patch the hide popup and show popup of the combobox menu so that we can
        # display the combo at the right time.
        def _showComboPopup():
            # set before the showPopup super call because leaveEvent on ButtonEnumerationWidget
            # will be called which would hide the combobox so this ordering is important
            self._currentComboIsFocused = True
            super(combobox.ExtendedComboBox, self.combo).showPopup()

        def hideComboPopup():
            self._currentComboIsFocused = False
            super(combobox.ExtendedComboBox, self.combo).hidePopup()
            self.combo.hide()

        self.combo.hidePopup = hideComboPopup
        self.combo.showPopup = _showComboPopup

    def enterEvent(self, event):
        # when the mouse enters the widget aka. the cell show the combo box
        super(ButtonEnumerationWidget, self).enterEvent(event)
        if self.enableEnterLeavePopup:
            self.combo.show()

    def leaveEvent(self, event):
        super(ButtonEnumerationWidget, self).leaveEvent(event)
        if not self.enableEnterLeavePopup:
            return
        # only when the combobox menu has been hidden will we hide the combobox on leave.
        if not self._currentComboIsFocused:
            self.combo.hide()


class LineEditButtonWidget(QtWidgets.QWidget):
    """LineEdit with a button to the Right side.
    """
    buttonClicked = QtCore.Signal()

    def __init__(self, text, size, parent):
        super(LineEditButtonWidget, self).__init__(parent=parent)

        self.setContentsMargins(0, 0, 0, 0)
        layout = layouts.hBoxLayout(self, spacing=0, margins=(0, 0, 0, 0))
        self.btn = buttons.regularButton(text="", icon="arrowSingleLeft",
                                         iconSize=utils.dpiScale(uiconstants.BTN_W_ICN_SML),
                                         maxWidth=utils.dpiScale(uiconstants.BTN_W_ICN_REG),
                                         maxHeight=size.height(),
                                         parent=self)
        self.lineEdit = QtWidgets.QLineEdit(text, parent=self)
        self.lineEdit.setContentsMargins(0, 0, 0, 0)
        self.lineEdit.setMinimumHeight(size.height())
        self.lineEdit.editingFinished.connect(self.lineEdit.hide)
        self.lineEdit.setHidden(True)
        policy = self.lineEdit.sizePolicy()
        policy.setRetainSizeWhenHidden(True)
        self.lineEdit.setSizePolicy(policy)
        layout.addWidget(self.lineEdit)
        layout.addWidget(self.btn)
        self.btn.clicked.connect(self.buttonClicked.emit)
        self.lineEdit.focusOutEvent = self._focusOutEventLineEdit

    def _focusOutEventLineEdit(self, event):
        super(LineEditButtonWidget, self).focusOutEvent(event)
        if self.lineEdit.hasAcceptableInput():
            self.lineEdit.hide()
            self.lineEdit.editingFinished.emit()

    def mouseDoubleClickEvent(self, event):
        self.lineEdit.show()
        self.lineEdit.selectAll()
        self.lineEdit.setFocus()
        super(LineEditButtonWidget, self).mouseDoubleClickEvent(event)
