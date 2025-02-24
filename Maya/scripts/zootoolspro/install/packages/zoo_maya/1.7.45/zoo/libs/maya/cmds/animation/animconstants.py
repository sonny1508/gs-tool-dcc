from maya import cmds as cmds

FPS_DICT = {'game': 15.0,
            'film': 24.0,
            'pal': 25.0,
            'ntsc': 30.0,
            'show': 48.0,
            'palf': 50.0,
            'ntscf': 60.0,
            }

GRAPH_CYCLE_LONG = ["Cycle (Regular)", "Cycle With Offset (Stairs)", "Oscillate (Bounce)", "Linear (Keeps Going)",
                    "Constant (No Cycle)"]
GRAPH_CYCLE = ["cycle", "cycleRelative", "oscillate", "linear", "constant"]


def getSceneFPS():
    """Returns maya's current frame rate as a float

    :return framesPerSecond: The current frame rate as a float
    :rtype framesPerSecond: float
    """
    timeString = cmds.currentUnit(query=True, time=True)
    if timeString in FPS_DICT.keys():
        framesPerSecond = FPS_DICT[timeString]
        return framesPerSecond
    timeString = timeString.replace("fps", "")
    return float(timeString)
