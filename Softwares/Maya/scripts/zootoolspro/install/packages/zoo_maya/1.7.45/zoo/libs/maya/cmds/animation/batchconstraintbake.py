"""Batch constraint and bake module.
Can transfer animation from multiple sources to multiple targets.  For example transferring animation
from a skeleton onto a Hive rig.

Note see the batchconstraintconstants.py for the dictionary format.
zoo.libs.maya.cmds.animation.batchconstraintconstants

Example use:

.. code-block:: python

    from zoo.libs.maya.cmds.animation import batchconstraintbake, batchconstraintconstants

    SOURCE_NAMESPACE = ""
    TARGET_NAMEPSACE = "n1"
    SOURCE_PREFIX = ""
    TARGET_PREFIX = ""
    SOURCE_SUFFIX = ""
    TARGET_SUFFIX = ""
    AUTO_LEFT_RIGHT = True
    SOURCE_LEFT_IDENTIFIER = "_l"
    SOURCE_RIGHT_IDENTIFIER = "_r"
    TARGET_LEFT_IDENTIFIER = "_L"
    TARGET_RIGHT_IDENTIFIER = "_R"
    MAINTAIN_OFFSET=True
    BAKE_FREQUENCY=1.0
    INCLUDE_SCALE=False
    TIME_RANGE=None

    UE5_JOINTS =  batchconstraintconstants.UE5_JOINTS
    HIVE_BIPED_STRD_CTRLS = batchconstraintconstants.HIVE_BIPED_STRD_CTRLS

    batchBakeInstance = batchconstraintbake.BatchConstraintAndBake(UE5_JOINTS,
                                                                   HIVE_BIPED_STRD_CTRLS,
                                                                   sourceNamespace=SOURCE_NAMESPACE,
                                                                   targetNamespace=TARGET_NAMEPSACE,
                                                                   sourcePrefix=SOURCE_PREFIX,
                                                                   targetPrefix=TARGET_PREFIX,
                                                                   sourceSuffix=SOURCE_SUFFIX,
                                                                   targetSuffix=TARGET_SUFFIX,
                                                                   autoLeftToRight=AUTO_LEFT_RIGHT,
                                                                   sourceLeftIdentifier=SOURCE_LEFT_IDENTIFIER,
                                                                   sourceRightIdentifier=SOURCE_RIGHT_IDENTIFIER,
                                                                   targetLeftIdentifier=TARGET_LEFT_IDENTIFIER,
                                                                   targetRightIdentifier=TARGET_RIGHT_IDENTIFIER,
                                                                   maintainOffset=MAINTAIN_OFFSET,
                                                                   bakeFrequency=BAKE_FREQUENCY,
                                                                   includeScale=INCLUDE_SCALE,
                                                                   timeRange=TIME_RANGE)
    batchBakeInstance.constrainSourceDictToTarget()
    batchBakeInstance.bakeAnimTargetObjs()
    batchBakeInstance.removeConstraintsTargetObjs()

"""
import re

from maya import cmds
import maya.mel as mel

from zoo.libs.utils import output
from zoo.libs.maya.cmds.animation import bakeanim, timerange, animlayers, generalanimation
from zoo.libs.maya.cmds.objutils import namehandling, attributes


def selection():
    """Selection for UIs, returns a list of selected objects

    :return: selected transform objects
    :rtype: list(str)
    """
    return cmds.ls(selection=True, type="transform")


