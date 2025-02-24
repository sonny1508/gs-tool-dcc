"""Hive Constants
"""

#: hive meta class name
RIG_TYPE = "HiveRig"
#: Rig layer constant
RIG_LAYER_TYPE = "HiveRigLayer"
#: Guide layer constant
GUIDE_LAYER_TYPE = "HiveGuideLayer"
#: Deform layer constant
DEFORM_LAYER_TYPE = "HiveDeformLayer"
#: Control layer constant
CONTROL_PANEL_TYPE = "controlPanel"
#: Input layer constant
INPUT_LAYER_TYPE = "HiveInputLayer"
#: Output layer constant
OUTPUT_LAYER_TYPE = "HiveOutputLayer"
#: xGroup layer constant
XGROUP_LAYER_TYPE = "HiveXGroupLayer"
#: Component layer constant
COMPONENT_LAYER_TYPE = "HiveComponentLayer"
#: Geometry layer constant
GEOMETRY_LAYER_TYPE = "HiveGeometryLayer"
#: Settings layer constant
SETTINGS_NODE_TYPE = "settings"
#: Guide offsets attribute name
GUIDE_OFFSET_ATTR_NAME = "guide_offset"
#: {section} token of the naming expression for the guide offset meta node
GUIDE_OFFSET_NODE_NAME = "guide_offset"
#: Input Offset attribute name
INPUT_OFFSET_ATTR_NAME = "inputGuide_offset"
#: {section} token of the naming expression for the input offset meta node
INPUT_GUIDE_OFFSET_NODE_NAME = "inputGuide_offset"
#: Root Node constant
ROOT_NODE_TYPE = "root"
#: Input prefix constant
INPUT_PREFIX = "IN"
#: Output prefix constant
OUTPUT_PREFIX = "OUT"
#: Input node type constant
INPUT_NODE_TYPE = "in"
#: Output node type constant
OUTPUT_NODE_TYPE = "out"
#: Component type constant
COMPONENT_TYPE = "component"
#: container Asset type constant
CONTAINER_TYPE_ASSET = "asset"
#: container Selection set type constant
CONTAINER_TYPE_SET = "set"
#: Container Name constant
CONTAINER_NAME = "container"
#: Inverse kinematric str type constant
IKTYPE = "ik"
#: forward kinematics str type constant
FKTYPE = "fk"
#: Deform type constant
SKINTYPE = "skin"
#: names for standard transform local attributes
TRANSFORM_ATTRS = ("translate", "rotate", "scale")

WORLD_UP_VEC_ID = "worldUpVec"
#: All Hive layers type names
LAYER_TYPES = (RIG_LAYER_TYPE,
               GUIDE_LAYER_TYPE,
               DEFORM_LAYER_TYPE,
               INPUT_LAYER_TYPE,
               OUTPUT_LAYER_TYPE,
               XGROUP_LAYER_TYPE,
               COMPONENT_LAYER_TYPE,
               GEOMETRY_LAYER_TYPE)

#: All layers and node types for hive
ALL_TYPES = (RIG_LAYER_TYPE,
             GUIDE_LAYER_TYPE,
             DEFORM_LAYER_TYPE,
             CONTROL_PANEL_TYPE,
             INPUT_LAYER_TYPE,
             OUTPUT_LAYER_TYPE,
             XGROUP_LAYER_TYPE,
             COMPONENT_LAYER_TYPE,
             GEOMETRY_LAYER_TYPE,
             SETTINGS_NODE_TYPE,
             ROOT_NODE_TYPE)
#: tuple for x,y,z string names
ALL_AXIS = ("x", "y", "z")
#: Axis name to compound child index
AXIS_DICT = {"x": 0, "y": 1, "z": 2}
MIRROR_BEHAVIOURS_TYPES = ["Behaviour", "Relative", "Scale"]
#: attributes to ignore when serializing nodes into the definition
ATTRIBUTES_SERIALIZE_SKIP = ("message", "center", "hyperLayout", "boundingBox", "zooConstraint")

#: hive template extension
TEMPLATE_EXT = ".template"
#: graph data file .extension
GRAPH_EXT = ".dgGraph"
#: hive component definition extension
DEFINITION_EXT = ".definition"

