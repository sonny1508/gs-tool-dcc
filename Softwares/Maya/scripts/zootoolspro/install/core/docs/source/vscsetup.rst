.. _vsc_setup:

Version Control Setup
#####################


This page shows how to setup a connection to Zoo Tools on GitLab .

With Git access you’ll be able to access alpha tools, push requests and pull from the
latest version of master between releases.
You'll also have access to any developer tools we create as we go.

This page assumes you’ve already completed the :ref:`PyCharm Install Page<pycharm_setup>` and
read the `Code Overview Page. <https://create3dcharacters.com/maya-zoo-tools-code-overview/>`_

The IDE PyCharm is optional though recommended.

We’ll also assume you are familiar with Git and how it works! 🙂

.. Note::

    This installation Requires Python3 to be installed.

Git Access
==========

You must request git access to Zoo Tools Pro 2.
Please email us if you are interested at info@create3dcharacters.com, or contact us through the Zoo Discord Channel .


Setup
=====

You’ll need Git installed on your machine, you can install it `here. <https://git-scm.com/downloads>`_

We use `GitLab.com <https://gitlab.com/>`_ to host the dev copy of Zoo Tools Pro.

First do one of the following:

#. Clone the dev installer via the below command.
    .. tabs::
        .. group-tab:: SSH

            git clone git@gitlab.com:zootoolspro/zoo_dev_download.git

        .. group-tab:: HTTPS

            git clone https://gitlab.com/zootoolspro/zoo_dev_download.git

#. Download the zip file of the repository.::

    https://gitlab.com/zootoolspro/zoo_dev_download/-/archive/main/zoo_dev_download-main.zip



This downloaded folder contains our dev installer script
Now run the below shell script in the zoo_dev_download folder for you're operating system.

.. note::

    Before running the below make sure you have admin permissions for creating symlink(Junction points on windows)

 .. tabs::
        .. group-tab:: Windows

            devinstall.ps1

        .. group-tab:: Linux

            devinstall.sh

This script will run an interactive session walking you through the setup process, lets have a look.

#. Specify the install path. We recommend installing outside of the zoo_dev_download folder to separate git folders.

    .. figure:: /resources/vcsSetup_installPath.png
        :align: center
        :alt: alternate text
        :figclass: align-center

        :colorlightgrayitalic:`Specify the Install path.`

#. Specify whether to use SSH or HTTPS for cloning, defaults to Yes, we recommend using SSH.

    .. note::

        Make sure you setup your machine for SSH or HTTPS for Gitlab before continuing.

    .. figure:: /resources/vcsSetup_sshorhttpsPath.png
        :align: center
        :alt: alternate text
        :figclass: align-center

        :colorlightgrayitalic:`Specify the Install path.`

#. Our Installer will setup a virtual environment which installs any dependencies, this next part
   allows you to decided whether those extra dependencies are desired.

   .. figure:: /resources/vcsSetup_dependencies.png
        :align: center
        :alt: alternate text
        :figclass: align-center

        :colorlightgrayitalic:`Specify Yes if developer dependencies should be included.`

#. Next step determines whether PySide2 should be included in the dependencies, this option is
   useful when you don't have you're own version on PySide2 already.

   .. figure:: /resources/vcsSetup_pyside2.png
        :align: center
        :alt: alternate text
        :figclass: align-center

        :colorlightgrayitalic:`Specify Yes if PySide2 should be installed as a dependency.`

#. Final Option Sets up Autocompletion for PySide2 and other modules in our zoovendor dependencies.

   .. note::

        As mentioned early on this page you'll need admin permissions to create a symlink for this step.

   .. figure:: /resources/vcsSetup_autocomplete.png
        :align: center
        :alt: alternate text
        :figclass: align-center

        :colorlightgrayitalic:`Specify Yes if Yes if pycharm autocompletion should be setup.`



Optional Set Custom zoo_preferences Location
--------------------------------------------
The Zoo Tools preferences are automatically created in a default location such as documents/zoo_preferences.

You can change this default location with the file preference_roots.config.

The path should already exist and contain the folder zoo_preferences Eg.::

    {"user_preferences": "D:/SomePath/zoo_preferences"}


Loading Zoo Tools in Maya
=========================

This video shows how to use a Windows .BAT file to create a Zoo Dev environment and connect Maya to the Zoo Tools Pro module.

.. vimeo:: 575728151

Other the Dev installer will create bat files for 2019 and above for you, you may need to change the maya location path
if it's not in the standard install location.

New Maya Prefs Directory
------------------------

The installer will create a mayaPrefs folder and setup the auto generated bat files to point maya to this
folder however the below is how to do it manually.

We’ll use a new Maya preferences directory so that Zoo can be run clean within it’s own environment,
this keeps the dev version separated from your regular Maya environment (usually found inside documents/maya).

The folder /zootoolspro/mayaPrefs can be the new location for Maya’s preferences when you’re using Zoo Dev.

Maya .BAT To Start The Zoo Dev Environment
In the folder /zootoolspro/bin you’ll edit a .BAT file (only for Windows) to start Maya and point it to Zoo.

In PyCharm edit the file maya2022.bat::

    set MAYA_APP_DIR=D:\somePath\repositories\zootoolspro\mayaPrefs
    set MAYA_MODULE_PATH=D:\somePath\repositories\zootoolspro\zoo\install\core\extensions\maya
    set ZOO_ADMIN=1
    set MAYA_NO_WARNING_FOR_MISSING_DEFAULT_RENDERER=1
    call "C:\Program Files\Autodesk\Maya2022\bin\maya.exe"
    exit

Note: Be sure that the MAYA_APP_DIR and MAYA_MODULE_PATH are valid and match your new folders.

Also check that .EXE path links to where your Maya.EXE is actually installed.

When the .BAT file is run Maya will use the new custom preferences location for it’s prefs,
rather than using the default location documents/maya preferences.


Create Maya Launcher
====================

.. vimeo:: 575728229

Create Desktop Icon
-------------------
To create a desktop icon Right-click the .BAT file and click on create shortcut.

Copy this shortcut to the desktop and rename it nicely.

Right-Click on the icon and change it’s image by clicking on Change Icon
Add the line::

    %ProgramFiles%\Autodesk\Maya2022\bin\maya.exe

Or use the full path to your .EXE. Icons should appear and select one.

You can run this icon to load the new Maya Environment copy of Dev Zoo Tools Pro.


This video shows how you can create branches in PyCharm so you’re not working on master.

.. vimeo:: 575728414

You’ll also see how to commit, push and pull from/to GitLab.com

Note that the dev copy can break more than the official release versions of Zoo,
we are working on it live! Keep in touch with us on the Zoo Discord or via email
in case of issues and unexpected errors.