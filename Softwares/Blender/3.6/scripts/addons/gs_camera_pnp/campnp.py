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

import bpy
import cv2 as cv
import numpy as np
from mathutils import Matrix, Vector


# getsceneinfo collects information from the movie clip and its camera, 
# as well as 2D points and 3D points from the chosen collection
def getsceneinfo(self, context):
    # get currently loaded movieclip or image
    clip = context.area.spaces.active.clip
    if not clip:
        self.report({'ERROR'}, 'Please load an image in the clip editor')
        return self, context, None, [], [], None, None, (0, 0), 0

    # get picture and camera metrics
    size = clip.size
    clipcam = clip.tracking.camera
    focal = clipcam.focal_length_pixels
    
    # Use center of image as principal point for Blender 3.6 compatibility
    optcent = [0.5, 0.5]
    
    # take radial distortion parameters with safe defaults
    k1, k2, k3 = 0.0, 0.0, 0.0
    try:
        if clipcam.distortion_model == 'POLYNOMIAL':
            k1, k2, k3 = clipcam.k1, clipcam.k2, clipcam.k3
        elif clipcam.distortion_model == 'BROWN':
            k1, k2, k3 = clipcam.brown_k1, clipcam.brown_k2, clipcam.brown_k3
    except AttributeError:
        self.report({'WARNING'}, 'Could not access distortion parameters, using defaults.')

    # get current frame to retrieve marker locations
    fr = bpy.data.scenes[0].frame_current - bpy.data.scenes[0].frame_start

    # get list of tracks and retrieve marker positions at current frame
    points2d = []
    tracks = clip.tracking.tracks
    if not tracks:
        self.report({'ERROR'}, 'Please add markers for the 2D points')
        l2d = 0
    else:
        for track in sorted(tracks, key = lambda o: o.name):
            try:
                points2d.append([track.markers[fr].co[0]*size[0],
                                size[1]-track.markers[fr].co[1]*size[1]])
            except (KeyError, IndexError):
                # Skip markers that don't exist at current frame
                continue
                
        if not points2d:
            self.report({'ERROR'}, 'No valid markers found at the current frame')
            return self, context, clip, [], [], None, None, size, 0
            
        points2d = np.asarray(points2d, dtype='double')
        l2d = len(points2d)

    # retrieve 3D points from scene objects
    points3d = []
    col3d = context.scene.gscampnp_points_collection  # Updated to use new property name
    if col3d is None:
        self.report({'ERROR'}, 'Please specify a collection for the 3D points')
        l3d = 0
    else: 
        for point in sorted(col3d.all_objects, key = lambda o: o.name):
            points3d.append(point.location)
        
        if not points3d:
            self.report({'ERROR'}, 'No 3D points found in the specified collection')
            return self, context, clip, [], [], None, None, size, 0
            
        points3d = np.asarray(points3d, dtype='double')
        l3d = len(points3d)

    # check point list length compatibility
    npoints = l2d
    if l2d > l3d: 
        points2d = points2d[:l3d,:]
        self.report({'WARNING'}, f'Ignoring extra 2D points ({l2d} 2D points, {l3d} 3D points)')
        npoints = l3d
    elif l2d < l3d: 
        points3d = points3d[:l2d,:]
        self.report({'WARNING'}, f'Ignoring extra 3D points ({l2d} 2D points, {l3d} 3D points)')

    # construct camera intrinsics
    # Principal point in pixel coordinates
    cx = optcent[0] * size[0]
    cy = size[1] - (optcent[1] * size[1])
    
    camintr = np.array([
        [focal, 0, cx],
        [0, focal, cy],
        [0, 0, 1]
    ], dtype='double')

    # construct distortion vector, only k1,k2,k3 (polynomial or brown models)
    distcoef = np.array([k1, k2, 0, 0, k3])
    
    return self, context, clip, points3d, points2d, camintr, distcoef, size, npoints


