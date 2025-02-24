import contextlib

from maya import cmds
from zoo.libs.maya.qt import mayaui
from zoo.libs.maya.api import nodes as apiNodes
from zoo.libs.maya.utils import mayaenv
from zoovendor.Qt import QtWidgets, QtCore

ALIGN_LEFT = 0
ALIGN_RIGHT = 1
ALIGN_TOP = 2
ALIGN_BOTTOM = 3
ALIGN_CENTER_X = 4
ALIGN_CENTER_Y = 5
ALIGN_DIAGONALLY_LEFT_RIGHT = 6
ALIGN_DIAGONALLY_RIGHT_LEFT = 7


def getPrimaryNodeEditor():
    """Find and return the name of the primary node editor if it exists.

    :return: The node editor name
    :rtype: str
    """
    allNEs = cmds.getPanel(scriptType="nodeEditorPanel")
    for oneNE in allNEs:
        ned = oneNE + "NodeEditorEd"
        if cmds.nodeEditor(ned, query=True, primary=True):
            return ned
    return ""


def createNodeEditor():
    """Creates(opens) the maya node editor.

    :return: Returns the NodeEditorWrapper object linked to the current node editor.
    :rtype: :class:`NodeEditorWrapper`
    """
    cmds.NodeEditorWindow()
    return NodeEditorWrapper()


def currentNodeEditorPanel():
    """Returns the currently active node editor panel if any.

    :return: The maya node editor panel name
    :rtype: str
    """
    currentPanel = cmds.getPanel(withFocus=True)
    if not currentPanel:
        return ""
    panelType = cmds.getPanel(typeOf=currentPanel)
    if panelType == "scriptedPanel" and cmds.scriptedPanel(currentPanel, query=True, type=True) == "nodeEditorPanel":
        return currentPanel
    return ""


def currentNodeEditor():
    """Returns the currently active nodeEditor name if any.

    .. note::
        This function should be used when using :class:`NodeEditorWrapper` if you want to work
        with the current active Node Editor.

    .. note::
        This is not the same :func:`getPrimaryEditor` which doesn't depend on user focus.

    :return: The maya node editor path
    :rtype: ""
    """
    currentPanel = currentNodeEditorPanel()
    if not currentPanel:
        return ""
    return "{}NodeEditorEd".format(currentPanel)


