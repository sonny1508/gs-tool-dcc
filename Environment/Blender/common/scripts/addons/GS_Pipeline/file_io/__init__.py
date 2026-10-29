"""'File I/O' category for GS Pipeline: moving files between applications and artists."""
from __future__ import annotations

from ..panel import Category
from . import file_transfer

CATEGORY = Category("FILE_IO", "File I/O", (file_transfer,))
