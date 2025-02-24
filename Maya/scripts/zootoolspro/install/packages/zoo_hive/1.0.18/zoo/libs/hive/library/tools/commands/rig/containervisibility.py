#
# if rig.configuration.useContainers and rig.configuration.containerAttrsShowAtTop and not mayaenv.isMayapy():
#     # mayas UI is confusing True for show at top means the bottom so here we invert the rig config
#     mayaui.setChannelBoxAtTop("mainChannelBox", not rig.configuration.containerAttrsShowAtTop)
# if rig.configuration.useContainers and rig.configuration.containerOutlinerDisplayUnderParent and not mayaenv.isMayapy():
#     for outliner in mayaui.outlinerPaths():
#         cmds.outlinerEditor(outliner, e=True, showContainerContents=False)
#         cmds.outlinerEditor(outliner, e=True, showContainedOnly=False)

