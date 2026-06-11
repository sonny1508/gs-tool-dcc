"""
Maya Cable Tool - Python 3 Compatible Version (Maya 2022+ Fixed)
A comprehensive tool for creating and managing cables in Maya using Paint Effects
"""

import maya.cmds as mc
import maya.mel as mel
import os
import sys

# ============================================================================
# INITIALIZATION
# ============================================================================

class CableTool:
    """Main Cable Tool class for organizing all functionality"""
    
    def __init__(self):
        self.window_name = "Cable_2_52"  # Changed from "Cable 3.0" to avoid spaces
        self.version = mc.about(v=True)
        self.os_type = mc.about(os=True)
        self.setup_tool()
    
    def setup_tool(self):
        """Initialize the cable tool with proper settings"""
        # Clear any existing error messages
        mc.warning()
        print("")
        
        # Delete existing UI if it exists
        if mc.window(self.window_name, exists=True):
            mc.deleteUI(self.window_name)
        
        if mc.workspaceControl(self.window_name, exists=True):
            mc.deleteUI(self.window_name)
        
        # Set correct brush based on OS
        self._setup_brush()
        
        # Configure default tube settings
        self._setup_default_settings()
        
        # Create the UI
        self._create_ui()
    
    def _setup_brush(self):
        """Configure the appropriate brush for the current OS"""
        if self.os_type == 'win64':
            mel.eval('string $maya = `getenv maya_location`;')
            mel.eval('$s="/Examples/Paint_Effects/Trees/birchLimb.mel";')
            mel.eval('$total= $maya+$s;')
            mel.eval('visorPanelBrushPressCallback files1VisorEd $total;')
            mel.eval('setToolTo $gMove;')
        elif self.os_type == 'linux64':
            print("For Linux users: Configure your path directly in the script.")
            print("If you need help with Maya scripting, ask on Discord.")
    
    def _setup_default_settings(self):
        """Set default settings for the tube"""
        try:
            mc.setAttr("birchLimb.globalScale", 10)
            mc.setAttr("birchLimb.brushWidth", 0.1)
            mc.setAttr("birchLimb.forwardTwist", 0)
            mc.setAttr("birchLimb.color1", 0, 0.149078, 0.228, type='double3')
            mc.setAttr("birchLimb.specularColor", 0, 0, 0, type='double3')
            mc.setAttr("birchLimb.tubeSections", 8)
        except:
            print("Warning: Could not set default brush settings. Brush may not be loaded.")

# ============================================================================
# USER INTERFACE
# ============================================================================

def create_custom_workspace_control(*args):
    """Create the main UI for the cable tool with scrollable layout"""
    # Create main scroll layout for the entire UI
    scroll_layout = mc.scrollLayout(
        childResizable=True,
        horizontalScrollBarThickness=0,
        verticalScrollBarThickness=16
    )
    
    mc.columnLayout(adj=True, w=300, h=600)
    
    # CREATE SECTION
    _create_section()
    
    # EDIT SECTION  
    _create_edit_section()
    
    # DYNAMICS SECTION
    _create_dynamics_section()
    
    # CONVERT SECTION
    _create_convert_section()
    
    mc.setParent('..')  # Exit columnLayout
    mc.setParent('..')  # Exit scrollLayout

def _create_section():
    """Create the CREATE section of the UI"""
    frame_create = mc.frameLayout(
        l="CREATE", 
        cll=1, 
        cl=0, 
        bgc=[0.15, 0.15, 0.15], 
        font='boldLabelFont'
    )
    
    # Tool buttons row
    mc.rowColumnLayout(numberOfRows=1)
    mc.separator(w=18, style='none')
    
    # Curve creation tools
    tool_cv = mc.symbolButton(
        image='curveEP.png', 
        c=lambda *args: mc.EPCurveTool(), 
        ann="EP Curve"
    )
    mc.separator(w=40, style='none')
    
    tool_bezier = mc.symbolButton(
        image='curveBezier.png', 
        c=lambda *args: mc.CreateBezierCurveTool(), 
        ann="Bezier Curve"
    )
    mc.separator(w=40, style='none')
    
    tool_pen = mc.symbolButton(
        image='pencil.png', 
        c=lambda *args: mc.PencilCurveTool(), 
        ann="Pencil Curve"
    )
    mc.separator(w=40, style='none')
    
    tool_edge = mc.symbolButton(
        image='polyEdgeToCurves.png', 
        c=lambda *args: edge_to_curve(), 
        ann="Create Curve from Edge"
    )
    mc.setParent('..')
    
    # Create cables button
    mc.rowColumnLayout(numberOfRows=1)
    mc.separator(w=2, style='none')
    
    button_create = mc.button(
        'buttonCreate',
        w=290,
        l="- Create Cables -",
        c=lambda *args: attach_cable(),
        ann="Create cables",
        bgc=[0.22, 0.22, 0.22]
    )
    mc.setParent('..')
    
    mc.setParent('..')  # Exit frame

