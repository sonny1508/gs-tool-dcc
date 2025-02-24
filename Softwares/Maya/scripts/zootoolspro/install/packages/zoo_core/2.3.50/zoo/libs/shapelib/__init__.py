"""This module holds utility methods for dealing with nurbscurves
"""
import os
import glob

from zoo.libs.utils import filesystem, output
from zoo.core.util import env

if env.isMaya():  # todo Remove this
    from zoo.libs.maya.api import curves

# The shape file extension
SHAPE_FILE_EXT = "shape"
# the shape lib environment variable which specifies all the
# root locations.
SHAPE_LIB_ENV = "ZOO_SHAPE_LIB"
# internal cache of the shape path and data, reducing I/O times
_SHAPELIB_PATH_CACHE = {}  # dict[str,dict[str,str]]


class MissingShapeFromLibrary(Exception):
    pass


def clearShapeCache():
    global _SHAPELIB_PATH_CACHE
    _SHAPELIB_PATH_CACHE.clear()


def _updateCache(force=False):
    global _SHAPELIB_PATH_CACHE
    if _SHAPELIB_PATH_CACHE and not force:
        return

    # pre pass to handle mem cache
    for root in iterShapeRootPaths():
        for shapePath in glob.glob(os.path.join(root, "*.{}".format(SHAPE_FILE_EXT))):
            _SHAPELIB_PATH_CACHE[os.path.splitext(os.path.basename(shapePath))[0]] = {"path": shapePath}


def iterShapeRootPaths():
    """Generator function which iterates the root location based on the
    environment variable "ZOO_LIB_PATH"

    :return: Each  absolute path to each shape root directory.
    :rtype: generator(str)
    """
    for root in os.environ.get(SHAPE_LIB_ENV, "").split(os.pathsep):
        if not os.path.exists(root):
            continue
        yield root


def iterShapePaths():
    """Iterator function which loops all the `*.shape` paths.

    :return: Generator  with each element == absolute path.shape
    :rtype: generator(str)
    """
    _updateCache()
    for shapeInfo in _SHAPELIB_PATH_CACHE.values():
        yield shapeInfo["path"]


def iterAvailableShapesNames():
    """Generator function for looping over all available shape names

    Shapes are sourced from all the set root locations specified by the
    "ZOO_LIB_PATH" environment variable

    :return: An Iterate which returns each shape Name
    :rtype: Generator(str)
    """
    _updateCache()
    for i in _SHAPELIB_PATH_CACHE.keys():
        yield i


def shapeNames():
    """List all the curve shapes (design/patterns) available.

    Shapes are sourced from all the set root locations specified by the
    "ZOO_LIB_PATH" environment variable

    :return shapeNames: a list of curve designs (strings) available
    :rtype shapeNames: list(str)
    """
    return list(iterAvailableShapesNames())


def findShapePathByName(shapeName):
    """Find's the absolute shape path based on the shape name

    ..code-block: python

        shapePath = findShapePathByName("cube")
        # result: rootFolder\zoo\libs\shapelib\__init__.py

    :param shapeName: The shape name to find. eg. "cube"
    :type shapeName: str
    :return: The absolute shape path
    :rtype: str
    """
    _updateCache()
    if _SHAPELIB_PATH_CACHE:
        return _SHAPELIB_PATH_CACHE.get(shapeName, {}).get("path")


def loadFromLib(shapeName):
    """Loads the data for the given shape Name

    :param shapeName: The shape name from the library, excluding the extension, see shapeNames()
    :type shapeName: str
    :return: A 2 tuple the first element is the MObject of the parent and the second is a list \
    of mobjects represents the shapes created.

    :rtype: tuple[:class:`om2.MObject, list(:class:`om2.MObject`))
    :raises: ValueError
    """
    _updateCache()
    info = _SHAPELIB_PATH_CACHE.get(shapeName)
    if not info:
        raise MissingShapeFromLibrary("The shape name '{}' doesn't exist in the library".format(shapeName))
    data = info.get("data")
    if not data:
        data = filesystem.loadJson(info["path"])
        info["data"] = data
    return data


def loadAndCreateFromLib(shapeName, parent=None, mod=None):
    """Load's and create's the nurbscurve from the shapelib.  If parent will shape node parent to the given object

    TODO: should combine zoo_preferences and zoo internal directories

    :param shapeName: the shape library name.
    :type shapeName: str
    :param parent: the parent for the nurbscurve default is None.
    :type parent: maya.api.OpenMaya.MObject
    :return: A 2 tuple the first element is the MObject of the parent and the second is a list \
    of mobjects represents the shapes created
    :rtype: tuple(MObject, list(MObject))
    """
    newData = loadFromLib(shapeName)
    return curves.createCurveShape(parent, newData,
                                   mod=mod)  # todo move these out of zoo_core or get createCurveShape app agnostic


def loadShape(shapeName, folderPath):
    """ Loads the shape with the provided shapeName and folderPath.

    :note: This doesn't update the mem-cache.

    :param shapeName: The name of the shape ie. "circle"
    :type shapeName: str
    :param folderPath: The fully qualified folder path.
    :type folderPath: str
    :return: The raw shape data.
    :rtype: dict
    """
    shapePath = os.path.join(folderPath, ".".join([shapeName, SHAPE_FILE_EXT]))
    newData = filesystem.loadJson(shapePath)
    return newData


