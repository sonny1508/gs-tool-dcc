"""
GSTools - self check

Static validation of menu_config against what's actually on disk. Safe to run
outside Maya (it imports no maya modules):

    python -c "import gstools.selfcheck as s; s.check()"

Checks:
  * tool ids are unique (menu_config raises on duplicates),
  * every "python" tool's module resolves to a .py / package on the tool paths,
  * every "mel_source" tool's source file exists,
  * every shelf id exists in the menu,
  * every menu id resolves through get_tool().
"""
import os

from gstools import menu_config

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # .../scripts


def _search_dirs():
    dirs = [_ROOT, os.path.join(_ROOT, "gstools")]
    for base in ("tools", "vendor"):
        base_dir = os.path.join(_ROOT, base)
        if not os.path.isdir(base_dir):
            continue
        dirs.append(base_dir)
        for name in os.listdir(base_dir):
            sub = os.path.join(base_dir, name)
            if os.path.isdir(sub):
                dirs.append(sub)
    return dirs


def _module_exists(module, dirs):
    for d in dirs:
        if os.path.exists(os.path.join(d, module + ".py")):
            return True
        if os.path.isdir(os.path.join(d, module)):
            return True
    return False


def check(verbose=True):
    """Return a list of problem strings (empty == all good)."""
    dirs = _search_dirs()
    problems = []
    ids = []

    for category in menu_config.MENU:
        for item in category.get("items", []):
            if item.get("divider"):
                continue
            tid = item["id"]
            ids.append(tid)
            ttype = item.get("type")
            if ttype == "python":
                if not _module_exists(item["module"], dirs):
                    problems.append("python module missing: '%s' (tool '%s')" % (item["module"], tid))
            elif ttype == "mel_source":
                src = os.path.join(_ROOT, item["source"].replace("/", os.sep))
                if not os.path.exists(src):
                    problems.append("mel source missing: '%s' (tool '%s')" % (item["source"], tid))

    for sid in menu_config.SHELF:
        if sid and menu_config.get_tool(sid) is None:
            problems.append("shelf id not in menu: '%s'" % sid)

    for tid in ids:
        if menu_config.get_tool(tid) is None:
            problems.append("get_tool() failed for: '%s'" % tid)

    if verbose:
        print("GSTools self-check: %d menu tools, %d shelf buttons" %
              (len(ids), sum(1 for s in menu_config.SHELF if s)))
        if problems:
            print("PROBLEMS (%d):" % len(problems))
            for p in problems:
                print("  - " + p)
        else:
            print("OK: every tool module/source exists and every id resolves.")
    return problems


if __name__ == "__main__":
    import sys
    sys.path.insert(0, _ROOT)
    raise SystemExit(1 if check() else 0)
