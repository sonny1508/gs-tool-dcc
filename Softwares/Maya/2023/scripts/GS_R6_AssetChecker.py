import pymel.core as pm
import maya.cmds as cmds
import maya.OpenMaya as api
import maya.mel as mel
import os
from stat import S_IWUSR, S_IREAD


class pieceInfo:
    def __init__(self, name, materialList):
        self.name = name
        self.materialList = materialList


def getPiecesList():
    pm.select(cl=True)
    piecesList =[pieceInfo("MAIN_BODY_LOD", ["mat_livery_0", "mat_livery_1", "mat_mechanics", "mat_cockpit"]),
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
                pieceInfo("R_HANDGUARD_LOD", ["mat_handguard"]),
                pieceInfo("L_HANDGUARD_LOD", ["mat_handguard"]),
                pieceInfo("BARPAD_LOD", ["mat_barpad"]),
                pieceInfo("KEY_LOD", ["mat_cockpit"]),
                pieceInfo("REFLECTOR_LOD", ["mat_livery_0", "mat_livery_1", "mat_mechanics"])]
    
    def addPiece(pieceName, materialsList):
        pieces = pm.ls(pieceName, type="transform")
        for piece in pieces:
            piecesList.append(pieceInfo(piece.name().replace("_LODA", "_LOD"), materialsList))
    
    addPiece("MUFFLER_00*_LODA", ["mat_muffler"])
    addPiece("MOUNT_00*_LODA", ["mat_muffler"])
    addPiece("EXMANIFOLD_00*_LODA", ["mat_exmanifold"])
        
    return piecesList
    

def check(self):
    pm.textScrollList("resultField", e=True, ra=True)
    pm.select(cl=True)
    
    polyCount = {"LODA":200000}                  
    
    matCorrectNameList = ["mat_livery_0", 
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
                          "mat_exmanifold"]
        
    piecesList = getPiecesList()
    
    mandatoryPiecesList = ["MAIN_BODY", "HANDLE", "L_LEVER", "R_LEVER", "L_GRIP", "R_GRIP", "F_TYRE", "B_TYRE", "F_RIM", "B_RIM", "B_RAKE"]
    
    # POLYCOUNT
    for lod, maxTris in polyCount.items():
        geoList = pm.ls("*_"+lod, type="transform")
        if pm.polyEvaluate(geoList, t=True) > maxTris:          
            pm.textScrollList("resultField", e=True, a=lod+" pieces togheter exceeds the polycount of "+str(maxTris - pm.polyEvaluate(geoList, t=True))+" tris")
            
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
            if bikePiece.name in  geo.name():
                if geo[-5:-4] == '_':
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
            if len(pieceShape) > 1:
                pm.textScrollList("resultField", e=True, a=pieceLod.name()+" has multiple shapes")
                
            uvChannelName = ["UVChannel_1", "UVChannel_2", "UVChannel_3", "UVChannel_4"] 
            pieceLodUVs = pm.polyUVSet(pieceLod, q=True, auv=True)            
            if len(pieceLodUVs) > 4:
                pm.textScrollList("resultField", e=True, a=pieceLod.name()+" has more than 4 UVs channels")           
            for uvs in pieceLodUVs: 
                if uvs not in uvChannelName: 
                    pm.textScrollList("resultField", e=True, a=pieceLod.name()+" has wrong UVs channel name: "+uvs)                                       
                    
            shadingList = pm.listConnections(pieceLod.getShape(), type="shadingEngine") 
            shadingList = list(set(shadingList)) # levo i doppioni
            for shading in shadingList:
                if len(pm.listConnections(shading.surfaceShader)) == 0:
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
    
    # matching UV1-UV2
    shapesList = pm.ls(type="mesh")
    transformList = pm.listRelatives(shapesList,parent=True)
    pm.select(transformList, r=True, vis=True)
    for piece in piecesList:
        pieceLodsList = pm.ls(piece.name+"*", type="transform")
        for pieceLod in pieceLodsList:
            pieceShape = pm.listRelatives(pieceLod, s=True)
            pm.select(pieceShape)
            pm.polyUVSet(cuv=True, uvs='UVChannel_1')
            pm.select(pm.polyListComponentConversion(tuv = True))
            UVValues_map1 = pm.polyEditUV(query = True, relative=False)
            pm.select(pieceShape)
            pm.polyUVSet(cuv=True, uvs='UVChannel_2')
            pm.select(pm.polyListComponentConversion(tuv = True))
            UVValues_map2 = pm.polyEditUV(query = True, relative=False)
            pm.select(pieceShape)
            if UVValues_map1 == None:
                pm.textScrollList("resultField", e=True, a=pieceLod.name()+" UVChannel_1 empty")
    
            if UVValues_map2 == None:
                pm.textScrollList("resultField", e=True, a=pieceLod.name()+" UVChannel_1 and UVChannel_2 not match")
    
            if not UVValues_map1 == None:
                if not UVValues_map2 == None:
                    if sum(UVValues_map1) != sum(UVValues_map2):
                        pm.textScrollList("resultField", e=True, a=pieceLod.name()+" UVChannel_1 and UVChannel_2 not match")
    pm.select(d=True)
    
    
     # UV checking count
    
    for piece in piecesList:
        pieceLodsList = pm.ls(piece.name+"*", type="transform")
        for pieceLod in pieceLodsList:
            pieceShape = pm.listRelatives(pieceLod, s=True)          
            pieceLodUVcount = pm.polyUVSet(pieceLod, q=True, auv=True)  
            if len(pieceLodUVcount) < 4:
                pm.textScrollList("resultField", e=True, a=pieceLod.name()+" has less than 4 UVs channels")
     

     #Everything OK
     
     
