from collections import defaultdict
import sys
import traceback

import maya.cmds as cmds
import maya.mel as mel
import maya.api.OpenMaya as om

# Detect Python version
PY3 = sys.version_info[0] >= 3

# Returns Error Tuple
#     "uv": {}, [UUID] : [... uvId]
#     "vertex": {},[UUID] : [... vertexId ]
#     "edge" : {},[UUID] : [... edgeId ]
#     "polygon": {}, -> [UUID] : [... polygonId ]
#     "nodes" : [] -> [... nodes UUIDs]

# Blind / metadata node types that get left behind in a mesh's input history
INPUT_DATA_NODE_TYPES = (
    "polyBlindData",
    "subdBlindData",
    "oldBlindDataBase",
    "editMetadata",
    "clipToGhostData",
    "blindDataTemplate",
    "dataBlockTest",
)

# Namespaces Maya itself owns
DEFAULT_NAMESPACES = ("UI", "shared")

# Added by Maya itself and read by its skin tools, so not anyone's custom data
MAYA_ATTRIBUTES = frozenset(("liw", "lockInfluenceWeights"))

# Nodes left over from modelling, only junk once nothing is connected to them
DISCONNECTED_NODE_TYPES = (
    "polyExtrudeEdge",
    "polyExtrudeFace",
    "polyExtrudeVertex",
    "polyMergeVert",
    "polyMoveVertex",
    "polyUnite",
    "groupId",
)

# Mesh display options, as Maya makes them
MESH_DISPLAY_DEFAULTS = (
    ("displayVertices", False),
    ("displayBorders", False),
    ("displayMapBorders", False),
    ("displayEdges", 1),
    ("displayCenter", False),
    ("displayTriangles", False),
    ("displayUVs", False),
    ("displayItemNumbers", 0),
    ("displayNonPlanar", False),
    ("displayNormal", False),
    ("displayTangent", False),
    ("displaySmoothMesh", 0),
    ("displaySubdComps", False),
    ("displayImmediate", False),
    ("backfaceCulling", 0),
    ("vertexBackfaceCulling", True),
)

# Maya's four default cameras, and whether each one is orthographic
DEFAULT_CAMERAS = (("persp", False), ("top", True), ("front", True), ("side", True))

# What a texture or utility node's message may lead to and still count as used,
# as MLdeleteUnused.mel decides it. Cameras and shaders are told apart by class.
RENDER_NODE_USERS = frozenset((
    "shadingEngine", "imagePlane", "arrayMapper", "directionalLight",
    "spotLight", "pointLight", "areaLight", "transform"))

# Internal Utility Functions
def _getNodeName(uuid):
    nodeName = cmds.ls(uuid, uuid=True)
    if nodeName:
        return nodeName[0]
    return None


def _sourcePlug(node, attr):
    """The plug feeding `node`.`attr`, or None."""
    plugs = cmds.listConnections("{}.{}".format(node, attr), source=True,
                                 destination=False, plugs=True, shapes=True) or []
    return plugs[0] if plugs else None


def _meshHistoryNode(shape):
    """The first node building `shape` that is not a deformer, or None.

    Follows the geometry itself, up from inMesh. Only what feeds the geometry
    is history: a per-face material's groupId is connected to the shape too,
    and survives Delete History, but builds nothing. Deformers, the groupParts
    between them and the original shape under them are what a rigged mesh is
    meant to have, so they are passed through - the same split the Cleanup's
    bake makes. Anything else (polyExtrude, polyUnite, a live mesh) is history.
    """
    plug = _sourcePlug(shape, "inMesh")
    visited = set()
    while plug:
        node, attr = plug.split(".", 1)
        if node in visited:
            return None
        visited.add(node)
        nodeType = cmds.nodeType(node)
        if "geometryFilter" in (cmds.nodeType(node, inherited=True) or []):
            # outputGeometry[i] is built from input[i].inputGeometry
            index = attr[attr.find("[") + 1:attr.find("]")] if "[" in attr else "0"
            plug = _sourcePlug(node, "input[{}].inputGeometry".format(index))
        elif nodeType == "groupParts":
            plug = _sourcePlug(node, "inputGeometry")
        elif nodeType == "mesh" and cmds.getAttr(node + ".intermediateObject"):
            plug = _sourcePlug(node, "inMesh")
        else:
            return node
    return None


def _orphanedBlindDataTemplates():
    """blindDataTemplate nodes whose typeId nothing in the scene uses."""
    templates = cmds.ls(type="blindDataTemplate") or []
    if not templates:
        return []

    usedIds = set()
    for typ in ("polyBlindData", "subdBlindData"):
        for user in cmds.ls(type=typ) or []:
            try:
                usedIds.add(cmds.getAttr(user + ".typeId"))
            except Exception:
                pass

    orphans = []
    for template in templates:
        try:
            if cmds.getAttr(template + ".typeId") in usedIds:
                continue
        except Exception:
            continue
        orphans.append(template)
    return orphans


def _deleteOrphanedBlindDataTemplates():
    """Delete blindDataTemplate nodes whose typeId nothing in the scene uses."""
    for template in _orphanedBlindDataTemplates():
        try:
            cmds.lockNode(template, lock=False)
        except Exception:
            pass
        try:
            cmds.delete(template)
        except Exception as e:
            cmds.warning("Failed to delete blind data template {}: {}".format(
                template, str(e)))


# Functions to be imported
def trailingNumbers(nodes, _):
    trailingNumbers = []
    for node in nodes:
        nodeName = _getNodeName(node)
        if nodeName and nodeName[-1].isdigit():
                trailingNumbers.append(node)
    return "nodes", trailingNumbers

def duplicatedNames(nodes, _):
    nodesByShortName = defaultdict(list)
    for node in nodes:
        nodeName = _getNodeName(node)
        name = nodeName.rsplit('|', 1)[-1]
        nodesByShortName[name].append(node)
    invalid = []
    for name, shortNameNodes in nodesByShortName.items():
        if len(shortNameNodes) > 1:
            invalid.extend(shortNameNodes)
    return "nodes", invalid


def namespaces(nodes, _):
    namespaces = []
    for node in nodes:
        nodeName = _getNodeName(node)
        if nodeName and ':' in nodeName:
            namespaces.append(node)
    return "nodes", namespaces


