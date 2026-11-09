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

# A scroll bar that reads against Maya's greys, whose own is easy to miss.
SCROLL_TRACK = "#2b2b2b"
SCROLL_HANDLE = "#a0a0a0"

# A section's header: darker than Maya's window grey (#444444), where its buttons
# are lighter (#5d5d5d), so that a header never reads as one more button.
SECTION_HEADER = "#383838"


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


def toggle_style(colour=STUDIO_ORANGE):
    """Style sheet for a checkable QPushButton that switches something on, like a
    viewport view: Maya's grey while off, filled with `colour` while on, so that
    nobody forgets it is on.

    The border is what makes Qt paint the fill: given a background colour alone,
    a style may draw its own pressed-in button over it."""
    return (
        "QPushButton:checked {{ background-color: {base}; color: {text}; font-weight: bold;"
        " border: 1px solid {pressed}; border-radius: 2px; }}"
        "QPushButton:checked:hover {{ background-color: {hover}; }}"
        "QPushButton:checked:pressed {{ background-color: {pressed}; }}"
    ).format(base=colour, text=BUTTON_TEXT,
             hover=mix(colour, "#ffffff", 0.15),
             pressed=mix(colour, "#000000", 0.2))


def style_toggle(button, colour=STUDIO_ORANGE):
    """Make a checkable QPushButton fill with a studio colour while on. Returns the button."""
    button.setStyleSheet(toggle_style(colour))
    return button


def section_header_style():
    """Style sheet for a section's header, a QPushButton and any QToolButton beside it.

    It reads as a title. The hover and pressed looks are there for a header that
    can also be clicked; one that can't should ignore the mouse.
    """
    return (
        "QPushButton, QToolButton {{ background-color: {base}; border: none; }}"
        "QPushButton {{ text-align: left; padding: 3px 8px; }}"
        "QPushButton:hover, QToolButton:hover {{ background-color: {hover}; }}"
        "QPushButton:pressed, QToolButton:pressed {{ background-color: {pressed}; }}"
    ).format(base=SECTION_HEADER,
             hover=mix(SECTION_HEADER, "#ffffff", 0.15),
             pressed=mix(SECTION_HEADER, "#000000", 0.2))


def style_section_header(widget):
    """Make a button into part of a section's header. Returns the widget."""
    widget.setStyleSheet(section_header_style())
    return widget


def scrollbar_style():
    """Style sheet for a vertical QScrollBar that artists can't miss."""
    return (
        "QScrollBar:vertical {{ background: {track}; width: 16px; margin: 0; }}"
        "QScrollBar::handle:vertical {{ background: {handle}; min-height: 40px;"
        " margin: 2px; border-radius: 3px; }}"
        "QScrollBar::handle:vertical:hover {{ background: {hover}; }}"
        "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical"
        " {{ height: 0; border: none; background: none; }}"
        "QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}"
    ).format(track=SCROLL_TRACK, handle=SCROLL_HANDLE,
             hover=mix(SCROLL_HANDLE, "#ffffff", 0.3))


def style_scrollbar(scroll_bar):
    """Make a vertical QScrollBar stand out. Returns the scroll bar."""
    scroll_bar.setStyleSheet(scrollbar_style())
    return scroll_bar
