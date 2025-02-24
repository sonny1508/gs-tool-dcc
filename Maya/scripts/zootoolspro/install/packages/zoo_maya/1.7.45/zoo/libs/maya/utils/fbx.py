"""Utilities for handling FBX related operations
"""
from maya import mel


def availableFbxVersions(ignoreBeforeVersion=None):
    """Returns the current available fbx versions in the form of [("FBX202000", "FBX 2020")].

    :param ignoreBeforeVersion: If provided then any version before the specified will be ignore \
    ie. if in 2020 provide ignoreBeforeVersion="2018" will ignore 2017 below.

    :type ignoreBeforeVersion: str
    :return: zip object contain a tuple of (version,version label)
    :rtype: zip[tuple[str, str]]
    """
    # basically the python command for this always raises a RuntimeError instead of returning
    # a list when running with a query flag so hence the mel. GRR
    # ie. # Error: RuntimeError: Use syntax: FBXExportFileVersion -v FBX202000 | ... or FBXExportFileVersion -q #
    versions = mel.eval("string $fbxVersionList[] = `FBXExportFileVersion -vl`")
    labelList = mel.eval(
        "string $fbxUIVList[] = `FBXExportFileVersion -uivl`;")  # "FBX 2016/2017" "FBX 2014/2015" "FBX 2013" ...
    if ignoreBeforeVersion:
        for i, version in enumerate(versions):
            if version[3:].startswith(ignoreBeforeVersion):
                return zip(versions[:i + 1], labelList[:i + 1])
    return zip(versions, labelList)


def currentFbxExportVersion():
    # basically the python command for this always raises a RuntimeError instead of returning
    # a list when running with a query flag so hence the mel. GRR
    # ie. # Error: RuntimeError: Use syntax: FBXExportFileVersion -v FBX202000 | ... or FBXExportFileVersion -q #
    return mel.eval("string $defaultFileVersion = `FBXExportFileVersion - q`;")
