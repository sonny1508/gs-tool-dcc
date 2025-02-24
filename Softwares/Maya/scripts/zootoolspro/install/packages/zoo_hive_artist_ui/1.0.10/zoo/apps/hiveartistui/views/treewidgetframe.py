from zoo.libs.pyqt import utils
from zoo.libs.pyqt.widgets import elements, searchwidget
from zoo.libs.pyqt.widgets import groupedtreewidget
from zoo.libs.pyqt.widgets import slidingwidget
from zoovendor.Qt import QtWidgets, QtCore


class SearchSlidingWidget(slidingwidget.SlidingWidget):

    def widgetFocusOut(self, event=None):
        if self.primaryWidget is not None and self.primaryWidget.text() == "":
            return super(SearchSlidingWidget, self).widgetFocusOut(event)


class TreeWidgetFrame(QtWidgets.QFrame):
    def __init__(self, parent=None, title=""):
        super(TreeWidgetFrame, self).__init__(parent=parent)
        self.mainLayout = elements.vBoxLayout(self)

        self.titleLabel = elements.ClippedLabel(parent=self, text=title.upper())
        self.searchEdit = searchwidget.SearchLineEdit(parent=self)
        self.slidingWidget = SearchSlidingWidget(self)
        self.treeWidget = None  # type: groupedtreewidget.GroupedTreeWidget

        self.toolbarLayout = elements.hBoxLayout(margins=(10, 6, 6, 0), spacing=0)

    def initUi(self, treeWidget):
        """Initialize Ui
        """
        self.treeWidget = treeWidget
        self.setupToolbar()

        self.mainLayout.addLayout(self.toolbarLayout)
        self.mainLayout.addWidget(self.treeWidget)

        self.setLayout(self.mainLayout)

    def setupToolbar(self):
        """The toolbar for the ComponentTreeView which will have widgets such as the searchbar,
        and other useful buttons.

        :return: The toolbar Qlayout
        :rtype: :class:`QtWidgets.QHBoxlayout`
        """
        self.searchEdit.setMinimumSize(utils.sizeByDpi(QtCore.QSize(21, 20)))
        self.slidingWidget.setWidgets(self.searchEdit, self.titleLabel)
        self.toolbarLayout.addWidget(self.slidingWidget)

        line = QtWidgets.QFrame(parent=self)
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.toolbarLayout.addWidget(line)

        return self.toolbarLayout

    def connections(self):
        self.searchEdit.textChanged.connect(self.onSearchChanged)

    def onSearchChanged(self):
        """Filter the results based on the text inputted into the search bar
        """

        if self.treeWidget is not None:
            text = self.searchEdit.text().lower()
            self.treeWidget.filter(text)
            self.treeWidget.updateTreeWidget()

    def addGroup(self, name="", expanded=True):
        if self.treeWidget is not None:
            groupWgt = groupedtreewidget.GroupWidget(name, hideTitleFrame=True)
            groupWgt.setFixedHeight(10)

            return self.treeWidget.addGroup(name, expanded=expanded, groupWgt=groupWgt)

        groupedtreewidget.logger.error("TreeWidgetFrame.addGroup(): TreeWidget shouldn't be None!")

    def deleteGroup(self):
        print("Delete Placeholder")

    def updateTreeWidget(self):
        """ Updates the TreeWidget UI for QT sizehints and visuals
        """
        if self.treeWidget is not None:
            self.treeWidget.updateTreeWidget()
