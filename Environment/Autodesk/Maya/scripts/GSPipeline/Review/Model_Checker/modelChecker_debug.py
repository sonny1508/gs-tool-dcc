"""Debug views for the Model Checker: ways of drawing the viewport, not checks.

A view changes how Viewport 2.0 draws and never touches the scene. No shader is
assigned, no attribute is set, nothing is created. So a view can't be saved into
a file, undone by accident, seen by a check or removed by the Cleanup, and it
works the same on referenced meshes. The views are drawn by one render override,
which the model panels are switched to while a view is on.

One view is on at a time, and it covers every mesh in every model panel. There
is nothing kept per object or per selection, so nothing can be left behind on a
mesh and forgotten.

Face Orientation draws the front of every face blue and the back red, as
Blender's overlay of that name does. Which side is which comes from the order of
the face's corners, the same thing a game engine culls by - not from the
normals, which can be locked or soft and point anywhere.

Locked Normals draws the scene grey and every face with a locked normal orange
over it, see-through enough that the shading those normals give still shows.

This module lives on in sys.modules while the window is opened and closed
again, so its state is the one record of what is on.
"""

import traceback

import maya.cmds as cmds
import maya.api.OpenMaya as om
import maya.api.OpenMayaRender as omr

OVERRIDE_NAME = "gsModelCheckerDebug"
VIEWPORT_2 = "vp2Renderer"

# Blender's face orientation colours, RGBA
FRONT_COLOUR = [0.2, 0.4, 1.0, 1.0]
BACK_COLOUR = [1.0, 0.1, 0.1, 1.0]

# Locked Normals: a lit grey under a see-through orange
BASE_GREY = [0.5, 0.5, 0.5, 1.0]
LOCKED_COLOUR = [1.0, 0.45, 0.0, 0.6]

# The views this module can draw, with the line shown in the viewport as each
# is switched on. The window's labels and tooltips are in modelChecker_list.
VIEW_MESSAGES = {
    "faceOrientation": "Face Orientation <hl>on</hl>. Blue: front. Red: back.",
    "lockMap": "Locked Normals <hl>on</hl>. Orange: locked normals.",
}
NO_LOCKS_MESSAGE = "Locked Normals <hl>on</hl>. No locked normals in the scene."

_state = {
    "view": None,        # the view that is on
    "override": None,    # the registered render override, while a view is on
    "panels": {},        # model panel -> (renderer, override) it had before
    "suspended": False,  # panels handed back for the length of a save
    "lockMap": None,     # the faces Locked Normals draws, while it is on
    "callbacks": [],     # scene message callback ids, kept for the session
    "listeners": [],     # called with no arguments when the view changes
}


class _ColourPass(omr.MSceneRender):
    """Draw every face in one colour: all of each face, or only its front or back."""

    def __init__(self, name, colour, culling, lit, clear):
        omr.MSceneRender.__init__(self, name)
        self.colour = colour
        self.culling = culling
        self.lit = lit
        self.clearMask = (
            omr.MClearOperation.kClearColor | omr.MClearOperation.kClearDepth
            | omr.MClearOperation.kClearStencil) if clear else omr.MClearOperation.kClearNone
        self.shader = None

    def shaderOverride(self):
        if self.shader is None:
            manager = omr.MRenderer.getShaderManager()
            if manager is None:
                return None
            # Lit, the shape still reads. A back face is left flat, since its
            # normal points away from the light and would go black
            if self.lit:
                self.shader = manager.getStockShader(omr.MShaderManager.k3dBlinnShader)
                parameter = "diffuseColor"
            else:
                self.shader = manager.getStockShader(omr.MShaderManager.k3dSolidShader)
                parameter = "solidColor"
            if self.shader is not None:
                self.shader.setParameter(parameter, self.colour)
        return self.shader

    def releaseShader(self):
        if self.shader is not None:
            manager = omr.MRenderer.getShaderManager()
            if manager is not None:
                manager.releaseShader(self.shader)
            self.shader = None

    def renderFilterOverride(self):
        return omr.MSceneRender.kRenderShadedItems

    def cullingOverride(self):
        return self.culling

    def displayModeOverride(self):
        # Shaded even in a wireframe panel, or there would be nothing to colour
        return omr.MSceneRender.kShaded

    def lightModeOverride(self):
        return omr.MSceneRender.kLightDefault

    def clearOperation(self):
        operation = self.mClearOperation
        operation.setMask(self.clearMask)
        return operation