def shapeNames(nodes, _):
    shapeNames = []
    for node in nodes:
        nodeName = _getNodeName(node)
        if nodeName:
            new = nodeName.split('|')
            shape = cmds.listRelatives(nodeName, shapes=True)
            if shape:
                shapename = new[-1] + "Shape"
                if shape[0] != shapename:
                    shapeNames.append(node)
    return "nodes", shapeNames

def triangles(_, SLMesh):
    triangles = defaultdict(list)
    selIt = om.MItSelectionList(SLMesh)
    while not selIt.isDone():
        faceIt = om.MItMeshPolygon(selIt.getDagPath())
        fn = om.MFnDependencyNode(selIt.getDagPath().node())
        uuid = fn.uuid().asString()
        while not faceIt.isDone():
            numOfEdges = faceIt.getEdges()
            if len(numOfEdges) == 3:
                triangles[uuid].append(faceIt.index())
            try:
                faceIt.next(True)  # Try with argument first
            except TypeError:
                faceIt.next()  # If that fails, try without argument
        selIt.next()  # No argument for selection iterator
    return "polygon", triangles

def ngons(_, SLMesh):
    ngons = defaultdict(list)
    selIt = om.MItSelectionList(SLMesh)
    while not selIt.isDone():
        faceIt = om.MItMeshPolygon(selIt.getDagPath())
        fn = om.MFnDependencyNode(selIt.getDagPath().node())
        uuid = fn.uuid().asString()
        while not faceIt.isDone():
            numOfEdges = faceIt.getEdges()
            if len(numOfEdges) > 4:
                ngons[uuid].append(faceIt.index())
            
            # For faceIt.next(), use a try-except to handle different behaviors
            try:
                faceIt.next(True)  # Try with an argument first (based on first error)
            except TypeError:
                faceIt.next()  # If that fails, try without argument
        
        # For selIt.next(), no argument (based on second error)
        selIt.next()
    
    return "polygon", ngons

def hardEdges(_, SLMesh):
    hardEdges = defaultdict(list)
    selIt = om.MItSelectionList(SLMesh)
    while not selIt.isDone():
        edgeIt = om.MItMeshEdge(selIt.getDagPath())
        fn = om.MFnDependencyNode(selIt.getDagPath().node())
        uuid = fn.uuid().asString()
        while not edgeIt.isDone():
            if edgeIt.isSmooth is False and edgeIt.onBoundary() is False:
                hardEdges[uuid].append(edgeIt.index())
            edgeIt.next()
        selIt.next()
    return "edge", hardEdges


def lockedNormals(_, SLMesh):
    # Locks live on face-vertices, but a vertex is what an artist selects to unlock
    lockedNormals = defaultdict(list)
    selIt = om.MItSelectionList(SLMesh)
    while not selIt.isDone():
        mesh = om.MFnMesh(selIt.getDagPath())
        fn = om.MFnDependencyNode(selIt.getDagPath().node())
        uuid = fn.uuid().asString()
        lockedVertices = set()
        for face in range(mesh.numPolygons):
            vertices = mesh.getPolygonVertices(face)
            normalIds = mesh.getFaceNormalIds(face)
            for i in range(len(vertices)):
                if mesh.isNormalLocked(normalIds[i]):
                    lockedVertices.add(vertices[i])
        if lockedVertices:
            lockedNormals[uuid] = sorted(lockedVertices)
        selIt.next()
    return "vertex", lockedNormals


def lamina(_, SLMesh):
    lamina = defaultdict(list)
    selIt = om.MItSelectionList(SLMesh)
    while not selIt.isDone():
        faceIt = om.MItMeshPolygon(selIt.getDagPath())
        fn = om.MFnDependencyNode(selIt.getDagPath().node())
        uuid = fn.uuid().asString()
        while not faceIt.isDone():
            laminaFaces = faceIt.isLamina()
            if laminaFaces is True:
                lamina[uuid].append(faceIt.index())
            try:
                faceIt.next(True)  # Try with argument first
            except TypeError:
                faceIt.next()  # If that fails, try without argument
        selIt.next()  # No argument for selection iterator
    return "polygon", lamina


def zeroAreaFaces(_, SLMesh):
    zeroAreaFaces = defaultdict(list)
    selIt = om.MItSelectionList(SLMesh)
    while not selIt.isDone():
        faceIt = om.MItMeshPolygon(selIt.getDagPath())
        fn = om.MFnDependencyNode(selIt.getDagPath().node())
        uuid = fn.uuid().asString()
        while not faceIt.isDone():
            faceArea = faceIt.getArea()
            if faceArea <= 0.00000001:
                zeroAreaFaces[uuid].append(faceIt.index())
            try:
                faceIt.next(True)  # Try with argument first
            except TypeError:
                faceIt.next()  # If that fails, try without argument
        selIt.next()  # No argument for selection iterator
    return "polygon", zeroAreaFaces


def zeroLengthEdges(_, SLMesh):
    zeroLengthEdges = defaultdict(list)
    selIt = om.MItSelectionList(SLMesh)
    while not selIt.isDone():
        edgeIt = om.MItMeshEdge(selIt.getDagPath())
        fn = om.MFnDependencyNode(selIt.getDagPath().node())
        uuid = fn.uuid().asString()
        while not edgeIt.isDone():
            if edgeIt.length() <= 0.00000001:
                zeroLengthEdges[uuid].append(edgeIt.index())
            edgeIt.next()
        selIt.next()
    return "edge", zeroLengthEdges

def selfPenetratingUVs(transformNodes, _):
    selfPenetratingUVs = defaultdict(list)
    for node in transformNodes:
        nodeName = _getNodeName(node)
        shapes = cmds.listRelatives(
            nodeName,
            shapes=True,
            type="mesh",
            noIntermediate=True)
        if shapes:
            overlapping = cmds.polyUVOverlap("{}.f[*]".format(shapes[0]), oc=True)
            if overlapping:
                formatted = [ overlap.split("{}.f[".format(shapes[0]))[1][:-1] for overlap in overlapping ]
                selfPenetratingUVs[node].extend(formatted)
    return "polygon", selfPenetratingUVs

def noneManifoldEdges(_, SLMesh):
    noneManifoldEdges = defaultdict(list)
    selIt = om.MItSelectionList(SLMesh)
    while not selIt.isDone():
        edgeIt = om.MItMeshEdge(selIt.getDagPath())
        fn = om.MFnDependencyNode(selIt.getDagPath().node())
        uuid = fn.uuid().asString()
        while not edgeIt.isDone():
            if edgeIt.numConnectedFaces() > 2:
                noneManifoldEdges[uuid].append(edgeIt.index())
            edgeIt.next()
        selIt.next()
    return "edge", noneManifoldEdges


