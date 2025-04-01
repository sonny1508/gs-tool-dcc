################################################### DAVIDE LOVECCHIO ###################################################
import pymel.core as pm
import maya.cmds as cmds
import maya.OpenMaya as api
import maya.mel as mel
import os
from stat import S_IWUSR, S_IREAD

#################################################### SERVICE METHODS ###################################################

def findNearby(point, Vol_BB, max_scale_val):
    mode = 'vertex'

    #convert an object to an API point (Get it's worldspace position)
    if isinstance(point, basestring):
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
	if pm.objExists(null):
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
		else:
			print "Volume for " + str(null) + " already exist"		


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


def ShowAll():
	pm.showHidden(all=True)
	layers = cmds.ls(long=True, type="displayLayer")
	for l in layers[1:]: 
		if l.find("defaultLayer") == -1: 
			cmds.setAttr("%s.visibility" % l, True)
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


def assignBikeLodsMaterial(geoName):
	if pm.objExists("mat_bike_lods")==False:
		pm.shadingNode("lambert", n="mat_bike_lods", asShader=True)		
	if "_LODE" in geoName or "_LODF" in geoName or "_LODG" in geoName or "_LODH" in geoName:
		pm.select(geoName)
		pm.hyperShade(assign="mat_bike_lods") 	
		pm.select(cl=True)
	
	
#######################################################################################################################

def createLods(lodName):
	pm.select(cl=True)
	
	def mergeSkinnedGeo(lodLetter):
		lodGeoList = pm.ls("*"+lodLetter, type="transform")
		if len(lodGeoList) > 1:
			pm.select(lodGeoList)
			pm.polyUniteSkinned()
			objName = pm.ls(sl=True, type="transform")[0].name()
			if pm.objExists("*"+lodLetter): # se vengono creato gruppi non voluti dal merge, li elimino
				pm.delete("*"+lodLetter)
			pm.rename(objName, lodName + "_" + lodLetter)
	
	mergeSkinnedGeo("LODA")
	mergeSkinnedGeo("LODB")
	mergeSkinnedGeo("LODC")
	mergeSkinnedGeo("LODD")
	mergeSkinnedGeo("LODE")
	mergeSkinnedGeo("LODF")
	mergeSkinnedGeo("LODG")
	mergeSkinnedGeo("LODH")	
	
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
	pm.rename("lodGroup1", lodName + "_lodGroup")
	
	if pm.objExists("*_LODB"):
		pm.setAttr(lodName + "_lodGroup.threshold[0]", 22.255)
	if pm.objExists("*_LODC"):
		pm.setAttr(lodName + "_lodGroup.threshold[1]", 89.022)
	if pm.objExists("*_LODD"):
		pm.setAttr(lodName + "_lodGroup.threshold[2]", 200.298)
	if pm.objExists("*_LODE"):
		pm.setAttr(lodName + "_lodGroup.threshold[3]", 356.086)
	if pm.objExists("*_LODF"):
		pm.setAttr(lodName + "_lodGroup.threshold[4]", 556.385)
	if pm.objExists("*_LODG"):
		pm.setAttr(lodName + "_lodGroup.threshold[5]", 801.194)	
	if pm.objExists("*_LODH"):
		pm.setAttr(lodName + "_lodGroup.threshold[5]", 901.194)			

'''------------------------------------------------RIM------------------------------------------------'''

def generateRimNulls(self):
	pm.select(cl=True)
	def generate(prefix):
		if not pm.objExists("NULL_" + prefix + "L_RIMHUB"):
			pm.move(pm.spaceLocator(n="NULL_" + prefix + "L_RIMHUB"), [0,10,0])
			pm.select(cl=True)
		if not pm.objExists("NULL_" + prefix + "R_RIMHUB"):
			pm.move(pm.spaceLocator(n="NULL_" + prefix + "R_RIMHUB"), [0,-10,0])
			pm.select(cl=True)
		if not pm.objExists("NULL_" + prefix + "L_RIM"):
			pm.move(pm.spaceLocator(n="NULL_" + prefix + "L_RIM"), [0,10,20])
			pm.select(cl=True)
		if not pm.objExists("NULL_" + prefix + "R_RIM"):
			pm.move(pm.spaceLocator(n="NULL_" + prefix + "R_RIM"), [0,-10,20])
			pm.select(cl=True)
	
	pm.select(cl=True)
	if len(pm.ls("F_RIM_LOD*", type="transform"))==0 and len(pm.ls("B_RIM_LOD*", type="transform"))==0:
		pm.warning("NO RIM FOUND! Please make sure at least one rim, with correct name, is in the scene")
		return
	
	if len(pm.ls("F_RIM_LOD*", type="transform")) > 0:
		generate("F")
	if len(pm.ls("B_RIM_LOD*", type="transform")) > 0:
		generate("B")		
	

