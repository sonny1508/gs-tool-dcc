from zoo.libs.maya.mayacommand import mayaexecutor as executor
from zoo.libs.maya.cmds.meta import metafocuspuller, metaadditivefk
from zoo.libs.maya.markingmenu import menu
from zoo.libs.maya.meta import base
from zoo.libs.utils.general import uniqify


class FocusPullerMarkingMenuCommand(menu.MarkingMenuCommand):
    """ Spline Marking menu command
    """
    id = "focusPullerMarkingMenu"  # a unique identifier for a class, should never be changed
    creator = "M.Marks"

    @staticmethod
    def uiData(arguments):
        """

        :param arguments:
        :type arguments:
        :return:
        :rtype:
        """
        ret = {"icon": "YesSir",
               "label": "HelloBoy",
               "bold": False,
               "italic": False,
               "optionBox": False,
               "optionBoxIcon": ""
               }

        #op = arguments['operation']
        #if op == "switchSpace":
        #    meta = base.metaNodeFromZApiObjects(arguments['nodes'])[-1]  # type: ZooFocusPuller
        #    ret['checkBox'] = not meta.getCtrlVisibility()

        return ret

    def execute(self, arguments):
        """The main execute methods for the joints marking menu. see executeUI() for option box commands

        :type arguments: dict
        """
        metaNodes = base.metaNodeFromZApiObjects(arguments['nodes'])[-1]  # type: ZooFocusPuller
        operation = arguments.get("operation", "")

        if operation == "switchSpace":
            # print(metaNodes.getFStopValue())
            pass
        elif operation == "centerControl":
            pass
