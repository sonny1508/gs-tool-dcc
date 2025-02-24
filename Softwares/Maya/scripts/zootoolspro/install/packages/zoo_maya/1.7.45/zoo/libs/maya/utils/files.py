import contextlib
import os

from maya import cmds, mel
from maya.api import OpenMaya as om2
from zoovendor.six import string_types
from zoo.libs.maya.utils import general
from zoo.libs.maya.api import nodes
from zoo.libs.maya.api import plugs
from zoo.libs.maya.cmds.objutils import objhandling
from zoo.libs.maya.cmds.cameras import cameras
from zoo.libs.utils import filesystem, profiling, output
from zoo.core.util import zlogging

logger = zlogging.getLogger(__name__)


@contextlib.contextmanager
def exportContext(rootNode):
    changed = []
    for i in nodes.iterChildren(rootNode, recursive=True):
        dp = om2.MFnDependencyNode(i)
        plug = dp.findPlug("visibility", False)
        with plugs.setLockedContext(plug):
            if plug.asFloat() != 1.0:
                plugs.setPlugValue(plug, 1.0)
                changed.append(dp)
    yield
    for i in iter(changed):
        plug = i.findPlug("visibility", False)
        with plugs.setLockedContext(plug):
            plugs.setPlugValue(plug, 0.0)


@contextlib.contextmanager
def exportMultiContext(nodes):
    try:
        changed = []
        for i in nodes:
            dp = om2.MFnDependencyNode(i)
            plug = dp.findPlug("visibility", False)
            with plugs.setLockedContext(plug):
                if plug.asFloat() != 1.0:
                    plugs.setPlugValue(plug, 1.0)
                    changed.append(dp)
        yield
        for i in iter(changed):
            plug = i.findPlug("visibility", False)
            with plugs.setLockedContext(plug):
                plugs.setPlugValue(plug, 0.0)
    except RuntimeError:
        logger.error("Unknown Error Occurred during export",
                     exc_info=True)


def newScene(force=True):
    """Creates a new maya scene.

    :param force: Whether to force the creation of a new scene.
    :type force: bool
    :return: The name of the new scene usually "untitled".
    :rtype: str
    """
    return cmds.file(new=True, force=force)


@profiling.fnTimer
def saveScene(path, removeUnknownPlugins=False):
    logger.info("Saving new work File {}".format(path))
    maya_file_type = "mayaAscii"
    filesystem.ensureFolderExists(os.path.dirname(path))
    if removeUnknownPlugins:
        logger.debug("Cleaning unknownPlugins from scene if any")
        general.removeUnknownPlugins()
    cmds.file(rename=path)
    cmds.file(save=True, force=True, type=maya_file_type)
    logger.info("Finished saving work file")


@profiling.fnTimer
def openFile(path, selectivePreload=False, force=True, modified=False):
    """ Opens the maya file.

    :param path: The absolute path to the maya file
    :type path: str
    :param selectivePreload: If True the preload reference dialog will be shown if there's references
    :type selectivePreload: bool
    :param force: Force's a new scene
    :type force: bool
    :param modified: If True then the scene state will be set to True, this is the same \
    as cmds.file(modified=True)
    :type modified: bool
    """
    path = path.replace("\\", "/")
    logger.debug("Starting a new maya session")
    cmds.file(new=True, force=force)
    if selectivePreload:
        cmds.file(path, buildLoadSettings=True, open=True)
        # query the reference count in the file, result of 1 means no references so don't show the preload dialog
        if cmds.selLoadSettings(numSettings=True, q=True) > 1:
            cmds.optionVar(stringValue=('preloadRefEdTopLevelFile', path))
            cmds.PreloadReferenceEditor()
            return
    logger.debug("Starting a opening maya scene: {}".format(path))
    newNodes = cmds.ls(cmds.file(path, open=True, force=True, ignoreVersion=True, returnNewNodes=True),
                       long=True)
    cmds.file(modified=modified)
    logger.debug("completed opening maya scene: {}".format(path))
    return newNodes


@profiling.fnTimer
def importScene(filePath, force=True):
    return cmds.ls(cmds.file(filePath, i=True, force=force, returnNewNodes=True), long=True)


