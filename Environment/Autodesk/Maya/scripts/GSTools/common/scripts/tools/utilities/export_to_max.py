"""Export the selected mesh to a .fbx (next to the scene) for 3ds Max."""
import os
import maya.cmds as cmds
import maya.mel as mel


def run():
    # get the selected object
    sel = cmds.ls(sl=True)
    if not sel:
        print("Please select mesh")
        return
    cmds.duplicate()
    root = sel
    p = cmds.listRelatives(sel, parent=True)
    mesh = sel[0]
    mesh = mesh.split('.')[-1]

    if cmds.nodeType(mesh) == 'transform':
        shapes = cmds.listRelatives(mesh, s=True)
        if shapes:
            mesh = shapes[0]
        else:
            return

    if cmds.nodeType(mesh) != 'mesh':
        return

    # select all the hard edges
    cmds.select(mesh)
    cmds.polySelectConstraint(m=3, t=0x8000, sm=1)
    cmds.DetachComponent()
    cmds.polySelectConstraint(disable=True)

    while p and len(p) > 0:
        root = p
        p = cmds.listRelatives(p, parent=True)

    filename = "{0}/{1}.fbx".format(os.path.dirname(cmds.file(q=True, sn=True)), root[0])
    mel.eval('FBXExport -f "{0}" -s'.format(filename))

    cmds.inViewMessage(smg="Exported: {0}".format(filename), pos="midCenter",
                       bkc="0x00000000", fade=True)
    cmds.select(sel, add=True)
    cmds.delete()
