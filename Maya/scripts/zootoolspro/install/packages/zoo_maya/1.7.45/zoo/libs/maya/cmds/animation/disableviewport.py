import functools

from maya import cmds
from maya import mel


def suspendViewportUpdate(suspend):
    """Suspends all of Maya's viewports, run code inbetween suspending and unsuspending. Handy for animation tools.

        disableviewport.suspendViewportUpdate(True)
        someCodeHere()
        disableviewport.suspendViewportUpdate(False)

    """
    if suspend:
        cmds.refresh(suspend=True)
    else:
        cmds.refresh(suspend=False)
        cmds.refresh(force=True)


def resetViewport():
    """Fully refreshes maya's viewport, gives it a kick!"""
    cmds.ogs(reset=True)


# ------------------
# Decorators
# ------------------


def disableViewportBlankDec(func):
    """Decorator - Blanks out the main Maya display while func is running.
    if func fails, the error will be raised after.

    Credit: https://blog.asimation.com/disable-maya-viewport-while-running-code/

    uses:

        mel.eval("paneLayout -e -manage false $gMainPane")

    """

    @functools.wraps(func)
    def wrap(*args, **kwargs):
        mel.eval("paneLayout -e -manage false $gMainPane")
        try:
            return func(*args, **kwargs)
        except Exception:
            raise  # will raise original error
        finally:
            mel.eval("paneLayout -e -manage true $gMainPane")

    return wrap


def disableViewportRefreshDec(func):
    """Decorator - suspends the Maya display while func is running.
    if func fails, the error will be raised after.

    uses:

        cmds.refresh(suspend=True)

    """
    @functools.wraps(func)
    def inner(*args, **kwargs):
        try:
            cmds.refresh(suspend=True)
            return func(*args, **kwargs)
        except Exception:
            raise  # will raise original error
        finally:
            cmds.refresh(suspend=False)
            cmds.refresh(force=True)

    return inner
