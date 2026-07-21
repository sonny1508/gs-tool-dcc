import pymel.core as pm
import maya.mel as mel
import pymel.core.datatypes as dt
import maya.OpenMaya as om
import math

def getLength(edge):
    pm.polyListComponentConversion(edge, tv = True)
    p = pm.xform(edge, q = True, t = True, ws = True)
    length = math.sqrt(math.pow(p[0]-p[3],2) + math.pow(p[1]-p[4],2) + math.pow(p[2]-p[5],2))
    return float('%.3f' % length)
     
def setEdgeLength(desLeg, direction = "center"):
    selEdge = pm.ls(sl = True, fl = True)
    if direction == "left": 
        for i in range(0, len(selEdge),1):
            curLeg = getLength(selEdge[i])
            #toVert = pm.polyListComponentConversion(selEdge[i], tv = True)
            pm.select(selEdge[i])
            mel.eval("PolySelectConvert 3;")
            toVert = pm.ls(sl = True, fl = True)
            vertPos1 = pm.xform(toVert[0], q = True, ws = True, t = True)
            vertPos2 = pm.xform(toVert[1], q = True, ws = True, t = True)

            vectorV1 = dt.Vector(vertPos1)
            vectorV2 = dt.Vector(vertPos2)
            
            direction = vectorV1 - vectorV2
            des = (direction/dt.length(direction))*(desLeg-curLeg)
            pm.polyMoveVertex( toVert[0], t = des, ch = False)
            
    elif direction == "right":
        for i in range(0, len(selEdge),1):
            curLeg = getLength(selEdge[i])
            #toVert = pm.polyListComponentConversion(selEdge[i], tv = True)
            pm.select(selEdge[i])
            mel.eval("PolySelectConvert 3;")
            toVert = pm.ls(sl = True, fl = True)
            vertPos1 = pm.xform(toVert[0], q = True, ws = True, t = True)
            vertPos2 = pm.xform(toVert[1], q = True, ws = True, t = True)

            vectorV1 = dt.Vector(vertPos1)
            vectorV2 = dt.Vector(vertPos2)
            
            direction = vectorV2 - vectorV1
            des = (direction/dt.length(direction))*(desLeg-curLeg)
            pm.polyMoveVertex( toVert[1], t = des, ch = False)
            
    else:
        for i in range(0, len(selEdge),1):
            curLeg = getLength(selEdge[i])
            #toVert1 = pm.polyListComponentConversion(selEdge[i], tv = True, internal = True)
            pm.select(selEdge[i])
            mel.eval("PolySelectConvert 3;")
            toVert = pm.ls(sl = True, fl = True)
            vertPos1 = pm.xform(toVert[0], q = True, ws = True, t = True)
            vertPos2 = pm.xform(toVert[1], q = True, ws = True, t = True)

            vectorV1 = dt.Vector(vertPos1)
            vectorV2 = dt.Vector(vertPos2)
            
            direction1 = vectorV1 - vectorV2
            direction2 = vectorV2 - vectorV1 
            
            des1 = ((direction1/dt.length(direction1))*(desLeg-curLeg))/2
            des2 = ((direction2/dt.length(direction2))*(desLeg-curLeg))/2
            
            pm.polyMoveVertex( toVert[0], t = des1, ch = False)
            pm.polyMoveVertex( toVert[1], t = des2, ch = False)
    mel.eval("DeleteAllHistory;")       
    mel.eval("PolySelectConvert 2;")        
    pm.select(selEdge)
    
def selEdge():
    
    sel = pm.ls(sl = True, o = True)
    
    if len(sel) != 0:
        listToCheck = []
        results = []
        for s in sel:
            if s.type() == "mesh":
                listToCheck.append(pm.listRelatives(s, p = True)[0])
            else:
                listToCheck.append(s)
                
        value =  pm.floatField("floatField1", q = True, value = True)
        
        for obj in listToCheck:
            edgeCount = pm.polyEvaluate(obj, e = True)
            pm.select(obj + '.e[0:'+str(edgeCount)+']')
            edgeSel = pm.ls(sl = True, fl = True)
            edgeSel.remove(edgeSel[0])
            for edge in edgeSel:
                if getLength(edge) < value:
                    results.append(edge)
        pm.select(cl = True)
        for i in range(0, len(results),1):
            pm.select(results[i], add = True)
    else:
        om.MGlobal.displayError("Select obj!")
    
def lenghtToField():
    sel = pm.ls(sl = True, fl = True)
    if not sel or len(sel) > 1:
        om.MGlobal.displayError("Select one edge!")
    else:
        leg = getLength(sel[0])
        pm.floatField("floatField2", e = True, value = leg)
    
    
def setLenght():
    value = pm.floatField("floatField2", q = True, value = True)
    direction = pm.radioCollection("direction", q = True, sl = True)
    
    if direction == "left":
        setEdgeLength(value, direction = "left")
    elif direction == "center":
        setEdgeLength(value)
    else:
        setEdgeLength(value, direction = "right")

def increaseValue():
    value = pm.floatField("floatField2", q = True, value = True)
    pm.floatField("floatField2", e = True, value = value + 0.001)
    
def decreaseValue():
    value = pm.floatField("floatField2", q = True, value = True)
    pm.floatField("floatField2", e = True, value = value - 0.001)

def UnbevelFn():
        import Unbevel as Unbevel
        reload(Unbevel)

def Gui():
    winName = "setEdgeWindow"

    if pm.window( winName, q = True, ex = True):
        pm.deleteUI(winName)
        
    if pm.windowPref( winName, q = True, ex = True):
        pm.windowPref(winName, r = True)
        
    UI = pm.window(winName, t = "Edge Length Tool", widthHeight = (160, 130), mnb = False, mxb = False, rtf = True)

    layout = pm.columnLayout(adjustableColumn=True)
    
    pm.button(l = "Get Length", c = lambda *a: lenghtToField(), parent = layout)
    pm.button(l = chr(int("1e", 16)), c = lambda *a: increaseValue(), parent = layout)
    pm.floatField("floatField2", minValue=-1, maxValue=10000, precision=3, step=.001 , parent = layout)
    pm.button(l = chr(int("1f", 16)), c = lambda *a: decreaseValue() , parent = layout)
    
    rowLayout = pm.rowLayout( cw = (80,80) , height = 40, numberOfColumns=3, adjustableColumn=2, columnAlign=(1, 'right'), parent = layout)
    #pm.button(l = "Select Edge  <  ", c = lambda *a: selEdge(), parent = rowLayout)
    #pm.floatField("floatField1", minValue=-1, maxValue=10000, precision=3, step=.001 , parent = rowLayout)

   

    #rowLayout2 = pm.rowLayout( cw = (80,80), height = 40, numberOfColumns=3, adjustableColumn=2, columnAlign=(1, 'right'), parent = layout)
    

    #rowLayout2 = pm.rowLayout( numberOfColumns=3, columnAlign=(1, 'right'), columnAttach=[(1, 'both', 0), (2, 'both', 0), (3, 'both', 0)] , parent = layout)

    pm.radioCollection("direction", parent = rowLayout)
    pm.radioButton("left", label='Left' , parent = rowLayout)
    pm.radioButton("center", label='Center' , sl = True, parent = rowLayout)
    pm.radioButton("right", label='Right' , parent = rowLayout)

    pm.button(l = "Set Length", c = lambda *a: setLenght(), parent = layout)
    #pm.button(l = "Unbevel", c = lambda *a: UnbevelFn(), parent = layout)


    pm.showWindow(UI)