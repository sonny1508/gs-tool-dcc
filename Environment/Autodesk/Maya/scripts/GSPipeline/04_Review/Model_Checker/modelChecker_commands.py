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

# Internal Utility Functions
def _getNodeName(uuid):
    nodeName = cmds.ls(uuid, uuid=True)
    if nodeName:
        return nodeName[0]
    return None


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


def openEdges(_, SLMesh):
    openEdges = defaultdict(list)
    selIt = om.MItSelectionList(SLMesh)
    while not selIt.isDone():
        edgeIt = om.MItMeshEdge(selIt.getDagPath())
        fn = om.MFnDependencyNode(selIt.getDagPath().node())
        uuid = fn.uuid().asString()
        while not edgeIt.isDone():
            if edgeIt.numConnectedFaces() < 2:
                openEdges[uuid].append(edgeIt.index())
            edgeIt.next()
        selIt.next()
    return "edge", openEdges


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
    """Delete history on the specified nodes."""
    affected_nodes = []
    for node in nodes:
        nodeName = _getNodeName(node)
        if nodeName:
            try:
                cmds.delete(nodeName, constructionHistory=True)
                affected_nodes.append(node)
            except Exception as e:
                cmds.warning("Failed to delete history on {}: {}".format(nodeName, str(e)))
    return "nodes", affected_nodes

def deleteDisplayLayers(nodes, _):
    """Delete all display layers except the default layer."""
    affected_nodes = []
    try:
        # Get all display layers
        displayLayers = cmds.ls(type="displayLayer")
        non_default_layers = [layer for layer in displayLayers if layer != "defaultLayer"]
        
        # If no non-default layers, report success
        if not non_default_layers:
            cmds.warning("No extra display layers in the scene!")
            if nodes:
                affected_nodes.append(nodes[0])
            return "nodes", affected_nodes
        
        # Delete any non-default layers found
        for layer in non_default_layers:
            try:
                cmds.delete(layer)
                # If at least one node is provided, use it for reporting success
                if nodes and not affected_nodes:
                    affected_nodes.append(nodes[0])
            except Exception as e:
                cmds.warning("Failed to delete layer {}: {}".format(layer, str(e)))
            
    except Exception as e:
        cmds.warning("Failed to delete display layers: {}".format(str(e)))
    return "nodes", affected_nodes

def deleteCameras(nodes, _):
    """Delete all cameras in the scene except default ones."""
    # Simply return success with at least one affected node
    if not nodes:
        cmds.warning("No nodes provided to deleteCameras")
        return "nodes", []
    
    # First, find all cameras in the scene
    all_cameras = cmds.ls(type="camera", long=True)
    default_cameras = ["frontShape", "perspShape", "sideShape", "topShape"]
    
    # Get their transform nodes (parents) - these are what we need to delete
    camera_transforms = []
    for cam in all_cameras:
        if not any(cam.endswith(default) for default in default_cameras):
            parent = cmds.listRelatives(cam, parent=True, fullPath=True)
            if parent:
                camera_transforms.append(parent[0])
    
    # If no cameras to delete, report success
    if not camera_transforms:
        cmds.warning("No extra cameras in the scene!")
        # Always return the first node to show green
        return "nodes", [nodes[0]]
    
    # Delete non-default camera transforms
    deleted_successfully = False
    for cam in camera_transforms:
        try:
            cmds.delete(cam)
            cmds.warning("Deleted camera: {}".format(cam))
            deleted_successfully = True
        except Exception as e:
            cmds.warning("Failed to delete camera {}: {}".format(cam, str(e)))
    
    # Return success ONLY if we actually deleted something or if there was nothing to delete
    if deleted_successfully:
        return "nodes", [nodes[0]]  # Success - return first node to show green
    else:
        return "nodes", []  # Nothing was deleted successfully - show red

def deleteColorSets(nodes, _):
    """Delete color sets from meshes."""
    affected_nodes = []
    for node in nodes:
        nodeName = _getNodeName(node)
        if nodeName:
            shapes = cmds.listRelatives(nodeName, shapes=True, type="mesh")
            if shapes:
                try:
                    # Get color sets on the mesh - handle None return with or []
                    colorSets = cmds.polyColorSet(shapes[0], query=True, allColorSets=True) or []
                    
                    # If there are color sets, delete them
                    if colorSets:
                        for colorSet in colorSets:
                            cmds.polyColorSet(shapes[0], delete=True, colorSet=colorSet)

                    # (We're considering "no color sets" as a successful state)
                    affected_nodes.append(node)
                    
                except Exception as e:
                    cmds.warning("Failed to process color sets on {}: {}".format(nodeName, str(e)))
    return "nodes", affected_nodes

def deleteUnusedMaterials(nodes, _):
    """Delete unused materials in the scene (always operates on the entire scene).
    
    Note: This function ignores the provided nodes and always works on all materials
    in the scene, since unused materials are a scene-level concept.
    """
    affected_nodes = []
    
    # Default materials that should never be deleted
    default_materials = ["lambert1", "particleCloud1", "shaderGlow1", "initialParticleSE"]
    
    try:
        # Find all shading engines (except initialShadingGroup)
        shadingEngines = cmds.ls(type="shadingEngine")
        shadingEngines = [sg for sg in shadingEngines if sg != "initialShadingGroup"]
        
        # Find unused shading engines
        unusedShadingEngines = []
        for sg in shadingEngines:
            # Find objects using this shading engine
            objects = cmds.sets(sg, query=True)
            if not objects:
                unusedShadingEngines.append(sg)
        
        # Find materials connected to unused shading engines
        unusedMaterials = []
        for sg in unusedShadingEngines:
            connections = cmds.listConnections(sg + ".surfaceShader", source=True, destination=False)
            if connections:
                unusedMaterials.extend(connections)
        
        # Filter out default materials that should be preserved
        unusedMaterials = [mat for mat in unusedMaterials if mat not in default_materials]
        
        # Report if nothing to delete
        if not unusedMaterials:
            cmds.warning("No unused materials found in the scene!")
            if nodes:
                affected_nodes.append(nodes[0])
            return "nodes", affected_nodes
        
        # Log the materials being deleted
        if unusedMaterials:
            cmds.warning("Deleting unused materials: {}".format(", ".join(unusedMaterials)))
        
        # Delete unused materials only (not shading engines)
        deleted_any = False
        if unusedMaterials:
            cmds.delete(unusedMaterials)
            deleted_any = True
        
        # For reporting purposes, return some nodes if materials were deleted
        if deleted_any and nodes:
            affected_nodes = [nodes[0]]  # Use the first node as a placeholder
        
    except Exception as e:
        cmds.warning("Failed to delete unused materials: {}".format(str(e)))
    
    return "nodes", affected_nodes