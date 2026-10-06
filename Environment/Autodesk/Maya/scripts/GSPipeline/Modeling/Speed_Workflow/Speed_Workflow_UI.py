## Copyright (C) Sylvain Jubeau - All Rights Reserved
## By purchasing this script you may use it for non-commercial and commercial purpose.You can't distribute it or resell.

## Unauthorized copying of this file, via any medium is strictly prohibited
## Proprietary and confidential
## Written by Sylvain Jubeau , september  2018
##
##


## speedworkflow
## Copyright (c) 2018 Jubeau Sylvain
## Revision: 1.3  Date: 27/10/2018

##	Description:    This script help you to speed up your workflow



##==============================================


from os import path
import maya.cmds as cmds
import os
import subprocess

import maya.mel as mel

import pymel.core as pm
##==============================================
## HARD EDGE SELECTION
##==============================================
def hardselec(ignore):

	selected=pm.ls(l=1, sl=1)



	pm.polySelectConstraint(type=0x8000, mode=3, sm=1)
	pm.mel.resetPolySelectConstraint()
##==============================================
## AUTO UV HARD EDGE
##==============================================
def AUTOUV(ignore):






	##mel.eval("SelectToggleMode;")
	pm.mel.UVAutomaticProjection()

	mel.eval("MergeUV -d 20;")
	selected=pm.ls(l=1, sl=1)
	pm.polySelectConstraint(type=0x8000, mode=3, sm=1)
	pm.mel.resetPolySelectConstraint()
	pm.polyMapCut(ch=1)


	mel.eval("SelectMeshUVShell;")
	mel.eval("SelectAll;")

	pm.u3dUnfold(rs=6, ite=1, bi=1, p=1, ms=2048, tf=1)
	mel.eval("texOrientShells;")

	pm.u3dLayout(box=(0, 1, 0, 1), scl=1, mar=0.003, res=2048, rmx=360, rst=90, trs=0, spc=0.003, rmn=0)
	pm.polyMultiLayoutUV(ps=0.05, fr=1, gv=1, gu=1, psc=0, lm=1, l=2, su=1, sv=1, ov=0, sc=1, rbf=1, ou=0)
	pm.select(selected)
##==============================================
## Merge uv
##==============================================
def Mergeuv(ignore):
	selected=pm.ls(l=1, sl=1)
	mel.eval("MergeUV -d 50;")



	mel.eval("SelectMeshUVShell;")
	mel.eval("SelectAll;")

	pm.u3dUnfold(rs=6, ite=1, bi=1, p=1, ms=2048, tf=1)
	mel.eval("texOrientShells;")

	pm.u3dLayout(box=(0, 1, 0, 1), scl=1, mar=0.003, res=2048, rmx=360, rst=90, trs=0, spc=0.003, rmn=0)
	pm.polyMultiLayoutUV(ps=0.05, fr=1, gv=1, gu=1, psc=0, lm=1, l=2, su=1, sv=1, ov=0, sc=1, rbf=1, ou=0)
	pm.select(selected)

##==============================================
## 	Auto smoothing group
##==============================================
def asg(ignore):

	Selected=pm.ls(o=1, sl=1)
	mel.eval("SoftPolyEdgeElements 1;")
	Selected2=pm.ls(o=1, sl=1)
	temp=pm.ls(Selected[0] + ".map[*]")
	pm.select(temp)
	pm.mel.polySelectBorderShell(1)
	pm.mel.PolySelectConvert(20)
	EDGES=pm.filterExpand(ex=1, sm=32)
	removedEdges = []
	for eachEdge in EDGES:
		uvs=pm.polyListComponentConversion(eachEdge, fe=1, tuv=1)
		uvs=pm.ls(uvs, fl=1)
		if len(uvs)<=2:
			removedEdges.append(str(eachEdge))


	pm.select(removedEdges, d=1)

	mel.eval("SoftPolyEdgeElements 0;")
	pm.select(Selected)
##==============================================
## HARDEN EDGE
##==============================================
def hardenedge(ignore):

	mel.eval("SoftPolyEdgeElements 0;")

##==============================================
## SOFTEN EDGE
##==============================================
def softenedge(ignore):

	mel.eval("SoftPolyEdgeElements 1;")

##==============================================
## SOFTEN/harden EDGE
##==============================================
def softenhard(ignore):

	pm.polySoftEdge(a=46, ch=1)

##==============================================
## coorect topo
##==============================================
def correctopo(ignore):

	selected=pm.ls(l=1, sl=1)


	pm.polySelectConstraint(type=0x0008, mode=3, size=3)
	pm.polySelectConstraint(disable=1)
	pm.mel.resetPolySelectConstraint()
	mel.eval("Triangulate;")
	pm.select(selected)
	mel.eval("Quadrangulate;")
##==============================================
##make high poly
##==============================================
def hp(ignore):





	selected=cmds.ls(l=1, sl=1)

	cmds.polyRemesh(selected)
	cmds.polyRetopo(selected)




