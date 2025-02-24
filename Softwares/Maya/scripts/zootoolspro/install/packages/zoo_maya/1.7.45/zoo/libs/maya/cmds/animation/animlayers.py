"""

Example use:

.. code-block:: python

    from zoo.libs.maya.cmds.animation import animlayers
    animlayers.firstSelectedAnimLayer(ignoreBaseLayer=True)

    from zoo.libs.maya.cmds.animation import animlayers
    animlayers.toggleMuteSelectedAnimationLayers()

"""


import maya.mel as mel
import maya.cmds as cmds

from zoo.libs.utils import output


# -------------------
# ANIMATION LAYERS
# -------------------


def getAttrPlugForLayer(nodeName, attr, animLayer):
    """Find the animBlendNode plug corresponding to the given node, attribute,
    and animation layer.

    Credit from rflannery
    https://forums.autodesk.com/t5/maya-programming/how-to-get-attribute-value-from-animation-layer/td-p/6537895

    :param nodeName: The name of a Maya obj/node name
    :type nodeName: str
    :param attr: The name of a Maya node attribute
    :type attr: str
    :param animLayer: The name of an animation layer
    :type animLayer: str
    :return plug: object.attribute, the plug that connects to the animation curve
    :rtype plug: str
    """
    if not cmds.attributeQuery(attr, node=nodeName, exists=True):  # if attribute does not exist skip
        return None

    nodeAttr = '.'.join([nodeName, attr])
    if not isObjectInAnimLayer(nodeAttr, animLayer):
        return None

    if animLayer == cmds.animLayer(query=True, root=True):
        # For the base animation layer, traverse the chain of animBlendNodes all
        # the way to the end.  The plug will be "inputA" on that last node.
        blendNode = cmds.listConnections(nodeAttr, type='animBlendNodeBase', s=True, d=False)[0]
        history = cmds.listHistory(blendNode)
        lastAnimBlendNode = cmds.ls(history, type='animBlendNodeBase')[-1]
        if cmds.objectType(lastAnimBlendNode, isa='animBlendNodeAdditiveRotation'):
            letterXYZ = nodeAttr[-1]
            plug = '{}.inputA{}'.format(lastAnimBlendNode, letterXYZ.upper())
        else:
            plug = '{}.inputA'.format(lastAnimBlendNode)
    else:
        # For every layer other than the base animation layer, we can just use
        # the "animLayer" command.  Unfortunately the "layeredPlug" flag is
        # broken in Python, so we have to use MEL.
        cmd = 'animLayer -q -layeredPlug "{}" "{}"'.format(nodeAttr, animLayer)
        plug = mel.eval(cmd)
    return plug


# ---------------
# GET ANIMATION CURVES
# ---------------


def getAnimCurveForLayer(nodeName, attr, animLayer):
    """Returns an animation curve name given the node, attribute and the animation layer

    :param nodeName: A Maya node name
    :type nodeName: str
    :param attr: A Maya node attribute name
    :type attr: str
    :param animLayer: The name of an animation layer
    :type animLayer: str
    :return animCurve: Then name of an animation node name, will be unique
    :rtype animCurve: str
    """
    # TODO can probably switch this to use cmds.keyframe(objs, query=True, name=True) with the selected layer
    animCurve = ""
    plug = getAttrPlugForLayer(nodeName, attr, animLayer)
    if not plug:
        return animCurve
    connections = cmds.listConnections(plug, plugs=True)
    if connections:
        animCurvePlug = connections[0]
    if animCurvePlug:
        animCurve = animCurvePlug.split(".")[0]
    return animCurve


def animCurvesInLayers(objs, animLayers):
    """Select all animation curves in all layers for all objects, can also pass in a single object too

    :param objs: A list of maya node names, can also be a single str
    :type objs: list(str)
    :param animLayers: A list of animation layer names
    :type animLayers:  list(str)

    :return animCurves: A list of animation curve node names
    :rtype animCurves: list(str)
    """
    if not animLayers:
        return cmds.keyframe(objs, query=True, name=True)  # can be selected curves or if none then all curves
    # Change selection so that each anim layer is selected, and add all animCurves together
    animCurves = list()
    selAnimLayers = selectedAnimationLayers()
    for animLayer in animLayers:
        replaceSelectAnimLayer(animLayer)  # select animLayer
        animCurves += cmds.keyframe(objs, query=True, name=True)  # Now add the curves from that layer
    if selAnimLayers:  # return animLayer selection
        replaceSelectAnimLayers(selAnimLayers)
    return animCurves


def animCurvesInSelLayers(objs):
    """Returns animation curves for objs found only in the selected layers

    :param objs: A list of maya node names, can also be a single str
    :type objs: list(str)

    :return animCurves: A list of animation curve node names
    :rtype animCurves: list(str)
    """
    selectedLayers = selectedAnimationLayers()
    if selectedLayers:
        return animCurvesInLayers(objs, selectedLayers)
    return list()