def _create_edit_section():
    """Create the EDIT section of the UI"""
    frame_edit = mc.frameLayout(
        l="EDIT", 
        cll=1, 
        cl=0, 
        bgc=[0.15, 0.15, 0.15]
    )
    
    mc.separator(h=1, style='none')
    
    # Manipulation checkbox
    mc.checkBoxGrp(
        'Check_Manip',
        l="Manipulation",
        onc=lambda *args: toggle_manipulation(True),
        ofc=lambda *args: toggle_manipulation(False),
        adj=0,
        cat=[1, "left", 1],
        cw=[1, 80],
        v1=0,
        ann="Easier to manipulate curves"
    )
    
    mc.separator(w=1, style='in')
    
    # Parameter sliders
    _create_parameter_sliders()
    
    # Advanced parameters
    _create_advanced_parameters()
    
    mc.setParent('..')

def _create_parameter_sliders():
    """Create the main parameter sliders"""
    sliders_config = [
        ('Slider_Scale', 'Scale', 0.1, 100, 100, lambda *args: update_scale(), "Configure to scene set in cm"),
        ('Slider_Width', 'Width', 0.001, 2, 0.1, lambda *args: update_width(), "Cable width"),
        ('Slider_Density', 'Density', 0.1, 5, 1, lambda *args: update_density(), "Sample density"),
        ('Slider_Section', 'Section', 3, 12, 8, lambda *args: update_section(), "Tube sections"),
        ('Slider_Smoothing', 'Smoothing', 0, 100, 0, lambda *args: update_smoothing(), "Curve smoothing")
    ]
    
    for slider_id, label, min_val, max_val, default_val, callback, annotation in sliders_config:
        if 'Section' in slider_id:
            mc.intSliderGrp(
                slider_id,
                l=label,
                min=min_val,
                max=max_val,
                po=True,
                field=True,
                cc=callback,
                dc=callback,
                v=default_val,
                adj=0,
                cat=[1, "left", 3],
                cw=[1, 60],
                ann=annotation
            )
        else:
            precision = 3 if 'Width' in slider_id else 1
            mc.floatSliderGrp(
                slider_id,
                l=label,
                min=min_val,
                max=max_val,
                po=True,
                field=True,
                cc=callback,
                dc=callback,
                v=default_val,
                pre=precision,
                adj=0,
                cat=[1, "left", 3],
                cw=[1, 60],
                ann=annotation
            )

def _create_advanced_parameters():
    """Create advanced parameter controls"""
    frame_advanced = mc.frameLayout(
        l="ADVANCE", 
        cll=1, 
        cl=1, 
        bgc=[0.15, 0.15, 0.15]
    )
    
    mc.separator(h=1, style='none')
    
    # Twist controls
    mc.checkBox(
        'Check_Twist',
        l="Twist",
        onc=lambda *args: toggle_twist(True),
        ofc=lambda *args: toggle_twist(False)
    )
    
    mc.floatSliderGrp(
        'Slider_Twist',
        l="Twist Rate",
        min=0,
        max=300,
        po=True,
        field=True,
        cc=lambda *args: update_twist(),
        dc=lambda *args: update_twist(),
        v=0,
        adj=0,
        cat=[1, "left", 3],
        cw=[1, 60]
    )
    
    mc.separator(w=1, style='in')
    
    # Additional advanced sliders
    advanced_sliders = [
        ('Slider_Flat', 'Flatness', 0, 1, 0, lambda *args: update_flatness()),
        ('Slider_Pstart', 'Pressure A', 0, 1, 1, lambda *args: update_pressure_start()),
        ('Slider_Pend', 'Pressure B', 0, 1, 1, lambda *args: update_pressure_end())
    ]
    
    for slider_id, label, min_val, max_val, default_val, callback in advanced_sliders:
        mc.floatSliderGrp(
            slider_id,
            l=label,
            min=min_val,
            max=max_val,
            po=True,
            field=True,
            cc=callback,
            dc=callback,
            pre=3,
            v=default_val,
            adj=0,
            cat=[1, "left", 3],
            cw=[1, 60]
        )
    
    mc.separator(h=1, style='none')
    mc.setParent('..')

