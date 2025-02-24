"""FBX Exporter for Hive Rigs


------------------------ BATCH RIG EXPORT SETTINGS ----------------------------
Example settings used in the batch exporter.

.. code-block:: python

    from zoo.libs.hive.library.exporters import fbxexporter
    fbxBatch = fbxexporter.fbxBatchExport()
    # Set settings ------------------------------------
    fbxBatch.outputPath = ""  # often overridden by the batch functions
    fbxBatch.skeletonDefinition = True
    fbxBatch.constraints = False
    fbxBatch.tangents = True
    fbxBatch.hardEdges = False
    fbxBatch.smoothMesh = False
    fbxBatch.smoothingGroups = True
    fbxBatch.version = "FBX201800"
    fbxBatch.shapes = True
    fbxBatch.skins = True
    fbxBatch.lights = False
    fbxBatch.cameras = False
    fbxBatch.animation = False
    fbxBatch.startEndFrame = []
    fbxBatch.ascii = False
    fbxBatch.triangulate = True
    fbxBatch.includeChildren = True
    fbxBatch.axis = "Y"
    fbxBatch.includeScale = True # If True then scale attributes will be included in the export
    fbxBatch.meshes = True



------------------------ BATCH RIG EXPORT SIMPLE ----------------------------

Batch by specifying exactly what you need to export, useful for a pipeline. This is the simplest way to export.

.. code-block:: python

    # Batch by specifying exactly what you need to export, useful for a pipeline.
    from zoo.libs.hive.library.exporters import fbxexporter
    fbxBatch = fbxexporter.fbxBatchExport()
    # Main Settings ------------------------------------
    namespace = "ref1"
    rigName = "zoo_mannequin"
    startEndFrames = [(0, 45), (46, 90)]
    outPaths = [r"C:/Users/Username/Desktop/manne_walk", r"C:/Users/Username/Desktop/manne_jump"]
    # Set settings (see above for all settings) ------------------------------------
    fbxBatch.skeletonDefinition = True
    fbxBatch.shapes = True
    fbxBatch.skins = True
    fbxBatch.animation = True
    fbxBatch.meshes = True
    fbxBatch.triangulate = True
    fbxBatch.axis = "Y"
    fbxBatch.version = "FBX201800"
    # Export ------------------------------------
    fbxBatch.exportHiveRigNameAnimClips(rigName, startEndFrames, outPaths, namespace=namespace)



------------------------ CINEMATIC SHOTS - BATCH RIG EXPORT ----------------------------

Batching rigs out for cinematic shots in engine.


1. Batch the SELECTED rigs with one frame range to individual files eg path/rigName.fbx:

FBX names are auto generated based on the rig name and namespace.  Can add suffix to the rig name if needed.

If nameSuffix= "shot05" then the name will be suffixed with the nameSuffix:

    zoo_mannequin_shot05.fbx

If cleanNamespaces is False name includes namespace.

    m1:zoo_mannequin
    becomes
    m1_zoo_mannequin.fbx

If cleanNamespaces is True, then will attempt to remove namespaces if there are no rigName multiples in the scene.

    m1:zoo_mannequin
    becomes
    zoo_mannequin.fbx

.. code-block:: python

    # Batch the selected rigs with one frame range to individual files eg path/rigName.fbx
    from zoo.libs.hive.library.exporters import fbxexporter
    fbxBatch = fbxexporter.fbxBatchExport()
    # Settings ------------------------------------
    folderPath = r"C:/Users/Username/Desktop/"
    nameSuffix = ""  # "shot05", eg will name zoo_mannequin_shot05.fbx
    fbxBatch.startEndFrame = [0, 45]
    fbxBatch.skeletonDefinition = True
    fbxBatch.shapes = True
    fbxBatch.skins = True
    fbxBatch.animation = True
    fbxBatch.meshes = True
    fbxBatch.triangulate = True
    fbxBatch.axis = "Y"
    fbxBatch.version = "FBX201800"
    # Export ------------------------------------
    fbxBatch.exportHiveRigsSel(folderPath, nameSuffix=nameSuffix, cleanNamespaces=True, message=True)


2. Batch the rigs by NAMES with one frame range to individual files eg path/rigName.fbx:

Rig names are the Hive rig name ie "zoo_mannequin".
If there are multiple rigs/clashing names in the scene, add the namespace ie "m1:zoo_mannequin"

If nameSuffix= "shot05" then the name will be suffixed with the nameSuffix:

    zoo_mannequin_shot05.fbx

FBX names are auto generated based on the rig name and namespace if a fileNames list is not given.

If the namespace is given and fileNames is False, names will be named:

    m1:zoo_mannequin
    becomes
    m1_zoo_mannequin.fbx

If no namespace is given and fileNames is False, and no clashes in the scene, names will be named:

    zoo_mannequin
    becomes
    zoo_mannequin.fbx

.. code-block:: python

    # Batch the rigs by name with one frame range to files with custom names Eg. manneExportA.fbx and roboExport.fbx
    from zoo.libs.hive.library.exporters import fbxexporter
    fbxBatch = fbxexporter.fbxBatchExport()
    # Settings ------------------------------------
    # If no rig clashes then the rig name does not need a namespace
    rigNames = ["m1:zoo_mannequin", "mannequinReg_rig_STRD:zoo_mannequin", "r1:robot", ":zoo_mannequin"]
    nameSuffix = "" # "shot05" eg zoo_mannequin.fbx becomes zoo_mannequin_shot05.fbx
    fileOverrideList = None # can be ["manneExportA", "manneExportB", "roboExport", "manneExportC"]
    folderPath = r"C:/Users/Username/Desktop/"
    fbxBatch.startEndFrame = [0, 45]
    fbxBatch.skeletonDefinition = True
    fbxBatch.shapes = True
    fbxBatch.skins = True
    fbxBatch.animation = True
    fbxBatch.meshes = True
    fbxBatch.triangulate = True
    fbxBatch.axis = "Y"
    fbxBatch.version = "FBX201800"
    # Export ------------------------------------
    fbxBatch.exportHiveRigNames(rigNames, folderPath, fileOverrideList=fileOverrideList,nameSuffix=nameSuffix, message=True)


------------------------ GAMES CYCLES - BATCH EXPORT ----------------------------

Batching frame-ranges for cycles.


1. Batch FRAME_RANGES with a single rig, ranges calculated by timeslider bookmarks, files named by timeslider bookmarks:

Files will be automatically named with the name of each timeslider bookmark:

    rigName_walkBookmark.fbx, rigName_runBookmark.fbx etc

If namespace given in the name will be:

    namespace_rigName_walkBookmark.fbx, namespace_rigName_runBookmark.fbx etc

Filenames can be overridden with another optional list of names:

    fileOverrideList = ["walkXX", "runXX"]
    "rigName_walkXX.fbx", "rigName_runXX".fbx"

Rig names can be removed from the filename with prefixRigName=False:

    walkBookmark.fbx, runBookmark.fbx

.. code-block:: python

    # Batch frame ranges with one rig, ranges calculated by timeslider bookmarks, files named by timeslider bookmarks
    from zoo.libs.hive.library.exporters import fbxexporter
    fbxBatch = fbxexporter.fbxBatchExport()
    # Settings ------------------------------------
    # If no rig clashes then the rig name does not need a namespace
    rigName = "zoo_mannequin"  # if multiple clashing rigs use the namespace "m1:zoo_mannequin"
    folderPath = r"C:/Users/Username/Desktop/"
    fileOverrideList = None  # can override the bookmark names eg ["walk", "run"]
    prefixRigName = True  # Adds the rig name to the start of the filename eg. zoo_mannequin_bookmark01.fbx
    fbxBatch.skeletonDefinition = True
    fbxBatch.shapes = True
    fbxBatch.skins = True
    fbxBatch.animation = True
    fbxBatch.meshes = True
    fbxBatch.triangulate = True
    fbxBatch.axis = "Y"
    fbxBatch.version = "FBX201800"
    # Export ------------------------------------
    fbxBatch.exportAnimBookmarksStartEnd(rigName, folderPath, fileOverrideList=fileOverrideList, prefixRigName=True, message=True)


2. Batch FRAME_RANGES with a single rig, ranges calculated by a given start/end list, various name options.

Files will be automatically named with the start/end frame:

    rigName_0_101.fbx, rigName_102_134.fbx etc

If namespace given in the name will be:

    namespace_rigName_0_101.fbx, namespace_rigName_102_134.fbx etc

Filenames can be overridden with another optional list of names:

    fileOverrideList = ["walk", "run"]
    "rigName_walk.fbx", "rigName_run.fbx"

Rig names can be removed from the filename with prefixRigName=False:

    fileOverrideList = ["walk", "run"]
    walk.fbx, run.fbx

.. code-block:: python

    # Batch frame ranges with one rig, ranges calculated by a given start/end list, various naming options.
    from zoo.libs.hive.library.exporters import fbxexporter
    fbxBatch = fbxexporter.fbxBatchExport()
    # Settings ------------------------------------
    # If no rig clashes then the rig name does not need a namespace
    rigName = "zoo_mannequin"  # if multiple clashing rigs use the namespace "m1:zoo_mannequin"
    folderPath = r"C:/Users/Username/Desktop/"
    startEndList = [(1, 73), (74, 120)]
    fileOverrideList = None  # can override the time-range names eg ["walk", "run"]
    prefixRigName = True  # True will prefix the rig name to the file name eg. zoo_mannequin_walk.fbx
    fbxBatch.skeletonDefinition = True
    fbxBatch.shapes = True
    fbxBatch.skins = True
    fbxBatch.animation = True
    fbxBatch.meshes = True
    fbxBatch.triangulate = True
    fbxBatch.axis = "Y"
    fbxBatch.version = "FBX201800"
    # Export ------------------------------------
    fbxBatch.exportStartEndList(rigName, folderPath, startEndList, fileOverrideList=fileOverrideList,
                                prefixRigName=prefixRigName, message=True)

"""
import ast
import os
import logging
import pprint

