import pymel.core as pm
import maya.mel as mel
import maya.cmds as cmds
import os
import ast
from stat import S_IWUSR, S_IREAD


def showPaintLayer(self):
	selList = pm.ls(sl=True, type="transform")
	for geo in selList:
		pm.setAttr(geo.name()+".displayColors", 1)	
		
def hidePaintLayer(self):
	selList = pm.ls(sl=True, type="transform")
	for geo in selList:
		pm.setAttr(geo.name()+".displayColors", 0)	

		
def paintVertexColorRGB(self):
	selectedVertices = pm.ls(sl=True, fl=True, type="float3")	
	if len(selectedVertices) == 0:
		return
	
	color = [pm.floatField("R_field", q=True, v=True), pm.floatField("G_field", q=True, v=True), pm.floatField("B_field", q=True, v=True)]					
	pm.polyColorPerVertex(rgb=color)


def paintVertexColorALPHA(self):
	selectedVertices = pm.ls(sl=True, fl=True, type="float3")	
	if len(selectedVertices) == 0:
		return
	
	alpha = pm.floatField("A_field", q=True, v=True)					
	pm.polyColorPerVertex(alpha=alpha)
					

def storeVertexColorData(self):
	vtxList = pm.ls(sl=True, type="float3", fl=True)
	if len(vtxList) == 0:
		return
		
	# cancello tutti i set
	vtxColorSetsList = pm.ls(["vtxColor_*", "vtxAlpha_*"], type="objectSet")
	if len(vtxColorSetsList) > 0:
		pm.delete(vtxColorSetsList)
			
	# metto i vertici in un set colore e in un set alpha
	for vtx in vtxList:
		color = pm.polyColorPerVertex(vtx, q=True, rgb=True)	
		setName = "vtxColor_"+str(color[0]).replace(".", "_")+"_"+str(color[1]).replace(".", "_")+"_"+str(color[2]).replace(".", "_")	
		pm.select(vtx)
		if pm.objExists(setName):
			pm.sets(setName, add=True)
		else:	
			pm.sets(n=setName)	
		
		alpha = pm.polyColorPerVertex(vtx, q=True, a=True)							
		setName = "vtxAlpha_"+str(alpha[0]).replace(".", "_")	
		pm.select(vtx)
		if pm.objExists(setName):
			pm.sets(setName, add=True)
		else:	
			pm.sets(n=setName)	
	#pm.select(cl=True)							


def applyVertexColor(self):
	vtxColorSetsList = pm.ls("vtxColor_*", type="objectSet")
	vtxAlphaSetsList = pm.ls("vtxAlpha_*", type="objectSet")
	
	for colorSet in vtxColorSetsList:
		splitName = colorSet.name().split("_")
		color = [float(splitName[1]+"."+splitName[2]), float(splitName[3]+"."+splitName[4]), float(splitName[5]+"."+splitName[6])]
		pm.select(colorSet)
		pm.polyColorPerVertex(rgb=color)
	
	for alphaSet in vtxAlphaSetsList:
		splitName = alphaSet.name().split("_")
		alpha = float(splitName[1]+"."+splitName[2])
		pm.select(alphaSet)
		pm.polyColorPerVertex(a=alpha)	
	
	pm.select(cl=True)		
		

def transferVertexPaint(self):
	pm.transferAttributes(transferPositions=0, transferNormals=0, transferUVs=0, transferColors=2, sampleSpace=0, searchMethod=3, flipUVs=0, colorBorders=1)


def Vertex_Painter_UI():
    # Check if window exists and delete it
    if cmds.window("Vertex_Painter_Window", exists=True):
        cmds.deleteUI("Vertex_Painter_Window")

    # Create window with responsive layout
    window = cmds.window("Vertex_Painter_Window", title='Vertex Painter', widthHeight=(360, 420), minimizeButton=False, maximizeButton=False, sizeable=False)
	
    # Main column layout
    mainLayout = cmds.columnLayout(adjustableColumn=True)
	
    vertexPaintRowLayout1 = pm.rowLayout(nc=3, p=mainLayout)
    vertexPaintColumnLayout = pm.columnLayout(p=vertexPaintRowLayout1)

    pm.gridLayout(nc=3, cw=58, p=vertexPaintColumnLayout)
    pm.text("R")
    pm.text("G")
    pm.text("B")		
    pm.floatField("R_field", min=0.0, max=1.0, v=1, pre=1)
    pm.floatField("G_field", min=0.0, max=1.0, v=0, pre=1)
    pm.floatField("B_field", min=0.0, max=1.0, v=0, pre=1)

    pm.gridLayout(nc=2, cw=58, p=vertexPaintColumnLayout)
    pm.text(l="")
    pm.text("A")
    pm.text(l="")
    pm.floatField("A_field", min=0.0, max=1.0, v=1, pre=1)

    pm.columnLayout(w=179, adj=True, p=vertexPaintRowLayout1)
    pm.button(l="PAINT RGB", h=70, c=paintVertexColorRGB)
    pm.button(l="PAINT ALPHA", h=70, c=paintVertexColorALPHA)

    vertexPaintRowLayout2 = pm.rowLayout(nc=2, p=mainLayout)
    btnWidth = 177
    pm.button(l="Show Paint Layer", h=70, w=btnWidth, c=showPaintLayer)
    pm.button(l="Hide Paint Layer", h=70, w=btnWidth, c=hidePaintLayer)

    pm.separator(style="in", h=20, p=mainLayout)

    vertexPaintRowLayout2 = pm.rowLayout(nc=2, p=mainLayout)
    btnWidth = 177
    pm.button(l="Store Vertex Color Data", h=70, w=btnWidth, c=storeVertexColorData)
    pm.button(l="Apply Vertex Color", h=70, w=btnWidth, c=applyVertexColor)	

    pm.separator(style="in", h=20, p=mainLayout)

    pm.text("Select first the source mesh, then the target mesh", h=20, p=mainLayout)
    pm.button(l="Transfer Vertex Paint", h=70, c=transferVertexPaint, p=mainLayout)

    cmds.showWindow(window)
	
Vertex_Painter_UI()