"""GS File Transfer: what is waiting where, and since when, for the tab's file rows.

Local rows are read while drawing: one local file or folder is cheap to look at.
Server rows are not, because an unreachable or slow share can block for seconds,
and a draw runs on every redraw. They are read on a worker thread, once per user
and mode, and kept until a transfer or the refresh button clears them.
"""
from __future__ import annotations

import datetime
import os
import threading

import bpy

from ...common import redraw_view3d
from .config import SERVER_DIR, server_stem, username
from .transfer import individual_files, individual_mode, individual_pattern, local_location


def describe_time(mtime):
    """'Today 14:32', 'Yesterday 09:10' or '12 Nov 09:10': never goes stale while on screen."""
    when = datetime.datetime.fromtimestamp(mtime)
    today = datetime.date.today()
    if when.date() == today:
        day = "Today"
    elif when.date() == today - datetime.timedelta(days=1):
        day = "Yesterday"
    else:
        day = f"{when.day} {when.strftime('%b')}"
    return f"{day} {when.strftime('%H:%M')}"


def scan(directory, stem, individual):
    """(name, when) for one transfer: '<stem>.fbx', or all its per-object files.

    File system only, so it is safe on a worker thread.
    """
    if not individual:
        path = os.path.join(directory, stem + ".fbx")
        try:
            return os.path.basename(path), describe_time(os.path.getmtime(path))
        except OSError:
            return os.path.basename(path), "none yet"
    times = []
    for path in individual_files(directory, stem):
        try:
            times.append(os.path.getmtime(path))
        except OSError:
            pass
    name = f"{individual_pattern(stem)} ({len(times)})"
    return name, describe_time(max(times)) if times else "none yet"


def local_row(context):
    individual = individual_mode(context)
    directory, stem = local_location(context)
    if individual:
        name, when = scan(directory, stem, True)
        return f"individual\\{name}", when
    return scan(directory, stem, False)


class ServerFiles:
    """The Received / Sent rows for one (user, individual) pair, read on a worker thread.

    ``rows_for`` is called from draw: it answers from the cache, or starts a read
    and answers None ("checking") until the result is in. Only the newest request
    matters, so a request made while a read runs replaces any earlier waiting one.
    """
    key = None          # (user, individual) the rows below belong to
    rows = None         # ((name, when) received, (name, when) sent)
    _thread = None
    _running = None     # key being read
    _waiting = None     # key asked for while another read ran
    _result = {}

    @classmethod
    def rows_for(cls, user, individual):
        key = (user, individual)
        if cls.key == key:
            return cls.rows
        cls._request(key)
        return None

    @classmethod
    def clear(cls):
        """Forget the cached rows, so the next draw reads them again (after a transfer)."""
        cls.key = None
        cls.rows = None
        if cls._thread is not None and cls._thread.is_alive():
            cls._waiting = cls._running     # it may have looked before the transfer landed
        redraw_view3d()

    @classmethod
    def _request(cls, key):
        if cls._thread is not None and cls._thread.is_alive():
            if key != cls._running:
                cls._waiting = key
            return
        cls._start(key)
        if not bpy.app.timers.is_registered(_apply):
            bpy.app.timers.register(_apply, first_interval=0.1)

    @classmethod
    def _start(cls, key):
        cls._running = key
        cls._waiting = None
        cls._result = {}
        cls._thread = threading.Thread(target=cls._read, args=(key, cls._result), daemon=True)
        cls._thread.start()

    @staticmethod
    def _read(key, result):
        # Worker thread: file system only, never bpy.
        other, individual = key
        received = scan(os.path.join(SERVER_DIR, other), server_stem(other, username), individual)
        sent = scan(os.path.join(SERVER_DIR, username), server_stem(username, other), individual)
        result["rows"] = (received, sent)


def _apply():
    if ServerFiles._thread is not None and ServerFiles._thread.is_alive():
        return 0.1
    ServerFiles.key = ServerFiles._running
    ServerFiles.rows = ServerFiles._result.get("rows")
    redraw_view3d()
    waiting = ServerFiles._waiting
    if waiting is not None:
        ServerFiles._start(waiting)     # this timer keeps running for it
        return 0.1
    return None


def unregister():
    if bpy.app.timers.is_registered(_apply):
        bpy.app.timers.unregister(_apply)
