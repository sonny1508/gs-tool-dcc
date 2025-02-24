"""
.. todo::

    feed maya stdout to output widget
    tab icons
    code completion
"""
import logging
import os
import sys
import traceback

from zoovendor import six
from zoovendor.Qt import QtWidgets, QtCore
from zoo.core import engine
from zoo.libs.pyqt.extended.sourcecodeeditor import pythoneditor
from zoo.libs.pyqt.widgets import logoutput
from zoo.libs.pyqt.widgets import elements
from zoo.libs.utils import filesystem
from zoo.preferences.interfaces import coreinterfaces



class Session(object):
    """This class is responsible for loading a session from a file and managing session data.


    :param name: The name of the session.
    :type name: str
    :param filePath: The path to the session file.
    :type filePath: str
    :param text: The text of the session. Default is an empty string.
    :type text: str or None
    """
    @classmethod
    def loadFromFile(cls, filePath):
        with open(filePath, "r") as f:
            text = "".join(f.readlines())
        name = os.path.basename(filePath).rpartition(os.extsep)[0]
        return cls(name, filePath, text)

    def __init__(self, name, filePath, text=None):
        self.name = name
        self.filePath = filePath
        self.text = text or ""


class SessionManager(object):
    """Manages sessions for a given directory.
    """
    def __init__(self):
        self.sessions = []
        self.rootDirectory = ""

    def reloadSessions(self, directory):
        self.rootDirectory = directory
        self.sessions = []
        filesystem.ensureFolderExists(directory)
        for root, dirs, files in os.walk(directory):
            for f in files:
                if not f.endswith(".py"):
                    continue
                fullPath = os.path.join(root, f)
                self.sessions.append(Session.loadFromFile(fullPath))



    def createSession(self, name):
        self.sessions.append(Session(name, "", ""))

    def deleteSession(self, session):
        """Deletes the given session by removing its file from the filesystem and removing it from the list of sessions.

        :param session: The session to be deleted.
        :type session: :class:`Session`
        :return: True if the session was successfully deleted, False otherwise.
        :rtype: bool
        """
        if os.path.exists(session.filePath):
            os.remove(session.filePath)
        self.sessions.remove(session)
        return True

    def renameSession(self, session, newName):
        """Renames the given session include the file name on disk.

        :param session: The session to be renamed.
        :type session: Session
        :param newName: The new name for the session.
        :type newName: str
        """
        if os.path.exists(session.filePath):
            dirPath = os.path.dirname(session.filePath)
            newPath = os.extsep.join((os.path.join(dirPath, session.name), "py"))
            os.rename(session.filePath, newPath)
            session.filePath = newPath
        session.name = newName

    def saveSession(self, session, text):
        """This method saves the session to a file.

        :param session: The session object to save.
        :type session: :class:`Session`
        :param text: The text content of the session to save.
        :type text: str
        """
        filePath = session.filePath
        if not filePath:
            filePath = os.extsep.join((os.path.join(self.rootDirectory, session.name), "py"))
        session.text = text
        with open(filePath, "w") as f:
            f.write(text)




