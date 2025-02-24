Overview
###########################

Welcome to the Zootools Pro Developer and reference Documentation.
Below you will find detailed technical information about Zootools Core
API useful for developers and engineers.

What is Zootools Core
---------------------------
The Zootools Core consists of a set of systems for managing the zootools
environment

- A :ref:`Descriptor API<descriptors>` which handles external resource management,
  configuration.
- An extendable :ref:`CLI<CLI_commands>` for running commands to managing code packages and environments.
- :ref:`Environment resolver API<packageResolver>` for package discovery, management and introspection.

Accessing Zootools Core API
---------------------------
As with all APIs, the Zootools Core API is a combination of public interface and internal logic.
We refactor and evolve the code on a regular basis and this sometimes changes internal structure of the code.
We recommend only accessing Core via the methods documented in this API reference. These form the official
Zootools Core API and we do our best to ensure backwards compatibility.

As a general rule access to the API should be only done via the public interface 'api.py' module. This
is to provide a cleaner interface and making refactoring easier.

.. code-block:: python

    # Recommended API Access
    from zoo.core import api
    cfg = api.currentConfig()
