from zoo.core.util import env, profiling
from zoo.libs.maya.mayacommand import mayaexecutor as executor
from zoo.libs.maya.utils import general as _general
from zoo.libs.utils import output
from zoo.libs.maya.qt import nodeeditor
from zoo.libs.hive.base.util import templateutils
from zoo.libs.maya import triggers

@triggers.blockSelectionCallbackDecorator
def createRig(name=None, namespace=None):
    """ Creates a new instance of a rig or returns the existing one

    :param name: Create rig with string name, if empty hive will generate a new rig name
    :param namespace:
    :return:
    """
    if env.isInMaya():
        with nodeeditor.disableNodeEditorAddNodeContext():
            return executor.execute("hive.rig.create", **locals())
    return executor.execute("hive.rig.create", **locals())


def renameRig(rig, name):
    """ Renames rig to new name
    
    :param rig: The Hive Rig
    :type rig: :class:`zoo.libs.hive.base.rig.Rig`
    :param name: New name as string
    :return: 
    """
    return executor.execute("hive.rig.rename", **locals())

@triggers.blockSelectionCallbackDecorator
def deleteRig(rig):
    """ Delete hive rig

    :param rig:
    :type rig: :class:`zoo.libs.hive.base.rig.Rig`
    :return:
    """
    return executor.execute("hive.rig.delete", **locals())

@triggers.blockSelectionCallbackDecorator
def createComponents(rig, components, buildGuides=False, buildRigs=False, parentNode=None):
    """ Create components under the specified rig

    :param rig:
    :type rig: :class:`zoo.libs.hive.base.rig.Rig`
    :param components: [{"type": "", "name":"", "side": ""}, ...]
    :type components: list[dict]
    :param buildGuides:
    :type buildGuides: bool
    :param buildRigs:
    :type buildRigs: bool
    :param parentNode:
    :type parentNode:
    :return:
    """
    if env.isInMaya():
        with nodeeditor.disableNodeEditorAddNodeContext():
            return executor.execute("hive.rig.create.components", **locals())
    return executor.execute("hive.rig.create.components", **locals())

@triggers.blockSelectionCallbackDecorator
def deleteComponents(rig, components, children=True):
    """ Delete components from rig

    :param rig: :class:`zoo.libs.hive.base.rig.Rig`
    :type components: list[:class:`zoo.libs.hive.base.component.Component`]
    :param children: If True will recursively delete all connected child components.
    :type children: bool
    """
    commandId = "hive.component.delete"

    def _repeatDeleteComponents():
        """Repeat command
        """
        from zoo.libs.hive import api
        selectedComponents = api.componentsFromSelected()
        if not selectedComponents:
            return
        rigInstance = None
        comps = list(selectedComponents.keys())
        for component in comps:
            rigInstance = component.rig
            break
        executor.execute(commandId, rig=rigInstance, components=comps, children=children)

    result = executor.execute(commandId, rig=rig, components=components, children=children)
    _general.createRepeatCommandForFunc(_repeatDeleteComponents)
    return result

@triggers.blockSelectionCallbackDecorator
def duplicateComponents(rig, sources):
    """ Duplicate component

    Sources takes the format of

    [{"component": component,
      "name": name,
      "side": side,
      "parent": parent},
      ...]

    :type rig: :class:`zoo.libs.hive.base.rig.Rig`
    :param sources: Components to duplicate.
    :type sources: list[dict]
    """
    if env.isInMaya():
        with nodeeditor.disableNodeEditorAddNodeContext():
            return executor.execute("hive.component.duplicate", **locals())
    return executor.execute("hive.component.duplicate", **locals())

@triggers.blockSelectionCallbackDecorator
def updateGuideSettings(component, settings):
    """Execute update guide settings

    :type component: :class:`zoo.libs.hive.base.component.Component`
    :type settings: dict
    """
    return executor.execute("component.guides.setting.update", **locals())

