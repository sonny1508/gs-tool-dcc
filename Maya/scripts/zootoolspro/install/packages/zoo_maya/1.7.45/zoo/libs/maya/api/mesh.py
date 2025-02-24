from maya.api import OpenMaya as om2


def selectedVertices():
    """Yields the selected vertices in the scene.
    :return: First Element is the mesh path, second element is the list of vertex indices for that mesh.
    :rtype: Iterator[Tuple[om2.MDagPath, List[int]]]
    """
    sel = om2.MGlobal.getActiveSelectionList()
    for i in range(sel.length()):
        meshPath, component = sel.getComponent(i)
        if component.apiType() == om2.MFn.kMeshVertComponent:
            yield meshPath, om2.MFnSingleIndexedComponent(component).getElements()


def selectedEdges():
    """Yields the selected edges in the scene

    :return: First Element is the mesh path, second element is the list of edge indices for that mesh.
    :rtype: Iterator[Tuple[om2.MDagPath, List[int]]]
    """
    sel = om2.MGlobal.getActiveSelectionList()
    for i in range(sel.length()):
        meshPath, component = sel.getComponent(i)
        if component.apiType() == om2.MFn.kMeshEdgeComponent:
            yield meshPath, om2.MFnDoubleIndexedComponent(component).getElements()



def constructVerticeGraph(meshPath, vertices):
    meshIt = om2.MItMeshVertex(meshPath)
    graph = {}
    for vertex in vertices:
        meshIt.setIndex(vertex)

        for vtx in meshIt.getConnectedVertices():
            if vtx not in vertices:
                continue
            graph.setdefault(vertex, []).append(vtx)

    return graph


def sortLoops(neighborDict):
    """Sort vertex loop neighbors into individual loops

    :param neighborDict:  A dictionary formatted like {vertIndex: [neighborVertIdx, ...]}
    :type neighborDict: dict[int, list[int]]
    :return: a list of lists containing ordered vertex loops. if the loop is closed,\
    the first and last element will be the same.
    :type: list[list[int]]
    """
    neighborDict = dict(
        neighborDict
    )  # work on a copy of the dict so I don't destroy the original
    loops = []

    index = 0
    while index <= 1000:  # safety check to prevent infinite loops
        if not neighborDict:
            break
        vertLoop = [list(neighborDict.keys())[0]]
        vertLoop.append(neighborDict[vertLoop[-1]][0])

        # Loop over this twice: Once forward, and once backward
        # This handles loops that don't connect back to themselves
        for i in range(2):
            vertLoop = vertLoop[::-1]
            while vertLoop[0] != vertLoop[-1]:
                nextNeighbors = neighborDict[vertLoop[-1]]
                if len(nextNeighbors) == 1:
                    break
                elif nextNeighbors[0] == vertLoop[-2]:
                    vertLoop.append(nextNeighbors[1])
                else:
                    vertLoop.append(nextNeighbors[0])

        # Remove vertices I've already seen from the dict
        # Don't remove the same vert twice if the first and last items are the same
        start = 0
        if vertLoop[0] == vertLoop[-1]:
            start = 1
        for v in vertLoop[start:]:
            del neighborDict[v]
        loops.append(vertLoop)
        index += 1
    return loops


def vertexPositions(mesh, vertices, space=om2.MSpace.kWorld, sortKey=None):
    """use sortKey to sort by axis"""
    mfn = om2.MFnMesh(mesh)
    positions = [om2.MVector(mfn.getPoint(i, space)) for i in vertices]
    if sortKey and getattr(positions[0], sortKey) > getattr(positions[-1], sortKey):
        positions.reverse()
    return positions
