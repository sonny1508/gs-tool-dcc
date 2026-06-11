from sys import stdout
import maya.cmds as cmds
import maya.api.OpenMaya as om

def GN_Eval(msg, mode='PRINT', deferred=False):
    if deferred is False:
        if mode == 'PRINT':
            stdout.write("{}\n".format(msg))
        elif mode == 'INFO':
            om.MGlobal.displayInfo(msg)
        elif mode == 'WARNING':
            om.MGlobal.displayWarning(msg)
        elif mode == 'ERROR':
            om.MGlobal.displayError(msg)
    else:
        if mode == 'PRINT':
            cmds.evalDeferred(r'from sys import stdout; stdout.write("{}\n")'.format(msg))
        elif mode == 'INFO':
            cmds.evalDeferred(r'import maya.api.OpenMaya as om; om.MGlobal.displayInfo("'+msg+'")')
        elif mode == 'WARNING':
            cmds.evalDeferred(r'import maya.api.OpenMaya as om; om.MGlobal.displayWarning("'+msg+'")')
        elif mode == 'ERROR':
            cmds.evalDeferred(r'import maya.api.OpenMaya as om; om.MGlobal.displayError("'+msg+'")')

def GN_Print(object, mode='PRINT', deferred=False):
    if type(object) is not list:
        GN_Eval(object, mode, deferred)
    else:
        for obj in object:
            GN_Eval(obj, mode, deferred)

# VERSION 2
'''
import maya.cmds as cmds
import maya.mel as mel

def GN_Eval(msg, deferred=False):
	if deferred is False:
		mel.eval(msg)
	else:
		cmds.evalDeferred(r"import maya.mel as mel; mel.eval(r'{}')".format(msg))

def GN_Print(obj, deferred=False):
    if type(obj) is not list:
        msg = r'print("{}\n")'.format(obj)
        GN_Eval(msg, deferred)
    else:
        for i in range(len(obj)):
            msg = r'print("{}\n")'.format(obj[i])
            GN_Eval(msg, deferred)
'''

# VERSION 1
'''
import maya.mel as mel

def GN_Print(msg):
    if type(msg) is not list:
		mel.eval(r'print("{}\n")'.format(msg))
    else:
        for i in range(len(msg)):
        	mel.eval(r'print("{}\n")'.format(msg[]))
'''

# Builtin override
'''
from __future__ import print_function
import sys
try:
    # Python 3
    import builtins
except ImportError:
    # Python 2
    import __builtin__ as builtins


def print(*args, **kwargs):
    sep, end = kwargs.pop('sep', ' '), kwargs.pop('end', '\n')
    file, flush = kwargs.pop('file', sys.stdout), kwargs.pop('flush', False)
    if kwargs:
        raise TypeError('print() got an unexpected keyword argument {!r}'.format(next(iter(kwargs))))
    builtins.print(*args, sep=sep, end=end, file=file)
    if flush:
        file.flush()
'''