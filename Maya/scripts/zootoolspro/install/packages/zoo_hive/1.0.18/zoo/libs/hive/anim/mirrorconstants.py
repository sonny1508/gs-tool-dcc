"""Constants for mirror/flipping Hive components and IDs

"""

# ---------------------------
# COMPONENT ANIMATION FLIP ATTRIBUTES
# ---------------------------

# KEYS
GOD_KEY = "godnodecomponent"
HEAD_KEY = "headcomponent"
SPINEIK_KEY = "spineIk"
SPINEFK_KEY = "spineFk"
JAW_KEY = "jaw"
FKCHAIN_KEY = "fkchain"
FINGER_KEY = "finger"
ARM_KEY = "armcomponent"
LEG_KEY = "legcomponent"
QUADLEG_KEY = "quadLeg"
VCHAIN_KEY = "vchaincomponent"
EYE_KEY = "eyecomponent"
AIM_KEY = "aimcomponent"

# FLIP ROTATIONS
FLIP_STANDARD_WORLD = ["translateX", "rotateY", "rotateZ"]
TZ_RY_RX = ["translateZ", "rotateY", "rotateX"]
TY_RZ_RX = ["translateY", "rotateZ", "rotateX"]
FLIP_STANDARD_FK = ["translateX", "translateY", "translateZ"]
FLIP_BENDY_WORLD = ["translateY"]
CENTER_FLIP_XUP = ["translateZ", "rotateX", "rotateY"]
TY = ["translateY"]
TX = ["translateX"]
RY_RX = ["rotateX", "rotateY"]
RY_RZ = ["rotateY", "rotateZ"]

# LEG (legcomponent) ----------------------
LEG_DICT = {"endik": FLIP_STANDARD_WORLD,
            "upVec": FLIP_STANDARD_WORLD,
            "controlPanel": [],
            "uprTwist": FLIP_STANDARD_FK,
            "lwrTwist": FLIP_STANDARD_FK,
            "toeTap_piv": [],
            "toeTip_piv": [],
            "outer_piv": [],
            "inner_piv": [],
            "heel_piv": [],
            "ballroll_piv": [],
            "lwrTwistOffset": [],
            "uprTwistOffset": [],
            "baseik": FLIP_STANDARD_WORLD,
            "endfk": FLIP_STANDARD_FK,
            "midfk": FLIP_STANDARD_FK,
            "ballfk": FLIP_STANDARD_FK,
            "uprfk": FLIP_STANDARD_FK,
            "bendy01": FLIP_BENDY_WORLD,
            "bendyMid00": FLIP_BENDY_WORLD,
            "bendyMid01": FLIP_BENDY_WORLD,
            "tangent00Out": FLIP_BENDY_WORLD,
            "tangent01In": FLIP_BENDY_WORLD,
            "tangent01Out": FLIP_BENDY_WORLD,
            "tangent02In": FLIP_BENDY_WORLD
            }

QUAD_LEG_DICT = {"endik": FLIP_STANDARD_WORLD,
                 "ankleik": FLIP_STANDARD_FK,
                 "upVec": FLIP_STANDARD_WORLD,
                 "upVecLwr": FLIP_STANDARD_WORLD,
                 "controlPanel": [],
                 "uprTwist": FLIP_STANDARD_FK,
                 "lwrTwist": FLIP_STANDARD_FK,
                 "ankleTwist": FLIP_STANDARD_FK,
                 "toeTap_piv": [],
                 "toeTip_piv": [],
                 "outer_piv": [],
                 "inner_piv": [],
                 "heel_piv": [],
                 "ballroll_piv": [],
                 "lwrTwistOffset": [],
                 "uprTwistOffset": [],
                 "ankleTwistOffset": [],
                 "baseik": FLIP_STANDARD_FK,
                 "endfk": FLIP_STANDARD_FK,
                 "midfk": FLIP_STANDARD_FK,
                 "ballfk": FLIP_STANDARD_FK,
                 "uprfk": FLIP_STANDARD_FK,
                 "bendy01": FLIP_BENDY_WORLD,
                 "bendy02": FLIP_BENDY_WORLD,
                 "bendyMid00": FLIP_BENDY_WORLD,
                 "bendyMid01": FLIP_BENDY_WORLD,
                 "bendyMid02": FLIP_BENDY_WORLD,
                 "tangent00Out": FLIP_BENDY_WORLD,
                 "tangent01In": FLIP_BENDY_WORLD,
                 "tangent01Out": FLIP_BENDY_WORLD,
                 "tangent02In": FLIP_BENDY_WORLD,
                 "tangent02Out": FLIP_BENDY_WORLD,
                 "tangent03In": FLIP_BENDY_WORLD
                 }

