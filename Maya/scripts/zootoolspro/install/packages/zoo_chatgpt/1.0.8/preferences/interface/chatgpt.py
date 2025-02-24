import os

from zoo.preferences import prefinterface

DEFAULT_SESSION_PATH_KEY = "defaultSessionPath"
DEFAULT_CONVO_KEY = "defaultConversationPreset"
CONVO_PRESETS_KEY = "conversationPresets"
DEFAULT_SESSION_FOLDER = "prefs/global/chatgpt/sessions"
DEFAULT_SESSION_NAME = "defaultSession"
SESSION_FILE_EXT = ".chatgpt"


class ChatGptInterface(prefinterface.PreferenceInterface):
    """Preference interface class for hive
    """
    id = "chatGpt"
    _relativePath = "prefs/global/chatgpt"

    def maxTokens(self, modelName, root=None):
        """Returns the maxTokens.

        :param modelName: the GPT model name.
        :type: modelName: str
        :param root: The root preferences name to use
        :type root: str
        :return maxTokens: The maxTokens
        :rtype maxTokens: int
        """
        tokens = self.settings(root=root, name="maxTokens")
        return tokens.get(modelName, self.settings(root=root, name="defaultMaxTokens"))

    def sessionPaths(self, root=None):
        """Returns the session paths

        :param root: The root preferences name to use
        :type root: str
        :return sessionPaths: The session paths
        :rtype sessionPaths: list
        """
        folderPath = self.settings(root=root, name=DEFAULT_SESSION_PATH_KEY)
        if not folderPath:
            folderPath = os.path.join(self.preference.root(root or "user_preferences"), DEFAULT_SESSION_FOLDER)
        sessionPaths = []
        for r, dirs, fileNames in os.walk(folderPath):
            sessionPaths.extend([os.path.join(r, fileName)
                                 for fileName in fileNames
                                 if fileName.endswith(SESSION_FILE_EXT)]
                                )

        return sessionPaths

    def defaultSessionPath(self, incrementNumber, root=None):
        """Returns the default session file path with its increment number.

        :param root: The root preferences name to use
        :type root: str
        :return sessionPath: The default session path
        :rtype sessionPath: str
        """
        folderPath = self.settings(root=root, name=DEFAULT_SESSION_PATH_KEY)
        if not folderPath:
            folderPath = os.path.join(self.preference.root(root or "user_preferences"), DEFAULT_SESSION_FOLDER)
        sessionPath = os.path.join(folderPath, DEFAULT_SESSION_NAME + str(incrementNumber) + SESSION_FILE_EXT)
        return sessionPath

    def conversationPresets(self, root=None):
        return self.settings(root=root, name=CONVO_PRESETS_KEY)

    def currentPrefDefaultConversation(self, root=None):
        conversationName = self.settings(root=root, name=DEFAULT_CONVO_KEY)
        conversations = self.settings(root=root, name=CONVO_PRESETS_KEY)
        for convo in conversations:
            if convo["name"] == conversationName:
                return convo
        return {}