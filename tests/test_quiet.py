# -*- coding: utf-8 -*-
"""Importing this package must be silent, and its output must be ASCII.

Two separate rules, both learned the hard way in the parent project.

SILENCE.  Module 3 printed a progress line at every table load, which is right
for a notebook module that is also the program and wrong for a package
somebody imports for one launch price.  `_log.say` is the shim; this is the
check that nothing slipped back to a bare `print`.

ASCII.  Windows picks cp1252 for a REDIRECTED stdout, so a single non-ASCII
character in a printed string kills `spacecost build > run.log` with a
UnicodeEncodeError before a row is written -- and never fires in a console, so
it stays invisible until the moment somebody logs a long run.  In the parent
project emoji were under a fifth of it: box-drawing characters were most of the
2,081 offenders.  The rule is ASCII, not "no emoji".

Comments, docstrings and the `notes` fields keep their Unicode.  Those are
prose and data, not output.
"""

import ast
import io
import os
import subprocess
import sys
import tokenize

import pytest

import spacecost

PKG_DIR = os.path.dirname(os.path.abspath(spacecost.__file__))


def _python_files():
    for fn in sorted(os.listdir(PKG_DIR)):
        if fn.endswith(".py"):
            yield os.path.join(PKG_DIR, fn)


def test_import_is_silent():
    """A fresh interpreter importing the package prints nothing at all."""
    proc = subprocess.run(
        [sys.executable, "-c", "import spacecost"],
        capture_output=True, text=True,
        cwd=os.path.dirname(PKG_DIR),
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout == "", "import printed: " + repr(proc.stdout[:300])


# Two files are allowed a real `print`, for opposite reasons:
#   _log.py  IS the shim -- `say` calls print, that is its whole job
#   cli.py   is a command line, where printing the answer is the point. A user
#            who runs `spacecost show vehicles` asked for that table on stdout,
#            and routing it through a verbosity flag would make the tool silent
#            by default, which for a CLI is not caution but a bug.
_PRINT_IS_ALLOWED = {"_log.py", "cli.py"}


def test_no_bare_print_calls():
    """Library output goes through `say`, so verbosity stays controllable.

    This is what stops a progress line reappearing in a module somebody imports
    for one launch price.
    """
    offenders = []
    for path in _python_files():
        if os.path.basename(path) in _PRINT_IS_ALLOWED:
            continue
        tree = ast.parse(open(path, encoding="utf-8").read())
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                    and node.func.id == "print"):
                offenders.append(os.path.basename(path) + ":" + str(node.lineno))
    assert not offenders, "bare print() calls: " + ", ".join(offenders)


def test_printed_strings_are_ascii():
    """No string that can reach stdout carries a character cp1252 cannot encode.

    Only the arguments of `say(...)` and `print(...)` are checked.  A `notes`
    field is data and keeps whatever it says.
    """
    offenders = []
    for path in _python_files():
        src = open(path, encoding="utf-8").read()
        for node in ast.walk(ast.parse(src)):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                    and node.func.id in ("say", "print")):
                continue
            for sub in ast.walk(node):
                if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
                    try:
                        sub.value.encode("cp1252")
                    except UnicodeEncodeError:
                        bad = [c for c in sub.value if ord(c) > 127][:5]
                        offenders.append(
                            os.path.basename(path) + ":" + str(sub.lineno)
                            + " " + repr("".join(bad)))
    assert not offenders, "non-ASCII in printed strings: " + "; ".join(offenders)


def test_notes_fields_do_contain_non_ascii():
    """The premise of the next test: `notes` are DATA and keep their Unicode.

    If this ever passes with zero hits, somebody has ASCII-flattened the
    citations, and the test below stops proving anything.
    """
    import spacecost as sc
    hits = 0
    for table in (sc.LAUNCH_VEHICLES_REFERENCE, sc.PROPELLANTS_REFERENCE,
                  sc.DELTA_V_REFERENCE, sc.OPERATIONAL_COSTS_REFERENCE,
                  sc.STORAGE_REFERENCE):
        for row in table:
            note = row.get("notes", "")
            if any(ord(c) > 127 for c in note):
                hits += 1
    assert hits > 0, "no notes field carries Unicode; has the data been flattened?"


