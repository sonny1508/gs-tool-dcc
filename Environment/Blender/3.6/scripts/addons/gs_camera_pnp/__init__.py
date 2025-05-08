#
#  Copyright (C) 2022 Roger Torm
#  Modified by GS Studios
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

bl_info = {
    "name": "GS Perspective-n-Point",
    "author": "Roger Torm, Modified by GS Studios",
    "license": "GPL",
    "version": (0, 0, 6),
    "blender": (3, 6, 0),
    "location": "Clip Editor > Tools > Solve > Solve PnP",
    "warning": "Requires OpenCV module (pre-installed)",
    "description": "PnP solver for camera calibration and tracking",
    "category": "Camera",
}

import bpy
import os
import sys
import importlib

# Define some helper functions
def get_blender_user_python_dir():
    """Get user's Blender Python directory"""
    # Get the user's scripts directory
    user_scripts = bpy.utils.user_resource('SCRIPTS')
    
    # Create a modules directory in the user's scripts directory
    user_modules = os.path.join(user_scripts, "modules")
    if not os.path.exists(user_modules):
        os.makedirs(user_modules)
    
    return user_modules

# Check if OpenCV is available
def check_opencv_available():
    """Check if OpenCV is available in Blender's Python path"""
    try:
        import cv2
        return True
    except ImportError:
        # Add user modules directory to Python path
        user_modules = get_blender_user_python_dir()
        if user_modules not in sys.path:
            sys.path.append(user_modules)
        
        # Try importing again after adding to path
        try:
            importlib.invalidate_caches()
            import cv2
            return True
        except ImportError:
            return False

# Global variable for OpenCV availability
opencv_available = check_opencv_available()

# PnP solver classes
class GSCAMPNP_OT_pose_camera(bpy.types.Operator):
    bl_idname = "gscampnp.solvepnp"
    bl_label = "Solve camera extrinsics"
    bl_options = {'UNDO'}
    bl_description = "Solve camera extrinsics using available markers and 3D points"
    
    @classmethod
    def poll(cls, context):
        return opencv_available and context.object and context.object.mode == 'OBJECT'
    
    def execute(self, context):
        if not opencv_available:
            self.report({'ERROR'}, 'OpenCV is not installed in the Blender modules directory')
            return {'CANCELLED'}
            
        if context.object.mode != 'OBJECT':
            self.report({'ERROR'}, 'Please switch to Object Mode')
            return {'CANCELLED'}
            
        return solvepnp(*getsceneinfo(self, context))

class GSCAMPNP_OT_calibrate_camera(bpy.types.Operator):
    bl_idname = "gscampnp.camcalib"
    bl_label = "Solve camera intrinsics"
    bl_options = {'UNDO'}
    bl_description = "Solve camera intrinsics using available markers and 3D points"
    
    @classmethod
    def poll(cls, context):
        return opencv_available and context.object and context.object.mode == 'OBJECT'
    
    def execute(self, context):
        if not opencv_available:
            self.report({'ERROR'}, 'OpenCV is not installed in the Blender modules directory')
            return {'CANCELLED'}
            
        if context.object.mode != 'OBJECT':
            self.report({'ERROR'}, 'Please switch to Object Mode')
            return {'CANCELLED'}
            
        return camcalib(*getsceneinfo(self, context))

