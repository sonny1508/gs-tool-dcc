.. _mayaCommands:

Zoo Maya Command
########################################

.. note::
    We're building a new version of undo commands for the api to more closely work with zapi(our api wrapper).
    This move has been made to simplify managing undo across tools and to make it easier to use.
    This will avoid having to write a custom zoo command for every tool and make undo far more stable

Python command pattern with undo,redo functionality for standard applications and or DCCs if supported via command executors

Commands follow some strict rules.

- All commands must inherent from zoo.libs.command.command.ZooCommand.
- All commands must have the following overrides.

    - id(property) the command id
    - isUndoable(property) Does the command support undo
    - doIt(method), Main method to do the operation
    - undoIt(method), if is undoable then undoIt() must be implemented

If a command is undoable then it will be part of maya internal undostack.
Maya commands are a thin wrapper around the MPxCommand so we maintain the undo/redo feature's but we extended the possibilities
with maya by allowing for arbitrary data types to be passed to and from commands eg. om2.MObject. we only support using
om2, cmds and pure python, no om1 code as per maya documentation.
A few design decision have been made to simplify command creation.

- Only the doIt and undoIt methods need to be implemented.
- Zoo handles the registry of supported commands and only one plugin is registered to maya which is the undo.py in zoo.
- User's only need to tell zoo executor instance about the command location(Environment variable), no need for the initializePlugin().
- Minimal differences between MPxCommand and Zoocommand
- maya's undo/redo stacks and zooCommands stacks are synced via the custom MPx.
- ZooCommands support passing api objects and any datatype to and from a command(see below).
- ZooCommands are not meant to do atomic operations and query ops. Only for maya state changes and only for large operations.
- ZooCommands are not meant to replace c++ commands or for efficient code but for tool development, it's not meant to be run in loops or something stupid like that.
  eg. you press a pushbutton then you execute a command that builds a rig which can be undone.



Usage
=====

Users can add there own paths via the environment variable 'ZOO_COMMAND_LIB' then running the following

.. code-block:: python

    from zoo.libs.maya.mayacommand import mayaexecutor as executor
    executor.Executor().registerEnv("ZOO_COMMAND_LIB")

To execute commands one must use the executor class and never execute the command directly otherwise
it will not be added to the internal undo stack and or the redostack.

.. code-block:: python

    # to execute a command
    from zoo.libs.maya.mayacommand import mayaexecutor as executor
    exe = executor.Executor()
    exe.executor("commandId", **kwargs)


To undo a command.

.. code-block:: python

    from zoo.libs.maya.mayacommand import mayaexecutor as executor
    executor.Executor().registerEnv("ZOO_COMMAND_LIB")
    executor.undoLast()

To redo a command from the undostack.

.. code-block:: python

    from zoo.libs.maya.mayacommand import mayaexecutor as executor
    executor.Executor().registerEnv("ZOO_COMMAND_LIB")
    executor.redoLast()

Example
-----------------------

.. code-block:: python

    
    from zoo.libs.maya.mayacommand import mayaexecutor as executor
    exe = executorExecutor()
    nodes = exe.execute("zoo.create.nodetype", name="transform", amount=10, Type="transform")
    print(nodes)
    # (<OpenMaya.MObjectHandle object at 0x0000024911572E70>, <OpenMaya.MObjectHandle object at 0x0000024911572E30>,
    <OpenMaya.MObjectHandle object at 0x0000024911572CB0>, <OpenMaya.MObjectHandle object at 0x0000024911572E90>,
    <OpenMaya.MObjectHandle object at 0x0000024911572EB0>, <OpenMaya.MObjectHandle object at 0x0000024911572ED0>,
    <OpenMaya.MObjectHandle object at 0x0000024911572EF0>, <OpenMaya.MObjectHandle object at 0x0000024911572F10>,
    <OpenMaya.MObjectHandle object at 0x0000024911572F30>, <OpenMaya.MObjectHandle object at 0x0000024911572F50>)


    # see below for the command class

    from zoo.libs.maya.mayacommand import command


    class CreateNodeTypeAmount(command.ZooCommandMaya):
        id = "zoo.create.nodetype" # id which is used for execution, and any filtering, lookups, GUIs etc
        creator = "David Sparrow"
        isUndoable = True
        _modifier = None

        def resolveArguments(self, arguments):
            """Method to Pre check arguments this is run outside of mayas internals and the result cached on to the command instance.
            Since the result is store for the life time of the command you need to convert MObjects to MObjectHandles.
            :param arguments: dict representing the arguments
            :type arguments: dict
            """
            name=  arguments.get("name")
            if not name:
                self.cancel("Please provide a name!")
            amount = arguments.get("amount")
            if amount < 1:
                self.cancel("The amount can't be below one")
            if not arguments.get("Type"):
                arguments["Type"] = "transform"
            return arguments

        def doIt(self, name=None, amount=1, Type=None):
            """Its expected that the arguments are setup correctly with the correct datatype,
            """
            mod = om2.MDagModifier()
            nodes = [None] * amount
            for i in xrange(amount):
                obj = mod.createNode(Type)
                mod.renameNode(obj, "name{}".format(i))
                nodes[i] = obj
            mod.doIt()
            nodes = map(om2.MObjectHandle, nodes)
            self._modifier = mod
            return tuple(nodes)

        def undoIt(self):
            if self._modifier is not None:
                self._modifier.undoIt()



API
---

.. automodule:: zoo.libs.maya.mayacommand.command
    :members:
    :undoc-members:
    :show-inheritance:

Executor
--------------------------------

.. automodule:: zoo.libs.maya.mayacommand.mayaexecutor
    :members:
    :undoc-members:
    :show-inheritance:


Errors
------------------------------

.. automodule:: zoo.libs.maya.mayacommand.errors
    :members:
    :undoc-members:
    :show-inheritance:



Zoo Command Library
=================================

Alignselectedcommand
-------------------------------------------------------------

.. automodule:: zoo.libs.maya.mayacommand.library.alignselectedcommand
    :members:
    :undoc-members:
    :show-inheritance:



Connectsrt
----------------------------------------------------------

.. automodule:: zoo.libs.maya.mayacommand.library.connectsrt
    :members:
    :undoc-members:
    :show-inheritance:


Createmetacommand
----------------------------------------------------------

.. automodule:: zoo.libs.maya.mayacommand.library.createmetacommand
    :members:
    :undoc-members:
    :show-inheritance:

Nodeeditorcommands
-----------------------------------------------------------

.. automodule:: zoo.libs.maya.mayacommand.library.nodeeditorcommands
    :members:
    :undoc-members:
    :show-inheritance:

Setselectednodes
---------------------------------------------------------

.. automodule:: zoo.libs.maya.mayacommand.library.setselectednodes
    :members:
    :undoc-members:
    :show-inheritance:

Swapconnections
--------------------------------------------------------

.. automodule:: zoo.libs.maya.mayacommand.library.swapconnections
    :members:
    :undoc-members:
    :show-inheritance:

