from zoo.core.plugin import plugin


class BaseBuildScript(plugin.Plugin):
    """Build scripting allows a user to run custom python code during each build stage.
    These build scripts will also be saved into the rigs configuration so when the
    rig loaded at a later time this scripts will be loaded once more.

    Each build script is setup as a plugin which will be discovered by hive when the
    hives configuration is loaded.

    """

    # unique identifier for the plugin which will be referenced by the registry.
    id = ""

    def __init__(self):
        super(BaseBuildScript, self).__init__()
        self._rig = None

    @staticmethod
    def properties():
        """Build script properties which will be passed to each method and provided
        to the buildScript UI Widget.

        Each property is described as a dict containing the necessary information for the UI
        to generate.

        .. Note::

            Only the following types are supported:
            #. filePath
            #. string
            #. boolean

        Example filePath property

        .. code-block:: python

            [{"name": "path", # the name for the property.
            "displayName": "", # The display name for the property.
             "value": "", # The python object which makes the type.
             "type": "filePath", # The type for the UI generation. currently only supports filePath.
             "layout": [0, 0], # The UI grid layout column,row.
             "toolTip": ""

             }
            ]

        When accessing the properties in pre/post methods it's simply `properties[propertyName]` which
        will return the value.
        When you need to set the properties you set it on the rig meta node like so

        .. code-block:: python

            rig.configuration.setBuildScriptConfig({"myBuildId": {"propertyName": "myValue"}})

        :return: A list of property dict
        :rtype: list
        """
        return []

    @classmethod
    def propertiesAsKeyValue(cls):
        """Returns the properties as a key value pair

        :return: A dict of properties
        :rtype: dict
        """
        return {prop["name"]: prop["value"] for prop in cls.properties()}

    @property
    def rig(self):
        """The current rig instance for the build

        :rtype: :class:`zoo.libs.hive.base.rig.Rig`
        """
        return self._rig

    @rig.setter
    def rig(self, rigInstance):
        """Sets the rig instance for the build script.

        .. Note::

            The build system will set this before the pre/post methods are called.

        :param rigInstance: The New rig instance.
        :type rigInstance: :class:`zoo.libs.hive.base.rig.Rig`
        """
        self._rig = rigInstance

    def delete(self):
        """Called When the build script is deleted from the rig
        """
        pass

    def preGuideBuild(self, properties):
        """Executed Before Any guide has been build on the rig"""
        pass

    def postGuideBuild(self, properties):
        """Executed once all guides on all components have been built into the scene."""
        pass

    def preDeformBuild(self, properties):
        """Executed before the deformation layer has been built or updated for all components.

        This is the ideal point in the process to export skin weights if the skeleton
        already exists.
        """
        pass

    def postDeformBuild(self, properties):
        """Executed after the deformation and I/O layers has been built for all components
        including all joints.

        This is ideal point in the process to reimport skin weights if necessary.
        """
        pass

    def preRigBuild(self, properties):
        """Executed before the rig Layer has been built for all components."""
        pass

    def postRigBuild(self, properties):
        """Executed after the rig Layer has been built for all components."""
        pass

    def postPolishBuild(self, properties):
        """Executed after the polish stage.

        Useful for building space switching, optimizing the rig, binding asset metadata and
        preparing for the animator.
        """
        pass

    def preDeleteGuideLayer(self, properties):
        """Executed before the guides of the rig gets deleted."""
        pass

    def preDeleteDeformLayer(self, properties):
        """Executed before the deform layer of the rig gets deleted.

        .. Note::

            This is pretty rare unless done directly through the API as we don't provide
            deletion currently to the end user.
        """

        pass

    def preDeleteRigLayer(self, properties):
        """Executed before the rig layer of the rig gets deleted."""
        pass

    def preDeleteComponents(self, properties):
        """Executed before all components gets deleted on the rig.

        .. Note::

            This method does get run when rig.deleteComponent get run use :func:`preDeleteComponent`

        """
        pass

    def preDeleteComponent(self, component, properties):
        """Executed before a single component gets deleted.

        .. Note::

            This method does get run when rig.deleteComponents get run use :func:`preDeleteComponents`

        """
        pass

    def preDeleteRig(self, properties):
        """Executed when the entire hive rig gets deleted.

        .. Note::

            :func:`preDeleteComponents` gets run before this method.

        """
        pass
