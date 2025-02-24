from maya import cmds


def tooltipState():
    """ Get the maya tooltip state

    :return:
    :rtype: bool
    """
    return cmds.help(q=1, popupMode=1)


def setMayaTooltipState(state):
    """ Set the maya state to show the tooltips or not.

    :param state: bool
    :return:
    """
    cmds.evalDeferred("from maya import cmds;cmds.help(popupMode={})".format(str(int(state))))