def openBorder(_, SLMesh):
    # Everything Maya's edge "On Border" constraint treats as a border edge:
    #   * fewer than two connected faces -> classic open edges, plus unwelded /
    #     overlapping duplicate edges (each coincident edge carries a single
    #     face) and stray wire edges
    #   * exactly two faces wound the same way -> a flipped neighbour, which
    #     Maya draws and selects as a border even though the face count is 2
    # (Three or more faces is non-manifold, handled by noneManifoldEdges.)
    openBorder = defaultdict(list)
    selIt = om.MItSelectionList(SLMesh)
    while not selIt.isDone():
        dagPath = selIt.getDagPath()
        fn = om.MFnDependencyNode(dagPath.node())
        uuid = fn.uuid().asString()

        # Collect the directed traversal every incident face imposes on each
        # edge, keyed by the real edge id so coincident edges stay distinct.
        # getEdges()[i] is the edge spanning getVertices()[i] .. [i + 1].
        edgeDirections = defaultdict(list)
        faceIt = om.MItMeshPolygon(dagPath)
        while not faceIt.isDone():
            verts = faceIt.getVertices()
            edges = faceIt.getEdges()
            count = len(verts)
            for i in range(count):
                edgeDirections[edges[i]].append((verts[i], verts[(i + 1) % count]))
            try:
                faceIt.next(True)  # Try with argument first
            except TypeError:
                faceIt.next()  # If that fails, try without argument

        edgeIt = om.MItMeshEdge(dagPath)
        while not edgeIt.isDone():
            directions = edgeDirections.get(edgeIt.index(), [])
            # < 2 faces -> open / overlapping; exactly 2 faces traversed the
            # same way -> a flipped neighbour. Both read as a border in Maya.
            if len(directions) < 2:
                openBorder[uuid].append(edgeIt.index())
            elif len(directions) == 2 and directions[0] == directions[1]:
                openBorder[uuid].append(edgeIt.index())
            edgeIt.next()
        selIt.next()
    return "edge", openBorder


def poles(_, SLMesh):
    poles = defaultdict(list)
    selIt = om.MItSelectionList(SLMesh)
    while not selIt.isDone():
        vertexIt = om.MItMeshVertex(selIt.getDagPath())
        fn = om.MFnDependencyNode(selIt.getDagPath().node())
        uuid = fn.uuid().asString()
        while not vertexIt.isDone():
            if vertexIt.numConnectedEdges() > 5:
                poles[uuid].append(vertexIt.index())
            vertexIt.next()
        selIt.next()
    return "vertex", poles


def starlike(_, SLMesh):
    noneStarlike = defaultdict(list)
    selIt = om.MItSelectionList(SLMesh)
    while not selIt.isDone():
        polyIt = om.MItMeshPolygon(selIt.getDagPath())
        fn = om.MFnDependencyNode(selIt.getDagPath().node())
        uuid = fn.uuid().asString()
        while not polyIt.isDone():
            if polyIt.isStarlike() is False:
                noneStarlike[uuid].append(polyIt.index())
            try:
                polyIt.next(True)  # Try with argument first
            except TypeError:
                polyIt.next()  # If that fails, try without argument
        selIt.next()  # No argument for selection iterator
    return "polygon", noneStarlike


def missingUVs(_, SLMesh):
    missingUVs = defaultdict(list)
    selIt = om.MItSelectionList(SLMesh)
    while not selIt.isDone():
        faceIt = om.MItMeshPolygon(selIt.getDagPath())
        fn = om.MFnDependencyNode(selIt.getDagPath().node())
        uuid = fn.uuid().asString()
        while not faceIt.isDone():
            if faceIt.hasUVs() is False:
                missingUVs[uuid].append(faceIt.index())
            try:
                faceIt.next(True)  # Try with argument first
            except TypeError:
                faceIt.next()  # If that fails, try without argument
        selIt.next()  # No argument for selection iterator
    return "polygon", missingUVs

def uvRange(_, SLMesh):
    uvRange = defaultdict(list)
    selIt = om.MItSelectionList(SLMesh)
    while not selIt.isDone():
        mesh = om.MFnMesh(selIt.getDagPath())
        fn = om.MFnDependencyNode(selIt.getDagPath().node())
        uuid = fn.uuid().asString()
        Us, Vs = mesh.getUVs()
        for i in range(len(Us)):
            if Us[i] < 0 or Us[i] > 10 or Vs[i] < 0:
                uvRange[uuid].append(i)
        selIt.next()
    return "uv", uvRange

def onBorder(_, SLMesh):
    onBorder = defaultdict(list)
    selIt = om.MItSelectionList(SLMesh)
    while not selIt.isDone():
        mesh = om.MFnMesh(selIt.getDagPath())
        fn = om.MFnDependencyNode(selIt.getDagPath().node())
        uuid = fn.uuid().asString()
        Us, Vs = mesh.getUVs()
        for i in range(len(Us)):
            if abs(int(Us[i]) - Us[i]) < 0.00001 or abs(int(Vs[i]) - Vs[i]) < 0.00001:
                onBorder[uuid].append(i)
        selIt.next()
    return "uv", onBorder

def crossBorder(_, SLMesh):
    crossBorder = defaultdict(list)
    selIt = om.MItSelectionList(SLMesh)
    while not selIt.isDone():
        faceIt = om.MItMeshPolygon(selIt.getDagPath())
        fn = om.MFnDependencyNode(selIt.getDagPath().node())
        uuid = fn.uuid().asString()
        while not faceIt.isDone():
            U, V = set(), set()
            try:
                UVs = faceIt.getUVs()
                Us, Vs, = UVs[0], UVs[1]
                for i in range(len(Us)):
                    uAdd = int(Us[i]) if Us[i] > 0 else int(Us[i]) - 1
                    vAdd = int(Vs[i]) if Vs[i] > 0 else int(Vs[i]) - 1
                    U.add(uAdd)
                    V.add(vAdd)
                if len(U) > 1 or len(V) > 1:
                    crossBorder[uuid].append(faceIt.index())
                # Replace the iterator advancement with the try-except pattern
                try:
                    faceIt.next(True)
                except TypeError:
                    faceIt.next()
            except:
                cmds.warning("Face " + str(faceIt.index()) + " has no UVs")
                # Also replace the iterator advancement in the exception handler
                try:
                    faceIt.next(True)
                except TypeError:
                    faceIt.next()
        selIt.next()  # No argument for selection iterator
    return "polygon", crossBorder

