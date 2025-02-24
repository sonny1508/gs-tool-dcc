from zoo.libs.maya.mayacommand import mayaexecutor as executor
from zoo.libs.maya.cmds.meta import metasplinerig, metaadditivefk
from zoo.libs.maya.markingmenu import menu
from zoo.libs.maya.meta import base


class SplineRigMarkingMenuCommand(menu.MarkingMenuCommand):
    """ Spline Marking menu command
    """
    id = "splineRigMarkingMenu"  # a unique identifier for a class, should never be changed
    creator = "Zootools"

    @staticmethod
    def uiData(arguments):
        """

        :param arguments:
        :type arguments:
        :return:
        :rtype:
        """
        ret = {"icon": "",
                "label": "",
                "bold": False,
                "italic": False,
                "optionBox": False,
                "optionBoxIcon": ""
                }
        metanodes = base.metaNodeFromZApiObjects(arguments['nodes']) #type: list[metasplinerig.MetaSplineRig]
        if not metanodes:
            return ret
        meta = metanodes[-1]  # type: metasplinerig.MetaSplineRig

        switch = {"switchToSpine": "buildSpine",
                  "switchToFk": "buildFk",
                  "switchToFloat": "buildFloat",
                  "switchToRevFk": "buildRevFk"}
        metaParents = list(meta.metaParents())
        if meta.isClassType(metasplinerig.MetaSplineRig) or (metaParents and metaParents[-1].isClassType(metasplinerig.MetaSplineRig)):
            if metaParents:
                meta = metaParents[-1]

            attr = switch.get(arguments['operation'])
            ret['show'] = meta.attribute(attr).value() if attr else True

            showForPublish = ['switchToSpine', 'switchToFk', 'switchToFloat', 'switchToRevFk', 'toggleControls']
            if meta.isPublished() and arguments['operation'] not in showForPublish:
                ret['show'] = False

            if arguments['operation'] == 'toggleControls':
                ret['checkBox'] = not meta.controlsHidden()
            elif arguments['operation'] == 'toggleControlsAdditiveFk':
                ret['show'] = meta.additiveFkMetaExists()
                if meta.additiveFkMetaExists():
                    ret['checkBox'] = not meta.additiveFkControlsHidden()
            elif arguments['operation'] == 'deleteAdditiveFk':
                if meta.isPublished():
                    ret['show'] = False
                else:
                    ret['show'] = meta.additiveFkMetaExists()
            elif arguments['operation'] == 'bakeAdditiveFk':
                ret['show'] = False  # Only show for delete additive Fk

        elif meta.isClassType(metaadditivefk.ZooMetaAdditiveFk):
            if arguments['operation'] == 'deleteAdditiveFk':
                ret['show'] = (arguments['operation'] == 'deleteAdditiveFk')
            elif arguments['operation'] == 'bakeAdditiveFk':
                ret['show'] = (arguments['operation'] == 'bakeAdditiveFk')  # Only show for delete additive Fk
            else:  # All other menu items hide
                ret['show'] = False

        return ret

    def execute(self, arguments):
        """The main execute methods for the joints marking menu. see executeUI() for option box commands

        :type arguments: dict
        """
        metaNodes = base.metaNodeFromZApiObjects(arguments['nodes'])  # type: list[metasplinerig.MetaSplineRig]

        operation = arguments.get("operation", "")

        for m in metaNodes:
            meta = m
            if not m.isClassType(metasplinerig.MetaSplineRig):
                if m.isClassType(metaadditivefk.ZooMetaAdditiveFk):
                    if list(m.metaParents()):
                        meta = list(m.metaParents())[-1]
                else:
                    continue
            if operation == "switchToSpine":
                executor.execute("zoo.maya.splinerig.switch", meta=meta, switchTo="spine")
            elif operation == "switchToFk":
                executor.execute("zoo.maya.splinerig.switch", meta=meta, switchTo="fk")
            elif operation == "switchToFloat":
                executor.execute("zoo.maya.splinerig.switch", meta=meta, switchTo="float")
            elif operation == "switchToRevFk":
                executor.execute("zoo.maya.splinerig.switch", meta=meta, switchTo="revFk")
            elif operation == "duplicate":
                executor.execute("zoo.maya.splinerig.duplicate", meta=meta)
            elif operation == "bake":
                executor.execute("zoo.maya.splinerig.bake", meta=meta)
            elif operation == "rebuild":
                executor.execute("zoo.maya.splinerig.rebuild", meta=meta, bake=False)
            elif operation == "rebuildBaked":
                executor.execute("zoo.maya.splinerig.rebuild", meta=meta, bake=True)
            elif operation == "delete":
                executor.execute("zoo.maya.splinerig.delete", meta=meta)
            elif operation == "deleteAdditiveFk":
                if meta.isClassType(metasplinerig.MetaSplineRig):  # if there's a spline rig
                    meta.deleteAdditiveFkRig()
                else:  # no spline rig, only Add FK
                    executor.execute("zoo.maya.additiveFk.delete", meta=meta)
            elif operation == "bakeAdditiveFk":  # Only shows while no spline rig
                executor.execute("zoo.maya.additiveFk.delete", meta=meta, bake=True)
            elif operation == "deleteAll":  # deletes meshes and joints
                executor.execute("zoo.maya.splinerig.delete", meta=meta, deleteAll=True)
            elif operation == "selectJoints":  # Select Skin Joints
                meta.selectJoints()
            elif operation == "selectMetaNode":
                meta.selectMeta()
            elif operation == "toggleControls":
                meta.toggleControls()
            elif operation == "toggleControlsAdditiveFk":
                meta.toggleControlsAdditiveFk()
            elif operation == "openToolset":
                from zoo.apps.toolsetsui import run
                run.openToolset("splineRig")



