from zoo.core.util import pathutils
import warnings

warnings.warn("zoo.libs.utils.path is deprecated, use zoo.core.util.pathutils instead", DeprecationWarning)

findFirstInPaths = pathutils.findFirstInPaths
findFirstInEnv = pathutils.findFirstInEnv
findFirstInPath = pathutils.findFirstInPath
findInPyPath = pathutils.findInPyPath
iterParents = pathutils.iterParents
relativeTo = pathutils.relativeTo
filesInDirectory = pathutils.filesInDirectory
filesByExtension = pathutils.filesByExtension
directories = pathutils.directories
getExtension = pathutils.getExtension
getFilesNoExt = pathutils.getFilesNoExt
getTexturesNames = pathutils.getTexturesNames
patchFromUdim = pathutils.patchFromUdim
udimFromPatch = pathutils.udimFromPatch
getFrameSequencePath = pathutils.getFrameSequencePath
getFileNameNoExt = pathutils.getFileNameNoExt
getVersionNumber = pathutils.getVersionNumber
getVersionNumberAsStr = pathutils.getVersionNumberAsStr
getImageNoExtension = pathutils.getImageNoExtension
isImage = pathutils.isImage
imageSupportByQt = pathutils.imageSupportByQt
withExtension = pathutils.withExtension
normpath = pathutils.normpath