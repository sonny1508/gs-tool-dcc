from maya import cmds, mel
from GSValidation.qt_util import *


def history_objects(uniqueGeometryList, allShapes, progressBar=None):
    # find all history information
    historyList = []
    shadingGroupList = []

    totalObjects = len(uniqueGeometryList)
    percentage = 99.0 / totalObjects
    for index, geo in enumerate(uniqueGeometryList):
        history = cmds.listHistory(geo)
        shapeNode = cmds.listRelatives(geo, ad=True, s=True)
        for shape in shapeNode:
            if not cmds.objExists(shape + '.instObjGroups[0]'):
                continue
            shadingGroup = cmds.listConnections(shape + '.instObjGroups[0]')
            if not shadingGroup is None:
                shadingGroupList.append(shadingGroup[0])
            objGroup = cmds.listConnections(shape + '.instObjGroups[0]')
            if not objGroup == None:
                shadingGroupList.append(objGroup[0])
        for j in history:
            if not j in allShapes and not j in shadingGroupList:
                if not 'groupId' in j and not 'lambert2SG' in j:
                    if not 'initialShadingGroup' in j and not 'doneUV' in j:
                        historyList.append(geo)
        setProgress(percentage * index, progressBar, "Checking history: %s" % geo.split('|')[-1])

    setProgress(100, progressBar, "history checked")
    newhistoryList = list(set(historyList))
    return {'history': newhistoryList}


def xforms(uniqueGeometryList, progressBar=None):
     # search for xforms
    totalObjects = len(uniqueGeometryList)
    percentage = 99.0 / totalObjects
    xformsList = []
    for index, geo in enumerate(uniqueGeometryList):
        xforms = cmds.xform(geo, q=True, t=True)
        if not xforms == [0.0, 0.0, 0.0]:
            xformsList.append(geo)
        xforms = cmds.xform(geo, q=True, ro=True)
        if not xforms == [0.0, 0.0, 0.0]:
            xformsList.append(geo)
        xforms = cmds.xform(geo, q=True, r=True, s=True)
        if not xforms == [1.0, 1.0, 1.0]:
            xformsList.append(geo)
        setProgress(percentage * index, progressBar, "checking xforms: %s" % geo.split('|')[-1])
    setProgress(100, progressBar, "xforms checked")

    return {'Xforms': xformsList}


def default_and_pasted_objects(uniqueGeometryList, progressBar=None):
    namedList = []
    totalObjects = len(uniqueGeometryList)
    percentage = 99.0 / totalObjects
    for index, geo in enumerate(uniqueGeometryList):
        geo = geo.split('|')[-1]
        if any(x in geo for x in ['pCube', 'polySurface', 'pCylinder',
                                  'pSphere', 'pCone', 'pPlane', 'pTorus',
                                  'pPyramid', 'pPipe', '__Pasted']):
            namedList.append(geo)
        setProgress(percentage * index, progressBar, "checking defaults: %s" % geo.split('|')[-1])
    setProgress(100, progressBar, "defaults checked")

    return {'Default and Pasted': namedList}


def default_shader(uniqueGeometryList, progressBar=None):
    defaultLambertGrp = []
    totalObjects = len(uniqueGeometryList)
    percentage = 99.0 / totalObjects
    for index, geo in enumerate(uniqueGeometryList):
        shaders = cmds.listConnections(cmds.listHistory(geo, f=1), type='lambert')

        if not shaders == None:
            for shader in shaders:
                if shader == 'lambert1':
                    defaultLambertGrp.append(geo)
        setProgress(percentage * index, progressBar, "checking default shader: %s" % geo.split('|')[-1])
    setProgress(100, progressBar, "default shader checked")
    return {'Default Shader': defaultLambertGrp}


def all_shaders(allCommonShaders, progressBar=None):
    # search shaders
    pastedShaders = []
    totalObjects = len(allCommonShaders)
    percentage = 99.0 / totalObjects
    for index, shader in enumerate(allCommonShaders):
        if 'pasted__' in shader:
            pastedShaders.append(shader)
        setProgress(percentage * index, progressBar, "checking pasted shaders: %s" % shader)
    setProgress(100, progressBar, "pasted shaders checked")

    return {"Pasted Shaders": pastedShaders}