@triggers.blockSelectionCallbackDecorator
def showComponents(components):
    """ Shows a component in the scene

    :param components: Hive component to show
    :type components: list[:class:`zoo.libs.hive.base.component.Component`]
    """
    return executor.execute("hive.components.show", **locals())

@triggers.blockSelectionCallbackDecorator
def hideComponents(components):
    """ Hides a component in the scene

    :param components: Hive component to hide
    :type components: list[:class:`zoo.libs.hive.base.component.Component`]
    """
    return executor.execute("hive.components.hide", **locals())

@triggers.blockSelectionCallbackDecorator
def toggleBlackBox(components, save=True):
    """ Toggle Black box for components

    :param components: List of components
    :type components: list[`zoo.libs.hive.base.component.Component`]
    :param save: If True the black box state will be saved with the rig.
    :type save: bool
    """
    return executor.execute("hive.component.blackbox.toggle", **locals())

@triggers.blockSelectionCallbackDecorator
def setComponentParent(parentComponent, parentGuide, childComponent):
    """ Set Parent of Component

    :param parentComponent:
    :type parentComponent: :class:`zoo.libs.hive.base.component.Component`
    :param parentGuide:
    :type parentGuide: :class:`zoo.libs.hive.base.hivenodes.hnodes.Guide`
    :param childComponent:
    :type childComponent: zoo.libs.hive.base.component.Component
    """
    return executor.execute("hive.component.parent.add", **locals())

@triggers.blockSelectionCallbackDecorator
def setComponentSide(component, side):
    """ Sets the component side (eg. L, R, etc)

    :param component: The components to change.
    :type component: :class:`zoo.libs.hive.base.component.Component`
    :param side: The side the change the component to
    :type side: str
    """
    return executor.execute("hive.component.rename.side", **locals())

@triggers.blockSelectionCallbackDecorator
def renameComponent(component, name):
    """ Rename component to new name excluding the side label

    :param component: The components to rename.
    :type component: :class:`zoo.libs.hive.base.component.Component`
    :param name: The new name for the component
    :type name: str
    """
    return executor.execute("hive.component.rename", **locals())

@triggers.blockSelectionCallbackDecorator
def matchIKFK(components, state, frameRange=None, bakeEveryFrame=True):
    """ Switches between IK FK while matching the transforms of the joints/controls.

    :param components: The list of IKFK components to switch
    :type components: list[:class:`zoo.libs.hive.base.component.Component`]
    :param state: 0 for IK 1 for FK.
    :type state: int
    :param frameRange: The frame range to bake or None if setting the current frame only.
    :type frameRange: list[int, int] or None
    :param bakeEveryFrame: When bake frames this determine whether bake every frame or update existing.
    :type bakeEveryFrame: bool
    """
    return executor.execute("hive.rig.ikfkMatch", **locals())

@triggers.blockSelectionCallbackDecorator
def FixFkRotations(components):
    """Fixes the FK rotations on the specified components.
    This is necessary when the animator rotates off the main rotation axis ie. Z where the twist
    joints won't compensate for.

    :param components: List of IKFK components to fix the fk mid joint rotations
    :type components: list[:class:`zoo.libs.hive.base.component.Component`]
    """
    with _general.undoContext("BuildHiveGuide"):
        matchIKFK(components, state=False)
        matchIKFK(components, state=True)

@triggers.blockSelectionCallbackDecorator
def recalculatePoleVector(components, frameRange=None, bakeEveryFrame=True):
    """ Recalculates the pole vector for component which contain ik.

    :param components: The list of ik components to set the pole vector position for.
    :type components: list[:class:`zoo.libs.hive.base.component.Component`]
    :param frameRange: The frame range to bake or None if setting the current frame only.
    :type frameRange: list[int, int] or None
    :param bakeEveryFrame: When bake frames this determine whether bake every frame or update existing.
    :type bakeEveryFrame: bool
    """
    return executor.execute("hive.rig.recalculatePoleVector", **locals())

