import json

from zoo.libs.maya import zapi
from zoo.libs.maya.api import nodes
from zoo.core.util import zlogging
from zoo.libs.hive import constants

logger = zlogging.getLogger(__name__)

DGGRAPH_ID_IDX = 0
DGGRAPH_NODES_IDX = 1
DGGRAPH_NAME_IDX = 2
DGGRAPH_METADATA_IDX = 3
DGGRAPH_OUTPUTNODE_IDX = 4
DGGRAPH_INPUTNODE_IDX = 5
DGGRAPH_NODEID_IDX = 0
DGGRAPH_NODE_IDX = 1
DGGRAPH_INPUTSID_IDX = 0
DGGRAPH_INPUTSNODE_IDX = 1
DGGRAPH_OUTPUTSID_IDX = 0
DGGRAPH_OUTPUTSNODE_IDX = 1


class NamedNodeAlreadyExists(Exception):
    pass


class NamedInputAlreadyExists(Exception):
    pass


class NamedOutputAlreadyExists(Exception):
    pass


class NamedDGGraph(object):
    """
    This class provides a way to store and access a named graph of nodes in Maya's Dependency Graph (DG).

    :param graphId: The name of the graph.
    :type graphId: str
    :param sceneNodes: A dictionary containing the node objects in the graph, with their node IDs as keys.
    :type sceneNodes: dict[str, :class:`zapi.DGNode`])
    :param inputs:
    :type inputs: dict[str, list[:class:`zapi.Plug`]]
    :param outputs:
    :type outputs: dict[str, :class:`zapi.Plug`]
    :param primaryInputNode:
    :type primaryInputNode: :class:`zapi.DGNode`
    :param primaryOutputNode:
    :type primaryOutputNode: :class:`zapi.DGNode`

    Example:

    Here is an example of the raw graph data that could be used to create an instance of this class:

    .. code-block:: python

        {'id': 'graphId',
          'nodes': [{'data': {'curveType': 3,
                              'frameRate': 24,
                              'frames': [0.0, 2.0, 5.0],
                              'inTangentAngles': [0.0, 0.0, 0.3217505543966422],
                              'inTangentWeights': [1.0, 1.0, 1.0],
                              'inTangents': [2, 8, 2],
                              'name': 'spine_M_squashCurve_animCurve',
                              'outTangentAngles': [-0.4636476090008062, 0.0, 0.0],
                              'outTangentWeights': [1.0, 1.0, 1.0],
                              'outTangents': [2, 8, 2],
                              'postInfinity': 0,
                              'preInfinity': 0,
                              'space': 2,
                              'type': 'animCurveTU',
                              'values': [0.0, -1.0, 0.0],
                              'weightTangents': False},
                     'id': 'nodeId'}]}

    """

    @staticmethod
    def inputDataToGraph(graphNodes, inputs):
        """Convert input data to graph format.

        :param graphNodes: A dictionary of graph nodes.
        :type graphNodes: dict[str, :class:`zapi.DGNode`]
        :param inputs: A dictionary of input data, where key is the name of the input \
         and value is the path to the node attribute.
        :type inputs: dict[str, list[str]]
        :return: A dictionary of input data in graph format, where key is the name of the input \
        and value is the value of the node attribute.
        :rtype: dict
        """
        data = {}
        for name, paths in inputs.items():
            for path in paths:
                try:
                    nodeId, attrName = path.split(":")
                except ValueError:
                    logger.error("Incorrect path expression: {}".format(path))
                    raise
                node = graphNodes.get(nodeId)
                if node is None:
                    continue
                data.setdefault(name, []).append(node.attribute(attrName))
        return data

    @staticmethod
    def outputDataToGraph(graphNodes, outputs):
        """Convert output data to graph format.

        :param graphNodes: A dictionary of graph nodes.
        :type graphNodes: dict[str, :class:`zapi.DGNode`]
        :param outputs: A dictionary of output data, where key is the name of the output \
         and value is the path to the node attribute.
        :type outputs: dict[str, str]
        :return: A dictionary of output data in graph format, where key is the name of the output \
        and value is the value of the node attribute.
        :rtype: dict
        """
        data = {}
        for name, path in outputs.items():
            nodeId, attrName = path.split(":")
            node = graphNodes.get(nodeId)
            if node is None:
                continue
            data[name] = node.attribute(attrName)
        return data

    @classmethod
    def create(cls, namedGraphData):
        """Class method that creates a new NamedDGGraph instance from raw graph data.

        :param namedGraphData: The raw graph data.
        :type namedGraphData: :class:`zoo.libs.hive.base.definition.NamedGraph`
        :return: A new NamedDGGraph instance created from the raw data.
        :rtype: :class:`NamedDGGraph`
        """
        createdNodes = {}
        # for each data node
        #   deserialize the node into the scene without connections
        #   yield the created node and the node id to allow renaming while deserializing
        #   store each created node into self for later access

        for nodeInfo in namedGraphData.nodes:
            nodeId = nodeInfo.id
            nodeData = nodeInfo["data"]
            nodeObject, _ = nodes.deserializeNode(nodeData)
            createdNodes[nodeId] = zapi.nodeByObject(nodeObject)
        # for each internal connection
        #   create the connection
        for connection in namedGraphData.connections:
            sourceNode = createdNodes[connection["source"]]
            destinationNode = createdNodes[connection["destination"]]
            sourcePlug = sourceNode.attribute(connection["sourcePlug"])
            destPlug = destinationNode.attribute(connection["destinationPlug"])
            sourcePlug.connect(destPlug)
        inputs = NamedDGGraph.inputDataToGraph(createdNodes, namedGraphData.inputs())
        outputs = NamedDGGraph.outputDataToGraph(createdNodes, namedGraphData.outputs())

        return NamedDGGraph(namedGraphData.id, namedGraphData.name, namedGraphData.metaData,
                            createdNodes, inputs, outputs)

    def __init__(self, graphId, name, metaData, sceneNodes, inputs, outputs,
                 primaryInputNode=None, primaryOutputNode=None):
        self._graphId = graphId
        self._name = name
        self._nodes = sceneNodes
        self._inputs = inputs  # type: dict[str, list[zapi.Plug]]
        self._outputs = outputs  # type: dict[str, zapi.Plug]
        self._primaryInputNode = primaryInputNode
        self._primaryOutputNode = primaryOutputNode
        self._metaData = metaData

    def __repr__(self):
        return "<{}> name: {}".format(self.__class__.__name__, self.name())

    def graphId(self):
        """Returns the Graph instance unique identifier.

        :rtype: str
        """
        return self._graphId

    def setGraphId(self, newId):
        self._graphId = newId

    def name(self):
        """Returns the name of the graph.

        :return: The name of the graph.
        :rtype: str
        """
        return self._name

    def rename(self, name):
        """Renames the graph.

        :param name: The new name for the graph.
        :type name: str
        """
        self._name = name

    def version(self):
        """Returns the version number of this graph instance. i.e. 1.0.0.

        :rtype: str
        """
        return self._metaData.get("version", "1.0.0")

    def metaData(self):
        """Returns the metaData dict for this graph.

        :rtype: dict
        """
        return self._metaData

    def clearNodes(self):
        """Clears the current graph of nodes without deleting the nodes.
        """
        self._nodes = {}
        self._inputs = {k: [] for k in self._inputs.keys()}
        self._outputs = {k: "" for k in self._outputs.keys()}

    def clearInputs(self):
        """Clears the current graph of inputs.
        """
        self._inputs = {}

    def clearOutputs(self):
        """Clears the current graph of outputs.
        """
        self._outputs = {}

    def hasNode(self, node):
        for n in self._nodes.values():
            if n == node:
                return True
        return False

    def node(self, nodeId):
        """Returns the node in the graph with the given ID.

        :param nodeId: The ID of the node to retrieve.
        :type nodeId: str
        :return: The node with the given ID, or None if no such node exists.
        :rtype: :class:`zapi.DGNode` or None
        """
        return self._nodes.get(nodeId)

    def nodes(self):
        """Returns the dictionary of nodes in the graph.

        :return: The dictionary of nodes in the graph, with their node IDs as keys.
        :rtype: dict[str, :class:`zapi.DGNode`]
        """
        return self._nodes

    def hasPrimaryInputNode(self):
        """Check if the graph has a primary input node.

        :return: True if the primary input node exists, False otherwise.
        :rtype: bool
        """
        return self._primaryInputNode is not None and self._primaryInputNode.exists()

    def hasPrimaryOutputNode(self):
        """Check if the graph has a primary output node.

        :return: True if the primary output node exists, False otherwise.
        :rtype: bool
        """
        return self._primaryOutputNode is not None and self._primaryOutputNode.exists()

    def primaryInputNode(self):
        """Get the primary input node of the graph.

        :return: The primary input node of the graph.
        :rtype: :class:`zapi.DGNode`
        """
        return self._primaryInputNode

    def primaryOutputNode(self):
        """Get the primary output node of the graph.

        :return: The primary output node of the graph.
        :rtype: :class:`zapi.DGNode`
        """
        return self._primaryOutputNode

    def _connectInputsToNode(self):
        """Connects inputs to the primary input node.
        """
        for inputName, plugs in self._inputs.items():
            if not plugs:
                continue
            plug = plugs[0]
            newAttr = self._primaryInputNode.addAttribute(inputName,
                                                          Type=plug.apiType(),
                                                          value=plug.value(),
                                                          )
            for plug in plugs:
                if not plug.mfn().connectable:
                    continue
                source = plug.source()
                if source is not None:
                    sourceNode = source.node()
                    if not self.hasNode(sourceNode):
                        source.connect(newAttr)
                newAttr.connect(plug)

    def _connectOutputsToNode(self):
        """
        Connects outputs to the primary output node.
        """
        for outputName, plug in self._outputs.items():
            newAttr = self._primaryOutputNode.addAttribute(outputName,
                                                           Type=plug.apiType(),
                                                           value=plug.value(),
                                                           )

            for dest in plug.destinations():
                if self.hasNode(dest.node()):
                    continue
                newAttr.connect(dest)

            plug.connect(newAttr)

    def createIONodes(self):
        """Create input and output nodes for the graph and connects these input and output nodes into the graph.
        """
        if not self.hasPrimaryInputNode():
            self._primaryInputNode = zapi.createDG("{}Inputs".format(self.name()), "network")

        if not self.hasPrimaryOutputNode():
            self._primaryOutputNode = zapi.createDG("{}Outputs".format(self.name()), "network")
        self._connectInputsToNode()
        self._connectOutputsToNode()

    def _reconnectInputsToScene(self, modifier):
        """Reconnects inputs to the scene.
        """
        for inputName, internalNodePlugs in self._inputs.items():
            for plug in internalNodePlugs:
                inputNodePlug = plug.source()
                if inputNodePlug is None or inputNodePlug.node() != self._primaryInputNode:
                    continue
                inputNodePlug.disconnect(plug, modifier, False)
                # incoming connection outside this graph
                externalInputAttrSource = inputNodePlug.source()
                if externalInputAttrSource:
                    externalInputAttrSource.connect(plug, mod=modifier, apply=False)

    def _reconnectOutputsToScene(self, modifier):
        """Reconnects outputs to the scene.
        """
        for outputName, plug in self._outputs.items():
            for dest in plug.destinations():
                if dest.node() != self._primaryOutputNode:
                    continue
                plug.disconnect(dest, modifier, False)
                for outDest in dest.destinations():
                    plug.connect(outDest, mod=modifier, apply=False)

    def delete(self, modifier=None):
        modifier = modifier or zapi.dgModifier()

        # To avoid certain nodes like the vector product node from erroring when the upstream node
        # is deleted, we first disconnect.
        for n in self._nodes.values():
            if n is None or not n.exists():
                continue
            for source, destination in n.iterConnections(source=True, destination=False):
                source.disconnect(destination, modifier, apply=False)
            for source, destination in n.iterConnections(source=False, destination=True):
                destination.disconnect(source, modifier, apply=False)
        for n in self._nodes.values():
            if n is None or not n.exists():
                continue
            n.delete(mod=modifier, apply=False)
        if self._primaryInputNode is not None:
            self._primaryInputNode.delete(mod=modifier, apply=False)
        if self._primaryOutputNode is not None:
            self._primaryOutputNode.delete(mod=modifier, apply=False)
        modifier.doIt()

    def deleteIONodes(self, modifier=None):
        """Deletes input and output nodes.
        """
        modifier = modifier or zapi.dgModifier()

        if self.hasPrimaryInputNode():
            self._reconnectInputsToScene(modifier)
            self._primaryInputNode.delete(mod=modifier, apply=False)
        if self.hasPrimaryOutputNode():
            self._reconnectOutputsToScene(modifier)
            self._primaryOutputNode.delete(mod=modifier, apply=False)
        modifier.doIt()

    def addNode(self, nodeId, node):
        """Add a node to the graph.

        :param nodeId: The identifier of the node.
        :type nodeId: str
        :param node: The node to be added.
        :type node: :class:`zapi.DGNode`
        """
        if nodeId in self._nodes:
            raise NamedNodeAlreadyExists("Node by id: {} already exists!".format(nodeId))

        self._nodes[nodeId] = node

    def addInput(self, inputId, plug):
        """Add an input to the graph.

        :param inputId: The identifier of the input.
        :type inputId: str
        :param plug: The input to be added.
        :type plug: :class:`zapi.Plug` or list[:class:`zapi.Plug`]
        """
        if isinstance(plug, list):
            for i in plug:
                self.addInput(inputId, i)
            return
        if any(i == plug for i in self._inputs.get(inputId, [])):
            raise NamedInputAlreadyExists("Input by id: {} already exists!".format(inputId))
        if self.hasPrimaryInputNode():
            newAttr = self._primaryInputNode.addAttribute(inputId,
                                                          Type=plug.apiType(),
                                                          value=plug.value(),
                                                          )
            source = plug.source()
            if source is not None:
                sourceNode = source.node()
                if not self.hasNode(sourceNode):
                    source.connect(newAttr)
            newAttr.connect(plug)
        self._inputs.setdefault(inputId, []).append(plug)

    def renameInput(self, inputId, newName):

        try:
            self._inputs[newName] = self._inputs[inputId]
            del self._inputs[inputId]
        except KeyError:
            pass
        if self.hasPrimaryInputNode():
            inputAttr = self._primaryInputNode.attribute(inputId)
            if inputAttr is not None:
                inputAttr.rename(newName)

    def renameOutput(self, outputId, newName):
        try:
            self._outputs[newName] = self._outputs[outputId]
            del self._outputs[outputId]
        except KeyError:
            pass
        if self.hasPrimaryOutputNode():
            inputAttr = self._primaryOutputNode.attribute(outputId)
            if inputAttr is not None:
                inputAttr.rename(newName)

    def addOutput(self, outputId, plug):
        """Add an output to the graph.

        :param outputId: The identifier of the output.
        :type outputId: str
        :param plug: The output to be added.
        :type plug: :class:`zapi.Plug`
        """
        if outputId in self._outputs:
            raise NamedInputAlreadyExists("Output by id: {} already exists!".format(outputId))
        if self.hasPrimaryOutputNode():
            newAttr = self._primaryOutputNode.addAttribute(outputId,
                                                           Type=plug.apiType(),
                                                           value=plug.value(),
                                                           )
            for dest in plug.destinations():
                if self.hasNode(dest.node()):
                    continue
                newAttr.connect(dest)

            plug.connect(newAttr)
        self._outputs[outputId] = plug

    def findNodes(self, *nodeIds):
        """Returns a list of nodes in the graph with the given IDs.

        :param nodeIds: The IDs of the nodes to retrieve.
        :type nodeIds: str
        :return: A list of nodes with the given IDs, in the same order as the IDs. \
        If a node with a given ID does not exist, the corresponding list element will be None.
        :rtype: list[:class:`zapi.DGNode` or None]
        """
        results = [None] * len(nodeIds)
        for index, nodeId in enumerate(nodeIds):
            results[index] = self._nodes.get(nodeId)
        return results

    def inputs(self):
        """Returns a dictionary of inputs, with the key being the name and value being the input plug object.
        If a primary input node exists, it also includes attributes that exist on the primary input node.

        :return: dictionary of inputs
        :rtype: dict
        """
        ins = {k: v for k, v in self._inputs.items()}
        if self.hasPrimaryInputNode():
            for k, v in self._inputs.items():
                existingAttr = self._primaryInputNode.attribute(k)
                if existingAttr is not None:
                    ins[k] = [existingAttr]
        return ins

    def outputs(self):
        """Returns a dictionary of outputs, with the key being the name and value being the output plug object.
        If a primary output node exists, it also includes attributes that exist on the primary output node.

        :return: dictionary of outputs
        :rtype: dict
        """
        outs = {k: v for k, v in self._outputs.items()}
        if self.hasPrimaryOutputNode():
            for k, v in self._outputs.items():
                existingAttr = self._primaryOutputNode.attribute(k)
                if existingAttr is not None:
                    outs[k] = existingAttr
        return outs

    def inputAttr(self, inputId):
        """Get the attribute of an input.

        :param inputId: The identifier of the input attribute.
        :type inputId: str
        :return: The attribute of the input. If the primary input node exists, \
        it returns the attribute on the primary input node. If not it returns the input plug object.
        :rtype: list[:class:`zapi.Plug`]
        """
        if self.hasPrimaryInputNode():
            attr = self._primaryInputNode.attribute(inputId)
            if attr is not None:
                return [attr]
        return self._inputs.get(inputId, [])

    def outputAttr(self, outputId):
        """Get the attribute of an output.

        :param outputId: The identifier of the output attribute.
        :type outputId: str
        :return: The attribute of the output. If the primary output node exists, \
        it returns the attribute on the primary output node. If not it returns the output plug object.
        :rtype: :class:`zapi.Plug`
        """
        if self.hasPrimaryOutputNode():
            attr = self._primaryOutputNode.attribute(outputId)
            if attr is not None:
                return attr
        return self._outputs.get(outputId)

    def setInputAttr(self, inputId, value):
        if isinstance(value, zapi.Plug):
            self.connectToInput(inputId, value)
            return
        inputAttrs = self.inputAttr(inputId)
        if not inputAttrs:
            return
        for inputAttr in inputAttrs:
            inputAttr.set(value)

    def connectToInput(self, inputId, source):
        inputAttrs = self.inputAttr(inputId)
        if not inputAttrs:
            return
        for inputAttr in inputAttrs:
            source.connect(inputAttr)

    def connectFromOutput(self, outputId, destinations):
        outputAttr = self.outputAttr(outputId)
        if not outputAttr:
            return False
        connected = False
        for dest in destinations:
            outputAttr.connect(dest)
            connected = True
        return connected

    def serializeIO(self):
        """Serialize the inputs and outputs of the graph.

        :return: A dictionary with the keys "inputs" and "outputs" containing the serialized \
        inputs and outputs respectively.
        :rtype: dict
        """
        inputNodes = {}
        if self._primaryInputNode:
            for existingAttr in self._primaryInputNode.iterExtraAttributes():
                for dest in existingAttr.destinations():
                    inputNodes.setdefault(dest.node(), []).append({"plug": dest,
                                                                   "key": existingAttr.partialName(False)})
        else:
            for k, plugs in self._inputs.items():
                for p in plugs:
                    inputNodes.setdefault(p.node(), []).append({"plug": p, "key": k})
        outputNodes = {}
        if self._primaryOutputNode:
            for existingAttr in self._primaryOutputNode.iterExtraAttributes():
                sourcePlug = existingAttr.source()
                if sourcePlug is not None:
                    outputNodes[sourcePlug.node()] = {"plug": sourcePlug,
                                                      "key": existingAttr.partialName(False)}
        else:
            outputNodes = {p.node(): {"plug": p,
                                      "key": k} for k, p in self._outputs.items()}

        inputs = {}
        outputs = {}
        for nodeId, node in self._nodes.items():
            hasInputs = inputNodes.get(node, [])
            hasOutput = outputNodes.get(node)
            for v in hasInputs:
                inputs.setdefault(v["key"], []).append(":".join((nodeId, v["plug"].partialName())))
            if hasOutput:
                outputs[hasOutput["key"]] = ":".join((nodeId, hasOutput["plug"].partialName()))
        return {"inputs": inputs,
                "outputs": outputs}

    def externalConnections(self):
        listedNodes = {v: k for k, v in self._nodes.items()}
        externalInputs = []
        externalOutputs = []
        for nodeId, node in self._nodes.items():
            for destination, source in node.iterConnections(source=False, destination=True):
                sourceNode = source.node()
                if sourceNode not in listedNodes:
                    externalInputs.append((source, destination))
        for nodeId, node in self._nodes.items():
            for destination, source in node.iterConnections(source=True, destination=False):
                if source.apiType() in (zapi.attrtypes.kMFnMessageAttribute,):
                    continue
                sourceNode = source.node()
                if sourceNode not in listedNodes:
                    externalOutputs.append((destination, source))
        return {"inputs": externalInputs,
                "outputs": externalOutputs}

    def serialize(self):
        """Returns a serialized representation of the graph.

        :return: A serialized representation of the graph.
        :rtype: dict
        """
        data = {"id": self._graphId,
                "name": self._name,
                "metaData": self._metaData}
        nodeData = []
        connections = []
        listedNodes = {v: k for k, v in self._nodes.items()}

        inputsOutputs = self.serializeIO()
        removeFromData = []
        for nodeId, node in self._nodes.items():
            if node is None or not node.exists():
                removeFromData.append(nodeId)
                continue

            d = node.serializeFromScene(skipAttributes=("message",),
                                        includeNamespace=False,
                                        includeConnections=False,
                                        useShortNames=True,
                                        )
            nData = {"id": nodeId,
                     "data": d}
            for destination, source in node.iterConnections(source=False, destination=True):
                sourceNode = source.node()
                if sourceNode not in listedNodes:
                    logger.warning("Missing input for path: {}".format(source.name()))
                    continue
                sourceId = listedNodes.get(sourceNode)

                connectionData = {"sourcePlug": source.partialName(),
                                  "source": sourceId,
                                  "destinationPlug": destination.partialName(),
                                  "destination": nodeId}
                connections.append(connectionData)
            nodeData.append(nData)
        data["nodes"] = nodeData
        data["connections"] = connections
        data["inputs"] = inputsOutputs["inputs"]
        data["outputs"] = inputsOutputs["outputs"]
        for nodeId in removeFromData:
            del self._nodes[nodeId]
        return data