# ARM (armcomponent) ----------------------
ARM_DICT = {"endik": FLIP_STANDARD_FK,
            "upVec": FLIP_STANDARD_WORLD,
            "controlPanel": [],
            "uprTwist": FLIP_STANDARD_FK,
            "lwrTwist": FLIP_STANDARD_FK,
            "lwrTwistOffset": [],
            "uprTwistOffset": [],
            "baseik": FLIP_STANDARD_FK,
            "endfk": FLIP_STANDARD_FK,
            "midfk": FLIP_STANDARD_FK,
            "uprfk": FLIP_STANDARD_FK,
            "bendy01": FLIP_BENDY_WORLD,
            "bendyMid00": FLIP_BENDY_WORLD,
            "bendyMid01": FLIP_BENDY_WORLD,
            "tangent00Out": FLIP_BENDY_WORLD,
            "tangent01In": FLIP_BENDY_WORLD,
            "tangent01Out": FLIP_BENDY_WORLD,
            "tangent02In": FLIP_BENDY_WORLD
            }

# FKCHAIN (fkchain) ----------------
FK_DICT = {"fk": FLIP_STANDARD_FK,
           "controlPanel": []}

# FINGER (finger) ----------------------
FINGER_DICT = FK_DICT

# HEAD_DICT (headcomponent) ----------------------
HEAD_DICT = {"controlPanel": [],
             "neck": [],
             "head": []}

# VCHAIN (vchaincomponent) ----------------------
VCHAIN_DICT = {"controlPanel": [],
               "endik": FLIP_STANDARD_FK,
               "upVec": FLIP_STANDARD_WORLD,
               "uprTwist": FLIP_STANDARD_FK,
               "lwrTwist": FLIP_STANDARD_FK,
               "lwrTwistOffset": [],
               "uprTwistOffset": [],
               "baseik": FLIP_STANDARD_FK,
               "endfk": FLIP_STANDARD_FK,
               "midfk": FLIP_STANDARD_FK,
               "uprfk": FLIP_STANDARD_FK,
               "bendy01": FLIP_STANDARD_FK,
               "bendyMid00": FLIP_STANDARD_WORLD,
               "bendyMid01": FLIP_STANDARD_FK,
               "tangent00Out": FLIP_STANDARD_WORLD,
               "tangent01In": FLIP_STANDARD_WORLD,
               "tangent01Out": FLIP_STANDARD_FK,
               "tangent02In": FLIP_STANDARD_FK
               }

# SPINEFK (spineFk) ----------------------
SPINEFK_DICT = {"controlPanel": [],
                "hips": FLIP_STANDARD_WORLD,
                "cog": FLIP_STANDARD_WORLD,
                "gimbal": FLIP_STANDARD_WORLD,
                "fk": FLIP_STANDARD_FK}

# SPINEIK (spineIk) ----------------------
SPINEIK_DICT = {"controlPanel": [],
                "hips": FLIP_STANDARD_FK,
                "hipSwing": FLIP_STANDARD_FK,
                "cog": FLIP_STANDARD_FK,
                "cogGimbal": FLIP_STANDARD_FK,
                "fk": FLIP_STANDARD_FK,
                "ctrl": FLIP_STANDARD_FK,
                "tweaker00": FLIP_STANDARD_FK,
                "tweaker01": FLIP_STANDARD_FK,
                "tweaker02": FLIP_STANDARD_FK,
                "worldUpVec": []}

