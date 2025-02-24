import json

from zoo.libs.hive import constants
from zoo.libs.maya import zapi
from zoovendor import six


def traverseDefinitionLayerDag(layerDef):
    """Depth first search recursive generator function which walks the layer definition DAG nodes.

    :param layerDef:
    :type layerDef: :class:`zoo.libs.hive.base.definition.definitionlayers.LayerDef`
    :return:
    :rtype: :class:`dict` or :class:`zoo.libs.hive.base.definition.definitionnodes.TransformDefinition`
    """

    def _nodeIter(n):
        for child in iter(n.get("children", [])):
            yield child
            for i in _nodeIter(child):
                yield i

    for node in iter(layerDef.get(constants.DAG_DEF_KEY, [])):
        yield node
        for ch in _nodeIter(node):
            yield ch


def parseRawDefinition(definitionData):
    translatedData = {}
    for k, v in definitionData.items():
        if not v:
            continue
        if k == "info":
            translatedData.update(json.loads(v))
            continue
        elif k == constants.SPACE_SWITCH_DEF_KEY:
            translatedData[constants.SPACE_SWITCH_DEF_KEY] = json.loads(v)
            continue
        dag, settings, metaData = (v[constants.DAG_DEF_KEY] or "[]",
                                   v[constants.SETTINGS_DEF_KEY] or ("{}" if k == constants.RIGLAYER_DEF_KEY else "[]"),
                                   v[constants.METADATA_DEF_KEY] or "[]")
        translatedData[k] = {constants.DAG_DEF_KEY: json.loads(dag),
                             constants.SETTINGS_DEF_KEY: json.loads(settings),
                             constants.METADATA_DEF_KEY: json.loads(metaData)}
    return translatedData

def offsetGuideShapeCVs(shapes, oldMatrix, newMatrix):
    """Offsets the shape definitions by the newMatrix

    .. note: Math is pointPosition * oldMatrix * newMatrix
    .. note: Modifies the shape in place.

    :param shapes: The list of shape data.
    :type shapes: dict[dict]
    :param oldMatrix:  The current inverse worldMatrix.
    :type oldMatrix: :class:`zapi.Matrix`
    :param newMatrix: The new worldMatrix
    :type newMatrix: :class:`zapi.Matrix`
    """
    if isinstance(shapes, six.string_types):
        return

    for shape in shapes.values():
        cvs = shape["cvs"]
        for index in range(len(cvs)):
            cvOffset = zapi.Point(cvs[index]) * oldMatrix * newMatrix
            cvs[index] = list(cvOffset)