class NodeEditorWrapper(QtCore.QObject):
    """This class wraps Autodesk Maya's node editor and provides Qt-related functions for working with it.
    """
    #  An attribute view mode that displays the most important attributes of the nodes.
    ATTR_VIEW_SIMPLE = 0
    # An attribute view mode that displays only the attributes that are connected to other attributes.
    ATTR_VIEW_CONNECTED = 1
    # An attribute view mode that displays all attributes of the nodes.
    ATTR_VIEW_ALL = 2
    # An attribute view mode that allows the user to customize which attributes are displayed.
    ATTR_VIEW_CUSTOM = 3
    # The default spacing between items when aligning them.
    ITEM_ALIGN_SPACING = 20
    # A mapping of attribute view mode constants to their corresponding string representation in Maya.
    _viewModeMap = {
        ATTR_VIEW_SIMPLE: "simple",
        ATTR_VIEW_CONNECTED: "connected",
        ATTR_VIEW_ALL: "all",
        ATTR_VIEW_CUSTOM: "custom"
    }

    @staticmethod
    def nodeEditorAsQtWidgets(nodeEditor):
        """Returns the node editor widget, graphics view, and graphics scene as Qt widgets.

        :param nodeEditor: The node editor as a Maya or Qt object.
        :type nodeEditor: str
        :return: The node editor widget, graphics view, and graphics scene as Qt widgets.
        :rtype: Tuple[:class:`QtWidgets.QWidget`, :class:`QtWidgets.QGraphicsView`, :class:`QtWidgets.QGraphicsScene`]
        """
        nodeEdPane = mayaui.toQtObject(nodeEditor)
        # get the tab layout which is a QStackedLayout
        stack = nodeEdPane.findChild(QtWidgets.QStackedLayout)  # type: QtWidgets.QStackedLayout
        view = stack.currentWidget().findChild(QtWidgets.QGraphicsView)
        return nodeEdPane, view, view.scene()

    @staticmethod
    def itemsRect(items):
        """Returns the bounding rectangle that encloses the specified graphics items.

        :param items: The list of graphics items.
        :type items: List[:class:`QtWidgets.QGraphicsItem`]
        :return: The bounding rectangle that encloses the graphics items.
        :rtype: :class:`QtCore.QRect`
        """
        sourceRect = QtCore.QRect()

        for item in items:
            sourceRect = sourceRect.united(QtCore.QRect(*item.sceneBoundingRect().getRect()))
        return sourceRect

    def __init__(self, nodeEditor=None):
        super(NodeEditorWrapper, self).__init__()
        if not nodeEditor:
            self.mayaName = getPrimaryNodeEditor()
            self.setObjectName(self.mayaName)
            if not self.mayaName:
                self.editor, self.view, self.scene = None, None, None
            else:
                self.editor, self.view, self.scene = NodeEditorWrapper.nodeEditorAsQtWidgets(self.mayaName)
        else:
            self.setObjectName(nodeEditor)
            self.mayaName = nodeEditor
            self.editor, self.view, self.scene = NodeEditorWrapper.nodeEditorAsQtWidgets(nodeEditor)

    def exists(self):
        """Returns whether a Node Editor with the object's name exists in Maya.

        :return: True if a Node Editor with the object's name exists, False otherwise.
        :type: bool
       """
        objName = self.objectName()
        if objName:
            return cmds.nodeEditor(objName, exists=True)
        return False

    def show(self):
        """Shows the Node Editor in Maya.
        """
        cmds.NodeEditorWindow()
        self.editor, self.view, self.scene = NodeEditorWrapper.nodeEditorAsQtWidgets(getPrimaryNodeEditor())

    def selectedNodeItems(self):
        """Returns the selected node items in the Node Editor.

        :return: A list of the selected node items.
        :rtype: List[:class:`QtWidgets.QGraphicsItem`]
        """
        # check against type instead of isinstance since graphicsPathItem inherents from QGraphicsItem
        return [i for i in self.scene.selectedItems() if type(i) == QtWidgets.QGraphicsItem]

    def selectedConnections(self):
        """Returns the selected connections in the Node Editor.

        :return: A list of the selected connections.
        :rtype: List[:class:`QtWidgets.QGraphicsPathItem`]
        """
        return [i for i in self.scene.selectedItems() if type(i) == QtWidgets.QGraphicsPathItem]

    def addNodes(self, nodes):
        """Adds a list of nodes to the current node editor

        :param nodes: a list of maya mobject representing valid nodes
        :type nodes: list(:class:`om2.MObject`)
        """

        for n in nodes:
            cmds.nodeEditor(self.objectName(), addNode=apiNodes.nameFromMObject(n), edit=True)

    def addNodesOnCreate(self):
        """
        Returns whether new nodes are added to the Node Editor when they are created.

        :return: True if new nodes are added to the Node Editor when they are created, \
        False otherwise.
        :rtype: bool
        """
        return cmds.nodeEditor(self.objectName(), addNewNodes=True, query=True)

    def setAddNodesOnCreate(self, state):
        """
        Sets whether new nodes are added to the Node Editor when they are created.

        :param state: True if new nodes should be added to the Node Editor when they are created,\
        False otherwise.
        :type state: bool
        """
        return cmds.nodeEditor(self.objectName(), addNewNodes=state, edit=True)

    def setNodeAttributeDisplay(self, viewMode):
        """Sets either the currently selected node or all viewed nodes attribute display to one of the follow
        states,ATTR_VIEW_SIMPLE, ATTR_VIEW_CONNECTED, ATTR_VIEW_ALL and ATTR_VIEW_CUSTOM.

        :param viewMode: View mode based on NodeEditorWrapper.VIEW_MODE_# .
        :type viewMode: int
        """
        mode = self._viewModeMap.get(viewMode)
        assert mode is not None, "ViewMode must be one of the NodeEditorWrapper.ATTR_VIEW_# constants"
        cmds.nodeEditor(self.mayaName, nodeViewMode=mode, edit=True)

    def graphDownstreamFromSelection(self):
        """This Graphs the downstream nodes from the currently selected nodes.
        """
        cmds.nodeEditor(self.mayaName, edit=True, rootsFromSelection=True, downstream=True)

    def itemTypeUnderCursor(self):
        """
        Returns the type of item under the cursor in the Node Editor.

        :return: The type of item under the cursor.
        :rtype: str
        """
        return cmds.nodeEditor(self.mayaName, feedbackType=True, q=True)

    def plugUnderCursor(self):
        """Returns the plug under the cursor in the Node Editor.

        :return: The plug under the cursor.
        :rtype: str
        """
        return cmds.nodeEditor(self.mayaName, feedbackPlug=True, query=True)

    def graphDownstreamFromPlug(self, plug):
        """Graphs the nodes downstream from the specified plug in the Node Editor.

        :param plug: The plug to graph downstream from.
        :type plug: str
        """
        # outgoing connections could obviously be changed to incoming connections, ...
        outConnections = cmds.listConnections(plug, source=True, destination=False, skipConversionNodes=True) or []
        outConnections.extend(
            cmds.listConnections(plug, source=False, destination=True, skipConversionNodes=False) or [])
        outConnections = list(set(outConnections))  # deduplicate
        if outConnections:
            with self.connectedGraphingModeContext():
                cmds.nodeEditor(self.mayaName, addNode=outConnections, layout=False, edit=True)
        else:
            cmds.warning("Attribute '{}' has no outgoing connections.".format(plug))

    def graphUpstreamFromPlug(self, plug):
        """Graphs the nodes upstream from the specified plug in the Node Editor.

        :param plug: The plug to graph upstream from.
        :type plug: str
        """
        # outgoing connections could obviously be changed to incoming connections, ...
        outConnections = cmds.listConnections(plug, source=True, destination=False, skipConversionNodes=True) or []
        outConnections.extend(
            cmds.listConnections(plug, source=True, destination=False, skipConversionNodes=False) or [])
        outConnections = list(set(outConnections))  # deduplicate
        if outConnections:
            with self.connectedGraphingModeContext():
                cmds.nodeEditor(self.mayaName, addNode=outConnections, layout=False, edit=True)
        else:
            cmds.warning("Attribute '{}' has no outgoing connections.".format(plug))

    @contextlib.contextmanager
    def connectedGraphingModeContext(self):
        """A context manager that temporarily disables connected graphing mode in the Node Editor.
        """
        if mayaenv.mayaVersion() < 2023:  # connectedGraphingMode was added in 2023
            yield
        else:
            state = cmds.nodeEditor(self.mayaName, connectedGraphingMode=True, query=True)
            cmds.nodeEditor(self.mayaName, connectedGraphingMode=False, edit=True)
            try:
                yield
            finally:
                if state:
                    cmds.nodeEditor(self.mayaName, connectedGraphingMode=state, edit=True)

    def alignLeft(self, items=None):
        """Aligns a list of QGraphicsItems to the left-most x position.

        :param items: The list of QGraphicsItems to align. If not specified, the selected \
        node items will be used.
        :type items:  List[QGraphicsItem]
        """
        items = items or self.selectedNodeItems()
        xPos = min([i.x() for i in items])

        alignItemsToXPos(items, xPos, NodeEditorWrapper.ITEM_ALIGN_SPACING)

    def alignRight(self, items=None):
        """Aligns a list of QGraphicsItems to the left-most x position.

        :param items: The list of QGraphicsItems to align. If not specified, the selected \
        node items will be used.
        :type items:  List[QGraphicsItem]
        """
        items = items or self.selectedNodeItems()
        xPos = max([i.pos().x() for i in items])
        alignItemsToXPos(items, xPos, NodeEditorWrapper.ITEM_ALIGN_SPACING)

    def alignTop(self, items):
        """Aligns a list of QGraphicsItems to the top-most y position.

        :param items: The list of QGraphicsItems to align. If not specified, the selected \
        node items will be used.
        :type items:  List[QGraphicsItem]
        """
        items = items or self.selectedNodeItems()
        yPos = min([i.pos().y() for i in items])
        alignItemsToYPos(items, yPos, NodeEditorWrapper.ITEM_ALIGN_SPACING)

    def alignBottom(self, items):
        """Aligns a list of QGraphicsItems to the bottom-most y position.

        :param items: The list of QGraphicsItems to align. If not specified, the selected \
        node items will be used.
        :type items:  List[QGraphicsItem]
        """
        items = items or self.selectedNodeItems()
        yPos = max([i.pos().y() for i in items])
        alignItemsToYPos(items, yPos, NodeEditorWrapper.ITEM_ALIGN_SPACING)

    def alignCenterX(self, items):
        """Aligns a list of QGraphicsItems to the center x position.

        :param items: The list of QGraphicsItems to align. If not specified, the selected \
        node items will be used.
        :type items:  List[QGraphicsItem]
        """
        items = items or self.selectedNodeItems()
        rect = NodeEditorWrapper.itemsRect(items)
        center = rect.center()
        alignItemsToXPos(items, center.x(), NodeEditorWrapper.ITEM_ALIGN_SPACING)

    def alignCenterY(self, items):
        """Aligns a list of QGraphicsItems to the center y position.

        :param items: The list of QGraphicsItems to align. If not specified, the selected \
        node items will be used.
        :type items:  List[QGraphicsItem]
        """
        items = items or self.selectedNodeItems()
        rect = NodeEditorWrapper.itemsRect(items)
        center = rect.center()
        alignItemsToYPos(items, center.y(), NodeEditorWrapper.ITEM_ALIGN_SPACING)

    def alignItemsDiagonallyLeftToRight(self, items=None):
        """Aligns a list of QGraphicsItems in a diagonal line from left to right,
        distributing them based on their bounding rectangles and a specified
        spacing value to prevent overlap. The x position of each item is set to
        half the width of the previous item.

        :param items: The list of QGraphicsItems to align. If not specified, the selected \
        node items will be used.
        :type items:  List[QGraphicsItem]
        """
        items = items or self.selectedNodeItems()

        alignItemsDiagonallyLeftToRight(items, NodeEditorWrapper.ITEM_ALIGN_SPACING)

    def alignItemsDiagonallyRightToLeft(self, items=None):
        """Aligns a list of QGraphicsItems in a diagonal line from right to left,
        distributing them based on their bounding rectangles and a specified
        spacing value to prevent overlap. The x position of each item is set to
        half the width of the previous item.

        :param items: The list of QGraphicsItems to align. If not specified, the selected \
        node items will be used.
        :type items:  List[QGraphicsItem]
        """
        items = items or self.selectedNodeItems()

        alignItemsDiagonallyRightToLeft(items, NodeEditorWrapper.ITEM_ALIGN_SPACING)


