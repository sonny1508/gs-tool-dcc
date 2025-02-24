from maya import cmds


def setPreserveChildren(state):
	"""Sets all manipulator preserve children options to `state`

	:type state: bool
	"""
	cmds.optionVar(intValue=("trsManipsPreserveChildPosition", state))
	cmds.manipMoveContext("Move", edit=True, preserveChildPosition=state)
	cmds.manipRotateContext("Rotate", edit=True, preserveChildPosition=state)
	cmds.manipScaleContext("Scale", edit=True, preserveChildPosition=state)

