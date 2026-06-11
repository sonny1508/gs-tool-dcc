"""Remove all non-reference namespaces from the scene."""
import maya.cmds as cmds


def run():
    list_ref = [n.replace('RN', '') for n in cmds.ls(rf=True)]
    cmds.namespace(set=':')
    all_namespaces = [
        n.split(':')[len(n.split(':')) - 1]
        for n in cmds.namespaceInfo(lon=True, fn=True, r=True)
        if n not in ['UI', 'shared']
    ]
    removed = []
    if all_namespaces:
        for ns in all_namespaces:
            if ns not in list_ref:
                cmds.namespace(rm=ns, mnr=True, f=True)
                removed.append(ns)
        cmds.confirmDialog(icn='warning', m='Removed namespaces: ' + str(removed))
    else:
        cmds.confirmDialog(icn='warning', m='No namespaces to remove.')
