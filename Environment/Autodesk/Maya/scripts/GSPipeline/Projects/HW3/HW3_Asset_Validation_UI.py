# -*- coding: utf-8 -*-
import pymel.core as pm
import maya.cmds as cmds
import maya.OpenMaya as api
import maya.mel as mel
import os
import sys
from stat import S_IWUSR, S_IREAD


class pieceInfo:  # Use Python 3 class syntax
    def __init__(self, name, materialList):
        self.name = name
        self.materialList = materialList

# Developer Settings - Exclusion patterns
excluded_geo_patterns = ["PROXY_BAR_LOD", "COLLISION_SHAPE"]  # Add geometry name patterns to exclude from checks
excluded_mat_patterns = ["lambert1", "Collision", "XGizmo_Mat", "YGizmo_Mat", "ZGizmo_Mat"]  # Add material name patterns to exclude from checks

def addErrorMessage(message):
    error_msg = f"[X] ERROR: {message}"
    pm.textScrollList("resultField", e=True, a=error_msg)
    
def addWarningMessage(message):
    warning_msg = f"[!] WARNING: {message}"
    pm.textScrollList("resultField", e=True, a=warning_msg)

def addCorrectMessage(message):
    success_msg = f"[+] CORRECT: {message}"
    pm.textScrollList("resultField", e=True, a=success_msg)

def addInfoMessage(message):
    """Add an info message"""
    pm.textScrollList("resultField", e=True, a=message)

def getPiecesList():
    pm.select(cl=True)
    piecesList = [
                pieceInfo("BODY_LOD", ["MI_Livery"]),
                pieceInfo("CHASSIS_LOD", ["MI_Chassis"]),
                pieceInfo("BL_TYRE_LOD", ["MI_B_Wheel"]),
                pieceInfo("BR_TYRE_LOD", ["MI_B_Wheel"]),
                pieceInfo("FL_TYRE_LOD", ["MI_F_Wheel"]),
                pieceInfo("FR_TYRE_LOD", ["MI_F_Wheel"]),
                pieceInfo("FL_RIM_LOD", ["MI_F_Wheel", "MI_Face_Rim"]),
                pieceInfo("FR_RIM_LOD", ["MI_F_Wheel", "MI_Face_Rim"]),
                pieceInfo("BR_RIM_LOD", ["MI_Face_Rim"]),
                pieceInfo("BL_RIM_LOD", ["MI_Face_Rim"]),
                pieceInfo("EXTERIOR_LOD", ["MI_Exterior"]),
                pieceInfo("INTERIOR_LOD", ["MI_Interior"]),
                # Special
                pieceInfo("ENGINE_LOD", ["MI_Exterior"]),
                pieceInfo("FENDER_LOD", ["MI_Extra"]),
                pieceInfo("TANK_LOD", ["MI_Exterior"]),
                pieceInfo("WINDOW_LOD", ["MI_Glass"]),
                pieceInfo("WINDOWSHIELD_LOD", ["MI_Glass"]),
    ]

    def addPiece(piecePattern, materialsList):
        # This will find all piece names matching the pattern
        pieces = pm.ls(piecePattern, type="transform")
        for piece in pieces:
            # Extract the original name and replace any _LOD[letter] with _LOD
            piece_name = piece.name()
            if "_LOD" in piece_name:
                # Find where the _LOD part starts
                lod_index = piece_name.find("_LOD")
                # Take everything up to _LOD and add _LOD
                new_name = piece_name[:lod_index] + "_LOD"
                piecesList.append(pieceInfo(new_name, materialsList))
            else:
                # Fallback if the naming pattern is different
                piecesList.append(pieceInfo(piece_name, materialsList))

    # Then call it with a pattern that matches LODA, LODB, etc.
    addPiece("BR_RIM_0*_LOD?", ["MI_Face_Rim"])
    addPiece("BR_TYRE_0*_LOD?", ["MI_F_Wheel"])
    # Highpoly
    addPiece("BR_Car_0*", ["MI_B_Wheel"])
    addPiece("BL_Car_0*", ["MI_B_Wheel"])
    addPiece("FR_Car_0*", ["MI_F_Wheel"])
    addPiece("FL_Car_0*", ["MI_F_Wheel"])
    addPiece("Car_0*", ["MI_Livery", "MI_Chassis", "MI_Interior", "MI_Window"])
        
    return piecesList