class _ScenePass(omr.MSceneRender):
    """Draw the scene as the panel would, or only its UI on top of earlier
    passes. `drawer`, when given, is called with a MUIDrawManager to add
    shapes of its own under that UI."""

    def __init__(self, name, uiOnly, drawer=None):
        omr.MSceneRender.__init__(self, name)
        self.uiOnly = uiOnly
        self.drawer = drawer

    def renderFilterOverride(self):
        if self.uiOnly:
            return omr.MSceneRender.kRenderUIItems
        return omr.MSceneRender.kNoSceneFilterOverride

    def clearOperation(self):
        operation = self.mClearOperation
        if self.uiOnly:
            operation.setMask(omr.MClearOperation.kClearNone)
        return operation

    def hasUIDrawables(self):
        return self.drawer is not None

    def addPreUIDrawables(self, drawManager, frameContext):
        # Before the wireframe, selection and components, which stay on top
        self.drawer(drawManager)


class _DebugOverride(omr.MRenderOverride):
    """The render override that draws whichever view is on."""

    def __init__(self, name):
        omr.MRenderOverride.__init__(self, name)
        self.panel = ""
        self.drawError = False
        self.viewPasses = {
            "faceOrientation": [
                # The back first, so that it wins where a front face lies exactly
                # on it if the depth test is "less"...
                _ColourPass(name + "_back", BACK_COLOUR,
                            omr.MSceneRender.kCullFrontFaces, lit=False, clear=True),
                _ColourPass(name + "_front", FRONT_COLOUR,
                            omr.MSceneRender.kCullBackFaces, lit=True, clear=False),
                # ...and again after the front, so that it wins there if the test
                # is "less or equal". A face pointing inwards can't hide under one
                # pointing outwards either way, and a back face behind the front
                # of the model still fails the depth test both times.
                _ColourPass(name + "_backOnTop", BACK_COLOUR,
                            omr.MSceneRender.kCullFrontFaces, lit=False, clear=False),
                # Wireframe, selection, components and the grid, with no culling
                _ScenePass(name + "_ui", uiOnly=True),
            ],
            "lockMap": [
                # Lit, so that the shading the locked normals give shows through
                _ColourPass(name + "_grey", BASE_GREY,
                            omr.MSceneRender.kNoCullingOverride, lit=True, clear=True),
                _ScenePass(name + "_lockMap", uiOnly=True, drawer=self.drawLockMap),
            ],
        }
        self.plainPasses = [_ScenePass(name + "_scene", uiOnly=False)]
        self.closingPasses = [omr.MHUDRender(), omr.MPresentTarget(name + "_present")]
        self.operations = []
        self.current = -1

    def uiName(self):
        return "Model Checker Debug"

    def supportedDrawAPIs(self):
        return omr.MRenderer.kAllDevices

    def setup(self, destination):
        # The panel about to be drawn, for its Isolate Select and Show menu
        self.panel = destination

    def drawLockMap(self, drawManager):
        lockMap = _state["lockMap"]
        if lockMap is None:
            return
        try:
            lockMap.draw(drawManager, self.panel)
        except Exception:
            # Once, rather than at every redraw
            if not self.drawError:
                self.drawError = True
                traceback.print_exc()

    def startOperationIterator(self):
        passes = self.viewPasses.get(_state["view"], self.plainPasses)
        self.operations = passes + self.closingPasses
        self.current = 0
        return True

    def renderOperation(self):
        if 0 <= self.current < len(self.operations):
            return self.operations[self.current]
        return None

    def nextRenderOperation(self):
        self.current += 1
        return self.current < len(self.operations)

    def releaseShaders(self):
        for passes in self.viewPasses.values():
            for operation in passes:
                if isinstance(operation, _ColourPass):
                    operation.releaseShader()


