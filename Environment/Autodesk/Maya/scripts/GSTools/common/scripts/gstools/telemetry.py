"""
GSTools - Telemetry

Single chokepoint for "a tool was launched" events. Every GSTools menu item and
shelf button is dispatched through gstools.launch(), which calls log_launch()
here, so this stays the ONE place that knows anything about usage reporting.

Design constraints, in priority order
-------------------------------------
1. NEVER slow down or destabilise a Maya session.
   log_launch() only builds a dict and does a non-blocking Queue.put_nowait().
   Every DNS lookup, socket connect and HTTP round trip happens on a daemon
   worker thread. A dead server, a black-holed IP or broken DNS costs the artist
   nothing - the worker eats the timeout, never the UI.

2. DEGRADE TO NOTHING off the studio LAN.
   The suite is used outside the studio. If GS_TELEMETRY_URL is unset, this
   module is inert: no worker thread is ever created and no socket is ever
   opened. The studio deploy sets the var in Maya.env; a copy used anywhere
   else simply doesn't have it.

3. DON'T COMPETE WITH PERFORCE for bandwidth.
   Events are batched and share a single copy of the session context, so a busy
   workstation is a few KB/hour. See _post() for why the payload is deliberately
   NOT compressed.

Configuration (environment, normally set in each version's Maya.env)
--------------------------------------------------------------------
    GS_TELEMETRY_URL       collector endpoint. ABSENT => fully disabled.
    GS_TELEMETRY_TOKEN     shared secret, sent as the X-GS-Token header.
    GS_TELEMETRY_DISABLED  kill switch, honoured even when the URL is set.
    GS_TELEMETRY_DEBUG     echo every event to the Script Editor.

Wire format
-----------
POST <url>, Content-Type: application/json, body = one JSON object:

    {"protocol": 1,
     "context": {host, os_user, dcc, dcc_version, suite_version, project,
                 session_id, ...},
     "dropped": <events lost to queue overflow since the last batch>,
     "events":  [{event_id, event_type, ts_utc, tool_id, ...}, ...]}

The context is sent once per batch rather than repeated on every event; the
server fans it back out across the rows. Every event carries a client-generated
uuid4 `event_id` which the server uses as the primary key, so replaying a
spooled batch is idempotent.
"""
import os
import sys
import json
import time
import uuid
import queue
import atexit
import socket
import getpass
import logging
import datetime
import threading
import urllib.request
from urllib.parse import urlparse

logging.basicConfig()
logger = logging.getLogger("gstools.telemetry")
logger.setLevel(logging.INFO)

PROTOCOL_VERSION = 1

ENV_URL = "GS_TELEMETRY_URL"
ENV_TOKEN = "GS_TELEMETRY_TOKEN"
ENV_DISABLED = "GS_TELEMETRY_DISABLED"
ENV_DEBUG = "GS_TELEMETRY_DEBUG"

# --- tunables -----------------------------------------------------------------
QUEUE_MAX = 2000            # events held in memory before we start dropping
BATCH_MAX_EVENTS = 20       # ship early once this many are queued
FLUSH_SECONDS = 30.0        # ...otherwise ship on this interval
HEARTBEAT_SECONDS = 300.0   # liveness ping; bounds the error on session duration
HTTP_TIMEOUT = 3.0
PROBE_TIMEOUT = 0.5         # pre-flight TCP probe, see _reachable()
BACKOFF_START = 30.0
BACKOFF_MAX = 900.0         # 15 min ceiling once the circuit is open
SHUTDOWN_BUDGET = 1.0       # hard cap on how long Maya may wait for us at exit
SPOOL_MAX_BYTES = 5 * 1024 * 1024
SPOOL_MAX_AGE_DAYS = 14

# One id per DCC process. Generated at import, which is cheap and never fails.
SESSION_ID = uuid.uuid4().hex


# ------------------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------------------

_config = None


def _get_config():
    """Read the environment once and cache it. Never raises."""
    global _config
    if _config is None:
        try:
            url = (os.environ.get(ENV_URL) or "").strip()
            disabled = bool((os.environ.get(ENV_DISABLED) or "").strip())
            _config = {
                "url": url,
                "token": (os.environ.get(ENV_TOKEN) or "").strip(),
                "debug": bool((os.environ.get(ENV_DEBUG) or "").strip()),
                "enabled": bool(url) and not disabled,
            }
        except Exception:
            _config = {"url": "", "token": "", "debug": False, "enabled": False}
    return _config


def is_enabled():
    """True if a collector is configured and telemetry hasn't been killed."""
    return _get_config()["enabled"]


