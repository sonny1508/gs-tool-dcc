from zoo.libs.maya.utils import scene
from zoo.libs.pyqt.widgets import elements
from maya import cmds

SCENE_UNIT_MSG = """Hive must be in centimeter units while building. Please switch to cms.

Preferences > Settings > Linear: centimeter.

After completion any unit scale may be used for animation.
You can switch back after the rig has been built.

Switch to cm units now?"""


def checkSceneUnits(parent):
    if not scene.isCentimeters():
        ret = elements.MessageBox.showWarning(parent=parent,
                                              title="Incorrect Working Units",
                                              message=SCENE_UNIT_MSG, buttonB="Cancel")

        if ret == "A":  # ok clicked == set scene to cm
            cmds.currentUnit(linear="cm")
            return True
        return False
    return True
