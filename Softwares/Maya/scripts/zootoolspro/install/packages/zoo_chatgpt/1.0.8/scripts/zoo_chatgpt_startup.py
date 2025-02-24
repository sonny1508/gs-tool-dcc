import os
import sys
from zoo.core import engine


def startup(package):
    eng = engine.currentEngine()
    if eng.engineName == "maya":
        package.resolveEnvPath("ZOO_CHATGPT_CONTROLLER",
                               ["{self}/zoo/apps/chatgptui/controllers/mayacontroller.py"],
                               applyEnvironment=True)

def install(package):
    if sys.version_info[0] != 3:
        return
    buildDir = os.path.join(package.root, "build")
    requirementsFile = os.path.join(buildDir, "requirements-3.txt")
    package.pipRequirementsPath = requirementsFile
