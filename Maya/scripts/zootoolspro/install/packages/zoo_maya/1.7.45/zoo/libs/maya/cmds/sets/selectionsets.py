"""Code regarding selection sets

.. code-block:: python

    from zoo.libs.maya.cmds.sets import selectionsets
    selectionsets.setsInScene()

Author: Andrew Silke
"""
import maya.mel as mel
import maya.cmds as cmds

from zoovendor import six
from zoo.core.util import classtypes
from zoo.libs.utils import output

from zoo.libs.maya.cmds.objutils import attributes, namehandling

PRIORITY_ATTR = "zooCyclePriority"
MARKING_MENU_VIS_ATTR = "zooMMenuVisibility"
ICON_ATTR = "zooSSetIcon"


def createSelectionSet():
    """Creates a selection set with a warning if in earlier versions of Maya.
    User must create through the menu for the hotkey to become available.
    """
    try:
        mel.eval("defineCharacter;")
    except:
        output.displayWarning("Maya Issue: Please create a set with `Create > Sets > Quick Select Set` first "
                              "and then this hotkey will work.")


def createSelectionSetZooSel(setName, icon="", visibility=None, parentSet="", soloParent=True, flattenSets=False,
                             priority=0, selectionSet=True, message=True):
    """Creates a selection set. If the name already exists adds a new incremented name.

    With options for Zoo marking menu settings.  Uses the selection as the nodes to add to the set.

    :param setName: The name of the select set
    :type setName: str
    :param icon: A zoo icon name that will be displayed in the marking menu.
    :type icon: str
    :param visibility: Show or hide the selection set in the marking menu.  None will not set, default is show.
    :type visibility: bool
    :param parentSet: Parent the selection set inside another selection set, specify the name here.
    :type parentSet: str
    :param soloParent: If True will unparent the set from all other selection sets before parenting.
    :type soloParent: bool
    :param flattenSets: Flattens sets so that their contents are included but not the sets themselves.
    :type flattenSets: bool
    :param selectionSet: If True the set will be a selection set, False will be an object set.
    :type selectionSet: bool
    :param message: Report a message to the user?
    :type message: bool

    :return: The name of the new or existing selection set
    :rtype: str
    """
    if not setName:
        setName = "newSet"

    nodes = cmds.ls(selection=True)

    if flattenSets:
        nodes = flattenObjsInSets(nodes)

    # Force create with a unique name if it already exists --------------
    setName = str(namehandling.nonUniqueNameNumber(setName, shortNewName=True, paddingDefault=2))
    selSet = cmds.sets(nodes, name=setName)

    if selectionSet:
        cmds.sets(selSet, e=True, text="gCharacterSet")
        # Edit options for marking menu ----------------
        markingMenuSetup(setName, icon=icon, visibility=visibility, parentSet=parentSet, soloParent=soloParent,
                         priority=priority)
    if message:
        if selectionSet:
            output.displayInfo("Selection Set created: `{}`".format(selSet))
        else:
            output.displayInfo("Object Set created: `{}`")

    return setName


def nodesInSet(sSet):
    """Returns all the nodes in a object/selection set.

    :param sSet: a Maya set, can be object set or selection set.
    :type sSet: str
    :return: objects and nodes in the selection set.
    :rtype: list(str)
    """
    setDagNodes = cmds.listConnections("{}.dagSetMembers".format(sSet))
    if not setDagNodes:
        setDagNodes = list()
    else:  # There is setDagNodes
        setDagNodes = cmds.ls(setDagNodes, long=True)  # force long names as listConnections is unique
    setDnNodes = cmds.listConnections("{}.dnSetMembers".format(sSet))
    if not setDnNodes:
        setDnNodes = list()
    return setDagNodes + setDnNodes


def addNodes(sSet, nodes):
    cmds.sets(nodes, add=sSet)


def removeNodes(sSet, nodes):
    """Removes nodes/objs from a set.

    :param sSet: a Maya set, can be object set or selection set.
    :type sSet: str
    :param nodes: name of a maya node or object
    :type nodes: list(str)
    """
    cmds.sets(nodes, remove=sSet)


def addRemoveNodesSel(add=True, includeRegSets=True, message=True):
    """Adds or removes nodes to selection sets based on selection.

    Selection must have

    :param add: If True adds, if False removes
    :type add: bool
    :param includeRegSets: Include sets other than selection sets in the search?
    :type includeRegSets: bool

    :param message: Report a message to the user
    :type message: bool
    """
    addRemoveWord = ""
    selNodes = cmds.ls(selection=True)
    if not selNodes:
        if message:
            output.displayWarning("Nothing selected. Please select objects and selection set/s from the Outliner.")
        return
    sSets = sSetInList(selNodes, includeRegSets=includeRegSets)
    if not sSets:
        if message:
            output.displayWarning("No selection sets selected. "
                                  "Please include Selection Set/s from the Outliner in your selection.")
        return
    nodesToAddRemove = [x for x in selNodes if x not in sSets]  # remove the selection sets nodes from the sel nodes
    if not nodesToAddRemove:
        if message:
            output.displayWarning("No nodes or objects selected. "
                                  "Please include nodes other that sets in your selection.")
        return

    for sSet in sSets:  # do the add or remove for each set
        if add:
            cmds.sets(nodesToAddRemove, add=sSet)
            addRemoveWord = "added"
        else:
            cmds.sets(nodesToAddRemove, remove=sSet)
            addRemoveWord = "removed"
    if message:
        output.displayInfo("Success: nodes {} to set/s: `{}`".format(addRemoveWord, sSets))


