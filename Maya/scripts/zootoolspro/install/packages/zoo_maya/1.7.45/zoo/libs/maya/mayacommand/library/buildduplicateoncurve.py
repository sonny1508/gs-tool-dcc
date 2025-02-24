from zoo.libs.maya.mayacommand import command
from zoo.libs.maya import zapi
from zoo.libs.maya.cmds.rig import duplicatealongcurve
from maya.api import OpenMaya as om2


class BuildDuplicateOnCurveCommand(command.ZooCommandMaya):
    """This command Creates a meta node from the registry.
    """
    id = "zoo.maya.duplicateoncurve.build"
    isUndoable = True
    disableQueue = True
    _modifier = None

    def resolveArguments(self, arguments):
        sourceObjects = arguments['sourceObjects']
        curve = arguments['curve']

        # convert to list
        if type(sourceObjects) is not list:
            sourceObjects = [sourceObjects]
        # Convert to zapi
        if type(sourceObjects[0]) is str:
            sourceObjects = list(zapi.nodesByNames(sourceObjects))
        # Convert to zapi
        if type(curve) is str:
            curve = zapi.nodeByName(curve)
        return {"meta": arguments['meta'], "sourceObjects": sourceObjects, "curve": curve}

    def doIt(self, meta=None, sourceObjects=None, curve=None, rename=True):
        """ Build the curve rig based on meta

        :param meta:
        :type meta: zoo.libs.maya.cmds.meta.metaduplicateoncurve.MetaDuplicateOnCurve
        :param sourceObjects:
        :type sourceObjects:
        :param curve:
        :type curve:
        :param rename:
        :type rename:
        :return:
        :rtype:
        """
        self._meta = meta
        self._modifier = om2.MDGModifier()
        ret = duplicatealongcurve.DuplicateAlongCurveCore.duplicateAlongCurve(sourceObjects, curve,
                                                                              multiplyObjects=meta.multiple.value(),
                                                                              spacingStart=meta.startPosition.value(),
                                                                              spacingEnd=meta.endPosition.value(),
                                                                              rotationStart=meta.startRotation.value(),
                                                                              rotationEnd=meta.endRotation.value(),
                                                                              scaleStart=meta.startScale.value(),
                                                                              scaleEnd=meta.endScale.value(),
                                                                              instance=meta.instanced.value(),
                                                                              follow=meta.followAxis.value(),
                                                                              fractionMode=meta.fractionMode.value(),
                                                                              upAxis=meta.upAxis.value(),
                                                                              followAxis=meta.followAxis.value(),
                                                                              group=meta.groupAllGeo.value(),
                                                                              inverseFront=meta.inverseFollow.value(),
                                                                              inverseUp=meta.inverseUp.value(),
                                                                              spacingWeight=meta.weight.value(),
                                                                              weightPosition=meta.weightPosition.value(),
                                                                              weightRotation=meta.weightRotation.value(),
                                                                              weightScale=meta.weightScale.value(),
                                                                              worldUpType="objectrotation",
                                                                              autoWorldUpV=True,
                                                                              message=True)

        meta.connectAttributes(**ret)
        if rename:
            name = meta.generateUniqueName(curve.fullPathName() + "_")
            meta.rename(name, mod=self._modifier)

        return meta

    def undoIt(self):
        if self._meta is not None:
            self._meta.deleteRig()