# ------------------------------------------------------------------------------
# Session context
# ------------------------------------------------------------------------------

_context = None


def _maya_version():
    try:
        import maya.cmds as cmds
        return cmds.about(version=True)
    except Exception:
        return "unknown"


def _launcher_config_path():
    """Locate launcher_config.ini, which lives at the root of the user's maya
    scripts folder (a sibling of GSTools/ and GSPipeline/).

    Tried in order of decreasing reliability: the GSPIPELINE env var set by
    Maya.env, then walking up from this package, then the conventional profile
    path."""
    candidates = []

    gspipeline = os.environ.get("GSPIPELINE")
    if gspipeline:
        candidates.append(os.path.join(os.path.dirname(gspipeline.rstrip("\\/")),
                                       "launcher_config.ini"))

    # .../maya/scripts/GSTools/common/scripts/gstools -> .../maya/scripts
    here = os.path.dirname(os.path.abspath(__file__))
    candidates.append(os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(here)))),
        "launcher_config.ini"))

    profile = os.environ.get("USERPROFILE") or os.path.expanduser("~")
    candidates.append(os.path.join(profile, "Documents", "maya", "scripts",
                                   "launcher_config.ini"))

    for path in candidates:
        if path and os.path.isfile(path):
            return path
    return None


def _project():
    """Current project name from launcher_config.ini, or "" if unavailable."""
    try:
        import configparser
        path = _launcher_config_path()
        if not path:
            return ""
        parser = configparser.ConfigParser()
        parser.read(path)
        return parser.get("maya_launcher", "project", fallback="") or ""
    except Exception:
        return ""


def _suite_version():
    try:
        import gstools
        return gstools.PACKAGE_VERSION
    except Exception:
        return "unknown"


def _get_context():
    """Build the per-session context once. Never raises."""
    global _context
    if _context is None:
        try:
            _context = {
                "session_id": SESSION_ID,
                "host": socket.gethostname(),
                "os_user": getpass.getuser(),
                "dcc": "maya",
                "dcc_version": _maya_version(),
                "suite_version": _suite_version(),
                "project": _project(),
                "py": "%d.%d" % (sys.version_info[0], sys.version_info[1]),
            }
        except Exception:
            _context = {"session_id": SESSION_ID, "dcc": "maya"}
    return _context


# ------------------------------------------------------------------------------
# Local spool
# ------------------------------------------------------------------------------
#
# Batches we couldn't ship land here as whole envelopes and are retried on the
# next successful connection and at the next Maya boot. Deliberately on LOCAL
# disk, never the NAS: no NAS I/O anywhere near an artist's hot path, and it
# works off-site. Bounded by size and age so a laptop away for a month can't
# fill a disk.

def _spool_dir():
    base = (os.environ.get("LOCALAPPDATA")
            or os.environ.get("TEMP")
            or os.path.expanduser("~"))
    return os.path.join(base, "GSTools", "telemetry", "spool")


def _spool_files():
    """Existing spool files, oldest first. Never raises."""
    try:
        directory = _spool_dir()
        if not os.path.isdir(directory):
            return []
        names = [os.path.join(directory, n) for n in os.listdir(directory)
                 if n.endswith(".json")]
        return sorted(names)
    except Exception:
        return []


def _spool_prune():
    """Drop spool files that are too old, then oldest-first until under the size
    cap."""
    try:
        files = _spool_files()
        cutoff = time.time() - SPOOL_MAX_AGE_DAYS * 86400
        keep = []
        for path in files:
            try:
                if os.path.getmtime(path) < cutoff:
                    os.remove(path)
                else:
                    keep.append(path)
            except Exception:
                pass

        total = 0
        sizes = []
        for path in keep:
            try:
                size = os.path.getsize(path)
            except Exception:
                size = 0
            sizes.append((path, size))
            total += size

        for path, size in sizes:            # oldest first
            if total <= SPOOL_MAX_BYTES:
                break
            try:
                os.remove(path)
                total -= size
            except Exception:
                pass
    except Exception:
        pass


def _spool_write(envelope):
    try:
        directory = _spool_dir()
        if not os.path.isdir(directory):
            os.makedirs(directory)
        _spool_prune()
        name = "%s-%s.json" % (
            datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%S%f"),
            uuid.uuid4().hex[:8],
        )
        with open(os.path.join(directory, name), "w") as handle:
            json.dump(envelope, handle)
    except Exception as exc:
        logger.debug("telemetry spool write failed: %s", exc)


# ------------------------------------------------------------------------------
# Async sink
# ------------------------------------------------------------------------------

