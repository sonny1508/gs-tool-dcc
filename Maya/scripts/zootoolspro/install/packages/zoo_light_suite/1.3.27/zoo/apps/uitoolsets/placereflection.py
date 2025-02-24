from zoovendor.Qt import QtWidgets

from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements
from zoo.libs.maya.cmds.lighting import lightingutils

PLACE_R_TLTIP = "Place Reflection by www.braverabbit.com (Ingo Clemens)\n" \
                "With a light selected click on a surface to place the light (and it's highlight) \n" \
                "Hold Ctrl or Shift and click-drag to vary the distance of the light from the surface \n" \
                "https://github.com/IngoClemens/placeReflection"


class PlaceReflection(toolsetwidget.ToolsetWidget):
    id = "placeReflection"

    uiData = {"label": "Place Reflection",
              "icon": "circlecursor",
              "tooltip": PLACE_R_TLTIP,
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-place-reflection/"}

    def preContentSetup(self):
        """First code to run, treat this as the __init__() method"""
        pass

    def contents(self):
        """The UI Modes to build, compact, medium and or advanced, in this case we are only building one UI mode """
        return [self.initCompactWidget()]

    def initCompactWidget(self):
        """Builds the Compact GUI (self.compactWidget) """
        parent = QtWidgets.QWidget(parent=self)
        self.widgetsLayoutAll(parent)
        return parent

    def postContentSetup(self):
        """Last of the initialize code"""
        self.uiConnections()

    def defaultAction(self):
        """Double Click"""
        pass

    # ------------------------------------
    # WIDGETS AND LAYOUT
    # ------------------------------------

    def widgetsLayoutAll(self, parent):
        """Creates the only UI for the toolset
        """
        self.mainLayout = elements.vBoxLayout(parent,
                                              margins=(uic.WINSIDEPAD, uic.WINBOTPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                              spacing=0)
        self.placeReflectionBtn = elements.styledButton("Place Reflection", "placeReflection", parent,
                                                        toolTip=PLACE_R_TLTIP, style=uic.BTN_DEFAULT)
        self.mainLayout.addWidget(self.placeReflectionBtn)
        self.mainLayout.addStretch(1)

    # ------------------------------------
    # THIRD PARTY
    # ------------------------------------

    def placeReflection(self):
        """placeReflection by braverabbit https://github.com/IngoClemens/placeReflection"""
        lightingutils.placeReflection()

    def uiConnections(self):
        """Add the connections
        """
        self.placeReflectionBtn.clicked.connect(self.placeReflection)
