from zoo.libs.maya.mayacommand import command
from zoo.libs.hive.base import rig as hiverig
from zoo.libs.hive import constants
from zoo.libs.maya import zapi


class BuildGuideCommand(command.ZooCommandMaya):
    """Builds the provided rig guide system
    """
    id = "hive.rig.global.buildGuides"

    isUndoable = True
    isEnabled = True
    _rig = None
    deletedRigs = False

    def resolveArguments(self, arguments):
        rig = arguments.get("rig")
        if rig is None or not isinstance(rig, hiverig.Rig):
            self.displayWarning("Must supply the rig instance to the command")
            return
        self._rig = rig
        return {"rig": rig}

    def doIt(self, rig=None, deleteRig=False):
        """

        :param rig: The rig Instance
        :type rig: :class:`rig.Rig`
        :return: The rig Instance
        :rtype: :class:`api.Rig`
        """
        zapi.clearSelection()
        if deleteRig:
            self.deletedRigs = deleteRig
            rig.deleteRigs()
        # purge the existing guides and rebuild this will allow for upgrading rigs automatically
        # and ensure a clean slate.
        if any(i.hasGuide() for i in rig.iterComponents()):
            rig.serializeFromScene()  # ensure we have the latest scene data before we delete the guides and update
            rig.deleteGuides()
        rig.buildGuides()
        rig.setGuideVisibility(constants.GUIDE_PIVOT_CONTROL_STATE,
                               False, True)
        rootGuides = []
        for comp in rig.iterComponents():
            comp.meta.attribute(constants.HASGUIDE_CONTROLS_ATTR).set(False)
            if not comp.hasParent():
                layer = comp.guideLayer()
                root = layer.guideRoot()
                if root:
                    rootGuides.append(root)
        zapi.clearSelection()

        if rootGuides:
            zapi.select(rootGuides)
        self._rig = rig
        return rig

    def undoIt(self):
        if self._rig.exists():
            if self.deletedRigs:
                self._rig.buildRigs()
            self._rig.deleteGuides()


class BuildGuidesControlsCommand(command.ZooCommandMaya):
    """Builds the provided rig guide  control system. Only rebuilds the guides if
    they don't exist otherwise the controls are just turned on
    """
    id = "hive.rig.global.buildGuidesControls"

    isUndoable = True
    isEnabled = True
    _rig = None
    deletedRigs = False


    def resolveArguments(self, arguments):
        rig = arguments.get("rig")
        if rig is None or not isinstance(rig, hiverig.Rig):
            self.displayWarning("Must supply the rig instance to the command")
            return
        self._rig = rig
        return {"rig": rig}

    def doIt(self, rig=None):
        """

        :param rig: The rig Instance
        :type rig: :class:`rig.Rig`
        :return: The rig Instance
        :rtype: :class:`api.Rig`
        """
        zapi.clearSelection()
        # ensure guides are built first, just in case the user was in polish or deleted
        for comp in rig.iterComponents():
            if not comp.hasGuide():
                rig.buildGuides()
                break
        rig.setGuideVisibility(constants.GUIDE_PIVOT_CONTROL_STATE,
                               True, True)
        for comp in rig.iterComponents():
            comp.meta.attribute(constants.HASGUIDE_CONTROLS_ATTR).set(True)
            comp.meta.attribute(constants.HASSKELETON_ATTR).set(False)

        zapi.clearSelection()

        self._rig = rig
        return rig

    def undoIt(self):
        if self._rig.exists():
            self._rig.setGuideVisibility(constants.GUIDE_PIVOT_CONTROL_STATE,
                                         False, True)
            for comp in self._.iterComponents():
                comp.meta.hasGuideControls.set(False)


class DeleteComponentGuideCommand(command.ZooCommandMaya):
    """Builds the component guides
    """
    id = "hive.component.guide.delete"
    isUndoable = False
    isEnabled = True
    _component = None

    def resolveArguments(self, arguments):
        super(DeleteComponentGuideCommand, self).resolveArguments(arguments)
        component = arguments.get("component")
        if not component.exists():
            self.displayWarning("The Component {} doesn't exist!".format(component.name()))
            return
        if not component.hasGuide():
            self.displayWarning("Component doesn't have a guide, canceling")
            return
        return {"component": component}

    def doIt(self, component=None):
        success = component.deleteGuide()
        if not success:
            raise ValueError("Failed to create hive component guides  {}".format(component.name()))
        self._component = component
        return success

    def undoIt(self):
        if self._component.exists():
            self._component.buildGuides()