@profiling.fnTimer
def referenceFile(filePath, namespace=None):
    kwargs = dict(reference=True, loadReferencedDepth="all",
                  mergeNamespacesOnClash=False)
    if namespace is not None:
        kwargs["namespace"] = namespace
    logger.debug("Referencing scene")
    newNodes = cmds.ls(cmds.file(filePath,
                                 reference=True,
                                 loadReferenceDepth="all",
                                 mergeNamespacesOnClash=False,
                                 namespace=namespace,
                                 returnNewNodes=True),
                       long=True
                       )

    return newNodes


@profiling.fnTimer
def exportSceneAsFbx(filePath, skeletonDefinition=False, constraints=False):
    if not cmds.pluginInfo("fbxmaya", query=True, loaded=True):
        cmds.loadPlugin("fbxmaya")
    filePath = filePath.replace("/", "\\")
    mel.eval("FBXExportSmoothingGroups -v true;")
    mel.eval("FBXExportHardEdges -v false;")
    mel.eval("FBXExportTangents -v true;")
    mel.eval("FBXExportSmoothMesh -v false;")
    mel.eval("FBXExportInstances -v true;")
    # Animation
    mel.eval("FBXExportCacheFile -v false;")
    mel.eval("FBXExportBakeComplexAnimation -v false;")
    mel.eval("FBXExportApplyConstantKeyReducer -v true;")
    mel.eval("FBXExportUseSceneName -v false;")
    mel.eval("FBXExportQuaternion -v euler;")
    mel.eval("FBXExportShapes -v true;")
    mel.eval("FBXExportSkins -v true;")
    mel.eval("FBXExportConstraints -v {};".format("false" if not constraints else "true"))
    mel.eval("FBXExportSkeletonDefinitions -v {};".format("false" if not skeletonDefinition else "true"))
    mel.eval("FBXExportCameras -v true;")
    mel.eval("FBXExportLights -v true;")
    mel.eval("FBXExportEmbeddedTextures -v false;")
    mel.eval("FBXExportInputConnections -v true;")
    mel.eval("FBXExportUpAxis {};".format(general.upAxis()))
    mel.eval('FBXExport -f "{}";'.format(filePath.replace("\\", "/")))  # this maya is retarded
    return filePath


@profiling.fnTimer
def exportAbc(filePath, objectRootList=None, frameRange="1 1", visibility=True, creases=True, uvSets=True,
              autoSubd=True, dataFormat="ogawa", userAttr=None, userAttrPrefix=None, stripNamespaces=False,
              selection=False):
    """Exports and alembic file from multiple objects/transform nodes, could be multiple selected hierarchies for
     example objectRootList is the list of objects who's hierarchy is to be exported.

     .. note::
         Since the cmds.AbcExport does not support spaces in filepaths, this function saves in temp and then moves
         the file to the correct location.

    :param filePath: the full file path to save to.
    :type filePath: str
    :param objectRootList: a list of objects that are the root object, under each transform gets exported, None is scene.
    :type objectRootList: list
    :param frameRange: frame range (to and from) separated by a space.
    :type frameRange: str
    :param visibility: export visibility state?
    :type visibility: bool
    :param creases: export creases?  autoSubd needs to be on.
    :type creases: bool
    :param uvSets: export with uv sets?.
    :type uvSets: bool
    :param creases: export creases?  autoSubd needs to be on.
    :type creases: bool
    :param autoSubd: Must be on for crease edges, crease vertices or holes, mesh is written out as an OSubD.
    :type autoSubd: str
    :param userAttr: will export including Maya attributes with these custom strings in a list.
    :type userAttr: tuple
    :param userAttrPrefix: will export including Maya attributes with these prefix's, custom strings in a list.
    :type userAttrPrefix: tuple
    :param stripNamespaces: will strip the namespaces on export, if duplicated names it will fail.
    :type stripNamespaces: bool
    :param selection: will export selected nodes only, given they are under the root list.
    :type selection: bool
    """
    loadAbcPlugin(message=False)
    filePath = filePath.replace("/", "\\")
    fileName = os.path.split(filePath)[-1]
    tempDir = filesystem.getTempDir()  # needs temp dir as filepaths with spaces aren't supported
    tempPath = os.path.join(tempDir, fileName)
    command = "-frameRange {} -dataFormat {}".format(frameRange, dataFormat)
    if visibility:
        command += " -writeVisibility"
    if creases:
        command += " -writeCreases"
    if uvSets:
        command += " -writeUVSets"
    if objectRootList:
        for node in objectRootList:
            command += " -root {}".format(node)
    if autoSubd:
        command += " -autoSubd"
    if userAttr:
        userAttr = [userAttr] if not isinstance(userAttr, list) else userAttr
        for userAttrSingle in userAttr:
            command += " -userAttr {}".format(userAttrSingle)
    if userAttrPrefix:
        userAttrPrefix = [userAttrPrefix] if not isinstance(userAttrPrefix, list) else userAttrPrefix
        for userAttrPSingle in userAttrPrefix:
            command += " -userAttrPrefix {}".format(userAttrPSingle)
    if selection:
        command += " -selection"
    if stripNamespaces:
        command += " -stripNamespaces"
    command += ' -file {}'.format(tempPath)
    cmds.AbcExport(j=command)  # this will write to the temp directory
    fileNameFrom = os.path.join(tempDir, fileName)  # move from temp to actual path
    filesystem.moveFile(fileNameFrom, filePath)
    om2.MGlobal.displayInfo("Success Alembic Written: `{}`".format(filePath))
    return filePath


