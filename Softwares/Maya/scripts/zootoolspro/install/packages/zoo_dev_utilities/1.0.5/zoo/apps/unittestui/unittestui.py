import logging
import unittest
from unittest.suite import TestSuite

from zoovendor.Qt import QtCore, QtWidgets

from zoo.libs.pyqt.widgets import elements
from zoo.libs.pyqt.extended import treeviewplus

from zoo.libs.utils import unittestBase
from zoo.libs import iconlib

from zoo.core import api as zooapi

from zoo.apps.unittestui import core


logger = logging.getLogger(__name__)


class TestRunnerDialog(elements.ZooWindow):
    windowSettingsPath = "zoo/unittestui"

    def __init__(self, title="Unit Test Runner", parent=None):
        super(TestRunnerDialog, self).__init__(name="unittestUI", title=title, parent=parent, resizable=True,
                                               alwaysShowAllTitle=True,
                                               width=600, height=500,
                                               minButton=True, maxButton=True, onTop=False,
                                               titleBar=None, overlay=True, minimizeEnabled=True,
                                               saveWindowPref=False)
        self.results = {}
        titleBarLayout = self.titleBar.contentsLayout
        action = elements.ExtendedButton(icon=iconlib.icon("run_all_tests"), parent=self)
        action.setObjectName('run_all_tests')
        action.setToolTip('Run all tests.')
        action.leftClicked.connect(self.runAllTests)

        titleBarLayout.addWidget(action)
        action = elements.ExtendedButton(icon=iconlib.icon('run_selected_tests'), parent=self)
        action.setObjectName('run_selected_tests')
        action.setToolTip('Run all selected tests.')
        action.leftClicked.connect(self.runSelectedTests)
        titleBarLayout.addWidget(action)

        action = elements.ExtendedButton(icon=iconlib.icon('run_failed_tests'), parent=self)
        action.setObjectName('run_failed_tests')
        action.setToolTip('Run all failed tests.')
        action.leftClicked.connect(self.runFailedTests)
        titleBarLayout.addWidget(action)

        vbox = elements.vBoxLayout()
        self.setMainLayout(vbox)

        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal, self)

        self.testView = treeviewplus.TreeViewPlus(parent=self, expand=False)
        self.testView.setSearchable(True)
        self.testView.treeView.setHeaderHidden(True)
        self.testView.setAlternatingColorEnabled(False)

        splitter.addWidget(self.testView)
        self.outputConsole = QtWidgets.QTextEdit(parent=self)
        self.outputConsole.setReadOnly(True)
        splitter.addWidget(self.outputConsole)
        vbox.addWidget(splitter)
        splitter.setStretchFactor(1, 4)
        self.stream = core.TestCaptureStream(self.outputConsole)

        self.refreshRepoSwitcher()

    def _rediscoverTestSuite(self, test=None):
        """ Get all test suites by test path.

        :param test: The test path eg: "tests.libs.ControlCreator". If none, all tests will be used.
        :return:
        """
        testSuites = []
        for pkgName, info in self.results.items():
            packageSuite = unittestBase.getTests([info["path"]],
                                                 test=test,
                                                 topLevelDir=info["root"])
            packageSuite._metaData = info
            testSuites.append(packageSuite)
        return TestSuite(testSuites)

    def refreshRepoSwitcher(self):
        self.results = {}
        for paths, package in zooapi.currentConfig().resolver.testPackagesInCurrentEnv():
            for p in paths:
                self.results[package.name] = {"package": package,
                                              "path": p,
                                              "root": package.root}

        self.model = core.TestDataModel(None, parent=self)
        self.model.refresh(self._rediscoverTestSuite())
        self.testView.setModel(self.model)
        self.testView.refresh()

    def runAllTests(self):
        """Callback method to run all the tests found."""
        self.outputConsole.clear()
        self.model.runTests(self.stream,
                            self._rediscoverTestSuite())

    def runSelectedTests(self):
        """Callback method to run the selected tests in the UI."""
        indices = self.testView.selectedQIndices()
        if not indices:
            return

        # Remove any child nodes if parent nodes are in the list.  This will prevent duplicate
        # tests from being run.
        testSuite = unittest.TestSuite()
        for index in indices:
            tests = index.internalPointer().test
            if isinstance(tests, unittest.TestSuite):
                testSuite.addTests(tests)
            else:
                testSuite.addTest(tests)
        self.outputConsole.clear()
        self.model.runTests(self.stream, testSuite)

    def runFailedTests(self):
        """Callback method to run all the tests with fail or error statuses."""
        testSuite = unittest.TestSuite()
        for node in self.model.node_lookup.values():
            if isinstance(node.test, unittest.TestCase) and node.status() in {core.TestStatus.fail,
                                                                              core.TestStatus.error}:
                testSuite.addTest(node.test)
        self.outputConsole.clear()
        self.model.runTests(self.stream, testSuite)

    def closeEvent(self, event):
        """Close event to clean up everything."""
        self.deleteLater()