class _Sink(object):
    """Owns the queue, the single daemon worker, and the retry state machine."""

    def __init__(self, url, token):
        self._url = url
        self._token = token
        self._queue = queue.Queue(maxsize=QUEUE_MAX)
        self._dropped = 0
        self._lock = threading.Lock()
        self._thread = None
        self._stop = threading.Event()
        self._failures = 0
        self._next_attempt = 0.0        # monotonic; 0 == try immediately
        self._probed_ok = False
        self._succeeded = False         # have we EVER reached the collector?

    # -- producer side (MAIN THREAD - must stay allocation-only) ---------------

    def submit(self, event):
        """Enqueue an event. Non-blocking; drops rather than waits."""
        try:
            self._queue.put_nowait(event)
        except queue.Full:
            with self._lock:
                self._dropped += 1
            return False
        self._ensure_thread()
        return True

    def _ensure_thread(self):
        # Fast, lock-free path for every call after the first.
        if self._thread is not None:
            return
        with self._lock:
            if self._thread is not None:
                return
            thread = threading.Thread(target=self._run, name="gstools-telemetry")
            thread.daemon = True        # Python must never wait on us at exit
            self._thread = thread
            thread.start()

    # -- consumer side (WORKER THREAD - all network lives below here) ----------

    def _run(self):
        try:
            self._retry_spool()
        except Exception:
            pass

        batch = []
        deadline = time.monotonic() + FLUSH_SECONDS
        last_heartbeat = time.monotonic()

        while not self._stop.is_set():
            try:
                timeout = max(0.0, deadline - time.monotonic())
                try:
                    batch.append(self._queue.get(timeout=timeout))
                except queue.Empty:
                    pass

                now = time.monotonic()
                if now - last_heartbeat >= HEARTBEAT_SECONDS:
                    batch.append(_build_event("heartbeat"))
                    last_heartbeat = now

                if len(batch) >= BATCH_MAX_EVENTS or now >= deadline:
                    if batch:
                        self._ship(batch)
                        batch = []
                    deadline = now + FLUSH_SECONDS
            except Exception as exc:
                # A bug in here must not kill the worker or leak into Maya.
                logger.debug("telemetry worker error: %s", exc)
                batch = []
                deadline = time.monotonic() + FLUSH_SECONDS

    def _envelope(self, events):
        with self._lock:
            dropped = self._dropped
            self._dropped = 0
        return {
            "protocol": PROTOCOL_VERSION,
            "context": _get_context(),
            "dropped": dropped,
            "events": events,
        }

    def _ship(self, events):
        """Try to send; spool on any failure. Worker thread only."""
        envelope = self._envelope(events)

        if time.monotonic() < self._next_attempt:
            # Circuit is open - don't even touch the network.
            _spool_write(envelope)
            return

        if not self._reachable():
            self._record_failure()
            _spool_write(envelope)
            return

        try:
            self._post(envelope)
        except Exception as exc:
            logger.debug("telemetry post failed: %s", exc)
            self._record_failure()
            _spool_write(envelope)
            return

        self._record_success()
        self._retry_spool()

    def _reachable(self):
        """Cheap pre-flight TCP probe.

        Two reasons this exists rather than relying on urlopen(timeout=):
          * it turns "server is gone" into a 0.5s answer instead of a full
            connect timeout, so a backoff cycle costs almost nothing;
          * urlopen's timeout does NOT reliably cover DNS resolution on Windows,
            and a hung getaddrinfo here is confined to the worker thread.
        Skipped once we've had a success and the circuit is closed.
        """
        if self._probed_ok and self._failures == 0:
            return True
        parsed = urlparse(self._url)
        host = parsed.hostname
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        if not host:
            return False
        try:
            sock = socket.create_connection((host, port), PROBE_TIMEOUT)
            sock.close()
            self._probed_ok = True
            return True
        except Exception:
            return False

    def _post(self, envelope, timeout=HTTP_TIMEOUT):
        # Plain JSON, deliberately NOT gzipped. Frappe's make_form_dict() does
        #     request_data = request.get_data(as_text=True)
        #     if request_data and request.is_json: args = json.loads(request_data)
        # so a gzipped body under Content-Type: application/json is fed straight
        # into json.loads() and blows up before the endpoint is ever reached.
        # Sending plain JSON means Frappe parses the envelope natively and hands
        # our whitelisted function its keys as kwargs - the idiomatic path, and
        # no dependence on how a given werkzeug version decodes a binary body.
        # The compression was worth ~2 MB/day studio-wide; not worth the risk.
        body = json.dumps(envelope).encode("utf-8")
        request = urllib.request.Request(self._url, data=body, method="POST")
        request.add_header("Content-Type", "application/json")
        if self._token:
            # NB urllib capitalises header names, so this goes out on the wire
            # as "X-gs-token". HTTP header lookup is case-insensitive, so any
            # sane server framework (Frappe/werkzeug included) still finds it -
            # but don't be surprised by the casing when reading a packet dump.
            request.add_header("X-GS-Token", self._token)
        response = urllib.request.urlopen(request, timeout=timeout)
        response.read()
        response.close()

    def _record_failure(self):
        self._failures += 1
        backoff = min(BACKOFF_START * (2 ** (self._failures - 1)), BACKOFF_MAX)
        self._next_attempt = time.monotonic() + backoff

    def _record_success(self):
        self._failures = 0
        self._next_attempt = 0.0
        self._succeeded = True

    def _retry_spool(self):
        """Ship spooled batches oldest-first, stopping at the first failure."""
        for path in _spool_files():
            try:
                with open(path) as handle:
                    envelope = json.load(handle)
            except Exception:
                try:
                    os.remove(path)     # unreadable, don't retry forever
                except Exception:
                    pass
                continue
            try:
                self._post(envelope)
            except Exception:
                self._record_failure()
                return
            try:
                os.remove(path)
            except Exception:
                pass

    # -- shutdown --------------------------------------------------------------

    def shutdown(self):
        """Best-effort final flush, hard-bounded. Called from the main thread at
        Maya exit, so it must be quick and must never raise."""
        try:
            self._stop.set()
            events = []
            while True:
                try:
                    events.append(self._queue.get_nowait())
                except queue.Empty:
                    break
            events.append(_build_event("session_end"))
            envelope = self._envelope(events)

            # Only touch the network at exit if we have ALREADY reached the
            # collector successfully in this session. Otherwise spool and get
            # out of the way.
            #
            # This is what bounds Maya's shutdown. Neither urlopen(timeout=) nor
            # socket.create_connection(timeout=) covers name resolution, so a
            # single getaddrinfo on an unreachable/unresolvable host can block
            # for many seconds - measured at 7.8s against a .invalid name. Any
            # check that has to touch DNS to decide is therefore already too
            # late; the only safe test is one answered from memory.
            if (not self._succeeded
                    or self._failures
                    or time.monotonic() < self._next_attempt):
                _spool_write(envelope)
                return
            try:
                self._post(envelope, timeout=SHUTDOWN_BUDGET)
            except Exception:
                _spool_write(envelope)
        except Exception as exc:
            logger.debug("telemetry shutdown failed: %s", exc)


