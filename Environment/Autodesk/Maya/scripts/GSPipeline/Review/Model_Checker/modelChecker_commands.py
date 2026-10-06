from collections import defaultdict
import sys

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

# Internal Utility Functions
def _getNodeName(uuid):
    nodeName = cmds.ls(uuid, uuid=True)
    if nodeName:
        return nodeName[0]
    return None


def _deleteOrphanedBlindDataTemplates():
    """Delete blindDataTemplate nodes whose typeId nothing in the scene uses."""
    templates = cmds.ls(type="blindDataTemplate") or []
    if not templates:
        return

    usedIds = set()
    for typ in ("polyBlindData", "subdBlindData"):
        for user in cmds.ls(type=typ) or []:
            try:
                usedIds.add(cmds.getAttr(user + ".typeId"))
            except Exception:
                pass

    for template in templates:
        try:
            if cmds.getAttr(template + ".typeId") in usedIds:
                continue
        except Exception:
            continue
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
    generalHistory = []
    for node in nodes:
        nodeName = _getNodeName(node)
        shape = cmds.listRelatives(nodeName, shapes=True, fullPath=True)
        if shape and cmds.nodeType(shape[0]) == 'mesh':
            historySize = len(cmds.listHistory(shape))
            if historySize > 1:
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

def reverseNormals(nodes, _):
    """Reverse normals on the specified nodes."""
    affected_nodes = []
    original_selection = cmds.ls(selection=True) or []
    
    try:
        for node in nodes:
            nodeName = _getNodeName(node)
            if nodeName:
                try:
                    # Select the node and perform normal reversal
                    cmds.select(nodeName, replace=True)
                    mel.eval('performPolyNormal 0 -1 0')
                    affected_nodes.append(node)
                    cmds.warning("Reversed normals on {}".format(nodeName))
                except Exception as e:
                    cmds.warning("Failed to reverse normals on {}: {}".format(nodeName, str(e)))
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
