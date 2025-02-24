import traceback
import unittest
import logging
import weakref
from functools import partial

from zoo.libs.pyqt.models import datasources, treemodel, constants
from zoovendor.Qt import QtCore, QtGui, QtWidgets
from zoo.libs.utils import unittestBase
from zoo.libs import iconlib

logger = logging.getLogger(__name__)


class TestStatus(object):
    """The possible status values of a test."""
    not_run = 0
    success = 1
    fail = 2
    error = 3
    skipped = 4


class TestCaptureStream(object):
    """Allows the output of the tests to be displayed in a QTextEdit."""
    success_color = QtGui.QColor(92, 184, 92)
    fail_color = QtGui.QColor(240, 173, 78)
    error_color = QtGui.QColor(217, 83, 79)
    skip_color = QtGui.QColor(88, 165, 204)
    normal_color = QtGui.QColor(200, 200, 200)

    def __init__(self, text_edit):
        self.text_edit = text_edit

    def write(self, text):
        """Write text into the QTextEdit."""
        # Color the output
        if text.startswith('ok'):
            self.text_edit.setTextColor(TestCaptureStream.success_color)
        elif text.startswith('FAIL'):
            self.text_edit.setTextColor(TestCaptureStream.fail_color)
        elif text.startswith('ERROR'):
            self.text_edit.setTextColor(TestCaptureStream.error_color)
        elif text.startswith('skipped'):
            self.text_edit.setTextColor(TestCaptureStream.skip_color)

        self.text_edit.insertPlainText(text)
        self.text_edit.setTextColor(TestCaptureStream.normal_color)
        vScrollBar = self.text_edit.verticalScrollBar()
        vScrollBar.triggerAction(QtWidgets.QScrollBar.SliderToMaximum)

    def flush(self):
        pass


class UnittestNode(datasources.BaseDataSource):
    successIcon = iconlib.icon('test_success')
    failIcon = iconlib.icon('test_fail')
    errorIcon = iconlib.icon('test_error')
    skipIcon = iconlib.icon('test_skip')

    def __init__(self, test, headerText=None, model=None, parent=None):
        super(UnittestNode, self).__init__(headerText, model, parent)
        self.test = test
        self._status = TestStatus.not_run
        self._tooltip = str(test)
        if 'ModuleImportFailure' == self.test.__class__.__name__:
            try:
                getattr(self.test, self.name())()
            except ImportError:
                self._tooltip = traceback.format_exc()
                logger.warning(self._tooltip + self.path())

    def label(self):
        if isinstance(self.test, unittest.TestCase):
            return self.test._testMethodName
        elif isinstance(self.child(0).test, unittest.TestCase):
            return self.child(0).test.__class__.__name__
        elif hasattr(self.test, "_metaData"):
            return self.test._metaData["package"].name
        return self.child(0).child(0).test.__class__.__module__

    def data(self, index):
        return self.label()

    def path(self):
        """Gets the import path of the test.  Used for finding the test by name."""
        if self.parent() and self.parent().parent():
            return '{0}.{1}'.format(self.parent().path(), self.label())
        return self.label()

    def toolTip(self, index):
        return str(self._tooltip)

    def setToolTip(self, index, value):
        self._tooltip = value
        return True

    def status(self):
        """Get the status of the TestNode.

        Nodes with children like the TestSuites, will get their status based on the status of the leaf nodes (the
        TestCases).
        @return: A status value from TestStatus.
        """
        if 'ModuleImportFailure' in [self.label(), self.test.__class__.__name__]:
            return TestStatus.error
        if not self.children:
            return self._status
        result = TestStatus.not_run
        for child in self.children:
            child_status = child.status()
            if child_status == TestStatus.error:
                # Error status has highest priority so propagate that up to the parent
                return child_status
            elif child_status == TestStatus.fail:
                result = child_status
            elif child_status == TestStatus.success and result != TestStatus.fail:
                result = child_status
            elif child_status == TestStatus.skipped and result != TestStatus.fail:
                result = child_status
        return result

    def icon(self, index):
        """Get the status icon to display with the Test."""
        status = self.status()
        return [None,
                UnittestNode.successIcon,
                UnittestNode.failIcon,
                UnittestNode.errorIcon,
                UnittestNode.skipIcon][status]

    def customRoles(self, index):
        return [constants.userRoleCount + 1]

    def setDataByCustomRole(self, index, value, customRole):
        if customRole == constants.userRoleCount + 1:
            self._status = value
            return True
        return False


