=========
ChangeLog
=========


1.0.8 (2024-05-10)
------------------

Bug
~~~

- (Core) Fix Chatgpt Ui not working outside of maya.
- (Pyside6) Fixes for pyside6.


1.0.7 (2024-05-03)
------------------

Change
~~~~~~

- (Openai) Update openAi to 1.13.3.


1.0.6 (2024-01-22)
------------------

Bug
~~~

- (Install) Added behavior to update openai to a 1.7.1 if the user is out of date.
- (Pip) Updated Api version to openai==1.7.1.


1.0.5 (2023-12-05)
------------------

Bug
~~~

- (Pip) Pip packages was always installing the latest instead of the specified versions.
- (Pip) Pip requirements was being installed twice.


1.0.4 (2023-08-22)
------------------

Change
~~~~~~

- (Toolpalette) Change Definition type to Action Type for better clarity in naming.


1.0.3 (2023-08-11)
------------------

Added
~~~~~

- (Chatgpt_Actionplugins.Py) Added new tooltips for the Chat GPT shelf icon.


1.0.2 (2023-06-22)
------------------

Change
~~~~~~

- (Controller) Better support for Host controllers.
- (Definitions) Update actionplugins to use new Host Engine code.


1.0.1 (2023-05-03)
------------------

Bug
~~~

- (Apikey) Api key not found nor set if the ZOO_OPENAI_KEY env var is set.
- (Codeexecution) Added Undo chunk.

Change
~~~~~~

- (Core) Split code into Separate modules where needed.
- (Maya) Added separate maya controller to manage maya only code execution.
- (Chatgpt_Actionplugins.Py Chatgptwin.Py) Removed beta status.


1.0.0 (2023-04-05)
------------------

Added
~~~~~

- (Chatgpt) Added first version of Chat GPT GUI.
