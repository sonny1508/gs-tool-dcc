""" ---------- Render Object Display -------------
Enables the user to easily toggle the following modes for render visibility

RS_PRIMARY_VIS = "primaryVisibility"
RS_CASTS_SHADOWS = "castsShadows"
RS_HOLDOUT = "holdOut"
RS_MOBLUR = "motionBlur"
RS_REFLECTION_VIS = "visibleInReflections"
RS_REFRACTION_VIS = "visibleInRefractions"
DOUBLE_SIDED = "doubleSided"
OPPOSITE = "opposite"

TODO: Add renderer specific attributes

Author:  Andrew Silke
"""

from zoovendor.Qt import QtWidgets

from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements

from zoo.core.util import env

if env.isMaya():
    from zoo.libs.maya.cmds.renderer import rendererstats
    from zoo.libs.maya.cmds.renderer.rendererstats import RS_PRIMARY_VIS, RS_CASTS_SHADOWS, RS_HOLDOUT, \
        RS_MOTION_BLUR, RS_REFLECTION_VIS, RS_REFRACTION_VIS, RS_DOUBLE_SIDED, RS_OPPOSITE, RE_RECEIVE_SHADOWS

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1


class RenderObjectDisplay(toolsetwidget.ToolsetWidget):
    id = "renderObjectDisplay"
    info = "Toggle render display modes for selected objects."
    uiData = {"label": "Render Object Display",
              "icon": "eye",
              "tooltip": "Toggle render display modes for selected objects.",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-render-object-display/"}

    # ------------------
    # STARTUP
    # ------------------

    def preContentSetup(self):
        """First code to run, treat this as the __init__() method"""
        pass

    def contents(self):
        """The UI Modes to build, compact, medium and or advanced """
        return [self.initCompactWidget(), self.initAdvancedWidget()]

    def initCompactWidget(self):
        """Builds the Compact GUI (self.compactWidget) """
        self.compactWidget = GuiCompact(parent=self, properties=self.properties, toolsetWidget=self)
        return self.compactWidget

    def initAdvancedWidget(self):
        """Builds the Advanced GUI (self.advancedWidget) """
        self.advancedWidget = GuiAdvanced(parent=self, properties=self.properties, toolsetWidget=self)
        return self.advancedWidget

    def postContentSetup(self):
        """Last of the initialize code"""
        self.uiConnections()

    def defaultAction(self):
        """Double Click
        Double clicking the tools toolset icon will run this method
        Be sure "defaultActionDoubleClick": True is set inside self.uiData (meta data of this class)"""
        pass

    def currentWidget(self):
        """ Currently active widget

        :return:
        :rtype: GuiAdvanced or GuiCompact
        """
        return super(RenderObjectDisplay, self).currentWidget()

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiAdvanced or GuiCompact]
        """
        return super(RenderObjectDisplay, self).widgets()

    # ------------------
    # LOGIC
    # ------------------
    def castShadows(self):
        """Sets castShadows"""
        rendererstats.renderStatsSel(vis=self.properties.castShadowsCheckbox.value,
                                     attr=RS_CASTS_SHADOWS)

    def receiveShadows(self):
        """Sets receiveShadows """
        rendererstats.renderStatsSel(vis=self.properties.receiveShadowsCheckbox.value,
                                     attr=RE_RECEIVE_SHADOWS)

    def visibleReflections(self):
        """Sets visibleReflections """
        rendererstats.renderStatsSel(vis=self.properties.reflectionVisCheckbox.value,
                                     attr=RS_REFLECTION_VIS)

    def visibleRefractions(self):
        """Sets visibleRefractions """
        rendererstats.renderStatsSel(vis=self.properties.refractionVisCheckbox.value,
                                     attr=RS_REFRACTION_VIS)

    def primaryVisibility(self):
        """Sets primaryVisibility """
        rendererstats.renderStatsSel(vis=self.properties.primVisCheckbox.value,
                                     attr=RS_PRIMARY_VIS)

    def motionBlur(self):
        """Sets motionBlur """
        rendererstats.renderStatsSel(vis=self.properties.motionBlurCheckbox.value,
                                     attr=RS_MOTION_BLUR)

    def holdout(self):
        """Sets holdout """
        rendererstats.renderStatsSel(vis=self.properties.holdOutCheckbox.value,
                                     attr=RS_HOLDOUT)

    def doubleSided(self):
        """Sets doubleSided """
        rendererstats.renderStatsSel(vis=self.properties.doubleSidedCheckbox.value,
                                     attr=RS_DOUBLE_SIDED)

    def opposite(self):
        """Sets opposite """
        rendererstats.renderStatsSel(vis=self.properties.oppositeCheckbox.value,
                                     attr=RS_OPPOSITE)

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        for widget in self.widgets():
            widget.primVisCheckbox.stateChanged.connect(self.primaryVisibility)
            widget.castShadowsCheckbox.stateChanged.connect(self.castShadows)
            widget.reflectionVisCheckbox.stateChanged.connect(self.visibleReflections)
            widget.refractionVisCheckbox.stateChanged.connect(self.visibleRefractions)
            widget.receiveShadowsCheckbox.stateChanged.connect(self.receiveShadows)

            widget.holdOutCheckbox.stateChanged.connect(self.primaryVisibility)
            widget.motionBlurCheckbox.stateChanged.connect(self.motionBlur)
            widget.doubleSidedCheckbox.stateChanged.connect(self.primaryVisibility)
            widget.oppositeCheckbox.stateChanged.connect(self.primaryVisibility)


class GuiWidgets(QtWidgets.QWidget):
    def __init__(self, parent=None, properties=None, uiMode=None, toolsetWidget=None):
        """Builds the main widgets for all GUIs

        properties is the list(dictionaries) used to set logic and pass between the different UI layouts
        such as compact/adv etc

        :param parent: the parent of this widget
        :type parent: QtWidgets.QWidget
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: zoo.apps.toolsetsui.widgets.toolsetwidget.PropertiesDict
        :param uiMode: 0 is compact ui mode, 1 is advanced ui mode
        :type uiMode: int
        """
        super(GuiWidgets, self).__init__(parent=parent)
        self.properties = properties
        # Primary Visibility ---------------------------------------
        tooltip = "Set whether the object will be visible in renders.  \n" \
                  "Objects will still cast shadows and emit global illumination. \n" \
                  "Select polygon or NURBS objects and toggle"
        self.primVisCheckbox = elements.CheckBox(label="Primary Visibility",
                                                 checked=True,
                                                 toolTip=tooltip)
        # Casts Shadows ---------------------------------------
        tooltip = "Set whether the object/s will cast shadows in renders.  \n" \
                  "Select polygon or NURBS objects and toggle"
        self.castShadowsCheckbox = elements.CheckBox(label="Casts Shadows",
                                                     checked=True,
                                                     toolTip=tooltip)
        # Visible In Reflections ---------------------------------------
        tooltip = "Set whether the object/s will be visible in the reflections on other objects.  \n" \
                  "Select polygon or NURBS objects and toggle"
        self.reflectionVisCheckbox = elements.CheckBox(label="Visible In Reflections",
                                                       checked=True,
                                                       toolTip=tooltip)
        # Visible In Refractions ---------------------------------------
        tooltip = "Set whether the object/s will be visible in the refractions of other objects.  \n" \
                  "Select polygon or NURBS objects and toggle"
        self.refractionVisCheckbox = elements.CheckBox(label="Visible In Refractions",
                                                       checked=True,
                                                       toolTip=tooltip)
        # Receive Shadows ---------------------------------------
        tooltip = "Set whether the object/s will receive shadows from other objects in renders.  \n" \
                  "Select polygon or NURBS objects and toggle"
        self.receiveShadowsCheckbox = elements.CheckBox(label="Receive Shadows",
                                                        checked=True,
                                                        toolTip=tooltip)

        # Double Sided ---------------------------------------
        tooltip = "Set if the object/s is single sided or double sided.  \n" \
                  "Select polygon or NURBS objects and toggle"
        self.doubleSidedCheckbox = elements.CheckBox(label="Double Sided",
                                                     checked=True,
                                                     toolTip=tooltip)
        # Opposite ---------------------------------------
        tooltip = "If the is single sided flip the side that is being displayed.  \n" \
                  "Select polygon or NURBS objects and toggle"
        self.oppositeCheckbox = elements.CheckBox(label="Opposite",
                                                  checked=True,
                                                  toolTip=tooltip)
        # Hold Out ---------------------------------------
        tooltip = "Makes an object receive shadows/reflections but is not be visible in renders.  \n" \
                  "Select polygon or NURBS objects and toggle"
        self.holdOutCheckbox = elements.CheckBox(label="Hold Out",
                                                 checked=True,
                                                 toolTip=tooltip)
        # Motion Blur ---------------------------------------
        tooltip = "Sets the object to have motion blur on or off, this setting requires motion blur to be on.  \n" \
                  "Select polygon or NURBS objects and toggle"
        self.motionBlurCheckbox = elements.CheckBox(label="Motion Blur",
                                                    checked=True,
                                                    toolTip=tooltip)


class GuiCompact(GuiWidgets):
    def __init__(self, parent=None, properties=None, uiMode=UI_MODE_COMPACT, toolsetWidget=None):
        """Adds the layout building the compact version of the GUI:

            default uiMode - 0 is advanced (UI_MODE_COMPACT)

        :param parent: the parent of this widget
        :type parent: QtWidgets.QWidget
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: zoo.apps.toolsetsui.widgets.toolsetwidget.PropertiesDict
        """
        super(GuiCompact, self).__init__(parent=parent, properties=properties, uiMode=uiMode,
                                         toolsetWidget=toolsetWidget)
        # Main Layout ---------------------------------------
        mainLayout = elements.vBoxLayout(self, margins=(uic.WINSIDEPAD, uic.WINBOTPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SREG)
        # Grid Layout -----------------------------
        gridTopLayout = elements.GridLayout(spacing=uic.SVLRG,
                                            margins=(uic.REGPAD, uic.REGPAD, uic.REGPAD, uic.REGPAD,))
        row = 0
        gridTopLayout.addWidget(self.castShadowsCheckbox, row, 0)
        gridTopLayout.addWidget(self.receiveShadowsCheckbox, row, 1)
        row += 1
        gridTopLayout.addWidget(self.reflectionVisCheckbox, row, 0)
        gridTopLayout.addWidget(self.refractionVisCheckbox, row, 1)
        row += 1
        gridTopLayout.addWidget(self.primVisCheckbox, row, 0)
        gridTopLayout.setColumnStretch(0, 1)
        gridTopLayout.setColumnStretch(1, 1)
        # Add To Main Layout ---------------------------------------
        mainLayout.addLayout(gridTopLayout)


class GuiAdvanced(GuiWidgets):
    def __init__(self, parent=None, properties=None, uiMode=UI_MODE_ADVANCED, toolsetWidget=None):
        """Adds the layout building the advanced version of the GUI:

            default uiMode - 1 is advanced (UI_MODE_ADVANCED)

        :param parent: the parent of this widget
        :type parent: QtWidgets.QWidget
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: zoo.apps.toolsetsui.widgets.toolsetwidget.PropertiesDict
        """
        super(GuiAdvanced, self).__init__(parent=parent, properties=properties, uiMode=uiMode,
                                          toolsetWidget=toolsetWidget)
        # Main Layout ---------------------------------------
        mainLayout = elements.vBoxLayout(self, margins=(uic.WINSIDEPAD, uic.WINBOTPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SREG)
        # Grid Layout -----------------------------
        gridTopLayout = elements.GridLayout(spacing=uic.SVLRG,
                                            margins=(uic.REGPAD, uic.REGPAD, uic.REGPAD, uic.REGPAD,))
        row = 0
        gridTopLayout.addWidget(self.castShadowsCheckbox, row, 0)
        gridTopLayout.addWidget(self.receiveShadowsCheckbox, row, 1)
        row += 1
        gridTopLayout.addWidget(self.reflectionVisCheckbox, row, 0)
        gridTopLayout.addWidget(self.refractionVisCheckbox, row, 1)
        row += 1
        gridTopLayout.addWidget(self.primVisCheckbox, row, 0)
        gridTopLayout.addWidget(self.motionBlurCheckbox, row, 1)
        row += 1
        gridTopLayout.addWidget(self.doubleSidedCheckbox, row, 0)
        gridTopLayout.addWidget(self.oppositeCheckbox, row, 1)
        row += 1
        gridTopLayout.addWidget(self.holdOutCheckbox, row, 0)
        gridTopLayout.setColumnStretch(0, 1)
        gridTopLayout.setColumnStretch(1, 1)
        # Add To Main Layout ---------------------------------------
        mainLayout.addLayout(gridTopLayout)
