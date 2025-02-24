"""
This script shows how you could use a mayapy/batch session to upgrade a hive rig.

With the below script make sure you change the paths for your setup.

CommandLine Example::

    set MAYA_MODULE_PATH=zootoolspro/install/core/extensions/maya;
    set ZOO_LOG_LEVEL=DEBUG
    mayapy.exe upgrade_hive_rig_cli.py --scene my_rig_scene.ma --outputPath my_rig_scene_upgraded.ma

"""
import argparse
import contextlib


def parseArguments():
    parser = argparse.ArgumentParser("Hive",
                                     description="Provides a script to upgrade a hive rig which resides within maya "
                                                 "scene")
    parser.add_argument("--outputPath", type=str, required=True, help="Output path for the upgrade rig file.")
    parser.add_argument("--rigName", type=str, required=False, help="The name of the rig in the scene, defaults to "
                                                                    "finding the first rig in the scene.")
    parser.add_argument("--scene", type=str, required=True,
                        help="The Maya scene path to load")
    return parser.parse_args()


def upgradeRig(rig):
    """Does the actual labour of rebuilding the rig, relies on the current scenes cached rig definition.

    We always go back to the guides which updates the rig definition merging new updates from the base components
    before user modification. Before we delete the control rig(maintaining joints and deformation) then we polish
    the rig for final output.

    :param rig: The Hive rig instance to upgrade.
    :type rig: :class:`api.Rig`
    """
    rig.buildGuides()
    rig.deleteRigs()
    rig.polish()


def findRigInstance(name=None):
    """Find the first occurrence of a hive rig which matches the give rig name.

    :param name: The rig name to find in the scene.
    :type name: str
    :return:
    :rtype: :class:`api.Rig`
    """
    from zoo.libs.hive import api
    if name:
        rigInstance = api.rootByRigName(name)
        if rigInstance is not None:
            return rigInstance
        raise api.HiveError("No rig in the scene with name: {}".format(name))
    rigs = list(api.iterSceneRigs())
    if not rigs:
        raise api.HiveError("No rigs in scene")
    return rigs[0]


@contextlib.contextmanager
def initializeContext():
    from maya import standalone
    standalone.initialize(name="python")
    try:

        yield
    finally:
        standalone.uninitialize()


if __name__ == "__main__":
    args = parseArguments()
    rigName = args.rigName
    outputPath = args.outputPath
    sceneFile = args.scene

    with initializeContext():
        from maya import cmds

        cmds.loadPlugin("zootools.py")

        from zoo.libs.maya.utils import files

        cmds.file(sceneFile, force=True, options="v=0;", ignoreVersion=True, open=True)
        rigInstance = findRigInstance(rigName)
        upgradeRig(rigInstance)
        files.saveScene(outputPath)
