import json
import maya.cmds as cmds
import maya.mel as mel

def send_mesh_to_center(mesh_objs, center_directory):
    cm_indx = 0
    wr_list = [] 
    backup_parent_data = []  
    
    for mesh_tf in mesh_objs:
        #get child object before unparent
        mesh_tf_fullname = cmds.ls(mesh_tf, allPaths = True)#check for name repeat
        obj_child = cmds.listRelatives(mesh_tf_fullname, children = True, type = "transform")
        if obj_child:
            for ob_chi in obj_child:
                ob_chi_tf = cmds.ls(ob_chi, type = "transform") 
                cmds.parent(ob_chi_tf, world = True) 
        else:
            obj_child = None
        backup_parent_data.append({"mesh_tf": mesh_tf, "child": obj_child })    

        sg_list = []

        mesh_shape = cmds.listRelatives(mesh_tf_fullname, fullPath = True, shapes = True)
        # print(mesh_shape)
        sgs = cmds.listConnections(mesh_shape, type='shadingEngine')
        mat_name = cmds.ls(cmds.listConnections(sgs),materials=True)
        # print(sgs)
        for sg in mat_name:
            if sg not in sg_list:
                sg_list.append(sg)  
                # print(sg)

        wr_list.insert(cm_indx,{"mesh_name": mesh_tf,"sg_name": sg_list}) 
        cm_indx += 1
     
    with open(center_directory +"MA_MeshUpdate.json", "w") as file:
        json.dump(wr_list,file,indent=2,sort_keys=True)   

    
    start = str(cmds.playbackOptions( q=True,min=True ))
    end  = str(cmds.playbackOptions( q=True,max=True ))  
    root_flag = ""
    for msh in mesh_objs:
        msh = cmds.ls(msh, allPaths = True, type='transform')#check for name repeat 
        root_flag += " -root " + msh[0] 
        print(msh[0])    
    
    if not cmds.pluginInfo("fbxmaya", loaded=True, query=True):
        cmds.loadPlugin("fbxmaya")
    
    cmds.file(center_directory + "MA_MeshTransfer.fbx", f=True, pr=True, typ="FBX export", es=True)

    # reparent child object
    for re_parent in backup_parent_data:
        # re_tf_obj  = cmds.ls(re_parent["mesh_tf"], type = "transform")          
        if re_parent["child"]:
            for chi in re_parent["child"]:
                ob_tf_parent = cmds.ls(re_parent["mesh_tf"], type = "transform")         
                ob_tf_child  = cmds.ls(chi, type = "transform")   
                cmds.parent(ob_tf_child, ob_tf_parent )  

    
    return {'FINISHED'}