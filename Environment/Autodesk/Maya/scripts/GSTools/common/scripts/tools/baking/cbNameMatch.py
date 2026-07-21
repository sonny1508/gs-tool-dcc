import maya.cmds as cmds
import functools
import importlib

##import cbNameMatch
#importlib.reload(cbNameMatch)
#cbNameMatch.cbMatchNames()##

def cbNameMatchUI(pWindowTitle, pApplyCallback):
	windowID = 'nameMatchSetup'
	if cmds.window(windowID, exists=True):
		cmds.deleteUI(windowID)
	if cmds.windowPref(windowID, exists=True):
		cmds.windowPref(windowID, remove=True)
	window = cmds.window(windowID, title=pWindowTitle, w=300, h=100, mnb=False, mxb=False, s=False)

	# optionsMenu = cmds.menu(parent=window, label='&Options')

	cmds.columnLayout(w=300, rowSpacing=10)
	cmds.separator()
	textRow = cmds.rowLayout(nc=3)
	cmds.text(label="Name for part: ")
	cmds.separator(w=120, style='none')
	optionValue = cmds.optionVar(q='nameMatch_hideMeshes')
	cmds.checkBox('hideOption', label='Hide Meshes', value=optionValue, cc=cbProcessCheckBox)
	cmds.setParent('..')
	partName = cmds.textField(w=280)

	# create OK and Cancel buttons
	cmds.rowLayout(numberOfColumns=4, columnWidth3=(100, 100, 100), columnAlign3=('center', 'center', 'center'))

	cmds.button(label="Apply", w=70, h=30, command=functools.partial(cbApplyNameMatchCallback, partName, False, windowID))
	cmds.button(label="Apply And Close", w=100, h=30, command=functools.partial(cbApplyNameMatchCallback, partName, True, windowID))
	cmds.button(label="Cancel", w=70, h=30, command=functools.partial(cbCloseNameMatchWindow, windowID))

	cmds.showWindow(window)


def cbProcessCheckBox(*args):
	print((args[0]))
	cmds.optionVar(iv=['nameMatch_hideMeshes', int(args[0])])

def cbApplyNameMatchCallback(partName, close, windowID, *args):
	nameOfPart = cmds.textField(partName, q=True, text=True)
	nameOfPart = nameOfPart.replace(" ", "_")
	selection = cmds.ls(selection=True)

	print((cmds.checkBox('hideOption', q=True, value=True)))

	if len(selection) != 2:
		cmds.confirmDialog(message='Must have exactly two meshes selected!')
		return
	object1 = selection[0]
	object2 = selection[1]
	obj1Size = cmds.polyEvaluate(object1, f=True)
	obj2Size = cmds.polyEvaluate(object2, f=True)
	if obj1Size == obj2Size:
		cmds.confirmDialog(message='%s and %s have the same number of faces!' % (selection[0], selection[1]))
		return
	if obj1Size > obj2Size:
		cmds.rename(object1, nameOfPart + "_high")
		cmds.rename(object2, nameOfPart + "_low")
	else:
		cmds.rename(object1, nameOfPart + "_low")
		cmds.rename(object2, nameOfPart + "_high")
	if cmds.optionVar(q='nameMatch_hideMeshes') == 1:
		cmds.hide(cmds.ls(sl=True))
	if close:
		cbCloseNameMatchWindow(windowID)


def cbCloseNameMatchWindow(windowID, *args):
	if cmds.checkBox('hideOption', q=True, exists=True):
		cmds.optionVar(iv=['nameMatch_hideMeshes', cmds.checkBox('hideOption', q=True, value=True)])
	if cmds.window(windowID, exists=True):
		cmds.deleteUI(windowID)


def cbMatchNames():
	cbNameMatchUI('Match Names', cbApplyNameMatchCallback)
