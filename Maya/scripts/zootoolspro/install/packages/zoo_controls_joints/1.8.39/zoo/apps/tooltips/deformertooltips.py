from zoo.libs.maya.cmds.hotkeys import hotkeymisc


def deformerToolbox():
    """Tooltips for the Deformer Toolbox UI.

    :return: A dictionary with the tooltips for the toolbox, string names are keys.
    :rtype: dict(str)
    """
    ttDict = {}
    keyMap = hotkeymisc.getAssignCommandsMap()

    # ---------------------------------------------------------------------
    # CREATE
    # ---------------------------------------------------------------------
    # blendShape ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("createSphereMatch", keyMap)
    ttDict["blendShape"] = "xxx. \n\n" \
                           "Hotkey: {}".format(hk)
    # deltaMush ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("createSphereMatch", keyMap)
    ttDict["deltaMush"] = "xxx. \n\n" \
                          "Hotkey: {}".format(hk)
    # wireDeformer ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("createSphereMatch", keyMap)
    ttDict["wireDeformer"] = "xxx. \n\n" \
                             "Hotkey: {}".format(hk)
    # createCluster ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("createSphereMatch", keyMap)
    ttDict["createCluster"] = "xxx. \n\n" \
                              "Hotkey: {}".format(hk)
    # controlsOnCurve ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("createSphereMatch", keyMap)
    ttDict["controlsOnCurve"] = "xxx. \n\n" \
                                "Hotkey: {}".format(hk)
    # createLattice ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("createSphereMatch", keyMap)
    ttDict["createLattice"] = "xxx. \n\n" \
                              "Hotkey: {}".format(hk)
    # softModifier ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("createSphereMatch", keyMap)
    ttDict["softModifier"] = "xxx. \n\n" \
                             "Hotkey: {}".format(hk)
    # bendDeformer ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("createSphereMatch", keyMap)
    ttDict["bendDeformer"] = "xxx. \n\n" \
                             "Hotkey: {}".format(hk)
    # wrapDeformer ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("createSphereMatch", keyMap)
    ttDict["wrapDeformer"] = "xxx. \n\n" \
                             "Hotkey: {}".format(hk)
    # proximityWrap ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("createSphereMatch", keyMap)
    ttDict["proximityWrap"] = "xxx. \n\n" \
                              "Hotkey: {}".format(hk)
    # sculptDeformer ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("createSphereMatch", keyMap)
    ttDict["sculptDeformer"] = "xxx. \n\n" \
                               "Hotkey: {}".format(hk)
    # twistDeformer ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("createSphereMatch", keyMap)
    ttDict["twistDeformer"] = "xxx. \n\n" \
                              "Hotkey: {}".format(hk)
    # waveDeformer ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("createSphereMatch", keyMap)
    ttDict["waveDeformer"] = "xxx. \n\n" \
                             "Hotkey: {}".format(hk)
    # flareDeformer ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("createSphereMatch", keyMap)
    ttDict["flareDeformer"] = "xxx. \n\n" \
                              "Hotkey: {}".format(hk)
    # jiggleDeformer ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("createSphereMatch", keyMap)
    ttDict["jiggleDeformer"] = "xxx. \n\n" \
                               "Hotkey: {}".format(hk)
    # sineDeformer ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("createSphereMatch", keyMap)
    ttDict["sineDeformer"] = "xxx. \n\n" \
                             "Hotkey: {}".format(hk)
    return ttDict


def blendshapeToolbox():
    """Tooltips for the Deformer Toolbox UI.

    :return: A dictionary with the tooltips for the toolbox, string names are keys.
    :rtype: dict(str)
    """
    ttDict = {}
    keyMap = hotkeymisc.getAssignCommandsMap()

    # ---------------------------------------------------------------------
    # CREATE
    # ---------------------------------------------------------------------
    # createSphere ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("createSphereMatch", keyMap)
    ttDict["xxx"] = "xxx. \n\n" \
                    "Hotkey: {}".format(hk)
    return ttDict


