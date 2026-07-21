from GSValidation.py23 import *
from GSValidation.qt_util import *

import os
from functools import partial
from maya import cmds

from GSValidation import mayaWidget, GSValidation_utils
from GSValidation.GSValidation_utils import *
from GSValidation.messageProgressBar import MessageProgressBar
__VERSION__ = "1.0"
_DIR = os.path.dirname(__file__)
#_DIR = os.path.dirname('C:\Users\GS50\Documents\maya\2018\scripts\GSValidation')

from importlib import reload
reload(GSValidation_utils)

class ValidationUI(mayaWidget.DockWidget):

    toolName = 'GS Validation Tool: %s' % __VERSION__

    def __init__(self, newPlacement=False, parent=None):
        super(ValidationUI, self).__init__(parent)
        self.setWindowTitle(self.__class__.toolName)

        mainLayout = nullVBoxLayout()
        self.setLayout(mainLayout)

        self.__defaults()
        self.__uiElements()
        self.addSearchFunctions()
        self.addErrorFunctions()

        if not newPlacement:
            self.loadUIState()

    def __defaults(self):
        _ini = os.path.join(_DIR, 'settings.ini')
        self.settings = QSettings(_ini, QSettings.IniFormat)

        self.searchFunctions = OrderedDict()
        self.searchFunctions['Modelling'] = ["History", "xForms", "Holes", "Locked normals", "N-gons", "Legal UV's", "Lamina faces", "Zero edge lenght", "Zero geometry data", "Concave faces"]                                        
        self.searchFunctions['Other'] = ["Pasted Objects", "Default Shader", "Pasted Shaders", "Keyed Objects"]
        self.checkConnections = OrderedDict()

    def __uiElements(self):
        # --- top
        topLayout = nullHBoxLayout()
        #topLayout.addItem(QSpacerItem(2, 2, QSizePolicy.Expanding, QSizePolicy.Minimum))
        #topLayout.addItem(QSpacerItem(2, 2, QSizePolicy.Expanding, QSizePolicy.Minimum))

        self.layout().addLayout(topLayout)
        # --- search + errorList
        vLayout = QHBoxLayout()
        self.layout().addLayout(vLayout)

        self._splitter = QSplitter()
        vLayout.addWidget(self._splitter)

        self.errorList = QGroupBox("Errors:")
        font2 = QFont()
        font2.setPointSize(12)
        font2.setBold(True)
        font2.setWeight(75)
        self.errorList.setFont(font2)

        for w in [self.errorList]:
            w.setLayout(nullVBoxLayout(size=3))
            self._splitter.addWidget(w)

        # --- progress and execute
        exLayout = nullHBoxLayout()
        self.exButton = QPushButton("Check")
        self.exButton.setMinimumSize(QSize(0, 30))
        font1 = QFont()
        font1.setPointSize(12)
        font1.setBold(True)
        font1.setWeight(75)
        self.exButton.setFont(font1)
        self.exButton.clicked.connect(self.checkScene)
        self._detailProgressBar = MessageProgressBar()
        self._detailProgressBar.setMinimumSize(QSize(0, 30))
        for w in [self.exButton, self._detailProgressBar]:
            exLayout.addWidget(w)
        self.layout().addLayout(exLayout)

    def addErrorFunctions(self):
        selectLayout = nullHBoxLayout()
        self.errorTree = QTreeWidget()
        self.errorTree.setHeaderHidden(True)
        self.errorTree.itemSelectionChanged.connect(self.handleChanged)
        font = QFont()
        font.setPointSize(11)
        font.setBold(True)
        font.setWeight(75)
        self.errorTree.setFont(font)
 
        self.errorList.layout().addLayout(selectLayout)
        self.errorList.layout().addWidget(self.errorTree)

        self._extraGrpBox = QGroupBox()
        self.errorList.layout().addWidget(self._extraGrpBox)

    def handleChanged(self, *args):
        items = []
        allSelected = self.errorTree.selectedItems()
        if allSelected != []:
            for item in allSelected:
                if str(item.toolTip(0)) != 'emptyData':
                    items.append(str(item.toolTip(0)))
            if len(items) == 0:
                cmds.select(cl=True)
            else:
                cmds.select(items)

    def addSearchFunctions(self):
        for topic, info in self.searchFunctions.items():

            topicGrp = QGroupBox(topic.upper())
            topicGrp.setStyleSheet("QGroupBox { border: 2px solid gray; border-radius: 10px; } ")
            topicGrp.setCheckable(True)
            topicGrp.setLayout(nullVBoxLayout(size=5))
            topicGrp.layout().addWidget(QLabel())
            topicGrp.toggled.connect(self.onToggled)

            for check in info:
                _check = QCheckBox(check)
                _check.setChecked(True)
                topicGrp.layout().addWidget(_check)
                self.checkConnections[check] = True
                _check.toggled.connect(partial(self.toggleConn, _check, check))

    def toggleConn(self, sender, check, *args):
        if self.sender() is not None:
            sender = self.sender()
        self.checkConnections[check] = sender.isChecked()

    def onToggled(self, on):
        # hacky override to make sure everything in the groupbox is not disabled on click
        for box in self.sender().findChildren(QCheckBox):
            box.setChecked(on)
            box.setEnabled(True)

    def checkScene(self):
        self.errorTree.clear()
        self.allObjects = cmds.ls(o=True, g=True, l=True)
        if len(self.allObjects) == 0:
            cmds.error('no objects in scene!')
            return

        self.allShapes = cmds.ls(o=True, g=True)
        self.allCommonShaders = cmds.ls(type=["lambert", "phong", "blinn", "anisotropic", "phongE"])
        self.allobjectsparents = cmds.listRelatives(self.allObjects, p=True, f=True)
        self.uniqueGeometryList = set(self.allobjectsparents)

        _functions = {
            "History": partial(history_objects, self.uniqueGeometryList, self.allShapes, self._detailProgressBar),
            "xForms": partial(xforms, self.uniqueGeometryList, self._detailProgressBar),
            "Holes": partial(holes, self._detailProgressBar),
            "Locked normals": partial(locked_normals, self.uniqueGeometryList, self._detailProgressBar),
            "N-gons": partial(ngons, self._detailProgressBar),
            "Legal UV's": partial(legal_uvs, self.uniqueGeometryList, self._detailProgressBar),
            "Lamina faces": partial(lamina_faces, self.uniqueGeometryList, self._detailProgressBar),
            "Zero edge lenght": partial(zero_edge_length, self._detailProgressBar),
            "Zero geometry data": partial(zero_geometry_area, self._detailProgressBar),
            #"Unmapped faces": partial(unmapped_faces, self._detailProgressBar),
            "Concave faces": partial(concave_faces, self._detailProgressBar),
            "Pasted Objects": partial(default_and_pasted_objects, self.uniqueGeometryList, self._detailProgressBar),
            "Default Shader": partial(default_shader,self.uniqueGeometryList, self._detailProgressBar),
            "Pasted Shaders": partial(all_shaders, self.allCommonShaders, self._detailProgressBar),
            "Keyed Objects": partial(keyed_objects, self.uniqueGeometryList, self._detailProgressBar)
        }

        amount = sum(self.checkConnections.values())
        percentage = 99.0 / amount

        for index, (name, toUse) in enumerate(self.checkConnections.items()):
            if not toUse:
                continue
            _dict = _functions[name]()
            for key, value in _dict.items():
                if key in ["res", "avg", "bbox", "tri"]:
                    continue
                self.createListWidget(value, key)
            #setProgress(index * percentage, self._globalProgressBar, "Processing %s" % name)

        #setProgress(100, self._globalProgressBar, "Finished")

    def addParent(self, parent, column, title, data):
        item = QTreeWidgetItem(parent, [title])
        item.setData(column, Qt.UserRole, data)
        item.setChildIndicatorPolicy(QTreeWidgetItem.ShowIndicator)
        item.setExpanded(False)
        item.setToolTip(column, data)
        return item

    def addChild(self, parent, column, title, data):
        item = QTreeWidgetItem(parent, [title])
        item.setData(column, Qt.UserRole, data)
        item.setToolTip(column, data)
        return item

    def createListWidget(self, inPutList, title):
        self.CurrentItem = self.addParent(self.errorTree.invisibleRootItem(), 0, title, 'emptyData')

        if inPutList == []:
            self.addChild(self.CurrentItem, 0, "'empty'", "emptyData")
            self.CurrentItem.setForeground(0, QBrush(QColor("green")))
        else:
            self.CurrentItem.setForeground(0, QBrush(QColor("red")))
            for object in inPutList:
                self.addChild(self.CurrentItem, 0, object.split('|')[-1], object)

    def saveUIState(self):
        """ save the current state of the ui in a seperate ini file, this should also hold information later from a seperate settings window

        :todo: instead of only geometry also store torn of tabs for each posssible object
        :todo: save the geometries of torn of tabs as well
        """
        self.settings.setValue("geometry", self.saveGeometry())

    def loadUIState(self):
        """ load the previous set information from the ini file where possible, if the ini file is not there it will start with default settings
        """
        getGeo = self.settings.value("geometry", None)
        if not getGeo in [None, "None"]:
            self.restoreGeometry(getGeo)

    def hideEvent(self, event):
        """ the hide event is something that is triggered at the same time as close,
        sometimes the close event is not handled correctly by maya so we add the save state in here to make sure its always triggered
        :note: its only storing info so it doesnt break anything
        """
        self.saveUIState()

        if not event is None:
            super(ValidationUI, self).hideEvent(event)

    def closeEvent(self, event):
        """ the close event,
        we save the state of the ui but we also force delete a lot of the skinningtool elements,
        normally python would do garbage collection for you, but to be sure that nothing is stored in memory that does not get deleted we
        force the deletion here as well. somehow this avoids crashes in maya!
        """
        self.saveUIState()
        self.deleteLater()
        return True


def showUI(newPlacement=False):
    """ convenience function to show the current user interface in maya,

    :param newPlacement: if `True` will force the tool to not read the ini file, if `False` will open the tool as intended
    :type newPlacement: bool
    """
    dock = ValidationUI(newPlacement, parent=None)
    dock.run()
    return dock


#showUI()