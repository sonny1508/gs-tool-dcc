from zoo.libs.hive import api
from zoo.libs.hive.library.tools import toolui
from zoo.libs.maya.cmds.objutils import curves
from zoo.libs.maya.markingmenu import menu
from zoo.libs.maya.mayacommand import mayaexecutor as executor
from zoo.libs.commands import hive
from zoo.libs.utils import output
from zoo.core.util import zlogging

logger = zlogging.getLogger(__name__)


class ConstrainGuides(menu.MarkingMenuCommand):
    # a unique identifier for a class, once release to public domain this
    # id should never be changed due to being baked into the maya scene.
    id = "hiveConstrainSelectedGuides"
    # The developers name must be specified so tracking who created it is easier.
    creator = "Zootools"

    @staticmethod
    def uiData(arguments):
        return {
            "icon": "connectionSRT",
            "label": "Parent",
            "bold": False,
            "italic": False,
            "optionBox": False,
        }

    def execute(self, arguments):
        """The execute method is called when triggering the action item. use executeUI() for a optionBox.

        :type arguments: dict
        """
        success = executor.execute("hive.component.parent.selectionAdd")
        if success:
            output.displayInfo("Completed creating constraint for selection")


class RemoveAllConstraints(menu.MarkingMenuCommand):
    # a unique identifier for a class, once release to public domain this
    # id should never be changed due to being baked into the maya scene.
    id = "hiveRemoveAllConstraints"
    # The developers name must be specified so tracking who created it is easier.
    creator = "Zootools"

    @staticmethod
    def uiData(arguments):
        return {
            "icon": "plugDisconnect",
            "label": "Unparent",
            "bold": False,
            "italic": False,
            "optionBox": False,
        }

    def execute(self, arguments):
        """The execute method is called when triggering the action item. use executeUI() for a optionBox.

        :type arguments: dict
        """
        executor.execute("hive.component.parent.removeAll")
        output.displayInfo("Completed Removing all constraints selected components")


class GuideToggleVisibility(menu.MarkingMenuCommand):
    # a unique identifier for a class, once released to public domain this
    # id should never be changed due to being baked into the maya scene.
    id = "hiveToggleVisibility"
    # The developers name must be specified so tracking who created it is easier.
    creator = "Zootools"

    @staticmethod
    def uiData(arguments):
        label = arguments.get("visibilityType", "None")
        ret = {
            "label": "{} Visibility".format(label),
            "bold": False,
            "italic": False,
            "optionBox": False,
            "checkBox": False,
        }
        rig = arguments.get("rig")
        if not rig:
            return {}

        arguments["rig"] = rig
        visibility = False
        visType = arguments.get("visibilityType", "").lower()
        if visType == "guides":
            visibility = rig.configuration.guidePivotVisibility
        elif visType == "controls":
            visibility = rig.configuration.guideControlVisibility
        arguments["toggleChecked"] = visibility
        ret["checkBox"] = visibility

        return ret

    def execute(self, arguments):
        """The execute method is called when triggering the action item. use executeUI() for a optionBox.

        :type arguments: dict
        """
        visibilityType = arguments.get("visibilityType", "").lower()
        rig = arguments["rig"]  # type: api.Rig
        settings = {}
        if visibilityType == "guides":
            settings = {
                "guidePivotVisibility": not rig.configuration.guidePivotVisibility
            }
        elif visibilityType == "controls":
            settings = {
                "guideControlVisibility": not rig.configuration.guideControlVisibility
            }
        if settings:
            hive.updateRigConfiguration(rig, settings)
            output.displayInfo(
                "Completed Toggling visibility of {}".format(visibilityType)
            )


