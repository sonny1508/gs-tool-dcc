"""Policy for Blender's online extensions platform (Blender 4.2+).

One repository, two routes. The studio proxy is only a mirror of
extensions.blender.org for workstations without internet, so it is a *URL* on
the stock ``blender_org`` repository rather than a repository of its own. The
module id and folder stay the same on either route, so installed extensions
keep their ``bl_ext.blender_org.*`` ids and keep loading wherever the machine is.

Every launch:
  * At startup-script register time, before Blender loads any extension:
      - "Allow Online Access" is on.
      - ``blender_org`` exists, is enabled, remote, with "Check for Updates on
        Startup" on.
      - Any other repo serving the same content (the separate proxy repo older
        versions of this policy created, or a re-added copy) is merged into it.
  * In a background thread: a TCP connect to the proxy. Reachable -> the repo
    points at the proxy; not -> at extensions.blender.org. Off the studio network
    that is plain stock Blender.

``GS_EXTENSIONS_PROXY_URL`` overrides the proxy; set it empty to never probe and
always go direct. Blender 3.6 has no extensions platform; this is a no-op there.
"""

import os
import shutil
import socket
import threading
import time
from urllib.parse import urlsplit

import bpy

OFFICIAL_URL = "https://extensions.blender.org/api/v1/extensions/"
PROXY_URL = os.environ.get(
    "GS_EXTENSIONS_PROXY_URL", "http://extension-proxy.local/api/v1/extensions/"
).strip()

# Stock module id of the extensions.blender.org repository.
REPO_MODULE = "blender_org"
# The separate proxy repository earlier versions of this policy created.
LEGACY_PROXY_MODULE = "extension_proxy_local"

PROBE_TIMEOUT = 3.0
# The socket timeout doesn't bound DNS: with the DNS server down a lookup can
# stall for ~10 s. Stop waiting after this and go direct.
PROBE_DEADLINE = 15.0
PROBE_POLL = 0.1

PKG_MANIFEST = "blender_manifest.toml"

_route_check = None


def _url_key(url):
    return url.strip().rstrip("/").lower()


def _host(url):
    try:
        return (urlsplit(url.strip()).hostname or "").lower()
    except ValueError:
        return ""


def _route_urls():
    return [url for url in (PROXY_URL, OFFICIAL_URL) if _host(url)]


def _set(obj, attr, value):
    """Assign only when different. Returns True if the value changed.

    Repository properties fire Blender's extension-repo update handlers on every
    write (add-on reloads etc.), so no-op writes are skipped.
    """
    if getattr(obj, attr) == value:
        return False
    setattr(obj, attr, value)
    return True


def _find_repo(repos):
    for repo in repos:
        if repo.module == REPO_MODULE:
            return repo
    return None


# -----------------------------------------------------------------------------
# Before extensions load


def _ensure_online_access(prefs):
    if bpy.app.online_access_override:
        # Launched with --offline-mode / --online-mode: the preference is
        # read-only for this session and the command line wins anyway.
        print("[GS Pipeline] Online access is forced from the command line; leaving it.")
        return False
    if _set(prefs.system, "use_online_access", True):
        print("[GS Pipeline] Enabled 'Allow Online Access'.")
        return True
    return False


def _ensure_repo(repos):
    """Create or repair the one repository. Returns ``(repo, changed)``."""
    repo = _find_repo(repos)
    changed = False
    if repo is None:
        repo = repos.new(name=_host(OFFICIAL_URL), module=REPO_MODULE, remote_url=OFFICIAL_URL)
        changed = True
        print(f"[GS Pipeline] Added extension repository: {repo.name}")

    # Either route is fine until the probe settles it; anything else is reset.
    route_keys = {_url_key(url) for url in _route_urls()}
    if _url_key(repo.remote_url) not in route_keys:
        changed |= _set(repo, "remote_url", OFFICIAL_URL)

    for attr, value in (
        ("name", _host(repo.remote_url)),
        ("use_remote_url", True),
        ("use_sync_on_startup", True),
        ("enabled", True),
    ):
        if _set(repo, attr, value):
            changed = True
            print(f"[GS Pipeline] Reset extension repository '{attr}' to {value!r}")
    return repo, changed


