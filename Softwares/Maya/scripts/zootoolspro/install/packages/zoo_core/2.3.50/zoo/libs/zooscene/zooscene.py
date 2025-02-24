import glob
import os
from os import path

from zoo.libs.general.exportglobals import ZOOSCENESUFFIX, VERSIONKEY, GENERICVERSIONNO, SHADERS, LIGHTS, AREALIGHTS, \
    IBLSKYDOMES, MESHOBJECTS
from zoo.libs.utils import path, filesystem, output
from zoo.libs.zooscene import constants
from zoo.libs.zooscene.constants import DEPENDENCY_FOLDER, ZOO_THUMBNAIL, ASSETTYPES, INFOASSET, INFOCREATORS, \
    INFOWEBSITES, INFOTAGS, INFODESCRIPTION


class ZooScene(object):
    def __init__(self, path=None, extension=ZOOSCENESUFFIX):
        """

        :param path:
        """
        self.path = path
        self.extension = extension

        # Info
        self.assetType = ""
        self.animation = None
        self.description = ""
        self.version = "1.0.0"
        self.tags = ""
        self.creators = ""
        self.saved = []
        self.websites = ""

    def dependencyFolder(self, create=True):
        """ Get the dependency folder the .zooscene files

        - These can contain .abc, .info, .obj, .fbx, textures etc

        :param create: Create if doesn't exist
        :type create: bool
        :return fullDirPath: the full directory path to the new folder
        :rtype fullDirPath: str
        """
        zooSceneFileName = os.path.basename(self.path)
        directoryPath = os.path.dirname(self.path)
        fileNameNoExt = os.path.splitext(zooSceneFileName)[0]
        extension = path.getExtension(self.path)
        newDirectory = "_".join([fileNameNoExt, extension, constants.DEPENDENCY_FOLDER])
        fullDirPath = os.path.join(directoryPath, newDirectory)

        # Create the dependency folder if it doesnt exist
        if create and not os.path.exists(fullDirPath):  # doesn't already exist
            os.makedirs(fullDirPath)
        return fullDirPath, fileNameNoExt

    def directory(self):
        return os.path.dirname(self.path)

    def fileName(self):
        return os.path.basename(self.path)

    def fileNameNoExt(self):
        return os.path.splitext(self.fileName())[0]

    def dependencyFiles(self, ignoreThumbnail=False):
        """ Retrieve a list of all files in the dependency directory DIRECTORYNAMEDEPENDENCIES
        Files do not have full path so directory path is also returned,
        files are ["fileName.abc", "fileName.zooInfo"] etc

        :param ignoreThumbnail: ignores the files called thumbnail.* useful for renaming
        :type ignoreThumbnail: str
        :return fileDependencyList: list of short name files found in the subdirectory DIRECTORYNAMEDEPENDENCIES
        :rtype fileDependencyList: list
        :return fullDirPath: the full path of the sub directory DIRECTORYNAMEDEPENDENCIES
        :rtype fullDirPath: str
        """
        fileDependencyList = list()
        fileNameNoExt = os.path.splitext(self.fileName())[0]
        ext = path.getExtension(self.path)

        newDirectory = "_".join([fileNameNoExt, ext, constants.DEPENDENCY_FOLDER])
        fullDirPath = os.path.join(self.directory(), newDirectory)
        if not os.path.exists(fullDirPath):  # doesn't already exist
            return fileDependencyList, ""  # return empty as directory doesn't exist
        globPattern = os.path.join(fullDirPath, fileNameNoExt)
        for fileName in glob.glob("{}.*".format(globPattern)):
            fileDependencyList.append(fileName)
        if not ignoreThumbnail:
            for fileName in glob.glob(os.path.join(fullDirPath, "thumbnail.*")):
                fileDependencyList.append(fileName)

        return fileDependencyList, fullDirPath

    def thumbnailPath(self):
        """ Gets the thumbnail path, usually in the dependency folder

        :return:
        """
        fileNameNoExt = self.fileNameNoExt()
        dependFolder = "_".join([fileNameNoExt, self.extension, DEPENDENCY_FOLDER])
        dependFolderPath = os.path.join(self.directory(), dependFolder)
        if not os.path.isdir(dependFolderPath):
            return None

        files, dirPath = self.dependencyFiles()
        length = len(ZOO_THUMBNAIL)
        for f in files:
            if ZOO_THUMBNAIL in f and f[:length] == ZOO_THUMBNAIL and path.imageSupportByQt(os.path.join(dirPath, f)):
                return f

    def getZooFiles(self, ignoreThumbnail=False):
        """ Retrieves all zoo files related to the given file (usually .zooscene).

        Expects .zooscene file but can be any file under the main folder that has file dependencies

        returns only filenames not the directory path

        :param filePath: full path of a .zooscene file or a file in the main folder
        :type filePath: basestring
        :param ignoreThumbnail: ignores the files called thumbnail.* useful for renaming
        :type ignoreThumbnail: str
        :return relatedFiles, subDir: all files related to the .zooscene in the current directory as string paths, and the dependency subdirectory
        :rtype relatedFiles: tuple(list[basestring], basestring)
        """
        relatedFiles = [self.path]
        fileDependencyList, subDir = self.dependencyFiles(ignoreThumbnail=ignoreThumbnail)
        # todo get files based on extension
        for fileName in fileDependencyList:
            relatedFiles.append(os.path.join(subDir, fileName))
        return relatedFiles, subDir  # todo create ZooScene object for each one

    def getSingleFileFromZooScene(self, fileExtension):
        """ Check if file exists in zooScene dependencies

        Returns the name of the file if it exists given the extension eg .abc from the zooSceneFullPath
        Gets all the files in the subdirectory associated with the .zooScene file and filters for the file type
        Supports returning of one file, the first it finds so not appropriate for textures


        :param fileExtension:  the file extension to find no ".", so alembic is "abc"
        :type fileExtension: str
        :return extFileName: the filename (no directory) of the extension given > for example "myFileName.abc"
        :rtype extFileName: str
        """

        extFileName = ""
        fileList, directory = self.dependencyFiles()
        if not directory:
            return extFileName
        for fileName in fileList:  # cycle through the files and find if a match with the extension
            if fileName.lower().endswith(fileExtension.lower()):
                return os.path.join(directory, fileName)
        return extFileName

    def createTagInfoDict(self, assetType, creator, website, tags, description, saveInfo, animInfo):
        """ Creates a dict ready for the zooInfo file

        :param assetType: the information about asset type, model, scene, lights, shaders, etc
        :type assetType: str
        :param creator: the information about creator/s
        :type creator: str
        :param website: the information about the creators website links
        :type website: str
        :param tags: the tag information
        :type tags: str
        :param description: the full description
        :type description: str
        :param saveInfo: the file information saved as a list ["alembic", "generic lights"] etc
        :type saveInfo: list
        :param animInfo: the animation information of the file "0 100" or "" or None if none
        :type animInfo: str
        :return zooInfoDict: the dict containing all information including the file version number
        :rtype zooInfoDict: str
        """
        zooInfoDict = {constants.INFOASSET: assetType,
                       constants.INFOCREATORS: creator,
                       constants.INFOWEBSITES: website,
                       constants.INFOTAGS: tags,
                       constants.INFODESCRIPTION: description,
                       constants.INFOSAVE: saveInfo,
                       constants.INFOANIM: animInfo,
                       VERSIONKEY: GENERICVERSIONNO}
        return zooInfoDict

    def updateZooInfo(self, assetType=ASSETTYPES[0], creator="", website="", tags="", description="",
                      saveInfo="", animInfo=""):
        """Updates the .zooInfo file depending on the incoming values, if not variable then leave the values as are.

        :param zooSceneFullPath: the full path of the zooScene file, this will save out as another file zooInfo
        :type zooSceneFullPath: str
        :param assetType: the information about asset type, model, scene, lights, shaders, etc
        :type assetType: str
        :param creator: the information about creator/s
        :type creator: str
        :param website: the information about the creators website links
        :type website: str
        :param tags: the tag information
        :type tags: str
        :param description: the full description
        :type description: str
        :param saveInfo: the file information saved as a list ["alembic", "generic lights"] etc
        :type saveInfo: list
        :param animInfo: the animation information of the file "0 100" or "" or None if none
        :type animInfo: str
        :return zooInfoFullPath: the full path of the .zooInfo file
        :rtype zooInfoFullPath: str
        :return zooInfoDict: the dict containing all information including the file version number
        :rtype zooInfoDict: str
        """
        # find if the .zooInfo file exists
        zooInfoDict, fileFound = self.getZooInfoFromFile(message=True)
        # if it does get the current information
        if not fileFound:
            zooInfoDict = self.createTagInfoDict(assetType, creator, website, tags, description, saveInfo, animInfo)
        else:
            if assetType != ASSETTYPES[0]:  # if not default "Not Specified"
                zooInfoDict[constants.INFOASSET] = assetType
            if creator:
                zooInfoDict[constants.INFOCREATORS] = creator
            if website:
                zooInfoDict[constants.INFOWEBSITES] = website
            if tags:
                zooInfoDict[constants.INFOTAGS] = tags
            if description:
                zooInfoDict[constants.INFODESCRIPTION] = description
            if saveInfo:
                zooInfoDict[constants.INFODESCRIPTION] = saveInfo
            if animInfo:
                zooInfoDict[constants.INFODESCRIPTION] = animInfo
        # save the updated dict
        zooInfoFullPath = self.writeZooInfo(zooInfoDict[constants.INFOASSET],
                                            zooInfoDict[constants.INFOCREATORS],
                                            zooInfoDict[constants.INFOWEBSITES], zooInfoDict[constants.INFOTAGS],
                                            zooInfoDict[constants.INFODESCRIPTION],
                                            zooInfoDict[constants.INFOSAVE], zooInfoDict[constants.INFOANIM],
                                            message=False)
        return zooInfoFullPath, zooInfoDict

    def writeZooInfo(self, assetType, creator, website, tags, description, saveInfo, animInfo,
                     message=True):
        """Saves a zooInfo file in the subdirectory from the zooScene file

        :param zooSceneFullPath: the full path of the zooScene file, this will save out as another file zooInfo
        :type zooSceneFullPath: str
        :param assetType: the information about asset type, model, scene, lights, shaders, etc
        :type assetType: str
        :param creator: the information about creator/s
        :type creator: str
        :param website: the information about the creators website links
        :type website: str
        :param tags: the tag information
        :type tags: str
        :param description: the full description
        :type description: str
        :param saveInfo: the save info list, what did the file save?
        :type saveInfo: list
        :param animInfo:
        :type animInfo:
        :param message: report the save success message to the user?
        :type message: bool

        :return zooInfoFullPath: the full path of the file saved (zooInfo)
        :rtype zooInfoFullPath:
        """
        zooInfoDict = self.createTagInfoDict(assetType, creator, website, tags, description, saveInfo, animInfo)
        fullDirPath, fileNameNoExt = self.dependencyFolder()
        zooInfoFileName = ".".join([fileNameNoExt, constants.ZOO_INFO_EXT])
        zooInfoFullPath = os.path.join(fullDirPath, zooInfoFileName)
        filesystem.saveJson(zooInfoDict, zooInfoFullPath, indent=4, separators=(",", ":"), message=False)
        return zooInfoFullPath

    def getZooInfoFromFile(self, message=True):
        """Gets other files from the .zooScene, for example .zooInfo from a file on disk

        :param zooSceneFullPath: the full path of the zooScene file, this will save out as another file zooInfo
        :type zooSceneFullPath: str
        :return zooInfoDict: the dictionary with all info information, if None the file wasn't found
        :rtype zooInfoDict: dict
        :return fileFound: was the zooInfo file found?
        :rtype fileFound: bool
        """
        zooInfoPath = self.getSingleFileFromZooScene(constants.ZOO_INFO_EXT)
        if not os.path.exists(zooInfoPath):  # doesn't exist
            if message:
                output.displayWarning("ZooInfo File Not Found")
            fileFound = False
            return self.createTagInfoDict(ASSETTYPES[0], "", "", "", "", "",
                                     ""), fileFound  # return the empty dict as no file found
        fileFound = True
        return filesystem.loadJson(zooInfoPath), fileFound  # returns zooInfoDict

    def deleteDependencies(self, keepThumbnailOverride=False, message=True):
        """Deletes zoo file dependencies and the .zooScene leaving the subDirectory, deletes the actual files on disk.
        Useful for saving over existing files

        :param message: report the message to the user in Maya?
        :type message: bool
        :param keepThumbnailOverride: keeps the existing thumbnail image if over righting, usually for delete when renaming
        :type keepThumbnailOverride: bool
        :return filesFullPathDeleted: The files deleted
        :rtype filesFullPathDeleted: list
        """
        deletedPaths = list()  # List of file paths that were deleted
        # get all the files to be renamed and the subDir
        paths, directory = self.getZooFiles(ignoreThumbnail=keepThumbnailOverride)
        if filesystem.checkWritableFile(directory) or filesystem.checkWritableFiles(paths):
            if message:
                output.displayWarning("This scene cannot be written at this time as it's most like in use by Maya or "
                                      "another program")
            return
        if len(paths) > 100:
            output.displayWarning("This function is deleting more than 100 files!! "
                                  "something is wrong, check the files in dir `{}`".format(directory))
            return
        for fileFullPath in paths:
            os.remove(fileFullPath)
            deletedPaths.append(fileFullPath)
        return deletedPaths

    def delete(self, message=True, keepThumbnailOverride=False):
        """Deletes a file and it's related dependencies on disk, usually a .zooScene but can have any extension

        The full file path of the file to be deleted, dependency files are deleted automatically

        :param message: report the message to the user in Maya?
        :type message: bool
        :param keepThumbnailOverride: If True will skip the thumbnail image deletion. Used while renaming.
        :type keepThumbnailOverride: bool
        :return filesFullPathDeleted: The files deleted in the format of absolute paths
        :rtype filesFullPathDeleted: list
        """
        deletedFiles = list()
        # get all the files to be renamed and the subDir
        zooPaths, dependencyDir = self.getZooFiles()
        if keepThumbnailOverride:
            if "thumbnail.jpg" in zooPaths:
                zooPaths.remove("thumbnail.jpg")
            if "thumbnail.png" in zooPaths:
                zooPaths.remove("thumbnail.png")
        if not dependencyDir:  # there's no subdirectory so just delete the file and return it
            # doesn't need a check as it should be deletable
            os.remove(self.path)
            deletedFiles.append(self.path)
            return deletedFiles
        # check the files and dir file-permissions, rename of itself to the same name, returns true if not writable
        if filesystem.checkWritableFile(dependencyDir) or filesystem.checkWritableFiles(zooPaths):
            if message:
                output.displayWarning("This scene cannot be deleted/renamed as it's most like in use by Maya or "
                                      "another program")
            return
        if len(zooPaths) > 20:
            output.displayWarning("This function is deleting more than 20 files!! "
                                  "something is wrong, check the files in dir `{}`".format(dependencyDir))
            return
        for fileFullPath in zooPaths:
            os.remove(fileFullPath)
            deletedFiles.append(fileFullPath)
        # delete subdir
        if not keepThumbnailOverride:
            os.rmdir(dependencyDir)
        deletedFiles.append(dependencyDir)
        return deletedFiles

    def updateZooSceneDir(self, directory):
        """Updates .zoo Scenes from pre v1 format where generic light and shader data was saved inside the .zooScene
        Will batch all .zooScene files in the given directory and fix them from the old format

        :param directory:
        :type directory:
        """
        # get a list of the .zooScenes
        zooSceneList = list()
        for fileName in glob.glob("{}/*.{}".format(directory, ZOOSCENESUFFIX)):
            zooSceneList.append(fileName)
        # start loop
        for zooScene in zooSceneList:
            zooSceneFullPath = os.path.join(directory, zooScene)
            zooSceneDict = filesystem.loadJson(zooSceneFullPath)
            if SHADERS in zooSceneDict:
                shaderDict = zooSceneDict[SHADERS]
            else:
                shaderDict = dict()
            lightDict = zooSceneDict[LIGHTS]
            # see if the directory dependancies exists if not create it
            getDependencyFolder(zooSceneFullPath)
            # create the shader dict and the light dict files if they exists
            if lightDict[AREALIGHTS] or lightDict[IBLSKYDOMES]:
                # create the light dict
                writeZooGLights(lightDict, zooSceneFullPath)
            if shaderDict:
                # create the shader dict
                writeZooGShaders(shaderDict, zooSceneFullPath)
            # remove the shader and light dicts
            zooSceneDict.pop(SHADERS, None)
            zooSceneDict.pop(LIGHTS, None)
            filesystem.saveJson(zooSceneDict, zooSceneFullPath, indent=4, separators=(",", ":"))

    def writeExportZooInfo(self, zooSceneDict, gShaderDict, gLightDict, objectRootList, tagInfoDict,
                           animationInfo):
        """While exporting writes the .zooInfo file
        Should add cameras

        :param zooSceneDict: the dictionary that will be written to the .zooScene
        :type zooSceneDict: dict
        :param objectRootList: the scene roots from alemebic
        :type objectRootList: list
        :param tagInfoDict: the tag info if provided ok if it's empty, this will be written
        :type tagInfoDict: dict
        :return zooInfoFullPath: the full path to the zooInfo file
        :rtype zooInfoFullPath: str
        :return fileInfoSaved: the info list with what was saved
        :rtype fileInfoSaved: list
        """
        fileInfoSaved = list()
        if objectRootList:
            fileInfoSaved.append(constants.SAVE_ALEMBIC)
        if gShaderDict:
            fileInfoSaved.append(constants.SAVE_G_SHADERS)
        if gLightDict:
            fileInfoSaved.append(constants.SAVE_LIGHTS)
        if MESHOBJECTS in zooSceneDict:
            if zooSceneDict[MESHOBJECTS]:
                fileInfoSaved.append(constants.SAVE_MESH)
        if not tagInfoDict:  # create an empty dict to pass in
            # ASSETTYPES[0] is "Not Specified"
            tagInfoDict = self.createTagInfoDict(ASSETTYPES[0], "", "", "", "", "", "")
        zooInfoFullPath = self.writeZooInfo(tagInfoDict[INFOASSET], tagInfoDict[INFOCREATORS],
                                            tagInfoDict[INFOWEBSITES], tagInfoDict[INFOTAGS],
                                            tagInfoDict[INFODESCRIPTION],
                                            fileInfoSaved, animationInfo)
        return zooInfoFullPath, fileInfoSaved


