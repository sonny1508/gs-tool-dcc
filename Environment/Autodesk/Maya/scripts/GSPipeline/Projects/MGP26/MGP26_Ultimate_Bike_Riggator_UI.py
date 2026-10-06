########### ULTIMATE BIKE RIGGATOR FROM HELL ######### BY ########### DAVIDE LOVECCHIO ################################
import pymel.core as pm
import maya.cmds as cmds
import maya.OpenMaya as api
import maya.mel as mel
import os
from stat import S_IWUSR, S_IREAD

# Default path for bikeNulls file (same directory as this script)
SCRIPT_DIR = os.path.join(cmds.internalVar(uad=True), "scripts", "GSPipeline", "05_Projects", "Motogp26")
DEFAULT_BIKE_NULLS_PATH = os.path.join(SCRIPT_DIR, "MotoGP20_bikeNulls.ma")
	
################################################### SERVICE METHODS ###################################################

def findNearby(point, Vol_BB, max_scale_val):
    mode = 'vertex'

    #convert an object to an API point (Get it's worldspace s)
    if isinstance(point, str):
        point = pointFromObject(point)
    point = Point(point)

    meshList = buildMeshList()
    selection  = api.MSelectionList()

    for mesh in meshList:
        matrix = api.MMatrix(mesh.inclusiveMatrix())
        meshObj = api.MFnMesh(mesh)
        meshBB = meshObj.boundingBox()
        meshBB.transformUsing(matrix)

        pointBB = api.MBoundingBox(Point(Vol_BB[0], Vol_BB[1], Vol_BB[2]),Point(Vol_BB[3], Vol_BB[4], Vol_BB[5]))

        #if the mesh is inside the bounding box for the point+tolerance
        if meshBB.contains(point) or meshBB.intersects(pointBB):
            if mode in ['vertex', 'cv', 'point']:
                iter = api.MItGeometry(mesh)
                while not iter.isDone():
                    vert = iter.position(api.MSpace.kWorld)
                    if pointBB.contains(vert):
                        if (point-vert).length()<max_scale_val:
                            selection.add(mesh, iter.currentItem())
                    iter.next()
            else:
                pass
    matching = []
    selection.getSelectionStrings(matching)
    return matching

def buildMeshList():
    meshList = []

    iter = api.MItDag(api.MItDag.kDepthFirst, api.MFn.kMesh)
    while not iter.isDone():
        dagPath = api.MDagPath()
        iter.getPath(dagPath)
        dagPath.extendToShape()
        #if not dagPath.name.endswith('Orig'):
        meshList.append(dagPath)
        iter.next()
    return meshList

#DEPS#
class Point(api.MPoint, object):
    def __init__(self, x=0, y=0, z=0):
        #allow point to take a single tuple, or 3 floats, or wrap an existing MVector
        if isinstance(x, api.MPoint) or isinstance(x, api.MVector):
            super(Point, self).__init__(x)
            return

        if isinstance(x, tuple) or isinstance(x, list):
            super(Point, self).__init__(x[0], x[1], x[2])
        else:
            api.MPoint.__init__(self, x, y, z)

    def __str__(self):
        return '(%g, %g, %g)'%(self.x, self.y, self.z)
    def __repr__(self):
        return '<<MPoint (%g, %g, %g)>>'%(self.x, self.y, self.z)

    def asTuple(self):
        return (self.x, self.y, self.z)

def pointFromObject(object):
    pos = pm.xform(object, q=True, ws=True, t=True)
    return Point(pos[0], pos[1], pos[2])


def if_inside_mesh(VtxPoint,VolShape, dir):
    sel = api.MSelectionList()
    dag = api.MDagPath()

    #replace torus with arbitrary shape name
    sel.add(VolShape)
    sel.getDagPath(0,dag)

    mesh = api.MFnMesh(dag)

    VtxPoint = api.MFloatPoint(*VtxPoint)
    dir = api.MFloatVector(*dir)
    farray = api.MFloatPointArray()

    mesh.allIntersections(
            VtxPoint, dir,
            None, None,
            False, api.MSpace.kWorld,
            10000, False,
            None, # replace none with a mesh look up accelerator if needed
            False,
            farray,
            None, None,
            None, None,
            None
        )
    return farray.length()%2 == 1


def skinVolume(vol, mesh, jnt):
	volPos = pointFromObject(vol)
	volBb = pm.xform(vol, q=True, bb=True)
	maxBbSize = max([abs(x) for x in volBb])
	vertices = findNearby(volPos, volBb, maxBbSize)
	verticesToSkin = []
	volShape = str(pm.ls(vol, type="transform")[0].getShape())
	for vtx in vertices:
		vtxPoint = pm.xform(vtx, q=True, ws=True, t=True)
		if if_inside_mesh(vtxPoint, volShape, dir=(1.0, 0.0, 0.0)) and mesh in str(vtx):
			verticesToSkin.append(vtx)
	if len(verticesToSkin) > 0:
		pm.skinPercent(mesh+"_SK", verticesToSkin, tv=[(jnt, 1)])


def aim(obj, objToAim, aimDir):
	pm.select(objToAim)
	pm.select(obj, tgl=True)
	aimTemp = pm.aimConstraint(offset=(0,0,0), weight=1, aimVector=aimDir, upVector=(0,0,1), worldUpType="scene")
	pm.delete(aimTemp)
	pm.select(cl=True)

	
def positioningVolume(volumeName, null, color, scale, pos=None):
	if getButtonState(null):
		if pm.objExists(volumeName) == False:
			volume = pm.polyCube(n=volumeName, cuv=0, ch=False)[0]
			pm.scale(volume, scale)
			pm.select(volume)
			pm.select(null, tgl=True)
			pm.parent()
			volume.tx.set(0)
			volume.ty.set(0)
			volume.tz.set(0)
			volume.rx.set(0)
			volume.ry.set(0)
			volume.rz.set(0)
			pm.parent(w=True)
			
			if not pos == None: # eventuale offset
				volume.tx.set(pos[0])
				volume.ty.set(pos[1])
				volume.tz.set(pos[2])
			
			pm.shadingNode("lambert", n="mat_"+volume.name(), asShader=True)
			pm.setAttr("mat_"+volume.name() + ".color", color)
			pm.setAttr("mat_"+volume.name() + ".transparency", [0.5,0.5,0.5])
			pm.select(volume)
			pm.hyperShade(assign="mat_"+volume.name())
			pm.select(cl=True)
			
			pm.editDisplayLayerMembers("Nulls_To_Be_Positioned", volumeName, nr=True)
			volumeGrp = next(vol for vol in volumeGrpList if vol.volumeName == volumeName)
			pm.checkBox(volumeGrp.activeCheckBox, e=True, en=True, v=True)
			pm.button(volumeGrp.blockButton, e=True, en=True, bgc=redColor)
			pm.button(volumeGrp.selectButton, e=True, en=True)
			
		else:
			print("Volume for " + str(null) + " already exist")	


def jntRotateToOrient(jnt):
	jnt.jox.set(jnt.rx.get())
	jnt.joy.set(jnt.ry.get())
	jnt.joz.set(jnt.rz.get())
	jnt.rx.set(0)
	jnt.ry.set(0)
	jnt.rz.set(0)


def positioningJnt(jnt, null):
	pm.select(null)
	pm.select(jnt, tgl=True)
	const = pm.parentConstraint(mo=False, w=1)
	pm.delete(const)	
	jntRotateToOrient(jnt)
	pm.select(cl=True)

	
def aimJnt(jnt, jntToAim, aimDir):
	pm.select(jntToAim)
	pm.select(jnt, tgl=True)
	aimConst = pm.aimConstraint(offset=(0,0,0), weight=1, aimVector=(aimDir), upVector=(0,0,1), worldUpType="none")
	pm.delete(aimConst)
	jntRotateToOrient(pm.ls(jnt)[0])

	
def parent(son, father):
	pm.select(son)
	pm.select(father, tgl=True)
	pm.parent()
	pm.select(cl=True)