def flattenOneLayer(nodes):
    """Finds any sets and replaces them with their contents.

    :param nodes: name of a maya node or object
    :type nodes: list(str)
    :return: The node list now including the set contents and minus any sets
    :rtype: list(str)
    """
    setsInObjs = list()
    nodesInObjs = list()
    for node in nodes:
        if cmds.nodeType(node) == "objectSet":
            setsInObjs.append(node)
        else:
            nodesInObjs.append(node)
    if setsInObjs:
        for sSet in setsInObjs:  # add contents of set as nodes, not sets.
            nodesInObjs += nodesInSet(sSet)
    return list(set(nodesInObjs))  # make unique


def sSetInListBool(nodes, includeRegSets=True):
    """Finds if a set is in a list of nodes, returns True if so.

    :param nodes: name of a maya node or object
    :type nodes: list(str)
    :param includeRegSets: Include sets other than selection sets in the search?
    :type includeRegSets: bool

    :return: True if a set was found, False if not
    :rtype: bool
    """
    for node in nodes:
        if cmds.nodeType(node) == "objectSet":
            if cmds.sets(node, q=True, text=True) == "gCharacterSet":  # selection sets only
                return True
            elif includeRegSets:
                return True
    return False


def sSetInList(nodes, includeRegSets=True):
    """Filters and returns all selection set nodes that are found in a node list.

    :param nodes: A list of Maya node names.
    :type nodes: list(str)
    :param includeRegSets: Include sets other than selection sets in the search?
    :type includeRegSets: bool

    :return: A list of selection set node names.
    :rtype: list(str)
    """
    selSets = list()
    for node in nodes:
        if cmds.nodeType(node) == "objectSet":
            if cmds.sets(node, q=True, text=True) == "gCharacterSet":  # selection sets only
                selSets.append(node)
            elif includeRegSets:  # All other set types
                selSets.append(node)
    return selSets


def sSetsInSelection(message=True, includeRegSets=True):
    """Finds any selection set nodes that are in the current selection.

    :param message: report messages to the user?
    :type message: bool
    :param includeRegSets: Include sets other than selection sets in the search?
    :type includeRegSets: bool

    :return: A list of selection set node names.
    :rtype: list(str)
    """
    sel = cmds.ls(selection=True)

    if not sel:
        if message:
            output.displayWarning("Nothing selected, please select selection sets in outliner.")
        return list()
    sSets = sSetInList(sel, includeRegSets=includeRegSets)
    if not sSets:
        if message:
            output.displayWarning("No sets found in the selection, please select selection sets in the outliner.")
        return list()
    return sSets


def flattenObjsInSets(nodes):
    """Takes a node list including sets, removes any sets including all their contents in the returned node list.

    Iterates over layers until no sets remain.

    :param nodes: A list of Maya nodes including sets
    :type nodes: list(str)
    :return: A list of Maya nodes with the set contents included and no sets.
    :rtype: list(str)
    """
    nodesInSet = list(nodes)
    while sSetInListBool(nodesInSet):
        nodesInSet = flattenOneLayer(nodesInSet)
    return nodesInSet


def addSelectionSet(selectSetName, objs, flattenSets=True):
    """Adds to an existing selection set, or if it doesn't exist then creates a new selection set

    :param selectSetName: The name of the select set
    :type selectSetName: str
    :param objs: A list of objects or nodes or components
    :type objs: list(str)
    :param flattenSets: Flattens sets so that their contents are included but not the sets themselves.
    :type flattenSets: bool
    :return selSet: The selection set name, if created could be a duplicate though unlikely
    :rtype selSet: str
    """
    if flattenSets:
        objs = flattenObjsInSets(objs)
    if not cmds.objExists(selectSetName):
        selSet = cmds.sets(objs, name=selectSetName)
        cmds.sets(selSet, e=True, text="gCharacterSet")
    else:
        cmds.sets(objs, addElement=selectSetName)
        selSet = str(selectSetName)
    return selSet


def setObjectSetAsSelectionSet(sSet, selectionSet=True, message=True):
    """Converts an object set to a selection set type (text="gCharacterSet")

    Or converts a selection set to an object set type (text="Unnamed object set")

    :param sSet: A Maya selection set name
    :type sSet: str
    :param selectionSet: Set the set to be a selection set True, or an object set False
    :type selectionSet: bool
    :param message: Report the message to the user?
    :type message: bool
    """
    if selectionSet:
        cmds.sets(sSet, e=True, text="gCharacterSet")
        if message:
            output.displayInfo("Set `{}` is now a Selection Set".format(sSet))
    elif cmds.sets(sSet, q=True, text=True) == "gCharacterSet":
        cmds.sets(sSet, e=True, text="Unnamed object set")
        if message:
            output.displayInfo("Set `{}` is now an Object Set".format(sSet))
    else:
        if message:
            output.displayInfo("Set `{}` is already an Object Set".format(sSet))
    return


