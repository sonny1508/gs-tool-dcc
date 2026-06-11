import sys
from maya import cmds

from mayautils.tools.pipeline.legacy import mayautils_setup as mus

##########################
# Major Python Version: 2
if sys.version_info.major < 3:
    reload(mus)

    main_window_created_script_job = cmds.scriptJob(
        event=["NewSceneOpened", mus.start],
        runOnce=True
    )
#########################
# Major Python Version: 3
else:
    import importlib

    module = importlib.import_module("mayautils.tools.pipeline.milestone_menu.milestone_menu")
    importlib.reload(module)
    importlib.reload(mus)
    
    main_window_created_script_job = cmds.scriptJob(
        event=["NewSceneOpened", mus.clear],
        runOnce=True
    )
    main_window_created_script_job = cmds.scriptJob(
        event=["NewSceneOpened", module.run],
        runOnce=True
    )

# region COMET

# def load_comet():
#     mel.eval('source "cometScripts/cometMenu.mel"')
#
#
# main_window_created_script_job = cmds.scriptJob(
#         event=["NewSceneOpened", load_comet],
#         runOnce=True
#     )
# endregion
