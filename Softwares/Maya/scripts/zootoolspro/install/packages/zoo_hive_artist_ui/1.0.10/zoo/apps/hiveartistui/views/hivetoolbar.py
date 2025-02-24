from zoo.apps.hiveartistui import artistuicore
from zoo.core.util import zlogging
from zoo.libs.pyqt import utils
from zoo.libs.pyqt.widgets import flowtoolbar
from zoo.libs.utils import profiling
from zoovendor.Qt import QtCore

logger = zlogging.getLogger(__name__)


class HiveToolbar(flowtoolbar.FlowToolBar):
    """
    The Hive artist UI toolbar
    """

    requestRefresh = QtCore.Signal()

    def __init__(self, core, parent, iconColor=(255, 255, 255), hueShift=30):
        """

        :param core:
        :type core: artistuicore.HiveUICore
        :param parent:
        :param iconColor:
        :param hueShift:
        """

        self.core = core
        self.iconColor = iconColor
        self.hueShift = hueShift
        self.toolRegistry = self.core.toolRegistry
        self.hiveTools = []

        self.artistUi = core.artistUi()

        super(HiveToolbar, self).__init__(parent=parent)

    def initUi(self):
        super(HiveToolbar, self).initUi()
        self.setFixedWidth(utils.dpiScale(32))

        self.setIconSize(18)
        self.setIconPadding(0)
        self.flowLayout.setSpacingX(0)
        self.flowLayout.setSpacingY(utils.dpiScale(3))
        logger.debug("Beginning search for hive UI tools")
        # for ht in self.toolRegistry.iterToolbarTools():  # todo: hive tools temporarily hidden
        #     self.addTool(ht)
        logger.debug("Finished searching for hive tools: Total: {}".format(len(self.hiveTools)))

    def buttonClicked(self, wgt, name):
        """ Button clicked by user.
        :param wgt:
        :param name:
        :return:
        """
        tool = wgt.property("tool")  # type: zoo.apps.hiveartistui.hivetool.HiveTool
        # No variants mean we should execute tool directly, otherwise we wait for the user to click on an action
        if tool is not None and not tool.variants():
            self.executeTool(tool)

    @profiling.fnTimer
    def executeTool(self, tool, args=None):
        if tool is not None:
            args = args or {}
            tool.setSelected(self.core.selection)
            logger.debug("Executing HiveTool: {}".format(tool.id))
            tool.execute(**args)

    def addTool(self, hiveTool):
        """ Add new tool button by hive tool

        :return:
        """
        # temp logger, need to hook the internal log to the ui
        tool = hiveTool(logger, parent=self,
                        uiInterface=self.core.uiInterface)  # type: zoo.apps.hiveartistui.hivetool.HiveTool
        variants = tool.variants()
        uiData = tool.uiData
        # Add menu items if there are variants
        if variants:
            actions = []
            for v in variants:
                actions.append((v['name'], lambda x=v['args']: self.executeTool(tool, x)))
            btn = self.addToolMenu(uiData.get("icon", ""),
                                   uiData.get("label", "NO_TITLE"),
                                   actions=actions,
                                   iconColor=uiData.get("iconColor", (192, 192, 192)))
        else:
            btn = self.addToolButton(uiData.get("icon", ""),
                                     uiData.get("label", "NO_TITLE"),
                                     iconColor=uiData.get("iconColor", (192, 192, 192)))

        self.hiveTools.append(tool)
        btn.setProperty("tool", tool)
        tool.refreshRequested.connect(self.requestRefresh.emit)

        return btn