def generateRimVolumes(self):
	pm.select(cl=True)
	def generate(prefix):
		positioningVolume("vol_" + prefix + "L_RIM", "NULL_" + prefix + "L_RIMHUB", [0,0,1], [45,5,45], pos=None)
		positioningVolume("vol_" + prefix + "R_RIM", "NULL_" + prefix + "R_RIMHUB", [0,0,1], [45,5,45], pos=None)
		positioningVolume("vol_" + prefix + "L_RIMHUB", "NULL_" + prefix + "L_RIMHUB", [1,0,0], [20,10,20], pos=None)
		positioningVolume("vol_" + prefix + "R_RIMHUB", "NULL_" + prefix + "R_RIMHUB", [1,0,0], [20,10,20], pos=None)
	
	pm.select(cl=True)
	if len(pm.ls("F_RIM_LOD*", type="transform"))==0 and len(pm.ls("B_RIM_LOD*", type="transform"))==0:
		pm.warning("NO RIM FOUND! Please make sure at least one rim, with correct name, is in the scene")
		return
			
	# se e' presente la geometria del rim ma non i suoi nulls, essendo questi generati automaticamente, vuol dire che devono essere generati, altrimenti se la geometria del rim non e' presente, la cosa viene ignorata	
	if len(pm.ls("F_RIM_LOD*", type="transform")) > 0:
		if pm.objExists("NULL_FL_RIM") and pm.objExists("NULL_FR_RIM") and pm.objExists("NULL_FL_RIMHUB") and pm.objExists("NULL_FR_RIMHUB"):
			generate("F")
		else:
			pm.warning("SOME F_RIM NULLS ARE MISSING! Please repeat the procedure of nulls creation")
	if len(pm.ls("B_RIM_LOD*", type="transform")) > 0:
		if pm.objExists("NULL_BL_RIM") and pm.objExists("NULL_BR_RIM") and pm.objExists("NULL_BL_RIMHUB") and pm.objExists("NULL_BR_RIMHUB"):
			generate("B")	
		else:
			pm.warning("SOME B_RIM NULLS ARE MISSING! Please repeat the procedure of nulls creation")

	