class GSCAMPNP_PT_pnp_panel(bpy.types.Panel):
    bl_label = "GS Solve PnP"
    bl_idname = "VIEW3D_PT_GSPnP_Panel"
    bl_space_type = "CLIP_EDITOR"
    bl_region_type = "UI"
    bl_category = "Solve"

    def draw(self, context):
        layout = self.layout
        
        if not opencv_available:
            box = layout.box()
            col = box.column()
            col.label(text="OpenCV is not installed in Blender modules directory")
            col.label(text=f"OpenCV should be in {get_blender_user_python_dir()}")
            return
        
        col = layout.column(heading="3D Points", align=True)
        col.prop(context.scene, "gscampnp_points_collection")
        
        col = layout.column(heading="Calibrate", align=True)
        col.prop(context.scene, "gscampnp_intrinsics_focal_length", text="Focal Length")
        col.prop(context.scene, "gscampnp_intrinsics_principal_point", text="Optical Center")
        row = col.row(align=True).split(factor=0.22)
        row.prop(context.scene, "gscampnp_intrinsics_distortion_k1", text="K1")
        row = row.row(align=True).split(factor=0.3)
        row.prop(context.scene, "gscampnp_intrinsics_distortion_k2", text="K2")
        row.prop(context.scene, "gscampnp_intrinsics_distortion_k3", text="K3 Distortion")
        
        col = layout.column(align=True)
        col.operator("gscampnp.camcalib", text="Calibrate Camera")
        
        col = layout.column(align=True)
        col.operator("gscampnp.solvepnp", text="Solve Camera Pose")
        col.scale_y = 2.0
        
        col = layout.column(align=True)
        col.label(text=context.scene.gscampnp_msg)

# Global variables for the module
solvepnp = None
camcalib = None
getsceneinfo = None

def load_campnp_module():
    """Load the campnp module and get the necessary functions"""
    global solvepnp, camcalib, getsceneinfo
    
    try:
        # Use the correct module name with the new folder name
        campnp = importlib.import_module("gs_camera_pnp.campnp")
        solvepnp = getattr(campnp, "solvepnp")
        camcalib = getattr(campnp, "camcalib")
        getsceneinfo = getattr(campnp, "getsceneinfo")
        return True
    except (ImportError, AttributeError) as e:
        print(f"Error loading campnp module: {e}")
        return False

# Class lists for registration
classes = [
    GSCAMPNP_OT_pose_camera,
    GSCAMPNP_OT_calibrate_camera,
    GSCAMPNP_PT_pnp_panel
]

def register():
    # Register scene properties
    bpy.types.Scene.gscampnp_points_collection = bpy.props.PointerProperty(
        name = "", 
        type = bpy.types.Collection)
    bpy.types.Scene.gscampnp_intrinsics_focal_length = bpy.props.BoolProperty(
        name="Focal Length",
        description="Calibrate Focal Length",
        default = True)
    bpy.types.Scene.gscampnp_intrinsics_principal_point = bpy.props.BoolProperty(
        name="Optical Center",
        description="Calibrate Optical Center",
        default = False)
    bpy.types.Scene.gscampnp_intrinsics_distortion_k1 = bpy.props.BoolProperty(
        name="Distortion K1",
        description="Calibrate Radial Distortion K1",
        default = False)
    bpy.types.Scene.gscampnp_intrinsics_distortion_k2 = bpy.props.BoolProperty(
        name="Distortion K2",
        description="Calibrate Radial Distortion K2",
        default = False)
    bpy.types.Scene.gscampnp_intrinsics_distortion_k3 = bpy.props.BoolProperty(
        name="Distortion K3",
        description="Calibrate Radial Distortion K3",
        default = False)
    bpy.types.Scene.gscampnp_msg = bpy.props.StringProperty(
        name="Information",
        description="Solver Output Message")
    
    # If OpenCV is available, load the campnp module and register classes
    if opencv_available:
        if load_campnp_module():
            for cls in classes:
                bpy.utils.register_class(cls)
    else:
        # Register just the panel to show the warning
        bpy.utils.register_class(GSCAMPNP_PT_pnp_panel)

def unregister():
    # Unregister all classes
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except:
            pass
    
    # Unregister scene properties
    del bpy.types.Scene.gscampnp_msg
    del bpy.types.Scene.gscampnp_intrinsics_distortion_k3
    del bpy.types.Scene.gscampnp_intrinsics_distortion_k2
    del bpy.types.Scene.gscampnp_intrinsics_distortion_k1
    del bpy.types.Scene.gscampnp_intrinsics_principal_point
    del bpy.types.Scene.gscampnp_intrinsics_focal_length
    del bpy.types.Scene.gscampnp_points_collection

if __name__ == "__main__":
    register()