def _create_dynamics_section():
    """Create the DYNAMICS section"""
    frame_dynamics = mc.frameLayout(
        l="DYNAMICS", 
        cll=1, 
        cl=1, 
        bgc=[0.15, 0.15, 0.15]
    )
    
    # Rebuild span slider
    mc.intSliderGrp(
        'Slider_Rebuild',
        l="Rebuild Span",
        min=1,
        max=100,
        po=True,
        field=True,
        cc=lambda *args: update_rebuild(),
        dc=lambda *args: update_rebuild(),
        v=25,
        adj=0,
        cat=[1, "left", 3],
        cw=[1, 80]
    )
    
    # Dynamic buttons
    mc.button(
        'buttonDyn',
        w=290,
        l="- Make Dynamic -",
        c=lambda *args: make_dynamic(),
        ann="Create Dynamic on Cable",
        bgc=[0.22, 0.22, 0.22]
    )
    
    mc.button(
        'buttonCollide',
        w=290,
        l="- Make Collide -",
        c=lambda *args: make_collide(),
        ann="Make Mesh Collider",
        bgc=[0.22, 0.22, 0.22]
    )
    
    mc.separator(w=1, style='in')
    mc.text("- Properties (Affect All) -")
    
    # Offset controls
    mc.rowColumnLayout(numberOfColumns=2, columnWidth=[(1, 100), (2, 250)])
    
    mc.checkBoxGrp(
        'CB_Offset',
        l="Offset Preview",
        onc=lambda *args: toggle_offset_preview(True),
        ofc=lambda *args: toggle_offset_preview(False),
        adj=0,
        cat=[1, "left", 3],
        cw=[1, 80]
    )
    
    mc.floatSliderGrp(
        'Slider_Offset',
        min=0,
        max=10,
        po=True,
        field=True,
        cc=lambda *args: update_offset(),
        dc=lambda *args: update_offset(),
        v=1,
        adj=0,
        cat=[1, "left", 3],
        cw=[1, 80],
        ann="Control the radius of collider"
    )
    mc.setParent('..')
    
    # Dynamic property sliders
    _create_dynamic_property_sliders()
    
    # Point lock buttons
    _create_point_lock_buttons()
    
    mc.setParent('..')

def _create_dynamic_property_sliders():
    """Create dynamic property sliders"""
    dynamic_sliders = [
        ('Slider_Friction', 'Friction', 0, 1, 0.5, lambda *args: update_friction()),
        ('Slider_Stretch', 'Stretch', 0, 100, 10, lambda *args: update_stretch()),
        ('Slider_StartCurve', 'Start Curve', 0, 1, 0, lambda *args: update_start_curve()),
        ('Slider_MotionDrag', 'Motion Drag', 0, 1, 0, lambda *args: update_motion_drag())
    ]
    
    for slider_id, label, min_val, max_val, default_val, callback in dynamic_sliders:
        mc.floatSliderGrp(
            slider_id,
            l=label,
            min=min_val,
            max=max_val,
            po=True,
            field=True,
            cc=callback,
            dc=callback,
            v=default_val,
            adj=0,
            cat=[1, "left", 3],
            cw=[1, 80],
            ann=f"{label} Parameter"
        )

def _create_point_lock_buttons():
    """Create point lock control buttons"""
    mc.separator(w=1, style='in')
    
    mc.rowColumnLayout(
        numberOfColumns=4,
        columnWidth=[(1, 70), (2, 70), (3, 70), (4, 70)]
    )
    
    point_lock_buttons = [
        ('buttonPlNo', 'No Attach', lambda *args: set_point_lock(0)),
        ('buttonPlBase', 'Base', lambda *args: set_point_lock(1)),
        ('buttonPlTip', 'Tip', lambda *args: set_point_lock(2)),
        ('buttonPlBoth', 'Both', lambda *args: set_point_lock(3))
    ]
    
    for button_id, label, callback in point_lock_buttons:
        mc.button(
            button_id,
            w=70,
            l=label,
            c=callback,
            ann=f"Point Lock {label}",
            bgc=[0.22, 0.22, 0.22]
        )
    
    mc.setParent('..')

def _create_convert_section():
    """Create the CONVERT section"""
    frame_convert = mc.frameLayout(
        l="CONVERT", 
        cll=1, 
        cl=1, 
        bgc=[0.15, 0.15, 0.15]
    )
    
    # Bake buttons row
    mc.rowColumnLayout(numberOfRows=1)
    
    bake_buttons = [
        ('buttonBakeHistory', 'Bake + History', lambda *args: bake_with_history()),
        ('buttonBake', 'BAKE', lambda *args: bake_clean()),
        ('buttonBakeCurve', 'Bake + Curve', lambda *args: bake_with_curve())
    ]
    
    for i, (button_id, label, callback) in enumerate(bake_buttons):
        if i > 0:
            mc.separator(w=4, style='none')
        
        mc.button(
            button_id,
            w=95,
            l=label,
            c=callback,
            ann=f"Convert to Mesh - {label}",
            bgc=[0.22, 0.22, 0.22]
        )
    
    mc.setParent('..')
    
    # Additional conversion buttons
    mc.rowColumnLayout(numberOfRows=1)
    mc.button(
        'buttonCleanDyn',
        w=290,
        l="Clean Dynamic Nodes",
        c=lambda *args: clean_dynamic_nodes(),
        ann="Be sure to Bake your Cables first",
        bgc=[0.22, 0.22, 0.22]
    )
    mc.setParent('..')
    
    mc.button(
        'buttonBackToCurve',
        w=290,
        l="Back to Curve",
        c=lambda *args: back_to_curve(),
        ann="Rebuild curve based on Geo",
        bgc=[0.22, 0.22, 0.22]
    )
    
    mc.setParent('..')

