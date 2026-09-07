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
    }
    for name, n in want.items():
        m = re.search(r"\|\s*`%s`\s*\|\s*(\d+)\s*\|" % re.escape(name), readme)
        assert m, "no row for " + name + " in the README table"
        assert int(m.group(1)) == n, (
            "README table says %s %s, actual %d" % (name, m.group(1), n))


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
def _slugs(text):
    """GitHub's heading-to-anchor rule, including its -N suffix for repeats."""
    out, seen = set(), {}
    for line in text.split("\n"):
        m = re.match(r"^(#{1,6})\s+(.*?)\s*$", line)
        if not m:
            continue
        h = re.sub(r"[`*~]|\[|\]|\(|\)", "", m.group(2))
        s = re.sub(r"[^\w\s\-]", "", h, flags=re.UNICODE).strip().lower()
        s = s.replace(" ", "-")
        k = seen.get(s, 0)
        seen[s] = k + 1
        out.add(s if k == 0 else "%s-%d" % (s, k))
    return out


@pytest.mark.parametrize("name", ["README.md", "CHANGELOG.md", "CITATIONS.md"])
def test_internal_anchors_resolve(name):
    """A table of contents that points at nothing is worse than none."""
    text = _read(name)
    have = _slugs(text)
    broken = []
    for m in re.finditer(r"\]\(#([^)]+)\)", text):
        if m.group(1) not in have:
            broken.append(m.group(1))
    assert not broken, name + " has broken anchors: " + ", ".join(broken)


@pytest.mark.parametrize("name", ["README.md", "CHANGELOG.md", "CITATIONS.md"])
def test_relative_links_point_at_files_that_exist(name):
    text = _read(name)
    missing = []
    for m in re.finditer(r"\]\((?!https?:|#)([^)#]+)", text):
        target = m.group(1).strip()
        if not os.path.exists(os.path.join(HERE, target)):
            missing.append(target)
    assert not missing, name + " links to missing files: " + ", ".join(missing)


# ------------------------------------------------------------------ manifest
def test_requirements_match_the_package_metadata():
    """`requirements.txt` and pyproject's dependencies are one list."""
    req = [ln.strip() for ln in _read("requirements.txt").split("\n")
           if ln.strip() and not ln.strip().startswith("#")]
    req = {re.split(r"[<>=!~;\[]", r)[0].strip() for r in req}
    block = re.search(r"^dependencies\s*=\s*\[(.*?)\]", _read("pyproject.toml"),
                      re.S | re.M)
    assert block, "pyproject has no dependencies list"
    meta = {re.split(r"[<>=!~;\[]", d)[0].strip()
            for d in re.findall(r'"([^"]+)"', block.group(1))}
    assert req == meta, "requirements.txt %s != pyproject %s" % (
        sorted(req), sorted(meta))


# ------------------------------------------------------------------ structure
@pytest.mark.parametrize("name", ["README.md", "CHANGELOG.md", "CITATIONS.md"])
def test_markdown_structure(name):
    """Balanced code fences, one h1, no heading-level jumps."""
    lines = _read(name).split("\n")
    fences = sum(1 for l in lines if l.startswith("```"))
    assert fences % 2 == 0, name + " has an unbalanced code fence"

    in_fence, levels, h1 = False, [], 0
    for l in lines:
        if l.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = re.match(r"^(#{1,6})\s", l)
        if m:
            lvl = len(m.group(1))
            if lvl == 1:
                h1 += 1
            if levels and lvl > levels[-1] + 1:
                raise AssertionError(
                    "%s jumps from h%d to h%d at %r" % (name, levels[-1], lvl, l[:50]))
            levels.append(lvl)
    assert h1 == 1, "%s has %d h1 headings, want exactly 1" % (name, h1)