def getCamGeoRootsFromScene(exportGeo=True, exportCams=True, returnWorldRoots=True):
    """Returns the root objects of ge and cams (so that objects can't be doubled) top most node/s
    in a scene.  This is for .abc exporting where the root nodes need to be given and not doubled

    :param exportGeo: find roots of all geo in the scene?
    :type exportGeo: bool
    :param exportCams: find roots of all cameras in the scene?
    :type exportCams: bool
    :param returnWorldRoots: instead of returning the object roots, return the full scene roots, bottom of hierarchy
    :type returnWorldRoots: bool
    :return objectRootList: all root object names (objects can't be doubled) of the scene with cams or geo
    :rtype objectRootList: list
    """
    allCameraTransforms = list()
    allGeoTransforms = list()
    worldRootList = list()
    if exportGeo:  # get all geo
        allGeoShapes = cmds.ls(type='mesh', long=True)
        allGeoTransforms = objhandling.getListTransforms(allGeoShapes)
    if exportCams:  # get all cams
        allCameraTransforms = cameras.cameraTransformsAll()
    allTransforms = allCameraTransforms + allGeoTransforms
    objectRootList = objhandling.getRootObjectsFromList(allTransforms)
    if returnWorldRoots:
        for obj in objectRootList:
            worldRootList.append(objhandling.getTheWorldParentOfObj(obj))
        objectRootList = list(set(worldRootList))
    return objectRootList


@profiling.fnTimer
def exportAbcSceneFilters(filePath, frameRange="1 1", visibility=True, creases=True, uvSets=True,
                          dataFormat="ogawa", noMayaDefaultCams=True, exportGeo=True, exportCams=True,
                          exportAll=True, userAttr=None, userAttrPrefix=None):
    """Export alembic whole scene settings

    :param filePath: the full file path to save to
    :type filePath: str
    :param frameRange: frame range (to and from) separated by a space
    :type frameRange: str
    :param visibility: export visibility state?
    :type visibility: bool
    :param creases: export creases?  autoSubd needs to be on
    :type creases: bool
    :param uvSets: export with uv sets?
    :type uvSets: bool
    :param dataFormat: Alembic can save is a variety of formats, most commonly "ogawa"
    :type dataFormat: str
    :param noMayaDefaultCams: If True don't export Maya's default cams such as persp, top, side, front etc
    :type noMayaDefaultCams: bool
    :param exportGeo: Export geometry?
    :type exportGeo: bool
    :param exportCams: Export cameras?
    :type exportCams: bool
    :param exportAll: exports everything in the scene
    :type exportAll: bool
    :param userAttr: will export including Maya attributes with these custom strings in a list
    :type userAttr: tuple
    :param userAttrPrefix: will export including Maya attributes with these prefix's, custom strings in a list
    :type userAttrPrefix: tuple
    :return filePath:  the full file path to save the alembic
    :rtype filePath: str
    :return objectRootList: list of the root object to export, alembic requires root objects/transforms to export
    :rtype objectRootList: list(str)
    """
    if not exportGeo and not exportCams and not exportAll:
        om2.MGlobal.displayWarning("Alembic Nothing To Export")
        return "", list()
    if exportAll:  # get all roots in scene as still want to filter the default cameras maybe
        objectRootList = objhandling.getAllTansformsInWorld()
    else:  # get all roots of cam/geo if needed/wanted
        objectRootList = getCamGeoRootsFromScene(exportGeo=exportGeo, exportCams=exportCams)
    if noMayaDefaultCams:  # remove maya default cameras, front side etc
        mayaStartupCams = cameras.getStartupCamTransforms()
        objectRootList = [x for x in objectRootList if x not in mayaStartupCams]  # removes the maya cams from rootList
    # export the alembic
    if not objectRootList:
        om2.MGlobal.displayWarning("Alembic Nothing To Export")
        return "", list()
    filePath = exportAbc(filePath, objectRootList=objectRootList, frameRange=frameRange, visibility=visibility,
                         creases=creases, uvSets=uvSets, dataFormat=dataFormat, userAttr=userAttr,
                         userAttrPrefix=userAttrPrefix)
    return filePath, objectRootList


