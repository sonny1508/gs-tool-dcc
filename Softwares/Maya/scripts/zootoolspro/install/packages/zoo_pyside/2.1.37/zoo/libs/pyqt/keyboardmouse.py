import warnings

from zoovendor.Qt import QtWidgets, QtCore, QtGui

# dict of keyBoard special characters which require remapping to other characters ie. ! == 1
SPECIAL_KEYS = {
    QtCore.Qt.Key.Key_Exclam: QtCore.Qt.Key.Key_1,
    QtCore.Qt.Key.Key_QuoteDbl: QtCore.Qt.Key_Apostrophe,
    QtCore.Qt.Key.Key_NumberSign: QtCore.Qt.Key_3,
    QtCore.Qt.Key.Key_Dollar: QtCore.Qt.Key_4,
    QtCore.Qt.Key.Key_Percent: QtCore.Qt.Key_5,
    QtCore.Qt.Key.Key_Ampersand: QtCore.Qt.Key_7,
    QtCore.Qt.Key.Key_ParenLeft: QtCore.Qt.Key_9,
    QtCore.Qt.Key.Key_ParenRight: QtCore.Qt.Key_0,
    QtCore.Qt.Key.Key_Asterisk: QtCore.Qt.Key_8,
    QtCore.Qt.Key.Key_Plus: QtCore.Qt.Key_Equal,
    QtCore.Qt.Key.Key_Colon: QtCore.Qt.Key_Semicolon,
    QtCore.Qt.Key.Key_Less: QtCore.Qt.Key_Comma,
    QtCore.Qt.Key.Key_Greater: QtCore.Qt.Key_Period,
    QtCore.Qt.Key.Key_Question: QtCore.Qt.Key_Slash,
    QtCore.Qt.Key.Key_At: QtCore.Qt.Key_2,
    QtCore.Qt.Key.Key_AsciiCircum: QtCore.Qt.Key_6,
    QtCore.Qt.Key.Key_Underscore: QtCore.Qt.Key_Minus,
    QtCore.Qt.Key.Key_BraceLeft: QtCore.Qt.Key_BracketLeft,
    QtCore.Qt.Key.Key_Bar: QtCore.Qt.Key_Backslash,
    QtCore.Qt.Key.Key_BraceRight: QtCore.Qt.Key_BracketRight,
    QtCore.Qt.Key.Key_AsciiTilde: QtCore.Qt.Key_QuoteLeft,
}


def ctrlShiftMultiplier(shiftMultiply=5.0, ctrlMultiply=0.2, altMultiply=1.0):
    """For offset functions multiply (shift) and minimise if (ctrl) is held down
    If (alt) then call the reset option

    :return multiplier: multiply value, 0.2 if ctrl 5.0 if shift 1.0 if None
    :rtype multiplier: float
    :return reset: Reset becomes True while resetting for alt
    :rtype reset: bool
    """
    modifiers = QtWidgets.QApplication.keyboardModifiers()
    if modifiers == QtCore.Qt.ShiftModifier:  # usually accelerate * 5.0
        return shiftMultiply, False
    elif modifiers == QtCore.Qt.ControlModifier:  # usually decelerate * 0.2
        return ctrlMultiply, False
    elif (
        modifiers == QtCore.Qt.AltModifier
    ):  # usually decelerate * 1.0 and reset is True
        return altMultiply, True
    return 1.0, False  # regular click


def eventKeySequence(
    event, includeShiftForSpecialCharacters=False, acceptedShiftCombinations=None
):
    """Returns the QKeySequence from the KeyEvent

    :param event:
    :type event: :class:`QtGui.QKeyEvent`
    :param includeShiftForSpecialCharacters: If True then special characters like ! which map to another key \
    i.e. ! maps to shift+1 then only return the sequence "!" not shift+1
    :type includeShiftForSpecialCharacters: bool
    :param acceptedShiftCombinations: A list of keys which are accepted to be returned with the shift modifier.
    :type acceptedShiftCombinations: list[QtCore.Qt.Key]
    :return:
    :rtype: :class:`QtGui.QKeySequence`
    """
    key = QtCore.Qt.Key(event.key())

    if key == QtCore.Qt.Key_unknown:
        warnings.warn("Unknown key from a macro")
        return QtGui.QKeySequence()

    # the user have clicked just and only the special keys Ctrl, Shift, Alt, Meta.
    if (
        key == QtCore.Qt.Key_Control
        or key == QtCore.Qt.Key_Shift
        or key == QtCore.Qt.Key_Alt
        or key == QtCore.Qt.Key_Meta
    ):
        return QtGui.QKeySequence()

    # check for a combination of user clicks
    modifiers = event.modifiers()
    mods = QtCore.Qt.NoModifier
    if modifiers & QtCore.Qt.ShiftModifier:
        acceptedShiftCombinations = acceptedShiftCombinations or []

        isSpecialKey = SPECIAL_KEYS.get(key) is not None
        if not isSpecialKey:
            mods |= QtCore.Qt.SHIFT
        elif includeShiftForSpecialCharacters and isSpecialKey:
            mods |= QtCore.Qt.SHIFT
        elif acceptedShiftCombinations and key in acceptedShiftCombinations:
            # if it's a special characters i.e. shift+1 or !
            # then just return the special character without the shift modifier i.e. !
            mods |= QtCore.Qt.SHIFT

    if modifiers & QtCore.Qt.ControlModifier:
        mods |= QtCore.Qt.CTRL
    if modifiers & QtCore.Qt.AltModifier:
        mods |= QtCore.Qt.ALT
    if modifiers & QtCore.Qt.MetaModifier:
        mods |= QtCore.Qt.META
    seq = QtGui.QKeySequence(key | mods)
    return seq