def checkWheels(*args):
    """Check wheel-specific requirements: pivot consistency, mirror symmetry, and ground clearance"""
    pm.textScrollList("resultField", e=True, ra=True)
    pm.select(cl=True)
    
    addInfoMessage("=== WHEEL VALIDATION ===")
    addInfoMessage("")
    
    # Initialize counters
    pivot_issues = 0
    mirror_issues = 0
    ground_issues = 0
    tolerance = 0.1  # Small tolerance for floating point comparisons
    
    # Define wheel prefixes
    wheel_prefixes = ["BL_", "BR_", "FL_", "FR_"]
    
    # Separate LOD and non-LOD objects
    lod_objects = []
    non_lod_objects = []
    
    for prefix in wheel_prefixes:
        all_objects = pm.ls(prefix + "*", type="transform")
        for obj in all_objects:
            if "_LOD" in obj.name():
                lod_objects.append(obj)
            else:
                non_lod_objects.append(obj)
    
    # 1) PIVOT CONSISTENCY CHECK (only for LOD objects)
    addInfoMessage("--- 1. CHECKING PIVOT CONSISTENCY ---")
    
    if lod_objects:
        for prefix in wheel_prefixes:
            # Find LOD objects with this prefix
            prefix_lod_objects = [obj for obj in lod_objects if obj.name().startswith(prefix)]
            
            # Group by base name (everything before the LOD part)
            base_groups = {}
            for obj in prefix_lod_objects:
                obj_name = obj.name()
                base_name = obj_name[:obj_name.find("_LOD")]
                if base_name not in base_groups:
                    base_groups[base_name] = []
                base_groups[base_name].append(obj)
            
            # Check pivot consistency within each group
            for base_name, objects in base_groups.items():
                # Find the LODA object as reference
                loda_obj = None
                for obj in objects:
                    if obj.name().endswith("_LODA"):
                        loda_obj = obj
                        break
                
                if not loda_obj:
                    continue  # Skip if no LODA reference found
                
                # Get reference pivot
                ref_pivot = pm.xform(loda_obj, q=True, ws=True, rp=True)
                
                # Check all other objects in the group
                for obj in objects:
                    if obj == loda_obj:
                        continue
                    
                    obj_pivot = pm.xform(obj, q=True, ws=True, rp=True)
                    
                    # Compare pivots with tolerance
                    pivot_diff = [abs(ref_pivot[i] - obj_pivot[i]) for i in range(3)]
                    if any(diff > tolerance for diff in pivot_diff):
                        pivot_issues += 1
                        addErrorMessage(f"{obj.name()} pivot doesn't match {loda_obj.name()}")
        
        if pivot_issues == 0:
            addCorrectMessage("All wheel LOD pivots are consistent")
    else:
        addWarningMessage("No LOD objects found for pivot consistency check")
    
    # 2) MIRROR SYMMETRY CHECK
    addInfoMessage("")
    addInfoMessage("--- 2. CHECKING MIRROR SYMMETRY ---")
    
    # First try LOD objects (TYRE_LODA)
    tyre_lod_objects = {}
    for prefix in wheel_prefixes:
        tyre_name = prefix + "TYRE_LODA"
        if pm.objExists(tyre_name):
            tyre_lod_objects[prefix] = pm.PyNode(tyre_name)
    
    # If we have all 4 LOD TYRE objects, check their symmetry
    if len(tyre_lod_objects) == 4:
        addInfoMessage("Checking LOD TYRE objects mirror symmetry:")
        
        # Get pivot positions
        pivots = {}
        for prefix, obj in tyre_lod_objects.items():
            pivots[prefix] = pm.xform(obj, q=True, ws=True, rp=True)
        
        # Check mirror symmetry
        # Front wheels should mirror each other on Y-axis
        if "FL_" in pivots and "FR_" in pivots:
            fl_pos = pivots["FL_"]
            fr_pos = pivots["FR_"]
            
            # Calculate actual distances
            y_distance_diff = abs(abs(fl_pos[1]) - abs(fr_pos[1]))
            
            if y_distance_diff > tolerance:
                mirror_issues += 1
                addErrorMessage(f"Front wheels Y-axis mirror distance mismatch (difference: {y_distance_diff:.3f})")
        
        # Back wheels should mirror each other on Y-axis
        if "BL_" in pivots and "BR_" in pivots:
            bl_pos = pivots["BL_"]
            br_pos = pivots["BR_"]
            
            # Calculate actual distances
            y_distance_diff = abs(abs(bl_pos[1]) - abs(br_pos[1]))

            if y_distance_diff > tolerance:
                mirror_issues += 1
                addErrorMessage(f"Back wheels Y-axis mirror distance mismatch (difference: {y_distance_diff:.3f})")

        # Front and Back wheels should mirror each other on X-axis

        # Calculate actual distances
        x_distance_diff_right = abs(abs(fr_pos[1]) - abs(br_pos[1]))
        x_distance_diff_left = abs(abs(fl_pos[1]) - abs(bl_pos[1]))

        if x_distance_diff_right > tolerance:
            mirror_issues += 1
            addErrorMessage(f"FR and BR wheels X-axis mirror distance mismatch (difference: {x_distance_diff_right:.3f})")

        if x_distance_diff_left > tolerance:
            mirror_issues += 1
            addErrorMessage(f"FL and BL wheels X-axis mirror distance mismatch (difference: {x_distance_diff_left:.3f})")

    # Also check non-LOD objects if they exist
    if non_lod_objects:
        addInfoMessage("Checking non-LOD wheel objects mirror symmetry:")
        
        # Group non-LOD objects by prefix
        non_lod_by_prefix = {}
        for obj in non_lod_objects:
            for prefix in wheel_prefixes:
                if obj.name().startswith(prefix):
                    if prefix not in non_lod_by_prefix:
                        non_lod_by_prefix[prefix] = []
                    non_lod_by_prefix[prefix].append(obj)
                    break
        
        # For each combination of objects with the same base name (ignoring prefix)
        # we need to find matching pairs across prefixes
        base_name_groups = {}
        for prefix, objects in non_lod_by_prefix.items():
            for obj in objects:
                # Remove prefix to get base name
                base_name = obj.name()[3:]  # Remove first 3 characters (prefix)
                if base_name not in base_name_groups:
                    base_name_groups[base_name] = {}
                base_name_groups[base_name][prefix] = obj
        
        # Check mirror symmetry for each base name group
        for base_name, prefix_objects in base_name_groups.items():
            # Get pivot positions
            pivots = {}
            for prefix, obj in prefix_objects.items():
                pivots[prefix] = pm.xform(obj, q=True, ws=True, rp=True)
            
            # Check front wheel pairs
            if "FL_" in pivots and "FR_" in pivots:
                fl_pos = pivots["FL_"]
                fr_pos = pivots["FR_"]

                # Calculate actual distances
                y_distance_diff = abs(abs(fl_pos[1]) - abs(fr_pos[1]))
                
                if y_distance_diff > tolerance:
                    mirror_issues += 1
                    addErrorMessage(f"Front wheels Y-axis mirror distance mismatch (difference: {y_distance_diff:.3f})")
            
            # Check back wheel pairs
            if "BL_" in pivots and "BR_" in pivots:
                bl_pos = pivots["BL_"]
                br_pos = pivots["BR_"]
                
                # Calculate actual distances
                y_distance_diff = abs(abs(bl_pos[1]) - abs(br_pos[1]))

                if y_distance_diff > tolerance:
                    mirror_issues += 1
                    addErrorMessage(f"Back wheels Y-axis mirror distance mismatch (difference: {y_distance_diff:.3f})")

            # Calculate actual distances
            x_distance_diff_right = abs(abs(fr_pos[1]) - abs(br_pos[1]))
            x_distance_diff_left = abs(abs(fl_pos[1]) - abs(bl_pos[1]))

            if x_distance_diff_right > tolerance:
                mirror_issues += 1
                addErrorMessage(f"FR and BR wheels X-axis mirror distance mismatch (difference: {x_distance_diff_right:.3f})")

            if x_distance_diff_left > tolerance:
                mirror_issues += 1
                addErrorMessage(f"FL and BL wheels X-axis mirror distance mismatch (difference: {x_distance_diff_left:.3f})")
    
    if mirror_issues == 0:
        addCorrectMessage("All wheel positions are properly mirrored")
    
    # 3) GROUND DISTANCE CHECK
    addInfoMessage("")
    addInfoMessage("--- 3. CHECKING GROUND DISTANCE ---")
    
    # Find LOD objects with "TYRE" in the name
    tyre_lod_objects = pm.ls("*TYRE*", type="transform")
    tyre_lod_objects = [obj for obj in tyre_lod_objects if "_LOD" in obj.name()]
    
    # Find non-LOD objects with wheel prefixes
    wheel_non_lod_objects = []
    for prefix in wheel_prefixes:
        prefix_objects = pm.ls(prefix + "*", type="transform")
        wheel_non_lod_objects.extend([obj for obj in prefix_objects if "_LOD" not in obj.name()])
    
    # Combine all objects to check
    all_ground_check_objects = tyre_lod_objects + wheel_non_lod_objects
    
    if all_ground_check_objects:
        if tyre_lod_objects:
            addInfoMessage("Checking LOD TYRE objects ground distance:")
            
        if wheel_non_lod_objects:
            addInfoMessage("Checking non-LOD wheel objects ground distance:")
        
        # Check all objects for ground distance
        for obj in all_ground_check_objects:
            # Get the mesh shape
            shapes = pm.listRelatives(obj, shapes=True, type="mesh")
            if not shapes:
                continue
            
            # Get all vertices
            mesh_shape = shapes[0]
            vertex_count = pm.polyEvaluate(mesh_shape, v=True)
            
            # Find the lowest vertex Z value
            lowest_z = float('inf')
            for i in range(vertex_count):
                vertex_pos = pm.xform(f"{mesh_shape}.vtx[{i}]", q=True, ws=True, t=True)
                if vertex_pos[2] < lowest_z:
                    lowest_z = vertex_pos[2]
            
            # Check if lowest vertex is below ground (Z=0)
            if abs(lowest_z) > tolerance:
                ground_issues += 1
                object_type = "LOD" if "_LOD" in obj.name() else "non-LOD"
                addErrorMessage(f"{obj.name()} ({object_type}) lowest vertex is far from ground: Z={lowest_z:.3f}")
        
        if ground_issues == 0:
            addCorrectMessage("All wheel objects are properly positioned on the ground")
    else:
        addWarningMessage("No wheel objects found for ground distance check")
    
    # Summary
    addInfoMessage("")
    addInfoMessage("=================================================")
    addInfoMessage("")
    addInfoMessage("--- WHEEL CHECK SUMMARY ---")
    addInfoMessage("")
    addInfoMessage("Issues found:")
    addInfoMessage(f"  - Pivot consistency issues: {pivot_issues}")
    addInfoMessage(f"  - Mirror symmetry issues: {mirror_issues}")
    addInfoMessage(f"  - Ground distance issues: {ground_issues}")
    addInfoMessage("")
    
    total_wheel_issues = pivot_issues + mirror_issues + ground_issues
    if total_wheel_issues == 0:
        addCorrectMessage("All wheel checks passed!")
    else:
        addErrorMessage(f"TOTAL WHEEL ISSUES: {total_wheel_issues}")