#Auto Create LOD Group
def createlod(self):
    cmds.SelectAll()
    sel = cmds.ls(sl = True)
    lodGrp0 = []
    lodGrp1 = []
    lodGrp2 = []
    lodGrp3 = []
    lodGrp4 = []
    lodGrp5 = []
    lodGrp6 = []
    lodGrp7 = []

    for obj in sel:
        if "LODA" in obj:
            lodGrp0.append(obj)
        
        if "LODB" in obj:
            lodGrp1.append(obj)
        
        if "LODC" in obj:
            lodGrp2.append(obj)
        
        if "LODD" in obj:
            lodGrp3.append(obj)
        
        if "LODE" in obj:
            lodGrp4.append(obj)
        
        if "LODF" in obj:
            lodGrp5.append(obj)
        
        if "LODG" in obj:
            lodGrp6.append(obj)
        
        if "LODH" in obj:
            lodGrp7.append(obj)
        
        
    Grp0 = cmds.group(lodGrp0, name = "LOD_0")
    Grp1 = cmds.group(lodGrp1, name = "LOD_1")
    if len(lodGrp2) == 0:
        None
    else:
        Grp2 = cmds.group(lodGrp2, name = "LOD_2")
    
    if len(lodGrp3) == 0:
        None
    else:
        Grp3 = cmds.group(lodGrp3, name = "LOD_3")
    
    if len(lodGrp4) == 0:
        None
    else:
        Grp4 = cmds.group(lodGrp4, name = "LOD_4")
    
    if len(lodGrp5) == 0:
        None
    else:
        Grp5 = cmds.group(lodGrp5, name = "LOD_5")
    
    if len(lodGrp6) == 0:
        None
    else:
        Grp6 = cmds.group(lodGrp6, name = "LOD_6")
    
    if len(lodGrp7) == 0:
        None
    else:
        Grp7 = cmds.group(lodGrp7, name = "LOD_7")

    cmds.select("LOD_0", add=True)
    cmds.select("LOD_1", add=True)
    if cmds.objExists("LOD_2"):
        cmds.select("LOD_2", add=True)
    if cmds.objExists("LOD_3"):
        cmds.select("LOD_3", add=True)
    if cmds.objExists("LOD_4"):
        cmds.select("LOD_4", add=True)
    if cmds.objExists("LOD_5"):
        cmds.select("LOD_5", add=True)
    if cmds.objExists("LOD_6"):
        cmds.select("LOD_6", add=True)
    if cmds.objExists("LOD_7"):
        cmds.select("LOD_7", add=True)

    cmds.LevelOfDetailGroup()
    cmds.rename("LOD_Group_1", "Bike_LOD_Group")
    cmds.select("Bike_LOD_Group", deselect=True)
     