def unfrozenTransforms(nodes, _):
    unfrozenTransforms = []
    for node in nodes:
        nodeName = _getNodeName(node)
        translation = cmds.xform(
            nodeName, q=True, worldSpace=True, translation=True)
        rotation = cmds.xform(nodeName, q=True, worldSpace=True, rotation=True)
        scale = cmds.xform(nodeName, q=True, worldSpace=True, scale=True)
        if translation != [0.0, 0.0, 0.0] or rotation != [0.0, 0.0, 0.0] or scale != [1.0, 1.0, 1.0]:
            unfrozenTransforms.append(node)
    return "nodes", unfrozenTransforms

def layers(nodes, _):
    layers = []
    for node in nodes:
        nodeName = _getNodeName(node)
        layer = cmds.listConnections(nodeName, type="displayLayer")
        if layer:
            layers.append(node)
    return "nodes", layers

def shaders(transformNodes, _):
    shaders = []
    for node in transformNodes:
        nodeName = _getNodeName(node)
        shape = cmds.listRelatives(nodeName, shapes=True, fullPath=True)
        if shape and cmds.nodeType(shape) == 'mesh':
            shadingGrps = cmds.listConnections(shape, type='shadingEngine')
            if shadingGrps[0] != 'initialShadingGroup':
                shaders.append(node)
    return "nodes", shaders

def generalHistory(nodes, _):
    # Not listHistory: that also returns the groupIds of per-face materials,
    # which stay after Delete History, and every shape when there are several
    generalHistory = []
    for node in nodes:
        nodeName = _getNodeName(node)
        if not nodeName:
            continue
        shapes = cmds.listRelatives(nodeName, shapes=True, type="mesh",
                                    noIntermediate=True, fullPath=True) or []
        if any(_meshHistoryNode(shape) for shape in shapes):
            generalHistory.append(node)
    return "nodes", generalHistory

def uncenteredPivots(nodes, _):
    uncenteredPivots = []
    for node in nodes:
        nodeName = _getNodeName(node)
        if cmds.xform(nodeName, q=1, ws=1, rp=1) != [0, 0, 0]:
            uncenteredPivots.append(node)
    return "nodes", uncenteredPivots

def emptyGroups(nodes, _):
    emptyGroups = []
    for node in nodes:
        nodeName = _getNodeName(node)
        if not cmds.listRelatives(nodeName, ad=True):
            emptyGroups.append(node)
    return "nodes", emptyGroups

def _checkSymmetry(_, SLMesh, axis='X'):
    """
    Generic symmetry checking function.
    
    Args:
        axis (str): 'X' to check symmetry across YZ plane, 'Y' to check symmetry across XZ plane
    """
    nonSymmetrical = defaultdict(list)
    tolerance = 0.175  # Increased tolerance for floating point comparison
    
    selIt = om.MItSelectionList(SLMesh)
    while not selIt.isDone():
        faceIt = om.MItMeshPolygon(selIt.getDagPath())
        fn = om.MFnDependencyNode(selIt.getDagPath().node())
        uuid = fn.uuid().asString()
        
        # Dictionary to store face centers grouped by their position on the two other axes
        faceCenters = {}
        faceIndices = {}
        
        # Don't reset iterator - remove this line that might be causing issues
        # faceIt.reset()  # REMOVED
        while not faceIt.isDone():
            # Get face center
            center = faceIt.center(om.MSpace.kWorld)
            faceIndex = faceIt.index()
            
            # Define which coordinates to use based on the symmetry axis
            if axis.upper() == 'X':
                # For X symmetry, group by Y and Z, check X positions
                # Add rounding to improve precision
                coord1_rounded = round(center.y / tolerance) * tolerance
                coord2_rounded = round(center.z / tolerance) * tolerance
                symmetry_coord = round(center.x, 4)  # Round the symmetry coordinate
            elif axis.upper() == 'Y':
                # For Y symmetry, group by X and Z, check Y positions
                # Add rounding to improve precision
                coord1_rounded = round(center.x / tolerance) * tolerance
                coord2_rounded = round(center.z / tolerance) * tolerance
                symmetry_coord = round(center.y, 4)  # Round the symmetry coordinate
            else:
                cmds.warning("Invalid axis '{}'. Use 'X' or 'Y'.".format(axis))
                return "polygon", nonSymmetrical
            
            key = (coord1_rounded, coord2_rounded)
            
            if key not in faceCenters:
                faceCenters[key] = []
                faceIndices[key] = []
            
            faceCenters[key].append(symmetry_coord)
            faceIndices[key].append(faceIndex)
            
            try:
                faceIt.next(True)
            except TypeError:
                faceIt.next()
        
        # Check for symmetry in each group
        for key, positions in faceCenters.items():
            indices = faceIndices[key]
            
            # If there's only one face at this position, it should be on the centerline (coord=0)
            if len(positions) == 1:
                if abs(positions[0]) > tolerance:
                    nonSymmetrical[uuid].append(indices[0])
            else:
                # For multiple faces, check if they form symmetric pairs
                positions_sorted = sorted(zip(positions, indices))
                unpaired_faces = []
                
                i = 0
                while i < len(positions_sorted):
                    pos, face_idx = positions_sorted[i]
                    
                    # Check if this face is on the centerline
                    if abs(pos) <= tolerance:
                        i += 1
                        continue
                    
                    # Look for its symmetric counterpart
                    found_pair = False
                    for j in range(i + 1, len(positions_sorted)):
                        other_pos, other_idx = positions_sorted[j]
                        if abs(pos + other_pos) <= tolerance:  # Symmetric positions
                            found_pair = True
                            # Remove the paired face from further consideration
                            positions_sorted.pop(j)
                            break
                    
                    if not found_pair:
                        unpaired_faces.append(face_idx)
                    
                    i += 1
                
                # Add any remaining unpaired faces as non-symmetrical
                nonSymmetrical[uuid].extend(unpaired_faces)
        
        selIt.next()
    
    return "polygon", nonSymmetrical


def symmetryX(nodes, SLMesh):
    """Check for X-axis symmetry by comparing polygon positions across the YZ plane."""
    return _checkSymmetry(nodes, SLMesh, 'X')


def symmetryY(nodes, SLMesh):
    """Check for Y-axis symmetry by comparing polygon positions across the XZ plane."""
    return _checkSymmetry(nodes, SLMesh, 'Y')

