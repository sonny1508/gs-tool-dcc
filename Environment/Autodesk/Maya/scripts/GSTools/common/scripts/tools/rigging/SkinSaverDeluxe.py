########### SKIN SAVER FROM HELL ######### BY ########### DAVIDE LOVECCHIO ################################
import maya.cmds as cmds
import maya.OpenMaya as om
import maya.OpenMayaAnim as oma
import pymel.core as pm
from stat import S_IWUSR, S_IREAD
import os

def exportSkinWeight(self):
	geoList = pm.ls(sl=True, type="transform")
	if len(geoList)==0:
		return
		
	filePath =  pm.textFieldButtonGrp("filePath_field", query=True, text=True)
	if os.path.isfile(filePath):		
		os.chmod(filePath, S_IWUSR|S_IREAD)						
	file = open(filePath, "w")
	
	for geo in geoList:		
		# il nodo di skin cluster contiene, tra i vari attributi, una lista di osso-influenza per ogni vertice, l'osso viene indicato con un ID numerico 
		skinClusterName = ""
		nodeList = pm.listHistory(geo.getShape())
		for node in nodeList:
			if pm.nodeType(node) == "skinCluster":	
				skinClusterName = node.name() 
		
		if skinClusterName == "": 
			pm.warning("No SkinCluster found for mesh "+geo.name())
			continue	

		file.write(geo.name()+"\r\n")

		selList = om.MSelectionList() # instanzio la lista di selezione di OpenMaya
		selList.add(skinClusterName) # ci aggiungo lo skin cluster
		clusterNode = om.MObject() # instanzio un oggetto di OpenMaya
		selList.getDependNode(0, clusterNode) # prendo le dipendenze del nodo di skin cluster
		skinFn = oma.MFnSkinCluster(clusterNode) # prendo lo skin cluster di OpenMaya 

		# instanzio un array di OpenMaya che conterra' i DAG path (quindi nome completo con inclusi i parent) di tutte le ossa con influenza nello skinCluster
		bonesDags = om.MDagPathArray() 
		skinFn.influenceObjects(bonesDags)
		
		# creo una libreria che conterra' come chiave l'ID dell'osso, e come value il suo DAG path
		idsAndBonesDict = {}
		for i in range(bonesDags.length()):
			bonePath = bonesDags[i].fullPathName() #DAG path dell'osso (es. |joint1|joint2 )
			boneId = int(skinFn.indexForInfluenceObject(bonesDags[i])) #ID del'osso nello skin cluster
			idsAndBonesDict[boneId] = bonePath #(ID e nome osso, es. {0: |joint1, 1: |joint1|joint2, 2: |joint1|joint2|joint3} )
			file.write(str(bonePath)+"_-_")
		file.write("\r\n")	

		# immagazzino attributi e connessioni (plug) ai parametri di weight del nodo di skin cluster
		weightPlugList = skinFn.findPlug("weightList")
		weightPlug = skinFn.findPlug("weights")
		weightAttrList = weightPlugList.attribute()
		weightAttr = weightPlug.attribute()
		weightInfIds = om.MIntArray()

		
		weights = {}
		for vtxId in range(weightPlugList.numElements()):
			file.write(str(vtxId)+"_-_")
			vtxWeights = {}
			
			weightPlug.selectAncestorLogicalIndex(vtxId, weightAttrList)
			
			# prendo l'indice di tutte le ossa con influenza maggiore di zero
			weightPlug.getExistingArrayAttributeIndices(weightInfIds)
			
			infPlug = om.MPlug(weightPlug)
			for infId in weightInfIds:
				infPlug.selectAncestorLogicalIndex(infId, weightAttr)
				
				try:
					vtxWeights[idsAndBonesDict[infId]] = infPlug.asDouble()
					file.write(str(idsAndBonesDict[infId])+"_-_"+str(infPlug.asDouble())+"_-_")
				except KeyError:
					pass	
			
			weights[vtxId] = vtxWeights	
			file.write("\r\n")		
			
		file.write("---\r\n")		
	file.close()	