@contextlib.contextmanager
def disableNodeEditorAddNodeContext():
    """Context manager which disables the current nodeEditors "Add to graph on create" which slows the maya
    down alot. So this function temporarily disables it.

    """
    editor = getPrimaryNodeEditor()
    state = False
    ed = None
    if editor:
        ed = NodeEditorWrapper(editor)
        state = ed.addNodesOnCreate()
        if state:
            ed.setAddNodesOnCreate(False)
    yield
    if state:
        ed.setAddNodesOnCreate(state)


def alignItemsToXPos(items, xPos, spacing=0):
    """Aligns a list of QGraphicsItems to a given x position, distributing them
    along the yaxis based on their bounding rectangles and a specified spacing
    value to prevent overlap.

    :param items: The list of QGraphicsItems to align.
    :type items: List[:class:`QtWidgets.QGraphicsItem`]
    :param xPos: The x position to align the items to.
    :type xPos: float
    :param spacing: The spacing between the items. Default is 0.
    :type spacing: float
    """
    # Sort the items by their y position

    sortedItemsByHeight = sorted(items, key=lambda item: item.y())
    # Set the y position of each item based on its bounding rectangle
    yPos = min(items, key=lambda item: item.y()).y()
    for item in sortedItemsByHeight:
        item.setPos(xPos, yPos)
        yPos += item.boundingRect().height() + spacing


