import os

from zoo.libs.pyqt.extended.imageview.model import MiniBrowserFileModel
from zoo.libs.zooscene import zooscenefiles
from zoo.libs.zooscene.constants import ZOOSCENE_EXT


class ZooSceneModel(MiniBrowserFileModel):
    def __init__(self, view, directories=None, chunkCount=0, uniformIcons=False,
                 assetPreference=None, extensions=None):
        """Loads .zooscene model data from a directory for a ThumbnailView widget

        Pulls thumbnails which are in dependency directories and tooltips are generated from the file.zooInfo files.

        Also see the inherited class FileModel() in zoo_pyside for more functionality and documentation.:
            zoo.libs.pyqt.extended.imageview.model.FileModel()

        This class can be overridden further for custom image loading in subdirectories such as Skydomes or Controls \
        which use the .zooScene tag and thumbnail information.

        :param view: The viewer to assign this model data?
        :type view: qtWidget?
        :param directories: The directory full path where the .zooScenes live
        :type directories: list[str] or list[DirectoryPath]
        :param chunkCount: The number of images to load at a time into the ThumbnailView widget
        :type chunkCount: int
        """
        extensions = extensions or [ZOOSCENE_EXT]
        super(ZooSceneModel, self).__init__(view, extensions=extensions,
                                            directories=directories, chunkCount=chunkCount,
                                            uniformIcons=uniformIcons,
                                            assetPref=assetPreference)

    def updateItems(self):
        super(ZooSceneModel, self).updateItems()
        # Update the metadata
        for f in self.fileItems:
            f.metadata = zooscenefiles.infoDictionary(f.fileNameExt(), f.directory)
            newThumb = zooscenefiles.thumbnail(f.fileNameExt(), f.directory)

            if newThumb is None:
                dep = zooscenefiles.getDependencyFolder(f.fullPath(), create=True)[0]
                thumbPath = os.path.join(dep, "thumbnail")
                f.thumbnail = self.checkFileImage(thumbPath)

            else:
                f.thumbnail = zooscenefiles.thumbnail(f.fileNameExt(), f.directory)

    def checkFileImage(self, filePath):
        """ Checks the jpg or png exists for the filePath.

        :param filePath: File path with the extension excluded.
        :return:
        """
        jpg = filePath + ".jpg"
        png = filePath + ".png"
        if os.path.exists(jpg):
            return jpg
        elif os.path.exists(png):
            return png
        return png
