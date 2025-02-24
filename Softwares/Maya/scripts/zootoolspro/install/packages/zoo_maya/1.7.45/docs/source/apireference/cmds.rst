Maya Commands
########################################

The following Zoo modules provide extra Maya functions that are built ontop of Maya's command (cmds) module.

.. code-block:: python

    from maya import cmds

Most of the functionality for our toolset tools can be found here.

Our Maya Commands can be accessed with:

.. code-block:: python

    from zoo.libs.maya.cmds

For example:

.. code-block:: python

    # Returns the scene's frame rate per second.
    from zoo.libs.maya.cmds.animation.animconstants.getSceneFPS()

.. toctree::
    :maxdepth: 2

    ./cmds/animation
    ./cmds/assets
    ./cmds/blendshapes
    ./cmds/cameras
    ./cmds/display
    ./cmds/filemanage
    ./cmds/general
    ./cmds/hotkeys
    ./cmds/lighting
    ./cmds/markingmenus
    ./cmds/math
    ./cmds/meta
    ./cmds/modeling
    ./cmds/ncloth
    ./cmds/objutils
    ./cmds/preferences
    ./cmds/renderer
    ./cmds/rig
    ./cmds/shaders
    ./cmds/textures
    ./cmds/skin
    ./cmds/uvs
    ./cmds/workspace
    ./cmds/broadunittests