Hive Commands
-------------

Hive Commands are subclasses of :class:`zoo.libs.command.command.ZooCommandMaya` but are solely built around hive
operation's.
Hive api is intentionally not undoable but we do have our way's of making an operation undoable
and that's what Hive Commands are for.

The general workflow is to use the api directly for queries but for state changes use hive commands
if a hive command doesn't exist then create one see :class:`zoo.libs.command.command.ZooCommandMaya` for more information.




.. automodule:: zoo.libs.commands.hive
    :members:
    :undoc-members:
    :show-inheritance:

