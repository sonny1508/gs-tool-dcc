"""
Zoo Python Hotkeys

Example use:

.. code-block:: python

    from zoo.libs.maya.cmds.hotkeys import definedhotkeys
    definedhotkeys.open_zooMirrorGeo(advancedMode=False)

Author: Andrew Silke
"""

import os
import webbrowser

import maya.mel as mel
from maya import cmds

from zoo.libs.utils import output

from zoo.libs.maya.markingmenu import menu as zooMenu
from zoo.libs.maya.cmds.shaders import shaderutils
from zoo.apps.toolsetsui.run import openToolset
from zoo.libs.maya.cmds.modeling import create, normals, modelnodes
from zoo.libs.maya.cmds.objutils import objhandling, matrix, selection
from zoo.apps.toolpalette import run
from zoo.libs.maya.cmds.animation import generalanimation
from zoo.libs.maya.utils import mayaenv
from zoo.apps.hotkeyeditor.markingmenus import deletehistory_markingmenu

MAYA_PATH_LOCATION = mayaenv.getMayaLocation(mayaenv.mayaVersion())
MAYA_VERSION = mayaenv.mayaVersion()


# -------------------
# CREATE FUNCTIONS
# -------------------


def createCamRooXzy():
    """Creates a camera and changes it's rotate order to zxy"""
    from zoo.libs.maya.cmds.cameras import cameras
    cameras.createCameraZxy()


def createCubeMatch():
    """Creates a cube and will match it to the selected object if an object is selected"""
    create.createPrimitiveAndMatch(primitive="cube")


def createCylinderMatch():
    """Creates a cylinder and will match it to the selected object if an object is selected"""
    create.createPrimitiveAndMatch(primitive="cylinder")


def createPlaneMatch():
    """Creates a plane and will match it to the selected object if an object is selected"""
    create.createPrimitiveAndMatch(primitive="plane")


def createSphereMatch():
    """Creates a plane and will match it to the selected object if an object is selected"""
    create.createPrimitiveAndMatch(primitive="sphere")


def createNurbsCircleMatch():
    """Creates a small locator with handle and will match it to the selected object if an object is selected"""
    create.createPrimitiveAndMatch(primitive="nurbsCircle")


def createLocatorMatch(handle=False, locatorSize=1.0):
    """Creates a locator and will match it to the selected object if an object is selected"""
    from zoo.libs.maya.cmds.objutils import locators
    locators.createLocatorAndMatch(handle=handle, locatorSize=locatorSize)


def createCenterPivot(handle=True, locatorSize=0.1):
    """Creates a small locator with handle and will match it to the selected object if an object is selected"""
    from zoo.libs.maya.cmds.objutils import locators
    locators.createLocatorAndMatch(handle=handle, locatorSize=locatorSize)


def createCvCurveTool():
    """Create a CV NURBS curve with 3 degree spans"""
    from zoo.libs.maya.cmds.objutils import curves
    curves.createCurveContext(degrees=3)


def createSelectionSet():
    """Creates a selection set with a warning if in earlier versions of Maya.
    User must create through the menu for the hotkey to become available.
    """
    try:
        mel.eval("defineCharacter;")
    except:
        output.displayWarning("Maya Issue: Please create a set with `Create > Sets > Quick Select Set` first "
                              "and then this hotkey will work.")


# -------------------
# SNAP FUNCTIONS
# -------------------

def snapToProjectedCenter(state=True):
    """Turn snap to projected center on or off

    :param state: Turn the snap on or off?
    :type state: bool
    """
    if state:
        mel.eval("snapMode -meshCenter true;")
    else:
        mel.eval("snapMode -meshCenter false;")


# -------------------
# Marking Menus
# -------------------


def displayMarkingMenuPress():
    # todo needs an upgrade as uses an instance hardcoded to the hotkey
    pass


def displayMarkingMenuRelease():
    # todo needs an upgrade as uses an instance hardcoded to the hotkey
    pass


def lightMarkingMenuPress(alt=False, shift=False, ctrl=False):
    """Lights Marking Menu : Press"""
    zooMenu.MarkingMenu.buildFromLayout("markingMenu.lights",
                                        "lightsMarkingMenu",
                                        parent=mel.eval("findPanelPopupParent"),
                                        options={"altModifier": alt,
                                                 "shiftModifier": shift,
                                                 "ctrlModifier": ctrl})


def lightMarkingMenuRelease():
    """Lights Marking Menu : Release"""
    zooMenu.MarkingMenu.removeExistingMenu("lightsMarkingMenu")


def shaderMarkingMenuPress(alt=False, shift=False, ctrl=False):
    """Shader Marking Menu : Press"""
    zooMenu.MarkingMenu.buildFromLayout("markingMenu.shaders",
                                        "shadersMarkingMenu",
                                        parent=mel.eval("findPanelPopupParent"),
                                        options={"altModifier": alt,
                                                 "shiftModifier": shift,
                                                 "ctrlModifier": ctrl})


def shaderMarkingMenuRelease():
    """Shader Marking Menu : Release"""
    zooMenu.MarkingMenu.removeExistingMenu("shadersMarkingMenu")


def selectionSetMarkingMenuPress(alt=False, shift=False, ctrl=False):
    """Selection Set Marking Menu : Press"""
    zooMenu.MarkingMenu.buildDynamicMenu("selectionSetDynamicMenu",
                                         "menuNameSelectionSet",
                                         mel.eval("findPanelPopupParent"),
                                         {},
                                         options={"altModifier": alt,
                                                  "shiftModifier": shift,
                                                  "ctrlModifier": ctrl})


def selectionSetMarkingMenuRelease():
    """Selection Set Marking Menu : Release"""
    zooMenu.MarkingMenu.removeExistingMenu("menuNameSelectionSet")
    # Secondary function -------------
    from zoo.apps.hotkeyeditor.markingmenus import selectionset_markingmenu
    selectionset_markingmenu.secondaryFunction()


def constraintMarkingMenuPress(alt=False, shift=True, ctrl=False):
    """Constraint Marking Menu : Press"""
    zooMenu.MarkingMenu.buildFromLayout("markingMenu.constraint",
                                        "markingMenuConstraint",
                                        parent=mel.eval("findPanelPopupParent"),
                                        options={"altModifier": alt,
                                                 "shiftModifier": shift,
                                                 "ctrlModifier": ctrl})


def constraintMarkingMenuRelease():
    """Constraint Marking Menu : Release"""
    zooMenu.MarkingMenu.removeExistingMenu("markingMenuConstraint")
    from zoo.apps.hotkeyeditor.markingmenus import constraint_markingmenu
    constraint_markingmenu.secondaryFunction()


def skinMarkingMenuPress(alt=False, shift=True, ctrl=False):
    """Skin Marking Menu : Press"""
    zooMenu.MarkingMenu.buildFromLayout("markingMenu.skinning",
                                        "markingMenuSkinning",
                                        parent=mel.eval("findPanelPopupParent"),
                                        options={"altModifier": alt,
                                                 "shiftModifier": shift,
                                                 "ctrlModifier": ctrl})


def skinMarkingMenuRelease():
    """Skin Marking Menu : Release"""
    zooMenu.MarkingMenu.removeExistingMenu("markingMenuSkinning")


def deformerMarkingMenuPress(alt=False, shift=True, ctrl=False):
    """Deform Marking Menu : Press"""
    zooMenu.MarkingMenu.buildFromLayout("markingMenu.deformers",
                                        "markingMenuDeformers",
                                        parent=mel.eval("findPanelPopupParent"),
                                        options={"altModifier": alt,
                                                 "shiftModifier": shift,
                                                 "ctrlModifier": ctrl})


def deformerMarkingMenuRelease():
    """Deform Marking Menu : Release"""
    zooMenu.MarkingMenu.removeExistingMenu("markingMenuDeformers")


def jointControlMarkingMenuPress(alt=False, shift=True, ctrl=False):
    """Joints and Controls Marking Menu : Press"""
    zooMenu.MarkingMenu.buildFromLayout("markingMenu.joints",
                                        "markingMenuJoints",
                                        parent=mel.eval("findPanelPopupParent"),
                                        options={"altModifier": alt,
                                                 "shiftModifier": shift,
                                                 "ctrlModifier": ctrl})


def jointControlMarkingMenuRelease():
    """Joints and Controls Marking Menu : Release"""
    zooMenu.MarkingMenu.removeExistingMenu("markingMenuJoints")


def motionTrailMarkingMenuPress(alt=False, shift=False, ctrl=False):
    """Motion Trail Marking Menu : Press"""
    zooMenu.MarkingMenu.buildFromLayout("markingMenu.motionTrails",
                                        "motionTrailsMarkingMenu",
                                        parent=mel.eval("findPanelPopupParent"),
                                        options={"altModifier": alt,
                                                 "shiftModifier": shift,
                                                 "ctrlModifier": ctrl})


