"""Module for handling layers and assignments

Example use:

.. code-block:: python

    from zoo.libs.maya.cmds.objutils import layers
    layers.addToLayer("newLayer", ["pSphere1"], ref=False, playback=True, hierarchy=False)

Author: Andrew Silke

"""


from maya import cmds

from zoo.libs.utils import output


def addToLayerExists(layerName, objs, ref=False, playback=True):
    """Adds objects to a display layer, can be a little flaky on the update.

    See addToLayer() to include hierarchy and auto create option, this assigns the current objects to existing layer.

    It does not include children.

    :param layerName:  The name of the layer, will create it if it doesn't exist
    :type layerName: str
    :param objs: a list of the objs to assign to the layer
    :type objs: list(str)
    :param ref: Reference the layer?
    :type ref: bool
    :param playback: set the layer to playback in the viewport?
    :type playback: bool
    """
    for obj in objs:
        cmds.editDisplayLayerMembers(layerName, obj, noRecurse=True)
    if ref:
        cmds.setAttr("{}.displayType".format(layerName), 2)
    if not playback:
        cmds.setAttr("{}.hideOnPlayback".format(layerName), True)


def addToLayer(layerName, objs, ref=False, playback=True, hierarchy=False, message=False):
    """Adds objects to a display layer, and if it doesn't exist create it, can be a little flaky on the update.

    Optional flags:

        ref - sets reference
        playback - sets playback setting
        hierarchy - includes child transform nodes

    Unfortunately cmds.editDisplayLayerMembers() includes shape nodes which is bad for shape colors as it overrides.

    :param layerName:  The name of the layer, will create it if it doesn't exist
    :type layerName: str
    :param objs: a list of the objs to assign to the layer
    :type objs: list(str)
    :param ref: Reference the layer?
    :type ref: bool
    :param playback: set the layer to playback in the viewport?
    :type playback: bool
    :param hierarchy: If True will include the hierarchy of transform nodes, usually not needed
    :type hierarchy: bool
    """
    if hierarchy:
        newObjs = cmds.listRelatives(objs, allDescendents=True, fullPath=True, type="transform")
        if newObjs:
            objs = list(set(objs + newObjs))

    if not cmds.objExists(layerName):
        cmds.createDisplayLayer(name=layerName)

    addToLayerExists(layerName, objs, ref=ref, playback=playback)

    if message:
        output.displayInfo("Success layer created {}".format(layerName))

