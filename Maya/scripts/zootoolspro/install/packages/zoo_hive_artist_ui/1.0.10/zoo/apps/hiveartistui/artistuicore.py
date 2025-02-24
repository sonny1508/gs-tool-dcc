from zoo.apps.hiveartistui import model
from zoo.apps.hiveartistui.model import ComponentModel
from zoo.apps.hiveartistui.registries import registry
from zoo.core.util import zlogging
from zoo.libs.hive import api
from zoo.libs.utils import profiling
from zoovendor.Qt import QtCore

logger = zlogging.getLogger(__name__)


class HiveUICore(QtCore.QObject):
    """The core backend for the HiveUI. Holds the RigModels and ComponentModels

    The UI queries the core to find out what is the current rig and what are its associated
    components.

    The UI interacts with this class to delete, add, and modify higher level aspects of
    the Rig and components. Works with RigModel and the ComponentModel to modify any data.

    Class breakdown:
    HiveUICore
        RigContainer (List of rigs)
            RigModel
            ComponentModels

        SelectionModel (Selected components so other UI elements can use, like the ToolBar Buttons)
    """

    rigAdded = QtCore.Signal()
    rigRenamed = QtCore.Signal()
    rigDeleted = QtCore.Signal()
    currentRigChanged = QtCore.Signal(str)
    rigsChanged = QtCore.Signal()

    def __init__(self, componentRegistry, toolRegistry, uiInterface):
        """

        :param componentRegistry:
        :type componentRegistry:
        :param toolRegistry:
        :type toolRegistry: zoo.apps.hiveartistui.registries.toolregistry.ToolRegistry
        :type uiInterface: zoo.apps.hiveartistui.uiinterface.UiInterface
        """

        super(HiveUICore, self).__init__()
        self.rigs = []  # type: list[RigContainer]
        self.currentRigContainer = None  # type: RigContainer
        self.toolRegistry = toolRegistry
        self.uiInterface = uiInterface
        self.uiInterface.setCore(self)
        self.componentRegistry = componentRegistry
        self.componentMdlRegistry = registry.ComponentModelRegistry(componentRegistry)
        self.componentMdlRegistry.discoverComponents()
        self.selection = SelectionModel()

    def setGroupName(self, item, name):
        return name

    def hasRig(self):
        return self.currentRigContainer is not None

    def currentRigExists(self):
        return bool(self.currentRigContainer and self.currentRigContainer.rigExists())

    def artistUi(self):
        """

        :return:
        :rtype: zoo.apps.hiveartistui.artistui.HiveArtistUI
        """
        return self.uiInterface.artistUi()

    def addRig(self, name=None, setCurrent=True):
        """
        Creates a new rig by name and
        :param name:
        :param setCurrent:
        :return:
        """
        r = self.executeTool("createRig", dict(name=name))
        if not r:
            return
        # create a rigModel instance which will be bound to the hive instance once create() is called
        newRig = model.RigModel(r)
        rc = RigContainer(newRig)
        self.rigs.append(rc)
        if setCurrent:
            self.currentRigContainer = rc
        self.rigAdded.emit()

        return newRig

    def rigNames(self):
        """
        Returns all the rig names as a list of strings

        :return:
        :rtye: list(basestring)
        """
        return [r.rigModel.name for r in self.rigs]

    def setComponentRegistry(self, componentRegistry):
        self.componentRegistry = componentRegistry

    def setCurrentRigByName(self, rigName):
        """Set rig by name

        :param rigName:
        :type rigName: basestring
        :return:
        :rtype:
        """
        r = self.getRigContainerByName(rigName)
        if r is not None:
            self.currentRigContainer = r  # type: RigContainer
            self.selection.rigModel = self.currentRigContainer.rigModel
            self.currentRigChanged.emit(rigName)

        return self.currentRigContainer.rigModel

    def rigMode(self):
        """Returns Mode "Guides", "Skeleton" "Rig" ,

        :return:
        :rtype:
        """
        if self.currentRigContainer is None or not self.currentRigContainer.rigExists():
            return
        return self.currentRigContainer.rigModel.rig.buildState()

    def setCurrentRig(self, newRig):
        """Set rig as the current rig.

        :param newRig:
        :type newRig: registry.RigModel
        :return:
        :rtype: registry.RigModel

        """
        r = self.getRigContainerByModel(newRig)
        self.currentRigContainer = r  # type: RigContainer

        self.selection.rigModel = self.currentRigContainer.rigModel
        self.currentRigChanged.emit(r.rigModel.name)
        return self.currentRigContainer.rigModel

    def addComponent(
        self, componentType, componentName=None, side=None, definition=None
    ):
        """Add Component

        Creates a new ComponentModel based on the type and name and
        adds into the scene.

        :param componentType:
        :param componentName:
        :param side:
        :return:
        """
        if not self.currentRigContainer:
            return
        compModel, componentType = self.componentMdlRegistry.findComponentModel(
            componentType
        )

        if compModel:
            self.executeTool(
                "createComponent",
                dict(
                    componentType=componentType,
                    name=componentName,
                    side=side,
                    definition=definition,
                ),
            )

    def loadFromTemplate(self):
        """Load from template"""
        self.executeTool("loadFromTemplate")

    def componentModelHash(self, componentModel):
        """Get the hash of the ComponentModel

        :param componentModel:
        :return:
        """
        return hash(componentModel)

    def componentModelByHash(self, componentHash):
        """
        Get the ComponentModel by hash.

        :param componentHash:
        :return:
        :rtype: model.ComponentModel
        """
        componentHash = int(componentHash)
        return self.currentRigContainer.componentModels[componentHash]

    def deleteComponent(self, component):
        # TODO
        """Might want to put this in rig.Rig(), a method to delete by reference"""
        self.currentRigContainer.deleteComponent(component)
        self.artistUi().componentRemoved()

    def deleteRig(self, rig):
        """
        Deletes rig from the UI and Hive by RigModel.

        :param rig:
        :type rig: model.RigModel or RigContainer
        :return:
        """

        if isinstance(rig, model.RigModel):
            for r in self.rigs:
                if r.rigModel == rig:
                    self.rigs.remove(r)
                    rig.delete()
                    self.rigDeleted.emit()
                    break

        elif isinstance(rig, RigContainer):
            for r in self.rigs:
                if r == rig:
                    self.rigs.remove(r)
                    rig.rigModel.delete()
                    self.rigDeleted.emit()
                    break

        return

    @profiling.fnTimer
    def executeTool(self, toolId, args=None):
        """Execute Hive tool

        :param toolId:
        :type toolId:
        :param args:
        :type args:
        :return:
        :rtype:
        """

        ids = toolId.split(".")
        variantId = None
        if len(ids) > 1:
            variantId = ids[1]
            toolId = ids[0]
        tool = self.toolRegistry.plugin(toolId=toolId)(logger, self.uiInterface)
        if tool is not None:
            args = args or {}
            if variantId:
                args["variant"] = variantId

            tool.setSelected(self.selection)
            logger.debug("Executing HiveTool: {}".format(tool.id))
            tool.refreshRequested.connect(self.uiInterface.refreshUi)
            return tool.process(variantId=variantId, args=args)

    def setSelectedComponents(self, componentModels):
        """Set currently selected component models. Usually run by the ComponentTreeWidget.

        :param componentModels:
        :type componentModels: list(model.ComponentModel)
        :return:
        """
        self.selection.componentModels = componentModels

    def getRigContainerByName(self, name):
        """
        Gets the RigContainer by name string
        :param name:
        :type name: basestring
        :return:
        :rtype: RigContainer
        """
        for r in self.rigs:
            if r.rigModel.name == name:
                return r

    def getRigByName(self, name):
        """
        Gets the RigModel by name string
        :param name:
        :type name: basestring
        :return:
        :rtype: model.RigModel
        """
        for r in self.rigs:
            if r.rigModel.name == name:
                return r.rigModel.rig

    def getRigModelByName(self, name):
        """Get rig model by string name
        :param name:
        :type name: basestring
        :return:
        :rtype: model.RigModel
        """
        for r in self.rigs:
            if r.rigModel.name == name:
                return r.rigModel

    def getRigByModel(self, rigModel):
        """Get hive rig by RigModel

        :param rigModel:
        :type rigModel: model.RigModel
        :return:
        :rtype: hive.zoo.libs.hivebase.rig.Rig
        """
        for r in self.rigs:
            if r.rigModel == rigModel:
                return r

    def getRigContainerByModel(self, rigModel):
        """Get hive rig by RigModel

        :param rigModel:
        :type rigModel: model.RigModel
        :return:
        :rtype: hive.zoo.libs.hivebase.rig.Rig
        """
        for r in self.rigs:
            if r.rigModel == rigModel:
                return r

    def createComponentModel(self, component, rigContainer):
        """Create a new component model from component

        :param rigContainer:
        :type rigContainer: RigContainer
        :param component:
        :return:
        """
        if component:
            componentType = component.componentType
            ModelClass, Type = self.componentMdlRegistry.findComponentModel(
                componentType
            )
            if not ModelClass:
                compModel = ComponentModel(component, rigContainer.rigModel)
                compModel.componentType = Type
            else:
                compModel = ModelClass(component, rigContainer.rigModel)
            return compModel

    def components(self):
        """
        Return list of the current rig's list of component models
        :return:
        :rtype: list(model.ComponentModel)
        """
        return self.currentRigContainer.rigModel.componentModels()

    def refresh(self):
        """Find all rigs in scene and reconstruct the UI with the components and widgets

        This is a pretty expensive process so we don't want to do it too often.
        (Unless we optimize the way the components are added into the scene here)
        :return:
        """
        logger.debug("Refreshing UI Core")
        self.rigs = []

        # todo: replace for a model method to avoid hive api code
        # Generates all the component models in the scene, maybe slow
        for r in api.iterSceneRigs():
            rc = RigContainer(model.RigModel(r))

            for c in r.iterComponents():
                componentModel = self.createComponentModel(c, rc)
                rc.addComponentModel(componentModel)

            self.rigs.append(rc)
        if not self.rigs:
            self.currentRigContainer = RigContainer(None)
        self.rigsChanged.emit()

    def needsRefresh(self):
        """A relatively low cost way of checking if the ui needs refreshing.

        O(n) Speed for n number of rigs.

        :return: Returns true if ui needs refreshing
        :rtype: bool
        """
        # Number of rigs in scene vs rigs in core should be the same
        logger.debug("Determining if UI requires refresh")
        rigMetas = list(api.iterSceneRigMeta())
        if len(rigMetas) != len(self.rigs):
            logger.debug(
                "Number of scene rigs doesn't match number of UI rigs, requires Refresh"
            )
            return True

        for m in rigMetas:
            container = self.containerByRigMeta(m)
            if (
                not container
            ):  # cant find matching container, which means it is out of sync
                logger.debug(
                    "Number of scene rigs doesn't match number of UI rigs, requires Refresh"
                )
                return True
            layer = m.componentLayer()
            if not layer:
                return False
            # Components and component models don't match in number?
            if len(m.componentLayer().components()) != len(
                container.rigModel.componentModels()
            ):
                logger.debug(
                    "Number of scene rigs doesn't match number of UI rigs, requires Refresh"
                )
                return True

        logger.debug("UI doesn't require a refresh")
        return False

    def containerByRig(self, rig):
        """

        :param rig:
        :type rig: zoo.libs.hive.base.rig.Rig
        :return:
        :rtype: :class:`RigContainer`
        """
        for c in self.rigs:
            if c.rigModel.rig == rig:
                return c

    def containerByRigMeta(self, rigMeta):
        """Find Rig container by its meta

        :param rigMeta:
        :return:
        :rtype: :class:`RigContainer`
        """
        for c in self.rigs:
            if c.rigModel.meta == rigMeta:
                return c

    def buildGuides(self):
        """
        Build guides for the current rig
        :return:
        """
        if not self.currentRigContainer:
            return
        logger.debug(
            "Attempting to build component guideLayer for rig: {}".format(
                self.currentRigContainer.rigModel.name
            )
        )
        self.executeTool("buildGuides")

    def toggleGuideControls(self, state=None):
        if not self.currentRigContainer:
            return
        logger.debug(
            "Attempting to toggle guide controls for rig: {}".format(
                self.currentRigContainer.rigModel.name
            )
        )
        self.executeTool("buildGuideControls")

    def buildRigs(self):
        """
        Build current rig
        :return:
        """
        if not self.currentRigContainer:
            return
        logger.debug(
            "Attempting to build component rigLayer for rig: {}".format(
                self.currentRigContainer.rigModel.name
            )
        )
        self.executeTool("buildRig")

    def buildSkeleton(self):
        """
        build current skeleton
        :return:
        """
        if not self.currentRigContainer:
            return
        logger.debug(
            "Attempting to build skeleton components for rig: {}".format(
                self.currentRigContainer.rigModel.name
            )
        )
        self.executeTool("buildSkeleton")

    def polishRig(self):
        if not self.currentRigContainer:
            return
        logger.debug(
            "Attempting to polish rig: {}".format(
                self.currentRigContainer.rigModel.name
            )
        )
        self.executeTool("polishRig")