def createArmBones(arm, armEnd, armAim, father, aimFather, aimAxis):
	aimJnt(arm, armEnd, aimAxis)
	parent(arm, father)
	parent(armEnd, arm)
	pm.ls(armEnd)[0].jox.set(0)
	pm.ls(armEnd)[0].joy.set(0)
	pm.ls(armEnd)[0].joz.set(0)
	pm.select(armEnd)
	pm.duplicate(n=armAim)
	pm.ls(armAim)[0].radius.set(2)
	parent(armAim, aimFather)


def alignBone(target, source, axis):
	parent(target, source)
	pm.setAttr(target+"."+axis, 0)
	pm.parent(target, w=True)
	pm.select(cl=True)


def ShowAll():
	pm.showHidden(all=True)
	layers = cmds.ls(long=True, type="displayLayer")
	#for l in layers[1:]: 
	#	if l.find("defaultLayer") == -1: 
	#		cmds.setAttr("%s.visibility" % l, True)
	for l in layers:
		if not "defaultLayer" in l:
			pm.delete(l)

			
def cleanUp():
	# prima di freezare elimino eventuali keyframe
	if pm.objExists("*_rotate*"):
		pm.delete("*_rotate*")
	if pm.objExists("*_translate*"): 
		pm.delete("*_translate*")
	if pm.objExists("*_scale*"):
		pm.delete("*_scale*")
	if pm.objExists("file*"):
		pm.delete("file*")		
	if pm.objExists("*Constraint*"):
		pm.delete("*Constraint*")
	pm.select("*_LOD*")
	pm.delete(ch=True)
	pm.select(cl=True)


# faccio un instanziazione per ogni NULL, che avra' come properties il nome del null, i 2 buttons, l'eventuale checkbox, quale delle due colonne dell'UI occupera' e se ha null figli
class NullGrp:		
	blockButton = None
	selectButton = None	
	def __init__(self, nullName, isCheckBoxAllowed, col, sons=None):
		self.nullName = nullName
		self.checkBoxLabel = (nullName.lower()[5:]).replace("_", " ").title() # la label per il checkbox la ottengo riformattando il nome del null che inserisco (rendo tutto minuscono, taglio via i primi 5 caratteri, quindi 'null_', sostotuisco l'underscore con lo spazio e con il metodo title rendo le prime lettere maiuscole)	
		self.isCheckBoxAllowed = isCheckBoxAllowed
		if isCheckBoxAllowed:
			self.activeCheckBox = None	
		self.col = col
		self.sons = sons

class VolumeGrp:
	blockButton = None
	selectButton = None	
	activeCheckBox = None
	def __init__(self, volumeName, geoPart, influence):
		self.volumeName = volumeName
		self.geoPart = geoPart
		self.influence = influence
	
redColor = [1.0, 0.0, 0.0]
greenColor = [0.0, 1.0, 0.0]
greyColor = [0.3, 0.3, 0.3]

####################################################################################################################### 

# NULLS
def instantiateNullGrpClass():
	global nullGrpList
	nullGrpList = [NullGrp("NULL_HANDLE", False, 0), NullGrp("NULL_L_LEVER", False, 0), NullGrp("NULL_R_LEVER", False, 0), NullGrp("NULL_L_GRIP", False, 0), NullGrp("NULL_R_GRIP", False, 0), NullGrp("NULL_F_WHEEL", False, 0), NullGrp("NULL_B_WHEEL", False, 0), NullGrp("NULL_GEAR", True, 1), NullGrp("NULL_B_RAKE", False, 0), NullGrp("NULL_DAMPER", True, 1, ["NULL_DAMPER_SPRING", "NULL_DAMPER_RAKE"]), NullGrp("NULL_DAMPER_SPRING", False, 1), NullGrp("NULL_DAMPER_RAKE", False, 1), NullGrp("NULL_HANDLE_DAMPER", True, 1), NullGrp("NULL_HANDLE_DAMPER_PISTON", False, 1), NullGrp("NULL_CLUTCH", True, 1)]


def getButtonColor(nullName):
	if "Nulls_To_Be_Positioned" in pm.listConnections(nullName):
		return redColor
	elif "Nulls_Blocked" in pm.listConnections(nullName):
		return greenColor
	else:
		return greyColor


def getButtonState(nullName):
	if "Nulls_To_Be_Positioned" in pm.listConnections(nullName) or "Nulls_Blocked" in pm.listConnections(nullName):
		return True
	else:
		return False	


def getCheckBoxState(nullName):
	if "Nulls_To_Be_Positioned" in pm.listConnections(nullName) or "Nulls_Blocked" in pm.listConnections(nullName) or "Nulls_Deflag_Active_Red" in pm.listConnections(nullName) or "Nulls_Deflag_Active_Green" in pm.listConnections(nullName):
		return True
	else:
		return False	


def getCheckBoxValue(nullName):
	if "Nulls_To_Be_Positioned" in pm.listConnections(nullName) or "Nulls_Blocked" in pm.listConnections(nullName) or "Nulls_Flag_Unactive_Red" in pm.listConnections(nullName) or "Nulls_Flag_Unactive_Green" in pm.listConnections(nullName):
		return True
	else:
		return False	


def deflagNullLayer(nullName):
	if "Nulls_To_Be_Positioned" in pm.listConnections(nullName):
		return "Nulls_Deflag_Active_Red"
	elif "Nulls_Blocked" in pm.listConnections(nullName):
		return "Nulls_Deflag_Active_Green"
		

def deflagSonNullLayer(nullName):
	if "Nulls_To_Be_Positioned" in pm.listConnections(nullName):
		return "Nulls_Flag_Unactive_Red"
	elif "Nulls_Blocked" in pm.listConnections(nullName):
		return "Nulls_Flag_Unactive_Green"
	elif "Nulls_Deflag_Active_Red" in pm.listConnections(nullName):
		return "Nulls_Deflag_Unactive_Red"
	elif "Nulls_Deflag_Active_Green" in pm.listConnections(nullName):
		return "Nulls_Deflag_Unactive_Green"	
				

def flagNullLayer(nullName):
	if "Nulls_Deflag_Active_Red" in pm.listConnections(nullName):
		return "Nulls_To_Be_Positioned"
	elif "Nulls_Deflag_Active_Green" in pm.listConnections(nullName):
		return "Nulls_Blocked"
		

def flagSonNullLayer(nullName):
	if "Nulls_Flag_Unactive_Red" in pm.listConnections(nullName):
		return "Nulls_To_Be_Positioned"
	elif "Nulls_Flag_Unactive_Green" in pm.listConnections(nullName):
		return "Nulls_Blocked"
	elif "Nulls_Deflag_Unactive_Red" in pm.listConnections(nullName):
		return "Nulls_Deflag_Active_Red"
	elif "Nulls_Deflag_Unactive_Green" in pm.listConnections(nullName):
		return "Nulls_Deflag_Active_Green"				
		

# DISATTIVO I NULL
def unactiveNull(nullGrp):
	pm.undoInfo(st=False) # impedisco di undare queste operazioni attivando e poi disattivando la funzione di undo
	
	# disattivo i buttons del null		
	pm.editDisplayLayerMembers(deflagNullLayer(nullGrp.nullName), nullGrp.nullName, nr=True)
	pm.button(nullGrp.blockButton, edit=True, en=False, bgc=greyColor)
	pm.button(nullGrp.selectButton, edit=True, en=False)		
	
	# se il null ha altri null che dipendono da lui, disattivo il loro eventuale checkbox e i loro button
	if nullGrp.sons != None:
		for sonName in nullGrp.sons:
			son = next(null for null in nullGrpList if null.nullName == sonName) 
			pm.editDisplayLayerMembers(deflagSonNullLayer(son.nullName), son.nullName, nr=True)	
			pm.button(son.blockButton, edit=True, en=False, bgc=greyColor)
			pm.button(son.selectButton, edit=True, en=False)
			if son.isCheckBoxAllowed:
				pm.checkBox(son.activeCheckBox, e=True, en=False)				
			
	pm.undoInfo(st=True)


