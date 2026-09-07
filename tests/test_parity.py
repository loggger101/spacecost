# -*- coding: utf-8 -*-
"""The acceptance test: a build reproduces the committed reference files exactly.

WHY THIS IS A BYTE COMPARISON AND NOT A TOLERANCE.  These tables are the input
to a model whose every release is argued from bit-identity, so the contract
this package offers its consumers is not "the same numbers" but "the same
bytes".  A tolerance would hide exactly the drift this exists to catch: a
reordered column, a float formatted differently, a row silently dropped.

The five reference CSVs under `reference/` were produced by economicspace
modules/transportation.py at pipeline_version 1.14.0 (commit b0b18b2) and by
this package, byte for byte identically, on 2026-09-07.  If this test fails and
you did not mean to change a row, the extraction has drifted.
"""

import hashlib
import os

import pandas as pd
import pytest

import spacecost

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REFERENCE = os.path.join(HERE, "reference")

# The stamp the committed reference files carry.  `catalog_date` is PROVENANCE,
# not a model value; pinning it is what stops midnight falling mid-run from
# reading like a defect.
PINNED_DATE = "2026-09-07"

SMALL_TABLES = ["launch_vehicles.csv", "propellants.csv", "delta_v_segments.csv",
                "operational_costs.csv", "storage_systems.csv"]


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    """One offline build, shared by every test in this file."""
    out = str(tmp_path_factory.mktemp("build"))
    cfg = spacecost.SpacecostConfig(output_dir=out, use_yfinance=False)
    frames = spacecost.build_catalog(cfg, catalog_date=PINNED_DATE)
    return cfg.table_dir(), frames


@pytest.mark.parametrize("name", SMALL_TABLES)
def test_table_is_byte_identical(built, name):
    """Every reference table reproduces the committed file exactly."""
    table_dir, _ = built
    fresh = open(os.path.join(table_dir, name), "rb").read()
    committed = open(os.path.join(REFERENCE, name), "rb").read()
    assert hashlib.sha256(fresh).hexdigest() == hashlib.sha256(committed).hexdigest(), (
        name + " differs from reference/" + name + ".  If you changed a row on "
        "purpose, bump pipeline_version, regenerate reference/, and add a "
        "CHANGELOG entry."
    )


def test_summary_matches_pinned_hash(built):
    """The composite summary is pinned by hash; it is too large to commit."""
    table_dir, _ = built
    path = os.path.join(table_dir, "transportation_summary.csv")
    got = hashlib.sha256(open(path, "rb").read()).hexdigest()
    want = open(os.path.join(REFERENCE, "SUMMARY_SHA256")).read().strip()
    assert got == want


def _bare_lf_outside_quotes(raw: bytes) -> int:
    """Count LF bytes that are RECORD terminators rather than data.

    A naive `raw.replace(b"\\r\\n", b"").count(b"\\n")` reports failures that do
    not exist, because many `notes` fields carry embedded newlines and a
    newline inside a quoted CSV field is data, not a line ending.  Writing that
    naive check first, and watching it fail on a byte-perfect file, is the
    comparator-stricter-than-the-artefact mistake in miniature.
    """
    in_quotes = False
    bare = 0
    i = 0
    while i < len(raw):
        byte = raw[i:i + 1]
        if byte == b'"':
            in_quotes = not in_quotes
        elif byte == b"\n" and not in_quotes:
            if raw[i - 1:i] != b"\r":
                bare += 1
        i += 1
    return bare


@pytest.mark.parametrize("name", SMALL_TABLES)
def test_crlf_is_pinned(built, name):
    """CRLF is a contract, not a Windows leftover.  Unpinning it breaks every hash.

    `pandas.to_csv` defaults `lineterminator` to `os.linesep`, so without the
    pin a byte-perfect Linux build reports DIFFER on every file with every
    value identical.  It reads on Linux like a leftover to clean up.  It is not.
    """
    table_dir, _ = built
    raw = open(os.path.join(table_dir, name), "rb").read()
    assert b"\r\n" in raw, name
    assert raw.endswith(b"\r\n"), name + " does not end with CRLF"
    assert _bare_lf_outside_quotes(raw) == 0, name + " has a bare LF record ending"


def test_data_version_mirror_agrees():
    """`spacecost.DATA_VERSION` mirrors config; a mirror can drift, so check it."""
    assert spacecost.DATA_VERSION == spacecost.CONFIG.pipeline_version


def test_stamped_columns_present(built):
    """Both provenance columns land in every file.  There are TWO, not one.

    Stripping only `pipeline_version` before a comparison and forgetting
    `catalog_date` is a real, recorded mistake in the parent project: it reads
    as a defect confined to whichever files were written after midnight.
    """
    table_dir, _ = built
    for name in SMALL_TABLES:
        df = pd.read_csv(os.path.join(table_dir, name))
        assert "pipeline_version" in df.columns, name
        assert "catalog_date" in df.columns, name
        assert (df["catalog_date"] == PINNED_DATE).all(), name
