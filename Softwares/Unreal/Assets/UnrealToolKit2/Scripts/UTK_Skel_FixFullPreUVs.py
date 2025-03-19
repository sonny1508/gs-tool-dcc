import unreal 


def fixFullPrecUVs(lo_ds_configuration):
    editor_asset_lib = unreal.EditorAssetLibrary()
    
    #Genero la Progress Bar 
    with unreal.ScopedSlowTask(100, 'Working!') as slow_task:
        slow_task.make_dialog(True)
        
        selectedSkelMesh = unreal.EditorUtilityLibrary.get_selected_assets()
        asset_count = len(selectedSkelMesh)
        counter = 0 
        for skelMesh in selectedSkelMesh:

            #Creo il tasto di interruzione task nella task bar
            if slow_task.should_cancel():
                break

            #Aggiorno la progress bar
            slow_task.enter_progress_frame(1, "Skeletal Mesh number " + str(counter) + ' / ' + str(asset_count))

            #Eseguo l'op solo su skeletal mesh      
            if skelMesh.get_class().get_name() == 'SkeletalMesh':
                for lod in range(len(lo_ds_configuration)):
                    SkelMeshSetLOD = unreal.EditorSkeletalMeshLibrary.get_lod_build_settings(skelMesh,lod)
                    if(lo_ds_configuration[lod] == True):
                        SkelMeshSetLOD.use_full_precision_u_vs = True
                        unreal.EditorSkeletalMeshLibrary.set_lod_build_settings(skelMesh, lod, SkelMeshSetLOD)
                    else:
                        SkelMeshSetLOD.use_full_precision_u_vs = False
                        unreal.EditorSkeletalMeshLibrary.set_lod_build_settings(skelMesh, lod, SkelMeshSetLOD)      
            else:
                print("Make sure to select only Skeletal Meshes")

        counter += 1