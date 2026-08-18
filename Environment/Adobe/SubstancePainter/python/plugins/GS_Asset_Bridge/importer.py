"""Importing assets into the open Painter project."""

import os
import shutil
import tempfile

import substance_painter.logging as sp_log
import substance_painter.project as sp_project
import substance_painter.resource as sp_resource


# Megascans map role -> Painter channel name. Applied only if the project's
# stack actually has that channel; anything unmatched is skipped rather than
# treated as an error, so an unusual project template degrades instead of
# failing.
MAP_TO_CHANNEL = {
    "baseColor":    "BaseColor",
    "normal":       "Normal",
    "roughness":    "Roughness",
    "metallic":     "Metallic",
    "height":       "Height",
    "displacement": "Height",
    "ao":           "AmbientOcclusion",
    "opacity":      "Opacity",
    "specular":     "Specular",
    "emissive":     "Emissive",
}

# Set once we learn which import route this installation accepts, so the
# diagnostic is logged once rather than per texture.
_texture_route = None

# Where every import lands, in the words Painter uses on screen. It rides back
# to the app in the ack and shows in the panel's import log, because an artist
# who cannot see what arrived needs to be told WHERE to look — and on a fresh
# project there is nothing to look at yet: Painter only grows a Session entry in
# the Assets shelf once something has been imported into it, so the first import
# of a session lands somewhere that did not exist a moment earlier.
SHELF_NAME = "Session shelf"


def _import_resource(path, usage):
    """Import into the SESSION shelf. Always.

    Where an import landed used to depend on which route happened to work.
    Textures were requested as PROJECT resources with a session import kept as
    a last-resort fallback, so a map that Painter refused twice quietly arrived
    in a different tab than the ones before it — and `_texture_route` then made
    that choice sticky for the rest of the session, so from the first awkward
    asset onward everything moved to the session shelf. Two exports of the same
    material could therefore land in two different places, which reads as the
    app losing someone's work rather than as a fallback doing its job.

    Session is also the right one of the two to settle on: browsing a library
    should not write entries into whatever project the artist has open, and a
    shelf entry that expires with the session is the cheaper mistake to make.
    """
    return sp_resource.import_session_resource(path, usage)


def _is_network_path(path):
    return path.startswith("\\\\") or path.startswith("//")


def _stage_locally(path):
    """Copy a texture to a local temp file and return the new path."""
    staging = os.path.join(tempfile.gettempdir(), "gs-asset-bridge")
    os.makedirs(staging, exist_ok=True)
    local = os.path.join(staging, os.path.basename(path))
    # Re-copying a 30-50 MB 8K map on every import would be wasteful; trust an
    # existing copy of the same size.
    if not (os.path.isfile(local) and os.path.getsize(local) == os.path.getsize(path)):
        shutil.copy2(path, local)
    return local


def import_texture(path):
    """Import a bitmap for use in a channel.

    Painter will not import a resource straight off a UNC share. It fails with

        Resource '<unc path>' is incompatible with usage 'texture'

    which is a misleading message — the usage is correct per the API docs, and
    the same file imports fine once copied locally. (.sbsar files are staged for
    a related reason: Painter locks whatever it opens.)

    So network paths are staged first and local paths imported directly, which
    is the cheap order in both cases: staging costs a 30-50 MB copy per map at
    8K, and is pointless for a file that is already local. Whichever route
    succeeds is logged once and tried first thereafter.

    Both routes import into the same place — see _import_resource. The route
    decides where the file is READ from, never which shelf it lands on; those
    two were tangled together, and that is what made the destination vary.
    """
    global _texture_route

    direct  = ("direct",  lambda: _import_resource(path, sp_resource.Usage.TEXTURE))
    staged  = ("staged",  lambda: _import_resource(_stage_locally(path), sp_resource.Usage.TEXTURE))

    attempts = [staged, direct] if _is_network_path(path) else [direct, staged]

    # Once a route is known to work here, go straight to it.
    if _texture_route is not None:
        attempts.sort(key=lambda a: a[0] != _texture_route)

    errors = []
    for name, attempt in attempts:
        try:
            resource = attempt()
            if _texture_route != name:
                _texture_route = name
                sp_log.info("[GS Asset Bridge] texture import route: %s" % name)
            return resource
        except Exception as exc:
            errors.append("%s: %s" % (name, exc))

    raise RuntimeError(" | ".join(errors))


def _import_sbsar(message):
    path = message.get("path", "")
    if not os.path.isfile(path):
        return {"status": "error", "error": "FILE_NOT_FOUND", "detail": path}

    resource = _import_resource(path, sp_resource.Usage.BASE_MATERIAL)
    # The resource identifier is for the log, not for the artist: what they need
    # from this line is which shelf to open.
    sp_log.info("[GS Asset Bridge] imported %s" % resource)
    return {"status": "ok", "detail": "in the %s" % SHELF_NAME}