@profiling.fnTimer
def exportAbcSelected(filePath, frameRange="1 1", visibility=True, creases=True, uvSets=True,
                      dataFormat="ogawa", userAttr=None, userAttrPrefix=None):
    """Exports selected objects as alembic filetype .ABC and will auto load the plugin/s if not loaded
    Alembics export from the root, so filter the root of each selection hierarchy

    :param filePath: the full file path to save to
    :type filePath: str
    :param frameRange: frame range (to and from) separated by a space
    :type frameRange: str
    :param visibility: export visibility state?
    :type visibility: bool
    :param creases: export creases?
    :type creases: bool
    :param uvSets: export with uv sets?
    :type uvSets:
    :param dataFormat: abc format type, usually "ogawa"
    :type dataFormat: str
    :return:  the full file path to saved.
    :rtype: str
    """
    objectRootList = objhandling.getRootObjectsFromSelection()
    if not objectRootList:  # will have already reported the error
        return
    filePath = exportAbc(filePath, objectRootList, frameRange=frameRange, visibility=visibility, creases=creases,
                         uvSets=uvSets, dataFormat=dataFormat, userAttr=userAttr, userAttrPrefix=userAttrPrefix)
    return filePath, objectRootList


@profiling.fnTimer
def exportObj(filePath, sceneNode):
    if not cmds.pluginInfo("objExport", query=True, loaded=True):
        cmds.loadPlugin("objExport")
    filePath = filePath.replace("/", "\\")
    cmds.select(sceneNode)
    cmds.file(filePath, force=True, options="groups=0;ptgroups=0;materials=0;smoothing=1;normals=1", typ="OBJexport",
              pr=True,
              es=True)
    cmds.select(cl=True)
    return filePath


def loadAbcPlugin(message=True):
    """Loads the AbcImport and AbcExport plugins, also autoloads the alembic plugins

    :param message: Report the message to the user?
    :type message: bool
    """
    abcImportLoaded = cmds.pluginInfo("AbcImport", query=True, loaded=True)
    abcExportLoaded = cmds.pluginInfo("AbcExport", query=True, loaded=True)
    if abcImportLoaded and abcExportLoaded:  # both abc import and export loaded
        if message:
            om2.MGlobal.displayWarning("Abc Alembic Import/Export Plugins Already Loaded")
        return
    if not abcImportLoaded:
        cmds.loadPlugin("AbcImport")
    if not abcExportLoaded:
        cmds.loadPlugin("AbcExport")
    if message:
        om2.MGlobal.displayInfo("Abc Alembic Import/Export Plugins Now Loaded")


@profiling.fnTimer
def importAlembic(filePath, message=False):
    """Loads an alembic file (.ABC) and will auto load the plugin/s if not loaded

    :param filePath: The full filepath to the file
    :type filePath: str
    :param message: Report the message to the user?
    :type message: bool
    :return: the filepath loaded
    :rtype: str
    """
    currentSceneNodes = cmds.ls(long=True)
    loadAbcPlugin(message=message)  # ignores if already loaded
    cmds.AbcImport(filePath, mode="import")
    newNodes = set(cmds.ls(long=True)) - set(currentSceneNodes)
    return list(newNodes)