def checkScene(*args):
    """Check scene objects for proper naming and setup"""
    pm.textScrollList("resultField", e=True , ra=True)
    pm.select(cl=True)

    # Show exclusion info in the results (debugging help)
    # if excluded_geo_patterns:
    #     addInfoMessage("Excluded geometry patterns: " + ", ".join(excluded_geo_patterns))
    # if excluded_mat_patterns:
    #     addInfoMessage("Excluded material patterns: " + ", ".join(excluded_mat_patterns))
    # if excluded_geo_patterns or excluded_mat_patterns:
    #     addInfoMessage("")

    # Initialize counters for summary
    scene_issues = 0
    material_issues = 0
    geometry_issues = 0
    uv_issues = 0
    total_mesh_objects = 0
    uv_checked_objects = 0

    polyCount = {"LODA": 50000}                  
    
    matCorrectNameList = [
        "MI_B_Wheel",
        "MI_Chassis",  
        "MI_Exterior", 
        "MI_Extra", 
        "MI_F_Wheel", 
        "MI_Face_Rim",
        "MI_Glass",
        "MI_Interior",
        "MI_Livery",                        
    ]
        
    piecesList = getPiecesList()
    
    # Extract just the piece names for easier checking
    allowedPieceNames = [piece.name for piece in piecesList]
    
    # 1) CHECKING SCENE SETTINGS
    addInfoMessage("--- 1. CHECKING SCENE ---")
    
    # Check up-axis
    current_up_axis = pm.upAxis(q=True, axis=True)
    if current_up_axis != 'z':
        scene_issues += 1
        addErrorMessage(f"Scene up-axis is {current_up_axis}, should be Z")
    else:
        addCorrectMessage("Scene up-axis: Z (correct)")
    
    # Check units
    current_unit = pm.currentUnit(q=True, linear=True)
    if current_unit != 'cm':
        scene_issues += 1
        addErrorMessage(f"Scene linear unit is {current_unit}, should be centimeters")
    else:
        addCorrectMessage("Scene linear unit: centimeters (correct)")
    
    # 2) UNKNOWN MATERIALS - Modified to use substring matching and exclude patterns
    addInfoMessage("")
    addInfoMessage("--- 2. CHECKING MATERIALS ---")
    shadingEngineList = pm.ls(type="shadingEngine")
    unknownMaterialsList = []
    for shadingEngine in shadingEngineList:
        try:
            mat = pm.listConnections(shadingEngine.surfaceShader)[0].name()
            
            # Skip materials matching any exclusion pattern
            excluded = False
            for pattern in excluded_mat_patterns:
                if pattern in mat:
                    excluded = True
                    break
            if excluded:
                continue
                
            materialFound = False
            
            # Check if the material name contains any of the allowed material names
            for allowedMat in matCorrectNameList:
                if allowedMat in mat:
                    materialFound = True
                    break
            
            # Special checks for materials with specific substrings
            if not materialFound and ("mat_vol" in mat or "Gizmo_Mat" in mat):
                materialFound = True
                
            if not materialFound:
                unknownMaterialsList.append(mat)
        except:
            continue    
    
    if len(unknownMaterialsList) > 0:
        material_issues = len(unknownMaterialsList)
        for unknownMat in unknownMaterialsList:
            addErrorMessage(unknownMat+" is an unknown material")
    else:
        addCorrectMessage("All materials are valid")

    # 3) UNKNOWN GEO - Modified to use substring matching and exclude patterns
    addInfoMessage("")
    addInfoMessage("--- 3. CHECKING GEOMETRY ---")
    
    # Get all mesh shapes first, then get their transforms
    meshShapes = pm.ls(type="mesh")
    meshTransforms = []
    for shape in meshShapes:
        transform = pm.listRelatives(shape, parent=True, type="transform")
        if transform:
            meshTransforms.extend(transform)
    
    # Remove duplicates
    meshTransforms = list(set(meshTransforms))
    total_mesh_objects = len(meshTransforms)
    
    autorigObjectsList = []
    if pm.objExists("Nulls_grp"):   
        autorigObjectsList = pm.listRelatives("Nulls_grp", ad=True, type="transform")       
    
    for geo in meshTransforms:
        geoName = geo.name()
        
        # Skip geometries matching any exclusion pattern
        excluded = False
        for pattern in excluded_geo_patterns:
            if pattern in geoName:
                excluded = True
                break
        if excluded:
            continue
        
        # Skip certain system objects, volume objects, and objects with NULL in name
        if ("vol_" in geoName or "NULL" in geoName or "Nulls_grp" in geoName or 
            geo in autorigObjectsList or 
            geoName in ["back", "front", "left", "persp", "side", "top"]):
            continue        
        
        isBikePiece = False         
        # Check if geometry name contains any of the allowed piece names
        for allowedPieceName in allowedPieceNames:
            if allowedPieceName in geoName:
                isBikePiece = True
                break
                
        if not isBikePiece:
            geometry_issues += 1
            addErrorMessage(geoName+" is an unknown object (or has a wrong name)")
    
    if geometry_issues == 0:
        addCorrectMessage("All geometry names are valid")
    
    # 4) CHECK: UV channel names and structure
    addInfoMessage("")
    addInfoMessage("--- 4. CHECKING UV CHANNELS ---")

    # SHAPE, UVs E MATERIAL SUI SINGOLI PEZZI
    for piece in piecesList:
        pieceLodsList = pm.ls(piece.name+"*", type="transform")
        for pieceLod in pieceLodsList:
            # Skip non-LOD objects for UV checking
            if "_LOD" not in pieceLod.name():
                continue
                
            pieceShape = pm.listRelatives(pieceLod, s=True)
                
            uvChannelName = ["UVChannel_1", "UVChannel_2", "UVChannel_3", "UVChannel_4"] 
            pieceLodUVs = pm.polyUVSet(pieceLod, q=True, auv=True)            
            if pieceLodUVs and len(pieceLodUVs) > 4:  # Added check for None
                uv_issues += 1
                addErrorMessage(pieceLod.name()+" has more than 4 UVs channels")           
            for uvs in (pieceLodUVs or []):  # Handle potential None
                if uvs not in uvChannelName: 
                    uv_issues += 1
                    addErrorMessage(pieceLod.name()+" has wrong UVs channel name: "+uvs)                                       
                    
            if not pieceShape:  # Skip if no shape found
                continue

    # MATCHING UV1-UV2
    # This line is crucial - select all meshes first to set up the state correctly
    shapesList = pm.ls(type="mesh")
    transformList = pm.listRelatives(shapesList, parent=True)
    if transformList:  # Added check for None
        pm.select(transformList, r=True, vis=True)

    for piece in piecesList:
        pieceLodsList = pm.ls(piece.name+"*", type="transform")
        for pieceLod in pieceLodsList:
            # Skip non-LOD objects for UV checking
            if "_LOD" not in pieceLod.name():
                continue
                
            # Skip geometries matching any exclusion pattern
            excluded = False
            for pattern in excluded_geo_patterns:
                if pattern in pieceLod.name():
                    excluded = True
                    break
            if excluded:
                continue
                
            pieceShape = pm.listRelatives(pieceLod, s=True)
            if not pieceShape:  # Skip if no shape found
                continue
                
            uv_checked_objects += 1
                
            # Select all shapes at once - this follows the working script pattern
            pm.select(pieceShape)
            pm.polyUVSet(cuv=True, uvs='UVChannel_1')
            pm.select(pm.polyListComponentConversion(tuv=True))
            UVValues_map1 = pm.polyEditUV(query=True, relative=False)
            
            pm.select(pieceShape)
            pm.polyUVSet(cuv=True, uvs='UVChannel_2')
            pm.select(pm.polyListComponentConversion(tuv=True))
            UVValues_map2 = pm.polyEditUV(query=True, relative=False)
            
            pm.select(pieceShape)
            
            if UVValues_map1 is None or len(UVValues_map1) == 0:
                uv_issues += 1
                addErrorMessage(pieceLod.name()+" UVChannel_1 empty")

            if UVValues_map2 is None or len(UVValues_map2) == 0:
                uv_issues += 1
                addErrorMessage(pieceLod.name()+" UVChannel_2 empty")

            if UVValues_map1 is not None and UVValues_map2 is not None:
                if sum(UVValues_map1) != sum(UVValues_map2):
                    uv_issues += 1
                    addErrorMessage(pieceLod.name()+" UVChannel_1 and UVChannel_2 not match")

    # CHECK UV3 EMPTY
    for piece in piecesList:
        pieceLodsList = pm.ls(piece.name+"*", type="transform")
        for pieceLod in pieceLodsList:
            # Skip non-LOD objects for UV checking
            if "_LOD" not in pieceLod.name():
                continue
                
            # Skip geometries matching any exclusion pattern
            excluded = False
            for pattern in excluded_geo_patterns:
                if pattern in pieceLod.name():
                    excluded = True
                    break
            if excluded:
                continue
                
            pieceShape = pm.listRelatives(pieceLod, s=True)
            if not pieceShape:  # Skip if no shape found
                continue
                
            pm.select(pieceShape)
            pm.polyUVSet(cuv=True, uvs='UVChannel_3')
            pm.select(pm.polyListComponentConversion(tuv=True))
            UVValues_map3 = pm.polyEditUV(query=True, relative=False)
            
            pm.select(pieceShape)
            
            # Check if UVChannel_3 has data (should be empty)
            if UVValues_map3 is not None and len(UVValues_map3) > 0:
                uv_issues += 1
                addErrorMessage(pieceLod.name()+" UVChannel_3 should be empty but contains data")
                    
    pm.select(d=True)  # Clear selection at the end

    if uv_issues == 0 and uv_checked_objects > 0:
        addCorrectMessage("All UV channels are valid")
    elif uv_checked_objects == 0:
        addWarningMessage("No LOD mesh objects found for UV check")
    
    # Add separator for completion
    addInfoMessage("")
    addInfoMessage("=================================================")
    addInfoMessage("")
    
    # 5) CHECK COMPLETE WITH SUMMARY
    addInfoMessage("--- 5. CHECK COMPLETE ---")
    addInfoMessage("")
    
    # Summary
    addInfoMessage(f"Total mesh objects checked: {total_mesh_objects}")
    addInfoMessage(f"UV objects checked: {uv_checked_objects}")
    addInfoMessage("")
    addInfoMessage("Issues found:")
    addInfoMessage(f"  - Scene issues: {scene_issues}")
    addInfoMessage(f"  - Material issues: {material_issues}")
    addInfoMessage(f"  - Geometry issues: {geometry_issues}")
    addInfoMessage(f"  - UV issues: {uv_issues}")
    addInfoMessage("")
    
    total_issues = scene_issues + material_issues + geometry_issues + uv_issues
    if total_issues == 0:
        addCorrectMessage("No issues found! All assets follow the required conventions.")
    else:
        addErrorMessage(f"TOTAL ISSUES: {total_issues}")

