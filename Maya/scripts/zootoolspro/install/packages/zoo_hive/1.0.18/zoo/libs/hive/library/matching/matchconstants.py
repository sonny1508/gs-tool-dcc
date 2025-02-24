ROOT_KEY = "root"
SHOULDER_KEY_L = "shoulder_L"
ELBOW_KEY_L = "elbow_L"
WRIST_KEY_L = "wrist_L"
THIGH_KEY_L = "thigh_L"
KNEE_KEY_L = "knee_L"
ANKLE_KEY_L = "ankle_L"
BALL_KEY_L = "ball_L"
TOE_KEY_L = "toe_L"
CLAVICLE_KEY_L = "clavicle_L"
HIP_KEY_M = "hip_M"  # Spine IK base
CHEST_KEY_M = "chest_M"  # Spine IK top
NECK_KEY_M = "neck_M"
HEAD_KEY_M = "head_M"
SPINE00_KEY_M = "spine00_M"  # Spine FK base
SPINE01_KEY_M = "spine01_M"
SPINE02_KEY_M = "spine02_M"
SPINE03_KEY_M = "spine03_M"
SPINE04_KEY_M = "spine04_M"
SPINE05_KEY_M = "spine05_M"
SPINE06_KEY_M = "spine06_M"
SPINE07_KEY_M = "spine07_M"
SPINE08_KEY_M = "spine08_M"
SPINE09_KEY_M = "spine09_M"
SPINE10_KEY_M = "spine10_M"
THUMB01_KEY_L = "thumb01_L"
THUMB02_KEY_L = "thumb02_L"
THUMB03_KEY_L = "thumb03_L"
INDEXMETACARPAL_KEY_L = "indexMetacarpal_L"
INDEX01_KEY_L = "index01_L"
INDEX02_KEY_L = "index02_L"
INDEX03_KEY_L = "index03_L"
MIDDLEMETACARPAL_KEY_L = "middleMetacarpal_L"
MIDDLE01_KEY_L = "middle01_L"
MIDDLE02_KEY_L = "middle02_L"
MIDDLE03_KEY_L = "middle03_L"
RINGMETACARPAL_KEY_L = "ringMetacarpal_L"
RING01_KEY_L = "ring01_L"
RING02_KEY_L = "ring02_L"
RING03_KEY_L = "ring03_L"
PINKYMETACARPAL_KEY_L = "pinkyMetacarpal_L"
PINKY01_KEY_L = "pinky01_L"
PINKY02_KEY_L = "pinky02_L"
PINKY03_KEY_L = "pinky03_L"

SPINESPINE_ORDER = [ROOT_KEY, HIP_KEY_M, CHEST_KEY_M]
FKSPINE_ORDER = [ROOT_KEY, SPINE00_KEY_M, SPINE01_KEY_M, SPINE02_KEY_M, SPINE03_KEY_M, SPINE04_KEY_M, SPINE05_KEY_M,
                 SPINE06_KEY_M, SPINE07_KEY_M, SPINE08_KEY_M, SPINE09_KEY_M, SPINE10_KEY_M]

HIERARCHY_ORDER_NO_SPINE = [NECK_KEY_M, HEAD_KEY_M, CLAVICLE_KEY_L, SHOULDER_KEY_L,
                            WRIST_KEY_L, ELBOW_KEY_L, THUMB01_KEY_L, THUMB02_KEY_L, THUMB03_KEY_L,
                            INDEXMETACARPAL_KEY_L, INDEX01_KEY_L, INDEX02_KEY_L, INDEX03_KEY_L,
                            MIDDLEMETACARPAL_KEY_L, MIDDLE01_KEY_L, MIDDLE02_KEY_L, MIDDLE03_KEY_L,
                            RINGMETACARPAL_KEY_L, RING01_KEY_L, RING02_KEY_L, RING03_KEY_L,
                            PINKYMETACARPAL_KEY_L, PINKY01_KEY_L, PINKY02_KEY_L, PINKY03_KEY_L,
                            THIGH_KEY_L, ANKLE_KEY_L, KNEE_KEY_L, BALL_KEY_L, TOE_KEY_L]

HIERARCHY_ORDER_SPLINESPINE = SPINESPINE_ORDER + HIERARCHY_ORDER_NO_SPINE
HIERARCHY_ORDER_FKSPINE = FKSPINE_ORDER + FKSPINE_ORDER

