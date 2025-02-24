from operator import itemgetter
from itertools import groupby
from zoovendor.Qt import QtCore


def groupModelRowIndexes(indexes):
    for k, g in groupby(enumerate(indexes), lambda x: x[0] - x[1].row()):
        yield list(map(itemgetter(1), g))


def dataModelFromProxyModel(model):
    """Returns the root source data model from the provided model.
    This is used when you have a proxyModel stack and you want to root source Model.

    :param model: The proxy Model to walk.
    :type model: QtCore.QAbstractProxyModel
    :return: The root data item model.
    :rtype: :class:`QtCore.QAbstractItemModel`
    """
    if model is None:
        return
    currentModel = model
    while isinstance(currentModel, QtCore.QAbstractProxyModel):
        currentModel = currentModel.sourceModel()
        if not currentModel:
            return
    return currentModel


def dataModelIndexFromIndex(modelIndex):
    """Returns the index from the root data model by walking the proxy model stack if present.

    If the provided modelIndex is not from a proxyModel then it will be immediately returned.

    :param modelIndex: The Qt Model index from the proxyModel.
    :type modelIndex: :class:`QtCore.QModelIndex`
    :rtype: tuple[:class:`QtCore.QModelIndex`, :class:`QtCore.QAbstractItemModel`]
    """
    dataModel = modelIndex.model()
    modelIndexMapped = modelIndex
    while isinstance(dataModel, QtCore.QAbstractProxyModel):
        modelIndexMapped = dataModel.mapToSource(modelIndexMapped)
        if not modelIndexMapped.isValid():
            return modelIndexMapped
        dataModel = modelIndexMapped.model()
    return modelIndexMapped, dataModel