@triggers.blockSelectionCallbackDecorator
def setDeformVisibility(rig, state=False):
    """Sets the visibility of the deformation Layer of every component in the rig

    :param rig: The hive rig instance.
    :type rig: :class:`zoo.libs.hive.base.rig.Rig`
    :param state: the visibility state to set too
    :type state: bool
    """
    return executor.execute("hive.rig.showHideDeform", **locals())

@triggers.blockSelectionCallbackDecorator
def mirrorComponents(rig, components):
    """Mirrors the provided components.

    :param rig: The rig instance
    :type rig: :class:`api.Rig`
    :param components: A dict of components to mirror
    :type components: list[dict[:class:`:class:`zoo.libs.hive.base.component.Component`, bool, tuple[str], str, str]]
    :return:
    :rtype:

    components argument values::

        list[
            dict[component :class:`:class:`zoo.libs.hive.base.component.Component` : The component instance to mirror.
            duplicate bool: Whether to duplicate then mirror or mirror in place.
            translate tuple[str]: list of axis to mirror translation on.
            rotate str : mirror plane "yz", "xz", "xy".
            side str: The newly created component side value.
        ]]

    """
    if env.isInMaya():
        with nodeeditor.disableNodeEditorAddNodeContext():
            executor.execute("hive.component.guide.mirror", **locals())
    else:
        executor.execute("hive.component.guide.mirror", **locals())

@triggers.blockSelectionCallbackDecorator
def applySymmetry(rig, components):
    executor.execute("hive.component.symmetry", **locals())



@triggers.blockSelectionCallbackDecorator
def buildGuides(rig):
    """Builds the provided rig guide system.

    :param rig: The rig Instance
    :type rig: :class:`rig.Rig`
    """

    if env.isInMaya():
        with _general.undoContext("BuildHiveGuide"), \
                nodeeditor.disableNodeEditorAddNodeContext():
            executor.execute("hive.component.rig.delete", rig=rig)
            executor.execute("hive.rig.global.buildGuides", rig=rig)
            if rig.deformLayer():
                executor.execute("hive.rig.showHideDeform", rig=rig, state=False)

            output.displayInfo("Success: {} Guide Mode".format(rig.name()))
    else:
        with _general.undoContext("BuildHiveGuide"):
            executor.execute("hive.component.rig.delete", rig=rig)
            executor.execute("hive.rig.global.buildGuides", rig=rig)
            if rig.deformLayer():
                executor.execute("hive.rig.showHideDeform", rig=rig, state=False)

            output.displayInfo("Success: {} Guide Mode".format(rig.name()))

@triggers.blockSelectionCallbackDecorator
def buildGuideControls(rig):
    if env.isInMaya():
        with _general.undoContext("BuildHiveGuide"), \
                nodeeditor.disableNodeEditorAddNodeContext():
            executor.execute("hive.component.rig.delete", rig=rig)
            executor.execute("hive.rig.global.buildGuidesControls", rig=rig)
            if rig.deformLayer():
                executor.execute("hive.rig.showHideDeform", rig=rig, state=False)

            output.displayInfo("Success: {} Guide Mode".format(rig.name()))
    else:
        executor.execute("hive.rig.global.buildGuidesControls", rig=rig)
        executor.execute("hive.component.rig.delete", rig=rig)
        if rig.deformLayer():
            executor.execute("hive.rig.showHideDeform", rig=rig, state=False)

        output.displayInfo("Success: {} Guide Mode".format(rig.name()))


@triggers.blockSelectionCallbackDecorator
def buildDeform(rig):
    """Builds the rigs Deformation Layer

    :param rig: The rig instance to build
    :type rig: :class:`rig.Rig`
    :return: True if the build succeeded.
    :rtype: bool
    """
    if env.isInMaya():
        with _general.undoContext("BuildHiveSkeleton"), \
                nodeeditor.disableNodeEditorAddNodeContext():
            executor.execute("hive.component.guide.hide", rig=rig)
            executor.execute("hive.component.rig.delete", rig=rig)
            result = executor.execute("hive.component.skeleton.build", rig=rig)
            output.displayInfo("Success: {} Skeleton Mode".format(rig.name()))
    else:
        with _general.undoContext("BuildHiveSkeleton"):
            executor.execute("hive.component.guide.hide", rig=rig)
            executor.execute("hive.component.rig.delete", rig=rig)
            result = executor.execute("hive.component.skeleton.build", rig=rig)
            output.displayInfo("Success: {} Skeleton Mode".format(rig.name()))
    return result


