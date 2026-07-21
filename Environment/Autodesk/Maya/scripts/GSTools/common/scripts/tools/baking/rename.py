# Embedded file name: C:/Users/GS50/Documents/maya/2018/scripts\rename.py
import os
import sys
import re
import time
import math
from PySide2.QtCore import QCoreApplication, QDate, QDateTime, QMetaObject, QObject, QPoint, QRect, QSize, QTime, QUrl, Qt
from PySide2.QtGui import QBrush, QColor, QConicalGradient, QCursor, QFont, QFontDatabase, QIcon, QKeySequence, QLinearGradient, QPalette, QPainter, QPixmap, QRadialGradient
from PySide2.QtWidgets import *
from PySide2 import QtWidgets, QtCore, QtUiTools
from shiboken2 import wrapInstance
import maya.cmds as cmds
import maya.OpenMayaUI as mui
import math
import rename_ui
import functools
import operator
import itertools
from collections import Counter as cn
import random
import pymel.core as p
import maya.mel as mel
import shiboken2

def maya_main_window():
    """
    Return the Maya main window widget as a Python object
    """
    main_window_ptr = mui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)


class RenameUI(rename_ui.Ui_Form, QtWidgets.QDialog):

    def __init__(self, parent = maya_main_window()):
        super(RenameUI, self).__init__(parent)
        self.setWindowTitle('Auto Rename')
        self.setupUi(self)
        self.create_layout()
        self.create_connections()

    def create_layout(self):
        pass

    def create_connections(self):
        self.renameButton.clicked.connect(self.find_pos)

    def do_something(self):
        print('TODO: Do something here')

    def find_pos(self, factor = 1):
        sel = self.get_selection()
        res = []
        while len(sel) > 0:
            a = sel.pop()
            s = [ [a, j] for j in sel if self.vector_find(a, j, factor) is True ]
            if len(s) >= 1:
                s = s[0]
                p = list(map(self.check_polycount, s))
                low = p.index(min(p))
                low = s.pop(low)
                if self.get_smooth_attr(low) == 0:
                    s.insert(0, low)
                else:
                    s.append(low)
                res.append(s)

        for item in res:
            if len(item) > 1:
                for ind, i in enumerate(item):
                    if i.split('_').pop() == 'low' or i.split('_').pop() == 'high':
                        pass
                    elif ind == 0:
                        cmds.rename(i, i + '_low')
                    else:
                        cmds.rename(i, item[0] + '_high')

    def get_selection(self):
        sel = cmds.ls(sl=True)
        return sel

    def vector_find(self, obj, obj2, factor):
        p1 = cmds.exactWorldBoundingBox(obj)
        p_max = p.datatypes.Point([p1[3], p1[4], p1[5]])
        p_min = p.datatypes.Point([p1[0], p1[1], p1[2]])
        p2 = cmds.exactWorldBoundingBox(obj2)
        p2_min = p.datatypes.Point([p2[0], p2[1], p2[2]])
        p2_max = p.datatypes.Point([p2[3], p2[4], p2[5]])
        v_dir = p.datatypes.Vector(p_min - p2_min).length()
        v_dir_02 = p.datatypes.Vector(p_max - p2_max).length()
        v_scale = p.datatypes.Vector(p_min - p_max).length()
        scale_factor = v_scale / 100 * factor
        if v_dir < scale_factor or v_dir_02 < scale_factor:
            return True
        else:
            return False

    def get_smooth_attr(self, obj):
        a = cmds.getAttr(obj + '.displaySmoothMesh')
        return a

    def check_polycount(self, sel):
        polycount = cmds.polyEvaluate(sel, v=True)
        return polycount


def getMainWindow():
    ptr = mui.MQtUtil.mainWindow()
    mainWin = shiboken2.wrapInstance(int(ptr), QtWidgets.QWidget)
    return mainWin


def show():
    global win
    try:
        win.close()
    except:
        pass

    win = RenameUI(parent=getMainWindow())
    win.show()
    return win