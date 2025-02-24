import logging
import os

from zoovendor.Qt import QtWidgets, QtCore

from zoo.core.plugin import pluginmanager
from zoo.libs.utils import color
from zoo.core.util import env
from zoo.libs.utils import filesystem
from zoo.apps.toolsetsui.widgets import toolsetwidget

if env.isMaya():
    from zoo.apps.toolsetsui.widgets import toolsetwidgetmaya

logger = logging.getLogger(__name__)


class ToolsetRegistry(QtCore.QObject):
    """Registry class to gather all the toolset classes.

    .. code-block:: python

        os.environ["ZOO_TOOLSET_UI_PATHS"] = "../examples/widgets"
        os.environ["ZOO_TOOLSET_LAYOUTS"] = "../examples/zootoolsets"
        reg = ToolsetRegistry()
        self.logger.debug("{}".format(reg.toolsetDefs))
        {'ConvertAllShadersRenderer': <class zoo.apps.generictoolsetui.zootoolsets.convertallshaders_renderer.ConvertAllShadersRendererToolset>,
        'importExportShaders': <class zoo.apps.generictoolsetui.zootoolsets.importexportshaders.ImportExportShadersToolset}

    """
    registryEnv = "ZOO_TOOLSET_UI_PATHS"
    toolsetJsons = "ZOO_TOOLSET_LAYOUTS"

    def __init__(self):
        super(ToolsetRegistry, self).__init__()
        # for discovering the component models
        self._toolsetDefs = {}
        self.toolsetGroups = []
        registryPluginName = "ToolsetRegistry"
        if env.isMaya():
            self._manager = pluginmanager.PluginManager(interface=[
                toolsetwidgetmaya.ToolsetWidgetMaya, toolsetwidget.ToolsetWidget],
                variableName="id",
                name=registryPluginName)
        else:
            self._manager = pluginmanager.PluginManager(interface=[toolsetwidget.ToolsetWidget],
                                                        variableName="id",
                                                        name=registryPluginName)

        self.discoverToolsets()

    def readJsons(self):
        """ Read jsons
        Merge the data in the jsons and put into one data structure: self.toolsetGroups

        :todo: Work with collisions
        :return:
        """
        jsonPaths = os.getenv(self.toolsetJsons, "")
        jsonPaths = [i for i in jsonPaths.split(os.pathsep) if os.path.isfile(i)]

        for jp in jsonPaths:
            self.toolsetGroups += filesystem.loadJson(jp)['toolsetGroups']

        self.toolsetGroups.sort(key=lambda x: x["name"])

    @property
    def toolsetDefs(self):
        if self._toolsetDefs == {}:
            self.discoverToolsets()
        return self._toolsetDefs

    def discoverToolsets(self):
        """Searches the component library specified by the environment variable "ZOO_TOOLSET_UI_PATHS"
        """
        self.readJsons()
        self._toolsetDefs = {}
        paths = os.environ.get(self.registryEnv, "").split(os.pathsep)
        if not paths:
            logger.warning("No paths found for '{}'".format(self.registryEnv))
            return False
        self._manager.registerPaths(paths)

        for toolset in self._manager.plugins.values():
            self._toolsetDefs[toolset.id] = toolset

        return True

    def groupsData(self, showHidden=False):
        return [g for g in self.toolsetGroups if showHidden or g.get('hidden') is not True]

    def groupType(self, groupName):
        """Get type by group name

        :param groupName:
        :return:
        """
        for g in self.toolsetGroups:
            if g['name'] == groupName:
                return g['type']

    def groupColor(self, groupType):
        for g in self.toolsetGroups:
            if g['type'] == groupType:
                return g['color']

    def toolsetColor(self, toolsetId):
        """ Get Toolset Colour
        Calculate colour based on the group colour from where it was found.
        Also shifts the colour depending on its position in the list.
        The further down the list, the more the colour gets shifted.

        :param toolsetId:
        :return:
        """

        for g in self.toolsetGroups:
            if toolsetId in g['toolsets']:
                index = g['toolsets'].index(toolsetId)
                groupColor = tuple(g['color'])
                hueShift = g['hueShift'] * (index + 1)

                return tuple(color.hueShift(groupColor, hueShift))

        if toolsetId == "toolsetId":
            return (255, 255, 255)

        logger.warning("toolsetId \"{}\" not found in any toolset group data dictionary for colours".format(toolsetId))

        return (255, 255, 255)

    def groupTypes(self):
        """Return group types

        :return: list(type)
        """

        return [g['type'] for g in self.toolsetGroups]

    def groupNames(self):
        """Return list of names

        :return:
        """
        return [g['name'] for g in self.toolsetGroups]

    def definitions(self, sort=True):
        """Returns a list of toolset definitions

        :return:
        """
        ret = self.toolsetDefs.values()
        if sort:
            ret = list(ret)
            ret.sort(key=lambda toolset: toolset.uiData['label'])

        return ret

    def toolsetIds(self, groupType):
        """ Return toolsets based on group type.

        :param groupType:
        :return:
        """
        for g in self.toolsetGroups:
            if g['type'] == groupType:
                return g['toolsets']

    def groupFromToolset(self, toolsetId, showHidden=False):
        """ Looks for the original group

        :param showHidden: Show hidden toolsets
        :type showHidden:
        :param toolsetId:
        :return groupType: groupType
        """

        for g in self.groupsData(showHidden=showHidden):
            for t in g['toolsets']:
                if t == toolsetId:
                    return g['type']

    def toolsets(self, groupType):
        """ List of toolsets under the group type

        :param groupType:
        :return:
        :rtype: class of toolsetwidget.ToolsetWidgetMaya
        """
        if not groupType:
            raise TypeError("'groupType' must not be empty")
        toolsetIds = self.toolsetIds(groupType)
        ret = []
        for t in toolsetIds:
            toolset = self.toolset(t)
            if toolset:
                ret.append(self.toolset(t))
        return ret

    def toolsetWidget(self, toolsetId):
        """ Creates a new toolset widget based on the toolsetId

        returns list of widgets. Each widget is the different content sizes eg simplified, advanced
        # todo this needs to be updated to work with the new toolsetWidget changes

        :param toolsetId:
        :return:
        """

        toolsetClass = self.toolset(toolsetId)

        ret = []
        for applyContents in toolsetClass.contents():
            newWidget = QtWidgets.QWidget()
            newWidget.setProperty("color", self.toolsetColor(toolsetId))
            applyContents(newWidget, None, None)  # Apply contents to widget
            ret.append(newWidget)

        return ret

    def toolset(self, toolsetID):
        """ Returns toolset based on Id

        :param toolsetID: toolset to find by id
        :type toolsetID: basestring
        :rtype: toolsetwidgetmaya.ToolsetWidgetMaya
        """
        ret = self.toolsetDefs.get(toolsetID)

        if ret is None:
            logger.warning(" \"{}\" toolset not found. Make sure the toolset ID name is correct in the toolsetgroups, "
                           "or the toolset folder has been added to 'ZOO_TOOLSET_UI_PATHS' in 'zoo_package.json'.".format(
                toolsetID))

        return ret


def toolset(toolsetID):
    """ Gets a toolset definition class by ID.

    Creates a new toolsetRegsistry instance and runs ToolsetRegistry.toolset()
    May be slow since it creates the instance and discovers the toolsets.

    .. code-block:: python

        from zoo.apps.toolsetsui import registry
        toolsetCls = registry.toolset("zooVertSkinning")

        zooVertSkinning = toolsetCls()

    :param toolsetID: toolset to find by id
    :type toolsetID: basestring
    :return: Subclass of ToolsetWidgetItem. Toolset class definition
    :rtype: toolsetwidgetmaya.ToolsetWidgetMaya

    """

    return instance().toolset(toolsetID)


def instance():
    """Returns the global instance of the toolset registry.
    :rtype: :class:`ToolsetRegistry`
    """
    global _instance
    if _instance is None:
        _instance = ToolsetRegistry()
    return _instance


_instance = None
