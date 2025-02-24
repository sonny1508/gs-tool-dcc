from zoovendor.Qt import QtWidgets, QtCore


class ListView(QtWidgets.QListView):
    # emits the selection List as items directly from the model and the QMenu at the mouse position
    contextMenuRequested = QtCore.Signal(list, object)

    def __init__(self, parent=None):
        super(ListView, self).__init__(parent=parent)

    def setSupportsRightClick(self, state):
        """Sets whether this list view should support a right click context menu.

        :param state: If True then A right click menu will be created and contextMenuRequested signal \
        will be emitted.

        :type state: bool
        """
        if state:
            self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
            self.customContextMenuRequested.connect(self._contextMenu)
        else:
            self.setContextMenuPolicy(QtCore.Qt.NoContextMenu)

    def _contextMenu(self, position):
        model = self.model()
        if model is None:
            return
        menu = QtWidgets.QMenu(self)
        selectionModel = self.selectionModel()
        selection = [model.itemFromIndex(index) for index in selectionModel.selectedIndexes()]
        self.contextMenuRequested.emit(selection, menu)
        menu.exec_(self.viewport().mapToGlobal(position))

    def closestIndex(self, pos):
        """ Get the closest index based on pos

        :param pos:
        :type pos: :class:`QtCore.QPoint`
        :return:
        :rtype: :class:`QtCore.QModelIndex`
        """
        maxDist = -1
        closest = None
        for index in self.visibleIndices():

            c = self.visualRect(index)
            if c.top() <= pos.y() <= c.bottom():  # Only choose the ones from the same row
                dist = pos.x() - c.center().x()
                if maxDist == -1 or dist < maxDist:
                    closest = index
                    maxDist = dist
        return closest

    def visibleIndices(self, pre=0, post=0):
        """ Gets visible items

        Set extra to 1 or more if you want extra indices at the beginning and at the end. It will only return
        valid indices.

        :param pre: Add extra items behind the currently visible items
        :type pre: int
        :param post: Add extra items after the currently visible items
        :type post: int
        :return: List of indices that are visible plus the pre and post. It only returns valid indices
        :rtype: list of QtCore.QModelIndex
        """
        viewportRect = self.viewport().rect()
        if viewportRect.width() == 0 or viewportRect.height() == 0:
            return
        proxyModel = self.model()
        if not proxyModel:
            return
        proxyStartIndex = self.indexAt(QtCore.QPoint())
        if not proxyStartIndex.isValid():
            return
        startRow = proxyStartIndex.row()


        if startRow < 0:
            proxyStartIndex = proxyModel.index(0, 0)
        elif pre:
            # pre not visible items
            for i in range(startRow-pre, startRow-2):
                proxyIndex = proxyModel.index(i, 0)
                if not proxyIndex.isValid():
                    break
                yield proxyIndex

        yield proxyStartIndex

        # only visible items
        endIndex = proxyStartIndex
        while True:
            sibling = endIndex.sibling(endIndex.row()+1, 0)
            if not sibling.isValid():
                break
            if not viewportRect.intersects(self.visualRect(sibling)):
                break
            endIndex = sibling
            yield endIndex
        if post:
            # post non visible items
            for i in range(endIndex.row() + post, endIndex.row()-1):
                proxyIndex = proxyModel.index(i, 0)
                if not proxyIndex.isValid():
                    break
                yield proxyIndex
