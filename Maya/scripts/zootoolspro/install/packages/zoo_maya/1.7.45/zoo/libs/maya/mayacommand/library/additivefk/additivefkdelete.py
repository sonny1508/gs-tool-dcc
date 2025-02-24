from zoo.libs.maya.mayacommand import command



class AdditiveFKDeleteCommand(command.ZooCommandMaya):
    id = "zoo.maya.additiveFk.delete"
    isUndoable = True

    _modifier = None

    def doIt(self, meta=None, bake=False, message=True):
        """ Bake the controls

        :type meta: :class:`metaadditivefk.ZooMetaAdditiveFk`
        :return:
        :rtype: :class:`metaadditivefk.ZooMetaAdditiveFk`

        """

        meta.deleteSetup(bake=bake)