##==============================================
## Bevel manager
##==============================================
def previewbevel(ignore):


	selection = cmds.ls (selection=True)

	pm.polySelectConstraint(type=0x8000, mode=3, sm=1)
	pm.mel.resetPolySelectConstraint()

	BevelA= mel.eval("polyBevel3 -fraction 0.3 -offsetAsFraction 1 -autoFit 1 -depth 1 -mitering 0 -miterAlong 0 -chamfer 1 -segments 2 -worldSpace 1 -smoothingAngle 45 -subdivideNgons 1 -mergeVertices 1;")
	bevel=BevelA[0]


	if pm.window('myWindow', exists=1):
		pm.deleteUI('myWindow', window=1)
		
	pm.window('myWindow', title="Bevel")
	pm.columnLayout(adjustableColumn=True)

	slider=str(pm.attrFieldSliderGrp(columnAlign=(1, "right"),
		 min=0,
		 columnWidth=[(1, 84), (4, 1)],
		 label=bevel,
		 at=(BevelA[0] + ".fraction"), max=20,
		 adjustableColumn=3))

	slider1=str(pm.attrFieldSliderGrp(columnAlign=(1, "right"),
		 min=0,
		 columnWidth=[(1, 84), (4, 1)],
		 label="Radial",
		 at=(BevelA[0] + ".mitering"), max=3,
		 adjustableColumn=3))


	slider2=str(pm.attrFieldSliderGrp(columnAlign=(1, "right"),
		 min=0,
		 columnWidth=[(1, 84), (4, 1)],
		 label="Segments",
		 at=(BevelA[0] + ".segments"), max=20,
		 adjustableColumn=3))



	slider3=str(pm.attrFieldSliderGrp(columnAlign=(1, "right"),
		 min=-1,
		 columnWidth=[(1, 84), (4, 1)],
		 label="Weight",
		 at=(BevelA[0] + ".depth"), max=2,
		 adjustableColumn=3))
	pm.showWindow()

	cmds.select(selection)
##==============================================
## Low poly on
##==============================================
def low(ignore):




	selection = cmds.ls (selection=True)




	for select in selection:

		historyNodes = cmds.listHistory(select)
		for historyNode in historyNodes:
			bevelnode=cmds.ls('polyBevel*')


			cmds.select(bevelnode)
		for sel in bevelnode:
				v=cmds.setAttr('%s.nodeState' % (sel), 1,q=True)

	cmds.select(selection)

##==============================================
## Low poly off
##==============================================
def lowoff(ignore):




	selection = cmds.ls (selection=True)




	for select in selection:

		historyNodes = cmds.listHistory(select)
		for historyNode in historyNodes:
			bevelnode=cmds.ls('polyBevel*')


			cmds.select(bevelnode)
		for sel in bevelnode:
				v=cmds.setAttr('%s.nodeState' % (sel), 0,q=True)

	cmds.select(selection)





##==============================================
## weight normal
##==============================================
def weightnormal(ignore):




	selection = cmds.ls (selection=True)


	pm.polySelectConstraint(type=0x8000, mode=3, sm=1)
	pm.mel.resetPolySelectConstraint()

	mel.eval("polyBevel3 -fraction 0.15 -offsetAsFraction 1 -autoFit 1 -depth 1 -mitering 0 -miterAlong 0 -chamfer 1 -segments 1 -worldSpace 1 -smoothingAngle 180 -subdivideNgons 1 -mergeVertices 1;")



	cmds.select(selection)


	for select in selection:

			historyNodes = cmds.listHistory(select)
			for historyNode in historyNodes:
				bevelnode=cmds.ls('polyBevel*')


				cmds.select(bevelnode)
			for sel in bevelnode:
					v=cmds.setAttr('%s.nodeState' % (sel), 1,q=True)

	cmds.select(selection)
	mel.eval("ConvertSelectionToContainedFaces;")
	selectionfaces = cmds.ls (selection=True)

	for select in selection:

			historyNodes = cmds.listHistory(select)
			for historyNode in historyNodes:
				bevelnode=cmds.ls('polyBevel*')


				cmds.select(bevelnode)
			for sel in bevelnode:
					v=cmds.setAttr('%s.nodeState' % (sel), 0,q=True)

	cmds.select(selectionfaces)

	for select in selection:

			historyNodes = cmds.listHistory(select)
			for historyNode in historyNodes:
				mnode=cmds.ls('polyBevel*')


				cmds.select(bevelnode)
			for sel in bevelnode:
					v=cmds.setAttr('%s.mitering' % (sel), 4,q=True)

	faceselection=cmds.select(selectionfaces)



	Facesel=pm.filterExpand(sm=34)
	pm.select(cl=1)
	for Fac in Facesel:
			pm.select(Fac, r=1)
			normals=pm.polyInfo(faceNormals=1)
			querry = []
			querry=normals[0].split()
			plane = [0.0] * (3)
			plane[0]=float(querry[2])
			plane[1]=float(querry[3])
			plane[2]=float(querry[4])
			pm.mel.PolySelectConvert(3)
			pm.polyNormalPerVertex(xyz=(plane[0], plane[1], plane[2]))

	cmds.select(selection)
	pm.polyOptions(displayNormal=True)
	pm.polyOptions(pt=1)

##==============================================
## clean mesh
##==============================================
def htl(ignore):



	selected=pm.ls(sl=1)
	pm.polySoftEdge(selected, ch=1, angle=0.3)
	mel.eval("ConvertSelectionToEdges;")

	pm.polySelectConstraint(type=32768, m=3, sm=2)
	selectEdges=pm.ls(sl=1)
	pm.polyDelEdge(selectEdges, cv=True)
	pm.polySelectConstraint(dis=1)


	mel.eval("SelectVertexMask;")
	mel.eval("InvertSelection;")
	mel.eval("doDelete;")

	pm.select(selected)
	pm.mel.polyPerformAction("polySoftEdge -a 45", 'e', 0)
	pm.select(selected)


