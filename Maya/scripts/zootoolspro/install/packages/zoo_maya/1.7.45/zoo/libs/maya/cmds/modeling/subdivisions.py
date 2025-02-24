"""

from zoo.libs.maya.cmds.modeling import subdivisions
subdivisions.toggleSubDsSel()

"""

from maya import cmds
import maya.mel as mel
import maya.api.OpenMaya as om2

from zoo.libs.maya.cmds.objutils import filtertypes
from zoo.libs.maya.cmds.objutils import selection
from zoo.libs.utils import output

from zoovendor import six
from zoo.core.util import classtypes


def subDSettingsShape(meshShape):
    """Returns the subdivision settings of the meshShape node

    :param meshShape: The mesh shape node name
    :type meshShape: str

    :return vpDiv: Gets the Preview Division Levels attribute on the mesh shape
    :rtype vpDiv: int
    :return renderDiv: Gets the Render Division Levels attribute on the mesh shape
    :rtype renderDiv: int
    :return useForRender: Gets the Use Preview Level For Rendering check box on the mesh shape
    :rtype useForRender: bool
    :return showSubDs: Gets the Display Subdivisions check box on the mesh shape
    :rtype showSubDs: bool
    """
    showSubDs = cmds.getAttr("{}.displaySubdComps".format(meshShape))
    vpDiv = cmds.getAttr("{}.smoothLevel".format(meshShape))
    useForRender = cmds.getAttr("{}.useSmoothPreviewForRender".format(meshShape))
    renderDiv = cmds.getAttr("{}.renderSmoothLevel".format(meshShape))
    subDValue = cmds.getAttr("{}.displaySmoothMesh".format(meshShape))
    return subDValue, vpDiv, renderDiv, useForRender, showSubDs


def subDSettingsSelected(message=False):
    """Returns the subdivision settings of the last selected mesh transform

    :param message: return the message to the user?
    :type message: bool

    :return vpDiv: Gets the Preview Division Levels attribute on the mesh shape
    :rtype vpDiv: int
    :return renderDiv: Gets the Render Division Levels attribute on the mesh shape
    :rtype renderDiv: int
    :return useForRender: Gets the Use Preview Level For Rendering check box on the mesh shape
    :rtype useForRender: bool
    :return showSubDs: Gets the Display Subdivisions check box on the mesh shape
    :rtype showSubDs: bool
    """
    selObjs = cmds.ls(selection=True)
    if not selObjs:
        return None, None, None, None, None
    meshList = filtertypes.filterTypeReturnTransforms(selObjs, children=False, shapeType="mesh")
    if not meshList:
        return None, None, None, None, None
    return subDSettingsShape(meshList[0])


def setSubDSettingsShape(meshShape, previewDivisions=2, rendererDivisions=2, usePreview=True, displaySubs=False,
                         subDValue=2, setSubDValue=False):
    """Sets the subD mesh settings on the mesh shape node for polygon object Maya.

    :param meshShape: The mesh shape node name
    :type meshShape: str
    :param previewDivisions: Sets the Preview Division Levels attribute on the mesh shape
    :type previewDivisions: int
    :param rendererDivisions: Sets the Render Division Levels attribute on the mesh shape
    :type rendererDivisions: int
    :param usePreview: Sets the Use Preview Level For Rendering check box on the mesh shape
    :type usePreview: bool
    :param displaySubs: Sets the Display Subdivisions check box on the mesh shape
    :type displaySubs: bool
    :param subDValue: Sets subD display to be on off Eg.  The 1, 2 or 3 key default shortcuts will be 0, 1 or 2
    :type subDValue: int
    :param setSubDValue: if False will not change the current 1, 2, 3 (0, 1, 2) mode of the SubD
    :type setSubDValue: bool
    """
    cmds.setAttr("{}.displaySubdComps".format(meshShape), displaySubs)
    cmds.setAttr("{}.smoothLevel".format(meshShape), previewDivisions)
    cmds.setAttr("{}.useSmoothPreviewForRender".format(meshShape), usePreview)
    cmds.setAttr("{}.renderSmoothLevel".format(meshShape), rendererDivisions)
    if setSubDValue:
        cmds.setAttr("{}.displaySmoothMesh".format(meshShape), subDValue)


