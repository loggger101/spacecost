# -*- coding: utf-8 -*-
"""Output shim, so importing a library never writes to stdout.

`transportation.py` printed a progress line at every table load and at every
step of the build, which is right for a notebook module that is also the
program, and wrong for a package somebody imports for one price.  Every one of
those calls became `say()` here.

`say()` is silent by default.  `set_verbose(True)`, or the `--verbose` flag on
the CLI, restores the original console output verbatim.

⚠️  ASCII ONLY, and that is not a style preference.  Windows picks cp1252 for a
redirected stdout, so a single non-ASCII character in a printed string kills
`spacecost build > run.log` with a UnicodeEncodeError before a row is written.
Comments, docstrings and the `notes` fields of the reference rows keep their
Unicode; those are data and prose, not output.
"""

_VERBOSE = False


def set_verbose(on: bool = True) -> None:
    """Turn the progress output on or off. Off is the default."""
    global _VERBOSE
    _VERBOSE = bool(on)


def is_verbose() -> bool:
    """Is progress output currently on?"""
    return _VERBOSE


def say(*args, **kwargs) -> None:
    """`print`, but only when verbose. The signature is print's."""
    if _VERBOSE:
        print(*args, **kwargs)