def alignItemsToYPos(items, yPos, spacing=0):
    """Aligns a list of QGraphicsItems to a given y position, distributing them
    along the xAxis based on their bounding rectangles and a specified spacing
    value to prevent overlap.

    :param items: The list of QGraphicsItems to align.
    :type items: List[:class:`QtWidgets.QGraphicsItem`]
    :param yPos: The y position to align the items to.
    :type yPos: float
    :param spacing: The spacing between the items. Default is 0.
    :type spacing: float
    """
    # Sort the items by their x position
    items.sort(key=lambda item: item.x())

    # Set the x position of each item based on its bounding rectangle
    xPos = min(item.x() for item in items)
    for item in items:
        item.setPos(xPos, yPos)
        xPos += item.boundingRect().width() + spacing


def alignItemsDiagonallyLeftToRight(items, spacing=0):
    """Aligns a list of QGraphicsItems diagonally, centering the distribution around
    the average X and Y of the total bounding box of all items, and distributing
    them diagonally based on their bounding rectangles and a specified spacing
    value to prevent overlap.

    :param items: The list of QGraphicsItems to align.
    :type items: List[:class:`QtWidgets.QGraphicsItem`]
    :param spacing: The spacing between the items. Default is 0.
    :type spacing: float
    """
    # Calculate the total bounding box of all items
    total_bounding_rect = items[0].boundingRect()
    for item in items[1:]:
        total_bounding_rect = total_bounding_rect.united(item.boundingRect())

    # Calculate the center point of the bounding box
    center_point = total_bounding_rect.center()

    # Sort the items by their height and width in reverse order
    sortedItemsBySize = sorted(items, key=lambda item: (item.boundingRect().height(), item.boundingRect().width()), reverse=True)

    # Calculate the slope of the diagonal line
    num_items = len(items)
    if num_items > 1:
        last_item = sortedItemsBySize[-1]
        last_item_top_left = last_item.boundingRect().topLeft()
        first_item = sortedItemsBySize[0]
        first_item_bottom_right = first_item.boundingRect().bottomRight()
        diagonal_slope = (last_item_top_left.y() - first_item_bottom_right.y()) / (first_item_bottom_right.x() - last_item_top_left.x())
    else:
        diagonal_slope = 0

    # Calculate the starting position of the distribution based on the center point
    start_x = center_point.x() + (total_bounding_rect.width() / 2)
    start_y = center_point.y() - (total_bounding_rect.height() / 2)

    # Set the position of each item diagonally
    x_pos = start_x
    y_pos = start_y
    for item in sortedItemsBySize:
        item.setPos(x_pos, y_pos)
        x_pos -= item.boundingRect().width() + spacing
        y_pos += diagonal_slope * (item.boundingRect().width() + spacing)