class ToggleLRA(menu.MarkingMenuCommand):
    id = "toggleLra"
    creator = "Keen Foong"

    @staticmethod
    def uiData(arguments):
        ret = {
            "icon": "eye",
            "label": "Toggle LRA",
            "bold": False,
            "italic": False,
            "checkBox": False,
        }
        components = arguments.get("components")
        if not components:
            return ret

        component = components[0]
        # Get the first guide
        first = None
        for g in component.guideLayer().iterGuides(includeRoot=False):

            first = g
            break
        if first is None:
            ret["enable"] = False
            return ret
        vis = first.displayAxisShapeVis()
        ret["checkBox"] = vis
        arguments["component"] = component
        arguments["visibility"] = vis
        return ret

    @classmethod
    def guideSettings(cls, component):
        """Get guide settings from component

        :param component:
        :type component:
        :return:
        :rtype:
        """
        guideLayer = component.guideLayer()
        guideSettings = guideLayer.guideSettings() if guideLayer is not None else None
        return guideSettings

    def execute(self, arguments):
        """The execute method is called when triggering the action item. use executeUI() for a optionBox.

        :type arguments: dict
        """
        # when the visibility is set in the marking menu by the user the argument visibility will be the inverted.
        # so we invert here for that reason
        visibility = not arguments.get("visibility", False)
        hive.setGuideLRA(components=arguments["components"], visibility=visibility)
        output.displayInfo("Completed LRA visibility change to: {}".format(visibility))


class ToggleGuideXRay(menu.MarkingMenuCommand):
    id = "toggleGuideXray"
    creator = "Zootools"

    @staticmethod
    def uiData(arguments):
        ret = {
            "icon": "eye",
            "label": "Toggle Guide XRay",
            "bold": False,
            "italic": False,
            "checkBox": False,
        }
        nodes = arguments.get("nodes")
        if not nodes:
            return ret
        state = False
        for n in nodes:
            for shape in n.iterShapes():
                attr = shape.attribute("alwaysDrawOnTop")
                if attr is not None:
                    state = attr.value()
            break
        ret["checkBox"] = state
        arguments["toggleState"] = not state
        return ret

    def execute(self, arguments):
        state = arguments.get("toggleState", False)
        api.sceneutils.setRigGuidesXRay(rig=arguments["rig"], state=state)


class ComponentManualOrient(menu.MarkingMenuCommand):
    """Example Command class which demonstrates how to dynamically change the UI Label and to have
    a UI.
    Specifying a Docstring for the class will act as the tooltip.
    """

    # a unique identifier for a class, once release to public domain this
    # id should never be changed due to being baked into the maya scene.
    id = "hiveManualOrientToggle"
    # The developers name must be specified so tracking who created it is easier.
    creator = "Zootools"

    @staticmethod
    def uiData(arguments):
        ret = {
            "icon": "cursorSelect",
            "label": "Manual Orient LRA",
            "bold": False,
            "italic": False,
            "optionBox": False,
            "checkBox": False,
        }
        components = arguments.get("components")

        # Stub code: replace with own manual orients in component/guide

        if not components:
            return ret
        component = components[0]
        compName = component.name()

        manualOrient = component.definition.guideLayer.guideSetting(
            "manualOrient"
        ).value
        if component.hasGuide():
            guideSettings = component.guideLayer().guideSettings()
            if guideSettings:
                manualOrient = guideSettings.attribute("manualOrient").value()

        ret["checkBox"] = manualOrient
        arguments["componentName"] = compName
        arguments["manualOrient"] = manualOrient
        arguments["component"] = component
        arguments["rig"] = component.rig

        return ret

    def execute(self, arguments):
        """The execute method is called when triggering the action item. use executeUI() for a optionBox.

        :type arguments: dict
        """
        orient = not arguments["manualOrient"]
        executor.execute(
            "component.guides.setting.update",
            component=arguments["component"],
            settings={"manualOrient": orient},
        )
        output.displayInfo(
            "Completed changing component manualOrient to {}".format(orient)
        )


