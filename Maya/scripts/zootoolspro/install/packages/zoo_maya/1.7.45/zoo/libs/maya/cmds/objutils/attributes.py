"""Functions related to Maya's node attributes

Example use:

.. code-block:: python

    from zoo.libs.maya.cmds.objutils import attributes
    attributes.shuffleAttr("eye_cntrl_L", "topLidDwn", up=True, message=True)

    from zoo.libs.maya.cmds.objutils import attributes
    print(attributes.listUserDefinedAttrs("eye_cntrl_L"))

Author: Andrew Silke

"""

import maya.api.OpenMaya as om2
from maya import OpenMaya as om1
import maya.cmds as cmds
import maya.mel as mel

from zoo.libs.maya import zapi
from zoo.libs.utils import output

MAYA_TRANSLATE_ATTRS = ["translateX", "translateY", "translateZ"]
MAYA_ROTATE_ATTRS = ["rotateX", "rotateY", "rotateZ"]
MAYA_SCALE_ATTRS = ["scaleX", "scaleY", "scaleZ"]
MAYA_TRANSFORM_ATTRS = MAYA_TRANSLATE_ATTRS + MAYA_ROTATE_ATTRS + MAYA_SCALE_ATTRS
MAYA_TRANS_ROT_ATTRS = MAYA_TRANSLATE_ATTRS + MAYA_ROTATE_ATTRS

# ------------------
# CREATE ATTRS
# ------------------


def createAttribute(node, attr, attributeType="float", channelBox=True, nonKeyable=False, defaultValue=0,
                    minValue=None, maxValue=None):
    """Creates an attribute for attribute types:

            "float", "int" or "bool"

    Simple one liner that handles non-keyable in the channel box more intuitively. Otherwise can use cmds.addAttr()

    :param node: The object or node to add the new attribute to
    :type node: str
    :param attr: The attribute's name that will be created
    :type attr: str
    :param attributeType: The type of attribute to be created "float", "int", or "bool"
    :type attributeType: str
    :param channelBox: Shows the attribute in the channel box or not
    :type channelBox: bool
    :param nonKeyable: Sets the attribute to be non-keyable in the channel box
    :type nonKeyable: bool
    :param defaultValue: The default value of the attribute
    :type defaultValue: float, bool or int
    :param minValue: The minimum value of the attribute
    :type minValue: float, bool or int
    :param maxValue: The maximum value of the attribute
    :type maxValue: float, bool or int
    """
    cmds.addAttr(node, longName=attr, attributeType=attributeType, defaultValue=defaultValue)
    if minValue is not None and attributeType != "bool":
        cmds.addAttr(".".join([node, attr]), edit=True, minValue=minValue)
    if maxValue is not None and attributeType != "bool":
        cmds.addAttr(".".join([node, attr]), edit=True, maxValue=maxValue)
    # Set channel box and keyable state
    if not channelBox:  # Hiding the attribute so leave keyable as False which is the default
        cmds.setAttr(".".join([node, attr]), channelBox=channelBox)
        return
    cmds.setAttr(".".join([node, attr]), channelBox=True)  # Must be True
    cmds.setAttr(".".join([node, attr]), keyable=not nonKeyable)


# ------------------
# CREATE: ENUM LIST ATTRS
# ------------------


def createEnumAttrList(node, attr, enumNames, channelBox=True, nonKeyable=False, defaultValue=False):
    """Creates a drop down attribute (enum attribute) from a list

    :param node: The object or node to add the new attribute to
    :type node: str
    :param attr: The attribute's name that will be created
    :type attr: str
    :param enumNames: Dropdown list of strings
    :type enumNames: list(str)
    :param nonKeyable: Is the attribute keyable?
    :type nonKeyable: bool
    :param defaultValue: The default value of the enum
    :type defaultValue: int
    :return driverAttr: The driver attribute that was created 'object.attribute'
    :rtype driverAttr: str
    """
    driverAttr = ".".join([node, attr])
    cmds.addAttr(node, longName=attr, attributeType='enum', enumName=":".join(enumNames), defaultValue=defaultValue)
    if not channelBox:  # Hiding the attribute so leave keyable as False which is the default
        cmds.setAttr(driverAttr, channelBox=channelBox)
        return driverAttr
    cmds.setAttr(".".join([node, attr]), channelBox=True)  # Must be True
    cmds.setAttr(".".join([node, attr]), keyable=not nonKeyable)
    return driverAttr


def createConnectAttrs(sourceNode, sourceAttr, createTargetNode, createTargetAttr, defaultValue=0,
                       minValue=None, maxValue=None, attributeType="float", channelBox=True, nonKeyable=False):
    """Creates an attribute on the createTargetNode and connects it

    Supports "float", "int", or "bool"

    :param sourceNode: The name of the source node
    :type sourceNode: str
    :param sourceAttr: The name of the source attribute
    :type sourceAttr: str
    :param createTargetNode: The name of the node that the new attr will be created, must exist already
    :type createTargetNode: str
    :param createTargetAttr: The name of the attribute to be created
    :type createTargetAttr: str
    :param defaultValue: The default value of the attribute
    :type defaultValue: float, bool or int
    :param minValue: The minimum value of the attribute, None will be ignored
    :type minValue: float, bool or int
    :param maxValue: The maximum value of the attribute, None will be ignored
    :type maxValue: float, bool or int
    :param attributeType: The type of attribute to be created "float", "int", or "bool"
    :type attributeType: str
    :param channelBox: Shows the attribute in the channel box or not
    :type channelBox: bool
    :param nonKeyable: Sets the attribute to be non-keyable in the channel box
    :type nonKeyable: bool
    """
    createAttribute(createTargetNode, createTargetAttr, attributeType=attributeType, channelBox=channelBox,
                    nonKeyable=nonKeyable, defaultValue=defaultValue, minValue=minValue, maxValue=maxValue)
    cmds.connectAttr(".".join([createTargetNode, createTargetAttr]), ".".join([sourceNode, sourceAttr]))


# ------------------
# PROXY ATTRS
# ------------------


def proxyAttributes(obj):
    """Returns a list of proxy attribute names from an object or node.

    :param obj: object or node name
    :type obj: str
    :return proxyAttrs: A list of proxy attribute names
    :rtype proxyAttrs: list(str)
    """
    proxyAttrs = []
    selectionList = om1.MSelectionList()
    try:
        selectionList.add(obj)
    except:
        return None
    mobj = om1.MObject()
    selectionList.getDependNode(0, mobj)
    dep = om1.MFnDependencyNode(mobj)
    for i in range(dep.attributeCount()):
        attr = om1.MFnAttribute(dep.attribute(i))
        if attr.isProxyAttribute():
            # we have full access to MFnAttribute here
            # example = attr.getAddAttrCmd(True)
            proxyAttrs.append(attr.name())
    return proxyAttrs


def notProxyAttributes(obj):
    """TODO source from zapi directly"""
    for attr in obj.iterAttributes():  # could be iterExtraAttributes if you only want non default attrs instead
        if attr.isProxy() or attr.isLocked or (attr.isDestination and not attr.isAnimated()):
            continue
        # ignore connected compound i.e translate
        if attr.isChild:
            parent = attr.parent()
            if (parent.isDestination and not parent.isAnimated()):
                continue

        apiPlug = attr.plug()
        if apiPlug.isChannelBox or apiPlug.isKeyable:
            yield attr


def setKeyIgnorePoxyAttrs(zapiNodeList):
    """TODO move into keyframe module"""
    for node in zapiNodeList:
        for objAttr in notProxyAttributes(node):
            objAttrPart = str(objAttr).split(".")
            cmds.setKeyframe(objAttrPart[0], attribute=objAttrPart[1], shape=False)


