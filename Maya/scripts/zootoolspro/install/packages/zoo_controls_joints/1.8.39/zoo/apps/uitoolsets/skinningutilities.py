from functools import partial

from zoovendor.Qt import QtWidgets, QtCore

from zoo.apps.toolsetsui.widgets import toolsetwidget
from zoo.libs.pyqt import uiconstants as uic
from zoo.libs.pyqt.widgets import elements
from zoo.libs import iconlib

from zoo.core.util import env

if env.isMaya():
    from zoo.libs.maya.cmds.skin import bindskin

UI_MODE_COMPACT = 0
UI_MODE_ADVANCED = 1


class SkinningUtilities(toolsetwidget.ToolsetWidget):
    id = "skinningUtilities"
    info = "Template file for building new GUIs."
    uiData = {"label": "Skinning Toolbox",
              "icon": "skinYoga",
              "tooltip": "Template file for building new GUIs.",
              "defaultActionDoubleClick": False,
              "helpUrl": "https://create3dcharacters.com/maya-tool-skinning-utilities/"}

    # ------------------
    # STARTUP
    # ------------------

    def preContentSetup(self):
        """First code to run, treat this as the __init__() method"""
        pass

    def contents(self):
        """The UI Modes to build, compact, medium and or advanced """
        return [self.initCompactWidget()]  # self.initAdvancedWidget()

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
        """Returns the current widget class eg. self.compactWidget or self.advancedWidget

        Over ridden class
        :rtype: GuiWidgets
        """
        return super(SkinningUtilities, self).currentWidget()

    def widgets(self):
        """ Override base method for autocompletion

        :return:
        :rtype: list[GuiAdvanced or GuiCompact]
        """
        return super(SkinningUtilities, self).widgets()

    # ------------------
    # LOGIC
    # ------------------

    @toolsetwidget.ToolsetWidget.undoDecorator
    def skinTransfer(self):
        bindskin.transferSkinWeightsSelected()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def copySkinWeights(self):
        bindskin.copySkinWeightsSel()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def pasteSkinWeights(self):
        bindskin.pasteSkinWeightsSel()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def skinToggle(self):
        bindskin.toggleSkinClusterListSelected()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def addJoints(self):
        bindskin.addJointsToSkinnedSelected()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def removeJoints(self):
        bindskin.removeInfluenceSelected()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def combineSkinMeshes(self):
        bindskin.combineSkinnedMeshesSelected(constructionHistory=True)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def duplicateOriginal(self):
        bindskin.duplicateSelectedBeforeBind()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def mirror(self, mirrorInverse=False):
        bindskin.mirrorSkinSelection(mirrorMode='YZ', mirrorInverse=mirrorInverse)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def autoRenameSkinCluster(self):
        bindskin.renameSelSkinClusters()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def weightHammer(self):
        bindskin.hammerWeights()

    @toolsetwidget.ToolsetWidget.undoDecorator
    def skinSelected(self):
        bindskin.bindSkinSelected(toSelectedBones=True, maximumInfluences=5, maxEditLimit=5, bindMethod=0,
                                  displayMessage=True)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def skinSelectedRigid(self):
        bindskin.bindSkinSelected(toSelectedBones=True, maximumInfluences=0, maxEditLimit=5, bindMethod=0,
                                  displayMessage=True)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def skinSelectedHeatMap(self):
        bindskin.bindSkinSelected(bindMethod=2)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def skinSelectedGeodesic(self):
        bindskin.bindSkinSelected(bindMethod=3)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def skinHierarchyDefaults(self):
        bindskin.bindSkinSelected(toSelectedBones=False, maximumInfluences=5, maxEditLimit=5, bindMethod=0,
                                  displayMessage=True)

    @toolsetwidget.ToolsetWidget.undoDecorator
    def unbindSkin(self):
        bindskin.unbindSkinSelected()

    # ------------------
    # CONNECTIONS
    # ------------------

    def uiConnections(self):
        """Add all UI connections here, button clicks, on changed etc"""
        for widget in self.widgets():
            widget.skinTransferBtn.clicked.connect(self.skinTransfer)
            widget.skinToggleBtn.clicked.connect(self.skinToggle)
            widget.copySkinBtn.clicked.connect(self.copySkinWeights)
            widget.pasteSkinBtn.clicked.connect(self.pasteSkinWeights)
            widget.addJointsBtn.clicked.connect(self.addJoints)
            widget.removeInfluencesBtn.clicked.connect(self.removeJoints)
            widget.combineSkinMeshesBtn.clicked.connect(self.combineSkinMeshes)
            widget.duplicateOriginalBtn.clicked.connect(self.duplicateOriginal)
            widget.mirrorXBtn.clicked.connect(partial(self.mirror, mirrorInverse=False))
            widget.mirrorNegXBtn.clicked.connect(partial(self.mirror, mirrorInverse=True))
            widget.nameSkinClusterBtn.clicked.connect(self.autoRenameSkinCluster)
            widget.weightHammerBtn.clicked.connect(self.weightHammer)
            widget.bindSkinBtn.clicked.connect(self.skinSelected)
            widget.unbindSkinBtn.clicked.connect(self.unbindSkin)
            widget.bindSkinBtn.addAction("Skin Selected - Default Settings",
                                         mouseMenu=QtCore.Qt.RightButton,
                                         icon=iconlib.icon("skinYoga"),
                                         connect=self.skinSelected)
            widget.bindSkinBtn.addAction("Skin Selected - Heat Map",
                                         mouseMenu=QtCore.Qt.RightButton,
                                         icon=iconlib.icon("skinYoga"),
                                         connect=self.skinSelectedHeatMap)
            widget.bindSkinBtn.addAction("Skin Selected - Geodesic Map",
                                         mouseMenu=QtCore.Qt.RightButton,
                                         icon=iconlib.icon("skinYoga"),
                                         connect=self.skinSelectedGeodesic)
            widget.bindSkinBtn.addAction("Skin Selected - Rigid",
                                         mouseMenu=QtCore.Qt.RightButton,
                                         icon=iconlib.icon("skinYoga"),
                                         connect=self.skinSelectedRigid)
            widget.bindSkinBtn.addAction("Skin Hierarchy - Default Settings",
                                         mouseMenu=QtCore.Qt.RightButton,
                                         icon=iconlib.icon("skinYoga"),
                                         connect=self.skinHierarchyDefaults)