import maya.mel as mel
from maya import cmds

from zoo.core.util import zlogging

from zoo.libs.maya import zapi
from zoo.libs.maya.utils import files, general
from zoo.libs.maya.cmds.filemanage import saveexportimport
from zoo.libs.hive import api
from zoo.libs.hive.base import rig

from zoo.libs.utils import output, filesystem
from zoo.libs.maya.cmds.animation import animbookmarks
from zoo.libs.hive.base.errors import HiveRigDuplicateRigsError

logger = zlogging.getLogger(__name__)

NO_GEOM_MSG = "Export Meshes is checked but no geometry has been found.\n" \
              "Please parent all geometry into the rig's 'geo_hrc' group."
UI_EXPORT_SETTINGS_NODE = "zooHiveExportFbxUiSettings"
UI_EXPORT_SETTINGS_ATTR = "hiveExportUiSettingsAttr"


class ExportSettings(object):
    """Handles All Currently available fbx export settings
    """

    def __init__(self):
        self.outputPath = ""
        self.skeletonDefinition = True
        self.constraints = False
        self.tangents = True
        self.hardEdges = False
        self.smoothMesh = False
        self.smoothingGroups = True
        self.version = "FBX201800"
        self.shapes = True
        self.skins = True
        self.lights = False
        self.cameras = False
        self.animation = False
        self.startEndFrame = []
        self.ascii = False
        self.triangulate = True
        self.includeChildren = True
        self.axis = "Y"
        # if True then the scene will not be reset, good for debugging the output skeleton.
        self.debugScene = False
        # If True then scale attributes will be included in the export
        self.includeScale = True
        self.meshes = True
        # If True then if there's user errors/warnings etc then they will be shown in a popup dialog.
        self.interactive = False

    def pprint(self):
        pprint.pprint({"outputPath": self.outputPath,
                       "skeletonDefinition": self.skeletonDefinition,
                       "constraints": self.constraints,
                       "tangents": self.tangents,
                       "hardEdges": self.hardEdges,
                       "smoothMesh": self.smoothMesh,
                       "smoothingGroups": self.smoothingGroups,
                       "version": self.version,
                       "shapes": self.shapes,
                       "skins": self.skins,
                       "lights": self.lights,
                       "cameras": self.cameras,
                       "animation": self.animation,
                       "ascii": self.ascii,
                       "triangulate": self.triangulate,
                       "includeChildren": self.includeChildren,
                       "startEndFrame": self.startEndFrame,
                       "includeScale": self.includeScale,
                       "debugScene": self.debugScene,
                       "axis": self.axis,
                       "meshes": self.meshes,
                       "interactive": self.interactive})


