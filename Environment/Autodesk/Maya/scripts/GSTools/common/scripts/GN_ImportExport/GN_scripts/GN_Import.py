import maya.cmds as cmds
import maya.mel as mel
import maya.api.OpenMaya as om
from six.moves import range
from collections import OrderedDict
from webbrowser import open_new_tab
from functools import partial
import os, os.path, re, difflib

from ..GN_source import GN_GetSelection, GN_Print

def sorted_alphanumeric(data):
	convert = lambda text: int(text) if text.isdigit() else text.lower()
	alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ] 
	return sorted(data, key=alphanum_key)

def hex_to_rgba(hex):
	if len(hex) == 8:
		rgba = [int(hex[i:i+2], 16) / 255. for i in (2, 4, 6, 0)]
	else:
		rgba = [1.0, 1.0, 1.0, 1.0]
	return rgba

def hex_to_color(hexList):
	colorList = om.MColorArray()
	for hex in hexList:
		if len(hex) == 8:
			rgba = [int(hex[i:i+2], 16) / 255. for i in (2, 4, 6, 0)]
			color = om.MColor().setColor(rgba, model=om.MColor.kRGB, dataType=om.MColor.kFloat)
		else:
			rgba = [1.0, 1.0, 1.0, 1.0]
			color = om.MColor().setColor(rgba, model=om.MColor.kRGB, dataType=om.MColor.kFloat)
		
		colorList.append(color)

	return colorList

def GN_importVertexColor(objects, file):
	# Initialize variables
	prefix = "|GN_Import:"
	objectsAll, colorAll, vtxAll = [], [], []

	# Read file content and check where file was exported from
	fileContent = open(file, 'r').read()
	zbrush = re.match(r"^# File exported by ZBrush.*$\n", fileContent, re.MULTILINE)
	blender = re.match(r"^# Blender.*$\n", fileContent, re.MULTILINE)

	# If file from ZBrush
	if zbrush:
		# Get object names
		geometry = re.findall(r"^g\s(\w+)$\n", fileContent, re.MULTILINE)
		objectsAll = [prefix + geo for geo in geometry]
		
		# Get vertex colors
		hexList = []
		mrgb_lines = re.findall(r"^#MRGB\s([a-z0-9]+)$\n", fileContent, re.MULTILINE)
		for line in mrgb_lines:
			hexList.extend([line[i:i+8] for i in range(0, len(line), 8)])
		
		# Get vertices
		if len(geometry) > 1:
			total = 0
			objects_data = re.split(r"^g\s\w+$\n", fileContent, 0, re.MULTILINE)[1:]
			for data in objects_data:
				vertices = re.findall(r"\b\s(\d+)/", data)
				vertices = list(OrderedDict.fromkeys(vertices))
				vertexCount = len(vertices)
				if total <= 0:
					vertices = list(range(vertexCount))
				else:
					minimum = total + 1
					vertices = [int(vtx) - minimum for vtx in vertices]
				maximum = total + vertexCount
				hex = hexList[total:maximum]
				color = hex_to_color(hex)
				colorAll.append(color)
				vtxAll.append(vertices)
				total += vertexCount
		else:
			vertices = list(range(len(hexList)))
			color = hex_to_color(hexList)
			colorAll.append(color)
			vtxAll.append(vertices)
	
	# If file not from ZBrush
	else:
		# If file from Blender
		if blender:
			# Get object names
			geometry = re.findall(r"^g\s(\w+)$\n", fileContent, re.MULTILINE)
			objectsAll = [prefix + geo for geo in geometry]
			objects_data = re.split(r"^g\s\w+$\n", fileContent, 0, re.MULTILINE)[1:]
		else:
			objects_data = fileContent.split("g default")[1:]
		
		for data in objects_data:
			# If file not from Blender
			if not blender:
				# Get object name
				objectName = re.search(r"^g\s(\w+)$\n", data, re.MULTILINE).group()
				objectsAll.append(prefix + objectName)
			
			# Get vertex colors
			mrgb_lines = re.findall(r"^#MRGB\s([a-z0-9]+)$\n", data, re.MULTILINE)
			if len(mrgb_lines):
				hexList = []
				for line in mrgb_lines:
					hexList.extend([line[i:i+8] for i in range(0, len(line), 8)])
				color = hex_to_color(hexList)
				colorAll.append(color)
				vtxAll.append([])
			else:
				colorAll.append([])
				vtxAll.append([])
		
	# Progress bar
	gMainProgressBar = mel.eval("$gMainProgressBar = $gMainProgressBar")
	cmds.progressBar(gMainProgressBar, e=True, bp=True, ii=True, st="Importing vertex color...", max=len(objectsAll))

	# Loop objects
	for i, obj in enumerate(objectsAll):
		# Progress bar
		if cmds.progressBar(gMainProgressBar, q=True, ic=True):
			break

		# Check that object has color data
		if not len(colorAll[i]):
			continue

		# Get fnMesh
		object = difflib.get_close_matches(obj, objects)[0]
		objList = om.MSelectionList().add(object)
		dag = objList.getDagPath(0)
		fnMesh = om.MFnMesh(dag)

		# Get vertices if file not from ZBrush
		if not zbrush:
			vertexCount = fnMesh.numVertices
			vtxAll[i] = list(range(vertexCount))
			# Doesn't seem to work properly
			'''
			if i != 0:
				vertices = fnMesh.getVertices()[1]
				vtxAll[i] = list(OrderedDict.fromkeys(vertices))
			'''
		
		# Set & display vertex color
		fnMesh.setVertexColors(colorAll[i], vtxAll[i], rep=om.MFnMesh.kRGBA)
		fnMesh.displayColors = True

		# Progress bar
		cmds.progressBar(gMainProgressBar, e=True, s=1)

	# Progress bar
	cmds.progressBar(gMainProgressBar, e=True, ep=True)

