import sys
import json
import maya.cmds as cmds
ScriptDir = cmds.internalVar(userScriptDir=True)
ScriptDir = ScriptDir + "bmc_maya/"
sys.path.append(ScriptDir)

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from maya import OpenMayaUI 
from shiboken2  import wrapInstance 

import ma_send_mesh as sms


from Ui_bmc_main import Ui_MainWindow
from Ui_rename_List import Ui_Rename_list_Form

class List_rn_Window(QWidget):
    def delete_namespace(self, namespace_list): 
        for ns in namespace_list:
            if cmds.namespace( exists=ns):
                cmds.namespace( removeNamespace = ":" + ns, mergeNamespaceWithRoot = True)     
        self.hide()     
        
  
    def __init__(self, namespace_list):
        QWidget.__init__(self)       

        self.ui = Ui_Rename_list_Form()
        self.ui.setupUi(self)  
        model = QStandardItemModel(self.ui.listView)
        
        for ob in namespace_list:
            item = QStandardItem(ob)
            model.appendRow(item)
        self.ui.listView.setModel(model)
        self.ui.pushButton_rename_list.clicked.connect(lambda:self.delete_namespace(namespace_list)) 
        # ==> END ##
        
class MainWindow(QMainWindow):
    def open_listWindow(self, namespace_list):
        self.ui_rn = List_rn_Window(namespace_list)  
        self.ui_rn.show()

    def __init__(self):
        window = OpenMayaUI.MQtUtil.mainWindow()
        mayaWindow = wrapInstance(int(window),QMainWindow)
        super(MainWindow, self).__init__(mayaWindow)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)      

        self.ui.pushButton_open_file_dialog.clicked.connect(self.filepath_Dialog)
        self.ui.pushButton_SEND.clicked.connect(self.BMC_send)

        #load user settting
        try:
            with open(ScriptDir + "bmc_setting.json") as json_file:
                user_data_list = json.load(json_file) 

            self.ui.label_file_path.setText(user_data_list[0]["center_path"]) 


        except:
          
            self.ui.label_file_path.setText(ScriptDir)

            user_data = []
            newuser_setting = {     "username": "Default",
                                    "center_path": ScriptDir,
                                    "Light_mult": 1,
                                    "botton_light": True,
                                    "botton_camera": True,
                                    "botton_material": True,
                                    "botton_mesh": True,
                                    "botton_select": False,
                                    "botton_invisible": False,
                                    "botton_keep_tf":False,
                                    "renderer": "VRay"
                                    }                
            user_data.append(newuser_setting)   
            with open(ScriptDir + "bmc_setting.json", "w") as file:
                json.dump(user_data, file, indent=2, sort_keys=False)

            print("bmc_setting not load")  

        self.show()
        ## ==> END ##

    def BMC_send(self):
        

        send = False
        center_dir = self.ui.label_file_path.text() + "/"

        obj_list_tf = cmds.ls( selection = True)   
        obj_list = cmds.listRelatives(obj_list_tf, shapes = True)    

        mesh_objs_shape =  cmds.ls(obj_list, type = 'mesh') #link mesh to materal


        mesh_objs = cmds.ls(obj_list, type = 'mesh')
        mesh_transformList = cmds.listRelatives(mesh_objs, parent=True)
        if mesh_transformList:       
            sms.send_mesh_to_center(mesh_transformList, center_dir)
            # print(mesh_transformList)
            print("send mesh to:" + center_dir)
            send = True

        if send:
            print("......................send comlete......................")            
        else:
            msg = QMessageBox()
            # msg.setIcon(QMessageBox.Information)

            msg.setText("Dont have anythning to send")
            msg.setWindowTitle("Warning")                
            msg.exec_()
        
        return {'FINISHED'}

    def filepath_Dialog(self):
        path_To_File = QFileDialog.getExistingDirectory()
        if path_To_File:
            self.ui.label_file_path.setText(path_To_File)
  
  

    

def show():
    """Entry point for the GSTools menu/shelf."""
    global _bmc_window
    _bmc_window = MainWindow()
    try:
        _bmc_window.show()
    except Exception:
        pass
    return _bmc_window