# ============================================================================
# CORE FUNCTIONALITY
# ============================================================================

def attach_cable():
    """Create cables from selected curves"""
    try:
        # Ensure we have curves selected
        selection = mc.ls(sl=True, type=['nurbsCurve', 'transform'])
        if not selection:
            mc.warning("Please select at least one curve to create cables.")
            return
        
        # Execute paint effects attachment
        mel.eval('AttachBrushToCurves')
        mel.eval('convertCurvesToStrokes')
        mel.eval('setToolTo $gMove;')
        
        # Wait a moment for the strokes to be created
        mc.refresh()
        
        # Get the newly created strokes and assign lambert1 to any associated geometry
        strokes = mc.ls(type='stroke')
        for stroke in strokes:
            try:
                # Get the transform node
                transform = mc.listRelatives(stroke, parent=True, type='transform')
                if transform:
                    # Try to assign lambert1 to the transform
                    mc.select(transform[0])
                    try:
                        mc.sets(transform[0], edit=True, forceElement='initialShadingGroup')
                    except:
                        pass
            except:
                continue
        
        print("Cables created successfully!")
        
    except Exception as e:
        print(f"Error creating cables: {e}")
        mc.warning("Failed to create cables. Make sure curves are selected and brush is loaded.")

def edge_to_curve():
    """Convert selected edges to curves"""
    try:
        mc.polyToCurve(form=3, degree=1, conformToSmoothMeshPreview=1)
    except Exception as e:
        print(f"Error converting edge to curve: {e}")

# ============================================================================
# PARAMETER UPDATE FUNCTIONS
# ============================================================================

def get_selected_strokes():
    """Get currently selected stroke objects"""
    return mc.ls(sl=True, fl=True, dag=True, type='stroke')

def get_connected_brushes(strokes):
    """Get brush nodes connected to stroke objects"""
    if not strokes:
        return []
    return mc.listConnections(strokes, d=True, scn=True, type='brush')

def update_scale():
    """Update the global scale of selected cables"""
    value = mc.floatSliderGrp("Slider_Scale", q=True, value=True)
    strokes = get_selected_strokes()
    brushes = get_connected_brushes(strokes)
    
    for brush in brushes or []:
        try:
            mc.setAttr(f"{brush}.globalScale", value)
        except:
            pass

def update_width():
    """Update the width of selected cables"""
    value = mc.floatSliderGrp("Slider_Width", q=True, value=True)
    strokes = get_selected_strokes()
    brushes = get_connected_brushes(strokes)
    
    for brush in brushes or []:
        try:
            mc.setAttr(f"{brush}.brushWidth", value)
        except:
            pass

def update_density():
    """Update the sample density of selected cables"""
    value = mc.floatSliderGrp("Slider_Density", q=True, value=True)
    strokes = get_selected_strokes()
    
    for stroke in strokes:
        try:
            mc.setAttr(f"{stroke}.sampleDensity", value)
        except:
            pass

def update_section():
    """Update the tube sections of selected cables"""
    value = mc.intSliderGrp("Slider_Section", q=True, value=True)
    strokes = get_selected_strokes()
    brushes = get_connected_brushes(strokes)
    
    for brush in brushes or []:
        try:
            mc.setAttr(f"{brush}.tubeSections", value)
        except:
            pass

def update_smoothing():
    """Update the smoothing of selected cables"""
    value = mc.floatSliderGrp("Slider_Smoothing", q=True, value=True)
    strokes = get_selected_strokes()
    
    for stroke in strokes:
        try:
            mc.setAttr(f"{stroke}.smoothing", value)
        except:
            pass

def update_twist():
    """Update the twist rate of selected cables"""
    value = mc.floatSliderGrp("Slider_Twist", q=True, value=True)
    strokes = get_selected_strokes()
    brushes = get_connected_brushes(strokes)
    
    for brush in brushes or []:
        try:
            mc.setAttr(f"{brush}.twistRate", value)
        except:
            pass

def update_flatness():
    """Update the flatness of selected cables"""
    value = mc.floatSliderGrp("Slider_Flat", q=True, value=True)
    strokes = get_selected_strokes()
    brushes = get_connected_brushes(strokes)
    
    for brush in brushes or []:
        try:
            mc.setAttr(f"{brush}.flatness1", value)
        except:
            pass

def update_pressure_start():
    """Update the start pressure of selected cables"""
    value = mc.floatSliderGrp("Slider_Pstart", q=True, value=True)
    strokes = get_selected_strokes()
    
    for stroke in strokes:
        try:
            mc.setAttr(f"{stroke}.pressureScale[0].pressureScale_FloatValue", value)
        except:
            pass