def motionTrailMarkingMenuRelease():
    """Motion Trail Marking Menu : Release"""
    zooMenu.MarkingMenu.removeExistingMenu("motionTrailsMarkingMenu")
    from zoo.apps.hotkeyeditor.markingmenus import motiontrails_markingmenu
    motiontrails_markingmenu.secondaryFunction()


def subDMarkingMenuPress(alt=False, shift=False, ctrl=False):
    """Motion Trail Marking Menu : Press"""
    zooMenu.MarkingMenu.buildFromLayout("markingMenu.subD",
                                        "subDMarkingMenu",
                                        parent=mel.eval("findPanelPopupParent"),
                                        options={"altModifier": alt,
                                                 "shiftModifier": shift,
                                                 "ctrlModifier": ctrl})


def subDMarkingMenuRelease():
    """Motion Trail Marking Menu : Release"""
    zooMenu.MarkingMenu.removeExistingMenu("subDMarkingMenu")
    from zoo.apps.hotkeyeditor.markingmenus import subd_markingmenu
    subd_markingmenu.secondaryFunction()


def animationMarkingMenuPress(alt=False, shift=False, ctrl=False):
    """Animation Marking Menu : Press"""
    zooMenu.MarkingMenu.buildFromLayout("markingMenu.animation",
                                        "animationMarkingMenu",
                                        parent=mel.eval("findPanelPopupParent"),
                                        options={"altModifier": alt,
                                                 "shiftModifier": shift,
                                                 "ctrlModifier": ctrl})


def animationMarkingMenuRelease():
    """Animation Marking Menu : Release"""
    zooMenu.MarkingMenu.removeExistingMenu("animationMarkingMenu")
    from zoo.apps.hotkeyeditor.markingmenus import animation_markingmenu
    animation_markingmenu.secondaryFunction()


def graphEditorMarkingMenuPress(alt=False, shift=False, ctrl=False):
    zooMenu.MarkingMenu.buildFromLayout("markingMenu.graphEditor",
                                        "graphEditorMarkingMenu",
                                        parent=mel.eval("findPanelPopupParent"),
                                        options={"altModifier": alt,
                                                 "shiftModifier": shift,
                                                 "ctrlModifier": ctrl})


def graphEditorMarkingMenuRelease():
    """Animation Marking Menu : Release"""
    zooMenu.MarkingMenu.removeExistingMenu("graphEditorMarkingMenu")
    from zoo.apps.hotkeyeditor.markingmenus import grapheditor_markingmenu
    grapheditor_markingmenu.secondaryFunction()


def bevelBoolMarkingMenuPress(alt=False, shift=True, ctrl=False):
    """Bevel Boolean Marking Menu : Press"""
    zooMenu.MarkingMenu.buildFromLayout("markingMenu.bevelbool",
                                        "markingMenuBevelBool",
                                        parent=mel.eval("findPanelPopupParent"),
                                        options={"altModifier": alt,
                                                 "shiftModifier": shift,
                                                 "ctrlModifier": ctrl})


def bevelBoolMarkingMenuRelease():
    """Bevel Boolean Marking Menu : Release"""
    zooMenu.MarkingMenu.removeExistingMenu("markingMenuBevelBool")
    from zoo.apps.hotkeyeditor.markingmenus import bevelbool_markingmenu
    bevelbool_markingmenu.secondaryFunction()


def deleteHistoryMarkingMenuPress(alt=False, shift=True, ctrl=False):
    """Delete History Marking Menu : Press"""
    zooMenu.MarkingMenu.buildFromLayout("markingMenu.deletehistory",
                                        "markingMenuDeleteHistory",
                                        parent=mel.eval("findPanelPopupParent"),
                                        options={"altModifier": alt,
                                                 "shiftModifier": shift,
                                                 "ctrlModifier": ctrl})


def deleteHistoryMarkingMenuRelease():
    """Delete History Marking Menu : Release"""
    zooMenu.MarkingMenu.removeExistingMenu("markingMenuDeleteHistory")
    from zoo.apps.hotkeyeditor.markingmenus import deletehistory_markingmenu
    deletehistory_markingmenu.secondaryFunction()


def freezeTransformMarkingMenuPress(alt=False, shift=True, ctrl=False):
    """Freeze Transform Marking Menu : Press"""
    zooMenu.MarkingMenu.buildFromLayout("markingMenu.freezetransform",
                                        "markingMenuFreezeTransform",
                                        parent=mel.eval("findPanelPopupParent"),
                                        options={"altModifier": alt,
                                                 "shiftModifier": shift,
                                                 "ctrlModifier": ctrl})


def freezeTransformMarkingMenuRelease():
    """Freeze Transform Marking Menu : Release"""
    zooMenu.MarkingMenu.removeExistingMenu("markingMenuFreezeTransform")
    from zoo.apps.hotkeyeditor.markingmenus import freezetransform_markingmenu
    freezetransform_markingmenu.secondaryFunction()


# -------------------
# SETTINGS
# -------------------


def hotkeySetToggle():
    """Toggles through all the zoo hotkey sets and user sets"""
    from zoo.apps.hotkeyeditor.core import keysets
    keysets.KeySetManager().nextKeySet()


def reloadZooTools():
    """Reloads Zoo Tools for developers"""
    from zoo.apps.toolpalette import run
    run.load().executePluginById("zoo.reload")


# -------------------
# SELECTION
# -------------------

def selectModeMel():
    mel.eval('SelectTool;')


def lassoSelectMel():
    mel.eval('LassoTool;')


def paintSelectMel():
    mel.eval('ArtPaintSelectTool;')


def selectContiguousEdges():
    mel.eval('performSelContiguousEdges 0;')


def selectShortestPathMel():
    mel.eval('setToolTo polyShortestEdgePathContext')


def selectSimilarMel():
    mel.eval('dR_DoCmd("selectSimilar")')


def selectContiguousEdgesOptions():
    mel.eval('performSelContiguousEdges 1;')


def softSelectToggleMel():
    mel.eval('dR_softSelStickyPress; dR_softSelStickyRelease;')


def softSelectVolume():
    mel.eval('dR_DoCmd("softSelDistanceTypeVolume")')


def softSelectSurface():
    mel.eval('dR_DoCmd("softSelDistanceTypeSurface")')


# -------------------
# CONVERT
# -------------------

def toVerticesMel():
    mel.eval('PolySelectConvert 3;')


def toVertexFacesMel():
    mel.eval('PolySelectConvert 5')


def toVertexPerimiterMel():
    mel.eval('{string $c[]; string $f[]; convertToSelectionBorder(0, true, $c, $f);}')


def toEdgesMel():
    mel.eval('PolySelectConvert 2')


def toEdgeLoopMel():
    mel.eval('polySelectSp -loop;')


def toEdgeRingMel():
    mel.eval('polySelectSp -ring;')


def toContainedEdgesMel():
    mel.eval('PolySelectConvert 20;')


def toEdgePerimiterMel():
    mel.eval('{string $c[]; string $f[]; convertToSelectionBorder(-1, true, $c, $f);}')


def toFacesMel():
    mel.eval('PolySelectConvert 1;')


def toFacePathMel():
    mel.eval('ConvertSelectionToFacePath;')


def toContainedFacesMel():
    mel.eval('ConvertSelectionToContainedFaces;')


def toFacePerimiterMel():
    mel.eval('polySelectEdges edgeRing;getFaces;')


def toFacePerimiterMel():
    mel.eval('polySelectFacePerimeter')


def toUVsMel():
    mel.eval('PolySelectConvert 4')


def toUVShellMel():
    mel.eval('polySelectBorderShell 0')


def toUVShellBorderMel():
    mel.eval('polySelectBorderShell 1')


def toUVPerimiterMel():
    mel.eval('{string $c[]; string $f[]; convertToSelectionBorder(1, true, $c, $f);}')


def toUVEdgeLoopMel():
    mel.eval('polySelectEdges edgeUVLoopOrBorder')


# -------------------
# OBJECTS
# -------------------


def alignSelection():
    """Match Align based on selection (rotation and translation)

    Matches to the first selected object, all other objects are matched to the first in the selection
    """
    from zoo.libs.maya.cmds.objutils import alignutils
    alignutils.matchAllSelection(translate=True, rotate=True, scale=False, pivot=False, message=True)


def mirrorInstanceGroupWorldX():
    """mirror instances an object across world X"""
    from zoo.libs.maya.cmds.modeling import mirror
    mirror.instanceMirror()


def mirrorPolygonPlus():
    """Mirrors polygon with special zero edge or vert selection, plus smooth all edges and delete history"""
    from zoo.libs.maya.cmds.modeling import mirror
    mirror.mirrorPolyEdgeToZero(smoothEdges=True, deleteHistory=True, smoothAngle=180, mergeThreshold=0.001)


