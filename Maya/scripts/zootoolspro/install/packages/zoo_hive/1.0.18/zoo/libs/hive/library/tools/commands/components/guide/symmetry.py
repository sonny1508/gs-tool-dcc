from zoo.libs.maya.mayacommand import command
from zoo.libs.hive import api


class GuideSymmetryCommand(command.ZooCommandMaya):
    id = "hive.component.symmetry"

    isUndoable = True
    isEnabled = True
    disableQueue = True  # If true, disable the undo queue in doIt()

    _mirrorData = {}
    _mirrorUndoData = {}

    def _resolveComponentData(self, rig, components, mirrorMapping, mirrorUndoData):
        namingInstance = rig.namingConfiguration()
        for component in components:
            key = component.serializedTokenKey()
            if key in mirrorMapping:
                continue
            name, side = component.name(), component.side()
            mirroredSide = namingInstance.field("sideSymmetry").valueForKey(side)
            oppositeComponent = rig.component(name, mirroredSide)
            if not oppositeComponent:
                continue
            oppositeSideLayer = oppositeComponent.guideLayer()
            oppositeGuides = {i.id(): i for i in oppositeSideLayer.iterGuides()}
            componentMirrorData = []
            componentRecoveryData = []
            for currentInfo, undoRecoveryData in api.mirrorutils.mirrorDataForComponent(component, oppositeGuides):
                componentMirrorData.append(currentInfo)
                if undoRecoveryData:
                    componentRecoveryData.append(undoRecoveryData)

            mirrorMapping[key] = {"data": componentMirrorData,
                                  "oppositeComponent": oppositeComponent}
            if componentRecoveryData:
                mirrorUndoData[key] = {"data": componentRecoveryData,
                                       "component": oppositeComponent}
            self._resolveComponentData(rig, component.children(), mirrorMapping, mirrorUndoData)

    def resolveArguments(self, arguments):
        components = arguments.get("components")
        rig = arguments.get("rig")
        mirrorMapping = {}
        mirrorUndoData = {}
        self._resolveComponentData(rig, components, mirrorMapping, mirrorUndoData)
        self._mirrorData = mirrorMapping
        self._mirrorUndoData = mirrorUndoData

        super(GuideSymmetryCommand, self).resolveArguments(arguments)

    def doIt(self, rig=None, components=None):
        components = [mirrorInfo["oppositeComponent"] for mirrorInfo in self._mirrorData.values()]
        with api.componentutils.disconnectComponentsContext(components):
            for _, mirrorInfo in self._mirrorData.items():
                comp = mirrorInfo["oppositeComponent"]
                comp.preMirror()
                api.mirrorutils.setMirrorData(mirrorInfo["data"])
                comp.postMirror()

        api.alignGuides(rig, components)

    def undoIt(self):
        components = [mirrorInfo["component"] for mirrorInfo in self._mirrorUndoData.values()]
        with api.componentutils.disconnectComponentsContext(components):
            for _, mirrorInfo in self._mirrorUndoData.items():
                    comp = mirrorInfo["component"]
                    comp.preMirror()
                    api.mirrorutils.setMirrorData(mirrorInfo["data"], mirrorCurve=False)
                    comp.postMirror()