def parentGeometry(transformNodes, _):
    parentGeometry = []
    for node in transformNodes:
        nodeName = _getNodeName(node)
        parents = cmds.listRelatives(nodeName, p=True, fullPath=True)
        if parents:
            for parent in parents:
                children = cmds.listRelatives(parent, fullPath=True)
                for child in children:
                    if cmds.nodeType(child) == 'mesh':
                        parentGeometry.append(node)
    return "nodes", parentGeometry


def freezeTransforms(nodes, _):
    """Freeze transformations on specified nodes."""
    affected_nodes = []
    original_selection = cmds.ls(selection=True) or []
    
    try:
        for node in nodes:
            try:
                nodeName = _getNodeName(node)
                if nodeName:
                    # Select the node and apply freeze transforms
                    cmds.select(nodeName, replace=True)
                    cmds.makeIdentity(apply=True, t=1, r=1, s=1, n=0, pn=1)
                    affected_nodes.append(node)
            except Exception as e:
                cmds.warning("Failed to freeze transforms on {}: {}".format(node, str(e)))
    finally:
        # Restore original selection
        if original_selection:
            cmds.select(original_selection, replace=True)
        else:
            cmds.select(clear=True)
            
    return "nodes", affected_nodes
    
def mergeIdenticalVertices(nodes, _):
    """Merge vertices with extremely low distance tolerance."""
    affected_nodes = []
    original_selection = cmds.ls(selection=True) or []
    
    try:
        for node in nodes:
            try:
                nodeName = _getNodeName(node)
                if nodeName:
                    # Select the node and apply the merge operation
                    cmds.select(nodeName, replace=True)
                    cmds.polyMergeVertex(distance=0.0001)
                    affected_nodes.append(node)
            except Exception as e:
                cmds.warning("Failed to merge vertices on {}: {}".format(node, str(e)))
    finally:
        # Restore original selection
        if original_selection:
            cmds.select(original_selection, replace=True)
        else:
            cmds.select(clear=True)
            
    return "nodes", affected_nodes

def centerPivots(nodes, _):
    """Center pivots on specified nodes."""
    affected_nodes = []
    for node in nodes:
        nodeName = _getNodeName(node)
        if nodeName:
            try:
                cmds.xform(nodeName, centerPivots=True)
                affected_nodes.append(node)
            except:
                cmds.warning("Failed to center pivots on {}".format(nodeName))
    return "nodes", affected_nodes

def fixLaminaFaces(nodes, _):
    """Delete lamina faces on the specified nodes."""
    affected_nodes = []
    original_selection = cmds.ls(selection=True) or []
    
    try:
        for node in nodes:
            nodeName = _getNodeName(node)
            if nodeName:
                # Use Maya's built-in polyInfo command to find lamina faces
                lamina_faces = cmds.polyInfo(nodeName, laminaFaces=True) or []
                
                # If lamina faces were found, delete them
                if lamina_faces:
                    try:
                        cmds.delete(lamina_faces)
                        affected_nodes.append(node)
                    except Exception as e:
                        cmds.warning("Failed to delete lamina faces on {}: {}".format(nodeName, str(e)))
    finally:
        # Restore original selection
        if original_selection:
            cmds.select(original_selection, replace=True)
        else:
            cmds.select(clear=True)
            
    return "nodes", affected_nodes


def deleteHistory(nodes, _):
    """Delete history on the given nodes, reporting only the ones that had any."""
    affected_nodes = []
    for node in nodes:
        nodeName = _getNodeName(node)
        if not nodeName:
            continue
        try:
            before = len(cmds.listHistory(nodeName) or [])
            cmds.delete(nodeName, constructionHistory=True)
            if len(cmds.listHistory(nodeName) or []) < before:
                affected_nodes.append(node)
        except Exception as e:
            cmds.warning("Failed to delete history on {}: {}".format(nodeName, str(e)))
    return "nodes", affected_nodes


def deleteDisplayLayers(nodes, _):
    """Delete every display layer except the default one.

    Deleted layers no longer exist as nodes, so they are reported by name via
    the "custom" result type rather than pretending a scene object changed.
    """
    deleted = []
    try:
        layers = [layer for layer in (cmds.ls(type="displayLayer") or [])
                  if layer != "defaultLayer"]
        for layer in layers:
            try:
                cmds.delete(layer)
                deleted.append(layer)
            except Exception as e:
                cmds.warning("Failed to delete layer {}: {}".format(layer, str(e)))
    except Exception as e:
        cmds.warning("Failed to delete display layers: {}".format(str(e)))
    return "custom", deleted


def deleteCameras(nodes, _):
    """Delete every camera in the scene except the default four."""
    deleted = []
    default_cameras = ["frontShape", "perspShape", "sideShape", "topShape"]

    # The transform is what has to go, not the camera shape
    camera_transforms = []
    for cam in cmds.ls(type="camera", long=True) or []:
        if any(cam.endswith(default) for default in default_cameras):
            continue
        parent = cmds.listRelatives(cam, parent=True, fullPath=True)
        if parent:
            camera_transforms.append(parent[0])

    for cam in camera_transforms:
        try:
            cmds.delete(cam)
            deleted.append(cam)
        except Exception as e:
            cmds.warning("Failed to delete camera {}: {}".format(cam, str(e)))
    return "custom", deleted


def deleteColorSets(nodes, _):
    """Delete colour sets from meshes, reporting only the sets actually removed."""
    deleted = []
    for node in nodes:
        nodeName = _getNodeName(node)
        if not nodeName:
            continue
        shapes = cmds.listRelatives(nodeName, shapes=True, type="mesh")
        if not shapes:
            continue
        try:
            colorSets = cmds.polyColorSet(
                shapes[0], query=True, allColorSets=True) or []
            for colorSet in colorSets:
                cmds.polyColorSet(shapes[0], delete=True, colorSet=colorSet)
                deleted.append("{}.{}".format(nodeName, colorSet))
        except Exception as e:
            cmds.warning("Failed to process color sets on {}: {}".format(
                nodeName, str(e)))
    return "custom", deleted