def rigRim(self):
	pm.select(cl=True)
	if len(pm.ls("F_RIM_LOD*", type="transform"))==0 and len(pm.ls("B_RIM_LOD*", type="transform"))==0:
		pm.warning("NO RIM FOUND! Please make sure at least one rim, with correct name, is in the scene")
		return
	
	nullsList = pm.ls("NULL_*", type="transform")
	for null in nullsList:
		positioningJnt(pm.joint(n=null.name().replace("NULL", "BONE")), null) 
	
	ShowAll()
	cleanUp()

	rimGeo = pm.ls("*_LODA", "*_LODB", "*_LODC", "*_LODD", "*_LODE", "*_LODF", "*_LODG", "*_LODH", type="transform")  
	for geo in rimGeo:
		geoShape = geo.getShape()
		if geoShape != None and "Grp" not in str(geo):  
			pm.select(geo)
			geoFaces = pm.polyListComponentConversion(toFace=True)  
			
			uv3Proj=""
			if "UVChannel_3" in pm.polyUVSet(geo.name(), auv=True, q=True):
				uv3Proj = pm.polyProjection(geoFaces, ch=True, type="Planar", ibd=True, md="y", cm=False, uvs="UVChannel_3")
			else:	
				uv3Proj = pm.polyProjection(geoFaces, ch=True, type="Planar", ibd=True, md="y", cm=True, uvs="UVChannel_3")
			
			pm.setAttr (uv3Proj[0] + ".imageScale", 0.01, 0.01, type = "double2") 		
			pm.setAttr (uv3Proj[0] + ".imageCenter", 0.6, 0.3, type = "double2")  

	pm.select(rimGeo)
	mel.eval("BakeAllNonDefHistory")
	pm.select(cl=True)			

	def skin(prefix):
		if pm.objExists("BONE_" + prefix + "L_RIM") and pm.objExists("BONE_" + prefix + "R_RIM") and pm.objExists("BONE_" + prefix + "L_RIMHUB") and pm.objExists("BONE_" + prefix + "R_RIMHUB"):	
			
			pm.setAttr("BONE_" + prefix + "R_RIM.ty", pm.getAttr("BONE_" + prefix + "R_RIM.ty") + pm.floatField("nullRimOffset", q=True, v=True))
			pm.setAttr("BONE_" + prefix + "L_RIM.ty", pm.getAttr("BONE_" + prefix + "L_RIM.ty") - pm.floatField("nullRimOffset", q=True, v=True))
			
			if pm.objExists("vol_" + prefix + "L_RIM") and pm.objExists("vol_" + prefix + "R_RIM") and pm.objExists("vol_" + prefix + "L_RIMHUB") and pm.objExists("vol_" + prefix + "R_RIMHUB"):
				pm.joint(n="BONE_" + prefix + "_VIS_WHEEL")
				pm.joint(n="BONE_SCALE_" + prefix + "_RIM")
				parent(("BONE_" + prefix + "L_RIM", "BONE_" + prefix + "R_RIM", "BONE_" + prefix + "L_RIMHUB", "BONE_" + prefix + "R_RIMHUB"), "BONE_SCALE_" + prefix + "_RIM")			
								
				geoList = pm.ls("" + prefix + "_RIM_LOD*", type="transform")
				for geo in geoList:
					assignBikeLodsMaterial(geo.name())
					skinName = geo.name()+"_SK"
					pm.skinCluster("BONE_" + prefix + "_VIS_WHEEL", geo, n=skinName)	
					pm.skinPercent(skinName, geo, tv=[("BONE_SCALE_" + prefix + "_RIM", 1)])
					skinVolume("vol_" + prefix + "L_RIM", geo.name(), "BONE_" + prefix + "L_RIM")
					skinVolume("vol_" + prefix + "R_RIM", geo.name(), "BONE_" + prefix + "R_RIM")
					skinVolume("vol_" + prefix + "L_RIMHUB", geo.name(), "BONE_" + prefix + "L_RIMHUB")
					skinVolume("vol_" + prefix + "R_RIMHUB", geo.name(), "BONE_" + prefix + "R_RIMHUB")
				pm.select(cl=True)
			else:
				pm.warning("SOME VOLUMES ARE MISSING! Please repeat the procedure of volumes creation")
		else:
			pm.warning("SOME BONE ARE MISSING! Please repeat the procedure of bones creation")
		
	if len(pm.ls("F_RIM_LOD*", type="transform")) > 0:
		skin("F")
	if len(pm.ls("B_RIM_LOD*", type="transform")) > 0:
		skin("B")
	
	if pm.objExists("NULL_*"):
		pm.delete("NULL_*")
	if pm.objExists("vol_*"):
		pm.delete("vol_*")
	
	if len(pm.ls("F_RIM_LOD*", type="transform")) > 0:	
		createLods("f_rim")
	if len(pm.ls("B_RIM_LOD*", type="transform")) > 0:
		createLods("b_rim")

'''------------------------------------------------MUFFLER------------------------------------------------'''
def generateMufflerNulls(self):	
	pm.select(cl=True)
	if not pm.objExists("NULL_MUFFLER_001"):	
		pm.move(pm.spaceLocator(n="NULL_MUFFLER_001"), [0,-30,10])
		pm.select(cl=True)
	if not pm.objExists("NULL_MOUNT_001"):
		pm.move(pm.spaceLocator(n="NULL_MOUNT_001"), [0,30,10])
		pm.select(cl=True)	


