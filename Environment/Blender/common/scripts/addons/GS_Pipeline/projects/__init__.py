"""'Projects' category for GS Pipeline: one package per project, shown in the
group bar once there is more than one.

To add a project, follow mgp27/: a package whose __init__.py has a GROUP (one
Tab per tool module of the project) and register() / unregister(). Then add it
to CATEGORY below, where it should sit in the bar.
"""
from __future__ import annotations

from ..panel import Category
from . import cm, hw3, mgp27

CATEGORY = Category("PROJECTS", "Projects", (cm, hw3, mgp27))
