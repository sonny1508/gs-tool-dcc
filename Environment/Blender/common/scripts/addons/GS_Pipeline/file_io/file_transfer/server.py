"""GS File Transfer: whether the studio share is reachable, and who is on the
user list. Checked on a worker thread, so an unreachable share never freezes
Blender."""
from __future__ import annotations

import csv
import os
import threading

import bpy

from ...common import redraw_view3d
from .config import SERVER_DIR, USER_CSVS


def _normalize_user(raw):
    """Turn a raw CSV user value into a bare studio username.

    The auto-deployment CSV writes entries like ``GLENDASTUDIO01\\son.ha.01`` and
    may append a status tag such as `` (locked)``. We want just ``son.ha.01``:
      * drop everything up to and including the last domain backslash, and
      * strip any trailing parenthesised status tag.
    """
    if not raw:
        return ""
    name = raw.strip()
    # Drop the domain prefix (everything through the last backslash).
    name = name.rsplit("\\", 1)[-1]
    # Remove a trailing status tag like "(locked)".
    paren = name.find("(")
    if paren != -1:
        name = name[:paren]
    return name.strip()


def _read_users(csv_path):
    """Usernames from one deployment CSV: any column order, header 'User' (or 'Users')."""
    # utf-8-sig: the Update CSV starts with a BOM.
    with open(csv_path, 'r', newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.reader(csvfile)
        header = next(reader, None)
        if header is None:
            raise ValueError("CSV file is empty")
        column = next((i for i, name in enumerate(header) if name.strip().lower() in ("user", "users")), None)
        if column is None:
            raise ValueError("No 'User' column found in CSV file")
        return [_normalize_user(row[column]) for row in reader if len(row) > column]


def read_user_list():
    """Every user from all USER_CSVS, de-duplicated and sorted. An unreadable file is skipped."""
    users = {}
    for path in USER_CSVS:
        try:
            for name in _read_users(path):
                if name:
                    users.setdefault(name.lower(), name)
        except Exception as e:
            print(f"Error reading user list from {path}: {e}")
    names = sorted(users.values(), key=str.lower)
    print(f"Loaded {len(names)} users from {len(USER_CSVS)} CSV files")
    return names


class ServerStatus:
    """Whether the share is reachable, and the user list read from it.

    The check runs on a worker thread: an unreachable UNC path can block for tens
    of seconds, and Blender must not freeze while it does. The result is applied
    on the main thread by a timer, because bpy data can't be touched from another
    thread. ``online`` is None while a check is running.
    """
    online = None
    users = []
    _thread = None
    _result = {}

    @classmethod
    def check(cls):
        if cls._thread is not None and cls._thread.is_alive():
            return
        cls.online = None
        cls._result = {}
        cls._thread = threading.Thread(target=cls._probe, args=(cls._result,), daemon=True)
        cls._thread.start()
        if not bpy.app.timers.is_registered(_apply_server_check):
            bpy.app.timers.register(_apply_server_check, first_interval=0.2, persistent=True)

    @staticmethod
    def _probe(result):
        # Worker thread: file system only, never bpy.
        result["online"] = os.path.isdir(SERVER_DIR)
        result["users"] = read_user_list()


def fill_user_lists():
    """Copy the known users into the window manager list that the User search reads."""
    for wm in bpy.data.window_managers:
        people = wm.gs_person_list
        people.clear()
        for name in ServerStatus.users:
            people.add().name = name


def _apply_server_check():
    if ServerStatus._thread.is_alive():
        return 0.2
    ServerStatus.online = ServerStatus._result.get("online", False)
    ServerStatus.users = ServerStatus._result.get("users", [])
    if not ServerStatus.online:
        print(f"GS File Transfer: can't reach {SERVER_DIR}, Server section disabled")
    fill_user_lists()
    redraw_view3d()
    return None


@bpy.app.handlers.persistent
def load_handler(_dummy):
    fill_user_lists()     # a newly opened file starts with an empty list
    ServerStatus.check()  # and the server may have come (or gone) since


def register():
    if load_handler not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(load_handler)
    ServerStatus.check()


def unregister():
    if load_handler in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(load_handler)
    if bpy.app.timers.is_registered(_apply_server_check):
        bpy.app.timers.unregister(_apply_server_check)
