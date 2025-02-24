"""Module for matching Hive guides to rigs or skeletons.

from zoo.libs.hive.library.matching import matchguides
guideNamesDict = matchguides.hiveGuideNames(hiveRig, namespace="", hiveIdDict=mc.HIVE_BIPED_IDS)

from zoo.libs.hive.library.matching import matchconstants as mc
from zoo.libs.hive.library.matching import matchguides
hiveRigName = "biped"
skeletonDict = mc.HIVE_BIPED_SKELETON
matchguides.matchGuidesBipedSkeleton(hiveRigName, skeletonDict, hiveIdDict=mc.HIVE_BIPED_IDS, leftIdentifier="_L",
                                    rightIdentifier="_R", mirrorSuffixPrefix="",
                                    keyOrder=mc.HIERARCHY_ORDER_SPLINESPINE)


"""
from maya import cmds

from zoo.libs.hive.library.matching import matchconstants as mc
from zoo.libs.utils import output
from zoo.libs.hive.base import rig
from zoo.libs.hive import api


def rigInstanceSafe(hiveRigName, namespace=""):
    """Returns the rig instance given and string name and namespace, if it does not exist it returns None

    :param hiveRigName: The string name of a Hive rig ie "zoo_mannequin"
    :type hiveRigName: str
    :param namespace: The namespace of the rig if it exists, otherwise leave blank ""
    :type namespace: str
    :return: A hive rig instance
    :rtype: :class:`api.Rig`
    """
    if not api.rootByRigName(hiveRigName, namespace):  # Doesn't exist
        if namespace:
            output.displayWarning("Rig `{}{}` not found".format(namespace, hiveRigName))
        else:
            output.displayWarning("Rig `{}` not found".format(hiveRigName))
        return None
    rigInstance = rig.Rig()
    if namespace:
        rigInstance.startSession(hiveRigName, namespace=namespace)
    else:
        rigInstance.startSession(hiveRigName, namespace="")
    return rigInstance


def guideStrName(rigInstance, component, id, side):
    """

    :param rigInstance:
    :type rigInstance: :class:`api.Rig`
    :param component:
    :type component: str
    :param id:
    :type id: str
    :param side:
    :type side: str
    :return:
    :rtype:
    """
    compInstance = rigInstance.component(component, side=side)
    if not compInstance:
        output.displayWarning("No component found: {}".format(component))
        return ""
    if not compInstance.hasGuide():
        output.displayWarning("No guides found for component: {}".format(component))
        return ""
    try:
        guideStr = compInstance.guideLayer().guide(id).fullPathName()
    except AttributeError:  # likely another spine type or guide that does not exist.
        return ""
    return guideStr


def hiveGuideNames(hiveRigName, namespace="", hiveIdDict=mc.HIVE_BIPED_IDS):
    """Returns a dict of the hive guide names with each value being a fullpath string name.

    :param hiveRigName:
    :type hiveRigName: str
    :param hiveIdDict: The hive id dictionary each key contains a list of [component, id, side]
    :type hiveIdDict: dict(list)
    :return guideNames: List of guide names now with full path string names of the guides
    :rtype guideNames: dict(str)
    """
    rigInstance = rigInstanceSafe(hiveRigName, namespace=namespace)
    if not rigInstance:  # error message reported
        output.displayWarning("No rig instance found for {}".format(hiveRigName))
        return dict(), rigInstance
    guideNames = {}
    for key, value in hiveIdDict.items():
        component, id, side = value
        guideNames[key] = guideStrName(rigInstance, component, id, side)
    return guideNames, rigInstance


def calculateHeight(bottomJoint, topJoint):
    botSpace = cmds.xform(bottomJoint, query=True, worldSpace=True, translation=True)
    topSpace = cmds.xform(topJoint, query=True, worldSpace=True, translation=True)
    return abs(botSpace[1] - topSpace[1])


def scaleGuides(rootGuide, headGuide, spineRoot, topSpineGuide, headJoint, toeJoint, topSpineJoint, bottomSpineJoint,
                rigInstance):
    # Scale all guides ------------------
    guideHeight = calculateHeight(rootGuide, headGuide)
    currentGuideScale = cmds.getAttr("{}.scaleY".format(rootGuide))
    skeletonHeight = calculateHeight(headJoint, toeJoint)
    scaleSkeleton = skeletonHeight / guideHeight
    newScale = currentGuideScale * scaleSkeleton
    cmds.setAttr("{}.scale".format(rootGuide), newScale, newScale, newScale)

    # Pin guides parented to the spine component ------------------
    rigInstance.component("leg", side="L").pin()
    rigInstance.component("leg", side="R").pin()
    rigInstance.component("clavicle", side="L").pin()
    rigInstance.component("clavicle", side="R").pin()
    rigInstance.component("head", side="M").pin()

    # Scale the spine guides ------------------
    guideSpineHeight = calculateHeight(spineRoot, topSpineGuide)
    spineSkeleHeight = calculateHeight(topSpineJoint, bottomSpineJoint)
    currentSpineGuideScale = cmds.getAttr("{}.scaleY".format(spineRoot))
    scaleSpine = spineSkeleHeight / guideSpineHeight
    newSpineScale = currentSpineGuideScale * scaleSpine
    cmds.setAttr("{}.scale".format(spineRoot), newSpineScale, newSpineScale, newSpineScale)

    # Unpin guides parented to the spine component ------------------
    rigInstance.component("leg", side="L").unPin()
    rigInstance.component("leg", side="R").unPin()
    rigInstance.component("clavicle", side="L").unPin()
    rigInstance.component("clavicle", side="R").unPin()
    rigInstance.component("head", side="M").unPin()

