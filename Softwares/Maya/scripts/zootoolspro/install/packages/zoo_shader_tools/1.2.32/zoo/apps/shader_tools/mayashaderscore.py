import os

from zoo.libs.maya.cmds.shaders import shaderutils
from zoo.libs.utils import output
from zoo.preferences.interfaces import shaderinterfaces
from zoovendor.Qt.QtCore import QObject


class MayaShadersCore(QObject):
    directory = None

    def __init__(self, toolset):
        self.toolset = toolset
        self.shaderPrefs = shaderinterfaces.shaderInterface()

    def deleteShader(self, item):
        """ Delete shader

        :param item:
        :return:
        """

        if item is None:
            output.displayWarning("Must select a shader.")
            return

        directory = item.directory
        thumbnail = item.thumbnailLookPath() if item.thumbnailExists() else None
        filePath = item.filePath

        os.remove(filePath)
        delPaths = [os.path.normpath(filePath)]
        if thumbnail:
            os.remove(thumbnail)
            delPaths.append(os.path.normpath(thumbnail))

        if len(os.listdir(directory)) == 0:
            os.rmdir(directory)
            delPaths.append(os.path.normpath(directory))


        output.displayInfo("Deleting {}".format(delPaths))

    def saveShader(self, directory, saveType="auto"):
        """ Saves selected shader

        :param directory: The directory to save the shader
        :type directory: str
        :param saveType: "auto" saves ma and if unknown nodes saves mb, "ma" saves .ma and "mb" saves .mb
        :type saveType: str
        """
        return shaderutils.saveSelectedShader(directory, saveType=saveType)
