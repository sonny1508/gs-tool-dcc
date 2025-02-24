"""Hive post buildscript template.  Blueprint for creating Hive buildscripts.


------------ TO CREATE YOUR NEW BUILD SCRIPT ----------------
Copy/paste this file and rename the `filename`, `class name` and the `id` ( id = "example" )

To enable the buildscript:

Change:

    class ExampleBuildScript(object):

To:

    class YourBuildScript(api.BaseBuildScript):

To assign to your rig in the Hive UI, reload Zoo Tools:

    ZooToolsPro (shelf) > Dev (purple icon) > Reload (menu item)

Open Hive UI and set the build script under:

    Settings (right top cog icon) >  Scripts > Build Scripts (dropdown combo box)

Be sure to reload Zoo Tools with any script changes.


------------ BUILD SCRIPT DOCUMENTATION ----------------

More Hive Build Script documentation found at:
    https://create3dcharacters.com/zoo-dev-documentation/packages/zoo_hive/buildscripting.html

Common build script code examples:
    https://create3dcharacters.com/zoo-dev-documentation/packages/zoo_hive/buildscripting_examples.html

"""

from maya import cmds

from zoo.libs.hive import api


class ExampleBuildScript(object):  # Change (object) to (api.BaseBuildScript), change the class name to your name.
    """

    .. note::

        Best to read the properties method in the base class :func:`api.BaseBuildScript.properties`

    """
    # unique identifier for the plugin which will be referenced by the registry.
    id = "example"  # change id to name that will appear in the hive UI.

    def preGuideBuild(self, properties):
        """Executed Before Any guide has been build on the rig
        """
        pass

    def postGuideBuild(self, properties):
        """Executed once all guides on all components have been built into the scene.
        """
        pass

    def preDeformBuild(self, properties):
        """Executed before the deformation layer has been built or updated for all components.

        This is the ideal point in the process to export skin weights if the skeleton
        already exists.
        """
        pass

    def postDeformBuild(self, properties):
        """ Executed after the deformation and I/O layers has been built for all components
        including all joints.

        This is ideal point in the process to reimport skin weights if necessary.
        """
        pass

    def preRigBuild(self, properties):
        """Executed before the rig Layer has been built for all components.
        """
        pass

    def postRigBuild(self, properties):
        """Executed after the rig Layer has been built for all components.
        """
        pass

    def postPolishBuild(self, properties):
        """Executed after the polish stage.

        Useful for building space switching, optimizing the rig, binding asset meta data and
        preparing for the animator.
        """
        pass

    def preDeleteGuideLayer(self, properties):
        """Executed before the guides of the rig gets deleted.
        """
        pass

    def preDeleteDeformLayer(self, properties):
        """Executed before the deform layer of the rig gets deleted.

        .. Note::

            This is pretty rare unless done directly through the API as we don't provide
            deletion currently to the end user.
        """

        pass

    def preDeleteRigLayer(self, properties):
        """Executed before the rig layer of the rig gets deleted.
        """
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

