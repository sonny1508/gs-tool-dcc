.. _pycharm_setup:

Pycharm Setup
#############


.. vimeo:: 496742182

This page shows how to setup PyCharm so you can add tools to `Zoo Tools Pro 2 <https://create3dcharacters.com/zoo2/>`_ with Python.

After you’ve completed this setup you’ll be able to add and navigate through our code,
use auto-complete, go-to declarations and use PyCharm’s extra functionality.

PyCharm’s a great IDE (integrated development environment). If you’re using another IDE
this page may still be helpful, you can follow the steps here and translate them to your program.

If you’ve only coded inside of Maya and have never used an IDE then you may find this setup cumbersome,
but don’t worry, once you start working with PyCharm and Zoo you won’t want to return
to the old ways of interacting with Maya.

.. contents:: Table of Contents
   :local:
   :depth: 2

Git Access
==========

You can request direct access to our Git repositories our email info@create3dcharacters.com.
Git access isn't necessary for this tutorial.

What You'll Learn
=================

On this page, you’ll learn how to install Zoo tools Pro 2 and PyCharm.

You’ll learn how:

#. Zoo Tools Pro 2 is comprised of many Python Packages.
#. you can configure PyCharm so it connects to Zoo Tools and Maya.
#. to setup a PyCharm Project running Python 2.7 or 3.7
#. external Zoo Packages connect to Zoo and PyCharm so you can add your code.

See our other tutorials for more details about coding with Zoo.

Roadmap
=======

We’re planning on making the creation and management of packages easier in the future.
We have a planned UI called Package Manager that will be loaded within Maya for managing all Zoo Packages.

We’ll be refining the setup of Zoo Tools, so it gets easier over time.


Installing Zoo, Pycharm, Python & The Example Package
=====================================================

.. vimeo:: 496582963

This section covers the installation of Zoo and PyCharm.
You should also install a system version of Python for PyCharm.

Step 4 links to the zoo_example_custom_tools package download,
this is where you’ll add your code and you can place it anywhere on your machine or network.

Install Zoo Tools Pro
---------------------
Install Zoo Tools Pro 2 as per the `Zoo2 Install Page <https://create3dcharacters.com/maya-zoo-tools-pro-installer/>`_.
You can use the drag and drop or manual install methods.

Install Python 2.7.11 or Python 3.7
-----------------------------------

Maya runs Python 2.7 (2020 and below) and Python 3.7 (2022 and above).
Zoo Tools runs both Python 2 and 3 in tandem, so you can use either.

Maya comes with Python 2 or 3 bundled, but PyCharm prefers it to be installed on your system.

If you do not have Python installed on your system it’s a good idea to download and install it on your system here…

* `Python 2.7.11 <https://www.python.org/downloads/release/python-2711/>`_
* `Python 3.7.10 <https://www.python.org/downloads/release/python-3710/>`_

More help is `here <https://datascience.com.co/how-to-install-python-2-7-and-3-6-in-windows-10-add-python-path-281e7eae62a>`_ .

Install PyCharm Community Edition
---------------------------------

Download and install the latest community edition of `PyCharm here for your OS <https://www.jetbrains.com/pycharm/download/>`_ .

Download & Unzip The Package “zoo_example_custom_tools”
-------------------------------------------------------

Download our example custom package `zoo_example_custom_tools here <https://create3dcharacters.com/files/downloads/zooTools/zoo2/dev/zoo_example_custom_tools_2.8.3.zip>`_ .
This package matches Zoo 2.5.0 and possibly versions above.

Unzip the folder and put it anywhere on a local drive or your network.
The example folder will be our work area for the tutorials.

Since we’ll work out of a PyCharm Project directory later, you can place the package in a
folder called “my_tools” or similar. The “my_tools” folder can contain many packages/repositories.

Example unzip location:
D:/yourPath/my_tools/zoo_example_custom_tools

Later you’ll be able to create and configure your own custom packages,
but we’ll use the zoo_example_custom_tools package for now.

.. _Configuring Zoo In Pycharm:

Configuring Zoo In Pycharm
==========================

.. vimeo:: 496583055

Now that you’ve installed everything, you need to start a PyCharm Project and add all the code to the project.

We’ll want the Zoo’s auto-complete and go-to declarations working within PyCharm.

Since Zoo is made of multiple Python Packages there’s a couple more steps to follow than the usual IDE configuration.

Create A New PyCharm Project
----------------------------

In PyCharm:

* File > New Project
* If unsure set the location of your “my_tools” directory.

    Example PyCharm Project location: D:/yourPath/my_tools/
    This folder should contain the zoo_example_custom_tools folder we unzipped earlier.

* Keep the “New Environment Using” radio button “on”
* Set the Base Interpreter to Python 27 or Python 37
* Click Create

You’ve now created a PyCharm Project. PyCharm marks the project with a hidden folder
named “.idea” in the root of the “my_tools” directory.

The PyCharm Project automatically creates a new `virtual environment <https://realpython.com/python-virtual-environments-a-primer/>`_ with Python.

Add The Zoo Tools Pro 2 Code To PyCharm
---------------------------------------

Next, you’ll need to add the zootoolspro folder to PyCharm.
The zootoolspro directory is where all the Zoo code is stored after installing it.

* Click File > Open… and add the zootoolspro folder (see below).
* In the popup window click Attach

This will add the zootoolspro code repository to the current PyCharm window.

Finding Your zootoolspro Folder
Your zootoolspro folder is usually found in your maya/scripts/ folder. In Windows it’s usually found at.

C:/Users/~YourUserName/Documents/maya/scripts/zootoolspro

If you’re unsure of your preferences location you can find it inside Maya by running the following Python code.

.. code-block:: python

    import os, sys, subprocess
    import maya.mel as mel
    directoryPath = os.path.abspath(os.path.join(mel.eval("internalVar -upd") , "../.."))
    if sys.platform == "win32":
        os.startfile(directoryPath)
    else:
        opener = "open" if sys.platform == "darwin" else "xdg-open"
        subprocess.call([opener, directoryPath])
    print("Maya Preferences Directory Path: ", directoryPath)

Add The Folder zoo_example_custom_tools
---------------------------------------
The PyCharm Project should already contain the package we downloaded earlier,
but if it doesn't add it to the project now. This folder will be our work area where we can extend Zoo and add code.

If the project does not already contain the zoo_example_custom_tools folder then:

* Click File > Open… and add the zoo_example_custom_tools folder.
* In the popup window click Attach

Set the startup “Source” Directory
----------------------------------

Zoo is comprised of multiple Python Packages, and when it loads it combines
all the packages into a single directory structure using `pkgutil <https://docs.python.org/3/library/pkgutil.html>`_ .

You’ll need to set all the packages as sources so PyCharm knows where to load our code.

Lets start with the Zoo startup package and mark it as a Source Root.
This folder contains the startup code for Zoo.

In the Project tab open the zootoolspro folder to:

* zootoolspro/install/core/python
* Select the python folder
* Right-Click > Mark Directories As > Sources Root

The python folder should turn blue as it’s now a Source Root.

Set the Zoo Internal packages as “Source” Directories
-----------------------------------------------------
Then you need to set all of Zoo’s internal packages sources. Go to:

* zootoolspro/install/packages/

    Inside this folder, you can see all of the internal Zoo Packages.

* Open each package and find its version number folder.
* Select all the version number folders.
* Right-Click > Mark Directory As > Sources Root

You’ve now told PyCharm the location of all the internal Zoo code.

Set the zoo_example_custom_tools “Source” Directory
------------------------------------------------------
Now we’ll add the example-work-area package as a source. This is the folder named
zoo_example_custom_tools that we unzipped earlier.

* Select the folder zoo_example_custom_tools
* Right-Click > Mark Directory As > Sources Root

You’ve now told PyCharm where to find the zoo_example_custom_tools code.

Set Dependencies
----------------

Although you’ve set all the source directories, PyCharm still needs to be told
that these packages are dependant on each other.

* Go to File > Settings > Project:my_tools > Project Dependencies
* Select each of the three repository folders and make sure all the sub-folders are checked on.

PyCharm now sees all the Source Packages as one and you can browse between all
of the Zoo and example files with auto-completion.

Check The Code Is Working In PyCharm
------------------------------------

You should test that the code has been setup correctly inside PyCharm.

* Go to the folder zoo_example_custom_tools/zoo/apps/uitoolsets/
* Open polycubebuilder_01_simple.py

Poly Cube Builder is a simple UI that builds a cube.

Check that the zoo imports are not underlined with red, on lines 14 – 16.

Ctrl-click on the word toolsetwidgetmaya on line 14, that should open the file
toolsetwidgetmaya.py which is stored in the zoo_maya package.

The Zoo code has now been setup inside a PyCharm Project.

Load The Example Tools In Maya
==============================

.. vimeo:: 496583205

Inside Maya we want to be able to use the new tools from the zoo_example_custom_tools package.