def uninstanceSelected():
    """Uninstances the selected object"""
    # Try mirror uninstance first
    from zoo.libs.maya.cmds.modeling import mirror
    networkNodeList = mirror.uninstanceMirrorInstanceSel(message=True)
    if networkNodeList:
        output.displayInfo("Success: Mirror Instance setups uninstanced {}".format(networkNodeList))
        return
    # Try Zoo uninstance
    return objhandling.uninstanceSelected(message=True)


def uninstanceAll():
    """Uninstances all instances in the scene"""
    from zoo.libs.maya.cmds.modeling import mirror
    return mirror.uninstanceMirrorInstacesAll()


# -------------------
# CREATE OBJECTS HOTKEYS
# -------------------

def createPolygonSphereMel():
    createSphereMatch()


def createPolygonCubeMel():
    createCubeMatch()


def createPolygonCylinderMel():
    createCylinderMatch()


def createPolygonPlaneMel():
    createPlaneMatch()


def createPolygonTorusMel():
    create.createPrimitiveAndMatch(primitive="torus")


def createPolygonConeMel():
    create.createPrimitiveAndMatch(primitive="cone")


def createPolygonDiskMel():
    create.createPrimitiveAndMatch(primitive="disk")


def createPolygonFacesMel():
    mel.eval('setToolTo polyCreateFacetContext ; polyCreateFacetCtx -e -pc `optionVar '
             '-q polyKeepFacetsPlanar` polyCreateFacetContext')


def createPlatnonicSolidMel():
    create.createPrimitiveAndMatch(primitive="platonicSolid")


def createPolygonPyramidMel():
    create.createPrimitiveAndMatch(primitive="pyramid")


def createPolygonPrismMel():
    create.createPrimitiveAndMatch(primitive="prism")


def createPolygonPipeMel():
    create.createPrimitiveAndMatch(primitive="pipe")


def createPolygonHelixMel():
    create.createPrimitiveAndMatch(primitive="helix")


def createPolygonGearMel():
    create.createPrimitiveAndMatch(primitive="gear")


def createPolygonSoccerBallMel():
    create.createPrimitiveAndMatch(primitive="soccerBall")


def createPolygonSuperEllipseMel():
    create.createPrimitiveAndMatch(primitive="superEllipsoid")


def createPolygonSphericalHarmonicsMel():
    create.createPrimitiveAndMatch(primitive="sphericalHarmonics")


def createPolygonUltraShapeMel():
    create.createPrimitiveAndMatch(primitive="ultraShape")


def createSweepMeshMel():
    mel.eval('CreateSweepMesh')


def createPolygonTypeMel():
    mel.eval('CreatePolygonType')


def createPolygonSVGMel():
    mel.eval('CreatePolygonSVG')


# -------------------
# OBJECT OPERATIONS HOTKEYS
# -------------------


def duplicateMel():
    mel.eval('performDuplicate false')


def duplicateOffsetMel():
    mel.eval('duplicate -smartTransform;')


def duplicateInputGraphMel():
    mel.eval('duplicate -rr -un;')


def duplicateInputConnectionsMel():
    mel.eval('duplicate -rr -ic;')


def duplicateOpenOptionsMel():
    mel.eval('performDuplicateSpecial true')


def duplicateFaceMel():
    if not meshSelectionWarning():  # message given
        return
    mel.eval('performPolyChipOff 0 1')


def instance():
    objSel = cmds.ls(selection=True)
    if not objSel:
        output.displayWarning("Please select an object to instance.")
        return
    return cmds.instance(objSel)


def boolDifferenceATakeBMel():
    mel.eval('polyPerformBooleanAction 2 o 0')


def boolDifferenceBTakeAMel():
    mel.eval('polyPerformBooleanAction 4 o 0')


def boolUnionMel():
    mel.eval('polyPerformBooleanAction 1 o 0')


def boolIntersectionMel():
    mel.eval('polyPerformBooleanAction 3 o 0')


def boolSiceMel():
    mel.eval('polyPerformBooleanAction 5 o 0')


def boolHolePunchMel():
    mel.eval('polyPerformBooleanAction 6 o 0')


def boolCutOutMel():
    mel.eval('polyPerformBooleanAction 7 o 0')


def boolSplitEdgesMel():
    mel.eval('polyPerformBooleanAction 8 o 0')


def combineMel():
    if not meshSelectionWarning():  # message given
        return
    mel.eval('polyPerformAction polyUnite o 0')


def separateMel():
    if not meshSelectionWarning():  # message given
        return
    mel.eval('performPolyShellSeparate')


def extractMel():
    if not meshSelectionWarning():  # message given
        return
    mel.eval('performPolyChipOff 0 0; toggleSelMode;')


def parentMel():
    mel.eval('performParent false')


def unparentMel():
    mel.eval('performUnparent false')


def groupMel():
    mel.eval('performGroup false')


def ungroupMel():
    mel.eval('performUngroup false')


# -------------------
# MODIFY HOTKEYS
# -------------------

def toggleEditPivotMel():
    mel.eval('ctxEditMode;')


def bakePivotMel():
    mel.eval('performBakeCustomToolPivot 0;')


def matchPivot():
    cmds.matchTransform(cmds.ls(selection=True), pos=False, rot=False, scl=False, piv=True)


def centerPivotMel():
    mel.eval('xform -cpc')


def freezeTransformationsMel():
    if not cmds.ls(selection=True):
        output.displayWarning("Please select an object/s to freeze.")
        return
    mel.eval('performFreezeTransformations(0)')


def unfreezeTransformations():
    if not cmds.ls(selection=True):
        output.displayWarning("Please select an object/s to unfreeze.")
        return
    objhandling.removeFreezeTransformSelected()


def deleteHistoryMel():
    deletehistory_markingmenu.deleteHistoryMel()


def deleteNonDeformerHistoryMel():
    deletehistory_markingmenu.deleteNonDeformerHistoryMel()


def freezeMatrixModeller():
    matrix.zeroSrtModelMatrixSel()


def freezeMatrixAll():
    matrix.srtToMatrixOffsetSel()


def unfreezeMatrix():
    matrix.zeroMatrixOffsetSel()


# -------------------
# MODELING HOTKEYS
# -------------------

def meshSelectionWarning():
    """Warns the user if the selection is not a mesh

    :return: Selection contains mesh objects.
    :rtype: bool
    """
    return selection.meshSelectionWarning(cmds.ls(selection=True))


def extrudeToolMel():
    modelnodes.createExtrude()  # selects the extrude node on multiple objects


def bevelToolMel(chamfer=True, segments=1):
    modelnodes.createBevel(chamfer=chamfer, segments=segments)  # selects the bevel node on multiple objects


def bevelToolMelRounded():
    modelnodes.createBevel(chamfer=True, segments=4)  # selects the bevel node on multiple objects


def bevelToolMelChamferOff():
    modelnodes.createBevel(chamfer=False, segments=1)  # selects the bevel node on multiple objects


def quadDrawToolMel():
    mel.eval('dR_DoCmd("quadDrawTool")')


def makeLiveMelQuadDraw():
    makeLiveMel()
    mel.eval('dR_DoCmd("quadDrawTool")')
    quadDrawToolMel()


def makeLiveMel():
    if cmds.ls(selection=True):
        mel.eval('makeLive')
        output.displayInfo("Make Live Turned On")


def makeLiveOffMel():
    sel = cmds.ls(selection=True)
    cmds.select(deselect=True)
    mel.eval('makeLive')
    if sel:
        cmds.select(sel, replace=True)
    output.displayInfo("Make Live Turned Off")


def bridgeToolMel():
    if not meshSelectionWarning():  # message given
        return
    mel.eval('performBridgeOrFill')


def fillHoleToolMel():
    if not meshSelectionWarning():  # message given
        return
    mel.eval('polyPerformAction polyCloseBorder e 0')


def appendToolMel():
    mel.eval('setToolTo polyAppendFacetContext ; polyAppendFacetCtx -e -pc `optionVar '
             '-q polyKeepFacetsPlanar` polyAppendFacetContext')


def wedgeToolMel():
    mel.eval('performPolyWedgeFace 0')


def chamferVertexToolMel():
    mel.eval('performPolyChamferVertex 0')


def multiCutToolMel():
    mel.eval('dR_DoCmd("multiCutTool")')


def edgeFlowToolMel():
    if not meshSelectionWarning():  # message given
        return
    mel.eval('performPolyEditEdgeFlow 0')


def connectToolMel():
    mel.eval('dR_DoCmd("connectTool")')


def edgeLoopToFromToolMel():
    mel.eval('polySelectEditCtx -e -mode 1 -ac 0 -insertWithEdgeFlow 0 polySelectEditContext; '
             'setToolTo polySelectEditContext;')


def offsetEdgeLoopToolMel():
    mel.eval('performPolyDuplicateEdge 0')