# RIATTIVO I NULL	
def activeNull(nullGrp):
	pm.undoInfo(st=False)
	  	
	pm.editDisplayLayerMembers(flagNullLayer(nullGrp.nullName), nullGrp.nullName, nr=True)			
	pm.button(nullGrp.blockButton, edit=True, en=True, bgc=getButtonColor(nullGrp.nullName))
	pm.button(nullGrp.selectButton, edit=True, en=True)		
	
	# se il null da riattivare ha dei figli, riattivo il loro checkbox e controllo se i buttons sono da riattivare o no
	if nullGrp.sons != None:
		for sonName in nullGrp.sons:
			son = next(null for null in nullGrpList if null.nullName == sonName) 
			pm.editDisplayLayerMembers(flagSonNullLayer(son.nullName), son.nullName, nr=True)
			pm.button(son.blockButton, edit=True, en=getButtonState(son.nullName), bgc=getButtonColor(son.nullName))
			pm.button(son.selectButton, edit=True, en=getButtonState(son.nullName))
			if son.isCheckBoxAllowed:
				pm.checkBox(son.activeCheckBox, e=True, en=True)	
		
	pm.undoInfo(st=True)
	

# quando premo il blockButton, viene passata l'instanziazione relativa al button schiacciato, confronto col colore attuale per farlo switchare da verde o rosso, metto in variabile il nuovo colore e modifico il colore del button 
def blockButtonPressed(nullGrp):
	pm.undoInfo(st=False)
	if pm.button(nullGrp.blockButton, q=True, bgc=True) == redColor:
		nullGrp.buttonColor = greenColor 
		pm.button(nullGrp.blockButton, edit=True, bgc=greenColor)
		pm.editDisplayLayerMembers("Nulls_Blocked", nullGrp.nullName, nr=True) # sposto il null nel layer che va a bloccarlo
	else:
		nullGrp.buttonColor = redColor 
		pm.button(nullGrp.blockButton, edit=True, bgc=redColor)
		pm.editDisplayLayerMembers("Nulls_To_Be_Positioned", nullGrp.nullName, nr=True) # riporto il null nel layer sbloccato
	pm.undoInfo(st=True)


def resetToDefault(self):
	pm.editDisplayLayerMembers("Nulls_To_Be_Positioned", pm.ls("NULL_*", type="transform"), nr=True) 
	if pm.objExists("vol_*"):
		pm.delete("vol_*")		
	UI()	


def deleteAll(self):
	if pm.objExists("NULL_*"):
		pm.delete("NULL_*")
	if pm.objExists("Nulls_grp"):
		pm.delete("Nulls_grp")	
	if pm.objExists("vol_*"):
		pm.delete("vol_*")	
	ShowAll()
	cleanUp()
	UI()


def selectNull(nullGrp):
	pm.select(nullGrp.nullName)


# VOLUMES
volumeGrpList = [VolumeGrp("vol_chain_from_chassis_to_rake", "CHAIN", "CHAIN => RAKE"), VolumeGrp("vol_damper_from_upper_to_low", "DAMPER", "UPPER_DAMPER => LOW_DAMPER"), VolumeGrp("vol_handle_damper_from_damper_to_piston", "HANDLE_DAMPER", "HANDLE_DAMPER => PISTON"), VolumeGrp("vol_Cables_from_f_susp_to_handle", "F_SUSP_BRAKE_CABLE", "F_SUSP => HANDLE"), VolumeGrp("vol_Cables_from_handle_to_chassis", "HANDLE_BRAKE_CABLE", "HANDLE => CHASSIS"), VolumeGrp("vol_from_rake_to_chassis", "RAKE", "RAKE => CHASSIS"), VolumeGrp("vol_gearbolt_from_chassis_to_gear", "GEAR_BOLT", "CHASSIS => GEAR")]	


def getButtonColorVolume(volumeName):
	if pm.objExists(volumeName):
		if "Nulls_To_Be_Positioned" in pm.listConnections(volumeName):
			return redColor
		elif "Nulls_Blocked" in pm.listConnections(volumeName):
			return greenColor
		else:
			return greyColor
	else:
		return greyColor		


def getButtonStateVolume(volumeName):
	if pm.objExists(volumeName):
		if "Nulls_To_Be_Positioned" in pm.listConnections(volumeName) or "Nulls_Blocked" in pm.listConnections(volumeName):
			return True
		else:
			return False
	else:
		return False				


def getCheckBoxStateVolume(volumeName):
	if pm.objExists(volumeName):
		return True
	else:
		return False	


def getCheckBoxValueVolume(volumeName):
	if pm.objExists(volumeName):
		if "Nulls_To_Be_Positioned" in pm.listConnections(volumeName) or "Nulls_Blocked" in pm.listConnections(volumeName):
			return True
		else:
			return False
	else:
		return False		
	

def volumeBlockButtonPressed(volumeGrp):
	if pm.objExists(volumeGrp.volumeName):
		if "Nulls_To_Be_Positioned" in pm.listConnections(volumeGrp.volumeName):
			pm.editDisplayLayerMembers("Nulls_Blocked", volumeGrp.volumeName, nr=True)
			pm.button(volumeGrp.blockButton, e=True, bgc=greenColor)
		elif "Nulls_Blocked" in pm.listConnections(volumeGrp.volumeName):
			pm.editDisplayLayerMembers("Nulls_To_Be_Positioned", volumeGrp.volumeName, nr=True)	
			pm.button(volumeGrp.blockButton, e=True, bgc=redColor)	
	else:
		pm.warning("THIS VOLUME HAS BEEN DELETED, PLEASE CLICK AGAIN 'CREATE VOLUMES' AND DEFLAG IT IF YOU DON'T NEED IT")

def deactiveVolume(volumeGrp):
	if pm.objExists(volumeGrp.volumeName):
		if "Nulls_To_Be_Positioned" in pm.listConnections(volumeGrp.volumeName):
			pm.editDisplayLayerMembers("Nulls_Deflag_Active_Red", volumeGrp.volumeName, nr=True)			
		elif "Nulls_Blocked" in pm.listConnections(volumeGrp.volumeName):
			pm.editDisplayLayerMembers("Nulls_Deflag_Active_Green", volumeGrp.volumeName, nr=True)
		pm.button(volumeGrp.blockButton, e=True, en=False, bgc=greyColor)
		pm.button(volumeGrp.selectButton, e=True, en=False)
	else:
		pm.warning("THIS VOLUME HAS BEEN DELETED, PLEASE CLICK AGAIN 'CREATE VOLUMES' AND DEFLAG IT IF YOU DON'T NEED IT")	

def activeVolume(volumeGrp):
	if pm.objExists(volumeGrp.volumeName):
		if "Nulls_Deflag_Active_Red" in pm.listConnections(volumeGrp.volumeName):
			pm.editDisplayLayerMembers("Nulls_To_Be_Positioned", volumeGrp.volumeName, nr=True)
			pm.button(volumeGrp.blockButton, e=True, en=True, bgc=redColor)
		elif "Nulls_Deflag_Active_Green" in pm.listConnections(volumeGrp.volumeName):
			pm.editDisplayLayerMembers("Nulls_Blocked", volumeGrp.volumeName, nr=True)
			pm.button(volumeGrp.blockButton, e=True, en=True, bgc=greenColor)
		pm.button(volumeGrp.selectButton, e=True, en=True)	
	else:
		pm.warning("THIS VOLUME HAS BEEN DELETED, PLEASE CLICK AGAIN 'CREATE VOLUMES' AND DEFLAG IT IF YOU DON'T NEED IT")
		

def selectVolume(volumeName):
	if pm.objExists(volumeName):
		pm.select(volumeName)
	else:
		pm.warning("THIS VOLUME HAS BEEN DELETED, PLEASE CLICK AGAIN 'CREATE VOLUMES' AND DEFLAG IT IF YOU DON'T NEED IT")

		
def CheckIfVolumesExist():
	if pm.objExists("vol_*"):
		return True
	else:
		return False	
			
