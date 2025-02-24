from maya.api import OpenMaya as om2
from zoo.libs.maya.cmds.meta import metasplinerig
from zoo.libs.maya.mayacommand import command


class SplineRigBakeCommand(command.ZooCommandMaya):
    """This command Creates a meta node from the registry.
    """
    id = "zoo.maya.splinerig.bake"

    isUndoable = True

    _modifier = None
    disableQueue = False

    def resolveArguments(self, arguments):
        self._modifier = om2.MDagModifier()
        return arguments

    def doIt(self, meta=None, showSpline=False, message=True):
        """ Bake the controls

        :type meta: :class:`metasplinerig.MetaSplineRig`
        :return:
        :rtype: class:`metasplinerig.MetaSplineRig`

        """

        meta.bake(mod=self._modifier, showSpline=showSpline)
        self._modifier.doIt()
        if message:
            om2.MGlobal.displayInfo("Success: Spline Rig Baked")
        return meta

    def undoIt(self):
        """ Undo bake

        :return:
        :rtype:
        """
        if self._modifier:
            self._modifier.undoIt()