# Locked Normals
def _lockedTriangles(mesh):
    """The corners of the triangles of every face with a locked normal, as
    vertex ids for MUIDrawManager.mesh(), or None when no normal is locked. A
    face counts when any one of its corners is locked."""
    isLocked = mesh.isNormalLocked
    locked = [isLocked(normal) for normal in range(mesh.numNormals)]
    if not any(locked):
        return None
    triangleCounts, triangleVertices = mesh.getTriangles()
    if all(locked):
        return om.MUintArray(list(triangleVertices))

    normalCounts, normalIds = mesh.getNormalIds()
    cornerLocked = [locked[normal] for normal in normalIds]
    vertices = list(triangleVertices)
    corners = []
    corner = triangle = 0
    for cornerCount, triangleCount in zip(normalCounts, triangleCounts):
        if any(cornerLocked[corner:corner + cornerCount]):
            corners.extend(vertices[triangle * 3:(triangle + triangleCount) * 3])
        corner += cornerCount
        triangle += triangleCount
    return om.MUintArray(corners) if corners else None


def _meshesShown(panel):
    """Which meshes `panel` draws: False for none (Show > Polygons is off), the
    long names of what Isolate Select shows, or None for every visible one."""
    if not panel:
        return None
    try:
        if not cmds.modelEditor(panel, query=True, polymeshes=True):
            return False
        if not cmds.isolateSelect(panel, query=True, state=True):
            return None
        viewSet = cmds.isolateSelect(panel, query=True, viewObjects=True)
        members = cmds.sets(viewSet, query=True) if viewSet else None
        # Never ls() with nothing, which lists the whole scene
        if not members:
            return []
        return cmds.ls(members, long=True, objectsOnly=True) or []
    except (RuntimeError, TypeError, ValueError):
        # Not a model panel: a playblast or another renderer
        return None


def _shownPoints(path, isolated):
    """The world space points of the mesh at `path`, or None if it isn't drawn."""
    try:
        if not path.isValid() or not path.isVisible():
            return None
        if isolated is not None:
            name = path.fullPathName()
            if not any(name == root or name.startswith(root + "|") for root in isolated):
                return None
        return om.MFnMesh(path).getPoints(om.MSpace.kWorld)
    except RuntimeError:
        return None


class _MeshLocks(object):
    """One mesh's locked faces, as the lock map last worked them out."""

    __slots__ = ("handle", "callback", "corners", "vertexCount", "stale")

    def __init__(self, handle):
        self.handle = handle
        self.callback = None
        self.corners = None
        self.vertexCount = 0
        self.stale = True

    def update(self):
        self.stale = False
        self.corners = None
        if not self.handle.isValid():
            return
        node = self.handle.object()
        try:
            # The hidden original under a deformed mesh is never drawn
            if om.MFnDependencyNode(node).findPlug("intermediateObject", False).asBool():
                return
            mesh = om.MFnMesh(node)
            self.corners = _lockedTriangles(mesh)
            self.vertexCount = mesh.numVertices
        except RuntimeError:
            # A mesh still being built: it gets its data, and a dirty message, later
            self.corners = None

    def paths(self):
        """Every instance of the mesh, found again at each draw so that one
        moved to another parent is still drawn."""
        if self.corners is None or not self.handle.isValid():
            return []
        try:
            return om.MDagPath.getAllPathsTo(self.handle.object())
        except RuntimeError:
            return []