def deleteUnusedMaterials(nodes, _):
    """Delete unused materials, always scene-wide - unused is a scene-level idea."""
    deleted = []
    default_materials = ["lambert1", "particleCloud1", "shaderGlow1",
                         "initialParticleSE"]
    try:
        shadingEngines = [sg for sg in (cmds.ls(type="shadingEngine") or [])
                          if sg != "initialShadingGroup"]

        unusedMaterials = []
        for sg in shadingEngines:
            # A shading engine with no members is not shading anything
            if cmds.sets(sg, query=True):
                continue
            connections = cmds.listConnections(
                sg + ".surfaceShader", source=True, destination=False) or []
            for material in connections:
                if material not in default_materials and material not in unusedMaterials:
                    unusedMaterials.append(material)

        for material in unusedMaterials:
            try:
                cmds.delete(material)
                deleted.append(material)
            except Exception as e:
                cmds.warning("Failed to delete material {}: {}".format(
                    material, str(e)))
    except Exception as e:
        cmds.warning("Failed to delete unused materials: {}".format(str(e)))
    return "custom", deleted


def deleteInputDataNodes(nodes, _):
    """Delete blind data / metadata nodes from the input history of the given nodes."""
    affected_nodes = []

    # cmds.ls() raises on an unregistered type, and not every type ships with
    # every Maya version, so only ask for the ones this session knows about.
    knownTypes = set(cmds.allNodeTypes())
    dataTypes = [typ for typ in INPUT_DATA_NODE_TYPES if typ in knownTypes]
    if not dataTypes:
        cmds.warning("None of the input data node types exist in this Maya version.")
        return "nodes", affected_nodes

    found = {}
    for node in nodes:
        nodeName = _getNodeName(node)
        if not nodeName:
            continue
        try:
            # The transform's history reaches through to its shape's inputs
            history = cmds.listHistory(nodeName) or []
            dataNodes = cmds.ls(history, type=dataTypes) or []
            if dataNodes:
                found[node] = dataNodes
        except Exception as e:
            cmds.warning("Failed to collect input data nodes on {}: {}".format(
                nodeName, str(e)))

    if not found:
        return "nodes", affected_nodes

    toDelete = set()
    for dataNodes in found.values():
        toDelete.update(dataNodes)

    for dataNode in sorted(toDelete):
        if not cmds.objExists(dataNode):
            continue
        try:
            cmds.lockNode(dataNode, lock=False)
        except Exception:
            pass
        try:
            cmds.delete(dataNode)
        except Exception as e:
            cmds.warning("Failed to delete input data node {}: {}".format(
                dataNode, str(e)))

    # Templates are standalone scene-level nodes with no connections at all, so
    # they can only be reached once the data that used them is gone
    _deleteOrphanedBlindDataTemplates()

    # Report only the objects that really did lose a data node
    for node, dataNodes in found.items():
        if any(not cmds.objExists(dataNode) for dataNode in dataNodes):
            affected_nodes.append(node)

    return "nodes", affected_nodes


# Cleanup. Each step is split in two: a find that only looks, and a fix that
# changes what the find returned. Scene Cleanup runs the finds alone, so the
# check reports exactly what the Cleanup button would change.
def _localNodes(*args, **flags):
    """cmds.ls() as long names, minus anything that belongs to a reference."""
    return [node for node in cmds.ls(*args, long=True, **flags) or []
            if not cmds.referenceQuery(node, isNodeReferenced=True)]


def _forceDelete(node):
    """Delete `node`, unlocking it first. Returns 1 if it went, for adding up."""
    try:
        cmds.lockNode(node, lock=False)
        cmds.delete(node)
    except (RuntimeError, ValueError):
        return 0
    return 1


def _deleteNodes(nodes):
    """Delete each of `nodes` still in the scene. Returns how many went."""
    return sum(_forceDelete(node) for node in nodes if cmds.objExists(node))


def _customAttributes(node):
    """The attributes added to `node`, as plugs. A compound's children are left
    out, since they go along with their parent."""
    plugs = []
    for attr in cmds.listAttr(node, userDefined=True) or []:
        plug = "{}.{}".format(node, attr)
        if (attr in MAYA_ATTRIBUTES or "." in attr or not cmds.objExists(plug)
                or cmds.attributeQuery(attr, node=node, listParent=True)):
            continue
        plugs.append(plug)
    return plugs


def _deleteAttributes(plugs):
    """Delete the attribute behind each plug. Returns how many went."""
    removed = 0
    for plug in plugs:
        try:
            cmds.setAttr(plug, lock=False)
            cmds.deleteAttr(plug)
            removed += 1
        except RuntimeError as e:
            cmds.warning("Could not remove {}: {}".format(plug, str(e)))
    return removed


def _findNamespaces():
    """Namespaces that are not Maya's, children before their parents. One that
    holds a referenced node is kept, since the reference needs it."""
    found = []

    def visit(namespace):
        for child in cmds.namespaceInfo(namespace, listOnlyNamespaces=True) or []:
            visit(child)
        contents = cmds.namespaceInfo(
            namespace, listOnlyDependencyNodes=True, dagPath=True) or []
        if not any(cmds.referenceQuery(node, isNodeReferenced=True) for node in contents):
            found.append(namespace)

    for namespace in cmds.namespaceInfo(":", listOnlyNamespaces=True) or []:
        if namespace not in DEFAULT_NAMESPACES:
            visit(namespace)
    return found


def _fixNamespaces(namespaces):
    """Empty each namespace into the root, then remove it."""
    cmds.namespace(setNamespace=":")
    removed = 0
    for namespace in namespaces:
        try:
            cmds.namespace(moveNamespace=(namespace, ":"), force=True)
            cmds.namespace(removeNamespace=namespace)
            removed += 1
        except RuntimeError as e:
            cmds.warning("Could not remove namespace {}: {}".format(namespace, str(e)))
    return removed


def _findDefaultMaterial():
    """lambert1's colour if it is not plain mid grey, and any custom attributes."""
    if not cmds.objExists("lambert1.color"):
        return []
    changes = []
    color = cmds.getAttr("lambert1.color")[0]
    if (any(abs(channel - 0.5) > 0.001 for channel in color)
            and not cmds.listConnections("lambert1.color", source=True, destination=False)):
        changes.append("lambert1.color")
    return changes + _customAttributes("lambert1")


def _fixDefaultMaterial(plugs):
    changed = 0
    if "lambert1.color" in plugs:
        cmds.setAttr("lambert1.color", 0.5, 0.5, 0.5, type="float3")
        changed += 1
    return changed + _deleteAttributes([plug for plug in plugs if plug != "lambert1.color"])


def _findEmptyLayers():
    return [layer for layer in _localNodes(type="displayLayer")
            if layer != "defaultLayer" and not cmds.editDisplayLayerMembers(layer, query=True)]