def rigMuffler(self):
	pm.select(cl=True)	
	if len(pm.ls("*MUFFLER_001_LOD*", type="transform")) == 0:
		pm.warning("NO MUFFLER IN THE SCENE!")
		return
	#if not pm.objExists("NULL_MOUNT_001"):	
	#	pm.warning("NULL_MOUNT IS MISSING!")
	#	return
	if not pm.objExists("NULL_MUFFLER_001"):	
		pm.warning("NULL_MUFFLER_001 IS MISSING!")
		return	
						
	nullsList = pm.ls("NULL_*", type="transform")
	for null in nullsList:
			positioningJnt(pm.joint(n=null.name().replace("NULL", "BONE")), null)		
		
	pm.delete("NULL_*")
	ShowAll()
	cleanUp()	

	pm.joint(n="VEHICLE_BASE")
	pm.select(cl=True)	
	parent("BONE_MUFFLER*", "VEHICLE_BASE")
	
	boneMufflerList = pm.ls("BONE_MUFFLER_00*", type="transform")	
	for i in range(1, len(boneMufflerList)+1):
		mufflerGeoList = pm.ls("MUFFLER_00"+str(i)+"_LOD*", type="transform")
		for geo in mufflerGeoList:
			assignBikeLodsMaterial(geo.name())
			pm.skinCluster("BONE_MUFFLER_00"+str(i), geo, tsb=True)
		if pm.objExists("BONE_MOUNT_00"+str(i)):	
			parent("BONE_MOUNT_00"+str(i),"BONE_MUFFLER_00"+str(i))
			mountGeoList = pm.ls("MOUNT_00"+str(i)+"_LOD*", type="transform")
			for geo in mountGeoList:
				assignBikeLodsMaterial(geo.name())
				pm.skinCluster("BONE_MOUNT_00"+str(i), geo, tsb=True)

		pm.setAttr("BONE_MUFFLER_00"+str(i)+".tx", 0)
		pm.setAttr("BONE_MUFFLER_00"+str(i)+".ty", 0)
		pm.setAttr("BONE_MUFFLER_00"+str(i)+".tz", 0)
		pm.setAttr("BONE_MUFFLER_00"+str(i)+".jox", 0)
		pm.setAttr("BONE_MUFFLER_00"+str(i)+".joy", 0)
		pm.setAttr("BONE_MUFFLER_00"+str(i)+".joz", 0)
	
	pm.select("bindPose*")
	pm.delete()
	pm.select("VEHICLE_BASE")
	pm.dagPose(bp=True, s=True)	
	
	createLods("muffler")	

'''------------------------------------------------EXMANIFOLD------------------------------------------------'''	
def importProxyGeo(GeoName):
	importFile = pm.fileDialog2(fileMode=1, dialogStyle=2, cap="Choose a "+GeoName+" to import")
	if not importFile[0] == None: 
		cmds.file(importFile[0], r=True, ignoreVersion=True, gl=True, mergeNamespacesOnClash=True, namespace=":", options="v=0;")
		
			
def rigExmanifold(self):
	pm.select(cl=True)
	if len(pm.ls("*EXMANIFOLD_001_LOD*", type="transform")) == 0:
		pm.warning("NO EXMANIFOLD IN THE SCENE!")
		return
	#if not pm.objExists("BONE_MOUNT_001"):	
	#	pm.warning("MOUNT IS MISSING!")
	#	return
	if not pm.objExists("BONE_MUFFLER_001"):	
		pm.warning("MUFFLER IS MISSING!")
		return
	
	# duplico e rinomino le ossa che mi servono dal muffler
	boneMufflerList = pm.ls("BONE_MUFFLER_00*", type="transform")
	for bone in boneMufflerList:
		pm.duplicate(bone, n="tempBone")
		pm.parent("tempBone", w=True)
		pm.rename("tempBone", bone.name())	

	# cancello tutte le reference e pulisco la scena
	refList = pm.ls(rf=True)
	for ref in refList:
		refPath = cmds.referenceQuery(ref.name(), filename=True)
		cmds.file(refPath, removeReference=True)
	ShowAll()
	cleanUp()			

	pm.joint(n="VEHICLE_BASE")
	pm.joint(n="BONE_CHASSIS")
	pm.select(cl=True)		
	parent("BONE_MUFFLER*", "VEHICLE_BASE")
	
	lodsList = pm.ls("*LOD*", type="transform")
	for geo in lodsList:
		assignBikeLodsMaterial(geo.name())
		skinName = geo.name()+"_SK"
		pm.skinCluster("VEHICLE_BASE", geo, n=skinName)			
		pm.skinPercent (skinName, geo, tv=[("BONE_CHASSIS", 1)])	
	
	pm.select("bindPose*")
	pm.delete()
	pm.select("VEHICLE_BASE")
	pm.dagPose(bp=True, s=True)	

	createLods("exmanifold")	

