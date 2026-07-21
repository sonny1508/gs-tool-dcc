"""Convert locked vertex normals to soft/hard edges (keeps the smoothing look
while unlocking the normals), with a progress window."""
import math
import maya.cmds as cmds

# Progress-window controls (set up in run()).
_win = None
_text = None
_progress = None


class MBVector(object):
    """Provides 3D vector functionality similar to Maya."""

    def __init__(self, *init_values):
        if len(init_values) == 1:
            self.x = init_values[0][0]
            self.y = init_values[0][1]
            self.z = init_values[0][2]
        else:
            self.x = init_values[0]
            self.y = init_values[1]
            self.z = init_values[2]

    def __add__(self, other):
        return MBVector([self.x + other.x, self.y + other.y, self.z + other.z])

    def __sub__(self, other):
        return MBVector([self.x - other.x, self.y - other.y, self.z - other.z])

    def __mul__(self, scalar):
        return MBVector([self.x * scalar, self.y * scalar, self.z * scalar])

    def mag(self):
        return math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z)


def _step_progress(step1):
    if _win and cmds.window(_win, q=True, ex=True):
        cmds.progressBar(_progress, edit=True, progress=step1 + 1)


def _set_max(val):
    if _win and cmds.window(_win, q=True, ex=True):
        if val == 0:
            val = 1
        cmds.progressBar(_progress, edit=True, maxValue=val)


def _del_win():
    if _win and cmds.window(_win, q=True, ex=True):
        cmds.deleteUI(_win, window=True)


def _message(new_text):
    if _win and cmds.window(_win, q=True, ex=True):
        cmds.text(_text, edit=True, label=new_text)


def _remove_values_from_list(the_list, val):
    for _ in range(the_list.count(val)):
        the_list.remove(val)


def _compare_vf_normal(vert):
    obj = vert.split(".")
    nr_vtx = obj[1].split("[")
    nr_vtx = nr_vtx[1].strip("]")
    edg = []
    vf_info = cmds.polyInfo(vert, vf=True)
    vf_list = []
    vf_ilist = vf_info[0].split(' ')
    _remove_values_from_list(vf_ilist, "")
    _remove_values_from_list(vf_ilist, "\n")
    vf_ilist.pop(0)
    vf_ilist.pop(0)
    for i in range(len(vf_ilist)):
        f_inf = vf_ilist[i].strip()
        vf_list.append(obj[0] + ".vtxFace[" + nr_vtx + "][" + f_inf + "]")
    vf_n = cmds.polyNormalPerVertex(vf_list[-1], query=True, xyz=True)
    vf_old_v = MBVector(vf_n[0], vf_n[1], vf_n[2])
    for j in range(len(vf_list)):
        vf_n1 = cmds.polyNormalPerVertex(vf_list[j], query=True, xyz=True)
        vf_new_v = MBVector(vf_n1[0], vf_n1[1], vf_n1[2])
        comp_v = vf_old_v - vf_new_v
        if comp_v.mag() != 0:
            h_edge = cmds.polyListComponentConversion(vf_list[j], te=True)
            edg.append(h_edge[0])
        vf_old_v = vf_new_v
    return edg


def _mb_join(list1, list2):
    for a in list2:
        list1.append(a)
    return list1


def _sg_to_hs():
    try:
        sel = cmds.ls(sl=True, fl=True)
        for obj in sel:
            _message('  Step 1 of 2 for: ' + str(obj))
            nr_vtx = cmds.polyEvaluate(obj, v=True)
            _set_max(nr_vtx)
            hard_edg = []
            for i in range(nr_vtx):
                curr_vert = obj + ".vtx[" + str(i) + "]"
                cmp_v = _compare_vf_normal(curr_vert)
                hard_edg = _mb_join(hard_edg, cmp_v)
                _step_progress(i)

            cmds.polyNormalPerVertex(obj, ufn=True)
            cmds.polySoftEdge(obj, a=180)
            _set_max(len(hard_edg))
            _step_progress(0)
            _message('  Step 2 of 2 for: ' + str(obj))
            if len(hard_edg) != 0:
                cmds.select(hard_edg, r=True)
                cmds.polySoftEdge(a=0)

        cmds.select(sel, r=True)
        _del_win()
    except Exception:
        _message('You need to have at least one object selected')


def run():
    global _win, _text, _progress
    if _win and cmds.window(_win, q=True, ex=True):
        _del_win()
    _win = cmds.window(title="Converting locked normals to Soft/Hard Edges")
    cmds.columnLayout(adjustableColumn=True)
    _text = cmds.text(label='  Step 1 of 2  ', align='center')
    _progress = cmds.progressBar(maxValue=10, width=400, isInterruptable=True)
    cmds.showWindow(_win)
    _sg_to_hs()