'''
--------------------------------------------------------- CREAZIONE VOLUMI ----------------------------------------------------
'''			
def createVolumes(self):
	positioningVolume("vol_chain_from_chassis_to_rake", "NULL_B_WHEEL", [1,0,0], [60, 5, 30], [-60, 10, 30])
	positioningVolume("vol_gearbolt_from_chassis_to_gear", "NULL_B_WHEEL", [0.25,0.25,0.5], [10, 5, 10], [-70, 10, 30])
	positioningVolume("vol_damper_from_upper_to_low", "NULL_DAMPER_RAKE", [1,1,0], [10, 10, 15])
	positioningVolume("vol_handle_damper_from_damper_to_piston", "NULL_HANDLE_DAMPER_PISTON", [1,0,1], [8, 8, 8])	
	positioningVolume("vol_Cables_from_f_susp_to_handle", "NULL_F_WHEEL", [0,0,1], [10, 10, 10], [50, 0, 65])	
	positioningVolume("vol_Cables_from_handle_to_chassis", "NULL_HANDLE", [1,0,0], [10, 10, 10], [45, 10, 75])
	positioningVolume("vol_from_rake_to_chassis", "NULL_B_RAKE", [0,1,1], [10, 20, 10], [-20, 0, 30])
	
	pm.button("rigButton", e=True, en=True)
					