'''------------------------------------------------BRAKES------------------------------------------------'''
def rigBrakes(self):
	pm.select(cl=True)
	ShowAll()
	cleanUp()		
	lodLetters = ["A", "B", "C", "D", "E", "F", "G"]
	frontLeftBrakes = pm.ls("FL_BRAKE_LOD*", type="transform")
	frontRightBrakes = pm.ls("FR_BRAKE_LOD*", type="transform")
	backBrakes = pm.ls("B_BRAKE_LOD*", type="transform")
	
	def checkAndSkin(brakeList, boneName):
		if len(brakeList) > 0:
			pm.select(cl=True)
			pm.joint(n=boneName)			
			for brake in brakeList:
				pm.skinCluster(boneName, brake, n=brake.name()+"_SK")	
	
	checkAndSkin(frontLeftBrakes, "BONE_FL_BRAKE")
	checkAndSkin(frontRightBrakes, "BONE_FR_BRAKE")	
	checkAndSkin(backBrakes, "BONE_B_BRAKE")

	def createLodGroup(geoName, lodName):
		pm.select(geoName+"LODA")
		if pm.objExists(geoName+"LODB"):
			pm.select(geoName+"LODB", tgl=True)
		if pm.objExists(geoName+"LODC"):
			pm.select(geoName+"LODC", tgl=True)
		if pm.objExists(geoName+"LODD"):
			pm.select(geoName+"LODD", tgl=True)
		if pm.objExists(geoName+"LODE"):
			pm.select(geoName+"LODE", tgl=True)
		if pm.objExists(geoName+"LODF"):
			pm.select(geoName+"LODF", tgl=True)
		if pm.objExists(geoName+"LODG"):
			pm.select(geoName+"LODG", tgl=True)		
		pm.runtime.LevelOfDetailGroup()
		pm.rename("lodGroup1", lodName + "_lodGroup")
		
		if pm.objExists("*_LODB"):
			pm.setAttr(lodName + "_lodGroup.threshold[0]", 22.255)
		if pm.objExists("*_LODC"):
			pm.setAttr(lodName + "_lodGroup.threshold[1]", 89.022)
		if pm.objExists("*_LODD"):
			pm.setAttr(lodName + "_lodGroup.threshold[2]", 200.298)
		if pm.objExists("*_LODE"):
			pm.setAttr(lodName + "_lodGroup.threshold[3]", 356.086)
		if pm.objExists("*_LODF"):
			pm.setAttr(lodName + "_lodGroup.threshold[4]", 556.385)
		if pm.objExists("*_LODG"):
			pm.setAttr(lodName + "_lodGroup.threshold[5]", 801.194)	

	if pm.objExists("bindPose*"):
		pm.delete("bindPose*")	
	pm.select(cl=True)
	
	if pm.objExists("BONE_B_BRAKE"):		
		pm.joint(n="BONE_B_VIS_WHEEL")
		parent("BONE_B_BRAKE", "BONE_B_VIS_WHEEL")
		pm.select("BONE_B_VIS_WHEEL")
		pm.dagPose(bp=True, s=True)	
		pm.select(cl=True)
		createLodGroup("B_BRAKE_", "backBrake")	
		pm.select(cl=True)
	
	if pm.objExists("BONE_F*_BRAKE"):
		pm.joint(n="BONE_F_VIS_WHEEL")		
		pm.select(cl=True)
	
	brakeGeoList = pm.ls("*_BRAKE_LOD*", type="transform")
	for geo in brakeGeoList:
		assignBikeLodsMaterial(geo.name())	
		
	def mergeLeftAndRight(lod, geoName):
		pm.select(lod)
		pm.polyUniteSkinned()
		objName = pm.ls(sl=True, type="transform")[0].name()	
		pm.rename(objName, geoName)
	
	# se esiste sia il front sinistro che destro mergio, altrimenti se esiste uno solo dei 2 faccio direttamente i lod (come per il back)
	if pm.objExists("BONE_FL_BRAKE") and pm.objExists("BONE_FR_BRAKE"):
		parent(["BONE_FL_BRAKE", "BONE_FR_BRAKE"], "BONE_F_VIS_WHEEL")
		for letter in lodLetters: 
			mergeLeftAndRight(pm.ls("F*_BRAKE_LOD"+letter, type="transform"), "F_BRAKE_LOD"+letter)
		createLodGroup("F_BRAKE_", "frontBrake")
	elif pm.objExists("BONE_FL_BRAKE") and pm.objExists("BONE_FR_BRAKE")==False:	
		parent("BONE_FL_BRAKE", "BONE_F_VIS_WHEEL")
		createLodGroup("FL_BRAKE_", "frontBrake")
	elif pm.objExists("BONE_FL_BRAKE")==False and pm.objExists("BONE_FR_BRAKE"):	
		parent("BONE_FR_BRAKE", "BONE_F_VIS_WHEEL")
		createLodGroup("FR_BRAKE_", "frontBrake")
		
	pm.select("BONE_F_VIS_WHEEL")
	pm.dagPose(bp=True, s=True)
	pm.select(cl=True)	
			
		
