.. _hiveExporterPlugin:

Exporting Hive Rigs
###################

Hive contains a small lightweight exporter plugin system. While it's not necessary
in anyway to use this system when you have you're own way of exporting with your own UI.
We do however provide out of box generalized exporters for the everyday user.

Lets walk through how these exporters work and how to build one.

First thing to know is as always there's two main parts the backend and the frontend(UI).
The backend is by hive configuration and a python plugin while the frontend will be managed
through toolsets.

Let's define the stub for the plugin before we flesh out the body.

We're not going to write out every line of code as much of it will be standard exporting logic
but we will go through our fbx pre export logic as that shows how you can interact with the hive api
to retrieve the geometry and skeleton.

You probably want to check out :class:`ExportPlugin<zoo.libs.hive.base.exporterplugin.ExporterPlugin>`
for details on the class.


.. code-block:: python

    from zoo.libs.hive import api

    class ExportSettings(object):
        def __init__(self):
            self.outputPath = ""

    class MyExporterPlugin(api.ExporterPlugin):
        id = "myExporter"

        def exportSettings(self):
            return ExportSettings()

        def export(self, rig, exportOptions):
            print(exportOptions.outputPath)

This is how you would use it.

.. _hiveexporter_code:

.. code-block:: python

    from zoo.libs.hive import api

    r = api.Rig()
    r.startSession("myRig")
    exporter = r.configuration.exportPluginForId("myExporter")()
    settings = exporter.exportSettings()
    settings.outputPath = "myOutputPath.fbx"
    exporter.export(r, settings)

Here we've reimplemented both the exportSettings and export methods which are both required overrides.

The exportSettings method has to return an object, it can be a dict or anything else as it's just a
convenience method however if you indeed to override our out of the box plugins then it'll need to contain
the same properties as the original plugin as our toolset use these plugins. More on that later.

For the export method lets actually do some hive logic. We're going to do some prep for a bindpose export.

Lets see the steps. The first 4 is about detaching the hive skeleton and geometry from the rig in
prep for a clean Fbx export.

#. Parent the geometry root transform to the world as we'll export that.
#. Disconnect all deformJoints metadata so we can clean the scene including deleting the rig.
#. Clean the skeleton of any metadata and namespaces.
#. Delete the rig that way the FBX won't carry any crud, Maya FBX exporter can be pretty flaky.
#. Standard export prep you would do ie. add attributes to the skeleton etc.

.. code-block:: python

    def export(self, rig, exportOptions):
        self.onProgressCallbackFunc(10, "Prepping scene for rig export")
        geoLayer = rig.geometryLayer()
        deformLayer = rig.deformLayer()
        geoRoot = geoLayer.rootTransform()
        deformRoot = deformLayer.rootTransform()

        # parent the geometry root transform to the world so we can use it directly in the export
        if geoRoot:
            geoParent = geoRoot.parent()
            geoRoot.setParent(None)
        # Detach the joints from the metaData, has to be done on each component.
        for comp in rig.iterComponents():
            compDeform = comp.deformLayer()
            compDeform.disconnectAllJoints()
        # grab the root skeleton roots, for the sake of support we'll just grab all roots
        # though 99% there should be one but its a good safe guard.
        skelRoots = list(deformRoot.iterChildren(recursive=False, nodeTypes=(zapi.kJoint,)))
        # important step to strip hive meta data from the skeleton joints and namespaces.
        # otherwise the fbx will contain extra attributes we don't need
        api.skeletonutils.cleanSkeletonBeforeExport(skelRoots)
        geoLayer.attribute(api.constants.ROOTTRANSFORM_ATTR).disconnectAll()
        # Remove the rig in the scene without deleting the joints which is what the above cleaning ensures.
        #This creates a clean FBX file.
        rig.delete()

     # ...standard export code
     # ...standard post export code

That's it. All that code is about cleanly detaching the skeleton and geometry from the rig that
way we can export FBX with the most cut down scene possible. Of coarse you can export however you
wish when writing your own exporters but this is an example of doing some prep with Hive.

Now lets override our built fbxExporter with the above class.

First thing to know is we don't yet have the PreferencesUI options to do this so it's rather manual.
Second we'll need to modify our plugin ExportSettings class to use the same settings as ours, we'll
simply copy it over instead of using inheritance as we may change it's location so we'll make it simple for now.

Replace the ExportSettings class above with the below.

.. code-block:: python

    class ExportSettings(object):
        def __init__(self):
            self.outputPath = ""
            self.skeletonDefinition = True
            self.constraints = False
            self.tangents = True
            self.hardEdges = False
            self.smoothMesh = False
            self.smoothingGroups = True
            self.version = "FBX201800"
            self.shapes = True
            self.skins = True
            self.lights = False
            self.cameras = False
            self.animation = False
            self.startEndFrame = []
            self.ascii = False
            self.triangulate = True
            self.includeChildren = True
            self.axis = "Y"
            self.debugScene = False
            self.includeScale = True

Now in the userPreferences folder go to file "/prefs/maya/hive.pref" and open it.

Now add a new setting called "exporterPluginOverrides" like below under the "settings" section.

.. code-block:: json

    {
        "settings": {
             "exporterPluginOverrides": {
                    "fbxExport": "myExporter"
                }
        }
    }

Now reload zoo/maya and let's run the code to access and run the export but instead of specifying "myExporter"
use "fbxexport" like so.

.. code-block:: python

    from zoo.libs.hive import api

    r = api.Rig()
    r.startSession("myRig")
    exporter = r.configuration.exportPluginForId("fbxExport")()
    settings = exporter.exportSettings()
    settings.outputPath = "myOutputPath.fbx"
    exporter.export(r, settings)


With that lets check out how the UI operates

.. figure:: resources/fbxexporttoolset.png
    :align: center
    :alt: alternate text
    :figclass: align-center

    :colorlightgrayitalic:`This is what our FBX exporter looks like in the hive artist UI.`

When we changed the preferences to use "myExporter" for the fbxExport will effectively switch over the toolset to
use our new plugin however the toolset UI will not change the layout so in this case you're limited to what we provide
in the Toolset but you can always build you're own toolset.

See :ref:`Extending Hive Artist UI Side Bar<hiveSideBarExtensions>` to add you're own toolset to Hive.