def _findHiddenSets(multiAttr, nameAttr):
    """UV or colour sets with no name, which Maya's UI cannot show, as plugs."""
    plugs = []
    for mesh in _localNodes(type="mesh"):
        for plug in cmds.ls("{}.{}[*]".format(mesh, multiAttr), flatten=True) or []:
            if not cmds.getAttr("{}.{}".format(plug, nameAttr)):
                plugs.append(plug)
    return plugs


def _findHiddenUVSets():
    return _findHiddenSets("uvst", "uvsn")


def _findHiddenColorSets():
    return _findHiddenSets("clst", "clsn")


def _fixHiddenSets(plugs):
    for plug in plugs:
        cmds.removeMultiInstance(plug, b=True)
    return len(plugs)


def _findCustomAttributes():
    """Every object in the scene, shapes included. FBX leftovers land here too."""
    plugs = []
    for node in _localNodes(dag=True):
        plugs.extend(_customAttributes(node))
    return plugs


def _findPastedNames():
    """Names with "pasted__", children first so parent paths stay valid."""
    nodes = _localNodes("*pasted__*", recursive=True)
    return sorted(nodes, key=lambda name: name.count("|"), reverse=True)


def _fixPastedNames(nodes):
    renamed = 0
    for node in nodes:
        newName = node.rsplit("|", 1)[-1].replace("pasted__", "")
        try:
            if newName:
                cmds.rename(node, newName)
                renamed += 1
        except RuntimeError:
            pass
    return renamed


def _findBrokenReferences():
    """Reference nodes tied to no file. An unloaded reference still has one."""
    broken = []
    for reference in cmds.ls(type="reference") or []:
        if reference.endswith("sharedReferenceNode"):
            continue
        try:
            cmds.referenceQuery(reference, filename=True)
        except RuntimeError:
            broken.append(reference)
    return broken


def _findHistory():
    """Meshes with history the bake would remove: the same test as the History check."""
    return [mesh for mesh in _localNodes(type="mesh", noIntermediate=True)
            if _meshHistoryNode(mesh)]


def _fixHistory(meshes):
    """Bake history, keeping deformers so rigged meshes still work."""
    baked = 0
    for mesh in meshes:
        try:
            cmds.bakePartialHistory(mesh, prePostDeformers=True)
        except RuntimeError as e:
            cmds.warning("Could not bake history on {}: {}".format(mesh, str(e)))
            continue
        if not _meshHistoryNode(mesh):
            baked += 1
    return baked


def _findLeftoverNodes():
    # cmds.ls() raises on an unregistered type, so only ask for ones this session has
    known = set(cmds.allNodeTypes())
    found = []

    # Bookkeeping nodes a model has no use for, unless a USD stage is in the scene
    bookkeeping = ["trackInfoManager"]
    if "mayaUsdLayerManager" in known and not cmds.ls(type="mayaUsdProxyShape"):
        bookkeeping.append("mayaUsdLayerManager")
    for nodeType in bookkeeping:
        if nodeType in known:
            found.extend(_localNodes(type=nodeType))

    for nodeType in DISCONNECTED_NODE_TYPES:
        if nodeType in known:
            found.extend(node for node in _localNodes(type=nodeType)
                         if not cmds.listConnections(node))

    return found + _orphanedBlindDataTemplates()


def _findHiddenMaterials():
    """Materials in use but missing from this list do not show in the Hypershade."""
    materialTypes = cmds.listNodeTypes("shader/surface") or []
    if not materialTypes:
        return []
    return [material for material in _localNodes(type=materialTypes)
            if cmds.listConnections(material, type="shadingEngine")
            and not cmds.listConnections(material, type="defaultShaderList")]


def _fixHiddenMaterials(materials):
    for material in materials:
        cmds.connectAttr(material + ".msg", "defaultShaderList1.s", nextAvailable=True)
    return len(materials)


def _meshDisplayChanges(mesh):
    """`mesh`'s display options away from Maya's defaults, as (plug, default)."""
    changes = []
    for attr, default in MESH_DISPLAY_DEFAULTS:
        plug = "{}.{}".format(mesh, attr)
        try:
            if cmds.getAttr(plug) != default:
                changes.append((plug, default))
        except (RuntimeError, ValueError):
            pass
    return changes


def _findMeshDisplay():
    return [mesh for mesh in _localNodes(type="mesh") if _meshDisplayChanges(mesh)]


def _fixMeshDisplay(meshes):
    changed = 0
    for mesh in meshes:
        meshChanged = False
        for plug, default in _meshDisplayChanges(mesh):
            try:
                cmds.setAttr(plug, default)
                meshChanged = True
            except (RuntimeError, ValueError):
                pass
        changed += meshChanged
    return changed


def _deletableNode(node, defaultNodes):
    """What MLdeleteUnused's deleteIfNotReferenced would agree to delete."""
    return (node not in defaultNodes and cmds.objExists(node)
            and not cmds.referenceQuery(node, isNodeReferenced=True)
            and not cmds.lockNode(node, query=True, lock=True)[0])


def _deletionPrevented(node, connection, source):
    """Whether a plug-in, such as a renderer, asks Delete Unused Nodes to keep
    `node` because of this one connection."""
    try:
        answers = cmds.callbacks(
            node, connection, source, executeCallbacks=True,
            hook="preventMaterialDeletionFromCleanUpSceneCommand") or []
    except RuntimeError:
        return False
    return any(answers)


def _keepsRenderNode(node, connection, source):
    """Whether one outgoing connection of a texture or utility node is a use,
    as stage 3 of MLdeleteUnused.mel decides it."""
    if not source.endswith(".message"):
        return True
    nodeType = cmds.nodeType(connection)
    if nodeType in RENDER_NODE_USERS or cmds.objectType(connection, isAType="camera"):
        return True
    if any(cmds.getClassification(nodeType, satisfies=classification)
           for classification in ("shader/surface", "shader/volume", "shader/displacement")):
        return True
    return _deletionPrevented(node, connection, source)


