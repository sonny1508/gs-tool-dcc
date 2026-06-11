bl_info = {
    "name": "Perspective-n-Point (Offline)",
    "author": "",
    "version": (0, 1, 0),
    "blender": (3, 6, 10),
    "location": "Clip Editor > Tools > Solve > Solve PnP",
    "description": "PnP solver using OpenCV.",
    "category": "Camera",
}

import bpy
import os
import sys
import importlib

# Force add OpenCV path to the BEGINNING of sys.path
username = os.environ['USERNAME']
opencv_path = f"C:\\Users\\{username}\\AppData\\Local\\Programs\\Python\\Python39\\Lib\\site-packages"

# Remove any existing instances of this path and add it to the beginning
if opencv_path in sys.path:
    sys.path.remove(opencv_path)
sys.path.insert(0, opencv_path)

# Try to import cv2
opencv_installed = False
try:
    # Force reload if already imported
    if 'cv2' in sys.modules:
        del sys.modules['cv2']
    
    import cv2 as cv
    opencv_installed = True
    print(f"OpenCV loaded successfully from: {opencv_path}")
except ImportError as e:
    print(f"Failed to import OpenCV from {opencv_path}")
    print(f"Error: {e}")
    print(f"sys.path includes: {opencv_path in sys.path}")

# Load the campnp module functions
solvepnp = None
camcalib = None
getsceneinfo = None

def load_campnp_module():
    """Load the campnp module and get the necessary functions"""
    global solvepnp, camcalib, getsceneinfo
    
    try:
        campnp = importlib.import_module("GS_Camera_PNP.campnp")
        solvepnp = getattr(campnp, "solvepnp")
        camcalib = getattr(campnp, "camcalib")
        getsceneinfo = getattr(campnp, "getsceneinfo")
        return True
    except (ImportError, AttributeError) as e:
        print(f"Error loading campnp module: {e}")
        return False

# PnP solver classes
class CAMPNP_OT_pose_camera(bpy.types.Operator):
    bl_idname = "campnp.solvepnp"
    bl_label = "Solve camera extrinsics"
    bl_options = {'UNDO'}
    bl_description = "Solve camera extrinsics using available markers and 3D points"
    
    @classmethod
    def poll(cls, context):
        return opencv_installed and context.object and context.object.mode == 'OBJECT'
    
    def execute(self, context):
        if not opencv_installed:
            self.report({'ERROR'}, f'OpenCV is not installed or not found at {opencv_path}')
            return {'CANCELLED'}
            
        if context.object.mode != 'OBJECT':
            self.report({'ERROR'}, 'Please switch to Object Mode')
            return {'CANCELLED'}
            
        return solvepnp(*getsceneinfo(self, context))

class CAMPNP_OT_calibrate_camera(bpy.types.Operator):
    bl_idname = "campnp.camcalib"
    bl_label = "Solve camera intrinsics"
    bl_options = {'UNDO'}
    bl_description = "Solve camera intrinsics using available markers and 3D points"
    
    @classmethod
    def poll(cls, context):
        return opencv_installed and context.object and context.object.mode == 'OBJECT'
    
    def execute(self, context):
        if not opencv_installed:
            self.report({'ERROR'}, f'OpenCV is not installed or not found at {opencv_path}')
            return {'CANCELLED'}
            
        if context.object.mode != 'OBJECT':
            self.report({'ERROR'}, 'Please switch to Object Mode')
            return {'CANCELLED'}
            
        return camcalib(*getsceneinfo(self, context))

class CAMPNP_PT_pnp_panel(bpy.types.Panel):
    bl_label = "Solve PnP"
    bl_idname = "CLIP_PT_PnP_Panel"
    bl_space_type = "CLIP_EDITOR"
    bl_region_type = "UI"
    bl_category = "Solve"

    def draw(self, context):
        layout = self.layout
        
        if not opencv_installed:
            box = layout.box()
            col = box.column()
            col.label(text="OpenCV not found!", icon="ERROR")
            col.label(text=f"Expected path: {opencv_path}")
            col.label(text="Check System Console for details")
            return
        
        col = layout.column(heading="3D Points", align=True)
        col.prop(context.scene, "campnp_points_collection")
        
        col = layout.column(heading="Calibrate", align=True)
        col.prop(context.scene, "campnp_intrinsics_focal_length", text="Focal Length")
        col.prop(context.scene, "campnp_intrinsics_principal_point", text="Optical Center")
        row = col.row(align=True).split(factor=0.22)
        row.prop(context.scene, "campnp_intrinsics_distortion_k1", text="K1")
        row = row.row(align=True).split(factor=0.3)
        row.prop(context.scene, "campnp_intrinsics_distortion_k2", text="K2")
        row.prop(context.scene, "campnp_intrinsics_distortion_k3", text="K3 Distortion")
        
        col = layout.column(align=True)
        col.operator("campnp.camcalib", text="Calibrate Camera")
        
        col = layout.column(align=True)
        col.operator("campnp.solvepnp", text="Solve Camera Pose")
        col.scale_y = 2.0
        
        col = layout.column(align=True)
        col.label(text=context.scene.campnp_msg)

# Class list for registration
classes = [
    CAMPNP_OT_pose_camera,
    CAMPNP_OT_calibrate_camera,
    CAMPNP_PT_pnp_panel
]

def register():
    # Register scene properties
    bpy.types.Scene.campnp_points_collection = bpy.props.PointerProperty(
        name="", 
        type=bpy.types.Collection)
    bpy.types.Scene.campnp_intrinsics_focal_length = bpy.props.BoolProperty(
        name="Focal Length",
        description="Calibrate Focal Length",
        default=True)
    bpy.types.Scene.campnp_intrinsics_principal_point = bpy.props.BoolProperty(
        name="Optical Center",
        description="Calibrate Optical Center",
        default=False)
    bpy.types.Scene.campnp_intrinsics_distortion_k1 = bpy.props.BoolProperty(
        name="Distortion K1",
        description="Calibrate Radial Distortion K1",
        default=False)
    bpy.types.Scene.campnp_intrinsics_distortion_k2 = bpy.props.BoolProperty(
        name="Distortion K2",
        description="Calibrate Radial Distortion K2",
        default=False)
    bpy.types.Scene.campnp_intrinsics_distortion_k3 = bpy.props.BoolProperty(
        name="Distortion K3",
        description="Calibrate Radial Distortion K3",
        default=False)
    bpy.types.Scene.campnp_msg = bpy.props.StringProperty(
        name="Information",
        description="Solver Output Message")
    
    # Load campnp module and register classes if OpenCV is available
    if opencv_installed:
        if load_campnp_module():
            for cls in classes:
                bpy.utils.register_class(cls)
        else:
            print("Failed to load campnp module")
    else:
        # Still register the panel to show error message
        bpy.utils.register_class(CAMPNP_PT_pnp_panel)
        print(f"OpenCV not found at: {opencv_path}")

def unregister():
    # Unregister all classes
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except:
            pass
    
    # Unregister scene properties
    del bpy.types.Scene.campnp_msg
    del bpy.types.Scene.campnp_intrinsics_distortion_k3
    del bpy.types.Scene.campnp_intrinsics_distortion_k2
    del bpy.types.Scene.campnp_intrinsics_distortion_k1
    del bpy.types.Scene.campnp_intrinsics_principal_point
    del bpy.types.Scene.campnp_intrinsics_focal_length
    del bpy.types.Scene.campnp_points_collection

if __name__ == "__main__":
    register()