"""Locator related code

Example use:

.. code-block:: python

    from zoo.libs.maya.cmds.objutils import locators
    locators.createLocatorAndMatch(handle=False, locatorSize=1.0)

    from zoo.libs.maya.cmds.objutils import locators
    locators.createLocatorsMatchMany(name="", handle=False, locatorSize=1.0, message=True)

Author: Andrew Silke

"""


import maya.cmds as cmds

from zoo.libs.utils import output
from zoo.libs.maya.cmds.objutils import matching


def createLocator(name="", handle=False, locatorSize=1.0):
    """

    :param name: The name of the locator, if empty will be default "locator1"
    :type name: str
    :param handle: Show display handle for the object?
    :type handle: bool
    :param locatorSize: The size of the locator to be created
    :type locatorSize: float
    :return locatorName: The name of the locator created
    :rtype locatorName: str
    """
    if not name:
        locator = cmds.spaceLocator()[0]
    else:
        locator = cmds.spaceLocator(name=name)[0]

    # Locator settings ------------------------------
    cmds.setAttr(".localScale".format(locator), locatorSize, locatorSize, locatorSize, type="double3")
    if handle:
        cmds.setAttr(".displayHandle".format(locator), 1)
    return locator


def createLocatorAndMatch(name="", handle=False, locatorSize=1.0, message=True):
    """Creates a locator and matches it to the currently selected object or component selection center or world center.

    :param name: The name of the locator, if empty will be default "locator1"
    :type name: str
    :param handle: Show display handle for the object?
    :type handle: bool
    :param locatorSize: The size of the locator to be created
    :type locatorSize: float
    :param message: Report a message to the user?
    :type message: bool

    :return locatorName: The name of the locator created
    :rtype locatorName: str
    """
    selectedObjList = cmds.ls(sl=1, l=1)

    locator = createLocator(name=name, handle=handle, locatorSize=locatorSize)

    # Match to selection and report message -------------------------------
    if matching.matchToCenterObjsComponents(locator, selectedObjList):
        if message:
            output.displayInfo("`{}` created and matched to selection".format(locator))
    else:
        if message:
            output.displayInfo("Created `{}`".format(locator))

    cmds.select(locator, replace=True)
    return locator


def createLocatorsMatchMany(name="", handle=False, locatorSize=1.0, message=True):
    """Creates locators at the center of each selected object.

    :param name: The name of the locator, if empty will be default "locator1"
    :type name: str
    :param handle: Show display handle for the object?
    :type handle: bool
    :param locatorSize: The size of the locator to be created
    :type locatorSize: float
    :param message: Report a message to the user?
    :type message: bool
    :return locatorList: A list of locators created.
    :rtype locatorName: list(str)
    """
    matched = False
    locators = list()
    selObjs = cmds.ls(selection=True)
    if not selObjs:
        output.displayWarning("Nothing is selected please select objects.")
        return list()

    for obj in selObjs:
        locator = createLocator(name=name, handle=handle, locatorSize=locatorSize)
        if matching.matchToCenterObjsComponents(locator, [obj]):
            matched = True

    if matched and message and locators:
        output.displayInfo("Success: Locators created. {}".format(locators))