'''
------------------------------------------------------------ RIGGING ---------------------------------------------------------
'''	
def Rigging(self):
	pm.progressWindow(title="AutoRig", progress=0, status="Start Process", isInterruptable=True)
	pm.select(cl=True)
		
	# elimino i volumi disattivati
	volumesList = pm.ls("vol_*", type="transform")
	for vol in volumesList:
		if "Nulls_Deflag_Active_Red" in pm.listConnections(vol) or "Nulls_Deflag_Active_Green" in pm.listConnections(vol):			
			pm.delete(vol)
	
	pm.rename("NULL_B_WHEEL", "NULL_B_VIS_WHEEL")
	pm.rename("NULL_F_WHEEL", "NULL_F_VIS_WHEEL")	
	
	if pm.objExists("MUFFLER_*"):
		pm.delete("MUFFLER_*")
	if pm.objExists("null_*"):
		pm.delete("null_*")	
		
	isHandleDamperParentToHandle = pm.getAttr("NULL_HANDLE_DAMPER.Parent_To")	
	
	geoList = pm.ls("*_LOD*", type="transform")

	# CHECK DEI NOMI DEI CANALI UV	
	uvChannelName = ["UVChannel_1", "UVChannel_2", "UVChannel_3", "UVChannel_4"]	
	UVsIssuesList = []
	for	geo in geoList:
		geoUVs = pm.polyUVSet(geo, q=True, auv=True)
		if len(geoUVs) > 4:
			pm.warning(geo.name()+" HAS MORE THAN 4 UV CHANNELS!")
			pm.progressWindow(endProgress=True)		
			return
		else:
			for i in range(0, len(geoUVs)):	
				if uvChannelName[i] != geoUVs[i]: 
					UVsIssuesList.append(geo.name()+" HAS WRONG UV CHANNEL NAME: "+geoUVs[i])
				
	if len(UVsIssuesList) > 0:
		for issue in UVsIssuesList:
			pm.warning(issue)
		pm.warning("FIX UV CHANNEL NAME BEFORE RIG THE BIKE!")
		#pm.progressWindow(endProgress=True)		
		#return
		
	# CHECK DEI MATERIALI
	matCorrectNameList = ["mat_livery", 
	                      "mat_mechanics",  
	                      "mat_cockpit", 
	                      "mat_chain", 
	                      "mat_gauge", 
	                      "mat_glass", 
	                      "mat_innerglass",	                      
	                      "mat_lights",
	                      "mat_brake",
	                      "mat_rim",
	                      "mat_b_tyre",
	                      "mat_f_tyre",
	                      "mat_livery_lod"]
	matInSceneList = [] 
	piecesWithoutMaterial = []
	for geo in geoList:
		shape = pm.ls(geo)[0].getShape() 
		shadingList = pm.listConnections(shape, type="shadingEngine") # ogni geometria ha uno shading engine per ogni materiale, se non ha materiali ha cmq uno shading engine
		for shading in shadingList:
			if len(pm.listConnections(shading.surfaceShader)) > 0:
				mat = pm.listConnections(shading.surfaceShader)[0] 
				matInSceneList.append(mat)	
			else:
				piecesWithoutMaterial.append(geo) 
	
	matInSceneList = list(set(matInSceneList)) # levo i doppioni
	missingMatlist = list(matCorrectNameList)
	unknownMaterials = []
	# se il materiale presente in scena non e' nella lista dei nomi corretti lo aggiungo alla lista dei materiali sconosciuti, altrimenti lo tolgo dalla lista dei materiali mancanti	
	for mat in matInSceneList:
		if not mat.name() in matCorrectNameList:
			unknownMaterials.append(mat)
		else: 	
			missingMatlist.remove(mat)									

	# controllo che sia corretto che certi materiali non siano presenti (quindi se la relativa geometria non esiste)
	matToRemoveFromMissingMatList = []
	for mat in missingMatlist: 
		if "chain" in mat:
			if pm.objExists("CHAIN_LOD*")==False:
				matToRemoveFromMissingMatList.append(mat)	
		elif "gauge" in mat:
			if pm.objExists("GAUGE_LOD*")==False:
				matToRemoveFromMissingMatList.append(mat)					
		elif "glass" in mat:
			if pm.objExists("*GLASS_LOD*")==False:
				matToRemoveFromMissingMatList.append(mat)
		elif "lights" in mat:
			if pm.objExists("*LIGHTS_LOD*")==False:
				matToRemoveFromMissingMatList.append(mat)		
				
	for mat in matToRemoveFromMissingMatList:
		missingMatlist.remove(mat)	

	if len(piecesWithoutMaterial) > 0:
		for piece in piecesWithoutMaterial:
			pm.warning(piece+" HAS NO MATERIAL!")
		pm.progressWindow(endProgress=True)	
		return
	if len(unknownMaterials) > 0:
		for unknownMat in unknownMaterials:
			pm.warning(unknownMat+" IS NOT A VALID NAME!")
		#pm.progressWindow(endProgress=True)
		#return
	if len(missingMatlist) > 0:
		for missMat in missingMatlist:
			pm.warning(missMat+" NOT PRESENT IN THE SCENE!")
		#pm.progressWindow(endProgress=True)
		#return	
												
	################################################ CREO E IMPARENTO LE OSSA #################################################
	pm.progressWindow(edit=True, progress=20, status="Creating and parenting the bones", isInterruptable=True)
	
	# creo le ossa solo per i null presenti nei layer giusti	
	nullsList = pm.ls("NULL_*", type="transform")
	for null in nullsList:
		if "Nulls_To_Be_Positioned" in pm.listConnections(null.name()) or "Nulls_Blocked" in pm.listConnections(null.name()):
			positioningJnt(pm.joint(n=null.name().replace("NULL", "BONE")), null)
			
	# pulisco la scena (cancellando anche i vari layers)
	ShowAll()
	cleanUp()	
	
	pm.joint(n="VEHICLE_BASE")
	pm.ls("VEHICLE_BASE")[0].radius.set(3)
	pm.select(cl=True)
	pm.joint(n="BONE_CHASSIS")
	pm.ls("BONE_CHASSIS")[0].radius.set(2)
	pm.select(cl=True)
	
	parent("BONE_*", "VEHICLE_BASE")
			
	pm.select("BONE_B_VIS_WHEEL")
	pm.duplicate(n="BONE_B_PHY_WHEEL")
	pm.ls("BONE_B_PHY_WHEEL")[0].radius.set(2)
	if pm.objExists("BONE_B_BRAKE"):
		parent("BONE_B_BRAKE", "BONE_B_VIS_WHEEL")
	if pm.objExists("BONE_B_GEAR"):
		parent("BONE_B_GEAR", "BONE_B_VIS_WHEEL")	
	parent("BONE_B_VIS_WHEEL", "BONE_B_RAKE")
		
	pm.select("BONE_F_VIS_WHEEL")
	pm.duplicate(n="BONE_F_PHY_WHEEL")
	pm.ls("BONE_F_PHY_WHEEL")[0].radius.set(2)
	if pm.objExists("BONE_FR_BRAKE"):
		parent("BONE_FR_BRAKE", "BONE_F_VIS_WHEEL")
	if pm.objExists("BONE_FL_BRAKE"):
		parent("BONE_FL_BRAKE", "BONE_F_VIS_WHEEL")				
	pm.select("BONE_HANDLE")	
	pm.duplicate(n="BONE_F_SUSP")
	pm.select(cl=True)
	pm.ls("BONE_HANDLE")[0].radius.set(2)
	parent(("BONE_L_GRIP", "BONE_R_GRIP", "BONE_L_LEVER", "BONE_R_LEVER", "BONE_F_SUSP"), "BONE_HANDLE")
	parent("BONE_F_VIS_WHEEL", "BONE_F_SUSP")		
	
	if pm.objExists("BONE_DAMPER"):
		pm.select("BONE_DAMPER_RAKE")
		pm.duplicate(n="BONE_DAMPER_LOW")
		pm.select(cl=True)
		pm.ls("BONE_DAMPER_RAKE")[0].radius.set(2)
		parent(("BONE_DAMPER_SPRING", "BONE_DAMPER_LOW"), "BONE_DAMPER")
		parent("BONE_DAMPER_RAKE", "BONE_B_RAKE")

							
	if pm.objExists("BONE_HANDLE_DAMPER"):							
		if isHandleDamperParentToHandle:					
			parent("BONE_HANDLE_DAMPER", "BONE_HANDLE")
			parent("BONE_HANDLE_DAMPER_PISTON", "VEHICLE_BASE")
		else:
			parent("BONE_HANDLE_DAMPER", "VEHICLE_BASE")
			parent("BONE_HANDLE_DAMPER_PISTON", "BONE_HANDLE")				

				
	if pm.objExists("NULL_*"):
		pm.delete("NULL_*")
	if pm.objExists("Nulls_grp"):
		pm.delete("Nulls_grp")
	
	################################################### SKINNING ###################################################
	pm.progressWindow(edit=True, progress=40, status="Base Skinning", isInterruptable=True)
	
	geoList = pm.ls("*_LOD*", type="transform")
	for geo in geoList:
		skinName = geo.name()+"_SK"
		pm.skinCluster("VEHICLE_BASE", geo, n=skinName)		
		
		if "F_SUSP" in geo.name() or "F_LOWSUSP" in geo.name() or "F_SUSP_BRAKE_CABLE" in geo.name():
			pm.skinPercent (skinName, geo, tv=[("BONE_F_SUSP", 1)])			
						
		elif "HANDLE_DAMPER_PISTON" in geo.name() and pm.objExists("BONE_HANDLE_DAMPER"):
			pm.skinPercent (skinName, geo, tv=[("BONE_HANDLE_DAMPER", 1)])	
		elif "HANDLE_DAMPER" in geo.name() and pm.objExists("BONE_HANDLE_DAMPER"):
			pm.skinPercent (skinName, geo, tv=[("BONE_HANDLE_DAMPER", 1)])	
			
		
		elif "HANDLE" in geo.name() or "HANDLEBAR" in geo.name() or "HANDLE_BRAKE_CABLE" in geo.name() or "TRIPLECLAMP" in geo.name() or "SUSP" in geo.name():
			pm.skinPercent (skinName, geo, tv=[("BONE_HANDLE", 1)])						
											
		elif "R_LEVER" in geo.name():
			pm.skinPercent (skinName, geo, tv=[("BONE_R_LEVER", 1)])
		elif "L_LEVER" in geo.name():
			pm.skinPercent (skinName, geo, tv=[("BONE_L_LEVER", 1)])
	
		elif "R_GRIP" in geo.name():
			pm.skinPercent (skinName, geo, tv=[("BONE_R_GRIP", 1)])
		elif "L_GRIP" in geo.name():
			pm.skinPercent (skinName, geo, tv=[("BONE_L_GRIP", 1)])
	
		elif "B_RAKE" in geo.name() or "B_BRAKE_CABLE" in geo.name():
			pm.skinPercent (skinName, geo, tv=[("BONE_B_RAKE", 1)])	
		
		elif "DAMPER_BODY" in geo.name() and pm.objExists("BONE_DAMPER"):
			pm.skinPercent (skinName, geo, tv=[("BONE_DAMPER", 1)])			
		elif "DAMPER_SPRING" in geo.name() and pm.objExists("BONE_DAMPER_SPRING"):
			pm.skinPercent (skinName, geo, tv=[("BONE_DAMPER_SPRING", 1)])	
		
		elif "F_WHEEL" in geo.name() or "F_BRAKE" in geo.name() or "F_TYRE" in geo.name() or "F_RIM" in geo.name():
			pm.skinPercent (skinName, geo, tv=[("BONE_F_VIS_WHEEL", 1)])
			
		elif "B_WHEEL" in geo.name() or "B_GEAR" in geo.name() or "B_BRAKE" in geo.name() or "B_TYRE" in geo.name() or "B_RIM" in geo.name():
			pm.skinPercent (skinName, geo, tv=[("BONE_B_VIS_WHEEL", 1)])
			
		elif "GEAR" in geo.name() and pm.objExists("BONE_GEAR"):
			pm.skinPercent (skinName, geo, tv=[("BONE_GEAR", 1)])	
			
		elif "CLUTCH" in geo.name() and pm.objExists("BONE_CLUTCH"):
			pm.skinPercent (skinName, geo, tv=[("BONE_CLUTCH", 1)])							
		
		else:
			pm.skinPercent (skinName, geo, tv=[("BONE_CHASSIS", 1)])
			
	
	################################################### SKIN VOLUMES ###################################################
	pm.progressWindow(edit=True, progress=60, status="Skin Volumes", isInterruptable=True)
		
	def passLODsToSkinVolume(vol, geoList, jnt):
		if pm.objExists(vol):
			for geo in geoList:
				lodsList = pm.ls(geo+"_LOD*", type="transform")
				for lod in lodsList:				
					skinVolume(vol, lod.name(), jnt)
	
	# nome volume - nome geometria interessata - nome dell'osso a cui i vertici dentro il volume devono skinnarsi			
	passLODsToSkinVolume("vol_chain_from_chassis_to_rake", ["CHAIN"], "BONE_B_RAKE")
	passLODsToSkinVolume("vol_gearbolt_from_chassis_to_gear", ["MAIN_BODY"], "BONE_B_VIS_WHEEL")
	passLODsToSkinVolume("vol_damper_from_upper_to_low", ["DAMPER_BODY"], "BONE_DAMPER_LOW")
	passLODsToSkinVolume("vol_handle_damper_from_damper_to_piston", ["HANDLE_DAMPER", "HANDLE_DAMPER_PISTON"], "BONE_HANDLE_DAMPER_PISTON")	
	passLODsToSkinVolume("vol_Cables_from_f_susp_to_handle", ["F_SUSP_BRAKE_CABLE", "F_SUSP"], "BONE_HANDLE")
	passLODsToSkinVolume("vol_Cables_from_handle_to_chassis", ["HANDLE_BRAKE_CABLE", "HANDLE"], "BONE_CHASSIS")
	passLODsToSkinVolume("vol_from_rake_to_chassis", ["B_RAKE"], "BONE_CHASSIS")
	
	pm.delete("vol_*")
	
	################################################### MERGE GEO ###################################################
	pm.progressWindow(edit=True, progress=80, status="Finalizing", isInterruptable=True)
	
	def mergeSkinnedGeo(lodLetter):
		lodGeoList = pm.ls("*"+lodLetter, type="transform")
		if len(lodGeoList) > 1:
			pm.select(lodGeoList)
			pm.polyUniteSkinned()
			objName = pm.ls(sl=True, type="transform")[0].name()
			if pm.objExists("*"+lodLetter): # se vengono creato gruppi non voluti dal merge, li elimino
				pm.delete("*"+lodLetter)			
			pm.rename(objName, "chassis_" + lodLetter)
		elif len(lodGeoList) == 1:
			pm.rename(lodGeoList[0].name(), "chassis_" + lodLetter)
	
	mergeSkinnedGeo("LODA")
	mergeSkinnedGeo("LODB")
	mergeSkinnedGeo("LODC")
	mergeSkinnedGeo("LODD")
	mergeSkinnedGeo("LODE")
	mergeSkinnedGeo("LODF")
	mergeSkinnedGeo("LODG")		
	
	pm.select("*_LODA")
	if pm.objExists("*_LODB"):
		pm.select("*_LODB", tgl=True)
	if pm.objExists("*_LODC"):
		pm.select("*_LODC", tgl=True)
	if pm.objExists("*_LODD"):
		pm.select("*_LODD", tgl=True)
	if pm.objExists("*_LODE"):
		pm.select("*_LODE", tgl=True)
	if pm.objExists("*_LODF"):
		pm.select("*_LODF", tgl=True)
	if pm.objExists("*_LODG"):
		pm.select("*_LODG", tgl=True)
	if pm.objExists("*_LODH"):
		pm.select("*_LODH", tgl=True)			
	pm.runtime.LevelOfDetailGroup()
	pm.rename("lodGroup1", "chassis_lodGroup")
	
	if pm.objExists("*_LODB"):
		pm.setAttr("chassis_lodGroup.threshold[0]", 22.255)
	if pm.objExists("*_LODC"):
		pm.setAttr("chassis_lodGroup.threshold[1]", 89.022)
	if pm.objExists("*_LODD"):
		pm.setAttr("chassis_lodGroup.threshold[2]", 200.298)
	if pm.objExists("*_LODE"):
		pm.setAttr("chassis_lodGroup.threshold[3]", 356.086)
	if pm.objExists("*_LODF"):
		pm.setAttr("chassis_lodGroup.threshold[4]", 556.385)
	if pm.objExists("*_LODG"):
		pm.setAttr("chassis_lodGroup.threshold[5]", 801.194)	
	if pm.objExists("*_LODH"):
		pm.setAttr("chassis_lodGroup.threshold[6]", 950.194)	
		
	pm.progressWindow(endProgress=True)
	
	pm.deleteUI("win", window=True)

	mel.eval('hyperShadePanelMenuCommand("hyperShadePanel1", "deleteUnusedNodes");')
	