def _findUnusedNodes():
    """What Maya's Delete Unused Nodes would remove on its first pass, without
    removing it.

    Mirrors the three stages of MLdeleteUnused.mel. Its later passes only reach
    nodes that these deletions free up, so if this finds nothing, neither will it.
    """
    mel.eval('if (!`exists shadingGroupUnused`) source "MLdeleteUnused.mel";')
    defaultNodes = set(cmds.ls(defaultNodes=True) or [])
    found = []

    # Stage 1: shading groups with no members, or no shader
    for shadingGroup in cmds.ls(sets=True) or []:
        if not (mel.eval('shadingGroupUnused("{}")'.format(shadingGroup))
                and _deletableNode(shadingGroup, defaultNodes)):
            continue
        outputs = cmds.listConnections(shadingGroup, connections=True, source=False,
                                       shapes=True) or []
        if not any(_deletionPrevented(shadingGroup, connection, source)
                   for source, connection in zip(outputs[0::2], outputs[1::2])):
            found.append(shadingGroup)

    # Stage 2: materials whose only outputs are message links to no shading group
    for material in cmds.ls(long=True, materials=True) or []:
        if not _deletableNode(material, defaultNodes):
            continue
        outputs = cmds.listConnections(material, connections=True, source=False,
                                       shapes=True) or []
        if outputs and all(
                source == material + ".message"
                and not cmds.listConnections(source, type="shadingEngine")
                and not _deletionPrevented(material, connection, source)
                for source, connection in zip(outputs[0::2], outputs[1::2])):
            found.append(material)

    # Stage 3: textures and utilities with no output that uses them
    renderTypes = []
    for classification in ("texture", "utility", "math", "imageplane", "shader"):
        renderTypes.extend(cmds.listNodeTypes(classification) or [])
    for node in (cmds.ls(long=True, type=renderTypes) or []) if renderTypes else []:
        if node in found or not _deletableNode(node, defaultNodes):
            continue
        nodeType = cmds.nodeType(node)
        if nodeType == "heightField" and cmds.listConnections(node, source=True, destination=False):
            continue
        if nodeType == "imagePlane" and not cmds.getAttr(node + ".lockedToCamera"):
            continue
        outputs = cmds.listConnections(node, connections=True, source=False, shapes=True) or []
        if not any(_keepsRenderNode(node, connection, source)
                   for source, connection in zip(outputs[0::2], outputs[1::2])):
            found.append(node)
    return found


def _fixUnusedNodes(_):
    """Maya's own Delete Unused Nodes, which leaves referenced nodes alone. It
    runs whatever the find said, as the Cleanup always has."""
    return mel.eval("MLdeleteUnused();")


def _findEmptySets():
    """Empty object sets, apart from the ones Maya or a deformer relies on."""
    found = []
    defaultNodes = set(cmds.ls(defaultNodes=True) or [])
    for objectSet in _localNodes(exactType="objectSet"):
        if (objectSet in defaultNodes or "ViewSelectedSet" in objectSet
                or "textureEditor" in objectSet):
            continue
        if not cmds.sets(objectSet, query=True) and not cmds.listConnections(objectSet + ".usedBy"):
            found.append(objectSet)
    return found


def _defaultCameraChanges(camera, orthographic):
    """View changes left on one of the default cameras, as (plug, value).

    Clip planes and focal length are not counted, since those suit the scene.
    """
    transform = "|" + camera
    shapes = (cmds.listRelatives(transform, shapes=True, fullPath=True)
              if cmds.objExists(transform) else None)
    if not shapes:
        return []
    return [(plug, value) for plug, value in (
                (transform + ".visibility", False),
                (shapes[0] + ".orthographic", orthographic),
                (shapes[0] + ".cameraScale", 1),
                (shapes[0] + ".panZoomEnabled", False))
            if cmds.getAttr(plug) != value]


def _findDefaultCameras():
    return [(camera, orthographic) for camera, orthographic in DEFAULT_CAMERAS
            if _defaultCameraChanges(camera, orthographic)]


def _fixDefaultCameras(cameras):
    """Hide the default cameras and undo view changes left on them."""
    for camera, orthographic in cameras:
        for plug, value in _defaultCameraChanges(camera, orthographic):
            cmds.setAttr(plug, lock=False)
            cmds.setAttr(plug, value)
    return len(cameras)


# (what Scene Cleanup reports, what Cleanup reports, find, fix)
CLEANUP_STEPS = (
    ("Namespaces", "Namespaces removed", _findNamespaces, _fixNamespaces),
    ("Default material changes", "Default material settings reset",
     _findDefaultMaterial, _fixDefaultMaterial),
    ("Empty display layers", "Empty display layers removed", _findEmptyLayers, _deleteNodes),
    ("Hidden UV sets", "Hidden UV sets removed", _findHiddenUVSets, _fixHiddenSets),
    ("Hidden color sets", "Hidden color sets removed", _findHiddenColorSets, _fixHiddenSets),
    ("Custom attributes", "Custom attributes removed", _findCustomAttributes, _deleteAttributes),
    ("Pasted prefixes", "Pasted prefixes removed", _findPastedNames, _fixPastedNames),
    ("Broken reference nodes", "Broken reference nodes removed",
     _findBrokenReferences, _deleteNodes),
    ("Meshes with history", "Meshes with history baked", _findHistory, _fixHistory),
    ("Leftover nodes", "Leftover nodes removed", _findLeftoverNodes, _deleteNodes),
    ("Hidden materials", "Hidden materials restored", _findHiddenMaterials, _fixHiddenMaterials),
    ("Meshes with display changes", "Meshes with display reset", _findMeshDisplay, _fixMeshDisplay),
    ("Unused rendering nodes", "Unused rendering nodes removed", _findUnusedNodes, _fixUnusedNodes),
    ("Empty sets", "Empty sets removed", _findEmptySets, _deleteNodes),
    ("Changed default cameras", "Default cameras reset", _findDefaultCameras, _fixDefaultCameras),
)


def cleanup(nodes, _):
    """Tidy the whole scene, whatever project it belongs to.

    Referenced nodes are left alone. A step that fails is reported, and the rest
    still run.
    """
    report = []
    for _, label, find, fix in CLEANUP_STEPS:
        try:
            count = fix(find())
        except Exception as e:
            traceback.print_exc()
            cmds.warning("Cleanup step failed ({}): {}".format(label, str(e)))
            report.append("{}: failed, see the Script Editor".format(label))
            continue
        if count:
            report.append("{}: {}".format(label, count))
    return "custom", report


def sceneCleanup(nodes, _):
    """The check for Cleanup: what it would change in the whole scene, changing
    nothing. An empty report is a pass."""
    report = []
    for label, _, find, _ in CLEANUP_STEPS:
        try:
            count = len(find())
        except Exception as e:
            traceback.print_exc()
            cmds.warning("Scene Cleanup check failed ({}): {}".format(label, str(e)))
            report.append("{}: could not check, see the Script Editor".format(label))
            continue
        if count:
            report.append("{}: {}".format(label, count))
    return "custom", report
