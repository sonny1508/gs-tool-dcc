from maya import cmds
import maya.api.OpenMaya as om2
import maya.mel as mel
from zoo.libs.maya import zapi
from zoo.libs.maya.cmds.meta import metatubecurve

from zoo.libs.maya.cmds.objutils import filtertypes, namehandling


def paintFxTubePolyTube(curve):
    """From a curve build a poly tube

    :param curve: A curve transform node
    :type curve: str

    :return strokeTransform: The transform node of the paintFX stroke
    :rtype strokeTransform: str
    :return strokeShape: The shape node of the stroke
    :rtype strokeShape: str
    :return meshTransform: The transform node of the mesh
    :rtype meshTransform: str
    :return meshShape: The shape node of the mesh
    :rtype meshShape: str
    """
    # Build --------------------------------------------
    mel.eval("ResetTemplateBrush;")  # resets paint effects brush
    cmds.select(curve, replace=True)
    mel.eval("AttachBrushToCurves;")  # creates the default paint effects on the curve
    mel.eval("doPaintEffectsToPoly(1, 0, 1, 1, 100000);")  # converts paint effects to a polygon mesh
    # Return the objects --------------------------------
    curveRelatives = cmds.listRelatives(curve, fullPath=True)
    strokeShape = cmds.listConnections(curveRelatives, type="stroke", shapes=True, destination=True)[0]
    meshShape = cmds.listConnections(strokeShape, type="mesh", shapes=True, destination=True)[0]
    strokeTransform = cmds.listRelatives(strokeShape, parent=True, type="transform", fullPath=True)[0]
    meshTransform = cmds.listRelatives(meshShape, parent=True, type="transform", fullPath=True)[0]
    brushNode = cmds.listConnections(strokeShape, type="brush")[0]
    group = cmds.listRelatives(meshTransform, parent=True, type="transform", fullPath=True)[0]
    mel.eval("hyperShade - assign initialShadingGroup;")  # assign default material, works because of the selection
    strokeTransform = cmds.parent(strokeTransform, group)[0]
    return strokeTransform, strokeShape, meshTransform, meshShape, brushNode, group


def paintFxTubeRig(curve, radius=1.0, tubeSections=12, minClip=0.0, maxClip=1.0, density=1.0, polyLimit=200000, buildMetaNode=True):
    """ Create poly tube from a given curve, with paint FX.

    :param curve: The curve to build the poly rig ontop of
    :type curve: str
    :param radius: radius of the poly tube
    :type radius: float
    :param tubeSections: The amount of tube radius sections
    :type tubeSections: int
    :param minClip: The minimum clip attribute value
    :type minClip: float
    :param maxClip: The maximum clip attribute value
    :type maxClip: float
    :param density: The density of the poly tube, higher numbers more polys
    :type density: float
    :param polyLimit: The poly limit of the setup
    :type polyLimit: int
    :param buildMetaNode: Add a meta setup to the rig for tracking?
    :type buildMetaNode: bool
    :return nodeList: A list of all the nodes created
    :rtype nodeList: list(str)
    """
    strokeTransform, strokeShape, meshTransform, meshShape, brushNode, group = paintFxTubePolyTube(curve)  # create tube
    # Set brush node to type "Mesh"
    cmds.setAttr("{}.brushType".format(brushNode), 5)
    # Add rig attrs
    cmds.addAttr(meshTransform, longName='radius', attributeType='float', keyable=1, defaultValue=1)
    cmds.addAttr(meshTransform, longName='axisDivisions', attributeType='float', keyable=1, defaultValue=1)
    cmds.addAttr(meshTransform, longName='density', attributeType='float', keyable=1, defaultValue=1)
    cmds.addAttr(meshTransform, longName='minClip', attributeType='float', keyable=1, defaultValue=1)
    cmds.addAttr(meshTransform, longName='maxClip', attributeType='float', keyable=1, defaultValue=1)
    cmds.addAttr(meshTransform, longName='polyLimit', attributeType='float', keyable=1, defaultValue=1)
    # Set rig attr
    cmds.setAttr("{}.radius".format(meshTransform), radius)
    cmds.setAttr("{}.axisDivisions".format(meshTransform), tubeSections)
    cmds.setAttr("{}.minClip".format(meshTransform), minClip)
    cmds.setAttr("{}.maxClip".format(meshTransform), maxClip)
    cmds.setAttr("{}.density".format(meshTransform), density)
    cmds.setAttr("{}.polyLimit".format(meshTransform), polyLimit)
    # Connect Attrs
    cmds.connectAttr("{}.radius".format(meshTransform), "{}.brushWidth".format(brushNode))
    cmds.connectAttr("{}.axisDivisions".format(meshTransform), "{}.tubeSections".format(brushNode))
    cmds.connectAttr("{}.minClip".format(meshTransform), "{}.minClip".format(strokeShape))
    cmds.connectAttr("{}.maxClip".format(meshTransform), "{}.maxClip".format(strokeShape))
    cmds.connectAttr("{}.density".format(meshTransform), "{}.sampleDensity".format(strokeShape))
    cmds.connectAttr("{}.polyLimit".format(meshTransform), "{}.meshPolyLimit".format(strokeShape))
    # Select mesh
    cmds.select(meshTransform, replace=True)
    # Convert to zapi dags so we get the correct names
    strokeShape = zapi.nodeByName(strokeShape)
    meshTransform = zapi.nodeByName(meshTransform)
    strokeTransform = zapi.nodeByName(strokeTransform)
    meshShape = zapi.nodeByName(meshShape)
    # Rename
    # todo: Q Can we just use zapi for this?  A. We'd need to write an undo queue lets not.
    namehandling.safeRename(meshTransform.fullPathName(), "_tube_".join([curve, filtertypes.GEO_SX]))
    group = namehandling.safeRename(group, "_tube_".join([curve, filtertypes.GROUP_SX]))
    namehandling.safeRename(strokeTransform.fullPathName(), "{}_tube_stroke".format(curve))

    ret = (strokeTransform, strokeShape, meshTransform, meshShape, brushNode, zapi.nodeByName(group), zapi.nodeByName(curve))
    if buildMetaNode:
        name = namehandling.nonUniqueNameNumber("{}_tube_meta".format(curve))
        metaNode = metatubecurve.ZooTubeCurve(name=name)
        metaNode.connectAttributes(*ret)

    return ret


def paintFxTubeRigSelected(radius=1.0, tubeSections=12, minClip=0.0, maxClip=1.0, density=1.0, polyLimit=200000,
                           message=True, selectMeshes=True):
    """Adds a paintfx poly tube rig on a selected curve see paintFxTubeRig() for documentation
    """
    nodeLists = list()
    curveTransforms = filtertypes.filterDagObjTransforms(["nurbsCurve"],
                                                         searchHierarchy=False,
                                                         selectionOnly=True,
                                                         message=True,
                                                         dag=False,
                                                         transformsOnly=True)
    if not curveTransforms:
        if message:
            om2.MGlobal.displayWarning("Please select curve/s")
        return
    for curve in curveTransforms:
        nodeLists.append(
            paintFxTubeRig(curve, radius=radius, tubeSections=tubeSections, minClip=minClip, maxClip=maxClip,
                           density=density, polyLimit=polyLimit))
    if message:
        meshList = list()
        for nodeList in nodeLists:
            meshList.append(nodeList[2])
        om2.MGlobal.displayInfo("Success: Tube/s created {}".format(namehandling.getShortNameList(meshList)))

    if selectMeshes:
        cmds.select([n[2].fullPathName() for n in nodeLists])

    return nodeLists



