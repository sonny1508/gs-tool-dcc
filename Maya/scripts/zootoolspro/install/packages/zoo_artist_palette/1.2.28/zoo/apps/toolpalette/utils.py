from zoo.libs import iconlib


def iconForItem(menuItem, path=False, iconSize=32, ignoreSeparators=True):
    """Get the icon for the given menuItem.

    :param menuItem: The menu item to get the icon for.
    :type menuItem: :class:`layouts.MenuItem`
    :param path: Whether to return the icon path or the icon itself.
    :type path: bool
    :param iconSize: The size of the icon to return.
    :type iconSize: int
    :param ignoreSeparators: Whether to ignore separators when getting the icon otherwise our internal separator\
    icon will be used.
    :type ignoreSeparators: bool
    :return: The icon path or the icon itself.
    :rtype: str or QtGui.QIcon

    """
    if not ignoreSeparators and menuItem.isSeparator():
        iconName = "separator_shlf"
    else:
        iconName = menuItem.icon
    if not iconName:
        return
    if path:
        return iconlib.iconPathForName(iconName, size=iconSize)

    iconColor = menuItem.iconColor
    if iconColor:
        icon = iconlib.iconColorized(iconName, size=iconSize,
                                     color=iconColor,
                                     overlayName=menuItem.overlayName,
                                     overlayColor=menuItem.overlayColor)
    else:
        icon = iconlib.icon(iconName, size=iconSize)

    if icon is None or icon.isNull():
        return
    return icon
