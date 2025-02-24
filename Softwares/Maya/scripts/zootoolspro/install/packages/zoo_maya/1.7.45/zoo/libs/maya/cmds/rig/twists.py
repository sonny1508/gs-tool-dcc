"""Code for calculating twist between two objects using quaternions.


Example use:

.. code-block:: python

    from zoo.libs.maya import zapi
    from zoo.libs.maya.cmds.rig import twists
    twists.twistNodeNetwork(zapi.nodeByName("joint1"),
                            zapi.nodeByName("joint1"),
                            drivenObj=zapi.nodeByName("twist1deformer"),
                            drivenAttr="endAngle",
                            axis="x",
                            inverse=True)


.. code-block:: python
    from zoo.libs.maya.cmds.rig import twists
    twists.XyzRotDifferentiator(inputNode1="locator1", inputNode2="locator2", outputNode="pCube1"
                                        attrs=["rotateX", "rotateY", "rotateZ"])

Author: Andrew Silke
"""

from maya import cmds
from zoo.libs.maya import zapi
from zoo.libs.utils import output

try:
    from zoo.libs.hive import api
except:
    pass


def obj():
    """Helper for UI, returns the selected object"""
    selObjs = cmds.ls(selection=True)
    if not selObjs:
        output.displayWarning("No objects selected, please select an object")
        return ""
    return selObjs[0]


def twistNodeNetwork(controlA, controlB, axis="x", drivenObj=None, drivenAttr="", inverse=False):
    inverseNode = None
    graphData = api.Configuration().graphRegistry().graph("distributedTwist")
    sceneGraph = api.serialization.NamedDGGraph.create(graphData)
    sceneGraph.connectToInput("driverSrtWorldInvMtx", controlB.attribute("worldInverseMatrix")[0])
    sceneGraph.connectToInput("drivenSrtWorldMtx", controlA.attribute("worldMatrix")[0])

    # Get nodes ---------------------
    twistOffsetNode = sceneGraph.node("twistOffset")
    offsetQuatNode = sceneGraph.node("twistOffsetQuat")
    offsetEulerNode = sceneGraph.node("twistOffsetEuler")

    # set offsetEuler to have the parent axis match the give axis -----------------
    rotOrder = 0  # xyz (Z parent)
    if axis == "x":
        rotOrder = 1  # yzx (X parent)
    elif axis == "y":
        rotOrder = 2  # zxy (Y parent)
    offsetEulerNode.attribute("inputRotateOrder").set(rotOrder)

    # Set axis, is connected to x by default -----------------
    if axis != "x":
        offsetQuatNode.outputQuatX.disconnectAll()
        outAttr = "outputQuat{}".format(axis.upper())
        inAttr = "inputQuat{}".format(axis.upper())
        offsetQuatNode.attribute(outAttr).connect(offsetEulerNode.attribute(inAttr))

    # Invert the output ----------------------
    if inverse:
        inverseNode = zapi.createDG("twistInverseMult", "multiplyDivide")
        inverseNode.attribute("input2{}".format(axis.upper())).set(-1.0)

    # Driven attribute -----------------------
    if drivenObj:
        outAttr = "outputRotate{}".format(axis.upper())
        if not inverse:
            offsetEulerNode.attribute(outAttr).connect(drivenObj.attribute(drivenAttr))
        else:  # Invert
            invertInAttr = "input1{}".format(axis.upper())
            invertOutAttr = "output{}".format(axis.upper())
            offsetEulerNode.attribute(outAttr).connect(inverseNode.attribute(invertInAttr))
            inverseNode.attribute(invertOutAttr).connect(drivenObj.attribute(drivenAttr))

    return twistOffsetNode, offsetQuatNode, offsetEulerNode, inverseNode


class XyzRotDifferentiator(object):
    xyzList = ["X", "Y", "Z"]

    def __init__(self, inputNode1="", inputNode2="", outputNode="", attrs=()):
        """Differentiates the rotation between two objects and outputs the difference to the output node.
        Math is calculated using quaternions and so avoids gimbal issues. Will flip at 180 degrees.

        :param inputNode1: The first object to measure the rotation difference from
        :type inputNode1: str
        :param inputNode2: The second object to measure the rotation difference from
        :type inputNode2: str
        :param outputNode: The object to receive all the attribute offset information
        :type outputNode: str
        :param attrs: A list of attribute names that should exist on the output node eg. [rotateX, rotateY, rotateZ]
        :type attrs: list(str)
        """
        super(XyzRotDifferentiator, self).__init__()
        self.nodesXyzRotDifferentiator()
        self.inputNode1 = inputNode1
        self.inputNode2 = inputNode2
        self.outputNode = outputNode
        self.attrs = attrs

        if inputNode1 and inputNode2:
            self.connectInputNodes()
            if outputNode and attrs:
                self.connectAttributes()

    def connectToTwistOffset(self, eulerNode, axis="X"):
        """Connects the euler node to the twist offset node"""
        cmds.connectAttr("{}.outputQuat{}".format(self.decomposeMatrix, axis), "{}.inputQuat{}".format(eulerNode, axis))
        cmds.connectAttr("{}.outputQuatW".format(self.decomposeMatrix), "{}.inputQuatW".format(eulerNode))

    def nodesXyzRotDifferentiator(self):
        """Creates the nodes for the xyz rotation differentiator network"""
        self.multMatrix = cmds.createNode('multMatrix', name='twistOffset')
        self.decomposeMatrix = cmds.createNode('decomposeMatrix', name='twistOffsetQuat')
        self.quatToEulerX = cmds.createNode('quatToEuler', name='twistOffsetEulerX')
        self.quatToEulerY = cmds.createNode('quatToEuler', name='twistOffsetEulerY')
        self.quatToEulerZ = cmds.createNode('quatToEuler', name='twistOffsetEulerZ')
        self.eulerNodeList = [self.quatToEulerX, self.quatToEulerY, self.quatToEulerZ]

        cmds.connectAttr("{}.matrixSum".format(self.multMatrix), "{}.inputMatrix".format(self.decomposeMatrix))
        for i, node in enumerate(self.eulerNodeList):
            self.connectToTwistOffset(node, axis=self.xyzList[i])

    def connectInputNodes(self):
        """Connects the input nodes to the network"""
        cmds.connectAttr("{}.worldMatrix[0]".format(self.inputNode1), "{}.matrixIn[1]".format(self.multMatrix))
        cmds.connectAttr("{}.worldInverseMatrix[0]".format(self.inputNode2), "{}.matrixIn[2]".format(self.multMatrix))

    def connectAttributes(self):
        """Connects the network to the attributes on the output node"""
        for i, node in enumerate(self.eulerNodeList):
            cmds.connectAttr("{}.outputRotate{}".format(node, self.xyzList[i]),
                             "{}.{}".format(self.outputNode, self.attrs[i]))