##==============================================
##OCTO HOLE
##==============================================
def octohole(ignore):


	selected=cmds.ls(l=1, sl=1)
	cmds.polyPoke()
	cmds.polySubdivideFacet(  )

	mel.eval("ShrinkPolygonSelectionRegion;")
	mel.eval("doDelete;")
	cmds.select(selected)
	mel.eval("polyConvertToShell;")

	mel.eval("ConvertSelectionToContainedEdges;")


	mel.eval("InvertSelection;")
	mel.eval("performPolyBridgeEdge 0;")

##==============================================
##id color green
##==============================================
def idcolorg():

	if pm.objExists('green'):

			cmds.sets(forceElement='greenSG', e=1)

	else:

		selectA=pm.ls(sl=1)

		crelambert=pm.shadingNode('lambert',name='green', asShader=1)
		pm.setAttr(crelambert + '.color', 0, 1, 0)
		pm.select(selectA)
		pm.hyperShade(assign=crelambert)

##==============================================
##id color red
##==============================================
def idcolorr():

	if pm.objExists('red'):

			cmds.sets(forceElement='redSG', e=1)

	else:



		selectA=pm.ls(sl=1)

		crelambert=pm.shadingNode('lambert',name='red', asShader=1)
		pm.setAttr(crelambert + '.color', 1, 0, 0)
		pm.select(selectA)
		pm.hyperShade(assign=crelambert)
##==============================================
##id color blue
##==============================================
def idcolorb():

	if pm.objExists('blue'):

			cmds.sets(forceElement='blueSG', e=1)

	else:



		selectA=pm.ls(sl=1)

		crelambert=pm.shadingNode('lambert',name='blue', asShader=1)
		pm.setAttr(crelambert + '.color', 0, 0, 1)
		pm.select(selectA)
		pm.hyperShade(assign=crelambert)
##==============================================
##id color yellow
##==============================================
def idcolory():

	if pm.objExists('yellow'):

			cmds.sets(forceElement='yellowSG', e=1)

	else:



		selectA=pm.ls(sl=1)

		crelambert=pm.shadingNode('lambert',name='yellow', asShader=1)
		pm.setAttr(crelambert + '.color', 1, 1, 0)
		pm.select(selectA)
		pm.hyperShade(assign=crelambert)
##==============================================
##id color cyan
##==============================================
def idcolorc():



	if pm.objExists('cyan'):

			cmds.sets(forceElement='cyanSG', e=1)

	else:



		selectA=pm.ls(sl=1)

		crelambert=pm.shadingNode('lambert',name='cyan', asShader=1)
		pm.setAttr(crelambert + '.color', 0, 1, 1)
		pm.select(selectA)
		pm.hyperShade(assign=crelambert)
##==============================================
##id color majenta
##==============================================
def idcolorm():


	if pm.objExists('magenta'):

			cmds.sets(forceElement='magentaSG', e=1)

	else:



		selectA=pm.ls(sl=1)

		crelambert=pm.shadingNode('lambert',name='magenta', asShader=1)
		pm.setAttr(crelambert + '.color', 1, 0, 1)
		pm.select(selectA)
		pm.hyperShade(assign=crelambert)
##==============================================
##id color default
##==============================================
def idcolorlambert():


	if pm.objExists('lambert1'):

			cmds.sets(forceElement='initialShadingGroup', e=1)

	else:



		selectA=pm.ls(sl=1)

		crelambert=pm.shadingNode('lambert',name='lambert1', asShader=1)
		pm.setAttr(crelambert + '.color', 1, 0, 1)
		pm.select(selectA)
		pm.hyperShade(assign=crelambert)


##==============================================
##baking idcolormap
##==============================================
def bakeid(ignore):
	colormap = cmds.textField(myidpath, query=True, text=True)

	selected=pm.ls(l=1, sl=1)
	mel.eval("Duplicate;")
	selected2=pm.ls(l=1, sl=1)
	pm.rename(selected2,"baking")
	mel.eval("performSurfaceSampling 1;")
	pm.select(selected)
	mel.eval("string $selected[] = `ls -sl -o`; for( $name in $selected) surfaceSamplingAddSource( $name, true );")


	mel.eval("addMapUIFrame 2;")
	pm.mel.surfaceSamplerFileNameCB(2, 0, colormap)

	print(myidpath)

##==============================================
## SET bakeid
##==============================================
def setbakeid(ignore):


	folderpath=cmds.fileDialog2(okc="Set mapid path", fileMode=0)

	if len(folderpath)>0:
		cmds.textField(myidpath, e=1, tx=(folderpath[0]))


##==============================================
## diff boolean
##==============================================
def Diff():


	selected=pm.ls(os=1)

	selection=len(selected)

	pm.polyCBoolOp(preserveColor=0, ch=1, name=selected[0], classification=1, op=2)

	for L in range(1,selection):
		getform=pm.ls(selected[L], dag=1)

		pm.setAttr((getform[1] + ".visibility"),
			1)
		pm.setAttr((getform[2] + ".intermediateObject"),
			0)

		pm.setAttr((getform[2] + ".overrideEnabled"),
			1)
		pm.setAttr((getform[2] + ".overrideShading"),
			0)

		pm.setAttr((getform[2] + ".primaryVisibility"),
			0)

		pm.setAttr((getform[2] + ".overrideColor"),
			0)