def holes(progressBar=None):
    # find holes
    setProgress(0, progressBar, "checking holes")
    FacesWithHoles = mel.eval('polyCleanupArgList 3 { "1","2","0","0","0","0","1","0","0","1e-005","0","1e-005","0","1e-005","0","-1","0" };')

    setProgress(100, progressBar, "holes checked")
    return {'Holes': FacesWithHoles}


def locked_normals(uniqueGeometryList, progressBar=None):
    # check for locked normals
    lockedNormals = []
    totalObjects = len(uniqueGeometryList)
    percentage = 99.0 / totalObjects
    for index, geo in enumerate(uniqueGeometryList):
        try:
            vertices = cmds.filterExpand(cmds.polyListComponentConversion(geo, tv=True), sm=31)
            for vert in vertices:
                locked = cmds.polyNormalPerVertex(vert, q=True, al=True)[0]
                if locked:
                    lockedNormals.append(geo)
        except:
            pass

        setProgress(percentage * index, progressBar, "checking locked normals: %s" % geo.split('|')[-1])
    setProgress(100, progressBar, "locked normals checked")
    uniqueLockedList = set(lockedNormals)

    return {'Locked Normals': list(uniqueLockedList)}

def ngons(progressBar=None):
    # n-gons poly
    concave = mel.eval('polyCleanupArgList 3 { "1","2","0","0","0","1","0","0","0","1e-005","0","1e-005","0","1e-005","0","-1","0" };')
    ngons = mel.eval('polyCleanupArgList 3 { "1","2","0","0","1","0","0","0","0","1e-005","0","1e-005","0","1e-005","0","-1","0" };')
    ngonobj = []
    totalObjects = len(ngons)
    if totalObjects == 0:
        setProgress(100, progressBar, "checked n-gons")
        return {'n-gons': ngonobj}
    percentage = 99.0 / totalObjects
    
    for index, geo in enumerate(ngons):
        if ngons:
            ngonobj.append(geo)
        setProgress(percentage * index, progressBar, "checking n-gons: %s" % geo.split('|')[-1])
    setProgress(100, progressBar, "checked n-gons")
    return {'N-Gons': ngonobj}

def legal_uvs(uniqueGeometryList, progressBar=None):
    # search for uv's outside legal space
    UVList = []
    NoUvList = []
    FinalList = []
    totalObjects = len(uniqueGeometryList)
    percentage = 99.0 / totalObjects

    for index, geo in enumerate(uniqueGeometryList):
        try:
            objectUVs = cmds.filterExpand(cmds.polyListComponentConversion(geo, tuv=True), sm=35)
            for uv in objectUVs:
                uvPos = cmds.polyEditUV(uv, q=True, v=True, u=True)
                for pos in uvPos:
                    if float(pos) < 0.0 or float(pos) > 1.0:
                        UVList.append(geo)
        except:
            NoUvList.append(geo)
        
        for i in UVList:
            if i not in FinalList:
                FinalList.append(i)
        setProgress(percentage * index, progressBar, "checking 0-1 UV's: %s" % geo.split('|')[-1])
    setProgress(100, progressBar, "0-1 UV's checked")

    return {"UV outside 0-1": FinalList, "No uv's": NoUvList}


def lamina_faces(uniqueGeometryList, progressBar=None):
    # check for lamina faces
    laminaFacesList = []
    totalObjects = len(uniqueGeometryList)
    percentage = 99.0 / totalObjects
    for index, geo in enumerate(uniqueGeometryList):
        laminaFaces = cmds.polyInfo(geo, laminaFaces=True)
        if not laminaFaces == None:
            laminaFacesList += laminaFaces
        setProgress(percentage * index, progressBar, "checking lamina: %s" % geo.split('|')[-1])
    setProgress(100, progressBar, "lamina checked")

    return {"Lamina Faces": laminaFacesList}


def zero_edge_length(progressBar=None):
    # zero edge lenght

    setProgress(0, progressBar, "checking zero edge")
    zeroEdgeLenght = mel.eval('polyCleanupArgList 3 { "1","2","0","0","0","0","0","0","0","1e-005","1","1e-005","0","1e-005","0","-1","0" };')

    setProgress(100, progressBar, "zero edge checked")
    return {'Zero Edge Length': zeroEdgeLenght}


