import os
import openai

from zoo.core.util import filesystem, zlogging

from zoovendor.Qt import QtCore
from zoo.libs.utils import output, execution
from zoo.libs.pyqt import thread
from zoo.preferences.interfaces import gptinterfaces
from zoo.apps.chatgptui import utils, constants

logger = zlogging.getLogger(__name__)


class Controller(QtCore.QObject):
    """Manages the chatGPT session include API Key, threading, response validation.
    """
    messageReceived = QtCore.Signal(str)
    messageErrored = QtCore.Signal(dict)
    gptModelListReceived = QtCore.Signal(list)

    def __init__(self, parent):
        super(Controller, self).__init__(parent)

        self.prefInterface = gptinterfaces.gptInterface()
        self._defaultConversation = self.prefInterface.currentPrefDefaultConversation()
        self._conversationPresets = self.prefInterface.conversationPresets()
        self.conversation = [{"role": self._defaultConversation["role"],
                              "content": self._defaultConversation["content"]}]
        self.gptModels = []
        self.lastResponse = {}
        self.stream = True
        self._streamContent = []
        self._currentThread = None
        self.chatSessions = []  # type: list[ChatSession]
        self.chatSession = None  # type: ChatSession or None
        self.threadPool = QtCore.QThreadPool.globalInstance()

        self._executionLocals = {"__name__": "__main__",
                                 "__doc__": None,
                                 "__package__": None}

        sessions = self.prefInterface.sessionPaths()
        for sessionPath in sessions:
            newSession = ChatSession.loadFromFile(sessionPath)
            if newSession is not None:
                self.chatSessions.append(newSession)
        self.chatSession = self.chatSessions[-1] if self.chatSession else ChatSession("New Chat Session",
                                                                                      self.prefInterface.defaultSessionPath(
                                                                                          0))
        self.gptMaxTokens = self.prefInterface.maxTokens("gpt-3.5-turbo")

    def onClose(self):
        logger.debug("Closing chatGPT Controller")
        # remove any threads that haven't started yet
        self.threadPool.clear()

        while not self.threadPool.waitForDone():
            continue

    def updateModels(self):
        if not utils.hasApiKey():
            return
        logger.debug("Updating GPT Models Via thread")
        thread_ = thread.ThreadedFunc(self._queryModelsThread)
        thread_.signals.result.connect(self._onQueryGptModels)
        thread_.signals.error.connect(self._onQueryGptModelsError)
        self.threadPool.start(thread_)

    def _queryModelsThread(self, **kwargs):
        return openai.models.list()

    def _onQueryGptModelsError(self, trace):
        output.displayError("Error occurred while querying GPT Models, "
                                 "please try again later.\n{}".format(trace[-1]))

    def _onQueryGptModels(self, queryResult):
        logger.debug("GptModels list received, updating controller")
        models = [i.id for i in queryResult]
        if "gpt-4" in models:
            self.chatSession.gptModel = "gpt-4"
        self.gptModels = models
        self.gptModelListReceived.emit(models)

    def clearMessages(self):
        self.conversation = [{"role": self._defaultConversation["role"],
                              "content": self._defaultConversation["content"]}]
        self.chatSession.chatHistory = []

    def setGptModel(self, modelIndex):
        self.chatSession.gptModel = self.gptModels[modelIndex]
        self.gptMaxTokens = self.prefInterface.maxTokens(self.chatSession.gptModel)

    def send(self, message):
        if self._currentThread is not None and self._currentThread.running:
            return
        if not utils.hasApiKey():
            if not self.parent().displayApiKeyInputDialog():
                return
        self.chatSession.addMessage("user", message)
        logger.debug("Creating QThread for openai Query")
        self._currentThread = thread.ThreadedFunc(self._onSendThread, message=message)
        self._currentThread.signals.result.connect(self._onGptResponse)
        self._currentThread.signals.error.connect(self._onGptError)
        self.conversation.append({"role": "user", "content": message})

        self.threadPool.start(self._currentThread)

    def _onSendThread(self, message, **kwargs):
        logger.debug("Querying OpenAI with user Message: {}".format(message))
        try:
            response = openai.chat.completions.create(
                model=self.chatSession.model,
                messages=self.conversation,
                temperature=0,
                max_tokens=self.gptMaxTokens,
                top_p=1,
                stream=self.stream
            )

            if self.stream:
                for chunk in response:
                    self._onStream(chunk)

                return
        except TimeoutError:
            logger.debug("Openai Timeout Error")
            self.messageErrored.emit({"type": "timeout",
                                      "message": "Open AI timed out, please wait a amount and try again."})
            return
        return {"response": response,
                "userMessage": message}

    def _onGptResponse(self, response):
        if self.stream:
            self.chatSession.addMessage("chatgpt", "".join(self._streamContent))
            self._streamContent = []
            return
        gptResponse = response["response"]  # type: openai.types.Completion
        choice = gptResponse.choices[0]
        if choice.finish_reason == "length":
            logger.debug("Openai MaxTokens reached")
            self.messageErrored.emit({"type": "maxTokens",
                                      "message": "Max Tokens for this session has been hit, "
                                                 "Please clear session and start a new session."})
            return
        responseText = choice.message.content

        self.conversation.append(
            {"role": "assistant", "content": responseText})
        self.lastResponse = response
        self.messageReceived.emit(responseText)

    def _onStream(self, chunk):
        """

        :param chunk:
        :type chunk: :class:`openai.types.Completion`
        :return:
        :rtype:
        """

        responseText = chunk.choices[0].delta.content
        if responseText:
            self._streamContent.append(responseText)
            self.messageReceived.emit(responseText)

    def _onGptError(self, stack, **kwargs):
        excType, value, trace = stack
        # Getting the error type from a generic exception which runs within a thread
        # tends to not like type checking so we can have a decent user message so
        # we convert to the class name explicitly
        errorType = str(excType.__name__)
        if isinstance(value, openai.RateLimitError):
            errorType = "RateLimitError"
            message = constants.RATE_LIMIT_MESSAGE
        else:
            message = "Unhandled occurred:\n{}".format(trace)
        logger.debug("Error Occurred during openai request", exc_info=value)
        self.messageErrored.emit({"type": errorType, "message": message, "trace": trace})

    def executeCode(self, text):
        executionResult = execution.execute(text, self._executionLocals, self._executionLocals)

        if executionResult["reason"] == "errored":
            output.displayError(executionResult["traceback"])