class RigContainer(QtCore.QObject):
    """
    Container that holds a RigModel and its related ComponentsModels in one object.
    Sort of like an outer Model for the RigModels and ComponentsModels, but put in hashes
    for speedy queries
    """

    def __init__(self, rigModel, componentModels=None):
        """

        :param rigModel:
        :type rigModel: :class:`zoo.apps.hiveartistui.model.RigModel`
        :param componentModels:
        :type componentModels: list[:class:`zoo.apps.hiveartistui.model.ComponentModel`]
        """
        self.rigModel = rigModel
        self.componentModels = componentModels or {}
        super(RigContainer, self).__init__()

    def addComponentModel(self, componentModel):
        """Add componentModel to the rig model.

        Does this by adding to the dictionary with the hash as the key.

        dict[componentHash] = componentModel

        :param componentModel:
        :type componentModel: :class:`zoo.apps.hiveartistui.model.ComponentModel`
        :return:
        """

        self.componentModels[hash(componentModel)] = componentModel
        self.rigModel.addComponentModel(componentModel)

    def deleteComponent(self, componentModel):
        """Removes the componentModel from the rigModel
        :param componentModel:
        :return:
        """
        self.rigModel.deleteComponent(componentModel)
        self.componentModels.pop(hash(componentModel))

    def delete(self):
        """

        :return:
        :rtype:
        """
        if self.rigModel is not None:
            self.rigModel.delete()
            self.rigModel = None
            self.componentModels = {}

    def rigExists(self):
        """Rig exists

        :return:
        :rtype:
        """
        return self.rigModel and self.rigModel.exists()


class SelectionModel(QtCore.QObject):
    """The selection model for selections of components in the main ComponentTreeWidget.
    Mainly to be used to send to other ui operations such as the ToolBar buttons if they
    require whatever component or rig is selected in the UI.

    """

    def __init__(self):
        self.rigModel = None  # type: model.RigModel
        self.componentModels = []  # type: list[model.ComponentModel]
