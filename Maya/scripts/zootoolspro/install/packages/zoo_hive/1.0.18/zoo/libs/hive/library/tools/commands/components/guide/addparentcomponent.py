from zoo.libs.maya.mayacommand import command
from zoo.libs.hive import api, constants
from zoo.libs.maya import zapi


class AddParentComponentFromSelectionCommand(command.ZooCommandMaya):
    id = "hive.component.parent.selectionAdd"
    
    isUndoable = True
    useUndoChunk = True  # Chunk all operations in doIt()
    disableQueue = True  # If true, disable the undo queue in doIt()

    _drivenComponents = []
    _driverComponent = []

    def resolveArguments(self, arguments):
        selection = list(zapi.selected(filterTypes=zapi.kTransform))
        if len(selection) < 2:
            self.displayWarning("Must have at least 2 nodes selected.")
            return
        # the last node in the selection is the driver node
        drivenNodes = selection[:-1]
        driver = selection[-1]
        if not api.Guide.isGuide(driver):
            self.displayWarning("Driver is not a Guide")
            return
        driverGuide = api.Guide(driver.object())
        if driverGuide.isRoot():
            self.displayWarning("Parenting to the root guide isn't allowed")
            return

        driverComp = api.componentFromNode(driver)
        if not driverComp.idMapping()[constants.DEFORM_LAYER_TYPE].get(driverGuide.id()):
            self.displayWarning("Setting parent to a guide which doesn't belong to a joint(Sphere shapes) isn't "
                                "allowed")
            return

        visited = set()
        drivenComponentMap = []
        for driven in drivenNodes:
            if not api.Guide.isGuide(driven):
                # self.cancel("Driven is not a Guide")
                self.displayWarning("Driven is not a Guide")
                return
            drivenComp = api.componentFromNode(driven)
            if not drivenComp:
                continue
            if drivenComp in visited or drivenComp == driverComp:
                continue
            visited.add(drivenComp)
            drivenComponentMap.append(drivenComp)
        if driverComp is None:
            self.displayWarning("Failed to find any hive components have selection.")
            return
        if not drivenComponentMap:
            self.displayWarning("No Valid Driven guides to parent.")
            return
        self._driverComponent = (driverComp, driverGuide)
        self._drivenComponents = drivenComponentMap

        arguments["driver"] = self._driverComponent[1]
        arguments["driven"] = drivenComponentMap
        return arguments

    def doIt(self, driver=None, driven=None):
        """

        :param driver:
        :type driver: list(tuple(component, Guide)
        :param driven:
        :type driven: list(Guide)
        :return:
        :rtype:
        """
        driver = self._driverComponent
        success = False
        for comp in self._drivenComponents:
            success = comp.setParent(driver[0],
                                     driver[1])
        return success

    def undoIt(self):
        driver = self._driverComponent
        for comp in self._drivenComponents:
            comp.removeParent(driver[0])


class AddParentComponent(command.ZooCommandMaya):
    id = "hive.component.parent.add"
    
    isUndoable = True
    useUndoChunk = True  # Chunk all operations in doIt()
    disableQueue = True  # If true, disable the undo queue in doIt()

    _childComponent = None
    _parentComponent = None

    def resolveArguments(self, arguments):
        self._childComponent = arguments["childComponent"]
        self._parentComponent = arguments["parentComponent"]
        return arguments

    def doIt(self, parentComponent=None, parentGuide=None, childComponent=None):
        """
        
        :param parentComponent:
        :type parentComponent: zoo.libs.hive.base.component.Component 
        :param parentGuide: 
        :type parentGuide: zoo.libs.hive.base.hivenodes.hnodes.Guide
        :param childComponent:
        :type childComponent: zoo.libs.hive.base.component.Component
        :return:
        :rtype:
        """

        return childComponent.setParent(parentComponent,
                                        driver=parentGuide,
                                        )

    def undoIt(self):
        self._childComponent.removeParent(self._parentComponent)


class RemoveAllParentsComponentFromSelectionCommand(command.ZooCommandMaya):
    id = "hive.component.parent.removeAll"
    
    isUndoable = True
    useUndoChunk = True  # Chunk all operations in doIt()
    disableQueue = True  # If true, disable the undo queue in doIt()

    _components = []
    _parentComponents = []

    def resolveArguments(self, arguments):
        selection = list(zapi.selected(filterTypes=zapi.kTransform))
        if not selection:
            self.displayWarning("Must have at least 1 node selected.")
            return
        visited = set()
        parents = []
        for n in selection:
            comp = api.componentFromNode(n)
            if comp is not None and comp not in visited:
                hasGuides = comp.hasGuide()
                if not hasGuides:
                    self.displayWarning("Component missing guides: {}".format(comp))
                    return
                visited.add(comp)
                parents.append([comp.parent(), comp, comp.serializeComponentGuideConnections()])
        if not visited:
            self.displayWarning("No Valid component selection")
            return

        self._components = visited
        arguments["components"] = visited
        self._parentComponents = parents
        return arguments

    def doIt(self, components=None):
        """
        :type components: list[:class:`api.Component`]
        """
        for comp in components:
            comp.removeAllParents()

    def undoIt(self):
        for parent, component, connection in self._parentComponents:
            component.setParent(parent)
            defini = component.definition
            defini.connections = connection
            component.saveDefinition(defini)
            component.deserializeComponentConnections(layerType=constants.GUIDE_LAYER_TYPE)