class FbxExporterPlugin(api.ExporterPlugin):
    """

    FBX Export hierarchy
    | ------------------- |
    | geometry transform  |
    |    geo              |
    | skeleton root       |
    | ------------------- |

    .. code-block:: python
        from zoo.libs.hive import api as hiveapi
        rigInstance = r.rig()
        rigInstance.startSession("rig")
        exporter = hiveapi.Configuration().exportPluginForId("fbxExport")()
        settings = exporter.exportSettings()  # type: zoo.libs.hive.library.exporters.fbxexporter
        settings.outputPath = outputPath

        # the actual FBX not the display label
        settings.version = "FBX201800"
        settings.shapes = True
        settings.axis = "y"
        settings.triangulate = True
        settings.ascii = True
        settings.animation = True
        settings.startEndFrame = [0.0, 40.0]
        settings.meshes = True
        settings.skins = False

        exporter.execute(rigInstance, settings)
    """
    id = "fbxExport"

    def exportSettings(self):
        return ExportSettings()

    def export(self, rig, exportOptions):
        """

        :param rig:
        :type rig: :class:`zoo.libs.hive.base.rig.Rig`
        :param exportOptions:
        :type exportOptions: :class:`ExportSettings`
        :return:
        :rtype:
        """

        self.onProgressCallbackFunc(10, "Prepping scene for rig export")

        general.loadPlugin("fbxmaya")
        if exportOptions.animation:
            self._exportAnimationRig(rig, exportOptions)
        else:
            self._exportBindPoseRig(rig, exportOptions)

    def _exportAnimationRig(self, rig, exportOptions):
        """
        :param rig:
        :type rig:
        :param exportOptions:
        :type exportOptions:
        :return:
        :rtype:

        Steps for exporting animation.
        We only need the skeleton and blend shapes. For the sake of simplicity the first solution
        we  have is to export blendshapes with the shapes=True option but later we should do a optimised
        version. We go with a simple solution here basically just straight use FBX bake animation instead of
        bakeResults command even though i don't trust fbx bake but to avoid reopening a complex animation
        scene since we would be baking blendshapes weights in this version.


        1. Duplicate the skeleton, this is so the hierarchy for the joints is the same as the bindPose.
            We don't care about the geometry as long as the blendshapes go out and only the weight attribute
            alias names matter. todo: check maya->unity
        2. Clean the skeleton, deleting constraints, attributes etc.
        3. Constraint the duplicate skeleton to the original.
        4. export fbx
        5. delete the duplicate skeleton.


        """
        components = [comp for comp in rig.iterComponents()]
        if not any(comp.hasSkeleton() for comp in components):
            output.displayError("Missing Skeleton please build the skeleton before exporting.")
            return
        currentScenePath = saveexportimport.currentSceneFilePath()
        exportOptions.pprint()
        deformLayer = rig.deformLayer()

        geoLayer = rig.geometryLayer()
        geoRoot = geoLayer.rootTransform()
        deformRoot = deformLayer.rootTransform()

        skelRoots = list(deformRoot.iterChildren(recursive=False, nodeTypes=(zapi.kJoint,)))

        if not exportOptions.skins:
            rootJoints = self._exportAnimNoSkin(skelRoots, exportOptions)
        else:
            rootJoints = self._exportAnimSkin(skelRoots, exportOptions)

        exportNodes = rootJoints
        # un parent the geometry layer so we can reuse it
        if exportOptions.meshes and geoRoot:

            geoParent = geoRoot.parent()
            geoRoot.lock(False)
            geoRoot.setParent(None)
            modifier = zapi.dgModifier()
            geoRoot.removeNamespace(modifier=modifier, apply=False)
            for mesh in geoRoot.iterChildren(recursive=True):
                mesh.removeNamespace(modifier=modifier, apply=False)
            modifier.doIt()
            exportNodes.append(geoRoot)

        self.onProgressCallbackFunc(50, "Starting FBX export")
        _exportFbx(exportNodes, exportOptions)
        self.onProgressCallbackFunc(80, "Completed export to : {}".format(exportOptions.outputPath))

        if not exportOptions.debugScene:
            self.onProgressCallbackFunc(85, "Reopening previous scene")
            files.openFile(currentScenePath)

    def _exportBindPoseRig(self, rig, exportOptions):
        """Exports a rig at bind pose.

        :param rig:
        :type rig: :class:`api.Rig`
        :param exportOptions:
        :type exportOptions: :class:`ExportSettings`

        Necessary Steps for exporting bind pose.
        FBX can be flaky in all sorts of ways and it doesn't flatten or remove namespaces. Asset
         containers always end up in the FBX as well so we do some extra work here to purge.

        1. import any file references. as the skeleton maybe be a ref and we need to remove namespaces
        2. un-parent geometry layer root transform
        3. un-parent joints
        4. clean the skeleton, removing constraints(based on settings), remove namespaces
        5. disconnect the geo layer root transform so we don't delete it when the rig is deleted.
        6. delete the rig. This purges containers and anything random FBX likes to add.
        7. export FBX
        8. reopen the scene.
        """

        components = [comp for comp in rig.iterComponents()]
        if not any(comp.hasSkeleton() for comp in components):
            output.displayError("Missing Skeleton please build the skeleton before exporting.")
            return
        exportOptions.pprint()
        currentScenePath = saveexportimport.currentSceneFilePath()

        deformLayer = rig.deformLayer()
        exportNodes = []
        deformRoot = deformLayer.rootTransform()

        rootGeoTransform, success = self.validate(exportOptions, rig)
        if not success:
            return
        if rootGeoTransform:
            exportNodes.append(rootGeoTransform)
        # import the current scene references so we can blow away nodes and clean namespaces
        saveexportimport.importAllReferences()

        if exportOptions.meshes:
            self._prepGeometry(rig)
        for comp in components:
            compDeform = comp.deformLayer()
            compDeform.disconnectAllJoints()

        skelRoots = list(deformRoot.iterChildren(recursive=False, nodeTypes=(zapi.kJoint,)))

        api.skeletonutils.cleanSkeletonBeforeExport(skelRoots)
        exportNodes.extend(skelRoots)
        # remove the rig in the scene without deleting the joints. This creates a clean FBX file.
        # note: we reopen the scene at the end

        rig.delete(deleteJoints=False)
        try:
            displayLayers = zapi.displayLayers(default=False)
            cmds.delete(displayLayers)
        except RuntimeError:
            pass  # it's erroring because theres no displaylayers left
        self.onProgressCallbackFunc(50, "Exporting Rig as FBX")
        _exportFbx(exportNodes,
                   exportOptions)
        self.onProgressCallbackFunc(75,
                                    "Finished Exporting to :{}, reopening original Scene".format(
                                        exportOptions.outputPath))
        self._resetScene(exportOptions, currentScenePath)

    def validate(self, exportOptions, rig):
        if not exportOptions.meshes:
            return "", True

        _, rootTransform = self._rootGeoHrc(rig)
        if rootTransform is None:
            self.showUserMessage("Missing Geometry", logging.WARNING, NO_GEOM_MSG)
            return "", False
        for _ in rootTransform.iterChildren(recursive=True, nodeTypes=(zapi.kNodeTypes.kMesh,)):
            return rootTransform, True

        if exportOptions.interactive:
            self.showUserMessage("Missing Geometry", logging.WARNING, NO_GEOM_MSG)
            return "", False
        else:
            logging.warning(NO_GEOM_MSG)

    def _resetScene(self, exportOptions, currentScenePath):
        if not exportOptions.debugScene:
            if currentScenePath:
                files.openFile(currentScenePath)
            else:
                files.newScene(force=True)

    def _rootGeoHrc(self, rig):
        geoLayer = rig.geometryLayer()
        if geoLayer is None:
            return
        return geoLayer, geoLayer.rootTransform()

    def _prepGeometry(self, rig):
        """

        :param rig:
        :type rig:
        :return:
        :rtype: :class:`zapi.DagNode`
        """
        geoLayer, geoRoot = self._rootGeoHrc(rig)
        if geoRoot is None:
            return
        geoRoot.setParent(None)
        modifier = zapi.dgModifier()
        modifier.setNodeLockState(geoRoot.object(), False)
        modifier.doIt()
        geoRoot.removeNamespace(modifier=modifier, apply=False)
        for mesh in geoRoot.iterChildren(recursive=True):
            mesh.removeNamespace(modifier=modifier, apply=False)
        modifier.doIt()

        geoLayer.attribute(api.constants.ROOTTRANSFORM_ATTR).disconnectAll()
        return geoRoot

    def _exportAnimNoSkin(self, skeletonRoots, exportOptions):
        # duplicate and constrain the skeleton will need to create temp namespace as mapping
        # the 2 skeleton will need to be done by node name not hive ids since we don't have all the
        # necessary data to do so.
        with zapi.tempNamespaceContext("tempNamespace"):
            self.onProgressCallbackFunc(15, "Prepping skeleton for export")
            duplicateSkeletonJoints = cmds.duplicate([i.fullPathName() for i in skeletonRoots],
                                                     returnRootsOnly=True,
                                                     inputConnections=False,
                                                     renameChildren=False)
            rootJoints = list(zapi.nodesByNames(duplicateSkeletonJoints))

            api.skeletonutils.cleanSkeletonBeforeExport(rootJoints, constraints=False)
            # generate a lookup table for the duplicate skeleton with the shortName: node
            # which will be used to create a constraints between the 2
            joints = {}
            for root in rootJoints:
                joints[root.name(includeNamespace=False)] = root
                for childJnt in root.iterChildren(nodeTypes=(zapi.kNodeTypes.kJoint,)):
                    joints[childJnt.name(includeNamespace=False)] = childJnt
            self.onProgressCallbackFunc(40, "Binding duplicate skeleton to original before exporting")
            # generate constraints between the duplicate and original skeleton
            for skelRoot in skeletonRoots:
                originalName = skelRoot.name(includeNamespace=False)
                matchedDupJnt = joints.get(originalName)
                zapi.buildConstraint(matchedDupJnt, {"targets": [("", skelRoot)]}, constraintType="parent",
                                     trace=False, maintainOffset=False)
                if exportOptions.includeScale:
                    zapi.buildConstraint(matchedDupJnt, {"targets": [("", skelRoot)]}, constraintType="scale",
                                         trace=False, maintainOffset=True)

                for originalChildJnt in skelRoot.iterChildren(nodeTypes=(zapi.kNodeTypes.kJoint,)):
                    originalName = originalChildJnt.name(includeNamespace=False)
                    matchedDupJnt = joints.get(originalName)
                    zapi.buildConstraint(matchedDupJnt, {"targets": [("", originalChildJnt)]}, constraintType="parent",
                                         trace=False, maintainOffset=False)
                    if exportOptions.includeScale:
                        zapi.buildConstraint(matchedDupJnt, {"targets": [("", originalChildJnt)]},
                                             constraintType="scale",
                                             trace=False, maintainOffset=True)
        return rootJoints

    def _exportAnimSkin(self, skeletonRoots, exportOptions):
        # to export with skin at the animation level and still be compatible with the bindpose
        # we need to flatten the references first
        # and then unparent, clean then export.
        # import the current scene references so we can blow away nodes and clean namespaces
        self.onProgressCallbackFunc(15, "Importing all references so we can correctly export skinning")
        saveexportimport.importAllReferences()
        self.onProgressCallbackFunc(30, "Cleaning skeleton data")
        # now unparent the joints and geometry root
        api.skeletonutils.cleanSkeletonBeforeExport(skeletonRoots, constraints=True, onlyHiveAttrs=True)
        try:
            displayLayers = zapi.displayLayers(default=False)
            cmds.delete(displayLayers)
        except RuntimeError:
            pass  # it's erroring because theres no displaylayers left
        return skeletonRoots


