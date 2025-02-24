import os
from zoo.libs.maya.mayacommand import command
from zoo.libs.hive import api
from zoo.libs.maya import zapi
from maya.api import OpenMaya as om2


class LoadFromTemplate(command.ZooCommandMaya):
    id = "hive.rig.create.template"
    
    isUndoable = True
    isEnabled = True
    useUndoChunk = True  # Chunk all operations in doIt()
    _rig = None
    _components = []
    _createdNewRig = False


    def resolveArguments(self, arguments):
        if not os.path.exists(arguments["templateFile"]):
            self.displayWarning("Template file doesn't exist: {}".format(arguments["templateFile"]))
            return
        self._rig = arguments.get("rig")
        return arguments

    def doIt(self, templateFile=None, name=None, rig=None):
        newRig, newComponents = api.loadFromTemplateFile(templateFile, name=name, rig=rig)
        newComponents = list(newComponents.values())
        if not newRig:
            return newRig, newComponents
        self._createdNewRig = True
        self._rig = newRig
        self._components = newComponents
        newRig.buildGuides()
        rootGuides = []
        for i in newComponents:
            if i.parent():
                continue
            root = i.guideLayer().guideRoot()
            if root is not None:
                rootGuides.append(root)
        if rootGuides:
            zapi.select(rootGuides)
        return newRig, newComponents

    def undoIt(self):
        if self._createdNewRig:
            self._rig.delete()
            return
        for comp in self._components:
            self._rig.deleteComponent(comp.name(), comp.side)


class SaveTemplate(command.ZooCommandMaya):
    """Saves the provide rig instance and components to the template library with the registered name.
    """
    id = "hive.rig.template.save"

    isUndoable = False
    isEnabled = True
    _rig = None


    def resolveArguments(self, arguments):
        self._rig = arguments.get("rig")
        if not self._rig or not isinstance(self._rig, api.Rig):
            self.displayWarning("Must supply a valid rig to save a template")
            return
        if not arguments.get("name"):
            self.displayWarning("Must supply a valid name for the template")
            return
        if not arguments.get("overwrite", True):
            registry = self._rig.configuration.templateRegistry()
            if registry.hasTemplate(arguments["name"]):
                self.displayWarning("Template already exists: {}".format(arguments["name"]))
                return
        return arguments

    def doIt(self, rig=None, name=None, components=None, overwrite=True, folderPath=None):
        """
        :param rig: The rig instance
        :type rig: :class:`api.Rig`
        :param name: The name for the template
        :type name: str
        :param components: A list of components to save, if None is provided then the full rig will be saved.
        :type components: list[:class:`api.Component`]
        """
        exporter = rig.configuration.exportPluginForId("hiveTemplate")()
        settings = exporter.exportSettings()
        settings.name = name
        settings.components = components
        settings.overwrite = overwrite
        settings.folderPath = folderPath
        path = exporter.export(rig, settings)
        om2.MGlobal.displayInfo("Finished saving template to: {}".format(path))
        return path


class DeleteTemplate(command.ZooCommandMaya):
    """Delete a Hive template based on the provided name
    """
    id = "hive.rig.template.delete"

    isUndoable = False
    isEnabled = True
    _rig = None

    _config = None

    def resolveArguments(self, arguments):
        templateName = arguments.get("name")
        self._config = api.Configuration()
        if not os.path.exists(self._config.templateRegistry().templatePath(templateName)):
            self.displayWarning("Template doesn't exist: {}".format(templateName))
            return
        return arguments

    def doIt(self, name=None):
        """
        :param name: the Template name to delete
        :type name: str
        """
        if self._config.templateRegistry().deleteTemplate(name):
            om2.MGlobal.displayInfo("Finished deleting template {}".format(name))
