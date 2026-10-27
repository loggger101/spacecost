# -*- coding: utf-8 -*-
"""The documentation still describes the code.

The parent project learned this the expensive way: its recurring failure is not
a missing table, it is a stale sentence left standing beside a correct one. A
commit that changes a number naturally rewrites the table it measured and
leaves every summary paragraph that quoted the old figure alone.

These are the checks that are mechanical here. What none of them can see is a
number that is merely out of date, so the rest is still a manual discipline:
after changing any row, grep the prose for the superseded claim, not only for
the digits.
"""

import os
import re

import pytest
from samebytes import docs, source

import spacecost

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(name):
    with open(os.path.join(HERE, name), encoding="utf-8") as fh:
        return fh.read()


# --------------------------------------------------------------- row counts
def test_readme_row_counts_match_the_tables():
    """"41 propellants" after a row was added is the classic rot.

    The counts are matched wherever they appear beside the table's name, so a
    figure quoted in prose is held to the same standard as one in the table.
    """
    readme = _read("README.md")
    sizes = {
        "launch vehicles": len(spacecost.LAUNCH_VEHICLES_REFERENCE),
        "propellant systems": len(spacecost.PROPELLANTS_REFERENCE),
        "delta-v segments": len(spacecost.DELTA_V_REFERENCE),
        "operational cost": len(spacecost.OPERATIONAL_COSTS_REFERENCE),
        "storage systems": len(spacecost.STORAGE_REFERENCE),
        "destinations": len(spacecost.ENVIRONMENTS_REFERENCE),
    }
    bad = []
    for phrase, actual in sizes.items():
        for m in re.finditer(r"(\d+)\s+" + re.escape(phrase), readme):
            if int(m.group(1)) != actual:
                bad.append("README says %s %s, tables have %d"
                           % (m.group(1), phrase, actual))
    assert not bad, "; ".join(bad)


def test_table_row_counts_in_the_what_is_in_it_table():
    """The `| table | rows |` table, held to the tables themselves."""
    readme = _read("README.md")
    want = {
        "launch_vehicles": len(spacecost.LAUNCH_VEHICLES_REFERENCE),
        "propellants": len(spacecost.PROPELLANTS_REFERENCE),
        "delta_v_segments": len(spacecost.DELTA_V_REFERENCE),
        "operational_costs": len(spacecost.OPERATIONAL_COSTS_REFERENCE),
        "storage_systems": len(spacecost.STORAGE_REFERENCE),
        "environments": len(spacecost.ENVIRONMENTS_REFERENCE),
    }
    for name, n in want.items():
        m = re.search(r"\|\s*`%s`\s*\|\s*(\d+)\s*\|" % re.escape(name), readme)
        assert m, "no row for " + name + " in the README table"
        assert int(m.group(1)) == n, (
            "README table says %s %s, actual %d" % (name, m.group(1), n))


def test_readme_bracketed_row_count():
    """"All 64 bracketed rows" stood for a release after the 65th was added.

    A bracketed row is one carrying both `range_low` and `range_high`, which
    is what the inside-its-own-range band checks, across the two tables that
    have them.
    """
    n = sum(1 for table in (spacecost.OPERATIONAL_COSTS_REFERENCE,
                            spacecost.STORAGE_REFERENCE)
            for row in table
            if row.get("range_low") is not None
            and row.get("range_high") is not None)
    quoted = [int(m.group(1)) for m in
              re.finditer(r"(\d+)\s+bracketed rows", _read("README.md"))]
    assert quoted, "README no longer quotes a bracketed-row count"
    assert all(q == n for q in quoted), (
        "README says %s bracketed rows, the tables have %d" % (quoted, n))


# ---------------------------------------------------------- code examples
def _python_blocks(text):
    """(line number, source) of every ```python fence."""
    out, lines, i = [], text.split("\n"), 0
    while i < len(lines):
        if lines[i].strip() == "```python":
            start, body = i + 2, []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                body.append(lines[i])
                i += 1
            out.append((start, "\n".join(body) + "\n"))
        i += 1
    return out