class TestDataModel(treemodel.TreeModel):

    def __init__(self, root, parent=None):
        super(TestDataModel, self).__init__(root, parent)
        self.node_lookup = {}

    def refresh(self, testSuite):
        self.node_lookup = {}
        self.root = UnittestNode(testSuite, model=self)
        for i in testSuite:
            child = self._recursiveCreateTests(i, self.root)
            self.createNodeLookUp(child)
        self.reload()

    def createNodeLookUp(self, node):
        """Create a lookup so we can find the TestNode given a TestCase or TestSuite.  The lookup will be used to set
        test statuses and tool tips after a test run.

        :param node: The node to add to the map
        :type node: :class:`UnittestNode`
        """
        self.node_lookup[str(node.test)] = node
        for child in node.children:
            self.createNodeLookUp(child)

    def _recursiveCreateTests(self, test, parent=None):
        """

        :param test:
        :type test: :class:`unittest.TestSuite` or :class:`unittest.TestCase`
        :return:
        :rtype:
        """
        parent = parent or self.root
        child = UnittestNode(test, parent=parent)
        parent.addChild(child)
        if isinstance(test, unittest.TestSuite):
            for test_ in test:
                if isinstance(test_, unittest.TestCase) or test_.countTestCases():
                    self._recursiveCreateTests(test_, child)
        return child

    def runTests(self, stream, test_suite):
        """Runs the given TestSuite.

        :param stream: A stream object with write functionality to capture the test output.
        :param test_suite: The TestSuite to run.
        """
        # UI updates handles by the results instance which calls updateFromResult
        unittestBase.runTests(test_suite=test_suite,
                              stream=stream, buffer=True,
                              resultClass=partial(TestResult, model=weakref.ref(self)))

    def updateFromResult(self, test, reason, status):
        node = self.node_lookup.get(str(test))
        if node is None:
            return
        index = node.modelIndex()
        self.setData(index, status, constants.userRoleCount + 1)
        self.setData(index, reason, QtCore.Qt.ToolTipRole)


class TestResult(unittestBase.ZooTestResult):
    """Customize the test result so we can do things like do a file new between each test and suppress script
    editor output.
    """

    def __init__(self, stream, descriptions, verbosity, **kwargs):
        super(TestResult, self).__init__(stream, descriptions, verbosity)
        self.successes = []
        self.model = kwargs.get("model")

    def addSuccess(self, test):
        """Override the base addSuccess method so we can store a list of the successful tests.

        :param test: TestCase that successfully ran."""
        super(TestResult, self).addSuccess(test)
        model = self.model()
        if model:
            model.updateFromResult(test, "Test Passed", TestStatus.success)

    def addSkip(self, test, reason):
        super(TestResult, self).addSkip(test, reason)
        model = self.model()
        if model:
            model.updateFromResult(test, reason, TestStatus.skipped)

    def addFailure(self, test, err):
        super(TestResult, self).addFailure(test, err)
        model = self.model()
        if model:
            model.updateFromResult(test, traceback.format_exception(*err),
                                   TestStatus.fail)

    def addError(self, test, err):
        super(TestResult, self).addError(test, err)
        model = self.model()
        if model:
            # self.errors is populated by the base class so we just grab that
            model.updateFromResult(test, self.errors[-1][1], TestStatus.error)
