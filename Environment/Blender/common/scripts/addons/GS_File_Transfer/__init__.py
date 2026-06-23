"""GS File Transfer — RETIRED.

This standalone addon has been merged into **GS Pipeline**:

    GS Pipeline sidebar tab > File I/O > GS File Transfer

The implementation now lives in:
    GS_Pipeline/file_io/gs_file_transfer.py

This stub remains only so any saved preference that still references
``GS_File_Transfer`` can enable cleanly without registering anything (which would
collide with the merged version's ``gs.*`` operators and ``gs_file_transfer_props``).
Enable **GS Pipeline** instead. See ``gs_pipeline_core`` startup, which
auto-disables this module and enables GS Pipeline.
"""

bl_info = {
    "name": "GS File Transfer (retired - use GS Pipeline)",
    "author": "Sonny",
    "version": (1, 5),
    "blender": (3, 6, 0),
    "location": "Merged into GS Pipeline > File I/O",
    "description": "Retired. Functionality moved into the GS Pipeline addon (File I/O > GS File Transfer).",
    "warning": "Superseded by GS Pipeline. Enable GS Pipeline instead.",
    "category": "Import-Export",
}


def register():
    print("[GS File Transfer] Retired stub - functionality is now in GS Pipeline (File I/O).")


def unregister():
    pass