def createNamedGraph(layer, namedGraphData, track=True, createIONodes=False):
    """Creates a Maya DG graph from the provided NamedGraph instance.

    :param layer: The Hive Layer to create the graph on, currently only support Guide and rig layer.
    :type layer: :class:`zoo.libs.hive.base.hivenodes.HiveLayer`
    :param namedGraphData:
    :type namedGraphData: :class:`zoo.libs.hive.base.definition.NamedGraph`
    :param track: Whether this graph will be tracked as meta-data on the provided layer
    :type track: bool
    :param createIONodes: Whether to create the input and output DG nodes for this graph.
    :type createIONodes: bool
    :return: Returns the newly created graph instance.
    :rtype: :class:`NamedDGGraph`
    """
    newGraph = NamedDGGraph.create(namedGraphData)
    if not track:
        return newGraph
    # don't track instances if we already have the same graph in the scene
    elif layer.hasNamedGraph(newGraph.name()):
        return newGraph
    graphAttr = layer.attribute(constants.DG_GRAPH_ATTR)
    index = 0
    for index, newElement in enumerate(graphAttr):
        if not newElement.child(DGGRAPH_ID_IDX).value():
            break
        index += 1
    else:
        newElement = graphAttr[index]
    newElement.child(DGGRAPH_ID_IDX).set(newGraph.graphId())
    newElement.child(DGGRAPH_NAME_IDX).set(newGraph.name())
    newElement.child(DGGRAPH_METADATA_IDX).set(json.dumps(newGraph.metaData()))
    nodeElement = newElement.child(DGGRAPH_NODES_IDX)
    for index, [nodeId, node] in enumerate(newGraph.nodes().items()):
        nodeDataElement = nodeElement.element(index)
        nodeDataElement.child(DGGRAPH_NODEID_IDX).set(nodeId)
        layer.connectToByPlug(nodeDataElement.child(DGGRAPH_NODE_IDX), node)

    if createIONodes:
        newGraph.createIONodes()
        newGraph.primaryInputNode().message.connect(newElement.child(DGGRAPH_INPUTNODE_IDX))
        newGraph.primaryOutputNode().message.connect(newElement.child(DGGRAPH_OUTPUTNODE_IDX))
    # add the IO nodes if required
    return newGraph


