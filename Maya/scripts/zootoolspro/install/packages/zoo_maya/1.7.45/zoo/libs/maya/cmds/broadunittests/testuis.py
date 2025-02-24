import maya.api.OpenMaya as om2

from zoo.apps.toolsetsui import run
from zoo.apps.toolpalette import run as runPalette
from zoo.libs.pyqt.widgets import elements

MODELING_TOOLSET_UIS = ["zooMirrorGeo", "modelingAlign", "curveDuplicate", "tubeFromCurve", "thickExtrude",
                        "subDSmoothControl", "objectCleaner", "sculptingToolbox", "objectsToolbox",
                        "topologyNormalsToolbox", "modelingToolbox"]
CONTROLS_JOINTS_TOOLSET_UIS = ["controlCreator", "editControls", "colorOverrides", "jointTool", "planeOrient",
                               "jointsOnCurve", "controlsOnCurve", "splineRig", "reparentGroupToggle",
                               "skinningUtilities", "motionPathRig", "replacejointweights", "riggingMisc",
                               "twistextractor", "constraintToolbox"]
MODEL_ASSETS_TOOLSET_UIS = ["alembicAssets", "mayaScenes", "thumbnailScenes"]
UTILITIES_TOOLSET_UIS = ["zooRenamer", "makeConnections", "channelBoxManager", "matrixTool", "manageNodes",
                         "nodeEditorAlign", "aimAligner", "selectionSets", "multiImportReference",
                         "setMultipleAttributes"]
CAMERAS_TOOLSET_UIS = ["cameraManager", "imagePlaneTool", "imagePlaneAnim", "focusPuller"]
ANIMATION_TOOLSET_UIS = ["generalAnimationTools", "createTurntable", "tweenMachine", "scaleKeysFromCenter",
                         "numericRetimer", "keyRandomizer", "graphEditorTools", "cycleAnimationTools",
                         "bakeAnimation", "animationPaths", "matchBakeAnim", "mocapFeetRetargeter"]
DYNAMIC_TOOLSET_UIS = ["nclothwrinklecreator"]
LIGHT_TOOLSET_UIS = ["lightPresets", "hdriSkydomeLights", "areaLights", "directionalLights", "editLights",
                     "fixViewport", "placeReflection"]
UV_TOOLSET_UIS = ["uvUnfold", "unwrapTube", "transferUvs"]
RENDERER_TOOLSET_UIS = ["convertRenderer", "renderObjectDisplay"]
SHADER_TOOLSET_UIS = ["shaderPresets", "mayaShaders", "shaderManager", "displacementCreator", "createMattesAovs",
                      "convertShaders", "hsvOffset", "matchSwatchSpace", "shaderSwapSuffix", "randomizeShaders"]
HIVE_TOOLSET_UIS = ["hiveFbxRigExport", "hiveMayaReferenceExport", "hiveMirrorPasteAnim", "hiveMayaReferenceExport",
                    "hiveFbxRigExport", "hiveGuideAlignMirror", "jointsToHiveGuides", "addCustomRig"]

ALL_TOOLSET_UIS = MODELING_TOOLSET_UIS + CONTROLS_JOINTS_TOOLSET_UIS + MODEL_ASSETS_TOOLSET_UIS + UTILITIES_TOOLSET_UIS
ALL_TOOLSET_UIS += CAMERAS_TOOLSET_UIS + ANIMATION_TOOLSET_UIS + DYNAMIC_TOOLSET_UIS + LIGHT_TOOLSET_UIS
ALL_TOOLSET_UIS += UV_TOOLSET_UIS + RENDERER_TOOLSET_UIS + SHADER_TOOLSET_UIS + HIVE_TOOLSET_UIS


def openAllUIs(hive=True):
    """Opens all Zoo UIs"""
    om2.MGlobal.displayInfo("\n\n---------- OPEN ALL TOOLSETS: {} -----------")
    palette = runPalette.load()
    for toolsetUi in ALL_TOOLSET_UIS:
        om2.MGlobal.displayInfo("log ---> Toolset Opening: {}".format(toolsetUi))
        run.openToolset(toolsetUi)
        om2.MGlobal.displayInfo("log ---> Toolset Toggled Off: {}".format(toolsetUi))
        run.openToolset(toolsetUi)
    om2.MGlobal.displayInfo("\n\n---------- OPEN OTHER ZOO WINDOWS: {} -----------")
    palette.executePluginById("zoo.preferencesui")
    om2.MGlobal.displayInfo("log ---> Toolset Opened: Zoo Prefs")
    palette.executePluginById("zoo.hotkeyeditorui")
    om2.MGlobal.displayInfo("log ---> Toolset Opened: Hotkey Editor")
    if hive:
        palette.executePluginById("zoo.hive.artistui")
        om2.MGlobal.displayInfo("log ---> Toolset Opened: Hive Artist UI")
    elements.MessageBox.showOK(title="Question Test Window", parent=None, message="Do something?")
    om2.MGlobal.displayInfo("log ---> Dialog Opened")
    om2.MGlobal.displayInfo("\n\n\n#### SUCCESS IMPORTED ASSETS FOR ALL RENDERERS ####\n\n\n")
