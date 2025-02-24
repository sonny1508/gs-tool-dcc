import glob
import os, re
import shutil

from zoo.core.util import processes, zlogging

logger = zlogging.getLogger(__name__)

PIP_PKG_UNDERSCORE = re.compile('[^A-Za-z0-9.]+')


def packageAlreadyExists(name, rootFolder):  # exclude version checking
    if os.path.exists(os.path.join(rootFolder, name)):
        return True
    return os.path.exists(PIP_PKG_UNDERSCORE.sub('_', name))


def missingRequirements(requirements, folder):
    for requirement in requirements:
        libraryName = requirement.name
        if packageAlreadyExists(libraryName, folder):
            continue
        yield requirement


def pipInstallRequirements(targetFolder, executable, requirements, upgrade=False, pipArguments=None):
    """Installs the specified requirements to the specified folder.

    :param targetFolder: The folder to remove the requirements from
    :type targetFolder: str
    :param upgrade: Whether to upgrade the requirements
    :type upgrade: bool
    :param executable: The python executable to use.
    :type executable: str
    :param requirements: The requirements to install.
    :type requirements: :class:`zoo.core.packageresolver.requirements.RequirementList`
    :param pipArguments: Additional arguments to pass to pip.
    :type pipArguments: list[str]
    """

    if not upgrade:
        missingLibraries = [requirement.line for requirement in missingRequirements(requirements, targetFolder)]
    else:
        missingLibraries = [requirement.line for requirement in requirements]
    if not missingLibraries:
        return
    fields = [executable, "-m", "pip", "install"]
    if upgrade:
        fields.append("--upgrade")
    fields.extend(["--no-warn-script-location", "--target", targetFolder])
    if pipArguments:
        fields.extend(pipArguments)
    fields.extend(missingLibraries)
    logger.debug("Installing requirements: {}".format(fields))
    returnCode = processes.checkOutput(fields, encoding="utf-8")
    return returnCode, missingLibraries


def uninstallRequirements(targetFolder, requirements):
    """Uninstalls the specified requirements from the specified folder

    :param targetFolder: The folder to remove the requirements from
    :type targetFolder: str
    :param requirements: The requirements to uninstall
    :type requirements: :class:`zoo.core.packageresolver.requirements.RequirementList`
    """
    for requirement in requirements:
        libraryName = requirement.name
        if not packageAlreadyExists(libraryName, targetFolder):
            continue
        shutil.rmtree(os.path.join(targetFolder, libraryName))

        for distInfo in glob.glob(os.path.join(targetFolder, libraryName + "*.dist-info")):
            for path in pipRecordAsPaths(targetFolder, distInfo):
                if os.path.isfile(path):
                    os.remove(path)
                elif os.path.isdir(path):
                    shutil.rmtree(distInfo)


def pipRecordAsPaths(packagesFolder, record):
    """Parses a pip record file as a list of paths

    :param packagesFolder: The folder we're the pip packages exist.
    :type packagesFolder: str
    :param record: The pip record file as a string
    :type record: str
    :return: A list of paths
    :rtype: list
    """
    # RECORD is a CSV file with the following fields: path, hash, size
    # at the moment we only care about the path
    with open(os.path.join(record, "RECORD"), "r") as f:
        for line in f.readlines():
            line = line.strip()
            if not line:
                continue
            line = line.partition(",")[0]
            # case where the path is relative to the record folder i.e. scripts
            if line.startswith(".."):
                line = os.path.join(record, line)
                yield os.path.abspath(line)
            else:
                yield os.path.join(packagesFolder, line)

