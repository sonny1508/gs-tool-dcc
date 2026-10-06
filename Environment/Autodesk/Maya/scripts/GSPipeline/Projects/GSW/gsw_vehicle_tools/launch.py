# -*- coding: utf-8 -*-
"""Entry point for GSW Vehicle Tools.

This is the file tool_config.py points at. GSPipeline runs tools by exec'ing
their path, and nothing under 05_Projects is importable by dotted path (the
folder starts with a digit), so this bootstraps sys.path itself.

Every launch purges the package from sys.modules first, so edits to the tool
take effect on the next shelf click without restarting Maya.
"""

import os
import sys

PACKAGE = "gsw_vehicle_tools"


def _bootstrap():
    package_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(package_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

    for name in [m for m in sys.modules if m == PACKAGE or m.startswith(PACKAGE + ".")]:
        del sys.modules[name]


def main():
    _bootstrap()
    from gsw_vehicle_tools import main_window
    main_window.show()


main()
