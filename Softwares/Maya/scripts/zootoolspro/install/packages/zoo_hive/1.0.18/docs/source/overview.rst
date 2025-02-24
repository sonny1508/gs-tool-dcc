
Overview
####################################################

The Hive API is a modular rigging framework that allows you to build high-quality rigs
and animation tools using a standardized API.

The Hive API is highly modular, allowing you to build custom rigs and tools by assembling components,
which are reusable building blocks that encapsulate rigging functionality.
The API also provides a range of utilities for creating and manipulating components,
as well as for managing and organizing rigs.

Built using the Maya API 2.0, the Hive API provides fast creation of components and queries.
However, because the Maya API 2.0 is not undoable, the Hive API includes ZooCommands,
which wraps around the Hive API and the Maya API to reproduce Maya mpxCommands.
This provides the undoable functionality that is essential for rigging and animation workflows.
For more information about zooCommands please refer to :ref:`ZooCommands <mayaCommands>`.
For a list of Hive commands and their docstring, please refer to :doc:`./apireference/hivecommands`.

Use Cases
============================================

Hive is Designed for two primary use cases.

    1. The Rigging Artist :doc:`hiveartistui`
    2. The Rigging/Anim/Pipeline TD  :doc:`development`


Supported Maya Versions
============================================
    * Maya 2020+
    * Maya 2022+
    * Maya 2023+