def setKeyIgnoreProxyAttrsSel():
    """TODO move into keyframe module"""
    selObjs = list(zapi.selected())
    if not selObjs:
        output.displayWarning("Nothing is selected, please select keyable node/s.")
        return
    setKeyIgnorePoxyAttrs(selObjs)


def addProxyAttribute(node, existingNode, existingAttr, proxyAttr="", channelBox=True, nonKeyable=False):
    """Creates a new proxy attribute on the given node.

    If `proxyAttr` is left empty the function will use the `existingAttr` name as the `proxyAttr` name.

    :param node: The maya object/node that the proxy attribute will be created on
    :type node: str
    :param existingNode: The Maya obj that already exists with the attribute to be copied
    :type existingNode: str
    :param existingAttr: The existing attribute to be copied on the existing obj, don't include obj
    :type existingAttr: str
    :param proxyAttr: the name of the proxy attribute, if empty will clone the existingAttr name
    :type proxyAttr: str
    :param channelBox: is the proxy attribute visible in the channelBox?
    :type channelBox: bool
    :param nonKeyable: is the proxy attribute keyable if in the channelBox?
    :type nonKeyable: bool

    :return node: The object name with the new proxy attribute
    :rtype obj: str
    :return proxyAttr: The attribute of the new proxy attribute
    :rtype proxyAttr: str
    """
    if not proxyAttr:
        proxyAttr = existingAttr
    # get attribute type, not sure if this is needed
    attrType = cmds.attributeQuery(existingAttr, node=existingNode, attributeType=True)
    cmds.addAttr(node, longName=proxyAttr, proxy=".".join([existingNode, existingAttr]), keyable=channelBox,
                 attributeType=attrType)

    # If parent attribute then the child attrs won't show in channel box so set all children as keyable
    childAttrs = cmds.attributeQuery(proxyAttr, node=node, listChildren=True)
    if childAttrs:
        for attr in childAttrs:
            cmds.setAttr(".".join([node, attr]), keyable=True)
            # Attribute children have the original name in the child name, so remove it so it's not doubled
            # "xxxvector1Y" becomes 'xxxY' or "vector1vector1Y" becomes "vector1Y"
            newName = attr.replace(existingAttr, "", 1)
            cmds.renameAttr(".".join([node, attr]), newName)

    # Set channel box and non-keyable -------------------------------
    if not channelBox:  # Hiding the attribute so leave keyable as False which is the default
        cmds.setAttr(".".join([node, proxyAttr]), channelBox=channelBox)
        return node, proxyAttr
    cmds.setAttr(".".join([node, proxyAttr]), channelBox=True)  # Must be True
    cmds.setAttr(".".join([node, proxyAttr]), keyable=not nonKeyable)

    return node, proxyAttr


def addProxyAttributeSel(driverNode, driverAttr, drivenNodeText="", drivenAttr="", channelBox=True, nonKeyable=False,
                         message=True):
    nodeAttrTuples = list()
    error = False
    # Error checks ----------------------------------------
    mayaVersion = cmds.about(version=True)
    if float(mayaVersion) < 2017.0:
        if message:
            om2.MGlobal.displayWarning("Proxy attributes do not exist in Maya 2017 and below and cannot be created. ")
        return nodeAttrTuples
    if not driverNode:
        if message:
            om2.MGlobal.displayWarning("No name given for the driver node.  Please type a driver node name.")
        return nodeAttrTuples
    if not driverAttr:
        if message:
            om2.MGlobal.displayWarning("No name given for the driver attribute.  Please type a driver attribute name.")
        return nodeAttrTuples
    if not cmds.objExists(driverNode):
        if message:
            om2.MGlobal.displayWarning("Could not find driver object: The object `{}` "
                                       "does not exist. ".format(driverNode))
        return nodeAttrTuples
    if not cmds.attributeQuery(driverAttr, node=driverNode, exists=True):
        if message:
            om2.MGlobal.displayWarning("Could not find attribute: The attribute `{}` "
                                       "on object `{}` does not exist. ".format(driverAttr, driverNode))
        return nodeAttrTuples
    if not drivenNodeText:
        nodes = cmds.ls(selection=True, long=True)
        if not nodes:
            if message:
                output.displayWarning("Nothing is selected, please select object/s. ")
            return nodeAttrTuples
    else:
        nodes = drivenNodeText.split(",")
        for i, node in enumerate(nodes):
            nodes[i] = node.strip()

    # Try to create proxy attributes ------------------------------------
    checkAttr = str(drivenAttr)
    if not checkAttr:
        checkAttr = driverAttr
    for node in nodes:
        if not cmds.objExists(node):  # check obj exists
            if message:
                output.displayWarning("The object `{}` does not exist".format(node))
            error = True
            continue
        if cmds.attributeQuery(checkAttr, node=node, exists=True):
            if message:  # check attr doesn't already exists
                output.displayWarning("The attribute `{}` already exists on node `{}`".format(checkAttr, node))
            error = True
            continue
        # Create the proxy attribute ------------------------------------------
        nodeAttrTuples.append(addProxyAttribute(node, driverNode, driverAttr, proxyAttr=drivenAttr,
                                                channelBox=channelBox, nonKeyable=nonKeyable))
        if message:
            output.displayInfo("The proxy attribute `{}` was created on node `{}`".format(checkAttr, node))

    # Finished give messages ---------------------------------
    if not message:
        return nodeAttrTuples
    if len(nodes) == 1:
        return nodeAttrTuples  # message already given.
    if error:
        output.displayWarning("Some attributes added with errors see script editor")
        return nodeAttrTuples
    output.displayInfo("Proxy attributes created: `{}`.  See script editor for details. ".format(checkAttr))
    return nodeAttrTuples


def addProxyAttrList(node, existingObj, existingAttrList, channelBox=True, nonKeyable=False):
    """Creates a proxy attributes from a list on the `node` from attributes on `existingObj`

    If `proxyAttr` is empty will use the `existingAttr` name

    :param node: The maya object the proxy attribute will be created on
    :type node: str
    :param existingObj: The Maya obj that already exists with the attribute to be copied
    :type existingObj: str
    :param existingAttrList: The existing attribute to be copied on the existing obj, don't include obj
    :type existingAttrList: list[str]
    :param channelBox: is the proxy attribute visible in the channelBox?
    :type channelBox: bool
    :param nonKeyable: is the proxy attribute keyable if in the channelBox?
    :type nonKeyable: bool
    """
    for i, attr in enumerate(existingAttrList):
        addProxyAttribute(node, existingObj, attr, channelBox=channelBox, nonKeyable=nonKeyable)


def lastNodeAttrFromSel(parent=False, message=True):
    """Returns the last object and its last attribute selected in the channel box.

    :param parent: Returns the attributes parent, eg in case of a vector returns "rotate" and not "rotateY"
    :type parent: bool
    :param message: Report a message to the user?
    :type message: bool

    :return obj: Name of the object or node
    :rtype obj: str
    :return attr: Name of the attribute selected
    :rtype attr: str
    """
    objSel = cmds.ls(selection=True)

    if not objSel:
        if message:
            output.displayWarning("No objects are selected, please select an object and "
                                  "channel box attribute selection.")
        return "", ""
    obj = objSel[-1]  # last selected will always be ok
    attributeNames = getChannelBoxAttrs(message=False)

    if not attributeNames:
        return obj, ""

    attr = attributeNames[0]

    if parent:  # Checks for parent attributes, is important for vectors etc sometimes.
        parentAttrs = returnParentAttrs(obj, [attr])
        if parentAttrs:
            attr = parentAttrs[0]

    return obj, attr