# Rotate align guides all finger joints need to rotate match align to skeleton fingers
ROT_ALIGN_GUIDES = [THUMB01_KEY_L, THUMB02_KEY_L, THUMB03_KEY_L,
                    INDEXMETACARPAL_KEY_L, INDEX01_KEY_L, INDEX02_KEY_L, INDEX03_KEY_L,
                    MIDDLEMETACARPAL_KEY_L, MIDDLE01_KEY_L, MIDDLE02_KEY_L, MIDDLE03_KEY_L,
                    RINGMETACARPAL_KEY_L, RING01_KEY_L, RING02_KEY_L, RING03_KEY_L,
                    PINKYMETACARPAL_KEY_L, PINKY01_KEY_L, PINKY02_KEY_L, PINKY03_KEY_L]

HIVE_BIPED_IDS = {ROOT_KEY: ["god", "root", "M"],
                  SHOULDER_KEY_L: ["arm", "root", "L"],
                  ELBOW_KEY_L: ["arm", "mid", "L"],
                  WRIST_KEY_L: ["arm", "end", "L"],
                  THIGH_KEY_L: ["leg", "root", "L"],
                  KNEE_KEY_L: ["leg", "mid", "L"],
                  ANKLE_KEY_L: ["leg", "end", "L"],
                  BALL_KEY_L: ["leg", "ball", "L"],
                  TOE_KEY_L: ["leg", "toe", "L"],
                  CLAVICLE_KEY_L: ["clavicle", "root", "L"],
                  HIP_KEY_M: ["spine", "root", "M"],
                  CHEST_KEY_M: ["spine", "endCurvePiv", "M"],
                  NECK_KEY_M: ["head", "root", "M"],
                  HEAD_KEY_M: ["head", "head", "M"],
                  SPINE00_KEY_M: ["spine", "00", "M"],
                  SPINE01_KEY_M: ["spine", "01", "M"],
                  SPINE02_KEY_M: ["spine", "02", "M"],
                  SPINE03_KEY_M: ["spine", "03", "M"],
                  SPINE04_KEY_M: ["spine", "04", "M"],
                  SPINE05_KEY_M: ["spine", "05", "M"],
                  SPINE06_KEY_M: ["spine", "06", "M"],
                  SPINE07_KEY_M: ["spine", "07", "M"],
                  SPINE08_KEY_M: ["spine", "08", "M"],
                  SPINE09_KEY_M: ["spine", "09", "M"],
                  SPINE10_KEY_M: ["spine", "10", "M"],
                  THUMB01_KEY_L: ["finger_thumb", "root", "L"],
                  THUMB02_KEY_L: ["finger_thumb", "fk01", "L"],
                  THUMB03_KEY_L: ["finger_thumb", "fk02", "L"],
                  INDEXMETACARPAL_KEY_L: ["finger_pointer", "root", "L"],
                  INDEX01_KEY_L: ["finger_pointer", "fk01", "L"],
                  INDEX02_KEY_L: ["finger_pointer", "fk02", "L"],
                  INDEX03_KEY_L: ["finger_pointer", "fk03", "L"],
                  MIDDLEMETACARPAL_KEY_L: ["finger_middle", "root", "L"],
                  MIDDLE01_KEY_L: ["finger_middle", "fk01", "L"],
                  MIDDLE02_KEY_L: ["finger_middle", "fk02", "L"],
                  MIDDLE03_KEY_L: ["finger_middle", "fk03", "L"],
                  RINGMETACARPAL_KEY_L: ["finger_ring", "root", "L"],
                  RING01_KEY_L: ["finger_ring", "fk01", "L"],
                  RING02_KEY_L: ["finger_ring", "fk02", "L"],
                  RING03_KEY_L: ["finger_ring", "fk03", "L"],
                  PINKYMETACARPAL_KEY_L: ["finger_pinky", "root", "L"],
                  PINKY01_KEY_L: ["finger_pinky", "fk01", "L"],
                  PINKY02_KEY_L: ["finger_pinky", "fk02", "L"],
                  PINKY03_KEY_L: ["finger_pinky", "fk03", "L"]
                  }