# Main function
def GN_PerformImport(filetype=1):
	# Initialize variables depending of filetype
	mode = cmds.optionVar(q="GNIE_mode")
	selectObject = cmds.optionVar(q="GNI_selectObject")
	mergeUvs = cmds.optionVar(q="GNI_mergeUvs")
	smoothingGroups = cmds.optionVar(q="GNI_smoothingGroups")
	polyClean = cmds.optionVar(q="GNI_polyClean")
	vertexColor = cmds.optionVar(q="GNIE_vertexColor")

	if filetype == 1:
		fileFormat = "mayaAscii"
		extension = ".ma"
		polyClean = 0
		vertexColor = 0

	elif filetype == 2:
		fileFormat = "OBJ"
		extension = ".obj"
		smoothingGroups = 0

		# Load plugin if needed
		if not cmds.pluginInfo("objExport", q=True, l=True):
			cmds.loadPlugin("objExport")

	elif filetype == 3:
		fileFormat = "FBX"
		extension = ".fbx"
		mergeUvs = 0
		smoothingGroups = 0
		polyClean = 0
		vertexColor = 0

		# Store dialog style & change for Maya default
		dialogStyle = cmds.optionVar(q="FileDialogStyle")
		cmds.optionVar(iv=("FileDialogStyle", 2))
		
		# Load plugin if needed
		if not cmds.pluginInfo("fbxmaya", q=True, l=True):
			cmds.loadPlugin("fbxmaya")

		# Edit Settings
		cmds.FBXImportAxisConversionEnable("-v", True)
		cmds.FBXImportCacheFile("-v", False)
		cmds.FBXImportCameras("-v", False)
		cmds.FBXImportConstraints("-v", False)
		cmds.FBXImportConvertDeformingNullsToJoint("-v", False)
		cmds.FBXImportConvertUnitString("cm")
		cmds.FBXImportFillTimeline("-v", False)
		cmds.FBXImportForcedFileAxis("-v", "disabled")
		cmds.FBXImportGenerateLog("-v", True)
		cmds.FBXImportHardEdges("-v", False)
		cmds.FBXImportLights("-v", False)
		cmds.FBXImportMergeBackNullPivots("-v", True)
		cmds.FBXImportMergeAnimationLayers("-v", True)
		cmds.FBXImportMode("-v", "add")
		cmds.FBXImportProtectDrivenKeys("-v", False)
		cmds.FBXImportQuaternion("-v", "resample")
		cmds.FBXImportResamplingRateSource("-v", "Scene")
		cmds.FBXImportScaleFactor(1)
		cmds.FBXImportSetMayaFrameRate("-v", False)
		cmds.FBXImportSetLockedAttribute("-v", False)
		cmds.FBXImportShapes("-v", True)
		#cmds.FBXImportSkeletonType("-v", "none")
		cmds.FBXImportSkins("-v", True)
		cmds.FBXImportUnlockNormals("-v", True)
		cmds.FBXImportUpAxis("y")
		
		'''
		gGameFbxExporterCurrentNode = mel.eval("$gGameFbxExporterCurrentNode = $gGameFbxExporterCurrentNode")
		cmds.FBXProperty("Export|AdvOptGrp|UI|ShowWarningsManager", "-v", cmds.getAttr(gGameFbxExporterCurrentNode + ".showWarningManager"))
		cmds.setAttr((gGameFbxExporterCurrentNode + ".showWarningManager") cmds.FBXProperty("Export|AdvOptGrp|UI|ShowWarningsManager", q=True))
		'''
	
	# Check that directory exist
	if not os.path.isdir("C:/temp/"):
		GN_Print.GN_Print("No file to import.")
		return
	
	# Single-File
	files = []
	if mode == 1:
		# Check that file exist
		file = "C:/temp/exported" + extension
		if not os.path.exists(file):
			GN_Print.GN_Print("No file to import.")
			return
		
		# Get file
		files.append(file)

		# Print result
		GN_Print.GN_Print("# Result: Imported from " + file, deferred=True)
	
	# Multi-File
	else:
		# Check that directory exist
		directory = "C:/temp/exported/"
		if not os.path.isdir(directory):
			GN_Print.GN_Print("No file to import.")
			return
		
		# Get file list
		allFiles = sorted_alphanumeric(os.listdir(directory))
		for file in allFiles:
			if file.lower().endswith(extension):
				files.append(directory + file)
		
		# Print result
		fileCount = len(files)
		if fileCount == 0:
			GN_Print.GN_Print("No file to import.")
			return
		else:
			message = "# Result: Imported {0} {1} file{2} from C:/temp/exported".format(fileCount, fileFormat, "s" if fileCount > 1 else "")
			GN_Print.GN_Print(message, deferred=True)
	
	# Store undo state & disable undo
	undo = cmds.undoInfo(q=True, st=True)
	cmds.undoInfo(st=False)

	# Check namespaces
	if cmds.namespace(ex="GN_Import"):
		cmds.namespace(mnr=True, rm="GN_Import")
	
	# Import
	objList = om.MSelectionList()
	for file in files:
		if any([selectObject, mergeUvs, smoothingGroups, polyClean, vertexColor]):
			# Import objects
			if filetype == 1:
				cmds.file(file, i=True, typ="mayaAscii", iv=True, ra=True, mnc=True, ns="GN_Import", op="v=0", pr=True, itr="combine")
			elif filetype == 2:
				cmds.file(file, i=True, typ="OBJ", iv=True, ra=True, mnc=True, ns="GN_Import", op="mo=1", pr=True, itr="combine")
			elif filetype == 3:
				cmds.file(file, i=True, typ="FBX", iv=True, ra=True, mnc=True, ns="GN_Import", pr=True, itr="combine")
				#cmds.FBXImport("-f", file, "-t", 0)
				# Delete warning window
				if cmds.window("FbxWarningWindow", ex=True):
					cmds.deleteUI("FbxWarningWindow", wnd=True)
			
			# Add to objects list
			objects = cmds.ls("GN_Import:*", l=True, typ="transform")
			meshes = GN_GetSelection.GN_GetSelection(objects, type="mesh", highlight=False)[2]
			for obj in objects:
				objList.add(obj)
			
			# Merges UVs
			if mergeUvs:	
				for obj in meshes:
					if cmds.polyEvaluate(obj, us=True) > 0:
						cmds.polyMergeUV(obj, ch=False, d=0.0001)
						cmds.select(cl=True)
			
			# Create smoothing groups
			if smoothingGroups:
				for obj in meshes:
					edges = []
					creases = cmds.polyCrease((obj + ".e[*]"), q=True, v=True)
					
					for i in range(len(creases)):
						if creases[i] > 0:
							edges.append(obj + ".e[" + str(i) + "]")
					
					if len(edges) > 0:
						cmds.polySoftEdge(obj, ch=False, a=180)
						cmds.polySoftEdge(edges, ch=False, a=0)
					else:
						cmds.polySoftEdge(obj, ch=False, a=60)
					
					cmds.select(cl=True)
			
			# Remove invalid components
			if polyClean:
				for obj in meshes:
					cmds.polyClean(obj, ch=False)
			
			# Import vertex color
			if vertexColor:
				GN_importVertexColor(meshes, file)
			
			# Remove namespace
			cmds.namespace(mnr=True, rm="GN_Import")
				
		else:
			if filetype == 1:
				cmds.file(file, i=True, typ="mayaAscii", iv=True, ra=True, mnc=True, ns=":", op="v=0", pr=True, itr="combine")
			if filetype == 2:
				cmds.file(file, i=True, typ="OBJ", iv=True, ra=True, mnc=True, ns=":", op="mo=1", pr=True, itr="combine")
			if filetype == 3:
				cmds.file(file, i=True, typ="FBX", iv=True, ra=True, mnc=True, ns=":", pr=True, itr="combine")
				#cmds.FBXImport("-f", file, "-t", 0)
				# Delete warning window
				if cmds.window("FbxWarningWindow", ex=True):
					cmds.deleteUI("FbxWarningWindow", wnd=True)
	
	# Select objects
	if selectObject:
		objects = cmds.ls(objList.getSelectionStrings(), l=True)
		cmds.selectMode(co=True), cmds.selectMode(o=True)
		cmds.select(objects, r=True)

	# Restore dialog style original state
	if filetype == 3:
		cmds.optionVar(iv=("FileDialogStyle", dialogStyle))

	# Restore undo original state
	cmds.undoInfo(st=undo)

