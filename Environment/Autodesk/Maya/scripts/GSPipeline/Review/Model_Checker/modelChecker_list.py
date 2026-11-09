# Every command the window shows, by its function name in modelChecker_commands.
#   label     - the button text
#   category  - the section it sits in
#   tooltip   - for artists: what it finds or does, in short plain English
#   isAction  - changes the scene, rather than reporting on it
#   isGlobal  - works on the whole scene, ignoring the selection
#   hidden    - kept working, but left off the window
mcCommandsList = {
    "trailingNumbers": {
        'label': 'Trailing Numbers',
        'category': 'naming',
        'tooltip': 'Finds object names that end with a number, like "pCube1" or "wheel_01".',
    },
    "duplicatedNames": {
        'label': 'Duplicated Names',
        'category': 'naming',
        'tooltip': "Finds objects with the same name as another object.\n"
                   "Every name must be unique.",
    },
    "shapeNames": {
        'label': 'Shape Names',
        'category': 'naming',
        'tooltip': 'Finds shapes not named after their object.\n'
                   'The shape of "wheel" must be "wheelShape".',
    },
    "namespaces": {
        'label': 'Namespaces',
        'category': 'naming',
        'tooltip': 'Finds objects with a namespace in the name, like "car:wheel".',
    },
    "layers": {
        'label': 'Layers',
        'category': 'general',
        'tooltip': "Finds objects that are in a display layer.",
    },
    "generalHistory": {
        'label': 'History',
        'category': 'general',
        'tooltip': "Finds meshes with construction history.\n"
                   "Deformers, like a skin, are allowed.",
    },
    "sceneCleanup": {
        'label': 'Scene Cleanup',
        'category': 'general',
        'isGlobal': True,
        'tooltip': "Finds what the Cleanup button would fix, in the whole scene.\n"
                   "Red: the artist presses Cleanup.",
    },
    "shaders": {
        'label': 'Shaders',
        'category': 'general',
        'tooltip': "Finds meshes with a material other than the default lambert1.",
    },
    "unfrozenTransforms": {
        'label': 'Unfrozen Transforms',
        'category': 'general',
        'tooltip': "Finds objects with translate or rotate not at 0, or scale not at 1.\n"
                   "Fix: Freeze Transforms.",
    },
    "uncenteredPivots": {
        'label': 'Uncentered Pivots',
        'category': 'general',
        'tooltip': "Finds objects whose pivot is not at the world center (0, 0, 0).",
    },
    "parentGeometry": {
        'label': 'Parent Geometry',
        'category': 'general',
        'tooltip': "Finds objects parented under a mesh. Put them under a group instead.",
    },
    "emptyGroups": {
        'label': 'Empty Groups',
        'category': 'general',
        'tooltip': "Finds groups with nothing inside.",
    },
    "symmetryX": {
        'label': 'Symmetry X',
        'category': 'general',
        'tooltip': "Checks left / right symmetry across world X = 0.\n"
                   "Finds faces with no mirror face on the other side.",
    },
    "symmetryY": {
        'label': 'Symmetry Y',
        'category': 'general',
        'tooltip': "Checks top / bottom symmetry across world Y = 0.\n"
                   "Finds faces with no mirror face on the other side.",
    },
    "triangles": {
        'label': 'Triangles',
        'category': 'topology',
        'tooltip': "Finds faces with 3 sides.",
    },
    "ngons": {
        'label': 'Ngons',
        'category': 'topology',
        'tooltip': "Finds faces with more than 4 sides.",
    },
    "openBorder": {
        'label': 'Open Border',
        'category': 'topology',
        'tooltip': "Finds open edges: holes, edges that are not welded,\n"
                   "and edges next to a flipped face.",
    },
    "poles": {
        'label': 'Poles',
        'category': 'topology',
        'hidden': True,
        'tooltip': "Finds vertices with more than 5 edges.",
    },
    "hardEdges": {
        'label': 'Hard Edges',
        'category': 'topology',
        'tooltip': "Finds hard edges. Border edges are not counted.",
    },
    "lockedNormals": {
        'label': 'Locked Normals',
        'category': 'topology',
        'hidden': True,
        'tooltip': "Finds vertices with locked normals.",
    },
    "lamina": {
        'label': 'Lamina',
        'category': 'topology',
        'tooltip': "Finds faces that share all their edges with another face:\n"
                   "one face lying on top of another.",
    },
    "zeroAreaFaces": {
        'label': 'Zero Area Faces',
        'category': 'topology',
        'tooltip': "Finds faces with no area: all their points on one line or spot.",
    },
    "zeroLengthEdges": {
        'label': 'Zero Length Edges',
        'category': 'topology',
        'tooltip': "Finds edges with no length: both points in the same spot.",
    },
    "noneManifoldEdges": {
        'label': 'Non-Manifold Edges',
        'category': 'topology',
        'tooltip': "Finds edges shared by more than 2 faces.",
    },
    "starlike": {
        'label': 'Starlike',
        'category': 'topology',
        'hidden': True,
        'tooltip': "Finds faces bent so badly that their center cannot see all their corners.",
    },
    "selfPenetratingUVs": {
        'label': 'Self Penetrating UVs',
        'category': 'UVs',
        'tooltip': "Finds faces whose UVs overlap other UVs of the same mesh.",
    },
    "missingUVs": {
        'label': 'Missing UVs',
        'category': 'UVs',
        'tooltip': "Finds faces with no UVs.",
    },
    "uvRange": {
        'label': 'UV Range',
        'category': 'UVs',
        'tooltip': "Finds UVs outside the allowed area: U from 0 to 10, V from 0 up.",
    },
    "crossBorder": {
        'label': 'Cross Border',
        'category': 'UVs',
        'tooltip': "Finds faces whose UVs cross the border of a UV tile.",
    },
    "onBorder": {
        'label': 'On Border',
        'category': 'UVs',
        'tooltip': "Finds UVs lying exactly on the border of a UV tile.",
    },
    "freezeTransforms": {
        'label': 'Freeze Transforms',
        'category': 'Actions',
        'isAction': True,
        'tooltip': "Sets translate and rotate to 0 and scale to 1. The shape stays in place.\n"
                   "Runs on your selection.",
    },
    "mergeIdenticalVertices": {
        'label': 'Merge Identical Vertices',
        'category': 'Actions',
        'isAction': True,
        'tooltip': "Merges vertices in the same spot (closer than 0.0001).\n"
                   "Runs on your selection.",
    },
    "centerPivots": {
        'label': 'Center Pivots',
        'category': 'Actions',
        'isAction': True,
        'tooltip': "Moves each pivot to the center of its object.\n"
                   "Runs on your selection.",
    },
    "fixLaminaFaces": {
        'label': 'Fix Lamina Faces',
        'category': 'Actions',
        'isAction': True,
        'tooltip': "Deletes faces that share all their edges with another face.\n"
                   "Runs on your selection.",
    },
    "cleanup": {
        'label': 'Cleanup',
        'category': 'Actions',
        'isAction': True,
        'isGlobal': True,
        'tooltip': ("Tidies the whole scene, ignoring your selection: namespaces, custom "
                    "attributes, empty layers and sets, unused nodes and mesh display.\n"
                    "Also bakes history on every mesh. Deformers stay."),
    },
    "deleteHistory": {
        'label': 'History',
        'category': 'Delete',
        'isAction': True,
        'tooltip': "Deletes all history, deformers too.\n"
                   "Runs on your selection.",
    },
    "deleteDisplayLayers": {
        'label': 'Display Layers',
        'category': 'Delete',
        'isAction': True,
        'isGlobal': True,
        'tooltip': "Deletes every display layer. The objects stay.\n"
                   "Runs on the whole scene, ignoring your selection.",
    },
    "deleteCameras": {
        'label': 'Cameras',
        'category': 'Delete',
        'isAction': True,
        'isGlobal': True,
        'tooltip': "Deletes every camera except persp, top, front and side.\n"
                   "Runs on the whole scene, ignoring your selection.",
    },
    "deleteColorSets": {
        'label': 'Color Sets',
        'category': 'Delete',
        'isAction': True,
        'tooltip': "Deletes all color sets (vertex colors).\n"
                   "Runs on your selection.",
    },
    "deleteUnusedMaterials": {
        'label': 'Unused Materials',
        'category': 'Delete',
        'isAction': True,
        'isGlobal': True,
        'tooltip': "Deletes materials that no object uses.\n"
                   "Runs on the whole scene, ignoring your selection.",
    },
    "deleteInputDataNodes": {
        'label': 'Input Data Nodes',
        'category': 'Delete',
        'isAction': True,
        'tooltip': "Deletes blind data and metadata nodes left in the mesh history.\n"
                   "Runs on your selection.",
    },
}

# Toggles in the Debug section, by their name in modelChecker_debug. They change
# how the viewport draws, never the scene. One is on at a time, for the whole scene.
mcDebugViews = {
    "faceOrientation": {
        'label': 'Check Face Orientation',
        'tooltip': "Blue: the front of a face. Red: the back of a face.\n"
                   "Red on the outside of a model is a flipped face.",
    },
    "lockMap": {
        'label': 'Check Locked Normals',
        'tooltip': "Orange: faces with a locked normal.\n"
                   "Grey: no locked normals.",
    },
}