##==============================================
## union boolean
##==============================================
def union():


	selected=pm.ls(os=1)

	selection=len(selected)

	pm.polyCBoolOp(preserveColor=0, ch=1, name=selected[0], classification=1, op=1)

	for L in range(1,selection):
		getform=pm.ls(selected[L], dag=1)

		pm.setAttr((getform[1] + ".visibility"),
			1)
		pm.setAttr((getform[2] + ".intermediateObject"),
			0)

		pm.setAttr((getform[2] + ".overrideEnabled"),
			1)
		pm.setAttr((getform[2] + ".overrideShading"),
			0)

		pm.setAttr((getform[2] + ".primaryVisibility"),
			0)

		pm.setAttr((getform[2] + ".overrideColor"),
			17)

#==============================================
## inter boolean
##==============================================
def inter():


	selected=pm.ls(os=1)

	selection=len(selected)

	pm.polyCBoolOp(preserveColor=0, ch=1, name=selected[0], classification=1, op=3)

	for L in range(1,selection):
		getform=pm.ls(selected[L], dag=1)

		pm.setAttr((getform[1] + ".visibility"),
			1)
		pm.setAttr((getform[2] + ".intermediateObject"),
			0)

		pm.setAttr((getform[2] + ".overrideEnabled"),
			1)
		pm.setAttr((getform[2] + ".overrideShading"),
			0)

		pm.setAttr((getform[2] + ".primaryVisibility"),
			0)

		pm.setAttr((getform[2] + ".overrideColor"),
			17)



#==============================================
## DIFF + INT boolean
##==============================================
def DIIFINT(ignore):

	selected=pm.ls(l=1, sl=1)
	pm.duplicate( un=True )

	selection=len(selected)

	pm.polyCBoolOp(preserveColor=0, ch=1, name=selected[0], classification=1, op=2)


	pm.select(selected)

	pm.polyCBoolOp(preserveColor=0, ch=1, name=selected[0], classification=1, op=3)

##==============================================
## crease hard edge
##==============================================
def crease(ignore):

	pm.polySelectConstraint(type=0x8000, mode=3, sm=1)
	pm.mel.resetPolySelectConstraint()

	cmds.polyCrease( value=2)
	mel.eval("PolyCreaseTool;")

##==============================================
## uncrease all
##==============================================
def uncreaseall(true):

	selected=pm.ls(l=1, sl=1)

	cmds.polyCrease( value=0)
	mel.eval("PolyCreaseTool;")


#==============================================
## inset slected
##==============================================
def inset(ignore):

	selection=pm.ls(selection=True)










	InsetA=pm.polyExtrudeFacet((selection),divisions=1, off=0.02, taper=1, pvy=0.5, pvx=0, pvz=0, thickness=0.000, twist=0, smoothingAngle=30, keepFacesTogether=1, constructionHistory=1)
	Inset=InsetA[0]


	if pm.window('myWindow', exists=1):
		pm.deleteUI('myWindow', window=1)

	pm.window('myWindow', title="attrFieldSliderGrp")
	pm.columnLayout(adjustableColumn=True)

	slider=str(pm.attrFieldSliderGrp(columnAlign=(1, "right"),
		 min=0,
		 columnWidth=[(1, 84), (4, 1)],
		 label="Inset",
		 at=(Inset + ".offset"), max=1,
		 adjustableColumn=3))



	pm.showWindow()

#==============================================
## inset all
##==============================================
def insetall(ignore):

	selection=pm.ls(sl=1)

	mel.eval("ConvertSelectionToContainedFaces;")
	selection2=pm.ls(sl=1)
	pm.select(selection)

	faces=pm.polyEvaluate(selection[0], f=1)
	for i in range(0,faces):






		InsetB=pm.polyExtrudeFacet((selection2[0] + ".f[" + str(i) + "]"), divisions=1, off=0.02, taper=1, pvy=0.5, pvx=0, pvz=0, thickness=0.000, twist=0, smoothingAngle=30, keepFacesTogether=1, constructionHistory=1)
		Inset=InsetB[0]
		pm.select(selection2)

	if pm.window('myWindow', exists=1):
		pm.deleteUI('myWindow', window=1)

	pm.window('myWindow', title="attrFieldSliderGrp")
	pm.columnLayout(adjustableColumn=True)

	slider=str(pm.attrFieldSliderGrp(columnAlign=(1, "right"),
		 min=0,
		 columnWidth=[(1, 84), (4, 1)],
		 label="Inset",
		 at=(Inset + ".offset"), max=1,
		 adjustableColumn=3))



	pm.showWindow()



#==============================================
## export 2 painter
##==============================================
def export(ignore):
	path="c:\\temp\\"

	filename="exported"
	extension=".fbx"
	fullpath=path + filename + extension

	mel.eval("FBXExportTriangulate -v true;")
	mel.eval("FBXExportSmoothingGroups -v true;")
	pm.FBXExport(['-f',fullpath,'-s'])




	subprocess.Popen(['C:/Program Files/Allegorithmic/Substance Painter/substance painter.exe' ,'--mesh' , 'c:/temp/exported.fbx'])


