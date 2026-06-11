"""
Welder - paint-effects based weld/cable create tool (by Wizix).

Refactored out of the old inline GS_tools.mel menu command:
  - Python 3 fixes (print statements, callbacks),
  - control callbacks are real function references (not __main__ string evals),
  - asset paths resolved relative to this module / the shared GSTools icons.

NOTE: the original shipped a 'Welder_shd.ma' shader and a 'Welder_icons' set.
If the shader is missing, the UI still builds but CreateWeld can't apply the
weld material (a warning is printed).
"""
import os
import maya.cmds as mc
import maya.mel as mel

_WIN = "Welder"


def _icon(name):
    """Welder icons live in the shared GSTools/icons/Welder_icons folder."""
    gstools = os.environ.get("GSTOOLS", "")
    return os.path.join(os.path.dirname(gstools.rstrip("\\/")), "icons", "Welder_icons", name)


def _ensure_shader():
    if mc.objExists('Welder_shd'):
        return
    shader_path = os.path.join(os.path.dirname(__file__), "Welder_shd.ma")
    if os.path.exists(shader_path):
        mc.file(shader_path, i=True)
    else:
        mc.warning("Welder: 'Welder_shd.ma' not found - CreateWeld will skip the weld material.")


def _init_brush():
    """Load the birchLimb paint-effects brush and apply default tube settings."""
    version = mc.about(v=True)
    os_name = mc.about(os=True)
    try:
        if os_name == 'win64':
            try:
                use_examples = int(str(version)[:4]) >= 2017
            except ValueError:
                use_examples = True
            if use_examples:
                brush = "C:/Program Files/Autodesk/Maya{v}/Examples/Paint_Effects/Trees/birchLimb.mel".format(v=version)
            else:
                brush = "C:/Program Files/Autodesk/Maya{v}/brushes/trees/birchLimb.mel".format(v=version)
            mel.eval('visorPanelBrushPressCallback files1VisorEd "{0}";'.format(brush))
            mel.eval('setToolTo $gMove;')
        elif os_name == 'mac':
            brush = "/Applications/Autodesk/maya{v}/Maya.app/Contents/Examples/Paint_Effects/Trees/birchLimb.mel".format(v=version)
            mel.eval('visorPanelBrushPressCallback files1VisorEd "{0}";'.format(brush))
            mel.eval('setToolTo $gMove;')

        mc.setAttr("birchLimb.globalScale", 1)
        mc.setAttr("birchLimb.brushWidth", 1)
        mc.setAttr("birchLimb.forwardTwist", 0)
        mc.setAttr("birchLimb.color1", 0.8, 0.067, 0.047, type='double3')
        mc.setAttr("birchLimb.specularColor", 0, 0, 0, type='double3')
        mc.setAttr("birchLimb.tubeSections", 8)
    except Exception as exc:
        mc.warning("Welder: could not initialise the birchLimb brush: %s" % exc)

    mc.dynWireCtx(displayQuality=100, surfaceOffset=-0.1, pressureMapping1=1,
                  pressureMapping2=0, pressureMapping3=0, pressureMin1=0.4)


# --- INFO ---
def go_artstation(*args):
    mc.launch(web="https://wizix.artstation.com/")


def go_gumroad(*args):
    mc.launch(web="https://gumroad.com/wzx")


def go_facebook(*args):
    mc.launch(web="https://www.facebook.com/WizixPage/")


# --- PAINT ---
def make_paint(*args):
    mc.MakePaintable()
    mc.select(d=True)


def brush_size_val(*args):
    value = mc.floatSliderGrp("Slider_BrushS", q=True, value=True)
    mc.setAttr("birchLimb.globalScale", value)


# --- EDIT ---
def scale_val(*args):
    value = mc.floatSliderGrp("Slider_Scale", q=True, value=True)
    selection = mc.ls(sl=True, fl=True, dag=True, type='stroke')
    for each in mc.listConnections(selection, d=True, scn=True, type='brush') or []:
        mc.setAttr(each + ".globalScale", value)


