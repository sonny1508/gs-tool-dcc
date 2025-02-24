from zoo.libs.maya.cmds.hotkeys import hotkeymisc

MM_PRIM = "MarkingMenu: shift+right-click (nothing selected)  "
MM_VERT = "MarkingMenu: shift+right-click (Vertex selected)  "
MM_FACE = "MarkingMenu: shift+right-click (Face selected)  "
MM_EDGE = "MarkingMenu: shift+right-click (Edge selected)  "
MM_EDGE_FACE = "MarkingMenu: shift+right-click (Edge/Face selected)  "
MM_VERT_EDGE = "MarkingMenu: shift+right-click (Vert/Edge selected)  "
MM_VERT_EDGE_FACE = "MarkingMenu: shift+right-click (Vert/Edge/Face selected)  "
MM_OBJ_EDGE_FACE_VERT = "MarkingMenu: shift+right-click (Obj/Edge/Face/Vert selected)  "
MM_OBJ_FACE = "MarkingMenu: shift+right-click (Poly Obj/Face selected)  "
MM_OBJ_EDGE = "MarkingMenu: shift+right-click (Poly Obj/Edge selected)  "
MM_OBJ = "MarkingMenu: shift+right-click (Poly Object selected)  "

MM_SCULPT = "MarkingMenu: shift+right-click (While In Sculpt Mode)  "


