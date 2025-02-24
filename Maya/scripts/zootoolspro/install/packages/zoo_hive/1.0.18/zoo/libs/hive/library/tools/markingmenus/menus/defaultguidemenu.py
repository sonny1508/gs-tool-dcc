from zoo.libs.maya.markingmenu import menu
from zoo.libs.hive import api
from zoo.libs.maya import zapi
from zoo.core.util import zlogging
from zoo.libs.hive.library.tools.toolui import markingmenutils


logger = zlogging.getLogger(__name__)


class BaseHiveGuideMM(menu.MarkingMenuDynamic):
    id = "hiveDefaultGuideMenu"

    def _applyHiveContextToArguments(self, arguments):
        """ Get component from marking menu arguments

        :type arguments: generator[:class:`api.Component`]
        """

        arguments["nodes"] = [i for i in arguments["nodes"] if i.hasFn(zapi.kNodeTypes.kDagNode)]
        try:
            components = api.componentsFromNodes(arguments['nodes'])
        except Exception:
            logger.error("Unhandled Exception when initialize hive from scene Nodes", exc_info=True)
            markingmenutils.logUnableToLoadComponentsMM()
            return None, None
        componentInstances = list(components.keys())
        rig = None
        if componentInstances:
            rig = componentInstances[0].rig
        arguments.update({"rig": rig,
                          "components": componentInstances,
                          "componentToNodes": components})
        return componentInstances, rig

    def execute(self, layout, arguments):
        components, rig = self._applyHiveContextToArguments(arguments)
        if components is None or rig is None:
            return layout
        generic = [
            {
                "type": "command",
                "id": "hiveConstrainSelectedGuides",
                "arguments": {
                    "rig": rig, "components": components}
            },
            {
                "id": "hiveRemoveAllConstraints",
                "type": "command",
                "arguments": arguments
            },

            {
                "type": "separator"
            },
            {
                "type": "command",
                "id": "hiveComponentGuideSymmetry",
                "arguments": arguments
            },
            {
                "type": "command",
                "id": "hiveComponentGuideMirror",
                "arguments": arguments
            },
            {
                "type": "command",
                "id": "hiveComponentGuideDuplicate",
                "arguments": arguments
            },
            {
                "type": "separator"
            },
            {
                "type": "command",
                "id": "hiveDeleteComponent",
                "arguments": arguments
            },
            {
                "type": "separator"
            },
            {
                "id": "hiveComponentGuideSelectRootPivots",
                "type": "command",
                "arguments": arguments
            },
            {
                "type": "command",
                "id": "hiveToggleVisibility",
                "arguments": {
                    "visibilityType": "Guides",
                    "rig": rig, "components": components
                }
            },
            {
                "type": "command",
                "id": "hiveToggleVisibility",
                "arguments": {
                    "visibilityType": "Controls",
                    "rig": rig, "components": components
                }
            },
            {
                "type": "command",
                "id": "hiveComponentGuidePin",
                "arguments": arguments
            },
            {
                "type": "command",
                "id": "toggleGuideXray",
                "arguments": arguments
            },
            {
                "type": "command",
                "id": "toggleLra",
                "arguments": arguments
            },
            {
                "type": "separator"
            },


        ]

        generic.extend([
            {
                "id": "hiveGuideAutoAlign",
                "type": "command",
                "arguments": {"rig": rig, "components": components, "alignAll": False}
            },
            {
                "id": "hiveGuideAutoAlign",
                "type": "command",
                "arguments": {"rig": rig, "components": components, "alignAll": True}
            },
            {
                "id": "hiveToggleBlackBox",
                "type": "command",
                "arguments": arguments
            },
            {
                "type": "separator"
            },
            {
                "type": "menu",
                "label": "Select",
                "children": [
                    {
                        "type": "command",
                        "id": "hiveComponentGuideSelectShapes",
                        "arguments": arguments
                    },
                    {
                        "type": "command",
                        "id": "hiveComponentGuideSelectAllShapes",
                        "arguments": arguments
                    },
                    {
                        "type": "command",
                        "id": "hiveComponentGuideSelectPivot",
                        "arguments": arguments
                    }
                ]
            },
            {
                "type": "menu",
                "label": "Options",
                "children": [
                    {
                        "type": "command",
                        "id": "hiveManualOrientToggle",
                        "arguments": arguments
                    }
                ]
            },

        ])
        layout["items"] = {
            "generic": generic
        }
        return layout
