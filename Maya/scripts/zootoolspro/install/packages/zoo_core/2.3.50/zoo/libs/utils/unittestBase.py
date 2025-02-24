import os
import sys
import tempfile
import timeit
import shutil
import unittest
from unittest.runner import TextTestRunner, TextTestResult
from unittest.loader import TestLoader
from unittest.suite import TestSuite
from zoovendor import six

from zoo.core.util import zlogging

logger = zlogging.getLogger(__name__)


def decorating_meta(decorator):
    class DecoratingMetaclass(type):
        def __new__(cls, class_name, bases, namespace):
            for key, value in list(namespace.items()):
                if callable(value):
                    namespace[key] = decorator(value)
            return type.__new__(cls, class_name, bases, namespace)

    return DecoratingMetaclass


def skipUnlessHasattr(obj):
    if not hasattr(obj, 'skip'):
        def decorated(*a, **kw):
            return obj(*a, **kw)

        return decorated

    def decorated(*a, **kw):
        return unittest.skip("{!r} doesn't have {!r}".format(obj, 'skip'))

    return decorated


@six.add_metaclass(decorating_meta(skipUnlessHasattr))
class BaseUnitest(unittest.TestCase):
    """This Class acts as the base for all unitests, supplies a helper method for creating tempfile which
    will be cleaned up once the class has been shutdown.
    If you override the tearDownClass method you must call super or at least clean up the _createFiles set
    """
    _createdFiles = set()
    application = "standalone"

    @classmethod
    def createTemp(cls, *args, **kwargs):

        temp = tempfile.mkstemp(*args, **kwargs)
        cls._createdFiles.add(temp)
        return temp

    mkstemp = createTemp

    @classmethod
    def mkdtemp(cls, *args, **kwargs):
        temp = tempfile.mkdtemp(*args, **kwargs)
        cls._createdFiles.add(temp)
        return temp

    @classmethod
    def addTempFile(cls, filepath):
        cls._createdFiles.add(filepath)

    @classmethod
    def tearDownClass(cls):
        super(BaseUnitest, cls).tearDownClass()
        for i in cls._createdFiles:
            if os.path.isfile(i):
                os.remove(i)
            elif os.path.isdir(i):
                shutil.rmtree(i)
        cls._createdFiles.clear()


class ZooTestResult(TextTestResult):
    def __init__(self, *args, **kwargs):
        super(ZooTestResult, self).__init__(*args, **kwargs)
        self.testTimings = []
        self._startedAt = 0.0

    def startTest(self, test):
        self._startedAt = timeit.default_timer()
        super(ZooTestResult, self).startTest(test)

    def addSuccess(self, test):
        super(ZooTestResult, self).addSuccess(test)
        elapsed = timeit.default_timer() - self._startedAt
        name = self.getDescription(test)
        self.testTimings.append((name, elapsed))


class ZooTestRunner(TextTestRunner):

    def __init__(self, slowTestThreshold=0.3, *args, **kwargs):
        self.slowTestThreshold = slowTestThreshold
        super(ZooTestRunner, self).__init__(
            *args,
            **kwargs
        )

    def run(self, test):
        result = super(ZooTestRunner, self).run(test)
        slowTimings = []
        for name, elapsed in result.testTimings:
            if elapsed > self.slowTestThreshold:
                slowTimings.append("({:.03}s) {}".format(elapsed, name))
        if slowTimings:
            self.stream.writeln(
                "\nSlow Tests (>{:.03}s):".format(
                    self.slowTestThreshold))
            for timing in slowTimings:
                self.stream.writeln(timing)
        return result


def runTests(directories=None,
             test=None,
             test_suite=None,
             buffer=False,
             failfast=False,
             stream=None,
             resultClass=None):
    """Run all the tests in the given paths.

    :param directories: A generator or list of paths containing tests to run.
    :param test: Optional name of a specific test to run.
    :param test_suite: Optional TestSuite to run.  If omitted, a TestSuite will be generated.
    """
    if test_suite is None:
        test_suite = getTests(directories, test)

    runner = ZooTestRunner(stream=stream,
                           verbosity=2,
                           resultclass=resultClass if resultClass is not None else ZooTestResult)
    runner.failfast = failfast
    runner.buffer = buffer
    results = runner.run(test_suite)
    return results


def getTests(directories, test=None, testSuite=None, topLevelDir=None):
    """Get a unittest.TestSuite containing all the desired tests.

    :param directories: Optional list of directories with which to search for tests.
    :param test: Optional test path to find a specific test such as 'test_mytest.SomeTestCase.test_function'.
    :param testSuite: Optional unittest.TestSuite to add the discovered tests to.  \
    If omitted a new TestSuite will be created.
    :return: The populated TestSuite.
    :rtype: :class:`unittest.suite.TestSuite`
    """
    # Populate a TestSuite with all the tests
    if testSuite is None:
        testSuite = TestSuite()

    if test:
        # Find the specified test to run
        directories_added_to_path = [os.path.dirname(p) for p in directories]
        discovered_suite = TestLoader().loadTestsFromName(test)
        if discovered_suite.countTestCases():
            testSuite.addTests(discovered_suite)
    else:
        # Find all tests to run
        directories_added_to_path = []
        for p in directories:
            discovered_suite = TestLoader().discover(p, top_level_dir=topLevelDir)
            if discovered_suite.countTestCases():
                testSuite.addTests(discovered_suite)
    # Remove the added paths.
    for path in directories_added_to_path:
        if path in sys.path:
            sys.path.remove(path)

    return testSuite
