import maya.utils
import sys
import os
import maya.cmds as cmds

user_home = os.path.expanduser("~")
user_profile = os.environ.get('USERPROFILE', user_home)

gspipeline_path = os.path.join(user_profile, "Documents", "maya", "scripts", "GSPipeline")

sys.path.append(gspipeline_path)

import GSPipeline