# JAW (jaw) ----------------------
JAW_DICT = {"controlPanel": [],
            "rotAll": FLIP_STANDARD_FK,
            "topLip": FLIP_STANDARD_FK,
            "botLip": FLIP_STANDARD_FK,
            "chin": FLIP_STANDARD_FK,
            "jaw": FLIP_STANDARD_FK}

# AIM (aimcomponent) ----------------------
AIM_DICT = {"controlPanel": [],
            "eye": FLIP_STANDARD_FK,
            "aim": ["rotateY", "rotateZ", "translateX", "translateY", "translateZ"]}

# EYE (jaw) ----------------------
EYE_DICT = {"eyeTarget": FLIP_STANDARD_WORLD,
            "eye": FLIP_STANDARD_WORLD,
            "controlPanel": ["rotOffsetY", "rotOffsetZ"],
            "eyeMain": FLIP_STANDARD_WORLD,
            "innerUprLidPrimary": [],
            "outerUprLidPrimary": [],
            "innerLwrLidPrimary": [],
            "outerLwrLidPrimary": [],
            "innerEnd": FLIP_STANDARD_FK,
            "innerStart": FLIP_STANDARD_FK,
            "innerUprLidCtrl": [],
            "innerLwrLidCtrl": [],
            "outerLwrLidCtrl": [],
            "outerUprLidCtrl": [],
            }

# ------------------- MAIN FLIP DICTIONARY ----------------------------
FLIP_ATTR_DICT = {LEG_KEY: LEG_DICT,
                  QUADLEG_KEY: QUAD_LEG_DICT,
                  FINGER_KEY: FINGER_DICT,
                  FKCHAIN_KEY: FK_DICT,
                  ARM_KEY: ARM_DICT,
                  HEAD_KEY: HEAD_DICT,
                  VCHAIN_KEY: VCHAIN_DICT,
                  AIM_KEY: AIM_DICT,
                  SPINEIK_KEY: SPINEIK_DICT,
                  SPINEFK_KEY: SPINEFK_DICT,
                  JAW_KEY: JAW_DICT,
                  EYE_KEY: EYE_DICT}

# -----------------------------------------------------------------------------------------------------------
# CENTER FLIP AXIS
# -----------------------------------------------------------------------------------------------------------

# GOD NODE ----------------------
GOD_CENTER_DICT = {"controlPanel": [],
                   "godnode": FLIP_STANDARD_WORLD,
                   "offset": FLIP_STANDARD_WORLD,
                   "rootMotion": FLIP_STANDARD_WORLD,
                   }

# SPLINE SPINE ----------------------
SPINEIK_CENTER_DICT = {"cog": FLIP_STANDARD_WORLD,
                       "cogGimbal": FLIP_STANDARD_WORLD,
                       "fk": FLIP_STANDARD_WORLD,
                       "ctrl": FLIP_STANDARD_WORLD,
                       "tweaker00": FLIP_STANDARD_WORLD,
                       "tweaker01": FLIP_STANDARD_WORLD,
                       "tweaker02": FLIP_STANDARD_WORLD,
                       "hipSwing": FLIP_STANDARD_WORLD,
                       "hips": FLIP_STANDARD_WORLD}

# HEAD ----------------------
HEAD_CENTER_DICT = {"neck": TZ_RY_RX,
                    "head": TZ_RY_RX}

JAW_CENTER_DICT = {"controlPanel": [],
                   "rotAll": FLIP_STANDARD_FK,
                   "topLip": FLIP_STANDARD_FK,
                   "botLip": FLIP_STANDARD_FK,
                   "chin": FLIP_STANDARD_FK,
                   "jaw": FLIP_STANDARD_FK}