def addNamespace(name, namespace):
    """Adds a namespace to a name, if the name already has a namespace it will add another one

    :param name: The name to add the namespace to
    :type name: str
    :param namespace: The namespace to add
    :type namespace: str
    :return name: The name with the namespace added
    :rtype name: str
    """
    if not namespace:
        return name
    return "{}:{}".format(namespace, name)

def matchGuidesBipedSkeleton(hiveRigName, skeletonDict, skeleNamespace="", skelePrefix="",
                             hiveIdDict=mc.HIVE_BIPED_IDS, leftIdentifier="_L",
                             rightIdentifier="_R", mirrorSuffixPrefix="", keyOrder=mc.HIERARCHY_ORDER_SPLINESPINE):
    """Matches Hive biped guides to a skeleton using hive ids to find guides.

    TODO: Add Hive UE5 ID preset
    TODO Aim the spine bottom at the top spine.
    TODO Snap the controls and foot pivots to the ground.

    :param hiveRigName:
    :type hiveRigName: str
    :param skeletonDict:
    :type skeletonDict:
    :param skeleNamespace: Adds a namespace suffix to the name
    :type skeleNamespace: str
    :param skelePrefix: Adds a prefix to the name
    :type skelePrefix: str
    :param hiveIdDict:
    :type hiveIdDict:
    :param leftIdentifier:
    :type leftIdentifier:
    :param rightIdentifier:
    :type rightIdentifier:
    :param mirrorSuffixPrefix:
    :type mirrorSuffixPrefix:
    :param keyOrder:
    :type keyOrder:
    :return:
    :rtype:
    """
    hiveGuideNameDict, rigInstance = hiveGuideNames(hiveRigName, namespace="", hiveIdDict=mc.HIVE_BIPED_IDS)
    if not hiveGuideNameDict:  # error message reported
        return

    # Size the skeleton and spine guides ----------------------------------------
    rootGuide = hiveGuideNameDict[mc.ROOT_KEY]
    headGuide = hiveGuideNameDict[mc.HEAD_KEY_M]
    spineRoot = guideStrName(rigInstance, "spine", "root", "M")
    topSpineGuide = guideStrName(rigInstance, "spine", "endCurvePiv", "M")

    headJoint = addNamespace(skeletonDict[mc.HEAD_KEY_M], skeleNamespace)
    toeJoint = addNamespace(skeletonDict[mc.TOE_KEY_L], skeleNamespace)
    topSpineJoint = addNamespace(skeletonDict[mc.SPINE05_KEY_M], skeleNamespace)   # TODO: iterate over all spine joints find the last one
    bottomSpineJoint = addNamespace(skeletonDict[mc.SPINE00_KEY_M], skeleNamespace)

    scaleGuides(rootGuide, headGuide, spineRoot, topSpineGuide, headJoint, toeJoint, topSpineJoint, bottomSpineJoint,
                rigInstance)

    # TODO Aim the spine bottom at the top spine.
    # TODO Snap the controls and foot pivots to the ground.

    # Snap match the guides ---------------------------------------------------
    for k in keyOrder:
        if k not in skeletonDict:
            continue
        rotMatch = False
        joint = skeletonDict[k]
        if skeleNamespace:  # to do handle names better support long names etc
            joint = "{}:{}".format(skeleNamespace, joint)
        if k in mc.ROT_ALIGN_GUIDES:  # rot match fingers
            rotMatch = True
        if not joint or not hiveGuideNameDict[k]:
            output.displayWarning("Object not found `{}` or `{}`".format(joint, hiveGuideNameDict[k]))
            output.displayWarning("No guide or skeleton joint found for {}".format(k))
            continue
        if not cmds.objExists(joint):
            output.displayWarning("Joint does not exist: {}".format(joint))
            continue
        cmds.matchTransform(hiveGuideNameDict[k], joint, pos=True, rot=rotMatch, scl=False, piv=False)
        if not hiveIdDict[k][2] == "L":
            continue
        # Build the right joint name according to the mirror rule -------------------
        if not mirrorSuffixPrefix:
            joint = joint.replace(leftIdentifier, rightIdentifier)
        elif mirrorSuffixPrefix == "prefix":
            if joint.endswith(leftIdentifier):
                continue
            if joint.startswith(leftIdentifier):
                continue
        if not cmds.objExists(joint):
            continue
        # get opposite guide ---------------------------------------------------
        component, id, side = hiveIdDict[k]
        rightGuideStr = guideStrName(rigInstance, component, id, "R")
        if not rightGuideStr:
            continue
        cmds.matchTransform(rightGuideStr, joint, pos=True, rot=rotMatch, scl=False, piv=False)
