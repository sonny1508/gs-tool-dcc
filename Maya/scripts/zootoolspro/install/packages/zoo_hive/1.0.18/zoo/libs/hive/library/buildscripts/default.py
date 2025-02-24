from zoo.libs.hive import api
from zoo.libs.maya import zapi
from zoo.libs.maya.cmds.general import manipulators


class DefaultBuildScript(api.BaseBuildScript):
    """The Default build script plugin handles setting world space switching(godnode),
    Ensuring that preserveChildren manipulator option is off and hiding the deform layer.
    """
    id = "default"

    def preGuideBuild(self, properties):
        zapi.clearSelection()
        manipulators.setPreserveChildren(False)
        state = self.rig.configuration.preferencesInterface.settings(name="containerOutlinerDisplayUnderParent")
        api.sceneutils.setMayaUIContainerDisplaySettings(outlinerDisplayUnderParent=state)

    def preDeformBuild(self, properties):
        zapi.clearSelection()
        manipulators.setPreserveChildren(False)
        state = self.rig.configuration.preferencesInterface.settings(name="containerOutlinerDisplayUnderParent")
        api.sceneutils.setMayaUIContainerDisplaySettings(outlinerDisplayUnderParent=state)

    def preRigBuild(self, properties):
        zapi.clearSelection()
        manipulators.setPreserveChildren(False)
        state = self.rig.configuration.preferencesInterface.settings(name="containerOutlinerDisplayUnderParent")
        api.sceneutils.setMayaUIContainerDisplaySettings(outlinerDisplayUnderParent=state)

    def postRigBuild(self, properties):
        components = []
        rootComponent = None

        for component in self.rig.iterComponents():
            if component.componentType == "godnodecomponent":
                rootComponent = component
                continue
            inputLayer = component.inputLayer()
            if inputLayer is None:
                continue
            worldInput = inputLayer.inputNode("world")
            if worldInput is None:
                continue
            components.append((component, worldInput))
        if not rootComponent or not components:
            return
        godNode = rootComponent.outputLayer().outputNode("offset")
        for component, worldInput in components:
            # we can just run the build again but this time with different another driver
            zapi.buildConstraint(worldInput,
                                 drivers={"targets": (("", godNode),)},
                                 constraintType="matrix",
                                 maintainOffset=True)

    def prePolish(self, properties):
        zapi.clearSelection()

    def postPolishBuild(self, properties):
        layer = self.rig.deformLayer()
        if layer is not None:
            layer.hide()
