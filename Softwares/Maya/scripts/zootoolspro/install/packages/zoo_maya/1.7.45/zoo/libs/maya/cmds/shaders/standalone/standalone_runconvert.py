"""Converts a Maya file's shaders to other renderers

"standardSurface" "lambert", "blinn", "phong", "phongE", "aiStandardSurface", "VRayMtl", "RedshiftMaterial", "PxrSurface"

OPEN_PATH: file should usually be a standardSurface file.
SHADER_TYPES: for the shaders to convert, a new Maya file is created for each shader.
REMOVE_SHADERS: Removes old shaders
MAINTAIN_CONNECTIONS: Keep any shader connections to diffuse etc

"""

if __name__ == "__main__":
    import subprocess
    import os

    OPEN_PATH = r"C:\Users\Andrew Silke\Documents\zoo_preferences\assets\maya_scenes\zoo_rigs_hive\natalie_rig_STRD\natalie_rig_STRD.ma"
    SHADER_TYPES = ["blinn"]
    REMOVE_SHADERS = "1"
    MAINTAIN_CONNECTIONS = "1"

    # MayaPath path ----------------
    mayaPath = r'C:\Program Files\Autodesk\Maya2020\bin\mayapy.exe'

    # Script path ----------------
    scriptPath = r'D:\repos\zootools_dev\zoo_maya\zoo\libs\maya\cmds\shaders\standalone\convertshaderscene.py'

    # Environment Variables ------------------------------------------------
    envCopy = os.environ.copy()
    envCopy["MAYA_APP_DIR"] = r"D:\repos\mayaPrefs\zoo_v2"
    envCopy["MAYA_MODULE_PATH"] = r"D:\repos\zootools_pro\modules"
    envCopy["MAYA_PLUG_IN_PATH"] = r"C:\Program Files\Pixar\RenderManForMaya-24.3\plug-ins"

    # Run ------------------------------------------------
    for shader in SHADER_TYPES:
        args = ["--shaderType", shader,
                "--sceneFile", OPEN_PATH,
                "--removeShaders", REMOVE_SHADERS,
                "--maintainConnections", MAINTAIN_CONNECTIONS]

        maya = subprocess.Popen([mayaPath, scriptPath] + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                universal_newlines=True, env=envCopy)
        out, err = maya.communicate()
        exitcode = maya.returncode

        if str(exitcode) != '0':
            print(err)
        else:
            for i in out.splitlines():
                print(i)