def pokeToolMel():
    if not meshSelectionWarning():  # message given
        return
    mel.eval('performPolyPoke 0')


def mergeCenterToolMel():
    if not meshSelectionWarning():  # message given
        return
    mel.eval('polyMergeToCenter')


def mergeToVertToolMel():
    mel.eval('setToolTo polyMergeVertexContext')


def mergeToleranceToolMel():
    if not meshSelectionWarning():  # message given
        return
    mel.eval('performPolyMerge 0')


def collapseEdgeRingToolMel():
    if not meshSelectionWarning():  # message given
        return
    mel.eval('SelectEdgeRing;polyCollapseEdge;')


def deleteEdgeToolMel():
    if not meshSelectionWarning():  # message given
        return
    mel.eval('performPolyDeleteElements')


def makeHoleToolMel():
    if not meshSelectionWarning():  # message given
        return
    mel.eval('setToolTo polyMergeFacetContext')


def circularizeToolMel():
    if not meshSelectionWarning():  # message given
        return
    mel.eval('performPolyCircularize 0')


def spinEdgeToolMel():
    if not meshSelectionWarning():  # message given
        return
    mel.eval('performPolySpinEdge 0')


def conformToolMel():
    if not meshSelectionWarning():  # message given
        return
    mel.eval('dR_DoCmd("conform")')


def averageVerticesToolMel():
    if not meshSelectionWarning():  # message given
        return
    mel.eval('performPolyAverageVertex 0')


# -------------------
# TOPOLOGY HOTKEYS
# -------------------

def smoothMeshDisplayOnMel():
    mel.eval('setDisplaySmoothness 3')


def smoothMeshDisplayHullMel():
    mel.eval('setDisplaySmoothness 2')


def smoothMeshDisplayOffMel():
    mel.eval('setDisplaySmoothness 1')


def smoothMeshPreviewToPolygonsMel():
    mel.eval('performSmoothMeshPreviewToPolygon')


def smoothPolyMel():
    if not meshSelectionWarning():  # message given
        return
    mel.eval('performPolySmooth 0; toggleSelMode; toggleSelMode; select -addFirst polySmoothFace1 ;')


def divideMel():
    if not meshSelectionWarning():  # message given
        return
    mel.eval('performPolySubdivide "" 0')


def retopologizeMel():
    if not meshSelectionWarning():  # message given
        return
    mel.eval('performPolyRetopo 0')


def retopologizeOptionsMel():
    mel.eval('performPolyRetopo 1')


def remeshMel():
    if not meshSelectionWarning():  # message given
        return
    mel.eval('performPolyRemesh 0')


def remeshOptionsMel():
    mel.eval('performPolyRemesh 1')


def reduceMel():
    if not meshSelectionWarning():  # message given
        return
    mel.eval('performPolyReduce 0')


def reduceOptionsMel():
    mel.eval('performPolyReduce 1')


def unSmoothMel():
    if MAYA_VERSION > 2024:
        output.displayWarning("Unsmooth is only available in 2024 and above.")
        return
    if not meshSelectionWarning():  # message given
        return
    mel.eval('performPolyUnsmooth 0')


def unSmoothOptionsMel():
    if MAYA_VERSION > 2024:
        output.displayWarning("Unsmooth is only available in 2024 and above.")
        return
    mel.eval('performPolyUnsmooth 1')


def triangulateMel():
    if not meshSelectionWarning():  # message given
        return
    mel.eval('polyPerformAction polyTriangulate f 0')


def quadragulateMel():
    if not meshSelectionWarning():  # message given
        return
    mel.eval('performPolyQuadrangulate 0')


def creaseToolMel():
    mel.eval('setToolTo polyCreaseContext')


def uncreaseAll():
    """Removes all crease nodes in the history of the selected objects."""
    sel = cmds.ls(selection=True)
    if not sel:
        return
    for obj in sel:
        shapes = cmds.listRelatives(obj, shapes=True)
        if not shapes:
            return
        for shape in shapes:
            input_nodes = cmds.listConnections(shape, source=True, destination=False)
            if not input_nodes:
                continue
            # Filter the crease nodes
            creaseNodes = cmds.ls(input_nodes, type='polyCrease')
            cmds.delete(creaseNodes)
    cmds.select(sel, replace=True)


def selectCreasedEdges():
    sel = cmds.ls(selection=True)
    # Select the creased in the current selection
    cmds.select([e for e in cmds.filterExpand(cmds.polyListComponentConversion(te=True), sm=32, expand=True) or [] if
                 cmds.polyCrease(e, q=True, v=True)[0] != -1] or [], r=True)
    # Correct the object selection mode
    cmds.select(sel, add=True)
    cmds.selectMode(component=True)


def spinEdgeMel():
    if not meshSelectionWarning():  # message given
        return
    mel.eval('performPolySpinEdge 0')


# -------------------
# NORMALS HOTKEYS
# -------------------


def softenEdgesMel():
    if not meshSelectionWarning():  # message given
        return
    mel.eval('SoftPolyEdgeElements 1')


def hardenEdgesMel():
    if not meshSelectionWarning():  # message given
        return
    mel.eval('SoftPolyEdgeElements 0')


def unlockVertexNormalsMel():
    if not meshSelectionWarning():  # message given
        return
    mel.eval('expandPolyGroupSelection; polyNormalPerVertex -ufn true')


def lockVertexNormalsMel():
    if not meshSelectionWarning():  # message given
        return
    mel.eval('expandPolyGroupSelection; polyNormalPerVertex -fn true')


def conformFaceNormalsMel():
    if not meshSelectionWarning():  # message given
        return
    mel.eval('performPolyNormal 0 2 0')


def reverseFaceNormalsMel():
    if not meshSelectionWarning():  # message given
        return
    mel.eval('performPolyNormal 0 -1 0')


def averageVertexNormalsMel():
    if not meshSelectionWarning():  # message given
        return
    mel.eval('performPolyAverageNormal 0')


def vertexNormalToolMel():
    mel.eval('setToolTo $gPolyNormEdit')


def transferVertexNormalsWorld(space='world'):
    normals.transferVertexNormalsSel(space)


def transferVertexNormalsLocal(space='local'):
    normals.transferVertexNormalsSel(space)


def transferVertexNormalsUv(space='uv'):
    normals.transferVertexNormalsSel(space)


def transferVertexNormalsComponent(space='component'):
    normals.transferVertexNormalsSel(space)


# -------------------
# SCULPTING HOTKEYS
# -------------------

def sculptBrushWithAlpha(brush="SetMeshSculptTool", stampImage="v_wrinkle_vdm.tif"):
    """Opens the Sculpt Tool and sets the v_wrinle_vdm.tif stamp"""
    settingsVis = cmds.workspaceControl("ToolSettings", q=True, r=True)
    mel.eval(brush)  # also opens tool settings window
    stampLocation = os.path.join(MAYA_PATH_LOCATION, r"Examples/Modeling/Sculpting_Stamps/", stampImage)
    stampLocation = stampLocation.replace(os.sep, '/')  # path must have forward slashes
    mel.eval('useSelectedStamp "{}"'.format(stampLocation))
    if not settingsVis:  # The settings was not visible before the tool was opened so toggle it off.
        mel.eval('ToggleToolSettings;')


def sculptToolMel():
    """Opens the Sculpt Tool with no stamp"""
    mel.eval("SetMeshSculptTool")
    mel.eval('sculptMeshCacheSetUseStampImage("sculptMeshCacheContext", false);')  # turn off stamp
    mel.eval('sculptMeshCacheCtx -e -stampFlipY false sculptMeshCacheContext;')  # flip y off


def sculptToolKnifeMel():
    """Opens the Sculpt Tool and sets the v_wrinle_vdm.tif stamp"""
    sculptBrushWithAlpha(brush="SetMeshSculptTool", stampImage="v_wrinkle_vdm.tif")
    mel.eval('sculptMeshCacheCtx -e -stampFlipY false sculptMeshCacheContext;')  # flip y off


def sculptToolDirectionalPinchMel():
    """Opens the Sculpt Tool and sets the v_directionalPinch_vdm.tif stamp"""
    sculptBrushWithAlpha(brush="SetMeshSculptTool", stampImage="v_directionalPinch_vdm.tif")
    mel.eval('sculptMeshCacheCtx -e -stampFlipY false sculptMeshCacheContext;')  # flip y off


def sculptToolEdgeMel(flipY=False):
    """Opens the Sculpt Tool and sets the v_edge_vdm.tif stamp"""
    sculptBrushWithAlpha(brush="SetMeshSculptTool", stampImage="v_edge_vdm.tif")
    if flipY:
        mel.eval('sculptMeshCacheCtx -e -stampFlipY true sculptMeshCacheContext;')  # flip y on
    else:
        mel.eval('sculptMeshCacheCtx -e -stampFlipY false sculptMeshCacheContext;')  # flip y off


