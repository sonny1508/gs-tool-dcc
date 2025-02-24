__path__ = __import__('pkgutil').extend_path(__path__, __name__)


# Set rot axis based on strings
ROT_AXIS_DICT = {"+x": (0.0, -90.0, 90.0),
                 "-x": (0.0, 90.0, 90.0),
                 "+y": (0.0, 0.0, 0.0),
                 "-y": (0.0, 180.0, 0.0),
                 "+z": (90.0, 0.0, 0.0),
                 "-z": (-90.0, 0.0, 0.0)}

# Set rot up axis based on lists
X_UP = 0
X_DOWN = 1
Y_UP = 2
Y_DOWN = 3
Z_UP = 4
Z_DOWN = 5

NEW_CONTROL = "newControl"
CONTROLS_GRP_SUFFIX = "controls_grp"
ZOO_TRANSLATE_TRACK_ATTR = "zooTranslateTrack"
ZOO_TRANSLATE_DEFAULT_ATTR = "zooTranslateDefault"
ZOO_ROTATE_TRACK_ATTR = "zooRotateTrack"
ZOO_ROTATE_DEFAULT_ATTR = "zooRotateDefault"
ZOO_SCALE_TRACK_ATTR = "zooScaleTrack"
ZOO_SCALE_DEFAULT_ATTR = "zooScaleDefault"
ZOO_COLOR_TRACK_ATTR = "zooColorTrack"
ZOO_COLOR_DEFAULT_ATTR = "zooColorDefault"
ZOO_SHAPE_TRACK_ATTR = "zooShapeTrack"
ZOO_SHAPE_DEFAULT_ATTR = "zooShapeDefault"
XYZ_LIST = ["x", "y", "z"]
RGB_LIST = ["r", "g", "b"]
CONTROL_BUILD_TYPE_LIST = ["Joint, Shape Parent Ctrl", "Match Selection Only", "Constrain Obj, Cnstn Ctrl",
                           "Constrain Obj, Parent Ctrl", "Constrain Obj, Float Ctrl"]

ZOO_CONTROLTRACK_VECTOR_LIST = [ZOO_TRANSLATE_TRACK_ATTR, ZOO_TRANSLATE_DEFAULT_ATTR,
                                ZOO_ROTATE_TRACK_ATTR, ZOO_ROTATE_DEFAULT_ATTR,
                                ZOO_SCALE_TRACK_ATTR, ZOO_SCALE_DEFAULT_ATTR]
ZOO_CONTROLTRACK_RGB_LIST = [ZOO_COLOR_TRACK_ATTR, ZOO_COLOR_DEFAULT_ATTR]
ZOO_CONTROLTRACK_STRING_LIST = [ZOO_SHAPE_TRACK_ATTR, ZOO_SHAPE_DEFAULT_ATTR]

ZOO_TEMPBREAK_NETWORK = "breakTrack_network"
ZOO_TEMPBREAK_CTRL_ATTR = "zoo_ctrl_tempBreakTrack"
ZOO_TEMPBREAK_GRP_ATTR = "zoo_grp_tempBreakTrack"
ZOO_TEMPBREAK_MASTER_ATTR = "zoo_mstr_tempBreakTrack"


# ---------------------------
# ROTATE CONTROLS
# ---------------------------

ROTATE_UP_DICT = {Y_UP: [0, 0, 0],
                  Y_DOWN: [0, 180, 0],
                  X_UP: [0, -90, 90],
                  X_DOWN: [0, 90, 90],
                  Z_UP: [90, 0, 0],
                  Z_DOWN: [-90, 0, 0]}