class ComponentGuideSelectAllShapes(menu.MarkingMenuCommand):
    """Example Command class which demonstrates how to dynamically change the UI Label and to have
    a UI.
    Specifying a Docstring for the class will act as the tooltip.
    """

    # a unique identifier for a class, once release to public domain this
    # id should never be changed due to being baked into the maya scene.
    id = "hiveComponentGuideSelectAllShapes"
    # The developers name must be specified so tracking who created it is easier.
    creator = "Zootools"

    @staticmethod
    def uiData(arguments):
        return {
            "icon": "cursorSelect",
            "label": "Select All Guide Controls",
            "bold": False,
            "italic": False,
            "optionBox": False,
        }

    def execute(self, arguments):
        """The execute method is called when triggering the action item. use executeUI() for a optionBox.

        :type arguments: dict
        """
        comps = arguments.get("components")
        if not comps:
            return
        executor.execute("hive.component.guide.selectAll.shapes", components=comps)
        output.displayInfo("Completed selecting all guide shapes")


class ComponentGuideSelectShape(menu.MarkingMenuCommand):
    id = "hiveComponentGuideSelectShapes"
    creator = "Zootools"

    @staticmethod
    def uiData(arguments):
        return {
            "icon": "cursorSelect",
            "label": "Select Guide Control",
            "bold": False,
            "italic": False,
            "optionBox": False,
        }

    def execute(self, arguments):
        """The execute method is called when triggering the action item. use executeUI() for a optionBox.

        :type arguments: dict
        """
        selection = arguments.get("nodes")
        selectedGuides = []
        for mobj in selection:
            if api.Guide.isGuide(api.nodeByObject(mobj.object())):
                selectedGuides.append(api.Guide(mobj.object()))

        if not selectedGuides:
            return
        executor.execute("hive.component.guide.select.shapes", guides=selectedGuides)
        output.displayInfo(
            "Completed Selecting guide shapes of guides: {}".format(selectedGuides)
        )


class ComponentGuideSelectPivot(menu.MarkingMenuCommand):
    id = "hiveComponentGuideSelectPivot"
    creator = "Zootools"

    @staticmethod
    def uiData(arguments):
        return {
            "icon": "cursorSelect",
            "label": "Select Guide Pivots",
            "bold": False,
            "italic": False,
            "optionBox": False,
        }

    def execute(self, arguments):
        """The execute method is called when triggering the action item. use executeUI() for a optionBox.

        :type arguments: dict
        """
        comps = arguments.get("components")
        if not comps:
            return
        executor.execute("hive.component.guide.select.pivot", components=comps)
        output.displayInfo("Completed selecting guide pivot nodes")


class ComponentGuideSelectRootPivot(menu.MarkingMenuCommand):
    id = "hiveComponentGuideSelectRootPivots"
    creator = "Zootools"

    @staticmethod
    def uiData(arguments):
        return {
            "icon": "hierarchy",
            "label": "Select Guide Root",
            "bold": False,
            "italic": False,
            "optionBox": False,
        }

    def execute(self, arguments):
        """The execute method is called when triggering the action item. use executeUI() for a optionBox.

        :type arguments: dict
        """

        comps = arguments.get("components")
        if not comps:
            return
        executor.execute("hive.component.guide.select.rootPivots", components=comps)
        output.displayInfo("Completed selecting guide root nodes")


class ComponentGuideSymmetry(menu.MarkingMenuCommand):
    id = "hiveComponentGuideSymmetry"
    creator = "Zootools"
    originalSettings = dict(translate=("x",), rotate="yz", parent=None, duplicate=True)

    @staticmethod
    def uiData(arguments):
        return {
            "icon": "symmetryTri",
            "label": "Apply Symmetry",
            "bold": False,
            "italic": False,
            "optionBox": False,
        }

    def execute(self, arguments):
        """The execute method is called when triggering the action item. use executeUI() for a optionBox.

        :type arguments: dict
        """
        components = arguments.get("components")
        rig = arguments.get("rig")
        if not components:
            output.displayInfo("No components found")
            return
        hive.applySymmetry(rig, components)
        output.displayInfo("Completed Applying symmetry")