def sculptToolFoldMel():
    """Opens the Sculpt Tool and sets the v_fold_vdm.tif stamp"""
    sculptBrushWithAlpha(brush="SetMeshSculptTool", stampImage="v_fold_vdm.tif")
    mel.eval('sculptMeshCacheCtx -e -stampFlipY false sculptMeshCacheContext;')  # flip y off


def sculptToolTubeMel():
    """Opens the Sculpt Tool and sets the v_tube_vdm.tif stamp"""
    sculptBrushWithAlpha(brush="SetMeshSculptTool", stampImage="v_tube_vdm.tif")
    mel.eval('sculptMeshCacheCtx -e -stampFlipY false sculptMeshCacheContext;')  # flip y off


def smoothToolMel():
    """Opens the Smooth Sculpt Tool"""
    mel.eval("SetMeshSmoothTool")


def relaxToolMel():
    """Opens the Sculpt Tool"""
    mel.eval("SetMeshRelaxTool")


def grabToolMel():
    """Opens the Sculpt Tool"""
    mel.eval("SetMeshGrabTool")


def pinchToolMel():
    """Opens the Sculpt Tool"""
    mel.eval("SetMeshPinchTool")


def flattenToolMel():
    """Opens the Sculpt Tool"""
    mel.eval("SetMeshFlattenTool")


def foamyToolMel():
    """Opens the Sculpt Tool"""
    mel.eval("SetMeshFoamyTool")


def sprayToolMel():
    """Opens the Sculpt Tool"""
    mel.eval("SetMeshSprayTool")


def repeatToolMel():
    """Opens the Sculpt Tool"""
    mel.eval("SetMeshRepeatTool")


def imprintToolMel():
    """Opens the Sculpt Tool"""
    mel.eval("SetMeshImprintTool")


def waxToolMel():
    """Sets the Wax Tool"""
    mel.eval("SetMeshWaxTool")
    mel.eval('sculptMeshCacheSetUseStampImage("sculptMeshCacheContext", false);')  # turn off stamp


def waxToolMelHardAlpha():
    """Sets the Wax Tool with bw_strip.tif alpha"""
    sculptBrushWithAlpha(brush="SetMeshWaxTool", stampImage="bw_strip.tif")


def waxToolMelSquareAlpha():
    """Sets the Wax Tool with bw_square.tif alpha"""
    sculptBrushWithAlpha(brush="SetMeshWaxTool", stampImage="bw_square.tif")


def scrapeToolMel():
    """Opens the Sculpt Tool"""
    mel.eval("SetMeshScrapeTool")


def fillToolMel():
    """Opens the Sculpt Tool"""
    mel.eval("SetMeshFillTool")


def knifeToolMel():
    """Opens the Sculpt Tool"""
    mel.eval("SetMeshKnifeTool")


def smearToolMel():
    """Opens the Sculpt Tool"""
    mel.eval("SetMeshSmearTool")


def bulgeToolMel():
    """Opens the Sculpt Tool"""
    mel.eval("SetMeshBulgeTool")


def amplifyToolMel():
    """Opens the Sculpt Tool"""
    mel.eval("SetMeshAmplifyTool")


def freezeToolMel():
    """Opens the Sculpt Tool"""
    mel.eval("SetMeshFreezeTool")


def unfreezeToolMel():
    """Opens the Sculpt Tool"""
    mel.eval('if ( `contextInfo -ex sculptMeshCacheContext`) sculptMeshUnFreeze;')


def invertFreezeToolMel():
    """Opens the Sculpt Tool"""
    mel.eval('if ( `contextInfo -ex sculptMeshCacheContext`) sculptMeshInvertFreeze;')


def convertToFrozenToolMel():
    """Converts vert selection to frozen sculpt mask"""
    mel.eval('ConvertToFrozen;')


def sculptFalloffSurfaceVolumeMel():
    mel.eval("sculptMeshCacheCtx -e -falloffType 0 `currentCtx`;")


def sculptFalloffSurfaceMel():
    mel.eval("sculptMeshCacheCtx -e -falloffType 1 `currentCtx`;")


def sculptFalloffVolumeMel():
    mel.eval("sculptMeshCacheCtx -e -falloffType 2 `currentCtx`;")


# -------------------
# DEFORMERS
# -------------------

def createLatticeMel():
    if MAYA_VERSION > 2019:
        mel.eval("pythonRunTimeCommand ffd.cmd_create 0")
    else:
        mel.eval("performLattice 0")


def createLatticeMelOptions():
    if MAYA_VERSION > 2019:
        mel.eval("pythonRunTimeCommand ffd.cmd_create 1")
    else:
        mel.eval("performLattice 1")


def createBendDeformerMel():
    if MAYA_VERSION > 2019:
        mel.eval("pythonRunTimeCommand bend.cmd_create 0")
    else:
        mel.eval("performBend 0")


def createBendDeformerMelOptions():
    if MAYA_VERSION > 2019:
        mel.eval("pythonRunTimeCommand bend.cmd_create 1")
    else:
        mel.eval("performBend 1")


def createTwistDeformerMel():
    if MAYA_VERSION > 2019:
        mel.eval("pythonRunTimeCommand twist.cmd_create 0")
    else:
        mel.eval("performTwist 0")


def createTwistDeformerMelOptions():
    if MAYA_VERSION > 2019:
        mel.eval("pythonRunTimeCommand twist.cmd_create 1")
    else:
        mel.eval("performTwist 1")


def createWaveDeformerMel():
    if MAYA_VERSION > 2019:
        mel.eval("pythonRunTimeCommand wave.cmd_create 0")
    else:
        mel.eval("performWave 0")


def createWaveDeformerMelOptions():
    if MAYA_VERSION > 2019:
        mel.eval("pythonRunTimeCommand wave.cmd_create 1")
    else:
        mel.eval("performWave 1")


def createFlareDeformerMel():
    if MAYA_VERSION > 2019:
        mel.eval("pythonRunTimeCommand flare.cmd_create 0")
    else:
        mel.eval("performFlare 0")


def createFlareDeformerMelOptions():
    if MAYA_VERSION > 2019:
        mel.eval("pythonRunTimeCommand flare.cmd_create 1")
    else:
        mel.eval("performFlare 1")


# ------------------------------------------------------------------------------------------------------------------
#                                                     WINDOWS
# ------------------------------------------------------------------------------------------------------------------


# -------------------
# ZOO WINDOWS
# -------------------

def toggleToolSettings():
    """Toggles the tool settings window"""
    mel.eval("ToggleToolSettings;")


def open_hiveArtistUI():
    """Opens the Hive Artist UI Window """
    run.show().executePluginById("zoo.hive.artistui")


def open_hiveNamingConvention():
    """Opens the Hive Naming Convention UI Window """
    run.show().executePluginById("hive.namingConfig")


def open_zooGpt():
    """Opens the Zoo GPT UI Window """
    run.show().executePluginById("zoo.chatgpt.ui")


def open_zooHotkeyEditor():
    """Opens the Zoo Hotkey Editor toolset tool"""
    run.show().executePluginById("zoo.hotkeyeditorui")


def open_zooPreferences():
    """Opens the Zoo Preferences toolset tool"""
    run.show().executePluginById("zoo.preferencesui")


# -------------------
# OPEN ZOO TOOLSET TOOLS
# -------------------

# MODELLING

def open_objectsToolbox(advancedMode=False):
    """Opens the Objects Toolbox toolset tool"""
    openToolset("objectsToolbox", advancedMode=advancedMode)


def open_modelingToolbox(advancedMode=False):
    """Opens the Modeling Toolbox toolset tool"""
    openToolset("modelingToolbox", advancedMode=advancedMode)


def open_zooMirrorGeo(advancedMode=False):
    """Opens the Mirror Geo toolset tool"""
    openToolset("zooMirrorGeo", advancedMode=advancedMode)


def open_topologyNormalsToolbox(advancedMode=False):
    """Opens the Topology and Normals Toolbox toolset tool"""
    openToolset("topologyNormalsToolbox", advancedMode=advancedMode)


def open_sculptingToolbox(advancedMode=False):
    """Opens the Sculpting Toolbox toolset tool"""
    openToolset("sculptingToolbox", advancedMode=advancedMode)


def open_modelingAlign(advancedMode=False):
    """Opens the Modeling Align toolset tool"""
    openToolset("modelingAlign", advancedMode=advancedMode)


def open_randomizeObjects(advancedMode=False):
    """Opens the Randomize Objects toolset tool"""
    openToolset("randomizeObjects", advancedMode=advancedMode)


def open_curveDuplicate(advancedMode=False):
    """Opens the Duplicate Along Curve toolset tool"""
    openToolset("curveDuplicate", advancedMode=advancedMode)