def update_pressure_end():
    """Update the end pressure of selected cables"""
    value = mc.floatSliderGrp("Slider_Pend", q=True, value=True)
    strokes = get_selected_strokes()
    
    for stroke in strokes:
        try:
            mc.setAttr(f"{stroke}.pressureScale[1].pressureScale_FloatValue", value)
            mc.setAttr(f"{stroke}.pressureScale[1].pressureScale_Position", 1)
        except:
            pass

# ============================================================================
# TOGGLE FUNCTIONS
# ============================================================================

def toggle_manipulation(enable):
    """Toggle manipulation mode for easier curve editing"""
    strokes = mc.ls(typ='stroke', ni=True, o=True, r=True)
    
    for stroke in strokes:
        try:
            mc.setAttr(f"{stroke}.overrideEnabled", 1 if enable else 0)
            if enable:
                mc.setAttr(f"{stroke}.overrideDisplayType", 2)
        except:
            pass
    
    if not enable:
        mc.select(d=True)

def toggle_twist(enable):
    """Toggle twist on/off for selected cables"""
    value = 0 if enable else 1
    strokes = get_selected_strokes()
    brushes = get_connected_brushes(strokes)
    
    for brush in brushes or []:
        try:
            mc.setAttr(f"{brush}.forwardTwist", value)
        except:
            pass

def toggle_offset_preview(enable):
    """Toggle offset preview for dynamics"""
    try:
        if mc.objExists("hairSystem1"):
            mc.setAttr("hairSystem1.solverDisplay", 1 if enable else 0)
    except:
        pass

def toggle_displacement():
    """Toggle displacement in viewport"""
    try:
        mc.toggleDisplacement()
    except:
        pass

# ============================================================================
# DYNAMICS FUNCTIONS
# ============================================================================

def make_dynamic():
    """Make selected curves dynamic"""
    try:
        # Set playback speed and evaluation mode
        mc.playbackOptions(ps=1)
        
        version = mc.about(v=True)
        if version != "2018":
            mc.evaluationManager(mode="off")
        
        # Create temporary set
        mc.sets(n="Settemps")
        
        # Convert Bezier curves
        mc.bezierCurveToNurbs()
        
        # Rebuild curves
        selection = mc.ls(sl=True, fl=True, dag=True)
        rebuild_value = mc.intSliderGrp("Slider_Rebuild", q=True, v=True)
        
        for obj in selection:
            mc.select(obj)
            mc.rebuildCurve(
                ch=0, rpo=1, rt=0, end=1, kr=0, 
                kcp=0, kep=1, kt=0, s=rebuild_value, 
                d=3, tol=0.01
            )
        
        # Make curves dynamic
        if mc.objExists('hairSystem1'):
            mc.select("Settemps", "hairSystem1")
            mc.delete("Settemps")
            mel.eval('makeCurvesDynamic 2 { "1", "0", "1", "1", "0"};')
        else:
            mc.select("Settemps")
            mc.delete("Settemps")
            mel.eval('makeCurvesDynamic 2 { "1", "0", "1", "1", "0"};')
            
            # Set default dynamic properties
            if mc.objExists("nucleus1"):
                mc.setAttr("nucleus1.spaceScale", 0.01)
            if mc.objExists("hairSystem1"):
                mc.setAttr("hairSystem1.collideWidthOffset", 1)
            if mc.objExists("hairSystem1Follicles"):
                mc.setAttr("hairSystem1Follicles.visibility", 0, l=True)
                
    except Exception as e:
        print(f"Error making dynamic: {e}")

def make_collide():
    """Make selected meshes colliders"""
    try:
        selection = mc.ls(sl=True, fl=True, dag=True, type="mesh")
        for mesh in selection:
            mel.eval("makeCollideNCloth;")
    except Exception as e:
        print(f"Error making collider: {e}")

def set_point_lock(lock_type):
    """Set point lock for all follicles"""
    try:
        follicles = mc.ls(type="follicle")
        for follicle in follicles:
            mc.setAttr(f"{follicle}.pointLock", lock_type)
    except Exception as e:
        print(f"Error setting point lock: {e}")

# Dynamic property update functions
def update_offset():
    """Update collision offset"""
    try:
        value = mc.floatSliderGrp("Slider_Offset", q=True, value=True)
        if mc.objExists("hairSystem1"):
            mc.setAttr("hairSystem1.collideWidthOffset", value)
    except:
        pass

def update_friction():
    """Update friction property"""
    try:
        value = mc.floatSliderGrp("Slider_Friction", q=True, value=True)
        if mc.objExists("hairSystem1"):
            mc.setAttr("hairSystem1.friction", value)
    except:
        pass

