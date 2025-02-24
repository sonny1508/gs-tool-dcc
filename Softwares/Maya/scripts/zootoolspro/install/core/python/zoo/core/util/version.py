"""This module provides handling of version strings i.e. 1.0.0
"""

from distutils.version import LooseVersion

MAJOR_VERSION = 0
MINOR_VERSION = 1
PATCH_VERSION = 2
ALPHABETA_VERSION = 3

VERSION_INDICES = {MAJOR_VERSION: 0,
                   MINOR_VERSION: 1,
                   PATCH_VERSION: 2,
                   ALPHABETA_VERSION: 4}


def incrementVersion(versionStr, level):
    """Increment the major, minor, patch, or alpha/beta version of a version string.

    :param versionStr: The version string to be incremented.
    :type versionStr:
    :param level: The level of the version to increment. One of "major", "minor", "patch", or "alphaBeta".
    :type level:
    :return: The new version string.
    :rtype:
    :raise ValueError: If an invalid level is provided.

    ..code-block python:

        versionStr = "0.9.0"
        newVersion = version.incrementVersion(versionStr, "major") # Increment major version
        print(newVersion) # Output: "1.0.0"

        versionStr = "0.9.0alpha0"
        newVersion = version.incrementVersion(versionStr, "patch") # Increment patch version
        print(newVersion) # Output: "0.9.1alpha0"

    """

    v = [None] * 5
    # Parse the current version into the list.
    for index, i in enumerate(LooseVersion(versionStr).version):
        v[index] = i
    # Increment the version number at the specified index.
    incrIndex = VERSION_INDICES[level]
    v[incrIndex] += 1

    # Convert the version list to a list of strings.
    newVersions = []
    for index, value in enumerate(v):
        # zero out all numbers after the level index except for
        if value is not None and index > incrIndex:
            if index != 3:
                newVersions.append("0")
            else:
                break
        elif value is not None:
            newVersions.append(str(value))

    # Concatenate the version numbers into a string with dot separators.
    if len(newVersions) == 5:
        outputVersion = ".".join(newVersions[:3]) + "".join(newVersions[3:])
    else:
        outputVersion = ".".join(newVersions)
    return outputVersion