def selObjsCommaSeparated(message=True):
    """Returns the selection as a str comma separated:

        "pCube1, pCube3, pCube2"

    :param message: Report the message to the user
    :type message: bool
    :return objsString: A single string comma separated of the selected object/s names. "pCube1, pCube3, pCube2"
    :rtype objsString: str
    """
    objSel = cmds.ls(selection=True)
    if not objSel:
        if message:
            output.displayWarning("No objects are selected, please select an object and "
                                  "channel box attribute selection.")
        return ""
    return ", ".join(objSel)


# ------------------
# SET DEFAULT ATTRS
# ------------------


def attributeDefault(node, attr, defaultValue, setValue=True):
    """Sets the attribute to a default value and changes the value to match.

    :param node: Maya node string name
    :type node: str
    :param attr: Maya attribute string name
    :type attr: str
    :param defaultValue: The default attribute value to set to ie 1.5
    :type defaultValue: float, int, bool
    """
    cmds.addAttr(".".join([node, attr]), edit=True, defaultValue=defaultValue)  # set default
    if setValue:
        cmds.setAttr(".".join([node, attr]), defaultValue)


# ------------------
# LABEL ATTRS
# ------------------


def nodeShortName(nodeName):
    if "|" in nodeName:
        return nodeName.split("|")[-1]
    else:
        return nodeName


def nodeShortNameList(nodeNameList):
    shortNames = list()
    for node in nodeNameList:
        shortNames.append(nodeShortName(node))
    return shortNames


def labelAttr(labelName, node, checkExists=False):
    """Adds a label attribute with the next attr named "_"  the label name is the enum entry and the attr is locked.

    :param labelName: The name of the first enum of the attribute, the attr name will be named "_", or "__" or "___" etc
    :type labelName: str
    :param node: The node name to add the label attribute, "pCube1"
    :type node: str
    :param checkExists: If true will check to see if the label name already exists before creating.
    :type checkExists: bool
    """
    attrName = "_"
    while cmds.attributeQuery(attrName, node=node, exists=True):
        if checkExists:
            attrType = cmds.getAttr("{}.{}".format(node, attrName), type=True)
            if attrType == "enum":
                if cmds.getAttr("{}.{}".format(node, attrName), asString=True) == labelName:
                    return
        attrName += "_"
    cmds.addAttr(node, longName=attrName, attributeType='enum', enumName=labelName, keyable=True)
    cmds.setAttr("{}.{}".format(node, attrName), lock=True)


def labelAttrSel(labelName, message=True):
    """Adds a label attribute with the next attr named "_"  the label name is the enum entry and the attr is locked.

    :param labelName: The name of the first enum of the attribute, the attr name will be named "_", or "__" or "___" etc
    :type labelName: str
    :param message: Report the message to the user?
    :type message: bool
    """
    if not labelName:
        if message:
            output.displayWarning("No attribute name given. Please enter the name of the label attribute in the UI.")
        return
    selNodes = cmds.ls(selection=True, long=True)
    if not selNodes:
        if message:
            output.displayWarning("Please select objects/nodes to add the attribute.")
        return
    for node in selNodes:
        labelAttr(labelName, node, checkExists=True)


# ------------------
# LIST DICT ATTRS
# ------------------


def getTransRotScaleAttrsAsList(transformNode):
    """Returns the attribute values of MAYATRANSFORMATTRS as a list, each value is a float value.

    ["translateX", "translateY", "translateZ", "rotateX", "rotateY", "rotateZ", "scaleX", "scaleY", "scaleZ"]

    :param transformNode: The transform or joint node name to return
    :type transformNode: str
    :return attrValueList: list with all the float values
    :rtype attrValueList: list(float)
    """
    attrValueList = list()
    for attribute in MAYA_TRANSFORM_ATTRS:
        attrValueList.append(cmds.getAttr(".".join([transformNode, attribute])))
    return attrValueList


def srtAttrsDict(transformNode, rotate=True, translate=True, scale=True):
    """Creates a dictionary with rot translate and scale attributes and their values.

    Useful for copying default SRT values.

    :param transformNode: Maya transform node name
    :type transformNode: str
    :param rotate: Record the rotate values
    :type rotate: bool
    :param translate: Record the rotate values
    :type translate: bool
    :param scale: Record the rotate values
    :type scale: bool
    :return srtAttrDict: A dictionary with rot translate and scale attributes and their values
    :rtype srtAttrDict: dict()
    """
    srtAttrDict = dict()
    if rotate:
        for attr in MAYA_ROTATE_ATTRS:
            srtAttrDict[attr] = cmds.getAttr(".".join([transformNode, attr]))
    if translate:
        for attr in MAYA_TRANSLATE_ATTRS:
            srtAttrDict[attr] = cmds.getAttr(".".join([transformNode, attr]))
    if scale:
        for attr in MAYA_SCALE_ATTRS:
            srtAttrDict[attr] = cmds.getAttr(".".join([transformNode, attr]))
    return srtAttrDict


def setFloatAttrsDict(mayaNode, attrDict):
    """Sets the dictionary with attributes that are floats (or ints?)

    Useful for pasting default SRT values

    :param mayaNode: Maya node name
    :type mayaNode: str
    :param attrDict: A dictionary with any attribute names as keys and floats as values
    :type attrDict: dict()
    """
    for attr in attrDict:
        cmds.setAttr(".".join([mayaNode, attr]), attrDict[attr])


def setTransRotScaleAttrsAsList(transformNode, attrValueList):
    """Given an attribute value list set the rotation, translation, and scale values on a transformNode

    :param transformNode: The name of the Maya transform or joint node
    :type transformNode: str
    :param attrValueList: A list of 9 float values to set for each value in MAYATRANSFORMATTRS
    :type attrValueList: list(float)
    """
    for i, attribute in enumerate(MAYA_TRANSFORM_ATTRS):
        cmds.setAttr(".".join([transformNode, attribute]), attrValueList[i])


# ------------------
# SET ATTR AUTO TYPE
# ------------------


def setAttrAutoType(node, attr, value, message=False, debugMe=False):
    """Sets a Maya attribute with auto type discovery functionality. Supports the most common attr types.

    - float
    - string
    - bool
    - enum
    - float3
    - double3
    - doubleLinear
    - double
    - doubleAngle
    - long

    Ie. Will find the type of the attribute and this function adds the type flag into the cmds.setAttr command

    :param node: The name of the Maya node
    :type node: str
    :param attr: The maya attribute name, attribute only, not the node or object
    :type attr: str
    :param value: The value of the attribute multi-type (can be many types)
    :type value: multipleTypes
    :param message: Report a message for each attribute set, off by default
    :type message: bool
    """
    if debugMe:
        om2.MGlobal.displayInfo("Node `{}`, attr `{}`, value `{}`".format(node, attr, value))
    attrType = cmds.getAttr(".".join([node, attr]), type=True)  # get the attribute type
    if debugMe:
        om2.MGlobal.displayInfo("attrType `{}`".format(attrType))
    # if regular one value
    if (attrType == "doubleLinear") or (attrType == "float") or (attrType == "enum") \
            or (attrType == "long") or (attrType == "double") or (attrType == "bool") \
            or (attrType == "doubleAngle"):
        cmds.setAttr(".".join([node, attr]), value)
        if message:
            om2.MGlobal.displayInfo("Attribute `{}` Set {}".format(".".join([node, attr]), value))
    elif attrType == "double3":  # if type
        cmds.setAttr(".".join([node, attr]), value[0], value[1], value[2], type="double3")
        if message:
            om2.MGlobal.displayInfo("Attribute `{}` Set {}".format(".".join([node, attr]), value))
    elif attrType == "float3":  # if type
        cmds.setAttr(".".join([node, attr]), value[0], value[1], value[2], type="float3")
        if message:
            om2.MGlobal.displayInfo("Attribute `{}` Set {}".format(".".join([node, attr]), value))
    elif attrType == "string":
        cmds.setAttr(".".join([node, attr]), value, type="string")
        if message:
            om2.MGlobal.displayInfo("Attribute `{}` Set {}".format(".".join([node, attr]), value))
    else:
        om2.MGlobal.displayWarning("The type `{}` for the attribute `{}` not "
                                   "found".format(attrType, ".".join([node, attr]), value))