def update_stretch():
    """Update stretch resistance"""
    try:
        value = mc.floatSliderGrp("Slider_Stretch", q=True, value=True)
        if mc.objExists("hairSystem1"):
            mc.setAttr("hairSystem1.stretchResistance", value)
    except:
        pass

def update_start_curve():
    """Update start curve attract"""
    try:
        value = mc.floatSliderGrp("Slider_StartCurve", q=True, value=True)
        if mc.objExists("hairSystem1"):
            mc.setAttr("hairSystem1.startCurveAttract", value)
    except:
        pass

def update_motion_drag():
    """Update motion drag"""
    try:
        value = mc.floatSliderGrp("Slider_MotionDrag", q=True, value=True)
        if mc.objExists("hairSystem1"):
            mc.setAttr("hairSystem1.motionDrag", value)
    except:
        pass

def update_rebuild():
    """Update rebuild span (placeholder for UI consistency)"""
    pass

# ============================================================================
# BAKING FUNCTIONS (FIXED)
# ============================================================================

def bake_with_history():
    """Convert paint effects to polygons keeping history - FIXED VERSION"""
    selection = mc.ls(sl=True, fl=True, dag=True, type='stroke')
    
    if not selection:
        mc.warning("Please select stroke objects to bake.")
        return
    
    for stroke in selection:
        try:
            mc.select(stroke)
            
            # Get connected objects before conversion
            sel1 = mc.ls(sl=True, fl=True, dag=True)
            sel2 = mc.listConnections(sel1) or []
            sel3 = mc.listConnections(sel1, type='transform') or []
            
            # Convert to polygon
            mel.eval('doPaintEffectsToPoly(1,0,1,1,100000);')
            mel.eval('polyMultiLayoutUV -lm 1 -sc 1 -rbf 0 -fr 1 -ps 0.05 -l 2 -gu 1 -gv 1 -psc 1 -su 1 -sv 1 -ou 0 -ov 0;')
            
            mc.delete(ch=True)
            mc.parent(w=True)
            
            # Clean up old objects
            sel4 = mc.ls("birchLimb*MeshGroup") or []
            
            # Delete old objects safely
            objects_to_delete = []
            if sel1:
                objects_to_delete.extend([obj for obj in sel1 if mc.objExists(obj)])
            if sel2:
                objects_to_delete.extend([obj for obj in sel2 if mc.objExists(obj)])
            if sel3:
                objects_to_delete.extend([obj for obj in sel3 if mc.objExists(obj)])
            if sel4:
                objects_to_delete.extend([obj for obj in sel4 if mc.objExists(obj)])
            
            for obj in objects_to_delete:
                try:
                    mc.delete(obj)
                except:
                    pass
            
            mc.CenterPivot()
            mc.hyperShade(a="lambert1")
            
            # Rename created objects
            selected_objects = mc.ls("birchLimb*MeshGroup") or mc.ls(selection=True)
            newname = "Cable_Hist_"
            for number, obj in enumerate(selected_objects):
                if mc.objExists(obj):
                    print(f'Old Name: {obj}')
                    new_name = f'{newname}{number:02d}'
                    print(f'New Name: {new_name}')
                    try:
                        mc.rename(obj, new_name)
                    except:
                        pass
        
        except Exception as e:
            print(f"Error baking stroke {stroke}: {e}")
            continue
    
    print("Bake with history completed")

def bake_clean():
    """Convert paint effects to polygons and clean up all history - FIXED VERSION"""
    selection = mc.ls(sl=True, fl=True, dag=True, type='stroke')
    
    if not selection:
        mc.warning("Please select stroke objects to bake.")
        return
    
    for stroke in selection:
        try:
            mc.select(stroke)
            
            # Get connected objects before conversion
            sel1 = mc.ls(sl=True, fl=True, dag=True)
            sel2 = mc.listConnections(sel1) or []
            sel_all = sel1 + sel2
            
            # Convert to polygon
            mel.eval('doPaintEffectsToPoly(1,0,1,1,100000);')
            mel.eval('polyMultiLayoutUV -lm 1 -sc 1 -rbf 0 -fr 1 -ps 0.05 -l 2 -gu 1 -gv 1 -psc 1 -su 1 -sv 1 -ou 0 -ov 0;')
            
            mc.delete(ch=True)  # Delete history
            mc.parent(w=True)   # Parent to world
            
            sel4 = mc.ls("birchLimb*MeshGroup") or []
            
            # Delete old objects safely
            for obj in sel_all:
                if mc.objExists(obj):
                    try:
                        mc.delete(obj)
                    except:
                        pass
            
            if sel4:
                for obj in sel4:
                    if mc.objExists(obj):
                        try:
                            mc.delete(obj)
                        except:
                            pass
            
            mc.CenterPivot()
            mc.hyperShade(a="lambert1")
            
            # Rename created objects
            selected_objects = mc.ls(selection=True)
            newname = "Cable_"
            for number, obj in enumerate(selected_objects):
                if mc.objExists(obj):
                    print(f'Old Name: {obj}')
                    new_name = f'{newname}{number:02d}'
                    print(f'New Name: {new_name}')
                    try:
                        mc.rename(obj, new_name)
                    except:
                        pass
                        
        except Exception as e:
            print(f"Error baking stroke {stroke}: {e}")
            continue
    
    print("Clean bake completed")

