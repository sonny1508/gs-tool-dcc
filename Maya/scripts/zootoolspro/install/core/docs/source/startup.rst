Startup
##########################
This section outlines how Zootools Core starts up initializes. It explains configuration management
and workflows for this process, we'll also go through customizing the startup procedure.

Introduction
--------------------------
Zootools Environment is determined  by a cached configuration which specifies what to load this is done through
the use of config files and descriptors which points to which set of packages to load and their location.

When Zootools startups, it ensures these packages exist physically on disk alongside all other necessary pieces
for Zootools to operate. This Collection of files is Zootools PRO

The Configuration on disk contains the following items:

- Package version config - Default config file which specifies all package descriptors.
- Preference location config - Defines the locations for zootools preferences.
- An install version of Zootools Core which includes `zoo_cmd` command which provides CLI access.
- Package cache which lives inside the install/packages folder, containing all installed packages and
  their versions. This cache is created for the zootools release.

By default we provide a single configuration file which contains all publicly released packages and all will
be loaded for every session whether inside a DCC or on the command Line. However it's possible to have multiple
package configurations, one for each environment(department,DCC, OS), this will be explain below.

Each Zoo Packages has it's own independent API and preferences, making it easy to extend, evolve
and customize Zoo overtime.


Initialization
--------------------------

Docs Coming Soon!