def hasNamedGraph(layer, graphName):
    """Determines if the given graph exists on the layer given the name,

    :param layer: The hive layer instance to search on.
    :type layer: :class:`zoo.libs.hive.base.hivenodes.HiveLayer`
    :param graphName: The graph name to filter by.
    :type graphName: str
    :rtype: bool
    """
    for graphElement in layer.attribute(constants.DG_GRAPH_ATTR):
        sceneGraphName = graphElement.child(DGGRAPH_NAME_IDX).value()
        if sceneGraphName == graphName:
            return True
    return False


def namedGraph(layer, graphName, graphRegistry):
    """Retrieve the named graph on the given layer based on its name.

    :param layer: The hive layer instance to search on.
    :type layer: :class:`zoo.libs.hive.base.hivenodes.HiveLayer`
    :param graphName: The graph name to filter by.
    :type graphName: str
    :param graphRegistry: The registry instance to look for the graph.
    :type graphRegistry: :class:`zoo.libs.hive.base.registry.GraphRegistry`
    :returns: The named graph if it exists, otherwise None.
    :rtype: :class:`zoo.libs.hive.base.serialization.NamedDGGraph` or None
    """
    comp = layer.attribute(constants.DG_GRAPH_ATTR)
    if len(comp) == 2:
        return
    for graphElement in layer.attribute(constants.DG_GRAPH_ATTR):
        if len(graphElement) == 2:
            return
        sceneGraphName = graphElement.child(DGGRAPH_NAME_IDX).value()

        if sceneGraphName != graphName:
            continue
        sceneGraphId = graphElement.child(DGGRAPH_ID_IDX).value()
        return _namedGraphFromElement(graphElement, sceneGraphName, sceneGraphId,
                                      graphRegistry.graph(sceneGraphId))


