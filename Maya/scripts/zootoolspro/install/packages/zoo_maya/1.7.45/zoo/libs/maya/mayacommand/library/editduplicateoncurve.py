from zoo.libs.maya.mayacommand import command
from maya.api import OpenMaya as om2


class EditDuplicateOnCurveCommand(command.ZooCommandMaya):
    """This command Creates a meta node from the registry.
    """
    id = "zoo.maya.duplicateoncurve.edit"
    isUndoable = True
    _modifier = None  # om2.MDGModifier
    _meta = None
    _undoEvent = None

    def resolveArguments(self, arguments):
        return {"meta": arguments['meta'], "metaAttrs": arguments['metaAttrs']}

    def doIt(self, meta=None, metaAttrs=None):
        """

        :param meta:
        :type meta:  zoo.libs.maya.cmds.meta.metaduplicateoncurve.MetaDuplicateOnCurve
        :return:
        :rtype:
        """

        self._meta = meta
        if not self._modifier:
            self._modifier = om2.MDGModifier()
        metaAttrs['mod'] = self._modifier
        meta.setMetaAttributes(**metaAttrs)
        meta.updateCurve(mod=self._modifier)
        self._modifier.doIt()
        return True

    def undoIt(self):
        if self._modifier is not None:
            self._modifier.undoIt()
