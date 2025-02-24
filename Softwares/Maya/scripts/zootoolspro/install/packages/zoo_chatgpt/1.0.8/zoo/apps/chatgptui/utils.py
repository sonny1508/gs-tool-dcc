import os, openai
from zoo.apps.chatgptui import constants
from zoo.core.util import zlogging

logger = zlogging.getLogger(__name__)

def hasApiKey():
    currentGlobalKey = os.getenv(constants.OPENAI_ENV)
    return currentGlobalKey is not None and openai.api_key is not None

def validateKey(key):
    try:
        openai.api_key = key
        openai.models.list()
    except openai.AuthenticationError:
        logger.error("Invalid API Key", exc_info=True)
        openai.api_key = None
        return False
    return True


def setAPIkey(key):
    openai.api_key = key
    os.environ[constants.OPENAI_ENV] = key

def setApiKeyIfFound():
    """Sets the openai api key if it's found in the environment variables as `ZOO_OPENAI_KEY`

    :rtype: bool
    """
    currentGlobalKey = os.getenv(constants.OPENAI_ENV)
    if currentGlobalKey is not None:
        openai.api_key = currentGlobalKey
        return True
    return False
