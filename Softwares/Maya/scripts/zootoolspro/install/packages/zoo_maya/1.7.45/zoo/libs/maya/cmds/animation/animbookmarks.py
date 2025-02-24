"""Functions related to animation bookmarks.

Example use:

.. code-block:: python

    from zoo.libs.maya.cmds.animation import animbookmarks
    bookmarkNodes, bookmarkNames, startEndList = animbookmarks.allBookmarkTimeranges()



"""
from maya import cmds


def createBookmark(name="SomePrettyName", start=1, stop=100, color=(1, 0, 0)):
    """Creates a maya timeslider bookmark, this is a node in the scene.

    :param name: The display name of the bookmark node in the timeline, not the node name.
    :type name: str
    :param start: The start from of the timeslider bookmark
    :type start: float
    :param stop: The end from of the timeslider bookmark
    :type stop: float
    :param color: The color of the bookmark in the timeslider srgb 0-1
    :type color: tuple(float, float, float)

    :return: The string node name of the bookmark node, eg "timeSliderBookmark1"
    :rtype: str
    """
    from maya.plugin.timeSliderBookmark.timeSliderBookmark import createBookmark
    return createBookmark(name=name, start=start, stop=stop, color=color)


def allBookmarkNodes():
    """Returns all the bookmark nodes in the scene

    :return: All the bookmark nodes in the scene, empty list if none.
    :rtype: list(str)
    """
    return cmds.ls(type="timeSliderBookmark")


def orderedBookmarkNodes():
    """Returns all the bookmark nodes in the scene ordered by their start frame.

    :return: All the bookmark nodes in the scene, empty list if none.
    :rtype: list(str)
    """
    orderedNodes = list()
    bookmarkNodes = cmds.ls(type="timeSliderBookmark")
    if not bookmarkNodes:
        return list()
    nodeFrame = list()
    for node in bookmarkNodes:
        nodeFrame.append((node, cmds.getAttr("{}.timeRangeStart".format(node))))

    nodeFrame.sort(key=lambda x: x[1], reverse=False)

    for t in nodeFrame:
        orderedNodes.append(t[0])
    return orderedNodes


def allBookmarkTimeranges():
    """Returns all the bookmark nodes in the scene with their timeline display names and time ranges.

    :return: bookmarkNodes (node names), bookmarkNames (display timeline names), startEndList [(0-121),(122-140)]
    :rtype: tuple(list(str), list(str), list(tuple(float, float))
    """
    bookmarkNames = list()
    startEndList = list()
    bookmarkNodes = orderedBookmarkNodes()
    if not bookmarkNodes:
        return list(), list(), list()

    for node in bookmarkNodes:
        start = cmds.getAttr("{}.timeRangeStart".format(node))
        end = cmds.getAttr("{}.timeRangeStop".format(node))
        startEndList.append((start, end))
        bookmarkNames.append(cmds.getAttr("{}.name".format(node)))
    return bookmarkNodes, bookmarkNames, startEndList
