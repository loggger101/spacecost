# -*- coding: utf-8 -*-
"""The acceptance test: a build reproduces the committed reference files.

TWO CONTRACTS, AND THEY ARE NOT THE SAME STRENGTH.  Which one applies depends
on whether the file contains a computed float:

    the five reference tables    BYTE identical, on every platform
    the composite summary        the same VALUES, to within a few ULP

The tables carry no arithmetic -- every value is a table entry passed through
-- so a byte comparison is the right contract and a tolerance would hide
exactly the drift it exists to catch: a reordered column, a float formatted
differently, a row silently dropped. These tables feed a model whose releases
are argued from bit-identity, so what is promised there is not "the same
numbers" but "the same bytes".

The summary is three columns of rocket equation, so it goes through `exp()`,
which is the platform libm and numpy's per-architecture SIMD kernels. Neither
is required by IEEE 754 to be correctly rounded. Promising bytes there would be
promising something no host can deliver, so its values are compared instead,
and its byte hash is checked only on the platform it was recorded on.

The reference files were produced by economicspace
modules/transportation.py at pipeline_version 1.14.0 (commit b0b18b2) and by
this package, byte for byte identically, on 2026-09-07.  If a table test fails
and you did not mean to change a row, the extraction has drifted.
"""

import hashlib
import json
import os
import platform
import sys

import numpy as np
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


def _summary_meta():
    with open(os.path.join(REFERENCE, "summary_meta.json")) as fh:
        return json.load(fh)


def _on_reference_platform(meta) -> bool:
    ref = meta["reference_platform"]
    return (platform.system() == ref["system"]
            and platform.machine() == ref["machine"]
            and ".".join(map(str, sys.version_info[:2])) == ref["python"]
            and np.__version__ == ref["numpy"]
            and pd.__version__ == ref["pandas"])


def test_summary_values_are_portable(built):
    """The composite summary reproduces its VALUES everywhere, to a few ULP.

    ⚠️  NOT its bytes, and that distinction is the point of this test.

    The five reference tables carry no computed floats -- every value is a
    table entry passed through -- so they are byte-portable, and
    `test_table_is_byte_identical` checks exactly that on every CI platform.

    The summary is different in kind. Three of its columns come out of the
    rocket equation, so they run through `exp()`: the platform libm, and
    numpy's per-architecture SIMD kernels. Neither is required by IEEE 754 to
    be correctly rounded, and they are not. CI caught this on the first push:
    Linux/3.9 and Linux/3.12 agreed with each other and Linux/3.14 did not,
    which is a numpy version picking different kernels, not an OS difference.

    So a byte comparison of this file is a statement about a host. A VALUE
    comparison is a statement about the model, and that is what is asserted
    here. rtol is 1e-12: tight enough that any real change to a table, a
    coefficient or a formula fails it by orders of magnitude, loose enough
    that last-bit differences in exp() do not.
    """
    table_dir, frames = built
    want = pd.read_csv(os.path.join(REFERENCE, "summary_sample.csv"),
                       float_precision="round_trip")
    stride = _summary_meta()["stride"]
    got = frames["summary"].iloc[::stride].reset_index(drop=True)

    assert len(got) == len(want), "the summary changed length"
    assert list(got.columns) == list(want.columns), "the summary changed shape"

    for col in want.columns:
        if pd.api.types.is_numeric_dtype(want[col]):
            np.testing.assert_allclose(
                got[col].to_numpy(dtype=float), want[col].to_numpy(dtype=float),
                rtol=1e-12, equal_nan=True,
                err_msg="column " + col + " moved by more than a few ULP")
        else:
            assert got[col].fillna("").tolist() == want[col].fillna("").tolist(), col


def test_summary_row_count_is_pinned(built):
    """A dropped vehicle, propellant or segment changes the cross-join size."""
    _, frames = built
    assert len(frames["summary"]) == _summary_meta()["rows"]


def test_summary_hash_on_the_reference_platform(built):
    """On the recorded platform, and only there, the summary is byte-exact.

    Skipped elsewhere rather than relaxed, because a hash that is only
    sometimes meaningful is worse than one that says when it applies.
    """
    meta = _summary_meta()
    if not _on_reference_platform(meta):
        pytest.skip("not the reference platform: " + repr(meta["reference_platform"]))
    table_dir, _ = built
    path = os.path.join(table_dir, "transportation_summary.csv")
    got = hashlib.sha256(open(path, "rb").read()).hexdigest()
    assert got == meta["sha256"]


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