def loadAndCreateFromPath(shapeName, folderPath, parent=None):
    """Load's and creates the nurbs curve from the design name and specific folder path.
    If parent will shape node parent to the given object

    TODO: should combine zoo_preferences and zoo internal directories

    :param shapeName: The shape name.
    :type shapeName: str
    :param folderPath: The folder path of the .shape file
    :type folderPath: str
    :param parent: the parent for the nurbs curve default is None.
    :type parent: maya.api.OpenMaya.MObject
    :return: A 2 tuple the first element is the MObject of the parent and the second is a list \
    of mobjects represents the shapes created
    :rtype: tuple(MObject, list(MObject))
    """
    newData = loadShape(shapeName, folderPath)
    return curves.createCurveShape(parent,
                                   newData)  # todo move these out of zoo_core or get createCurveShape app agnostic


def saveToLib(node, name, override=True, saveMatrix=False):
    """Save's the current transform node shapes to the zoo library
    Uses the default first SHAPE_LIB_ENV location as the directory:

    :param node: The MObject to the transform that you want to save
    :type node: MObject
    :param name: The name of the file to create, if not specified the node name will be used, usually the design name
    :type name: str
    :param override: Whether to force override the library shape file if it exists.
    :type override: bool
    :param saveMatrix: If True save the matrix information. On import can override matching, usually matrix not wanted.
    :type saveMatrix: bool
    :return: The file path to the newly created shape file
    :rtype: str
    """
    directory = os.environ.get(SHAPE_LIB_ENV, "").split(os.pathsep)[0]
    return saveToDirectory(node, name, directory, override=override, saveMatrix=saveMatrix)


def saveToDirectory(node, name, directory, override=True, saveMatrix=False):
    """Saves the current transform node shapes to a directory path

    :param node: The MObject to the transform that you want to save
    :type node: MObject
    :param name: The name of the file to create, if not specified the node name will be used, usually the design name
    :type name: str
    :param directory: The directory folder to save into
    :type directory: str
    :param saveMatrix: If True save the matrix information. On import can override matching, usually matrix not wanted.
    :type saveMatrix: bool
    :return: The file path to the newly created shape file
    :rtype: str

    .. code-block:: python

        nurbsCurve = cmds.circle()[0]
        # requires an MObject of the shape node
        data, path = saveToDirectory(api.asMObject(nurbsCurve))

    """

    if name is None:
        from zoo.libs.maya.api import nodes  # todo app agnostic
        name = nodes.nameFromMObject(node, True, False)
    if not name.endswith(".{}".format(SHAPE_FILE_EXT)):
        name = ".".join([name, SHAPE_FILE_EXT])
    # if we don't want to override raise an error if there's a conflict in naming
    if not override and name in shapeNames():
        raise ValueError("name-> {} already exists in the shape library!".format(name))
    # serialize all the child shapes straight to a dict
    data = curves.serializeCurve(node)
    if not saveMatrix:  # remove the matrix key and info, usually not wanted, see docs
        for curveShape in data:
            data[curveShape].pop("matrix", None)
    path = os.path.join(directory, name)
    filesystem.saveJson(data, path)
    _SHAPELIB_PATH_CACHE[os.path.splitext(name)[0]] = {"path": path,
                                                       "data": data}

    return data, path


def deleteShapeFromLib(shapeName, message=True):
    """Deletes a shape from the internal zoo library.  Deletes the file on disk.

    TODO: replace maya displayMessages with logging and create a maya log handler

    :param shapeName: The name of the shape without the extension.  Eg "circle" deletes "path/circle.shape"
    :type shapeName: str
    :param message: Report the message to the user?
    :type message: bool
    :return fileDeleted: If the file was deleted return True
    :rtype fileDeleted: bool
    """
    shapePath = findShapePathByName(shapeName)
    if not shapePath:
        if message:
            output.displayWarning("The file could not be deleted, it does not exist.")
        return False
    # delete
    os.remove(shapePath)
    if shapeName in _SHAPELIB_PATH_CACHE:
        del _SHAPELIB_PATH_CACHE[shapeName]
    if message:
        output.displayInfo("The Curve `{}` has been deleted from the Zoo Library".format(shapeName))
    return True


def renameLibraryShape(shapeName, newName, message=True):
    """Renames a shape from the internal zoo library.  Renames the file on disk.

    TODO: replace messages with a maya log handler

    :param shapeName: The name of the shape without the extension.  Eg "circle" deletes "path/circle.shape"
    :type shapeName: str
    :param newName: The new name of the shape.  Should not have the file extension.  eg. "star_05"
    :type newName: str
    :param message: Report the message to the user?
    :type message: bool
    :return newPath: the full path of the file now renamed.  Empty string if could not be renamed
    :rtype newPath: str
    """
    shapePath = findShapePathByName(shapeName)

    if not os.path.exists(shapePath):  # if not current path exists
        if message:
            output.displayWarning("File not found: `{}`".format(shapePath))
        return ""
    newPath = os.path.join(os.path.dirname(shapePath), ".".join([newName, SHAPE_FILE_EXT]))
    # can't rename as new name already exists
    if os.path.exists(newPath):
        if message:
            output.displayWarning("Cannot rename, new filename already exists: `{}`".format(newPath))
        return ""
    os.rename(shapePath, newPath)
    oldData = _SHAPELIB_PATH_CACHE.get(shapeName)
    oldData["path"] = newPath
    _SHAPELIB_PATH_CACHE[newName] = oldData
    del _SHAPELIB_PATH_CACHE[shapeName]
    if message:
        output.displayInfo("Success: Filename `{}` renamed to `{}`".format(shapePath, newPath))
    return newPath