@pytest.mark.parametrize("table", ["vehicles", "propellants", "deltav",
                                   "operations", "storage"])
def test_show_survives_a_cp1252_redirect(table):
    """`show` prints DATA, and data carries Unicode the ASCII rule does not cover.

    A separate failure from the printed-string one, with a separate fix: the
    ASCII rule keeps the package's OWN output safe, and cannot keep a yen sign
    somebody put in a citation safe. `cli._make_stdout_total` is what does
    that, and this is the test that it is still wired up.
    """
    env = dict(os.environ, PYTHONUTF8="0", PYTHONIOENCODING="cp1252")
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "out.txt")
        with open(out, "w") as fh:
            proc = subprocess.run(
                [sys.executable, "-m", "spacecost", "show", table],
                stdout=fh, stderr=subprocess.PIPE, text=True, env=env,
                cwd=os.path.dirname(PKG_DIR),
            )
        assert proc.returncode == 0, proc.stderr
        assert "UnicodeEncodeError" not in proc.stderr, proc.stderr


def test_build_survives_a_cp1252_redirect():
    """The regression test for the crash itself: build with stdout redirected.

    Reproduces the exact failing condition -- cp1252 stdout, redirected to a
    file, verbose output on, no reconfigure anywhere.
    """
    import tempfile
    env = dict(os.environ, PYTHONUTF8="0", PYTHONIOENCODING="cp1252")
    with tempfile.TemporaryDirectory() as tmp:
        script = (
            "import spacecost;"
            "spacecost.set_verbose(True);"
            "cfg = spacecost.SpacecostConfig(output_dir=%r, use_yfinance=False);"
            "spacecost.build_catalog(cfg)" % tmp
        )
        log = os.path.join(tmp, "run.log")
        with open(log, "w") as fh:
            proc = subprocess.run(
                [sys.executable, "-c", script], stdout=fh,
                stderr=subprocess.PIPE, text=True, env=env,
                cwd=os.path.dirname(PKG_DIR),
            )
        assert proc.returncode == 0, proc.stderr
        assert proc.stderr == "", proc.stderr


def test_no_unused_imports():
    """Dead imports, kept out because one of them was actively misleading.

    `tables.py` imported numpy and never called it, which reads as though the
    module does array work. It deliberately does NOT -- the summary loop stays
    scalar because `np.exp` dispatches a different SIMD kernel for an array and
    the committed hash is a scalar-path hash. An unused import there argued the
    opposite of the comment three lines below it.
    """
    offenders = []
    for path in _python_files():
        src = open(path, encoding="utf-8").read()
        tree = ast.parse(src)
        imported = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported[(alias.asname or alias.name).split(".")[0]] = node.lineno
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    imported[alias.asname or alias.name] = node.lineno
        used = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
        used |= {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
        # A re-export counts as a use: __init__.py imports names so that
        # `spacecost.X` resolves, and lists them as strings in __all__.
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                used.add(node.value)
        for name, line in sorted(imported.items()):
            if name not in used:
                offenders.append("%s:%d imports %s and never uses it"
                                 % (os.path.basename(path), line, name))
    assert not offenders, "; ".join(offenders)


def test_tables_does_not_reach_for_numpy():
    """The vectorisation decision, asserted rather than only commented.

    `build_transportation_summary` must keep evaluating the rocket equation one
    scalar at a time. Vectorising it is faster and changes the output bytes,
    because numpy picks a SIMD kernel for an array that is not the scalar path,
    and `reference/summary_meta.json` records a scalar-path hash.

    The shortest way to keep that true is for the module to have no array
    library in reach at all.
    """
    src = open(os.path.join(PKG_DIR, "tables.py"), encoding="utf-8").read()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module or ""]
        else:
            continue
        assert not any(n.startswith("numpy") for n in names), (
            "tables.py imports numpy at line %d. If that is to vectorise the "
            "summary, the committed hash moves; see the comment in "
            "build_transportation_summary." % node.lineno)