def setObjectSetAsSelectionSet_sel(selectionSet=True, message=True):
    """Converts a selected set to a selection set type selectionSet=True (text="gCharacterSet")

    Or converts a selection set to an object set type selectionSet=False (text="Unnamed object set")

    :param selectionSet: Set the set to be a selection set True, or an object set False
    :type selectionSet: bool
    :param message: Report the message to the user?
    :type message: bool
    """
    selNodes = cmds.ls(selection=True, long=True)
    if not selNodes:
        if message:
            output.displayWarning("Nothing is selected, please sets")
        return "", list()
    for sSet in selNodes:
        if cmds.nodeType(sSet) == "objectSet":
            setObjectSetAsSelectionSet(sSet, selectionSet=selectionSet, message=message)


def filterSets(sSet, selectionSets=True, objectSets=False, ignoreHidden=False):
    """Given a set of node type "objectSet" return it if it matches the criteria.

        selectionSet or objectSet

    :param sSet: The name of a selection set, node type "objectSet"
    :type sSet: str
    :param selectionSets: Returns set if "selection sets", checks for "gCharacterSet"
    :type selectionSets: bool
    :param objectSets:  Returns set if "objects sets", checks for "Unnamed object set"
    :type objectSets: bool
    :param ignoreHidden:  Ignore sets that are marked as hidden in the zoo marking menu
    :type ignoreHidden: bool

    :return: The selection set name if found. "" if the set does not meet the criteria.
    :rtype: str
    """

    def returnSet(sSet):
        if ignoreHidden:
            if markingMenuVis(sSet):
                return sSet
            else:
                return ""
        else:
            return sSet

    if cmds.sets(sSet, q=True, text=True) == "gCharacterSet" and selectionSets:  # then is a selection set
        return returnSet(sSet)

    if cmds.sets(sSet, q=True, text=True) == "Unnamed object set" and objectSets:  # then is a object set
        return returnSet(sSet)
    return ""


def setsInScene(selectionSets=True, objectSets=False, ignoreHidden=False):
    """Returns all selection sets in the scene matching the node type "objectSet".

    Can return selection sets, objects sets or both.

    :param selectionSets: Returns sets that are "selection sets", checks for "gCharacterSet"
    :type selectionSets: bool
    :param objectSets:  Returns sets that are "objects sets", checks for "Unnamed object set"
    :type objectSets: bool
    :param ignoreHidden:  Ignore sets that are marked as hidden in the zoo marking menu
    :type ignoreHidden: bool

    :return selSets: all the selection set names found in the scene
    :rtype selSets: list(str)
    """
    returnedSets = list()
    allSetsList = cmds.ls(sets=True)
    if not allSetsList:
        return list()
    for sSet in allSetsList:
        if cmds.nodeType(sSet) == "objectSet":
            returnedSet = filterSets(sSet, selectionSets=selectionSets,
                                     objectSets=objectSets,
                                     ignoreHidden=ignoreHidden)
            if returnedSet:
                returnedSets.append(returnedSet)
    return returnedSets


def setsRelatedToObj(obj, extendToShape=False, selectionSets=True, objectSets=False, ignoreHidden=False):
    """Returns all sets related to an object or node.

    Set are of node type "objectSet" and can be selection sets or object sets.

    :param obj: Object or maya node as a string name
    :type obj: str
    :param extendToShape: Includes shape nodes while searching for sets.
    :type extendToShape: bool
    :param selectionSets: Returns sets that are "selection sets", checks for "gCharacterSet"
    :type selectionSets: bool
    :param objectSets:  Returns sets that are "objects sets", checks for "Unnamed object set"
    :type objectSets: bool
    :param ignoreHidden:  Ignore sets that are marked as hidden in the zoo marking menu
    :type ignoreHidden: bool

    :return: A list of set names related to the node/obj.
    :rtype: list(str)
    """
    returnedSets = list()
    relatedSets = cmds.listSets(object=obj, extendToShape=extendToShape)
    if not relatedSets:
        return list()
    parentSets = allParents(relatedSets)
    if parentSets:  # add parent sets as they also contain the object/node
        relatedSets += parentSets
    for sSet in relatedSets:  # filter selection sets or object sets
        returnedSet = filterSets(sSet, selectionSets=selectionSets, objectSets=objectSets, ignoreHidden=ignoreHidden)
        if returnedSet:
            returnedSets.append(returnedSet)
    return list(set(returnedSets))


def relatedSelSets(extendToShape=False, selectionSets=True, objectSets=False, message=True):
    """Returns the selection and the related sets to the current selection.

    Includes options

    Sets are of node type "objectSet" and can be selection sets or object sets.

    :param extendToShape: Includes shape nodes while searching for sets.
    :type extendToShape: bool
    :param selectionSets: Returns sets that are "selection sets", checks for "gCharacterSet"
    :type selectionSets: bool
    :param objectSets:  Returns sets that are "objects sets", checks for "Unnamed object set"
    :type objectSets: bool
    :param message: Report a message to the user?
    :type message: bool

    :return: A list of set names related to the selected nodes or objects.
    :rtype: list(str)
    """
    selNodes = cmds.ls(selection=True, long=True)
    if not selNodes:
        if message:
            output.displayWarning("Nothing is selected, please select objects or nodes")
        return "", list(), selNodes
    # Selection found -------------
    for node in selNodes:
        relatedSets = setsRelatedToObj(node,
                                       extendToShape=extendToShape,
                                       selectionSets=selectionSets,
                                       objectSets=objectSets)
        if relatedSets:
            return node, relatedSets, selNodes
    if message:
        output.displayWarning("No related sets found.")
    return "", list(), selNodes


