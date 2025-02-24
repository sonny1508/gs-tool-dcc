"""
from zoo.apps.hotkeyeditor.markingmenus import selectionset_markingmenu
selectionset_markingmenu.secondaryFunction()

"""

from maya import cmds

from zoo.libs.maya.markingmenu import menu

from zoo.apps.toolsetsui.run import openToolset
from zoo.libs.maya.cmds.sets import selectionsets
from zoo.apps.popupuis import selseticonpopup

SSET_TRACKER_INST = selectionsets.ZooSelSetTrackerSingleton()  # tracks options for the session


def secondaryFunction():
    """When the marking menu is released, run for a secondary feature

    Search for `SSET_TRACKER_INST.markingMenuTriggered = True ` to see where the trigger is set to be True
    """
    if SSET_TRACKER_INST.markingMenuTriggered:  # Ignore if the menu was triggered
        SSET_TRACKER_INST.markingMenuTriggered = False
        return
    namespace = selectionsets.namespaceFromSelection(message=False)  # remember namespace
    if namespace:
        SSET_TRACKER_INST.lastNamespace = namespace  # update to last remembered as valid
    SSET_TRACKER_INST.selectPrimarySet()  # loops through selection sets and selects sets based on selection


class SelectionSetMarkingMenuCommand(menu.MarkingMenuDynamic):
    """Command class for the Selection Set Marking Menu, dynamic menu style.

    This class creates the marking menu dictionary and passes it to the SelectionSetMarkingMenu() class.

    Map the following code to a hotkey press. Note: Change the key modifiers if using shift alt ctrl etc:

    .. code-block:: python

        import maya.mel as mel
        from zoo.libs.maya.markingmenu import menu as zooMenu
        zooMenu.MarkingMenu.buildDynamicMenu("selectionSetDynamicMenu",
                                             "menuNameSelectionSet",
                                             mel.eval("findPanelPopupParent"),
                                             {},
                                             options={"altModifier": False,
                                                      "shiftModifier": False})

    Map to hotkey release:

    .. code-block:: python

        from zoo.libs.maya.markingmenu import menu as zooMenu
        from zoo.apps.hotkeyeditor.markingmenus import selectionset_markingmenu
        zooMenu.MarkingMenu.removeExistingMenu("menuNameSelectionSet")
        # Secondary function -------------
        selectionset_markingmenu.secondaryFunction()

    """
    id = "selectionSetDynamicMenu"
    creator = "ZooTools"

    def execute(self, layout, arguments):
        """Example override creating a linear menu with passing arguments down to the MMCommands.

        :param layout: The layout instance to update.
        :type layout: :class:`menu.Layout`
        """
        # Build a dictionary for the
        # each command must be specified in the format of {"type": "command", "id": "mycommandid"}
        internalId = "selectionSetMarkingMenu"
        items = {"S": {"type": "command",
                       "id": internalId,
                       "arguments": {"operation": "createSelectionSet"}
                       },
                 "N": {"type": "command",
                       "id": internalId,
                       "arguments": {"operation": "selectSet"}
                       }, "W": {"type": "command",
                                "id": internalId,
                                "arguments": {"operation": "add"}
                                },
                 "E": {"type": "command",
                       "id": internalId,
                       "arguments": {"operation": "remove"}
                       },
                 "SE": {"type": "command",
                        "id": internalId,
                        "arguments": {"operation": "window"}
                        },
                 "NW": {"type": "command",
                        "id": internalId,
                        "arguments": {"operation": "show"}
                        },
                 "NE": {"type": "command",
                        "id": internalId,
                        "arguments": {"operation": "hide"}
                        },
                 "generic": []}

        # COLLECT SCENE VARIABLES --------------------------------------------------
        skip = False
        sceneNamespaces = selectionsets.sSetNamespacesInScene()
        sceneSets = selectionsets.setsInScene()
        namespaceOption = SSET_TRACKER_INST.optionNamespace
        namespace = selectionsets.namespaceFromSelection(message=False)

        if namespace:  # STORE SELECTED NAMSPACE ----------------
            if namespace not in sceneNamespaces:  # check if namespace exists in the scene
                namespace = ""
            SSET_TRACKER_INST.lastNamespace = namespace

        if not namespace:  # Figure the display name of the current namespace
            if not SSET_TRACKER_INST.lastNamespace:
                displayNamespace = "None"
            else:
                displayNamespace = str(SSET_TRACKER_INST.lastNamespace)
        else:
            displayNamespace = str(namespace)

        if namespaceOption == "selected":  # OPTION: SELECTED NAMESPACE --------------------------------
            if SSET_TRACKER_INST.lastNamespace:
                if SSET_TRACKER_INST.lastNamespace in sceneNamespaces:
                    selsets = selectionsets.sceneSetsByNamespace(SSET_TRACKER_INST.lastNamespace, ignoreHidden=True)
                else:  # not found so reset last found
                    SSET_TRACKER_INST.lastNamespace = ""
                    selsets = sceneSets
            else:
                SSET_TRACKER_INST.lastNamespace = ""
                selsets = sceneSets

            namespaceLabel = "Auto Namespace: {}".format(displayNamespace)
            namespaceFilterVal = True
            skip = True

        elif namespaceOption == "custom":  # OPTION: CUSTOM NAMESPACE --------------------------------

            namespace = SSET_TRACKER_INST.overrideNamespace
            if namespace:
                if namespace in sceneNamespaces:  # check if namespace exists in the scene
                    selsets = selectionsets.sceneSetsByNamespace(namespace, ignoreHidden=True)
                    namespaceLabel = "Cstm Namespace: {}".format(namespace)
                    namespaceFilterVal = True
                    skip = True

        elif ":" in namespaceOption:  # OPTION: NAMESPACE GIVEN --------------------------------
            namespace = SSET_TRACKER_INST.optionNamespace[:-1]
            # check if namespace exists in the scene
            if namespace in sceneNamespaces:
                selsets = selectionsets.sceneSetsByNamespace(namespace, ignoreHidden=True)
                namespaceLabel = "Cstm Namespace: {}".format(namespace)
                namespaceFilterVal = True
                skip = True

        else:  # OPTION: ALL NAMESPACES --------------------------------
            if displayNamespace in sceneNamespaces:
                selsets = sceneSets
                namespaceLabel = "Auto Namespace: {}".format(displayNamespace)
                namespaceFilterVal = False
                skip = True

        if not skip:  # No namespace set or were found so show all ------------------
            namespaceLabel = "Auto Namespace: None"
            selsets = sceneSets
            namespaceFilterVal = False

        # Namespace menu -----------------------
        items["SW"] = {"type": "command",
                       "id": internalId,
                       "arguments": {"operation": "namespace",
                                     "label": namespaceLabel,
                                     "checked": namespaceFilterVal}
                       }

        filteredSelSets = list()
        if selsets:
            for i, selset in enumerate(selsets):
                if not selectionsets.markingMenuVis(selset):
                    continue
                filteredSelSets.append(selset)
            selsets = filteredSelSets

        # Limit Menu Length --------------------------------------------------
        limitExceeded = False
        if len(selsets) > 30:
            selsets = selsets[:30]
            limitExceeded = True

        # Icons --------------------
        icons = list()
        if selsets:
            icons = selectionsets.icons(selsets)

        if selsets:
            for i, selset in enumerate(selsets):
                if not icons[i]:
                    icons[i] = "sets"
                selsetCommand = {"type": "command",
                                 "id": internalId,
                                 "arguments": {"operation": "selset_{}".format(selset),
                                               "selset": selset,
                                               "selsets": selsets,
                                               "icon": icons[i]}
                                 }
                items["generic"].append(selsetCommand)

        if limitExceeded:
            limitExceededCommand = {"type": "command",
                                    "id": internalId,
                                    "arguments": {"operation": "limitExceeded",
                                                  "icon": ""}
                                    }
            items["generic"].append(limitExceededCommand)

        # Update the layout object
        layout["items"] = items
        return layout


