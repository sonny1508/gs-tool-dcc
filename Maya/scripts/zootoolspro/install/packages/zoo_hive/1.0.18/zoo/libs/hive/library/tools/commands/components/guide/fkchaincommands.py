from zoo.libs.maya.mayacommand import command
from zoo.libs.hive import api
from zoo.libs.maya import zapi
from zoo.libs.maya.meta import base


class HiveSetFkParentGuides(command.ZooCommandMaya):
    """Re parents the children guides(first selected) to the parent Guide(last Selected)
    """

    id = "hive.components.guides.setFkGuideParent"
    description = __doc__
    
    isUndoable = True

    _guideMapping = []  # type: list[list[api.Guide, api.Guide, None or api.Annotation, api.HiveGuideLayer]]

    def resolveArguments(self, arguments):
        parentGuide = arguments.get("parentGuide")
        childGuides = arguments.get("childGuides", [])
        if not parentGuide or not childGuides:
            self.displayWarning("Parent or children nodes are not valid")
            return arguments
        if not api.Guide.isGuide(parentGuide):
            self.displayWarning("Parent Node isn't a guide, parent: {}".format(parentGuide))
            return arguments
        # validate requested hierarchy by grab all of the new parent parent nodes all the way to the root
        # if any of the new children exists in the parent hierarchy then skip that child as you can't
        # parent the parent node to its own child as that would crash
        parentTree = [parentGuide] + list(parentGuide.iterParents())
        _guideMapping = []
        for child in childGuides:
            if child in parentTree:
                continue
            childGuide = api.Guide(child.object())
            guideParent, _ = childGuide.guideParent()
            if guideParent == parentGuide:
                continue
            _guideMapping.append([childGuide, guideParent, None, None])
        if not _guideMapping:
            self.displayWarning("No valid Nodes selected for parenting, could be the result of trying to parent "
                                "to it's own child")
            return arguments
        self._guideMapping = _guideMapping
        return arguments

    def doIt(self, parentGuide=None, childGuides=None):
        """
        :param parentGuide: The parent Fk guide for the child to re-parent too.
        :type parentGuide: :class:`api.Guide`
        :param childGuides: The child FK guides to re-parent
        :type childGuides: list[:class:`api.Guide`]
        :return: True if successful
        :rtype: bool
        """

        for index, [guide, currentGuideParent, _, _] in enumerate(self._guideMapping):
            guide.setParent(parentGuide, useSrt=True)
            guideLayers = base.findRelatedMetaNodesByClassType([guide], api.constants.GUIDE_LAYER_TYPE)
            if not guideLayers:
                continue
            annotation = guideLayers[0].annotation(guide, currentGuideParent)
            if not annotation:
                print("No annotation found for guide: {}".format(guide.name()))
                continue
            annDagParent = annotation.parent()
            name = annotation.name()
            annotation.delete()
            newAnnotation = guideLayers[0].createAnnotation(name=name, start=guide,
                                                            end=parentGuide, attrHolder=guide,
                                                            parent=annDagParent)
            self._guideMapping[index][2] = newAnnotation
            self._guideMapping[index][3] = guideLayers[0]

        return True

    def undoIt(self):
        for guide, currentGuideParent, annotation, layer in self._guideMapping:
            guide.setParent(currentGuideParent, useSrt=True)
            if annotation:
                name = annotation.name()
                annParent = annotation.parent()
                annotation.delete()
                layer.createAnnotation(name, start=guide, end=currentGuideParent, attrHolder=guide, parent=annParent)


class HiveCreateFkChainGuides(command.ZooCommandMaya):
    """Creates a new guide for each provided node if that node is linked
    to a FKChain Component.
    """
    id = "hive.components.guides.addFkGuide"
    description = __doc__
    
    isUndoable = True
    _newGuides = []  # type: list[api.Component, list[str]]
    _selection = []  # type: list[zapi.DagNode]

    def resolveArguments(self, arguments):
        components = arguments.get("components")

        if not components:
            self.displayWarning("Must supply at least one selected node")
            return
        self._selection = list(zapi.selected())
        return arguments

    def doIt(self, components=None):
        """
        :param components: A list of components to show guides for
        :type components: dict[:class:`api.Component`, list[:class:`zapi.DagNode`]]
        :return: True if successful
        :rtype: bool
        """
        newGuides = []
        selectables = []
        componentsNeedingBuild = []
        for comp, parentNodes in components.items():
            namer = comp.namingConfiguration()
            guideLayer = comp.guideLayer()  # type: api.HiveGuideLayer
            if not guideLayer:
                continue
            guideLayerDef = comp.definition.guideLayer
            # exclude the root guide and we're zero indexed
            totalGuideCount = guideLayerDef.guideCount(includeRoot=False)
            totalCount = totalGuideCount + len(parentNodes)
            # update the guide settings without forcing the component to build ie. updateGuideSettings will do this.
            guideLayer.guideSettings().jointCount.set(totalCount)
            guideLayerDef.guideSetting("jointCount").value = totalCount
            index = 0
            created = set()
            compName, compSide = comp.name(), comp.side()

            for node in parentNodes:

                if not api.Guide.isGuide(node):
                    continue
                parentGuide = api.Guide(node.object())
                # serialize the guide and remap to the new fk index before we add
                # to the definition
                newGuideDef = parentGuide.serializeFromScene()
                parentId = newGuideDef["id"]
                guidId = "".join(("fk", str(totalGuideCount + index).zfill(2)))
                name = namer.resolve("guideName", {"componentName": compName,
                                                   "side": compSide,
                                                   "id": guidId,
                                                   "type": "guide"})
                newGuideDef["id"] = guidId
                newGuideDef["name"] = name
                newGuideDef["parent"] = parentId
                del newGuideDef["children"]
                for srt in newGuideDef.get("srts", []):
                    srt["name"] = "_".join((guidId, "piv", "srt"))
                guideLayerDef.createGuide(**newGuideDef)
                created.add(guidId)
                index += 1
            newGuides.append([comp, created])
            comp.saveDefinition(comp.definition)
            componentsNeedingBuild.append(comp)

        if componentsNeedingBuild:
            componentsNeedingBuild[0].rig.buildGuides(componentsNeedingBuild)
            for comp, guideIds in newGuides:
                selectables.extend(comp.guideLayer().findGuides(*guideIds))

            zapi.select(selectables)
            self._newGuides = newGuides
            return True
        return False

    def undoIt(self):
        for comp, guideIds in self._newGuides:
            guideLayer = comp.guideLayer()
            jointCountPlug = guideLayer.guideSettings().attribute("jointCount")
            jointCount = jointCountPlug.value()
            jointCountPlug.set(jointCount - len(guideIds))
            guideLayer.deleteGuides(*guideIds)
            comp.definition.guideLayer.deleteGuides(*guideIds)
        zapi.select(self._selection)
