from maya.api import OpenMaya as om2
from zoo.libs.maya import zapi

from zoo.libs.maya.cmds.rig import splinebuilder
from zoo.libs.maya.mayacommand import command
from zoo.core.util import zlogging
from zoo.libs.maya.mayacommand.library.splinerig import splinerigbake, splinerigdelete, splinerigbuild


logger = zlogging.getLogger(__name__)


class SplineRigRebuildCommand(command.ZooCommandMaya):
    """This command rebuilds the spline rig
    """
    id = "zoo.maya.splinerig.rebuild"
    isUndoable = True

    disableQueue = True
    _modifier = None
    _selMod = None
    _commands = []

    def resolveArguments(self, arguments):
        self._commands = []
        self._modifier = None
        self._selMod = om2.MDGModifier()

        logger.debug("'{}': Resolve arguments {}".format(self.id, arguments))
        metaAttrs = arguments['metaAttrs']
        meta = arguments['meta']
        self._modifier = om2.MDagModifier()
        if metaAttrs is not None:
            meta.setMetaAttributes(mod=self._modifier, **metaAttrs)
        else:
            metaAttrs = meta.metaAttributeValues()

        return {"meta": arguments['meta'],
                "metaAttrs": metaAttrs,
                "bake": arguments.get("bake", False)}

    def doIt(self, meta=None, metaAttrs=None, bake=False):
        """ Rebuilds the curve rig based on meta

        :type meta: class: `metasplinerig.MetaSplineRig`
        :param metaAttrs: Meta attrs to send before rebuilding
        :type metaAttrs:
        :return:
        :rtype:
        """
        selected = zapi.fullNames(list(zapi.selected()))
        if metaAttrs is not None:
            self._modifier.doIt()
        if bake:
            command = splinerigbake.SplineRigBakeCommand()
            command.runArguments(meta=meta, showSpline=True, message=False)
            self._commands.append(command)
        else:
            command = splinerigdelete.SplineRigDeleteCommand()
            command.runArguments(meta=meta, showSpline=True, message=False)
            self._commands.append(command)

        buildCommand = splinerigbuild.SplineRigBuildCommand()
        meta = buildCommand.runArguments(metaAttrs=metaAttrs, buildType=splinebuilder.BT_STARTENDJOINT)
        self._commands.append(buildCommand)

        if selected:
            try:
                zapi.selectByNames(selected, mod=self._selMod)
            except ValueError as e:
                if "No object matches name" not in str(e):
                    raise e

        return meta

    def undoIt(self):
        """ Undo in the correct order

        :return:
        :rtype:
        """

        logger.debug("'{}' Undoing {} commands".format(self.id, len(self._commands)))
        for command in reversed(self._commands):
            if command:
                logger.debug("Undoing '{}'".format(command.id))
                command.undoIt()

        if self._modifier:
            logger.debug("Undoing 'meta.setMetaAttributes()'")
            self._modifier.undoIt()