@triggers.blockSelectionCallbackDecorator
def buildRigs(rig):
    """Builds the provided rig instance Rig Layer.

    :param rig: The rig instance to build
    :type rig: :class:`api.Rig`
    :return: True if succeeded.
    :rtype: bool
   """
    if env.isInMaya():
        with _general.undoContext("BuildHiveRig"), \
                nodeeditor.disableNodeEditorAddNodeContext():
            executor.execute("hive.component.guide.hide", rig=rig)
            result = executor.execute("hive.rig.global.buildRigs", rig=rig)
            output.displayInfo("Success: {} Rig Mode".format(rig.name()))
    else:
        with _general.undoContext("BuildHiveRig"):
            executor.execute("hive.component.guide.hide", rig=rig)
            result = executor.execute("hive.rig.global.buildRigs", rig=rig)
            output.displayInfo("Success: {} Rig Mode".format(rig.name()))
    return result

@triggers.blockSelectionCallbackDecorator
def polishRig(rig):
    """Runs polishRig() on the provide rig instance.

    .. note::

        Currently this isn't undoable.

    :param rig: The rig instance to polish
    :type rig: :class:`api.Rig`
    :return: Returns True if successful
    :rtype: bool
    """
    if env.isInMaya():
        with nodeeditor.disableNodeEditorAddNodeContext():
            result = executor.execute("hive.rig.global.polishRig", **locals())
    else:
        result = executor.execute("hive.rig.global.polishRig", **locals())
    output.displayInfo("Success: {} Polish Mode".format(rig.name()))
    return result

@triggers.blockSelectionCallbackDecorator
def saveTemplate(rig, name, components=None, overwrite=True, folderPath=None):
    """Saves the provide rig instance and components to the template library with the registered name.

    :param rig: The rig instance
    :type rig: :class:`api.Rig`
    :param name: The name for the template
    :type name: str
    :param components: A list of components to save, if None is provided then the full rig will be saved.
    :type components: list[:class:`api.Component`]
    :param overwrite: If True will force save the template even if the template elready exists.
    :type overwrite: bool
    :param folderPath: The folder Path to save the template too. If None then default assets location is used.
    :type folderPath: str or None
    :return: The Template path which was exported
    :rtype: str
    """
    return executor.execute("hive.rig.template.save", **locals())

@triggers.blockSelectionCallbackDecorator
def loadTemplate(filePath, rig=None, name=None):
    """Loads the provided filepath as a hive template and either creates
    or updates the rig.

    :param filePath: The template file path
    :type filePath: str
    :param rig: If None a new rig with the provided will be created other \
    the template will be applied to the provided rig.

    :type rig: :class:`api.Rig` or None
    :param name: The name for the new rig if rig is None
    :type name: str
    :return: Rig instance and a list of created components.
    :rtype: tuple[:class:`api.Rig`, dict[str, :class:`api.Component`]
    """
    if env.isInMaya():
        with nodeeditor.disableNodeEditorAddNodeContext():
            rig, components = executor.execute("hive.rig.create.template",
                                               templateFile=filePath,
                                               rig=rig,
                                               name=name)
    else:
        rig, components = executor.execute("hive.rig.create.template",
                                           templateFile=filePath,
                                           rig=rig,
                                           name=name)
    return rig, components

@triggers.blockSelectionCallbackDecorator
def deleteTemplate(name):
    """Delete a Hive template based on the provided name.

    :param name: the Template name to delete
    :type name: str
    """
    executor.execute("hive.rig.template.delete", **locals())

