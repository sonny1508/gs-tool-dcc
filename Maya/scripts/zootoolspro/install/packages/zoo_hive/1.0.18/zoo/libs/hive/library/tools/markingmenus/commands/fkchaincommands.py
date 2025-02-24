from zoo.libs.maya.markingmenu import menu
from zoo.libs.utils import output
from zoo.libs.maya.utils import general
from zoo.libs.hive import api


class FkReparentGuide(menu.MarkingMenuCommand):
    id = "hiveFkSetParentGuide"
    creator = "Zootools"

    @staticmethod
    def uiData(arguments):
        uiData = {"icon": "convert",
                  "label": "Link FK to FK",
                  "bold": False,
                  "italic": False,
                  "optionBox": False,
                  }
        return uiData

    def execute(self, arguments):
        registry = api.Configuration().componentRegistry()

        guides = []
        fkChainCompareObject = registry.findComponentByType("fkchain")
        for comp, nodes in arguments.get("componentToNodes", {}).items():
            if not isinstance(comp, fkChainCompareObject):
                continue
            guides.append([i for i in nodes if api.Guide.isGuide(i)])
        if not guides:
            output.displayWarning("Must select at least 2 guides on a FK compatible component")
        else:
            passedValidation = True
            with general.undoContext("HiveFKLinkParent"):
                for componentGuides in guides:
                    if len(componentGuides) < 2:
                        passedValidation = False
                    else:
                        success = api.commands.setFkGuideParent(componentGuides[-1], componentGuides[:-1])
                        if success:
                            output.displayInfo("Completed Setting parent for selected guides")
            if not passedValidation:
                output.displayWarning("Must select at least 2 guides on a FK compatible component")


class FkAddGuide(menu.MarkingMenuCommand):
    id = "hiveFkAddGuide"
    creator = "Zootools"

    @staticmethod
    def uiData(arguments):
        uiData = {"icon": "plusThin",
                  "label": "Add Guide",
                  "bold": False,
                  "italic": False,
                  "optionBox": False,
                  }
        return uiData

    def execute(self, arguments):
        validFkComponents = {}
        registry = api.Configuration().componentRegistry()
        fkChainObject = registry.findComponentByType("fkchain")
        for comp, nodes in arguments.get("componentToNodes", {}).items():
            if not isinstance(comp, fkChainObject):
                continue

            validFkComponents[comp] = nodes
        if not validFkComponents:
            return

        success = api.commands.addFkGuide(validFkComponents)
        if success:
            output.displayInfo("Completed Adding new guides to components")
