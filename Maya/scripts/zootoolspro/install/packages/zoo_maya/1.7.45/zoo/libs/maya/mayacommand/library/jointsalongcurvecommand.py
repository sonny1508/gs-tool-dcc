from maya import cmds

from zoo.libs.maya.cmds.rig import jointsalongcurve
from zoo.libs.maya import zapi
from zoo.libs.maya.mayacommand import command


class JointsAlongCurveCommand(command.ZooCommandMaya):
    """Joints along curve that is undoable
    """
    id = "zoo.maya.jointsAlongCurve"
    isUndoable = True
    useUndoChunk = False
    disableQueue = True

    _modifier = None
    _jointsList = None

    def resolveArguments(self, arguments):
        self._curve = zapi.nodeByName(arguments['splineCurve'])
        return arguments

    def doIt(self, **kwargs):
        """ Bake the controls

        :return:
        :rtype: list[:class:`DagNode`]

        """
        jointList = jointsalongcurve.jointsAlongACurve(**kwargs)
        self._jointsList = list(zapi.nodesByNames(jointList))
        return jointList

    def undoIt(self):
        """ Delete the joints if it exists

        :return:
        :rtype:
        """
        if self._jointsList:
            cmds.delete(zapi.fullNames(self._jointsList))
            self._curve.show()


class JointsAlongCurveSelectedCommand(command.ZooCommandMaya):
    """Joints along curve that is undoable
    """
    id = "zoo.maya.jointsAlongCurve.selected"
    isUndoable = True
    useUndoChunk = False
    disableQueue = True

    _modifier = None
    _jointsList = None

    def doIt(self, **kwargs):
        """ Bake the controls

        :return:
        :rtype: list[:class:`DagNode`]

        """
        jointList = jointsalongcurve.jointsAlongACurveSelected(**kwargs)[0]
        self._jointsList = list(zapi.nodesByNames(jointList))
        return jointList

    def undoIt(self):
        """ Delete the joints if it exists

        :return:
        :rtype:
        """
        if self._jointsList:
            cmds.delete(zapi.fullNames(self._jointsList))


class JointsAlongCurveRebuildCommand(command.ZooCommandMaya):
    """Joints along curve that is undoable
    """
    id = "zoo.maya.jointsAlongCurve.rebuild"
    isUndoable = True
    useUndoChunk = True
    disableQueue = False

    _modifier = None
    _jointsList = None

    def doIt(self, **kwargs):
        """ Bake the controls

        :return:
        :rtype: list[:class:`DagNode`]

        """
        jointList = jointsalongcurve.rebuildSplineJointsSelected(**kwargs)
        # self._jointsList = list(zapi.nodesByNames(jointList))
        return jointList

    def undoIt(self):
        """ Delete the joints if it exists

        :return:
        :rtype:
        """
