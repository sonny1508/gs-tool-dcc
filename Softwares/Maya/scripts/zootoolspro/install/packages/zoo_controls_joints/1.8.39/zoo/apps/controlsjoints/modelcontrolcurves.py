import os

from zoo.libs.pyqt.extended.imageview import model
from zoo.libs.zooscene import zooscenefiles

from zoo.apps.controlsjoints.controlsjointsconstants import CONTROL_SHAPE_EXTENSION

# List is backwards
CONTROL_PRIORITY_LIST = ["slider_square_handle",
                         "slider_square",
                         "circle_half_thick",
                         "circle_halved_thick",
                         "bean_4_all",
                         "locator",
                         "arrow_1_thinbev",
                         "arrow_2way_thinbev",
                         "arrow_4way_circle3",
                         "arrow_4way_roundFlat",
                         "pin_tri_fat",
                         "pick_tri_fat",
                         "pear",
                         "pill",
                         "triangle_round",
                         "square_rounded_front",
                         "square_bev",
                         "octagon_bevel",
                         "hex",
                         "circle",
                         "cube",
                         "sphere"]


class ControlCurvesViewerModel(model.MiniBrowserFileModel):
    def __init__(self, view, directories, activeDirs=None, chunkCount=0, uniformIcons=False, assetPreference=None):
        """Loads control shape model data from a directory for a ThumbnailView widget
        Pulls thumbnails which are in dependency directories and tooltips are generated from the zooInfo files.

        Uses model.FileModel as a base class and overrides controlshape related code, see more documentation at:
            zoo.libs.pyqt.extended.imageview.models.model.FileModel()

        :param view: The viewer to assign this model data?
        :type view: qtWidget?
        :param chunkCount: The number of images to load at a time into the ThumbnailView widget
        :type chunkCount: int
        """
        super(ControlCurvesViewerModel, self).__init__(view, extensions=[CONTROL_SHAPE_EXTENSION],
                                                       directories=directories, activeDirs=activeDirs,
                                                       chunkCount=chunkCount,
                                                       uniformIcons=uniformIcons, assetPref=assetPreference)

    def updateItems(self):
        """ Updates self.fileItems
        """
        super(ControlCurvesViewerModel, self).updateItems()  # Updates fileItems
        for f in self.fileItems:
            f.thumbnail = zooscenefiles.thumbnail(f.fileNameExt(), f.directory)