class GuiWidgets(QtWidgets.QWidget):
    def __init__(self, parent=None, properties=None, uiMode=None, toolsetWidget=None):
        """Builds the main widgets for all GUIs

        properties is the list(dictionaries) used to set logic and pass between the different UI layouts
        such as compact/adv etc

        :param parent: the parent of this widget
        :type parent: qtObject
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: object
        :param uiMode: 0 is compact ui mode, 1 is advanced ui mode
        :type uiMode: int
        """
        super(GuiWidgets, self).__init__(parent=parent)
        self.properties = properties
        # Skin Transfer ---------------------------------------
        tooltip = "Transfers the skinning from one mesh to another. \n" \
                  "Meshes can have different topology. Transfers in World Space. \n\n" \
                  "Select the skinned mesh, then shift select the target, and run."
        self.skinTransferBtn = elements.AlignedButton("Skin Transfer",
                                                      icon="transfer",
                                                      toolTip=tooltip)
        # Skin Toggle ---------------------------------------
        tooltip = "Toggles the skinning on/off for selected meshes. \n" \
                  "Affects related skin clusters. \n" \
                  "Useful for moving joint pivots. \n\n" \
                  "Run once; the skin cluster will be disabled.\n" \
                  "Run again, and the cluster will be re-enabled."
        self.skinToggleBtn = elements.AlignedButton("Skin Toggle",
                                                    icon="on",
                                                    toolTip=tooltip)
        # Copy Skin Weights ---------------------------------------
        tooltip = "Choose a mesh with skinning applied and run to copy \n" \
                  "skin weight values."
        self.copySkinBtn = elements.AlignedButton("Copy Skin Weights",
                                                  icon="copy",
                                                  toolTip=tooltip)
        # Paste Skin Weights ---------------------------------------
        tooltip = "Choose a mesh or component (vertex, edge, or face) selection, \n" \
                  "and run to paste skin weights."
        self.pasteSkinBtn = elements.AlignedButton("Paste Skin Weights",
                                                   icon="paste",
                                                   toolTip=tooltip)
        # Add Joints ---------------------------------------
        tooltip = "Select joint/s and a mesh to add the joint to the related skin cluster."
        self.addJointsBtn = elements.AlignedButton("Add Joints",
                                                   icon="plus",
                                                   toolTip=tooltip)
        # Remove Influences ---------------------------------------
        tooltip = "Select joint/s and a mesh to remove the joint from the related skin cluster."
        self.removeInfluencesBtn = elements.AlignedButton("Remove Joints",
                                                          icon="minusSolid",
                                                          toolTip=tooltip)
        # Combine Mesh ---------------------------------------
        tooltip = "Select meshes and run to combine the objects \n" \
                  "without destroying the skinning. \n" \
                  "At least one mesh should have skinning."
        self.combineSkinMeshesBtn = elements.AlignedButton("Combine Skin Meshes",
                                                           icon="combineCurve",
                                                           toolTip=tooltip)
        # Duplicate Original  ---------------------------------------
        tooltip = "Duplicates the selected mesh before the mesh was skinned. \n" \
                  "Attributes are unlocked. \n" \
                  "Useful for blendshapes, UVs, and other tasks."
        self.duplicateOriginalBtn = elements.AlignedButton("Duplicate Original",
                                                           icon="duplicate",
                                                           toolTip=tooltip)
        # Mirror +X ---------------------------------------
        tooltip = "Mirrors the skinning from +X to -X.  \n" \
                  "Mesh should be in it's default bind pose. \n\n" \
                  "If two meshes are selected will try to mirror \n" \
                  "from the first selected object to the second, \n" \
                  "and mirror direction is ignored."
        self.mirrorXBtn = elements.AlignedButton("Mirror +X to -X",
                                                 icon="symmetryTri",
                                                 toolTip=tooltip)
        # Mirror -X  ---------------------------------------
        tooltip = "Mirrors the skinning from -X to +X.  \n" \
                  "Mesh should be in it's default bind pose. \n\n" \
                  "If two meshes are selected will try to mirror \n" \
                  "from the first selected object to the second, \n" \
                  "and mirror direction is ignored."
        self.mirrorNegXBtn = elements.AlignedButton("Mirror -X to +X",
                                                    icon="symmetryTri",
                                                    toolTip=tooltip)
        # Auto Rename From Meshes ---------------------------------------
        tooltip = "Automatically renames the selected mesh's skin cluster \n" \
                  "Will match the mesh eg. - `meshName_skin`"
        self.nameSkinClusterBtn = elements.AlignedButton("Auto Name Skin Cluster",
                                                         icon="editText",
                                                         toolTip=tooltip)
        # Weight Hammer  ---------------------------------------
        tooltip = "Weights the selected vertices to match the weights of the surrounding vertices."
        self.weightHammerBtn = elements.AlignedButton("Hammer Weights",
                                                      icon="hammer",
                                                      toolTip=tooltip)
        # Bind Skin ---------------------------------------
        tooltip = "Selected meshes and joints to skin with default settings. \n" \
                  "  - Skins to the selected joints, not the joint hierarchy. \n" \
                  "  - Closest distance. \n" \
                  "  - 5 influences and max influences per joint."
        self.bindSkinBtn = elements.AlignedButton("Skin Selected (right-click)",
                                                  icon="skinYoga",
                                                  toolTip=tooltip)
        # Unbind Skin ---------------------------------------
        tooltip = "Deletes skinning from the selected meshes."
        self.unbindSkinBtn = elements.AlignedButton("Unbind Skin",
                                                    icon="trash",
                                                    toolTip=tooltip)


