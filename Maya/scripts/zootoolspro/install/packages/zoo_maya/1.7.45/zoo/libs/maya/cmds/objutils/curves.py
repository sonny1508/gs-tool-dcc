import maya.mel as mel
from maya import cmds

from zoo.libs.utils import output
from zoo.libs.maya.cmds.objutils import filtertypes


def createCurveContext(degrees=3, bezier=0):
    """Enters the create curve context (user draws cvs).  Uses mel. Cubic Has option for curve degrees.

    More options can be added later.

    :param degrees: The curve degrees of the curve.  3 is Bezier, 1 is linear.
    :type degrees: int
    :param bezier: when the curves has 3 degrees make the curve bezier.  Default 0 is cubic.
    :type bezier: int
    """
    mel.eval("curveCVToolScript 4;\n"
             "curveCVCtx -e -d {} -bez {} `currentCtx`;".format(str(degrees), str(bezier)))

def createBezierCurveContext():
    """Enters the create bezier curve context (user draws cvs).

    Uses mel.
    """
    mel.eval("curveBezierToolScript 4;")

def splineIkHandleContext(spans=2):
    """ Create Spline Ik Handle

    :param spans:
    :type spans:
    :return:
    :rtype:
    """
    cmds.IKSplineHandleTool()
    cmds.ikSplineHandleCtx("ikSplineHandleContext", e=1, numSpans=spans, priorityH=1, weightH=1, poWeightH=1,
                           autoPriorityH=0, snapHandleH=1, forceSolverH=1, stickyH="off",
                           createCurve=1, simplifyCurve=1, rootOnCurve=1, twistType="linear", createRootAxis=0,
                           parentCurve=1, snapCurve=0, rootTwistMode=0)


def reverseCurves(curveList, replaceOriginal=True):
    """Reverses multiple Maya nurbs curves direction.  Uses cmds.reverseCurve()

    :param curveList: A list of Maya nurbsCurves, usually transforms is ok
    :type curveList: list(str)
    :param replaceOriginal: If True will reverse the current curve, False and will duplicate
    :type replaceOriginal: bool
    """
    for curve in curveList:
        cmds.reverseCurve(curve, replaceOriginal=replaceOriginal)


def reverseCurvesSelection(replaceOriginal=True):
    """Reverses selected Maya nurbs curve direction. Uses cmds.reverseCurve()

    :param replaceOriginal: If True will reverse the current curve, False and will duplicate
    :type replaceOriginal: bool
    """
    objList = cmds.ls(selection=True)
    if not objList:
        output.displayWarning("Nothing is selected, please select a curve to reverse.")
        return
    curveList = filtertypes.filterTypeReturnTransforms(objList, shapeType="nurbsCurve")
    if not curveList:
        output.displayWarning("No curves found in the selection. Please select curve objects t0 reverse.")
        return
    reverseCurves(curveList, replaceOriginal=replaceOriginal)


def xrayCurves(curveShapes, xray, message=True):
    """Sets the curveShapes to be XRay mode on or off.

    XRay sees through other objects, like joints.

    :param xray: Set selected curves to be xray or normal display mode.
    :type xray: bool
    """
    for n in curveShapes:
        if cmds.attributeQuery("alwaysDrawOnTop", node=n, exists=True):  # error checking, other shapes ignores
            cmds.setAttr(".".join([n, "alwaysDrawOnTop"]), xray)
    if message:
        output.displayInfo("Curve XRay mode `{}`".format(xray))


def xrayCurvesSelected(xray, message=True):
    """Sets the selected curve transforms to be XRay display mode on or off.

    XRay sees through other objects, like joints.

    :param xray: Set selected curves to be xray or normal display mode.
    :type xray: bool
    """
    nodes = cmds.ls(selection=True)
    if not nodes:
        output.displayWarning("Please select an object")
        return
    shapes = cmds.listRelatives(nodes, shapes=True)
    if not shapes:
        output.displayWarning("No shape nodes found, please select curves")
        return
    xrayCurves(shapes, xray, message=message)