#Custom Export FBX 
def aoexport(self):

    cmds.SelectAll()
    cmds.select("BLINKERS_GLASS" + "*",
            "BLINKERS" + "*",
            "MIRROR" + "*",
            "B_BRAKE" + "*",
            "B_RIM" + "*",
            "PLATE" + "*",
            "MUFFLER" + "*",
            "CHAIN" + "*",
            "F_RIM" + "*",
            "FR_BRAKE" + "*",
            "FL_BRAKE" + "*",
            "EXMANIFOLD" + "*",
            "B_GEAR" + "*",
            deselect=True)
    if cmds.objExists("MOUNT"+"*"):
        cmds.select("MOUNT"+"*", deselect=True)
    

# Check and Fix UV

def check_uv(*args):
    pm.textScrollList("resultField", e=True, ra=True)

    #piecesList = getPiecesList()
    sel = cmds.ls(sl = True)
    #UVSort = ['UVChannel_1', 'UVChannel_2', 'UVChannel_3', 'UVChannel_4']

    if not sel:
        pm.textScrollList("resultField", e=True, a=" Please select mesh to create\\fix UVChannel")
        return

    for pieceLod in sel:
        pm.textScrollList("resultField", e=True, a=pieceLod + "Processing")

        # Get all uv sets
        uv_sets = pm.polyUVSet(pieceLod, query=True, allUVSets=True) or []

        # Step 01: Detect if starts with "map" exists
        map_uv_exists = any(uv.startswith("map") for uv in uv_sets)
        print(f"'map' UV exists: {map_uv_exists}")

        # Step 02: Backup _4 only if it exists
        backup_4 = None
        for uv in uv_sets:
            if uv.endswith("_4"):    
                backup_4 = uv + "_backup"
                pm.polyUVSet(pieceLod, create=True, uvSet=backup_4)
                pm.polyUVSet(pieceLod, currentUVSet=True, uvSet=uv)
                pm.polyCopyUV(pieceLod, uvSetName=backup_4)
                print(f"Backed up: {uv} -> {backup_4}")

        # Step 03: Handle cases based on "map" existence
        uv_1 = str("UVChannel_1") #backup_4.replace("_4_backup", "_1") 

        backup_1 = None
        for uv in uv_sets:
            if uv.endswith("_1"):
                backup_1 = uv + "_backup"
                pm.polyUVSet(pieceLod, create=True, uvSet=backup_1)
                pm.polyUVSet(pieceLod, currentUVSet=True, uvSet=uv_1)
                pm.polyCopyUV(pieceLod, uvSetName=backup_1)
                print(f"Backed up: {uv} -> {backup_1}")

        # Delete all UV sets starting with UV
        for uv in uv_sets:
            if map_uv_exists:
                if uv.startswith("UV"):
                    pm.polyUVSet(pieceLod, delete=True, uvSet=uv)
                    print(f"Deleted UV set: {uv}")
            else:
                if uv.startswith("UV") and not uv.endswith("_1"):
                    pm.polyUVSet(pieceLod, delete=True, uvSet=uv)
                    print(f"Deleted UV set: {uv}")

        # Rename starts with "map" to match ends with _1
        map_uv = next((uv for uv in pm.polyUVSet(pieceLod, query=True, allUVSets=True) if uv.startswith("map")), None)
        # new_name = backup_1.replace("_backup", "")

        if map_uv_exists:
            if map_uv:
                pm.polyUVSet(pieceLod, rename=True, uvSet=map_uv, newUVSet=uv_1)
                print(f"Renamed {map_uv} -> {uv_1}")

        if backup_1:
            pm.polyUVSet(pieceLod, currentUVSet=True, uvSet=backup_1)
            pm.polyCopyUV(pieceLod, uvSetName=uv_1)
            print(f"Restored UV data to: {uv_1}")

        # Create _2 and copy _1's data
        uv_2 = uv_1.replace("_1", "_2")
        pm.polyUVSet(pieceLod, create=True, uvSet=uv_2)
        pm.polyUVSet(pieceLod, currentUVSet=True, uvSet=uv_1)
        pm.polyCopyUV(pieceLod, uvSetName=uv_2)
        print(f"Created {uv_2} with same data as {uv_1}")
        pm.textScrollList("resultField", e=True, a=pieceLod+"match UV_1 and UV_2.")

        # Create _3 as empty
        uv_3 = uv_1.replace("_1", "_3")
        pm.polyUVSet(pieceLod, create=True, uvSet=uv_3)
        print(f" Created {uv_3} (empty)")
        pm.textScrollList("resultField", e=True, a=pieceLod+"clean UV_3.")

        # Restore _4 if it was backed up
        if backup_4:
            uv_4 = backup_4.replace("_backup", "")
            pm.polyUVSet(pieceLod, create=True, uvSet=uv_4)
            pm.polyUVSet(pieceLod, currentUVSet=True, uvSet=backup_4)
            pm.polyCopyUV(pieceLod, uvSetName=uv_4)
            print(f"Restored UV data to: {uv_4}")

        else:
            uv_4 = uv_1.replace("_1", "_4")
            pm.polyUVSet(pieceLod, create=True, uvSet=uv_4)
            print(f" Created {uv_4} (empty)")

        # Delete backup UV sets


