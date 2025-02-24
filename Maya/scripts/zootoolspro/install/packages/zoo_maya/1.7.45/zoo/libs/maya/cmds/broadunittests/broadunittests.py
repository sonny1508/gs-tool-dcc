"""
Broad Unit Tests zoo code roughly by creating and deleting objects rigs scenes etc to see if anything \
breaks or gives errors.

To test run

.. code-block:: python

    from zoo.libs.maya.cmds.broadunittests import broadunittests
    broadunittests.broadUnitTests(skipRenderers=["Redshift", "Renderman"], includeUIs=True, assetPresets=True,
                              cameraTools=True, modelingTools=True, controlsJoints=True, utilities=True, dynamics=True,
                              animationTools=True, uvTools=True, hive=True)

"""
from zoo.libs.maya.cmds.broadunittests import testrenderers
from zoo.libs.maya.cmds.broadunittests import testuis
from zoo.libs.maya.cmds.broadunittests import testcmdsrigging
from zoo.libs.utils import output


def testAssetsPresetsAllRenderers(skipRenderers=[]):
    # Assets - test import and delete of some assets for each renderer
    testrenderers.testImportAssetAllRenderers(skipRenderers)
    # Save an asset, rename asset and delete from disk

    # Light Presets - test import and delete of some assets for each renderer
    testrenderers.testLightPresetsAllRenderers(skipRenderers)
    # Save a light preset, rename preset, and delete from disk

    # Delete light preset from disk

    # Change shader via presets

    # Change shader settings

    # Displacement

    # Mattes

    # Test Area lights

    # Test IBL switch

    # Test directional lights

    # Test enter place reflection

    # Test Edit lights scale

    # Change light Preset

    # Test mattes if not renderman

    # Test displacement creator

    # Test Shader Swap


def testCameraTools():
    pass
    # Test Cameras

    # Test Image Planes

    # Test Animate Image Planes


def testModelingTools():
    pass
    # Test Mirror tools

    # Test Duplicate Along Path

    # Test Tube from Curve

    # Test Modeling Align

    # Test Thick Extrude

    # Test SubD smooth control

    # Test Object Cleaner


def testControlJoints():
    # Test Control Creator

    # Test Edit Curves

    # Test Color Overrides

    # Joint Tool Window

    # Joints On Curve

    # Controls On Curve

    # Spline Rig - Builds a curve and then spline rig
    testcmdsrigging.testSplineRig()

    # Reparent Group toggle

    # Skinning Utilities


def testUtitlities():
    pass


def testDynamics():
    pass


def testAnimationTools():
    pass


def testAnimationTools():
    pass


def testUVTools():
    pass


def broadUnitTests(skipRenderers=[], includeUIs=True, assetPresets=True, cameraTools=True, modelingTools=True,
                   controlsJoints=True, utilities=True, dynamics=True, animationTools=True, uvTools=True,
                   hive=True):
    """Tests all cmds related code.  Not a proper unit test, broadly tests all tools and optionally UIs too.

    :param skipRenderers: Add the renderers to skip if you don't have them installed ["Redshift", "Renderman"]
    :type skipRenderers: list(str)
    :param includeUIs: If True will test the UIs, should be False for mayapy standalone tests without Maya open.
    :type includeUIs: bool
    :param assetPresets: Include asset preset tools?
    :type assetPresets: bool
    :param cameraTools: Include cameraTools tools?
    :type cameraTools: bool
    :param modelingTools: Include modelingTools tools?
    :type modelingTools: bool
    :param controlsJoints: Include controlsJoints tools?
    :type controlsJoints: bool
    :param utilities: Include utilities tools?
    :type utilities: bool
    :param dynamics: Include dynamics tools?
    :type dynamics: bool
    :param animationTools: Include animationTools tools?
    :type animationTools: bool
    :param uvTools: Include uvTools tools?
    :type uvTools: bool
    :param hive: Ignores opening the Hive UI as it may not be installed
    :type hive: bool

    :return successState: Returns True if successfully completed
    :rtype successState: bool
    """
    # Open all UIs
    if includeUIs:
        testuis.openAllUIs(hive=hive)
    # Test all assets shaders and light presets for each renderer
    if assetPresets:
        testAssetsPresetsAllRenderers(skipRenderers)

    # Test Camera tools
    if cameraTools:
        testCameraTools()

    # Test modeling tools
    if modelingTools:
        testModelingTools()

    # Test Controls Joints
    if controlsJoints:
        testControlJoints()

    # Test Utilities
    if utilities:
        testUtitlities()

    # Test Dynamics
    if dynamics:
        testDynamics()

    # Test Animation Tools
    if animationTools:
        testAnimationTools()

    # Test UV Tools
    if uvTools:
        testUVTools()

    output.displayInfo("\n\n\n\n$$$$$$$$$$$$$$$$$$$$$$$ SUCCESS FIN $$$$$$$$$$$$$$$$$$$$$$$\n\n\n\n")
    return True