class SourceCodeUI(elements.ZooWindow):
    helpUrl = "https://www.create3dcharacters.com/zoo2"
    windowSettingsPath = "zoo/sourcecodeui"

    def __init__(
        self,
        parent=None,
        resizable=True,
        width=960,
        height=540,
        modal=False,
        alwaysShowAllTitle=False,
        minButton=False,
        maxButton=False,
        onTop=False,
        saveWindowPref=False,
        titleBar=None,
        overlay=True,
        minimizeEnabled=True,
        initPos=None
    ):
        super(SourceCodeUI, self).__init__(
            "SourceCodeEditor",
            "Source Code Editor",
            parent,
            resizable,
            width,
            height,
            modal,
            alwaysShowAllTitle,
            minButton,
            maxButton,
            onTop,
            saveWindowPref,
            titleBar,
            overlay,
            minimizeEnabled,
            initPos
        )

        hostName = engine.currentEngine().engineName
        rootDirectory = os.path.join(coreinterfaces.coreInterface().assetPath(), "scriptEditor", hostName)
        self.sessionManager = SessionManager()
        self.sessionManager.reloadSessions(rootDirectory)
        layout = elements.vBoxLayout()
        self.setMainLayout(layout)
        self._splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        self._outputWidget = logoutput.OutputLogDialog(title="Output", parent=self)

        self._stdoutRedirect = StdoutFeed(parent=self)
        self._stdinRedirect = StdinFeed(self._requestUserInput, parent=self)
        self._stderrRedirect = StderrorFeed(parent=self)

        self._inputWidget = pythoneditor.TabbedEditor(
            name="scriptEditorInput", parent=self
        )

        self._inputWidget.newTabAdded.connect(self.onEditorTabCreated)
        self._inputWidget.removeTabRequested.connect(self.onEditorTabDeleted)
        self._inputWidget.renameTabRequested.connect(self.onEditorTabRenamed)
        if not self.sessionManager.sessions:
            self._inputWidget.addNewEditor(name="python", language="python")
        else:
            sessions = list(self.sessionManager.sessions)
            self.sessionManager.sessions = []
            for session in sessions:

                editor = self._inputWidget.addNewEditor(name=session.name, language="python")
                newSession = sessions[len(self.sessionManager.sessions)-1]
                newSession.filePath = session.filePath
                newSession.text = session.text
                editor.setText(session.text)


        self._splitter.addWidget(self._outputWidget)
        self._splitter.addWidget(self._inputWidget)
        layout.addWidget(self._splitter)

        self._stdoutRedirect.output.connect(self.writeStdOutToOutput)
        self._stderrRedirect.error.connect(self.writeStdErrToOutput)
        self._inputWidget.executed.connect(self.execute)
        self._locals = {
            "scriptEditor": self,
            "__name__": "__main__",
            "__doc__": None,
            "__package__": None,
        }

    def close(self):
        self.saveSessions()
        super(SourceCodeUI, self).close()

    @property
    def outputWidget(self):
        return self._outputWidget

    @property
    def inputWidget(self):
        return self._inputWidget

    def _requestUserInput(self):
        print("input")

    def createNewSession(self, widget, event):
        self._inputWidget.addNewEditor(name="TEMP", language="python")

    def onEditorTabCreated(self, widget, name):
        """

        :param widget:
        :type widget: :class:`zoo.libs.pyqt.extended.sourcecodeeditor.pythoneditor.Editor`
        :param name:
        :type name:
        :return:
        :rtype:
        """
        widget.textEdit.addHotKey(
            "Ctrl+Shift+S", func=self.onSaveAll, name="SaveAll"
        )
        widget.textEdit.addHotKey("Ctrl+N", func=self.createNewSession,
                                  name="NewFile")
        widget.textEdit.addHotKey("Ctrl+S", func=self.onSave, name="Save")
        widget.setLanguage("python", widget.defaultTheme)
        self.sessionManager.createSession(name)

    def onEditorTabDeleted(self, index):
        self.sessionManager.deleteSession(self.sessionManager.sessions[index])

    def onEditorTabRenamed(self, index, name):
        self.sessionManager.renameSession(
                self.sessionManager.sessions[index], name
            )

    def onSave(self, textEdit, event):
        text = textEdit.toPlainText()
        self.sessionManager.saveSession(
            self.sessionManager.sessions[self._inputWidget.currentIndex()],
            text
        )

    def onSaveAll(self, textEdit, event):
        self.saveSessions()

    def saveSessions(self):
        for index in range(self._inputWidget.count()):
            editor = self._inputWidget.widget(index)
            text = editor.text()
            self.sessionManager.saveSession(self.sessionManager.sessions[index], text)

    def writeStdOutToOutput(self, msg):
        self.outputWidget.factoryLog(msg, logging.INFO)

    def writeStdErrToOutput(self, msg):
        self.outputWidget.factoryLog(msg, logging.ERROR)

    def execute(self, script):
        self.saveSessions()
        script = script.replace("\u2029", "\n")
        script = six.ensure_str(script).strip()
        if not script:
            return

        with self._stdoutRedirect as stdOutFeed:
            with self._stdinRedirect:
                stdOutFeed.write(script)  # echo the script
                evalCode = True
                try:
                    outputCode = compile(script, "<string>", "eval")
                except SyntaxError:
                    evalCode = False
                    try:
                        outputCode = compile(script, "string", "exec")
                    except SyntaxError:
                        trace = traceback.format_exc()
                        self._stderrRedirect.write(trace)
                        return

                # ok we've compiled the code now exec
                if evalCode:
                    try:
                        results = eval(outputCode, self._locals, self._locals)
                        if results is not None:
                            stdOutFeed.write(str(results))
                    except Exception:
                        trace = traceback.format_exc()
                        self._stderrRedirect.write(trace)
                else:
                    try:
                        exec(outputCode, self._locals, self._locals)
                    except Exception:
                        trace = traceback.format_exc()
                        self._stderrRedirect.write(trace)


class StdoutFeed(QtCore.QObject):
    output = QtCore.Signal(str)

    def __init__(self, writeToStdout=True, parent=None):
        super(StdoutFeed, self).__init__(parent=parent)

        # temporarily assigned during enter
        self.stdHandle = None
        self.writeToStdout = writeToStdout

    def __enter__(self):
        self.stdHandle = sys.stdout
        sys.stdout = self
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self.stdHandle

    def write(self, msg):
        msg = six.ensure_str(msg)
        self.output.emit(msg)
        QtCore.QCoreApplication.processEvents()
        if self.writeToStdout and self.stdHandle:
            self.stdHandle.write(msg)


class StdinFeed(QtCore.QObject):
    inputRequested = QtCore.Signal(str)

    def __init__(self, readLineCallback, parent=None):
        super(StdinFeed, self).__init__(parent=parent)

        self.stdHandle = None
        self.readLineCallback = readLineCallback

    def __enter__(self):
        self.stdHandle = sys.stdin
        sys.stdin = self
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdin = self.stdHandle

    def readline(self):
        self.readLineCallback()


class StderrorFeed(QtCore.QObject):
    error = QtCore.Signal(str)

    def __init__(self, parent=None):
        super(StderrorFeed, self).__init__(parent=parent)

        # temporarily assigned during enter
        self.stdHandle = None

    def write(self, msg):
        self.error.emit(msg)
        QtCore.QCoreApplication.processEvents()
        sys.stderr.write(msg)