def animCurvesAllLayers(objs):
    """Returns animation curves for objs in all animation layers

    :param objs: A list of maya node names, can also be a single str
    :type objs: list(str)

    :return animCurves: A list of animation curve node names
    :rtype animCurves: list(str)
    """
    return animCurvesInLayers(objs, getAllAnimationLayers())


# ---------------
# QUERY ANIMATION LAYERS
# ---------------


def deselectAnimLayer(animLayer):
    """Deselects an animation layer in the layer editor

    :param animLayer: A maya animation layer name
    :type animLayer: str
    """
    mel.eval('animLayerEditorOnSelect "{}" 0;'.format(animLayer))


def selectAnimLayer(animLayer):
    """Selects an animation set, only adds does not deselect

    :param animLayer: A maya animation layer name
    :type animLayer: str
    """
    mel.eval('animLayerEditorOnSelect "{}" 1;'.format(animLayer))


def replaceSelectAnimLayer(animLayer):
    """Selects an animation set while deselecting all other layers

    :param animLayer: A maya animation layer name
    :type animLayer: str
    """
    for lyr in getAllAnimationLayers():
        deselectAnimLayer(lyr)
    selectAnimLayer(animLayer)


def replaceSelectAnimLayers(animLayers):
    """Replace selects multiple animation layers, unselecting all others.

    :param animLayers: A list of Maya animation layer names
    :type animLayers: list(str)
    """
    for lyr in getAllAnimationLayers():
        deselectAnimLayer(lyr)
    for animLayer in animLayers:
        selectAnimLayer(animLayer)


# ---------------
# QUERY ANIMATION LAYERS
# ---------------


def isObjectInAnimLayer(obj, animLayer):
    """Returns whether an object is in an animation layer or not.

    :param obj: The name of a Maya object, can also be a plug "obj.attr"
    :type obj: str
    :param animLayer: The name of an animation layer
    :type animLayer: str
    :return isInLayer: True if the object is a member of the animation layer
    :rtype isInLayer: bool
    """
    objAnimLayers = cmds.animLayer([obj], query=True, affectedLayers=True) or []
    if animLayer in objAnimLayers:
        return True
    return False


def allObjectsInAnimLayer(objs, animLayer):
    """Checks if all objects are all members of an animation layer, returns False if any objects are not members.

    :param objs: A maya node/object name
    :type objs: str
    :param animLayer: The name of an animation layer
    :type animLayer: str
    :return areAllObjectsMembers: True if all objects are members of an animation layer, False if any obj is not
    :rtype areAllObjectsMembers: bool
    """
    for obj in objs:
        if isObjectInAnimLayer(obj, animLayer) is False:
            return False
    return True


def noObjectsInAnimLayer(objs, animLayer):
    """Checks if none of the objects are members of an animation layer, returns False if any objects are members.

    :param objs: A maya node/object name
    :type objs: str
    :param animLayer: The name of an animation layer
    :type animLayer: str
    :return areAllObjectsMembers: True if all objects are members of an animation layer, False if any obj is not
    :rtype areAllObjectsMembers: bool
    """
    for obj in objs:
        if isObjectInAnimLayer(obj, animLayer) is True:
            return False
    return True


# ---------------
# GET ANIMATION LAYERS
# ---------------


def selectedAnimationLayers():
    """Returns all the selected animation layers

    :return animLayer: The name of an animation layer
    :rtype animLayer: str
    """
    return mel.eval('treeView -query -selectItem ("AnimLayerTabanimLayerEditor")') or []


def firstSelectedAnimLayer(ignoreBaseLayer=True):
    """Returns the first selected animation layer or empty string if None are selected

    :param ignoreBaseLayer: Ignore the baseLayer if it's the first selected and don't return it.
    :type ignoreBaseLayer: bool

    :return animLayer: The name of an animation layer
    :rtype animLayer: str
    """
    selAnimLayers = selectedAnimationLayers()
    if selAnimLayers:
        if ignoreBaseLayer and selAnimLayers[0] == "BaseAnimation":
            return ""
        return selAnimLayers[0]
    return ""


def getAllAnimationLayers():
    """Returns all animation layers in the scene

    :return allAnimLayers:  A list of all animation layer names in the scene
    :rtype allAnimLayers: list(str)
    """
    return cmds.ls(type='animLayer')


# ---------------
# Interact with selected animation layers
# ---------------

def toggleMuteSelectedAnimationLayers():
    """Toggles the mute of the selected animation layers, uses the first found value to toggle all selected layers.
    """
    animLayers = selectedAnimationLayers()
    if not animLayers:
        output.displayWarning("No animation layers are selected")
        return

    for animLayerName in animLayers:
        muteValue = cmds.animLayer(animLayerName, query=True, mute=True)
        cmds.animLayer(animLayerName, edit=True, mute=not muteValue)
    output.displayInfo("Animation layers toggled mute: `{}`".format(animLayers))

def deleteSelectedAnimationLayers():
    """Deletes the selected animation layers
    """
    animLayers = selectedAnimationLayers()
    if not animLayers:
        output.displayWarning("No animation layers are selected")
        return
    for animLayer in animLayers:
        cmds.delete(animLayer)
    output.displayInfo("Animation layers deleted: `{}`".format(animLayers))
