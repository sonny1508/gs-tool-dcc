# -*- coding: utf-8 -*-
"""
gs_style - the Glenda Studio colour scheme for tool windows.

The one place the studio colours are defined. Tools import this instead of
copying hex codes, so a change here reaches every window. It has no Qt import -
it only builds style sheet strings and colour values - so it works the same
under PySide2 and PySide6, and in maya.cmds windows through rgb().

    import gs_style
    gs_style.style_button(check_button, gs_style.STUDIO_RED)
    gs_style.style_button(fix_button, gs_style.STUDIO_ORANGE)

Which colour goes where is in Docs/Maya_UI_Guidelines.md, section 4.
"""

# Primary action buttons, in reading order: the first red, the second orange.
STUDIO_RED = "#6b0914"
STUDIO_ORANGE = "#f6921e"
BUTTON_TEXT = "#ffffff"

# Log and status text, by level. Plain information keeps the default colour.
LOG_COLOURS = {"ok": "#7ec87e", "warn": "#e0b64c", "error": "#e06c6c"}

# Maya's own button grey, which a disabled studio button fades towards.
_DISABLED_BASE = "#444444"
_DISABLED_TEXT = "#8a8a8a"


def _channels(colour):
    return [int(colour[i:i + 2], 16) for i in (1, 3, 5)]


def mix(colour, other, amount):
    """`colour` moved `amount` (0-1) of the way to `other`, both '#rrggbb'."""
    return "#" + "".join("{:02x}".format(int(round(a + (b - a) * amount)))
                         for a, b in zip(_channels(colour), _channels(other)))


def rgb(colour):
    """`colour` as an (r, g, b) tuple in 0-1, for maya.cmds backgroundColor=."""
    return tuple(channel / 255.0 for channel in _channels(colour))


def button_style(colour):
    """Style sheet for a QPushButton filled with `colour`, with hover, pressed and disabled looks."""
    return (
        "QPushButton {{ background-color: {base}; color: {text}; font-weight: bold; }}"
        "QPushButton:hover {{ background-color: {hover}; }}"
        "QPushButton:pressed {{ background-color: {pressed}; }}"
        "QPushButton:disabled {{ background-color: {disabled}; color: {disabled_text}; }}"
    ).format(base=colour, text=BUTTON_TEXT,
             hover=mix(colour, "#ffffff", 0.15),
             pressed=mix(colour, "#000000", 0.2),
             disabled=mix(colour, _DISABLED_BASE, 0.75),
             disabled_text=_DISABLED_TEXT)


def style_button(button, colour):
    """Fill a QPushButton with a studio colour. Returns the button."""
    button.setStyleSheet(button_style(colour))
    return button
