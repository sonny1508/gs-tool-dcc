from zoo.apps.toolpalette import palette
from zoo.libs.maya.cmds.hotkeys import definedhotkeys

class RiggingIconShelf(palette.ActionPlugin):
    id = "zoo.shelf.rigging"
    creator = "Andrew Silke"
    tags = ["shelf", "icon"]
    uiData = {"icon": "riggingMenu_shlf",
              "label": "Manual Rigging Tools: \nTools related to joints, control curves, constraints and more.",
              "color": "",
              "multipleTools": False,
              "backgroundColor": ""
              }

    def execute(self, *args, **kwargs):
        name = kwargs["variant"]
        if name == "smoothSkin":
            definedhotkeys.open_brSmoothWeights()
        elif name == "skinWrangler":
            from zoo.libs.skinwrangler import skinwrangler
            skinwrangler.skinWrangler()
        elif name == "brShapes":
            definedhotkeys.open_brShapes()
        elif name == "brSkinTransferExport":
            definedhotkeys.open_brTransferSkinWeights_export()