def _exportFbx(nodeNames, exportOptions):
    frames = exportOptions.startEndFrame
    startFrame, endFrame = None, None
    if frames:
        startFrame, endFrame = frames
    files.exportFbx(exportOptions.outputPath, [i.fullPathName() for i in nodeNames if i],
                    skeletonDefinition=exportOptions.skeletonDefinition,
                    constraints=exportOptions.constraints,
                    tangents=exportOptions.tangents,
                    hardEdges=exportOptions.hardEdges,
                    smoothMesh=exportOptions.smoothMesh,
                    smoothingGroups=exportOptions.smoothingGroups,
                    version=exportOptions.version,
                    shapes=exportOptions.shapes,
                    skins=exportOptions.skins,
                    lights=exportOptions.lights,
                    cameras=exportOptions.cameras,
                    animation=exportOptions.animation,
                    includeChildren=exportOptions.includeChildren,
                    startFrame=startFrame,
                    endFrame=endFrame,
                    triangulate=exportOptions.triangulate,
                    meshes=exportOptions.meshes
                    )


# ---------------
# Helper Functions For Batching And UI
# ---------------

def rigNeedsNamespace(rigName):
    """If there are duplicated Hive rig names in the scene return True

    :param rigName: The name of a hive rig eg "zoo_mannequin"
    :type rigName: str
    :return: If Duplicated rigs return True
    :rtype: bool
    """
    try:
        api.rootByRigName(rigName, "")
        return False
    except HiveRigDuplicateRigsError:
        return True


def allRigsInScene():
    """Returns a list of rig instances, names and namespaces from the scene's Hive rigs.

    :return: A list of rig instances, names and namespaces
    :rtype: tuple(list(:class:`api.Rig`), list(str), list(str))
    """
    rigNames = list()
    rigNamespaces = list()
    rigInstances = list(api.iterSceneRigs())
    if not rigInstances:
        return list(), list(), list()
    for rigInstance in rigInstances:
        rigNames.append(rigInstance.name())
        rigNamespaces.append(rigInstance.meta.namespace())
    return rigInstances, rigNames, rigNamespaces


def rigsFromNodes(nodes):
    """Returns a list of rig instances, names and namespaces from the given zapi nodes.  Usually a selection.

    :param nodes: A list of zapi node names
    :type nodes: list(:class:`zapi.DagNode`)
    :return: rigInstances, rigNames, rigNamespaces
    :rtype: tuple(list(:class:`api.Rig`), list(str), list(str)
    """
    rigInstances = list()
    rigNames = list()
    rigNamespaces = list()
    for node in nodes:  # get the current selection
        try:
            rigInstance = api.rigFromNode(node)
        except api.MissingMetaNode:
            continue
        if rigInstance.buildState() < api.constants.CONTROL_VIS_STATE:
            output.displayWarning("Rig `{}` must be in at least skeleton mode".format(rigInstance.name()))
            continue
        if rigInstance not in rigInstances:
            rigInstances.append(rigInstance)
            rigNames.append(rigInstance.name())
            rigNamespaces.append(rigInstance.meta.namespace())
    return rigInstances, rigNames, rigNamespaces


def rigsFromNodesSel():
    """Returns a list of rig instances, names and namespaces from the current selection

    :return: A list of Hive rig instances
    :rtype: list(:class:`api.Rig`)
    """
    return rigsFromNodes(list(zapi.selected()))


# ---------------
# UI list rigs and handle namespaces
# ---------------

def allRigsComboUI():
    """Returns a list of unique rig names usually for UI.  Namespaces are added if needed.

    :return: A list of rigNames and a matching set of rig instances
    :rtype: tuple(list(str), list(:class:`api.Rig`))
    """
    rigNamesCombo = list()
    rigInstances, rigNames, namespaces = allRigsInScene()
    if not rigInstances:
        return list(), list()
    for i, name in enumerate(rigNames):
        if namespaces[i] and rigNeedsNamespace(name):
            if namespaces[i].endswith(":"):
                namespaces[i] = namespaces[i][:-1]  # remove the trailing colon
            if namespaces[i].startswith(":"):
                namespaces[i] = namespaces[i][1:]  # remove the start colon
            rigNamesCombo.append("{}:{}".format(namespaces[i], name))
        else:
            rigNamesCombo.append("{}".format(name))
    return rigNamesCombo, rigInstances


# ---------------
# UI text field string conversions
# ---------------

def rigNamesToString(rigNames, namespaces):
    """Converts a list of rig names and namespaces to a string for display in the UI

        "m1:zoo_mannequin, m2:zoo_mannequin, m3:zoo_mannequin"

    will remove the namespace of the name if it doesn't clash in the scene.

        "zoo_mannequin, robot"

    :param rigNames: A list of Hive rig names Eg. ["zoo_mannequin", "zoo_mannequin", "zoo_mannequin"]
    :type rigNames: list(str)
    :param namespaces: A list of Hive rig names Eg. ["m1", "m2", "m3"]
    :type namespaces: list(str)
    :return: A string for a UI text edit field, comma separated. Eg. "m1:zoo_mannequin, m2:zoo_mannequin"
    :rtype: str
    """
    rigNamesStr = ""
    for i, name in enumerate(rigNames):
        if namespaces[i] and rigNeedsNamespace(name):
            if namespaces[i].endswith(":"):
                namespaces[i] = namespaces[i][:-1]  # remove the trailing colon
            if namespaces[i].startswith(":"):
                namespaces[i] = namespaces[i][1:]  # remove the start colon
            if rigNamesStr:
                rigNamesStr += ",  "
            rigNamesStr += "{}:{}".format(namespaces[i], name)
        else:
            rigNamesStr += "{}".format(name)
    return rigNamesStr