def zero_geometry_area(progressBar=None):
    # zero geometry area
    setProgress(0, progressBar, "checking zero face")
    zerofaceLenght = mel.eval('polyCleanupArgList 3 { "1","2","0","0","0","0","0","0","1","1e-005","0","1e-005","0","1e-005","0","-1","0" };')

    setProgress(100, progressBar, "zero face checked")
    return {'Zero Face Length': zerofaceLenght}


"""def unmapped_faces(progressBar=None):
    # unmapped faces
    setProgress(0, progressBar, "checking unmapped")
    zeromaparea = mel.eval('polyCleanupArgList 3 { "1","2","0","0","0","0","0","0","0","0","0","0","1","0","0","-2","0","0" };')

    setProgress(100, progressBar, "unmapped checked")
    return {'Zero Map Area': zeromaparea}"""


def concave_faces(progressBar=None):
    # concave faces
    concave = mel.eval('polyCleanupArgList 3 { "1","2","0","0","0","1","0","0","0","1e-005","0","1e-005","0","1e-005","0","-1","0" };')
    ngons = mel.eval('polyCleanupArgList 3 { "1","2","0","0","1","0","0","0","0","1e-005","0","1e-005","0","1e-005","0","-1","0" };')
    concaveNotNgon = []
    totalObjects = len(concave)
    if totalObjects == 0:
        setProgress(100, progressBar, "checked concave")
        return {'Concave Faces': concaveNotNgon}
    percentage = 99.0 / totalObjects
    
    for index, geo in enumerate(concave):
        if concave:
            concaveNotNgon.append(geo)
        setProgress(percentage * index, progressBar, "checking concave: %s" % geo.split('|')[-1])
    setProgress(100, progressBar, "checked concave")
    return {'Concave Faces': concaveNotNgon}


def keyed_objects(uniqueGeometryList, progressBar=None):
    # keyed objects
    objectWithKeys = []
    totalObjects = len(uniqueGeometryList)
    percentage = 99.0 / totalObjects

    for index, geo in enumerate(uniqueGeometryList):
        translatekey = cmds.keyframe(geo, query=True, at='translate', timeChange=True)
        rotatekey = cmds.keyframe(geo, query=True, at='rotate', timeChange=True)
        scalekey = cmds.keyframe(geo, query=True, at='scale', timeChange=True)
        if not translatekey == None:
            objectWithKeys.append(geo)
        elif not rotatekey == None:
            objectWithKeys.append(geo)
        elif not scalekey == None:
            objectWithKeys.append(geo)
        setProgress(percentage * index, progressBar, "checking keys: %s" % geo.split('|')[-1])
    setProgress(100, progressBar, "checked keys")

    return {'Keyed Objects': objectWithKeys}


# section for HW check

def geo_list():
    piecesList = ["FL_RIM_LOD", "F_RIM_LOD", "FL_TYRE_LOD", "F_TYRE_LOD", "BL_RIM_LOD", "B_RIM_LOD",
                  "BL_TYRE_LOD",
                  "B_TYRE_LOD",
                  "FR_RIM_LOD",
                  "FR_TYRE_LOD",
                  "BR_TYRE_LOD",
                  "BR_RIM_LOD",
                  "BODY_LOD",
                  "CHASSIS_LOD",
                  "INTERIOR_LOD",
                  "WINDOW_LOD",
                  "WINDSHIELD_LOD",
                  "TANK_LOD",
                  "EXTERIOR_LOD",
                  "ENGINE_LOD",
                  "FENDER_LOD",
                  "SEAT_LOD",
                  "EXTRA_LOD",
                  "Handle_Bar_LOD"]
    return piecesList