def createLodGroup(self):
    cmds.select(all=True)
    sel = cmds.ls(sl=True)
    
    # Define LOD groups in a list to maintain correct order
    lod_order = ['LODA', 'LODB', 'LODC', 'LODD', 'LODE', 'LODF']
    lodGroups = {lod: [] for lod in lod_order}  # Create ordered dictionary
    
    # Sort objects into LOD groups
    for obj in sel:
        for lod_key in lod_order:  # Use ordered list instead of dictionary keys
            if obj.endswith(lod_key):
                lodGroups[lod_key].append(obj)
                break
            else:
                print("Object {0} didn't match {1}".format(obj, lod_key))
    
    # Delete existing LOD groups if they exist
    existing_groups = cmds.ls("LOD_*")
    if existing_groups:
        cmds.delete(existing_groups)
    
    # Create new groups in correct order
    created_groups = []
    for i, lod_key in enumerate(lod_order):  # Use ordered list for group creation
        objects = lodGroups[lod_key]
        if objects:
            group_name = "LOD_{0}".format(i)
            cmds.group(objects, name=group_name)
            created_groups.append(group_name)
    
    # Create final LOD group
    if created_groups:
        cmds.select(clear=True)
        for group in created_groups:
            cmds.select(group, add=True)
        cmds.LevelOfDetailGroup()
        
        if cmds.objExists("Car_LOD_Group"):
            cmds.delete("CarLOD_Group")
        
        cmds.rename("LOD_Group_1", "Car_LOD_Group")
        cmds.select("Car_LOD_Group", deselect=True)