#: definition keys
INPUTLAYER_DEF_KEY = "inputLayer"
OUTPUTLAYER_DEF_KEY = "outputLayer"
GUIDELAYER_DEF_KEY = "guideLayer"
RIGLAYER_DEF_KEY = "rigLayer"
DEFORMLAYER_DEF_KEY = "deformLayer"
PARENT_DEF_KEY = "parent"
CONNECTIONS_DEF_KEY = "connections"
DAG_DEF_KEY = "dag"
SETTINGS_DEF_KEY = "settings"
NAME_DEF_KEY = "name"
SIDE_DEF_KEY = "side"
TYPE_DEF_KEY = "type"
METADATA_DEF_KEY = "metadata"
DG_GRAPH_DEF_KEY = "dg"
DEFINITION_VERSION_DEF_KEY = "definitionVersion"
SPACE_SWITCH_DEF_KEY = "spaceSwitching"
NAMING_PRESET_DEF_KEY = "namingPreset"

LAYER_DEF_KEYS = (INPUTLAYER_DEF_KEY,
                  OUTPUTLAYER_DEF_KEY,
                  GUIDELAYER_DEF_KEY,
                  RIGLAYER_DEF_KEY,
                  DEFORMLAYER_DEF_KEY)
#: Definition attribute expression constants
ATTR_EXPR_SELF_TOKEN = "@{self}"
ATTR_EXPR_INHERIT_TOKEN = "@{inherit}"
ATTR_EXPR_REGEX_PATTERN = r"(?:\@{(.*)\})"

#: Meta Data Attribute Names
ISCOMPONENT_ATTR = "isComponent"
ISHIVE_ATTR = "isHive"
ISHIVEROOT_ATTR = "isHiveRoot"
RIG_CONFIG_ATTR = "hiveConfig"
DISPLAY_LAYER_ATTR = "controlDisplayLayer"
CONTAINER_ATTR = "container"
HNAME_ATTR = "hName"
SIDE_ATTR = "hiveSide"
ID_ATTR = "zooHiveId"
VERSION_ATTR = "version"
COMPONENTTYPE_ATTR = "componentType"
HASGUIDE_ATTR = "hasGuide"
HASGUIDE_CONTROLS_ATTR = "hasGuideControls"
HASSKELETON_ATTR = "hasSkeleton"
HASPOLISHED_ATTR = "hasPolished"
HASRIG_ATTR = "hasRig"
COMPONENTDEFINITION_ATTR = "componentDefinition"
COMPONENTGROUP_ATTR = "componentGroup"
DG_GRAPH_ATTR = "hiveDGGraph"
CONTROLMODE_ATTR = "controlMode"
MESSAGE_ATTR = "message"
PIVOTNODE_ATTR = "pivotNode"
COMPONENTGROUPS_ATTR = "componentGroups"
EXTRANODES_ATTR = "extraNodes"
LAYERTYPE_ATTR = "layerType"
ROOTTRANSFORM_ATTR = "rootTransform"
ISGUIDE_ATTR = "hiveIsGuide"
ISINPUT_ATTR = "hiveIsInput"
ISOUTPUT_ATTR = "hiveIsOutput"
GUIDESHAPE_ATTR = "guideShape"
PIVOTSHAPE_ATTR = "pivotShape"
PIVOTCOLOR_ATTR = "pivotColor"
GUIDESNAP_PIVOT_ATTR = "guideSnapPivot"
GUIDE_SHAPE_PRIMARY_ATTR = "guideShapePrimary"
AUTOALIGNAIMVECTOR_ATTR = "autoAlignAimVector"
AUTOALIGNUPVECTOR_ATTR = "autoAlignUpVector"
AUTOALIGN_ATTR = "autoAlign"
MIRROR_ATTR = "mirror"
# Determines the mirroring behaviour for a single guide
MIRROR_BEHAVIOUR_ATTR = "mirrorBehaviour"
# Mirror plane direction storage attr
MIRROR_PLANE_ATTR = "mirrorPlane"
# Attr to determine if the guide was scaled
MIRROR_SCALED_ATTR = "mirrorScaled"
DISPLAYAXISSHAPE_ATTR = "displayAxisShape"
ZOO_ANNOTATIONS_ATTR = "zooAnnotations"
CONTROL_DISPLAY_LAYER_ATTR = "controlDisplayLayer"
ROOT_SELECTION_SET_ATTR = "zooRootSelectionSet"
CTRL_SELECTION_SET_ATTR = "zooCtrlSelectionSet"
DEFORM_SELECTION_SET_ATTR = "zooDeformSelectionSet"
BUILD_SCRIPT_CONFIG_ATTR = "zooBuildScriptConfig"
GUIDE_MM_LAYOUT_DEF_KEY = "mm_guide_Layout"
RIG_MM_LAYOUT_DEF_KEY = "mm_rig_Layout"
DEFORM_MM_LAYOUT_DEF_KEY = "mm_deform_Layout"
ANIM_MM_LAYOUT_DEF_KEY = "mm_anim_Layout"
#: used for storing component meta data when referencing joint hierarchies
HIVE_EXTERNAL_METADATA_ATTR = "hiveExternalMetaData"