'''
vertJointWeightData = [ ('someMesh.vtx[0]', [('joint1', 0.25), ('joint2', 0.75)]), ('someMesh.vtx[1]', [('joint1', 0.2), ('joint2', 0.7), ('joint3', 0.1)]) ]
'''
def setSkinWeights(skinCluster, vertJointWeightData):
	# converto il vertice da nome ad indice 
	idxJointWeight = []
	for vert, jointsAndWeights in vertJointWeightData:
		idx = int(vert[vert.rindex("[")+1:-1 ])
		idxJointWeight.append((idx, jointsAndWeights))

	# prendo lo skin cluster in openMaya
	selList = om.MSelectionList()
	selList.add(skinCluster) 
	clusterNode = om.MObject() 
	selList.getDependNode(0, clusterNode) 
	skinFn = oma.MFnSkinCluster(clusterNode)

	# converto il bone da nome ad indice (e gli do come value la sua influenza)
	jApiIndices = {}
	_tmp = om.MDagPathArray()
	skinFn.influenceObjects( _tmp)
	for n in range(_tmp.length()):
		jApiIndices[(_tmp[n].fullPathName())] = skinFn.indexForInfluenceObject(_tmp[n])

	# prendo i plug del nodo di skinCluster
	weightListP = skinFn.findPlug("weightList")
	weightListObj = weightListP.attribute()
	weightsP = skinFn.findPlug("weights")

	tmpIntArray = om.MIntArray() 
	baseFmtStr = str(skinCluster)+".weightList[%d]"  

	for vertIdx, jointsAndWeights in idxJointWeight:
		# we need to use the api to query the physical indices used
		weightsP.selectAncestorLogicalIndex(vertIdx, weightListObj)
		weightsP.getExistingArrayAttributeIndices(tmpIntArray)

		weightFmtStr = baseFmtStr % vertIdx+".weights[%d]"
		
		# clear up di skin data
		for n in range(tmpIntArray.length()):
			pm.removeMultiInstance(weightFmtStr % tmpIntArray[n])
		
		# applico lo skin in pymel, ma utilizzando direttamente gli attributi del nodo di skinCluster
		for joint, weight in jointsAndWeights:
			if weight:
				infIdx = jApiIndices[joint]
				pm.setAttr(weightFmtStr % infIdx, weight)
'''---------------------------------------------------------------------------------------------------------------'''

def importSkinWeight(self):
	filePath =  pm.textFieldButtonGrp("filePath_field", query=True, text=True)
	if os.path.isfile(filePath) == False:
		pm.warning("File does not exist!")
		return
	pm.select(cl=True)
	
	file = open(filePath, "r")	
	lines = file.readlines()
	x = 0	
	isGeoInTheScene = True
	for line in lines:	
		# fine mesh info (setto tutte le influenze della mesh, azzero il count delle linee e passo alla prossima mesh)
		if "---" in line:
			setSkinWeights(skinClusterName, vertJointWeightData)
			isGeoInTheScene = True
			x = 0
			continue			
		
		# mesh (sempre la prima linea)	
		elif x == 0:
			vertJointWeightData = []
			geo = pm.ls(line.replace("\r\n",""), type="transform")
			
			# se la mesh non esiste skippero' tutte le linee fino alla prossima mesh
			if len(geo) == 0:
				isGeoInTheScene = False
			else:
				shape = geo[0].getShape()	
			
			# per sicurezza, se la mesh e' skinnata la unbindo
			try:
				pm.skinCluster(shape, e=True, ub=True)
			except:
				pass					
		
		# lista di ossa da skinnare (sempre la seconda linea)
		elif x == 1 and isGeoInTheScene == True:
			bonesToSkin = line.replace("\r\n", "").split("_-_")	
			bonesToSkin.remove(bonesToSkin[len(bonesToSkin)-1])
			skinClusterName = geo[0].name()+"_SK"
			pm.select(shape, bonesToSkin)
			pm.skinCluster(n=skinClusterName, tsb=True)	
			pm.select(cl=True)
												
		# vertice e ossa che lo influenzano (dalla terza linea in poi)
		elif x > 1 and isGeoInTheScene == True:
			splittedLine = line.split("_-_")
			vtxId = int(splittedLine[0]) # immagazzino l'ID del vertice
			vtxName = shape+".vtx["+str(vtxId)+"]" # creo il nome del vertice
			splittedLine.remove(splittedLine[0])	# levo il vertice dalla lista
			splittedLine.remove(splittedLine[len(splittedLine)-1]) # levo il simbolo di a capo 
						
			infList = []
			for y in range(0, len(splittedLine), 2):
				splitBonePath = splittedLine[y].split("|")
				boneName = splitBonePath[len(splitBonePath)-1]
				infList.append((splittedLine[y], float(splittedLine[y+1]))) 
			
			vertJointWeightData.append((vtxName, infList))				
			
		# incremento per trackare sempre a che linea mi trovo
		x+=1 					
		
		
def getFilePath():
	filePath = pm.fileDialog(m=1, dm="*.txt", t="Choose the skin weight file to save/open")
	if filePath != None:
		pm.textFieldButtonGrp("filePath_field", edit=True, text=filePath)


def UI():		
	if cmds.window("win", exists=True):
		cmds.deleteUI("win", window=True)
	
	cmds.window("win", t="Skin Saver DELUXE")	
	mainLayout = pm.columnLayout(adj=True)	

	pm.separator(style="none", h=5, p=mainLayout)
	pm.textFieldButtonGrp("filePath_field", cw3=[30,200,10], l="File: ", text="S:/", buttonLabel='...', bc=getFilePath, p=mainLayout)
	pm.separator(style="in", h=15, p=mainLayout)
	pm.text("Select just one or more meshes")
	pm.button(l="Export Skin Weight", h=50, c=exportSkinWeight)
	pm.separator(style="in", h=15, p=mainLayout)
	pm.button(l="Import Skin Weight", h=50, c=importSkinWeight)

	cmds.showWindow('win')
	
UI()