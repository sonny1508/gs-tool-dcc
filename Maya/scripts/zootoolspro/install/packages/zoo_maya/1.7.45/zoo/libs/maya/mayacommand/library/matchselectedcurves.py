from zoo.libs.maya.mayacommand import command
from zoo.libs.maya.api import scene, curves, nodes
from maya.api import OpenMaya as om2
from maya import cmds


class MatchSelectedCurves(command.ZooCommandMaya):
    """This command Matches the first selected curve to the second
    """
    id = "zoo.maya.curves.match"
    isUndoable = True
    _shapes = []
    _origShape = None

    def resolveArguments(self, arguments):
        selected = scene.getSelectedNodes()
        if len(selected) < 2:
            self.cancel("Please Select at least 2 nodes")
        driver = om2.MObjectHandle(selected[0])  # driver
        drivenNodes = []
        for driven in selected[1:]:
            handle = om2.MObjectHandle(driven)
            shape = curves.serializeCurve(driven, arguments.get("space", om2.MSpace.kObject))
            drivenNodes.append((handle, shape))
        self._origShape = drivenNodes
        arguments["driver"] = driver
        arguments["driven"] = drivenNodes
        return arguments

    def doIt(self, driver=None, driven=None, space=om2.MSpace.kObject):
        """Create the meta node based on the type parameter, if the type isn't specified then the baseMeta class will
        be used instead

        """

        newShapes = curves.matchCurves(driver.object(), [n.object() for n, _ in driven], space=space)
        self._shapes = map(om2.MObjectHandle, newShapes)
        return True

    def undoIt(self):
        for shape in self._shapes:

            if shape.isValid() and shape.isAlive():
                cmds.delete(nodes.nameFromMObject(shape.object()))
        for driven, originalInfo in self._origShape:
            if originalInfo:
                curves.createCurveShape(driven.object(), originalInfo, space=self.arguments.space)
