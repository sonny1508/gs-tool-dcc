"""Biped Selection Sets Build Script for adding custom selection sets to the rig after Polish.

Handles
- Animator selection sets


------------ BUILD SCRIPT UI DOCUMENTATION ----------------

More Hive Build Script documentation found at:
    https://create3dcharacters.com/zoo-dev-documentation/packages/zoo_hive/buildscripting.html

Common build script code examples:
    https://create3dcharacters.com/zoo-dev-documentation/packages/zoo_hive/buildscripting_examples.html

Author: David Sparrow, Andrew Silke
"""

from zoo.libs.hive import api
from zoo.libs.maya import zapi
from zoo.libs.maya.cmds.sets import selectionsets

FK_COMPONENT_TYPE = "fkchain"
FINGER_COMPONENT_TYPE = "finger"
SEL_SET_SUFFIX = "sSet"
ROOT_SET_NAME = "all_sSet"
BODY_SET_NAME = "body_sSet"


class SelectionSetBipedBuildScript(api.BaseBuildScript):
    """
    """
    # unique identifier for the plugin which will be referenced by the registry.
    id = "selectionSetBipedBuildScript"
    fingerThumbNames = ["finger", "thumb", "index", "middle", "ring", "pinky"]
    iconsDict = {"all": "st_starYellow",
                 "body": "st_starRed",
                 "spine": "st_pentagonAqua",
                 "leg": "st_triangleBlue",
                 "head": "st_circlePink",
                 "god": "st_squarePink",
                 "arm": "st_triangleOrange",
                 "fingersAndThumb": "st_squarePink",
                 "hand": "st_squarePurple",
                 "fingers": "st_squarePink",
                 "toes": "st_squareGreen"}
    defaultIcon = "st_squarePink"

    # todo: check existing joints, delete or keep depending on whether is a reference and the same path.
    @staticmethod
    def properties():
        """Defines the maya reference filePath. For more information about properties see
        :func:`zoo.libs.hive.base.buildscript.BaseBuildScript.properties`

        :rtype: list[dict]
        """
        return [{"name": "metaCarpelExcluded",
                 "displayName": "Rig Has Meta-carpel Finger Joints",
                 "value": False,
                 "type": "boolean",
                 "layout": [0, 0]},
                {"name": "addBody",
                 "displayName": "Add Extra Body Set For Faces",
                 "value": False,
                 "type": "boolean",
                 "layout": [1, 0]}
                ]

    def setMarkingMenu(self, sSet, icon, hidden=False):
        selectionsets.setIcon(sSet, icon)
        if hidden:
            selectionsets.setMarkingMenuVis(sSet, visibility=False)

    def postPolishBuild(self, properties):
        """Executed after the polish stage.
        """
        r = self.rig
        self.armFingerL_R = dict()
        self.extraSets = list()
        excludeMetaC = properties.get("metaCarpelExcluded")
        addBody = properties.get("addBody")
        # first gather all ctrl selectionSets by component, group them by side, fingers/toes/clav are special
        # cases where these can use fingers components for toe or fk component. clav uses fk.
        components = list(r.iterComponents())
        # dict[componentType: {componentSide: [component, component]}]
        componentGroups = {}
        for comp in components:
            componentGroups.setdefault(comp.componentType, {}).setdefault(comp.side(), []).append(comp)
        # root selection set, root has no objects.
        allSSet = zapi.nodeByName(selectionsets.addSelectionSet(ROOT_SET_NAME, []))
        selectionsets.markingMenuSetup(str(allSSet), icon=self.iconsDict["all"], visibility=True)
        bodySetParent = allSSet
        if addBody:
            bodySSet = zapi.nodeByName(selectionsets.addSelectionSet(BODY_SET_NAME, []))
            selectionsets.markingMenuSetup(str(bodySSet), icon=self.iconsDict["body"], visibility=True)
            allSSet.addMember(bodySSet)
            bodySetParent = bodySSet

        selSetMap = {k: v for k, v in self._createSets(components)}
        # now manage anything but fk and fingers generically.
        for k, v in componentGroups.items():
            if k in (FINGER_COMPONENT_TYPE, FK_COMPONENT_TYPE):
                toes, fingers, everythingElse = self._filterToeComponents(v)
                self._solveFingerComponents(fingers, selSetMap, excludeMetaC)
                self._solveToesComponents(toes, selSetMap)
                self._solveClavComponents(everythingElse, selSetMap, componentGroups)

        # parent arms to the parent set ---------------
        if self.armFingerL_R:
            for key in self.armFingerL_R:
                bodySetParent.addMember(self.armFingerL_R[key])

        # Loop over remaining sets and parent the sets ------------
        for sel in selSetMap.values():
            # Parent ------------
            if sel.parent() is None:
                bodySetParent.addMember(sel)  # body set parent can be either "all_sSet" or "body_sSet"

    def _filterToeComponents(self, v):
        """Filters toes and finger components

        :param v:
        :type v:
        :return:
        :rtype:
        """
        toes, fingers, skipped = {}, {}, {}
        for side, comps in v.items():
            for comp in comps:
                name = comp.name().lower()
                if "toe" in name:
                    toes.setdefault(side, []).append(comp)
                elif str(name).split("_")[0] in self.fingerThumbNames:
                    fingers.setdefault(side, []).append(comp)
                else:
                    skipped.setdefault(side, []).append(comp)

        return toes, fingers, skipped

    def _solveToesComponents(self, v, selectionSetsMap):
        """Create and parent the toe sets

        :param v:
        :type v:
        :param selectionSetsMap:
        :type selectionSetsMap:
        :return:
        :rtype:
        """
        for side, components in v.items():
            # ie. armComponent
            rootParent = None
            toesSet = zapi.nodeByName(
                selectionsets.addSelectionSet("_".join(["toes", side, SEL_SET_SUFFIX]), []))
            selectionsets.markingMenuSetup(str(toesSet), icon=self.iconsDict["toes"], visibility=True)
            for component in components:
                if rootParent is None:
                    # just in case the user built with specifying a parent
                    parentComponent = component.parent()
                    if parentComponent is not None:
                        rootParent = selectionSetsMap[parentComponent.serializedTokenKey()]
                compSet = selectionSetsMap[component.serializedTokenKey()]
                # toes marking menu
                selectionsets.markingMenuSetup(str(compSet), icon=self.defaultIcon, visibility=False)
                toesSet.addMember(compSet)

            if rootParent is not None:
                rootParent.addMember(toesSet)

    def _solveFingerComponents(self, v, selectionSetsMap, excludeMetaC):
        """Create and parent the finger and hand sets

        :param v:
        :type v:
        :param selectionSetsMap:
        :type selectionSetsMap:
        :param excludeMetaC:
        :type excludeMetaC:
        """
        for side, components in v.items():  # components are fingers and thumb
            armFingersSet = zapi.nodeByName(selectionsets.addSelectionSet("_".join(["armClavHand",
                                                                                    side, SEL_SET_SUFFIX]), []))
            selectionsets.markingMenuSetup(str(armFingersSet), icon=self.iconsDict["arm"], visibility=True)
            handParent = zapi.nodeByName(selectionsets.addSelectionSet("_".join(["hand", side, SEL_SET_SUFFIX]), []))
            selectionsets.markingMenuSetup(str(handParent), icon=self.iconsDict["hand"], visibility=True)
            fingersSet = zapi.nodeByName(selectionsets.addSelectionSet("_".join(["fingers", side, SEL_SET_SUFFIX]), []))
            selectionsets.markingMenuSetup(str(fingersSet), icon=self.iconsDict["fingers"], visibility=False)
            if excludeMetaC:  # then add the fingersAndThumb_sSet
                thumbFingerSet = zapi.nodeByName(
                    selectionsets.addSelectionSet("_".join(["fingersAndThumb", side, SEL_SET_SUFFIX]), []))
                selectionsets.markingMenuSetup(str(thumbFingerSet),
                                               icon=self.iconsDict["fingersAndThumb"],
                                               visibility=False)
                self.extraSets.append(thumbFingerSet)
                handParent.addMember(thumbFingerSet)
                figerParentSet = thumbFingerSet
            else:  # no need for fingersAndThumb_sSet, don't create it.
                figerParentSet = handParent
            figerParentSet.addMember(fingersSet)
            for component in components:  # iterates over fingers and thumbs
                compName = component.name()
                compSet = selectionSetsMap[component.serializedTokenKey()]
                if "thumb" in compName:
                    figerParentSet.addMember(compSet)
                else:
                    fingersSet.addMember(compSet)
                    # move the fk00(meta) to the thumbFingerSet
                    if excludeMetaC:
                        meta = component.rigLayer().control("fk00")
                        if meta:
                            compSet.removeMember(meta)
                        handParent.addMember(meta)
                # fingers and thumb marking menu
                selectionsets.markingMenuSetup(str(compSet), icon=self.defaultIcon, visibility=False)
            armFingersSet.addMember(handParent)  # add the hand to the armFinger set
            self.armFingerL_R[side] = armFingersSet  # so can be used in other methods.

    def _solveClavComponents(self, v, selectionSetMap, componentGroups):
        """Parent and create the clavicle set. Also parents the arm to the armFingerSet. Assigns Arm icon

        :param v:
        :type v:
        :param selectionSetMap:
        :type selectionSetMap:
        :param componentGroups:
        :type componentGroups:
        """
        # explicitly handle clavicle
        for side, components in v.items():
            armComp = None
            armFingerSet = None
            armComponents = componentGroups.get("armcomponent", {}).get(side)
            if armComponents:
                # build armClavHand set or if exists retrieve
                armFingerSet = zapi.nodeByName(selectionsets.addSelectionSet("_".join(["armClavHand",
                                                                                       side, SEL_SET_SUFFIX]), []))
                armComp = selectionSetMap.get(armComponents[0].serializedTokenKey())
                selectionsets.markingMenuSetup(str(armComp), icon=self.iconsDict["arm"], visibility=False)
                armFingerSet.addMember(armComp)  # parent arm to armFingerSet
            if armComp is None:  # could be center and not left or right
                continue
            for comp in components:
                if "clav" not in comp.name():
                    continue
                compSet = selectionSetMap[comp.serializedTokenKey()]
                selectionsets.markingMenuSetup(str(compSet), icon=self.defaultIcon, visibility=False)
                armFingerSet.addMember(compSet)  # parent clavicle to armFingerSet

    def _createSets(self, components):
        """Creates sets for th given components

        :param components:
        :type components:
        """
        for component in components:
            ctrlSet = component.rigLayer().selectionSet()
            sel = zapi.nodeByName(selectionsets.addSelectionSet("_".join([component.name(), component.side(),
                                                                          SEL_SET_SUFFIX]),
                                                                [ctrlSet.fullPathName()], flattenSets=True))
            type = component.componentType
            if "headcomponent" == type:
                selectionsets.markingMenuSetup(str(sel), icon=self.iconsDict["head"], visibility=False)
            elif "spine" == type or "spineFk" == type or "spineIk" == type:
                selectionsets.markingMenuSetup(str(sel), icon=self.iconsDict["spine"], visibility=True)
            elif "legcomponent" == type:
                selectionsets.markingMenuSetup(str(sel), icon=self.iconsDict["leg"], visibility=True)
            elif "godnodecomponent" == type:
                selectionsets.markingMenuSetup(str(sel), icon=self.iconsDict["god"], visibility=False)
            else:
                selectionsets.setIcon(str(sel), self.defaultIcon)
            yield component.serializedTokenKey(), sel
