import bpy

LITERAL_ZENUV_EVENT = 'zenuv_event'


class ZUV_OT_EventService(bpy.types.Operator):
    bl_idname = "wm.zuv_event_service"
    bl_label = "Zen UV Event Detection"
    bl_description = 'Drag event detection for Zen UV internal purposes'
    bl_options = {'INTERNAL'}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):

        t_event_data = {
            'ctrl': event.ctrl,
            'shift': event.shift,
            'alt': event.alt,
            'oskey': event.oskey,

            'mouse_x': event.mouse_x,
            'mouse_y': event.mouse_y,
        }

        bpy.app.driver_namespace[LITERAL_ZENUV_EVENT] = t_event_data

        return {'PASS_THROUGH'}  # Never change this !!!


class ZUV_OT_EventGet(bpy.types.Operator):
    bl_idname = "wm.zuv_event_get"
    bl_label = "Get Blender Event"
    bl_description = 'Get blender event and store'
    bl_options = {'INTERNAL'}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        t_event_data = {
            'ctrl': event.ctrl,
            'shift': event.shift,
            'alt': event.alt,
            'oskey': event.oskey,

            'mouse_x': event.mouse_x,
            'mouse_y': event.mouse_y,
            'mouse_region_x': event.mouse_region_x,
            'mouse_region_y': event.mouse_region_y,

            'type': event.type,
            'value': event.value
        }

        bpy.app.driver_namespace[LITERAL_ZENUV_EVENT] = t_event_data
        return {'FINISHED'}


def get_blender_event(force=False):
    if force:
        bpy.ops.wm.zuv_event_get('INVOKE_DEFAULT')
    return bpy.app.driver_namespace.get(LITERAL_ZENUV_EVENT, {})