#==============================================
## quad cap
##==============================================
def quadcap(ignore):
	selectedvert=pm.ls(sl=1)
	mel.eval("polyChamferVtx 1 0.75 0;")
	pm.select(selectedvert)
	mel.eval("ConvertSelectionToEdges;")

	pm.mel.toggleSelMode()
	pm.selectMode(object=True )




	mel.eval("ConvertSelectionToVertices;")
	mel.eval("ShrinkLoopPolygonSelectionRegion;")
	mel.eval("invertSelection;")
	mel.eval("ConvertSelectionToEdges;")
	mel.eval("ShrinkPolygonSelectionRegion;")





	mel.eval("ConvertSelectionToContainedFaces;")
	selctedfacemid=pm.ls(sl=1)


	cmds.polyCut( selctedfacemid,cd='X')
	pm.select(selctedfacemid)
	cmds.polyCut( selctedfacemid,cd='Z')

	mel.eval("ConvertSelectionToEdges;")

	pm.mel.toggleSelMode()
	pm.selectMode(object=1)


	mel.eval("ConvertSelectionToVertices;")
	mel.eval("ShrinkLoopPolygonSelectionRegion;")
	mel.eval("invertSelection;")
	mel.eval("ConvertSelectionToContainedFaces;")


	cmds.polyCut( cd='Z')

	pm.mel.toggleSelMode()
	pm.selectMode(object=1)
	mel.eval("ConvertSelectionToVertices;")
	mel.eval("PolyMerge;")

	pm.mel.toggleSelMode()
	pm.selectMode(object=1)
	selectedobj=pm.ls(sl=1)
	mel.eval("ConvertSelectionToVertices;")
	mel.eval("ShrinkLoopPolygonSelectionRegion;")
	selctedvertex1=pm.ls(sl=1)
	mel.eval("invertSelection;")
	mel.eval("ShrinkPolygonSelectionRegion;")
	mel.eval("ConvertSelectionToEdgePerimeter;")








	pm.mel.toggleSelMode()
	pm.selectMode(object=1)
	selectedobject=pm.ls(sl=1)
	mel.eval("ConvertSelectionToEdges;")
	mel.eval("ShrinkLoopPolygonSelectionRegion;")
	mel.eval("invertSelection;")
	mel.eval("ShrinkPolygonSelectionRegion;")
	mel.eval("GrowLoopPolygonSelectionRegion;")
	mel.eval("GrowPolygonSelectionRegion;")
	mel.eval("ShrinkLoopPolygonSelectionRegion;")
	mel.eval("ConvertSelectionToEdgePerimeter;")

	mel.eval("CreateCurveFromPoly;")
	selected2=pm.ls(l=1, sl=1)
	pm.select(selectedobject)

	mel.eval("ConvertSelectionToEdges;")
	mel.eval("ShrinkLoopPolygonSelectionRegion;")
	mel.eval("invertSelection;")
	mel.eval("ShrinkPolygonSelectionRegion;")
	mel.eval("GrowLoopPolygonSelectionRegion;")
	mel.eval("ConvertSelectionToFaces;")

	mel.eval("ShrinkPolygonSelectionRegion;")

	selectedfaces=pm.ls(l=1, sl=1)
	mel.eval("ConvertSelectionToContainedEdges;")
	mel.eval("DuplicateCurve;")
	selected3=pm.ls(l=1, sl=1)
	pm.select(selected2+selected3)
	mel.eval("CutCurve;")
	mel.eval("Boundary;")
	selectedbound=pm.ls(l=1, sl=1)
	pm.nurbsToPoly(selectedbound, uss=1, ch=1, ft=0.0604, d=0.1, pt=1, f=2, mrt=0, mel=0.9866, ntr=0, vn=1, pc=200, chr=0.1, un=1, vt=3, ut=3, ucr=0, cht=0.2, mnd=1, es=0, uch=0)

	selectedcap=pm.ls(l=1, sl=1)
	pm.select(selectedfaces)
	mel.eval("doDelete;")
	pm.select(selectedobj+selectedcap)


	pm.select(selectedcap)
	mel.eval("ReversePolygonNormals;")

	pm.select(selectedobj+selectedcap)
	mel.eval("CombinePolygons;")
	selectedcomb=pm.ls(l=1, sl=1)
	mel.eval("ConvertSelectionToVertices;")
	mel.eval("performPolyMerge 0;")


	pm.select(selected2+selected3+selectedbound)
	mel.eval("doDelete;")

	pm.select(selectedcomb)
	mel.eval("DeleteHistory;")
	pm.select("detachedCurve*")
	mel.eval("doDelete;")
	pm.select(selectedcomb)

##==============================================
## getname
##==============================================
def getname(ignore):

	selectedObject = cmds.ls(sl=True)
	selected = cmds.ls(sl=True)
	for eachSel in selected:

		cmds.textField(selectedobj, e=1, tx=(selected[0] ))
		# # Create Nodes
		objname= cmds.textField(selectedobj, query=True, text=True)


##==============================================
## renaming tools
##==============================================

def renamehigh(ignore):
	objname= cmds.textField(selectedobj, query=True, text=True)
	prefixname= cmds.textField(prefix, query=True, text=True)
	sel=pm.ls(sl=1)
	pm.select(cl=1)


	newNamePrefix=objname
	for i in range(0,len(sel)):
		pm.rename(sel[i],
			(newNamePrefix  + "_" + prefixname))


##==============================================
## window
##==============================================

if cmds.window("SpeedWorkflow", exists =True):
	cmds.deleteUI("SpeedWorkflow")

if cmds.dockControl("SpeedWorkflowDock", exists =True):
	cmds.deleteUI("SpeedWorkflowDock")

myWindow = cmds.window("SpeedWorkflow", t="Speed workflow 1.4", tlb=True, menuBar=True, sizeable=False)
buttonForm = cmds.formLayout( parent = myWindow)
allowedAreas = ['all']
cmds.dockControl("SpeedWorkflowDock", l = "Speed workflow 1.4",area='left', content=myWindow, allowedArea=allowedAreas,floating=True,fixedHeight= False ,fixedWidth= False,width=200, height=420)