'''
---------------------------------------------------------- RIG MUFFLER -----------------------------------------------------
'''
def exportPath():
    exportPath = pm.fileDialog2(fm=2, cap="Select a folder")
    if exportPath != None:
        pm.textFieldButtonGrp("ExportPath_field", edit=True, text=exportPath[0])

def RigMufflers(self):
	# prendo il path di esportazione, se esiste
	exportPath = pm.textFieldButtonGrp("ExportPath_field", q=True, text=True)
	if "Select" in exportPath:
		pm.warning("NO VALID PATH, CAN'T EXPORT MUFFLER!")
		return
	
	# ricavo l'ID del muffler dalla cartella del path	
	id = ""
	cuttedPath = exportPath.split("mufflers")[1] # limito la stringa del path per evitare di trovare altri numeri
	for char in cuttedPath:
		if char.isdigit():
			id = id+char
	if id == "":
		id = "_MISSING_ID"	
						
	# pulisco la scena	
	lodsList = pm.ls("*_LOD*", type="transform")
	geoToDelete = []
	for lod in lodsList:
		if "MUFFLER" not in lod.name():
			geoToDelete.append(lod)
	if len(geoToDelete) > 0:
		pm.delete(geoToDelete)
	if pm.objExists("NULL_*"):
		pm.delete("NULL_*")
	if pm.objExists("Nulls_grp"):
		pm.delete("Nulls_grp")	
	if pm.objExists("vol_*"):
		pm.delete("vol_*")	
	ShowAll()
	cleanUp()	
		
	mufflerNumber = len(pm.ls("MUFFLER_*_LODA", type="transform"))
	
	if mufflerNumber == 0:
		pm.warning("NO MUFFLER IN THE SCENE")
		return
	
	# scorro i muffler ID per ID	
	for mufflerID in range(1, 99):
		if not pm.objExists("MUFFLER_"+"%03d"%(mufflerID,)+"_LOD*"):
			continue
			
		# creo le ossa
		pm.select(cl=True)
		pm.joint(n="VEHICLE_BASE")
		pm.select(cl=True)
		pm.joint(n="BONE_CHASSIS")
		parent("BONE_CHASSIS", "VEHICLE_BASE")
		
		# ci skinno sopra tutti i lod
		mufflerLodsList = pm.ls("MUFFLER_"+"%03d"%(mufflerID,)+"_LOD*", type="transform")
		for muffler in mufflerLodsList: 	 			
			pm.skinCluster("VEHICLE_BASE", muffler, n=muffler.name()+"_SK")
			pm.skinPercent (muffler.name()+"_SK", muffler, tv=[("BONE_CHASSIS", 1)])
			
		# creo il lods group
		pm.select("MUFFLER_"+"%03d"%(mufflerID,)+"_LODA")
		pm.select("MUFFLER_"+"%03d"%(mufflerID,)+"_LODB", tgl=True)
		pm.select("MUFFLER_"+"%03d"%(mufflerID,)+"_LODC", tgl=True)
		pm.select("MUFFLER_"+"%03d"%(mufflerID,)+"_LODD", tgl=True)
		pm.select("MUFFLER_"+"%03d"%(mufflerID,)+"_LODE", tgl=True)
		pm.select("MUFFLER_"+"%03d"%(mufflerID,)+"_LODF", tgl=True)
		pm.select("MUFFLER_"+"%03d"%(mufflerID,)+"_LODG", tgl=True)		
		pm.runtime.LevelOfDetailGroup()
		pm.rename("lodGroup1", "muffler_lodGroup")
		
		pm.setAttr("muffler_lodGroup.threshold[0]", 22.255)
		pm.setAttr("muffler_lodGroup.threshold[1]", 89.022)
		pm.setAttr("muffler_lodGroup.threshold[2]", 200.298)
		pm.setAttr("muffler_lodGroup.threshold[3]", 356.086)
		pm.setAttr("muffler_lodGroup.threshold[4]", 556.385)
		pm.setAttr("muffler_lodGroup.threshold[5]", 801.194)		
			
		# esporto il muffler
		pm.select("VEHICLE_BASE", "muffler_lodGroup")
		if os.path.isfile(exportPath+"\\muffler"+id+"_"+"%03d"%(mufflerID,)+".fbx"):
			os.chmod(exportPath+"\\muffler"+id+"_"+"%03d"%(mufflerID,)+".fbx", S_IWUSR|S_IREAD)
		pm.mel.FBXExport(f=exportPath+"\\muffler"+id+"_"+"%03d"%(mufflerID,)+".fbx", s=True)
						
		# cancello tutto per fare la stessa operazione sul muffler successivo
		pm.delete("VEHICLE_BASE", "muffler_lodGroup")
	
	cmds.file(f=True, new=True)
	
'''
---------------------------------------------------------- IMPORT NULLS -----------------------------------------------------
'''
def newProjPath():
    ProjPath = pm.fileDialog(m=0, t="Bike nulls path")
    if ProjPath != None:
        pm.textFieldButtonGrp("BikeNullsPath_field", edit=True, text=ProjPath)
 
    	