@profiling.fnTimer
def importObj(filePath):
    if not cmds.pluginInfo("objExport", query=True, loaded=True):
        cmds.loadPlugin("objExport")
    newNodes = cmds.ls(cmds.file(filePath, i=True, type="OBJ", ignoreVersion=True, mergeNamespacesOnClash=False,
                                 options="mo=1;lo=0",
                                 returnNewNodes=True),
                       long=True)
    return newNodes


@profiling.fnTimer
def importFbx(filepath, cameras=False, lights=False, skeletonDefinition=True, constraints=True):
    if not cmds.pluginInfo("fbxmaya", query=True, loaded=True):
        cmds.loadPlugin("fbxmaya")
    filepath = filepath.replace("/", "\\")
    mel.eval("FBXImportMode -v add;")
    mel.eval("FBXImportMergeAnimationLayers -v false;")
    mel.eval("FBXImportProtectDrivenKeys -v false;")
    mel.eval("FBXImportConvertDeformingNullsToJoint -v false;")
    mel.eval("FBXImportMergeBackNullPivots -v false;")
    mel.eval("FBXImportSetLockedAttribute -v true;")
    mel.eval("FBXExportConstraints -v {};".format("false" if not constraints else "true"))
    mel.eval("FBXExportSkeletonDefinitions -v {};".format("false" if not skeletonDefinition else "true"))
    mel.eval("FBXImportLights -v {};".format(str(lights).lower()))
    mel.eval("FBXImportCameras -v {};".format(str(cameras).lower()))
    mel.eval("FBXImportHardEdges -v true;")
    mel.eval("FBXImportShapes -v true;")
    mel.eval("FBXImportUnlockNormals -v true;")
    mel.eval('FBXImport -f "{}";'.format(filepath.replace("\\", "/")))  # stupid autodesk and there mel crap
    return True


@profiling.fnTimer
def exportFbx(filePath, exportNodes, skeletonDefinition=False, constraints=False, **kwargs):
    """
    :param filePath: The absolute file path
    :type filePath: str
    :param exportNodes:
    :type exportNodes: list or str
    :param skeletonDefinition:
    :type skeletonDefinition: bool
    :param constraints:
    :type constraints: bool
    :param kwargs:
    :type kwargs: dict
    :return:
    :rtype:
    """
    general.loadPlugin("fbxmaya")
    if isinstance(exportNodes, string_types):
        exportNodes = [exportNodes]
    upAxis = kwargs.get("FBXExportUpAxis", general.upAxis())
    # If baking required over a specific frame range, for subframes for example, then set them in kwargs.
    startFrame = kwargs.get("startFrame")
    endFrame = kwargs.get("endFrame")
    with exportMultiContext(map(nodes.asMObject, exportNodes)):
        mel.eval("FBXResetExport;")
        mel.eval("FBXExportSmoothingGroups -v {};".format("false" if not kwargs.get("smoothingGroups") else "true"))
        mel.eval("FBXExportHardEdges -v {};".format("false" if not kwargs.get("hardEdges") else "true"))
        mel.eval("FBXExportTangents -v {};".format("false" if not kwargs.get("tangents") else "true"))
        mel.eval("FBXExportSmoothMesh -v {};".format("false" if not kwargs.get("smoothMesh") else "true"))
        mel.eval("FBXExportInstances -v {};".format("false" if not kwargs.get("instances") else "true"))
        mel.eval("FBXExportTriangulate -v {}".format("false" if not kwargs.get("triangulate") else "true"))
        # Animation
        mel.eval("FBXExportCacheFile -v false;")
        mel.eval("FBXExportApplyConstantKeyReducer -v false;")
        mel.eval("FBXExportUseSceneName -v false;")
        mel.eval("FBXExportQuaternion -v resample;")
        mel.eval("FBXExportShapes -v {};".format("false" if not kwargs.get("shapes") else "true"))
        mel.eval("FBXExportSkins -v {};".format("false" if not kwargs.get("skins") else "true"))
        mel.eval("FBXExportConstraints -v {};".format("false" if not constraints else "true"))
        mel.eval("FBXExportSkeletonDefinitions -v {};".format("false" if not skeletonDefinition else "true"))
        mel.eval("FBXExportCameras -v {};".format("false" if not kwargs.get("cameras") else "true"))
        mel.eval("FBXExportLights -v {};".format("false" if not kwargs.get("lights") else "true"))
        mel.eval("FBXExportEmbeddedTextures -v {};".format("false" if not kwargs.get("textures") else "true"))
        mel.eval("FBXExportInputConnections -v {};".format("false" if not kwargs.get("inputConnections") else "true"))
        mel.eval("FBXExportUpAxis {};".format(upAxis))
        mel.eval("FBXExportBakeComplexAnimation -v {};".format("false" if not kwargs.get("animation") else "true"))
        mel.eval("FBXExportBakeResampleAnimation -v {};".format("false" if not kwargs.get("resample") else "true"))
        mel.eval("FBXExportBakeComplexStep -v {:f};".format(kwargs.get("step", 1.0)))
        mel.eval("FBXExportIncludeChildren -v {}".format("false" if not kwargs.get("includeChildren") else "true"))
        mel.eval("FBXExportInAscii -v {}".format("false" if not kwargs.get("ascii") else "true"))
        if startFrame is not None:
            mel.eval("FBXExportBakeComplexStart -v {:0.1f};".format(startFrame))
        if endFrame is not None:
            mel.eval("FBXExportBakeComplexEnd -v {:0.1f};".format(endFrame))
        mel.eval("FBXExportGenerateLog -v true")
        if kwargs.get("version"):
            # FBX version FBX202000 | FBX201900 | FBX201800
            mel.eval("FBXExportFileVersion -v {}".format(kwargs.get("version")))
        cmds.select(exportNodes)
        mel.eval('FBXExport -f "{}" -s;'.format(filePath.replace("\\", "/")))
        cmds.select(cl=True)

    return filePath


