import bpy

from ZenUV.utils.blender_zen_utils import update_areas_in_all_screens


class ZUV_OT_UpdateToggle(bpy.types.Operator):
    bl_idname = 'wm.zenuv_update_toggle'
    bl_label = 'Toggle Value'
    bl_description = 'Toggles value with updating viewports'
    bl_options = {'INTERNAL'}

    data_path: bpy.props.StringProperty(
        name='Data Path',
        default='',
        options={'HIDDEN', 'SKIP_SAVE'}
    )

    def execute(self, context: bpy.types.Context):
        bpy.ops.wm.context_toggle('INVOKE_DEFAULT', data_path=self.data_path)
        update_areas_in_all_screens(context)
        return {'FINISHED'}


context_utils_classes = [
    ZUV_OT_UpdateToggle,
]