def parentSelectionSets(sSetChildren, sSetParent):
    """Parents a list of selection sets to another"""
    for sSet in sSetChildren:
        cmds.sets(sSet, forceElement=sSetParent)


def parent(sSet):
    """Returns the parent of a selection set. Returns "" if no parent.

    :param sSet: A maya object or selection set
    :type sSet: str
    :return: A maya set name or "" if None found
    :rtype: str
    """
    connections = cmds.listConnections('.'.join([sSet, "message"]))
    if not connections:
        return ""
    for node in connections:
        if cmds.nodeType(node) == "objectSet":
            return node
    return ""


def parents(sSet, selectionSets=True):
    """Returns all the sets that a set is a member of, ie parent sets.

    :param sSet: A maya object or selection set
    :type sSet: str
    :param selectionSets: Return only selection sets if True, object sets will be ignored.
    :type selectionSets: bool
    :return: A list of selection set nodes, if none will be an empty list.
    :rtype: list(str)
    """
    parentSets = list()
    connections = cmds.listConnections('.'.join([sSet, "message"]))
    if not connections:
        return list()
    for node in connections:
        if cmds.nodeType(node) == "objectSet":
            if selectionSets:
                if cmds.sets(sSet, e=True, text="gCharacterSet"):
                    parentSets.append(node)
            else:
                parentSets.append(node)
    return parentSets


def unParentAll(sSet):
    """Unparent the selection set from all other sets.

    This is really just unassigning the set from all other selection sets as sets aren't part of a DAG hierarchy.

    :param sSet: A maya object or selection set
    :type sSet: str
    """
    parentSets = parents(sSet, selectionSets=True)
    if parentSets:
        for pSet in parentSets:
            cmds.sets(sSet, remove=pSet)  # unparent


def allParents(sSets, safetyLimit=1000):
    """Returns all parent sets including all grandparents etc

    :param sSets: A list of selection set node names
    :type sSets: list(str)
    :param safetyLimit: In case of errors stop cycling at this loop number.
    :type safetyLimit: int

    :return: A list of set names
    :rtype: list(str)
    """
    selSets = list(sSets)
    parentSets = list()
    count = 0
    while selSets:
        count += 1
        parents = cmds.listConnections('.'.join([selSets[0], "message"]))
        if parents:
            for p in parents:  # will be only one set as a parent
                if cmds.nodeType(p) == "objectSet":
                    parentSets.append(p)
                    selSets.append(p)
        del selSets[0]  # remove the operated set for next loop
        if count == safetyLimit:
            break
    return parentSets


def allChildren(sSets, safetyLimit=1000):
    """Returns all children sets including grandchildren

    :param sSets: A list of selection set node names
    :type sSets: list(str)
    :param safetyLimit: In case of errors stop cycling at this loop number.
    :type safetyLimit: int

    :return: A list of set names
    :rtype: list(str)
    """
    selSets = list(sSets)
    childrenSets = list()
    count = 0
    while selSets:
        count += 1
        children = cmds.listConnections('.'.join([selSets[0], "dnSetMembers"]))
        if children:
            childrenSets += children
            selSets += children
        del selSets[0]  # remove the operated set for next loop
        if count == safetyLimit:
            break
    return childrenSets


def hierarchyDepth(sSet):
    """Calculates the depth of the hierarchy of a set that is parented to other sets.

    Returns 0 if in world.

    :param sSet: A maya object or selection set
    :type sSet: str
    :return: depth of the set, the parented depth
    :rtype: int
    """
    count = -1
    while sSet != "":
        sSet = parent(sSet)
        count += 1
    return count


# ------------------------------
# MARKING MENU VISIBILITY
# ------------------------------


def addSSetZooOptions(setName, nodes, icon="", visibility=None, parentSet="", soloParent=True, flattenSets=False):
    """Creates or adds to an existing selection set. With options for Zoo marking menu settings.

    :param setName: The name of the select set
    :type setName: str
    :param nodes: A list of objects or nodes or components
    :type nodes: list(str)
    :param icon: A zoo icon name that will be displayed in the marking menu.
    :type icon: str
    :param visibility: Show or hide the selection set in the marking menu.  None will not set, default is show.
    :type visibility: bool
    :param parentSet: Parent the selection set inside another selection set, specify the name here.
    :type parentSet: str
    :param soloParent: If True will unparent the set from all other selection sets before parenting.
    :type soloParent: bool
    :param flattenSets: Flattens sets so that their contents are included but not the sets themselves.
    :type flattenSets: bool

    :return: The name of the new or existing selection set
    :rtype: str
    """
    selSet = addSelectionSet(setName, nodes, flattenSets=flattenSets)
    markingMenuSetup(selSet, icon=icon, visibility=visibility, parentSet=parentSet, soloParent=soloParent)
    return selSet