def rigsFromNodesSelUI():
    """Returns a single string for UI from the current selection of Hive rigs.  If no rigs are selected returns "".

    :return: A string for a UI text edit field, comma separated. Eg. "m1:zoo_mannequin, m2:zoo_mannequin"
    :rtype: str
    """
    rigInstances, rigNames, namespaces = rigsFromNodesSel()
    if not rigNames:
        output.displayWarning("No Hive Rigs selected")
        return ""
    return rigNamesToString(rigNames, namespaces)


def allRigsInSceneUI():
    """Returns a single string for UI from all Hive rigs in the scene.  If no rigs are selected returns "".

    :return: A string for a UI text edit field, comma separated. Eg. "m1:zoo_mannequin, m2:zoo_mannequin"
    :rtype: str
    """
    rigInstances, rigNames, namespaces = allRigsInScene()
    if not rigNames:
        output.displayWarning("No Hive Rigs Found In Scene")
        return ""
    return rigNamesToString(rigNames, namespaces)


def numberToNiceStr(number):
    """Converts a number to a string and removes the trailing ".0" if it exists

    :param number: A number
    :type number: float
    :return: The number now formatted nicely as a string
    :rtype: str
    """
    numberStr = str(number)
    if numberStr.endswith(".0"):
        numberStr = numberStr[:-2]
    return numberStr


def nameFramerangeToStr(names, frameRanges):
    """Converts a list of names and frame ranges to a string for display in the UI

    :param names: A list of names matching the frame ranges, usually from timeslider bookmarks or from the Game Exporter.
    :type names: list(str)
    :param frameRanges: A list of frame ranges, each frame range is a tuple of (startFrame, endFrame)
    :type frameRanges: list(tuple(float, float))
    :return: Two strings for a UI text edit field, comma separated. Eg. "m1:rig, m2:rig", "1-10, 20-30"
    :rtype: tuple(str)
    """
    nameString = ""
    frameRangeString = ""
    if names:
        for name in names:
            if nameString:
                nameString += ", "
            nameString += "{}".format(name)
    if frameRanges:
        for frameRange in frameRanges:
            if frameRangeString:
                frameRangeString += ", "
            frameRangeString += numberToNiceStr(frameRange[0])
            frameRangeString += "-"
            frameRangeString += numberToNiceStr(frameRange[1])
    return nameString, frameRangeString


def convertStrToList(aString):
    """Converts a string to a list, removing spaces and splitting by commas.

    :param aString: a string comma separated " a file name,  another file name,  a third file name  "
    :type aString: str
    :return: A list of string names ["a file name", "another file name", "a third file name"]
    :rtype: list(str)
    """
    stringList = aString.split(",")
    return [string.strip() for string in stringList]


def strToRigListUI(rigNamesStr):
    """Converts a string of rig names to a list of rig names

    :param rigNamesStr: A string of rig names " zoo_mannequin,  robot ,  zanzi  "
    :type rigNamesStr: str
    :return: A list of rig names ["zoo_mannequin", "robot", "zanzi"]
    :rtype: list(str)
    """
    if not rigNamesStr:
        return list()
    return convertStrToList(rigNamesStr)


def strToFrameRangeListUI(frameRangeStr):
    """Converts a string of frame ranges to a list of frame ranges.

    :param frameRangeStr: A string of frame ranges "1-10, 20-30, 40-50"
    :type frameRangeStr: str
    :return: A list of frame ranges  [(1, 10), (20, 30), (40, 50)]
    :rtype: list(tuple(float, float))
    """
    if not frameRangeStr:
        return list()
    rangeList = list()
    rangeStringList = convertStrToList(frameRangeStr)
    if not rangeStringList:
        return list()
    for i, rangeString in enumerate(rangeStringList):
        if "-" not in rangeString:
            output.displayWarning("Invalid frame range: Must be numbers joined by dashes and comma separated. "
                                  "Eg. `1-10, 20-30`")
            return ["error"]
        startEnd = rangeString.split("-")
        try:
            start = float(startEnd[0].strip())
            end = float(startEnd[1].strip())
        except ValueError:
            output.displayWarning("Invalid frame range: Must be numbers joined by dashes and comma separated. "
                                  "Eg. `1-10, 20-30`")
            return ["error"]
        rangeList.append((start, end))
    return rangeList


def strToClipNameListUI(clipNamesStr):
    """Converts a string of clip names to a list of clip names.

    :param clipNamesStr: a string comma separated " runCycle ,  walk,  jump  "
    :type clipNamesStr: str
    :return: A list of string names ["runCycle", "walk", "jump"]
    :rtype: list(str)
    """
    if not clipNamesStr:
        return list()
    return convertStrToList(clipNamesStr)


# ---------------
# Load Save UI Settings
# ---------------

def saveUIExportSettingsScene(uiSettingsDict):
    """Save the UI settings to the scene on a network node named "zooHiveExportSettings"

    :param uiSettingsDict:
    :type uiSettingsDict:
    :return:
    :rtype:
    """
    uiSettingsNode = cmds.ls(UI_EXPORT_SETTINGS_NODE, type="network", long=True)
    if not uiSettingsNode:  # create the node
        exportNode = cmds.createNode("network", name=UI_EXPORT_SETTINGS_NODE)
        cmds.addAttr(exportNode, longName=UI_EXPORT_SETTINGS_ATTR, dataType="string")
    else:
        exportNode = uiSettingsNode[0]
    cmds.setAttr("{}.{}".format(exportNode, UI_EXPORT_SETTINGS_ATTR), str(uiSettingsDict), type="string")
    output.displayInfo("Saved UI settings to scene: {}".format(exportNode))
    return exportNode


def loadUIExportSettingsScene():
    """Load the UI settings dict and return it, from a network node named "zooHiveExportSettings"

    :return: A dictionary of UI settings
    :rtype: dict
    """
    if not cmds.objExists(UI_EXPORT_SETTINGS_NODE):
        return dict()
    uiSettingsStr = cmds.getAttr("{}.{}".format(UI_EXPORT_SETTINGS_NODE, UI_EXPORT_SETTINGS_ATTR))
    return ast.literal_eval(uiSettingsStr)


def saveUIExportSettingsFile(uiSettingsDict, filePath):
    """Saves the UI settings to a json file

    :param uiSettingsDict: A dictionary of UI settings
    :type uiSettingsDict: dict()
    :param filePath: The full file path to save to
    :type filePath: str
    :return: Success file written?
    :rtype: bool
    """
    filesystem.saveJson(uiSettingsDict, filePath, indent=4, separators=(",", ":"))


def loadUIExportSettingsFile(filePath):
    """Loads the UI settings from a json file

    :param filePath: The full file path to the file to open
    :type filePath: str
    :return: The json file as a dictionary
    :rtype: dict()
    """
    return filesystem.loadJson(filePath)


# ---------------
# Get Bookmark Data
# ---------------