def alignItemsDiagonallyRightToLeft(items, spacing=0):
    """Aligns a list of QGraphicsItems diagonally, centering the distribution around
    the average X and Y of the total bounding box of all items, and distributing
    them diagonally based on their bounding rectangles and a specified spacing
    value to prevent overlap.

    :param items: The list of QGraphicsItems to align.
    :type items: List[:class:`QtWidgets.QGraphicsItem`]
    :param spacing: The spacing between the items. Default is 0.
    :type spacing: float
    """
    # Calculate the total bounding box of all items
    total_bounding_rect = items[0].boundingRect()
    for item in items[1:]:
        total_bounding_rect = total_bounding_rect.united(item.boundingRect())

    # Calculate the center point of the bounding box
    center_point = total_bounding_rect.center()

    # Sort the items by their height and width in reverse order
    sortedItemsBySize = sorted(items, key=lambda item: (item.boundingRect().height(), item.boundingRect().width()), reverse=True)

    # Calculate the slope of the diagonal line
    num_items = len(items)
    if num_items > 1:
        last_item = sortedItemsBySize[-1]
        last_item_top_right = last_item.boundingRect().topRight()
        first_item = sortedItemsBySize[0]
        first_item_bottom_left = first_item.boundingRect().bottomLeft()
        diagonal_slope = (first_item_bottom_left.y() - last_item_top_right.y()) / (last_item_top_right.x() - first_item_bottom_left.x())
    else:
        diagonal_slope = 0

    # Calculate the starting position of the distribution based on the center point
    start_x = center_point.x() + (total_bounding_rect.width() / 2)
    start_y = center_point.y() - (total_bounding_rect.height() / 2)

    # Set the position of each item diagonally
    x_pos = start_x
    y_pos = start_y
    for item in sortedItemsBySize:
        item.setPos(x_pos, y_pos)
        x_pos -= item.boundingRect().width() + spacing
        y_pos += diagonal_slope * (item.boundingRect().width() + spacing)