addpath = path.join(cmds.internalVar(upd=True), 'icons', 'add.png')
addpathhallow = path.join(cmds.internalVar(upd=True), 'icons', 'add_hallow.png')
addpathchris = path.join(cmds.internalVar(upd=True), 'icons', 'add_chris.png')
diffpath = path.join(cmds.internalVar(upd=True), 'icons', 'diff.png')
diffpathhallow = path.join(cmds.internalVar(upd=True), 'icons', 'diff_hallow.png')
diffpathchris = path.join(cmds.internalVar(upd=True), 'icons', 'diff_chris.png')
interpath = path.join(cmds.internalVar(upd=True), 'icons', 'inter.png')
interpathhallow = path.join(cmds.internalVar(upd=True), 'icons', 'inter_hallow.png')
interpathchris = path.join(cmds.internalVar(upd=True), 'icons', 'inter_chris.png')
pumpkin = path.join(cmds.internalVar(upd=True), 'icons', 'pumpkin.png')
chrisbanner = path.join(cmds.internalVar(upd=True), 'icons', 'Flakes_banner.png')
invisible = path.join(cmds.internalVar(upd=True), 'icons', 'invisible.png')


cmds.menu( label='Settings')




tab=cmds.tabLayout('windowLayout',parent = buttonForm,width=205,bs="none")
cmds.separator( style='none', height=2,parent=buttonForm)


mode=cmds.columnLayout('Mod',parent = tab)
topo=cmds.columnLayout('Topo',parent = tab)
uv=cmds.columnLayout('Uv',parent = tab)
id=cmds.columnLayout('IDcolor',parent = tab)

ict2 = cmds.text(label='',height=5,backgroundColor=(0.3,0.6,0.7),width=205,parent=mode)
ict3 = cmds.text(label='',height=5,parent=topo,backgroundColor=(0.3,0.6,0.7),width=205 )
ict4 = cmds.text(label='',height=5,parent=uv,backgroundColor=(0.3,0.6,0.7),width=205 )
ict5 = cmds.text(label='',height=5,parent=id,backgroundColor=(0.3,0.6,0.7),width=205 )
## Onglet Mode








def something(ignore):
	print("Default theme")


	cmds.text(ict2, e=True, label='',height=5,backgroundColor=(0.3,0.6,0.7),width=205,parent=mode)
	cmds.text(ict3, e=True,label='',height=5,parent=topo,backgroundColor=(0.3,0.6,0.7),width=205 )
	cmds.text(ict4, e=True,label='',height=5,parent=uv,backgroundColor=(0.3,0.6,0.7),width=205 )
	cmds.text(ict5, e=True,label='',height=5,parent=id,backgroundColor=(0.3,0.6,0.7),width=205 )
	cmds.separator(ict6, e=True,style='none', height=5, parent=rowLayout03,width=10)
	cmds.iconTextButton(ict7, e=True,image1=diffpath, command=Diff, parent=rowLayout03)
	cmds.separator(ict8, e=True, style='none', height=5, parent=rowLayout03,width=30)
	cmds.iconTextButton(ict9, e=True, image1=addpath, command=union, parent=rowLayout03,width=37)
	cmds.separator(ict10, e=True, style='none', height=5, parent=rowLayout03,width=30)
	cmds.iconTextButton(ict11, e=True, image1=interpath, command=inter, parent=rowLayout03,width=37)
	cmds.separator(ict12, e=True, style='none', height=5, parent=rowLayout03,width=15)
	cmds.iconTextButton(ict13, e=True,image1=invisible, parent=mode,width=37)
def something_else(ignore):
	print("Halloween theme")

	cmds.text(ict2, e=True, label='',height=5,backgroundColor=(0.8,0.3,0.1),width=205,parent=mode)
	cmds.text(ict3, e=True,label='',height=5,parent=topo,backgroundColor=(0.8,0.3,0.1),width=205 )
	cmds.text(ict4, e=True,label='',height=5,parent=uv,backgroundColor=(0.8,0.3,0.1),width=205 )
	cmds.text(ict5, e=True,label='',height=5,parent=id,backgroundColor=(0.8,0.3,0.1),width=205 )
	cmds.separator(ict6, e=True,style='none', height=5, parent=rowLayout03,width=10)
	cmds.iconTextButton(ict7, e=True,image1=diffpathhallow, command=Diff, parent=rowLayout03)
	cmds.separator(ict8, e=True, style='none', height=5, parent=rowLayout03,width=30)
	cmds.iconTextButton(ict9, e=True, image1=addpathhallow , command=union, parent=rowLayout03,width=37)
	cmds.separator(ict10, e=True, style='none', height=5, parent=rowLayout03,width=30)
	cmds.iconTextButton(ict11, e=True, image1=interpathhallow , command=inter, parent=rowLayout03,width=37)
	cmds.separator(ict12, e=True, style='none', height=5, parent=rowLayout03,width=15)
	cmds.iconTextButton(ict13, e=True, image1=pumpkin, parent=mode,width=205)
