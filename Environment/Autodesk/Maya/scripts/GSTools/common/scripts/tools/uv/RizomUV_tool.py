import maya.cmds as cmds
import maya.mel as mel
import subprocess, tempfile, os
import maya.OpenMaya as om
import pymel.core as pm
import sys
import math


#def getRizomPath():
    
    #filePath = pm.fileDialog2(fm=3, okc='Select',dir = "C:/Program Files" , cap='Select Rizom Folder')
    #pm.optionVar['pbfilePath'] = filePath
    
    #if filePath == None:
			#return
    #pm.textFieldButtonGrp("path_rizom", edit=True, text=filePath[0])
  
    
def getRizomPath(*args):
    
    default = cmds.optionVar(q='saved_value') or "default path"
    if pm.window("w", exists=True):
        pm.deleteUI("w", window=True)
        
    w = cmds.window("w",t="Rizom Path",w=200, h=10,rtf=True, s=True, ip=True )
    col = cmds.columnLayout()
    rizompathrun = cmds.textField( text = default, w=200)
    
    def save_and_close(*_):
        cmds.optionVar(sv = ('saved_value', cmds.textField(rizompathrun, q=True,  text=True)))
        cmds.deleteUI(w)
        
    btn = cmds.button('save and close', c= save_and_close)
    cmds.showWindow(w)

###########################################################################
#  Change the RizomUV path to your location                               #
###########################################################################
rizomPath = r'C:\Program Files\Rizom Lab\RizomUV 2022.1\rizomuv.exe'
################## DONT TOUCH ANYTHING BELOW THIS LINE ####################

AccuName = ['Low', 'Normal', 'High', 'Higher', 'Ultra']
MapRes = ['128', '256', '512', '1024', '2048', '4096', '8192']
UvName = ['map1', 'map2', 'map3', 'map4']
ScaleMode = ['Keep Texel', 'Average Texel']
RotateMode = ['Rotate Off', 'Horizontal', 'Vertical', 'X-axis', 'Y-axis', 'Z-axis']
OverlapMode = ['Keep Overlapping UV', 'Non-overlapping UV']

def sendToRizom(*args):
  sel = cmds.ls( selection=True )
  exportFile = tempfile.gettempdir() + os.sep + "ODRizomExport.fbx"
  
  if not cmds.pluginInfo("fbxmaya", loaded=True, query=True):
    cmds.loadPlugin("fbxmaya")
    
  cmds.file(exportFile, f=True, pr=True, typ="FBX export", es=True)
  cmd = '"' + rizomPath + '" "' + exportFile + '"'
  subprocess.Popen(cmd)
  
def getFromRizom(*args):
  namespace = ':RIZOMUV'
  if not cmds.namespace(ex=namespace):
    cmds.namespace(add=namespace)
  cmds.namespace(set=namespace)
  
  mel.eval('string $X = (`internalVar -userTmpDir`) + "/ODRizomExport.fbx" ;')
  mel.eval('FBXImportMode -v add;')
  mel.eval('FBXImport -file $X;')
  
  imported_objects = cmds.ls('RIZOMUV:*', long=True, type="mesh")
  #cmds.select(imported_objects)
  original_matches = []
  for riz_obj in imported_objects:
    print ("Imported object name", riz_obj)
    original = riz_obj.replace('RIZOMUV:', '')
    original_matches.append(original)
    
    cmds.polyTransfer(original, ao=riz_obj, ch=False, uv=True)
  
  cmds.select(original_matches)
  cmds.bakePartialHistory()
  cmds.delete(':RIZOMUV:*')
  cmds.namespace(rm=':RIZOMUV')
  
