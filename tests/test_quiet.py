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
