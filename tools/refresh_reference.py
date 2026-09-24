# -*- coding: utf-8 -*-
"""Regenerate `reference/` after a table changes.  Run from the repo root.

    python tools/refresh_reference.py            rewrite reference/
    python tools/refresh_reference.py --check    report drift, write nothing

WHY THIS EXISTS.  Step 3 of "Changing a row" in the README said "regenerate
`reference/` so the committed CSVs match", and left HOW to the reader.  Doing
it by hand is six file copies, a stride sample, a sha256 and a five-field
platform block hand-edited into a JSON file -- and the platform block is the
part that rots, because it is the one nobody notices is wrong.  A stale block
does not fail: `test_summary_hash_on_the_reference_platform` SKIPS when the
recorded platform does not match the running one, so a wrong block turns the
strictest test in the suite into a no-op, silently, on every machine.

⚠️  THE SUMMARY HASH IS PLATFORM-SPECIFIC AND THIS TOOL RECORDS WHICH PLATFORM.
The five reference tables and environments.csv carry no transcendental
arithmetic and are byte-identical everywhere.  `transportation_summary.csv` runs
through `exp()`, so its bytes belong to the machine that wrote them.  Running
this on a different machine from the last one MOVES the recorded platform, and
that is a real change to a committed file: say so in the CHANGELOG rather than
letting it ride along with a data edit.

⚠️  `--check` IS NOT A SUBSTITUTE FOR THE TEST SUITE.  `tests/test_parity.py`
compares a fresh build against the committed bytes and is the authority.  This
flag answers a different question -- "would running this tool change anything"
-- which is what a release checklist and a CI freshness job want to know.
"""

import argparse
import hashlib
import json
import os
import platform
import shutil
import sys
import tempfile

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import spacecost  # noqa: E402

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REFERENCE = os.path.join(HERE, "reference")

# The date stamped into every committed reference file.  PINNED, because
# `catalog_date` is provenance rather than a model value: let it take today and
# every file in reference/ changes on every regeneration, and a real data diff
# becomes impossible to see.  Move it deliberately, when a release wants to say
# when these tables were cut.
PINNED_DATE = "2026-09-23"

# Files committed whole.  These are the byte-identical-everywhere contract.
COMMITTED = ["launch_vehicles.csv", "propellants.csv", "delta_v_segments.csv",
             "operational_costs.csv", "storage_systems.csv",
             "environments.csv"]

# The summary is 7.4 MB and is NOT committed; a strided sample of it is, at
# full precision, alongside the hash of the whole file and the platform that
# hash belongs to.
SUMMARY = "transportation_summary.csv"
SAMPLE = "summary_sample.csv"
META = "summary_meta.json"
STRIDE = 97   # prime, so the sample does not align with any table's period


def _build(out_dir):
    cfg = spacecost.SpacecostConfig(output_dir=out_dir, use_yfinance=False)
    frames = spacecost.build_catalog(cfg, catalog_date=PINNED_DATE)
    return cfg.table_dir(), frames