def open_tubeFromCurve(advancedMode=False):
    """Opens the Tube From Curve toolset tool"""
    openToolset("tubeFromCurve", advancedMode=advancedMode)


def open_thickExtrude(advancedMode=False):
    """Opens the Thick Extrude toolset tool"""
    openToolset("thickExtrude", advancedMode=advancedMode)


def open_subDSmoothControl(advancedMode=False):
    """Opens the SubD Smooth Control toolset tool"""
    openToolset("subDSmoothControl", advancedMode=advancedMode)


def open_objectCleaner(advancedMode=False):
    """Opens the Object CLeaner toolset tool"""
    openToolset("objectCleaner", advancedMode=advancedMode)


def open_select(advancedMode=False):  # New
    """Opens the Select toolset tool"""
    openToolset("selector", advancedMode=advancedMode)


def open_replaceShapes(advancedMode=False):  # New
    """Opens the Replace Shapes toolset tool"""
    openToolset("replaceShapes", advancedMode=advancedMode)


# CONTROLS JOINTS ---------------------

def open_controlCreator(advancedMode=False):
    """Opens the Control Creator toolset tool"""
    openToolset("controlCreator", advancedMode=advancedMode)


def open_editControls(advancedMode=False):
    """Opens the Edit Controls toolset tool"""
    openToolset("editControls", advancedMode=advancedMode)


def open_colorOverrides(advancedMode=False):
    """Opens the Color Overrides toolset tool"""
    openToolset("colorOverrides", advancedMode=advancedMode)


def open_jointTool(advancedMode=False):
    """Opens the Joint Tool toolset tool"""
    openToolset("jointTool", advancedMode=advancedMode)


def open_jointsOnCurve(advancedMode=False):
    """Opens the Joints On Curve toolset tool"""
    openToolset("jointsOnCurve", advancedMode=advancedMode)


def open_splineRig(advancedMode=False):
    """Opens the Spline Rig toolset tool"""
    openToolset("splineRig", advancedMode=advancedMode)


def open_controlsOnCurve(advancedMode=False):
    """Opens the Controls On Curve toolset tool"""
    openToolset("controlsOnCurve", advancedMode=advancedMode)


def open_motionPathRig(advancedMode=False):
    """Opens the Motion Path Rig toolset tool"""
    openToolset("motionPathRig", advancedMode=advancedMode)


def open_twistExtractor(advancedMode=False):
    """Opens the Twist Extractor toolset tool"""
    openToolset("twistextractor", advancedMode=advancedMode)


def open_skinningUtilities(advancedMode=False):
    """Opens the Skinning Utilities toolset tool"""
    openToolset("skinningUtilities", advancedMode=advancedMode)


def open_replaceJointWeights(advancedMode=False):
    """Opens the `Replace Joint Weights` toolset tool"""
    openToolset("replacejointweights", advancedMode=advancedMode)


def open_riggingMiscellaneous(advancedMode=False):  # new
    """Opens the Skinning Utilities toolset tool"""
    openToolset("riggingMisc", advancedMode=advancedMode)


def open_reparentGroupToggle(advancedMode=False):
    """Opens the Reparent Group Toggle toolset tool"""
    openToolset("reparentGroupToggle", advancedMode=advancedMode)


# MODEL ASSETS ---------------------

def open_scenesBrowser(advancedMode=False):
    """Opens the Maya Scenes toolset tool"""
    openToolset("mayaScenes", advancedMode=advancedMode)


def open_mayaScenes(advancedMode=False):
    """Legacy hotkey"""
    open_scenesBrowser()


def open_alembicAssets(advancedMode=False):
    """Opens the Alembic Assets toolset tool"""
    openToolset("alembicAssets", advancedMode=advancedMode)


def open_modelAssets(advancedMode=False):
    """legacy hotkey"""
    open_alembicAssets()


def open_thumbnailScenes(advancedMode=False):
    """Opens the Thumbnail Scenes toolset tool"""
    openToolset("thumbnailScenes", advancedMode=advancedMode)


# UTILITIES ---------------------

def open_zooRenamer(advancedMode=False):
    """Opens the Zoo Renamer toolset tool"""
    openToolset("zooRenamer", advancedMode=advancedMode)


def open_zooSelectionSets(advancedMode=False):
    """Opens the Zoo Selection Sets toolset tool"""
    openToolset("selectionSets", advancedMode=advancedMode)


def open_makeConnections(advancedMode=False):
    """Opens the Attribute Connections toolset tool"""
    openToolset("makeConnections", advancedMode=advancedMode)


def open_channelBoxManager(advancedMode=False):
    """Opens the `Channel Box Manager` toolset tool"""
    openToolset("channelBoxManager", advancedMode=advancedMode)


def open_manageNodes(advancedMode=False):
    """Opens the Manage Nodes toolset tool"""
    openToolset("manageNodes", advancedMode=advancedMode)


def open_matrixTool(advancedMode=False):  # new
    """Opens the Matrix Tool toolset tool"""
    openToolset("matrixTool", advancedMode=advancedMode)


def open_manageNodesPlugins(advancedMode=False):  # new
    """Opens the Matrix Tool toolset tool"""
    openToolset("manageNodes", advancedMode=advancedMode)


def open_nodeEditorAlign(advancedMode=False):
    """Opens the Node Editor Align toolset tool"""
    openToolset("nodeEditorAlign", advancedMode=advancedMode)


def open_aimAligner(advancedMode=False):
    """Opens the Aim Aligner toolset tool"""
    openToolset("aimAligner", advancedMode=advancedMode)


def open_zooShelfFloatingWindow():
    from zoo.apps.popupuis import zooshelfpopup
    zooshelfpopup.main()


# CAMERAS ---------------------

def open_cameraManager(advancedMode=False):
    """Opens the Camera Manager toolset tool"""
    openToolset("cameraManager", advancedMode=advancedMode)


def open_imagePlaneTool(advancedMode=False):
    """Opens the Image Plane Tool toolset tool"""
    openToolset("imagePlaneTool", advancedMode=advancedMode)


def open_imagePlaneAnim(advancedMode=False):
    """Opens the Animate Image Plane toolset tool"""
    openToolset("imagePlaneAnim", advancedMode=advancedMode)


def open_focusPuller(advancedMode=False):  # new
    """Opens the Focus Puller toolset tool"""
    openToolset("focusPuller", advancedMode=advancedMode)


# ANIMATION ---------------------

def open_generalAnimationTools(advancedMode=False):
    """Opens the General Animation toolset tool"""
    openToolset("generalAnimationTools", advancedMode=advancedMode)


def open_graphEditorTools(advancedMode=False):
    """Opens the Graph Editor Toolbox toolset tool"""
    openToolset("graphEditorTools", advancedMode=advancedMode)


def open_changeRotationOrders(advancedMode=False):  # new
    """Opens the Change Rotation Orders toolset tool"""
    openToolset("changeRotOrder", advancedMode=advancedMode)


def open_tweenMachine(advancedMode=False):  # new
    """Opens the Tween Machine toolset tool"""
    openToolset("tweenMachine", advancedMode=advancedMode)


def open_tweenMachinePopup(cursorOnSlider=False, clickOffClose=False, closeOnRelease=False):
    """Opens the mini popup version of the Tween Machine tool.

    :param cursorOnSlider: If True opens window with the mouse pointer on the slider instead of the window bar.
    :type cursorOnSlider: bool
    :param clickOffClose: If True clicking off the window will close it. False the window will stay open.
    :type clickOffClose: bool
    :param clickOffClose: If True releasing the slider mouse will close the window acting like a marking menu.
    :type clickOffClose: bool
    """
    from zoo.apps.popupuis import tweenpopup
    tweenpopup.main(cursorOnSlider=cursorOnSlider, clickOffClose=clickOffClose, closeOnRelease=closeOnRelease)


def open_bakeAnimation(advancedMode=False):
    """Opens the Bake Animation toolset tool"""
    openToolset("bakeAnimation", advancedMode=advancedMode)


def open_matchBakeAnim(advancedMode=False):
    """Opens the Match And Bake Animation toolset tool"""
    openToolset("matchBakeAnim", advancedMode=advancedMode)


def open_mocapFeetRetargeter(advancedMode=False):
    """Opens the Mocap Feet Retargeter toolset tool"""
    openToolset("mocapFeetRetargeter", advancedMode=advancedMode)


def open_numericRetimer(advancedMode=False):
    """Opens the Numeric Retimer toolset tool"""
    openToolset("numericRetimer", advancedMode=advancedMode)


def open_keyRandomizer(advancedMode=False):
    """Opens the Randomize Keys toolset tool"""
    openToolset("keyRandomizer", advancedMode=advancedMode)


def open_scaleKeysFromCenter(advancedMode=False):
    """Opens the Scale Keys From Center Values toolset tool"""
    openToolset("scaleKeysFromCenter", advancedMode=advancedMode)