def setAttrributesFromDict(node, attributeDict, message=False):
    """Takes an attribute dictionary and applies it to a node setting all the attributes
    d = {'translateX': (1.2, 'diffuseColor': (.5, .5, .5)}

    :param node: the name of the Maya node
    :type node: str
    :param attributeDict: The dictionary with attribute names as keys and values as values
    :type attributeDict: dict
    :param message: Report a message for each attribute set, off by default
    :type message: bool
    """
    for attr, value in iter(attributeDict.items()):
        if value is None:  # must look for None as some values can be 0
            continue
        setAttrAutoType(node, attr, value, message=message)


# ------------------
# SET CURRENT VALUES AS DEFAULTS
# ------------------


def setAttCurrentDefault(obj, attr, report=True):
    """Sets an attribute's current value to the default value

    :param obj: The objects name
    :type obj: str
    :param attr: the attribute name to set
    :type attr: str
    :param report: report error messages?
    :type report: bool
    :return value: the default value set, or None if none set
    :rtype: float
    """
    try:
        value = cmds.getAttr('.'.join([obj, attr]))
        cmds.addAttr('.'.join([obj, attr]), e=1, dv=value)
        if report:
            om2.MGlobal.displayInfo('Object `{}` Attribute `{}` default set to `{}`'.format(obj, attr, value))
        return value
    except RuntimeError:
        if report:
            om2.MGlobal.displayInfo('Attribute Skipped: {}'.format(attr))
    return None


def setAllAttrsCurrentDefualts(obj, report=True):
    """Sets all the attributes current value of the given object to be the default value
    Will only work on user defined attributes as you're unable to cahnge default attributes

    :param obj: The objects name
    :type obj: str
    :param report: report error messages?
    :type report: bool
    """
    attributeList = cmds.listAttr(obj, visible=True, userDefined=True)
    for attr in attributeList:
        setAttCurrentDefault(obj, attr, report=report)


def setSelCurValuesAsDefaults(report=True):
    """Iterates through the current object selection setting it's current attribute values as the default values
    Will only work on user defined attributes as you're unable to change default attributes

    :param report: report error messages?
    :type report: bool
    """
    objectList = cmds.ls(selection=True)
    for obj in objectList:
        setAllAttrsCurrentDefualts(obj, report=report)


def setAttrsShapeAuto(nodes, attr, value, includeTransforms=True, includeShapes=True, message=True):
    """Sets attributes on many objects with options to include shape nodes.

    If the attribute is not found then the node will be ignored and not set.

    Supports multiple attribute types see docs for setAttrAutoType()

    :param nodes: The maya node names to set
    :type nodes: list(str)
    :param attr: The attribute name to set
    :type attr: str
    :param value: The value of the attribute multi-type (can be many types, str, float, int or list/tuple)
    :type value: multipleTypes
    :param includeTransforms: Try to the selected nodes usually transforms but can be others.
    :type includeTransforms: bool
    :param includeShapes: Also try to set any shape nodes
    :type includeShapes: bool
    :param message: Report a message to the user
    :type message: bool
    """
    success = False
    for node in nodes:
        nodeList = list()
        if includeShapes:
            nodeList = cmds.listRelatives(shapes=True)
            if not nodeList:
                nodeList = list()
        if includeTransforms:  # also can be shaders etc
            nodeList += [node]
        elif not nodeList:  # no shapes found and not transform check so skip.
            continue
        for n in nodeList:
            if cmds.attributeQuery(attr, node=n, exists=True):
                setAttrAutoType(n, attr, value)
                success = True
    if message and success:
        output.displayInfo("Attribute was set `{}`".format(attr))
    elif not success and message:
        output.displayWarning("Attribute was not set/found `{}`".format(attr))
    return success


def setAttrShapeAutoSel(attr, value, includeTransforms=True, includeShapes=True, message=True):
    """Sets attributes on the selected objects with options to include shape nodes and or transforms.

    If the attribute is not found then the node will be ignored and not set.

    Supports multiple attribute types see docs for setAttrAutoType()

    :param attr: The attribute name to set
    :type attr: str
    :param value: The value of the attribute multi-type (can be many types, str, float, int or list/tuple)
    :type value: multipleTypes
    :param includeShapes: Also try to set the
    :type includeShapes: bool
    :param message: Report a message to the user
    :type message: bool
    """
    sel = cmds.ls(selection=True)
    if not sel:
        output.displayWarning("Please select nodes")
        return
    setAttrsShapeAuto(sel, attr, value, includeTransforms=includeTransforms, includeShapes=includeShapes,
                      message=message)


# ------------------
# VISIBILITY CONNNECT ATTRS
# ------------------


def visibilityConnectObjs(visAttr, masterObj, objList, channelBox=True, nonKeyable=True, defaultValue=False):
    """Creates a new attribute that is a visibility switch for multiple objects.

    :param visAttr: The attribute name to create that will toggle visibility
    :type visAttr: str
    :param masterObj: The object/control that will have the attribute
    :type masterObj: str
    :param objList: The objects that will be affected with the visibility switch
    :type objList: list(str)
    :param channelBox: Show in the channelbox
    :type channelBox: bool
    :param nonKeyable: Make non-keyable if in the channelbox
    :type nonKeyable: bool
    :param defaultValue:  The default visibility of the main attribute
    :type defaultValue: bool
    """
    createAttribute(masterObj, visAttr, attributeType="bool", channelBox=channelBox, nonKeyable=nonKeyable,
                    defaultValue=defaultValue)
    for obj in objList:
        cmds.connectAttr("{}.{}".format(masterObj, visAttr), "{}.visibility".format(obj))


# ------------------
# SHOW ATTRS
# ------------------


def showAllAttrChannelBox(obj, translate=True, rotate=True, scale=True, visibility=True, channelBValue=True,
                          keyable=True):
    """Shows Common (rotation, translation, scale and vis) attributes in the channel box

    :param obj: Maya object name to reset
    :type obj: str
    :param rotate: reset rotate
    :type rotate: bool
    :param translate: reset translate
    :type translate: bool
    :param scale: reset scale
    :type scale: bool
    :param visibility: reset visibility
    :type visibility: bool
    :param channelBValue: Display in the channel box, should be True in most cases
    :type channelBValue: bool
    :param keyable: Make the attribute keyable, should be true in most cases
    :type keyable: bool
    """
    if translate:
        cmds.setAttr("{}.translate".format(obj), channelBox=channelBValue)
        cmds.setAttr("{}.translate".format(obj), keyable=keyable)  # must add as channel box makes non keyable
    if rotate:
        cmds.setAttr("{}.rotate".format(obj), channelBox=channelBValue)
        cmds.setAttr("{}.rotate".format(obj), keyable=keyable)
    if scale:
        cmds.setAttr("{}.scale".format(obj), channelBox=channelBValue)
        cmds.setAttr("{}.scale".format(obj), keyable=keyable)
    if visibility:
        cmds.setAttr("{}.visibility".format(obj), channelBox=channelBValue)
        cmds.setAttr("{}.visibility".format(obj), keyable=keyable)