def objectToolbox():
    """Tooltips for the Object Toolbox UI.

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
    ttDict["createSphere"] = "Creates a Polygon Sphere. \n" \
                             "Matches to the current selection, if there is a selection. \n\n" \
                             "Hotkey: {} \n{}".format(hk, MM_PRIM)
    # createCube ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("createCubeMatch", keyMap)
    ttDict["createCube"] = "Creates a Polygon Cube. \n" \
                           "Matches to the current selection, if there is a selection. \n\n" \
                           "Hotkey: {} \n{}".format(hk, MM_PRIM)
    # createCylinder ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("createCylinderMatch", keyMap)
    ttDict["createCylinder"] = "Creates a Polygon Cylinder. \n" \
                               "Matches to the current selection, if there is a selection. \n\n" \
                               "Hotkey: {} \n{}".format(hk, MM_PRIM)
    # createPlane ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("createPlaneMatch", keyMap)
    ttDict["createPlane"] = "Creates a Polygon Plane. \n" \
                            "Matches to the current selection, if there is a selection. \n\n" \
                            "Hotkey: {} \n{}".format(hk, MM_PRIM)
    # createTorus ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("createTorusMatch", keyMap)
    ttDict["createTorus"] = "Creates a Polygon Torus. \n" \
                            "Matches to the current selection, if there is a selection. \n\n" \
                            "Hotkey: {} \n{}".format(hk, MM_PRIM)
    # createCone ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("createConeMatch", keyMap)
    ttDict["createCone"] = "Creates a Polygon Cone. \n" \
                           "Matches to the current selection, if there is a selection. \n\n" \
                           "Hotkey: {} \n{}".format(hk, MM_PRIM)
    # createPolygon ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("CreatePolygonTool", keyMap)
    ttDict["createPolygon"] = "Opens the Create Polygon Tool. \n" \
                              "Click multiple times on the ground to create a new polygon. \n\n" \
                              "Hotkey: {} \n{}".format(hk, MM_PRIM)
    # createSweepMesh ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("createSweepMesh", keyMap)
    ttDict["createSweepMesh"] = "Creates a tube along a curve that can be edited in the Attribute Editor. \n" \
                                "Select an existing curve, or nothing, and run. \n" \
                                "Hotkey: {}".format(hk)
    # createType ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("createPolygonType", keyMap)
    ttDict["createType"] = "Creates Polygon Type (Text). \n" \
                           "Open the Attribute Editor to edit text. \n\n" \
                           "Hotkey: {} \n{}".format(hk, MM_PRIM)

    # ---------------------------------------------------------------------
    # MODIFY FUNCTIONS
    # ---------------------------------------------------------------------
    # Duplicate ---------------------------------------------------------------
    ttDict["duplicate"] = "Duplicate copy/pastes the selected object/s to create new objects. \n\n" \
                          "Right-click for more options:  \n" \
                          " - Duplicate Node Graph: Duplicates all incoming connections, ie animation and more. \n" \
                          " - Duplicate Share Connections: Duplicates objects and shares the incoming connections. \n" \
                          " - Duplicate Options: Opens Maya's duplicate options window.  \n" \
                          " - Duplicate Faces: Duplicates the selected faces to create a new object.  \n\n" \
                          "Hotkey: ctrl+d"  # Note: Auto hotkey does not work, Maya doesn't display either
    # DuplicateOffset ---------------------------------------------------------------
    ttDict["duplicateOffset"] = "Duplicates with transform. \n" \
                                "Duplicates the selected objects and keeps the same \n" \
                                "offset spacing (move/rotation) as previous duplicates. \n\n" \
                                "Hotkey: shift+d"  # Note: Auto hotkey does not work, Maya doesn't display either
    # Instance ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("instance", keyMap)
    ttDict["instance"] = "Instances the selected object/s and keeps identical shape nodes. \n\n" \
                         "Changes made on one mesh will also propagate to the instanced objects. \n\n" \
                         "Hotkey: {}".format(hk)
    # Uninstance ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("zooUnInstance", keyMap)
    ttDict["uninstance"] = "Un-instances (removes/bakes) the selected objects and/or their parent groups. \n" \
                           "This function also un-instances `Zoo Mirror` objects. \n\n" \
                           "Hotkey: {}".format(hk)
    # Boolean ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("PolygonBooleanDifference", keyMap)
    if hk == "None":  # might be the zoo marking menu
        hk = hotkeymisc.niceHotkeyFromName("zooBevelBoolMarkingMenuPress", keyMap)
        if hk:
            hk = "{} (boolean in the marking menu)".format(hk)
    ttDict["boolean"] = "Join, intersect or difference multiple objects together. \n\n" \
                        "Default (A-B) leaves the first selected object and subtracts other selected objects. \n" \
                        "Use the `Attribute Editor` to manage/change boolean options. \n\n" \
                        "Right-click for more options.  Some options are not available in early Maya versions.  \n\n" \
                        "Hotkey: {}  \n{}".format(hk, MM_OBJ)
    # Combine ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("CombinePolygons", keyMap)
    ttDict["combine"] = "Combines the selected polygon objects to form one new object. \n\n" \
                        "Shells remain and are not booleaned. \n" \
                        "The first selected object's name is kept. \n\n" \
                        "Hotkey: {}  \n{}".format(hk, MM_OBJ)
    # Separate ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("extractFaceToObjectMode", keyMap)
    ttDict["separate"] = "Separates selected objects so each shell (connected mesh) becomes its own object. \n" \
                         "Note: Extract preforms identical functionality. Below is the Extract hotkey. \n\n" \
                         "Hotkey: {}  \n{}".format(hk, MM_FACE)
    # Extract ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("extractFaceToObjectMode", keyMap)
    ttDict["extract"] = "Extracts the selected object so that the selected faces becomes another object. \n\n" \
                        "Note: In object mode, extract will separate shells into individual objects. \n\n" \
                        "Hotkey: {}  \n{}".format(hk, MM_FACE)
    # parent ---------------------------------------------------------------
    hk = "p"  # Note: Auto hotkey does not work, Maya doesn't display either
    ttDict["parent"] = "Parent \n" \
                       "Parents the first objects to the last in the selection. \n\n" \
                       " - Select multiple objects with the parent last. \n" \
                       " - Run the tool. \n\n" \
                       "Right-Click for `Group` and `Ungroup`. \n\n" \
                       "Hotkey: {}".format(hk)
    # unparent ---------------------------------------------------------------
    hk = "shift+P"  # Note: Auto hotkey does not work, Maya doesn't display either
    ttDict["unparent"] = "Unparents\n" \
                         "Unparents the selected objects and places them in the world root location. \n\n" \
                         "Hotkey: {}".format(hk)
    # group ---------------------------------------------------------------
    hk = "ctrl+g"  # Note: Auto hotkey does not work, Maya doesn't display either
    ttDict["group"] = "Group \n" \
                      "Groups the selected objects and creates a new `group`. \n" \
                      "If nothing is selected creates a `null` or an empty `transform node`. \n\n" \
                      " - Select multiple objects. \n" \
                      " - Run the tool. \n\n" \
                      "Hotkey: {}".format(hk)
    # ungroup ---------------------------------------------------------------
    hk = "None"  # Note: Auto hotkey does not work, Maya doesn't display either
    ttDict["ungroup"] = "Ungroup \n" \
                        "Unparents the selected objects and deletes the group. \n\n" \
                        " - Select a group or groups and run. \n\n" \
                        "Hotkey: {}".format(hk)

    # ---------------------------------------------------------------------
    # OBJECT FUNCTIONS
    # ---------------------------------------------------------------------
    # ToggleEditPivot ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("EnterEditModePress", keyMap)
    ttDict["toggleEditPivot"] = "Toggles `Edit Pivot` mode.  Move/rotate the pivot of any object. \n\n" \
                                "Right-Click for more options: \n" \
                                " - Bake Pivot: Bakes the pivot and removes temporary offsets. \n\n" \
                                "Also right-click on the manipulator handle for more pivot options. \n\n" \
                                "Hotkey: {}".format(hk)
    # CenterPivot ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("CenterPivot", keyMap)
    ttDict["centerPivot"] = "Moves (and bakes) the pivot to be at the center of an object. \n\n" \
                            "Right-Click for more options: \n" \
                            " - Match Pivot: Matches the pivot to the second selected object. \n\n" \
                            "Hotkey: {}".format(hk)
    # Freeze ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("FreezeTransformations", keyMap)
    if hk == "None":  # might be the zoo marking menu
        hk = hotkeymisc.niceHotkeyFromName("zooFreezeTransformMarkingMenuPress", keyMap)
        if hk:
            hk = "{} (more options in marking menu)".format(hk)
    Freeze = "Freeze the selected object's transformations: \n" \
             " - Translation and Rotation become 0.0 \n" \
             " - Scale becomes 1.0. \n" \
             "Objects remain in the same position. \n\n" \
             "Right-Click for more options: \n" \
             " - Freeze Translation: Translate only \n" \
             " - Freeze Rotation: Rotation only \n" \
             " - Freeze Scale: Scale only \n" \
             " - Un-Freeze: Attempts to reverse the Freeze function. \n\n" \
             "Hotkey: {}".format(hk)
    ttDict["Freeze"] = Freeze
    # deleteHistory ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("DeleteHistory", keyMap)
    if hk == "None":  # might be the zoo marking menu
        hk = hotkeymisc.niceHotkeyFromName("zooDeleteHistoryMarkingMenuPress", keyMap)
        if hk:
            hk = "{} (more options in marking menu)".format(hk)

    deleteHistory = "Delete's all node connection history on the selected objects so that the mesh has \n" \
                    "no incoming connections. \n\n" \
                    "Right-Click for more options:  \n" \
                    " - Non-Deformer History: Removes mesh edits, leaves skinning and deformers. \n\n" \
                    "Hotkey: {}".format(hk)
    ttDict["deleteHistory"] = deleteHistory
    # freezeMatrix ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("freezeMatrix", keyMap)
    if hk == "None":  # might be the zoo marking menu
        hk = hotkeymisc.niceHotkeyFromName("zooFreezeTransformMarkingMenuPress", keyMap)
        if hk:
            hk = "{} (in the marking menu)".format(hk)
    freezeMatrix = "Modeler Freeze Matrix, freezes the selected object/s translate/rotate/scale attributes \n" \
                   "transferring offsets to the object's `Offset Matrix` attributes (Maya 2020+). \n\n" \
                   "Scale attributes will be reset and cannot be unfrozen.\n\n" \
                   "Right-Click for more options:  \n" \
                   " - Freeze Maintain Scale Space: Scale attrs are not reset, can cause non uniform scale issues. \n\n" \
                   "Hotkey: {}".format(hk)
    ttDict["freezeMatrix"] = freezeMatrix
    # unfreezeMatrix ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("unfreezeMatrix", keyMap)
    if hk == "None":  # might be the zoo marking menu
        hk = hotkeymisc.niceHotkeyFromName("zooFreezeTransformMarkingMenuPress", keyMap)
        if hk:
            hk = "{} (in the marking menu)".format(hk)
    unfreezeMatrix = "Unfreezes Offset Matrix changes. \n" \
                     "Returns changes made by Freeze Matrix. \n\n" \
                     "Hotkey: {}".format(hk)
    ttDict["unfreezeMatrix"] = unfreezeMatrix
    return ttDict


def modelingToolbox():
    """Tooltips for the Modeling Toolbox UI.

    :return: A dictionary with the tooltips for the toolbox, string names are keys.
    :rtype: dict(str)
    """
    toolTipDict = {}
    keyMap = hotkeymisc.getAssignCommandsMap()
    # ---------------------------------------------------------------------
    # CREATE ADD FACES
    # ---------------------------------------------------------------------
    # extrude ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("PolyExtrude", keyMap)
    extrude = "Extrude Tool  \n" \
              "Creates new polygons by pulling out a face/s. \n\n" \
              " - Select an object/faces/edges/vertices to extrude. \n" \
              " - Run the tool and adjust settings in the tool popup. \n\n" \
              "To extrude a long a curve: \n" \
              " - Create a curve starting at the face/s you wish to extrude. \n" \
              " - Select the faces with: `right-click > face` \n" \
              " - Shift-select the curve. \n" \
              " - Run the tool and adjust `divisions` and other settings such as `taper`. \n\n" \
              "Right-Click to create a Nurbs Curve. \n\n" \
              "Hotkey: {}  \nHotkey: Shift-drag a face \n{}".format(hk, MM_OBJ_EDGE_FACE_VERT)
    toolTipDict["extrude"] = extrude
    # bevel ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("BevelPolygon", keyMap)
    if hk == "None":  # might be the zoo marking menu
        hk = hotkeymisc.niceHotkeyFromName("zooBevelBoolMarkingMenuPress", keyMap)
        if hk:
            hk = "{} (more options in marking menu)".format(hk)
    bevel = "Bevel Tool \n" \
            "Creates a bevel effect along edges. \n\n" \
            " - Select object/faces/edges or vertices. \n" \
            " - Run the tool \n" \
            " - Adjust settings in the popup window. \n\n" \
            "Right-click to turn chamfer off, or add round edges. \n\n" \
            "Hotkey: {}  \n{}".format(hk, MM_EDGE_FACE)
    toolTipDict["bevel"] = bevel
    # quadDraw ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("dR_quadDrawTool", keyMap)
    quadDraw = "Quad Draw  \n" \
               "Draw topology onto a live mesh.  Mesh must be live. \n" \
               "Used for manual retopology and more. \n\n" \
               "Tool Options: \n" \
               " - Drop Dots = left click on a `live mesh` to place dots. \n" \
               " - Fill Create = hold shift-left-click to fill dots or other and make a quad. \n" \
               " - Tweak = click-drag moves dots or vertices. \n" \
               " - Relax = shift click drag to relax vertices. Start inside or border edge. \n" \
               " - Extend Edge = tab drag out/extrude an edge. \n" \
               " - Delete = ctrl-shift-click. \n" \
               " - Strips = tab + click-drag to drag out polygon strips. \n" \
               " - Edge Loop Split = ctrl-click on an edge to edge loop split. \n" \
               " - Center Loop Split = ctrl-middle-click edge to center edge loop split. \n" \
               " - Extend Border = tab middle drag out/extrude a border. \n\n" \
               "Right-Click to make a mesh live. \n\n" \
               "Hotkey: {}  \n{}".format(hk, MM_OBJ)
    toolTipDict["quadDraw"] = quadDraw
    # bridge ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("BridgeOrFill", keyMap)
    bridge = "Bridge Tool  \n" \
             "Draws new quad polygons between selected edges. \n\n" \
             " - Select edges/faces on two sides with a matching number. \n" \
             " - Run the tool. \n" \
             " - Adjust settings in the tool popup window. \n\n" \
             "Hotkey: {}  \n{}".format(hk, MM_EDGE_FACE)
    toolTipDict["bridge"] = bridge
    # fillHole ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("BridgeOrFill", keyMap)
    fillHole = "Fill Hole Tool  \n" \
               "Creates a new polygon to fill a hole in a mesh. \n\n" \
               " - Select an edge of a hole left empty with surrounding polygons. \n" \
               " - Run the tool to fill the hole. \n\n" \
               "Hotkey: {}  \n{}".format(hk, MM_EDGE)
    toolTipDict["fillHole"] = fillHole
    # append ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("poly_appendAndComplete", keyMap)
    append = "Append Tool \n" \
             "Creates a new polygon from border edges. \n\n" \
             " - Run the tool. \n" \
             " - Click on an open border edge, and follow the triangle arrows. \n" \
             " - Hit enter to finish the new polygon. \n\n" \
             "Hotkey: {}  \n{}".format(hk, MM_OBJ)
    toolTipDict["append"] = append
    # wedge ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("WedgePolygon", keyMap)
    wedge = "Wedge Tool \n" \
            "Creates a radial/angle sweep from faces, useful for pipes and other operations.\n\n" \
            " - Enter multi-component mode (right-click on the mesh > multi) \n" \
            " - Select face/s and an edge to pivot off. \n" \
            " - Run the tool. A new wedge will be created. \n\n" \
            "Advanced functionality can use two objects and create a more complex pipe wedges. \n" \
            "See the tool's help `?` for more information. \n\n" \
            "Hotkey: {}  \n{}".format(hk, MM_FACE)
    toolTipDict["wedge"] = wedge
    # chamferVertex ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("BevelPolygon", keyMap)
    chamferVertex = "Chamfer A Vertex \n" \
                    "Chamfers vertices adding a flat polygon where each vertex was. \n\n" \
                    " - Select vertices and run.  \n\n" \
                    "Note:  The Bevel tool functionality is identical, use its hotkey.\n\n" \
                    "Hotkey: {}  \n{}".format(hk, MM_VERT)
    toolTipDict["chamferVertex"] = chamferVertex
    # ---------------------------------------------------------------------
    # CUT
    # ---------------------------------------------------------------------
    # multiCut ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("dR_multiCutTool", keyMap)
    multiCut = "Multi Cut Tool \n" \
               "Multi-purpose cut tool that also slices and edge-loop splits. \n\n" \
               "Tool Options:\n" \
               " - Tweak = Click to drag a point along an edge. \n" \
               " - Edge Loop = Ctrl drag an edge. \n" \
               " - Center Loop = Ctrl middle drag edge to center the edge-loop. \n" \
               " - Slice = Click-drag off object through the object to slice. \n" \
               " - Slice Inside = Middle click drag inside an object to slice it. \n" \
               " - Undo = Delete \n" \
               " - Snap = Hold shift to snap in percentages. \n" \
               " - Perpendicular = Ctrl shift click to cut perpendicular. \n" \
               " - Commit/Finish = Enter or right-click\n\n" \
               "Hotkey: {}  \n{}".format(hk, MM_OBJ_EDGE_FACE_VERT)
    toolTipDict["multiCut"] = multiCut
    # edgeFlow ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("PolyEditEdgeFlow", keyMap)
    edgeFlow = "Edge Flow Tool \n" \
               "The tool will attempt to adjust the edge-loop to flow with the surrounding edges.\n\n" \
               " - Select an edge-loop or an edge. \n" \
               " - Run the tool. \n" \
               " - Adjust the amount of flow with the tool popup window. \n\n" \
               "Hotkey: {}  \n{}".format(hk, MM_EDGE)
    toolTipDict["edgeFlow"] = edgeFlow
    # connect ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("dR_connectTool", keyMap)
    connect = "Connect Tool (Toolkit) \n" \
              "Adds multiple edge-loop splits along a selected edge. \n\n" \
              " - Select an edge and run the tool. \n" \
              " - Middle-click drag to interactively add more corresponding edge-loops.\n" \
              " - Finish the tool with enter. \n\n" \
              "Hotkey: {}  \n{}".format(hk, MM_OBJ_EDGE_FACE_VERT)
    toolTipDict["connect"] = connect
    # edgeLoopToFrom ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("zooPolyEdgeLoopSplitAutoOff", keyMap)
    edgeLoopToFrom = "Edge Loop (To/From Edges) \n" \
                     "Creates a limited edge-loop split from one edge to another. \n\n" \
                     " - Run the tool. \n" \
                     " - Select a start and end point on an edge loop.\n" \
                     " - Finish the too with enter. \n\n" \
                     "Hotkey: {}".format(hk)
    toolTipDict["edgeLoopToFrom"] = edgeLoopToFrom
    # offsetEdgeLoop ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("DuplicateEdges", keyMap)
    offsetEdgeLoop = "Offset Edge Loop Tool ( Duplicate Edges ) \n" \
                     "Creates a new edge-loop split either side of an existing edge-loop. \n\n" \
                     " - Run the tool. \n" \
                     " - Click and hold on an edge to select the edge loop. \n" \
                     " - Drag the mouse to adjust the depth of the two edge loops either side.\n\n" \
                     "Hotkey: {}  \n{}".format(hk, MM_EDGE)
    toolTipDict["offsetEdgeLoop"] = offsetEdgeLoop
    # poke ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("PokePolygon", keyMap)
    poke = "Poke Tool \n" \
           "Creates a new vertex in the center of a polygon face. \n\n" \
           " - Select a face. \n" \
           " - Run the tool to create a center vertex. \n" \
           " - All vertices of the face border will connect to the new vertex. \n\n" \
           "Hotkey: {}  \n{}".format(hk, MM_FACE)
    toolTipDict["poke"] = poke
    # ---------------------------------------------------------------------
    # MERGE REMOVE
    # ---------------------------------------------------------------------
    # mergeCenter ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("MergeToCenter", keyMap)
    mergeCenter = "Merge To Center Tool \n" \
                  "Merges vertices to a center point.\n\n" \
                  " - Select faces/edges or vertices and run. \n\n" \
                  "Hotkey: {}  \n{}".format(hk, MM_VERT_EDGE_FACE)
    toolTipDict["mergeCenter"] = mergeCenter
    # mergeToVert ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("MergeVertexTool", keyMap)
    mergeToVert = "Merge To Vertex Tool \n" \
                  "Snap and merge a vertex to another vertex. \n\n" \
                  " - Run the tool. \n" \
                  " - Click and drag one vertex to another.  \n\n" \
                  "The vertices will be merged. \n\n" \
                  "Hotkey: {}  \n{}".format(hk, MM_OBJ_EDGE_FACE_VERT)
    toolTipDict["mergeToVert"] = mergeToVert
    # mergeTolerance ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("PolyMerge", keyMap)
    mergeTolerance = "Merge Tolerance Tool \n" \
                     "Merges the selected vertices that are closer than a `distance threshold`. \n\n" \
                     " - Select vertices/edges/faces. \n" \
                     " - Run the tool. \n" \
                     " - Tweak the merge `distance threshold` setting (cms).\n\n" \
                     "Hotkey: {}  \n{}".format(hk, MM_VERT_EDGE)
    toolTipDict["mergeTolerance"] = mergeTolerance
    # collapseEdgeRing ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("PolygonCollapse", keyMap)
    collapseEdgeRing = "Collapse Edge Ring Tool \n" \
                       "Collapses/merges a selected edge ring (not loop) to a center point. \n\n" \
                       " - Select an edge ring.  Select one edge and shift-double-click an opposite edge. \n" \
                       " - Run the tool. \n\n" \
                       "Hotkey: {}  \n{}".format(hk, MM_EDGE)
    toolTipDict["collapseEdgeRing"] = collapseEdgeRing
    # deleteEdge ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("DeletePolyElements", keyMap)
    deleteEdge = "Delete Edge Tool \n" \
                 "Deletes an edge, and removes the interior vertices that remain if using the delete key. \n\n" \
                 " - Select edges and run. \n\n" \
                 "Hotkey: {}  \n{}".format(hk, MM_EDGE)
    toolTipDict["deleteEdge"] = deleteEdge
    # makeHole ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("MakeHoleTool", keyMap)
    makeHole = "Make Hole Tool \n" \
               "Precision tool for cutting holes in polygons. \n" \
               "This tool has many `merge mode` options, see the tool's help `?` for more information. \n\n" \
               " - Combine a face with a shape of the desired hole. \n" \
               " - Select the object. \n" \
               " - Run the tool. \n" \
               " - Select the shaped-face first and then the face where the hole should appear. \n" \
               " - Hit enter to create the hole. \n\n" \
               "Hotkey: {}".format(hk)
    toolTipDict["makeHole"] = makeHole
    # ---------------------------------------------------------------------
    # MISC
    # ---------------------------------------------------------------------
    # circularize ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("PolyCircularize", keyMap)
    circularize = "Circularize \n" \
                  "Reshapes the selection into a circle. \n\n" \
                  " - Select faces/edges or vertices and run. \n\n" \
                  "Hotkey: {}  \n{}".format(hk, MM_VERT_EDGE_FACE)
    toolTipDict["circularize"] = circularize
    # spinEdge ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("PolySpinEdgeBackward", keyMap)
    hk2 = hotkeymisc.niceHotkeyFromName("PolySpinEdgeForward", keyMap)
    spinEdge = "Spin Edge Tool \n" \
               "Spins an edge so that it connects to other vertices. \n\n" \
               " - Select an edge and run.  \n\n" \
               "Hotkey Spin Backwards: {}  \n" \
               "Hotkey Spin Forwards: {} \n{}".format(hk, hk2, MM_EDGE)
    toolTipDict["spinEdge"] = spinEdge
    # conform ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("ConformPolygon", keyMap)
    conform = "Conform Polygon Snap \n" \
              "Snaps the current selection to a live mesh. \n\n" \
              " - Select object/faces/edges or vertices and run.  \n\n" \
              "Right-Click to make a mesh live. \n\n" \
              "Hotkey: {}".format(hk)
    toolTipDict["conform"] = conform
    # averageVertices ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("AverageVertex", keyMap)
    averageVertices = "Average Vertices Tool \n" \
                      "Smooths vertices to match the distance between each vertex. \n\n" \
                      " - Select object/faces/edges or vertices and run. \n" \
                      " - Adjust the strength `iterations` with the popup window. \n\n" \
                      "Hotkey: {}  \n{}".format(hk, MM_VERT)
    toolTipDict["averageVertices"] = averageVertices
    return toolTipDict


def topologyAndNormalsToolbox():
    """Tooltips for the Topology And Normals Toolbox UI.

    :return: A dictionary with the tooltips for the toolbox, string names are keys.
    :rtype: dict(str)
    """
    toolTipDict = {}
    keyMap = hotkeymisc.getAssignCommandsMap()
    # ---------------------------------------------------------------------
    # TOPOLOGY
    # ---------------------------------------------------------------------
    # subDSmoothOff ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("zooSubDMarkingMenuPress", keyMap)
    hkLowQualityDisplay = hotkeymisc.niceHotkeyFromName("LowQualityDisplay", keyMap)
    subDSmoothOff = "Smooth Mesh Preview Off\n" \
                    "Turns off the smooth preview for polygon objects (Sub Division Surface) \n\n" \
                    " - Select a polygon object and run. \n\n" \
                    "Hotkey Toggle & Marking Menu: {}  \n" \
                    "Hotkey: {}".format(hk, hkLowQualityDisplay)
    toolTipDict["subDSmoothOff"] = subDSmoothOff
    # subDSmoothOn ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("zooSubDMarkingMenuPress", keyMap)
    hkHighQualityDisplay = hotkeymisc.niceHotkeyFromName("HighQualityDisplay", keyMap)
    subDSmoothOn = "Smooth Mesh Preview On\n" \
                   "Turns on the smooth preview for polygon objects (Sub Division Surface) \n\n" \
                   " - Select a polygon object and run. \n\n" \
                   "Right-click for more options. \n" \
                   "Hotkey Toggle & Marking Menu: {}  \n" \
                   "Hotkey: {}".format(hk, hkHighQualityDisplay)
    toolTipDict["subDSmoothOn"] = subDSmoothOn
    # polySmooth ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("smoothPolyObject", keyMap)
    polySmooth = "Smooth (Poly Smooth) Tool\n" \
                 "Subdivides a polygon mesh and smooths the result. \n" \
                 "Similar to a baked version of Sub Division Surfaces. \n\n" \
                 " - Select a polygon object and run. Adjust divisions. \n\n" \
                 "Each extra division adds four times more faces. \n\n" \
                 "Hotkey: {}  \n{}".format(hk, MM_FACE)
    toolTipDict["polySmooth"] = polySmooth
    # divide ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("SubdividePolygon", keyMap)
    divide = "Divide Polygon Tool\n" \
             "Divides the mesh adding four times more polygons.\n" \
             "No smoothing is added unlike `Poly Smooth`\n\n" \
             " - Select a polygon object and run. Adjust divisions. \n\n" \
             "Each extra division adds four times more faces. \n\n" \
             "Hotkey: {}  \n{}".format(hk, MM_FACE)
    toolTipDict["divide"] = divide
    # unSmooth ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("UnsmoothPolygon", keyMap)
    unSmooth = "Unsmooth Tool (Maya 2024+ only)\n" \
               "Attempts to reduce polygons with quads. Is the opposite of `Poly Smooth`. \n\n" \
               " - Select a polygon object and run. Adjust divisions. \n\n" \
               "Each extra division reduces four times less faces. \n\n" \
               "Hotkey: {}  \n{}".format(hk, MM_FACE)
    toolTipDict["unSmooth"] = unSmooth
    # reduce ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("ReducePolygon", keyMap)
    reduce = "Reduce Polygon Tool\n" \
             "Reduces polygon counts via a reduce algorithm.\n" \
             "Percentage/Vert Count/Triangles\n\n" \
             " - Select a polygon mesh and run.  \n" \
             " - Adjust settings as desired, higher values reduce more. \n\n" \
             "Right-click for options. \n\n" \
             "Hotkey: {}  \n{}".format(hk, MM_FACE)
    toolTipDict["reduce"] = reduce
    # retopologize ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("PolyRetopo", keyMap)
    retopologize = "Retopology Tool\n" \
                   "Automatically retopologizes dense meshes to create lores quad meshes. \n\n" \
                   " - Select a dense polygon object and run. \n\n" \
                   "Right-click for options window. \n\n" \
                   "Hotkey: {}  \n{}".format(hk, MM_FACE)
    toolTipDict["retopologize"] = retopologize
    # remesh ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("PolyRemesh", keyMap)
    remesh = "Remesh Tool\n" \
             "Tessellates the selection with triangles. Can rebuild at various density levels. \n" \
             "Useful for adding detail to areas for sculpting or other. \n\n" \
             " - Select Objects/Faces/Edges or Vertices and run. " \
             " - Adjust the settings in the popup options. \n\n" \
             "Right-click for tool options. `Max Edge Length` is in cms. \n\n" \
             "Hotkey: {}  \n{}".format(hk, MM_FACE)
    toolTipDict["remesh"] = remesh
    # triangulate ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("Triangulate", keyMap)
    triangulate = "Triangulate\n" \
                  "Triangulates Quad and NGon polygons." \
                  " - Select Objects/Faces/Edges or Vertices and run. \n\n" \
                  "Hotkey: {}  \n{}".format(hk, MM_OBJ_FACE)
    toolTipDict["triangulate"] = triangulate
    # quadrangulate ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("Quadrangulate", keyMap)
    quadrangulate = "Quadrangulate\n" \
                    "Attempts to turn the selection into only quad faces.\n\n" \
                    " - Select Objects/Faces/Edges or Vertices and run. \n\n" \
                    "Hotkey: {}  \n{}".format(hk, MM_OBJ_FACE)
    toolTipDict["quadrangulate"] = quadrangulate
    # creaseSubD ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("PolyCreaseTool", keyMap)
    creaseSubD = "Crease Tool (SubDivision Surfaces)\n" \
                 "Creases edges on a SubD Polygon Object (Mesh Smooth On) to sharpen edges.\n\n" \
                 " - Select edges and run to enter tool. \n" \
                 " - Middle-click drag to adjust the crease as desired. \n\n" \
                 "Hotkey: {}  \n{}".format(hk, MM_FACE)
    toolTipDict["creaseSubD"] = creaseSubD
    # spinEdge ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("PolySpinEdgeBackward", keyMap)
    hk2 = hotkeymisc.niceHotkeyFromName("PolySpinEdgeForward", keyMap)
    spinEdge = "Spin Edge Tool \n" \
               "Spins an edge so that it connects to other vertices. \n\n" \
               " - Select an edge and run.  \n\n" \
               "Hotkey Spin Backwards: {}  \n" \
               "Hotkey Spin Forwards: {} \n{}".format(hk, hk2, MM_EDGE)
    toolTipDict["spinEdge"] = spinEdge
    # ---------------------------------------------------------------------
    # FACE & VERT NORMALS
    # ---------------------------------------------------------------------
    # conformFaceNormals ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("ConformPolygonNormals", keyMap)
    conformFaceNormals = "Conform Face Normals\n" \
                         "Conforms all face normals to face the same direction. \n" \
                         "Corrects black polygon face issues. \n\n" \
                         " - Select Object or Faces and run. \n\n" \
                         "Hotkey: {}  \n{}".format(hk, MM_FACE)
    toolTipDict["conformFaceNormals"] = conformFaceNormals
    # reverseFaceNormals ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("ReversePolygonNormals", keyMap)
    reverseFaceNormals = "Reverse Normals\n" \
                         "Reverses face normals to flip their direction. \n" \
                         "Corrects black polygon face issues. \n\n" \
                         " - Select Object or Faces and run.\n\n" \
                         "Hotkey: {}  \n{}".format(hk, MM_FACE)
    toolTipDict["reverseFaceNormals"] = reverseFaceNormals
    # softenEdges ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("polySoftenEdgeZoo", keyMap)
    softenEdges = "Soften Edges (Vertex Normals)\n" \
                  "Softens all selected edge or object vertex normals. \n\n" \
                  " - Select obj/faces/edges/vertices and run. \n\n" \
                  "Hotkey: {}  \n{}".format(hk, MM_OBJ_EDGE)
    toolTipDict["softenEdges"] = softenEdges
    # hardenEdges ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("polyHardenEdgeZoo", keyMap)
    hardenEdges = "Harden Edges (Vertex Normals)\n" \
                  "Hardens all selected edge or object vertex normals. \n\n" \
                  " - Select Obj/Faces/Edges/Vertices and run. \n\n" \
                  "Hotkey: {}  \n{}".format(hk, MM_OBJ_EDGE)
    toolTipDict["hardenEdges"] = hardenEdges
    # unlockVertexNormals ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("UnlockNormals", keyMap)
    unlockVertexNormals = "Unlock Vertex Normals\n" \
                          "Unlocks vertex normals so they are automatically adjusted.\n\n" \
                          " - Select Obj/Faces/Edges/Vertices and run. \n\n" \
                          "Hotkey: {}".format(hk)
    toolTipDict["unlockVertexNormals"] = unlockVertexNormals
    # averageVertexNormals ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("AveragePolygonNormals", keyMap)
    averageVertexNormals = "Average Vertex Normals\n" \
                           "Averages vertex normals so they are soft. \n\n" \
                           " - Select Obj/Faces/Edges/Vertices and run. \n\n" \
                           "Hotkey: {}  \n{}".format(hk, MM_VERT)
    toolTipDict["averageVertexNormals"] = averageVertexNormals
    # vertexNormalTool ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("PolygonNormalEditTool", keyMap)
    vertexNormalTool = "Vertex Normal Tool\n" \
                       "Manually set the angle of each vertex normal. \n\n" \
                       " - Select Obj/Vertices and run. \n" \
                       " - Select vertices and adjust the angle of each vertex normal. \n\n" \
                       "Hotkey: {}  \n{}".format(hk, MM_VERT)
    toolTipDict["vertexNormalTool"] = vertexNormalTool
    # transferVertexNormals ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("Transfer Attributes", keyMap)
    transferVertexNormals = "Transfer Vertex Normals\n" \
                            "Copies vertex normals to other objects. \n\n" \
                            " - Select the object you want to copy from. \n" \
                            " - Select the objects you want to copy to. \n" \
                            " - Run the tool.  \n\n" \
                            "Right-click for transfer options. \n\n" \
                            "Hotkey: {}  \n{}".format(hk, MM_FACE)
    toolTipDict["transferVertexNormals"] = transferVertexNormals
    return toolTipDict


def sculptModeHotkey(runtimeCommandName, keyMap):
    waxHotkey = hotkeymisc.niceHotkeyFromName("zooSetMeshWaxAlphaTool", keyMap)
    hk = hotkeymisc.niceHotkeyFromName(runtimeCommandName, keyMap)
    if hk != "None":
        hk += " (Must Be In Sculpt Mode."
        if waxHotkey != "None":
            hk += " Use {})".format(waxHotkey)
        else:
            hk += ")"
    return hk


def sculptingToolbox():
    """Tooltips for the Sculpting Toolbox UI.

    :return: A dictionary with the tooltips for the toolbox, string names are keys.
    :rtype: dict(str)
    """
    BRUSH_STRENGTH_INFO = "\n\nBrush Size: b (hold) drag left right (or middle mouse drag) \n" \
                          "Brush Strength: m (hold) drag up down (or middle mouse drag)\n"
    SCULPT_GRAB_MODES = "{}Normal Grab Mode: Hold Ctrl \nSmooth Mode: Hold Shift \nRelax Mode: Hold Ctrl Shift".format(
        BRUSH_STRENGTH_INFO)
    SCULPT_BRUSH_MODES = "{}Invert Mode: Hold Ctrl \nSmooth Mode: Hold Shift \nRelax Mode: Hold Ctrl Shift".format(
        BRUSH_STRENGTH_INFO)

    toolTipDict = {}
    keyMap = hotkeymisc.getAssignCommandsMap()

    # ---------------------------------------------------------------------
    # MAIN SCULPTING
    # ---------------------------------------------------------------------
    # wax ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("zooSetMeshWaxAlphaTool", keyMap)
    wax = "Wax Brush (Clay Buildup)\n" \
          "Builds a surface up from the lower parts of the sculpt upwards. \n" \
          "The main sculpting brush similar to clay buildup in ZBrush. \n\n" \
          "Right-click for more stamp options. \n\n" \
          "Hotkey: {}  \n{}".format(hk, MM_SCULPT)
    wax += SCULPT_BRUSH_MODES
    toolTipDict["wax"] = wax
    # grab ---------------------------------------------------------------
    hk = sculptModeHotkey("SetMeshGrabTool", keyMap)
    grab = "Grab Brush (Move)\n" \
           "Moves the mesh planar to the camera. \n" \
           "Hold `ctrl` to move relative to the object's normals. \n\n" \
           "Hotkey: {}  \n{}".format(hk, MM_SCULPT)
    grab += SCULPT_GRAB_MODES
    toolTipDict["grab"] = grab
    # knifeSculpt ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("zooSetMeshSculptKnifeAlphaTool", keyMap)
    knifeSculpt = "Sculpt Brush Used As Knife (v_wrinkle_vdm.tif stamp)\n" \
                  "Cuts/slices into the mesh using the sculpt brush with the wrinkle stamp assigned.\n\n" \
                  "Right-click for more stamp options. \n\n" \
                  "Hotkey: {}".format(hk)
    knifeSculpt += SCULPT_BRUSH_MODES
    toolTipDict["knifeSculpt"] = knifeSculpt
    # pinch ---------------------------------------------------------------
    hk = sculptModeHotkey("SetMeshPinchTool", keyMap)
    pinch = "Pinch Brush \n" \
            "Pinches the geometry together. \n" \
            "Useful for creating sharp corners. \n\n" \
            "Hotkey: {}  \n{}".format(hk, MM_SCULPT)
    pinch += SCULPT_BRUSH_MODES
    toolTipDict["pinch"] = pinch
    # sculpt ---------------------------------------------------------------
    hk = sculptModeHotkey("SetMeshSculptTool", keyMap)
    sculpt = "Sculpt Brush (Regular Mode)\n" \
             "Regular sculpt brush pushes in or out from the normals. \n" \
             "Can create blobby forms, use `Wax` instead in most scenarios. \n\n" \
             "Hotkey: {}  \n{}".format(hk, MM_SCULPT)
    sculpt += SCULPT_BRUSH_MODES
    toolTipDict["sculpt"] = sculpt
    # flatten ---------------------------------------------------------------
    hk = sculptModeHotkey("SetMeshFlattenTool", keyMap)
    flatten = "Flatten Brush\n" \
              "Flattens the mesh.\n\n" \
              "Hotkey: {}  \n{}".format(hk, MM_SCULPT)
    flatten += SCULPT_BRUSH_MODES
    toolTipDict["flatten"] = flatten
    # smooth ---------------------------------------------------------------
    hk = sculptModeHotkey("XgmSetSmoothBrushTool", keyMap)
    smooth = "Smooth Brush\n" \
             "Smooths the topology of the mesh. \n" \
             "Can cause the mesh to suck in if rounded. \n\n" \
             "Note: This tool is activated by holding `shift` on most brushes. \n\n" \
             "Hotkey: {}  \n{}".format(hk, MM_SCULPT)
    toolTipDict["smooth"] = smooth
    # relax ---------------------------------------------------------------
    hk = sculptModeHotkey("SetMeshRelaxTool", keyMap)
    relax = "Relax Brush\n" \
            "Smooths the surface while trying to maintain the mesh volume. \n\n" \
            "Note: This tool is activated by holding `ctrl + shift` on most brushes. \n\n" \
            "Hotkey: {}  \n{}".format(hk, MM_SCULPT)
    toolTipDict["relax"] = relax
    # freeze ---------------------------------------------------------------
    hk = sculptModeHotkey("SetMeshFreezeTool", keyMap)
    freeze = "Freeze Brush (Mask) \n" \
             "A mask tool which causes the painted blue mesh to be locked while sculpting.\n" \
             "Requires Lambert/Blinn shaders in older versions of Maya. \n" \
             "Hotkey: {}  \n{}".format(hk, MM_SCULPT)
    freeze += SCULPT_BRUSH_MODES
    toolTipDict["freeze"] = freeze
    # unfreeze ---------------------------------------------------------------
    hk = sculptModeHotkey("SculptMeshUnfreezeAll", keyMap)
    unfreeze = "UnFreeze Brush (Remove Mask)\n" \
               "Removes the freeze, erases it.\n\n" \
               "Hotkey: {}  \n{}".format(hk, MM_SCULPT)
    toolTipDict["unfreeze"] = unfreeze
    # invertFreeze ---------------------------------------------------------------
    hk = sculptModeHotkey("SculptMeshInvertFreeze", keyMap)
    invertFreeze = "Invert Freeze Brush (Invert Mask) \n" \
                   "Inverts the blue freeze mask if painted on an object.\n\n" \
                   "Hotkey: {}  \n{}".format(hk, MM_SCULPT)
    toolTipDict["invertFreeze"] = invertFreeze
    # toggleToolSettings ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("yyyyy", keyMap)
    toggleToolSettings = "Toggle Tool Settings Window\n" \
                         "Opens Maya's tool window with more brush settings.\n\n" \
                         "Hotkey: {}".format(hk)
    toolTipDict["toggleToolSettings"] = toggleToolSettings
    # falloffSurface ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("yyyyy", keyMap)
    falloffSurface = "Falloff Mode: Surface \n" \
                     "Sculpting affects the surrounding surface does not nearby shells or separated surfaces".format(hk)
    toolTipDict["falloffSurface"] = falloffSurface
    # falloffVolume ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("yyyyy", keyMap)
    falloffVolume = "Falloff Mode: Volume \n" \
                    "Sculpting affects the surrounding volume including nearby shells and or volumes".format(hk)
    toolTipDict["falloffVolume"] = falloffVolume

    # ---------------------------------------------------------------------
    # MISC SCULPTING
    # ---------------------------------------------------------------------
    # fill ---------------------------------------------------------------
    hk = sculptModeHotkey("SetMeshFillTool", keyMap)
    fill = "Fill Brush\n" \
           "Fills the valleys of a mesh.  Builds up from the low areas.\n\n" \
           "Hotkey: {}  \n{}".format(hk, MM_SCULPT)
    fill += SCULPT_BRUSH_MODES
    toolTipDict["fill"] = fill
    # scrape ---------------------------------------------------------------
    hk = sculptModeHotkey("SetMeshScrapeTool", keyMap)
    scrape = "Scrape Brush\n" \
             "Scrapes the top higher points of a mesh.\n" \
             "Minimize or remove raised areas of a surface. \n\n" \
             "Hotkey: {}  \n{}".format(hk, MM_SCULPT)
    scrape += SCULPT_BRUSH_MODES
    toolTipDict["scrape"] = scrape
    # knife ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("SetMeshKnifeTool", keyMap)
    knife = "Knife Brush\n" \
            "Cuts/slices into a mesh. Better to use Knife (Sculpt Brush) \n" \
            "This brush is mays default tool and is inferior to other methods. \n\n" \
            "Hotkey: {}  \n{}".format(hk, MM_SCULPT)
    knife += SCULPT_BRUSH_MODES
    toolTipDict["knife"] = knife
    # smear ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("SetMeshSmearTool", keyMap)
    smear = "Smear Brush\n" \
            "Pull/smear a mesh in the direction of the stroke.\n\n" \
            "Hotkey: {}  \n{}".format(hk, MM_SCULPT)
    smear += SCULPT_BRUSH_MODES
    toolTipDict["smear"] = smear
    # bulge ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("SetMeshBulgeTool", keyMap)
    bulge = "Bulge Brush\n" \
            "Inflate an area of a mesh in the direction of the surface normals.\n\n" \
            "Hotkey: {}  \n{}".format(hk, MM_SCULPT)
    bulge += SCULPT_BRUSH_MODES
    toolTipDict["bulge"] = bulge
    # amplify ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("SetMeshAmplifyTool", keyMap)
    amplify = "Amplify Brush\n" \
              "Accentuate/exaggerate the details on the surface of a mesh.\n\n" \
              "Hotkey: {}  \n{}".format(hk, MM_SCULPT)
    amplify += SCULPT_BRUSH_MODES
    toolTipDict["amplify"] = amplify
    # foamy ---------------------------------------------------------------
    hk = sculptModeHotkey("SetMeshFoamyTool", keyMap)
    foamy = "Foamy Brush\n" \
            "Raise/lift an area of the mesh without destroying the surface details.\n\n" \
            "Hotkey: {}  \n{}".format(hk, MM_SCULPT)
    foamy += SCULPT_BRUSH_MODES
    toolTipDict["foamy"] = foamy
    # spray ---------------------------------------------------------------
    hk = sculptModeHotkey("SetMeshSprayTool", keyMap)
    spray = "Spray Brush\n" \
            "Randomly spray a stamp imprint on a surface. \n" \
            "Open the tool settings to choose stamps. \n\n" \
            "Hotkey: {}  \n{}".format(hk, MM_SCULPT)
    spray += SCULPT_BRUSH_MODES
    toolTipDict["spray"] = spray
    # repeat ---------------------------------------------------------------
    hk = sculptModeHotkey("SetMeshRepeatTool", keyMap)
    repeat = "Repeat Brush\n" \
             "Stamp a pattern on a surface repeatedly. \n" \
             "Open the tool settings to choose stamps. \n\n" \
             "Hotkey: {}  \n{}".format(hk, MM_SCULPT)
    repeat += SCULPT_BRUSH_MODES
    toolTipDict["repeat"] = repeat
    # imprint ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("SetMeshImprintTool", keyMap)
    imprint = "Imprint Brush\n" \
              "Draw a single stamp on a surface.\n" \
              "Click and drag then release to see the effect\n" \
              "Open the tool settings to choose stamps. \n\n" \
              "Hotkey: {}  \n{}".format(hk, MM_SCULPT)
    imprint += SCULPT_BRUSH_MODES
    toolTipDict["imprint"] = imprint
    return toolTipDict


def selectToolbox():
    BRUSH_STRENGTH_INFO = "\n\nBrush Size: b (hold) drag left right (or middle mouse drag) \n" \
                          "Brush Strength: m (hold) drag up down (or middle mouse drag)\n"
    SCULPT_GRAB_MODES = "{}Normal Grab Mode: Hold Ctrl \nSmooth Mode: Hold Shift \nRelax Mode: Hold Ctrl Shift".format(
        BRUSH_STRENGTH_INFO)
    toolTipDict = {}
    keyMap = hotkeymisc.getAssignCommandsMap()
    # select ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("SelectToolOptionsNameCommand", keyMap)
    select = "Maya's default select tool.\n\n" \
             "Hotkey: {}".format(hk)
    toolTipDict["select"] = select
    # contiguousEdges ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("SelectContiguousEdges", keyMap)
    contiguousEdges = "Select Contiguous Edges\n" \
                      "Select based on the angles between edges.\n\n" \
                      " - Select Edge/s. \n" \
                      " - Run the tool. \n\n" \
                      "Optionally right click to open the options and other tools. \n\n" \
                      "Hotkey: {}".format(hk)
    toolTipDict["contiguousEdges"] = contiguousEdges
    # grab ---------------------------------------------------------------
    hk = sculptModeHotkey("SetMeshGrabTool", keyMap)
    grab = "Grab Brush (Move)\n" \
           "Moves the mesh planar to the camera. \n" \
           "Hold `ctrl` to move relative to the object's normals. \n\n" \
           "Hotkey: {}  \n{}".format(hk, MM_SCULPT)
    grab += SCULPT_GRAB_MODES
    toolTipDict["grab"] = grab
    # openZooSelectSets ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("SelectToolOptionsNameCommand", keyMap)
    openZooSelectSets = "Maya's default select tool.\n\n" \
                        "Hotkey: {}".format(hk)
    toolTipDict["openZooSelectSets"] = openZooSelectSets
    # growSelection ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("GrowPolygonSelectionRegion", keyMap)
    growSelection = "Grow Selection.\n" \
                    "Grows the existing  component selection. \n\n" \
                    " - Select a vertex, face, edge, or UV and run to grow to surrounding components. \n\n" \
                    "Hotkey: {}".format(hk)
    toolTipDict["growSelection"] = growSelection
    # shrinkSelection ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("ShrinkPolygonSelectionRegion", keyMap)
    shrinkSelection = "Grow Selection.\n" \
                      "Grows the existing  component selection. \n\n" \
                      " - Select a vertex, face, edge, or UV and run to shrink to surrounding components. \n\n" \
                      "Hotkey: {}".format(hk)
    toolTipDict["shrinkSelection"] = shrinkSelection
    # softSelect ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("dR_softSelStickyPress", keyMap)
    toolTipDict["softSelect"] = "Soft Select. \n" \
                                "Hotkey: {}".format(hk)
    # convertSelection ---------------------------------------------------------------
    toolTipDict["convertSelection"] = "Converts the current selection to the specified component type. \n\n" \
                                      "Left click to activate the menu for options."
    # invertSelection ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("InvertSelection", keyMap)
    toolTipDict["invertSelection"] = "Inverts the current selection \n" \
                                     "Hotkey: {}".format(hk)
    # selectHierarchy ---------------------------------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("zoo_selectHierarchy", keyMap)
    toolTipDict["selectHierarchy"] = "Adds children of the currently selected objects to the selection. \n" \
                                     "Hotkey: {}".format(hk)
    # selectRandom ---------------------------------------------------------------
    toolTipDict["selectRandom"] = "Select random objects or components and run. \n" \
                                  "  - 50 will randomly select 50% of the current selection. \n" \
                                  "  - 10 will randomly select 10% of the current selection."
    return toolTipDict


def mirrorToolbox():
    toolTipDict = {}
    keyMap = hotkeymisc.getAssignCommandsMap()
    # symmetryCombo ---------------------------------------
    toolTipDict["symmetryCombo"] = "The mirror axis for all modes, also changes symmetry mode.\n" \
                                   "  - World: Mirror/Symmetry across world coordinates. \n" \
                                   "  - Object: Mirror/Symmetry across object space coordinates. \n" \
                                   "Note:  Object mode affects instances in local coordinates"
    # directionCombo ---------------------------------------
    toolTipDict["directionCombo"] = "The direction of the mirror, + mirrors from positive to negative. \n" \
                                    "Note: Regarding instances the direction only affects naming."
    # toggleSymmetryMode ---------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("symmetricalToggle", keyMap)
    toolTipDict["toggleSymmetryMode"] = "Toggles Maya's native symmetry mode. On/Off. \n\n" \
                                        "Hotkey: {}".format(hk)
    # symmetrize ---------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("Symmetrize", keyMap)
    toolTipDict["symmetrize"] = "Symmetrize a mesh while keeping mesh vertex orders. \n\n" \
                                "  1. Select the vertices to symmetrize. \n" \
                                "  2. Press the Symmetrize button.  \n" \
                                "  3. Select a center edge.  \n\n" \
                                "The mesh will be symmetrized while keeping UVs and point orders.\n\n" \
                                "Hotkey: {}".format(hk)
    # flip ---------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("FlipMesh", keyMap)
    toolTipDict["flip"] = "Flip mirrors a mesh while keeping mesh vertex orders. \n\n" \
                          "  1. Select the vertices to symmetrize. \n" \
                          "  2. Press the Flip button.  \n" \
                          "  3. Select a center edge.  \n\n" \
                          "The mesh will be mirror flipped and will keep UVs and point orders.\n\n" \
                          "Hotkey: {}".format(hk)
    # zooMirrorPolygon ---------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("mirrorPolygonPlus", keyMap)
    toolTipDict[
        "zooMirrorPolygon"] = "Uses Maya's `Mesh > Mirror` with extra functionality. Rebuilds the opposite side.\n\n" \
                              "- In object mode acts as `Mesh > Mirror` \n\n" \
                              "- In component mode if verts or edges are selected the selection \n" \
                              "will be centered and then the whole object mirrored\n\n" \
                              "  1. Select center edges or vertices. \n" \
                              "  2. Run \n\n" \
                              "Hotkey: {}".format(hk)
    # instanceMirror ---------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("mirrorInstanceGroupWorldX", keyMap)
    toolTipDict["instanceMirror"] = "Instance mirrors an object. \n" \
                                    "Will group selected objects, then duplicates an instanced group with negative scale. \n\n" \
                                    "  1. Select objects and run  \n\n" \
                                    "Use the uninstance buttons to remove instancing. \n\n" \
                                    "Hotkey: {}".format(hk)
    # removeAllInstances ---------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("zooUnInstanceAll", keyMap)
    toolTipDict[
        "removeAllInstances"] = "Uninstances all `Mirror Instances` in the scene. Removes instances and leaves geometry.\n\n" \
                                "Hotkey: {}".format(hk)
    # removeSelectedInstances ---------------------------------------
    hk = hotkeymisc.niceHotkeyFromName("zooUnInstance", keyMap)
    toolTipDict["removeSelectedInstances"] = "Uninstances any selected `Mirror Instance` setup/s. \n\n" \
                                             "Hotkey: {}".format(hk)
    # removeFreeze -------------------------------------------------------
    toolTipDict["removeFreeze"] = "Object Symmetry and Mirror modes do not work intuitively on objects that \n" \
                                  "have had their transforms frozen.  This button removes the freeze by resetting the \n" \
                                  "Local Rotate/Scale Pivots on and objects transform node. \n" \
                                  "Select objects and run."
    # mergeThreshold ---------------------------------------
    toolTipDict["mergeThreshold"] = "Vertices within this threshold will be merged. \n" \
                                    "Note: This setting only affects shells, the cut mesh is not affected"
    # smoothAngle ---------------------------------------
    toolTipDict["smoothAngle"] = "Affects the soften/harden edge crease value across the seam. \n" \
                                 "If `Force Smooth All` is checked then the whole object will be smoothed. "
    # deleteHistory ---------------------------------------
    toolTipDict["deleteHistory"] = "Delete history after the mirror is performed?"
    return toolTipDict
