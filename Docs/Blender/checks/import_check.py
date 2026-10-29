"""Import GS_Pipeline against a stand-in ``bpy`` and run register / unregister.

    python Docs/Blender/checks/import_check.py [addons folder]

The addons folder defaults to ``Environment/Blender/common/scripts/addons``.
Checks the package wiring only: relative imports, import cycles, the panel's
Category / Group / Tab tree, and that unregister() undoes register() (classes,
window-manager / scene properties, load handlers). It says nothing about how the
tools behave in Blender. That is tested in Blender (Docs/Blender/README.md).

Needs numpy, which the add-on imports (Blender bundles it; ``pip install numpy``
for the local Python). Don't run it with ``python -I``: that hides user-installed
numpy. If a module starts using a new ``bpy`` name at import time, add it to the
stand-in below.
"""
import os
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT = os.path.join(HERE, "..", "..", "..", "Environment", "Blender", "common", "scripts", "addons")


class Any:
    """Absorbs any attribute access or call."""

    def __getattr__(self, name):
        return Any()

    def __call__(self, *args, **kwargs):
        return Any()

    def __iter__(self):
        return iter(())

    def __bool__(self):
        return False


def module(name, **attrs):
    mod = types.ModuleType(name)
    mod.__dict__.update(attrs)
    sys.modules[name] = mod
    return mod


registered = []
bpy_types = module("bpy.types", **{n: type(n, (), {}) for n in (
    "Operator", "PropertyGroup", "UIList", "Panel", "WindowManager", "Scene", "Object", "Mesh")})
bpy_props = module("bpy.props", **{n: (lambda *a, **k: ("prop", k)) for n in (
    "BoolProperty", "IntProperty", "FloatProperty", "StringProperty", "EnumProperty",
    "PointerProperty", "CollectionProperty", "FloatVectorProperty", "IntVectorProperty")})
handlers = types.SimpleNamespace(load_post=[], save_pre=[], depsgraph_update_post=[],
                                 persistent=lambda fn: fn)
timers = types.SimpleNamespace(register=lambda *a, **k: None,
                               is_registered=lambda fn: False, unregister=lambda fn: None)
utils = types.SimpleNamespace(register_class=registered.append,
                              unregister_class=lambda cls: registered.remove(cls),
                              user_resource=lambda kind: ".")
module("bpy", types=bpy_types, props=bpy_props, utils=utils, ops=Any(), data=Any(),
       context=Any(), path=Any(),
       app=types.SimpleNamespace(handlers=handlers, timers=timers, version=(4, 5, 0)))
module("bmesh")
module("mathutils", Vector=type("Vector", (), {}), Matrix=type("Matrix", (), {}))


def owned_props():
    return {owner.__name__: sorted(k for k in vars(owner) if k.startswith("gs"))
            for owner in (bpy_types.WindowManager, bpy_types.Scene)}


def main():
    sys.path.insert(0, os.path.normpath(sys.argv[1] if len(sys.argv) > 1 else DEFAULT))
    import GS_Pipeline as addon

    # Keep GS File Transfer's server probe off the network.
    addon.file_io.file_transfer.server.ServerStatus.check = classmethod(lambda cls: None)

    for category in addon.CATEGORIES:
        print(category.id, category.label)
        for group in category.groups:
            print("   ", group.id, "|", ", ".join(tab.label for tab in group.tabs))
            assert group.tabs, group
            for tab in group.tabs:
                assert callable(tab.draw), tab

    addon.register()
    print("registered classes:", len(registered))
    for owner, names in owned_props().items():
        print(owner, names)
    print("load_post handlers:", len(handlers.load_post))

    addon.unregister()
    leftovers = registered + [n for names in owned_props().values() for n in names] + handlers.load_post
    assert not leftovers, "left behind after unregister: {}".format(leftovers)
    print("OK: unregister undid everything")


if __name__ == "__main__":
    main()