def open_cycleAnimationTools(advancedMode=False):
    """Opens the Cycle Animation toolset tool"""
    openToolset("cycleAnimationTools", advancedMode=advancedMode)


def open_createTurntable(advancedMode=False):
    """Opens the Create Turntable toolset tool"""
    openToolset("createTurntable", advancedMode=advancedMode)


def open_animationPaths(advancedMode=False):
    """Opens the Animation Paths toolset tool"""
    openToolset("animationPaths", advancedMode=advancedMode)


# DYNAMICS ---------------------


def open_nclothwrinklecreator(advancedMode=False):
    """Opens the NCloth Wrinkle Creator toolset tool"""
    openToolset("nclothwrinklecreator", advancedMode=advancedMode)


# LIGHTS ---------------------

def open_lightPresets(advancedMode=False):
    """Opens the Light Presets toolset tool"""
    openToolset("lightPresets", advancedMode=advancedMode)


def open_hdriSkydomeLights(advancedMode=False):
    """Opens the HDRI Skydome toolset tool"""
    openToolset("hdriSkydomeLights", advancedMode=advancedMode)


def open_directionalLights(advancedMode=False):
    """Opens the Directional Lights toolset tool"""
    openToolset("directionalLights", advancedMode=advancedMode)


def open_editLights(advancedMode=False):
    """Opens the Edit Lights toolset tool"""
    openToolset("editLights", advancedMode=advancedMode)


def open_areaLights(advancedMode=False):
    """Opens the Area Lights toolset tool"""
    openToolset("areaLights", advancedMode=advancedMode)


def open_placeReflection(advancedMode=False):
    """Opens the Place Reflection toolset tool"""
    openToolset("placeReflection", advancedMode=advancedMode)


def open_fixViewport(advancedMode=False):
    """Opens the Fix Viewport toolset tool"""
    openToolset("fixViewport", advancedMode=advancedMode)


def open_viewportLight(advancedMode=False):
    """Legacy hotkey"""
    open_fixViewport()


# UVS ---------------------

def open_transferUvs(advancedMode=False):
    """Opens the Transfer UVs toolset tool"""
    openToolset("transferUvs", advancedMode=advancedMode)


def open_unwrapTube(advancedMode=False):
    """Opens the UV Unfold toolset tool"""
    openToolset("unwrapTube", advancedMode=advancedMode)


def open_uvUnfold(advancedMode=False):
    """Opens the UV Unfold toolset tool"""
    openToolset("uvUnfold", advancedMode=advancedMode)


# RENDERING ---------------------

def open_convertRenderer(advancedMode=False):
    """Opens the Convert Renderer toolset tool"""
    openToolset("convertRenderer", advancedMode=advancedMode)


def open_renderObjectDisplay(advancedMode=False):  # new
    """Opens the Render Object Display toolset tool"""
    openToolset("renderObjectDisplay", advancedMode=advancedMode)


# SHADERS ---------------------


def open_shaderPresetsMa(advancedMode=False):
    """Opens the Shader Presets (.MA/.MB) toolset tool"""
    openToolset("mayaShaders", advancedMode=advancedMode)


def open_mayaShaders(advancedMode=False):
    """Legacy hotkey"""
    open_shaderPresetsMa()


def open_shaderPresetsMultRenderer(advancedMode=False):
    """Opens the Shader Presets Multi-Renderer toolset tool"""
    openToolset("shaderPresets", advancedMode=advancedMode)


def open_shaderPresets(advancedMode=False):
    """legacy hotkey"""
    open_shaderPresetsMultRenderer()


def open_shaderManager(advancedMode=False):
    """Opens the Shader Manager toolset tool"""
    openToolset("shaderManager", advancedMode=advancedMode)


def open_convertShaders(advancedMode=False):  # new
    """Opens the Convert Shaders toolset tool"""
    openToolset("convertShaders", advancedMode=advancedMode)


def open_randomizeShaders(advancedMode=False):  # new
    """Opens the Randomize Shaders toolset tool"""
    openToolset("randomizeShaders", advancedMode=advancedMode)


def open_shaderSwapSuffix(advancedMode=False):
    """Opens the Shader Swap Suffix toolset tool"""
    openToolset("shaderSwapSuffix", advancedMode=advancedMode)


def open_hsvOffset(advancedMode=False):
    """Opens the HSV Offset shader toolset tool"""
    openToolset("hsvOffset", advancedMode=advancedMode)


def open_hsvOffsetPopup():
    """Opens the mini popup version of the hsv offset tool. """
    from zoo.apps.popupuis import hsvpopup
    hsvpopup.main()


def open_displacementCreator(advancedMode=False):
    """Opens the Displacement Creator toolset tool"""
    openToolset("displacementCreator", advancedMode=advancedMode)


def open_createMattesAovs(advancedMode=False):
    """Opens the Convert Renderer toolset tool"""
    openToolset("createMattesAovs", advancedMode=advancedMode)


def open_matchSwatchSpace(advancedMode=False):
    """Opens the Match Swatch Color Space toolset tool"""
    openToolset("matchSwatchSpace", advancedMode=advancedMode)


# HIVE ---------------------


def open_hiveRefModelSkel(advancedMode=False):
    """Opens the `Hive Reference Model Skeleton` toolset tool"""
    openToolset("referenceModelSkeleton", advancedMode=advancedMode)


def open_hiveExportFbx(advancedMode=False):
    """Opens the Hive Export FBX toolset tool"""
    openToolset("hiveExportFbx", advancedMode=advancedMode)


def open_hiveMirrorPasteAnim(advancedMode=False):
    """Opens the Hive Mirror Paste Anim toolset tool"""
    openToolset("hiveMirrorPasteAnim", advancedMode=advancedMode)


def open_hiveGuideAlignAndMirror(advancedMode=False):
    """Opens the Hive Guide Align and Mirror toolset tool"""
    openToolset("hiveGuideAlignMirror", advancedMode=advancedMode)


def open_hiveAddCustomRigGroup(advancedMode=False):
    """Opens the Add Custom Rig toolset tool"""
    openToolset("addCustomRig", advancedMode=advancedMode)


def hiveToggleControlPanelNodesSel():
    """Toggles the selection of the control panel nodes, if they are selected it will deselect them, if they are not
    """
    from zoo.libs.hive.anim import animatortools
    animatortools.toggleControlPanelNodesSel()


# CODE ---------------------


def open_iconLibrary(advancedMode=False):
    """Opens the Icon Library toolset tool"""
    openToolset("zooIcons", advancedMode=advancedMode)


# THIRD PARTY ---------------------

def open_skinWrangler():
    """Opens the Skin Wrangler third party tool"""
    try:
        from skinWrangler import skinWranglerui
        skinWranglerWindow = skinWranglerui.show()
    except Exception as e:
        address = "https://create3dcharacters.com/maya-third-party/#skinwrangler"
        webbrowser.open(address)
        output.displayWarning("Skin Wrangler is a third party script and is not installed correctly, "
                              "please install from the instructions at {}.".format(address))


def open_brSmoothWeights(advancedMode=False):
    """Opens the Brave Rabbit Smooth Skin Weights third party toolset tool"""
    openToolset("smoothSkin", advancedMode=advancedMode)


def brTransferSkinWeights(export=True):
    """Commands for the Brave Rabbit Transfer Skin Weights third party tool"""
    loaded = cmds.pluginInfo("transferSkinCluster", query=True, loaded=True)
    if not loaded:
        cmds.loadPlugin("transferSkinCluster")
    if export:
        try:
            mel.eval("icTransferSkinCluster 0 0")
        except RuntimeError:
            output.displayWarning("Select geometry with skinning to export the skin weights.")

    else:
        mel.eval("icTransferSkinCluster 1 0")


def open_brTransferSkinWeights_export():
    """Opens the Brave Rabbit Transfer Skin Weights third party tool"""
    try:
        loaded = cmds.pluginInfo("transferSkinCluster", query=True, loaded=True)
        if not loaded:
            cmds.loadPlugin("transferSkinCluster")
    except:
        address = "https://create3dcharacters.com/maya-third-party/#transferskin"
        webbrowser.open(address)
        output.displayWarning("Brave Rabbit Transfer Skin Weights is a third party plugin and is not installed "
                              "correctly, please install from the instructions at {}.".format(address))
        return
    # Plugin loaded now open the tool
    openToolset("brSkinTransferExport", advancedMode=False)


def open_brShapes():
    """Opens the Brave Rabbit SHAPES third party tool"""
    try:
        loaded = cmds.pluginInfo("SHAPESTools", query=True, loaded=True)
        if not loaded:
            cmds.loadPlugin("SHAPESTools")
        mel.eval("SHAPES;")
    except:
        address = "https://create3dcharacters.com/maya-third-party/#shapes"
        webbrowser.open(address)
        output.displayWarning("Brave Rabbit SHAPES is a third party plugin and is not installed correctly, "
                              "please install from the instructions at {}.".format(address))