SPINEFK_CENTER_DICT = {"controlPanel": [],
                       "hips": FLIP_STANDARD_WORLD,
                       "cog": FLIP_STANDARD_WORLD,
                       "gimbal": FLIP_STANDARD_WORLD,
                       "fk": FLIP_STANDARD_WORLD}

# TODO outer and inner piv is a special case
LEG_CENTER_DICT = {"endik": FLIP_STANDARD_WORLD,
                   "upVec": FLIP_STANDARD_WORLD,
                   "controlPanel": ["toeSide", "toeBank", "sideBank", "heelSideToSide", "ikRoll"],
                   "uprTwist": TY_RZ_RX,
                   "lwrTwist": TY_RZ_RX,
                   "toeTap_piv": RY_RX,
                   "toeTip_piv": RY_RX,
                   "outer_piv": [],
                   "inner_piv": [],
                   "heel_piv": RY_RZ,
                   "ballroll_piv": TZ_RY_RX,
                   "lwrTwistOffset": TY_RZ_RX,
                   "uprTwistOffset": TY_RZ_RX,
                   "baseik": TY,
                   "endfk": TZ_RY_RX,
                   "midfk": TY_RZ_RX,
                   "ballfk": TY_RZ_RX,
                   "uprfk": TY_RZ_RX,
                   "bendy01": TY,
                   "bendyMid00": TY,
                   "bendyMid01": TY,
                   "tangent00Out": TY,
                   "tangent01In": TY,
                   "tangent01Out": TY,
                   "tangent02In": TY
                   }

# TODO outer and inner piv is a special case
QUAD_LEG_CENTER_DICT = {"endik": FLIP_STANDARD_WORLD,
                        "ankleik": TZ_RY_RX,
                        "upVec": FLIP_STANDARD_WORLD,
                        "upVecLwr": FLIP_STANDARD_WORLD,
                        "controlPanel": ["toeSide", "toeBank", "sideBank", "heelSideToSide", "ikRoll"],
                        "uprTwist": TY_RZ_RX,
                        "lwrTwist": TY_RZ_RX,
                        "ankleTwist": TY_RZ_RX,
                        "toeTap_piv": TZ_RY_RX,
                        "toeTip_piv": TZ_RY_RX,
                        "outer_piv": [],
                        "inner_piv": [],
                        "heel_piv": RY_RZ,
                        "ballroll_piv": TZ_RY_RX,
                        "lwrTwistOffset": TY_RZ_RX,
                        "uprTwistOffset": TY_RZ_RX,
                        "ankleTwistOffset": TY_RZ_RX,
                        "baseik": TY,
                        "endfk": FLIP_STANDARD_FK,
                        "midfk": FLIP_STANDARD_FK,
                        "ballfk": FLIP_STANDARD_FK,
                        "uprfk": FLIP_STANDARD_FK,
                        "bendy01": TX,
                        "bendy02": TX,
                        "bendyMid00": FLIP_BENDY_WORLD,
                        "bendyMid01": FLIP_BENDY_WORLD,
                        "bendyMid02": FLIP_BENDY_WORLD,
                        "tangent00Out": FLIP_BENDY_WORLD,
                        "tangent01In": FLIP_BENDY_WORLD,
                        "tangent01Out": FLIP_BENDY_WORLD,
                        "tangent02In": FLIP_BENDY_WORLD,
                        "tangent02Out": FLIP_BENDY_WORLD,
                        "tangent03In": FLIP_BENDY_WORLD
                        }

FK_CENTER_DICT = {"fk": FLIP_STANDARD_WORLD,
                  "controlPanel": []}  # FK Varies
FINGER_CENTER_DICT = FK_CENTER_DICT  # finger will vary

