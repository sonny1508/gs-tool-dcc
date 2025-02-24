"""CLI python entry point calls the command loader for handling directives.

Internal use only
"""
import os
import sys
import logging

logger = logging.getLogger(__name__)

if os.getenv("ZOO_LOG_LEVEL", "INFO") == "DEBUG":
    logger.setLevel(level=logging.DEBUG)
else:
    logger.setLevel(level=logging.INFO)


def install(rootDirectory, args):
    """Installs zootools into the current environment by calling zooFromPath
    """

    zooCmdDir = os.path.abspath(os.path.dirname(rootDirectory))
    pyFolder = os.path.join(zooCmdDir, "python")
    if pyFolder not in sys.path:
        logger.debug("Installing PythonPath into current environment: {}".format(pyFolder))
        sys.path.append(pyFolder)
    # ensure zoo tools has been added to the python path
    from zoo.core.util import env
    env.addToEnv("PYTHONPATH", [pyFolder])

    from zoo.core import api
    cfg = api.zooFromPath(zooCmdDir)
    api.setCurrentConfig(cfg)
    return api.fromCli(cfg, args)


def run(argv, exit=True):
    root = os.path.dirname(argv[0])
    returnCode = install(root, argv[1:])
    if exit:
        sys.exit(returnCode or 0)


if __name__ == "__main__":
    run(sys.argv)
