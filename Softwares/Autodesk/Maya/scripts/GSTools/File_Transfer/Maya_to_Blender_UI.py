import maya.cmds as cmds
import maya.mel as mel
import subprocess, tempfile, os
import maya.OpenMaya as om
import sys
import math

def removeAllNamespace():
    listRef = [n.replace('RN','') for n in cmds.ls(rf = True)]
    cmds.namespace( set=':' )
    allNameSpace = [n.split(':')[len(n.split(':'))-1] for n in cmds.namespaceInfo(lon = True, fn = True, r = True) if n not in ['UI', 'shared']]
    remove = []
    if allNameSpace:
        for a in allNameSpace:
            if a not in listRef:
                cmds.namespace(rm = a , mnr = True, f = True)
                remove.append(a)

def sendToBlender(*args):
  sel = cmds.ls( selection=True )
  exportFile = tempfile.gettempdir() + os.sep + "MeshTransfer.fbx"
  
  if not cmds.pluginInfo("fbxmaya", loaded=True, query=True):
    cmds.loadPlugin("fbxmaya")
    
  cmds.file(exportFile, f=True, pr=True, typ="FBX export", es=True)

def getFromBlender(*args):
  namespace = ':BLENDER'
  if not cmds.namespace(ex=namespace):
    cmds.namespace(add=namespace)
  cmds.namespace(set=namespace)
  
  mel.eval('string $X = (`internalVar -userTmpDir`) + "/MeshTransfer.fbx" ;')
  mel.eval('FBXImportMode -v add;')
  mel.eval('FBXImport -file $X;')
  
  removeAllNamespace() 
          
def UI():
    if cmds.window("MtBwin", exists=True):
        cmds.deleteUI("MtBwin", window=True)
    
    cmds.window("MtBwin",t="Maya Blender Transfer Tool",rtf=True, s=True, ip=True )    
    
    width = 8
    height = 20
    
    mainLayout = cmds.columnLayout(adj=True)
    
    cmds.separator(height=20, style="in", p=mainLayout)
    cmds.frameLayout(label="Maya Blender Transfer",width= 350, p=mainLayout)
    cmds.button(l="Send To Blender", h=height+10, c=sendToBlender, p=mainLayout)
    cmds.button(l="Get From Blender", h=height+10, c=getFromBlender, p=mainLayout)
    
    cmds.separator(height=20, style="in", p=mainLayout)
    #cmds.frameLayout(label="Utilities",width= 350, p=mainLayout)
    
    cmds.showWindow('MtBwin')

UI()