def bookmarkData():
    """Returns a list of bookmark names and a list of frame ranges from the timeslider bookmarks.

    :return: A list of bookmark names and a list of frame ranges from the timeslider bookmarks
    :rtype: tuple(list(str)), list(tuple(float, float)))
    """
    bookmarkNodes, bookmarkNames, startEndList = animbookmarks.allBookmarkTimeranges()
    if not bookmarkNodes:
        output.displayWarning("No bookmarks found")
        return list(), list()
    return bookmarkNames, startEndList


def bookmarkDataUI():
    """Converts a list of bookmark names and a list of frame ranges to a string for display in the UI

    :return: Two strings for a UI text edit field, comma separated. Eg. "m1:rig, m2:rig", "1-10, 20-30"
    :rtype: tuple(str)
    """
    names, frameRanges = bookmarkData()
    nameString, frameRangeString = nameFramerangeToStr(names, frameRanges)
    return nameString, frameRangeString


# ---------------
# Get Game Export Data
# ---------------

def openMayaGameExporter():
    """Opens the Maya Game Exporter UI"""
    mel.eval("gameFbxExporter;")


def createTimesliderBookmarkWindow():
    """Opens the  Create Time Slider Bookmark window"""
    mel.eval("CreateTimeSliderBookmark;")


def gameExporterClipData():
    """Returns a list of clip names and a list of frame ranges from the Game Exporter.

    :return: clipNames, startEndList, path: A list of clip names, a list of frame ranges and the export path
    :rtype: tuple(list(str), list(tuple(float, float)), str)
    """
    clipNames = list()
    startEndList = list()

    if not cmds.objExists("gameExporterPreset2"):
        output.displayWarning("No game exporter preset found, open the Game Exporter UI and create clips")
        return list(), list(), ""

    path = zapi.nodeByName("gameExporterPreset2").attribute("exportPath").value()

    for i in range(len(zapi.nodeByName("gameExporterPreset2").attribute("animClips"))):  # loop over existing clips
        export = zapi.nodeByName("gameExporterPreset2").attribute("animClips[{}].exportAnimClip".format(i)).value()
        if not export:  # skip if not exporting
            continue
        start = zapi.nodeByName("gameExporterPreset2").attribute("animClips[{}].animClipStart".format(i)).value()
        end = zapi.nodeByName("gameExporterPreset2").attribute("animClips[{}].animClipEnd".format(i)).value()
        name = zapi.nodeByName("gameExporterPreset2").attribute("animClips[{}].animClipName".format(i)).value()
        if not name and not start and not end:
            continue  # not valid
        clipNames.append(name)
        startEndList.append((start, end))

    if not clipNames:
        output.displayWarning("No enabled clips found in game exporter preset.")
        return list(), list(), ""

    return clipNames, startEndList, path


def gameExporterClipDataUI():
    """

    :return: Two strings, comma separated. Eg. "m1:rig, m2:rig", "1-10, 20-30" and the output folder
    :rtype: tuple(str, str, str)
    """
    names, frameRanges, outputFolder = gameExporterClipData()
    nameString, frameRangeString = nameFramerangeToStr(names, frameRanges)
    return nameString, frameRangeString, outputFolder


# ---------------
# Main Batch Export Class
# ---------------


