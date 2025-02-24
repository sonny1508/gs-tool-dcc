from functools import partial

from zoo.apps.hiveartistui import uiinterface
from zoo.libs.pyqt.widgets import elements
from zoo.preferences.interfaces import coreinterfaces


class VisibilityButton(elements.IconMenuButton):
    def __init__(self, parent=None):
        """ The Rig Visibility button.

        :param parent: Parent Widget
        """
        super(VisibilityButton, self).__init__(iconName=["eye", "menuIndicator2"], parent=parent)
        self._core = uiinterface.instance().core()
        self._initTheme()
        self._generateMenu()

    def menuActions(self):
        """ Menu items that will be shown when the button is pressed. Uses HiveTool ids'

        :return:
        """
        return ("toggleGuidePivotVisibility",
                "toggleGuideShapeVisibility",
                "soloComponent",
                "unSoloComponentAll"
                )

    def _initTheme(self):
        """ Init theme. Maybe move to qss

        :return:
        """
        themes = coreinterfaces.coreInterface()
        self.setStyleSheet("background-color: rgb{}; border-radius: 4px;".format(themes.SECONDARY_BACKGROUND_COLOR))

    def _generateMenu(self):
        """ Generate the menu based on the menu actions

        :return:
        """
        hiveTools = self.menuActions()
        for h in hiveTools:
            if h == "---":
                self.addSeparator()
            else:
                tool = self._core.toolRegistry.plugin(h)
                self.addAction(name=tool.uiData['label'],
                               connect=partial(self._core.executeTool, h),
                               icon=tool.uiData["icon"],
                               toolTip=tool.uiData.get('tooltip'))
