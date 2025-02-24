from zoovendor.Qt import QtWidgets, QtCore, QtGui
from zoo.preferences.interfaces import coreinterfaces

def getDirectoriesDialog(startingDir):
    """ Create a file dialog with zoo themes and multifile selection

    Returns a list of paths

    :param startingDir:
    :return: eg ["c:/path/to/folder1", "c:/path/to/second/folder"]
    """
    themePref = coreinterfaces.coreInterface()
    fileDialog = QtWidgets.QFileDialog()
    flags = fileDialog.windowFlags()

    fileDialog.setWindowFlags(flags | QtCore.Qt.WindowStaysOnTopHint)

    fileDialog.setDirectory(startingDir)
    if themePref:
        fileDialog.setStyleSheet(themePref.stylesheet().data)

    fileDialog.setFileMode(QtWidgets.QFileDialog.DirectoryOnly)
    fileDialog.setOption(QtWidgets.QFileDialog.DontUseNativeDialog, True)
    file_view = fileDialog.findChild(QtWidgets.QListView, 'listView')

    # to make it possible to select multiple directories:
    if file_view:
        file_view.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
    f_tree_view = fileDialog.findChild(QtWidgets.QTreeView)
    if f_tree_view:
        f_tree_view.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
    if fileDialog.exec_():
        return fileDialog.selectedFiles()
    fileDialog.deleteLater()