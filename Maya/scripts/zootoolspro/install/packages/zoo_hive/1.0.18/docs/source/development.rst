Development
####################################################



.. toctree::
   :maxdepth: 3

   ./terminology
   ./buildscripting
   ./exporting
   ./namingconventions
   ./components
   ./api
   ./namedgraphs
   ./examples



Accessing the Hive Api
----------------------------------------
There is a single entry point to the api which contains all functions and classes
which we support publicly.

.. code-block:: python

    from zoo.libs.hive import api

.. _hiveEnvironmentVariables:


Environment Variables
----------------------------------------

.. list-table::
   :widths: 25 50
   :header-rows: 1

   * - Name
     - Description
   * - HIVE_COMPONENT_PATH
     - ; Separated paths to each folder containing Hive component files.
   * - HIVE_DEFINITIONS_PATH
     - ; Separated paths to each folder containing Hive Definition files.
   * - HIVE_TEMPLATE_PATH
     - ; Separated paths to each folder containing Hive .template files.
   * - HIVE_TEMPLATE_SAVE_PATH
     - Default Save path for templates only one path accepted.
   * - HIVE_BUILD_SCRIPTS_PATH
     - ; Separated paths to each folder containing Hive build script py files.
   * - HIVE_NAMING_PATH
     - Absolute path to naming configuration json file for hive to use.
   * - HIVE_EXPORT_PLUGIN_PATH
     - ; Separated paths to each folder containing Hive exporter py files.