# ------------------
# ZERO AND RESET ATTRS
# ------------------


def checkAllAttrsZeroed(transformNode):
    """Checks to see if all the current pos values are zeroed, a useful check before freezing transforms.  Uses a \
     tolerance in case of micro values which is often on Maya objects.

    Checks these values are zeroed:

        ["translateX", "translateY", "translateZ", "rotateX", "rotateY", "rotateZ"]

    Checks these values are 1.0:

        ["scaleX", "scaleY", "scaleZ"]

    :param transformNode: The name of the Maya transform or joint node
    :type transformNode: str
    :return isZero: True if zeroed, False if not
    :rtype isZero: bool
    """
    attrValList = getTransRotScaleAttrsAsList(transformNode)
    for val in attrValList[:-3]:
        if val > 0.0001 or val < -0.0001:
            return False
    for val in attrValList[6:]:
        if val > 1.0001 or val < -0.9999:
            return False
    return True


def checkAllAttrsZeroedList(transformNodeList):
    """Checks to see if all the current pos values are zeroed on an object list, a useful check before freezing \
    transforms.  Uses a tolerance in case of micro values which is often on Maya objects.

    Returns a list of True False values.

    Checks these values are zeroed:

        ["translateX", "translateY", "translateZ", "rotateX", "rotateY", "rotateZ"]

    Checks these values are 1.0:

        ["scaleX", "scaleY", "scaleZ"]

    :param transformNodeList: A list of Maya transform or joint node names
    :type transformNodeList: list(str)
    :return isZeroList: A list of True or False values, True if the object is zeroed, False if not
    :rtype isZeroList: list(bool)
    """
    for transform in transformNodeList:
        if not checkAllAttrsZeroed(transform):
            return False
    return True


def resetTransformAttributes(obj, rotate=True, translate=True, scale=True, visibility=False):
    """Resets the transforms (and potentially visibility) of a Maya object.

    :param obj: Maya object name to reset
    :type obj: str
    :param rotate: reset rotate
    :type rotate: bool
    :param translate: reset translate
    :type translate: bool
    :param scale: reset scale
    :type scale: bool
    :param visibility: reset visibility
    :type visibility: bool
    """
    if translate:
        cmds.setAttr("{}.translate".format(obj), 0.0, 0.0, 0.0)
    if rotate:
        cmds.setAttr("{}.rotate".format(obj), 0.0, 0.0, 0.0)
    if scale:
        cmds.setAttr("{}.scale".format(obj), 1.0, 1.0, 1.0)
    if visibility:
        cmds.setAttr("{}.visibility".format(obj), 1.0)


def srtIsZeroed(obj):
    """Returns True if the translate and rotate attributes and zeroes and the scale values are set to 1.0

    :param obj: A maya transform name
    :type obj: str
    :return zeroed:  True if the translate and rotate attributes and zeroes and the scale values are set to 1.0
    :rtype zeroed: bool
    """
    zeroed = True
    if cmds.getAttr("{}.translate".format(obj))[0] != (0.0, 0.0, 0.0):
        zeroed = False
    if cmds.getAttr("{}.rotate".format(obj))[0] != (0.0, 0.0, 0.0):
        zeroed = False
    if cmds.getAttr("{}.scale".format(obj))[0] != (1.0, 1.0, 1.0):
        zeroed = False
    return zeroed


# ------------------
# COLOR ATTRS
# ------------------


def createColorAttribute(node, attrName="color", keyable=True):
    """Creates a color attribute in maya on the node, attrName can be changed from color

    :param node: any maya node
    :type node: str
    :param attrName: the name of the attribute, subattributes will be nameR, nameG nameB
    :type attrName: str
    :param keyable: Add attribute into the channel box and make it keyable?
    :type keyable: bool
    :return:
    :rtype:
    """
    cmds.addAttr(node, longName=attrName, usedAsColor=True, attributeType='float3', keyable=keyable)
    cmds.addAttr(node, longName='{}R'.format(attrName), attributeType='float', parent=attrName, keyable=keyable)
    cmds.addAttr(node, longName='{}G'.format(attrName), attributeType='float', parent=attrName, keyable=keyable)
    cmds.addAttr(node, longName='{}B'.format(attrName), attributeType='float', parent=attrName, keyable=keyable)


# ------------------
# DELETE ATTRS
# ------------------


def deleteNodesWithAttributeList(nodeList, attributeName):
    """deletes nodes that have an attribute with attributeName

    :param nodeList: a list of maya nodes
    :type nodeList: list
    :param attributeName: the name of the attribute without the node
    :type attributeName: str
    :return deletedNodes: list of the nodes that have been deleted
    :rtype deletedNodes: list
    """
    deletedNodes = list()
    for node in nodeList:
        if cmds.attributeQuery(attributeName, node=node, exists=True):
            cmds.delete(node)
            deletedNodes.append(node)
    return deletedNodes


def checkRemoveAttr(node, attrName):
    """Checks if the attribute exists and if it does remove/delete the attribute, deletes the parent if a vector etc

    Also unlocks and disconnects before deleting.

    :param node: A maya node name
    :type node: str
    :param attrName: the attribute to remove name
    :type attrName: str
    :return deleted:  True if deleted False if not
    :rtype deleted: bool
    """
    if cmds.attributeQuery(attrName, n=node, exists=True):
        parentAttrs = cmds.attributeQuery(attrName, node=node, listParent=True)
        if parentAttrs:
            attrName = parentAttrs[0]
            # Unlock child attributes
            childAttrs = cmds.attributeQuery(attrName, node=node, listChildren=True)
            if childAttrs:  # unlock all
                unlockDisconnectAttrs(node, childAttrs)
        else:  # unlock
            unlockDisconnectAttrs(node, [attrName])

        cmds.deleteAttr(".".join([node, attrName]))
        return True
    return False


def deleteAttributeSel(message=True):
    """Deletes selected attributes from the channel box selection.  Can delete multiple on multiple objects.

    :param message: Report a message to the user?
    :type message: bool

    :return deletedAttrs: list of strings, "node.attribute" example if successfully deleted.
    :rtype deletedAttrs: str
    """
    deletedAttrs = list()
    deletedAttrsShort = list()
    selObjs = cmds.ls(selection=True, long=True)
    if not selObjs:
        if message:
            output.displayWarning("Nothing is selected, please select object/s. ")
        return deletedAttrs
    attrList = getChannelBoxAttrs()
    if not attrList:
        if message:
            output.displayWarning("No attributes are selected in the Channel Box, please select attribute/s. ")
        return deletedAttrs
    # Find only parent attributes for deletion

    # Delete the attributes if found
    for obj in selObjs:
        for attr in attrList:
            if checkRemoveAttr(obj, attr):
                deletedAttrs.append(".".join([obj, attr]))
                if message:
                    deletedAttrsShort.append(".".join([nodeShortName(obj), attr]))
    if message:
        output.displayInfo("Success: Attributes deleted `{}`".format(deletedAttrsShort))
    return deletedAttrs


# ------------------
# LOCKED/CONNECTED/ANIMATED ATTRS
# ------------------


def removeKeysAttr(node, attr, timeRange=(-10000, 100000)):
    """Deletes all the keys on an attribute within the range

    :param node: A maya node name
    :type node: str
    :param attr: a maya attribute name
    :type attr: str
    :param timeRange: Delete all keys within this time range. Eg (-10000, 100000)
    :type timeRange: tuple
    """
    if cmds.keyframe(node, attribute=attr, selected=False, q=True):
        cmds.cutKey(node, time=timeRange, attribute=attr)


