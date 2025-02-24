.. _gptInstallation-reference:

Installation
############

The following section outlines the technical details of Zoo Chat-GPT.


Prerequisites
--------------

#. OpenAI only support Python 3 and above, in the case of Maya this starts at Maya 2022 by default.

#. Ensure that your firewall allows exceptions for "pypi.python.org", "pypi.org", and "pythonhosted.org"
   as these are the sites from which OpenAI and its Python library dependencies will be downloaded.

#. Ensure that you have you're ZootoolsPro preferences folder path using ascii characters only, we have found
   that to be a limitation with the download via subprocess.Popen function which downloads the OpenAI library.


ZooTools will download the OpenAI library and its dependencies into your Zoo Tools Preferences folder under
`zoo_preferences/cache/site-packages` for each for each version of python that you use eg. maya 2023 == python 3.9.7 .


OpenAI API Key
--------------

To use the Chat GPT library of OpenAI, an API key is required.
You can obtain a free API key by visiting the following link: https://platform.openai.com/account/api-keys. and logging
in with your OpenAI account.

When you enter the API key in the Zoo Chat GPT window, the openai.api_key is checked to confirm if the key is valid.
This key needs to be set every time you launch Maya.

To avoid setting the API key every time a new Maya session is launched,
you can add the following environment variable: ZOO_OPENAI_API_KEY.


How the Automatic install works
-------------------------------

If you're curious about how OpenAI is installed, you may be wondering if it's possible to manually install it,
or if you can use an existing installation. To learn about manual installation, refer to :ref:`see <chatgpt_manual_Installation-reference>`.

When the Chat GPT window is launched, zootools checks to see if the OpenAI library is
already installed by attempting to import the `openai` library. If the import fails, then the installation process starts.

The installation process uses the `subprocess.Popen` function to run the following command::

    {currentPythonExe} -m pip install {allRequirements} --target {myPreferences}\cache\site-packages\3.7.7

`{AllRequirements}` is a resolved list of libraries to install, which can be found in
the `zoo_chatgpt` package in the `/build/requirements-3.txt` file.
We do this to ensure that we only install the libraries and their specific versions
hat we know work based on our testing.

That's all there is to the installation.

.. _chatgpt_manual_Installation-reference:

Manual Installation
-------------------


This section provides instructions for manually installing the OpenAI library and its dependencies.
This is helpful if you have security restrictions on your computer or if you want to install the library on a network drive.

To install OpenAI manually, run the following command::

    "%PROGRAMFILES%\Autodesk\Maya2022\bin\mayapy.exe" -m pip install openai --target {myPreferences}\cache\site-packages\3.7.7

.. Note:: Replace {myPreferences} in the target path with your own path to your Zoo Tools Pro preferences folder.

You will need to run this command for each version of Maya that uses a different Python version.