def setSubDSettingsTransform(obj, previewDivisions=2, rendererDivisions=2, usePreview=True, displaySubs=False,
                             subDValue=2, setSubDValue=False):
    """Sets the subd mesh settings on a transform polygon node.

    :param obj: The transform node name
    :type obj: str
    :param previewDivisions: Sets the Preview Division Levels attribute on the mesh shape
    :type previewDivisions: int
    :param rendererDivisions: Sets the Render Division Levels attribute on the mesh shape
    :type rendererDivisions: int
    :param usePreview: Sets the Use Preview Level For Rendering check box on the mesh shape
    :type usePreview: bool
    :param displaySubs: Sets the Display Subdivisions check box on the mesh shape
    :type displaySubs: bool
    :param subDValue: Sets subD display to be on off Eg.  The 1, 2 or 3 key default shortcuts will be 0, 1 or 2
    :type subDValue: int
    :param setSubDValue: if False will not change the current 1, 2, 3 (0, 1, 2) mode of the SubD
    :type setSubDValue: bool
    """
    meshShapes = cmds.listRelatives(obj, shapes=True, fullPath=True, type="mesh")
    if not meshShapes:
        return
    for meshShape in meshShapes:
        setSubDSettingsShape(meshShape, previewDivisions=previewDivisions, rendererDivisions=rendererDivisions,
                             usePreview=usePreview, displaySubs=displaySubs, subDValue=subDValue,
                             setSubDValue=setSubDValue)


def setSubDSettingsList(objList, previewDivisions=2, rendererDivisions=2, usePreview=True, displaySubs=False,
                        subDValue=2, setSubDValue=False):
    """Sets the subd mesh settings on a transform polygon node list.

    :param objList: A list of transform node names with mesh shapes
    :type objList: list(str)
    :param previewDivisions: Sets the Preview Division Levels attribute on the mesh shape
    :type previewDivisions: int
    :param rendererDivisions: Sets the Render Division Levels attribute on the mesh shape
    :type rendererDivisions: int
    :param usePreview: Sets the Use Preview Level For Rendering check box on the mesh shape
    :type usePreview: bool
    :param displaySubs: Sets the Display Subdivisions check box on the mesh shape
    :type displaySubs: bool
    :param subDValue: Sets subD display to be on off Eg.  The 1, 2 or 3 key default shortcuts will be 0, 1 or 2
    :type subDValue: int
    :param setSubDValue: if False will not change the current 1, 2, 3 (0, 1, 2) mode of the SubD
    :type setSubDValue: bool
    """
    for obj in objList:
        setSubDSettingsTransform(obj, previewDivisions=previewDivisions, rendererDivisions=rendererDivisions,
                                 usePreview=usePreview, displaySubs=displaySubs, subDValue=subDValue,
                                 setSubDValue=setSubDValue)


def setSubDSettingsList(previewDivisions=2, rendererDivisions=2, usePreview=True, displaySubs=False, subDValue=2,
                        setSubDValue=False, message=True):
    """Sets the subD mesh settings on the current selection

    :param previewDivisions: Sets the Preview Division Levels attribute on the mesh shape
    :type previewDivisions: int
    :param rendererDivisions: Sets the Render Division Levels attribute on the mesh shape
    :type rendererDivisions: int
    :param usePreview: Sets the Use Preview Level For Rendering check box on the mesh shape
    :type usePreview: bool
    :param displaySubs: Sets the Display Subdivisions check box on the mesh shape
    :type displaySubs: bool
    :param subDValue: Sets subD display to be on off Eg.  The 1, 2 or 3 key default shortcuts will be 0, 1 or 2
    :type subDValue: int
    :param setSubDValue: if False will not change the current 1, 2, 3 (0, 1, 2) mode of the SubD
    :type setSubDValue: bool
    :param message: Report the message to the user?
    :type message: bool
    """
    selObjs = cmds.ls(selection=True)
    if not selObjs:
        if message:
            om2.MGlobal.displayWarning("No objects selected.  Please select mesh object/s")
        return
    meshList = filtertypes.filterTypeReturnTransforms(selObjs, children=False, shapeType="mesh")
    if not meshList:
        if message:
            om2.MGlobal.displayWarning("Please select mesh object/s.  No polygon mesh objects found")
        return
    for obj in meshList:
        setSubDSettingsTransform(obj, previewDivisions=previewDivisions, rendererDivisions=rendererDivisions,
                                 usePreview=usePreview, displaySubs=displaySubs, subDValue=subDValue,
                                 setSubDValue=setSubDValue)


def polySmoothMeshes(objs, divisions=1, keepHistory=True):
    """Adds a polysmooth to selected objects

    :param objs: A list of maya meshes
    :type objs: list(str)
    :param divisions: The subdivision level to divide
    :type divisions: int
    :param keepHistory: Keep construction history?
    :type keepHistory: bool
    """
    for obj in objs:
        mel.eval('polySmooth -dv {} -ch 0 {};'.format(divisions, keepHistory, obj))


def polySmoothMeshesSel(divisions=1, keepHistory=True):
    """Adds a polysmooth to selected objects

    :param divisions: The subdivision level to divide
    :type divisions: int
    :param keepHistory: Keep construction history?
    :type keepHistory: bool
    """
    objs = cmds.ls(selection=True)
    polySmoothMeshes(objs, divisions=divisions, keepHistory=keepHistory)


# ----------------------------
# TOGGLE FORCE SUBD ON/OFF
# ----------------------------

