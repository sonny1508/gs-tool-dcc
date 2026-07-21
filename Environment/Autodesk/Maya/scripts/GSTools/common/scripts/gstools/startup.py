"""
GSTools - startup registration

Runs once at Maya startup (via gstools.boot() from GSTools.mel). It registers the
"extras" that aren't part of the data-driven GSTools menu:

  * zhcg_polyTools : builds its own "ZhCG_PolyTools" menu on import
  * GN_ImportExport: builds its own "GN Import/Export" menu (MEL proc)
  * GS_Spread      : a hotkey operation (Alt+S), not a menu tool

Each piece is wrapped so a single failure is logged but never aborts the rest
(the old userSetup.mel ran these as bare lines, so one bad import killed them all).
"""
import logging

logging.basicConfig()
logger = logging.getLogger("gstools.startup")
logger.setLevel(logging.INFO)


def _safe(label, fn):
    try:
        fn()
        logger.info("startup: %s OK", label)
    except Exception as exc:
        logger.warning("startup: %s FAILED: %s", label, exc)


def _load_zhcg():
    # zhcg_polyTools hardcodes its own module name in command strings and builds
    # its menu on import, so it must import as the top-level name 'zhcg_polyTools'
    # and be visible in __main__ (where its runtime-command strings evaluate).
    import __main__
    import importlib
    import zhcg_polyTools
    importlib.reload(zhcg_polyTools)
    __main__.zhcg_polyTools = zhcg_polyTools


def _load_gn():
    import maya.mel as mel
    # GN_ImportExport.mel lives at the scripts root, now on MAYA_SCRIPT_PATH.
    mel.eval('source "GN_ImportExport/GN_ImportExport.mel"; GN_ImportExport;')


def _load_gs_spread():
    import GS_Spread
    import importlib
    importlib.reload(GS_Spread)
    GS_Spread.register()


def run():
    _safe("zhcg_polyTools menu", _load_zhcg)
    _safe("GN Import/Export menu", _load_gn)
    _safe("GS_Spread hotkey", _load_gs_spread)