def lockAttr(node, attr, lock=True):
    """Simple function that locks/unlocks an attribute

    :param node: A maya node name
    :type node: str
    :param attr: a maya attribute name
    :type attr: str
    :param lock: Lock or unlock?
    :type lock: bool
    """
    cmds.setAttr("{}.{}".format(node, attr), lock=lock)


def hideAttr(node, attr, hide=True, keyable=True):
    """

    :param node: A maya object or node name
    :type node: str
    :param attr: The attribute to hide or show
    :type attr: str
    :param hide: If True hides the attribute from the channel box.
    :type hide: bool
    :param keyable: Only if showing the attribute, set the keyable to False as an option
    :type keyable: bool
    :return:
    :rtype:
    """
    if hide:
        cmds.setAttr("{}.{}".format(node, attr), keyable=False, channelBox=False)
    else:
        cmds.setAttr("{}.{}".format(node, attr), keyable=keyable)
        cmds.setAttr("{}.{}".format(node, attr), channelBox=True)


def hideAttrs(node, attrs, hide=True, keyable=True):
    """

    :param node: A maya object or node name
    :type node: str
    :param attrs: The attributes to hide or show
    :type attrs: list(str)
    :param hide: If True hides the attribute from the channel box.
    :type hide: bool
    :param keyable: Only if showing the attribute, set the keyable to False as an option
    :type keyable: bool
    """
    for attr in attrs:
        hideAttr(node, attr, hide=hide, keyable=keyable)


def lockHideAttr(node, attr, lockHide=True, keyable=True):
    """Locks and hides an attribute.

    If lockHide=False then show and unlock the attribute

    :param node: A maya object or node name
    :type node: str
    :param attr: The attribute to lock and hide
    :type attr: str
    :param lockHide: If True will lock and hide, if False then shows and unlocks
    :type lockHide: bool
    :param keyable: Only if showing the attribute, set the keyable to False as an option
    :type keyable: bool
    """
    childAttrs = cmds.attributeQuery(attr, node=node, listChildren=True)
    if childAttrs:
        attrs = childAttrs
    else:
        attrs = [attr]

    for attr in attrs:
        cmds.setAttr("{}.{}".format(node, attr), lock=lockHide)
        hideAttr(node, attr, hide=lockHide, keyable=keyable)


def disconnectAttr(node, attr):
    """Disconnects using only one attribute, as per right click disconnect in the channel box.

    :param node: A maya node name
    :type node: str
    :param attr: a maya attribute name
    :type attr: str
    :return success: True if an attribute was disconnected
    :rtype success: bool
    """
    objectAttribute = "{}.{}".format(node, attr)
    # get the connection of that attribute
    oppositeAttrs = cmds.listConnections(objectAttribute, plugs=True)
    if not oppositeAttrs:
        return False
    try:
        cmds.disconnectAttr(oppositeAttrs[0], objectAttribute)
        return True
    except RuntimeError:
        pass
    return False


def unlockDisconnectAttrs(node, attrList):
    """Unlocks/deletes keys/disconnects all attributes in a list on a single node

    :param node: A maya node name
    :type node: str
    :param attrList: A list of Maya attribute names
    :type attrList: list(str)
    """
    for attr in attrList:
        cmds.setAttr("{}.{}".format(node, attr), lock=False)  # Unlock
        removeKeysAttr(node, attr)
        disconnectAttr(node, attr)


def unlockDisconnectSRT(node):
    """Unlocks/deletes keys/disconnects translate, rotate and scale

    :param node: A maya node name
    :type node: str
    """
    unlockDisconnectAttrs(node, MAYA_TRANSFORM_ATTRS)


def unlockSRTV(obj, translate=True, rotate=True, scale=True, visibility=True, lock=False, keyable=True):
    """Unlocks All Common (rotation, translation, scale and vis) Attributes

    :param obj: The name of the object
    :type obj: str
    :param translate: Do you want to affect translate?
    :type translate: bool
    :param rotate: Do you want to affect rotate?
    :type rotate: bool
    :param scale: Do you want to affect scale?
    :type scale: bool
    :param visibility: Do you want to affect visibility?
    :type visibility: bool
    :param lock: this state will either lock or unlock, True will lock all attributes
    :type lock: bool
    """
    if translate:  # must unlock on the individual attr translateX and not translate for some reason
        for transAttr in MAYA_TRANSLATE_ATTRS:
            cmds.setAttr("{}.{}".format(obj, transAttr), lock=lock, keyable=keyable)
    if rotate:
        for transAttr in MAYA_ROTATE_ATTRS:
            cmds.setAttr("{}.{}".format(obj, transAttr), lock=lock, keyable=keyable)
    if scale:
        for transAttr in MAYA_SCALE_ATTRS:
            cmds.setAttr("{}.{}".format(obj, transAttr), lock=lock, keyable=keyable)
    if visibility:
        cmds.setAttr("{}.visibility".format(obj), lock=lock, keyable=keyable)


def isSettable(obj, attr):
    return cmds.getAttr(".".join([obj, attr]), settable=True)


def getLockedConnectedAttrs(obj, attrList=None, keyframes=False, constraints=False):
    """Gets all the locked or connected attributes from either:

        1. attrList=None: all keyable attributes on an object
        2. attrList=list(attrs): the given attributes

    Returns connected or locked attributes as a list, empty list if none found

    :param obj: the maya objects name
    :type obj: str
    :param attrList: list of attributes to check
    :type attrList: list(str)
    :param keyframes: If True also check for keyframes
    :type keyframes: bool

    :return: locked or connected attributes
    :rtype: list
    """
    lockedConnectedAttrs = list()
    if attrList:  # Check only the given attributes
        for attr in attrList:
            if not cmds.getAttr(".".join([obj, attr]), settable=True):
                lockedConnectedAttrs.append(".".join([obj, attr]))
            if keyframes and cmds.keyframe(obj, attribute=attr, selected=False, q=True):
                lockedConnectedAttrs.append(".".join([obj, attr]))
    else:  # Check all channel box (keyable) attrs
        for attr in cmds.listAttr(obj, keyable=True):
            if not cmds.getAttr(".".join([obj, attr]), settable=True):
                lockedConnectedAttrs.append(".".join([obj, attr]))
    if constraints:
        for attr in attrList:
            if cmds.listConnections(".".join([obj, attr]), type="constraint"):
                lockedConnectedAttrs.append(".".join([obj, attr]))

    return lockedConnectedAttrs


def getLockedConnectedAttrsList(nodeList, attrList=None, keyframes=False, constraints=False):
    """Gets all the locked or connected attributes from a node list.

    Attributes can be either:

        1. attrList=None: all keyable attributes on an object
        2. attrList=list(attrs): the given attributes

    Returns two lists:
        lockedNodes: A list of nodes with locked or connected attributes
        lockedAttrList: Records the attrs locked/connected.  Is a list(list) of attributes matching the lockedNodes

    :param nodeList: A list of Maya nodes
    :type nodeList: list(str)
    :param attrList: A list of attributes to check, if empty or None will check all keyable attributes
    :type attrList: list(str)
    :param keyframes: If True also check for keyframes
    :type keyframes: bool
    :param constraints: If True also check for constraints
    :type constraints: bool

    :return lockedNodes: A list of nodes with locked or connected attributes, is empty if no locked or connected attrs
    :rtype lockedNodes: list(str)
    :return lockedNodes: Records the attrs locked/connected.  Is a list(list) of attributes matching the lockedNodes
    :rtype lockedNodes: list(list(str))
    """
    lockedNodes = list()
    lockedAttrList = list()
    for node in nodeList:
        lockedConnectedAttrs = getLockedConnectedAttrs(node, attrList=attrList, keyframes=keyframes,
                                                       constraints=constraints)
        if lockedConnectedAttrs:
            lockedNodes.append(node)
            lockedAttrList += lockedConnectedAttrs

    return lockedNodes, lockedAttrList


