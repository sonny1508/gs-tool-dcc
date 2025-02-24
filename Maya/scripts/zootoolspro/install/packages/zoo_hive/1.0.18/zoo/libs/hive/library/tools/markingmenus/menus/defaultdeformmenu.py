from zoo.libs.maya.markingmenu import menu
from zoo.libs.hive import api
from zoo.core.util import zlogging
from zoo.libs.maya import zapi
from zoo.libs.hive.library.tools.toolui import markingmenutils


logger = zlogging.getLogger(__name__)


class BaseHiveDeformMM(menu.MarkingMenuDynamic):
    id = "hiveDefaultDeformMenu"

    def _applyHiveContextToArguments(self, arguments):
        """ Get component from marking menu arguments

        :type arguments: generator[:class:`api.Component`]
        """
        arguments["nodes"] = [i for i in arguments["nodes"] if i.hasFn(zapi.kNodeTypes.kDagNode)]
        try:
            components = api.componentsFromNodes(arguments['nodes'])
        except Exception:
            markingmenutils.logUnableToLoadComponentsMM()
            return None, None
        componentInstances = list(components.keys())
        rig = None
        if componentInstances:
            rig = componentInstances[0].rig
            arguments["liveLink"] = rig.isLiveLink()
        arguments.update({"rig": rig,
                          "components": componentInstances,
                          "componentToNodes": components})
        return componentInstances, rig

    def execute(self, layout, arguments):
        components, rig = self._applyHiveContextToArguments(arguments)
        if components is None or rig is None:
            return layout

        layout["items"] = {
            "generic": [
                {
                    "type": "separator"
                },
                {
                    "id": "hiveToggleBlackBox",
                    "type": "command",
                    "arguments": arguments
                }
            ]
        }
        return layout