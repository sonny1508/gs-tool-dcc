"""
from zoo.libs.maya.cmds.hotkeys import hotkeyexample

Delete Static Channels on the selected Object(s)

Paint Skin weights/  Brave rabbit smooth weights/ Mirror weights/ Convert selected components to selected to Vertex component/

Create Locator/ Shape Editor/  Graph editor/ Hypershade

"""
import maya.mel as mel

from zoovendor.Qt import QtCore, QtGui
from zoo.libs.pyqt.widgets import elements
from zoo.libs.pyqt import uiconstants as uic

from zoo.libs.maya.cmds.objutils import cleanup, selection
from zoo.libs.maya.cmds.modeling import pivots

WINDOW_HEIGHT = 64
BTN_COUNT = 9

WINDOW_OFFSET_X = int(-(BTN_COUNT / 2 * 32))
WINDOW_OFFSET_Y = -10


class MyPopupToolbar(elements.ZooWindowThin):

    def __init__(self, name="", title="", parent=None, resizable=True, width=BTN_COUNT * 32, height=WINDOW_HEIGHT,
                 modal=False, alwaysShowAllTitle=False, minButton=False, maxButton=False, onTop=False,
                 saveWindowPref=False, titleBar=None, overlay=True, minimizeEnabled=True, initPos=None):
        super(MyPopupToolbar, self).__init__(name, title, parent, resizable, width, height, modal, alwaysShowAllTitle,
                                             minButton, maxButton, onTop, saveWindowPref, titleBar, overlay,
                                             minimizeEnabled, initPos)
        # self.parentContainer.setWindowFlags(self.parentContainer.defaultWindowFlags | QtCore.Qt.Popup)

        self.widgets()
        self.layout()

    # -------------
    # COMMANDS
    # -------------

    def deleteHistory(self):
        cleanup.deleteHistory()

    def freezeTransforms(self):
        cleanup.freezeTransforms()

    def centerPivot(self):
        pivots.centerPivotSelected()

    def matchTransforms(self):
        pivots.centerPivotSelected()

    def extrude(self):
        mel.eval('selectMode - co;')
        mel.eval('performPolyExtrude 0')

    def multicut(self):
        selection.selectComponentSelectionMode("edges")
        mel.eval('dR_DoCmd("multiCutTool")')

    def mergeVerts(self):
        selection.selectComponentSelectionMode("vertices")
        mel.eval('polyMergeToCenter')

    def fillHole(self):
        selection.selectComponentSelectionMode("edges")
        mel.eval('polyPerformAction polyCloseBorder e 0')

    def bridge(self):
        selection.selectComponentSelectionMode("edges")
        mel.eval('performBridgeOrFill')

    # -------------
    # CREATE A BUTTON
    # -------------

    def createIconButton(self, icon, toolTip):
        return elements.styledButton("", icon,
                                     toolTip=toolTip,
                                     style=uic.BTN_DEFAULT,
                                     btnHeight=32, btnWidth=32)

    # -------------
    # MAKE ALL BUTTONS
    # -------------

    def widgets(self):
        self.buttonList = list()

        toolTip = "Delete History"
        self.delHistoryBtn = self.createIconButton("crossXFat", toolTip)
        self.delHistoryBtn.clicked.connect(self.deleteHistory)
        self.buttonList.append(self.delHistoryBtn)

        toolTip = "FreezeTransforms"
        self.freezeBtn = self.createIconButton("cold", toolTip)
        self.freezeBtn.clicked.connect(self.freezeTransforms)
        self.buttonList.append(self.freezeBtn)

        toolTip = "Center Pivot"
        self.centerPivotBtn = self.createIconButton("focusAim", toolTip)
        self.centerPivotBtn.clicked.connect(self.centerPivot)
        self.buttonList.append(self.centerPivotBtn)

        toolTip = "Match Transformations"
        self.matchBtn = self.createIconButton("magnet", toolTip)
        self.matchBtn.clicked.connect(self.matchTransforms)
        self.buttonList.append(self.matchBtn)

        # modeling
        toolTip = "Extrude"
        self.extrudeBtn = self.createIconButton("maximise", toolTip)
        self.extrudeBtn.clicked.connect(self.extrude)
        self.buttonList.append(self.extrudeBtn)

        toolTip = "Multi Cut"
        self.multicutBtn = self.createIconButton("scissors", toolTip)
        self.multicutBtn.clicked.connect(self.multicut)
        self.buttonList.append(self.multicutBtn)

        toolTip = "Merge Vertices Center"
        self.mergeVertsBtn = self.createIconButton("mergeVertex", toolTip)
        self.mergeVertsBtn.clicked.connect(self.mergeVerts)
        self.buttonList.append(self.mergeVertsBtn)

        toolTip = "Fill Hole"
        self.fillHoleBtn = self.createIconButton("snapAlignThree", toolTip)
        self.fillHoleBtn.clicked.connect(self.fillHole)
        self.buttonList.append(self.fillHoleBtn)

        toolTip = "Bridge"
        self.bridgeBtn = self.createIconButton("retimer", toolTip)
        self.bridgeBtn.clicked.connect(self.bridge)
        self.buttonList.append(self.bridgeBtn)

    # -------------
    # LAYOUT UI
    # -------------

    def layout(self):
        self.mainLayout = elements.hBoxLayout(spacing=0, margins=(0, 0, 0, 0))
        for btn in self.buttonList:
            self.mainLayout.addWidget(btn)

        self.setMainLayout(self.mainLayout)


def main():
    win = MyPopupToolbar()
    point = QtGui.QCursor.pos()
    point.setX(point.x() + WINDOW_OFFSET_X)
    point.setY(point.y() + WINDOW_OFFSET_Y)
    win.show(point)


if __name__ == "__main__":
    main()
