""" Hive tool functions here.

"""

import sys
import traceback

from zoo.apps.hiveartistui import uiinterface
from zoo.core.plugin import plugin
from zoo.libs import iconlib
from zoo.libs.utils import general
from zoovendor.Qt import QtCore, QtWidgets, QtGui

if general.TYPE_CHECKING:
    from zoo.apps.hiveartistui import model


class HiveTool(QtCore.QObject):
    id = ""
    creator = ""
    uiData = {"icon": "hive",
              "iconColor": (192, 192, 192),
              "iconColorToggled": (192, 192, 192),
              "tooltip": "",
              "label": ""}
    refreshRequested = QtCore.Signal(bool)
    _icon = None  # type: QtGui.QIcon
    _iconToggled = None

    def __init__(self, logger, uiInterface):
        """

        :param logger:
        :type logger: :class:`logging.Logger`
        :param uiInterface:
        :type uiInterface: :class:`zoo.apps.hiveartistui.uiinterface.UiInterface`
        """
        super(HiveTool, self).__init__()
        self.logger = logger
        self.parentWidget = uiInterface.artistUi()
        self.selectedModels = []  # type: list[model.ComponentModel]
        self._rigModel = None  # type: model.RigModel or None

        self.uiInterface = uiinterface.instance()
        self.model = None  # type: model.ComponentModel or None
        self.attachedWidget = None  # type: QtWidgets.QWidget or None
        self._core = self.uiInterface.core()

        self.uiData["iconColor"] = self.uiData.get("iconColor") or HiveTool.uiData["iconColor"]

    def icon(self, variantId=None, refresh=False):
        """
        :rtype: :class:`QtGui.QIcon`
        """
        iconColor = self.uiData.get("iconColor") or HiveTool.uiData["iconColor"]

        if self._icon is None or refresh:
            self._icon = iconlib.iconColorizedLayered(self.uiData["icon"], colors=iconColor)

        return self._icon

    @property
    def rigModel(self):
        """

        :return:
        :rtype: zoo.apps.hiveartistui.model.RigModel
        """
        return self._rigModel

    def rigExists(self):
        """ If rig exists True, false otherwise

        :return:
        :rtype:
        """
        return not self.rigModel or (self.rigModel and not self.rigModel.exists())

    @rigModel.setter
    def rigModel(self, value):
        """ Rig Model

        :param value:
        :type value: zoo.apps.hiveartistui.model.RigModel
        :rtype:
        """
        self._rigModel = value

    def iconToggled(self, refresh=False):
        """

        :param refresh:
        :type refresh:
        :return:
        :rtype: Qt.QtGui.QIcon
        """

        iconColor = self.uiData.get("iconColorToggled")
        if not iconColor:
            iconColor = HiveTool.uiData["iconColorToggled"]
        if self._iconToggled is None or refresh:
            self._iconToggled = iconlib.iconColorizedLayered(self.uiData["icon"], colors=iconColor)

        return self._iconToggled

    def setSelected(self, selectionModel):
        """ Set selected

        :param selectionModel:
        :type selectionModel:
        :return:
        :rtype:
        """
        self.selectedModels = selectionModel.componentModels
        self._rigModel = selectionModel.rigModel

    def selectedComponents(self):
        """ Component models based on selection and what is the target model

        - Uses target model first and foremost. It will exclude selectedModels if not included in selectedModels
        - If target model is in selectedModels, it includes all selectedModels.
        - If target model is none, it will use the last element in selectedModels

        :return:
        :rtype: list[:class:`model.ComponentModel`]
        """

        if self.model in self.selectedModels:  # use model directly if not in selection
            componentModels = list(set(self.selectedModels + [self.model]))
        else:
            if self.model is not None:
                componentModels = [self.model]
            else:
                if len(self.selectedModels) > 0:
                    componentModels = [self.selectedModels[-1]]  # use last selected if no target model
                else:
                    return []

        return componentModels

    def refreshIcons(self):
        self.icon(refresh=True)
        self.iconToggled(refresh=True)

    def refreshSelectedComponents(self):
        """ Refresh selected components only. in the ui.

        :return:
        """
        self.refreshComponents(self.selectedComponents())

    def refreshComponents(self, componentModels):
        self.uiInterface.artistUi().softRefreshComponents(componentModels)

    def refreshAll(self):
        """ Refresh Everything in the rig.

        :return:
        """
        self.uiInterface.refreshUi()

    def variantById(self, variantId):
        """ Get Variant from tool by id

        :param variantId:
        :type variantId: basestring
        :return:
        :rtype:
        """

        if not variantId:
            return {}
        try:
            ret = [x for x in self.variants() if x['id'] == variantId][0]
        except:
            raise Exception("VariantID: '{}' not found for '{}'".format(variantId, self.id))
        return ret

    def process(self, variantId=None, args=None):
        args = args or {}
        stat = plugin.PluginStats(self)
        exc_type, exc_value, exc_tb = None, None, None
        try:
            stat.start()
            self.logger.debug("Executing plugin: {}".format(self.id))
            variant = self.variantById(variantId)
            if variantId:
                exeArgs = variant['args']
                exeArgs.update(args)
                return self.execute(**exeArgs)
            return self.execute(**args)

        except Exception:
            exc_type, exc_value, exc_tb = sys.exc_info()
            stat.finish(traceback.format_exception(exc_type, exc_value, exc_tb))
            raise
        finally:
            if not exc_type:
                stat.finish(None)
            self.logger.debug("Finished executing plugin: {}, "
                              "execution time: {}".format(self.id,
                                                          stat.info["executionTime"]))

    def execute(self, **kwargs):
        """ Execute based on selected component models and rig model
        """
        pass

    def requestRefresh(self, force=False):
        """ Request a refresh in the UI

        :return:
        """
        self.logger.debug("HiveTool: {} requested UI refresh".format(self.id))
        self.refreshRequested.emit(force)

    def variants(self):
        return []