# ---------------------------
# SCALE ATTRIBUTES
# ---------------------------


def disableNonUniformScale(obj):
    """Links the scaleX to the other two scales, so the object can't be non-uniformly scaled.

    :param obj: The transform node to disable non-uniform scale
    :type obj: str
    """
    cmds.connectAttr("{}.scaleX".format(obj), "{}.scaleY".format(obj))
    cmds.connectAttr("{}.scaleX".format(obj), "{}.scaleZ".format(obj))
    cmds.setAttr("{}.scaleY".format(obj), lock=True)
    cmds.setAttr("{}.scaleZ".format(obj), lock=True)


# ---------------------------
# LIST ANIMATABLE ATTRIBUTES
# ---------------------------


def animatableAttrs(obj):
    """Returns a list of all the animatable attribute names on a node (channel box animatable, not locked etc.

    :param obj: Name of the object or node
    :type obj: str
    :return attrs: List of attribute names eg [u'visibility', u'translateX', u'translateY', u'translateZ', u'rotateX']
    :rtype attrs: list(str)
    """
    attrs = []
    allAttrs = cmds.listAttr(obj)
    cbAttrs = cmds.listAnimatable(obj)
    if allAttrs and cbAttrs:
        orderedAttrs = [attr for attr in allAttrs for cb in cbAttrs if cb.endswith(attr)]
        attrs.extend(orderedAttrs)
    return attrs


# ---------------------------
# LIST CONNECTABLE ATTRIBUTES
# ---------------------------


def listConnectableAttrs(obj):
    """List all the connectable attributes of a Maya node

    :param obj: A Maya object or node name
    :type obj: str
    :return attributeList: list of potentially connectable attributes on the node
    :rtype attributeList: list(str)
    """
    return cmds.listAttr(obj, connectable=True)


def listConnectableAttrsSel(selectionIndex=0, message=True):
    """From the selection list all the connectable attributes

    :param selectionIndex: Only takes one object from the selection, this is the index number of the selection
    :type selectionIndex: int
    :param message: Report the message to the user
    :type message: bool
    :return attributeList: list of potentially connectable attributes on the node
    :rtype attributeList: list(str)
    """
    selObjs = cmds.ls(selection=True, long=True)
    # Filter only transforms since dealing with rot trans and scale
    if not selObjs:
        if message:
            om2.MGlobal.displayWarning("No objects selected, please select an object or node")
        return list()
    if len(selObjs) < (selectionIndex + 1):
        return list()
    return listConnectableAttrs(selObjs[selectionIndex])


# ---------------------------
# GET CHANNEL BOX ATTRS
# ---------------------------

def removeUnsettableAttrs(obj, attrs):
    """Removes attributes that cannot be set.

    :param obj: Object or node name
    :type obj: str
    :param attrs: list of attribute names
    :type attrs: list(str)
    :return filteredAttrs: The attribute list now with unsettable attributes removed.
    :rtype filteredAttrs:
    """
    removeAttrs = list()
    for attr in attrs:
        if not cmds.getAttr(".".join([obj, attr]), settable=True):
            removeAttrs.append(attr)
    filteredAttrs = [x for x in attrs if x not in removeAttrs]
    return filteredAttrs


def channelBoxAttrs(obj, settableOnly=True, includeProxyAttrs=True):
    """helper function to retrieve all the attributes listed in the channelbox as cmds does not support.

    Extra support for returning only settable attrs and for including proxy attributes too.

    :param obj: Object or node name
    :type obj: str
    :param settableOnly: Returns only settable attributes and removes unsettable.
    :type settableOnly: bool
    :param includeProxyAttrs: Includes proxy attributes that may exist on other node/objects
    :type includeProxyAttrs: bool
    :return attrs: A list of attribute names in the channel box.
    :rtype attrs: list(str)
    """
    proxyCBAttrs = list()
    attrs = list()
    # get most common channel box attributes ---------
    keyableAttrs = cmds.listAttr(obj, keyable=True)
    if keyableAttrs:
        attrs += keyableAttrs
    channelboxAttrs = cmds.listAttr(obj, channelBox=True)
    if channelboxAttrs:
        attrs += channelboxAttrs
    # proxyAttrs are not found with channelboxAttrs ----------
    allProxyAttrs = proxyAttributes(obj)
    if allProxyAttrs:
        if includeProxyAttrs:
            for proxyAttr in allProxyAttrs:
                if cmds.getAttr(".".join([obj, proxyAttr]), channelBox=True):
                    proxyCBAttrs.append(proxyAttr)
            attrs = list(set(attrs + proxyCBAttrs))  # add proxies with attrs
        else:  # remove any proxy attrs from list
            attrs = [x for x in attrs if x not in allProxyAttrs]

    # filter settable attrs if kwarg ---------
    if settableOnly:
        attrs = removeUnsettableAttrs(obj, attrs)
    return attrs


def getChannelBoxAttrs(message=False):
    """Selected Chnnel box attributes. Returns the long name of the selected attribute from the channel box

    Annoying function as it's not easy to retrieve the long name. Mel has a one liner for short names.

    selAttrs = mel.eval('selectedChannelBoxAttributes')

    :param message: Report the message to the user
    :type message: bool
    :return attrNames: list of long attribute names eg ["translateX", "rotateX"]
    :rtype attrNames: list(str)
    """
    mainObjs = cmds.channelBox("mainChannelBox", query=True, mainObjectList=True)
    mainAttrs = cmds.channelBox("mainChannelBox", query=True, selectedMainAttributes=True)
    histObjs = cmds.channelBox("mainChannelBox", query=True, historyObjectList=True)
    histAttrs = cmds.channelBox("mainChannelBox", query=True, selectedHistoryAttributes=True)
    shapeObjs = cmds.channelBox("mainChannelBox", query=True, shapeObjectList=True)
    shapeAttrs = cmds.channelBox("mainChannelBox", query=True, selectedShapeAttributes=True)
    # now combine and get the long names
    attrNames = []
    for pair in ((mainObjs, mainAttrs), (histObjs, histAttrs), (shapeObjs, shapeAttrs)):
        objs, attrs = pair
        if attrs is not None:
            for nodeName in objs:
                # Get the long name not the short name ----------------------
                resultList = list()
                for attr in attrs:
                    try:
                        longName = cmds.attributeQuery(attr, node=nodeName, longName=True)
                        resultList.append(longName)
                    except RuntimeError:  # multiple selected objects the attr may not exist.
                        pass
                attrNames += resultList
    attrNames = list(set(attrNames))  # Remove duplicates
    if not attrNames and message:
        om2.MGlobal.displayWarning("Please select attributes in the channel box")
    return attrNames


# ---------------------------
#  MOVE ATTRS
# ---------------------------


def moveAttrBottomList(attrList, obj, indx):
    """Drops a single attribute to the bottom of the channel box. The list is updated as it's been shuffled.

    Note: Uses the Maya hack and is not undoable:

        cmds.deleteAttr(attribute=attrList[indx], name=obj)
        cmds.undo()

    :param attrList:  A list of attributes in order as per the channel box
    :type attrList: list(str)
    :param obj: The object with the attribute list
    :type obj: str
    :param indx: The index of the attribute to drop
    :type indx: int
    :return attrList:
    :rtype attrList: list(str)
    """
    attrList = list(attrList)
    attr = attrList[indx]
    # get locked state of the attribute
    locked = cmds.getAttr(".".join([obj, attr]), lock=True)
    if locked:  # Unlock
        cmds.setAttr(".".join([obj, attr]), lock=False)
    # Do the delete ------------------------------------
    cmds.undoInfo(openChunk=True)
    checkRemoveAttr(obj, attr)
    cmds.undoInfo(closeChunk=True)
    cmds.undo()
    if locked:  # Lock
        cmds.setAttr(".".join([obj, attr]), lock=True)
    droppedAttr = attrList.pop(indx)
    attrList.append(droppedAttr)
    return attrList