def namedGraphs(layer, graphRegistry):
    """Returns all NamedGraphs on the given layer.

    :param layer: The hive layer instance to search on.
    :type layer: :class:`zoo.libs.hive.base.hivenodes.HiveLayer`
    :param graphRegistry: The registry instance to look for the graph.
    :type graphRegistry: :class:`zoo.libs.hive.base.registry.GraphRegistry`
    :rtype: list[:class:`zoo.libs.hive.base.serialization.NamedDGGraph`]
    """
    for graphElement in layer.attribute(constants.DG_GRAPH_ATTR):
        if len(graphElement) == 2:
            return
        sceneGraphName = graphElement.child(DGGRAPH_NAME_IDX).value()
        sceneGraphId = graphElement.child(DGGRAPH_ID_IDX).value()
        if not sceneGraphId:
            continue
        yield _namedGraphFromElement(graphElement, sceneGraphName, sceneGraphId,
                                     graphRegistry.graph(sceneGraphId))


def findNamedGraphs(layer, graphRegistry, names):
    """Returns all NamedGraphs on the given layer with the provided names.

    :param layer: The hive layer instance to search on.
    :type layer: :class:`zoo.libs.hive.base.hivenodes.HiveLayer`
    :param graphRegistry: The registry instance to look for the graph.
    :type graphRegistry: :class:`zoo.libs.hive.base.registry.GraphRegistry`
    :param names: A list of graph names to retrieve graph instances for.
    :type names: list[str]
    :rtype: list[:class:`zoo.libs.hive.base.serialization.NamedDGGraph` or None]
    """
    results = [None] * len(names)

    for graphElement in layer.attribute(constants.DG_GRAPH_ATTR):
        if len(graphElement) == 2:
            return
        sceneGraphName = graphElement.child(DGGRAPH_NAME_IDX).value()
        if sceneGraphName not in names:
            continue
        sceneGraphId = graphElement.child(DGGRAPH_ID_IDX).value()
        results[names.index(sceneGraphName)] = _namedGraphFromElement(graphElement, sceneGraphName, sceneGraphId,
                                                                      graphRegistry.graph(sceneGraphId))
    return results