def something_else1(ignore):
	print("Christmas theme")

	cmds.text(ict2, e=True, label='',height=5,backgroundColor=(0.8,0,0.1),width=205,parent=mode)
	cmds.text(ict3, e=True,label='',height=5,parent=topo,backgroundColor=(0.8,0,0.1),width=205 )
	cmds.text(ict4, e=True,label='',height=5,parent=uv,backgroundColor=(0.8,0,0.1),width=205 )
	cmds.text(ict5, e=True,label='',height=5,parent=id,backgroundColor=(0.8,0,0.1),width=205 )
	cmds.separator(ict6, e=True,style='none', height=5, parent=rowLayout03,width=10)
	cmds.iconTextButton(ict7, e=True,image1=diffpathchris, command=Diff, parent=rowLayout03)
	cmds.separator(ict8, e=True, style='none', height=5, parent=rowLayout03,width=30)
	cmds.iconTextButton(ict9, e=True, image1=addpathchris , command=union, parent=rowLayout03,width=37)
	cmds.separator(ict10, e=True, style='none', height=5, parent=rowLayout03,width=30)
	cmds.iconTextButton(ict11, e=True, image1=interpathchris , command=inter, parent=rowLayout03,width=37)
	cmds.separator(ict12, e=True, style='none', height=5, parent=rowLayout03,width=15)
	cmds.iconTextButton(ict13, e=True, image1=chrisbanner, parent=mode,width=200)

cmds.menuItem(label='Default theme', command = something)
cmds.menuItem(label='Halloween theme', command = something_else)
cmds.menuItem(label='Christmas theme', command = something_else1)
cmds.separator( style='none', height=2, parent=mode)
bool=cmds.frameLayout(l = "LIVE BOOLEAN", cll =1, cl =0, backgroundColor=(0.18,0.18,0.18), font= 'boldLabelFont',parent=mode )


cmds.separator( style='none', height=2, parent=bool)
rowLayout03 = cmds.rowColumnLayout( numberOfColumns=7, parent=bool)
rowLayout04 = cmds.rowColumnLayout( numberOfColumns=7, parent=bool)
cmds.separator( style='none', height=5, parent=mode)

## iconpath


ict6 =cmds.separator( style='none', height=5, parent=rowLayout03,width=10)
ict7 =cmds.iconTextButton(image1=diffpath, command=Diff, parent=rowLayout03)
ict8 =cmds.separator( style='none', height=5, parent=rowLayout03,width=30)
ict9 = cmds.iconTextButton( image1=addpath, command=union, parent=rowLayout03,width=37)
ict10 =cmds.separator( style='none', height=5, parent=rowLayout03,width=30)
ict11 =cmds.iconTextButton( image1=interpath, command=inter, parent=rowLayout03,width=37)
ict12 =cmds.separator( style='none', height=5, parent=rowLayout03,width=15)


cmds.separator( style='none', height=5, parent=rowLayout04,width=6)
cmds.text(label='difference',parent=rowLayout04)
cmds.separator( style='none', height=5, parent=rowLayout04,width=20)
cmds.text(label='union',parent=rowLayout04)
cmds.separator( style='none', height=5, parent=rowLayout04,width=20)
cmds.text(label='intersection',parent=rowLayout04)
cmds.separator( style='none', height=5, parent=rowLayout04,width=10)

cmds.separator( style='none', height=2, parent=bool)
cmds.button( label='Diff + Int', command=DIIFINT, parent=bool,width=205)

cmds.separator( style='none', height=2, parent=mode)
creaselayout=cmds.frameLayout(l = "CREASE", cll =1, cl =0, backgroundColor=(0.18,0.18,0.18), font= 'boldLabelFont',parent=mode )



cmds.button( label='Crease hard edge', command=crease, parent=creaselayout,width=205)

cmds.button( label='Uncrease all', command=uncreaseall, parent=creaselayout,width=205)



cmds.separator( style='none', height=8, parent=mode)
tools=cmds.frameLayout(l = "TOOLS", cll =1, cl =0, backgroundColor=(0.18,0.18,0.18), font= 'boldLabelFont',parent=mode )


cmds.button( label='Inset', command=inset, parent=tools,width=205)

cmds.button( label='Cylinder Quad Cap', command=quadcap, parent=tools,width=205)

cmds.button( label='Octogonal Hole', command=octohole, parent=tools,width=205)

cmds.separator( style='none', height=5, parent=mode)

ict13 =cmds.iconTextButton( image1=invisible, parent=mode)


## Onglet TOPO
cmds.separator( style='none', height=2, parent=topo)


topotools=cmds.frameLayout(l = "TOPO TOOLS", cll =1, cl =0, backgroundColor=(0.18,0.18,0.18), font= 'boldLabelFont',parent=topo )
cmds.button( label='Clean Mesh', command=htl, parent=topotools,width=205)
cmds.separator( style='none', height=10, parent=topo)
cmds.button( label='Correct topo', command=correctopo,parent=topotools,width=205)

cmds.separator( style='none', height=10, parent=topo)
cmds.button( label='Remesh', command=hp, parent=topotools,width=205)

cmds.separator( style='none', height=10, parent=topo)
cmds.button( label='Weight Normal', command=weightnormal, parent=topotools,width=205)

topotools2=cmds.frameLayout(l = "BEVEL", cll =1, cl =0, backgroundColor=(0.18,0.18,0.18), font= 'boldLabelFont',parent=topo )

cmds.button( label='Add Bevel', command=previewbevel, parent=topotools2,width=205)

cmds.separator( style='none', height=10, parent=topo)
cmds.button( label='Toggle Bevel ON', command=lowoff, parent=topotools2,width=205)

cmds.separator( style='none', height=10, parent=topo)
cmds.button( label='Toggle Bevel OFF', command=low, parent=topotools2,width=205)





cmds.separator( style='none', height=2, parent=topo)




## Onglet uv

cmds.separator( style='none', height=2, parent=uv)




