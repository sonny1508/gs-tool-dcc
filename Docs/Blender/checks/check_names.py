"""Find undefined and unused module-level names in a Blender add-on, without pyflakes.

    python Docs/Blender/checks/check_names.py [folder]

``folder`` defaults to the GS_Pipeline add-on. Run it after moving or splitting
modules: compiling catches syntax, this catches a name a module uses but no longer
imports, which otherwise only shows up when Blender runs that line.

Undefined: a name some scope reads as a global (per ``symtable``) that the module
never binds and isn't a builtin. Class-body annotations are checked too: Blender
evaluates them for PropertyGroups / Operators even under ``from __future__ import
annotations``. Unused: a module-level import nothing in the file reads.

Plain Python 3.9+, standard library only; it never imports the add-on.
"""
import ast
import builtins
import os
import symtable
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT = os.path.join(HERE, "..", "..", "..", "Environment", "Blender", "common",
                       "scripts", "addons", "GS_Pipeline")
BUILTINS = set(dir(builtins)) | {"__file__", "__name__", "__doc__", "__package__"}


def _targets(node):
    if isinstance(node, ast.Assign):
        return node.targets
    if isinstance(node, (ast.AnnAssign, ast.AugAssign, ast.For)):
        return [node.target]
    if isinstance(node, ast.With):
        return [item.optional_vars for item in node.items if item.optional_vars]
    if isinstance(node, ast.Try):
        return [t for body in (node.body, node.orelse, node.finalbody) for n in body for t in _targets(n)]
    if isinstance(node, ast.If):
        return [t for n in node.body + node.orelse for t in _targets(n)]
    return []


def module_bindings(tree):
    bound = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            bound.update((alias.asname or alias.name).split(".")[0] for alias in node.names)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            bound.add(node.name)
        elif isinstance(node, ast.Global):
            bound.update(node.names)
    for node in tree.body:
        for target in _targets(node):
            bound.update(n.id for n in ast.walk(target) if isinstance(n, ast.Name))
    return bound


def global_reads(table, out):
    is_module = table.get_type() == "module"
    for sym in table.get_symbols():
        if sym.is_referenced() and (sym.is_global() or is_module):
            if not (is_module and (sym.is_assigned() or sym.is_imported())):
                out.add(sym.get_name())
    for child in table.get_children():
        global_reads(child, out)


def check(path):
    with open(path, encoding="utf-8") as fh:
        source = fh.read()
    tree = ast.parse(source, path)
    bound = module_bindings(tree)
    reads = set()
    global_reads(symtable.symtable(source, path, "exec"), reads)
    for cls in (n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)):
        for stmt in cls.body:
            if isinstance(stmt, ast.AnnAssign):
                reads.update(n.id for n in ast.walk(stmt.annotation) if isinstance(n, ast.Name))
    problems = ["undefined: " + name for name in sorted(reads - bound - BUILTINS)]

    loaded = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    loaded |= {n.value.id for n in ast.walk(tree)
               if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)}
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                name = (alias.asname or alias.name).split(".")[0]
                if name not in loaded and name != "annotations":
                    problems.append("unused import: " + name)
    return problems


def main():
    root = os.path.normpath(sys.argv[1] if len(sys.argv) > 1 else DEFAULT)
    total = 0
    for folder, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for name in sorted(files):
            if name.endswith(".py"):
                path = os.path.join(folder, name)
                for problem in check(path):
                    total += 1
                    print("{}: {}".format(os.path.relpath(path, root), problem))
    print("{} problem(s)".format(total))
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