def deleteNamedGraph(layer, graphName, graphRegistry, modifier=None):
    """Deletes the NamedGraph if found by its name.

    :param layer: The hive layer instance to search on.
    :type layer: :class:`zoo.libs.hive.base.hivenodes.HiveLayer`
    :param graphName: The graph name to filter by.
    :type graphName: str
    :param graphRegistry: The registry instance to look for the graph.
    :type graphRegistry: :class:`zoo.libs.hive.base.registry.GraphRegistry`
    :param modifier: The maya dagModifier to use for deletion.
    :type modifier: :class:`zapi.dagModifier` or None
    """

    elementsToPurge = []
    for graphElement in layer.attribute(constants.DG_GRAPH_ATTR):
        if len(graphElement) == 2:
            return
        sceneGraphName = graphElement.child(DGGRAPH_NAME_IDX).value()
        if sceneGraphName != graphName:
            continue
        sceneGraphId = graphElement.child(DGGRAPH_ID_IDX).value()
        graphInstance = _namedGraphFromElement(graphElement, sceneGraphName, sceneGraphId,
                                               graphRegistry.graph(sceneGraphId))
        graphElement.child(DGGRAPH_ID_IDX).set("")
        graphElement.child(DGGRAPH_NAME_IDX).set("")
        graphInstance.delete(modifier)
        elementsToPurge.append(graphElement)
    for element in elementsToPurge:
        element.delete(modifier=modifier)


def _namedGraphFromElement(graphElement, graphName, graphId, graphData):
    nodeData = {}
    for element in graphElement.child(DGGRAPH_NODES_IDX):
        nodeData[element.child(DGGRAPH_NODEID_IDX).value()] = element.child(DGGRAPH_NODE_IDX).sourceNode()
    inputData = graphData.inputs()
    outData = graphData.outputs()

    inputData = NamedDGGraph.inputDataToGraph(nodeData, inputData)
    outData = NamedDGGraph.outputDataToGraph(nodeData, outData)

    metaData = json.loads(graphElement.child(DGGRAPH_METADATA_IDX).value() or "{}")

    return NamedDGGraph(graphId, graphName, metaData, nodeData, inputData, outData,
                        graphElement.child(DGGRAPH_INPUTNODE_IDX).sourceNode(),
                        graphElement.child(DGGRAPH_OUTPUTNODE_IDX).sourceNode())
