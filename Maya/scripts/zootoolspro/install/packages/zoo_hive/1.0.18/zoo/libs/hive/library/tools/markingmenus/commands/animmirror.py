from zoo.libs.maya.markingmenu import menu
from zoo.core.util import zlogging

from zoo.libs.hive.anim import mirroranim
from zoo.apps.toolsetsui.run import openToolset

logger = zlogging.getLogger(__name__)


class AnimMirror(menu.MarkingMenuCommand):
    id = "hiveAnimMirror"
    creator = "Zootools"

    def execute(self, arguments):
        """Mirrors animation or a pose on the selected controls.

        :type arguments: dict
        """
        mirroranim.flipPoseCtrlsSelected(flip=False, animation=arguments["animation"])


class AnimFlipMirror(menu.MarkingMenuCommand):
    id = "hiveAnimFlipMirror"
    creator = "Zootools"

    def execute(self, arguments):
        """Flip Mirrors animation or a pose on the selected controls.

        :type arguments: dict
        """
        mirroranim.flipPoseCtrlsSelected(flip=True, animation=arguments["animation"])


class OpenMirrorWindow(menu.MarkingMenuCommand):
    id = "hiveOpenMirrorWindow"
    creator = "Zootools"

    def execute(self, arguments):
        """Opens the Hive Mirror Flip Animation Toolset

        :type arguments: dict
        """
        openToolset("hiveMirrorPasteAnim", advancedMode=False)