def material_list():
    materialList = ["MI_F_Wheel",
                    "MI_F_Wheel",
                    "MI_F_Wheel",
                    "MI_F_Wheel",
                    "MI_B_Wheel",
                    "MI_B_Wheel",
                    "MI_B_Wheel",
                    "MI_B_Wheel",
                    "MI_F_Wheel",
                    "MI_F_Wheel",
                    "MI_B_Wheel",
                    "MI_B_Wheel",
                    "MI_Livery",
                    "MI_Chassis",
                    "MI_Interior",
                    "MI_Glass",
                    "MI_Glass",
                    "MI_Exterior",
                    "MI_Exterior",
                    "MI_Exterior",
                    "MI_Exterior",
                    "MI_Interior",
                    "MI_Extra",
                    "MI_Extra"]
    return materialList

def unknow_materials(allCommonShaders, progressBar=None):
    matCorrectNameList = ["MI_Glass", 
                          "MI_Chassis",
                          "MI_F_Wheel",  
                          "MI_Interior", 
                          "MI_B_Wheel", 
                          "MI_Livery",
                          "MI_GlassA",
                          "MI_GlassB",
                          "MI_GlassC",
                          "MI_Exterior",
                          "MI_Extra"]
    unknownMaterialsList = []
    totalObjects = len(allCommonShaders)
    percentage = 99.0 / totalObjects
    for index, shader in enumerate(allCommonShaders):
        if shader not in matCorrectNameList and "MI_Extra" not in shader and "lambert1" not in shader and "Gizmo_Mat" not in shader:
            unknownMaterialsList.append(shader)
        setProgress(percentage * index, progressBar, "checking HW shader: %s" % shader)
    setProgress(100, progressBar, "HW shader checked")
    
    return {"HW materials": unknownMaterialsList}
    
def unknow_geo(uniqueGeometryList, progressBar=None):
    piecesList = geo_list()
    unknowList = []
    totalObjects = len(uniqueGeometryList)
    percentage = 99.0 / totalObjects
    for index, geo in enumerate(uniqueGeometryList):
        geo = geo.split('|')[-1]
        if any(x in geo for x in ['_PROXY', 'Nulls_grp', 'car_lodGroup',
                                  'LOD_', 'back', 'front', 'left',
                                  'persp', 'side', 'top', 'bottom', 'Collision', 'COLLISION_SHAPE']):
            continue
        
        if geo[:-1] not in piecesList:
            unknowList.append(geo)
        setProgress(percentage * index, progressBar, "checking unknow geo: %s" % geo.split('|')[-1])
    setProgress(100, progressBar, "unknow geo checked")

    return {'HW Geometry': unknowList}
    
def assigned_material(uniqueGeometryList, progressBar=None):
    piecesList = geo_list()
    materialList = material_list()
    assignedList = []
    totalObjects = len(uniqueGeometryList)
    percentage = 99.0 / totalObjects
    for index, geo in enumerate(uniqueGeometryList):
        geo = geo.split('|')[-1]
        if geo[:-1] in piecesList:
            geoindex = piecesList.index(geo[:-1])
            shaders = cmds.listConnections(cmds.listHistory(geo, f=1), type='lambert')
            if len(shaders) == 1:
                for sh in shaders:
                    if materialList[geoindex] != sh:
                        assignedList.append(geo)
            else:
                assignedList.append(geo)
        setProgress(percentage * index, progressBar, "checking assigned materials: %s" % geo.split('|')[-1])
    setProgress(100, progressBar, "assigned materials checked")
    
    return {'HW Assigned Materials': assignedList}
    
def uv_channel_name(uniqueGeometryList, progressBar=None):
    uvChannelName = ["UVChannel_1", "UVChannel_2", "UVChannel_3", "UVChannel_4"] 
    piecesList = geo_list()
    materialList = material_list()
    geo_uv_channel = []
    UVList = []
    totalObjects = len(uniqueGeometryList)
    percentage = 99.0 / totalObjects
    for index, geo in enumerate(uniqueGeometryList):
        geo = geo.split('|')[-1]
        if geo[:-1] in piecesList:
            geoUVs = cmds.polyUVSet(geo, q=True, auv=True)
            if len(geoUVs) > 4:
                UVList.append(geo)
            if len(geoUVs) < 4:
                UVList.append(geo)
            for uv in geoUVs:
                if uv not in uvChannelName:
                    UVList.append(geo)
        for i in UVList:
            if i not in geo_uv_channel:
                geo_uv_channel.append(i)
        setProgress(percentage * index, progressBar, "checking uv channel name: %s" % geo.split('|')[-1])
    setProgress(100, progressBar, "uv channel name checked")
    
    return {'HW UVchannel': geo_uv_channel}  