def returnParentAttrs(obj, attrs, channelBoxOnly=True):
    """Filters out child attrs eg rotateX and returns only the parent

    :param obj: The object with the attribute
    :type obj: str
    :param attrs: a list of attribute names
    :type attrs: list(str)
    :param channelBoxOnly: If True will only return attrs seen in the channel box
    :type channelBoxOnly: bool

    :return parentAttrs: A list of attrs only parents, no child attributes
    :rtype parentAttrs: list(str)
    """
    parentAttrs = list(attrs)
    # Check if a child attrs and set as the parent attr instead, causes duplicate entries --------------------
    for i, attr in enumerate(parentAttrs):
        parent = cmds.attributeQuery(attr, node=obj, listParent=True)
        if parent:
            parentAttrs[i] = parent[0]
        if channelBoxOnly:  # Check is displayed keyable or channel box
            if not (cmds.getAttr(".".join([obj, attr]), k=True) or cmds.getAttr(".".join([obj, attr]), cb=True)):
                parentAttrs[i] = None

    # Remove list duplicates but keep list order -----------------------
    seen = set()
    seen_add = seen.add
    parentAttrs = [x for x in parentAttrs if not (x in seen or seen_add(x))]

    if channelBoxOnly:  # Remove None entries --------------------
        parentAttrs = list(filter(None, parentAttrs))

    return parentAttrs


def listUserDefinedAttrs(obj, channelBoxOnly=True):
    """Returns the user defined attributes and only includes parent attributes.

    Eg a vector of attributes becomes a single attr

        blinkX, blinkY, blinkZ becomes blink

    :param obj: The object to look for user attributes.
    :type obj: str
    :param channelBoxOnly: If True will only return attrs seen in the channel box
    :type channelBoxOnly: bool
    :return userDefinedAttrs: User defined attributes, returns parent attributes only
    :rtype userDefinedAttrs: list(str)
    """
    userDefinedAttrs = cmds.listAttr(obj, userDefined=True)
    if not userDefinedAttrs:
        return list()
    return returnParentAttrs(obj, userDefinedAttrs, channelBoxOnly=channelBoxOnly)


def shuffleAttr(obj, attr, up=True, message=True):
    """Shuffles attributes up and down in the channel box.  up=True is up and up=False is down.

    Note: Requires selection of the obj for the cmds.deleteAttr() weird, this function does not handle select

    Note: Uses the Maya hack to drop attributes to the bottom of a list and is not undoable:

        cmds.deleteAttr(attribute=attrList[indx], name=obj)
        cmds.undo()

    :param obj: The object with the attribute
    :type obj: str
    :param attr: The name of the attribute
    :type attr: str
    :param up: If True shuffle the attribute up, if False shuffle down
    :type up: bool
    :param message: Report a message to the user?
    :type message: bool
    :return success: True if success
    :rtype success: bool
    """
    userDefinedAttrs = listUserDefinedAttrs(obj, channelBoxOnly=True)  # returns only parent attrs not every attribute

    if not userDefinedAttrs:
        if message:
            output.displayWarning("No user attributes found")
        return False

    # Be sure it's a parent attribute and not a child, convert to parent if so ----------------------------
    attrList = returnParentAttrs(obj, [attr], channelBoxOnly=True)
    if not attrList:
        if message:
            output.displayWarning("Attribute `{}` may be hidden in the channel box".format(attr))
        return False
    attr = attrList[0]

    # Check it's a user defined attribute and not a default which cannot be moved ------------------------
    if attr not in userDefinedAttrs:
        if message:
            output.displayWarning("Attribute `{}` cannot be moved, must be a user created "
                                  "attribute and not default".format(attr))
        return False

    # Attribute legit so continue ---------------------------------------------------------
    indx = userDefinedAttrs.index(attr)
    listLen = len(userDefinedAttrs)

    if up:  # Shuffle up ---------------------------------------------------------------
        if indx == 0:
            return False  # already at the top
        # index above should be dropped
        userDefinedAttrs = moveAttrBottomList(userDefinedAttrs, obj, indx - 1)
        indx -= 1
        # Now drop all below to -2 to reshuffle correctly and keep order
        if listLen == indx + 2:
            return False  # no attrs were below

        for a in userDefinedAttrs[indx + 1:-1]:  # drop remaining attrs that were under the original index, keeps order
            userDefinedAttrs = moveAttrBottomList(userDefinedAttrs, obj, indx + 1)
        if message:
            output.displayInfo("Attribute was shuffled up `{}`".format(attr))
    else:  # Shuffle down ---------------------------------------------------------------
        if indx == listLen - 1:
            return False  # then already at the bottom
        # index should be dropped
        userDefinedAttrs = moveAttrBottomList(userDefinedAttrs, obj, indx)
        newIndx = listLen - 1
        if indx == newIndx + 1:
            return False  # no attrs are above
        # now at bottom of list so drop everything from the same index
        for a in userDefinedAttrs[indx + 1:-1]:  # drop remaining attrs that were under the original index, keeps order
            userDefinedAttrs = moveAttrBottomList(userDefinedAttrs, obj, indx + 1)
        if message:
            output.displayInfo("Attribute was shuffled down `{}`".format(attr))
        return True


def shuffleAttrChannelBoxSel(up=True, message=True):
    """From the channel box selection shuffle the attributes up or down.

    Note: Uses the Maya hack and is not undoable:

        cmds.deleteAttr(attribute=attrList[indx], name=obj)
        cmds.undo()

    :param up: If True shuffle the attribute up, if False shuffle down
    :type up: bool
    :param message: Report a message to the user?
    :type message: bool
    """
    successList = list()

    objSel = cmds.ls(selection=True)
    if not objSel:
        if message:
            output.displayWarning("No objects are selected, please select an object and channel box selection.")
        return

    attributeNames = getChannelBoxAttrs(message=False)

    if not attributeNames:
        if message:
            output.displayWarning("No channel box names are selected, click name/s in the channel box.")
        return

    for obj in objSel:
        for attr in attributeNames:
            successList.append(shuffleAttr(obj, attr, up=up, message=True))


# ---------------------------
#  OPEN WINDOWS
# ---------------------------


def openAddAttrWindow():
    """Opens Maya's Add Attribute window"""
    selObjs = cmds.ls(selection=True)
    if not selObjs:
        output.displayWarning("Maya's Add Attribute window needs to be opened with an object selected.  "
                              "Please select an object. ")
        return
    mel.eval("dynAddAttrWin({})")


def openEditAttrWindow():
    """Opens Maya's Add Attribute window"""
    selObjs = cmds.ls(selection=True)
    if not selObjs:
        output.displayWarning("Maya's Edit Attribute window needs to be opened with an object selected.  "
                              "Please select an object. ")
        return
    mel.eval("dynRenameAttrWin({})")


def openDeleteAttrWindow():
    """Opens Maya's Add Attribute window"""
    selObjs = cmds.ls(selection=True)
    if not selObjs:
        output.displayWarning("Maya's Delete Attribute window needs to be opened with an object selected.  "
                              "Please select an object. ")
        return
    mel.eval("dynDeleteAttrWin({})")