def addSSetZooOptionsSel(setName, icon="", visibility=None, parentSet="", soloParent=True, flattenSets=False):
    """Creates or adds to an existing selection set. With options for Zoo marking menu settings.

    Uses the selection as the nodes to add to the set

    :param setName: The name of the select set
    :type setName: str
    :param nodes: A list of objects or nodes or components
    :type nodes: list(str)
    :param icon: A zoo icon name that will be displayed in the marking menu.
    :type icon: str
    :param visibility: Show or hide the selection set in the marking menu.  None will not set, default is show.
    :type visibility: bool
    :param parentSet: Parent the selection set inside another selection set, specify the name here.
    :type parentSet: str
    :param soloParent: If True will unparent the set from all other selection sets before parenting.
    :type soloParent: bool
    :param flattenSets: Flattens sets so that their contents are included but not the sets themselves.
    :type flattenSets: bool

    :return: The name of the new or existing selection set
    :rtype: str
    """
    if not setName:
        setName = "newSet"

    nodes = cmds.ls(selection=True)
    if not nodes:
        output.displayWarning("Nothing is selected, please select nodes for the selection set.")
        return

    addSSetZooOptions(setName, nodes, icon=icon, visibility=visibility, parentSet=parentSet, soloParent=soloParent,
                      flattenSets=flattenSets)


def markingMenuSetup(sSet, icon="", visibility=None, parentSet="", soloParent=True, priority=None):
    """Convenience function for setting up a selection set for the Zoo marking menu.

    - adds icon, visibility and parent set with options

    :param sSet: A maya object or selection set
    :type sSet: str
    :param icon: A zoo icon name that will be displayed in the marking menu.
    :type icon: str
    :param visibility: Show or hide the selection set in the marking menu.  None will not set, default is show.
    :type visibility: bool
    :param parentSet: Parent the selection set inside another selection set, specify the name here.
    :type parentSet: str
    :param soloParent: If True will unparent the set from all other selection sets before parenting.
    :type soloParent: bool
    :param priority: Sets the marking menu priority as an int, higher numbers will prioritise while cycling.
    :type priority: int
    """
    if icon:
        setIcon(sSet, icon)
    if visibility is not None:
        setMarkingMenuVis(sSet, visibility=visibility)
    if soloParent and parentSet:
        unParentAll(sSet)
    if priority is not None:
        setPriorityValue(sSet, priority)
    if parentSet:
        cmds.sets(sSet, forceElement=parentSet)


def setMarkingMenuVis(sSet, visibility=False):
    """Sets the priority value of a set by creating or changing the "zooSetPriority" attribute

    :param sSet: A maya object or selection set
    :type sSet: str
    :param visibility: The visibility of the selection set in the Zoo Tools Sel Set Marking Menu
    :type visibility: bool

    :return: The attribute was successfully set, False if node is locked
    :rtype: bool
    """
    if not cmds.attributeQuery(MARKING_MENU_VIS_ATTR, node=sSet, exists=True):  # Try to create it.
        if cmds.lockNode(sSet, query=True)[0]:  # node is locked
            return False
        attributes.createAttribute(sSet, MARKING_MENU_VIS_ATTR,
                                   attributeType="bool",
                                   channelBox=True,
                                   defaultValue=True)
    cmds.setAttr(".".join([sSet, MARKING_MENU_VIS_ATTR]), visibility)
    return True


def setMarkingMenuVisSel(visibility=0, message=True):
    """Sets the `marking menu visibility` attribute on any selected `selection set` nodes.

    :param visibility: The visibility of the selection set in the Zoo Tools Sel Set Marking Menu
    :type visibility: bool
    :param message: Report a message to the user?
    :type message: bool
    """
    failed = list()
    sSets = sSetsInSelection(message=message)
    if not sSets:  # messages already given
        return
    for sSet in sSets:
        if not setMarkingMenuVis(sSet, visibility=visibility):
            failed.append(sSet)
    if message and not failed:
        output.displayInfo("Success: Marking menu visibility set to `{}` "
                           "on selection sets: {}".format(str(visibility), sSets))
    elif message and failed:
        output.displayWarning("Set/s were not able to be set and are likely locked, please unlock: {} "
                              "with Zoo's `Manage Nodes Plugins` Tool".format(failed))


def markingMenuVis(sSet):
    """Returns the marking menu visibility value of a set, if it doesn't have one will return True (visible)

    :param sSet: A maya object or selection set
    :type sSet: str
    :return: The marking menu visibility value of the set
    :rtype: bool
    """
    if not cmds.attributeQuery(MARKING_MENU_VIS_ATTR, node=sSet, exists=True):
        return True
    return cmds.getAttr(".".join([sSet, MARKING_MENU_VIS_ATTR]))


# ------------------------------
# SELECTION SET CYCLE PRIORITY
# ------------------------------


def setPriorityValue(sSet, priority=0):
    """Sets the priority value of a set by creating or changing the "zooSetPriority" attribute

    :param sSet: A maya object or selection set
    :type sSet: str
    :param priority: The priority, higher is more selectable.
    :type priority: int

    :return: The attribute was successfully set, False if node is locked
    :rtype: bool
    """
    if not cmds.attributeQuery(PRIORITY_ATTR, node=sSet, exists=True):  # Try to create it.
        if cmds.lockNode(sSet, query=True)[0]:  # node is locked
            return False
        attributes.createAttribute(sSet, PRIORITY_ATTR, attributeType="long", channelBox=True, defaultValue=True)
    cmds.setAttr(".".join([sSet, PRIORITY_ATTR]), priority)
    return True


