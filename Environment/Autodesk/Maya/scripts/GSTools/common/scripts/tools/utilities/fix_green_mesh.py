"""Repair a Maya ASCII (.ma) file whose mesh data contains 'nan(ind)' values
(which show up as green / lost meshes) by replacing them with 0."""
import re
import os
import maya.cmds as cmds


def search_delete_nan(file_path):
    with open(file_path, 'r') as fh:
        file_content = fh.read()

    new_content = re.sub(r'nan\(ind\)', '0', file_content)

    if new_content == file_content:
        cmds.confirmDialog(title='Error', message="Error, MA file can't fix.", button=['OK'])
        return False

    file_name, file_ext = os.path.splitext(file_path)
    new_file_path = file_name + '_fixed' + file_ext
    with open(new_file_path, 'w') as fh:
        fh.write(new_content)

    cmds.confirmDialog(title='Success',
                       message='MA file fixed. Saved as:\n{}'.format(new_file_path),
                       button=['OK'])
    return True


def open_file(*args):
    file_path = cmds.fileDialog2(fileMode=1, caption="Select .ma file to open",
                                 fileFilter='Maya ASCII (*.ma)')
    if file_path:
        search_delete_nan(file_path[0])


def run():
    open_file()