def setNurbsDisplaySmooth(nurbsShape, value=0):
    """Sets the Display Smoothness of a list of nurbs curves or surfaces high, med or low quality.

    Value is 0, 1, 0r 3 for low, med, high quality

    :param nurbsShapes: A nurbs shape node name, either surface or curve
    :type nurbsShapes: str
    :param value:  0, 1, or 3 for low, med, high quality
    :type value: int
    """
    if value == 0:
        cmds.displaySmoothness(nurbsShape,
                               divisionsU=0,
                               divisionsV=0,
                               pointsWire=4,
                               pointsShaded=1,
                               polygonObject=1)
    elif value == 1:
        cmds.displaySmoothness(nurbsShape,
                               divisionsU=1,
                               divisionsV=1,
                               pointsWire=8,
                               pointsShaded=2,
                               polygonObject=2)
    else:
        cmds.displaySmoothness(nurbsShape,
                               divisionsU=3,
                               divisionsV=3,
                               pointsWire=16,
                               pointsShaded=4,
                               polygonObject=3)


def toggleNurbsDisplaySmooth(nurbsShapes):
    """Toggles the Display Smoothness of a list of nurbs curves or surfaces high quality or low.

    :param nurbsShapes: a list of nurbs surface or curve shape nodes
    :type nurbsShapes: list(str)
    """
    for shape in nurbsShapes:
        divisions = cmds.displaySmoothness(shape, query=True, divisionsU=True, pointsWire=True)[0]
        if divisions == 4 or divisions == 0:  # surfaces are 0 and curves are 4
            setNurbsDisplaySmooth(shape, value=2)
        else:
            setNurbsDisplaySmooth(shape, value=0)


def toggleSubDs(meshShapes):
    """Toggles the Smooth Mesh Preview (SubD on/off) mode of a list of mesh shapes on or off.

    :param meshShapes: A list of mesh shape nodes.
    :type meshShapes: str
    """
    for shape in meshShapes:  # get the current value
        subDValue = cmds.getAttr("{}.displaySmoothMesh".format(shape))
        if not subDValue:  # set its opposite
            subDValue = 2
        else:
            subDValue = 0
        cmds.setAttr("{}.displaySmoothMesh".format(shape), subDValue)


def toggleSubDsSel(message=False):
    """Toggles the Smooth Mesh Preview (SubD on/off) for the selection.

    Handles both mesh and nurbs surface and curve selection.

    :param message: Report a message to the user?
    :type message: bool
    """
    objSel = cmds.ls(selection=True)
    if not objSel:
        if message:
            output.displayWarning("Nothing is selected, please select some mesh geometry.")
        return
    objSel = selection.componentsToObjectList(objSel)
    nurbsTypes = ["nurbsCurve", "nurbsSurface"]
    nurbsShapes = filtertypes.shapeFromTransformOrShapeTypeList(objSel, nurbsTypes)
    meshShapes = filtertypes.shapeFromTransformOrShapeTypeList(objSel, ["mesh"])
    if not meshShapes and not nurbsShapes:
        if message:
            output.displayWarning("No mesh shapes were found to toggle the SubD setting.")
        return

    if meshShapes:
        toggleSubDs(meshShapes)
    if nurbsShapes:
        toggleNurbsDisplaySmooth(nurbsShapes)


def selectedMeshShapes():
    """Returns the selected mesh shapes or list() if None.

    :return: A list of mesh shape nodes
    :rtype: str
    """
    objSel = cmds.ls(selection=True)
    if not objSel:
        return list()
    meshShapes = cmds.listRelatives(objSel, shapes=True, fullPath=True, type="mesh")
    if not meshShapes:
        return list()
    return meshShapes


def setSubDMode(value):
    """Sets the subD mode to be off (0), hull (1) or on (2)

    :param value: 0: subD is off. 1: subD is in hull mode. 2: subd is on
    :type value: int
    """
    objSel = cmds.ls(selection=True)
    if not objSel:
        return
    objSel = selection.componentsToObjectList(objSel)

    nurbsTypes = ["nurbsCurve", "nurbsSurface"]
    nurbsShapes = filtertypes.shapeFromTransformOrShapeTypeList(objSel, nurbsTypes)
    meshShapes = filtertypes.shapeFromTransformOrShapeTypeList(objSel, ["mesh"])
    if not meshShapes and not nurbsShapes:
        return
    if meshShapes:
        for shape in meshShapes:
            cmds.setAttr("{}.displaySmoothMesh".format(shape), value)
    if nurbsShapes:
        for shape in nurbsShapes:
            setNurbsDisplaySmooth(shape, value)


@six.add_metaclass(classtypes.Singleton)
class ZooSubDTrackerSingleton(object):
    """Used by the subd marking menu & UI, tracks data for subds
    """

    def __init__(self):
        self.markingMenuTriggered = False