def setPriorityValueSel(priority=0, message=True):
    """Sets the cycle priority on any selected selection set nodes.

    :param priority: The cycle priority to set on the selected selection sets. Higher is more selectable while cycling.
    :type priority: int
    :param message: Report a message to the user?
    :type message: bool
    """
    failed = list()
    sSets = sSetsInSelection(message=message)
    if not sSets:  # messages already given
        return
    for sSet in sSets:
        if not setPriorityValue(sSet, priority=priority):
            failed.append(sSet)
    if message and not failed:
        output.displayInfo("Success: Cycle priority set to `{}` "
                           "on selection sets: {}".format(str(priority), sSets))
    elif message and failed:
        output.displayWarning("Set/s were not able to be set and are likely locked, please unlock: {} "
                              "with Zoo's `Manage Nodes Plugins` Tool".format(failed))


def priorityValue(sSet):
    """Returns the priority value of a set, if it doesn't have one will return 0

    :param sSet: A maya object or selection set
    :type sSet: str
    :return: The priority value of the set
    :rtype: int
    """
    if not cmds.attributeQuery(PRIORITY_ATTR, node=sSet, exists=True):
        return 0
    return cmds.getAttr(".".join([sSet, PRIORITY_ATTR]))


def sortPriorityList(sSets, priorityList, priorityDict):
    """Helper function for sorting sets by priority or depth

    :param sSets: A list of maya object or selection sets
    :type sSets: list(str)
    :param priorityList: A list of priority or depth numbers
    :type priorityList: list(int)
    :param priorityDict: A dictionary of sSets as the keys and priority/depth ints as the values.
    :type priorityDict: dict()
    :return: The sorted list of sets now in order
    :rtype: list(str)
    """
    sortedList = list()
    priorityList = list(set(priorityList))  # remove duplicates and sort reverse order [3, 2, 1, 0]
    if len(priorityList) == 1:  # no need to sort all at the same level
        return sSets
    priorityList.sort(reverse=True)
    for number in priorityList:  # reversed
        for sSet in sSets:
            if priorityDict[sSet] == number:  # if match
                sortedList.append(sSet)
    return sortedList


def sortSSetPriority(sSets, alphabetical=True, priority=True, hierarchy=True):
    """Sorts selection sets (or object sets) based on any of the following: alphabetical, priority, hierarchy

    :param sSets: A list of maya object or selection sets
    :type sSets: list(str)
    :param alphabetical: Sort alphabetically (first)
    :type alphabetical: bool
    :param priority: Sort by priority (last)
    :type priority: bool
    :param hierarchy: Sort by hierarchy (second)
    :type hierarchy: bool
    :return: The sorted list of sets now in order
    :rtype: list(str)
    """
    priorityList = list()
    priorityDict = dict()

    # alphabetical ------------------------------
    if alphabetical:
        sSets = [str(i) for i in sSets]  # convert to strings if unicode
        sSets.sort(key=str.lower)
    # hierarchy ---------------------------------

    if hierarchy:
        for sSet in sSets:
            priorityNumber = hierarchyDepth(sSet)  # gets the priority of the set
            priorityList.append(priorityNumber)  # adds the priority number to a list ie [0, 1, 0, 3]
            priorityDict[sSet] = priorityNumber  # {"someSet": 0, "someSet2": 1, "someSet2": 0}
        sSets = sortPriorityList(sSets, priorityList, priorityDict)

    # priority ----------------------------------
    if priority:
        for sSet in sSets:
            priorityNumber = priorityValue(sSet)  # gets the priority of the set
            priorityList.append(priorityNumber)  # adds the priority number to a list ie [0, 1, 0, 3]
            priorityDict[sSet] = priorityNumber  # {"someSet": 0, "someSet2": 1, "someSet2": 0}

        sSets = sortPriorityList(sSets, priorityList, priorityDict)
    return sSets


# ------------------------------
# NAMESPACE FILTERING
# ------------------------------

def sSetNamespacesInScene(selectionSets=True, objectSets=False, addColon=False):
    """Returns all the namespaces that belong to sets in the scene.

    :param selectionSets: Returns sets that are "selection sets", checks for "gCharacterSet"
    :type selectionSets: bool
    :param objectSets:  Returns sets that are "objects sets", checks for "Unnamed object set"
    :type objectSets: bool

    :return: A list of namespaces that belong to sets in the scene.
    :rtype: list(str)
    """
    namespacesInScene = list()
    namespaces = namehandling.namespacesInScene()
    if not namespaces:
        return list()
    sSets = setsInScene(selectionSets=selectionSets, objectSets=objectSets)
    if not sSets:
        return list()
    for namespace in namespaces:
        for sSet in sSets:
            if "{}:".format(namespace) in sSet:
                namespacesInScene.append(namespace)
    namespacesInScene = list(set(namespacesInScene))
    if addColon:
        for i, name in enumerate(namespacesInScene):
            namespacesInScene[i] = "{}:".format(name)
    return namespacesInScene