def copyUV1ToUV2(*args):
    """Copy UVChannel_1 to UVChannel_2 for selected objects"""
    selection = pm.selected()
    if not selection:
        pm.warning("No objects selected. Please select objects to copy UVs.")
        return
    
    processed_count = 0
    failed_objects = []
    
    for obj in selection:
        shapes = pm.listRelatives(obj, shapes=True, type="mesh")
        if not shapes:
            continue
            
        shape = shapes[0]
        
        try:
            # Check if UVChannel_1 exists
            uv_sets = pm.polyUVSet(shape, query=True, allUVSets=True)
            if 'UVChannel_1' not in uv_sets:
                print(f"Warning: {obj.name()} missing UVChannel_1")
                continue
            
            pm.select(shape)
            
            # Store existing channels that need to be preserved and recreated
            channels_to_preserve = []
            temp_names = []
            
            # Check what channels exist and need to be preserved
            for channel_num in [3, 4]:  # Check UVChannel_3 and UVChannel_4
                channel_name = f'UVChannel_{channel_num}'
                if channel_name in uv_sets:
                    temp_name = f'temp_uv_{channel_num}'
                    channels_to_preserve.append((channel_name, temp_name))
                    temp_names.append(temp_name)
            
            # Step 1: Copy existing UVChannel_3 and UVChannel_4 to temporary channels
            for original_name, temp_name in channels_to_preserve:
                pm.polyUVSet(shape, copy=True, nuv=temp_name, uvs=original_name)
            
            # Step 2: Delete UVChannel_2, UVChannel_3, UVChannel_4 if they exist
            for channel_num in [2, 3, 4]:
                channel_name = f'UVChannel_{channel_num}'
                if channel_name in uv_sets:
                    pm.polyUVSet(shape, delete=True, uvs=channel_name)
            
            # Step 3: Copy UVChannel_1 to create new UVChannel_2
            pm.polyUVSet(shape, copy=True, nuv='UVChannel_2', uvs='UVChannel_1')
            
            # Step 4: Recreate UVChannel_3 and UVChannel_4 in the correct order
            for original_name, temp_name in channels_to_preserve:
                pm.polyUVSet(shape, copy=True, nuv=original_name, uvs=temp_name)
            
            # Step 5: Clean up temporary channels
            for temp_name in temp_names:
                pm.polyUVSet(shape, delete=True, uvs=temp_name)
            
            processed_count += 1
            print(f"Successfully copied UVs for {obj.name()}")
            addInfoMessage(f"Succesfully copied UVs for {obj.name()}")
            
        except Exception as e:
            failed_objects.append(obj.name())
            print(f"Failed to copy UVs for {obj.name()}: {str(e)}")
            addInfoMessage(f"Failed to copy UVs for {obj.name()}: {str(e)}")
    
    pm.select(selection)  # Restore original selection
    
    # Report results
    if processed_count > 0:
        print(f"Successfully copied UVChannel_1 to UVChannel_2 for {processed_count} objects")
    if failed_objects:
        print(f"Failed objects: {', '.join(failed_objects)}")

