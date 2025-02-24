"""Converts a Maya file's shaders to other renderers

Run from inside
    zoo.libs.maya.cmds.shaders.standalone.standalone_runconvert.py

Or run as a standalone script from a bat file such as
    set MAYA_APP_DIR=D:\repos\mayaPrefs\zoo_v2
    set MAYA_MODULE_PATH=D:\repos\zootools_pro\modules
    set MAYA_PLUG_IN_PATH=C:\Program Files\Pixar\RenderManForMaya-24.3\plug-ins
    call "C:\Program Files\Autodesk\Maya2022\bin\mayapy D:\aPath\convertshaderscene.py"

TODO:
- Support Glass
- Support Thin Glass
- Add auto VRay SubDivision
- Support Subsurface
- Renderman Clear Coat is on when it shouldn't be
"""
import argparse


def parseArguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--shaderType", type=str, required=True)
    parser.add_argument("--sceneFile", type=str, required=True)
    parser.add_argument("--removeShaders", type=str, required=False)
    parser.add_argument("--maintainConnections", type=str, required=False)
    return parser.parse_args()


if __name__ == "__main__":
    args = parseArguments()

    import maya.standalone
    maya.standalone.initialize()  # Start Maya in batch mode
    import maya.cmds as cmds
    cmds.loadPlugin("zootools.py")
    from zoo.libs.maya.cmds.shaders import convertshaders
    print("Imported: convertshaders")
    convertshaders.openConvertFileSave(args.sceneFile,
                                       args.shaderType,
                                       removeShaders=args.removeShaders,
                                       maintainConnections=args.maintainConnections,
                                       message=True)
    maya.standalone.uninitialize()
