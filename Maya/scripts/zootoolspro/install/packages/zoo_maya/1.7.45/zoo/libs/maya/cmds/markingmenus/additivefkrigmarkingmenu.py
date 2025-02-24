from collections import OrderedDict

from zoo.libs.maya.mayacommand import mayaexecutor as executor
from zoo.libs.maya.cmds.meta.metaadditivefk import ZooMetaAdditiveFk
from zoo.libs.maya.markingmenu import menu
from zoo.libs.maya.meta import base
from zoo.libs.utils.general import uniqify


class AdditiveFKMarkingMenuCommand(menu.MarkingMenuCommand):
    """ Additive fk Marking menu command
    """
    id = "additiveFkRigMarkingMenu"  # a unique identifier for a class, should never be changed
    creator = "Zootools"

    @staticmethod
    def uiData(arguments):
        """

        :param arguments:
        :type arguments:
        :return:
        :rtype:
        """
        ret = {"icon": "",
               "label": "",
               "bold": False,
               "italic": False,
               "optionBox": False,
               "optionBoxIcon": ""
               }

        op = arguments['operation']
        if op == "toggleControls":
            meta = base.metaNodeFromZApiObjects(arguments['nodes'])[-1]  # type: ZooMetaAdditiveFk
            ret['checkBox'] = not meta.controlsHidden()

        return ret

    def execute(self, arguments):
        """The main execute methods for the joints marking menu. see executeUI() for option box commands

        :type arguments: dict
        """
        metaNodes = base.metaNodeFromZApiObjects(arguments['nodes'])[-1]  # type: ZooMetaAdditiveFk
        operation = arguments.get("operation", "")

        for m in metaNodes:

            if operation == "delete":
                executor.execute("zoo.maya.additiveFk.delete", meta=m)
            if operation == "bake":
                executor.execute("zoo.maya.additiveFk.delete", meta=m, bake=True)
            elif operation == "toggleControls":
                m.toggleControls()





