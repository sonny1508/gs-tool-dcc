"""The dock panel: connection state and a log of this session's imports."""

try:
    from PySide2 import QtCore, QtGui, QtWidgets
except ImportError:
    from PySide6 import QtCore, QtGui, QtWidgets


class _ElidedLabel(QtWidgets.QLabel):
    """QLabel that appends an ellipsis when the text is wider than the widget."""

    def paintEvent(self, _):
        painter = QtGui.QPainter(self)
        metrics = painter.fontMetrics()
        painter.setPen(self.palette().color(QtGui.QPalette.WindowText))
        elided = metrics.elidedText(self.text(), QtCore.Qt.ElideRight, self.width())
        painter.drawText(self.rect(), QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft, elided)


class BridgePanel(QtWidgets.QWidget):
    # Styles are set ONCE and swapped by dynamic property, never rebuilt per
    # update. setStyleSheet() forces a full Qt style repolish, and the original
    # code did it on every 3-second connection retry.
    _STYLE = """
        QLabel#dot                { font-size: 16px; color: #555; }
        QLabel#dot[live=true]     { color: #3ecf8e; }
        QLabel#status             { font-size: 12px; color: #888; }
        QLabel#status[live=true]  { color: #e0e0e0; }
        QLabel#header             { font-size: 11px; color: #888; font-weight: bold; }
        QLabel#empty              { font-size: 11px; color: #555; padding: 4px 0; }
        QListWidget               { background: #1e1e1e; border: 1px solid #333;
                                    border-radius: 4px; font-size: 11px; }
        QListWidget::item         { padding: 4px 6px; color: #ccc;
                                    border-bottom: 1px solid #2a2a2a; }
        QPushButton               { font-size: 11px; color: #ccc; background: #2a2a30;
                                    border: 1px solid #444; border-radius: 3px;
                                    padding: 4px 10px; }
        QPushButton:hover         { color: #fff; border-color: #666; }
        QPushButton#clear         { font-size: 10px; color: #888; background: transparent;
                                    padding: 0 6px; }
    """

    def __init__(self, on_launch_app, on_check_connection=None):
        super().__init__()
        # Called when the panel becomes visible; see showEvent below.
        self._on_check_connection = on_check_connection
        self.setWindowTitle("GS Asset Bridge")
        # Painter logs an error for a dock widget without one, and cannot
        # persist the dock's position between sessions.
        self.setObjectName("GSAssetBridgePanel")
        self.setMinimumWidth(260)
        self.setStyleSheet(self._STYLE)

        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        status_row = QtWidgets.QHBoxLayout()
        status_row.setSpacing(8)

        self._dot = QtWidgets.QLabel("●")
        self._dot.setObjectName("dot")
        self._dot.setFixedWidth(18)

        self._status = QtWidgets.QLabel("GS Asset Manager not running")
        self._status.setObjectName("status")

        status_row.addWidget(self._dot)
        status_row.addWidget(self._status, 1)
        root.addLayout(status_row)

        self._launch_button = QtWidgets.QPushButton("Open GS Asset Manager")
        self._launch_button.clicked.connect(on_launch_app)
        root.addWidget(self._launch_button)

        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.HLine)
        root.addWidget(separator)

        header_row = QtWidgets.QHBoxLayout()
        header = QtWidgets.QLabel("IMPORTED THIS SESSION")
        header.setObjectName("header")
        clear = QtWidgets.QPushButton("Clear")
        clear.setObjectName("clear")
        clear.setFixedHeight(20)
        clear.clicked.connect(self.clear_imports)
        header_row.addWidget(header, 1)
        header_row.addWidget(clear)
        root.addLayout(header_row)

        self._list = QtWidgets.QListWidget()
        self._list.setWordWrap(False)
        root.addWidget(self._list, 1)

        self._empty = QtWidgets.QLabel("Nothing imported yet")
        self._empty.setObjectName("empty")
        self._empty.setAlignment(QtCore.Qt.AlignCenter)
        root.addWidget(self._empty, 1)

        self._refresh_empty()

    def showEvent(self, event):
        """Dial the app again the moment this panel is looked at.

        The panel is the one place that answers "is the app connected", so
        being brought to the front is the strongest possible signal that
        somebody wants that answer to be current. Without this, a docked panel
        tabbed into view could show a state up to one backoff old — which is
        how an artist ends up reading "not running" about an app they have just
        opened and pressing the launch button below it.

        Cheap enough to do unconditionally: connected, it does nothing.
        """
        super().showEvent(event)
        if self._on_check_connection is not None:
            self._on_check_connection()

    def set_connected(self, connected):
        # Flipping a dynamic property and re-polishing two labels is far cheaper
        # than re-parsing a stylesheet, and only happens on a real transition.
        for widget in (self._dot, self._status):
            widget.setProperty("live", connected)
            widget.style().unpolish(widget)
            widget.style().polish(widget)
        self._status.setText(
            "Connected to GS Asset Manager" if connected
            else "GS Asset Manager not running"
        )
        # Nothing to open once it is already running.
        self._launch_button.setEnabled(not connected)

    def add_entry(self, name, detail, ok=True):
        item = QtWidgets.QListWidgetItem()
        self._list.addItem(item)

        row = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(row)
        layout.setContentsMargins(6, 3, 6, 3)
        layout.setSpacing(6)

        name_label = _ElidedLabel(name)
        name_label.setToolTip("%s\n%s" % (name, detail))
        name_label.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Preferred)

        badge = QtWidgets.QLabel("OK" if ok else "FAILED")
        badge.setStyleSheet(
            "font-size: 9px; font-weight: bold; color: #e8e8e8; border-radius: 3px;"
            " padding: 1px 6px; background: %s;" % ("#2d6b50" if ok else "#8a3a3a")
        )
        badge.setFixedSize(54, 16)
        badge.setAlignment(QtCore.Qt.AlignCenter)

        layout.addWidget(name_label, 1)
        layout.addWidget(badge, 0)

        item.setSizeHint(QtCore.QSize(0, 32))
        self._list.setItemWidget(item, row)
        self._list.scrollToBottom()
        self._refresh_empty()

    def clear_imports(self):
        self._list.clear()
        self._refresh_empty()

    def _refresh_empty(self):
        has_items = self._list.count() > 0
        self._list.setVisible(has_items)
        self._empty.setVisible(not has_items)