def bake_with_curve():
    """Convert paint effects to polygons but keep original curves - FIXED VERSION"""
    selection = mc.ls(sl=True, fl=True, dag=True, type='stroke')
    
    if not selection:
        mc.warning("Please select stroke objects to bake.")
        return
    
    for stroke in selection:
        try:
            mc.select(stroke)
            
            # Get connected objects before conversion
            sel1 = mc.ls(sl=True, fl=True, dag=True)
            sel2 = mc.listConnections(sel1, type='stroke') or []
            sel3 = mc.listConnections(sel1, type='transform') or []
            
            # Convert to polygon
            mel.eval('doPaintEffectsToPoly(1,0,1,1,100000);')
            mel.eval('polyMultiLayoutUV -lm 1 -sc 1 -rbf 0 -fr 1 -ps 0.05 -l 2 -gu 1 -gv 1 -psc 1 -su 1 -sv 1 -ou 0 -ov 0;')
            
            mc.delete(ch=True)
            mc.parent(w=True)
            
            # Clean up (but keep curves)
            sel4 = mc.ls("birchLimb*MeshGroup") or []
            
            # Only delete specific stroke-related objects, not curves
            for obj in sel2:  # Only stroke objects
                if mc.objExists(obj):
                    try:
                        mc.delete(obj)
                    except:
                        pass
            
            if sel4:
                for obj in sel4:
                    if mc.objExists(obj):
                        try:
                            mc.delete(obj)
                        except:
                            pass
            
            mc.CenterPivot()
            mc.hyperShade(a="lambert1")
            
            # Rename created objects
            selected_objects = mc.ls(selection=True)
            newname = "Cable_Curve_"
            for number, obj in enumerate(selected_objects):
                if mc.objExists(obj):
                    print(f'Old Name: {obj}')
                    new_name = f'{newname}{number:02d}'
                    print(f'New Name: {new_name}')
                    try:
                        mc.rename(obj, new_name)
                    except:
                        pass
                        
        except Exception as e:
            print(f"Error baking stroke {stroke}: {e}")
            continue
    
    print("Bake with curve completed")

def back_to_curve():
    """Convert selected geometry back to curves"""
    try:
        selection = mc.ls(sl=True)
        
        for obj in selection:
            mc.select(obj)
            mc.ConvertSelectionToEdgePerimeter()
            mc.ConvertSelectionToFaces()
            mc.ConvertSelectionToContainedEdges()
            
            sel = mc.ls(sl=True)
            sel_objects = mc.ls(os=True)
            
            if len(sel_objects) > 1:
                mc.select(sel_objects[1])
                mc.SelectEdgeLoopSp()
                mc.polyToCurve(form=2, degree=1, conformToSmoothMeshPreview=0)
                mc.CenterPivot()
                mc.DeleteHistory()
                mc.rename("Curve_0")
                
                # Adjust pivot to first control point
                sel_curve = mc.ls(sl=True)
                if sel_curve:
                    curve = sel_curve[0]
                    try:
                        pos_x = mc.getAttr(f"{curve}.controlPoints[0].xValue")
                        pos_y = mc.getAttr(f"{curve}.controlPoints[0].yValue")
                        pos_z = mc.getAttr(f"{curve}.controlPoints[0].zValue")
                        mc.move(pos_x, pos_y, pos_z, 
                               f"{curve}.scalePivot", f"{curve}.rotatePivot", 
                               absolute=True)
                    except:
                        pass
    except Exception as e:
        print(f"Error converting back to curve: {e}")

def clean_dynamic_nodes():
    """Clean up all dynamic simulation nodes"""
    try:
        nodes_to_delete = []
        
        # Check for hair system nodes
        if mc.objExists("hairSystem1"):
            nodes_to_delete.append("hairSystem1")
        
        if mc.objExists("nucleus1"):
            nodes_to_delete.append("nucleus1")
        
        if mc.objExists("hairSystem1Follicles"):
            nodes_to_delete.append("hairSystem1Follicles")
        
        if mc.objExists("hairSystem1OutputCurves"):
            nodes_to_delete.append("hairSystem1OutputCurves")
        
        # Find nRigid nodes
        rigid_nodes = mc.ls("nRigid*")
        nodes_to_delete.extend(rigid_nodes)
        
        # Delete nodes if they exist
        if nodes_to_delete:
            for node in nodes_to_delete:
                if mc.objExists(node):
                    try:
                        mc.delete(node)
                    except:
                        pass
            print(f"Cleaned up dynamic nodes: {nodes_to_delete}")
        else:
            print("No dynamic nodes found to clean up")
            
    except Exception as e:
        print(f"Error cleaning dynamic nodes: {e}")