def deleteUV3(*args):
    """Delete UV shells from UVChannel_3 for selected objects"""
    selection = pm.selected()
    if not selection:
        pm.warning("No objects selected. Please select objects to clear UVChannel_3.")
        return
    
    processed_count = 0
    failed_objects = []
    
    for obj in selection:
        shapes = pm.listRelatives(obj, shapes=True, type="mesh")
        if not shapes:
            continue
            
        shape = shapes[0]
        
        try:
            # Check if UVChannel_3 exists
            uv_sets = pm.polyUVSet(shape, query=True, allUVSets=True)
            if 'UVChannel_3' not in uv_sets:
                print(f"Warning: {obj.name()} does not have UVChannel_3")
                continue
            
            pm.select(shape)
            
            # Step 1: Check if UVChannel_4 exists and back it up
            has_channel_4 = 'UVChannel_4' in uv_sets
            temp_channel_4_name = 'temp_uv_4'
            
            if has_channel_4:
                # Back up UVChannel_4
                pm.polyUVSet(shape, copy=True, nuv=temp_channel_4_name, uvs='UVChannel_4')
            
            # Step 2: Delete UVChannel_3 and UVChannel_4 (if it exists)
            pm.polyUVSet(shape, delete=True, uvs='UVChannel_3')
            if has_channel_4:
                pm.polyUVSet(shape, delete=True, uvs='UVChannel_4')
            
            # Step 3: Recreate empty UVChannel_3
            pm.polyUVSet(shape, create=True, uvs='UVChannel_3')
            
            # Step 4: Restore UVChannel_4 if it existed
            if has_channel_4:
                pm.polyUVSet(shape, copy=True, nuv='UVChannel_4', uvs=temp_channel_4_name)
                # Clean up temporary channel
                pm.polyUVSet(shape, delete=True, uvs=temp_channel_4_name)
            
            processed_count += 1
            print(f"Successfully cleared UVChannel_3 for {obj.name()}")
            addInfoMessage(f"Successfully cleared UVChannel_3 for {obj.name()}")
            
        except Exception as e:
            failed_objects.append(obj.name())
            print(f"Failed to clear UVChannel_3 for {obj.name()}: {str(e)}")
            addInfoMessage(f"Failed to clear UVChannel_3 for {obj.name()}: {str(e)}")
    
    pm.select(selection)  # Restore original selection
    
    # Report results
    if processed_count > 0:
        print(f"Successfully cleared UVChannel_3 for {processed_count} objects")
    if failed_objects:
        print(f"Failed objects: {', '.join(failed_objects)}")