@triggers.blockSelectionCallbackDecorator
def updateRigConfiguration(rig, settings):
    """Updates a set of rig configuration settings.

    :param rig: The rig instance to modify
    :type rig: :class:`api.Rig`
    :param settings: The configuration setting name and value.
    :type settings: dict[str, value]
    :return: True when successful.
    :rtype: bool
    """
    executor.execute("hive.configuration.update", **locals())

@triggers.blockSelectionCallbackDecorator
def setFkGuideParent(parentGuide, childGuides):
    """Re parents the children guides(first selected) to the parent Guide(last Selected)

    :param parentGuide: The parent Fk guide for the child to re-parent too.
    :type parentGuide: :class:`api.Guide`
    :param childGuides: The child FK guides to re-parent
    :type childGuides: list[:class:`api.Guide`]
    :return: True if successful
    :rtype: bool
    """
    return executor.execute("hive.components.guides.setFkGuideParent",
                            **locals())

@triggers.blockSelectionCallbackDecorator
def addFkGuide(components):
    """Creates a new guide for each provided node if that node is linked
    to a FKChain Component.

    :param components: A list of components to show guides for
    :type components: dict[:class:`api.Component`, list[:class:`zapi.DagNode`]]
    :return: True if successful
    :rtype: bool
    """
    return executor.execute("hive.components.guides.addFkGuide",
                            **locals())

@triggers.blockSelectionCallbackDecorator
def autoAlignGuides(components):
    """Realign all provided component guides. This includes realigning the rotations
    using the guide settings for autoAlign.

    :param components: The list of hive components which support twists.
    :type components: list[:class:`api.Component`]
    """
    executor.execute("hive.components.guides.alignGuides", **locals())

@triggers.blockSelectionCallbackDecorator
def setGuideLRA(components, visibility=True):
    """ Sets all LRA shape visibility on the guides for the given components.

    :param components: Components to set.
    :type components: list[`api.Component`]
    :param visibility: Visibility state.
    :type visibility: bool
    """
    executor.execute("hive.component.guide.lra", components=components, visibility=visibility)
@triggers.blockSelectionCallbackDecorator
def setGuidesWorldMatrices(guides, matrices):
    """Sets all given guide worldMatrices to the given matrices.
    This command will appropriately maintain all child guide transforms

    :param guides: The guides to set.
    :type guides: list[:class:`zapi.DagNode`] or list[:class:`zoo.libs.hive.base.hivenodes.Guide`]
    :param matrices: The matrices to set.
    :type matrices: list[:class:`zapi.Matrix`]
    """

    executor.execute("hive.component.guide.setGuideWorldMatrix", **locals())

@triggers.blockSelectionCallbackDecorator
def updateRigFromTemplateData(rig, templateData, remapData):
    """Updates the rig instance with the template.

    It is important to note that this function will completely wipe
    out all meta-data for each component, except for the component meta node.
    However, all deform Joints will be maintained.

    .. note:
        The templateData must contain all components as any components not present in
        the template will be deleted.

    :param rig: The rig instance to update with the template.
    :type rig: :class:`zoo.libs.hive.base.rig.Rig`
    :param templateData: The template dict which will override the rigInstance.
    :type templateData: dict
    :param remapData: The remapping between the rig and the template components
    :type remapData: dict
    """
    existingComponents = list(rig.iterComponents())
    hasRig = any(i.hasRig() for i in existingComponents)
    hasPolish = any(i.hasPolished() for i in existingComponents)
    hasSkeleton = any(i.hasSkeleton() for i in existingComponents)

    templateutils.updateRigFromTemplate(rig, templateData, remapData)
    buildGuides(rig)
    autoAlignGuides(list(rig.iterComponents()))
    if hasPolish:
        polishRig(rig)
    elif hasRig:
        buildRigs(rig)
    elif hasSkeleton:
        buildDeform(rig)

    output.displayInfo("Success: {} Updating rig".format(rig.name()))
