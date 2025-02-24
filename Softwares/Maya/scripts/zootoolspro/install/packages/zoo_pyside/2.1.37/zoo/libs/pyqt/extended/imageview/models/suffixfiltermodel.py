import os

from zoo.libs.pyqt.extended.imageview import model


class SuffixFilterModel(model.MiniBrowserFileModel):
    def __init__(self, view, extensions, directories=None, activeDirs=None, chunkCount=0, uniformIcons=False,
                 includeSubdir=False, assetPreference=None):
        """ Filters out the suffixes as set by setFilterSuffixList

        :param view:
        :param extensions:
        :param directories:
        :param activeDirs:
        :param chunkCount:
        :param uniformIcons:
        :param includeSubdir:
        """
        super(SuffixFilterModel, self).__init__(view=view, directories=directories, extensions=extensions,
                                                chunkCount=chunkCount, uniformIcons=uniformIcons,
                                                activeDirs=activeDirs,
                                                includeSubdir=includeSubdir, assetPref=assetPreference)

    def updateItems(self):
        """Updates self.fileItems

        """
        super(SuffixFilterModel, self).updateItems()
        for f in self.fileItems:
            filePath = os.path.join(f.directory, f.fileName)
            f.thumbnail = self.checkFileImage(filePath)

    def checkFileImage(self, filePath):
        """ Checks the the jpg or png exists for the filePath.

        :param filePath: File path with the extension excluded.
        :return:
        """
        for i in (".png", ".PNG", ".jpg", ".JPG"):
            if os.path.exists(filePath + i):
                return filePath + i
        return filePath + ".png"