_sink = None


def _get_sink():
    """The process-wide sink, or None when telemetry is disabled.

    Note this creates no thread - the worker starts on the first submit().
    """
    global _sink
    if _sink is None:
        config = _get_config()
        if not config["enabled"]:
            return None
        _sink = _Sink(config["url"], config["token"])
    return _sink


# ------------------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------------------

def _build_event(event_type, **fields):
    event = {
        "event_id": uuid.uuid4().hex,
        "event_type": event_type,
        "ts_utc": datetime.datetime.utcnow().isoformat(timespec="seconds"),
    }
    event.update(fields)
    return event


def _record(event_type, **fields):
    """Build and enqueue an event. Never raises, never blocks."""
    try:
        config = _get_config()
        if not config["enabled"]:
            return False
        event = _build_event(event_type, **fields)
        if config["debug"]:
            print("[GSTools telemetry] %s" % json.dumps(event))
        sink = _get_sink()
        if sink is None:
            return False
        return sink.submit(event)
    except Exception as exc:
        logger.debug("telemetry _record failed: %s", exc)
        return False


def log_launch(tool_id, label=None, source="menu", **extra):
    """
    Record that a tool was launched. Never raises - telemetry must not be able
    to block a tool from running.

    Args:
        tool_id (str): stable id of the tool from menu_config.
        label (str): human label, if known.
        source (str): "menu", "shelf", or other surface that triggered it.
        **extra: any additional context to record.
    """
    return _record(
        "tool_launch",
        tool_id=tool_id,
        tool_label=label or tool_id,
        source=source,
        payload=extra or None,
    )


def session_start():
    """Announce this DCC process and arm the exit hook. Called from gstools.boot()."""
    if not is_enabled():
        return False
    atexit.register(_on_exit)
    return _record("session_start")


def session_end():
    """Flush and close out the session. Idempotent-ish; safe to call twice."""
    sink = _sink
    if sink is not None:
        sink.shutdown()
    return True


_exited = False


def _on_exit():
    global _exited
    if _exited:
        return
    _exited = True
    session_end()
