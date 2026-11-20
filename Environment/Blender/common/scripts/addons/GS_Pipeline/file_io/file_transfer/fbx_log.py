"""GS File Transfer: what each import / export ran with, printed to the system console.

For us, not artists: the file, every setting handed to Blender's FBX operator
(``*`` marks one that differs from the FBX dialog's factory default), and the
steps this tool adds around the FBX call that a manual File > Export / Import
doesn't do (applying scale / rotation, merging materials, auto smooth). That's what to read when a transferred file differs from a manual
one. The FBX add-on's own messages land in the same console
(Window > Toggle System Console). The panel still shows only the one-line result.
"""
from __future__ import annotations

import datetime
import os

PREFIX = "[GS File Transfer]"


def log(message=""):
    print(f"{PREFIX} {message}" if message else "")


def log_header(title):
    log("=" * 70)
    log(title)


def log_file(path):
    try:
        stat = os.stat(path)
    except OSError:
        log(f"  File: {path} (not there)")
        return
    written = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    log(f"  File: {path} ({stat.st_size:,} bytes, written {written})")


def _text(value):
    if isinstance(value, (set, frozenset)):
        return "{" + ", ".join(sorted(value)) + "}"
    if isinstance(value, float):
        return f"{value:g}"
    return str(value)


def _factory_default(operator, key):
    """The FBX operator's own default for ``key``, or None when it can't be read."""
    try:
        prop = operator.get_rna_type().properties[key]
    except (AttributeError, KeyError, RuntimeError):
        return None
    if getattr(prop, "is_enum_flag", False):
        return set(prop.default_flag)
    return getattr(prop, "default", None)


def log_settings(label, operator, settings):
    """Every keyword handed to ``operator``, ``*`` on those that differ from its factory default."""
    log(f"  {label} settings (* = differs from the FBX dialog's factory default):")
    for key in sorted(settings):
        value = settings[key]
        default = _factory_default(operator, key)
        changed = default is not None and _text(default) != _text(value)
        suffix = f"   (default {_text(default)})" if changed else ""
        log(f"   {'*' if changed else ' '} {key:<34} {_text(value)}{suffix}")