def _sha256(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def _sample_values_differ(fresh_path, committed_path, rtol=1e-12):
    """Do two summary samples disagree by more than a few ULP?

    `rtol` matches `tests/test_parity.py`: tight enough that any real change to
    a table, a coefficient or a formula fails it by orders of magnitude, loose
    enough that last-bit differences in `exp()` across hosts do not.
    """
    fresh = pd.read_csv(fresh_path, float_precision="round_trip")
    committed = pd.read_csv(committed_path, float_precision="round_trip")
    if (len(fresh) != len(committed)
            or list(fresh.columns) != list(committed.columns)):
        return True
    for col in committed.columns:
        if pd.api.types.is_numeric_dtype(committed[col]):
            if not np.allclose(fresh[col].to_numpy(dtype=float),
                               committed[col].to_numpy(dtype=float),
                               rtol=rtol, equal_nan=True):
                return True
        elif (fresh[col].fillna("").tolist()
              != committed[col].fillna("").tolist()):
            return True
    return False


def _meta(summary_path, rows):
    return {
        "sha256": _sha256(summary_path),
        "rows": rows,
        "stride": STRIDE,
        "reference_platform": {
            "system": platform.system(),
            "machine": platform.machine(),
            "python": ".".join(map(str, sys.version_info[:2])),
            "numpy": np.__version__,
            "pandas": pd.__version__,
        },
        "note": (
            "The sha256 is the byte hash ON THE REFERENCE PLATFORM ONLY. The "
            "summary's computed columns run through exp(), which is the "
            "platform libm and numpy's per-architecture SIMD kernels, and "
            "neither is required by IEEE 754 to be correctly rounded. Other "
            "platforms reproduce the VALUES to within a few ULP, not the "
            "bytes. The six reference tables carry no transcendental "
            "arithmetic and ARE byte-portable; that is checked on every CI "
            "platform."
        ),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true",
                    help="report what would change and write nothing; exits "
                         "1 if reference/ is stale")
    args = ap.parse_args(argv)

    tmp = tempfile.mkdtemp(prefix="spacecost_refresh_")
    try:
        table_dir, frames = _build(tmp)
        summary_path = os.path.join(table_dir, SUMMARY)

        sample = frames["summary"].iloc[::STRIDE].reset_index(drop=True)
        sample_path = os.path.join(tmp, SAMPLE)
        # Same writer settings as the build: CRLF is pinned because the
        # committed hashes are hashes of CRLF, and `float_format=None` keeps
        # repr round-tripping so the sample compares to full precision.
        sample.to_csv(sample_path, index=False, lineterminator="\r\n")
        meta = _meta(summary_path, len(frames["summary"]))

        changed = []
        for name in COMMITTED:
            fresh = os.path.join(table_dir, name)
            committed = os.path.join(REFERENCE, name)
            if (not os.path.exists(committed)
                    or _sha256(fresh) != _sha256(committed)):
                changed.append(name)

        # ⚠️  THE SAMPLE IS COMPARED BY VALUE, NOT BY BYTES, and that is the
        # same distinction test_parity.py draws.  It is a slice of the SUMMARY,
        # so three of its columns came out of `exp()` -- its bytes belong to
        # the machine that wrote them exactly as the summary's hash does.  A
        # byte comparison here would report every non-reference platform as
        # stale, which on this repo's CI matrix is five legs out of six.
        sample_ref = os.path.join(REFERENCE, SAMPLE)
        if not os.path.exists(sample_ref):
            changed.append(SAMPLE)
        elif _sha256(sample_path) != _sha256(sample_ref):
            if _sample_values_differ(sample_path, sample_ref):
                changed.append(SAMPLE)
            else:
                print("  . %s differs in BYTES but not in values: that is "
                      "exp() on a different host, not drift" % SAMPLE)

        meta_path = os.path.join(REFERENCE, META)
        old_meta = {}
        if os.path.exists(meta_path):
            with open(meta_path, encoding="utf-8") as fh:
                old_meta = json.load(fh)

        # `rows` and `stride` are PORTABLE facts about the model: how many
        # combinations the cross-join produces, and how the committed sample
        # was taken.  `sha256` and `reference_platform` are facts about a
        # MACHINE.  The two halves are compared separately, because only the
        # first half can be held to on a runner that is not the machine.
        portable_meta_drift = [
            k for k in ("rows", "stride", "note")
            if old_meta.get(k) != meta[k]
        ]
        platform_moved = (
            old_meta.get("reference_platform") != meta["reference_platform"])
        if portable_meta_drift or platform_moved:
            changed.append(META)
        if platform_moved:
            print("  ! the reference PLATFORM differs:")
            print("      recorded %s" % old_meta.get("reference_platform"))
            print("      running  %s" % meta["reference_platform"])
            print("    The summary hash belongs to a machine.  Regenerating "
                  "HERE would move it; note that in CHANGELOG.md rather than "
                  "letting it ride along with a data edit.")

        if args.check:
            # ⚠️  The platform block alone is NOT staleness.  CI runs on Linux
            # and on three Pythons; if the recorded platform counted as drift,
            # this check would fail on every runner but one and would be
            # switched off within a week.  What it holds to is the part that is
            # the same everywhere: the six byte-portable tables, the sample,
            # and the row count and stride that describe the model.
            hard = [c for c in changed if c != META] + portable_meta_drift
            if hard:
                print("reference/ is STALE; these would change: "
                      + ", ".join(hard))
                print("run: python tools/refresh_reference.py")
                return 1
            print("reference/ is up to date (%d tables + sample, %d summary "
                  "rows)" % (len(COMMITTED), meta["rows"]))
            if platform_moved:
                print("  (the summary hash was recorded elsewhere; it is "
                      "checked only on its own platform, and is not drift)")
            return 0

        for name in COMMITTED:
            shutil.copyfile(os.path.join(table_dir, name),
                            os.path.join(REFERENCE, name))
        shutil.copyfile(sample_path, os.path.join(REFERENCE, SAMPLE))
        # LF, matching .gitattributes, and a trailing newline so the file is
        # POSIX-clean.  Only this JSON is LF here; the CSVs beside it are CRLF
        # by contract.
        with open(meta_path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(meta, fh, indent=2)
            fh.write("\n")

        print("reference/ rewritten: %d tables, %d-row sample of %d summary rows"
              % (len(COMMITTED), len(sample), meta["rows"]))
        print("  summary sha256 %s" % meta["sha256"])
        if changed:
            print("  changed: " + ", ".join(changed))
            print("  Now: bump pipeline_version if a VALUE moved, add a "
                  "CHANGELOG entry, re-run pytest, and tag.")
        else:
            print("  nothing changed")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