class ChatSession(object):
    """
    A class representing a chat session object.

    :param title: The title of the chat session.
    :type title str
    :param saveLocation: The file path to save the chat session history as a JSON file.
    :type saveLocation: str
    """

    @classmethod
    def loadFromFile(cls, filePath):
        if not os.path.exists(filePath):
            return
        data = filesystem.loadJson(filePath)
        session = cls(data["title"], filePath)
        session.chatHistory = data["messages"]
        session.model = data["model"]
        return session

    def __init__(self, title, saveLocation):
        self.title = title
        self.saveLocation = saveLocation
        # The chat history list.
        self.chatHistory = []  # type: list[tuple[str, str]]
        self.model = "gpt-3.5-turbo"
        self._changedName = False

    def rename(self, newTitle):
        self.title = newTitle
        self._changedName = True

    def delete(self):
        if os.path.exists(self.saveLocation):
            os.remove(self.saveLocation)

    def addMessage(self, sender, message):
        """Adds a new message to the chat history list.

        :param sender: The sender of the message.
        :type sender: str
        :param message: The message text.
        :type message: str
        """
        logger.debug("Adding message to chat history: {} - {}".format(sender, message))
        self.chatHistory.append((sender, message))

    def saveChatHistory(self):
        """Saves the chat history as a JSON file at the specified save location.
        """
        data = {
            "title": self.title,
            "messages": self.chatHistory,
            "model": self.model
        }
        if self._changedName:
            self._changedName = False
            if os.path.exists(self.saveLocation):
                os.remove(self.saveLocation)
            self.saveLocation = os.path.join(os.path.dirname(self.saveLocation), self.title + ".chatgpt")
        filesystem.saveJson(data, self.saveLocation)

    def loadChatHistory(self):
        """Loads the chat history from the JSON file at the specified save location.
        """
        self.chatHistory = []
        data = filesystem.loadJson(self.saveLocation)
        self.title = data["name"]
        self.chatHistory = data["messages"]

    def clearChatHistory(self):
        """Clears the chat history list.
        """
        logger.debug("Clearing chat history.")
        self.chatHistory = []