class ZooSceneLights(ZooScene):

    def writeZooGLights(self, zooLightsDict):
        """Writes a light dict to disk inside the zoo dependency sub folder of the given .zooScene file
        todo subclass

        :param zooLightsDict: the generic lights dictionary
        :type zooLightsDict: dict
        :param zooSceneFullPath: the full path to the zooScene file
        :type zooSceneFullPath: str
        :return zooShadFullPath: the full path to the shader file that has been saved
        :rtype zooShadFullPath: str
        """
        fullDirPath, fileNameNoExt = self.dependencyFolder()
        zooLightsFileName = ".".join([fileNameNoExt, constants.ZOO_LIGHT_EXT])
        zooLightsFullPath = os.path.join(fullDirPath, zooLightsFileName)
        filesystem.saveJson(zooLightsDict, zooLightsFullPath, indent=4, separators=(",", ":"))
        return zooLightsFullPath


class ZooSceneShader(ZooScene):
    def loadGenericShaderLightFiles(self):
        """loads a .zooGShad and .zooGLight information from a zooSceneFullPath
        todo subclass

        :param zooSceneFullPath: the full path to the .zooScene file
        :type zooSceneFullPath: str
        :return shadMultDict: the generic shader dictionary
        :rtype shadMultDict: dict
        :return lightMultDict: the generic light dictionary
        :rtype lightMultDict: dict
        """
        shadMultDict = dict()
        lightMultDict = dict()
        directoryPath = self.dependencyFolder()[0]  # just pull the path and not the filename
        if not directoryPath:  # could not find folder so dicts are empty
            return shadMultDict, lightMultDict
        lightFile = self.getSingleFileFromZooScene(constants.ZOO_LIGHT_EXT)  # the filename only no path
        shaderFile = self.getSingleFileFromZooScene(constants.ZOO_SHADER_EXT)
        if shaderFile:
            shaderFullPath = os.path.join(directoryPath, shaderFile)
            if os.path.isfile(shaderFullPath):
                shadMultDict = filesystem.loadJson(shaderFullPath)
        if lightFile:
            lightFullPath = os.path.join(directoryPath, lightFile)
            if os.path.isfile(lightFullPath):
                lightMultDict = filesystem.loadJson(lightFullPath)
        return shadMultDict, lightMultDict

    def writeZooGShaders(self, zooShaderDict):
        """Writes a shader dict to disk in the zoo dependency sub folder

        :param zooShaderDict: the generic shader dictionary
        :type zooShaderDict: dict
        :param zooSceneFullPath: the full path to the zooScene file
        :type zooSceneFullPath: str
        :return zooShadFullPath: the full path to the shader file that has been saved
        :rtype zooShadFullPath: str
        """
        fullDirPath, fileNameNoExt = self.dependencyFolder()
        zooShadFileName = ".".join([fileNameNoExt, constants.ZOO_SHADER_EXT])
        zooShadFullPath = os.path.join(fullDirPath, zooShadFileName)
        filesystem.saveJson(zooShaderDict, zooShadFullPath, indent=4, separators=(",", ":"))
        return zooShadFullPath