# ============================================================================
# UI UPDATE FUNCTIONS
# ============================================================================

def update_ui_from_selection():
    """Update UI sliders based on current selection"""
    try:
        selection = mc.ls(sl=True, fl=True, dag=True, type='stroke')
        
        if len(selection) == 1:
            stroke = selection[0]
            brushes = mc.listConnections(stroke, d=True, scn=True, type='brush')
            
            if brushes:
                brush = brushes[0]
                
                # Update sliders with current values
                try:
                    scale_val = mc.getAttr(f"{brush}.globalScale")
                    mc.floatSliderGrp("Slider_Scale", e=True, value=scale_val)
                    
                    width_val = mc.getAttr(f"{brush}.brushWidth")
                    mc.floatSliderGrp("Slider_Width", e=True, value=width_val)
                    
                    section_val = mc.getAttr(f"{brush}.tubeSections")
                    mc.intSliderGrp("Slider_Section", e=True, value=section_val)
                    
                    twist_val = mc.getAttr(f"{brush}.twistRate")
                    mc.floatSliderGrp("Slider_Twist", e=True, value=twist_val)
                    
                    flat_val = mc.getAttr(f"{brush}.flatness1")
                    mc.floatSliderGrp("Slider_Flat", e=True, value=flat_val)
                    
                    # Twist checkbox
                    forward_twist = mc.getAttr(f"{brush}.forwardTwist")
                    twist_on = (forward_twist == 0)
                    mc.checkBox("Check_Twist", e=True, value=twist_on)
                    
                except:
                    pass
                
                # Update stroke-specific attributes
                try:
                    density_val = mc.getAttr(f"{stroke}.sampleDensity")
                    mc.floatSliderGrp("Slider_Density", e=True, value=density_val)
                    
                    smooth_val = mc.getAttr(f"{stroke}.smoothing")
                    mc.floatSliderGrp("Slider_Smoothing", e=True, value=smooth_val)
                    
                    pstart_val = mc.getAttr(f"{stroke}.pressureScale[0].pressureScale_FloatValue")
                    mc.floatSliderGrp("Slider_Pstart", e=True, value=pstart_val)
                    
                    pend_val = mc.getAttr(f"{stroke}.pressureScale[1].pressureScale_FloatValue")
                    mc.floatSliderGrp("Slider_Pend", e=True, value=pend_val)
                    
                except:
                    pass
    except:
        pass

def create_fallback_window():
    """Create a fallback regular window if workspace control fails"""
    window_name = "Cable_Tool_Window"
    
    if mc.window(window_name, exists=True):
        mc.deleteUI(window_name)
    
    window = mc.window(
        window_name,
        title="Cable Tool 3.0",
        widthHeight=(320, 500),
        sizeable=True
    )
    
    create_custom_workspace_control()
    mc.showWindow(window)

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main function to initialize and show the cable tool"""
    window_name = "Cable_3.0"
    
    # Clean up any existing UI elements
    if mc.window(window_name, exists=True):
        mc.deleteUI(window_name)
    
    if mc.workspaceControl(window_name, exists=True):
        mc.deleteUI(window_name)
    
    # Delete any existing script jobs for this tool
    try:
        existing_jobs = mc.scriptJob(listJobs=True)
        for job in existing_jobs:
            if "update_ui_from_selection" in job:
                job_id = int(job.split(':')[0])
                mc.scriptJob(kill=job_id)
    except:
        pass
    
    # Make the UI creation function available globally for workspace control
    import __main__
    __main__.create_custom_workspace_control = create_custom_workspace_control
    __main__.update_ui_from_selection = update_ui_from_selection
    
    # Create the workspace control
    try:
        mc.workspaceControl(
            window_name,
            retain=False,
            floating=True,
            uiScript="create_custom_workspace_control()",
            label="Cable Tool 3.0",
            widthProperty="preferred",
            heightProperty="preferred"
        )
        
        # Set up selection change callback to update UI
        mc.scriptJob(
            runOnce=False,
            e=["SelectionChanged", lambda *args: update_ui_from_selection()]
        )
        
        print("Cable Tool 3.0 - Python 3 Compatible Version Loaded")
        print("Fixed: NameError, Added scrollable UI, Added material fix functions")
        print("Updated for Maya 2022+ compatibility")
        
    except Exception as e:
        print(f"Error creating Cable Tool UI: {e}")
        print("Trying alternative UI creation method...")
        
        # Fallback to regular window if workspace control fails
        create_fallback_window()

# Initialize the tool when the script is run
if __name__ == "__main__":
    main()
else:
    # If imported as module, just run main
    main()