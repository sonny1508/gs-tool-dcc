import os
import sys


def _currentFolder():
    currentFolder = os.path.dirname(__file__)
    return currentFolder


def _embedPaths():
    """This ensures zootools python paths have been setup correctly"""
    currentFolder = _currentFolder()
    envPath = os.getenv("ZOOTOOLS_PRO_ROOT", "")
    rootPath = ""
    if envPath:
        rootPath = os.path.abspath(os.path.expandvars(os.path.expanduser(envPath)))
    if not os.path.exists(rootPath):
        rootPath = os.path.abspath(os.path.join(currentFolder, "..", ".."))

    rootPythonPath = os.path.join(rootPath, "python")
    if rootPath is None:
        msg = """Zootools is missing the 'ZOOTOOLS_PRO_ROOT' environment variable
                in the maya mod file.
                """
        raise ValueError(msg)
    elif not os.path.exists(rootPythonPath):
        raise ValueError("Failed to find valid zootools python folder")
    if rootPythonPath not in sys.path:
        sys.path.append(rootPythonPath)
    if currentFolder not in sys.path:
        sys.path.append(currentFolder)
    return rootPath


def loadZoo():
    rootPath = _embedPaths()

    if rootPath is None:
        msg = """Zoo Tools PRO is missing the 'ZOOTOOLS_PRO_ROOT' environment variable
        in the maya mod file.
        """
        raise ValueError(msg)

    from zoo.core import api
    from zoo.core import engine
    from zoounreal import unreallogging
    from zoo.core.util import zlogging

    manager = zlogging.CentralLogManager()
    manager.removeHandlers(zlogging.CENTRAL_LOGGER_NAME)
    manager.addHandler(zlogging.CENTRAL_LOGGER_NAME, unreallogging.UnrealLogHandler())

    from zoounreal import unrealengine
    currentInstance = api.currentConfig()
    if currentInstance is None:
        coreConfig = api.zooFromPath(rootPath)
        engine.startEngine(coreConfig, unrealengine.UnrealEngine, "unreal")


if __name__ == "__main__":
    loadZoo()
