from maya import cmds
from zoo.libs.utils import output
from zoo.libs.maya import zapi


def resetNodes(nodes, skipVisibility=True, proxies=True, message=False):
    """Resets all keyable unlocked attributes on given objects to their default values.

    Will filter to the channelBox selection if there is one.

    If from selection will only work on transform nodes. See resetSelection()

    Great for running on a large selection such as all character controls.

    :param nodes: A list of Maya nodes
    :type nodes: list(str)
    :param skipVisibility: Don't reset the visibility attribute
    :type skipVisibility: bool
    :param proxies: Whether to reset proxy attributes.
    :type proxies: bool
    """
    selAttrs = cmds.channelBox('mainChannelBox', q=True, sma=True) or cmds.channelBox('mainChannelBox', q=True,
                                                                                      sha=True)

    def _validResetAttr(attr):
        if selAttrs is not None and attr not in selAttrs:
            return False
        elif attr == "ro" or (skipVisibility and attr == 'v'):
            return False
        return True

    for node in nodes:
        attrs = cmds.listAttr(node, keyable=True, shortNames=True, unlocked=True)
        if not attrs:
            continue
        attrs = [attr for attr in attrs if _validResetAttr(attr)]
        resetAttrs(node, attrs, proxies)

    if message:
        output.displayInfo("Attributes Reset")


def resetAttrs(node, attrs, proxies):
    """Resets all keyable unlocked attributes provided

    :param node: A Maya node
    :type node: str
    :param attrs: A list of attribute names
    :type attrs: list[str]
    :param proxies: Whether to reset proxy attributes.
    :type proxies: bool
    """
    for attr in attrs:
        attrPath = ".".join([node, attr])
        if not cmds.getAttr(attrPath, settable=True):
            continue
        elif not proxies and zapi.plugByName(".".join([node, attr])).isProxy():
            continue
        default = 0
        try:
            default = cmds.attributeQuery(attr, n=node, listDefault=True)
        except RuntimeError:
            pass
        if not isinstance(default, (list,type)):
            default = [default]
        # need to catch because maya will let the default value lie outside an attribute's
        # valid range (ie maya will let you create an attribute with a default of 0, min 5, max 10)
        try:
            cmds.setAttr(attrPath, *default, clamp=True)
        except RuntimeError:
            pass


def resetNode(node, skipVisibility=True):
    """Resets all keyable attributes on a single Maya object to it's default value
    Great for running on a large selection such as all character controls.

    :param skipVisibility: don't reset the visibility attribute
    :type skipVisibility: bool
    """
    return resetNodes([node], skipVisibility=skipVisibility)


def resetSelection(skipVisibility=True, message=True):
    """Resets all keyable attributes on a selection of object to their default value
    Great for running on a large selection such as all character controls.

    :param skipVisibility: don't reset the visibility attribute
    :type skipVisibility: bool
    """
    # all transforms and asset containers(Hive)
    nodes = cmds.ls(selection=True, type=["transform", "network"])
    if not nodes:
        if message:
            output.displayWarning("No Objects Selected, please select the objects to be reset")
        return
    resetNodes(nodes, skipVisibility=skipVisibility, message=message)
