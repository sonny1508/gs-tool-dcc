from zoo.libs.pyqt import utils
from zoo.libs.pyqt.widgets import elements
from zoovendor.Qt import QtWidgets, QtCore


class SideNameWidget(QtWidgets.QWidget):
    renamed = QtCore.Signal(str)

    def __init__(self, model, parent=None, showLabel=True, showArrow=True):
        """
        :param model: The component model for this widget to operate on
        :type model: :class:`zoo.apps.hiveartistui.model.ComponentModel`
        :param parent:
        :type parent: :class:`QtWidgets.QWidget`
        """
        super(SideNameWidget, self).__init__(parent=parent)
        self.showLabel = showLabel
        self.model = model
        self._initUi()
        styleSheet = """
        QComboBox {
            background-color: #30000000;
        }
        QComboBox:hover {
            background-color: #88111111;
        }
        QComboBox::drop-down {
            background-color: transparent;
            border-left: 0px solid #33FF1111;
        }
        QComboBox::drop-down:pressed {
            background-color: #8871a0d0;
        }
        
        QComboBox:pressed {
            background-color: #8871a0d0;
        }


        """

        hideArrow = """
        QComboBox::down-arrow {
            image: none;
        }
        
        """
        # used when the displayed in the component widget titlebar
        if not showArrow:
            styleSheet += hideArrow
            self.setStyleSheet(styleSheet)

    def _initUi(self):

        layout = elements.hBoxLayout(parent=self)
        self._sideComboBox = elements.ComboBoxRegular("Side",
                                                      [],
                                                      labelRatio=4,
                                                      boxRatio=16,
                                                      sortAlphabetically=True,
                                                      parent=self,
                                                      supportMiddleMouseScroll=False)
        self._sideComboBox.itemChanged.connect(self.onValueChanged)
        self._sideComboBox.box.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.updateCombo()
        layout.addWidget(self._sideComboBox)
        if not self.showLabel:
            self._sideComboBox.label.hide()

    def updateCombo(self):
        self._sideComboBox.blockSignals(True)
        namingObj = self.model.component.namingConfiguration()
        sideField = namingObj.field("side")
        sides = sorted(list([i.name for i in sideField.keyValues()]))
        side = sideField.valueForKey(self.model.side)
        self._sideComboBox.clear()
        self._sideComboBox.addItems(sides)
        self._sideComboBox.setToText(side, QtCore.Qt.MatchFixedString | QtCore.Qt.MatchCaseSensitive)
        self._sideComboBox.blockSignals(False)

    def onValueChanged(self, event=None):
        """

        :param event: Event with all the values related to the change.
        :type event: zoo.libs.pyqt.extended.combobox.ComboItemChangedEvent
        :return:
        :rtype:
        """
        side = str(self.model.component.namingConfiguration().field("side").valueForKey(event.text))
        self.renamed.emit(side)


class ParentWidget(QtWidgets.QWidget):
    parentChanged = QtCore.Signal(object, object)  # component, guide

    def __init__(self, rigModel=None, componentModel=None, parent=None):
        """
        :param rigModel: The component model for this widget to operate on
        :type rigModel: :class:`zoo.apps.hiveartistui.model.RigModel`
        :param componentModel: The Hive UI component Data Model.
        :type componentModel: :class:`zoo.apps.hiveartistui.model.ComponentModel`
        :param parent:
        :type parent: :class:`QtWidgets.QWidget`
        """
        super(ParentWidget, self).__init__(parent=parent)
        self.currentParent = (None, None)
        self.itemData = []
        self.componentModel = componentModel
        self.rigModel = rigModel

        layout = elements.hBoxLayout(parent=self)
        self._parentComboBox = elements.ComboBoxRegular(label="Parent",
                                                        boxRatio=16, labelRatio=4,
                                                        parent=self,
                                                        supportMiddleMouseScroll=False)
        self._parentComboBox.setFixedHeight(utils.dpiScale(21))
        self._parentComboBox.currentIndexChanged.connect(self.onValueChanged)
        layout.addWidget(self._parentComboBox)

    def initUi(self):
        self.updateCombo()

    def updateCombo(self, softRefresh=False):
        self._hardRefresh()

    def isCurrentParent(self, component, guide):
        """ Checks if the component + guide combination is the same as the current parent

        :param component:
        :type component: :class:`zoo.libs.hive.base.component.Component`
        :param guide:
        :type guide:
        :return:
        :rtype:
        """
        if self.currentParent[0] is not None:
            return self.currentParent == (component, guide)

    def _hardRefresh(self):
        """ Do a hard refresh.
        Clear out the combobox and add it all based on the rigs and components

        :return:
        :rtype:
        """
        self._parentComboBox.blockSignals(True)
        self._parentComboBox.clear()
        self.itemData = [[None, None]]
        self._parentComboBox.addItem("")

        if not self.rigModel:
            self._parentComboBox.blockSignals(False)
            return
        self.currentParent = self.componentModel.component.componentParentGuide()
        comboSet = False
        rig = self.rigModel.rig
        for i, c in enumerate(rig.components()):
            if c == self.componentModel.component:
                continue
            guideLayer = c.guideLayer()
            if not guideLayer:
                continue
            for g in guideLayer.iterGuides(includeRoot=False):
                self._parentComboBox.addItem(self.itemName(c, g))
                self.itemData.append([c, g])

                if self.isCurrentParent(c, g) and not comboSet:
                    comboSet = True
                    self._parentComboBox.setCurrentIndex(self._parentComboBox.count() - 1)

        self._parentComboBox.blockSignals(False)

    @classmethod
    def itemName(cls, component, guide):
        return '[{} {}] {}'.format(component.name(), component.side(), guide.name(includeNamespace=False))

    def onValueChanged(self, event):
        """ on Value Changed

        :param event: Event with all the values related to the change.
        :type event: zoo.libs.pyqt.extended.combobox.ComboItemChangedEvent
        :return:
        :rtype:
        """
        data = self.itemData[self._parentComboBox.currentIndex()]
        self.parentChanged.emit(data[0], data[1])  # component, guide
        self.currentParent = data[0], data[1]