class SelectionSetMarkingMenu(menu.MarkingMenuCommand):
    """The selection set marking menu as called by the class SelectionSetMarkingMenuCommand()

    This class adds the labels and icons and execute functionality when the menu items are clicked.
    """
    id = "selectionSetMarkingMenu"  # id should never be changed
    creator = "Zootools"

    @staticmethod
    def uiData(arguments):
        operation = arguments.get("operation")
        if operation == "createSelectionSet":
            SSET_TRACKER_INST.markingMenuTriggered = True  # Register the menu as being clicked for secondaryFunction()
            return {"icon": "menu_sets",
                    "label": "Create New Selection Set",
                    "bold": False,
                    "italic": False,
                    "optionBox": False,
                    "optionBoxIcon": ""
                    }
        elif operation == "selectSet":
            return {"icon": "cursorSelect",
                    "label": "Select Associated Set (Default)",
                    "bold": False,
                    "italic": False,
                    "optionBox": False,
                    "optionBoxIcon": ""
                    }
        elif operation == "show":
            return {"icon": "eye",
                    "label": "Show In MM",
                    "bold": False,
                    "italic": False,
                    "optionBox": False,
                    "optionBoxIcon": ""
                    }
        elif operation == "hide":
            return {"icon": "invisible",
                    "label": "Hide In MM",
                    "bold": False,
                    "italic": False,
                    "optionBox": False,
                    "optionBoxIcon": ""
                    }
        elif operation == "window":
            return {"icon": "windowBrowser",
                    "label": "Options Window",
                    "bold": False,
                    "italic": False,
                    "optionBox": False,
                    "optionBoxIcon": ""
                    }
        elif operation == "namespace":
            return {"icon": "",
                    "label": arguments.get("label"),
                    "bold": False,
                    "italic": True,
                    "optionBox": False,
                    "checkBox": arguments.get("checked"),
                    "optionBoxIcon": ""
                    }
        elif operation == "add":
            return {"icon": "plusHollow",
                    "label": "Add Objs",
                    "bold": False,
                    "italic": False,
                    "optionBox": False,
                    "optionBoxIcon": ""
                    }
        elif operation == "remove":
            return {"icon": "minusHollow",
                    "label": "Remove Objs",
                    "bold": False,
                    "italic": False,
                    "optionBox": False,
                    "optionBoxIcon": ""
                    }
        elif operation.startswith("selset_"):
            return {"icon": arguments.get("icon"),
                    "label": arguments.get("selset"),
                    "bold": False,
                    "italic": False,
                    "optionBox": False,
                    "optionBoxIcon": ""
                    }
        elif operation == "limitExceeded":
            return {"icon": "",
                    "label": "------ Limit Exceeded ------",
                    "bold": False,
                    "italic": False,
                    "optionBox": False,
                    "optionBoxIcon": ""
                    }

    def execute(self, arguments):
        """The execute method is called when triggering the action item. use executeUI() for a optionBox.

        :type arguments: dict
        """
        operation = arguments.get("operation", "")

        if operation == "createSelectionSet":
            selseticonpopup.createSelectionSetWindow()
        elif operation == "selectSet":
            SSET_TRACKER_INST.selectPrimarySet()  # loops through selection sets and selects sets based on selection
            # selectionsets.selectFirstRelatedSelSet()
        elif operation == "namespace":  # Open options window
            checked = arguments.get("checked", "")
            if not checked:  # then turn on so set to be selected
                SSET_TRACKER_INST.optionNamespace = "selected"
                return
            # check off, so make all
            SSET_TRACKER_INST.optionNamespace = "all"
        elif operation == "window":
            openToolset("selectionSets", advancedMode=False)
        elif operation == "add":  # Open options window
            selectionsets.addRemoveNodesSel(add=True, includeRegSets=True, message=True)
        elif operation == "remove":  # Open options window
            selectionsets.addRemoveNodesSel(add=False, includeRegSets=True, message=True)
        elif operation == "show":  # Open options window
            selectionsets.setMarkingMenuVisSel(visibility=True, message=True)
        elif operation == "hide":  # Open options window
            selectionsets.setMarkingMenuVisSel(visibility=False, message=True)
        elif operation.startswith("selset_"):
            selSet = arguments.get("selset")
            if ":" in selSet:
                SSET_TRACKER_INST.lastNamespace = selSet.split(":")[0]
            else:
                SSET_TRACKER_INST.lastNamespace = ""
            SSET_TRACKER_INST.primarySets = [selSet]  # remember for next time.
            SSET_TRACKER_INST.loopSetIndex = 0

            cmds.select(selSet, replace=True)

    def executeUI(self, arguments):
        """The executeUI method is called when the user triggering the box icon on the right handle side
        of the action item.

        For this method to be called you must specify in the UIData method "optionBox": True.

        :type arguments: dict
        """
        pass