class fbxBatchExport(object):
    """Handles multiple batch FBX exporting
    """

    def __init__(self):

        self.outputPath = ""
        self.skeletonDefinition = True
        self.constraints = False
        self.tangents = True
        self.hardEdges = False
        self.smoothMesh = False
        self.smoothingGroups = True
        self.version = "FBX201800"
        self.shapes = True
        self.skins = True
        self.lights = False
        self.cameras = False
        self.animation = False
        self.startEndFrame = []
        self.ascii = False
        self.triangulate = True
        self.includeChildren = True
        self.axis = "Y"
        # if True then the scene will not be reset, good for debugging the output skeleton.
        self.debugScene = False
        # If True then scale attributes will be included in the export
        self.includeScale = True
        self.meshes = True
        # If True then if there's user errors/warnings etc then they will be shown in a popup dialog.
        self.interactive = False

    def exportFbxRigInstance(self, rigInstance):
        """FBX Exports a rig instance using the current settings.

        :param rigInstance: A Hive rig instance in the scene.
        :type rigInstance: :class:`hive.rig.Rig`
        """
        exporter = api.Configuration().exportPluginForId("fbxExport")()
        settings = exporter.exportSettings()
        settings.skeletonDefinition = self.skeletonDefinition
        settings.constraints = self.constraints
        settings.tangents = self.tangents
        settings.hardEdges = self.hardEdges
        settings.smoothMesh = self.smoothMesh
        settings.smoothingGroups = self.smoothingGroups
        settings.outputPath = self.outputPath  # The output path has no file extension, so no .fbx
        settings.version = self.version
        settings.shapes = self.shapes
        settings.skins = self.skins
        settings.lights = self.lights
        settings.cameras = self.cameras
        settings.animation = self.animation
        settings.startEndFrame = self.startEndFrame
        settings.ascii = self.ascii
        settings.triangulate = self.triangulate
        settings.includeChildren = self.includeChildren
        settings.axis = self.axis
        settings.meshes = self.meshes
        # Export the rig ----------------------
        exporter.execute(rigInstance, settings)

    def rigInstance(self, rigName, namespace=""):
        """From the rig name and namespace create a rig instance and start a session.

        Must be done before each export as the scene is reloaded each time.

        :param rigName: The Hive name of the rig to export ie "zoo_mannequin"
        :type rigName: str
        :param namespace: The optional namespace, used if multiples of the same rig and clashes.
        :type namespace: str
        :return: The rigInstance object
        :rtype: :class:`api.Rig`
        """
        if not api.rootByRigName(rigName, namespace):  # Doesn't exist
            if namespace:
                output.displayWarning("Rig `{}{}` not found".format(namespace, rigName))
            else:
                output.displayWarning("Rig `{}` not found".format(rigName))
            return None
        rigInstance = rig.Rig()
        if namespace:
            rigInstance.startSession(rigName, namespace=namespace)
        else:
            rigInstance.startSession(rigName, namespace="")
        return rigInstance

    def extractNameAndNamespace(self, rigName):
        """Given a "namespace:rigName" return the rigName and namespace, supports nested namespaces.

        :param rigNames: The Hive name to export, if namespace will be namespace:rigName
        :type rigNames: str
        :return: Rig name with no namespace and the namespace if one exists otherwise ":"
        :rtype: tuple(str, str)
        """
        if ":" not in rigName:
            return rigName, ""
        namespace = ":".join(rigName.split(":")[0:-1])
        rigName = rigName.split(":")[-1]
        if not namespace:
            namespace = ":"
        return rigName, namespace

    def pathWithNamespace(self, rigName, folderPath, namespace):
        """Helper function that builds the full path to the fbx file with no fbx extension.
        Removes the : from the namespaces if they exist.

        :param rigName: The Hive name of the rig
        :type rigName: str
        :param folderPath: The path to the save folder
        :type folderPath: str
        :param namespace: The namespace of the rig can be nested xxx:yyy
        :type namespace: str
        :return: The full path to the fbx file but with no extension c:/folder/namespace_rigName
        :rtype: str
        """
        newNamespace = str(namespace)
        if newNamespace.startswith(":"):
            newNamespace = str(newNamespace[1:])
        if not newNamespace:
            return os.path.join(folderPath, rigName)
        fileN = "_".join([newNamespace, rigName])
        return os.path.join(folderPath, fileN)

    def fileNameSetup(self, rigName, folderPath, namespace="", name="", prefixRigName=True):
        """Builds the full path name file name depending on the settings.  No file extension is added.

        prefixRigName = False means the rig will not be in the name

            c:/path/walk

        prefixRigName adds the rig name

            c:/path/rigName_walk

        namespace adds the namespace if prefixRigName is on

            c:/path/namespace_rigName_walk

        :param rigName: The Hive name of the rig to export ie "zoo_mannequin"
        :type rigName: str
        :param folderPath: The folder path to export to
        :type folderPath: str
        :param namespace: The namespace of the rig example "r1" or "" if no namespace clashes with other rigs
        :type namespace: str
        :param name: The name of the file if given, often the cycle name "walk" or "run"
        :type name: str
        :param prefixRigName: If True then the name will start with the rig name. If False then rigName is ignored.
        :type prefixRigName: bool
        :return: The full out path of one fbx file, not including the .fbx extension
        :rtype: str
        """
        if prefixRigName:
            if name:
                name = "{}_{}".format(rigName, name)
            else:  # No name given
                name = rigName
            outpath = self.pathWithNamespace(name, folderPath, namespace)
        else:
            outpath = self.pathWithNamespace(name, folderPath, "")
        return outpath

    # ---------------
    # Batch Multiple Rigs - Cinematics
    # ---------------

    def exportHiveRigNamesPaths(self, rigNames, outPaths, namespaces=None):
        """FBX export the rigNames to the outPaths with the given options.
        If multiple of the same rigs are in the scene then the namespaces must be provided to avoid clashes.

        :param rigNames: The Hive names of the rigs to export, if namespace will be namespace:rigName
        :type rigNames: list(str)
        :param outPaths: The full path of each file to save including the filename but without the .fxb extension
        :type outPaths: list(str)
        :param namespaces: Optional list of namespaces if multiple rigs in the scene to avoid clashes. None if ignored
        :type namespaces: list(str)
        :return: Exported full paths and exported short names with no file extension
        :rtype: tuple(list(str), list(str))
        """
        exportedFiles = list()
        exportedPaths = list()
        for i, rigName in enumerate(rigNames):
            rigInstance = self.rigInstance(rigName, namespace=namespaces[i])
            if not rigInstance:
                continue  # Error message already displayed
            self.outputPath = outPaths[i]
            self.exportFbxRigInstance(rigInstance)

            exportedPaths.append(outPaths[i])
            exportedFiles.append(os.path.basename(outPaths[i]))

        return exportedPaths, exportedFiles

    def exportHiveRigNames(self, rigNames, folderPath, fileOverrideList=None, nameSuffix="", message=True):
        """FBX exports a list of rig names to the given folder path.  Optional fileNames list can be given for names.

        Rig names are the Hive rig name ie "zoo_mannequin".
        If there are multiple rigs/clashing names in the scene, add the namespace ie "m1:zoo_mannequin"

        If nameSuffix= "shot05" then the name will be suffixed with the nameSuffix:

            zoo_mannequin_shot05.fbx

        FBX names are auto generated based on the rig name and namespace if a fileNames list is not given.

        If the namespace is given and fileNames is False, names will be named:

            m1:zoo_mannequin
            becomes
            m1_zoo_mannequin.fbx

        If no namespace is given and fileNames is False, names will be named:

            zoo_mannequin
            becomes
            zoo_mannequin.fbx

        :param rigNames: The Hive names of the rigs to export, if namespace will be namespace:rigName
        :type rigNames: list(str)
        :param folderPath: The full path of the folder to save the files
        :type folderPath: str
        :param fileOverrideList: Optional list of string names for the filenames, length of list must match the rigNames
        :type fileOverrideList: list(str)
        :param nameSuffix: Adds a suffix to the name eg zoo_mannequin.fbx becomes zoo_mannequin_shot05.fbx
        :type nameSuffix: str
        :param message: Report the export details in the script editor?
        :type message: bool
        :return: The full paths of the exported files
        :rtype: list(str)
        """
        outPaths = list()
        namespaces = list()

        if fileOverrideList and not len(rigNames) == len(fileOverrideList):
            output.displayWarning("The number of rig names and file names must match")
            return None

        for i, rigName in enumerate(rigNames):  # generate output paths and namespaces
            rigName, namespace = self.extractNameAndNamespace(rigName)
            rigNames[i] = rigName
            namespaces.append(namespace)
            nspace = str(namespace)
            name = str(rigName)
            if fileOverrideList:  # Don't use the rig name switch with the given file names
                name = fileOverrideList[i]
                nspace = ""
            outPaths.append(self.fileNameSetup(name,
                                               folderPath,
                                               namespace=nspace,
                                               name=nameSuffix,
                                               prefixRigName=True))

        # Export the files ------------------------------------
        exportedPaths, exportedFiles = self.exportHiveRigNamesPaths(rigNames,
                                                                    outPaths,
                                                                    namespaces=namespaces)
        if message:
            output.displayInfo("Exported {} to {}".format(exportedFiles, folderPath))

        return exportedPaths

    def exportHiveRigsSel(self, folderPath, nameSuffix="", cleanNamespaces=True, message=True):
        """FBX exports the selected rigs to the given folder path.  Any part of a rig can be selected, usually controls.

        FBX names are auto-generated based on the rig-name and namespace.

        If nameSuffix= "shot05" then the name will be suffixed with the nameSuffix:

            zoo_mannequin_shot05.fbx

        If cleanNamespaces is False name includes namespace.

            m1:zoo_mannequin
            becomes
            m1_zoo_mannequin.fbx

        If cleanNamespaces is True, then will attempt to remove namespaces if there are no rigName multiples in the scene.

            m1:zoo_mannequin
            becomes
            zoo_mannequin.fbx

        :param folderPath: The full path of the folder to save the files
        :type folderPath: str
        :param nameSuffix: Adds a suffix to the name eg zoo_mannequin.fbx becomes zoo_mannequin_shot05.fbx
        :type nameSuffix: str
        :param cleanNamespaces: If True will attempt to remove namespaces if there are no rigName multiples in the scene
        :type cleanNamespaces: bool
        :param message: Report the export details in the script editor?
        :type message: bool
        :return: The full paths of the exported files
        :rtype: list(str)
        """
        addNamespace = True
        outPaths = list()

        if not os.path.isdir(folderPath):
            output.displayWarning("The folder path `{}` does not exist, please create a folder or use "
                                  "another. ".format(folderPath))
            return None

        rigInstances, rigNames, rigNamespaces = rigsFromNodes(list(zapi.selected()))

        if not rigInstances:
            output.displayWarning("No rigs found in the selection")
            return None

        # Build the paths based off rig names and namespaces ---------------------
        if cleanNamespaces and len(rigNames) == len(set(rigNames)):  # Then there are no clashing rigs so all good
            addNamespace = False

        for i, rigName in enumerate(rigNames):  # generate output paths with filename no suffix .fbx is added later
            if not addNamespace:  # cull namespace as rig is unique
                rigNamespaces[i] = ""

            outPaths.append(self.fileNameSetup(rigName,
                                               folderPath,
                                               namespace=rigNamespaces[i],
                                               name=nameSuffix,
                                               prefixRigName=True))

        # Export the files ------------------------------------
        exportedPaths, exportedFiles = self.exportHiveRigNamesPaths(rigNames,
                                                                    outPaths,
                                                                    namespaces=rigNamespaces)

        if message:
            output.displayInfo("Exported {} to {}".format(exportedFiles, folderPath))

        return exportedPaths

    # ---------------
    # Batch Time Clips (cycles)
    # ---------------

    def exportHiveRigNameAnimClips(self, rigName, startEndFrames, outPaths, namespace=":"):
        """FBX export to a range of anim clip time ranges.  Requires all output paths to be given.
        Use other methods to auto generate out paths and filenames.

        If multiple of the same rigs are in the scene then the namespaces must be provided to avoid clashes.

        :param rigName: The Hive names of the rig to export
        :type rigName: str
        :param startEndFrames: A list of start end tuples for each time clip to export
        :type startEndFrames: list(tuple(float, float))
        :param outPaths: The full path of each file to save including the filename but without the .fxb extension
        :type outPaths: list(str)
        :param namespace: Optional list of namespaces if multiple rigs in the scene to avoid clashes. None if ignored
        :type namespace: list(str)
        :return: Exported full paths and exported short names with no file extension
        :rtype: tuple(list(str), list(str))
        """
        exportedFiles = list()
        exportedPaths = list()

        for i, startEndFrame in enumerate(startEndFrames):
            rigInstance = self.rigInstance(rigName, namespace)
            if not rigInstance:
                return list(), list()  # Error already reported

            self.startEndFrame = startEndFrame
            self.outputPath = outPaths[i]
            self.exportFbxRigInstance(rigInstance)

            exportedPaths.append(outPaths[i])
            exportedFiles.append(os.path.basename(outPaths[i]))

        return exportedPaths, exportedFiles

    def exportAnimBookmarksStartEnd(self, rigName, folderPath, fileOverrideList=None, prefixRigName=True, message=True):
        """FBX Exports a rig to FBX names of each bookmark matching its start/end frame.

        Files will be automatically named with the name of each timeslider bookmark:

            rigName_walkBookmark.fbx, rigName_runBookmark.fbx etc

        If namespace given in the name will be:

            namespace_rigName_walkBookmark.fbx, namespace_rigName_runBookmark.fbx etc

        Filenames can be overridden with another optional list of names:

            fileOverrideList = ["walkXX", "runXX"]
            "rigName_walkXX.fbx", "rigName_runXX".fbx"

        Rig names can be removed from the filename with prefixRigName=False:

            walkBookmark.fbx, runBookmark.fbx

        :param rigName: The Hive name of the rig to export, if namespace will be namespace:rigName
        :type rigName: str
        :param folderPath: The full path of the folder to save the files
        :type folderPath: str
        :param fileOverrideList: A list of file override names, must match the length of the timeslider bookmarks
        :type fileOverrideList: list(str)
        :param prefixRigName: Prefix the rig name to the file name? eg. zoo_mannequin_0_101.fbx
        :type prefixRigName: bool
        :param message: Report a message to the user?
        :type message: bool
        :return: All exported full paths to each fbx file
        :rtype: list(str)
        """
        outpathList = list()

        if not os.path.isdir(folderPath):
            output.displayWarning("The folder path `{}` does not exist, please create a folder or use "
                                  "another. ".format(folderPath))
            return None

        # Get the rigName and namespace ----------------
        rigName, namespace = self.extractNameAndNamespace(rigName)
        rigInstance = self.rigInstance(rigName, namespace)
        if not rigInstance:
            return list()  # Error message already displayed

        # Get bookmark data ----------------
        bookmarkNodes, bookmarkNames, startEndList = animbookmarks.allBookmarkTimeranges()

        if not bookmarkNodes:
            output.displayWarning("No animation bookmarks found in the scene, time ranges cannot be calculated")
            return list()

        if fileOverrideList and not len(bookmarkNodes) == len(fileOverrideList):
            output.displayWarning("The number of bookmark names and file override names must match")
            return None

        # Set the output full paths and name the files ----------------
        for i, startEnd in enumerate(startEndList):
            if not fileOverrideList:  # use the start end ie "0_101"
                name = bookmarkNames[i]
            else:  # Use the override name given ie "walk
                name = fileOverrideList[i]
            # Create the full path to the file with no extension
            outpathList.append(self.fileNameSetup(rigName,
                                                  folderPath,
                                                  namespace=namespace,
                                                  name=name,
                                                  prefixRigName=prefixRigName))

        exportedPaths, exportedFiles = self.exportHiveRigNameAnimClips(rigName,
                                                                       startEndList,
                                                                       outpathList,
                                                                       namespace=namespace)
        if message:
            output.displayInfo("Exported {} to {}".format(exportedFiles, folderPath))

        return exportedPaths

    def exportStartEndList(self, rigName, folderPath, startEndList, fileOverrideList=None, prefixRigName=True,
                           message=True):
        """FBX Exports a rig to multiple files given a list of start/end frames:

            startEndList = [(0, 101), (102, 134)]

        Files will be automatically named with the start/end frame:

            rigName_0_101.fbx, rigName_102_134.fbx etc

        If namespace given in the name will be:

            namespace_rigName_0_101.fbx, namespace_rigName_102_134.fbx etc

        Filenames can be overridden with another optional list of names:

            fileOverrideList = ["walk", "run"]
            "rigName_walk.fbx", "rigName_run.fbx"

        Rig names can be removed from the filename with prefixRigName=False:

            fileOverrideList = ["walk", "run"]
            walk.fbx, run.fbx

        :param rigName: The Hive name of the rig to export, if namespace will be namespace:rigName
        :type rigName: str
        :param folderPath: The full path of the folder to save the files
        :type folderPath: str
        :param startEndList: A list of start end tuples for each time clip to export [(0, 101), (102, 134)]
        :type startEndList: list(tuple(float, float))
        :param fileOverrideList: A list of file override names, must match the length of startEndList
        :type fileOverrideList: list(str)
        :param prefixRigName: Prefix the rig name to the file name? eg. zoo_mannequin_0_101.fbx
        :type prefixRigName: bool
        :param message: Report a message to the user?
        :type message: bool
        :return: All exported full paths to each fbx file
        :rtype: list(str)
        """
        outpathList = list()

        if not os.path.isdir(folderPath):
            output.displayWarning("The folder path `{}` does not exist, please create a folder or use "
                                  "another. ".format(folderPath))
            return None

        # Calculate the rigName and namespace ----------------
        rigName, namespace = self.extractNameAndNamespace(rigName)
        rigInstance = self.rigInstance(rigName, namespace)
        if not rigInstance:
            return list()  # Message already given

        if fileOverrideList and not len(startEndList) == len(fileOverrideList):
            output.displayWarning("The number of file ranges (startEnds) and file override names must match")
            return None

        # Set the output full paths and name the files ----------------
        for i, startEnd in enumerate(startEndList):
            if not fileOverrideList:  # use the start end ie "0_101"
                name = "{}_{}".format(numberToNiceStr(startEnd[0]), numberToNiceStr(startEnd[1]))
            else:  # Use the override name given ie "walk
                name = fileOverrideList[i]
            # Create the full path to the file with no extension
            outpathList.append(self.fileNameSetup(rigName,
                                                  folderPath,
                                                  namespace=namespace,
                                                  name=name,
                                                  prefixRigName=prefixRigName))
        exportedPaths, exportedFiles = self.exportHiveRigNameAnimClips(rigName,
                                                                       startEndList,
                                                                       outpathList,
                                                                       namespace=namespace)
        if message:
            output.displayInfo("Exported {} to {}".format(exportedFiles, folderPath))

        return exportedPaths
