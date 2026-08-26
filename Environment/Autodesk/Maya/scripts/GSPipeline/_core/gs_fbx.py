# -*- coding: utf-8 -*-
"""
Shared FBX import/export layer for GSPipeline tools.

Why this module exists
----------------------
The FBX plug-in stores its settings in *global, session-sticky* state. Whatever
the last tool set - or whatever the artist last picked in Maya's own FBX dialog -
stays set until something changes it. A tool that overrides only the three or
four flags it cares about silently inherits everything else, so the same button
emits a different FBX depending on what else ran earlier in that Maya session.

That is exactly what used to happen between GS File Exporter (which sets
`FBXExportUpAxis z`) and GS File Transfer (which never set an up axis): run the
exporter first, and every later transfer went out Z-up.

So every entry point here starts from `FBXResetExport` / `FBXResetImport` and
then applies a *complete* named preset. Order of operations stops mattering, and
the studio's FBX contract lives in one file instead of four.

Pure maya.cmds / maya.mel - deliberately no pymel - so any GSPipeline tool can
import it regardless of what that tool itself uses.

Usage
-----
    import gs_fbx

    gs_fbx.export_selection(path, preset='transfer')
    gs_fbx.import_file(path, preset='transfer', add_as_new=True)

Presets are plain lists of MEL statements so they can be read straight across
against the Autodesk FBX documentation. Add a preset rather than reaching past
this module to poke a flag from a tool.
"""

import maya.mel as mel

__all__ = [
    'EXPORT_PRESETS', 'IMPORT_PRESETS',
    'mel_path', 'mel_bool',
    'apply_export_preset', 'apply_import_preset',
    'export_selection', 'import_file',
]


# ============================================================================
# PRESETS
# ============================================================================

# Everything the studio always wants, whatever the preset.
_EXPORT_BASE = [
    'FBXExportFileVersion "FBX202000"',
    'FBXExportScaleFactor 1.0',
    'FBXExportInAscii -v false',
]

EXPORT_PRESETS = {
    # DCC-to-DCC handoff (GS File Transfer). Maya-native orientation, nothing
    # but geometry. Up axis is pinned to y - which is the plug-in default and
    # what a fresh Maya session produced - so the exporter's z can never leak in.
    'transfer': _EXPORT_BASE + [
        'FBXExportUpAxis y',
        'FBXExportSmoothingGroups -v true',
        'FBXExportSmoothMesh -v false',
        'FBXExportTriangulate -v false',
        'FBXExportTangents -v false',
        'FBXExportInstances -v false',
        'FBXExportHardEdges -v false',
        'FBXExportBakeComplexAnimation -v false',
        'FBXExportCameras -v false',
        'FBXExportLights -v false',
        'FBXExportAudio -v false',
        'FBXExportEmbeddedTextures -v false',
        'FBXExportConstraints -v false',
        'FBXExportInputConnections -v false',
    ],

    # Batch asset export (GS File Exporter). Z-up, centimetres - the engine
    # contract, not the Maya one.
    'asset': _EXPORT_BASE + [
        'FBXExportUpAxis z',
        'FBXExportConvertUnitString "cm"',
        'FBXExportSmoothingGroups -v true',
        'FBXExportSmoothMesh -v false',
        'FBXExportTriangulate -v false',
        'FBXExportTangents -v false',
        'FBXExportInstances -v false',
        'FBXExportHardEdges -v false',
        'FBXExportReferencedAssetsContent -v false',
        'FBXExportBakeComplexAnimation -v false',
        'FBXExportCameras -v false',
        'FBXExportLights -v false',
        'FBXExportAudio -v false',
        'FBXExportEmbeddedTextures -v false',
        'FBXExportConstraints -v false',
        'FBXExportInputConnections -v false',
    ],
}

IMPORT_PRESETS = {
    # Geometry-only import for DCC handoff. The three flags the artist controls
    # (smoothing groups, unlock normals, add-vs-merge) are passed per call.
    'transfer': [
        'FBXImportScaleFactor 1.0',
        'FBXImportUpAxis y',
        'FBXImportCameras -v false',
        'FBXImportLights -v false',
        'FBXImportConstraints -v false',
        'FBXImportShapes -v true',
        'FBXImportSkins -v true',
    ],
}


# ============================================================================
# HELPERS
# ============================================================================

def mel_path(path):
    """MEL only accepts forward slashes inside quoted paths."""
    return path.replace('\\', '/')


def mel_bool(value):
    return 'true' if value else 'false'


def _run(statements):
    for statement in statements:
        mel.eval(statement + ';')


# ============================================================================
# SETTINGS
# ============================================================================

def apply_export_preset(preset='transfer'):
    """
    Reset the FBX exporter to plug-in defaults, then apply the named preset.

    The reset is the point: it is what stops one tool's settings leaking into
    the next one's export.
    """
    try:
        statements = EXPORT_PRESETS[preset]
    except KeyError:
        raise ValueError('Unknown FBX export preset: {0!r} (have: {1})'.format(
            preset, ', '.join(sorted(EXPORT_PRESETS))))

    mel.eval('FBXResetExport;')
    _run(statements)


def apply_import_preset(preset='transfer', smoothing_groups=None,
                        unlock_normals=None, add_as_new=None):
    """
    Reset the FBX importer to plug-in defaults, then apply the named preset.

    smoothing_groups / unlock_normals / add_as_new are the per-call options the
    artist drives from a UI; leave them None to keep the preset's own value.

    add_as_new picks the import mode: True keeps everything already in the scene
    and brings the FBX in as new nodes (Maya auto-numbers name clashes), False
    lets the FBX write into existing nodes of the same name.
    """
    try:
        statements = list(IMPORT_PRESETS[preset])
    except KeyError:
        raise ValueError('Unknown FBX import preset: {0!r} (have: {1})'.format(
            preset, ', '.join(sorted(IMPORT_PRESETS))))

    if smoothing_groups is not None:
        statements.append('FBXImportSmoothingGroups -v {0}'.format(mel_bool(smoothing_groups)))
    if unlock_normals is not None:
        statements.append('FBXImportUnlockNormals -v {0}'.format(mel_bool(unlock_normals)))
    if add_as_new is not None:
        statements.append('FBXImportMode -v {0}'.format('add' if add_as_new else 'merge'))

    mel.eval('FBXResetImport;')
    _run(statements)


# ============================================================================
# OPERATIONS
# ============================================================================

def export_selection(file_path, preset='transfer'):
    """
    Apply the preset and export the current selection to file_path.

    Deliberately does no selection check and shows no dialogs - callers own
    their own UI and error reporting.
    """
    apply_export_preset(preset)
    mel.eval('FBXExport -f "{0}" -s;'.format(mel_path(file_path)))


def import_file(file_path, preset='transfer', smoothing_groups=None,
                unlock_normals=None, add_as_new=None):
    """Apply the preset and import file_path into the current scene."""
    apply_import_preset(preset,
                        smoothing_groups=smoothing_groups,
                        unlock_normals=unlock_normals,
                        add_as_new=add_as_new)
    mel.eval('FBXImport -f "{0}";'.format(mel_path(file_path)))
