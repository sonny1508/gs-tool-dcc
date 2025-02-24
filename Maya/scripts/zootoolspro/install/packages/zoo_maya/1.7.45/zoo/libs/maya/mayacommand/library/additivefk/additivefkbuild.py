from zoo.libs.maya.cmds.meta import metaadditivefk
from zoo.libs.maya.mayacommand import command
from zoo.libs.maya import zapi
from zoo.libs.maya.cmds.objutils.joints import getJointChain


class AdditiveFKBuildCommand(command.ZooCommandMaya):
    """This command Creates a meta node from the registry.
    """
    id = "zoo.maya.additiveFk.build"
    isUndoable = True
    _modifier = None

    def doIt(self, joints=None, startJoint=None, endJoint=None, controlSpacing=1, rigName="additive", message=True):
        """ Bake the controls

        :type meta: :class:`metaadditivefk.ZooMetaAdditiveFk`
        :return:
        :rtype: :class:`metaadditivefk.ZooMetaAdditiveFk`

        """
        if joints is None:
            joints = zapi.nodesByNames(getJointChain(startJoint.fullPathName(), endJoint.fullPathName()))
        self.meta = metaadditivefk.ZooMetaAdditiveFk()
        self.meta.createAdditiveFk(zapi.fullNames(joints), rigName=rigName, controlSpacing=controlSpacing)
        return self.meta

    def undoIt(self):
        """ Undo

        :return:
        :rtype:
        """

        self.meta.deleteSetup(message=False) if self.meta else None