def rizomAutoPack(*args):

  sel = cmds.ls( selection=True)
  accu = cmds.optionMenuGrp('accu', q=True, v=True)
  if accu == 'Low':
    packRes = '128'
  if accu == 'Normal':
    packRes = '256'
  if accu == 'High':
    packRes = '512'
  if accu == 'Higher':
    packRes = '1024'
  if accu == 'Ultra':
    packRes = '2048'
    
  mapR = cmds.optionMenuGrp('map', q=True, v=True)
  if mapR == '128':
    texRes = '128'
  if mapR == '256':
    texRes = '256'
  if mapR == '512':
    texRes = '512'
  if mapR == '1024':
    texRes = '1024'
  if mapR == '2048':
    texRes = '2048'
  if mapR == '4096':
    texRes = '4096'
  if mapR == '8192':
    texRes = '8192'
    
  Uvset = cmds.optionMenuGrp('uvset', q=True, v=True)
  uvcount = cmds.polyUVSet(q=True, auv = True)
  if Uvset == 'map1':
    for uvc in uvcount:
        if uvc == 'UVChannel_1':
            uv = '"UVChannel_1"'
        else:
            if uvc == 'map1':
                uv = '"map1"'
  if Uvset == 'map2':
    for uvc in uvcount:
        if uvc == 'UVChannel_2':
            uv = '"UVChannel_2"'
        else:
            if uvc == 'map2':
                uv = '"map2"'
  if Uvset == 'map3':
    for uvc in uvcount:
        if uvc == 'UVChannel_3':
            uv = '"UVChannel_3"'
        else:
            if uvc == 'map3':
                uv = '"map3"'
  if Uvset == 'map4':
    for uvc in uvcount:
        if uvc == 'UVChannel_4':
            uv = '"UVChannel_4"'
        else:
            if uvc == 'map4':
                uv = '"map4"'
    
  RScale = cmds.optionMenuGrp('scale', q=True, v=True)
  if RScale == 'Keep Texel':
    scale = '0'
  if RScale == 'Average Texel':
    scale = '2'
    
  RRotate = cmds.optionMenuGrp('rotate', q=True, v=True)
  if RRotate == 'Rotate Off':
    rotate = '0'
  if RRotate == 'Horizontal':
    rotate = '1'
  if RRotate == 'Vertical':
    rotate = '2'
  if RRotate == 'X-axis':
    rotate = '3'
  if RRotate == 'Y-axis':
    rotate = '4'
  if RRotate == 'Z-axis':
    rotate = '5'
    
  ROverlap = cmds.optionMenuGrp('overlap', q=True, v=True)
  if ROverlap == 'Keep Overlapping UV':
    overlap = 'true'
    groupmode = '"DefineGroupsByOverlapness"'
  if ROverlap == 'Non-overlapping UV':
    overlap = 'false'
    groupmode = '"TransferToParent"'
    
  if pm.checkBox("moveflip", q=True, v=True):
    Rmoveflip = 'ZomSelect({PrimType="Island", WorkingSet="Visible&UnLocked", IslandGroupMode="Group", Select=true, InvertedNormals=true})\
                ZomDeform({WorkingSet="Visible&Selected", PrimType="Island", Transform={ 1, 0, 1, 0, 1, 0, 0, 0, 1}})'
  else:
    Rmoveflip = ''
    
  exportFile = tempfile.gettempdir() + os.sep + "ODRizomExport.fbx"
  if not cmds.pluginInfo("fbxmaya", loaded=True, query=True):
    cmds.loadPlugin("fbxmaya")
    
  cmds.file(exportFile, f=True, pr=True, typ="FBX export", es=True)


  luascript = """ZomLoad({File={Path="odfilepath", ImportGroups=true, XYZUVW=true, UVWProps=true}, NormalizeUVW=true})
--U3dSymmetrySet({Point={0, 0, 0}, Normal={1, 0, 0}, Threshold=0.01, Enabled=true, UPos=0.5, LocalMode=false})
ZomSet({Path="Vars.EditMode.BoundingBoxMode", Value=1})
ZomSet({Path="Vars.EditMode.CenterMode", Value=3})
ZomUvset({Mode="SetCurrent", Name=""" + uv + """})
ZomIslandGroups({Mode=""" + groupmode + """, WorkingSet="Visible&UnLocked", GroupPath="RootGroup", AutoDelete=true, Properties={Pack={Stacked=""" + overlap + """}}})
ZomIslandGroups({Mode="SetGroupsProperties", WorkingSet="Visible", GroupPaths={ "RootGroup" }, Properties={Pack={Scaling={Mode=""" + scale + """}}}})
ZomIslandGroups({Mode="SetGroupsProperties", WorkingSet="Visible", GroupPaths={ "RootGroup" }, Properties={Pack={Rotate={Mode=""" + rotate + """}}}})
ZomSelect({PrimType="IslandGroup", WorkingSet="Visible", IslandGroupMode="Group", Select=true, All=true})
ZomIslandGroups({Mode="SetGroupsProperties", WorkingSet="Visible", GroupPath="RootGroup", Properties={Pack={MapResolution="""+ texRes +"""}}})
ZomIslandGroups({Mode="SetGroupsProperties", WorkingSet="Visible", GroupPaths={ "RootGroup" }, Properties={Pack={MarginSize=0.00390625}}})
ZomIslandGroups({Mode="SetGroupsProperties", WorkingSet="Visible", GroupPaths={ "RootGroup" }, Properties={Pack={PaddingSize=0.00390625}}})
ZomIslandGroups({Mode="SetGroupsProperties", WorkingSet="Visible", GroupPaths={ "RootGroup" }, Properties={Pack={Resolution=""" + packRes + """}}})
ZomPack({RootGroup="RootGroup", WorkingSet="Visible", ProcessTileSelection=false, RecursionDepth=1, Translate=true, AuxGroup="RootGroup", LayoutScalingMode=0})
""" + Rmoveflip + """
ZomSave({File={Path="odfilepath", UVWProps=true}, __UpdateUIObjFileName=true})
ZomQuit()
"""

  f = open(tempfile.gettempdir() + os.sep + "riz.lua", "w")
  f.write(luascript.replace("odfilepath", exportFile.replace("\\", "/")))
  f.close()

  cmd = '"' + rizomPath + '" -cfi "' + tempfile.gettempdir() + os.sep + "riz.lua" + '"'
  subprocess.call(cmd, shell=False)
  
  namespace = ':RIZOMUV'
  if not cmds.namespace(ex=namespace):
    cmds.namespace(add=namespace)
  cmds.namespace(set=namespace)
  
  mel.eval('string $X = (`internalVar -userTmpDir`) + "/ODRizomExport.fbx" ;')
  mel.eval('FBXImportMode -v add;')
  mel.eval('FBXImport -file $X;')

  imported_objects = cmds.ls('RIZOMUV:*', long=True, type="mesh")
  #cmds.select(imported_objects)
  original_matches = []
  for riz_obj in imported_objects:
    print ("Imported object name", riz_obj)
    original = riz_obj.replace('RIZOMUV:', '')
    original_matches.append(original)
    
    cmds.polyTransfer(original, ao=riz_obj, ch=False, uv=True)
  
  cmds.select(original_matches)
  cmds.bakePartialHistory()
  cmds.delete(':RIZOMUV:*')
  cmds.namespace(rm=':RIZOMUV')
  
  cmds.select(sel)

             