def filterSetsByNameSpace(sSets, namespace, ignoreHidden=False):
    """Filters selection sets that have the given namespace, returns sets with the matching namespace.

    :param sSets: A list of Maya selection set names.
    :type sSets: list(str)
    :param namespace: The namespace to use as the filter.
    :type namespace: str
    :param ignoreHidden: Will also filter out any sel sets that have been marked as hidden in the Zoo marking menu.
    :type ignoreHidden: bool
    :return: A list of sets with the matching namespace.
    :rtype: list(str)
    """
    filteredSets = list()
    for sSet in sSets:
        if sSet.startswith("{}:".format(namespace)):
            filteredSets.append(sSet)
    if not ignoreHidden:
        return filteredSets
    filteredShownSets = list()
    for sSet in filteredSets:
        if markingMenuVis(sSet):
            filteredShownSets.append(sSet)
    return filteredShownSets


def sceneSetsByNamespace(namespace, ignoreHidden=False):
    """Returns all selection sets that have the given namespace.  Can filter out Zoo Marking Menu hidden sets.

    :param namespace: The namespace to use as the filter.
    :type namespace: str
    :param ignoreHidden: Will also filter out any sel sets that have been marked as hidden in the Zoo marking menu.
    :type ignoreHidden: bool
    :return: A list of maya selection set names matching the namespace.
    :rtype: list(str)
    """
    sSets = setsInScene(selectionSets=True, objectSets=False)
    if not sSets:
        return list()
    return filterSetsByNameSpace(sSets, namespace, ignoreHidden=ignoreHidden)


def sceneSetsByNamespaceSel(ignoreHidden=False):
    """Returns all selection sets that match the namespace of the first selected object.

    Can filter out Zoo Marking Menu hidden sets.

    :param ignoreHidden: Will also filter out any sel sets that have been marked as hidden in the Zoo marking menu.
    :type ignoreHidden: bool
    :return: A list of maya selection set names matching the namespace.
    :rtype: list(str)
    """
    sSets = setsInScene(selectionSets=True, objectSets=False)
    if not sSets:
        return list()
    namespace = namehandling.namespaceSelected(message=False)
    if not namespace:
        return sSets
    return filterSetsByNameSpace(sSets, namespace, ignoreHidden=ignoreHidden)


def namespaceFromSelection(message=True):
    """Returns the namespace from the first selected node.

    :param message: Report a message tot he user?
    :type message: bool
    :return: the namespace name if one was found. "" if not found
    :rtype: str
    """
    return namehandling.namespaceSelected(message=message)


# ------------------------------
# ICONS
# ------------------------------


def icon(sSet):
    """Returns the marking menu icon of the given selection set.

    :param sSet: A maya selection set name
    :type sSet: str
    :return: The name of the icon on the given selection set, returns "" if None found.
    :rtype: str
    """
    if not cmds.attributeQuery(ICON_ATTR, node=sSet, exists=True):
        return ""
    return cmds.getAttr(".".join([sSet, ICON_ATTR]))


def icons(sSets):
    """Returns all the icons from a list of selection set names.

    :param sSets: A list of maya object or selection sets
    :type sSets: list(str)
    :return: A list of icon names, icons will be "" if None found.
    :rtype: list(str)
    """
    iconNames = list()
    for sSet in sSets:
        iconNames.append(icon(sSet))
    return iconNames


def setIcon(sSet, iconName):
    """Adds a Zoo icon on the given selection sets. For the Zoo Sel Set Marking Menu.

    :param sSet: A maya selection set name
    :type sSet: str
    :param iconName: The name of the zoo icon to set, remove _64.png etc. eg "save"
    :type iconName: str
    """
    if not cmds.attributeQuery(ICON_ATTR, node=sSet, exists=True):  # Try to create it.
        if cmds.lockNode(sSet, query=True)[0]:  # node is locked
            return False
        cmds.addAttr(sSet, longName=ICON_ATTR, dataType="string")
    cmds.setAttr(".".join([sSet, ICON_ATTR]), iconName, type="string")
    return True


def setIconSel(iconName, message=True):
    """Adds a Zoo icon on the selected selection sets. For the Zoo Sel Set Marking Menu.

    :param iconName: The name of the zoo icon to set, remove _64.png etc. eg "save"
    :type iconName: str
    :param message: report a message to the user?
    :type message: bool
    """
    failed = list()
    sSets = sSetsInSelection(message=message)
    if not sSets:  # messages already given
        return
    for sSet in sSets:
        if not setIcon(sSet, iconName):
            failed.append(sSet)
    if message and not failed:
        output.displayInfo("Success: Icon set to `{}` "
                           "on selection sets: {}".format(str(iconName), sSets))
    elif message and failed:
        output.displayWarning("Set/s were not able to be set and are likely locked, please unlock: {} "
                              "with Zoo's `Manage Nodes Plugins` Tool".format(failed))


# ------------------------------
# TRACK DATA
# ------------------------------


