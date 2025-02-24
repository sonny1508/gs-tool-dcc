import maya.mel as mel


def openVRayRenderview(final=False, ipr=False):
    """Open the VRay Frame Buffer window (render view) and optionally start rendering

    :param final: True will immediately start final rendering an image
    :type final: bool
    :param ipr: True will immediately start IPR rendering an image
    :type ipr: bool
    """
    if ipr or final:
        mel.eval("vrayShowVFBCmd")
    else:
        mel.eval("vrayShowVFBCmd")