#: Attribute names which store parts of the component definition
DEF_CACHE_INFO_ATTR = "{}.zooDefCacheInfo".format(COMPONENTDEFINITION_ATTR)
DEF_CACHE_GUIDE_DAG_ATTR = "{}.zooDefCacheGuideLayerDag".format(COMPONENTDEFINITION_ATTR)
DEF_CACHE_GUIDE_DG_ATTR = "{}.zooDefCacheGuideLayerDg".format(COMPONENTDEFINITION_ATTR)
DEF_CACHE_GUIDE_SETTINGS_ATTR = "{}.zooDefCacheGuideLayerSettings".format(COMPONENTDEFINITION_ATTR)
DEF_CACHE_GUIDE_METADATA_ATTR = "{}.zooDefCacheGuideLayerMetadata".format(COMPONENTDEFINITION_ATTR)
DEF_CACHE_DEFORM_DAG_ATTR = "{}.zooDefCacheDeformLayerDag".format(COMPONENTDEFINITION_ATTR)
DEF_CACHE_DEFORM_SETTINGS_ATTR = "{}.zooDefCacheDeformLayerSettings".format(COMPONENTDEFINITION_ATTR)
DEF_CACHE_DEFORM_METADATA_ATTR = "{}.zooDefCacheDeformLayerMetadata".format(COMPONENTDEFINITION_ATTR)
DEF_CACHE_INPUT_DAG_ATTR = "{}.zooDefCacheInputLayerDag".format(COMPONENTDEFINITION_ATTR)
DEF_CACHE_INPUT_SETTINGS_ATTR = "{}.zooDefCacheInputLayerSettings".format(COMPONENTDEFINITION_ATTR)
DEF_CACHE_INPUT_METADATA_ATTR = "{}.zooDefCacheInputLayerMetadata".format(COMPONENTDEFINITION_ATTR)
DEF_CACHE_OUTPUT_DAG_ATTR = "{}.zooDefCacheOutputLayerDag".format(COMPONENTDEFINITION_ATTR)
DEF_CACHE_OUTPUT_SETTINGS_ATTR = "{}.zooDefCacheOutputLayerSettings".format(COMPONENTDEFINITION_ATTR)
DEF_CACHE_OUTPUT_METADATA_ATTR = "{}.zooDefCacheOutputLayerMetadata".format(COMPONENTDEFINITION_ATTR)
DEF_CACHE_RIG_DAG_ATTR = "{}.zooDefCacheRigLayerDag".format(COMPONENTDEFINITION_ATTR)
DEF_CACHE_RIG_DG_ATTR = "{}.zooDefCacheRigLayerDg".format(COMPONENTDEFINITION_ATTR)
DEF_CACHE_RIG_SETTINGS_ATTR = "{}.zooDefCacheRigLayerSettings".format(COMPONENTDEFINITION_ATTR)
DEF_CACHE_RIG_METADATA_ATTR = "{}.zooDefCacheRigLayerMetadata".format(COMPONENTDEFINITION_ATTR)
DEF_CACHE_SPACE_SWITCHING_ATTR = "{}.zooDefCacheSpaceSwitching".format(COMPONENTDEFINITION_ATTR)