@six.add_metaclass(classtypes.Singleton)
class ZooSelSetTrackerSingleton(object):
    """Used by the selection set marking menu, tracks data for selection sets

    """

    def __init__(self):
        # ----------------
        self.markingMenuTriggered = False

        # Primary Object management ---------
        self.primaryObject = ""
        self.primarySets = list()
        self.loopSetIndex = 0
        self.lastSetLen = 0

        # Options from potential UI ----------
        self.optionSelectionSet = True  # select selection sets
        self.optionObjectSet = False  # select object sets
        self.optionExtendToShape = False  # include shape nodes while finding sets

        # Namespace ------------------
        self.optionNamespace = "all"  # "selected", "aNameSpaceName:", "all", "custom"
        self.lastNamespace = ""
        self.overrideNamespace = ""

    def resetPrimaryObject(self):
        """Resets the primary object"""
        self.primaryObject = ""
        self.primarySets = list()
        self.lastSetLen = 0
        self.loopSetIndex = 0

    def _selectNodesInOrder(self, sSet):
        """Selects the sets contents with the primary object at the start of the selection"""
        setNodes = nodesInSet(sSet)
        setNodes = [i for i in setNodes if i != self.primaryObject]  # remove self.primaryObject
        setNodes = [self.primaryObject] + setNodes  # add primary obj at index[0]
        cmds.select(setNodes, replace=True)
        return setNodes

    def _setLastSetLen(self):
        """Sets self.lastSetLen which records the amount of objects selected at the end of self.selectPrimarySet()
        """
        selNodes = cmds.ls(selection=True)
        if selNodes:
            self.lastSetLen = len(selNodes)
        else:
            self.lastSetLen = 0

    def selectPrimarySet(self, message=True):
        """Selects the first selection set found on first go.

        Supports looping through all the selection sets found.

        Sets and controls depending on the state:

            self.primaryObject: str: Is the first object selected, and it remembers this for each cycle.
            self.primarySets: list(str): Are all the related sets to the primary object
            self.lastSetLen: int: is the number of selected objects, uses as a comparison to potentially restart cycle
            self.loopSetIndex: int: Is the index referring to self.primary[x] , tracks how many times the sets cycle.

        :param message: report a message to the user?
        :type message: bool
        """
        startAgain = False
        selNode, selSets, selNodes = relatedSelSets(extendToShape=self.optionExtendToShape,
                                                    selectionSets=self.optionSelectionSet,
                                                    objectSets=self.optionObjectSet,
                                                    message=False)

        # There's only one related selection set, so there's no need to cycle ---------------------------
        if not selNode and len(self.primarySets) == 1:  # then just select the given selection set.
            if cmds.objExists(self.primarySets[0]):
                cmds.select(self.primarySets[0], replace=True)
            else:
                output.displayWarning("Nothing is selected, please select objects or nodes")
            self._setLastSetLen()  # sets self.lastSetLen
            return "", list()  # don't do anything

        # No selection sets were found related to the current selection --------------------------
        if not selSets:
            if self.primarySets and not selNodes:  # Nothing is selected so select the last saved set
                sSet = self.primarySets[self.loopSetIndex]
                setNodes = self._selectNodesInOrder(sSet)  # Select and keep primary object at index 0
                self._setLastSetLen()  # sets self.lastSetLen
                return sSet, setNodes
            else:  # reset, nothing was found --------------
                self.resetPrimaryObject()
                if message:
                    if selNodes:
                        output.displayWarning("No `selection sets` found related to the selected nodes. "
                                              "Be sure that any sets are `selection sets`.")
                    else:
                        output.displayWarning("Nothing is selected, please select objects or nodes")
                self.lastSetLen = 0
                return "", list()

        # Check the number of selected objects matches the last loop number, should match for cycling. --------------
        if selNodes and self.lastSetLen:
            if self.lastSetLen != len(selNodes):  # Doesn't match so start from the beginning again in the cycle.
                startAgain = True

        # Something's changed so start from beginning of the cycle -----------------------------
        if not self.primaryObject or self.primaryObject != selNode or startAgain:
            self.primaryObject = selNode
            self.primarySets = sortSSetPriority(selSets, alphabetical=True, priority=True, hierarchy=True)  # sort
            self.loopSetIndex = 0
            setNodes = self._selectNodesInOrder(self.primarySets[0])  # Select and keep primary object at index 0
            if message:
                output.displayInfo("Selected selection set: `{}`".format(self.primarySets[0]))
            self._setLastSetLen()  # sets self.lastSetLen
            return self.primarySets[0], setNodes

        # Primary object is a match so increment to next set ---------------------------------------
        numberOfSets = len(self.primarySets)
        if self.loopSetIndex + 1 >= numberOfSets:  # Max hit so reset and start again
            self.loopSetIndex = 0
        else:
            self.loopSetIndex += 1
        sSet = self.primarySets[self.loopSetIndex]  # The set to select

        if not cmds.objExists(sSet):
            if message:
                output.displayWarning("The selection set `{}` no longer exists".format(sSet))
            self.resetPrimaryObject()
            self.lastSetLen = 0
            return "", list()

        # All checks passed so select the next set :) ------------------------------------------------------
        setNodes = self._selectNodesInOrder(sSet)  # Select and keep primary object at index 0
        if message:
            output.displayInfo("Selected selection set: `{}`".format(sSet))
        self._setLastSetLen()  # sets self.lastSetLen
        return sSet, setNodes
