"""Snap selected vertices to the nearest vertex, or to the midpoint between
the selection and the nearest vertex."""
import math
import maya.cmds as cmds


def get_distance(p1, p2):
    length = math.sqrt(math.pow(p1[0] - p2[0], 2) +
                       math.pow(p1[1] - p2[1], 2) +
                       math.pow(p1[2] - p2[2], 2))
    return float('%.5f' % length)


def center_2_point(p1, p2):
    return [(p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2, (p1[2] + p2[2]) / 2]


def snap_to_nearest(center=False):
    dic_test = {}
    vert_pos = {}
    sel = cmds.ls(sl=True, fl=True)
    check = cmds.nodeType(sel[len(sel) - 1])
    vtx_list = []
    vtx_list_s = {}
    source = None
    if check == 'transform':
        source = sel.pop(len(sel) - 1)
        vert_count = cmds.polyEvaluate(source, v=True)
        for i in range(0, vert_count, 1):
            vtx_list.append("{0}.vtx[{1}]".format(source, i))
    elif check == 'mesh':
        objso = cmds.listRelatives(sel[0], p=True, f=True)[0].split('|')[1]
        vert_count = cmds.polyEvaluate(objso, v=True)
        for i in range(0, vert_count, 1):
            vtx_index = "{0}.vtx[{1}]".format(objso, i)
            if vtx_index in sel:
                pass
            else:
                vtx_list.append(vtx_index)
    for s in sel:
        p1 = cmds.xform(s, q=True, ws=True, t=True)
        for i in range(0, len(vtx_list), 1):
            p2 = cmds.xform(vtx_list[i], q=True, ws=True, t=True)
            if center is False:
                vert_pos[vtx_list[i]] = p2
            else:
                vert_pos[vtx_list[i]] = center_2_point(p2, p1)
            dic_test[vtx_list[i]] = get_distance(p1, p2)
        min_val = min(dic_test.values())
        target_n = [k for k, v in dic_test.items() if v == min_val]
        target_p = [v for k, v in vert_pos.items() if target_n[0] == k][0]
        vtx_list_s[target_n[0]] = target_p
        cmds.xform(s, ws=True, t=target_p)
    for k, v in vtx_list_s.items():
        cmds.xform(k, ws=True, t=v)
    try:
        if source:
            cmds.select(source, d=True)
    except Exception:
        pass


def run():
    win_name = 'SnapTools'
    if cmds.window(win_name, q=True, ex=True):
        cmds.deleteUI(win_name)
    cmds.window(win_name, rtf=True, mnb=False, mxb=False)
    rowcol = cmds.rowColumnLayout(p=win_name, nc=2)
    cmds.button(p=rowcol, l="Snap To Vertex", c=lambda *a: snap_to_nearest())
    cmds.button(p=rowcol, l="Snap To Center", c=lambda *a: snap_to_nearest(center=True))
    cmds.showWindow(win_name)
