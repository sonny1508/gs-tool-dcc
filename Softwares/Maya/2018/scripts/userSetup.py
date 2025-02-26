import maya.utils
import sys

sys.path.append("//192.168.1.10/Softwares/Technical_Script/Maya_2018/MayaTools/scripts/")

def addPaths():
    sys.path.append("//192.168.1.10/Softwares/Pipeline/GSTools/Softwares/Maya/scripts/GSTools")
    
    # Import your menu creation script
    import GS_Development

maya.utils.executeDeferred(addPaths)