def wrong_materials_type(allCommonShaders, progressBar=None):
    matCorrectNameList = ["MI_Glass", 
                          "MI_Chassis",
                          "MI_F_Wheel",  
                          "MI_Interior", 
                          "MI_B_Wheel", 
                          "MI_Livery",
                          "MI_GlassA",
                          "MI_GlassB",
                          "MI_GlassC",
                          "MI_Exterior",
                          "MI_Extra"]
    unknownMaterialsType = []
    totalObjects = len(allCommonShaders)
    percentage = 99.0 / totalObjects
    for index, shader in enumerate(allCommonShaders):
        if shader in matCorrectNameList:
            ShadersType = cmds.nodeType(shader)
            if ShadersType != "lambert":
                unknownMaterialsType.append(shader)
        setProgress(percentage * index, progressBar, "checking HW shader type: %s" % shader)
    setProgress(100, progressBar, "HW shader type checked")
    
    return {"HW materials type": unknownMaterialsType}   

def pivot_position(uniqueGeometryList, progressBar=None):
    piecesList = geo_list()
    pivotList = []
    totalObjects = len(uniqueGeometryList)
    percentage = 99.0 / totalObjects
    for index, geo in enumerate(uniqueGeometryList):
        pivotposition = cmds.xform(geo, ws=True, rp=True, q=True)
        if pivotposition != [0,0,0]:
            pivotList.append(geo)
        setProgress(percentage * index, progressBar, "checking pivot position: %s" % geo.split('|')[-1])
    setProgress(100, progressBar, "pivot position checked")

    return {'HW Pivot Position': pivotList} 

def uv1_match_uv2(uniqueGeometryList, progressBar=None):
    piecesList = geo_list()
    geo_match_uv = []
    totalObjects = len(uniqueGeometryList)
    percentage = 99.0 / totalObjects
    for index, geo in enumerate(uniqueGeometryList):
        geo = geo.split('|')[-1]
        if geo[:-1] in geo:
            cmds.select(geo)
            cmds.polyUVSet(cuv=True, uvs='UVChannel_1')
            cmds.select(cmds.polyListComponentConversion(tuv = True))
            UVValues_map1 = cmds.polyEditUV(query = True, relative=False)
            cmds.select(geo)
            cmds.polyUVSet(cuv=True, uvs='UVChannel_2')
            cmds.select(cmds.polyListComponentConversion(tuv = True))
            UVValues_map2 = cmds.polyEditUV(query = True, relative=False)
            cmds.select(geo)
            if not UVValues_map1:
                geo_match_uv.append(geo)
            else:
                if sum(UVValues_map1) != sum(UVValues_map2):
                    geo_match_uv.append(geo)
        
        setProgress(percentage * index, progressBar, "checking uv matching: %s" % geo.split('|')[-1])
        cmds.select(d=True)
    setProgress(100, progressBar, "uv matching checked")
    
    return {'HW Matching UV1-UV2': geo_match_uv} 

def uv_channel_order(uniqueGeometryList, progressBar=None):
    uvChannelName = ["UVChannel_1", "UVChannel_2", "UVChannel_3", "UVChannel_4"] 
    piecesList = geo_list()
    geo_uv_order = []
    totalObjects = len(uniqueGeometryList)
    percentage = 99.0 / totalObjects
    for index, geo in enumerate(uniqueGeometryList):
        geo = geo.split('|')[-1]
        if geo[:-1] in piecesList:
            i=0
            orderUv = []
            cmds.select(geo)
            AllUVset = cmds.polyUVSet(q=True, auv=True)
            if len(AllUVset) ==4:
                for uv in AllUVset:
                    if uvChannelName[i] != uv:
                        orderUv.append(uv)
                    i=i+1
                if len(orderUv):
                    geo_uv_order.append(geo)
        setProgress(percentage * index, progressBar, "checking uv channel order: %s" % geo.split('|')[-1])
        cmds.select(d=True)
    setProgress(100, progressBar, "uv channel order checked")
    
    return {'HW UVchannel Order': geo_uv_order}      