def _move_packages(prefs, src, dst):
    """Move ``src``'s installed extensions into ``dst`` and carry their add-on
    entries (enabled state + add-on preferences) over.

    Returns False if any package couldn't be moved.
    """
    ok = True
    src_dir, dst_dir = src.directory, dst.directory
    if os.path.isdir(src_dir):
        with os.scandir(src_dir) as it:
            entries = list(it)
        for entry in entries:
            if entry.name.startswith(".") or not os.path.isfile(os.path.join(entry.path, PKG_MANIFEST)):
                continue
            target = os.path.join(dst_dir, entry.name)
            if os.path.exists(target):
                continue  # Already installed in dst; that copy wins.
            try:
                os.makedirs(dst_dir, exist_ok=True)
                shutil.move(entry.path, target)
            except OSError as e:
                print(f"[GS Pipeline] Could not move extension {entry.name}: {e}")
                ok = False

    src_prefix = f"bl_ext.{src.module}."
    dst_prefix = f"bl_ext.{dst.module}."
    for addon in [a for a in prefs.addons if a.module.startswith(src_prefix)]:
        pkg = addon.module[len(src_prefix):]
        if not os.path.isdir(os.path.join(dst_dir, pkg)):
            continue  # Not moved; stays with src.
        if dst_prefix + pkg in prefs.addons:
            prefs.addons.remove(addon)
        else:
            addon.module = dst_prefix + pkg
    return ok


def _merge_duplicates(prefs, keep):
    """Fold every other repo serving the same content into ``keep``."""
    repos = prefs.extensions.repos
    route_hosts = {_host(url) for url in _route_urls()}
    keep_ptr = keep.as_pointer()
    duplicates = [
        repo for repo in repos
        if repo.as_pointer() != keep_ptr
        and (repo.module == LEGACY_PROXY_MODULE or _host(repo.remote_url) in route_hosts)
    ]

    changed = False
    for repo in duplicates:
        name = repo.name
        if not repo.use_custom_directory and _move_packages(prefs, repo, keep):
            repos.remove(repo)
            changed = True
            print(f"[GS Pipeline] Merged extension repository '{name}' into '{keep.name}'")
        elif _set(repo, "enabled", False):
            # Custom folder (may be shared or hand-managed, so its files are left
            # alone), or a move failed and the merge is retried next launch.
            changed = True
            print(f"[GS Pipeline] Disabled duplicate extension repository '{name}'")
    return changed


def _apply_before_load(prefs):
    changed = _ensure_online_access(prefs)
    repo, repo_changed = _ensure_repo(prefs.extensions.repos)
    changed |= repo_changed
    changed |= _merge_duplicates(prefs, repo)
    return changed


# -----------------------------------------------------------------------------
# Route check


class _RouteCheck:
    """Probe the proxy off the main thread; apply the result on it."""

    def __init__(self, changed):
        self.changed = changed  # Edits made before load, still to be saved.
        self.route = None       # URL once known, "" to leave the route alone.
        self.deadline = time.monotonic() + PROBE_DEADLINE

    def probe(self):
        # Worker thread: no bpy access here.
        parts = urlsplit(PROXY_URL)
        try:
            port = parts.port or (443 if parts.scheme == "https" else 80)
            with socket.create_connection((parts.hostname, port), timeout=PROBE_TIMEOUT):
                pass
            self.route = PROXY_URL
        except (OSError, ValueError):
            self.route = OFFICIAL_URL

    def finish(self):
        # Main-thread timer: polls until the probe answers or the deadline passes.
        route = self.route
        if route is None:
            if time.monotonic() < self.deadline:
                return PROBE_POLL
            route = OFFICIAL_URL
            print("[GS Pipeline] Extension proxy check timed out.")

        changed = self.changed
        try:
            if route:
                print(f"[GS Pipeline] Extensions route: {route}")
                repo = _find_repo(bpy.context.preferences.extensions.repos)
                if repo is not None:
                    changed |= _set(repo, "remote_url", route)
                    changed |= _set(repo, "name", _host(route))
            if changed:
                bpy.ops.wm.save_userpref()
                print("[GS Pipeline] Preferences saved (extensions).")
        except Exception as e:
            print(f"[GS Pipeline] Failed to apply extensions route: {e}")
        return None


def register():
    """Run from the startup script's register(), i.e. before extensions load."""
    global _route_check
    prefs = bpy.context.preferences
    if not hasattr(prefs, "extensions"):
        return

    try:
        changed = _apply_before_load(prefs)
    except Exception as e:  # never let this break Blender startup
        print(f"[GS Pipeline] Failed to apply extensions policy: {e}")
        changed = False

    check = _RouteCheck(changed)
    if bpy.app.online_access_override and not bpy.app.online_access:
        check.route = ""  # --offline-mode: keep off the network entirely.
    elif not _host(PROXY_URL):
        check.route = OFFICIAL_URL  # No proxy configured.
    else:
        threading.Thread(target=check.probe, name="gs-extensions-probe", daemon=True).start()

    # Keep the bound method: timers are matched by object identity. Persistent,
    # or a .blend opened at launch would drop it before it ever runs.
    _route_check = check.finish
    bpy.app.timers.register(_route_check, first_interval=0.0, persistent=True)


def unregister():
    global _route_check
    if _route_check is not None and bpy.app.timers.is_registered(_route_check):
        bpy.app.timers.unregister(_route_check)
    _route_check = None
