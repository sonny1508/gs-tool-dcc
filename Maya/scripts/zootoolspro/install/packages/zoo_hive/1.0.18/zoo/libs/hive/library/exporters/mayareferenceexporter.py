from zoo.libs.hive import api
from zoo.core.util import zlogging
from zoo.libs.maya import zapi
from zoo.libs.maya.cmds.filemanage import saveexportimport
from zoo.libs.maya.utils import files

from maya import cmds
from zoo.libs.utils import output

logger = zlogging.getLogger(__name__)


class MayaRefExportSettings(object):
    """Maya reference exporter settings.
    """

    def __init__(self):
        # The output path to use  should end in .ma or .mb
        self.outputPath = ""
        # if True then the scene will not be reset, good for debugging the output skeleton.
        self.debugScene = False
        # if True then the current rig configuration will be updated
        self.updateRig = False
        # The build script settings to update if updateRig is Set
        self.buildScriptProperty = {"script": "mayaReference", "property": "filePath"}


class MayaRefExporterPlugin(api.ExporterPlugin):
    """Export Plugin for skeletal and geometry maya referencing.
    """
    id = "mayaReference"

    def exportSettings(self):
        """Returns the Export Settings for this exporter Plugin.

        :rtype: :class:`MayaRefExportSettings`
        """
        return MayaRefExportSettings()

    def export(self, rig, exportOptions):
        """

        :param rig:
        :type rig: :class:`zoo.libs.hive.base.rig.Rig`
        :param exportOptions:
        :type exportOptions: :class:`MayaRefExportSettings`
        :return:
        :rtype:
        """

        components = [comp for comp in rig.iterComponents()]
        if not any(comp.hasSkeleton() for comp in components):
            output.displayError("Missing Skeleton please build the skeleton before exporting.")
            return
        rigName = rig.name()
        currentScenePath = saveexportimport.currentSceneFilePath()
        self.onProgressCallbackFunc(10, "Apply Hive MetaData to skeleton")
        api.skeletonutils.applySkeletalMetaData(rig)
        self.onProgressCallbackFunc(25, "Organising current scene for export")
        geoLayer = rig.geometryLayer()
        deformLayer = rig.deformLayer()
        geoRoot = None
        if geoLayer is not None:
            geoRoot = geoLayer.rootTransform()
            geoLayer.attribute(api.constants.ROOTTRANSFORM_ATTR).disconnectAll()
        deformRoot = deformLayer.rootTransform()

        if geoRoot:
            geoRoot.lock(False)
            geoRoot.setParent(None)

        for comp in components:
            compDeform = comp.deformLayer()
            compDeform.disconnectAllJoints()

        skelRoots = list(deformRoot.iterChildren(recursive=False, nodeTypes=(zapi.kJoint,)))
        api.skeletonutils.cleanSkeletonBeforeExport(skelRoots)
        # remove the rig in the scene without deleting the joints. This creates a clean FBX file.
        # note: we reopen the scene at the end

        rig.delete()

        self.onProgressCallbackFunc(50, "Exporting Rig as ma")
        exportNodes = skelRoots
        if geoRoot is not None:
            exportNodes.append(geoRoot)
        zapi.select(exportNodes)
        logger.info("Exporting skeleton rig to: {}".format(exportOptions.outputPath))
        cmds.file(exportOptions.outputPath,
                  force=True,
                  options="v=0;",
                  type="mayaAscii",
                  constraints=False,
                  preserveReferences=False,
                  exportSelected=True,
                  constructionHistory=True,
                  channels=False,
                  exportAnim=False
                  )
        self.onProgressCallbackFunc(75, "Finished exporting, starting cleanup")
        if exportOptions.debugScene:
            return
        files.openFile(currentScenePath)

        if not exportOptions.updateRig:
            return

        rigMeta = api.rootByRigName(rigName)
        if not rigMeta:
            output.displayError("Unable to find rig after opening the file")
            return

        rig = api.Rig(meta=rigMeta)

        currentBuildState = rig.buildState()
        buildScriptId = exportOptions.buildScriptProperty["script"]
        buildScriptProperty = exportOptions.buildScriptProperty["property"]

        if not rig.configuration.addBuildScript(buildScriptId):
            output.displayError("Missing build script: {}".format(buildScriptId))
            return
        self.onProgressCallbackFunc(90, "Updating Rig with new reference: {}".format(exportOptions.outputPath))
        rig.configuration.updateBuildScriptConfig(rig, {
            buildScriptId: {buildScriptProperty: exportOptions.outputPath}
        })
        rig.saveConfiguration()

        api.commands.buildDeform(rig)
        if currentBuildState != api.constants.SKELETON_STATE:
            if currentBuildState == api.constants.RIG_STATE:
                api.commands.buildRigs(rig)
            elif currentBuildState == api.constants.POLISH_STATE:
                api.commands.polishRig(rig)
