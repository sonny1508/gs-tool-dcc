import pprint
import subprocess
import sys
from zoo.core.util import zlogging
from zoovendor import six
logger = zlogging.getLogger(__name__)


class SubprocessError(Exception):
    def __init__(self, cmd, returnCode):
        msg = "Command '{}' returned non-zero exit status {:d}".format(cmd, returnCode)
        super(SubprocessError, self).__init__(msg)

def subprocessCheckOutput(*args, **kwargs):
    """called subprocess.Popen with communicate()

    :param args: subprocess.Popen arguments
    :type args: tuple
    :param kwargs: subprocess.Popen keyword arguments
    :type kwargs: dict
    :return: str output from subprocess.Popen.communicate
    :rtype: str
    """
    # handle default std
    if "stdout" not in kwargs:
        kwargs["stdout"] = subprocess.PIPE
    if "stderr" not in kwargs:
        kwargs["stderr"] = subprocess.STDOUT
    if "stdin" not in kwargs:
        kwargs["stdin"] = subprocess.PIPE

    process = subprocess.Popen(
        *args,
        **kwargs

    )
    if sys.platform == "win32":
        process.stdin.close()
    output, _ = process.communicate()
    output = six.ensure_str(output)
    failCode = process.poll()
    if failCode:
        logger.debug("Subprocess invocation failed:")
        if args:
            logger.debug("Args: {}".format( pprint.pformat(args)))
        if kwargs:
            logger.debug("Kwargs: {}".format(pprint.pformat(kwargs)))
        logger.debug("Return code: {:d}".format(failCode))
        logger.debug("Process stdout/stderr:")
        logger.debug(output)

        cmd = kwargs.get("args")
        if cmd is None:
            cmd = args[0]

        raise SubprocessError(cmd, failCode)
    return output


def checkOutput(*args, **kwargs):
    """Helper function that handles sub processing safely on win32
    which requires extra flags

    :param args: The arguments to pass to subprocess
    :type args: list
    :param kwargs: The keyword arguments to pass to subprocess
    :type kwargs: dict
    :return: The subprocess output string
    :rtype: str
    """
    if sys.platform == "win32":
        info = subprocess.STARTUPINFO()
        info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        info.wShowWindow = subprocess.SW_HIDE
        kwargs["startupinfo"] = info
    return subprocessCheckOutput(*args, **kwargs)
