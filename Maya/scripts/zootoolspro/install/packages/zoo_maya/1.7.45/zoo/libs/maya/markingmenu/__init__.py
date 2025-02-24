"""Maya RMB marking menu setup
"""

from .menu import (MarkingMenu,
                   Registry,
                   Layout,
                   findLayout,
                   InvalidJsonFileFormat,
                   MissingMarkingMenu,
                   MarkingMenuCommand)

from .markingmenuoverride import setup as setupTrigger
from .markingmenuoverride import setup as resetTriggerToDefaults

removeAllActiveMenus = MarkingMenu.removeAllActiveMenus
removeExistingMenu = MarkingMenu.removeExistingMenu