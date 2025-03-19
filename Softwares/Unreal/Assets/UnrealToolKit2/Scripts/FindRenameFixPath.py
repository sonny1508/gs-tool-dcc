import unreal
import os


def FindRenameFixPathFn():
    #get unreal selected assets
    assets = unreal.EditorUtilityLibrary.get_selected_assets()

    for asset in assets:
        if asset.get_class().get_name() == 'Texture2D' or asset.get_class().get_name() == 'StaticMesh':

            #get uasset source path
            assetPath = asset.get_editor_property("asset_import_data").get_first_filename()

            if(os.path.exists(assetPath)):

                #get soure file name
                assetFileName = os.path.basename(assetPath)

                #get uasset editor name
                assetUeName = asset.get_name()

                 #get uasset editor path
                assetUePath = asset.get_path_name()

                assetUeBasePath = assetUePath.split(assetUeName)[0]

                # get file directory path
                dir_path = os.path.dirname(assetPath)

                # get datasource path
                datasource_dir_path = dir_path.split("content")[0]

                new_dir_paht = datasource_dir_path + assetUeBasePath.replace("/Game","content")

                # get file original extension
                file_extension = os.path.splitext(assetFileName)[1]

                # create a new path with assetUeName and original extension
                new_path = os.path.join(new_dir_paht, assetUeName + file_extension)

                if (new_path != assetPath):

                    #remove ReadOnly Flag
                    os.chmod(assetPath, 0o777)

                    os.makedirs(new_path.rsplit("/",1)[0], exist_ok=True)

                    # Rename File
                    os.rename(assetPath, new_path)

                    print("File successfully reanamed.\nOld Path:\t" + assetPath + "\nNew Path:\t" + new_path)

                    #modify ue asset source path
                    import_data = asset.get_editor_property("asset_import_data")
                    asset = import_data.scripted_add_filename(new_path,0,'')

                else:
                    print("Warning: Path sorgente e destinazione coincidenti.")

            else:
                print("Error: Missing file: " + assetPath)