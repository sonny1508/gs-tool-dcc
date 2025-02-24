from zoo.libs.pyqt.extended.imageview import model
from zoo.libs.zooscene import zooscenefiles


class HdrSkydomeViewerModel(model.MiniBrowserFileModel):

    def __init__(self, view, directories, chunkCount=0, uniformIcons=False, assetPreference=None):
        """Loads skydome model data from a directory for a ThumbnailView widget
        Pulls thumbnails which are in dependency directories and tooltips are generated from the zooInfo files.

        Uses model.FileModel as a base class and overrides skydome related code, see more documentation at:
            zoo.libs.pyqt.extended.imageview.model.FileModel()

        :param view: The viewer to assign this model data?
        :type view: qtWidget?
        :param chunkCount: The number of images to load at a time into the ThumbnailView widget
        :type chunkCount: int
        """

        super(HdrSkydomeViewerModel, self).__init__(view, extensions=assetPreference.fileTypes,
                                                    directories=directories, chunkCount=chunkCount,
                                                    uniformIcons=uniformIcons, assetPref=assetPreference)

    def updateItems(self):
        """

        :return:
        """
        super(HdrSkydomeViewerModel, self).updateItems()
        moveToEnd = []
        for i, f in enumerate(self.fileItems):
            f.thumbnail = zooscenefiles.thumbnail(f.fileNameExt(), f.directory)
            if f.fileName.startswith("braverabbit_"):
                moveToEnd.append(i)

        # Move braverabbit items to the end
        for it in reversed(moveToEnd):
            self.fileItems.append(self.fileItems.pop(it))

        # Update the metadata
        for f in self.fileItems: # todo maybe use zooSceneModel instead?
            # f.metadata = zooscenefiles.infoDictionary(f.fileNameExt(), f.directory)
            f.thumbnail = zooscenefiles.thumbnail(f.fileNameExt(), f.directory)