class _LockMap(object):
    """The faces with a locked normal, in every mesh of the scene, kept up to
    date while Locked Normals is on.

    Working the faces out takes a moment on a big mesh. So it is done for the
    whole scene once, when the view goes on, and after that for one mesh at a
    time, when Maya is next idle after that mesh changes. The points are read
    at every draw instead, which is quick, so the map follows a model as it
    moves."""

    def __init__(self):
        self.meshes = {}  # MObjectHandle hash -> _MeshLocks
        self.callbacks = []
        self.running = False
        self.updatePending = False
        self.outMesh = om.MNodeClass("mesh").attribute("outMesh")

    def start(self):
        self.running = True
        self.callbacks = [
            om.MDGMessage.addNodeAddedCallback(self._meshAdded, "mesh"),
            om.MDGMessage.addNodeRemovedCallback(self._meshRemoved, "mesh"),
        ]
        meshes = om.MItDependencyNodes(om.MFn.kMesh)
        while not meshes.isDone():
            self._watch(meshes.thisNode())
            meshes.next()
        cmds.waitCursor(state=True)
        try:
            self._update()
        finally:
            cmds.waitCursor(state=False)

    def stop(self):
        self.running = False
        for entry in self.meshes.values():
            _removeCallback(entry.callback)
        for callback in self.callbacks:
            _removeCallback(callback)
        self.meshes = {}
        self.callbacks = []

    def hasLocks(self):
        return any(entry.corners is not None for entry in self.meshes.values())

    def draw(self, drawManager, panel):
        isolated = _meshesShown(panel)
        if isolated is False:
            return
        drawManager.beginDrawable(omr.MUIDrawManager.kNonSelectable)
        drawManager.setColor(om.MColor(LOCKED_COLOUR))
        # Over the grey of the same faces, which lies at exactly the same depth
        drawManager.setDepthPriority(omr.MRenderItem.sDormantWireDepthPriority)
        for entry in self.meshes.values():
            # Every instance draws the same faces, each in its own place
            for path in entry.paths():
                points = _shownPoints(path, isolated)
                # A mesh that lost or gained points since it was worked out
                # would draw the wrong ones; it is worked out again shortly
                if points is not None and len(points) == entry.vertexCount:
                    drawManager.mesh(omr.MUIDrawManager.kTriangles, points,
                                     None, None, entry.corners)
        drawManager.endDrawable()

    # Keeping up with the scene
    def _watch(self, node):
        handle = om.MObjectHandle(node)
        key = handle.hashCode()
        entry = self.meshes.get(key)
        if entry is not None:
            entry.stale = True
            return
        entry = _MeshLocks(handle)
        entry.callback = om.MNodeMessage.addNodeDirtyPlugCallback(node, self._meshDirty, key)
        self.meshes[key] = entry

    def _meshAdded(self, node, *_):
        self._watch(node)
        self._scheduleUpdate()

    def _meshRemoved(self, node, *_):
        entry = self.meshes.pop(om.MObjectHandle(node).hashCode(), None)
        if entry is not None:
            _removeCallback(entry.callback)

    def _meshDirty(self, node, plug, key):
        # outMesh carries every change to the mesh's data, normals included,
        # however it was made. Moving the object doesn't touch it
        if not plug.attribute() == self.outMesh:
            return
        entry = self.meshes.get(key)
        if entry is not None and not entry.stale:
            entry.stale = True
            self._scheduleUpdate()

    def _scheduleUpdate(self):
        if self.running and not self.updatePending:
            self.updatePending = True
            cmds.evalDeferred(self._deferredUpdate, lowestPriority=True)

    def _deferredUpdate(self):
        self.updatePending = False
        if self.running:
            self._update()
            _refresh()

    def _update(self):
        for entry in list(self.meshes.values()):
            if entry.stale:
                entry.update()


def _removeCallback(callback):
    if callback is None:
        return
    try:
        om.MMessage.removeCallback(callback)
    except RuntimeError:
        pass


# Switching the panels
def _register():
    """Register the override under its name, replacing one left behind by an
    earlier copy of this module."""
    try:
        old = omr.MRenderer.findRenderOverride(OVERRIDE_NAME)
    except Exception:
        old = None
    if old is not None:
        omr.MRenderer.deregisterOverride(old)
    override = _DebugOverride(OVERRIDE_NAME)
    omr.MRenderer.registerOverride(override)
    return override


def _deregister(override):
    override.releaseShaders()
    try:
        omr.MRenderer.deregisterOverride(override)
    except Exception:
        traceback.print_exc()


def _takePanels():
    """Point every model panel at the override, remembering what each had."""
    panels = {}
    for panel in cmds.getPanel(type="modelPanel") or []:
        try:
            renderer = cmds.modelEditor(panel, query=True, rendererName=True)
            override = cmds.modelEditor(panel, query=True, rendererOverrideName=True)
            cmds.modelEditor(panel, edit=True, rendererName=VIEWPORT_2,
                             rendererOverrideName=OVERRIDE_NAME)
        except RuntimeError:
            continue
        panels[panel] = (renderer, override or "")
    return panels