HIVE_BIPED_SKELETON = {ROOT_KEY: "god_M_root_jnt",
                       SHOULDER_KEY_L: "arm_L_shldr_jnt",
                       ELBOW_KEY_L: "arm_L_elbow_jnt",
                       WRIST_KEY_L: "arm_L_wrist_jnt",
                       THIGH_KEY_L: "leg_L_upr_jnt",
                       KNEE_KEY_L: "leg_L_knee_jnt",
                       ANKLE_KEY_L: "leg_L_foot_jnt",
                       BALL_KEY_L: "leg_L_ball_jnt",
                       TOE_KEY_L: "leg_L_toe_jnt",
                       CLAVICLE_KEY_L: "clavicle_L_00_jnt",
                       HIP_KEY_M: "spine_M_00_jnt",
                       CHEST_KEY_M: "spine_M_05_jnt",
                       NECK_KEY_M: "head_M_neck_jnt",
                       HEAD_KEY_M: "head_M_head_jnt",
                       SPINE00_KEY_M: "spine_M_00_jnt",
                       SPINE01_KEY_M: "spine_M_01_jnt",
                       SPINE02_KEY_M: "spine_M_02_jnt",
                       SPINE03_KEY_M: "spine_M_03_jnt",
                       SPINE04_KEY_M: "spine_M_04_jnt",
                       SPINE05_KEY_M: "spine_M_05_jnt",
                       SPINE06_KEY_M: "spine_M_06_jnt",
                       SPINE07_KEY_M: "spine_M_07_jnt",
                       SPINE08_KEY_M: "spine_M_08_jnt",
                       SPINE09_KEY_M: "spine_M_09_jnt",
                       SPINE10_KEY_M: "spine_M_10_jnt",
                       THUMB01_KEY_L: "finger_thumb_L_00_jnt",
                       THUMB02_KEY_L: "finger_thumb_L_01_jnt",
                       THUMB03_KEY_L: "finger_thumb_L_02_jnt",
                       INDEXMETACARPAL_KEY_L: "finger_pointer_L_00_jnt",
                       INDEX01_KEY_L: "finger_pointer_L_01_jnt",
                       INDEX02_KEY_L: "finger_pointer_L_02_jnt",
                       INDEX03_KEY_L: "finger_pointer_L_03_jnt",
                       MIDDLEMETACARPAL_KEY_L: "finger_middle_L_00_jnt",
                       MIDDLE01_KEY_L: "finger_middle_L_01_jnt",
                       MIDDLE02_KEY_L: "finger_middle_L_02_jnt",
                       MIDDLE03_KEY_L: "finger_middle_L_03_jnt",
                       RINGMETACARPAL_KEY_L: "finger_ring_L_00_jnt",
                       RING01_KEY_L: "finger_ring_L_01_jnt",
                       RING02_KEY_L: "finger_ring_L_02_jnt",
                       RING03_KEY_L: "finger_ring_L_03_jnt",
                       PINKYMETACARPAL_KEY_L: "finger_pinky_L_00_jnt",
                       PINKY01_KEY_L: "finger_pinky_L_01_jnt",
                       PINKY02_KEY_L: "finger_pinky_L_02_jnt",
                       PINKY03_KEY_L: "finger_pinky_L_03_jnt",
                       }

SKELEBUILDER_BIPED_SKELETON = {ROOT_KEY: "",
                               SHOULDER_KEY_L: "L_bicep",
                               ELBOW_KEY_L: "L_elbow",
                               WRIST_KEY_L: "L_wrist",
                               THIGH_KEY_L: "L_leg01",
                               KNEE_KEY_L: "L_leg02",
                               ANKLE_KEY_L: "L_leg03",
                               BALL_KEY_L: "L_toeBase",
                               TOE_KEY_L: "L_leg03_tip",
                               CLAVICLE_KEY_L: "L_clavicle",
                               HIP_KEY_M: "root",
                               CHEST_KEY_M: "spine5",
                               NECK_KEY_M: "neck1",
                               HEAD_KEY_M: "head",
                               SPINE00_KEY_M: "root",
                               SPINE01_KEY_M: "spine1",
                               SPINE02_KEY_M: "spine2",
                               SPINE03_KEY_M: "spine3",
                               SPINE04_KEY_M: "spine4",
                               SPINE05_KEY_M: "spine5",
                               SPINE06_KEY_M: "",
                               SPINE07_KEY_M: "",
                               SPINE08_KEY_M: "",
                               SPINE09_KEY_M: "",
                               SPINE10_KEY_M: "",
                               THUMB01_KEY_L: "Thumb_0_L",
                               THUMB02_KEY_L: "Thumb_1_L",
                               THUMB03_KEY_L: "Thumb_2_L",
                               INDEXMETACARPAL_KEY_L: "Index_0_L",
                               INDEX01_KEY_L: "Index_1_L",
                               INDEX02_KEY_L: "Index_2_L",
                               INDEX03_KEY_L: "Index_3_L",
                               MIDDLEMETACARPAL_KEY_L: "Mid_0_L",
                               MIDDLE01_KEY_L: "Mid_1_L",
                               MIDDLE02_KEY_L: "Mid_2_L",
                               MIDDLE03_KEY_L: "Mid_3_L",
                               RINGMETACARPAL_KEY_L: "Ring_0_L",
                               RING01_KEY_L: "Ring_1_L",
                               RING02_KEY_L: "Ring_2_L",
                               RING03_KEY_L: "Ring_3_L",
                               PINKYMETACARPAL_KEY_L: "Pinky_0_L",
                               PINKY01_KEY_L: "Pinky_1_L",
                               PINKY02_KEY_L: "Pinky_2_L",
                               PINKY03_KEY_L: "Pinky_3_L",
                               }