def importNulls(self):
	pm.select(cl=True)
	
	# se in scena non esistonp null, ma sono rimasti dei display layer perche' il gruppo dei null e' stato eliminato brutalmente, elimino anche i layer prima di importare tutto il file
	if not pm.objExists("Nulls_grp"):
		layers = cmds.ls(long=True, type="displayLayer")
		for l in layers:
			if "Nulls_To_Be_Positioned" in l or "Nulls_Blocked" in l or "Nulls_Deflag_Active_Red" in l or "Nulls_Deflag_Active_Green" in l or "Nulls_Flag_Unactive_Red" in l or "Nulls_Flag_Unactive_Green" in l or "Nulls_Deflag_Unactive_Red" in l or "Nulls_Deflag_Unactive_Green" in l:
				pm.delete(l)
				
	ProjPath =  pm.textFieldButtonGrp("BikeNullsPath_field", query=True, text=True)
	if not "Select" in ProjPath and ProjPath != "" and "MotoGP20_bikeNulls.ma" in ProjPath:
		cmds.file(ProjPath, iv=True, ra=True, i=True, ns="nulls", options="v=0;", prompt=False, mergeNamespacesOnClash=True, type="mayaAscii")
		pm.namespace(mv=("nulls", ":"), f=True)				
			
		if pm.objExists("Nulls_grp1"):			
			nullsListNew = pm.listRelatives("Nulls_grp1")
			nullsListOld = pm.listRelatives("Nulls_grp")
			nullsListNewName=[]
			nullsListOldName=[]
			for null in nullsListNew:
				nullsListNewName.append(str(null))
			for null in nullsListOld:
				nullsListOldName.append(str(null))	
			
			for null in nullsListNewName:
				if not "Nulls_grp1|" in null:
					pm.parent(null, "Nulls_grp")
					pm.editDisplayLayerMembers("Nulls_To_Be_Positioned", null, nr=True)
					sons = pm.listRelatives(null, s=False, type="transform")
					for son in sons:
						if not "Constraint" in son.name():
							pm.editDisplayLayerMembers("Nulls_To_Be_Positioned", son, nr=True)
			
			layers = cmds.ls(long=True, type="displayLayer")
			for l in layers:
				if "Nulls_To_Be_Positioned1" in l or "Nulls_Blocked1" in l or "Nulls_Deflag_Active_Red1" in l or "Nulls_Deflag_Active_Green1" in l or "Nulls_Flag_Unactive_Red1" in l or "Nulls_Flag_Unactive_Green1" in l or "Nulls_Deflag_Unactive_Red1" in l or "Nulls_Deflag_Unactive_Green1" in l:
					pm.delete(l)					
			pm.delete("Nulls_grp1")
		UI()
	else:
		pm.warning("WRONG PATH, PLEASE SELECT THE MotoGP20_bikeNulls.ma FILE!")						
	
	
def SetTranspacrencyOff(self):
	pm.setAttr("XGizmo_Mat.transparency", [0,0,0])
	pm.setAttr("YGizmo_Mat.transparency", [0,0,0])
	pm.setAttr("ZGizmo_Mat.transparency", [0,0,0])
	
def SetTranspacrencyOn(self):
	tValue = 0.9
	pm.setAttr("XGizmo_Mat.transparency", [tValue,tValue,tValue])
	pm.setAttr("YGizmo_Mat.transparency", [tValue,tValue,tValue])
	pm.setAttr("ZGizmo_Mat.transparency", [tValue,tValue,tValue])	

'''
---------------------------------------------------------- ALIGN NULL TO FACE -------------------------------------------------
'''
# il PointOnPolyConstraint e' preciso ma non mi permette di scegliere l'asse di puntamento (sembra usi +Y di default), quindi genero un locator, lo imparento al null, 
#lo translo proprio nella direzione +Y del null, e lo faccio puntare dal null stesso con l'asse che voglio
def alignNullToFace(xRadio, yRadio, zRadio, negCheckbox):
	selection = pm.ls(sl=True)
	if len(selection) != 2:
		pm.warning("Please select two elements!")
		return 
			
	surface = selection[0]
	null = selection[1]
	
	if "MeshFace" not in str(type(surface)):
		pm.warning("First selected element must be a face component!")
		return
	if "Transform" not in str(type(null))==False or "NULL" not in null.name():
		pm.warning("Second selected element must be a NULL!") 	
		return
	
	cmds.PointOnPolyConstraint(surface, null, mo=[0,0,0], w=1)	
	pm.delete(null+"_pointOnPolyConstraint1")
	
	pm.spaceLocator(n="TempLocator")	
	parent("TempLocator", null)	
	pm.setAttr("TempLocator.tx", 0)
	pm.setAttr("TempLocator.ty", 0)
	pm.setAttr("TempLocator.tz", 0)
	pm.setAttr("TempLocator.rx", 0)
	pm.setAttr("TempLocator.ry", 0)
	pm.setAttr("TempLocator.rz", 0)
		
	if pm.radioButton(xRadio, q=True, sl=True):
		if negCheckbox.getValue():
			pm.setAttr("TempLocator.ty", 10)
			pm.parent("TempLocator", w=True)
			aim(null, "TempLocator", [-1,0,0])
		else:
			pm.setAttr("TempLocator.ty", 10)
			pm.parent("TempLocator", w=True)
			aim(null, "TempLocator", [1,0,0])
	elif pm.radioButton(yRadio, q=True, sl=True):
		if negCheckbox.getValue():
			pm.setAttr("TempLocator.ty", 10)
			pm.parent("TempLocator", w=True)
			aim(null, "TempLocator", [0,-1,0])			
	elif pm.radioButton(zRadio, q=True, sl=True):
		if negCheckbox.getValue():
			pm.setAttr("TempLocator.ty", 10)
			pm.parent("TempLocator", w=True)
			aim(null, "TempLocator", [0,0,-1])
		else:
			pm.setAttr("TempLocator.ty", 10)
			pm.parent("TempLocator", w=True)
			aim(null, "TempLocator", [0,0,1])
			
	pm.delete("TempLocator")	
	