def test_readme_python_examples_run():
    """Every README Python block runs, and a `>>>` block prints what it says.

    The delivery example printed the pre-v0.4.0 lunar price for a whole
    release, beside a table quoting the new one.  Nothing read it.

    A `>>>` block is a doctest with ELLIPSIS, so an example can stop its
    digits short -- and must, for anything that goes through `exp()`, which
    the platform libm need not round identically everywhere.  Any other block
    is executed and only has to not raise.
    """
    import doctest

    blocks = _python_blocks(_read("README.md"))
    assert blocks, "README has no ```python blocks to check"
    parser = doctest.DocTestParser()
    for lineno, src in blocks:
        where = "README.md:%d" % lineno
        if ">>>" not in src:
            exec(compile(src, where, "exec"), {})
            continue
        test = parser.get_doctest(src, {}, where, "README.md", lineno)
        runner = doctest.DocTestRunner(optionflags=doctest.ELLIPSIS)
        out = []
        result = runner.run(test, out=out.append)
        assert result.failed == 0, "".join(out)


# ----------------------------------------------------------------- versions
def test_package_version_agrees_everywhere():
    """`__version__`, pyproject and the newest CHANGELOG entry are one number."""
    v = spacecost.__version__
    pyproject = _read("pyproject.toml")
    m = re.search(r'^version\s*=\s*"([^"]+)"', pyproject, re.M)
    assert m and m.group(1) == v, (
        "pyproject says %s, __version__ is %s" % (m.group(1) if m else "?", v))

    changelog = _read("CHANGELOG.md")
    m = re.search(r"^### (\d+\.\d+\.\d+)", changelog, re.M)
    assert m and m.group(1) == v, (
        "newest CHANGELOG entry is %s, __version__ is %s"
        % (m.group(1) if m else "?", v))


def test_data_contract_version_agrees_with_the_docs():
    """The stamp in the docs is the stamp the build writes."""
    v = spacecost.CONFIG.pipeline_version
    for name in ("README.md", "CHANGELOG.md"):
        text = _read(name)
        assert v in text, name + " never states the data contract version " + v


# ------------------------------------------------------------------- links
# The link, structure and manifest rules are samebytes' (`samebytes.docs`,
# `samebytes.source`), the one copy the repositories in this family share.
DOCS = ["README.md", "CHANGELOG.md", "CITATIONS.md"]


@pytest.mark.parametrize("name", DOCS)
def test_links_and_anchors_resolve(name):
    """A table of contents that points at nothing is worse than none.

    Every relative link names a file that exists, and every #anchor a heading
    in the file it lands in.
    """
    bad, _ = docs.links(HERE, [name])
    assert not bad, name + ": " + "; ".join(bad)


# ------------------------------------------------------------------ manifest
def test_requirements_match_the_package_metadata():
    """`requirements.txt` and pyproject's dependencies are one list."""
    bad, n = source.requirements_match(HERE)
    assert bad == [] and n > 0


# The files a `github.com/loggger101/<repo>@<ref>` pin can sit in.  CHANGELOG
# is left out: an old pin there is history.
PINNED = ["pyproject.toml", "requirements.txt", "requirements-live.txt",
          ".github/workflows/tests.yml", "README.md", "CITATIONS.md"]


def test_git_pins_agree():
    """Every git pin of a sibling repository names one ref.

    samebytes is pinned in pyproject's test extra and in two CI steps (the
    wheel's consumer-contract run and the hooks check).  A repin that reaches
    one copy installs two releases, and both import cleanly: the hooks job
    pinned v0.1.0 while the test extra pinned v0.3.0 until samebytes v0.5.0.
    """
    bad, n = docs.pins(HERE, PINNED, "loggger101")
    assert bad == [] and n >= 3, "; ".join(bad)


# ------------------------------------------------------------------ structure
@pytest.mark.parametrize("name", DOCS)
def test_markdown_structure(name):
    """Balanced fences, one h1, no heading-level jumps, no ragged tables."""
    bad, n = docs.structure(HERE, [name])
    assert bad == [] and n == 1, "; ".join(bad)