HUMANIK_BIPED_SKELETON = {ROOT_KEY: "",
                          SHOULDER_KEY_L: "LeftArm",
                          ELBOW_KEY_L: "LeftForeArm",
                          WRIST_KEY_L: "LeftHand",
                          THIGH_KEY_L: "LeftUpLeg",
                          KNEE_KEY_L: "LeftLeg",
                          ANKLE_KEY_L: "LeftFoot",
                          BALL_KEY_L: "LeftToeBase",
                          TOE_KEY_L: "LeftToe_End",
                          CLAVICLE_KEY_L: "LeftShoulder",
                          HIP_KEY_M: "Hips",
                          CHEST_KEY_M: "Spine2",
                          NECK_KEY_M: "Neck",
                          HEAD_KEY_M: "Head",
                          SPINE00_KEY_M: "Hips",
                          SPINE01_KEY_M: "Spine",
                          SPINE02_KEY_M: "Spine1",
                          SPINE03_KEY_M: "",
                          SPINE04_KEY_M: "",
                          SPINE05_KEY_M: "Spine2",
                          SPINE06_KEY_M: "",
                          SPINE07_KEY_M: "",
                          SPINE08_KEY_M: "",
                          SPINE09_KEY_M: "",
                          SPINE10_KEY_M: "",
                          THUMB01_KEY_L: "LeftHandThumb1",
                          THUMB02_KEY_L: "LeftHandThumb2",
                          THUMB03_KEY_L: "LeftHandThumb3",
                          INDEXMETACARPAL_KEY_L: "",
                          INDEX01_KEY_L: "LeftHandIndex1",
                          INDEX02_KEY_L: "LeftHandIndex2",
                          INDEX03_KEY_L: "LeftHandIndex3",
                          MIDDLEMETACARPAL_KEY_L: "",
                          MIDDLE01_KEY_L: "LeftHandMiddle1",
                          MIDDLE02_KEY_L: "LeftHandMiddle2",
                          MIDDLE03_KEY_L: "LeftHandMiddle3",
                          RINGMETACARPAL_KEY_L: "",
                          RING01_KEY_L: "LeftHandRing1",
                          RING02_KEY_L: "LeftHandRing2",
                          RING03_KEY_L: "LeftHandRing3",
                          PINKYMETACARPAL_KEY_L: "",
                          PINKY01_KEY_L: "LeftHandPinky1",
                          PINKY02_KEY_L: "LeftHandPinky2",
                          PINKY03_KEY_L: "LeftHandPinky3",
                          }

MIXAMO_BIPED_SKELETON = HUMANIK_BIPED_SKELETON

UNITY_BIPED_SKELETON = HUMANIK_BIPED_SKELETON  # Not sure but seems Human IK is ok