# TODO ARM, VCHAIN, EYE, AIM
ARM_CENTER_DICT = {"endik": FLIP_STANDARD_FK,
                   "upVec": FLIP_STANDARD_WORLD,
                   "controlPanel": ["ikRoll"],
                   "uprTwist": FLIP_STANDARD_FK,
                   "lwrTwist": FLIP_STANDARD_FK,
                   "lwrTwistOffset": [],
                   "uprTwistOffset": [],
                   "baseik": FLIP_STANDARD_FK,
                   "endfk": FLIP_STANDARD_FK,
                   "midfk": FLIP_STANDARD_FK,
                   "uprfk": FLIP_STANDARD_FK,
                   "bendy01": FLIP_BENDY_WORLD,
                   "bendyMid00": FLIP_BENDY_WORLD,
                   "bendyMid01": FLIP_BENDY_WORLD,
                   "tangent00Out": FLIP_BENDY_WORLD,
                   "tangent01In": FLIP_BENDY_WORLD,
                   "tangent01Out": FLIP_BENDY_WORLD,
                   "tangent02In": FLIP_BENDY_WORLD
                   }

# TODO
VCHAIN_CENTER_DICT = {"controlPanel": ["ikRoll"],
                      "endik": FLIP_STANDARD_WORLD,
                      "upVec": FLIP_STANDARD_WORLD,
                      "uprTwist": TY_RZ_RX,
                      "lwrTwist": TY_RZ_RX,
                      "lwrTwistOffset": TY_RZ_RX,
                      "uprTwistOffset": TY_RZ_RX,
                      "baseik": FLIP_STANDARD_FK,
                      "endfk": FLIP_STANDARD_FK,
                      "midfk": FLIP_STANDARD_FK,
                      "uprfk": FLIP_STANDARD_FK,
                      "bendy01": FLIP_STANDARD_FK,
                      "bendyMid00": FLIP_STANDARD_WORLD,
                      "bendyMid01": FLIP_STANDARD_FK,
                      "tangent00Out": FLIP_STANDARD_WORLD,
                      "tangent01In": FLIP_STANDARD_WORLD,
                      "tangent01Out": FLIP_STANDARD_FK,
                      "tangent02In": FLIP_STANDARD_FK
                      }

# AIM (aimcomponent) ----------------------
AIM_CENTER_DICT = {"controlPanel": [],
                   "eye": TZ_RY_RX,
                   "aim": TZ_RY_RX}

# EYE (jaw) ----------------------
EYE_AIM_DICT = {"eyeTarget": FLIP_STANDARD_WORLD,
                "eye": FLIP_STANDARD_WORLD,
                "controlPanel": ["rotOffsetY", "rotOffsetZ"],
                "eyeMain": FLIP_STANDARD_WORLD,
                "innerUprLidPrimary": FLIP_STANDARD_WORLD,
                "outerUprLidPrimary": FLIP_STANDARD_WORLD,
                "innerLwrLidPrimary": FLIP_STANDARD_WORLD,
                "outerLwrLidPrimary": FLIP_STANDARD_WORLD,
                "innerEnd": FLIP_STANDARD_FK,
                "innerStart": FLIP_STANDARD_FK,
                "innerUprLidCtrl": [],
                "innerLwrLidCtrl": [],
                "outerLwrLidCtrl": [],
                "outerUprLidCtrl": [],
                }

CENTER_FLIP_ATTR_DICT = {GOD_KEY: GOD_CENTER_DICT,
                         HEAD_KEY: HEAD_CENTER_DICT,
                         SPINEIK_KEY: SPINEIK_CENTER_DICT,
                         SPINEFK_KEY: SPINEFK_CENTER_DICT,
                         JAW_KEY: JAW_CENTER_DICT,
                         FKCHAIN_KEY: FK_CENTER_DICT,
                         FINGER_KEY: FINGER_CENTER_DICT,
                         ARM_KEY: ARM_CENTER_DICT,
                         LEG_KEY: LEG_CENTER_DICT,
                         QUADLEG_KEY: QUAD_LEG_CENTER_DICT,
                         VCHAIN_KEY: ARM_CENTER_DICT,
                         AIM_KEY: AIM_CENTER_DICT,
                         EYE_KEY: EYE_AIM_DICT}