def UI():
    if cmds.window("win", exists=True):
        cmds.deleteUI("win", window=True)
    
    cmds.window("win", title="Hotwheels3 Asset Validation")   
    
    height = 20
        
    mainLayout = pm.columnLayout(adjustableColumn=True, width=640, height=720)
    
    # Main check section
    pm.separator(style="out", height=5)
    pm.text(label="Asset Validation", font="boldLabelFont", align="center")
    pm.separator(style="in", height=20)
    
    pm.button(label="Check Scene", height=height+10, command=checkScene)

    pm.button(label="Check Wheels", height=height+10, command=checkWheels)
    pm.separator(style="in", height=20)
    
    pm.text(label="Results:", align="left")
    pm.separator(style="none", height=5)
    
    # Create a colored text field for better visibility
    pm.textScrollList("resultField", width=640, height=360, 
                     selectCommand=lambda: None,  # Disable selection
                     allowMultiSelection=False)
    
    pm.separator(style="in", height=20)

    pm.button(label="Create LOD Group", height=height+10, command=createLodGroup)

    pm.button(label="Copy UVChannel_1 to UVChannel_2 for Selection", height=height+10, command=copyUV1ToUV2)

    pm.button(label="Delete UV shells from UVChannel_3 for Selection", height=height+10, command=deleteUV3)

    pm.separator(style="in", height=20)

    # Add legend for symbols
    pm.separator(style="none", height=5)
    pm.text(label="Symbol: [X] = Error | [!] = Warning | [+] = Correct", 
           align="center", font="smallPlainLabelFont")
    
    pm.separator(style="in", height=20)

    cmds.showWindow("win")

if __name__ == "__main__":
    UI()