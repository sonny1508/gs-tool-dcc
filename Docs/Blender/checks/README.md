# Checks that need no Blender

Two scripts for after moving or splitting GS Pipeline modules. Run them with the
dev machine's own Python, from the repo root:

```bat
python Docs\Blender\checks\check_names.py
python Docs\Blender\checks\import_check.py
```

| Script            | Catches                                                              | Needs |
| ----------------- | -------------------------------------------------------------------- | ----- |
| `check_names.py`  | names a module uses but doesn't import or define (including PropertyGroup annotations), imports nothing uses | standard library |
| `import_check.py` | broken relative imports, import cycles, a malformed Category / Group / Tab tree, anything `unregister()` leaves behind | numpy (`pip install numpy`) |

Both exit non-zero / raise on a problem. Neither runs a tool or tells you anything about
behaviour in Blender. That is still Sonny's test in real Blender
([README.md](../README.md) section 4). Together with `python -m compileall -q
Environment\Blender\common\scripts\addons\GS_Pipeline` they are the whole check before
handing a refactor over.