def selectionPairs():
    """Returns the first half of the objects selected and the second half of the objects selected.

    :return: Two lists, source objects (first half), target objects (second half)
    :rtype: list(str), list(str)
    """
    selObjs = selection()
    if not selObjs:
        return list(), list()
    sourceObjs = selObjs[:len(selObjs) // 2]
    targetObjs = selObjs[len(selObjs) // 2:]
    if not len(sourceObjs) == len(targetObjs):  # take the first target object and append to the source objects
        sourceObjs.append(targetObjs.pop(0))
    return sourceObjs, targetObjs


class BatchConstraintAndBake(object):
    """Transfer animation from a dictionary of source objects to a dictionary of target objects
    For example transferring skeleton animation onto a Hive rig.  Constrains, bakes the animation and remove the constraints.

    Dictionary examples.  Note the constraint type is taken from the target dictionary only:

    .. code-block:: python

        UE5_JOINTS = [{'root': {'node': 'pelvis', 'constraint': 'parent'}},
              {'shoulder_L': {'node': 'upperarm_l', 'constraint': 'orient'}}]

        HIVE_BIPED_STRD_CTRLS = [{'root': {'node': 'spine_M_cog_anim', 'constraint': 'parent'}},
                         {'shoulder_L': {'node': 'arm_L_shldr_fk_anim', 'constraint': 'orient'}}]

    """

    def __init__(self,
                 sourceObjsListDict,
                 targetObjsListDict,
                 checkKeyMatches=False,
                 sourceNamespace="",
                 targetNamespace="",
                 sourcePrefix="",
                 targetPrefix="",
                 sourceSuffix="",
                 targetSuffix="",
                 autoLeftToRight=True,
                 sourceLeftIdentifier="_L",
                 sourceRightIdentifier="_R",
                 sourceLRIsPrefix=False,
                 sourceLRIsSuffix=False,
                 sourceLRSeparatorOnBorder=False,
                 targetLeftIdentifier="_L",
                 targetRightIdentifier="_R",
                 targetLRIsPrefix=False,
                 targetLRIsSuffix=False,
                 targetLRSeparatorOnBorder=False,
                 maintainOffset=True,
                 bakeFrequency=1.0,
                 includeScale=False,
                 timeRange=None):
        """Initialize variables for the class


        :param sourceObjsListDict: The source list of dictionaries
        :type sourceObjsListDict: dict(str)
        :param targetObjsListDict: The target list of dictionaries
        :type targetObjsListDict: dict(str)
        :param checkKeyMatches: If True will check if the keys match in the dictionary lists. If False will not check.
        :type checkKeyMatches: bool
        :param sourceNamespace: The source obj namespace, eg "skeletonReferenceName". Note a semicolon will be added.
        :type sourceNamespace: str
        :param targetNamespace: The target object namespace, eg "hiveReferenceName". Note a semicolon will be added.
        :type targetNamespace: str
        :param sourcePrefix: The source prefix eg "characterName_".  Source sometimes have the char as prefix
        :type sourcePrefix: str
        :param targetPrefix: The target prefix eg "characterName_".  Target sometimes have the char as prefix
        :type targetPrefix: str
        :param sourceSuffix: The source prefix eg "characterName_".  Source sometimes have the char as suffix
        :type sourceSuffix: str
        :param targetSuffix: The target prefix eg "characterName_".  Target sometimes have the char as suffix
        :type targetSuffix: str
        :param sourceLeftIdentifier: The source left side identifier
        :type sourceLeftIdentifier: str
        :param sourceRightIdentifier: The source right side identifier
        :type sourceRightIdentifier: str
        :param sourceLRIsPrefix: The identifier is always at the start of the name.
        :type sourceLRIsPrefix: bool
        :param sourceLRIsSuffix: The identifier is always at the end of the name.
        :type sourceLRIsSuffix: bool
        :param sourceLRSeparatorOnBorder: Underscores are on either side of the identifier eg "L" will be "_L" or "L_"
        :type sourceLRSeparatorOnBorder: bool
        :param targetLeftIdentifier: The target left side identifier
        :type targetLeftIdentifier: str
        :param targetRightIdentifier: The target right side identifier
        :type targetRightIdentifier: str
        :param targetLRIsPrefix: The identifier is always at the start of the name.
        :type targetLRIsPrefix: bool
        :param targetLRIsSuffix: The identifier is always at the end of the name.
        :type targetLRIsSuffix: bool
        :param targetLRSeparatorOnBorder: Underscores are on either side of the identifier eg "L" will be "_L" or "L_"
        :type targetLRSeparatorOnBorder: bool
        :param bakeFrequency: Bake ever n frames
        :type bakeFrequency: float
        :param includeScale: include scale attributes in the bake?
        :type includeScale: bool
        :param timeRange: a start and end frame list [start, end], if None will use the current playback or selected range
        :type timeRange: list(float)
        """
        super(BatchConstraintAndBake, self).__init__()
        self.sourceObjsListDict = sourceObjsListDict
        self.targetObjsListDict = targetObjsListDict
        self.checkKeyMatches = checkKeyMatches
        self.targetNamespace = targetNamespace
        self.sourceNamespace = sourceNamespace
        self.sourcePrefix = sourcePrefix
        self.targetPrefix = targetPrefix
        self.sourceSuffix = sourceSuffix
        self.targetSuffix = targetSuffix
        self.autoLeftToRight = autoLeftToRight
        self.sourceLeftIdentifier = sourceLeftIdentifier
        self.sourceRightIdentifier = sourceRightIdentifier
        self.sourceLRIsPrefix = sourceLRIsPrefix
        self.sourceLRIsSuffix = sourceLRIsSuffix
        self.sourceLRSeparatorOnBorder = sourceLRSeparatorOnBorder
        self.targetLeftIdentifier = targetLeftIdentifier
        self.targetRightIdentifier = targetRightIdentifier
        self.targetLRIsPrefix = targetLRIsPrefix
        self.targetLRIsSuffix = targetLRIsSuffix
        self.targetLRSeparatorOnBorder = targetLRSeparatorOnBorder
        self.maintainOffset = maintainOffset
        self.bakeFrequency = bakeFrequency
        self.includeScale = includeScale
        if not timeRange:
            self.timeRange = timerange.getRangePlayback()
        else:
            self.timeRange = timeRange

    def setTimeRange(self, timeRange):
        """Sets the time range for the bake, if None will use the current playback or selected range.

        :param timeRange: a start/end frame list [start, end], if None will use the current playback or selected range.
        :type timeRange: list(float)
        """
        if not self.timeRange:
            self.timeRange = timerange.getRangePlayback()
        else:
            self.timeRange = timeRange

    def _constrainObj(self, sourceObj, targetObj, constraintType):
        """Constrains one object to another. Can specify the constraint type.

        :param sourceObj: The source object the driver
        :type sourceObj: str
        :param targetObj: The target object the driven
        :type targetObj: str
        :param constraintType: "parent", "orient", "scale" or "point"
        :type constraintType: str
        :return: Success True, failed is False
        :rtype: bool
        """
        try:
            if constraintType == "parent":
                cmds.parentConstraint(sourceObj, targetObj, maintainOffset=self.maintainOffset)
            elif constraintType == "orient":
                cmds.orientConstraint(sourceObj, targetObj, maintainOffset=self.maintainOffset)
            elif constraintType == "scale":
                cmds.scaleConstraint(sourceObj, targetObj, maintainOffset=self.maintainOffset)
            elif constraintType == "point":
                cmds.pointConstraint(sourceObj, targetObj, maintainOffset=self.maintainOffset)
            else:
                output.displayWarning("Constraint type {} not supported".format(constraintType))
        except RuntimeError as e:
            output.displayWarning("Constraint  is already connected. Likely in the list twice. Skipping: {}".format(e))
            return False

        return sourceObj

    def _renameObj(self, name, namespace, prefix, suffix):
        """Renames an object with a namespace, prefix and suffix.  Does not perform a Maya rename.

        Returns the new name.

        :param name: obj string name
        :type name: str
        :param namespace: The obj namespace, eg "characterX". Note a semicolon will be added.
        :type namespace: str
        :param prefix: Adds a prefix to the object name eg "prefix_" for prefix_pCube1
        :type prefix: str
        :param suffix: Adds a suffix to the object name eg "_suffix" for pCube1_suffix
        :type suffix: str
        :return: obj string name now renamed
        :rtype: str
        """
        if not name:
            return ""
        longPrefix, existingNamespace, pureName = namehandling.mayaNamePartTypes(name)  # break apart name "x|x:name"
        if prefix:
            pureName = "".join([prefix, pureName])
        if suffix:
            pureName = "".join([pureName, suffix])
        if namespace:
            if not namespace.endswith(":"):
                pureName = ":".join([namespace, pureName])
            else:
                pureName = "".join([namespace, pureName])
        return namehandling.mayaNamePartsJoin(longPrefix, existingNamespace, pureName)  # rebuild name "x|x:name"

    def _rightSideName(self, name, leftId, rightId, LRIsPrefix, LRIsSuffix, LRSeparatorOnBorder):
        """Finds the right side name of an object, with many options. If it can't be built the name will be empty.

        Name can be long with namespaces. "x|x:name"

        :param name: The name of the left side
        :type name: str
        :param leftId: The left identifier eg "L"
        :type leftId: str
        :param rightId: The left identifier eg "R"
        :type rightId: str
        :param LRIsPrefix: The identifier is always at the start of the name.
        :type LRIsPrefix: bool
        :param LRIsSuffix: The identifier is always at the end of the name.
        :type LRIsSuffix: bool
        :param LRSeparatorOnBorder: Underscores are on either side of the identifier eg "L" will be "_L" or "L_"
        :type LRSeparatorOnBorder: bool
        :return: The name of the right side, if not found returns an empty string
        :rtype: str
        """
        pureNameR = ""
        longPrefix, namespace, pureName = namehandling.mayaNamePartTypes(name)  # break apart name "x|x:name"
        if LRIsPrefix:  # eg "Lname_type"
            if pureName.startswith(leftId):
                pureNameR = re.sub("^{}".format(leftId), rightId, pureName)  # replace at end of name only
        elif LRIsSuffix:  # eg "name_typeL"
            if pureName.endswith(leftId):
                pureNameR = re.sub("{}$".format(leftId), rightId, pureName)  # replace at start of name only
        elif LRSeparatorOnBorder:  # eg "_L" or "L_"
            if "{}_".format(leftId) in pureName:
                pureNameR = pureName.replace("{}_".format(leftId), "{}_".format(rightId))
            elif "_{}".format(leftId) in pureName:
                pureNameR = pureName.replace("_{}".format(leftId), "_{}".format(rightId))
        else:  # Do a straight find and replace
            if leftId in pureName:
                pureNameR = pureName.replace(leftId, rightId)
        if not pureNameR:
            return ""
        return namehandling.mayaNamePartsJoin(longPrefix, namespace, pureNameR)  # rebuild name "x|x:name"

    def _buildObjectLists(self):
        """Returns three lists of source objects, target objects, and constraint types.
        """
        sourceObjs = list()
        targetObjs = list()
        constraintTypes = list()

        for i, tDict in enumerate(self.targetObjsListDict):
            # Sort and check dictionaries, check key IDs match --------------------------
            targetId = list(tDict.keys())[0]  # gets the key inside the dict which is its ID
            targetDict = tDict[targetId]  # # object and constraint type dict
            try:
                sDict = self.sourceObjsListDict[i]
                sourceId = list(sDict.keys())[0]  # gets the key inside the dict which is its ID
                sourceDict = sDict[sourceId]  # object and constraint type dict
            except IndexError:
                output.displayWarning("List entry {}: Target object not found".format(str(i)))
                continue
            if self.checkKeyMatches:  # Then check if the keys match in the lists. If False will not check.
                if not sourceId == targetId:
                    output.displayWarning(
                        "List entry {}: Source ID {} does not match Target ID {}".format(str(i), sourceId, targetId))
                    continue

            # ------------------------------------------
            sourceObj = sourceDict["node"]
            targetObj = targetDict["node"]
            constraintType = targetDict["constraint"]

            # Add name prefix and namespaces -------------------------------------
            sourceObj = self._renameObj(sourceObj,
                                        self.sourceNamespace,
                                        self.sourcePrefix,
                                        self.sourceSuffix)
            targetObj = self._renameObj(targetObj,
                                        self.targetNamespace,
                                        self.targetPrefix,
                                        self.targetSuffix)
            sourceObjs.append(sourceObj)
            targetObjs.append(targetObj)
            constraintTypes.append(constraintType)

            # Right side if passes checks --------------
            if not self.autoLeftToRight:
                continue
            if self.targetLeftIdentifier not in targetObj:
                continue

            rightSource = self._rightSideName(sourceObj,
                                              self.sourceLeftIdentifier,
                                              self.sourceRightIdentifier,
                                              self.sourceLRIsPrefix,
                                              self.sourceLRIsSuffix,
                                              self.sourceLRSeparatorOnBorder)
            rightTarget = self._rightSideName(targetObj,
                                              self.targetLeftIdentifier,
                                              self.targetRightIdentifier,
                                              self.targetLRIsPrefix,
                                              self.targetLRIsSuffix,
                                              self.targetLRSeparatorOnBorder)
            sourceObjs.append(rightSource)
            targetObjs.append(rightTarget)
            constraintTypes.append(constraintType)

        return sourceObjs, targetObjs, constraintTypes

    def printValidateObjects(self):
        """Validates the source and target objects, checks if they exist in the scene.
        """
        sourceObjs, targetObjs, constraintTypes = self._buildObjectLists()
        if not sourceObjs and not targetObjs:
            output.displayWarning("No objects found in the table, please add.")
            return
        output.displayInfo("\n\n\n\n---------------------- START LOG ----------------------")
        for i, sourceObj in enumerate(sourceObjs):
            output.displayInfo("------------------------- ROW {} -------------------------".format(str(i + 1)))
            targetObj = targetObjs[i]
            constraintType = constraintTypes[i]
            sourceErrorTxt = ""
            targetErrorTxt = ""
            sourceHasText = True
            targetHasText = True
            sourceExists = False
            targetExists = False
            sourceUnique = True
            targetUnique = True
            connectedLockedAttrs = []

            if not sourceObj and not targetObj:
                output.displayInfo("!!! SKIPPING !!! SOURCE: Empty \nTARGET: Skipping empty")
                continue
            elif not sourceObj and targetObj:
                output.displayInfo("!!! SKIPPING !!! SOURCE: Empty \n"
                                   "TARGET: {} Skipping nothing to match to".format(targetObj))
                continue
            elif sourceObj and not targetObj:
                output.displayInfo("!!! SKIPPING !!! SOURCE: {} Skipping nothing to match to \n"
                                   "TARGET: Skipping empty".format(sourceObj))
                continue

            if sourceObj:
                if cmds.objExists(sourceObj):
                    sourceExists = True
                    if not namehandling.nameIsUnique(sourceObj):
                        sourceUnique = False
            else:
                sourceHasText = False
                sourceObj = "-- NO NAME SPECIFIED -- "

            if targetObj:
                if cmds.objExists(targetObj):
                    targetExists = True
                    if not namehandling.nameIsUnique(targetObj):
                        targetUnique = False
                    connectedLockedAttrs = self._lockedConnectedAttrs(targetObj, constraintType)
            else:
                targetHasText = False
                targetObj = "-- NO NAME SPECIFIED -- "

            if not sourceExists or not sourceUnique or not sourceHasText:
                sourceErrorTxt = "!!! ERROR !!! "

            if not targetExists or not targetUnique or not targetHasText or connectedLockedAttrs:
                targetErrorTxt = "!!! ERROR !!! "

            # Report ---------------------------

            if sourceErrorTxt:
                output.displayInfo("{}Source: {}      Exists: {}      Unique: {}".format(sourceErrorTxt,
                                                                                         sourceObj,
                                                                                         sourceExists,
                                                                                         sourceUnique))
            else:
                output.displayInfo("Source: {} Tests passed. ".format(sourceObj))
            if targetErrorTxt:
                output.displayInfo(
                    "{}Target: {}      Exists: {}      Unique: {}      "
                    "Connected Locked Atts: {}".format(targetErrorTxt,
                                                       targetObj,
                                                       targetExists,
                                                       targetUnique,
                                                       connectedLockedAttrs))
            else:
                output.displayInfo("Target: {} Tests passed. ".format(targetObj))

        output.displayInfo("---------------------- LOG FINISHED ----------------------")
        output.displayInfo("\nValidation Complete: Please check the script editor for object details. ")
        mel.eval("if (`scriptedPanel - q - exists scriptEditorPanel1`) "
                 "{scriptedPanel -e -tor scriptEditorPanel1; "
                 "showWindow scriptEditorPanel1Window; "
                 "selectCurrentExecuterControl;} "
                 "else {CommandWindow;}")

    def constrainSourceDictToTarget(self, message=True):
        """Constrains one dictionary to another. Can specify the constraint type.

        Can auto add namespaces and prefixes to the names, also apply to right side if left is given.
        """
        success = False
        constrainedObjs = list()

        sourceObjs, targetObjs, constraintTypes = self._buildObjectLists()
        if not sourceObjs:
            output.displayWarning("No Source Objects found in the table.")
            return

        sourceObjs, targetObjs, constraintTypes = self._filterInvalidSourcesTargets(sourceObjs,
                                                                                    targetObjs,
                                                                                    constraintTypes,
                                                                                    message=True)
        if not sourceObjs:
            output.displayWarning("No Source Objects found in the scene")
            return

        # Source and Target objects are now legitimate --------------

        for i, sourceObj in enumerate(sourceObjs):
            targetObj = targetObjs[i]
            constraintType = constraintTypes[i]

            if not sourceObj or not targetObj:
                continue

            # Do the constraint ---------------------------
            constrainedObj = self._constrainObj(sourceObj, targetObj, constraintType)

            if not constrainedObj:  # if obj not found
                continue
            else:
                constrainedObjs.append(constrainedObj)
            success = True

            if self.includeScale:
                cmds.scaleConstraint(sourceObj, targetObj, maintainOffset=self.maintainOffset)

        if message:
            if success:
                output.displayInfo("Success: Constrained objects, see script editor for details.")
            else:
                output.displayWarning("Failed to constrain any objects, see script editor for details.")
        return constrainedObjs

    def matchSourceDictToTarget(self, message=True):
        """Matches one dictionary to another. uses the constraint type to determine what to match.

        parent = pos and rot
        orient = rot
        scale = scale
        point = pos

        Can auto add namespaces and prefixes to the names, also apply to right side if left is given.
        """
        success = False
        matchedObjs = list()

        sourceObjs, targetObjs, constraintTypes = self._buildObjectLists()
        if not sourceObjs:
            output.displayWarning("No Source Objects found in the table.")
            return

        sourceObjs, targetObjs, constraintTypes = self._filterInvalidSourcesTargets(sourceObjs,
                                                                                    targetObjs,
                                                                                    constraintTypes,
                                                                                    message=True)
        if not sourceObjs:
            output.displayWarning("No Source Objects found in the scene")
            return

        for i, sourceObj in enumerate(sourceObjs):
            pos = False
            rot = False
            scl = False

            targetObj = targetObjs[i]
            constraintType = constraintTypes[i]

            if not sourceObj or not targetObj:
                continue

            # Do the match ---------------------------
            if constraintType == "parent":
                pos = True
                rot = True
            elif constraintType == "orient":
                rot = True
            elif constraintType == "scale":
                scl = True
            elif constraintType == "point":
                pos = True
            if self.includeScale:
                scl = True
            cmds.matchTransform(targetObj, sourceObj, pos=pos, rot=rot, scl=scl)
            matchedObjs.append(sourceObj)
            success = True

        if message:
            if success:
                output.displayInfo("Success: Constrained objects, see script editor for details.")
            else:
                output.displayWarning("Failed to constrain any objects, see script editor for details.")
        return matchedObjs

    def _lockedConnectedAttrs(self, obj, constraintType):
        if constraintType == "parent":
            attrs = ["translateX", "translateY", "translateZ", "rotateX", "rotateY", "rotateZ"]
        elif constraintType == "orient":
            attrs = ["rotateX", "rotateY", "rotateZ"]
        elif constraintType == "scale":
            attrs = ["scaleX", "scaleY", "scaleZ"]
        elif constraintType == "point":
            attrs = ["translateX", "translateY", "translateZ"]

        if self.includeScale and "scaleX" not in attrs:
            attrs += ["scaleX", "scaleY", "scaleZ"]

        return attributes.getLockedConnectedAttrs(obj, attrList=attrs, keyframes=False, constraints=False)

    def _objectValid(self, obj, constraintType, connectedAttrs=False, message=True):
        """Checks if an object exists or is valid in the scene

        :param obj: string name of the object
        :type obj: str
        :param constraintType: "parent", "orient", "scale" or "point"
        :type constraintType: str
        :param connectedAttrs: Check if the object has locked or connected attributes
        :type connectedAttrs: bool
        :return: True if the object exists and is unique
        :rtype: bool
        """
        if not obj:
            return False
        if not cmds.objExists(obj):
            if message:
                output.displayWarning("Object {} not found in the scene".format(obj))
            return False
        else:
            if not namehandling.nameIsUnique(obj):
                if message:
                    output.displayWarning("Object {} is not unique in the scene".format(obj))
                return False
        if connectedAttrs:
            lockedAttrs = self._lockedConnectedAttrs(obj, constraintType)
            if lockedAttrs:
                if message:
                    output.displayWarning("Object {} has locked or connected attributes: {}".format(obj, lockedAttrs))
                return False

        return True

    def _filterInvalidSourcesTargets(self, sourceObjs, targetObjs, constraintTypes, connectedAttrs=True, message=True):
        """Returns source and target lists filtered of invalid objects in either list pair.

        :param sourceObjs: A list of source objs
        :type sourceObjs: list(str)
        :param targetObjs: A list of target objs
        :type targetObjs: list(str)
        :param constraintTypes: A list of constraint types
        :type constraintTypes: list(str)
        :param connectedAttrs: Check if the target object has locked or connected attributes
        :type connectedAttrs: bool
        :param message: Report message to the user?
        :type message: bool
        :return: Returns the lists filtered of invalid objects in either the source or target.
        :rtype: tuple(list(str), list(str))
        """
        filteredSources = list()
        filteredTargets = list()
        filteredConstraintTypes = list()

        for i, sourceObj in enumerate(sourceObjs):
            targetObj = targetObjs[i]
            if not sourceObj or not targetObj:
                output.displayWarning("Skipping source `{}` and target `{}` "
                                      "at least one object is empty".format(sourceObj, targetObj))
                continue
            constraintType = constraintTypes[i]

            sourceValid = self._objectValid(sourceObj, constraintType, connectedAttrs=False, message=message)
            targetValid = self._objectValid(targetObj, constraintType, connectedAttrs=connectedAttrs, message=message)

            if sourceValid and targetValid:
                filteredSources.append(sourceObj)
                filteredTargets.append(targetObj)
                filteredConstraintTypes.append(constraintType)
        return filteredSources, filteredTargets, filteredConstraintTypes

    def selectObjs(self, selSourceObjs=False, selTargetObjs=False):
        """Selects the source or target objects.

        :param selSourceObjs: Select the source objects?
        :type selSourceObjs: bool
        :param selTargetObjs: Select the target objects?
        :type selTargetObjs: bool
        """
        sourceObjs, targetObjs, constraintTypes = self._buildObjectLists()
        if not sourceObjs:
            output.displayWarning("No Source Objects found in the table.")
            return
        sourceObjs, targetObjs, constraintTypes = self._filterInvalidSourcesTargets(sourceObjs,
                                                                                    targetObjs,
                                                                                    constraintTypes,
                                                                                    connectedAttrs=False,
                                                                                    message=True)
        if not sourceObjs:
            output.displayWarning("No Valid Source Objects found in the scene. See script editor for details. ")
            return
        if selSourceObjs and selTargetObjs:
            cmds.select(sourceObjs + targetObjs, replace=True)
            output.displayInfo("Selected Source and Target Objects")
        elif selSourceObjs:
            cmds.select(sourceObjs, replace=True)
            output.displayInfo("Selected Source Objects")
        elif selTargetObjs:
            cmds.select(targetObjs, replace=True)
            output.displayInfo("Selected Target Objects")

    def _allTargetObjects(self):
        """Takes the target objects dictionary and returns an object list of names including the right sides.
        Source objects must exist in the current scene.

        :return: A list of all source objects and a list of constraint types
        :rtype: tuple(list(str), list(str))
        """
        existingTargetObjs = list()
        constraintTypeList = list()
        for i, tDict in enumerate(self.targetObjsListDict):
            # Sort and check dictionaries, check key IDs match --------------------------
            targetDict = list(tDict.values())[0]  # # object and constraint type dict
            targetObj = targetDict["node"]
            constraintType = targetDict["constraint"]
            # Rename ----------------
            targetObj = self._renameObj(targetObj, self.targetNamespace, self.targetPrefix, self.targetSuffix)

            if not self._objectValid(targetObj, constraintType, connectedAttrs=True, message=True):
                continue

            existingTargetObjs.append(targetObj)
            constraintTypeList.append(constraintType)

            if not self.autoLeftToRight:
                continue

            # right side ----------------
            rightSourceObj = self._rightSideName(targetObj,
                                              self.targetLeftIdentifier,
                                              self.targetRightIdentifier,
                                              self.targetLRIsPrefix,
                                              self.targetLRIsSuffix,
                                              self.targetLRSeparatorOnBorder)

            if self._objectValid(rightSourceObj, constraintType, connectedAttrs=False, message=True):
                existingTargetObjs.append(rightSourceObj)
                constraintTypeList.append(constraintType)
        if not existingTargetObjs:
            output.displayWarning("No Source Objects found in the scene")
        return existingTargetObjs, constraintTypeList

    def bakeAnimTargetObjs(self, message=True):
        """Bakes the constraints on the target objects.
        Handles the constraint type, checks if objects exist in scene, and adds right side.

        :param message: Report message to the user?
        :type message: bool
        """
        success = False
        parentList = list()
        orientList = list()
        scaleList = list()
        pointList = list()
        allObjsList = [parentList, orientList, scaleList, pointList]
        attrList = [["translate", "rotate"], ["rotate"], ["scale"], ["translate"]]
        existingSourceObjs, constraintTypeList = self._allTargetObjects()
        if not existingSourceObjs:  # error message reported
            if message:
                output.displayWarning("No objects found to bake")
            return False

        for i, constraintType in enumerate(constraintTypeList):
            if constraintType == "parent":
                parentList.append(existingSourceObjs[i])
            elif constraintType == "orient":
                orientList.append(existingSourceObjs[i])
            elif constraintType == "scale":
                scaleList.append(existingSourceObjs[i])
            elif constraintType == "point":
                pointList.append(existingSourceObjs[i])

        if self.includeScale:
            for attrs in attrList:
                if not "scale" in attrs:
                    attrs.append("scale")

        for i, objs in enumerate(allObjsList):
            if not objs:
                continue
            animLayer = animlayers.firstSelectedAnimLayer(
                ignoreBaseLayer=True)  # get the first selected animation layer
            bakeanim.bakeAnimationLayers(objs, attrList[i], self.timeRange, self.bakeFrequency, animLayer,
                                         shapes=True, message=True)
            success = True

        # Euler filter all objects -----------------------
        sel = cmds.ls(selection=True)
        cmds.select(parentList + orientList + scaleList + pointList, replace=True)
        generalanimation.eulerFilter()
        cmds.select(sel, replace=True)

        if message:
            if success:
                output.displayInfo("Success: Baked animation.")
            else:
                output.displayWarning("Failed to bake animation, no objects baked.")
        return success

    def removeConstraintsTargetObjs(self, message=True):
        """Removes all the constraints on the Target Objects, includes the right side controls not in the dictionary.

        :param message: Report message to the user?
        :type message: bool
        """
        existingTargetObjs, constraintTypeList = self._allTargetObjects()
        if not existingTargetObjs:  # error message reported
            if message:
                output.displayWarning("No objects found to remove constraints from.")
            return False
        constrainList = cmds.listRelatives(existingTargetObjs, children=True, type="constraint", allDescendents=False)
        if not constrainList:
            output.displayWarning("No constraints found attached to these objects.")
            return list()
        cmds.delete(list(set(constrainList)))
        if message:
            output.displayInfo("Success: Constraints deleted.")
        return constrainList

    def constrainBakeRemoveConstraints(self, message=True):
        """Constrains the Source Objects to the Target objects bakes the animation and removes the constraints.

        Handles if the objects exist in the scene and adds the right side if identifiers are found.

        :param message: Report message to the user?
        :type message: bool
        """
        success = True
        if not self.constrainSourceDictToTarget():
            success = False
        if success:  # continue
            if not self.bakeAnimTargetObjs():
                success = False
            if success:  # continue
                self.removeConstraintsTargetObjs()
        if message:
            if success:
                output.displayInfo(
                    "Success: Constrained, baked and removed constraints from Hive controls. "
                    "See script editor for details.")
            else:
                output.displayWarning("Failed the constrain process, see the script editor for details.")