class ComponentGuideMirror(menu.MarkingMenuCommand):
    id = "hiveComponentGuideMirror"
    creator = "Zootools"
    originalSettings = dict(translate=("x",), rotate="yz", parent=None, duplicate=True)

    @staticmethod
    def uiData(arguments):
        return {
            "icon": "mirrorComponent",
            "label": "Create Mirror",
            "bold": False,
            "italic": False,
            "optionBox": True,
        }

    def execute(self, arguments):
        """The execute method is called when triggering the action item. use executeUI() for a optionBox.

        :type arguments: dict
        """
        components = arguments.get("components")  # type: list[api.Component]
        comps = []
        # ok no components , what about selection?
        rig = None

        for component in components:
            rig = component.rig
            config = rig.namingConfiguration()
            side = config.field("sideSymmetry").valueForKey(component.side())
            settings = {"side": side}
            settings.update(self.originalSettings)
            settings["component"] = component
            comps.append(settings)

        if not comps:
            return

        executor.execute("hive.component.guide.mirror", rig=rig, components=comps)
        output.displayInfo("Completed Mirroring components")

    def executeUI(self, arguments):
        components = arguments.get("components")
        comps = []
        # ok no components , what about selection?
        for component in components:
            args = dict(**self.originalSettings)
            args["component"] = component
            comps.append(args)
        if not comps:
            return
        toolui.launchMirrorWidget(comps)


class ComponentGuideDuplicate(menu.MarkingMenuCommand):
    id = "hiveComponentGuideDuplicate"
    creator = "Zootools"

    @staticmethod
    def uiData(arguments):
        return {
            "icon": "duplicate",
            "label": "Duplicate",
            "bold": False,
            "italic": False,
            "optionBox": False,
        }

    def execute(self, arguments):
        """The execute method is called when triggering the action item. use executeUI() for a optionBox.

        :type arguments: dict
        """
        components = arguments.get("components")
        rig = arguments.get("rig")
        sources = []
        # ok no components , what about selection?
        for component in components:
            sources.append(
                {
                    "component": component,
                    "name": component.name(),
                    "side": component.side(),
                    "parent": None,
                }
            )
        executor.execute("hive.component.duplicate", rig=rig, sources=sources)
        output.displayInfo("Completed duplicating components")


class ComponentGuidePin(menu.MarkingMenuCommand):
    id = "hiveComponentGuidePin"
    creator = "Zootools"

    @staticmethod
    def uiData(arguments):
        arguments.update(
            {
                "icon": "duplicate",
                "label": "Pin Components",
                "bold": False,
                "italic": False,
                "optionBox": False,
                "checkBox": False,
                "pinned": False,
            }
        )

        pinStates = set()
        for component in arguments.get("components"):
            layer = component.guideLayer()
            if not layer:
                continue
            pinStates.add(layer.isPinned())
        pinState = any(pinStates)
        arguments["checkBox"] = pinState
        arguments["pinned"] = pinState
        return arguments

    def execute(self, arguments):
        """The execute method is called when triggering the action item. use executeUI() for a optionBox.

        :type arguments: dict
        """
        if not arguments["pinned"]:
            cmdName = "hive.component.guide.pin"

        else:
            cmdName = "hive.component.guide.unpin"
        executor.execute(cmdName, components=arguments["components"])
        output.displayInfo("Completed {} components".format(arguments["label"]))


class AutoAlignGuides(menu.MarkingMenuCommand):
    """Align guide transformations, if Align All is selected then all components will be aligned.
    Subject to component implementation and per guide settings.
    """

    id = "hiveGuideAutoAlign"

    @staticmethod
    def uiData(arguments):
        arguments.update(
            {
                "icon": "crosshair",
                "label": (
                    "Align Selected" if not arguments.get("alignAll") else "Align All"
                ),
                "bold": False,
                "italic": False,
                "optionBox": False,
            }
        )
        return arguments

    def execute(self, arguments):
        if not arguments["components"]:
            return
        if arguments.get("alignAll"):
            hive.autoAlignGuides(components=arguments["rig"].components())
        else:
            hive.autoAlignGuides(components=arguments["components"])
        output.displayInfo("Completed Align guides")