edgetools=cmds.frameLayout(l = "EDGE TOOLS", cll =1, cl =0, backgroundColor=(0.18,0.18,0.18), font= 'boldLabelFont',parent=uv )
cmds.button( label='Hard Edge Selection', command=hardselec,parent=edgetools,width=205)
cmds.separator( style='none', height=10,parent=uv)
cmds.button( label='Harden Edge', command=hardenedge,parent=edgetools,width=205)
cmds.separator( style='none', height=10,parent=uv)
cmds.button( label='Soften Edge', command=softenedge,parent=edgetools,width=205)
cmds.separator( style='none', height=10,parent=uv)
cmds.button( label='Soften/Hard Edge', command=softenhard,parent=edgetools,width=205)
cmds.separator( style='none', height=10,parent=uv)
autouv=cmds.frameLayout(l = "UV TOOLS", cll =1, cl =0, backgroundColor=(0.18,0.18,0.18), font= 'boldLabelFont',parent=uv )
cmds.button( label='Auto UV ', command=AUTOUV,parent=autouv,width=205)
cmds.separator( style='none', height=2, parent=uv)
cmds.button( label='Merge UV shell ', command=Mergeuv,parent=autouv,width=205)
cmds.separator( style='none', height=2, parent=uv)
cmds.separator( style='none', height=2, parent=uv)
cmds.button( label='Auto Smoothing Group ', command=asg,parent=autouv,width=205)
cmds.separator( style='none', height=2, parent=uv)
## Onglet idcolor

greenpath = path.join(cmds.internalVar(upd=True), 'icons', 'green.png')
redpath = path.join(cmds.internalVar(upd=True), 'icons', 'red.png')
bluepath = path.join(cmds.internalVar(upd=True), 'icons', 'blue.png')
yellowpath = path.join(cmds.internalVar(upd=True), 'icons', 'yellow.png')
cyanpath = path.join(cmds.internalVar(upd=True), 'icons', 'cyan.png')
magentapath = path.join(cmds.internalVar(upd=True), 'icons', 'magenta.png')
nonepath = path.join(cmds.internalVar(upd=True), 'icons', 'none.png')



cmds.separator( style='none', height=2, parent=id)

idlayout=cmds.frameLayout(l = "ID COLOR", cll =1, cl =0, backgroundColor=(0.18,0.18,0.18), font= 'boldLabelFont',parent=id )
cmds.separator( style='none', height=7, parent=idlayout)
rowLayout1 = cmds.rowColumnLayout( numberOfColumns=11, columnWidth=[(1, 30), (2, 2), (3, 30), (4, 2), (5,30), (6, 2), (7, 30), (8, 2), (9, 30), (10, 2), (11, 30) ],parent=idlayout )

cmds.iconTextButton(image1=greenpath, command=idcolorg,parent = rowLayout1,width=30)
cmds.separator( style='none', parent=rowLayout1,width=2)
cmds.iconTextButton(image1=redpath, command=idcolorr,parent = rowLayout1,width=30)
cmds.separator( style='none', parent=rowLayout1,width=2)
cmds.iconTextButton(image1=bluepath, command=idcolorb,parent = rowLayout1,width=30)
cmds.separator( style='none', parent=rowLayout1,width=2)
cmds.iconTextButton(image1=yellowpath, command=idcolory,parent = rowLayout1,width=30)
cmds.separator( style='none', parent=rowLayout1,width=2)
cmds.iconTextButton(image1=cyanpath, command=idcolorc,parent = rowLayout1,width=30)
cmds.separator( style='none', parent=rowLayout1,width=2)
cmds.iconTextButton(image1=magentapath, command=idcolorm,parent = rowLayout1,width=30)
cmds.separator( style='none', parent=rowLayout1,width=2)






rowLayout05 = cmds.rowColumnLayout( numberOfColumns=1, columnWidth=[(1, 20) ] , parent=idlayout)
cmds.iconTextButton(image1=nonepath, command=idcolorlambert,parent = rowLayout05,width=30)



global rowLayout2

rowLayout2 = cmds.rowColumnLayout( numberOfColumns=3, columnWidth=[(1, 150),(2, 10), (3, 20) ] , parent=idlayout)

myidpath = cmds.textField(text='search directory', width=150, height=20, p=rowLayout2)

cmds.symbolButton(image="folder-open.png", command=setbakeid, width=20,p=rowLayout2)




cmds.button( label='Bake idcolormap', command=bakeid,parent=idlayout,width=200)
cmds.separator( style='none', height=2, parent=idlayout)

exportsp=cmds.frameLayout(l = "RENAME", cll =1, cl =0, backgroundColor=(0.18,0.18,0.18), font= 'boldLabelFont',parent=id )



rowLayout3 = cmds.rowColumnLayout( numberOfColumns=3, columnWidth=[(1, 110),(2, 20), (3, 50) ] , parent=exportsp)
cmds.text(label='Object name',parent=rowLayout3)
cmds.separator( style='none', width=2, parent=rowLayout3)
cmds.text(label='Prefix',parent=rowLayout3)
selectedobj = cmds.textField(text='Old name', width=110, height=20, parent=rowLayout3)
cmds.separator( style='none', width=20, parent=rowLayout3)
prefix = cmds.textField(text='', width=50, height=20,parent=rowLayout3)

cmds.button( label='Get Obj name', command=getname,parent=exportsp,width=205)
cmds.button( label='Rename', command=renamehigh,parent=exportsp,width=205)



exportsp=cmds.frameLayout(l = "EXPORT", cll =1, cl =0, backgroundColor=(0.18,0.18,0.18), font= 'boldLabelFont',parent=id )
cmds.button( label='export to painter', command=export,parent=exportsp,width=205)

cmds.window (myWindow, edit=True)


