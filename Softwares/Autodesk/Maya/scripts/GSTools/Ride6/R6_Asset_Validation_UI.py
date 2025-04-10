import pymel.core as pm
import maya.cmds as cmds
import maya.OpenMaya as api
import maya.mel as mel
import os
import sys
from stat import S_IWUSR, S_IREAD


class pieceInfo(object):  # Explicitly inherit from object for Python 2.7
    def __init__(self, name, materialList):
        self.name = name
        self.materialList = materialList


def getPiecesList():
    pm.select(cl=True)
    piecesList = [
                pieceInfo("MAIN_BODY_LOD", ["mat_livery_0", "mat_livery_1", "mat_mechanics", "mat_cockpit"]),
                pieceInfo("F_SUSP_LOD", ["mat_livery_0", "mat_livery_1", "mat_mechanics", "mat_cockpit"]),  
                pieceInfo("SUSP_LOD", ["mat_mechanics"]),
                pieceInfo("B_RAKE_LOD", ["mat_livery_0", "mat_livery_1", "mat_mechanics", "mat_cockpit"]),
                pieceInfo("F_RAKE_LOD", ["mat_livery_0", "mat_livery_1", "mat_mechanics", "mat_cockpit"]),
                pieceInfo("F_ARM_LOD", ["mat_mechanics"]),
                pieceInfo("HANDLE_LOD", ["mat_cockpit"]),
                pieceInfo("TRIPLECLAMP_LOD", ["mat_cockpit"]),
                pieceInfo("HANDLEBAR_LOD", ["mat_cockpit"]),
                pieceInfo("DAMPER_BODY_LOD", ["mat_mechanics"]),
                pieceInfo("DAMPER_SPRING_LOD", ["mat_mechanics"]),
                pieceInfo("HANDLE_DAMPER_LOD", ["mat_cockpit"]),
                pieceInfo("HANDLE_DAMPER_PISTON_LOD", ["mat_cockpit"]),
                pieceInfo("F_DAMPER_BODY_LOD", ["mat_mechanics"]),
                pieceInfo("F_DAMPER_SPRING_LOD", ["mat_mechanics"]),                
                pieceInfo("F_RIM_LOD", ["mat_rim"]),
                pieceInfo("B_RIM_LOD", ["mat_rim"]),
                pieceInfo("F_TYRE_LOD", ["mat_f_tyre"]),
                pieceInfo("B_TYRE_LOD", ["mat_b_tyre"]),
                pieceInfo("B_BRAKE_LOD", ["mat_brake"]),
                pieceInfo("FL_BRAKE_LOD", ["mat_brake"]),
                pieceInfo("FR_BRAKE_LOD", ["mat_brake"]),
                pieceInfo("GAUGE_LOD", ["mat_gauge"]),
                pieceInfo("GAUGE_GLASS_LOD", ["mat_glass"]),
                pieceInfo("RPM_NEEDLE_LOD", ["mat_lights"]),
                pieceInfo("SPD_NEEDLE_LOD", ["mat_lights"]),
                pieceInfo("PLATE_LOD", ["mat_livery_0", "mat_livery_1", "mat_mechanics"]),
                pieceInfo("PLATE_GLASS_LOD", ["mat_glass"]),
                pieceInfo("PLATE_GLASS_TINT_LOD", ["mat_glasstint"]),
                pieceInfo("BLINKERS_LOD", ["mat_livery_0", "mat_livery_1", "mat_mechanics"]),
                pieceInfo("BLINKERS_GLASS_LOD", ["mat_glass"]),
                pieceInfo("BLINKERS_GLASS_TINT_LOD", ["mat_glasstint"]),
                pieceInfo("FOOTPEGS_LOD", ["mat_mechanics"]),
                pieceInfo("MIRROR_LOD", ["mat_livery_0", "mat_livery_1", "mat_mechanics"]),
                pieceInfo("MIRROR_GLASS_LOD", ["mat_glass"]),
                pieceInfo("MIRROR_GLASS_TINT_LOD", ["mat_glasstint"]),
                pieceInfo("MIRROR_VIEW_LOD", ["mat_mirror_view"]),
                pieceInfo("F_GLASS_LOD", ["mat_glass", "mat_glass_edge"]),
                pieceInfo("F_GLASS_TINT_LOD", ["mat_glasstint"]),
                pieceInfo("F_GLASS_DECAL_LOD", ["mat_glassdecal"]),
                pieceInfo("F_LIGHT_LOD", ["mat_lights", "mat_mechanics", "mat_livery_0", "mat_livery_1"]),
                pieceInfo("F_LIGHT_GLASS_LOD", ["mat_glass"]),
                pieceInfo("F_LIGHT_GLASS_TINT_LOD", ["mat_glasstint"]),
                pieceInfo("B_LIGHT_LOD", ["mat_lights"]),
                pieceInfo("B_LIGHT_GLASS_LOD", ["mat_glass"]),
                pieceInfo("B_LIGHT_GLASS_TINT_LOD", ["mat_glasstint"]),
                pieceInfo("F_CALIPER_LOD", ["mat_mechanics"]),
                pieceInfo("B_CALIPER_LOD", ["mat_mechanics"]),
                pieceInfo("R_GRIP_LOD", ["mat_cockpit"]),
                pieceInfo("L_GRIP_LOD", ["mat_cockpit"]),
                pieceInfo("R_LEVER_LOD", ["mat_cockpit"]),
                pieceInfo("L_LEVER_LOD", ["mat_cockpit"]),
                pieceInfo("CLUTCH_LOD", ["mat_mechanics"]),
                pieceInfo("GEAR_LOD", ["mat_gear"]),
                pieceInfo("B_GEAR_LOD", ["mat_gear"]),
                pieceInfo("CHAIN_LOD", ["mat_chain"]),
                pieceInfo("HANDLE_BRAKE_CABLE_LOD", ["mat_mechanics"]),
                pieceInfo("F_SUSP_BRAKE_CABLE_LOD", ["mat_mechanics"]),
                pieceInfo("B_BRAKE_CABLE_LOD", ["mat_mechanics"]),
                pieceInfo("KICKSTAND_LOD", ["mat_mechanics"]),
                #pieceInfo("R_HANDGUARD_LOD", ["mat_handguard"]),
                #pieceInfo("L_HANDGUARD_LOD", ["mat_handguard"]),
                pieceInfo("BARPAD_LOD", ["mat_barpad"]),
                pieceInfo("KEY_LOD", ["mat_cockpit"]),
                pieceInfo("REFLECTOR_LOD", ["mat_livery_0", "mat_livery_1", "mat_mechanics", "mat_glass"]),
                # Modify for Ride6
                pieceInfo("FAIRING_BAR_LOD", ["mat_mechanics"]),
                pieceInfo("FAIRING_BAR_ENDURO_LOD", ["mat_preset_enduro"]),
                pieceInfo("HEADLIGHT_GRILLE_LOD", ["mat_mechanics"]),
                pieceInfo("HEADLIGHT_GRILLE_ENDURO_LOD", ["mat_preset_enduro"]),
                pieceInfo("R_HANDGUARD_LOD", ["mat_livery_0", "mat_livery_1"]),
                pieceInfo("L_HANDGUARD_LOD", ["mat_livery_0", "mat_livery_1"]),
                pieceInfo("R_HANDGUARD_ENDURO_LOD", ["mat_preset_enduro"]),
                pieceInfo("L_HANDGUARD_ENDURO_LOD", ["mat_preset_enduro"]),
                pieceInfo("SUMP_GUARD_LOD", ["mat_mechanics"]),
                pieceInfo("SUMP_GUARD_ENDURO_LOD", ["mat_preset_enduro"]),
                pieceInfo("RADIATOR_GRILLE_LOD", ["mat_mechanics"]),
                pieceInfo("RADIATOR_GRILLE_ENDURO_LOD", ["mat_preset_enduro"])
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
    addPiece("MUFFLER_00*_LOD?", ["mat_muffler"])
    addPiece("MOUNT_00*_LOD?", ["mat_muffler"])
    addPiece("EXMANIFOLD_00*_LOD?", ["mat_exmanifold"])
        
    return piecesList
    

def check(self):
    pm.textScrollList("resultField", e=True, ra=True)
    pm.select(cl=True)
    
    polyCount = {"LODA": 200000}                  
    
    matCorrectNameList = [
        "mat_livery_0", 
        "mat_livery_1",
        "mat_mechanics",  
        "mat_cockpit", 
        "mat_chain", 
        "mat_gauge", 
        "mat_glass", 
        "mat_glasstint",                        
        "mat_glassdecal",
        "mat_lights",
        "mat_gear",
        "mat_mirror_view",
        "mat_brake",
        "mat_rim",
        "mat_f_tyre",
        "mat_b_tyre",
        "mat_handguard",
        "mat_barpad",
        "mat_muffler",
        "mat_glass_edge",                     
        "mat_exmanifold",
        # Modify for Ride6
        "mat_preset_enduro"
    ]
        
    piecesList = getPiecesList()
    
    mandatoryPiecesList = ["MAIN_BODY", "HANDLE", "L_LEVER", "R_LEVER", "L_GRIP", "R_GRIP", "F_TYRE", "B_TYRE", "F_RIM", "B_RIM", "B_RAKE"]
    
    # POLYCOUNT
    for lod, maxTris in list(polyCount.items()):
        geoList = pm.ls("*_"+lod, type="transform")
        try:
            polyCount = int(pm.polyEvaluate(geoList, t=True))
            if polyCount > maxTris:          
                pm.textScrollList("resultField", e=True, a=lod+" pieces together exceeds the polycount of "+str(maxTris - polyCount)+" tris")
        except ValueError:
            # Handle case when no polygonal objects are found
            pm.textScrollList("resultField", e=True, a="No polygonal objects found for "+lod)  

    # UNKNOWN MATERIALS
    shadingEngineList = pm.ls(type="shadingEngine")
    unknownMaterialsList = []
    for shadingEngine in shadingEngineList:
        try:
            mat = pm.listConnections(shadingEngine.surfaceShader)[0].name()
            if mat not in matCorrectNameList and "mat_vol" not in mat and "lambert1" not in mat and "Gizmo_Mat" not in mat:
                unknownMaterialsList.append(mat)
        except:
            continue    
    if len(unknownMaterialsList) > 0:
        for unknownMat in unknownMaterialsList:
            pm.textScrollList("resultField", e=True, a=unknownMat+" is an unknown material")
    
    # UNKNOWN GEO                   
    geoList = pm.ls(type="transform")
    autorigObjectsList = []
    if pm.objExists("Nulls_grp"):   
        autorigObjectsList = pm.listRelatives("Nulls_grp", ad=True, type="transform")       
    for geo in geoList:
        if "vol_" in geo.name() or "Nulls_grp" in geo.name() or geo.name() in autorigObjectsList or geo.name()=="back" or geo.name()=="front" or geo.name()=="left" or geo.name()=="persp" or geo.name()=="side" or geo.name()=="top":
            continue        
        isBikePiece = False         
        for bikePiece in piecesList:
            if bikePiece.name in geo.name():
                if geo.name()[-5:-4] == '_':
                    isBikePiece = True
                    break
        if isBikePiece:
            continue        
        pm.textScrollList("resultField", e=True, a=geo.name()+" is an unknown object (or has a wrong name)")
    
    # SHAPE, UVs E MATERIAL SUI SINGOLI PEZZI
    for piece in piecesList:
        pieceLodsList = pm.ls(piece.name+"*", type="transform")
        for pieceLod in pieceLodsList:
            pieceShape = pm.listRelatives(pieceLod, s=True)
            if pieceShape and len(pieceShape) > 1:  # Added check for None
                pm.textScrollList("resultField", e=True, a=pieceLod.name()+" has multiple shapes")
                
            uvChannelName = ["UVChannel_1", "UVChannel_2", "UVChannel_3", "UVChannel_4"] 
            pieceLodUVs = pm.polyUVSet(pieceLod, q=True, auv=True)            
            if pieceLodUVs and len(pieceLodUVs) > 4:  # Added check for None
                pm.textScrollList("resultField", e=True, a=pieceLod.name()+" has more than 4 UVs channels")           
            for uvs in (pieceLodUVs or []):  # Handle potential None
                if uvs not in uvChannelName: 
                    pm.textScrollList("resultField", e=True, a=pieceLod.name()+" has wrong UVs channel name: "+uvs)                                       
                    
            if not pieceShape:  # Skip if no shape found
                continue
                
            shadingList = pm.listConnections(pieceLod.getShape(), type="shadingEngine") 
            shadingList = list(set(shadingList)) # Remove duplicates
            for shading in shadingList:
                if not pm.listConnections(shading.surfaceShader):  # Changed length check to existence check
                    pm.textScrollList("resultField", e=True, a=pieceLod.name()+" has no material assigned")
                    continue
                mat = pm.listConnections(shading.surfaceShader)[0]  
                if mat.name() not in piece.materialList:
                    pm.textScrollList("resultField", e=True, a=pieceLod.name()+" has assigned a wrong material: "+mat.name())
                else:
                    if "_LODA" in pieceLod.name() and "mat_livery_1" in mat.name():     
                        pm.textScrollList("resultField", e=True, a=pieceLod.name()+" has assigned a wrong material: "+mat.name())
                    if "_LODA" not in pieceLod.name() and "mat_livery_0" in mat.name():     
                        pm.textScrollList("resultField", e=True, a=pieceLod.name()+" has assigned a wrong material: "+mat.name())   
    
    # MATCHING UV1-UV2
    shapesList = pm.ls(type="mesh")
    transformList = pm.listRelatives(shapesList, parent=True)
    if transformList:  # Added check for None
        pm.select(transformList, r=True, vis=True)
        
    for piece in piecesList:
        pieceLodsList = pm.ls(piece.name+"*", type="transform")
        for pieceLod in pieceLodsList:
            pieceShape = pm.listRelatives(pieceLod, s=True)
            if not pieceShape:  # Skip if no shape found
                continue
                
            pm.select(pieceShape)
            pm.polyUVSet(cuv=True, uvs='UVChannel_1')
            pm.select(pm.polyListComponentConversion(tuv=True))
            UVValues_map1 = pm.polyEditUV(query=True, relative=False)
            
            pm.select(pieceShape)
            pm.polyUVSet(cuv=True, uvs='UVChannel_2')
            pm.select(pm.polyListComponentConversion(tuv=True))
            UVValues_map2 = pm.polyEditUV(query=True, relative=False)
            
            pm.select(pieceShape)
            
            if UVValues_map1 is None:
                pm.textScrollList("resultField", e=True, a=pieceLod.name()+" UVChannel_1 empty")
    
            if UVValues_map2 is None:
                pm.textScrollList("resultField", e=True, a=pieceLod.name()+" UVChannel_1 and UVChannel_2 not match")
    
            if UVValues_map1 is not None and UVValues_map2 is not None:
                if sum(UVValues_map1) != sum(UVValues_map2):
                    pm.textScrollList("resultField", e=True, a=pieceLod.name()+" UVChannel_1 and UVChannel_2 not match")
                    
    pm.select(d=True)
    
    # UV CHECKING COUNT
    for piece in piecesList:
        pieceLodsList = pm.ls(piece.name+"*", type="transform")
        for pieceLod in pieceLodsList:
            pieceShape = pm.listRelatives(pieceLod, s=True)          
            pieceLodUVcount = pm.polyUVSet(pieceLod, q=True, auv=True)  
            if pieceLodUVcount and len(pieceLodUVcount) < 4:  # Added check for None
                pm.textScrollList("resultField", e=True, a=pieceLod.name()+" has less than 4 UVs channels")


def createlod(self):
    cmds.select(all=True)
    sel = cmds.ls(sl=True)
    
    # Define LOD groups in a list to maintain correct order
    lod_order = ['LODA', 'LODB', 'LODC', 'LODD', 'LODE', 'LODF', 'LODG', 'LODH']
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
        
        if cmds.objExists("Bike_LOD_Group"):
            cmds.delete("Bike_LOD_Group")
        
        cmds.rename("LOD_Group_1", "Bike_LOD_Group")
        cmds.select("Bike_LOD_Group", deselect=True)
     
def aoexport(self):
    """Custom Export FBX"""
    # Use select(all=True) instead of SelectAll for better compatibility
    cmds.select(all=True)
    
    # Combine all objects into a list for cleaner selection
    deselect_objects = [
        "BLINKERS_GLASS*", "BLINKERS*", "MIRROR*", "B_BRAKE*",
        "B_RIM*", "PLATE*", "MUFFLER*", "CHAIN*", "F_RIM*",
        "FR_BRAKE*", "FL_BRAKE*", "EXMANIFOLD*", "B_GEAR*"
    ]
    
    # Deselect all objects at once
    cmds.select(deselect_objects, deselect=True)
    
    # Check for MOUNT objects
    if cmds.objExists("MOUNT*"):
        cmds.select("MOUNT*", deselect=True)

def check_uv(*args):
    """Check and Fix UV"""
    pm.textScrollList("resultField", e=True, ra=True)
    sel = cmds.ls(sl=True)

    if not sel:
        pm.textScrollList("resultField", e=True, a=" Please select mesh to create\\fix UVChannel")
        return

    for pieceLod in sel:
        pm.textScrollList("resultField", e=True, a=pieceLod + " Processing")

        # Get all uv sets with None protection
        uv_sets = pm.polyUVSet(pieceLod, query=True, allUVSets=True) or []

        # Check for map UVs
        map_uv_exists = any(uv.startswith("map") for uv in uv_sets)
        print("'map' UV exists: {0}".format(map_uv_exists))

        # Backup UV4 if exists
        backup_4 = None
        for uv in uv_sets:
            if uv.endswith("_4"):    
                backup_4 = "{0}_backup".format(uv)
                pm.polyUVSet(pieceLod, create=True, uvSet=backup_4)
                pm.polyUVSet(pieceLod, currentUVSet=True, uvSet=uv)
                pm.polyCopyUV(pieceLod, uvSetName=backup_4)
                print("Backed up: {0} -> {1}".format(uv, backup_4))

        # Define UV1
        uv_1 = "UVChannel_1"

        # Backup UV1 if exists
        backup_1 = None
        for uv in uv_sets:
            if uv.endswith("_1"):
                backup_1 = "{0}_backup".format(uv)
                pm.polyUVSet(pieceLod, create=True, uvSet=backup_1)
                pm.polyUVSet(pieceLod, currentUVSet=True, uvSet=uv_1)
                pm.polyCopyUV(pieceLod, uvSetName=backup_1)
                print("Backed up: {0} -> {1}".format(uv, backup_1))

        # Delete UV sets with appropriate conditions
        for uv in uv_sets:
            if map_uv_exists:
                if uv.startswith("UV"):
                    pm.polyUVSet(pieceLod, delete=True, uvSet=uv)
                    print("Deleted UV set: {0}".format(uv))
            else:
                if uv.startswith("UV") and not uv.endswith("_1"):
                    pm.polyUVSet(pieceLod, delete=True, uvSet=uv)
                    print("Deleted UV set: {0}".format(uv))

        # Find and rename map UV if exists
        current_uvs = pm.polyUVSet(pieceLod, query=True, allUVSets=True) or []
        map_uv = next((uv for uv in current_uvs if uv.startswith("map")), None)

        if map_uv_exists and map_uv:
            pm.polyUVSet(pieceLod, rename=True, uvSet=map_uv, newUVSet=uv_1)
            print("Renamed {0} -> {1}".format(map_uv, uv_1))

        # Restore UV1 data if backed up
        if backup_1:
            pm.polyUVSet(pieceLod, currentUVSet=True, uvSet=backup_1)
            pm.polyCopyUV(pieceLod, uvSetName=uv_1)
            print("Restored UV data to: {0}".format(uv_1))

        # Create and setup UV2
        uv_2 = uv_1.replace("_1", "_2")
        pm.polyUVSet(pieceLod, create=True, uvSet=uv_2)
        pm.polyUVSet(pieceLod, currentUVSet=True, uvSet=uv_1)
        pm.polyCopyUV(pieceLod, uvSetName=uv_2)
        print("Created {0} with same data as {1}".format(uv_2, uv_1))
        pm.textScrollList("resultField", e=True, a="{0} match UV_1 and UV_2.".format(pieceLod))

        # Create UV3
        uv_3 = uv_1.replace("_1", "_3")
        pm.polyUVSet(pieceLod, create=True, uvSet=uv_3)
        print("Created {0} (empty)".format(uv_3))
        pm.textScrollList("resultField", e=True, a="{0} clean UV_3.".format(pieceLod))

        # Handle UV4
        if backup_4:
            uv_4 = backup_4.replace("_backup", "")
            pm.polyUVSet(pieceLod, create=True, uvSet=uv_4)
            pm.polyUVSet(pieceLod, currentUVSet=True, uvSet=backup_4)
            pm.polyCopyUV(pieceLod, uvSetName=uv_4)
            print("Restored UV data to: {0}".format(uv_4))
        else:
            uv_4 = uv_1.replace("_1", "_4")
            pm.polyUVSet(pieceLod, create=True, uvSet=uv_4)
            print("Created {0} (empty)".format(uv_4))

def fix_uv(self):
    """Clean up UV backups"""
    pm.textScrollList("resultField", e=True, a="delete backup function")
    sel = cmds.ls(sl=True)

    if not sel:
        pm.textScrollList("resultField", e=True, a=" Please select mesh to create\\fix UVChannel")
        return

    for pieceLod in sel:
        target_uv = {"UVChannel_1", "UVChannel_2", "UVChannel_3", "UVChannel_4"}
        uv_sets = pm.polyUVSet(pieceLod, query=True, allUVSets=True) or []

        for uv in uv_sets:
            if uv not in target_uv:
                pm.polyUVSet(pieceLod, delete=True, uvSet=uv)
                print("Deleted backup: {0}".format(uv))

def printResult(self):
    """Print results to file"""
    pm.select(cl=True)
    resultFilePath = pm.fileDialog(m=1, dm="*.txt", t="Choose where to save the result file")
    
    if resultFilePath is not None:
        if os.path.isfile(resultFilePath):      
            os.chmod(resultFilePath, S_IWUSR|S_IREAD)                       
        with open(resultFilePath, "w") as resultFile:
            resultList = pm.textScrollList("resultField", q=True, ai=True)
            for line in resultList:
                resultFile.write("{0}\r\n".format(str(line)))

def createStatic(lod):
    """Create static LOD"""
    pm.select(cl=True)
    
    # Merge everything
    piecesList = getPiecesList()  # Assuming getPiecesList is defined elsewhere
    for piece in piecesList:
        pieceLod = pm.ls(piece.name + lod, type="transform")
        if pieceLod:  # Changed from len(pieceLod) > 0
            pm.select(pieceLod, add=True)
            
    pm.duplicate()
    pm.polyUnite(n="chassis_MERGED_LOD" + lod, ch=False) 


def UI():
    if cmds.window("win", exists=True):
        cmds.deleteUI("win", window=True)
    
    cmds.window("win", title="R6_AssetChecker")   
    
    height = 20
        
    mainLayout = pm.columnLayout(adjustableColumn=True)
    pm.button(label="CHECK", height=height+10, command=check)
    pm.separator(style="none", height=10)
    
    pm.text(label="Result:", align="left")
    pm.textScrollList("resultField", height=300)
    pm.button(label="Print Result", height=height+10, command=printResult)
    
    pm.separator(style="in", height=20)
    pm.button(label="Create LOD Group", height=height+15, command=createlod)
    pm.separator(style="none", height=10)
    pm.button(label="Check UV", height=height, command=check_uv)
    pm.separator(style="none", height=10)
    pm.button(label="Fix UV", height=height, command=fix_uv)
    pm.separator(style="none", height=10)
    pm.button(label="Export for AO Check", height=height+15, command=aoexport)
    pm.separator(style="none", height=10)
    pm.button(label="Create Merged from LODA", height=height, command=pm.Callback(createStatic, "A"))
    pm.separator(style="none", height=10)
    pm.button(label="Create Merged from LODB", height=height, command=pm.Callback(createStatic, "B"))
    
    cmds.showWindow("win")

if __name__ == "__main__":
    UI()