class ModFile(object):
    pluginPath = ''
    version = ''
    pluginName = ''
    scriptsPath = ''

    def __init__(self, path):
        """ Read mod file.

        Note: Not feature complete yet

        :param path:
        """
        self.path = path

        with open(path, 'r') as m:
            self._lines = m.readlines()

        self._readArgs()
        self._readScripts()
        self._readEnvPaths()

    def _readArgs(self):
        """ Read the args of the mod file (the first line with the '+')

        :return:
        """
        argLine = ""
        for l in self._lines:
            if l[0] == '+':
                argLine = l.replace("\n", '')
                break

        args = argLine.split(" ")

        versionIndex = -1
        version = ""
        name = ""
        for i, a in enumerate(args):
            if "." in a:
                version = a
                name = args[i - 1]
                versionIndex = i

        self.args = args[1:versionIndex - 2]

        # Join the path back together excluding the version and everything before it
        self.pluginPath = ' '.join(args[versionIndex + 1:])
        self.version = version
        self.pluginName = name

    def _readEnvPaths(self):
        # todo
        # https://help.autodesk.com/view/MAYAUL/2016/ENU/?guid=__files_GUID_130A3F57_2A5D_4E56_B066_6B86F68EEA22_htm
        pass

    def _readScripts(self):
        """ Read scripts file

        :return:
        """
        s = 'scripts:'

        for l in self._lines:
            try:
                if l.index(s) == 0:
                    self.scriptsPath = l[len(s):].strip()
            except ValueError:
                pass

    @property
    def resolvedScriptsPath(self):
        # todo
        raise NotImplementedError()
        return os.path.normpath(os.path.join(os.path.dirname(self.path), self.scriptsPath))


def mayaFileType(message=True):
    """ Returns the current Maya file type

    :return:
    """

    path = cmds.file(query=True, l=True)[0]
    if path.lower().endswith(".ma"):
        mayaType = "mayaAscii"
    elif path.lower().endswith(".mb"):
        mayaType = "mayaBinary"
    else:
        if message:
            output.displayWarning("This path has an unknown file type, not .ma or .mb")
        return

    return mayaType
