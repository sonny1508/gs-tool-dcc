from zoo.libs.pyqt.widgets import elements
from zoo.libs.commands import hive
from maya.api import OpenMaya as om2
from zoovendor.Qt import QtCore
from zoo.libs.pyqt import uiconstants


class MirrorWidget(elements.ZooWindow):
    onFinishedMirroring = QtCore.Signal()
    windowSettingsPath = "zoo/hiveMirrorWidget"

    def __init__(self, components, **kwargs):
        super(MirrorWidget, self).__init__(**kwargs)
        self.components = components
        toolTip = "Set the mirror axis to mirror across. X, Y or Z?"
        self.mirrorTranslate = elements.ComboBoxRegular("Mirror Axis",
                                                        items=("x", "y", "z"),
                                                        setIndex=0,
                                                        parent=self, toolTip=toolTip)
        self.duplicate = elements.CheckBox("Duplicate", checked=True,
                                           parent=self)
        namingInstance = self.components[0]["component"].namingConfiguration()
        componentSide = self.components[0]["component"].side()
        sideLabels = [i.value for i in namingInstance.field("side").keyValues()]
        mirroredSide = namingInstance.field("sideSymmetry").valueForKey(componentSide)
        if not mirroredSide:
            index = sideLabels.index(namingInstance.field("sideSymmetry").valueForKey("L"))
        else:
            index = sideLabels.index(mirroredSide)
        self.sideLabel = elements.ComboBoxRegular("Side Label",
                                                  items=sideLabels,
                                                  setIndex=index,
                                                  parent=self)
        self.okcancel = elements.OkCancelButtons(parent=self)
        self.okcancel.CancelBtnPressed.connect(self.close)
        self.okcancel.OkBtnPressed.connect(self._execute)
        layout = elements.GridLayout(margins=(uiconstants.WINSIDEPAD,
                                              uiconstants.WINBOTPAD,
                                              uiconstants.WINSIDEPAD,
                                              uiconstants.WINBOTPAD),
                                     spacing=uiconstants.SREG)
        self.setMainLayout(layout)
        layout.addWidget(self.mirrorTranslate, 0, 0)
        layout.addWidget(self.sideLabel, 0, 1)
        layout.addWidget(self.duplicate, 1, 1)
        layout.addWidget(self.okcancel, 2, 1)

    def isDocked(self):
        return False

    def _execute(self):
        namer = self.components[0]["component"].namingConfiguration()
        rig = None
        axis = self.mirrorTranslate.value()
        axisMap = {"x": "yz", "y": "xz", "z": "xy"}
        translationAxis = axisMap[axis]
        field = namer.field("side")
        for comp in self.components:
            compObj = comp["component"]
            userLabel = self.sideLabel.value()
            resolvedValue = field.valueForKey(userLabel)
            comp.update(dict(translate=(axis,),
                             rotate=translationAxis, parent=om2.MObject.kNullObj,
                             side=resolvedValue, duplicate=bool(self.duplicate.isChecked())))
            rig = compObj.rig
        hive.mirrorComponents(rig, self.components)
        self.close()
        self.onFinishedMirroring.emit()


def launchMirrorWidget(components, **uiKwargs):
    win = MirrorWidget(components, title="Mirror Component", **uiKwargs)
    win.show()
    return win