def _build_fill_layer(sp_ls, position, label, resources, channels):
    """Insert a fill layer and bind each map to its channel.

    Contains only layerstack MODIFICATIONS, so it is safe to call inside a
    ScopedModification. `channels` is passed in because querying the stack from
    within a scoped edit is rejected.
    """
    fill = sp_ls.insert_fill(position)
    fill.set_name(label)

    applied = 0
    for role, resource in resources.items():
        channel_name = MAP_TO_CHANNEL.get(role)
        if not channel_name:
            continue
        channel = getattr(sp_ls.ChannelType, channel_name, None)
        # Probing beats assuming: a project template without, say, a Height
        # channel should skip it rather than abort the whole import.
        if channel is None or (channels and channel not in channels):
            continue
        try:
            fill.set_source(channel, resource.identifier())
            applied += 1
        except Exception as exc:
            sp_log.warning("[GS Asset Bridge] channel %s: %s" % (channel_name, exc))

    return fill, applied


def _import_megascans(message):
    """Import Megascans maps, optionally wiring them into a new fill layer."""
    maps = message.get("maps") or {}
    if not maps:
        return {"status": "error", "error": "NO_MAPS"}

    label = message.get("label") or "Megascans asset"
    mode = message.get("mode", "layer")

    missing = [role for role, p in maps.items() if not os.path.isfile(p)]
    if len(missing) == len(maps):
        return {"status": "error", "error": "FILE_NOT_FOUND", "detail": ", ".join(missing[:3])}

    # Always land the textures in the shelf; that alone is the "shelf" mode.
    resources = {}
    failures = []
    for role, path in maps.items():
        if not os.path.isfile(path):
            continue
        try:
            resources[role] = import_texture(path)
        except Exception as exc:
            failures.append(role)
            sp_log.warning("[GS Asset Bridge] could not import %s: %s" % (role, exc))

    if not resources:
        return {
            "status": "error",
            "error": "IMPORT_FAILED",
            "detail": "no textures could be imported (%d attempted)" % len(maps),
        }

    partial = " (%d failed)" % len(failures) if failures else ""

    if mode != "layer":
        return {
            "status": "ok",
            "detail": "%d textures in the %s%s" % (len(resources), SHELF_NAME, partial),
        }

    # -- fill layer --------------------------------------------------------
    try:
        import substance_painter.layerstack as sp_ls
        import substance_painter.textureset as sp_ts
    except ImportError:
        return {
            "status": "ok",
            "detail": "textures in the %s (layer API unavailable)" % SHELF_NAME,
        }

    try:
        stack = sp_ts.get_active_stack()

        # Queried BEFORE opening a ScopedModification. Inside one, nothing is
        # computed until the block exits, so reads of stack state are rejected
        # with "This method can't be called from a ScopedModification".
        channels = set(stack.all_channels().keys())
        position = sp_ls.InsertPosition.from_textureset_stack(stack)

        # ScopedModification collapses the build into one undo entry and one
        # texture recompute instead of one per channel. It is an optimisation,
        # never a requirement: if this version rejects any call we make inside
        # it, redo the build without it rather than losing the layer.
        scope = getattr(sp_ls, "ScopedModification", None)
        fill = None
        if scope is not None:
            try:
                with scope("Import %s" % label):
                    fill, applied = _build_fill_layer(sp_ls, position, label, resources, channels)
            except Exception as exc:
                sp_log.warning(
                    "[GS Asset Bridge] grouped edit rejected (%s); rebuilding ungrouped" % exc)
                fill = None

        if fill is None:
            fill, applied = _build_fill_layer(sp_ls, position, label, resources, channels)

        # Selection is a UI action, not a layerstack edit — kept outside the
        # scope for the same reason as the channel query.
        try:
            sp_ls.set_selected_nodes([fill])
        except Exception:
            pass

        return {"status": "ok", "detail": "fill layer with %d channels%s" % (applied, partial)}
    except Exception as exc:
        # The textures are in the shelf regardless, so this is a partial success.
        sp_log.warning("[GS Asset Bridge] fill layer failed: %s" % exc)
        return {
            "status": "ok",
            "detail": "textures in the %s (layer build failed)" % SHELF_NAME,
        }


def handle_request(message):
    """Runs on Painter's main thread. Returns an ack describing what happened."""
    if not sp_project.is_open():
        return {"status": "error", "error": "NO_PROJECT"}

    kind = message.get("kind", "sbsar")
    try:
        if kind == "megascans":
            return _import_megascans(message)
        return _import_sbsar(message)
    except Exception as exc:
        sp_log.error("[GS Asset Bridge] import failed: %s" % exc)
        return {"status": "error", "error": "IMPORT_FAILED", "detail": str(exc)}
