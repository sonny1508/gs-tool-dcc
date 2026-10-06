import pymel.core as pm
import maya.cmds as cmds
import os
from stat import S_IWUSR, S_IREAD


class pieceInfo:
	def __init__(self, name, materialList):
		self.name = name
		self.materialList = materialList


def getPiecesList():
	pm.select(cl=True)
	piecesList =[pieceInfo("MAIN_BODY_LOD", ["mat_livery", "mat_livery_lod", "mat_mechanics", "mat_cockpit"]),
				pieceInfo("F_SUSP_LOD", ["mat_livery", "mat_livery_lod", "mat_mechanics", "mat_cockpit"]),
				pieceInfo("SUSP_LOD", ["mat_mechanics"]),
				pieceInfo("B_RAKE_LOD", ["mat_livery", "mat_livery_lod", "mat_mechanics", "mat_cockpit"]),
				pieceInfo("F_RAKE_LOD", ["mat_livery", "mat_livery_lod", "mat_mechanics", "mat_cockpit"]),
				pieceInfo("F_ARM_LOD", ["mat_mechanics"]),
				pieceInfo("HANDLE_LOD", ["mat_cockpit", "mat_mechanics", "mat_livery"]),
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
				pieceInfo("F_BRAKE_LOD", ["mat_brake"]),
				pieceInfo("GAUGE_LOD", ["mat_gauge"]),
				pieceInfo("GAUGE_GLASS_LOD", ["mat_glass"]),
				pieceInfo("RPM_NEEDLE_LOD", ["mat_lights"]),
				pieceInfo("SPD_NEEDLE_LOD", ["mat_lights"]),
				pieceInfo("PLATE_LOD", ["mat_livery", "mat_livery_lod", "mat_mechanics"]),
				pieceInfo("PLATE_GLASS_LOD", ["mat_glass"]),
				pieceInfo("PLATE_GLASS_TINT_LOD", ["mat_glasstint"]),
				pieceInfo("BLINKERS_LOD", ["mat_livery", "mat_livery_lod", "mat_mechanics"]),
				pieceInfo("BLINKERS_GLASS_LOD", ["mat_glass"]),
				pieceInfo("BLINKERS_GLASS_TINT_LOD", ["mat_glasstint"]),
				pieceInfo("FOOTPEGS_LOD", ["mat_mechanics"]),
				pieceInfo("MIRROR_LOD", ["mat_livery", "mat_livery_lod", "mat_mechanics"]),
				pieceInfo("MIRROR_GLASS_LOD", ["mat_glass"]),
				pieceInfo("MIRROR_GLASS_TINT_LOD", ["mat_glasstint"]),
				pieceInfo("MIRROR_VIEW_LOD", ["mat_mirror_view"]),
				pieceInfo("F_GLASS_LOD", ["mat_glass"]),
				pieceInfo("GLASS_LOD", ["mat_glass"]),
				pieceInfo("INNER_GLASS_LOD", ["mat_innerglass"]),
				pieceInfo("F_GLASS_TINT_LOD", ["mat_glasstint"]),
				pieceInfo("F_GLASS_DECAL_LOD", ["mat_glassdecal"]),
				pieceInfo("LIGHTS_LOD", ["mat_lights"]),
				pieceInfo("F_LIGHT_LOD", ["mat_lights"]),
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
				pieceInfo("GEAR_LOD", ["mat_brake"]),
				pieceInfo("B_GEAR_LOD", ["mat_brake"]),
				pieceInfo("CHAIN_LOD", ["mat_chain"]),
				pieceInfo("HANDLE_BRAKE_CABLE_LOD", ["mat_mechanics"]),
				pieceInfo("F_SUSP_BRAKE_CABLE_LOD", ["mat_mechanics"]),
				pieceInfo("B_BRAKE_CABLE_LOD", ["mat_mechanics"]),
				pieceInfo("KICKSTAND_LOD", ["mat_mechanics"]),
				pieceInfo("R_HANDGUARD_LOD", ["mat_handguard"]),
				pieceInfo("L_HANDGUARD_LOD", ["mat_handguard"]),
				pieceInfo("BARPAD_LOD", ["mat_barpad"]),
				pieceInfo("KEY_LOD", ["mat_cockpit"]),
				pieceInfo("REFLECTOR_LOD", ["mat_livery", "mat_livery_lod", "mat_mechanics"])]
	
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
	
	polyCount = {"LODA":200000, 
	             "LODB":70000,
	             "LODC":35000,
	             "LODD":17500,
	             "LODE":9000,
	             "LODF":5000,
	             "LODG":2500,
	             "LODH":1250}
	
	matCorrectNameList = ["mat_livery",
	                      "mat_livery_lod",
	                      "mat_mechanics",  
	                      "mat_cockpit", 
	                      "mat_chain", 
	                      "mat_gauge", 
	                      "mat_glass",
						  					"mat_innerglass",
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
	                      "mat_exmanifold"]
		
	piecesList = getPiecesList()
	
	mandatoryPiecesList = ["MAIN_BODY", "HANDLE", "L_LEVER", "R_LEVER", "L_GRIP", "R_GRIP", "F_TYRE", "B_TYRE", "F_RIM", "B_RIM", "B_RAKE"]
	
	# POLYCOUNT
	#for lod, maxTris in polyCount.iteritems():
		#geoList = pm.ls("*_"+lod, type="transform")
		#if pm.polyEvaluate(geoList, t=True) > maxTris:
			#pm.textScrollList("resultField", e=True, a=lod+" pieces togheter exceeds the polycount of "+str(maxTris - pm.polyEvaluate(geoList, t=True))+" tris")
			
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
				firstLOD = ["LODA", "LODB", "LODC", "LODD"]
				for flod in firstLOD:
					if mat.name() not in piece.materialList:
						if flod in pieceLod.name():
							pm.textScrollList("resultField", e=True, a=pieceLod.name()+" has assigned a wrong material: "+mat.name())
				secondLOD = ["LODE", "LODF", "LODG", "LODH"]
				for slod in secondLOD:
					if mat.name() not in piece.materialList:
						if slod in pieceLod.name() and "LIGHTS" not in pieceLod.name()  and "mat_livery_lod" not in mat.name():
							pm.textScrollList("resultField", e=True, a=pieceLod.name()+" has assigned a wrong material: "+mat.name())
				if mat.name() not in piece.materialList:
					if "LIGHTS" in pieceLod.name() :
						pm.textScrollList("resultField", e=True,a=pieceLod.name() + " has assigned a wrong material: " + mat.name())

	
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
	
	# CREO IL GLASS TINT
	if pm.objExists("mat_glasstint")==False:
		pm.shadingNode("lambert", n="mat_glasstint", asShader=True)

	glassList = pm.ls("*GLASS*LOD"+lod, type="transform")
	for glass in glassList:			
		glassSplittedName = glass.name().split("_LOD")
		glassTintName = glassSplittedName[0]+"_TINT_LOD"+glassSplittedName[1]	
		pm.duplicate(glass, n=glassTintName)
		pm.select(glassTintName)
		pm.hyperShade(assign="mat_glasstint") 	
		pm.select(cl=True)			
	
	# MERGIO TUTTO
	piecesList = getPiecesList()
	for piece in piecesList:
		pieceLod = pm.ls(piece.name+lod, type="transform")
		if len(pieceLod) > 0:
			pm.select(pieceLod, add=True)
	pm.duplicate()
	pm.polyUnite(n="STATIC_BIKE_LOD"+lod, ch=False)	


def UI():
	if cmds.window("MGP26_Asset_Checker", exists=True):
		cmds.deleteUI("MGP26_Asset_Checker", window=True)
	
	cmds.window("MGP26_Asset_Checker", title="MGP26 Asset Checker", w=720, h=360, sizeable=False)	
	
	height = 40
		
	mainLayout = pm.columnLayout(adj=True)	
	
	pm.button(l="CHECK", h=height+10, c=check)	
	pm.separator(style="none", h=10)
	
	pm.text(l="Result:", al="left")
	pm.textScrollList("resultField", h=500)
	pm.button(l="Print Result", h=height-10, c=printResult)
	
	pm.separator(style="in", h=20)
	
	pm.button(l="Create Static from LODA", h=height, c=pm.Callback(createStatic, "A"))
	pm.separator(style="none", h=10)
	pm.button(l="Create Static from LODB", h=height, c=pm.Callback(createStatic, "B"))
	
	cmds.showWindow("MGP26_Asset_Checker")

if __name__ == "__main__":
    UI()