def open_studioLibrary():
    """Opens the Studio Library third party tool"""
    try:
        from studiolibrary import main as studiolibraryMain
        studiolibraryMain()
    except:
        address = "https://create3dcharacters.com/maya-third-party/#studiolibrary"
        webbrowser.open(address)
        output.displayWarning("Studio Library is a third party script and is not installed correctly, "
                              "please install from the instructions at {}.".format(address))


def open_quadPatcher():
    """Opens the Quad Patcher third party tool"""
    try:
        from quadPatcher import quadPatcherUI
        quadPatcherUI()
    except:
        address = "https://create3dcharacters.com/maya-third-party/#quadpatcher"
        webbrowser.open(address)
        output.displayWarning("Quad Patcher is a third party script and is not installed correctly, "
                              "please install from the instructions at {}.".format(address))


# MAYA WINDOWS ---------------------

def open_mayLightEditor():
    """Opens Maya's Light Editor depending on the version of Maya."""
    try:
        mel.eval('callPython "maya.app.renderSetup.lightEditor.views.editorUI" "createLightEditorWindow" {}')
    except:  # old light editor
        import maya.app.renderSetup.views.lightEditor.editor as __mod
        try:
            __mod.openEditorUI()
        finally:
            del __mod


# ------------------------------------------------------------------------------------------------------------------
#                                                     ANIMATION
# ------------------------------------------------------------------------------------------------------------------


# -------------------
# ANIMATION SELECT
# -------------------


def animSelectHierarchy():
    """Selects all animated nodes in the selected hierarchy"""
    generalanimation.selectAnimNodes(mode=0)


def animSelectScene():
    """Selects all animated nodes in the scene"""
    generalanimation.selectAnimNodes(mode=1)


def animSelectSelection():
    """Filters all animated nodes in the current selection"""
    generalanimation.selectAnimNodes(mode=2)


# -------------------
# ANIMATION GENERAL
# -------------------


def setKeyframeChannelBox():
    """Keys the selected attrs or if nothing is selected keys all attrs"""
    generalanimation.setKeyChannel()


def setKeyAll():
    """Sets a key on all attributes ignoring any Channel Box selection."""
    generalanimation.setKeyAll()


def animMakeHold():
    """Creates a held pose with two identical keys and flat tangents intelligently from the current keyframes
    """
    generalanimation.animHold()


def toogleKeyVisibility():
    """Reverses the visibility of an object in Maya and keys it's visibility attribute"""
    generalanimation.keyToggleVis()


def resetAttrs():
    """Resets attributes in the channel box to defaults"""
    generalanimation.resetAttrsBtn()


def bakeKeys():
    """Bakes animation keyframes using bake curves or bake simulation depending on the selection"""
    generalanimation.bakeKeys()


def eulerFilter():
    """Perform Maya's Euler Filter on selected objects rotation values"""
    generalanimation.eulerFilter()


def createMotionTrail(nameAsObject=True, trailDrawMode=2, showFrames=False, showFrameMarkers=True,
                      frameMarkerSize=1, frameMarkerColor=(0.0, 1.0, 1.0), keyframeSize=2.0,
                      selectOriginal=True, replaceOld=True, suffixNameFrames=False):
    """Creates a motion trail on the selected object and changes the draw mode to `alternating` frames"""
    from zoo.libs.maya.cmds.animation import motiontrail
    motiontrail.createMotionTrailsSel(nameAsObject=nameAsObject, trailDrawMode=trailDrawMode, showFrames=showFrames,
                                      showFrameMarkers=showFrameMarkers, frameMarkerSize=frameMarkerSize,
                                      frameMarkerColor=frameMarkerColor, keyframeSize=keyframeSize,
                                      selectOriginal=selectOriginal, replaceOld=replaceOld,
                                      suffixNameFrames=suffixNameFrames)


def openGhostEditor():
    """Opens Maya's Ghost Editor Window"""
    generalanimation.openGhostEditor()


# -------------------
# GRAPH EDITOR
# -------------------


def jumpKeySelectedTime():
    """Changes the current time in the graph editor (Maya timeline) to match to the closest selected keyframe"""
    generalanimation.timeToKey()


def keySnapToTime():
    """Moves the selected keys to the current time. The first keyframe matching, maintains the spacing of selection"""
    generalanimation.snapKeysCurrent()


def selectObjFromFCurve():
    """Selects an object from an fCurve"""
    generalanimation.selObjGraph()


def snapKeysWholeFrames():
    """Snaps the selected keys to whole frames."""
    generalanimation.snapKeysWholeFrames()


def toggleInfinity():
    """Toggles infinity on and off in the Graph Editor"""
    generalanimation.toggleInfinity()


def cycleInfinity():
    """Cycles the selected objects, with standard cycle option pre and post."""
    generalanimation.cycleAnimation()


def removeCycleAnimation():
    """Cycles the selected objects, with standard cycle option pre and post."""
    generalanimation.removeCycleAnimation()


def copyKeys():
    """Snaps the selected keys to whole frames."""
    generalanimation.copyKeys()


def pasteKeys():
    """Snaps the selected keys to whole frames."""
    generalanimation.pasteKeys()


# -------------------
# PLAY STEP
# -------------------


def playPause():
    """Regular Maya play pause hotkey"""
    generalanimation.playPause()


def playReversePause():
    """Regular Maya play pause hotkey"""
    generalanimation.reverse()


def animMoveTimeBack5Frames():
    """Moves the time slider backwards by 5 frames."""
    generalanimation.step5framesBackwards()


def animMoveTimeForwards5Frames():
    """Moves the time slider forwards by 5 frames."""
    generalanimation.step5framesForwards()


# -------------------
# TIMELINE
# -------------------


def playRangeStart():
    """Sets the range slider start to be the current frame in time"""
    generalanimation.playRangeStart()


def playRangeEnd():
    """Sets the range slider end to be the current frame in time
    """
    generalanimation.playRangeEnd()


def timeRangeStart():
    """Sets the time-range start to the current time."""
    generalanimation.timeRangeStart()


def timeRangeEnd():
    """Sets the time-range end to the current time."""
    generalanimation.timeRangeEnd()


# -------------------
# DISPLAY
# -------------------


def displayToggleTextureMode():
    """Toggles the texture viewport mode, will invert. Eg. if "on" turns "off" """
    from zoo.libs.maya.cmds.display import viewportmodes
    viewportmodes.displayToggleTextureMode()


def displayToggleWireShadedMode():
    """Toggles the texture viewport mode, will invert. Eg. if "on" turns "off" """
    from zoo.libs.maya.cmds.display import viewportmodes
    viewportmodes.displayToggleWireShadedMode()


def displayToggleLightingMode():
    """Toggles the light viewport mode, will invert. Eg. if "on" turns "off" """
    from zoo.libs.maya.cmds.display import viewportmodes
    viewportmodes.displayToggleLightingMode()


def displayToggleWireOnShadedMode():
    """Toggles the 'wireframe on shaded' viewport mode. Will invert. Eg. if "shaded" turns "wireframeOnShaded" """
    from zoo.libs.maya.cmds.display import viewportmodes
    viewportmodes.displayToggleWireOnShadedMode()


def displayToggleXrayMode():
    """Toggles the xray viewport mode. Will invert. Eg. if "xray on" turns "xray off" """
    from zoo.libs.maya.cmds.display import viewportmodes
    viewportmodes.displayToggleXrayMode()


def selectCamInView():
    """Selects the camera under the pointer or if an error, get the camera in active panel, if error return message"""
    from zoo.libs.maya.cmds.cameras import cameras
    cameras.selectCamInView()


def zooCycleBackgroundColors():
    """Adds additional colors to "alt b" which adds more dark colors while cycling through viewport background colors"""
    from zoo.libs.maya.cmds.display import viewportcolors
    viewportcolors.cycleBackgroundColorsZoo()


def cyclePerspCameras(limitPerspective=True):
    """Cycles the main view through all cameras in the scene, default skips orthographic cams"""
    from zoo.libs.maya.cmds.cameras import cameras
    cameras.cycleThroughCameras(limitPerspective=limitPerspective)


# -------------------
# SELECT
# -------------------


def selectHierarchy():
    """Select all children in the hierarchy"""
    from zoo.libs.maya.cmds.objutils import selection
    selection.selectHierarchy()


def selectNodeOrShaderAttrEditor():
    """Selects the shader or the selected nodes:

        1. Selects the node if selected in the channel box and opens the attribute editor
        2. Or if a transform node is selected, select the shaders of the current selection and open attr editor

    """
    shaderutils.selectNodeOrShaderAttrEditor()


def openNamespaceEditor():
    """Opens the namespace editor"""
    mel.eval("namespaceEditor;")
