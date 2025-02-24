from zoo.apps.hiveartistui.views import componentsettings
from zoo.core.util import zlogging
from zoo.libs.commands import hive
from zoo.libs.utils import profiling
from zoovendor.Qt import QtCore, QtGui


logger = zlogging.getLogger(__name__)


class RigModel(QtCore.QObject):
    def __init__(self, rig=None):
        """ Rig Model

        :param rig:
        :type rig: zoo.libs.hive.base.rig.Rig
        """
        super(RigModel, self).__init__(parent=None)

        self._componentModels = []  # type: list[ComponentModel]
        self.rig = rig

    @property
    def configuration(self):
        return self.rig.configuration

    @property
    def name(self):
        """

        :return:
        :rtype: str
        """
        return self.rig.name()

    @name.setter
    def name(self, newName):
        hive.renameRig(self.rig, newName)

    @property
    def meta(self):
        return self.rig.meta

    def exists(self):
        return self.rig is not None and self.rig.exists()

    @profiling.fnTimer
    def deleteComponent(self, componentModel):
        if componentModel in self._componentModels:
            hive.deleteComponents(rig=self.rig, components=[componentModel.component])
            self._componentModels.remove(componentModel)
            return True
        return False

    # todo: replace as tool classes
    @profiling.fnTimer
    def duplicateComponent(self, componentModel, name, side):
        """
        :param componentModel:
        :type componentModel: :class:`ComponentModel`
        :return:
        :rtype: ComponentModel
        """
        parents = componentModel.parent()
        newComponents = hive.duplicateComponents(rig=self.rig,
                                                 sources=[{"component": componentModel.component,
                                                           "name": name,
                                                           "side": side,
                                                           "parent": parents[0] if parents else None}])
        self._componentModels.extend(ComponentModel(nc, self) for nc in newComponents)
        return newComponents

    @profiling.fnTimer
    def componentModels(self):
        """

        :return:
        :rtype: list[:class:`ComponentModel`]
        """
        return self._componentModels

    @profiling.fnTimer
    def addComponentModel(self, componentModel):
        """
        Add component model to the _uiComponents list
        :param componentModel:
        :return:
        """
        self._componentModels.append(componentModel)

    @profiling.fnTimer
    def component(self, name, side):
        """
        Get the component by name and side
        :return:
        """
        for comp in iter(self._componentModels):
            if comp.name == name and comp.side == side:
                return comp

    @profiling.fnTimer
    def delete(self):
        hive.deleteRig(rig=self.rig)


class ComponentModel(QtCore.QObject):
    componentType = ""

    parentChanged = QtCore.Signal(object, object)

    def __init__(self, component=None, rigModel=None):
        """ Component Model for the ui


        :param component:
        :type component: zoo.libs.hive.base.component.Component
        :type rigModel: :class:`RigModel`
        """
        self.rigModel = rigModel
        self.component = component
        self.hidden = False
        # helper for passing a central logger to each subclass
        self.logger = logger
        super(ComponentModel, self).__init__()

    def icon(self):
        return QtGui.QIcon()

    @property
    def componentIcon(self):
        uiData = self.component.uiData
        if uiData["icon"]:
            return uiData["icon"]
        return self.component.icon

    @property
    def name(self):
        return self.component.name()

    @name.setter
    def name(self, newName):
        if self.component.name() == str(newName):
            return
        hive.renameComponent(self.component, newName)

    @property
    def side(self):
        return self.component.side()

    @side.setter
    def side(self, newSide):
        if self.component.side() == str(newSide):
            return
        hive.setComponentSide(component=self.component, side=newSide)

    def parent(self):
        return self.component.parent()

    def isHidden(self):
        return self.component.isHidden()

    def hasGuide(self):
        return self.component.hasGuide()

    def hasRig(self):
        return self.component.hasRig()

    def displayName(self):
        return " ".join((self.name, self.side))

    def toolLayout(self):
        # return ["toggleComponentVisibility", "soloComponent", "toggleGuides", "toggleRigs"] # todo: reimplement these
        return []

    def menuActions(self):

        return ["selectInScene", "---",
                "toggleBlackToggle", "---",
                "toggleLra", "---",
                "duplicateComponent",
                "mirrorComponents",
                "applySymmetry",
                "---",
                "deleteComponent"
                ]

    def createWidget(self, componentWidget, parentWidget):
        return componentsettings.ComponentSettingsWidget(componentWidget,
                                                         parentWidget,
                                                         componentModel=self)