Editing package_version.config
A file called package_version.config tells Zoo which packages to run when Maya is loaded.

We need to add the new path of the zoo_example_custom_tools folder to the package_version.config file. Find it here:

* zootoolspro/config/env/package_version.config

Double-Click this file in PyCharm to open it. It’s format is JSON.

Add the Example Tools package by adding the following lines of code to the JSON data.

.. code-block:: json

    },
    "zoo_example_custom_tools": {
        "type": "path",
        "path": "D:/yourPath/my_tools/zoo_example_custom_tools"
    }

Be sure the path to your zoo_example_custom_tools folder is correct,
and always use “/” forward slashes in JSON and Python path names.

Restart Maya To See The New Example Tools
Now restart Maya, when Zoo Tools Pro loads it will build a new shelf called “Custom_Tools”.

From inside Maya click on the first icon in the “Custom_Tools” shelf.
You’ll see a drop-down list of tools. These tools are all the Toolset UIs in the folder:

zoo_example_custom_tools/zoo/apps/uitoolsets/

Setup Complete
You have successfully installed the Example Package in Pycharm, auto-complete and go-to
declarations should now all be working. You can modify and add code as you wish.

Making Zoo Changes In Pycharm
=============================
From inside PyCharm open the Poly Cube Builder 01 UI

zoo_example_custom_tools/zoo/apps/uitoolsets/polycubebuilder_01_simple.py

You can find the icon of this tool on line 23.::

    "icon": "cubeWire",


Change this code to the save icon.::

    "icon": "save",

Now reload Zoo Tools to see the changes.

In Maya go:

* ZooToolsPro (shelf) > Developer Icon (purple code icon) > Reload

    Reload will rebuild the Zoo shelves and menus and reloaded all the code.

* Click on the Custom_Tools (shelf) > Green Sphere (icon) > Poly Cube Builder (Demo 01) Simple

You’ll see that the icon of the tool has changed to the internal “save” icon. You can see the changes in the menu too.

ZooTools (menu) > Modeling > Poly Cube Builder (Demo 01) Simple

Zoo Tools Pro 2 and PyCharm are working correctly. You can make code changes, reload Zoo in Maya and see your changes.




Updating Zoo Tools Pro 2
========================
Please note that when you update Zoo Tools Pro 2 you will have to re-setup the zootoolspro folder and mark Source Root folders again.

See :ref:`Configuring Zoo In Pycharm` steps 2, 4, 5 and 7.


Customizing Pycharm
===================

.. vimeo:: 496583403

You can further customize PyCharm. The following steps are optional.

Set .config files to be JSON
-----------------------------
You can change the type of CONFIG files to format as JSON

* File > Settings > Editor > File Types
* Highlight JSON in the side panel
* Add `*.config` and assign

Auto documentation as per Zoo
-----------------------------

We use documentation that’s compatible with `Sphinx Documentation <https://www.sphinx-doc.org/en/master/>`_ .

To match the documentation type:

File > Settings > Tools > Python Integrated tools > Docstrings > reStructuredText

To automatically fill documentation when you type “”” under a function/method.

* File > Settings > Editor > General > Smart Keys >
* Python > Insert type placeholders in the documentation comment stub

You can also hit alt enter on the args and kwargs to add new variables to the docstring.

Add Code Glance plugin (sublime sidebar)
----------------------------------------
To add a visual scroll bar similar to the Sublime Text Editor you can add the third-party plugin Code Glance:

* Settings > Plugin >
* Search for Code Glance, Install it and restart PyCharm

You will see a large scroll bar on the side of your code, this can be helpful while scrolling through your code.

Mouse Ctrl + Middle Wheel Sizes Text
------------------------------------

In the Settings/Preferences dialog Ctrl+Alt+S, go to

* File > Settings > Editor > General >
* Mouse Control > Change font size with Ctrl+Mouse Wheel (on)

You can now ctrl-middle-scroll for text size.




Summary
=======

This completes the installation of Zoo tools Pro 2 within PyCharm.

You’ve learned how:

* Zoo Tools Pro 2 is comprised of many Python Packages.
* you can configure PyCharm so it connects to Zoo Tools and Maya.
* to setup a PyCharm Project running Python 2.7 or 3.7
* external Zoo Packages connect to Zoo and PyCharm so you can add your code.

See our other tutorials for more details about coding with Zoo.
It’s worth starting with the `Zoo Code Overview Page <https://create3dcharacters.com/maya-zoo-tools-code-overview>`_.