def density_val(*args):
    value = mc.floatSliderGrp("Slider_Density", q=True, value=True)
    selection = mc.ls(sl=True, fl=True, dag=True, type='stroke')
    for each in selection or []:
        mc.setAttr(each + ".sampleDensity", value)


def section_val(*args):
    value = mc.intSliderGrp("Slider_Section", q=True, value=True)
    selection = mc.ls(sl=True, fl=True, dag=True, type='stroke')
    for each in mc.listConnections(selection, d=True, scn=True, type='brush') or []:
        mc.setAttr(each + ".tubeSections", value)


def smoothing_val(*args):
    value = mc.floatSliderGrp("Slider_Smoothing", q=True, value=True)
    selection = mc.ls(sl=True, fl=True, dag=True, type='stroke')
    for each in selection or []:
        mc.setAttr(each + ".smoothing", value)


# --- CREATE ---
def create_weld(*args):
    selection = mc.ls(sl=True, fl=True, dag=True, type='stroke')
    for _ in selection:
        sel1 = mc.ls(sl=True, fl=True, dag=True)
        sel3 = mc.listConnections(sel1, type='brush')
        sel_all = sel1 + sel3
        mel.eval('doPaintEffectsToPoly(1,0,1,1,100000);')
        mel.eval('polyMultiLayoutUV -lm 1 -sc 1 -rbf 0 -fr 1 -ps 0.05 -l 2 -gu 1 -gv 1 -psc 1 -su 1 -sv 1 -ou 0 -ov 0;')
        mc.delete(ch=True)
        mc.parent(w=True)
        sel4 = mc.ls("birchLimb*MeshGroup")
        mc.delete(sel_all)
        mc.delete(sel4)
        mc.CenterPivot()
        mc.hyperShade(a="Welder_shd")
        selected_objects = mc.ls(selection=True)
        mc.toggleDisplacement()
        newname = "Weld_"
        for number, obj in enumerate(selected_objects):
            print('Old Name: %s' % obj)
            print('New Name: %s%02d' % (newname, number))
            mc.setAttr(obj + ".aiSubdivType", 1)
            mc.setAttr(obj + ".aiSubdivIterations", 2)
            mc.rename(obj, ('%s%02d' % (newname, number)))


# --- SHADER ---
def displace_val(*args):
    value = mc.floatSliderGrp("Slider_Displace", q=True, value=True)
    mc.setAttr("Large_Noise.alphaGain", value)


def wave_plus_val(*args):
    for each in mc.ls(sl=True, fl=True, dag=True, type='mesh') or []:
        mc.select(each + ".map[*]")
        mc.polyEditUV(pu=0.5, pv=0.5, su=1, sv=1.2)
        mc.select(each)


def wave_min_val(*args):
    for each in mc.ls(sl=True, fl=True, dag=True, type='mesh') or []:
        mc.select(each + ".map[*]")
        mc.polyEditUV(pu=0.5, pv=0.5, su=1, sv=0.8)
        mc.select(each)


