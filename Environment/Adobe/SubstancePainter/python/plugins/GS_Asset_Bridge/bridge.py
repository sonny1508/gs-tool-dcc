"""TCP link to GS Asset Manager.

GS Asset Manager is the server; this is the client and dials out to it. That
means the plugin sits idle and retrying whenever the app is closed — which is
most of the day — so idle cost is the single most important property here.

The previous version retried every 3 seconds and, on each attempt, wrote a line
to Painter's log panel and called setStyleSheet() on two widgets. Over an 8-hour
day with the app closed that is ~9,600 retained log entries and ~9,600 full Qt
style repolishes, which is what made Painter degrade over a session.

The fix for that was to touch the log and the widgets only when the connection
state actually CHANGES, and it is the whole fix: a refused connect to
127.0.0.1 costs a syscall that returns immediately, and doing nothing with the
result costs nothing at all.

The retry ceiling was pushed to 30 seconds at the same time, which was one
change too many. Idle cost was never the socket, and the artist pays that
ceiling at the exact moment they care: they open GS Asset Manager, switch to
Painter, and the panel says the app is not running for up to half a minute
after it plainly is. So the ceiling is 5 seconds, and the wait is interruptible
-- retry_now() dials again on the spot when something happens that makes a
connection likely, such as the panel being brought to the front or the app
being launched from the button on it.
"""

import json
import socket
import threading

import substance_painter.logging as sp_log

try:
    from PySide2 import QtCore
except ImportError:
    from PySide6 import QtCore


HOST = "127.0.0.1"
PORT = 47832
PROTOCOL_VERSION = 1

RECONNECT_DELAY_MIN = 1.0
RECONNECT_DELAY_MAX = 5.0
RECONNECT_BACKOFF = 2.0


class BridgeSignals(QtCore.QObject):
    """Marshals socket-thread events onto Painter's main thread.

    `request` carries a dict rather than a delimited string. The original code
    packed path, location and label into "a|b|c", which corrupted any path or
    label containing a pipe — and Megascans ships assets with spaces and
    non-ASCII names such as `Bozkow`.
    """
    state_changed = QtCore.Signal(bool)
    request = QtCore.Signal(object)


class BridgeThread(threading.Thread):
    def __init__(self, signals):
        super().__init__(daemon=True, name="gs-asset-bridge")
        self.signals = signals
        self._stop_event = threading.Event()
        # Cuts the current backoff short. Anything that makes a connection
        # newly likely sets this rather than waiting the retry out.
        self._wake_event = threading.Event()
        self._sock = None
        self._send_lock = threading.Lock()
        self._connected = False

    # -- lifecycle ------------------------------------------------------------

    def run(self):
        delay = RECONNECT_DELAY_MIN
        while not self._stop_event.is_set():
            if self._try_connect():
                delay = RECONNECT_DELAY_MIN   # reset backoff after a good run
                self._recv_loop()
                self._set_connected(False)
            else:
                delay = min(delay * RECONNECT_BACKOFF, RECONNECT_DELAY_MAX)

            if not self._stop_event.is_set():
                # Interruptible: retry_now() releases this immediately. Cleared
                # afterwards so the next pass waits properly again.
                self._wake_event.wait(delay)
                self._wake_event.clear()

    def _try_connect(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5.0)
            sock.connect((HOST, PORT))
            sock.settimeout(None)
            # Detect a peer that vanished without closing cleanly, so a dead
            # socket cannot sit there reporting "connected" while exports
            # disappear into nothing.
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            self._sock = sock
            self._set_connected(True)
            return True
        except OSError:
            # Deliberately silent: this fires on every retry while the app is
            # closed, which is most of the day.
            self._close_socket()
            return False

    def _set_connected(self, value):
        if value == self._connected:
            return                      # no transition, nothing to report
        self._connected = value
        self.signals.state_changed.emit(value)

    def _close_socket(self):
        if self._sock is not None:
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None

    def retry_now(self):
        """Dial again immediately instead of finishing the current backoff.

        Safe to call from the UI thread and safe to call when already
        connected, in which case the thread is sitting in recv() and this does
        nothing at all.
        """
        self._wake_event.set()

    def stop(self):
        self._stop_event.set()
        # Or a stopping thread sits out the rest of its backoff before noticing.
        self._wake_event.set()
        self._close_socket()

    @property
    def connected(self):
        return self._connected

    # -- protocol -------------------------------------------------------------

    def _recv_loop(self):
        buffer = b""
        while not self._stop_event.is_set():
            try:
                chunk = self._sock.recv(8192)
            except OSError:
                break
            if not chunk:
                break

            buffer += chunk
            # A TCP read can split or merge messages, so hold the trailing
            # partial line until the rest arrives.
            while b"\n" in buffer:
                line, buffer = buffer.split(b"\n", 1)
                text = line.decode("utf-8", errors="replace").strip()
                if text:
                    self._dispatch(text)
        self._close_socket()

    def _dispatch(self, raw):
        try:
            message = json.loads(raw)
        except json.JSONDecodeError:
            sp_log.warning("[GS Asset Bridge] ignoring malformed message")
            return

        if message.get("v", 0) > PROTOCOL_VERSION:
            self.send({
                "status": "error",
                "error": "UNSUPPORTED_PROTOCOL",
                "detail": "Update the Painter plugin to match GS Asset Manager.",
            })
            return

        # Handled on the main thread; the ack goes out once the import has
        # actually run. The original code acked on receipt, so the app reported
        # success even when the import failed.
        self.signals.request.emit(message)

    def send(self, payload):
        """Thread-safe reply. Both the socket thread and the main thread use this."""
        with self._send_lock:
            if self._sock is None:
                return
            try:
                self._sock.sendall((json.dumps(payload) + "\n").encode("utf-8"))
            except OSError:
                pass
