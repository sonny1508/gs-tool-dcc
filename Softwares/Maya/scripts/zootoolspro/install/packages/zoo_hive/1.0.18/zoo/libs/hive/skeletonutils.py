import json

from zoo.libs.hive import constants
from zoo.libs.maya import zapi
from maya import cmds


def cleanSkeletonBeforeExport(rootJoints, constraints=False, onlyHiveAttrs=False):
    """Given a list of root joints loops through all children and purge constraints and clean
    nodes so their compatible with Game engine formats with redundant attributes/namespace.

    :param rootJoints: A list of root joints to search, this function walks all children recursively.
    :type rootJoints: list[:class:`zapi.DagNode`]
    :param constraints: Whether or not the constraints should be deleted.
    :type constraints: bool
    """
    constraintsToRemove = []
    for rootJoint in rootJoints:
        rootJoint.setParent(None)
        cleanNodeForExport(rootJoint, onlyHiveAttrs=onlyHiveAttrs)
        # purge all nodes which don't below in the FBX, fbx exports a flaky so we clean it
        # by simple removing constraints
        for childNode in rootJoint.iterChildren():
            if childNode.hasFn(zapi.kNodeTypes.kConstraint) and not constraints:
                constraintsToRemove.append(childNode.fullPathName())
            else:
                cleanNodeForExport(childNode, onlyHiveAttrs=onlyHiveAttrs)
    if constraintsToRemove:
        cmds.delete(constraintsToRemove)


def cleanNodeForExport(node, onlyHiveAttrs=False):
    """Cleans the node for export by purge hive attributes(id, constraint metadata) and namespace.

    :param node: The maya node to clean
    :type node: :class:`zapi.DagNode`
    """
    # we need to clean namespaces
    node.removeNamespace()
    if not onlyHiveAttrs:
        for source, dest in node.destinations():
            source.lock(False)
            dest.disconnect(source)
    idAttr = node.attribute(constants.ID_ATTR)
    if idAttr is not None:
        idAttr.delete()
    zapi.deleteConstraintMapAttribute(node)
    # print(node.attribute("segmentScaleCompensate"))
    # node.attribute("segmentScaleCompensate").set(1)
    node.setScale((1, 1, 1))
    # print(node.attribute("segmentScaleCompensate").value(),)


def applySkeletalMetaData(rig):
    """Given A rig gather and apply component name,side, type and store it on the joints.

    This meta data is used by :func:`extractSkeletalMetaData` to help convert an existing
    hive joint chain back into the rig.

    .. note::

        A new attribute called "hiveExternalMetaData" will be added to all deform joints.

    :param rig: The rig instance to apply the meta data too.
    :type rig: :class:`rig.Rig`
    """
    # first apply latest meta data so we can recover on import
    for comp in rig.components():
        deform = comp.deformLayer()
        if not deform:
            continue
        data = {
            "name": comp.name(),
            "side": comp.side(),
            "componentType": comp.componentType,
        }
        for jnt in deform.iterJoints():
            data["nodeId"] = jnt.id()
            if not jnt.hasAttribute(constants.HIVE_EXTERNAL_METADATA_ATTR):
                jnt.addAttribute(
                    constants.HIVE_EXTERNAL_METADATA_ATTR,
                    Type=zapi.attrtypes.kMFnDataString,
                    value=json.dumps(data),
                )
            else:
                jnt.attribute(constants.HIVE_EXTERNAL_METADATA_ATTR).set(
                    json.dumps(data)
                )


def extractSkeletalMetaData(joints):
    """Given a set of joints return a dict containing a mapping between the Joint scene node and it's
    metaData.

    Example return structure.

    .. code-block:: json

        {("vchaincomponent", "myCompName", "compSide"): {"jntId": joint}}

    :param joints: The joints to search.
    :type joints: iterable[:class:`api.DagNode`]
    :return: The metadata -> jnt mapping
    :rtype: dict
    """
    data = {}
    for jnt in joints:
        attr = jnt.attribute(constants.HIVE_EXTERNAL_METADATA_ATTR)
        if not attr:
            continue
        stringData = attr.value()
        metaData = json.loads(stringData)
        data.setdefault(
            (metaData["componentType"], metaData["name"], metaData["side"]), {}
        )[metaData["nodeId"]] = jnt
    return data