def UI():
	if pm.window("win", exists=True):
		pm.deleteUI("win", window=True)
	
	win = pm.window("win", t="Custom Parts Rigger - RIDE4")	
	mainLayout = pm.columnLayout(adj=True)	
	
	btnHeight = 50
	
	rimsFrameLayout = pm.frameLayout(label="BACK & FRONT RIMS", collapsable=True, p=mainLayout)
	pm.text(" - Open a scene with only one rim (back or front, not both)\n - Put it AT THE CENTER OF THE SCENE", al="left", h=btnHeight, p=rimsFrameLayout)	
	pm.button(l="Generate Nulls", h=btnHeight, c=generateRimNulls, p=rimsFrameLayout)	
	pm.button(l="Generate Volumes", h=btnHeight, c=generateRimVolumes, p=rimsFrameLayout)
	pm.rowLayout(nc=2, cw2=(160, 50), h=50, p=rimsFrameLayout)
	pm.text("                        NULL_RIM offset: ")
	pm.floatField("nullRimOffset", v=0.5, pre=2)	
	pm.button(l="Rig The Rim", h=btnHeight, c=rigRim, p=rimsFrameLayout)

	pm.separator(style="in", h=15, p=mainLayout)
	
	mufflerFrameLayout = pm.frameLayout(label="MUFFLER", collapsable=True, p=mainLayout)
	pm.text(" - Put the MUFFLER null alligned with the muffler back,\n    with the X axis in backward direction, and do the same\n    for the MOUNT null with the mount geometry\n - If you need more NULL, just duplicate them", al="left", h=btnHeight, p=mufflerFrameLayout)
	pm.button(l="Generate Nulls", h=btnHeight, c=generateMufflerNulls, p=mufflerFrameLayout)
	pm.button(l="Rig The Muffler", h=btnHeight, c=rigMuffler, p=mufflerFrameLayout)
	
	pm.separator(style="in", h=15, p=mainLayout)
		
	exmanifoldFrameLayout = pm.frameLayout(label="EXMANIFOLD", collapsable=True, p=mainLayout)
	pm.text(" - Make sure to import a rigged custom muffler \n - Put both muffler and exmanifold in the right place\n    by moving just MUFFLER and MOUNT bones,\n    exmanifold bones will be generated from them", al="left", h=btnHeight)
	pm.button("Import Proxy Bike", h=btnHeight, c=pm.Callback(importProxyGeo, "Chassis"))
	pm.button("Import Proxy Muffler", h=btnHeight, c=pm.Callback(importProxyGeo, "Custom Muffler"))
	pm.button(l="Rig The Exmanifold", h=btnHeight, c=rigExmanifold, p=exmanifoldFrameLayout)
	
	pm.separator(style="in", h=15, p=mainLayout)
		
	brakeFrameLayout = pm.frameLayout(label="BACK & FRONT BRAKES", collapsable=True, p=mainLayout)
	pm.text(" - Put the brakes at the center of the scene", al="left")
	pm.button("Rig Brakes", h=btnHeight, c=rigBrakes)

	win.show()

if __name__ == "__main__":
    UI()