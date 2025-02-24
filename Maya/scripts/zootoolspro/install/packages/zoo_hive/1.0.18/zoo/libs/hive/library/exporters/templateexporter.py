from zoo.libs.hive import api
from zoo.libs.utils import output


class TemplateExportSettings(object):
    def __init__(self):
        self.name = ""
        self.overwrite = True
        self.components = []
        self.displayErrors = False
        self.folderPath = None


class TemplateExporterPlugin(api.ExporterPlugin):
    id = "hiveTemplate"

    def exportSettings(self):
        return TemplateExportSettings()

    def displayWarning(self, message):
        output.displayWarning(message)

    def export(self, rig, exportOptions):
        """Exports the Hive Rig as a template

        :param rig: The rig instance to export
        :type rig: :class:`zoo.libs.hive.base.rig.Rig`
        :param exportOptions:
        :type exportOptions: :class:`TemplateExportSettings`
        :return: The file path to the exported template
        :rtype: str
        """
        if not rig or not isinstance(rig, api.Rig):
            self.displayWarning("Must supply a valid rig to save a template")
            return
        if not exportOptions.name:
            self.displayWarning("Must supply a valid name for the template")
            return
        if not exportOptions.overwrite:
            registry = rig.configuration.templateRegistry()
            if registry.hasTemplate(exportOptions.name):
                self.displayWarning("Template already exists: {}".format(exportOptions.name))
                return

        data = rig.serializeFromScene(components=exportOptions.components)
        path = rig.configuration.templateRegistry().saveTemplate(exportOptions.name,
                                                                 data,
                                                                 overwrite=exportOptions.overwrite,
                                                                 templateRootPath=exportOptions.folderPath)
        return path
