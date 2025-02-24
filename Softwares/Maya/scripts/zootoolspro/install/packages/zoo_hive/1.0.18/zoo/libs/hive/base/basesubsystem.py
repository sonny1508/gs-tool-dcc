from zoo.libs.hive.base.util import componentutils


class BaseSubsystem(object):
    """Base class for subsystems

    :param component: the Component instance that this subsystem is attached to.
    :type component: :class:`zoo.libs.hive.base.component.Component`
    """

    def __init__(self, component):
        self.component = component
        self.debugGraphs = False

    def active(self):
        """Returns whether the subsystem is active.

        :return: True if the subsystem is active, False otherwise.
        :rtype: bool
        """
        return True

    def createGraph(self, layer, namedGraphData, suffix=None):
        """Creates a graph for the component in the specified layer.

        :param layer: the layer in which to create the graph.
        :type layer: :class:`zoo.libs.hive.base.hivenodes.layers.HiveLayer`
        :param namedGraphData: the data for the named graph.
        :type namedGraphData: :class:`zoo.libs.hive.base.definition.NamedGraph`
        :param suffix: an optional suffix for the section name.
        :type suffix: str
        :return: the created graph.
        :rtype: :class:`zoo.libs.hive.base.component.ComponentGraph`
        """
        return componentutils.createGraphForComponent(
            self.component,
            layer,
            namedGraphData,
            track=True,
            sectionNameSuffix=suffix,
            createIONodes=self.debugGraphs,
        )

    def deleteGuides(self):
        """Deletes the guides in the subsystem."""
        pass

    def preAlignGuides(self):
        return [], []

    def postAlignGuides(self):
        """Performs post-alignment operations on the guides."""
        return

    def preUpdateGuideSettings(self, settings):
        """Performs pre-update operations on the guide settings.

        :param settings: The guide settings.
        :type settings: dict[str, any]
        :return: A tuple containing a boolean indicating whether a rebuild is required and a boolean indicating
                 whether the post-update operations should be executed.
        :rtype: tuple[bool, bool]
        """
        return False, False

    def postUpdateGuideSettings(self, settings):
        """Performs post-update operations on the guide settings.

        :param settings: The guide settings.
        :type settings: dict[str, any]
        :return: A boolean indicating whether a rebuild is required.
        :rtype: bool
        """
        return False

    def preSetupGuide(self):
        """Performs pre-setup operations on the guide."""
        pass

    def setupGuide(self):
        """Sets up the guide."""
        pass

    def postSetupGuide(self):
        """Performs post-setup operations on the guide."""
        pass

    def preMirror(self, translate, rotate, parent):
        """Performs pre-mirror operations.

        :param translate: The translation axis.
        :type translate: tuple[str]
        :param rotate: The rotation plane ie. 'xy'.
        :type rotate: str
        :param parent: The parent node.
        :type parent: :class:`zapi.DagNode`
        """
        pass

    def postMirror(self, translate, rotate, parent):
        """Performs post-mirror operations.

        :param translate: The translation vector.
        :type translate: tuple[float, float, float]
        :param rotate: The rotation vector.
        :type rotate: tuple[float, float, float]
        :param parent: the parent node.
        :type parent: :class:`zapi.DagNode`
        """
        pass

    def setupDeformLayer(self, parentJoint):
        """Sets up the deform layer.

        :param parentJoint: The parent joint.
        :type parentJoint: :class:`zapi.DagNode`
        """
        pass

    def postSetupDeform(self, parentNode):
        """Performs post-setup operations for the deformation.

        :param parentNode: The parent node.
        :type parentNode: :class:`zapi.DagNode`
        """

    def setupInputs(self):
        """Sets up the inputs."""
        pass

    def setupOutputs(self, parentNode):
        """Sets up the outputs.

        :param parentNode: The parent node.
        :type parentNode: :class:`zapi.DagNode`
        """
        pass

    def preSetupRig(self, parentNode):
        """Performs pre-setup operations for the rig.

        :param parentNode: The parent node.
        :type parentNode: :class:`zapi.DagNode`
        """
        pass

    def setupRig(self, parentNode):
        """Sets up the rig.

        :param parentNode: The parent node.
        :type parentNode: :class:`zapi.DagNode`
        """
        pass

    def postSetupRig(self, parentNode):
        """Performs post-setup operations for the rig.

        :param parentNode: The parent node.
        :type parentNode: :class:`zapi.DagNode`
        """
        pass