def constraintsToolbox():
    """Tooltips for the Deformer Toolbox UI.

    :return: A dictionary with the tooltips for the toolbox, string names are keys.
    :rtype: dict(str)
    """
    ttDict = {}
    keyMap = hotkeymisc.getAssignCommandsMap()

    # ---------------------------------------------------------------------
    # CREATE
    # ---------------------------------------------------------------------
    # matchPosRot ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("MatchTransform", keyMap)
    mm = hotkeymisc.niceHotkeyFromName("Zoo_ConstraintMarkingMenu_Press", keyMap)
    ttDict["matchPosRot"] = "Matches the position and rotation of the first selected object/s \n" \
                            "to the last selected object. \n\n" \
                            "Hotkey: {} \n" \
                            "Marking Menu: {}".format(hk, mm)
    # matchPosition ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("MatchTranslation", keyMap)
    ttDict["matchPosition"] = "Matches the position of the first selected object/s \n" \
                              "to the last selected object. \n\n" \
                              "Hotkey: {} \n" \
                              "Marking Menu: {}".format(hk, mm)
    # matchRotation ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("MatchRotation", keyMap)
    ttDict["matchRotation"] = "Matches the rotation of the first selected object/s \n" \
                              "to the last selected object. \n\n" \
                              "Hotkey: {} \n" \
                              "Marking Menu: {}".format(hk, mm)
    # matchScale ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("MatchScaling", keyMap)
    ttDict["matchScale"] = "Matches the scale of the first selected object/s \n" \
                           "to the last selected object. \n\n" \
                           "Hotkey: {} \n" \
                           "Marking Menu: {}".format(hk, mm)
    # matchPivot ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("MatchPivots", keyMap)
    ttDict["matchPivot"] = "Matches the pivot of the first selected object/s \n" \
                           "to the last selected object. \n\n" \
                           "Hotkey: {} \n" \
                           "Marking Menu: {}".format(hk, mm)
    # maintainOffset ---------------------------------------------------------------
    ttDict["maintainOffset"] = ["Keeps the constrained object in its current position.",
                                "Snaps the constrained object relative to the master object."]
    # groupZeroObject ---------------------------------------------------------------
    ttDict["groupZeroObject"] = "Groups the selected object/s so that they are zeroed out. \n" \
                                "Includes scale freeze transform to 1.0."
    # markCenterPivot ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("zooCreateMarkCenterPivot_", keyMap)
    ttDict["markCenterPivot"] = "Marks the center of selection. \n" \
                                "Can be object or component selection. \n\n" \
                                "Hotkey: {}".format(hk)
    # parentConstraint ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("ParentConstraint", keyMap)
    ttDict["parentConstraint"] = "Parent constrains the last selected object to the " \
                                 "first selected object/s. \n\n" \
                                 "Hotkey: {} \n" \
                                 "Marking Menu: {}".format(hk, mm)
    # pointConstraint ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("PointConstraint", keyMap)
    ttDict["pointConstraint"] = "Translate constrains the last selected object to the " \
                                "first selected object/s. \n\n" \
                                "Hotkey: {} \n" \
                                "Marking Menu: {}".format(hk, mm)
    # orientConstraint ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("OrientConstraint", keyMap)
    ttDict["orientConstraint"] = "Orient constrains the last selected object to the " \
                                 "first selected object/s. \n\n" \
                                 "Hotkey: {} \n" \
                                 "Marking Menu: {}".format(hk, mm)
    # scaleConstraint ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("ScaleConstraint", keyMap)
    ttDict["scaleConstraint"] = "Scale constrains the last selected object to the " \
                                "first selected object/s. \n\n" \
                                "Hotkey: {} \n" \
                                "Marking Menu: {}".format(hk, mm)
    # aimConstraint ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("AimConstraint", keyMap)
    ttDict["aimConstraint"] = "Aim constrains the last selected object to aim at the  " \
                              "first selected object/s. \n\n" \
                              "Hotkey: {} \n" \
                              "Marking Menu: {}".format(hk, mm)
    # poleVectorConstraint ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("PoleVectorConstraint", keyMap)
    ttDict["poleVectorConstraint"] = "Sets up a Pole Vector, aims an Ik handle (Rotate Plane or Spring Solver) \n" \
                                     "towards an object.   \n\n" \
                                     "- Select an ik handle and then an object or control to act as " \
                                     "the Pole Vector.\n\n" \
                                     "Hotkey: {} \n" \
                                     "Marking Menu: {}".format(hk, mm)
    # pointOnPolyConstraint ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("PointOnPolyConstraint", keyMap)
    ttDict[
        "pointOnPolyConstraint"] = "Constrains the last selected object to the surface of the first " \
                                   "selected object.  \n" \
                                   "The last object will be position and orient constrained to the UV space of " \
                                   "the surface. \n\n" \
                                   "Hotkey: {} \n" \
                                   "Marking Menu: {}".format(hk, mm)
    # geometryConstraint ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("GeometryConstraint", keyMap)
    ttDict["geometryConstraint"] = "Constrains the last selected object to the surface of the first " \
                                   "selected object.  \n" \
                                   "The last object will be position constrained to the closest distance in " \
                                   "3d space to the surface. \n\n" \
                                   "Hotkey: {} \n" \
                                   "Marking Menu: {}".format(hk, mm)
    # geoNormalConstraint ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("createSphereMatch", keyMap)
    ttDict["geoNormalConstraint"] = "Constrains the last selected object's position/orientation to the surface \n" \
                                    "of the first selected object.  \n" \
                                    "The last object will be position snapped and oriented to the closest surface \n" \
                                    "in 3d space. \n\n" \
                                    "Marking Menu: {}".format(mm)
    # tangentConstraint ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("TangentConstraint", keyMap)
    ttDict["tangentConstraint"] = "Constrains the last selected object to a curve (first selected object).  \n" \
                                  "The last object will be position and orient constrained to the closest distance in " \
                                  "3d space to the curve. \n\n" \
                                  "Hotkey: {} \n" \
                                  "Marking Menu: {}".format(hk, mm)
    # normalConstraint ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("NormalConstraint", keyMap)
    ttDict["normalConstraint"] = "Constrains the last selected objects orientation to the surface of the first " \
                                 "selected object.  \n" \
                                 "The last object will be oriented to the closest surface in " \
                                 "3d space. \n\n" \
                                 "Hotkey: {} \n" \
                                 "Marking Menu: {}".format(hk, mm)
    # motionPath ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("AttachToPath", keyMap)
    ttDict["motionPath"] = "Creates a motion path setup.  \n" \
                           "The driven object can be animated along the distance of a curve 0.0-1.0. \n" \
                           "Select an object and a curve and run. \n\n" \
                           "Right-click for more options including the Motion Path Rig tool. \n\n" \
                           "Hotkey: {} \n" \
                           "Marking Menu: {}".format(hk, mm)
    # Multi Constraint (Match And Bake) ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("matchBakeAnim", keyMap)
    ttDict["multiConstraint"] = ("Opens the window for creating multiple constraints at once. \n"
                                 " - Opens the Match And Bake Anim Tool ")
    # select ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("createSphereMatch", keyMap)
    ttDict["select"] = "Select any constraints connected to a selected object."
    # delete ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("createSphereMatch", keyMap)
    ttDict["delete"] = "Delete any constraints connected to a selected object. \n\n" \
                       "Marking Menu: {}".format(mm)
    return ttDict