ACCURIG_BIPED_SKELETON = {ROOT_KEY: "RL_BoneRoot",
                          SHOULDER_KEY_L: "CC_Base_L_Upperarm",
                          ELBOW_KEY_L: "CC_Base_L_Forearm",
                          WRIST_KEY_L: "CC_Base_L_Hand",
                          THIGH_KEY_L: "CC_Base_L_Thigh",
                          KNEE_KEY_L: "CC_Base_L_Calf",
                          ANKLE_KEY_L: "CC_Base_L_Foot",
                          BALL_KEY_L: "CC_Base_L_ToeBase",
                          TOE_KEY_L: "CC_Base_L_ToeBase",
                          CLAVICLE_KEY_L: "CC_Base_L_Clavicle",
                          HIP_KEY_M: "CC_Base_Hip",
                          CHEST_KEY_M: "CC_Base_Spine02",
                          NECK_KEY_M: "CC_Base_NeckTwist01",
                          HEAD_KEY_M: "CC_Base_Head",
                          SPINE00_KEY_M: "CC_Base_Pelvis",
                          SPINE01_KEY_M: "CC_Base_Waist",
                          SPINE02_KEY_M: "CC_Base_Spine01",
                          SPINE03_KEY_M: "",
                          SPINE04_KEY_M: "",
                          SPINE05_KEY_M: "CC_Base_Spine02",
                          SPINE06_KEY_M: "",
                          SPINE07_KEY_M: "",
                          SPINE08_KEY_M: "",
                          SPINE09_KEY_M: "",
                          SPINE10_KEY_M: "",
                          THUMB01_KEY_L: "CC_Base_L_Thumb1",
                          THUMB02_KEY_L: "CC_Base_L_Thumb2",
                          THUMB03_KEY_L: "CC_Base_L_Thumb3",
                          INDEXMETACARPAL_KEY_L: "",
                          INDEX01_KEY_L: "CC_Base_L_Index1",
                          INDEX02_KEY_L: "CC_Base_L_Index2",
                          INDEX03_KEY_L: "CC_Base_L_Index3",
                          MIDDLEMETACARPAL_KEY_L: "",
                          MIDDLE01_KEY_L: "CC_Base_L_Mid1",
                          MIDDLE02_KEY_L: "CC_Base_L_Mid2",
                          MIDDLE03_KEY_L: "CC_Base_L_Mid3",
                          RINGMETACARPAL_KEY_L: "",
                          RING01_KEY_L: "CC_Base_L_Ring1",
                          RING02_KEY_L: "CC_Base_L_Ring2",
                          RING03_KEY_L: "CC_Base_L_Ring3",
                          PINKYMETACARPAL_KEY_L: "",
                          PINKY01_KEY_L: "CC_Base_L_Pinky1",
                          PINKY02_KEY_L: "CC_Base_L_Pinky2",
                          PINKY03_KEY_L: "CC_Base_L_Pinky3",
                          }

UE5_BIPED_SKELETON = {ROOT_KEY: "root",
                      SHOULDER_KEY_L: "upperarm_l",
                      ELBOW_KEY_L: "lowerarm_l",
                      WRIST_KEY_L: "hand_l",
                      THIGH_KEY_L: "thigh_l",
                      KNEE_KEY_L: "calf_l",
                      ANKLE_KEY_L: "foot_l",
                      BALL_KEY_L: "ball_l",
                      TOE_KEY_L: "toe_l",
                      CLAVICLE_KEY_L: "clavicle_l",
                      HIP_KEY_M: "hipsSwing",
                      CHEST_KEY_M: "spine_06",
                      NECK_KEY_M: "neck_01",
                      HEAD_KEY_M: "head",
                      SPINE00_KEY_M: "hipsSwing",
                      SPINE01_KEY_M: "spine_01",
                      SPINE02_KEY_M: "spine_02",
                      SPINE03_KEY_M: "spine_03",
                      SPINE04_KEY_M: "spine_04",
                      SPINE05_KEY_M: "spine_05",
                      SPINE06_KEY_M: "spine_06",
                      SPINE07_KEY_M: "",
                      SPINE08_KEY_M: "",
                      SPINE09_KEY_M: "",
                      SPINE10_KEY_M: "",
                      THUMB01_KEY_L: "thumb_01_l",
                      THUMB02_KEY_L: "thumb_02_l",
                      THUMB03_KEY_L: "thumb_03_l",
                      INDEXMETACARPAL_KEY_L: "index_metacarpal_l",
                      INDEX01_KEY_L: "index_01_l",
                      INDEX02_KEY_L: "index_02_l",
                      INDEX03_KEY_L: "index_03_l",
                      MIDDLEMETACARPAL_KEY_L: "middle_metacarpal_l",
                      MIDDLE01_KEY_L: "middle_01_l",
                      MIDDLE02_KEY_L: "middle_02_l",
                      MIDDLE03_KEY_L: "middle_03_l",
                      RINGMETACARPAL_KEY_L: "ring_metacarpal_l",
                      RING01_KEY_L: "ring_01_l",
                      RING02_KEY_L: "ring_02_l",
                      RING03_KEY_L: "ring_03_l",
                      PINKYMETACARPAL_KEY_L: "pinky_metacarpal_l",
                      PINKY01_KEY_L: "pinky_01_l",
                      PINKY02_KEY_L: "pinky_02_l",
                      PINKY03_KEY_L: "pinky_03_l",
                      }
