from zoo.libs.maya.mayacommand import mayaexecutor as executor


def resetTransforms(nodes, translate=True, rotate=True, scale=True):
    """Resets all provided node transforms in transform space.

    :param nodes: a list of DagNodes to have their transforms reset
    :type nodes: list[:class:`zoo.libs.maya.zapi.DagNode`]
    :param translate: If True reset the translation channel
    :type translate: bool
    :param rotate: If True reset the rotation channel
    :type rotate: bool
    :param scale: If True reset the scale channel
    :type scale: tuple[float]
    """
    return executor.execute("zoo.nodes.resetTransform", **locals())


def matchTransforms(nodes, translate=True, rotate=True, scale=True):
    return executor.execute("zoo.maya.matchTransforms", **locals())


def matchTransformsBake(nodes, translate=True, rotate=True, scale=True,
                        bakeEveryFrame=False, frameRange=None):
    return executor.execute("zoo.maya.matchTransformsBake", **locals())


def coPlanarAlign(create=False, align=False, metaNode=None, skipEnd=False):
    """Aligns the provided meta node to the closest plane which is attached to the metaNode

    :param create: If True creates a new meta node
    :type create: bool
    :param align: If True align the meta node
    :type align: bool
    :param metaNode: The meta node to align
    :type metaNode: :class:`zoo.libs.maya.meta.coplanar.CoPlanarMeta`
    :param skipEnd: Skip the orient of the last joint in the chain.
    :type skipEnd: bool
    :return: If create is True returns the new meta node, if align is True returns True if successful
    :rtype: bool or :class:`zoo.libs.maya.meta.coplanar.CoPlanarMeta`
    """
    if not align and not create:
        raise ValueError("Either create or align must be True")
    if align and not metaNode:
        raise ValueError("If align is True metaNode must be provided")
    return executor.execute("zoo.maya.planeOrient", **locals())


def orientNodes(nodes,
                primaryAxis,
                secondaryAxis,
                worldUpAxis,
                skipEnd=True):
    """Given the provided nodes each node will be aligned to the next in the list

    For the sake of flexibly in how to apply the rotations depending on
    client workflow and node types, all rotations will be applied directly to
    the world rotations , for joints their joint orient will be reset to zero.


    :param nodes: The full list of nodes from parent to child.
    :type nodes: list[:class:`zapi.DagNode`]
    :param worldUpAxis: The calculated Plane to align all nodes too.
    :type worldUpAxis: :class:`om2.MVector`
    :param primaryAxis: The primary(aim) axis for each node.
    :type primaryAxis: :class:`om2.MVector`
    :param secondaryAxis: The Secondary vector for all the nodes in the chain.
    :type secondaryAxis: :class:`om2.MVector`
    :param skipEnd: If True the last node will not be aligned.
    :type skipEnd: bool
    """
    return executor.execute("zoo.maya.orientNodes", **locals())
