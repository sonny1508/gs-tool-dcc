import inspect
import sys
import time
import traceback

from zoovendor import six
from zoo.core.util import env, classtypes, zlogging
from zoo.core.plugin import pluginmanager
from zoo.libs.utils import output
from maya import cmds
from maya.api import OpenMaya as om2
from zoo.libs.maya.mayacommand import errors
from zoo.libs.maya.mayacommand import command
from zoo.libs.maya.utils import general

logger = zlogging.getLogger(__name__)


@six.add_metaclass(classtypes.Singleton)
class MayaExecutor(object):
    """Maya Executor class for safely injecting zoo commands into the maya undo stack via MPXCommands.
    Always call executor.execute() method when executing commands
    """

    def __init__(self, interface=None, registerEnv="ZOO_COMMAND_LIB"):
        interface = interface or [command.ZooCommandMaya]
        self.registry = pluginmanager.PluginManager(interface, variableName="id", name="commandQueue")
        self.registry.registerByEnv(registerEnv)

    @property
    def commands(self):
        return self.registry.plugins

    def findCommand(self, id):
        return self.registry.getPlugin(id)

    def cancel(self, msg):
        raise errors.UserCancel(msg)

    def execute(self, commandName, **kwargs):
        """Function to execute Zoo commands which lightly wrap maya MPXCommands.
        Deals with prepping the Zoo plugin with the command instance. Safely opens and closes the undo chunks via
        maya commands (cmds.undoInfo)

        :param commandName: The command.id value
        :type commandName: str
        :param kwargs: A dict of command instance arguments, should much the signature of the command.doit() method
        :type kwargs: dict
        :return: The command instance returns arguments, up to the command developer
        """
        logger.debug("Executing command: {}".format(commandName))
        cmdObj = self.findCommand(commandName)
        if cmdObj is None:
            raise ValueError("No command by the name: {} exists within the registry!".format(commandName))

        cmd = cmdObj()
        if not cmd.isEnabled:
            return
        try:
            cmd.parseArguments(kwargs)
            if cmd.requiresWarning():
                output.displayWarning(cmd.warningMessage())
                return
        except errors.UserCancel:
            raise
        except Exception:
            raise
        exc_tb, exc_type, exc_value = None, None, None
        cmd.stats = CommandStats(cmd)
        try:
            if cmd.isUndoable and cmd.useUndoChunk:
                cmds.undoInfo(openChunk=True, chunkName=cmd.id)
            om2._REQUIRED_COMMAND_SYNC = cmd
            cmds.zooAPIUndo(commandId=cmd.id)
            if cmd.returnStatus == command.RETURN_STATE_ERROR:
                exc_type, exc_value, exc_tb = sys.exc_info()
                message = "Command failed to execute: {}".format(cmd.id)
                raise errors.CommandExecutionError(message)
            return cmd._returnResult

        finally:
            tb = None
            if exc_type and exc_value and exc_tb:
                tb = traceback.format_exception(exc_type, exc_value, exc_tb)
            if cmd.isUndoable and cmd.useUndoChunk:
                cmds.undoInfo(closeChunk=True, chunkName=cmd.id)
            cmd.stats.finish(tb)
            logger.debug("Finished executing command: {}".format(commandName))

    def flush(self):
        cmds.flushUndo()


class CommandStats(object):
    def __init__(self, tool):
        self.command = tool
        self.startTime = 0.0
        self.endTime = 0.0
        self.executionTime = 0.0

        self.info = {}
        self._init()

    def _init(self):
        """Initializes some basic info about the plugin and the use environment
        Internal use only:
        """
        try:
            path = inspect.getfile(self.command.__class__)
        except:
            path = ""

        self.info.update({"id": self.command.id,
                          "module": self.command.__class__.__module__,
                          "filepath": path,
                          "application": env.application()
                          })
        self.info.update(env.machineInfo())

    def finish(self, tb=None):
        """Called when the plugin has finish executing
        """
        self.endTime = time.time()
        self.executionTime = self.endTime - self.startTime
        self.info["executionTime"] = self.executionTime
        self.info["lastUsed"] = self.endTime
        if tb:
            self.info["traceback"] = tb


def execute(executeId, **kwargs):
    """ Helper to execute zoo commands by id

    :param executeId: ID To execute
    :type executeId: basestring
    :return: Returns the executor and anything from exe execute
    """
    exe = MayaExecutor()
    return exe.execute(executeId, **kwargs)
