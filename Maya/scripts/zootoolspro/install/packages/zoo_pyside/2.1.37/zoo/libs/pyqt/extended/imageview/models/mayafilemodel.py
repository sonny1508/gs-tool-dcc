import os

from zoo.core.util import zlogging

from zoo.libs.pyqt.extended.imageview.models.suffixfiltermodel import SuffixFilterModel
from zoo.libs.utils import filesystem
from zoo.libs.zooscene import zooscenefiles

logger = zlogging.getLogger(__name__)


class MayaFileModel(SuffixFilterModel):

    def __init__(self, view, directories=None, chunkCount=0, uniformIcons=False, assetPreference=None):
        """ Overridden base model to handle loading of the ThumbnailView widget data eg. specific files/images

        This class is the most basic form of the Thumbnail model which is attached to a ThumbnailView

        A directory given and is populated with "png", "jpg", or "jpeg" images.

        Tooltips are also generated from the file names

        This class can be overridden further for custom image loading in subdirectories such as .zooScene files.

        :param view: The viewer to assign this model data?
        :type view: :class:`thumbwidget.ThumbListView`
        :param directories: The directory full path where the .zooScenes live
        :type directories: list[str] or list[DirectoryPath]
        :param chunkCount: The number of images to load at a time into the ThumbnailView widget
        :type chunkCount: int
        :param uniformIcons: False keeps the images non-square.  True the icons will be square, clipped on longest axis
        :type uniformIcons: bool
        """

        extensions = ["ma", "mb"]
        super(MayaFileModel, self).__init__(view=view, directories=directories, extensions=extensions,
                                            chunkCount=chunkCount, uniformIcons=uniformIcons,
                                            includeSubdir=True, assetPreference=assetPreference)
    def updateItems(self):
        """Updates self.fileItems

        """
        super(SuffixFilterModel, self).updateItems()
        # Update the metadata
        for f in self.fileItems:
            dep = zooscenefiles.getDependencyFolder(f.fullPath(), create=False)[0]
            thumbPath = os.path.join(dep, "thumbnail")
            newThumb = self.checkFileImage(thumbPath)
            # upgrade the thumbnail by moving the file to file dependencies folder if possible.
            if not os.path.exists(newThumb):
                legacyThumbnail = self.checkFileImage(os.path.join(f.directory, f.fileName))
                if os.path.exists(legacyThumbnail):
                    with filesystem.MoveFileContext() as FileContext:
                        filesystem.ensureFolderExists(os.path.dirname(newThumb))
                        FileContext.move(legacyThumbnail, newThumb)
            f.thumbnail = newThumb