def _returnPanels(panels):
    """Give each panel back the renderer it had."""
    for panel, (renderer, override) in panels.items():
        try:
            if cmds.modelPanel(panel, exists=True):
                cmds.modelEditor(panel, edit=True, rendererName=renderer,
                                 rendererOverrideName=override)
        except RuntimeError:
            pass


def _refresh():
    try:
        cmds.refresh(force=True)
    except RuntimeError:
        pass


def _notify():
    for listener in list(_state["listeners"]):
        try:
            listener()
        except Exception:
            # A window that was closed without saying so
            traceback.print_exc()
            removeListener(listener)


# Keeping the scene file clean
def _beforeSave(*_):
    """The panels' renderers are saved with the scene, and a file must never
    open asking for an override that may not be there. Hand them back for the
    save, and take them again once it's written."""
    if _state["override"] is not None and not _state["suspended"]:
        _returnPanels(_state["panels"])
        _state["suspended"] = True


def _afterSave(*_):
    if _state["override"] is not None and _state["suspended"]:
        _state["panels"] = _takePanels()
        _state["suspended"] = False


def _beforeSceneChange(*_):
    """A new or opened scene rebuilds the panels, so turn the view off first."""
    turnAllOff()


def _addCallbacks():
    """Listen for saves and scene changes, once for the session. They do nothing
    while no view is on, and are never removed: one of them turns the view off,
    and a callback shouldn't remove itself while it runs."""
    if _state["callbacks"]:
        return
    messages = (
        (om.MSceneMessage.kBeforeSave, _beforeSave),
        (om.MSceneMessage.kAfterSave, _afterSave),
        (om.MSceneMessage.kBeforeNew, _beforeSceneChange),
        (om.MSceneMessage.kBeforeOpen, _beforeSceneChange),
        (om.MSceneMessage.kMayaExiting, _beforeSceneChange),
    )
    _state["callbacks"] = [om.MSceneMessage.addCallback(message, function)
                           for message, function in messages]


# What the window calls
def isOn(view):
    return _state["view"] == view


def setView(view, on):
    """Switch one view on or off. Switching one on switches off the one that
    was on. The panels follow: switched to the override with the first view on,
    and given back when the last goes off."""
    if view not in VIEW_MESSAGES or on == isOn(view):
        return
    if not on:
        turnAllOff()
        return

    _stopLockMap()
    _state["view"] = None
    if _state["override"] is None:
        _state["override"] = _register()
        _state["panels"] = _takePanels()
        _state["suspended"] = False
        _addCallbacks()

    message = VIEW_MESSAGES[view]
    try:
        if view == "lockMap":
            lockMap = _LockMap()
            _state["lockMap"] = lockMap
            lockMap.start()
            if not lockMap.hasLocks():
                message = NO_LOCKS_MESSAGE
    except Exception:
        turnAllOff()
        raise
    _state["view"] = view

    cmds.inViewMessage(assistMessage=message, position="topCenter",
                       fade=True, fadeStayTime=2500, fadeOutTime=500)
    _refresh()
    _notify()


def turnAllOff():
    """Switch the view off and give the panels back their renderers."""
    if _state["view"] is None and _state["override"] is None:
        return
    _state["view"] = None
    _stopLockMap()
    _shutDown()
    _refresh()
    _notify()


def _stopLockMap():
    lockMap = _state["lockMap"]
    _state["lockMap"] = None
    if lockMap is not None:
        lockMap.stop()


def _shutDown():
    override = _state["override"]
    if override is None:
        return
    if not _state["suspended"]:
        _returnPanels(_state["panels"])
    _state["panels"] = {}
    _state["suspended"] = False
    _state["override"] = None
    _deregister(override)


def addListener(listener):
    if listener not in _state["listeners"]:
        _state["listeners"].append(listener)


def removeListener(listener):
    if listener in _state["listeners"]:
        _state["listeners"].remove(listener)