def fix_uv(self):
    pm.textScrollList("resultField", e=True, a="delete backup function")
    sel = cmds.ls(sl = True)

    if not sel:
        pm.textScrollList("resultField", e=True, a=" Please select mesh to create\\fix UVChannel")
        return

    for pieceLod in sel:
        target_uv = {"UVChannel_1", "UVChannel_2", "UVChannel_3", "UVChannel_4"}
        uv_sets = pm.polyUVSet(pieceLod, query=True, allUVSets=True) or []

        for uv in uv_sets:
            if uv not in target_uv:
                pm.polyUVSet(pieceLod, delete=True, uvSet=uv)
                print(f"Deleted backup: {uv}")


def printResult(self):
    pm.select(cl=True)
    resultFilePath = pm.fileDialog(m=1, dm="*.txt", t="Choose where to save the result file")
    if not resultFilePath == None:
        if os.path.isfile(resultFilePath):      
            os.chmod(resultFilePath, S_IWUSR|S_IREAD)                       
        resultFile = open(resultFilePath, "w") 
        resultList = pm.textScrollList("resultField", q=True, ai=True)
        for line in resultList:
            resultFile.write(str(line)+"\r\n")
        resultFile.close()


def createStatic(lod):
    pm.select(cl=True)
        
    # MERGIO TUTTO
    piecesList = getPiecesList()
    for piece in piecesList:
        pieceLod = pm.ls(piece.name+lod, type="transform")
        if len(pieceLod) > 0:
            pm.select(pieceLod, add=True)
    pm.duplicate()
    pm.polyUnite(n="chassis_MERGED_LOD"+lod, ch=False) 


def UI():
    if cmds.window("win", exists=True):
        cmds.deleteUI("win", window=True)
    
    cmds.window("win", t="R6_AssetChecker")   
    
    height = 20
        
    mainLayout = pm.columnLayout(adj=True)  
    pm.button(l="CHECK", h=height+10, c=check)  
    pm.separator(style="none", h=10)
    
    pm.text(l="Result:", al="left")
    pm.textScrollList("resultField", h=300)
    pm.button(l="Print Result", h=height+10, c=printResult)
    
    pm.separator(style="in", h=20)
    pm.button(l="Create LOD Group", h=height+15, c = createlod)
    pm.separator(style="none", h=10)
    pm.button(l="Check UV", h=height, c = check_uv)
    pm.separator(style="none", h=10)
    pm.button(l="Fix UV", h=height, c = fix_uv)
    pm.separator(style="none", h=10)
    pm.button(l="Export for AO Check", h=height+15, c = aoexport)
    pm.separator(style="none", h=10)
    pm.button(l="Create Merged from LODA", h=height, c=pm.Callback(createStatic, "A"))
    pm.separator(style="none", h=10)
    pm.button(l="Create Merged from LODB", h=height, c=pm.Callback(createStatic, "B"))
    
    cmds.showWindow('win')
UI()