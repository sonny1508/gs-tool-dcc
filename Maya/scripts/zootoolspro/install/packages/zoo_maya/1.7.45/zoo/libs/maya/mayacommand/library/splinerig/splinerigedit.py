from zoo.libs.maya.mayacommand import command
from zoo.libs.maya.cmds.meta import metasplinerig
from zoo.core.util import zlogging

logger = zlogging.getLogger(__name__)


class SplineRigEditCommand(command.ZooCommandMaya):
    """ Edits the spline rig based on given attributes
    """
    id = "zoo.maya.splinerig.edit"
    isUndoable = True
    _modifier = None

    def resolveArguments(self, arguments):
        if arguments['meta'] is None:
            self.cancel("Meta must not be none")

        if arguments['metaAttrs'] is None:
            logger.warning("metaAttrs is none.")

        return arguments

    def doIt(self, meta=None, metaAttrs=None):
        """ Build the curve rig based on meta

        :type meta: metasplinerig.MetaSplineRig
        :return:
        :rtype: metasplinerig.MetaSplineRig
        """

        meta.updateRig(metaAttrs)
        return meta

    def undoIt(self):
        # Spline rig already undoes nicely
        pass
