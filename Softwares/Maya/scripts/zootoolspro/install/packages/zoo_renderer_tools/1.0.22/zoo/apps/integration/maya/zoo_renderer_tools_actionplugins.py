from zoo.apps.toolpalette import palette


class RendererIconsShelf(palette.ActionPlugin):
    id = "zoo.shelf.rendering"
    creator = "Andrew Silke"
    tags = ["shelf", "icon"]
    uiData = {"icon": "renderingMenu_shlf",
              "label": "Renderer Tools",
              "color": "",
              "multipleTools": False,
              "backgroundColor": ""
              }

    def execute(self, *args, **kwargs):
        name = kwargs["variant"]
        from zoo.libs.maya.cmds.renderer import multirenderersettings, rendererconstants
        from zoo.libs.maya.utils import mayacolors
        if name == "zoo_set_default_render_settings":
            multirenderersettings.setDefaultRenderSettingsAuto()
        elif name == "zoo_open_render_view":
            multirenderersettings.openRenderviewAuto()
        elif name == "zoo_open_render_view_ipr":
            multirenderersettings.openRenderviewAuto(ipr=True)
        elif name == "zoo_open_render_view_final":
            multirenderersettings.openRenderviewAuto(final=True)
        elif name == "zoo_set_arnold_renderer":
            multirenderersettings.changeRenderer(rendererconstants.ARNOLD)
        elif name == "zoo_set_redshift_renderer":
            multirenderersettings.changeRenderer(rendererconstants.REDSHIFT)
        elif name == "zoo_set_renderman_renderer":
            multirenderersettings.changeRenderer(rendererconstants.RENDERMAN)
        elif name == "zoo_set_vray_renderer":
            multirenderersettings.changeRenderer(rendererconstants.VRAY)
        elif name == "zoo_set_aces_colorspace":
            mayacolors.setColorSpaceAces()
        elif name == "zoo_set_aces_colorspace_noTone":
            mayacolors.setColorSpaceAcesNoTone()
        elif name == "zoo_set_linear_colorspace":
            mayacolors.setColorSpaceLinear()