class GuiCompact(GuiWidgets):
    def __init__(self, parent=None, properties=None, uiMode=UI_MODE_COMPACT, toolsetWidget=None):
        """Adds the layout building the compact version of the GUI:

            default uiMode - 0 is advanced (UI_MODE_COMPACT)

        :param parent: the parent of this widget
        :type parent: qtObject
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: list[dict]
        """
        super(GuiCompact, self).__init__(parent=parent, properties=properties, uiMode=uiMode,
                                         toolsetWidget=toolsetWidget)
        # Main Layout ---------------------------------------
        mainLayout = elements.vBoxLayout(self, margins=(uic.WINSIDEPAD, uic.WINBOTPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SPACING)
        # Transfer Layout ---------------------------------------
        skinTransferLayout = elements.hBoxLayout(self, spacing=uic.SPACING)
        skinTransferLayout.addWidget(self.skinTransferBtn, 1)
        skinTransferLayout.addWidget(self.skinToggleBtn, 1)
        # Copy Paste Layout ---------------------------------------
        copyPasteSkinLayout = elements.hBoxLayout(self, spacing=uic.SPACING)
        copyPasteSkinLayout.addWidget(self.copySkinBtn, 1)
        copyPasteSkinLayout.addWidget(self.pasteSkinBtn, 1)
        # Bind Layout ---------------------------------------
        addRemoveLayout = elements.hBoxLayout(self, spacing=uic.SPACING)
        addRemoveLayout.addWidget(self.addJointsBtn, 1)
        addRemoveLayout.addWidget(self.removeInfluencesBtn, 1)
        # Combine Duplicate Layout ---------------------------------------
        combineDupLayout = elements.hBoxLayout(self, spacing=uic.SPACING)
        combineDupLayout.addWidget(self.combineSkinMeshesBtn, 1)
        combineDupLayout.addWidget(self.duplicateOriginalBtn, 1)
        # Mirror X Layout ---------------------------------------
        mirrorLayout = elements.hBoxLayout(self, spacing=uic.SPACING)
        mirrorLayout.addWidget(self.mirrorXBtn, 1)
        mirrorLayout.addWidget(self.mirrorNegXBtn, 1)
        # Auto Name Layout ---------------------------------------
        autoNameLayout = elements.hBoxLayout(self, spacing=uic.SPACING)
        autoNameLayout.addWidget(self.nameSkinClusterBtn, 1)
        autoNameLayout.addWidget(self.weightHammerBtn, 1)
        # Bind Layout ---------------------------------------
        bindUnbindLayout = elements.hBoxLayout(self, spacing=uic.SPACING)
        bindUnbindLayout.addWidget(self.bindSkinBtn, 1)
        bindUnbindLayout.addWidget(self.unbindSkinBtn, 1)
        # Add To Main Layout ---------------------------------------
        mainLayout.addLayout(skinTransferLayout)
        mainLayout.addLayout(copyPasteSkinLayout)
        mainLayout.addLayout(combineDupLayout)
        mainLayout.addLayout(addRemoveLayout)
        mainLayout.addLayout(mirrorLayout)
        mainLayout.addLayout(autoNameLayout)
        mainLayout.addLayout(bindUnbindLayout)


class GuiAdvanced(GuiWidgets):
    def __init__(self, parent=None, properties=None, uiMode=UI_MODE_ADVANCED, toolsetWidget=None):
        """Adds the layout building the advanced version of the GUI:

            default uiMode - 1 is advanced (UI_MODE_ADVANCED)

        :param parent: the parent of this widget
        :type parent: qtObject
        :param properties: the properties dictionary which tracks all the properties of each widget for UI modes
        :type properties: list[dict]
        """
        super(GuiAdvanced, self).__init__(parent=parent, properties=properties, uiMode=uiMode,
                                          toolsetWidget=toolsetWidget)
        # Main Layout ---------------------------------------
        mainLayout = elements.vBoxLayout(self, margins=(uic.WINSIDEPAD, uic.WINBOTPAD, uic.WINSIDEPAD, uic.WINBOTPAD),
                                         spacing=uic.SPACING)
        # Transfer Layout ---------------------------------------
        skinTransferLayout = elements.hBoxLayout(spacing=uic.SPACING)
        skinTransferLayout.addWidget(self.skinTransferBtn, 1)
        skinTransferLayout.addWidget(self.skinToggleBtn, 1)
        # Bind Layout ---------------------------------------
        addRemoveLayout = elements.hBoxLayout(spacing=uic.SPACING)
        addRemoveLayout.addWidget(self.addJointsBtn, 1)
        addRemoveLayout.addWidget(self.removeInfluencesBtn, 1)
        # Combine Duplicate Layout ---------------------------------------
        combineDupLayout = elements.hBoxLayout(spacing=uic.SPACING)
        combineDupLayout.addWidget(self.combineSkinMeshesBtn, 1)
        combineDupLayout.addWidget(self.duplicateOriginalBtn, 1)
        # Bind Layout ---------------------------------------
        bindUnbindLayout = elements.hBoxLayout(spacing=uic.SPACING)
        bindUnbindLayout.addWidget(self.bindSkinBtn, 1)
        bindUnbindLayout.addWidget(self.unbindSkinBtn, 1)
        # Mirror X Layout ---------------------------------------
        mirrorLayout = elements.hBoxLayout(spacing=uic.SPACING)
        mirrorLayout.addWidget(self.mirrorXBtn, 1)
        mirrorLayout.addWidget(self.mirrorNegXBtn, 1)
        # Add To Main Layout ---------------------------------------
        mainLayout.addLayout(skinTransferLayout)
        mainLayout.addLayout(combineDupLayout)
        mainLayout.addLayout(addRemoveLayout)
        mainLayout.addLayout(mirrorLayout)
        mainLayout.addLayout(bindUnbindLayout)
