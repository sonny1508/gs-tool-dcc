"""Toggle the viewport background between a grey gradient and flat magenta."""
import maya.cmds as cmds


def run():
    if cmds.displayPref(q=True, displayGradient=True) is False:
        cmds.displayRGBColor('background', 0.5, 0.5, 0.5)
        cmds.displayPref(displayGradient=True)
    else:
        cmds.displayRGBColor('background', 1, 0, 1)
        cmds.displayPref(displayGradient=False)
