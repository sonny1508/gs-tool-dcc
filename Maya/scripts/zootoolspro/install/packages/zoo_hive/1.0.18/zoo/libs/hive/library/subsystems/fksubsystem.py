from zoo.libs.hive import api
from zoo.libs.maya import zapi
from zoo.libs.hive.base import basesubsystem


class FKSubsystem(basesubsystem.BaseSubsystem):
    def __init__(self, component, guideIds, fkIds, rootParentId):
        super(FKSubsystem, self).__init__(component)
        self.guideIds = guideIds
        self.fkIds = fkIds
        self.rootParentId = rootParentId

    def setupRig(self, parentNode):
        if not self.active():
            return
        namer = self.component.namingConfiguration()
        comp = self.component
        rigLayer = comp.rigLayer()
        compName, compSide = self.component.name(), self.component.side()
        guides = comp.definition.guideLayer.findGuides(*self.guideIds)
        fkCtrlPt = rigLayer.taggedNode(self.rootParentId)
        for i, guide in enumerate(guides):
            fkGuideId = self.fkIds[i]

            fkControlName = namer.resolve(
                "controlName",
                {
                    "componentName": compName,
                    "side": compSide,
                    "system": api.constants.FKTYPE,
                    "id": fkGuideId,
                    "type": "control",
                },
            )
            fkCtrl = rigLayer.createControl(
                name=fkControlName,
                id=fkGuideId,
                translate=guide.translate,
                rotate=guide.rotate,
                parent=fkCtrlPt,
                rotateOrder=guide.rotateOrder,
                shape=guide.shape,
                shapeTransform=guide.shapeTransform,
                selectionChildHighlighting=self.component.configuration.selectionChildHighlighting,
                srts=[{"name": "_".join([fkControlName, "srt"])}],
            )

            fkCtrlPt = fkCtrl

    def matchTo(self, nodes):
        """Matches the current fk controls to the specified nodes in worldSpace.
        Returns the controls and the expected selectable.

        :param nodes:
        :type nodes: list[:class:`zapi.DagNode`]
        :return:
        :rtype: dict
        """
        rigLayer = self.component.rigLayer()

        controls = rigLayer.findControls(*self.fkIds)
        mats = []
        for jnt, ctrl in zip(nodes, controls):
            mat = jnt.worldMatrix()
            mat = zapi.TransformationMatrix(mat)
            mat.setScale((1, 1, 1), zapi.kWorldSpace)
            mats.append(mat.asMatrix())
        for ctrl, mat in zip(controls, mats):
            ctrl.setWorldMatrix(mat)

        return {"controls": controls, "selectables": [controls[-1]]}