# main PnP solver function
def solvepnp(self, context, clip, points3d, points2d, camintr, distcoef, size, npoints):
    if clip is None:
        return {'CANCELLED'}
        
    if npoints < 4:
        self.report({'ERROR'}, 'Not enough point pairs, use at least 4 markers to solve a camera pose.')
        return {'CANCELLED'}
    
    # solve Perspective-n-Point
    try:
        ret, rvec, tvec, error = cv.solvePnPGeneric(points3d, points2d, camintr, distcoef, flags=cv.SOLVEPNP_SQPNP)
    except Exception as e:
        self.report({'ERROR'}, f'OpenCV error: {str(e)}')
        return {'CANCELLED'}
    
    if not ret or len(rvec) == 0:
        self.report({'ERROR'}, 'solvePnP failed! Check your 2D-3D point correspondences.')
        return {'CANCELLED'}
        
    rmat, _ = cv.Rodrigues(rvec[0])
    context.scene.gscampnp_msg = ("Reprojection Error: %.2f" %error) if ret else "solvePnP failed!"  # Updated to use new property name

    # get R and T matrices
    # https://blender.stackexchange.com/questions/38009/3x4-camera-matrix-from-blender-camera
    R_world2cv = Matrix(rmat.tolist()) 
    T_world2cv = Vector(tvec[0]) 

    # blender camera to opencv camera coordinate conversion 
    R_bcam2cv = Matrix(
        ((1, 0, 0),
         (0, -1, 0),
         (0, 0, -1)))

    # calculate transform in world coordinates
    R_cv2world = R_world2cv.transposed()
    rot = R_cv2world @ R_bcam2cv
    loc =  -1 * R_cv2world @ T_world2cv

    # Create new camera or use existing
    # check if active object is a camera, if so, assume user wants to set it up, otherwise create a new camera
    if context.active_object == None or context.active_object.type != 'CAMERA': # add a new one
        bpy.ops.object.add(type='CAMERA')
        bpy.context.object.name = clip.name 

    # Set camera intrinsics, extrinsics and background
    cam = context.object
    camd = cam.data
    camd.type = 'PERSP'
    camd.lens = clip.tracking.camera.focal_length
    camd.sensor_width = clip.tracking.camera.sensor_width
    camd.sensor_height = clip.tracking.camera.sensor_width*size[1]/size[0]
    render_size = [context.scene.render.pixel_aspect_x * context.scene.render.resolution_x,
                    context.scene.render.pixel_aspect_y * context.scene.render.resolution_y]
    camd.sensor_fit = 'HORIZONTAL' if render_size[0]/render_size[1] <= size[0]/size[1] else 'VERTICAL'
    
    # Using fixed principal point (center of image)
    optcent = [0.5, 0.5]
    
    refsize = size[0] if render_size[0]/render_size[1] <= size[0]/size[1] else size[1]
    camd.shift_x = (size[0]*0.5 - optcent[0]*size[0])/refsize
    camd.shift_y = (size[1]*0.5 - optcent[1]*size[1])/refsize
    
    camd.show_background_images = True
    if not camd.background_images: 
        bg = camd.background_images.new()
    else: 
        bg = camd.background_images[0]
    
    bg.source = 'MOVIE_CLIP'
    bg.clip = clip
    bg.frame_method = 'FIT' 
    bg.display_depth = 'FRONT'
    
    # Check for use_render_undistorted attribute
    try:
        bg.clip_user.use_render_undistorted = True
    except AttributeError:
        # Attribute might not exist in newer Blender versions
        pass
    
    cam.matrix_world = Matrix.Translation(loc) @ rot.to_4x4()
    context.scene.camera = cam
    
    return {'FINISHED'}


# main Calibration solver function
def camcalib(self, context, clip, points3d, points2d, camintr, distcoef, size, npoints):   
    if clip is None:
        return {'CANCELLED'}
        
    if npoints < 6:
        self.report({'ERROR'}, 'Not enough point pairs, use at least 6 markers to calibrate a camera.')
        return {'CANCELLED'}

    flags = (cv.CALIB_USE_INTRINSIC_GUESS + cv.CALIB_FIX_ASPECT_RATIO + cv.CALIB_ZERO_TANGENT_DIST
            + (cv.CALIB_FIX_PRINCIPAL_POINT if not context.scene.gscampnp_intrinsics_principal_point else 0)  # Updated to use new property name
            + (cv.CALIB_FIX_FOCAL_LENGTH if not context.scene.gscampnp_intrinsics_focal_length else 0)  # Updated to use new property name
            + (cv.CALIB_FIX_K1 if not context.scene.gscampnp_intrinsics_distortion_k1 else 0)  # Updated to use new property name
            + (cv.CALIB_FIX_K2 if not context.scene.gscampnp_intrinsics_distortion_k2 else 0)  # Updated to use new property name
            + (cv.CALIB_FIX_K3 if not context.scene.gscampnp_intrinsics_distortion_k3 else 0))  # Updated to use new property name
    
    try:
        ret, camintr, distcoef, _, _ = cv.calibrateCamera(
            np.asarray([points3d], dtype='float32'), 
            np.asarray([points2d], dtype='float32'), 
            size, 
            camintr, distcoef,
            flags = flags
        )
    except Exception as e:
        self.report({'ERROR'}, f'OpenCV error: {str(e)}')
        return {'CANCELLED'}
                                                    
    context.scene.gscampnp_msg = ("Reprojection Error: %.2f" %ret)  # Updated to use new property name
    
    # set picture and camera metrics
    if context.scene.gscampnp_intrinsics_focal_length:  # Updated to use new property name
        clip.tracking.camera.focal_length_pixels = camintr[0][0] 
    
    # Update distortion parameters if supported by this Blender version
    if (context.scene.gscampnp_intrinsics_distortion_k1 or  # Updated to use new property name
        context.scene.gscampnp_intrinsics_distortion_k2 or  # Updated to use new property name
        context.scene.gscampnp_intrinsics_distortion_k3):  # Updated to use new property name
        try:
            # Try to set distortion parameters if they exist
            if hasattr(clip.tracking.camera, 'k1'):
                clip.tracking.camera.k1 = distcoef[0]
            if hasattr(clip.tracking.camera, 'k2'):
                clip.tracking.camera.k2 = distcoef[1]
            if hasattr(clip.tracking.camera, 'k3'):
                clip.tracking.camera.k3 = distcoef[4]
            
            # Also try to set brown model parameters if they exist
            if hasattr(clip.tracking.camera, 'brown_k1'):
                clip.tracking.camera.brown_k1 = distcoef[0]
            if hasattr(clip.tracking.camera, 'brown_k2'):
                clip.tracking.camera.brown_k2 = distcoef[1]
            if hasattr(clip.tracking.camera, 'brown_k3'):
                clip.tracking.camera.brown_k3 = distcoef[4]
        except AttributeError:
            self.report({'WARNING'}, 'Could not update all distortion parameters due to version differences')

    return {'FINISHED'}