DEF_CACHE_ATTR_NAMES = (DEF_CACHE_INFO_ATTR,
                        DEF_CACHE_GUIDE_DAG_ATTR,
                        DEF_CACHE_GUIDE_DG_ATTR,
                        DEF_CACHE_GUIDE_SETTINGS_ATTR,
                        DEF_CACHE_GUIDE_METADATA_ATTR,
                        DEF_CACHE_DEFORM_DAG_ATTR,
                        DEF_CACHE_DEFORM_SETTINGS_ATTR,
                        DEF_CACHE_DEFORM_METADATA_ATTR,
                        DEF_CACHE_INPUT_DAG_ATTR,
                        DEF_CACHE_INPUT_SETTINGS_ATTR,
                        DEF_CACHE_INPUT_METADATA_ATTR,
                        DEF_CACHE_OUTPUT_DAG_ATTR,
                        DEF_CACHE_OUTPUT_SETTINGS_ATTR,
                        DEF_CACHE_OUTPUT_METADATA_ATTR,
                        DEF_CACHE_RIG_DAG_ATTR,
                        DEF_CACHE_RIG_DG_ATTR,
                        DEF_CACHE_RIG_SETTINGS_ATTR,
                        DEF_CACHE_RIG_METADATA_ATTR,
                        DEF_CACHE_SPACE_SWITCHING_ATTR
                        )
#: guide visibility state types
GUIDE_PIVOT_STATE = 0
GUIDE_CONTROL_STATE = 1
GUIDE_PIVOT_CONTROL_STATE = 2

_ATTRIBUTES_TO_SKIP_PUBLISH = (ID_ATTR, "metaNode", "zooConstraint")

#: environment variable keys
ENV_COMPONENT_KEY = "HIVE_COMPONENT_PATH"
ENV_DEFINITION_KEY = "HIVE_DEFINITIONS_PATH"
ENV_TEMPLATES_KEY = "HIVE_TEMPLATE_PATH"
ENV_GRAPHS_KEY = "HIVE_GRAPHS_PATH"
ENV_TEMPLATE_SAVE_KEY = "HIVE_TEMPLATE_SAVE_PATH"

#: guide alignment default Aim/up Vectors
DEFAULT_AIM_VECTOR = (1.0, 0.0, 0.0)
DEFAULT_UP_VECTOR = (0.0, 1.0, 0.0)
#: default guide pivot color
DEFAULT_GUIDE_PIVOT_COLOR = (1.0, 1.0, 0.0)
#: naming preset keys
GLOBAL_NAME_CONFIG_TYPE = "global"
GLOBAL_NAME_CONFIG_NAME = "zootoolsProGlobalConfig"
DEFAULT_BUILTIN_PRESET_NAME = "ZooToolsPro"

#: Rig has yet to be built
NOT_BUILT = 0
#: Rig Guides has been built
GUIDES_STATE = 1
#: Guides are built and the controls are visible.
CONTROL_VIS_STATE = 2
#: Skeleton(deform) has been built
SKELETON_STATE = 3
#: Animation rig has been built, this is the riggers state.
RIG_STATE = 4
#: Rig has been polished, ready for animation.
POLISH_STATE = 5


#: build script function type constants, Maps to individual build script functions.
GUIDE_FUNC_TYPE = 0
DEFORM_FUNC_TYPE = 1
RIG_FUNC_TYPE = 2
POLISH_FUNC_TYPE = 3
DELETE_GUIDELAYER_FUNC_TYPE = 4
DELETE_DEFORMLAYER_FUNC_TYPE = 5
DELETE_RIGLAYER_FUNC_TYPE = 6
DELETE_COMP_FUNC_TYPE = 7
DELETE_COMPS_FUNC_TYPE = 8
DELETE_RIG_FUNC_TYPE = 9

#: class method name mapping for building scripting for pre and post for each step
BUILDSCRIPT_FUNC_MAPPING = {GUIDE_FUNC_TYPE: ("preGuideBuild", "postGuideBuild"),
                            DEFORM_FUNC_TYPE: ("preDeformBuild", "postDeformBuild"),
                            RIG_FUNC_TYPE: ("preRigBuild", "postRigBuild"),
                            POLISH_FUNC_TYPE: ("prePolish", "postPolishBuild"),
                            DELETE_GUIDELAYER_FUNC_TYPE: ("preDeleteGuideLayer", None),
                            DELETE_DEFORMLAYER_FUNC_TYPE: ("preDeleteDeformLayer", None),
                            DELETE_RIGLAYER_FUNC_TYPE: ("preDeleteRigLayer", None),
                            DELETE_COMPS_FUNC_TYPE: ("preDeleteComponents", None),
                            DELETE_COMP_FUNC_TYPE: ("preDeleteComponent", None),
                            DELETE_RIG_FUNC_TYPE: ("preDeleteRig", None)
                            }