'''
----------------------------------------------------------------- UI ----------------------------------------------------------
'''	
def UI(isNeedToInstantiate = True):
	if cmds.window("MGP26_Ultimate_Bike_Riggator", exists=True):
		cmds.deleteUI("MGP26_Ultimate_Bike_Riggator", window=True)
	
	cmds.window("MGP26_Ultimate_Bike_Riggator", title="MGP26 Ultimate Bike Riggator")	
	mainLayout = pm.columnLayout(adj=True)
	
	if not pm.objExists("NULL_HANDLE") or not pm.objExists("NULL_B_RAKE") or not pm.objExists("NULL_DAMPER") or not pm.objExists("NULL_DAMPER_SPRING") or not pm.objExists("NULL_GEAR") or not pm.objExists("NULL_L_LEVER") or not pm.objExists("NULL_R_LEVER") or not pm.objExists("NULL_B_WHEEL") or not pm.objExists("NULL_F_WHEEL") or not pm.objExists("NULL_R_GRIP") or not pm.objExists("NULL_L_GRIP") or not pm.objExists("NULL_HANDLE_DAMPER") or not pm.objExists("NULL_HANDLE_DAMPER_PISTON") or not pm.objExists("NULL_DAMPER_RAKE") or not pm.objExists("NULL_CLUTCH"):			
		pm.textFieldButtonGrp("BikeNullsPath_field", adj=True, text=DEFAULT_BIKE_NULLS_PATH, buttonLabel='...', bc=newProjPath, p=mainLayout)
		pm.button(l="Import Nulls", w=200, h=100, c=importNulls, p=mainLayout)
	else:	
		nullFrameLayout = pm.frameLayout(label="NULLs", collapsable=True, p=mainLayout)
		mainRowLayout = pm.rowLayout(nc=2, rat=[(1,"top",0), (2,"top",0)], p=nullFrameLayout)
		leftColLayout = pm.columnLayout(adj=True, h=315, p=mainRowLayout)
		rightColLayout = pm.columnLayout(adj=True, h=315, p=mainRowLayout)
		colLayout = [leftColLayout, rightColLayout]
					 	
		rowWidth = (150, 5, 52, 5, 52)
		rowHeight = 25
		sepHeight = 20
		
		pm.button(l="Reset To Default", h=rowHeight, c=resetToDefault, p=leftColLayout)
		pm.separator(h=sepHeight, style = 'in', p=leftColLayout)
		pm.button(l="Delete All", h=rowHeight, c=deleteAll, p=rightColLayout)
		pm.separator(h=sepHeight, style = 'in', p=rightColLayout)
		
		pm.button(l="Transparency OFF", h=rowHeight, c=SetTranspacrencyOff, p=leftColLayout)
		pm.separator(h=sepHeight, style = 'in', p=leftColLayout)
		pm.button(l="Transparency ON", h=rowHeight, c=SetTranspacrencyOn, p=rightColLayout)
		pm.separator(h=sepHeight, style = 'in', p=rightColLayout)

		pm.rowLayout(nc=5, h=rowHeight, cw5=rowWidth, p=leftColLayout)
		pm.text("Active", w=rowWidth[0], fn="obliqueLabelFont")
		pm.separator(hr=False, height=sepHeight, style = 'in')
		pm.text("Block", w=rowWidth[2], fn="obliqueLabelFont")
		pm.separator(hr=False, height=sepHeight, style = 'in')
		pm.text("Select", w=rowWidth[2], fn="obliqueLabelFont")
		
		pm.rowLayout(nc=5, h=rowHeight, cw5=rowWidth, p=rightColLayout)
		pm.text("Active", w=rowWidth[0], fn="obliqueLabelFont")
		pm.separator(hr=False, height=sepHeight, style = 'in')
		pm.text("Block", w=rowWidth[2], fn="obliqueLabelFont")
		pm.separator(hr=False, height=sepHeight, style = 'in')
		pm.text("Select", w=rowWidth[2], fn="obliqueLabelFont")
		
		# se i null sono presenti in scena, ma la lista di oggetti della classe NullGrp non esiste perche' la scena e' stata appena aperta, oppure se c'e' bisogno di un refresh intensivo, reinstazio tutto
		if not "nullGrpList" in globals() or isNeedToInstantiate:
			instantiateNullGrpClass()					
			
		for nullGrp in nullGrpList:					
			rowNullGrp = pm.rowLayout(nc=5, h=rowHeight, cw5=rowWidth, p=colLayout[nullGrp.col])		
			
			pm.rowLayout(nc=2, p=rowNullGrp)		
			if nullGrp.isCheckBoxAllowed: 
				pm.text("    ")
				nullGrp.activeCheckBox = pm.checkBox(l=nullGrp.checkBoxLabel, en=getCheckBoxState(nullGrp.nullName), v=getCheckBoxValue(nullGrp.nullName), onc=pm.Callback(activeNull, nullGrp), ofc=pm.Callback(unactiveNull, nullGrp))
			else:
				pm.text("          ")
				pm.text(nullGrp.checkBoxLabel)
				
			pm.separator(hr=False, height=sepHeight, style="in", p=rowNullGrp)
			
			pm.rowLayout(nc=2, p=rowNullGrp)
			pm.text("   ")
			nullGrp.blockButton = pm.button(l="", bgc=getButtonColor(nullGrp.nullName), w=rowHeight, en=getButtonState(nullGrp.nullName), c=pm.Callback(blockButtonPressed, nullGrp))
			
			pm.separator(hr=False, height=sepHeight, style="in", p=rowNullGrp)
			
			pm.rowLayout(nc=2, p=rowNullGrp)
			pm.text("   ")
			nullGrp.selectButton = pm.button(l="", w=rowHeight, en=getButtonState(nullGrp.nullName), c=pm.Callback(selectNull, nullGrp))
		
		pm.separator(style="in", h=15, p=nullFrameLayout)
		
		pm.text("ALIGN NULL TO SURFACE FACES", p=nullFrameLayout)
		alignNullRowLayout = pm.rowLayout(nc=5, cw5=(190, 10, 250, 10, 80), p=nullFrameLayout)
		pm.text("  First select the face, then the null", p=alignNullRowLayout)
		pm.separator(hr=False, height=sepHeight, style="in", p=alignNullRowLayout)
		aimGridLayout = pm.gridLayout(nc=5, cw=50, p=alignNullRowLayout)
		pm.radioCollection()
		pm.text("Aim Axis: ", p=aimGridLayout)
		xRadio = pm.radioButton(l="X", p=aimGridLayout)
		yRadio = pm.radioButton(l="Y", sl=True, p=aimGridLayout)
		zRadio = pm.radioButton(l="Z", p=aimGridLayout)
		negCheckbox = pm.checkBox(l="Neg")
		pm.separator(hr=False, height=sepHeight, style="in", p=alignNullRowLayout)
		pm.button(l="Align!", w=85, h=40, c=pm.Callback(alignNullToFace, xRadio, yRadio, zRadio, negCheckbox), p=alignNullRowLayout)
						
		pm.separator(style="in", h=15, p=mainLayout)
		
		volumesFrameLayout = pm.frameLayout(l="Volumes", collapsable=True, p=mainLayout)
		pm.columnLayout(adj=True, p=volumesFrameLayout)		
		pm.button(l="Create Volumes", h=rowHeight*2, w=sum(rowWidth)*2, c=createVolumes)
		pm.separator(style="none", h=15)
		
		twoRowFrameLayout = pm.rowLayout(nc=2)
		leftCol = pm.columnLayout(adj=True, p=twoRowFrameLayout)
		rightCol = pm.columnLayout(adj=True, p=twoRowFrameLayout)
		
		leftRowWidth = (190, 5, 225, 5)
		rightRowWidth = (52, 5, 52)
		
		pm.rowLayout(nc=4, h=rowHeight, cw4=leftRowWidth, p=leftCol)
		pm.text("Geo Part", w=leftRowWidth[0], fn="obliqueLabelFont")
		pm.separator(hr=False, height=sepHeight, style="in")
		pm.text("Influence From Bone - To Bone", w=leftRowWidth[2], fn="obliqueLabelFont")
		pm.separator(hr=False, height=sepHeight, style="in")
		
		pm.rowLayout(nc=3, h=rowHeight, cw3=rightRowWidth, p=rightCol)
		pm.text("Block", w=rightRowWidth[0], fn="obliqueLabelFont")
		pm.separator(hr=False, height=sepHeight, style="in")
		pm.text("Select", w=rightRowWidth[2], fn="obliqueLabelFont")

		for volumeGrp in volumeGrpList:
			pm.rowLayout(nc=4, h=rowHeight, cw4=leftRowWidth, p=leftCol)
			pm.rowLayout(nc=2)
			pm.text("    ")
			volumeGrp.activeCheckBox = pm.checkBox(l=volumeGrp.geoPart, en=getCheckBoxStateVolume(volumeGrp.volumeName), v=getCheckBoxValueVolume(volumeGrp.volumeName), ofc=pm.Callback(deactiveVolume, volumeGrp), onc=pm.Callback(activeVolume, volumeGrp))
			pm.setParent(u=True)
			pm.separator(hr=False, height=sepHeight, style="in")
			pm.text(volumeGrp.influence, w=leftRowWidth[2])
			pm.separator(hr=False, height=sepHeight, style="in")
			
			pm.rowLayout(nc=3, h=rowHeight, cw3=rightRowWidth, p=rightCol)
			pm.rowLayout(nc=2)
			pm.text("   ")
			volumeGrp.blockButton = pm.button(l="", w=rowHeight, en=getButtonStateVolume(volumeGrp.volumeName), bgc=getButtonColorVolume(volumeGrp.volumeName), c=pm.Callback(volumeBlockButtonPressed, volumeGrp))
			pm.setParent(u=True)
			pm.separator(hr=False, height=sepHeight, style="in")
			pm.rowLayout(nc=2)
			pm.text("   ")
			volumeGrp.selectButton = pm.button(l="", w=rowHeight, en=getButtonStateVolume(volumeGrp.volumeName), c=pm.Callback(selectVolume, volumeGrp.volumeName))
					
		pm.separator(style="in", h=15, p=mainLayout)
											
		pm.button("rigButton", l="RIG CHASSIS!", w=sum(rowWidth)*2, h=rowHeight*3, en=CheckIfVolumesExist(), c=Rigging, p=mainLayout)
		pm.separator(style="in", h=10, p=mainLayout)
		pm.textFieldButtonGrp("ExportPath_field", adj=True, text="Select the folder in which to export the mufflers", buttonLabel='...', bc=exportPath, p=mainLayout)	
		pm.button(l="RIG MUFFLERS!", w=sum(rowWidth)*2, h=rowHeight*2, c=RigMufflers, p=mainLayout)
			
	cmds.showWindow("MGP26_Ultimate_Bike_Riggator")

if __name__ == "__main__":
    UI()