def show():
    _ensure_shader()
    _init_brush()

    if mc.window(_WIN, exists=True):
        mc.deleteUI(_WIN)

    ram = mc.window(_WIN, t="Welder v1.0", tlb=True, menuBar=True)
    mc.columnLayout(adj=True, w=300, h=280)

    mc.menu(label='Info')
    mc.menuItem(label='Artstation', annotation='My Website', c=go_artstation)
    mc.menuItem(label='Gumroad', annotation='Tutorial', c=go_gumroad)
    mc.menuItem(label='Contact', annotation='For Any Help', c=go_facebook)

    c_h1 = mc.columnLayout(adj=True)
    mc.text(l='  > PAINT', al='left', h=18, font='smallPlainLabelFont', bgc=[0.906, 0.286, 0.239])
    mc.rowColumnLayout(numberOfRows=1)
    mc.separator(w=50, style='none')
    mc.symbolButton(image=_icon("Welder_UVs.png"), c=lambda *a: mc.AutoProjection(), ann="UV Project")
    mc.separator(w=50, style='none')
    mc.symbolButton(image=_icon("Welder_MakeP.png"), c=make_paint, ann="Make Paintable")
    mc.separator(w=50, style='none')
    mc.symbolButton(image=_icon("Welder_Paint.png"), c=lambda *a: mc.PaintEffectsTool(), ann="Paint Weld")
    mc.setParent('..')
    mc.separator(h=3, style='none')
    mc.floatSliderGrp('Slider_BrushS', l="Brush Size", min=0.1, max=10, po=True, field=True,
                      cc=brush_size_val, dc=brush_size_val, v=1, adj=0, cat=[1, "left", 3],
                      cw=[1, 60], ann="Brush Size")

    mc.setParent(c_h1)
    mc.separator(h=10, style='none')
    c_h2 = mc.columnLayout(adj=True)
    mc.text(l='  > EDIT', al='left', h=18, font='smallPlainLabelFont', bgc=[0.906, 0.286, 0.239])
    mc.separator(h=3, style='none')
    mc.floatSliderGrp('Slider_Scale', l="Scale", min=0.1, max=100, po=True, field=True,
                      cc=scale_val, dc=scale_val, v=1, adj=0, cat=[1, "left", 3], cw=[1, 60],
                      ann="Configure to scene set in cm")
    mc.floatSliderGrp('Slider_Density', l="Density", min=0.1, max=5, po=True, field=True,
                      cc=density_val, dc=density_val, v=1, adj=0, cat=[1, "left", 3], cw=[1, 60])
    mc.intSliderGrp('Slider_Section', l="Section", min=3, max=12, po=True, field=True,
                    cc=section_val, dc=section_val, v=8, adj=0, cat=[1, "left", 3], cw=[1, 60])
    mc.floatSliderGrp('Slider_Smoothing', l="Smoothing", min=0, max=10, po=True, field=True,
                      cc=smoothing_val, dc=smoothing_val, v=0, adj=0, cat=[1, "left", 3], cw=[1, 60])

    mc.setParent(c_h2)
    mc.separator(h=15, style='none')
    c_h3 = mc.columnLayout(adj=True)
    mc.text(l='  > CREATE', al='left', h=18, font='smallPlainLabelFont', bgc=[0.906, 0.286, 0.239])
    mc.separator(h=5, style='none')
    mc.rowColumnLayout(numberOfRows=1)
    mc.separator(w=1, h=5, style='none')
    mc.button('buttonCreateWeld', w=290, l="CREATE Weld", c=create_weld, ann="Create Weld")
    mc.setParent('..')

    mc.setParent(c_h3)
    mc.separator(h=5, style='none')
    c_h4 = mc.columnLayout(adj=True)
    mc.text(l='  > SHADER', al='left', h=18, font='smallPlainLabelFont', bgc=[0.906, 0.286, 0.239])
    mc.floatSliderGrp('Slider_Displace', l="Displace", min=0, max=50, po=True, field=True,
                      cc=displace_val, dc=displace_val, v=2, adj=0, cat=[1, "left", 3], cw=[1, 60],
                      ann="Configure to scene set in cm")
    mc.rowColumnLayout(numberOfRows=1)
    mc.separator(w=50, style='none')
    mc.symbolButton(image=_icon("Welder_Min.png"), c=wave_min_val, ann="Wave Down")
    mc.separator(w=20, style='none')
    mc.image(image=_icon("Welder_Wave.png"), ann="Wave")
    mc.separator(w=20, style='none')
    mc.symbolButton(image=_icon("Welder_Plus.png"), c=wave_plus_val, ann="Wave Up")
    mc.setParent('..')

    mc.setParent(c_h4)
    mc.showWindow(ram)
    mc.window(ram, edit=True, h=380)