# Create window
class GN_Import(object):
	def __init__(self, optionBox=False, *args, **kwargs):
		# Create default variables
		self.pfx = "GNI_"
		self.windowName = self.pfx + "window"
		self.windowSizeMenuItem = self.pfx + "saveWindowSize_menuItem"
		
		self.windowTitle = "GN Import"
		self.runLabel = "Import"
		self.windowSize = [546, 350]
		
		# Create option variables
		self.saveWindowSize = self.pfx + "saveWindowSize"
		self.mode = self.pfx + "mode"
		self.filetype = self.pfx + "filetype"
		self.selectObject = self.pfx + "selectObject"
		self.mergeUvs = self.pfx + "mergeUvs"
		self.smoothingGroups = self.pfx + "smoothingGroups"
		self.polyClean = self.pfx + "polyClean"
		self.vertexColor = self.pfx + "vertexColor"
		
		# Create window or run command
		if optionBox:
			self.createWindow()
		elif optionBox is not None:
			self.runCmd(closeWindow=False, **kwargs)
		
	# Help command
	def helpCmd(self, *args):
		open_new_tab("https://gabrielnadeau.com/pages/gn-zbrushmaya-importexport-tool")
	
	# Run command
	def runCmd(self, closeWindow=False, **kwargs):
		# Get option variables
		self.defaultSettings(reset=False)

		if "filetype" in kwargs:
			filetype = kwargs["filetype"]
		else:
			filetype = cmds.optionVar(q="GNIE_filetype")
		
		# Import
		GN_PerformImport(filetype)

		# Close window if specified
		if closeWindow:
			self.closeWindow()
	
	def sync(self):
		if cmds.window("GNE_window", ex=True):
			from ..GN_scripts import GN_Export
			GN_Export.GN_Export(optionBox=None).windowSetup()
	
	# Close window
	def closeWindow(self):
		if cmds.window(self.windowName, ex=True):
			cmds.evalDeferred('import maya.cmds as cmds; cmds.deleteUI("'+self.windowName+'", wnd=True)')

	# Window size
	def resizeWindow(self):
		if cmds.optionVar(q=self.saveWindowSize) == 0:
			cmds.window(self.windowName, e=True, wh=self.windowSize)

	# Default settings
	def defaultSettings(self, reset=False):
		if cmds.optionVar(ex=self.saveWindowSize) == 0:
			cmds.optionVar(iv=(self.saveWindowSize, 1))
		if reset or cmds.optionVar(ex="GNIE_mode") == 0:
			cmds.optionVar(iv=("GNIE_mode", 1))
		if reset or cmds.optionVar(ex="GNIE_filetype") == 0:
			cmds.optionVar(iv=("GNIE_filetype", 1))
		if reset or cmds.optionVar(ex=self.selectObject) == 0:
			cmds.optionVar(iv=(self.selectObject, 1))
		if reset or cmds.optionVar(ex=self.mergeUvs) == 0:
			cmds.optionVar(iv=(self.mergeUvs, 1))
		if reset or cmds.optionVar(ex=self.smoothingGroups) == 0:
			cmds.optionVar(fv=(self.smoothingGroups, 1))
		if reset or cmds.optionVar(ex=self.polyClean) == 0:
			cmds.optionVar(iv=(self.polyClean, 1))
		if reset or cmds.optionVar(ex="GNIE_vertexColor") == 0:
			cmds.optionVar(iv=("GNIE_vertexColor", 0))
		
	# Reset settings
	def resetSettings(self, sync=False, *args):
		self.defaultSettings(reset=True)
		self.windowSetup()
		if sync:
			self.sync()

	# Save settings
	def saveSettings(self, sync=False, *args):
		cmds.optionVar(iv=(self.saveWindowSize, cmds.menuItem(self.windowSizeMenuItem, q=True, cb=True)))
		cmds.optionVar(iv=("GNIE_mode", cmds.radioButtonGrp(self.mode, q=True, sl=True)))
		filetype = cmds.optionMenu(self.filetype, q=True, sl=True)
		cmds.optionVar(iv=("GNIE_filetype", filetype))
		cmds.optionVar(iv=(self.selectObject, cmds.checkBoxGrp(self.selectObject, q=True, v1=True)))
		cmds.optionVar(iv=(self.mergeUvs, cmds.checkBoxGrp(self.mergeUvs, q=True, v1=True)))
		cmds.optionVar(iv=(self.smoothingGroups, cmds.checkBoxGrp(self.smoothingGroups, q=True, v1=True)))
		cmds.optionVar(iv=(self.polyClean, cmds.checkBoxGrp(self.polyClean, q=True, v1=True)))
		cmds.optionVar(iv=("GNIE_vertexColor", cmds.checkBoxGrp(self.vertexColor, q=True, v1=True)))
		
		if filetype == 1:
			cmds.checkBoxGrp(self.mergeUvs, e=True, vis=True)
			cmds.checkBoxGrp(self.smoothingGroups, e=True, vis=True)
			cmds.checkBoxGrp(self.polyClean, e=True, vis=False)
			cmds.checkBoxGrp(self.vertexColor, e=True, vis=False)
		elif filetype == 2:
			cmds.checkBoxGrp(self.mergeUvs, e=True, vis=True)
			cmds.checkBoxGrp(self.smoothingGroups, e=True, vis=False)
			cmds.checkBoxGrp(self.polyClean, e=True, vis=True)
			cmds.checkBoxGrp(self.vertexColor, e=True, vis=True)
		elif filetype == 3:
			cmds.checkBoxGrp(self.mergeUvs, e=True, vis=False)
			cmds.checkBoxGrp(self.smoothingGroups, e=True, vis=False)
			cmds.checkBoxGrp(self.polyClean, e=True, vis=False)
			cmds.checkBoxGrp(self.vertexColor, e=True, vis=False)
		
		if sync:
			self.sync()
		
	# Setup window
	def windowSetup(self):
		cmds.menuItem(self.windowSizeMenuItem, e=True, cb=cmds.optionVar(q=self.saveWindowSize))
		cmds.radioButtonGrp(self.mode, e=True, sl=cmds.optionVar(q="GNIE_mode"))
		cmds.optionMenu(self.filetype, e=True, sl=cmds.optionVar(q="GNIE_filetype"))
		cmds.checkBoxGrp(self.selectObject, e=True, v1=cmds.optionVar(q=self.selectObject))
		cmds.checkBoxGrp(self.mergeUvs, e=True, v1=cmds.optionVar(q=self.mergeUvs))
		cmds.checkBoxGrp(self.smoothingGroups, e=True, v1=cmds.optionVar(q=self.smoothingGroups))
		cmds.checkBoxGrp(self.polyClean, e=True, v1=cmds.optionVar(q=self.polyClean))
		cmds.checkBoxGrp(self.vertexColor, e=True, v1=cmds.optionVar(q="GNIE_vertexColor"))
		self.saveSettings()
	
	def initializeWindow(self):
		cmds.showWindow(self.windowName)
		self.resizeWindow()
		cmds.setFocus(self.windowName)
	
	# Create window
	def createWindow(self):
		# If window already opened, set focus on it
		if cmds.window(self.windowName, ex=True):
			self.initializeWindow()
			return
		
		# Window
		cmds.window(self.windowName, t=self.windowTitle, mb=True, wh=self.windowSize)
		
		# Edit Menu
		cmds.menu(l="Edit")
		cmds.menuItem(l="Save Settings", c=partial(self.saveSettings), ecr=False)
		cmds.menuItem(l="Reset Settings", c=partial(self.resetSettings, True), ecr=False)
		cmds.menuItem(d=True)
		cmds.menuItem(self.windowSizeMenuItem, l="Save Window Size", c=partial(self.saveSettings), cb=False, ecr=False)
		cmds.setParent("..")	
		# Help Menu
		cmds.menu(l="Help", helpMenu=True)
		cmds.menuItem(l="Help on "+self.windowTitle, i="help.png", c=partial(self.helpCmd), ecr=False)
		cmds.setParent("..")
		
		# Window Form (START)
		cmds.formLayout(self.pfx+"window_formLayout")
		# Tab Layout (START)
		cmds.tabLayout(self.pfx+"window_tabLayout", tv=False)
		cmds.formLayout(self.pfx+"scroll_formLayout")
		# Scroll Layout (START)
		cmds.scrollLayout(self.pfx+"settings_scrollLayout", cr=True)
		cmds.formLayout(self.pfx+"settings_formLayout")
		
		# Settings Frame (START)
		cmds.frameLayout(self.pfx+"settings_frameLayout", cll=True, l="Settings", li=5, bgs=True, mh=4, mw=0)
		# Settings Column (START)
		cmds.columnLayout(adj=1)
		
		# Mode
		cmds.radioButtonGrp(self.mode, nrb=2, l="Mode:  ", la2=("Single-File", "Multi-File"), cc=partial(self.saveSettings, True))
		
		# File type
		cmds.rowLayout(nc=2, cw=(1, 138), cat=(1, "right", 4), ct2=("left", "left"))
		cmds.text(l="File type:")
		cmds.optionMenu(self.filetype, w=124, cc=partial(self.saveSettings, True))
		cmds.menuItem(l="Maya ASCII")
		cmds.menuItem(l="OBJ")
		cmds.menuItem(l="FBX")
		cmds.setParent("..")
		
		# Separation
		cmds.rowLayout(h=3)
		cmds.setParent("..")
		cmds.rowLayout(h=2, bgc=[0.266, 0.266, 0.266])
		cmds.setParent("..")
		cmds.rowLayout(h=3)
		cmds.setParent("..")
		
		# Options
		cmds.checkBoxGrp(self.selectObject, l1="Select Object", cat=(1, "left", 143), cc=partial(self.saveSettings))
		cmds.checkBoxGrp(self.mergeUvs, l1="Merge UVs", cat=(1, "left", 143), cc=partial(self.saveSettings))
		cmds.checkBoxGrp(self.smoothingGroups, l1="Soften/Harden Edges from Creases", cat=(1, "left", 143), cc=partial(self.saveSettings))
		cmds.checkBoxGrp(self.polyClean, l1="Remove Invalid Components", cat=(1, "left", 143), cc=partial(self.saveSettings))
		cmds.checkBoxGrp(self.vertexColor, l1="Vertex Color", cat=(1, "left", 143), cc=partial(self.saveSettings, True))
		
		# Settings Column (END)
		cmds.setParent("..")
		# Settings Frame (END)
		cmds.setParent("..")
		# Scroll Layout (END)
		cmds.setParent("..")
		cmds.setParent("..")
		# Tab Layout (END)
		cmds.setParent("..")
		cmds.setParent("..")
		
		# Buttons
		cmds.formLayout(self.pfx+"buttons_formLayout", nd=150)
		cmds.iconTextButton(self.pfx+"applyAndClose_button", st="textOnly", l=self.runLabel, c=partial(self.runCmd, closeWindow=True), fla=False, h=26, rpt=True)
		cmds.iconTextButton(self.pfx+"apply_button", st="textOnly", l="Apply", c=partial(self.runCmd, closeWindow=False), fla=False, h=26, rpt=True)
		cmds.iconTextButton(self.pfx+"close_button", st="textOnly", l="Close", c=partial(self.closeWindow), fla=False, h=26, rpt=True)
		cmds.setParent("..")
		
		# Window Form (END)
		cmds.setParent("..")
		
		# Window Form Layout
		cmds.formLayout(self.pfx+"window_formLayout", e=True,
			af=[(self.pfx+"window_tabLayout", "top", 0), (self.pfx+"window_tabLayout", "left", 0), (self.pfx+"window_tabLayout", "right", 0), (self.pfx+"window_tabLayout", "bottom", 36)])
		
		cmds.formLayout(self.pfx+"window_formLayout", e=True,
			ac=(self.pfx+"buttons_formLayout", "top", 5, self.pfx+"window_tabLayout"),
			af=[(self.pfx+"buttons_formLayout", "left", 5), (self.pfx+"buttons_formLayout", "right", 5)],
			an=(self.pfx+"buttons_formLayout", "bottom"))
		
		# Scroll Form Layout
		cmds.formLayout(self.pfx+"scroll_formLayout", e=True,
			af=[(self.pfx+"settings_scrollLayout", "top", 2), (self.pfx+"settings_scrollLayout", "left", 2), (self.pfx+"settings_scrollLayout", "right", 2), (self.pfx+"settings_scrollLayout", "bottom", 2)])
		
		# Settings Form Layout
		cmds.formLayout(self.pfx+"settings_formLayout", e=True,
			af=[(self.pfx+"settings_frameLayout", "top", 0), (self.pfx+"settings_frameLayout", "left", 0), (self.pfx+"settings_frameLayout", "right", 0)],
			an=(self.pfx+"settings_frameLayout", "bottom"))
		
		# Buttons Form Layout
		cmds.formLayout(self.pfx+"buttons_formLayout", e=True,
			af=[(self.pfx+"applyAndClose_button", "top", 0), (self.pfx+"applyAndClose_button", "left", 0)],
			ap=(self.pfx+"applyAndClose_button", "right", 2, 50),
			an=(self.pfx+"applyAndClose_button", "bottom"))
		
		cmds.formLayout(self.pfx+"buttons_formLayout", e=True,
			af=(self.pfx+"apply_button", "top", 0),
			ap=[(self.pfx+"apply_button", "left", 2, 50), (self.pfx+"apply_button", "right", 2, 100)],
			an=(self.pfx+"apply_button", "bottom"))
			
		cmds.formLayout(self.pfx+"buttons_formLayout", e=True,
			af=[(self.pfx+"close_button", "top", 0), (self.pfx+"close_button", "right", 0)],
			ap=(self.pfx+"close_button", "left", 2, 100),
			an=(self.pfx+"close_button", "bottom"))
		
		# Window Setup
		self.defaultSettings(reset=False)
		self.windowSetup()
		self.initializeWindow()