def UI():
    if cmds.window("Rizomwin", exists=True):
        cmds.deleteUI("Rizomwin", window=True)
    
    cmds.window("Rizomwin",t="RizomUV Tool",rtf=True, s=True, ip=True )    
    
    width = 8
    height = 20
    
    
    
    mainLayout = pm.columnLayout(adj=True)
    
    #pm.textFieldButtonGrp("path_rizom", cw3=[65,185,10], l="Rizom path: ", text="", buttonLabel='...', bc=getRizomPath, p=mainLayout)
    #pm.button(l="Edit/Change Rizom Path", h=height+10, c=getRizomPath, p=mainLayout)
    pm.frameLayout(label="Auto Packing",width= 350, p=mainLayout)
    #pm.rowLayout(numberOfColumns=2)
    pm.optionMenuGrp('accu',l="Pack Algorithm Accuracy")
    for a in AccuName:
        pm.menuItem(l=a)   
    pm.optionMenuGrp('map',l="Map Resolution")
    for m in MapRes:
        pm.menuItem(l=m)
        
    pm.optionMenuGrp('uvset',l="UVChannel")
    for u in UvName:
        pm.menuItem(l=u)
        
    pm.optionMenuGrp('overlap',l="Overlapping Mode")
    for o in OverlapMode:
        pm.menuItem(l=o)
        
    pm.optionMenuGrp('scale',l="Initial Scale")
    for s in ScaleMode:
        pm.menuItem(l=s)
        
    pm.optionMenuGrp('rotate',l="Initial Rotate")
    for r in RotateMode:
        pm.menuItem(l=r)
    
    
    pm.text(l="")  
    pm.checkBox("moveflip", l="Move Flipped UV Outside After Packing", p=mainLayout)
        
    pm.button(l="Pack Selected Mesh", h=height+10, c=rizomAutoPack, p=mainLayout)
    
    pm.separator(height=20, style="in", p=mainLayout)
    pm.frameLayout(label="RizomUV",width= 350, p=mainLayout)
    pm.button(l="Send To Rizom", h=height+10, c=sendToRizom, p=mainLayout)
    pm.button(l="Get From Rizom", h=height+10, c=getFromRizom, p=mainLayout)
    
    pm.separator(height=20, style="in", p=mainLayout)
    #pm.frameLayout(label="Utilities",width= 350, p=mainLayout)
    
    cmds.showWindow('Rizomwin')

#UI()
